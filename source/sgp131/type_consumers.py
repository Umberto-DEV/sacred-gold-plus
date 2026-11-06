"""Repair confined overlay-12 type, ability and battle-state consumers.

SG-AI02 replaces ``GetTypeEffectivnessData`` in its original 64-byte span so
Conversion2 enumerates the 325 selectable records of the Plus 18-type chart.
SG-DM01 retargets the defender/effect literals used by the Ground/Flying
grounding helper to the same modern row indexed by the damage loop.
HG-B01 replaces the off-by-one Fire Fang effect in the Wonder Guard two-turn
gate with Shadow Force.  Effects 273 and 272 are unique to Fire Fang and
Shadow Force in the authenticated move tables; Fire Fang follows the ordinary
path while Shadow Force keeps the native charge/damaging-turn guard.
HG-B02 replaces the positive Rage mask in the pre-turn controller with the
canonical bit clear, so abandoning Rage removes only Rage and preserves every
other volatile ``status2`` bit.

This module only transforms a decoded overlay image.  The combined ``ai``
producer performs the one canonical BLZ rewrite and its UI-seed reconciliation.
"""
from __future__ import annotations

import hashlib
import importlib.util
import shutil
import subprocess
import tempfile
from pathlib import Path

from sgp12.rom import bl_decode, bl_thumb
from sgp13.compiler import compiler_environment, compiler_path


SOURCE = Path(__file__).resolve().parents[1]
NATIVE = SOURCE / 'features/type-consumers/native.S'

OVERLAY_BASE = 0x022378C0
OVERLAY_SIZE = 0x37380
CONVERSION_SITE = 0x0225260C
CONVERSION_BYTES = 64
RANDOM_CALL_OFFSET = 14
RANDOM = 0x0223BD98
MODERN_CHART = 0x021FBE60
ROW_COUNT = 325
CONVERSION_PREIMAGE = bytes.fromhex(
    '38b5151c1c1c0122702905d3e9f7befb7021a0f6c2ea0022480008180549095c'
    '29700549095c21700449095c04980170101c38bd7ccc26027dcc26027ecc2602')
PAYLOAD_SHA256 = '1ab0ab8d6b3b2bc003a44e57330beab3a4a393020b52e71f4c48bb7489645875'

GROUNDING_SITE = 0x02251D20
GROUNDING_PREIMAGE = bytes.fromhex('7dcc26027ecc2602')
GROUNDING_REPLACEMENT = bytes.fromhex('61be1f0262be1f02')

FIRE_FANG_CONTEXT_ADDRESS = 0x0225848C
FIRE_FANG_CONTEXT = bytes.fromhex(
    '1132934205d105494158022000020840704701207047c046')
FIRE_FANG_SITE = 0x0225848C
FIRE_FANG_PREIMAGE = bytes.fromhex('1132')
FIRE_FANG_REPLACEMENT = bytes.fromhex('1032')
FIRE_FANG_BRANCH_SITE = 0x02258490
FIRE_FANG_BRANCH_PREIMAGE = bytes.fromhex('05d1')
_need_fire_fang_context = (
    FIRE_FANG_CONTEXT[
        FIRE_FANG_SITE - FIRE_FANG_CONTEXT_ADDRESS:
        FIRE_FANG_SITE - FIRE_FANG_CONTEXT_ADDRESS + len(FIRE_FANG_PREIMAGE)]
    == FIRE_FANG_PREIMAGE
)
if not _need_fire_fang_context:
    raise RuntimeError('Fire Fang branch is inconsistent with its context')
_need_fire_fang_branch = (
    FIRE_FANG_CONTEXT[
        FIRE_FANG_BRANCH_SITE - FIRE_FANG_CONTEXT_ADDRESS:
        FIRE_FANG_BRANCH_SITE - FIRE_FANG_CONTEXT_ADDRESS
        + len(FIRE_FANG_BRANCH_PREIMAGE)]
    == FIRE_FANG_BRANCH_PREIMAGE
)
if not _need_fire_fang_branch:
    raise RuntimeError('Fire Fang/Shadow Force branch pin is inconsistent')

RAGE_CONTEXT_ADDRESS = 0x022493EC
RAGE_CONTEXT = bytes.fromhex(
    '08f080ff632806d01848295802208005014016482950761cc035be42e8dba06a')
