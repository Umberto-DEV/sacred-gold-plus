"""Class B machine-code save caller tests; graphics/flash seams are explicit.

Supply SGP_SAVE_UI_CANDIDATES and SGP_PRET_SOURCE. These tests execute the
actual candidate dispatcher, Field BOOL conversion, composed refusal and native
rollback. They do not establish rendered pixels, physical I/O or raw-save
compatibility. Private ROMs and extracted bytes are never test assets.
"""
import binascii
import json
import os
from pathlib import Path
import struct
import unittest
import zlib

from sgp12.rom import Arm9, Rom

CANDIDATES = os.environ.get('SGP_SAVE_UI_CANDIDATES')
PRET = os.environ.get('SGP_PRET_SOURCE')
DATA = 0x02280000
FS = DATA + 0x100
SAVE = 0x02290000
BAG = 0x023DD700
TRAIN = 0x023D3000
STACK = 0x023FF000
STOP = 0x023EF000


class NativeTouchSave:
    """Native caller/dispatcher with controlled rendering and storage seams."""
    def __init__(self, path, symbols, mode='foreign', image=None):
        from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB, UC_HOOK_CODE
        from unicorn import arm_const as reg
        self.reg = reg
        self.mode = mode
        self.events = []
        self.reads = []
        self.writes = []
        self.sleep = 0
        self.native_calls = 0
        self.field_results = []
        self.raw_results = []
        self.text_active = False
        self.symbols = symbols
        self.a = Arm9(path)
        if image is not None:
            # This patch leaves ARM9 segments intact; retain their independently
            # parsed file map and substitute only the complete new cartridge.
            self.a.raw = bytearray(image)
        self.mu = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
        self.mu.mem_map(0x01FF0000, 0x410000)
        for addr, offset, size in self.a.segmenti:
            if 0x01FF0000 <= addr and addr + size <= 0x02400000:
                self.mu.mem_write(addr, bytes(self.a.raw[offset:offset + size]))
        rom = Rom(self.a.raw)
        for oid in (1, 30):
            record, _, overlay = rom.immagine_overlay(oid)
            self.mu.mem_write(record['ram'], bytes(overlay))
        self.put(DATA + 0x1c, FS)
        self.put(FS + 12, SAVE)
        self.mu.mem_write(FS + 0xd2, b'\x02')
        self.put(DATA + 12, 12)
        self.put(DATA + 0x64, 0x02281040)
        self.put(DATA + 0x68, 0x02281080)
        self.put(SAVE, 1)
        self.put(SAVE + 4, 1)
        self.put(SAVE + 0x23010, 17)
        self.put(SAVE + 0x232BC, 0x10000)
        self.put(BAG, 0x43415042)
        self.put(BAG + 4, SAVE)
        self.put(BAG + 8, SAVE + 0x1000)
        self.put(TRAIN, 0x31544E52)
        self.put(TRAIN + 4, SAVE)
        self.put(TRAIN + 8, 1)
        self.put(TRAIN + 12, 1)
        self.mu.hook_add(UC_HOOK_CODE, self.hook)

    def put(self, address, value):
        self.mu.mem_write(address, struct.pack('<I', value))

    def get(self, address):
        return struct.unpack('<I', self.mu.mem_read(address, 4))[0]

    def ret(self, value=0):
        self.mu.reg_write(self.reg.UC_ARM_REG_R0, value)
        self.mu.reg_write(self.reg.UC_ARM_REG_PC, self.mu.reg_read(self.reg.UC_ARM_REG_LR))

    def hook(self, uc, address, size, user):
        a, b, c, d = [uc.reg_read(r) for r in (self.reg.UC_ARM_REG_R0,
                      self.reg.UC_ARM_REG_R1, self.reg.UC_ARM_REG_R2, self.reg.UC_ARM_REG_R3)]
        if address == 0x021f43f6:
            self.raw_results.append(a)
        if address in (0x021f43fc, 0x021f4400):
            self.field_results.append(a)
        if address == (self.symbols.get('training_save', 0) & ~1):
            self.events.append(('training_save',))
        if address in (0x021F4404, 0x0202C714, 0x02031084):
            self.ret()
        elif address == 0x02050590:
            self.ret(1)  # field task running; actual dispatcher selects state
        elif address == 0x021F6A9C:
            self.events.append(('field_return',))
            self.ret()
        elif address == 0x0201A4BC:
            self.sleep |= a
            self.ret()
        elif address == 0x0201A4CC:
            self.sleep &= ~a
            self.ret()
        elif address == 0x0201FF98:
            self.ret(binascii.crc_hqx(bytes(uc.mem_read(a, b)), 0xffff))
        elif address == 0x0202877C:
            self.reads.append((a, c))
            self.mu.mem_write(b, b'FOREIGN!' + bytes(c - 8))
            self.ret(1)  # real successful read of foreign ownership bytes
        elif address == 0x02028758:
            self.writes.append((a, c))
            raise AssertionError('refusal must not write')
        elif address == 0x020273F0 and self.mode == 'success_control':
            self.ret(2)  # caller TRUE-path control, not composed flash proof
        elif address == 0x02027C20:
            self.native_calls += 1
            raise AssertionError('foreign refusal must precede native writer')
        elif address in (0x021F2FF0, 0x0200F450):
            self.events.append(('movement_clear' if address == 0x021F2FF0 else 'spinner_clear', a))
            self.ret()
        elif address == 0x02016748 and self.mode == 'cancel':
            self.ret(2)
        elif address in (0x020169c0, 0x02016624, 0x02018410) and self.mode == 'cancel':
            self.ret()
        elif address == 0x02020094:
            self.ret(int(self.text_active))
        elif address == 0x02026380:
            self.events.append(('string_delete', a))
            self.ret()
        elif address in (0x0200e998, 0x0201D978, 0x0202AD3C, 0x020200A8,
                         0x020034DC, 0x020237BC):
            self.ret()
        elif address == 0x0200BBA0:
            self.events.append(('message', b))
            self.ret(0x02281000)
        elif address == 0x0200BC4C:
            self.events.append(('message', c))
            self.ret(0x02281000)
        elif address == 0x0200604C:
            self.events.append(('sound', a))
            self.ret()

    def tick(self):
        self.mu.reg_write(self.reg.UC_ARM_REG_R0, 0)
        self.mu.reg_write(self.reg.UC_ARM_REG_R1, DATA)
        self.mu.reg_write(self.reg.UC_ARM_REG_SP, STACK)
        self.mu.reg_write(self.reg.UC_ARM_REG_LR, STOP | 1)
        self.mu.emu_start(0x0225D701, STOP, count=2000000)
        assert self.mu.reg_read(self.reg.UC_ARM_REG_PC) == STOP
        assert self.mu.reg_read(self.reg.UC_ARM_REG_SP) == STACK

    def input(self, held=0, edge=0, touch=0, touch_edge=0):
        self.put(0x021d1150, held)
        self.put(0x021d1154, edge)
        self.mu.mem_write(0x021d1170, struct.pack('<HH', touch_edge, touch))

    def acknowledge(self, button='A'):
        # Deliberately hold speedup input through printing and entry to state17.
        self.input(held=3, edge=3, touch=1, touch_edge=1)
        self.text_active = True
        for _ in range(40):
            self.tick()
        assert self.get(DATA + 12) == 2
        self.text_active = False
        self.tick()
        assert self.get(DATA + 12) == 17
        for _ in range(40):
            self.tick()
        assert self.get(DATA + 20) == 0
        self.input()
        self.tick()
        assert self.get(DATA + 20) == 1
        self.input(held=0x400, edge=0x400)
        for _ in range(80):
            self.tick()
        assert self.get(DATA + 20) == 1
        before = self.events.count(('field_return',))
        self.input(held=1 if button == 'A' else 2 if button == 'B' else 0,
                   edge=1 if button == 'A' else 2 if button == 'B' else 0,
                   touch=int(button == 'touch'), touch_edge=int(button == 'touch'))
        self.tick()
        assert self.get(DATA + 20) == 2
        for _ in range(40):
            self.tick()
        assert self.events.count(('field_return',)) == before
        self.input()
        self.tick()
        assert self.events.count(('field_return',)) == before + 1
        for _ in range(4):
            self.tick()
        assert self.events.count(('field_return',)) == before + 1

    def fresh_app_boundary(self):
        # Only app allocation/setup is modeled. Native input/menu reopening is
        # a separate emulator gate; the actual dispatcher/state machine runs.
        self.put(DATA + 12, 12)
        self.put(DATA + 20, 0)
        self.put(DATA + 0x64, 0x02281040)
        self.put(DATA + 0x68, 0x02281080)
        self.mu.mem_write(FS + 0xd2, b'\x02')
        self.input()


