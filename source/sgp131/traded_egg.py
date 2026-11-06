"""HG-T12: classify the hatch palette with the final hatcher OT.

Overlay 95 builds the hatch sprite before ``MonSetTrainerMemo(strategy=6)``
installs the hatcher as final OT.  The hook keeps that ordering and delegates
the whole sprite-template build to the original function; it replaces only
the low shiny bit of ``palDataID`` using the player profile already passed to
the hatch task.
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

from sgp12.blz import blz_comprimi_ottimo
from sgp12.rom import Arm9, Rom, bl_decode, bl_thumb
from sgp13.compiler import compiler_environment, compiler_path


SOURCE = Path(__file__).resolve().parents[1]
NATIVE = SOURCE / 'features/traded-egg/native.S'
LANGUAGES = ('EN', 'IT')

OVERLAY_ID = 95
OVERLAY_BASE = 0x021E5900
OVERLAY_SIZE = 0x1FC0
OVERLAY_SHA256 = '337162d87e125fb77900fed2087dbfcc007525838a63187f88e640c4b61a8dac'
CALL_SITE = 0x021E6270
CALL_PREIMAGE = bytes.fromhex('89f658ff')
CONTEXT = (0x021E623C, 0x021E6290)
CONTEXT_SHA256 = '98cb278e2c82c5cdf852e631ea5a9e99ede88f1d0d28feb1788085e08143d505'

HELPER_ADDRESS = OVERLAY_BASE + OVERLAY_SIZE
PAYLOAD_BYTES = 44
PAYLOAD_SHA256 = 'cae05eaa01717185fa19b4dc8a46a5df5a92f0a8bbc13ba8e71949a9fddcb055'
GET_SPRITE_IDS = 0x02070124
GET_MON_DATA = 0x0206E540
IS_SHINY = 0x02070068
CALL_SYMBOLS = (
    ('traded_egg_sprite_call', GET_SPRITE_IDS),
    ('traded_egg_get_pid_call', GET_MON_DATA),
    ('traded_egg_shiny_call', IS_SHINY),
)

MODULE_SEED = 0x023D7B60
MODULE_MAGIC = 0x314D4955
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


def plus_is_shiny(ot_id, personality):
    """The shipped Plus rule: XOR of the four halfwords is below 255."""
    value = ((ot_id & 0xFFFF) ^ (ot_id >> 16) ^
             (personality & 0xFFFF) ^ (personality >> 16))
    return value < 255


def final_palette_id(palette, hatcher_ot, personality):
    """Replace only the palette's normal/shiny low bit."""
    return (palette & ~1) | int(plus_is_shiny(hatcher_ot, personality))


def compile_native(work_dir: Path):
    """Compile and bind the exact overlay-local 44-byte Thumb helper."""
    work_dir = Path(work_dir)
    _need(shutil.disk_usage(work_dir).free >= FREE_SPACE_FLOOR,
          'free-space floor (10 GiB)')
    compiler = compiler_path(COMPILER_SHA256)
    version = subprocess.run(
        [compiler, '--version'], env=compiler_environment(), capture_output=True,
        text=True, check=True).stdout.splitlines()[0]
    _need(version == COMPILER_VERSION, 'compiler version drift: ' + version)
    source = NATIVE.read_bytes()
    loader = _module(SOURCE / 'features/options/tools/carica_text.py',
                     'traded_egg_object_loader')
    names = ('traded_egg_palette_hook', *(name for name, _ in CALL_SYMBOLS))
    with tempfile.TemporaryDirectory(prefix='traded-egg-', dir=work_dir) as scratch:
        scratch = Path(scratch)
        obj = scratch / 'native.o'
        environment = dict(compiler_environment())
        environment['TMPDIR'] = str(scratch)
        done = subprocess.run(
            [compiler, *FLAGS, '-c', str(NATIVE), '-o', str(obj)],
            cwd=scratch, env=environment, capture_output=True, text=True,
            timeout=60)
        _need(done.returncode == 0 and not done.stderr,
              'native assembly failed: ' + done.stderr)
        raw = obj.read_bytes()
    payload, symbols = loader.load_text(raw, HELPER_ADDRESS, names)
    _need((symbols['traded_egg_palette_hook'] & ~1) == HELPER_ADDRESS,
          'helper entry geometry')
    payload = bytearray(payload)
    call_offsets = []
    for name, target in CALL_SYMBOLS:
        offset = (symbols[name] & ~1) - HELPER_ADDRESS
        _need(0 <= offset <= len(payload) - 4 and offset % 2 == 0,
              'native call geometry')
        payload[offset:offset + 4] = bl_thumb(HELPER_ADDRESS + offset, target | 1)
        call_offsets.append(offset)
    payload = bytes(payload)
    _need(len(payload) == PAYLOAD_BYTES, 'native payload size drift')
    _need(_sha(payload) == PAYLOAD_SHA256,
          'native payload drift: ' + _sha(payload))
    targets = [bl_decode(HELPER_ADDRESS + offset, payload[offset:offset + 4])
               for offset in call_offsets]
    _need(targets == [target for _, target in CALL_SYMBOLS],
          'native call target drift')
    return payload, {
        'bytes': len(payload), 'payload_sha256': _sha(payload),
        'source_sha256': _sha(source), 'object_sha256': _sha(raw),
        'entry': symbols['traded_egg_palette_hook'],
        'call_offsets': call_offsets, 'call_targets': targets,
        'stack_delta': 0, 'preserved_registers': ['r4', 'r5', 'r6', 'r7'],
        'compiler': {'version': version, 'executable_sha256': COMPILER_SHA256,
                     'flags': list(FLAGS)},
    }


