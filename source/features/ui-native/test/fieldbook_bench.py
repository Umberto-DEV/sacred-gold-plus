"""Compiled successor hooks at the conditional B6 base; never installs a ROM."""
import importlib.util
import struct
import subprocess
from pathlib import Path
from heap_bench import FLAGS, SOURCE, STACK, REGS, IME
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_ARM, UC_HOOK_CODE
from unicorn.arm_const import *

CODE, STATE, LABELS, TEMPLATE = 0x023D4000, 0x023D7E00, 0x023D7C40, 0x023D7B10
STOP, MENU, FIELD, TASK = 0x023B0000, 0x022A0000, 0x022A1000, 0x022A2000
CONTROL_TASK, CONTROL, TM, ENV, SYS = 0x022A2100, 0x022A2200, 0x022A2300, 0x022A2400, 0x021D110C

def compile_fieldbook(directory, scaffold=False, mutation=None):
    directory=Path(directory)
    body=(SOURCE/'features/ui-native/fieldbook.c').read_text() if not scaffold else '''
void fieldbook_create(void *m){(void)m;}
void fieldbook_frame(void *t,void *m){(void)t;(void)m;}
int fieldbook_touch(void *m){(void)m;return 1;}
void fieldbook_dpad(void *m){(void)m;}
void fieldbook_focus(void **s,unsigned i){(void)s;(void)i;}
int fieldbook_task_input(void *t){(void)t;return 0;}
int fieldbook_launch(void *t){(void)t;return 0;}
int fieldbook_return(void *t){(void)t;return 0;}
'''
    if mutation:
        old,new=mutation;assert old in body;body=body.replace(old,new,1)
    src=directory/'fieldbook.c';src.write_text(body);obj=directory/'fieldbook.o'
    subprocess.run(['clang',*FLAGS,'-fno-jump-tables','-fstack-usage','-I',str(SOURCE/'features/ui-native'),'-c',str(src),'-o',str(obj)],check=True,capture_output=True)
    spec=importlib.util.spec_from_file_location('fieldbook_loader',SOURCE/'features/options/tools/carica_text.py')
    loader=importlib.util.module_from_spec(spec);spec.loader.exec_module(loader)
    entries=('fieldbook_create','fieldbook_frame','fieldbook_touch','fieldbook_dpad',
             'fieldbook_focus','fieldbook_task_input','fieldbook_launch','fieldbook_return')
    result=loader.load_text(obj.read_bytes(),CODE,entries=entries)
    assert len(result[0]) <= 3072, "Fieldbook exceeds conditional B6 capacity"
    assert all(result[1][n]&1 and CODE<=result[1][n]&~1<CODE+len(result[0]) for n in entries),'loaded Thumb callbacks'
    return result

