"""Immutable-source composition for the local-directory Convert wrapper."""
from pathlib import Path
import types

PARENT_SHA256='b8cdc185cb618790d2eb40a7a5ed7f455aeb7064a50729b07ad47ba3b9630e64'
ADAPTER_SHA256='5ba8c6232951288a3370f53b4db217ba543872bc7e108547c3ab0593e9f25849'


def bind(parent):
    parent.need(parent.sha(Path(parent.__file__).read_bytes())==PARENT_SHA256 and
                parent.sha(Path(parent.A.__file__).read_bytes())==ADAPTER_SHA256,
                'Convert Open-parent source drift')
    return parent


def rewrite(parent,module,function,edits,namespace,kind):
    engine=parent.O.H.X.A
    scope={**vars(engine),'PINS':{
        'fs_open_caller':PARENT_SHA256,
        'fs_init_caller':'691b7c423019b92cda65259e124829a92579b181582056b946312f3904feeef8',
        'pp_caller':'7294d729b42b81ebc9dd180d485ff8ad5c170d94191d8d483d9d6d1e2dad999f',
        'narc_reader':'f21c05e1c12c8d7b77a5a18796c1a1da081ab5e3a0ae90b9856e5b2a8e29d42d',
        'message_caller':'f326503b432d74296c4983ae52dfe50a3a9298df2ce21acf4697a783c3a50632'}}
    fn=types.FunctionType(engine.rewrite.__code__,scope)
    return fn(module,function,edits,{**namespace,'__source_kind__':kind})


def edits(recipe):
    return [(e['before'],e['after'],e['count'])for e in recipe['edits']]


def clone(fn,namespace):
    result=types.FunctionType(fn.__code__,{**fn.__globals__,**namespace},fn.__name__,fn.__defaults__,fn.__closure__)
    result.__kwdefaults__=fn.__kwdefaults__
    return result
