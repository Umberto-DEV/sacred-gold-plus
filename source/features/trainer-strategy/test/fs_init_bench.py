"""Source-authenticated extension of the finite PP caller, without parent edits."""
import types
from pathlib import Path

PARENT_SHA256 = '7294d729b42b81ebc9dd180d485ff8ad5c170d94191d8d483d9d6d1e2dad999f'
ADAPTER_SHA256 = 'd607890286b41fa1bdb16edf75e791c457e49004cde413729d034f7ff6a29d62'


def bind(parent):
    parent.need(parent.sha(Path(parent.__file__).read_bytes()) == PARENT_SHA256 and
                parent.sha(Path(parent.A.__file__).read_bytes()) == ADAPTER_SHA256,
                'FS Init PP parent source drift')
    return parent


def rewrite(parent, module, function, edits, namespace, kind):
    scope = dict(vars(parent.X.A))
    scope['PINS'] = {'pp_caller': PARENT_SHA256,
                     'narc_reader': 'f21c05e1c12c8d7b77a5a18796c1a1da081ab5e3a0ae90b9856e5b2a8e29d42d',
                     'message_caller': 'f326503b432d74296c4983ae52dfe50a3a9298df2ce21acf4697a783c3a50632'}
    fn = types.FunctionType(parent.X.A.rewrite.__code__, scope)
    return fn(module, function, edits, {**namespace, '__source_kind__': kind})


def edits(parent, index):
    return [(e['before'], e['after'], e['count']) for e in parent.RECIPES[index]['edits']]


def clone(fn, namespace):
    result = types.FunctionType(fn.__code__, {**fn.__globals__, **namespace},
                                fn.__name__, fn.__defaults__, fn.__closure__)
    result.__kwdefaults__ = fn.__kwdefaults__
    return result
