"""Execute the real patched ARM9 Bag APIs, substituting only OS/flash services."""
import json,struct,zlib
from pathlib import Path
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_THUMB,UC_HOOK_CODE
from unicorn.arm_const import *
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from sgp12.rom import Arm9
BASE=0x02000000
SAVE=0x02200000
NATIVE=SAVE+0xD634
S=0x023DD700
STOP=0x023AF000
REGS=(UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3)
class Bench:
    def __init__(self,rom,build):
        self.mu=Uc(UC_ARCH_ARM,UC_MODE_THUMB);self.mu.mem_map(BASE,0x400000)
        arm=Arm9(rom)
        for base,off,size in arm.segmenti:
            if BASE<=base and base+size<=BASE+0x400000:self.mu.mem_write(base,bytes(arm.raw[off:off+size]))
        self.mu.mem_write(STOP,b'\x00\xbe')
        self.symbols={n:int(a,16) for n,a in json.loads((Path(build)/'manifesto.json').read_text())['simboli'].items()}
        self.flash=bytearray(b'\xff'*0x80000);self.pockets={};self.heap=0x02240000
        self.read_fail=False;self.reads=0;self.fail_on_read=0;self.write_cut=None;self.writes=[];self.original_saves=0;self.errors=0
        self.store(SAVE+4,1);self.store(SAVE+8,0);self.store(SAVE+0x23010,1)
        self.store(SAVE+0x232B8,0);self.store(SAVE+0x232BC,0x10000)
        self.mu.mem_write(SAVE+0x2330A,b'\0\0')
        for addr in [0x020272C8,0x02077D88,0x0201AA8C,0x0202877C,0x02028758,0x0201FF98,0x0209263C,self.symbols['sgp_cap_original_save']&~1]:
            self.mu.hook_add(UC_HOOK_CODE,self.hook,begin=addr,end=addr)
    def store(self,a,v):self.mu.mem_write(a,struct.pack('<I',v))
    def read32(self,a):return struct.unpack('<I',self.mu.mem_read(a,4))[0]
    def return_(self,v):self.mu.reg_write(UC_ARM_REG_R0,v);self.mu.reg_write(UC_ARM_REG_PC,self.mu.reg_read(UC_ARM_REG_LR))
    def hook(self,uc,address,size,user):
        a=[uc.reg_read(r) for r in REGS]
        if address==STOP:uc.emu_stop()
        elif address==0x020272C8:self.return_(NATIVE)
        elif address==0x02077D88:
            assert a[1]==5,('wrong fieldPocket attribute',a)
            self.return_(self.pockets.get(a[0],0))
        elif address==0x0201AA8C:
            out=self.heap;self.heap+=(a[1]+7)&~7;self.return_(out)
        elif address==0x0202877C:
            self.reads+=1;fail=self.read_fail or self.reads==self.fail_on_read
            if not fail:uc.mem_write(a[1],bytes(self.flash[a[0]:a[0]+a[2]]))
            self.return_(not fail)
        elif address==0x02028758:
            raw=bytes(uc.mem_read(a[1],a[2]));n=len(raw) if self.write_cut is None else (self.write_cut.pop(0) if isinstance(self.write_cut,list) else self.write_cut)
            self.flash[a[0]:a[0]+n]=raw[:n];self.writes.append((a[0],n));self.return_(n==len(raw))
        elif address==0x0201FF98:self.return_(zlib.crc32(bytes(uc.mem_read(a[0],a[1])))&65535)
        elif address==(self.symbols['sgp_cap_original_save']&~1):self.original_saves+=1;self.return_(2)
        elif address==0x0209263C:self.errors+=1;uc.emu_stop()
    def call(self,a,*args):
        if isinstance(a,str):a=self.symbols[a]
        sp=0x023B0000
        for i,x in enumerate(args):
            if i<4:self.mu.reg_write(REGS[i],x)
            else:self.store(sp+(i-4)*4,x)
        self.mu.reg_write(UC_ARM_REG_SP,sp);self.mu.reg_write(UC_ARM_REG_LR,STOP|1)
        self.mu.emu_start(a|1,STOP,count=3000000)
        if self.errors:raise RuntimeError('native save read error')
        if self.mu.reg_read(UC_ARM_REG_PC)!=STOP:raise RuntimeError('ARM did not return')
        assert self.mu.reg_read(UC_ARM_REG_SP)==sp,'stack not preserved'
        return self.mu.reg_read(UC_ARM_REG_R0)
    def bag(self):return self.call('sgp_cap_get',SAVE)
    def slot(self,bag,p,n):
        a=self.call('sgp_cap_slot',bag,p,n)
        return None if not a else struct.unpack('<HH',self.mu.mem_read(a,4))
