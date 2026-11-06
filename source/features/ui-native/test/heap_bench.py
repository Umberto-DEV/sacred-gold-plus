"""Bounded checked-heap ARM harness. Synthetic addresses are not reservations."""
import importlib.util
from pathlib import Path
import struct
import subprocess
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_ARM, UC_HOOK_CODE, UC_HOOK_MEM_WRITE
from unicorn.arm_const import *
SOURCE=Path(__file__).resolve().parents[3]
CODE,STOP,TOKEN=0x02204000,0x02203f00,0x027e3000
META,BASE,PARENT=0x021d1584,0x0226f000,0x02280000
TEMPLATES=((0x02380000,0xd200),(0x0238d200,0x23600),(0x023b0800,0x10))
CREATE,ALLOC,FREE,DESTROY,DISABLE,RESTORE=0x020b535c,0x020b53a0,0x020b5530,0x020b5394,0x020d3a38,0x020d3a4c
STACK,IME=0x027e3778,0x04000208
REGS=[UC_ARM_REG_R4,UC_ARM_REG_R5,UC_ARM_REG_R6,UC_ARM_REG_R7,UC_ARM_REG_R8,UC_ARM_REG_R9,UC_ARM_REG_R10,UC_ARM_REG_R11]
FLAGS=['--target=armv5te-none-eabi','-mcpu=arm946e-s','-mthumb','-Oz','-ffreestanding','-fno-builtin','-fno-stack-protector','-fomit-frame-pointer','-fno-unwind-tables','-fno-asynchronous-unwind-tables','-Wall','-Wextra','-Werror']
def compile_heap(directory,mutation=None):
    source=SOURCE/'features/ui-native/heap.c'
    if mutation:
        old,new=mutation;content=source.read_text();assert old in content
        source=directory/'heap.c';source.write_text(content.replace(old,new,1))
    obj=directory/'heap.o'
    subprocess.run(['clang',*FLAGS,'-I',str(SOURCE/'features/ui-native'),'-fstack-usage','-c',str(source),'-o',str(obj)],check=True,capture_output=True)
    spec=importlib.util.spec_from_file_location('heap_loader',SOURCE/'features/options/tools/carica_text.py')
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    return mod.load_text(obj.read_bytes(),CODE)
class HeapBench:
    def __init__(self,compiled):
        self.code,self.symbols=compiled;self.u=Uc(UC_ARCH_ARM,UC_MODE_ARM)
        for p,n in ((0x02000000,0x400000),(0x027e0000,0x4000),(0x04000000,0x1000)):self.u.mem_map(p,n)
        self.u.mem_write(CODE,self.code);self.u.reg_write(UC_ARM_REG_CPSR,0x5f);self.put(IME,1)
        self.handles=BASE;self.parents=BASE+116;self.raws=BASE+228;self.counts=BASE+340;self.idxs=BASE+662
        self.u.mem_write(META,struct.pack('<5I4H',self.handles,self.parents,self.raws,self.counts,self.idxs,161,4,28,28))
        self.u.mem_write(self.idxs,bytes([28])*161)
        # Installed convention: every template ID keeps its matching slot,
        # including template2 whose 0x10 constructor result is NULL.
        for slot in range(4):self.put(self.idxs+slot,slot,1)
        for slot,(raw,size) in enumerate(TEMPLATES[:2]):
            self.header(raw,size);self.put(self.handles+4*slot,raw)
        self.put(self.handles+12,PARENT);self.header(PARENT,0x100000)
        self.calls=[];self.writes=[];self.store_contexts=[];self.allowed=[(BASE,BASE+824),(TOKEN,TOKEN+92),(PARENT,PARENT+0x100000),(0x021d84b0,0x021d84c0)]
        self.allowed.extend((raw,raw+size) for raw,size in TEMPLATES)
        self.instructions=0;self.low=STACK;self.metrics=[];self.fail=None;self.native=False
        self.native_metrics=[];self.active_service=None;self.adapter_entry=False
        self.u.hook_add(UC_HOOK_CODE,self.hook);self.u.hook_add(UC_HOOK_MEM_WRITE,self.store)
    def put(self,p,v,n=4):self.u.mem_write(p,int(v&((1<<(8*n))-1)).to_bytes(n,'little'))
    def get(self,p,n=4):return int.from_bytes(self.u.mem_read(p,n),'little')
    def header(self,p,n):
        self.put(p,0x45585048);self.put(p+0x18,p+0x38);self.put(p+0x1c,p+n)
    def token(self):return bytes(self.u.mem_read(TOKEN,92))
    def metadata(self):return bytes(self.u.mem_read(BASE,824))
    def ret(self,v=0):self.u.reg_write(UC_ARM_REG_R0,v);self.u.reg_write(UC_ARM_REG_PC,self.u.reg_read(UC_ARM_REG_LR))
    def store(self,u,access,p,n,v,data):
        self.store_contexts.append((p,n,v,u.reg_read(UC_ARM_REG_PC),u.reg_read(UC_ARM_REG_CPSR)))
        self.writes.append((p,n,v));assert any(a<=p<p+n<=b for a,b in self.allowed) or STACK-1024<=p<p+n<=STACK,f'unexpected store {p:08x}/{n}'
    def hook(self,u,p,n,data):
        self.instructions+=1;sp=u.reg_read(UC_ARM_REG_SP);self.low=min(self.low,sp)
        if self.active_service:
            a,ret,start,entry,low=self.active_service
            low=min(low,sp)
            if p==ret:
                self.native_metrics.append((a,self.instructions-start,entry-low))
                self.active_service=None
            else:self.active_service=(a,ret,start,entry,low)
        assert STACK-1024<=sp<=STACK,'stack budget'
        if p==STOP:u.emu_stop();return
        assert p not in (0x0202551c,0x02096338,0x0201a910,0x0201a91c,0x0201aa8c,0x0201aacc),f'forbidden GF assert/reset/unsafe allocator {p:08x}'
        if p in (CREATE,ALLOC,FREE,DESTROY,DISABLE,RESTORE):
            assert sp%8==0,'native boundary alignment'
            assert not u.reg_read(UC_ARM_REG_CPSR)&32,'native boundary must be ARM/even'
            if self.adapter_entry and p in (CREATE,ALLOC,FREE,DESTROY):
                assert u.reg_read(UC_ARM_REG_CPSR)&128,'NNS publication must be IRQ masked'
            args=tuple(u.reg_read(r) for r in (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2));self.calls.append((p,args))
            if self.fail==p:self.ret(0);return
            if self.native:
                self.active_service=(p,u.reg_read(UC_ARM_REG_LR)&~1,self.instructions,sp,sp)
                return
            r0,r1,r2=args
            if p==DISABLE:
                old=u.reg_read(UC_ARM_REG_CPSR);u.reg_write(UC_ARM_REG_CPSR,old|128);self.ret(old&128)
            elif p==RESTORE:
                old=u.reg_read(UC_ARM_REG_CPSR);u.reg_write(UC_ARM_REG_CPSR,(old&~128)|r0);self.ret()
            elif p==ALLOC:
                raw=PARENT+0x100 if r0==PARENT else r0+0x100+sum(1 for a,_ in self.calls if a==ALLOC)*0x100
                self.put(raw-16,0x5544,2);self.put(raw-12,(r1+3)&~3);self.ret(raw)
            elif p==CREATE:self.header(r0,r1);self.ret(r0)
            else:self.ret()
            return
        assert CODE<=p<CODE+len(self.code) or self.native and self.native_allowed(p),f'unexpected execution {p:08x}'
    def native_allowed(self,p):return 0x020b4b68<=p<0x020b556c or DISABLE<=p<RESTORE+0x18
    def call(self,name,*args):return self.address(self.symbols[name],*args)
    def address(self,p,*args):
        seed=[0x44440000+i for i in range(8)]
        for r,v in zip(REGS,seed):self.u.reg_write(r,v)
        for i,r in enumerate((UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3)):self.u.reg_write(r,args[i] if i<len(args) else 0)
        self.adapter_entry=CODE<=p<CODE+len(self.code)
        self.u.reg_write(UC_ARM_REG_SP,STACK);self.u.reg_write(UC_ARM_REG_LR,STOP|1)
        cpsr=self.u.reg_read(UC_ARM_REG_CPSR)&0xdf;ime=self.get(IME);start=self.instructions;self.low=STACK
        self.u.mem_write(STACK-1024,b'\xa5'*64)
        self.u.emu_start(p,STOP,count=1000000)
        if self.active_service and self.active_service[1]==STOP and self.u.reg_read(UC_ARM_REG_PC)==STOP:
            a,ret,start,entry,low=self.active_service
            self.native_metrics.append((a,self.instructions-start+1,entry-low));self.active_service=None
        assert self.u.reg_read(UC_ARM_REG_PC)==STOP,'finite instruction limit'
        assert self.u.reg_read(UC_ARM_REG_SP)==STACK,'SP balance'
        assert [self.u.reg_read(r) for r in REGS]==seed,'callee-saved registers'
        assert self.u.reg_read(UC_ARM_REG_CPSR)&0xdf==cpsr,'IRQ/CPSR restore'
        assert self.get(IME)==ime,'IME preservation'
        assert bytes(self.u.mem_read(STACK-1024,64))==b'\xa5'*64,'DTCM canary'
        self.metrics.append((p,STACK-self.low,self.instructions-start))
        return self.u.reg_read(UC_ARM_REG_R0)
    def create(self,n=0x30000,g=1):return self.call('ui_heap38_create',TOKEN,n,g)
    def alloc(self,n,tail=0):return self.call('ui_alloc38',TOKEN,n,tail)
    def free(self,p):return self.call('ui_free38',TOKEN,p)
    def destroy(self):return self.call('ui_heap38_destroy',TOKEN)

