"""Shared Class B fixture: the supported candidate ROMs, read in memory only.

A missing input skips (reason stated); with SGP_REMATCH_REQUIRE_INPUTS=1 it fails instead.
A present input with the wrong sha256 always fails. Nothing is written to disk.
The module is overlay 126 loaded on demand; only its 64-byte resident stub needs reserve memory, taken from a
reserve.allocate receipt for `c8.module-stubs`. The real policy cannot grant that slot yet (its owner is conditional),
so these tests run under a DECLARED test policy (`declared_reserve`: own version and digest, refused by the real
policy) whose slot is COPIED from reserve-map.json (192 zero bytes in the V4). Nothing here is a product assignment.
"""
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
from unittest import mock

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / 'source'))
sys.path.insert(0, str(HERE))

import constructor_bench as bench                    # noqa: E402
from sgp131 import rematches                         # noqa: E402
from sgp131.baseline import INPUT_HASHES             # noqa: E402

CANDIDATES = ROOT / 'local' / 'experiments' / 'balance493-2026-10-28'
INPUTS = {
    'EN': (os.environ.get('SGP_REMATCH_ROM_EN') or CANDIDATES / 'candidate-v4-EN.nds',
           '179edfb1ca331503f438e98f3afccfb0ab85759bf9ab88fb86c735f5fcefbf90'),
    'IT': (os.environ.get('SGP_REMATCH_ROM_IT') or CANDIDATES / 'candidate-v4-IT.nds',
           '2a2f0b437fca524c18b71b20feb01a1f51351e61c7c897ce73d9b3be1ee3a156'),
}
REQUIRE_INPUTS = os.environ.get('SGP_REMATCH_REQUIRE_INPUTS') == '1'
SIZES = (1280, 768)               # (code, config) allocations of the module image
SIZES_2 = (1536, 768)             # a second layout (bigger code region) for the relocation checks
OFFSET_2 = 64                     # the stub at the second 64-byte position of the shared slot

_ROMS, _ARCHIVES, _BENCHES = {}, {}, {}

# --- declared TEST reserve policy ------------------------------------------------------------------------
TEST_POLICY_VERSION = 'TEST-ONLY-reserve-policy'
TEST_POLICY_SHA256 = hashlib.sha256(b'TEST-ONLY reserve policy: a declared test double, never the product map').hexdigest()
REAL_RESERVE_POLICY = rematches._reserve_policy       # captured before any patch
CANDIDATE = hashlib.sha256(b'fixture: the inert candidate ROM of the rematch tests').hexdigest()


def real_slot(name=rematches.SLOT_NAME):
    """(start, bytes) of `name` in the real reserve-map.json (read only)."""
    policy = json.loads((ROOT / 'source/sgp131/data/reserve-map.json').read_text())
    for entry in policy['subdivisions']:
        for part in entry['parts']:
            if part['name'] == name and part['kind'] == 'payload':
                return part['start'], part['bytes']
    raise AssertionError('reserve-map.json has no slot ' + name)


STUB_START, STUB_BYTES = real_slot()


def declared_policy_for(start, size):
    def policy():
        part = {'name': rematches.SLOT_NAME, 'kind': 'payload', 'start': start, 'bytes': size}
        return ({'version': TEST_POLICY_VERSION, 'conditional_parents': [],
                 'subdivisions': [{'parent': 'test.declared-parent', 'parts': [part]}]}, TEST_POLICY_SHA256)
    return policy


def declared_allocation(language, start=None, size=None, request=None, **override):
    """A reserve.allocate-shaped receipt under the declared test policy (fixture, not an assignment)."""
    start = STUB_START if start is None else start
    size = STUB_BYTES if size is None else size
    request = size if request is None else request
    record = {'schema': 1, 'input_sha256': next(h for h, lang in INPUT_HASHES.items() if lang == language),
              'language': language, 'policy_version': TEST_POLICY_VERSION, 'policy_sha256': TEST_POLICY_SHA256,
              'audit_sha256': hashlib.sha256(b'test audit').hexdigest(), 'requested': {rematches.SLOT_NAME: request},
              'assignments': [{'name': rematches.SLOT_NAME, 'parent': 'test.declared-parent', 'start': start,
                               'bytes': request, 'capacity': size}],
              'preservation': {}, 'address_reserved': True, 'installed': False, 'installation_authorized': False}
    record.update(override)
    return record


