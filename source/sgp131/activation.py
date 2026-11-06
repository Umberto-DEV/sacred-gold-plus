"""Evidence-bound owner configuration and the single final all-inert identity gate.

This module never grants reserve ownership or authenticates captures. Run the gate
AFTER independent owner/chain readback, using those verified owner receipts.
Production callers provide immutable StageOptions, never mutable option dictionaries.
"""
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
import struct

OWNERS = ('controls', 'portable', 'rematches')
MAX_CONFIG_BYTES = 256 * 1024
_HASH = re.compile(r'[0-9a-f]{64}')


def _need(ok, message):
    if not ok:
        raise ValueError('activation: ' + message)


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def _pairs(items):
    out = {}
    for key, value in items:
        _need(key not in out, 'duplicate JSON key: ' + key)
        out[key] = value
    return out


def _noninteger(_value):
    raise ValueError('activation: config numbers must be integers')


def _decode(raw):
    _need(type(raw) is bytes and 0 < len(raw) <= MAX_CONFIG_BYTES, 'immutable bounded config bytes required')
    try:
        return json.loads(raw, object_pairs_hook=_pairs, parse_float=_noninteger, parse_constant=_noninteger)
    except (UnicodeError, RecursionError) as error:
        raise ValueError('activation: malformed config encoding/depth') from error


def _geometry(value):
    from . import controls
    _need(type(value) is dict and set(value) == set(controls.PROPOSAL), 'controls geometry exact fields')
    _need(all(type(v) is int and 0 <= v <= 1024 for v in value.values()), 'controls geometry integer fields')


def _validate_inner(document):
    from . import controls, portable, rematches
    _need(type(document) is dict and set(document) == {'schema', 'language', 'stage_options'}, 'config exact fields')
    _need(type(document['schema']) is int and document['schema'] == 1, 'config schema')
    language = document['language']
    _need(type(language) is str and language in ('EN', 'IT'), 'config language')
    entries = document['stage_options']
    _need(type(entries) is dict and set(entries) <= set(OWNERS), 'unknown stage options')
    roots = set()
    for name, entry in entries.items():
        _need(type(entry) is dict and entry.get('mode') in ('inert', 'active'), name + ' mode')
        active = entry['mode'] == 'active'
        fields = {'mode'}
        if name == 'controls':
            fields |= {'geometry', 'variant'}
            if active:
                fields |= {'candidate_sha256', 'evidence'}
            _need(set(entry) == fields, 'controls exact options')
            _geometry(entry['geometry'])
            _need(entry['variant'] in controls.VARIANTS, 'controls variant')
            if active:
                controls.check_evidence(entry['evidence'], entry['geometry'], entry['candidate_sha256'], language)
        elif name == 'portable':
            fields.add('activation')
            if active:
                fields |= {'candidate_sha256', 'context_proof'}
            _need(set(entry) == fields, 'portable exact options')
            words = entry['activation']
            _need(type(words) is dict and set(words) == {'bridge', 'input', 'prompt', 'travel_mask'}
                  and all(type(v) is int for v in words.values()), 'portable explicit integer activation words')
            portable._activation(words)
            _need(any(words[key] for key in ('bridge', 'input', 'prompt')) == active, 'portable mode/words disagree')
            if active:
                _need(entry['context_proof'].get('status') == 'measured', 'portable needs measured context proof')
                portable._proof(entry['context_proof'], False, language, entry['candidate_sha256'])
        else:
            if active:
                fields |= {'candidate_sha256', 'context_proof'}
            _need(set(entry) == fields, 'rematches exact options')
            if active:
                proof = entry['context_proof']
                _need(type(proof) is dict and set(proof) == set(rematches.PROOF_FIELDS) | {'language', 'observations'},
                      'rematches exact capture-proof fields; synthetic bypass is unavailable')
                rematches.validate_context_proof(proof, rematches.load_abi(), language,
                                                entry['candidate_sha256'], allow_synthetic=False)
        if active:
            root = entry['candidate_sha256']
            _need(type(root) is str and _HASH.fullmatch(root), 'candidate lowercase SHA256')
            roots.add(root)
    _need(len(roots) <= 1, 'every active owner must name the same inert candidate')
    return document


