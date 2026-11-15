"""Bounded parent recipes for the native header / modeled constructor split."""
from pathlib import Path
import types,hashlib
X=R=None
PINS={
 'species_caller':'4a08d1623b782c384fcf8d7936b55628b14bc47b7ea44dc1a321714ee9f5f05f',
 'narc_reader':'f21c05e1c12c8d7b77a5a18796c1a1da081ab5e3a0ae90b9856e5b2a8e29d42d',
 'message_caller':'f326503b432d74296c4983ae52dfe50a3a9298df2ce21acf4697a783c3a50632',
 'constructor_oracle':'0199a89927cbbcb08ed8f13d2a124380cd16da6c8b4dd7dacf6a4b43117d9090',
}
GENERIC_SHA256='b8d8819e366528c2d30dde0d0f45c0270ff9c0e3f00989868828af96643efc31'
def sha(blob):return hashlib.sha256(blob).hexdigest()
def need(ok,reason):
 if not ok:raise ValueError(reason)
def bind(caller,reader):
 global X,R
 need(sha(Path(caller.__file__).read_bytes())==PINS['species_caller'] and sha(Path(reader.__file__).read_bytes())==PINS['narc_reader'],'native header parent source drift');need(sha(Path(caller.A.__file__).read_bytes())==GENERIC_SHA256,'native header generic recipe source drift');X,R=caller,reader;X.V.A.bind(X.U)
def rewrite(module,function,edits,namespace,kind):
 need(X is not None,'bind native header parents first');scope=dict(vars(X.A));scope['PINS']={**X.A.PINS,**PINS};function_copy=types.FunctionType(X.A.rewrite.__code__,scope,X.A.rewrite.__name__,X.A.rewrite.__defaults__,X.A.rewrite.__closure__);return function_copy(module,function,edits,{**namespace,'__source_kind__':kind})
def adapt(bench,driver):
 need(X is not None,'native header adapter bound');run,proof=X.A.adapt(bench,driver);old=dict(run.__globals__['STUBS']);expected={k:v for k,v in bench.STUBS.items() if k!=0x200BCDC};need(old==expected and old.get(0x2007508)=='ReadWholeNarcMemberByIdPair','native header inherited effective SDK table drift');run.__globals__['STUBS']={k:v for k,v in old.items() if k!=0x2007508}
 return run,dict(schema='native-header-caller-adapter-v1',inherited=proof,removed_high_level_sdk={'0x2007508':'ReadWholeNarcMemberByIdPair'},effective_sdk={hex(k):v for k,v in run.__globals__['STUBS'].items()},isolated_namespace_only=True,constructor_read_backend='original nested B implementation dispatched once by owner; explicit PC=LR replaces removed BXLR',constructor_evidence_recipe=CONSTRUCTOR_RECIPE)

def constructor_result(*args):return X.V.A.constructor_result(*args)
# Set by the root's authenticated binding construction, before any CPU.
CONSTRUCTOR_RECIPE=None
constructor_evidence=None
