"""Rematch variants: ROM-free tests of the materialised configuration and the C core.

Synthetic parties and a synthetic specification stand in for the retail archives, so
the checks do not depend on private inputs. The real specification is checked for
internal consistency without a ROM; the ROM-level campaign is test_rematches_rom.
"""
import copy
import ctypes as C
import hashlib
import json
from pathlib import Path
import re
import struct
import subprocess
import tempfile
import unittest

from sgp131 import rematches

CORE = Path(__file__).resolve().parents[1] / 'features/rematch-variants/variants.c'
HEADER, DESCRIPTOR = 20, 24


def sha(data):
    return hashlib.sha256(data).hexdigest()


def slot(difficulty=255, override=0, level=60, species=22, form=0, item=0, moves=(1, 2, 3, 4), capsule=0):
    return dict(difficulty=difficulty, override=override, level=level, species=species, form=form,
                item=item, moves=list(moves), capsule=capsule)


def pack(slots):
    return b''.join(struct.pack('<BBHHH4HH', s['difficulty'], s['override'], s['level'],
                                s['species'] | (s['form'] << 10), s['item'], *s['moves'], s['capsule'])
                    for s in slots)


FALCON = [slot(level=68, species=22, moves=(355, 65, 366, 224)),
          slot(level=64, species=279, moves=(255, 403, 366, 56)),
          slot(level=68, species=277, item=273, moves=(283, 332, 97, 403)),
          slot(level=66, species=164, moves=(375, 355, 138, 417)),
          slot(level=70, species=398, moves=(370, 97, 413, 38)),
          slot(level=72, species=18, item=158, moves=(366, 119, 403, 413), capsule=11)]
BEETLE = [slot(level=70, species=469, override=32, moves=(103, 369, 403, 405)),
          slot(level=72, species=212, item=158, moves=(442, 14, 364, 400), capsule=12),
          slot(level=68, species=214, item=285, moves=(179, 364, 224, 32)),
          slot(level=70, species=284, moves=(403, 18, 405, 56)),
          slot(level=68, species=416, moves=(92, 455, 194, 403)),
          slot(level=69, species=127, moves=(12, 276, 224, 370))]
HEADER_BYTES = bytes.fromhex('0342000617001700170000000700000000000000')


def change(index, **fields):
    return dict(slot=index, **fields)


def synthetic_spec():
    def trainer(tid, base, a_changes, b_changes, ace):
        a_slots = copy.deepcopy(base)
        for c in a_changes:
            for key, value in c.items():
                if key == 'moves': a_slots[c['slot']]['moves'] = list(value['after'])
                elif key != 'slot': a_slots[c['slot']][key] = value['after']
        b_slots = copy.deepcopy(a_slots)
        for c in b_changes:
            for key, value in c.items():
                if key == 'moves': b_slots[c['slot']]['moves'] = list(value['after'])
                elif key != 'slot': b_slots[c['slot']][key] = value['after']
        return dict(trainer_id=tid, type=3, count=6, bytes=108, header_sha256=sha(HEADER_BYTES),
                    party_sha256=sha(pack(base)), baseline=[dict(slot=i, **s) for i, s in enumerate(base)],
                    ace=ace, variants=dict(A=dict(parent='baseline', sha256=sha(pack(a_slots)), changes=a_changes),
                                           B=dict(parent='A', sha256=sha(pack(b_slots)), changes=b_changes)),
                    legality=[])
    mv = lambda before, after: dict(before=list(before), after=list(after))
    fal = trainer(712, FALCON,
                  [change(1, moves=mv((255, 403, 366, 56), (58, 403, 366, 56))),
                   change(5, moves=mv((366, 119, 403, 413), (366, 355, 403, 413)))],
                  [change(0, species=dict(before=22, after=169), moves=mv((355, 65, 366, 224), (355, 413, 369, 440)))],
                  dict(slot=5, species=18, level=72))
    bee = trainer(713, BEETLE,
                  [change(0, moves=mv((103, 369, 403, 405), (182, 369, 403, 405))), change(2, item=dict(before=285, after=0))],
                  [change(3, species=dict(before=284, after=205), moves=mv((403, 18, 405, 56), (191, 229, 360, 89)))],
                  dict(slot=1, species=212, level=72))
    return {'schema': 1, 'type_count': 0x0306, 'party_bytes': 108, 'trainers': [fal, bee], 'moves': {}, 'species': {}}


def synthetic_inputs():
    return ({712: pack(FALCON), 713: pack(BEETLE)}, {712: HEADER_BYTES, 713: HEADER_BYTES})


