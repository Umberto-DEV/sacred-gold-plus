"""Descriptor-bound, no-replace publication for private debug artifacts."""
from __future__ import annotations

import json
import os
from pathlib import Path
import stat


class OutputRefused(ValueError):
    pass


def _open_directory(path: Path, create: bool) -> tuple[int, Path]:
    original = path.absolute()
    if original.is_symlink():
        raise OutputRefused(f'output directory is a symlink: {original}')
    resolved = original.resolve(strict=False)
    fd = os.open('/', os.O_RDONLY | os.O_DIRECTORY)
    try:
        for component in resolved.parts[1:]:
            flags = os.O_RDONLY | os.O_DIRECTORY | getattr(os, 'O_NOFOLLOW', 0)
            try:
                child = os.open(component, flags, dir_fd=fd)
            except FileNotFoundError:
                if not create:
                    raise
                os.mkdir(component, 0o700, dir_fd=fd)
                child = os.open(component, flags, dir_fd=fd)
                os.fchmod(child, 0o700)
            os.close(fd)
            fd = child
        info = os.fstat(fd)
        if (not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid()
                or info.st_mode & 0o077):
            raise OutputRefused(f'output directory is not private/owned: {resolved}')
        return fd, resolved
    except Exception:
        os.close(fd)
        raise


class PrivateDirectory:
    def __init__(self, path, *, create=True):
        self.fd, self.path = _open_directory(Path(path), create)

    def _parts(self, name):
        relative = Path(name)
        if relative.is_absolute() or not relative.parts:
            raise OutputRefused('output name must be relative')
        if any(part in ('', '.', '..') for part in relative.parts):
            raise OutputRefused('invalid output path component')
        return relative.parts

    def _parent(self, name):
        parts = self._parts(name)
        fd = os.dup(self.fd)
        try:
            for component in parts[:-1]:
                flags = os.O_RDONLY | os.O_DIRECTORY | getattr(os, 'O_NOFOLLOW', 0)
                try:
                    child = os.open(component, flags, dir_fd=fd)
                except FileNotFoundError:
                    os.mkdir(component, 0o700, dir_fd=fd)
                    child = os.open(component, flags, dir_fd=fd)
                    os.fchmod(child, 0o700)
                info = os.fstat(child)
                if info.st_uid != os.getuid() or info.st_mode & 0o077:
                    os.close(child)
                    raise OutputRefused('nested output directory is not private/owned')
                os.close(fd)
                fd = child
            return fd, parts[-1]
        except Exception:
            os.close(fd)
            raise

    def open_new(self, name, *, binary=False):
        parent, leaf = self._parent(name)
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, 'O_NOFOLLOW', 0)
        try:
            fd = os.open(leaf, flags, 0o600, dir_fd=parent)
        finally:
            os.close(parent)
        os.fchmod(fd, 0o600)
        info = os.fstat(fd)
        if (not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid()
                or info.st_nlink != 1 or info.st_mode & 0o077):
            os.close(fd)
            raise OutputRefused('unsafe output identity')
        if binary:
            return os.fdopen(fd, 'wb')
        return os.fdopen(fd, 'w', encoding='utf-8')

    def ensure_dir(self, name):
        parts = self._parts(name)
        fd = os.dup(self.fd)
        try:
            for component in parts:
                flags = os.O_RDONLY | os.O_DIRECTORY | getattr(os, 'O_NOFOLLOW', 0)
                try:
                    child = os.open(component, flags, dir_fd=fd)
                except FileNotFoundError:
                    os.mkdir(component, 0o700, dir_fd=fd)
                    child = os.open(component, flags, dir_fd=fd)
                    os.fchmod(child, 0o700)
                info = os.fstat(child)
                if info.st_uid != os.getuid() or info.st_mode & 0o077:
                    os.close(child)
                    raise OutputRefused('nested output directory is not private/owned')
                os.close(fd)
                fd = child
        finally:
            os.close(fd)
        return self.path.joinpath(*parts)

    def write_new(self, name, data):
        with self.open_new(name, binary=True) as output:
            output.write(data)
            output.flush()
            os.fsync(output.fileno())

    def close(self):
        if self.fd is not None:
            os.close(self.fd)
            self.fd = None

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()


def write_new(path, data):
    path = Path(path).absolute()
    payload = data.encode() if isinstance(data, str) else data
    with PrivateDirectory(path.parent) as directory:
        directory.write_new(path.name, payload)


def write_json_new(path, value):
    write_new(path, json.dumps(value, indent=2, ensure_ascii=False) + '\n')
