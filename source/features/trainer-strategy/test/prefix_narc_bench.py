"""Finite parent recipes for the native party parser in its actual caller."""
from pathlib import Path
import types
Y=None
PARENT_SHA256='b599824891cd5e14b15272fd6c47df3f7d4209088f025c0e134b38e22cd89bfd'
ADAPTER_SHA256='19aeefbbedf42b3859995f9b8bf4be82c07e3cb404f2ab1bf3b4bf6f176b46c4'
def bind(parent):
 global Y
 parent.need(parent.sha(Path(parent.__file__).read_bytes())==PARENT_SHA256 and parent.sha(Path(parent.A.__file__).read_bytes())==ADAPTER_SHA256,'native prefix caller parent source drift');Y=parent

def rewrite(module,function,edits,namespace,kind):
 Y.need(Y is not None,'bind native prefix parent');scope=dict(vars(Y.X.A));scope['PINS']={**Y.X.A.PINS,**Y.A.PINS,'header_caller':PARENT_SHA256};fn=types.FunctionType(Y.X.A.rewrite.__code__,scope);return fn(module,function,edits,{**namespace,'__source_kind__':kind})

def inherited(index,extra=()):
 return [(e['before'],e['after'],e['count']) for e in Y.RECIPES[index]['edits']]+list(extra)

def adapt(bench,driver):
 run,proof=Y.A.adapt(bench,driver)
 return run,dict(schema='native-prefix-caller-adapter-v1',inherited=proof,effective_sdk=proof['effective_sdk'],constructor_evidence_recipe=CONSTRUCTOR_RECIPE,prefix_owner='native parser with five FS models; no high-level party56 callback or fabricated event')
def constructor_result(*args):return Y.A.constructor_result(*args)
constructor_evidence=None
CONSTRUCTOR_RECIPE=None
