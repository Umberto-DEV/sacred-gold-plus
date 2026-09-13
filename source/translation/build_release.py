#!/usr/bin/env python3
"""Build one reviewed Plus release from locally owned, exact-hash input ROMs.

Recipes contain edits and references to retail Italian messages, not a retail
message corpus. Existing code/files stay at their original cartridge offsets.
"""
import argparse
import collections
import hashlib
import json
import struct
import sys
import zlib
from pathlib import Path

from ndspy import _common, narc, rom
import audit_localization as audit
from message_codec import Bank, encode_text, pack_name
from rom_container import append_files
from ui_resource import normalize_donor
from release_recipe import load_recipe

sys.path.insert(0, str(Path(__file__).resolve().parent.parent/'scripts'))
from build_rom_variants import correct_waits, SITES
from build_classic_camera import build as classic_camera


def sha(data):
    return hashlib.sha256(data).hexdigest()


def word_sha(words):
    return sha(struct.pack(f'<{len(words)}H', *words))


def apply_message_recipe(archives, recipe, chars, commands):
    parsed = {key: [Bank(b) for b in archive.files] for key, archive in archives.items()}
    target = parsed['SG']
    if len(target) != recipe['bank_count'] or sum(len(b.words) for b in target) != recipe['message_count']:
        raise ValueError('Unexpected message bank layout')
    seen = set()
    for row in recipe['messages']:
        b, m = row['bank'], row['message']
        if (b, m) in seen:
            raise ValueError(f'Duplicate recipe entry {b}/{m}')
        seen.add((b, m))
        old = target[b].words[m]
        if word_sha(old) != row['before_sha256']:
            raise ValueError(f'Message preimage mismatch {b}/{m}')
        kinds = [key for key in ('copy_from', 'text', 'word_patches') if key in row]
        if len(kinds) != 1:
            raise ValueError(f'Ambiguous message edit {b}/{m}')
        if 'copy_from' in row:
            source = row['copy_from']
            if source['rom'] not in ('US', 'IT'):
                raise ValueError('Only immutable retail donors are supported')
            words = parsed[source['rom']][source['bank']].words[source['message']].copy()
        elif 'text' in row:
            words = encode_text(row['text'], chars, commands)
            if old[0] == 0xF100:
                words = pack_name(words)
        else:
            words = old.copy()
            for edit in row['word_patches']:
                if words[edit['word_index']] != edit['old']:
                    raise ValueError(f'Word preimage mismatch {b}/{m}')
                words[edit['word_index']] = edit['new']
        if word_sha(words) != row['after_sha256']:
            raise ValueError(f'Message output mismatch {b}/{m}')
        target[b].replace(m, words)
    output = narc.NARC(archives['SG'].save())
    output.files = [b.save() for b in target]
    # Re-decode every emitted message independently from the builder codec.
    for bi, raw in enumerate(output.files):
        decoded = audit.read_bank(raw)
        if len(decoded) != len(target[bi].words):
            raise ValueError('Message count changed')
        for mi, value in enumerate(decoded):
            if value['malformed_controls'] or value['unknown_codes']:
                raise ValueError(f'Invalid emitted message {bi}/{mi}')
            if value['normalized'] != audit.render(target[bi].words[mi])['normalized']:
                raise ValueError('Independent decoder differs')
    return output.save()


def keyboard_edits(data, spec):
    data = bytearray(data)
    section = struct.unpack_from('<I', data, 0x20)[0]
    ram = struct.unpack_from('<I', data, 0x28)[0]
    changed = []
    for edit in spec['edits']:
        ptr = section + int(edit['pointer_guard_address'], 16) - ram
        if struct.unpack_from('<I', data, ptr)[0] != int(edit['pointer_guard_value'], 16):
            raise ValueError('Keyboard pointer guard failed')
        position = section + int(edit['section_offset'], 16)
        old, new = bytes.fromhex(edit['preimage_hex']), bytes.fromhex(edit['postimage_hex'])
        if len(old) != len(new) or data[position:position + len(old)] != old:
            raise ValueError('Keyboard data guard failed')
        data[position:position + len(old)] = new
        changed.extend(position + i for i, (a, b) in enumerate(zip(old, new)) if a != b)
    identity = section + int(spec['identity_guard']['runtime_address'], 16) - ram
    if data[identity] != spec['identity_guard']['must_remain']:
        raise ValueError('Internal save/game identity changed')
    return bytes(data), changed