def build_receipt(directory):
    """Small reproducible report; no ROM bytes or compiled artifacts retained."""
    import hashlib
    code,symbols=compile_heap(directory);obj=(directory/'heap.o').read_bytes()
    header=struct.unpack_from('<HHIIIIIHHHHHH',obj,16)
    sections=[struct.unpack_from('<10I',obj,header[5]+i*header[10]) for i in range(header[11])]
    def contents(s):return obj[s[4]:s[4]+s[5]]
    names=contents(sections[header[12]])
    def name(table,index):return table[index:table.index(b'\0',index)].decode()
    labels=[name(names,s[0]) for s in sections];ti=labels.index('.text')
    markers=[];undefined=[];relocations={}
    for s in sections:
        if s[1]==2:
            strings=contents(sections[s[6]])
            for index,value,size,info,other,si in struct.iter_unpack('<IIIBBH',contents(s)):
                label=name(strings,index)
                if si==ti and label.startswith(('$d','$t')):markers.append((value&~1,label[:2]))
                if label and not si and info&0xf0:undefined.append(label)
        if s[1]==9 and s[7]==ti:
            for offset,info in struct.iter_unpack('<II',contents(s)):relocations[info&255]=relocations.get(info&255,0)+1
    literal=0;markers.sort()
    for j,(start,kind) in enumerate(markers):
        end=markers[j+1][0] if j+1<len(markers) else len(code)
        if kind=='$d':literal+=end-start
    return {'compiler':subprocess.check_output(['clang','--version'],text=True).strip(),
            'object_sha256':hashlib.sha256(obj).hexdigest(),'payload_sha256':hashlib.sha256(code).hexdigest(),
            'payload_bytes':len(code),'literal_and_padding_bytes':literal,'instruction_region_bytes':len(code)-literal,
            'undefined':undefined,'relocations':relocations,'stack_usage':(directory/'heap.su').read_text().strip()}
if __name__=='__main__':
    import json,tempfile
    with tempfile.TemporaryDirectory(prefix='heap-receipt-') as d:print(json.dumps(build_receipt(Path(d)),indent=2))
