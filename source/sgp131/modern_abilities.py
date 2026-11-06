"""Keen Eye (51) ignores every change to the target's evasion.

One seam in the battle accuracy check (overlay 12, BattleSystem_CheckMoveHit)
called the native ability getter and compared with Unaware (109) before
zeroing the target's evasion delta. The seam now calls a compiled predicate
that asks the same getter once and answers 1 for an effective Keen Eye or
Unaware; the compare becomes CMP #1 and the following branch is unchanged.
Gastro Acid and the getter's other suppressions therefore still apply, and
the accuracy-drop protection (stat-change command) is not touched.

The payload address is an owner slot that the integrator assigns in the
reserve map. Nothing here picks an address: `apply` refuses without a slot,
and the slot's current bytes must match the preimage the assignment states.
The overlay is always decoded from the input being patched, so changes made
by earlier stages elsewhere in overlay 12 are preserved, never reloaded.
"""
import hashlib
import importlib.util
import shutil
import struct
import subprocess
from sgp13.compiler import compiler_path, compiler_environment
import tempfile
from pathlib import Path

from sgp12.rom import Rom, bl_decode, bl_thumb, valida_layout_arm9

SOURCE = Path(__file__).resolve().parents[1]
FEATURE = SOURCE / 'features/modern-accuracy'
NATIVE = FEATURE / 'native.c'
ENTRY = 'sgp_ignore_target_evasion'

OV12_BASE = 0x022378C0
SITE = 0x0224BD5C                 # BL GetBattlerAbility(ctx, attacker)
COMPARE = SITE + 4                # CMP r0, #109 -> CMP r0, #1
GETTER = 0x022527CC               # GetBattlerAbility, Thumb, (ctx, battler)
CONTEXT_ADDRESS = 0x0224BD4C
CONTEXT = bytes.fromhex('6d2306f071fd012800d10027281c311c06f036fd6d2800d10024')
SEAM_BEFORE = bytes.fromhex('06f036fd6d28')
COMPARE_AFTER = bytes.fromhex('0128')
FUNCTION = (0x0224BCC4, 0x0224C018,
            'fa00e51e1f5fd0250d0de9aa7da2773da95040d575c9bb1cb6300420e4cef59e')
GETTER_FUNCTION = (GETTER, 0x02252834,
                   '07b2a41710a1dfe99de465ea1be3ea9f735993ea683e63c348692aaaa2191198')

PAYLOAD_BUDGET = 128
PAYLOAD_SHA256 = '9370a52456cd303a935e69a033224d00f8a18d03c6d70a4032839efa2ef43cdd'
COMPILER_VERSION = 'Apple clang version 21.0.0 (clang-2100.4.1.1)'
COMPILER_SHA256 = 'fc5e3cbba6ad54059295cad716aacb05ace8235f5f7a6031f1d8c15d24bd6d66'
FLAGS = ['--target=armv5te-none-eabi', '-mcpu=arm946e-s', '-mthumb', '-Oz',
         '-ffreestanding', '-fno-builtin', '-fno-stack-protector', '-fomit-frame-pointer',
         '-fno-unwind-tables', '-fno-asynchronous-unwind-tables', '-Wall', '-Wextra',
         '-Werror', '-fno-jump-tables', '-fstack-usage', '-std=c11']
FREE_SPACE_FLOOR = 10 * 1024 ** 3
LANGUAGES = ('EN', 'IT')


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


def _check_address(owned_address):
    _require(type(owned_address) is int, 'owned address must be an integer')
    _require(owned_address % 4 == 0, 'owned address must be 4-byte aligned (literal pool)')
    _require(0x02000000 <= owned_address < 0x02400000, 'owned address outside main RAM')
    delta = owned_address - (SITE + 4)
    _require(-0x400000 <= delta < 0x400000, 'owned address outside Thumb BL range of the seam')


