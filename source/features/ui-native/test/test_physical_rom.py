"""Class B: actual guarded V4 keypad, complete mapping, and lid bodies.

ROMs are read directly. Only RAM loaded into Unicorn is patched. Hardware TP,
mic, cartridge and PM boundaries below are finite deterministic seams.
"""
import hashlib
import os
from pathlib import Path
import struct
import tempfile
import unittest
from physical_bench import *
from sgp12.blz import ndspy_load_arm9_sicuro
PINS=(
 (KEYPAD,0x10c,'079d3fd26925231957b6dd2296c500ec59876605bfaa40230ff012fc842b86da'),
 (MAPPING,0x134,'417bca15af82261332b698b605add8e4f275111f9e7b0e65eed3d5a291929b0c'),
 (LID,0xd0,'ccd36eef895ae37bf2fe3a6e0799f1066edb77eeabbd18e0d91545500a373a3e'),
 (MAIN,8,'88df72099431802e689af88c38622ee5114406db555889eb625b4c79e0ff31e7'),
 (0x0201a556,4,'0819d8d3cf7ec964d6eef45f05ee0c27b5da8823e2a41d0bc6d803b1556be8c0'),
 (MAIN,4,'1c8d071db3d544a23431095b4cd5936facacc1da035f1763d872cb268782720a'))
ROM_PINS={'EN':(147345256,'179edfb1ca331503f438e98f3afccfb0ab85759bf9ab88fb86c735f5fcefbf90'),
          'IT':(153228136,'2a2f0b437fca524c18b71b20feb01a1f51351e61c7c897ce73d9b3be1ee3a156')}
