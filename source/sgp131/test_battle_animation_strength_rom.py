"""Class B HG-F18 tests on immutable EN/IT V4 candidates, in memory."""
from pathlib import Path
import hashlib
import struct
import unittest

import ndspy.narc
import ndspy.rom
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2

from sgp12.blz import ndspy_load_overlays_sicuri
from sgp131 import battle_animation_dynamicpunch as dynamicpunch
from sgp131 import battle_animation_facade as facade
from sgp131 import battle_animation_helping_hand as helping_hand
from sgp131 import battle_animation_strength as strength
from sgp131 import mechanics_stages
from sgp131.test_battle_animation_helping_hand_rom import NativeOverlay7


ROOT = Path(__file__).resolve().parents[2]
V4_ROOT = ROOT / 'local/experiments/balance493-2026-10-28'
V4 = {
    'EN': ('179edfb1ca331503f438e98f3afccfb0ab85759bf9ab88fb86c735f5fcefbf90',
           '01bdf67e3be5357d0f4eb9201dd748bf153e1b102d758f390daf0ad2b8dbf5bd',
           'acfc8db48ab33240c5f11c9352282c2891767c66e9eb78cdfb746e043725d089'),
    'IT': ('2a2f0b437fca524c18b71b20feb01a1f51351e61c7c897ce73d9b3be1ee3a156',
           '3025d43221df9bd340a6b4183d73eda2941960c5f0633356f1b14207f61c4ba2',
           '7d29d51de92c6c3f413db1c6b2712d441b0a9b8ba9873a2e7bb68a1f96215e23'),
}

OVERLAY_SHA256 = '245d65b0a3aab0b753d0b45d3532ecb168e4d50d2dd4c3894821f1ccdbad0ad0'
TASK_SHA256 = '9c4ca4a92bd69173157f08dfd4b6c507676d591acfddd6d3f1989e2c9bf7e769'
CLEANUP_SHA256 = '7a61f1ad710b20487a6ab8eed87f0730e4126657fdd93db51efdec5ca60ff8f2'
STRENGTH_TASK = 0x02227630
SHAKE_INIT = 0x022227A8
SET_ATTRIBUTE = 0x020087A4
ADD_ATTRIBUTE = 0x02008C2C
CTX, SPRITE, FAKE_TASK = 0x02320000, 0x02321000, 0x02322000


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def signed32(value):
    return value if value < 0x80000000 else value - 0x100000000


def install_sprite_stubs(native):
    native.cpu.mem_map(0x02000000, 0x00100000)
    native.cpu.mem_write(SET_ATTRIBUTE, b'\x70\x47')
    native.cpu.mem_write(ADD_ATTRIBUTE, b'\x70\x47')


def run_strength_shrink(rom_bytes, frames):
    native = NativeOverlay7(rom_bytes)
    install_sprite_stubs(native)
    added_x = []

    def capture_add(uc, address, _size, _user):
        if address == ADD_ATTRIBUTE:
            if uc.reg_read(UC_ARM_REG_R0) != SPRITE:
                raise AssertionError('Strength AddAttribute sprite differs')
            if uc.reg_read(UC_ARM_REG_R1) != 0:
                raise AssertionError('Strength AddAttribute is not X')
            added_x.append(signed32(uc.reg_read(UC_ARM_REG_R2)))

    native.cpu.hook_add(UC_HOOK_CODE, capture_add,
                        begin=ADD_ATTRIBUTE, end=ADD_ATTRIBUTE + 2)
    ctx = bytearray(0x5C)
    ctx[0] = 0
    struct.pack_into('<h', ctx, 0x02, 77)
    struct.pack_into('<I', ctx, 0x04, 32)
    struct.pack_into('<I', ctx, 0x10, SPRITE)
    struct.pack_into('<I', ctx, 0x18, frames)
    native.cpu.mem_write(CTX, bytes(ctx))
    native.call(SHAKE_INIT, r0=CTX + 0x38, r1=2, r2=0, r3=0,
                stack_word=10)
    for _ in range(frames + 1):
        native.call(STRENGTH_TASK, r0=FAKE_TASK, r1=CTX)
    if native.cpu.mem_read(CTX, 1)[0] != 1:
        raise AssertionError('Strength shrink did not advance to state 1')
    return added_x


def run_strength_cleanup(rom_bytes):
    native = NativeOverlay7(rom_bytes)
    install_sprite_stubs(native)
    set_calls, add_calls = [], []

    def capture(uc, address, _size, _user):
        args = (uc.reg_read(UC_ARM_REG_R0),
                uc.reg_read(UC_ARM_REG_R1),
                signed32(uc.reg_read(UC_ARM_REG_R2)))
        if address == SET_ATTRIBUTE:
            set_calls.append(args)
        elif address == ADD_ATTRIBUTE:
            add_calls.append(args)

    native.cpu.hook_add(UC_HOOK_CODE, capture,
                        begin=SET_ATTRIBUTE, end=SET_ATTRIBUTE + 2)
    native.cpu.hook_add(UC_HOOK_CODE, capture,
                        begin=ADD_ATTRIBUTE, end=ADD_ATTRIBUTE + 2)
    ctx = bytearray(0x5C)
    ctx[0] = 5
    struct.pack_into('<h', ctx, 0x02, 77)
    struct.pack_into('<I', ctx, 0x10, SPRITE)
    struct.pack_into('<I', ctx, 0x18, 0)
    native.cpu.mem_write(CTX, bytes(ctx))
    native.call(STRENGTH_TASK, r0=FAKE_TASK, r1=CTX)
    if native.cpu.mem_read(CTX, 1)[0] != 6:
        raise AssertionError('Strength cleanup did not advance to state 6')
    return set_calls, add_calls


