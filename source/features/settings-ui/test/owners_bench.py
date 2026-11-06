"""Composed real Settings/Training/Shiny ARM; Class A native boundaries explicit."""
import ctypes as C
import importlib.util
from pathlib import Path
import struct
import sys
from unicorn.arm_const import UC_ARM_REG_CPSR
SOURCE = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location('owners_shiny_bench', SOURCE/'features/shiny/test/ui_transaction_bench.py')
sh = importlib.util.module_from_spec(spec); spec.loader.exec_module(sh)
spec = importlib.util.spec_from_file_location('owners_model_types', Path(__file__).with_name('test_state.py'))
model = importlib.util.module_from_spec(spec); spec.loader.exec_module(model)
base, FS, SAVE, APP, OPTIONS, IME = sh.base, sh.FS, sh.SAVE, sh.APP, sh.OPTIONS, sh.IME
RT, STATE, DESCRIPTOR = sh.RT, sh.STATE, sh.DESCRIPTOR
OWNER_CODE, MODEL, OWNERS, SNAPSHOT = 0x02206000, 0x022D0800, 0x022D0400, 0x022D0600
MONO, BUTTON, POOL, NODES = 0x021D05F0, 0x021D1140, 0x021E1A60, 0x021E1D40
class Audio(C.Structure):
    _fields_=[(x,C.c_uint) for x in ('original_raw','expected_raw','accepted_target','accepted_generation','pending_target','pending_generation','app_generation','ever_previewed','pending_changed')]
class Owners(C.Structure):
    _fields_=[(x,C.c_uint) for x in ('magic','bytes','app','generation','fs','save','options')]+[('native_raw',C.c_ushort),('plus_raw',C.c_ubyte*5),('plus_guard',C.c_ubyte*5),('plus_load',C.c_ubyte),('reserved',C.c_ubyte),('mirrors',C.c_ubyte*2),('button_raw',C.c_uint),('audio',Audio),('opened',model.Snapshot)]

def compile_all(directory, owners_source=None):
    old,ts=base.training.compile_native(directory/'historical')
    te,us=base.compile_object(SOURCE/'features/training-native/ui_transaction.c',directory/'training.o',['-DSGP_SETTINGS_UI_SUCCESSOR=1'])
    core,cs=base.shiny_core.compile_native(directory/'core')
    native,ns=base.shiny.compile_native(directory/'native','native')
    loader=base.training.module(SOURCE/'features/options/tools/carica_text.py','settings_owner_loader')
    combined=directory/'owners-unit.c'
    if owners_source is None:owner_path=SOURCE/'features/settings-ui/owners.c'
    else:
        owner_path=directory/'owners-mutant.c'
        owner_path.write_text(owners_source.replace('#include "owners.h"','#include "'+str(SOURCE/'features/settings-ui/owners.h')+'"'))
    combined.write_text('#include "'+str(SOURCE/'features/settings-ui/state.c')+'"\n#include "'+str(owner_path)+'"\n')
    base.compile_object(combined,directory/'owners.o',['-fstack-usage'])
    owners,os=loader.load_text((directory/'owners.o').read_bytes(),OWNER_CODE)
    base.compile_object(SOURCE/'features/shiny/ui_transaction.c',directory/'shiny-ui.o',['-DSGP_SETTINGS_UI_SUCCESSOR=1',f'-DSGP_SETTINGS_UI_FINAL_CHECK={os["settings_final_check"]}'])
    shiny,ss=loader.load_text((directory/'shiny-ui.o').read_bytes(),sh.EXT)
    return (old,ts,te,us,core,cs,native,ns),shiny,ss,owners,os

