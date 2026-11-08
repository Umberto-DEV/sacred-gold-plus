"""Compose official retail dialogue with explicitly translated Sacred Gold/Plus edits."""
from collections import Counter
import importlib.util
from pathlib import Path

from ndspy.narc import NARC
from translation.message_codec import Bank, encode_text

_PATH = Path(__file__).resolve().parents[1] / 'quality-audit/hgss_text.py'
_SPEC = importlib.util.spec_from_file_location('_localization_text_reader', _PATH)
_TEXT = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_TEXT)

# The shared US executable formats height in feet/inches. Non-US retail donors
# leave this entry empty because their native executables use metric formatting.
# Preserve the formatter together with the protected US Pokédex graphics group.
PROTECTED_MESSAGES = frozenset({(802, 175)})


def classify(core, original):
    if original is None:
        return 'authored'
    if core['normalized'] == original['normalized']:
        return 'retail'
    if (not core['unknown_codes'] and not original['unknown_codes']
            and not core['malformed_controls'] and not original['malformed_controls']
            and core['controls'] == original['controls']
            and core['text'].strip().casefold() == original['text'].strip().casefold()):
        return 'retail-style'
    return 'authored'


def translate_messages(core_archive, reference_archive, donor_archive, strings, chars, commands, *, layout=None):
    """No fallback for changed content; preserve script control arguments exactly.

    Cosmetic case/padding edits use official locale presentation. Existing save
    names are never read or rewritten. Binary Guide content is owned separately.
    """
    result, reference, donor = (NARC(raw) for raw in (core_archive, reference_archive, donor_archive))
    aliases, counts, required = {}, Counter(retail=0, **{'retail-style': 0}, authored=0), set()
    for bank_index, raw in enumerate(result.files):
        if raw.startswith(b'SGG1'):
            continue
        core = Bank(raw)
        old = Bank(reference.files[bank_index]).words if bank_index < len(reference.files) else []
        native = Bank(donor.files[bank_index]).words if bank_index < len(donor.files) else []
        for index, words in enumerate(core.words):
            if (bank_index, index) in PROTECTED_MESSAGES:
                counts['protected'] += 1
                continue
            before = _TEXT.render(words, chars, commands)
            original = _TEXT.render(old[index], chars, commands) if index < len(old) else None
            action = 'authored' if (bank_index, index) == (300, 29) else classify(before, original)
            counts[action] += 1
            if action != 'authored':
                if index >= len(native):
                    raise ValueError(f'missing donor message {bank_index}/{index}')
                replacement = native[index]
            else:
                identity = aliases.setdefault(before['text'], f'm:{bank_index}:{index}')
                required.add(identity)
                if identity not in strings or not isinstance(strings[identity], str):
                    raise ValueError('missing translation ' + identity)
                value = strings[identity]
                if layout is not None:
                    value = layout(bank_index, value, index)
                replacement = encode_text(value, chars, commands)
                decoded = _TEXT.render(replacement, chars, commands)
                if (decoded['controls'] != before['controls'] or decoded['malformed_controls']
                        or decoded['unknown_codes']):
                    raise ValueError('translated control/glyph contract: ' + identity)
            if replacement != words:
                core.replace(index, replacement)
        result.files[bank_index] = core.save()
    return result.save(), dict(counts=dict(counts), required_ids=sorted(required))
