"""Search orchestration tests: compiled code, explicit native service seams."""
from test_native_owner import OwnerTests, ROOT
from unicorn import UC_HOOK_CODE
import struct
from unicorn.arm_const import UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3

class SearchTests(OwnerTests):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        assert (ROOT/'features/shiny/search.c').exists(), 'Dedicated native search is not implemented'
        cls.search_blob,cls.search_sym=cls.module.compile_native(cls.temp.name,'search')
    def setUp(self):
        self.started=0;self.deleted=0;self.generate_ok=1;self.seen={25};self.time=1;self.builds=0
        super().setUp()
        self.u.mem_write(0x023CE900,self.search_blob);self.sym=dict(self.sym,**self.search_sym)
        self.put(0x023CB100+56,self.search_sym['sgp_shiny_capture'])
        self.put(0x023CB100+60,self.search_sym['sgp_shiny_dispatch'])
        self.put(self.fs,0x022C7000);self.put(0x022C7000,1)
        self.put(self.fs+0x20,0x022C7100);self.put(0x022C7100,123)
        self.put(self.fs+0x40,0x022C7200);self.put(self.fs+0x6C,1)
        self.put(0x02246C94,0x28038800);self.u.mem_write(0x02246A84,b'\x38\xb5');self.u.mem_write(0x02248618,b'\xf8\xb5')
    def hook(self,u,a,size,_):
        x,y,z,w=[u.reg_read(r) for r in (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3)]
        if a==0x0203DF34 and getattr(self,'native_options_path',False):return
        if a==0x0203B8B8:self.u.mem_write(0x022C8000,bytes([20,0,0,0,0,0])+bytes(190));self.ret(0x022C8000)
        elif a==0x020649B8:self.u.mem_write(y,struct.pack('<II4HII',123,0,0,0,1,0,0x022C7200,self.fs));self.ret()
        elif a==0x020503D0:self.ret(0x022C9000)
        elif a in (0x02066860,0x02066870,0x02066644):self.ret(0)
        elif a==0x0224762C:self.u.mem_write(z,b'\0');self.ret(20)
        elif a in (0x0205C67C,0x0205C688):self.ret(0)
        elif a==0x0201481C:self.ret(self.time)
        elif a==0x02246A84:
            self.builds+=1;self.u.mem_write(y,b''.join(struct.pack('<IHH',p,10,10) for p in [25,25,26]*4));self.ret()
        elif a in (0x02246B58,0x02246B00):self.ret()
        elif a==0x0202A634:self.ret(0x022CA000)
        elif a==0x0202A044:self.ret(int(y in self.seen))
        elif a==0x02074644:self.ret(0x022CB000)
        elif a==0x02248618:self.u.mem_write(w,bytes(28));self.ret()
        elif a==0x022482A4:self.ret(1)
        elif a==0x0203E13C:self.ret(int(self.get(self.fs+0x10)==0))
        elif a==0x020518D8:self.ret(0x022CC000)
        elif a in (0x02051F00,0x02052544):self.ret()
        elif a==0x02247B64:
            self.assertEqual([struct.unpack('<I',self.u.mem_read(w+i*8,4))[0] for i in range(12)],[25]*12)
            self.assertEqual(self.get(z+8),1);self.assertEqual(self.get(z+4),0)
            self.ret(self.generate_ok)
        elif a==0x02051BF8:self.deleted+=1;self.ret()
        elif a==0x02050B08:self.started+=1;self.ret()
        else:super().hook(u,a,size,_)
    def configure(self):
        self.call('sgp_shiny_leave',self.fs)
        _,s=self.snapshot();self.assertEqual(s[24],1)
        self.u.mem_write(self.draft,s[:12]+struct.pack('<HBB4B',25,1,0,0,0,0,0))
        self.assertEqual(self.call('sgp_shiny_apply',self.app,self.draft),0)
        for _ in range(40):self.call('sgp_shiny_step_impl',0,0,self.fs)
    def queue(self):
        _,s=self.snapshot();self.assertEqual(s[19],40)
        self.u.mem_write(self.draft,s[:12]+struct.pack('<HBB4B',25,1,0,1,0,0,0))
        self.assertEqual(self.call('sgp_shiny_apply',self.app,self.draft),0)
    def test_capture_filters_seen_and_can_read_after_overlay_unload(self):
        self.call('sgp_shiny_leave',self.fs);_,s=self.snapshot()
        self.assertEqual(s[24:29],bytes([1,0,0,0,0]))
        self.put(0x02246C94,0)
        self.assertEqual(self.call('sgp_shiny_candidate',self.app,self.out,0,0),25)
        self.assertEqual(self.call('sgp_shiny_candidate',self.app,self.out,0,1),0)
    def test_cached_targets_are_not_reused_after_map_change(self):
        self.call('sgp_shiny_leave',self.fs);self.snapshot()
        self.put(0x022C7100,456)
        self.assertEqual(self.call('sgp_shiny_candidate',self.app,self.out,0,0),0)
        self.assertEqual(self.snapshot()[1][24:29],bytes(5))
    def test_queue_waits_for_menu_then_launches_once_and_consumes_charge(self):
        self.configure();self.queue();self.put(self.fs+0x10,1)
        self.call('sgp_shiny_control',self.fs);self.assertEqual(self.started,0)
        self.put(self.fs+0x10,0);self.call('sgp_shiny_control',self.fs)
        self.assertEqual(self.started,1);self.assertEqual(self.snapshot()[1][19],0)
        before=self.builds;self.call('sgp_shiny_control',self.fs)
        self.assertEqual(self.started,1);self.assertEqual(self.builds,before)
    def test_context_loss_clears_queue_even_on_nonordinary_field(self):
        self.configure();self.queue();self.put(0x022C7100,456);self.put(self.fs+0x70,1)
        self.call('sgp_shiny_control',self.fs)
        _,snapshot=self.snapshot();self.assertEqual(snapshot[21],2)
        self.u.mem_write(self.draft,snapshot[:12]+struct.pack('<HBB4B',25,1,0,0,0,0,0))
        self.assertEqual(self.call('sgp_shiny_apply',self.app,self.draft),0)
    def test_failed_generation_deletes_setup_and_retains_charge(self):
        self.configure();self.queue();self.generate_ok=0
        self.call('sgp_shiny_control',self.fs)
        self.assertEqual(self.started,0);self.assertEqual(self.deleted,1)
        self.assertEqual(self.snapshot()[1][19],40)
    def test_time_change_rejects_stale_request_without_consuming_charge(self):
        self.configure();self.queue();self.time=3
        self.call('sgp_shiny_control',self.fs)
        self.assertEqual(self.started,0);self.assertEqual(self.snapshot()[1][19],40)

if __name__=='__main__':
    import unittest;unittest.main()
