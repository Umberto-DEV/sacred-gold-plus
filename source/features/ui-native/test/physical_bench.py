"""Bounded compiled ARM9 CPU harness; native/hardware seams are explicit."""
import hashlib
import importlib.util
from pathlib import Path
import struct
import subprocess
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_ARM, UC_HOOK_CODE, UC_HOOK_MEM_WRITE, UC_HOOK_MEM_READ
from unicorn.arm_const import *
SOURCE=Path(__file__).resolve().parents[3]
CODE,SLOT,OWNER,OUT=0x02204000,0x022D0000,0x022D1000,0x022D2000
SYSTEM,KEY,SHARED=0x021D110C,0x04000130,0x027FFFA8
MAPPING,LID,KEYPAD,MAIN=0x0201A5E8,0x0200110C,0x0201A4DC,0x02000DB0
STACK,STOP,IME=0x027E3778,0x02203F00,0x04000208
REGS=[UC_ARM_REG_R4,UC_ARM_REG_R5,UC_ARM_REG_R6,UC_ARM_REG_R7,UC_ARM_REG_R8,UC_ARM_REG_R9,UC_ARM_REG_R10,UC_ARM_REG_R11]
FLAGS=['--target=armv5te-none-eabi','-mcpu=arm946e-s','-mthumb','-Oz','-ffreestanding','-fno-builtin','-fno-stack-protector','-fomit-frame-pointer','-fno-unwind-tables','-fno-asynchronous-unwind-tables','-Wall','-Wextra','-Werror']
def compile_physical(directory):
    obj=directory/'physical.o'
    config={'SLOT':SLOT,'SYSTEM':SYSTEM,'KEYINPUT':KEY,'SHARED':SHARED,'MAPPING':MAPPING|1,'LID':LID|1}
    subprocess.run(['clang',*FLAGS,*[f'-DSGP_PHYSICAL_{k}_ADDR={v}' for k,v in config.items()],'-fstack-usage','-c',str(SOURCE/'features/ui-native/physical.c'),'-o',str(obj)],check=True,capture_output=True)
    spec=importlib.util.spec_from_file_location('physical_text_loader',SOURCE/'features/options/tools/carica_text.py')
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    code,symbols=mod.load_text(obj.read_bytes(),CODE)
    return code,symbols

def bl(address,target):
    delta=(target&~1)-address-4
    assert delta%2==0 and -0x400000<=delta<0x400000
    return struct.pack('<HH',0xf000|((delta>>12)&2047),0xf800|((delta>>1)&2047))

