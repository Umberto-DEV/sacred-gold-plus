"""Compiled resident unit. Synthetic addresses are NOT reservations.
Class A seams lower native services; Class B executes their actual bodies.
"""
import hashlib,importlib.util,struct,subprocess,sys,zlib
import ndspy.codeCompression
from capstone import Cs,CS_ARCH_ARM,CS_MODE_ARM,CS_MODE_THUMB,CS_OP_IMM
from pathlib import Path
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM,UC_HOOK_CODE,UC_HOOK_MEM_WRITE,UC_HOOK_MEM_READ
from unicorn.arm_const import *
from heap_bench import SOURCE,FLAGS,REGS,STACK,IME
sys.path.insert(0,str(SOURCE))
from sgp12.blz import ndspy_decomprimi_sicuro
CODE,STOP,STATE,CONFIG=0x023e1000,0x023e0f00,0x02370000,0x02373000
IMAGE,REGISTRY,ARC,FAT,FNT,TABLE=0x021e5900,0x021d0df0,0x021e3654,0x02270000,0x02271008,0x02274000
INFO,LOAD,UNLOAD,CPSR=0x020d88c0,0x02006ff8,0x02006f7c,0x020d3a90
SIZE=4624
REFUSED,MORE,READY,FAILED,RELEASED,HOLD=range(6)
ZERO,META_OPEN,META_INVALIDATE,META_READ,META_WAIT,META_CLOSE,META_VERIFY,RESERVE,IMAGE_OPEN,IMAGE_CLEAR,IMAGE_READ,IMAGE_WAIT,IMAGE_CLOSE,PACKED_VERIFY,START,DECODED_VERIFY,WIFI,ACTIVE,ABORT_DRAIN,ABORT_CLOSE,ABORT_END,RELEASE_END,ABORT_UNRESERVE,RELEASE_UNRESERVE,FAILURE,RETIRED,HELD=range(27)
INITFILE,DIRECT,FAST,CLOSE,READ,CLEAR,STARTFN,END,WIFIFN,INVALIDATE,DISABLE,RESTORE=(0x20d7f98,0x20d81c0,0x20d8208,0x20d82c0,0x20d83bc,0x20d8764,0x20d8b6c,0x20d8d50,0x23da3cc,0x20d285c,0x20d3a38,0x20d3a4c)
LOWER=(INITFILE,DIRECT,FAST,CLOSE,READ,CLEAR,STARTFN,END,WIFIFN,INVALIDATE)
def compile_module(directory,mutation=None,extra=""):

    content=(SOURCE/'features/ui-native/module.c').read_text()
    if mutation:
        old,new=mutation;assert old in content;content=content.replace(old,new,1)
    src=directory/'module.c';obj=directory/'module.o';src.write_text(content+extra)
    subprocess.run(['clang',*FLAGS,'-fno-jump-tables','-I',str(SOURCE/'features/ui-native'),'-fstack-usage','-c',str(src),'-o',str(obj)],check=True,capture_output=True)
    spec=importlib.util.spec_from_file_location('module_loader',SOURCE/'features/options/tools/carica_text.py')
    loader=importlib.util.module_from_spec(spec);spec.loader.exec_module(loader)
    return loader.load_text(obj.read_bytes(),CODE)
def image_bytes(size=0x8000):
    # Authored Thumb probes: Init/Main return1; Exit returns1 on its second call.
    # No instructions/assets from a retail image.
    result=bytearray([0x5a])*size
    result[:4]=bytes.fromhex('01207047');result[4:8]=bytes.fromhex('01207047')
    result[8:28]=bytes.fromhex('0868 0130 0860 0228 01d2 0020 7047 0120 7047 0000')
    return bytes(result)
def packed_bytes(raw):
    encoded=ndspy.codeCompression.compress(raw)
    assert len(encoded)<=len(raw) and ndspy_decomprimi_sicuro(encoded,len(raw))==raw
    return encoded
