"""Class B: real cartridge Check/Set/Clear and Continue caller, in Unicorn RAM.

SGP_EVENT_FLAGS_ROMS is a JSON EN/IT path map. SGP_EVENT_FLAGS_ORIGINAL=1
runs preservation regressions on unchanged code (expected RED). No ROM/save
is written. Flash, OS reset and reload are explicit seams, not hardware proof.
"""
import json
import os
from pathlib import Path
import struct
import tempfile
import unittest
from sgp12.rom import Arm9, Rom

VARS = 0x02280000
SAVE = 0x02290000
CHATOT = 0x022A0000
FS = 0x02270000
CTX = 0x02260000
SCRIPT = 0x02261000
STOP = 0x023EF000
STACK = 0x023FF000
CHECK, SET, CLEAR = 0x020503DC, 0x02050408, 0x02050430
VAR_GET, SET_VAR = 0x020403AC, 0x02040F14
FAMILY_IDS = tuple(range(0x612E, 0x613A)) + tuple(range(0x619E, 0x61AA))
FAMILY_FLAGS = (0x3F03, 0x3F06, 0x3F07, 0x3F09, 0x3F0A, 0x3F0B,
                0x3F0C, 0x3F0D, 0x3F0E, 0x3F0F, 0x3F10, 0x3F11,
                0x3F12, 0x3F13, 0x3F14, 0x3F15, 0x3F16, 0x3F17,
                0x3F1D, 0x3F1E, 0x3F1F, 0x3F26, 0x3F27, 0x3F28)
CHATOT_OFFSETS = tuple(range(0x1CC, 0x1E4, 2)) + tuple(range(0x2AC, 0x2C4, 2))


class Machine:
    def __init__(self, arm, patch=None):
        from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB, UC_HOOK_CODE
        from unicorn import arm_const as reg
        self.reg = reg
        self.mu = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
        self.mu.mem_map(0x01FF0000, 0x410000)
        for address, offset, size in arm.segmenti:
            if 0x01FF0000 <= address and address + size <= 0x02400000:
                self.mu.mem_write(address, bytes(arm.raw[offset:offset + size]))
        record, _, code = Rom(arm.raw).immagine_overlay(36)
        self.mu.mem_write(record['ram'], bytes(code))
        if patch:
            for address, payload in patch.items():
                self.mu.mem_write(address, payload)
        self.events = []
        self.reload = None
        self.reload_chatot = None
        self.loader = None
        self.load_result = 1
        self.player = None
        self.put(SAVE, 1)
        self.put(FS + 12, SAVE)
        self.mu.hook_add(UC_HOOK_CODE, self.hook)

    def put(self, address, value):
        self.mu.mem_write(address, struct.pack('<I', value))

    def read(self, address, length):
        return bytes(self.mu.mem_read(address, length))

    def ret(self, value=0):
        self.mu.reg_write(self.reg.UC_ARM_REG_R0, value)
        self.mu.reg_write(self.reg.UC_ARM_REG_PC, self.mu.reg_read(self.reg.UC_ARM_REG_LR))

    def hook(self, uc, address, size, user):
        a = uc.reg_read(self.reg.UC_ARM_REG_R0)
        b = uc.reg_read(self.reg.UC_ARM_REG_R1)
        if address == 0x0202551C:
            self.events.append('assert')
            self.ret()  # release assert returns; this causes the original defect
        elif address == 0x020272C8:
            assert a == SAVE and b in (4, 18)
            self.ret(VARS if b == 4 else CHATOT)
        elif address == self.loader:
            self.events.append('load')
            if self.reload is not None:
                self.mu.mem_write(VARS, self.reload)
            if self.reload_chatot is not None:
                self.mu.mem_write(CHATOT, self.reload_chatot)
            self.ret(self.load_result)
        elif address == 0x020D3B84:
            assert a == 0
            self.events.append('reset')
            self.mu.emu_stop()  # SDK noreturn hardware reset boundary
        elif address in (0x02028758, 0x020274A8, 0x02000EF4):
            raise AssertionError('unexpected flash/newgame/field registration')
        elif address in (0x020279EC, 0x02027180):
            self.events.append('postload')
            self.ret()  # checksum bookkeeping after accepted native Continue
        elif address in (0x0205C67C, 0x0205C688) and self.player is not None:
            self.ret(self.player[address == 0x0205C688])

    def call(self, address, *args):
        for i in range(4):
            self.mu.reg_write(getattr(self.reg, 'UC_ARM_REG_R'+str(i)), args[i] if i < len(args) else 0)
        self.mu.reg_write(self.reg.UC_ARM_REG_SP, STACK)
        self.mu.reg_write(self.reg.UC_ARM_REG_LR, STOP | 1)
        self.mu.emu_start(address | 1, STOP, count=100000)
        if self.events[-1:] != ['reset']:
            assert self.mu.reg_read(self.reg.UC_ARM_REG_PC) == STOP, 'instruction budget exhausted'
            assert self.mu.reg_read(self.reg.UC_ARM_REG_SP) == STACK
        return self.mu.reg_read(self.reg.UC_ARM_REG_R0)