def compile_native(work_dir: Path, owned_address: int) -> tuple[bytes, dict]:
    """Compile native.c for `owned_address`; return payload and receipt.

    The payload is position independent apart from the getter literal, so its
    bytes are pinned. Scratch lives under `work_dir` and is removed on return.
    """
    _check_address(owned_address)
    compiler = compiler_path(COMPILER_SHA256)
    _require(compiler is not None, 'clang unavailable')
    work_dir = Path(work_dir)
    _require(shutil.disk_usage(work_dir).free >= FREE_SPACE_FLOOR, 'free-space floor (10 GiB)')
    version = subprocess.run([compiler, '--version'], env=compiler_environment(), capture_output=True, text=True,
                             check=True).stdout.splitlines()[0]
    _require(version == COMPILER_VERSION, 'compiler version drift: ' + version)
    executable = _sha(Path(compiler).resolve().read_bytes())
    _require(executable == COMPILER_SHA256, 'compiler binary drift')
    source = NATIVE.read_bytes()
    defines = {'SGP_GET_BATTLER_ABILITY_ADDR': '0x%08X' % GETTER}
    loader = _module(SOURCE / 'features/options/tools/carica_text.py', 'modern_accuracy_loader')
    with tempfile.TemporaryDirectory(prefix='modern-accuracy-', dir=work_dir) as scratch:
        scratch = Path(scratch)
        obj = scratch / 'native.o'
        command = [compiler, *FLAGS, *['-D%s=%s' % item for item in defines.items()],
                   '-c', str(NATIVE), '-o', str(obj)]
        result = subprocess.run(command, cwd=scratch, env=compiler_environment(), capture_output=True, text=True, timeout=60)
        _require(result.returncode == 0 and not result.stderr, 'native compile failed: ' + result.stderr)
        raw = obj.read_bytes()
        usage = (scratch / 'native.su').read_text()
    payload, symbols = loader.load_text(raw, owned_address, (ENTRY,))
    _require(symbols[ENTRY] == owned_address | 1, 'predicate entry must be the first byte')
    _require(0 < len(payload) <= PAYLOAD_BUDGET, 'payload exceeds the 128-byte budget')
    _require(_sha(payload) == PAYLOAD_SHA256, 'payload drift: ' + _sha(payload))
    rows = [line.split('\t') for line in usage.splitlines() if line.strip()]
    _require(len(rows) == 1 and rows[0][0].endswith(':' + ENTRY) and rows[0][2] == 'static',
             'unexpected stack usage report')
    return payload, {'address': owned_address, 'entry': symbols[ENTRY], 'bytes': len(payload),
                     'budget': PAYLOAD_BUDGET, 'alignment': 4, 'payload_sha256': _sha(payload),
                     'object_sha256': _sha(raw), 'source_sha256': _sha(source),
                     'stack_bytes': int(rows[0][1]), 'getter': GETTER, 'defines': defines,
                     'compiler': {'version': version, 'executable_sha256': executable, 'flags': FLAGS}}


def seam_bytes(owned_address: int) -> bytes:
    _check_address(owned_address)
    return bl_thumb(SITE, owned_address | 1) + COMPARE_AFTER


def patch_overlay(image: bytes, owned_address: int) -> tuple[bytes, dict]:
    """Rewrite the six seam bytes of a decoded overlay 12 image, nothing else."""
    after = seam_bytes(owned_address)
    for start, end, digest in (FUNCTION, GETTER_FUNCTION):
        _require(0 <= start - OV12_BASE and end - OV12_BASE <= len(image), 'overlay 12 image truncated')
        part = image[start - OV12_BASE:end - OV12_BASE]
        if start == FUNCTION[0] and part[SITE - start:SITE - start + 6] == after:
            raise ValueError('Keen Eye seam already patched')
        _require(_sha(part) == digest, 'accuracy/getter preimage mismatch at %#x' % start)
    offset = CONTEXT_ADDRESS - OV12_BASE
    _require(image[offset:offset + len(CONTEXT)] == CONTEXT, 'seam context preimage mismatch')
    result = bytearray(image)
    result[SITE - OV12_BASE:SITE - OV12_BASE + 6] = after
    return bytes(result), {'site': SITE, 'before': SEAM_BEFORE.hex(), 'after': after.hex(),
                           'target': owned_address | 1, 'function_preimage_sha256': FUNCTION[2],
                           'getter_preimage_sha256': GETTER_FUNCTION[2]}