def build(images, recipe, chars, commands, camera='plus', ui_manifest=None):
    if recipe['schema'] != 1 or recipe['language'] not in ('en', 'it') or recipe['internal_game_language'] != 2:
        raise ValueError('Unsupported recipe')
    if {key: sha(data) for key, data in images.items()} != recipe['input_sha256']:
        raise ValueError('Input ROM checksum does not match the reviewed versions')
    parsed = {key: rom.NintendoDSRom(data) for key, data in images.items()}
    archives = {key: narc.NARC(value.getFileByName('a/0/2/7')) for key, value in parsed.items()}
    message_data = apply_message_recipe(archives, recipe, chars, commands)
    data = correct_waits(images['SG'], images['US'])
    arm9_start, _, ram = struct.unpack_from('<III', data, 0x20)
    if camera == 'classic':
        data = bytearray(classic_camera(images['SG'], images['US']))
        for address in SITES:
            struct.pack_into('<I', data, arm9_start + address - ram, 0x1AFFFFFC)
        data = bytes(data)
    keyboard = []
    if recipe['keyboard']:
        data, keyboard = keyboard_edits(data, recipe['keyboard'])
    expected_arm9 = rom.NintendoDSRom(data).arm9
    replacements = {'a/0/2/7': message_data}
    # UI manifests are explicit member-level decisions. Whole-archive language
    # swaps are not inferred from matching member counts or filenames.
    ui_proof = []
    if ui_manifest:
        if ui_manifest['schema'] != 2 or ui_manifest['variant'] != recipe['language']:
            raise ValueError('UI manifest does not match the language recipe')
        by_file = collections.defaultdict(list)
        seen_ui = set()
        for row in ui_manifest['edits']:
            key = (row['file'], row['member'])
            if key in seen_ui or row['donor'] not in ('US', 'IT'):
                raise ValueError('Invalid or duplicate UI edit')
            if recipe['language'] == 'en' and row['donor'] != 'US':
                raise ValueError('English UI cannot import an Italian graphic')
            seen_ui.add(key)
            by_file[row['file']].append(row)
        required = {('a/0/6/8', i, 'US') for i in (12, 13, 14, 57, 58, 65, 66)}
        actual = {(r['file'], r['member'], r['donor']) for r in ui_manifest['edits']
                  if r.get('atomic_group') == 'pokedex-us-imperial-search'}
        if actual != required:
            raise ValueError('Incomplete Pokédex imperial search resource group')
        for group, members in ui_manifest['required_atomic_groups'].items():
            expected_group = {(r['file'], r['member'], r['donor']) for r in members}
            actual_group = {(r['file'], r['member'], r['donor']) for r in ui_manifest['edits'] if r.get('atomic_group') == group}
            if expected_group != actual_group:
                raise ValueError(f'Incomplete UI resource group: {group}')
        for path, rows in by_file.items():
            target = narc.NARC(parsed['SG'].getFileByName(path))
            italian = narc.NARC(parsed['IT'].getFileByName(path))
            original = narc.NARC(parsed['US'].getFileByName(path))
            before_members = target.files.copy()
            for row in rows:
                index = row['member']
                for key, member in [('SG', target.files[index]), ('IT', italian.files[index]), ('US', original.files[index])]:
                    if sha(member) != row['sha256'][key]:
                        raise ValueError(f'UI member checksum mismatch {path}/{index} {key}')
                if target.files[index] != original.files[index] and not row.get('plus_diff_reviewed', False):
                    raise ValueError(f'Unreviewed Plus-specific UI member {path}/{index}')
                donor = original if row['donor'] == 'US' else italian
                final_member = normalize_donor(target.files[index], donor.files[index], row.get('transform'))
                target.files[index] = final_member
                ui_proof.append({'file': path, 'member': index, 'donor': row['donor'],
                                 'transform': row.get('transform'), 'sha256': sha(final_member)})
            selected = {row['member'] for row in rows}
            if len(target.files) != len(before_members) or any(a != b and i not in selected for i, (a, b) in enumerate(zip(before_members, target.files))):
                raise ValueError('Unexpected UI archive change')
            replacements[path] = target.save()
        for row in ui_manifest['protected_members']:
            path, index = row['file'], row['member']
            members = narc.NARC(replacements.get(path, parsed['SG'].getFileByName(path))).files
            if sha(members[index]) != row['SG_sha256']:
                raise ValueError(f'Protected Plus resource changed {path}/{index}')
    data, extents = append_files(data, replacements, reuse_existing=True)
    result = rom.NintendoDSRom(data)
    original = parsed['SG']
    if result.arm9 != expected_arm9 or result.arm7 != original.arm7 or result.arm9OverlayTable != original.arm9OverlayTable or result.arm7OverlayTable != original.arm7OverlayTable:
        raise ValueError('Unexpected executable or overlay-table change')
    changed_ids = {original.filenames.idOf(path) for path in replacements}
    if len(result.files) != len(original.files) or result.filenames != original.filenames:
        # ndspy Folder has value equality; all paths and IDs must stay stable.
        if repr(result.filenames) != repr(original.filenames) or len(result.files) != len(original.files):
            raise ValueError('NitroFS structure changed')
    for i, (before, after) in enumerate(zip(original.files, result.files)):
        if i not in changed_ids and before != after:
            raise ValueError(f'Unexpected file change {i}')
    for path, replacement in replacements.items():
        if result.getFileByName(path) != replacement:
            raise ValueError(f'Reinserted file mismatch {path}')
    if data[arm9_start + 0xF5670] != 2:
        raise ValueError('English save identity was not retained')
    if struct.unpack_from('<H', data, 0x15E)[0] != _common.crc16(data[:0x15E]):
        raise ValueError('Invalid header CRC')
    report = {'schema': 1, 'release': recipe['release'], 'ui_language': recipe['language'],
              'internal_game_language': 2, 'camera': camera, 'sha256': sha(data), 'bytes': len(data),
              'cheat_id': data[12:16].decode('ascii') + ' ' + f'{zlib.crc32(data[:512]) ^ 0xFFFFFFFF:08X}',
              'recipe_sha256': sha(json.dumps(recipe, ensure_ascii=False, separators=(',', ':')).encode() + b'\n'),
              'replaced_files': extents, 'ui_members': ui_proof, 'keyboard_changed_bytes': len(keyboard),
              'message_edits': len(recipe['messages']), 'message_count': recipe['message_count'],
              'static_checks': 'PASS: hashes, message decoding, counts, file/code isolation, language identity, header CRC',
              'runtime_checks': 'Not performed by this builder'}
    return data, report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--rom-dir', type=Path, required=True)
    p.add_argument('--pret-source', type=Path, required=True)
    p.add_argument('--recipe', type=Path, required=True)
    p.add_argument('--camera', choices=('plus', 'classic'), default='plus')
    p.add_argument('--ui-manifest', type=Path)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    report_path = args.output.with_suffix('.build.json')
    if args.output.exists() or report_path.exists():
        p.error('Output already exists; no file is overwritten')
    recipe = load_recipe(args.recipe)
    audit.PRET = args.pret_source
    chars, commands = audit.mapping()
    audit.CHARMAP, audit.COMMANDS = chars, commands
    images = {key: (args.rom_dir / name).read_bytes() for key, name in audit.NAMES.items()}
    ui_manifest = json.loads(args.ui_manifest.read_text()) if args.ui_manifest else None
    data, report = build(images, recipe, chars, commands, args.camera, ui_manifest)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('xb') as f:
        f.write(data)
    with report_path.open('x') as f:
        json.dump(report, f, indent=2)
        f.write('\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