class FieldbookBench:
    def __init__(self,compiled,memory=()):
        self.code,self.symbols=compiled;self.u=Uc(UC_ARCH_ARM,UC_MODE_ARM)
        for a,n in [(0x02000000,0x400000),(0x027E0000,0x4000),(0x04000000,0x2000),(0x05000000,0x1000)]:self.u.mem_map(a,n)
        for a,data in memory:self.u.mem_write(a,data)
        self.u.mem_write(CODE,self.code);self.u.reg_write(UC_ARM_REG_CPSR,0x5f);self.put(IME,1)
        self.put(0x021D4158,FIELD);self.put(FIELD+0xD8,CONTROL_TASK);self.put(CONTROL_TASK+16,CONTROL)
        self.put(CONTROL,0x100);self.put(CONTROL+4,TASK);self.put(CONTROL+8,FIELD)
        self.put(TASK+16,MENU);self.put(TASK+20,self.symbols['fieldbook_frame'])
        self.put(MENU+8,TASK);self.put(MENU+12,FIELD+0xD0);self.put(MENU+16,FIELD)
        self.put(MENU+20,3);self.put(FIELD+0xD2,2,1);self.put(TM+24,FIELD);self.put(TM+12,ENV)
        for i in range(7):self.put(MENU+0x470+8*i,1,1)
        for i in range(9):self.put(MENU+0x390+4*i,0x022B0000+i*0x100)
        self.events=[];self.allocation_failure=False;self.string_failure=False;self.put(MENU+0x460,0x022C0000);self.u.mem_write(MENU+0x464,bytes([5,11,21,9,2,4]));self.put(MENU+0x46A,0x174,2);self.put(MENU+0x46C,0x022D0000);self.put(LABELS,2,2);self.u.mem_write(LABELS+2,struct.pack('<6H',0x12D,0x13B,0x12F,0x12A,0x127,0xffff))
        self.u.mem_write(STATE+240,b'fieldbook-canary');self.u.mem_write(CODE+3072,b'fieldbook-guard!')
        self.instructions=0;self.low=STACK;self.metrics=[]
        self.u.hook_add(UC_HOOK_CODE,self.hook)
    def put(self,a,v,n=4):self.u.mem_write(a,int(v&((1<<(8*n))-1)).to_bytes(n,'little'))
    def get(self,a,n=4):return int.from_bytes(self.u.mem_read(a,n),'little')
    def ret(self,v=0):self.u.reg_write(UC_ARM_REG_R0,v);self.u.reg_write(UC_ARM_REG_PC,self.u.reg_read(UC_ARM_REG_LR))
    def hook(self,u,a,n,d):
        self.instructions+=1;self.low=min(self.low,u.reg_read(UC_ARM_REG_SP))
        if a==STOP:u.emu_stop();return
        if CODE<=a<CODE+len(self.code):return
        args=[u.reg_read(r) for r in [UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3]]
        assert u.reg_read(UC_ARM_REG_SP)%8==0,f'ABI8 {a:08x}'
        self.events.append((a,tuple(args)))
        if a in (0x0205064C,0x02050650):self.ret(self.get(args[0]+(24 if a==0x0205064C else 12)));return
        if a==0x0201F988:self.ret(self.get(args[0]+16));return
        if a==0x02026354:
            self.put(0x022D1000,32,2);self.put(0x022D1004,0xB6F8D2EC)
            self.ret(0 if self.string_failure else 0x022D1000);return
        if a==0x02002F30:self.ret(30);return
        if a==0x0201D40C:
            if not self.allocation_failure:
                stack=u.reg_read(UC_ARM_REG_SP);tail=[self.get(stack+4*i) for i in range(5)]
                self.u.mem_write(args[1],struct.pack('<I6BHI',args[0],args[2],args[3],*tail[:4],tail[4],0x022D2000))
            self.ret();return
        if a==0x0201D978:
            p=self.get(args[0]+12);w=self.get(args[0]+7,1);h=self.get(args[0]+8,1)
            self.u.mem_write(p,bytes([args[1]*17])*(w*h*32));self.ret();return
        if a in (0x0201D578,0x0201D520,0x020200FC,0x02026380,0x0225A320,
                 0x0203C460,0x0203DF64,0x021E636C,0x0203DFB4,0x020505C0):self.ret();return
        if a==0x0200FB5C:self.ret(1);return
        if a in (0x0205C6D4,0x021F6B00):self.ret(0);return
        if a==0x021F6B10:self.ret(1);return
        if a in (0x0225B4D8,0x0225B404):self.ret(1);return
        if a in (0x0225BC84,0x0200604C,0x02024B78,0x020CFD70,0x0225B398,0x0225B4AC):self.ret();return
        if a==0x0225C170:self.ret(args[1]);return
        if a==0x0203C47C:self.ret(7);return
        raise AssertionError(f'undeclared seam {a:08x}')
    def call(self,name,*args):
        seeds=[0x62340000+i for i in range(8)]
        for r,v in zip(REGS,seeds):self.u.reg_write(r,v)
        self.u.reg_write(UC_ARM_REG_SP,STACK);self.u.reg_write(UC_ARM_REG_LR,STOP)
        for r,v in zip([UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3],args):self.u.reg_write(r,v)
        start=self.instructions;self.low=STACK;self.u.mem_write(STACK-2048,b'\xa5'*32)
        self.u.emu_start(self.symbols[name],STOP,count=2000000)
        assert self.u.reg_read(UC_ARM_REG_PC)==STOP
        assert self.u.reg_read(UC_ARM_REG_SP)==STACK and [self.u.reg_read(r) for r in REGS]==seeds
        assert self.u.reg_read(UC_ARM_REG_CPSR)&0xDF==0x5F and self.get(IME)==1
        assert bytes(self.u.mem_read(STATE+240,16))==b'fieldbook-canary'
        assert bytes(self.u.mem_read(CODE+3072,16))==b'fieldbook-guard!'
        assert bytes(self.u.mem_read(STACK-2048,32))==b'\xa5'*32
        self.metrics.append((name,STACK-self.low,self.instructions-start))
        return self.u.reg_read(UC_ARM_REG_R0)


class FieldbookTouchFrameBench(FieldbookBench):
    """Explicit native frame-to-touch dispatch seam, not native scheduling."""
    def __init__(self, compiled):
        self.fade_done=True;self.moving=False
        super().__init__(compiled)
    def hook(self,u,a,n,d):
        if a==0x0225A320:
            # Native ov27 frame delegates touch with its menu (second argument).
            u.reg_write(UC_ARM_REG_R0,u.reg_read(UC_ARM_REG_R1))
            u.reg_write(UC_ARM_REG_PC,self.symbols['fieldbook_touch']);return
        if a==0x0200FB5C:self.ret(int(self.fade_done));return
        if a==0x0205C6D4:self.ret(int(self.moving));return
        super().hook(u,a,n,d)
