"""HG-B05 native consumer for the outgoing U-turn held-item snapshot.

Two tiny resident wrappers replace only the held-effect and modifier calls in
the retail ``TryItemFlinch`` function.  The rest of that function—including
failure gates, damage checks, RNG position, move eligibility and target HP—
remains byte-identical.  The wrappers occupy the reviewed 128-byte tail of the
``c8.module-stubs`` allocation; no save structure or overlay RAM geometry is
changed.
"""
from __future__ import annotations

import hashlib
import importlib.util
import shutil
import struct
import subprocess
import tempfile
import zlib
from pathlib import Path

from sgp12.rom import Rom, bl_decode, bl_thumb
from sgp13.compiler import compiler_environment, compiler_path


SOURCE = Path(__file__).resolve().parents[1]
NATIVE = SOURCE / 'features/type-consumers/uturn.S'

LANGUAGES = ('EN', 'IT')
OVERLAY_ID = 12
OVERLAY_BASE = 0x022378C0
OVERLAY_SIZE = 0x37380

SLOT_NAME = 'c8.module-stubs'
SLOT_START = 0x023D59E0
STUB_BYTES = 64
SLOT_PAYLOAD_BYTES = 192
HELPER_ADDRESS = SLOT_START + STUB_BYTES
HELPER_CAPACITY = 128
HELPER_BYTES = 68
HELPER_SHA256 = '8dfc3389b012ba046fd81df9c4a79119d1ffa4bf044b2462720a1868e0ea7f02'
EFFECT_ENTRY = HELPER_ADDRESS | 1
MODIFIER_ENTRY = (HELPER_ADDRESS + 0x20) | 1
EFFECT_LIVE_CALL = 24
MODIFIER_LIVE_CALL = 62
GET_EFFECT = 0x02255830
GET_MODIFIER = 0x02255844

EFFECT_SITE = 0x0224E084
MODIFIER_SITE = 0x0224E090
EFFECT_PREIMAGE = bytes.fromhex('07f0d4fb')
MODIFIER_PREIMAGE = bytes.fromhex('07f0d8fb')
EFFECT_POSTIMAGE = bytes.fromhex('87f1ccfc')
MODIFIER_POSTIMAGE = bytes.fromhex('87f1d6fc')
FUNCTION = 0x0224E078
FUNCTION_END = 0x0224E130
FUNCTION_PREIMAGE = bytes.fromhex(
    'f8b50d1c696e0090281c002407f0d4fb071c696e281c221c07f0d8fb061ce86e'
    'ff283cd0382f3ad11e496a581e49114235d11c214143b6206a1880001158002903'
    'd108301058002829d00098edf768fe6421a4f666ecb14221da1448285800012918'
    '1348095c2020084218d0e86ec02141436a180f495158002910d0291c9431086028'
    '1c022188300160281c01210e2200f048fda8680124e8601620a860201cf8bdc046'
    '6c21000049da1f8044300000e90300008c2d0000')
_function_after = bytearray(FUNCTION_PREIMAGE)
_function_after[EFFECT_SITE - FUNCTION:EFFECT_SITE - FUNCTION + 4] = EFFECT_POSTIMAGE
_function_after[MODIFIER_SITE - FUNCTION:MODIFIER_SITE - FUNCTION + 4] = MODIFIER_POSTIMAGE
FUNCTION_POSTIMAGE = bytes(_function_after)
FUNCTION_AFTER_SHA256 = '80ca05b40b182b891deaba3163437aac063a6dd3c93916873407fb177c32fd29'
_need_function_hash = hashlib.sha256(FUNCTION_POSTIMAGE).hexdigest()
if _need_function_hash != FUNCTION_AFTER_SHA256:
    raise RuntimeError('U-turn function postimage pin differs')

MODULE_SEED = 0x023D7B60
MODULE_MAGIC = 0x314D4955

COMPILER_VERSION = 'Apple clang version 21.0.0 (clang-2100.4.1.1)'
COMPILER_SHA256 = 'fc5e3cbba6ad54059295cad716aacb05ace8235f5f7a6031f1d8c15d24bd6d66'
FLAGS = ('--target=armv5te-none-eabi', '-mcpu=arm946e-s', '-mthumb',
         '-ffreestanding', '-fno-builtin', '-x', 'assembler-with-cpp')
FREE_SPACE_FLOOR = 10 * 1024**3


def _need(ok, reason):
    if not ok:
        raise ValueError(reason)


def _sha(data):
    return hashlib.sha256(bytes(data)).hexdigest()


