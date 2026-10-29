"""Private-ROM actual CreateMon differential, never mocking Get/SetMonData.

OS heap, NARC reads and localized name strings are service seams. This is a
machine-level constructor proof, not a field/battle gameplay test.
"""
from pathlib import Path
import importlib.util,json,os,struct,sys,tempfile,unittest
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from sgp13 import shiny,shiny_core
spec=importlib.util.spec_from_file_location('shiny_constructor_bench',ROOT/'features/training-native/test/native_bench.py')
bm=importlib.util.module_from_spec(spec);spec.loader.exec_module(bm)
from unicorn.arm_const import *
ROM_DIR=Path(os.environ.get('SGP_SHINY_ROM_DIR',ROOT.parent/'local/experiments/save-ui-2026-10-28/integration'))

class ConstructorBench(bm.Bench):
    def __init__(self,path,temp,blob,symbols,core,cs):
        report=Path(temp)/'empty-symbols.json';report.write_text('{"symbols":{"training_native_save":1}}')
        super().__init__(path,report)
        self.native=symbols;self.mu.mem_write(0x023C9100,blob);self.mu.mem_write(0x023C8100,core)
        self.fs=0x022D0000;self.setup=0x022D1000;self.gen=0x022D2000;self.options=0x022D3000
        self.ot=0xABCD1234;self.pid=0x12345678;self.saved=bytes(16);self.constructor=None;self.actual_producer=False;self.party_count=0
        cfg=shiny.configuration('EN',{'training_shiny_access':0x023EE001,'training_shiny_bind':0x023EE005,'training_read':0x023EE009},
          dict.fromkeys(('sgp_ui_frame','opz_apri','opz_chiudi','opz_disegna'),0x023EE021),symbols,
          {'sgp_shiny_capture':0x023EE00D,'sgp_shiny_dispatch':0x023EE011},cs)
        self.mu.mem_write(0x023CB100,cfg);self.put(self.fs+12,bm.SAVE);self.put(0x021D4158,self.fs)
        self.put(self.setup+0x1C0,bm.SAVE);self.put(self.gen,self.ot)
        self.call(symbols['sgp_shiny_continue'],0)
    def member(self,narc,member):
        if narc in (11,33):
            import ndspy.narc
            if narc not in self.archives:self.archives[narc]=ndspy.narc.NARC(self.rom.getFileByName({11:'a/0/1/1',33:'a/0/3/3'}[narc]))
            return bytes(self.archives[narc].files[member])
        return super().member(narc,member)
    def hook(self,u,a,size,_):
        x,y,z,w=[u.reg_read(r) for r in bm.REGS]
        if a==0x0200BCDC:
            p=self.alloc(12);u.mem_write(p,struct.pack('<HHIHH',2,1,0xB6F8D2EC,0x012B,0xFFFF));self.ret(p)
        elif a==0x0203DFE0:self.ret(self.fs)
        elif a==0x02028EA8:self.ret(self.options)
        elif a==0x02028E9C:self.ret(bm.SAVE+0x100)
        elif a==0x02028F84:self.ret(self.ot)
        elif a==0x02074904:self.ret(bm.SAVE+0x1000)
        elif a==0x02074640:self.ret(self.party_count)
        elif a==0x02074644:self.ret(bm.MON)
        elif a==0x023EE008:u.reg_write(UC_ARM_REG_PC,0x0206E541)
        elif a==0x023EE004:self.ret()
        elif a==0x023EE000:
            if z:self.saved=bytes(u.mem_read(y,16))
            else:u.mem_write(y,self.saved)
            self.ret(1)
        elif a==0x02074524 and self.actual_producer:
            u.mem_write(bm.MON,bytes(u.mem_read(y,236)));self.ret(1)
        elif a==0x02247A18 and not self.actual_producer:
            context=u.context_save()
            if self.constructor is None:address,args=self.native['sgp_shiny_create'],(bm.MON,x,y,32,1,self.pid,0,0)
            else:address,tail=self.constructor;args=(bm.MON,x,y,32,*tail)
            self.call_low(address,*args)
            self.put(bm.ARGS,self.ot);self.call_low(0x0206EC40,bm.MON,7,bm.ARGS)
            u.context_restore(context);self.ret()
        else:super().hook(u,a,size,_)
    def call_low(self,address,*args):
        for i,r in enumerate(bm.REGS):self.mu.reg_write(r,args[i] if i<len(args) else 0)
        self.mu.reg_write(UC_ARM_REG_SP,0x023FD000);self.mu.reg_write(UC_ARM_REG_LR,bm.STOP|1)
        for i,v in enumerate(args[4:]):self.put(0x023FD000+i*4,v)
        self.mu.emu_start(address|1,bm.STOP,count=2000000)
        if self.mu.reg_read(UC_ARM_REG_PC)!=bm.STOP:raise AssertionError('nested instruction budget')
        if self.mu.reg_read(UC_ARM_REG_SP)!=0x023FD000:raise AssertionError('nested stack balance')
    def fields(self):return {f:self.get(f) for f in (0,3,5,6,7,8,10,54,55,56,57,58,59,60,61,70,71,72,73,74,75,111,112,160,161,162,163,164,165,166,167,168,169)}

