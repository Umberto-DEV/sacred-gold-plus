"""Class A: guarded post-KO scoring patch on a synthetic overlay image.

No game data beyond the 20 guard bytes (ten Thumb instructions around the
conversion) is embedded: the rest of the 0x37380-byte image is authored
filler. Real bytes, the real function and the type helper are exercised by
test_ai_scoring_rom. Expected bytes are written out here, independently of the
module under test.
"""
import hashlib
import struct
import unittest

from . import ai_scoring as ai

BASE = 0x022378C0
SIZE = 0x37380
FUNCTION = (0x02258800, 0x02258BA0)
EFFECTIVENESS_FUNCTION = (0x02252054, 0x02252218)
CONTEXT_ADDRESS = 0x02258934
EFFECTIVENESS_CONTEXT_ADDRESS = 0x022521F8
# ldr r1,[sp,#0x4c]; adds r0,r1,r0; lsls r0,#24; lsrs r0,#24; str r0,[sp,#0x4c];
# ldr r1,[sp,#0x48]; cmp r1,r0; bhs; ldr r0,[sp,#0x4c]; str r0,[sp,#0x48]
CONTEXT = bytes.fromhex('1399 0818 0006 000e 1390 1299 8142 0dd2 1398 1290'.replace(' ', ''))
# lsls r1,r0,#24; lsrs r1,r1,#24; str r1,[sp,#0x4c]   |   nop in place of the reload
SITES = ((0x02258938, bytes.fromhex('0006000e1390'), bytes.fromhex('0106090e1391')),
         (0x02258944, bytes.fromhex('1398'), bytes.fromhex('c046')))
EFFECTIVENESS_CONTEXT = bytes.fromhex(
    '04201043086070470a680420104203d0042082430a6070470220104308607047')
EFFECTIVENESS_SITE = (0x02252202, bytes.fromhex('0420'), bytes.fromhex('0c20'))
CHANGED = [0x02252202, 0x02258938, 0x0225893A, 0x0225893D, 0x02258944, 0x02258945]
OLD_TWO_NOP = bytes.fromhex('c046c046')  # the superseded fix: it widened the stored stage-two word too


def digest(data):
    return hashlib.sha256(data).hexdigest()


def synthetic():
    """Image with authored filler; only the guard window holds game bytes."""
    image = bytearray((index * 37 + 11) & 0xFF for index in range(SIZE))
    window = CONTEXT_ADDRESS - BASE
    image[window:window + len(CONTEXT)] = CONTEXT
    window = EFFECTIVENESS_CONTEXT_ADDRESS - BASE
    image[window:window + len(EFFECTIVENESS_CONTEXT)] = EFFECTIVENESS_CONTEXT
    return bytes(image)


def pin(image):
    return digest(image[FUNCTION[0] - BASE:FUNCTION[1] - BASE])


def pin_effectiveness(image):
    return digest(image[EFFECTIVENESS_FUNCTION[0] - BASE:EFFECTIVENESS_FUNCTION[1] - BASE])


def expected_after(image):
    result = bytearray(image)
    for address, _, post in SITES:
        result[address - BASE:address - BASE + len(post)] = post
    address, _, post = EFFECTIVENESS_SITE
    result[address - BASE:address - BASE + len(post)] = post
    return bytes(result)


def with_site(image, address, value):
    result = bytearray(image)
    result[address - BASE:address - BASE + len(value)] = value
    return bytes(result)


