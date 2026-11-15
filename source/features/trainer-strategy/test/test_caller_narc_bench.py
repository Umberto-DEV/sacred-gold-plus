"""Portable source-recipe, single-CPU and dispatch guards for native headers."""
from pathlib import Path
import importlib.util,types,unittest
from unittest.mock import Mock,patch
SOURCE=Path(__file__).resolve().parents[3]
def tool():
 p=SOURCE/'features/trainer-strategy/tools/attribuisci_lettore_chiamante.py';s=importlib.util.spec_from_file_location('native_header_portable',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
class Portable(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.y=tool()
 def test_full_parent_recipe_and_generic_source_pins(self):
  y=self.y;self.assertEqual(len(y.RECIPES),7)
  with patch.object(y.A,'GENERIC_SHA256','0'*64),self.assertRaisesRegex(ValueError,'generic recipe source'):y.A.bind(y.X,y.R)
 def test_recipe_occurrence_drift_refused(self):
  y=self.y
  with self.assertRaisesRegex(ValueError,'recipe occurrence'):y.A.rewrite(y.R,'require_case',[('missing_source_marker','x',1)],{},'narc_reader')
 def test_only_second_high_level_stub_removed_in_isolated_table(self):
  y=self.y;before=dict(y.B.STUBS);run,receipt=y.A.adapt(y.B,types.SimpleNamespace(parent=y.U,composition=y.V,factory=None));self.assertEqual(y.B.STUBS,before);self.assertEqual(run.__globals__['STUBS'],{k:v for k,v in before.items() if k not in (y.R.ENTRY,y.X.W.ENTRY)});self.assertEqual(receipt['removed_high_level_sdk'],{'0x2007508':'ReadWholeNarcMemberByIdPair'})
 def test_snapshot_has_no_standalone_cpu_setup_execution_or_register_restore(self):
  self.assertFalse({'setup','emu_start','reg_write','mem_write','Uc'}&set(self.y.header_snapshot.__code__.co_names))
 def test_reader_binding_borrows_existing_cpu_without_factory(self):
  y=self.y;u=types.SimpleNamespace(reg_read=lambda register:0);d=types.SimpleNamespace(bench=types.SimpleNamespace(segments=[]),qualified={'header_code':{}},data={'header':{'55':{}}},poison=0xC7,observe=True,header_clobber=False,header_variant='current',u=u,read_bytes=lambda address,n:bytes(n))
  with patch.object(y.R,'Uc') as factory:r=y.bind_reader(d)
  factory.assert_not_called();self.assertIs(r.u,u);self.assertEqual(r.step.__globals__['TOP'],y.INNER);self.assertEqual(r.service.__globals__['DEST'],y.Q.LOCAL)
 def test_invalid_variant_control_refused_before_parent_setup(self):
  y=self.y
  for kwargs in (dict(variant='other'),dict(header_clobber=1)):
   with patch.object(y.X.Driver,'__init__') as parent,self.assertRaisesRegex(ValueError,'finite native header'):y.Driver(None,None,None,1,0,**kwargs)
   parent.assert_not_called()
 def test_original_constructor_backend_and_parent_observer_run_once(self):
  y=self.y
  for event_count in (1,2):
   registers=[0]*16;registers[:4]=[y.B.ARENA+384,2,94,0x2007509];registers[4:12]=list(y.N.COOKIES);registers[13:]=[y.INNER-304,0x2073321,0x3F];state={'pc':y.R.ENTRY}
   def write(register,value):
    if register==y.UC_ARM_REG_PC:state['pc']=value&~1
    else:registers[y.B.R.index(register)]=value
   u=types.SimpleNamespace(reg_write=write,reg_read=lambda register:state['pc']);d=y.Driver.__new__(y.Driver);d.stage='ctor';d.header_active=d.message_active=d.name_active=False;d.events=[];d.ctor_read_dispatch=[];d.regs=lambda:list(registers)
   def copy_member(cpu):
    cpu.reg_write(y.B.R[0],y.B.LOADER_RESULT)
    for _ in range(event_count):d.events.append(('read',2,94,y.B.ARENA+384,44))
   d.original_ctor_read=Mock(side_effect=copy_member)
   with patch.object(y.X.Driver,'step') as parent:
    if event_count==1:y.Driver.step(d,u,y.R.ENTRY,2,None)
    else:
     with self.assertRaisesRegex(ValueError,'single original constructor'):y.Driver.step(d,u,y.R.ENTRY,2,None)
   parent.assert_called_once_with(u,y.R.ENTRY,2,None);d.original_ctor_read.assert_called_once_with(u)
   if event_count==1:self.assertEqual(state['pc'],0x2073320);self.assertEqual(d.ctor_read_dispatch[0]['owner'],'constructor_model')
if __name__=='__main__':unittest.main()
