#!/usr/bin/env python3
"""Build reproducible 1.2.5 player ZIPs. No ROM is packaged or downloaded."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import zipfile

HERE = Path(__file__).resolve().parent
STAMP = (2026, 10, 27, 0, 0, 0)


def config():
    return json.loads((HERE / 'release.json').read_text())


def guide_names(lang, cfg):
    version = cfg['version']
    return ([f'Come-installare-{version}-IT.pdf', f'Novita-{version}-IT.pdf']
            if lang == 'IT' else [f'How-to-install-{version}-EN.pdf', f'Whats-New-{version}-EN.pdf'])


def patch_path(source_id):
    """Folders describe the input ROM; the ZIP edition selects the output."""
    parts = source_id.split('-')
    if parts[0] == 'clean':
        folder = 'From Clean ROM/' + parts[1].upper()
    else:
        version = parts[1]
        language = 'IT' if 'it' in parts else 'US'
        folder = f'From Plus {version}/{language}'
        if version == '1.04':
            folder += '/Normal Angle' if parts[-1] == 'classic' else '/New Angle'
        elif version == '1.2.2':
            folder += '/First Edition 2026-09-19' if parts[-1] == 'prima' else '/Second Edition'
    return f'Patch/{folder}/from-{source_id}.xdelta'


def install_text(lang, cfg):
    name = 'COME-INSTALLARE.txt' if lang == 'IT' else 'HOW-TO-INSTALL.txt'
    text = (HERE / 'documents' / lang / name).read_text(encoding='utf-8')
    # Fail packaging if a handwritten guide drifts from the actual routes.
    for source in cfg['sources']:
        if patch_path(source['id']) not in text or source['sha256'] not in text:
            raise ValueError('Installation guide is missing source: ' + source['id'])
    if cfg['targets'][lang]['sha256'] not in text:
        raise ValueError('Installation guide has an outdated output fingerprint')
    return text


def finalize_members(members, manifest):
    members = dict(members)
    members['Patch/manifest.json'] = (json.dumps(manifest, indent=2, ensure_ascii=False) + '\n').encode()
    inventory = {n: {'bytes': len(b), 'sha256': hashlib.sha256(b).hexdigest()}
                 for n, b in sorted(members.items())}
    members['Patch/CONTENTS.json'] = (json.dumps({'version': manifest['version'], 'files': inventory}, indent=2) + '\n').encode()
    root = 'Sacred Gold Plus ' + manifest['version'] + '/'
    return {root + name: data for name, data in members.items()}


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''): h.update(b)
    return h.hexdigest()


def verify_bytes(data, pin):
    if len(data) != pin['bytes'] or hashlib.sha256(data).hexdigest() != pin['sha256']:
        raise ValueError('Content differs from the pinned reference')


def verify_file(path, pin):
    if Path(path).is_symlink() or Path(path).stat().st_size != pin['bytes'] or digest(path) != pin['sha256']:
        raise ValueError('Input differs from the release pin: ' + Path(path).name)


def write_zip(path, members):
    with zipfile.ZipFile(path, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for name, data in sorted(members.items()):
            info = zipfile.ZipInfo(name, STAMP)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            z.writestr(info, data)
    with zipfile.ZipFile(path) as z:
        if len(z.namelist()) != len(members) or set(z.namelist()) != set(members):
            raise ValueError('ZIP member list differs')
        for name, data in members.items():
            if z.read(name) != data: raise ValueError('ZIP read-back failed: ' + name)


def run(args):
    result = subprocess.run([str(x) for x in args], capture_output=True, text=True)
    if result.returncode: raise ValueError(result.stderr[-2000:] or result.stdout[-2000:])
    return result.stdout


def reference_members(lang, reference_dir, guide_dir, cfg):
    install_text(lang, cfg)
    ref = cfg['references'][lang]
    path = reference_dir / ref['name']
    if digest(path) != ref['sha256']: raise ValueError('Reference ZIP hash mismatch')
    with zipfile.ZipFile(path) as z:
        originals = {'Manual/' + n for n in cfg['original_documents']} | {'Manual/Game Guide.txt'}
        members = {n: z.read(n) for n in z.namelist() if n in originals}
        for name, pin in cfg['original_documents'].items(): verify_bytes(members['Manual/'+name], pin)
        for name in z.namelist():
            if name.startswith('Cheats/'):
                members[name.replace('1.2.3', '1.2.5')] = z.read(name).replace(b'1.2.3', b'1.2.5')
        license_name = 'LICENZA.txt' if lang == 'IT' else 'LICENSE.txt'
        members[license_name] = z.read(license_name)
    for p in sorted((HERE/'documents'/lang).rglob('*.txt')):
        relative = p.relative_to(HERE/'documents'/lang)
        # Root text files are authoring sources for the two player-facing PDFs.
        if len(relative.parts) > 1 and 'History' not in relative.parts:
            members[relative.as_posix()] = p.read_bytes()
    for name in guide_names(lang, cfg):
        members[name] = (guide_dir / name).read_bytes()
    return members


def build(inputs, references, guides, output, rpjs, node='node', xdelta='xdelta3'):
    cfg = config()
    if output.exists(): raise FileExistsError('Use a new output directory')
    paths = {k: Path(v) for k,v in json.loads(inputs.read_text()).items()}
    for row in cfg['sources']: verify_file(paths[row['id']], row)
    for lang, row in cfg['targets'].items(): verify_file(paths['target-'+lang], row)
    if run(['git', '-C', rpjs, 'rev-parse', 'HEAD']).strip() != cfg['rompatcher_commit']:
        raise ValueError('Unexpected RomPatcher.js revision')
    if run(['git', '-C', rpjs, 'status', '--porcelain', '--untracked-files=no']).strip():
        raise ValueError('RomPatcher.js checkout is modified')
    # Validate reference documents before allocating any output.
    for lang in cfg['targets']: reference_members(lang, references, guides, cfg)
    output.mkdir(parents=True)
    results = []
    with tempfile.TemporaryDirectory(prefix='sgp-package-', dir=output) as temporary:
        work = Path(temporary)
        for lang, target in cfg['targets'].items():
            members = reference_members(lang, references, guides, cfg)
            rows = []
            for source in cfg['sources']:
                patch = work/'route.xdelta'
                decoded = work/'decoded.nds'
                run([xdelta, '-e', '-A', '-S', 'none', '-D', '-s', paths[source['id']], paths['target-'+lang], patch])
                raw = patch.read_bytes()
                if raw[:5] != bytes.fromhex('d6c3c40000'): raise ValueError('Unexpected VCDIFF header')
                run([xdelta, '-d', '-D', '-R', '-s', paths[source['id']], patch, decoded])
                verify_file(decoded, target); decoded.unlink()
                result = json.loads(run([node, HERE/'verify-rompatcher.cjs', rpjs,
                                          paths[source['id']], patch, source['sha256'], target['sha256'], decoded]))
                verify_file(decoded, target); decoded.unlink()
                if result['result'] != 'PASS' or result['patch_sha256'] != hashlib.sha256(raw).hexdigest():
                    raise ValueError('Independent decoder failed')
                name = patch_path(source['id'])
                members[name] = raw
                rows.append({'file': name, 'source': source, 'bytes':len(raw), 'sha256':hashlib.sha256(raw).hexdigest()})
                patch.unlink()
                print(f'{lang}: {len(rows)}/{len(cfg["sources"])} routes verified', flush=True)
            manifest = {'schema':1, 'version':cfg['version'], 'language':lang,
                        'target':target, 'patches':rows,
                        'decoders':['xdelta3','RomPatcher.js'], 'rompatcher_commit':cfg['rompatcher_commit']}
            members = finalize_members(members, manifest)
            tag = 'US' if lang == 'EN' else 'IT'
            archive = output/f'Sacred-Gold-Plus-1.2.5-{tag}.zip'
            write_zip(archive, members)
            results.append({'file':archive.name,'bytes':archive.stat().st_size,'sha256':digest(archive),
                            'members':len(members),'routes':len(rows)})
    # Detect changed inputs even if a decoder happened to accept them earlier.
    for row in cfg['sources']: verify_file(paths[row['id']], row)
    for lang, row in cfg['targets'].items(): verify_file(paths['target-'+lang], row)
    (output/'SHA256SUMS').write_text(''.join(f'{r["sha256"]}  {r["file"]}\n' for r in results))
    (output/'verification.json').write_text(json.dumps({'version':cfg['version'],'assets':results,
        'scope':'File reconstruction with two decoders; no game runtime or save compatibility test.'},indent=2)+'\n')
    return results


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['inputs','references','guides','output','rompatcher']: p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--node',default='node');p.add_argument('--xdelta',default='xdelta3')
    a=p.parse_args()
    print(json.dumps(build(a.inputs,a.references,a.guides,a.output,a.rompatcher,a.node,a.xdelta),indent=2))