def declared_reserve(start=None, size=None):
    """Context manager: rematches._reserve_policy is the declared test double granting [start, start+size)."""
    start = STUB_START if start is None else start
    size = STUB_BYTES if size is None else size
    return mock.patch.object(rematches, '_reserve_policy', declared_policy_for(start, size))


def real_reserve():
    return mock.patch.object(rematches, '_reserve_policy', REAL_RESERVE_POLICY)


def install(data, language, work, *, stub_offset=0, sizes=SIZES, allocation=None, **kwargs):
    """rematches.install under the declared test policy; activation gets the fixture candidate sha256."""
    kwargs.setdefault('code_size', sizes[0])
    kwargs.setdefault('config_size', sizes[1])
    if kwargs.get('activate'):
        kwargs.setdefault('candidate_sha256', CANDIDATE)
    with declared_reserve():
        return rematches.install(data, language, work, allocation=allocation or declared_allocation(language),
                                 stub_offset=stub_offset, **kwargs)


def verify(before, after, receipt, **kwargs):
    assignment = receipt['assignment']
    with declared_reserve(assignment['start'], assignment['capacity']):
        return rematches.verify(before, after, receipt, **kwargs)


class MissingInput(Exception):
    pass


def synthetic_proof(language):
    """Harness-only stand-in for the Android context proof (labelled synthetic; never runtime evidence)."""
    return {'language': language, 'synthetic_harness_only': True,
            'observations': [{'trainer': t, 'family': f, 'battle_type': b, 'enemy_index': 1}
                             for t in (712, 713) for f, b in (('phone', 0x1), ('dojo-sequence', 0x801))]}


def rom(language):
    path, expected = INPUTS[language]
    path = Path(path)
    if not path.is_file():
        raise MissingInput(f'{language} input ROM not present: {path}')
    if language not in _ROMS:
        data = path.read_bytes()
        if hashlib.sha256(data).hexdigest() != expected:
            raise AssertionError(f'{language} input ROM sha256 mismatch')
        _ROMS[language] = data
    return _ROMS[language]


def archives(language):
    if language not in _ARCHIVES:
        _ARCHIVES[language] = bench.Archives(rom(language))
    return _ARCHIVES[language]


def native_bench(language):
    key = (language, 'native')
    if key not in _BENCHES:
        _BENCHES[key] = bench.Bench(rom(language), archives(language), language)
    return _BENCHES[key]


def installed(language, mode='active', stub_offset=0, sizes=SIZES):
    """(Bench over the patched image with the REAL overlay loader, receipt). The patched ROM bytes are not kept."""
    key = (language, mode, stub_offset, sizes)
    if key not in _BENCHES:
        data = rom(language)
        proof = synthetic_proof(language) if mode == 'active' else None
        out, receipt = install(data, language, tempfile.mkdtemp(prefix='rematch-'), stub_offset=stub_offset, sizes=sizes,
                               activate=mode == 'active', context_proof=proof, allow_synthetic=True)
        window = receipt['overlay']['window']
        _BENCHES[key] = (bench.Bench(out, archives(language), language, watch=(window, window + sizes[0]), overlay=True), receipt)
    return _BENCHES[key]


def seed_for(trainer, outcome):
    return next(s for s in range(0x20000, 0x20400) if ((s ^ (s >> 16) ^ trainer) & 1) == outcome)


def variant_buffer(receipt, trainer, label):
    tuples = receipt['trainers'][str(trainer)][label]['tuples']
    return rematches.encode_party([dict(slot=i, species=u[0], form=u[1], level=u[2], difficulty=u[3],
                                        override=u[4], item=u[5], moves=u[6], capsule=u[7])
                                   for i, u in enumerate(tuples)])


def skip_ranges(stub_offset=0, sizes=SIZES):
    """RAM ranges the native oracle cannot share with an installed run: the stub, the seam word, the module window,
    the overlay registry (entries keep their id after an unload) and the WFC overlay counter."""
    seam = 0x0207363A
    window = int(rematches.load_abi()['overlay']['window'], 16)
    return [(STUB_START + stub_offset, STUB_START + stub_offset + 64), (seam, seam + 4), (window, window + sizes[0] + sizes[1]),
            (bench.REGISTRY, bench.REGISTRY + bench.REGISTRY_BYTES), (0x023DA044, 0x023DA048)]