class PatchOverlayTests(unittest.TestCase):
    def test_constants_describe_the_declared_delta(self):
        self.assertEqual(getattr(ai, 'PATCHES', None), SITES)
        self.assertEqual(getattr(ai, 'CONTEXT', None), CONTEXT)
        self.assertEqual(getattr(ai, 'CONTEXT_ADDRESS', None), CONTEXT_ADDRESS)
        self.assertEqual((ai.FUNCTION_START, ai.FUNCTION_END), FUNCTION)
        self.assertEqual(ai.FUNCTION_SHA256, '45b8c7da8e9c25d38616d0524c824098182e48d807fde80da59a4e082569da84')
        self.assertEqual(ai.EFFECTIVENESS_FUNCTION_SHA256,
                         'eb5c3828aa198508aa0644dcf61bad54cf2022dab25923d62e8622a840e952a5')
        self.assertEqual(ai.EFFECTIVENESS_CONTEXT, EFFECTIVENESS_CONTEXT)
        self.assertEqual(ai.EFFECTIVENESS_PATCHES, (EFFECTIVENESS_SITE,))
        self.assertEqual(sum(len(post) for _, _, post in SITES), 8)

    def test_exactly_the_five_instructions_change(self):
        image = synthetic()
        patched, info = ai.patch_overlay(
            image, function_sha256=pin(image),
            effectiveness_function_sha256=pin_effectiveness(image))
        self.assertEqual(patched, expected_after(image))
        self.assertEqual(len(patched), len(image))
        differing = [BASE + i for i in range(len(image)) if image[i] != patched[i]]
        self.assertEqual(differing, CHANGED)
        self.assertEqual(info['changed_offsets'], [a - BASE for a in CHANGED])
        all_sites = (*SITES, EFFECTIVENESS_SITE)
        self.assertEqual(info['sites'], [{'address': a, 'preimage': pre.hex(), 'replacement': post.hex()} for a, pre, post in all_sites])
        self.assertEqual(info['overlay_sha256_before'], digest(image))
        self.assertEqual(info['overlay_sha256_after'], digest(patched))

    def test_wrong_preimage_is_refused_at_every_guard_byte(self):
        image = synthetic()
        pinned = pin(image)
        effectiveness_pinned = pin_effectiveness(image)
        for delta in range(len(CONTEXT)):
            broken = bytearray(image)
            broken[CONTEXT_ADDRESS - BASE + delta] ^= 0x01
            with self.assertRaisesRegex(ValueError, 'preimage', msg='guard byte %d' % delta):
                ai.patch_overlay(bytes(broken), function_sha256=pinned,
                                 effectiveness_function_sha256=effectiveness_pinned)

    def test_changed_extra_byte_inside_the_pinned_function_is_refused(self):
        image = synthetic()
        pinned = pin(image)
        effectiveness_pinned = pin_effectiveness(image)
        for address in (FUNCTION[0] + 3, CONTEXT_ADDRESS - 2, CONTEXT_ADDRESS + len(CONTEXT), FUNCTION[1] - 1):
            broken = bytearray(image)
            broken[address - BASE] ^= 0xFF
            with self.assertRaisesRegex(ValueError, 'function'):
                ai.patch_overlay(bytes(broken), function_sha256=pinned,
                                 effectiveness_function_sha256=effectiveness_pinned)

    def test_effectiveness_guard_and_function_pin_fail_closed(self):
        image = synthetic()
        for delta in range(len(EFFECTIVENESS_CONTEXT)):
            broken = bytearray(image)
            broken[EFFECTIVENESS_CONTEXT_ADDRESS - BASE + delta] ^= 1
            with self.assertRaisesRegex(ValueError, 'effectiveness preimage'):
                ai.patch_overlay(
                    bytes(broken), function_sha256=pin(image),
                    effectiveness_function_sha256=pin_effectiveness(image))
        broken = bytearray(image)
        broken[EFFECTIVENESS_FUNCTION[0] - BASE + 3] ^= 1
        with self.assertRaisesRegex(ValueError, 'function'):
            ai.patch_overlay(
                bytes(broken), function_sha256=pin(image),
                effectiveness_function_sha256=pin_effectiveness(image))

    def test_bytes_outside_the_function_do_not_belong_to_the_guard(self):
        """Other stages edit the same overlay: only the function is pinned."""
        image = bytearray(synthetic())
        pinned = pin(image)
        image[0x0224BD5C - BASE:0x0224BD62 - BASE] = bytes(range(1, 7))  # another stage's window
        image[0x02264A14 - BASE:0x02264A16 - BASE] = bytes.fromhex('c046')
        patched, _ = ai.patch_overlay(
            bytes(image), function_sha256=pinned,
            effectiveness_function_sha256=pin_effectiveness(bytes(image)))
        self.assertEqual(patched[0x0224BD5C - BASE:0x0224BD62 - BASE], bytes(range(1, 7)))
        self.assertEqual(patched[0x02264A14 - BASE:0x02264A16 - BASE], bytes.fromhex('c046'))
        self.assertEqual(patched, expected_after(bytes(image)))

    def test_repeat_is_refused_not_idempotent(self):
        image = synthetic()
        patched, _ = ai.patch_overlay(
            image, function_sha256=pin(image),
            effectiveness_function_sha256=pin_effectiveness(image))
        with self.assertRaises(ValueError):
            ai.patch_overlay(patched, function_sha256=pin(image),
                             effectiveness_function_sha256=pin_effectiveness(image))
        with self.assertRaises(ValueError):
            ai.patch_overlay(patched, function_sha256=pin(patched),
                             effectiveness_function_sha256=pin_effectiveness(patched))

    def test_wrong_image_size_or_type_is_refused(self):
        image = synthetic()
        with self.assertRaisesRegex(ValueError, 'size'):
            ai.patch_overlay(image[:-1], function_sha256=pin(image),
                             effectiveness_function_sha256=pin_effectiveness(image))
        with self.assertRaisesRegex(ValueError, 'size'):
            ai.patch_overlay(image + b'\0', function_sha256=pin(image),
                             effectiveness_function_sha256=pin_effectiveness(image))
        with self.assertRaises((TypeError, ValueError)):
            ai.patch_overlay('not bytes')

    def test_default_pin_refuses_a_synthetic_image(self):
        with self.assertRaisesRegex(ValueError, 'function'):
            ai.patch_overlay(synthetic())


