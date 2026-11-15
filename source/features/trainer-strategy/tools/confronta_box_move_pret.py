#!/usr/bin/env python3
"""Compare actual global C definitions across two pinned HGSS source trees.

This bounded lexical reader skips calls, prototypes, comments and strings.
It is source alignment only: no preprocessing, compiler, ROM or CPU evidence.
"""
from pathlib import Path
import argparse
import hashlib
import json
import re
import subprocess


HERE=Path(__file__).resolve();SOURCE=HERE.parents[3]
PINS={'productive':'cb614ad23449d5852b40321dc409c4143872b35c','heartgold':'6bf138d6035aa6b43d6f8f4132a12df70f86dcec'}
FILES={
 'productive':{'src/pokemon.c':'1d784ece4650b84e426a437ee20e4a926475fc20ef761e67440d0c0136548fa3','src/move.c':'e9adae2d57511a89ec5cc52ebb5741172a5d90123d02d33be66143ddf210e7b2','src/trainer_data.c':'2e5232c4989f6f2752087bf46579e8207b90b2e5abf65f04dac72e2b03496803','include/constants/pokemon.h':'64d5d0cee8001830298ec7175c1863165ffccdf037685a51ea27037273187c74'},
 'heartgold':{'src/pokemon.c':'f0a4323e9ad7925a4a2c9a4628216054e9d93c55a28472bef70e2eaefedcc928','src/move.c':'2583303832d737aa6299d0b086f945d3640d5cddf948797a0deed65b52d93d73','src/trainer_data.c':'bf9e8cb41dac9b05f3c925dba5d2ec10954955524cc08505c3667cbeabac6be0','include/constants/pokemon.h':'64d5d0cee8001830298ec7175c1863165ffccdf037685a51ea27037273187c74'}}
FUNCTIONS={name:'src/pokemon.c'for name in('BoxMonSetMoveInSlot','SetBoxMonData','MonSetMoveInSlot','MonSetMoveInSlot_ResetPpUp')}
FUNCTIONS.update(GetMoveMaxPP='src/move.c',CreateNPCTrainerParty='src/trainer_data.c')
EXPECTED={
 'BoxMonSetMoveInSlot':(320,'41c060b0536add51a98415666742a80ded4e677228ac955b48daa23636ad59ac'),
 'SetBoxMonData':(558,'300ded32f42c5d022b3c6a5e525c499af61120334d5a50cd132f4712c43fa385'),
 'GetMoveMaxPP':(184,'f40957552425aa458c822bdb13d88a11101277a95fb6d17c601a28a21727b195'),
 'MonSetMoveInSlot':(106,'3eb4e2d2b945be8a193c316affa2a525a3d55ddbc7039dbf4ad99441bbe655e2'),
 'MonSetMoveInSlot_ResetPpUp':(290,'e80f65e6bfd87861d55399c0bade3e8c3beabf840a4bcf563cebaa68f53101cd'),
 'CreateNPCTrainerParty':(8462,'8a33236816322806c9664ad237660a01d578a3663c7c7ce1dd7b568651f1e13d')}


def need(value,message):
    if not value:raise ValueError(message)


def sha(blob):return hashlib.sha256(blob).hexdigest()


def lexical_mask(text):
    """Preserve character offsets/newlines while hiding comments and literals."""
    need(type(text)is str and len(text)<=4*1024**2,'bounded C source text')
    out=list(text);i=0
    def hide(a,b):
        for p in range(a,b):
            if text[p]not in'\r\n':out[p]=' '
    while i<len(text):
        if text.startswith('//',i):
            end=text.find('\n',i+2);end=len(text)if end<0 else end;hide(i,end);i=end
        elif text.startswith('/*',i):
            end=text.find('*/',i+2);need(end>=0,'terminated C block comment');hide(i,end+2);i=end+2
        elif text[i]in'\"\'':
            quote=text[i];j=i+1
            while j<len(text):
                if text[j]=='\\':j+=2;continue
                if text[j]==quote:break
                need(text[j]not in'\r\n','terminated C literal before newline');j+=1
            need(j<len(text),'terminated C literal');hide(i,j+1);i=j+1
        else:i+=1
    return ''.join(out)


