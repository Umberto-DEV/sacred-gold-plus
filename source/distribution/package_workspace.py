#!/usr/bin/env python3
"""Edit player documents in a complete package without rebuilding game patches."""
import argparse
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import tempfile
import unicodedata
import zipfile


HERE = Path(__file__).resolve().parent
BASELINE = HERE / 'package-baseline-1.3.2.json'
ROOT = 'Sacred Gold Plus 1.3.2'
ZIP_NAME = 'Sacred-Gold-Plus-1.3.2.zip'
LOCK_NAME = '.workspace-lock.json'
STAMP = (2026, 10, 27, 0, 0, 0)
CHUNK = 1024 * 1024
MAX_TREE_BYTES = 2 * 1024 * 1024 * 1024
MAX_FILES = 2048
MIN_FREE_BYTES = 10 * 1024 * 1024 * 1024
GENERATED = frozenset((ROOT + '/CONTENTS.json', ROOT + '/SHA256SUMS'))
LANGUAGES = {'EN': 'EN-English', 'IT': 'IT-Italiano', 'FR': 'FR-Francais',
             'ES': 'ES-Espanol', 'DE': 'DE-Deutsch'}
MUTABLE = frozenset(
    [f'{ROOT}/{folder}/{kind}-1.3.2-{language}.pdf'
     for language, folder in LANGUAGES.items()
     for kind in ('Installation', 'Whats-New')]
    + [f'{ROOT}/Originals/{kind}-1.3.2-EN.pdf'
       for kind in ('Evolutions', 'Game-Guide', 'Items-TMs', 'Pokemon-Changes',
                    'Pokemon-Locations', 'Special-Events', 'Trainers', 'Move-Changes')]
    + [ROOT + '/Originals/ABOUT-THESE-GUIDES.txt'])
OPTIONAL = frozenset((ROOT + '/Originals/Move-Changes-1.3.2-EN.pdf',
                      ROOT + '/Originals/ABOUT-THESE-GUIDES.txt'))


def _json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8')


def _digest_stream(stream):
    digest = hashlib.sha256()
    size = 0
    for data in iter(lambda: stream.read(CHUNK), b''):
        size += len(data)
        digest.update(data)
    return {'bytes': size, 'sha256': digest.hexdigest()}


def _names(names):
    """Validate portable paths and aliases before creating any destination."""
    entries = {}
    devices = {'CON', 'PRN', 'AUX', 'NUL',
               *('COM' + str(n) for n in range(1, 10)),
               *('LPT' + str(n) for n in range(1, 10)),
               *('COM' + n for n in '¹²³'), *('LPT' + n for n in '¹²³')}
    for name in names:
        if not isinstance(name, str) or not name or '\\' in name:
            raise ValueError('Unsafe package member name')
        parts = name.rstrip('/').split('/')
        if parts[0] != ROOT:
            raise ValueError('Unexpected package root: ' + repr(name))
        for part in parts:
            if (not part or part in ('.', '..') or part.endswith(('.', ' '))
                    or any(ord(c) < 32 or c in '<>:"|?*' for c in part)
                    or part.split('.')[0].upper() in devices):
                raise ValueError('Unsafe package member name: ' + repr(name))
        key = unicodedata.normalize('NFC', '/'.join(parts)).casefold()
        if key in entries:
            raise ValueError('Duplicate or aliased package member: ' + repr(name))
        entries[key] = name.endswith('/')
    for key in entries:
        parts = key.split('/')
        for count in range(1, len(parts)):
            parent = '/'.join(parts[:count])
            if parent in entries and not entries[parent]:
                raise ValueError('Package file/directory collision: ' + key)


def _location(path):
    path = Path(path).absolute()
    if path.is_symlink():
        raise ValueError('Workspace/output path is a symlink')
    # Canonicalize OS parent aliases such as macOS /var -> /private/var.
    return path.parent.resolve() / path.name


def _regular(path, boundary):
    try:
        parts = path.relative_to(boundary).parts
    except ValueError as exc:
        raise ValueError('Path is outside workspace') from exc
    current = boundary
    for part in parts[:-1]:
        current = current / part
        if current.is_symlink() or not current.is_dir():
            raise ValueError('Workspace contains a symlink or non-directory')
    mode = path.lstat().st_mode
    if not stat.S_ISREG(mode):
        raise ValueError('Workspace contains a symlink or non-regular file')


