"""Checked heap11 compiled harness. Prepared addresses are not reservations."""
import hashlib,importlib.util,struct,subprocess
from pathlib import Path
from heap_bench import *
from module_bench import instruction_set
from test_heap_rom import PINS,ROM_PINS,TEMPLATES
SIZE=40
RESIDENT=0x023d7b20
RESIDENT_CONFIG='UI_PERSISTENT_RESIDENT_TOKEN_ADDRESS'
CPSR=0x020d3a90
HEAP11_BYTES=0x1c000
REFUSED,RELEASED,HOLD=0,1,2
EXTRA_PINS=((CPSR,24,"df0fcaa0e5aad641260041edb6a5688cb9a43de0bfeeff2bfcb54ef8c8cc54b8"),)

def compile_persistent(directory,mutation=None,*,full_heap=True,resident=None,prefix="",extra=""):
    body=(SOURCE/'features/ui-native/persistent.c').read_text()
    if mutation:
        old,new=mutation;assert old in body;body=body.replace(old,new,1)
    src=directory/'persistent.c';obj=directory/'persistent.o'
    src.write_text(prefix+('#include "heap.c"\n' if full_heap else '')+body+extra)
    config=[] if resident is None else ['-D'+RESIDENT_CONFIG+'='+str(resident)]
    subprocess.run(['clang',*FLAGS,*config,'-fno-jump-tables','-I',str(SOURCE/'features/ui-native'),'-fstack-usage','-c',str(src),'-o',str(obj)],check=True,capture_output=True)
    spec=importlib.util.spec_from_file_location('persistent_loader',SOURCE/'features/options/tools/carica_text.py')
    loader=importlib.util.module_from_spec(spec);spec.loader.exec_module(loader)
    return loader.load_text(obj.read_bytes(),CODE)

class PersistentBench(HeapBench):
    def __init__(self,compiled,sections=None,slot=6,token=TOKEN):
        super().__init__(compiled)
        self.owner=token;self.slot=slot;self.normal_control=False;self.visited=set();self.mask_run=0;self.max_mask_run=0
        if sections:
            for p,data in sections:self.u.mem_write(p,data)
            self.u.mem_write(CODE,self.code)
        self.compiled_fetch=instruction_set(self.u,[v for k,v in self.symbols.items() if not k.startswith('$')],[(CODE,CODE+len(self.code))])
        self.native_fetch=instruction_set(self.u,[CREATE,ALLOC,FREE,DESTROY,DISABLE,RESTORE,CPSR,CPSR+12,0x0201aa8d,0x0201ab0d],[(a,a+n) for a,n,d in (*PINS,*EXTRA_PINS)]) if sections else set()
        if sections:
            self.native=True;self.u.mem_write(0x021d84b0,bytes(16))
            for j,(raw,size) in enumerate(TEMPLATES):self.put(self.handles+4*j,self.address(CREATE,raw,size,0))
            self.put(self.handles+12,0);assert self.address(CREATE,PARENT,0x100000,0)==PARENT;self.put(self.handles+12,PARENT)
            raw=self.address(ALLOC,PARENT,HEAP11_BYTES,4);assert raw
            assert self.address(CREATE,raw,HEAP11_BYTES,0)==raw
        else:
            raw=PARENT+0x10000;self.put(raw-16,0x5544,2);self.put(raw-12,HEAP11_BYTES);self.header(raw,HEAP11_BYTES)
        self.heap=raw
        self.put(self.handles+slot*4,raw);self.put(self.parents+slot*4,PARENT);self.put(self.raws+slot*4,raw);self.put(self.idxs+11,slot,1)
        self.u.mem_write(token,bytes(SIZE));self.calls.clear();self.writes.clear();self.metrics.clear()
        self.allowed=[(BASE,BASE+824),(TOKEN,TOKEN+SIZE),(token,token+SIZE),(self.heap,self.heap+HEAP11_BYTES)]
        self.prepared=True
    def hook(self,u,p,n,data):
        self.visited.add(p)
        if p==ALLOC and getattr(self,"return_fault",None) is not None:
            self.ret(self.return_fault);return
        if u.reg_read(UC_ARM_REG_CPSR)&128:self.mask_run+=1;self.max_mask_run=max(self.max_mask_run,self.mask_run)
        else:self.mask_run=0
        if p==CPSR:
            assert u.reg_read(UC_ARM_REG_SP)%8==0
            if not self.native:self.ret(u.reg_read(UC_ARM_REG_CPSR)&128);return
        if 0x0201a910<=p<0x0201abec:
            assert self.normal_control and not 0x0201aa7c<=p<0x0201aa8c,"forbidden production GF wrapper/AllocFail"
            assert p in self.native_fetch
            # Isolated successful native Heap_Alloc comparison only.
            self.instructions+=1;self.low=min(self.low,u.reg_read(UC_ARM_REG_SP));return
        if CODE<=p<CODE+len(self.code):assert p in self.compiled_fetch,f'non-code compiled fetch {p:08x}'
        return super().hook(u,p,n,data)
    def native_allowed(self,p):
        return p in self.native_fetch and any(a<=p<a+n for a,n,d in (*PINS,*EXTRA_PINS))
    def store(self,u,access,p,n,v,data):
        if getattr(self,"prepared",False) and self.handles<=p<self.handles+824:assert (p,n)==(self.counts+22,2),"only heapID11 u16 count may change"
        return super().store(u,access,p,n,v,data)
    def metadata(self):return bytes(self.u.mem_read(self.handles,824))
    def token(self,p=None):return bytes(self.u.mem_read(self.owner if p is None else p,SIZE))
    def alloc(self,n=5000,g=1,t=None):return self.call('ui_persistent_alloc',self.owner if t is None else t,n,g)
    def free(self,g=1,t=None):return self.call('ui_persistent_free',self.owner if t is None else t,g)
    def move(self,dst,src=None,g=1):return self.call('ui_persistent_move',dst,self.owner if src is None else src,g)
    def totals(self):
        node=self.get(self.heap+0x24);total=largest=count=0;seen=set()
        while node:
            assert node not in seen and len(seen)<4096;seen.add(node)
            assert self.heap+0x38<=node<self.heap+HEAP11_BYTES-16
            n=self.get(node+4);assert node+16+n<=self.heap+HEAP11_BYTES
            total+=n;largest=max(largest,n);count+=1;node=self.get(node+12)
        return total,largest,count
    def snapshot(self):return self.token(),self.metadata(),bytes(self.u.mem_read(self.heap,HEAP11_BYTES))