class CoreMixin:
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        target = Path(cls.temp.name) / 'variants.dylib'
        subprocess.run(['clang', '-shared', '-fPIC', '-Wall', '-Wextra', '-Werror', str(CORE), '-o', str(target)],
                       check=True, capture_output=True)
        cls.lib = C.CDLL(str(target))
        cls.lib.rematch_apply.argtypes = [C.c_void_p, C.c_uint32, C.c_uint32, C.c_uint32, C.c_uint32,
                                          C.c_void_p, C.c_uint32]
        cls.lib.rematch_apply.restype = C.c_int

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def run_core(self, config, buffer, trainer, seed, plus=1, type_count=0x0306):
        guard = C.create_string_buffer(b'\xC3' * 8 + buffer + b'\x3C' * 8, len(buffer) + 16)
        image = C.create_string_buffer(config, len(config))
        result = self.lib.rematch_apply(C.addressof(guard) + 8, trainer, type_count, plus, seed, image, len(config))
        self.assertEqual(guard.raw[:8], b'\xC3' * 8)
        self.assertEqual(guard.raw[-8:], b'\x3C' * 8)
        self.assertEqual(image.raw, config)
        return result, guard.raw[8:-8]

    @staticmethod
    def seed(trainer, outcome):
        return next(s for s in range(0x20000, 0x20100) if ((s ^ (s >> 16) ^ trainer) & 1) == outcome)


