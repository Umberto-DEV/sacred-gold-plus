"""Class B: actual EN/IT V4 encounter rolls, patched in memory only.

Run 02247568..0224760E from entry through return, retaining the native step
boost, radio getters, second roll and signed-division routines. Only avatar,
terrain and the RNG source are controlled at guarded native entries. This is instruction
coverage with synthetic field state, not gameplay or SAVE/cold validation.

SGP_LULLABY_ROM_EN/IT override the immutable V4 paths, never their hashes.
Missing inputs skip unless SGP_LULLABY_REQUIRE_INPUTS=1. No ROM is written.
"""
import hashlib
import itertools
import os
from pathlib import Path
import struct
import unittest

from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB, UC_HOOK_CODE
from unicorn.arm_const import (
    UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3,
    UC_ARM_REG_R4, UC_ARM_REG_R5, UC_ARM_REG_R6, UC_ARM_REG_R7,
    UC_ARM_REG_R8, UC_ARM_REG_R9, UC_ARM_REG_R10, UC_ARM_REG_R11,
    UC_ARM_REG_SP, UC_ARM_REG_LR, UC_ARM_REG_PC,
)

from sgp12.rom import Arm9, Rom
from . import lullaby

ROOT = Path(__file__).resolve().parents[2]
V4_ROOT = ROOT / 'local/experiments/balance493-2026-10-28'
V4 = {
    'EN': ('179edfb1ca331503f438e98f3afccfb0ab85759bf9ab88fb86c735f5fcefbf90', 147345256),
    'IT': ('2a2f0b437fca524c18b71b20feb01a1f51351e61c7c897ce73d9b3be1ee3a156', 153228136),
}
# Independent pins: do not derive the native execution oracle from the applier.
ENTRY, END, RADIO_TAIL, FIRST_ROLL, SECOND_ROLL = (
    0x02247568, 0x0224760E, 0x022475D4, 0x022475E8, 0x0224766C)
FUNCTION_SHA = '046812ab4798bf0e73dd39bd46b952d768a05fabf526cf932fa974fd4467a86e'
NATIVE_TAIL = bytes.fromhex('0af06efe022802d1193c2006040e642c00d96424')
FIXED_TAIL = bytes.fromhex('022804d1193c02d200242006040e642c00d96424')
RADIO_GETTER = 0x022522B4
RADIO_GETTER_SHA = 'd6a8e1224748bbeed9865b96fc8ff814e01511bcd2ab07cfa4f978a89482b132'
SOUND_GETTER = 0x02004A20
SOUND_GETTER_BYTES = bytes.fromhex('014800687047c046e0051d02')
RADIO_GLOBAL = 0x021D05E0
STUBS = {
    0x0205C700: ('get_avatar_state', '10b5041c01d1c8f709ffa06910bd0000'),
    0x0205DE98: ('get_run_flag', '08b5fef781fc583803280bd800187844'),
    0x0205B6F4: ('is_very_tall_grass', '032801d10120704700207047802801d1'),
    0x0201FD44: ('random', '054906484a68131c4343054818184860'),
}
REGISTERS = (UC_ARM_REG_R4, UC_ARM_REG_R5, UC_ARM_REG_R6, UC_ARM_REG_R7,
             UC_ARM_REG_R8, UC_ARM_REG_R9, UC_ARM_REG_R10, UC_ARM_REG_R11)
FIELD, AVATAR, STACK_TOP, STOP = 0x02700000, 0x02701000, 0x02710000, 0x0271F000
INPUT_CACHE = {}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def input_image(case, language):
    if language not in INPUT_CACHE:
        path = Path(os.environ.get('SGP_LULLABY_ROM_' + language)
                    or V4_ROOT / f'candidate-v4-{language}.nds')
        if not path.is_file():
            message = f'private {language} V4 input missing: {path}'
            if os.environ.get('SGP_LULLABY_REQUIRE_INPUTS') == '1':
                case.fail(message)
            case.skipTest(message)
        raw = path.read_bytes()
        sha, size = V4[language]
        case.assertEqual((digest(raw), len(raw)), (sha, size))
        header, _, original = Rom(raw).immagine_overlay(2)
        base = header['ram']
        case.assertEqual((base, len(original)), (0x02245B80, 0xE2A0))
        case.assertEqual(digest(original[ENTRY-base:END-base]), FUNCTION_SHA)
        case.assertEqual(original[RADIO_TAIL-base:RADIO_TAIL-base+20], NATIVE_TAIL)
        patched = lullaby.patch_overlay(original)
        case.assertEqual(patched[RADIO_TAIL-base:RADIO_TAIL-base+20], FIXED_TAIL)
        arm9 = Arm9(path)
        INPUT_CACHE[language] = (raw, arm9, base, original, patched)
    return INPUT_CACHE[language]


