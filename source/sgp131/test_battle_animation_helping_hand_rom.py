"""Class B HG-F20-HH tests on immutable EN/IT V4 candidates, in memory."""
from pathlib import Path
import hashlib
import struct
import unittest

import ndspy.narc
import ndspy.rom
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB
from unicorn.arm_const import (UC_ARM_REG_LR, UC_ARM_REG_R0, UC_ARM_REG_R1,
                               UC_ARM_REG_R2, UC_ARM_REG_R3, UC_ARM_REG_SP)

from sgp12.blz import ndspy_load_overlays_sicuri
from sgp131 import battle_animation_dynamicpunch as dynamicpunch
from sgp131 import battle_animation_facade as facade
from sgp131 import battle_animation_helping_hand as helping_hand
from sgp131 import mechanics_stages


ROOT = Path(__file__).resolve().parents[2]
V4_ROOT = ROOT / 'local/experiments/balance493-2026-10-28'
V4 = {
    'EN': ('179edfb1ca331503f438e98f3afccfb0ab85759bf9ab88fb86c735f5fcefbf90',
           '102e5fca155807a5bde6e0b534901b6314c187f8a30672acf1a9db147a0abc73',
           '01bdf67e3be5357d0f4eb9201dd748bf153e1b102d758f390daf0ad2b8dbf5bd'),
    'IT': ('2a2f0b437fca524c18b71b20feb01a1f51351e61c7c897ce73d9b3be1ee3a156',
           '0fc63429cad6a33d0d76204f2ed1c2c96abcbdb8cd98f1fc22df0ebbca635d98',
           '3025d43221df9bd340a6b4183d73eda2941960c5f0633356f1b14207f61c4ba2'),
}

OVERLAY_SHA256 = '245d65b0a3aab0b753d0b45d3532ecb168e4d50d2dd4c3894821f1ccdbad0ad0'
INIT_SHAKE = 0x022227A8
STEP_SHAKE = 0x022227D8
DELAY_HANDLER = 0x0221C6EC
DELAY_CALLBACK = 0x0221BE20
INTERPRETER_CALLBACK = 0x0221BE44
BEGIN_LOOP_HANDLER = 0x0221C934
END_LOOP_HANDLER = 0x0221C974
MAP_BASE, MAP_SIZE = 0x02200000, 0x200000
STATE, CONTEXT, SCRIPT = 0x02300000, 0x02301000, 0x02302000
STACK, STOP = 0x023F0000, 0x023FF000


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def signed_halfword(raw):
    return struct.unpack('<h', raw)[0]


