#!/usr/bin/env python3
"""Assemble the recovered FS_InitFile recipe; optionally check original headers.

Outputs are attribution artifacts, never a patched ROM. The optional reference
must be a clean checkout of ctrl-cheeb-del/pokeheartgold at the documented pin.
"""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import shutil
import shlex
import subprocess

SOURCE = Path(__file__).resolve().parents[3]
RECIPE = Path(__file__).resolve().parents[1] / 'sorgenti/fs-init.S'
LOADER = SOURCE / 'features/anim/tools/carica_text.py'
PIN = 'cb614ad23449d5852b40321dc409c4143872b35c'
ADDRESS = 0x020D7F98
EXPECTED = '131f15b7db06da746cb03744ffda8f5453b1c6c2fbdf8f0dacab41326e10421f'
LAYOUT = '''#include <nitro/fs/file.h>
#define CHECK(x) _Static_assert((x), #x)
#define OFF(f) __builtin_offsetof(FSFile,f)
CHECK(sizeof(void*)==4); CHECK(sizeof(u32)==4); CHECK(sizeof(BOOL)==4);
CHECK(sizeof(FSCommandType)==4); CHECK(sizeof(FSResult)==4);
CHECK(sizeof(FSFileLink)==8); CHECK(sizeof(OSThreadQueue)==8);
CHECK(sizeof(FSDirPos)==12); CHECK(sizeof(FSFindPathInfo)==24);
CHECK(sizeof(FSFile)==72); CHECK(_Alignof(FSFile)==4);
CHECK(OFF(link)==0); CHECK(OFF(arc)==8); CHECK(OFF(stat)==12);
CHECK(OFF(command)==16); CHECK(OFF(error)==20); CHECK(OFF(queue)==24);
CHECK(OFF(prop)==32); CHECK(OFF(arg)==48);
CHECK(OFF(link.prev)==0); CHECK(OFF(link.next)==4);
CHECK(OFF(queue[0].head)==24); CHECK(OFF(queue[0].tail)==28);
CHECK(__builtin_offsetof(FSFindPathInfo,path)==12);
CHECK(__builtin_offsetof(FSFindPathInfo,find_directory)==16);
CHECK(__builtin_offsetof(FSFindPathInfo,result)==20);
CHECK(sizeof(((FSFile*)0)->prop)==16); CHECK(sizeof(((FSFile*)0)->arg)==24);
CHECK(FS_COMMAND_INVALID==14);
'''


def sha(data):
    return hashlib.sha256(data).hexdigest()


def need(condition, message):
    if not condition:
        raise ValueError(message)


