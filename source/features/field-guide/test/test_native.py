import sys,unittest,tempfile,subprocess
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from sgp13.guide import compile_native,CANARY,BASE,STATE,CODE_LIMIT,CONFIG_BASE,CONFIG_SIZE,OWNED_RANGES
class NativeTests(unittest.TestCase):
 def test_native_code_has_no_external_runtime_and_stays_in_own_code_range(self):
  with tempfile.TemporaryDirectory() as d:
   blob,symbols=compile_native(d)
   self.assertEqual(CODE_LIMIT,0x2000)
   self.assertEqual(OWNED_RANGES,((0x023d4000,0x2000),(0x023d7b00,0x400)))
   self.assertLessEqual(len(blob),CODE_LIMIT)
   self.assertEqual(len(CANARY),16)
   self.assertEqual(STATE+240+len(CANARY),CONFIG_BASE+CONFIG_SIZE)
   for name in ('guide_init','guide_main','guide_exit','guide_task_input','guide_field_frame','guide_field_create','guide_touch_input','guide_dpad'):
    self.assertTrue(symbols[name]&1)
    self.assertTrue(BASE<=symbols[name]<BASE+len(blob))
 def test_cursor_pages_back_and_touch_bounds(self):
  with tempfile.TemporaryDirectory() as d:
   exe=Path(d)/'controller'
   subprocess.run(['clang',str(Path(__file__).with_name('controller.c')),'-o',str(exe)],check=True)
   subprocess.run([str(exe)],check=True)
if __name__=='__main__':unittest.main()
