#!/usr/bin/env python3
"""Build a separate read-only ITCM observer; never edit the historical frontend/core."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def prepare(out):
    if out.exists():
        raise ValueError('Output directory must be new')
    source = ROOT / 'runtime/main.cpp'
    if sha(source) != 'ff94c480fbf56ab60749ff1d2dcf2b409224ecdcae2123d71c5165ec43d34552':
        raise ValueError('Unknown frontend source')
    build = ROOT / '<build directory>'
    core = ROOT / '<melonDS checkout>/src'
    anchor = 'else if(c=="dump"){require(2);writeFile(t[1],nds->MainRAM,0x400000);}'
    original = source.read_text()
    if original.count(anchor) != 1:
        raise ValueError('Observer anchor differs')
    edited = original.replace(anchor, anchor + '\n        else if(c=="dumpitcm"){require(2);writeFile(t[1],nds->ARM9.ITCM,sizeof(nds->ARM9.ITCM));}')
    out.mkdir(parents=True)
    cpp = out / 'main.cpp'
    cpp.write_text(edited)
    obj = out / 'main.o'
    command = ['/usr/bin/c++', '-O3', '-DNDEBUG', '-std=gnu++17', '-arch', 'arm64', '-fwrapv',
               '-I'+str(core), '-I'+str(build/'melonds/src'), '-I'+str(source.parent), '-c', str(cpp), '-o', str(obj)]
    link_inputs = [build/'CMakeFiles/hg_runtime.dir/platform.cpp.o', build/'melonds/src/libcore.a',
                   build/'melonds/src/teakra/src/libteakra.a']
    link = ['/usr/bin/c++', '-O3', '-DNDEBUG', '-arch', 'arm64', str(obj),
            *map(str, link_inputs), '-o', str(out/'hg_runtime')]
    logs = ''
    for cmd in [command, link]:
        result = subprocess.run(cmd, capture_output=True, text=True)
        logs += result.stdout + result.stderr
        (out/'compile.log').write_text(logs)
        if result.returncode:
            raise ValueError('Observer compile failed')
    meta = {'kind':'read-only-itcm-observer', 'original_source_sha256':sha(source),
            'prepared_source_sha256':sha(cpp), 'binary_sha256':sha(out/'hg_runtime'),
            'inputs':{str(p):sha(p) for p in link_inputs}, 'commands':[command,link],
            'change':'One dumpitcm command copies the physical 32768-byte ARM9.ITCM array; no timing or CPU changes.'}
    (out/'observer.json').write_text(json.dumps(meta,indent=2)+'\n')
    return meta

if __name__ == '__main__':
    print(json.dumps(prepare(Path(sys.argv[1]).resolve())))
