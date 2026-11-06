#!/usr/bin/env python3
"""Add observation-only ARM9 counters to an exact pinned melonDS checkout."""
from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path, PurePosixPath
import stat
import subprocess
import sys
import tempfile


EXPECTED_REVISION = "906e9ebb27da8c6a715cd7abab4abfe8a8d29427"
PATCHED_PATHS = ("src/ARM.cpp", "src/NDS.cpp")


class CheckoutError(ValueError):
    pass


def _git(source: Path, *args: str) -> bytes:
    env = os.environ.copy()
    env["GIT_CONFIG_NOSYSTEM"] = "1"
    env["GIT_CONFIG_GLOBAL"] = os.devnull
    env["GIT_NO_REPLACE_OBJECTS"] = "1"
    env["GIT_OPTIONAL_LOCKS"] = "0"
    command = [
        "git",
        "-c", "core.fsmonitor=false",
        "-c", "core.hooksPath=/dev/null",
        "-c", "core.untrackedCache=false",
        "-C", str(source),
        *args,
    ]
    try:
        return subprocess.check_output(command, env=env)
    except (OSError, subprocess.CalledProcessError) as exc:
        raise CheckoutError(f"Cannot inspect melonDS checkout: {exc}") from exc


def _instrument_nds(pristine: str) -> str:
    include = '#include "ARMJIT_Memory.h"'
    hook = "void NDS::MonitorARM9Jump(u32 addr)\n{"
    if pristine.count(include) != 1 or pristine.count(hook) != 1:
        raise CheckoutError("Pinned NDS.cpp observation anchors changed")
    result = pristine.replace(
        include,
        include + '\n#ifdef HG_RUNTIME_TRACE\n#include "hg_trace.h"\n#endif',
    )
    return result.replace(
        hook,
        hook
        + "\n#ifdef HG_RUNTIME_TRACE"
        + "\n    if (HGTrace::Enabled && (addr & ~1u) == 0x02000DAC)"
        + " ++HGTrace::MainLoopJumps;"
        + "\n#endif",
    )


def _instrument_arm(pristine: str) -> str:
    include = '#include "ARMJIT_Memory.h"'
    execute = """                // actually execute
                if (CheckCondition(CurInstr >> 28))"""
    execute_instrumented = """                // actually execute
#ifdef HG_RUNTIME_TRACE
                const u32 hgAddress = R[15] - 8;
                const bool hgTrace = HGTrace::Enabled &&
                    (hgAddress == 0x020D3FA8 || hgAddress == 0x020DE16C);
                const u32 hgR10Before = hgTrace ? R[10] : 0;
                const bool hgCondition = hgTrace && CheckCondition(CurInstr >> 28);
#endif
                if (CheckCondition(CurInstr >> 28))"""
    end = """                else
                    AddCycles_C();
            }

            // TODO optimize this shit!!!"""
    end_instrumented = """                else
                    AddCycles_C();
#ifdef HG_RUNTIME_TRACE
                if (hgTrace)
                    HGTrace::Record(hgAddress, hgCondition, hgR10Before, R[10], CurInstr);
#endif
            }

            // TODO optimize this shit!!!"""
    if pristine.count(include) != 1:
        raise CheckoutError("Pinned ARM.cpp include anchor changed")
    if pristine.count(execute) != 2 or pristine.count(end) != 2:
        raise CheckoutError("Pinned ARM.cpp interpreter anchors changed")
    result = pristine.replace(
        include,
        include + '\n#ifdef HG_RUNTIME_TRACE\n#include "hg_trace.h"\n#endif',
    )
    result = result.replace(execute, execute_instrumented, 1)
    return result.replace(end, end_instrumented, 1)


