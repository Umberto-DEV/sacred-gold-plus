"""Authenticated, finite NARC2/355 profile of the qualified native reader."""
from pathlib import Path
import types
Z=None
PARENT_SHA256='d089fa726c1047a4448bf9ee018849d5a6dbe0684934b8b2a51ba7451d798d72'
ADAPTER_SHA256='78b4bdc1832553e4d1aeeda0d809dd5b5b97d9fcb53c199cebed722fa48e9166'
def bind(parent):
 global Z
 parent.need(parent.sha(Path(parent.__file__).read_bytes())==PARENT_SHA256 and parent.sha(Path(parent.A.__file__).read_bytes())==ADAPTER_SHA256,'personal reader parent source drift');Z=parent

def rewrite(module,function,edits,namespace,kind):
 Z.need(Z is not None,'bind personal reader parent');scope=dict(vars(Z.X.A));scope['PINS']={**Z.X.A.PINS,**Z.Y.A.PINS,'header_caller':Z.A.PARENT_SHA256,'prefix_caller':PARENT_SHA256};fn=types.FunctionType(Z.X.A.rewrite.__code__,scope);return fn(module,function,edits,{**namespace,'__source_kind__':kind})
def inherited(index,extra=()):return [(e['before'],e['after'],e['count']) for e in Z.RECIPES[index]['edits']]+list(extra)
def adapt(bench,driver):
 run,proof=Z.A.adapt(bench,driver);return run,dict(schema='native-personal-caller-adapter-v1',inherited=proof,effective_sdk=proof['effective_sdk'],native_owner='first body NARC2/355 only; no high-level read event or model fabricated')
def constructor_result(*args):return Z.A.constructor_result(*args)
def constructor_evidence(*args):return Z.A.constructor_evidence(*args)
