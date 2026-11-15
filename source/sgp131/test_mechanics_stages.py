"""Class A: mechanics-stage registry, pending markers and the post-UI composition rule.

No game file. Synthetic bytes exercise the generic confinement rule, the chain
reconstruction/ordering logic and the refusal of pending stages. The structural
UI invariants (y9, FAT 54/156, seeds, reserve) are Class B in
`test_mechanics_stages_rom.py` because they need a real UI image.
"""
import hashlib
import json
from pathlib import Path
import struct
import unittest
from unittest.mock import patch

from . import mechanics_stages as ms


def sha(data):
    return hashlib.sha256(data).hexdigest()


class FakeStage:
    """Registry entry shaped like ms.MechanicalStage, acting on a tiny buffer."""
    def __init__(self, name, start, end, value):
        self.name, self.span, self.value = name, (start, end), value
        self.receipt_stage = name

    def regions(self, rom):
        return [ms.Region(self.span[0], self.span[1], self.name + '.file')]

    def apply(self, data, language):
        out = bytearray(data)
        out[self.span[0]] = self.value
        return bytes(out), {'fake': self.name, 'offset': self.span[0], 'value': self.value}

    def verify(self, before, after, receipt):
        if after[receipt['offset']] != receipt['value'] or before[receipt['offset']] == after[receipt['offset']]:
            raise ValueError('fake stage readback')
        return {'ok': True}


def no_structure(prev, nxt, regions):
    return {'structure': 'synthetic'}


REGISTRY = {'one': FakeStage('one', 10, 20, 0xA1), 'two': FakeStage('two', 30, 40, 0xB2)}
BEFORE = bytes(100)


def chain(order, base=BEFORE):
    data, receipts = base, []
    for name in order:
        data, receipt = ms.run_stage(name, data, 'EN', invariants=no_structure, registry=REGISTRY)
        receipts.append(receipt)
    return data, receipts


class RangeRule(unittest.TestCase):
    def test_changed_ranges_merges_adjacent_and_splits_gaps(self):
        a = bytes(64)
        b = bytearray(a)
        for i in (3, 4, 5, 9, 63):
            b[i] = 1
        self.assertEqual(ms.changed_ranges(a, bytes(b)), [(3, 6), (9, 10), (63, 64)])
        self.assertEqual(ms.changed_ranges(a, a), [])

    def test_changed_ranges_crosses_chunk_boundaries(self):
        a = bytes(3 * 65536)
        b = bytearray(a)
        b[65535] = b[65536] = 7
        self.assertEqual(ms.changed_ranges(a, bytes(b)), [(65535, 65537)])

    def test_confined_accepts_edge_bytes_and_rejects_one_past_either_side(self):
        regions = [ms.Region(10, 20, 'r')]
        for index, ok in ((10, True), (19, True), (9, False), (20, False)):
            after = bytearray(BEFORE)
            after[index] = 1
            if ok:
                ms.check_confined(BEFORE, bytes(after), regions, 'stage')
            else:
                with self.subTest(index=index), self.assertRaisesRegex(ms.CompositionError, 'outside declared'):
                    ms.check_confined(BEFORE, bytes(after), regions, 'stage')

    def test_confined_rejects_any_length_change(self):
        for after in (BEFORE + b'\0', BEFORE[:-1]):
            with self.assertRaisesRegex(ms.CompositionError, 'length'):
                ms.check_confined(BEFORE, after, [ms.Region(0, 100, 'all')], 'stage')

    def test_overlapping_regions_are_refused(self):
        ms.require_disjoint([[ms.Region(0, 10, 'a')], [ms.Region(10, 20, 'b')]])
        with self.assertRaisesRegex(ms.CompositionError, 'overlap'):
            ms.require_disjoint([[ms.Region(0, 11, 'a')], [ms.Region(10, 20, 'b')]])
        with self.assertRaisesRegex(ms.CompositionError, 'empty|invalid'):
            ms.require_disjoint([[ms.Region(5, 5, 'a')]])


