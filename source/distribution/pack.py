#!/usr/bin/env python3
"""Build versioned player ZIPs. No ROM is packaged or downloaded."""
import argparse
from contextlib import contextmanager
import hashlib
import io
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import tempfile
import unicodedata
import zipfile

HERE = Path(__file__).resolve().parent
IMAGES = HERE.parents[1] / 'images'
STAMP = (2026, 10, 27, 0, 0, 0)
MAX_REFERENCE_ZIP_BYTES = 256 * 1024 * 1024
MAX_REFERENCE_MEMBER_BYTES = 8 * 1024 * 1024
MAX_REFERENCE_TOTAL_BYTES = 32 * 1024 * 1024


def path_token(value):
    if not isinstance(value, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]*', value):
        raise ValueError('Invalid release path token')
    return value


def member_names(names):
    """Reject portable extraction aliases before dictionary insertion or output."""
    entries = {}
    devices = {'CON', 'PRN', 'AUX', 'NUL',
               *('COM' + str(n) for n in range(1, 10)),
               *('LPT' + str(n) for n in range(1, 10)),
               *('COM' + n for n in '¹²³'), *('LPT' + n for n in '¹²³')}
    for name in names:
        if not isinstance(name, str) or not name or '\\' in name:
            raise ValueError('Unsafe archive member name')
        directory = name.endswith('/')
        parts = name[:-1].split('/') if directory else name.split('/')
        for part in parts:
            if (not part or part in ('.', '..') or part.endswith(('.', ' '))
                    or any(ord(c) < 32 or c in '<>:"|?*' for c in part)
                    or part.split('.')[0].rstrip(' ').upper() in devices):
                raise ValueError('Unsafe archive member name: ' + repr(name))
        key = unicodedata.normalize('NFC', '/'.join(parts)).casefold()
        if key in entries:
            raise ValueError('Archive member collision: ' + repr(name))
        entries[key] = directory
    for key in entries:
        parts = key.split('/')
        for count in range(1, len(parts)):
            parent = '/'.join(parts[:count])
            if parent in entries and not entries[parent]:
                raise ValueError('Archive file/directory collision: ' + key)


def add_member(members, name, data, *, authored_override=False):
    # Only the project's explicit document overlay may replace the exact
    # inherited name. Aliases and duplicates within an archive remain errors.
    names = [key for key in members if not (authored_override and key == name)]
    member_names([*names, name])
    members[name] = data


def config(path=None):
    cfg = json.loads(Path(path or HERE / 'release-1.3.1.json').read_text())
    path_token(cfg['version'])
    ids = [path_token(row['id']) for row in cfg['sources']]
    if len(ids) != len(set(ids)):
        raise ValueError('Duplicate release source ID')
    if cfg.get('cheats_policy', 'inherit-reference') not in ('inherit-reference', 'omit-unverified'):
        raise ValueError('Unknown cheats policy')
    documents_dir(cfg)
    for name in cfg.get('title_images', {}).values():
        image_file_bytes(name)
    for language in cfg.get('feature_images', {}).values():
        for pictures in language.values():
            for name, _caption in pictures:
                image_file_bytes(name)
    return cfg


def documents_dir(cfg):
    relative = Path(cfg.get('documents', 'documents'))
    if relative.is_absolute() or '..' in relative.parts or relative.parts[0] != 'documents':
        raise ValueError('Documents must remain inside the distribution documents directory')
    external = os.environ.get('SGP_PLAYER_DOCUMENTS_DIR')
    if external:
        root = Path(external)
        if not root.is_absolute():
            raise ValueError('SGP_PLAYER_DOCUMENTS_DIR must be an absolute path')
        return root
    return HERE / relative


def document_text(lang, name, cfg):
    """Read public English or explicitly supplied private localization sources."""
    if lang not in ('EN', 'IT'):
        raise ValueError('Unsupported player document language')
    try:
        with guide_directory_descriptor(documents_dir(cfg) / lang) as descriptor:
            return guide_file_bytes(descriptor, name).decode('utf-8')
    except ValueError as exc:
        raise ValueError('Player document unavailable: supply a complete private '
                         'bundle with SGP_PLAYER_DOCUMENTS_DIR. ' + str(exc)) from exc


