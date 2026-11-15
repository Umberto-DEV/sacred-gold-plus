#!/usr/bin/env python3
"""Read-only attribution of Battle Party in an exact 1.3.2 r4 EN/IT image.

No ROM, extracted bytes or personal input paths are written to the JSON report.
The pre/post installer reader remains tools/rileggi.py; this checks the final
composed image without pretending later composition is confined to this owner.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

import ndspy.narc
import ndspy.rom

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
sys.path.insert(0, str(HERE))
from rileggi import (Arm9RO, bersaglio_bl, immagine_overlay, leggi_overlay,
                    tabelle)

BASE, SIZE = 0x023DBE00, 256
CODE_SHA = 'a9b56d5ea7fe8df1c9a91b4305b04512d329ac7f7ad51cc74cf24bff399912be'
SYMBOLS = {'sgp_squadra_attr_cache': 0x023DBE01,
           'sgp_squadra_attr_hook': 0x023DBEB5,
           'sgp_squadra_pp_cache': 0x023DBE7D,
           'sgp_squadra_pp_hook': 0x023DBEBF}
CALLS = ((0x0221D3DE, 0x023DBEBE), (0x0221D3E8, 0x023DBEB4),
         (0x0221D3F2, 0x023DBEB4), (0x0221D3FC, 0x023DBEB4),
         (0x0221D406, 0x023DBEB4))


def sha(data):
    return hashlib.sha256(data).hexdigest()


def require(ok, message):
    if not ok:
        raise ValueError(message)


def check_identity(raw, language):
    contract = json.loads((REPO / 'source/distribution/game-1.3.2-r4.json').read_text())
    require(language in ('EN', 'IT'), 'only r4 EN/IT are qualified')
    identity = {'bytes': len(raw), 'sha256': sha(raw)}
    target = contract['targets'][language]
    require(all(identity[k] == target[k] for k in identity), 'wrong r4 identity/language')
    return identity


def check_block(block, build):
    build = Path(build)
    blob = (build / 'blob.bin').read_bytes()
    manifest = json.loads((build / 'manifesto.json').read_text())
    require(len(blob) == 200 and sha(blob) == CODE_SHA, 'unqualified compiled payload')
    require({k: int(v, 16) for k, v in manifest['simboli'].items()} == SYMBOLS,
            'unqualified symbol layout')
    canary = b''.join(struct.pack('<I', 0xCA5A1A00 | i) for i in range(4))
    require(bytes(block) == blob + bytes(40) + canary, 'installed code/padding/canary mismatch')
    origin = json.loads((build / 'origine.json').read_text())
    sources = ('source/features/squadra-lotta/sorgenti/squadra_cache.c',
               'source/features/squadra-lotta/tools/compila.py')
    require(origin['sorgenti'] == {p: sha((REPO / p).read_bytes()) for p in sources},
            'source drift: rebuild and review before attributing')
    return {'address': BASE, 'bytes': len(block), 'sha256': sha(block),
            'code_bytes': len(blob), 'code_sha256': sha(blob),
            'padding_bytes': 40, 'canary_bytes': 16,
            'source_sha256': origin['sorgenti'], 'symbols': SYMBOLS}


def check_call(site, encoded, expected):
    actual = bersaglio_bl(site, encoded)
    require(actual == expected, 'wrong Thumb BL at %#x' % site)
    return {'site': site, 'target': actual}


def move_table(raw):
    """Independent raw BTAF/GMIF walk; cross-check ndspy's per-member decoder.

    The native loader reads 7488 contiguous bytes from member 0. Concatenating
    members alone would hide padding or gaps between the physical records.
    """
    require(len(raw) >= 28 and raw[:4] == b'NARC', 'missing move NARC')
    size, header, blocks = struct.unpack_from('<IHH', raw, 8)
    require(size == len(raw) and header == 16 and blocks == 3, 'move NARC geometry')
    magic, fat_size, count = struct.unpack_from('<4sII', raw, 16)
    require(magic == b'BTAF' and count == 471 and fat_size == 12 + count * 8,
            'move BTAF geometry')
    names = 16 + fat_size
    require(names + 8 <= len(raw) and raw[names:names+4] == b'BTNF', 'move BTNF')
    image = names + struct.unpack_from('<I', raw, names + 4)[0]
    require(image + 8 <= len(raw) and raw[image:image+4] == b'GMIF', 'move GMIF')
    image_size = struct.unpack_from('<I', raw, image + 4)[0]
    require(image + image_size == len(raw), 'move GMIF extent')
    data = image + 8
    for index in range(count):
        start, end = struct.unpack_from('<II', raw, 28 + index * 8)
        require((start, end) == (16 * index, 16 * (index + 1)),
                'noncontiguous move record %d' % index)
    require(data + 16 * count <= len(raw), 'truncated move records')
    members = ndspy.narc.NARC(raw).files
    table = bytes(raw[data:data+7488])
    require(table == b''.join(members[:468]), 'raw/ndspy move table disagreement')
    return data, table


def inspect_image(path, language, build):
    arm = Arm9RO(path)
    raw = arm.raw
    identity = check_identity(raw, language)
    report = {'schema': 1, 'language': language, 'rom': identity,
              'block': check_block(arm.leggi(BASE, SIZE), build)}
    report['block']['rom_offset'] = arm.off(BASE, SIZE)
    nds = ndspy.rom.NintendoDSRom(raw)
    main = nds.loadArm9()
    matches = [s for s in main.sections if s.ramAddress <= BASE
               and BASE + SIZE <= s.ramAddress + len(s.data)]
    require(len(matches) == 1, 'ambiguous ARM9 section')
    section = matches[0]
    at = BASE - section.ramAddress
    require(bytes(section.data[at:at+SIZE]) == arm.leggi(BASE, SIZE),
            'ARM9 raw/ndspy mapping disagreement')
    report['arm9'] = {'file_offset': arm.off9, 'stored_bytes': arm.siz9,
                      'section_address': section.ramAddress, 'section_bytes': len(section.data),
                      'autoload': not section.implicit, 'module_params_offset': main.codeSettingsOffs}
    report['overlays'] = {}
    # Select only these overlays rather than decompressing all 129.
    decoded = nds.loadArm9Overlays([8, 12])
    for oid in (8, 12):
        entry = leggi_overlay(raw, tabelle(raw), oid)
        require(entry['id'] == oid, 'overlay record ID')
        image = immagine_overlay(raw, entry)
        ov = decoded[oid]
        require(image == bytes(ov.data) and entry['file_id'] == ov.fileID
                and entry['ram'] == ov.ramAddress, 'independent overlay decoder disagreement')
        report['overlays'][str(oid)] = {**entry, 'logical_sha256': sha(image),
            'logical_bytes': len(image), 'stored_sha256': sha(raw[entry['inizio']:entry['fine']])}
        if oid == 8:
            report['calls'] = [dict(check_call(site, image[site-entry['ram']:site-entry['ram']+4], target),
                                    overlay_offset=site-entry['ram']) for site, target in CALLS]
        else:
            off = 0x022486A8 - entry['ram']
            require(struct.unpack_from('<I', image, off)[0] == 0x3DE, 'MoveTbl offset is not 3DE')
            check_call(0x02248692, image[0x02248692-entry['ram']:0x02248696-entry['ram']], 0x02073300)
    # Native getter entry points and their dependencies are guarded by exact r4
    # identity. The isolated execution test runs those actual installed bytes.
    fid = nds.filenames.idOf('a/0/1/1')
    fat = struct.unpack_from('<I', raw, 0x48)[0]
    start, end = struct.unpack_from('<II', raw, fat + fid * 8)
    archive = raw[start:end]
    require(archive == nds.files[fid], 'FNT/FAT archive disagreement')
    data, table = move_table(archive)
    report['moves'] = {'file_id': fid, 'rom_offset': start, 'archive_bytes': end-start,
        'archive_sha256': sha(archive), 'member0_rom_offset': start+data,
        'table_bytes': len(table), 'table_sha256': sha(table), 'records_loaded': 468,
        'records_in_archive': 471, 'ctx_offset': 0x3DE, 'move261_accuracy': table[261*16+5]}
    report['limits'] = ['Exact r4 EN/IT component readback; no pre/post confinement claim.',
        'Two overlay decoders; ARM9 raw mapping shares the project layout validator.',
        'Static callers and loader, not an observation of all game paths or hardware timing.']
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom', required=True)
    parser.add_argument('--language', choices=('EN', 'IT'), required=True)
    parser.add_argument('--build', type=Path, default=REPO / 'source/sgp12/build/squadra_lotta')
    parser.add_argument('--json', type=Path)
    args = parser.parse_args()
    try:
        result = inspect_image(args.rom, args.language, args.build)
    except (ValueError, OSError, KeyError, struct.error) as exc:
        print('attribution rejected: %s' % exc, file=sys.stderr)
        return 1
    output = json.dumps(result, indent=2) + '\n'
    if args.json:
        # Never overwrite an input ROM or an existing report accidentally.
        with args.json.open('x') as handle:
            handle.write(output)
    print(output, end='')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