def _arm9_map(data):
    """RAM -> ROM offset map of the uncompressed ARM9 and its autoloads."""
    offset, _, base, length = struct.unpack_from('<4I', data, 0x20)
    table, table_end, body, _bss, _, packed = struct.unpack_from('<6I', data, offset + 0xBA0)
    _require(base == 0x02000000 and not packed and base < body <= table <= table_end <= base + length,
             'ARM9 initialized layout')
    _t0, _t1, _d0, _sections, segments = valida_layout_arm9(
        data, offset, base, length)
    return segments


def _arm9_locate(segments, address, size):
    found = [rom + address - start for start, rom, count in segments
             if start <= address and address + size <= start + count]
    _require(len(found) == 1, 'address %#x+%d not in exactly one ARM9 segment' % (address, size))
    return found[0]


def _text_module():
    return _module(FEATURE / 'text.py', 'modern_accuracy_text')


def _check_slot(slot):
    _require(type(slot) is dict and set(slot) == {'name', 'start', 'bytes', 'preimage_sha256'},
             'reserve slot assignment required: {name, start, bytes, preimage_sha256}')
    _require(type(slot['name']) is str and slot['name'], 'slot name')
    _check_address(slot['start'])
    _require(type(slot['bytes']) is int and 0 < slot['bytes'] <= 4096, 'slot size')


def apply_code(data: bytes, language: str, work_dir: Path, *, slot=None) -> tuple[bytes, dict]:
    """Install only the code: payload in the assigned slot and the overlay 12 seam.

    In place: no file is appended and the message archive is not touched, so the
    description can travel separately as a member delta (`text.patch_bank`).
    """
    from sgp12.overlay import applica
    _require(language in LANGUAGES, 'unsupported language')
    _require(slot is not None, 'Keen Eye needs a reserve slot assigned by the integrator; none given')
    _check_slot(slot)
    payload, compiled = compile_native(Path(work_dir), slot['start'])
    _require(len(payload) <= slot['bytes'], 'payload exceeds the assigned slot')
    segments = _arm9_map(data)
    at = _arm9_locate(segments, slot['start'], slot['bytes'])
    _require(_sha(data[at:at + slot['bytes']]) == slot['preimage_sha256'], 'assigned slot preimage mismatch')
    staged = bytearray(data)
    staged[at:at + len(payload)] = payload
    _, _, image = Rom(staged).immagine_overlay(12)
    patched, seam = patch_overlay(image, slot['start'])
    result, overlay_receipt = applica(bytes(staged), 12, [(CONTEXT_ADDRESS, CONTEXT)],
                                      [{'addr': SITE, 'pre': SEAM_BEFORE, 'post': seam_bytes(slot['start'])}])
    _require(Rom(result).immagine_overlay(12)[2] == patched, 'overlay readback differs from the seam patch')
    receipt = {'schema': 1, 'stage': 'keen-eye-code', 'language': language,
               'input_sha256': _sha(data), 'output_sha256': _sha(result),
               'slot': dict(slot), 'payload_rom_offset': at, 'native': compiled, 'seam': seam,
               'overlay': overlay_receipt, 'installed_hook_requires_assignment': True}
    receipt['verification'] = verify_code(data, result, receipt)
    return result, receipt


def apply(data: bytes, language: str, work_dir: Path, *, slot=None, charmap=None) -> tuple[bytes, dict]:
    """`apply_code`, then the EN/IT description appended by `text.apply`.

    Valid only where appending a rebuilt `a/0/2/7` is allowed (exact V4 inputs).
    After the UI stage, use `apply_code` and ship the description as a member
    delta of bank 722 instead.
    """
    _require(language in LANGUAGES, 'unsupported language')
    _require(slot is not None, 'Keen Eye needs a reserve slot assigned by the integrator; none given')
    _check_slot(slot)
    _require(charmap is not None, 'description charmap required')
    staged, code = apply_code(data, language, work_dir, slot=slot)
    result, text_receipt = _text_module().apply(staged, language, charmap)
    receipt = {'schema': 2, 'language': language, 'input_sha256': _sha(data), 'output_sha256': _sha(result),
               'slot': dict(slot), 'code': code, 'text': text_receipt}
    receipt['verification'] = verify(data, result, receipt, charmap=charmap)
    return result, receipt