def _tree_manifest(source: Path) -> dict[str, tuple[str, str]]:
    raw = _git(source, "ls-tree", "-r", "-z", "--full-tree", EXPECTED_REVISION)
    manifest = {}
    for record in raw.split(b"\0"):
        if not record:
            continue
        try:
            metadata, raw_path = record.split(b"\t", 1)
            mode, kind, oid = metadata.split(b" ", 2)
        except ValueError as exc:
            raise CheckoutError("Malformed pinned Git tree record") from exc
        path = os.fsdecode(raw_path)
        pure = PurePosixPath(path)
        if pure.is_absolute() or ".." in pure.parts or pure.as_posix() != path:
            raise CheckoutError(f"Unsafe path in pinned Git tree: {path!r}")
        if kind != b"blob" or mode not in {b"100644", b"100755", b"120000"}:
            raise CheckoutError(f"Unsupported pinned Git tree entry: {mode!r} {kind!r} {path!r}")
        if path in manifest:
            raise CheckoutError(f"Duplicate path in pinned Git tree: {path!r}")
        manifest[path] = (mode.decode("ascii"), oid.decode("ascii"))
    if not manifest:
        raise CheckoutError("Pinned Git tree is empty")
    return manifest


def _expected_sources(
    source: Path,
    manifest: dict[str, tuple[str, str]],
) -> tuple[dict[str, bytes], dict[str, bytes]]:
    missing = [name for name in PATCHED_PATHS if name not in manifest]
    if missing:
        raise CheckoutError(f"Pinned Git tree lacks observation sources: {', '.join(missing)}")
    pristine = {
        name: _git(source, "cat-file", "blob", manifest[name][1])
        for name in PATCHED_PATHS
    }
    try:
        patched = {
            "src/ARM.cpp": _instrument_arm(pristine["src/ARM.cpp"].decode("utf-8")).encode("utf-8"),
            "src/NDS.cpp": _instrument_nds(pristine["src/NDS.cpp"].decode("utf-8")).encode("utf-8"),
        }
    except UnicodeDecodeError as exc:
        raise CheckoutError("Pinned melonDS sources are not UTF-8") from exc
    return pristine, patched


def _working_tree_entries(source: Path) -> tuple[set[str], set[str]]:
    files = set()
    directories = set()
    for current, names, filenames in os.walk(source, topdown=True, followlinks=False):
        current_path = Path(current)
        if current_path == source:
            names[:] = [name for name in names if name != ".git"]
            filenames = [name for name in filenames if name != ".git"]
        for name in list(names):
            path = current_path / name
            relative = path.relative_to(source).as_posix()
            if path.is_symlink():
                files.add(relative)
                names.remove(name)
            else:
                directories.add(relative)
        for name in filenames:
            files.add((current_path / name).relative_to(source).as_posix())
    return files, directories


def _read_regular_file(path: Path) -> tuple[bytes, os.stat_result]:
    flags = os.O_RDONLY
    if hasattr(os, "O_CLOEXEC"):
        flags |= os.O_CLOEXEC
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise CheckoutError(f"Cannot open checkout file without following links: {path}") from exc
    try:
        info = os.fstat(descriptor)
        if not stat.S_ISREG(info.st_mode):
            raise CheckoutError(f"Checkout path is not a regular file: {path}")
        if info.st_nlink != 1:
            raise CheckoutError(f"Checkout path has shared hardlinks: {path}")
        chunks = []
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            chunks.append(chunk)
        return b"".join(chunks), info
    finally:
        os.close(descriptor)


def _git_blob_oid(data: bytes) -> str:
    framed = b"blob " + str(len(data)).encode("ascii") + b"\0" + data
    return hashlib.sha1(framed).hexdigest()


