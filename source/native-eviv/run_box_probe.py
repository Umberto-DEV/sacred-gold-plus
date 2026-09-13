#!/usr/bin/env python3
"""Replay native EV/IV on a normally deposited TEST Pokemon in Box 1.

The private fixture was prepared with synthetic party members, then deposited
and saved through the game. This replay performs no cheats, writes or deposit.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct

from run_probe import ROOT, HARNESS_SHA, sha, run, snapshot, same_region, inspect, require

FIXTURE_SHA = '5208191f489232908c41d160c0782d945bbf0084897c0465d809b9a41d7527d7'
BOX_MON_SHA = '4209e3d8273a9b1fc8b2b5c354b434fb2f27cbf48e668d30a3950662e10511d9'
PARTY_SHA = '9d820e84155a37af3fb2a1ad54c07a13d1ce42ce202a3d3598ba1fdd93cbfe2a'
CHECKS = ['stats', 'EV', 'IV', 'restored', 'page-return', 'outside', 'saved']


def open_summary():
    return ((ROOT / 'runtime/inputs/cold-reload.script').read_text()
            + 'tap A 8 360\ntap A 8 360\ntap A 8 360\ntap RIGHT 2 120\ntap A 8 600\n'
            + 'touch 190 50 2\nrun 600\ntap A 8 180\ntap DOWN 2 120\n'
            + 'tap A 8 600\ntap RIGHT 2 300\n')


def script():
    text = open_summary() + snapshot('stats')
    text += 'tap L 2 120\n' + snapshot('EV')
    text += 'tap R 2 120\n' + snapshot('IV')
    text += 'tap SELECT 2 120\n' + snapshot('restored')
    text += 'tap L 2 120\ntap RIGHT 2 120\ntap LEFT 2 120\n' + snapshot('page-return')
    # Summary returns to the context menu. Close it, then leave the selector,
    # answer No to continuing box operations, leave both PC menus, then SAVE.
    text += ('tap B 2 360\ntap B 8 240\ntap B 8 240\ntap DOWN 2 60\n'
             'tap A 8 360\ntap B 8 360\ntap B 8 360\n') + snapshot('outside')
    text += ('sram unchanged.sav\ntouch 120 75 2\nrun 600\ntap A 8 600\n'
             'tap A 8 1600\n') + snapshot('saved')
    return text + 'sram normal-SAVE-TEST.sav\nquit\n'


def read_data(path):
    ram = path.read_bytes()
    party = [inspect(ram, expected_count=2, slot=i) for i in range(2)]
    require(hashlib.sha256(b''.join(m['raw'] for m in party)).hexdigest() == PARTY_SHA,
            'Remaining TEST party differs from the independently prepared members')
    save = struct.unpack_from('<I', ram, 0x11186C)[0]
    # Relative offset confirmed by the actual deposited 136-byte member and
    # cold boot. PCStorage layout is from the pinned pret header (18 boxes).
    pc = save - 0x02000000 + 0x1C6F0
    require(0 <= pc <= len(ram) - 0x122FC, 'PC storage outside main RAM')
    boxed = ram[pc:pc + 136]
    require(hashlib.sha256(boxed).hexdigest() == BOX_MON_SHA,
            'Box 1 slot 1 differs from the independently prepared member')
    return {'party': [m['raw'] for m in party], 'boxed': boxed,
            'all_box_members': ram[pc:pc + 0x12000],
            'storage': ram[pc:pc + 0x122FC]}


def probe(build, fixture, harness, out):
    require(not out.exists(), 'Output must be new')
    meta = json.loads(build.read_text())
    require(meta['kind'] == 'private-native-pilot-not-release', 'Wrong build kind')
    require(Path(meta['rom_file']).name == meta['rom_file'], 'Unexpected ROM filename')
    rom = build.parent / meta['rom_file']
    require(sha(rom) == meta['rom_sha256'], 'Wrong ROM hash')
    require(sha(fixture) == FIXTURE_SHA and sha(harness) == HARNESS_SHA, 'Wrong TEST inputs')
    execution = run(harness, rom, fixture, out, script())
    initial = read_data(out / 'stats.bin')
    unchanged = {}
    for name in CHECKS:
        current = read_data(out / (name + '.bin'))
        # Saving may change bookkeeping. Every box's Pokemon bytes and the
        # remaining party must stay identical, including after a cold boot.
        keys = ['party', 'boxed', 'all_box_members']
        unchanged[name] = all(current[k] == initial[k] for k in keys)
        if name != 'saved':
            unchanged[name] &= current['storage'] == initial['storage']
    require(all(unchanged.values()), 'Party/storage data changed during the viewer')
    require(sha(out / 'unchanged.sav') == FIXTURE_SHA, 'Viewer changed SRAM')
    regions = [(4, 22, 143, 38), (4, 48, 143, 135), (152, 6, 248, 20)]
    restored = {n: all(same_region(out, 'stats', n, rect) for rect in regions)
                for n in ['restored', 'page-return']}
    require(all(restored.values()), 'Box numbers/title not restored')
    saved = out / 'normal-SAVE-TEST.sav'
    require(sha(saved) != FIXTURE_SHA, 'Normal SAVE did not complete')
    cold = run(harness, rom, saved, out / 'cold-reload', open_summary() + snapshot('cold') + 'quit\n')
    after = read_data(out / 'cold-reload/cold.bin')
    require(all(after[k] == initial[k] for k in ['party', 'boxed', 'all_box_members']),
            'Party/boxes differ after cold boot')
    require(sha(out / 'cold-reload/reloaded.sav') == sha(saved), 'Cold SRAM differs')
    result = {'kind': 'native-eviv-box-real-core', 'language': meta['language'],
              'build_sha256': sha(build), 'execution': execution, 'cold_execution': cold,
              'box_mon_sha256': BOX_MON_SHA, 'remaining_party_sha256': PARTY_SHA,
              'unchanged': unchanged, 'regions_restored': restored,
              'normal_save_sha256': sha(saved), 'cold_party_boxes_and_save_equal': True,
              'visual_review': 'pending',
              'limits': ['One deposited synthetic TEST Chikorita, Box 1 slot 1.',
                         'Not a trade, hatch, form, other species, GUI or Android test.']}
    (out / 'verification.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ['build', 'fixture', 'harness', 'out']:
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(probe(*(getattr(args, n).resolve() for n in ['build', 'fixture', 'harness', 'out']))))
