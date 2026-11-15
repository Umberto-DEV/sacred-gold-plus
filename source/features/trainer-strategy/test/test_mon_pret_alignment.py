"""Owned source snippets for the bounded cross-PRET mapping adapter."""
from pathlib import Path
import importlib.util
import itertools
import unittest


p=Path(__file__).parents[1]/'tools/confronta_mon_pret.py';s=importlib.util.spec_from_file_location('owned_mon_reference_adapter',p)
D=importlib.util.module_from_spec(s);s.loader.exec_module(D)


def owned_source():
    rows=list(itertools.permutations((0,1,2,3)));rows+=rows[:8]
    enum='enum PokemonDataBlockID { DATA_BLOCK_A = 0, DATA_BLOCK_B, DATA_BLOCK_C, DATA_BLOCK_D };\n'
    macro='#define DATA_BLOCK_SHUFFLE_CASE(v1, v2, v3, v4) { PokemonDataBlock *dataBlocks = boxMon->dataBlocks; switch (dataBlockID) {'
    macro+=''.join('case DATA_BLOCK_'+letter+': result = &dataBlocks[v'+str(i)+']; break;'for i,letter in enumerate('ABCD',1))+'} break; }\n'
    body=D.PT_MARKER+'\n    personality = (personality & 0x3e000) >> 13;\n    GF_ASSERT(personality <= 31);\n    void *result;\n    switch (personality) {\n'
    for row in range(24):
        body+='    case '+str(row)+':\n'
        if row<8:body+='    case '+str(row+24)+':\n'
        body+='        DATA_BLOCK_SHUFFLE_CASE('+', '.join(str(v)for v in rows[row])+')\n'
    body+='    }\n    return result;\n}\n'
    return enum+macro+body,bytes(32*v for row in rows for v in row)


class MonSourceAlignmentTest(unittest.TestCase):
    def test_owned_switch_maps_every32row4selector(self):
        source,expected=owned_source();self.assertEqual(D.platinum_offsets(source),expected)
        self.assertNotEqual(D.sha(expected),D.L.DATA['offsets'][-1])

    def test_macro_must_map_logical_ids_to_expected_parameters(self):
        source,_=owned_source();source=source.replace('result = &dataBlocks[v1]','result = &dataBlocks[v2]',1)
        with self.assertRaisesRegex(ValueError,'macro'):D.platinum_offsets(source)

    def test_missing_duplicate_and_out_of_range_rows_rejected(self):
        source,_=owned_source()
        for text in(source.replace('    case 24:\n',''),source.replace('    case 24:','    case 0:'),source.replace('    case 24:','    case 32:')):
            with self.assertRaises(ValueError):D.platinum_offsets(text)

    def test_changed_mask_and_extra_executable_statement_rejected(self):
        source,_=owned_source()
        for text in(source.replace('0x3e000','0x1e000'),source.replace('    case 0:\n','    case 0:\nresult = 0;\n')):
            with self.assertRaises(ValueError):D.platinum_offsets(text)

    def test_nonconstant_macro_or_wrong_enum_rejected(self):
        source,_=owned_source()
        for text in(source.replace('DATA_BLOCK_A = 0','DATA_BLOCK_A = 1'),source.replace('DATA_BLOCK_SHUFFLE_CASE(0,','DATA_BLOCK_SHUFFLE_CASE(1+0,',1)):
            with self.assertRaises(ValueError):D.platinum_offsets(text)

    def test_function_fragment_has_unique_explicit_boundary(self):
        text='void owned(void) {\n    return;\n}\n'
        self.assertEqual(D.function_block(text,'void owned(void) {'),text)
        for bad in(text+text,'void owned(void) {\n    return;'):
            with self.assertRaises(ValueError):D.function_block(bad,'void owned(void) {')


if __name__=='__main__':unittest.main()