def expected_bank(legacy, chatot):
    bank = bytearray(legacy)
    for flag, offset in zip(FAMILY_FLAGS, CHATOT_OFFSETS):
        byte, bit = divmod(flag - 0x3F00, 8)
        if struct.unpack_from('<H', chatot, offset)[0]:
            bank[byte] |= 1 << bit
        else:
            bank[byte] &= ~(1 << bit)
    return bytes(bank)


def normalize_hf01_candidate(arm):
    """Return an in-memory pre-event-flags view of the exact current candidate."""
    from sgp13 import event_flags
    if arm.leggi(event_flags.BASE, event_flags.SIZE) == bytes(event_flags.SIZE):
        return arm
    return event_flags.normalize_hf01(arm, 'EN')[0]  # native spans are EN/IT-identical


@unittest.skipUnless(os.environ.get('SGP_EVENT_FLAGS_ROMS'), 'private EN/IT cartridges required')
class NativeFlags(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.installed_arms = {lang: Arm9(path) for lang, path in json.loads(os.environ['SGP_EVENT_FLAGS_ROMS']).items()}
        cls.arms = {lang: normalize_hf01_candidate(arm) for lang, arm in cls.installed_arms.items()}
        cls.patch = {}
        cls.temp = tempfile.TemporaryDirectory(prefix='event-flags-native-')
        cls.addClassCleanup(cls.temp.cleanup)
        if not os.environ.get('SGP_EVENT_FLAGS_ORIGINAL'):
            from sgp13 import event_flags
            for lang, arm in cls.arms.items():
                cls.patch[lang], _ = event_flags.prepare(arm, cls.temp.name, lang)

    def machine(self, lang):
        return Machine(self.arms[lang], self.patch.get(lang))

    def test_first_set_preserves_all_palpad_and_copies_whole_bank(self):
        for lang in self.arms:
            with self.subTest(language=lang):
                m = self.machine(lang)
                old = bytearray((i * 43 + 20) % 256 for i in range(0x1400))
                old[0xAD9] &= 0xFE
                m.mu.mem_write(VARS, bytes(old))
                m.mu.mem_write(VARS + 0x2BC, bytes(36))
                before = m.read(VARS, 0x1400)
                m.call(SET, VARS, 0x3FC8)
                self.assertEqual(m.read(VARS + 0xA00, 0xA00), before[0xA00:])
                expected = bytearray(expected_bank(before[0xAC0:0xAE0], bytes(1004))); expected[25] |= 1
                self.assertEqual(m.read(VARS + 0x2C0, 32), expected)

    def test_first_check_installs_tag_and_snapshots_without_palpad_writes(self):
        for lang in self.arms:
            with self.subTest(language=lang):
                m = self.machine(lang)
                legacy = bytes((i * 37 + 5) % 256 for i in range(32))
                m.mu.mem_write(VARS + 0xAC0, legacy)
                self.assertEqual(m.call(CHECK, VARS, 0x3FC8), legacy[25] & 1)
                self.assertEqual(m.read(VARS + 0x2BC, 36), b'HF02' + expected_bank(legacy, bytes(1004)))
                self.assertEqual(m.read(VARS + 0xAC0, 32), legacy)

    def test_every_id_first_operation_snapshots_entire_bank_and_preserves_neighbors(self):
        # Mutants: old Pal Pad destination, partial import, wrong bank/mask.
        for lang in self.arms:
            m = self.machine(lang)
            for flag in range(0x3F00, 0x4000):
                byte, bit = divmod(flag - 0x3F00, 8)
                for value in (0, 1):
                    for operation in (CHECK, SET, CLEAR):
                        with self.subTest(lang=lang, flag=hex(flag), value=value, operation=operation):
                            before = bytearray((i * 43 + 20) % 256 for i in range(0x1400))
                            before[0x2BC:0x2E0] = bytes(36)
                            before[0xAC0 + byte] &= ~(1 << bit)
                            before[0xAC0 + byte] |= value << bit
                            m.mu.mem_write(VARS, bytes(before))
                            result = m.call(operation, VARS, flag)
                            expected = bytearray(before)
                            expected[0x2BC:0x2C0] = b'HF02'
                            expected[0x2C0:0x2E0] = expected_bank(before[0xAC0:0xAE0], bytes(1004))
                            if operation == SET:
                                expected[0x2C0 + byte] |= 1 << bit
                            elif operation == CLEAR:
                                expected[0x2C0 + byte] &= ~(1 << bit)
                            else:
                                self.assertEqual(result, 0 if flag in FAMILY_FLAGS else value)
                            self.assertEqual(m.read(VARS, 0x1400), bytes(expected))
            self.assertNotIn('assert', m.events)

    def test_tag_is_authoritative_after_friend_changes_and_repeated_access(self):
        for lang in self.arms:
            m = self.machine(lang)
            bank = bytes((37 * i + 1) % 256 for i in range(32))
            m.mu.mem_write(VARS + 0xAC0, bank)
            m.call(CHECK, VARS, 0x3F00)
            m.mu.mem_write(VARS + 0xAC0, bytes(x ^ 255 for x in bank))
            expected = bytearray(expected_bank(bank, bytes(1004)))
            for i in range(256):
                self.assertEqual(m.call(CHECK, VARS, 0x3F00 + i), (expected[i // 8] >> (i % 8)) & 1)
            m.call(SET, VARS, 0x3FFF); expected[31] |= 128
            m.call(CLEAR, VARS, 0x3F00); expected[0] &= 254
            self.assertEqual(m.read(VARS + 0x2BC, 36), b'HF02' + expected)
            self.assertEqual(m.read(VARS + 0xAC0, 32), bytes(x ^ 255 for x in bank))

    def test_foreign_and_future_getter_never_returns_or_mutates(self):
        for lang in self.arms:
            for reservation in (b'FORE' + bytes(32), b'HF03' + bytes(32), bytes(35) + b'X'):
                for operation in (CHECK, SET, CLEAR):
                    m = self.machine(lang)
                    m.mu.mem_write(VARS + 0x2BC, reservation)
                    before = m.read(VARS, 0x1400)
                    m.call(operation, VARS, 0x3FC8)
                    self.assertEqual(m.events, ['reset'])
                    self.assertEqual(m.read(VARS, 0x1400), before)

    def test_continue_preflight_postreload_and_native_failure(self):
        # Execute native overlay36 caller AND native TryLoadOnContinue BOOL
        # propagation. Only delegated Training/Bag load and SDK reset are seams.
        from sgp12.rom import bl_decode
        for lang in self.arms:
            loader = bl_decode(0x02027AD6, self.arms[lang].leggi(0x02027AD6, 4))
            for stage in ('preflight', 'reload', 'native_failure', 'success'):
                for bad in (b'FORE' + bytes(32), b'HF03' + bytes(32)):
                    m = self.machine(lang); m.loader = loader
                    if stage == 'preflight': m.mu.mem_write(VARS + 0x2BC, bad)
                    if stage == 'reload':
                        fresh = bytearray(0x1400); fresh[0x2BC:0x2E0] = bad
                        m.reload = bytes(fresh)
                    if stage == 'native_failure': m.load_result = 0
                    before = m.read(VARS, 0x1400)
                    save = m.read(SAVE, 0x100)
                    m.call(0x021E5BB4, 75, SAVE)
                    if stage == 'success':
                        self.assertEqual(m.events, ['load', 'postload', 'postload'])
                        self.assertEqual(m.read(VARS + 0x2BC, 4), b'HF02')
                    else:
                        self.assertEqual(m.events, (['load'] if stage != 'preflight' else []) + ['reset'])
                        self.assertEqual(m.read(SAVE, 0x100), save)  # no newgame/save marker writes
                        self.assertEqual(m.read(VARS, 0x1400), m.reload or before)

    def test_hf01_load_snapshots_all_24_gates_without_touching_chatot(self):
        from sgp12.rom import bl_decode
        for lang, arm in self.arms.items():
            m = self.machine(lang)
            m.loader = bl_decode(0x02027AD6, arm.leggi(0x02027AD6, 4))
            state = bytearray((i * 31 + 9) % 256 for i in range(0x1400))
            bank = bytes((i * 13 + 5) % 256 for i in range(32))
            state[0x2BC:0x2E0] = b'HF01' + bank
            chatot = bytearray((i * 29 + 7) % 256 for i in range(1004))
            for index, offset in enumerate(CHATOT_OFFSETS):
                struct.pack_into('<H', chatot, offset, 0 if index % 3 == 0 else 0x8888)
            m.reload, m.reload_chatot = bytes(state), bytes(chatot)
            m.call(0x021E5BB4, 75, SAVE)
            self.assertEqual(m.events, ['load', 'postload', 'postload'])
            self.assertEqual(m.read(VARS + 0x2BC, 36), b'HF02' + expected_bank(bank, chatot))
            self.assertEqual(m.read(CHATOT, 1004), bytes(chatot))

    def test_real_new_game_setvar_before_high_flag(self):
        for lang in self.arms:
            m = self.machine(lang)
            legacy = bytes((i * 7 + 1) % 256 for i in range(32))
            m.mu.mem_write(VARS + 0xAC0, legacy)
            m.put(CTX + 8, SCRIPT)
            m.put(CTX + 0x80, FS)
            m.mu.mem_write(SCRIPT, struct.pack('<HH', 0x6130, 2))
            self.assertEqual(m.call(SET_VAR, CTX), 0)
            self.assertEqual(m.events, [])
            self.assertEqual(m.read(CTX + 8, 4), struct.pack('<I', SCRIPT + 4))
            self.assertEqual(m.read(VARS + 0x2BC, 4), b'HF02')
            self.assertEqual(m.read(VARS + 0xAC0, 32), legacy)
            self.assertEqual(m.call(VAR_GET, FS, 0x6130), 2)

    def test_real_setvar_and_field_varget_redirect_only_the_finite_family(self):
        def set_script(machine, variable, value):
            machine.put(CTX + 8, SCRIPT)
            machine.put(CTX + 0x80, FS)
            machine.mu.mem_write(SCRIPT, struct.pack('<HH', variable, value))
            result = machine.call(SET_VAR, CTX)
            self.assertEqual(machine.read(CTX + 8, 4), struct.pack('<I', SCRIPT + 4))
            return result

        for lang, arm in self.arms.items():
            m = self.machine(lang)
            m.mu.mem_write(VARS + 0x2BC, b'HF02' + bytes(32))
            chatot = bytes((i * 17 + 9) % 256 for i in range(1004))
            m.mu.mem_write(CHATOT, chatot)
            for variable in FAMILY_IDS:
                with self.subTest(language=lang, variable=hex(variable)):
                    self.assertEqual(m.call(VAR_GET, FS, variable), 0)
                    self.assertEqual(set_script(m, variable, 2), 0)
                    self.assertEqual(m.call(VAR_GET, FS, variable), 2)
                    self.assertEqual(set_script(m, variable, 0), 0)
                    self.assertEqual(m.call(VAR_GET, FS, variable), 0)
            self.assertEqual(m.read(CHATOT, 1004), chatot)
            self.assertNotIn('assert', m.events)

            # Execute the real coordinate-event reader: exact zero opens the
            # gate, the historical SetVar value 2 closes it.
            m.player = (16, 12)
            m.put(FS + 0x40, CTX)
            coord_address = SCRIPT + 0x100
            coord = struct.pack('<HhhHHHHH', 777, 16, 12, 1, 1, 0, 0, 0x6131)
            m.mu.mem_write(coord_address, coord)
            self.assertEqual(m.call(0x0203DE04, FS, coord_address, 1), 777)
            set_script(m, 0x6131, 2)
            self.assertEqual(m.call(0x0203DE04, FS, coord_address, 1), 0xFFFF)
            set_script(m, 0x6131, 0)
            self.assertEqual(m.read(CHATOT, 1004), chatot)

            # A healthy native variable still takes the complete original path.
            original = Machine(arm)
            original.mu.mem_write(VARS + 0x2BC, b'HF02' + bytes(32))
            for machine in (original, m):
                machine.mu.mem_write(VARS + 2 * (0x415D - 0x4000), struct.pack('<H', 0x1234))
            self.assertEqual(original.call(VAR_GET, FS, 0x415D), m.call(VAR_GET, FS, 0x415D))
            set_script(original, 0x415D, 0x5678)
            set_script(m, 0x415D, 0x5678)
            self.assertEqual(original.read(VARS, 0x44C), m.read(VARS, 0x44C))

            bad = self.machine(lang)
            bad.mu.mem_write(VARS + 0x2BC, b'HF02' + bytes(32))
            before = bad.read(VARS, 0x1400), bad.read(CHATOT, 1004)
            bad.put(CTX + 8, SCRIPT); bad.put(CTX + 0x80, FS)
            bad.mu.mem_write(SCRIPT, struct.pack('<HH', 0x612E, 1))
            bad.call(SET_VAR, CTX)
            self.assertEqual(bad.events, ['reset'])
            self.assertEqual((bad.read(VARS, 0x1400), bad.read(CHATOT, 1004)), before)

    def test_original_zero_low_temp_and_outlier_reads_are_preserved(self):
        # Out-of-domain E3EE/E3F3 are existing hidden-item scanner reads.
        # Preserve original behavior rather than introduce a reset there.
        for lang, arm in self.arms.items():
            for flag in (0, 1, 7, 8, 0xAA0, 0xB5F, 0xB60, 0x3EFF,
                         0x4000, 0x403F, 0x4040, 0xE3EE, 0xE3F3, 0xFFFF):
                a, b = Machine(arm), self.machine(lang)
                pattern = bytes((i * 17 + 3) % 256 for i in range(0x3000))
                for m in (a, b):
                    m.mu.mem_write(VARS, pattern)
                    m.mu.mem_write(0x021D4170, pattern[:0x1800])
                self.assertEqual(a.call(CHECK, VARS, flag), b.call(CHECK, VARS, flag))
                self.assertEqual(a.events, b.events)
                self.assertEqual(a.read(VARS, 0x3000), b.read(VARS, 0x3000))
                if flag < 0xB60 or 0x4000 <= flag < 0x4040:
                    for operation in (SET, CLEAR):
                        a.call(operation, VARS, flag); b.call(operation, VARS, flag)
                        self.assertEqual(a.read(VARS, 0x3000), b.read(VARS, 0x3000))
                        self.assertEqual(a.read(0x021D4170, 8), b.read(0x021D4170, 8))

    def test_native_daily_map_resets_and_newgame_initialization(self):
        for lang in self.arms:
            m = self.machine(lang)
            m.mu.mem_write(VARS, bytes([0xA5]) * 0x1400)
            m.mu.mem_write(VARS + 0x2BC, b'HF02' + bytes(range(32)))
            before = m.read(VARS, 0x1400)
            m.call(0x02040438, FS)
            m.call(0x02040470, FS)
            expected = bytearray(before)
            expected[:64] = bytes(64)
            expected[0x2E0:0x2E8] = bytes(8)
            expected[0x434:0x44C] = bytes(24)
            self.assertEqual(m.read(VARS, 0x1400), bytes(expected))
            m.call(0x020503C0, VARS)  # native whole-struct init, no high access
            self.assertEqual(m.read(VARS, 0x44C), bytes(0x44C))
            self.assertEqual(m.read(VARS + 0x44C, 0x1400 - 0x44C), before[0x44C:])
            # Pal Pad initialization completes later; lazy access must see that
            # final bank, not the previous save's uninitialized neighbor bytes.
            m.mu.mem_write(VARS + 0xAC0, bytes(32))
            self.assertEqual(m.call(CHECK, VARS, 0x3FC8), 0)
            self.assertEqual(m.read(VARS + 0x2BC, 36), b'HF02' + bytes(32))

    def test_guarded_installer_readback_and_mutants(self):
        from sgp13 import event_flags
        import copy
        for lang, original in self.arms.items():
            arm = copy.copy(original); arm.raw = bytearray(original.raw)
            from sgp12.rom import bl_decode
            delegated = bl_decode(0x02027AD6, original.leggi(0x02027AD6, 4)) | 1
            with self.assertRaisesRegex(ValueError, 'composition mismatch'):
                event_flags.prepare(arm, self.temp.name, lang, delegated + 2)
            receipt = event_flags.install(arm, lang, delegated, self.temp.name)
            event_flags.verify(arm, receipt, self.temp.name)
            for address in (0x023CF900, 0x023CFE80, 0x023CFE8A, 0x023CFE94,
                            0x023CFEA8, 0x023CFEF0, 0x0205045C, 0x02027AD4,
                            0x020403AC, 0x02040F14):
                old = arm.leggi(address, 1)
                arm.scrivi(address, bytes([old[0] ^ 1]))
                with self.assertRaises(ValueError): event_flags.verify(arm, receipt, self.temp.name)
                arm.scrivi(address, old)
            with self.assertRaises(ValueError):
                event_flags.prepare(arm, self.temp.name, lang)

    def test_exact_installed_hf01_candidate_upgrades_in_memory(self):
        from sgp13 import event_flags
        import copy
        for lang, installed in self.installed_arms.items():
            successor = installed.u32(event_flags.CONFIG)
            writes, receipt = event_flags.prepare_upgrade(
                installed, self.temp.name, lang, successor)
            upgraded = copy.copy(installed); upgraded.raw = bytearray(installed.raw)
            before = bytes(upgraded.raw)
            for address, payload in writes.items():
                upgraded.scrivi(address, payload)
            self.assertEqual(event_flags.verify(upgraded, receipt, self.temp.name)['verified'], True)
            changed = set()
            for address, payload in writes.items():
                at = upgraded.off(address, len(payload))
                changed.update(range(at, at + len(payload)))
            self.assertTrue(all(a == b or i in changed for i, (a, b) in enumerate(zip(before, upgraded.raw))))


if __name__ == '__main__':
    unittest.main()