def patch_overlay(image: bytes, payload: bytes, *,
                  overlay_sha256=OVERLAY_SHA256,
                  context_sha256=CONTEXT_SHA256):
    """Retarget the one sprite call and append the authenticated helper."""
    image, payload = bytes(image), bytes(payload)
    _need(len(image) == OVERLAY_SIZE, 'overlay 95 size differs')
    _need(len(payload) == PAYLOAD_BYTES and _sha(payload) == PAYLOAD_SHA256,
          'native payload identity')
    if overlay_sha256 is not None:
        _need(_sha(image) == overlay_sha256, 'overlay 95 identity differs')
    context = image[CONTEXT[0] - OVERLAY_BASE:CONTEXT[1] - OVERLAY_BASE]
    if context_sha256 is not None:
        _need(_sha(context) == context_sha256, 'overlay 95 call context differs')
    at = CALL_SITE - OVERLAY_BASE
    _need(image[at:at + 4] == CALL_PREIMAGE, 'overlay 95 call preimage differs')
    _need(bl_decode(CALL_SITE, CALL_PREIMAGE) == GET_SPRITE_IDS,
          'pinned sprite target differs')
    result = bytearray(image)
    result[at:at + 4] = bl_thumb(CALL_SITE, HELPER_ADDRESS | 1)
    result += payload
    changed = [i for i, (old, new) in enumerate(zip(image, result)) if old != new]
    return bytes(result), {
        'call_site': CALL_SITE, 'preimage': CALL_PREIMAGE.hex(),
        'replacement': bytes(result[at:at + 4]).hex(),
        'old_target': GET_SPRITE_IDS, 'new_target': HELPER_ADDRESS,
        'appended': len(payload), 'changed_offsets': changed,
        'overlay_sha256_before': _sha(image),
        'overlay_sha256_after': _sha(result),
    }


def verify_images(before, after, payload):
    expected, logical = patch_overlay(
        before, payload, overlay_sha256=None, context_sha256=None)
    _need(bytes(after) == expected,
          'decoded overlay differs from the call seam and appended helper')
    return logical


def _seed_offset(data):
    return Arm9.from_bytes(bytes(data)).off(MODULE_SEED, 96)


def _reconcile_ui_seed(before, after):
    at = _seed_offset(before)
    words = struct.unpack_from('<24I', before, at)
    if words[0] != MODULE_MAGIC:
        return bytes(after), None
    y9, y9_bytes = struct.unpack_from('<II', before, 0x50)
    _need(words[17] == zlib.crc32(before[y9:y9 + y9_bytes]),
          'input UI seed does not match y9')
    _need(before[at:at + 68] == after[at:at + 68]
          and before[at + 72:at + 96] == after[at + 72:at + 96],
          'UI seed changed outside its derived y9 word')
    digest = zlib.crc32(after[y9:y9 + y9_bytes])
    result = bytearray(after)
    struct.pack_into('<I', result, at + 68, digest)
    return bytes(result), {
        'address': MODULE_SEED + 68, 'rom_offset': at + 68,
        'before_crc32': '%08x' % words[17], 'after_crc32': '%08x' % digest,
    }


def _ranges(before, after):
    found = []
    for index, (old, new) in enumerate(zip(before, after)):
        if old != new:
            if found and found[-1][1] == index:
                found[-1][1] = index + 1
            else:
                found.append([index, index + 1])
    return found


