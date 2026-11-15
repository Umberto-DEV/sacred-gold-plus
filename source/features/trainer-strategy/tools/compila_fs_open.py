#!/usr/bin/env python3
"""Build the recovered ARM Open wrapper for attribution, never patch a ROM.

Optional original-reference headers verify ARM32 FSFileID by-value layout.
No original SDK compiler or external ARM linker is reconstructed.
"""
from pathlib import Path
import argparse, importlib.util, json, shlex, shutil, subprocess

spec = importlib.util.spec_from_file_location('fs_open_init_builder_parent', Path(__file__).with_name('compila_fs_init.py'))
C = importlib.util.module_from_spec(spec); spec.loader.exec_module(C)
need, sha = C.need, C.sha
PARENT = 'c412b858e85410ce511354bc3e96e78f860783130d53396e12dc746062473e8a'
RECIPE = Path(__file__).resolve().parents[1] / 'sorgenti/fs-open.S'
ADDRESS = 0x20D8278
EXPECTED = '844c19c244efe83b1be9dd83f73da60917d201793d237d72cf0a429ca9158a2d'


def build(out, cc='clang', reference=None):
    need(sha(Path(C.__file__).read_bytes()) == PARENT, 'qualified layout/loader parent drift')
    out = Path(out).resolve()
    need(C.SOURCE not in out.parents and out != C.SOURCE and not out.exists() and not out.is_symlink(),
         'fresh output outside source required')
    compiler = Path(shutil.which(cc) or cc).resolve(); need(compiler.is_file(), 'compiler must exist')
    if reference is not None:
        reference = Path(reference).resolve()
        need(subprocess.check_output(['git', '-C', str(reference), 'rev-parse', 'HEAD'], text=True).strip() == C.PIN and
             not subprocess.check_output(['git', '-C', str(reference), 'status', '--porcelain'], text=True).strip(),
             'clean pinned reference required')
    loader_spec = importlib.util.spec_from_file_location('fs_open_text_loader', C.LOADER)
    loader = importlib.util.module_from_spec(loader_spec); loader_spec.loader.exec_module(loader)
    out.mkdir(parents=True); commands = []

    def run(label, argv):
        result = subprocess.run(argv, capture_output=True, text=True, timeout=30)
        payload = (result.stdout + result.stderr).encode(); (out / (label + '.log')).write_bytes(payload)
        commands.append(dict(label=label, argv=argv, exit_code=result.returncode, log_sha256=sha(payload)))
        result.check_returncode()

    flags = [str(compiler), '--target=armv5te-none-eabi', '-mcpu=arm946e-s', '-marm']
    run('assemble', flags + ['-c', str(RECIPE), '-o', str(out / 'fs-open.o')])
    body, symbols = loader.load_text((out / 'fs-open.o').read_bytes(), ADDRESS, ('native_fs_open_recipe',))
    need(len(body) == 72 and sha(body) == EXPECTED and symbols['native_fs_open_recipe'] == ADDRESS,
         'recovered Open extent/ARM entry/PC-relative calls differ')
    report = dict(schema='native-fs-open-recipe-v1', builder_sha256=sha(Path(__file__).read_bytes()),
        parent_builder_sha256=PARENT, recipe_sha256=sha(RECIPE.read_bytes()), loader_sha256=sha(C.LOADER.read_bytes()),
        compiler_sha256=sha(compiler.read_bytes()),
        compiler_version=subprocess.check_output([str(compiler), '--version'], text=True).splitlines()[0],
        object_sha256=sha((out / 'fs-open.o').read_bytes()), text_bytes=72, text_sha256=sha(body),
        arm_entry=hex(ADDRESS), call_targets=['0x20d8180', '0x20d8208'],
        recipe_is_recovered=True, original_compiler_reconstructed=False)
    if reference is not None:
        layout = C.LAYOUT + '\nCHECK(sizeof(FSFileID)==8);\nCHECK(__builtin_offsetof(FSFileID,arc)==0);\nCHECK(__builtin_offsetof(FSFileID,file_id)==4);\n'
        (out / 'layout.c').write_text(layout)
        run('layout', flags + ['-DSDK_ARM9', '-I', str(reference / 'lib/include'), '-MMD', '-MT', 'fs_open_layout',
            '-MF', str(out / 'layout.d'), '-fsyntax-only', str(out / 'layout.c')])
        dependencies = (out / 'layout.d').read_text().replace('\\\n', ' ')
        need(dependencies.startswith('fs_open_layout:'), 'layout dependency target differs')
        headers = {}
        for name in shlex.split(dependencies.split(':', 1)[1].replace('$$', '$'), comments=False):
            path = Path(name).resolve()
            if path.is_relative_to(reference): headers[str(path.relative_to(reference))] = sha(path.read_bytes())
        need(all('lib/include/nitro/' + name in headers for name in
            ('fs/file.h', 'fs/archive.h', 'types.h', 'os/common/thread_shared.h')), 'layout dependency provenance incomplete')
        source = reference / 'lib/NitroSDK/src/fs/FS_file.c'
        text = source.read_text(); begin = text.index('BOOL FS_OpenFile('); end = text.index('\n}\n', begin) + 3
        report['reference'] = dict(repository='https://github.com/ctrl-cheeb-del/pokeheartgold', pin=C.PIN,
            source_sha256=sha(source.read_bytes()), function_body_sha256=sha(text[begin:end].encode()),
            header_sha256=headers, layout_assertions=layout, layout_passed=True,
            limits='Original headers compiled for layout; C wrapper and native SDK callees not rebuilt.')
    report['commands'] = commands
    (out / 'manifesto.json').write_text(json.dumps(report, indent=2) + '\n')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--uscita', type=Path, required=True)
    parser.add_argument('--cc', default='clang')
    parser.add_argument('--reference', type=Path)
    args = parser.parse_args()
    try: report = build(args.uscita, args.cc, args.reference)
    except (ValueError, subprocess.SubprocessError) as error: parser.exit(2, str(error) + '\n')
    print('Recovered Open ARM recipe verified:', report['text_sha256'])


if __name__ == '__main__': main()
