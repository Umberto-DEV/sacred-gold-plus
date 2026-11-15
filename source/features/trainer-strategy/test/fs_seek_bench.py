"""Authenticated composition for native Seek and a declared property projection."""
from pathlib import Path
import types
PARENT_SHA256='2886dfb1262c4e091254bc56fbc020997e03f7fabcbbf460da1362a4932ebefc'
ADAPTER_SHA256='88ac8f7976a749678b6f752ac4d7d33ba5dac36b6f5f6c5f97430fe1f475e7c5'


def bind(parent):
    parent.need(parent.sha(Path(parent.__file__).read_bytes())==PARENT_SHA256 and
        parent.sha(Path(parent.A.__file__).read_bytes())==ADAPTER_SHA256,'Seek Close-parent source drift')


def rewrite(parent,module,function,edits,namespace,kind):
    engine=parent.H.H.H.O.H.X.A
    pins={'fs_close_caller':PARENT_SHA256,'fs_fast_caller':parent.A.PARENT_SHA256,
        'fs_convert_caller':'cda419aee381e5647a07868cf6ec34688d4dab2eddd824b463e00600215df829',
        'fs_open_caller':'b8cdc185cb618790d2eb40a7a5ed7f455aeb7064a50729b07ad47ba3b9630e64',
        'fs_init_caller':'691b7c423019b92cda65259e124829a92579b181582056b946312f3904feeef8',
        'pp_caller':'7294d729b42b81ebc9dd180d485ff8ad5c170d94191d8d483d9d6d1e2dad999f',
        'narc_reader':'f21c05e1c12c8d7b77a5a18796c1a1da081ab5e3a0ae90b9856e5b2a8e29d42d',
        'message_caller':'f326503b432d74296c4983ae52dfe50a3a9298df2ce21acf4697a783c3a50632'}
    return types.FunctionType(engine.rewrite.__code__,{**vars(engine),'PINS':pins})(module,function,edits,
        {**namespace,'__source_kind__':kind})


def edits(recipe):return [(e['before'],e['after'],e['count'])for e in recipe['edits']]


def clone(fn,namespace):
    result=types.FunctionType(fn.__code__,{**fn.__globals__,**namespace},fn.__name__,fn.__defaults__,fn.__closure__)
    result.__kwdefaults__=fn.__kwdefaults__;return result
