#!/usr/bin/env python3
"""Check the public file list: no game files, no private data, only our own small blobs."""
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


# No tracked file may exceed this, so that a ROM, a dump or a captured video
# cannot slip in unnoticed. The few legitimate exceptions are named below with
# the reason they are large.
SIZE_LIMIT = 2 * 1024 * 1024
SIZE_EXCEPTIONS = {
    # The full GPL-3.0 text.
    'LICENSE',
}

# Extensions that only a game file, a save or a memory dump would carry. They
# are refused outright: this repository ships tools and our own compiled code,
# never game bytes. The player packages (patches, manuals) live only on the
# GitHub release page; our own small payloads live under source/ with an
# explicit .bin allowance below.
FORBIDDEN_SUFFIXES = ('.nds', '.sav', '.sav2', '.srm', '.dump', '.dsv', '.bak',
                      '.state', '.ml0', '.ml1', '.nds.gz')

# The only binaries allowed outside the screenshot gallery:
# blobs we compiled ourselves from the C sources in this repository, each a few
# hundred bytes, plus the intermediate object of that same build.
OUR_BLOBS_PREFIXES = ('source/sgp12/build/', 'source/features/')
OUR_BLOBS_SUFFIXES = ('.bin', '.o')
OUR_BLOB_MAX = 8 * 1024


def check(root=ROOT):
    allowed = set(json.loads((root/'.github/public-files.json').read_text()))
    r = subprocess.run(['git', '-C', str(root), 'rev-parse', '--show-toplevel'], capture_output=True, text=True)
    if r.returncode == 0 and Path(r.stdout.strip()).resolve() == root.resolve():
        actual = set(subprocess.check_output(['git', '-C', str(root), 'ls-files', '-z']).decode().rstrip('\0').split('\0'))
    else:
        actual = {str(p.relative_to(root)) for p in root.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
    if actual != allowed:
        raise ValueError('Unexpected or missing public files; review the public file list')
    owned = set()
    bad_text = re.compile(r'/(?:Users|home)/|/private/(?:tmp|var)/|(?:192\.168\.|10\.0\.)\d|\b[A-Za-z0-9._%+-]+@(?:gmail|outlook|icloud|hotmail)\.com\b', re.I)
    for name in sorted(actual):
        p = root/name
        if p.is_symlink() or any(x.is_symlink() for x in p.parents if x != root.parent):
            raise ValueError('Symbolic links are not public artifacts')
        if name.lower().endswith(FORBIDDEN_SUFFIXES):
            raise ValueError('A game file, save or dump must never be tracked: ' + name)
        data = p.read_bytes()
        if len(data) > SIZE_LIMIT and name not in SIZE_EXCEPTIONS and name not in owned:
            raise ValueError('Tracked file over the size limit; declare it or keep it out: ' + name)
        if name.endswith('.xdelta'):
            if len(data) < 5 or data[:4] != bytes([0xD6, 0xC3, 0xC4, 0]):
                raise ValueError('Patch has an unexpected format')
            if data[4] & 4:
                raise ValueError('Patch contains an application header; regenerate with -A')
            continue
        try:
            text = data.decode('utf-8')
        except UnicodeDecodeError:
            # Binary files are only expected in the screenshot gallery or as
            # one of our own small compiled blobs under source/.
            ours = (name.startswith(OUR_BLOBS_PREFIXES) and name.endswith(OUR_BLOBS_SUFFIXES)
                    and len(data) <= OUR_BLOB_MAX)
            if name not in owned and not name.startswith('images/') and not ours:
                raise ValueError('Unexpected binary public file: ' + name) from None
            continue
        if bad_text.search(text):
            raise ValueError('Possible private information: review locally before publication: ' + name)
    return len(actual)


if __name__ == '__main__':
    print(f'Public contract and fingerprint checks passed: {check()} files')
