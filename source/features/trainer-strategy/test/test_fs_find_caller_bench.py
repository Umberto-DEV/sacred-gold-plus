"""Read-only setup and source-owned stack extents; synthetic input, no guest CPU."""
from pathlib import Path
import importlib.util,unittest
s=importlib.util.spec_from_file_location('find_caller_profile',Path(__file__).with_name('fs_find_caller_bench.py'))
M=importlib.util.module_from_spec(s);s.loader.exec_module(M)


class RootInput(unittest.TestCase):
    def test_only_declared_twelve_bss_bytes_may_change_once(self):
        before=bytes(0x400000);after=bytearray(before);i=M.CURRENT-M.BASE;after[i:i+12]=M.ROOT
        regs=[0]*15+[0x3F]
        result=M.require_root_input(before,bytes(after),regs,regs)
        self.assertEqual(result['changed_bytes'],4);self.assertEqual(result['before'],bytes(12).hex())
        self.assertEqual(result['after'],M.ROOT.hex())
        with self.assertRaises(ValueError):M.require_root_input(bytes(after),bytes(after),regs,regs)

    def test_other_memory_or_register_changes_are_rejected(self):
        before=bytes(0x400000);after=bytearray(before);i=M.CURRENT-M.BASE;after[i:i+12]=M.ROOT;after[100]=1
        regs=[0]*15+[0x3F]
        with self.assertRaises(ValueError):M.require_root_input(before,bytes(after),regs,regs)
        after[100]=0;changed=list(regs);changed[0]=1
        with self.assertRaises(ValueError):M.require_root_input(before,bytes(after),regs,changed)
        changed=list(regs);changed[3]=False
        with self.assertRaises(ValueError):M.require_root_input(before,bytes(after),regs,changed)


class Ownership(unittest.TestCase):
    def test_native_frame_fits_existing_masks_and_guard_is_not_poisoned(self):
        r=M.coverage()
        self.assertEqual(r['local_projection'],[M.TOP-296,M.TOP])
        self.assertEqual(r['frame'],[M.TOP-280,M.TOP]);self.assertEqual(r['guard'],[M.TOP-336,M.TOP-280])
        self.assertEqual(r['outside_global_readonly_bytes'],48)
        self.assertEqual(r['guard_outside_local_projection_bytes'],40)
        self.assertEqual(r['guard_inside_local_projection_bytes'],16)
        self.assertEqual(r['legacy_global_guard_offset_in_new_guard'],[40,48])
        self.assertEqual(r['global_projection_bytes'],608);self.assertEqual(r['heap_OFF_projection_bytes'],1124)


if __name__=='__main__':unittest.main()