class MaterialisedConfiguration(CoreMixin, unittest.TestCase):
    def config(self, **kwargs):
        parties, headers = synthetic_inputs()
        return rematches.materialize(synthetic_spec(), parties, headers, **kwargs)

    def expected(self):
        spec = synthetic_spec()
        result = {}
        for trainer in spec['trainers']:
            slots = copy.deepcopy(trainer['baseline'])
            for label in ('A', 'B'):
                for c in trainer['variants'][label]['changes']:
                    for key, value in c.items():
                        if key == 'slot': continue
                        slots[c['slot']]['moves' if key == 'moves' else key] = value['after']
                result[(trainer['trainer_id'], label)] = pack(slots)
        return result

    def test_layout_and_independent_header_fields(self):
        config = self.config()
        self.assertEqual(len(config), 20 + 2 * 24 + 2 * 3 * 108)
        magic, size, active, count, types, mask, reserved = struct.unpack_from('<IHBBBBH', config, 0)
        self.assertEqual((magic, size, active, count, types, mask, reserved),
                         (0x31564D52, len(config), 0, 2, 1, 0b10, 0))
        self.assertEqual(struct.unpack_from('<2I', config, 12), (1, 0))
        self.assertEqual(len(config), 20 + 2 * 24 + 2 * 3 * 108)
        trainer, kind = struct.unpack_from('<2H', config, HEADER)
        self.assertEqual((trainer, kind), (712, 0x0306))
        self.assertEqual(self.config(active=1)[6], 1)
        self.assertEqual(len(self.config(battle_types=(1, 5), enemy_indexes=(1, 3))[:20]), 20)

    def test_normal_unknown_and_invalid_records_noop(self):
        config = self.config()
        base = pack(FALCON)
        damaged = bytearray(base); damaged[9] ^= 0x10
        for outcome in (0, 1):
            seed = self.seed(712, outcome)
            for trainer, plus, kind, buffer in ((712, 0, 0x0306, base), (21, 1, 0x0306, base),
                                                (712, 1, 0x0603, base), (712, 1, 0x0305, base),
                                                (712, 1, 0x0306, bytes(damaged))):
                with self.subTest(trainer=trainer, plus=plus, kind=hex(kind), outcome=outcome):
                    self.assertEqual(self.run_core(config, buffer, trainer, seed, plus, kind), (0, buffer))

    def test_both_selector_outcomes_and_seed_unchanged(self):
        config = self.config()
        expected = self.expected()
        for trainer, source in ((712, FALCON), (713, BEETLE)):
            for outcome, label in ((0, 'A'), (1, 'B')):
                seed = self.seed(trainer, outcome)
                with self.subTest(trainer=trainer, label=label):
                    result, after = self.run_core(config, pack(source), trainer, seed)
                    self.assertEqual((result, after), (1 + outcome, expected[(trainer, label)]))
                    # nothing is stored between calls: the same arguments give the same party
                    self.assertEqual(self.run_core(config, pack(source), trainer, seed), (result, after))

    def test_four_complete_outputs_and_canaries(self):
        config = self.config()
        expected = self.expected()
        self.assertEqual(len(set(expected.values())), 4)
        for (trainer, label), party in expected.items():
            source = pack(FALCON if trainer == 712 else BEETLE)
            outcome = 'AB'.index(label)
            result, after = self.run_core(config, source, trainer, self.seed(trainer, outcome))
            self.assertEqual((result, after), (1 + outcome, party))
            self.assertEqual(len(after), 108)

    def test_bad_config_offsets_counts_ids_hash_refuse(self):
        parties, headers = synthetic_inputs()
        spec = synthetic_spec()
        def refused(message, mutate=None, parties_=None, headers_=None, **kwargs):
            candidate = copy.deepcopy(spec)
            if mutate: mutate(candidate)
            with self.assertRaisesRegex(ValueError, message):
                rematches.materialize(candidate, parties_ or parties, headers_ or headers, **kwargs)
        changed = bytearray(parties[712]); changed[5] ^= 1
        refused('party preimage', parties_={**parties, 712: bytes(changed)})
        refused('party preimage', parties_={**parties, 712: parties[712][:90]})
        refused('header preimage', headers_={**headers, 713: bytes(20)})
        refused('missing', parties_={712: parties[712]})
        refused('format|count|bytes', lambda s: s['trainers'][0].update(count=5))
        refused('format|count|bytes', lambda s: s['trainers'][0].update(type=2))
        refused('variant preimage|before', lambda s: s['trainers'][0]['variants']['A']['changes'][0]['moves'].update(before=[1, 2, 3, 4]))
        refused('variant hash', lambda s: s['trainers'][0]['variants']['A'].update(sha256='0' * 64))
        refused('variant hash', lambda s: s['trainers'][1]['variants']['B'].update(sha256='1' * 64))
        refused('duplicate trainer', lambda s: s['trainers'][1].update(trainer_id=712))
        refused('trainers', lambda s: s.update(trainers=s['trainers'] * 3))
        refused('trainers', lambda s: s.update(trainers=[]))
        refused('schema', lambda s: s.update(schema=2))
        refused('type_count', lambda s: s.update(type_count=0x0603))
        refused('context', battle_types=(1, 2, 3))
        refused('context', enemy_indexes=(8,))
        refused('context', active=2)

    def test_levels_IV_capsules_and_aces_preserved(self):
        parties, headers = synthetic_inputs()
        def changed(trainer_index, label, edit):
            spec = synthetic_spec()
            variants = spec['trainers'][trainer_index]['variants']
            edit(variants[label]['changes'])
            # recompute the declared hash for the edited transformation so only policy can refuse
            return spec
        # a level/IV/capsule change is expressed as an extra transformation
        for field, before, after in (('level', 68, 69), ('difficulty', 255, 254), ('capsule', 0, 1)):
            spec = synthetic_spec()
            spec['trainers'][0]['variants']['A']['changes'].append(change(0, **{field: dict(before=before, after=after)}))
            with self.assertRaisesRegex(ValueError, 'level|difficulty|capsule|preserve|variant hash'):
                rematches.materialize(spec, parties, headers)
        spec = synthetic_spec()
        spec['trainers'][0]['variants']['B']['changes'].append(change(5, species=dict(before=18, after=22)))
        with self.assertRaisesRegex(ValueError, 'ace|preserve|variant hash|species'):
            rematches.materialize(spec, parties, headers)
        spec = synthetic_spec()
        spec['trainers'][1]['ace'] = dict(slot=1, species=212, level=73)
        with self.assertRaisesRegex(ValueError, 'ace'):
            rematches.materialize(spec, parties, headers)
        # the good specification keeps every level, IV byte, capsule and ace
        config = self.config()
        for trainer, source in ((712, FALCON), (713, BEETLE)):
            for outcome in (0, 1):
                _, after = self.run_core(config, pack(source), trainer, self.seed(trainer, outcome))
                for index, original in enumerate(source):
                    member = after[index * 18:(index + 1) * 18]
                    self.assertEqual((member[0], member[2:4], member[16:18]),
                                     (original['difficulty'], struct.pack('<H', original['level']),
                                      struct.pack('<H', original['capsule'])))