def guide_names(lang, cfg):
    version = path_token(cfg['version'])
    return ([f'Come-installare-{version}-IT.pdf', f'Novita-{version}-IT.pdf']
            if lang == 'IT' else [f'How-to-install-{version}-EN.pdf', f'Whats-New-{version}-EN.pdf'])


def patch_path(source_id):
    """Folders describe the input ROM; the ZIP edition selects the output."""
    parts = path_token(source_id).split('-')
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
    text = document_text(lang, name, cfg)
    # Fail packaging if a handwritten guide drifts from the actual routes.
    for source in cfg['sources']:
        if patch_path(source['id']) not in text or source['sha256'] not in text:
            raise ValueError('Installation guide is missing source: ' + source['id'])
    if cfg['targets'][lang]['sha256'] not in text:
        raise ValueError('Installation guide has an outdated output fingerprint')
    return text


def authored_notices(lang, cfg):
    names = {
        'EN': ('Cheats/ABOUT-CHEATS.txt', 'Manual/ABOUT-THESE-GUIDES.txt'),
        'IT': ('Cheats/LEGGIMI-CHEAT.txt', 'Manual/LEGGIMI-MANUALI.txt'),
    }
    if lang not in names:
        raise ValueError('Unsupported player document language')
    result = {}
    for name in names[lang]:
        relative = Path(name)
        try:
            with guide_directory_descriptor(documents_dir(cfg) / lang / relative.parent) as descriptor:
                result[name] = guide_file_bytes(descriptor, relative.name)
        except ValueError as exc:
            raise ValueError('Required player notice unavailable: supply a complete '
                             'SGP_PLAYER_DOCUMENTS_DIR bundle. ' + str(exc)) from exc
    return result


def finalize_members(members, manifest):
    members = dict(members)
    path_token(manifest['version'])
    member_names(members)
    add_member(members, 'Patch/manifest.json', (json.dumps(manifest, indent=2, ensure_ascii=False) + '\n').encode())
    inventory = {n: {'bytes': len(b), 'sha256': hashlib.sha256(b).hexdigest()}
                 for n, b in sorted(members.items())}
    add_member(members, 'Patch/CONTENTS.json', (json.dumps({'version': manifest['version'], 'files': inventory}, indent=2) + '\n').encode())
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


def pinned_reference_bytes(path, pin):
    path = Path(path)
    flags = os.O_RDONLY
    if hasattr(os, 'O_CLOEXEC'):
        flags |= os.O_CLOEXEC
    if hasattr(os, 'O_NOFOLLOW'):
        flags |= os.O_NOFOLLOW
    elif path.is_symlink():
        raise ValueError('Reference ZIP must be a regular non-symlink file')
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise ValueError('Reference ZIP must be a regular non-symlink file') from exc
    try:
        info = os.fstat(descriptor)
        if not stat.S_ISREG(info.st_mode):
            raise ValueError('Reference ZIP must be a regular non-symlink file')
        if info.st_size > MAX_REFERENCE_ZIP_BYTES:
            raise ValueError('Reference ZIP exceeds the byte limit')
        chunks = []
        total = 0
        while True:
            chunk = os.read(descriptor, min(1 << 20, MAX_REFERENCE_ZIP_BYTES + 1 - total))
            if not chunk:
                break
            chunks.append(chunk)
            total += len(chunk)
            if total > MAX_REFERENCE_ZIP_BYTES:
                raise ValueError('Reference ZIP exceeds the byte limit')
    finally:
        os.close(descriptor)
    data = b''.join(chunks)
    if hashlib.sha256(data).hexdigest() != pin['sha256']:
        raise ValueError('Reference ZIP hash mismatch')
    return data


