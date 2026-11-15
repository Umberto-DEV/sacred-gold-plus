#!/usr/bin/env python3
"""Follow Mon62 wrapper calls/default/table leaf in four exact images per language.

244 bounded bytes:148 new code,82 retained internal code,2 selected row and
12 followed crypto/checksum entry bytes. No historical activation claim.
"""
from pathlib import Path
import argparse
import importlib.util
import json
import struct


def load(path,name):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


HERE=Path(__file__).resolve();SOURCE=HERE.parents[3]
L=load(HERE.with_name('rileggi_mon_ppup_setter.py'),'Mon_lineage_current_reader')
OLD=load(HERE.with_name('rileggi_box_move_lineage.py'),'Mon_lineage_qualified_owner_helpers')
R,need,sha=L.R,L.need,L.sha
NAMES=tuple(L.NEW_THUMB)+('internal_prefix','internal_dispatch','row62','cipher_wrapper','decrypt_wrapper','checksum_entry')


def locate(sections,signature):
    need(type(signature)is bytes and len(signature)==56,'complete Mon entry fingerprint')
    found=[]
    for section in sections:
        data=bytes(section.data);start=0
        while True:
            i=data.find(signature,start)
            if i<0:break
            address=section.ramAddress+i
            if address%2==0:found.append(address)
            start=i+1
    need(len(found)==1,'unique aligned Mon entry fingerprint');return found[0]


def components(sections,current):
    need(type(current)is dict and set(current)==set(NAMES)and all(type(b)is bytes for b in current.values()),'complete Mon lineage fingerprints')
    entry=locate(sections,current['mon_before_check']);valid=entry+86;bridge=entry+144;default=entry+296
    body,_=OLD.piece(sections,entry,56);validbody,_=OLD.piece(sections,valid,56);defaultbody,_=OLD.piece(sections,default,8)
    decrypt=OLD.bl_target(entry+24,body[24:28]);need(OLD.bl_target(entry+36,body[36:40])==decrypt,'two Mon decrypt calls share primitive')
    checksum=OLD.bl_target(entry+46,body[46:50]);need(OLD.bl_target(valid+36,validbody[36:40])==checksum,'both Mon checksum calls share primitive')
    need(OLD.bl_target(valid+6,validbody[6:10])==bridge,'actual Mon bridge BL')
    encrypt=OLD.bl_target(valid+26,validbody[26:30]);need(OLD.bl_target(valid+50,validbody[50:54])==encrypt,'two Mon encrypt calls share primitive')
    internal=OLD.bl_target(default+2,defaultbody[2:6]);row,_=OLD.piece(sections,internal+84+124,2)
    leaf=internal+86+struct.unpack('<h',row)[0]
    specs=dict(mon_before_check=(entry,56),mon_valid=(valid,56),mon_internal_prefix=(bridge,12),mon_internal_default=(default,8),
        internal_leaf62_return=(leaf,16),internal_prefix=(internal,70),internal_dispatch=(internal+72,12),row62=(internal+208,2),
        cipher_wrapper=(encrypt,4),decrypt_wrapper=(decrypt,4),checksum_entry=(checksum,4))
    return dict(entry=entry,Box_internal=internal,row62_target=leaf,decrypt=decrypt,encrypt=encrypt,checksum=checksum,
        parts={name:(a,*OLD.piece(sections,a,n))for name,(a,n)in specs.items()})


def inspect(path,identity,current):
    import ndspy.code,ndspy.codeCompression
    path=Path(path);need(path.stat().st_size==identity['bytes']and R.file_sha(path)==identity['sha256'],'exact historical Mon image')
    with path.open('rb')as f:
        header=f.read(512);off,base,size=(R.u32(header,x)for x in(0x20,0x28,0x2c))
        need(0<size<=4*1024**2 and off+size<=path.stat().st_size,'bounded Mon lineage ARM9 owner');f.seek(off);stored=f.read(size)
    expanded=ndspy.codeCompression.decompress(stored);need(len(expanded)<=4*1024**2,'bounded expanded Mon owner')
    compressed=stored!=expanded;sections=ndspy.code.MainCodeFile(stored,base).sections
    metadata=dict(ROM_sha256=identity['sha256'],ROM_bytes=identity['bytes'],game_code=header[12:16].decode('ascii',errors='replace'),revision=header[30],
        ARM9_stored_rom_range=[off,off+size],ARM9_stored_sha256=sha(stored),ARM9_expanded_sha256=sha(expanded),compression='BLZ'if compressed else'plain')
    try:
        selected=components(sections,current);rows={}
        for name,(a,blob,owner)in selected['parts'].items():
            physical=OLD.physical_position(owner,base,off,size,a,len(blob),compressed)
            if physical is not None:
                with path.open('rb')as f:f.seek(physical);direct=f.read(len(blob))
                need(direct==blob,'independent Mon lineage physical read '+name)
            rows[name]=dict(ram=a,bytes=len(blob),sha256=sha(blob),physical_plaintext_offset=physical,decoded_owner_ram=owner.ramAddress,
                decoded_owner_bytes=len(owner.data),equal_to_current=blob==current[name],kind='signed table data'if name=='row62'else'code')
        need(len(rows)==11 and sum(r['bytes']for r in rows.values())==244,'Mon148new+82internal+2row+12targets')
        return dict(**metadata,status='complete bounded readback',**{k:v for k,v in selected.items()if k!='parts'},components=rows,
            all_components_equal=all(r['equal_to_current']for r in rows.values()))
    except ValueError as e:return dict(**metadata,status='unattributed layout',reason=str(e),components={},all_components_equal=False)


def analyze(paths,language):
    ids=OLD.identities(language);identity=R.EN if language=='EN'else R.IT
    _,parts=L.read(paths['r4'],identity);current={n:parts[n]for n in NAMES if n not in('row62','checksum_entry','cipher_wrapper')}
    current['row62']=parts['attribute_table'][124:126];current['checksum_entry']=parts['checksum'][:4];current['cipher_wrapper']=parts['wrapper']
    rows=[dict(role=role,**inspect(paths[role],ids[role],current))for role in('retail','base11','v4','r4')]
    return dict(schema='native-Mon-PPUp-setter-lineage-v1',language=language,images=rows,
        all_images_attributed=all(r['status']=='complete bounded readback'for r in rows),
        source_sha256={str(p.relative_to(SOURCE)):sha(p.read_bytes())for p in(HERE,Path(L.__file__),Path(OLD.__file__),Path(OLD.OLD.__file__))},
        manifest_sha256={n:sha((SOURCE/n).read_bytes())for n in OLD.OLD.MANIFESTS},CPU_executed=False,compiler_invoked=False,
        scope='244 selected bytes and actual BL/default/row62 relationships only; no whole-ROM build, historical activation or save claim',
        mapping_limit='BLZ/non-linear owners keep null physical plaintext offsets; require attribution and individual component equality')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in('retail','base','v4','rom','json'):p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--language',choices=('EN','IT'),required=True);a=p.parse_args()
    try:
        out=a.json.resolve();need(SOURCE not in out.parents and out!=SOURCE and not out.exists()and not out.is_symlink(),'fresh private Mon lineage output')
        result=analyze(dict(retail=a.retail,base11=a.base,v4=a.v4,r4=a.rom),a.language)
        with out.open('x')as f:json.dump(result,f,indent=2);f.write('\n')
    except(ValueError,OSError,EOFError)as e:p.exit(2,str(e)+'\n')
    print(a.language+' Mon244B lineage recorded; attributed='+str(result['all_images_attributed'])+'; no CPU/compiler')


if __name__=='__main__':main()
