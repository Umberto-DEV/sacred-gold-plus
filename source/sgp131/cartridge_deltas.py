"""Fixed-owner overlay plans consumed by the UI's sole append writer.

Plans compile from the current map and grant no reserve permission. The UI owns
only file126 and row126. A separate granted mechanical stage installs the stub
and seam in place. Only inert preparation is supported here; runtime activation
still requires the owner's measured context proof and final candidate gate.
"""
from dataclasses import dataclass
import hashlib
import json
import struct

from . import baseline, rematches, reserve


def _need(ok, message):
    if not ok:
        raise ValueError(message)


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


@dataclass(frozen=True)
class OverlayDelta:
    """Immutable payload and provenance. Construction alone grants no write."""
    input_sha256: str
    planning_json: bytes
    image: bytes
    row: tuple
    resident_writes: tuple  # deferred until a verified reserve grant, never UI writes

    @property
    def file_id(self):
        return 126

    @property
    def config_offset(self):
        return rematches.DEFAULT_CODE_SIZE

    @property
    def activation_offset(self):
        """Offset relative to file126; final activation must use the common inert root."""
        return self.config_offset + rematches.ACTIVE_BYTE

    def record(self):
        return {'schema': 1, 'producer': 'rematches-module', 'input_sha256': self.input_sha256,
                'planning': json.loads(self.planning_json),
                'file_id': 126, 'overlay_id': 126, 'row': list(self.row),
                'config_offset': self.config_offset, 'activation_offset': self.activation_offset,
                'image_bytes': len(self.image), 'image_sha256': _sha(self.image),
                'deferred_resident_writes': [{'address': address, 'bytes': len(after),
                                            'before_sha256': _sha(before), 'after_sha256': _sha(after)}
                                           for address, before, after in self.resident_writes],
                'function_state': 'inert'}


def _planning():
    """Read only the current validated map. This is deliberately NOT an allocation."""
    raw = reserve.MAP.read_bytes()
    policy = json.loads(raw)
    reserve.validate_policy(policy)
    matches = [(entry['parent'], part) for entry in policy['subdivisions'] for part in entry['parts']
               if part['name'] == rematches.SLOT_NAME and part['kind'] == 'payload']
    _need(len(matches) == 1, 'fixed rematches map slot')
    parent, part = matches[0]
    _need(part['start'] % 4 == 0 and part['bytes'] >= 64, 'fixed rematches map geometry')
    return {'policy_sha256': _sha(raw), 'policy_version': policy['version'], 'slot': rematches.SLOT_NAME,
            'parent': parent, 'start': part['start'], 'capacity': part['bytes'],
            'planning_only': True, 'installation_authorized': False}


def _parts(data, language, work_dir, *, installed=False):
    plan = _planning()
    parts = rematches._prepare_module(data, language, work_dir, stub_base=plan['start'], check_placeholder=not installed)
    (old, abi, stub_max, spec, seam, old_target, window, conflicts, origin,
     config, blob, symbols, hook, stub, stub_symbols, image) = parts
    _need(origin is None and config[rematches.ACTIVE_BYTE] == 0, 'overlay declaration cannot activate rematches')
    writes = ((seam, bytes(old.leggi(seam, 4)), rematches.bl_thumb(seam, plan['start'])),
              (plan['start'], bytes(old.leggi(plan['start'], stub_max)), stub + bytes(stub_max - len(stub))))
    row = (126, window, len(image), 0, window, window, 126, 0)
    return plan, image, row, writes


def derive_rematches(base, language, work_dir):
    """Compile pinned inert parts from V4; return data only, with no reserve grant."""
    _need(type(base) is bytes and baseline.identify(base) == language, 'overlay exact V4/language')
    plan, image, row, writes = _parts(base, language, work_dir)
    return OverlayDelta(_sha(base), _canonical(plan), image, row, writes)


def check_against(deltas, base, language, work_dir):
    """Default deny and reproduce declarations; no record may widen ownership."""
    try:
        deltas = tuple(deltas)
        _need(len(deltas) <= 1 and all(type(d) is OverlayDelta for d in deltas),
              'only one fixed rematches overlay delta is supported')
        for delta in deltas:
            expected = derive_rematches(base, language, work_dir)
            _need(delta == expected, 'overlay delta differs from owner replay')
        return deltas
    except (TypeError, KeyError, json.JSONDecodeError, UnicodeDecodeError) as error:
        raise ValueError('malformed overlay delta') from error


def rederive(base, language, work_dir, records):
    """Replay recorded provenance; bytes are always rebuilt by the fixed owner."""
    _need(isinstance(records, list) and len(records) <= 1, 'recorded overlay delta list')
    if not records:
        return ()
    record = records[0]
    _need(isinstance(record, dict) and record.get('producer') == 'rematches-module', 'unknown overlay delta producer')
    expected = derive_rematches(base, language, work_dir)
    _need(_canonical(record) == _canonical(expected.record()), 'recorded overlay delta differs from owner replay')
    return (expected,)


def verify_readback(delta, old, new):
    """Read final cartridge through ui_verify.Image, independently of the writer."""
    _need(new.records[126] == delta.row, 'rematches overlay row readback')
    _need(new.file(126) == delta.image, 'rematches module file readback')
    _need(new.records[126][2] == len(delta.image) and new.records[126][7] == 0,
          'rematches module geometry/flags')
    # All resident writes are deferred. UI complement comparison protects them.


