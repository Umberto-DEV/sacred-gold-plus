"""Finite Box setter addition: STRB immediate5, preserving its pinned parent."""
from pathlib import Path
import hashlib
import importlib.util
import types


def load(path,name):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


P=load(Path(__file__).with_name('arm_thumb_box_oracle.py'),'setter_pinned_box_frontend')
A,need,MASK=P.A,P.need,P.MASK
PARENT_SHA='928ad971af08036008a04fca2dbdcc6c88aad0d0354be119be0a130763cfc64d'


def source_identity_guard():
    need(hashlib.sha256(Path(P.__file__).read_bytes()).hexdigest()==PARENT_SHA,'pinned Box setter frontend drift')
    P.source_identity_guard()


def validate_thumb(blob):
    need(type(blob)is bytes and len(blob)in(2,4),'complete finite Box setter instruction')
    if len(blob)==2 and int.from_bytes(blob,'little')&0xf800==0x7000:return 'strb_imm5'
    return P.validate_thumb(blob)


def thumb_step(pc,blob,regs,pages,reads,stores,read_guard=None,write_guard=None):
    if validate_thumb(blob)!='strb_imm5':
        return P.thumb_step(pc,blob,regs,pages,reads,stores,read_guard,write_guard)
    need(pc%2==0 and regs[15]&0x3f==0x3f,'Thumb System Box setter state')
    op=int.from_bytes(blob,'little');address=(regs[(op>>3)&7]+((op>>6)&31))&MASK
    value=regs[op&7]&255
    if write_guard:need(write_guard(pc,address,1),'Box setter byte owner/site')
    before=A.F.read(pages,address,1)
    stores.append(dict(pc=pc,address=address,bytes=1,before=before.hex(),value=value))
    A.F.put(pages,address,bytes([value]));return (pc+2)&MASK


run=types.FunctionType(P.run.__code__,{**P.run.__globals__,'source_identity_guard':source_identity_guard,
    'validate_thumb':validate_thumb,'thumb_step':thumb_step},argdefs=P.run.__defaults__)
run.__kwdefaults__=P.run.__kwdefaults__
