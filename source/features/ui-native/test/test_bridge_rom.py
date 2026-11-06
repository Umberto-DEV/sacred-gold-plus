"""Prepared native EN/IT Bridge/Manager/Field/NNS/FS CPU execution.
CARD and unrelated outer task/control producers are explicit seams. Authored
Scene stub actually creates/frees checked heap38; it is NOT the final app.
No ROM, save or emulator artifacts are written.
"""
import hashlib
import os
import struct
import tempfile
import unittest
from pathlib import Path
import ndspy.code
from bridge_bench import compile_bridge,compile_scene_stub,loader
import bridge_bench as bb
from test_module_rom import NativeModuleBench,ROM_PINS,PINS,FS_PINS,LOADER_PINS,NEW,RUN,DELETE
from test_heap_rom import NativeHeapBench
from heap_bench import BASE as HEAP_META,PARENT,TEMPLATES,META,CREATE,ALLOC,FREE,DESTROY,FLAGS,SOURCE,STACK,REGS,IME
from module_bench import *
from unicorn.arm_const import *
import test_physical_rom as pr
from physical_bench import bl as thumb_bl

BRIDGE_PINS=(
 (0x0203E0AC,208,'a7d366ddd3a3647571487e322e9058650a4450118b08bc240c39ee1c1a56a553'),
 (0x0203DE8C,0x290,'a9272cb0636b8e07f1ddb7b7b5dd0348edc7b750e4827ef7f598dcf0b66a4900'),
 (0x0203D33C,0x60,'c1b0c60b7c8ce8ddd043b82f9ee4631d3345abc5342fb4e6b697ba5641497b88'),
 (0x0203EE14,0x40,'b844fda8a9aab3955f0182a5754d4b8d3c40e101d44d8bec3a3f44875e9bb945'),
 (0x02028EA8,12,'e53aa60fe290a49618a1b8cffa2be5bc1be32cdf80999c6445c9aef2e7562285'),
 (0x020272C8,64,'22c36f526e2de23e382807e9e3afb967cdff6384b1a2f69a53e14282d6d3ac7c'),
 (0x0205064C,8,'e777ca5564a66a27c64283fab4fee8810b682ce2b5847607a9baab2b9bb5d4d2'),
 (0x020D3A90,24,'df0fcaa0e5aad641260041edb6a5688cb9a43de0bfeeff2bfcb54ef8c8cc54b8'))
FIELD_MAIN,OUTER_RETURN=0x0203E0CD,0x0203D369
SEAM_CONTROL,SEAM_TASK,SEAM_RELOAD=0x023C93BC,0x02050544,0x020505C0
TEST_PARENT,OUTER_TASK,OUTER_ENV=0x023E0000,0x023B9000,0x023BA000