def build_receipt(directory,*,full_heap=True,resident=None,module=False):
    """Recompile exact composition, report ELF properties without retaining code."""
    prefix=(SOURCE/'features/ui-native/module.c').read_text() if module else ''
    code,symbols=compile_persistent(directory,full_heap=full_heap,resident=resident,prefix=prefix,
        extra='\n#include "heap.h"\n_Static_assert(sizeof(UiHeap)==92,"heap ABI");\n')
    obj=(directory/'persistent.o').read_bytes()
    header=struct.unpack_from('<HHIIIIIHHHHHH',obj,16)
    sections=[struct.unpack_from('<10I',obj,header[5]+i*header[10]) for i in range(header[11])]
    def content(s):return obj[s[4]:s[4]+s[5]]
    def name(table,i):return table[i:table.index(b'\0',i)].decode()
    names=content(sections[header[12]]);labels=[name(names,s[0]) for s in sections];ti=labels.index('.text')
    markers=[];undefined=[];relocations={};mutable=[]
    for label,s in zip(labels,sections):
        if s[2]&1 and s[5]:mutable.append((label,s[5]))
        if s[1]==2:
            strings=content(sections[s[6]])
            for index,value,size,info,other,si in struct.iter_unpack('<IIIBBH',content(s)):
                label=name(strings,index)
                if si==ti and label.startswith(('$d','$t')):markers.append((value&~1,label[:2]))
                if label and not si and info&0xf0:undefined.append(label)
        if s[1]==9 and s[7]==ti:
            for offset,info in struct.iter_unpack('<II',content(s)):relocations[info&255]=relocations.get(info&255,0)+1
    literal=0;markers.sort()
    for j,(start,kind) in enumerate(markers):
        end=markers[j+1][0] if j+1<len(markers) else len(code)
        if kind=='$d':literal+=end-start
    heap,_=compile_heap(directory)
    assert not mutable and not undefined
    return {'composition':{'full_heap':full_heap,'resident':resident,'module':module},
            'flags':FLAGS+['-fno-jump-tables','-fstack-usage']+([] if resident is None else ['-D'+RESIDENT_CONFIG+'='+str(resident)]),
            'abi_bytes':{'UiHeap':92,'UiPersistent':40},
            'compiler':subprocess.check_output(['clang','--version'],text=True).strip(),
            'object_sha256':hashlib.sha256(obj).hexdigest(),'payload_sha256':hashlib.sha256(code).hexdigest(),
            'payload_bytes':len(code),'heap_baseline_bytes':len(heap),'persistent_increment_bytes':len(code)-len(heap),
            'literal_and_padding_bytes':literal,'instruction_region_bytes':len(code)-literal,
            'undefined':undefined,'mutable_sections':mutable,'relocations':relocations,
            'stack_usage':'\n'.join(line.split(':')[-2]+':'+line.split(':')[-1] for line in (directory/'persistent.su').read_text().splitlines())}
if __name__=='__main__':
    import json,tempfile
    with tempfile.TemporaryDirectory(prefix='persistent-receipt-') as d:print(json.dumps(build_receipt(Path(d)),indent=2))
