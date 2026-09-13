#!/usr/bin/env python3
"""Measure a pinned private pilot/baseline on the separate observation core."""
import argparse
import json
from pathlib import Path

from run_probe import ROOT, FIXTURE_SHA, sha, run, inspect, require

ROMS = {
    '3ed4ea0291092d46def2f71454821bbde7832014ec020680468af7bfca686248': 'base-en',
    'bd09b0c8a1e9cbd06cf574d38bcdea776bb60477c371bf80d23fc752dd770fc0': 'pilot-en-r4',
    'a1d7ed3ecb8aa98f96f65c17015cb49df5bda84323459cb17fd3d4c4501f556e': 'pilot-en-r5',
}


def script():
    text = (ROOT / 'runtime/inputs/cold-reload.script').read_text()
    text += ('dump initial.bin\ntouch 40 75 2\nrun 240\ntouch 64 30 2\nrun 120\n'
             'touch 184 40 2\nrun 360\ntap RIGHT 2 300\nprofile reset\nprofile on\n'
             'run 600\nprofile off\nprofile report idle.json\nprofile reset\nprofile on\n')
    text += 'tap L 2 120\ntap R 2 120\ntap SELECT 2 120\n' * 8
    text += ('profile off\nprofile report inputs.json\ncapture restored.ppm\n'
             'dump final.bin\nsram unchanged.sav\nquit\n')
    return text


def profile(rom, fixture, harness, expected_harness_sha, out):
    require(not out.exists(), 'Output directory must be new')
    require(sha(rom) in ROMS and sha(fixture) == FIXTURE_SHA, 'Wrong TEST input')
    require(sha(harness) == expected_harness_sha, 'Observation binary identity differs')
    execution = run(harness, rom, fixture, out, script())
    reports = {n: json.loads((out / (n + '.json')).read_text()) for n in ['idle', 'inputs']}
    for report in reports.values():
        require(report['kind'] == 'ARM9-summary-input-inclusive-cycles'
                and not report['active'] and report['incomplete'] == 0,
                'Incomplete or unexpected observation result')
    idle = reports['idle']['groups']
    require(len(idle) == 1 and idle[0]['new_keys'] == 0 and idle[0]['calls'] == 300,
            'Idle sampling differs')
    groups = {g['new_keys']: g for g in reports['inputs']['groups']}
    require(set(groups) == {0, 4, 256, 512} and all(groups[k]['calls'] == 8 for k in [4, 256, 512]),
            'Expected eight calls for L/R/Select')
    require(inspect((out / 'initial.bin').read_bytes())['raw'] == inspect((out / 'final.bin').read_bytes())['raw']
            and sha(out / 'unchanged.sav') == FIXTURE_SHA, 'Pokemon or SRAM changed')
    result = {'variant': ROMS[sha(rom)], 'execution': execution, **reports,
              'pokemon_and_sram_unchanged': True,
              'scope': 'Inclusive ARM9 interpreter cycles; scheduled VRAM transfer excluded. No FPS claim.'}
    (out / 'verification.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ['rom', 'fixture', 'harness', 'out']:
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--harness-sha256', required=True, help='Hash of the reviewed observation build')
    args = parser.parse_args()
    print(json.dumps(profile(args.rom.resolve(), args.fixture.resolve(), args.harness.resolve(),
                             args.harness_sha256, args.out.resolve())))
