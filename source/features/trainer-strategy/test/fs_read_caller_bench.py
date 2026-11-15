"""Finite caller bridge and source-authenticated Read/Wait integration helpers."""
import struct

FRAME=0x23BEDD0
U32=0xFFFFFFFF


def need(value,message):
    if not value:raise ValueError(message)


def advance_bridge(code,pc,regs,frame):
    r=list(regs);memory=bytearray(frame);flow=[];reads=[];stores=[]
    need(len(r)==16 and all(type(v)is int and 0<=v<=U32 for v in r)and
         r[15]&0x0FFFFFFF==0x3F and len(memory)==240,'Bridge unsigned32 Thumb/SYS input and frame240')

    def arithmetic(a,b,subtract=False):
        full=a-b if subtract else a+b;value=full&U32
        carry=int(a>=b)if subtract else int(full>U32)
        overflow=((a^b)&(a^value))if subtract else(~(a^b)&(a^value))
        r[15]=(r[15]&0x0FFFFFFF)|(value&0x80000000)|(int(value==0)<<30)|(carry<<29)|((overflow&0x80000000)>>3)
        return value

    def load(address,n):
        i=address-FRAME;need(0<=i and i+n<=len(memory),'Bridge owned stack load')
        blob=bytes(memory[i:i+n]);reads.append(dict(pc=hex(pc),address=address,bytes=n,hex=blob.hex()))
        return int.from_bytes(blob,'little')

    for _ in range(80):
        need(0x2007352<=pc<0x2007408 and pc in code,'Bridge finite qualified caller PC')
        blob=code[pc];need(len(blob)in(2,4),'Bridge Thumb width')
        op=struct.unpack_from('<H',blob)[0];flow.append(dict(pc=hex(pc),regs=list(r)));next_pc=pc+2
        if op&0xF800==0x9800:  # LDR Rd,[SP,#imm8*4]
            r[(op>>8)&7]=load(r[13]+(op&255)*4,4)
        elif op&0xF800==0x8800:  # LDRH Rd,[Rn,#imm5*2]
            r[op&7]=load(r[(op>>3)&7]+((op>>6)&31)*2,2)
        elif op&0xF800==0x9000:  # STR Rd,[SP,#imm8*4]
            address=r[13]+(op&255)*4;i=address-FRAME
            need(0<=i and i+4<=len(memory),'Bridge owned stack store')
            value=r[(op>>8)&7];stores.append(dict(pc=hex(pc),address=address,bytes=4,before=bytes(memory[i:i+4]).hex(),value=value))
            memory[i:i+4]=struct.pack('<I',value)
        elif op&0xF800==0xA800:  # ADD Rd,SP,#imm8*4, without flags
            r[(op>>8)&7]=(r[13]+(op&255)*4)&U32
        elif op&0xF800==0x1800:  # ADDS/SUBS low register or immediate3
            b=(op>>6)&7 if op&0x400 else r[(op>>6)&7]
            r[op&7]=arithmetic(r[(op>>3)&7],b,bool(op&0x200))
        elif op&0xF800==0x3000:  # ADDS Rd,#imm8
            rd=(op>>8)&7;r[rd]=arithmetic(r[rd],op&255)
        elif op&0xF800==0:  # LSLS Rd,Rs,#imm5 (zero preserves C)
            rd,rs,shift=op&7,(op>>3)&7,(op>>6)&31;value=(r[rs]<<shift)&U32
            carry=((r[rs]>>(32-shift))&1)if shift else((r[15]>>29)&1)
            r[rd]=value;r[15]=(r[15]&0x1FFFFFFF)|(value&0x80000000)|(int(value==0)<<30)|(carry<<29)
        elif op&0xF800==0x2000:  # MOVS Rd,#imm8, retaining C/V
            value=op&255;r[(op>>8)&7]=value
            r[15]=(r[15]&0x3FFFFFFF)|(int(value==0)<<30)
        elif op&0xFFC0==0x4280:  # CMP low registers
            arithmetic(r[op&7],r[(op>>3)&7],True)
        elif op&0xF800==0x2800:  # CMP Rd,#imm8
            arithmetic(r[(op>>8)&7],op&255,True)
        elif op&0xF000==0xD000:
            condition=(op>>8)&15;need(condition in(1,12),'Bridge only source NE/GT conditions')
            n,z,v=(r[15]>>31)&1,(r[15]>>30)&1,(r[15]>>28)&1
            take=not z if condition==1 else(not z and n==v)
            offset=op&255
            if offset&128:offset-=256
            if take:next_pc=pc+4+2*offset
        elif op&0xF800==0xF000:
            need(len(blob)==4,'Bridge complete BLX pair');low=struct.unpack_from('<H',blob,2)[0]
            need(low&0xF800==0xE800 and low&1==0,'Bridge ARMv5 BLX word-aligned encoding')
            high=op&0x7FF
            if high&0x400:high-=0x800
            target=((pc+4)&~3)+(high<<12)+((low&0x7FF)<<1)
            need(target in(0x20D83DC,0x20D83CC,0x20D82C0),'Bridge permitted native FS target')
            r[14]=(pc+4)|1;r[15]&=~0x20
            return dict(target=target,entry=r,next_pc=pc+4,frame=memory.hex(),flow=flow,reads=reads,stores=stores)
        else:raise ValueError('Bridge unsupported finite Thumb instruction '+hex(op))
        need(len(blob)==2,'Bridge ordinary instruction width');pc=next_pc
    raise ValueError('Bridge instruction budget')


def require_page(before,after,frame_after,destination,payload):
    need(len(before)==len(after)==4096 and len(frame_after)==240,'Read witness exact4KiB page/frame240')
    page=FRAME&~4095;offset=destination-page
    need(type(destination)is int and page<=destination and offset+len(payload)<=4096,
         'Read witness output belongs to the captured page')
    lo,hi=max(destination,FRAME),min(destination+len(payload),FRAME+240)
    need(lo>=hi or frame_after[lo-FRAME:hi-FRAME]==payload[lo-destination:hi-destination],
         'Read frame and payload predictions agree at every overlapping byte')
    expected=bytearray(before);i=FRAME-page;expected[i:i+240]=frame_after
    expected[offset:offset+len(payload)]=payload
    need(bytes(expected)==after,'Read witness exact source delta; other page bytes unchanged')
    return True
