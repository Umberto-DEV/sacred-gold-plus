"""A torn payload can be repaired only after a durable, exact sector lease."""
import ctypes as C
from pathlib import Path
import subprocess
import tempfile
import unittest
ROOT = Path(__file__).resolve().parents[1]
class Ownership(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.temp=tempfile.TemporaryDirectory(); path=Path(cls.temp.name)/'owner.dylib'
  subprocess.run(['clang','-shared','-fPIC',str(ROOT/'ownership.c'),'-o',str(path)],check=True)
  cls.lib=C.CDLL(str(path))
 @classmethod
 def tearDownClass(cls):cls.temp.cleanup()
 def test_lease_exact_and_every_torn_prefix(self):
  buf=(C.c_ubyte*32)();self.lib.training_owner_encode(buf);expected=bytes(buf)
  self.assertEqual(expected[:16],b'TNO1\x01\0\x20\0\0\x01\0\x02\0\x01\0\0')
  self.assertEqual(self.lib.training_owner_valid(buf),1)
  for n in range(32):
   torn=(C.c_ubyte*32).from_buffer_copy(expected[:n]+b'\xff'*(32-n))
   self.assertEqual(self.lib.training_owner_valid(torn),int(bytes(torn)==expected))
  for i in range(32):
   changed=bytearray(expected);changed[i]^=1
   self.assertEqual(self.lib.training_owner_valid((C.c_ubyte*32).from_buffer_copy(changed)),0)
 def test_future_version_veto_even_with_lease(self):
  for version in (0,3,255,256,65535):
   buf=(C.c_ubyte*256)();buf[:8]=b'TNR1'+version.to_bytes(2,'little')+b'\0\1'
   self.assertEqual(self.lib.training_record_future(buf),1)
  for version in (1,2):
   buf=(C.c_ubyte*256)();buf[:8]=b'TNR1'+version.to_bytes(2,'little')+b'\0\1'
   self.assertEqual(self.lib.training_record_future(buf),0)
 def test_first_payload_header_torn_prefix_is_recoverable_only_with_erased_tail(self):
  for version in (1,2):
   header=b'TNR1'+version.to_bytes(2,'little')+b'\0\1'
   for n in range(4,8):
    raw=header[:n]+b'\xff'*(256-n)
    self.assertEqual(self.lib.training_record_future((C.c_ubyte*256).from_buffer_copy(raw)),0)
    raw=raw[:-1]+b'X'
    self.assertEqual(self.lib.training_record_future((C.c_ubyte*256).from_buffer_copy(raw)),1)
if __name__=='__main__':unittest.main()
