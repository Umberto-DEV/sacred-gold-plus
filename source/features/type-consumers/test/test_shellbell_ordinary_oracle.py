"""Finite flag counterexamples for the ordinary source frontend; no guest CPU."""
from pathlib import Path
import importlib.util
import unittest


class OrdinaryOracleTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        p = Path(__file__).with_name('shellbell_ordinary_oracle.py')
        s = importlib.util.spec_from_file_location('ordinary_oracle_test', p)
        cls.T = importlib.util.module_from_spec(s); s.loader.exec_module(cls.T)

    def test_parent_is_still_pinned_and_does_not_accept_new_instructions(self):
        t = self.T; t.source_identity_guard()
        for op in (0x4208, 0x5a10, 0x500a, 0x447a, 0x4497, 0xd200, 0xd500, 0xda00, 0xdb00):
            with self.assertRaises(ValueError): t.B.validate_thumb(op.to_bytes(2, 'little'))

    def test_signed_branches_use_overflow_and_preserve_all_registers_flags(self):
        t = self.T
        for flags in range(16):
            n, v = (flags >> 3) & 1, flags & 1
            expected = {0xd2: bool(flags & 2), 0xd5: n == 0, 0xda: n == v, 0xdb: n != v, 0xdd: bool(flags & 4) or n != v}
            for condition, taken in expected.items():
                for delta in (-128, 0, 127):
                    regs = list(range(15)) + [(flags << 28) | 0x3f]; before = list(regs)
                    op = ((condition << 8) | (delta & 255)).to_bytes(2, 'little')
                    actual = t.thumb_step(0x200, op, regs, {}, [], [])
                    self.assertEqual(actual, 0x204 + 2 * delta if taken else 0x202)
                    self.assertEqual(regs, before)

    def test_TST_sets_NZ_and_preserves_CV_without_writing_operands_or_memory(self):
        t = self.T
        for left, right, nz in ((0, 0xffffffff, 0x40000000),
                                 (0x80000000, 0x80000000, 0x80000000),
                                 (0x7fffffff, 1, 0),
                                 (0x80000000, 1, 0x40000000)):
            for flags in range(16):
                regs = [left, right] + list(range(2, 15)) + [(flags << 28) | 0x3f]
                before = list(regs); reads, writes = [], []
                self.assertEqual(t.thumb_step(0x200, bytes.fromhex('0842'), regs, {}, reads, writes), 0x202)
                self.assertEqual(regs[:15], before[:15])
                self.assertEqual(regs[15], nz | (before[15] & 0x3fffffff))
                self.assertEqual((reads, writes), ([], []))

    def test_invalid_state_and_scalar_aliases_are_rejected(self):
        for cpsr in (0x1f, 0x10, True):
            regs = [0] * 15 + [cpsr]
            with self.assertRaises(ValueError): self.T.thumb_step(0x200, bytes.fromhex('0842'), regs, {}, [], [])

    def test_register_halfword_load_uses_two_bytes_and_preserves_flags(self):
        t = self.T; regs = [0] * 15 + [0x9000003f]; regs[1] = 2; regs[2] = 0x1000
        page = bytearray(4096); page[2:6] = bytes.fromhex('81fe1122'); reads = []
        self.assertEqual(t.thumb_step(0x200, bytes.fromhex('505a'), regs, {0x1000: page}, reads, []), 0x202)
        self.assertEqual((regs[0], regs[15]), (0xfe81, 0x9000003f))
        self.assertEqual(reads, [dict(pc=0x200, address=0x1002, bytes=2, hex='81fe')])
        regs[1] = 1
        with self.assertRaises(ValueError): t.thumb_step(0x200, bytes.fromhex('505a'), regs, {0x1000: page}, [], [])
        regs[1] = 2
        with self.assertRaises(ValueError): t.thumb_step(0x200, bytes.fromhex('505a'), regs, {0x1000: page}, [], [], lambda *a: False)

    def test_ADD_r2_pc_uses_unrounded_pipeline_PC_and_preserves_flags(self):
        for pc, value, expected in ((0x200, 10, 0x20e), (0x202, 10, 0x210), (0x200, 0xffffffff, 0x203)):
            regs = [0] * 15 + [0xf000003f]; regs[2] = value
            self.assertEqual(self.T.thumb_step(pc, bytes.fromhex('7a44'), regs, {}, [], []), pc + 2)
            self.assertEqual((regs[2], regs[15]), (expected, 0xf000003f))
        regs = [0] * 15 + [0xf000003f]; regs[2] = 5; before = list(regs)
        self.assertEqual(self.T.thumb_step(0x202, bytes.fromhex('9744'), regs, {}, [], []), 0x20a)
        self.assertEqual(regs, before)

    def test_switch_ADD_r3_pc_keeps_the_same_unrounded_rule(self):
        regs = [0] * 15 + [0xf000003f]; regs[3] = 5
        self.T.thumb_step(0x202, bytes.fromhex('7b44'), regs, {}, [], [])
        self.assertEqual((regs[3], regs[15]), (0x20b, 0xf000003f))
        regs[3] = 5
        self.assertEqual(self.T.thumb_step(0x202, bytes.fromhex('9f44'), regs, {}, [], []), 0x20a)
        regs[5] = 5
        self.T.thumb_step(0x202, bytes.fromhex('7d44'), regs, {}, [], [])
        self.assertEqual(regs[5], 0x20b)
        regs[5] = 5
        self.assertEqual(self.T.thumb_step(0x202, bytes.fromhex('af44'), regs, {}, [], []), 0x20a)

    def test_register_word_store_records_preimage_and_rejects_wrong_owner(self):
        regs = [0] * 15 + [0x9000003f]; regs[:3] = [0x1000, 4, 0x87654321]
        pages = {0x1000: bytearray(b'\xa5' * 4096)}; stores = []; before = list(regs)
        self.assertEqual(self.T.thumb_step(0x200, bytes.fromhex('4250'), regs, pages, [], stores), 0x202)
        self.assertEqual(regs, before)
        self.assertEqual(pages[0x1000][4:8], bytes.fromhex('21436587'))
        self.assertEqual(stores, [dict(pc=0x200, address=0x1004, bytes=4, before='a5a5a5a5', value=0x87654321)])
        with self.assertRaises(ValueError):
            self.T.thumb_step(0x200, bytes.fromhex('4250'), regs, pages, [], [], None, lambda *a: False)
        regs[1] = 5; stores = []
        self.T.thumb_step(0x200, bytes.fromhex('4254'), regs, pages, [], stores)
        self.assertEqual(stores, [dict(pc=0x200, address=0x1005, bytes=1, before='43', value=0x21)])
        self.assertEqual(pages[0x1000][4:8], bytes.fromhex('21216587'))

    def test_ORR_updates_only_destination_and_NZ(self):
        for left, right, expected, nz in ((0, 0, 0, 0x40000000),
                                          (0x80000000, 1, 0x80000001, 0x80000000),
                                          (1, 2, 3, 0)):
            regs = [left, right] + [0] * 13 + [0x3000003f]
            self.T.thumb_step(0x200, bytes.fromhex('0843'), regs, {}, [], [])
            self.assertEqual((regs[0], regs[1], regs[15]), (expected, right, nz | 0x3000003f))

    def test_script_BLX_r2_requires_Thumb_and_records_pipeline_return(self):
        regs = [0] * 15 + [0x9000003f]; regs[2] = 0x401
        self.assertEqual(self.T.thumb_step(0x202, bytes.fromhex('9047'), regs, {}, [], []), 0x400)
        self.assertEqual((regs[14], regs[15]), (0x205, 0x9000003f))
        regs[2] = 0x400
        with self.assertRaises(ValueError): self.T.thumb_step(0x202, bytes.fromhex('9047'), regs, {}, [], [])

    def test_BIC_masks_to_u32_and_preserves_CV(self):
        for left, right, expected, nz in ((0xffffffff, 0x80000001, 0x7ffffffe, 0),
                                          (0xffffffff, 0xffffffff, 0, 0x40000000),
                                          (0x80000000, 1, 0x80000000, 0x80000000)):
            regs = [left, right] + [0] * 13 + [0x3000003f]
            self.T.thumb_step(0x200, bytes.fromhex('8843'), regs, {}, [], [])
            self.assertEqual((regs[0], regs[1], regs[15]), (expected, right, nz | 0x3000003f))

    def test_MVN_is_32bit_and_accepts_defined_register_alias(self):
        for value, expected, nz in ((0, 0xffffffff, 0x80000000),
                                     (0xffffffff, 0, 0x40000000),
                                     (0x80000000, 0x7fffffff, 0)):
            regs = [value] + [0] * 14 + [0x3000003f]
            self.T.thumb_step(0x200, bytes.fromhex('c043'), regs, {}, [], [])
            self.assertEqual((regs[0], regs[15]), (expected, nz | 0x3000003f))

    def test_signed_packet_halfword_and_ip_moves_preserve_flags(self):
        regs = [0] * 15 + [0xb000003f]; regs[1] = 2; regs[2] = 0x1000
        page = bytearray(4096); page[2:4] = bytes.fromhex('81fe')
        self.T.thumb_step(0x200, bytes.fromhex('505e'), regs, {0x1000: page}, [], [])
        self.assertEqual((regs[0], regs[15]), (0xfffffe81, 0xb000003f))
        self.T.thumb_step(0x202, bytes.fromhex('9446'), regs, {}, [], [])
        self.T.thumb_step(0x204, bytes.fromhex('6046'), regs, {}, [], [])
        self.assertEqual((regs[0], regs[12], regs[15]), (0x1000, 0x1000, 0xb000003f))
        for op, source in ((0x46a4, 4), (0x46ac, 5)):
            regs[source] = source + 100
            self.T.thumb_step(0x200, op.to_bytes(2, 'little'), regs, {}, [], [])
            self.assertEqual((regs[12], regs[15]), (source + 100, 0xb000003f))

    def test_NEG_zero_minimum_and_signed_damage_flags(self):
        for operand, expected, flags in ((0, 0, 0x60000000), (1, 0xffffffff, 0x80000000),
                                         (0xffffff9c, 100, 0),
                                         (0x80000000, 0x80000000, 0x90000000)):
            regs = [operand] + [0] * 14 + [0xf000003f]
            self.T.thumb_step(0x200, bytes.fromhex('4042'), regs, {}, [], [])
            self.assertEqual((regs[0], regs[15]), (expected, flags | 0x3f))

    def test_counterfactual_NOP_preserves_all_registers_and_flags(self):
        regs = list(range(15)) + [0xf000003f]; before = list(regs)
        self.assertEqual(self.T.thumb_step(0x200, bytes.fromhex('c046'), regs, {}, [], []), 0x202)
        self.assertEqual(regs, before)

    def test_division_selector_rejects_wrong_pair_caller_state_and_aliases(self):
        for a, b, lr, psr in ((0, 8, 0x225318d, 0x1f), (100, 100, 0x225318d, 0x1f),
                              (100, 8, 0, 0x1f), (100, 8, 0x225318d, 0x3f),
                              (True, 8, 0x225318d, 0x1f)):
            regs = [a, b] + [0] * 12 + [lr, psr]
            with self.assertRaises(ValueError): self.T.select_division(self.T.DIV_ENTRY, regs, {})
        regs = [100, 8] + [0] * 12 + [0x225318d, 0x1f]
        with self.assertRaises(ValueError): self.T.select_division(self.T.DIV_ENTRY + 4, regs, {})

    def test_LDRSH_extremes_aliases_and_rejected_reads_have_no_events(self):
        t = self.T
        for raw, expected in (('0080', 0xffff8000), ('ff7f', 0x7fff), ('ffff', 0xffffffff), ('0000', 0)):
            page = bytearray(4096); page[2:4] = bytes.fromhex(raw)
            for opcode, destination in ((0x5e40, 0), (0x5e41, 1)):
                regs = [0x1000, 2] + [0] * 13 + [0x3000003f]
                t.thumb_step(0x200, opcode.to_bytes(2, 'little'), regs, {0x1000: page}, [], [])
                self.assertEqual((regs[destination], regs[15]), (expected, 0x3000003f))
            regs = [0x1000, 2] + [0] * 13 + [0x3000003f]; before = list(regs); reads = []
            with self.assertRaises(ValueError):
                t.thumb_step(0x200, bytes.fromhex('405e'), regs, {0x1000: page}, reads, [], lambda *a: False)
            self.assertEqual((regs, reads), (before, []))

    def test_store_aliases_and_truncation_use_original_address_operands(self):
        for opcode, expected in ((0x5040, 0x1000), (0x5041, 4)):
            regs = [0x1000, 4] + [0] * 13 + [0x3f]; pages = {0x1000: bytearray(4096)}
            self.T.thumb_step(0x200, opcode.to_bytes(2, 'little'), regs, pages, [], [])
            self.assertEqual(int.from_bytes(pages[0x1000][4:8], 'little'), expected)
        regs = [0x1000, 3, 0xffffffff] + [0] * 12 + [0x3f]; pages = {0x1000: bytearray(4096)}
        with self.assertRaises(ValueError): self.T.thumb_step(0x200, bytes.fromhex('4250'), regs, pages, [], [])
        self.T.thumb_step(0x200, bytes.fromhex('4254'), regs, pages, [], [])
        self.assertEqual(pages[0x1000][2:5], bytes.fromhex('00ff00'))

    def test_logical_aliases_preserve_each_CV_combination(self):
        for cv in (0, 0x10000000, 0x20000000, 0x30000000):
            for opcode, expected, nz in ((0x4300, 0x80000001, 0x80000000),
                                         (0x4380, 0, 0x40000000),
                                         (0x43c0, 0x7ffffffe, 0)):
                regs = [0x80000001] + [0] * 14 + [cv | 0x3f]
                self.T.thumb_step(0x200, opcode.to_bytes(2, 'little'), regs, {}, [], [])
                self.assertEqual((regs[0], regs[15]), (expected, cv | nz | 0x3f))
        regs = [99, 0xffffff9c] + [0] * 13 + [0x3f]
        self.T.thumb_step(0x200, bytes.fromhex('4842'), regs, {}, [], [])
        self.assertEqual(regs[:2], [100, 0xffffff9c])

    def test_pc_wrap_and_rejected_BLX_preserve_link_and_flags(self):
        regs = [0] * 15 + [0xb000003f]; regs[2] = 8
        self.T.thumb_step(0xfffffffc, bytes.fromhex('7a44'), regs, {}, [], [])
        self.assertEqual((regs[2], regs[15]), (8, 0xb000003f))
        regs[2] = 0x400; regs[14] = 0x123; before = list(regs)
        with self.assertRaises(ValueError): self.T.thumb_step(0x200, bytes.fromhex('9047'), regs, {}, [], [])
        self.assertEqual(regs, before)


if __name__ == '__main__': unittest.main()
