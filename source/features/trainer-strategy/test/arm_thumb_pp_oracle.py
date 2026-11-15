"""Finite PP getter additions to the pinned NARC instruction predictor.

The parent and its ARM arithmetic remain unchanged. Reusing its run function
with two explicit dispatch overrides adds no CPU service or hidden phase bridge.
Only the two actual high-ADD words and BX r3/lr encodings are added.
"""
from pathlib import Path
import hashlib
import importlib.util
import types


s=importlib.util.spec_from_file_location('pp_pinned_narc_frontend',Path(__file__).with_name('arm_thumb_narc_oracle.py'))
P=importlib.util.module_from_spec(s);s.loader.exec_module(P)
A,need,MASK=P.A,P.need,P.MASK
PARENT_SHA=P.PARENT_SHA
FRONTEND_SHA='476b389e2c875ff80feabba3e8990a5313ce912aff607729febc8c4df4dc9ce0'
RETURNS,exchange,arm_return=P.RETURNS,P.exchange,P.arm_return


def validate_thumb(blob):
    need(type(blob)is bytes and len(blob)in(2,4),'complete finite Thumb instruction')
    if len(blob)==2:
        op=int.from_bytes(blob,'little')
        if op in(0x4479,0x448f):return 'high_add_pc'
        if op in(0x4718,0x4770):return 'bx_thumb'
        if op&0xff00==0xd800:return 'bhi'
        if op&0xf800==0x1000:return 'asr'
        if op&0xf800==0x7800:return 'ldrb'
    return P.validate_thumb(blob)


def thumb_step(pc,blob,regs,pages,reads,stores,read_guard=None,write_guard=None):
    kind=validate_thumb(blob)
    if kind not in('high_add_pc','bx_thumb','bhi','asr','ldrb'):
        return P.thumb_step(pc,blob,regs,pages,reads,stores,read_guard,write_guard)
    need(pc%2==0 and regs[15]&0x3f==0x3f,'Thumb System instruction state')
    op=int.from_bytes(blob,'little');nxt=pc+2
    if kind=='high_add_pc':
        rd=(op&7)|((op>>4)&8);rm=(op>>3)&15
        # Register-form ADD reads unrounded PC+4; an ALU write retains T.
        a=(pc+4)&MASK if rd==15 else regs[rd]
        b=(pc+4)&MASK if rm==15 else regs[rm]
        value=(a+b)&MASK
        if rd==15:nxt=value&~1
        else:regs[rd]=value
    elif kind=='bx_thumb':nxt=exchange(regs[(op>>3)&15],regs)
    elif kind=='bhi':
        delta=op&255
        if delta&128:delta-=256
        if A.condition(8,regs[15]):nxt=(pc+4+2*delta)&MASK
    elif kind=='asr':
        rd,rm,amount=op&7,(op>>3)&7,(op>>6)&31
        value,carry=A.shifted(regs[rm],2,amount,(regs[15]>>29)&1)
        regs[rd]=value;regs[15]=A.nzcv(regs[15],value,carry,bool(regs[15]&0x10000000))
    else:
        address=(regs[(op>>3)&7]+((op>>6)&31))&MASK
        if read_guard:need(read_guard(pc,address,1),'source read owner/site')
        b=A.F.read(pages,address,1);reads.append(dict(pc=pc,address=address,bytes=1,hex=b.hex()))
        regs[op&7]=b[0]
    return nxt


def run(f,code_spans,stop,cap=8192,read_guard=None,write_guard=None,*,thumb_code):
    need(hashlib.sha256(Path(P.__file__).read_bytes()).hexdigest()==FRONTEND_SHA,'pinned NARC frontend drift')
    fn=types.FunctionType(P.run.__code__,{**vars(P),'validate_thumb':validate_thumb,'thumb_step':thumb_step})
    return fn(f,code_spans,stop,cap,read_guard,write_guard,thumb_code=thumb_code)
