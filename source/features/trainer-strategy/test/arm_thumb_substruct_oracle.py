"""Finite GetSubstruct additions over the pinned cipher Thumb frontend.

Only ANDS low register and LDRB register offset are added. The run retains the
parent's bytecode, defaults and complete effective namespace, changing just
three bindings. This module imports no CPU backend or assembler.
"""
from pathlib import Path
import hashlib
import importlib.util
import types


def load(path,name):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


P=load(Path(__file__).with_name('arm_thumb_cipher_oracle.py'),'substruct_pinned_cipher_frontend')
A,need,MASK=P.A,P.need,P.MASK
PARENT_SHA='d423e27c188173e8729a5ce56050d9574d0bf8a2f4155c60b19d43f46bcbc8c3'


def source_identity_guard():
    need(hashlib.sha256(Path(P.__file__).read_bytes()).hexdigest()==PARENT_SHA,'pinned substructure frontend drift')
    P.source_identity_guard()


def validate_thumb(blob):
    need(type(blob)is bytes and len(blob)in(2,4),'complete finite substructure instruction')
    if len(blob)==2:
        op=int.from_bytes(blob,'little')
        if op&0xffc0==0x4000:return 'and'
        if op&0xfe00==0x5c00:return 'byte_register'
    return P.validate_thumb(blob)


def thumb_step(pc,blob,regs,pages,reads,stores,read_guard=None,write_guard=None):
    kind=validate_thumb(blob)
    if kind not in('and','byte_register'):
        return P.thumb_step(pc,blob,regs,pages,reads,stores,read_guard,write_guard)
    need(pc%2==0 and regs[15]&0x3f==0x3f,'Thumb System substructure instruction state')
    op=int.from_bytes(blob,'little');rd=op&7
    if kind=='and':
        value=regs[rd]&regs[(op>>3)&7]
        regs[rd]=value;regs[15]=(regs[15]&0x3fffffff)|(value&0x80000000)|(int(value==0)<<30)
    else:
        address=(regs[(op>>3)&7]+regs[(op>>6)&7])&MASK
        if read_guard:need(read_guard(pc,address,1),'substructure byte owner/site')
        b=A.F.read(pages,address,1);reads.append(dict(pc=pc,address=address,bytes=1,hex=b.hex()));regs[rd]=b[0]
    return pc+2


run=types.FunctionType(P.run.__code__,{**P.run.__globals__,'source_identity_guard':source_identity_guard,
    'validate_thumb':validate_thumb,'thumb_step':thumb_step},argdefs=P.run.__defaults__)
run.__kwdefaults__=P.run.__kwdefaults__
