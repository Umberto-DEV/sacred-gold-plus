"""Descriptor-bound admission for private build inputs."""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import stat


MAX_NDS_BYTES = 512 * 1024 * 1024
MAX_CHARMAP_BYTES = 1024 * 1024
MAX_SCRCMD_BYTES = 1024 * 1024
MAX_SOURCE_BYTES = 1024 * 1024
MAX_SOURCE_FILES = 10000
MAX_SOURCE_TOTAL_BYTES = 64 * 1024 * 1024


def _open_regular(path):
    # O_NONBLOCK lets fstat reject FIFOs/devices without waiting for a writer.
    # It has no effect on admitted regular files.
    flags = (os.O_RDONLY | getattr(os, 'O_CLOEXEC', 0)
             | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_NONBLOCK', 0))
    fd = os.open(Path(path), flags)
    info = os.fstat(fd)
    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
        os.close(fd)
        raise ValueError('input must be one regular non-aliased file')
    return fd, info


def read_bounded(path, limit, label, *, exact_size=None, expected_sha256=None):
    """Read one admitted inode once; size is checked before allocation."""
    fd, before = _open_regular(path)
    try:
        if before.st_size < 0 or before.st_size > limit:
            raise ValueError(f'{label} exceeds its {limit}-byte limit')
        if exact_size is not None and before.st_size != exact_size:
            raise ValueError(f'{label} has unexpected size')
        digest = hashlib.sha256()
        chunks = []
        remaining = before.st_size
        while remaining:
            chunk = os.read(fd, min(1024 * 1024, remaining))
            if not chunk:
                raise ValueError(f'{label} was truncated during admission')
            chunks.append(chunk)
            digest.update(chunk)
            remaining -= len(chunk)
        if os.read(fd, 1):
            raise ValueError(f'{label} grew during admission')
        after = os.fstat(fd)
        if ((before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
                != (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)):
            raise ValueError(f'{label} changed during admission')
        hexdigest = digest.hexdigest()
        if expected_sha256 is not None and hexdigest != expected_sha256:
            raise ValueError(f'{label} SHA-256 does not match')
        return b''.join(chunks), hexdigest
    finally:
        os.close(fd)


def read_contract(path, contracts, label):
    """Admit only a finite ``sha256 -> (identity, exact bytes)`` contract."""
    sizes = {size for _identity, size in contracts.values()}
    fd, before = _open_regular(path)
    try:
        if before.st_size not in sizes:
            raise ValueError(f'{label} is not an exact supported input size')
        digest = hashlib.sha256()
        chunks = []
        remaining = before.st_size
        while remaining:
            chunk = os.read(fd, min(1024 * 1024, remaining))
            if not chunk:
                raise ValueError(f'{label} was truncated during admission')
            chunks.append(chunk)
            digest.update(chunk)
            remaining -= len(chunk)
        if os.read(fd, 1):
            raise ValueError(f'{label} grew during admission')
        after = os.fstat(fd)
        if ((before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
                != (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)):
            raise ValueError(f'{label} changed during admission')
        hexdigest = digest.hexdigest()
        if hexdigest not in contracts or contracts[hexdigest][1] != before.st_size:
            raise ValueError(f'{label} is not an exact supported input')
        return b''.join(chunks), contracts[hexdigest][0], hexdigest
    finally:
        os.close(fd)


def source_snapshot(root, paths):
    """Hash a bounded set of source inodes without pathname re-opens."""
    root = Path(root).resolve()
    # Normalize lexical ``..`` without resolving a final symlink. Otherwise a
    # spelling such as root/../outside can pass Path.relative_to(root).
    selected = sorted({Path(os.path.abspath(path)) for path in paths})
    if len(selected) > MAX_SOURCE_FILES:
        raise ValueError('source snapshot file-count limit')
    result = {}
    total = 0
    for path in selected:
        try:
            relative = path.relative_to(root)
        except ValueError as exc:
            raise ValueError('source snapshot path outside root') from exc
        fd, before = _open_regular(path)
        try:
            if before.st_size < 0 or before.st_size > MAX_SOURCE_BYTES:
                raise ValueError('source snapshot per-file limit')
            total += before.st_size
            if total > MAX_SOURCE_TOTAL_BYTES:
                raise ValueError('source snapshot total-byte limit')
            digest = hashlib.sha256()
            remaining = before.st_size
            while remaining:
                chunk = os.read(fd, min(1024 * 1024, remaining))
                if not chunk:
                    raise ValueError('source changed during snapshot')
                digest.update(chunk)
                remaining -= len(chunk)
            if os.read(fd, 1):
                raise ValueError('source grew during snapshot')
            after = os.fstat(fd)
            current = os.stat(path, follow_symlinks=False)
            identity = lambda info: (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns)
            if identity(before) != identity(after) or identity(after) != identity(current):
                raise ValueError('source path/inode changed during snapshot')
            result[str(relative)] = digest.hexdigest()
        finally:
            os.close(fd)
    return result
