#!/usr/bin/env python3
"""Separate read-only bus/ITCM observer over unchanged historical core objects."""
import json
from pathlib import Path
import subprocess
import sys
from prepare_lease_observer import prepare, sha


def build(out):
    base = prepare(out / 'itcm-base')
    src = out / 'itcm-base/main.cpp'
    anchor = 'else if(c=="dumpitcm"){require(2);writeFile(t[1],nds->ARM9.ITCM,sizeof(nds->ARM9.ITCM));}'
    original = src.read_text()
    if original.count(anchor) != 1:
        raise ValueError('ITCM observer anchor differs')
    cpp = out / 'main.cpp'
    cpp.write_text(original.replace(anchor, anchor + '\n'
        '        else if(c=="dumpbus"){require(4);u32 address=n(2),length=n(3);'
        'if((address|length)&1)throw std::runtime_error("Aligned halfword dump required");'
        'std::vector<u16> data(length/2);for(u32 i=0;i<length/2;i++)data[i]=nds->ARM9Read16(address+2*i);'
        'writeFile(t[1],data.data(),length);}'))
    commands = []
    for cmd in base['commands']:
        commands.append([v.replace(str(out / 'itcm-base'), str(out)) for v in cmd])
    for cmd in commands:
        result = subprocess.run(cmd, capture_output=True, text=True)
        with (out / 'compile.log').open('a') as log:
            log.write(result.stdout + result.stderr)
        if result.returncode:
            raise ValueError('Summary observer compile failed')
    if any(sha(Path(p)) != value for p, value in base['inputs'].items()):
        raise ValueError('Historical observer objects changed')
    meta = dict(base, kind='read-only-itcm-and-halfword-bus-observer',
                prepared_source_sha256=sha(cpp), binary_sha256=sha(out / 'hg_runtime'),
                commands=commands,
                change='Physical ITCM plus aligned ARM9Read16 bus snapshots; no game writes or core modifications.')
    (out / 'observer.json').write_text(json.dumps(meta, indent=2) + '\n')
    return meta


if __name__ == '__main__':
    print(json.dumps(build(Path(sys.argv[1]).resolve())))
