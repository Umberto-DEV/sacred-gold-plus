"""Guarded native high-event-flag storage; no game bytes are public assets."""
import hashlib
import json
from pathlib import Path
import struct
import subprocess
from .training import module, entry_hook

ROOT = Path(__file__).resolve().parents[1]
BASE, SIZE = 0x023CF900, 0x600
TRAMPOLINE, CONFIG = 0x023CFE80, 0x023CFEF0
GETTER, LOAD = 0x0205045C, 0x02027AD4


def sha(data):
    return hashlib.sha256(data).hexdigest()


def compile_native(directory):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    obj = directory / 'event-flags.o'
    flags = ['--target=armv5te-none-eabi', '-mcpu=arm946e-s', '-mthumb', '-Oz',
             '-ffreestanding', '-fno-builtin', '-fno-stack-protector', '-fno-jump-tables',
             '-fno-unwind-tables', '-fno-asynchronous-unwind-tables', '-Wall', '-Wextra', '-Werror']
    subprocess.run(['clang', *flags, '-c', str(ROOT / 'features/event-flags/runtime.c'),
                    '-o', str(obj)], check=True, capture_output=True)
    loader = module(ROOT / 'features/options/tools/carica_text.py', 'event_flags_loader')
    blob, symbols = loader.load_text(obj.read_bytes(), BASE,
                                    ('sgp_event_flags_get', 'sgp_event_flags_load', 'sgp_event_flags_valid'))
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
    for name in ('a/0/1/2', 'a/0/3/2', 'a/1/8/2'):
        arc = ndspy.narc.NARC(rom.getFileByName(name))
        guard_archive_members(name, arc.files)


def guard_archive_members(name, members):
    for index, member in enumerate(members):
        for offset in range(len(member) - 1):
            value = member[offset] | member[offset + 1] << 8
            if 0x415E <= value <= 0x416F:
                raise ValueError(f'event flags variable reservation: {name}:{index}+{offset:#x}')


def guard_native(arm, language):
    from sgp12.rom import Rom
    guards = json.loads((ROOT / 'features/event-flags/native-guards.json').read_text())[language]
    for address, pin in guards['arm9'].items():
        if sha(arm.leggi(int(address, 16), pin['bytes'])) != pin['sha256']:
            raise ValueError('event flags native ABI ' + address)
    if sha(Rom(arm.raw).immagine_overlay(36)[2]) != guards['continue_overlay36_sha256']:
        raise ValueError('event flags Continue caller ABI')


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
    if not 0x023D0100 <= delegated < 0x023D2F00:
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
    struct.pack_into('<I', payload, CONFIG - BASE, delegated)
    writes = {BASE: bytes(payload), GETTER: entry_hook(GETTER, symbols['sgp_event_flags_get']),
              LOAD: entry_hook(LOAD, symbols['sgp_event_flags_load'])}
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
    struct.pack_into('<I', expected, CONFIG - BASE, receipt['training_load'])
    if arm.leggi(BASE, SIZE) != expected:
        raise ValueError('event flags payload readback')
    for site, name in ((GETTER, 'sgp_event_flags_get'), (LOAD, 'sgp_event_flags_load')):
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
    guard_native(original, receipt['language'])
    if prefix != original.leggi(GETTER, 12):
        raise ValueError('event flags trampoline prologue')
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
