#!/usr/bin/env python3
"""Prepare private, controlled pre-HpCalc arenas from an exact Plus ROM.

No CPU, compiler or natural-checkpoint claim. ROM code and NARC bytes stay in
the private output. This is preparation, not a prediction or execution result.
"""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import mmap
import struct


HERE = Path(__file__).resolve()
SOURCE = HERE.parents[3]
CTX, BS, OPP, CACHE = 0x02380000, 0x02370000, 0x02390000, 0x023A0000
ITEM_SHA = '276334b390f6072348f3de8c1971f60290bd350b60f57c19d0c7c6e6e09d908f'
MOVE_SHA = 'c64da77ab5f1158520a0f17905d457f3104c32aae1513c622cec0daa9f3e1588'
SHELL_SHA = '908a7f24f3f913a567fac9eb45d55b4493ab791c6f3e217345c883e8c4dc60d1'
HP_SCRIPT_SHA = 'bf7ad08c8f82d1b33126bf3b11cddcf34f4e7fbd49beb2fe45d90b9f65bafe70'
HEADER_SHA = '4842a1f377ddc623a50bf3001f4498864963881c236a3b4c3fad36fe1d04d2ff'


def need(ok, message):
    if not ok:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def seed_before_99():
    """Owned seed: first native LCG upper half is99, not observed input."""
    return (((99 << 16) - 24691) * pow(1103515245, -1, 1 << 32)) & 0xffffffff


