"""Resident Fairy support plus the remaining modern-type consumers.

The Plus damage engine has an 18x18 chart, but the trainer AI still consumes
the sparse retail chart and therefore never sees Fairy interactions.  This
stage installs one 148-byte Thumb helper in an explicitly assigned zero-filled
reserve slot and redirects two overlay-12 seams:

* the flag-producing effectiveness walk and its loop backedge;
* the scalar score tail.

The resident helper handles only rows or columns involving type 9 (Fairy).
The same canonical overlay rewrite also installs the exact in-place SG-AI02
Conversion2 helper and SG-DM01 grounding-column correction.  Every unrelated
pair continues through the native semantics.
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

from sgp12.rom import Rifiuto, Rom, bl_decode, bl_thumb, valida_layout_arm9
from sgp13.compiler import compiler_environment, compiler_path


SOURCE = Path(__file__).resolve().parents[1]
FEATURE = SOURCE / 'features/fairy-ai'
NATIVE = FEATURE / 'native.S'

LANGUAGES = ('EN', 'IT')
OVERLAY_ID = 12
OVERLAY_BASE = 0x022378C0
OVERLAY_SIZE = 0x37380
FLAGS_SITE = 0x022520C6
SCALAR_SITE = 0x0225268E
FLAGS_PREIMAGE = bytes.fromhex('00246000')
SCALAR_PREIMAGE = bytes.fromhex('081cf8bd')
# The original backedge targeted the second halfword of FLAGS_PREIMAGE.
# After installing BL there, that target would execute a lone BL suffix with
# an unrelated LR. The existing loop tail already leaves R1 = 3 * R4;
# resume at the literal load, keeping that index and bypassing the hook.
LOOP_SITE = 0x02252138
LOOP_PREIMAGE = bytes.fromhex('c6d1')
LOOP_REPLACEMENT = bytes.fromhex('c8d1')
LOOP_TARGET = 0x022520CC
CONTEXTS = (
    (0x022520B6, bytes.fromhex(
        '0b986a2804d0316808200843306039e000246000211829484518415cfe2904d101987128')),
    (0x0225267E, bytes.fromhex(
        '0a21a0f68ae9011ce41c2078ff28e4d1081cf8bdc0467ccc2602002811d0d6280fd0094a')),
    (0x0225212E, bytes.fromhex('600021181048405cff28c6d1')),
)

DEFAULT_SLOT = 0x023D746C
SLOT_NAME = 'fairy-ai.code'
PAYLOAD_BYTES = 148
SCALAR_OFFSET = 60
FAIRY_CODE_OFFSET = 94
APPLY_CALL_OFFSETS = (24, 50)
NATIVE_APPLY = 0x022521C8
PACKED_CODES = bytes.fromhex('6e aa 99 aa 6f ae b9 aa 4a')
PAYLOAD_SHA256 = 'd965f5ffa34f4c696189be23313bf69a51a7e2a7abaf77c0228ea2ed521b2a6f'
MODULE_SEED = 0x023D7B60
MODULE_MAGIC = 0x314D4955

COMPILER_VERSION = 'Apple clang version 21.0.0 (clang-2100.4.1.1)'
COMPILER_SHA256 = 'fc5e3cbba6ad54059295cad716aacb05ace8235f5f7a6031f1d8c15d24bd6d66'
FLAGS = ('--target=armv5te-none-eabi', '-mcpu=arm946e-s', '-mthumb',
         '-ffreestanding', '-fno-builtin', '-x', 'assembler-with-cpp')
FREE_SPACE_FLOOR = 10 * 1024**3


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _check_address(address):
    _require(type(address) is int and address % 4 == 0,
             'owned address must be a 4-byte-aligned integer')
    _require(0x02000000 <= address and address + PAYLOAD_BYTES <= 0x02400000,
             'owned address outside main RAM')
    for site, offset in ((FLAGS_SITE, 0), (SCALAR_SITE, SCALAR_OFFSET)):
        delta = address + offset - (site + 4)
        _require(-0x400000 <= delta < 0x400000,
                 'owned address outside Thumb BL range')


def slot_contract(start, size):
    """Return the only slot shape this owner accepts: exact and zero-filled."""
    _check_address(start)
    _require(start == DEFAULT_SLOT,
             'Fairy AI slot must use the reviewed fixed address')
    _require(type(size) is int and size == PAYLOAD_BYTES,
             'Fairy AI slot must be exactly 148 bytes')
    return {'name': SLOT_NAME, 'start': start, 'bytes': size,
            'preimage_sha256': _sha(bytes(size))}


def _check_slot(slot):
    _require(type(slot) is dict and set(slot) == {
        'name', 'start', 'bytes', 'preimage_sha256'},
        'reserve slot assignment required: {name, start, bytes, preimage_sha256}')
    _require(slot.get('name') == SLOT_NAME, 'Fairy AI reserve slot owner differs')
    expected = slot_contract(slot.get('start'), slot.get('bytes'))
    _require(slot == expected, 'Fairy AI reserve slot must carry the exact zero preimage')


def compile_native(work_dir: Path, owned_address: int) -> tuple[bytes, dict]:
    """Compile and relocate the exact 148-byte helper for ``owned_address``."""
    _check_address(owned_address)
    _require(owned_address == DEFAULT_SLOT,
             'Fairy AI payload identity is pinned to the reviewed fixed slot')
    compiler = compiler_path(COMPILER_SHA256)
    _require(compiler is not None, 'pinned clang unavailable')
    work_dir = Path(work_dir)
    _require(shutil.disk_usage(work_dir).free >= FREE_SPACE_FLOOR,
             'free-space floor (10 GiB)')
    version = subprocess.run(
        [compiler, '--version'], env=compiler_environment(), capture_output=True,
        text=True, check=True).stdout.splitlines()[0]
    _require(version == COMPILER_VERSION, 'compiler version drift: ' + version)
    _require(_sha(Path(compiler).resolve().read_bytes()) == COMPILER_SHA256,
             'compiler binary drift')
    source = NATIVE.read_bytes()
    loader = _module(SOURCE / 'features/options/tools/carica_text.py',
                     'fairy_ai_object_loader')
    with tempfile.TemporaryDirectory(prefix='fairy-ai-', dir=work_dir) as scratch:
        scratch = Path(scratch)
        obj = scratch / 'native.o'
        command = [compiler, *FLAGS, '-c', str(NATIVE), '-o', str(obj)]
        environment = dict(compiler_environment())
        environment['TMPDIR'] = str(scratch)
        done = subprocess.run(command, cwd=scratch, env=environment,
                              capture_output=True, text=True, timeout=60)
        _require(done.returncode == 0 and not done.stderr,
                 'native assembly failed: ' + done.stderr)
        raw = obj.read_bytes()
    payload, symbols = loader.load_text(
        raw, owned_address,
        ('fairy_flags_hook', 'fairy_scalar_tail', 'fairy_apply_call_1',
         'fairy_apply_call_2'))
    _require((symbols['fairy_flags_hook'] & ~1) == owned_address,
             'flags entry geometry')
    _require((symbols['fairy_scalar_tail'] & ~1) == owned_address + SCALAR_OFFSET,
             'scalar entry geometry')
    call_offsets = tuple((symbols[name] & ~1) - owned_address for name in
                         ('fairy_apply_call_1', 'fairy_apply_call_2'))
    _require(call_offsets == APPLY_CALL_OFFSETS, 'native apply call geometry')
    payload = bytearray(payload)
    for offset in call_offsets:
        payload[offset:offset + 4] = bl_thumb(owned_address + offset,
                                              NATIVE_APPLY | 1)
    payload = bytes(payload)
    _require(len(payload) == PAYLOAD_BYTES, 'Fairy AI payload must fill 148 bytes')
    _require(_sha(payload) == PAYLOAD_SHA256, 'Fairy AI payload drift: ' + _sha(payload))
    semantics = _payload_semantics(payload)
    return payload, {
        'address': owned_address, 'bytes': len(payload), 'budget': PAYLOAD_BYTES,
        'payload_sha256': _sha(payload), 'object_sha256': _sha(raw),
        'source_sha256': _sha(source),
        'entries': {'flags': symbols['fairy_flags_hook'],
                    'scalar': symbols['fairy_scalar_tail']},
        'apply_call_offsets': list(call_offsets),
        'native_apply_targets': [NATIVE_APPLY, NATIVE_APPLY],
        'compiler': {'version': version, 'executable_sha256': COMPILER_SHA256,
                     'flags': list(FLAGS)},
        'semantics': semantics,
    }


def seam_bytes(owned_address):
    _check_address(owned_address)
    return {
        FLAGS_SITE: bl_thumb(FLAGS_SITE, owned_address | 1),
        SCALAR_SITE: bl_thumb(SCALAR_SITE,
                              owned_address + SCALAR_OFFSET | 1),
    }


def patch_overlay(image: bytes, owned_address: int) -> tuple[bytes, dict]:
    """Patch two calls and keep the native loop out of the BL suffix."""
    _check_address(owned_address)
    image = bytes(image)
    _require(len(image) == OVERLAY_SIZE, 'overlay 12 image size differs')
    for address, context in CONTEXTS:
        offset = address - OVERLAY_BASE
        _require(image[offset:offset + len(context)] == context,
                 'Fairy AI seam context differs at %#x' % address)
    seams = seam_bytes(owned_address)
    result = bytearray(image)
    for address, preimage in ((FLAGS_SITE, FLAGS_PREIMAGE),
                              (SCALAR_SITE, SCALAR_PREIMAGE)):
        offset = address - OVERLAY_BASE
        _require(result[offset:offset + 4] == preimage,
                 'Fairy AI seam preimage differs or is already patched at %#x' % address)
        result[offset:offset + 4] = seams[address]
    offset = LOOP_SITE - OVERLAY_BASE
    result[offset:offset + 2] = LOOP_REPLACEMENT
    result = bytes(result)
    changed = [i for i, (old, new) in enumerate(zip(image, result)) if old != new]
    return result, {
        'sites': [
            {'address': address, 'preimage': pre.hex(),
             'replacement': seams[address].hex(),
             'target': bl_decode(address, seams[address])}
            for address, pre in ((FLAGS_SITE, FLAGS_PREIMAGE),
                                 (SCALAR_SITE, SCALAR_PREIMAGE))],
        'loop_backedge': {'address': LOOP_SITE,
                          'preimage': LOOP_PREIMAGE.hex(),
                          'replacement': LOOP_REPLACEMENT.hex(),
                          'target': LOOP_TARGET},
        'changed_offsets': changed,
        'overlay_sha256_before': _sha(image),
        'overlay_sha256_after': _sha(result),
    }


def _arm9_map(data):
    offset, _, base, length = struct.unpack_from('<4I', data, 0x20)
    table, table_end, body, _bss, _, packed = struct.unpack_from(
        '<6I', data, offset + 0xBA0)
    _require(base == 0x02000000 and not packed
             and base < body <= table <= table_end <= base + length,
             'ARM9 initialized layout')
    _t0, _t1, _d0, _sections, segments = valida_layout_arm9(
        data, offset, base, length)
    return segments


def _arm9_locate(segments, address, size):
    found = [rom + address - start for start, rom, count in segments
             if start <= address and address + size <= start + count]
    _require(len(found) == 1,
             'address %#x+%d not in exactly one ARM9 segment' % (address, size))
    return found[0]


def _reconcile_ui_seed(before: bytes, after: bytes):
    """Keep the installed UI's y9 digest coherent after overlay 12 grows.

    Pristine V4 inputs have no UI seed and retain the historical isolated
    helper behaviour.  A composed UI must already carry a valid old digest;
    only word 17 (crc32(y9)) is then replaced with the new derived value.
    """
    segments = _arm9_map(before)
    at = _arm9_locate(segments, MODULE_SEED, 96)
    words = struct.unpack_from('<24I', before, at)
    if words[0] != MODULE_MAGIC:
        return after, None
    y9, y9_bytes = struct.unpack_from('<II', before, 0x50)
    _require(words[17] == zlib.crc32(before[y9:y9 + y9_bytes]),
             'input UI seed does not match y9')
    _require(before[at:at + 68] == after[at:at + 68]
             and before[at + 72:at + 96] == after[at + 72:at + 96],
             'Fairy AI changed UI seed words before reconciliation')
    digest = zlib.crc32(after[y9:y9 + y9_bytes])
    output = bytearray(after)
    struct.pack_into('<I', output, at + 68, digest)
    return bytes(output), {
        'address': MODULE_SEED + 68,
        'rom_offset': at + 68,
        'before_crc32': '%08x' % words[17],
        'after_crc32': '%08x' % digest,
    }


def apply_code(data: bytes, language: str, work_dir: Path, *, slot=None):
    """Install shared AI, type and battle-state fixes in one overlay rewrite."""
    from sgp12.overlay import applica
    from . import transform_reload, type_consumers
    _require(language in LANGUAGES, 'unsupported language')
    _require(slot is not None,
             'Fairy AI needs a reserve slot assigned by the integrator; none given')
    _check_slot(slot)
    data = bytes(data)
    payload, compiled = compile_native(Path(work_dir), slot['start'])
    type_payload, type_compiled = type_consumers.compile_native(Path(work_dir))
    reload_payload, reload_compiled = transform_reload.compile_native(Path(work_dir))
    at = _arm9_locate(_arm9_map(data), slot['start'], slot['bytes'])
    _require(data[at:at + slot['bytes']] == bytes(slot['bytes']),
             'assigned slot preimage is not the declared zero block')
    staged = bytearray(data)
    staged[at:at + PAYLOAD_BYTES] = payload
    old_image = Rom(data).immagine_overlay(OVERLAY_ID)[2]
    typed_image, type_logical = type_consumers.patch_overlay(old_image, type_payload)
    reload_image, reload_logical = transform_reload.patch_overlay(
        typed_image, reload_payload)
    expected, logical = patch_overlay(reload_image, slot['start'])
    edits = type_consumers.edits(type_payload) + transform_reload.edits(reload_payload) + [
        {'addr': FLAGS_SITE, 'pre': FLAGS_PREIMAGE,
         'post': seam_bytes(slot['start'])[FLAGS_SITE]},
        {'addr': SCALAR_SITE, 'pre': SCALAR_PREIMAGE,
         'post': seam_bytes(slot['start'])[SCALAR_SITE]},
        {'addr': LOOP_SITE, 'pre': LOOP_PREIMAGE, 'post': LOOP_REPLACEMENT},
    ]
    result, writer = applica(
        bytes(staged), OVERLAY_ID, list(CONTEXTS), edits)
    _require(Rom(result).immagine_overlay(OVERLAY_ID)[2] == expected,
             'overlay 12 readback differs from the Fairy calls/backedge')
    result, ui_seed = _reconcile_ui_seed(data, result)
    receipt = {
        'schema': 1, 'stage': 'fairy-ai-code', 'language': language,
        'input_sha256': _sha(data), 'output_sha256': _sha(result),
        'slot': dict(slot), 'payload_rom_offset': at,
        'native': compiled, 'logical': logical, 'overlay': writer,
        'type_consumers': {'native': type_compiled, 'logical': type_logical},
        'transform_reload': {'native': reload_compiled,
                             'logical': reload_logical},
        'ui_seed': ui_seed,
    }
    receipt['verification'] = verify_code(data, result, receipt)
    return result, receipt


def _payload_semantics(payload):
    payload = bytes(payload)
    _require(len(payload) == PAYLOAD_BYTES and _sha(payload) == PAYLOAD_SHA256,
             'installed Fairy AI payload identity')
    _require(payload.count(PACKED_CODES) == 1, 'packed Fairy table identity')
    targets = [bl_decode(DEFAULT_SLOT + offset,
                         payload[offset:offset + 4])
               for offset in APPLY_CALL_OFFSETS]
    # The payload bytes are position-independent: decoding them at DEFAULT_SLOT
    # must reach the one native flag combiner twice.
    _require(targets == [NATIVE_APPLY, NATIVE_APPLY],
             'native flag-combiner calls differ')
    return {'bytes': PAYLOAD_BYTES, 'fairy_pairs': 12,
            'native_apply_calls': 2, 'entries': [0, SCALAR_OFFSET]}


def _ranges(a, b):
    found = []
    for index, (old, new) in enumerate(zip(a, b)):
        if old != new:
            if found and found[-1][1] == index:
                found[-1][1] = index + 1
            else:
                found.append([index, index + 1])
    return found


def _crc16(data):
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            crc = (crc >> 1) ^ 0xA001 if crc & 1 else crc >> 1
    return crc


def _overlay_stream(rom, fat, y9):
    import ndspy.codeCompression as codec
    row = struct.unpack_from('<8I', rom, y9)
    start, end = struct.unpack_from('<II', rom, fat + 8 * row[6])
    _require(row[0] == OVERLAY_ID and row[7] >> 24 & 1,
             'overlay 12 row/compression')
    _require(end - start == row[7] & 0xFFFFFF,
             'overlay 12 FAT length differs from y9')
    stream = bytes(rom[start:end])
    try:
        image = Rom(rom).immagine_overlay(OVERLAY_ID)[2]
    except Rifiuto as error:
        raise ValueError('overlay 12 decode refused: ' + str(error)) from error
    _require(bytes(codec.decompress(stream)) == image,
             'independent BLZ decoders disagree')
    return row, start, end, image


def verify_code(before: bytes, after: bytes, receipt: dict) -> dict:
    """Account independently for every byte written by :func:`apply_code`."""
    from sgp12.blz import blz_comprimi_ottimo
    from . import transform_reload, type_consumers
    _require(type(receipt) is dict and receipt.get('schema') == 1,
             'receipt schema')
    _require(receipt.get('input_sha256') == _sha(before)
             and receipt.get('output_sha256') == _sha(after),
             'receipt must name the exact input and output ROM hashes')
    slot = receipt.get('slot')
    _check_slot(slot)
    _require(len(before) == len(after), 'Fairy AI stage must be in place')
    fat = struct.unpack_from('<I', before, 0x48)[0]
    y9_base = struct.unpack_from('<I', before, 0x50)[0]
    _require(struct.unpack_from('<II', after, 0x48)
             == struct.unpack_from('<II', before, 0x48)
             and struct.unpack_from('<II', after, 0x50)
             == struct.unpack_from('<II', before, 0x50),
             'FAT/y9 placement changed')
    y9 = y9_base + 32 * OVERLAY_ID
    old_row, start, old_end, old_image = _overlay_stream(before, fat, y9)
    new_row, new_start, new_end, new_image = _overlay_stream(after, fat, y9)
    _require(old_row[:7] == new_row[:7],
             'overlay 12 y9 row changed beyond compressed size')
    _require(old_row[7] >> 24 == new_row[7] >> 24,
             'overlay 12 compression flags changed')
    _require(new_start == start, 'overlay 12 moved')
    following = min([
        first for first, _ in (
            struct.unpack_from('<II', before, fat + 8 * index)
            for index in range(struct.unpack_from('<I', before, 0x4C)[0] // 8))
        if first > start] + [len(before)])
    _require(new_end <= following, 'overlay 12 stream exceeds its slot')
    _require(set(after[new_end:max(old_end, new_end)]) <= {0xFF},
             'overlay 12 slot tail is not 0xFF padding')
    _require(blz_comprimi_ottimo(new_image, bersaglio=old_end - start)
             == bytes(after[start:new_end]),
             'overlay 12 stream is not the canonical writer output')
    type_at = type_consumers.CONVERSION_SITE - OVERLAY_BASE
    type_payload = new_image[type_at:type_at + type_consumers.CONVERSION_BYTES]
    _require(_sha(type_payload) == type_consumers.PAYLOAD_SHA256,
             'installed Conversion2 helper identity')
    typed_image, type_logical = type_consumers.patch_overlay(old_image, type_payload)
    reload_at = transform_reload.RELOAD_ADDRESS - OVERLAY_BASE
    reload_payload = new_image[reload_at:reload_at + transform_reload.RELOAD_BYTES]
    _require(_sha(reload_payload) == transform_reload.PAYLOAD_SHA256,
             'installed Transform reload helper identity')
    reload_image, reload_logical = transform_reload.patch_overlay(
        typed_image, reload_payload)
    expected, fairy_logical = patch_overlay(reload_image, slot['start'])
    _require(new_image == expected,
             'decoded overlay differs from the declared type/Transform/Fairy edits')
    changed = [i for i, (old, new) in enumerate(zip(old_image, new_image))
               if old != new]
    expected_changed = sorted(set(type_logical['changed_offsets']) |
                              set(reload_logical['changed_offsets']) |
                              set(fairy_logical['changed_offsets']))
    _require(changed == expected_changed,
             'logical type/Transform/Fairy change set differs')

    _require(_arm9_map(before) == _arm9_map(after), 'ARM9 layout changed')
    at = _arm9_locate(_arm9_map(after), slot['start'], slot['bytes'])
    _require(before[at:at + slot['bytes']] == bytes(slot['bytes']),
             'slot preimage is not zero')
    payload = after[at:at + PAYLOAD_BYTES]
    semantics = _payload_semantics(payload)
    _require(receipt.get('payload_rom_offset') == at,
             'payload ROM offset receipt differs')
    native = receipt.get('native')
    _require(type(native) is dict
             and native.get('bytes') == PAYLOAD_BYTES
             and native.get('payload_sha256') == PAYLOAD_SHA256
             and native.get('semantics') == semantics,
             'native compilation receipt differs')
    type_receipt = receipt.get('type_consumers')
    _require(type(type_receipt) is dict
             and type(type_receipt.get('native')) is dict
             and type_receipt['native'].get('bytes') == type_consumers.CONVERSION_BYTES
             and type_receipt['native'].get('payload_sha256') == type_consumers.PAYLOAD_SHA256
             and type_receipt.get('logical') == type_logical,
             'type-consumer compilation/logical receipt differs')
    type_verified = type_consumers.verify_overlay(
        old_image, typed_image, type_payload, type_receipt['logical'])
    reload_receipt = receipt.get('transform_reload')
    _require(type(reload_receipt) is dict
             and type(reload_receipt.get('native')) is dict
             and reload_receipt['native'].get('bytes') == transform_reload.RELOAD_BYTES
             and reload_receipt['native'].get('payload_sha256')
             == transform_reload.PAYLOAD_SHA256
             and reload_receipt.get('logical') == reload_logical,
             'Transform reload compilation/logical receipt differs')
    reload_verified = transform_reload.verify_overlay(
        typed_image, reload_image, reload_payload, reload_receipt['logical'])

    seed_at = _arm9_locate(_arm9_map(before), MODULE_SEED, 96)
    old_seed = struct.unpack_from('<24I', before, seed_at)
    ui_seed = receipt.get('ui_seed')
    seed_zone = []
    if old_seed[0] == MODULE_MAGIC:
        _require(old_seed[17] == zlib.crc32(before[y9_base:y9_base + struct.unpack_from('<I', before, 0x54)[0]]),
                 'input UI seed does not match y9')
        expected_crc = zlib.crc32(after[y9_base:y9_base + struct.unpack_from('<I', after, 0x54)[0]])
        expected_seed = {
            'address': MODULE_SEED + 68, 'rom_offset': seed_at + 68,
            'before_crc32': '%08x' % old_seed[17],
            'after_crc32': '%08x' % expected_crc,
        }
        _require(ui_seed == expected_seed, 'UI y9 seed reconciliation receipt differs')
        _require(struct.unpack_from('<I', after, seed_at + 68)[0] == expected_crc,
                 'UI y9 seed was not reconciled')
        _require(before[seed_at:seed_at + 68] == after[seed_at:seed_at + 68]
                 and before[seed_at + 72:seed_at + 96] == after[seed_at + 72:seed_at + 96],
                 'UI seed changed outside y9 crc32 word')
        seed_zone = [(seed_at + 68, seed_at + 72)]
    else:
        _require(ui_seed is None and before[seed_at:seed_at + 96] == after[seed_at:seed_at + 96],
                 'non-UI input unexpectedly changed UI seed')

    zones = [
        (start, max(old_end, new_end)),
        (fat + 8 * old_row[6], fat + 8 * old_row[6] + 8),
        (y9 + 28, y9 + 32),
        (0x15E, 0x160),
        (at, at + PAYLOAD_BYTES),
    ] + seed_zone
    outside = [region for region in _ranges(before, after)
               if not any(lo <= region[0] and region[1] <= hi
                          for lo, hi in zones)]
    _require(not outside,
             'ROM bytes differ outside declared zones: %s' % outside[:8])
    _require(struct.unpack_from('<H', after, 0x15E)[0]
             == _crc16(after[:0x15E]), 'header CRC16')
    return {
        'logical_changed_bytes': len(changed),
        'payload_sha256': PAYLOAD_SHA256,
        'payload_semantics': semantics,
        'type_consumers': type_verified,
        'transform_reload': reload_verified,
        'arm9_changed_only_in_slot': True,
        'canonical_blz': True,
        'ui_y9_seed_reconciled': bool(seed_zone),
        'compressed_bytes': [old_end - start, new_end - start],
        'zones': [(hex(lo), hex(hi)) for lo, hi in zones],
    }