def _replace_regular_file(path: Path, data: bytes) -> None:
    current, info = _read_regular_file(path)
    if current == data:
        return
    descriptor, temporary_name = tempfile.mkstemp(prefix=".sgp-core-patch-", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        os.fchmod(descriptor, stat.S_IMODE(info.st_mode))
        view = memoryview(data)
        while view:
            written = os.write(descriptor, view)
            if written <= 0:
                raise CheckoutError(f"Short write while patching checkout source: {path}")
            view = view[written:]
        os.fsync(descriptor)
        os.close(descriptor)
        descriptor = -1
        os.replace(temporary, path)
    except OSError as exc:
        raise CheckoutError(f"Cannot atomically patch checkout source {path}: {exc}") from exc
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def _verify_manifest(
    source: Path,
    manifest: dict[str, tuple[str, str]],
    pristine: dict[str, bytes],
    patched: dict[str, bytes],
    *,
    require_patched: bool,
) -> None:
    actual_files, actual_directories = _working_tree_entries(source)
    expected_files = set(manifest)
    expected_directories = {
        parent.as_posix()
        for name in expected_files
        for parent in PurePosixPath(name).parents
        if parent.as_posix() != "."
    }
    extra_files = sorted(actual_files - expected_files)
    missing_files = sorted(expected_files - actual_files)
    extra_directories = sorted(actual_directories - expected_directories)
    if extra_files or missing_files or extra_directories:
        detail = []
        if extra_files:
            detail.append("extra files: " + ", ".join(extra_files[:5]))
        if missing_files:
            detail.append("missing files: " + ", ".join(missing_files[:5]))
        if extra_directories:
            detail.append("extra directories: " + ", ".join(extra_directories[:5]))
        raise CheckoutError("Checkout tree differs from the pinned tree (" + "; ".join(detail) + ")")

    for name, (mode, oid) in manifest.items():
        path = source / name
        if mode == "120000":
            if not path.is_symlink():
                raise CheckoutError(f"Checkout path is not the pinned symlink: {name}")
            data = os.fsencode(os.readlink(path))
            info = path.lstat()
        else:
            if path.is_symlink():
                raise CheckoutError(f"Checkout path unexpectedly follows a symlink: {name}")
            data, info = _read_regular_file(path)
            executable = bool(info.st_mode & 0o111)
            if executable != (mode == "100755"):
                raise CheckoutError(f"Checkout executable mode differs from the pinned tree: {name}")

        if name in PATCHED_PATHS:
            allowed = {patched[name]} if require_patched else {pristine[name], patched[name]}
            if data not in allowed:
                raise CheckoutError(f"Checkout source {name} does not match the exact approved state")
        elif _git_blob_oid(data) != oid:
            raise CheckoutError(f"Checkout file differs from the pinned tree: {name}")


def verify_checkout(source: Path, *, require_patched: bool) -> dict[str, bytes]:
    source = source.resolve()
    revision = _git(source, "rev-parse", "HEAD").decode("ascii").strip()
    if revision != EXPECTED_REVISION:
        raise CheckoutError(f"Expected source {EXPECTED_REVISION}, got {revision}")
    top = Path(_git(source, "rev-parse", "--show-toplevel").decode().strip()).resolve()
    if top != source:
        raise CheckoutError(f"Checkout source must be its repository root: {top}")

    manifest = _tree_manifest(source)
    pristine, patched = _expected_sources(source, manifest)
    _verify_manifest(
        source,
        manifest,
        pristine,
        patched,
        require_patched=require_patched,
    )
    return patched


def patch_core(source: Path) -> None:
    patched = verify_checkout(source, require_patched=False)
    source = source.resolve()
    for name in ("src/NDS.cpp", "src/ARM.cpp"):
        path = source / name
        current, _ = _read_regular_file(path)
        if current == patched[name]:
            print(f"Exact observation patch already present in {name}")
            continue
        _replace_regular_file(path, patched[name])
        print(f"Patched {name} with observation-only hooks")
    verify_checkout(source, require_patched=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source",
        type=Path,
        required=True,
        help="Separate melonDS checkout at the pinned revision",
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Require the exact pinned checkout plus the exact observation patch",
    )
    args = parser.parse_args(argv)
    try:
        if args.verify_only:
            verify_checkout(args.source, require_patched=True)
            print("Pinned melonDS checkout and observation patch verified")
        else:
            patch_core(args.source)
    except CheckoutError as exc:
        print(f"Rejected melonDS checkout: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
