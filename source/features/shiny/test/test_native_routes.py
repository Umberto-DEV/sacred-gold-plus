"""Scoped routing ABI tests; producer and constructor are declared seams here."""
from test_native_owner import OwnerTests
import struct
from unicorn.arm_const import *

class RouteTests(OwnerTests):
    def setUp(self):
        self.constructed=[];self.producers=0;self.final_pid=0x12345678;self.ot=0xABCD1234;self.forced=False;self.corrupt_setup=False
        super().setUp()
        self.setup=0x022D0000;self.gen=0x022D1000
        self.put(self.setup+0x1C0,self.save);self.put(self.gen,self.ot)
    def nested_construct(self,species,level):
        context=self.u.context_save()
        for reg,value in zip((UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3),(0x022D2000,species,level,32)):self.u.reg_write(reg,value)
        self.u.reg_write(UC_ARM_REG_SP,0x023FD000);self.u.reg_write(UC_ARM_REG_LR,0x023EF001)
        self.u.mem_write(0x023FD000,struct.pack('<4I',1,self.final_pid,0,0))
        self.u.emu_start(self.sym['sgp_shiny_create']|1,0x023EF000,count=100000)
        self.assertEqual(self.u.reg_read(UC_ARM_REG_SP),0x023FD000)
        self.u.context_restore(context)
    def hook(self,u,a,size,_):
        x,y,z,w=[u.reg_read(r) for r in (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3)]
        if a==0x023EE100:self.ret(0)
        elif a==0x02247A18:
            self.producers+=1
            if self.corrupt_setup:self.put(self.setup+0x1C0,self.save+4)
            self.nested_construct(x,y);self.ret(0xFFFFFFFF)
        elif a==0x0206DE38:
            self.constructed.append((x,y,z,w,*struct.unpack('<4I',u.mem_read(u.reg_read(UC_ARM_REG_SP),16))));self.ret()
        elif a==0x02028E9C:self.ret(self.save+0x100)
        elif a==0x02028F84:self.ret(self.ot)
        elif a==0x0201FD2C:self.ret(0xCAFEBABE)
        elif a==0x02050724:self.ret(99)
        elif a==0x02247F30:
            self.producers+=1
            if not w:self.nested_construct(y,z)
            self.ret()
        else:super().hook(u,a,size,_)
    def generate(self,method=0,battler=1,perfect=0):
        self.assertIn('sgp_shiny_regular_impl',self.sym,'Scoped native producer hook is not implemented')
        return self.call('sgp_shiny_regular_impl',25,10,battler,perfect,self.gen,0x022D3000,self.setup,method)
    def test_regular_draw_exactly_once_final_ot_and_lowbyte(self):
        self.assertEqual(self.generate(),1);self.assertEqual(self.writes,1)
        args=self.constructed[-1];self.assertEqual(args[6:],(1,self.ot))
        self.assertEqual(args[5]&255,self.final_pid&255);self.assertEqual(args[5]%25,self.final_pid%25)
        self.assertEqual(self.call('sgp_shiny_create',0x022D2000,25,10,32,1,self.final_pid,0,0),0)
        self.assertEqual(self.constructed[-1][5:],(self.final_pid,0,0));self.assertEqual(self.writes,1)
    def test_core_failure_aborts_without_committing_lottery_or_outcome(self):
        self.put(0x023CB100+40,0x023EE101)
        self.assertEqual(self.generate(),0);self.assertEqual(self.writes,0)
        self.assertEqual(len(self.constructed),1)  # disposable native setup content
        self.put(self.setup+0x14,1);self.call('sgp_shiny_outcome',self.setup,self.fs)
        self.assertEqual(self.writes,0)
    def test_outer_abort_adapters_are_required(self):
        for name in ('sgp_shiny_static','sgp_shiny_scent_abort','sgp_shiny_scent_cleanup','sgp_shiny_script'):
            self.assertIn(name,self.sym)
    def test_gen_range_accepts_bounded_dtcm_without_widening_heap_owner(self):
        self.u.mem_map(0x027E0000,0x4000)
        for address,admitted in ((0x027E0000,True),(0x027E3FE4,True),(0x023FFFE4,True),
                                 (0x027E0001,False),(0x027E3FE8,False),(0x023FFFE8,False),
                                 (0x027DFFFC,False),(0x027E4000,False)):
            with self.subTest(gen=hex(address)):
                if 0x027E0000<=address<0x027E4000 or 0x02000000<=address<0x02400000:self.put(address,self.ot)
                old=self.writes;self.gen=address
                self.assertEqual(self.generate(),1)
                self.assertEqual(self.writes-old,int(admitted))
        self.gen=0x027E0100;self.put(self.gen,self.ot)
        self.setup=0x027E1000;self.put(self.setup+0x1C0,self.save)
        old=self.writes;self.assertEqual(self.generate(),1);self.assertEqual(self.writes,old)

    def test_final_constructor_rechecks_setup_owner_before_drawing(self):
        self.corrupt_setup=True
        self.assertEqual(self.generate(),0);self.assertEqual(self.writes,0)
    def test_excluded_scopes_are_exact_pass_through(self):
        for method,battler,perfect,btype in [(5,1,0,0),(0,0,0,0),(0,1,1,0),(0,1,0,2)]:
            self.put(self.setup,btype);self.assertEqual(self.generate(method,battler,perfect),1)
            self.assertEqual(self.constructed[-1][5:],(self.final_pid,0,0))
        self.assertEqual(self.writes,0)
    def test_outcome_consumed_once_and_flee_breaks_without_charge_reset(self):
        self.data=struct.pack('<IHBBB7x',1,25,9,1,1)
        self.assertEqual(self.generate(),1)
        for _ in range(40):self.call('sgp_shiny_step_impl',0,0,self.fs)
        self.put(self.setup+0x14,1)
        self.call('sgp_shiny_outcome',self.setup,self.fs);self.assertEqual(self.data[6],10)
        before=self.writes;self.call('sgp_shiny_outcome',self.setup,self.fs);self.assertEqual(self.writes,before)
        self.generate();self.put(self.setup+0x14,5);self.call('sgp_shiny_outcome',self.setup,self.fs)
        self.assertEqual(self.data[6],0);self.assertEqual(self.snapshot()[1][19],40)
    def test_static_forced_bypasses_and_regular_static_pauses_chain(self):
        self.assertIn('sgp_shiny_static_impl',self.sym,'Static scope is not implemented')
        self.data=struct.pack('<IHBBB7x',1,25,20,1,1)
        self.assertEqual(self.call('sgp_shiny_static_impl',self.fs,25,10,1,self.setup),1)
        self.assertEqual(self.writes,0)
        self.assertEqual(self.call('sgp_shiny_static_impl',self.fs,25,10,0,self.setup),1)
        self.assertEqual(self.writes,1);self.put(self.setup+0x14,1)
        self.call('sgp_shiny_outcome',self.setup,self.fs);self.assertEqual(self.data[6],20)

if __name__=='__main__':
    import unittest;unittest.main()