@contextmanager
def _reader(path, boundary):
    _regular(path, boundary)
    descriptor = os.open(path, os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0))
    with os.fdopen(descriptor, 'rb') as stream:
        if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
            raise ValueError('Workspace member is not a regular file')
        yield stream


def _identity(path, boundary):
    with _reader(path, boundary) as stream:
        return _digest_stream(stream)


def _budget(parent, required):
    ancestor = parent
    while not ancestor.exists():
        ancestor = ancestor.parent
    if shutil.disk_usage(ancestor).free < required + MIN_FREE_BYTES:
        raise ValueError('Insufficient disk space: retain at least 10 GiB free')


def _delivery(value):
    if value is None:
        value = BASELINE
    data = value if isinstance(value, dict) else json.loads(Path(value).read_text())
    size, digest = data.get('bytes'), data.get('sha256')
    if (type(size) is not int or size < 1 or size > MAX_TREE_BYTES
            or not isinstance(digest, str) or not re.fullmatch('[0-9a-f]{64}', digest)):
        raise ValueError('Invalid delivery identity')
    return {'bytes': size, 'sha256': digest}


def _seed_signature(stream):
    state = os.fstat(stream.fileno())
    return state.st_dev, state.st_ino, state.st_size, state.st_mtime_ns, state.st_ctime_ns


@contextmanager
def _authenticated_archive(seed, expected):
    # Parse the very same open file that was hashed. Reopening its pathname
    # after authentication would allow a replacement archive to bypass the pin.
    with _reader(seed, seed.parent) as stream:
        signature = _seed_signature(stream)
        if _digest_stream(stream) != expected or _seed_signature(stream) != signature:
            raise ValueError('Seed ZIP identity does not match the delivery SHA-256/size')
        stream.seek(0)
        with zipfile.ZipFile(stream) as archive:
            yield archive, signature


def seed_workspace(seed, workspace, *, delivery=None, limit=MAX_TREE_BYTES):
    """Authenticate an existing ZIP and extract once into a new contents tree.

    ``delivery`` is a tracked pin path, or an explicit pin dictionary for callers
    and ROM-free fixtures. The CLI defaults to the frozen corrected baseline.
    """
    if not 0 < limit <= MAX_TREE_BYTES:
        raise ValueError('Invalid expanded-size limit')
    seed = Path(seed).absolute()
    expected = _delivery(delivery)
    if seed.is_symlink() or not seed.is_file():
        raise ValueError('Seed must be a regular ZIP file')
    actual = expected
    work = _location(workspace)
    if ((work / 'contents').exists() or (work / 'contents').is_symlink()
            or (work / LOCK_NAME).exists() or (work / LOCK_NAME).is_symlink()):
        raise FileExistsError('Workspace already contains contents or a lock; preserve it')
    with _authenticated_archive(seed, expected) as (archive, seed_signature):
        infos = archive.infolist()
        if len(infos) > MAX_FILES:
            raise ValueError('Archive member-count limit exceeded')
        _names([info.filename for info in infos])
        total = 0
        for info in infos:
            kind = stat.S_IFMT(info.external_attr >> 16)
            allowed = (0, stat.S_IFDIR) if info.is_dir() else (0, stat.S_IFREG)
            if kind not in allowed or info.flag_bits & 1:
                raise ValueError('Archive contains an encrypted or non-regular member type')
            if info.compress_type not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED):
                raise ValueError('Unsupported archive compression type')
            total += info.file_size
            if info.file_size < 0 or total > limit:
                raise ValueError('Archive expanded-size limit exceeded')
        _budget(work.parent, total)
        work.mkdir(parents=True, exist_ok=True)
        if not work.is_dir():
            raise ValueError('Workspace is not a directory')
        with tempfile.TemporaryDirectory(prefix='.seed-', dir=work) as temporary:
            contents = Path(temporary) / 'contents'
            contents.mkdir()
            identities = {}
            expanded = 0
            for info in infos:
                path = contents / info.filename
                if info.is_dir():
                    path.mkdir(parents=True, exist_ok=True)
                    continue
                path.parent.mkdir(parents=True, exist_ok=True)
                digest, count = hashlib.sha256(), 0
                with archive.open(info) as source, path.open('xb') as destination:
                    for data in iter(lambda: source.read(CHUNK), b''):
                        count += len(data)
                        expanded += len(data)
                        if count > info.file_size or expanded > limit:
                            raise ValueError('Archive actual expanded-size limit exceeded')
                        destination.write(data)
                        digest.update(data)
                if count != info.file_size:
                    raise ValueError('Truncated archive member')
                identities[info.filename] = {'bytes': count, 'sha256': digest.hexdigest()}
            inventory = contents / ROOT / 'CONTENTS.json'
            if not GENERATED.issubset(identities) or inventory.stat().st_size > CHUNK:
                raise ValueError('Missing or oversized root package inventories')
            template = json.loads(inventory.read_text())
            if (template.get('schema') != 3 or template.get('version') != '1.3.2'
                    or not isinstance(template.get('files'), dict)):
                raise ValueError('Unsupported package inventory')
            template.pop('files')
            lock = {'schema': 1, 'seed': actual, 'members': identities,
                    'inventory_template': template}
            if _seed_signature(archive.fp) != seed_signature:
                raise ValueError('Seed ZIP changed during extraction')
            lock_path = work / LOCK_NAME
            # Exclusive creation preserves a concurrent workspace or existing lock.
            with lock_path.open('xb') as output:
                output.write(_json_bytes(lock))
            try:
                if (work / 'contents').exists():
                    raise FileExistsError('Contents appeared during extraction')
                contents.rename(work / 'contents')
                lock_path.chmod(0o444)
            except BaseException:
                lock_path.unlink()
                raise
    return {'workspace': str(work), 'members': len(identities),
            'expanded_bytes': expanded, 'seed': actual}


