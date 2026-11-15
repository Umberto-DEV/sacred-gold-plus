"""Finite native NARC3 table profile and caller recipes; parents stay immutable."""
from pathlib import Path
import types
J=None
PARENT_SHA256='a07a8032c6fd277b5d8cc82f8c187ddf5e88c4d66adaf1a935b8b8b59bae9ab9'
ADAPTER_SHA256='888d89c473aac62424a473f95fba9ad8eac7c5f91bc9640f508c371c9cdb9c0c'
def bind(parent):
 global J
 parent.need(parent.sha(Path(parent.__file__).read_bytes())==PARENT_SHA256 and parent.sha(Path(parent.A.__file__).read_bytes())==ADAPTER_SHA256,'growth parent source drift');J=parent

def rewrite(module,function,edits,namespace,kind):
 J.need(J is not None,'bind growth parent');scope=dict(vars(J.X.A));scope['PINS']={**J.X.A.PINS,**J.Y.A.PINS,'header_caller':J.Z.A.PARENT_SHA256,'prefix_caller':J.A.PARENT_SHA256,'personal_caller':PARENT_SHA256};fn=types.FunctionType(J.X.A.rewrite.__code__,scope);return fn(module,function,edits,{**namespace,'__source_kind__':kind})
def inherited(index,extra=()):return [(e['before'],e['after'],e['count']) for e in J.RECIPES[index]['edits']]+list(extra)
def adapt(bench,driver):
 run,proof=J.A.adapt(bench,driver);return run,dict(schema='native-growth-caller-adapter-v1',inherited=proof,effective_sdk=proof['effective_sdk'],native_owner='first growth NARC3/4 only, explicit counter2; no fabricated high-level read model/event')
def constructor_result(*args):return J.A.constructor_result(*args)
def constructor_evidence(*args):return J.A.constructor_evidence(*args)
