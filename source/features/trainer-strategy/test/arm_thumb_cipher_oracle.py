"""Finite cipher Thumb additions over the pinned MaxPP arithmetic frontend.

No parent code changes: the run bytecode/defaults are reused with explicit
validator/step/identity bindings. Native cipher admission remains Thumb-only
in its owner bench. No CPU backend is imported here.
"""
from pathlib import Path
import hashlib
import importlib.util
import types


def load(path,name):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


P=load(Path(__file__).with_name('arm_thumb_maxpp_oracle.py'),'cipher_pinned_maxpp')
A,need,MASK=P.A,P.need,P.MASK
PARENT_SHA='8fd915dfabd9cce1d7fa497efbc6125d468f4f3698843c1af825890915d0d053'


def source_identity_guard():
    need(hashlib.sha256(Path(P.__file__).read_bytes()).hexdigest()==PARENT_SHA,'pinned cipher frontend drift')
    P.source_identity_guard()


def validate_thumb(blob):
    need(type(blob)is bytes and len(blob)in(2,4),'complete finite cipher instruction')
    if len(blob)==2:
        op=int.from_bytes(blob,'little')
        if op&0xffc0==0x4040:return 'eor'
        if op&0xf800 in(0x6000,0x6800):return 'word'
        if op&0xff00 in(0xd000,0xd300):return 'cipher_condition'
    return P.validate_thumb(blob)


def thumb_step(pc,blob,regs,pages,reads,stores,read_guard=None,write_guard=None):
    kind=validate_thumb(blob)
    if kind not in('eor','word','cipher_condition'):
        return P.thumb_step(pc,blob,regs,pages,reads,stores,read_guard,write_guard)
    need(pc%2==0 and regs[15]&0x3f==0x3f,'Thumb System cipher instruction state')
    op=int.from_bytes(blob,'little');nxt=pc+2
    if kind=='eor':
        rd,rm=op&7,(op>>3)&7;value=regs[rd]^regs[rm]
        regs[rd]=value;regs[15]=(regs[15]&0x3fffffff)|(value&0x80000000)|(int(value==0)<<30)
    elif kind=='word':
        rd,rn,offset=op&7,(op>>3)&7,((op>>6)&31)*4
        address=(regs[rn]+offset)&MASK
        need(address%4==0,'aligned cipher word access')
        guard=read_guard if op&0x800 else write_guard
        if guard:need(guard(pc,address,4),'cipher word owner/site')
        before=A.F.read(pages,address,4)
        if op&0x800:
            reads.append(dict(pc=pc,address=address,bytes=4,hex=before.hex()));regs[rd]=int.from_bytes(before,'little')
        else:
            value=regs[rd]&MASK;stores.append(dict(pc=pc,address=address,bytes=4,before=before.hex(),value=value))
            A.F.put(pages,address,value.to_bytes(4,'little'))
    else:
        delta=op&255
        if delta&128:delta-=256
        if A.condition((op>>8)&15,regs[15]):nxt=(pc+4+2*delta)&MASK
    return nxt


run=types.FunctionType(P.run.__code__,{**vars(P),'source_identity_guard':source_identity_guard,
    'validate_thumb':validate_thumb,'thumb_step':thumb_step},argdefs=P.run.__defaults__)
run.__kwdefaults__=P.run.__kwdefaults__
