"""Class A production API/hooks on ARM; synthetic hardware/native callees."""
from pathlib import Path
import tempfile
import unittest
from physical_bench import *
class PhysicalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory(prefix='physical-a-');cls.addClassCleanup(cls.temp.cleanup)
        cls.compiled=compile_physical(Path(cls.temp.name))
    def test_activation_lease_is_nonzero(self):
        b=Bench(self.compiled)
        self.assertEqual(b.activate(),1)
    def test_invalid_busy_and_pointer_reuse_preserve_live_lease(self):
        b=Bench(self.compiled)
        for owner,mask in ((0,0xf03),(OWNER+1,0xf03),(SLOT,0xf03),(0x02400000,0xf03),(OWNER,0),(OWNER,0x8000)):
            self.assertEqual(b.activate(owner,mask),0)
        self.assertEqual(b.activate(),1);saved=b.slot()
        self.assertEqual(b.activate(),0);self.assertEqual(b.slot(),saved)
        for owner,token in ((OWNER+4,1),(OWNER,2),(OWNER,0)):
            b.u.mem_write(OUT,b'X'*16)
            self.assertEqual(b.consume(token,owner),3);self.assertEqual(bytes(b.u.mem_read(OUT,16)),b'X'*16)
            self.assertEqual(b.call('physical_deactivate',owner,token),0)
            self.assertEqual(b.call('physical_ack_suspend',owner,token,0),0)
            self.assertEqual(b.slot(),saved)
        self.assertEqual(b.call('physical_deactivate',OWNER,1),1)
        self.assertEqual(b.activate(),2);self.assertEqual(b.consume(1),3)
    def test_release_edges_duplicate_missing_and_output_validation(self):
        b=Bench(self.compiled);b.activate();b.u.mem_write(OUT,b'X'*16)
        self.assertEqual(b.consume(),0);self.assertEqual(bytes(b.u.mem_read(OUT,16)),b'X'*16)
        for held in (0xf03,0x201):
            self.assertEqual(b.frame(held),1);self.assertEqual(b.sample()[3:],(0,0,1))
        self.assertEqual(b.frame(0x40),1);self.assertEqual(b.sample()[2:],(0x40,0,0,1))
        self.assertEqual(b.frame(0x241),1);self.assertEqual(b.sample()[2:],(0x241,0x201,0x201,0))
        saved=b.slot();out=bytes(b.u.mem_read(OUT,16));self.assertEqual(b.consume(),0);self.assertEqual(b.slot(),saved);self.assertEqual(bytes(b.u.mem_read(OUT,16)),out)
        self.assertEqual(b.frame(0x240),1);self.assertEqual(b.sample()[3:],(0,0,0))
        for p in (0,OUT+1,SLOT,SLOT+32,0x0226ec3c,0x023bfff4,0x027e007c,0x027e3774,0xfffffff8):
            self.assertEqual(b.consume(out=p),3)
        # Real aligned local above the callee stack is admitted.
        self.assertEqual(b.frame(0),1)
        b.call('physical_lid_action');b.call('physical_after_native_mapping')
        b.stack=0x027e3740;b.allowed.append((0x027e3770,0x027e3780))
        self.assertEqual(b.consume(out=0x027e3770),1)
        # Prior pending frame expires at the next open lid entry even if no
        # observer catches closed keypad -> open consume.
        b.input(1);b.call('physical_lid_action');b.call('physical_after_native_mapping')
        b.call('physical_lid_action');b.input(1,True);b.input(1)
        self.assertEqual(b.consume(),0)
        self.assertEqual(b.frame(1),1);self.assertEqual(b.sample()[3:],(0,0,1))
        b.release();self.assertEqual(b.frame(1),1);self.assertEqual(b.sample()[3:],(1,1,0))
    def test_repeat_defaults_full_mask_changes_and_machine_timer_bits(self):
        b=Bench(self.compiled);b.activate();b.release()
        repeats=[]
        for n in range(1,18):
            b.frame(0x40)
            if b.sample()[4]:repeats.append(n)
        self.assertEqual(repeats,[1,9,13,17])
        b.frame(0x44);self.assertEqual(b.sample()[3:5],(4,4));self.assertEqual(b.get(SLOT+24),8)
        b.frame(0x40);self.assertEqual(b.sample()[3:5],(0,0));self.assertEqual(b.get(SLOT+24),8)
        b.put(SYSTEM+0x58,2);b.frame(0x80);self.assertEqual(b.get(SLOT+24),2)
        b.put(SYSTEM+0x54,3);b.frame(0x80);b.frame(0x80);self.assertEqual(b.sample()[4],0x80);self.assertEqual(b.get(SLOT+24),3)
        for delay,want in ((0,0xffffffff),(0xffffffff,0xfffffffe)):
            b.put(SYSTEM+0x58,delay);b.frame(0);b.frame(0x20);b.frame(0x20)
            self.assertEqual(b.get(SLOT+24),want);self.assertEqual(b.sample()[4],0)
        b.put(SLOT+24,1);b.put(SYSTEM+0x54,0);b.frame(0x20);self.assertEqual(b.sample()[4],0x20);self.assertEqual(b.get(SLOT+24),0)
    def test_suspend_ack_blocking_and_closed_episode(self):
        b=Bench(self.compiled);b.activate();b.release();b.frame(1)
        b.input(1,True)
        b.lid_callback=lambda x:(self.assertEqual(x.get(SLOT+16),1),x.input(1))
        b.call('physical_lid_action');self.assertEqual(b.consume(),2);self.assertEqual(b.sample(),(0,1,0,0,0,0))
        b.call('physical_after_native_mapping');self.assertEqual(b.consume(),2)
        self.assertEqual(b.call('physical_ack_suspend',OWNER,1,0),0)
        self.assertEqual(b.call('physical_ack_suspend',OWNER,1,1),1)
        b.lid_callback=None
        self.assertEqual(b.frame(1),1);self.assertEqual(b.sample()[3:],(0,0,1));b.release();b.frame(1);self.assertEqual(b.sample()[3],1)
        b.input(1,True);b.call('physical_lid_action');b.call('physical_lid_action');self.assertEqual(b.get(SLOT+16),2)
        self.assertEqual(b.call('physical_ack_suspend',OWNER,1,2),0)
        self.assertEqual(b.consume(),2)
    def test_each_closed_observer_fails_closed_on_suspend_exhaustion(self):
        for observer in ('physical_lid_action','physical_after_native_mapping','physical_consume','physical_ack_suspend'):
            b=Bench(self.compiled);b.activate();b.release();b.put(SLOT+16,0xffffffff);b.input(1,True)
            b.u.mem_write(OUT,b'Z'*16)
            args=(OWNER,1,OUT) if observer=='physical_consume' else (OWNER,1,0xffffffff) if observer=='physical_ack_suspend' else ()
            b.call(observer,*args);self.assertEqual(b.consume(),3)
            self.assertEqual(bytes(b.u.mem_read(OUT,16)),b'Z'*16);self.assertEqual(b.activate(),2)
    def test_fold_race_serial_last_and_inactive_no_slot_writes(self):
        b=Bench(self.compiled);b.call('physical_after_native_mapping');b.call('physical_lid_action')
        self.assertEqual((b.mapping_calls,b.lid_calls),(1,1));self.assertEqual(b.slot(),bytes(48))
        b.activate();b.release();b.writes.clear();b.frame(1)
        slotstores=[x for x in b.writes if SLOT<=x[0]<SLOT+48]
        self.assertEqual(slotstores[-2][0],SLOT+8) # consume marks consumed next
        b.input(0);b.call('physical_lid_action');seen=[]
        def race(x,p,n):
            if p==SHARED:
                seen.append(p)
                if len(seen)==2:x.input(0,True)
        b.read_callback=race;b.call('physical_after_native_mapping');b.read_callback=None
        self.assertEqual(b.consume(),2);self.assertEqual(b.sample()[0],0)
        b.call('physical_deactivate',OWNER,1);saved=b.slot();b.input(0,True)
        b.call('physical_after_native_mapping');b.call('physical_lid_action');self.assertEqual(b.slot(),saved)
    def test_fail_closed_serial_suspend_and_generation_exhaustion(self):
        for offset,closed in ((8,False),(16,True)):
            b=Bench(self.compiled);b.activate();b.release();b.put(SLOT+offset,0xffffffff)
            b.input(1,closed);b.call('physical_after_native_mapping');self.assertEqual(b.consume(),3)
            self.assertEqual(b.activate(),2)
        b=Bench(self.compiled);b.put(SLOT+4,0xfffffffe);self.assertEqual(b.activate(),0xffffffff)
        b.call('physical_deactivate',OWNER,0xffffffff);self.assertEqual(b.activate(),0);saved=b.slot()
        b.call('physical_deactivate',OWNER,0xffffffff);self.assertEqual(b.activate(),0);self.assertEqual(b.slot(),saved)
    def test_reserved_slot_bytes_stay_zero_and_hooks_never_read_owner(self):
        b=Bench(self.compiled);b.activate();b.release()
        self.assertEqual(b.get(SLOT+42,2),0)
        b.frame(0x201);b.input(0,True);b.call('physical_lid_action');b.consume()
        self.assertFalse(any(OWNER<=p<OWNER+4 for p,n in b.reads))
    def test_consume_observed_fold_never_leaves_pending_payload_replayable(self):
        b=Bench(self.compiled);b.activate();b.release();b.input(1)
        b.call('physical_lid_action');b.call('physical_after_native_mapping')
        seen=[]
        def close(x,p,n):
            if p==SHARED:
                seen.append(p)
                if len(seen)==2:x.input(1,True)
        b.read_callback=close
        self.assertEqual(b.consume(),2)
        b.read_callback=None;b.input(1)
        self.assertEqual(b.consume(),2);self.assertEqual(b.sample()[0],0)
    def test_configuration_is_mandatory_and_payload_stays_bounded(self):
        with tempfile.TemporaryDirectory(prefix='physical-config-') as t:
            result=subprocess.run(['clang',*FLAGS,'-c',str(SOURCE/'features/ui-native/physical.c'),'-o',str(Path(t)/'bad.o')],capture_output=True)
            self.assertNotEqual(result.returncode,0)
            self.assertIn(b'explicit slot and native address configuration',result.stderr)
        self.assertLessEqual(len(self.compiled[0]),2048)
    def test_actual_settings_reducer_keeps_physical_identity_and_cancelled_metadata(self):
        import ctypes as C
        spec=importlib.util.spec_from_file_location('physical_model_types',SOURCE/'features/settings-ui/test/test_state.py')
        model=importlib.util.module_from_spec(spec);spec.loader.exec_module(model)
        with tempfile.TemporaryDirectory(prefix='physical-model-') as t:
            libfile=Path(t)/'model.dylib'
            subprocess.run(['clang','-std=c11','-shared','-fPIC','-O2',str(SOURCE/'features/settings-ui/state.c'),'-o',str(libfile)],check=True,capture_output=True)
            lib=C.CDLL(str(libfile));lib.settings_keys.restype=C.c_uint
            p=model.Snapshot();p.editable_rows=0x3fff;s=model.State()
            lib.settings_init(C.byref(s),C.byref(p))
            b=Bench(self.compiled);b.activate()
            def apply(held):
                self.assertEqual(b.frame(held),1)
                serial,suspend,physical,pressed,repeated,flags=b.sample()
                new=lib.settings_keys(pressed,pressed,0);rep=lib.settings_keys(repeated,repeated,0)
                lib.settings_sample(C.byref(s),physical,1,0)
                result=lib.settings_step(C.byref(s),new,rep)
                return new,rep,result
            self.assertEqual(apply(0),(0,0,0))
            self.assertEqual(apply(0x10),(0x10,0x10,1));self.assertEqual(s.draft.native.text,1)
            apply(0)
            new,rep,result=apply(0x30)
            self.assertEqual(new,0x80000000);self.assertEqual(rep,0x80000000);self.assertEqual(result,0)
            self.assertEqual(s.draft.native.text,1)
            apply(0);new,rep,result=apply(0x300)
            self.assertEqual(new,0x80000000);self.assertEqual(result,0)
            apply(0);new,rep,result=apply(0x201)
            self.assertEqual(new,0x201);self.assertEqual(result,1);self.assertEqual(s.view,1)
    def test_cpsr_and_ime_controls_across_all_operations(self):
        for controls in (0x1f,0x5f,0x9f,0xdf):
            b=Bench(self.compiled);b.u.reg_write(UC_ARM_REG_CPSR,controls);b.put(IME,0)
            b.activate();b.release();b.frame(1);b.consume();b.input(0,True);b.call('physical_lid_action');b.consume();b.input(0)
            b.call('physical_ack_suspend',OWNER,1,1);b.call('physical_deactivate',OWNER,1)
if __name__=='__main__':unittest.main()
