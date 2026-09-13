#!/usr/bin/env python3
"""Read one TEST party member from a 4 MiB dump; never modify it.

Layout and checksum/cipher verified against pret/pokeheartgold at
0985e8718df4f25e64d6507d89c0c97c0d288981: pokemon_types_def.h,
pokemon.c:GetSubstruct and math_util.c:MonEncryptionLCRNG.
The save-root-relative offset is additionally checked against live TEST data.
The default requires the original one-member fixture. Native-pilot tests may
explicitly select a slot and expected count; this remains a Chikorita TEST
reader, not a general editor.
"""
import argparse
import itertools
import json
from pathlib import Path
import struct


def crypt(data, seed):
    words = []
    for word, in struct.iter_unpack('<H', data):
        seed = (seed * 1103515245 + 24691) & 0xFFFFFFFF
        words.append(word ^ (seed >> 16))
    return struct.pack('<' + 'H' * len(words), *words)


def inspect(ram, expected_level=5, *, expected_count=1, slot=0):
    if len(ram) != 0x400000:
        raise ValueError('Expected exactly 4 MiB of main RAM')
    if (type(expected_count) is not int or not 1 <= expected_count <= 6
            or type(slot) is not int or not 0 <= slot < expected_count):
        raise ValueError('Invalid expected party count or slot')
    save = struct.unpack_from('<I', ram, 0x11186C)[0]
    offset = save + 0xD080 - 0x02000000
    if not 0 <= offset <= len(ram) - 8 - 236 * expected_count:
        raise ValueError('Save/party pointer outside main RAM')
    if struct.unpack_from('<II', ram, offset) != (6, expected_count):
        raise ValueError('Unexpected TEST party count or capacity')
    offset += 236 * slot
    mon = ram[offset + 8:offset + 8 + 236]
    pid, flags, checksum = struct.unpack_from('<IHH', mon)
    if flags & ~3:
        raise ValueError('Unexpected Pokémon flags or bad-egg marker')
    blocks = mon[8:136] if flags & 2 else crypt(mon[8:136], checksum)
    if sum(struct.unpack('<64H', blocks)) & 0xFFFF != checksum:
        raise ValueError('Pokémon checksum mismatch')
    order = list(itertools.permutations(range(4)))[((pid >> 13) & 31) % 24]
    a, b, c = (order.index(i) * 32 for i in [0, 1, 2])
    ivword = struct.unpack_from('<I', blocks, b + 16)[0]
    party = mon[136:] if flags & 1 else crypt(mon[136:], pid)
    species = struct.unpack_from('<H', blocks, a)[0]
    if (type(expected_level) is not int or not 1 <= expected_level <= 100
            or species != 152 or party[4] != expected_level):
        raise ValueError('Expected the specified-level Chikorita TEST fixture')
    return {
        'address': offset + 8 + 0x02000000, 'raw': mon,
        'species': species, 'level': party[4], 'checksum_valid': True,
        'pid': pid, 'ot_id': struct.unpack_from('<I', blocks, a + 4)[0],
        'nickname_u16': list(struct.unpack_from('<11H', blocks, c)),
        'is_nicknamed': bool(ivword & (1 << 31)),
        'is_egg': bool(ivword & (1 << 30)),
        'experience': struct.unpack_from('<I', blocks, a + 8)[0],
        'moves': list(struct.unpack_from('<4H', blocks, b)),
        'pp': list(blocks[b + 8:b + 12]),
        'status': struct.unpack_from('<I', party)[0],
        'EVs_HP_Atk_Def_Spe_SpA_SpD': list(blocks[a + 16:a + 22]),
        'IVs_HP_Atk_Def_Spe_SpA_SpD': [(ivword >> (5 * i)) & 31 for i in range(6)],
        'HP_current_max_Atk_Def_Spe_SpA_SpD': list(struct.unpack_from('<7H', party, 6)),
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('dump', type=Path)
    parser.add_argument('--expected-level', type=int, default=5)
    args = parser.parse_args()
    print(json.dumps({k: v for k, v in inspect(args.dump.read_bytes(), args.expected_level).items()
                      if k != 'raw'}, indent=2))
