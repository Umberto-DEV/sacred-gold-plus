#!/usr/bin/env python3
"""Attribute exact Full-Bag gift code, generated keys and later script drift."""
import argparse
import gc
import hashlib
import importlib.util
import json
import mmap
from pathlib import Path
import shutil
import struct
import sys

SOURCE=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(SOURCE));sys.path.insert(0,str(Path(__file__).resolve().parent))
import applica_borsa as A
import rileggi_borsa as R
sys.path.insert(0,str(SOURCE/'features/caramelle/tools'))
from carica_text import load_text
from sgp131 import baseline,gifts_audit,legacy_scripts as L,gifts_scripts as G
import ndspy.code
import ndspy.fnt
import ndspy.narc

BASE=0x023DAD00
CODE_SHA='315f86bd89c49634d11bb7ef1c86746636d84af62b913a84ad2bc0b16ddf7b9e'
NATIVE=((0x0203FD6C,108),(0x0203FE2C,28),(0x0204E9D8,88),(0x0204EA88,88))
MOVED={(932,167):197,(932,357):413,(874,442):442,(237,1378):1384,
       (232,1505):1511,(232,1854):1860,(938,1705):1711,(938,1856):1862}
BASES={'EN':('281c2d68e442479e679d8b7e36566ade614d236151c65c9684bad6985461827d',127104144),
       'IT':('7b61646c627eb67cd991dbc33d68519edd69395468ea8b326e867fe98e62d077',131906120)}
RETAILS={'EN':'65f02a56842b75aa92d775d56d657a56fe3fa993550b04dc20704ab82d760105',
         'IT':'013d04f5512b01ad98735a5f850dc039f0ee80bc57035b3a10e8b650be690ce1'}


def sha(data):return hashlib.sha256(data).hexdigest()


def need(ok,why):
    if not ok:raise ValueError(why)


def build_code(directory):
    directory=Path(directory);manifest=json.loads((directory/'manifesto.json').read_text())
    code,symbols=load_text((directory/'borsa.o').read_bytes(),BASE,A.TRAMPOLINI.keys()|
        {'sgp_borsa_has_space','sgp_borsa_give_item'})
    need(len(code)==658 and sha(code)==CODE_SHA and code==(directory/'blob.bin').read_bytes(),'rebuilt ELF/code identity')
    need(manifest['sorgente']['sha256']==sha((SOURCE/'features/borsa/sorgenti/borsa.c').read_bytes())
         and manifest['intestazione']['sha256']==sha((SOURCE/'features/borsa/sorgenti/sgp_borsa.h').read_bytes()),'build source/header drift')
    for field,path in (('builder_sha256',Path(__file__).with_name('compila_borsa.py')),
            ('loader_sha256',SOURCE/'features/caramelle/tools/carica_text.py')):
        need(manifest.get(field)==sha(path.read_bytes()),field+' drift; rebuild')
    compiler=Path(shutil.which(manifest['comando'][0]) or manifest['comando'][0]).resolve()
    need(manifest.get('compilatore_eseguibile_sha256')==sha(compiler.read_bytes()),'compiler executable drift')
    canonical=json.loads((SOURCE/'sgp12/build/borsa/manifesto.json').read_text())
    need(manifest['blob']==canonical['blob'] and manifest['canarino']==canonical['canarino'],'build blob/canary metadata')
    need(manifest['indirizzi']==canonical['indirizzi'] and manifest['simboli']==canonical['simboli']
         and all(int(manifest['simboli'][n],16)==v for n,v in symbols.items()),'build address/symbol drift')
    can=b''.join(struct.pack('<I',0xCA5A1700|i) for i in range(4))
    need((directory/'canarino.bin').read_bytes()==can,'build canary')
    return code,can,dict(compiler=manifest['compilatore'],compiler_sha256=sha(compiler.read_bytes()),
        flags=manifest['comando'][1:manifest['comando'].index('-c')+1],
        source_sha256=manifest['sorgente']['sha256'],header_sha256=manifest['intestazione']['sha256'],
        symbols=manifest['simboli'])


