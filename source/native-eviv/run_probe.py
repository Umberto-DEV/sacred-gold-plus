#!/usr/bin/env python3
"""Replay the bounded native pilot on a private, identified TEST save.

No cheats or RAM writes. Cold boots use normal saves; no state crosses ROMs.
Captures, RAM and saves are private and must not be uploaded or added to Git.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from PIL import Image, ImageChops

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'proofs/cheat-functional'))
from inspect_test_mon import inspect
from native_image import require

HARNESS_SHA = '81e58a86e3d055696d7a661eca9e91e9e23f7a06a1dcd862badd78d4c58877e1'
FIXTURE_SHA = 'aed79449cf3d507873786484dc46800b086fbf614543868f4652e38dc359de8c'
CAPTURES = ['stats', 'EV', 'IV', 'held-EV', 'held-IV', 'restored',
            'page-return', 'touch-return', 'reopened', 'saved']
CHECK_MON = ['initial'] + CAPTURES[:-1] + ['saved', 'outside']


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def snapshot(name):
    return f'capture {name}.ppm\ndump {name}.bin\n'


def script():
    text = (ROOT / 'runtime/inputs/cold-reload.script').read_text()
    text += ('dump initial.bin\ntouch 40 75 2\nrun 240\ntouch 64 30 2\nrun 120\n'
             'touch 184 40 2\nrun 360\ntap RIGHT 2 300\n') + snapshot('stats')
    text += 'tap L 2 120\n' + snapshot('EV')
    text += 'run 600 L\nrun 2 NONE\n' + snapshot('held-EV')
    text += 'tap R 2 120\n' + snapshot('IV')
    text += 'run 600 R\nrun 2 NONE\n' + snapshot('held-IV')
    text += 'tap SELECT 2 120\n' + snapshot('restored')
    text += 'tap L 2 120\ntap RIGHT 2 120\ntap LEFT 2 120\n' + snapshot('page-return')
    text += ('tap R 2 120\ntouch 20 174 2\nrun 240\ncapture info.ppm\n'
             'tap L 2 120\ntap R 2 120\ncapture info-buttons.ppm\n'
             'touch 75 174 2\nrun 240\n') + snapshot('touch-return')
    text += ('tap R 2 120\ntap B 2 180\ntouch 64 30 2\nrun 120\n'
             'touch 184 40 2\nrun 360\ntap RIGHT 2 300\n') + snapshot('reopened')
    text += 'tap B 2 180\ntap B 2 180\n' + snapshot('outside')
    text += ('sram unchanged.sav\ntouch 120 75 2\nrun 600\ntap A 8 600\n'
             'tap A 8 1600\n') + snapshot('saved')
    return text + 'sram normal-SAVE-TEST.sav\nquit\n'


def run(harness, rom, save, out, commands):
    out.mkdir(parents=True, exist_ok=False)
    input_hashes = {n: sha(p) for n, p in [('rom', rom), ('save', save), ('harness', harness)]}
    command_file = out / 'commands.script'
    command_file.write_text(commands)
    command = [str(harness), '--rom', str(rom), '--sram', str(save), '--out', str(out),
               '--script', str(command_file), '--trace-pc']
    with (out / 'runtime.log').open('w') as log:
        result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, timeout=120)
    require(result.returncode == 0 and 'ERROR ' not in (out / 'runtime.log').read_text(),
            'Core failed; inspect private runtime.log')
    require(input_hashes == {n: sha(p) for n, p in [('rom', rom), ('save', save), ('harness', harness)]},
            'Input changed')
    return {'input_sha256': input_hashes, 'script_sha256': sha(command_file),
            'exit_code': result.returncode, 'inputs_unchanged': True}


def same_region(out, a, b, box):
    return ImageChops.difference(Image.open(out / (a + '.ppm')).crop(box),
                                Image.open(out / (b + '.ppm')).crop(box)).getbbox() is None


def probe(build, fixture, harness, out):
    require(not out.exists(), 'Output directory must be new')
    report = json.loads(build.read_text())
    require(report['kind'] == 'private-native-pilot-not-release', 'Not a native pilot build')
    require(Path(report['rom_file']).name == report['rom_file'], 'Unexpected ROM filename')
    rom = build.parent / report['rom_file']
    require(sha(rom) == report['rom_sha256'], 'Pilot ROM hash mismatch')
    require(sha(fixture) == FIXTURE_SHA, 'Wrong EV TEST fixture')
    require(sha(harness) == HARNESS_SHA, 'Unknown core harness')
    execution = run(harness, rom, fixture, out, script())
    initial = inspect((out / 'initial.bin').read_bytes())
    require(initial['EVs_HP_Atk_Def_Spe_SpA_SpD'] == [1, 2, 3, 4, 5, 6], 'Wrong EV values')
    unchanged = {name: inspect((out / (name + '.bin')).read_bytes())['raw'] == initial['raw']
                 for name in CHECK_MON}
    require(all(unchanged.values()), 'Pokemon data changed')
    require(sha(out / 'unchanged.sav') == FIXTURE_SHA, 'UI changed SRAM')
    # Ignore the animated HP gauge and Pokemon sprite. Compare all six number
    # rows and the complete title; the stale-title bug must fail this check.
    regions = [(4, 22, 143, 38), (4, 48, 143, 135), (152, 6, 248, 20)]
    restored = {name: all(same_region(out, 'stats', name, box) for box in regions)
                for name in ['restored', 'page-return', 'touch-return', 'reopened']}
    require(all(restored.values()), 'Normal values/title were not restored')
    held = {name: all(same_region(out, name, 'held-' + name, box) for box in regions)
            for name in ['EV', 'IV']}
    require(all(held.values()), 'Held key changed the displayed mode')
    outside_mode = same_region(out, 'info', 'info-buttons', (0, 6, 143, 188))
    require(outside_mode, 'L/R changed the info page')
    saved = out / 'normal-SAVE-TEST.sav'
    require(sha(saved) != FIXTURE_SHA, 'Normal SAVE did not complete')
    cold_script = (ROOT / 'runtime/inputs/cold-reload.script').read_text()
    cold_script += 'dump cold.bin\nquit\n'
    cold = run(harness, rom, saved, out / 'cold-reload', cold_script)
    require(inspect((out / 'cold-reload/cold.bin').read_bytes())['raw'] == initial['raw'],
            'Pokemon changed after cold boot')
    require(sha(out / 'cold-reload/reloaded.sav') == sha(saved), 'SRAM cold roundtrip differs')
    result = {'kind': 'native-eviv-real-core-probe', 'build_sha256': sha(build),
              'language': report['language'], 'execution': execution, 'cold_execution': cold,
              'pokemon': {k: v for k, v in initial.items() if k != 'raw'},
              'pokemon_unchanged': unchanged, 'normal_regions_restored': restored,
              'held_regions_unchanged': held, 'info_page_unaffected': outside_mode,
              'sram_before_save_unchanged': True, 'normal_save_sha256': sha(saved),
              'cold_save_roundtrip': True, 'cold_pokemon_unchanged': True,
              'config': 'Core 906e9ebb, interpreter, software 1x, FreeBIOS, fixed RTC, no cheats',
              'visual_review': 'pending',
              'limits': ['One TEST Chikorita slot, no eggs/box/party changes.',
                         'No GUI, audio, Android or performance claim.']}
    (out / 'verification.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ['build', 'fixture', 'harness', 'out']:
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(probe(*(getattr(args, n).resolve() for n in ['build', 'fixture', 'harness', 'out']))))