class LogicalVerifierTests(unittest.TestCase):
    def setUp(self):
        self.before = synthetic()
        self.after = expected_after(self.before)

    def test_exact_delta_accepted(self):
        report = ai.verify_images(self.before, self.after)
        self.assertEqual(report['changed_offsets'], [a - BASE for a in CHANGED])
        self.assertEqual(report['changed_bytes'], 6)
        self.assertEqual(report['declared_window_bytes'], 10)

    def test_extra_changed_byte_refused(self):
        for address in (0x02252201, 0x02252204, 0x02258937, 0x0225893E,
                        0x02258943, 0x02258946, FUNCTION[0], FUNCTION[1],
                        BASE, BASE + SIZE - 1):
            damaged = bytearray(self.after)
            damaged[address - BASE] ^= 0x80
            with self.assertRaisesRegex(ValueError, 'logical|replacement', msg=hex(address)):
                ai.verify_images(self.before, bytes(damaged))

    def test_superseded_two_nop_fix_is_refused(self):
        old = with_site(self.before, 0x02258938, OLD_TWO_NOP)
        with self.assertRaises(ValueError):
            ai.verify_images(self.before, old)

    def test_each_instruction_left_original_is_refused(self):
        """lsls, lsrs, str and the nop each matter: one missing makes the readback fail."""
        for address, post in ((0x02258938, bytes.fromhex('0006')), (0x0225893A, bytes.fromhex('000e')),
                              (0x0225893C, bytes.fromhex('1390')), (0x02258944, bytes.fromhex('1398'))):
            damaged = with_site(self.after, address, post)
            with self.assertRaises(ValueError, msg=hex(address)):
                ai.verify_images(self.before, damaged)
        damaged = with_site(self.after, EFFECTIVENESS_SITE[0], EFFECTIVENESS_SITE[1])
        with self.assertRaises(ValueError):
            ai.verify_images(self.before, damaged)

    def test_wrong_preimage_or_size_refused(self):
        damaged = bytearray(self.before)
        damaged[0x02258938 - BASE] ^= 1
        with self.assertRaisesRegex(ValueError, 'preimage'):
            ai.verify_images(bytes(damaged), self.after)
        damaged = bytearray(self.before)
        damaged[0x02258944 - BASE] ^= 1
        with self.assertRaisesRegex(ValueError, 'preimage'):
            ai.verify_images(bytes(damaged), self.after)
        with self.assertRaisesRegex(ValueError, 'size'):
            ai.verify_images(self.before, self.after[:-1])
        with self.assertRaisesRegex(ValueError, 'size'):
            ai.verify_images(self.before[:-1], self.after[:-1])

    def test_unchanged_after_is_refused(self):
        with self.assertRaises(ValueError):
            ai.verify_images(self.before, self.before)