def _payload_semantics(payload):
    from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB
    instructions = list(Cs(CS_ARCH_ARM, CS_MODE_THUMB).disasm(payload[:-4], 0))
    calls = [i for i in instructions if i.mnemonic in ('bl', 'blx')]
    immediates = {i.op_str.split('#')[-1] for i in instructions if '#' in i.op_str}
    _require(len(calls) == 1 and calls[0].mnemonic == 'blx', 'predicate must call the getter exactly once')
    _require(struct.unpack('<I', payload[-4:])[0] == GETTER | 1, 'getter literal')
    _require({'0x33', '0x6d'} <= immediates, 'predicate must test 51 and 109')
    return {'getter_calls': 1, 'abilities': [51, 109]}


def _ranges(a, b):
    found, step = [], 1 << 16
    for start in range(0, len(a), step):
        if a[start:start + step] == b[start:start + step]:
            continue
        for i in range(start, min(start + step, len(a))):
            if a[i] != b[i]:
                if found and found[-1][1] == i:
                    found[-1][1] = i + 1
                else:
                    found.append([i, i + 1])
    return found


def _crc16(data):
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            crc = (crc >> 1) ^ 0xA001 if crc & 1 else crc >> 1
    return crc


def _overlay_stream(rom, fat, y9):
    """Overlay 12 row, FAT span and decoded image, by two independent decoders."""
    import ndspy.codeCompression as codec
    row = struct.unpack_from('<8I', rom, y9)
    start, end = struct.unpack_from('<II', rom, fat + 8 * row[6])
    _require(row[7] >> 24 & 1, 'overlay 12 must stay a compressed stream')
    _require(end - start == row[7] & 0xFFFFFF, 'overlay 12 FAT length differs from the y9 compressed size')
    stream = bytes(rom[start:end])
    image = Rom(rom).immagine_overlay(12)[2]
    _require(bytes(codec.decompress(stream)) == image, 'the two BLZ decoders disagree on overlay 12')
    return row, start, end, image