@contextmanager
def guide_directory_descriptor(path):
    """Open every directory component without following links; retain the final inode."""
    nofollow = getattr(os, 'O_NOFOLLOW', 0)
    directory = getattr(os, 'O_DIRECTORY', 0)
    if not nofollow or not directory or os.open not in os.supports_dir_fd:
        raise ValueError('Guide directory no-follow checks are unavailable on this platform')
    flags = os.O_RDONLY | nofollow | directory
    if hasattr(os, 'O_CLOEXEC'):
        flags |= os.O_CLOEXEC
    absolute = Path(path).absolute()
    components = list(absolute.parts[1:])
    current = Path(os.sep)
    try:
        canonical = []
        index = 0
        while index < len(components):
            component = components[index]
            current /= component
            info = os.lstat(current)
            if stat.S_ISLNK(info.st_mode):
                parent = os.stat(current.parent, follow_symlinks=False)
                if (info.st_uid != 0 or parent.st_uid != 0
                        or stat.S_IMODE(parent.st_mode) & 0o022):
                    raise ValueError('Guide directory must contain no user-controlled symlinks')
                # Resolve only this immutable, root-owned system alias (for
                # example macOS /var -> private/var). Never resolve the later
                # user-controlled suffix, which would reopen a swap race.
                target = current.resolve(strict=True)
                canonical = list(target.parts[1:])
                current = target
            else:
                canonical.append(component)
            index += 1
        absolute = Path(os.sep).joinpath(*canonical)
    except OSError as exc:
        raise ValueError('Guide directory must contain no symlinks') from exc
    descriptor = None
    try:
        descriptor = os.open(os.sep, flags)
        for component in absolute.parts[1:]:
            next_descriptor = os.open(component, flags, dir_fd=descriptor)
            os.close(descriptor)
            descriptor = next_descriptor
        if not stat.S_ISDIR(os.fstat(descriptor).st_mode):
            raise ValueError('Guide directory must be a regular directory')
        yield descriptor
    except OSError as exc:
        raise ValueError('Guide directory must contain no symlinks') from exc
    finally:
        if descriptor is not None:
            os.close(descriptor)


def guide_file_bytes(directory_descriptor, name):
    """Read one fixed guide basename from the retained directory, no links or devices."""
    if Path(name).name != name:
        raise ValueError('Guide input name must be a basename')
    flags = (os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0)
             | getattr(os, 'O_NONBLOCK', 0))
    if hasattr(os, 'O_CLOEXEC'):
        flags |= os.O_CLOEXEC
    try:
        descriptor = os.open(name, flags, dir_fd=directory_descriptor)
    except OSError as exc:
        raise ValueError('Guide input must be a regular non-symlink file: ' + name) from exc
    try:
        if not stat.S_ISREG(os.fstat(descriptor).st_mode):
            raise ValueError('Guide input must be a regular non-symlink file: ' + name)
        chunks = []
        while True:
            chunk = os.read(descriptor, 1 << 20)
            if not chunk:
                return b''.join(chunks)
            chunks.append(chunk)
    finally:
        os.close(descriptor)


def image_path_parts(name):
    """Return a portable relative image path without aliases or traversal."""
    if (not isinstance(name, str) or not name or name.startswith('/')
            or '\\' in name or ':' in name):
        raise ValueError('Image path must be a portable relative path')
    parts = name.split('/')
    if any(not part or part in ('.', '..') or any(ord(c) < 32 for c in part)
           for part in parts):
        raise ValueError('Image path must be a portable relative path')
    return parts


