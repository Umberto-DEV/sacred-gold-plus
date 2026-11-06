"""Local HG-T10 guard for the Bell Tower legendary reveal script.

Only member 21 of ``a/0/1/2`` is transformed.  When the Ho-Oh hide flag is
already clear, map loading has already materialized object ID 5, so the script
skips the inherited ``ClearFlag; ShowPerson`` pair and continues at
``MakeObjectVisible``.  The global ShowPerson consumer and Lugia member 104 are
not changed.
"""
import hashlib

from . import gifts_scripts as G
from .legacy_scripts import _edit, _preserved, _sequence


ARCHIVE = 'a/0/1/2'
MEMBER = 21
METADATA_SHA256 = 'fbfbf438104cfc3735c3144730ed711bb882fca370a8de680db5c1d39ffaca5a'
PREIMAGE_SHA256 = 'cccdd680958b2d3da9cf700a6fffa4ce079eb4a8664345934fac150da038c609'
POSTIMAGE_SHA256 = '8907965e5f6afea59b82f940901e49e5dbad0d15b23e8d2aa3cdd66e570e394c'
SITE, CONTINUATION = 0x67E, 0x686
HIDE_FLAG, OBJECT_ID = 0x242, 5


def _need(condition, reason):
    if not condition:
        raise ValueError('legendary scenes: ' + reason)


def _before(raw, commands):
    _need(type(raw) is bytes, 'member bytes')
    _need(len(commands) == 853
          and getattr(commands, 'metadata_sha256', None) == METADATA_SHA256,
          'command metadata differs from the pinned reference')
    _need(hashlib.sha256(raw).hexdigest() == PREIMAGE_SHA256,
          'member 21 preimage differs: foreign or already patched input')
    parsed = G.decode(raw, commands, MEMBER)
    clear = parsed.istruzioni.get(SITE)
    show = parsed.istruzioni.get(SITE + 4)
    visible = parsed.istruzioni.get(CONTINUATION)
    _need(clear is not None and clear.nome == 'ClearFlag'
          and clear.args == [HIDE_FLAG] and clear.fine == SITE + 4,
          'inherited Ho-Oh ClearFlag differs')
    _need(show is not None and show.nome == 'ShowPerson'
          and show.args == [OBJECT_ID] and show.fine == CONTINUATION,
          'inherited Ho-Oh ShowPerson differs')
    _need(visible is not None and visible.nome == 'MakeObjectVisible'
          and visible.args == [OBJECT_ID],
          'inherited Ho-Oh continuation differs')
    return parsed


def patch_member(raw, commands):
    """Return the guarded member; reject foreign metadata and member bytes."""
    _before(raw, commands)
    # The second conditional targets its own fallthrough.  It is semantically
    # inert on the create path and makes the replacement delta even, preserving
    # halfword alignment of every later native movement stream.
    guard = _edit(commands, SITE, CONTINUATION, [
        ('CheckFlag', HIDE_FLAG),
        ('GoToIf', 0, ('old', CONTINUATION)),
        ('GoToIf', 5, ('label', 'create')),
        ('label', 'create'),
        ('ClearFlag', HIDE_FLAG),
        ('ShowPerson', OBJECT_ID),
    ])
    result, _, _ = G.relocate(raw, commands, [guard], MEMBER)
    _need(hashlib.sha256(result).hexdigest() == POSTIMAGE_SHA256,
          'derived member 21 postimage differs')
    verify_member(raw, result, commands)
    return result


def verify_member(before, after, commands):
    """Read back guard semantics, all old edges, movements and complementary bytes."""
    old = _before(before, commands)
    _need(type(after) is bytes, 'after image type')
    _need(hashlib.sha256(after).hexdigest() == POSTIMAGE_SHA256,
          'member 21 postimage differs')
    new = G.decode(after, commands, MEMBER)
    _need(not G.overlapping_instructions(new), 'after image has overlapping instructions')
    end = _sequence(new, SITE, [
        ('CheckFlag', [HIDE_FLAG], None),
        ('GoToIf', [0], 0x698),
        ('GoToIf', [5], 0x690),
        ('ClearFlag', [HIDE_FLAG], None),
        ('ShowPerson', [OBJECT_ID], None),
    ])
    _need(end == 0x698, 'guard width')
    continuation = new.istruzioni.get(end)
    _need(continuation is not None and continuation.nome == 'MakeObjectVisible'
          and continuation.args == [OBJECT_ID], 'guard continuation target')
    replacements = [(SITE, CONTINUATION, 26)]
    survived = _preserved(before, after, old, new, replacements)
    return {
        'member': MEMBER,
        'before_sha256': hashlib.sha256(before).hexdigest(),
        'after_sha256': hashlib.sha256(after).hexdigest(),
        'bytes_added': len(after) - len(before),
        'surviving_instructions': survived,
        'entry_count': len(new.entry),
        'verification': 'decoded local guard, branches, movements and complementary bytes',
    }
