"""Finite NARC Thumb predictor composed with the unchanged ARM source oracle.

This is arithmetic, not a CPU or an FS service model. ARM segments retain their
exact registers/pages and stop before one of five native interworking returns.
The guest producer must execute those instructions in one uninterrupted CPU.
Load-PC semantics require ARMv5 TBIT loading enabled (CP15 control bit15=0).
"""
from pathlib import Path
import hashlib
import importlib.util


def load(path,name):
    s=importlib.util.spec_from_file_location(name,path)
    m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


A=load(Path(__file__).with_name('arm32_sync_oracle.py'),'narc_pinned_arm_arithmetic')
need,MASK=A.need,A.MASK
PARENT_SHA='92b75e6111555139cdb312ec60535de1c142ad5b33629bb100c05caf8bb58fd4'
RETURNS={0x20d7f98:(0x20d7fbc,0xe12fff1e),0x20d8278:(0x20d82b0,0x18bd8010),
         0x20d83dc:(0x20d8444,0xe12fff1e),0x20d83cc:(0x20d817c,0xe8bd80f8),
         0x20d82c0:(0x20d82f8,0xe8bd8010)}


def exchange(target,regs,*,load_tbit_enabled=True):
    need(type(load_tbit_enabled)is bool and load_tbit_enabled,'TBIT loading must be enabled')
    need(type(target)is int and 0<=target<=MASK,'typed branch target')
    if target&1:regs[15]|=0x20;return target&~1
    need(target%4==0,'word aligned ARM exchange target')
    regs[15]&=~0x20;return target


def validate_thumb(blob):
    need(type(blob)is bytes and len(blob)in(2,4),'complete finite Thumb instruction')
    op=int.from_bytes(blob[:2],'little')
    if op&0xf800==0xf000:
        need(len(blob)==4,'complete Thumb BL/BLX pair')
        low=int.from_bytes(blob[2:],'little')
        need(low&0xf800==0xf800 or low&0xf801==0xe800,'unsupported Thumb BL/BLX suffix')
        return 'call'
    need(len(blob)==2,'ordinary Thumb width')
    if op&0xf600==0xb400:
        need(op&0x1ff,'empty Thumb stack register list');return 'stack'
    if op&0xff00==0xb000:return 'sp'
    if op&0xfe00==0x5800:return 'ordinary'
    if op&0xf800 in(0x4800,0x8000,0x8800,0x9000,0x9800,0xa800,0x1800,0x3000,0x0000,0x2000,0x2800):return 'ordinary'
    if op&0xffc0==0x4280:return 'ordinary'
    if op&0xf000==0xd000 and(op>>8)&15 in(1,12):return 'condition'
    raise ValueError('unsupported finite Thumb instruction '+hex(op))


def thumb_step(pc,blob,regs,pages,reads,stores,read_guard=None,write_guard=None):
    kind=validate_thumb(blob)
    need(pc%2==0 and regs[15]&0x3f==0x3f,'Thumb System instruction state')
    op=int.from_bytes(blob[:2],'little');nxt=pc+len(blob)
    def read(address,n):
        need(n in(2,4)and address%n==0,'aligned Thumb read')
        if read_guard:need(read_guard(pc,address,n),'source read owner/site')
        b=A.F.read(pages,address,n);reads.append(dict(pc=pc,address=address,bytes=n,hex=b.hex()))
        return int.from_bytes(b,'little')
    def store(address,value,n):
        need(n in(2,4)and address%n==0,'aligned Thumb store')
        if write_guard:need(write_guard(pc,address,n),'source write owner/site')
        value&=(1<<(8*n))-1
        stores.append(dict(pc=pc,address=address,bytes=n,before=A.F.read(pages,address,n).hex(),value=value))
        A.F.put(pages,address,value.to_bytes(n,'little'))
    def arithmetic(a,b,subtract=False):
        full=a-b if subtract else a+b;value=full&MASK
        carry=int(a>=b)if subtract else int(full>MASK)
        overflow=(a^b)&(a^value)if subtract else~(a^b)&(a^value)
        regs[15]=A.nzcv(regs[15],value,carry,bool(overflow&0x80000000));return value
    if kind=='stack':
        pop=bool(op&0x800);indices=[i for i in range(8)if op&(1<<i)]
        if op&0x100:indices.append(15 if pop else 14)
        address=regs[13]if pop else(regs[13]-4*len(indices))&MASK
        if pop:
            values=[read(address+4*i,4)for i in range(len(indices))]
            for i,value in zip(indices,values):
                if i==15:nxt=exchange(value,regs)
                else:regs[i]=value
            regs[13]=(regs[13]+4*len(indices))&MASK
        else:
            for i,index in enumerate(indices):store(address+4*i,regs[index],4)
            regs[13]=address
    elif kind=='sp':regs[13]=(regs[13]+((-1 if op&0x80 else 1)*(op&127)*4))&MASK
    elif kind=='call':
        high=op&0x7ff
        if high&0x400:high-=0x800
        low=int.from_bytes(blob[2:],'little');is_arm=low&0xf800==0xe800
        base=((pc+4)&~3)if is_arm else pc+4
        nxt=(base+(high<<12)+((low&0x7ff)<<1))&MASK
        regs[14]=(pc+4)|1
        if is_arm:nxt=exchange(nxt,regs)
    elif op&0xf800==0x4800:regs[(op>>8)&7]=read(((pc+4)&~3)+(op&255)*4,4)
    elif op&0xfe00==0x5800:regs[op&7]=read((regs[(op>>3)&7]+regs[(op>>6)&7])&MASK,4)
    elif op&0xf800==0x8000:store((regs[(op>>3)&7]+((op>>6)&31)*2)&MASK,regs[op&7],2)
    elif op&0xf800==0x8800:regs[op&7]=read((regs[(op>>3)&7]+((op>>6)&31)*2)&MASK,2)
    elif op&0xf800==0x9000:store((regs[13]+(op&255)*4)&MASK,regs[(op>>8)&7],4)
    elif op&0xf800==0x9800:regs[(op>>8)&7]=read((regs[13]+(op&255)*4)&MASK,4)
    elif op&0xf800==0xa800:regs[(op>>8)&7]=(regs[13]+(op&255)*4)&MASK
    elif op&0xf800==0x1800:
        b=(op>>6)&7 if op&0x400 else regs[(op>>6)&7]
        regs[op&7]=arithmetic(regs[(op>>3)&7],b,bool(op&0x200))
    elif op&0xf800==0x3000:
        rd=(op>>8)&7;regs[rd]=arithmetic(regs[rd],op&255)
    elif op&0xf800==0:
        rd,rs,shift=op&7,(op>>3)&7,(op>>6)&31
        value,carry=A.shifted(regs[rs],0,shift,(regs[15]>>29)&1)
        regs[rd]=value;regs[15]=A.nzcv(regs[15],value,carry,bool(regs[15]&0x10000000))
    elif op&0xf800==0x2000:
        value=op&255;regs[(op>>8)&7]=value
        regs[15]=(regs[15]&0x3fffffff)|(int(value==0)<<30)
    elif op&0xffc0==0x4280:arithmetic(regs[op&7],regs[(op>>3)&7],True)
    elif op&0xf800==0x2800:arithmetic(regs[(op>>8)&7],op&255,True)
    elif kind=='condition':
        delta=op&255
        if delta&128:delta-=256
        if A.condition((op>>8)&15,regs[15]):nxt=(pc+4+2*delta)&MASK
    else:raise ValueError('unsupported finite Thumb semantic')
    return nxt