def _write_overlay(data, image):
    rom = Rom(data)
    entry = rom.voce_overlay(OVERLAY_ID)
    _need((entry['id'], entry['ram'], entry['ram_size'], entry['file_id'],
           entry['bss_size']) ==
          (OVERLAY_ID, OVERLAY_BASE, OVERLAY_SIZE, OVERLAY_ID, 0),
          'overlay 95 placement differs')
    fat = rom.voce_fat(entry['file_id'])
    capacity = rom.capienza_slot(entry['file_id'])
    padding = data[fat['fine']:fat['inizio'] + capacity]
    _need(not padding or len(set(padding)) == 1 and padding[0] in (0, 0xFF),
          'overlay 95 following slot is not uniform cartridge padding')
    pad_byte = padding[:1] or b'\xFF'
    stream = blz_comprimi_ottimo(image, bersaglio=fat['bytes'])
    _need(len(stream) <= capacity, 'expanded overlay 95 exceeds its physical slot')
    result = bytearray(data)
    new_end = fat['inizio'] + len(stream)
    result[fat['inizio']:new_end] = stream
    result[new_end:max(fat['fine'], new_end)] = pad_byte * (max(fat['fine'], new_end) - new_end)
    struct.pack_into('<I', result, fat['offset_voce'] + 4, new_end)
    struct.pack_into('<I', result, entry['offset_voce'] + 8, len(image))
    struct.pack_into('<I', result, entry['offset_voce'] + 28,
                     (entry['parola_comp'] & 0xFF000000) | len(stream))
    return bytes(result), {
        'slot_start': fat['inizio'], 'slot_capacity': capacity,
        'compressed_before': fat['bytes'], 'compressed_after': len(stream),
        'decoded_before': OVERLAY_SIZE, 'decoded_after': len(image),
        'fat_entry': fat['offset_voce'], 'y9_entry': entry['offset_voce'],
        'padding_byte': pad_byte.hex(),
    }


def spans(data: bytes):
    """Physical cartridge regions owned by the post-UI HG-T12 stage."""
    data = bytes(data)
    rom = Rom(data)
    entry = rom.voce_overlay(OVERLAY_ID)
    fat = rom.voce_fat(entry['file_id'])
    slot_end = fat['inizio'] + rom.capienza_slot(entry['file_id'])
    result = [
        (fat['inizio'], slot_end, 'overlay 95 physical slot'),
        (fat['offset_voce'], fat['offset_voce'] + 8, 'overlay 95 FAT entry'),
        (entry['offset_voce'] + 8, entry['offset_voce'] + 12,
         'overlay 95 y9 ram size'),
        (entry['offset_voce'] + 28, entry['offset_voce'] + 32,
         'overlay 95 y9 compressed size'),
    ]
    seed_at = _seed_offset(data)
    result.append((seed_at + 68, seed_at + 72,
                   'ui.module.seed derived y9 crc32'))
    return result


def apply(data: bytes, language: str):
    _need(language in LANGUAGES, 'unsupported language')
    data = bytes(data)
    old_image = Rom(data).immagine_overlay(OVERLAY_ID)[2]
    with tempfile.TemporaryDirectory(prefix='traded-egg-build-') as scratch:
        payload, native = compile_native(Path(scratch))
    new_image, logical = patch_overlay(old_image, payload)
    result, writer = _write_overlay(data, new_image)
    result, ui_seed = _reconcile_ui_seed(data, result)
    _need(Rom(result).immagine_overlay(OVERLAY_ID)[2] == new_image,
          'expanded overlay 95 readback differs')
    receipt = {
        'schema': 1, 'stage': 'traded-egg', 'language': language,
        'input_sha256': _sha(data), 'output_sha256': _sha(result),
        'native': native, 'logical': logical, 'writer': writer,
        'ui_seed': ui_seed,
    }
    receipt['verification'] = verify(data, result, receipt)
    return result, receipt


