"""Finite prepared-state admission probes, never an installed Scene.

Class A seams native getters/transition queries and allocation construction.
Class B reuses native heap setup, executes the pinned queries/getter, and uses
real GF/NNS allocations. Parent teardown and authenticated Bridge handoff are
explicit prepared-state seams, not an emulation of a complete Scene.
"""
import hashlib
import importlib.util
import struct
import subprocess
from pathlib import Path
from heap_bench import *
from font_bench import synthetic_widths
from bg_bench import object_details,check_compiled,prepare_retired_wvr,retired_wvr_snapshot
from module_bench import instruction_set

REASON=0x027E377C
CONTEXT_OFFSET=4848
HEAP_OFFSET=4944
WAIT,REFUSE,READY=range(3)
NONE,OUTPUT,CONTEXT_ERROR,EXECUTION,FIELD_ERROR,ARGS_ERROR,FONT_ERROR,CALLBACK,PRINTER,DMA,DISPLAY,FADE,BRIGHTNESS=range(13)
OPTIONS_GET,FADE_GET,BRIGHTNESS_GET=0x02028EA8,0x0200FB5C,0x0200B5C0


def compile_admission(directory,scaffold=False,baseline=False,mutation=None):
    directory=Path(directory)
    body=(SOURCE/'features/ui-native/scene_admission.c').read_text() if not scaffold and not baseline else ''
    if scaffold:
        body='''#include "scene_admission.h"
SceneAdmission ui_scene_admit(const UiSceneContext *c,unsigned *r) {
 (void)c;(void)r;return SCENE_ADMIT_REFUSE;
}
'''
    if mutation:
        old,new=mutation
        assert old in body
        body=body.replace(old,new,1)
    text='#include "heap.c"\n#include "resource.c"\n#include "font.c"\n#include "bg.c"\n'+body
    source=directory/'admission_unit.c';obj=directory/'admission.o'
    source.write_text(text)
    cp=subprocess.run(['clang',*FLAGS,'-fno-jump-tables','-fstack-usage','-I',str(SOURCE/'features/ui-native'),
                       '-c',str(source),'-o',str(obj)],capture_output=True,text=True)
    if cp.returncode:raise AssertionError(cp.stderr)
    spec=importlib.util.spec_from_file_location('scene_admission_loader',SOURCE/'features/options/tools/carica_text.py')
    loader=importlib.util.module_from_spec(spec);spec.loader.exec_module(loader)
    compiled=loader.load_text(obj.read_bytes(),CODE)
    receipt=object_details(obj.read_bytes(),compiled[0])
    receipt['stack_usage']=(directory/'admission.su').read_text().replace(str(directory),'TEMP')
    return compiled,receipt


def prepare_borrowed(b,allocate,widths=None,gmif=0x8C,role=1,bottom=1,domain=0):
    """Only the post-parent + Bridge handoff is prepared. No app or heap38."""
    b.root=allocate(11,5036);b.field=allocate(11,0x110);b.process=allocate(11,16)
    b.manager=allocate(11,40);b.save=allocate(3,0x2330C)
    b.font=allocate(3,124);b.narc=allocate(3,84);b.widths=allocate(3,509)
    b.args=allocate(11,12) if role==1 else 0
    for p,n in ((b.root,5036),(b.field,0x110),(b.process,16),(b.manager,40),(b.save,0x2330C),(b.font,124),(b.narc,84)):
        b.u.mem_write(p,bytes(n))
    b.context=b.root+CONTEXT_OFFSET;b.heap=b.root+HEAP_OFFSET;b.options=b.save+0x100
    b.put(0x021D4158,b.field);b.put(b.field,b.process);b.put(b.field+12,b.save)
    b.put(b.field+0x18,bottom);b.put(b.field+0x10C,domain);b.put(b.process+4,b.manager)
    b.put(b.save+0x2302C,0xF0)
    b.template=0x020FA354 if role==1 else 0x023D7B10
    # Prepared resident template identity; these callbacks are never executed.
    callbacks=(0x023CB801,0x023CB805,0x023CB809,0xFFFFFFFF)
    b.u.mem_write(b.template,struct.pack('<4I',*callbacks))
    b.u.mem_write(b.manager,struct.pack('<10I',*callbacks,1,0,b.args,b.root,0xA6A6A6A6,0x69696969))
    if b.args:b.u.mem_write(b.args,struct.pack('<3I',0xA5962CF0,b.options,b.field+0x10C))
    b.u.mem_write(b.context,struct.pack('<16I',0x32435355,role,7,b.field,b.options,b.field+0x10C,b.args,0,0,
                                        b.root+4720,b.root+4784,0,0,b.heap,0,0))
    b.put(b.root+4624+8,role);b.put(b.root+4624+12,7)
    b.put(b.root+4784+12,7)
    b.put(0x0211188C,0x02111890);b.put(0x0211192C,b.font);b.put(0x02111944,1,1)
    for off,v in ((0,1),(4,0x02026111),(8,3),(12,64),(0x54,b.narc),(0x5C,16),(0x60,0x7F50),
                  (0x64,509),(0x68,0x02021010),(0x70,0x020262B5),(0x74,b.widths),(0x78,gmif)):
        b.put(b.font+off,v)
    b.u.mem_write(b.widths,widths if widths is not None else synthetic_widths())
    b.u.mem_write(0x021D110C,bytes(16));b.u.mem_write(0x021D1F74,bytes(32))
    b.put(0x04000304,0x203,2);b.put(0x02110C7C,1);b.put(0x02110C80,3)
    b.put(0x04000064,0)
    for ch in range(4):b.put(0x040000B8+ch*12,0)
    b.u.mem_write(0x021E15C0,struct.pack('<13H',0,4,96,0,3,16,0,0,0,128,256,0,0))
    b.u.mem_write(0x04000240,bytes((0x83,0x8B,0x81,0,0x83,0x82,0x8A,0,0x81,0x82)))
    prepare_retired_wvr(b)
    b.put(REASON,0xA5A59696)


