"""Explicit historical r4 helper identity for the attribution tools.

The shared geometry is unchanged; the archived source, compiler offsets and
payload pin here identify the old 1.3.2 helper, never the current candidate.
"""
from . import uturn_flinch as _current

NATIVE = _current.SOURCE / 'features/type-consumers/uturn-r4.S'
HELPER_BYTES = 68
HELPER_SHA256 = '8dfc3389b012ba046fd81df9c4a79119d1ffa4bf044b2462720a1868e0ea7f02'
EFFECT_LIVE_CALL = 24
MODIFIER_LIVE_CALL = 62


def compile_native(work_dir, *, retain_object=False):
    return _current._compile_native(
        work_dir, retain_object=retain_object, source_path=NATIVE,
        helper_bytes=HELPER_BYTES, helper_sha256=HELPER_SHA256,
        effect_live_call=EFFECT_LIVE_CALL, modifier_live_call=MODIFIER_LIVE_CALL)


def __getattr__(name):
    return getattr(_current, name)
