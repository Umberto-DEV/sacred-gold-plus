"""Earlier model fields do not freeze the native volatile ABI or saved stack."""
from pathlib import Path
import copy,importlib.util,struct,unittest

path=Path(__file__).parents[1]/'tools/congela_fs_translate_contract.py'
spec=importlib.util.spec_from_file_location('translate_freeze',path)
M=importlib.util.module_from_spec(spec);spec.loader.exec_module(M)


class Fields(unittest.TestCase):
    def test_comparison_spans_exclude_only_new_native_saved24(self):
        frame=bytes(range(256))+bytes(range(160));expected=M.stable_frame(frame.hex())
        self.assertEqual([(x['offset'],x['bytes'])for x in expected],[(0,80),(104,312)])
        for offset in(0,79,104,196,415):
            changed=bytearray(frame);changed[offset]^=1
            self.assertNotEqual(M.stable_frame(changed.hex()),expected)
        changed=bytearray(frame);changed[80:104]=b'\xa5'*24
        self.assertEqual(M.stable_frame(changed.hex()),expected)

    def test_stable_fields_preserve_fsresult_and_document_only_two_volatile_exclusions(self):
        entry=list(range(16));entry[13]=M.TOP-312
        for value in(0,1):
            old=list(entry);old[0]=value
            fields=M.stable_registers(old)
            self.assertEqual(set(fields),{str(i)for i in range(16)}-{'1','14'})
            self.assertEqual(fields['0'],value)
        invalid=copy.deepcopy(old);invalid[0]=True
        with self.assertRaises(ValueError):M.stable_registers(invalid)


if __name__=='__main__':unittest.main()