def verify_code(before: bytes, after: bytes, receipt: dict) -> dict:
    """Independent readback of `apply_code`: every ROM byte is accounted for.

    Allowed differences: the overlay 12 stream inside its own FAT slot (which
    must be the writer's canonical BLZ encoding of the decoded image, not just
    an equivalent stream), its FAT entry and y9 size/flag word, the header CRC,
    and the payload bytes at the head of the assigned ARM9 slot.
    """
    from sgp12.blz import blz_comprimi_ottimo
    _require(type(receipt) is dict, 'receipt')
    _require(receipt.get('input_sha256') == _sha(before) and receipt.get('output_sha256') == _sha(after),
             'receipt must name the exact input and output ROM hashes')
    slot = receipt.get('slot')
    _check_slot(slot)
    _require(len(before) == len(after), 'code stage must be in place')
    fat, y9_base = struct.unpack_from('<I', before, 0x48)[0], struct.unpack_from('<I', before, 0x50)[0]
    _require(struct.unpack_from('<II', after, 0x48) == struct.unpack_from('<II', before, 0x48)
             and struct.unpack_from('<II', after, 0x50) == struct.unpack_from('<II', before, 0x50),
             'FAT/y9 table placement changed')
    y9 = y9_base + 32 * 12
    old_row, start, old_end, old_image = _overlay_stream(before, fat, y9)
    new_row, new_start, new_end, new_image = _overlay_stream(after, fat, y9)
    _require(old_row[:7] == new_row[:7] and old_row[0] == 12, 'overlay 12 y9 row changed beyond its size word')
    _require((old_row[7] >> 24) == (new_row[7] >> 24), 'overlay 12 y9 flag byte changed')
    _require(new_start == start, 'overlay 12 must stay in its FAT slot')
    following = min([first for first, _ in (struct.unpack_from('<II', before, fat + 8 * i)
                                            for i in range(struct.unpack_from('<I', before, 0x4C)[0] // 8))
                     if first > start] + [len(before)])
    _require(new_end <= following, 'overlay 12 stream exceeds its slot')
    tail = after[new_end:max(old_end, new_end)]
    _require(set(tail) <= {0xFF}, 'overlay 12 slot tail must be 0xFF padding')
    _require(blz_comprimi_ottimo(new_image, bersaglio=old_end - start) == bytes(after[start:new_end]),
             'overlay 12 BLZ stream is not the canonical writer output')
    _require(len(old_image) == len(new_image) == old_row[2], 'overlay 12 image size')
    site = SITE - OV12_BASE
    diff = [i for i in range(len(old_image)) if old_image[i] != new_image[i]]
    _require(diff and min(diff) >= site and max(diff) < site + 6, 'overlay 12 changed outside the seam')
    _require(old_image[site:site + 6] == SEAM_BEFORE, 'seam preimage')
    _require(bl_decode(SITE, new_image[site:site + 4]) == slot['start'], 'seam target is not the slot')
    _require(new_image[site + 4:site + 6] == COMPARE_AFTER, 'seam compare must be CMP r0, #1')
    _require(_arm9_map(before) == _arm9_map(after), 'ARM9 layout changed')
    at = _arm9_locate(_arm9_map(after), slot['start'], slot['bytes'])
    _require(_sha(before[at:at + slot['bytes']]) == slot['preimage_sha256'], 'slot preimage')
    payload_bytes = receipt.get('native', {}).get('bytes')
    _require(type(payload_bytes) is int and 0 < payload_bytes <= slot['bytes'], 'payload size')
    payload = after[at:at + payload_bytes]
    _require(_sha(payload) == PAYLOAD_SHA256, 'installed payload identity')
    semantics = _payload_semantics(payload)
    zones = [(start, max(old_end, new_end)), (fat + 8 * old_row[6], fat + 8 * old_row[6] + 8),
             (y9 + 28, y9 + 32), (0x15E, 0x160), (at, at + payload_bytes)]
    outside = [r for r in _ranges(before, after) if not any(a <= r[0] and r[1] <= b for a, b in zones)]
    _require(not outside, 'ROM bytes differ outside the declared zones: %s' % [(hex(a), hex(b)) for a, b in outside[:8]])
    _require(struct.unpack_from('<H', after, 0x15E)[0] == _crc16(after[:0x15E]), 'header CRC16')
    return {'overlay_changed_bytes': len(diff), 'seam_target': slot['start'] | 1,
            'arm9_changed_only_in_slot': True, 'payload_sha256': PAYLOAD_SHA256,
            'payload_semantics': semantics, 'canonical_blz': True,
            'compressed_bytes': [old_end - start, new_end - start], 'zones': [(hex(a), hex(b)) for a, b in zones]}


def verify(before: bytes, after: bytes, receipt: dict, *, charmap=None) -> dict:
    """Independent readback of `apply`: the code stage, then the description.

    The intermediate image is rebuilt from `after` by undoing only the append
    of `a/0/2/7` (its FAT entry and header length/capacity/CRC); it must hash to
    the code stage output named in the receipt, so neither reader trusts the
    other's bytes. With `charmap` row 51 is decoded to the expected text.
    """
    import ndspy.rom
    _require(type(receipt) is dict and receipt.get('schema') == 2, 'receipt schema')
    _require(receipt.get('input_sha256') == _sha(before) and receipt.get('output_sha256') == _sha(after),
             'receipt must name the exact input and output ROM hashes')
    code = receipt.get('code')
    _require(type(code) is dict and code.get('slot') == receipt.get('slot'), 'code receipt')
    _require(len(after) > len(before), 'description stage must append')
    fid = ndspy.rom.NintendoDSRom(before).filenames.idOf('a/0/2/7')
    entry = struct.unpack_from('<I', before, 0x48)[0] + 8 * fid
    middle = bytearray(after[:len(before)])
    for lo, hi in ((entry, entry + 8), (0x14, 0x15), (0x80, 0x84)):
        middle[lo:hi] = before[lo:hi]
    struct.pack_into('<H', middle, 0x15E, _crc16(middle[:0x15E]))
    middle = bytes(middle)
    _require(_sha(middle) == code.get('output_sha256'), 'after minus the description append is not the code output')
    checked = verify_code(before, middle, code)
    text = _text_module().verify(middle, after, receipt['text'], charmap_path=charmap)
    return dict(checked, text=text)
