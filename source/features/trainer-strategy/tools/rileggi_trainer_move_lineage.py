#!/usr/bin/env python3
"""Locate the first type3 move prefix and follow its veneer in exact images.

New ROI40 = prefix30 + veneer4 + literal4 + excluded branch2. The66-byte
Box callee is followed again as a target witness, giving106 bounded bytes.
Trainer resource lineage already established elsewhere is not reacquired.
"""
from pathlib import Path
import argparse
import importlib.util
import json
import struct


def load(path,name):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


HERE=Path(__file__).resolve();SOURCE=HERE.parents[3]
L=load(HERE.with_name('rileggi_trainer_move_prefix.py'),'first_move_current_resources')
OLD=load(HERE.with_name('rileggi_box_move_lineage.py'),'first_move_qualified_lineage_helpers')
R,need,sha=L.R,L.need,L.sha
NAMES=('trainer_prefix','mon_veneer','mon_target','prefix_gate','box_caller')


def locate_prefix(sections,signature):
    need(type(signature)is bytes and len(signature)==30,'complete first-slot prefix fingerprint')
    found=[]
    for section in sections:
        data=bytes(section.data);start=0
        while True:
            i=data.find(signature,start)
            if i<0:break
            a=section.ramAddress+i
            if a%2==0:found.append(a)
            start=i+1
    need(len(found)==1,'unique aligned first-slot prefix fingerprint')
    return found[0]


def components(sections,current):
    need(type(current)is dict and set(current)==set(NAMES)and all(type(b)is bytes for b in current.values()),'typed complete first-slot current fingerprints')
    entry=locate_prefix(sections,current['trainer_prefix']);prefix,owner=OLD.piece(sections,entry,30)
    veneer=OLD.bl_target(entry+16,prefix[16:20]);code,code_owner=OLD.piece(sections,veneer,4)
    need(code==bytes.fromhex('004b1847'),'qualified literal-load/BX veneer layout')
    literal,lit_owner=OLD.piece(sections,veneer+4,4);pointer=struct.unpack('<I',literal)[0]
    need(pointer&1,'Thumb veneer literal target bit');box=pointer&~1;callee,callee_owner=OLD.piece(sections,box,66)
    gate,gate_owner=OLD.piece(sections,entry+30,2)
    need(gate==bytes.fromhex('f2db'),'qualified excluded LT branch gate')
    target=entry+30+4+2*int.from_bytes(gate[:1],'little',signed=True);need(target==entry+6,'gate loops to the cursor load after setup')
    return dict(prefix=entry,veneer=veneer,box_caller=box,gate_target=target,parts=dict(
        trainer_prefix=(entry,prefix,owner),mon_veneer=(veneer,code,code_owner),mon_target=(veneer+4,literal,lit_owner),
        prefix_gate=(entry+30,gate,gate_owner),box_caller=(box,callee,callee_owner)))


def inspect(path,identity,current):
    import ndspy.code,ndspy.codeCompression
    path=Path(path);need(path.stat().st_size==identity['bytes']and R.file_sha(path)==identity['sha256'],'exact historical first-slot image')
    with path.open('rb')as f:
        h=f.read(512);off,base,size=(R.u32(h,x)for x in(0x20,0x28,0x2c));need(0<size<=4*1024**2 and off+size<=path.stat().st_size,'bounded first-slot ARM9 owner')
        f.seek(off);stored=f.read(size)
    expanded=ndspy.codeCompression.decompress(stored);need(len(expanded)<=4*1024**2,'bounded expanded first-slot owner')
    compressed=stored!=expanded;sections=ndspy.code.MainCodeFile(stored,base).sections
    metadata=dict(ROM_sha256=identity['sha256'],ROM_bytes=identity['bytes'],game_code=h[12:16].decode('ascii',errors='replace'),revision=h[30],
        ARM9_stored_rom_range=[off,off+size],ARM9_stored_sha256=sha(stored),ARM9_expanded_sha256=sha(expanded),compression='BLZ'if compressed else'plain')
    try:
        selected=components(sections,current);rows={}
        for name,(a,b,owner)in selected['parts'].items():
            pos=OLD.physical_position(owner,base,off,size,a,len(b),compressed)
            if pos is not None:
                with path.open('rb')as f:f.seek(pos);physical=f.read(len(b))
                need(physical==b,'independent first-slot physical read '+name)
            rows[name]=dict(ram=a,bytes=len(b),sha256=sha(b),physical_plaintext_offset=pos,decoded_owner_ram=owner.ramAddress,
                decoded_owner_bytes=len(owner.data),equal_to_current=b==current[name],
                kind='literal data'if name=='mon_target'else'excluded branch code'if name=='prefix_gate'else'code')
        need(len(rows)==5 and sum(r['bytes']for r in rows.values())==106,'finite40new+66target-witness lineage')
        return dict(**metadata,status='complete bounded readback',located_prefix=selected['prefix'],actual_veneer=selected['veneer'],
            actual_Box_caller=selected['box_caller'],excluded_gate_target=selected['gate_target'],components=rows,
            all_components_equal=all(r['equal_to_current']for r in rows.values()))
    except ValueError as e:return dict(**metadata,status='unattributed layout',reason=str(e),components={},all_components_equal=False)


def analyze(paths,language):
    ids=OLD.identities(language);identity=R.EN if language=='EN'else R.IT
    _,new=L.read_new(paths['r4'],identity);_,parent=L.C.read_box(paths['r4'],identity)
    current={n:new[n]for n in NAMES if n!='box_caller'};current['box_caller']=parent['move_caller']
    rows=[dict(role=role,**inspect(paths[role],ids[role],current))for role in('retail','base11','v4','r4')]
    return dict(schema='native-trainer-first-move-lineage-v1',language=language,images=rows,
        all_images_attributed=all(r['status']=='complete bounded readback'for r in rows),
        source_sha256={str(p.relative_to(SOURCE)):sha(p.read_bytes())for p in(HERE,Path(L.__file__),Path(OLD.__file__),Path(OLD.OLD.__file__))},
        manifest_sha256={n:sha((SOURCE/n).read_bytes())for n in OLD.OLD.MANIFESTS},CPU_executed=False,compiler_invoked=False,
        scope='40 new prefix/veneer/literal/gate bytes and66 followed target bytes only; no record-history rerun, native activation or whole-ROM equivalence',
        mapping_limit='BLZ/non-linear owners keep null physical plaintext offsets; require top attribution and per-image component equality')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in('retail','base','v4','rom','json'):p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--language',choices=('EN','IT'),required=True);a=p.parse_args()
    try:
        out=a.json.resolve();need(out!=SOURCE and SOURCE not in out.parents and not out.exists()and not out.is_symlink(),'fresh private first-slot lineage output')
        r=analyze(dict(retail=a.retail,base11=a.base,v4=a.v4,r4=a.rom),a.language)
        with out.open('x')as f:json.dump(r,f,indent=2);f.write('\n')
    except(ValueError,OSError,EOFError)as e:p.exit(2,str(e)+'\n')
    print(a.language+' first-slot106B lineage recorded; attributed='+str(r['all_images_attributed'])+'; no CPU/compiler')


if __name__=='__main__':main()
