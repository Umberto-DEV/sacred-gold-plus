"""Training successor contract: actual historical Thumb predicates, no ROM."""
import hashlib
from pathlib import Path
import struct
import subprocess
import tempfile
import unittest
from ui_bench import (SOURCE, FLAGS, EXT, STATE, GENERATION, DESCRIPTOR, FS, SAVE,
                      APP, OPTIONS, OUT, PROOF, NEXT, STACK, SHINY, ADMITTED,
                      FLAGS_OFFSET, Bench, compile_object, training, shiny, shiny_core)


class TrainingUiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix='training-ui-')
        cls.addClassCleanup(cls.temp.cleanup)
        cls.directory = Path(cls.temp.name)
        cls.old, cls.ts = training.compile_native(cls.directory / 'historical')
        cls.extension, cls.us = compile_object(
            SOURCE / 'features/training-native/ui_transaction.c', cls.directory / 'ui.o',
            ['-DSGP_SETTINGS_UI_SUCCESSOR=1', '-fstack-usage'])
        cls.core, cls.cs = shiny_core.compile_native(cls.directory / 'core')
        cls.native, cls.ns = shiny.compile_native(cls.directory / 'shiny', 'native')

    def bench(self):
        return Bench((self.old, self.ts, self.extension, self.us, self.core,
                      self.cs, self.native, self.ns))

    def unchanged(self, b, before):
        self.assertEqual(b.owner(), before)
        self.assertEqual(b.owner_writes, [])
        self.assertEqual(b.flash_writes, [])

    def test_legacy_read_admits_and_stale_apply_mutates_real_training(self):
        b = self.bench()
        b.u.mem_write(FLAGS_OFFSET, b'\0\0')
        before = b.owner()
        self.assertEqual(b.call(b.ts['training_shiny_access'], FS, OUT, 0), 1)
        self.assertEqual(b.get(ADMITTED), 1)
        self.assertEqual(bytes(b.u.mem_read(FLAGS_OFFSET, 2)), b'\x01\0')
        self.assertNotEqual(b.owner(), before)
        self.assertTrue(b.owner_writes)
        self.assertEqual(b.flash_writes, [])
        # Set the real shiny runtime live without invoking Continue's binding.
        b = self.bench()
        b.u.mem_write(0x023CB200, struct.pack('<7I', 0x594E4853, 1, 1, 1, FS, SAVE, OPTIONS))
        b.u.mem_write(NEXT, bytes(20))  # epoch0 is stale, before validation access mutates
        self.assertEqual(b.call(b.ns['sgp_shiny_apply'], APP, NEXT), 2)
        self.assertEqual(b.get(ADMITTED), 1)
        self.assertTrue(b.owner_writes)
        self.assertEqual(b.flash_writes, [])

    def test_peek_returns_exact_local_proof_without_admission(self):
        for enabled in (0, 1):
            for admitted in (0, 1):
                with self.subTest(enabled=enabled, admitted=admitted):
                    b = self.bench()
                    b.put(STATE + 8, enabled)
                    b.put(ADMITTED, admitted)
                    b.u.mem_write(FLAGS_OFFSET, struct.pack('<H', 0 if enabled else 1))
                    saved = struct.pack('<IHBBB7s', 123, 493, 40, 1, 1, bytes(7))
                    b.u.mem_write(SHINY, saved)
                    before = b.owner()
                    self.assertEqual(b.peek(), 0)
                    self.assertEqual(bytes(b.u.mem_read(OUT, 16)), saved)
                    expected = struct.pack('<8IHH', 1, SAVE, 17, 0, enabled, 1, 0,
                                           admitted, 0 if enabled else 1, 0) + saved
                    self.assertEqual(bytes(b.u.mem_read(PROOF, 52)), expected)
                    self.unchanged(b, before)
                    self.assertEqual(bool(b.reads), not admitted)
                    self.assertLessEqual(STACK - b.low_sp, 1024)

    def test_unavailable_and_bad_domains_never_initialize_or_publish(self):
        mutations = [(STATE, 0), (STATE + 4, SAVE + 4), (STATE + 12, 0),
                     (STATE + 8, 2), (STATE + 12, 2), (STATE + 16, 5),
                     (ADMITTED, 2), (GENERATION, 0), (GENERATION + 4, 0),
                     (GENERATION + 8, SAVE + 4), (GENERATION + 12, 1),
                     (0x021D4158, FS + 4), (FS + 12, SAVE + 4), (SAVE+0x2330A, 2),
                     (FS+12, 0x023E0000)]
        for address, value in mutations:
            with self.subTest(address=hex(address), value=value):
                b = self.bench(); b.put(address, value); before = b.owner()
                self.assertNotEqual(b.peek(), 0)
                self.unchanged(b, before)
                self.assertEqual(bytes(b.u.mem_read(OUT, 16)), b'\xa5' * 16)
                self.assertEqual(bytes(b.u.mem_read(PROOF, 52)), b'\xa5' * 52)
                self.assertEqual(b.reads, [])
        for offset, value in ((4, 494), (6, 41), (7, 2), (8, 2), (9, 1)):
            b = self.bench()
            b.u.mem_write(SHINY + offset, struct.pack('<H', value) if offset == 4 else bytes([value]))
            self.assertNotEqual(b.peek(), 0)
            self.assertEqual(b.owner_writes, [])
            self.assertEqual(b.reads, [])
        b = self.bench(); b.u.mem_write(FLAGS_OFFSET, b'\x02\0')
        self.assertNotEqual(b.peek(), 0)
        self.assertEqual(b.reads, [])

    def test_invalid_extents_overlap_and_owner_aliases_fail_before_reads(self):
        for fs in (0, FS + 1, 0x023FFFF4, 0xFFFFFFFC):
            b = self.bench(); before = b.owner()
            self.assertNotEqual(b.ui('peek', fs, OUT, PROOF), 0)
            self.unchanged(b, before); self.assertEqual(b.reads, [])
        for output in (0, OUT + 1, 0x01FFFFFC, 0x023FFFF4, 0xFFFFFFFC,
                       0x027E007C, 0x027E3774, 0x027E3780, 0x027E4000,
                       FS, SAVE, OPTIONS, SAVE + 0x23308, STATE, GENERATION, DESCRIPTOR,
                       0x023CB200, 0x023D8700, 0x023D86FC, 0x021D4158):
            for which in (0, 1):
                with self.subTest(output=hex(output), which=which):
                    b = self.bench(); before = b.owner()
                    self.assertNotEqual(b.ui('peek', FS, output if which == 0 else OUT,
                                             output if which else PROOF), 0)
                    self.unchanged(b, before); self.assertEqual(b.reads, [])
        for proof in (OUT, OUT + 4, OUT - 48):
            b = self.bench(); before = b.owner()
            self.assertNotEqual(b.ui('peek', FS, OUT, proof), 0)
            self.unchanged(b, before); self.assertEqual(b.reads, [])
        for saved, proof in ((0x027E0080, 0x027E374C), (0x0226EC40, 0x023BFFCC)):
            b = self.bench()
            # Caller owns locals above its current SP, as a native C frame does.
            b.stack = 0x027E3000
            self.assertEqual(b.ui('peek', FS, saved, proof), 0)
            self.assertEqual(b.owner_writes, [])

    def test_each_bank_storage_classification_uses_real_readonly_predicates(self):
        for sector in (0x31000, 0x71000):
            for kind, expected in (('erased', 0), ('lease', 0), ('torn', 0),
                                   ('foreign', 1), ('foreign_payload', 1), ('future', 1),
                                   ('future_mirror', 1), ('unreadable', 1)):
                with self.subTest(sector=hex(sector), kind=kind):
                    b = self.bench()
                    if kind in ('lease', 'future', 'future_mirror'):
                        b.lease(sector)
                    elif kind == 'torn':
                        marker = b.lease(sector)
                        b.flash[sector+0x400:sector+0x420] = marker[:7] + b'\xff' * 25
                    elif kind == 'foreign':
                        b.flash[sector+0x400] = 0x44
                    if kind == 'foreign_payload':
                        b.flash[sector + 0x800] = 0x44
                    if kind in ('future', 'future_mirror'):
                        record = sector + (0x200 if kind == 'future_mirror' else 0)
                        b.flash[record:record+8] = b'TNR1\x03\0\0\x01'
                    if kind == 'unreadable':
                        b.fail_address = sector + 0x400
                    before = b.owner()
                    self.assertEqual(b.peek() != 0, bool(expected))
                    self.unchanged(b, before)
        for address in (0x30000, 0x30200, 0x70000, 0x70200):
            for unreadable in (False, True):
                b = self.bench()
                if unreadable: b.fail_address = address
                else: b.flash[address:address+8] = b'FOREIGN!'
                before = b.owner(); self.assertNotEqual(b.peek(), 0)
                self.unchanged(b, before)

    def test_validate_memory_only_and_fresh_storage_even_if_admitted(self):
        b = self.bench(); self.assertEqual(b.peek(), 0)
        b.reads.clear(); before = b.owner()
        self.assertEqual(b.ui('validate', FS, PROOF, NEXT, 0), 0)
        self.unchanged(b, before); self.assertEqual(b.reads, [])
        for sector in (0x31000, 0x71000):
            b = self.bench(); b.put(ADMITTED, 1); self.assertEqual(b.peek(), 0)
            b.flash[sector + 0x400] = 42; before = b.owner()
            self.assertNotEqual(b.ui('validate', FS, PROOF, NEXT, 1), 0)
            self.unchanged(b, before); self.assertTrue(b.reads)
        for inspect in (2, 0xFFFFFFFF):
            b = self.bench(); self.assertEqual(b.peek(), 0); b.reads.clear()
            self.assertNotEqual(b.ui('validate', FS, PROOF, NEXT, inspect), 0)
            self.assertEqual(b.reads, []); self.assertEqual(b.owner_writes, [])

    def test_proof_and_next_corruption_refuse_before_storage(self):
        for offset in range(52):
            b = self.bench(); self.assertEqual(b.peek(), 0); b.reads.clear()
            raw = bytearray(b.u.mem_read(PROOF, 52)); raw[offset] ^= 1
            b.u.mem_write(PROOF, bytes(raw)); before = b.owner()
            self.assertNotEqual(b.ui('validate', FS, PROOF, NEXT, 1), 0)
            self.unchanged(b, before); self.assertEqual(b.reads, [])
        for raw in (struct.pack('<I', 1) + bytes(12), bytes(7)+b'\x02'+bytes(8),
                    bytes(9)+b'\x01'+bytes(6), bytes(6)+b'\x01'+bytes(9)):
            b = self.bench(); self.assertEqual(b.peek(), 0); b.reads.clear()
            b.u.mem_write(NEXT, raw); before = b.owner()
            self.assertNotEqual(b.ui('validate', FS, PROOF, NEXT, 1), 0)
            self.unchanged(b, before); self.assertEqual(b.reads, [])
        for proof, nxt in ((PROOF+1, NEXT), (PROOF, NEXT+1), (PROOF, PROOF),
                           (STATE, NEXT), (PROOF, GENERATION), (0x027E3770, NEXT)):
            b = self.bench(); self.assertEqual(b.peek(), 0); b.reads.clear()
            self.assertNotEqual(b.ui('validate', FS, proof, nxt, 1), 0)
            self.assertEqual(b.owner_writes, []); self.assertEqual(b.reads, [])

    def test_every_flash_read_rechecks_all_volatile_identity_and_proof_fields(self):
        mutations = [(STATE, 0), (STATE+4, SAVE+4), (STATE+8, 1), (STATE+12, 0),
                     (STATE+16, 1), (ADMITTED, 1), (FLAGS_OFFSET, 0),
                     (SHINY, 1), (GENERATION, 0), (GENERATION+4, 2),
                     (GENERATION+8, SAVE+4), (GENERATION+12, 1),
                     (SAVE+0x23010, 18), (SAVE+0x2330A, 1),
                     (FS+12, SAVE+4), (0x021D4158, FS+4)]
        for method in ('peek', 'validate'):
            for nth in range(1, 11):  # leased sectors: exactly4 Bag +3+3 Training reads
                for address, value in mutations:
                    with self.subTest(method=method, nth=nth, field=hex(address)):
                        b = self.bench(); b.lease(0x31000); b.lease(0x71000)
                        if method == 'validate': self.assertEqual(b.peek(), 0)
                        b.reads.clear(); expected_owner = [b.owner()]
                        before_out = bytes(b.u.mem_read(OUT, 16))
                        before_proof = bytes(b.u.mem_read(PROOF, 52))
                        def mutate(machine, count):
                            if count == nth:
                                machine.put(address, value)
                                expected_owner[0] = machine.owner()
                        b.on_read = mutate
                        result = b.peek() if method == 'peek' else b.ui('validate', FS, PROOF, NEXT, 1)
                        self.assertNotEqual(result, 0)
                        self.assertEqual(b.owner_writes, [])
                        self.assertEqual(b.owner(), expected_owner[0])
                        self.assertEqual(b.flash_writes, [])
                        self.assertEqual(bytes(b.u.mem_read(OUT, 16)), before_out)
                        self.assertEqual(bytes(b.u.mem_read(PROOF, 52)), before_proof)

    def test_store_is_bounded_infallible_and_has_no_read_or_callback(self):
        for enabled in (0, 1):
            b = self.bench(); b.put(STATE+8, enabled)
            b.u.mem_write(FLAGS_OFFSET, b'\0\0')
            self.assertEqual(b.peek(), 0)
            next_saved = struct.pack('<IHBBB7s', 123, 25, 10, 1, 1, bytes(7))
            b.u.mem_write(NEXT, next_saved); before = b.owner()
            b.reads.clear(); b.delegates.clear()
            b.ui('store', PROOF, NEXT)
            after = bytearray(before)
            after[SHINY-0x023C0000:SHINY-0x023C0000+16] = next_saved
            struct.pack_into('<I', after, ADMITTED-0x023C0000, 1)
            if not enabled: struct.pack_into('<H', after, FLAGS_OFFSET-0x023C0000, 1)
            self.assertEqual(b.owner(), bytes(after))
            allowed = set(range(SHINY, SHINY+16)) | set(range(ADMITTED, ADMITTED+4))
            if not enabled: allowed |= set(range(FLAGS_OFFSET, FLAGS_OFFSET+2))
            self.assertTrue(b.owner_writes)
            self.assertTrue(all(set(range(p, p+n)) <= allowed for p, n, _ in b.owner_writes))
            self.assertEqual(b.reads, []); self.assertEqual(b.flash_writes, []); self.assertEqual(b.delegates, [])

    def test_bind_same_pointer_and_failed_load_invalidate_before_delegate(self):
        for fresh in (0, 1):
            b = self.bench(); self.assertEqual(b.peek(), 0)
            b.ui('bind', SAVE, fresh)
            self.assertEqual(b.delegates, [(SAVE, fresh, 2, 0)])
            self.assertEqual(b.get(GENERATION+8), SAVE)
            self.assertNotEqual(b.ui('validate', FS, PROOF, NEXT, 0), 0)
        for result in (0, 1, 7):
            b = self.bench(); self.assertEqual(b.peek(), 0)
            b.native_load_result = result
            self.assertEqual(b.ui('load', SAVE), result)
            self.assertEqual(b.delegates[0][0], SAVE)
            self.assertEqual(b.delegates[0][2:], (2, 0))
            self.assertEqual(b.get(GENERATION+8), SAVE if result else 0)
            self.assertNotEqual(b.ui('validate', FS, PROOF, NEXT, 0), 0)
            self.assertEqual(b.flash_writes, [])

    def test_generation_cold_init_repeated_load_and_permanent_overflow(self):
        b = self.bench(); b.u.mem_write(GENERATION, bytes(16))
        b.ui('bind', SAVE, 1)
        self.assertEqual(b.get(GENERATION), 0x31475554)
        self.assertEqual(b.get(GENERATION+4), 1)
        self.assertEqual(b.peek(), 0)
        for epoch in (2, 3):
            self.assertEqual(b.ui('load', SAVE), 1)
            self.assertEqual(b.get(GENERATION+4), epoch)
            self.assertEqual(b.get(GENERATION+8), SAVE)
        b.put(GENERATION+4, 0xFFFFFFFF)
        for _ in range(3):
            b.ui('bind', SAVE, 1)
            self.assertEqual(b.get(GENERATION+4), 0)
            self.assertEqual(b.get(GENERATION+8), 0)
            self.assertNotEqual(b.peek(), 0)
            b.ui('load', SAVE)
            self.assertEqual(b.get(GENERATION+4), 0)
            self.assertEqual(b.get(GENERATION+8), 0)

    def test_each_actual_storage_read_failure_refuses_without_owner_store(self):
        # Valid leases avoid sector scans: all ten distinct hardware READ sites.
        addresses = (0x30000, 0x30200, 0x70000, 0x70200, 0x31400,
                     0x31000, 0x31200, 0x71400, 0x71000, 0x71200)
        for address in addresses:
            for method in ('peek', 'validate'):
                with self.subTest(address=hex(address), method=method):
                    b = self.bench(); b.lease(0x31000); b.lease(0x71000)
                    if method == 'validate': self.assertEqual(b.peek(), 0)
                    b.fail_address = address; b.reads.clear(); before = b.owner()
                    self.assertNotEqual(b.peek() if method == 'peek' else
                                        b.ui('validate', FS, PROOF, NEXT, 1), 0)
                    self.unchanged(b, before)
                    self.assertEqual(b.reads[-1][0], address)

    def test_buffers_stay_in_native_heap_or_system_stack_not_static_bss(self):
        for address in (0x021D1140, 0x021D110C, 0x021D0000, 0x0226EC3C,
                        0x023BFFF4, 0x023FF000, 0x023FFFCC):
            with self.subTest(address=hex(address)):
                b = self.bench(); before = b.owner()
                self.assertNotEqual(b.ui('peek', FS, address, PROOF), 0)
                self.unchanged(b, before); self.assertEqual(b.reads, [])
        b = self.bench(); before = b.owner()
        self.assertEqual(b.ui('peek', FS, 0x0226EC40, 0x023BFFCC), 0)
        self.unchanged(b, before)

    def test_descriptor_refusals_and_actual_caller_stack_locals(self):
        for offset in (0, 4, 8, 12, 48, 52, 56, 60, 64, 68, 72, 76):
            b = self.bench(); b.put(DESCRIPTOR+offset, b.get(DESCRIPTOR+offset) ^ 1)
            before = b.owner()
            self.assertNotEqual(b.peek(), 0)
            self.unchanged(b, before); self.assertEqual(b.reads, [])
        b = self.bench()
        b.stack = 0x027E3000
        # Simulate a caller frame with saved/proof/next locals ABOVE its SP.
        saved, proof, nxt = 0x027E3100, 0x027E3140, 0x027E3180
        b.u.mem_write(nxt, bytes(16)); before = b.owner()
        self.assertEqual(b.ui('peek', FS, saved, proof), 0)
        self.assertEqual(b.ui('validate', FS, proof, nxt, 1), 0)
        self.assertEqual(b.ui('validate', FS, proof, nxt, 0), 0)
        self.unchanged(b, before)

    def test_historical_blob_and_all_symbols_match_independent_pre_extraction(self):
        self.assertEqual(len(self.old), 11420)
        self.assertEqual(hashlib.sha256(self.old).hexdigest(), '09bf05a472ec02151c5ed19ed578af519f9e186cd53cd9cf8791910b6ed49f07')
        # Independent original declaration: do not obtain it from state.h.
        # A literal typedef also works in shallow CI clones without old Git objects.
        historical_state = """typedef struct {
 u32 magic; void *save; u32 enabled,writable,record_status,preview_slot,preview_valid;
 sgp_train_journal journal;
 sgp_training_request request;
 u8 primary[256],mirror[256],record[256];
 u32 shiny_admitted;
} TrainingState;"""
        runtime = (SOURCE/'features/training-native/runtime.c').read_text()
        self.assertEqual(runtime.count('#include "state.h"'), 1)
        original = runtime.replace('#include "state.h"', historical_state).encode()
        old_c = self.directory / 'before.c'; old_c.write_bytes(original)
        obj = self.directory / 'before.o'
        subprocess.run(['clang', *FLAGS, '-I', str(SOURCE/'features/training-native'),
                        '-c', str(old_c), '-o', str(obj)], check=True, capture_output=True)
        loader = training.module(SOURCE/'features/options/tools/carica_text.py', 'historical_before_loader')
        before_blob, before_symbols = loader.load_text(obj.read_bytes(), training.BASE)
        self.assertEqual(self.old, before_blob)
        self.assertEqual(self.ts, before_symbols)
        self.assertEqual(len(self.ts), 73)

    def test_successor_flag_is_required(self):
        run = subprocess.run(['clang', *FLAGS, '-c', str(SOURCE/'features/training-native/ui_transaction.c'),
                              '-o', str(self.directory/'forbidden.o')], capture_output=True)
        self.assertNotEqual(run.returncode, 0)
        self.assertIn(b'requires SGP_SETTINGS_UI_SUCCESSOR=1', run.stderr)


if __name__ == '__main__':
    unittest.main()