class AdmissionChecks:
    def snapshot(self):
        return tuple(bytes(self.u.mem_read(p,n)) for p,n in ((0x02000000,0x400000),(0x04000000,0x1000)))
    def admit(self,context=None,reason=REASON):
        before=self.snapshot();self.writes.clear();self.low=STACK
        self.admitting=True
        try:result=self.call('ui_scene_admit',self.context if context is None else context,reason)
        finally:self.admitting=False
        assert self.snapshot()==before,'admission changed main RAM or MMIO'
        assert all(STACK-1024<=p<p+n<=STACK or reason==REASON and p==REASON and n==4
                   for p,n,*rest in self.writes),'non-output mutation'
        return result,self.get(reason) if reason==REASON else None
    def store(self,u,access,p,n,v,data):
        if getattr(self,'admitting',False):
            self.writes.append((p,n,v))
            assert STACK-1024<=p<p+n<=STACK or p==REASON and n==4,f'admission store {p:08x}/{n}'
        else:super().store(u,access,p,n,v,data)


class AdmissionBench(AdmissionChecks,HeapBench):
    def __init__(self,compiled,role=1,bottom=1,domain=0):
        self.admitting=False
        super().__init__(compiled)
        heap11=PARENT+0x10000;self.header(heap11,0x1C000)
        self.put(heap11-16,0x5544,2);self.put(heap11-12,0x1C000)
        self.put(self.handles+16,heap11);self.put(self.parents+16,PARENT);self.put(self.raws+16,heap11);self.put(self.idxs+11,4,1)
        self.next11=heap11+0x100;self.next3=PARENT+0x30000
        def allocate(heap,n):
            size=(n+19)&~3;p=self.next11 if heap==11 else self.next3
            if heap==11:self.next11+=size+32
            else:self.next3+=size+32
            self.put(p-32,0x5544,2);self.put(p-28,size)
            self.u.mem_write(p-16,struct.pack('<4I',0,0,0,heap))
            return p
        self.fade_finished=1;self.brightness_inactive=1;self.getter_calls=[]
        prepare_borrowed(self,allocate,role=role,bottom=bottom,domain=domain)
        self.fetch=instruction_set(self.u,[v for k,v in self.symbols.items() if not k.startswith('$')],[(CODE,CODE+len(self.code))])
    def hook(self,u,p,n,data):
        if p in (OPTIONS_GET,FADE_GET,BRIGHTNESS_GET,0x020D3A90,0x020D3A9C):
            self.instructions+=1
            if p in (OPTIONS_GET,FADE_GET,BRIGHTNESS_GET):self.getter_calls.append(p)
            assert u.reg_read(UC_ARM_REG_SP)%8==0
            self.ret((u.reg_read(UC_ARM_REG_CPSR)&0x80) if p==0x020D3A90 else (u.reg_read(UC_ARM_REG_CPSR)&0x1F) if p==0x020D3A9C else self.options if p==OPTIONS_GET else self.fade_finished if p==FADE_GET else self.brightness_inactive)
            return
        if p!=STOP and CODE<=p<CODE+len(self.code):
            assert p in self.fetch
            assert u.reg_read(UC_ARM_REG_CPSR)&32
            check_compiled(self.code,p,n)
        super().hook(u,p,n,data)
