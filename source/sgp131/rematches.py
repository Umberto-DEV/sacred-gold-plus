"""Plus-only complete-party variants for the two ordinary rematches (trainer IDs 712 and 713).

Two authored variants (A, B) per trainer, selected once per construction by the
core in features/rematch-variants and frozen in the transient party buffer.
Normal difficulty, every other trainer and every other battle context keep the
native bytes. This module owns the authored data, the materialised config image,
the compile step and the parametric installer/verifier. It never chooses an
address: the base comes only from a `reserve.allocate` receipt. It pins byte
intervals and archive members (never the whole ROM), so it composes after any
stage that leaves them alone.
"""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import struct
import subprocess
from sgp13.compiler import compiler_path, compiler_environment
import tempfile

import ndspy.narc
import ndspy.rom
from ndspy import _common

from sgp12.rom import Arm9, bl_decode, bl_thumb, valida_layout_arm9
from . import baseline, reserve

SOURCE = Path(__file__).resolve().parents[1]
DATA = Path(__file__).with_name('data')
FEATURE = SOURCE / 'features/rematch-variants'
MAGIC = 0x31564D52
HEADER, DESCRIPTOR, PARTY, SLOT = 20, 24, 108, 18
TYPE_COUNT = 0x0306
MAX_TRAINERS = 4
SPECIES_MAX, MOVE_MAX = 493, 467
LANGUAGES = ('EN', 'IT')
DEFAULT_CODE_SIZE, DEFAULT_CONFIG_SIZE = 1280, 768
COMPILER_VERSION = 'Apple clang version 21.0.0 (clang-2100.4.1.1)'     # same pin as controls.py
COMPILER_SHA256 = 'fc5e3cbba6ad54059295cad716aacb05ace8235f5f7a6031f1d8c15d24bd6d66'
# Member of a/0/1/1 rewritten by sgp131.modern_moves (accuracy 75 -> 85). Only the members actually read are pinned,
# so this module is independent of that stage's order.
REWRITTEN_MOVE_MEMBER = 261
FIELDS = ('species', 'form', 'override', 'item', 'moves', 'level', 'difficulty', 'capsule')


def load_spec():
    return json.loads((DATA / 'rematch-variants.json').read_text())


def load_abi():
    return json.loads((DATA / 'rematch-native-abi.json').read_text())


def fnv(data):
    value = 2166136261
    for byte in data:
        value = ((value ^ byte) * 16777619) & 0xffffffff
    return value


def sha(data):
    return hashlib.sha256(data).hexdigest()


# ---------------------------------------------------------------- party codec

def decode_party(raw):
    if len(raw) != PARTY:
        raise ValueError('party preimage: expected 108 bytes')
    slots = []
    for index in range(6):
        difficulty, override, level, word, item, m0, m1, m2, m3, capsule = struct.unpack_from(
            '<BBHHH4HH', raw, index * SLOT)
        slots.append(dict(slot=index, difficulty=difficulty, override=override, level=level,
                          species=word & 0x3FF, form=word >> 10, item=item,
                          moves=[m0, m1, m2, m3], capsule=capsule))
    return slots


def encode_party(slots):
    return b''.join(struct.pack('<BBHHH4HH', s['difficulty'], s['override'], s['level'],
                                s['species'] | (s['form'] << 10), s['item'], *s['moves'], s['capsule'])
                    for s in slots)


def _plain(slot):
    return {k: (list(v) if k == 'moves' else v) for k, v in slot.items() if k != 'slot'}


def apply_changes(slots, changes):
    """Return a new list with every transformation applied; each declared 'before' must match."""
    result = [dict(s, moves=list(s['moves'])) for s in slots]
    for change in changes:
        index = change['slot']
        if type(index) is not int or not 0 <= index < 6:
            raise ValueError('variant preimage: slot')
        for field, value in change.items():
            if field in ('slot', 'why'):
                continue
            if field not in FIELDS:
                raise ValueError(f'variant preimage: unknown field {field}')
            current = result[index][field]
            if value['before'] != current:
                raise ValueError(f'variant preimage: slot {index} {field} is {current}, declared {value["before"]}')
            result[index][field] = list(value['after']) if field == 'moves' else value['after']
    return result


def check_policy(trainer, spec, base, a, b):
    """Levels, IV byte, capsule and ace are never edited; members stay plausible and distinct."""
    ace = trainer['ace']
    item_max = spec.get('item_archive', {}).get('item_max', 515)
    for name, team in (('baseline', base), ('A', a), ('B', b)):
        if team[ace['slot']]['species'] != ace['species'] or team[ace['slot']]['level'] != ace['level']:
            raise ValueError(f'ace not preserved in {name}')
    for name, team in (('A', a), ('B', b)):
        seen = set()
        for old, new in zip(base, team):
            for field in ('level', 'difficulty', 'capsule'):
                if old[field] != new[field]:
                    raise ValueError(f'variant {name} must preserve {field} (slot {old["slot"]})')
            if not 1 <= new['species'] <= SPECIES_MAX or new['form'] != 0 or new['item'] > item_max:
                raise ValueError(f'variant {name} slot {old["slot"]}: species/form/item out of range')
            same = (new['species'], new['form']) == (old['species'], old['form'])
            if (new['override'] != old['override']) if same else new['override'] != 0:
                raise ValueError(f'variant {name} slot {old["slot"]}: override must follow the species')
            if (new['species'], new['form']) in seen:
                raise ValueError(f'variant {name}: duplicate species {new["species"]}')
            seen.add((new['species'], new['form']))
            if (len(set(new['moves'])) != 4 or not all(1 <= m <= MOVE_MAX for m in new['moves'])):
                raise ValueError(f'variant {name} slot {old["slot"]}: moves must be four distinct ids in 1..{MOVE_MAX}')
    if len({encode_party(t) for t in (base, a, b)}) != 3:
        raise ValueError('the three parties must differ')


# ------------------------------------------------------------- configuration

def _context(active, battle_types, enemy_indexes):
    if active not in (0, 1) or type(active) is not int:
        raise ValueError('context: active must be 0 or 1')
    if (not 1 <= len(battle_types) <= 2 or any(type(v) is not int or not 0 <= v <= 0xFFFFFFFF for v in battle_types)
            or len(set(battle_types)) != len(battle_types)):
        raise ValueError('context: one or two exact battleType values')
    if (not 1 <= len(enemy_indexes) <= 4 or any(type(v) is not int or not 0 <= v <= 3 for v in enemy_indexes)
            or len(set(enemy_indexes)) != len(enemy_indexes)):
        raise ValueError('context: enemy indexes 0..3 (BattleSetup has four trainers)')