def image_file_bytes(name):
    """Read an image below the fixed root without following any component link."""
    parts = image_path_parts(name)
    nofollow = getattr(os, 'O_NOFOLLOW', 0)
    directory = getattr(os, 'O_DIRECTORY', 0)
    if not nofollow or not directory or os.open not in os.supports_dir_fd:
        raise ValueError('Image no-follow checks are unavailable on this platform')
    directory_flags = os.O_RDONLY | nofollow | directory
    file_flags = os.O_RDONLY | nofollow
    if hasattr(os, 'O_CLOEXEC'):
        directory_flags |= os.O_CLOEXEC
        file_flags |= os.O_CLOEXEC
    with guide_directory_descriptor(IMAGES) as root_descriptor:
        descriptor = os.dup(root_descriptor)
        try:
            for component in parts[:-1]:
                next_descriptor = os.open(component, directory_flags, dir_fd=descriptor)
                os.close(descriptor)
                descriptor = next_descriptor
            image_descriptor = os.open(parts[-1], file_flags, dir_fd=descriptor)
            try:
                if not stat.S_ISREG(os.fstat(image_descriptor).st_mode):
                    raise ValueError('Image input must be a regular non-symlink file')
                chunks = []
                while True:
                    chunk = os.read(image_descriptor, 1 << 20)
                    if not chunk:
                        return b''.join(chunks)
                    chunks.append(chunk)
            finally:
                os.close(image_descriptor)
        except OSError as exc:
            raise ValueError('Image input must remain below the image root') from exc
        finally:
            os.close(descriptor)


def write_zip(path, members):
    member_names(members)
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


def _git_environment():
    env = {key: value for key, value in os.environ.items() if not key.startswith('GIT_')}
    env.update({
        'GIT_CONFIG_GLOBAL': os.devnull,
        'GIT_CONFIG_NOSYSTEM': '1',
        'GIT_NO_LAZY_FETCH': '1',
        'GIT_NO_REPLACE_OBJECTS': '1',
        'GIT_OPTIONAL_LOCKS': '0',
        'GIT_PAGER': 'cat',
        'GIT_TERMINAL_PROMPT': '0',
    })
    return env


def _git_bytes(checkout, *args):
    command = [
        'git', '--no-pager', '-c', 'core.hooksPath=' + os.devnull,
        '-c', 'core.fsmonitor=false', '-C', str(checkout), *args,
    ]
    result = subprocess.run(command, capture_output=True, env=_git_environment())
    if result.returncode:
        message = (result.stderr or result.stdout)[-2000:].decode('utf-8', errors='replace')
        raise ValueError(message or 'Git object read failed')
    return result.stdout


def _verified_git_object(checkout, kind, object_id):
    if len(object_id) != 40 or any(c not in '0123456789abcdef' for c in object_id):
        raise ValueError('RomPatcher.js commit contains an invalid object ID')
    data = _git_bytes(checkout, 'cat-file', kind, object_id)
    actual = hashlib.sha1(f'{kind} {len(data)}\0'.encode() + data).hexdigest()
    if actual != object_id:
        raise ValueError('RomPatcher.js Git object hash mismatch')
    return data


def _materialize_git_tree(checkout, tree_id, destination):
    raw = _verified_git_object(checkout, 'tree', tree_id)
    position = 0
    seen = set()
    while position < len(raw):
        space = raw.find(b' ', position)
        nul = raw.find(b'\0', space + 1)
        if space < 0 or nul < 0 or nul + 21 > len(raw):
            raise ValueError('RomPatcher.js commit contains a malformed tree')
        mode = raw[position:space]
        name_bytes = raw[space + 1:nul]
        object_id = raw[nul + 1:nul + 21].hex()
        position = nul + 21
        try:
            name = name_bytes.decode('utf-8')
        except UnicodeDecodeError as exc:
            raise ValueError('RomPatcher.js commit contains a non-UTF-8 path') from exc
        if (not name or name in ('.', '..') or '/' in name or '\\' in name
                or name in seen):
            raise ValueError('RomPatcher.js commit contains an unsafe path')
        seen.add(name)
        target = destination / name
        if mode in (b'40000', b'040000'):
            target.mkdir(mode=0o700)
            _materialize_git_tree(checkout, object_id, target)
        elif mode in (b'100644', b'100755'):
            data = _verified_git_object(checkout, 'blob', object_id)
            flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
            if hasattr(os, 'O_CLOEXEC'):
                flags |= os.O_CLOEXEC
            if hasattr(os, 'O_NOFOLLOW'):
                flags |= os.O_NOFOLLOW
            descriptor = os.open(target, flags, 0o700 if mode == b'100755' else 0o600)
            with os.fdopen(descriptor, 'wb') as stream:
                stream.write(data)
        else:
            raise ValueError('RomPatcher.js commit contains a link or unsupported entry')


