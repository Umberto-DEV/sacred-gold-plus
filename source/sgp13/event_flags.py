"""Guarded native high-event-flag storage; no game bytes are public assets."""
import hashlib
import json
from pathlib import Path
import struct
import subprocess
from sgp13.compiler import compiler_path, compiler_environment, run_compiler
from .training import module, entry_hook

ROOT = Path(__file__).resolve().parents[1]
BASE, SIZE = 0x023CF900, 0x600
TRAMPOLINE, VAR_GET_TRAMPOLINE = 0x023CFE80, 0x023CFE94
SET_VAR_TRAMPOLINE, CONFIG = 0x023CFEA8, 0x023CFEF0
GETTER, LOAD = 0x0205045C, 0x02027AD4
VAR_GET, SET_VAR = 0x020403AC, 0x02040F14
GET_VAR_POINTER, SCRIPT_READ_HALFWORD = 0x02040374, 0x0203FE2C
FAMILY_FLAGS = (0x3F03, 0x3F06, 0x3F07, 0x3F09, 0x3F0A, 0x3F0B,
                0x3F0C, 0x3F0D, 0x3F0E, 0x3F0F, 0x3F10, 0x3F11,
                0x3F12, 0x3F13, 0x3F14, 0x3F15, 0x3F16, 0x3F17,
                0x3F1D, 0x3F1E, 0x3F1F, 0x3F26, 0x3F27, 0x3F28)
FAMILY_IDS = frozenset(range(0x612E, 0x613A)) | frozenset(range(0x619E, 0x61AA))
FAMILY_CENSUS_SHA256 = '9996ef7f1b017639893d0d50025684f652a137a1bbc7390f43ec415269aafe0c'
HF01_NORMALIZED_SHA256 = '310ad9d53fcfb636c3220cf2157682f4cdd50bc1753746b70bce1f5190348e84'
HF01_GETTER, HF01_LOAD = 0x023CF934, 0x023CF9C4


def sha(data):
    return hashlib.sha256(data).hexdigest()


def compile_native(directory):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    obj = directory / 'event-flags.o'
    flags = ['--target=armv5te-none-eabi', '-mcpu=arm946e-s', '-mthumb', '-Oz',
             '-ffreestanding', '-fno-builtin', '-fno-stack-protector', '-fno-jump-tables',
             '-fno-unwind-tables', '-fno-asynchronous-unwind-tables', '-Wall', '-Wextra', '-Werror']
    run_compiler([ *flags, '-c', str(ROOT / 'features/event-flags/runtime.c'),
                    '-o', str(obj)], check=True, capture_output=True)
    loader = module(ROOT / 'features/options/tools/carica_text.py', 'event_flags_loader')
    blob, symbols = loader.load_text(obj.read_bytes(), BASE,
                                    ('sgp_event_flags_get', 'sgp_event_flags_load', 'sgp_event_flags_valid',
                                     'sgp_event_vars_get', 'sgp_event_vars_set',
                                     'sgp_field_var_get', 'sgp_script_set_var'))
    if len(blob) > TRAMPOLINE - BASE:
        raise ValueError('event flags code overflow')
    return blob, symbols


def guard_reservation_archives(data):
    """Reject new literal uses of the allocated variables, at any alignment.

    Native indirect ranges were audited separately; these archive guards cover
    field scripts, map events and Frontier scripts, including unknown opcodes.
    """
    import ndspy.rom
    import ndspy.narc
    rom = ndspy.rom.NintendoDSRom(bytes(data))
    rows = []
    for name in ('a/0/1/2', 'a/0/3/2', 'a/1/8/2'):
        arc = ndspy.narc.NARC(rom.getFileByName(name))
        guard_archive_members(name, arc.files)
        for index, member in enumerate(arc.files):
            for offset in range(len(member) - 1):
                value = member[offset] | member[offset + 1] << 8
                if value in FAMILY_IDS:
                    rows.append((name, index, offset, value))
    encoded = json.dumps(rows, separators=(',', ':')).encode()
    if len(rows) != 48 or sha(encoded) != FAMILY_CENSUS_SHA256:
        raise ValueError('event variable family census changed')


def guard_archive_members(name, members):
    for index, member in enumerate(members):
        for offset in range(len(member) - 1):
            value = member[offset] | member[offset + 1] << 8
            if 0x415E <= value <= 0x416F:
                raise ValueError(f'event flags variable reservation: {name}:{index}+{offset:#x}')
            if value in FAMILY_FLAGS:
                raise ValueError(f'event flags family bit owner: {name}:{index}+{offset:#x}')


def guard_native(arm, language):
    from sgp12.rom import Rom
    guards = json.loads((ROOT / 'features/event-flags/native-guards.json').read_text())[language]
    for address, pin in guards['arm9'].items():
        if sha(arm.leggi(int(address, 16), pin['bytes'])) != pin['sha256']:
            raise ValueError('event flags native ABI ' + address)
    if sha(Rom(arm.raw).immagine_overlay(36)[2]) != guards['continue_overlay36_sha256']:
        raise ValueError('event flags Continue caller ABI')


