"""Authenticated source composition and namespace bindings for native OpenFast."""
from pathlib import Path
import types
PARENT_SHA256='cda419aee381e5647a07868cf6ec34688d4dab2eddd824b463e00600215df829'
ADAPTER_SHA256='38a7e122040f0de0564e3665dc3ecdcbc1105d4f88e283a84129a83abb07c86f'


def bind(parent):
    parent.need(parent.sha(Path(parent.__file__).read_bytes())==PARENT_SHA256 and
        parent.sha(Path(parent.A.__file__).read_bytes())==ADAPTER_SHA256,'Fast Convert-parent source drift')


def rewrite(parent,module,function,edits,namespace,kind):
    engine=parent.H.O.H.X.A
    scope={**vars(engine),'PINS':{'fs_convert_caller':PARENT_SHA256,
        'fs_open_caller':parent.A.PARENT_SHA256,'fs_init_caller':'691b7c423019b92cda65259e124829a92579b181582056b946312f3904feeef8',
        'pp_caller':'7294d729b42b81ebc9dd180d485ff8ad5c170d94191d8d483d9d6d1e2dad999f',
        'narc_reader':'f21c05e1c12c8d7b77a5a18796c1a1da081ab5e3a0ae90b9856e5b2a8e29d42d',
        'message_caller':'f326503b432d74296c4983ae52dfe50a3a9298df2ce21acf4697a783c3a50632'}}
    return types.FunctionType(engine.rewrite.__code__,scope)(module,function,edits,{**namespace,'__source_kind__':kind})


def edits(recipe):return [(e['before'],e['after'],e['count'])for e in recipe['edits']]


def clone(fn,namespace):
    result=types.FunctionType(fn.__code__,{**fn.__globals__,**namespace},fn.__name__,fn.__defaults__,fn.__closure__)
    result.__kwdefaults__=fn.__kwdefaults__;return result