@contextmanager
def pinned_git_snapshot(checkout, commit):
    checkout = Path(checkout)
    try:
        checkout_info = checkout.lstat()
    except OSError as exc:
        raise ValueError('RomPatcher.js checkout is unavailable') from exc
    if stat.S_ISLNK(checkout_info.st_mode):
        raise ValueError('RomPatcher.js checkout root must not be a symlink')
    if not stat.S_ISDIR(checkout_info.st_mode):
        raise ValueError('RomPatcher.js checkout root must be a directory')

    top_lines = _git_bytes(checkout, 'rev-parse', '--show-toplevel').decode(
        'utf-8', errors='strict').splitlines()
    if len(top_lines) != 1 or Path(top_lines[0]).resolve() != checkout.resolve():
        raise ValueError('RomPatcher.js path must be the Git checkout root')
    object_format = _git_bytes(checkout, 'rev-parse', '--show-object-format').decode().strip()
    if object_format != 'sha1':
        raise ValueError('RomPatcher.js checkout uses an unsupported Git object format')
    head = _git_bytes(checkout, 'rev-parse', '--verify', 'HEAD^{commit}').decode().strip()
    if head != commit:
        raise ValueError('Unexpected RomPatcher.js revision')
    commit_data = _verified_git_object(checkout, 'commit', commit)
    first_line = commit_data.split(b'\n', 1)[0]
    if not first_line.startswith(b'tree '):
        raise ValueError('RomPatcher.js commit has no tree')
    tree_id = first_line[5:].decode('ascii', errors='strict')

    with tempfile.TemporaryDirectory(prefix='sgp-rompatcher-') as temporary:
        snapshot = Path(temporary) / 'tree'
        snapshot.mkdir(mode=0o700)
        _materialize_git_tree(checkout, tree_id, snapshot)
        yield snapshot


def reference_members(lang, reference_dir, guide_dir, cfg):
    install_text(lang, cfg)
    notices = authored_notices(lang, cfg)
    ref = cfg['references'][lang]
    path = reference_dir / ref['name']
    reference = pinned_reference_bytes(path, ref)
    with zipfile.ZipFile(io.BytesIO(reference)) as z:
        consumed = 0

        def read_member(info):
            nonlocal consumed
            # ZipExtFile bounds DEFLATE output, but BZIP2/LZMA backends may
            # expand an unbounded block before honoring read(size).
            if info.compress_type not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED):
                raise ValueError('Unsupported reference compression method')
            remaining = min(MAX_REFERENCE_MEMBER_BYTES, MAX_REFERENCE_TOTAL_BYTES - consumed)
            if info.file_size > remaining:
                raise ValueError('Reference decompression byte limit')
            with z.open(info) as stream:
                data = stream.read(remaining + 1)
            if len(data) > remaining:
                raise ValueError('Reference decompression byte limit')
            consumed += len(data)
            return data

        originals = {'Manual/' + n for n in cfg['original_documents']} | {'Manual/Game Guide.txt'}
        members = {}
        for info in z.infolist():
            if info.filename in originals:
                add_member(members, info.filename, read_member(info))
        for name, pin in cfg['original_documents'].items(): verify_bytes(members['Manual/'+name], pin)
        for info in z.infolist():
            name = info.filename
            if name.startswith('Cheats/') and cfg.get('cheats_policy', 'inherit-reference') == 'inherit-reference':
                member_names([name])
                add_member(members, name.replace('1.2.3', path_token(cfg['version'])),
                           read_member(info).replace(b'1.2.3', cfg['version'].encode()))
        license_name = 'LICENZA.txt' if lang == 'IT' else 'LICENSE.txt'
        licenses = [info for info in z.infolist() if info.filename == license_name]
        if len(licenses) != 1:
            raise ValueError('Reference license collision or missing license')
        add_member(members, license_name, read_member(licenses[0]))
    for name, raw in notices.items():
        add_member(members, name, raw, authored_override=True)
    for p in sorted((documents_dir(cfg)/lang).rglob('*.txt')):
        relative = p.relative_to(documents_dir(cfg)/lang)
        # Root text files are authoring sources for the two player-facing PDFs.
        if (len(relative.parts) > 1 and 'History' not in relative.parts
                and relative.as_posix() not in notices):
            with guide_directory_descriptor(p.parent) as descriptor:
                raw = guide_file_bytes(descriptor, p.name)
            add_member(members, relative.as_posix(), raw, authored_override=True)
    with guide_directory_descriptor(guide_dir) as guide_descriptor:
        for name in guide_names(lang, cfg):
            add_member(members, name, guide_file_bytes(guide_descriptor, name))
    return members


