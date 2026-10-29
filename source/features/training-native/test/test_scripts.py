"""ROM-free script structure and installer contracts, with no retail assets."""
from pathlib import Path
import json,struct,sys,tempfile,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from sgp13.training_scripts import append_script,service_script
from sgp13.training import append_npc,compile_native,entry_hook
class Scripts(unittest.TestCase):
 def test_existing_entries_and_opaque_body_relocate_together(self):
  old=struct.pack('<IIH',6,8,0xfd13)+b'abcdef0123456789'
  new,id=append_script(old,b'\2\0')
  self.assertEqual(id,3)
  for i in range(2):
   before=i*4+4+struct.unpack_from('<I',old,i*4)[0];after=i*4+4+struct.unpack_from('<I',new,i*4)[0]
   self.assertEqual(new[after:len(old)+4],old[before:])
  self.assertEqual(new[len(old)+4:],b'\2\0')
 def test_npc_append_preserves_old_objects_warps_and_backgrounds(self):
  obj=struct.pack('<14Hi',3,10,0,0,0,1,1,0,0,0,0,0,3,5,0)
  old=struct.pack('<II',0,1)+obj+struct.pack('<I',1)+bytes(12)+bytes(4)
  new=append_npc(old,8,6,7);self.assertEqual(new[8:40],obj);self.assertEqual(new[72:],old[40:]);self.assertEqual(struct.unpack_from('<H',new,50)[0],8)
  with self.assertRaises(ValueError):append_npc(old,8,3,5)
 def test_all_menu_targets_resolve_both_languages_and_use_exact_bridge_width(self):
  prose=json.loads((Path(__file__).resolve().parents[3]/'sgp13/data/training-text.json').read_text())
  self.assertEqual(prose['EN'].keys(),prose['IT'].keys())
  mapping={k:i for i,k in enumerate(prose['EN'])};script=service_script(mapping)
  self.assertGreater(script.count(bytes.fromhex('ea013af1')),10)
  self.assertEqual(script.count(struct.pack('<H',349)),2)
  self.assertEqual(script.count(struct.pack('<HH',351,0x8007)),2)
 def test_native_compile_uses_owned_compartment_only(self):
  with tempfile.TemporaryDirectory()as d:
   blob,symbols=compile_native(d);self.assertLessEqual(len(blob),0x2e00)
   self.assertTrue(symbols['training_script']&1)
   self.assertEqual(entry_hook(0x0208fd9c,symbols['training_canuse'])[:2],b'\x10\xb5')
if __name__=='__main__':unittest.main()