class NativeRoll:
    def __init__(self, arm9, base, image):
        self.cpu = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
        self.cpu.mem_map(0x02000000, 0x400000)
        self.cpu.mem_map(0x01FF8000, 0x4000)
        self.cpu.mem_map(0x027E0000, 0x20000)
        self.cpu.mem_map(0x02700000, 0x20000)
        for address, offset, size in arm9.segmenti:
            self.cpu.mem_write(address, bytes(arm9.raw[offset:offset+size]))
        self.cpu.mem_write(base, image)
        if digest(bytes(self.cpu.mem_read(RADIO_GETTER, 0x84))) != RADIO_GETTER_SHA:
            raise AssertionError('native radio classifier changed')
        if bytes(self.cpu.mem_read(SOUND_GETTER, 12)) != SOUND_GETTER_BYTES:
            raise AssertionError('native sound getter/global changed')
        for address, (_, signature) in STUBS.items():
            actual = bytes(self.cpu.mem_read(address, len(bytes.fromhex(signature))))
            if actual != bytes.fromhex(signature):
                raise AssertionError(f'unguarded native seam {address:08x}')
            self.cpu.hook_add(UC_HOOK_CODE, self.stub, None, address, address)
        self.cpu.hook_add(UC_HOOK_CODE, self.observe, None, FIRST_ROLL, FIRST_ROLL)
        self.cpu.hook_add(UC_HOOK_CODE, self.observe, None, SECOND_ROLL, SECOND_ROLL)
        self.cpu.hook_add(UC_HOOK_CODE, self.observe, None, RADIO_GETTER, RADIO_GETTER)
        self.cpu.mem_write(FIELD + 0x40, struct.pack('<I', AVATAR))

    def observe(self, cpu, address, size, unused):
        if address == RADIO_GETTER:
            self.calls.append('get_radio_music')
        elif address == FIRST_ROLL:
            self.modified_rate = cpu.reg_read(UC_ARM_REG_R4)
        else:
            self.calls.append('second_encounter_roll')
            if (cpu.reg_read(UC_ARM_REG_R0), cpu.reg_read(UC_ARM_REG_R1)) != (
                    FIELD, min(self.state['encounter_rate'], 100)):
                self.error = 'second encounter roll received wrong arguments'
                cpu.emu_stop()

    def stub(self, cpu, address, size, unused):
        name = STUBS[address][0]
        self.calls.append(name)
        arg = cpu.reg_read(UC_ARM_REG_R0)
        try:
            if name in ('get_avatar_state', 'get_run_flag'):
                assert arg == AVATAR, 'avatar accessor received a foreign pointer'
                result = self.state['avatar' if name == 'get_avatar_state' else 'running']
            elif name == 'is_very_tall_grass':
                assert arg == self.state['metatile'], 'terrain accessor argument'
                result = self.state['tall']
            else:
                index = self.calls.count('random') - 1
                assert index < 2, 'unexpected third RNG call'
                result = (self.state['first_rng'], self.state['second_rng'])[index]
            # The real accessors may clobber caller-saved registers. Do not let
            # accidental preservation hide a native/patch liveness regression.
            for register in (UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3):
                cpu.reg_write(register, 0xA6A6A6A6)
            cpu.reg_write(UC_ARM_REG_R0, result)
            cpu.reg_write(UC_ARM_REG_PC, cpu.reg_read(UC_ARM_REG_LR))
        except Exception as error:
            self.error = str(error)
            cpu.emu_stop()

    def run(self, *, avatar=0, running=0, tall=0, counter=0, radio=2,
            encounter_rate=20, first_rng=0, second_rng=0, radio_seq=None):
        self.state = dict(avatar=avatar, running=running, tall=tall, counter=counter,
                          radio=radio, encounter_rate=encounter_rate,
                          first_rng=first_rng, second_rng=second_rng, metatile=3 if tall else 0)
        self.calls, self.error, self.modified_rate = [], None, None
        cpu = self.cpu
        # Controlled input to the real pure getter; no mocking of its switch,
        # radio aliases, or SndRadio_GetSeqNo's load from the native global.
        sequence = (0, 1100, 1099)[radio] if radio_seq is None else radio_seq
        cpu.mem_write(RADIO_GLOBAL, struct.pack('<I', sequence))
        cpu.mem_write(FIELD + 0x7C, struct.pack('<H', counter))
        cpu.mem_write(STACK_TOP - 0x100, b'\xA5' * 0x40)
        cpu.mem_write(STACK_TOP, b'\x5A' * 0x40)
        for index, register in enumerate(REGISTERS):
            cpu.reg_write(register, 0xB0000000 + index)
        cpu.reg_write(UC_ARM_REG_R0, FIELD)
        cpu.reg_write(UC_ARM_REG_R1, encounter_rate)
        cpu.reg_write(UC_ARM_REG_R2, self.state['metatile'])
        cpu.reg_write(UC_ARM_REG_SP, STACK_TOP)
        cpu.reg_write(UC_ARM_REG_LR, STOP | 1)
        cpu.emu_start(ENTRY | 1, STOP, count=2000)
        if self.error:
            raise AssertionError(self.error)
        assert cpu.reg_read(UC_ARM_REG_PC) == STOP, 'native execution did not return'
        assert cpu.reg_read(UC_ARM_REG_SP) == STACK_TOP, 'native stack imbalance'
        assert [cpu.reg_read(r) for r in REGISTERS] == [0xB0000000+i for i in range(8)], 'callee-saved register changed'
        assert bytes(cpu.mem_read(STACK_TOP - 0x100, 0x40)) == b'\xA5' * 0x40
        assert bytes(cpu.mem_read(STACK_TOP, 0x40)) == b'\x5A' * 0x40
        assert bytes(cpu.mem_read(RADIO_GLOBAL, 4)) == struct.pack('<I', sequence), 'radio getter mutated input'
        return cpu.reg_read(UC_ARM_REG_R0), self.modified_rate, tuple(self.calls)


