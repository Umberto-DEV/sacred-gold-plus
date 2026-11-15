"""Authenticated Open-wrapper extension; immutable parent source namespaces."""
from pathlib import Path
import types

PARENT_SHA256 = '691b7c423019b92cda65259e124829a92579b181582056b946312f3904feeef8'
ADAPTER_SHA256 = 'c8929d35012b0aa861177a34edb9421484cbc5a0b1f18b150c6cd9d463d4e8ab'


def bind(parent):
    parent.need(parent.sha(Path(parent.__file__).read_bytes()) == PARENT_SHA256 and
                parent.sha(Path(parent.A.__file__).read_bytes()) == ADAPTER_SHA256,
                'Open Init-parent source drift')
    return parent


def rewrite(parent, module, function, edits, namespace, kind):
    scope = dict(vars(parent.H.X.A))
    scope['PINS'] = {'fs_init_caller': PARENT_SHA256,
        'pp_caller': parent.A.PARENT_SHA256,
        'narc_reader': 'f21c05e1c12c8d7b77a5a18796c1a1da081ab5e3a0ae90b9856e5b2a8e29d42d',
        'message_caller': 'f326503b432d74296c4983ae52dfe50a3a9298df2ce21acf4697a783c3a50632'}
    fn = types.FunctionType(parent.H.X.A.rewrite.__code__, scope)
    return fn(module, function, edits, {**namespace, '__source_kind__': kind})


def edits(parent, index):
    return [(e['before'], e['after'], e['count']) for e in parent.RECIPES[index]['edits']]


def clone(fn, namespace):
    result = types.FunctionType(fn.__code__, {**fn.__globals__, **namespace}, fn.__name__, fn.__defaults__, fn.__closure__)
    result.__kwdefaults__ = fn.__kwdefaults__
    return result