def make_arenas(item_cache, move_cache, *, full_hp=False):
    """Build synthetic arenas; caller must authenticate resource content first.

    Widths describe storage, not every native load width. All unassigned bytes
    are explicitly zero. No HP, success flag, accumulator or command is changed
    after entry by this builder. Returned bytes contain no execution forecast.
    """
    need(type(full_hp) is bool, 'full_hp must be a bool')
    need(type(item_cache) is bytes and len(item_cache) == 516 * 36,
         '516 item records with two padding bytes each')
    need(type(move_cache) is bytes and len(move_cache) == 468 * 16,
         '468 move records')
    need(all(item_cache[i + 34:i + 36] == bytes(2)
             for i in range(0, len(item_cache), 36)), 'item padding must be zero')
    arenas = {'BS': (BS, bytearray(0x3000)),
              'CTX': (CTX, bytearray(0x4000)),
              'OPP': (OPP, bytearray(0x600)),
              'CACHE': (CACHE, bytearray(item_cache))}
    fields, occupied = [], set()

    def field(arena, offset, name, kind, value):
        formats = {'u8': '<B', 'u16': '<H', 'u32': '<I', 's32': '<i'}
        if kind == 'bytes':
            need(type(value) is bytes, 'byte field ' + name)
            data = value
        else:
            need(kind in formats and type(value) is int, 'integer field ' + name)
            data = struct.pack(formats[kind], value)
        base, image = arenas[arena]
        need(0 <= offset < len(image) and offset + len(data) <= len(image),
             'field bounds ' + name)
        region = set(range(base + offset, base + offset + len(data)))
        need(not region & occupied, 'overlapping initial fields ' + name)
        occupied.update(region)
        image[offset:offset + len(data)] = data
        fields.append(dict(arena=arena, offset=offset, ram=base + offset,
                           name=name, storage=kind, hex=data.hex()))

    field('CTX', 0x3DE, 'trainerAIData.moveData', 'bytes', move_cache)
    for offset, name, value in (
        (8, 'command', 28), (12, 'commandNext', 0),
        (0x30, 'attackerAfterMoveState', 0), (0x38, 'afterMoveMessageType', 0),
        (0x3C, 'afterMoveHitState', 0), (0x40, 'afterMoveEffectState', 0),
        (0x44, 'afterMoveEffectIndex', 0), (0x58, 'sendOutState', 0),
        (0x64, 'battlerIdAttacker', 0), (0x6C, 'battlerIdTarget', 1),
        (0x2120, 'trainerAIData.itemData', CACHE),
        (0x213C, 'battleStatus', 0), (0x2140, 'battleStatus2', 0),
        (0x2150, 'criticalMultiplier', 1),
        (0x2EC, 'selfTurnData[0].shellBellDamage', 0),
        (0x3040, 'moveNoTemp', 33), (0x3044, 'moveNoCur', 33),
        (0x3048, 'moveNoPrev', 0),
    ):
        field('CTX', offset, name, 'u32', value)
    field('CTX', 0x2144, 'damage', 's32', -100)
    field('CTX', 0x215C, 'hpCalc', 's32', 0)
    field('CTX', 0x21E8, 'executionOrder', 'bytes', bytes((0, 1, 2, 3)))
    field('CTX', 0x21EC, 'turnOrder', 'bytes', bytes((0, 1, 2, 3)))
    for b, species, ability, item, types in (
        (0, 1, 65, 253, (12, 3)), (1, 7, 67, 0, (11, 11)),
    ):
        at = 0x2D40 + 192 * b
        prefix = 'battleMons[' + str(b) + '].'
        field('CTX', at, prefix + 'species', 'u16', species)
        for i, stat in enumerate(('atk', 'def', 'speed', 'spAtk', 'spDef')):
            field('CTX', at + 2 + 2 * i, prefix + stat, 'u16', 100)
        field('CTX', at + 12, prefix + 'moves', 'bytes', struct.pack('<4H', 33, 0, 0, 0))
        field('CTX', at + 24, prefix + 'statChanges_s8[8]', 'bytes', bytes([6] * 8))
        field('CTX', at + 36, prefix + 'type1_type2', 'bytes', bytes(types))
        field('CTX', at + 39, prefix + 'ability', 'u8', ability)
        field('CTX', at + 44, prefix + 'movePPCur', 'bytes', bytes((35, 0, 0, 0)))
        field('CTX', at + 48, prefix + 'movePP', 'bytes', bytes((35, 0, 0, 0)))
        field('CTX', at + 52, prefix + 'level', 'u8', 50)
        field('CTX', at + 53, prefix + 'friendship', 'u8', 70)
        hp = 300 if b == 1 or full_hp else 150
        field('CTX', at + 76, prefix + 'hp', 's32', hp)
        field('CTX', at + 80, prefix + 'maxHp', 'u32', 300)
        field('CTX', at + 120, prefix + 'item', 'u16', item)
        field('CTX', 0x21A8 + 16 * b, 'playerActions[' + str(b) + '].command', 'u32', 23)
        field('CTX', 0x21F0 + 4 * b, 'effectiveSpeed[' + str(b) + ']', 'u32', 100)
        field('BS', 0x34 + 4 * b, 'opponentData[' + str(b) + ']', 'u32', OPP + 0x300 * b)
        field('OPP', 0x194 + 0x300 * b, 'opponent[' + str(b) + '].battlerId', 'u8', b)
        field('OPP', 0x195 + 0x300 * b, 'opponent[' + str(b) + '].battlerType', 'u8', b)
    field('BS', 0x2C, 'battleType_single', 'u32', 0)
    field('BS', 0x44, 'maxBattlers', 'u32', 2)
    field('BS', 0x2448, 'rngSeed', 'u32', seed_before_99())
    return dict(schema='sgp-ordinary-shellbell-arenas-v1',
                origin='owned controlled pre-HpCalc input; not a natural RAM capture',
                full_hp=full_hp, default_unassigned_byte=0, fields=fields,
                arenas=[dict(name=name, ram=base, bytes=len(image),
                             sha256=sha(image), hex=image.hex())
                        for name, (base, image) in arenas.items()],
                CPU_executed=False, compiler_invoked=False,
                forecast_produced=False)


