"""Finite MaxPP Thumb additions and an explicitly scoped signed-DIV router.

The NARC loop is retained except for its identity guard and ARM selector.
SDK segments use the original ARM oracle; only the authenticated DIV corpus
uses RSB/ADC arithmetic. The actual CPU producer has no segmented execution.
"""
from pathlib import Path
import hashlib
import importlib.util
import types


def load(path,name):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


P=load(Path(__file__).with_name('arm_thumb_pp_oracle.py'),'maxPP_pinned_PP_frontend')
D=load(Path(__file__).with_name('arm32_div_oracle.py'),'maxPP_scoped_DIV_arithmetic')
A,need,MASK=P.A,P.need,P.MASK
PARENT_SHA=P.PARENT_SHA
FRONTEND_SHA=P.FRONTEND_SHA
PP_FRONTEND_SHA='1930abd1a993c9f8945ba179c59a359ca0fe14815963b15a450cfd98f4a1d71b'
DIV_ORACLE_SHA='a73b6128514f76ca46fc710e3cee51f6881a35bc6b817ba34dbc65e710284559'
DIV_ENTRY,DIV_RETURN=0x20f2998,0x20f2ba0
RETURNS={**P.RETURNS,DIV_ENTRY:(DIV_RETURN,0xe12fff1e)}
exchange=P.exchange
arm_return=types.FunctionType(P.P.arm_return.__code__,{**vars(P.P),'RETURNS':RETURNS},argdefs=P.P.arm_return.__defaults__)


def source_identity_guard():
    for path,digest in((Path(P.__file__),PP_FRONTEND_SHA),(Path(P.P.__file__),FRONTEND_SHA),
                        (Path(A.__file__),PARENT_SHA),(Path(D.__file__),DIV_ORACLE_SHA)):
        need(hashlib.sha256(path.read_bytes()).hexdigest()==digest,'pinned MaxPP predictor dependency drift')


def select_arm(pc,regs,code_spans):
    need(pc in RETURNS,'qualified MaxPP ARM entry only')
    if pc==DIV_ENTRY:
        need(type(regs[0])is int and type(regs[1])is int and regs[0]in(0,60,900)and regs[1]==100,'finite native division arguments')
        return D,((DIV_ENTRY,524),)
    return A,code_spans


def validate_thumb(blob):
    need(type(blob)is bytes and len(blob)in(2,4),'complete finite Thumb instruction')
    if len(blob)==2:
        op=int.from_bytes(blob,'little')
        if op&0xffc0==0x4340:
            need(((op>>3)&7)!=(op&7),'ARMv5 MUL register alias is outside defined domain')
            return 'mul'
        if op&0xf800==0x0800:return 'lsr'
        if op&0xff00==0xd900:return 'bls'
    return P.validate_thumb(blob)


def thumb_step(pc,blob,regs,pages,reads,stores,read_guard=None,write_guard=None):
    kind=validate_thumb(blob)
    if kind not in('mul','lsr','bls'):
        return P.thumb_step(pc,blob,regs,pages,reads,stores,read_guard,write_guard)
    need(pc%2==0 and regs[15]&0x3f==0x3f,'Thumb System instruction state')
    op=int.from_bytes(blob,'little');nxt=pc+2
    if kind=='mul':
        rd,rm=op&7,(op>>3)&7;value=(regs[rd]*regs[rm])&MASK
        regs[rd]=value;regs[15]=(regs[15]&0x3fffffff)|(value&0x80000000)|(int(value==0)<<30)
    elif kind=='lsr':
        rd,rm,amount=op&7,(op>>3)&7,(op>>6)&31
        value,carry=A.shifted(regs[rm],1,amount,(regs[15]>>29)&1)
        regs[rd]=value;regs[15]=A.nzcv(regs[15],value,carry,bool(regs[15]&0x10000000))
    else:
        delta=op&255
        if delta&128:delta-=256
        if A.condition(9,regs[15]):nxt=(pc+4+2*delta)&MASK
    return nxt


def run(f,code_spans,stop,cap=8192,read_guard=None,write_guard=None,*,thumb_code):
    source_identity_guard()
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
            interpreter,selected_spans=select_arm(pc,regs,code_spans)
            segment=interpreter.run(dict(entry_pc=pc,entry_regs=regs,pages=pages),selected_spans,ret,
                          cap=cap-len(flow),read_guard=read_guard,write_guard=write_guard)
            low=min(low,regs[13]-segment['native_peak'])
            flow.extend(segment['flow']);reads.extend(segment['reads']);stores.extend(segment['stores'])
            regs=segment['returned'];pages={a:bytearray(b)for a,b in segment['pages'].items()}
            need(len(flow)<cap and A.F.read(pages,ret,4)==word.to_bytes(4,'little'),'qualified ARM return bytes/budget')
            flow.append(dict(pc=ret,regs=list(regs)))
            pc=arm_return(ret,word,regs,pages,reads,read_guard)
    return dict(flow=flow,reads=reads,stores=stores,returned=list(regs),stop_pc=pc,
                native_peak=initial_sp-low,pages={a:bytes(b)for a,b in pages.items()})
