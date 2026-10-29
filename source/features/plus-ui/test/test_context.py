"""Run the actual ARM helper against native-window API seams and old pixel data."""
import struct
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from sgp13.plus_ui import compile_native, version_title, module, ROOT, BASE, LABELS
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB, UC_HOOK_CODE
from unicorn.arm_const import *

APP, STRING, PIXELS, SP, STOP = 0x02210000, 0x02211000, 0x02212000, 0x02300000, 0x02001000
REGS = (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3)


class MigrationTextTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        codec = module(ROOT / 'features/options/tools/codifica_testo.py', 'migration_test_codec')
        table, _ = codec.carica_charmap()
        table['-'] = 0x1be  # pinned pret charmap: version suffix, absent in fallback
        cls.encode = staticmethod(lambda text: codec.codifica(text, table))

    def strings(self, bank):
        result = []
        for index in range(29):
            offset = int.from_bytes(bank[index * 2:index * 2 + 2], 'little')
            self.assertTrue(58 <= offset < len(bank) and offset % 2 == 0)
            words = []
            for position in range(offset, len(bank), 2):
                word = struct.unpack_from('<H', bank, position)[0]
                words.append(word)
                if word == 0xffff:
                    break
            else:
                self.fail('rebuilt string has no terminator')
            result.append(words)
        return result

    def baseline(self, language):
        # The shipped intermediate table has the same IDs and note. Prepare
        # its existing title storage as the 1.2.5 stage does, without rebuilding.
        bank = bytearray((ROOT / f'sgp12/build/opzioni/testi-{language}.bin').read_bytes())
        bank[:2] = bank[40:42]
        offset = int.from_bytes(bank[40:42], 'little')
        words = self.encode('Sacred Gold Plus 1.2.5')
        bank[offset:offset + len(words) * 2] = struct.pack('<%dH' % len(words), *words)
        return bytes(bank)

    def test_rebuilt_migration_bank_changes_only_titles_and_english_note(self):
        for language, note in (('EN', 'Change them in OPTIONS with SELECT.'),
                               ('IT', 'Si cambiano dalle OPZIONI con SELECT.')):
            with self.subTest(language=language):
                before = self.baseline(language)
                after = version_title(before, self.encode, language)
                old, new = self.strings(before), self.strings(after)
                self.assertEqual(len(after), 1008)
                self.assertEqual(new[25], self.encode(note))
                self.assertEqual(new[0], self.encode('Sacred Gold Plus 1.3-dev'))
                self.assertEqual(new[20], new[0])
                changed = {0, 20, 25} if language == 'EN' else {0, 20}
                self.assertEqual({i for i in range(29) if old[i] != new[i]}, changed)
                for index in set(range(29)) - changed:
                    self.assertEqual(new[index], old[index])

    def test_unknown_migration_note_preimage_is_rejected(self):
        for language in ('EN', 'IT'):
            with self.subTest(language=language):
                before = bytearray(self.baseline(language))
                offset = int.from_bytes(before[50:52], 'little')
                struct.pack_into('<H', before, offset, 0x12b)
                with self.assertRaisesRegex(ValueError, 'Plus migration note preimage'):
                    version_title(bytes(before), self.encode, language)

    def test_wrong_or_unknown_language_is_rejected(self):
        for language in ('IT', 'DE'):
            with self.subTest(language=language):
                with self.assertRaises(ValueError):
                    version_title(self.baseline('EN'), self.encode, language)

    def test_malformed_note_offset_and_terminator_are_rejected(self):
        for offset in (0, 59, 1008):
            with self.subTest(offset=offset):
                before = bytearray(self.baseline('EN'))
                struct.pack_into('<H', before, 50, offset)
                with self.assertRaisesRegex(ValueError, 'Plus string offset'):
                    version_title(bytes(before), self.encode, 'EN')
        before = bytearray(self.baseline('EN'))
        offset = int.from_bytes(before[50:52], 'little')
        before[offset:] = bytes(len(before) - offset)
        with self.assertRaisesRegex(ValueError, 'Plus string terminator'):
            version_title(bytes(before), self.encode, 'EN')


class ContextTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.main, cls.symbols, cls.code = compile_native(Path(cls.tmp.name))

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def invoke(self, setting=0, failure=None, frame=True, app=True, printer="none"):
        uc = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
        uc.mem_map(0x02000000, 0x400000)
        uc.mem_write(BASE, self.code)
        labels = bytearray(20)
        expected = []
        for index in range(10):
            text = [65+index, 0xffff]
            struct.pack_into('<H', labels, index*2, len(labels))
            labels += struct.pack('<2H', *text)
            expected.append(text[:-1])
        uc.mem_write(LABELS, bytes(labels))
        data = bytearray(0x32c)
        struct.pack_into("<I", data, 0x324, STRING+0x200)
        data[0x328] = {"invalid8":8,"invalid255":255}.get(printer,3)
        struct.pack_into('<I', data, 0, 40)
        # Native frame is window index2. Index3 is the lower Quit button.
        for index in range(5):
            bg, width, height = (5, 27, 4) if index == 2 and frame else (1, 7, 3)
            struct.pack_into('<IBBBBBBHI', data, 0x34+index*16,
                             APP+0x200, bg, 2, 19, width, height, 12, 1, APP+0x400+index*64)
        uc.mem_write(APP, bytes(data))
        task, printer_data, table = APP+0x800, APP+0x900, 0x021d1f74
        active = printer in ('own','foreign','null_data')
        uc.mem_write(table+12,struct.pack('<I',task if active else 0))
        uc.mem_write(table+20,struct.pack('<I',task+0x40)) # unrelated slot must survive
        uc.mem_write(printer_data+4,struct.pack('<I',APP+0x54 if printer=='own' else APP+0x64))
        original = bytearray(uc.mem_read(APP, 0x600))
        calls = []
        def native(machine, address, size, unused):
            r = [machine.reg_read(reg) for reg in REGS]
            stack = lambda n: struct.unpack('<%dI' % n, machine.mem_read(machine.reg_read(UC_ARM_REG_SP), n*4))
            ret = 0
            if address == STOP:
                machine.emu_stop(); return
            if address == 0x0201f988:
                self.assertEqual(r[0],task)
                calls.append('task_data');ret = 0 if printer=='null_data' else printer_data
            elif address == 0x021e61a8:
                self.assertEqual(printer,'own','must not settle a foreign printer')
                self.assertEqual(r[:3],[APP,STRING+0x200,1])
                calls.append('complete_preview')
                machine.mem_write(table+12,bytes(4))
                # Native completion intentionally finishes the original pixels.
                complete=bytes([0x5a])*64
                machine.mem_write(APP+0x480,complete)
                original[0x480:0x4c0]=complete
            elif address == 0x02026354:
                calls.append('string_new'); ret = 0 if failure == 'string' else STRING
                machine.mem_write(STRING, struct.pack('<HHI', 64, 0, 0x1234)+bytes(128))
            elif address == 0x0201d40c:
                extra = stack(5)
                calls.append(('window', r[2], r[3], *extra))
                # Actual frame parameters, not just whichever source the code chose.
                self.assertEqual((r[2], r[3], *extra), (5,2,19,27,4,12,1))
                if failure != 'window':
                    machine.mem_write(r[1], struct.pack('<IBBBBBBHI',r[0],r[2],r[3],*extra,PIXELS))
            elif address == 0x0201d978:
                calls.append('fill')
            elif address == 0x020200fc:
                n = struct.unpack('<H', machine.mem_read(r[2]+2,2))[0]
                words = list(struct.unpack('<%dH'%n,machine.mem_read(r[2]+8,n*2)))
                calls.append(('print',r[3],stack(1)[0],words))
            elif address == 0x0201d578:
                calls.append('copy')
            elif address == 0x0201d520:
                calls.append('remove')
            elif address == 0x02026380:
                calls.append('string_delete')
            else:
                return
            machine.reg_write(UC_ARM_REG_R0,ret)
            machine.reg_write(UC_ARM_REG_PC,machine.reg_read(UC_ARM_REG_LR))
        uc.hook_add(UC_HOOK_CODE,native)
        uc.reg_write(UC_ARM_REG_SP,SP)
        uc.reg_write(UC_ARM_REG_LR,STOP|1)
        uc.reg_write(UC_ARM_REG_R0,APP if app else 0)
        uc.reg_write(UC_ARM_REG_R1,setting)
        uc.emu_start(BASE|1,STOP,count=20000)
        self.assertEqual(uc.reg_read(UC_ARM_REG_PC),STOP)
        self.assertEqual(uc.reg_read(UC_ARM_REG_SP),SP)
        self.assertEqual(bytes(uc.mem_read(APP,0x600)),bytes(original),'native completed pixels and window fields must survive for close')
        self.assertEqual(struct.unpack('<I',uc.mem_read(table+20,4))[0],task+0x40)
        if active and 'complete_preview' not in calls:
            self.assertEqual(struct.unpack('<I',uc.mem_read(table+12,4))[0],task)
        return calls,expected

    def test_all_settings_print_two_lines_into_upper_frame_without_touching_original(self):
        for setting in range(5):
            with self.subTest(setting=setting):
                calls,expected=self.invoke(setting)
                self.assertEqual([x for x in calls if isinstance(x,tuple) and x[0]=='print'],
                                 [('print',0,0,expected[setting*2]),('print',0,16,expected[setting*2+1])])
                self.assertEqual(calls[-3:],['copy','remove','string_delete'])

    def test_active_owned_preview_completes_before_context_copy(self):
        calls,_=self.invoke(printer='own')
        self.assertEqual(calls.count('complete_preview'),1)
        self.assertLess(calls.index('complete_preview'),calls.index('copy'))
        self.assertLess(calls.index('complete_preview'),next(i for i,x in enumerate(calls) if isinstance(x,tuple) and x[0]=='print'))

    def test_foreign_inactive_invalid_and_missing_printers_are_not_completed(self):
        for printer in ('foreign','none','invalid8','invalid255','null_data'):
            with self.subTest(printer=printer):
                calls,_=self.invoke(printer=printer)
                self.assertNotIn('complete_preview',calls)
                if printer in ('none','invalid8','invalid255'):self.assertNotIn('task_data',calls)

    def test_failed_context_allocation_keeps_active_preview_running(self):
        for failure in ('string','window'):
            with self.subTest(failure=failure):
                calls,_=self.invoke(printer='own',failure=failure)
                self.assertNotIn('complete_preview',calls)
                self.assertNotIn('copy',calls)

    def test_allocation_failures_release_only_acquired_resources_and_do_not_draw(self):
        calls,_=self.invoke(failure='string');self.assertEqual(calls,['string_new'])
        calls,_=self.invoke(failure='window');self.assertEqual(calls[0],'string_new');self.assertEqual(calls[-1],'string_delete')
        self.assertNotIn('copy',calls);self.assertNotIn('remove',calls)

    def test_absent_app_invalid_setting_or_unexpected_frame_is_inert(self):
        for kwargs in ({'app':False},{'setting':5},{'frame':False}):
            with self.subTest(kwargs=kwargs):self.assertEqual(self.invoke(**kwargs)[0],[])

if __name__ == '__main__': unittest.main()
