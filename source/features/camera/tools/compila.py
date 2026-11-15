#!/usr/bin/env python3
"""Rebuild the project's 84-byte camera body; no ROM input or ROM output."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

SOURCE = Path(__file__).resolve().parents[1] / 'sorgenti/camera.S'
LOADER = Path(__file__).resolve().parents[2] / 'anim/tools/carica_text.py'
sys.path.insert(0, str(LOADER.parent))
from carica_text import load_text


def sha(data):
    return hashlib.sha256(data).hexdigest()


def compila(out, layout='r4', cc='clang'):
    bounds = {'base11': (0x023DEB6C,0x023DEB8C),
              'r4': (0x023D8A10,0x023D8A98)}
    start,end = bounds[layout]
    constants = dict(CAM_VALIDATE=0x0203B269, CAM_STATE=0x023DFFFC,
        CAM_EXC=start, CAM_EXC_END=end, CAM_TABLE=0x020F6BE0,
        CAM_STRIDE=24, CAM_WORD_OFF=20, CAM_LSL=14, CAM_LSR=26,
        CAM_PLUS_DEFAULT=11)
    out = Path(out);out.mkdir(parents=True, exist_ok=True)
    inc = ''.join(f'.equ {key}, {value:#x}\n' for key,value in constants.items())
    (out/'indirizzi.inc').write_text(inc)
    compiler = Path(shutil.which(cc) or cc).resolve()
    command = [str(compiler), '--target=armv5te-none-eabi', '-mcpu=arm946e-s',
        '-mthumb', '-Wall', '-Wextra', '-Werror', '-I', str(out),
        '-c', str(SOURCE), '-o', str(out/'camera.o')]
    built = subprocess.run(command, capture_output=True, text=True)
    (out/'compila.log').write_text(built.stdout+built.stderr)
    built.check_returncode()
    blob,symbols = load_text((out/'camera.o').read_bytes(),0x023DEB8C,('cam_hook',))
    if len(blob)!=84 or symbols['cam_hook']!=0x023DEB8D:
        raise ValueError('unexpected camera extent/Thumb entry')
    (out/'camera.bin').write_bytes(blob)
    report = dict(layout=layout, bytes=len(blob), sha256=sha(blob), symbols=symbols,
        source_sha256=sha(SOURCE.read_bytes()), loader_sha256=sha(LOADER.read_bytes()),
        constants=constants, command=command,
        compiler_sha256=sha(compiler.read_bytes()),
        compiler_version=subprocess.check_output([str(compiler),'--version'],text=True).splitlines()[0])
    (out/'manifesto.json').write_text(json.dumps(report,indent=2)+'\n')
    return report


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--uscita',type=Path,required=True)
    ap.add_argument('--layout',choices=('base11','r4'),default='r4')
    ap.add_argument('--cc',default='clang')
    a=ap.parse_args()
    print(json.dumps(compila(a.uscita,a.layout,a.cc),indent=2))


if __name__=='__main__':
    main()