def raw_archive(raw,name):
    """Read only the requested NitroFS archive and verify NARC extents two ways."""
    fntoff,fntsize,fatoff,fatsize=struct.unpack_from('<4I',raw,0x40)
    need(fntoff+fntsize<=len(raw) and fatoff+fatsize<=len(raw),'FNT/FAT bounds')
    fid=ndspy.fnt.load(raw[fntoff:fntoff+fntsize]).idOf(name)
    need(fid is not None and (fid+1)*8<=fatsize,'NitroFS file ID')
    start,end=struct.unpack_from('<II',raw,fatoff+8*fid)
    need(0<=start<end<=len(raw),'FAT file extent')
    archive=raw[start:end]
    need(archive[:4]==b'NARC' and struct.unpack_from('<IHH',archive,8)==(len(archive),16,3),'NARC header')
    magic,size,count=struct.unpack_from('<4sII',archive,16)
    need(magic==b'BTAF' and size==12+8*count,'BTAF')
    names=16+size;need(archive[names:names+4]==b'BTNF','BTNF')
    image=names+struct.unpack_from('<I',archive,names+4)[0]
    need(archive[image:image+4]==b'GMIF' and image+struct.unpack_from('<I',archive,image+4)[0]==len(archive),'GMIF')
    members=[];positions=[]
    for i in range(count):
        lo,hi=struct.unpack_from('<II',archive,28+8*i)
        need(0<=lo<=hi and image+8+hi<=len(archive),'member extent')
        members.append(archive[image+8+lo:image+8+hi]);positions.append(start+image+8+lo)
    need(members==[bytes(b) for b in ndspy.narc.NARC(archive).files],'raw/ndspy NARC member readback')
    return members,dict(file_id=fid,archive_bytes=len(archive),archive_sha256=sha(archive),
        members=count,member_rom_offsets=positions)


def image(path,label,digest,size,language):
    # Mapping avoids multiple complete heap copies of private cartridges.
    with Path(path).open('rb') as handle,mmap.mmap(handle.fileno(),0,access=mmap.ACCESS_READ) as raw:
        need(len(raw)==size and sha(raw)==digest,'exact '+label+' input')
        off,entry,ram,length=struct.unpack_from('<4I',raw,0x20)
        setting=struct.unpack_from('<I',raw,0x70)[0]
        main=ndspy.code.MainCodeFile(raw[off:off+length],ram,setting)
        view=gifts_audit.Arm9View(raw) if label in ('v4','r4') else None
        ranges=[]
        def read(address,n):
            blocks=[bytes(s.data[address-s.ramAddress:address-s.ramAddress+n]) for s in main.sections
                    if s.ramAddress<=address and address+n<=s.ramAddress+len(s.data)]
            need(len(blocks)==1,'ndspy ARM9 range')
            if view:
                need(blocks[0]==view.read(address,n),'raw/ndspy ARM9 mapping')
                ranges.append(dict(ram=hex(address),rom_offset=hex(view.offset(address,n)),bytes=n,sha256=sha(blocks[0])))
            return blocks[0]
        native=[read(a,n) for a,n in NATIVE]
        table_address=0x020FAC78 if label=='retail' and language=='IT' else 0x020FAD00
        entries=[struct.unpack('<I',read(table_address+4*c,4))[0] for c in (125,127)]
        data=dict(input=label,sha256=digest,bytes=size,native_sha256=[sha(b) for b in native],command_entries=entries,command_table=hex(table_address),ranges=ranges)
        if view:
            owner=read(BASE,2048);members,archive=raw_archive(raw,'a/0/1/2')
            data.update(owner_sha256=sha(owner),archive=archive,
                mapping=[dict(ram=hex(a),rom_offset=hex(o),bytes=n) for a,o,n in view.segments])
        else:owner=members=None
        del view
    return data,native,owner,members