class Bench(sh.Bench):
    def __init__(self,compiled,leased=True,real_native=False):
        self.real_native=real_native
        self.native_calls=[]
        self.in_gate=False;self.gate_return=0;self.gate_contexts=[];self.gate_writes=[]
        self.applying=False;self.apply_store_start=0;self.calls_after_store=[]
        self.bad_refusal_writes=[];self.bad_capture_writes=[]
        super().__init__(compiled,leased)
        self.u.reg_write(UC_ARM_REG_CPSR,(self.u.reg_read(UC_ARM_REG_CPSR)&~0x9f)|0x1f)
        self.os=compiled[4]
        self.u.mem_write(OWNER_CODE,compiled[3])
        self.put(OPTIONS,0x8001)
        self.u.mem_write(0x023D8710,bytes(3)+bytes([0,1,0,1,0,1]))
        self.u.mem_write(0x023D8700,bytes([0,1,0,1,0x5a]))
        for p,v in ((0x023D8E41,0x5a),(0x023D89E2,0x5a),(0x023DA240,0x57)):
            self.u.mem_write(p,bytes([v]))
        self.put(MONO,0); self.put(BUTTON,0)
        self.pool(4)
        self.stack=0x027E3378
        self.active=True
        self.reset_trace()
    def pool(self,count,pending=0):
        self.put(0x021E1A40,1)
        self.u.mem_write(POOL,bytes(36))
        for i in range(count):
            self.u.mem_write(NODES+24*i,struct.pack('<6I',NODES+24*(i+1) if i+1<count else 0,0,0,0,0,0))
        self.put(POOL,NODES if count else 0); self.put(POOL+16,NODES+24*(count-1) if count else 0)
        if pending:
            p=NODES+24*255; self.u.mem_write(p,bytes(24)); self.put(POOL+8,p); self.put(POOL+12,p)
    def write_hook(self,u,access,address,size,value,data):
        super().write_hook(u,access,address,size,value,data)
        if self.in_gate and not (0x027e0080<=address<address+size<=self.stack):
            self.gate_writes.append((address,size,value))
    def hook(self,u,address,size,data):
        from unicorn.arm_const import UC_ARM_REG_R0,UC_ARM_REG_LR
        if self.in_gate and address==self.gate_return:self.in_gate=False
        gs=getattr(self,'gs',{})
        if address==(gs.get('settings_final_check',1)&~1):
            self.in_gate=True;self.gate_return=u.reg_read(UC_ARM_REG_LR)&~1
            context=u.reg_read(UC_ARM_REG_R0)
            wire=bytes(u.mem_read(context,492)) if (0x02000000<=context<=0x02400000-492 or 0x027e0000<=context<=0x027e4000-492) else b''
            self.gate_contexts.append((context,wire))
        native_entries=(0x02028ea8,0x020d3a38,0x020d3a4c,0x020d3a90,0x020d5714,0x020d579c,0x0200597c,0x0202877c,0x02028758)
        if self.applying and len(self.owner_writes)>self.apply_store_start and address in native_entries:self.calls_after_store.append(address)
        if self.in_gate and address in native_entries:raise AssertionError('native call in pure gate '+hex(address))
        if self.real_native and address in (0x02028EA8,0x020D3A38,0x020D3A4C,0x020D5714,0x020D579C,0x0202ACF4):
            from unicorn.arm_const import UC_ARM_REG_R0,UC_ARM_REG_R1
            self.native_calls.append((address,u.reg_read(UC_ARM_REG_R0),u.reg_read(UC_ARM_REG_R1)))
            return  # Execute guarded native bytes, with no return stub.
        # Class A only: each native seam enforces the exact ABI and bounded
        # queue protocol. Class B overrides these with actual guarded ROM code.
        if address in (0x020D3A38,0x020D3A4C,0x020D5714,0x020D579C,0x0202ACF4):
            from unicorn.arm_const import UC_ARM_REG_R0,UC_ARM_REG_R1
            a,b=u.reg_read(UC_ARM_REG_R0),u.reg_read(UC_ARM_REG_R1)
            self.native_calls.append((address,a,b))
            cpsr=u.reg_read(UC_ARM_REG_CPSR)
            if address==0x020D3A38:
                u.reg_write(UC_ARM_REG_CPSR,cpsr|128); self.ret(cpsr&128)
            elif address==0x020D3A4C:
                u.reg_write(UC_ARM_REG_CPSR,(cpsr&~128)|(a&128)); self.ret()
            elif address==0x020D5714:
                assert a==0 and cpsr&128
                p=self.get(POOL)
                if p:
                    self.put(POOL,self.get(p))
                    if not self.get(POOL):self.put(POOL+16,0)
                self.ret(p)
            elif address==0x020D579C:
                assert cpsr&128 and NODES<=a<NODES+6144 and (a-NODES)%24==0
                tail=self.get(POOL+12)
                if tail:self.put(tail,a)
                else:self.put(POOL+8,a)
                self.put(POOL+12,a); self.put(a,0); self.ret()
            else:
                assert a==0
                self.put(BUTTON,3 if b==1 else 0); self.ret()
            return
        super().hook(u,address,size,data)
    def call(self,address,*args):
        try:return super().call(address,*args)
        finally:self.in_gate=False
    def capture(self,owners=OWNERS,out=SNAPSHOT,app=APP):
        start=len(self.all_writes);result=self.call(self.os['settings_owner_capture'],app,owners,out)
        if result:
            self.bad_capture_writes.extend((a,n,v) for a,n,v in self.all_writes[start:] if a!=IME and not (0x027e0080<=a<a+n<=self.stack))
        return result
    def init(self):
        result=self.capture()
        if result:return result
        self.call(self.os['settings_init'],MODEL,SNAPSHOT)
        self.release(); self.reset_trace(); return 0
    def read_model(self):return model.State.from_buffer_copy(bytes(self.u.mem_read(MODEL,C.sizeof(model.State))))
    def read_owners(self):return Owners.from_buffer_copy(bytes(self.u.mem_read(OWNERS,C.sizeof(Owners))))
    def release(self):self.call(self.os['settings_sample'],MODEL,0,1,0)
    def key(self,key,row=None):
        if row is not None:self.u.mem_write(MODEL+model.State.row.offset,struct.pack('<H',row))
        self.release(); self.call(self.os['settings_sample'],MODEL,key,1,0)
        return self.call(self.os['settings_step'],MODEL,key,0)
    def request(self):
        self.key(model.X); self.key(model.LEFT); return self.key(model.A)
    def apply(self):
        self.applying=True;self.apply_store_start=len(self.owner_writes)
        start=len(self.all_writes)
        try:
            result=self.call(self.os['settings_apply'],MODEL,OWNERS)
            if result!=4:
                allowed={MODEL+getattr(model.State,x).offset for x in ('awaiting_apply','owner_status','notice','view','release_gate','sample_ready')}
                for a,n,v in self.all_writes[start:]:
                    if a!=IME and not (0x027e0080<=a<a+n<=self.stack) and not set(range(a,a+n))<=allowed:
                        self.bad_refusal_writes.append((a,n,v))
            return result
        finally:self.applying=False
    def preview(self):return self.call(self.os['settings_owner_preview'],OWNERS,MODEL)
    def rollback(self):return self.call(self.os['settings_owner_rollback'],OWNERS)
