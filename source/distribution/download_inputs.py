#!/usr/bin/env python3
"""Copy pinned developer inputs from the authenticated single player ZIP.

No ROM is downloaded. The complete ZIP is checked against a separately tracked
delivery pin before any member is opened. Only named, size/hash-pinned regular
files are copied; archive paths are never used as filesystem destinations.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import secrets
import shutil
import stat
import tempfile
import time
import unicodedata
import urllib.request
import urllib.parse
import zipfile

HERE = Path(__file__).resolve().parent
MAX_CONTAINER_BYTES = 2 * 1024**3
MIN_FREE_BYTES = 10 * 1024**3
BLOCK = 1024**2
DEADLINE_SECONDS = 30 * 60


def _pin(row):
    return (isinstance(row, dict) and type(row.get('bytes')) is int
            and 0 < row['bytes'] < MAX_CONTAINER_BYTES
            and isinstance(row.get('sha256'), str)
            and re.fullmatch('[0-9a-f]{64}', row['sha256']))


def _member(name):
    if (not isinstance(name, str) or not name or '\\' in name
            or any(ord(c) < 32 or c in '<>:"|?*' for c in name)):
        raise ValueError('Unsafe container member name')
    path = PurePosixPath(name)
    parts = name.rstrip('/').split('/')
    if (path.is_absolute() or any(not p or p in ('.', '..') or p.endswith(('.', ' ')) for p in parts)
            or path.as_posix() != name.rstrip('/')):
        raise ValueError('Unsafe container member path')
    return unicodedata.normalize('NFC', name.rstrip('/')).casefold()


def validate_delivery(delivery):
    if (not _pin(delivery) or delivery.get('schema') != 1
            or not isinstance(delivery.get('url'), str) or not delivery['url'].startswith('https://')
            or not isinstance(delivery.get('files'), list) or not delivery['files']):
        raise ValueError('Invalid build-input delivery pin')
    names, members = set(), set()
    for row in delivery['files']:
        if not _pin(row) or set(row) != {'name', 'member', 'bytes', 'sha256'}:
            raise ValueError('Invalid build-input member pin')
        name, member = row['name'], row['member']
        key = _member(member)
        if (not isinstance(name, str) or not re.fullmatch('[A-Za-z0-9][A-Za-z0-9._-]*', name)
                or name.endswith('.') or PurePosixPath(member).name != name
                or name.casefold() in names or key in members):
            raise ValueError('Invalid or duplicate build-input name')
        names.add(name.casefold()); members.add(key)
    return delivery


def load_delivery(path=None):
    delivery = validate_delivery(json.loads(Path(path or HERE / 'build-input-delivery.json').read_text()))
    expected = json.loads((HERE / 'build-inputs.json').read_text())['files']
    actual = [{key: row[key] for key in ('name', 'sha256', 'bytes')} for row in delivery['files']]
    if actual != expected:
        raise ValueError('Delivery changes an immutable historical build input')
    return delivery


def _destination(path):
    flags = os.O_RDONLY | getattr(os, 'O_DIRECTORY', 0) | getattr(os, 'O_NOFOLLOW', 0)
    descriptor = os.open(path, flags)
    info = os.fstat(descriptor)
    if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o022:
        os.close(descriptor)
        raise ValueError('Destination must be a private directory owned by the current user')
    return descriptor


def _hash(stream):
    digest, size = hashlib.sha256(), 0
    for chunk in iter(lambda: stream.read(BLOCK), b''):
        digest.update(chunk); size += len(chunk)
    return dict(bytes=size, sha256=digest.hexdigest())


def _matches(actual, pin):
    return all(actual[key] == pin[key] for key in ('bytes', 'sha256'))


def _present(directory, row):
    try:
        info = os.stat(row['name'], dir_fd=directory, follow_symlinks=False)
    except FileNotFoundError:
        return False
    if not stat.S_ISREG(info.st_mode):
        raise ValueError('Existing build input is not a regular file: ' + row['name'])
    descriptor = os.open(row['name'], os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0), dir_fd=directory)
    with os.fdopen(descriptor, 'rb') as stream:
        opened = os.fstat(stream.fileno())
        if (opened.st_dev, opened.st_ino) != (info.st_dev, info.st_ino) or not _matches(_hash(stream), row):
            raise ValueError('Existing build input differs; preserve it and choose a new destination: ' + row['name'])
    return True


def _selection(delivery, names):
    by_name = {row['name']: row for row in delivery['files']}
    selected = list(by_name) if names is None else list(names)
    if not selected or len(selected) != len(set(selected)) or set(selected) - set(by_name):
        raise ValueError('Unknown, empty or duplicate build-input selection')
    return [by_name[name] for name in selected]


def extract_inputs(container, destination, delivery, names=None):
    """Verify the complete local ZIP, then atomically copy selected pinned files."""
    validate_delivery(delivery)
    selected = _selection(delivery, names)
    directory, pending = _destination(destination), []
    try:
        descriptor = os.open(container, os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0))
        with os.fdopen(descriptor, 'rb') as stream:
            info = os.fstat(stream.fileno())
            if (not stat.S_ISREG(info.st_mode) or info.st_size != delivery['bytes']
                    or not _matches(_hash(stream), delivery)):
                raise ValueError('Release ZIP differs from the tracked delivery pin')
            stream.seek(0)
            with zipfile.ZipFile(stream) as archive:
                entries = archive.infolist()
                if len(entries) > 4096:
                    raise ValueError('Too many release ZIP members')
                keys = [_member(row.filename) for row in entries]
                if len(keys) != len(set(keys)):
                    raise ValueError('Duplicate or aliased release ZIP members')
                for entry in entries:
                    mode = entry.external_attr >> 16
                    if entry.flag_bits & 1 or stat.S_IFMT(mode) not in (0, stat.S_IFREG, stat.S_IFDIR):
                        raise ValueError('Encrypted or non-regular release ZIP member')
                results = []
                for row in selected:
                    name = row['name']
                    if _present(directory, row):
                        results.append(dict(name=name, status='present', **{k: row[k] for k in ('bytes', 'sha256')}))
                        continue
                    entry = archive.getinfo(row['member'])
                    if entry.is_dir() or entry.file_size != row['bytes']:
                        raise ValueError('Build-input member size differs: ' + name)
                    temporary = '.sgp-input-' + secrets.token_hex(16)
                    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL
                                         | getattr(os, 'O_NOFOLLOW', 0), 0o600, dir_fd=directory)
                    pending.append((temporary, name))
                    digest, size = hashlib.sha256(), 0
                    with os.fdopen(descriptor, 'wb') as out, archive.open(entry) as source:
                        while True:
                            chunk = source.read(min(BLOCK, row['bytes'] - size + 1))
                            if not chunk: break
                            size += len(chunk)
                            if size > row['bytes']:
                                raise ValueError('Build-input member exceeds its pinned size')
                            digest.update(chunk); out.write(chunk)
                        out.flush(); os.fsync(out.fileno())
                    if not _matches(dict(bytes=size, sha256=digest.hexdigest()), row):
                        raise ValueError('Build-input member content differs: ' + name)
                    results.append(dict(name=name, status='extracted', bytes=size, sha256=digest.hexdigest()))
                # All selected members authenticate before the first publication.
                for temporary, name in pending:
                    os.link(temporary, name, src_dir_fd=directory, dst_dir_fd=directory, follow_symlinks=False)
                return results
    except (OSError, KeyError, zipfile.BadZipFile) as exc:
        raise ValueError('Cannot retrieve authenticated build inputs: ' + str(exc)) from exc
    finally:
        for temporary, _ in pending:
            try: os.unlink(temporary, dir_fd=directory)
            except FileNotFoundError: pass
        os.close(directory)


def fetch_inputs(destination, delivery, names=None, *, container=None, opener=None,
                 url_override=None, clock=time.monotonic):
    """Use a local ZIP or one bounded temporary download, removed after extraction."""
    validate_delivery(delivery)
    url = delivery['url'] if url_override is None else url_override
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme not in ('https', 'http') or not parsed.hostname or parsed.username or parsed.fragment:
        raise ValueError('Explicit mirror must be an HTTP(S) URL without credentials or fragment')
    if container is not None:
        return extract_inputs(container, destination, delivery, names)
    selected = _selection(delivery, names)
    directory = _destination(destination)
    try:
        present = [_present(directory, row) for row in selected]
        if all(present):
            return [dict(name=row['name'], status='present', **{k: row[k] for k in ('bytes', 'sha256')})
                    for row in selected]
    finally:
        os.close(directory)
    required = delivery['bytes'] + sum(row['bytes'] for row in delivery['files']) + MIN_FREE_BYTES
    if shutil.disk_usage(destination).free < required:
        raise ValueError('Insufficient storage: retain at least 10 GiB free after retrieval')
    opener = opener or (lambda url: urllib.request.urlopen(url, timeout=60))
    started = clock()
    with tempfile.TemporaryDirectory(prefix='.sgp-inputs-', dir=destination) as temporary:
        path = Path(temporary) / 'release.zip'
        size = 0
        with opener(url) as source, path.open('xb') as out:
            headers = getattr(source, 'headers', {})
            length = headers.get('Content-Length')
            if length is not None and int(length) != delivery['bytes']:
                raise ValueError('Release ZIP Content-Length differs from its pin')
            read = getattr(source, 'read1', source.read)
            while True:
                if clock() - started > DEADLINE_SECONDS:
                    raise ValueError('Release ZIP download exceeded its time limit')
                chunk = read(min(BLOCK, delivery['bytes'] - size + 1))
                if clock() - started > DEADLINE_SECONDS:
                    raise ValueError('Release ZIP download exceeded its time limit')
                if not chunk: break
                size += len(chunk)
                if size > delivery['bytes']:
                    raise ValueError('Release ZIP download exceeds its pinned size')
                out.write(chunk)
        if size != delivery['bytes']:
            raise ValueError('Release ZIP download is truncated')
        return extract_inputs(path, destination, delivery, names)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--destination', required=True, type=Path)
    parser.add_argument('--container', type=Path, help='reuse an already downloaded player ZIP')
    parser.add_argument('--delivery', type=Path, help='tracked delivery pin; default is beside this script')
    parser.add_argument('--file', action='append', dest='names', help='one pinned basename; repeat to select')
    args = parser.parse_args(argv)
    try:
        rows = fetch_inputs(args.destination, load_delivery(args.delivery), args.names, container=args.container)
    except (ValueError, OSError) as exc:
        parser.exit(2, 'REFUSED: ' + str(exc) + '\n')
    print(json.dumps(rows, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
