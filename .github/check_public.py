#!/usr/bin/env python3
"""Check the public file list: no game files, no private data, only our own small blobs."""
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]


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

# Text that would mean a personal path, a personal machine or a private
# workspace leaked into a public file.
PRIVATE_TEXT = re.compile(
    r'/(?:Users|home)/'                                     # a home directory in a path
    r'|<home>'                                              # the same, redacted by hand
    r'|/private/(?:tmp|var)/'                               # a scratch path of one machine
    r'|Desktop/PERSONAL'                                    # the private working folder
    r'|lab/python3'                                         # the old private laboratory tree
    r'|(?:192\.168\.|10\.0\.)\d'                          # an address on someone's network
    r'|\b[A-Za-z0-9._%+-]+@(?:gmail|outlook|icloud|hotmail)\.com\b'
    r'|\bThor\b'                                           # a personal test device
    r'|\bUmberto\b',                                       # a personal name
    re.I)

# Two deliberate exemptions, so the rule above stays strict elsewhere.
# The maintainer's GitHub account is public by definition and is the only
# correct way to write CODEOWNERS and the links to issues and releases.
GITHUB_ACCOUNT = re.compile(r'(?:@|github\.com/)Umberto-DEV\b')
# This file spells the forbidden patterns out, so it cannot scan itself.
SELF = '.github/check_public.py'

# Hidden folders are where a dump or a private workspace hides in plain sight.
# Only these may appear in a tracked path; anything else is refused even if it
# was added to the public file list.
HIDDEN_DIRS_ALLOWED = {'.github'}

# Signatures of game containers. A payload of ours is a few hundred bytes of
# Thumb code or a small table; none of these can legitimately start one.
CONTAINER_MAGICS = (b'NARC', b'BTAF', b'SDAT', b'RGCN', b'RLCN', b'RECN',
                    b'RNAN', b'RCSN', b'BMD0', b'BTX0', b'CRAG')
# The Nintendo logo in an NDS header at 0x0C0, and the constant CRC16 of that
# logo at 0x15C. Either one identifies a cartridge image, header included.
NDS_LOGO_PREFIX = bytes.fromhex('24FFAE51699AA221')
NDS_LOGO_CRC = 0xCF56

# Long unbroken runs of base64 are how a binary travels inside a text file: a
# megabyte of ROM re-encoded as ASCII passes every extension and every decode
# check. Our own text never does this — the longest legitimate run measured in
# the tree is far below the threshold.
B64_ALPHABET = set('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=')
B64_RUN_LIMIT = 1024


def longest_base64_run(text):
    best = run = 0
    for ch in text:
        run = run + 1 if ch in B64_ALPHABET else 0
        if run > best:
            best = run
    return best


def looks_like_game_bytes(data):
    """Is this the beginning of a cartridge image or a game container?"""
    if data[:4] in CONTAINER_MAGICS:
        return 'a game container header (%r)' % data[:4].decode('ascii', 'replace')
    if len(data) >= 0xC8 and data[0xC0:0xC0 + 8] == NDS_LOGO_PREFIX:
        return 'the Nintendo logo of an NDS header at 0x0C0'
    if len(data) >= 0x15E and int.from_bytes(data[0x15C:0x15E], 'little') == NDS_LOGO_CRC:
        return 'the NDS header logo CRC at 0x15C'
    return None


def check(root=ROOT):
    allowed = set(json.loads((root/'.github/public-files.json').read_text()))
    r = subprocess.run(['git', '-C', str(root), 'rev-parse', '--show-toplevel'], capture_output=True, text=True)
    if r.returncode == 0 and Path(r.stdout.strip()).resolve() == root.resolve():
        actual = set(subprocess.check_output(['git', '-C', str(root), 'ls-files', '-z']).decode().rstrip('\0').split('\0'))
    else:
        actual = {str(p.relative_to(root)) for p in root.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
    if actual != allowed:
        raise ValueError('Unexpected or missing public files; review the public file list')
    for name in sorted(actual):
        p = root/name
        if p.is_symlink() or any(x.is_symlink() for x in p.parents if x != root.parent):
            raise ValueError('Symbolic links are not public artifacts')
        basso = name.lower()
        # Anywhere in the name, not only at the end: `rom.nds.txt` used to pass.
        if any(s in basso for s in FORBIDDEN_SUFFIXES):
            raise ValueError('A game file, save or dump must never be tracked: ' + name)
        nascoste = [c for c in Path(name).parts[:-1] if c.startswith('.')]
        if any(c not in HIDDEN_DIRS_ALLOWED for c in nascoste):
            raise ValueError('Undeclared hidden folder in a public path: ' + name)
        data = p.read_bytes()
        if len(data) > SIZE_LIMIT and name not in SIZE_EXCEPTIONS:
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
            if not name.startswith('images/') and not ours:
                raise ValueError('Unexpected binary public file: ' + name) from None
            # Being small and living under source/ was the whole allowance: an
            # 8 KiB slice of a cartridge satisfied it. Now the bytes are read.
            perche = looks_like_game_bytes(data)
            if perche:
                raise ValueError('This binary carries %s: it is game data, not one of our '
                                 'payloads: %s' % (perche, name)) from None
            # Binaries never went through the private-text scan, so a personal
            # path inside a blob was invisible. Latin-1 never fails to decode.
            if PRIVATE_TEXT.search(GITHUB_ACCOUNT.sub('', data.decode('latin-1'))):
                raise ValueError('Possible private information inside a binary: ' + name) from None
            continue
        if name != SELF and PRIVATE_TEXT.search(GITHUB_ACCOUNT.sub('', text)):
            raise ValueError('Possible private information: review locally before publication: ' + name)
        corsa = longest_base64_run(text)
        if corsa > B64_RUN_LIMIT:
            raise ValueError('A %d-character unbroken base64 run: this text file is carrying a '
                             'binary, not text: %s' % (corsa, name))
    return len(actual)


if __name__ == '__main__':
    print(f'Public file contract checks passed: {check()} files')