def _module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _assignment(allocation):
    _need(type(allocation) is dict and type(allocation.get('assignments')) is list,
          'U-turn helper requires the full reserve allocation receipt')
    rows = [row for row in allocation['assignments']
            if type(row) is dict and row.get('name') == SLOT_NAME]
    _need(len(rows) == 1, 'U-turn helper allocation row missing or duplicated')
    row = rows[0]
    _need((row.get('start'), row.get('bytes'), row.get('capacity'))
          == (SLOT_START, SLOT_PAYLOAD_BYTES, SLOT_PAYLOAD_BYTES),
          'U-turn helper requires the full reviewed C8 slot')
    return row


def compile_native(work_dir: Path):
    """Compile, relocate and authenticate both wrappers at their fixed owner."""
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
                     'uturn_snapshot_object_loader')
    with tempfile.TemporaryDirectory(prefix='uturn-snapshot-', dir=work_dir) as scratch:
        scratch = Path(scratch)
        obj = scratch / 'uturn.o'
        environment = dict(compiler_environment())
        environment['TMPDIR'] = str(scratch)
        done = subprocess.run(
            [compiler, *FLAGS, '-c', str(NATIVE), '-o', str(obj)],
            cwd=scratch, env=environment, capture_output=True, text=True,
            timeout=60)
        _need(done.returncode == 0 and not done.stderr,
              'U-turn wrapper assembly failed: ' + done.stderr)
        raw = obj.read_bytes()
    payload, symbols = loader.load_text(
        raw, HELPER_ADDRESS,
        ('uturn_snapshot_effect', 'uturn_effect_live_call',
         'uturn_snapshot_modifier', 'uturn_modifier_live_call'))
    _need((symbols['uturn_snapshot_effect'] & ~1) == HELPER_ADDRESS
          and symbols['uturn_snapshot_modifier'] == MODIFIER_ENTRY,
          'U-turn wrapper entry geometry')
    payload = bytearray(payload)
    for name, offset, target in (
            ('uturn_effect_live_call', EFFECT_LIVE_CALL, GET_EFFECT),
            ('uturn_modifier_live_call', MODIFIER_LIVE_CALL, GET_MODIFIER)):
        actual = (symbols[name] & ~1) - HELPER_ADDRESS
        _need(actual == offset, name + ' geometry')
        payload[offset:offset + 4] = bl_thumb(HELPER_ADDRESS + offset,
                                             target | 1)
        _need(bl_decode(HELPER_ADDRESS + offset, payload[offset:offset + 4])
              == target, name + ' target')
    payload = bytes(payload)
    _need(len(payload) == HELPER_BYTES and _sha(payload) == HELPER_SHA256,
          'U-turn helper payload drift: ' + _sha(payload))
    return payload, {
        'bytes': len(payload), 'payload_sha256': _sha(payload),
        'object_sha256': _sha(raw), 'source_sha256': _sha(source),
        'entries': {'effect': symbols['uturn_snapshot_effect'],
                    'modifier': symbols['uturn_snapshot_modifier']},
        'live_calls': {'effect': GET_EFFECT, 'modifier': GET_MODIFIER},
        'compiler': {'version': version, 'executable_sha256': COMPILER_SHA256,
                     'flags': list(FLAGS)},
    }


def edits():
    return (
        {'addr': EFFECT_SITE, 'pre': EFFECT_PREIMAGE,
         'post': EFFECT_POSTIMAGE},
        {'addr': MODIFIER_SITE, 'pre': MODIFIER_PREIMAGE,
         'post': MODIFIER_POSTIMAGE},
    )


