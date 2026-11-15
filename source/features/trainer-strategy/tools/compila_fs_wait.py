#!/usr/bin/env python3
"""Assemble recovered Wait/IRQ objects; no SDK rebuild or ROM output."""
from pathlib import Path
import argparse, importlib.util, json, shlex, shutil, subprocess


def load(name, path):
    s = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m


D = load('wait_read_builder', Path(__file__).with_name('compila_fs_read.py'))
need, sha, C = D.need, D.sha, D.C
PARENT_SHA = '92b0d052f87f456050fce873f0b0552a33abc42017c00afffa535a1951dc9788'
RECIPE = Path(__file__).resolve().parents[1] / 'sorgenti/fs-wait.S'
BODIES = {
    'core': (0x20D82FC, 192, '74a4b27bab72e380afd92fbdf9cae9b524f24641668dae54a2af802184caf167'),
    'disable': (0x20D3A38, 20, 'a8cdb747f9936730571b220bb9570615892665b120713ffc59b1cb2d7dee76ff'),
    'restore': (0x20D3A4C, 24, '46b5111b6fad094dfff177dca974d33b477cb72772ecfe95b74b1c7f656bc4fd'),
}


def build(out, cc='clang', reference=None):
    need(sha(Path(D.__file__).read_bytes()) == PARENT_SHA, 'qualified builder drift')
    need(sha(Path(C.__file__).read_bytes()) == D.D.PARENT, 'qualified layout/loader drift')
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
        path = out / ('fs-wait-' + role + '.o'); symbol = 'native_fs_wait_' + role + '_recipe'
        run(role, flags + ['-DBUILD_COMPONENT=' + str(('core','disable','restore').index(role)), '-c', str(RECIPE), '-o', str(path)])
        body, symbols = loader.load_text(path.read_bytes(), address, (symbol,))
        need(len(body) == length and sha(body) == digest and symbols[symbol] == address,
             'recovered Read body identity/entry differs')
        objects[role] = dict(bytes=length, sha256=digest, ram=hex(address), object_sha256=sha(path.read_bytes()))
    report = dict(schema='native-fs-wait-recipe-v1', builder_sha256=sha(Path(__file__).read_bytes()),
        parent_builder_sha256=PARENT_SHA, loader_sha256=sha(C.LOADER.read_bytes()),
        recipe_sha256=sha(RECIPE.read_bytes()), compiler_sha256=sha(compiler.read_bytes()),
        compiler_version=subprocess.check_output([str(compiler), '--version'], text=True).splitlines()[0],
        objects=objects, recipe_is_recovered=True, original_compiler_reconstructed=False)
    if reference:
        layout = C.LAYOUT + '#include <nitro/os/system.h>\nCHECK(sizeof(OSIntrMode)==4);\nCHECK(HW_PSR_IRQ_DISABLE==0x80);\nCHECK(HW_PSR_CPU_MODE_MASK==0x1F);\nCHECK(FS_RESULT_SUCCESS==0);\nCHECK(FS_RESULT_FAILURE==1);\nCHECK(FS_COMMAND_READFILE==0);\nCHECK(FS_FILE_STATUS_BUSY==1);\nCHECK(FS_FILE_STATUS_SYNC==4);\nCHECK((FS_FILE_STATUS_CANCEL|FS_FILE_STATUS_BUSY|FS_FILE_STATUS_SYNC|FS_FILE_STATUS_ASYNC|FS_FILE_STATUS_OPERATING)==0x4F);\n'
        (out / 'layout.c').write_text(layout)
        run('layout', flags + ['-DSDK_ARM9', '-I', str(reference / 'lib/include'), '-MMD', '-MT', 'fs_wait_layout',
            '-MF', str(out / 'layout.d'), '-fsyntax-only', str(out / 'layout.c')])
        dependencies = (out / 'layout.d').read_text().replace('\\\n', ' ')
        need(dependencies.startswith('fs_wait_layout:'), 'layout dependency target')
        headers = {}
        for name in shlex.split(dependencies.split(':', 1)[1].replace('$$', '$')):
            p = Path(name).resolve()
            if p.is_relative_to(reference): headers[str(p.relative_to(reference))] = sha(p.read_bytes())
        need(all('lib/include/nitro/' + n in headers for n in
             ('fs/file.h', 'fs/archive.h', 'types.h', 'os/common/thread_shared.h')), 'header provenance incomplete')
        sources = {}
        for rel, functions in (
            ('lib/NitroSDK/src/fs/FS_file.c', ('BOOL FS_WaitAsync(',)),
            ('lib/NitroSDK/src/os/os_system.c', ('asm OSIntrMode OS_DisableInterrupts(', 'asm OSIntrMode OS_RestoreInterrupts(')),
            ('lib/NitroSDK/src/fs/fs_send_command.c', ('int FSi_SendCommand(',)),
            ('lib/NitroSDK/src/fs/FS_command.c', ('void FSi_ReleaseCommand(',))):
            source = reference / rel; text = source.read_text(); bodies = {}
            for function in functions:
                a = text.index(function); b = text.index('\n}\n', a) + 3
                bodies[function] = sha(text[a:b].encode())
            sources[rel] = dict(sha256=sha(source.read_bytes()), function_body_sha256=bodies)
        report['reference'] = dict(repository='https://github.com/ctrl-cheeb-del/pokeheartgold', pin=C.PIN,
            sources=sources, header_sha256=headers, layout_assertions=layout, layout_passed=True,
            limits='Pinned C/inline-asm counterparts and original layouts; no original MW rebuild or complete SDK execution.')
    report['commands'] = commands; (out / 'manifesto.json').write_text(json.dumps(report, indent=2) + '\n')
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--uscita', type=Path, required=True); p.add_argument('--cc', default='clang')
    p.add_argument('--reference', type=Path); a = p.parse_args()
    try: build(a.uscita, a.cc, a.reference)
    except (ValueError, subprocess.SubprocessError) as e: p.exit(2, str(e) + '\n')
    print('Recovered Wait192/Disable20/Restore24 verified')


if __name__ == '__main__': main()
