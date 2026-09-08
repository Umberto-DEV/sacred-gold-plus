#!/usr/bin/env python3
"""Check the public file list and patch fingerprints without game files."""
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def check(root=ROOT):
    allowed = set(json.loads((root/'.github/public-files.json').read_text()))
    r = subprocess.run(['git', '-C', str(root), 'rev-parse', '--show-toplevel'], capture_output=True, text=True)
    if r.returncode == 0 and Path(r.stdout.strip()).resolve() == root.resolve():
        actual = set(subprocess.check_output(['git', '-C', str(root), 'ls-files', '-z']).decode().rstrip('\0').split('\0'))
    else:
        actual = {str(p.relative_to(root)) for p in root.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
    if actual != allowed:
        raise ValueError('Unexpected or missing public files; review the public file list')
    bad_text = re.compile(r'/(?:Users|home)/|/private/(?:tmp|var)/|(?:192\.168\.|10\.0\.)\d|\b[A-Za-z0-9._%+-]+@(?:gmail|outlook|icloud|hotmail)\.com\b', re.I)
    for name in sorted(actual):
        p = root/name
        if p.is_symlink() or any(x.is_symlink() for x in p.parents if x != root.parent):
            raise ValueError('Symbolic links are not public artifacts')
        data = p.read_bytes()
        if name == 'sacred-gold-plus-logo.webp':
            if hashlib.sha256(data).hexdigest() != '6e9d416eb4b3c87f5fcb893da6772283eb116988f189b6d25fe25c10342a53d2':
                raise ValueError('Logo differs from the reviewed original')
        elif name.endswith('.xdelta'):
            if data[:4] != bytes([0xD6, 0xC3, 0xC4, 0]):
                raise ValueError('Patch has an unexpected format')
            if data[4] & 4:
                raise ValueError('Patch contains an application header; regenerate with -A')
        else:
            text = data.decode('utf-8')
            if bad_text.search(text):
                raise ValueError('Possible private information: review locally before publication')
    manifest = json.loads((root/'patches/manifest.json').read_text())
    if len(manifest['variants']) != 4:
        raise ValueError('Expected four release variants')
    for row in manifest['variants']:
        data = (root/row['patch']).read_bytes()
        if len(data) != row['patch_bytes'] or hashlib.sha256(data).hexdigest() != row['patch_sha256']:
            raise ValueError('Patch fingerprint differs from the release manifest')
    return len(actual)


if __name__ == '__main__':
    print(f'Public file and patch checks passed: {check()} files')
