"""Fault injection through compiled adapters and guarded native epilogues."""
from test_native_routes import RouteTests
from unicorn.arm_const import *
import struct

class AbortTests(RouteTests):
    def setUp(self):
        super().setUp();self.deletes=[];self.graphics=[];self.abort_script=False;self.script_calls=[];self.unpaused=[]
        self.u.mem_map(0x04000000,0x1000)
        self.u.mem_write(0x0205108A,bytes.fromhex('03b0f0bd'))
        self.u.mem_write(0x0203FD60,bytes.fromhex('0021417081607047'))
        self.u.mem_write(0x0224736E,bytes.fromhex('27b0f0bd'))
    def hook(self,u,a,size,_):
        x,y,z=[u.reg_read(r) for r in (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2)]
        if a==0x02051020:
            self.script_calls.append(tuple(u.reg_read(r) for r in (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3))+struct.unpack('<2I',u.mem_read(u.reg_read(UC_ARM_REG_SP),8)))
            if self.abort_script:
                context=u.context_save();u.reg_write(UC_ARM_REG_R0,self.setup);u.reg_write(UC_ARM_REG_SP,0x023FD000);u.reg_write(UC_ARM_REG_LR,0x023EF001)
                u.emu_start(self.sym['sgp_shiny_abort_static']|1,0x023EF000,count=10000);u.context_restore(context)
            self.ret()
        elif a==0x0205F5A4:self.unpaused.append(x);self.ret()
        elif a==0x02051BF8:self.deletes.append(x);self.ret()
        elif a in (0x02022C60,0x0201BB68,0x0201CB04):self.graphics.append((a,x,y,z));self.ret()
        else:super().hook(u,a,size,_)
    def test_regular_trampoline_reads_original_method_and_preserves_registers(self):
        for method in range(6):
            for i,r in enumerate((UC_ARM_REG_R4,UC_ARM_REG_R5,UC_ARM_REG_R6,UC_ARM_REG_R7)):
                self.u.reg_write(r,0xABCD0000+i)
            args=[25,10,1,0,self.gen,0x022D3000,self.setup]+[0]*7+[method]
            before=self.writes
            self.assertEqual(self.call('sgp_shiny_regular',*args),1)
            self.assertEqual(self.writes-before,int(method<5))
            for i,r in enumerate((UC_ARM_REG_R4,UC_ARM_REG_R5,UC_ARM_REG_R6,UC_ARM_REG_R7)):
                self.assertEqual(self.u.reg_read(r),0xABCD0000+i)
    def native_frame(self,entry,local_bytes,args):
        base=0x023FF000-local_bytes-20
        self.u.mem_write(base,bytes(local_bytes+20))
        self.u.mem_write(base+local_bytes,struct.pack('<5I',0x44444444,0x55555555,0x66666666,0x77777777,0x023EF001))
        self.u.reg_write(UC_ARM_REG_SP,base);self.u.reg_write(UC_ARM_REG_LR,0x023EE801)
        for r,v in zip((UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3),args):self.u.reg_write(r,v)
        self.u.reg_write(UC_ARM_REG_R4,self.setup);self.u.reg_write(UC_ARM_REG_R5,self.fs)
        return base
    def finish_frame(self,name):
        self.u.emu_start(self.sym[name]|1,0x023EF000,count=100000)
        self.assertEqual(self.u.reg_read(UC_ARM_REG_PC),0x023EF000)
        self.assertEqual(self.u.reg_read(UC_ARM_REG_SP),0x023FF000)
        for r,v in zip((UC_ARM_REG_R4,UC_ARM_REG_R5,UC_ARM_REG_R6,UC_ARM_REG_R7),(0x44444444,0x55555555,0x66666666,0x77777777)):
            self.assertEqual(self.u.reg_read(r),v)
    def test_static_failure_deletes_setup_and_skips_native_launch(self):
        self.put(0x023CB100+40,0x023EE101)
        base=self.native_frame('sgp_shiny_static',12,(self.fs,25,10,0));self.put(base,self.setup)
        self.finish_frame('sgp_shiny_static')
        self.assertEqual(self.deletes,[self.setup]);self.assertEqual(self.writes,0)
    def test_scent_failure_reads_native_setup_and_returns_false(self):
        base=self.native_frame('sgp_shiny_scent_abort',156,(0,0,0,0));self.put(base+28,self.setup)
        self.finish_frame('sgp_shiny_scent_abort')
        self.assertEqual(self.u.reg_read(UC_ARM_REG_R0),0);self.assertEqual(self.deletes,[self.setup])
    def test_script_abort_preserves_call_abi_and_stops_only_current_context(self):
        ctx=0x022E1000;self.put(ctx+0x80,self.fs);self.put(self.fs+0x3C,0x022E2000)
        self.u.mem_write(ctx+1,b'\x01');self.put(ctx+8,0x022E3000)
        self.u.reg_write(UC_ARM_REG_R5,ctx)
        args=(0x022E4000,25,10,0x022E5000,1,0)
        self.call('sgp_shiny_script',*args)
        self.assertEqual(self.script_calls,[args]);self.assertEqual(bytes(self.u.mem_read(ctx+1,1)),b'\x01')
        self.abort_script=True;self.u.reg_write(UC_ARM_REG_R5,ctx)
        self.call('sgp_shiny_script',*args)
        self.assertEqual(self.script_calls,[args,args]);self.assertEqual(self.deletes,[self.setup])
        self.assertEqual(bytes(self.u.mem_read(ctx+1,1)),b'\0');self.assertEqual(self.get(ctx+8),0)
        self.assertEqual(self.unpaused,[0x022E2000]);self.assertEqual(self.u.reg_read(UC_ARM_REG_R5),ctx)
    def test_scent_task_cleanup_restores_graphics_once(self):
        self.put(self.fs+8,0x022E0000);self.put(0x04000050,0xFFFF)
        self.u.reg_write(UC_ARM_REG_R5,self.fs)
        self.assertEqual(self.call('sgp_shiny_scent_cleanup'),1)
        self.assertEqual(self.get(0x04000050)&65535,0)
        self.assertEqual([(x[0],x[1],x[2]) for x in self.graphics],[(0x02022C60,4,0),(0x0201BB68,2,3),(0x0201CB04,0x022E0000,2),(0x02022C60,4,1)])

if __name__=='__main__':
    import unittest;unittest.main()
