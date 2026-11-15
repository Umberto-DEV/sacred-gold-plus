#!/usr/bin/env python3
"""Attribute native move getters in exact r4 EN/IT without emitting game bytes.

Optional Work Party CSV is a subordinate observation: authenticate its runtime
and neutrality separately. Isolated execution exercises the real native switch
and one type-icon predicate, not the whole graphics pipeline or game lifetime.
"""
import argparse
from collections import Counter
import csv
import gzip
import hashlib
import json
from pathlib import Path
import struct
import sys

import ndspy.narc
import ndspy.rom
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB, UC_PROT_ALL, UC_HOOK_CODE
from unicorn.arm_const import (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2,
    UC_ARM_REG_R3, UC_ARM_REG_R4, UC_ARM_REG_R5, UC_ARM_REG_R6, UC_ARM_REG_R7,
    UC_ARM_REG_R8, UC_ARM_REG_R9, UC_ARM_REG_R10, UC_ARM_REG_R11,
    UC_ARM_REG_SP, UC_ARM_REG_LR, UC_ARM_REG_PC, UC_ARM_REG_CPSR)

REPO = Path(__file__).resolve().parents[4]
NONE = 0xFFFFFFFF
MAX_PP, ATTR = 0x0207332C, 0x02073314
PP_LR, CHILD_LR, TYPE_LR = 0x0224EF7D, 0x0207333D, 0x022688DD
CTX, OLD, NEW, STACK, RETURN = 0x02300000,0x02310000,0x02320000,0x023EF000,0x023EFF00
SAVED = (UC_ARM_REG_R4,UC_ARM_REG_R5,UC_ARM_REG_R6,UC_ARM_REG_R7,
         UC_ARM_REG_R8,UC_ARM_REG_R9,UC_ARM_REG_R10,UC_ARM_REG_R11)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def need(ok, reason):
    if not ok:
        raise ValueError(reason)


def bl(site, encoded):
    need(len(encoded)==4,'BL extent')
    hi,lo=struct.unpack('<HH',encoded)
    need(hi&0xF800==0xF000 and lo&0xF800==0xF800,'not a Thumb-1 BL')
    delta=((hi&0x7FF)<<12)|((lo&0x7FF)<<1)
    if delta&0x400000:delta-=0x800000
    return (site+4+delta)&0xFFFFFFFF