def verify(before: bytes, after: bytes, receipt: dict):
    import ndspy.codeCompression as codec

    before, after = bytes(before), bytes(after)
    _need(len(before) == len(after), 'traded-egg stage changed ROM length')
    _need(type(receipt) is dict and receipt.get('schema') == 1
          and receipt.get('input_sha256') == _sha(before)
          and receipt.get('output_sha256') == _sha(after),
          'traded-egg receipt hashes differ')
    old_rom, new_rom = Rom(before), Rom(after)
    old_entry = old_rom.voce_overlay(OVERLAY_ID)
    new_entry = new_rom.voce_overlay(OVERLAY_ID)
    _need(old_entry['offset_voce'] == new_entry['offset_voce']
          and old_entry['ram'] == new_entry['ram'] == OVERLAY_BASE
          and old_entry['file_id'] == new_entry['file_id'] == OVERLAY_ID
          and old_entry['ram_size'] == OVERLAY_SIZE
          and new_entry['ram_size'] == OVERLAY_SIZE + PAYLOAD_BYTES
          and old_entry['parola_comp'] >> 24 == new_entry['parola_comp'] >> 24,
          'overlay 95 y9 geometry differs')
    old_fat = old_rom.voce_fat(OVERLAY_ID)
    new_fat = new_rom.voce_fat(OVERLAY_ID)
    _need(old_fat['inizio'] == new_fat['inizio'], 'overlay 95 moved')
    following = old_fat['inizio'] + old_rom.capienza_slot(OVERLAY_ID)
    _need(new_fat['fine'] <= following, 'overlay 95 exceeds its physical slot')
    old_padding = before[old_fat['fine']:following]
    _need(not old_padding or len(set(old_padding)) == 1 and old_padding[0] in (0, 0xFF),
          'overlay 95 input padding is not uniform')
    padding_byte = old_padding[:1] or b'\xFF'
    _need(set(after[new_fat['fine']:max(old_fat['fine'], new_fat['fine'])])
          <= {padding_byte[0]}, 'overlay 95 slot tail is not cartridge padding')
    old_image = old_rom.immagine_overlay(OVERLAY_ID)[2]
    new_stream = after[new_fat['inizio']:new_fat['fine']]
    new_image = new_rom.immagine_overlay(OVERLAY_ID)[2]
    _need(bytes(codec.decompress(new_stream)) == new_image,
          'independent overlay 95 decoders disagree')
    _need(blz_comprimi_ottimo(new_image, bersaglio=old_fat['bytes']) == new_stream,
          'overlay 95 is not the canonical writer output')
    payload = new_image[OVERLAY_SIZE:]
    _need(_sha(payload) == PAYLOAD_SHA256, 'installed helper identity differs')
    logical = verify_images(old_image, new_image, payload)
    _need(receipt.get('logical') == logical, 'logical receipt differs')
    native = receipt.get('native')
    _need(type(native) is dict and native.get('bytes') == PAYLOAD_BYTES
          and native.get('payload_sha256') == PAYLOAD_SHA256
          and native.get('call_targets') == [target for _, target in CALL_SYMBOLS],
          'native receipt differs')

    seed_at = _seed_offset(before)
    words = struct.unpack_from('<24I', before, seed_at)
    seed_zone = []
    if words[0] == MODULE_MAGIC:
        y9, y9_bytes = struct.unpack_from('<II', before, 0x50)
        expected_crc = zlib.crc32(after[y9:y9 + y9_bytes])
        _need(struct.unpack_from('<I', after, seed_at + 68)[0] == expected_crc,
              'UI y9 seed was not reconciled')
        _need(before[seed_at:seed_at + 68] == after[seed_at:seed_at + 68]
              and before[seed_at + 72:seed_at + 96] == after[seed_at + 72:seed_at + 96],
              'UI seed changed outside y9 crc32')
        expected_seed = {
            'address': MODULE_SEED + 68, 'rom_offset': seed_at + 68,
            'before_crc32': '%08x' % words[17],
            'after_crc32': '%08x' % expected_crc,
        }
        _need(receipt.get('ui_seed') == expected_seed, 'UI seed receipt differs')
        seed_zone = [(seed_at + 68, seed_at + 72)]
    else:
        _need(receipt.get('ui_seed') is None,
              'non-UI input unexpectedly reports a seed update')

    y9 = old_entry['offset_voce']
    zones = [
        (old_fat['inizio'], max(old_fat['fine'], new_fat['fine'])),
        (old_fat['offset_voce'], old_fat['offset_voce'] + 8),
        (y9 + 8, y9 + 12), (y9 + 28, y9 + 32),
    ] + seed_zone
    outside = [span for span in _ranges(before, after)
               if not any(start <= span[0] and span[1] <= end
                          for start, end in zones)]
    _need(not outside, 'ROM changed outside declared zones: %s' % outside[:8])
    return {
        'ok': True, 'canonical_blz': True,
        'logical_changed_bytes': len(logical['changed_offsets']) + PAYLOAD_BYTES,
        'payload_sha256': PAYLOAD_SHA256,
        'compressed_bytes': [old_fat['bytes'], new_fat['bytes']],
        'ui_y9_seed_reconciled': bool(seed_zone),
        'zones': [(hex(start), hex(end)) for start, end in zones],
    }