def raw_sites(table,members):
    words=list(struct.unpack('<120I',table));keys=[w for w in words if w]
    need(len(keys)==110 and keys==sorted(set(keys)) and words[110:]==[0]*10,'installed table shape')
    found={};orphan=[]
    for key in keys:
        off,digest=key>>16,key&65535;candidates=[]
        for member,raw in enumerate(members):
            end=off+8
            if end>len(raw):continue
            opcode=struct.unpack_from('<H',raw,off)[0]
            if opcode in (125,127) and R._fnv16(raw[max(0,end-32):end])==digest:
                candidates.append((member,opcode,off,digest))
        need(len(candidates)<=1,'ambiguous installed key')
        if candidates:found[key]=candidates[0]
        else:orphan.append(key)
    return found,orphan


def offline(rom,v4,base,retail,build,scrcmd,language):
    code,can,compile_proof=build_code(build)
    commands=gifts_audit.load_commands(scrcmd)
    pin=json.loads((SOURCE/'distribution/game-1.3.2-r4.json').read_text())['targets'][language]
    vpin=next((h,n) for h,n in baseline.INPUT_SIZES.items() if baseline.INPUT_HASHES[h]==language)
    records=[];native={};old=final=owner0=owner1=None
    for label,path,digest,size in (('retail',retail,RETAILS[language],134217728),
            ('base11',base,*BASES[language]),('v4',v4,*vpin),('r4',rom,pin['sha256'],pin['bytes'])):
        record,windows,owner,members=image(path,label,digest,size,language)
        records.append(record);native[label]=windows
        need(record['command_entries']==([0x023DAD09,0x023DAD01] if owner else [0x0204E9D9,0x0204EA89]),'native/project command entries')
        if label=='v4':old,owner0=members,owner
        if label=='r4':final,owner1=members,owner
    need(all(w==native['retail'] for w in native.values()),'native caller/handler revision drift')
    signed,census_sha=A.leggi_censimento_firmato(SOURCE/'features/borsa/permissivi-1.2.tsv')
    rows,diag=A.genera_tabella(None,scrcmd,signed,{'cancelli':[]},archive=(old,records[2]['archive']['archive_bytes']))
    table=A.corpo_tabella(rows)
    expected=bytearray(2048);expected[:len(code)]=code
    struct.pack_into('<2I',expected,0x5E0,0x0204EA89,0x0204E9D9)
    expected[0x600:0x7E0]=table;expected[0x7F0:]=can
    need(owner0==owner1==bytes(expected),'complete reconstructed initial owner')
    found0,orphans0=raw_sites(table,old);found,orphans=raw_sites(table,final)
    need(len(found0)==110 and not orphans0 and len(found)==102 and len(orphans)==8,'expected exact revision key coverage')
    recipes=[]
    for member in (232,237,757,874,932,938):
        if member in L.MEMBERS:
            after=L.patch_member(bytes(old[member]),language,member,commands)
            independent=L.verify_member(bytes(old[member]),bytes(final[member]),language,member,commands)
            producer='legacy-scripts'
        else:
            after=G.patch_member(old[member],language,member,commands,G.load_recipe())
            independent=G.verify_member(old[member],final[member],commands,G.load_recipe());producer='gifts-scripts'
        need(after==final[member],'current member source recipe '+str(member))
        recipes.append(dict(member=member,producer=producer,before_sha256=sha(old[member]),after_sha256=sha(after),
            before_bytes=len(old[member]),after_bytes=len(after),independent_readback=independent))
    permissive,all_sites,parsed,_=A.censisci_archivio(final,records[3]['archive']['archive_bytes'],scrcmd)
    classified={(v['membro'],v['opcode'],v['offset'],v['impronta_gancio']) for v in permissive
                if (v['membro'],v['opcode'],v['offset']) not in R.NERI_R}
    need(len(classified)==112 and set(found.values())<=classified,'current classified coverage')
    by_key={v['chiave']:v for v in rows};drift=[]
    for key in orphans:
        before=by_key[key];member,off=before['membro'],before['offset'];new=MOVED[(member,off)];op=struct.unpack_from('<H',old[member],off)[0]
        args=struct.unpack_from('<3H',old[member],off+2)
        need(struct.unpack_from('<4H',old[member],off)==struct.unpack_from('<4H',final[member],new),'moved instruction/arguments')
        digest=R._fnv16(final[member][max(0,new+8-32):new+8]);newkey=(new<<16)|digest
        need(newkey not in by_key and (member,op,new,digest) in classified,'moved key remains outside table')
        drift.append(dict(member=member,opcode=op,old_offset=off,new_offset=new,
            old_key=hex(key),new_key=hex(newkey),arguments=args,
            producer='gifts-scripts' if member in (232,938) else 'legacy-scripts'))
    new_enigma=[v for v in all_sites if v['membro']==757 and v['opcode']==127]
    need(len(new_enigma)==2 and all((v['offset']<<16|v['impronta_gancio']) not in by_key for v in new_enigma),'intentional strict Enigma checks')
    proof=dict(inputs=records,compile=compile_proof,census_sha256=census_sha,
        metadata_sha256=commands.metadata_sha256,table_sha256=sha(table),table_generation=diag,
        initial_owner_sha256=sha(expected),v4_valid_keys=110,r4_valid_keys=102,r4_orphans=drift,
        current_classifier_count=112,strict_new_enigma=new_enigma,script_recipes=recipes)
    return proof,final,all_sites


