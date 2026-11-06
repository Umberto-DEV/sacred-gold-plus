"""Authenticate the actual protected compiler before process creation."""
import hashlib
import ctypes
import errno
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys

COMPILER_SHA256 = 'fc5e3cbba6ad54059295cad716aacb05ace8235f5f7a6031f1d8c15d24bd6d66'
APPLE_COMPILER = Path('/Library/Developer/CommandLineTools/usr/bin/clang')


def _reject_acl(path):
    if sys.platform != 'darwin':
        raise ValueError('protected Apple compiler requires macOS ACL verification')
    library = ctypes.CDLL('/usr/lib/libSystem.B.dylib', use_errno=True)
    library.acl_get_file.argtypes = [ctypes.c_char_p, ctypes.c_int]
    library.acl_get_file.restype = ctypes.c_void_p
    library.acl_free.argtypes = [ctypes.c_void_p]
    ctypes.set_errno(0)
    acl = library.acl_get_file(os.fsencode(path), 0x100)  # ACL_TYPE_EXTENDED
    if acl:
        library.acl_free(acl)
        raise ValueError('compiler path has an extended ACL')
    # macOS reports ENOENT when this existing path has no extended ACL.
    if ctypes.get_errno() != errno.ENOENT:
        raise ValueError('compiler path ACL inspection failed')


def compiler_environment():
    # Do not inherit dyld, clang driver overrides, plugin/configuration paths,
    # include paths or user toolchain selection from the invoking environment.
    return {'PATH': '/usr/bin:/bin', 'HOME': '/var/empty', 'LC_ALL': 'C',
            'CLANG_NO_DEFAULT_CONFIG': '1'}


def compiler_path(expected_sha256=COMPILER_SHA256):
    """Bind launches against an unprivileged PATH/checkout writer.

    Root ownership of the file and all ancestors prevents such a writer from
    replacing it after authentication. Administrative toolchain replacement
    is outside this boundary. Keep the installed path for Clang resource lookup.
    """
    selected = shutil.which('clang')
    if selected is None:
        raise ValueError('clang unavailable')
    path = Path(selected).resolve(strict=True)
    if path == Path('/usr/bin/clang'):
        path = APPLE_COMPILER.resolve(strict=True)
    with path.open('rb') as stream:
        info = os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode):
            raise ValueError('compiler must be a regular file')
        digest = hashlib.sha256()
        for chunk in iter(lambda: stream.read(1 << 20), b''):
            digest.update(chunk)
    if digest.hexdigest() != expected_sha256:
        raise ValueError('compiler binary drift')
    for entry in (path, *path.parents):
        info = entry.stat()
        if info.st_uid != 0 or info.st_mode & 0o022:
            raise ValueError('compiler path must be protected by root ownership')
        _reject_acl(entry)
    return str(path)


def run_compiler(arguments, **kwargs):
    return subprocess.run([compiler_path(), *arguments],
                          env=compiler_environment(), **kwargs)