class ApplyArgumentTests(unittest.TestCase):
    def test_unknown_language_is_refused_before_touching_the_rom(self):
        for language in ('FR', 'en', '', None):
            with self.assertRaisesRegex(ValueError, 'language'):
                ai.apply(b'not a rom', language)

    def test_garbage_rom_is_refused(self):
        with self.assertRaises(Exception):
            ai.apply(b'not a rom', 'EN')


class DrySkinAIPatchTests(unittest.TestCase):
    """Regression: Basic AI must score Water into Dry Skin as an immunity."""

    BASE = 0x0221BE20
    SIZE = 0xF460
    CONTEXT_ADDRESS = 0x02220BC4
    SITE = 0x02220BD4
    CONTEXT = struct.pack('<13I', 19, 26, 34, 19, 26, 38,
                          76, 43, 30, 4, 34, 13, 2442)

    @classmethod
    def image(cls):
        data = bytearray((index * 29 + 7) & 0xFF for index in range(cls.SIZE))
        at = cls.CONTEXT_ADDRESS - cls.BASE
        data[at:at + len(cls.CONTEXT)] = cls.CONTEXT
        return bytes(data)

    def test_duplicate_levitate_word_becomes_dry_skin_and_nothing_else(self):
        self.assertTrue(hasattr(ai, 'patch_dry_skin_overlay'),
                        'production Dry Skin patch is missing')
        before = self.image()
        after, report = ai.patch_dry_skin_overlay(
            before, overlay_sha256=digest(before))
        expected = bytearray(before)
        expected[self.SITE - self.BASE:self.SITE - self.BASE + 4] = (87).to_bytes(4, 'little')
        self.assertEqual(after, bytes(expected))
        self.assertEqual(report['site'], self.SITE)
        self.assertEqual(report['ability_before'], 26)
        self.assertEqual(report['ability_after'], 87)
        self.assertEqual(report['changed_offsets'], [self.SITE - self.BASE])

    def test_archive_member_copy_receives_the_same_one_word_correction(self):
        self.assertTrue(hasattr(ai, 'patch_dry_skin_member'),
                        'production Dry Skin archive-member patch is missing')
        before = bytearray((index * 17 + 3) & 0xFF for index in range(42428))
        before[0x118:0x118 + len(self.CONTEXT)] = self.CONTEXT
        before = bytes(before)
        after, report = ai.patch_dry_skin_member(
            before, member_sha256=digest(before))
        expected = bytearray(before)
        expected[0x128:0x12C] = (87).to_bytes(4, 'little')
        self.assertEqual(after, bytes(expected))
        self.assertEqual(report['member_offset'], 0x128)
        self.assertEqual(report['ability_before'], 26)
        self.assertEqual(report['ability_after'], 87)
        self.assertEqual(report['changed_offsets'], [0x128])

    def test_both_copies_fail_closed_on_foreign_or_repeated_inputs(self):
        overlay = self.image()
        member = bytearray((index * 17 + 3) & 0xFF for index in range(42428))
        member[0x118:0x118 + len(self.CONTEXT)] = self.CONTEXT
        member = bytes(member)

        for before, patcher, pin_name in (
                (overlay, ai.patch_dry_skin_overlay, 'overlay_sha256'),
                (member, ai.patch_dry_skin_member, 'member_sha256')):
            with self.subTest(copy=pin_name):
                damaged = bytearray(before)
                damaged[(self.CONTEXT_ADDRESS - self.BASE) if pin_name == 'overlay_sha256' else 0x118] ^= 1
                with self.assertRaisesRegex(ValueError, 'context'):
                    patcher(bytes(damaged), **{pin_name: digest(bytes(damaged))})
                with self.assertRaisesRegex(ValueError, 'pinned'):
                    patcher(before, **{pin_name: '00' * 32})
                after, _ = patcher(before, **{pin_name: digest(before)})
                with self.assertRaises(ValueError):
                    patcher(after, **{pin_name: digest(after)})