class NativeBridgeBench(NativeModuleBench):
    observed={'max_stack':0,'max_instructions':0,'max_masked_instructions':0,'calls':0}
    def __init__(self,compiled,fixture,scene,role=1):
        self.ready=False;self.bridge=compiled[0];self.physical=compiled[1];self.scene=scene
        self.trace=[];self.forced_scene={};self.lower_fault=None;self.root_freed=False
        self.fault_after_exit=None;self.dynamic_mutation=None;self.physical_mutation=None;self.scene_return=None
        self.app_alloc_failure=False;self.destroy_failures=0;self.destroy_pending=None
        self.destroy_results=[];self.destroy_retirements=0
        super().__init__((b'',{}),fixture,0x400)
        self.code,self.symbols=self.bridge
        self.u.mem_write(bb.CODE,self.code);self.u.mem_write(bb.PHYSICAL,self.physical[0])
        self.compiled_fetch=instruction_set(self.u,[v for k,v in self.symbols.items() if not k.startswith("$")],[(bb.CODE,bb.CODE+len(self.code))])
        self.physical_fetch=instruction_set(self.u,[v for k,v in self.physical[1].items() if not k.startswith("$")],[(bb.PHYSICAL,bb.PHYSICAL+len(self.physical[0]))])
        self.native_fetch |= instruction_set(self.u,[0x020B4E4C],[(a,a+n) for a,n,_ in PINS])
        self.physical_native_fetch=instruction_set(self.u,[pr.KEYPAD|1,pr.MAPPING|1,pr.LID|1,pr.MAIN|1],
            [(a,a+n) for a,n,_ in pr.PINS])
        self.u.mem_write(0x0201A556,thumb_bl(0x0201A556,self.physical[1]['physical_after_native_mapping']))
        self.u.mem_write(pr.MAIN,thumb_bl(pr.MAIN,self.physical[1]['physical_lid_action']))
        self.extra_fetch=instruction_set(self.u,[FIELD_MAIN,0x0203E0AD,OUTER_RETURN,0x02028EA9,
            0x020272C9,0x0205064D,0x02050651,CPSR,CPSR+12],[(a,a+n) for a,n,_ in BRIDGE_PINS])
        self.allowed.extend(((pr.SYSTEM+0x38,pr.SYSTEM+0x68),(0x02111864,0x02111868)))
        self.allowed.extend(((bb.TOKEN,bb.BOOT+16),(bb.SLOT,bb.SLOT+48),
                             (0x021D4158,0x021D415C),(OUTER_ENV,OUTER_ENV+0x400)))
        h=NativeHeapBench((b'',{}),self.sections)
        for p,n in [(META,28),(HEAP_META,824),(0x021D84B0,16),(PARENT,0x100000),*TEMPLATES]:
            self.u.mem_write(p,bytes(h.u.mem_read(p,n)));self.allowed.append((p,p+n))
        raw=self.address(ALLOC,PARENT,0x1C000,4);assert raw
        assert self.address(CREATE,raw,0x1C000,0)==raw
        for p,v in ((HEAP_META+16,raw),(HEAP_META+116+16,PARENT),(HEAP_META+228+16,raw)):
            self.put(p,v)
        self.put(HEAP_META+662+11,4,1);self.heap_backing=raw
        self.field=self.address(0x0201AA8D,11,0x200)
        self.process=self.address(0x0201AA8D,11,16)
        self.save=self.address(0x0201AA8D,3,0x2330C)
        self.font=self.address(0x0201AA8D,3,124)
        for p,n in ((self.field,0x200),(self.process,16),(self.save,0x2330C),(self.font,124)):
            self.u.mem_write(p,bytes(n))
        self.put(self.field,self.process);self.put(self.field+12,self.save)
        self.put(0x021D4158,self.field);self.options=self.save+0x100
        self.put(self.save+0x2302C,0xF0)
        self.put(0x0211188C,0x02111890);self.put(0x0211192C,self.font)
        self.put(0x02111944,1,1);self.put(self.font,1);self.put(self.font+4,0x02026111)
        self.u.mem_write(0x021D110C,bytes(16));self.u.mem_write(bb.TOKEN,bytes(40+16))
        self.u.mem_write(bb.SLOT,bytes(48));self.put(0x04000130,0x3FF,2);self.put(0x027FFFA8,0x2C00,2)
        self.u.mem_write(bb.SEEDS+96,bytes(128))
        self.raw,self.dynamic_symbols=scene;self.encoded=packed_bytes(self.raw);self.metadata()
        self.allowed.append((IMAGE,IMAGE+len(self.raw)))
        self.bind_config();self.configure_seed()
        self.scene_fetch=set();self.role=role;self.new_manager(role)
        self.ready=True;self.trace.clear();self.calls.clear();self.root_freed=False
        self.initial_count=self.get(HEAP_META+340+22,2)
    def configure_seed(self):
        c=bytearray(config_bytes(self.raw,table=self.table_rom))
        struct.pack_into('<3I',c,52,*[self.dynamic_symbols[n]-IMAGE for n in
             ('test_scene_init','test_scene_main','test_scene_exit')])
        self.u.mem_write(bb.SEEDS,bytes(c))
    def new_manager(self,role):
        self.role=role;self.args=self.address(0x0201AA8D,11,12) if role==1 else 0
        if self.args:self.u.mem_write(self.args,struct.pack('<3I',0xA5962CF0,self.options,self.field+0x10C))
        init=self.symbols['ui_bridge_settings_init' if role==1 else 'ui_bridge_guide_init']
        template=0x020FA354 if role==1 else 0x023D7B10
        self.u.mem_write(template,struct.pack('<4I',init,self.symbols['ui_bridge_main'],self.symbols['ui_bridge_exit'],0xFFFFFFFF))
        self.manager=self.address(NEW,template,self.args,11);self.put(self.process+4,self.manager)
        self.u.mem_write(OUTER_TASK,bytes(32));self.put(OUTER_TASK+24,self.field);self.put(OUTER_TASK+12,OUTER_ENV)
        self.put(OUTER_ENV+0x380,self.args)
    @property
    def context(self):return self.state_address+4848
    @property
    def heap_token(self):return self.state_address+4944
    def heap_words(self):return bytes(self.u.mem_read(self.heap_token,92))
    def read(self,u,a,p,n,v,d):
        assert p in (IME,0x04000130,0x040000B8,0x040000C4,0x040000D0,0x040000DC),f'MMIO read {p:08x}'
    def store(self,u,a,p,n,v,d):
        self.writes.append((p,n,v,u.reg_read(UC_ARM_REG_PC)))
        assert any(lo<=p<p+n<=hi for lo,hi in self.allowed),f'unknown bridge/native write {p:08x}/{n}'
        pc=u.reg_read(UC_ARM_REG_PC)
        if self.ready and self.root_freed:
            assert not self.state_address<=p<p+n<=self.state_address+5036,'write retired root'
        if bb.CODE<=pc<bb.CODE+len(self.code) and REGISTRY<=p<p+n<=REGISTRY+64:
            assert u.reg_read(UC_ARM_REG_CPSR)&128,'registry transaction unmasked'
        if self.ready and pc in self.compiled_fetch and p==self.manager+28 and v:
            self.state_address=v;self.trace.append(('root',v))
    def hook(self,u,p,n,d):
        if not hasattr(self,'extra_fetch'):return super().hook(u,p,n,d)
        # NativeModuleBench's fault boundary returns into this relocated blob,
        # so acknowledge its declared temporary archive-suspend seam here.
        if self.failure_return is not None and p==self.failure_return:
            self.failure_return=None;self.put(ARC+0x1C,self.get(ARC+0x1C)&~0x80)
        if self.close_pending and p==self.close_pending[-1][0]:
            ret,file=self.close_pending.pop()
            self.closes.append((file,u.reg_read(UC_ARM_REG_R0),self.get(file+8),self.get(file+12),self.get(ARC+36)))
        args=[u.reg_read(r) for r in (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3)]
        assert STACK-3072<=u.reg_read(UC_ARM_REG_SP)<=STACK,'native/compiled stack bound'
        if p in (CREATE,ALLOC,FREE,DESTROY,DISABLE,RESTORE,CPSR,NEW&~1,RUN&~1,DELETE&~1,
                 0x0201AA8C,0x0201AACC,0x0201AB0C,0x02028EA8,0x020272C8):
            assert u.reg_read(UC_ARM_REG_SP)%8==0,f'native ABI8 {p:08x}'
        if self.destroy_pending and self.destroy_pending[0]==p:
            _,token,before,metadata,injected=self.destroy_pending;self.destroy_pending=None
            result=args[0];after=bytes(self.u.mem_read(token,92))
            self.destroy_results.append((token,result,before,after))
            if injected:
                assert result==0 and before==after,'refused destroy mutated authoritative token'
                assert bytes(self.u.mem_read(HEAP_META,824))==metadata,'refused destroy mutated native topology'
                self.put(HEAP_META+340+76,0,2)
            if result:
                assert after==bytes(92),'successful destroy did not zero all23 authority words'
                self.destroy_retirements+=1
        if self.scene_return==p:
            self.scene_return=None
            if self.fault_after_exit and args[0]==3:
                k=self.fault_after_exit
                if isinstance(k,tuple) and k[0]=='token':self.put(self.heap_token+4*k[1],1)
                elif k=='count':self.put(HEAP_META+340+76,1,2)
                elif k=='font':self.put(self.font+4,0x02026069)
                elif k=='callback':self.put(0x021D110C,IMAGE|1)
                elif k=='dma':self.put(0x040000B8,0x80000000)
        if p==pr.MAIN+8:u.reg_write(UC_ARM_REG_PC,STOP|1);return
        if p in (pr.TP_REQUEST,pr.TP_WAIT,pr.TP_AUTO,pr.TP_CALIBRATE,pr.PAUSE,pr.RESUME,
                 pr.MIC_PAUSE,pr.MIC_RESUME,pr.CART,pr.SLEEP,pr.CARD,pr.POWEROFF,pr.BACK_GET,pr.BACK_SET):
            assert u.reg_read(UC_ARM_REG_SP)%8==0
            if p in (pr.TP_WAIT,pr.TP_AUTO):self.u.mem_write(args[0],bytes(8))
            if p==pr.TP_CALIBRATE:self.u.mem_write(args[0],bytes(self.u.mem_read(args[1],8)))
            if p==pr.BACK_GET:self.put(args[0],1);self.put(args[1],1)
            if p==pr.SLEEP:
                assert self.get(bb.SLOT+16)>0 and self.get(bb.SLOT+28)&8
                self.put(0x027FFFA8,0x2C00,2);self.trace.append(('suspend',))
            assert p!=pr.POWEROFF,'unexpected poweroff'
            self.ret(0);return
        if p in (SEAM_CONTROL,SEAM_TASK):self.ret(0);return
        if p==SEAM_RELOAD:
            assert not self.get(self.process+4) and not self.get(bb.TOKEN+12)
            self.trace.append(('field_reload',));self.ret(0);return
        if p==UNLOAD and args[0]==1:
            assert not self.get(self.process);self.trace.append(('parent_unloaded',));self.ret(1);return
        if p==TEST_PARENT:
            self.put(self.field+4,0);self.trace.append(('parent_exit',));self.ret(1);return
        if self.ready and p==ALLOC and self.app_alloc_failure and self.state_address and args[0]==self.get(self.heap_token+16):
            self.trace.append(('app_alloc_failure',));self.ret(0);return
        if self.ready and p==ALLOC and self.lower_fault is not None:
            self.trace.append(('fault_alloc',));self.ret(self.lower_fault);return
        if self.ready and p==FREE:
            self.trace.append(('nns_free',args[1]))
            if args[1]==self.state_address-16:
                assert self.phase==RETIRED and self.get(self.context+28)==0
                self.root_freed=True
        if self.ready and p==0x0201AB0C:
            self.trace.append(('gf_free',args[0]))
            if args[0]==getattr(self,'manager',0):
                assert self.get(self.manager+28)==0 and self.get(bb.TOKEN+12)==0,'manager deleted before checked root retirement'
            assert args[0]!=self.state_address,'generic root free forbidden'
        if self.ready and p==DESTROY and args[0]==self.get(self.heap_token+16):
            self.trace.append(('nns_destroy_scene',args[0]))
        if self.ready and p==END:
            assert self.heap_words()==bytes(92),'module release before authoritative token retirement'
            assert self.get(self.context+28)==0 and self.get(self.context+32)==0
            assert self.get(HEAP_META+662+38,1)==28 and self.get(HEAP_META+340+76,2)==0,'module release before heap38 retirement'
            self.trace.append(('module_end',))
        if IMAGE<=p<IMAGE+len(self.raw):
            if p==self.dynamic_symbols['ui_heap38_destroy']&~1:
                assert args[0]==self.heap_token,'heap authority copied out of resident root'
                injected=bool(self.destroy_failures)
                if injected:
                    assert not self.get(self.context+28),'destroy barrier injected before actual app free'
                    self.destroy_failures-=1;self.put(HEAP_META+340+76,1,2)
                    self.trace.append(('destroy_refusal_after_free',self.heap_token))
                self.destroy_pending=(u.reg_read(UC_ARM_REG_LR)&~1,args[0],self.heap_words(),
                                      bytes(self.u.mem_read(HEAP_META,824)),injected)
            assert self.phase==ACTIVE and not self.root_freed,'dynamic fetch after module retirement'
            if not self.scene_fetch:self.scene_fetch=instruction_set(self.u,[v for k,v in self.dynamic_symbols.items() if not k.startswith("$")],[(IMAGE,IMAGE+len(self.raw))])
            assert p in self.scene_fetch,'dynamic literal/data fetch'
            if p in (v&~1 for v in self.dynamic_symbols.values()):
                assert u.reg_read(UC_ARM_REG_SP)%8==0,'dynamic ABI8'
            for selector,name in enumerate(('test_scene_init','test_scene_main','test_scene_exit')):
                if p==self.dynamic_symbols[name]&~1:
                    assert args[:2]==[self.context,self.state_address+4916]
                    assert bb.CODE<=u.reg_read(UC_ARM_REG_LR)&~1<bb.CODE+len(self.code),'dynamic return stack not resident'
                    token=self.get(self.context+32)
                    if selector==0:assert token==0,'activation before InitREADY'
                    if selector==1:assert token and self.get(bb.SLOT)==self.context
                    if selector==2:assert token==0 and self.get(bb.SLOT)==0,'cleanup before physical retirement'
                    self.trace.append(('scene',selector))
                    if selector==2:self.scene_return=u.reg_read(UC_ARM_REG_LR)&~1
                    if self.dynamic_mutation:self.dynamic_mutation(self,selector)
                    if selector in self.forced_scene:self.ret(self.forced_scene[selector]);return
            self.measure_irq();self.instructions+=1;self.visited.add(p);self.low=min(self.low,u.reg_read(UC_ARM_REG_SP));return
        if p in self.extra_fetch or p in self.compiled_fetch or p in self.physical_fetch or p in self.physical_native_fetch:
            if p in self.physical_fetch:
                if p==self.physical[1]['physical_activate']&~1:self.trace.append(('activate',args[0]))
                if p==self.physical[1]['physical_deactivate']&~1:
                    self.trace.append(('deactivate',args[0]))
                    if self.physical_mutation:self.physical_mutation(self)
            self.measure_irq();self.instructions+=1;self.visited.add(p);self.low=min(self.low,u.reg_read(UC_ARM_REG_SP));return
        return super().hook(u,p,n,d)
    def address(self,p,*args):
        seeds=[0x44440000+i for i in range(8)]
        for r,v in zip(REGS,seeds):self.u.reg_write(r,v)
        for i,r in enumerate((UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3)):
            self.u.reg_write(r,args[i] if i<len(args) else 0)
        self.u.reg_write(UC_ARM_REG_SP,STACK);self.u.reg_write(UC_ARM_REG_LR,STOP|1)
        cpsr=self.u.reg_read(UC_ARM_REG_CPSR)&0xDF;ime=self.get(IME);start=self.instructions;self.low=STACK
        self.u.mem_write(STACK-3072,b'\xA5'*64)
        self.u.emu_start(p,STOP,count=3000000)
        assert self.u.reg_read(UC_ARM_REG_PC)==STOP,f'finite return {self.u.reg_read(UC_ARM_REG_PC):08x}'
        assert self.u.reg_read(UC_ARM_REG_SP)==STACK and [self.u.reg_read(r) for r in REGS]==seeds,'ABI preservation'
        assert self.u.reg_read(UC_ARM_REG_CPSR)&0xDF==cpsr and self.get(IME)==ime,'CPSR/IME preservation'
        assert bytes(self.u.mem_read(STACK-3072,64))==b'\xA5'*64,'stack canary'
        self.metrics.append((hex(p),STACK-self.low,self.instructions-start))
        self.observed['max_stack']=max(self.observed['max_stack'],STACK-self.low)
        self.observed['max_instructions']=max(self.observed['max_instructions'],self.instructions-start)
        self.observed['max_masked_instructions']=max(self.observed['max_masked_instructions'],self.max_mask_run)
        self.observed['calls']+=1
        return self.u.reg_read(UC_ARM_REG_R0)
    def frame(self):return self.address(FIELD_MAIN,self.field)
    def drive(self,predicate,limit=180):
        for _ in range(limit):
            if predicate():return
            self.frame()
        raise AssertionError(f'no lifecycle progress boot={self.get(bb.BOOT+12)} module={self.phase}')
    def poison_stack(self):self.u.mem_write(STACK-3000,b'\xA5'*3000)

class BridgeRomTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixtures={}
        canonical=SOURCE.parent/'local/experiments/balance493-2026-10-28'
        for lang,pin in ROM_PINS.items():
            path=Path(os.environ.get('SGP_UI_BRIDGE_'+lang,str(canonical/f'candidate-v4-{lang}.nds')))
            if not path.is_file():
                if os.environ.get('SGP_UI_BRIDGE_REQUIRE_INPUTS')=='1':raise AssertionError('missing '+lang)
                raise unittest.SkipTest('missing canonical '+lang)
            sha=hashlib.sha256()
            with path.open('rb') as stream:
                for block in iter(lambda:stream.read(1<<20),b''):sha.update(block)
                assert (path.stat().st_size,sha.hexdigest())==pin
                stream.seek(0);header=stream.read(512)
                offset,entry,ram,length=struct.unpack_from('<4I',header,32)
                stream.seek(offset);sections=ndspy.code.MainCodeFile(stream.read(length),ram,struct.unpack_from('<I',header,112)[0]).sections
                fnt,fn,fat,fa=struct.unpack_from('<4I',header,64);y9,yn=struct.unpack_from('<2I',header,80)
                stream.seek(fat);fatdata=stream.read(fa);stream.seek(fnt);fntdata=stream.read(fn)
                stream.seek(y9);table=stream.read(yn)
            for p,n,want in (*PINS,*FS_PINS,*LOADER_PINS,*BRIDGE_PINS,*pr.PINS):
                section=next(s for s in sections if s.ramAddress<=p<p+n<=s.ramAddress+len(s.data))
                assert hashlib.sha256(section.data[p-section.ramAddress:p-section.ramAddress+n]).hexdigest()==want,(lang,hex(p))
            cls.fixtures[lang]=([(s.ramAddress,bytes(s.data)) for s in sections if 0x02000000<=s.ramAddress<0x02400000],fatdata,fntdata,table)
        cls.temp=tempfile.TemporaryDirectory(prefix='bridge-b-');cls.addClassCleanup(cls.temp.cleanup)
        cls.compiled=compile_bridge(Path(cls.temp.name));cls.scene=compile_scene_stub(Path(cls.temp.name))
    def bench(self,lang='EN',role=1):return NativeBridgeBench(self.compiled,self.fixtures[lang],self.scene,role)
    def test_native_both_roles_checked_heap_and_outer_args_retire_once(self):
        for lang in self.fixtures:
            for role in (1,2):
                b=self.bench(lang,role);args=b.args
                seeds=bytes(b.u.mem_read(bb.SEEDS,224));save_before=bytes(b.u.mem_read(b.save,0x2330C))
                original=bytes(b.u.mem_read(args,12)) if args else None
                b.drive(lambda:not b.get(b.process+4))
                self.assertEqual(b.get(bb.BOOT),0);self.assertEqual(b.get(bb.BOOT+4),1)
                self.assertEqual(b.get(bb.TOKEN+12),0)
                self.assertEqual(sum(e==('nns_free',b.state_address-16) for e in b.trace),1)
                self.assertEqual(sum(e==('gf_free',b.manager) for e in b.trace),1)
                self.assertEqual(sum(e==('gf_free',args) for e in b.trace),0)
                if args:
                    self.assertEqual(bytes(b.u.mem_read(args,12)),original)
                    b.address(OUTER_RETURN,OUTER_TASK)
                    self.assertEqual(sum(e==('gf_free',args) for e in b.trace),1)
                    self.assertIn(('field_reload',),b.trace)
                events=[e[0] for e in b.trace]
                self.assertLess(events.index('activate'),events.index('deactivate'))
                self.assertLess(events.index('deactivate'),events.index('module_end'))
                self.assertTrue(b.root_freed)
                self.assertEqual(bytes(b.u.mem_read(bb.SEEDS,224)),seeds)
                self.assertEqual(bytes(b.u.mem_read(b.save,0x2330C)),save_before)
                self.assertEqual(b.address(b.symbols['ui_bridge_exit'],b.manager,b.manager+20),0)
                b.u.mem_write(IMAGE,b'\xFE'*len(b.raw))
                self.assertEqual(b.address(self.symbols_value(b,'ui_module_check'),b.state_address,role,1,0),0)
    def test_native_heap_authority_is_resident_before_ready(self):
        for lang in self.fixtures:
            b=self.bench(lang);b.drive(lambda:bool(b.get(b.context+28)))
            self.assertEqual(b.get(b.context+52),b.state_address+4944,
                             'actual native heap38 authority must survive app free and SYS return')
            self.assertEqual(b.get(b.state_address+4944),0x55483831)

    def test_native_app_free_destroy_refusal_survives_sys_return_more_and_success(self):
        # Removing the resident authority, retaining app after free or treating
        # MORE as EXITED breaks independent native ownership/free observations.
        for lang in self.fixtures:
            for role in (1,2):
                b=self.bench(lang,role);b.drive(lambda:b.get(b.manager+16)==2)
                token=b.get(b.context+52);app=b.get(b.context+28)
                self.assertEqual(token,b.heap_token)
                self.assertEqual(b.get(HEAP_META+340+76,2),16)
                self.assertEqual(sum(bool(b.get(token+28+4*i)) for i in range(16)),16)
                b.drive(lambda:b.get(b.manager+16)==3);b.destroy_failures=3
                b.drive(lambda:len(b.destroy_results)==1)
                held=b.heap_words();self.assertEqual(b.get(b.context+28),0)
                self.assertEqual(sum(e==('nns_free',app-16) for e in b.trace),1)
                self.assertEqual(held[28:],bytes(64),'every acquired root must retire before destroy')
                self.assertEqual(b.get(HEAP_META+340+76,2),0)
                for expected in (2,3):
                    b.poison_stack();b.frame()
                    self.assertEqual(len(b.destroy_results),expected)
                    self.assertEqual(b.heap_words(),held)
                    self.assertEqual(b.get(b.context+52),token)
                    self.assertEqual(b.get(b.manager+28),b.state_address)
                    self.assertEqual(b.get(b.process+4),b.manager)
                    self.assertEqual(b.phase,ACTIVE);self.assertFalse(b.root_freed)
                    self.assertFalse(any(e[0] in ('module_end','nns_destroy_scene') for e in b.trace))
                b.poison_stack();b.drive(lambda:not b.get(b.process+4))
                self.assertEqual([v[1] for v in b.destroy_results],[0,0,0,1])
                self.assertTrue(all(v[0]==token for v in b.destroy_results))
                self.assertEqual(b.destroy_retirements,1)
                self.assertEqual(sum(e[0]=='nns_destroy_scene' for e in b.trace),1)
                self.assertEqual(sum(e==('nns_free',app-16) for e in b.trace),1)
                self.assertTrue(b.root_freed)

    def test_native_post_free_terminal_hold_retains_same_token_module_and_child(self):
        for lang in self.fixtures:
            b=self.bench(lang);b.drive(lambda:b.get(b.manager+16)==3)
            app=b.get(b.context+28);b.put(b.context+44,1);b.destroy_failures=1
            b.drive(lambda:b.get(bb.BOOT+12)==3)
            held=b.heap_words();trace=list(b.trace)
            self.assertEqual(b.get(b.context+28),0)
            self.assertEqual(sum(e==('nns_free',app-16) for e in trace),1)
            self.assertEqual([v[1] for v in b.destroy_results],[0])
            for _ in range(3):
                b.poison_stack();b.frame()
                self.assertEqual(b.heap_words(),held);self.assertEqual(b.trace,trace)
                self.assertEqual(b.get(b.context+52),b.heap_token)
                self.assertEqual(b.get(b.manager+28),b.state_address)
                self.assertEqual(b.get(b.process+4),b.manager);self.assertEqual(b.phase,ACTIVE)
            self.assertFalse(b.root_freed);self.assertEqual(b.destroy_retirements,0)

    def test_native_app_alloc_failure_after_create_destroys_resident_authority(self):
        for lang in self.fixtures:
            for role in (1,2):
                b=self.bench(lang,role);b.app_alloc_failure=True
                b.drive(lambda:not b.get(b.process+4))
                self.assertIn(('app_alloc_failure',),b.trace)
                self.assertFalse(any(e[0]=='activate' for e in b.trace))
                self.assertEqual([v[1] for v in b.destroy_results],[1])
                self.assertEqual(b.destroy_results[0][0],b.heap_token)
                self.assertEqual(b.destroy_retirements,1);self.assertTrue(b.root_freed)

    def test_native_ready_requires_full_heap_authority_and_actual_app_ledger(self):
        faults=('magic','generation','parent','raw','handle','backing','index','ledger','count',
                'native_index','native_handle','native_parent','native_raw')
        for lang in self.fixtures:
            for fault in faults:
                with self.subTest(lang=lang,fault=fault):
                    b=self.bench(lang);b.drive(lambda:bool(b.get(b.context+28)))
                    token=b.heap_token;slot=b.get(token+24)
                    if fault=='count':b.put(HEAP_META+340+76,15,2)
                    elif fault=='native_index':b.put(HEAP_META+662+38,28,1)
                    elif fault.startswith('native_'):
                        base={'native_handle':0,'native_parent':116,'native_raw':228}[fault]
                        address=HEAP_META+base+4*slot;b.put(address,b.get(address)+4)
                    else:
                        offset={'magic':0,'generation':4,'parent':8,'raw':12,'handle':16,
                                'backing':20,'index':24,'ledger':28}[fault]
                        b.put(token+offset,0 if fault=='ledger' else b.get(token+offset)^4)
                    before=b.heap_words();native=bytes(b.u.mem_read(HEAP_META,824));app=b.get(b.context+28)
                    b.frame();self.assertEqual(b.get(bb.BOOT+12),3)
                    self.assertEqual(b.heap_words(),before);self.assertEqual(bytes(b.u.mem_read(HEAP_META,824)),native)
                    self.assertFalse(any(e[0]=='activate' for e in b.trace))
                    self.assertEqual(b.get(b.context+28),app);self.assertFalse(b.root_freed)

    def test_native_other_approved_backing_is_rejected_for_each_scene_role(self):
        with tempfile.TemporaryDirectory(prefix='bridge-role-backing-') as temp:
            scene=compile_scene_stub(Path(temp),wrong_backing=True)
            for lang in self.fixtures:
                for role in (1,2):
                    b=NativeBridgeBench(self.compiled,self.fixtures[lang],scene,role)
                    b.drive(lambda:bool(b.get(b.context+28)))
                    self.assertEqual(b.get(b.heap_token+20),0x40000 if role==1 else 0x30000)
                    token=b.heap_words();b.frame()
                    self.assertEqual(b.get(bb.BOOT+12),3);self.assertEqual(b.heap_words(),token)
                    self.assertFalse(any(e[0]=='activate' for e in b.trace));self.assertFalse(b.root_freed)

    def test_native_foreign_misaligned_stale_context_refuses_before_dynamic_calls(self):
        for lang in self.fixtures:
            for phase in ('init','main','exit'):
                for fault in ('foreign','misaligned','usc1'):
                    with self.subTest(lang=lang,phase=phase,fault=fault):
                        b=self.bench(lang)
                        b.drive(lambda:bool(b.get(b.context+28)))
                        if phase!='init':b.drive(lambda:b.get(b.manager+16)==(2 if phase=='main' else 3))
                        foreign=b.address(0x0201AA8D,11,92);b.u.mem_write(foreign,b'\x6B'*92)
                        b.put(b.context if fault=='usc1' else b.context+52,
                              0x31435355 if fault=='usc1' else foreign if fault=='foreign' else b.heap_token+1)
                        trace=list(b.trace);token=b.heap_words();b.frame()
                        self.assertEqual(b.get(bb.BOOT+12),3)
                        self.assertEqual(b.trace,trace);self.assertEqual(b.heap_words(),token)
                        self.assertEqual(bytes(b.u.mem_read(foreign,92)),b'\x6B'*92)
                        self.assertFalse(b.root_freed)

    def test_native_heap_pointer_mutation_on_dynamic_return_is_terminal_hold(self):
        for selector in (0,1,2):
            b=self.bench();b.drive(lambda:bool(b.get(b.context+28)))
            if selector:b.drive(lambda:b.get(b.manager+16)==(2 if selector==1 else 3))
            token=b.heap_words();b.forced_scene[selector]=0
            b.dynamic_mutation=lambda x,s:x.put(x.context+52,x.heap_token+4) if s==selector else None
            b.frame();self.assertEqual(b.get(bb.BOOT+12),3)
            self.assertEqual(b.heap_words(),token);self.assertFalse(b.root_freed)
            trace=list(b.trace);b.poison_stack();b.frame();self.assertEqual(b.trace,trace)

    def test_native_exited_needs_zero_token_and_inactive_native_heap_together(self):
        for lang in self.fixtures:
            # A forged zero token cannot make a live native heap retire.
            b=self.bench(lang);b.drive(lambda:b.get(b.manager+16)==3)
            native=bytes(b.u.mem_read(HEAP_META,824));b.u.mem_write(b.heap_token,bytes(92))
            b.put(b.context+28,0);b.forced_scene[2]=3;b.frame()
            self.assertEqual(b.get(bb.BOOT+12),3);self.assertEqual(bytes(b.u.mem_read(HEAP_META,824)),native)
            self.assertFalse(b.root_freed);self.assertFalse(any(e[0]=='module_end' for e in b.trace))
            # Every one of the23 authority words is independently required zero.
            for word in range(23):
                b=self.bench(lang);b.drive(lambda:b.get(b.manager+16)==3);b.frame()
                b.fault_after_exit=('token',word);b.drive(lambda:b.get(bb.BOOT+12)==3)
                self.assertEqual(b.get(b.heap_token+4*word),1)
                self.assertEqual(b.get(HEAP_META+662+38,1),28)
                self.assertEqual(b.get(HEAP_META+340+76,2),0)
                self.assertFalse(b.root_freed);self.assertFalse(any(e[0]=='module_end' for e in b.trace))

    def test_native_delayed_reads_close_and_cancel_keep_real_manager_root(self):
        for lang in self.fixtures:
            b=self.bench(lang);b.delay=True;b.drive(lambda:b.phase==META_WAIT)
            root=b.state_address;count=b.get(HEAP_META+340+22,2)
            for _ in range(3):
                b.poison_stack();self.assertEqual(b.frame(),0)
                self.assertEqual(b.get(b.manager+28),root);self.assertEqual(b.get(ARC+36),b.file)
                self.assertEqual(b.get(HEAP_META+340+22,2),count)
            self.assertEqual(b.address(b.symbols['ui_module_cancel'],root,1,1),MORE)
            for _ in range(3):b.poison_stack();self.assertEqual(b.frame(),0)
            b.complete();b.delay=False;b.close_failures=3
            b.drive(lambda:not b.get(b.process+4))
            self.assertFalse(any(e[0]=='scene' for e in b.trace));self.assertTrue(b.root_freed)
            b=self.bench(lang);b.delay=True;b.drive(lambda:b.phase==META_WAIT)
            # The pump may cross transient CLOSE phases inside one field
            # callback. Stop on the delayed image read, then observe the three
            # failed close effects themselves instead of requiring
            # IMAGE_CLOSE to be scheduler-visible between callbacks.
            b.complete();b.drive(lambda:b.phase==IMAGE_WAIT)
            b.complete();b.delay=False;b.close_failures=3
            before=sum(c[1]==0 for c in b.closes)
            b.drive(lambda:sum(c[1]==0 for c in b.closes)>=before+3)
            self.assertEqual(b.get(b.file+8),ARC)
            self.assertFalse(any(e[0]=='scene' for e in b.trace))
            b.drive(lambda:not b.get(b.process+4));self.assertTrue(b.root_freed)
    def test_native_changed_null_and_delayed_holds_block_outer_teardown(self):
        for lang in self.fixtures:
            for result in (0,0xFFFFFFFF):
                b=self.bench(lang);b.put(b.process+12,1);b.lower_fault=result
                before=bytes(b.u.mem_read(bb.TOKEN,40));b.frame()
                if result==0:
                    self.assertEqual(bytes(b.u.mem_read(bb.TOKEN,40)),before)
                    b.drive(lambda:not b.get(b.process+4));self.assertEqual(b.frame(),1)
                else:
                    held=bytes(b.u.mem_read(bb.TOKEN,40));self.assertNotEqual(held,before)
                    for _ in range(4):
                        b.poison_stack();self.assertEqual(b.frame(),0)
                        self.assertEqual(b.get(b.process+4),b.manager)
                        self.assertEqual(bytes(b.u.mem_read(bb.TOKEN,40)),held)
                    self.assertFalse(any(e[0] in ('nns_free','gf_free') for e in b.trace))
            b=self.bench(lang);b.delay=True;b.drive(lambda:b.phase==META_WAIT)
            b.complete();b.drive(lambda:b.phase==IMAGE_WAIT)
            b.complete();b.delay=False;b.close_failures=0xFFFFFFFF
            b.drive(lambda:sum(c[1]==0 for c in b.closes)>=4)
            for _ in range(4):b.poison_stack();self.assertEqual(b.frame(),0)
            self.assertEqual(b.get(b.manager+28),b.state_address);self.assertEqual(b.get(b.file+8),ARC)
            b.put(ARC+0x48,b.get(ARC+0x48)+4);b.frame()
            self.assertEqual(b.get(bb.BOOT+12),3)
            self.assertFalse(b.root_freed)
    def test_native_parent_finishes_before_child_and_recycled_manager_gets_new_lifetime(self):
        b=self.bench();parent=b.address(NEW,0x020FA354,0,11)
        b.put(parent+16,3);b.put(parent+8,TEST_PARENT|1);b.put(b.process,parent)
        b.put(b.field+4,0x1234);b.frame()
        self.assertEqual(b.trace[:3],[('parent_exit',),('gf_free',parent),('nns_free',parent-16)])
        self.assertIn(('parent_unloaded',),b.trace);self.assertFalse(any(e[0]=='root' for e in b.trace))
        b.drive(lambda:not b.get(b.process+4));old_manager=b.manager
        b.address(OUTER_RETURN,OUTER_TASK);b.root_freed=False;b.new_manager(1)
        self.assertEqual(b.manager,old_manager)
        b.drive(lambda:b.get(b.manager+16)==2)
        self.assertEqual(b.get(bb.BOOT+4),2);self.assertEqual(b.get(b.context+8),2)
        self.assertEqual(b.get(b.manager+20),0,'native proc reset is independent of scene state')
        b.drive(lambda:not b.get(b.process+4))
    def test_native_physical_pair_uses_exact_context_owner_and_closes_token(self):
        for lang in self.fixtures:
            b=self.bench(lang);b.drive(lambda:b.get(b.manager+16)==2)
            owner=b.context;token=b.get(owner+32);out=b.address(0x0201AA8D,11,16)
            b.put(pr.SYSTEM+0x54,4);b.put(pr.SYSTEM+0x58,8);b.put(pr.SYSTEM+0x68,1,1)
            b.address(pr.MAIN|1)
            self.assertEqual(b.address(b.physical[1]['physical_consume'],owner,token,out),1)
            self.assertEqual(b.get(out+14,2),1)
            b.put(0x04000130,0x3FE,2);b.address(pr.MAIN|1)
            self.assertEqual(b.address(b.physical[1]['physical_consume'],owner,token,out),1)
            self.assertEqual(b.get(out+10,2),1)
            b.put(0x027FFFA8,0xAC00,2);b.address(pr.MAIN|1)
            self.assertEqual(b.address(b.physical[1]['physical_consume'],owner,token,out),2)
            self.assertEqual(b.address(b.physical[1]['physical_ack_suspend'],owner,token,b.get(out+4)),1)
            b.drive(lambda:not b.get(b.process+4))
            self.assertEqual(b.address(b.physical[1]['physical_consume'],owner,token,out),3)
            b.address(0x0201AB0D,out)
    def test_actual_native_exhaustion_is_clean_null_without_token_change(self):
        b=self.bench();blocks=[]
        for size in (0x3000,0x1000):
            for _ in range(40):
                raw=b.address(ALLOC,b.heap_backing,size,4)
                if not raw:break
                blocks.append(raw)
            else:self.fail('unbounded exhaustion setup')
        before=bytes(b.u.mem_read(bb.TOKEN,40));b.drive(lambda:not b.get(b.process+4))
        self.assertEqual(bytes(b.u.mem_read(bb.TOKEN,40)),before)
        self.assertEqual(b.get(bb.BOOT+4),1)
        self.assertFalse(any(e[0] in ('root','scene','activate') for e in b.trace))
        for raw in reversed(blocks):b.address(FREE,b.heap_backing,raw)
    def test_native_release_identity_loss_holds_after_scene_retirement(self):
        b=self.bench();b.drive(lambda:b.get(b.state_address+4912)==5)
        self.assertEqual(b.get(b.context+28),0);self.assertEqual(b.get(b.context+32),0)
        b.put(REGISTRY+4,0)
        b.frame();self.assertEqual(b.get(bb.BOOT+12),3)
        for _ in range(3):b.poison_stack();self.assertEqual(b.frame(),0)
        self.assertEqual(b.get(b.manager+28),b.state_address);self.assertFalse(b.root_freed)

    def test_native_clean_load_failure_returns_without_dynamic_entry(self):
        for lang in self.fixtures:
            b=self.bench(lang);b.partial=True;b.drive(lambda:not b.get(b.process+4))
            self.assertFalse(any(e[0]=='scene' for e in b.trace))
            self.assertTrue(b.root_freed);self.assertEqual(b.get(REGISTRY+4),0)
            self.assertEqual(b.get(bb.TOKEN+12),0)
    def test_native_stale_child_role_and_module_identity_never_dispatch_or_free(self):
        for fault in ('child','role','module_config'):
            b=self.bench();b.drive(lambda:b.get(b.manager+16)==2)
            before=list(b.trace);root=b.state_address
            if fault=='child':b.put(b.process+4,b.manager+4)
            elif fault=='role':b.put(bb.BOOT+8,2)
            else:b.put(root+4624+48,b.get(root+4624+48)^1)
            # Invoke the saved resident callback directly to test stale caller
            # refusal without asking native Run to dereference a forged child.
            for _ in range(3):
                self.assertEqual(b.address(b.symbols['ui_bridge_main'],b.manager,b.manager+20),0)
            self.assertEqual(b.trace,before);self.assertFalse(b.root_freed)
            self.assertEqual(b.get(b.manager+28),root)

    def test_native_ready_without_checked_app_never_activates_physical(self):
        b=self.bench();b.forced_scene[0]=1
        b.drive(lambda:b.get(b.manager+16)==2 or b.get(bb.BOOT+12)==3)
        self.assertFalse(any(e[0]=='activate' for e in b.trace),'READY alone is not app ownership')
        self.assertEqual(b.get(bb.BOOT+12),3)

    def test_native_ready_rejects_stale_or_foreign_app_prefix(self):
        for fault in ('generation','options','magic','alias'):
            b=self.bench();b.drive(lambda:bool(b.get(b.context+28)))
            app=b.get(b.context+28)
            if fault=='alias':b.put(b.context+28,b.state_address)
            else:
                offset={'generation':40,'options':36,'magic':44}[fault]
                b.put(app+offset,b.get(app+offset)^4)
            b.frame()
            self.assertEqual(b.get(bb.BOOT+12),3)
            self.assertFalse(any(e[0]=='activate' for e in b.trace))
            self.assertFalse(b.root_freed)

    def test_native_scene_hold_and_physical_deactivation_failure_keep_app_alive(self):
        for kind in ('init','main','exit','deactivate','forged_token'):
            b=self.bench()
            if kind=='init':b.forced_scene[0]=4
            else:b.drive(lambda:b.get(b.manager+16)==2)
            if kind=='main':b.forced_scene[1]=4
            if kind=='exit':b.forced_scene[2]=4
            if kind=='deactivate':b.physical_mutation=lambda x:x.put(bb.SLOT+4,x.get(bb.SLOT+4)+1)
            if kind=='forged_token':b.dynamic_mutation=lambda x,s:x.put(x.context+32,99)
            b.drive(lambda:b.get(bb.BOOT+12)==3)
            for _ in range(3):b.poison_stack();self.assertEqual(b.frame(),0)
            self.assertFalse(b.root_freed);self.assertEqual(b.get(b.process+4),b.manager)
            self.assertFalse(any(e[0]=='module_end' for e in b.trace))
    def test_native_exit_cannot_bypass_observable_retirement(self):
        for kind in ('app','count','font','callback','dma'):
            b=self.bench();b.drive(lambda:b.get(b.manager+16)==3)
            # Declared false-EXITED seam: production must independently reject
            # the observable still-owned native state before module release.
            b.forced_scene[2]=3
            if kind!='app':
                # Run the authored cleanup first, then corrupt the boundary on
                # the next call by holding one native retirement fact live.
                del b.forced_scene[2]
                b.frame()
                # Inject only after actual dynamic cleanup returns to resident code.
                b.fault_after_exit=kind
            b.drive(lambda:b.get(bb.BOOT+12)==3)
            self.assertFalse(b.root_freed);self.assertFalse(any(e[0]=='module_end' for e in b.trace))

    def test_effect_omission_mutants_fail_native_lifetime_guards(self):
        baseline=self.bench();baseline.drive(lambda:not baseline.get(baseline.process+4))
        self.assertTrue(baseline.root_freed);self.assertEqual(baseline.destroy_retirements,1)
        self.assertEqual(sum(e[0]=='module_end' for e in baseline.trace),1)
        mutants=[
          (('if(c->physical_token) {','if(0) {'),'cleanup before physical retirement',None),
          (('b->stage=B_RELEASE;return 0;','b->stage=B_RELEASE;return 1;'),
           'manager deleted before checked root retirement',None),
          (('m->data=0;','/* omitted data retirement */'),
           'manager deleted before checked root retirement',None),
          (('ui_persistent_free(BT,BC->generation)!=UI_PERSISTENT_RELEASED','0'),
           'manager deleted before checked root retirement',None),
          (('for(unsigned i=0;i<23;++i)if(((const unsigned *)&b->scene_heap)[i])return 0;',
            '/* omitted authoritative token retirement */'),
           'module release before authoritative token retirement', ('token',22)),
          ((' HINFO->counts[38]||!bfont(b,0)',' 0||!bfont(b,0)'),
           'module release before heap38 retirement', 'count'),
        ]
        for mutation,reason,fault in mutants:
            with self.subTest(mutation=mutation[0]),tempfile.TemporaryDirectory(prefix='bridge-mutant-') as temp:
                compiled=compile_bridge(Path(temp),mutation=mutation)
                b=NativeBridgeBench(compiled,self.fixtures['EN'],self.scene)
                b.fault_after_exit=fault
                with self.assertRaisesRegex(AssertionError,reason):
                    b.drive(lambda:not b.get(b.process+4))

    @classmethod
    def tearDownClass(cls):
        if os.environ.get('SGP_UI_BRIDGE_METRICS'):
            import json
            Path(os.environ['SGP_UI_BRIDGE_METRICS']).write_text(json.dumps(NativeBridgeBench.observed,indent=2)+'\n')

    @staticmethod
    def symbols_value(b,name):return b.symbols[name]

if __name__=='__main__':unittest.main()
