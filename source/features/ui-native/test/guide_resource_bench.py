"""Compiled Guide owner; Class A lowerFS seams, no ROM extraction/output."""
import tempfile,zlib,sys
from heap_bench import *
from unicorn import UC_HOOK_MEM_READ
from bg_bench import object_details,check_compiled,bg_stack_arguments
sys.path.insert(0,str(SOURCE))
from sgp131 import guide_content
CFG,OUT,ARC,FAT,FNT=0x02210000,0x027e3100,0x021e3654,0x02270000,0x02271008
INIT,FAST,ASYNC,CLOSE,SEEK,CPSR=0x020d7f98,0x020d8208,0x020d83bc,0x020d82c0,0x020d83dc,0x020d3a90
MORE,READY,FAILED,RELEASED,HOLD=1,2,3,4,5

def compile_guide(directory,mutation=None):
    text=(SOURCE/'features/ui-native/guide_resource.c').read_text()
    if mutation:
        old,new=mutation;assert old in text;text=text.replace(old,new,1)
    src=directory/'guide.c';obj=directory/'guide.o'
    src.write_text('#include "heap.c"\n#include "resource.c"\n'+text)
    subprocess.run(['clang',*FLAGS,'-fno-jump-tables','-fstack-usage','-I',str(SOURCE/'features/ui-native'),'-c',str(src),'-o',str(obj)],check=True,capture_output=True)
    s=importlib.util.spec_from_file_location('ggr_loader',SOURCE/'features/options/tools/carica_text.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
    result=m.load_text(obj.read_bytes(),CODE);object_details(obj.read_bytes(),result[0]);return result

def synthetic():
    # Deliberate unsorted IDs + shared immutable pages + cyclic references.
    cats=[dict(id=4,title='A',entries=[dict(id=9,title='B',pages=[dict(lines=['C'],reference=2)])]),
          dict(id=1,title='D',entries=[dict(id=2,title='E',pages=[dict(lines=['F'],reference=9)])])]
    enc=lambda t:[ord(c)-64 for c in t]+[65535]
    data=guide_content.build_content(cats,enc,lambda t:len(t)*4)
    return data,guide_content.read_content(data)

def config(data,fid=5,off=100,whole=None):
    whole=off+len(data) if whole is None else whole
    nc,ne=struct.unpack_from('<HH',data,8)
    return struct.pack('<16I',0x31435247,1,0,1,fid,0x100000,0x100000+whole,0x18000000,whole,off,len(data),zlib.crc32(data),nc,ne,0,0)

class GuideBench(HeapBench):
    def guard_setup(self):
        self.u.hook_add(UC_HOOK_MEM_READ,self.read_guard,begin=0x04000000,end=0x04000fff)
        self.owner_regions=[]
        funcs=sorted((v&~1,k) for k,v in self.symbols.items() if v&1 and not k.startswith('$'))
        for i,(a,name) in enumerate(funcs):
            if name.startswith(('ggr_','ui_guide_')):self.owner_regions.append((a,funcs[i+1][0] if i+1<len(funcs) else CODE+len(self.code)))
    def read_guard(self,u,access,p,n,v,data):
        assert IME<=p<p+n<=IME+4,f'unknown Guide MMIO read {p:08x}/{n}'
    def store(self,u,access,p,n,v,data):
        if hasattr(self,'owner_regions') and any(a<=u.reg_read(UC_ARM_REG_PC)<z for a,z in self.owner_regions):
            assert any(a<=p<p+n<=z for a,z in ((self.reader,self.reader+292),(self.lease,self.lease+36),(OUT,OUT+128),(STACK-1024,STACK))),f'Guide owner write {p:08x}/{n}'
        super().store(u,access,p,n,v,data)
    def __init__(self,compiled,data=None,cfg=None):
        super().__init__(compiled);self.data,self.graph=synthetic();self.data=data if data is not None else self.data
        self.cfg=config(self.data) if cfg is None else cfg;self.fs_calls=[];self.close_failures=0;self.open_fault=False;self.short=False;self.cursor=0;self.next=0
        assert self.create(0x40000)==1
        self.app=self.alloc(1024);assert self.app;self.reader=self.app+32;self.lease=self.app+352
        self.allowed.append((OUT,OUT+128));self.u.mem_write(CFG,self.cfg);self.archive();self.guard_setup()
    def address(self,p,*args):bg_stack_arguments(self,args);return super().address(p,*args)
    def archive(self):
        self.u.mem_write(ARC,bytes(92));self.put(ARC,0x6d6f72);self.put(ARC+28,7)
        for off,val in ((44,FAT),(48,4104),(52,FNT),(56,2902),(68,FAT),(72,0x020d84c4),(76,0x020d850c),(80,0x020d7484),(84,0x020d8514),(88,0x602)):self.put(ARC+off,val)
        self.put(0x021e3638,1);self.put(0x021e363c,0x42);self.put(0x021e3640,0)
        words=struct.unpack('<16I',self.cfg);self.put(FAT+8*words[4],words[5]);self.put(FAT+8*words[4]+4,words[6])
    def relocate_archive_cache(self,raw):
        """Prepare native arena cache; preserve its actual FAT/FNT contents."""
        fat=bytes(self.u.mem_read(self.get(ARC+44),4104))
        fnt=bytes(self.u.mem_read(self.get(ARC+52),2902))
        aligned=(raw+31)&~31
        self.u.mem_write(aligned,fat);self.u.mem_write(aligned+4104,fnt)
        self.put(ARC+68,raw);self.put(ARC+44,aligned);self.put(ARC+52,aligned+4104)
        return aligned
    def hook(self,u,p,n,data):
        check_compiled(self.code,p,n)
        if p==ALLOC and self.get(TOKEN+16)==u.reg_read(UC_ARM_REG_R0):
            size=u.reg_read(UC_ARM_REG_R1);raw=self.get(TOKEN+16)+0x100+self.next;self.next+=(size+19)&~3
            self.put(raw-16,0x5544,2);self.put(raw-12,size);self.calls.append((p,(u.reg_read(UC_ARM_REG_R0),size,4)));self.ret(raw);return
        if p==CPSR:self.instructions+=1;self.ret(u.reg_read(UC_ARM_REG_CPSR)&128);return
        if p in (INIT,FAST,ASYNC,CLOSE,SEEK):
            self.instructions+=1;sp=u.reg_read(UC_ARM_REG_SP)
            assert sp%8==0 and self.get(IME)==1 and not u.reg_read(UC_ARM_REG_CPSR)&(128|32),'FS EABI/IME/state'
            a,b,c=[u.reg_read(x) for x in (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2)];assert a==self.reader
            self.fs_calls.append((p,a,b,c));f=a
            if p==INIT:self.u.mem_write(f,bytes(72));self.put(f+16,14)
            elif p==FAST:
                self.put(f+8,ARC)
                if self.open_fault:self.ret(0);return
                w=struct.unpack('<16I',self.cfg)
                for off,v in ((12,16),(16,0),(20,0),(32,w[4]),(36,w[5]),(40,w[6]),(44,w[5])):self.put(f+off,v)
            elif p==SEEK:self.put(f+44,self.get(f+36)+b)
            elif p==ASYNC:
                w=struct.unpack('<16I',self.cfg);off=self.get(f+44)-self.get(f+36)-w[9]
                count=max(0,c-2) if self.short else c;u.mem_write(b,self.data[off:off+count]);self.put(f+44,self.get(f+44)+count)
                for off,v in ((16,0),(20,0),(48,b),(52,c),(56,c)):self.put(f+off,v)
                self.ret(count);return
            else:
                if self.close_failures:self.close_failures-=1;self.ret(0);return
                self.put(f+8,0);self.put(f+12,0);self.put(f+16,14);self.put(f+20,0)
            self.ret(1);return
        super().hook(u,p,n,data)
    def start(self):
        assert self.call('ui_guide_init',self.reader)==1
        return self.call('ui_guide_begin',self.reader,CFG,TOKEN)
    def finish(self,limit=200):
        for i in range(limit):
            r=self.call('ui_guide_step',self.reader,4096)
            if r!=MORE:return r
        raise AssertionError('bounded Guide polls exceeded')

def build_receipt(directory):
    import hashlib
    code,symbols=compile_guide(directory)
    r=object_details((directory/'guide.o').read_bytes(),code)
    r['stack_usage']=(directory/'guide.su').read_text().replace(str(directory),'TEMP')
    r['compiler']=subprocess.check_output(['clang','--version'],text=True).strip()
    r['abi_bytes']={'UiGuideConfig':64,'UiGuideReader':292,'UiGuideLease':36,'Category':32,'Entry':32,'Page':16}
    r['dependencies']={n:hashlib.sha256((SOURCE/'features/ui-native'/n).read_bytes()).hexdigest() for n in ('heap.c','heap.h','heap_internal.h','resource.c','resource.h','font.h')}
    return r
if __name__=='__main__':
    import json
    with tempfile.TemporaryDirectory() as d:print(json.dumps(build_receipt(Path(d)),indent=2))