def prepare(rom, language, reference):
    need(language in ('EN', 'IT'), 'explicit language')
    source_pins = {'include/battle/battle.h': HEADER_SHA,
                   'src/battle/battle_controller_player.c':
                   'f7af28b3c492876a56c8a9621c463de71e27d2f04665253bd5abd77b63a7888b'}
    for name, digest in source_pins.items():
        need(sha((Path(reference) / name).read_bytes()) == digest,
             'exact source file identity ' + name)
    reader = load(SOURCE / 'features/fairy-ai/tools/attribuisci.py', 'ordinary_input_image')
    narc = load(SOURCE / 'features/borsa/tools/attribuisci.py', 'ordinary_input_narc')
    model = reader.read_current(rom, language)
    with Path(rom).open('rb') as stream, mmap.mmap(stream.fileno(), 0, access=mmap.ACCESS_READ) as raw:
        need(len(raw) == model['record']['bytes'] and sha(raw) == model['record']['sha256'],
             'ROM identity unchanged between code and resource reads')
        items, ir = narc.raw_archive(raw, 'a/0/1/7')
        moves, mr = narc.raw_archive(raw, 'a/0/1/1')
        scripts, sr = narc.raw_archive(raw, 'a/0/0/1')
    need(ir['file_id'] == 146 and len(items) == 516 and all(len(x) == 34 for x in items), 'item geometry')
    need(mr['file_id'] == 140 and len(moves) == 471 and all(len(x) == 16 for x in moves), 'move geometry')
    need(sr['file_id'] == 130 and len(scripts) == 297, 'script geometry')
    item_cache = b''.join(x + bytes(2) for x in items)
    move_cache = b''.join(moves[:468])
    need(sha(item_cache) == ITEM_SHA and sha(move_cache) == MOVE_SHA, 'exact cache identities')
    need(sha(items[231]) == SHELL_SHA and items[231][2:4] == bytes((88, 8)), 'Conchinella resource')
    need(sha(scripts[2]) == HP_SCRIPT_SHA and len(scripts[2]) == 152, 'HP script identity')
    def piece(address, size):
        matches = [data[address-base:address-base+size] for base, data in model['segments']
                   if base <= address and address + size <= base + len(data)]
        need(len(matches) == 1, 'unique ARM9 segment'); return matches[0]
    mapping = {}
    for item, member in ((0, 0), (253, 231)):
        row = piece(0x02100194 + item * 8, 8)
        need(struct.unpack('<4H', row)[0] == member, 'item to member mapping')
        mapping[str(item)] = dict(member=member, row_hex=row.hex(), sha256=sha(items[member]))
    ro = [dict(ram=base, bytes=len(data), sha256=sha(data), hex=data.hex())
          for base, data in model['segments'] if data]
    ro.append(dict(ram=int(model['record']['overlays'][1]['ram'], 16),
                   bytes=len(model['overlay']), sha256=sha(model['overlay']), hex=model['overlay'].hex()))
    arenas = make_arenas(item_cache, move_cache)
    spans = [(x['ram'], x['ram'] + x['bytes']) for x in ro + arenas['arenas']]
    for i, (low, high) in enumerate(spans):
        need(all(high <= a or b <= low for a, b in spans[:i]), 'nonoverlapping input maps')
    return dict(schema='sgp-ordinary-shellbell-input-preparation-v1', ROM=model['record'],
                read_only_images=ro, controlled_input=arenas,
                resources=dict(items=ir, moves=mr, scripts=sr, selected_item_mapping=mapping,
                               selected_scripts={str(i): dict(member=i, bytes=len(scripts[i]),
                                    sha256=sha(scripts[i]), hex=scripts[i].hex()) for i in (2, 16, 293)}),
                tool_sha256=sha(HERE.read_bytes()),
                reader_sha256={str(Path(m.__file__).relative_to(SOURCE)): sha(Path(m.__file__).read_bytes())
                               for m in (reader, narc)},
                source_file_sha256=source_pins,
                source_provenance='Content pins from productive cb614ad23449d5852b40321dc409c4143872b35c; Git state not checked by this preparer',
                limits=['Controlled arenas only; no entry-register/stack kernel or source forecast yet',
                        'Exact image/resources authenticated; data presence does not admit their execution',
                        'Native item-cache loader, NARC loader and UI transport are not executed',
                        'No healing, loss of healing, natural battle, SAVE or hardware result'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom', type=Path, required=True)
    parser.add_argument('--language', choices=('EN', 'IT'), required=True)
    parser.add_argument('--reference', type=Path, required=True)
    parser.add_argument('--json', type=Path, required=True)
    args = parser.parse_args()
    output = load(HERE.with_name('rileggi_shellbell_ordinary.py'), 'ordinary_input_output')
    try:
        path = output.private_output(args.json)
        need(path != args.rom.resolve(), 'output must not replace ROM')
        output.save_new(path, prepare(args.rom, args.language, args.reference))
    except (ValueError, OSError) as error:
        parser.exit(1, str(error) + '\n')
    print('Private controlled pre-HpCalc arenas saved; no forecast or guest execution.')


if __name__ == '__main__':
    main()
