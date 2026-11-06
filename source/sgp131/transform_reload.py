"""HG-B08 in-place repair for level-up while Transform is active.

The retail reload function overwrites the five copied combat stats before it
checks ``STATUS2_TRANSFORM``.  This exact-span replacement guards only those
five reads.  Level, friendship, HP and max HP still reload; the existing
Transform/Mimic treatment of moves, PP, PP Ups and experience is preserved.
"""
from __future__ import annotations

import hashlib
import importlib.util
import shutil
import struct
import subprocess
import tempfile
from pathlib import Path

from sgp13.compiler import compiler_environment, compiler_path


SOURCE = Path(__file__).resolve().parents[1]
NATIVE = SOURCE / 'features/type-consumers/reload_transform.S'

OVERLAY_BASE = 0x022378C0
OVERLAY_SIZE = 0x37380
RELOAD_ADDRESS = 0x0224EA14
RELOAD_BYTES = 340
RELOAD_PREIMAGE = bytes.fromhex(
    'f8b584b0151c0091291c1a1cebf72effc02169430191a5210022061c1ff686fd'
    '009a019952184b495052301ca62100221ff67cfd009a0199521847495052301ca7'
    '2100221ff672fd009a0199521843495052301ca82100221ff668fd009a01995218'
    '3f495052301ca92100221ff65efd009a019952183b495052301ca12100221ff654'
    'fd009a0199521837495054301c092100221ff64afd009a0199521833495054301c'
    'a32100221ff640fd009a019952182f495050301ca42100221ff636fd009a019952'
    '182b495050081c203012580220000510423bd1c0206843009a029017183c31101c'
    '401800243d1c0390201c23f6dcfd039a029951588906090f084217d1211c301c36'
    '3100221ff60ffd1a4900227852211c301c3a311ff607fd174900226854211c301c'
    '3e311ff6fffc14496854641cbf1c6d1c042cd8db301c082100221ff6f3fc009a'
    '019952180d49505004b0f8bd')
RELOAD_PREIMAGE_SHA256 = 'be3d7eed5638700df69d0d701dd7e5d0ca4564ef516f92abeb1a12d7e57f08a2'
LITERAL_ADDRESS = RELOAD_ADDRESS + RELOAD_BYTES
LITERAL_PREIMAGE = bytes.fromhex(
    '422d0000442d0000462d0000482d00004a2d0000742d0000752d00008c2d0000'
    '902d00004c2d00006c2d0000702d0000a42d0000')
LITERAL_SHA256 = 'cee233e2d20a36a9ea65ba6bee1bea92392467730e62773bd2a1102b07dbd142'

GET_PARTY_MON = 0x0223A880
GET_MON_DATA = 0x0206E540
PAYLOAD_SHA256 = '41ad8522c1920ccf38115b5e971d28ec9ae0126536756d002379e0624eb2f942'
PAYLOAD_BATTLE_MONS_OFFSET = 0x110
PAYLOAD_PARTY_TARGET_OFFSET = 0x114
PAYLOAD_DATA_TARGET_OFFSET = 0x118

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
    """Compile and authenticate the exact 340-byte function replacement."""
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
                     'transform_reload_object_loader')
    with tempfile.TemporaryDirectory(prefix='transform-reload-', dir=work_dir) as scratch:
        scratch = Path(scratch)
        obj = scratch / 'reload_transform.o'
        environment = dict(compiler_environment())
        environment['TMPDIR'] = str(scratch)
        done = subprocess.run(
            [compiler, *FLAGS, '-c', str(NATIVE), '-o', str(obj)],
            cwd=scratch, env=environment, capture_output=True, text=True,
            timeout=60)
        _need(done.returncode == 0 and not done.stderr,
              'Transform reload assembly failed: ' + done.stderr)
        raw = obj.read_bytes()
    payload, symbols = loader.load_text(raw, RELOAD_ADDRESS, ('reload_mon_data',))
    payload = bytes(payload)
    _need(symbols['reload_mon_data'] == (RELOAD_ADDRESS | 1),
          'Transform reload entry geometry')
    _need(len(payload) == RELOAD_BYTES,
          'Transform reload replacement does not fill the exact retail span')
    _need(_sha(payload) == PAYLOAD_SHA256,
          'Transform reload payload drift: ' + _sha(payload))
    _need(struct.unpack_from('<I', payload, PAYLOAD_BATTLE_MONS_OFFSET)[0] == 0x2D40,
          'BattleMon base literal differs')
    _need(struct.unpack_from('<I', payload, PAYLOAD_PARTY_TARGET_OFFSET)[0]
          == (GET_PARTY_MON | 1), 'GetPartyMon target differs')
    _need(struct.unpack_from('<I', payload, PAYLOAD_DATA_TARGET_OFFSET)[0]
          == (GET_MON_DATA | 1), 'GetMonData target differs')
    return payload, {
        'bytes': len(payload), 'payload_sha256': _sha(payload),
        'object_sha256': _sha(raw), 'source_sha256': _sha(source),
        'entry': symbols['reload_mon_data'],
        'party_target': GET_PARTY_MON | 1, 'data_target': GET_MON_DATA | 1,
        'compiler': {'version': version, 'executable_sha256': COMPILER_SHA256,
                     'flags': list(FLAGS)},
    }


