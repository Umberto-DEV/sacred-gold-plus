"""Actual compiled reader + checked heap. Class A seams explicitly fake FS.
Class B extends this with actual pinned FS and declared cartridge transport.
All fixture addresses are private synthetic addresses, never reservations.
"""
import sys, zlib
from heap_bench import *
from unicorn import UC_HOOK_MEM_READ
sys.path.insert(0,str(SOURCE))
from sgp131 import ui_resource
READER,CONFIG,LEASE,SLICE=0x02360000,0x02210000,0x027e3100,0x027e3120
ARC,FAT,FNT=0x021e3654,0x02270000,0x02271008
INIT,OPEN,READ,CLOSE,SEEK,CPSR=0x020d7f98,0x020d8278,0x020d83cc,0x020d82c0,0x020d83dc,0x020d3a90
R_SIZE=744
PHASE,GEN,OWN,FAILED,CANCEL,ROOT=616,620,624,628,632,636
MORE,OK,ERROR,HELD=0,1,2,3
ZERO,P_OPEN,P_PREFIX,P_MEMBER,P_CLOSE,P_VERIFY,READY,P_FAILED,RELEASED,HOLD=range(10)
def compile_resource(directory,mutation=None):
    content=(SOURCE/'features/ui-native/resource.c').read_text()
    if mutation:
        old,new=mutation;assert old in content;content=content.replace(old,new,1)
    src=directory/'resource_unit.c';obj=directory/'resource.o'
    src.write_text('#include "heap.c"\n'+content)
    subprocess.run(['clang',*FLAGS,'-I',str(SOURCE/'features/ui-native'),'-fstack-usage','-c',str(src),'-o',str(obj)],check=True,capture_output=True)
    spec=importlib.util.spec_from_file_location('resource_loader',SOURCE/'features/options/tools/carica_text.py')
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    return mod.load_text(obj.read_bytes(),CODE)
def synthetic(lang='EN',authored=None):
    assets=bytes((i*17+3)%256 for i in range(48320))
    member=bytearray(ui_resource._pack_member(lang,assets,{i:(i%509+1,65535) for i in range(1,494)},({1:(1,0xe000,2,65535)} if authored is None else authored),0x885ab7fc))
    # Synthetic asset bytes with canonical identity LABEL; runtime whole CRC owns
    # corruption detection, compiler's real asset identity remains Class B.
    member[64:96]=bytes.fromhex('96490ff4d596a9c21f4a8d8ac7a42a4c7c57834bbfbcd8a7ef0b2a0aed14e102')
    prefix=bytearray(468)
    struct.pack_into('<4sHHIHH4sIHH',prefix,0,b'NARC',0xfffe,0x100,35380+len(member),16,3,b'BTAF',428,52,0)
    for i in range(51):struct.pack_into('<II',prefix,28+i*8,i*4,(i+1)*4)
    struct.pack_into('<II',prefix,436,34912,34912+len(member))
    struct.pack_into('<4sIIHH4sI',prefix,444,b'BTNF',16,4,0,1,b'GMIF',34920+len(member))
    # unnamed BTNF is 04 00 00 00 00 00 01 00, 8 bytes.
    prefix[452:460]=bytes.fromhex('0400000000000100')
    raw=bytes(prefix)+bytes(34912)+bytes(member)
    config=struct.pack('<16I',0x32435255,2,0 if lang=='EN' else 1,len(raw),468,51,35380,len(member),48320,zlib.crc32(prefix),zlib.crc32(member),0x885ab7fc,509,64,7,0)
    return raw,config
