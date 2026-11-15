#!/usr/bin/env python3
"""Read back resident ANIM v4, its retired roots and lexical reference candidates.

The scan covers initialized ARM9/ARM7 sections and decoded overlay images only.
It is not a reachable-code disassembler: aligned words and A32/Thumb encodings
can be data or the wrong ISA. No game bytes or personal input paths are emitted.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import struct
import sys

import ndspy.rom

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[3]
sys.path.insert(0,str(HERE))
from rileggi_anim4 import Arm9RO,immagine_overlay,leggi_overlay,tabelle

BASE, END, CODE_END = 0x023D8B00,0x023D8F00,0x023D8DF0
CODE_SHA='06a031fd71b3225409845bea7abeca77c66227d0c266ba8dbfbca38eba3eb18b'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def need(ok,reason):
    if not ok:raise ValueError(reason)


def domain(target):
    if target<CODE_END:return 'code'
    if target<BASE+0x300:return 'canary'
    if target<BASE+0x340:return 'tables'
    if target<BASE+0x380:return 'state'
    return 'slots'


def references(component,base,data):
    """Lexical candidates, preserving data-pointer low bits. Never reachability."""
    found=[]
    def add(offset,kind,target):
        if BASE<=target<END:
            found.append({'component':component,'source':base+offset,'offset':offset,
                          'kind':kind,'target':target,'domain':domain(target),
                          'source_inside_owner':BASE<=base+offset<END})
    for offset in range((-base)%4,len(data)-3,4):
        word=struct.unpack_from('<I',data,offset)[0]
        add(offset,'aligned_u32',word)
        # Conditional A32 B/BL only. BLX immediate, register/computed targets,
        # short Thumb B and unaligned words are explicitly outside this scan.
        if word>>28!=15 and word&0x0E000000==0x0A000000:
            delta=(word&0xFFFFFF)<<2
            if delta&0x2000000:delta-=0x4000000
            add(offset,'arm_branch_candidate',(base+offset+8+delta)&0xFFFFFFFF)
    for offset in range((-base)%2,len(data)-3,2):
        hi,lo=struct.unpack_from('<HH',data,offset)
        if hi&0xF800==0xF000 and lo&0xF800==0xF800:
            delta=((hi&0x7FF)<<12)|((lo&0x7FF)<<1)
            if delta&0x400000:delta-=0x800000
            add(offset,'thumb_bl',(base+offset+4+delta)&0xFFFFFFFF)
    return found


def check_block(block,build):
    build=Path(build);blob=(build/'blob.bin').read_bytes()
    need(len(blob)==752 and sha(blob)==CODE_SHA,'unqualified v4 payload')
    can=(build/'canarino.bin').read_bytes();tab=(build/'tab_u.bin').read_bytes();par=(build/'par.bin').read_bytes()
    need(len(can)==16 and len(tab)==len(par)==32,'v4 data geometry')
    state=bytearray(64);state[1]=0x5A
    need(bytes(block)==blob+can+tab+par+state+bytes(128),'v4 owner code/data/state mismatch')
    return {'address':BASE,'bytes':len(block),'sha256':sha(block),'code_bytes':752,
            'code_sha256':sha(blob),'canary_bytes':16,'tables_bytes':64,
            'state_bytes':64,'slots_bytes':128,'state_guard_address':BASE+0x341,
            'source_sha256':{str(p.relative_to(REPO)):sha(p.read_bytes()) for p in (
                HERE.parent/'sorgenti/anim_blob4.c',HERE.parent/'sorgenti/anim_idle4.c',
                HERE.parent/'sorgenti/sgp_anim4.h',HERE.parent/'sorgenti/sgp_chunk.h',
                HERE/'compila_anim4.py',HERE/'carica_text.py')}}


def thumb_bl(site,encoded):
    hi,lo=struct.unpack('<HH',encoded)
    need(hi&0xF800==0xF000 and lo&0xF800==0xF800,'not a Thumb BL')
    delta=((hi&0x7FF)<<12)|((lo&0x7FF)<<1)
    if delta&0x400000:delta-=0x800000
    return (site+4+delta)&0xFFFFFFFF


def inspect(path,language,build,scan=True):
    arm=Arm9RO(path);raw=arm.raw;identity={'bytes':len(raw),'sha256':sha(raw)}
    target=json.loads((REPO/'source/distribution/game-1.3.2-r4.json').read_text())['targets'][language]
    need(language in ('EN','IT') and all(identity[k]==target[k] for k in identity),'wrong exact r4 identity')
    result={'schema':1,'rom':identity,'language':language,
            'v4':check_block(arm.leggi(BASE,1024),build)}
    result['v4']['rom_offset']=arm.off(BASE,1024)
    nds=ndspy.rom.NintendoDSRom(raw);decoded=nds.loadArm9Overlays([12])
    ov=decoded[12];entry=leggi_overlay(raw,tabelle(raw),12)
    image=immagine_overlay(raw,entry)
    need(image==bytes(ov.data),'overlay12 independent decoder disagreement')
    read=lambda a,n:image[a-ov.ramAddress:a-ov.ramAddress+n]
    pointer=struct.unpack('<I',read(0x0226200C,4))[0]
    maintenance=REPO/'source/sgp12/build/manutenzione'
    wrapper=(maintenance/'copie.bin').read_bytes()
    man=json.loads((maintenance/'manifesto.json').read_text())['parti']['copie']
    need(arm.leggi(man['base'],len(wrapper))==wrapper,'installed copy barrier mismatch')
    need(pointer==man['simboli']['sgp_idle_copie']==0x023DBC9B,'v4 task root not redirected to copy barrier')
    need(read(0x02262032,4)==bytes.fromhex('206a0421')
         and thumb_bl(0x02262036,read(0x02262036,4))==0x020087A4,
         'v4 stop root not restored to native instructions')
    current=REPO/'source/sgp12/build/anim2'
    v5=json.loads((current/'manifesto.json').read_text());v5blob=(current/'blob.bin').read_bytes()
    need(arm.leggi(0x023DB500,len(v5blob))==v5blob,'installed ANIM2 code mismatch')
    v5symbols=v5['simboli']
    calls={0x02262016:'sgp_stop_testa',0x0225DC8A:'sgp_avvia_tutti',0x0223EBD8:'sgp_avvia_cattura'}
    for site,name in calls.items():
        need(thumb_bl(site,read(site,4))==int(v5symbols[name],16)&~1,'wrong current ANIM2 root')
    literals=[struct.unpack_from('<I',wrapper,i)[0] for i in range(0,144,4)]
    for literal in (0x023DB72D,0x023DB621,0x023DBBC0):need(literal in literals,'copy barrier literal mismatch')
    result['roots']={'old_task_symbol':0x023D8BE5,'old_stop_symbol':0x023D8BD3,
        'task_literal_site':0x0226200C,'current_task_pointer':pointer,
        'old_stop_site':0x02262032,'native_continuation':0x020087A4,
        'wrapper':{'address':man['base'],'bytes':len(wrapper),'sha256':sha(wrapper)},
        'current_ANIM2_code_sha256':sha(v5blob),'current_task':0x023DB72D,
        'current_enable_getter':0x023DB621,'copy_counter':0x023DBBC0}
    result['overlay12']={**entry,'decoded_sha256':sha(image)}
    if scan:
        external=[];internal=0;components=[]
        def visit(name,base,data):
            nonlocal internal
            refs=references(name,base,data)
            external.extend(r for r in refs if not r['source_inside_owner'])
            internal+=sum(r['source_inside_owner'] for r in refs)
            components.append({'name':name,'ram':base,'bytes':len(data),'sha256':sha(data)})
        for cpu in (9,7):
            for i,s in enumerate(getattr(nds,'loadArm%d'%cpu)().sections):
                visit('arm%d.section.%d'%(cpu,i),s.ramAddress,bytes(s.data))
            overlays=getattr(nds,'loadArm%dOverlays'%cpu)()
            for oid,o in sorted(overlays.items()):
                visit('arm%d.overlay.%d'%(cpu,oid),o.ramAddress,bytes(o.data))
        result['scan']={'component_count':len(components),'initialized_bytes':sum(c['bytes'] for c in components),
            'components':components,'internal_candidates':internal,'external_candidates':external,
            'external_by_kind':dict(Counter(r['kind'] for r in external)),
            'external_to_code':[r for r in external if r['domain']=='code']}
    result['limits']=['Lexical candidates, not an exhaustive call graph or reachability proof.',
        'Initialized native sections/overlays only; excludes BSS, archives, heap, unaligned pointers, computed calls, short Thumb branches and A32 BLX immediate.',
        'A32 encodings can be Thumb instructions or data; review every candidate.',
        'Two retired roots do not make the whole 1024-byte owner reclaimable; state has separate consumers.',
        'No new runtime activation or global-inactivity observation.']
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--rom',required=True);p.add_argument('--language',choices=('EN','IT'),required=True)
    p.add_argument('--build',type=Path,default=REPO/'source/sgp12/build/anim')
    p.add_argument('--no-scan',action='store_true',help='check owner and roots only')
    p.add_argument('--json',type=Path);args=p.parse_args()
    try:
        result=inspect(args.rom,args.language,args.build,not args.no_scan);out=json.dumps(result,indent=2)+'\n'
        if args.json:
            with args.json.open('x') as f:f.write(out)
        print(out,end='');return 0
    except (ValueError,OSError,KeyError,struct.error) as exc:
        print('ANIM attribution rejected: %s'%exc,file=sys.stderr);return 1


if __name__=='__main__':
    raise SystemExit(main())
