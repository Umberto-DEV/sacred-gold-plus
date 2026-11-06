"""Compiled font+reader+heap. Class A explicitly seams native font/FS/heap.
Synthetic addresses and CRC-equivalent metrics are NOT native asset evidence.
"""
from resource_bench import *
import tempfile,hashlib
FL,FJ,SC,REQ,TO,WIN,BG=0x02362000,0x02362400,0x02362800,0x02362c00,0x02362d00,0x02363000,0x02363200
FM,FW,FN,EXT,SGG=0x02370000,0x02370200,0x02370500,0x02300000,0x02310000
PIX,FRONT,PIX_BYTES=0x02340000,0x02346000,21120
WORK,WORKPTR,FFLAGS,COLORS,LOOKUP=0x02111890,0x0211188c,0x02111886,0x021d1f6e,0x021d1f94
RENDER,GENERATE=0x02020358,0x0202036c
F_REFUSE,F_READY,F_ACTIVE,F_DONE,F_HOLD,F_DEFER,F_CANCEL,F_INVALID=range(8)
def compile_font(directory,mutation=None):
    content=(SOURCE/'features/ui-native/font.c').read_text()
    if mutation:
        old,new=mutation;assert old in content;content=content.replace(old,new,1)
    src=directory/'font_unit.c';obj=directory/'font.o'
    src.write_text('#include "heap.c"\n#include "resource.c"\n'+content)
    cp=subprocess.run(['clang',*FLAGS,'-I',str(SOURCE/'features/ui-native'),'-fstack-usage','-c',str(src),'-o',str(obj)],capture_output=True,text=True)
    if cp.returncode:raise AssertionError(cp.stderr)
    spec=importlib.util.spec_from_file_location('font_loader',SOURCE/'features/options/tools/carica_text.py')
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    return mod.load_text(obj.read_bytes(),CODE)
def synthetic_widths():
    # Linear CRC equation: alter 32 low bits of legal metric values. This tests
    # the production CRC gate with synthetic metrics without redistributing data.
    v=bytearray([6]*509)
    for g in [224,*range(493,510)]:v[g-1]=0
    base=zlib.crc32(v);basis={}
    for i in range(64):
        w=v.copy();w[i]^=1;x=zlib.crc32(w)^base;mask=1<<i
        while x:
            k=x.bit_length()-1
            if k in basis:x^=basis[k][0];mask^=basis[k][1]
            else:basis[k]=(x,mask);break
    x=0x885ab7fc^base;mask=0
    while x:
        k=x.bit_length()-1;a,b=basis[k];x^=a;mask^=b
    for i in range(64):
        if mask>>i&1:v[i]^=1
    assert zlib.crc32(v)==0x885ab7fc
    return bytes(v)
