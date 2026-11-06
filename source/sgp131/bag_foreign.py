"""Refuse a lossy expanded-Bag native commit without changing Bag ABI.

The shipped Bag writer already preserves foreign destination bytes and records
status 2.  It also records status 3 when neither write verifies and status 4
when the destination cannot be read.  The successor Training coordinator
interprets all three statuses before the native save: it returns the existing
recoverable failure only when one of the 108 expanded cells is live.  An empty
extension may still commit.  Status 5 may commit because one verified copy of
the extension exists in the destination bank.

The Bag blob and its hook remain byte-identical.  This stage replaces only the
fixed Training code compartment in ARM9; its config, state, hooks and save
layouts are unchanged.
"""
from __future__ import annotations

import hashlib
import shutil
import struct
import tempfile
from pathlib import Path

from sgp12.rom import Arm9, bl_decode
from sgp13 import training
from sgp13.compiler import run_compiler


BASE = training.BASE
CAPACITY = training.CONFIG - training.BASE
HOOK = 0x023DCC9C
HOOK_BYTES = bytes.fromhex('10b5f4f71dfc10bd')
HOOK_TARGET = 0x023D14DC
LANGUAGES = ('EN', 'IT')
PREIMAGE_SHA256 = '79317ea6485c9f1d38b69c6554dab5ddaac4c5ce417d1420b6bb28c5f19d8332'
BASELINE_BYTES = 11420
BASELINE_SHA256 = '09bf05a472ec02151c5ed19ed578af519f9e186cd53cd9cf8791910b6ed49f07'
GUARD_BYTES = 184
GUARD_SHA256 = '09109786104ff74166a3d32c0d1215d1c808964ea911dc7ccf3a232dbbae49c2'
PAYLOAD_BYTES = 11604
PAYLOAD_SHA256 = 'bcf9d15d06f1e2f433b48e4aef4876f68c9a6625bcb666263a9f29a6fd7f4c8b'
POSTIMAGE_SHA256 = '336a6583ac6c530fae86992cec1dbf964e4c93d76cc25c122b7abbf4c3e7e424'
TRAINING_SAVE = 0x023D14DD
TRAINING_NATIVE_SAVE = 0x023D17AD
TRAINING_SHINY_BIND = 0x023D1A45
TRAINING_SHINY_ACCESS = 0x023D1A59
STORAGE_READY = 0x023D1B1D
ENTRY_PATCH = bytes.fromhex('004b1847312e3d02')
FREE_SPACE_FLOOR = 10 * 1024 ** 3


def _need(condition, message):
    if not condition:
        raise ValueError('Bag foreign: ' + message)


def _sha(data):
    return hashlib.sha256(bytes(data)).hexdigest()


def _compile_guard(work_dir, base):
    obj = Path(work_dir) / 'bag-foreign-guard.o'
    flags = ['--target=armv5te-none-eabi', '-mcpu=arm946e-s', '-mthumb',
             '-Oz', '-ffreestanding', '-fno-builtin', '-fno-stack-protector',
             '-fno-jump-tables', '-fno-unwind-tables',
             '-fno-asynchronous-unwind-tables', '-Wall', '-Wextra', '-Werror']
    run_compiler([*flags, '-c', str(training.ROOT /
                 'features/training-native/bag_foreign_guard.c'), '-o', str(obj)],
                 check=True, capture_output=True)
    loader = training.module(training.ROOT /
                             'features/options/tools/carica_text.py',
                             'bag_foreign_guard_loader')
    return loader.load_text(obj.read_bytes(), base, ('bag_foreign_guard',))


def compile_successor(work_dir):
    work_dir = Path(work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)
    _need(shutil.disk_usage(work_dir).free >= FREE_SPACE_FLOOR,
          'free-space floor (10 GiB)')
    baseline, symbols = training.compile_native(work_dir / 'training')
    _need(len(baseline) == BASELINE_BYTES and _sha(baseline) == BASELINE_SHA256,
          'Training ABI baseline drift: %d B %s' %
          (len(baseline), _sha(baseline)))
    _need(symbols.get('training_save') == TRAINING_SAVE
          and symbols.get('training_native_save') == TRAINING_NATIVE_SAVE
          and symbols.get('training_shiny_bind') == TRAINING_SHINY_BIND
          and symbols.get('training_shiny_access') == TRAINING_SHINY_ACCESS
          and symbols.get('storage_ready') == STORAGE_READY,
          'public Training capability geometry drift')
    guard, guard_symbols = _compile_guard(work_dir, BASE + len(baseline))
    _need(len(guard) == GUARD_BYTES and _sha(guard) == GUARD_SHA256,
          'Bag foreign guard drift: %d B %s' % (len(guard), _sha(guard)))
    payload = bytearray(baseline)
    entry = (symbols['training_save'] & ~1) - BASE
    patch = b'\x00\x4b\x18\x47' + struct.pack(
        '<I', guard_symbols['bag_foreign_guard'] | 1)
    _need(patch == ENTRY_PATCH, 'Bag foreign entry geometry drift')
    payload[entry:entry + len(patch)] = patch
    payload.extend(guard)
    payload = bytes(payload)
    _need(len(payload) == PAYLOAD_BYTES and _sha(payload) == PAYLOAD_SHA256,
          'successor payload drift: %d B %s' % (len(payload), _sha(payload)))
    installed = payload + bytes(CAPACITY - len(payload))
    _need(_sha(installed) == POSTIMAGE_SHA256,
          'installed compartment drift: %s' % _sha(installed))
    return installed, {
        'bytes': len(payload), 'payload_sha256': _sha(payload),
        'installed_sha256': _sha(installed),
        'baseline_bytes': len(baseline),
        'baseline_sha256': _sha(baseline),
        'guard_bytes': len(guard), 'guard_sha256': _sha(guard),
        'guard_entry': guard_symbols['bag_foreign_guard'],
        'entry_patch': patch.hex(), 'public_abi_preserved': True,
        'training_save': symbols['training_save'],
        'training_native_save': symbols['training_native_save'],
        'training_shiny_bind': symbols['training_shiny_bind'],
        'training_shiny_access': symbols['training_shiny_access'],
        'storage_ready': symbols['storage_ready'],
        'source_sha256': _sha(training.ROOT.joinpath(
            'features/training-native/bag_foreign_guard.c').read_bytes()),
    }