def _validate(document):
    try:
        return _validate_inner(document)
    except (TypeError, KeyError, IndexError, AttributeError, OverflowError, RecursionError) as error:
        raise ValueError('activation: malformed owner options/proof') from error


@dataclass(frozen=True)
class StageOptions:
    """Closed validated JSON snapshot. Extraction returns copies; no mutable payload is retained."""
    wire: bytes

    def __post_init__(self):
        document = _validate(_decode(self.wire))
        _need(_canonical(document) == self.wire, 'StageOptions requires canonical bytes; use parse')

    @classmethod
    def parse(cls, raw):
        return cls(_canonical(_validate(_decode(raw))))

    def document(self):
        return _validate(_decode(self.wire))

    @property
    def active_owners(self):
        entries = self.document()['stage_options']
        return tuple(name for name in OWNERS if entries.get(name, {}).get('mode') == 'active')

    @property
    def candidate_sha256(self):
        entries = self.document()['stage_options']
        return next((entries[name]['candidate_sha256'] for name in self.active_owners), None)


def validate_for_chain(options, language, names):
    _need(type(language) is str and language in ('EN', 'IT'), 'ROM language')
    if options is None:
        return
    _need(type(options) is StageOptions, 'immutable StageOptions required')
    doc = options.document()
    _need(doc['language'] == language, 'options language differs from ROM')
    _need(set(doc['stage_options']) <= set(names), 'options name an owner outside the requested stage chain')


def owner_kwargs(options, owner, language):
    _need(owner in OWNERS, 'unknown owner')
    validate_for_chain(options, language, OWNERS)
    entry = {} if options is None else options.document()['stage_options'].get(owner, {})
    active = entry.get('mode') == 'active'
    proof = {key: entry[key] for key in ('candidate_sha256', 'context_proof') if key in entry}
    if owner == 'controls':
        return {'active': active, **{key: entry[key] for key in ('geometry', 'variant', 'evidence', 'candidate_sha256') if key in entry}}
    if owner == 'portable':
        return {**proof, **({'activation': entry['activation']} if entry else {})}
    return {'activate': active, **proof}


def snapshot_config(path):
    """Bounded non-symlink file snapshot; record original bytes, preserve canonical parsed options separately."""
    path = Path(path).absolute()
    _need(not any(part.is_symlink() for part in (path, *path.parents)), 'config symlink forbidden')
    from sgp13 import admission
    try:
        raw, digest = admission.read_bounded(path, MAX_CONFIG_BYTES, 'mechanics config')
    except (OSError, ValueError) as error:
        raise ValueError('activation: missing/oversized/aliased mechanics config') from error
    _need(bool(raw), 'missing/oversized mechanics config')
    options = StageOptions.parse(raw)
    return options, {'path': str(path), 'bytes': len(raw), 'sha256': digest,
                     'options_sha256': _sha(options.wire)}


def refresh_config(record, options):
    fresh, new_record = snapshot_config(record['path'])
    _need(new_record == record and fresh == options, 'mechanics config changed during operation')


def _slots():
    from . import reserve
    policy = json.loads(reserve.MAP.read_bytes())
    reserve.validate_policy(policy)
    return {part['name']: part for entry in policy['subdivisions'] for part in entry['parts'] if part['kind'] == 'payload'}


def _locations(data, receipts):
    """Fixed offsets plus independently verified portable config placement. Not a replacement owner verifier."""
    from . import controls, portable, rematches
    slots = _slots()
    found = []
    if 'controls' in receipts:
        part = slots[controls.SLOT_NAME]
        found.append((controls.rom_offset(data, part['start'] + controls.STATE_ENABLED, 4), 4, 'controls'))
    if 'portable' in receipts:
        part = slots[portable.SLOT_NAME]
        raw = receipts['portable']
        address = raw['config']['address']
        _need(type(address) is int and address == raw['state']['address'] + portable.STATE_BYTES
              and part['start'] <= address and address + portable.CONFIG_BYTES <= part['start'] + part['bytes'],
              'portable config placement leaves its fixed slot')
        segments = portable.arm9_segments(data)
        for key in ('bridge', 'input', 'prompt', 'context_proof'):
            at = portable.locate(segments, address + portable.CONFIG_OFFSETS[key], 4)
            found.append((at, 4, 'portable'))
    if 'rematches' in receipts:
        at = rematches._active_at(data, {'file_id': 126, 'config_offset': rematches.DEFAULT_CODE_SIZE})
        found.append((at, 1, 'rematches'))
    return tuple(found)


