"""Portable box (party -> native PC mode 2 -> rebuilt party) for Sacred Gold Plus 1.3.1.

Parametric installer: the compartment base comes only from a `reserve.allocate`
receipt (never chosen here, never a free-form address). Every hook is installed in
its guarded form and the activation words in the compartment default to zero, so a
freshly installed ROM behaves like the native one until Codex flips a word after
the Android proof. The module pins byte intervals (hook sites, native prefixes,
literals), never the whole ROM, so it composes after any stage that leaves them
alone. The ROM is read and patched in memory only.

  prepare(data, language, work, *, allocation, preimage_sha256, activation=None, context_proof=None,
          candidate_sha256=None, allow_synthetic_proof=False) -> (patched ROM bytes, receipt)
  verify(before, after, receipt) -> dict

Evidence levels (see source/docs/portable-box-1.3.1.md): host Python, ARM
instructions executed by Unicorn on the real V4 bytes, Android (absent here).
"""
import copy
import hashlib
import json
import re
import shutil
import struct
import subprocess
from sgp13.compiler import compiler_path, compiler_environment
import tempfile
from pathlib import Path

from sgp12.rom import bl_decode, bl_thumb, valida_layout_arm9
from . import baseline, reserve

SOURCE = Path(__file__).resolve().parents[1]
FEATURE = SOURCE / 'features' / 'portable-box'
RUNTIME = FEATURE / 'runtime.c'
ABI_JSON = Path(__file__).with_name('data') / 'portable-native-abi.json'
LANGUAGES = ('EN', 'IT')
V4_SHA256 = {
    'EN': '179edfb1ca331503f438e98f3afccfb0ab85759bf9ab88fb86c735f5fcefbf90',
    'IT': '2a2f0b437fca524c18b71b20feb01a1f51351e61c7c897ce73d9b3be1ee3a156',
}

# Hook sites (complete Thumb BL pairs unless noted) and the entries they reach.
STATE1_BL = 0x0207909C         # BL MainNormal            -> sgp_box_party_main
LAUNCH_BL = 0x0203E572         # BL FieldSystem_LaunchApp -> sgp_box_launch_app (inside PartyMenu_LaunchApp_Unk1)
PRINT32_BL = 0x0207DAD2        # BL PrintMessageOnWindowEx -> sgp_box_prompt_print (window 32 only)
CALLBACK = 0x0203CA9C          # Task_StartMenu_HandleReturn_Pokemon entry (8-byte hook + trampoline)
CALLBACK_RESUME = CALLBACK + 12  # first byte after the displaced push/sub/mov/BL/mov span
NATIVE_CALLBACK_PTR = 0x0203CA9D
BL_HOOKS = (
    ('state1', STATE1_BL, 'sgp_box_party_main', 0x02079308),
    ('launch', LAUNCH_BL, 'sgp_box_launch_app', 0x0203DFB4),
    ('print32', PRINT32_BL, 'sgp_box_prompt_print', 0x0207DA64),
)
CALLBACK_BEFORE = bytes.fromhex('f0b583b0071c13f0d3fd051c')
GET_FIELD_SYSTEM = 0x0205064C  # target of the BL displaced by the trampoline

ENTRIES = ('sgp_box_bind', 'sgp_box_launch_app', 'sgp_box_party_main', 'sgp_box_party_return',
           'sgp_box_pc_return', 'sgp_box_eligibility', 'sgp_box_prompt', 'sgp_box_prompt_print',
           'sgp_box_area')
FLAGS = ['--target=armv5te-none-eabi', '-mcpu=arm946e-s', '-mthumb', '-Oz', '-ffreestanding',
         '-fno-builtin', '-fno-stack-protector', '-fno-jump-tables', '-fomit-frame-pointer',
         '-fno-unwind-tables', '-fno-asynchronous-unwind-tables', '-Wall', '-Wextra', '-Werror',
         '-fstack-usage', '-std=c11']
FREE_SPACE_FLOOR = 10 * 1024 ** 3
COMPILER_VERSION = 'Apple clang version 21.0.0 (clang-2100.4.1.1)'     # same pin as controls.py
COMPILER_SHA256 = 'fc5e3cbba6ad54059295cad716aacb05ace8235f5f7a6031f1d8c15d24bd6d66'