def config_bytes(raw,role=1,generation=1,table=None,y9_offset=0x10020000):
    packed=packed_bytes(raw)
    return struct.pack('<24I',0x314d4955,2,role,generation,54,54,IMAGE,len(raw),0,IMAGE+len(raw),IMAGE+len(raw),0x01000000|len(packed),zlib.crc32(raw),1,5,9,zlib.crc32(packed),zlib.crc32(table or bytes(4128)),y9_offset,4128,0x10030000,0x10000000,0x10000000+len(packed),129)
def instruction_set(u,roots,regions):
    """Recursive actual-byte instruction graph. Literal pools are not roots.
    Conditional exits retain fallthrough; indirect calls use explicit roots.
    This is a test fetch allowlist, not proof about arbitrary code corruption.
    """
    decoders={0:Cs(CS_ARCH_ARM,CS_MODE_ARM),1:Cs(CS_ARCH_ARM,CS_MODE_THUMB)}
    for decoder in decoders.values():decoder.detail=True
    todo=list(roots);seen=set();allowed=set()
    while todo:
        address=todo.pop();mode=address&1;p=address&~1
        if (p,mode) in seen or not any(a<=p<b for a,b in regions):continue
        seen.add((p,mode));ins=next(decoders[mode].disasm(bytes(u.mem_read(p,4)),p),None)
        if ins is None:continue
        allowed.add(p);mn=ins.mnemonic;ops=ins.operands;fall=True
        if mn.startswith('bl') and mn not in ('bls','blt','ble','blo'):
            if ops and ops[0].type==CS_OP_IMM:todo.append(ops[0].imm|(0 if mn.startswith('blx') and mode else mode))
        elif mn.startswith('b') and mn not in ('bic','bics','bkpt'):
            if ops and ops[0].type==CS_OP_IMM:todo.append(ops[0].imm|mode)
            if mn in ('b','bx'):fall=False
        if 'pc' in ins.op_str and (mn.startswith('pop') or mn.startswith('ldm')):
            if mn in ('pop','ldm','ldmia','ldmdb'):fall=False
        if mn=='ldr' and ins.op_str.startswith('pc, [pc,'):
            target=int.from_bytes(u.mem_read(p+8+ops[1].mem.disp,4),'little')
            todo.append(target);fall=False
        if mn in ('mov','add') and ins.op_str.startswith('pc,'):fall=False
        if fall:todo.append((p+ins.size)|mode)
    return allowed

