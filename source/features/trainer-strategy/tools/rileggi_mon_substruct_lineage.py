#!/usr/bin/env python3
"""Locate GetSubstruct in exact retail/base1.1/V4/r4 images without a ROM model.

The new ROI is code34 + literal4 + table128. Find the two code fingerprints
independently in decoded sections, then follow the actual LDR literal. Never
invent a linear per-instruction offset inside compressed/autoload owners.
"""
from pathlib import Path
import argparse
import importlib.util
import json
import struct


HERE=Path(__file__).resolve();SOURCE=HERE.parents[3]
s=importlib.util.spec_from_file_location('GetSubstruct_lineage_current_reader',HERE.with_name('rileggi_mon_substruct.py'))
L=importlib.util.module_from_spec(s);s.loader.exec_module(L)
R,need,sha=L.R,L.need,L.sha
MANIFESTS=('sgp12/base11.json','distribution/bootstrap-13-v4.json','distribution/release-1.3.2-r4.json')


def identities(language):
    need(language in('EN','IT'),'finite lineage language')
    base,bootstrap,release=(json.loads((SOURCE/n).read_bytes())for n in MANIFESTS)
    b=base['basi'][language]
    return dict(retail=dict(sha256=b['originale']['sha256'],bytes=b['originale']['byte']),
        base11=dict(sha256=b['base_1_1']['sha256'],bytes=b['base_1_1']['byte']),
        v4=bootstrap['outputs'][language],r4=release['targets'][language])


def piece(sections,address,size):
    need(type(address)is int and type(size)is int and 0<=address<2**32 and 0<size<=4*1024**2 and address+size<=2**32,'bounded lineage decoded read')
    owners=[s for s in sections if s.ramAddress<=address and address+size<=s.ramAddress+len(s.data)]
    need(len(owners)==1,'one decoded lineage owner');owner=owners[0]
    return bytes(owner.data[address-owner.ramAddress:address-owner.ramAddress+size]),owner


def locate(sections,prefix,lookup):
    need(type(prefix)is bytes and len(prefix)==20 and type(lookup)is bytes and len(lookup)==14,'two GetSubstruct fingerprints')
    candidates=[]
    for section in sections:
        data=bytes(section.data);start=0
        while True:
            i=data.find(prefix,start)
            if i<0:break
            a=section.ramAddress+i
            if i+38<=len(data)and data[i+24:i+38]==lookup:candidates.append(a)
            start=i+1
    need(len(candidates)==1,'unique ROM-to-GetSubstruct code correspondence')
    entry=candidates[0];pc=entry+24;op=int.from_bytes(lookup[:2],'little')
    need(op&0xf800==0x4800 and(op>>8)&7==0,'qualified Thumb literal load recipe')
    literal=((pc+4)&~3)+(op&255)*4;blob,_=piece(sections,literal,4);table=struct.unpack('<I',blob)[0]
    return entry,literal,table


def inspect(path,identity,current):
    import ndspy.code,ndspy.codeCompression
    path=Path(path);need(path.stat().st_size==identity['bytes']and R.file_sha(path)==identity['sha256'],'exact historical GetSubstruct input')
    with path.open('rb')as f:
        h=f.read(512);off,base,size=(R.u32(h,n)for n in(0x20,0x28,0x2c))
        need(0<size<=4*1024**2 and off+size<=path.stat().st_size,'bounded stored ARM9');f.seek(off);stored=f.read(size)
    expanded=ndspy.codeCompression.decompress(stored);need(len(expanded)<=4*1024**2,'bounded expanded ARM9')
    compressed=expanded!=stored;decoded=ndspy.code.MainCodeFile(stored,base)
    entry,literal,table=locate(decoded.sections,current['prefix'],current['lookup'])
    table_blob,_=piece(decoded.sections,table,128);need(sha(table_blob)==L.DATA['offsets'][-1],'historical source offset-table identity')
    components={}
    for name,address,n in(('prefix',entry,20),('lookup',entry+24,14),('table_literal',literal,4),('offsets',table,128)):
        blob,owner=piece(decoded.sections,address,n);pos=None
        if not compressed and owner.ramAddress==base and base<=address and address+n<=base+size:
            candidate=off+address-base
            with path.open('rb')as f:f.seek(candidate);physical=f.read(n)
            need(physical==blob,'independent plain physical lineage read');pos=candidate
        components[name]=dict(ram=address,bytes=n,sha256=sha(blob),physical_plaintext_offset=pos,
            decoded_owner_ram=owner.ramAddress,decoded_owner_bytes=len(owner.data),equal_to_current=blob==current[name])
    return dict(ROM_sha256=identity['sha256'],ROM_bytes=identity['bytes'],game_code=h[12:16].decode('ascii',errors='replace'),revision=h[30],
        ARM9_stored_rom_range=[off,off+size],ARM9_stored_sha256=sha(stored),ARM9_expanded_sha256=sha(expanded),
        compression='BLZ'if compressed else'plain',located_entry=entry,located_table=table,components=components,
        mapping_limit='Per-instruction physical offsets are null for compressed or non-linear owners; decode the identified stored ARM9 owner')


def analyze(paths,language):
    ids=identities(language);_,current=L.read(paths['r4'],R.EN if language=='EN'else R.IT)
    rows=[dict(role=role,**inspect(paths[role],ids[role],current))for role in('retail','base11','v4','r4')]
    return dict(schema='native-mon-substructure-lineage-v1',language=language,images=rows,
        source_sha256={str(p.relative_to(SOURCE)):sha(p.read_bytes())for p in(HERE,Path(L.__file__),Path(R.__file__))},
        manifest_sha256={n:sha((SOURCE/n).read_bytes())for n in MANIFESTS},CPU_executed=False,compiler_invoked=False,
        scope='New GetSubstruct166B ROI only; independently located code and actual literal/table, not historical activation or full-image equivalence')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in('retail','base','v4','rom','json'):p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--language',choices=('EN','IT'),required=True);a=p.parse_args()
    try:
        out=a.json.resolve();need(out!=SOURCE and SOURCE not in out.parents and not out.exists()and not out.is_symlink(),'fresh private lineage receipt')
        receipt=analyze(dict(retail=a.retail,base11=a.base,v4=a.v4,r4=a.rom),a.language)
        with out.open('x')as f:json.dump(receipt,f,indent=2);f.write('\n')
    except(ValueError,OSError,EOFError)as e:p.exit(2,str(e)+'\n')
    print(a.language+' four-image GetSubstruct code/literal/table lineage PASS; noCPU/compiler/wholeROMmodel')


if __name__=='__main__':main()
