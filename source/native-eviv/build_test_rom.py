#!/usr/bin/env python3
"""Build a private 1.05 EV/IV pilot from one exact Community 1 ROM.

Requires ndspy, Clang's ARM backend and the pinned public pret charmap.
No download, source-ROM overwrite, save access or emulator-profile mutation.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys

import ndspy.narc
import ndspy.rom

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'translation'))
from message_codec import Bank, encode_text
from rom_container import append_files
from native_image import PAYLOAD_BASE, require, reserve_itcm, replace_arm9
from thumb_object import load_text

KNOWN = {
    '3ed4ea0291092d46def2f71454821bbde7832014ec020680468af7bfca686248': 'en',
    'ef0e61bbcad07d732054a19a0b4ee64563bb2d7503ee9fd62348643fcb630760': 'en',
    '217daa45f4945abd3feda6f583f5163db029d1aa361c33c18f12b32ad4eca4a4': 'it',
    '9dd0c98eb96b91037592bc30574210b191e9f2c2fca45f466733eeb5b9a12d0a': 'it',
}
CHARMAP_SHA = 'd010fe01f7a83d29d039c6732cb3e88c1d5ada4407b7aea6eb43f74e96dbfa29'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def build(source_path, charmap_path, out, baseline_r4=False):
    require(not out.exists(), 'Output directory must be new')
    source = source_path.read_bytes()
    source_hash = digest(source)
    require(source_hash in KNOWN, 'Unknown complete ROM hash')
    raw_charmap = charmap_path.read_bytes()
    require(digest(raw_charmap) == CHARMAP_SHA, 'Unexpected public charmap revision')
    chars, commands = {}, {}
    for line in raw_charmap.decode().splitlines():
        line = line.split('//')[0].lstrip()
        if '=' not in line:
            continue
        number, value = line.split('=', 1)
        code = int(number, 16)
        if value.startswith('{') and value.endswith('}'):
            commands[code] = value[1:-1]
        else:
            chars[code] = value
    nds = ndspy.rom.NintendoDSRom(source)
    main = nds.loadArm9()
    messages = ndspy.narc.NARC(nds.getFileByName('a/0/2/7'))
    original_messages = list(messages.files)
    bank = Bank(messages.files[302])
    old_count = len(bank.words)
    language = KNOWN[source_hash]
    normal = 'Stats L:EV R:IV' if language == 'en' else 'Dati L:EV R:IV'
    ev = 'EV Sel:Stats' if language == 'en' else 'EV Sel:Dati'
    iv = 'IV Sel:Stats' if language == 'en' else 'IV Sel:Dati'
    bank.replace(109, encode_text(normal, chars, commands))
    # Build a new bank because appending changes the allocation table size.
    bank = Bank.from_words(bank.words + [encode_text(ev, chars, commands),
                                       encode_text(iv, chars, commands)], bank.key)
    out.mkdir(parents=True)
    obj = out / 'eviv.o'
    payload_source = Path(__file__).with_name('eviv.c')
    if baseline_r4:
        payload_source = payload_source.parent / 'history/eviv-r4.c'
    command = ['clang', '--target=armv5te-none-eabi', '-mcpu=arm946e-s', '-mthumb', '-Oz',
               '-ffreestanding', '-fno-builtin', '-fno-stack-protector', '-fno-unwind-tables',
               '-fno-asynchronous-unwind-tables', '-fno-jump-tables',
               '-DEV_MSG_ID=' + str(old_count), '-DIV_MSG_ID=' + str(old_count + 1),
               '-c', str(payload_source), '-o', str(obj)]
    compilation = subprocess.run(command, text=True, capture_output=True)
    (out / 'compile.log').write_text(compilation.stdout + compilation.stderr)
    require(compilation.returncode == 0, 'ARM compilation failed; inspect compile.log')
    payload, symbols = load_text(obj.read_bytes(), PAYLOAD_BASE)
    if baseline_r4:
        require(digest(payload) == '7677a6b5f1ec7657f70efa335f1ce36669bce1bfe484315d6e75e038abb050c0',
                'Historical r4 payload does not match the measured baseline')
    memory = reserve_itcm(main, payload, symbols['eviv_hook'], symbols['stats_hook'])
    arm9 = main.save(compress=True)
    result = replace_arm9(source, arm9)
    messages.files[302] = bank.save()
    result, changes = append_files(result, {'a/0/2/7': messages.save()}, reuse_existing=True)
    check = ndspy.rom.NintendoDSRom(result)
    actual = check.loadArm9()
    require(actual.sections[1].data == main.sections[1].data, 'ITCM decompression mismatch')
    require(actual.sections[2].data == main.sections[2].data, 'DTCM changed')
    require(check.arm7 == nds.arm7 and check.arm9OverlayTable == nds.arm9OverlayTable
            and check.arm7OverlayTable == nds.arm7OverlayTable, 'Other executable metadata changed')
    msg_id = nds.filenames.idOf('a/0/2/7')
    require(len(check.files) == len(nds.files)
            and all(a == b or i == msg_id for i, (a, b) in enumerate(zip(nds.files, check.files))),
            'Unselected NitroFS data changed')
    checked_messages = ndspy.narc.NARC(check.files[msg_id]).files
    require(len(checked_messages) == len(original_messages)
            and all(a == b or i == 302 for i, (a, b) in
                    enumerate(zip(original_messages, checked_messages))),
            'Unselected message bank changed')
    checked_words = Bank(checked_messages[302]).words
    original_words = Bank(original_messages[302]).words
    require(checked_words == bank.words
            and all(a == b or i == 109 for i, (a, b) in
                    enumerate(zip(original_words, checked_words))),
            'Unselected summary message changed')
    target = out / ('Sacred Gold Plus 1.05 EVIV TEST ' + language.upper() + '.nds')
    target.write_bytes(result)
    require(digest(source_path.read_bytes()) == source_hash, 'Input ROM changed')
    report = {'kind': 'private-native-pilot-not-release', 'base_sha256': source_hash,
              'rom_file': target.name, 'rom_sha256': digest(result), 'rom_bytes': len(result),
              'language': language, 'memory': memory, 'symbols': symbols,
              'source_variant': 'r4-performance-baseline' if baseline_r4 else 'current-pilot',
              'payload_source_sha256': digest(payload_source.read_bytes()),
              'object_sha256': digest(obj.read_bytes()), 'payload_sha256': digest(payload),
              'compile_command': command, 'message_bank': 302,
              'message_edits': [109, old_count, old_count + 1],
              'NitroFS_changes': changes, 'ARM9_compressed_bytes': len(arm9),
              'secure_crc_before': nds.secureAreaChecksum, 'secure_crc_after': check.secureAreaChecksum,
              'secure_crc_scope': 'Source-relative update with unchanged encrypted prefix; no hardware boot certification.',
              'static_checks': 'ITCM/DTCM roundtrip, ARM7/overlay tables/unselected files/banks/messages preserved',
              'runtime_validation': 'pending'}
    (out / 'build.json').write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ['rom', 'charmap', 'out']:
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--baseline-r4', action='store_true',
                        help='Reconstruct the historical performance baseline, not the current pilot')
    args = parser.parse_args()
    print(json.dumps(build(args.rom.resolve(), args.charmap.resolve(), args.out.resolve(), args.baseline_r4)))