def arm_return(pc,word,regs,pages,reads,read_guard=None):
    need((pc,word)in RETURNS.values(),'unqualified ARM interworking return')
    need(regs[15]&0x3f==0x1f,'ARM System return state')
    need(A.condition(word>>28,regs[15]),'native return condition outside successful domain')
    if word==0xe12fff1e:return exchange(regs[14],regs)
    indices=[i for i in range(16)if word&(1<<i)];base=regs[13]
    need(base%4==0,'aligned ARM return frame')
    values=[]
    for i in range(len(indices)):
        address=base+4*i
        if read_guard:need(read_guard(pc,address,4),'source read owner/site')
        b=A.F.read(pages,address,4);reads.append(dict(pc=pc,address=address,bytes=4,hex=b.hex()))
        values.append(int.from_bytes(b,'little'))
    for i,value in zip(indices,values):
        if i!=15:regs[i]=value
    regs[13]=(base+4*len(indices))&MASK
    return exchange(values[-1],regs)


def run(f,code_spans,stop,cap=8192,read_guard=None,write_guard=None,*,thumb_code):
    need(hashlib.sha256(Path(A.__file__).read_bytes()).hexdigest()==PARENT_SHA,'pinned ARM predictor drift')
    need(type(cap)is int and 0<cap<=8192,'finite mixed instruction cap')
    need(type(thumb_code)is dict and all(type(pc)is int and pc%2==0 for pc in thumb_code),'typed qualified Thumb code')
    for blob in thumb_code.values():validate_thumb(blob)
    need(all(not any(pc<a+len(b)and a<pc+len(blob)for a,b in thumb_code.items()if a!=pc)for pc,blob in thumb_code.items()),'overlapping qualified Thumb instructions')
    regs=list(f['entry_regs']);pc=f['entry_pc'];initial_sp=regs[13];low=initial_sp
    need(len(regs)==16 and all(type(x)is int and 0<=x<=MASK for x in regs),'typed mixed full16')
    need(regs[15]&0x3f in(0x1f,0x3f),'mixed System state only')
    pages={a:bytearray(b)for a,b in f['pages'].items()};flow=[];reads=[];stores=[]
    while pc!=stop:
        need(len(flow)<cap,'mixed instruction budget');low=min(low,regs[13])
        if regs[15]&0x20:
            need(pc in thumb_code,'instruction outside qualified Thumb starts')
            blob=thumb_code[pc];need(A.F.read(pages,pc,len(blob))==blob,'qualified Thumb byte identity')
            flow.append(dict(pc=pc,regs=list(regs)))
            pc=thumb_step(pc,blob,regs,pages,reads,stores,read_guard,write_guard)
        else:
            need(pc in RETURNS,'unqualified ARM API entry from Thumb')
            ret,word=RETURNS[pc]
            segment=A.run(dict(entry_pc=pc,entry_regs=regs,pages=pages),code_spans,ret,
                          cap=cap-len(flow),read_guard=read_guard,write_guard=write_guard)
            low=min(low,regs[13]-segment['native_peak'])
            flow.extend(segment['flow']);reads.extend(segment['reads']);stores.extend(segment['stores'])
            regs=segment['returned'];pages={a:bytearray(b)for a,b in segment['pages'].items()}
            need(len(flow)<cap and A.F.read(pages,ret,4)==word.to_bytes(4,'little'),'qualified ARM return bytes/budget')
            flow.append(dict(pc=ret,regs=list(regs)))
            pc=arm_return(ret,word,regs,pages,reads,read_guard)
    return dict(flow=flow,reads=reads,stores=stores,returned=list(regs),stop_pc=pc,
                native_peak=initial_sp-low,pages={a:bytes(b)for a,b in pages.items()})
