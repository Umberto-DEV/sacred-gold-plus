#!/usr/bin/env python3
"""Qualify five finite ARM/Thumb returns using owned synthetic programs.

No ROM, compiler, FS implementation, controller or timing model is used.
Every prediction is computed before its uninterrupted Unicorn CPU17 run.
"""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import struct


HERE=Path(__file__).resolve()
s=importlib.util.spec_from_file_location('qualified_mixed_narc',HERE.parents[1]/'test/arm_thumb_narc_oracle.py')
A=importlib.util.module_from_spec(s);s.loader.exec_module(A)
need=A.need


def kernel(target,cpsr):
    entry,stop,sp=0x20073fe,0x22f0180,0x23fcffc
    ret,word=A.RETURNS[target];pages={}
    def put(a,b):
        for base in range(a&~4095,(a+len(b)+4095)&~4095,4096):pages.setdefault(base,bytearray(b'\xa5'*4096))
        A.A.F.put(pages,a,b)
    delta=target-((entry+4)&~3);need(delta%4==0 and -(1<<22)<=delta<1<<22,'owned BLX range')
    call=struct.pack('<HH',0xf000|((delta>>12)&0x7ff),0xe800|((delta>>1)&0x7ff))
    thumb={entry:call,entry+4:bytes.fromhex('0720'),entry+6:bytes.fromhex('00bd')}
    for a,b in thumb.items():put(a,b)
    prefix=[]
    if word==0x18bd8010 or word==0xe8bd8010:prefix=[0xe92d4010]
    elif word==0xe8bd80f8:prefix=[0xe92d40f8]
    branch=target+4*len(prefix)
    offset=ret-(branch+8);need(offset%4==0,'owned ARM branch alignment')
    prefix.append(0xea000000|((offset>>2)&0xffffff))
    put(target,struct.pack('<'+'I'*len(prefix),*prefix));put(ret,struct.pack('<I',word))
    put(sp-64,b'\xa5'*64+struct.pack('<I',stop|1));put(stop,b'\0'*4)
    regs=[0x10000000+i*0x10101 for i in range(13)]+[sp,stop|1,cpsr]
    return dict(entry_pc=entry,entry_regs=regs,pages={a:bytes(b)for a,b in pages.items()}),thumb,((target,4*len(prefix)),(ret,4)),stop


def execute(f,thumb,spans,stop):
    # Imported only by explicit qualification, never by CPU-free raw verification.
    from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM,UC_HOOK_CODE,UC_HOOK_MEM_READ,UC_HOOK_MEM_WRITE
    from unicorn.arm_const import UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3,UC_ARM_REG_R4,UC_ARM_REG_R5,UC_ARM_REG_R6,UC_ARM_REG_R7,UC_ARM_REG_R8,UC_ARM_REG_R9,UC_ARM_REG_R10,UC_ARM_REG_R11,UC_ARM_REG_R12,UC_ARM_REG_SP,UC_ARM_REG_LR,UC_ARM_REG_CPSR,UC_ARM_REG_PC
    rr=[UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3,UC_ARM_REG_R4,UC_ARM_REG_R5,UC_ARM_REG_R6,UC_ARM_REG_R7,UC_ARM_REG_R8,UC_ARM_REG_R9,UC_ARM_REG_R10,UC_ARM_REG_R11,UC_ARM_REG_R12,UC_ARM_REG_SP,UC_ARM_REG_LR,UC_ARM_REG_CPSR]
    code={a:(4,False)for base,n in spans for a in range(base,base+n,4)}
    code.update({a:(len(b),True)for a,b in thumb.items()})
    u=Uc(UC_ARCH_ARM,UC_MODE_ARM);need(u.ctl_get_cpu_model()==17,'qualified CPU17')
    for base,b in sorted(f['pages'].items()):u.mem_map(base,4096);u.mem_write(base,b)
    u.reg_write(UC_ARM_REG_CPSR,f['entry_regs'][15])
    for reg,value in zip(rr[:15],f['entry_regs'][:15]):u.reg_write(reg,value)
    flow=[];reads=[];stores=[]
    def step(uc,pc,n,_):
        need(pc in code and code[pc]==(n,bool(uc.reg_read(UC_ARM_REG_CPSR)&32)),'owned kernel fetch width/state')
        need(bytes(uc.mem_read(pc,n))==A.A.F.read(f['pages'],pc,n),'owned kernel code bytes')
        flow.append(dict(pc=pc,regs=[uc.reg_read(r)for r in rr]));need(len(flow)<=64,'owned CPU instruction cap')
    def read(uc,_,address,n,value,user):
        reads.append(dict(pc=uc.reg_read(UC_ARM_REG_PC),address=address,bytes=n,hex=bytes(uc.mem_read(address,n)).hex()))
    def write(uc,_,address,n,value,user):
        stores.append(dict(pc=uc.reg_read(UC_ARM_REG_PC),address=address,bytes=n,before=bytes(uc.mem_read(address,n)).hex(),value=value&((1<<(8*n))-1)))
    u.hook_add(UC_HOOK_CODE,step);u.hook_add(UC_HOOK_MEM_READ,read);u.hook_add(UC_HOOK_MEM_WRITE,write)
    u.emu_start(f['entry_pc']|int(bool(f['entry_regs'][15]&32)),stop,timeout=1000000,count=65)
    need(u.reg_read(UC_ARM_REG_PC)==stop,'owned kernel stop')
    return dict(flow=flow,reads=reads,stores=stores,returned=[u.reg_read(r)for r in rr],stop_pc=stop,
                pages={a:bytes(u.mem_read(a,4096))for a in f['pages']})