def _activation_image(data, language, delta, stage_options):
    """Materialize the owner config from STAGE-BEFORE, never by rewriting final receipt hashes."""
    from . import activation
    kwargs = activation.owner_kwargs(stage_options, 'rematches', language)
    if not kwargs['activate']:
        return delta.image, None
    candidate, proof = kwargs['candidate_sha256'], kwargs['context_proof']
    abi = rematches.load_abi()
    origin = rematches.validate_context_proof(proof, abi, language, candidate, allow_synthetic=False)
    _need(delta.image[delta.activation_offset] == 0, 'prepared rematches image is not inert')
    authored = bytearray(delta.image)
    authored[delta.activation_offset] = 1
    return bytes(authored), {'candidate_sha256': candidate, 'context_proof': proof, 'proof_origin': origin,
                      'capture_rom_sha256': proof['capture_rom_sha256'], 'proof_sha256': rematches.proof_digest(proof)}


def install_prepared(data, language, work_dir, delta, *, allocation, stage_options=None):
    """Granted in-place stage. UI has installed the inert module; evidence may author its one active byte."""
    _need(type(data) is bytes, 'immutable prepared stage input required')
    _need(type(delta) is OverlayDelta and baseline.INPUT_HASHES.get(delta.input_sha256) == language,
          'prepared module input/language')
    assignment = rematches.check_allocation(allocation, language)
    plan = _planning()
    _need(delta.planning_json == _canonical(plan), 'prepared module planning differs from current map')
    image, row, writes = delta.image, delta.row, delta.resident_writes
    _need(assignment['start'] == plan['start'] and assignment['bytes'] >= 64,
          'grant does not cover the fixed compiled stub')
    from .ui_verify import Image
    before = Image(data)
    verify_readback(delta, before, before)  # stage-before contains the exact INERT UI module
    authored_image, proof_record = _activation_image(data, language, delta, stage_options)
    out = bytearray(data)
    for address, original, authored in writes:
        _need(before.arm(address, len(original)) == original, 'prepared resident preimage')
        at = before.offset(address, len(authored))
        out[at:at+len(authored)] = authored
    active_at = before.files[126][0] + delta.activation_offset
    out[active_at] = authored_image[delta.activation_offset]
    result = bytes(out)
    receipt = {'module': 'sgp131.rematches.prepared', 'language': language,
               'input_sha256': _sha(data), 'output_sha256': _sha(result),
               'overlay_delta': delta.record(), 'allocation': allocation,
               'function_state': 'active' if proof_record else 'inert'}
    if proof_record is not None:
        receipt['activation'] = proof_record
    verify_prepared(data, result, receipt, work_dir, stage_options=stage_options, delta=delta)
    return result, receipt


def verify_prepared(before, after, receipt, work_dir, *, stage_options=None, delta=None):
    """Fresh fixed-owner materialization and complete unchanged complement, with proof-bound options."""
    from .ui_verify import Image
    from . import activation
    _need(type(before) is bytes and type(after) is bytes, 'immutable prepared stage images required')
    fields = {'module','language','input_sha256','output_sha256','overlay_delta','allocation','function_state'}
    _need(type(receipt) is dict and set(receipt) in (fields, fields | {'activation'}), 'prepared stage receipt shape')
    language = receipt['language']
    _need(receipt['module'] == 'sgp131.rematches.prepared'
          and baseline.INPUT_HASHES.get(receipt['overlay_delta'].get('input_sha256')) == language,
          'prepared stage module/input/language')
    _need(_sha(before) == receipt['input_sha256'] and _sha(after) == receipt['output_sha256']
          and len(before) == len(after), 'prepared stage hashes/length')
    _need(type(delta) is OverlayDelta and baseline.INPUT_HASHES.get(delta.input_sha256) == language,
          'prepared stage needs the V4-derived overlay delta')
    assignment = rematches.check_allocation(receipt['allocation'], language)
    plan = _planning()
    _need(delta.planning_json == _canonical(plan) and delta.record() == receipt['overlay_delta'],
          'prepared stage provenance')
    row, writes = delta.row, delta.resident_writes
    _need(assignment['start'] == plan['start'] and assignment['bytes'] >= 64, 'prepared stage grant')
    old, new = Image(before), Image(after)
    verify_readback(delta, old, old)
    expected_image, expected_proof = _activation_image(before, language, delta, stage_options)
    _need(receipt.get('activation') == expected_proof, 'prepared stage evidence differs from owner replay')
    _need(new.records[126] == row and new.file(126) == expected_image, 'prepared stage active module differs')
    activation.check_owner_options('rematches', receipt, stage_options, language)
    ranges = []
    for address, original, authored in writes:
        _need(old.arm(address, len(original)) == original and new.arm(address, len(authored)) == authored,
              'prepared stage resident readback')
        lo = old.offset(address, len(authored)); ranges.append((lo, lo+len(authored)))
    active_at = old.files[126][0] + delta.activation_offset
    ranges.append((active_at, active_at + 1))
    cursor = 0
    for lo, hi in sorted(ranges):
        _need(cursor <= lo < hi and before[cursor:lo] == after[cursor:lo], 'prepared stage foreign write')
        cursor = hi
    _need(before[cursor:] == after[cursor:], 'prepared stage foreign suffix')
    return {'function_state': receipt['function_state'], 'all_other_bytes_preserved': True,
            'regions': [{'start': lo, 'end': hi} for lo, hi in sorted(ranges)]}
