"""ROM-free production training + Bag ARM at their shared save boundary.

Only OS/flash, script-variable lookup, reward census and the final native
commit are seams. The actual Bag writer calls the actual training coordinator;
no native game code, ROM or save is loaded. Flash and RAM inputs are synthetic.
"""
import ctypes as C
import importlib.util
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest

from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB, UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2

SOURCE = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(SOURCE))
from sgp13.training import BASE, compile_native, entry_hook
from native_bench import ARGS, Bench, SAVE, STOP

BAG_ADDRESSES = (0x30000, 0x30200, 0x70000, 0x70200)
STATE = 0x023D3000


def bag_compiler():
    spec = importlib.util.spec_from_file_location(
        'save_composition_bag', SOURCE / 'features/capacita-borsa/tools/compila.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ComposedBench(Bench):
    def __init__(self, training_blob, training_symbols, bag_blob, bag_symbols):
        self.mu = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
        self.mu.mem_map(0x01FF0000, 0x410000)
        self.symbols = training_symbols
        self.bag_symbols = bag_symbols
        self.mu.mem_write(BASE, training_blob)
        self.mu.mem_write(0x023DBF00, bag_blob)
        self.mu.mem_write(STOP, b'\0\xbe')
        site = bag_symbols['sgp_cap_original_save'] & ~1
        self.mu.mem_write(site, entry_hook(site, training_symbols['training_save']))
        self.put(0x023D2F04, 0x12C4)
        self.heap = 0x02300000
        self.flash = bytearray(b'\xff' * 0x80000)
        self.writes, self.reads, self.charges = [], [], []
        self.cut = self.fail_address = None
        self.native_saves = self.assertions = 0
        self.pay_ok = True
        self.league = self.rtc_now = self.phone_buffers = None
        self.phone_messages = []
        self.mu.hook_add(UC_HOOK_CODE, self.hook)
        self.activate(0)
        self.put(STATE + 8, 0)
        self.put(SAVE + 0x23010, 17)
        self.put(SAVE + 0x232B8, 0)
        self.put(SAVE + 0x232BC, 0x10000)

    def hook(self, uc, address, size, user):
        a, b, c = [uc.reg_read(r) for r in
                   (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2)]
        if address == 0x0202877C:
            self.reads.append((a, b, c))
        if address == 0x020403AC:
            self.ret(struct.unpack('<H', uc.mem_read(ARGS + 0x1000 + 2 * (b - 0x8000), 2))[0]
                     if 0x8000 <= b <= 0x800C else 0)
        elif address == 0x02028E9C:
            self.ret(ARGS + 0x3000)
        elif address in (0x02028F98, 0x0202D18C):
            self.ret(0)
        else:
            super().hook(uc, address, size, user)

    def save(self):
        return self.call(self.bag_symbols['sgp_cap_save'], SAVE, ARGS)


class SaveComposition(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix='sgp-save-composition-')
        cls.addClassCleanup(cls.temp.cleanup)
        directory = Path(cls.temp.name)
        cls.training_blob, cls.training_symbols = compile_native(directory / 'training')
        compiler = bag_compiler()
        manifest = compiler.compila(directory / 'bag')
        cls.bag_blob = (directory / 'bag/blob.bin').read_bytes()
        cls.bag_symbols = {name: int(value, 16) for name, value in manifest['simboli'].items()}
        # Independent oracle: compile the writer's real predicates, never
        # reproduce their classification logic in Python.
        library = directory / 'ownership.dylib'
        bag_source = SOURCE / 'features/capacita-borsa/sorgenti'
        subprocess.run(['clang', '-shared', '-fPIC',
                        str(SOURCE / 'features/training-native/ownership.c'),
                        str(bag_source / 'core.c'), str(bag_source / 'journal.c'),
                        '-o', str(library)], check=True, capture_output=True)
        cls.library = C.CDLL(str(library))

    def bench(self):
        return ComposedBench(self.training_blob, self.training_symbols,
                             self.bag_blob, self.bag_symbols)

    def test_foreign_bag_destination_rejects_activation_and_keeps_native_save(self):
        # Removing any one of the four admission checks must fail this test,
        # even when the foreign copy belongs to the currently active bank.
        for address in BAG_ADDRESSES:
            for active_bank in (0, 1):
                with self.subTest(address=hex(address), active_bank=active_bank):
                    b = self.bench()
                    b.flash[address:address + 8] = b'FOREIGN!'
                    b.mu.mem_write(SAVE + 0x2330A, struct.pack('<H', active_bank))
                    before_flash = bytes(b.flash)
                    before_save = bytes(b.mu.mem_read(SAVE, 0x23400))
                    before_mon = bytes(b.mu.mem_read(0x022C0000, 236))
                    before_state = bytes(b.mu.mem_read(STATE, 0x1000))
                    self.assertEqual(b.service(1, arg=0), 8)
                    self.assertEqual(b.u32(STATE + 8), 0)
                    self.assertEqual(b.writes, [])
                    self.assertEqual(bytes(b.flash), before_flash)
                    self.assertEqual(bytes(b.mu.mem_read(SAVE, 0x23400)), before_save)
                    self.assertEqual(bytes(b.mu.mem_read(0x022C0000, 236)), before_mon)
                    self.assertEqual(bytes(b.mu.mem_read(STATE, 0x1000)), before_state)
                    self.assertEqual(b.charges, [])
                    # Bag may write the other, claimable bank during this later
                    # save. Those writes are distinct from read-only admission.
                    self.assertEqual(b.save(), 2)
                    self.assertEqual(b.native_saves, 1)
                    self.assertTrue(all(a in BAG_ADDRESSES and len(data) == 452
                                        for a, data in b.writes))
                    self.assertEqual(b.flash[address:address + 8], b'FOREIGN!')

    def test_claimable_predicate_matches_real_bag_writer(self):
        # Any narrowed uniform-pattern rule or broadened interrupted-magic
        # ownership must disagree with a literal case or the real Bag writer.
        cases = [(bytes([v]) * 452, 1) for v in (0, 255, 0xA5)]
        cases += [(b'B252' + b'foreign body' + bytes(436), 1),
                  (b'FOREIGN!' + bytes(444), 0)]
        for n in (1, 2, 3):
            raw = b'B252'[:n] + b'\xff' * (452 - n)
            cases += [(raw, 1), (raw[:-1] + b'X', 0)]
        for raw, expected in cases:
            with self.subTest(prefix=raw[:8], tail=raw[-1]):
                buf = (C.c_ubyte * 452).from_buffer_copy(raw)
                oracle = bool(self.library.cap_record_uniform(buf) or
                              self.library.cap_record_owned_prefix(buf))
                self.assertEqual(oracle, bool(expected))
                self.assertEqual(self.library.training_bag_claimable(buf), expected)
                self.assertEqual(bytes(buf), raw)
        # Every single-byte disturbance of an interrupted prefix is compared
        # against the production writer too, including all final byte offsets.
        for n in (1, 2, 3):
            for offset in range(452):
                raw = bytearray(b'B252'[:n] + b'\xff' * (452 - n))
                raw[offset] ^= 0x55
                buf = (C.c_ubyte * 452).from_buffer_copy(raw)
                expected = bool(self.library.cap_record_uniform(buf) or
                                self.library.cap_record_owned_prefix(buf))
                self.assertEqual(bool(self.library.training_bag_claimable(buf)), expected,
                                 (n, offset))

    def test_claimable_bag_records_admit_without_writes(self):
        cases = [bytes([v]) * 452 for v in (0, 255, 0xA5)]
        cases += [b'B252' + b'X' * 448]
        cases += [b'B252'[:n] + b'\xff' * (452 - n) for n in (1, 2, 3)]
        for record in cases:
            with self.subTest(prefix=record[:4]):
                b = self.bench()
                for address in BAG_ADDRESSES:
                    b.flash[address:address + 452] = record
                flash = bytes(b.flash)
                self.assertEqual(b.service(1, arg=0), 0)
                self.assertEqual(b.u32(STATE + 8), 1)
                self.assertEqual(b.writes, [])
                self.assertEqual(bytes(b.flash), flash)
                bag_reads = [(a, dst, n) for a, dst, n in b.reads if a in BAG_ADDRESSES]
                self.assertEqual([a for a, _, _ in bag_reads], list(BAG_ADDRESSES))
                self.assertTrue(all(n == 452 and dst % 4 == 0 for _, dst, n in bag_reads))
                self.assertEqual(b.heap, 0x02300000)

    def test_interrupted_magic_with_foreign_tail_rejects_each_destination(self):
        for n in (1, 2, 3):
            for address in BAG_ADDRESSES:
                with self.subTest(prefix=n, address=hex(address)):
                    b = self.bench()
                    b.flash[address:address + 452] = b'B252'[:n] + b'\xff' * (451 - n) + b'X'
                    before = bytes(b.mu.mem_read(STATE, 0x1000))
                    self.assertEqual(b.service(1, arg=0), 8)
                    self.assertEqual(b.u32(STATE + 8), 0)
                    self.assertEqual(bytes(b.mu.mem_read(STATE, 0x1000)), before)
                    self.assertEqual(b.writes, [])

    def test_read_failure_rejects_each_bag_destination(self):
        for address in BAG_ADDRESSES:
            for active_bank in (0, 1):
                with self.subTest(address=hex(address), active_bank=active_bank):
                    b = self.bench()
                    b.fail_address = address
                    b.mu.mem_write(SAVE + 0x2330A, struct.pack('<H', active_bank))
                    before = bytes(b.mu.mem_read(STATE, 0x1000))
                    self.assertEqual(b.service(1, arg=0), 8)
                    self.assertEqual(bytes(b.mu.mem_read(STATE, 0x1000)), before)
                    self.assertEqual(b.writes, [])

    def test_rejection_preserves_active_journal_and_still_blocks_failed_save(self):
        # Clearing enabled on a refused policy change would let native data
        # commit while the already-active training journal cannot persist.
        for active_bank, destination in ((0, 0x70000), (1, 0x30000)):
            with self.subTest(active_bank=active_bank):
                b = self.bench()
                b.activate(0)
                b.mu.mem_write(SAVE + 0x2330A, struct.pack('<H', active_bank))
                b.flash[destination:destination + 8] = b'FOREIGN!'
                before = bytes(b.mu.mem_read(STATE, 0x1000))
                self.assertEqual(b.service(1, arg=0), 8)
                self.assertEqual(bytes(b.mu.mem_read(STATE, 0x1000)), before)
                self.assertEqual(b.u32(STATE + 8), 1)
                self.assertEqual(b.writes, [])
                self.assertEqual(b.save(), 3)
                self.assertEqual(b.native_saves, 0)
                self.assertEqual(b.writes, [])


if __name__ == '__main__':
    unittest.main()
