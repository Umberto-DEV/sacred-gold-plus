"""Owned metadata/bytecode counterexamples; no ROM, compiler or CPU."""
from pathlib import Path
import importlib.util
import struct
import unittest


class UTurnShellBellOrderTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        p=Path(__file__).parents[1]/'tools/rileggi_uturn_shellbell.py';s=importlib.util.spec_from_file_location('owned_shellbell_order',p)
        cls.T=importlib.util.module_from_spec(s);s.loader.exec_module(cls.T)
    def test_inline_comments_do_not_shift_command_IDs(self):
        names=['BtlCmd_Own'+str(i)for i in range(225)]
        text='; sBattleScriptCommandTable:\nsBattleScriptCommandTable:\n'
        text+='\n'.join('.word '+name+(' ; comment'if i%5==0 else'')for i,name in enumerate(names))
        text+='\n.public NextOwnedTable\nNextOwnedTable:\n.word outside\n'
        self.assertEqual(self.T.parse_command_table(text),names)
    def test_ambiguous_or_non_word_table_is_rejected(self):
        for text in('; sBattleScriptCommandTable:\n.word BtlCmd_Own\n',
                     'sBattleScriptCommandTable:\n.word A, B\n',
                     'sBattleScriptCommandTable:\n.word A\nsBattleScriptCommandTable:\n.word B\n'):
            with self.assertRaises(ValueError):self.T.parse_command_table(text)
    def own(self):return[213,2,61,5,50,7,68,1<<16,224]
    def test_owned_prefix_has_consumer_then_call_then_project_marker(self):
        words=self.own();rows=self.T.decode_prefix(words,4)
        self.assertEqual([r['word']for r in rows],[0,2]);self.assertEqual(rows[0]['jump_word'],4)
        proof=self.T.require_order(rows,words,4,expected_var=5)
        self.assertTrue(proof['consumer_before_snapshot']);self.assertFalse(proof['healing_observed'])
    def test_opcode_in_an_operand_is_not_a_command(self):
        words=[61,213,61,5,50,7,68,1<<16,224];rows=self.T.decode_prefix(words,4)
        self.assertEqual([r['opcode']for r in rows],[61,61])
        with self.assertRaises(ValueError):self.T.require_order(rows,words,4,expected_var=5)
    def test_branch_into_operand_negative_or_out_of_program_is_rejected(self):
        for relative in(0xffffffff,1,0x7fffffff):
            words=self.own();words[1]=relative
            with self.assertRaises(ValueError):self.T.decode_prefix(words,4)
    def test_unknown_opcode_truncation_and_bool_alias_are_rejected(self):
        for words,stop in(([123,0,224],2),([213,2,224],1),([True,2,224],2),([213,False,224],2)):
            with self.assertRaises(ValueError):self.T.decode_prefix(words,stop)
    def test_call_variable_and_marker_are_separate_contracts(self):
        words=self.own();rows=self.T.decode_prefix(words,4)
        with self.assertRaises(ValueError):self.T.require_order(rows,words,4,expected_var=43)
        words[6]=9
        with self.assertRaises(ValueError):self.T.require_order(rows,words,4,expected_var=5)
    def test_command213_and_scriptID213_are_distinct_namespaces(self):
        words=[61,213,61,5,224];rows=self.T.decode_prefix(words,4)
        self.assertFalse(any(r['opcode']==213 for r in rows))
        self.assertEqual(rows[0]['arguments'],[213])
    def test_Thumb_BL_positive_negative_and_wrong_ISA(self):
        for pc,target in((0x1000,0x1200),(0x1200,0x1000)):
            delta=target-pc-4;blob=struct.pack('<HH',0xf000|((delta>>12)&0x7ff),0xf800|((delta>>1)&0x7ff))
            self.assertEqual(self.T.bl_target(blob,pc),target)
        for blob,pc in((bytes.fromhex('00f000e8'),0x1000),(b'\0'*2,0x1000),(bytes.fromhex('00f000f8'),True)):
            with self.assertRaises(ValueError):self.T.bl_target(blob,pc)
    def test_owned_legacy_profile_is_located_from_bytes_and_table_not_a_shift(self):
        profile=bytes.fromhex('01207047');image=bytearray(b'\xa5'*64);image[8:12]=profile
        struct.pack_into('<II',image,32,0x1009,0x100d)
        proof=self.T.locate_handler(bytes(image),0x1000,profile,opcode=1)
        self.assertEqual((proof['handler'],proof['table']),(0x1008,0x101c))
        self.assertFalse(proof['comparison_bytes_normalized'])
    def test_ambiguous_legacy_code_or_dispatch_pair_is_rejected(self):
        profile=bytes.fromhex('01207047');image=bytearray(b'\xa5'*64);image[8:12]=profile
        struct.pack_into('<II',image,32,0x1009,0x100d)
        duplicate=bytearray(image);duplicate[16:20]=profile
        with self.assertRaises(ValueError):self.T.locate_handler(bytes(duplicate),0x1000,profile,1)
        duplicate=bytearray(image);struct.pack_into('<II',duplicate,48,0x1009,0x100d)
        with self.assertRaises(ValueError):self.T.locate_handler(bytes(duplicate),0x1000,profile,1)
        struct.pack_into('<I',image,36,0x100f)
        with self.assertRaises(ValueError):self.T.locate_handler(bytes(image),0x1000,profile,1)
    def test_legacy_successor_one_past_the_overlay_is_rejected(self):
        profile=bytes.fromhex('01207047');image=bytearray(b'\xa5'*64);image[60:64]=profile
        struct.pack_into('<II',image,32,0x103d,0x1041)
        with self.assertRaises(ValueError):self.T.locate_handler(bytes(image),0x1000,profile,1)


if __name__=='__main__':unittest.main()