class ResourceBench(HeapBench):
    def __init__(self,compiled,raw=None,config=None):
        super().__init__(compiled)
        self.raw,self.config=synthetic() if raw is None else (raw,config)
        self.fs_calls=[];self.fs_fault=None;self.open_length=None;self.close_failures=0
        self.u.mem_write(CONFIG,self.config);self.allowed.extend(((READER,READER+R_SIZE),(LEASE,LEASE+12),(SLICE,SLICE+8)))
        self.archive_fixture();assert self.create()==1
        self.guarded_memory();self.guards_ready=True
    def store(self,u,access,p,n,v,data):
        pc=u.reg_read(UC_ARM_REG_PC)
        if not hasattr(self,'resource_regions'):
            funcs=sorted((addr&~1,name) for name,addr in self.symbols.items() if not name.startswith('$') and addr&1)
            self.resource_regions=[(a,funcs[i+1][0] if i+1<len(funcs) else CODE+len(self.code)) for i,(a,name) in enumerate(funcs) if name.startswith(('r','ui_res_'))]
        if any(a<=pc<b for a,b in self.resource_regions):
            assert any(a<=p<p+n<=b for a,b in ((READER,READER+R_SIZE),(LEASE,LEASE+12),(SLICE,SLICE+8),(STACK-1024,STACK))),f'resource owner store {p:08x}/{n}'
        super().store(u,access,p,n,v,data)
    def guarded_memory(self):
        self.u.mem_write(READER-16,b'\x96'*16);self.u.mem_write(READER+R_SIZE,b'\x69'*16)
        self.u.hook_add(UC_HOOK_MEM_READ,self.read_guard,begin=0x04000000,end=0x04000fff)
    def read_guard(self,u,access,p,n,v,data):
        assert IME<=p<p+n<=IME+4,f'unknown MMIO read {p:08x}/{n}'
    def call(self,name,*args):
        check=args and args[0]==READER and name.startswith('ui_res_')
        tail=bytes(self.u.mem_read(READER+72,8)) if check else None
        before=(self.get(READER+PHASE),self.get(READER+652)) if name=='ui_res_step' else None
        result=super().call(name,*args)
        if before is not None:
            if not hasattr(self,'step_metrics'):self.step_metrics=[]
            self.step_metrics.append((*before,self.metrics[-1][1],self.metrics[-1][2]))
        if check and hasattr(self,'guards_ready'):
            assert bytes(self.u.mem_read(READER-16,16))==b'\x96'*16,'reader prefix canary'
            assert bytes(self.u.mem_read(READER+R_SIZE,16))==b'\x69'*16,'reader suffix canary'
            assert bytes(self.u.mem_read(READER+72,8))==(bytes(8) if name in ('ui_res_init','ui_res_begin') else tail),'native FS72 boundary'
        return result
    def archive_fixture(self):
        self.u.mem_write(ARC,bytes(92));self.put(ARC,0x6d6f72);self.put(ARC+0x1c,7)
        for off,value in ((0x2c,FAT),(0x30,4104),(0x34,FNT),(0x38,2902),(0x44,FAT),(0x48,0x020d84c4),(0x4c,0x020d850c),(0x50,0x020d7484),(0x54,0x020d8514),(0x58,0x602)):self.put(ARC+off,value)
        self.put(0x021e3638,1)
    def hook(self,u,p,n,data):
        if p==CPSR:
            self.instructions+=1;self.ret(u.reg_read(UC_ARM_REG_CPSR)&128);return
        if p in (INIT,OPEN,READ,CLOSE,SEEK):
            self.instructions+=1
            assert self.get(IME)==1 and not u.reg_read(UC_ARM_REG_CPSR)&128
            assert not u.reg_read(UC_ARM_REG_CPSR)&32
            a,b,c,d=[u.reg_read(r) for r in (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3)]
            self.fs_calls.append((p,a,b,c,d));assert a==READER
            if p==INIT:
                for off in (0,4,8,12,24,28):self.put(a+off,0)
                self.put(a+16,14);self.ret()
            elif p==OPEN:
                assert bytes(u.mem_read(b,13))==b'rom:/a/0/3/8\0'
                if self.fs_fault=='open':self.ret(0);return
                self.put(a+8,ARC);self.put(a+12,0x10);self.put(a+32,167);self.put(a+36,0x100000)
                self.put(a+40,0x100000+(self.open_length or len(self.raw)));self.put(a+44,0x100000);self.ret(1)
            elif p==READ:
                pos=self.get(a+44)-self.get(a+36);count=min(c,len(self.raw)-pos)
                u.mem_write(b,self.raw[pos:pos+count]);self.put(a+44,self.get(a+44)+count)
                fault=self.fs_fault=='prefix' and pos==0 or self.fs_fault=='member' and pos!=0
                self.ret(0xffffffff if fault else count)
            elif p==SEEK:
                self.put(a+44,min(self.get(a+36)+b,self.get(a+40))-(4 if self.fs_fault=='seek' else 0));self.ret(1)
            else:
                if self.close_failures:self.close_failures-=1;self.ret(0)
                else:self.put(a+8,0);self.put(a+12,0);self.ret(1)
            return
        super().hook(u,p,n,data)
    def start(self):
        assert self.call('ui_res_init',READER)==1
        return self.call('ui_res_begin',READER,CONFIG,TOKEN)
    def start_duplicate(self):return self.call('ui_res_begin',READER,CONFIG,TOKEN)
    def step(self):return self.call('ui_res_step',READER)
    def phase(self):return self.get(READER+PHASE)
    def root(self):return self.get(READER+ROOT)
    def finish(self,limit=60):
        for _ in range(limit):
            result=self.step()
            if result!=MORE:return result
        raise AssertionError('reader bounded verification exceeded')

def resource_receipt(directory):
    import hashlib
    code,symbols=compile_resource(directory);obj=(directory/'resource.o').read_bytes()
    h=struct.unpack_from('<HHIIIIIHHHHHH',obj,16)
    sections=[struct.unpack_from('<10I',obj,h[5]+i*h[10]) for i in range(h[11])]
    def contents(s):return obj[s[4]:s[4]+s[5]]
    def name(table,index):return table[index:table.index(b'\0',index)].decode()
    names=contents(sections[h[12]]);labels=[name(names,s[0]) for s in sections];ti=labels.index('.text')
    markers=[];undefined=[];relocations={};functions={}
    for s in sections:
        if s[1]==2:
            strings=contents(sections[s[6]])
            for index,value,size,info,other,si in struct.iter_unpack('<IIIBBH',contents(s)):
                label=name(strings,index)
                if si==ti and label.startswith(('$d','$t')):markers.append((value&~1,label[:2]))
                if si==ti and info&15==2:functions[label]=size
                if label and not si and info&0xf0:undefined.append(label)
        if s[1]==9 and s[7]==ti:
            for offset,info in struct.iter_unpack('<II',contents(s)):relocations[info&255]=relocations.get(info&255,0)+1
    markers.sort();literal=0
    for i,(at,kind) in enumerate(markers):
        end=markers[i+1][0] if i+1<len(markers) else len(code)
        if kind=='$d':literal+=end-at
    return dict(compiler=subprocess.check_output(['clang','--version'],text=True).strip(),
                object_sha256=hashlib.sha256(obj).hexdigest(),payload_sha256=hashlib.sha256(code).hexdigest(),
                text_bytes=len(code),literal_padding_bytes=literal,instruction_bytes=len(code)-literal,
                undefined=undefined,relocations=relocations,function_bytes=functions,
                stack_usage=(directory/'resource.su').read_text().strip())
if __name__=='__main__':
    import json,tempfile
    with tempfile.TemporaryDirectory(prefix='resource-receipt-') as d:print(json.dumps(resource_receipt(Path(d)),indent=2))