class ModuleBench:
    def __init__(self,compiled,size=0x8000):
        self.state_address=STATE;self.code,self.symbols=compiled;self.u=Uc(UC_ARCH_ARM,UC_MODE_ARM)
        for p,n in ((0x02000000,0x400000),(0x027e0000,0x4000),(0x027ff000,0x1000),(0x04000000,0x1000)):self.u.mem_map(p,n)
        self.u.mem_write(CODE,self.code);self.compiled_fetch=instruction_set(self.u,[v for k,v in self.symbols.items() if not k.startswith("$")],[(CODE,CODE+len(self.code))]);self.u.reg_write(UC_ARM_REG_CPSR,0x5f);self.put(IME,1)
        self.raw=image_bytes(size);self.encoded=packed_bytes(self.raw);self.u.mem_write(CONFIG,config_bytes(self.raw));self.u.mem_write(STATE,bytes(SIZE))
        self.allow_disabled_seam=False;self.mask_run=0;self.max_mask_run=0;self.calls=[];self.writes=[];self.metrics=[];self.phase_metrics=[];self.mask_intervals=[];self.mask_start=None;self.instructions=0;self.low=STACK;self.native=False;self.loaded=False;self.fault=None;self.visited=set()
        self.allowed=[(STATE,STATE+SIZE),(REGISTRY,REGISTRY+192),(ARC,ARC+92),(IMAGE,IMAGE+len(self.raw)),(STACK-3072,STACK)]
        self.put(0x021e3638,1);self.put(ARC,0x6d6f72);self.put(ARC+0x1c,7)
        for off,value in ((0x2c,FAT),(0x30,4104),(0x34,FNT),(0x38,2902),(0x44,FAT),(0x48,0x020d84c4),(0x4c,0x020d850c),(0x50,0x020d7484),(0x54,0x020d8514),(0x58,0x602)):self.put(ARC+off,value)
        self.put(0x021e3644,TABLE);self.put(0x021e3648,129*32)
        self.put(0x027ffe50,0x10020000);self.put(0x027ffe54,129*32)
        for i in range(129):
            self.u.mem_write(TABLE+i*32,struct.pack('<8I',i,0x02200000+i*32,32,0,0,0,i,0))
            self.put(FAT+8*i,0x100000+i*0x10000);self.put(FAT+8*i+4,0x100000+i*0x10000+32)
        self.metadata();self.bind_config()
        self.delay=False;self.pending=None;self.close_failures=0;self.open_failure=False;self.partial=False;self.read_error=0
        self.u.mem_write(IMAGE,b'\xa5'*size)
        self.u.mem_write(STATE-16,b'\x96'*16);self.u.mem_write(STATE+SIZE,b'\x69'*16)
        self.u.hook_add(UC_HOOK_CODE,self.hook);self.u.hook_add(UC_HOOK_MEM_WRITE,self.store)
        self.u.hook_add(UC_HOOK_MEM_READ,self.read,begin=0x04000000,end=0x04000fff)
    def metadata(self):
        self.u.mem_write(TABLE+54*32,struct.pack('<8I',54,IMAGE,len(self.raw),0,IMAGE+len(self.raw),IMAGE+len(self.raw),54,0x01000000|len(self.encoded)))
        self.put(FAT+54*8,0x10000000);self.put(FAT+54*8+4,0x10000000+len(self.encoded))
    def bind_config(self,role=1,generation=1):
        self.table_rom=bytes(self.u.mem_read(TABLE,4128))
        self.u.mem_write(CONFIG,config_bytes(self.raw,role,generation,self.table_rom,self.get(0x027ffe50)))
    @property
    def file(self):return self.state_address+192
    @property
    def table(self):return (self.state_address+464+31)&~31
    @property
    def phase(self):return self.get(self.state_address+8)
    def poison_stack(self):self.u.mem_write(STACK-3000,b'\xd3'*3000)
    def complete(self,error=None):
        assert self.pending is not None
        f,dst,data=self.pending;self.pending=None
        self.u.mem_write(dst,data)
        self.put(f,0);self.put(f+4,0);self.put(f+12,16);self.put(f+20,self.read_error if error is None else error)
        self.put(ARC+0x24,0);self.put(ARC+0x1c,7)
    def drive(self,limit=256,role=1,generation=1):
        for _ in range(limit):
            r=self.step(role,generation)
            if r!=MORE:return r
        raise AssertionError('phase did not finish: '+str(self.phase))
    def put(self,p,v,n=4):self.u.mem_write(p,int(v&((1<<(8*n))-1)).to_bytes(n,'little'))
    def get(self,p,n=4):return int.from_bytes(self.u.mem_read(p,n),'little')
    def ret(self,v=0):self.u.reg_write(UC_ARM_REG_R0,v);self.u.reg_write(UC_ARM_REG_PC,self.u.reg_read(UC_ARM_REG_LR))
    def state(self):return bytes(self.u.mem_read(self.state_address,SIZE))
    def read(self,u,a,p,n,v,d):assert IME<=p<p+n<=IME+4,f'MMIO read {p:08x}'
    def store(self,u,a,p,n,v,d):
        self.writes.append((p,n,v,u.reg_read(UC_ARM_REG_PC)))
        if REGISTRY<=p<p+n<=REGISTRY+64 and CODE<=u.reg_read(UC_ARM_REG_PC)<CODE+len(self.code):assert u.reg_read(UC_ARM_REG_CPSR)&128,'registry transaction unmasked'
        assert any(lo<=p<p+n<=hi for lo,hi in self.allowed),f'unknown write {p:08x}/{n}'
        if CODE<=u.reg_read(UC_ARM_REG_PC)<CODE+len(self.code):assert self.state_address<=p<p+n<=self.state_address+SIZE or REGISTRY<=p<p+n<=REGISTRY+64 or STACK-3072<=p<p+n<=STACK,f'module store {p:08x}'
    def measure_irq(self):
        masked=bool(self.u.reg_read(UC_ARM_REG_CPSR)&128)
        if masked and self.mask_start is None:self.mask_start=(self.instructions,self.u.reg_read(UC_ARM_REG_PC))
        if not masked and self.mask_start is not None:
            self.mask_intervals.append((*self.mask_start,self.instructions-self.mask_start[0],self.u.reg_read(UC_ARM_REG_PC)));self.mask_start=None
        self.mask_run=self.mask_run+1 if self.u.reg_read(UC_ARM_REG_CPSR)&128 else 0
        self.max_mask_run=max(self.max_mask_run,self.mask_run)
    def hook(self,u,p,n,d):
        self.measure_irq();self.instructions+=1;self.visited.add(p);self.low=min(self.low,u.reg_read(UC_ARM_REG_SP))
        assert STACK-3072<=u.reg_read(UC_ARM_REG_SP)<=STACK,'stack bound'
        if p==STOP:u.emu_stop();return
        if p==CPSR:self.ret(u.reg_read(UC_ARM_REG_CPSR)&128);return
        if p==DISABLE:
            old=u.reg_read(UC_ARM_REG_CPSR)&128;u.reg_write(UC_ARM_REG_CPSR,u.reg_read(UC_ARM_REG_CPSR)|128);self.ret(old);return
        if p==RESTORE:
            u.reg_write(UC_ARM_REG_CPSR,(u.reg_read(UC_ARM_REG_CPSR)&~128)|(u.reg_read(UC_ARM_REG_R0)&128));self.ret();return
        if p in LOWER:
            assert u.reg_read(UC_ARM_REG_SP)%8==0,'native boundary alignment'
            assert self.get(IME)==1 and not u.reg_read(UC_ARM_REG_CPSR)&128
            a,b,c,d=[u.reg_read(r) for r in (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3)]
            self.calls.append((p,a,b,c));f=a
            if p==INITFILE:
                assert f==self.file and self.get(f+8)==0
                for off in (0,4,8,12,20,24,28):self.put(f+off,0)
                self.put(f+16,14);self.ret()
            elif p in (DIRECT,FAST):
                assert f==self.file and b==ARC and not self.get(f+8)
                self.put(f+8,ARC)
                if self.open_failure:self.put(f+20,3);self.ret(0);return
                top,bottom,idx=(c,d,self.get(u.reg_read(UC_ARM_REG_SP))) if p==DIRECT else (self.get(FAT+8*c),self.get(FAT+8*c+4),c)
                for off,val in ((12,16),(16,7 if p==DIRECT else 6),(20,0),(32,idx),(36,top),(40,bottom),(44,top)):self.put(f+off,val)
                self.ret(1)
            elif p==READ:
                assert f==self.file and self.get(f+8)==ARC and self.pending is None
                raw=self.table_rom if b==self.table else self.encoded
                assert c==len(raw) and b in (self.table,IMAGE)
                data=raw[:-4] if self.partial else raw
                for off,val in ((0,ARC+32),(12,0x59),(16,0),(20,2),(44,self.get(f+36)+c),(48,b),(52,c),(56,c)):self.put(f+off,val)
                self.put(ARC+36,f);self.put(ARC+28,0x117);self.pending=(f,b,data)
                if not self.delay:self.complete()
                self.ret(c)
            elif p==CLOSE:
                assert f==self.file and self.get(f+8)==ARC and self.pending is None
                if self.close_failures:
                    self.close_failures-=1;self.put(f+20,3);self.ret(0);return
                for off in (8,12,20):self.put(f+off,0)
                self.put(f+16,14);self.ret(1)
            elif p==INVALIDATE:
                assert a==self.table and b==4128 and a%32==0;self.ret()
            elif p==CLEAR:
                assert a==self.state_address+272;self.ret()
            elif p==STARTFN:
                assert not self.get(self.file+8)
                u.mem_write(IMAGE,ndspy_decomprimi_sicuro(bytes(u.mem_read(IMAGE,len(self.encoded))),len(self.raw)))
                if self.fault=='crc':self.put(IMAGE+len(self.raw)-1,0,1)
                self.loaded=True;self.ret()
            elif p==WIFIFN:
                assert a==54;self.ret()
            elif p==END:
                assert a==self.state_address+272;self.loaded=False;self.ret(1)
            return
        assert p in self.compiled_fetch,f'unexpected fetch {p:08x}'
    def call(self,name,*args):return self.address(self.symbols[name],*args)
    def address(self,p,*args):
        seeds=[0x44440000+i for i in range(8)]
        for r,v in zip(REGS,seeds):self.u.reg_write(r,v)
        for i,r in enumerate((UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3)):self.u.reg_write(r,args[i] if i<len(args) else 0)
        self.u.reg_write(UC_ARM_REG_SP,STACK);self.u.reg_write(UC_ARM_REG_LR,STOP|1)
        phase_before=self.phase
        cpsr=self.u.reg_read(UC_ARM_REG_CPSR)&0xdf;ime=self.get(IME);start=self.instructions;self.low=STACK
        self.u.mem_write(STACK-3072,b'\xa5'*64);
        if len(args)>4:self.u.mem_write(STACK,struct.pack('<'+'I'*(len(args)-4),*args[4:]))
        self.u.emu_start(p,STOP,count=10000000)
        assert self.u.reg_read(UC_ARM_REG_PC)==STOP,f'finite native nonreturn at {self.u.reg_read(UC_ARM_REG_PC):08x}'
        assert self.u.reg_read(UC_ARM_REG_SP)==STACK and [self.u.reg_read(r) for r in REGS]==seeds,'ABI preservation'
        assert self.u.reg_read(UC_ARM_REG_CPSR)&0xdf==cpsr and self.get(IME)==ime,'IRQ/IME preservation'
        assert bytes(self.u.mem_read(STACK-3072,64))==b'\xa5'*64
        assert bytes(self.u.mem_read(self.state_address-16,16))==b'\x96'*16 and bytes(self.u.mem_read(self.state_address+SIZE,16))==b'\x69'*16
        self.metrics.append((name if (name:=next((k for k,v in self.symbols.items() if v==p),None)) else hex(p),STACK-self.low,self.instructions-start))
        self.phase_metrics.append((phase_before,self.phase,*self.metrics[-1]))
        return self.u.reg_read(UC_ARM_REG_R0)
    def init(self):return self.call('ui_module_init',self.state_address)
    def begin(self,role=1,generation=1):return self.call('ui_module_begin' if 'ui_module_begin' in self.symbols else 'ui_module_open',self.state_address,CONFIG,role,generation)
    def step(self,role=1,generation=1,budget=4096):return self.call('ui_module_step',self.state_address,role,generation,budget)
    def cancel(self,role=1,generation=1):return self.call('ui_module_cancel',self.state_address,role,generation)
    def open(self,role=1,generation=1):
        result=self.begin(role,generation)
        return self.drive(role=role,generation=generation) if result==MORE else result
    def check(self,role=1,generation=1,selector=0):return self.call('ui_module_check',self.state_address,role,generation,selector)
    def release(self,role=1,generation=1):return self.call('ui_module_release',self.state_address,role,generation)
    def close(self,role=1,generation=1):
        result=self.release(role,generation)
        return self.drive(role=role,generation=generation) if result==MORE else result

def build_receipt(directory):
    """Small reproducible report; no ROM bytes or compiled artifacts retained."""
    import hashlib
    code,symbols=compile_module(directory);obj=(directory/'module.o').read_bytes()
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
            'undefined':undefined,'relocations':relocations,'stack_usage':(directory/'module.su').read_text().strip()}
if __name__=='__main__':
    import json,tempfile
    with tempfile.TemporaryDirectory(prefix='module-receipt-') as d:print(json.dumps(build_receipt(Path(d)),indent=2))
