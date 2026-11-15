#!/usr/bin/env python3
"""Compare pinned Mon source components across productive HGSS and newer PRET.

Read-only source audit, no ROM/compiler/CPU. Whole-file drift is distinguished
from unchanged functions and a source-level block-index mapping in Platinum.
"""
from pathlib import Path
import argparse
import importlib.util
import json
import re
import subprocess


HERE=Path(__file__).resolve();SOURCE=HERE.parents[3]
s=importlib.util.spec_from_file_location('mon_alignment_bounded_HG_table',HERE.with_name('rileggi_mon_substruct.py'))
L=importlib.util.module_from_spec(s);s.loader.exec_module(L)
need,sha=L.need,L.sha
PINS={'productive':'cb614ad23449d5852b40321dc409c4143872b35c','heartgold':'6bf138d6035aa6b43d6f8f4132a12df70f86dcec','platinum':'62bdaacdca6c56a6a396f3e9911e2f922b79bba8'}
FILES={
 'productive':{'src/pokemon.c':'1d784ece4650b84e426a437ee20e4a926475fc20ef761e67440d0c0136548fa3','src/math_util.c':'ed76da9a0792494d7b22a029d903db402f5c2cec06212870e0337205be747612'},
 'heartgold':{'src/pokemon.c':'f0a4323e9ad7925a4a2c9a4628216054e9d93c55a28472bef70e2eaefedcc928','src/math_util.c':'b2f3eb5c0c2e7a2494df6401783a79bcee5971ed4607a5850073fb89968b71a6'},
 'platinum':{'src/pokemon.c':'84838b196abe0d851f76e2f1ea75e04473b158ede6d517a4229f2c337b4dda8b','src/math_util.c':'0a43d4ad609caaeb8774461f09987f31d505167c3693e3a21dfd8870e8887a5a','include/math_util.h':'170bafe2b8fbff0074b25299268743744821efde4b1280aa71e6558451e26544'}}
COMPONENTS={
 'checksum':('src/pokemon.c','u32 CalcMonChecksum(void *_data, u32 size) {'),
 'substructure':('src/pokemon.c','PokemonDataBlock *GetSubstruct(BoxPokemon *boxMon, u32 pid, u8 which) {'),
 'cipher':('src/math_util.c','void _MonEncryptSegment(u16 *data, u32 size, u32 seed) {'),
 'LCG':('src/math_util.c','static u16 MonEncryptionLCRNG(u32 *seed) {')}
PT_MARKER='static void *BoxPokemon_GetDataBlock(BoxPokemon *boxMon, u32 personality, enum PokemonDataBlockID dataBlockID)\n{'


def function_block(text,marker):
    need(type(text)is str and text.count(marker)==1 and '\n}\n'in text.split(marker,1)[1],'one bounded pinned function')
    return marker+text.split(marker,1)[1].split('\n}\n',1)[0]+'\n}\n'


def flat(text):return re.sub(r'\s+','',text)


def platinum_offsets(text):
    need('enumPokemonDataBlockID{DATA_BLOCK_A=0,DATA_BLOCK_B,DATA_BLOCK_C,DATA_BLOCK_D};'in flat(text),'Platinum logical block IDs0..3')
    macro_start='#define DATA_BLOCK_SHUFFLE_CASE('
    need(text.count(macro_start)==1 and text.count(PT_MARKER)==1,'one bounded Platinum macro/selector')
    macro=text.split(macro_start,1)[1].split(PT_MARKER,1)[0]
    expected='v1,v2,v3,v4){PokemonDataBlock*dataBlocks=boxMon->dataBlocks;switch(dataBlockID){'
    expected+=''.join('caseDATA_BLOCK_'+letter+':result=&dataBlocks[v'+str(i)+'];break;'for i,letter in enumerate('ABCD',1))+'}break;}'
    need(flat(macro.replace('\\',''))==expected,'exact Platinum macro logical-to-physical assignments')
    body=function_block(text,PT_MARKER)[len(PT_MARKER):-3]
    match=re.fullmatch(r'\s*personality\s*=\s*\(personality\s*&\s*0x3e000\)\s*>>\s*13\s*;\s*GF_ASSERT\(personality\s*<=\s*31\);\s*void\s*\*result;\s*switch\s*\(personality\)\s*\{(.*?)\}\s*return\s+result;\s*',body,re.S)
    need(match is not None,'bounded Platinum selector mask/switch/return')
    cases=match.group(1);pattern=r'case\s+(\d+)\s*:|DATA_BLOCK_SHUFFLE_CASE\(([^)]*)\)'
    need(not re.sub(pattern,'',cases).strip(),'no unparsed Platinum case expressions')
    rows={};pending=[]
    for item in re.finditer(pattern,cases):
        if item.group(1)is not None:
            row=int(item.group(1));need(0<=row<32 and row not in rows and row not in pending,'unique Platinum row0..31');pending.append(row)
        else:
            fields=[v.strip()for v in item.group(2).split(',')]
            need(len(fields)==4 and sorted(fields)==['0','1','2','3']and pending,'four constant block-index permutation')
            offsets=tuple(32*int(v)for v in fields)
            for row in pending:rows[row]=offsets
            pending=[]
    need(not pending and set(rows)==set(range(32)),'all32 Platinum source rows')
    return bytes(v for row in range(32)for v in rows[row])