class RealSpecificationWithoutRom(unittest.TestCase):
    def test_declared_hashes_follow_from_declared_transformations(self):
        spec = rematches.load_spec()
        self.assertEqual(spec['schema'], 1)
        self.assertEqual([t['trainer_id'] for t in spec['trainers']], [712, 713])
        for trainer in spec['trainers']:
            base = [dict(s) for s in trainer['baseline']]
            self.assertEqual(sha(pack(base)), trainer['party_sha256'])
            a = rematches.apply_changes(base, trainer['variants']['A']['changes'])
            self.assertEqual(sha(pack(a)), trainer['variants']['A']['sha256'])
            b = rematches.apply_changes(a, trainer['variants']['B']['changes'])
            self.assertEqual(sha(pack(b)), trainer['variants']['B']['sha256'])
            self.assertEqual(len({sha(pack(x)) for x in (base, a, b)}), 3)


# --- C2/C3/C5: reserve receipt, proof binding, composition ---------------------------------------------------
import sys  # noqa: E402

sys.path.insert(0, str(CORE.parent / 'test'))
import rom_fixture as fx  # noqa: E402
from sgp131.test_controls import Intervals  # noqa: E402


class AllocationReceipt(unittest.TestCase):
    """The base is accepted only from a reserve.allocate receipt checked against the policy in force."""

    def check(self, language='EN', **override):
        return rematches.check_allocation(fx.declared_allocation('EN', **override), language)

    def test_the_declared_double_is_accepted_and_the_real_policy_refuses_it(self):
        with fx.declared_reserve():
            row = self.check()
        self.assertEqual(row, {'name': rematches.SLOT_NAME, 'parent': 'test.declared-parent', 'start': fx.STUB_START,
                               'bytes': fx.STUB_BYTES, 'capacity': fx.STUB_BYTES})
        with fx.real_reserve(), self.assertRaisesRegex(ValueError, 'policy in force'):
            self.check()

    def test_the_real_policy_has_the_stub_slot_but_cannot_grant_it_yet(self):
        """c8.module-stubs (192 B at 0x023D59E0) is in the product map under field-guide.code, a conditional owner: even
        a receipt carrying the real policy digest is refused (INTEGRATION.md asks Codex to lift the condition)."""
        policy, digest = rematches._reserve_policy()
        parts = {part['name']: (entry['parent'], part) for entry in policy['subdivisions'] for part in entry['parts']}
        parent, part = parts[rematches.SLOT_NAME]
        self.assertEqual((parent, part['start'], part['bytes']), ('field-guide.code', fx.STUB_START, 192))
        forged = fx.declared_allocation('EN', policy_version=policy['version'], policy_sha256=digest)
        forged['assignments'][0].update(parent=parent)
        with self.assertRaisesRegex(ValueError, 'conditional'):
            rematches.check_allocation(forged, 'EN')

    def test_every_forgery_of_a_good_receipt_is_refused(self):
        base = fx.declared_allocation('EN')
        row, size = base['assignments'][0], fx.STUB_BYTES
        cases = {
            'policy digest': dict(policy_sha256='1' * 64), 'policy version': dict(policy_version='sgp131-resident-5'),
            'schema': dict(schema=2), 'language': dict(language='IT'), 'input is not a V4': dict(input_sha256='2' * 64),
            'input of the other language': dict(input_sha256=next(h for h, l in fx.INPUT_HASHES.items() if l == 'IT')),
            'installed': dict(installed=True), 'authorized': dict(installation_authorized=True),
            'not reserved': dict(address_reserved=False), 'audit hash': dict(audit_sha256='zz'),
            'name not requested': dict(requested={'other.slot': size}),
            'unknown slot': dict(requested={rematches.SLOT_NAME: size, 'nobody.slot': 4}),
            'size over capacity': dict(requested={rematches.SLOT_NAME: size + 4}, assignments=[dict(row, bytes=size + 4)]),
            'start moved': dict(assignments=[dict(row, start=row['start'] + 4)]),
            'bytes differ from the request': dict(assignments=[dict(row, bytes=size - 4)]),
            'capacity': dict(assignments=[dict(row, capacity=size * 2)]), 'parent': dict(assignments=[dict(row, parent='x')]),
            'extra assignment': dict(assignments=[row, dict(row, name='x')]), 'no assignment': dict(assignments=[]),
        }
        with fx.declared_reserve():
            for name, override in cases.items():
                with self.subTest(name), self.assertRaises(ValueError):
                    rematches.check_allocation(dict(base, **override), 'EN')
            for field in list(base):
                broken = dict(base)
                del broken[field]
                with self.subTest(missing=field), self.assertRaises(ValueError):
                    rematches.check_allocation(broken, 'EN')
            for junk in (None, [], 'receipt', {**base, 'extra': 1}):
                with self.subTest(junk=type(junk).__name__), self.assertRaises(ValueError):
                    rematches.check_allocation(junk, 'EN')

    def test_a_conditional_owner_is_refused_even_with_the_real_digest(self):
        policy, digest = rematches._reserve_policy()
        parents = list(policy['subdivisions'])[0]['parent']
        conditional = next(iter(rematches.reserve.CONDITIONAL_REQUIREMENTS))
        part = next(p for e in policy['subdivisions'] if e['parent'] == conditional for p in e['parts'] if p['kind'] == 'payload')
        forged = fx.declared_allocation('EN', policy_version=policy['version'], policy_sha256=digest,
                                        requested={part['name']: part['bytes']},
                                        assignments=[{'name': part['name'], 'parent': conditional, 'start': part['start'],
                                                      'bytes': part['bytes'], 'capacity': part['bytes']}])
        with self.assertRaisesRegex(ValueError, 'conditional'):
            rematches.check_allocation(forged, 'EN', part['name'])
        self.assertTrue(parents)


