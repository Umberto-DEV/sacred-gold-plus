"""Build the r5/lease ROM fixtures the native-guide tests need, on this machine.

The suite used to point at ROMs left over in a scratch directory by earlier, unrelated
sessions (see private development notes (ex 01-AUDIT-1.1.md), §I4/R4): a scratchpad wiped on
reboot, so 5 of 11 tests errored with FileNotFoundError for anyone else, or
after any reboot. This module builds the same fixtures fresh, from files that
already live in this checkout (a recognized 1.04 Plus ROM plus the pinned pret
charmap), under a fresh directory it creates itself. build_lease_rom.build()
requires its output directory to sit outside this checkout, so the fixture
directory is created under the platform temporary directory and removed again
in tearDownModule.

Needs the venv interpreter documented in native-eviv/README.md
(python3 (vedi source/requirements.txt): ndspy + Pillow) and a
working `clang` with the ARM target, per the same README. Skips with a clear
reason instead of failing when the source ROM or the charmap is not present
locally -- both are external inputs, never committed to git.
"""
import shutil
import os
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent          # source/native-guide
# Le ROM di prova e la charmap di pret non stanno in questo repository:
# si indicano con SGP_ROM_DIR e SGP_CHARMAP (vedi source/README.md).
ROM_DIR = Path(os.environ.get("SGP_ROM_DIR", "rom-dir-not-set"))
NATIVE_EVIV = HERE.parents[0] / 'native-eviv'    # source/native-eviv
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(NATIVE_EVIV))

import build_test_rom  # noqa: E402  (native-eviv)
import build_lease_rom  # noqa: E402  (native-guide)

# The only source build_lease_rom.BASES/build_test_rom.KNOWN both accept that
# this checkout carries in full: the recognized 1.04 US Plus (New Angle) ROM.
SOURCE_SHA256 = '3ed4ea0291092d46def2f71454821bbde7832014ec020680468af7bfca686248'
SOURCE_CANDIDATES = [
    ROM_DIR / 'us-retail-to-en-plus.nds',
    ROM_DIR / 'plus103-to-en-plus.nds',
]
# The pinned pret charmap (CHARMAP_SHA in build_test_rom.py) is an external
# input like the ROMs: not tracked at a stable path. These are the copies
# this checkout happens to carry, kept from earlier lab handoffs.
CHARMAP_CANDIDATES = [
    Path(os.environ.get('SGP_CHARMAP', 'charmap-not-set')),
    ROM_DIR / 'charmap.txt',
]


def _first_existing(candidates):
    for path in candidates:
        if path.is_file():
            return path
    return None


def locate_inputs():
    """Return (source, charmap) paths, or (None, reason) if either is missing."""
    source = _first_existing(SOURCE_CANDIDATES)
    if source is None:
        return None, 'no local 1.04 US Plus ROM found (see SOURCE_CANDIDATES)'
    charmap = _first_existing(CHARMAP_CANDIDATES)
    if charmap is None:
        return None, 'no local pret charmap.txt found (see CHARMAP_CANDIDATES)'
    return (source, charmap), None


_workdir = None


def _fresh_workdir():
    global _workdir
    if _workdir is None:
        _workdir = Path(tempfile.mkdtemp(prefix='sgpc-native-guide-tests-'))
    return _workdir


def cleanup():
    global _workdir, _r5_rom_path, _lease_build
    if _workdir is not None and _workdir.exists():
        shutil.rmtree(_workdir, ignore_errors=True)
    _workdir = None
    _r5_rom_path = None
    _lease_build = None


_r5_rom_path = None
_lease_build = None


def require_inputs_or_skip(test):
    inputs, reason = locate_inputs()
    if inputs is None:
        test.skipTest('native-guide fixture cannot be built locally: ' + reason)
    return inputs


def r5_rom_path(test):
    """Build (once) the plain r5 EV/IV pilot ROM and return its path."""
    global _r5_rom_path
    if _r5_rom_path is None:
        (source, charmap) = require_inputs_or_skip(test)
        out = _fresh_workdir() / 'r5'
        meta = build_test_rom.build(source, charmap, out)
        _r5_rom_path = out / meta['rom_file']
    return _r5_rom_path


def r5_arm9(test):
    """Load a fresh MainCodeFile for the plain r5 ROM (mutated freely by tests)."""
    from ndspy.rom import NintendoDSRom
    return NintendoDSRom.fromFile(str(r5_rom_path(test))).loadArm9()


def lease_build(test):
    """Build (once) the full lease-gate ROM and return (rom_path, build_json_path)."""
    global _lease_build
    if _lease_build is None:
        (source, charmap) = require_inputs_or_skip(test)
        out = _fresh_workdir() / 'lease'
        meta = build_lease_rom.build(source, charmap, out)
        _lease_build = (out / meta['rom_file'], out / 'build.json')
    return _lease_build
