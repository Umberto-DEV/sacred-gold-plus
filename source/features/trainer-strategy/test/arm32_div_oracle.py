"""Finite signed-division arithmetic additions to the pinned sync oracle.

Only RSB and ADC are added. ADC samples CPSR carry before Operand2 shifting.
The original SDK interpreter remains unchanged; callers must select this
extension only for the separately authenticated division code corpus.
"""
from pathlib import Path
import importlib.util
import hashlib


def load(path,name):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


F=load(Path(__file__).parents[1]/'tools/congela_fs_cached_seekdir.py','sparse_arm_cached_memory')
need=F.need
MASK=0xffffffff
PARENT_SHA='92b75e6111555139cdb312ec60535de1c142ad5b33629bb100c05caf8bb58fd4'


def condition(code,psr):
    n,z,c,v=(bool(psr&(1<<bit))for bit in(31,30,29,28))
    values=(z,not z,c,not c,n,not n,v,not v,c and not z,not c or z,n==v,n!=v,not z and n==v,z or n!=v,True)
    need(type(code)is int and 0<=code<15,'unsupported ARM condition')
    return values[code]


def shifted(value,kind,amount,carry,register=False):
    """ARM immediate/register LSL/LSR/ASR; ROR is outside this finite scope."""
    value&=MASK
    need(kind in(0,1,2)and type(amount)is int and 0<=amount<=255,'unsupported ARM shift')
    if amount==0:
        if register or kind==0:return value,carry
        amount=32
    if kind==0:
        return ((value<<amount)&MASK,(value>>(32-amount))&1)if amount<=32 else(0,0)
    if kind==1:
        return (value>>amount,(value>>(amount-1))&1)if amount<=32 else(0,0)
    sign=(value>>31)&1
    if amount>=32:return (MASK if sign else 0),sign
    signed=value-(1<<32)if sign else value
    return (signed>>amount)&MASK,(value>>(amount-1))&1


def nzcv(old,value,carry,overflow):
    return (old&0x0fffffff)|(value&0x80000000)|(int(value==0)<<30)|(int(carry)<<29)|(int(overflow)<<28)


def validate_word(word):
    """Reject unsupported encodings even when their predicate is false."""
    need(type(word)is int and 0<=word<=MASK and word>>28<15,'unsupported ARM encoding/condition')
    if word&0x0fffffff in(0x010f0000,0x010f1000):return 'mrs'
    if word&0x0fffffff in(0x0121f001,0x0121f002):return 'msr'
    rn,rt=(word>>16)&15,(word>>12)&15
    exchange=word&0x0ffffff0
    if exchange in(0x012fff10,0x012fff30):return 'exchange'
    if (word>>25)&7==5:return 'branch'
    if (word>>25)&7==4:
        indices=[i for i in range(16)if word&(1<<i)]
        need(not word&(1<<22)and indices and rn!=15,'unsupported block transfer')
        need(not(word&(1<<21)and rn in indices),'unsupported block base alias')
        need(bool(word&(1<<20))or 15 not in indices,'unsupported store PC')
        return 'block'
    if (word>>26)&3==1 or word&0x0e000090==0x00000090:
        half=(word>>26)&3!=1;p,u,w,l=((word>>bit)&1 for bit in(24,23,21,20))
        if half:
            need((word>>5)&3==1 and bool(word&(1<<22)),'unsupported halfword/signed/multiply encoding')
            need(rt!=15,'unsupported halfword PC')
        elif word&(1<<25):
            need(not word&16 and (word>>5)&3 in(0,1,2),'unsupported memory register shift')
        need(not(not p and w),'unsupported unprivileged transfer')
        need(not((w or not p)and(rn==15 or rn==rt)),'unsupported memory writeback alias')
        need(l or rt!=15,'unsupported store PC')
        return 'memory'
    if (word>>26)&3==0:
        op=(word>>21)&15;sets=bool(word&(1<<20))
        need(op in(0,1,2,3,4,5,8,10,12,13,14,15),'unsupported ARM data opcode')
        need(op not in(8,10)or(sets and rt==0),'unsupported PSR/test encoding')
        need(not(op in(13,15)and rn!=0),'unsupported MOV/MVN encoding')
        need(not(sets and rt==15 and op not in(8,10)),'unsupported exception return')
        if not word&(1<<25):
            need((word>>5)&3 in(0,1,2),'unsupported ARM shift')
            if word&16:need(not word&128 and word&15!=15 and (word>>8)&15!=15,'unsupported register shift encoding')
        return 'data'
    raise ValueError('unsupported ARM encoding '+hex(word))