class LullabyCandidate(unittest.TestCase):
    @classmethod
    def tearDownClass(cls):
        for language in INPUT_CACHE:
            path = Path(os.environ.get('SGP_LULLABY_ROM_' + language)
                        or V4_ROOT / f'candidate-v4-{language}.nds')
            if digest(path.read_bytes()) != V4[language][0]:
                raise AssertionError(f'{language} original ROM changed during the tests')

    def benches(self, language):
        _, arm9, base, original, patched = input_image(self, language)
        return NativeRoll(arm9, base, original), NativeRoll(arm9, base, patched)

    def test_writer_retains_slot_geometry_and_every_unrelated_byte(self):
        for language in ('EN', 'IT'):
            with self.subTest(language=language):
                before, _, base, old, fixed_image = input_image(self, language)
                after, receipt = lullaby.apply(before, language)
                _, _, new = Rom(after).immagine_overlay(2)
                self.assertEqual(new, fixed_image, 'container writer installed a different overlay')
                fat, fat_size, y9, y9_size = struct.unpack_from('<4I', before, 0x48)
                start, end = struct.unpack_from('<II', before, fat + 16)
                self.assertEqual(len(before), len(after))
                self.assertEqual(before[:0x200], after[:0x200])
                self.assertEqual(before[fat:fat+fat_size], after[fat:fat+fat_size])
                self.assertEqual(before[y9:y9+y9_size], after[y9:y9+y9_size])
                self.assertEqual(before[:start], after[:start])
                self.assertEqual(before[end:], after[end:])
                self.assertEqual(new[RADIO_TAIL-base:RADIO_TAIL-base+20], FIXED_TAIL)
                self.assertEqual([base+i for i, (a, b) in enumerate(zip(old, new)) if a != b],
                                 [0x022475D4, 0x022475D5, 0x022475D6, 0x022475D7,
                                  0x022475D8, 0x022475D9, 0x022475DB,
                                  0x022475DC, 0x022475DD])
                self.assertTrue(lullaby.verify(before, after, receipt)['ok'])
                self.assertEqual(digest(Path(os.environ.get('SGP_LULLABY_ROM_' + language)
                                            or V4_ROOT / f'candidate-v4-{language}.nds').read_bytes()), V4[language][0])

    def test_walking_lullaby_zero_floor_and_native_reverse_turn_boost(self):
        # These count reverse-direction frames, not ordinary walking steps.
        for language in ('EN', 'IT'):
            old, new = self.benches(language)
            for counter, old_rate, new_rate in ((0, 100, 0), (1, 100, 0), (2, 25, 25),
                                                (3, 35, 35), (4, 55, 55), (5, 55, 55)):
                with self.subTest(language=language, counter=counter):
                    before = old.run(counter=counter)
                    after = new.run(counter=counter)
                    self.assertEqual((before[0], before[1]), (1, old_rate))
                    self.assertEqual((after[0], after[1]), (int(counter >= 2), new_rate))
                    self.assertEqual(before[2].count('random'), 2)
                    self.assertEqual(after[2].count('random'), 2 if counter >= 2 else 1)
                    self.assertEqual(after[2].count('second_encounter_roll'), int(counter >= 2))

    def test_complete_native_paths_change_only_the_low_lullaby_gate(self):
        for language in ('EN', 'IT'):
            old, new = self.benches(language)
            changed = 0
            for avatar, running, tall, counter, radio in itertools.product(
                    (0, 1, 2, 3), (0, 1), (0, 1), range(6), (0, 1, 2)):
                # Independent semantic oracle, with hand-checked step thresholds.
                pre = (40 if avatar in (1, 2) or running else 20)
                pre += 40 if tall else (30 if avatar == 1 else 0)
                pre += (0, 0, 30, 40, 60, 60)[counter]
                effect = 25 if radio == 1 else (-25 if radio == 2 else 0)
                expected_old = min((pre + effect) & 255, 100)
                expected_new = min(max(pre + effect, 0), 100)
                for first_rng, second_rng, encounter_rate in itertools.product(
                        (0, 24, 25, 99), (0, 99), (20, 255)):
                    args = dict(avatar=avatar, running=running, tall=tall, counter=counter,
                                radio=radio, first_rng=first_rng, second_rng=second_rng,
                                encounter_rate=encounter_rate)
                    with self.subTest(language=language, **args):
                        before, after = old.run(**args), new.run(**args)
                        for row, rate in ((before, expected_old), (after, expected_new)):
                            passed = first_rng < rate
                            self.assertEqual(row[0], int(passed and second_rng < min(encounter_rate, 100)))
                            self.assertEqual(row[1], rate)
                            self.assertEqual(row[2].count('random'), 1 + int(passed))
                            self.assertEqual(row[2].count('second_encounter_roll'), int(passed))
                            self.assertEqual(row[2].count('get_avatar_state'), 1)
                            self.assertEqual(row[2].count('get_run_flag'), int(avatar not in (1, 2)))
                            self.assertEqual(row[2].count('is_very_tall_grass'), 1)
                        self.assertEqual(before[2].count('get_radio_music'), 1 if radio == 1 else 2)
                        self.assertEqual(after[2].count('get_radio_music'), 1)
                        if expected_old == expected_new:
                            self.assertEqual(before[:2], after[:2])
                            self.assertEqual(tuple(c for c in before[2] if c != 'get_radio_music'),
                                             tuple(c for c in after[2] if c != 'get_radio_music'))
                        else:
                            self.assertEqual((radio, pre), (2, 20))
                            changed += 1
            self.assertGreater(changed, 0, 'the low Lullaby branch was not exercised')

    def test_native_radio_classifier_keeps_both_music_aliases(self):
        for language in ('EN', 'IT'):
            old, new = self.benches(language)
            for radio, sequence, old_rate, new_rate in (
                    (0, 0, 20, 20), (1, 1100, 45, 45), (1, 1312, 45, 45),
                    (2, 1099, 100, 0), (2, 1311, 100, 0)):
                with self.subTest(language=language, sequence=sequence):
                    before = old.run(radio=radio, radio_seq=sequence)
                    after = new.run(radio=radio, radio_seq=sequence)
                    self.assertEqual(before[1], old_rate)
                    self.assertEqual(after[1], new_rate)
                    self.assertEqual(before[2].count('get_radio_music'), 1 if radio == 1 else 2)
                    self.assertEqual(after[2].count('get_radio_music'), 1)


if __name__ == '__main__':
    unittest.main()
