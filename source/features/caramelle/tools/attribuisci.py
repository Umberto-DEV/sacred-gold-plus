#!/usr/bin/env python3
"""Attribute the current Rare Candy helper and bounded native caller in r4 EN/IT."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import shutil
import sys
import ndspy.rom
from unicorn.arm_const import UC_ARM_REG_R4

sys.path.insert(0,str(Path(__file__).resolve().parent))
from rileggi_caramelle import VistaArm9,decodifica_bl
from carica_text import load_text

SOURCE=Path(__file__).resolve().parents[3]
BASE,HOOK,PARENT=0x023DAC00,0x02081E96,0x02081C50
CODE_SHA='9acfd1fdbcb72f0f9d28efc0042e0ca46fac4229ce569ad786eadfd2ad2f264f'
PARENT_SHA='f4bfaf599f81577817b6a6dc51e71ac81f39cdc7e29ceceb4f44ab4ac77eb466'
BASES={'EN':('281c2d68e442479e679d8b7e36566ade614d236151c65c9684bad6985461827d',127104144),
       'IT':('7b61646c627eb67cd991dbc33d68519edd69395468ea8b326e867fe98e62d077',131906120)}
RETAILS={'EN':'65f02a56842b75aa92d775d56d657a56fe3fa993550b04dc20704ab82d760105',
         'IT':'013d04f5512b01ad98735a5f850dc039f0ee80bc57035b3a10e8b650be690ce1'}


def sha(data):return hashlib.sha256(data).hexdigest()


def need(ok,why):
    if not ok:raise ValueError(why)


def isolated(rom):
    path=SOURCE/'features/caramelle/test/banco.py'
    spec=importlib.util.spec_from_file_location('current_candy_bench',path)
    B=importlib.util.module_from_spec(spec);spec.loader.exec_module(B)
    machine=B.Banco(rom)  # real ROM bytes, never a substituted bundle
    rows=[]
    cases=(('normal',{},1,6,6,4,0,6),('evolution',{'species':157},1,6,6,32,9,0),
        ('item-none',{'item':0},1,6,6,32,0,0),('context',{'context':8},1,6,6,32,0,0),
        ('quantity-zero',{},0,6,6,32,0,1),('count',{'slot':3},1,2,6,32,0,3),
        ('capacity',{'slot':3},1,6,2,32,0,3),('slot-255',{'slot':255},1,6,6,32,0,3),
        ('boundary',{'slot':5},1,6,6,4,0,6),('null-args',{'args_nullo':True},1,6,6,32,0xEE,0),
        ('null-pm',{'pm_nullo':True},1,6,6,32,0xEE,0),('null-bag',{},1,6,6,32,0,0),
        ('null-party',{},1,6,6,32,0,1))
    for name,params,quantity,count,capacity,state,action,ncalls in cases:
        for mode in ('hook','direct'):
            machine.prepara(**params)
            if name=='null-bag':machine.uc.mem_write(B.ARGS+B.A_BAG,bytes(4))
            if name=='null-party':machine.uc.mem_write(B.ARGS+B.A_PARTY,bytes(4))
            machine.quantita,machine.conteggio,machine.capienza=quantity,count,capacity
            result=machine.esegui() if mode=='hook' else machine.esegui_blob()
            need(result['stato']==state and result['azione']==action and len(result['chiamate'])==ncalls,'gate '+name+'/'+mode)
            for register,expected in B.CALLEE.items():
                if mode=='direct' and register==UC_ARM_REG_R4:expected=0 if params.get('pm_nullo') else B.PM
                need(result['callee'][register]==expected,'callee-saved '+name+'/'+mode)
            if state==4:
                calls=result['chiamate']
                need([c[0] for c in calls]==list(B.NATIVE.values()),'native sequence')
                need(calls[0][1:]==(B.BAG,50,12) and calls[1][1]==calls[2][1]==B.PARTY,'quantity/Party arguments')
                need(calls[3][1:3]==(B.PM+B.PM_WIN34,1) and calls[4][1:]==(B.PM,33,1)
                     and calls[5][1:3]==(B.SPRITE,0),'UI arguments')
                need(struct.unpack('<I',machine.uc.mem_read(B.ARGS+B.A_SEARCH,4))[0]==0,'move-search reset')
            rows.append(dict(case=name,entry=mode,state=state,action=action,calls=result['chiamate'],
                stack_depth=machine.last_stack_depth,writes=[[hex(a),n] for a,n in machine.last_writes]))
    return rows


def analyze(rom,base,retail,build,language):
    pin=json.loads((SOURCE/'distribution/game-1.3.2-r4.json').read_text())['targets'][language]
    records=[];windows={};pool={};ranges=[]
    for label,path,digest,size in (('retail',retail,RETAILS[language],134217728),
            ('base11',base,*BASES[language]),('r4',rom,pin['sha256'],pin['bytes'])):
        raw=Path(path).read_bytes();need(len(raw)==size and sha(raw)==digest,'exact '+label+' input')
        main=ndspy.rom.NintendoDSRom(raw).loadArm9()
        def rd(a,n):
            for section in main.sections:
                offset=a-section.ramAddress
                if 0<=offset and offset+n<=len(section.data):return bytes(section.data[offset:offset+n])
            raise ValueError('ndspy range')
        windows[label]=rd(PARENT,600);pool[label]=rd(PARENT+600,20)
        if label!='r4':need(sha(windows[label])==PARENT_SHA,'native parent provenance')
        if label=='r4':
            view=VistaArm9(path)
            for a,n in ((BASE,256),(HOOK,6),(PARENT,600),(PARENT+600,20)):
                block=view.prendi(a,n);need(block==rd(a,n),'raw/ndspy')
                ranges.append(dict(ram=hex(a),rom_offset=hex(view.posto(a,n)),bytes=n,sha256=sha(block)))
            need(decodifica_bl(view,HOOK)==BASE and view.prendi(HOOK+4,2)==bytes.fromhex('38bd'),'BL/pop installed hook')
            obj=(build/'caramelle.o').read_bytes()
            blob,symbols=load_text(obj,BASE,('sgp_caramelle_gancio','sgp_caramelle_decidi'))
            need(len(blob)==192 and sha(blob)==CODE_SHA and blob==(build/'blob.bin').read_bytes(),'rebuilt object identity')
            need(decodifica_bl(view,BASE+4)|1==symbols['sgp_caramelle_decidi'] and symbols['sgp_caramelle_gancio']==BASE|1,'compiled/installed entries')
            can=b''.join(struct.pack('<I',0xCA5A1600|i) for i in range(4))
            need((build/'canarino.bin').read_bytes()==can and view.prendi(BASE,256)==blob+bytes(48)+can,'complete owner')
            manifest=json.loads((build/'manifesto.json').read_text())
            need(int(manifest['indirizzi']['base'],16)==BASE and
                 int(manifest['indirizzi']['canarino'],16)==BASE+240 and
                 int(manifest['indirizzi']['gancio_arm9'],16)==HOOK and
                 manifest['indirizzi']['blocco_byte']==256,'build address contract')
            need(manifest['blob']['byte']==192 and manifest['blob']['sha256']==CODE_SHA and
                 all(int(manifest['simboli'][name],16)==symbols[name] for name in
                     ('sgp_caramelle_gancio','sgp_caramelle_decidi')),'build metadata/object mismatch')
            need(manifest['sorgente']['sha256']==sha((SOURCE/'features/caramelle/sorgenti/caramelle.c').read_bytes()),'source drift')
            for field,relative in (('header_sha256','sorgenti/sgp_caramelle.h'),
                    ('loader_sha256','tools/carica_text.py'),('builder_sha256','tools/compila.py')):
                need(manifest.get(field)==sha((SOURCE/'features/caramelle'/relative).read_bytes()),
                     field+' drift or old build; rerun compila.py')
            compiler=Path(shutil.which(manifest['comando'][0]) or manifest['comando'][0]).resolve()
            need(manifest.get('compilatore_eseguibile_sha256')==sha(compiler.read_bytes()),'compiler identity drift')
            del view
        records.append(dict(input=label,sha256=digest,bytes=size,parent_sha256=sha(windows[label]),continuation_pool_sha256=sha(pool[label])))
        del raw,main
    # Retail IT has a different input-system base; code identity does not imply data identity.
    for label,blob in pool.items():
        system=0x021D10AC if language=='IT' and label=='retail' else 0x021D110C
        need(struct.unpack('<5I',blob)==(0xBD382005,0xC67,system,0x5DC,0x654),
             'revision-specific continuation/literal pool')
    need(pool['base11']==pool['r4'],'inherited continuation/literal pool drift')
    for label in ('retail','base11'):
        changed=[PARENT+i for i,(a,b) in enumerate(zip(windows[label],windows['r4'])) if a!=b]
        need(changed==list(range(HOOK,HOOK+6)),'parent delta beyond hook')
    need(windows['r4'][:2]==bytes.fromhex('38b5'),'parent frame')
    offset=struct.unpack_from('<h',windows['r4'],0x18+6*2)[0]
    need(PARENT+0x1A+offset==0x02081E54,'state6 PC-relative table')
    need(struct.unpack_from('<I',pool['r4'],4)[0]==0xC67 and struct.unpack_from('<I',pool['r4'],16)[0]==0x654,'parent state/args offsets')
    return dict(language=language,inputs=records,ranges=ranges,build=manifest,
        source_header_sha256=sha((SOURCE/'features/caramelle/sorgenti/sgp_caramelle.h').read_bytes()),
        loader_sha256=sha((SOURCE/'features/caramelle/tools/carica_text.py').read_bytes()),
        retail_it_system_literal_diff=language=='IT',execution=isolated(rom),limits=[
            'Current compiler rebuild matches bytes; historical compiler executable is not authenticated.',
            'Execution begins at the hook or helper, not native parent entry or natural gameplay.',
            'Six native transports model quantity/Party/UI; no actual expanded-Bag quantity proof.',
            'Only the bounded 600+20 native window is attributed, not all HGSS source.',
            'Raw mapping shares project layout validation; ndspy is separate.'])


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    for name in ('rom','base','retail','build','json'):ap.add_argument('--'+name,type=Path,required=True)
    ap.add_argument('--language',choices=('EN','IT'),required=True)
    a=ap.parse_args();report=analyze(a.rom,a.base,a.retail,a.build,a.language)
    # Build manifests can contain local command paths. The public result only needs file hashes and flags.
    build=report['build'];command=build.pop('comando')
    compiler=Path(shutil.which(command[0]) or command[0]).resolve()
    report['compiler_executable_sha256']=sha(compiler.read_bytes())
    report['compiler_flags']=command[1:command.index('-c')]
    build.pop('funzione',None)
    a.json.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(language=a.language,cases=len(report['execution']),status='PASS')))


if __name__=='__main__':main()
