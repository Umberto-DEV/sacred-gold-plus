"""Compiled resident Bridge probes. Class A seams dependencies explicitly.
The production ELF loader remains authoritative; no ROM installation occurs.
"""
import importlib.util
import struct
import subprocess
from pathlib import Path
from heap_bench import FLAGS, SOURCE, STACK, REGS, IME
from module_bench import instruction_set
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_ARM, UC_HOOK_CODE, UC_HOOK_MEM_WRITE
from unicorn.arm_const import *

CODE, STOP = 0x023CB800, 0x023CF000
PHYSICAL, SLOT = 0x023D6E10, 0x023D7210
TOKEN, BOOT, SEEDS = 0x023D7B20, 0x023D7B48, 0x023D7B60
ROOT, MANAGER, FIELD, PROCESS, ARGS = 0x02290000, 0x022A4000, 0x022A4100, 0x022A4300, 0x022A4400
SAVE, OPTIONS, FONT = 0x02300000, 0x02300100, 0x022B0000
CONTEXT = ROOT + 4848


def loader():
    spec = importlib.util.spec_from_file_location('bridge_loader', SOURCE/'features/options/tools/carica_text.py')
    result = importlib.util.module_from_spec(spec); spec.loader.exec_module(result)
    return result


def compile_bridge(directory, scaffold=False, mutation=None):
    directory = Path(directory)
    physical_obj = directory/'physical.o'
    binds = {'SLOT': SLOT, 'SYSTEM': 0x021D110C, 'KEYINPUT': 0x04000130,
             'SHARED': 0x027FFFA8, 'MAPPING': 0x0201A5E9, 'LID': 0x0200110D}
    subprocess.run(['clang', *FLAGS, *[f'-DSGP_PHYSICAL_{k}_ADDR={v}' for k,v in binds.items()],
                    '-c', str(SOURCE/'features/ui-native/physical.c'), '-o', str(physical_obj)],
                   check=True, capture_output=True)
    physical = loader().load_text(physical_obj.read_bytes(), PHYSICAL)
    assert len(physical[0]) <= 1024
    defines = [f'-DUI_BRIDGE_PHYSICAL_{name.upper()}={physical[1]["physical_"+name]}'
               for name in ('activate', 'deactivate')]
    body = ('unsigned ui_bridge_settings_init(void *m,unsigned *p){(void)m;(void)p;return 0;}\n'
            'unsigned ui_bridge_guide_init(void *m,unsigned *p){(void)m;(void)p;return 0;}\n'
            'unsigned ui_bridge_main(void *m,unsigned *p){(void)m;(void)p;return 0;}\n'
            'unsigned ui_bridge_exit(void *m,unsigned *p){(void)m;(void)p;return 0;}\n') if scaffold else (SOURCE/'features/ui-native/bridge.c').read_text()
    if mutation:
        before, after = mutation; assert before in body; body = body.replace(before, after, 1)
    source = directory/'composed.c'
    source.write_text('#include "persistent.c"\n#include "module.c"\n'+body)
    obj = directory/'bridge.o'
    subprocess.run(['clang', *FLAGS, '-fno-jump-tables', '-fstack-usage',
                    '-DUI_PERSISTENT_RESIDENT_TOKEN_ADDRESS=0x023D7B20u', *defines,
                    '-I', str(SOURCE/'features/ui-native'), '-c', str(source), '-o', str(obj)],
                   check=True, capture_output=True)
    return loader().load_text(obj.read_bytes(), CODE), physical


