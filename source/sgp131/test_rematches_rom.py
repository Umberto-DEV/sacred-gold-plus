"""Class B: the real EN/IT candidate ROMs, read and patched in memory only.

Part 1 (R1) checks the authored data against the actual archives; part 2 (R2) checks the
installer and drives the REAL trainer-party constructor (Unicorn) before and after the
wrapper is installed. Inputs default to the balance493 candidates under local/experiments.
A missing input skips with a reason; SGP_REMATCH_REQUIRE_INPUTS=1 makes it fail instead.
A present input with the wrong sha256 always fails. Nothing is written to disk.

Evidence classes: host Python (parts of part 1), ARM instructions executed in Unicorn on
the real ARM9 bytes (part 2 constructor tests), Android (absent: not claimed here).
"""
import copy
import json
import hashlib
from pathlib import Path
import struct
import sys
import tempfile
import unittest

import ndspy.narc

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'source/features/rematch-variants/test'))
sys.path.insert(0, str(ROOT / 'source/quality-audit'))

import rom_fixture as fx                                     # noqa: E402
import constructor_bench as bench                            # noqa: E402
from sgp131 import rematches                                 # noqa: E402

PRET = Path(__import__('os').environ.get('SGP_PRET_SOURCE') or ROOT / 'local/tools/pokeheartgold')

# Transcribed by hand from the audit and the plan (independent of the JSON): (species, level, override, item,
# moves, capsule) of the retail-derived baseline and the authored changes.
BASE = {
    712: [(22, 68, 0, 0, [355, 65, 366, 224], 0), (279, 64, 0, 0, [255, 403, 366, 56], 0),
          (277, 68, 0, 273, [283, 332, 97, 403], 0), (164, 66, 0, 0, [375, 355, 138, 417], 0),
          (398, 70, 0, 0, [370, 97, 413, 38], 0), (18, 72, 0, 158, [366, 119, 403, 413], 11)],
    713: [(469, 70, 32, 0, [103, 369, 403, 405], 0), (212, 72, 0, 158, [442, 14, 364, 400], 12),
          (214, 68, 0, 285, [179, 364, 224, 32], 0), (284, 70, 0, 0, [403, 18, 405, 56], 0),
          (416, 68, 0, 0, [92, 455, 194, 403], 0), (127, 69, 0, 0, [12, 276, 224, 370], 0)]}
EDIT_A = {712: {1: {'moves': [58, 403, 366, 56]}, 2: {'moves': [283, 332, 97, 263]},
                3: {'moves': [94, 355, 403, 417]}, 5: {'moves': [366, 355, 403, 413]}},
          713: {0: {'moves': [182, 369, 403, 405]}, 1: {'moves': [442, 14, 450, 400]},
                2: {'item': 0, 'moves': [179, 157, 224, 370]}, 4: {'moves': [92, 455, 456, 403]},
                5: {'moves': [404, 276, 224, 370]}}}
EDIT_B = {712: {0: {'species': 169, 'override': 0, 'moves': [355, 413, 369, 440]}, 4: {'moves': [370, 369, 413, 38]}},
          713: {0: {'moves': [94, 369, 403, 405]}, 3: {'species': 205, 'override': 0, 'moves': [191, 229, 360, 89]}}}


def expected_team(trainer, label):
    team = [dict(species=s, level=l, override=o, item=i, moves=list(m), capsule=c) for s, l, o, i, m, c in BASE[trainer]]
    for index, edit in EDIT_A[trainer].items():
        team[index].update(edit)
    if label == 'B':
        for index, edit in EDIT_B[trainer].items():
            team[index].update(edit)
    return team


class RomCase(unittest.TestCase):
    def need(self, language):
        try:
            return fx.rom(language)
        except fx.MissingInput as exc:
            if fx.REQUIRE_INPUTS:
                self.fail(str(exc))
            self.skipTest(str(exc))


# ===================================================================== part 1

