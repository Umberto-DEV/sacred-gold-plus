#!/usr/bin/env python3
"""Compila il gancio Squadra: codice Thumb e canarino, nessun asset di gioco."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
sys.path.insert(0, str(REPO / 'source/features/anim/tools'))
from carica_text import load_text


HOOKS = [{'overlay': 8, 'sito': '0x221d3de', 'pre': '55f6a5ff', 'bersaglio': 'sgp_squadra_pp_hook'}, {'overlay': 8, 'sito': '0x221d3e8', 'pre': '55f694ff', 'bersaglio': 'sgp_squadra_attr_hook'}, {'overlay': 8, 'sito': '0x221d3f2', 'pre': '55f68fff', 'bersaglio': 'sgp_squadra_attr_hook'}, {'overlay': 8, 'sito': '0x221d3fc', 'pre': '55f68aff', 'bersaglio': 'sgp_squadra_attr_hook'}, {'overlay': 8, 'sito': '0x221d406', 'pre': '55f685ff', 'bersaglio': 'sgp_squadra_attr_hook'}]

def sha(data):
    return hashlib.sha256(data).hexdigest()


def compila(out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    source = HERE.parent / 'sorgenti/squadra_cache.c'
    flags = ['--target=armv5te-none-eabi', '-mcpu=arm946e-s', '-mthumb', '-Oz',
             '-ffreestanding', '-fno-builtin', '-fno-stack-protector',
             '-fno-unwind-tables', '-fno-asynchronous-unwind-tables',
             '-fno-jump-tables', '-Wall', '-Wextra', '-Werror']
    with tempfile.TemporaryDirectory(prefix='sgp-squadra-compile-') as temp:
        obj = Path(temp) / 'squadra_cache.o'
        subprocess.run(['clang', *flags, '-c', str(source), '-o', str(obj)], check=True)
        blob, symbols = load_text(obj.read_bytes(), 0x023DBE00,
                                  ('sgp_squadra_attr_cache', 'sgp_squadra_attr_hook', 'sgp_squadra_pp_cache', 'sgp_squadra_pp_hook'))
    if len(blob) > 240:
        raise ValueError('codice oltre il canarino a +0xF0')
    canary = b''.join((0xCA5A1A00 | i).to_bytes(4, 'little') for i in range(4))
    (out / 'blob.bin').write_bytes(blob)
    (out / 'canarino.bin').write_bytes(canary)
    manifest = {
        'schema': 1, 'base': '0x023dbe00', 'blocco_byte': 256,
        'canarino_offset': 240,
        'blob': {'byte': len(blob), 'sha256': sha(blob)},
        'canarino': {'byte': len(canary), 'sha256': sha(canary)},
        'simboli': {k: hex(symbols[k]) for k in ('sgp_squadra_attr_cache', 'sgp_squadra_attr_hook', 'sgp_squadra_pp_cache', 'sgp_squadra_pp_hook')},
        'ganci': HOOKS,
        'compilatore': subprocess.check_output(['clang', '--version'], text=True).splitlines()[0],
        'opzioni_compilazione': flags,
    }
    (out / 'manifesto.json').write_text(json.dumps(manifest, indent=2) + '\n')
    sources = [source, Path(__file__).resolve()]
    origin = {'metodo': 'compilazione da sorgenti; nessuna estrazione ROM',
              'sorgenti': {str(p.relative_to(REPO)): sha(p.read_bytes()) for p in sources}}
    (out / 'origine.json').write_text(json.dumps(origin, indent=2) + '\n')
    names = ['blob.bin', 'canarino.bin', 'manifesto.json', 'origine.json']
    (out / 'SHA256SUMS').write_text(''.join(sha((out / n).read_bytes()) + '  ' + n + '\n' for n in names))
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--uscita', required=True)
    args = parser.parse_args()
    print(json.dumps(compila(args.uscita), indent=2))
