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
# Where the bench hands out the native 1948-byte Bag array. It is a bench
# constant, not the game's: in a real save the array starts at SaveBlock+0x654.
# Only the extension code's view of it matters, and that comes from CALL_ARRAY.
NATIVE=SAVE+0xD634
S=0x023DD700
RECORD_BYTES=452          # sizeof(CapRecord)
CHUNK_BYTES=32            # verify_copy's stack buffer: it reads back in chunks
READBACK_READS=-(-RECORD_BYTES//CHUNK_BYTES)   # ceil(452/32) = 15 reads per copy
OWNERSHIP_READS=2         # one per destination, before anything is written
# CapState field addresses, as the shipped manifest and the lab tools read them.
S_MAGIC=S+0x0000
S_SAVE=S+0x0004
S_NATIVE=S+0x0008
S_REJECTED=S+0x000C
S_OWNED=S+0x0010
S_BAG=S+0x0014
S_SNAPSHOT=S+0x0960
S_RECORD=S+0x10FC
S_STATO_CARICAMENTO=S+0x12C0
S_STATO_SCRITTURA=S+0x12C4
STOP=0x023AF000
REGS=(UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3)
class Bench:
    def __init__(self,rom,build):
        self.mu=Uc(UC_ARCH_ARM,UC_MODE_THUMB);self.mu.mem_map(BASE,0x400000)
        arm=Arm9(rom)
        for base,off,size in arm.segmenti:
            if BASE<=base and base+size<=BASE+0x400000:self.mu.mem_write(base,bytes(arm.raw[off:off+size]))
        self.mu.mem_write(STOP,b'\x00\xbe')
        manifest=json.loads((Path(build)/'manifesto.json').read_text())
        self.symbols={n:int(a,16) for n,a in manifest['simboli'].items()}
        # The ROM under test must carry exactly the build under test: otherwise
        # these tests would certify code that is not the one being shipped.
        blob=(Path(build)/'blob.bin').read_bytes()
        if arm.leggi(int(manifest['base'],16),len(blob))!=blob:
            raise AssertionError('la ROM non contiene il blob di %s'%build)
        self.flash=bytearray(b'\xff'*0x80000);self.pockets={};self.heap=0x02240000
        self.read_fail=False;self.reads=0;self.fail_on_read=0;self.write_cut=None;self.writes=[];self.original_saves=0;self.errors=0
        # read_filter(index,address,size,data)->data: a flash that hands back
        # bytes other than the ones just written, without failing the read.
        self.read_filter=None
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
            if not fail:
                data=bytes(self.flash[a[0]:a[0]+a[2]])
                if self.read_filter:data=self.read_filter(self.reads,a[0],a[2],data)
                uc.mem_write(a[1],data)
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