def bench_module():
    path=SOURCE/'features/borsa/test/banco.py'
    spec=importlib.util.spec_from_file_location('installed_gift_bench',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def execution(rom,members,sites,drift):
    """Installed project/native handlers; seven variable/Bag transports remain models."""
    from types import SimpleNamespace
    from unicorn import UC_HOOK_CODE,UC_HOOK_MEM_WRITE
    from unicorn.arm_const import (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R4,UC_ARM_REG_SP,
        UC_ARM_REG_LR,UC_ARM_REG_PC,UC_ARM_REG_CPSR)
    B=bench_module();rows=[]
    def new():return B.Banco(rom,installed=True)
    def prepare(b,member,offset,item=50,quantity=5):
        raw=members[member];op,*args=struct.unpack_from('<4H',raw,offset)
        need(op in (125,127),'actual command fixture')
        b.prepara(SimpleNamespace(byte=bytes(raw),off=offset))
        b.vars={args[0]:item,args[1]:quantity}
        # The tested sites use script variables; literal arguments must not be silently reinterpreted.
        need(args[0]>=0x4000 and args[1]>=0x4000,'fixture requires variable item/quantity operands')
        return op,args[2]
    entries={BASE:'cmd127',BASE+8:'cmd125',BASE+16:'has_space',0x023DAF88:'give_item',
             0x0204E9D8:'native GiveItem',0x0204EA88:'native HasSpace',
             0x0203FE2C:'native ReadHalfword',0x0203FD6C:'native RunScriptCommand',0x0203FDCE:'native BLX command'}
    def observe(b,operation,dispatcher=False):
        uc=b.uc;stack=B.PILA-64;info={'instructions':0,'stack_depth':0,'events':[],'writes':{}}
        regions=(('stack',stack-4096,stack),('script PC',B.CTX+8,B.CTX+12),
                 ('variables',B.VARS,B.VARS+0x2000),('relay',BASE+0x5F0,BASE+0x5F8))
        def code(cpu,address,size,unused):
            info['instructions']+=1;info['stack_depth']=max(info['stack_depth'],stack-cpu.reg_read(UC_ARM_REG_SP))
            need(address in B.NATIVE or BASE<=address<BASE+658
                 or 0x0203FE2C<=address<0x0203FE48 or 0x0204E9D8<=address<0x0204EA30
                 or 0x0204EA88<=address<0x0204EAE0
                 or dispatcher and 0x0203FD6C<=address<0x0203FDD8,'unexpected gift execution %#x'%address)
            if address in entries:
                need(len(info['events'])<64,'gift event budget')
                row=dict(address=hex(address),function=entries[address])
                if address==0x0203FDCE:row['target']=hex(cpu.reg_read(UC_ARM_REG_R1))
                info['events'].append(row)
        def write(cpu,access,address,size,value,unused):
            matches=[name for name,lo,hi in regions if lo<=address and address+size<=hi]
            need(len(matches)==1,'unexpected guest write %#x+%d'%(address,size))
            name=matches[0];r=info['writes'].setdefault(name,dict(count=0,bytes=0,low=address,high=address+size))
            r['count']+=1;r['bytes']+=size;r['low']=min(r['low'],address);r['high']=max(r['high'],address+size)
        hooks=[uc.hook_add(UC_HOOK_CODE,code),uc.hook_add(UC_HOOK_MEM_WRITE,write)]
        try:result=operation()
        finally:
            for hook in hooks:uc.hook_del(hook)
        return result,info
    def run(b,member,offset,item=50,quantity=5):
        op,ret=prepare(b,member,offset,item,quantity)
        if op==125:b.scrivi_var(0x800A,0xBEEF)  # Test unconditional discard-flag initialization.
        result,trace=observe(b,lambda:b.esegui(op))
        need(result['reso']==0 and result['avanzamento']==6,'handler result/argument advance')
        return dict(member=member,opcode=op,offset=offset,result=b.var(ret),discard=b.var(0x800A),
            relay=result['staffetta'],calls=result['chiamate'],**trace)
    for quantity_before,added in ((999,0),(998,1),(997,2),(994,5)):
        b=new();b.quantita=quantity_before
        first=run(b,171,40);need(first['result']==1 and first['relay']['armata']==int(added<5),'permissive 127 relay')
        last=run(b,3,2064)
        add=[c for c in last['calls'] if c[0]=='Bag_AddItem']
        need(last['result']==1 and last['discard']==int(added<5) and last['relay']['armata']==0,'common GiveItem outcome')
        need([c[3] for c in add]==([added] if added else []),'clamped/native amount')
        rows.append(dict(case='real gift and common give',quantity_before=quantity_before,added=added,steps=[first,last]))
        del b;gc.collect()
    for stale in ('item','quantity'):
        b=new();b.quantita=999;first=run(b,171,40);b.aggiunta=0
        last=run(b,3,2064,item=51 if stale=='item' else 50,quantity=6 if stale=='quantity' else 5)
        need(last['result']==0 and last['discard']==0 and last['relay']['armata']==0,'stale relay native refusal')
        need(any(c[0]=='Bag_AddItem' for c in last['calls']) and not any(c[0]=='Bag_GetItemPocket' for c in last['calls']),'stale relay must execute native handler')
        rows.append(dict(case='stale '+stale,steps=[first,last]));del b;gc.collect()
    for pocket in (5,7,8):
        b=new();b.tasca=pocket;b.quantita=999;b.spazio=0
        step=run(b,171,40)
        need(step['result']==0 and step['relay']['armata']==0,'Mail/Key/unknown pocket native amount')
        need(any(c[0]=='Bag_HasSpaceForItem' and c[3]==5 for c in step['calls'])
             and not any(c[0]=='Bag_GetItemQuantity' for c in step['calls']),'immune pocket quantity untouched')
        rows.append(dict(case='immune pocket',pocket=pocket,steps=[step]));del b;gc.collect()
    for member,op,offset in R.NERI_R:
        b=new();b.quantita=999;b.spazio=0
        step=run(b,member,offset)
        need(step['result']==0 and step['relay']['armata']==0 and
             not any(c[0]=='Bag_GetItemPocket' for c in step['calls']),'audited blacklist remains native')
        rows.append(dict(case='audited blacklist',steps=[step]));del b;gc.collect()
    strict=[(d['member'],d['new_offset'],'moved site without matching relay') for d in drift]
    strict.extend((s['membro'],s['offset'],'intentional new Enigma check') for s in sites if s['membro']==757 and s['opcode']==127)
    for member,offset,label in strict:
        b=new();b.quantita=999;b.spazio=b.aggiunta=0
        step=run(b,member,offset)
        need(step['result']==0 and step['discard']==0 and step['relay']['armata']==0,'unlisted site remains native')
        need(not any(c[0]=='Bag_GetItemPocket' for c in step['calls']),'unlisted site used permissive path')
        rows.append(dict(case=label,steps=[step]));del b;gc.collect()
    b=new();b.quantita=999;step=run(b,145,1048)
    need(step['result']==1 and step['relay']['armata']==1,'header-crossing FNV window')
    rows.append(dict(case='32-byte window crosses long member header',steps=[step]));del b;gc.collect()
    # Execute the native table load and BLX, stopping exactly after one callback.
    # This observes a live caller frame; it does not claim a full dispatcher return.
    b=new();b.quantita=999;prepare(b,171,40);u=b.uc
    u.mem_write(B.CTX+1,b'\x01');u.mem_write(B.CTX+8,struct.pack('<I',B.MEMBRO+40))
    u.mem_write(B.CTX+0x5C,struct.pack('<II',0x020FAD00,853))
    for register,value in B.CALLEE.items():u.reg_write(register,value)
    u.reg_write(UC_ARM_REG_R0,B.CTX);u.reg_write(UC_ARM_REG_SP,B.PILA-64);u.reg_write(UC_ARM_REG_LR,B.FINE|1)
    b.chiamate=[]
    def dispatch():u.emu_start(0x0203FD6D,0x0203FDD0,count=20000)
    _,trace=observe(b,dispatch,True)
    need(u.reg_read(UC_ARM_REG_PC)==0x0203FDD0 and u.reg_read(UC_ARM_REG_SP)==B.PILA-72
         and u.reg_read(UC_ARM_REG_R4)==B.CTX and u.reg_read(UC_ARM_REG_CPSR)&32
         and u.reg_read(UC_ARM_REG_R0)==0,'native dispatcher callback checkpoint')
    need(all(u.reg_read(r)==v for r,v in B.CALLEE.items() if r!=UC_ARM_REG_R4),'live dispatcher callee registers')
    need(struct.unpack('<I',u.mem_read(B.CTX+8,4))[0]==B.MEMBRO+48
         and b.staffetta()['armata']==1,'native dispatcher opcode/argument consumption')
    need(any(e.get('target')=='0x23dad01' for e in trace['events']),'actual table-loaded BLX target')
    b._check_installed()
    rows.append(dict(case='native dispatcher callback checkpoint',steps=[dict(checkpoint_pc='0x0203FDD0',
        checkpoint_sp=B.PILA-72,full_dispatcher_return=False,calls=b.chiamate,**trace)]))
    del b;gc.collect()
    return rows


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('rom','v4','base','retail','build','scrcmd','json'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--language',choices=('EN','IT'),required=True)
    a=p.parse_args();proof,members,sites=offline(a.rom,a.v4,a.base,a.retail,a.build,a.scrcmd,a.language)
    proof['execution']=execution(a.rom,members,sites,proof['r4_orphans'])
    proof.update(schema='gift-source-rom-v1',language=a.language,verifier_sha256=sha(Path(__file__).read_bytes()),
        dependencies_sha256={str(p.relative_to(SOURCE)):sha(p.read_bytes()) for p in (
            Path(__file__).with_name('applica_borsa.py'),Path(__file__).with_name('rileggi_borsa.py'),
            Path(__file__).with_name('scr_disasm.py'),SOURCE/'features/borsa/test/banco.py',
            SOURCE/'sgp131/legacy_scripts.py',SOURCE/'sgp131/gifts_scripts.py',
            SOURCE/'sgp131/data/gifts-claims.json',SOURCE/'sgp131/baseline.py')},
        limits=['isolated fixtures and declared variable/Bag transports','102 current keys and8 obsolete keys; no table correction',
                'native dispatcher observed through one callback only','no natural gameplay/SAVE/cold/hardware'])
    a.json.parent.mkdir(parents=True,exist_ok=True);a.json.write_text(json.dumps(proof,indent=2)+'\n')
    print(a.language,'compiled658B/owner2048,110V4→102current+8drift; installed execution PASS',
          sum(len(r['steps']) for r in proof['execution']),'invocations')


if __name__=='__main__':main()
