"""Common Scene composition. Test pins are explicit, never production defaults."""
import hashlib
import json
import os
import importlib.util
import subprocess
import sys
from pathlib import Path
from scene_admission_bench import AdmissionBench, REASON
from heap_bench import *
from bg_bench import object_details

SCENE_MORE,SCENE_READY,SCENE_CLOSE,SCENE_EXITED,SCENE_HOLD=range(5)
STEP=REASON-4
CONSUME,ACK=0x023DF001,0x023DF005

def compile_scene(directory,scaffold=False,work_calls=4):
    directory=Path(directory)
    units=['ui-native/heap.c','ui-native/resource.c','ui-native/guide_resource.c',
           'ui-native/font.c','ui-native/bg.c','settings-ui/state.c','settings-ui/owners.c',
           'settings-ui/render.c','settings-ui/painter.c','guide-ui/controller.c',
           'guide-ui/render.c','guide-ui/painter.c','ui-native/scene_admission.c']
    text='\n'.join('#include "'+str(SOURCE/'features'/p)+'"' for p in units)+'\n'
    if scaffold:
        text+='''UiSceneResult ui_scene_init(UiSceneContext *c,unsigned *s){(void)c;(void)s;return UI_SCENE_CLOSE;}
UiSceneResult ui_scene_main(UiSceneContext *c,unsigned *s){(void)c;(void)s;return UI_SCENE_CLOSE;}
UiSceneResult ui_scene_exit(UiSceneContext *c,unsigned *s){(void)c;(void)s;return UI_SCENE_EXITED;}
'''
    else:
        for p in ('settings-ui/scene.c','ui-native/scene.c'):
            text+='#include "'+str(SOURCE/'features'/p)+'"\n'
    source=directory/'scene_unit.c';obj=directory/'scene.o';source.write_text(text)
    defines=[f'UI_SCENE_WORK_CALLS={work_calls}','UI_SCENE_GLYPH_BUDGET=8','UI_SCENE_LAST_START_LINE=240',
             f'SGP_UI_SCENE_PHYSICAL_CONSUME={CONSUME}',f'SGP_UI_SCENE_PHYSICAL_ACK={ACK}']
    cp=subprocess.run(['clang',*FLAGS,'-fno-jump-tables','-fstack-usage','-std=c11',
                       *['-D'+v for v in defines],'-MMD','-MF',str(directory/'scene.d'),'-c',str(source),'-o',str(obj)],capture_output=True,text=True)
    if cp.returncode:raise AssertionError(cp.stderr)
    spec=importlib.util.spec_from_file_location('scene_loader',SOURCE/'features/options/tools/carica_text.py')
    loader=importlib.util.module_from_spec(spec);spec.loader.exec_module(loader)
    compiled=loader.load_text(obj.read_bytes(),CODE)
    receipt=object_details(obj.read_bytes(),compiled[0])
    receipt['stack_usage']=(directory/'scene.su').read_text().replace(str(directory),'TEMP')
    receipt['defines']=defines
    receipt['payload_sha256']=hashlib.sha256(compiled[0]).hexdigest()
    receipt['exports']={n:{'address':compiled[1][n],'offset':compiled[1][n]-CODE} for n in ('ui_scene_init','ui_scene_main','ui_scene_exit','settings_final_check')}
    deps=(directory/'scene.d').read_text().replace('\\\n','').split()[1:]
    receipt['source_sha256']={str(Path(p).relative_to(SOURCE.parent)):hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in deps if Path(p)!=source}
    receipt['translation_unit_sha256']=hashlib.sha256(text.encode()).hexdigest()
    owned=('ui-native/scene.h','ui-native/scene.c','settings-ui/scene.c','ui-native/test/scene_bench.py','ui-native/test/test_scene.py','ui-native/test/test_scene_rom.py')
    receipt['owned_source_sha256']={str(Path('source/features')/p):hashlib.sha256((SOURCE/'features'/p).read_bytes()).hexdigest() for p in owned}
    return compiled,receipt

def evidence(kind,data):
    path=os.environ.get('SGP_UI_SCENE_EVIDENCE')
    if path:
        with open(path,'a') as output:output.write(json.dumps({'kind':kind,**data},sort_keys=True)+'\n')

