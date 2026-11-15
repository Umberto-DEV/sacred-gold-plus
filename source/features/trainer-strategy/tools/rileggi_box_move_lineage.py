#!/usr/bin/env python3
"""Locate the complete Box caller and read its bounded component lineage.

Retail/base1.1/V4/r4 inputs are authenticated from existing public manifests.
The unique caller is located from its66-byte fingerprint; actual BL and jump
table entries select children. Report differences or unresolved layouts without
inventing physical offsets inside compressed/non-linear owners. No CPU/model.
"""
from pathlib import Path
import argparse
import importlib.util
import json
import struct


def load(path,name):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


HERE=Path(__file__).resolve();SOURCE=HERE.parents[3]
L=load(HERE.with_name('rileggi_box_move_caller.py'),'lineage_Box_caller_current')
OLD=load(HERE.with_name('rileggi_mon_substruct_lineage.py'),'lineage_retained_identity_owner_helpers')
R,need,sha=L.R,L.need,L.sha
piece,identities=OLD.piece,OLD.identities
CURRENT_KEYS=dict(move_caller='move_caller',set_before='setter_before_check',set_valid='setter_valid',
 set_internal='internal_prefix',set_dispatch='internal_dispatch',set54='internal_leaf54_return',set58='set_pp_leaf',
 set_table='attribute_table',get_before='get_getter_before_check',get_valid='get_getter_valid',
 get_internal='get_internal_prefix',get_dispatch='get_internal_dispatch',get62='get_internal_leaf62',
 get_return='get_internal_return',get_table='get_attribute_table',maxpp='maxpp')


def locate_caller(sections,signature):
    need(type(signature)is bytes and len(signature)==66,'complete caller fingerprint')
    found=[]
    for section in sections:
        data=bytes(section.data);start=0
        while True:
            i=data.find(signature,start)
            if i<0:break
            a=section.ramAddress+i
            if a%2==0:found.append(a)
            start=i+1
    need(len(found)==1,'unique caller fingerprint in decoded owners')
    return found[0]


def bl_target(pc,blob):
    need(type(pc)is int and 0<=pc<2**32 and pc%2==0 and type(blob)is bytes and len(blob)==4,'typed ordinary Thumb BL')
    high,low=struct.unpack('<HH',blob)
    need(high&0xf800==0xf000 and low&0xf800==0xf800,'ordinary Thumb BL pair only')
    upper=high&0x7ff
    if upper&0x400:upper-=0x800
    return (pc+4+(upper<<12)+((low&0x7ff)<<1))&0xffffffff


def branch_target(pc,blob):
    need(type(blob)is bytes and len(blob)==2,'complete getter return branch')
    word=int.from_bytes(blob,'little');need(word&0xf800==0xe000,'ordinary getter return B')
    offset=word&0x7ff
    if offset&0x400:offset-=0x800
    return (pc+4+2*offset)&0xffffffff


def physical_position(owner,base,offset,stored_size,address,size,compressed):
    need(all(type(x)is int for x in(base,offset,stored_size,address,size))and type(compressed)is bool,'typed lineage physical owner')
    if compressed or owner.ramAddress!=base or not(base<=address and address+size<=base+stored_size):return None
    return offset+address-base