class WaterSpoutAIPatchTests(unittest.TestCase):
    """AI-WEB-01: both HP checks must resolve the move user, not its target."""

    def test_only_the_two_battler_tokens_change_from_target_to_user(self):
        before = bytearray((index * 17 + 3) & 0xFF for index in range(42428))
        struct.pack_into('<25i', before, 0x6450,
                         43, 0, 19, 43, 10, 16, 43, 20, 13, 36, 1, 6,
                         6, 0, 50, 8, 76, 4, 6, 0, 70, 2, 4, -1, 77)
        before = bytes(before)
        after, report = ai.patch_water_spout_member(
            before, member_sha256=digest(before))
        expected = bytearray(before)
        struct.pack_into('<I', expected, 0x6484, 1)
        struct.pack_into('<I', expected, 0x649C, 1)
        self.assertEqual(after, bytes(expected))
        self.assertEqual(report['changed_offsets'], [0x6484, 0x649C])
        self.assertEqual(report['battler_before'], 0)
        self.assertEqual(report['battler_after'], 1)

    def test_context_pin_and_replay_fail_closed(self):
        before = bytearray((index * 11 + 5) & 0xFF for index in range(42428))
        struct.pack_into('<25i', before, 0x6450,
                         43, 0, 19, 43, 10, 16, 43, 20, 13, 36, 1, 6,
                         6, 0, 50, 8, 76, 4, 6, 0, 70, 2, 4, -1, 77)
        before = bytes(before)
        with self.assertRaisesRegex(ValueError, 'pinned'):
            ai.patch_water_spout_member(before, member_sha256='00' * 32)
        damaged = bytearray(before)
        damaged[0x6488] ^= 1
        with self.assertRaisesRegex(ValueError, 'context'):
            ai.patch_water_spout_member(bytes(damaged), member_sha256=digest(bytes(damaged)))
        after, _ = ai.patch_water_spout_member(before, member_sha256=digest(before))
        with self.assertRaises(ValueError):
            ai.patch_water_spout_member(after, member_sha256=digest(after))


class FacadeAIPatchTests(unittest.TestCase):
    """AI-WEB-03: Facade must inspect the move user, not its target."""

    CONTEXT = (10, 0, 0xD8, 2, 4, 1, 77)

    @classmethod
    def member(cls, multiplier=13, addend=7):
        before = bytearray((index * multiplier + addend) & 0xFF
                           for index in range(42428))
        struct.pack_into('<7i', before, 0x5B64, *cls.CONTEXT)
        return bytes(before)

    def test_only_the_facade_battler_token_changes_from_target_to_user(self):
        self.assertTrue(hasattr(ai, 'patch_facade_member'),
                        'production Facade AI patch is missing')
        before = self.member()
        after, report = ai.patch_facade_member(
            before, member_sha256=digest(before))
        expected = bytearray(before)
        struct.pack_into('<I', expected, 0x5B68, 1)
        self.assertEqual(after, bytes(expected))
        self.assertEqual(report['changed_offsets'], [0x5B68])
        self.assertEqual(report['battler_before'], 0)
        self.assertEqual(report['battler_after'], 1)

    def test_context_pin_mask_score_and_replay_fail_closed(self):
        before = self.member(19, 5)
        with self.assertRaisesRegex(ValueError, 'pinned'):
            ai.patch_facade_member(before, member_sha256='00' * 32)
        damaged = bytearray(before)
        damaged[0x5B70] ^= 1
        with self.assertRaisesRegex(ValueError, 'context'):
            ai.patch_facade_member(bytes(damaged),
                                   member_sha256=digest(bytes(damaged)))
        after, report = ai.patch_facade_member(
            before, member_sha256=digest(before))
        self.assertEqual(struct.unpack_from('<I', after, 0x5B6C)[0], 0xD8)
        self.assertEqual(struct.unpack_from('<i', after, 0x5B78)[0], 1)
        self.assertEqual(report['status_mask'], 0xD8)
        self.assertEqual(report['score_delta'], 1)
        with self.assertRaises(ValueError):
            ai.patch_facade_member(after, member_sha256=digest(after))


