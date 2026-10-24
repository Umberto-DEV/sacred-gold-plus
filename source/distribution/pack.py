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
STAMP = (2026, 10, 24, 0, 0, 0)


def config():
    return json.loads((HERE / 'release.json').read_text())


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
    ref = cfg['references'][lang]
    path = reference_dir / ref['name']
    if digest(path) != ref['sha256']: raise ValueError('Reference ZIP hash mismatch')
    with zipfile.ZipFile(path) as z:
        members = {n: z.read(n) for n in z.namelist() if n.startswith('Manual/')}
        for name, pin in cfg['original_documents'].items(): verify_bytes(members['Manual/'+name], pin)
        # Original manuals and historical illustrated guides stay byte-identical.
        for name in z.namelist():
            if name.startswith('Cheats/'):
                members[name.replace('1.2.3', '1.2.5')] = z.read(name).replace(b'1.2.3', b'1.2.5')
        license_name = 'LICENZA.txt' if lang == 'IT' else 'LICENSE.txt'
        members[license_name] = z.read(license_name)
        history = 'NOVITA-1.2.3.txt' if lang == 'IT' else 'WHATS-NEW-1.2.3.txt'
        members['Manual/'+history] = z.read(history)
    for p in sorted((HERE/'documents'/lang).rglob('*.txt')):
        members[p.relative_to(HERE/'documents'/lang).as_posix()] = p.read_bytes()
    members[f'Manual/Guide-1.2.5-{lang}.pdf'] = (guide_dir/f'Guide-1.2.5-{lang}.pdf').read_bytes()
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
                name = 'Patch/from-'+source['id']+'.xdelta'
                members[name] = raw
                rows.append({'file': name, 'source': source, 'bytes':len(raw), 'sha256':hashlib.sha256(raw).hexdigest()})
                patch.unlink()
                print(f'{lang}: {len(rows)}/{len(cfg["sources"])} routes verified', flush=True)
            manifest = {'schema':1, 'version':cfg['version'], 'language':lang,
                        'target':target, 'patches':rows,
                        'decoders':['xdelta3','RomPatcher.js'], 'rompatcher_commit':cfg['rompatcher_commit']}
            members['Patch/manifest.json'] = (json.dumps(manifest,indent=2,ensure_ascii=False)+'\n').encode()
            inventory = {n:{'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()} for n,b in sorted(members.items())}
            members['CONTENTS.json'] = (json.dumps({'version':cfg['version'],'files':inventory},indent=2)+'\n').encode()
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