class NativeOverlay7:
    def __init__(self, rom_bytes):
        overlay = ndspy_load_overlays_sicuri(
            ndspy.rom.NintendoDSRom(rom_bytes), [7])[7]
        self.overlay_sha256 = sha(bytes(overlay.data))
        if self.overlay_sha256 != OVERLAY_SHA256:
            raise AssertionError('overlay 7 decompressed identity differs')
        self.cpu = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
        self.cpu.mem_map(MAP_BASE, MAP_SIZE)
        self.cpu.mem_write(overlay.ramAddress, bytes(overlay.data))

    def call(self, address, *, r0=0, r1=0, r2=0, r3=0,
             stack_word=None, count=10_000):
        self.cpu.reg_write(UC_ARM_REG_R0, r0)
        self.cpu.reg_write(UC_ARM_REG_R1, r1)
        self.cpu.reg_write(UC_ARM_REG_R2, r2)
        self.cpu.reg_write(UC_ARM_REG_R3, r3)
        self.cpu.reg_write(UC_ARM_REG_SP, STACK)
        self.cpu.reg_write(UC_ARM_REG_LR, STOP | 1)
        if stack_word is not None:
            self.cpu.mem_write(STACK, struct.pack('<I', stack_word))
        self.cpu.emu_start(address | 1, STOP, count=count)

    def shake(self):
        self.cpu.mem_write(STATE, bytes(0x40))
        self.call(INIT_SHAKE, r0=STATE, r1=1, r2=0, r3=1, stack_word=2)
        offsets = []
        for _ in range(10):
            self.call(STEP_SHAKE, r0=STATE)
            active = self.cpu.reg_read(UC_ARM_REG_R0)
            if not active:
                break
            offsets.append(signed_halfword(bytes(self.cpu.mem_read(STATE, 2))))
        return tuple(offsets)

    def delay_resume_calls(self, delay):
        self.cpu.mem_write(CONTEXT, bytes(0x100))
        self.cpu.mem_write(CONTEXT + 0x18, struct.pack('<I', SCRIPT - 4))
        self.cpu.mem_write(SCRIPT, struct.pack('<I', delay))
        self.call(DELAY_HANDLER, r0=CONTEXT)
        for call in range(1, delay + 3):
            self.call(DELAY_CALLBACK, r0=CONTEXT)
            callback = struct.unpack(
                '<I', bytes(self.cpu.mem_read(CONTEXT + 0xBC, 4)))[0]
            if callback & ~1 == INTERPRETER_CALLBACK:
                return call
        raise AssertionError('Delay callback did not resume the interpreter')

    def loop_trace(self):
        self.cpu.mem_write(CONTEXT, bytes(0x100))
        self.cpu.mem_write(SCRIPT, struct.pack('<II', 2, 2))
        self.cpu.mem_write(SCRIPT + 0x20, struct.pack('<I', 3))
        self.cpu.mem_write(CONTEXT + 0x18, struct.pack('<I', SCRIPT))
        self.call(BEGIN_LOOP_HANDLER, r0=CONTEXT)

        def state(label):
            return {
                'label': label,
                'script': struct.unpack('<I', bytes(
                    self.cpu.mem_read(CONTEXT + 0x18, 4)))[0],
                'body': struct.unpack('<I', bytes(
                    self.cpu.mem_read(CONTEXT + 0x28, 4)))[0],
                'active': struct.unpack('<I', bytes(
                    self.cpu.mem_read(CONTEXT + 0x30, 4)))[0],
                'counter': self.cpu.mem_read(CONTEXT + 0x2C, 1)[0],
                'limit': self.cpu.mem_read(CONTEXT + 0x2D, 1)[0],
            }

        trace = [state('begin')]
        for label in ('first-end', 'second-end'):
            self.cpu.mem_write(CONTEXT + 0x18,
                               struct.pack('<I', SCRIPT + 0x20))
            self.call(END_LOOP_HANDLER, r0=CONTEXT)
            trace.append(state(label))
        return trace


