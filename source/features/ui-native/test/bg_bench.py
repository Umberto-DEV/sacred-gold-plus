"""Scoped BG ARM harness; test addresses never assign product placement."""
import tempfile
from heap_bench import *
STATE=0x027e3100
def prepare_retired_wvr(b,lock_id=0x43):
    """Prepared native post-WVR residue, observed at real Settings entry.

    OS lock-ID allocation persists; WVR and VRAM ownership have retired.
    This prepares a seam, not execution of WVR/ARM7 termination.
    """
    if not getattr(b,'wvr_lock_page',False):
        b.u.mem_map(0x027ff000,0x1000);b.wvr_lock_page=True
    b.u.mem_write(0x027fffb0,struct.pack('<2I',0xffffffff,0xffff0000))
    p=0x027fffb0+4*((lock_id-0x40)//32)
    b.put(p,b.get(p)&~(0x80000000>>((lock_id-0x40)%32)))
    b.u.mem_write(0x021d43bc,struct.pack('<3I',lock_id,0,0))
    b.put(0x021d4138,0)
    b.u.mem_write(0x021e1a08,bytes(22))
    b.put(0x04000243,0x82,1)

def retired_wvr_snapshot(b):
    return tuple(bytes(b.u.mem_read(p,n)) for p,n in
                 ((0x04000243,1),(0x021d43bc,12),(0x021d4138,4),
                  (0x021e1a08,22),(0x027fffb0,8)))

_EXECUTION={}
def object_details(blob,code):
    import hashlib
    from capstone import Cs,CS_ARCH_ARM,CS_MODE_THUMB
    head=struct.unpack_from('<HHIIIIIHHHHHH',blob,16)
    sections=[struct.unpack_from('<10I',blob,head[5]+j*head[10]) for j in range(head[11])]
    def content(s):return blob[s[4]:s[4]+s[5]]
    def name(table,index):return table[index:table.index(b'\0',index)].decode()
    names=content(sections[head[12]]);labels=[name(names,s[0]) for s in sections];ti=labels.index('.text')
    markers=[];undefined=[];relocations={};bodies={}
    for section in sections:
        if section[1]==2:
            strings=content(sections[section[6]])
            for index,value,size,info,other,si in struct.iter_unpack('<IIIBBH',content(section)):
                label=name(strings,index)
                if si==ti and label.startswith(('$t','$d')):markers.append((value&~1,label[:2]))
                if label and not si and info&0xf0:undefined.append(label)
                if label and si==ti and info&15==2:bodies[label]=size
        if section[1]==9 and section[7]==ti:
            for offset,info in struct.iter_unpack('<II',content(section)):relocations[info&255]=relocations.get(info&255,0)+1
    markers.sort();literal=0;instructions={}
    for j,(start,kind) in enumerate(markers):
        end=markers[j+1][0] if j+1<len(markers) else len(code)
        if kind=='$d':literal+=end-start
        else:
            for ins in Cs(CS_ARCH_ARM,CS_MODE_THUMB).disasm(code[start:end],CODE+start):instructions[ins.address]=ins.size
    _EXECUTION[code]=instructions
    return dict(object_sha256=hashlib.sha256(blob).hexdigest(),payload_sha256=hashlib.sha256(code).hexdigest(),
                payload_bytes=len(code),literal_bytes=literal,instruction_bytes=len(code)-literal,
                undefined=undefined,relocations=relocations,function_bytes=bodies)
def check_compiled(code,p,n):
    if CODE<=p<CODE+len(code):assert _EXECUTION[code].get(p)==n,'compiled literal or invalid instruction entry'

def compile_bg(directory,mutation=None):
    content=(SOURCE/'features/ui-native/bg.c').read_text()
    if mutation:
        old,new=mutation
        assert old in content
        content=content.replace(old,new,1)
    src=directory/'bg.c'
    src.write_text('#include "heap.c"\n'+content)
    obj=directory/'bg.o'
    subprocess.run(['clang',*FLAGS,'-fno-jump-tables','-I',str(SOURCE/'features/ui-native'),'-fstack-usage','-c',str(src),'-o',str(obj)],check=True,capture_output=True)
    spec=importlib.util.spec_from_file_location('bg_loader',SOURCE/'features/options/tools/carica_text.py')
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    compiled=mod.load_text(obj.read_bytes(),CODE)
    object_details(obj.read_bytes(),compiled[0])
    return compiled
def bg_stack_arguments(b,args):
    """Pass the two extra unsigned EABI arguments in live caller stack words."""
    assert len(args)<=6
    extra=list(args[4:]);extra.extend([0]*(2-len(extra)))
    b.u.mem_write(STACK,struct.pack('<2I',*extra))

class BgBench(HeapBench):
    def __init__(self,compiled):
        super().__init__(compiled)
        self.allowed.append((STATE,STATE+176))
        self.u.mem_map(0x04001000,0x1000);self.u.mem_map(0x05000000,0x1000);self.u.mem_map(0x06000000,0x20000)
        self.allowed.extend(((0x04000000,0x04000004),(0x0400006c,0x0400006e),(0x04001000,0x04001004),
            (0x0400106c,0x0400106e),(0x05000000,0x05000002),(0x05000400,0x05000402),
            (0x021d21fc,0x021d2204),(0x021d110c,0x021d1114),(0x0600f000,0x06010000)))
        self.free_refuse=False
        self.next=0;self.acquisitions=0;self.fail_at=None
    def address(self,p,*args):
        bg_stack_arguments(self,args)
        return super().address(p,*args)
    def prepared_display(self):
        """Declared native-output fixture, not executed native display entry."""
        config=self.get(STATE+16);self.put(config,38)
        for i in range(2):
            self.u.mem_write(STATE+36+16*i,struct.pack('<I6BHI',config,i+1,1,1,30,22,13,1,self.get(STATE+28+4*i)))
            self.u.mem_write(config+8+44*(i+1),struct.pack('<5I4B2H4I',self.get(STATE+20+4*i),2048,0,0,0,0,1,0,32,0,0,0x1000,0x1000,0,0))
        self.put(STATE+12,2);self.put(STATE+100,1);self.put(STATE+108,3)
        self.put(0x04001000,0x10000);self.put(0x04000000,0x10000);self.put(0x0400000a,0x1e01,2);self.put(0x0400000c,0x1f11,2);self.put(0x04000304,0x8203,2)
        self.put(0x02110c80,0xffffffff)
        self.u.mem_write(0x021e15c0,struct.pack('<13H',0,1,64,0,0,0,0,0,0,4,256,0,0))
        self.u.mem_write(0x04000240,bytes((0x81,0,0x84,0,0,0,0x82,0,0,0x82)))
    def hook(self,u,p,n,data):
        check_compiled(self.code,p,n)
        if p==self.symbols.get('ui_free38',0)&~1 and self.free_refuse:self.ret(0);return
        if p in (0x0201d650,0x0201bf7c,0x02022c9c,0x02022d04,0x0201a0fc,0x020d28b8):
            r0,r1=[u.reg_read(r) for r in (UC_ARM_REG_R0,UC_ARM_REG_R1)]
            self.calls.append((p,(r0,r1,0)))
            if p==0x0201d650:
                bg=self.get(r0);index=self.get(r0+4,1);dest=self.get(bg+8+44*index)
                for row in range(22):
                    for col in range(30):self.put(dest+2*(32*(1+row)+1+col),0xd001+30*row+col,2)
            elif p==0x0201bf7c:self.u.mem_write(0x0600f000+2048*(r1-1),bytes(self.u.mem_read(self.get(r0+8+44*r1),2048)))
            elif p in (0x02022c9c,0x02022d04):
                dest=0x04000000 if p==0x02022c9c else 0x04001000
                self.put(dest,(self.get(dest)&~0x1f00)|(r0<<8));self.put(0x021d2200 if p==0x02022c9c else 0x021d21fc,r0)
            elif p==0x0201a0fc:self.put(0x021d110c,r0);self.put(0x021d1110,r1)
            self.ret(0);return
        if p==ALLOC and self.get(TOKEN+16)==u.reg_read(UC_ARM_REG_R0):
            self.acquisitions+=1
            if self.acquisitions==self.fail_at:self.ret(0);return
            size=u.reg_read(UC_ARM_REG_R1);raw=self.get(TOKEN+16)+0x100+self.next
            self.next+=(size+19)&~3
            self.put(raw-16,0x5544,2);self.put(raw-12,size)
            self.calls.append((p,(u.reg_read(UC_ARM_REG_R0),size,4)))
            self.ret(raw);return
        super().hook(u,p,n,data)
    def bgcreate(self):return self.call('ui_bg_create',TOKEN,STATE,1)
    def bgdestroy(self):return self.call('ui_bg_destroy',TOKEN,STATE,1)

def build_receipt(directory):
    code,symbols=compile_bg(directory)
    receipt=object_details((directory/'bg.o').read_bytes(),code)
    receipt['compiler']=subprocess.check_output(['clang','--version'],text=True).strip()
    receipt['flags']=FLAGS+['-fno-jump-tables','-fstack-usage']
    receipt['stack_usage']=(directory/'bg.su').read_text().replace(str(directory),'TEMP')
    receipt['heap_baseline_bytes']=1868
    receipt['bg_composed_delta']=len(code)-1868
    receipt['abi_bytes']={'UiBg':176,'Window':16,'Background':44,'BgConfig':360,'BgTemplate':28}
    return receipt
if __name__=='__main__':
    import json
    with tempfile.TemporaryDirectory(prefix='bg-receipt-') as d:print(json.dumps(build_receipt(Path(d)),indent=2))
