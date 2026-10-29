"""Execute the compiled app's allocation-failure cleanup on synthetic ARM RAM."""
import sys,unittest,tempfile,struct,subprocess
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from sgp13.guide import compile_native,BASE,STATE,CANARY
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_THUMB,UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_SP,UC_ARM_REG_LR,UC_ARM_REG_PC,UC_ARM_REG_R0,UC_ARM_REG_R1

class AllocationFailureTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  probe=subprocess.run([sys.executable,'-c',"from unicorn import *; from unicorn.arm_const import *; u=Uc(UC_ARCH_ARM,UC_MODE_THUMB);u.mem_map(0x1000,0x1000);u.mem_write(0x1000,bytes.fromhex('00bf'));u.emu_start(0x1001,0x1002)"],capture_output=True)
  if probe.returncode:raise unittest.SkipTest('Unicorn native execution unavailable (probe exit %d)'%probe.returncode)
 def run_failure(self,fail):
  with tempfile.TemporaryDirectory() as d: blob,syms=compile_native(d)
  u=Uc(UC_ARCH_ARM,UC_MODE_THUMB);u.mem_map(0x2000000,0x400000)
  u.mem_write(BASE,blob);u.mem_write(STATE+240,CANARY)
  u.mem_write(0x23d7b00,struct.pack('<II',829,4096))
  calls=[]
  def hook(uc,addr,size,_):
   if addr==0x2001000:uc.emu_stop();return
   if addr in (0x201a910,0x201aa8c,0x201a9c4,0x201a0fc,0x201ab0c):
    calls.append(addr)
    result=0 if addr==fail else 1
    uc.reg_write(UC_ARM_REG_R0,result);uc.reg_write(UC_ARM_REG_PC,uc.reg_read(UC_ARM_REG_LR))
  u.hook_add(UC_HOOK_CODE,hook)
  for name in ('guide_init','guide_main','guide_exit'):
   u.mem_write(0x2300100,bytes(4));u.reg_write(UC_ARM_REG_SP,0x2300000)
   u.reg_write(UC_ARM_REG_LR,0x2001001);u.reg_write(UC_ARM_REG_R0,0);u.reg_write(UC_ARM_REG_R1,0x2300100)
   u.emu_start(syms[name],0,count=100000)
   self.assertEqual(u.reg_read(UC_ARM_REG_R0),1,name)
  self.assertEqual(bytes(u.mem_read(STATE+240,16)),CANARY)
  self.assertNotIn(0x201ab0c,calls,'unacquired objects must not be freed')
  self.assertEqual(calls.count(0x201a9c4),int(fail==0x201aa8c))
 def test_heap_create_failure_closes_without_destroying_unowned_heap(self):self.run_failure(0x201a910)
 def test_content_allocation_failure_releases_the_owned_heap(self):self.run_failure(0x201aa8c)
if __name__=='__main__':unittest.main()