def definition(text,name):
    need(type(name)is str and re.fullmatch(r'[A-Za-z_]\w*',name)and name.isascii(),'exact C function identifier')
    masked=lexical_mask(text);depth=[];level=0
    for c in masked:
        depth.append(level)
        if c=='{':level+=1
        elif c=='}':level-=1;need(level>=0,'balanced C global braces')
    need(level==0,'balanced C global braces')
    # Accepted source style: a type/qualifier sequence and function name on
    # one line. Parameters may span lines or contain nested callback types.
    # Attributes, macro-generated signatures and preprocessing are excluded.
    pattern=r'^[ \t]*(?:[A-Za-z_]\w*[ \t]+)+[* \t]*'+re.escape(name)+r'[ \t]*\('
    candidates=[]
    for match in re.finditer(pattern,masked,re.M):
        if depth[match.start()]!=0:continue
        i=match.end();parens=1
        while i<len(masked)and parens:
            if masked[i]=='(':parens+=1
            elif masked[i]==')':parens-=1
            i+=1
        need(parens==0,'balanced C parameter parentheses')
        while i<len(masked)and masked[i].isspace():i+=1
        if i==len(masked)or masked[i]!='{':continue
        end=i+1;braces=1
        while end<len(masked)and braces:
            if masked[end]=='{':braces+=1
            elif masked[end]=='}':braces-=1
            end+=1
        need(braces==0,'balanced C definition body')
        start=match.start()
        while text[start]in' \t':start+=1
        fragment=text[start:end];blob=fragment.encode('utf8')
        candidates.append(dict(text=fragment,start=start,end=end,line=text.count('\n',0,start)+1,bytes=len(blob),sha256=sha(blob)))
    need(len(candidates)==1,'unique accepted global definition '+name)
    return candidates[0]


def read_reference(root,kind):
    root=Path(root)
    need(subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip()==PINS[kind]and
         not subprocess.check_output(['git','-C',str(root),'status','--porcelain']),'clean pinned '+kind+' reference')
    texts={}
    for name,digest in FILES[kind].items():
        raw=(root/name).read_bytes();need(sha(raw)==digest,'pinned source dependency '+kind+'/'+name);texts[name]=raw.decode('utf8')
    return texts


def compare(reference,heartgold_ref):
    texts={kind:read_reference(root,kind)for kind,root in(('productive',reference),('heartgold',heartgold_ref))};result={}
    for name,file in FUNCTIONS.items():
        rows={kind:definition(t[file],name)for kind,t in texts.items()}
        need(rows['productive']['text']==rows['heartgold']['text'],'identical pinned C definitions '+name)
        need((rows['productive']['bytes'],rows['productive']['sha256'])==EXPECTED[name],'expected actual definition extent/digest '+name)
        result[name]=dict(file=file,bytes=rows['productive']['bytes'],sha256=rows['productive']['sha256'],identical_definition=True,
                         lines={kind:row['line']for kind,row in rows.items()})
    return dict(schema='sgp-Box-move-PRET-definitions-v1',reference_pins=PINS,reference_files=FILES,
        source_sha256={str(HERE.relative_to(SOURCE)):sha(HERE.read_bytes())},functions=result,
        extraction='UTF8 bytes from first return-type/qualifier character through matching closing brace; no trailing newline; comments/strings masked only for locating boundaries; no whitespace normalization',
        parser_scope='Pinned ordinary C definitions; no preprocessor interpretation or macro-generated/attribute signatures; ambiguous/missing definitions rejected',
        previous_mislabeled_callsite_hashes={'BoxMonSetMoveInSlot':'dd6c45a958ac7fb1e921f5626e3acf18d53c693b8dec0cf84f38f8e5f927fbf7','SetBoxMonData':'c68e773ab7107e20be3f04ead24c335452720b67893224849aeb69d044055fcd'},
        CPU_executed=False,ROM_opened=False,compiler_invoked=False,original_C_codegen_reconstructed=False,
        scope='Source definitions equal across two clean pins only; no new compiled-byte/ABI/runtime/language-target claim')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in('reference','heartgold-ref','json'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args()
    try:
        out=a.json.resolve();need(out!=SOURCE and SOURCE not in out.parents and not out.exists()and not out.is_symlink(),'fresh private C-definition comparison output')
        result=compare(a.reference,a.heartgold_ref)
        with out.open('x')as f:json.dump(result,f,indent=2);f.write('\n')
    except(ValueError,OSError,subprocess.CalledProcessError,UnicodeError)as e:p.exit(2,str(e)+'\n')
    print('Six actual pinned C definitions identical; exact definition hashes, no ROM/CPU/compiler')


if __name__=='__main__':main()