def _load_lock(work):
    path = work / LOCK_NAME
    if path.stat().st_size > 2 * CHUNK:
        raise ValueError('Oversized workspace lock')
    with _reader(path, work) as stream:
        lock = json.load(stream)
    if (not isinstance(lock, dict)
            or set(lock) != {'schema', 'seed', 'members', 'inventory_template'}
            or lock['schema'] != 1 or not isinstance(lock['members'], dict)
            or not 0 < len(lock['members']) <= MAX_FILES):
        raise ValueError('Invalid workspace lock')
    _delivery(lock['seed'])
    _names(lock['members'])
    if not GENERATED.issubset(lock['members']):
        raise ValueError('Workspace lock lacks generated inventories')
    for row in lock['members'].values():
        if (not isinstance(row, dict) or set(row) != {'bytes', 'sha256'}
                or type(row['bytes']) is not int or not 0 <= row['bytes'] <= MAX_TREE_BYTES
                or not isinstance(row['sha256'], str)
                or not re.fullmatch('[0-9a-f]{64}', row['sha256'])):
            raise ValueError('Invalid locked member identity')
    template = lock['inventory_template']
    if (not isinstance(template, dict) or 'files' in template
            or template.get('schema') != 3 or template.get('version') != '1.3.2'):
        raise ValueError('Invalid locked inventory template')
    return lock


def _scan(contents):
    if contents.is_symlink() or not contents.is_dir():
        raise ValueError('Contents must be a regular directory, not a symlink')
    files = {}
    total = 0
    for base, directories, names in os.walk(contents, followlinks=False):
        for name in directories:
            if (Path(base) / name).is_symlink():
                raise ValueError('Workspace contains a directory symlink')
        for name in names:
            path = Path(base) / name
            _regular(path, contents)
            relative = path.relative_to(contents).as_posix()
            files[relative] = path
            total += path.stat().st_size
            if len(files) > MAX_FILES or total > MAX_TREE_BYTES:
                raise ValueError('Workspace size/count limit exceeded')
    _names(files)
    return files, total


def _write_generated(path, data):
    with tempfile.NamedTemporaryFile(prefix='.' + path.name + '-',
                                     dir=path.parent, delete=False) as temporary:
        temporary_path = Path(temporary.name)
        temporary.write(data)
    try:
        os.replace(temporary_path, path)
    finally:
        temporary_path.unlink(missing_ok=True)