def patch_overlay(image: bytes):
    """Retarget only the two retail getters in decoded overlay 12."""
    image = bytes(image)
    _need(len(image) == OVERLAY_SIZE, 'overlay 12 image size differs')
    at = FUNCTION - OVERLAY_BASE
    _need(image[at:at + len(FUNCTION_PREIMAGE)] == FUNCTION_PREIMAGE,
          'TryItemFlinch function preimage differs')
    result = bytearray(image)
    for edit in edits():
        offset = edit['addr'] - OVERLAY_BASE
        _need(result[offset:offset + 4] == edit['pre'],
              'U-turn getter preimage differs at %#x' % edit['addr'])
        result[offset:offset + 4] = edit['post']
    result = bytes(result)
    changed = [i for i, pair in enumerate(zip(image, result))
               if pair[0] != pair[1]]
    _need(bl_decode(EFFECT_SITE, EFFECT_POSTIMAGE) == (EFFECT_ENTRY & ~1)
          and bl_decode(MODIFIER_SITE, MODIFIER_POSTIMAGE)
          == (MODIFIER_ENTRY & ~1), 'U-turn wrapper seams differ')
    return result, {
        'effect': {'address': EFFECT_SITE, 'before': EFFECT_PREIMAGE.hex(),
                   'after': EFFECT_POSTIMAGE.hex(),
                   'old_target': GET_EFFECT, 'new_target': EFFECT_ENTRY & ~1},
        'modifier': {'address': MODIFIER_SITE,
                     'before': MODIFIER_PREIMAGE.hex(),
                     'after': MODIFIER_POSTIMAGE.hex(),
                     'old_target': GET_MODIFIER,
                     'new_target': MODIFIER_ENTRY & ~1},
        'changed_offsets': changed,
        'overlay_sha256_before': _sha(image),
        'overlay_sha256_after': _sha(result),
    }


def verify_overlay(before, after, receipt):
    expected, details = patch_overlay(before)
    _need(bytes(after) == expected, 'U-turn overlay output differs')
    _need(receipt == details, 'U-turn overlay receipt differs')
    return {'ok': True, 'logical_changed_bytes': len(details['changed_offsets']),
            'seams': 2}


def _reconcile_ui_seed(before, after):
    from . import ui_verify
    old = ui_verify.Image(before)
    at = old.offset(MODULE_SEED, 96)
    words = struct.unpack_from('<24I', before, at)
    if words[0] != MODULE_MAGIC:
        return after, None
    _need(words[17] == zlib.crc32(before[old.y9:old.y9 + old.y9_bytes]),
          'input UI seed does not match y9')
    _need(before[at:at + 68] == after[at:at + 68]
          and before[at + 72:at + 96] == after[at + 72:at + 96],
          'U-turn writer changed UI seed outside y9 digest')
    digest = zlib.crc32(after[old.y9:old.y9 + old.y9_bytes])
    result = bytearray(after)
    struct.pack_into('<I', result, at + 68, digest)
    return bytes(result), {
        'address': MODULE_SEED + 68, 'rom_offset': at + 68,
        'before_crc32': '%08x' % words[17], 'after_crc32': '%08x' % digest,
    }


def install(data: bytes, language: str, work_dir: Path, *, allocation):
    """Install the helper and two seams in memory; never write a cartridge."""
    from sgp12.overlay import applica
    from . import ui_verify
    _need(type(data) is bytes and language in LANGUAGES,
          'U-turn installer input/language')
    _assignment(allocation)
    payload, native = compile_native(Path(work_dir))
    block = payload + bytes(HELPER_CAPACITY - len(payload))
    image = ui_verify.Image(data)
    at = image.offset(HELPER_ADDRESS, HELPER_CAPACITY)
    _need(data[at:at + HELPER_CAPACITY] == bytes(HELPER_CAPACITY),
          'U-turn helper tail preimage is not zero')
    staged = bytearray(data)
    staged[at:at + HELPER_CAPACITY] = block
    old_image = Rom(data).immagine_overlay(OVERLAY_ID)[2]
    expected, logical = patch_overlay(old_image)
    result, writer = applica(bytes(staged), OVERLAY_ID,
                             [(FUNCTION, FUNCTION_PREIMAGE)], list(edits()))
    _need(Rom(result).immagine_overlay(OVERLAY_ID)[2] == expected,
          'U-turn overlay readback differs')
    result, ui_seed = _reconcile_ui_seed(data, result)
    receipt = {
        'schema': 1, 'stage': 'uturn-flinch', 'language': language,
        'input_sha256': _sha(data), 'output_sha256': _sha(result),
        'allocation': allocation, 'assignment': _assignment(allocation),
        'helper_rom_offset': at, 'native': native, 'logical': logical,
        'overlay': writer, 'ui_seed': ui_seed,
    }
    receipt['verification'] = verify_install(data, result, receipt)
    return result, receipt