class ProofBinding(unittest.TestCase):
    """C3: a capture is bound to the language and to the inert candidate ROM that was played."""

    def proof(self, **over):
        record = {'language': 'EN', 'capture_file': 'captures/rematch.json', 'build_id': 'candidate-example',
                  'capture_rom_sha256': fx.CANDIDATE,
                  'observations': [{'trainer': t, 'family': f, 'battle_type': b, 'enemy_index': 1}
                                   for t in (712, 713) for f, b in (('phone', 0x1), ('dojo-sequence', 0x801))]}
        record.update(over)
        return record

    def validate(self, proof, candidate=fx.CANDIDATE, language='EN', synthetic=False):
        return rematches.validate_context_proof(proof, rematches.load_abi(), language, candidate, synthetic)

    def test_a_bound_capture_is_android_and_a_mismatch_is_refused(self):
        self.assertEqual(self.validate(self.proof()), 'android')
        other = hashlib.sha256(b'another ROM').hexdigest()
        with self.assertRaisesRegex(ValueError, 'another ROM'):
            self.validate(self.proof(capture_rom_sha256=other))
        with self.assertRaisesRegex(ValueError, 'another ROM'):
            self.validate(self.proof(), candidate=other)
        with self.assertRaisesRegex(ValueError, 'language'):
            self.validate(self.proof(), language='IT')
        for bad in (None, '', 'ABC', 7):
            with self.subTest(candidate=bad), self.assertRaisesRegex(ValueError, 'candidate_sha256'):
                self.validate(self.proof(), candidate=bad)
        for missing in ('capture_file', 'build_id', 'capture_rom_sha256'):
            with self.subTest(missing=missing), self.assertRaisesRegex(ValueError, 'identity field'):
                self.validate({k: v for k, v in self.proof().items() if k != missing})

    def test_a_synthetic_stand_in_is_refused_without_the_test_flag_and_still_needs_a_candidate(self):
        synthetic = fx.synthetic_proof('EN')
        with self.assertRaisesRegex(ValueError, 'synthetic'):
            self.validate(synthetic)
        self.assertEqual(self.validate(synthetic, synthetic=True), 'synthetic')
        with self.assertRaisesRegex(ValueError, 'candidate_sha256'):
            self.validate(synthetic, candidate=None, synthetic=True)