def inspect(path,identity,current):
    import ndspy.code,ndspy.codeCompression
    path=Path(path);need(path.stat().st_size==identity['bytes']and R.file_sha(path)==identity['sha256'],'exact historical Box caller input')
    with path.open('rb')as f:
        h=f.read(512);off,base,size=(R.u32(h,x)for x in(0x20,0x28,0x2c))
        need(0<size<=4*1024**2 and off+size<=path.stat().st_size,'bounded lineage ARM9')
        f.seek(off);stored=f.read(size)
    expanded=ndspy.codeCompression.decompress(stored);need(len(expanded)<=4*1024**2,'bounded expanded lineage owner')
    compressed=expanded!=stored;sections=ndspy.code.MainCodeFile(stored,base).sections
    metadata=dict(ROM_sha256=identity['sha256'],ROM_bytes=identity['bytes'],game_code=h[12:16].decode('ascii',errors='replace'),revision=h[30],
        ARM9_stored_rom_range=[off,off+size],ARM9_stored_sha256=sha(stored),ARM9_expanded_sha256=sha(expanded),compression='BLZ'if compressed else'plain')
    try:
        entry=locate_caller(sections,current['move_caller']);caller,_=piece(sections,entry,66)
        targets=[bl_target(entry+i,caller[i:i+4])for i in(14,26,38,54)]
        setter,getter,maxpp,last=targets;need(last==setter,'both caller setters reach same function')
        specs=dict(move_caller=(entry,66),set_before=(setter,44),set_valid=(setter+74,44),set_internal=(setter+120,70),
            set_dispatch=(setter+192,12),set_table=(setter+204,376),get_before=(getter,44),get_valid=(getter+60,36),
            get_internal=(getter+96,72),get_dispatch=(getter+170,12),get_table=(getter+182,376),maxpp=(maxpp,40))
        dispatch,_=piece(sections,setter+192,12);get_dispatch,_=piece(sections,getter+170,12)
        need(dispatch==current['set_dispatch']and get_dispatch==current['get_dispatch'],'identified selector dispatch layout')
        set_table,_=piece(sections,setter+204,376);get_table,_=piece(sections,getter+182,376)
        for attr,name in((54,'set54'),(58,'set58')):
            delta=struct.unpack_from('<h',set_table,2*attr)[0];specs[name]=(setter+206+delta,16)
        get_leaf=getter+184+struct.unpack_from('<h',get_table,124)[0];specs['get62']=(get_leaf,12)
        leaf,_=piece(sections,get_leaf,12);specs['get_return']=(branch_target(get_leaf+10,leaf[10:]),6)
        components={}
        for name,(a,n)in specs.items():
            blob,owner=piece(sections,a,n);position=physical_position(owner,base,off,size,a,n,compressed)
            if position is not None:
                with path.open('rb')as f:f.seek(position);physical=f.read(n)
                need(physical==blob,'independent physical Box lineage '+name)
            components[name]=dict(ram=a,bytes=n,sha256=sha(blob),kind='data'if name.endswith('_table')else'code',
                physical_plaintext_offset=position,decoded_owner_ram=owner.ramAddress,decoded_owner_bytes=len(owner.data),equal_to_current=blob==current[name])
        need(sum(x['bytes']for x in components.values())==1242 and len(components)==16,'finite490code+752data lineage')
        return dict(**metadata,status='complete bounded readback',located_caller=entry,BL_targets=targets,components=components,
            all_components_equal=all(x['equal_to_current']for x in components.values()))
    except ValueError as e:
        return dict(**metadata,status='unattributed layout',reason=str(e),components={},all_components_equal=False)


def analyze(paths,language):
    ids=identities(language)
    _,box=L.read_box(paths['r4'],R.EN if language=='EN'else R.IT);extra,_=L.MX.physical(paths['r4']);box.update(extra)
    current={name:box[key]for name,key in CURRENT_KEYS.items()}
    rows=[dict(role=role,**inspect(paths[role],ids[role],current))for role in('retail','base11','v4','r4')]
    return dict(schema='native-box-move-component-lineage-v1',language=language,images=rows,
        all_images_attributed=all(row['status']=='complete bounded readback'for row in rows),
        source_sha256={str(p.relative_to(SOURCE)):sha(p.read_bytes())for p in(HERE,Path(L.__file__),Path(OLD.__file__))},
        manifest_sha256={name:sha((SOURCE/name).read_bytes())for name in OLD.MANIFESTS},CPU_executed=False,compiler_invoked=False,
        scope='New bounded caller/Box/Get/MaxPP490code+752table bytes; no historical activation or whole-ROM equivalence',
        mapping_limit='Compressed/non-linear owners retain null per-instruction physical offsets; decode the identified ARM9 owner')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in('retail','base','v4','rom','json'):p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--language',choices=('EN','IT'),required=True);a=p.parse_args()
    try:
        out=a.json.resolve();need(out!=SOURCE and SOURCE not in out.parents and not out.exists()and not out.is_symlink(),'fresh private Box lineage receipt')
        receipt=analyze(dict(retail=a.retail,base11=a.base,v4=a.v4,r4=a.rom),a.language)
        with out.open('x')as f:json.dump(receipt,f,indent=2);f.write('\n')
    except(ValueError,OSError,EOFError)as e:p.exit(2,str(e)+'\n')
    print(a.language+' four-image1242B component lineage recorded; attributed='+str(receipt['all_images_attributed'])+'; noCPU/compiler')


if __name__=='__main__':main()
