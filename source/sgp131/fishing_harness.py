"""Small actual-ARM harness: hooks only external clock/data/RNG functions."""
import struct
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB, UC_HOOK_CODE
from unicorn.arm_const import *

BASES = {2: 0x02245B80, 101: 0x021E7740}
RET, DATA, SLOTS, FS, LOC, SP = 0x02001000, 0x02300000, 0x02301000, 0x02302000, 0x02302100, 0x023F0000
REGS = (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3)
SAVED = (UC_ARM_REG_R4, UC_ARM_REG_R5, UC_ARM_REG_R6, UC_ARM_REG_R7, UC_ARM_REG_R8, UC_ARM_REG_R9, UC_ARM_REG_R10, UC_ARM_REG_R11)

def species(record, rod):
    return [struct.unpack_from('<H',record,(0x80,0x94,0xa8)[rod]+4*i+2)[0] for i in range(5)]

class Arm:
    def __init__(self, images):
        self.cpu=Uc(UC_ARCH_ARM,UC_MODE_THUMB)
        self.cpu.mem_map(0x02000000,0x400000)
        for ov,image in images.items(): self.cpu.mem_write(BASES[ov],image)
        self.cpu.mem_write(FS+0x20,struct.pack('<I',LOC))
        self.cpu.mem_write(FS+0xc,struct.pack('<I',0x02302200))
        self.state={'time':3,'swarm':False,'has_enc':True,'random':3,'record':bytes(196)}
        self.calls=[]
        self.cpu.hook_add(UC_HOOK_CODE,self.hook)
    def hook(self,u,a,size,user):
        if a==RET: u.emu_stop(); return
        values={0x0201481C:self.state['time'],0x0202D9C4:0x02302200,0x0202D9E0:int(self.state['swarm']),0x0202D9A8:0,0x02097F6C:int(self.state['swarm']),0x0203B324:int(self.state['has_enc']),0x0201FD44:self.state['random']}
        if a==0x0203B88C:
            self.calls.append(a)
            u.mem_write(u.reg_read(UC_ARM_REG_R0),self.state['record'])
        elif a==0x020F2998:
            self.calls.append(a)
            n,d=u.reg_read(UC_ARM_REG_R0),u.reg_read(UC_ARM_REG_R1)
            u.reg_write(UC_ARM_REG_R0,n//d);u.reg_write(UC_ARM_REG_R1,n%d)
        elif a in values:
            self.calls.append(a);u.reg_write(UC_ARM_REG_R0,values[a])
        else:return
        u.reg_write(UC_ARM_REG_PC,u.reg_read(UC_ARM_REG_LR))
    def call(self,addr,args):
        self.calls.clear()
        for i,r in enumerate(SAVED):self.cpu.reg_write(r,0xABCD0000+i)
        for r,v in zip(REGS,args):self.cpu.reg_write(r,v)
        self.cpu.reg_write(UC_ARM_REG_SP,SP);self.cpu.reg_write(UC_ARM_REG_LR,RET|1)
        self.cpu.emu_start(addr|1,RET,count=5000)
        assert self.cpu.reg_read(UC_ARM_REG_PC)==RET
        assert self.cpu.reg_read(UC_ARM_REG_SP)==SP
        assert [self.cpu.reg_read(r)for r in SAVED]==[0xABCD0000+i for i in range(len(SAVED))]
        return self.cpu.reg_read(UC_ARM_REG_R0)
    def battle(self,record,rod,time,swarm=False):
        self.state.update(time=time,swarm=swarm)
        self.cpu.mem_write(DATA,record.ljust(196,b'\0'))
        slots=b''.join(struct.pack('<IHH',s,31+i,21+i)for i,s in enumerate(species(record,rod)))
        self.cpu.mem_write(SLOTS-16,b'\xa5'*16+slots+b'\x5a'*16)
        self.call(0x02246AD4,[DATA,rod,SLOTS])
        self.call(0x02246BD8,[FS,rod,DATA,SLOTS])
        actual=bytes(self.cpu.mem_read(SLOTS,40))
        assert bytes(self.cpu.mem_read(SLOTS-16,16))==b'\xa5'*16
        assert bytes(self.cpu.mem_read(SLOTS+40,16))==b'\x5a'*16
        assert all(actual[i*8+4:i*8+8]==slots[i*8+4:i*8+8]for i in range(5))
        return [struct.unpack_from('<I',actual,i*8)[0]for i in range(5)]
    def phone(self,record,trainer=11,time=2,slot=3,has_enc=True):
        self.state.update(record=record.ljust(196,b'\0'),random=slot,has_enc=has_enc)
        return self.call(0x021F2E04,[60,trainer,time])