class ThunderDispatchPatchTests(unittest.TestCase):
    """AI-WEB-04: effect 152 must dispatch to Expert_Thunder."""

    DISPATCH = (47, 144, 2721, 47, 145, 2814, 47, 151, 2811,
                47, 151, 2855, 47, 155, 2878)
    ROUTINE = (43, 0, 17, 43, 20, 14, 43, 10, 11, 46, 19, 1, 7,
               20, 2, 9, 4, 1, 76, 5, 0, 50, 2, 4, -3)

    @classmethod
    def member(cls, multiplier=23, addend=3):
        before = bytearray((index * multiplier + addend) & 0xFF
                           for index in range(42428))
        struct.pack_into('<15i', before, 0x2BD8, *cls.DISPATCH)
        struct.pack_into('<25i', before, 0x58A4, *cls.ROUTINE)
        return bytes(before)

    def test_only_the_duplicate_solarbeam_effect_becomes_thunder(self):
        self.assertTrue(hasattr(ai, 'patch_thunder_member'),
                        'production Thunder dispatch patch is missing')
        before = self.member()
        after, report = ai.patch_thunder_member(
            before, member_sha256=digest(before))
        expected = bytearray(before)
        struct.pack_into('<I', expected, 0x2C00, 152)
        self.assertEqual(after, bytes(expected))
        self.assertEqual(report['changed_offsets'], [0x2C00])
        self.assertEqual((report['effect_before'], report['effect_after']),
                         (151, 152))

    def test_context_routine_pin_and_replay_fail_closed(self):
        before = self.member(29, 11)
        with self.assertRaisesRegex(ValueError, 'pinned'):
            ai.patch_thunder_member(before, member_sha256='00' * 32)
        for offset, message in ((0x2BE0, 'dispatch'), (0x58B0, 'routine')):
            damaged = bytearray(before)
            damaged[offset] ^= 1
            with self.subTest(offset=offset), self.assertRaisesRegex(
                    ValueError, message):
                ai.patch_thunder_member(
                    bytes(damaged), member_sha256=digest(bytes(damaged)))
        after, _ = ai.patch_thunder_member(
            before, member_sha256=digest(before))
        with self.assertRaises(ValueError):
            ai.patch_thunder_member(after, member_sha256=digest(after))


class MetalBurstPatchTests(unittest.TestCase):
    """AI-WEB-02: partial item/Stall shortcuts must not override real order."""

    ROUTINE = (43, 0, 607, 41, 0, 19, 100, 602, 85, 0, 107, 598,
               41, 1, 19, 100, 7, 85, 1, 107, 3, 36, 0, 586, 77)
    SITES = (0x1DFC, 0x1E0C, 0x1E20, 0x1E30)

    @classmethod
    def member(cls, multiplier=31, addend=7):
        before = bytearray((index * multiplier + addend) & 0xFF
                           for index in range(42428))
        struct.pack_into('<25i', before, 0x1DE0, *cls.ROUTINE)
        return bytes(before)

    def test_partial_shortcuts_are_disabled_so_order_is_authoritative(self):
        self.assertTrue(hasattr(ai, 'patch_metal_burst_member'),
                        'production Metal Burst AI patch is missing')
        before = self.member()
        after, report = ai.patch_metal_burst_member(
            before, member_sha256=digest(before))
        expected = bytearray(before)
        for site in self.SITES:
            struct.pack_into('<I', expected, site, 0)
        self.assertEqual(after, bytes(expected))
        self.assertEqual(report['ability'], 100)
        self.assertEqual(report['item_id'], 107)
        self.assertEqual(report['jump_before'], [602, 598, 7, 3])
        self.assertEqual(report['jump_after'], [0, 0, 0, 0])
        self.assertEqual(report['changed_offsets'],
                         [0x1DFC, 0x1DFD, 0x1E0C, 0x1E0D,
                          0x1E20, 0x1E30])

    def test_context_pin_and_replay_fail_closed(self):
        self.assertTrue(hasattr(ai, 'patch_metal_burst_member'),
                        'production Metal Burst AI patch is missing')
        before = self.member(37, 9)
        with self.assertRaisesRegex(ValueError, 'pinned'):
            ai.patch_metal_burst_member(before, member_sha256='00' * 32)
        damaged = bytearray(before)
        damaged[0x1DF8] ^= 1
        with self.assertRaisesRegex(ValueError, 'context'):
            ai.patch_metal_burst_member(
                bytes(damaged), member_sha256=digest(bytes(damaged)))
        after, _ = ai.patch_metal_burst_member(
            before, member_sha256=digest(before))
        with self.assertRaises(ValueError):
            ai.patch_metal_burst_member(after, member_sha256=digest(after))


