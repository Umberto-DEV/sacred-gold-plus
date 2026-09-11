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
    'version': '1.1', 'base': 'Pokemon HeartGold (USA)',
    'base_sha256': '65f02a56842b75aa92d775d56d657a56fe3fa993550b04dc20704ab82d760105',
    'base_bytes': 134217728, 'patch_kind': 'cumulative-from-clean-us',
}
# One release per language, camera Plus. Third copy of the variant identities:
# this file is the exported gate and must stay standalone, so it repeats them.
CUMULATIVE_VARIANTS = {
    'it-plus': ('IT', 'Plus', '7b61646c627eb67cd991dbc33d68519edd69395468ea8b326e867fe98e62d077', 131906120),
    'en-plus': ('US', 'Plus', '281c2d68e442479e679d8b7e36566ade614d236151c65c9684bad6985461827d', 127104144),
}
# The camera never forms a name. The US game keeps the EN suffix; its ZIP keeps US.
GAME_STEM = {'IT': 'Sacred Gold Plus 1.1 IT', 'US': 'Sacred Gold Plus 1.1 EN'}
ASSET_NAME = {'IT': 'Sacred-Gold-Plus-1.1-IT.zip', 'US': 'Sacred-Gold-Plus-1.1-US.zip'}


def cheat_names(stem):
    """melonDS pairs the desktop .mch with the game by base name."""
    return {stem+'.mch', stem+' - cheat.xml'}


RECOGNIZED_SOURCES = {
    'clean-us': ('Pokemon HeartGold (USA)', '65f02a56842b75aa92d775d56d657a56fe3fa993550b04dc20704ab82d760105', 134217728),
    'plus-1.01': ('Sacred Gold Plus 1.01 English', 'f19b87321dbe8c8013894afe155d01b8e0cf0cf0951a9ed08cc323373015e4a6', 126978016),
    'plus-1.02': ('Sacred Gold Plus 1.02 English', '020791e06c87cfd7aee9d2d24c2b2d460ac1aea9545f8540375d6c875499a66b', 126976992),
    'plus-1.03': ('Sacred Gold Plus 1.03 English', '78b198fbad961970ef8563587fb2278ee957e6297589a847dbe78f73d12cc0c1', 126979552),
    'plus-1.04-en-plus': ('Sacred Gold Plus 1.04 US New Angle', '3ed4ea0291092d46def2f71454821bbde7832014ec020680468af7bfca686248', 127038608),
    'plus-1.04-en-classic': ('Sacred Gold Plus 1.04 US Normal Angle', 'ef0e61bbcad07d732054a19a0b4ee64563bb2d7503ee9fd62348643fcb630760', 127038608),
    'plus-1.04-it-plus': ('Sacred Gold Plus 1.04 IT New Angle', '217daa45f4945abd3feda6f583f5163db029d1aa361c33c18f12b32ad4eca4a4', 131840584),
    'plus-1.04-it-classic': ('Sacred Gold Plus 1.04 IT Normal Angle', '9dd0c98eb96b91037592bc30574210b191e9f2c2fca45f466733eeb5b9a12d0a', 131840584),
}
INSTALLER_MANUAL_NAMES = {
    'Evolution Changes.pdf', 'Important Item Locations.pdf', 'Pokemon Changes.pdf',
    'Pokemon Locations.pdf', 'Special Event Guide.pdf',
    'SS_SG Trainer Pokemon by @JD48096761.txt', 'Game Guide.txt', 'Project Notes.txt',
}
INSTALLER_VENDOR = {
    'vendor/HashCalculator.js': ('rom-patcher-js/modules/HashCalculator.js', '9d3a437aa3a75706533a44745f0201f773718be276d4e60bc2d7613ec01ab95a', 9027),
    'vendor/BinFile.js': ('rom-patcher-js/modules/BinFile.js', '3856e2f30bb8f105796a0371231a9b2aa37266148ac496711f07fd1e80fef688', 14745),
    'vendor/RomPatcher.format.vcdiff.js': ('rom-patcher-js/modules/RomPatcher.format.vcdiff.js', 'c395b1121a6b1c03f1df7ca68ba2681b007d630b17ddac20bcf6252e5742de1b', 10556),
    'vendor/LICENSE': ('LICENSE', 'a379dd012587a2fbe434ea6fcef30f502f32077738c2bd36e9e20cce621162bb', 1229),
}


def validate_cumulative_manifest(manifest):
    """Validate declared identities only; game decoding is a separate local test."""
    if not isinstance(manifest, dict) or any(
            type(manifest.get(key)) is not type(value) or manifest[key] != value
            for key, value in CUMULATIVE_BASE.items()):
        raise ValueError('Unexpected or missing cumulative base contract')
    rows = manifest.get('variants')
    if not isinstance(rows, list) or len(rows) != len(CUMULATIVE_VARIANTS):
        raise ValueError('Expected two cumulative release variants')
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


