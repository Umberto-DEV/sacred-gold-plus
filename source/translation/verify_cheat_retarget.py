#!/usr/bin/env python3
"""Read-only address/guard check when retargeting the selected Plus cheats.

Pass every final ROM with --candidate. Only a JSON audit is written.
This does not produce, enable or install any cheat database.
"""
import argparse
import hashlib
import json
import sys
import zlib
from pathlib import Path

import ndspy.rom

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent))
import audit_cheats as audit


def inspect(path):
    image = Path(path).read_bytes()
    parsed = ndspy.rom.NintendoDSRom(image)
    sections = audit.rom_sections(path)
    return {'file': Path(path).name, 'sha256': hashlib.sha256(image).hexdigest(),
            'game_code': image[12:16].decode('ascii'),
            'cheat_id': image[12:16].decode('ascii') + ' ' + f'{zlib.crc32(image[:512]) ^ 0xFFFFFFFF:08X}',
            'arm9_ram_address': parsed.arm9RamAddress,
            'section_layout': [(name, start, len(data)) for name, start, data in sections],
            'sections': sections}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-rom', required=True, type=Path)
    parser.add_argument('--candidate', required=True, action='append', type=Path)
    parser.add_argument('--manifest', type=Path, default=ROOT.parent.parent/'cheats/source/selected-codes.json')
    parser.add_argument('--keyboard-plan', type=Path, default=ROOT.parent/'ui/keyboard-reference.json')
    parser.add_argument('--output', type=Path, default=ROOT/'cheat-retarget-verification.json')
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text())
    cheats = next(game['cheats'] for game in manifest['games'] if game['key'] == 'SG_PLUS')
    assert len(cheats) == 13 and all(not cheat['enabled'] for cheat in cheats)
    base = inspect(args.base_rom)
    assert base['sha256'] == '78b198fbad961970ef8563587fb2278ee957e6297589a847dbe78f73d12cc0c1'
    keyboard = json.loads(args.keyboard_plan.read_text())
    keyboard_ranges = [(int(edit['runtime_address'], 16), len(bytes.fromhex(edit['postimage_hex']))) for edit in keyboard['edits']]
    reports = []
    for path in args.candidate:
        candidate = inspect(path)
        rows = []
        for cheat in cheats:
            source = {'name': cheat['name'], 'codes': cheat['codes'], 'folders': [cheat['category']]}
            check = audit.analyze_cheat(source, candidate['sections'], base['sections'])
            watches = {(int(row['address'], 16), row['bytes']) for row in check['equality_guards']}
            watches |= {(int(row['address'], 16), row['bytes']) for row in check['writes'] if row['address'] is not None}
            instructions, issues = audit.decode(cheat['codes'])
            for instruction in instructions:
                if instruction['op'] >> 4 in (6, 0xB):
                    watches.add((instruction['a'] & 0x0FFFFFFF, 4))
            changed = []
            overlaps = []
            for address, size in sorted(watches):
                old_values = {row['region']: row['value'] for row in audit.read_sources(base['sections'], address, size)}
                new_values = {row['region']: row['value'] for row in audit.read_sources(candidate['sections'], address, size)}
                if old_values != new_values:
                    changed.append({'address': f'{address:08X}', 'bytes': size, 'before': old_values, 'after': new_values})
                if any(address < begin+length and begin < address+size for begin, length in keyboard_ranges):
                    overlaps.append({'address': f'{address:08X}', 'bytes': size})
            rows.append({'name': cheat['name'], 'code_sha256': hashlib.sha256(cheat['codes'].encode()).hexdigest(),
                         'changed_watched_sites': changed, 'keyboard_overlap': overlaps,
                         'guards': [{'address': guard['address'], 'status': guard['status'], 'regions': guard['matching_regions']}
                                    for guard in check['equality_guards']],
                         'parser_issues': check['issues'], 'enabled': False})
        same_layout = candidate['section_layout'] == base['section_layout']
        reusable = same_layout and all(not row['changed_watched_sites'] and not row['keyboard_overlap'] and not row['parser_issues'] for row in rows)
        reports.append({key: value for key, value in candidate.items() if key != 'sections'} | {
            'RAM_section_layout_unchanged': same_layout, 'selected_13_cheat_addresses_reusable_static': reusable, 'cheats': rows})
    result = {
        'scope': 'Selected Plus cheat set only; static guards and original bytes at all mapped read/write sites.',
        'base': {key: value for key, value in base.items() if key not in ('sections', 'section_layout')},
        'candidates': reports,
        'routing': {'Android_XML': 'Create a game entry for each distinct final cheat_id. Keep the Plus IPKE address set even for the Italian UI; do not switch to retail IPKI cheats.',
                    'desktop_MCH': 'Use the exact ROM basename with .mch; the selected command text stays unchanged after these checks pass.',
                    'defaults': 'All cheats disabled, including experiments. Header identity alone does not prove command compatibility.'},
        'planned_keyboard_ranges': [{'address': f'{start:08X}', 'bytes': size} for start, size in keyboard_ranges],
        'CRC_rule': 'Game code at bytes12–15 plus CRC32 of the first512 bytes with initialFFFFFFFF and no final XOR (zlib.crc32(header)^FFFFFFFF).',
        'limitations': ['No game execution or Android import performed by this script.',
                       'Dynamic save pointers, overlay lifetime and JIT code invalidation retain the limitations from the existing cheat audit.',
                       'Rerun on every final ROM; reports for preliminary variants do not validate a later binary.']
    }
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps([{'file': row['file'], 'cheat_id': row['cheat_id'], 'addresses_reusable_static': row['selected_13_cheat_addresses_reusable_static']}
                      for row in reports], ensure_ascii=False))
    if not all(row['selected_13_cheat_addresses_reusable_static'] for row in reports):
        raise SystemExit(1)


if __name__ == '__main__':
    main()