class BridgeBench:
    """Bridge CPU execution with declared allocator/module/dynamic seams.
    Lifecycle observations are asserted independently by the tests. Class B
    replaces these service seams with pinned native allocation/FS bodies.
    """
    def __init__(self, compiled, role=1):
        (self.code,self.symbols),self.physical = compiled
        self.u=Uc(UC_ARCH_ARM, UC_MODE_ARM)
        for p,n in ((0x02000000,0x400000),(0x027E0000,0x4000),(0x027FF000,0x1000),(0x04000000,0x1000)):
            self.u.mem_map(p,n)
        self.u.mem_write(CODE,self.code);self.u.mem_write(PHYSICAL,self.physical[0])
        self.u.reg_write(UC_ARM_REG_CPSR,0x5f);self.put(IME,1)
        self.events=[];self.role=role;self.alloc_failure=False;self.alloc_hold=False
        self.module_result=1;self.dynamic_result={0:1,1:0,2:3};self.activated=False
        self.put(0x021D4158,FIELD);self.put(FIELD,PROCESS);self.put(PROCESS+4,MANAGER)
        self.put(FIELD+12,SAVE);self.put(FIELD+0x10C,0);self.put(SAVE+0x2302C,OPTIONS-SAVE-16)
        self.put(ARGS,0xA5962CF0);self.put(ARGS+4,OPTIONS);self.put(ARGS+8,FIELD+0x10C)
        self.put(0x0211188C,0x02111890);self.put(0x0211192C,FONT);self.put(0x02111944,1,1)
        self.put(FONT,1);self.put(FONT+4,0x02026111)
        init='ui_bridge_settings_init' if role==1 else 'ui_bridge_guide_init'
        self.u.mem_write(MANAGER,struct.pack('<10I',self.symbols[init],self.symbols['ui_bridge_main'],
             self.symbols['ui_bridge_exit'],0xFFFFFFFF,1,0,ARGS if role==1 else 0,0,0xA6A6A6A6,0x69696969))
        self.u.mem_write(0x020FA354,bytes(self.u.mem_read(MANAGER,16)))
        self.u.mem_write(0x023D7B10,struct.pack('<4I',self.symbols['ui_bridge_guide_init'],
             self.symbols['ui_bridge_main'],self.symbols['ui_bridge_exit'],0xFFFFFFFF))
        self.fetch=instruction_set(self.u,[v for k,v in self.symbols.items() if not k.startswith("$")],[(CODE,CODE+len(self.code))])
        self.fetch |= instruction_set(self.u,[v for k,v in self.physical[1].items() if not k.startswith("$")],[(PHYSICAL,PHYSICAL+len(self.physical[0]))])
        self.u.hook_add(UC_HOOK_CODE,self.hook)
        self.instructions=0;self.low=STACK
    def put(self,p,v,n=4):self.u.mem_write(p,int(v & ((1<<(n*8))-1)).to_bytes(n,'little'))
    def get(self,p,n=4):return int.from_bytes(self.u.mem_read(p,n),'little')
    def ret(self,v=0):self.u.reg_write(UC_ARM_REG_R0,v);self.u.reg_write(UC_ARM_REG_PC,self.u.reg_read(UC_ARM_REG_LR))
    def hook(self,u,p,n,d):
        self.instructions+=1;sp=u.reg_read(UC_ARM_REG_SP);self.low=min(self.low,sp)
        if p==STOP:u.emu_stop();return
        name=next((k for k,v in self.symbols.items() if v&~1==p),None)
        args=[u.reg_read(r) for r in (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3)]
        if name=='ui_persistent_alloc':
            assert sp%8==0 and args[:2]==[TOKEN,5036]
            self.events.append(('allocate',args[2]))
            if self.alloc_hold:self.put(TOKEN,0x48504955);self.put(TOKEN+8,args[2]);self.ret(0)
            elif self.alloc_failure:self.ret(0)
            else:
                self.u.mem_write(ROOT,bytes(5036));self.u.mem_write(TOKEN,struct.pack('<10I',0x31504955,TOKEN,args[2],ROOT,5036,0,0,0,0,0));self.ret(ROOT)
            return
        if name=='ui_module_init':self.put(ROOT,0x32444D55);self.put(ROOT+4,ROOT);self.ret(1);return
        if name=='ui_module_begin':
            self.events.append(('begin',args[2],args[3]));self.put(ROOT+8,1);self.put(ROOT+12,args[2]);self.put(ROOT+16,args[3]);self.put(ROOT+20,args[1]);self.ret(1);return
        if p==0x02028EA8:self.ret(OPTIONS);return
        if p==0x0203E344:self.ret(SAVE);return
        if p==0x020D3A90:self.ret(0);return
        assert p in self.fetch,f'unexpected instruction {p:08x}'
    def call(self,name):
        seeds=[0x45670000+i for i in range(8)]
        for r,v in zip(REGS,seeds):self.u.reg_write(r,v)
        self.u.reg_write(UC_ARM_REG_SP,STACK);self.u.reg_write(UC_ARM_REG_LR,STOP)
        self.u.reg_write(UC_ARM_REG_R0,MANAGER);self.u.reg_write(UC_ARM_REG_R1,MANAGER+20)
        self.u.emu_start(self.symbols[name],STOP,count=1000000)
        assert self.u.reg_read(UC_ARM_REG_PC)==STOP
        assert self.u.reg_read(UC_ARM_REG_SP)==STACK and [self.u.reg_read(r) for r in REGS]==seeds
        assert self.u.reg_read(UC_ARM_REG_CPSR)&0xDF==0x5F and self.get(IME)==1
        return self.u.reg_read(UC_ARM_REG_R0)