def _clear(data, locations):
    _need(type(data) is bytes, 'immutable final ROM bytes required')
    output = bytearray(data)
    end = 0
    for at, size, owner in sorted(locations):
        _need(type(at) is int and type(size) is int and size in (1, 4) and end <= at and at + size <= len(data),
              'overlapping/out-of-bounds activation location')
        _need(int.from_bytes(data[at:at + size], 'little') in (0, 1), 'nonboolean activation word')
        output[at:at + size] = bytes(size)
        end = at + size
    return bytes(output)


def _check_owner_options_inner(name, receipt, options, language):
    """Bind owner readback to the exact requested settings, for inert and active owners."""
    from . import controls, portable
    kwargs = owner_kwargs(options, name, language)
    active = kwargs.get('active', kwargs.get('activate', False))
    if name == 'portable':
        active = any(kwargs.get('activation', {}).get(key, 0) for key in ('bridge', 'input', 'prompt'))
    _need(type(receipt) is dict and receipt.get('language') == language, 'owner receipt language')
    _need(receipt.get('function_state') == ('active' if active else 'inert'), 'owner/options activation state differs')
    candidate = kwargs.get('candidate_sha256')
    if name == 'controls':
        _need(receipt.get('candidate_sha256') == candidate and receipt.get('evidence') == kwargs.get('evidence')
              and receipt.get('geometry') == kwargs.get('geometry', controls.PROPOSAL)
              and receipt.get('variant') == kwargs.get('variant', 'compact'), 'controls receipt/options differ')
    elif name == 'portable':
        proof = portable._proof(kwargs.get('context_proof'), False, language, candidate)
        words = portable._activation(kwargs.get('activation'))
        words['context_proof'] = int(proof is not None)
        _need(receipt.get('candidate_sha256') == candidate and receipt.get('context_proof') == proof
              and receipt.get('config', {}).get('values') == words, 'portable receipt/options differ')
    elif active:
        record = receipt.get('activation')
        _need(type(record) is dict and record.get('candidate_sha256') == candidate
              and record.get('context_proof') == kwargs.get('context_proof'), 'rematches receipt/options differ')
    else:
        _need(receipt.get('activation') is None, 'inert rematches receipt carries activation evidence')


def check_owner_options(name, receipt, options, language):
    try:
        return _check_owner_options_inner(name, receipt, options, language)
    except (TypeError, KeyError, IndexError, AttributeError, OverflowError) as error:
        raise ValueError('activation: malformed owner receipt') from error


def _check_owner_receipts(options, receipts, language):
    _need(type(receipts) is dict and set(receipts) <= set(OWNERS), 'owner receipt mapping')
    validate_for_chain(options, language, receipts)
    for name, receipt in receipts.items():
        check_owner_options(name, receipt, options, language)


def final_gate(final_rom, options, owner_receipts, *, language):
    """ONE whole-ROM comparison after independent chain readback; clears every installed owner's flags together."""
    _need(type(final_rom) is bytes, 'immutable final ROM bytes required')
    _check_owner_receipts(options, owner_receipts, language)
    try:
        projected = _clear(final_rom, _locations(final_rom, owner_receipts))
    except (TypeError, KeyError, IndexError, AttributeError, OverflowError) as error:
        raise ValueError('activation: malformed owner activation locations') from error
    root = None if options is None else options.candidate_sha256
    digest = _sha(projected)
    _need(root is None or root == digest, 'final all-inert ROM differs from the common captured candidate')
    return {'schema': 1, 'active_owners': [] if options is None else list(options.active_owners),
            'candidate_sha256': root, 'all_inert_sha256': digest}
