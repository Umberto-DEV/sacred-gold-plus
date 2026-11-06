"""SG-SV01: make the two Plus-option writes observable and truthful.

The historical 1.2.x blob remains immutable.  The 1.3.1 stage recompiles the
same reviewed source with ``SGP_SAVE_WRITE_STATUS_FIX``, replaces its fixed
ARM9 compartment and retargets the existing save call to the successor entry.
Save layout, call-site address and vanilla return values do not change.
"""
import hashlib
import importlib.util
from pathlib import Path
import shutil
import subprocess
import tempfile

from sgp12.rom import Arm9, bl_decode, bl_thumb
from sgp13.compiler import compiler_environment, compiler_path


SOURCE = Path(__file__).resolve().parents[1]
NATIVE = SOURCE / 'features/native-core/sorgenti-v-finale/salva_blob.c'
LOADER = SOURCE / 'features/options/tools/carica_text.py'
HISTORICAL = SOURCE / 'sgp12/build/plus/salva_blob.bin'

BASE = 0x023D8220
CAPACITY = 0x2E0
HOOK = 0x02027456
HOOK_OLD_TARGET = 0x023D8330
HOOK_NEW_TARGET = 0x023D8370
HOOK_PREIMAGE = bytes.fromhex('b0f36bff')
HOOK_POSTIMAGE = bytes.fromhex('b0f38bff')
ENTRY_LOAD = 'sgp_gancio_carica'
ENTRY_SAVE = 'sgp_gancio_salva'
ENTRIES = (ENTRY_LOAD, ENTRY_SAVE)
HISTORICAL_BYTES = 500
HISTORICAL_SHA256 = 'f408c76327aeefaf0f994b9d47f694930f47588e5e8290084516dfb8dcef167d'
PREIMAGE_SHA256 = 'b60075d45045d53fb466587465352c134ca8cf05baccd8622790946ddbaa26f6'
PAYLOAD_BYTES = 608
PAYLOAD_SHA256 = 'f6d42c2d9001c5f3a92faf223bdbea6eb0a4aa04cdccfe7a0bfd689a9c5c4c4d'
POSTIMAGE_SHA256 = 'c6a787f0732e2f3a89f4f39187c894d688d3e68f1356e83d39fd88fb8096e7b6'
COMPILER_VERSION = 'Apple clang version 21.0.0 (clang-2100.4.1.1)'
COMPILER_SHA256 = 'fc5e3cbba6ad54059295cad716aacb05ace8235f5f7a6031f1d8c15d24bd6d66'
FLAGS = ['--target=armv5te-none-eabi', '-mcpu=arm946e-s', '-mthumb', '-Oz',
         '-ffreestanding', '-fno-builtin', '-fno-stack-protector', '-fno-unwind-tables',
         '-fno-asynchronous-unwind-tables', '-fno-jump-tables',
         '-DSGP_PLUS_BASE=0x23d8100u', '-DSGP_BUF_ADDR=0x23d8f00u',
         '-DSGP_SAVE_WRITE_STATUS_FIX=1']
FREE_SPACE_FLOOR = 10 * 1024 ** 3
LANGUAGES = ('EN', 'IT')


def _need(ok, reason):
    if not ok:
        raise ValueError('Plus save: ' + reason)


def _sha(data):
    return hashlib.sha256(bytes(data)).hexdigest()


def _module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def compile_native(work_dir):
    """Compile the exact successor payload with the authenticated toolchain."""
    work_dir = Path(work_dir)
    _need(shutil.disk_usage(work_dir).free >= FREE_SPACE_FLOOR, 'free-space floor (10 GiB)')
    compiler = compiler_path(COMPILER_SHA256)
    version = subprocess.run([compiler, '--version'], env=compiler_environment(),
                             capture_output=True, text=True, check=True).stdout.splitlines()[0]
    _need(version == COMPILER_VERSION, 'compiler version drift: ' + version)
    _need(_sha(Path(compiler).read_bytes()) == COMPILER_SHA256, 'compiler binary drift')
    with tempfile.TemporaryDirectory(prefix='plus-save-', dir=work_dir) as scratch:
        obj = Path(scratch) / 'salva.o'
        command = [compiler, *FLAGS, '-c', str(NATIVE), '-o', str(obj)]
        result = subprocess.run(command, cwd=scratch, env=compiler_environment(),
                                capture_output=True, text=True, timeout=60)
        _need(result.returncode == 0 and not result.stderr,
              'native compile failed: ' + result.stderr)
        raw = obj.read_bytes()
    payload, symbols = _module(LOADER, 'plus_save_loader').load_text(raw, BASE, ENTRIES)
    _need(len(payload) == PAYLOAD_BYTES and _sha(payload) == PAYLOAD_SHA256,
          'successor payload drift: %d B %s' % (len(payload), _sha(payload)))
    entries = {name: symbols.get(name) for name in ENTRIES}
    _need(entries == {ENTRY_LOAD: BASE | 1, ENTRY_SAVE: HOOK_NEW_TARGET | 1},
          'successor entry addresses drift')
    return payload, {
        'bytes': len(payload), 'sha256': _sha(payload),
        'symbols': {key: entries[key] for key in ENTRIES},
        'source_sha256': _sha(NATIVE.read_bytes()), 'object_sha256': _sha(raw),
        'compiler': {'version': version, 'executable_sha256': COMPILER_SHA256,
                     'flags': list(FLAGS)},
    }


