#!/usr/bin/env python3
"""Create a separate local observation frontend; never modify the input core."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
CORE_COMMIT = '906e9ebb27da8c6a715cd7abab4abfe8a8d29427'
CORE_OBSERVATION = {
    'src/ARM.cpp': '7a093181f2f2b5b94b7103a642d19f74bbcfe72787fbe7ad8a5473777cce3eed',
    'src/NDS.cpp': '5781323086ac7231501505daf3896000bd572e0b9057be491aecc9e6c71e6f55',
}


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def prepare(core, out):
    if out.exists():
        raise ValueError('Output directory must be new')
    revision = subprocess.check_output(['git', '-C', str(core), 'rev-parse', 'HEAD'], text=True).strip()
    if revision != CORE_COMMIT or any(sha(core / n) != h for n, h in CORE_OBSERVATION.items()):
        raise ValueError('Requires the exact existing runtime observation core; see runtime/README.md')
    tracked = subprocess.check_output(['git', '-C', str(core), 'ls-files', '-z']).decode().split('\0')
    before = {n: sha(core / n) for n in tracked if n and (core / n).is_file()}
    for n in before:
        src, dst = core / n, out / 'core' / n
        if src.is_symlink():
            raise ValueError('Unexpected source symlink')
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)
    front = out / 'frontend'
    front.mkdir()
    for name in ['main.cpp', 'platform.cpp', 'hg_trace.h', 'CMakeLists.txt']:
        shutil.copyfile(ROOT / 'runtime' / name, front / name)
    shutil.copyfile(Path(__file__).with_name('profile_trace.h'), front / 'profile_trace.h')
    p = out / 'core/src/ARM.cpp'
    s = p.read_text()
    marker = '                u32 icode = (CurInstr >> 6) & 0x3FF;'
    if s.count(marker) != 1:
        raise ValueError('Thumb observation point changed')
    s = s.replace(marker, '''#ifdef HG_RUNTIME_TRACE
                HGProfile::Step(R[15]-4,R[14],R[13],NDS.ARM9Timestamp+Cycles,
                    R[15]-4==0x02088B40?NDS.ARM9Read32(0x021D1154):0);
#endif
''' + marker)
    marker = '                const u32 hgAddress = R[15] - 8;'
    if s.count(marker) != 1:
        raise ValueError('ARM observation point changed')
    s = s.replace(marker, '''                HGProfile::Step(R[15]-8,R[14],R[13],NDS.ARM9Timestamp+Cycles,
                    R[15]-8==0x02088B40?NDS.ARM9Read32(0x021D1154):0);
''' + marker)
    p.write_text(s)
    p = front / 'hg_trace.h'
    p.write_text(p.read_text() + '\n#include "profile_trace.h"\n')
    p = front / 'main.cpp'
    s = p.read_text()
    marker = '        else if(c=="tracepc")'
    if s.count(marker) != 1:
        raise ValueError('Frontend command interface changed')
    s = s.replace(marker, '''        else if(c=="profile") {
            require(2);
            if(t[1]=="reset")HGProfile::Reset();
            else if(t[1]=="on")HGProfile::Enabled=true;
            else if(t[1]=="off")HGProfile::Enabled=false;
            else if(t[1]=="report") {require(3);auto data=HGProfile::Json();writeFile(t[2],data.data(),data.size());}
            else throw std::runtime_error("Unknown profile command");
        }
''' + marker)
    p.write_text(s)
    if any(sha(core / n) != h for n, h in before.items()):
        raise ValueError('Source core changed during preparation')
    result = {'kind': 'private-observation-snapshot', 'core_commit': revision,
              'original_files_unchanged': True, 'copied_files': len(before),
              'instrumented_ARM_cpp_sha256': sha(out / 'core/src/ARM.cpp'),
              'frontend_sha256': {p.name: sha(p) for p in front.iterdir() if p.is_file()},
              'scope': 'ARM9 interpreter instructions; no production patch, ROM or save included'}
    (out / 'preparation.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--core', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.core.resolve(), args.out.resolve())))