class ActualHelpingHandCandidates(unittest.TestCase):
    def test_native_overlay_primitives_match_the_schedule_oracle(self):
        reference = None
        for language, (input_sha, _predecessor_sha, _output_sha) in V4.items():
            with self.subTest(language=language):
                path = V4_ROOT / f'candidate-v4-{language}.nds'
                if not path.is_file():
                    self.skipTest('immutable V4 candidate unavailable: ' + str(path))
                before = path.read_bytes()
                self.assertEqual(sha(before), input_sha)
                native = NativeOverlay7(before)
                result = {
                    'overlay': native.overlay_sha256,
                    'shake': native.shake(),
                    'delay': tuple(native.delay_resume_calls(value)
                                   for value in (1, 2, 3)),
                    'loop': native.loop_trace(),
                }
                if reference is None:
                    reference = result
                else:
                    self.assertEqual(result, reference)
                self.assertEqual(result['shake'], (1, 0, -1, 0, 1, 0, -1, 0))
                self.assertEqual(result['delay'], (2, 3, 4))
                self.assertEqual(result['loop'], [
                    {'label': 'begin', 'script': SCRIPT + 8,
                     'body': SCRIPT + 8, 'active': 1, 'counter': 0, 'limit': 2},
                    {'label': 'first-end', 'script': SCRIPT + 8,
                     'body': SCRIPT + 8, 'active': 1, 'counter': 1, 'limit': 2},
                    {'label': 'second-end', 'script': SCRIPT + 0x24,
                     'body': SCRIPT + 8, 'active': 0, 'counter': 2, 'limit': 2},
                ])

    def test_combined_successor_fixes_only_the_three_loop_boundary_bytes(self):
        for language, (input_sha, predecessor_sha, output_sha) in V4.items():
            with self.subTest(language=language):
                path = V4_ROOT / f'candidate-v4-{language}.nds'
                if not path.is_file():
                    self.skipTest('immutable V4 candidate unavailable: ' + str(path))
                before = path.read_bytes()
                self.assertEqual(sha(before), input_sha)
                with self.assertRaisesRegex(ValueError, 'predecessor missing'):
                    helping_hand.apply(before, language)

                after_facade, facade_receipt = facade.apply(before, language)
                predecessor, dynamic_receipt = dynamicpunch.apply(after_facade, language)
                self.assertEqual(sha(predecessor), predecessor_sha)
                old_archive = bytes(ndspy.rom.NintendoDSRom(predecessor).getFileByName(
                    helping_hand.ARCHIVE))
                old_files = ndspy.narc.NARC(old_archive).files
                retail = helping_hand.read_member_timing(
                    bytes(old_files[helping_hand.MEMBER_INDEX]))
                self.assertEqual(retail.schedule.final_x, -1)

                after, receipt = helping_hand.apply(predecessor, language)
                report = helping_hand.verify(predecessor, after, receipt)
                self.assertEqual(sha(after), output_sha)
                self.assertEqual(report['changed_rom_bytes'], 3)
                self.assertEqual(report['rom_offsets'],
                                 [17255212, 17255216, 17255220])
                self.assertEqual(report['shake_start_ticks_before'], [0, 7, 16])
                self.assertEqual(report['shake_start_ticks_after'], [0, 9, 18])
                self.assertEqual(report['captured_base_x_before'], [0, -1, -1])
                self.assertEqual(report['captured_base_x_after'], [0, 0, 0])
                self.assertEqual((report['final_x_before'], report['final_x_after']),
                                 (-1, 0))

                new_archive = bytes(ndspy.rom.NintendoDSRom(after).getFileByName(
                    helping_hand.ARCHIVE))
                new_files = ndspy.narc.NARC(new_archive).files
                self.assertEqual(sha(new_archive), helping_hand.ARCHIVE_AFTER_SHA256)
                self.assertEqual(sha(bytes(new_files[helping_hand.MEMBER_INDEX])),
                                 helping_hand.MEMBER_AFTER_SHA256)
                self.assertEqual(bytes(new_files[facade.MEMBER_INDEX]),
                                 bytes(old_files[facade.MEMBER_INDEX]))
                self.assertEqual(bytes(new_files[dynamicpunch.MEMBER_INDEX]),
                                 bytes(old_files[dynamicpunch.MEMBER_INDEX]))
                self.assertEqual(sha(path.read_bytes()), input_sha)

                stage = mechanics_stages.require_stage(
                    'battle-animation-helping-hand')
                cold_regions = stage.regions(before)
                predecessor_regions = stage.regions(predecessor)
                self.assertEqual(cold_regions, predecessor_regions)
                self.assertEqual([(region.start, region.end)
                                  for region in predecessor_regions],
                                 [(17255212, 17255213),
                                  (17255216, 17255217),
                                  (17255220, 17255221)])
                mechanics_stages.check_confined(
                    predecessor, after, predecessor_regions, stage.name)

                no_ui_writes = lambda *_args: None
                staged_facade, wrapped_facade = mechanics_stages.run_stage(
                    'battle-animation-facade', before, language,
                    invariants=no_ui_writes)
                staged_dynamic, wrapped_dynamic = mechanics_stages.run_stage(
                    'battle-animation-dynamicpunch', staged_facade, language,
                    invariants=no_ui_writes)
                staged_final, wrapped_helping = mechanics_stages.run_stage(
                    'battle-animation-helping-hand', staged_dynamic, language,
                    invariants=no_ui_writes)
                self.assertEqual(staged_final, after)

                replay = mechanics_stages.verify_chain(
                    before, staged_final,
                    ['battle-animation-facade',
                     'battle-animation-dynamicpunch',
                     'battle-animation-helping-hand'],
                    [wrapped_facade, wrapped_dynamic, wrapped_helping],
                    lambda image: {'cold_v4_reconstructed': image == before},
                    invariants=no_ui_writes,
                )
                self.assertEqual(replay['stages'], [
                    'battle-animation-facade',
                    'battle-animation-dynamicpunch',
                    'battle-animation-helping-hand',
                ])

                mutant = bytearray(after)
                mutant[0x300] ^= 1
                mutant = bytes(mutant)
                with self.assertRaisesRegex(ValueError, 'changed ROM offsets'):
                    helping_hand.verify(
                        predecessor, mutant,
                        dict(receipt, output_sha256=sha(mutant)))


if __name__ == '__main__':
    unittest.main()