class ArenaTrapSwitchGatePatchTests(unittest.TestCase):
    """HG-B14: the AI must use the engine's complete switch contract."""

    BASE = 0x0221BE20
    SIZE = 0xF460
    FUNCTION = (0x022203A4, 0x022205BC)
    SITE = 0x022203B4
    PREIMAGE = bytes.fromhex('7c4a7d4bac58019002911c4230d11032')
    REPLACEMENT = bytes.fromhex('01900291321c35f0b1fa002830d132e0')

    @classmethod
    def image(cls):
        data = bytearray((index * 31 + 9) & 0xFF for index in range(cls.SIZE))
        at = cls.SITE - cls.BASE
        data[at:at + len(cls.PREIMAGE)] = cls.PREIMAGE
        return bytes(data)

    def test_partial_trap_checks_become_one_authoritative_switch_gate(self):
        self.assertTrue(hasattr(ai, 'patch_arena_switch_overlay'),
                        'production Arena Trap switch-gate patch is missing')
        before = self.image()
        function_pin = digest(before[self.FUNCTION[0] - self.BASE:
                                     self.FUNCTION[1] - self.BASE])
        after, report = ai.patch_arena_switch_overlay(
            before, function_sha256=function_pin)
        expected = bytearray(before)
        expected[self.SITE - self.BASE:self.SITE - self.BASE + len(self.REPLACEMENT)] = \
            self.REPLACEMENT
        self.assertEqual(after, bytes(expected))
        self.assertEqual(report['site'], self.SITE)
        self.assertEqual(report['target'], 0x02255920)
        self.assertEqual(report['changed_offsets'], [
            self.SITE - self.BASE + index
            for index, (old, new) in enumerate(zip(self.PREIMAGE, self.REPLACEMENT))
            if old != new])

    def test_switch_gate_fails_closed_on_context_function_and_repeat(self):
        before = self.image()
        function_pin = digest(before[self.FUNCTION[0] - self.BASE:
                                     self.FUNCTION[1] - self.BASE])
        damaged = bytearray(before)
        damaged[self.SITE - self.BASE] ^= 1
        with self.assertRaisesRegex(ValueError, 'context'):
            ai.patch_arena_switch_overlay(bytes(damaged),
                                          function_sha256=digest(bytes(damaged)[
                                              self.FUNCTION[0] - self.BASE:
                                              self.FUNCTION[1] - self.BASE]))
        damaged = bytearray(before)
        damaged[self.FUNCTION[1] - self.BASE - 1] ^= 1
        with self.assertRaisesRegex(ValueError, 'function'):
            ai.patch_arena_switch_overlay(bytes(damaged), function_sha256=function_pin)
        after, _ = ai.patch_arena_switch_overlay(before, function_sha256=function_pin)
        with self.assertRaises(ValueError):
            ai.patch_arena_switch_overlay(
                after, function_sha256=digest(after[self.FUNCTION[0] - self.BASE:
                                                     self.FUNCTION[1] - self.BASE]))


