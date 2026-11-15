#!/usr/bin/env python3
"""Prepare or compile the owned continuous dispatch fixture, never a game ROM."""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import struct
import subprocess
import sys

HERE=Path(__file__).resolve();SOURCE=HERE.parents[3];ASM=HERE.parents[1]/'test/shellbell_dispatch.S'
BASE=0x022F1000;TABLE=0x0226CA90
COMPILER_SHA='fc5e3cbba6ad54059295cad716aacb05ace8235f5f7a6031f1d8c15d24bd6d66'
LOADER_SHA='fff73b384cacedae6525b72a46665a05f3c9710a4ff789fd296568e82e2ce1a8'
ASM_SHA='78420e149e8d168f390825e8533912cbdbe309ba503d8c4b3b1bbe11ab398ba8'
FLAGS=('--target=armv5te-none-eabi','-mcpu=arm946e-s','-mthumb','-ffreestanding','-fno-builtin','-x','assembler-with-cpp')
FUNCTIONS=(('shellbell_dispatch',1,32),('shellbell_owned_first',33,6),('shellbell_owned_second',39,6))
CODE_HALFWORDS=(0xb570,0x1c04,0x1c0d,0x4e05,0x68aa,0x2a27,0xd005,0x0092,0x58b3,0x1c20,0x1c29,0x4798,0xe7f6,0xbd70)


def need(value,message):
    if not value:raise ValueError(message)


def sha(data):return hashlib.sha256(data).hexdigest()


def exact(a,b):
    """Typed recursive equality for receipts, including dictionary key types."""
    if type(a)is not type(b):return False
    if type(a)is dict:
        if any(type(k)not in(str,int)for k in(*a,*b)):return False
        left={(type(k),k)for k in a};right={(type(k),k)for k in b}
        return left==right and all(exact(a[k],b[k])for k in a)
    if type(a)in(list,tuple):return len(a)==len(b)and all(exact(x,y)for x,y in zip(a,b))
    return type(a)in(str,int,bool,bytes,type(None))and a==b


def load(path,name):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


def own_text():
    return struct.pack('<14H',*CODE_HALFWORDS)+struct.pack('<I',TABLE)+struct.pack('<6H',0x201d,0x6088,0x4770,0x2027,0x6088,0x4770)


def validate_text(text,symbols):
    need(type(text)is bytes and text==own_text(),'exact owned44-byte text, code/pool/handlers')
    need(type(symbols)is dict and all(symbols.get(name)==BASE+value for name,value,_ in FUNCTIONS),'three exact owned Thumb entry symbols')
    return dict(bytes=44,sha256=sha(text),driver_code=[BASE,BASE+28],literal=[BASE+28,BASE+32],owned_handlers=[[BASE+32,BASE+38],[BASE+38,BASE+44]],
        driver_starts=14,total_starts=20,table=TABLE,frame_bytes=16,BLX_register=3,stop_command=39,
        scope='Owned driver and handlers only; no game insertion or original dispatcher')


def inspect_object(data):
    """Bounded ELF readback independent of the retained text loader."""
    need(type(data)is bytes and 52<=len(data)<=1024**2 and data[:7]==b'\x7fELF\x01\x01\x01','bounded ELF32LE')
    h=struct.unpack_from('<HHIIIIIHHHHHH',data,16)
    need(h[:5]==(1,40,1,0,0)and h[6:11]==(0x5000000,52,0,0,40),'ARM ET_REL EABI5, no program headers')
    off,count,strings_index=h[5],h[11],h[12]
    need(1<count<=32 and off>=52 and off%4==0 and off+40*count==len(data)and 0<strings_index<count,'bounded complete section table')
    sections=[struct.unpack_from('<10I',data,off+40*i)for i in range(count)]
    def content(row):
        start,size=row[4:6];need(start+size<=off and (start>=52 if size else True),'bounded non-header section data');return data[start:start+size]
    def string(table,i):
        need(0<=i<len(table),'bounded ELF string');end=table.find(b'\0',i);need(end>=i,'terminated ELF string');return table[i:end].decode('ascii')
    labels=[string(content(sections[strings_index]),s[0])for s in sections];need(labels.count('.text')==1 and labels.count('.symtab')==1,'unique text and symbols')
    intervals=sorted((s[4],s[4]+s[5])for s in sections if s[5]);need(all(a[1]<=b[0]for a,b in zip(intervals,intervals[1:])),'nonoverlapping section payloads')
    for label,row in zip(labels,sections):
        need(label in('','.strtab','.text','.ARM.attributes','.symtab','.note.GNU-stack'),'only bounded assembly sections')
        need(row[3]==0 and row[1]not in(4,9),'no runtime addresses or relocations in owned object')
        need(not(row[2]&2 and row[5]and label!='.text'),'no other allocated payload')
    text_index=labels.index('.text');textrow=sections[text_index];need(textrow[1:4]==(1,6,0)and textrow[8]==4,'executable aligned text')
    text=content(textrow);symrow=sections[labels.index('.symtab')];need(symrow[1]==2 and symrow[9]==16 and symrow[5]%16==0 and symrow[6]<count,'symbol table geometry')
    strings=content(sections[symrow[6]]);symbols=[];names={}
    for n,v,size,info,other,index in struct.iter_unpack('<IIIBBH',content(symrow)):
        name=string(strings,n);symbols.append(dict(name=name,value=v,bytes=size,info=info,other=other,section=index))
        need(not(name and index==0 and info&0xf0),'no undefined external symbols')
        if index==text_index and name:names[name]=BASE+v
    funcs=[row for row in symbols if row['name']in {x[0]for x in FUNCTIONS}]
    need([(s['name'],s['value'],s['bytes'])for s in funcs]==list(FUNCTIONS)and all(s['info']==0x12 and s['section']==text_index for s in funcs),'owned function definitions/sizes')
    mapping=[s for s in symbols if s['name'].split('.')[0]in('$t','$d')]
    need([(s['name'].split('.')[0],s['value'])for s in mapping]==[('$t',0),('$d',28),('$t',32)],'ordered code/data/code mapping symbols')
    need(all((m['section'],m['info'],m['bytes'],m['other'])==(text_index,0,0,0)for m in mapping),'local NOTYPE mapping symbols belong to text with zero size/visibility')
    result=validate_text(text,names);result.update(object_bytes=len(data),object_sha256=sha(data),section_names=labels,symbols=symbols,mappings=mapping,relocations=0)
    return text,names,result


