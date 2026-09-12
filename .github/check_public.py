#!/usr/bin/env python3
"""Check the public file list and the release/1.2 fingerprints; no game files."""
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def _fingerprint(value, size_key, hash_key):
    return (isinstance(value, dict) and type(value.get(size_key)) is int and
            value[size_key] >= 0 and isinstance(value.get(hash_key), str) and
            re.fullmatch(r'[0-9a-f]{64}', value[hash_key]) is not None)


def validate_release_folder(root):
    """Check every downloadable release folder against its own two manifests.

    `release/<version>/contenuto.json` pins the size and SHA-256 of every file a
    download carries, and `release/<version>/<language>/Patch/manifest.json`
    repeats the patch fingerprints for the player. Both must agree with the
    bytes on disk and with each other, and no file may sit in a language folder
    that neither declares. Returns the paths verified here, so the caller knows
    which files it has already accounted for.
    """
    owned = set()
    base = root/'release'
    if not base.is_dir():
        return owned
    for version in sorted(p for p in base.iterdir() if p.is_dir()):
        census = json.loads((version/'contenuto.json').read_text())
        if (not isinstance(census, dict) or census.get('schema') != 1 or
                census.get('version') != version.name or
                not isinstance(census.get('packages'), list) or not census['packages']):
            raise ValueError('Release census declares an unexpected contract')
        for package in census['packages']:
            folder = version/package['folder']
            files = package['files']
            if not isinstance(files, dict) or not files:
                raise ValueError('Release census lists no files')
            present = {str(p.relative_to(folder)) for p in folder.rglob('*') if p.is_file()}
            if present != set(files):
                raise ValueError('Release folder differs from its census')
            for name, pin in sorted(files.items()):
                path = folder/name
                if path.is_symlink():
                    raise ValueError('Symbolic links are not public artifacts')
                data = path.read_bytes()
                if (not _fingerprint(pin, 'bytes', 'sha256') or len(data) != pin['bytes'] or
                        hashlib.sha256(data).hexdigest() != pin['sha256']):
                    raise ValueError('Release file differs from the reviewed census')
                owned.add(str(path.relative_to(root)))
            patches = json.loads((folder/'Patch/manifest.json').read_text())
            if (patches.get('version') != version.name or
                    patches.get('language') != package['language'] or
                    patches['game']['sha256'] != package['game']['sha256'] or
                    patches['game']['bytes'] != package['game']['bytes']):
                raise ValueError('Release patch manifest names another game')
            declared = {row['file'] for row in patches['patches']}
            if declared != {n[len('Patch/'):] for n in files if n.endswith('.xdelta')}:
                raise ValueError('Release patch manifest and folder disagree')
            for row in patches['patches']:
                data = (folder/'Patch'/row['file']).read_bytes()
                if (len(data) != row['bytes'] or
                        hashlib.sha256(data).hexdigest() != row['sha256']):
                    raise ValueError('Release patch fingerprint differs from its manifest')
                if data[:4] != bytes([0xD6, 0xC3, 0xC4, 0]) or data[4] & 4:
                    raise ValueError('Release patch has an unexpected format')
        for name in ('contenuto.json', 'build_zip.py', 'README.md'):
            if (version/name).is_file():
                owned.add(str((version/name).relative_to(root)))
    return owned


def check(root=ROOT):
    allowed = set(json.loads((root/'.github/public-files.json').read_text()))
    r = subprocess.run(['git', '-C', str(root), 'rev-parse', '--show-toplevel'], capture_output=True, text=True)
    if r.returncode == 0 and Path(r.stdout.strip()).resolve() == root.resolve():
        actual = set(subprocess.check_output(['git', '-C', str(root), 'ls-files', '-z']).decode().rstrip('\0').split('\0'))
    else:
        actual = {str(p.relative_to(root)) for p in root.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
    if actual != allowed:
        raise ValueError('Unexpected or missing public files; review the public file list')
    owned = validate_release_folder(root)
    bad_text = re.compile(r'/(?:Users|home)/|/private/(?:tmp|var)/|(?:192\.168\.|10\.0\.)\d|\b[A-Za-z0-9._%+-]+@(?:gmail|outlook|icloud|hotmail)\.com\b', re.I)
    for name in sorted(actual):
        p = root/name
        if p.is_symlink() or any(x.is_symlink() for x in p.parents if x != root.parent):
            raise ValueError('Symbolic links are not public artifacts')
        data = p.read_bytes()
        if name.endswith('.xdelta'):
            if len(data) < 5 or data[:4] != bytes([0xD6, 0xC3, 0xC4, 0]):
                raise ValueError('Patch has an unexpected format')
            if data[4] & 4:
                raise ValueError('Patch contains an application header; regenerate with -A')
            continue
        try:
            text = data.decode('utf-8')
        except UnicodeDecodeError:
            # Binary files are only expected inside a reviewed release folder
            # (pinned by size and SHA-256 above) or the screenshot gallery.
            if name not in owned and not name.startswith('images/'):
                raise ValueError('Unexpected binary public file') from None
            continue
        if bad_text.search(text):
            raise ValueError('Possible private information: review locally before publication')
    return len(actual)


if __name__ == '__main__':
    print(f'Public contract and fingerprint checks passed: {check()} files')
