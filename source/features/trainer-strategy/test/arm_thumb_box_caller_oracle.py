"""Locally bounded complete caller oracle; earlier interpreters stay immutable.

Only the outer limit and ARM residual cap change. No new ISA, DIV arguments,
return handling, memory access semantics or synthetic service is admitted.
"""
from pathlib import Path
import ast
import hashlib
import importlib.util
import inspect
import types


def load(path,name):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


P=load(Path(__file__).with_name('arm_thumb_box_move_oracle.py'),'caller_pinned_move_frontend')
BASE=load(Path(__file__).with_name('arm_thumb_maxpp_oracle.py'),'caller_pinned_mixed_loop')
need=P.need
PARENT_SHA='c47b0e28c4e89c5b56837c6c9891b02e9f4a72d8b0b0412c4c78cfa883803bea'
BASE_SHA='8fd915dfabd9cce1d7fa497efbc6125d468f4f3698843c1af825890915d0d053'
CAP=32768


def audit_source_delta():
    old=ast.parse(inspect.getsource(BASE.run));new=ast.parse(inspect.getsource(_run_source))
    old.body[0].name=new.body[0].name='normalized_run'
    changes=0
    class Delta(ast.NodeTransformer):
        def visit_Constant(self,node):
            nonlocal changes
            if type(node.value)is int and node.value==8192:changes+=1;return ast.copy_location(ast.Constant(32768),node)
            return node
        def visit_keyword(self,node):
            nonlocal changes
            node=self.generic_visit(node)
            if node.arg=='cap' and isinstance(node.value,ast.BinOp)and ast.unparse(node.value)=='cap - len(flow)':
                changes+=1;node.value=ast.Call(func=ast.Name(id='min',ctx=ast.Load()),args=[ast.Constant(8192),node.value],keywords=[])
            return node
    old=Delta().visit(old)
    need(changes==3 and ast.dump(old,include_attributes=False)==ast.dump(new,include_attributes=False),'exact caller three-node source delta')
    return changes


def source_identity_guard():
    for module,digest in((P,PARENT_SHA),(BASE,BASE_SHA)):
        need(hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest()==digest,'pinned complete caller predictor drift')
    P.source_identity_guard();audit_source_delta()


def _run_source(f,code_spans,stop,cap=32768,read_guard=None,write_guard=None,*,thumb_code):
    source_identity_guard()
    need(type(cap)is int and 0<cap<=32768,'finite mixed instruction cap')
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
                          cap=min(8192,cap-len(flow)),read_guard=read_guard,write_guard=write_guard)
            low=min(low,regs[13]-segment['native_peak'])
            flow.extend(segment['flow']);reads.extend(segment['reads']);stores.extend(segment['stores'])
            regs=segment['returned'];pages={a:bytearray(b)for a,b in segment['pages'].items()}
            need(len(flow)<cap and A.F.read(pages,ret,4)==word.to_bytes(4,'little'),'qualified ARM return bytes/budget')
            flow.append(dict(pc=ret,regs=list(regs)))
            pc=arm_return(ret,word,regs,pages,reads,read_guard)
    return dict(flow=flow,reads=reads,stores=stores,returned=list(regs),stop_pc=pc,
                native_peak=initial_sp-low,pages={a:bytes(b)for a,b in pages.items()})

run=types.FunctionType(_run_source.__code__,{**P.run.__globals__,'source_identity_guard':source_identity_guard},argdefs=_run_source.__defaults__)
run.__kwdefaults__=_run_source.__kwdefaults__
