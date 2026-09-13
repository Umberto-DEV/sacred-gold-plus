#!/usr/bin/env python3
"""Bounded no-SRAM New Game runner with loaded-code and source identities."""
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[0]
sys.path.insert(0, str(ROOT / 'native-eviv'))
from native_image import require
from run_probe import sha

PREFIX = ('run 600\nrun 60\nrun 1200\ntap A 2 120\n'
          'run 180\ntap A 2 180\n')
OBSERVER_SHA = 'f918f1afb00a1aeff3833d655f5ad078dc680e4ba663ee9c1d7a381c4bed2af1'


def current_build(rom, observer):
    from ndspy.rom import NintendoDSRom
    from thumb_object import load_text
    meta = json.loads((rom.parent / 'build.json').read_text())
    require(meta['kind'] == 'private-native-combined-guide', 'Wrong composition')
    for name, value in meta['source_sha256'].items():
        require(Path(name).name == name and sha(HERE / name) == value,
                'Stale combined source: ' + name)
    require(sha(rom) == meta['rom_sha256'], 'Stale combined ROM')
    require(sha(rom.parent / 'guide.o') == meta['object_sha256'], 'Stale object')
    code, symbols = load_text((rom.parent / 'guide.o').read_bytes(), meta['memory']['code_start'])
    require(hashlib.sha256(code).hexdigest() == meta['payload_sha256']
            and symbols == meta['symbols'], 'Stale payload')
    itcm = NintendoDSRom(rom.read_bytes()).loadArm9().sections[1].data
    require(itcm[0x880:0x880+len(code)] == code and itcm[0x1fc0:0x2000] == bytes(64),
            'ROM code/state differs')
    start = meta['memory']['text_start'] - 0x01ff8000
    require(hashlib.sha256(itcm[start:start+meta['text_bytes']]).hexdigest() == meta['text_sha256'],
            'ROM text differs')
    require(sha(observer) == OBSERVER_SHA, 'Unexpected observer')
    manifest = json.loads((observer.parent / 'observer.json').read_text())
    require(all(sha(Path(p)) == value for p, value in manifest['inputs'].items()),
            'Observer input object changed')
    return meta


def loaded_code(out, name, meta):
    data = (out / (name + '.itcm')).read_bytes()
    require(hashlib.sha256(data[0x620:0x870]).hexdigest() ==
            '6865177a8e819d603bbcfd3bce5c324566780dd01aa4d6793d052a17b57bc1c0', 'Loaded r5 differs')
    require(hashlib.sha256(data[0x880:0x880+meta['payload_bytes']]).hexdigest() ==
            meta['payload_sha256'], 'Loaded combined code differs')
    start = meta['memory']['text_start'] - 0x01ff8000
    require(hashlib.sha256(data[start:start+meta['text_bytes']]).hexdigest() ==
            meta['text_sha256'], 'Loaded combined text differs')
    return struct.unpack_from('<16I', data, 0x1fc0)


def capture(name):
    return (f'capture {name}.ppm\ndump {name}.bin\ndumpitcm {name}.itcm\n'
            f'dumpbus {name}.vram 0x06200000 0x20000\n'
            f'dumpbus {name}.regs 0x04000000 0x1100\n'
            f'dumpbus {name}.pal 0x05000400 0x200\n')


def run_new(rom, observer, out, commands, save=None):
    require(not out.exists(), 'Output directory must be new')
    require(out.resolve().is_relative_to(Path('/private/tmp')), 'Private output required')
    for line in commands.splitlines():
        require(not line.split() or line.split()[0] not in
                ['write', 'freeze', 'load', 'cheat'], 'Normal run may not change RAM or load state')
    inputs = {'rom': sha(rom), 'observer': sha(observer)}
    if save is not None:
        inputs['save'] = sha(save)
    out.mkdir(parents=True)
    script = out / 'commands.script'
    script.write_text(commands)
    command = [str(observer), '--rom', str(rom), '--out', str(out),
               '--script', str(script), '--trace-pc']
    if save is not None:
        command += ['--sram', str(save)]
    record = {'command': command, 'input_sha256': inputs, 'input_save': str(save) if save else None,
              'script_sha256': sha(script), 'runner_sha256': sha(Path(__file__))}
    (out / 'execution.json').write_text(json.dumps(record, indent=2) + '\n')
    with (out / 'runtime.log').open('w') as log:
        result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, timeout=120)
    record['exit_code'] = result.returncode
    require(result.returncode == 0 and 'ERROR ' not in (out / 'runtime.log').read_text(), 'Core failed')
    require(sha(rom) == inputs['rom'] and sha(observer) == inputs['observer'], 'Input changed')
    if save is not None:
        require(sha(save) == inputs['save'], 'Input save changed')
    record['inputs_unchanged'] = True
    (out / 'execution.json').write_text(json.dumps(record, indent=2) + '\n')
    return record