def build(out, cc='clang', reference=None):
    out = Path(out).resolve()
    need(SOURCE not in out.parents and out != SOURCE, 'output must be outside source')
    need(not out.exists() and not out.is_symlink(), 'output must be fresh')
    compiler = Path(shutil.which(cc) or cc).resolve()
    need(compiler.is_file(), 'compiler must exist')
    if reference is not None:
        reference = Path(reference).resolve()
        need(subprocess.check_output(['git', '-C', str(reference), 'rev-parse', 'HEAD'], text=True).strip() == PIN,
             'reference revision differs')
        need(not subprocess.check_output(['git', '-C', str(reference), 'status', '--porcelain'], text=True).strip(),
             'reference checkout must be clean')
    spec = importlib.util.spec_from_file_location('fs_recipe_text_loader', LOADER)
    loader = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loader)
    out.mkdir(parents=True)
    commands = []

    def run(label, argv):
        result = subprocess.run(argv, capture_output=True, text=True, timeout=30)
        log = (result.stdout + result.stderr).encode()
        (out / (label + '.log')).write_bytes(log)
        commands.append(dict(label=label, argv=argv, exit_code=result.returncode, log_sha256=sha(log)))
        result.check_returncode()

    flags = [str(compiler), '--target=armv5te-none-eabi', '-mcpu=arm946e-s', '-marm']
    run('assemble', flags + ['-c', str(RECIPE), '-o', str(out / 'fs-init.o')])
    blob, symbols = loader.load_text((out / 'fs-init.o').read_bytes(), ADDRESS, ('native_fs_init_recipe',))
    need(len(blob) == 40 and sha(blob) == EXPECTED and symbols['native_fs_init_recipe'] == ADDRESS,
         'recovered recipe extent/ARM entry/bytes differ')
    report = dict(schema='native-fs-init-recipe-v1', builder_sha256=sha(Path(__file__).read_bytes()), compiler_sha256=sha(compiler.read_bytes()),
                  compiler_version=subprocess.check_output([str(compiler), '--version'], text=True).splitlines()[0],
                  recipe_sha256=sha(RECIPE.read_bytes()), loader_sha256=sha(LOADER.read_bytes()),
                  object_sha256=sha((out / 'fs-init.o').read_bytes()),
                  text_bytes=len(blob), text_sha256=sha(blob), arm_entry=hex(ADDRESS), symbols=symbols,
                  recipe_is_recovered=True, original_compiler_reconstructed=False)
    if reference is not None:
        header = reference / 'lib/include'
        (out / 'layout.c').write_text(LAYOUT)
        run('layout', flags + ['-DSDK_ARM9', '-I', str(header), '-MMD', '-MT', 'fs_init_layout', '-MF', str(out / 'layout.d'),
                              '-fsyntax-only', str(out / 'layout.c')])
        source = reference / 'lib/NitroSDK/src/fs/FS_file.c'
        text = source.read_text()
        begin = text.index('void FS_InitFile(')
        end = text.index('\n}\n', begin) + 3
        body = text[begin:end]
        (out / 'counterpart.c').write_text('#include <nitro/fs/file.h>\n' + body)
        run('counterpart', flags + ['-DSDK_ARM9', '-I', str(header), '-O2', '-ffreestanding',
            '-fno-unwind-tables', '-fno-asynchronous-unwind-tables', '-c', str(out / 'counterpart.c'),
            '-o', str(out / 'counterpart.o')])
        emitted, _ = loader.load_text((out / 'counterpart.o').read_bytes(), ADDRESS, ('FS_InitFile',))
        deptext = (out / 'layout.d').read_text().replace('\\\n', ' ')
        need(deptext.startswith('fs_init_layout:'), 'unexpected layout dependency target')
        dependencies = shlex.split(deptext.split(':', 1)[1].replace('$$', '$'), comments=False)
        headers = {}
        for name in dependencies:
            path = Path(name).resolve()
            if path.is_relative_to(reference):
                headers[str(path.relative_to(reference))] = sha(path.read_bytes())
        need(all('lib/include/nitro/' + name in headers for name in
                 ('fs/file.h', 'fs/archive.h', 'types.h', 'os/common/thread_shared.h')),
             'layout dependency provenance incomplete')
        report['reference'] = dict(repository='https://github.com/ctrl-cheeb-del/pokeheartgold', pin=PIN,
            source_file='lib/NitroSDK/src/fs/FS_file.c', source_sha256=sha(source.read_bytes()),
            extracted_body_sha256=sha(body.encode()), header_sha256=headers,
            layout_assertions=LAYOUT, layout_passed=True, counterpart_text_bytes=len(emitted),
            counterpart_text_sha256=sha(emitted), counterpart_exact_recipe_match=emitted == blob,
            limits='Layout is compiled ARM32; C code generation is this compiler, not the original SDK build. '
                   'An unequal C emission needs a separate semantic comparison; no equivalence inferred here.')
    report['commands'] = commands
    (out / 'manifesto.json').write_text(json.dumps(report, indent=2) + '\n')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--uscita', type=Path, required=True)
    parser.add_argument('--cc', default='clang')
    parser.add_argument('--reference', type=Path)
    args = parser.parse_args()
    try:
        report = build(args.uscita, args.cc, args.reference)
    except (ValueError, subprocess.SubprocessError) as error:
        parser.exit(2, str(error) + '\n')
    print('Recovered ARM recipe verified:', report['text_sha256'])


if __name__ == '__main__':
    main()
