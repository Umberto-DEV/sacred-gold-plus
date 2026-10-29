"""Guarded, Plus-only trainer move improvements; no permanent TRPOKE edits."""
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import subprocess

import ndspy.narc
import ndspy.rom

from sgp12.rom import Arm9, bl_decode, bl_thumb

BASE, CODE_SIZE, SIZE = 0x023D6000, 0x600, 0x800
ORIGINAL_HOOK = 0x023D8194
HOOK_BYTES = bytes.fromhex('52880eb5101c62192832d178127809020a432199fff7c4ff0ebc021c301c00bd')
SITES = (0x02073718, 0x02073802, 0x0207390C, 0x02073A0C)
SOURCE = Path(__file__).resolve().parents[1]


def fnv(data):
    value = 2166136261
    for byte in data:
        value = ((value ^ byte) * 16777619) & 0xffffffff
    return value


def configuration(data):
    rom = ndspy.rom.NintendoDSRom(data)
    parties = ndspy.narc.NARC(rom.getFileByName('a/0/5/6')).files
    trainers = ndspy.narc.NARC(rom.getFileByName('a/0/5/5')).files
    spec = json.loads(Path(__file__).with_name('data').joinpath('strategic-teams.json').read_text())
    records, moves = bytearray(), bytearray()
    for team in spec['teams']:
        index = team['trainer_id']
        before = parties[index]
        if (len(before) != team['bytes'] or hashlib.sha256(before).hexdigest() != team['source_sha256'] or
            trainers[index][0] != team['type'] or trainers[index][3] != team['count']):
            raise ValueError(f'strategic team source preimage {index}')
        after = bytearray(before)
        first = len(moves) // 8
        for move in team['moves']:
            offset = move['offset']
            if (offset & 1 or not 0 <= offset <= len(after) - 2 or
                not 8 <= offset % 18 <= 14 or
                struct.unpack_from('<H', after, offset)[0] != move['before']):
                raise ValueError(f'strategic move preimage {index}:{offset}')
            struct.pack_into('<H', after, offset, move['after'])
            moves += struct.pack('<4H', offset, move['before'], move['after'], 0)
        records += struct.pack('<HHIIBBBB', index, first, fnv(before), fnv(after),
                               team['type'], team['count'], len(before), len(team['moves']))
    result = struct.pack('<IHH', 0x31544753, len(records) // 16, len(moves) // 8) + records + moves
    if len(result) > SIZE - CODE_SIZE:
        raise ValueError('strategic team configuration overflow')
    return bytes(result)


def compile_native(work_dir):
    output = Path(work_dir)
    output.mkdir(parents=True, exist_ok=True)
    obj = output / 'teams.o'
    subprocess.run(['clang', '--target=armv5te-none-eabi', '-mcpu=arm946e-s', '-mthumb', '-Os',
                    '-ffreestanding', '-fno-builtin', '-fno-stack-protector', '-fno-jump-tables',
                    '-fno-unwind-tables', '-fno-asynchronous-unwind-tables', '-Wall', '-Wextra',
                    '-Werror', '-c', str(SOURCE / 'features/trainer-strategy/native.c'),
                    '-o', str(obj)], check=True, capture_output=True)
    spec = importlib.util.spec_from_file_location('strategy_loader', SOURCE / 'features/options/tools/carica_text.py')
    loader = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loader)
    blob, symbols = loader.load_text(obj.read_bytes(), BASE, ('strategy_hook', 'strategy_apply'))
    if len(blob) > CODE_SIZE:
        raise ValueError('strategic trainer code exceeds its allocation')
    return blob, symbols


def install(input_path, output_path, work_dir):
    arm = Arm9(input_path)
    config = configuration(bytes(arm.raw))
    if arm.leggi(BASE, SIZE) != bytes(SIZE):
        raise ValueError('strategic trainer allocation already occupied')
    if arm.leggi(ORIGINAL_HOOK, len(HOOK_BYTES)) != HOOK_BYTES:
        raise ValueError('original Plus trainer hook preimage')
    for address in SITES:
        if bl_decode(address, arm.leggi(address, 4)) != ORIGINAL_HOOK:
            raise ValueError('original Plus trainer call-site preimage')
    blob, symbols = compile_native(work_dir)
    payload = blob + bytes(CODE_SIZE - len(blob)) + config
    payload += bytes(SIZE - len(payload))
    arm.scrivi(BASE, payload)
    for address in SITES:
        arm.scrivi(address, bl_thumb(address, symbols['strategy_hook'] & ~1))
    Path(output_path).write_bytes(arm.raw)
    check = Arm9(output_path)
    if check.leggi(BASE, SIZE) != payload:
        raise ValueError('strategic trainer payload readback')
    for address in SITES:
        if bl_decode(address, check.leggi(address, 4)) != symbols['strategy_hook'] & ~1:
            raise ValueError('strategic trainer hook readback')
    return {'code_bytes': len(blob), 'config_bytes': len(config), 'teams': 7, 'moves': 9,
            'symbols': symbols, 'mode': 'Plus only', 'trpoke_archive_unchanged': True}