class AuthoredDataOnRealArchives(RomCase):
    def test_configuration_is_identical_for_en_and_it_and_fits_the_allocation(self):
        configs = {}
        for language in ('EN', 'IT'):
            data = self.need(language)
            configs[language] = rematches.configuration(data)
            self.assertEqual(len(configs[language]), 716)
            self.assertLessEqual(len(configs[language]), fx.SIZES[1])
        self.assertEqual(configs['EN'], configs['IT'])

    def test_four_complete_teams_equal_the_hand_transcribed_tuples(self):
        for language in ('EN', 'IT'):
            data = self.need(language)
            config = rematches.configuration(data)
            parties = fx.archives(language).files('a/0/5/6')
            for index, trainer in enumerate((712, 713)):
                tid, kind, o_base, o_a, o_b = struct.unpack_from('<5H', config, 20 + index * 24)
                self.assertEqual((tid, kind), (trainer, 0x0306))
                self.assertEqual(config[o_base:o_base + 108], bytes(parties[trainer]))
                for label, offset in (('A', o_a), ('B', o_b)):
                    with self.subTest(language=language, trainer=trainer, label=label):
                        got = [dict(species=s['species'], level=s['level'], override=s['override'], item=s['item'],
                                    moves=s['moves'], capsule=s['capsule'])
                               for s in rematches.decode_party(config[offset:offset + 108])]
                        self.assertEqual(got, expected_team(trainer, label))

    def test_levels_IV_capsules_aces_and_unique_species_preserved(self):
        data = self.need('EN')
        config = rematches.configuration(data)
        for index, trainer in enumerate((712, 713)):
            o_base, o_a, o_b = struct.unpack_from('<3H', config, 20 + index * 24 + 4)
            base = rematches.decode_party(config[o_base:o_base + 108])
            for offset in (o_a, o_b):
                team = rematches.decode_party(config[offset:offset + 108])
                self.assertEqual([(s['level'], s['difficulty'], s['capsule']) for s in team],
                                 [(s['level'], s['difficulty'], s['capsule']) for s in base])
                self.assertTrue(all(s['difficulty'] == 255 and s['form'] == 0 for s in team))
                self.assertEqual(len({s['species'] for s in team}), 6)
                ace = (5, 18) if trainer == 712 else (1, 212)
                self.assertEqual((team[ace[0]]['species'], team[ace[0]]['level']), (ace[1], 72))
        self.assertEqual(expected_team(713, 'A')[2]['item'], 0)      # Damp Rock removed in both variants
        self.assertEqual(expected_team(713, 'B')[2]['item'], 0)

    def names(self, language):
        import hgss_text
        data = self.need(language)
        chars, commands = hgss_text.load_charmap(PRET / 'charmap.txt')
        messages = fx.archives(language).files('a/0/2/7')
        return {kind: hgss_text.read_bank(messages[bank], chars, commands)
                for kind, bank in (('move', 750), ('species', 237), ('item', 222))}

    def test_move_species_and_item_names_match_the_specification_in_both_languages(self):
        if not (PRET / 'charmap.txt').is_file():
            self.skipTest('pret reference charmap not available')
        spec = rematches.load_spec()
        for language, key in (('EN', 'en'), ('IT', 'it')):
            banks = self.names(language)
            for move, meaning in spec['moves'].items():
                self.assertEqual(banks['move'][int(move)]['text'], meaning[key], f'{language} move {move}')
            for species, meaning in spec['species'].items():
                self.assertEqual(banks['species'][int(species)]['text'], meaning[key], f'{language} species {species}')
            for item, meaning in spec['items'].items():
                self.assertEqual(banks['item'][int(item)]['text'], meaning[key], f'{language} item {item}')

    def test_new_move_ids_mean_what_the_plan_says_and_reused_ids_are_not_used(self):
        # (id, effect, category, power, type): read by hand from the audit; categories 0 physical 1 special 2 status
        expected = {263: (169, 0, 70, 0), 94: (72, 1, 90, 14), 182: (111, 2, 0, 0), 450: (224, 0, 60, 6),
                    157: (31, 0, 75, 5), 456: (32, 2, 0, 6), 404: (0, 0, 80, 6), 191: (112, 2, 0, 4),
                    229: (129, 0, 20, 0), 360: (219, 0, 1, 8), 89: (147, 0, 100, 4), 369: (228, 0, 70, 6),
                    440: (209, 0, 70, 3), 58: (5, 1, 95, 15), 370: (229, 0, 120, 1), 355: (214, 2, 0, 2),
                    413: (198, 0, 120, 2)}
        reused = {6, 27, 134, 140, 160, 169, 176}        # names differ from retail in this hack
        for language in ('EN', 'IT'):
            self.need(language)
            records = fx.archives(language).files('a/0/1/1')
            for move, (effect, category, power, kind) in expected.items():
                record = records[move]
                self.assertEqual((struct.unpack_from('<H', record, 0)[0], record[2], record[3], record[4]),
                                 (effect, category, power, kind), f'{language} move {move}')
        used = {int(m) for m in rematches.load_spec()['moves']}
        self.assertEqual(used & reused, set())

    def test_new_species_types_and_every_new_pair_is_legal_by_an_independent_reading(self):
        import re
        data = self.need('EN')
        res = fx.archives('EN')
        personal, wotbl, eggs = res.files('a/0/0/2'), res.files('a/0/3/3'), res.files('a/2/2/9')
        self.assertEqual([personal[169][6:8], personal[205][6:8], personal[284][6:8]],
                         [bytes((3, 2)), bytes((6, 8)), bytes((6, 11))])       # Crobat, Forretress, Masquerain
        text = (PRET / 'src/item.c').read_text() if (PRET / 'src/item.c').is_file() else None
        if text is None:
            self.skipTest('pret reference item table not available')
        block = text[text.index('sTMHMMoves[] = {'):]
        block = block[:block.index('};')]
        constants = dict((m[1], int(m[2])) for m in re.finditer(r'#define MOVE_([A-Z0-9_]+)\s+(\d+)',
                         (PRET / 'include/constants/moves.h').read_text()))
        machines = [constants[n] for n in re.findall(r'MOVE_([A-Z0-9_]+),', block)]
        self.assertEqual(len(machines), 100)

        def learns(species, move, level):
            words = struct.unpack('<%dH' % (len(wotbl[species]) // 2), wotbl[species])
            for word in words:
                if word == 0xFFFF:
                    break
                if word & 511 == move and word >> 9 <= level:
                    return True
            bits = int.from_bytes(personal[species][0x1C:0x2C], 'little')
            return move in machines and (bits >> machines.index(move)) & 1 == 1

        for trainer in (712, 713):
            for label in ('A', 'B'):
                base = expected_team(trainer, 'A') if False else [dict(species=s, moves=m) for s, _l, _o, _i, m, _c in BASE[trainer]]
                for index, member in enumerate(expected_team(trainer, label)):
                    for move in member['moves']:
                        if member['species'] == base[index]['species'] and move in base[index]['moves']:
                            continue
                        self.assertTrue(learns(member['species'], move, member['level']),
                                        f'{trainer}{label} slot {index} species {member["species"]} move {move}')

    def test_semantic_guards_refuse_changed_archives(self):
        data = self.need('EN')
        spec = rematches.load_spec()
        base = rematches.Resources(data)
        rematches.verify_semantics(spec, base)                      # control: untouched resources pass
        cases = []
        broken = rematches.Resources(data)
        broken.moves[263] = broken.moves[263][:3] + bytes([71]) + broken.moves[263][4:]   # Facade power changes
        cases.append(('move meaning', broken))
        broken = rematches.Resources(data)
        broken.moves[94] = struct.pack('<H', 99) + broken.moves[94][2:]                   # Psychic effect id reused
        cases.append(('effect reuse', broken))
        broken = rematches.Resources(data)
        record = bytearray(broken.personal[279]); record[0x1C + 12 // 8] &= ~(1 << (12 % 8))   # Pelipper loses TM13 (index 12)
        broken.personal[279] = bytes(record)
        cases.append(('TM compatibility', broken))
        broken = rematches.Resources(data)
        broken.personal[169] = broken.personal[169][:6] + bytes((0, 2)) + broken.personal[169][8:]   # Crobat type
        cases.append(('species type', broken))
        broken = rematches.Resources(data)
        broken.wotbl[205] = struct.pack('<H', (1 << 9) | 33) + b'\xff\xff'                # Forretress loses its moves
        cases.append(('learnset', broken))
        broken = rematches.Resources(data)
        broken.digests['a/0/5/6'] = '0' * 64
        cases.append(('archive preimage', broken))
        broken = rematches.Resources(data)
        broken.items = broken.items[:515]
        cases.append(('item archive', broken))
        broken = rematches.Resources(data)
        broken.items[273] = bytes([broken.items[273][0] ^ 1]) + broken.items[273][1:]      # Flame Orb record
        cases.append(('item record', broken))
        for name, resources in cases:
            with self.subTest(name=name), self.assertRaises(ValueError):
                rematches.verify_semantics(spec, resources)


    def test_order_independent_after_modern_moves_and_changed_read_member_refused(self):
        from sgp131 import modern_moves                              # read-only import of the 4a module
        used = {int(m) for m in rematches.load_spec()['moves']}
        self.assertNotIn(rematches.REWRITTEN_MOVE_MEMBER, used)
        for language in ('EN', 'IT'):
            data = self.need(language)
            changed, _receipt = modern_moves.apply(data, language)    # rewrites member 261 of a/0/1/1 only
            self.assertNotEqual(hashlib.sha256(fx.archives(language).rom.getFileByName('a/0/1/1')).hexdigest(),
                                hashlib.sha256(__import__('ndspy.rom').rom.NintendoDSRom(changed).getFileByName('a/0/1/1')).hexdigest())
            self.assertEqual(rematches.configuration(changed), rematches.configuration(data))
            out, receipt = fx.install(changed, language, tempfile.mkdtemp(prefix='rematch-order-'))
            fx.verify(changed, out, receipt)
            _, plain = fx.install(data, language, tempfile.mkdtemp(prefix='rematch-order-'))
            self.assertEqual(receipt['config_sha256'], plain['config_sha256'])
            self.assertEqual(receipt['code_sha256'], plain['code_sha256'])
            self.assertEqual({k: v['sha256'] for k, v in receipt['trainers']['712'].items()},
                             {k: v['sha256'] for k, v in plain['trainers']['712'].items()})
        # a change in a member this module reads is still refused; the rewritten member is not read at all
        spec = rematches.load_spec()
        data = self.need('EN')
        for member, byte, accepted in ((263, 6, False), (94, 6, False), (263, 11, False), (94, 10, False), (261, 6, True)):
            resources = rematches.Resources(data)
            record = bytearray(resources.moves[member]); record[byte] ^= 1                 # PP / flags / priority byte
            resources.moves[member] = bytes(record)
            with self.subTest(member=member, byte=byte):
                if accepted:
                    rematches.verify_semantics(spec, resources)
                else:
                    with self.assertRaisesRegex(ValueError, 'audited record|no longer means'):
                        rematches.verify_semantics(spec, resources)
        # declaring the rewritten member in the specification is itself refused
        declared = copy.deepcopy(spec)
        declared['moves']['261'] = dict(declared['moves']['263'])
        with self.assertRaisesRegex(ValueError, 'rewritten by another'):
            rematches.verify_semantics(declared, rematches.Resources(data))


# ===================================================================== part 2

def mutate(data, language, address, payload):
    """Copy of a ROM with bytes replaced at an ARM9 RAM address."""
    image = rematches._Image(data)
    offset = image.off(address, len(payload))
    changed = bytearray(data)
    changed[offset:offset + len(payload)] = payload
    return bytes(changed)


class InstallerGuards(RomCase):
    def setUp(self):
        self.work = tempfile.mkdtemp(prefix='rematch-test-')

    def install(self, data, **kwargs):
        return fx.install(data, 'EN', self.work, **kwargs)

    def test_wrong_seam_or_constructor_hash_refused(self):
        data = self.need('EN')
        from sgp12.rom import bl_thumb
        cases = [('seam retargeted', 0x0207363A, bl_thumb(0x0207363A, 0x020735EC), 'seam preimage'),
                 ('seam not a BL', 0x0207363A, b'\x00\xbf\x00\xbf', 'seam preimage'),
                 ('constructor byte', 0x02073A40, b'\x00', 'constructor preimage'),
                 ('constructor first byte', 0x02073604, b'\x00', 'constructor preimage'),
                 ('legacy level hook', 0x02073718, bl_thumb(0x02073718, 0x020735E8), 'constructor preimage'),
                 ('native reader', 0x020735F0, b'\x39', 'native reader preimage')]
        for name, address, payload, message in cases:
            with self.subTest(name=name):
                with self.assertRaisesRegex(ValueError, message):
                    self.install(mutate(data, 'EN', address, payload))
        with self.assertRaisesRegex(ValueError, 'game code'):
            changed = bytearray(data); changed[0xC:0x10] = b'IPKJ'
            self.install(bytes(changed))

    def test_the_stub_slot_must_be_supplied_aligned_and_inside_the_reserve(self):
        data = self.need('EN')
        with self.assertRaisesRegex(ValueError, 'no reserve allocation'):
            rematches.install(data, 'EN', self.work)
        with self.assertRaises(TypeError):
            rematches.install(data, 'EN', self.work, base=fx.STUB_START)             # the free-form base is gone
        for offset in (-4, 2, 3, 1.5, 64 * 3, 130):
            with self.subTest(stub_offset=offset), self.assertRaises(ValueError):
                self.install(data, stub_offset=offset)
        self.install(data, stub_offset=128)                                            # the last 64-byte position fits 192
        for start in (0x023D59E2, 0, 0x023DFFC0, 0x02300000):
            with self.subTest(start=hex(start)), self.assertRaises(ValueError):
                fx.install(data, 'EN', self.work, allocation=fx.declared_allocation('EN', start=start))
        with self.assertRaisesRegex(ValueError, 'language'):
            fx.install(data, 'FR', self.work, allocation=fx.declared_allocation('EN'))

    def test_occupied_stub_region_and_overflows_refused(self):
        data = self.need('EN')
        for offset in (0, 31, 63):
            with self.subTest(offset=offset), self.assertRaisesRegex(ValueError, 'occupied'):
                self.install(mutate(data, 'EN', fx.STUB_START + offset, b'\x01'))
        # the second stub position of the shared slot is independent of the first
        self.install(mutate(data, 'EN', fx.STUB_START + 64, b'\x01'))
        with self.assertRaisesRegex(ValueError, 'code overflow'):
            self.install(data, code_size=1024)
        with self.assertRaisesRegex(ValueError, 'config overflow'):
            self.install(data, config_size=512)
        with self.assertRaisesRegex(ValueError, 'window'):
            self.install(data, code_size=0x4000)                                        # image past the end of the window
        out, receipt = self.install(data, code_size=receipt_code_size(data, self.work), config_size=716)
        self.assertEqual((receipt['code_bytes'], receipt['config_bytes']), (receipt['code_allocated'], 716))

    def test_the_overlay_placeholder_and_the_loader_are_pinned(self):
        data = self.need('EN')
        image = rematches._Image(data)
        fat, _fs, y9, _ys = rematches._tables(data)
        file_start = struct.unpack_from('<I', data, fat + 8 * 126)[0]
        cases = {'placeholder row': (y9 + 32 * 126 + 8, 'placeholder row'), 'placeholder file': (file_start + 3, 'placeholder file')}
        for name, (offset, message) in cases.items():
            changed = bytearray(data)
            changed[offset] ^= 1
            with self.subTest(name), self.assertRaisesRegex(ValueError, message):
                self.install(bytes(changed))
        for name, address in (('HandleLoadOverlay', 0x02006FF8 + 0x40), ('UnloadOverlayByID', 0x02006F7C + 8)):
            with self.subTest(name), self.assertRaisesRegex(ValueError, name):
                self.install(mutate(data, 'EN', address, bytes([image.leggi(address, 1)[0] ^ 1])))

    def test_a_window_over_a_live_overlay_is_refused(self):
        data = self.need('EN')
        window = int(rematches.load_abi()['overlay']['window'], 16)
        self.assertEqual(rematches.window_conflicts(data, window, sum(fx.SIZES), 126), [12])
        self.assertTrue(rematches.window_conflicts(data, 0x02250000, 0x1000, 126), 'a window in the field overlay area is busy')

    def test_activation_requires_a_complete_runtime_context_proof(self):
        data = self.need('EN')
        good = fx.synthetic_proof('EN')
        with self.assertRaisesRegex(ValueError, 'proof'):
            self.install(data, activate=True)
        partial = copy.deepcopy(good); partial['observations'] = partial['observations'][:2]
        outside = copy.deepcopy(good); outside['observations'][0]['battle_type'] = 2
        wrong_language = dict(good, language='IT')
        for name, proof in (('partial', partial), ('outside', outside), ('language', wrong_language), ('empty', {})):
            with self.subTest(name=name), self.assertRaises(ValueError) as caught:
                self.install(data, activate=True, context_proof=proof, allow_synthetic=True)
            self.assertNotIn('cannot activate the wrapper', str(caught.exception))     # refused for structure, not origin
        # the harness stand-in is refused unless the test says so, and then the receipt says "synthetic"
        with self.assertRaisesRegex(ValueError, 'synthetic'):
            self.install(data, activate=True, context_proof=good)
        out, receipt = self.install(data, activate=True, context_proof=good, allow_synthetic=True)
        self.assertEqual((receipt['active'], receipt['function_state']), (1, 'active'))
        self.assertEqual(receipt['context']['proof_origin'], 'synthetic')
        self.assertEqual(receipt['context']['proof_sha256'], rematches.proof_digest(good))
        self.assertIsNone(receipt['capture_rom_sha256'], 'a synthetic stand-in has no capture')
        # a capture-shaped proof (unit-test fixture, not real evidence) reaches 'android' only with its identity fields
        # and only when its capture_rom_sha256 is the declared candidate (C3)
        capture = {k: v for k, v in good.items() if k != 'synthetic_harness_only'}
        capture.update(capture_file='unit-test-fixture-not-an-android-capture', build_id='unit-test',
                       capture_rom_sha256=fx.CANDIDATE)
        out, receipt = self.install(data, activate=True, context_proof=capture)
        self.assertEqual(receipt['context']['proof_origin'], 'android')
        self.assertEqual(receipt['context']['proof_sha256'], rematches.proof_digest(capture))
        self.assertEqual((receipt['candidate_sha256'], receipt['capture_rom_sha256']), (fx.CANDIDATE, fx.CANDIDATE))
        for missing in ('capture_file', 'build_id', 'capture_rom_sha256'):
            with self.subTest(missing=missing), self.assertRaisesRegex(ValueError, 'identity field'):
                self.install(data, activate=True, context_proof={k: v for k, v in capture.items() if k != missing})
        with self.assertRaisesRegex(ValueError, 'sha256'):
            self.install(data, activate=True, context_proof=dict(capture, capture_rom_sha256='XYZ'))
        other = hashlib.sha256(b'a different ROM').hexdigest()
        with self.assertRaisesRegex(ValueError, 'another ROM'):
            self.install(data, activate=True, context_proof=dict(capture, capture_rom_sha256=other))
        with self.assertRaisesRegex(ValueError, 'another ROM'):
            self.install(data, activate=True, context_proof=capture, candidate_sha256=other)
        for bad in ('ABC', 'a' * 63, 'A' * 64):
            with self.subTest(candidate=bad), self.assertRaises(ValueError):
                self.install(data, activate=True, context_proof=capture, candidate_sha256=bad)
        with self.assertRaisesRegex(ValueError, 'candidate_sha256'):
            self.install_without_candidate(data, capture)
        for bad in ('ABC', 'a' * 63, 'A' * 64, 7):
            with self.subTest(inert_candidate=bad), self.assertRaisesRegex(ValueError, 'candidate_sha256 must be'):
                self.install(data, candidate_sha256=bad)
        out_inert, inert = self.install(data)
        self.assertEqual((inert['active'], inert['function_state'], inert['context']['proof_origin']), (0, 'inert', None))
        self.assertEqual((inert['candidate_sha256'], inert['capture_rom_sha256'], inert['candidate_relation']), (None, None, None))

    def install_without_candidate(self, data, proof):
        with fx.declared_reserve():
            return rematches.install(data, 'EN', self.work, allocation=fx.declared_allocation('EN'), activate=True,
                                     context_proof=proof)

    def test_a_candidate_that_is_the_stage_inert_output_is_recognised_from_the_bytes(self):
        data = self.need('EN')
        inert, _r = self.install(data)
        stage_candidate = hashlib.sha256(inert).hexdigest()
        capture = dict({k: v for k, v in fx.synthetic_proof('EN').items() if k != 'synthetic_harness_only'},
                       capture_file='unit-test-fixture', build_id='unit-test', capture_rom_sha256=stage_candidate)
        out, receipt = self.install(data, activate=True, context_proof=capture, candidate_sha256=stage_candidate)
        self.assertEqual(receipt['candidate_relation'], 'stage-inert-output')
        self.assertEqual(fx.verify(data, out, receipt)['candidate_relation'], 'stage-inert-output')
        with self.assertRaisesRegex(ValueError, 'candidate relation'):
            fx.verify(data, out, dict(receipt, candidate_relation='composed-candidate'))
        out2, receipt2 = self.install(data, activate=True, context_proof=dict(capture, capture_rom_sha256=fx.CANDIDATE))
        self.assertEqual(receipt2['candidate_relation'], 'composed-candidate')

    def test_function_state_is_explicit_and_recomputed_from_the_installed_byte(self):
        data = self.need('EN')
        capture = dict({k: v for k, v in fx.synthetic_proof('EN').items() if k != 'synthetic_harness_only'},
                       capture_file='unit-test-fixture', build_id='unit-test', capture_rom_sha256=fx.CANDIDATE)
        for activate in (False, True):
            out, receipt = self.install(data, activate=activate, context_proof=capture if activate else None)
            self.assertEqual(receipt['function_state'], 'active' if activate else 'inert')
            self.assertEqual(fx.verify(data, out, receipt)['function_state'], receipt['function_state'])
            for forged in (dict(receipt, function_state='inert' if activate else 'active'), dict(receipt, function_state=None),
                           {k: v for k, v in receipt.items() if k != 'function_state'}):
                with self.assertRaisesRegex(ValueError, 'function_state|activation byte'):
                    fx.verify(data, out, forged)
            flipped = bytearray(out)
            flipped[rematches._active_at(out, receipt['overlay'])] = 0 if activate else 1
            flipped = bytes(flipped)
            forged = dict(receipt, output_sha256=hashlib.sha256(flipped).hexdigest())
            with self.assertRaises(ValueError):
                fx.verify(data, flipped, forged)      # the byte says one thing, the receipt another (and config_sha differs)

    def test_receipts_carry_no_process_state(self):
        data = self.need('EN')
        for activate in (False, True):
            _out, receipt = self.install(data, activate=activate, context_proof=fx.synthetic_proof('EN') if activate else None,
                                         allow_synthetic=True)
            blob = json.dumps(receipt, sort_keys=True)
            for word in ('UNPROVEN', 'SOURCE_READY', 'ANDROID', 'not run', '"status"'):
                self.assertNotIn(word, blob, word)

    def test_base_comes_only_from_a_reserve_receipt(self):
        data = self.need('EN')
        good = fx.declared_allocation('EN')
        cases = {'free-form dict': {'start': fx.STUB_START, 'bytes': 192, 'name': rematches.SLOT_NAME},
                 'integer': fx.STUB_START, 'other language': fx.declared_allocation('IT'),
                 'moved': fx.declared_allocation('EN', assignments=[dict(good['assignments'][0], start=fx.STUB_START + 4)]),
                 'too small for the stub': fx.declared_allocation('EN', request=32),
                 'real digest, test slot': dict(good, policy_sha256=fx.REAL_RESERVE_POLICY()[1])}
        for name, allocation in cases.items():
            with self.subTest(name), self.assertRaises(ValueError):
                with fx.declared_reserve():
                    rematches.install(data, 'EN', self.work, allocation=allocation)

    def test_the_real_policy_cannot_grant_the_stub_slot_today(self):
        """No test double: the product map has `c8.module-stubs` (192 B at 0x023D59E0) but under the conditional owner
        field-guide.code, so `reserve.allocate` refuses it, and a genuine receipt for another owner does not help.
        Fail-closed until Codex lifts the condition (INTEGRATION.md)."""
        from sgp131 import reserve
        data = self.need('EN')
        with fx.real_reserve():
            with self.assertRaisesRegex(ValueError, 'conditional'):
                reserve.allocate(data, {rematches.SLOT_NAME: 64})
            genuine = reserve.allocate(data, {'training.ui': 1536})
            self.assertEqual(rematches.check_allocation(genuine, 'EN', 'training.ui')['start'], 0x023D6800)
            for allocation in (genuine, fx.declared_allocation('EN')):
                with self.subTest(requested=sorted(allocation['requested'])), self.assertRaises(ValueError):
                    rematches.install(data, 'EN', self.work, allocation=allocation)

    def test_verify_accepts_the_installed_image_and_refuses_every_tamper(self):
        data = self.need('EN')
        out, receipt = self.install(data)
        proof = fx.verify(data, out, receipt)
        self.assertEqual((proof['config_bytes'], proof['active'], proof['stub_bytes']), (716, 0, receipt['stub']['bytes']))
        self.assertLessEqual(receipt['stub']['bytes'], 64)
        self.assertEqual(proof['appended_bytes'], len(out) - len(data))
        image = rematches._Image(out)
        fat, _fs, y9, _ys = rematches._tables(data)
        file_start = receipt['overlay']['file_offset']
        def tamper(offset, value=1, blob=out):
            changed = bytearray(blob); changed[offset] ^= value
            return bytes(changed)
        cases = [('config party byte', tamper(file_start + receipt['overlay']['config_offset'] + 250)),
                 ('config header', tamper(file_start + receipt['overlay']['config_offset'] + 7)),
                 ('module code byte', tamper(file_start + 8)), ('module code tail', tamper(file_start + receipt['code_allocated'] - 1)),
                 ('stub byte', tamper(image.off(fx.STUB_START + 8, 1))), ('stub tail padding', tamper(image.off(fx.STUB_START + 63, 1))),
                 ('seam', tamper(image.off(0x0207363A, 4))), ('outside ARM9 byte', tamper(image.off(0x02000100, 1))),
                 ('neighbouring stub slot', tamper(image.off(fx.STUB_START + 64, 1))),
                 ('overlay row size', tamper(y9 + 32 * 126 + 8)), ('overlay row window', tamper(y9 + 32 * 126 + 4, 0x10)),
                 ('overlay row flags', tamper(y9 + 32 * 126 + 28, 0x01)), ('other overlay row', tamper(y9 + 32 * 125 + 8)),
                 ('FAT entry of the module', tamper(fat + 8 * 126)), ('FAT entry of another file', tamper(fat + 8 * 125)),
                 ('header used size', tamper(0x80)), ('header CRC', tamper(0x15E)), ('header title', tamper(0x4)),
                 ('appended padding', out[:len(data)] + b'\x01' + out[len(data) + 1:] if (len(data) % 4) else tamper(len(out) - 1))]
        for name, changed in cases:
            with self.subTest(name=name), self.assertRaises(ValueError):
                fx.verify(data, changed, dict(receipt, output_sha256=hashlib.sha256(changed).hexdigest()))
        longer = out + b'\x00'
        with self.subTest('extra byte at the end'), self.assertRaises(ValueError):
            fx.verify(data, longer, dict(receipt, output_sha256=hashlib.sha256(longer).hexdigest()))
        with self.assertRaises(ValueError):
            fx.verify(data, out, dict(receipt, input_sha256='0' * 64))
        with self.assertRaises(ValueError):
            fx.verify(data, out, dict(receipt, config_sha256='0' * 64))
        with self.assertRaises(ValueError):
            fx.verify(data, data, receipt)                    # not installed
        with self.assertRaises(ValueError):
            fx.verify(out, out, receipt)                      # stub region no longer empty before


class EntryFamiliesOnRealCode(RomCase):
    """B1: the battle types are measured on the real ARM code and scripts, not taken from the reference source."""

    SETUP = 0x02051370        # SetupAndStartTrainerBattle in the V4 ARM9 (EN = IT)
    NEW_BATTLE_SETUP = 0x020518D8

    def battle_type_built(self, data, opponent1, opponent2, follower, a4):
        from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB, UC_HOOK_CODE
        from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3, UC_ARM_REG_SP, UC_ARM_REG_LR
        image = rematches._Image(data)
        uc = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
        uc.mem_map(0x01FF8000, 0x8000)
        uc.mem_map(0x02000000, 0x400000)
        uc.mem_map(0x027E0000, 0x20000)
        for ram, off, size in image.segmenti:
            if ram < 0x02400000 or ram in (0x01FF8000, 0x027E0000):
                uc.mem_write(ram, bytes(image.raw[off:off + size]))
        seen = []
        def hook(emu, address, size, _):
            seen.append(emu.reg_read(UC_ARM_REG_R1))
            emu.emu_stop()
        uc.hook_add(UC_HOOK_CODE, hook, begin=self.NEW_BATTLE_SETUP, end=self.NEW_BATTLE_SETUP)
        sp = 0x023F0000
        uc.mem_write(sp, struct.pack('<4I', a4, 0, 0x0B, 0))           # stack arguments a4, a5, heap id, win flag
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, 0x023F8001)
        uc.reg_write(UC_ARM_REG_R0, 0x02300000)                        # a zeroed TaskManager
        uc.reg_write(UC_ARM_REG_R1, opponent1)
        uc.reg_write(UC_ARM_REG_R2, opponent2)
        uc.reg_write(UC_ARM_REG_R3, follower)
        uc.emu_start(self.SETUP | 1, 0x023F8000, count=2000)
        self.assertEqual(len(seen), 1, 'BattleSetup_New was reached exactly once')
        return seen[0]

    def test_the_real_setup_function_builds_0x1_and_0x801_for_a_single_trainer(self):
        for language in ('EN', 'IT'):
            data = self.need(language)
            with self.subTest(language=language):
                self.assertEqual(self.battle_type_built(data, 712, 0, 0, a4=0), 0x1)
                self.assertEqual(self.battle_type_built(data, 712, 0, 0, a4=1), 0x801)
                self.assertEqual(self.battle_type_built(data, 713, 0, 0, a4=0x77), 0x801, 'any non-zero a4')
                # the multi-trainer forms are other values, never whitelisted
                self.assertEqual(self.battle_type_built(data, 712, 713, 0, a4=0), 0x13)
                self.assertEqual(self.battle_type_built(data, 712, 713, 1, a4=1), 0x4B)
                self.assertEqual(self.battle_type_built(data, 712, 712, 0, a4=1), 0x3)

    def test_the_scripts_reach_it_with_a4_zero_for_the_phone_and_one_for_the_sequence(self):
        for language in ('EN', 'IT'):
            self.need(language)
            member = bytes(ndspy.narc.NARC(ndspy.rom.NintendoDSRom(fx.rom(language)).getFileByName('a/0/1/2')).files[832])
            found = {}
            for offset in range(len(member) - 8):
                op, tid, var1, var2, var3 = struct.unpack_from('<HHHBB', member, offset)
                if op == 213 and tid in (712, 713):
                    found[offset] = (tid, var1, var2)
            with self.subTest(language=language):
                self.assertEqual(found, {0x41F: (713, 0, 0), 0x4D9: (712, 0, 0), 0x706: (712, 0, 1), 0x738: (713, 0, 1)})

    def test_the_installed_whitelist_is_exactly_the_two_values(self):
        data = self.need('EN')
        work = tempfile.mkdtemp(prefix='rematch-b1-')
        out, receipt = fx.install(data, 'EN', work)
        start = receipt['overlay']['file_offset'] + receipt['overlay']['config_offset']
        magic, size, active, count, kinds, mask, reserved, t0, t1 = struct.unpack('<IHBBBBH2I', out[start:start + 20])
        self.assertEqual(([t0, t1][:kinds], mask), ([0x1, 0x801], 1 << 1))
        self.assertEqual(receipt['context']['battle_types'], [0x1, 0x801])
        self.assertEqual(receipt['context']['families'], {'phone': 0x1, 'dojo-sequence': 0x801})

    def test_a_changed_setup_function_is_refused(self):
        data = self.need('EN')
        work = tempfile.mkdtemp(prefix='rematch-b1-')
        for offset in (0, 0x30, 0x34, 0x38, 0xB7):
            with self.subTest(offset=offset), self.assertRaisesRegex(ValueError, 'setup function'):
                fx.install(mutate(data, 'EN', self.SETUP + offset, bytes([rematches._Image(data).leggi(self.SETUP + offset, 1)[0] ^ 1])), 'EN', work)
        out, receipt = fx.install(data, 'EN', work)
        changed = mutate(out, 'EN', self.SETUP + 0x30, bytes([rematches._Image(out).leggi(self.SETUP + 0x30, 1)[0] ^ 1]))
        with self.assertRaises(ValueError):
            fx.verify(data, changed, dict(receipt, output_sha256=hashlib.sha256(changed).hexdigest()))


class OverlayModule(RomCase):
    """The module is overlay 126: loaded, run and unloaded inside one seam call by a resident stub, with the REAL
    HandleLoadOverlay / CanOverlayBeLoaded / UnloadOverlayByID bytes (only the file system layer is replaced)."""

    def runs(self, language, mode='active', trainer=712, **kwargs):
        native = fx.native_bench(language)
        patched, receipt = fx.installed(language, mode)
        seed = fx.seed_for(trainer, 1)
        return native.run(trainer, plus=1, seed=seed), patched.run(trainer, plus=1, seed=seed, **kwargs), receipt

    @staticmethod
    def free(run):
        return not any(active for _oid, active in run['overlay']['registry'])

    def test_the_stub_is_small_position_independent_and_never_writes_the_hosts_registers(self):
        from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB
        for language in ('EN', 'IT'):
            self.need(language)
            _patched, receipt = fx.installed(language, 'active')
            with tempfile.TemporaryDirectory() as work:
                stub, _symbols = rematches.compile_stub(work, fx.STUB_START, receipt['stub']['entry'])
                again, _ = rematches.compile_stub(work, fx.STUB_START + 128, receipt['stub']['entry'])
            self.assertLessEqual(len(stub), 64)
            self.assertEqual(stub, again, 'no relocation inside the stub')
            md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
            md.detail = True
            written = set()
            for insn in md.disasm(stub[:-16], fx.STUB_START):          # the last 16 bytes are the literal pool
                read, write = insn.regs_access()
                written |= {insn.reg_name(r) for r in write}
            self.assertEqual(written - {'r0', 'r1', 'r2', 'r3', 'sp', 'pc', 'lr', 'cpsr'}, set(),
                             'r4-r7 belong to the host (r4 is BattleSetup for the module)')

    def test_success_refusal_failure_and_inert_all_leave_the_registry_free(self):
        for language in ('EN', 'IT'):
            self.need(language)
            skip = fx.skip_ranges()
            cases = {'success': ('active', {}), 'inert module': ('inert', {}), 'load fails': ('active', dict(load_ok=False)),
                     'window busy (battle live)': ('active', dict(busy=(12,)))}
            for name, (mode, kwargs) in cases.items():
                with self.subTest(language=language, case=name):
                    before, after, receipt = self.runs(language, mode, **kwargs)
                    if name == 'success':
                        self.assertNotEqual([m['moves'] for m in after['decoded']], [m['moves'] for m in before['decoded']])
                    else:
                        self.assertEqual(bench.compare_runs(after, before, skip), [], 'native behaviour, no variant')
                    info = after['overlay']
                    # a failed image load makes the loader itself call GF_AssertFail (a no-op without a debugger) before returning 0
                    self.assertEqual(info['assert'], 1 if name == 'load fails' else 0)
                    if name == 'window busy (battle live)':
                        self.assertEqual(info['image'], [], 'the loader refused before reading the file')
                        self.assertEqual([entry for entry in info['registry'] if entry[1]], [(12, 1)], 'the live overlay is intact')
                        self.assertNotIn((126, 1), info['registry'])
                    else:
                        self.assertTrue(self.free(after), 'no entry left active: the battle overlay can load afterwards')
                        self.assertEqual(info['image'], [(126, name != 'load fails')])
                    if name in ('success', 'inert module'):
                        self.assertEqual(info['unload'], [126], 'unloaded in the same call')
                        window, size = info['window']
                        base = window - 0x02000000
                        self.assertEqual(after['ram'][base:base + size], bytes([bench.POISON]) * size,
                                         'the window was released: nothing may use it afterwards')

    def test_every_trainer_pays_one_balanced_load_and_unload(self):
        """The seam is on the path of EVERY trainer party: each construction loads and unloads once (cost to measure on a device)."""
        for language in ('EN', 'IT'):
            self.need(language)
            patched, receipt = fx.installed(language, 'active')
            headers = fx.archives(language).files('a/0/5/5')
            others = [t for t, h in enumerate(headers) if len(h) >= 4 and h[3] and t not in (712, 713)][:4]
            for trainer in others + [712, 713]:
                with self.subTest(language=language, trainer=trainer):
                    run = patched.run(trainer, plus=1, seed=fx.seed_for(trainer, 0))
                    self.assertEqual((len(run['overlay']['image']), run['overlay']['unload']), (1, [126]))
                    self.assertTrue(self.free(run))

    def test_stack_use_of_the_load_path_is_bounded(self):
        for language in ('EN', 'IT'):
            self.need(language)
            native = fx.native_bench(language)
            patched, receipt = fx.installed(language, 'active')
            seed = fx.seed_for(712, 1)
            before, after = native.run(712, plus=1, seed=seed), patched.run(712, plus=1, seed=seed)
            host_sp = after['resume']['sp']
            native_depth = host_sp - before['seam_low'] if before['seam_low'] else 0     # the native reader is a stubbed thunk
            patched_depth = host_sp - after['seam_low']
            self.assertGreater(patched_depth, native_depth)
            # stub (16) + HandleLoadOverlay chain + module (200 measured before) + the reader: measured, not guessed
            self.assertLessEqual(patched_depth, 512, 'stack below the host SP across the seam call (stub + loader + module)')

    def test_the_module_file_is_the_overlay_the_loader_reads(self):
        for language in ('EN', 'IT'):
            data = self.need(language)
            patched, receipt = fx.installed(language, 'active')
            window, image = patched.module_image()
            self.assertEqual((window, hashlib.sha256(image).hexdigest()), (receipt['overlay']['window'], receipt['overlay']['image_sha256']))
            self.assertEqual(len(image), receipt['overlay']['image_bytes'])
            self.assertEqual(rematches.window_conflicts(patched.rom, window, len(image), 126), [12])


class PostReview(RomCase):
    """Corrections after K-review: I3 candidate gate, I4 verify strength, M1 forged fields, M5 compiler pin."""

    def setUp(self):
        self.work = tempfile.mkdtemp(prefix='rematch-post-')

    def capture(self, candidate=None):
        proof = {k: v for k, v in fx.synthetic_proof('EN').items() if k != 'synthetic_harness_only'}
        return dict(proof, capture_file='unit-test-fixture-not-an-android-capture', build_id='unit-test',
                    capture_rom_sha256=candidate or fx.CANDIDATE)

    def active(self, data, candidate=None):
        return fx.install(data, 'EN', self.work, activate=True, context_proof=self.capture(candidate),
                          candidate_sha256=candidate or fx.CANDIDATE)

    def test_the_final_candidate_gate_refuses_an_invented_candidate(self):
        data = self.need('EN')
        invented = 'ab' * 32
        out, receipt = self.active(data, invented)
        self.assertEqual(receipt['candidate_relation'], 'composed-candidate', 'the installer alone cannot tell')
        with self.assertRaisesRegex(ValueError, 'not the candidate'):
            rematches.candidate_gate(out, receipt)
        genuine = hashlib.sha256(rematches.inert_view(out, receipt)).hexdigest()
        out2, receipt2 = self.active(data, genuine)
        self.assertEqual(out2, out)
        rematches.candidate_gate(out2, receipt2)
        with self.assertRaisesRegex(ValueError, 'no candidate'):
            rematches.candidate_gate(out2, dict(receipt2, candidate_sha256=None))

    def test_inert_view_clears_only_the_active_byte_and_is_pure(self):
        data = self.need('EN')
        out, receipt = self.active(data)
        snapshot = bytes(out)
        view = rematches.inert_view(out, receipt)
        self.assertEqual(out, snapshot)
        at = rematches._active_at(out, receipt['overlay'])
        self.assertEqual([i for i, (a, b) in enumerate(zip(out, view)) if a != b], [at])
        self.assertEqual(rematches.inert_view(view, receipt), view, 'idempotent')
        inert, inert_receipt = self.install(data)
        self.assertEqual(rematches.inert_view(inert, inert_receipt), inert)
        self.assertEqual(hashlib.sha256(view).hexdigest(), hashlib.sha256(inert).hexdigest())

    def install(self, data, **kwargs):
        return fx.install(data, 'EN', self.work, **kwargs)

    def test_verify_refuses_a_synthetic_proof_by_default_like_portable_and_controls(self):
        data = self.need('EN')
        out, receipt = self.install(data, activate=True, context_proof=fx.synthetic_proof('EN'), allow_synthetic=True)
        self.assertEqual(receipt['context']['proof_origin'], 'synthetic')
        with self.assertRaisesRegex(ValueError, 'synthetic'):
            fx.verify(data, out, receipt)
        with self.assertRaisesRegex(ValueError, 'synthetic'):
            fx.verify(data, out, receipt, require_measured=True)
        self.assertEqual(fx.verify(data, out, receipt, require_measured=False)['function_state'], 'active')

    def test_verify_binds_an_active_receipt_to_its_candidate_and_origin(self):
        data = self.need('EN')
        out, receipt = self.active(data)
        self.assertEqual(fx.verify(data, out, receipt)['function_state'], 'active')
        other = hashlib.sha256(b'another candidate').hexdigest()
        context = receipt['context']
        cases = {
            'capture dropped (I4b)': dict(receipt, capture_rom_sha256=None),
            'capture differs from the candidate (X3)': dict(receipt, capture_rom_sha256=other),
            'candidate differs from the capture': dict(receipt, candidate_sha256=other),
            'candidate dropped': dict(receipt, candidate_sha256=None),
            'origin forced to synthetic (I4c)': dict(receipt, context=dict(context, proof_origin='synthetic')),
            'origin dropped': dict(receipt, context=dict(context, proof_origin=None)),
            'proof hash dropped': dict(receipt, context=dict(context, proof_sha256=None)),
            'proof hash malformed': dict(receipt, context=dict(context, proof_sha256='zz')),
        }
        for name, forged in cases.items():
            with self.subTest(name), self.assertRaises(ValueError):
                fx.verify(data, out, forged)
        # an inert receipt carries no proof at all
        inert_out, inert = self.install(data)
        for name, forged in {'origin on an inert receipt': dict(inert, context=dict(inert['context'], proof_origin='android')),
                             'capture on an inert receipt': dict(inert, capture_rom_sha256=fx.CANDIDATE),
                             'proof hash on an inert receipt': dict(inert, context=dict(inert['context'], proof_sha256='1' * 64))}.items():
            with self.subTest(name), self.assertRaises(ValueError):
                fx.verify(data, inert_out, forged)

    def test_the_compiler_is_pinned(self):
        from unittest import mock
        fake = Path(tempfile.mkdtemp(prefix='fake-clang-')) / 'clang'
        fake.write_text('#!/bin/sh\necho "Apple clang version 99.0.0 (fake)"\n')
        fake.chmod(0o755)
        with mock.patch.object(rematches.shutil, 'which', lambda name: str(fake)):
            with self.assertRaisesRegex(ValueError, 'compiler'):
                rematches.compile_native(self.work, 0x0226B000, 0x0226B000 + 1280, 768)
        fake.unlink()
        fake.parent.rmdir()
        # each pin on its own: a copy of the real compiler passes the binary pin, so patch the expected values
        for constant, message in (('COMPILER_VERSION', 'version drift'), ('COMPILER_SHA256', 'binary drift')):
            with mock.patch.object(rematches, constant, 'x' * 8):
                with self.assertRaisesRegex(ValueError, message):
                    rematches.compile_native(self.work, 0x0226B000, 0x0226B000 + 1280, 768)


_UI = {}


def ui_output(test, language):
    """The REAL sgp131.ui.install output for a V4 input (read-only use of the UI stage, in memory, ~5 s)."""
    if language not in _UI:
        from sgp131 import ui
        from sgp131.test_ui import CONFIG
        data = test.need(language)
        with tempfile.TemporaryDirectory(prefix='rematch-ui-') as work:
            (Path(work) / 'ui-candidate.json').write_text(json.dumps(CONFIG))
            _UI[language] = ui.install(data, language, ROOT / 'local/tools/pokeheartgold/charmap.txt', Path(work))[0]
    return _UI[language]


class RealUiComposition(RomCase):
    """The rematch pins (seam, constructor, reader, archives) and the stub slot survive the real UI stage."""

    def test_the_module_installs_after_the_real_ui_at_the_real_stub_slot(self):
        for language in ('EN', 'IT'):
            after_ui = ui_output(self, language)
            work = tempfile.mkdtemp(prefix='rematch-ui-test-')
            with self.subTest(language=language):
                # the stub slot of the reserve map is zero in the UI output too, and the module needs nothing else
                out, receipt = fx.install(after_ui, language, work)
                self.assertEqual(fx.verify(after_ui, out, receipt)['function_state'], 'inert')
                self.assertEqual(receipt['input_sha256'], hashlib.sha256(after_ui).hexdigest())
                self.assertEqual(receipt['stub']['address'], fx.STUB_START)
                self.assertGreater(len(out), len(after_ui), 'the module file is appended: the cartridge grows (INTEGRATION.md, UI seeds)')
                # the UI seeds record the cartridge length and the y9 CRC: this stage changes both, as every appending stage does
                self.assertNotEqual(out[rematches._tables(out)[2]:rematches._tables(out)[2] + 4128],
                                    after_ui[rematches._tables(after_ui)[2]:rematches._tables(after_ui)[2] + 4128])


def receipt_code_size(data, work):
    _, receipt = fx.install(data, 'EN', work)
    return receipt['code_bytes']


def gender_byte(ratio, pid_low):
    if ratio == 255:
        return 2
    if ratio == 254:
        return 1
    return 0 if ratio == 0 or pid_low >= ratio else 1


class RealConstructor(RomCase):
    """Unicorn over the real ARM9 bytes. Stubs (documented in constructor_bench): heap allocator, archive
    reader, species-name loader, NARC handle functions; everything else, CreateMon included, is real code."""

    def runs(self, language, trainer, label, plus, stub_offset=0, sizes=fx.SIZES):
        native = fx.native_bench(language)
        patched, receipt = fx.installed(language, 'active', stub_offset, sizes)
        outcome = 'AB'.index(label)
        seed = fx.seed_for(trainer, outcome)
        expected = fx.variant_buffer(receipt, trainer, label) if plus else fx.archives(language).files('a/0/5/6')[trainer]
        before = native.run(trainer, plus=plus, seed=seed, buffer=bytes(expected))
        after = patched.run(trainer, plus=plus, seed=seed)
        return before, after, receipt, seed

    def test_every_constructed_member_matches_selected_team(self):
        for language in ('EN', 'IT'):
            self.need(language)
            archives = fx.archives(language)
            personal, moves = archives.files('a/0/0/2'), archives.files('a/0/1/1')
            skip = fx.skip_ranges()
            for trainer in (712, 713):
                header = archives.files('a/0/5/5')[trainer]
                for label in ('A', 'B'):
                    for plus in (0, 1):
                        with self.subTest(language=language, trainer=trainer, label=label, plus=plus):
                            before, after, receipt, seed = self.runs(language, trainer, label, plus)
                            self.assertEqual(bench.compare_runs(after, before, skip), [])
                            # Normal keeps the native party; Plus builds the selected authored team
                            team = expected_team(trainer, label) if plus else [
                                dict(species=s, level=l, override=o, item=i, moves=list(m), capsule=c)
                                for s, l, o, i, m, c in BASE[trainer]]
                            self.assertEqual(len(after['decoded']), 6)
                            # trainer class gender table (native: pointer at 0x02073600): female classes start at 0x78
                            table = struct.unpack('<I', fx.native_bench(language).segment_bytes(0x02073600, 4))[0]
                            gender_base = 0x78 if fx.native_bench(language).segment_bytes(table + header[1], 1)[0] == 1 else 0x88
                            for slot, (mon, member) in enumerate(zip(after['decoded'], team)):
                                self.assertTrue(mon['checksum_ok'])
                                self.assertEqual((mon['species'], mon['form'], mon['item'], mon['moves']),
                                                 (member['species'], 0, member['item'], member['moves']))
                                self.assertEqual(mon['ball_capsule'], 1 if member['capsule'] else 0)
                                self.assertEqual(mon['ivs'], [31] * 6)
                                self.assertEqual(mon['evs'], [0] * 6)
                                self.assertEqual(mon['pp'], [moves[m][6] for m in member['moves']])
                                self.assertEqual(mon['friendship'], 255)
                                if plus:
                                    self.assertGreaterEqual(mon['level'], member['level'])
                                else:
                                    self.assertEqual(mon['level'], member['level'])
                                # personality: seeded by difficulty + level + species + trainer id, rolled `class` times
                                if member['override'] and member['override'] >> 4 == 2:
                                    gender_base |= 1
                                value = (255 + member['level'] + member['species'] + trainer) & 0xFFFFFFFF
                                for _ in range(header[1]):
                                    value = (value * 0x41C64E6D + 0x6073) & 0xFFFFFFFF
                                self.assertEqual(mon['pid'], ((value >> 16) << 8) + gender_base,
                                                 f'slot {slot} personality')
                                record = personal[member['species']]
                                ability = record[0x17] if record[0x17] and mon['pid'] & 1 else record[0x16]
                                self.assertEqual(mon['ability'], ability)
                                self.assertEqual(mon['gender'], gender_byte(record[0x10], mon['pid'] & 0xFF))
                                self.assertEqual(mon['nature'], mon['pid'] % 25)
                            # the loader ran exactly once and the host seed is back where it started
                            self.assertEqual(len([e for e in after['events'] if e[0] == 'read' and e[1] == 56]), 1)
                            self.assertEqual(after['seed_after'], seed_value(after))
                            self.assertEqual(after['seed_after'], before['seed_after'])

    def test_first_species_change_reaches_the_personality_and_ability(self):
        # B replaces slot 0 species: PID/ability/gender must be those of the NEW species (early seam)
        for language in ('EN', 'IT'):
            self.need(language)
            for trainer, slot, new, old in ((712, 0, 169, 22), (713, 3, 205, 284)):
                _, after_b, _, _ = self.runs(language, trainer, 'B', 1)
                _, after_a, _, _ = self.runs(language, trainer, 'A', 1)
                self.assertEqual(after_b['decoded'][slot]['species'], new)
                self.assertEqual(after_a['decoded'][slot]['species'], old)
                self.assertNotEqual(after_b['decoded'][slot]['pid'], after_a['decoded'][slot]['pid'])
                self.assertEqual(after_b['decoded'][slot]['form'], 0)
                others = [m['species'] for i, m in enumerate(after_b['decoded']) if i != slot]
                self.assertEqual(others, [m['species'] for i, m in enumerate(after_a['decoded']) if i != slot])

    def test_loader_once_SP_registers_and_resume_equivalent(self):
        for language in ('EN', 'IT'):
            self.need(language)
            for trainer in (712, 713):
                for label in ('A', 'B'):
                    with self.subTest(language=language, trainer=trainer, label=label):
                        before, after, _, _ = self.runs(language, trainer, label, 1)
                        self.assertEqual([e for e in after['events'] if e[0] == 'read' and e[1] == 56],
                                         [e for e in before['events'] if e[0] == 'read' and e[1] == 56])
                        a, b = after['resume'], before['resume']
                        self.assertEqual((a['r'][0], a['r'][4:12], a['sp']), (b['r'][0], b['r'][4:12], b['sp']))
                        self.assertEqual(a['r'][0], bench.LOADER_RESULT)          # the loader's result is handed back
                        self.assertEqual(a['r'][8:12], [bench.SENTINEL_REGS[n] for n in range(8, 12)])
                        self.assertEqual(a['sp'] & 7, 0)
                        self.assertEqual(after['misalign'], [])
                        self.assertTrue(after['stack_canary'])
                        depth = a['sp'] - min(after['wrapper_sp'])
                        self.assertLessEqual(depth, 200, 'wrapper stack use above the measured bound')
                        self.assertTrue(all(sp % 4 == 0 for sp in after['wrapper_sp']))

    def test_allocation_and_free_sequence_unchanged(self):
        for language in ('EN', 'IT'):
            self.need(language)
            before, after, _, _ = self.runs(language, 712, 'B', 1)
            kinds = lambda run: [(e[0], e[1:]) for e in run['events'] if e[0] in ('alloc', 'free')]
            self.assertEqual(kinds(after), kinds(before))
            allocations = [e for e in after['events'] if e[0] == 'alloc']
            frees = {e[1] for e in after['events'] if e[0] == 'free'}
            self.assertEqual(allocations[0][2], 108)                       # the transient party buffer
            self.assertIn(allocations[0][3], frees)                        # ...is released exactly as natively
            self.assertIn(allocations[1][3], frees)                        # ...and so is the Pokemon workspace

    def test_relocated_install_behaves_identically(self):
        for language in ('EN', 'IT'):
            self.need(language)
            skip = fx.skip_ranges(fx.OFFSET_2, fx.SIZES_2)
            for trainer in (712, 713):
                for label in ('A', 'B'):
                    for plus in (0, 1):
                        with self.subTest(language=language, trainer=trainer, label=label, plus=plus):
                            before, after, receipt, _ = self.runs(language, trainer, label, plus, fx.OFFSET_2, fx.SIZES_2)
                            self.assertEqual(receipt['stub']['address'], fx.STUB_START + fx.OFFSET_2)
                            self.assertEqual(bench.compare_runs(after, before, skip), [])
            first = fx.installed(language, 'active')[1]
            second = fx.installed(language, 'active', fx.OFFSET_2, fx.SIZES_2)[1]
            self.assertNotEqual(first['stub']['address'], second['stub']['address'])    # the stub really moved
            self.assertEqual(first['stub']['sha256'], second['stub']['sha256'], 'position independent: same bytes anywhere')
            self.assertNotEqual(first['seam']['new_bytes'], second['seam']['new_bytes'])  # the seam BL follows it
            self.assertNotEqual(first['config_address'], second['config_address'])        # and so did the config inside the window


def seed_value(run):
    return run['seed_before']


if __name__ == '__main__':
    unittest.main()