class ComposedNativeTouchSave(NativeTouchSave):
    """Candidate writers with copied fixture state and synthetic successful I/O.

    Only SaveData and runtime data are copied from the old dump. Candidate code
    remains loaded from the new cartridge. The mismatch affects returned bytes
    after a successful write; it does not claim a returning hardware failure.
    """
    def __init__(self, path, symbols, language, fixture_root, image=None):
        super().__init__(path, symbols, 'composition', image)
        root = Path(fixture_root) / f'{language}-save'
        dump = (root / 'v8-saved.bin').read_bytes()
        if len(dump) != 0x400000:
            raise ValueError('expected a full private RAM data fixture')
        old_save = struct.unpack_from('<I', dump, TRAIN + 4 - 0x02000000)[0]
        if not 0x02000000 <= old_save < 0x023c0000:
            raise ValueError('invalid fixture SaveData pointer')
        self.mu.mem_write(SAVE, dump[old_save - 0x02000000:old_save - 0x02000000 + 0x2330c])
        self.mu.mem_write(BAG, dump[BAG - 0x02000000:BAG - 0x02000000 + 0x12c8])
        self.mu.mem_write(TRAIN, dump[TRAIN - 0x02000000:TRAIN - 0x02000000 + 0x1000])
        self.put(TRAIN + 4, SAVE)
        self.put(BAG + 4, SAVE)
        self.put(BAG + 8, self.get(BAG + 8) - old_save + SAVE)
        self.flash = bytearray((root / 'v8-saved.sav').read_bytes())
        if len(self.flash) != 0x80000:
            raise ValueError('expected a raw 512 KiB save fixture')
        self.original_flash = bytes(self.flash)
        self.mismatch = True
        self.native_writes = []
        self.assertions = []
        # Fixture identity is independently checked against its actual native
        # main footer and CCITT checksum before executing the candidate writer.
        main_size = self.get(SAVE + 0x232bc)
        footer = self.flash[main_size - 16:main_size]
        assert struct.unpack_from('<I', footer)[0] == 120
        assert struct.unpack_from('<H', footer, 14)[0] == binascii.crc_hqx(
            self.flash[:main_size - 16], 0xffff)
        assert self.get(SAVE + 0x23010) == 120
        assert self.get(SAVE + 0x23308) >> 16 == 0

    def hook(self, uc, address, size, user):
        a, b, c = [uc.reg_read(r) for r in (self.reg.UC_ARM_REG_R0,
                  self.reg.UC_ARM_REG_R1, self.reg.UC_ARM_REG_R2)]
        if address == 0x0202877c:
            self.reads.append((a, c))
            raw = bytes(self.flash[a:a + c])
            if self.mismatch and a == 0x70000 and c == 32 and self.writes:
                raw = bytes([raw[0] ^ 1]) + raw[1:]
            uc.mem_write(b, raw)
            self.ret(1)
        elif address in (0x02028758, 0x020287f8):
            raw = bytes(uc.mem_read(b, c))
            assert a + c <= len(self.flash)
            self.writes.append((a, c))
            if address == 0x020287f8:
                self.native_writes.append((a, c))
            self.flash[a:a + c] = raw
            self.ret(1)  # sync success, or successful async lock handle
        elif address == 0x02028874:
            self.put(c, 1)
            self.ret(1)  # async operation completed successfully
        elif address == 0x02027c20:
            self.native_calls += 1  # observe; execute the actual native body
        elif address in (0x0202d18c, 0x02028f98):
            self.ret(0)  # league reward census / RTC extras not under test
        elif address == 0x0202551c:
            self.assertions.append(uc.reg_read(self.reg.UC_ARM_REG_LR))
            raise AssertionError('native assertion during composed save')
        else:
            super().hook(uc, address, size, user)


