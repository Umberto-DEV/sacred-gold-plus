"""Owned dispatcher qualification on the retained source and CPU interpreters.

Adds only register BLX r3 with an odd Thumb target to the source interpreter.
The retained CPU producer has two audited cap constants reduced65536→64.
No ROM, original API, service model or runtime host write is involved.
"""
from pathlib import Path
import ast
import copy
import hashlib
import importlib.util
import inspect
import struct
import types


def load(path,name):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


HERE=Path(__file__).resolve();SOURCE=HERE.parents[3];PARENT=SOURCE/'features/trainer-strategy'
BUILD=load(HERE.parents[1]/'tools/compila_shellbell_dispatch.py','owned_dispatch_build')
A=load(PARENT/'test/arm_thumb_mon_reset_oracle.py','owned_dispatch_retained_source')
C=load(PARENT/'test/mon_reset_cpu.py','owned_dispatch_retained_CPU')
Q=load(PARENT/'tools/qualifica_box_move_caller.py','owned_dispatch_retained_owned_runner')
M,need=Q.M,Q.need
PINNED={A:'f69e8a044f13d46c0ed7e69597958c03bd8d1ce863f7c4cc38bc9501dab29789',C:'ee7b5a82dc57e50740e43ac10cc9677ef6f310f7a5cfa678aceda92962f13382',Q:'82932767324749607c66d8cf59254aba24ada36a21459c26a53b0f4525c36901'}
BASE,TABLE=BUILD.BASE,BUILD.TABLE
CTX,BS,TOP,STOP=0x02380000,0x02370000,0x023B8000,BASE+0x100
parent_validate=A.run.__globals__['validate_thumb'];parent_step=A.run.__globals__['thumb_step']


def source_identity_guard():
    for module,digest in PINNED.items():need(hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest()==digest,'retained dispatcher qualification dependency')
    A.source_identity_guard();C.source_identity_guard()


def validate_thumb(blob):
    if type(blob)is bytes and len(blob)==2:
        op=int.from_bytes(blob,'little')
        if op&0xff87==0x4780:
            need(op==0x4798,'only owned register BLX r3 is added');return 'owned_BLX_r3'
    return parent_validate(blob)


def thumb_step(pc,blob,regs,pages,reads,stores,read_guard=None,write_guard=None):
    if validate_thumb(blob)!='owned_BLX_r3':return parent_step(pc,blob,regs,pages,reads,stores,read_guard,write_guard)
    need(type(pc)is int and pc%2==0 and 0<=pc<=0xfffffffc and regs[15]&0x3f==0x3f,'owned BLX Thumb System state')
    target=regs[3];need(type(target)is int and 0<=target<=0xffffffff and target&1,'owned BLX requires odd Thumb target')
    regs[14]=(pc+2)|1
    return target&~1


def kernel(text=None):
    text=BUILD.own_text()if text is None else text
    BUILD.validate_text(text,{name:BASE+value for name,value,_ in BUILD.FUNCTIONS})
    code={BASE+i:text[i:i+2]for i in(*range(0,28,2),*range(32,44,2))}
    pages={address:bytearray(b'\xa5'*4096)for address in(BASE&~4095,TABLE&~4095,CTX,TOP-4096)}
    M.put(pages,BASE,text);M.put(pages,CTX+8,struct.pack('<I',28))
    M.put(pages,TABLE+28*4,struct.pack('<I',BASE+33));M.put(pages,TABLE+29*4,struct.pack('<I',BASE+39))
    regs=[0xA0000000+i*0x10101 for i in range(13)]+[TOP,STOP|1,0x6000003f];regs[:2]=[BS,CTX]
    return dict(entry_pc=BASE,entry_regs=regs,pages={a:bytes(b)for a,b in pages.items()}),code,(),STOP