RAGE_FUNCTION_ADDRESS = 0x0224930C
RAGE_FUNCTION_BYTES = 0x154
RAGE_FUNCTION_SHA256 = '6b1cc1e0aed12d29a592a6ec41d80c942bceb37c3dc68dfe09b1b82fe79a2de0'
RAGE_SITE = 0x022493FC
RAGE_PREIMAGE = bytes.fromhex('0140')       # ands r1, r0: retain Rage only
RAGE_REPLACEMENT = bytes.fromhex('8143')    # bics r1, r0: clear Rage only
_need_rage_context = (
    RAGE_CONTEXT[
        RAGE_SITE - RAGE_CONTEXT_ADDRESS:
        RAGE_SITE - RAGE_CONTEXT_ADDRESS + len(RAGE_PREIMAGE)]
    == RAGE_PREIMAGE
)
if not _need_rage_context:
    raise RuntimeError('Rage edit is inconsistent with its context')

COMPILER_VERSION = 'Apple clang version 21.0.0 (clang-2100.4.1.1)'
COMPILER_SHA256 = 'fc5e3cbba6ad54059295cad716aacb05ace8235f5f7a6031f1d8c15d24bd6d66'
FLAGS = ('--target=armv5te-none-eabi', '-mcpu=arm946e-s', '-mthumb',
         '-ffreestanding', '-fno-builtin', '-x', 'assembler-with-cpp')
FREE_SPACE_FLOOR = 10 * 1024**3


def _need(condition, message):
    if not condition:
        raise ValueError(message)


def _sha(data):
    return hashlib.sha256(bytes(data)).hexdigest()


def _module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def compile_native(work_dir: Path):
    """Build and authenticate the exact in-place Conversion2 helper."""
    compiler = compiler_path(COMPILER_SHA256)
    _need(compiler is not None, 'pinned clang unavailable')
    work_dir = Path(work_dir)
    _need(shutil.disk_usage(work_dir).free >= FREE_SPACE_FLOOR,
          'free-space floor (10 GiB)')
    version = subprocess.run(
        [compiler, '--version'], env=compiler_environment(), capture_output=True,
        text=True, check=True).stdout.splitlines()[0]
    _need(version == COMPILER_VERSION, 'compiler version drift: ' + version)
    _need(_sha(Path(compiler).resolve().read_bytes()) == COMPILER_SHA256,
          'compiler binary drift')
    source = NATIVE.read_bytes()
    loader = _module(SOURCE / 'features/options/tools/carica_text.py',
                     'type_consumers_object_loader')
    with tempfile.TemporaryDirectory(prefix='type-consumers-', dir=work_dir) as scratch:
        scratch = Path(scratch)
        obj = scratch / 'native.o'
        environment = dict(compiler_environment())
        environment['TMPDIR'] = str(scratch)
        done = subprocess.run(
            [compiler, *FLAGS, '-c', str(NATIVE), '-o', str(obj)],
            cwd=scratch, env=environment, capture_output=True, text=True,
            timeout=60)
        _need(done.returncode == 0 and not done.stderr,
              'type-consumer assembly failed: ' + done.stderr)
        raw = obj.read_bytes()
    payload, symbols = loader.load_text(
        raw, CONVERSION_SITE,
        ('conversion2_type_row', 'conversion2_random_call'))
    _need((symbols['conversion2_type_row'] & ~1) == CONVERSION_SITE,
          'Conversion2 entry geometry')
    call_offset = (symbols['conversion2_random_call'] & ~1) - CONVERSION_SITE
    _need(call_offset == RANDOM_CALL_OFFSET, 'Conversion2 RNG call geometry')
    payload = bytearray(payload)
    payload[call_offset:call_offset + 4] = bl_thumb(
        CONVERSION_SITE + call_offset, RANDOM | 1)
    payload = bytes(payload)
    _need(len(payload) == CONVERSION_BYTES,
          'Conversion2 replacement does not fill its exact 64-byte span')
    _need(_sha(payload) == PAYLOAD_SHA256,
          'Conversion2 replacement drift: ' + _sha(payload))
    _need(bl_decode(CONVERSION_SITE + call_offset,
                    payload[call_offset:call_offset + 4]) == RANDOM,
          'Conversion2 RNG target differs')
    return payload, {
        'bytes': len(payload), 'payload_sha256': _sha(payload),
        'object_sha256': _sha(raw), 'source_sha256': _sha(source),
        'entry': symbols['conversion2_type_row'],
        'random_call_offset': call_offset, 'random_target': RANDOM,
        'modern_chart': MODERN_CHART, 'row_count': ROW_COUNT,
        'compiler': {'version': version, 'executable_sha256': COMPILER_SHA256,
                     'flags': list(FLAGS)},
    }


