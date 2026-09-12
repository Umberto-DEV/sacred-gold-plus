#!/usr/bin/env python3
"""Pack the 1.2 downloads from the folders next to this file.

    python3 -B release/1.2/build_zip.py

`IT/` and `EN/` hold exactly what a player gets; `contenuto.json` records the
size and SHA-256 of every one of those files. This script verifies each file
against that record, refuses to run if anything is missing, extra or altered,
and writes `dist/Sacred-Gold-Plus-1.2-IT.zip` and `-EN.zip`.

Nothing here needs a game file, a ROM or any private input, so anyone who
clones this repository can rebuild the downloads and compare them byte for
byte with the published ones. `dist/` is not tracked by git.
"""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

HERE = Path(__file__).resolve().parent
# Fixed timestamp and mode for every member: two runs must give the same bytes.
STAMP = (2026, 9, 12, 0, 0, 0)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read_member(folder, name, expected):
    path = folder/name
    if path.is_symlink() or not path.is_file():
        raise SystemExit(f'missing or unsafe file: {folder.name}/{name}')
    data = path.read_bytes()
    if len(data) != expected['bytes'] or sha(data) != expected['sha256']:
        raise SystemExit(f'{folder.name}/{name} differs from contenuto.json')
    return data


def build(destination=None):
    contents = json.loads((HERE/'contenuto.json').read_text())
    if contents.get('schema') != 1 or contents.get('version') != '1.2':
        raise SystemExit('contenuto.json declares an unexpected contract')
    destination = destination or HERE/'dist'
    destination.mkdir(parents=True, exist_ok=True)
    report = []
    for package in contents['packages']:
        folder = HERE/package['folder']
        declared = package['files']
        present = {str(p.relative_to(folder)) for p in folder.rglob('*') if p.is_file()}
        if present != set(declared):
            missing = sorted(set(declared)-present)
            extra = sorted(present-set(declared))
            raise SystemExit(f'{package["folder"]}: missing {missing}, unexpected {extra}')
        members = {name: read_member(folder, name, declared[name])
                   for name in sorted(declared)}
        archive = destination/package['zip']
        if archive.exists():
            archive.unlink()
        with zipfile.ZipFile(archive, 'x', compression=zipfile.ZIP_DEFLATED,
                             compresslevel=9) as bundle:
            for name, data in members.items():
                info = zipfile.ZipInfo(name, STAMP)
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o100644 << 16
                bundle.writestr(info, data)
        report.append({'zip': package['zip'], 'members': len(members),
                       'bytes': archive.stat().st_size,
                       'sha256': sha(archive.read_bytes()),
                       'game': package['game']['name']})
    print(json.dumps({'directory': str(destination), 'assets': report}, indent=2))
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--destination', type=Path, default=None,
                        help='where to write the ZIPs (default: release/1.2/dist)')
    build(parser.parse_args().destination)