class AbsorbSwitchPatchTests(unittest.TestCase):
    """HG-B15: preserve old absorbers and admit Dry Skin/Motor Drive."""

    BASE = 0x0221BE20
    SIZE = 0xF460
    FUNCTION = (0x0221FE8C, 0x02220010)
    ACTIVE_SITE = 0x0221FF10
    ACTIVE_PREIMAGE = bytes.fromhex('0499814202d1')
    ACTIVE_REPLACEMENT = bytes.fromhex('0bf0acf902d1')
    PARTY_SITE = 0x0221FFC6
    PARTY_PREIMAGE = bytes.fromhex('0006010e049888420dd1')
    PARTY_REPLACEMENT = bytes.fromhex('0bf051f90fd1c046c046')
    HELPER_ADDRESS = 0x0222B26C
    HELPER = bytes.fromhex('0499884205d00c2903d8401ac9000c3988427047')

    @classmethod
    def image(cls):
        data = bytearray((index * 23 + 5) & 0xFF for index in range(cls.SIZE))
        data[cls.ACTIVE_SITE - cls.BASE:cls.ACTIVE_SITE - cls.BASE + len(cls.ACTIVE_PREIMAGE)] = \
            cls.ACTIVE_PREIMAGE
        data[cls.PARTY_SITE - cls.BASE:cls.PARTY_SITE - cls.BASE + len(cls.PARTY_PREIMAGE)] = \
            cls.PARTY_PREIMAGE
        data[cls.HELPER_ADDRESS - cls.BASE:cls.HELPER_ADDRESS - cls.BASE + len(cls.HELPER)] = \
            bytes(len(cls.HELPER))
        return bytes(data)

    def test_both_comparisons_redirect_to_exact_safe_tail_helper(self):
        self.assertTrue(hasattr(ai, 'patch_absorb_switch_overlay'),
                        'production absorb-switch patch is missing')
        before = self.image()
        function_pin = digest(before[self.FUNCTION[0] - self.BASE:
                                     self.FUNCTION[1] - self.BASE])
        after, report = ai.patch_absorb_switch_overlay(
            before, function_sha256=function_pin)
        expected = bytearray(before)
        expected[self.ACTIVE_SITE - self.BASE:
                 self.ACTIVE_SITE - self.BASE + len(self.ACTIVE_REPLACEMENT)] = \
            self.ACTIVE_REPLACEMENT
        expected[self.PARTY_SITE - self.BASE:
                 self.PARTY_SITE - self.BASE + len(self.PARTY_REPLACEMENT)] = \
            self.PARTY_REPLACEMENT
        expected[self.HELPER_ADDRESS - self.BASE:
                 self.HELPER_ADDRESS - self.BASE + len(self.HELPER)] = self.HELPER
        self.assertEqual(after, bytes(expected))
        self.assertEqual(report['active_site'], self.ACTIVE_SITE)
        self.assertEqual(report['party_site'], self.PARTY_SITE)
        self.assertEqual(report['helper'], self.HELPER_ADDRESS)
        self.assertEqual(report['helper_bytes'], len(self.HELPER))

    def test_absorb_switch_guard_function_tail_and_repeat_fail_closed(self):
        before = self.image()
        function_pin = digest(before[self.FUNCTION[0] - self.BASE:
                                     self.FUNCTION[1] - self.BASE])
        damaged = bytearray(before)
        damaged[self.ACTIVE_SITE - self.BASE] ^= 1
        with self.assertRaisesRegex(ValueError, 'caller'):
            ai.patch_absorb_switch_overlay(
                bytes(damaged), function_sha256=digest(bytes(damaged)[
                    self.FUNCTION[0] - self.BASE:self.FUNCTION[1] - self.BASE]))
        damaged = bytearray(before)
        damaged[self.PARTY_SITE - self.BASE] ^= 1
        with self.assertRaisesRegex(ValueError, 'caller'):
            ai.patch_absorb_switch_overlay(
                bytes(damaged), function_sha256=digest(bytes(damaged)[
                    self.FUNCTION[0] - self.BASE:self.FUNCTION[1] - self.BASE]))
        damaged = bytearray(before)
        damaged[self.HELPER_ADDRESS - self.BASE + 7] = 1
        with self.assertRaisesRegex(ValueError, 'tail'):
            ai.patch_absorb_switch_overlay(bytes(damaged), function_sha256=function_pin)
        damaged = bytearray(before)
        damaged[self.FUNCTION[0] - self.BASE] ^= 1
        with self.assertRaisesRegex(ValueError, 'function'):
            ai.patch_absorb_switch_overlay(bytes(damaged), function_sha256=function_pin)
        after, _ = ai.patch_absorb_switch_overlay(before, function_sha256=function_pin)
        with self.assertRaises(ValueError):
            ai.patch_absorb_switch_overlay(
                after, function_sha256=digest(after[self.FUNCTION[0] - self.BASE:
                                                     self.FUNCTION[1] - self.BASE]))


if __name__ == '__main__':
    unittest.main()