# State / configuration layout (mirrors features/portable-box/abi.h; test_portable checks parity).
STATE_BYTES, CONFIG_BYTES = 64, 32
STATE_OFFSETS = {'magic': 0x00, 'generation': 0x04, 'phase': 0x08, 'requested': 0x0C, 'field': 0x10,
                 'owner': 0x14, 'args': 0x18, 'pc_args': 0x1C, 'selection': 0x20, 'reason': 0x24,
                 'prompt_shown': 0x28, 'request_generation': 0x2C, 'allocs': 0x30, 'frees': 0x34,
                 'opens': 0x38, 'failures': 0x3C}
CONFIG_OFFSETS = {'magic': 0x00, 'bridge': 0x04, 'input': 0x08, 'prompt': 0x0C,
                  'refresh_field_data': 0x10, 'travel_mask': 0x14, 'context_proof': 0x18}
ACTIVATION_DEFAULT = {'bridge': 0, 'input': 0, 'prompt': 0, 'travel_mask': 3, 'context_proof': 0}
TRAMPOLINE_BYTES = 0x2C


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def abi():
    return json.loads(ABI_JSON.read_text())


# ---------------------------------------------------------------- ARM9 image map

def arm9_segments(data):
    """(ram, rom offset, size) of the uncompressed ARM9 and its autoloads."""
    offset, _, base, length = struct.unpack_from('<4I', data, 0x20)
    table, table_end, body, _bss, _, packed = struct.unpack_from('<6I', data, offset + 0xBA0)
    _require(base == 0x02000000 and not packed and base < body <= table <= table_end <= base + length,
             'ARM9 initialized layout')
    _t0, _t1, _d0, _sections, segments = valida_layout_arm9(
        data, offset, base, length)
    return segments


def locate(segments, address, size):
    found = [rom + address - start for start, rom, count in segments
             if start <= address and address + size <= start + count]
    _require(len(found) == 1, 'address %#x+%d is not inside exactly one ARM9 segment' % (address, size))
    return found[0]


def read_ram(data, segments, address, size):
    at = locate(segments, address, size)
    return bytes(data[at:at + size])


# ------------------------------------------------------------------- pins / audit

def audit_native(data, language):
    """Compare the pinned V4 spans/literals/native prefixes with `data`; return a digest report."""
    _require(language in LANGUAGES, 'unsupported language')
    pins = abi()
    segments = arm9_segments(data)
    lang = pins['languages'][language]
    report = {'language': language, 'spans': {}, 'natives': {}}
    for name, span in lang['spans'].items():
        got = read_ram(data, segments, span['address'], span['bytes'])
        _require(_sha(got) == span['sha256'], 'native ABI preimage mismatch: %s at %#x' % (name, span['address']))
        report['spans'][name] = span['sha256']
    for name, native in lang['natives'].items():
        got = read_ram(data, segments, native['address'], native['prefix_bytes'])
        _require(got.hex() == native['prefix_hex'], 'native function prefix mismatch: %s at %#x' % (name, native['address']))
        report['natives'][name] = got.hex()
    for address, value in pins['literals'].items():
        _require(struct.unpack('<I', read_ram(data, segments, int(address, 16), 4))[0] == value,
                 'literal mismatch at ' + address)
    return report


# ----------------------------------------------------------------------- compile

