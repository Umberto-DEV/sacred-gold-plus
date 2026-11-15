#!/usr/bin/env python3
"""Assemble recovered Read core/veneer objects; no SDK rebuild or ROM output."""
from pathlib import Path
import argparse, importlib.util, json, shlex, shutil, subprocess


def load(name, path):
    s = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m


D = load('read_open_builder', Path(__file__).with_name('compila_fs_open.py'))
need, sha, C = D.need, D.sha, D.C
PARENT_SHA = 'e804541b4a4cb44ef0d906424bc2f77fea6cc774b8f9897a27a4315d9dc2fa6b'
RECIPE = Path(__file__).resolve().parents[1] / 'sorgenti/fs-read.S'
BODIES = {
    'core': (0x20D8104, 124, '10e97eb8d4fed727a55cf2ac3f9851ff0abd332b427a67189ad13b5b9d4008ae'),
    'wrapper': (0x20D83CC, 16, '501741a75e11deaadaf8bd6856124771f09fa272502e3fa6752c1340d19c0aa3'),
}


def build(out, cc='clang', reference=None):
    need(sha(Path(D.__file__).read_bytes()) == PARENT_SHA, 'qualified builder drift')
    need(sha(Path(C.__file__).read_bytes()) == D.PARENT, 'qualified layout/loader drift')
    out = Path(out).resolve()
    need(C.SOURCE not in out.parents and out != C.SOURCE and not out.exists() and not out.is_symlink(),
         'fresh output outside source required')
    compiler = Path(shutil.which(cc) or cc).resolve(); need(compiler.is_file(), 'compiler must exist')
    loader = load('read_relocated_text', C.LOADER)
    if reference:
        reference = Path(reference).resolve()
        need(subprocess.check_output(['git', '-C', str(reference), 'rev-parse', 'HEAD'], text=True).strip() == C.PIN
             and not subprocess.check_output(['git', '-C', str(reference), 'status', '--porcelain']),
             'clean pinned reference required')
    out.mkdir(parents=True); commands = []; objects = {}

    def run(label, argv):
        r = subprocess.run(argv, capture_output=True, timeout=30)
        log = r.stdout + r.stderr; (out / (label + '.log')).write_bytes(log)
        commands.append(dict(label=label, argv=argv, exit_code=r.returncode, log_sha256=sha(log)))
        r.check_returncode()

    flags = [str(compiler), '--target=armv5te-none-eabi', '-mcpu=arm946e-s', '-marm']
    for role, (address, length, digest) in BODIES.items():
        path = out / ('fs-read-' + role + '.o'); symbol = 'native_fs_read_' + role + '_recipe'
        run(role, flags + ['-DBUILD_WRAPPER=' + str(int(role == 'wrapper')), '-c', str(RECIPE), '-o', str(path)])
        body, symbols = loader.load_text(path.read_bytes(), address, (symbol,))
        need(len(body) == length and sha(body) == digest and symbols[symbol] == address,
             'recovered Read body identity/entry differs')
        objects[role] = dict(bytes=length, sha256=digest, ram=hex(address), object_sha256=sha(path.read_bytes()))
    report = dict(schema='native-fs-read-recipe-v1', builder_sha256=sha(Path(__file__).read_bytes()),
        parent_builder_sha256=PARENT_SHA, loader_sha256=sha(C.LOADER.read_bytes()),
        recipe_sha256=sha(RECIPE.read_bytes()), compiler_sha256=sha(compiler.read_bytes()),
        compiler_version=subprocess.check_output([str(compiler), '--version'], text=True).splitlines()[0],
        objects=objects, recipe_is_recovered=True, original_compiler_reconstructed=False)
    if reference:
        layout = C.LAYOUT + '\nCHECK(OFF(prop.file.bottom)==40);\nCHECK(OFF(prop.file.pos)==44);\nCHECK(OFF(arg.readfile.dst)==48);\nCHECK(OFF(arg.readfile.len_org)==52);\nCHECK(OFF(arg.readfile.len)==56);\nCHECK(sizeof(FSReadFileInfo)==12);\nCHECK(FS_COMMAND_READFILE==0);\nCHECK(FS_FILE_STATUS_SYNC==4);\n'
        (out / 'layout.c').write_text(layout)
        run('layout', flags + ['-DSDK_ARM9', '-I', str(reference / 'lib/include'), '-MMD', '-MT', 'fs_read_layout',
            '-MF', str(out / 'layout.d'), '-fsyntax-only', str(out / 'layout.c')])
        dependencies = (out / 'layout.d').read_text().replace('\\\n', ' ')
        need(dependencies.startswith('fs_read_layout:'), 'layout dependency target')
        headers = {}
        for name in shlex.split(dependencies.split(':', 1)[1].replace('$$', '$')):
            p = Path(name).resolve()
            if p.is_relative_to(reference): headers[str(p.relative_to(reference))] = sha(p.read_bytes())
        need(all('lib/include/nitro/' + n in headers for n in
             ('fs/file.h', 'fs/archive.h', 'types.h', 'os/common/thread_shared.h')), 'header provenance incomplete')
        source = reference / 'lib/NitroSDK/src/fs/FS_file.c'; text = source.read_text(); functions = {}
        for function in ('FSi_ReadFileCore', 'FS_ReadFile'):
            a = text.index('int ' + function + '('); b = text.index('\n}\n', a) + 3
            functions[function] = sha(text[a:b].encode())
        report['reference'] = dict(repository='https://github.com/ctrl-cheeb-del/pokeheartgold', pin=C.PIN,
            source_sha256=sha(source.read_bytes()), function_body_sha256=functions,
            header_sha256=headers, layout_assertions=layout, layout_passed=True,
            limits='Original headers/layout; recovered assembly only, not original compiler or C binary rebuild.')
    report['commands'] = commands; (out / 'manifesto.json').write_text(json.dumps(report, indent=2) + '\n')
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--uscita', type=Path, required=True); p.add_argument('--cc', default='clang')
    p.add_argument('--reference', type=Path); a = p.parse_args()
    try: build(a.uscita, a.cc, a.reference)
    except (ValueError, subprocess.SubprocessError) as e: p.exit(2, str(e) + '\n')
    print('Recovered Read core124/veneer16 verified')


if __name__ == '__main__': main()
