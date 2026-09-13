#!/usr/bin/env python3
"""Private cold-boot screen oracle for the native Summary guide."""
import json
from pathlib import Path
import struct
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[0]
sys.path.insert(0, str(ROOT / 'native-eviv'))
from run_probe import run, sha, same_region, require
from run_box_probe import open_summary


def current_build(rom, observer):
    from thumb_object import load_text
    from ndspy.rom import NintendoDSRom
    import hashlib
    meta = json.loads((rom.parent / 'build.json').read_text())
    require(meta['kind'] == 'private-native-summary-guide', 'Wrong build kind')
    for name, value in meta['source_sha256'].items():
        require(Path(name).name == name and sha(HERE / name) == value, 'Stale source: ' + name)
    require(sha(rom) == meta['rom_sha256'], 'Stale ROM')
    obj = rom.parent / 'guide.o'
    require(sha(obj) == meta['object_sha256'], 'Stale object')
    code, symbols = load_text(obj.read_bytes(), meta['memory']['code_start'])
    require(hashlib.sha256(code).hexdigest() == meta['payload_sha256'] and symbols == meta['symbols'], 'Stale payload')
    itcm = NintendoDSRom(rom.read_bytes()).loadArm9().sections[1].data
    require(itcm[0x880:0x880+len(code)] == code and itcm[0x1fc0:0x2000] == bytes(64), 'ROM code/state differs')
    require(hashlib.sha256(itcm[0x1b00:0x1b00+meta['text_bytes']]).hexdigest() == meta['text_sha256'], 'ROM text differs')
    obs = json.loads((observer.parent / 'observer.json').read_text())
    require(sha(observer) == obs['binary_sha256'], 'Observer differs')
    require(all(sha(Path(p)) == value for p, value in obs['inputs'].items()), 'Observer input object changed')
    return meta


def loaded_code(out, name, meta):
    import hashlib
    data = (out / (name + '.itcm')).read_bytes()
    require(hashlib.sha256(data[0x620:0x870]).hexdigest() == '6865177a8e819d603bbcfd3bce5c324566780dd01aa4d6793d052a17b57bc1c0', 'Loaded r5 differs')
    require(hashlib.sha256(data[0x880:0x880+meta['payload_bytes']]).hexdigest() == meta['payload_sha256'], 'Loaded guide code differs')
    require(hashlib.sha256(data[0x1b00:0x1b00+meta['text_bytes']]).hexdigest() == meta['text_sha256'], 'Loaded guide text differs')
    return struct.unpack_from('<16I', data, 0x1fc0)


def enter(kind):
    if kind == 'box':
        return open_summary()
    return ((ROOT / 'runtime/inputs/cold-reload.script').read_text()
            + 'touch 40 75 2\nrun 240\ntouch 64 30 2\nrun 120\n'
              'touch 184 40 2\nrun 360\ntap RIGHT 2 300\n')


def capture(name):
    return f'capture {name}.ppm\ndump {name}.bin\ndumpitcm {name}.itcm\n'


def video(name):
    return (capture(name) + f'dumpbus {name}.vram 0x06210000 32768\n'
            f'dumpbus {name}.map 0x0620f800 2048\ndumpbus {name}.regs 0x04001000 96\n')


def screen_oracle(out):
    require(not same_region(out, 'before', 'panel1', (0, 192, 256, 384)),
            'Physical START did not display a native guide panel')
    data = (out / 'panel1.itcm').read_bytes()
    require(struct.unpack_from('<I', data, 0x1fc0)[0] == 0x47554931,
            'No game-executed native guide state')


def return_graphics(out, before, clean):
    # Original move-type icons use native OAM. They must be visible even while
    # the closing B press remains held and input dispatch is still latched.
    for rect in [(8, 199, 44, 211), (8, 231, 44, 243)]:
        require(same_region(out, before, clean, rect),
                'Native move-type sprites missing during the release latch')


def red(rom, fixture, observer, out, kind):
    execution = run(observer, rom, fixture, out,
                    enter(kind) + capture('before') + 'tap START 2 60\n'
                    + capture('panel1') + 'sram unchanged.sav\nquit\n')
    result = {'kind': kind, 'execution': execution, 'runner_sha256': sha(Path(__file__))}
    try:
        screen_oracle(out)
    except ValueError as exc:
        result['failure'] = str(exc)
        result['sram_unchanged'] = sha(fixture) == sha(out / 'unchanged.sav')
        (out / 'verification.json').write_text(json.dumps(result, indent=2) + '\n')
        return result
    raise ValueError('Unchanged r5 unexpectedly provides the guide')