TP_REQUEST,TP_WAIT,TP_AUTO,TP_CALIBRATE=0x020da124,0x020da1b8,0x020da3a0,0x020da6e0
PAUSE,RESUME,MIC_PAUSE,MIC_RESUME=0x0202135c,0x02021328,0x02005568,0x02005584
CART,SLEEP,CARD,POWEROFF,BACK_GET,BACK_SET=0x020e10e8,0x020db43c,0x020ddb24,0x020db330,0x020db3b4,0x020db25c
class NativeBench(Bench):
    def __init__(self,compiled,code):
        super().__init__(compiled)
        self.native=True
        for p,raw in code:self.u.mem_write(p,raw)
        self.u.mem_write(0x0201a556,bl(0x0201a556,self.symbols['physical_after_native_mapping']))
        self.u.mem_write(MAIN,bl(MAIN,self.symbols['physical_lid_action']))
        self.allowed.extend(((SYSTEM+0x38,SYSTEM+0x54),(SYSTEM+0x5c,SYSTEM+0x68),(0x02111864,0x02111868)))
        self.tp_calls=[];self.hardware=[];self.busy=0;self.tp=(41,73,1,0)
        self.backlight=1;self.main_end=MAIN+8;self.sleep_count=0;self.sleep_closed_once=False
        self.raw_out=None
        self.put(SYSTEM+0x68,1,1)
    def native_allowed(self,address):
        return any(p<=address<p+n for p,n,_ in PINS[:4])
    def seam_stack(self,p,n):
        assert self.u.reg_read(UC_ARM_REG_SP)<=p<p+n<=self.stack,'hardware output not live stack'
    def hook(self,u,address,size,data):
        r0,r1=u.reg_read(UC_ARM_REG_R0),u.reg_read(UC_ARM_REG_R1)
        if address==self.main_end:
            u.reg_write(UC_ARM_REG_PC,STOP|1);return
        if address in (TP_REQUEST,TP_WAIT,TP_AUTO,TP_CALIBRATE,PAUSE,RESUME,MIC_PAUSE,MIC_RESUME,CART,SLEEP,CARD,POWEROFF,BACK_GET,BACK_SET):
            assert u.reg_read(UC_ARM_REG_SP)%8==0,'native seam stack alignment'
            self.hardware.append(address)
            if address==TP_REQUEST:
                self.tp_requests+=1;self.tp_calls.append(address);assert self.tp_requests<=2,'bounded TP request loop';self.ret(0)
            elif address in (TP_WAIT,TP_AUTO):
                self.seam_stack(r0,8);self.raw_out=r0
                self.u.mem_write(r0,struct.pack('<4H',*self.tp));self.tp_calls.append(address)
                result=1 if address==TP_WAIT and self.busy else 0
                if self.busy:self.busy-=1
                self.ret(result)
            elif address==TP_CALIBRATE:
                self.seam_stack(r0,8);self.seam_stack(r1,8);assert r1==self.raw_out
                self.u.mem_write(r0,bytes(self.u.mem_read(r1,8)));self.ret()
            elif address==SLEEP:
                self.sleep_count+=1;assert self.sleep_count<=2,'bounded native PM loop'
                assert r0 in (12,28) and r1==0 and u.reg_read(UC_ARM_REG_R2)==0
                if self.get(SLOT+28)&1:assert self.get(SLOT+16)>0 and self.get(SLOT+28)&8,'suspend must precede sleep'
                if not self.sleep_closed_once or self.sleep_count==2:self.input(1)
                self.ret()
            elif address==BACK_GET:
                self.seam_stack(r0,4);self.seam_stack(r1,4);self.put(r0,self.backlight);self.put(r1,self.backlight);self.ret()
            elif address==BACK_SET:
                assert r0==2 and r1 in (0,1);self.backlight=r1;self.ret()
            elif address==POWEROFF:raise AssertionError('unexpected native poweroff')
            elif address in (CART,CARD):self.ret(0)
            else:self.ret()
            return
        super().hook(u,address,size,data)
    def address(self,address,*args):
        self.tp_requests=0
        return super().address(address,*args)
    def keypad(self):return self.address(KEYPAD|1)
    def lid(self):
        self.main_end=MAIN+4
        try:return self.address(MAIN|1)
        finally:self.main_end=MAIN+8
    def pair(self):return self.address(MAIN|1)
    def frame(self,held,closed=False):
        self.input(held,closed);self.pair();return self.consume()
    def frozen(self):
        return [(p,bytes(self.u.mem_read(p,n))) for p,n in ((0x02000000,0x400000),(0x027e0000,0x4000),(0x027ff000,0x1000),(0x04000000,0x1000))]
    def unchanged(self,before,extra=()):
        allowed=[*self.allowed,(0x027e0080,self.stack),*extra]
        for p,old in before:
            new=bytes(self.u.mem_read(p,len(old)))
            for i,(a,b) in enumerate(zip(old,new)):
                if a!=b:assert any(lo<=p+i<hi for lo,hi in allowed),f'other mapped byte changed {p+i:08x}'

class PhysicalRomTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        canonical=SOURCE.parent/'local/experiments/balance493-2026-10-28'
        paths={lang:Path(os.environ.get('SGP_UI_PHYSICAL_'+lang,str(canonical/f'candidate-v4-{lang}.nds'))) for lang in ROM_PINS}
        missing=[lang for lang,p in paths.items() if not p.is_file()]
        if missing:
            message='canonical V4 physical native inputs missing: '+','.join(missing)
            if os.environ.get('SGP_UI_PHYSICAL_REQUIRE_INPUTS')=='1':raise AssertionError(message)
            raise unittest.SkipTest(message)
        import ndspy.rom
        cls.codes={}
        for lang,p in paths.items():
            digest=hashlib.sha256()
            with p.open('rb') as stream:
                for block in iter(lambda:stream.read(1024*1024),b''):digest.update(block)
            assert (p.stat().st_size,digest.hexdigest())==ROM_PINS[lang],f'wrong V4 {lang}'
            rom=ndspy.rom.NintendoDSRom.fromFile(p);sections=ndspy_load_arm9_sicuro(rom).sections;code=[]
            for address,n,want in PINS:
                matches=[s for s in sections if s.ramAddress<=address<address+n<=s.ramAddress+len(s.data)]
                assert len(matches)==1,'pin extent'
                s=matches[0];raw=bytes(s.data[address-s.ramAddress:address-s.ramAddress+n])
                assert hashlib.sha256(raw).hexdigest()==want,f'pin {lang} {address:08x}'
                code.append((address,raw))
            cls.codes[lang]=code
            del rom,sections
        cls.temp=tempfile.TemporaryDirectory(prefix='physical-b-');cls.addClassCleanup(cls.temp.cleanup)
        cls.compiled=compile_physical(Path(cls.temp.name))
    def benches(self):
        for lang,code in self.codes.items():
            yield NativeBench(self.compiled,code)
    def test_actual_complete_mapping_physical_and_simulated_input(self):
        for b in self.benches():
            b.activate();b.release();b.put(SYSTEM+0x34,3)
            start=b.mapping_calls;before=b.frozen();self.assertEqual(b.frame(0x200),1)
            self.assertEqual(b.mapping_calls,start+1);self.assertEqual(b.get(SYSTEM+0x44),1)
            self.assertEqual(b.sample()[2:5],(0x200,0x200,0x200));b.unchanged(before,((KEY,KEY+2),(SHARED,SHARED+2)))
            b.frame(0);b.put(SYSTEM+0x5c,1);b.frame(0)
            self.assertEqual(b.get(SYSTEM+0x44),1);self.assertEqual(b.sample()[2:5],(0,0,0));self.assertEqual(b.get(SYSTEM+0x5c),0)
            b.frame(0);b.put(SYSTEM+0x5c,1);b.frame(1)
            self.assertEqual(b.sample()[2:5],(1,1,1))
            b.frame(0);b.frame(0x201);self.assertEqual(b.sample()[2:5],(0x201,0x201,0x201))
    def test_all_actual_button_modes_leave_independent_physical_streams(self):
        for b in self.benches():
            b.activate();b.release()
            for mode,physical,native in ((0,0x200,0x200),(1,8,0x408),(2,0x400,0x800),(3,0x200,1)):
                b.frame(0);b.put(SYSTEM+0x34,mode);b.frame(physical)
                self.assertEqual(b.get(SYSTEM+0x44),native)
                self.assertEqual(b.sample()[2:5],(physical,physical,physical))
    def test_native_closed_raw_retention_missing_cycle_and_rearm(self):
        for b in self.benches():
            b.activate();b.release();b.input(1);b.lid();b.keypad() # leave pending
            serial=b.get(SLOT+8);raw=bytes(b.u.mem_read(SYSTEM+0x38,12));start=b.mapping_calls
            b.input(1);b.lid();b.input(1,True);before=b.frozen();b.keypad();b.unchanged(before)
            self.assertEqual(b.mapping_calls,start);self.assertEqual(bytes(b.u.mem_read(SYSTEM+0x38,12)),raw)
            self.assertEqual(b.get(SLOT+8),serial);self.assertEqual(b.get(SYSTEM+0x44),0)
            b.input(1);old=bytes(b.u.mem_read(OUT,16));self.assertEqual(b.consume(),0);self.assertEqual(bytes(b.u.mem_read(OUT,16)),old)
            b.frame(1);self.assertEqual(b.sample()[3:],(0,0,1));b.release();b.frame(1);self.assertEqual(b.sample()[3],1)
    def test_native_touch_auto_request_busy_and_validity_tail(self):
        for b in self.benches():
            b.activate();b.release();self.assertEqual((b.get(SYSTEM+0x60,2),b.get(SYSTEM+0x62,2)),(41,73))
            b.put(SYSTEM+0x68,0,1);b.busy=1;b.tp_calls=[];b.frame(0)
            self.assertEqual(b.tp_calls,[TP_REQUEST,TP_WAIT,TP_REQUEST,TP_WAIT])
            self.assertEqual((b.get(SYSTEM+0x64,2),b.get(SYSTEM+0x66,2)),(0,1))
            b.tp=(99,100,1,1);b.frame(0);self.assertEqual((b.get(SYSTEM+0x60,2),b.get(SYSTEM+0x62,2)),(41,100))
            b.tp=(88,101,1,2);b.frame(0);self.assertEqual((b.get(SYSTEM+0x60,2),b.get(SYSTEM+0x62,2)),(88,100))
            b.tp=(0,0,0,3);b.frame(0);self.assertEqual(b.get(SYSTEM+0x66,2),0)
    def test_fold_race_after_actual_mapping_before_adapter_final_read(self):
        for b in self.benches():
            b.activate();b.release();b.input(1);b.lid();seen=[];serial=b.get(SLOT+8)
            def race(x,p,n):
                if p==SHARED:
                    seen.append(p)
                    if len(seen)==3:x.input(1,True)
            b.read_callback=race;b.keypad();b.read_callback=None
            self.assertEqual(b.get(SYSTEM+0x44),1);self.assertEqual(b.get(SLOT+8),serial)
            self.assertEqual(b.consume(),2);self.assertEqual(b.sample(),(0,1,0,0,0,0))
    def test_actual_lid_sleep_resume_disabled_and_open_backlight(self):
        for b in self.benches():
            b.activate();b.release();start=b.lid_calls;b.input(1,True);before=b.frozen();b.lid();b.unchanged(before,((SHARED,SHARED+2),(KEY,KEY+2)))
            self.assertEqual(b.lid_calls,start+1);self.assertEqual(b.sleep_count,1)
            self.assertEqual(b.hardware[-7:],[PAUSE,MIC_PAUSE,CART,SLEEP,CARD,RESUME,MIC_RESUME])
            self.assertEqual(b.consume(),2);self.assertEqual(b.call('physical_ack_suspend',OWNER,1,1),1)
            b.frame(1);self.assertEqual(b.sample()[3:],(0,0,1));b.release()
            b.put(SYSTEM+0x6b,1,1);b.input(0,True);b.lid();self.assertEqual(b.backlight,0);self.assertEqual(b.get(SLOT+16),2)
            b.lid();self.assertEqual(b.get(SLOT+16),2);b.input(0);b.lid();self.assertEqual(b.backlight,0)
            self.assertEqual(b.hardware[-3:],[BACK_GET,RESUME,BACK_SET])
    def test_actual_native_sleep_loop_is_bounded_and_suspension_precedes_pm(self):
        for b in self.benches():
            b.activate();b.sleep_closed_once=True;b.input(0,True);b.lid()
            self.assertEqual(b.sleep_count,2);self.assertEqual(b.get(0x02111864),1);self.assertEqual(b.get(SLOT+16),1)
    def test_inactive_actual_hooks_keep_native_behavior_without_slot_stores(self):
        for b in self.benches():
            before=b.frozen();b.input(0x200);b.put(SYSTEM+0x34,3);saved=b.slot();b.pair()
            self.assertEqual((b.mapping_calls,b.lid_calls),(1,1));self.assertEqual(b.get(SYSTEM+0x44),1);self.assertEqual(b.slot(),saved)
            self.assertFalse(any(SLOT<=p<SLOT+48 for p,n,v in b.writes))
            b.unchanged(before,((KEY,KEY+2),(SHARED,SHARED+2),(SYSTEM+0x34,SYSTEM+0x38)))
            b.input(0,True);b.lid();self.assertEqual(b.sleep_count,1);self.assertEqual(b.slot(),saved)
            self.assertFalse(any(SLOT<=p<SLOT+48 for p,n,v in b.writes))
if __name__=='__main__':unittest.main()