def compile_scene_stub(directory, wrong_backing=False):
    """Authored test Scene only: actual checked heap38 create/app/free/destroy.
    No font, BG, job, transaction or asset implementation is impersonated.
    The native services underneath heap.c execute in the Class B harness.
    """
    source=Path(directory)/'scene_stub.c';obj=Path(directory)/'scene_stub.o'
    source.write_text('''#include "heap.c"
#include "bridge.h"
/* Authored test protocol: flags bit0 chooses terminal HOLD on refusal.
 * Sixteen real allocations exercise every existing acquired ledger entry. */
unsigned test_scene_init(UiSceneContext *c,unsigned *step) {
 if(c->abi!=UI_SCENE_CONTEXT_ABI)return UI_SCENE_HOLD;
 if(*step)return UI_SCENE_READY;
 UiHeap *h=(UiHeap *)c->heap_token;
 if(!ui_heap38_create(h,c->role==1?0x30000:0x40000,c->generation))return UI_SCENE_CLOSE;
 unsigned *a=ui_alloc38(h,48,0);
 if(!a){if(!ui_heap38_destroy(h))return UI_SCENE_HOLD;return UI_SCENE_CLOSE;}
 a[9]=c->options;a[10]=c->generation;a[11]=0x31495553;c->app=(unsigned)a;
 for(unsigned i=1;i<16;++i)if(!ui_alloc38(h,32,i&1))return UI_SCENE_CLOSE;
 ++*step;return UI_SCENE_MORE;
}
unsigned test_scene_main(UiSceneContext *c,unsigned *step) {
 if(!c->app)return UI_SCENE_HOLD;
 ++*step;return *step<3?UI_SCENE_MORE:UI_SCENE_CLOSE;
}
unsigned test_scene_exit(UiSceneContext *c,unsigned *step) {
 if(!*step){++*step;return UI_SCENE_MORE;}
 UiHeap *h=(UiHeap *)c->heap_token;
 if(c->app){
  for(unsigned i=0;i<16;++i)if(h->acquired[i]&&h->acquired[i]!=c->app)
   if(!ui_free38(h,(void *)h->acquired[i]))return UI_SCENE_HOLD;
  if(!ui_free38(h,(void *)c->app))return UI_SCENE_HOLD;
  c->app=0;
 }
 if(!h->magic)return UI_SCENE_EXITED;
 if(!ui_heap38_destroy(h))return c->flags&1?UI_SCENE_HOLD:UI_SCENE_MORE;
 return UI_SCENE_EXITED;
}
''')
    if wrong_backing:
        source.write_text(source.read_text().replace('c->role==1?0x30000:0x40000','c->role==1?0x40000:0x30000'))
    subprocess.run(['clang',*FLAGS,'-fno-jump-tables','-I',str(SOURCE/'features/ui-native'),
                    '-c',str(source),'-o',str(obj)],check=True,capture_output=True)
    code,symbols=loader().load_text(obj.read_bytes(),0x021E5900)
    return code+bytes((-len(code))%4+4096),symbols