def relocated_trampolines(arm):
    """Relocate complete Thumb functions whose displaced spans contain BLs."""
    from sgp12.rom import bl_thumb, bl_decode
    var_get = bytearray(arm.leggi(VAR_GET, 18))
    set_var = bytearray(arm.leggi(SET_VAR, 34))
    if bl_decode(VAR_GET + 4, var_get[4:8]) != GET_VAR_POINTER:
        raise ValueError('event variable getter call ABI')
    expected = ((4, SCRIPT_READ_HALFWORD), (16, GET_VAR_POINTER),
                (24, SCRIPT_READ_HALFWORD))
    for offset, target in expected:
        if bl_decode(SET_VAR + offset, set_var[offset:offset + 4]) != target:
            raise ValueError('event SetVar call ABI')
    var_get[4:8] = bl_thumb(VAR_GET_TRAMPOLINE + 4, GET_VAR_POINTER)
    for offset, target in expected:
        set_var[offset:offset + 4] = bl_thumb(SET_VAR_TRAMPOLINE + offset, target)
    return bytes(var_get), bytes(set_var)


def normalize_hf01(arm, language):
    """Authenticate and remove the installed HF01 layer in a private RAM view."""
    from sgp12.rom import bl_decode, bl_thumb
    import copy
    payload = bytearray(arm.leggi(BASE, SIZE))
    struct.pack_into('<I', payload, CONFIG - BASE, 0)
    if sha(payload) != HF01_NORMALIZED_SHA256:
        raise ValueError('unexpected installed HF01 payload')
    if bl_decode(GETTER + 2, arm.leggi(GETTER + 2, 4)) != HF01_GETTER:
        raise ValueError('unexpected installed HF01 getter')
    if bl_decode(LOAD + 2, arm.leggi(LOAD + 2, 4)) != HF01_LOAD:
        raise ValueError('unexpected installed HF01 loader')
    delegated = arm.u32(CONFIG)
    if not (0x023D0100 <= delegated < 0x023D2F00
            or 0x023D6800 <= delegated < 0x023D6E00):
        raise ValueError('unexpected installed HF01 delegate')
    result = copy.copy(arm)
    result.raw = bytearray(arm.raw)
    result.scrivi(GETTER, arm.leggi(TRAMPOLINE, 8))
    result.scrivi(LOAD, b'\x10\xb5' + bl_thumb(LOAD + 2, delegated & ~1) + b'\x10\xbd')
    result.scrivi(BASE, bytes(SIZE))
    guard_native(result, language)
    return result, delegated


def prepare_upgrade(arm, directory, language, successor_load):
    """Derive the complete HF02 write set from an exact installed HF01 image."""
    if not (0x023D0100 <= successor_load < 0x023D2F00
            or 0x023D6800 <= successor_load < 0x023D6E00):
        raise ValueError('event flags successor loader address')
    guard_reservation_archives(arm.raw)
    normalized, predecessor = normalize_hf01(arm, language)
    writes, receipt = prepare(normalized, directory, language, predecessor)
    payload = bytearray(writes[BASE])
    struct.pack_into('<I', payload, CONFIG - BASE, successor_load)
    writes[BASE] = bytes(payload)
    receipt.update({'training_load': successor_load, 'predecessor_load': predecessor,
                    'payload_sha256': sha(payload), 'upgrade': 'HF01-to-HF02'})
    return writes, receipt


def prepare(arm, directory, language='EN', training_load=None):
    """Return disjoint in-place writes without writing a cartridge.

    Caller supplies the already-compiled Training entry to enforce composition;
    private native tests may discover it from the guarded entry hook.
    """
    from sgp12.rom import bl_decode
    guard_native(arm, language)
    if arm.leggi(BASE, SIZE) != bytes(SIZE):
        raise ValueError('event flags compartment occupied')
    old = arm.leggi(LOAD, 8)
    if old[:2] != b'\x10\xb5' or old[6:] != b'\x10\xbd':
        raise ValueError('event flags composed load hook')
    delegated = bl_decode(LOAD + 2, old[2:6]) | 1
    if not (0x023D0100 <= delegated < 0x023D2F00
            or 0x023D6800 <= delegated < 0x023D6E00):
        raise ValueError('event flags delegated Training address')
    if training_load is not None and delegated != training_load:
        raise ValueError('event flags Training composition mismatch')
    blob, symbols = compile_native(directory)
    payload = bytearray(SIZE)
    payload[:len(blob)] = blob
    # The original first 12 bytes have only one internal relative branch:
    # flag zero returns, otherwise branch to byte 12. Resume original byte 12
    # with the original stack/register state. No external BL is displaced.
    prefix = arm.leggi(GETTER, 12)
    trampoline = prefix + b'\x00\x4b\x18\x47' + struct.pack('<I', GETTER + 13)
    payload[TRAMPOLINE - BASE:TRAMPOLINE - BASE + len(trampoline)] = trampoline
    var_get_trampoline, set_var_trampoline = relocated_trampolines(arm)
    payload[VAR_GET_TRAMPOLINE - BASE:VAR_GET_TRAMPOLINE - BASE + len(var_get_trampoline)] = var_get_trampoline
    payload[SET_VAR_TRAMPOLINE - BASE:SET_VAR_TRAMPOLINE - BASE + len(set_var_trampoline)] = set_var_trampoline
    struct.pack_into('<I', payload, CONFIG - BASE, delegated)
    writes = {BASE: bytes(payload), GETTER: entry_hook(GETTER, symbols['sgp_event_flags_get']),
              LOAD: entry_hook(LOAD, symbols['sgp_event_flags_load']),
              VAR_GET: entry_hook(VAR_GET, symbols['sgp_field_var_get']),
              SET_VAR: entry_hook(SET_VAR, symbols['sgp_script_set_var'])}
    return writes, {'code_bytes': len(blob), 'compartment_bytes': SIZE,
                    'symbols': symbols, 'training_load': delegated,
                    'payload_sha256': sha(payload), 'language': language}