def build(inputs, references, guides, output, rpjs, node='node', xdelta='xdelta3', contract=None):
    cfg = config(contract)
    if output.exists(): raise FileExistsError('Use a new output directory')
    paths = {k: Path(v) for k,v in json.loads(inputs.read_text()).items()}
    for row in cfg['sources']: verify_file(paths[row['id']], row)
    for lang, row in cfg['targets'].items(): verify_file(paths['target-'+lang], row)
    with pinned_git_snapshot(rpjs, cfg['rompatcher_commit']) as rpjs_snapshot:
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
                    result = json.loads(run([node, HERE/'verify-rompatcher.cjs', rpjs_snapshot,
                                              paths[source['id']], patch, source['sha256'], target['sha256'], decoded]))
                    verify_file(decoded, target); decoded.unlink()
                    if result['result'] != 'PASS' or result['patch_sha256'] != hashlib.sha256(raw).hexdigest():
                        raise ValueError('Independent decoder failed')
                    name = patch_path(source['id'])
                    add_member(members, name, raw)
                    rows.append({'file': name, 'source': source, 'bytes':len(raw), 'sha256':hashlib.sha256(raw).hexdigest()})
                    patch.unlink()
                    print(f'{lang}: {len(rows)}/{len(cfg["sources"])} routes verified', flush=True)
                manifest = {'schema':1, 'version':cfg['version'], 'language':lang,
                            'target':target, 'patches':rows,
                            'decoders':['xdelta3','RomPatcher.js'], 'rompatcher_commit':cfg['rompatcher_commit']}
                if 'status' in cfg:
                    manifest.update(status=cfg['status'], open_gates=cfg['open_gates'], cheats_policy=cfg['cheats_policy'])
                members = finalize_members(members, manifest)
                tag = 'US' if lang == 'EN' else 'IT'
                archive = output/f'Sacred-Gold-Plus-{cfg["version"]}-{tag}.zip'
                write_zip(archive, members)
                results.append({'file':archive.name,'bytes':archive.stat().st_size,'sha256':digest(archive),
                                'members':len(members),'routes':len(rows)})
    # Detect changed inputs even if a decoder happened to accept them earlier.
    for row in cfg['sources']: verify_file(paths[row['id']], row)
    for lang, row in cfg['targets'].items(): verify_file(paths['target-'+lang], row)
    (output/'SHA256SUMS').write_text(''.join(f'{r["sha256"]}  {r["file"]}\n' for r in results))
    (output/'verification.json').write_text(json.dumps({'version':cfg['version'],'assets':results,
        'status':cfg.get('status', 'file-reconstruction-verified'),
        'open_gates':cfg.get('open_gates', []),
        'contract_sha256':digest(contract or HERE/'release-1.3.1.json'),
        'scope':'File reconstruction with two decoders; no game runtime or save compatibility test.'},indent=2)+'\n')
    return results


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['inputs','references','guides','output','rompatcher']: p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--node',default='node');p.add_argument('--xdelta',default='xdelta3')
    p.add_argument('--contract',type=Path,help='Versioned contract; default is current 1.3.1')
    a=p.parse_args()
    print(json.dumps(build(a.inputs,a.references,a.guides,a.output,a.rompatcher,a.node,a.xdelta,a.contract),indent=2))