def uninstall(data: bytes):
    """Peel this stage from a composed image while preserving earlier edits."""
    from sgp12.overlay import applica
    from . import ui_verify
    _need(type(data) is bytes, 'U-turn peel needs immutable ROM bytes')
    image = ui_verify.Image(data)
    at = image.offset(HELPER_ADDRESS, HELPER_CAPACITY)
    _need(_sha(data[at:at + HELPER_BYTES]) == HELPER_SHA256
          and data[at + HELPER_BYTES:at + HELPER_CAPACITY]
          == bytes(HELPER_CAPACITY - HELPER_BYTES),
          'U-turn peel helper preimage')
    reverse = [
        {'addr': row['addr'], 'pre': row['post'], 'post': row['pre']}
        for row in edits()
    ]
    result, _ = applica(data, OVERLAY_ID,
                        [(FUNCTION, FUNCTION_POSTIMAGE)], reverse)
    staged = bytearray(result)
    staged[at:at + HELPER_CAPACITY] = bytes(HELPER_CAPACITY)
    result, _ = _reconcile_ui_seed(data, bytes(staged))
    logical = Rom(result).immagine_overlay(OVERLAY_ID)[2]
    fn = FUNCTION - OVERLAY_BASE
    _need(logical[fn:fn + len(FUNCTION_PREIMAGE)] == FUNCTION_PREIMAGE,
          'U-turn peel overlay readback')
    return result


def verify_install(before: bytes, after: bytes, receipt: dict):
    """Read back the resident block, decoded overlay and derived seed."""
    from . import ui_verify
    _need(type(before) is bytes and type(after) is bytes and len(before) == len(after),
          'U-turn install geometry')
    _need(type(receipt) is dict and receipt.get('schema') == 1
          and receipt.get('stage') == 'uturn-flinch'
          and receipt.get('language') in LANGUAGES,
          'U-turn install receipt schema')
    _need(receipt.get('input_sha256') == _sha(before)
          and receipt.get('output_sha256') == _sha(after),
          'U-turn install hashes')
    row = _assignment(receipt.get('allocation'))
    _need(receipt.get('assignment') == row, 'U-turn assignment receipt')
    old = ui_verify.Image(before)
    new = ui_verify.Image(after)
    _need((old.fat, old.fat_bytes, old.y9, old.y9_bytes)
          == (new.fat, new.fat_bytes, new.y9, new.y9_bytes),
          'U-turn install moved FAT/y9')
    at = old.offset(HELPER_ADDRESS, HELPER_CAPACITY)
    _need(receipt.get('helper_rom_offset') == at
          and before[at:at + HELPER_CAPACITY] == bytes(HELPER_CAPACITY),
          'U-turn helper preimage/offset')
    payload = after[at:at + HELPER_BYTES]
    _need(_sha(payload) == HELPER_SHA256
          and after[at + HELPER_BYTES:at + HELPER_CAPACITY]
          == bytes(HELPER_CAPACITY - HELPER_BYTES),
          'U-turn helper block readback')
    native = receipt.get('native')
    _need(type(native) is dict and native.get('bytes') == HELPER_BYTES
          and native.get('payload_sha256') == HELPER_SHA256
          and native.get('entries')
          == {'effect': EFFECT_ENTRY, 'modifier': MODIFIER_ENTRY}
          and native.get('live_calls')
          == {'effect': GET_EFFECT, 'modifier': GET_MODIFIER},
          'U-turn native receipt')
    old_image = Rom(before).immagine_overlay(OVERLAY_ID)[2]
    new_image = Rom(after).immagine_overlay(OVERLAY_ID)[2]
    logical = verify_overlay(old_image, new_image, receipt.get('logical'))

    seed_at = old.offset(MODULE_SEED, 96)
    words = struct.unpack_from('<24I', before, seed_at)
    if words[0] == MODULE_MAGIC:
        expected_crc = zlib.crc32(after[old.y9:old.y9 + old.y9_bytes])
        expected_seed = {
            'address': MODULE_SEED + 68, 'rom_offset': seed_at + 68,
            'before_crc32': '%08x' % words[17],
            'after_crc32': '%08x' % expected_crc,
        }
        _need(receipt.get('ui_seed') == expected_seed
              and struct.unpack_from('<I', after, seed_at + 68)[0]
              == expected_crc,
              'U-turn UI seed readback')
        _need(before[seed_at:seed_at + 68] == after[seed_at:seed_at + 68]
              and before[seed_at + 72:seed_at + 96]
              == after[seed_at + 72:seed_at + 96],
              'U-turn UI seed complement')
    else:
        _need(receipt.get('ui_seed') is None,
              'U-turn non-UI seed receipt')
    result = {'ok': True, 'native_bytes': HELPER_BYTES,
              'helper_capacity': HELPER_CAPACITY, 'logical': logical}
    existing = receipt.get('verification')
    _need(existing in (None, result), 'U-turn verification receipt differs')
    return result