class Bench:
    def __init__(self,compiled):
        self.code,self.symbols=compiled
        self.u=Uc(UC_ARCH_ARM,UC_MODE_ARM)
        for address,length in ((0x02000000,0x400000),(0x027E0000,0x4000),(0x027FF000,0x1000),(0x04000000,0x1000)):
            self.u.mem_map(address,length)
        self.u.mem_write(CODE,self.code)
        self.u.reg_write(UC_ARM_REG_CPSR,0x5f)
        self.put(IME,1);self.put(SYSTEM+0x54,4);self.put(SYSTEM+0x58,8)
        self.input(0)
        self.mapping_calls=self.lid_calls=0
        self.lid_callback=self.mapping_callback=None
        self.read_callback=None
        self.native=False
        self.stack=STACK;self.writes=[];self.reads=[];self.min_sp=STACK;self.instructions=0;self.call_low=STACK;self.metrics=[]
        self.u.hook_add(UC_HOOK_CODE,self.hook)
        self.u.hook_add(UC_HOOK_MEM_WRITE,self.write_hook)
        self.u.hook_add(UC_HOOK_MEM_READ,self.read_hook)
        self.allowed=[(SLOT,SLOT+48),(OUT,OUT+16)]
    def put(self,p,v,size=4):self.u.mem_write(p,int(v&((1<<(size*8))-1)).to_bytes(size,'little'))
    def get(self,p,size=4):return int.from_bytes(self.u.mem_read(p,size),'little')
    def input(self,held,closed=False):
        self.put(KEY,(~held)&0x3ff,2)
        self.put(SHARED,((~held)&0x2c00)|(0x8000 if closed else 0),2)
    def ret(self,value=0):
        self.u.reg_write(UC_ARM_REG_R0,value);self.u.reg_write(UC_ARM_REG_PC,self.u.reg_read(UC_ARM_REG_LR))
    def hook(self,u,address,size,data):
        self.instructions+=1
        assert self.stack-256 <= u.reg_read(UC_ARM_REG_SP) <= self.stack,'stack instruction bound'
        self.min_sp=min(self.min_sp,u.reg_read(UC_ARM_REG_SP))
        self.call_low=min(self.call_low,u.reg_read(UC_ARM_REG_SP))
        if address==MAPPING:
            self.mapping_calls+=1
            assert u.reg_read(UC_ARM_REG_SP)%8==0,'mapping call alignment'
            if self.mapping_callback:self.mapping_callback(self)
            if not self.native:self.ret();return
        if address==LID:
            self.lid_calls+=1
            assert u.reg_read(UC_ARM_REG_SP)%8==0,'lid call alignment'
            if self.lid_callback:self.lid_callback(self)
            if not self.native:self.ret();return
        if address==STOP:u.emu_stop();return
        assert CODE<=address<CODE+len(self.code) or self.native_allowed(address),f'unknown call/code {address:08x}'
    def native_allowed(self,address):return False
    def write_hook(self,u,access,address,size,value,data):
        self.writes.append((address,size,value))
        assert any(a<=address<address+size<=b for a,b in self.allowed) or self.stack-256<=address<address+size<=self.stack,f'unexpected write {address:08x}/{size}'
    def read_hook(self,u,access,address,size,value,data):
        self.reads.append((address,size))
        if 0x04000000<=address<0x04001000:assert (address,size)==(KEY,2),f'unknown MMIO {address:08x}/{size}'
        if self.read_callback:self.read_callback(self,address,size)
    def call(self,name,*args):return self.address(self.symbols[name],*args)
    def address(self,address,*args):
        self.call_low=self.stack
        instruction_start=self.instructions
        seed=[0x44440000+i for i in range(8)]
        for r,v in zip(REGS,seed):self.u.reg_write(r,v)
        for i,r in enumerate((UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3)):
            self.u.reg_write(r,args[i] if i<len(args) else 0)
        self.u.reg_write(UC_ARM_REG_SP,self.stack);self.u.reg_write(UC_ARM_REG_LR,STOP|1)
        cpsr=self.u.reg_read(UC_ARM_REG_CPSR)&0xdf;ime=self.get(IME)
        frozen=[(p,bytes(self.u.mem_read(p,n))) for p,n in ((0x02000000,0x400000),(0x027e0000,0x4000),(0x027ff000,0x1000),(0x04000000,0x1000))]
        self.u.emu_start(address,STOP,count=20000)
        allowed=[*self.allowed,(self.stack-256,self.stack),(KEY,KEY+2),(SHARED,SHARED+2)]
        for p,old in frozen:
            new=bytes(self.u.mem_read(p,len(old)))
            for offset in range(0,len(old),4096):
                a,b=old[offset:offset+4096],new[offset:offset+4096]
                if a!=b:
                    for i,(x,y) in enumerate(zip(a,b)):
                        if x!=y:assert any(lo<=p+offset+i<hi for lo,hi in allowed),f'other mapped byte changed {p+offset+i:08x}'
        assert self.u.reg_read(UC_ARM_REG_PC)==STOP,'instruction bound'
        assert self.u.reg_read(UC_ARM_REG_SP)==self.stack,'stack balance'
        assert [self.u.reg_read(r) for r in REGS]==seed,'callee-saved registers'
        assert self.u.reg_read(UC_ARM_REG_CPSR)&0xdf==cpsr,'CPSR controls changed'
        assert self.get(IME)==ime,'IME changed'
        self.metrics.append((address,self.stack-self.call_low,self.instructions-instruction_start))
        return self.u.reg_read(UC_ARM_REG_R0)
    def activate(self,owner=OWNER,mask=0xf03):return self.call('physical_activate',owner,mask)
    def consume(self,token=1,owner=OWNER,out=OUT):return self.call('physical_consume',owner,token,out)
    def sample(self):return struct.unpack('<IIHHHH',self.u.mem_read(OUT,16))
    def frame(self,held,closed=False):
        self.input(held,closed);self.call('physical_lid_action');self.call('physical_after_native_mapping');return self.consume()
    def release(self):assert self.frame(0)==1
    def slot(self):return bytes(self.u.mem_read(SLOT,48))