def read_reference(root,kind):
    root=Path(root)
    need(subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip()==PINS[kind]and
         not subprocess.check_output(['git','-C',str(root),'status','--porcelain']),'clean pinned '+kind+' reference')
    texts={}
    for name,digest in FILES[kind].items():
        b=(root/name).read_bytes();need(sha(b)==digest,'reference source drift '+kind+'/'+name);texts[name]=b.decode()
    return texts


def compare(reference,heartgold_ref,platinum_ref):
    prod,hg,pt=(read_reference(root,kind)for root,kind in((reference,'productive'),(heartgold_ref,'heartgold'),(platinum_ref,'platinum')))
    components={}
    for name,(file,marker)in COMPONENTS.items():
        a,b=(function_block(texts[file],marker).encode()for texts in(prod,hg));need(a==b,'unchanged HGSS component '+name)
        components[name]=dict(bytes=len(a),sha256=sha(a),identical_source_fragment=True)
    a,b,c=L.source_offsets(prod['src/pokemon.c']),L.source_offsets(hg['src/pokemon.c']),platinum_offsets(pt['src/pokemon.c'])
    need(a==b==c and sha(a)==L.DATA['offsets'][-1],'source128 normalized block-offset mapping')
    checksum=function_block(pt['src/pokemon.c'],'static u16 Pokemon_GetDataChecksum(void *data, u32 bytes)\n{')
    need(all(x in flat(checksum)for x in('u16checksum=0;','i<bytes/2','checksum+=dataWords[i];','returnchecksum;')),'Platinum local16 halfword checksum recipe')
    cipher=function_block(pt['src/math_util.c'],'void EncodeData(void *data, u32 size, u32 seed)\n{')
    lcg=function_block(pt['src/math_util.c'],'static u16 LCRNG_NextFrom(u32 *seed)\n{')
    need('halfWords[i]^=LCRNG_NextFrom(&seed);'in flat(cipher)and 'i<size/2'in flat(cipher)and
         '*seed=*seed*LCRNG_MULTIPLIER+LCRNG_INCREMENT;'in flat(lcg)and 'return*seed>>16;'in flat(lcg),'Platinum source cipher/localLCG recipe')
    header=pt['include/math_util.h']
    need(re.search(r'^#define\s+LCRNG_MULTIPLIER\s+1103515245L\s*$',header,re.M)and
         re.search(r'^#define\s+LCRNG_INCREMENT\s+24691\s*$',header,re.M),'same local LCG constants')
    return dict(schema='sgp-mon-PRET-source-alignment-v1',reference_pins=PINS,reference_files=FILES,
        source_sha256={str(p.relative_to(SOURCE)):sha(p.read_bytes())for p in(HERE,Path(L.__file__),Path(L.R.__file__))},
        unchanged_HGSS_components=components,source_mapping=dict(rows=32,selectors=4,normalized_HGSS_byte_offsets_sha256=sha(a),
            first24unique=True,last8repeatfirst8=True,Platinum_implementation='switch and DATA_BLOCK_SHUFFLE_CASE macro'),
        declared_checksum_return_types=dict(HGSS='u32',Platinum='static u16'),
        source_recipes=dict(checksum='sum of u16 elements with localu16 accumulator',cipher='advance localu32 LCG then XOR u16 element with high16',LCG_multiplier=1103515245,LCG_increment=24691),
        CPU_executed=False,ROM_opened=False,compiler_invoked=False,ABI_interchangeability_proved=False,
        scope='Pinned source-only alignment; addresses, compiled bytes, volatile ABI and language build targets require separate evidence')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in('reference','heartgold-ref','platinum-ref','json'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args()
    try:
        out=a.json.resolve();need(out!=SOURCE and SOURCE not in out.parents and not out.exists()and not out.is_symlink(),'fresh private source-alignment receipt')
        result=compare(a.reference,a.heartgold_ref,a.platinum_ref)
        with out.open('x')as f:json.dump(result,f,indent=2);f.write('\n')
    except(ValueError,OSError,subprocess.CalledProcessError)as e:p.exit(2,str(e)+'\n')
    print('Four HGSS functions unchanged;128source mappings agree with Platinum; declared return type difference recorded; noROM/CPU/compiler')


if __name__=='__main__':main()
