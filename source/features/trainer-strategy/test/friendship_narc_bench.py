"""Finite second personal-read context and source-authenticated caller recipes."""
from pathlib import Path
import types
G=None
PARENT_SHA256='c8f73b9b121575a12e27cd422e3935bf79f581b87eb85e4544caf977fa5ca525'
ADAPTER_SHA256='9b1590789982ee65d2e41cd6be66a535834755d7674ad201f6bf6be9eb4b80bd'
def bind(parent):
 global G
 parent.need(parent.sha(Path(parent.__file__).read_bytes())==PARENT_SHA256 and parent.sha(Path(parent.A.__file__).read_bytes())==ADAPTER_SHA256,'friendship parent source drift');G=parent

def rewrite(module,function,edits,namespace,kind):
 G.need(G is not None,'bind friendship parent');scope=dict(vars(G.X.A));scope['PINS']={**G.X.A.PINS,**G.Y.A.PINS,'header_caller':G.Z.A.PARENT_SHA256,'prefix_caller':G.J.A.PARENT_SHA256,'personal_caller':G.A.PARENT_SHA256,'growth_caller':PARENT_SHA256};fn=types.FunctionType(G.X.A.rewrite.__code__,scope);return fn(module,function,edits,{**namespace,'__source_kind__':kind})
def inherited(index,extra=()):return [(e['before'],e['after'],e['count']) for e in G.RECIPES[index]['edits']]+list(extra)
def adapt(bench,driver):
 run,proof=G.A.adapt(bench,driver);return run,dict(schema='native-friendship-caller-adapter-v1',inherited=proof,effective_sdk=proof['effective_sdk'],native_owner='second NARC2/355 read for initial friendship only; no synthetic read event/model or checkpoint bridge')
def constructor_result(*args):return G.A.constructor_result(*args)
def constructor_evidence(*args):return G.A.constructor_evidence(*args)