def save_new(path,value):
    with path.open('x')as out:json.dump(value,out,indent=2);out.write('\n')


def prepare(out):
    need(sha(ASM.read_bytes())==ASM_SHA,'owned assembly source identity')
    compiler=load(SOURCE/'sgp13/compiler.py','owned_dispatch_protected_compiler')
    selected=compiler.compiler_path(COMPILER_SHA)
    loader=SOURCE/'features/native-core/tools/carica_text.py';need(sha(loader.read_bytes())==LOADER_SHA,'retained loader identity')
    return dict(schema='owned-ShellBell-dispatch-source-v1',source_sha256=ASM_SHA,compiler=dict(path=selected,sha256=COMPILER_SHA,flags=list(FLAGS)),loader_sha256=LOADER_SHA,
        expected_text_sha256=sha(own_text()),expected_profile=validate_text(own_text(),{name:BASE+value for name,value,_ in FUNCTIONS}),compiler_invoked=False,CPU_executed=False)


def build(mode,out):
    out=Path(out).resolve();need(out!=SOURCE and SOURCE not in out.parents and not out.exists(),'fresh private build directory');out.mkdir(parents=True)
    recipe=prepare(out);save_new(out/'source-before-compiler.json',recipe)
    if mode=='prepare':return recipe
    compiler=load(SOURCE/'sgp13/compiler.py','owned_dispatch_compiler_environment');obj=out/'dispatch.o'
    argv=[recipe['compiler']['path'],*FLAGS,'-c',str(ASM),'-o',str(obj)]
    done=subprocess.run(argv,env=compiler.compiler_environment(),capture_output=True,timeout=30)
    log_cap=2*1024**2;stdout=done.stdout[:log_cap];stderr=done.stderr[:max(0,log_cap-len(stdout))]
    (out/'compiler.stdout').write_bytes(stdout);(out/'compiler.stderr').write_bytes(stderr)
    save_new(out/'compiler-receipt.json',dict(argv=argv,exit_code=done.returncode,stdout_sha256=sha(stdout),stderr_sha256=sha(stderr),driver_invocations=1,timeout_s=30,stdout_bytes=len(done.stdout),stderr_bytes=len(done.stderr),log_truncated=len(stdout)+len(stderr)!=len(done.stdout)+len(done.stderr)))
    need(done.returncode==0 and not done.stderr and len(stdout)+len(stderr)==len(done.stdout)+len(done.stderr),'owned driver assembly failed/truncated; preserve artifacts')
    need(obj.stat().st_size<=1024**2,'owned object exceeds1MiB')
    data=obj.read_bytes();text,symbols,readback=inspect_object(data)
    loader=load(SOURCE/'features/native-core/tools/carica_text.py','owned_dispatch_retained_loader');linked,names=loader.load_text(data,BASE,tuple(name for name,_,_ in FUNCTIONS))
    need(linked==text and all(names[name]==symbols[name]for name,_,_ in FUNCTIONS),'independent raw ELF/text loader agreement')
    (out/'dispatch.bin').write_bytes(text);save_new(out/'readback.json',readback)
    return dict(recipe=recipe,readback=readback,compiler_invoked=True,CPU_executed=False)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--mode',choices=('prepare','compile'),required=True);p.add_argument('--out-dir',type=Path,required=True);a=p.parse_args()
    try:result=build(a.mode,a.out_dir)
    except(ValueError,OSError,subprocess.SubprocessError,UnicodeError)as e:p.exit(1,str(e)+'\n')
    print('Owned driver '+a.mode+' complete; no ROM or guest execution.')


if __name__=='__main__':main()