@unittest.skipUnless(CANDIDATES and PRET, 'private candidate EN/IT ROMs and reference charmap not supplied')
class SaveUiRom(unittest.TestCase):
    def machine(self, language, mode='foreign'):
        root = Path(CANDIDATES)
        path = root / f'mew-fixed-{language}.nds'
        symbols = json.loads(path.with_name(f'mew-fixed-{language}-training.json').read_text())['symbols']
        image = None
        if not os.environ.get('SGP_SAVE_UI_UNPATCHED'):
            from sgp13 import save_ui
            image, _ = save_ui.apply(path.read_bytes(), language, Path(PRET) / 'charmap.txt')
        if mode == 'composition':
            return ComposedNativeTouchSave(path, symbols, language,
                                          os.environ['SGP_SAVE_UI_ACTIVE_DUMPS'], image)
        return NativeTouchSave(path, symbols, mode, image)

    def test_real_foreign_training_refusal_never_claims_saved(self):
        for language in ('EN', 'IT'):
            with self.subTest(language=language):
                machine = self.machine(language)
                machine.tick()  # actual state12 -> Field -> composed refusal
                self.assertEqual(machine.field_results, [0])
                self.assertEqual(machine.raw_results, [3])
                self.assertIn(('training_save',), machine.events)
                self.assertEqual(machine.get(BAG + 0x12c4), 2)
                self.assertEqual(machine.get(SAVE + 0x23010), 17)
                self.assertEqual(machine.get(SAVE + 0x23308) >> 16, 0)
                self.assertEqual(machine.sleep, 0)
                self.assertEqual(machine.writes, [])
                self.assertEqual(machine.native_calls, 0)
                machine.tick()  # real dispatcher invokes selected outcome
                self.assertNotIn(('message', 16), machine.events,
                                 'Field FALSE must not display the saved message')
                self.assertEqual([e[0] for e in machine.events].count('movement_clear'), 1)
                self.assertEqual([e[0] for e in machine.events].count('spinner_clear'), 1)
                for _ in range(80):
                    machine.tick()
                self.assertNotIn(('sound', 1562), machine.events)
                self.assertNotIn(('field_return',), machine.events,
                                 'failure requires deliberate acknowledgment')

    def test_true_preserves_native_success_feedback_and_close_delay(self):
        for language in ('EN', 'IT'):
            with self.subTest(language=language):
                machine = self.machine(language, 'success_control')
                machine.tick()
                self.assertEqual(machine.field_results, [1])
                self.assertEqual(machine.raw_results, [2])
                self.assertEqual(machine.get(DATA + 12), 13)
                machine.tick()
                self.assertIn(('message', 16), machine.events)
                self.assertEqual(machine.get(DATA + 12), 2)
                machine.text_active = True
                for _ in range(40):
                    machine.tick()
                self.assertEqual(machine.get(DATA + 12), 2)
                self.assertNotIn(('sound', 1562), machine.events)
                machine.text_active = False
                machine.tick()
                self.assertEqual(machine.get(DATA + 12), 14)
                machine.tick()
                self.assertEqual(machine.events.count(('sound', 1562)), 1)
                for _ in range(30):
                    machine.tick()
                self.assertNotIn(('field_return',), machine.events)
                machine.tick()
                self.assertEqual(machine.events.count(('field_return',)), 1)
                self.assertEqual(machine.events.count(('message', 16)), 1)
                self.assertEqual([e[0] for e in machine.events].count('movement_clear'), 1)
                self.assertEqual([e[0] for e in machine.events].count('spinner_clear'), 1)

    def test_repeated_refusal_requires_fresh_ack_and_releases_each_resource_once(self):
        for language in ('EN', 'IT'):
            for button in ('A', 'B', 'touch'):
                with self.subTest(language=language, button=button):
                    machine = self.machine(language)
                    for attempt in (1, 2):
                        machine.tick()
                        self.assertEqual(machine.get(DATA + 12), 16)
                        machine.tick()
                        machine.acknowledge(button)
                        self.assertEqual(machine.events.count(('message', 117)), attempt)
                        self.assertEqual([e[0] for e in machine.events].count('movement_clear'), attempt)
                        self.assertEqual([e[0] for e in machine.events].count('spinner_clear'), attempt)
                        self.assertEqual([e[0] for e in machine.events].count('string_delete'), attempt)
                        self.assertEqual(machine.writes, [])
                        self.assertEqual(machine.get(SAVE + 0x23010), 17)
                        self.assertEqual(machine.sleep, 0)
                        self.assertNotIn(('message', 16), machine.events)
                        self.assertNotIn(('sound', 1562), machine.events)
                        machine.fresh_app_boundary()

    @unittest.skipUnless(os.environ.get('SGP_SAVE_UI_ACTIVE_DUMPS'),
                         'private active SaveData/raw fixtures not supplied')
    def test_partial_readback_refusal_then_actual_composed_native_commit(self):
        for language in ('EN', 'IT'):
            with self.subTest(language=language):
                machine = self.machine(language, 'composition')
                original = bytes(machine.flash)
                machine.tick()
                self.assertEqual(machine.field_results, [0])
                self.assertEqual(machine.raw_results, [3])
                self.assertEqual(machine.get(BAG + 0x12c4), 5)  # one verified Bag copy
                self.assertEqual(machine.writes, [(0x70000, 452), (0x70200, 452)])
                self.assertEqual(machine.native_calls, 0)
                self.assertEqual(machine.native_writes, [])
                self.assertEqual(machine.get(SAVE + 0x23010), 120)
                self.assertEqual(machine.get(SAVE + 0x23308) >> 16, 0)
                self.assertEqual(machine.sleep, 0)
                machine.tick()
                self.assertNotIn(('message', 16), machine.events)
                machine.acknowledge()
                machine.mismatch = False  # remove transient readback seam only
                machine.fresh_app_boundary()
                machine.tick()
                self.assertEqual(machine.field_results, [0, 1])
                self.assertEqual(machine.raw_results, [3, 2])
                self.assertEqual(machine.native_calls, 1)
                self.assertEqual(machine.get(SAVE + 0x23010), 121)
                self.assertEqual(machine.get(SAVE + 0x23308) >> 16, 1)
                self.assertEqual(machine.sleep, 0)
                self.assertEqual(machine.assertions, [])
                self.assertEqual(machine.native_writes,
                                 [(0x40000, 63000), (0x4f618, 16), (0x61700, 768), (0x61a00, 16)])
                machine.tick()  # original state13
                machine.tick()  # original state2 text completion
                machine.tick()  # original state14 success sound
                for _ in range(31):
                    machine.tick()
                self.assertEqual(machine.events.count(('message', 16)), 1)
                self.assertEqual(machine.events.count(('sound', 1562)), 1)
                self.assertEqual(machine.events.count(('message', 117)), 1)
                self.assertEqual(machine.events.count(('field_return',)), 2)
                self.assertEqual([e[0] for e in machine.events].count('movement_clear'), 2)
                self.assertEqual([e[0] for e in machine.events].count('spinner_clear'), 2)
                size = machine.get(SAVE + 0x232bc)
                main = bytes(machine.flash[0x40000:0x40000 + size])
                main_crc = binascii.crc_hqx(main[:-16], 0xffff)
                self.assertEqual(struct.unpack_from('<II', main, size - 16), (121, size))
                self.assertEqual(struct.unpack_from('<H', main, size - 2)[0], main_crc)
                pc_start = 0x40000 + machine.get(SAVE + 0x232c4)
                pc_size = machine.get(SAVE + 0x232c8)
                pc = bytes(machine.flash[pc_start:pc_start + pc_size])
                self.assertEqual(struct.unpack_from('<II', pc, pc_size - 16), (121, pc_size))
                self.assertEqual(struct.unpack_from('<H', pc, pc_size - 2)[0],
                                 binascii.crc_hqx(pc[:-16], 0xffff))
                for address, length, magic in ((0x70000, 452, b'B252'), (0x70200, 452, b'B252'),
                                               (0x71000, 256, b'TNR1'), (0x71200, 256, b'TNR1')):
                    record = bytes(machine.flash[address:address + length])
                    self.assertEqual(record[:4], magic)
                    self.assertEqual(struct.unpack_from('<I', record, 8)[0], 121)
                    self.assertEqual(struct.unpack_from('<H', record, 12)[0], main_crc)
                    self.assertEqual(struct.unpack_from('<I', record, length - 4)[0], zlib.crc32(record[:-4]))
                self.assertEqual(machine.flash[0x70010:0x701c0], original[0x30010:0x301c0])
                for start, species in ((64, 9), (144, 26)):
                    old = original[0x31000 + start:0x31000 + start + 80]
                    new = bytes(machine.flash[0x71000 + start:0x71000 + start + 80])
                    self.assertEqual(struct.unpack_from('<H', new, 12)[0], species)
                    self.assertEqual(new[:32], old[:32])
                    self.assertEqual(new[48:], old[48:])
                    self.assertGreaterEqual(struct.unpack_from('<Q', new, 40)[0],
                                            struct.unpack_from('<Q', old, 40)[0])
                # Previous active bank stays intact: no erasing/repairing foreign
                # ownership or committing native data on the partial attempt.
                self.assertEqual(machine.flash[:0x2f000], original[:0x2f000])
                self.assertEqual(machine.flash[0x2f020:0x40000], original[0x2f020:0x40000])

    def test_native_cancel_and_not_my_save_keep_their_original_exit_paths(self):
        for language in ('EN', 'IT'):
            for state in (4, 7):
                with self.subTest(language=language, state=state):
                    b = self.machine(language, 'cancel')
                    b.put(DATA + 12, state)
                    b.tick()
                    self.assertEqual(b.events, [('field_return',)])
                    self.assertEqual(b.field_results, [])
                    self.assertEqual(b.writes, [])
            b = self.machine(language)
            b.put(DATA + 12, 8)
            for _ in range(34):
                b.tick()
            self.assertEqual([e for e in b.events if e[0] in ('message', 'sound', 'field_return')],
                             [('message', 20), ('field_return',)])
            self.assertFalse(any(e[0] in ('spinner_clear', 'movement_clear') for e in b.events))
            self.assertEqual(b.field_results, [])

    def test_actual_rom_identity_geometry_and_readback_reject_meaningful_mutants(self):
        import ndspy.rom
        import ndspy.narc
        import ndspy.codeCompression
        from sgp12.blz import blz_comprimi_ottimo
        from sgp13 import save_ui
        for language in ('EN', 'IT'):
            with self.subTest(language=language):
                before = (Path(CANDIDATES) / f'mew-fixed-{language}.nds').read_bytes()
                charmap = Path(PRET) / 'charmap.txt'
                after, receipt = save_ui.apply(before, language, charmap)
                original = ndspy.rom.NintendoDSRom(before)
                changed = ndspy.rom.NintendoDSRom(after)
                raw = ndspy.codeCompression.decompress(changed.files[30])
                old = ndspy.codeCompression.decompress(original.files[30])
                self.assertLessEqual(len(raw) - len(old), 512)
                self.assertLessEqual(len(changed.files[30]), 2048)
                self.assertEqual(len(raw) % 32, 0)
                self.assertEqual(raw[:0x7b0], old[:0x7b0])
                self.assertEqual(raw[0x7b4:1984], old[0x7b4:1984])
                self.assertEqual(receipt['message_widths'], [63, 159] if language == 'EN' else [134, 188])
                self.assertEqual([i for i, (a, b) in enumerate(zip(original.files, changed.files)) if a != b],
                                 [30, original.filenames.idOf('a/0/2/7')])
                for image, lang in ((after, language), (before, 'IT' if language == 'EN' else 'EN')):
                    with self.assertRaisesRegex(ValueError, 'preimage'):
                        save_ui.apply(image, lang, charmap)
                fat = struct.unpack_from('<I', after, 0x48)[0]
                y9 = struct.unpack_from('<I', after, 0x50)[0] + 30 * 32
                start = struct.unpack_from('<I', after, fat + 30 * 8)[0]
                symbols = receipt['symbols']
                from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB
                code_start = 0x0225dce8 - 0x0225d520
                ins = list(Cs(CS_ARCH_ARM, CS_MODE_THUMB).disasm(raw[code_start:], 0x0225dce8))
                first_branch = next(i.address for i in ins if i.mnemonic == 'beq')
                message = next(i.address for i in ins if i.mnemonic == 'movs' and i.op_str == 'r1, #0x75')
                failure_state = next(i.address for i in ins if i.mnemonic == 'movs' and i.op_str == 'r0, #0x11')
                cleanup = raw.index(struct.pack('<I', 0x021f2ff1), 1992)
                # Flip the actual FALSE branch, message ID, cleanup callee,
                # after-text state, and final release branch independently.
                ack_blob = raw[(symbols['sgp_saveui_ack'] & ~1) - 0x0225d520:]
                ack_ins = list(Cs(CS_ARCH_ARM, CS_MODE_THUMB).disasm(
                    ack_blob, symbols['sgp_saveui_ack'] & ~1))
                ack_release = [i.address for i in ack_ins if i.mnemonic == 'beq'][-1]
                sites = {'state12': 0x7b0,
                         'result_branch': first_branch - 0x0225d520 + 1,
                         'cleanup_callee': cleanup,
                         'message117': message - 0x0225d520,
                         'after_text_state17': failure_state - 0x0225d520,
                         'ack_release_branch': ack_release - 0x0225d520 + 1}
                for name, offset in sites.items():
                    with self.subTest(language=language, mutant=name):
                        damaged = bytearray(raw)
                        damaged[offset] ^= 1
                        compressed = blz_comprimi_ottimo(bytes(damaged))
                        if isinstance(compressed, tuple):
                            compressed = compressed[0]
                        mutant = bytearray(after)
                        mutant[start:start + len(compressed)] = compressed
                        struct.pack_into('<I', mutant, fat + 30 * 8 + 4, start + len(compressed))
                        struct.pack_into('<I', mutant, y9 + 28, 0x1000000 | len(compressed))
                        with self.assertRaisesRegex(ValueError, 'readback'):
                            save_ui.readback(before, bytes(mutant), language, charmap)
                foreign = bytearray(before)
                _, end = struct.unpack_from('<II', before, fat + 30 * 8)
                foreign[end] = 1
                with self.assertRaisesRegex(ValueError, 'preimage'):
                    save_ui.apply(bytes(foreign), language, charmap)
                # Corrupt an untouched original overlay byte on input.
                foreign = bytearray(before)
                foreign[start + 5] ^= 1
                with self.assertRaises((ValueError, AssertionError)):
                    save_ui.apply(bytes(foreign), language, charmap)


if __name__ == '__main__':
    unittest.main()
