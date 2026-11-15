"""Finite move setter addition: aligned STRH register offset, no parent changes."""
from pathlib import Path
import hashlib
import importlib.util
import types


def load(path,name):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


P=load(Path(__file__).with_name('arm_thumb_box_setter_oracle.py'),'move_pinned_byte_setter_frontend')
A,need,MASK=P.A,P.need,P.MASK
PARENT_SHA='d2dcc979218ea25cc28752a3a7c892ea470e1bec486849c53f98c393d4e55583'


def source_identity_guard():
    need(hashlib.sha256(Path(P.__file__).read_bytes()).hexdigest()==PARENT_SHA,'pinned move setter frontend drift')
    P.source_identity_guard()


def validate_thumb(blob):
    need(type(blob)is bytes and len(blob)in(2,4),'complete finite move setter instruction')
    if len(blob)==2 and int.from_bytes(blob,'little')&0xfe00==0x5200:return 'strh_register'
    return P.validate_thumb(blob)


def thumb_step(pc,blob,regs,pages,reads,stores,read_guard=None,write_guard=None):
    if validate_thumb(blob)!='strh_register':
        return P.thumb_step(pc,blob,regs,pages,reads,stores,read_guard,write_guard)
    need(pc%2==0 and regs[15]&0x3f==0x3f,'Thumb System move setter state')
    op=int.from_bytes(blob,'little');address=(regs[(op>>3)&7]+regs[(op>>6)&7])&MASK
    need(address%2==0,'aligned Box move halfword domain')
    value=regs[op&7]&65535
    if write_guard:need(write_guard(pc,address,2),'Box move halfword owner/site')
    before=A.F.read(pages,address,2)
    stores.append(dict(pc=pc,address=address,bytes=2,before=before.hex(),value=value))
    A.F.put(pages,address,value.to_bytes(2,'little'));return (pc+2)&MASK


run=types.FunctionType(P.run.__code__,{**P.run.__globals__,'source_identity_guard':source_identity_guard,
    'validate_thumb':validate_thumb,'thumb_step':thumb_step},argdefs=P.run.__defaults__)
run.__kwdefaults__=P.run.__kwdefaults__