def build_workspace(workspace, output):
    """Compose a new deterministic ZIP, permitting only known document edits."""
    work, output = _location(workspace), _location(output)
    contents = work / 'contents'
    if output == contents or contents in output.parents:
        raise ValueError('Output must be outside the editable contents tree')
    if output.exists():
        raise FileExistsError('Output directory already exists; preserve previous builds')
    lock = _load_lock(work)
    files, total = _scan(contents)
    expected = set(lock['members'])
    missing = expected - set(files) - GENERATED
    unexpected = set(files) - expected - OPTIONAL
    if missing:
        raise ValueError('Missing package members: ' + ', '.join(sorted(missing)))
    if unexpected:
        raise ValueError('Unexpected package members: ' + ', '.join(sorted(unexpected)))
    identities = {}
    for name, path in sorted(files.items()):
        if name in GENERATED:
            continue
        row = _identity(path, contents)
        if name not in MUTABLE and row != lock['members'][name]:
            raise ValueError('Immutable package member changed: ' + name)
        if name in MUTABLE and name.endswith('.pdf'):
            with _reader(path, contents) as stream:
                if stream.read(5) != b'%PDF-':
                    raise ValueError('Document is not a PDF: ' + name)
        identities[name] = row
    inventory = dict(lock['inventory_template'])
    inventory['files'] = {name[len(ROOT) + 1:]: row for name, row in identities.items()}
    inventory_bytes = _json_bytes(inventory)
    inventory_name = ROOT + '/CONTENTS.json'
    identities[inventory_name] = {'bytes': len(inventory_bytes),
                                  'sha256': hashlib.sha256(inventory_bytes).hexdigest()}
    checksums = ''.join(f"{row['sha256']}  {name[len(ROOT) + 1:]}\n"
                        for name, row in sorted(identities.items())).encode()
    checksum_name = ROOT + '/SHA256SUMS'
    identities[checksum_name] = {'bytes': len(checksums),
                                'sha256': hashlib.sha256(checksums).hexdigest()}
    final_size = sum(row['bytes'] for row in identities.values())
    if final_size > MAX_TREE_BYTES:
        raise ValueError('Final package expanded-size limit exceeded')
    _budget(output.parent, max(total, final_size) + MAX_FILES * 1024 + CHUNK)
    _write_generated(contents / inventory_name, inventory_bytes)
    _write_generated(contents / checksum_name, checksums)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.mkdir()
    try:
        temporary = output / (ZIP_NAME + '.pending')
        with zipfile.ZipFile(temporary, 'x', compression=zipfile.ZIP_DEFLATED,
                             compresslevel=6, allowZip64=True) as archive:
            for name, expected_row in sorted(identities.items()):
                info = zipfile.ZipInfo(name, STAMP)
                info.create_system = 3
                info.external_attr = (stat.S_IFREG | 0o644) << 16
                info.compress_type = zipfile.ZIP_DEFLATED
                digest, count = hashlib.sha256(), 0
                with _reader(contents / name, contents) as source, archive.open(info, 'w') as destination:
                    for data in iter(lambda: source.read(CHUNK), b''):
                        count += len(data)
                        digest.update(data)
                        destination.write(data)
                if {'bytes': count, 'sha256': digest.hexdigest()} != expected_row:
                    raise ValueError('Workspace changed during composition: ' + name)
        # Reopen independently: compare every full member, including generated
        # inventories, with the scanned source identities before publishing.
        with zipfile.ZipFile(temporary) as archive:
            infos = archive.infolist()
            if len(infos) != len(identities) or set(archive.namelist()) != set(identities):
                raise ValueError('Output ZIP membership differs')
            for info in infos:
                with archive.open(info) as stream:
                    if _digest_stream(stream) != identities[info.filename]:
                        raise ValueError('Output ZIP member differs: ' + info.filename)
        target = output / ZIP_NAME
        temporary.rename(target)
        identity = _identity(target, output)
        report = {'schema': 1, 'zip': str(target), **identity, 'seed': lock['seed'],
                  'members': len(identities), 'immutable_members':
                  len(set(identities) - MUTABLE - GENERATED),
                  'all_members_verified': True}
        (output / 'verification.json').write_bytes(_json_bytes(report))
        (output / 'SHA256SUMS').write_text(f"{identity['sha256']}  {ZIP_NAME}\n")
        return report
    except BaseException:
        # This directory was created exclusively by this invocation. Preserve
        # the editable inputs and every pre-existing output, remove failed ZIPs.
        shutil.rmtree(output)
        raise


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    seed = commands.add_parser('seed', help='authenticate and extract one existing package')
    seed.add_argument('--seed', required=True, type=Path)
    seed.add_argument('--workspace', default=Path('package'), type=Path)
    seed.add_argument('--delivery', default=BASELINE, type=Path,
                      help='tracked archive identity; defaults to frozen corrected baseline')
    build = commands.add_parser('build', help='verify payloads and compose to a new output directory')
    build.add_argument('--workspace', default=Path('package'), type=Path)
    build.add_argument('--output', required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == 'seed':
            result = seed_workspace(args.seed, args.workspace, delivery=args.delivery)
        else:
            result = build_workspace(args.workspace, args.output)
    except (ValueError, OSError, zipfile.BadZipFile, KeyError) as exc:
        parser.exit(1, str(exc) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