def qualify():
    rows=[]
    for target in A.RETURNS:
        for flags in(0x2000003f,0xb000003f):
            f,thumb,spans,stop=kernel(target,flags)
            prediction=A.run(f,spans,stop,cap=64,thumb_code=thumb)
            # Independent hard postconditions precede CPU execution.
            need(prediction['returned'][0]==7 and prediction['returned'][13]==f['entry_regs'][13]+4 and
                 prediction['returned'][15]==(flags&0x3fffffff)|0x20,'owned semantic postcondition')
            actual=execute(f,thumb,spans,stop)
            for key in('flow','reads','stores','returned','stop_pc','pages'):
                need(actual[key]==prediction[key],'owned mixed differential '+key)
            rows.append(dict(API=hex(target),return_pc=hex(A.RETURNS[target][0]),entry_cpsr=hex(flags),
                instructions=len(actual['flow']),reads=len(actual['reads']),stores=len(actual['stores']),
                returned=actual['returned'],flow_sha256=hashlib.sha256(json.dumps(actual['flow'],sort_keys=True).encode()).hexdigest(),
                full16_every_pc=True,all_pages=True,uninterrupted_CPU=True))
    # A false NE return must not read an unmapped stack, pop or exchange ISA.
    pc,stop=0x20d82b0,0x22f0180
    offset=(stop-(pc+4+8))>>2
    words=struct.pack('<II',0x18bd8010,0xea000000|(offset&0xffffff))
    page=bytearray(b'\xa5'*4096);page[pc&4095:(pc&4095)+8]=words
    f=dict(entry_pc=pc,entry_regs=[0]*13+[0x2300000,0x1101,0x4000001f],
           pages={pc&~4095:bytes(page),stop&~4095:bytes(4096)})
    spans=((pc,8),);prediction=A.A.run(f,spans,stop,cap=4)
    need(prediction['reads']==prediction['stores']==[]and prediction['returned']==f['entry_regs'],'false NE no access/register/ISA change')
    actual=execute(f,{},spans,stop)
    for key in('flow','reads','stores','returned','stop_pc','pages'):
        need(actual[key]==prediction[key],'owned false NE differential '+key)
    rows.append(dict(API='owned_false_NE',return_pc=hex(pc),instructions=len(actual['flow']),
                     no_stack_access=True,unchanged_registers=True,ARM_state_preserved=True))
    return dict(schema='native-narc-interworking-qualification-v1',CPU_model=17,
        scope='Owned synthetic kernels only; not original FS bodies or ARM946 hardware timing/CP15 state',
        source_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest()for p in(HERE,Path(A.__file__),Path(A.A.__file__))},cases=rows)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--json',type=Path,required=True);a=p.parse_args()
    try:
        source=HERE.parents[3];out=a.json.resolve()
        need(source!=out and source not in out.parents,'private qualification output outside source')
        need(not a.json.exists()and not a.json.is_symlink(),'fresh qualification output')
        receipt=qualify()
        with a.json.open('x')as f:json.dump(receipt,f,indent=2);f.write('\n')
    except(ValueError,OSError)as e:p.exit(2,str(e)+'\n')
    print('Eleven owned kernels: interworking/full16/all pages and false NE without stack access PASS')


if __name__=='__main__':main()
