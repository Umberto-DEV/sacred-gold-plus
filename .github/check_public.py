#!/usr/bin/env python3
"""Check the public file list and patch fingerprints without game files."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
CUMULATIVE_BASE = {
    'version': '1.04', 'base': 'Pokemon HeartGold (USA)',
    'base_sha256': '65f02a56842b75aa92d775d56d657a56fe3fa993550b04dc20704ab82d760105',
    'base_bytes': 134217728, 'patch_kind': 'cumulative-from-clean-us',
}
CUMULATIVE_VARIANTS = {
    'it-classic': ('IT', 'Normal Angle', '9dd0c98eb96b91037592bc30574210b191e9f2c2fca45f466733eeb5b9a12d0a', 131840584),
    'it-plus': ('IT', 'New Angle', '217daa45f4945abd3feda6f583f5163db029d1aa361c33c18f12b32ad4eca4a4', 131840584),
    'en-classic': ('US', 'Normal Angle', 'ef0e61bbcad07d732054a19a0b4ee64563bb2d7503ee9fd62348643fcb630760', 127038608),
    'en-plus': ('US', 'New Angle', '3ed4ea0291092d46def2f71454821bbde7832014ec020680468af7bfca686248', 127038608),
}


def validate_cumulative_manifest(manifest):
    """Validate declared identities only; game decoding is a separate local test."""
    if not isinstance(manifest, dict) or any(
            type(manifest.get(key)) is not type(value) or manifest[key] != value
            for key, value in CUMULATIVE_BASE.items()):
        raise ValueError('Unexpected or missing cumulative base contract')
    rows = manifest.get('variants')
    if not isinstance(rows, list) or len(rows) != 4:
        raise ValueError('Expected four cumulative release variants')
    seen = set()
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get('id'), str):
            raise ValueError('Invalid cumulative variant')
        ident = row['id']
        if ident not in CUMULATIVE_VARIANTS or ident in seen:
            raise ValueError('Unexpected or duplicate cumulative variant')
        expected = CUMULATIVE_VARIANTS[ident]
        actual = tuple(row.get(key) for key in ('language', 'camera', 'output_sha256', 'output_bytes'))
        if actual != expected or type(row.get('output_bytes')) is not int:
            raise ValueError('Cumulative variant does not match the reviewed output')
        seen.add(ident)


def check(root=ROOT):
    allowed = set(json.loads((root/'.github/public-files.json').read_text()))
    reviewed_media = json.loads((root/'.github/reviewed-media.json').read_text())
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
        if name in reviewed_media:
            if hashlib.sha256(data).hexdigest() != reviewed_media[name]:
                raise ValueError('Public media differs from the reviewed original')
        elif name == 'sacred-gold-plus-logo.webp':
            if hashlib.sha256(data).hexdigest() != '6e9d416eb4b3c87f5fcb893da6772283eb116988f189b6d25fe25c10342a53d2':
                raise ValueError('Logo differs from the reviewed original')
        elif name.endswith('.xdelta'):
            if len(data) < 5 or data[:4] != bytes([0xD6, 0xC3, 0xC4, 0]):
                raise ValueError('Patch has an unexpected format')
            if data[4] & 4:
                raise ValueError('Patch contains an application header; regenerate with -A')
        else:
            text = data.decode('utf-8')
            if bad_text.search(text):
                raise ValueError('Possible private information: review locally before publication')
    manifest = json.loads((root/'patches/manifest.json').read_text())
    validate_cumulative_manifest(manifest)
    for row in manifest['variants']:
        data = (root/row['patch']).read_bytes()
        if len(data) != row['patch_bytes'] or hashlib.sha256(data).hexdigest() != row['patch_sha256']:
            raise ValueError('Patch fingerprint differs from the release manifest')
    cheats = json.loads((root/'cheats/manifest.json').read_text())['variants']
    variants = {row['id']: row for row in manifest['variants']}
    if set(cheats) != set(variants):
        raise ValueError('Cheat and release variants differ')
    expected_cheats = set()
    for variant, catalog in cheats.items():
        game = variants[variant]
        if catalog['language'] != game['language'] or catalog['rom_sha256'] != game['output_sha256']:
            raise ValueError('Cheats target a different language or game')
        if catalog['count'] != 7 or catalog['enabled_count'] != 0 or {f['format'] for f in catalog['files']} != {'mch', 'xml'} or len(catalog['files']) != 2:
            raise ValueError('Expected seven optional codes in two formats')
        for entry in catalog['files']:
            name = 'cheats/'+entry['path']
            expected_cheats.add(name)
            data = (root/name).read_bytes()
            if len(data) != entry['bytes'] or hashlib.sha256(data).hexdigest() != entry['sha256']:
                raise ValueError('Cheat fingerprint differs from the reviewed manifest')
            if entry['format'] == 'mch':
                codes = re.findall(r'^CODE (\d+) ', data.decode(), re.M)
                if codes != ['0'] * 7 or catalog['rom_sha256'] not in data.decode():
                    raise ValueError('Desktop cheats must be off and match this game')
            else:
                tree = ET.fromstring(data)
                if tree.findtext('game/gameid') != catalog['gameid'] or len(tree.findall('.//cheat')) != 7 or tree.findall('.//enabled'):
                    raise ValueError('Android cheat identity or selection differs')
    if {n for n in actual if n.endswith(('.mch', '.xml'))} != expected_cheats:
        raise ValueError('Unexpected or missing cheat files')
    return len(actual)


if __name__ == '__main__':
    print(f'Public contract and fingerprint checks passed: {check()} files; ROM decoding not run')