def compile_native(work, base):
    """Compile runtime.c at `base`; return (blob, symbols, receipt). Scratch is removed on return."""
    from importlib import util
    _require(type(base) is int and base % 4 == 0 and 0x02000000 <= base < 0x02400000,
             'compartment base must be a 4-aligned main-RAM address')
    compiler = compiler_path(COMPILER_SHA256)
    _require(compiler is not None, 'clang unavailable')
    work = Path(work)
    work.mkdir(parents=True, exist_ok=True)
    _require(shutil.disk_usage(work).free >= FREE_SPACE_FLOOR, 'free-space floor (10 GiB)')
    spec = util.spec_from_file_location('portable_loader', SOURCE / 'features/options/tools/carica_text.py')
    loader = util.module_from_spec(spec)
    spec.loader.exec_module(loader)
    version = subprocess.run([compiler, '--version'], env=compiler_environment(), capture_output=True, text=True, check=True).stdout.splitlines()[0]
    _require(version == COMPILER_VERSION, 'compiler version drift: ' + version)
    _require(_sha(Path(compiler).resolve().read_bytes()) == COMPILER_SHA256, 'compiler binary drift')
    with tempfile.TemporaryDirectory(prefix='portable-box-', dir=work) as scratch:
        scratch = Path(scratch)
        obj = scratch / 'runtime.o'
        result = subprocess.run([compiler, *FLAGS, '-I', str(FEATURE), '-c', str(RUNTIME), '-o', str(obj)],
                                cwd=scratch, env=compiler_environment(), capture_output=True, text=True, timeout=120)
        _require(result.returncode == 0 and not result.stderr, 'native compile failed: ' + result.stderr)
        raw = obj.read_bytes()
        usage = (scratch / 'runtime.su').read_text()
    blob, symbols = loader.load_text(raw, base, ENTRIES)
    stacks = {}
    for line in usage.splitlines():
        parts = line.split('\t')
        if len(parts) >= 3:
            stacks[parts[0].rsplit(':', 1)[-1]] = int(parts[1])
    return blob, symbols, {
        'bytes': len(blob), 'object_sha256': _sha(raw), 'payload_sha256': _sha(blob),
        'stack_bytes': stacks, 'stack_max': max(stacks.values(), default=0),
        'source_sha256': {p.name: _sha(p.read_bytes()) for p in sorted(FEATURE.glob('*.[ch]'))},
        'compiler': version, 'flags': FLAGS}


# ------------------------------------------------------------------- trampoline