def edits(payload):
    """Return the exact owned overlay edits for the shared writer."""
    payload = bytes(payload)
    _need(len(payload) == CONVERSION_BYTES and _sha(payload) == PAYLOAD_SHA256,
          'Conversion2 payload identity')
    return [
        {'addr': CONVERSION_SITE, 'pre': CONVERSION_PREIMAGE, 'post': payload},
        {'addr': GROUNDING_SITE, 'pre': GROUNDING_PREIMAGE,
         'post': GROUNDING_REPLACEMENT},
        {'addr': FIRE_FANG_SITE, 'pre': FIRE_FANG_PREIMAGE,
         'post': FIRE_FANG_REPLACEMENT},
        {'addr': RAGE_SITE, 'pre': RAGE_PREIMAGE,
         'post': RAGE_REPLACEMENT},
    ]


def patch_overlay(image: bytes, payload: bytes):
    """Apply the shared type/ability/state fixes to one decoded overlay 12."""
    image = bytes(image)
    _need(len(image) == OVERLAY_SIZE, 'overlay 12 image size differs')
    context = FIRE_FANG_CONTEXT_ADDRESS - OVERLAY_BASE
    _need(image[context:context + len(FIRE_FANG_CONTEXT)] == FIRE_FANG_CONTEXT,
          'Fire Fang/Wonder Guard context differs')
    context = RAGE_CONTEXT_ADDRESS - OVERLAY_BASE
    _need(image[context:context + len(RAGE_CONTEXT)] == RAGE_CONTEXT,
          'Rage volatile-state context differs')
    result = bytearray(image)
    for edit in edits(payload):
        offset = edit['addr'] - OVERLAY_BASE
        pre, post = edit['pre'], edit['post']
        _need(result[offset:offset + len(pre)] == pre,
              'type-consumer preimage differs at %#x' % edit['addr'])
        _need(len(pre) == len(post), 'type-consumer edit changes overlay size')
        result[offset:offset + len(post)] = post
    result = bytes(result)
    changed = [i for i, (old, new) in enumerate(zip(image, result)) if old != new]
    _need(changed, 'type-consumer patch changed no bytes')
    return result, {
        'conversion': {'address': CONVERSION_SITE,
                       'bytes': CONVERSION_BYTES,
                       'before_sha256': _sha(CONVERSION_PREIMAGE),
                       'after_sha256': PAYLOAD_SHA256},
        'grounding': {'address': GROUNDING_SITE,
                      'before': GROUNDING_PREIMAGE.hex(),
                      'after': GROUNDING_REPLACEMENT.hex(),
                      'modern_columns': [MODERN_CHART + 1, MODERN_CHART + 2]},
        'fire_fang_wonder_guard': {
            'address': FIRE_FANG_SITE,
            'before': FIRE_FANG_PREIMAGE.hex(),
            'after': FIRE_FANG_REPLACEMENT.hex(),
            'effect_before': 273,
            'effect_after': 272,
            'branch_address': FIRE_FANG_BRANCH_SITE,
            'branch': FIRE_FANG_BRANCH_PREIMAGE.hex(),
        },
        'rage_status2': {
            'address': RAGE_SITE,
            'before': RAGE_PREIMAGE.hex(),
            'after': RAGE_REPLACEMENT.hex(),
            'rage_mask': 1 << 23,
            'operation_before': 'status2 &= STATUS2_RAGE',
            'operation_after': 'status2 &= ~STATUS2_RAGE',
        },
        'changed_offsets': changed,
        'overlay_sha256_before': _sha(image),
        'overlay_sha256_after': _sha(result),
    }


def verify_overlay(before: bytes, after: bytes, payload: bytes, receipt: dict):
    expected, details = patch_overlay(before, payload)
    _need(bytes(after) == expected, 'type-consumer overlay output differs')
    _need(receipt == details, 'type-consumer receipt differs')
    return {'ok': True, 'logical_changed_bytes': len(details['changed_offsets']),
            'conversion_rows': ROW_COUNT, 'modern_grounding_columns': True}