class EntryFamilies(unittest.TestCase):
    """B1: one exact battleType per entry family, in the pin file and in the proof."""

    def test_the_pin_file_declares_a_value_per_family(self):
        context = rematches.load_abi()['gate']['context']
        self.assertEqual({k: v['battle_type'] for k, v in context['families'].items()}, {'phone': 0x1, 'dojo-sequence': 0x801})
        self.assertEqual(context['battle_types'], [0x1, 0x801])
        self.assertNotIn('status', context)

    def test_the_setup_function_that_builds_the_values_is_pinned(self):
        setup = rematches.load_abi()['setup']
        self.assertEqual((setup['address'], setup['bytes']), ('0x02051370', 184))
        self.assertRegex(setup['sha256'], r'^[0-9a-f]{64}$')

    def proof(self, **over):
        record = {'language': 'EN', 'capture_file': 'captures/rematch.json', 'build_id': 'candidate-example',
                  'capture_rom_sha256': fx.CANDIDATE,
                  'observations': [{'trainer': t, 'family': f, 'battle_type': b, 'enemy_index': 1}
                                   for t in (712, 713) for f, b in (('phone', 1), ('dojo-sequence', 0x801))]}
        record.update(over)
        return record

    def validate(self, proof):
        return rematches.validate_context_proof(proof, rematches.load_abi(), 'EN', fx.CANDIDATE)

    def test_a_faithful_proof_for_both_families_is_accepted(self):
        self.assertEqual(self.validate(self.proof()), 'android')

    def test_every_other_pairing_bit_and_shape_is_refused(self):
        def with_first(**fields):
            record = self.proof()
            record['observations'][0] = dict(record['observations'][0], **fields)
            return record
        cases = {'phone with the sequence value': with_first(battle_type=0x801),
                 'sequence with the phone value': with_first(family='dojo-sequence', battle_type=1),
                 'phone with doubles': with_first(battle_type=0x3), 'phone with 0x401': with_first(battle_type=0x401),
                 'sequence with an extra bit': with_first(family='dojo-sequence', battle_type=0x803),
                 'sequence with BATTLE_TYPE_TRAINER dropped': with_first(family='dojo-sequence', battle_type=0x800),
                 'unknown family': with_first(family='gym'), 'entry key instead of family': None,
                 'enemy index': with_first(enemy_index=2), 'trainer': with_first(trainer=711),
                 'string value': with_first(battle_type='1')}
        legacy = self.proof()
        legacy['observations'] = [{k if k != 'family' else 'entry': v for k, v in o.items()} for o in legacy['observations']]
        cases['entry key instead of family'] = legacy
        for name, proof in cases.items():
            with self.subTest(name), self.assertRaises(ValueError):
                self.validate(proof)
        only_phone = self.proof()
        only_phone['observations'] = [o for o in only_phone['observations'] if o['family'] == 'phone']
        only_sequence = self.proof()
        only_sequence['observations'] = [o for o in only_sequence['observations'] if o['family'] == 'dojo-sequence']
        one_trainer = self.proof()
        one_trainer['observations'] = [o for o in one_trainer['observations'] if o['trainer'] == 712]
        for name, proof in (('phone only', only_phone), ('sequence only', only_sequence), ('one trainer', one_trainer)):
            with self.subTest(name), self.assertRaisesRegex(ValueError, 'every trainer'):
                self.validate(proof)


class UiComposition(unittest.TestCase):
    """The pinned intervals, the stub slot and the overlay window never overlap what sgp131/ui.py writes."""

    def test_pins_are_clear_of_the_ui_writes(self):
        abi = rematches.load_abi()
        rows = [('seam', rematches._hex(abi['seam']['address']), 4),
                ('constructor', rematches._hex(abi['constructor']['start']),
                 rematches._hex(abi['constructor']['end']) - rematches._hex(abi['constructor']['start'])),
                ('reader', rematches._hex(abi['loader']['address']), abi['loader']['bytes']),
                ('setup function', rematches._hex(abi['setup']['address']), abi['setup']['bytes']),
                ('HandleLoadOverlay', rematches._hex(abi['overlay']['loader']['HandleLoadOverlay']['address']), 300),
                ('UnloadOverlayByID', rematches._hex(abi['overlay']['loader']['UnloadOverlayByID']['address']), 48),
                ('tm table', rematches._hex(abi['tm_table']['address']), 2 * abi['tm_table']['count']),
                ('stub slot', fx.STUB_START, fx.STUB_BYTES)]
        for name, start, size in rows:
            for ui_name, ui_start, ui_size in Intervals.UI_WRITES:
                with self.subTest(pin=name, ui=ui_name):
                    self.assertTrue(start + size <= ui_start or ui_start + ui_size <= start, (name, ui_name))

    def test_the_overlay_window_is_not_arm9_memory_the_ui_writes(self):
        """The window (0x0226B000) lies in the overlay area; the UI writes overlay 54 at 0x021E5900 and ARM9 reserve bytes."""
        window = int(rematches.load_abi()['overlay']['window'], 16)
        for name, start, size in Intervals.UI_WRITES:
            self.assertTrue(window + sum(fx.SIZES) <= start or start + size <= window, name)


class ReceiptHygiene(unittest.TestCase):
    def test_no_process_state_is_written_by_the_code(self):
        source = (CORE.parents[2] / 'sgp131/rematches.py').read_text()
        for word in ('SOURCE_READY_FOR_REVIEW', 'ANDROID_ACCEPTED', "'status'", 'UNPROVEN'):
            self.assertNotIn(word, source, word)
        self.assertIsNone(re.search(r'\bnot run\b', source))


if __name__ == '__main__':
    unittest.main()