def edits(payload):
    payload = bytes(payload)
    _need(len(payload) == RELOAD_BYTES and _sha(payload) == PAYLOAD_SHA256,
          'Transform reload payload identity')
    return [{'addr': RELOAD_ADDRESS, 'pre': RELOAD_PREIMAGE, 'post': payload}]


def patch_overlay(image: bytes, payload: bytes):
    """Replace only the authenticated retail reload function."""
    image = bytes(image)
    _need(len(image) == OVERLAY_SIZE, 'overlay 12 image size differs')
    literal = LITERAL_ADDRESS - OVERLAY_BASE
    _need(image[literal:literal + len(LITERAL_PREIMAGE)] == LITERAL_PREIMAGE,
          'Transform reload literal-pool preimage differs')
    result = bytearray(image)
    for edit in edits(payload):
        at = edit['addr'] - OVERLAY_BASE
        _need(result[at:at + len(edit['pre'])] == edit['pre'],
              'Transform reload function preimage differs')
        result[at:at + len(edit['post'])] = edit['post']
    result = bytes(result)
    changed = [i for i, pair in enumerate(zip(image, result))
               if pair[0] != pair[1]]
    _need(changed, 'Transform reload patch changed no bytes')
    return result, {
        'address': RELOAD_ADDRESS, 'bytes': RELOAD_BYTES,
        'before_sha256': RELOAD_PREIMAGE_SHA256,
        'after_sha256': PAYLOAD_SHA256,
        'literal_pool_sha256': LITERAL_SHA256,
        'preserved_while_transformed': ['atk', 'def', 'speed', 'sp_atk', 'sp_def'],
        'still_reloaded': ['level', 'friendship', 'hp', 'max_hp'],
        'changed_offsets': changed,
        'overlay_sha256_before': _sha(image),
        'overlay_sha256_after': _sha(result),
    }


def verify_overlay(before, after, payload, receipt):
    expected, details = patch_overlay(before, payload)
    _need(bytes(after) == expected, 'Transform reload overlay output differs')
    _need(receipt == details, 'Transform reload receipt differs')
    return {'ok': True, 'logical_changed_bytes': len(details['changed_offsets']),
            'function_bytes': RELOAD_BYTES, 'transform_stats_preserved': 5}


_need(len(RELOAD_PREIMAGE) == RELOAD_BYTES, 'reload preimage length differs')
_need(_sha(RELOAD_PREIMAGE) == RELOAD_PREIMAGE_SHA256,
      'reload preimage hash differs')
_need(_sha(LITERAL_PREIMAGE) == LITERAL_SHA256,
      'reload literal-pool hash differs')