class Registry(unittest.TestCase):
    def test_lottery_id_is_a_confined_non_resident_stage(self):
        self.assertIn('lottery-id', ms.IMPLEMENTED)
        stage = ms.require_stage('lottery-id')
        self.assertFalse(stage.archive_only)
        self.assertFalse(stage.needs_row)
        self.assertEqual(stage.archive_producers, ())
        self.assertEqual(stage.legacy_owners, ())
        self.assertEqual(stage.resident_owners, ())
        self.assertIsNone(stage.peel)
        self.assertEqual(ms.chain_for('lottery-id')[-2:],
                         ('bag-view-position', 'lottery-id'))

    def test_bag_view_position_is_a_confined_non_resident_stage(self):
        stage = ms.require_stage('bag-view-position')
        self.assertEqual(stage.name, 'bag-view-position')
        self.assertFalse(stage.archive_only)
        self.assertFalse(stage.needs_row)
        self.assertEqual(stage.archive_producers, ())
        self.assertEqual(stage.legacy_owners, ())
        self.assertEqual(stage.resident_owners, ())
        self.assertIsNone(stage.peel)
        self.assertEqual(ms.chain_for('bag-view-position')[-2:],
                         ('bag-foreign', 'bag-view-position'))

    def test_battle_tower_wrap_is_a_confined_non_resident_stage(self):
        stage = ms.require_stage('battle-tower-wrap')
        self.assertEqual(stage.name, 'battle-tower-wrap')
        self.assertFalse(stage.archive_only)
        self.assertFalse(stage.needs_row)
        self.assertEqual(stage.archive_producers, ())
        self.assertEqual(stage.legacy_owners, ())
        self.assertEqual(stage.resident_owners, ())
        self.assertIsNone(stage.peel)
        self.assertEqual(ms.chain_for('battle-tower-wrap')[-2:],
                         ('lottery-id', 'battle-tower-wrap'))

    def test_facade_animation_is_a_confined_non_resident_stage(self):
        stage = ms.require_stage('battle-animation-facade')
        self.assertEqual(stage.name, 'battle-animation-facade')
        self.assertFalse(stage.archive_only)
        self.assertFalse(stage.needs_row)
        self.assertEqual(stage.archive_producers, ())
        self.assertEqual(stage.legacy_owners, ())
        self.assertEqual(stage.resident_owners, ())
        self.assertIsNone(stage.peel)
        self.assertEqual(ms.chain_for('battle-animation-facade')[-2:],
                         ('battle-tower-wrap', 'battle-animation-facade'))

    def test_dynamicpunch_animation_is_a_confined_facade_successor(self):
        stage = ms.require_stage('battle-animation-dynamicpunch')
        self.assertEqual(stage.name, 'battle-animation-dynamicpunch')
        self.assertFalse(stage.archive_only)
        self.assertFalse(stage.needs_row)
        self.assertEqual(stage.archive_producers, ())
        self.assertEqual(stage.legacy_owners, ())
        self.assertEqual(stage.resident_owners, ())
        self.assertIsNone(stage.peel)
        self.assertEqual(ms.chain_for('battle-animation-dynamicpunch')[-2:],
                         ('battle-animation-facade', 'battle-animation-dynamicpunch'))

    def test_helping_hand_animation_is_a_confined_dynamicpunch_successor(self):
        stage = ms.require_stage('battle-animation-helping-hand')
        self.assertEqual(stage.name, 'battle-animation-helping-hand')
        self.assertFalse(stage.archive_only)
        self.assertFalse(stage.needs_row)
        self.assertEqual(stage.archive_producers, ())
        self.assertEqual(stage.legacy_owners, ())
        self.assertEqual(stage.resident_owners, ())
        self.assertIsNone(stage.peel)
        self.assertEqual(ms.chain_for('battle-animation-helping-hand')[-2:],
                         ('battle-animation-dynamicpunch',
                          'battle-animation-helping-hand'))

    def test_strength_animation_is_a_confined_helping_hand_successor(self):
        stage = ms.require_stage('battle-animation-strength')
        self.assertEqual(stage.name, 'battle-animation-strength')
        self.assertFalse(stage.archive_only)
        self.assertFalse(stage.needs_row)
        self.assertEqual(stage.archive_producers, ())
        self.assertEqual(stage.legacy_owners, ())
        self.assertEqual(stage.resident_owners, ())
        self.assertIsNone(stage.peel)
        self.assertEqual(ms.chain_for('battle-animation-strength')[-2:],
                         ('battle-animation-helping-hand',
                          'battle-animation-strength'))

    def test_spit_up_animation_is_a_confined_strength_successor(self):
        stage = ms.require_stage('battle-animation-spit-up')
        self.assertEqual(stage.name, 'battle-animation-spit-up')
        self.assertFalse(stage.archive_only)
        self.assertFalse(stage.needs_row)
        self.assertIsNone(stage.peel)
        self.assertEqual(ms.chain_for('battle-animation-spit-up')[-2:],
                         ('battle-animation-strength',
                          'battle-animation-spit-up'))

    def test_giratina_pc_form_is_a_confined_spit_up_successor(self):
        stage = ms.require_stage('giratina-pc-form')
        self.assertEqual(stage.name, 'giratina-pc-form')
        self.assertFalse(stage.archive_only)
        self.assertFalse(stage.needs_row)
        self.assertIsNone(stage.peel)
        self.assertEqual(ms.chain_for('giratina-pc-form')[-2:],
                         ('battle-animation-spit-up', 'giratina-pc-form'))

    def test_invisible_grass_is_a_confined_giratina_successor(self):
        stage = ms.require_stage('invisible-grass')
        self.assertEqual(stage.name, 'invisible-grass')
        self.assertFalse(stage.archive_only)
        self.assertFalse(stage.needs_row)
        self.assertEqual(stage.archive_producers, ())
        self.assertEqual(stage.legacy_owners, ())
        self.assertEqual(stage.resident_owners, ())
        self.assertIsNone(stage.peel)
        self.assertEqual(ms.chain_for('invisible-grass')[-2:],
                         ('giratina-pc-form', 'invisible-grass'))

    def test_waterfall_facing_is_confined_and_owns_the_legacy_tail(self):
        stage = ms.require_stage('waterfall-facing')
        self.assertEqual(stage.name, 'waterfall-facing')
        self.assertFalse(stage.archive_only)
        self.assertFalse(stage.needs_row)
        self.assertEqual(stage.legacy_owners, ('sgp.waterfall_facing',))
        self.assertEqual(stage.resident_owners, ())
        self.assertIsNone(stage.peel)
        self.assertEqual(ms.chain_for('waterfall-facing')[-2:],
                         ('invisible-grass', 'waterfall-facing'))

    def test_follower_menu_jump_shares_overlay_one_with_an_exact_peel(self):
        stage = ms.require_stage('follower-menu-jump')
        self.assertEqual(stage.name, 'follower-menu-jump')
        self.assertFalse(stage.archive_only)
        self.assertFalse(stage.needs_row)
        self.assertEqual(stage.legacy_owners, ())
        self.assertEqual(stage.resident_owners, ())
        self.assertIsNotNone(stage.peel)
        self.assertEqual(ms.chain_for('follower-menu-jump')[-2:],
                         ('waterfall-facing', 'follower-menu-jump'))

    def test_implemented_and_pending_are_exact_and_disjoint(self):
        self.assertEqual(ms.IMPLEMENTED, ('moves', 'ai', 'ai-immunities', 'abilities', 'gifts', 'legacy', 'legendary-scenes', 'legendary-scene-version', 'trainer-fixes', 'pokeathlon', 'traded-egg', 'bag-foreign', 'bag-view-position', 'lottery-id', 'battle-tower-wrap', 'battle-animation-facade', 'battle-animation-dynamicpunch', 'battle-animation-helping-hand', 'battle-animation-strength', 'battle-animation-spit-up', 'giratina-pc-form', 'invisible-grass', 'waterfall-facing', 'follower-menu-jump', 'controls', 'portable', 'rematches', 'uturn-flinch', 'identity'))
        self.assertEqual(ms.REGISTRY['bag-foreign'].resident_owners,
                         ('training.code',))
        self.assertEqual(ms.REGISTRY['bag-foreign'].legacy_owners, ())
        self.assertEqual(ms.PENDING, {})
        self.assertFalse(set(ms.IMPLEMENTED) & set(ms.PENDING))

    def test_pending_is_a_dedicated_error_not_a_stub(self):
        self.assertTrue(issubclass(ms.StagePending, ValueError))
        with patch.dict(ms.PENDING, {'future-stage': ('missing reviewed installer',)}, clear=True):
            with self.assertRaises(ms.StagePending) as caught:
                ms.require_stage('future-stage')
            self.assertEqual(caught.exception.stage, 'future-stage')
            self.assertEqual(caught.exception.reasons, ('missing reviewed installer',))
            self.assertIn('pending', str(caught.exception))

    def test_abilities_is_a_registered_stage_with_an_explicit_reserve_slot_and_a_text_producer(self):
        stage = ms.require_stage('abilities')
        self.assertEqual(stage.name, 'abilities')
        self.assertEqual(stage.slot, 'modern-accuracy.code')
        self.assertEqual(stage.slot_payload, 28)
        self.assertTrue(stage.needs_row)
        self.assertEqual(stage.archive_producers, ('keen-eye-text',))   # the text travels as an archive delta, never appended
        self.assertTrue(callable(stage.peel))                           # it shares the overlay 12 slot with `ai`
        ai = ms.require_stage('ai')
        self.assertTrue(ai.needs_row)
        self.assertEqual((ai.slot, ai.slot_payload), ('fairy-ai.code', 148))
        self.assertTrue(callable(ai.peel))       # restores FAT/y9 and the derived UI seed as well as overlay 12
        self.assertIs(ai.invariants, ms.check_ai_ui_invariants)
        for name in ('moves', 'ai-immunities'):
            plain = ms.require_stage(name)
            self.assertFalse(plain.needs_row)
            self.assertEqual(plain.archive_producers, ())
            self.assertIsNone(plain.peel)

    def test_uturn_stage_owns_only_the_c8_tail_two_seams_and_script(self):
        stage = ms.require_stage('uturn-flinch')
        self.assertEqual((stage.slot, stage.slot_payload),
                         ('c8.module-stubs', 192))
        self.assertTrue(stage.contextual)
        self.assertEqual(stage.archive_producers,
                         ('uturn-item-snapshot',))
        self.assertTrue(callable(stage.peel))
        self.assertIs(stage.invariants, ms.check_ai_ui_invariants)
        self.assertEqual(ms.chain_for('uturn-flinch')[-2:],
                         ('rematches', 'uturn-flinch'))

    def test_ai_immunities_is_a_confined_two_region_stage(self):
        stage = ms.require_stage('ai-immunities')
        self.assertEqual(stage.name, 'ai-immunities')
        self.assertFalse(stage.archive_only)
        self.assertFalse(stage.needs_row)
        self.assertEqual(stage.archive_producers, ())
        self.assertIsNone(stage.peel)
        self.assertEqual(ms.chain_for('ai-immunities'),
                         ('moves', 'ai', 'ai-immunities'))

    def test_legacy_names_only_the_reviewed_reserve_owners_it_rewrites(self):
        stage = ms.require_stage('legacy')
        self.assertEqual(stage.legacy_owners,
                         ('sgp.plus', 'sgp.capacita_borsa', 'sgp.soul_dew',
                          'sgp.wonder_card', 'sgp.gb_sounds_evolution',
                          'sgp.pokegear_autocull'))
        self.assertIsNone(stage.slot)
        self.assertFalse(stage.needs_row)
        with self.assertRaisesRegex(ValueError, 'cannot mix'):
            ms.MechanicalStage('mixed', lambda d, l: (d, {}), lambda *a: {}, lambda rom: [],
                               slot='modern-accuracy.code', slot_payload=1,
                               legacy_owners=('sgp.plus',))
        for owners in (['sgp.plus'], ('sgp.plus', 'sgp.plus'), ('',)):
            with self.subTest(owners=owners), self.assertRaisesRegex(ValueError, 'legacy reserve owners'):
                ms.MechanicalStage('bad', lambda d, l: (d, {}), lambda *a: {}, lambda rom: [],
                                   legacy_owners=owners)
        for owners in (['training.code'], ('training.code', 'training.code'), ('',)):
            with self.subTest(owners=owners), self.assertRaisesRegex(ValueError, 'current resident reserve owners'):
                ms.MechanicalStage('bad', lambda d, l: (d, {}), lambda *a: {}, lambda rom: [],
                                   resident_owners=owners)
        with self.assertRaisesRegex(ValueError, 'cannot mix legacy and current'):
            ms.MechanicalStage('mixed-owners', lambda d, l: (d, {}), lambda *a: {}, lambda rom: [],
                               legacy_owners=('sgp.plus',), resident_owners=('training.code',))

    def test_gifts_is_an_archive_only_stage_without_a_post_ui_writer(self):
        stage = ms.require_stage('gifts')
        self.assertEqual(stage.name, 'gifts')
        self.assertTrue(stage.archive_only)
        self.assertEqual(stage.archive_producers, ('gifts-scripts',))   # the script fixes travel as an archive delta
        self.assertIsNone(stage.slot)                                    # no reserve memory
        self.assertFalse(stage.needs_row)
        self.assertIsNone(stage.peel)
        for attribute in ('apply', 'verify', 'regions'):                 # no ARM9 region, no writer, no own reader
            self.assertIsNone(getattr(stage, attribute))
        for name in ('moves', 'ai', 'ai-immunities', 'abilities'):
            self.assertFalse(ms.require_stage(name).archive_only)

    def test_writers_drop_the_archive_only_stage_and_the_producers_keep_it(self):
        self.assertEqual(ms.writers(ms.chain_for('gifts')), ('moves', 'ai', 'ai-immunities', 'abilities'))
        self.assertEqual(ms.writers(ms.chain_for('ai')), ('moves', 'ai'))
        self.assertEqual(ms.required_producers(ms.chain_for('gifts')), ('gifts-scripts', 'keen-eye-text'))
        self.assertEqual(ms.required_producers(ms.chain_for('abilities')), ('keen-eye-text',))
        self.assertEqual(ms.required_producers(ms.chain_for('ai')), ())

    def test_legendary_scenes_is_a_separate_archive_only_owner_after_legacy(self):
        stage = ms.require_stage('legendary-scenes')
        self.assertTrue(stage.archive_only)
        self.assertEqual(stage.archive_producers, ('legendary-scenes-scripts',))
        self.assertEqual(ms.writers(ms.chain_for('legendary-scenes'))[-1], 'legacy')
        self.assertIn('legendary-scenes-scripts',
                      ms.required_producers(ms.chain_for('legendary-scenes')))
        self.assertEqual(ms.chain_for('legendary-scenes')[-2:],
                         ('legacy', 'legendary-scenes'))

    def test_an_archive_only_stage_has_no_writer_to_run_or_replay(self):
        version = ms.require_stage('legendary-scene-version')
        self.assertFalse(version.archive_only)
        self.assertEqual(ms.chain_for('legendary-scene-version')[-2:],
                         ('legendary-scenes', 'legendary-scene-version'))
        with self.assertRaisesRegex(ms.CompositionError, 'no post-UI writer'):
            ms.run_stage('gifts', b'\0' * 0x400, 'EN')
        with self.assertRaisesRegex(ms.CompositionError, 'no post-UI writer'):
            ms.verify_chain(BEFORE, BEFORE, ['gifts'], [{}], lambda image: {})

    def test_the_archive_only_shape_is_all_or_nothing(self):
        for kwargs in ({'archive_producers': ()}, {'archive_producers': ('x',), 'slot': 'y', 'slot_payload': 4}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                ms.MechanicalStage('half', None, None, None, **kwargs)
        with self.assertRaises(ValueError):
            ms.MechanicalStage('half', lambda d, l: (d, {}), None, None, archive_producers=('x',))
        ms.MechanicalStage('ok', None, None, None, archive_producers=('x',))

    def test_unknown_stage_is_not_pending(self):
        with self.assertRaises(ValueError) as caught:
            ms.require_stage('typo')
        self.assertNotIsInstance(caught.exception, ms.StagePending)

    def test_chain_is_the_implemented_prefix_ending_at_the_requested_stage(self):
        self.assertEqual(ms.chain_for('baseline'), ())
        self.assertEqual(ms.chain_for('ui'), ())
        self.assertEqual(ms.chain_for('moves'), ('moves',))
        self.assertEqual(ms.chain_for('ai'), ('moves', 'ai'))
        self.assertEqual(ms.chain_for('abilities'), ('moves', 'ai', 'ai-immunities', 'abilities'))
        self.assertEqual(ms.chain_for('gifts'), ('moves', 'ai', 'ai-immunities', 'abilities', 'gifts'))
        self.assertEqual(ms.chain_for('identity'), ms.IMPLEMENTED)
        with patch.dict(ms.PENDING, {'future-stage': ('missing reviewed installer',)}, clear=True):
            with self.assertRaises(ms.StagePending):
                ms.chain_for('future-stage')
        with self.assertRaises(ValueError):
            ms.chain_for('unknown-stage')

    def test_run_stage_refuses_pending_before_reading_data(self):
        with patch.dict(ms.PENDING, {'future-stage': ('missing reviewed installer',)}, clear=True):
            with self.assertRaises(ms.StagePending):
                ms.run_stage('future-stage', object(), 'EN')

    def test_real_stage_entries_declare_uniform_interface(self):
        for name in ms.writers(ms.IMPLEMENTED):
            stage = ms.require_stage(name)
            self.assertEqual(stage.name, name)
            for attribute in ('apply', 'verify', 'regions'):
                self.assertTrue(callable(getattr(stage, attribute)))


class WrappedReceipt(unittest.TestCase):
    def test_run_stage_produces_json_safe_chained_receipts(self):
        final, receipts = chain(['one', 'two'])
        json.dumps(receipts)
        self.assertEqual(receipts[0]['input_sha256'], sha(BEFORE))
        self.assertEqual(receipts[0]['output_sha256'], receipts[1]['input_sha256'])
        self.assertEqual(receipts[1]['output_sha256'], sha(final))
        self.assertEqual([r['stage'] for r in receipts], ['one', 'two'])
        for receipt, name in zip(receipts, ('one', 'two')):
            ms.validate_receipt(receipt, name, 'EN')

    def test_validate_rejects_shape_changes(self):
        _, receipts = chain(['one'])
        good = receipts[0]
        for key, value in (('stage', 'two'), ('schema', 2), ('language', 'IT'), ('input_sha256', 'zz'),
                           ('output_bytes', -1), ('regions', []), ('stage_receipt_sha256', '0' * 64),
                           ('changed_ranges', []), ('changed_ranges', [[12, 11]]), ('changed_ranges', [[10, 12], [11, 13]]),
                           ('changed_ranges', [[0, 1]]), ('changed_ranges', [[10, 11, 12]])):
            bad = dict(good, **{key: value})
            with self.subTest(key=key), self.assertRaises(ValueError):
                ms.validate_receipt(bad, 'one', 'EN')
        extra = dict(good, extra=1)
        with self.assertRaises(ValueError):
            ms.validate_receipt(extra, 'one', 'EN')

    def test_receipt_hash_binds_the_embedded_stage_receipt(self):
        _, receipts = chain(['one'])
        forged = json.loads(json.dumps(receipts[0]))
        forged['stage_receipt']['value'] = 0xFF
        with self.assertRaisesRegex(ValueError, 'stage receipt'):
            ms.validate_receipt(forged, 'one', 'EN')

    def test_stage_that_touches_outside_its_declared_region_is_rejected_when_run(self):
        class Wild(FakeStage):
            def apply(self, data, language):
                out, receipt = super().apply(data, language)
                tampered = bytearray(out)
                tampered[90] = 1
                return bytes(tampered), receipt
        registry = {'wild': Wild('wild', 10, 20, 5)}
        with self.assertRaisesRegex(ms.CompositionError, 'outside declared'):
            ms.run_stage('wild', BEFORE, 'EN', invariants=no_structure, registry=registry)

    def test_stage_without_a_visible_change_is_rejected(self):
        class Idle(FakeStage):
            def apply(self, data, language):
                return data, {'offset': 10, 'value': 0}
        with self.assertRaises(ValueError):
            ms.run_stage('idle', BEFORE, 'EN', invariants=no_structure, registry={'idle': Idle('idle', 10, 20, 0)})


class ChainVerification(unittest.TestCase):
    def verify(self, final, names, receipts, seen=None):
        def verify_ui(image):
            if seen is not None:
                seen.append(image)
            return {'ui': 'accepted'}
        return ms.verify_chain(BEFORE, final, names, receipts, verify_ui,
                               invariants=no_structure, registry=REGISTRY)

    def test_valid_chain_reconstructs_the_exact_ui_image_for_independent_verification(self):
        final, receipts = chain(['one', 'two'])
        seen = []
        result = self.verify(final, ['one', 'two'], receipts, seen)
        self.assertEqual(seen, [BEFORE])
        self.assertEqual(result['stages'], ['one', 'two'])
        self.assertEqual(result['ui'], {'ui': 'accepted'})

    def test_order_of_disjoint_stages_is_equivalent_when_both_orders_are_declared(self):
        a, ra = chain(['one', 'two'])
        b, rb = chain(['two', 'one'])
        self.assertEqual(a, b)
        self.verify(a, ['one', 'two'], ra)
        self.verify(b, ['two', 'one'], rb)

    def test_change_outside_all_declared_regions_is_rejected(self):
        final, receipts = chain(['one', 'two'])
        tampered = bytearray(final)
        tampered[60] = 9
        with self.assertRaisesRegex(ms.CompositionError, 'differs|outside|does not describe'):
            self.verify(bytes(tampered), ['one', 'two'], receipts)

    def test_receipt_chain_must_match_roms_and_order(self):
        final, receipts = chain(['one', 'two'])
        with self.assertRaisesRegex(ValueError, 'receipt'):
            self.verify(final, ['one', 'two'], list(reversed(receipts)))
        with self.assertRaisesRegex(ms.CompositionError, 'count|receipt'):
            self.verify(final, ['one', 'two'], receipts[:1])
        with self.assertRaises(ValueError):
            self.verify(final, ['one', 'one'], receipts)

    def test_receipts_for_the_wrong_stage_names_are_refused(self):
        final, receipts = chain(['one'])
        with self.assertRaises(ValueError):
            self.verify(final, ['one', 'two'], receipts + receipts)

    def test_declared_region_that_does_not_change_is_rejected_even_with_a_lenient_stage_reader(self):
        class Lenient(FakeStage):
            def verify(self, before, after, receipt):
                return {}
        registry = {'one': Lenient('one', 10, 20, 0)}
        wrapped = ms._wrap('one', 'EN', BEFORE, BEFORE, registry['one'].regions(BEFORE), {'offset': 10, 'value': 0})
        wrapped['changed_ranges'] = [[10, 11]]          # a forged claim: the bytes did not change
        with self.assertRaisesRegex(ms.CompositionError, 'unchanged'):
            ms.verify_chain(BEFORE, BEFORE, ['one'], [wrapped], lambda image: {},
                            invariants=no_structure, registry=registry)

    def test_independent_verifier_is_called_and_its_rejection_propagates(self):
        final, receipts = chain(['one'])
        def refuse(image):
            raise ValueError('foreign active file 140')
        with self.assertRaisesRegex(ValueError, 'foreign active file'):
            ms.verify_chain(BEFORE, final, ['one'], receipts, refuse, invariants=no_structure, registry=REGISTRY)

    def test_overlapping_stage_regions_cannot_be_reconstructed(self):
        registry = {'one': FakeStage('one', 10, 20, 1), 'clash': FakeStage('clash', 15, 25, 2)}
        data, r1 = ms.run_stage('one', BEFORE, 'EN', invariants=no_structure, registry=registry)
        data, r2 = ms.run_stage('clash', data, 'EN', invariants=no_structure, registry=registry)
        with self.assertRaisesRegex(ms.CompositionError, 'overlap'):
            ms.verify_chain(BEFORE, data, ['one', 'clash'], [r1, r2], lambda image: {},
                            invariants=no_structure, registry=registry)

    def test_stage_verifier_failure_on_the_reconstructed_step_is_not_masked(self):
        final, receipts = chain(['one'])
        class Strict(FakeStage):
            def verify(self, before, after, receipt):
                raise ValueError('independent stage readback refused')
        with self.assertRaisesRegex(ValueError, 'readback refused'):
            ms.verify_chain(BEFORE, final, ['one'], receipts, lambda image: {},
                            invariants=no_structure, registry={'one': Strict('one', 10, 20, 0xA1)})


class ActualChangedRanges(unittest.TestCase):
    def test_receipt_reports_the_bytes_that_really_changed_not_only_the_declared_region(self):
        _, receipts = chain(['one', 'two'])
        self.assertEqual([r['changed_ranges'] for r in receipts], [[[10, 11]], [[30, 31]]])
        self.assertEqual(receipts[0]['regions'], [{'start': 10, 'end': 20, 'label': 'one.file'}])

    def test_replay_refuses_a_receipt_whose_ranges_differ_from_the_replayed_bytes(self):
        final, receipts = chain(['one', 'two'])
        for claimed in ([[10, 12]], [[11, 12]], [[10, 11], [15, 16]]):
            forged = json.loads(json.dumps(receipts))
            forged[0]['changed_ranges'] = claimed
            with self.subTest(claimed=claimed), self.assertRaisesRegex(ms.CompositionError, 'changed_ranges'):
                ms.verify_chain(BEFORE, final, ['one', 'two'], forged, lambda image: {},
                                invariants=no_structure, registry=REGISTRY)


class FailClosed(unittest.TestCase):
    ERRORS = (struct.error('truncated'), KeyError('x'), IndexError('i'), TypeError('t'), AttributeError('a'),
              OverflowError('o'), UnicodeDecodeError('utf-8', b'\xff', 0, 1, 'bad'))

    def test_any_non_value_error_from_a_stage_reader_or_writer_is_a_composition_error(self):
        for error in self.ERRORS:
            for hook in ('apply', 'verify', 'regions'):
                class Boom(FakeStage):
                    pass
                def raiser(*args, _e=error):
                    raise _e
                setattr(Boom, hook, raiser)
                with self.subTest(error=type(error).__name__, hook=hook), \
                        self.assertRaisesRegex(ms.CompositionError, 'fail-closed'):
                    ms.run_stage('x', BEFORE, 'EN', invariants=no_structure, registry={'x': Boom('x', 10, 20, 1)})

    def test_non_value_error_from_the_invariant_reader_or_ui_verifier_is_a_composition_error(self):
        final, receipts = chain(['one'])
        def raising_invariants(prev, nxt, regions):
            raise struct.error('mutated FNT')
        with self.assertRaisesRegex(ms.CompositionError, 'fail-closed'):
            ms.run_stage('one', BEFORE, 'EN', invariants=raising_invariants, registry=REGISTRY)
        def raising_ui(image):
            raise KeyError('a/0/2/7')
        with self.assertRaisesRegex(ms.CompositionError, 'fail-closed'):
            ms.verify_chain(BEFORE, final, ['one'], receipts, raising_ui, invariants=no_structure, registry=REGISTRY)
        with self.assertRaisesRegex(ms.CompositionError, 'fail-closed'):
            ms.verify_chain(BEFORE, final, ['one'], receipts, lambda image: {}, invariants=raising_invariants,
                            registry=REGISTRY)

    def test_value_errors_keep_their_own_message(self):
        def refuse(image):
            raise ValueError('foreign active file 140')
        final, receipts = chain(['one'])
        with self.assertRaisesRegex(ValueError, 'foreign active file 140'):
            ms.verify_chain(BEFORE, final, ['one'], receipts, refuse, invariants=no_structure, registry=REGISTRY)

    def test_malformed_cartridge_bytes_are_refused_not_crashed(self):
        for data in (b'', b'\0' * 0x1FF, bytes(0x400), b'\xff' * 0x4000):
            with self.subTest(size=len(data)), self.assertRaises(ms.CompositionError):
                ms.check_ui_invariants(data, data, [])


class RegistryOrder(unittest.TestCase):
    def test_order_implemented_and_pending_agree(self):
        self.assertEqual(ms.ORDER, ('moves', 'ai', 'ai-immunities', 'abilities', 'gifts', 'legacy', 'legendary-scenes', 'legendary-scene-version', 'trainer-fixes', 'pokeathlon', 'traded-egg', 'bag-foreign', 'bag-view-position', 'lottery-id', 'battle-tower-wrap', 'battle-animation-facade', 'battle-animation-dynamicpunch', 'battle-animation-helping-hand', 'battle-animation-strength', 'battle-animation-spit-up', 'giratina-pc-form', 'invisible-grass', 'waterfall-facing', 'follower-menu-jump', 'controls', 'portable', 'rematches', 'uturn-flinch', 'identity'))
        self.assertEqual(ms.IMPLEMENTED, ('moves', 'ai', 'ai-immunities', 'abilities', 'gifts', 'legacy', 'legendary-scenes', 'legendary-scene-version', 'trainer-fixes', 'pokeathlon', 'traded-egg', 'bag-foreign', 'bag-view-position', 'lottery-id', 'battle-tower-wrap', 'battle-animation-facade', 'battle-animation-dynamicpunch', 'battle-animation-helping-hand', 'battle-animation-strength', 'battle-animation-spit-up', 'giratina-pc-form', 'invisible-grass', 'waterfall-facing', 'follower-menu-jump', 'controls', 'portable', 'rematches', 'uturn-flinch', 'identity'))
        self.assertEqual(ms.REGISTRY['bag-foreign'].resident_owners,
                         ('training.code',))
        self.assertEqual(ms.REGISTRY['bag-foreign'].legacy_owners, ())
        self.assertEqual(set(ms.ORDER), set(ms.IMPLEMENTED) | set(ms.PENDING))
        self.assertEqual(ms.IMPLEMENTED, tuple(name for name in ms.ORDER if name in ms.IMPLEMENTED))
        self.assertEqual(set(ms.REGISTRY), set(ms.IMPLEMENTED))
        for name in ms.IMPLEMENTED:
            self.assertEqual(ms.REGISTRY[name].name, name)

    def test_implemented_stages_form_a_prefix_of_the_order(self):
        # chain_for is a prefix rule: a pending stage may never sit before an implemented one
        first_pending = min((ms.ORDER.index(n) for n in ms.PENDING), default=len(ms.ORDER))
        self.assertTrue(all(ms.ORDER.index(n) < first_pending for n in ms.IMPLEMENTED))

    def test_the_module_refuses_to_import_when_its_own_tables_drift(self):
        source = Path(ms.__file__).read_text()
        for old, new in (("ORDER = ('moves', 'ai', 'ai-immunities', 'abilities',", "ORDER = ('ai', 'moves', 'ai-immunities', 'abilities',"),
                         ("IMPLEMENTED = ('moves', 'ai', 'ai-immunities', 'abilities', 'gifts', 'legacy', 'legendary-scenes', 'legendary-scene-version', 'trainer-fixes', 'pokeathlon', 'traded-egg', 'bag-foreign', 'bag-view-position', 'lottery-id', 'battle-tower-wrap', 'battle-animation-facade', 'battle-animation-dynamicpunch', 'battle-animation-helping-hand', 'battle-animation-strength', 'battle-animation-spit-up', 'giratina-pc-form', 'invisible-grass', 'waterfall-facing', 'follower-menu-jump', 'controls', 'portable', 'rematches', 'uturn-flinch', 'identity')", "IMPLEMENTED = ('moves', 'ai', 'abilities')"),
                         ("IMPLEMENTED = ('moves', 'ai', 'ai-immunities', 'abilities', 'gifts', 'legacy', 'legendary-scenes', 'legendary-scene-version', 'trainer-fixes', 'pokeathlon', 'traded-egg', 'bag-foreign', 'bag-view-position', 'lottery-id', 'battle-tower-wrap', 'battle-animation-facade', 'battle-animation-dynamicpunch', 'battle-animation-helping-hand', 'battle-animation-strength', 'battle-animation-spit-up', 'giratina-pc-form', 'invisible-grass', 'waterfall-facing', 'follower-menu-jump', 'controls', 'portable', 'rematches', 'uturn-flinch', 'identity')", "IMPLEMENTED = ('moves', 'abilities', 'gifts')"),
                         ("ORDER = ('moves', 'ai', 'ai-immunities', 'abilities', 'gifts', 'legacy', 'legendary-scenes', 'legendary-scene-version', 'trainer-fixes', 'pokeathlon', 'traded-egg', 'bag-foreign', 'bag-view-position', 'lottery-id', 'battle-tower-wrap', 'battle-animation-facade', 'battle-animation-dynamicpunch', 'battle-animation-helping-hand', 'battle-animation-strength', 'battle-animation-spit-up', 'giratina-pc-form', 'invisible-grass', 'waterfall-facing', 'follower-menu-jump', 'controls', 'portable', 'rematches', 'uturn-flinch', 'identity')",
                          "ORDER = ('moves', 'ai', 'ai-immunities', 'abilities', 'gifts', 'legacy', 'legendary-scenes', 'legendary-scene-version', 'trainer-fixes', 'pokeathlon', 'traded-egg', 'bag-foreign', 'bag-view-position', 'lottery-id', 'controls', 'portable', 'rematches')")):
            self.assertEqual(source.count(old), 1, old)
            with self.subTest(drift=new), self.assertRaises(ValueError):
                exec(compile(source.replace(old, new), 'drifted_mechanics_stages', 'exec'), {'__name__': 'drifted'})
        exec(compile(source, 'pristine_mechanics_stages', 'exec'), {'__name__': 'pristine'})   # the control imports fine

    def test_drift_between_order_and_registry_is_refused_at_import_time(self):
        with self.assertRaises(ValueError):
            ms.check_registry_consistency(order=('moves', 'ai'), implemented=('moves', 'ai'), pending={'x': ('r',)},
                                          registry=ms.REGISTRY)
        with self.assertRaises(ValueError):                      # abilities listed implemented but not registered
            ms.check_registry_consistency(order=('moves', 'ai', 'abilities'), implemented=('moves', 'ai', 'abilities'),
                                          pending={}, registry={k: v for k, v in ms.REGISTRY.items() if k != 'abilities'})
        with self.assertRaises(ValueError):
            ms.check_registry_consistency(order=('ai', 'moves', 'controls'), implemented=('moves', 'ai'),
                                          pending={'controls': ('r',)}, registry=ms.REGISTRY)


class SharedRegionStage(FakeStage):
    """Second writer of a region another stage already declared (the way `abilities` re-writes overlay 12 after `ai`)."""
    def __init__(self, name, start, end, value, offset):
        super().__init__(name, start, end, value)
        self.offset = offset

    def apply(self, data, language):
        out = bytearray(data)
        out[self.offset] = self.value
        return bytes(out), {'fake': self.name, 'offset': self.offset, 'value': self.value}

    def peel(self, after, before, regions):
        out = bytearray(after)
        out[self.offset] = before[self.offset]
        return bytes(out)


def shared_registry(peel=True, second_span=(10, 20), first_span=(10, 20)):
    second = SharedRegionStage('two', *second_span, 0xC3, offset=second_span[0] + 2)
    if not peel:
        second.peel = None
    return {'one': FakeStage('one', *first_span, 0xA1), 'two': second}


class SharedRegions(unittest.TestCase):
    """Two stages may declare the identical region only when the later one can peel itself back out of it."""

    def run_chain(self, registry, order=('one', 'two')):
        data, receipts = BEFORE, []
        for name in order:
            data, receipt = ms.run_stage(name, data, 'EN', invariants=no_structure, registry=registry)
            receipts.append(receipt)
        return data, receipts

    def verify(self, final, receipts, registry, order=('one', 'two'), seen=None):
        def verify_ui(image):
            if seen is not None:
                seen.append(image)
            return {'ui': 'accepted'}
        return ms.verify_chain(BEFORE, final, list(order), receipts, verify_ui, invariants=no_structure,
                               registry=registry)

    def test_a_peelable_stage_may_share_the_identical_region_and_the_chain_replays(self):
        registry = shared_registry()
        final, receipts = self.run_chain(registry)
        self.assertEqual((final[10], final[12]), (0xA1, 0xC3))
        seen = []
        result = self.verify(final, receipts, registry, seen=seen)
        self.assertEqual(seen, [BEFORE])
        self.assertEqual(result['stages'], ['one', 'two'])
        self.assertEqual(result['output_sha256'], sha(final))
        self.assertEqual(receipts[1]['input_sha256'], receipts[0]['output_sha256'])

    def test_the_intermediate_image_is_the_exact_output_of_the_first_stage(self):
        registry = shared_registry()
        final, receipts = self.run_chain(registry)
        first_only = bytearray(BEFORE)
        first_only[10] = 0xA1
        self.assertEqual(receipts[1]['input_sha256'], sha(bytes(first_only)))
        forged = json.loads(json.dumps(receipts))
        forged[1]['input_sha256'] = sha(BEFORE)                      # claims the second stage ran on the untouched image
        with self.assertRaisesRegex(ms.CompositionError, 'does not describe'):
            self.verify(final, forged, registry)

    def test_sharing_without_a_peel_is_an_overlap(self):
        registry = shared_registry(peel=False)
        final, receipts = self.run_chain(registry)
        with self.assertRaisesRegex(ms.CompositionError, 'overlap'):
            self.verify(final, receipts, registry)

    def test_partial_overlap_is_never_shareable_even_with_a_peel(self):
        registry = shared_registry(second_span=(15, 25))
        final, receipts = self.run_chain(registry)
        with self.assertRaisesRegex(ms.CompositionError, 'overlap'):
            self.verify(final, receipts, registry)

    def test_the_earlier_stage_cannot_be_the_one_that_shares(self):
        registry = shared_registry()
        final, receipts = self.run_chain(registry, ('two', 'one'))
        with self.assertRaisesRegex(ms.CompositionError, 'overlap'):
            self.verify(final, receipts, registry, ('two', 'one'))

    def test_a_peel_that_leaves_the_stage_bytes_behind_is_refused(self):
        registry = shared_registry()
        registry['two'].peel = lambda after, before, regions: after
        final, receipts = self.run_chain(registry)
        with self.assertRaises(ms.CompositionError):
            self.verify(final, receipts, registry)

    def test_a_peel_that_touches_bytes_outside_its_declaration_is_refused(self):
        registry = shared_registry()
        def greedy(after, before, regions):
            out = bytearray(after)
            out[12] = before[12]
            out[50] = 7
            return bytes(out)
        registry['two'].peel = greedy
        final, receipts = self.run_chain(registry)
        with self.assertRaises(ms.CompositionError):
            self.verify(final, receipts, registry)

    def test_a_foreign_exception_or_length_change_in_a_peel_is_a_composition_error(self):
        for hook in (lambda a, b, r: (_ for _ in ()).throw(KeyError('x')), lambda a, b, r: a + b'\0', lambda a, b, r: None):
            registry = shared_registry()
            registry['two'].peel = hook
            final, receipts = self.run_chain(registry)
            with self.assertRaises(ms.CompositionError):
                self.verify(final, receipts, registry)

    def test_foreign_bytes_outside_every_declared_region_are_still_refused(self):
        registry = shared_registry()
        final, receipts = self.run_chain(registry)
        tampered = bytearray(final)
        tampered[60] = 9
        with self.assertRaisesRegex(ms.CompositionError, 'differs|outside|does not describe'):
            self.verify(bytes(tampered), receipts, registry)


class ReserveRows(unittest.TestCase):
    """The reserve row is the only source of a slot; without a proven row a slot stage refuses, explicitly."""

    def slot_stage(self, slot='modern-accuracy.code', payload=28):
        def apply(data, language, *, row, work_dir):
            return data, {}
        return ms.MechanicalStage('slotty', apply, lambda *a: {}, lambda rom: [], slot=slot, slot_payload=payload)

    def row(self, **changes):
        _, part = ms.reserve_slot('modern-accuracy.code')
        row = {'name': part['name'], 'parent': 'field-guide.code', 'start': part['start'], 'bytes': 28,
               'capacity': part['bytes']}
        row.update(changes)
        return row

    def test_the_real_map_defines_the_slot_under_a_conditional_parent(self):
        parent, part = ms.reserve_slot('modern-accuracy.code')
        self.assertEqual((parent, part['start'], part['bytes'], part['kind']), ('field-guide.code', 0x023D5AA0, 32, 'payload'))
        for unknown in ('typo.slot', 'field-guide.code.preserved', 'fieldbook.guard'):
            with self.subTest(slot=unknown), self.assertRaisesRegex(ms.CompositionError, 'reserve map'):
                ms.reserve_slot(unknown)

    def test_without_a_row_run_stage_refuses_with_the_unproven_condition_before_reading_the_rom(self):
        for allocation in (None, [], [self.row(name='training.ui')]):
            with self.subTest(allocation=allocation), self.assertRaisesRegex(
                    ms.CompositionError, r'reserve condition not proven: field-guide\.code'):
                ms.run_stage('slotty', bytes(64), 'EN', registry={'slotty': self.slot_stage()}, allocation=allocation)

    def test_the_real_abilities_stage_refuses_the_same_way(self):
        with self.assertRaisesRegex(ms.CompositionError, r'reserve condition not proven: field-guide\.code'):
            ms.run_stage('abilities', bytes(64), 'EN')

    def test_the_assigned_row_must_be_the_map_assignment_exactly(self):
        stage = self.slot_stage()
        self.assertEqual(ms.assigned_row(stage, [self.row()])['start'], 0x023D5AA0)
        for label, change in (('start', dict(start=0x023D5AA4)), ('capacity', dict(capacity=64)),
                              ('capacity smaller', dict(capacity=28)), ('name', dict(name='other')),
                              ('bytes above capacity', dict(bytes=33)), ('bytes zero', dict(bytes=0)),
                              ('bool bytes', dict(bytes=True))):
            with self.subTest(case=label), self.assertRaises(ms.CompositionError):
                ms.assigned_row(stage, [self.row(**change)])
        with self.assertRaises(ms.CompositionError):
            ms.assigned_row(stage, [self.row(), self.row()])
        with self.assertRaises(ms.CompositionError):
            ms.assigned_row(stage, 'not a list')

    def test_the_payload_requested_from_allocate_must_fit_the_row(self):
        with self.assertRaisesRegex(ms.CompositionError, 'payload'):
            ms.assigned_row(self.slot_stage(payload=28), [self.row(bytes=16)])

    def test_the_production_path_asks_reserve_allocate_and_wraps_its_refusal(self):
        from unittest.mock import patch
        from . import reserve
        refusal = ValueError('conditional payload requires a separately reviewed final installer verifier: modern-accuracy.code')
        with patch.object(reserve, 'allocate', side_effect=refusal) as allocate:
            with self.assertRaisesRegex(ms.CompositionError,
                                        r'reserve condition not proven: field-guide\.code.*separately reviewed') as caught:
                ms.resolve_allocation(b'V4', ['moves', 'ai', 'abilities'])
        allocate.assert_called_once_with(b'V4', {'fairy-ai.code': 148,
                                                  'modern-accuracy.code': 28})
        self.assertIs(caught.exception.__cause__, refusal)
        for error in (KeyError('k'), TypeError('t'), struct.error('s')):          # fail-closed for foreign exceptions too
            with patch.object(reserve, 'allocate', side_effect=error), self.assertRaises(ms.CompositionError):
                ms.resolve_allocation(b'V4', ['abilities'])

    def test_allocator_receipt_is_preserved_in_full_instead_of_reduced_to_rows(self):
        from . import reserve
        # Synthetic dispatch seam, not a production allocation/proof.
        fairy = {'name': 'fairy-ai.code', 'parent': 'training.extension',
                 'start': 0x023D746C, 'bytes': 148, 'capacity': 148}
        fresh = {'assignments': [fairy, self.row()],
                 'requested': {'fairy-ai.code': 148, 'modern-accuracy.code': 28},
                 'schema': 2}
        with patch.object(reserve, 'allocate', return_value=fresh):
            allocation, origin = ms.resolve_allocation(b'V4', ['moves', 'ai', 'abilities'])
        self.assertIs(allocation, fresh)
        self.assertEqual(origin, 'reserve.allocate')

    def test_supplied_full_receipt_is_freshly_reissued_against_exact_cold_ui_context(self):
        from . import reserve
        # These small dictionaries are deliberately synthetic boundary values.
        fresh = {'assignments': [self.row()], 'requested': {'modern-accuracy.code': 28}, 'schema': 2}
        context = dict(installed_ui=b'cold UI', charmap=Path('map'), work_dir=Path('work'),
                       archive_deltas=('archive plan',), overlay_deltas=('overlay plan',))
        with patch.object(reserve, 'allocate', return_value=fresh) as allocate:
            actual, origin = ms.resolve_allocation(b'V4', ['abilities'], dict(fresh), **context)
        self.assertIs(actual, fresh)
        self.assertEqual(origin, 'reserve.allocate-rederived')
        allocate.assert_called_once_with(b'V4', fresh['requested'], **context)
        with patch.object(reserve, 'allocate', return_value=fresh), self.assertRaisesRegex(
                ms.CompositionError, 'differs from the freshly reissued'):
            ms.resolve_allocation(b'V4', ['abilities'], dict(fresh, schema=1), **context)

    def test_a_caller_supplied_allocation_is_labelled_and_never_calls_allocate(self):
        from unittest.mock import patch
        from . import reserve
        rows = [self.row()]
        with patch.object(reserve, 'allocate', side_effect=AssertionError('production path used')):
            self.assertEqual(ms.resolve_allocation(b'V4', ['abilities'], rows), (rows, 'caller-supplied'))

    def test_stages_without_a_slot_never_touch_the_reserve_and_reject_a_useless_allocation(self):
        from unittest.mock import patch
        from . import reserve
        with patch.object(reserve, 'allocate', side_effect=AssertionError('must not be called')):
            self.assertEqual(ms.resolve_allocation(b'V4', ['moves', 'ai-immunities']), (None, None))
            with self.assertRaisesRegex(ValueError, 'no stage'):
                ms.resolve_allocation(b'V4', ['moves', 'ai-immunities'], [self.row()])

    def test_archive_producers_are_derived_from_the_registry(self):
        self.assertEqual(ms.required_producers(['moves', 'ai']), ())
        self.assertEqual(ms.required_producers(['moves', 'ai', 'abilities']), ('keen-eye-text',))
        extra = {'abilities': ms.REGISTRY['abilities'], 'x': ms.MechanicalStage('x', None, None, None, archive_producers=('b', 'keen-eye-text'))}
        self.assertEqual(ms.required_producers(['abilities', 'x'], extra), ('b', 'keen-eye-text'))



# Frozen pre-change reference for small synthetic compatibility checks.
_LEGACY_SOURCE = r'''
def _legacy_intermediate_images(before, final, stages, declared):
    """The n+1 images of a chain: the UI image, the output of each stage, `final`; rebuilt from `final` alone.

    Going backwards, a stage that can peel is taken out of its output; any other stage has its declared regions restored from
    the pristine input. The bottom must then be exactly `final` with every declared region restored, so a peel can neither
    leave bytes behind nor touch what is not declared.
    """
    check_sharing(stages, declared)
    overrides = {}
    by_stage = []
    for stage, regions in zip(stages, declared):
        callback = getattr(stage, 'cold_preimages', None)
        local = guarded(stage.name + ' cold preimages', callback, before, final, regions) if callback else {}
        if (type(local) is not dict or any(key not in {_span(r) for r in regions}
                or type(value) is not bytes or len(value) != key[1] - key[0]
                for key, value in local.items())):
            _fail('invalid fixed cold preimages for ' + stage.name)
        for key, value in local.items():
            if key in overrides and overrides[key] != value:
                _fail('inconsistent fixed cold preimages')
            overrides[key] = value
        by_stage.append(local)
    images = [None] * len(stages) + [final]
    for index in range(len(stages), 0, -1):
        stage, regions = stages[index - 1], declared[index - 1]
        peel = getattr(stage, 'peel', None)
        if peel is None:
            images[index - 1] = _restore(images[index], before, regions, by_stage[index-1])
            continue
        peeled = guarded(stage.name + ' peel', peel, images[index], before, regions)
        if type(peeled) is not bytes or len(peeled) != len(final):
            _fail('%s peel returned a mutable, non-bytes or resized ROM' % stage.name)
        images[index - 1] = peeled
    if images[0] != _restore(final, before, [r for regions in declared for r in regions], overrides):
        _fail('the chain does not peel back to the cold UI: a stage left bytes behind or touched undeclared ones')
    return images



def _legacy_verify_chain(before, final, names, receipts, verify_ui, *, invariants=None, registry=None,
                 allocation=None, charmap=None, stage_options=None, overlay_deltas=()):
    """Independent admission of `final` = UI(before) + the named mechanical stages, in order.

    `verify_ui(ui_image)` must be the existing independent UI verifier (it raises on any byte
    outside the UI policy); it receives the image rebuilt by restoring every declared region
    from `before`, so a stage can only have touched what it declared. Every external reader is
    fail-closed: an unexpected exception type is a refusal, never a crash or a pass.
    """
    caller_invariants = invariants
    names = list(names)
    if len(set(names)) != len(names):
        raise ValueError('duplicate mechanical stage')
    stages = [require_stage(n, registry) for n in names]
    if any(getattr(stage, 'archive_only', False) for stage in stages):
        _fail('an archive-only stage has no post-UI writer to replay: pass mechanics_stages.writers(names)')
    if not isinstance(receipts, list) or len(receipts) != len(stages):
        _fail('mechanics receipt count %s does not match %d stages'
              % (len(receipts) if isinstance(receipts, list) else '?', len(stages)))
    from . import baseline
    try:
        expected_language = baseline.identify(before)
    except ValueError:
        expected_language = None  # synthetic unit fixtures have no cartridge identity
    for receipt, name in zip(receipts, names):
        validate_receipt(receipt, name, expected_language)
    for stage in stages:
        if getattr(stage, 'contextual', False) and not isinstance(allocation, dict):
            _fail('%s requires the full reserve allocation receipt' % stage.name)
        if getattr(stage, 'slot_payload', 0) > 0:
            assigned_row(stage, allocation)       # an unproven reserve condition is refused before any ROM work
    declared = [list(guarded(stage.name + ' declaration', stage.regions, final if getattr(stage, 'regions_from_final', False) else before)) for stage in stages]
    for stage, regions in zip(stages, declared):
        _check_regions(regions, len(final) if getattr(stage, 'regions_from_final', False) else len(before))
    images = _legacy_intermediate_images(before, final, stages, declared)
    ui_image = images[0]
    ui_result = guarded('UI verifier', verify_ui, ui_image)
    previous, hashes = ui_image, []
    for index, (stage, regions, receipt) in enumerate(zip(stages, declared, receipts)):
        step = images[index + 1]
        if receipt['input_sha256'] != _sha(previous) or receipt['output_sha256'] != _sha(step):
            _fail('receipt for %s does not describe this step of the final ROM' % stage.name)
        if [dict(start=r.start, end=r.end, label=r.label) for r in regions] != receipt['regions']:
            _fail('receipt regions for %s differ from the stage declaration' % stage.name)
        if list(guarded(stage.name + ' declaration', stage.regions, previous)) != regions:
            _fail('%s declaration moved between the input and the intermediate image' % stage.name)
        if step == previous:
            _fail('%s left its declared region unchanged' % stage.name)
        if receipt['changed_ranges'] != [list(pair) for pair in changed_ranges(previous, step)]:
            _fail('receipt changed_ranges for %s differ from the bytes actually changed' % stage.name)
        policy = (getattr(stage, 'invariants', None) or check_ui_invariants) if caller_invariants is None else caller_invariants
        _run_invariants(policy, previous, step, regions, _grants(stage, previous, allocation))
        check_confined(previous, step, regions, stage.name)
        raw = receipt['stage_receipt']
        if getattr(stage, 'contextual', False):
            if raw.get('allocation') != allocation:
                _fail('%s owner receipt allocation differs from the granted receipt' % stage.name)
            verify_kwargs = {'charmap': charmap, 'stage_options': stage_options}
            if stage.name == 'rematches':
                verify_kwargs['overlay_deltas'] = overlay_deltas
            guarded(stage.name + ' reader', lambda a, b, r: stage.verify(a, b, r, **verify_kwargs), previous, step, raw)
        else:
            guarded(stage.name + ' reader', stage.verify, previous, step, raw)
        hashes.append(receipt['stage_receipt_sha256'])
        previous = step
    if previous != final:
        _fail('final ROM differs from the chain reconstruction outside the declared regions')
    return {'stages': names, 'ui': ui_result, 'stage_receipt_sha256': hashes,
            'ui_image_sha256': _sha(ui_image), 'output_sha256': _sha(final)}

'''
_legacy_namespace = dict(ms.__dict__)
exec(_LEGACY_SOURCE, _legacy_namespace)
legacy_images = _legacy_namespace["_legacy_intermediate_images"]
legacy_verify = _legacy_namespace["_legacy_verify_chain"]


class BoundedChain(unittest.TestCase):
    def test_reference_and_compatibility_for_disjoint_shared_empty_and_single(self):
        for registry, names in ((REGISTRY, []), (REGISTRY, ['one']),
                                (REGISTRY, ['one', 'two']),
                                (shared_registry(), ['one', 'two'])):
            data, receipts = BEFORE, []
            for name in names:
                data, receipt = ms.run_stage(name, data, 'EN', invariants=no_structure, registry=registry)
                receipts.append(receipt)
            stages = [registry[n] for n in names]
            declared = [list(stage.regions(BEFORE)) for stage in stages]
            expected = legacy_images(BEFORE, data, stages, declared)
            self.assertEqual(ms.intermediate_images(BEFORE, data, stages, declared), expected)
            self.assertEqual(ms.cold_ui_image(BEFORE, data, stages, declared), expected[0])
            ui = lambda image: {'hash': sha(image)}
            old = legacy_verify(BEFORE, data, names, receipts, ui, invariants=no_structure, registry=registry)
            with patch.object(ms, 'intermediate_images', side_effect=AssertionError('list allocation')):
                actual = ms.verify_chain(BEFORE, data, names, receipts, ui, invariants=no_structure, registry=registry)
                self.assertEqual(ms.cold_ui_image(BEFORE, data, stages, declared), expected[0])
            self.assertEqual(actual, old)

    def test_appended_fixed_preimages_match_reference(self):
        before, final = bytes(8), bytes(8) + b'XY'
        stage = FakeStage('append', 8, 10, 88)
        stage.regions_from_final = True
        stage.cold_preimages = lambda b, f, r: {(8, 10): b'AB'}
        regions = [stage.regions(final)]
        self.assertEqual(ms.intermediate_images(before, final, [stage], regions),
                         legacy_images(before, final, [stage], regions))
        self.assertEqual(ms.cold_ui_image(before, final, [stage], regions), before + b'AB')
        cold = before + b'AB'
        receipt = ms._wrap('append', 'EN', cold, final, regions[0],
                           {'offset': 8, 'value': 88})
        args = (before, final, ['append'], [receipt], lambda x: {'hash': sha(x)})
        self.assertEqual(ms.verify_chain(*args, invariants=no_structure, registry={'append': stage}),
                         legacy_verify(*args, invariants=no_structure, registry={'append': stage}))

    def test_both_passes_enforce_global_bottom(self):
        final, receipts = chain(['one', 'two'])
        original = ms._restore; global_checks = []
        def restore(rom, before, regions, overrides=None):
            if len(regions) == 2: global_checks.append(1)
            return original(rom, before, regions, overrides)
        with patch.object(ms, '_restore', side_effect=restore):
            ms.verify_chain(BEFORE, final, ['one', 'two'], receipts, lambda x: {},
                            invariants=no_structure, registry=REGISTRY)
        self.assertEqual(len(global_checks), 2)

    def test_nonrepeatable_peel_is_refused_before_readers(self):
        registry = shared_registry(); final, receipts = SharedRegions().run_chain(registry)
        good = registry['two'].peel; calls = []
        def changing(after, before, regions):
            calls.append(1); image = bytearray(good(after, before, regions))
            if len(calls) == 2: image[10] ^= 1
            return bytes(image)
        registry['two'].peel = changing
        with self.assertRaisesRegex(ms.CompositionError, 'boundary|reconstruction'):
            ms.verify_chain(BEFORE, final, ['one', 'two'], receipts, lambda x: {},
                            invariants=no_structure, registry=registry)
        self.assertEqual(len(calls), 2)

    def test_ui_gate_and_reverse_reader_order(self):
        registry = shared_registry(); final, receipts = SharedRegions().run_chain(registry)
        events = []
        for name in ('one', 'two'):
            stage = registry[name]; original = stage.verify
            def reader(a, b, r, name=name, original=original):
                events.append('reader-' + name); return original(a, b, r)
            stage.verify = reader
        original_peel = registry['two'].peel
        def peel(a, b, r):
            events.append('peel'); return original_peel(a, b, r)
        registry['two'].peel = peel
        def ui(image): events.append('ui'); return {}
        ms.verify_chain(BEFORE, final, ['one', 'two'], receipts, ui,
                        invariants=no_structure, registry=registry)
        self.assertEqual(events, ['peel', 'ui', 'peel', 'reader-two', 'reader-one'])
        events.clear()
        def bad_ui(image): events.append('ui'); raise ValueError('refuse UI')
        with self.assertRaisesRegex(ValueError, 'refuse UI'):
            ms.verify_chain(BEFORE, final, ['one', 'two'], receipts, bad_ui,
                            invariants=no_structure, registry=registry)
        self.assertEqual(events, ['peel', 'ui'])

    def test_fixed_plan_is_once_and_global_bottom_precedes_ui(self):
        registry = shared_registry(); final, receipts = SharedRegions().run_chain(registry)
        events = []
        for name in ('one', 'two'):
            stage = registry[name]
            def cold(b, f, r, name=name): events.append('cold-' + name); return {}
            stage.cold_preimages = cold
            stage.apply = lambda *args: (_ for _ in ()).throw(AssertionError('writer called'))
        original = registry['two'].peel
        def peel(a, b, r): events.append('peel'); return original(a, b, r)
        registry['two'].peel = peel
        def ui(image): events.append('ui'); return {}
        ms.verify_chain(BEFORE, final, ['one', 'two'], receipts, ui,
                        invariants=no_structure, registry=registry)
        self.assertEqual(events, ['cold-one', 'cold-two', 'peel', 'ui', 'peel'])
        events.clear()
        def corrupt(a, b, r):
            out = bytearray(original(a, b, r)); out[50] = 1; return bytes(out)
        registry['two'].peel = corrupt
        with self.assertRaises(ms.CompositionError):
            ms.verify_chain(BEFORE, final, ['one', 'two'], receipts, ui,
                            invariants=no_structure, registry=registry)
        self.assertNotIn('ui', events)

    def test_single_invalid_inputs_fail_in_reference_and_bounded(self):
        import copy
        for case in ('receipt-hash', 'changed-ranges', 'reader', 'invariant',
                     'ui', 'sharing', 'peel', 'preimages'):
            for verifier in (legacy_verify, ms.verify_chain):
                with self.subTest(case=case, verifier=verifier.__name__):
                    registry = shared_registry(); final, receipts = SharedRegions().run_chain(registry)
                    receipts = copy.deepcopy(receipts); ui = lambda x: {}; invariant = no_structure
                    if case == 'receipt-hash': receipts[1]['input_sha256'] = 'f' * 64
                    if case == 'changed-ranges': receipts[1]['changed_ranges'] = [[0, 1]]
                    if case == 'reader': registry['two'].verify = lambda *a: (_ for _ in ()).throw(ValueError('reader'))
                    if case == 'invariant': invariant = lambda *a: (_ for _ in ()).throw(ValueError('invariant'))
                    if case == 'ui': ui = lambda x: (_ for _ in ()).throw(ValueError('ui'))
                    if case == 'sharing': registry['two'].peel = None
                    if case == 'peel': registry['two'].peel = lambda *a: bytearray(100)
                    if case == 'preimages': registry['one'].cold_preimages = lambda *a: {(10, 20): b'x'}
                    with self.assertRaises(ValueError):
                        verifier(BEFORE, final, ['one', 'two'], receipts, ui,
                                 invariants=invariant, registry=registry)

    def test_bounded_peak_against_legacy_image_retention(self):
        import tracemalloc
        size = 256 * 1024
        def fixture(count):
            before = bytes(size); data = before; registry = {}; receipts = []
            for i in range(count):
                name = 's%d' % i; registry[name] = FakeStage(name, i, i + 1, 1)
                data, receipt = ms.run_stage(name, data, 'EN', invariants=no_structure, registry=registry)
                receipts.append(receipt)
            return before, data, list(registry), receipts, registry
        short, long = fixture(3), fixture(24)
        def peak(fn, fixture):
            before, final, names, receipts, registry = fixture
            tracemalloc.start()
            try:
                fn(before, final, names, receipts, lambda x: {}, invariants=no_structure, registry=registry)
                return tracemalloc.get_traced_memory()[1]
            finally: tracemalloc.stop()
        small = peak(ms.verify_chain, short)
        new = peak(ms.verify_chain, long)
        old = peak(legacy_verify, long)
        print("\ntracemalloc peak bytes: short=%d bounded=%d legacy=%d" % (small, new, old))
        self.assertLess(new, old * 0.7, (small, new, old))
        self.assertLess(new, small + size * 4, (small, new, old))

if __name__ == '__main__':
    unittest.main()
