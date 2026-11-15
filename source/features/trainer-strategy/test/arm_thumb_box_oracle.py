"""Finite Box additions: SUBS immediate8, Thumb B and two high ADD words.

Retains the pinned substructure interpreter's effective namespace and bytecode.
This module never imports a CPU backend, compiler or ROM loader.
"""
from pathlib import Path
import hashlib
import importlib.util
import types


def load(path,name):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


P=load(Path(__file__).with_name('arm_thumb_substruct_oracle.py'),'box_pinned_substruct_frontend')
A,need,MASK=P.A,P.need,P.MASK
PARENT_SHA='4d999f9db1db46b2959064f75b82365c9d8b1d0b0e0fca4f01c77d6c199a79c8'


def source_identity_guard():
    need(hashlib.sha256(Path(P.__file__).read_bytes()).hexdigest()==PARENT_SHA,'pinned Box frontend drift')
    P.source_identity_guard()


def validate_thumb(blob):
    need(type(blob)is bytes and len(blob)in(2,4),'complete finite Box instruction')
    if len(blob)==2:
        op=int.from_bytes(blob,'little')
        if op&0xf800==0x3800:return 'sub_imm8'
        if op&0xf800==0xe000:return 'branch_imm11'
        if op in(0x4478,0x4487):return 'box_high_add_pc'
    return P.validate_thumb(blob)


def thumb_step(pc,blob,regs,pages,reads,stores,read_guard=None,write_guard=None):
    kind=validate_thumb(blob)
    if kind not in('sub_imm8','branch_imm11','box_high_add_pc'):
        return P.thumb_step(pc,blob,regs,pages,reads,stores,read_guard,write_guard)
    need(pc%2==0 and regs[15]&0x3f==0x3f,'Thumb System Box instruction state')
    op=int.from_bytes(blob,'little')
    if kind=='box_high_add_pc':
        value=(regs[0]+pc+4)&MASK
        if op==0x4487:return value&~1
        regs[0]=value;return (pc+2)&MASK
    if kind=='branch_imm11':
        offset=op&0x7ff
        if offset&0x400:offset-=0x800
        return (pc+4+2*offset)&MASK
    rd=(op>>8)&7;x=regs[rd];y=op&255;value=(x-y)&MASK
    carry=int(x>=y);overflow=int(bool((x^y)&(x^value)&0x80000000))
    regs[rd]=value
    regs[15]=(regs[15]&0x0fffffff)|(value&0x80000000)|(int(value==0)<<30)|(carry<<29)|(overflow<<28)
    return (pc+2)&MASK


run=types.FunctionType(P.run.__code__,{**P.run.__globals__,'source_identity_guard':source_identity_guard,
    'validate_thumb':validate_thumb,'thumb_step':thumb_step},argdefs=P.run.__defaults__)
run.__kwdefaults__=P.run.__kwdefaults__