def _ldr_pc(here, literal):
    delta = literal - ((here + 4) & ~3)
    _require(delta >= 0 and delta % 4 == 0 and delta // 4 < 256, 'literal out of ldr range')
    return struct.pack('<H', 0x4800 | 3 << 8 | delta // 4)


def callback_trampoline(address, gate):
    """Instruction-aware trampoline for the party return callback.

    Entered at CALLBACK by the 8-byte hook (r0 = TaskManager, lr = caller). It
    asks `gate` (sgp_box_party_return); non-zero means the request was consumed
    and the callback returns FALSE. Otherwise it restores r0/lr, re-executes the
    five displaced instructions (the BL at +6 is re-encoded for this address)
    and resumes at +12, the first instruction after the displaced span.
    """
    _require(address % 4 == 0 and gate % 2 == 1, 'trampoline alignment / Thumb gate')
    out = bytearray()
    out += struct.pack('<H', 0xB501)                       # push {r0, lr}
    out += _ldr_pc(address + 2, address + 0x24)            # ldr r3, =gate
    out += struct.pack('<H', 0x4798)                       # blx r3
    out += struct.pack('<H', 0x2800)                       # cmp r0, #0
    out += struct.pack('<H', 0xD001)                       # beq native
    out += struct.pack('<H', 0x2000)                       # movs r0, #0   (callback result FALSE)
    out += struct.pack('<H', 0xBD02)                       # pop {r1, pc}
    out += struct.pack('<H', 0xBC03)                       # native: pop {r0, r1}
    out += struct.pack('<H', 0x468E)                       # mov lr, r1
    out += CALLBACK_BEFORE[0:6]                            # push {r4-r7,lr}; sub sp,#12; adds r7,r0,#0
    out += bl_thumb(address + 0x18, GET_FIELD_SYSTEM)      # displaced BL, re-encoded
    out += CALLBACK_BEFORE[10:12]                          # adds r5, r0, #0
    out += _ldr_pc(address + 0x1E, address + 0x28)         # ldr r3, =resume
    out += struct.pack('<H', 0x4718)                       # bx r3
    out += struct.pack('<H', 0x46C0)                       # nop (literal alignment)
    out += struct.pack('<I', gate)                         # +0x24
    out += struct.pack('<I', CALLBACK_RESUME | 1)          # +0x28
    _require(len(out) == TRAMPOLINE_BYTES, 'trampoline size')
    return bytes(out)


def callback_hook(trampoline):
    """Eight bytes written at CALLBACK: ldr r3,[pc,#0]; bx r3; .word trampoline|1."""
    return bytes.fromhex('004b1847') + struct.pack('<I', trampoline | 1)


def hook_patches(symbols, trampoline):
    """{site: bytes} for the three BL hooks and the callback entry (shared by installer and benches)."""
    patches = {site: bl_thumb(site, symbols[entry]) for _name, site, entry, _old in BL_HOOKS}
    patches[CALLBACK] = callback_hook(trampoline)
    return patches


# ------------------------------------------------------------------------ prepare

def _activation(activation, internal=False):
    """Validated activation words. `context_proof` is set by the installer from an accepted proof only
    (`internal=True` is for the test bench that places the payload itself)."""
    config = dict(ACTIVATION_DEFAULT)
    if activation is not None:
        allowed = set(ACTIVATION_DEFAULT) if internal else set(ACTIVATION_DEFAULT) - {'context_proof'}
        _require(set(activation) <= allowed, 'unknown activation word')
        config.update(activation)
    for key in ('bridge', 'input', 'prompt'):
        _require(config[key] in (0, 1), 'activation words are 0 or 1')
    _require(config['context_proof'] in (0, 1), 'context_proof word is 0 or 1')
    _require(type(config['travel_mask']) is int and 0 <= config['travel_mask'] < 1 << 8, 'travel_mask range')
    # a key that triggers nothing, a label for a command that does nothing: refused
    if not internal:   # the test bench places incoherent words on purpose to prove the runtime defends itself
        _require(not config['input'] or config['bridge'], 'input needs bridge')
        _require(not config['prompt'] or (config['bridge'] and config['input']), 'prompt needs bridge and input')
    return config


_HEX64 = re.compile(r'[0-9a-f]{64}')


def _is_sha256(value):
    return type(value) is str and _HEX64.fullmatch(value) is not None


PROOF_BASE = ('sha256', 'origin', 'status')
PROOF_CAPTURE = ('capture_file', 'capture_rom_sha256', 'build_id', 'language')   # same identity fields as the rematch proof


def _proof(context_proof, allow_synthetic, language, candidate_sha256):
    """Validate a context proof: what a static read of the start menu and field cannot show (Elite Four
    rooms, structures outside the pinned signals, travel cases) must be attested by a receipt.

    A `measured` proof names the capture it comes from (`capture_file`, `build_id`), the language that was
    played and the `capture_rom_sha256` of the inert candidate ROM that was played: the last must equal the
    caller's `candidate_sha256`, the language the declared one. A `synthetic` one is for tests only. The proof
    is an attestation: this module cannot check that the capture exists, only that it is identified and bound
    to the candidate."""
    if context_proof is None:
        return None
    _require(type(context_proof) is dict, 'context proof must be a mapping')
    _require(_is_sha256(candidate_sha256), 'a context proof needs candidate_sha256: the inert candidate ROM that was captured')
    status = context_proof.get('status')
    _require(status in ('measured', 'synthetic'), 'context proof status is measured or synthetic')
    required = set(PROOF_BASE) | (set(PROOF_CAPTURE) if status == 'measured' else set())
    allowed = set(PROOF_BASE) | set(PROOF_CAPTURE)
    _require(required <= set(context_proof) <= allowed, 'context proof needs exactly %s' % ', '.join(sorted(required)))
    _require(_is_sha256(context_proof['sha256']), 'context proof sha256')
    _require(type(context_proof['origin']) is str and context_proof['origin'].strip(), 'context proof origin')
    for key in ('capture_file', 'build_id'):
        _require(key not in context_proof or (type(context_proof[key]) is str and context_proof[key].strip()),
                 'context proof ' + key)
    _require('capture_rom_sha256' not in context_proof or _is_sha256(context_proof['capture_rom_sha256']),
             'context proof capture_rom_sha256 must be a lowercase sha256')
    _require('language' not in context_proof or context_proof['language'] == language,
             'context proof belongs to another language')
    if status == 'synthetic':
        _require(allow_synthetic is True, 'a synthetic context proof is for tests only')
        return dict(context_proof, accepted_as='synthetic-for-test')
    _require(context_proof['capture_rom_sha256'] == candidate_sha256,
             'context proof belongs to another ROM (capture_rom_sha256 differs from candidate_sha256)')
    return dict(context_proof, accepted_as='measured')


SLOT_NAME = 'portable-box.runtime'
ALLOCATION_FIELDS = {'schema', 'input_sha256', 'language', 'policy_version', 'policy_sha256', 'audit_sha256', 'requested',
                     'assignments', 'preservation', 'address_reserved', 'installed', 'installation_authorized'}


def _reserve_policy():
    """(policy, sha256 of the policy file) in force. Tests replace this one function with a declared test policy."""
    raw = reserve.MAP.read_bytes()
    policy = json.loads(raw)
    reserve.validate_policy(policy)
    return policy, hashlib.sha256(raw).hexdigest()


def check_allocation(allocation, language, name=SLOT_NAME):
    """Accept a base only from a `reserve.allocate` receipt; return the assignment for `name`.

    The receipt is re-derived against the reserve policy in force: the same policy file, an input that is an
    exact V4 of this language, every requested name a non-conditional payload slot of that policy, and the
    assignment list identical to what `reserve.allocate` computes. The ROM bytes are not needed (the
    installer may run after other stages); the audit hash inside the receipt is only shape-checked."""
    if type(allocation) is dict and type(allocation.get('schema')) is int and allocation['schema'] == 2:
        # Downstream structure/policy constraint only. The builder MUST reissue this grant against the
        # exact pristine and cold-UI images; a JSON proof/hash is not authentication or authorization.
        validate = getattr(reserve, 'validate_allocation', None)
        _require(callable(validate), 'bound reserve allocation verifier unavailable')
        rows = validate(allocation, language)
        selected = [row for row in rows if row['name'] == name]
        _require(len(selected) == 1, 'allocation receipt does not request %s' % name)
        row = selected[0]
        _require(row['start'] % 4 == 0 and row['bytes'] % 4 == 0 and reserve.BASE <= row['start']
                 and row['start'] + row['bytes'] <= reserve.END, 'assignment outside the reserve range or unaligned')
        return dict(row)
    _require(type(allocation) is dict and set(allocation) == ALLOCATION_FIELDS,
             'the base must come from a reserve.allocate receipt (exact fields %s)' % sorted(ALLOCATION_FIELDS))
    policy, digest = _reserve_policy()
    _require(allocation['schema'] == 1 and allocation['policy_sha256'] == digest
             and allocation['policy_version'] == policy['version'],
             'allocation receipt was not issued under the reserve policy in force')
    _require(allocation['address_reserved'] is True and allocation['installed'] is False
             and allocation['installation_authorized'] is False, 'allocation receipt flags')
    _require(allocation['language'] == language and baseline.INPUT_HASHES.get(allocation['input_sha256']) == language,
             'allocation receipt belongs to another ROM or language')
    _require(_is_sha256(allocation['audit_sha256']), 'allocation audit hash')
    requested = allocation['requested']
    _require(type(requested) is dict and name in requested, 'allocation receipt does not request %s' % name)
    conditional = policy.get('conditional_parents', reserve.CONDITIONAL_REQUIREMENTS)
    slots = {part['name']: (entry['parent'], part) for entry in policy['subdivisions']
             for part in entry['parts'] if part['kind'] == 'payload'}
    expected = []
    for slot_name, size in requested.items():
        _require(type(slot_name) is str and slot_name in slots, 'the reserve policy has no payload slot %s' % slot_name)
        _require(type(size) is int and 0 < size, 'requested size')
        parent, slot = slots[slot_name]
        _require(parent not in conditional, 'slot %s belongs to a conditional owner (%s): the reserve refuses it' % (slot_name, parent))
        _require(size <= slot['bytes'], 'requested size exceeds the slot capacity')
        expected.append({'name': slot_name, 'parent': parent, 'start': slot['start'], 'bytes': size, 'capacity': slot['bytes']})
    expected.sort(key=lambda row: row['start'])
    _require(allocation['assignments'] == expected, 'allocation assignments differ from what the reserve policy grants')
    row = next(item for item in expected if item['name'] == name)
    _require(row['start'] % 4 == 0 and row['bytes'] % 4 == 0 and reserve.BASE <= row['start']
             and row['start'] + row['bytes'] <= reserve.END, 'assignment outside the reserve range or unaligned')
    return dict(row)


def layout(blob_bytes, base):
    code_end = (blob_bytes + 3) & ~3
    return {'code': base, 'trampoline': base + code_end, 'end': base + code_end + TRAMPOLINE_BYTES}


def measure(work):
    """Compartment size and stack for an assignment request (the object does not depend on the base)."""
    blob, _symbols, compiled = compile_native(work, 0x02000000)
    return {'code_bytes': len(blob), 'bytes': ((len(blob) + 3) & ~3) + TRAMPOLINE_BYTES,
            'stack_max': compiled['stack_max'], 'payload_sha256': compiled['payload_sha256']}


def _config_words(blob, area):
    return {key: struct.unpack_from('<I', blob, area + STATE_BYTES + CONFIG_OFFSETS[key])[0] for key in ACTIVATION_DEFAULT}


def _function_state(words):
    return 'active' if (words['bridge'] or words['input'] or words['prompt']) else 'inert'


def inert_view(data, receipt):
    """The same image with this stage's activation words (bridge, input, prompt, context_proof) cleared; pure.

    The builder's mandatory final gate is `sha256(inert_view(final_rom, receipt)) == candidate_sha256` (see
    `candidate_gate`). `travel_mask` is configuration, not activation, and is kept."""
    address = receipt['config']['address']
    inert = bytearray(data)
    segments = arm9_segments(bytes(data))
    for key in ('bridge', 'input', 'prompt', 'context_proof'):
        at = locate(segments, address + CONFIG_OFFSETS[key], 4)
        inert[at:at + 4] = bytes(4)
    return bytes(inert)


def candidate_gate(final_rom, receipt):
    """Final gate before activation: the final ROM with the activation words cleared must be the declared candidate."""
    candidate = receipt.get('candidate_sha256')
    _require(candidate is not None, 'the receipt declares no candidate: nothing to gate')
    _require(_sha(inert_view(final_rom, receipt)) == candidate,
             'the final ROM with the activation words cleared is not the candidate the proof was captured on')


def slot_preimage_from_v4(v4, language, allocation):
    """The expected preimage of the whole assigned slot, taken from the exact V4 image (never from the stage input).

    Valid as long as the stages between the V4 and this one leave the slot alone (the UI does); a stage that leaves
    residue there must have its post-stage hash pinned in the stage manifest and passed as `preimage_sha256`."""
    v4 = bytes(v4)
    _require(baseline.INPUT_HASHES.get(_sha(v4)) == language, 'the V4 image must be the exact V4 of this language')
    assignment = check_allocation(allocation, language)
    return _sha(read_ram(v4, arm9_segments(v4), assignment['start'], assignment['bytes']))


def _relation(candidate_sha256, inert_sha):
    if candidate_sha256 is None:
        return None
    return 'stage-inert-output' if candidate_sha256 == inert_sha else 'composed-candidate'


def prepare(data, language, work, *, allocation, preimage_sha256, activation=None, context_proof=None,
            candidate_sha256=None, allow_synthetic_proof=False):
    """Install the guarded portable box into an in-memory ROM image.

    `allocation` is a `reserve.allocate` receipt naming `portable-box.runtime`: the compartment base is its
    assignment (4-aligned, inside one ARM9 segment), never an address chosen here. `preimage_sha256` is
    mandatory: it is the sha256 of the bytes the assignment replaces in `data`, and the current bytes must
    match it. Activating (or carrying a context proof) needs `candidate_sha256`, the inert candidate ROM the
    proof was captured on. Returns (new ROM bytes, receipt).
    """
    _require(language in LANGUAGES, 'unsupported language')
    _require(allocation is not None, 'compartment base must come from a reserve allocation receipt; none given')
    _require(_is_sha256(preimage_sha256), 'the assignment must state the sha256 of the bytes it replaces')
    _require(candidate_sha256 is None or _is_sha256(candidate_sha256), 'candidate_sha256 must be a lowercase sha256')
    assignment = check_allocation(allocation, language)
    base = assignment['start']
    data = bytes(data)
    audit = audit_native(data, language)
    config = _activation(activation)
    proof = _proof(context_proof, allow_synthetic_proof, language, candidate_sha256)
    _require(proof is not None or not (config['bridge'] or config['input'] or config['prompt']),
             'activating the box needs a context proof (receipt with sha256 and origin)')
    config['context_proof'] = 1 if proof else 0
    segments = arm9_segments(data)
    blob, symbols, compiled = compile_native(work, base)
    plan = layout(len(blob), base)
    size = plan['end'] - base
    _require(size <= assignment['bytes'], 'compartment (%d bytes) exceeds the reserve assignment (%d bytes)' % (size, assignment['bytes']))
    at = locate(segments, base, size)
    slot_at = locate(segments, base, assignment['bytes'])
    before = data[slot_at:slot_at + assignment['bytes']]       # the whole assigned slot, not only the compartment
    _require(_sha(before) == preimage_sha256, 'assigned compartment preimage mismatch')
    # Every hook BL must reach the compartment and the compartment must not cover a hook site.
    sites = [site for _name, site, _entry, _old in BL_HOOKS] + [CALLBACK]
    _require(not any(base <= site < plan['end'] for site in sites), 'compartment overlaps a hook site')
    payload = bytearray(blob)
    payload += bytes(plan['trampoline'] - base - len(blob))
    area = symbols['sgp_box_area'] - base
    for key, value in config.items():
        struct.pack_into('<I', payload, area + STATE_BYTES + CONFIG_OFFSETS[key], value)
    gate = symbols['sgp_box_party_return']
    payload += callback_trampoline(plan['trampoline'], gate)
    out = bytearray(data)
    out[at:at + size] = payload
    writes = {base: bytes(payload)}
    for name, site, entry, old in BL_HOOKS:
        _require(bl_decode(site, read_ram(data, segments, site, 4)) == old, 'hook site %s is not the pinned BL' % name)
    _require(read_ram(data, segments, CALLBACK, 12) == CALLBACK_BEFORE, 'callback entry is not the pinned span')
    for site, hook in hook_patches(symbols, plan['trampoline']).items():
        out[locate(segments, site, len(hook)):locate(segments, site, len(hook)) + len(hook)] = hook
        writes[site] = hook
    result = bytes(out)
    config_address = symbols['sgp_box_area'] + STATE_BYTES
    receipt = {
        'module': 'portable-box', 'language': language, 'input_sha256': _sha(data),
        'output_sha256': _sha(result), 'base': base, 'allocation': copy.deepcopy(allocation), 'assignment': assignment,
        'compartment': {'start': base, 'bytes': size, 'code_bytes': len(blob),
                        'trampoline': plan['trampoline'], 'trampoline_bytes': TRAMPOLINE_BYTES,
                        'preimage_sha256': _sha(before), 'payload_sha256': _sha(payload)},
        'symbols': {k: v for k, v in symbols.items()},
        'state': {'address': symbols['sgp_box_area'], 'bytes': STATE_BYTES, 'offsets': STATE_OFFSETS},
        'context_proof': proof,
        'function_state': _function_state(config),
        'candidate_sha256': candidate_sha256,
        'capture_rom_sha256': None if proof is None else proof.get('capture_rom_sha256'),
        'candidate_relation': _relation(candidate_sha256, _sha(inert_view(result, {'config': {'address': config_address}}))),
        'config': {'address': config_address, 'bytes': CONFIG_BYTES,
                   'offsets': CONFIG_OFFSETS, 'values': config},
        'hooks': {name: {'site': site, 'old_target': old, 'new_target': symbols[entry] & ~1}
                  for name, site, entry, old in BL_HOOKS},
        'callback_hook': {'site': CALLBACK, 'bytes': 8, 'trampoline': plan['trampoline'],
                          'displaced': CALLBACK_BEFORE.hex(), 'resume': CALLBACK_RESUME},
        'writes': {hex(k): _sha(v) for k, v in writes.items()},
        'write_ranges': [[k, len(v)] for k, v in sorted(writes.items())],
        'measure': compiled, 'native_audit': audit,
    }
    verify(data, result, receipt, require_measured=False)   # the proof status is the caller's gate, see verify()
    return result, receipt


# ------------------------------------------------------------------------- verify

def _changed(before, after, chunk=1 << 20):
    changed = []
    for start in range(0, len(before), chunk):
        end = min(start + chunk, len(before))
        if before[start:end] != after[start:end]:
            changed.extend(i for i in range(start, end) if before[i] != after[i])
    return changed


def verify(before, after, receipt, require_measured=True):
    """Independent read-back: only owned ranges changed, hooks decode, payload recompiles.

    `require_measured` (default True) refuses a receipt whose context proof is `synthetic-for-test`; only
    tests pass False. A receipt of an inert install (no proof, all words zero) is accepted either way."""
    before, after = bytes(before), bytes(after)
    _require(len(before) == len(after), 'ROM length changed')
    _require(_sha(before) == receipt['input_sha256'], 'input identity differs from the receipt')
    _require(_sha(after) == receipt['output_sha256'], 'output identity differs from the receipt')
    language = receipt['language']
    segments = arm9_segments(after)
    owned = set()
    for start, length in receipt['write_ranges']:
        at = locate(segments, start, length)
        owned.update(range(at, at + length))
    stray = [i for i in _changed(before, after) if i not in owned]
    if stray:
        raise ValueError('bytes changed outside the owned ranges (first at ROM offset %#x)' % stray[0])
    audit_native(before, language)
    symbols = receipt['symbols']
    for name, hook in receipt['hooks'].items():
        site = hook['site']
        target = bl_decode(site, read_ram(after, segments, site, 4))
        _require(target == hook['new_target'] and target == symbols[dict((n, e) for n, _s, e, _o in BL_HOOKS)[name]] & ~1,
                 'hook %s does not reach its entry' % name)
        _require(hook['old_target'] == dict((n, o) for n, _s, _e, o in BL_HOOKS)[name], 'hook old target')
    callback = receipt['callback_hook']
    _require(read_ram(after, segments, CALLBACK, 8) == callback_hook(callback['trampoline']), 'callback hook bytes')
    gate = symbols['sgp_box_party_return']
    _require(read_ram(after, segments, callback['trampoline'], TRAMPOLINE_BYTES)
             == callback_trampoline(callback['trampoline'], gate), 'trampoline bytes')
    comp = receipt['compartment']
    assignment = check_allocation(receipt.get('allocation'), language)   # the base still comes from the reserve policy in force
    _require(receipt['base'] == comp['start'] == assignment['start'] and comp['bytes'] <= assignment['bytes']
             and receipt.get('assignment') == assignment, 'compartment differs from the reserve assignment')
    _require(_sha(read_ram(before, segments, comp['start'], assignment['bytes'])) == comp['preimage_sha256'],
             'assigned slot preimage differs from the receipt')
    blob = read_ram(after, segments, comp['start'], comp['bytes'])
    _require(_sha(blob) == comp['payload_sha256'], 'compartment readback')
    with tempfile.TemporaryDirectory(prefix='portable-verify-') as work:
        fresh, fresh_symbols, _ = compile_native(work, comp['start'])
    _require(fresh_symbols == symbols, 'recompiled symbols differ')
    expected = bytearray(fresh)
    area = symbols['sgp_box_area'] - comp['start']
    for key, value in receipt['config']['values'].items():
        struct.pack_into('<I', expected, area + STATE_BYTES + CONFIG_OFFSETS[key], value)
    _require(blob[:len(fresh)] == bytes(expected), 'recompiled payload differs from the installed bytes')
    values = receipt['config']['values']
    installed = _config_words(blob, area)                     # the activation words as installed, from the bytes
    _require(installed == values, 'activation words differ from the receipt')
    state = _function_state(installed)
    _require(receipt.get('function_state') == state, 'function_state differs from the installed activation words')
    proof = receipt.get('context_proof')
    candidate = receipt.get('candidate_sha256')
    _require(candidate is None or _is_sha256(candidate), 'candidate_sha256')
    _require(values['context_proof'] == (1 if proof else 0), 'context proof word and receipt disagree')
    _require(state == 'inert' or proof is not None, 'active words without a context proof')
    if proof is not None:
        again = _proof({k: v for k, v in proof.items() if k != 'accepted_as'}, True, language, candidate)
        _require(again == proof, 'context proof differs from its validated form')
        _require(receipt.get('capture_rom_sha256') == proof.get('capture_rom_sha256'), 'capture_rom_sha256 differs from the proof')
        _require(not require_measured or proof['accepted_as'] == 'measured',
                 'the receipt carries a synthetic (test-only) context proof')
    else:
        _require(receipt.get('capture_rom_sha256') is None, 'capture_rom_sha256 without a proof')
    _require(receipt.get('candidate_relation') == _relation(candidate, _sha(inert_view(after, receipt))),
             'candidate relation differs from the installed bytes')
    _require(not values['input'] or values['bridge'], 'input without bridge')
    _require(not values['prompt'] or (values['bridge'] and values['input']), 'prompt without bridge and input')
    return {'verified': True, 'language': language, 'function_state': state, 'candidate_sha256': candidate,
            'candidate_relation': receipt['candidate_relation'],
            'context_proof': None if proof is None else proof['accepted_as'], 'code_bytes': comp['code_bytes'],
            'owned_ranges': len(receipt['write_ranges']), 'stray_bytes': 0,
            'stack_max': receipt['measure']['stack_max'], 'activation': receipt['config']['values']}