def materialize(spec, parties, headers, *, active=0, battle_types=(1,), enemy_indexes=(1,)):
    """Build the config image from a specification and the supplied trainer archive members."""
    if spec.get('schema') != 1:
        raise ValueError('unsupported schema')
    if spec.get('type_count') != TYPE_COUNT or spec.get('party_bytes') != PARTY:
        raise ValueError('type_count must be 0x0306 with 108-byte parties')
    _context(active, battle_types, enemy_indexes)
    trainers = spec.get('trainers', [])
    if not 1 <= len(trainers) <= MAX_TRAINERS:
        raise ValueError('trainers: between 1 and 4 supported')
    ids = [t['trainer_id'] for t in trainers]
    if len(set(ids)) != len(ids):
        raise ValueError('duplicate trainer id')
    prepared = []
    for trainer in trainers:
        tid = trainer['trainer_id']
        if trainer['type'] != 3 or trainer['count'] != 6 or trainer['bytes'] != PARTY:
            raise ValueError(f'trainer {tid}: format/count/bytes must be 3/6/108')
        if tid not in parties or tid not in headers:
            raise ValueError(f'trainer {tid}: archive member missing')
        raw, header = bytes(parties[tid]), bytes(headers[tid])
        if len(raw) != PARTY or sha(raw) != trainer['party_sha256']:
            raise ValueError(f'trainer {tid}: party preimage differs')
        if sha(header) != trainer['header_sha256'] or header[0] != 3 or header[3] != 6:
            raise ValueError(f'trainer {tid}: header preimage differs')
        base = decode_party(raw)
        declared = [dict(s) for s in trainer['baseline']]
        if [_plain(s) for s in base] != [_plain(s) for s in declared]:
            raise ValueError(f'trainer {tid}: party preimage tuples differ from the specification')
        a = apply_changes(base, trainer['variants']['A']['changes'])
        b = apply_changes(a, trainer['variants']['B']['changes'])
        check_policy(trainer, spec, base, a, b)
        for label, team in (('A', a), ('B', b)):
            if sha(encode_party(team)) != trainer['variants'][label]['sha256']:
                raise ValueError(f'trainer {tid}: variant hash {label} differs from the declared transformation')
        prepared.append((tid, raw, encode_party(a), encode_party(b)))
    first = HEADER + DESCRIPTOR * len(prepared)
    table = body = b''
    for index, (tid, base, a, b) in enumerate(prepared):
        offsets = [first + PARTY * (3 * index + n) for n in range(3)]
        body += base + a + b
        table += struct.pack('<6H3I', tid, TYPE_COUNT, *offsets, 0, fnv(base), fnv(a), fnv(b))
    types = list(battle_types) + [0] * (2 - len(battle_types))
    mask = sum(1 << i for i in set(enemy_indexes))
    head = struct.pack('<IHBBBBH2I', MAGIC, first + len(body), active, len(prepared),
                       len(battle_types), mask, 0, *types)
    return head + table + body


# --------------------------------------------------------------- ROM access

class _Image(Arm9):
    """Arm9 over an in-memory ROM image (no file)."""

    def __init__(self, data):
        self.path = None
        self.raw = bytearray(data)
        self.off9 = struct.unpack_from('<I', self.raw, 0x20)[0]
        self.ram9 = struct.unpack_from('<I', self.raw, 0x28)[0]
        self.siz9 = struct.unpack_from('<I', self.raw, 0x2C)[0]
        (self.tab0, self.tab1, self.dati0, self.sezioni,
         self.segmenti) = valida_layout_arm9(self.raw, self.off9, self.ram9, self.siz9)


def _hex(value):
    return int(value, 16) if isinstance(value, str) else value