class ActualStrengthCandidates(unittest.TestCase):
    def test_real_task_proves_phase_and_cleanup_omits_x(self):
        expected = {
            8: ([2, 0, -2, 0, 2, 0, -2, 0], 0),
            9: ([2, 0, -2, 0, 2, 0, -2, 0, 2], 2),
            10: ([2, 0, -2, 0, 2, 0, -2, 0, 2, 0], 2),
            11: ([2, 0, -2, 0, 2, 0, -2, 0, 2, 0, -2], 0),
        }
        reference = None
        for language, (input_sha, _predecessor_sha, _output_sha) in V4.items():
            with self.subTest(language=language):
                path = V4_ROOT / f'candidate-v4-{language}.nds'
                if not path.is_file():
                    self.skipTest('immutable V4 candidate unavailable: ' + str(path))
                before = path.read_bytes()
                self.assertEqual(sha(before), input_sha)
                overlay = ndspy_load_overlays_sicuri(
                    ndspy.rom.NintendoDSRom(before), [7])[7]
                raw = bytes(overlay.data)
                self.assertEqual(sha(raw), OVERLAY_SHA256)
                self.assertEqual(sha(raw[0xB810:0xBA04]), TASK_SHA256)
                self.assertEqual(sha(raw[0xB9C4:0xB9F0]), CLEANUP_SHA256)
                observed = {}
                for frames, (trace, total) in expected.items():
                    actual = run_strength_shrink(before, frames)
                    self.assertEqual(actual, trace)
                    self.assertEqual(sum(actual), total)
                    observed[frames] = actual
                set_calls, add_calls = run_strength_cleanup(before)
                self.assertEqual(set_calls, [
                    (SPRITE, 12, 0x100),
                    (SPRITE, 13, 0x100),
                    (SPRITE, 1, 77),
                ])
                self.assertEqual(add_calls, [])
                self.assertNotIn(0, [attribute for _, attribute, _ in set_calls])
                current = (observed, set_calls, add_calls)
                if reference is None:
                    reference = current
                else:
                    self.assertEqual(current, reference)
                self.assertEqual(sha(path.read_bytes()), input_sha)

    def test_helping_hand_successor_changes_only_one_strength_byte(self):
        for language, (input_sha, predecessor_sha, output_sha) in V4.items():
            with self.subTest(language=language):
                path = V4_ROOT / f'candidate-v4-{language}.nds'
                if not path.is_file():
                    self.skipTest('immutable V4 candidate unavailable: ' + str(path))
                before = path.read_bytes()
                self.assertEqual(sha(before), input_sha)
                with self.assertRaisesRegex(ValueError, 'predecessor missing'):
                    strength.apply(before, language)
                after_facade, facade_receipt = facade.apply(before, language)
                after_dynamic, dynamic_receipt = dynamicpunch.apply(
                    after_facade, language)
                predecessor, helping_receipt = helping_hand.apply(
                    after_dynamic, language)
                self.assertEqual(sha(predecessor), predecessor_sha)
                after, receipt = strength.apply(predecessor, language)
                report = strength.verify(predecessor, after, receipt)
                self.assertEqual(sha(after), output_sha)
                self.assertEqual(report['changed_rom_bytes'], 1)
                self.assertEqual(report['rom_offset'], 0x0105F3F8)
                self.assertEqual((report['frames_before'], report['frames_after']),
                                 (10, 8))
                self.assertEqual((report['final_x_before'], report['final_x_after']),
                                 (2, 0))

                archive = bytes(ndspy.rom.NintendoDSRom(after).getFileByName(
                    strength.ARCHIVE))
                files = ndspy.narc.NARC(archive).files
                self.assertEqual(sha(archive), strength.ARCHIVE_AFTER_SHA256)
                self.assertEqual(sha(bytes(files[strength.MEMBER_INDEX])),
                                 strength.MEMBER_AFTER_SHA256)
                self.assertEqual(sha(path.read_bytes()), input_sha)

                stage = mechanics_stages.require_stage('battle-animation-strength')
                self.assertEqual(stage.regions(before), stage.regions(predecessor))
                no_ui_writes = lambda *_args: None
                staged_facade, wrapped_facade = mechanics_stages.run_stage(
                    'battle-animation-facade', before, language,
                    invariants=no_ui_writes)
                staged_dynamic, wrapped_dynamic = mechanics_stages.run_stage(
                    'battle-animation-dynamicpunch', staged_facade, language,
                    invariants=no_ui_writes)
                staged_helping, wrapped_helping = mechanics_stages.run_stage(
                    'battle-animation-helping-hand', staged_dynamic, language,
                    invariants=no_ui_writes)
                staged_final, wrapped_strength = mechanics_stages.run_stage(
                    'battle-animation-strength', staged_helping, language,
                    invariants=no_ui_writes)
                self.assertEqual(staged_final, after)
                replay = mechanics_stages.verify_chain(
                    before, staged_final,
                    ['battle-animation-facade',
                     'battle-animation-dynamicpunch',
                     'battle-animation-helping-hand',
                     'battle-animation-strength'],
                    [wrapped_facade, wrapped_dynamic,
                     wrapped_helping, wrapped_strength],
                    lambda image: {'cold_v4_reconstructed': image == before},
                    invariants=no_ui_writes,
                )
                self.assertEqual(replay['stages'][-1],
                                 'battle-animation-strength')


if __name__ == '__main__':
    unittest.main()
