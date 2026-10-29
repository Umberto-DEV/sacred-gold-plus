"""Synthetic machine bench: actual candidate ARM9, private ROM assets, OS/flash seams."""
from pathlib import Path
import json,struct,sys
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_THUMB,UC_HOOK_CODE
from unicorn.arm_const import *
sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from sgp12.rom import Arm9,Rom
import ndspy.rom,ndspy.narc
BASE=0x02000000;STOP=0x023EF000;STACK=0x023FF000;MON=0x022C0000;SAVE=0x02290000;ARGS=0x022C2000
REGS=(UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3)
class Bench:
 def __init__(self,path,report):
  self.mu=Uc(UC_ARCH_ARM,UC_MODE_THUMB);self.mu.mem_map(0x01FF0000,0x410000);self.arm=Arm9(path)
  for base,off,size in self.arm.segmenti:
   if 0x01FF0000<=base and base+size<=0x02400000:self.mu.mem_write(base,bytes(self.arm.raw[off:off+size]))
  self.symbols=json.loads(Path(report).read_text())['symbols'];self.mu.mem_write(STOP,b'\0\xbe')
  self.rom=ndspy.rom.NintendoDSRom(bytes(self.arm.raw));self.archives={}
  self.heap=0x02300000;self.flash=bytearray(b'\xff'*0x80000);self.writes=[];self.cut=None;self.fail_address=None;self.native_saves=0;self.charges=[];self.pay_ok=True;self.assertions=0;self.league=None;self.rtc_now=None;self.phone_buffers=None;self.phone_messages=[]
  self.mu.hook_add(UC_HOOK_CODE,self.hook)
 def u32(self,p):return struct.unpack('<I',self.mu.mem_read(p,4))[0]
 def put(self,p,value):self.mu.mem_write(p,struct.pack('<I',value))
 def ret(self,value=0):self.mu.reg_write(UC_ARM_REG_R0,value&0xffffffff);self.mu.reg_write(UC_ARM_REG_PC,self.mu.reg_read(UC_ARM_REG_LR))
 def alloc(self,n):p=self.heap;self.heap=(p+n+7)&~7;assert self.heap<0x023B0000;self.mu.mem_write(p,bytes(n));return p
 def member(self,narc,member):
  names={2:'a/0/0/2',3:'a/0/0/3',17:'a/0/1/7'}
  if narc not in self.archives:self.archives[narc]=ndspy.narc.NARC(self.rom.getFileByName(names[narc]))
  return bytes(self.archives[narc].files[member])
 def hook(self,uc,address,size,user):
  a,b,c,d=[uc.reg_read(r)for r in REGS]
  if address in (0x0201AA8C,0x0201AACC):self.ret(self.alloc(b))
  elif address==0x0201AB0C:self.ret()
  elif address==0x02007508:self.mu.mem_write(a,self.member(b,c));self.ret()
  elif address in (0x02007524,0x02007544):
   blob=self.member(a,b);p=self.alloc(len(blob));self.mu.mem_write(p,blob);self.ret(p)
  elif address==0x0200757C:
   length=self.u32(uc.reg_read(UC_ARM_REG_SP));blob=b''.join(x+b'\xff'*((-len(x))%4)for x in self.archives.get(a,ndspy.narc.NARC(self.rom.getFileByName('a/0/1/7'))).files)
   p=self.alloc(length);assert d+length<=len(blob);self.mu.mem_write(p,blob[d:d+length]);self.ret(p)
  elif address==0x0202551C:self.assertions+=1;self.ret() # release ROM assertion handler returns when fatal-error mode is off
  elif address==0x0201FF98:
   from sgp12.rom import crc16
   self.ret(crc16(bytes(uc.mem_read(a,b))))
  elif address==0x0202877C:
   if self.fail_address==a:self.ret(0)
   else:self.mu.mem_write(b,bytes(self.flash[a:a+c]));self.ret(1)
  elif address==0x02028758:
   data=bytes(self.mu.mem_read(b,c));self.writes.append((a,data));n=c if self.cut is None else min(c,self.cut)
   self.flash[a:a+n]=data[:n];self.ret(n==c)
  elif address==0x02040374:
   self.ret(ARGS+0x1000+(b-0x8000)*2 if 0x8000<=b<=0x800C else ARGS+0x1040)
  elif address==0x0202D18C and self.league is not None:self.ret(self.league)
  elif address==0x020147DC and self.rtc_now is not None:
   self.mu.reg_write(UC_ARM_REG_R1,self.rtc_now>>32);self.ret(self.rtc_now&0xffffffff)
  elif address in (0x0200BFCC,0x0200C1D4) and self.phone_buffers is not None:
   self.phone_buffers.append((address,a,b,c,d));self.ret()
  elif address==0x021F2208:self.phone_messages.append((a,b,c));self.ret()
  elif address==0x0200BF8C:self.ret()
  elif address==0x023DCA98:self.ret(1)
  elif address==0x020272C8:self.ret(SAVE+0x1000+b*0x2000)
  elif address==self.symbols['training_native_save']&~1:self.native_saves+=1;self.ret(2)
  elif address==0x023EEC00:self.charges.append((b,c));self.ret(int(self.pay_ok))
 def call(self,address,*args):
  for i,reg in enumerate(REGS):self.mu.reg_write(reg,args[i] if i<len(args) else 0)
  self.mu.reg_write(UC_ARM_REG_SP,STACK);self.mu.reg_write(UC_ARM_REG_LR,STOP|1)
  for i,a in enumerate(args[4:]):self.put(STACK+i*4,a)
  self.mu.emu_start(address|1,STOP,count=2000000)
  if self.mu.reg_read(UC_ARM_REG_PC)!=STOP:raise AssertionError('instruction budget '+hex(self.mu.reg_read(UC_ARM_REG_PC)))
  if self.mu.reg_read(UC_ARM_REG_SP)!=STACK:raise AssertionError('stack imbalance')
  return self.mu.reg_read(UC_ARM_REG_R0)
 def get(self,field):return self.call(0x0206E540,MON,field,0)
 def set(self,field,value):self.put(ARGS,value);self.call(0x0206EC40,MON,field,ARGS)
 def make_mon(self,species=25,level=50):
  self.call(0x0206DCE4,MON)
  self.set(0,12345);self.set(7,87654);self.set(5,species);exp=self.call(0x0206FD00,species,level);self.set(8,exp)
  for i in range(6):self.set(70+i,10)
  self.call(0x0206E250,MON)

 def activate(self,policy=2):
  s=0x023D3000;self.put(s,0x31544e52);self.put(s+4,SAVE);self.put(s+8,1);self.put(s+12,1)
  self.call(self.symbols['sgp_train_defaults'],s+32);self.mu.mem_write(s+40,bytes([policy,0]))
 def service(self,op,slot=0,arg=0,value=0,kind=0):
  ctx=ARGS+0x2000;fs=ARGS+0x2100;pc=ARGS+0x2200
  self.put(ctx+8,pc);self.put(ctx+0x80,fs);self.put(fs+12,SAVE);self.mu.mem_write(pc,b'\x3a\xf1')
  self.mu.mem_write(ARGS+0x100c,struct.pack('<5H',op,slot,arg,value,kind))
  self.call(self.symbols['training_script'],ctx)
  return struct.unpack('<H',self.mu.mem_read(ARGS+0x1016,2))[0]