def _fingerprint(value, size_key, hash_key):
    return (isinstance(value, dict) and type(value.get(size_key)) is int and
            value[size_key] >= 0 and isinstance(value.get(hash_key), str) and
            re.fullmatch(r'[0-9a-f]{64}', value[hash_key]) is not None)


def validate_recognized_manifest(manifest):
    """Pin supported inputs and routes independently of generated metadata."""
    if (not isinstance(manifest, dict) or
            set(manifest) != {'schema', 'version', 'status', 'patch_kind', 'sources', 'variants'} or
            type(manifest.get('schema')) is not int or manifest['schema'] != 2 or
            manifest.get('version') != '1.1' or manifest.get('status') != 'released' or
            manifest.get('patch_kind') != 'recognized-inputs'):
        raise ValueError('Unexpected recognized-input release contract')
    sources = manifest.get('sources')
    if not isinstance(sources, list) or len(sources) != len(RECOGNIZED_SOURCES):
        raise ValueError('Expected eight recognized sources')
    seen = set()
    for source in sources:
        if (not isinstance(source, dict) or set(source) != {'id', 'label', 'sha256', 'bytes'} or
                not isinstance(source.get('id'), str) or source['id'] not in RECOGNIZED_SOURCES or
                source['id'] in seen or type(source.get('bytes')) is not int or
                tuple(source.get(key) for key in ('label', 'sha256', 'bytes')) != RECOGNIZED_SOURCES[source['id']]):
            raise ValueError('Unknown, altered or duplicate recognized source')
        seen.add(source['id'])
    variants = manifest.get('variants')
    if not isinstance(variants, list) or len(variants) != len(CUMULATIVE_VARIANTS):
        raise ValueError('Expected two recognized-input release variants')
    seen = set()
    for row in variants:
        if (not isinstance(row, dict) or
                set(row) != {'id', 'language', 'camera', 'output_sha256', 'output_bytes',
                             'output_name', 'routes', 'installer', 'asset', 'archive_members'} or
                not isinstance(row.get('id'), str) or row['id'] not in CUMULATIVE_VARIANTS or row['id'] in seen):
            raise ValueError('Unexpected or duplicate recognized-input variant')
        ident = row['id']
        language, camera, output, size = CUMULATIVE_VARIANTS[ident]
        stem = GAME_STEM[language]
        if (tuple(row.get(key) for key in ('language', 'camera', 'output_sha256', 'output_bytes')) !=
                (language, camera, output, size) or type(row.get('output_bytes')) is not int or
                row.get('output_name') != stem+'.nds' or row.get('installer') != 'Install-or-update.html' or
                row.get('asset') != ASSET_NAME[language]):
            raise ValueError('Recognized-input variant differs from reviewed output or download')
        seen.add(ident)
        routes = row.get('routes')
        if not isinstance(routes, list) or len(routes) != len(RECOGNIZED_SOURCES):
            raise ValueError('Expected eight recognized routes per variant')
        route_sources = set()
        for route in routes:
            if (not isinstance(route, dict) or set(route) != {'source_id', 'patch', 'patch_sha256', 'patch_bytes'} or
                    not isinstance(route.get('source_id'), str) or route['source_id'] not in RECOGNIZED_SOURCES or
                    route['source_id'] in route_sources or
                    route.get('patch') != 'patches/from-'+route['source_id']+'-to-'+ident+'.xdelta' or
                    not _fingerprint(route, 'patch_bytes', 'patch_sha256') or route['patch_bytes'] < 5):
                raise ValueError('Unexpected, altered or duplicate recognized route')
            route_sources.add(route['source_id'])
        expected_members = ({'README.txt', 'LICENSE', 'Install-or-update.html'} |
                            {'Cheats/'+name for name in cheat_names(stem)} |
                            {'Manual/'+name for name in INSTALLER_MANUAL_NAMES})
        members = row.get('archive_members')
        if (not isinstance(members, dict) or set(members) != expected_members or
                any(not _fingerprint(record, 'size', 'sha256') or set(record) != {'size', 'sha256'}
                    for record in members.values())):
            raise ValueError('Unexpected archive member contract for recognized-input variant')


def validate_release_manifest(manifest):
    if isinstance(manifest, dict) and manifest.get('patch_kind') == 'recognized-inputs':
        validate_recognized_manifest(manifest)
    else:
        # Retain the previous contract and its diagnostic messages for frozen
        # cumulative exports and their regression tests.
        validate_cumulative_manifest(manifest)


