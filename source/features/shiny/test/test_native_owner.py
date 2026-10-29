"""Compiled resident owner tests; native services are explicit Unicorn seams."""
import importlib.util
from pathlib import Path
import struct
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB, UC_HOOK_CODE
from unicorn.arm_const import *
from sgp13.shiny_core import compile_native as compile_core

class OwnerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = ROOT / 'sgp13/shiny.py'
        assert path.exists(), 'Native shiny installer is not implemented'
        spec = importlib.util.spec_from_file_location('shiny_native', path)
        cls.module = importlib.util.module_from_spec(spec); spec.loader.exec_module(cls.module)
        cls.temp = tempfile.TemporaryDirectory()
        cls.blob, cls.sym = cls.module.compile_native(cls.temp.name, 'native')
        cls.core, cls.csym = compile_core(cls.temp.name)
    @classmethod
    def tearDownClass(cls): cls.temp.cleanup()
    def setUp(self):
        self.u=Uc(UC_ARCH_ARM,UC_MODE_THUMB); self.u.mem_map(0x02000000,0x400000)
        self.u.mem_write(0x023C9100,self.blob); self.u.mem_write(0x023C8100,self.core)
        self.fs=0x022C0000; self.save=0x022C1000; self.app=0x022C2000; self.options=0x022C3000
        self.out=0x022C4000; self.draft=0x022C4100
        self.data=bytes(16); self.available=True; self.writes=0; self.bound=[]; self.dispatches=0; self.party=[]; self.refreshed=[]; self.party_reads=0
        config=[0x594E4853, (152<<16)|2, self.sym['sgp_shiny_snapshot'],self.sym['sgp_shiny_candidate'],self.sym['sgp_shiny_apply']]
        config += [self.csym['sgp_shiny_'+n] for n in ('valid','denominator','select','complete','draw','transform')]
        config += [0x023EE001,0x023EE005,0x023EE009,0x023EE00D,0x023EE011,0,0,0,0,0]
        self.u.mem_write(0x023CB100,struct.pack('<21IHH',*config,1,0)+b'\x02'+bytes(63))
        self.put(self.fs+12,self.save); self.put(self.app+0x24,self.options)
        self.put(0x021D4158,self.fs)
        self.u.hook_add(UC_HOOK_CODE,self.hook)
        self.call('sgp_shiny_continue',0)
    def put(self,p,v):self.u.mem_write(p,struct.pack('<I',v))
    def get(self,p):return struct.unpack('<I',self.u.mem_read(p,4))[0]
    def ret(self,v=0):self.u.reg_write(UC_ARM_REG_R0,v);self.u.reg_write(UC_ARM_REG_PC,self.u.reg_read(UC_ARM_REG_LR))
    def hook(self,u,a,size,_):
        x,y,z=[u.reg_read(r) for r in (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2)]
        if a==0x0203DFE0:self.ret(self.fs)
        elif a==0x02028EA8:self.ret(self.options)
        elif a==0x023EE000:
            if self.available:
                if z:self.data=bytes(u.mem_read(y,16));self.writes+=1
                else:u.mem_write(y,self.data)
            self.ret(int(self.available))
        elif a==0x023EE004:self.bound.append((x,y));self.ret()
        elif a==0x02074904:self.party_reads+=1;self.ret(0x022C6000)
        elif a==0x02074640:self.ret(len(self.party))
        elif a==0x02074644:self.ret(0x022C7000+y*256)
        elif a==0x023EE008:self.ret(self.party[(x-0x022C7000)//256].get(y,0))
        elif a==0x0206E250:self.refreshed.append((x-0x022C7000)//256);self.ret()
        elif a in (0x02000E6C,0x0203E058,0x0203DF34,0x0203E15C,0x0202D0FC):self.ret(77)
        elif a==0x023EE010:self.dispatches+=1;self.ret()
    def call(self,name,*args):
        for i,r in enumerate((UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3)):
            self.u.reg_write(r,args[i] if i<len(args) else 0)
        for i,v in enumerate(args[4:]):self.put(0x023FF000+i*4,v)
        self.u.reg_write(UC_ARM_REG_SP,0x023FF000);self.u.reg_write(UC_ARM_REG_LR,0x023EF001)
        self.u.emu_start(self.sym[name]|1,0x023EF000,count=100000)
        self.assertEqual(self.u.reg_read(UC_ARM_REG_PC),0x023EF000)
        self.assertEqual(self.u.reg_read(UC_ARM_REG_SP),0x023FF000)
        return self.u.reg_read(UC_ARM_REG_R0)
    def snapshot(self):
        self.u.mem_write(self.out,b'\xff'*32)
        result=self.call('sgp_shiny_snapshot',self.app,self.out)
        return result,bytes(self.u.mem_read(self.out,32))
    def test_live_owner_snapshot_and_newgame_binding(self):
        self.assertEqual(self.bound,[(self.save,0)])
        ok,s=self.snapshot();self.assertEqual(ok,1);self.assertEqual(s[16],1)
        self.assertEqual(struct.unpack_from('<H',s,14)[0],512)
        self.assertEqual(s[29:],bytes(3))
        self.call('sgp_shiny_newgame',0);self.assertEqual(self.bound[-1],(self.save,1))
    def test_foreign_options_and_deleted_owner_never_leak_snapshot(self):
        self.put(self.app+0x24,self.options+4)
        ok,s=self.snapshot();self.assertEqual(ok,0);self.assertEqual(s[16],0)
        self.put(self.app+0x24,self.options)
        self.call('sgp_shiny_delete',0)
        ok,s=self.snapshot();self.assertEqual(ok,0);self.assertEqual(s[16],0)
    def test_foreign_storage_is_visible_unavailable_without_write(self):
        self.available=False
        ok,s=self.snapshot();self.assertEqual(ok,1);self.assertEqual(s[16],0);self.assertEqual(s[21],1)
        self.assertEqual(self.writes,0)
    def test_mode_change_commits_once_same_selection_preserves(self):
        _,s=self.snapshot()
        self.u.mem_write(self.draft,s[:12]+struct.pack('<HBB4B',0,1,0,0,0,0,0))
        self.assertEqual(self.call('sgp_shiny_apply',self.app,self.draft),0)
        self.assertEqual(self.data[7],1);self.assertEqual(self.writes,1)
        _,s=self.snapshot(); self.u.mem_write(self.draft,s[:12]+struct.pack('<HBB4B',0,1,0,0,0,0,0))
        self.assertEqual(self.call('sgp_shiny_apply',self.app,self.draft),0);self.assertEqual(self.writes,1)
    def test_stale_or_reserved_draft_cannot_commit(self):
        _,s=self.snapshot();self.u.mem_write(self.draft,s[:12]+struct.pack('<HBB4B',0,1,0,0,1,0,0))
        self.assertNotEqual(self.call('sgp_shiny_apply',self.app,self.draft),0);self.assertEqual(self.writes,0)
        self.u.mem_write(self.draft,bytes(20))
        self.assertEqual(self.call('sgp_shiny_apply',self.app,self.draft),2)
    def test_boot_invalidates_old_native_global(self):
        self.call('sgp_shiny_boot');self.assertEqual(self.snapshot()[0],0)

class RefreshTests(OwnerTests):
    """Party seams are isolated from search subclasses' lead-mon fixture."""
    def refresh_config(self, ids):
        bitmap=bytearray(64)
        for species in ids:bitmap[species//8]|=1<<(species%8)
        self.u.mem_write(0x023CB100+84,struct.pack('<HH',len(ids),0)+bitmap)
    def test_refresh_selects_bitmap_boundaries_and_high_id(self):
        for species in (1,7,8,15,16,31,32,63,64,127,128,255,256,487,488,493):
            with self.subTest(species=species):
                self.refresh_config([species]);self.refreshed=[]
                self.party=[{5:species},{5:species+1 if species<493 else 492},{5:0},{5:494},{5:511},{5:0xffffffff}]
                self.call('sgp_shiny_continue',0)
                self.assertEqual(self.refreshed,[0])
    def test_refresh_all_species_skips_bad_checksum_and_eggs(self):
        self.refresh_config(range(1,494))
        self.party=[{5:1},{5:493},{5:256,3:1},{5:488,76:1},{5:0},{5:494}]
        self.call('sgp_shiny_continue',0);self.assertEqual(self.refreshed,[0,1])
    def test_refresh_rejects_malformed_bitmap_and_count(self):
        cases=[('zero count',84,b'\0\0'),('count too high',84,struct.pack('<H',494)),
               ('count mismatch',84,b'\x02\0'),('reserved',86,b'\x01\0'),
               ('bit zero',88,b'\x03'),('bit 494',149,b'\x40'),
               ('bit 503',150,b'\x80'),('bit 511',151,b'\x80')]
        for label,offset,data in cases:
            with self.subTest(case=label):
                self.refresh_config([1]);self.u.mem_write(0x023CB100+offset,data)
                if label.startswith('bit '):self.u.mem_write(0x023CB100+84,struct.pack('<H',2))
                if label=='zero count':self.u.mem_write(0x023CB100+88,bytes(64))
                self.party=[{5:1}];self.refreshed=[];self.party_reads=0
                self.call('sgp_shiny_continue',0)
                self.assertEqual(self.refreshed,[]);self.assertEqual(self.party_reads,0)
    def test_refresh_rejects_party_larger_than_native_capacity(self):
        self.refresh_config([1]);self.party=[{5:1}]*7
        self.call('sgp_shiny_continue',0);self.assertEqual(self.refreshed,[])

if __name__=='__main__':unittest.main()