class Resources:
    """The archives and tables the specification is checked against."""

    def __init__(self, data):
        rom = ndspy.rom.NintendoDSRom(bytes(data))
        self.digests, files = {}, {}
        for path in ('a/0/5/5', 'a/0/5/6', 'a/0/0/2', 'a/0/1/1', 'a/0/3/3', 'a/2/2/9', 'a/0/1/7'):
            raw = rom.getFileByName(path)
            self.digests[path] = sha(raw)
            files[path] = ndspy.narc.NARC(raw).files
        self.headers, self.parties, self.personal = files['a/0/5/5'], files['a/0/5/6'], files['a/0/0/2']
        self.moves, self.wotbl, self.eggs, self.items = files['a/0/1/1'], files['a/0/3/3'], files['a/2/2/9'], files['a/0/1/7']
        abi = load_abi()['tm_table']
        arm = _Image(data)
        table = arm.leggi(_hex(abi['address']), abi['count'] * 2)
        if sha(table) != abi['sha256']:
            raise ValueError('TM/HM table preimage differs')
        self.machines = list(struct.unpack('<%dH' % abi['count'], table))

    def sources(self, species, move):
        found = []
        raw = self.wotbl[species]
        for word in struct.unpack('<%dH' % (len(raw) // 2), raw):
            if word == 0xFFFF:
                break
            if word & 511 == move:
                found.append('lvl%d' % (word >> 9))
        bits = struct.unpack_from('<4I', self.personal[species], 0x1C)
        for number, machine in enumerate(self.machines):
            if machine == move and (bits[number // 32] >> (number % 32)) & 1:
                found.append('TM%02d' % (number + 1) if number < 92 else 'HM%02d' % (number - 91))
        current = None
        raw = self.eggs[0]
        for word in struct.unpack('<%dH' % (len(raw) // 2), raw):
            if word > 20000:
                current = word - 20000
            elif current == species and word == move:
                found.append('egg')
        return found


def verify_semantics(spec, res):
    """Archive preimages, move meanings (including reused ids), species data and legality."""
    for path, digest in spec['preimages'].items():
        if res.digests[path] != digest:
            raise ValueError(f'archive preimage differs: {path}')
    items = spec['item_archive']
    if len(res.items) != items['members'] or items['item_max'] != items['members'] - 1:
        raise ValueError('item archive member count differs')
    for key, meaning in spec['items'].items():
        if sha(res.items[int(key)]) != meaning['sha256']:
            raise ValueError(f'item record {key} differs from the audited record')
    declared_moves, declared_species = spec['moves'], spec['species']
    for key, meaning in declared_moves.items():
        move = int(key)
        if move == REWRITTEN_MOVE_MEMBER:
            raise ValueError(f'move {move} is rewritten by another 1.3.1 stage and must not be read here')
        record = res.moves[move]
        if sha(record) != meaning['sha256']:
            raise ValueError(f'move member {move} differs from the audited record')
        actual = dict(effect=struct.unpack_from('<H', record, 0)[0], category=record[2], power=record[3],
                      type=record[4], accuracy=record[5], pp=record[6])
        if any(actual[name] != meaning[name] for name in actual):
            raise ValueError(f'move {move} no longer means {meaning["en"]}: {actual}')
    for key, meaning in declared_species.items():
        record = res.personal[int(key)]
        if [record[6], record[7]] != meaning['types'] or [record[0x16], record[0x17]] != meaning['abilities']:
            raise ValueError(f'species {key} personal data differs from the specification')
    for trainer in spec['trainers']:
        base = [dict(s) for s in trainer['baseline']]
        a = apply_changes(base, trainer['variants']['A']['changes'])
        b = apply_changes(a, trainer['variants']['B']['changes'])
        covered = {(e['variant'], e['slot'], e['species'], e['move']): e for e in trainer['legality']}
        for label, team in (('A', a), ('B', b)):
            for slot, original in zip(team, base):
                if str(slot['species']) not in declared_species:
                    raise ValueError(f'species {slot["species"]} not declared')
                if slot['item'] and slot['item'] not in [int(k) for k in spec['items']]:
                    raise ValueError(f'item {slot["item"]} not declared')
                for move in slot['moves']:
                    if str(move) not in declared_moves:
                        raise ValueError(f'move {move} not declared')
                    if slot['species'] == original['species'] and move in original['moves']:
                        continue
                    key = (slot['slot'], slot['species'], move)
                    # a pair inherited unchanged from variant A is declared once, under A
                    entry = covered.get((label,) + key) or (covered.get(('A',) + key) if label == 'B' else None)
                    if not entry:
                        raise ValueError(f'legality of species {slot["species"]} move {move} not declared')
                    actual = res.sources(slot['species'], move)
                    usable = [s for s in actual if s.startswith(('TM', 'HM')) or
                              (s.startswith('lvl') and int(s[3:]) <= slot['level'])]
                    if actual != entry['sources'] or not usable:
                        raise ValueError(f'illegal or changed sources for species {slot["species"]} move {move}: {actual}')


def configuration(data, spec=None, *, active=0, battle_types=(1,), enemy_indexes=(1,)):
    """Config image for the supported archives in `data` (a complete ROM image)."""
    spec = load_spec() if spec is None else spec
    res = Resources(data)
    verify_semantics(spec, res)
    parties = {t['trainer_id']: res.parties[t['trainer_id']] for t in spec['trainers']}
    headers = {t['trainer_id']: res.headers[t['trainer_id']] for t in spec['trainers']}
    return materialize(spec, parties, headers, active=active, battle_types=battle_types,
                       enemy_indexes=enemy_indexes)


# ------------------------------------------------------- compile and install

def _compiler():
    """The pinned clang (version string and binary hash, as in controls.py)."""
    compiler = compiler_path(COMPILER_SHA256)
    if compiler is None:
        raise ValueError('clang unavailable')
    version = subprocess.run([compiler, '--version'], env=compiler_environment(), capture_output=True, text=True, check=True).stdout.splitlines()[0]
    if version != COMPILER_VERSION:
        raise ValueError('compiler version drift: ' + version)
    if sha(Path(compiler).resolve().read_bytes()) != COMPILER_SHA256:
        raise ValueError('compiler binary drift')
    return compiler


def _loader():
    spec = importlib.util.spec_from_file_location('rematch_loader', SOURCE / 'features/options/tools/carica_text.py')
    loader = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loader)
    return loader


def compile_native(work_dir, base, config_address, config_bytes):
    """Compile native.c for ARM946E-S Thumb; code is relocated to `base`, the config is at `config_address`
    and its allocation (the bound the core enforces at runtime) is `config_bytes`. The module is entered from the
    resident stub, whose frame (STUB_STACK bytes) the hook adds to its host-SP offset."""
    work = Path(work_dir)
    work.mkdir(parents=True, exist_ok=True)
    obj = work / 'rematch-variants.o'
    compiler = _compiler()
    subprocess.run([compiler, '--target=armv5te-none-eabi', '-mcpu=arm946e-s', '-mthumb', '-Os',
                    '-ffreestanding', '-fno-builtin', '-fno-stack-protector', '-fno-jump-tables',
                    '-fno-unwind-tables', '-fno-asynchronous-unwind-tables', '-Wall', '-Wextra', '-Werror',
                    f'-DREMATCH_CONFIG_ADDR=0x{config_address:08X}u', f'-DREMATCH_CONFIG_BYTES={config_bytes}u',
                    f'-DREMATCH_HOST_SP_OFFSET={32 + load_abi()["stub"]["stack_bytes"]}', '-c', str(FEATURE / 'native.c'),
                    '-o', str(obj)], check=True, env=compiler_environment_for(work), capture_output=True)
    blob, symbols = _loader().load_text(obj.read_bytes(), base, ('rematch_hook', 'rematch_native'))
    obj.unlink()
    return blob, symbols


def compile_stub(work_dir, base, entry):
    """Assemble stub.S for the resident slot at `base`; `entry` is the module's Thumb entry (bit 0 set)."""
    abi = load_abi()
    work = Path(work_dir)
    work.mkdir(parents=True, exist_ok=True)
    obj = work / 'rematch-stub.o'
    loader = abi['overlay']['loader']
    defines = {'ID': abi['overlay']['id'], 'ENTRY': entry, 'NATIVE': _hex(abi['stub']['native_reader']),
               'HLO': _hex(loader['HandleLoadOverlay']['address']) | 1, 'ULO': _hex(loader['UnloadOverlayByID']['address']) | 1}
    subprocess.run([_compiler(), '--target=armv5te-none-eabi', '-mcpu=arm946e-s', '-mthumb', '-x', 'assembler-with-cpp',
                    *[f'-D{k}=0x{v:08X}' for k, v in defines.items()], '-c', str(FEATURE / 'stub.S'), '-o', str(obj)],
                   check=True, env=compiler_environment_for(work), capture_output=True)
    blob, symbols = _loader().load_text(obj.read_bytes(), base, ('c8_stub',))
    obj.unlink()
    if len(blob) > abi['stub']['max_bytes']:
        raise ValueError(f'stub overflow: {len(blob)} > {abi["stub"]["max_bytes"]}')
    return blob, symbols


def compiler_environment_for(work_dir):
    """Use the authenticated compiler environment with a private writable temp root."""
    work = Path(work_dir).resolve(strict=True)
    if not work.is_dir():
        raise ValueError('rematch compiler TMPDIR is not a directory')
    environment = dict(compiler_environment())
    environment['TMPDIR'] = str(work)
    return environment


PROOF_FIELDS = ('capture_file', 'capture_rom_sha256', 'build_id')
_HEX64 = set('0123456789abcdef')


def _is_sha256(value):
    return isinstance(value, str) and len(value) == 64 and set(value) <= _HEX64


def proof_digest(proof):
    return sha(json.dumps(proof, sort_keys=True, separators=(',', ':')).encode())


def validate_context_proof(proof, abi, language, candidate_sha256, allow_synthetic=False):
    """Runtime evidence supplied by the Android campaign that the exact gate values are the ordinary ones.

    A capture is bound to the inert candidate ROM it was played on: `capture_rom_sha256` must equal the
    caller's `candidate_sha256`, and the proof's language the declared one. Returns the proof origin:
    'android' for a capture, 'synthetic' for the harness stand-in, which is refused unless the caller (a
    test) passes allow_synthetic=True explicitly."""
    context = abi['gate']['context']
    families = {name: item['battle_type'] for name, item in context['families'].items()}
    if not isinstance(proof, dict) or proof.get('language') != language or not proof.get('observations'):
        raise ValueError('activation requires a runtime context proof for this language')
    if not _is_sha256(candidate_sha256):
        raise ValueError('activation requires candidate_sha256: the inert candidate ROM that was captured')
    synthetic = proof.get('synthetic_harness_only') is True
    if synthetic and not allow_synthetic:
        raise ValueError('a synthetic harness proof is not runtime evidence and cannot activate the wrapper')
    if not synthetic:
        for field in PROOF_FIELDS:
            if not isinstance(proof.get(field), str) or not proof[field]:
                raise ValueError(f'context proof lacks the capture identity field {field}')
        if not _is_sha256(proof['capture_rom_sha256']):
            raise ValueError('context proof capture_rom_sha256 must be a lowercase sha256')
        if proof['capture_rom_sha256'] != candidate_sha256:
            raise ValueError('context proof belongs to another ROM (capture_rom_sha256 differs from candidate_sha256)')
    seen = set()
    for item in proof['observations']:
        if not isinstance(item, dict) or set(item) != {'trainer', 'family', 'battle_type', 'enemy_index'}:
            raise ValueError(f'context proof observation needs exactly trainer, family, battle_type, enemy_index: {item}')
        family = item['family']
        # exact family -> value pairing: a bit more or less than the whitelisted value is another battle
        if (family not in families or type(item['battle_type']) is not int or item['battle_type'] != families[family]
                or item['enemy_index'] not in context['enemy_indexes'] or item['trainer'] not in abi['gate']['trainers']):
            raise ValueError(f'context proof contains an observation outside the whitelist: {item}')
        seen.add((item['trainer'], family))
    needed = {(t, f) for t in abi['gate']['trainers'] for f in families}
    if seen != needed:
        raise ValueError('context proof must observe every trainer through every entry family')
    return 'synthetic' if synthetic else 'android'


SLOT_NAME = 'c8.module-stubs'      # the resident stub; the module itself is overlay 126 (no reserve memory)
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
        rows = reserve.validate_allocation(allocation, language)  # structural only; production builder reissues
        selected = [row for row in rows if row['name'] == name]
        if len(selected) != 1:
            raise ValueError('allocation receipt does not request ' + name)
        return dict(selected[0])
    if not isinstance(allocation, dict) or set(allocation) != ALLOCATION_FIELDS:
        raise ValueError(f'the base must come from a reserve.allocate receipt (exact fields {sorted(ALLOCATION_FIELDS)})')
    policy, digest = _reserve_policy()
    checks = (
        (allocation['schema'] == 1 and allocation['policy_sha256'] == digest
         and allocation['policy_version'] == policy['version'],
         'allocation receipt was not issued under the reserve policy in force'),
        (allocation['address_reserved'] is True and allocation['installed'] is False
         and allocation['installation_authorized'] is False, 'allocation receipt flags'),
        (allocation['language'] == language and baseline.INPUT_HASHES.get(allocation['input_sha256']) == language,
         'allocation receipt belongs to another ROM or language'),
        (_is_sha256(allocation['audit_sha256']), 'allocation audit hash'),
        (isinstance(allocation['requested'], dict) and name in allocation['requested'],
         f'allocation receipt does not request {name}'))
    for ok, message in checks:
        if not ok:
            raise ValueError(message)
    conditional = policy.get('conditional_parents', reserve.CONDITIONAL_REQUIREMENTS)
    slots = {part['name']: (entry['parent'], part) for entry in policy['subdivisions']
             for part in entry['parts'] if part['kind'] == 'payload'}
    expected = []
    for slot_name, size in allocation['requested'].items():
        if not isinstance(slot_name, str) or slot_name not in slots:
            raise ValueError(f'the reserve policy has no payload slot {slot_name}')
        if type(size) is not int or size <= 0:
            raise ValueError('requested size')
        parent, slot = slots[slot_name]
        if parent in conditional:
            raise ValueError(f'slot {slot_name} belongs to a conditional owner ({parent}): the reserve refuses it')
        if size > slot['bytes']:
            raise ValueError('requested size exceeds the slot capacity')
        expected.append({'name': slot_name, 'parent': parent, 'start': slot['start'], 'bytes': size, 'capacity': slot['bytes']})
    expected.sort(key=lambda row: row['start'])
    if allocation['assignments'] != expected:
        raise ValueError('allocation assignments differ from what the reserve policy grants')
    row = next(item for item in expected if item['name'] == name)
    if not (row['start'] % 4 == 0 and row['bytes'] % 4 == 0 and reserve.BASE <= row['start']
            and row['start'] + row['bytes'] <= reserve.END):
        raise ValueError('assignment outside the reserve range or unaligned')
    return dict(row)


ACTIVE_BYTE = 6        # offset of the `active` byte in the config header (<IHBBBBH2I)
HEADER_USED, HEADER_CRC = 0x80, 0x15E     # NDS header: used ROM size, CRC16 of the header


def _tables(data):
    """(FAT offset, FAT size, overlay table offset, overlay table size) of a cartridge image."""
    return struct.unpack_from('<4I', data, 0x48)


def _relation(candidate_sha256, inert_sha):
    if candidate_sha256 is None:
        return None
    return 'stage-inert-output' if candidate_sha256 == inert_sha else 'composed-candidate'


def _active_at(data, overlay):
    """ROM offset of the activation byte inside the module's file, found through the FAT of `data`."""
    fat = _tables(data)[0]
    start, end = struct.unpack_from('<II', data, fat + 8 * overlay['file_id'])
    at = start + overlay['config_offset'] + ACTIVE_BYTE
    if not start <= at < end:
        raise ValueError('the module file does not hold the activation byte')
    return at


def inert_view(data, receipt):
    """The same image with this stage's activation byte (inside the module's overlay file) cleared; pure.

    The builder's mandatory final gate is `sha256(inert_view(final_rom, receipt)) == candidate_sha256` (see
    `candidate_gate`)."""
    view = bytearray(data)
    view[_active_at(data, receipt['overlay'])] = 0
    return bytes(view)


def candidate_gate(final_rom, receipt):
    """Final gate before activation: the final ROM with the activation byte cleared must be the declared candidate."""
    candidate = receipt.get('candidate_sha256')
    if candidate is None:
        raise ValueError('the receipt declares no candidate: nothing to gate')
    if sha(inert_view(final_rom, receipt)) != candidate:
        raise ValueError('the final ROM with the activation byte cleared is not the candidate the proof was captured on')


def window_conflicts(data, window, size, own_id):
    """Overlay ids (other than the module's) whose RAM window touches [window, window + size)."""
    y9, y9_size = _tables(data)[2:]
    found = []
    for oid in range(y9_size // 32):
        row = struct.unpack_from('<8I', data, y9 + 32 * oid)
        if oid != own_id and row[2] and window < row[1] + row[2] + row[3] and row[1] < window + size:
            found.append(oid)
    return found


def _check_overlay_preimage(data, overlay):
    """The y9 row and the file of the placeholder are exactly the V4's, and the module window is clear of every
    overlay but the battle."""
    fat, _fat_size, y9, _y9_size = _tables(data)
    if list(struct.unpack_from('<8I', data, y9 + 32 * overlay['id'])) != overlay['placeholder_row']:
        raise ValueError('overlay placeholder row differs from the pin')
    start, end = struct.unpack_from('<II', data, fat + 8 * overlay['file_id'])
    if end - start != overlay['placeholder_file_bytes'] or sha(data[start:end]) != overlay['placeholder_file_sha256']:
        raise ValueError('overlay placeholder file differs from the pin')


def _prepare_module(data, language, work, *, stub_base, code_size=DEFAULT_CODE_SIZE,
                    config_size=DEFAULT_CONFIG_SIZE, activate=False, context_proof=None,
                    candidate_sha256=None, allow_synthetic=False, spec=None, check_placeholder=True):
    """Pure preparation: checks pins and compiles parts, grants no reserve permission.

    The caller must separately obtain and validate a grant before writing a stub.
    The legacy installer and the single-append producer share these exact parts.
    """
    abi = load_abi()
    stub_max = abi['stub']['max_bytes']
    spec = load_spec() if spec is None else spec
    arm = _Image(data)
    if bytes(arm.raw[0xC:0x10]) != b'IPKE':
        raise ValueError('unsupported game code')
    seam = _hex(abi['seam']['address'])
    old_target = _hex(abi['seam']['old_target'])
    if (arm.leggi(seam, 4).hex() != abi['seam']['old_bytes'] or
            bl_decode(seam, arm.leggi(seam, 4)) != old_target):
        raise ValueError('seam preimage differs: expected BL to the native reader')
    start, end = _hex(abi['constructor']['start']), _hex(abi['constructor']['end'])
    if sha(arm.leggi(start, end - start)) != abi['constructor']['sha256']:
        raise ValueError('constructor preimage differs')
    loader = _hex(abi['loader']['address'])
    if sha(arm.leggi(loader, abi['loader']['bytes'])) != abi['loader']['sha256']:
        raise ValueError('native reader preimage differs')
    setup = abi['setup']
    if sha(arm.leggi(_hex(setup['address']), setup['bytes'])) != setup['sha256']:
        raise ValueError('setup function preimage differs: the battle types it builds are no longer the pinned ones')
    overlay = abi['overlay']
    for name, pin in overlay['loader'].items():
        if sha(arm.leggi(_hex(pin['address']), pin['bytes'])) != pin['sha256']:
            raise ValueError(f'{name} preimage differs: the module loader is no longer the pinned one')
    if check_placeholder:
        _check_overlay_preimage(bytes(arm.raw), overlay)
    try:
        arm.off(stub_base, stub_max)
    except KeyError as exc:
        raise ValueError('assigned stub region is not inside one ARM9 segment') from exc
    if arm.leggi(stub_base, stub_max) != bytes(stub_max):
        raise ValueError('assigned stub region is occupied')
    window = _hex(overlay['window'])
    total = code_size + config_size
    if window + total > _hex(overlay['window_limit']):
        raise ValueError('module image exceeds its overlay window')
    conflicts = window_conflicts(bytes(arm.raw), window, total, overlay['id'])
    if not set(conflicts) <= set(overlay['allowed_conflicts']):
        raise ValueError(f'overlay window {window:#x} touches live overlays {conflicts}: HandleLoadOverlay would refuse more than the battle')
    context = abi['gate']['context']
    origin = None
    if activate:
        origin = validate_context_proof(context_proof, abi, language, candidate_sha256, allow_synthetic)
    config = configuration(data, spec, active=1 if activate else 0, battle_types=tuple(context['battle_types']),
                           enemy_indexes=tuple(context['enemy_indexes']))
    if len(config) > config_size:
        raise ValueError(f'config overflow: {len(config)} > {config_size}')
    blob, symbols = compile_native(work, window, window + code_size, config_size)
    if len(blob) > code_size:
        raise ValueError(f'code overflow: {len(blob)} > {code_size}')
    hook = symbols['rematch_hook']
    if not window <= hook & ~1 < window + len(blob):
        raise ValueError('hook outside the module code')
    stub, stub_symbols = compile_stub(work, stub_base, hook)
    image = blob + bytes(code_size - len(blob)) + config + bytes(config_size - len(config))
    return (arm, abi, stub_max, spec, seam, old_target, window, conflicts, origin, config, blob, symbols, hook, stub, stub_symbols, image)


def install(data, language, work, *, allocation=None, stub_offset=0, code_size=DEFAULT_CODE_SIZE,
            config_size=DEFAULT_CONFIG_SIZE, activate=False, context_proof=None, candidate_sha256=None,
            allow_synthetic=False, spec=None):
    """Patch a supported ROM image in memory: a 64-byte resident stub, the module as overlay 126, one seam.

    The stub address comes only from a `reserve.allocate` receipt for `c8.module-stubs` (plus `stub_offset`, the
    stub's offset in the shared slot); the module needs no reserve memory: its image is appended to the cartridge as
    the file of the placeholder overlay 126 and loaded at the pinned window by HandleLoadOverlay for the length of
    one seam call. Activation needs a context proof and `candidate_sha256`, the inert candidate ROM the proof was
    captured on (`context_proof['capture_rom_sha256']` must equal it)."""
    if language not in LANGUAGES:
        raise ValueError('language must be EN or IT')
    if allocation is None:
        raise ValueError('no reserve allocation receipt: the installer never chooses a base')
    for name, value in (('code_size', code_size), ('config_size', config_size)):
        if type(value) is not int or value <= 0 or value % 4:
            raise ValueError(f'{name} must be a positive multiple of 4')
    if type(stub_offset) is not int or stub_offset < 0 or stub_offset % 4:
        raise ValueError('stub_offset must be a non-negative multiple of 4')
    if candidate_sha256 is not None and not _is_sha256(candidate_sha256):
        raise ValueError('candidate_sha256 must be a lowercase sha256')
    assignment = check_allocation(allocation, language)
    abi = load_abi()
    stub_max = abi['stub']['max_bytes']
    if stub_offset + stub_max > assignment['bytes']:
        raise ValueError(f'the stub ({stub_max} bytes at +{stub_offset}) does not fit the reserve assignment ({assignment["bytes"]} bytes)')
    stub_base = assignment['start'] + stub_offset
    spec = load_spec() if spec is None else spec
    (arm, abi, stub_max, spec, seam, old_target, window, conflicts, origin, config, blob, symbols, hook, stub, stub_symbols, image) = _prepare_module(
        data, language, work, stub_base=stub_base, code_size=code_size, config_size=config_size,
        activate=activate, context_proof=context_proof, candidate_sha256=candidate_sha256,
        allow_synthetic=allow_synthetic, spec=spec)
    overlay, context = abi['overlay'], abi['gate']['context']
    new_bl = bl_thumb(seam, stub_base)
    arm.scrivi(stub_base, stub)
    arm.scrivi(seam, new_bl)
    if arm.leggi(stub_base, len(stub)) != stub or arm.leggi(seam, 4) != new_bl:
        raise ValueError('stub readback differs')
    out = arm.raw
    fat, _fat_size, y9, _y9_size = _tables(bytes(out))
    out += bytes(-len(out) % 4)
    file_start = len(out)
    out += image
    file_end = len(out)
    if len(out) > (128 * 1024 << out[0x14]):
        raise ValueError('the module file exceeds the cartridge capacity')
    struct.pack_into('<II', out, fat + 8 * overlay['file_id'], file_start, file_end)
    struct.pack_into('<8I', out, y9 + 32 * overlay['id'], overlay['id'], window, len(image), 0, window, window,
                     overlay['file_id'], overlay['flags_uncompressed'])
    struct.pack_into('<I', out, HEADER_USED, len(out))
    struct.pack_into('<H', out, HEADER_CRC, _common.crc16(bytes(out[:HEADER_CRC])))
    output = bytes(out)
    receipt = {
        'module': 'sgp131.rematches', 'language': language, 'input_sha256': sha(data), 'output_sha256': sha(output),
        'spec_sha256': sha(json.dumps(spec, sort_keys=True).encode()), 'abi_sha256': sha(json.dumps(abi, sort_keys=True).encode()),
        'seam': {'address': seam, 'old_bytes': abi['seam']['old_bytes'], 'old_target': old_target,
                 'new_bytes': new_bl.hex(), 'new_target': stub_base, 'resume': _hex(abi['seam']['resume'])},
        'allocation': copy.deepcopy(allocation), 'assignment': assignment,
        'stub': {'address': stub_base, 'offset': stub_offset, 'bytes': len(stub), 'sha256': sha(stub),
                 'entry': hook, 'symbols': {k: v for k, v in stub_symbols.items() if k == 'c8_stub'}},
        'overlay': {'id': overlay['id'], 'file_id': overlay['file_id'], 'window': window, 'image_bytes': len(image),
                    'image_sha256': sha(image), 'file_offset': file_start, 'config_offset': code_size,
                    'row': [overlay['id'], window, len(image), 0, window, window, overlay['file_id'], overlay['flags_uncompressed']],
                    'conflicts': conflicts},
        'code_allocated': code_size, 'config_allocated': config_size,
        'code_bytes': len(blob), 'code_sha256': sha(blob), 'config_address': window + code_size,
        'config_bytes': len(config), 'config_sha256': sha(config),
        'symbols': {k: v for k, v in symbols.items() if k.startswith('rematch')},
        'constructor_sha256_before': abi['constructor']['sha256'], 'loader_sha256': abi['loader']['sha256'],
        'active': 1 if activate else 0, 'function_state': 'active' if activate else 'inert',
        'candidate_sha256': candidate_sha256,
        'capture_rom_sha256': context_proof.get('capture_rom_sha256') if activate and origin == 'android' else None,
        'context': {'battle_types': context['battle_types'], 'enemy_indexes': context['enemy_indexes'],
                    'families': {name: item['battle_type'] for name, item in context['families'].items()},
                    'proof_origin': origin,
                    'proof_sha256': proof_digest(context_proof) if activate else None},
        'trainers': {str(t['trainer_id']): {label: {'sha256': t['variants'][label]['sha256'],
                                                    'tuples': _tuples(t, label)} for label in ('A', 'B')}
                     for t in spec['trainers']},
        'seed_policy': abi['seed_policy'], 'scope': spec['scope'], 'selector': spec['selector']}
    receipt['candidate_relation'] = _relation(candidate_sha256, sha(inert_view(output, receipt)))
    return output, receipt


def _tuples(trainer, label):
    """Independent tuple-level construction of a variant (used by receipts and by verify)."""
    slots = [dict(s, moves=list(s['moves'])) for s in trainer['baseline']]
    order = ['A'] if label == 'A' else ['A', 'B']
    for name in order:
        for change in trainer['variants'][name]['changes']:
            target = slots[change['slot']]
            for field in ('species', 'form', 'override', 'item', 'level', 'difficulty', 'capsule'):
                if field in change:
                    target[field] = change[field]['after']
            if 'moves' in change:
                target['moves'] = list(change['moves']['after'])
    return [[s['species'], s['form'], s['level'], s['difficulty'], s['override'], s['item'],
             list(s['moves']), s['capsule']] for s in slots]


def _diff_offsets(before, after, chunk=1 << 22):
    changed = []
    for start in range(0, len(before), chunk):
        end = min(start + chunk, len(before))
        if before[start:end] != after[start:end]:
            changed.extend(start + i for i in range(end - start) if before[start + i] != after[start + i])
    return changed


def verify(before, after, receipt, spec=None, require_measured=True):
    """Independent readback of an installed ROM against its receipt and the specification.

    `require_measured` (default True, as in `portable.verify` and `controls.verify`) refuses an active receipt whose
    proof origin is the synthetic harness; only tests pass False."""
    spec = load_spec() if spec is None else spec
    abi = load_abi()
    before, after = bytes(before), bytes(after)
    if sha(before) != receipt['input_sha256'] or sha(after) != receipt['output_sha256'] or len(after) < len(before):
        raise ValueError('ROM hashes differ from the receipt')
    arm_before, arm_after = _Image(before), _Image(after)
    seam = receipt['seam']['address']
    assignment = check_allocation(receipt.get('allocation'), receipt['language'])   # the stub slot is still the reserve's
    stub_info, ov = receipt['stub'], receipt['overlay']
    stub_base, stub_max = stub_info['address'], abi['stub']['max_bytes']
    if (receipt.get('assignment') != assignment or stub_base != assignment['start'] + stub_info['offset']
            or stub_info['offset'] % 4 or stub_info['offset'] + stub_max > assignment['bytes']
            or ov['id'] != abi['overlay']['id'] or ov['file_id'] != abi['overlay']['file_id']):
        raise ValueError('stub or overlay differ from the reserve assignment and the pins')
    code_allocated, config_allocated = receipt['code_allocated'], receipt['config_allocated']
    window = ov['window']
    if window != _hex(abi['overlay']['window']) or ov['image_bytes'] != code_allocated + config_allocated:
        raise ValueError('overlay window or image size differ from the pins')
    # --- the cartridge outside the owned ranges is byte-identical -----------------------------------------------
    fat, _fat_size, y9, _y9_size = _tables(before)
    file_start = len(before) + (-len(before) % 4)
    file_end = file_start + ov['image_bytes']
    if len(after) != file_end or ov['file_offset'] != file_start:
        raise ValueError('the module file is not appended at the end of the cartridge')
    if after[len(before):file_start] != bytes(file_start - len(before)):
        raise ValueError('cartridge padding is not zero')
    owned = {}
    for offset in range(arm_before.off(stub_base, stub_max), arm_before.off(stub_base, stub_max) + stub_max):
        owned[offset] = 'stub'
    for offset in range(arm_before.off(seam, 4), arm_before.off(seam, 4) + 4):
        owned[offset] = 'seam'
    for offset in range(y9 + 32 * ov['id'], y9 + 32 * ov['id'] + 32):
        owned[offset] = 'overlay row'
    for offset in range(fat + 8 * ov['file_id'], fat + 8 * ov['file_id'] + 8):
        owned[offset] = 'FAT entry'
    for offset in list(range(HEADER_USED, HEADER_USED + 4)) + list(range(HEADER_CRC, HEADER_CRC + 2)):
        owned[offset] = 'header'
    changed = _diff_offsets(before, after[:len(before)])
    stray = [offset for offset in changed if offset not in owned]
    if stray:
        raise ValueError(f'bytes changed outside the stub, the seam, the overlay row and the file table: {stray[:4]}')
    # --- pins that must survive ----------------------------------------------------------------------------------
    if arm_before.leggi(stub_base, stub_max) != bytes(stub_max):
        raise ValueError('assigned stub region was not empty before installation')
    if bl_decode(seam, arm_before.leggi(seam, 4)) != _hex(abi['seam']['old_target']) or \
            arm_before.leggi(seam, 4).hex() != receipt['seam']['old_bytes']:
        raise ValueError('seam preimage differs')
    _check_overlay_preimage(before, abi['overlay'])
    for name, pin in abi['overlay']['loader'].items():
        text = arm_after.leggi(_hex(pin['address']), pin['bytes'])
        if sha(text) != pin['sha256']:
            raise ValueError(f'{name} differs from the pin')
    if bl_decode(seam, arm_after.leggi(seam, 4)) != stub_base or arm_after.leggi(seam, 4) != bl_thumb(seam, stub_base):
        raise ValueError('seam readback differs')
    start, end = _hex(abi['constructor']['start']), _hex(abi['constructor']['end'])
    expected = bytearray(arm_before.leggi(start, end - start))
    expected[seam - start:seam - start + 4] = bl_thumb(seam, stub_base)
    if arm_after.leggi(start, end - start) != bytes(expected):
        raise ValueError('constructor differs beyond the seam')
    if arm_before.leggi(_hex(abi['loader']['address']), abi['loader']['bytes']) != \
            arm_after.leggi(_hex(abi['loader']['address']), abi['loader']['bytes']):
        raise ValueError('native reader changed')
    setup = abi['setup']
    if sha(arm_before.leggi(_hex(setup['address']), setup['bytes'])) != setup['sha256'] or \
            arm_after.leggi(_hex(setup['address']), setup['bytes']) != arm_before.leggi(_hex(setup['address']), setup['bytes']):
        raise ValueError('setup function differs from the pin')
    # --- the file table, the overlay row and the header ---------------------------------------------------------
    if struct.unpack_from('<II', after, fat + 8 * ov['file_id']) != (file_start, file_end):
        raise ValueError('file table entry differs from the appended module file')
    expected_row = (ov['id'], window, ov['image_bytes'], 0, window, window, ov['file_id'], abi['overlay']['flags_uncompressed'])
    if struct.unpack_from('<8I', after, y9 + 32 * ov['id']) != expected_row or list(expected_row) != ov['row']:
        raise ValueError('overlay row differs from the module')
    if struct.unpack_from('<I', after, HEADER_USED)[0] != len(after) or \
            struct.unpack_from('<H', after, HEADER_CRC)[0] != _common.crc16(after[:HEADER_CRC]):
        raise ValueError('cartridge header differs from the appended file')
    if len(after) > (128 * 1024 << after[0x14]):
        raise ValueError('the module file exceeds the cartridge capacity')
    conflicts = window_conflicts(after, window, ov['image_bytes'], ov['id'])
    if conflicts != ov['conflicts'] or not set(conflicts) <= set(abi['overlay']['allowed_conflicts']):
        raise ValueError(f'overlay window touches live overlays {conflicts}')
    # --- the module image and the resident stub, recompiled ------------------------------------------------------
    image = after[file_start:file_end]
    if sha(image) != ov['image_sha256']:
        raise ValueError('module image readback differs')
    with tempfile.TemporaryDirectory(prefix='rematch-verify-') as scratch:
        blob, symbols = compile_native(scratch, window, window + code_allocated, config_allocated)
        stub, _stub_symbols = compile_stub(scratch, stub_base, symbols['rematch_hook'])
    code = image[:code_allocated]
    if sha(code[:receipt['code_bytes']]) != receipt['code_sha256'] or code[receipt['code_bytes']:] != bytes(
            code_allocated - receipt['code_bytes']) or code[:len(blob)] != blob:
        raise ValueError('code readback differs')
    if arm_after.leggi(stub_base, stub_max) != stub + bytes(stub_max - len(stub)) or stub_info['bytes'] != len(stub) \
            or sha(stub) != stub_info['sha256'] or stub_info['entry'] != symbols['rematch_hook']:
        raise ValueError('resident stub differs from the recompiled stub')
    if not window <= symbols['rematch_hook'] & ~1 < window + receipt['code_bytes']:
        raise ValueError('hook outside the installed code')
    config = image[code_allocated:]
    size = receipt['config_bytes']
    if ov['config_offset'] != code_allocated or receipt['config_address'] != window + code_allocated:
        raise ValueError('config position differs from the overlay layout')
    if sha(config[:size]) != receipt['config_sha256'] or config[size:] != bytes(config_allocated - size):
        raise ValueError('config readback differs')
    magic, length, active, count, kinds, mask, reserved = struct.unpack_from('<IHBBBBH', config, 0)
    if (magic, length, reserved, active) != (MAGIC, size, 0, receipt['active']) or count != len(spec['trainers']):
        raise ValueError('config header differs')
    if _active_at(after, ov) != file_start + code_allocated + ACTIVE_BYTE:
        raise ValueError('activation byte position differs')
    if struct.unpack_from('<%dI' % kinds, config, 12) != tuple(receipt['context']['battle_types']) or \
            mask != sum(1 << i for i in receipt['context']['enemy_indexes']) or \
            list(receipt['context']['battle_types']) != abi['gate']['context']['battle_types']:
        raise ValueError('context whitelist differs')
    state = {0: 'inert', 1: 'active'}.get(active)      # recomputed from the installed byte, never from the receipt
    if state is None or receipt.get('function_state') != state:
        raise ValueError('function_state differs from the installed activation byte')
    candidate = receipt.get('candidate_sha256')
    if candidate is not None and not _is_sha256(candidate):
        raise ValueError('candidate_sha256')
    origin, proof_sha = receipt['context'].get('proof_origin'), receipt['context'].get('proof_sha256')
    capture = receipt.get('capture_rom_sha256')
    if state == 'inert':
        if origin is not None or proof_sha is not None or capture is not None:
            raise ValueError('an inert wrapper carries no context proof')
    else:
        if candidate is None or origin not in ('android', 'synthetic') or not _is_sha256(proof_sha):
            raise ValueError('an active wrapper needs its context proof (origin, hash) and its candidate ROM')
        if origin == 'synthetic':
            if require_measured:
                raise ValueError('the receipt carries a synthetic (test-only) context proof')
            if capture is not None:
                raise ValueError('a synthetic stand-in has no capture')
        elif capture is None or capture != candidate:
            raise ValueError('capture_rom_sha256 differs from candidate_sha256')
    if receipt.get('candidate_relation') != _relation(candidate, sha(inert_view(after, receipt))):
        raise ValueError('candidate relation differs from the installed bytes')
    res = Resources(before)
    for index, trainer in enumerate(spec['trainers']):
        tid, kind, o_base, o_a, o_b, zero, h_base, h_a, h_b = struct.unpack_from(
            '<6H3I', config, HEADER + index * DESCRIPTOR)
        if (tid, kind, zero) != (trainer['trainer_id'], TYPE_COUNT, 0):
            raise ValueError('descriptor differs')
        parts = {name: config[offset:offset + PARTY] for name, offset in (('base', o_base), ('A', o_a), ('B', o_b))}
        if (fnv(parts['base']), fnv(parts['A']), fnv(parts['B'])) != (h_base, h_a, h_b):
            raise ValueError('party fingerprint differs')
        if parts['base'] != res.parties[tid]:
            raise ValueError('baseline copy differs from the archive')
        for label in ('A', 'B'):
            tuples = [[s['species'], s['form'], s['level'], s['difficulty'], s['override'], s['item'],
                       s['moves'], s['capsule']] for s in decode_party(parts[label])]
            if tuples != _tuples(trainer, label) or tuples != receipt['trainers'][str(tid)][label]['tuples']:
                raise ValueError(f'variant {label} of trainer {tid} differs from the specification')
    return {'changed_rom_bytes': len(changed), 'appended_bytes': len(after) - len(before), 'seam_changed': True,
            'stub_bytes': len(stub), 'image_bytes': ov['image_bytes'], 'function_state': state,
            'candidate_relation': receipt['candidate_relation'],
            'code_bytes': receipt['code_bytes'], 'config_bytes': size, 'active': active,
            'constructor_unchanged_beyond_seam': True, 'neighbours_unchanged': True}


def prepare(data, language, work):
    """Prepare a non-authorizing inert UI overlay delta from the current map."""
    from . import cartridge_deltas
    return cartridge_deltas.derive_rematches(data, language, work)
