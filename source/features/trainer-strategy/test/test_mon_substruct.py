"""Owned GetSubstruct source-table, selector and exact owner contracts."""
from pathlib import Path
import importlib.util
import itertools
import struct
import unittest


p=Path(__file__).with_name('mon_substruct_bench.py');s=importlib.util.spec_from_file_location('substruct_contracts',p)
B=importlib.util.module_from_spec(s);s.loader.exec_module(B)


def owned_table_source():
    # Generated test permutations deliberately have a different order from ROM.
    rows=list(itertools.permutations((0,32,64,96)));rows+=rows[:8]
    table=bytes(v for row in rows for v in row)
    source='PokemonDataBlock *GetSubstruct(BoxPokemon *boxMon, u32 pid, u8 which) {\n    static const u8 offsets[32][4] = {\n'
    source+=''.join('        { '+', '.join('0x%02X'%v for v in row)+' },\n'for row in rows)
    source+='    };\n    pid = ((pid & 0x3E000) >> 13);\n    GF_ASSERT(which <= 3);\n    return (PokemonDataBlock *)((char *)boxMon->dataBlocks + offsets[pid][which]);\n}\n'
    return table,source


class SubstructContractTest(unittest.TestCase):
    def test_bounded_source_parser_accepts_owned_array_not_rom_fixture(self):
        table,source=owned_table_source();self.assertEqual(B.L.source_offsets(source),table)
        self.assertNotEqual(B.R.sha(table),B.L.DATA['offsets'][-1])

    def test_parser_rejects_expressions_extra_tokens_and_wrong_guard(self):
        _,source=owned_table_source()
        for s in (source.replace('0x00','(0+0)',1),source.replace('0x00','0x100',1),source.replace('which <= 3','which <= 4'),source.replace('0x3E000','0x1E000'),source+source):
            with self.assertRaises(ValueError):B.L.source_offsets(s)

    def test_parser_rejects_wrong_repeated_rows(self):
        _,source=owned_table_source();i=source.rindex('        { ');end=source.index('\n',i)
        bad=source[:i]+'        { 0x00, 0x20, 0x40, 0x60 },'+source[end:]
        with self.assertRaisesRegex(ValueError,'permutations'):B.L.source_offsets(bad)

    def test_all32_source_rows_and4_selectors(self):
        table,_=owned_table_source()
        for row in range(32):
            for which in range(4):self.assertEqual(B.source_offset(table,row<<13,which),(row,table[4*row+which]))

    def test_row24_does_not_become_row0_even_when_offset_matches(self):
        table,_=owned_table_source()
        a,b=B.source_offset(table,0,1),B.source_offset(table,24<<13,1)
        self.assertEqual(a[1],b[1]);self.assertEqual((a[0],b[0]),(0,24))

    def test_ignored_pid_bits_are_number_bits_not_thumb_pointer(self):
        table,_=owned_table_source();self.assertEqual(B.source_offset(table,0x80006001,1),B.source_offset(table,0x6000,1))

    def test_typed_pid_which_domains_and_exact_frozen_cardinality(self):
        table,_=owned_table_source()
        for pid,which in ((True,0),(-1,0),(2**32,0),(0,True),(0,4),(0,255)):
            with self.assertRaises(ValueError):B.source_offset(table,pid,which)
            with self.assertRaises(ValueError):B.F.make_input({},pid,which)
        self.assertEqual((len(B.F.PROFILES),len(B.F.MATRIX)),(129,130))

    def test_literal_keeps_odd_data_pointer_and_table_lookup_is_one_byte(self):
        self.assertTrue(B.read_owner(0x2072620,0x2072630,4))
        for index in range(128):
            self.assertTrue(B.read_owner(0x2072626,B.TABLE+index,1,table_index=index))
            self.assertFalse(B.read_owner(0x2072626,(B.TABLE+index)&~3,4,table_index=index))
            self.assertFalse(B.read_owner(0x2072626,B.TABLE+index+1,1,table_index=index))

    def test_same_pointer_duplicate_row_still_requires_different_read_address(self):
        self.assertTrue(B.read_owner(0x2072626,B.TABLE+97,1,table_index=97))
        self.assertFalse(B.read_owner(0x2072626,B.TABLE+1,1,table_index=97))
        self.assertFalse(B.read_owner(0x2072626,B.TABLE,1,table_index=True))

    def test_box_and_global_reads_or_writes_are_never_authorized(self):
        for pc in (0x2072608,0x207260a,0x2072620,0x2072626,0x207262c):
            for a in(B.F.BOX,B.F.BOX+8,0x21d15a8):
                for n in(1,4):self.assertFalse(B.read_owner(pc,a,n,table_index=0));self.assertFalse(B.write_owner(pc,a,n))

    def test_stack_has_only_four_saved_words_and_precise_sites(self):
        for a in range(B.R.TOP-16,B.R.TOP,4):
            self.assertTrue(B.write_owner(0x2072608,a,4));self.assertTrue(B.read_owner(0x207262c,a,4))
        for a,n in((B.R.TOP-20,4),(B.R.TOP,4),(B.R.TOP-16,1)):
            self.assertFalse(B.write_owner(0x2072608,a,n));self.assertFalse(B.read_owner(0x207262c,a,n))

    def test_full_parent_replay_uses_new_write_owner(self):
        self.assertIs(B.require_memory_delta.__code__,B.C.require_memory_delta.__code__)
        self.assertIs(B.require_memory_delta.__globals__['write_owner'],B.write_owner)
        a=B.R.TOP-16;base=a&~4095;initial={base:bytes([165])*4096};final={base:bytearray(initial[base])}
        B.M.put(final,a,struct.pack('<I',17));final={k:bytes(v)for k,v in final.items()};x=dict(pc=0x2072608,address=a,bytes=4,before='a5a5a5a5',value=17)
        B.require_memory_delta(initial,final,[x])
        with self.assertRaisesRegex(ValueError,'preimage'):B.require_memory_delta(initial,final,[{**x,'before':'00000000'}])
        with self.assertRaisesRegex(ValueError,'owner'):B.require_memory_delta(initial,final,[{**x,'address':B.F.BOX}])

    def test_source_parent_pins_and_footprint(self):
        B.source_identity_guard();self.assertEqual(B.CODE_SPANS,());self.assertEqual((B.F.FRAME,B.F.GUARD),(16,56))


class SubstructLineageLocatorTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path=Path(__file__).parents[1]/'tools/rileggi_mon_substruct_lineage.py'
        spec=importlib.util.spec_from_file_location('owned_substruct_locator',path)
        cls.D=importlib.util.module_from_spec(spec);spec.loader.exec_module(cls.D)

    def owned_section(self,entry=0x2000100):
        from types import SimpleNamespace
        data=bytearray(b'\xa5'*4096);prefix=bytes(range(20));lookup=b'\x03\x48'+bytes(range(20,32))
        base=0x2000000;offset=entry-base;data[offset:offset+20]=prefix;data[offset+24:offset+38]=lookup
        literal=((entry+28)&~3)+12;data[literal-base:literal-base+4]=struct.pack('<I',0x2000303)
        return SimpleNamespace(ramAddress=base,data=data),prefix,lookup,literal

    def test_literal_odd_value_is_preserved_as_data_pointer(self):
        section,prefix,lookup,literal=self.owned_section()
        self.assertEqual(self.D.locate([section],prefix,lookup),(0x2000100,literal,0x2000303))

    def test_relocated_halfword_entry_uses_word_aligned_literal_pc(self):
        entry=0x2000202;section,prefix,lookup,literal=self.owned_section(entry)
        self.assertEqual(literal,entry+38)
        self.assertEqual(self.D.locate([section],prefix,lookup),(entry,literal,0x2000303))

    def test_missing_and_ambiguous_correspondence_are_rejected(self):
        section,prefix,lookup,_=self.owned_section()
        with self.assertRaisesRegex(ValueError,'unique ROM-to'):self.D.locate([section],prefix,bytes(14))
        section.data[0x500:0x514]=prefix;section.data[0x518:0x526]=lookup
        with self.assertRaisesRegex(ValueError,'unique ROM-to'):self.D.locate([section],prefix,lookup)

    def test_decoded_owner_must_be_unique_and_range_typed(self):
        section,_,_,_=self.owned_section()
        with self.assertRaisesRegex(ValueError,'one decoded'):self.D.piece([section,section],0x2000100,1)
        for address,size in((True,1),(0x2000100,0),(0xffffffff,2)):
            with self.assertRaisesRegex(ValueError,'bounded'):self.D.piece([section],address,size)


if __name__=='__main__':unittest.main()