def hard_forecast(k):
    """Independent32-step control ledger, not a Thumb instruction decoder."""
    f,code,spans,stop=k;need(k==kernel(),'exact authored owned kernel')
    r=list(f['entry_regs']);initial=list(r);pages={a:bytearray(b)for a,b in f['pages'].items()};flow=[];reads=[];stores=[]
    def emit(offset):flow.append(dict(pc=BASE+offset,regs=list(r)))
    def read(offset,address):
        data=M.read(pages,address,4);reads.append(dict(pc=BASE+offset,address=address,bytes=4,hex=data.hex()));return struct.unpack('<I',data)[0]
    def write(pc,address,value):
        before=M.read(pages,address,4);stores.append(dict(pc=BASE+pc,address=address,bytes=4,before=before.hex(),value=value));M.put(pages,address,struct.pack('<I',value))
    emit(0);r[13]-=16
    for i,value in enumerate([initial[4],initial[5],initial[6],initial[14]]):write(0,r[13]+4*i,value)
    emit(2);r[4]=BS;r[15]=0x3f
    emit(4);r[5]=CTX;r[15]=0x3f
    emit(6);r[6]=read(6,BASE+28)
    for command,handler in((28,32),(29,38)):
        emit(8);r[2]=read(8,CTX+8);need(r[2]==command,'owned hard command sequence')
        emit(10);r[15]=0x8000003f
        emit(12)
        emit(14);r[2]=command*4;r[15]=0x3f
        emit(16);r[3]=read(16,TABLE+4*command);need(r[3]==BASE+handler+1,'owned hard table pointer')
        emit(18);r[0]=BS;r[15]=0x3f
        emit(20);r[1]=CTX;r[15]=0x3f
        emit(22);r[14]=BASE+25
        emit(handler);r[0]=29 if command==28 else 39;r[15]=0x3f
        emit(handler+2);write(handler+2,CTX+8,r[0])
        emit(handler+4)
        emit(24)
    emit(8);r[2]=read(8,CTX+8)
    emit(10);r[15]=0x6000003f
    emit(12)
    emit(26)
    for i,reg in enumerate((4,5,6)):r[reg]=read(26,r[13]+4*i)
    need(read(26,r[13]+12)==stop|1,'owned hard POP return');r[13]+=16
    return dict(flow=flow,reads=reads,stores=stores,returned=r,stop_pc=stop,native_peak=16,pages={a:bytes(b)for a,b in pages.items()})


def forecast(k):
    source_identity_guard();globals={**A.run.__globals__,'validate_thumb':validate_thumb,'thumb_step':thumb_step}
    fn=types.FunctionType(A.run.__code__,globals,argdefs=A.run.__defaults__);fn.__kwdefaults__=A.run.__kwdefaults__
    f,code,spans,stop=k;p=fn(f,spans,stop,cap=64,thumb_code=code)
    need(BUILD.exact(p,hard_forecast(k)),'independent full16/control/access/preimage/page ledger');return p


def bounded_bind(**geometry):
    original=C.bind(**geometry);tree=ast.parse(inspect.getsource(C._run_cpu));changed=0
    class ReduceCap(ast.NodeTransformer):
        def visit_Constant(self,node):
            nonlocal changed
            if type(node.value)is int and node.value==65536:changed+=1;return ast.copy_location(ast.Constant(64),node)
            return node
    tree=ReduceCap().visit(tree);need(changed==2,'only two retained CPU cap constants reduced to64')
    space=dict(original.__globals__);exec(compile(ast.fix_missing_locations(tree),'<owned-dispatch-cap64>','exec'),space)
    return space['_run_cpu']


def execute(k,p,observe):
    source_identity_guard()
    fn=types.FunctionType(Q.execute.__code__,{**Q.execute.__globals__,'C':types.SimpleNamespace(bind=bounded_bind)},argdefs=Q.execute.__defaults__)
    return fn(k,p,observe)


def synthetic_raw(p,observe):
    """Explicitly fabricated source-shaped input for pure mutation tests only."""
    f=kernel()[0]
    initial=dict(entry_pc=f['entry_pc'],entry_regs=copy.deepcopy(f['entry_regs']),initial_map_sha256=M.map_digest(f['pages']))
    return dict(schema='native-fs-memory-narc-raw-v1',initial=initial,backend=copy.deepcopy(C.P.run.__globals__['BACKEND']),fault=None,stopped=True,observed=observe,models=[],runtime_host_writes=[],stop_pc=p['stop_pc'],returned=copy.deepcopy(p['returned']),
        executed_count=32,callback_count=33,ARM_count=0,Thumb_count=32,unique_executed_starts=20,read_count=10,store_count=6,stack_peak=16,
        flow=copy.deepcopy(p['flow'])if observe else[],reads=copy.deepcopy(p['reads'])if observe else[],stores=copy.deepcopy(p['stores'])if observe else[],
        final_pages=[dict(ram=a,hex=b.hex())for a,b in sorted(p['pages'].items())],final_map_sha256=M.map_digest(p['pages']))


def check_raw(raw,p,observe):
    need(type(observe)is bool,'owned observer selection');C.require_completion(raw,32)
    expected=synthetic_raw(p,observe)
    need(type(raw)is dict and set(raw)==set(expected),'owned raw exact envelope fields')
    for key,value in expected.items():need(BUILD.exact(raw[key],value),'owned dispatcher typed raw '+key)
    return dict(observed=observe,instructions=32,callbacks=33,static_starts=20,reads=10,stores=6,frame_bytes=16,all_pages=True,final_map_sha256=raw['final_map_sha256'])