class SceneBench(AdmissionBench):
    def __init__(self,compiled,**kw):
        super().__init__(compiled,**kw)
        self.put(STEP,0)
    def scene(self,entry='init'):
        return self.call('ui_scene_'+entry,self.context,STEP)

# Real native composition: only retired-parent/Bridge setup, cartridge transport,
# physical delivery, IRQ/DMA/cache scheduling and audio service remain seams.
sys.path.insert(0,str(SOURCE/'features/settings-ui/test'))
import painter_bench as pb
import test_bg_rom as nb
import font_bench as fb
import resource_bench as rb
import guide_resource_bench as gb
from test_scene_admission_rom import ADMISSION_PINS,FADE_STATE,BRIGHT_MAIN,BRIGHT_SUB
from scene_admission_bench import prepare_borrowed,OPTIONS_GET,FADE_GET,BRIGHTNESS_GET
from test_resource_rom import FS_PINS,TRANSPORT,LOCK,UNLOCK,PULLED,SLEEP,CALLBACK
from test_heap_rom import PINS
OPTIONS_SPEED_PIN=(0x0202AD20,56,"530c7819bb9341755535264f43d0b2fff48979083715ace36c48133a5f548bc7")
from module_bench import instruction_set
from contextlib import contextmanager

class NativeSceneBench(nb.NativeBgBench):
    def __init__(self,compiled,fixture,role=2):
        self.span_entries={};self.span_active=[];self.span_metrics={};self.audio_service=False;self.audio_calls=[];self.phase_metrics={};self.trace_returns=[];self.trace=[];self.extra_fetch=set();self.callback_return=None;self.context=0;self.checked=False
        self.physical_valid=True;self.physical_folded=False;self.physical_suspend=None;self.sample_event=0;self.sample_data=(0,0,0,0,0,0);self.acks=[];self.fs_calls=[];self.transports=[]
        self.destroy_fault=False;self.alloc_failure=0;self.allocations=0;self.font_calls=[];self.close_failures=0;self.return_fault=None
        self.fixture=fixture;self.raw,self.config,self.widths,self.glyphs,sections=fixture['painter']
        super().__init__(compiled,sections)
        roots=[rb.INIT,rb.OPEN,rb.READ,gb.FAST,gb.ASYNC,rb.CLOSE,rb.SEEK,rb.CPSR,CALLBACK,0x020d7edc,0x020d8104,
               0x020d7340,0x020d73c0,0x020d73e8,0x020d6b94,0x020d7484,0x020d84c4,0x020d8514,0x020d850c,
               OPTIONS_GET|1,FADE_GET|1,BRIGHTNESS_GET|1,0x020272C9,0x020D3A9C,0x0202AD3D,
               0x0201a911,0x0201aa8d,0x0201a9c5,fb.GENERATE|1,fb.RENDER|1,0x02026069,0x020262b5]
        roots += list(struct.unpack("<9I",bytes(self.u.mem_read(0x0210e124,36))))
        self.extra_fetch=instruction_set(self.u,roots,[(a,a+n) for a,n,_ in (*PINS,*FS_PINS,*ADMISSION_PINS,OPTIONS_SPEED_PIN,*pb.nf.FONT_PINS)])
        self.u.mem_write(CODE,self.code)
        self.checked=True
        assert self.address(0x0201A911,3,11,0x1C000)==1
        prepare_borrowed(self,lambda heap,n:self.address(0x0201AA8D,heap,n),self.widths,fixture['gmif'],role)
        self.step=self.root+4916;self.put(self.step,0)
        self.u.mem_write(self.context+36,struct.pack('<II',self.root+4720,self.root+4784))
        self.u.mem_write(self.root+4720,self.config)
        cfg=bytearray(fixture['guide_config']);struct.pack_into('<I',cfg,12,7)
        self.u.mem_write(self.root+4784,bytes(cfg))
        rb.ResourceBench.archive_fixture(self)
        self.u.mem_write(rb.FAT,fixture['fat']);self.u.mem_write(rb.FNT,fixture['fnt'])
        self.put(rb.FAT+167*8,0x10000000);self.put(rb.FAT+167*8+4,0x10000000+len(self.raw))
        fid=struct.unpack_from('<I',cfg,16)[0];self.put(rb.FAT+fid*8,0x100000);self.put(rb.FAT+fid*8+4,0x100000+len(fixture['guide_raw']))
        for p,v in ((0x021e3628,rb.ARC),(0x021e362c,rb.ARC),(0x021e3630,0),(0x021e3634,0),(0x021e363c,0x42),(0x021e3640,0),
                    (FADE_STATE,0),(BRIGHT_MAIN,0),(BRIGHT_SUB,0),(0x0210f6d8,0x020f56d8),(0x021D05F0,0),(0x021D1140,0)):
            self.put(p,v)
        self.allowed.extend(((rb.ARC+12,rb.ARC+40),(0x021e363c,0x021e3644),
             (fb.FFLAGS,fb.FFLAGS+2),(fb.COLORS,fb.COLORS+6),(fb.LOOKUP,fb.LOOKUP+512),(fb.WORK,fb.WORK+130),
             (0x02111944,0x02111945)))
        self.put(0x023D8703,0,1);self.u.mem_write(0x023CB1A0,bytes(80))
        self.borrowed=[(self.args,bytes(self.u.mem_read(self.args,12)))] if self.args else []
        self.borrowed += [(self.save,bytes(self.u.mem_read(self.save,0x2330C))),(self.field,bytes(self.u.mem_read(self.field,0x110)))]
        self.u.mem_write(CODE,self.code) # Base BG fixture palette address lies inside this larger TU.
        self.trace_entries={self.symbols[n]&~1:n for n in ('sc_build','sc_begin','guide_ui_build','guide_paint_begin','gp_binding','gr_build','gu_view','ui_guide_category','ui_res_text') if n in self.symbols}
        self.span_entries={self.symbols[n]&~1:n for n in ('sc_build','sc_pump','settings_paint_step','guide_paint_step','ui_font_step','bg_callback')}
        self.span_entries.update({fb.GENERATE:'native_font_generate',fb.RENDER:'native_font_render'})
        self.allocations=0;self.writes.clear();self.store_contexts.clear()
    def native_allowed(self,p):return p in self.extra_fetch or nb.NativeBgBench.native_allowed(self,p)
    def address(self,p,*args):
        if self.context and self.get(self.context+28):nb.STATE=self.get(self.context+28)+848
        seed=[0x44440000+i for i in range(8)]
        for r,v in zip(REGS,seed):self.u.reg_write(r,v)
        for i,r in enumerate((UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3)):self.u.reg_write(r,args[i] if i<len(args) else 0)
        self.u.mem_write(STACK,struct.pack('<8I',*(list(args[4:])+[0]*(8-len(args[4:])))))
        self.adapter_entry=CODE<=p<CODE+len(self.code);self.u.reg_write(UC_ARM_REG_SP,STACK);self.u.reg_write(UC_ARM_REG_LR,STOP|1)
        before=self.u.reg_read(UC_ARM_REG_CPSR)&0xdf;ime=self.get(IME);self.low=STACK;start=self.instructions
        self.u.mem_write(STACK-4096,b'\xa5'*64)
        self.u.emu_start(p,STOP,count=4000000)
        assert self.u.reg_read(UC_ARM_REG_PC)==STOP,f'finite scene invocation pc={self.u.reg_read(UC_ARM_REG_PC):08x}'
        # emu_start stops before executing the terminal return address.
        while self.span_active and self.span_active[-1][0]==STOP:
            _,name,begin=self.span_active.pop();cost=self.instructions-begin
            item=self.span_metrics.setdefault(name,{'calls':0,'max_instructions':0})
            item['calls']+=1;item['max_instructions']=max(item['max_instructions'],cost)
        assert not self.span_active,'all nested cost probes returned'
        assert self.u.reg_read(UC_ARM_REG_SP)==STACK and [self.u.reg_read(r) for r in REGS]==seed,'EABI state'
        assert self.u.reg_read(UC_ARM_REG_CPSR)&0xdf==before and self.get(IME)==ime,'IRQ/IME restored'
        assert bytes(self.u.mem_read(STACK-4096,64))==b'\xa5'*64,'stack canary'
        if self.checked:assert bytes(self.u.mem_read(CODE,len(self.code)))==self.code,'whole composed payload unchanged'
        self.metrics.append((p,STACK-self.low,self.instructions-start));self.writes.clear();self.store_contexts.clear()
        return self.u.reg_read(UC_ARM_REG_R0)
    def store(self,u,a,p,n,v,d):
        if STACK-4096<=p<p+n<=STACK:return
        # All real borrowed objects are checked byte-for-byte at each lifecycle
        # barrier. Native BG retains its immutable front/DMA upload checks.
        try:return super().store(u,a,p,n,v,d)
        except AssertionError as exc:
            raise AssertionError(f'{exc}; pc={u.reg_read(UC_ARM_REG_PC):08x} phase={self.get(self.get(self.context+28)+56) if self.context and self.get(self.context+28) else -1}') from exc
    def hook(self,u,p,n,d):
        while self.span_active and p==self.span_active[-1][0]:
            _,name,start=self.span_active.pop();cost=self.instructions-start
            item=self.span_metrics.setdefault(name,{'calls':0,'max_instructions':0})
            item['calls']+=1;item['max_instructions']=max(item['max_instructions'],cost)
        if p in self.span_entries:self.span_active.append((u.reg_read(UC_ARM_REG_LR)&~1,self.span_entries[p],self.instructions))
        if self.trace_returns and p==self.trace_returns[-1][0]:
            _,name=self.trace_returns.pop();self.trace.append((name,u.reg_read(UC_ARM_REG_R0)))
        if p in getattr(self,'trace_entries',{}):self.trace_returns.append((u.reg_read(UC_ARM_REG_LR)&~1,self.trace_entries[p]))
        if self.return_fault==p:
            self.return_fault=None;self.put(rb.ARC+28,self.get(rb.ARC+28)&~0x80)
        if p in (CONSUME&~1,ACK&~1):
            self.instructions+=1
            assert u.reg_read(UC_ARM_REG_R0)==self.context and u.reg_read(UC_ARM_REG_R1)==self.get(self.context+32)
            if p==CONSUME&~1:
                out=u.reg_read(UC_ARM_REG_R2)
                if self.physical_valid and self.sample_event in (1,2):self.u.mem_write(out,struct.pack('<II4H',*self.sample_data))
                value=self.sample_event if self.physical_valid else 3;self.sample_event=0;self.ret(value)
            else:
                observed=u.reg_read(UC_ARM_REG_R2);self.acks.append(observed)
                app=self.get(self.context+28)
                if self.get(self.context+4)==2:
                    assert self.get(app+1512+92)==1 and self.get(app+1512+104)==0,'Guide rearmed before ACK'
                else:assert self.get(app+1436+221,1)==1,'Settings rearmed before ACK'
                # Faithful finite resident boundary: folded, superseded or lost
                # owner refuses. Next consume still reports lost ownership.
                self.ret(int(self.physical_valid and not self.physical_folded and
                    (self.physical_suspend is None or observed==self.physical_suspend)))
            return
        if p in (0x020D5714,0x020D579C):
            # Explicit scheduler/queue seam. Real owner validation, pending
            # generations, native IRQ entry/restore and Scene retries execute.
            assert self.audio_service and u.reg_read(UC_ARM_REG_CPSR)&128
            arg=u.reg_read(UC_ARM_REG_R0);self.audio_calls.append((p,arg));self.instructions+=1
            pool=0x021E1A60
            if p==0x020D5714:
                assert arg==0;node=self.get(pool)
                if node:
                    self.put(pool,self.get(node))
                    if not self.get(pool):self.put(pool+16,0)
                self.ret(node)
            else:
                assert 0x021E1D40<=arg<0x021E3540 and (arg-0x021E1D40)%24==0
                tail=self.get(pool+12)
                if tail:self.put(tail,arg)
                else:self.put(pool+8,arg)
                self.put(pool+12,arg);self.put(arg,0);self.ret()
            return
        if p==STOP+0x40:
            ret=self.callback_return;self.callback_return=None;self.ret();u.reg_write(UC_ARM_REG_PC,ret);return
        if p in (LOCK,UNLOCK,PULLED):self.instructions+=1;self.ret(0);return
        if p==SLEEP:raise AssertionError('unexpected scheduler sleep')
        if p==TRANSPORT:
            self.instructions+=1
            dma,pos,dst,length=[u.reg_read(r) for r in (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3)]
            cb,arg,async_=struct.unpack('<3I',bytes(u.mem_read(u.reg_read(UC_ARM_REG_SP),12)))
            assert dma==0 and async_==1 and cb==CALLBACK and arg==rb.ARC
            raw,base=(self.raw,0x10000000) if pos>=0x10000000 else (self.fixture['guide_raw'],0x100000)
            assert base<=pos<=pos+length<=base+len(raw)
            self.transports.append((pos,dst,length));u.mem_write(dst,raw[pos-base:pos-base+length])
            assert self.callback_return is None;self.callback_return=u.reg_read(UC_ARM_REG_LR)
            u.reg_write(UC_ARM_REG_R0,arg);u.reg_write(UC_ARM_REG_LR,STOP+0x40);u.reg_write(UC_ARM_REG_PC,cb);return
        if p in (rb.INIT,rb.OPEN,rb.READ,gb.FAST,gb.ASYNC,rb.CLOSE,rb.SEEK):
            file=u.reg_read(UC_ARM_REG_R0);self.fs_calls.append((p,file))
            if CODE<=u.reg_read(UC_ARM_REG_LR)&~1<CODE+len(self.code):assert self.get(IME)==1 and not u.reg_read(UC_ARM_REG_CPSR)&128
            if p==rb.CLOSE and self.close_failures:
                self.close_failures-=1;self.put(rb.ARC+28,self.get(rb.ARC+28)|0x80);self.return_fault=u.reg_read(UC_ARM_REG_LR)&~1
        if p==self.symbols.get('ui_heap38_destroy',0)&~1 and self.destroy_fault:
            self.destroy_fault=False;self.put(self.counts+76,1,2)
        if p==self.symbols.get('ui_alloc38',0)&~1:
            self.allocations+=1
        if p==ALLOC and self.context and self.alloc_failure==self.allocations and self.alloc_failure and u.reg_read(UC_ARM_REG_R0)==self.get(self.heap+16):
            self.alloc_failure=0;self.ret(0);return
        if p in (fb.GENERATE,fb.RENDER):
            self.font_calls.append(p);assert u.reg_read(UC_ARM_REG_CPSR)&128
            app=self.get(self.context+28)
            assert self.get(app+104+8)==0 and self.get(app+104+616)==6,'UIR closed before painting'
            if self.get(self.context+4)==2:assert self.get(app+1184+8)==0 and self.get(app+1184+220)==9,'SGG closed before painting'
        if p==gb.FAST and self.context and self.get(self.context+28) and u.reg_read(UC_ARM_REG_R0)==self.get(self.context+28)+1184:
            assert self.get(self.get(self.context+28)+104+8)==0 and self.get(self.get(self.context+28)+104+616)==6,'serial reader ownership'
        font_body=any(lo<=p<hi for lo,hi in ((0x020021a0,0x02002c90),(0x02002e7c,0x02002ec8),(0x02002fac,0x02003030),
            (0x02020358,0x020204b8),(0x0202604c,0x02026110),(0x020262b4,0x020262d4),(0x0201dacc,0x0201ec48)))
        if CODE<=p<CODE+len(self.code) or (p in self.extra_fetch or font_body) and p not in nb.NATIVE_INSTRUCTIONS:
            self.instructions+=1;self.low=min(self.low,u.reg_read(UC_ARM_REG_SP));assert STACK-4096<=self.low<=STACK
            if CODE<=p<CODE+len(self.code):pb.check_compiled(self.code,p,n)
            if self.active_service and p==self.active_service[1]:self.active_service=None
            return
        return super().hook(u,p,n,d)
    def scene(self,entry='init',publish=True):
        app=self.get(self.context+28);phase=self.get(app+56) if app else -1
        result=self.call('ui_scene_'+entry,self.context,self.step)
        _,stack,cost=self.metrics[-1];key=f'{entry}:{phase}'
        old=self.phase_metrics.setdefault(key,{'calls':0,'max_stack':0,'max_instructions':0})
        old['calls']+=1;old['max_stack']=max(old['max_stack'],stack);old['max_instructions']=max(old['max_instructions'],cost)
        if publish and self.get(0x021D110C):
            self.put(0x04000006,192,2);self.address(self.get(0x021D110C),self.get(0x021D1110))
        return result
    def finish_init(self):
        for _ in range(1800):
            result=self.scene()
            if result!=SCENE_MORE:return result
        raise AssertionError('scene init finite bound')
    def finish_exit(self):
        self.put(self.context+32,0) # Explicit Bridge deactivation handoff seam.
        for _ in range(300):
            result=self.scene('exit',False)
            if result!=SCENE_MORE:return result
        raise AssertionError('scene exit finite bound')
    def input(self,key=0,held=None,flags=0,event=1,suspend=0,x=0,y=0,down=0,mode=0,mapped=None):
        self.put(self.context+32,7)
        self.sample_data=(self.sample_data[0]+1,suspend,key if held is None else held,key,0,flags);self.sample_event=event
        self.put(0x021D1150,key if held is None else held);self.put(0x021D1154,key if mapped is None else mapped);self.put(0x021D1158,0);self.put(0x021D1140,mode)
        self.put(0x021D116C,x,2);self.put(0x021D116E,y,2);self.put(0x021D1170,down,2)
        return self.scene('main')
    def idle(self):
        for _ in range(1200):
            a=self.get(self.context+28)
            if self.get(a+56)==14:return
            assert self.input()==SCENE_MORE
        raise AssertionError('scene main finite bound')
    def borrowed_intact(self):
        for p,data in self.borrowed:assert bytes(self.u.mem_read(p,len(data)))==data,'borrowed owner modified'
    def heap_free(self):
        h=self.get(self.heap+16);node=self.get(h+0x24);sizes=[]
        while node:
            assert len(sizes)<32;sizes.append(self.get(node+4));node=self.get(node+12)
        return sum(sizes),max(sizes,default=0),len(sizes)

    def audio_pool(self):
        self.audio_service=True
        self.allowed.extend(((0x021E1A40,0x021E1A44),(0x021E1A60,0x021E1A84),
            (0x021E1D40,0x021E3540),(0x021D05F0,0x021D05F4)))
        self.put(0x021E1A40,1);self.u.mem_write(0x021E1A60,bytes(36))
        self.u.mem_write(0x021E1D40,bytes(48));self.put(0x021E1A60,0x021E1D40);self.put(0x021E1A70,0x021E1D40)

    def record(self,label,lang):
        app=self.get(self.context+28);roots=[]
        if self.get(self.heap):
            for i in range(16):
                p=self.get(self.heap+28+4*i)
                if p:roots.append({'payload':p,'native_extent':self.get(p-28)+16})
        evidence(label,{'language':lang,'role':self.get(self.context+4),'app':app,
            'heap_backing':self.get(self.heap+20),'roots':roots,'free':self.heap_free() if roots else None,
            'phase_metrics':self.phase_metrics,'span_metrics':self.span_metrics,'font_calls':len(self.font_calls)})

    def checkpoint(self):
        assert self.callback_return is None and self.dma_pending is None
        spans=((0x02000000,0x400000),(0x027e0000,0x4000),(0x04000000,0x1000),
               (0x04001000,0x1000),(0x05000000,0x1000),(0x06000000,0x20000),(0x06200000,0x20000))
        return [(p,bytes(self.u.mem_read(p,n))) for p,n in spans],self.allocations
    def restore_checkpoint(self,snapshot):
        memories,self.allocations=snapshot
        for p,data in memories:self.u.mem_write(p,data)
        self.callback_return=self.return_fault=self.active_service=self.dma_pending=self.upload=None
        self.physical_valid=True;self.physical_folded=False;self.physical_suspend=None;self.sample_event=0;self.acks.clear()
        self.trace_returns.clear();self.trace.clear();self.span_active.clear();self.close_failures=0;self.alloc_failure=0;self.fail=None;self.clean.clear()
        assert bytes(self.u.mem_read(CODE,len(self.code)))==self.code
