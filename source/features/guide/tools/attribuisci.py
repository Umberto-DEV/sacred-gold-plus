#!/usr/bin/env python3
"""Attribute the 96-byte Summary hint patch in exact EN/IT final images."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys
import ndspy.rom
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB, UC_HOOK_CODE, UC_HOOK_MEM_WRITE
from unicorn.arm_const import (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R4,UC_ARM_REG_R5,
    UC_ARM_REG_R6,UC_ARM_REG_R7,UC_ARM_REG_R8,UC_ARM_REG_R9,UC_ARM_REG_R10,
    UC_ARM_REG_R11,UC_ARM_REG_SP,UC_ARM_REG_LR,UC_ARM_REG_PC,UC_ARM_REG_CPSR)

sys.path.insert(0,str(Path(__file__).resolve().parent))
from rileggi_guida import _Immagine, ORIGINALE_SHA, SPENTA_SHA, LINGUA_FIRMA

REPO=Path(__file__).resolve().parents[4]
PATCH,TEXT=0x01FF8A1A,0x01FF9B10
P,SYS=0x01FF9FC0,0x021D110C
ENTRY,RETURN,STACK=0x01FF8880,0x01000000,0x027EF000
S,A,BG,MAP,FONT,FD,STATE=(0x02300000+i*0x1000 for i in range(7))
SAVED=(UC_ARM_REG_R4,UC_ARM_REG_R5,UC_ARM_REG_R6,UC_ARM_REG_R7,
       UC_ARM_REG_R8,UC_ARM_REG_R9,UC_ARM_REG_R10,UC_ARM_REG_R11)
BASES={'EN':('281c2d68e442479e679d8b7e36566ade614d236151c65c9684bad6985461827d',127104144),
       'IT':('7b61646c627eb67cd991dbc33d68519edd69395468ea8b326e867fe98e62d077',131906120)}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def need(ok,why):
    if not ok:
        raise ValueError(why)


def branch(site,data):
    need(len(data)==2,'Thumb B extent')
    word=struct.unpack('<H',data)[0];need(word&0xF800==0xE000,'Thumb B opcode')
    off=word&0x7FF
    if off&0x400:off-=0x800
    return site+4+2*off


def inspect_patch(blob,tail,epilogue):
    need(len(blob)==96 and sha(blob)==SPENTA_SHA,'exact installed patch')
    need(struct.unpack_from('<3H',blob)==(0x2001,0x62F8,0x6338),'badge/pending stores')
    need(branch(PATCH+6,blob[6:8])==0x01FF8B18,'patch branch')
    need(blob[8:]==bytes.fromhex('c046')*44,'unexecuted NOP fill')
    need(branch(0x01FF8B18,tail)==0x01FF894A,'continuation branch')
    need(epilogue==bytes.fromhex('280009b0f0bd'),'shared return epilogue')


def isolated(main):
    """Execute installed guide_main; synthetic resources, no helper stubs."""
    uc=Uc(UC_ARCH_ARM,UC_MODE_THUMB)
    for a,n in ((0x01FF8000,0x8000),(0x02000000,0x400000),(0x04000000,0x2000),
                (0x06200000,0x20000),(0x027E0000,0x10000),(RETURN,0x1000)):
        uc.mem_map(a,n)
    for section in main.sections:
        uc.mem_write(section.ramAddress,bytes(section.data))
    def w(a,v):uc.mem_write(a,struct.pack('<I',v))
    def h(a,v):uc.mem_write(a,struct.pack('<H',v))
    def setup():
        for a,n in ((P,64),(S,0x800),(A,0x40),(BG,0x168),(MAP,2048),
                    (FONT,0xBC),(FD,0x80),(0x0620F800,2048)):
            uc.mem_write(a,bytes(n))
        w(S,BG);w(S+0x22C,A);uc.mem_write(S+0x7BC,b'\x01');w(STATE,2)
        w(SYS,0x020885DD);w(SYS+4,S)
        for off in (0x3C,0x48,0x4C,0x60,0x64):w(SYS+off,0)
        w(0x04001000,0x1F00);h(0x04001008,0x1F10);w(0x04000240,0x82848381)
        h(0x04000244,0x8382);uc.mem_write(0x04000246,b'\x8B');h(0x04000248,0x8280)
        w(BG,19);w(BG+0xB8,MAP);w(BG+0xBC,2048);w(BG+0xCC,0x20000100)
        w(0x0211188C,FONT);w(FONT+0x9C,FD);w(FD+4,0x02026069)
    def call():
        seen={'patch_hits':0,'writes':[],'instructions':0}
        def code(cpu,a,n,unused):
            need(0x01FF8880<=a<TEXT,'execution escaped installed Plus code')
            seen['instructions']+=1
            if a==PATCH:seen['patch_hits']+=1
        def write(cpu,access,a,n,value,unused):
            need((STACK-128<=a and a+n<=STACK) or (P<=a and a+n<=P+64)
                 or (0x04001000<=a and a+n<=0x04001004),'unexpected write-set')
            seen['writes'].append((a,n))
        hooks=[uc.hook_add(UC_HOOK_CODE,code),uc.hook_add(UC_HOOK_MEM_WRITE,write)]
        expected=[0xA5000000+i for i in range(8)]
        for reg,val in zip(SAVED,expected):uc.reg_write(reg,val)
        uc.reg_write(UC_ARM_REG_R0,S);uc.reg_write(UC_ARM_REG_R1,STATE)
        uc.reg_write(UC_ARM_REG_SP,STACK);uc.reg_write(UC_ARM_REG_LR,RETURN|1)
        try:uc.emu_start(ENTRY|1,RETURN,count=10000)
        finally:
            for hook in hooks:uc.hook_del(hook)
        need(uc.reg_read(UC_ARM_REG_PC)==RETURN and uc.reg_read(UC_ARM_REG_SP)==STACK
             and uc.reg_read(UC_ARM_REG_CPSR)&32
             and [uc.reg_read(r) for r in SAVED]==expected,'guide_main return/ABI')
        seen['result']=uc.reg_read(UC_ARM_REG_R0)
        seen['state']=list(struct.unpack('<16I',uc.mem_read(P,64)))
        seen['stack_write_depth']=max((STACK-a for a,n in seen['writes'] if STACK-128<=a<STACK),default=0)
        seen['writes_outside_stack']=sorted({hex(a) for a,n in seen['writes'] if not STACK-128<=a<STACK})
        del seen['writes']
        return seen
    cases=[]
    # Single-change controls distinguish resources, settling, visibility and tile availability.
    for name,modify in (('idle',lambda:None),('keys',lambda:w(SYS+0x48,1)),
            ('heap',lambda:w(BG,18)),('unsettled',lambda:h(BG+6,16)),
            ('display-off',lambda:w(0x04001000,0)),('map-tile',lambda:h(MAP+2*0x255,1)),
            ('gpu-tile',lambda:h(0x0620F800+2*0x255,1)),('wrong-phase',lambda:w(STATE,1))):
        setup();modify();seen=call();active=name=='idle'
        need(seen['patch_hits']==int(active) and seen['result']==0 and
             seen['state'][11:13]==[int(active)]*2,'hint gate '+name)
        need(seen['state'][1:3]==[0,0],'unexpected context/heap allocation '+name)
        cases.append(dict(case=name,**seen))
    # Existing badge flags permit the opening transition, without allocating/drawing a badge.
    for name,off,value,expected in (('start',0x3C,8,1),('touch',0x64,1,1),
                                   ('start-with-key-blocker',0x48,1,0)):
        setup();call()
        if name.startswith('start'):w(SYS+0x3C,8)
        if name=='touch':
            h(SYS+0x60,176);h(SYS+0x62,152)
        w(SYS+off,value);seen=call()
        need(seen['result']==expected and seen['state'][4]==expected,'opening transition '+name)
        need(seen['state'][1:3]==[0,0],'opening transition allocated context')
        cases.append(dict(case=name,**seen))
    return cases


def analyze(base,rom,language):
    pin=json.loads((REPO/'source/distribution/game-1.3.2-r4.json').read_text())['targets'][language]
    records=[];windows=[];execution=None
    for label,path,digest,size in (('base11',base,*BASES[language]),('r4',rom,pin['sha256'],pin['bytes'])):
        raw=Path(path).read_bytes();need(len(raw)==size and sha(raw)==digest,'exact '+label+' input')
        image=_Immagine(raw);main=ndspy.rom.NintendoDSRom(raw).loadArm9()
        def read(a,n):
            for section in main.sections:
                k=a-section.ramAddress
                if 0<=k and k+n<=len(section.data):return bytes(section.data[k:k+n])
            raise ValueError('ndspy range')
        fields={};data={}
        for name,a,n in (('patch',PATCH,96),('text',TEXT,1098),('main',ENTRY,0x2A0),
                ('wrapper',0x01FF91F4,52),('root',0x02088424,8)):
            blob=image.b(a,n);need(blob==read(a,n),'raw/ndspy '+name);data[name]=blob
            fields[name]=dict(ram=hex(a),rom_offset=hex(image.off(a,n)),bytes=n,sha256=sha(blob))
        need(sha(data['patch'])==(ORIGINALE_SHA if label=='base11' else SPENTA_SHA),'patch state')
        need(sha(data['text'])==LINGUA_FIRMA[language],'language/text preservation')
        need(data['root']==struct.pack('<HHI',0x4B00,0x4718,0x01FF91F5),'native root to wrapper')
        need(data['wrapper'][:16]==bytes.fromhex('38b50c00084b984705002100fff73efb'),'wrapper entry to guide_main')
        if label=='r4':
            inspect_patch(data['patch'],image.b(0x01FF8B18,2),image.b(0x01FF894A,6))
            execution=isolated(main)
        records.append(dict(input=label,sha256=digest,bytes=size,ranges=fields));windows.append(data)
        del raw,image,main
    delta=[i for i,(a,b) in enumerate(zip(windows[0]['main'],windows[1]['main'])) if a!=b]
    need(delta and all(PATCH<=ENTRY+i<PATCH+96 for i in delta),'main delta outside patch')
    need(windows[0]['wrapper']==windows[1]['wrapper'],'wrapper changed')
    return dict(language=language,inputs=records,main_delta_bytes=len(delta),execution=execution,
        limits=['No original combined_guide compiler reconstruction.',
                'No natural Summary activation, panel rendering, save or visual claim.',
                'Synthetic resources/MMIO are host memory; no hardware transport.',
                'Two readers share project layout validation; ndspy is separate.'])


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--base',type=Path,required=True);ap.add_argument('--rom',type=Path,required=True)
    ap.add_argument('--language',choices=('EN','IT'),required=True);ap.add_argument('--json',type=Path,required=True)
    a=ap.parse_args();report=analyze(a.base,a.rom,a.language)
    a.json.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(language=a.language,cases=len(report['execution']),status='PASS')))


if __name__=='__main__':main()