class RegularDTCMBench(ConstructorBench):
    """Real Regular/producer/constructor path; slot/Plus/OS/storage services seamed."""
    def __init__(self,*args):
        self.track_lottery=False;self.draws=0;self.commits=0;self.native_final=[]
        super().__init__(*args)
        self.mu.mem_map(0x027E0000,0x4000)
    def hook(self,u,a,size,_):
        # Selection/suppression helpers choose the first legitimate fixture slot.
        seams={0x02248150:0,0x0224768C:0,0x02247720:0,0x02247764:0,
               0x0224779C:0,0x022477C0:0,0x022485B0:0,0x022478A4:35,
               0x023D81F0:0,0x022481EC:0,0x02248290:0,0x02050724:99}
        if a in seams:self.ret(seams[a]);return
        if self.track_lottery:
            if a==self.draw_address:self.draws+=1
            if a==0x023EE000 and u.reg_read(UC_ARM_REG_R2):self.commits+=1
            if a==0x0206DE38:
                self.native_final.append(struct.unpack('<4I',u.mem_read(u.reg_read(UC_ARM_REG_SP),16)))
        super().hook(u,a,size,_)
    def dtcm_call(self,address,*args):
        sp=0x027E3F00
        for i,r in enumerate(bm.REGS):self.mu.reg_write(r,args[i] if i<len(args) else 0)
        for i,v in enumerate(args[4:]):self.put(sp+i*4,v)
        self.mu.reg_write(UC_ARM_REG_SP,sp);self.mu.reg_write(UC_ARM_REG_LR,bm.STOP|1)
        self.mu.emu_start(address|1,bm.STOP,count=2000000)
        assert self.mu.reg_read(UC_ARM_REG_PC)==bm.STOP
        assert self.mu.reg_read(UC_ARM_REG_SP)==sp
        return self.mu.reg_read(UC_ARM_REG_R0)

class NativeConstructorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not all((ROM_DIR/f'candidate-{lang}.nds').exists() for lang in ('EN','IT')):
            raise unittest.SkipTest('private EN/IT integration cartridges unavailable')
        cls.temp=tempfile.TemporaryDirectory();cls.blob,cls.symbols=shiny.compile_native(cls.temp.name);cls.core,cls.cs=shiny_core.compile_native(cls.temp.name)
    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()
    def test_native_constructor_preserves_iv_ability_gender_stats_and_rng(self):
        for language in ('EN','IT'):
            for species,pid in ((25,0x12345678),(201,0xDEADBEEF),(292,0x12345678),(133,0x0000001F)):
                with self.subTest(language=language,species=species):
                    b=ConstructorBench(ROM_DIR/f'candidate-{language}.nds',self.temp.name,self.blob,self.symbols,self.core,self.cs)
                    b.pid=pid;seed=0x31415926
                    previous=((0x00001234-1013904223)*pow(1664525,-1,2**32))&0xFFFFFFFF
                    b.saved=struct.pack('<IHBBB7x',previous,0,0,0,1)
                    b.call(0x0201FD38,seed);b.call(0x0206DE38,bm.MON,species,35,32,1,pid,0,0);b.set(7,b.ot)
                    baseline=b.fields();end_seed=b.call(0x0201FD2C)
                    b.call(0x0201FD38,seed)
                    self.assertEqual(b.call(self.symbols['sgp_shiny_regular_impl'],species,35,1,0,b.gen,bm.MON+0x400,b.setup,0),1)
                    actual=b.fields();self.assertEqual(b.call(0x0201FD2C),end_seed)
                    self.assertEqual(actual[0]&255,pid&255);self.assertEqual(actual[0]%25,pid%25)
                    self.assertEqual(actual[7],b.ot);self.assertEqual(actual[3],0)
                    self.assertLess((actual[0]>>16)^(actual[0]&65535)^(b.ot>>16)^(b.ot&65535),255)
                    for field in baseline:
                        if field!=0:self.assertEqual(actual[field],baseline[field],f'native field {field}')
                    self.assertEqual(b.assertions,0)
    def test_native_nature_and_gender_constructor_loops_preserve_rng(self):
        from sgp12.rom import bl_thumb
        for language in ('EN','IT'):
            for address,tail,site in ((0x0206E108,(17,),0x0206E142),(0x0206E14C,(1,17,0),0x0206E1E4)):
                with self.subTest(language=language,constructor=hex(address)):
                    b=ConstructorBench(ROM_DIR/f'candidate-{language}.nds',self.temp.name,self.blob,self.symbols,self.core,self.cs)
                    b.call(0x0201FD38,0x12345678);b.call(address,bm.MON,25,35,32,*tail);b.set(7,b.ot)
                    baseline=b.fields();end_seed=b.call(0x0201FD2C)
                    b.mu.mem_write(site,bl_thumb(site,self.symbols['sgp_shiny_create']));b.mu.ctl_remove_cache(site,site+4)
                    b.constructor=address,tail
                    b.saved=struct.pack('<IHBBB7x',((0x1234-1013904223)*pow(1664525,-1,2**32))&0xFFFFFFFF,0,0,0,1)
                    b.call(0x0201FD38,0x12345678)
                    self.assertEqual(b.call(self.symbols['sgp_shiny_regular_impl'],25,35,1,0,b.gen,bm.MON+0x400,b.setup,0),1)
                    actual=b.fields();self.assertEqual(b.call(0x0201FD2C),end_seed)
                    self.assertEqual(actual[0]%25,17);self.assertEqual(actual[0]&255,baseline[0]&255)
                    for field in baseline:
                        if field!=0:self.assertEqual(actual[field],baseline[field],f'native field {field}')
                    self.assertEqual(b.assertions,0)
    def test_actual_producer_preserves_native_item_and_form_draws(self):
        from sgp12.rom import bl_thumb
        for language in ('EN','IT'):
            for species,ability in ((25,0),(25,28),(25,56),(201,0)):
                with self.subTest(language=language,species=species,ability=ability):
                    b=ConstructorBench(ROM_DIR/f'candidate-{language}.nds',self.temp.name,self.blob,self.symbols,self.core,self.cs)
                    overlay=b.rom.loadArm9Overlays()[2];b.mu.mem_write(overlay.ramAddress,bytes(overlay.data));b.actual_producer=True
                    b.call(0x0206DE38,bm.MON,25,35,32,1,0x12345678,1,b.ot)
                    lead=bm.MON+0x400;b.mu.mem_write(lead,bytes(b.mu.mem_read(bm.MON,236)))
                    b.mu.mem_write(b.gen+13,bytes([0,ability]));b.mu.mem_write(b.gen+17,bytes([1,1,1,1,1]))
                    b.put(b.setup+8,0x022D4000)
                    b.call(0x0201FD38,0x12345678);b.call(0x02247A18,species,35,1,0,b.gen,lead,b.setup)
                    baseline=b.fields();end_seed=b.call(0x0201FD2C)
                    for site in (0x0206E142,0x0206E1E4):
                        b.mu.mem_write(site,bl_thumb(site,self.symbols['sgp_shiny_create']));b.mu.ctl_remove_cache(site,site+4)
                    b.saved=struct.pack('<IHBBB7x',((0x1234-1013904223)*pow(1664525,-1,2**32))&0xFFFFFFFF,0,0,0,1)
                    b.call(0x0201FD38,0x12345678)
                    self.assertEqual(b.call(self.symbols['sgp_shiny_regular_impl'],species,35,1,0,b.gen,lead,b.setup,0),1)
                    actual=b.fields();self.assertEqual(b.call(0x0201FD2C),end_seed)
                    self.assertEqual(actual[0]&255,baseline[0]&255);self.assertEqual(actual[0]%25,baseline[0]%25)
                    for field in baseline:
                        if field!=0:self.assertEqual(actual[field],baseline[field],f'native field {field}')
                    self.assertEqual(b.assertions,0)
    def test_actual_regular_dtcm_stack_and_gen_commit_then_settle_once(self):
        from sgp12.rom import bl_thumb
        for language in ('EN','IT'):
            for method in range(5):
                for dtcm_gen in (False,True):
                    with self.subTest(language=language,method=method,dtcm_gen=dtcm_gen):
                        b=RegularDTCMBench(ROM_DIR/f'candidate-{language}.nds',self.temp.name,self.blob,self.symbols,self.core,self.cs)
                        ov=b.rom.loadArm9Overlays()[2];b.mu.mem_write(ov.ramAddress,bytes(ov.data));b.actual_producer=True
                        b.call(0x0206DE38,bm.MON,25,35,32,1,0x12345678,1,b.ot)
                        lead=bm.MON+0x400;b.mu.mem_write(lead,bytes(b.mu.mem_read(bm.MON,236)))
                        gen=0x027E3F60 if dtcm_gen else b.gen
                        b.mu.mem_write(gen,struct.pack('<I',b.ot)+bytes(24))
                        slots=0x022D5000;b.mu.mem_write(slots,struct.pack('<IHH',75,35,35)*12)
                        b.put(b.setup+8,0x022D4000)
                        for site,name in ((0x0206E142,'sgp_shiny_create'),(0x0206E1E4,'sgp_shiny_create'),(0x02247D96,'sgp_shiny_regular')):
                            b.mu.mem_write(site,bl_thumb(site,self.symbols[name]));b.mu.ctl_remove_cache(site,site+4)
                        b.mu.mem_write(0x02247D9A,bytes.fromhex('c046'))
                        b.saved=struct.pack('<IHBBB7x',0,75,0,1,0)
                        b.draw_address=self.cs['sgp_shiny_draw']&~1;b.track_lottery=True
                        b.call(0x0201FD38,0x12345678)
                        self.assertEqual(b.dtcm_call(0x02247B64,lead,0 if method==2 else 255,gen,slots,method,1,b.setup),1)
                        self.assertEqual((b.draws,b.commits,b.saved[8]),(1,1,1))
                        self.assertNotEqual(struct.unpack_from('<I',b.saved)[0],0)
                        self.assertEqual(b.native_final[-1][2:],(1,b.ot))
                        self.assertEqual(b.u32(0x023CB200+680),1)  # pending outcome
                        b.put(b.setup+0x14,1)
                        self.assertEqual(b.dtcm_call(self.symbols['sgp_shiny_outcome'],b.setup,b.fs),99)
                        self.assertEqual((b.saved[6],b.commits,b.u32(0x023CB200+680)),(1,2,0))
                        b.dtcm_call(self.symbols['sgp_shiny_outcome'],b.setup,b.fs)
                        self.assertEqual((b.saved[6],b.commits,b.draws),(1,2,1))
                        self.assertEqual(b.assertions,0)

    def test_continue_stat_refresh_preserves_damage_faint_and_box_identity(self):
        for language in ('EN','IT'):
            for species in (20,493):
                for hp in (0,20):
                    with self.subTest(language=language,species=species,hp=hp):
                        b=ConstructorBench(ROM_DIR/f'candidate-{language}.nds',self.temp.name,self.blob,self.symbols,self.core,self.cs)
                        b.mu.mem_write(0x023CB100+84,struct.pack('<HH',493,0)+b'\xfe'+b'\xff'*60+b'\x3f\0\0')
                        b.call(0x0206DE38,bm.MON,species,35,32,1,0x12345678,1,b.ot)
                        b.set(163,hp);b.set(160,8)
                        before_box=bytes(b.mu.mem_read(bm.MON,136));old_max=b.get(164)
                        old_stats=[b.get(field) for field in range(165,170)]
                        personal=bytearray(b.archives[2].files[species])
                        personal[:6]=bytes(value+20 for value in personal[:6])
                        b.archives[2].files[species]=bytes(personal)
                        b.party_count=1;b.call(self.symbols['sgp_shiny_continue'],0)
                        new_max=b.get(164);self.assertGreater(new_max,old_max)
                        self.assertEqual(b.get(163),0 if hp==0 else hp+new_max-old_max)
                        for field,old in zip(range(165,170),old_stats):self.assertGreater(b.get(field),old)
                        self.assertEqual(b.get(160),8);self.assertEqual(bytes(b.mu.mem_read(bm.MON,136)),before_box)
                        first=bytes(b.mu.mem_read(bm.MON,236));b.call(self.symbols['sgp_shiny_continue'],0)
                        self.assertEqual(bytes(b.mu.mem_read(bm.MON,236)),first)
                        self.assertEqual(b.assertions,0)

if __name__=='__main__':unittest.main()