def source_identity_guard():
    path=Path(__file__).with_name('arm32_sync_oracle.py')
    need(hashlib.sha256(path.read_bytes()).hexdigest()==PARENT_SHA,'pinned synchronous ARM predictor drift')


def run(f,code_spans,stop,cap=8192,read_guard=None,write_guard=None):
    source_identity_guard()
    need(type(cap)is int and 0<cap<=8192,'finite ARM instruction cap')
    regs=list(f['entry_regs']);pc=f['entry_pc'];initial_sp=regs[13];low=initial_sp
    need(len(regs)==16 and all(type(x)is int and 0<=x<=MASK for x in regs),'typed ARM full16')
    need(regs[15]&0x3f==0x1f,'ARM System state only')
    pages={a:bytearray(b)for a,b in f['pages'].items()};flow=[];reads=[];stores=[]
    starts={a for address,n in code_spans for a in range(address,address+n,4)}
    def reg(index):return (pc+8)&MASK if index==15 else regs[index]
    def read(address,n):
        need(n in(1,2,4)and address%n==0,'aligned finite ARM read width')
        if read_guard:need(read_guard(pc,address,n),'source read owner/site')
        blob=F.read(pages,address,n);reads.append(dict(pc=pc,address=address,bytes=n,hex=blob.hex()))
        return int.from_bytes(blob,'little')
    def store(address,value,n):
        need(n in(1,2,4)and address%n==0,'aligned finite ARM write width')
        if write_guard:need(write_guard(pc,address,n),'source write owner/site')
        value&=(1<<(8*n))-1
        stores.append(dict(pc=pc,address=address,bytes=n,before=F.read(pages,address,n).hex(),value=value))
        F.put(pages,address,value.to_bytes(n,'little'))
    def operand(word):
        carry=(regs[15]>>29)&1
        if word&(1<<25):
            imm=word&255;rotate=((word>>8)&15)*2
            if rotate==0:return imm,carry
            value=((imm>>rotate)|(imm<<(32-rotate)))&MASK
            return value,value>>31
        rm=word&15;kind=(word>>5)&3
        if word&16:
            need(not word&128 and rm!=15 and (word>>8)&15!=15,'unsupported register shift encoding')
            return shifted(reg(rm),kind,reg((word>>8)&15)&255,carry,True)
        return shifted(reg(rm),kind,(word>>7)&31,carry)
    while pc!=stop:
        need(len(flow)<cap,'ARM instruction budget')
        need(pc in starts and pc%4==0,'ARM instruction outside qualified code')
        need(not regs[15]&0x20,'unsupported Thumb state')
        low=min(low,regs[13]);flow.append(dict(pc=pc,regs=list(regs)))
        word=int.from_bytes(F.read(pages,pc,4),'little');next_pc=pc+4
        group=validate_word(word)
        cond=word>>28
        if not condition(cond,regs[15]):pc=next_pc;continue
        exchange=word&0x0ffffff0
        if group=='mrs':
            regs[(word>>12)&15]=regs[15]
        elif group=='msr':
            updated=(regs[15]&~255)|(reg(word&15)&255)
            need((updated^regs[15])&~0x80==0,'IRQ control domain: only I may change')
            regs[15]=updated
        elif group=='exchange':
            target=reg(word&15);need(target&3==0,'unsupported ARM/Thumb exchange target')
            if exchange==0x012fff30:regs[14]=pc+4
            next_pc=target
        elif group=='branch':
            delta=word&0xffffff
            if delta&0x800000:delta-=1<<24
            if word&(1<<24):regs[14]=pc+4
            next_pc=(pc+8+(delta<<2))&MASK
        elif group=='block':
            p,u,s,w,l=((word>>bit)&1 for bit in(24,23,22,21,20))
            rn=(word>>16)&15;indices=[i for i in range(16)if word&(1<<i)];base=reg(rn)
            need(not s and indices and rn!=15 and base%4==0,'unsupported block transfer')
            need(not(w and rn in indices),'unsupported block base writeback alias')
            address=base+(4 if p else 0)if u else base-4*len(indices)+(0 if p else 4)
            if l:
                values=[read((address+4*i)&MASK,4)for i in range(len(indices))]
                for index,value in zip(indices,values):
                    if index==15:need(value&3==0,'unsupported POP ISA exchange');next_pc=value
                    else:regs[index]=value
            else:
                need(15 not in indices,'unsupported store PC')
                values=[reg(i)for i in indices]
                for i,value in enumerate(values):store((address+4*i)&MASK,value,4)
            if w:regs[rn]=(base+(4*len(indices)if u else-4*len(indices)))&MASK
        elif group=='memory':
            half=(word>>26)&3!=1
            p,u,w,l=((word>>bit)&1 for bit in(24,23,21,20))
            rn,rt=(word>>16)&15,(word>>12)&15;base=reg(rn)
            if half:
                need((word>>5)&3==1,'unsupported halfword/signed/multiply encoding')
                offset=((word>>4)&0xf0)|(word&15)if word&(1<<22)else reg(word&15);width=2
            else:
                width=1 if word&(1<<22)else 4
                if word&(1<<25):
                    need(not word&16,'unsupported memory register shift')
                    offset,_=shifted(reg(word&15),(word>>5)&3,(word>>7)&31,(regs[15]>>29)&1)
                else:offset=word&4095
            need(not(not p and w),'unsupported unprivileged transfer')
            writeback=bool(w or not p);updated=(base+(offset if u else-offset))&MASK
            need(not(writeback and(rn==15 or rn==rt)),'unsupported memory base/destination writeback alias')
            address=updated if p else base
            if l:
                value=read(address,width)
                if rt==15:need(width==4 and value&3==0,'unsupported load PC');next_pc=value
                else:regs[rt]=value
            else:need(rt!=15,'unsupported store PC');store(address,reg(rt),width)
            if writeback:regs[rn]=updated
        elif group=='data':
            op=(word>>21)&15;s=bool(word&(1<<20));rn=(word>>16)&15;rd=(word>>12)&15
            need(op in(0,1,2,3,4,5,8,10,12,13,14,15),'unsupported ARM data opcode')
            need(op not in(8,10)or s,'unsupported PSR/test encoding')
            carry_in=(regs[15]>>29)&1
            b,carry=operand(word);a=reg(rn);overflow=bool(regs[15]&0x10000000)
            if op in(2,10):
                value=(a-b)&MASK;carry=int(a>=b);overflow=bool((a^b)&(a^value)&0x80000000)
            elif op==3:
                value=(b-a)&MASK;carry=int(b>=a);overflow=bool((b^a)&(b^value)&0x80000000)
            elif op==4:
                total=a+b;value=total&MASK;carry=int(total>MASK);overflow=bool(~(a^b)&(a^value)&0x80000000)
            elif op==5:
                total=a+b+carry_in;value=total&MASK;carry=int(total>MASK);overflow=bool(~(a^b)&(a^value)&0x80000000)
            elif op in(0,8):value=a&b
            elif op==1:value=a^b
            elif op==12:value=a|b
            elif op==13:value=b
            elif op==14:value=a&(~b&MASK)
            else:value=~b&MASK
            if s:need(rd!=15 or op in(8,10),'unsupported exception-return data opcode');regs[15]=nzcv(regs[15],value,carry,overflow)
            if op not in(8,10):
                if rd==15:need(value&3==0,'unsupported data PC ISA exchange');next_pc=value
                else:regs[rd]=value
        else:raise ValueError('unsupported ARM encoding '+hex(word))
        pc=next_pc&MASK
    return dict(flow=flow,reads=reads,stores=stores,returned=list(regs),stop_pc=pc,
                native_peak=initial_sp-low,pages={a:bytes(b)for a,b in pages.items()})