def classify(events, table):
    rows=[{k:int(v) for k,v in e.items()} for e in events]
    need(len(table)==7488,'expected 468 move records')
    need(len(rows)<=16384 and len({e['event'] for e in rows})==len(rows),'event budget/identity')
    by_id={e['event']:e for e in rows}
    native=[e for e in rows if e['site'] in (MAX_PP,ATTR)]
    groups=Counter();frames={};paired=set()
    for e in native:
        need(e['complete']==1 and e['mode']==31 and e['entry_cpsr']&63==63
             and e['exit_cpsr']&63==63,'incomplete/non-System-Thumb native span')
        need(0<e['entry_order']<e['exit_order'] and 0<=e['first_frame']<=e['last_frame'],
             'native chronology')
        move=e['arg0'];need(0<=move<468,'move outside qualified table')
        if e['site']==MAX_PP and e['lr']==PP_LR:
            need(e['parent']==NONE,'unexpected observed maxPP parent')
            expected=(table[16*move+6]+table[16*move+6]*min(e['arg1'],3)//5)&255
            need(e['result']==expected,'native maxPP value')
            key='GetBattlerVar.max_pp'
        elif e['site']==ATTR and e['lr']==CHILD_LR:
            need(e['parent'] in by_id,'missing maxPP parent')
            parent=by_id[e['parent']]
            need(parent['site']==MAX_PP and parent['lr']==PP_LR and
                 e['arg1']==5 and e['arg0']==parent['arg0'] and
                 parent['entry_order']<e['entry_order']<e['exit_order']<parent['exit_order'] and
                 parent['first_frame']<=e['first_frame']<=e['last_frame']<=parent['last_frame'],
                 'wrong maxPP/attribute ancestry')
            need(parent['event'] not in paired,'duplicate maxPP child');paired.add(parent['event'])
            need(e['result']==table[16*move+6],'native PP-base value')
            key='GetMoveMaxPP.attribute5'
        elif e['site']==ATTR and e['lr']==TYPE_LR:
            need(e['parent']==NONE and e['arg1']==3,'wrong type-icon caller/attribute')
            need(e['result']==table[16*move+4],'native type value')
            key='BattleInput_LoadFightMenuText.type'
        else:
            raise ValueError('unattributed native getter caller')
        groups[key]+=1;frames.setdefault(key,[]).append(e['first_frame'])
    need(groups and groups['GetBattlerVar.max_pp']==len(paired)==groups['GetMoveMaxPP.attribute5']
         and groups['BattleInput_LoadFightMenuText.type']>0,'missing consumer or PP child')
    return {'native_spans':len(native),'groups':dict(groups),'frames':frames,
            'limits':['No observed parent means no instrumented parent, not no caller.',
                      'Native caller windows are separately checked in the exact ROM.',
                      'CSV cannot authenticate its producer; no CPU-time or lifetime claim.']}


def isolated(nds, table):
    uc=Uc(UC_ARCH_ARM,UC_MODE_THUMB)
    for a,n in ((0x02000000,0x400000),(0x01FF8000,0x8000),(0x027E0000,0x10000)):
        uc.mem_map(a,n,UC_PROT_ALL)
    for section in nds.loadArm9().sections:
        uc.mem_write(section.ramAddress,bytes(section.data))
    overlay=nds.loadArm9Overlays([12])[12]
    uc.mem_write(overlay.ramAddress,bytes(overlay.data))
    members=ndspy.narc.NARC(nds.getFileByName('a/0/1/1')).files
    loads=[];predicate_stop=[]
    def load(_uc,_address,_size,_user):
        move=uc.reg_read(UC_ARM_REG_R0);dest=uc.reg_read(UC_ARM_REG_R1)
        need(0<=move<468 and STACK-256<=dest<=STACK-16,'native transport ABI')
        loads.append(move);uc.mem_write(dest,bytes(members[move]))
        uc.reg_write(UC_ARM_REG_PC,uc.reg_read(UC_ARM_REG_LR)|1)
    def stop(_uc,address,_size,_user):
        predicate_stop.append(address);uc.emu_stop()
    uc.hook_add(UC_HOOK_CODE,load,begin=0x020733B0,end=0x020733B0)
    for address in (0x022688DC,0x02268910):
        uc.hook_add(UC_HOOK_CODE,stop,begin=address,end=address)
    def regs(r0,r1,r2):
        for r,v in ((UC_ARM_REG_R0,r0),(UC_ARM_REG_R1,r1),(UC_ARM_REG_R2,r2),
                    (UC_ARM_REG_R3,0),(UC_ARM_REG_SP,STACK),(UC_ARM_REG_LR,RETURN|1)):
            uc.reg_write(r,v)
    cases=0
    # Execute the actual function entry and native switch, not just its case body.
    for battler in range(4):
        for index in range(4):
            for move in (1,261,467):
                for ups in (0,1,2,3,4,255):
                    mon=CTX+0x2D40+0xC0*battler
                    uc.mem_write(mon+0x0C+2*index,struct.pack('<H',move))
                    uc.mem_write(mon+0x30+index,bytes([ups]))
                    regs(CTX,battler,39+index);saved=tuple(0xA0000000+i for i in range(8))
                    for r,v in zip(SAVED,saved):uc.reg_write(r,v)
                    loads.clear();uc.emu_start(0x0224EDE1,RETURN,count=10000)
                    pp=table[move*16+6];expected=(pp+pp*min(ups,3)//5)&255
                    need(uc.reg_read(UC_ARM_REG_PC)==RETURN and uc.reg_read(UC_ARM_REG_SP)==STACK
                         and uc.reg_read(UC_ARM_REG_CPSR)&32 and uc.reg_read(UC_ARM_REG_R0)==expected
                         and tuple(uc.reg_read(r) for r in SAVED)==saved and loads==[move],
                         'GetBattlerVar dispatch/value/ABI mismatch')
                    cases+=1
    predicates=[]
    # The graphics continuation is not simulated: stop immediately after the
    # real getter returns, or at the compiled skip target.
    for old,new in ((0,0),(1,1),(261,0),(0,261),(1,261),(261,1),(1,467)):
        uc.mem_write(OLD,struct.pack('<H',old));uc.mem_write(NEW,struct.pack('<H',new))
        uc.mem_write(STACK+8,struct.pack('<I',NEW));regs(0,0,0)
        uc.reg_write(UC_ARM_REG_R4,OLD);uc.reg_write(UC_ARM_REG_R5,NEW)
        loads.clear();predicate_stop.clear();uc.emu_start(0x022688CB,RETURN,count=10000)
        take=new!=old and new!=0
        need(predicate_stop==[0x022688DC if take else 0x02268910]
             and loads==([new] if take else []),'changed/nonzero predicate mismatch')
        if take:need(uc.reg_read(UC_ARM_REG_R0)==table[new*16+4],'native type result mismatch')
        predicates.append({'old':old,'new':new,'calls_getter':take})
    return {'max_pp_dispatch_cases':cases,'battlers':4,'ids':[39,40,41,42],
            'type_predicate_cases':predicates,
            'limits':['Synthetic context and NARC transport; actual installed instructions.',
                      'Type window only, not full graphics execution or allocation lifetime.']}


def inspect(path,language,trace=None):
    raw=Path(path).read_bytes();identity={'bytes':len(raw),'sha256':sha(raw)}
    target=json.loads((REPO/'source/distribution/game-1.3.2-r4.json').read_text())['targets'][language]
    need(language in ('EN','IT') and all(identity[k]==target[k] for k in identity),'wrong exact r4 identity')
    nds=ndspy.rom.NintendoDSRom(raw);overlay=nds.loadArm9Overlays([12])[12]
    image=bytes(overlay.data);base=overlay.ramAddress
    def read(a,n):
        need(base<=a and a+n<=base+len(image),'overlay interval')
        return image[a-base:a-base+n]
    need(bl(0x0224EF78,read(0x0224EF78,4))==MAX_PP and
         bl(0x022688D8,read(0x022688D8,4))==ATTR,'wrong native caller BL')
    main=nds.loadArm9()
    def main_read(address,n):
        matches=[s for s in main.sections if s.ramAddress<=address
                 and address+n<=s.ramAddress+len(s.data)]
        need(len(matches)==1,'native ARM9 section')
        s=matches[0];return bytes(s.data[address-s.ramAddress:address-s.ramAddress+n])
    need(bl(0x02073338,main_read(0x02073338,4))==ATTR,'wrong maxPP child BL')
    yoff,ylen=struct.unpack_from('<II',raw,0x50)
    entries=[struct.unpack_from('<8I',raw,off) for off in range(yoff,yoff+ylen,32)]
    entries=[e for e in entries if e[0]==12];need(len(entries)==1,'overlay12 record')
    entry=entries[0];fat=struct.unpack_from('<I',raw,0x48)[0]
    physical=struct.unpack_from('<II',raw,fat+entry[6]*8)
    need(entry[1]==base and entry[6]==overlay.fileID,'raw/ndspy overlay mapping')
    # Validate the switch's signed halfword entries; values are data, not code.
    for case in range(39,43):
        offset=struct.unpack('<h',read(0x0224EE02+2*case,2))[0]
        need(0x0224EE04+offset==0x0224EF6A,'unexpected native switch target')
    windows={name:{'start':a,'end':b,'overlay_offset':a-base,'sha256':sha(read(a,b-a))}
             for name,a,b in (('GetBattlerVar',0x0224EDE0,0x0224F168),
                              ('BattleInput_LoadFightMenuText',0x0226885C,0x02268A64))}
    archive=nds.getFileByName('a/0/1/1');members=ndspy.narc.NARC(archive).files
    need(len(members)>=468 and all(len(m)==16 for m in members[:468]),'move records')
    table=b''.join(members[:468])
    result={'schema':1,'rom':identity,'language':language,'overlay12':{'ram':base,
        'file_id':overlay.fileID,'decoded_bytes':len(image),'decoded_sha256':sha(image),
        'stored_start':physical[0],'stored_end':physical[1],
        'compressed_bytes':entry[7]&0xFFFFFF,'flags':entry[7]>>24},
        'native_arm9_window':{'start':0x02073300,'bytes':184,'sha256':sha(main_read(0x02073300,184))},
        'native_windows':windows,'isolated':isolated(nds,table)}
    if trace:
        data=Path(trace).read_bytes()
        if str(trace).endswith('.gz'):data=gzip.decompress(data)
        result['trace']=classify(list(csv.DictReader(data.decode().splitlines())),table)
        result['trace']['sha256']=sha(data)
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--rom',required=True);p.add_argument('--language',choices=('EN','IT'),required=True)
    p.add_argument('--trace',help='authenticated Work Party CSV or lossless .gz')
    p.add_argument('--json',type=Path);args=p.parse_args()
    try:
        result=inspect(args.rom,args.language,args.trace);out=json.dumps(result,indent=2)+'\n'
        if args.json:
            with args.json.open('x') as f:f.write(out)
        print(out,end='');return 0
    except (ValueError,OSError,KeyError,struct.error) as exc:
        print('native attribution rejected: %s'%exc,file=sys.stderr);return 1


if __name__=='__main__':
    raise SystemExit(main())