def _preimage(arm):
    historical = HISTORICAL.read_bytes()
    _need(len(historical) == HISTORICAL_BYTES and _sha(historical) == HISTORICAL_SHA256,
          'historical fixture identity')
    region = arm.leggi(BASE, CAPACITY)
    _need(_sha(region) == PREIMAGE_SHA256, 'compartment preimage changed or already patched')
    _need(region == historical + bytes(CAPACITY - HISTORICAL_BYTES),
          'compartment is not the historical blob followed by zero fill')
    _need(arm.leggi(HOOK, 4) == HOOK_PREIMAGE
          and bl_decode(HOOK, HOOK_PREIMAGE) == HOOK_OLD_TARGET,
          'save hook no longer targets the reviewed entry')
    return region


def apply(data, language, *, work_dir=None):
    _need(type(data) is bytes and language in LANGUAGES, 'input/language')
    arm = Arm9.from_bytes(data)
    before = _preimage(arm)
    owner = Path(work_dir) if work_dir is not None else Path('/tmp')
    payload, compiled = compile_native(owner)
    installed = payload + bytes(CAPACITY - len(payload))
    _need(_sha(installed) == POSTIMAGE_SHA256, 'installed compartment digest')
    arm.scrivi(BASE, installed)
    hook = bl_thumb(HOOK, compiled['symbols'][ENTRY_SAVE] & ~1)
    _need(hook == HOOK_POSTIMAGE, 'successor hook encoding drift')
    arm.scrivi(HOOK, hook)
    out = bytes(arm.raw)
    receipt = {
        'stage': 'plus-save', 'language': language,
        'input_sha256': _sha(data), 'output_sha256': _sha(out),
        'address': BASE, 'capacity': CAPACITY,
        'hook_address': HOOK, 'hook_preimage': HOOK_PREIMAGE.hex(),
        'hook_postimage': HOOK_POSTIMAGE.hex(),
        'preimage_sha256': _sha(before), 'postimage_sha256': _sha(installed),
        'compiled': compiled, 'save_layout_unchanged': True,
        'vanilla_return_unchanged': True,
    }
    receipt['verification'] = verify(data, out, receipt)
    return out, receipt


def verify(before, after, receipt):
    _need(type(before) is bytes and type(after) is bytes and len(before) == len(after),
          'image geometry')
    old, new = Arm9.from_bytes(before), Arm9.from_bytes(after)
    pre = _preimage(old)
    post = new.leggi(BASE, CAPACITY)
    _need(_sha(post) == POSTIMAGE_SHA256 and _sha(post[:PAYLOAD_BYTES]) == PAYLOAD_SHA256,
          'successor compartment readback')
    _need(post[PAYLOAD_BYTES:] == bytes(CAPACITY - PAYLOAD_BYTES), 'successor zero fill')
    _need(new.leggi(HOOK, 4) == HOOK_POSTIMAGE
          and bl_decode(HOOK, HOOK_POSTIMAGE) == HOOK_NEW_TARGET,
          'successor save hook readback')
    start = old.off(BASE, CAPACITY)
    hook_at = old.off(HOOK, 4)
    restored = bytearray(after)
    restored[start:start + CAPACITY] = pre
    restored[hook_at:hook_at + 4] = HOOK_PREIMAGE
    _need(bytes(restored) == before,
          'bytes changed outside the Plus-save compartment and save hook')
    _need(type(receipt) is dict and receipt.get('stage') == 'plus-save'
          and receipt.get('language') in LANGUAGES
          and receipt.get('input_sha256') == _sha(before)
          and receipt.get('output_sha256') == _sha(after)
          and receipt.get('preimage_sha256') == PREIMAGE_SHA256
          and receipt.get('postimage_sha256') == POSTIMAGE_SHA256
          and receipt.get('hook_address') == HOOK
          and receipt.get('hook_preimage') == HOOK_PREIMAGE.hex()
          and receipt.get('hook_postimage') == HOOK_POSTIMAGE.hex(),
          'receipt identity')
    return {'ok': True, 'address': BASE, 'bytes': CAPACITY, 'hook_address': HOOK,
            'payload_bytes': PAYLOAD_BYTES, 'payload_sha256': PAYLOAD_SHA256,
            'save_layout_unchanged': True, 'hook_retargeted': True,
            'vanilla_return_unchanged': True}


def span(data):
    arm = Arm9.from_bytes(bytes(data))
    at = arm.off(BASE, CAPACITY)
    return at, at + CAPACITY


def spans(data):
    """Physical byte ranges owned by this successor stage."""
    arm = Arm9.from_bytes(bytes(data))
    compartment = span(data)
    hook = arm.off(HOOK, 4)
    return (compartment, (hook, hook + 4))