def verify(arm, receipt, directory):
    """Recompile and independently validate hooks, trampoline and payload."""
    from sgp12.rom import bl_decode
    blob, symbols = compile_native(directory)
    expected = bytearray(SIZE)
    expected[:len(blob)] = blob
    # Recover the private displaced prologue from the installed trampoline.
    # The normalized full native range hash below authenticates every byte.
    prefix = arm.leggi(TRAMPOLINE, 12)
    expected[TRAMPOLINE - BASE:TRAMPOLINE - BASE + 20] = (
        prefix + b'\x00\x4b\x18\x47' + struct.pack('<I', 0x02050469))
    var_get_trampoline = arm.leggi(VAR_GET_TRAMPOLINE, 18)
    set_var_trampoline = arm.leggi(SET_VAR_TRAMPOLINE, 34)
    expected[VAR_GET_TRAMPOLINE - BASE:VAR_GET_TRAMPOLINE - BASE + 18] = var_get_trampoline
    expected[SET_VAR_TRAMPOLINE - BASE:SET_VAR_TRAMPOLINE - BASE + 34] = set_var_trampoline
    struct.pack_into('<I', expected, CONFIG - BASE, receipt['training_load'])
    if arm.leggi(BASE, SIZE) != expected:
        raise ValueError('event flags payload readback')
    for site, name in ((GETTER, 'sgp_event_flags_get'), (LOAD, 'sgp_event_flags_load'),
                       (VAR_GET, 'sgp_field_var_get'), (SET_VAR, 'sgp_script_set_var')):
        hook = arm.leggi(site, 8)
        if (hook[:2] != b'\x10\xb5' or hook[6:] != b'\x10\xbd'
                or bl_decode(site + 2, hook[2:6]) != symbols[name] & ~1):
            raise ValueError('event flags hook readback')
    # Restore only independently checked hooks in a memory view for source ABI
    # validation; no changes to the user's input or output paths.
    import copy
    original = copy.copy(arm)
    original.raw = bytearray(arm.raw)
    original.scrivi(GETTER, prefix[:8])
    from sgp12.rom import bl_thumb
    restored_var_get = bytearray(var_get_trampoline)
    restored_var_get[4:8] = bl_thumb(VAR_GET + 4, GET_VAR_POINTER)
    restored_set_var = bytearray(set_var_trampoline)
    for offset, target in ((4, SCRIPT_READ_HALFWORD), (16, GET_VAR_POINTER),
                           (24, SCRIPT_READ_HALFWORD)):
        restored_set_var[offset:offset + 4] = bl_thumb(SET_VAR + offset, target)
    original.scrivi(VAR_GET, restored_var_get[:8])
    original.scrivi(SET_VAR, restored_set_var[:8])
    guard_native(original, receipt['language'])
    if prefix != original.leggi(GETTER, 12):
        raise ValueError('event flags trampoline prologue')
    if bytes(restored_var_get) != original.leggi(VAR_GET, 18):
        raise ValueError('event variable getter trampoline')
    if bytes(restored_set_var) != original.leggi(SET_VAR, 34):
        raise ValueError('event SetVar trampoline')
    return {'verified': True, 'code_bytes': len(blob), 'native_abi_preserved': True}


def install(arm, language, training_load, directory):
    """Install on an existing ARM9 view; preserves all non-owned ROM bytes."""
    guard_reservation_archives(arm.raw)
    writes, receipt = prepare(arm, directory, language, training_load)
    before = bytes(arm.raw)
    for address, payload in writes.items():
        arm.scrivi(address, payload)
    verify(arm, receipt, Path(directory) / 'readback')
    restored = bytearray(arm.raw)
    for address, payload in writes.items():
        offset = arm.off(address, len(payload))
        restored[offset:offset + len(payload)] = before[offset:offset + len(payload)]
    if bytes(restored) != before:
        raise ValueError('event flags unowned cartridge bytes changed')
    receipt['cartridge_byte_preservation'] = True
    return receipt