def validate_installer_vendor(root):
    directory = root/'source/installer'
    try:
        manifest = json.loads((directory/'vendor-manifest.json').read_text())
    except (OSError, ValueError):
        raise ValueError('Missing or invalid installer vendor manifest') from None
    if (not isinstance(manifest, dict) or set(manifest) != {'repository', 'commit', 'files'} or
            manifest.get('repository') != 'https://github.com/marcrobledo/RomPatcher.js' or
            manifest.get('commit') != '3183884086825c3a57c72026234debcef1e2240c' or
            not isinstance(manifest.get('files'), list) or len(manifest['files']) != 4):
        raise ValueError('Installer vendor revision differs from reviewed source')
    seen = set()
    for row in manifest['files']:
        if (not isinstance(row, dict) or set(row) != {'path', 'upstream_path', 'sha256', 'bytes'} or
                not isinstance(row.get('path'), str) or row['path'] not in INSTALLER_VENDOR or row['path'] in seen or
                type(row.get('bytes')) is not int or
                tuple(row.get(key) for key in ('upstream_path', 'sha256', 'bytes')) != INSTALLER_VENDOR[row['path']]):
            raise ValueError('Installer vendor file differs from reviewed source')
        path = directory/row['path']
        try:
            content = path.read_bytes()
        except OSError:
            raise ValueError('Missing installer vendor file') from None
        if len(content) != row['bytes'] or hashlib.sha256(content).hexdigest() != row['sha256']:
            raise ValueError('Installer vendor fingerprint differs from reviewed source')
        seen.add(row['path'])
    actual = {str(p.relative_to(directory)) for p in (directory/'vendor').rglob('*') if p.is_file()}
    if actual != seen:
        raise ValueError('Unexpected installer vendor files')


def validate_release_files(root, manifest):
    """Check actual patch files; no patch engine or game code is executed."""
    recognized = manifest.get('patch_kind') == 'recognized-inputs'
    rows = ([route for row in manifest['variants'] for route in row['routes']]
            if recognized else manifest['variants'])
    if recognized:
        actual = {str(p.relative_to(root)) for p in root.rglob('*.xdelta') if p.is_file()}
        if actual != {row['patch'] for row in rows}:
            raise ValueError('Unexpected or missing recognized route patch files')
    for row in rows:
        data = (root/row['patch']).read_bytes()
        if len(data) != row['patch_bytes'] or hashlib.sha256(data).hexdigest() != row['patch_sha256']:
            raise ValueError('Patch fingerprint differs from the release manifest')
        if recognized and data[:5] != bytes.fromhex('d6c3c40000'):
            raise ValueError('Recognized route patch has an unexpected format')
    if recognized:
        validate_installer_vendor(root)


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
    validate_release_manifest(manifest)
    validate_release_files(root, manifest)
    cheats = json.loads((root/'cheats/manifest.json').read_text())['variants']
    variants = {row['id']: row for row in manifest['variants']}
    if set(cheats) != set(variants):
        raise ValueError('Cheat and release variants differ')
    expected_cheats = set()
    for variant, catalog in cheats.items():
        game = variants[variant]
        if catalog['language'] != game['language'] or catalog['rom_sha256'] != game['output_sha256']:
            raise ValueError('Cheats target a different language or game')
        # The code count is a package datum, not a constant, and the two formats no
        # longer carry the same set: the desktop MCH holds the project codes, the
        # Android XML also holds the third-party catalogue. What stays invariant is
        # that nothing is enabled and that both files name this exact game.
        counts = catalog.get('counts')
        if (not isinstance(counts, dict) or set(counts) != {'mch', 'xml'} or
                any(type(value) is not int or value < 1 for value in counts.values()) or
                catalog['enabled_count'] != 0 or
                {f['format'] for f in catalog['files']} != {'mch', 'xml'} or len(catalog['files']) != 2):
            raise ValueError('Expected one MCH and one XML with declared code counts, none enabled')
        for entry in catalog['files']:
            name = 'cheats/'+entry['path']
            expected_cheats.add(name)
            data = (root/name).read_bytes()
            if len(data) != entry['bytes'] or hashlib.sha256(data).hexdigest() != entry['sha256']:
                raise ValueError('Cheat fingerprint differs from the reviewed manifest')
            if entry['format'] == 'mch':
                codes = re.findall(r'^CODE (\d+) ', data.decode(), re.M)
                if codes != ['0'] * counts['mch'] or catalog['rom_sha256'] not in data.decode():
                    raise ValueError('Desktop cheats must be off and match this game')
            else:
                tree = ET.fromstring(data)
                if (tree.findtext('game/gameid') != catalog['gameid'] or
                        len(tree.findall('.//cheat')) != counts['xml'] or tree.findall('.//enabled')):
                    raise ValueError('Android cheat identity or selection differs')
    if {n for n in actual if n.endswith(('.mch', '.xml'))} != expected_cheats:
        raise ValueError('Unexpected or missing cheat files')
    return len(actual)


if __name__ == '__main__':
    print(f'Public contract and fingerprint checks passed: {check()} files; ROM decoding not run')
