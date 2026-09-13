#!/usr/bin/env python3
"""Native pilot regression on the identified three-slot synthetic TEST party."""
import argparse
import json
from pathlib import Path

from run_probe import ROOT, HARNESS_SHA, sha, run, snapshot, same_region, inspect, require

FIXTURE_SHA = '966338cfff49cd214479adce11f113df4085c357634b1febce1d89638e1ac583'
PARTY_SHA = '0eb5010010a256858f55346b268e26ee185a5d23c30f8d4ed3da5da226da5f59'
MON_CHECKS = ['initial', 'first-stats', 'first-EV', 'second-stats', 'second-EV',
              'second-IV', 'second-restored', 'first-return', 'egg', 'egg-after', 'saved']


def script():
    text = (ROOT / 'runtime/inputs/cold-reload.script').read_text()
    # Field frames can stop inside GetBoxMonData's transient decrypt/re-encrypt
    # window. Sample all slots at the settled summary screen before using L/R.
    text += ('touch 40 75 2\nrun 240\ntouch 64 30 2\nrun 120\n'
             'touch 184 40 2\nrun 360\ntap RIGHT 2 300\n') + snapshot('first-stats')
    text += 'dump initial.bin\n'
    text += 'tap L 2 120\n' + snapshot('first-EV')
    text += 'tap DOWN 2 300\n' + snapshot('second-stats')
    text += 'tap L 2 120\n' + snapshot('second-EV')
    text += 'tap R 2 120\n' + snapshot('second-IV')
    text += 'tap SELECT 2 120\n' + snapshot('second-restored')
    text += 'tap UP 2 300\n' + snapshot('first-return')
    text += ('tap B 2 180\ntouch 64 75 2\nrun 120\n'
             'touch 184 40 2\nrun 360\n') + snapshot('egg')
    text += 'tap L 2 120\ntap R 2 120\ntap SELECT 2 120\ntap RIGHT 2 120\n' + snapshot('egg-after')
    text += ('tap B 2 180\ntap B 2 180\nsram unchanged.sav\ntouch 120 75 2\nrun 600\n'
             'tap A 8 600\ntap A 8 1600\n') + snapshot('saved')
    return text + 'sram normal-SAVE-TEST.sav\nquit\n'


def read_party(path):
    ram = path.read_bytes()
    return [inspect(ram, expected_count=3, slot=i) for i in range(3)]


def probe(build, fixture, harness, out):
    require(not out.exists(), 'Output directory must be new')
    meta = json.loads(build.read_text())
    require(meta['kind'] == 'private-native-pilot-not-release', 'Not a native build')
    require(Path(meta['rom_file']).name == meta['rom_file'], 'Unexpected ROM name')
    rom = build.parent / meta['rom_file']
    require(sha(rom) == meta['rom_sha256'], 'ROM hash mismatch')
    require(sha(fixture) == FIXTURE_SHA and sha(harness) == HARNESS_SHA, 'Wrong TEST inputs')
    execution = run(harness, rom, fixture, out, script())
    initial = read_party(out / 'initial.bin')
    require(initial[0]['EVs_HP_Atk_Def_Spe_SpA_SpD'] == [1, 2, 3, 4, 5, 6]
            and initial[1]['EVs_HP_Atk_Def_Spe_SpA_SpD'] == [252, 0, 0, 252, 4, 2]
            and initial[1]['IVs_HP_Atk_Def_Spe_SpA_SpD'] == [31, 0, 1, 30, 15, 16]
            and initial[1]['HP_current_max_Atk_Def_Spe_SpA_SpD'][:2] == [11, 24]
            and initial[2]['is_egg'], 'Fixture conditions missing')
    raws = [m['raw'] for m in initial]
    import hashlib
    require(hashlib.sha256(b''.join(raws)).hexdigest() == PARTY_SHA,
            'Party differs from the independently prepared fixture before L/R')
    unchanged = {n: [m['raw'] for m in read_party(out / (n + '.bin'))] == raws for n in MON_CHECKS}
    require(all(unchanged.values()), 'A party member changed')
    require(sha(out / 'unchanged.sav') == FIXTURE_SHA, 'UI changed SRAM')
    regions = [(4, 22, 143, 38), (4, 48, 143, 135), (152, 6, 248, 20)]
    restored = {a: all(same_region(out, a, b, box) for box in regions)
                for a, b in [('first-stats', 'first-return'), ('second-stats', 'second-restored')]}
    require(all(restored.values()), 'Wrong numbers/title after return or Select')
    egg_same = same_region(out, 'egg', 'egg-after', (0, 6, 143, 188))
    require(egg_same, 'EV/IV inputs changed the egg information page')
    saved = out / 'normal-SAVE-TEST.sav'
    require(sha(saved) != FIXTURE_SHA, 'Normal SAVE not completed')
    cold_script = (ROOT / 'runtime/inputs/cold-reload.script').read_text()
    cold_script += ('touch 40 75 2\nrun 240\ntouch 64 30 2\nrun 120\n'
                    'touch 184 40 2\nrun 360\ntap RIGHT 2 300\ndump cold.bin\nquit\n')
    cold = run(harness, rom, saved, out / 'cold-reload', cold_script)
    require([m['raw'] for m in read_party(out / 'cold-reload/cold.bin')] == raws,
            'Party changed after cold boot')
    require(sha(out / 'cold-reload/reloaded.sav') == sha(saved), 'Cold SRAM differs')
    result = {'kind': 'native-eviv-three-slot-real-core', 'language': meta['language'],
              'build_sha256': sha(build), 'execution': execution, 'cold_execution': cold,
              'party': [{k: v for k, v in m.items() if k != 'raw'} for m in initial],
              'party_unchanged': unchanged, 'regions_restored': restored,
              'egg_info_unchanged': egg_same, 'cold_party_and_save_equal': True,
              'normal_save_sha256': sha(saved), 'visual_review': 'pending',
              'limits': ['Synthetic Chikorita copies sharing PID/OT, one synthetic egg.',
                         'No hatch, breeding, trade, box, other species or full party claim.',
                         'Core interpreter/software 1x, no cheats; no GUI/Android claim.']}
    (out / 'verification.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ['build', 'fixture', 'harness', 'out']:
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(probe(*(getattr(args, n).resolve() for n in ['build', 'fixture', 'harness', 'out']))))