def _preimage(arm):
    region = arm.leggi(BASE, CAPACITY)
    _need(_sha(region) == PREIMAGE_SHA256,
          'Training compartment preimage changed or already patched')
    hook = arm.leggi(HOOK, len(HOOK_BYTES))
    _need(hook == HOOK_BYTES
          and bl_decode(HOOK + 2, hook[2:6]) == HOOK_TARGET,
          'Bag-to-Training save hook differs')
    return region


def apply(data, language, *, work_dir=None):
    _need(type(data) is bytes and language in LANGUAGES, 'input/language')
    arm = Arm9.from_bytes(data)
    before = _preimage(arm)
    owner = Path(work_dir) if work_dir is not None else Path('/tmp')
    installed, compiled = compile_successor(owner)
    arm.scrivi(BASE, installed)
    result = bytes(arm.raw)
    receipt = {
        'stage': 'bag-foreign', 'language': language,
        'input_sha256': _sha(data), 'output_sha256': _sha(result),
        'address': BASE, 'capacity': CAPACITY,
        'preimage_sha256': _sha(before),
        'postimage_sha256': _sha(installed),
        'hook_address': HOOK, 'hook_unchanged': HOOK_BYTES.hex(),
        'bag_blob_unchanged': True, 'save_layout_unchanged': True,
        'compiled': compiled,
    }
    receipt['verification'] = verify(data, result, receipt)
    return result, receipt


def verify(before, after, receipt):
    _need(type(before) is bytes and type(after) is bytes
          and len(before) == len(after), 'image geometry')
    old, new = Arm9.from_bytes(before), Arm9.from_bytes(after)
    pre = _preimage(old)
    post = new.leggi(BASE, CAPACITY)
    _need(_sha(post) == POSTIMAGE_SHA256
          and _sha(post[:PAYLOAD_BYTES]) == PAYLOAD_SHA256,
          'successor compartment readback')
    entry = (TRAINING_SAVE & ~1) - BASE
    _need(post[entry:entry + len(ENTRY_PATCH)] == ENTRY_PATCH,
          'Bag foreign entry patch readback')
    _need(post[PAYLOAD_BYTES:] == bytes(CAPACITY - PAYLOAD_BYTES),
          'successor zero fill')
    _need(new.leggi(HOOK, len(HOOK_BYTES)) == HOOK_BYTES,
          'save hook changed')
    start = old.off(BASE, CAPACITY)
    restored = bytearray(after)
    restored[start:start + CAPACITY] = pre
    _need(bytes(restored) == before,
          'bytes changed outside the Training code compartment')
    _need(type(receipt) is dict and receipt.get('stage') == 'bag-foreign'
          and receipt.get('language') in LANGUAGES
          and receipt.get('input_sha256') == _sha(before)
          and receipt.get('output_sha256') == _sha(after)
          and receipt.get('preimage_sha256') == PREIMAGE_SHA256
          and receipt.get('postimage_sha256') == POSTIMAGE_SHA256
          and receipt.get('hook_unchanged') == HOOK_BYTES.hex()
          and receipt.get('bag_blob_unchanged') is True
          and receipt.get('save_layout_unchanged') is True,
          'receipt identity')
    return {'ok': True, 'address': BASE, 'bytes': CAPACITY,
            'payload_bytes': PAYLOAD_BYTES, 'payload_sha256': PAYLOAD_SHA256,
            'entry_patch': ENTRY_PATCH.hex(), 'public_abi_preserved': True,
            'hook_unchanged': True, 'bag_blob_unchanged': True,
            'save_layout_unchanged': True}


def spans(data):
    arm = Arm9.from_bytes(bytes(data))
    start = arm.off(BASE, CAPACITY)
    return ((start, start + CAPACITY),)