class FontBench(ResourceBench):
    def __init__(self,compiled,raw=None,config=None,expected=OK):
        self.publication_injection=None
        super().__init__(compiled,raw,config)
        self.allowed.extend(((FL,FL+0x1200),(FM-32,FM+0x800),(PIX,PIX+PIX_BYTES),(WORK,WORK+130),(WORK+0xb4,WORK+0xb5),(FFLAGS,FFLAGS+2),(COLORS,COLORS+6),(LOOKUP,LOOKUP+512)))
        self.widths=synthetic_widths();self.font_calls=[];self.anomaly=None;self.publication_injection=None
        self.prepare_font()
        assert self.start()==MORE
        result=MORE
        for _ in range(60):
            result=ResourceBench.step(self)
            if result!=MORE:break
        assert result==expected
    def store(self,u,access,p,n,v,data):HeapBench.store(self,u,access,p,n,v,data)
    def prepare_font(self):
        self.put(WORKPTR,WORK);self.put(WORK+0x9c,FM);self.put(WORK+0xb4,1,1)
        self.u.mem_write(FM,bytes(124));self.put(FM,1);self.put(FM+4,0x02026111)
        for off,val in ((8,3),(12,64),(0x54,FN),(0x58,0),(0x5c,16),(0x60,0x7f50),(0x64,509),(0x68,0x02021010),(0x6c,0),(0x70,0x020262b5),(0x74,FW),(0x78,0x8c)):self.put(FM+off,val)
        self.u.mem_write(FW,self.widths)
        self.u.mem_write(BG,bytes(360));self.put(BG,38);self.put(BG+8+20,0x20000100)
        self.u.mem_write(WIN,struct.pack('<I6BHI',BG,0,0,0,30,22,0,0,PIX))
        self.u.mem_write(PIX,bytes((i*7+9)%256 for i in range(PIX_BYTES)))
        self.u.mem_write(FRONT,bytes([0xb9])*PIX_BYTES)
        for p,n in ((FFLAGS,2),(COLORS,6),(LOOKUP,512),(WORK,130)):self.u.mem_write(p,bytes((i*13+17)%256 for i in range(n)))
    def allocate_pool(self,size=256):
        # Class A retains an explicit NNS boundary seam; ui_alloc38 itself
        # publishes the real ledger/GF prefix. Class B executes native NNS.
        self.pool_allocation=True
        try:pool=self.call('ui_alloc38',TOKEN,size,0)
        finally:self.pool_allocation=False
        assert pool
        return pool
    def buffer_request(self,pool,words,size=256,offset=0,**kw):
        self.request(**kw)
        self.u.mem_write(pool+offset,struct.pack('<%dH'%len(words),*words))
        self.u.mem_write(TO,struct.pack('<5I',3,pool,size,1,1))
        self.put(REQ+16,offset);self.put(REQ+20,len(words))
    def acquire(self,owner=0):return self.call('ui_font_acquire',FL,READER,owner)
    def globals(self):return tuple(bytes(self.u.mem_read(p,n)) for p,n in ((FFLAGS,2),(COLORS,6),(LOOKUP,512),(WORK,130)))
    def pixels(self):return bytes(self.u.mem_read(PIX,PIX_BYTES))
    def request(self,words=(299,65535),x=0,y=0,cap=11,colors=(1,15,2),kind=2,policy=1):
        root=self.root() if kind==1 else SGG;size=len(self.raw)-35380 if kind==1 else 120000
        if kind==1:
            assert self.call('ui_res_text',FL+8,1,SLICE)==1
            text=self.get(SLICE);words=struct.unpack('<%dH'%(self.get(SLICE+4)//2),bytes(self.u.mem_read(text,self.get(SLICE+4))))
        else:
            text=SGG+0x200;self.u.mem_write(text,struct.pack('<%dH'%len(words),*words))
        self.u.mem_write(TO,struct.pack('<5I',kind,root,size,1,1))
        self.u.mem_write(REQ,struct.pack('<8I8B',WIN,FRONT,PIX_BYTES,TO,text-root,len(words),policy,SC,x,y,cap,*colors,0,0))
        return text
    def begin(self,**kw):self.request(**kw);return self.call('ui_font_begin',FL,FJ,REQ)
    def step(self,budget=8):return self.call('ui_font_step',FL,FJ,budget)
    def cancel(self):return self.call('ui_font_cancel',FL,FJ)
    def release(self):return self.call('ui_font_release',FL)
    def hook(self,u,p,n,data):
        if p==ALLOC and getattr(self,'pool_allocation',False) and not self.native:
            self.instructions+=1
            args=tuple(u.reg_read(r) for r in (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2));self.calls.append((p,args))
            roots=[self.get(TOKEN+28+4*i) for i in range(16)]
            raw=max(root-16+self.get(root-28) for root in roots if root)+0x40
            raw=(raw+3)&~3
            self.put(raw-16,0x5544,2);self.put(raw-12,args[1]);self.ret(raw);return
        if p==DISABLE and self.publication_injection:
            callback=self.publication_injection;self.publication_injection=None;callback()
        if p in (GENERATE,RENDER):
            self.instructions+=1;self.font_calls.append(p)
            assert u.reg_read(UC_ARM_REG_CPSR)&128 and self.get(IME)==1
            if p==GENERATE:
                assert not self.get(FFLAGS,2)&17
                self.u.mem_write(LOOKUP,b'\x36'*512);self.ret();return
            j=u.reg_read(UC_ARM_REG_R0);text=self.get(j);x=self.get(j+12,2);y=self.get(j+14,2)
            while True:
                c=self.get(text,2);text+=2
                if c!=0xe000:break
                x=self.get(j+10,1);y+=16
            if c!=65535:x+=self.widths[c-1]
            self.put(j,text);self.put(j+12,x,2);self.put(j+14,y,2)
            self.u.mem_write(WORK,b'\x51'*130)
            if self.anomaly=='noadvance':self.put(j,text-2)
            if self.anomaly=='speed':self.put(j+41,128,1)
            self.ret(3 if self.anomaly=='update' else int(c==65535));return
        super().hook(u,p,n,data)

def font_receipt(directory):
    code,symbols=compile_font(directory);obj=(directory/'font.o').read_bytes()
    header=struct.unpack_from('<HHIIIIIHHHHHH',obj,16)
    sections=[struct.unpack_from('<10I',obj,header[5]+i*header[10]) for i in range(header[11])]
    def contents(s):return obj[s[4]:s[4]+s[5]]
    def name(table,index):return table[index:table.index(b'\0',index)].decode()
    names=contents(sections[header[12]]);labels=[name(names,s[0]) for s in sections];ti=labels.index('.text')
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
      stack_usage=(directory/'font.su').read_text().strip())
if __name__=='__main__':
    import json
    with tempfile.TemporaryDirectory(prefix='font-receipt-') as d:print(json.dumps(font_receipt(Path(d)),indent=2))
