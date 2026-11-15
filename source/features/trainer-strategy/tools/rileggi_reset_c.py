#!/usr/bin/env python3
"""Read back the qualified Reset LLVM ELF profile without compiling or executing.

This deliberately accepts one bounded codegen/ABI profile, not arbitrary ARM
objects. All mapping symbols are kept. The unchanged native-core loader is
cross-checked by independent BL decoding, and its ignored exidx is validated.
"""
from pathlib import Path
import argparse
import importlib.util
import json
import struct


def load(path,name):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


HERE=Path(__file__).resolve();S=load(HERE.with_name('compila_reset_c.py'),'Reset_C_ELF_recipe')
need,sha=S.need,S.sha
L=load(S.LOADER,'Reset_C_unchanged_text_loader')
ROOT=S.BODY_NAME
FUNCTIONS=(('MonSetMoveInSlot',1,8),('SetMonData',9,8),('GetMoveMaxPP',17,8),(ROOT,25,52))
MAPPINGS=(('$t',0),('$d',4),('$t',8),('$d',12),('$t',16),('$d',20),('$t',24))
# Exact current LLVM orchestration profile. Strings denote four raw BL sites.
ROOT_PROFILE=(0xb5fe,0x0014,0x000e,0x0005,'MonSetMoveInSlot',0x2700,0x9701,
              0x0021,0x313e,0xaa01,0x0028,'SetMonData',0x0030,0x0039,'GetMoveMaxPP',
              0x9002,0x343a,0xaa02,0x0028,0x0021,'SetMonData',0xbdfe)
SECTION_PROFILE={'.strtab':(3,0,0,0,1,0),'.text':(1,6,0,0,4,0),
    '.rel.text':(9,64,10,2,4,8),'.ARM.exidx':(0x70000001,130,2,0,4,0),
    '.rel.ARM.exidx':(9,64,10,4,4,8),'.comment':(1,48,0,0,1,1),
    '.note.GNU-stack':(1,0,0,0,1,0),'.ARM.attributes':(0x70000003,0,0,0,1,0),
    '.llvm_addrsig':(0x6fff4c03,0x80000000,10,0,1,0),'.symtab':(2,0,1,10,4,16)}


def signed(value,bits):return value-(1<<bits)if value&(1<<(bits-1))else value


def bl_addend(data,offset):
    need(0<=offset<=len(data)-4,'bounded Thumb BL offset')
    hi,lo=struct.unpack_from('<HH',data,offset)
    need(hi&0xf800==0xf000 and lo&0xf800==0xf800,'Thumb1 BL pair')
    return signed(((hi&0x7ff)<<12)|((lo&0x7ff)<<1),23)


def inspect_elf(data,base=S.BASE):
    need(type(data)is bytes and 52<=len(data)<=1024**2,'ELF bytes1MiB bound')
    need(type(base)is int and base==S.BASE,'qualified disjoint code base')
    need(data[:16]==b'\x7fELF\x01\x01\x01'+b'\0'*9,'ELF32 little endian version1/SystemV')
    h=struct.unpack_from('<HHIIIIIHHHHHH',data,16)
    need(h[:5]==(1,40,1,0,0)and h[6:11]==(0x5000000,52,0,0,40),'ARM ET_REL EABI5 with no program headers')
    shoff,count,strings_index=h[5],h[11],h[12]
    need(1<=count<=64 and shoff>=52 and shoff%4==0 and shoff+40*count==len(data)
         and strings_index==1,'bounded complete section table and exact profile string table')
    sections=[]
    for i in range(count):
        n,t,flags,addr,off,size,link,info,align,ent=struct.unpack_from('<10I',data,shoff+40*i)
        need(addr==0 and off+size<=shoff and align in(0,1,2,4,8,16)and(off%align==0 if align else off==0),'section bounds/address/alignment')
        need(not size or off>=52,'nonempty section outside ELF header')
        sections.append(dict(index=i,name_index=n,type=t,flags=flags,offset=off,bytes=size,link=link,info=info,align=align,entry_bytes=ent))
    need(sections[0]==dict(index=0,name_index=0,type=0,flags=0,offset=0,bytes=0,link=0,info=0,align=0,entry_bytes=0),'null section')
    def content(s):return data[s['offset']:s['offset']+s['bytes']]
    def string(table,index):
        need(0<=index<len(table),'bounded string index');end=table.find(b'\0',index)
        need(end>=index,'terminated ELF string')
        try:return table[index:end].decode('ascii')
        except UnicodeDecodeError:raise ValueError('ASCII ELF names required')from None
    labels=[string(content(sections[strings_index]),s['name_index'])for s in sections]
    need(labels==['',*SECTION_PROFILE],'exact qualified section set/order')
    for s,label in zip(sections,labels):
        s['name']=label
        if label:need(tuple(s[k]for k in('type','flags','link','info','align','entry_bytes'))==SECTION_PROFILE[label],'qualified section attributes '+label)
    intervals=sorted((s['offset'],s['offset']+s['bytes'])for s in sections if s['bytes'])
    need(all(a[1]<=b[0]for a,b in zip(intervals,intervals[1:])),'section payloads do not overlap')
    by={s['name']:s for s in sections};text=content(by['.text']);symsec=by['.symtab']
    need(len(text)==76 and len(text)<=4096 and symsec['bytes']==14*16,'qualified text and bounded symbol profile')
    need(by['.note.GNU-stack']['bytes']==by['.llvm_addrsig']['bytes']==0,'no extra stack/addrsig payload')
    need(by['.comment']['bytes']<=256 and 1<=by['.ARM.attributes']['bytes']<=4096
         and content(by['.ARM.attributes'])[:1]==b'A','bounded nonexecuted ELF annotations')
    symbols=[];strings=content(sections[symsec['link']])
    for i,(n,v,size,info,other,section)in enumerate(struct.iter_unpack('<IIIBBH',content(symsec))):
        symbols.append(dict(index=i,name=string(strings,n),value=v,bytes=size,info=info,other=other,section=section))
    need(symbols[0]==dict(index=0,name='',value=0,bytes=0,info=0,other=0,section=0),'null symbol')
    need(symbols[1]['name']and tuple(symbols[1][k]for k in('value','bytes','info','other','section'))==(0,0,4,0,0xfff1),'local source-file symbol')
    need(tuple(symbols[2][k]for k in('name','value','bytes','info','other','section'))==('',0,0,3,0,2),'local text section symbol')
    mapping=symbols[3:10]
    need([(s['name'],s['value'])for s in mapping]==list(MAPPINGS)
         and all(tuple(s[k]for k in('bytes','info','other','section'))==(0,0,0,2)for s in mapping),'all seven ordered mapping symbols including duplicates')
    funcs=symbols[10:]
    need([(s['name'],s['value'],s['bytes'])for s in funcs]==list(FUNCTIONS)
         and all((s['info'],s['other'],s['section'])==(0x12,0,2)for s in funcs),'four exact defined Thumb function symbols; no externals')
    calls=[];instructions=[];cursor=24
    for part in ROOT_PROFILE:
        if type(part)is str:
            need(bl_addend(text,cursor)==-4,'qualified raw internal BL addend−4')
            calls.append(dict(offset=cursor,callee=part,addend=-4));size=4
        else:
            need(struct.unpack_from('<H',text,cursor)[0]==part,'qualified root instruction/frame profile')
            size=2
        instructions.append(dict(offset=cursor,bytes=size));cursor+=size
    need(cursor==76 and len(instructions)==22,'complete root code coverage')
    for i,(name,target)in enumerate(S.TARGETS.items()):
        start=i*8
        need(text[start:start+4]==struct.pack('<HH',0x4b00,0x4718)
             and struct.unpack_from('<I',text,start+4)[0]==target,'exact LDR/BX thunk plus odd native literal '+name)
        instructions.extend((dict(offset=start,bytes=2),dict(offset=start+2,bytes=2)))
    rel=content(by['.rel.text'])
    need(len(rel)==32,'four and only four text relocations')
    target_by_name={s['name']:s for s in funcs}
    for call,(offset,info)in zip(calls,struct.iter_unpack('<II',rel)):
        symbol=target_by_name[call['callee']]
        need(offset==call['offset']and info==(symbol['index']<<8)|10,'ordered internal R_ARM_THM_CALL symbol/site')
        call.update(relocation_type=10,symbol_index=symbol['index'],instruction=base+offset,linked_target=base+(symbol['value']&~1))
    # The common loader permits exidx but ignores its relocation. Verify its
    # entire single entry, local section-symbol binding, addend and descriptor.
    need(by['.ARM.exidx']['bytes']==8 and by['.rel.ARM.exidx']['bytes']==8,'one complete exidx entry/relocation')
    first,descriptor=struct.unpack('<II',content(by['.ARM.exidx']))
    offset,info=struct.unpack('<II',content(by['.rel.ARM.exidx']))
    addend=signed(first&0x7fffffff,31)
    need(first>>31==0 and addend==24 and descriptor==1 and offset==0 and info==(2<<8)|42,'exidx PREL31 to root section offset24 and CANTUNWIND')
    # A synthetic place is used only to check PREL31 arithmetic; this metadata
    # is never installed/mapped. No unwinder is part of this finite execution.
    place=base+len(text);relocated=(base+addend-place)&0x7fffffff
    need(place+signed(relocated,31)==base+24,'independent PREL31 roundtrip')
    need(S.file_sha(S.LOADER)==S.LOADER_SHA,'unchanged qualified loader hash')
    linked,loader_symbols=L.load_text(data,base,entries=tuple(s[0]for s in FUNCTIONS))
    independent=bytearray(text)
    for call in calls:
        delta=call['linked_target']-(base+call['offset']+4)
        need(-0x400000<=delta<0x400000 and delta%2==0,'bounded independent BL displacement')
        struct.pack_into('<HH',independent,call['offset'],0xf000|((delta>>12)&0x7ff),0xf800|((delta>>1)&0x7ff))
        need(base+call['offset']+4+bl_addend(linked,call['offset'])==call['linked_target'],'independent linked BL target readback')
    need(linked==bytes(independent),'whole relocated-text readback independent from loader')
    need(all(loader_symbols[name]==base+value for name,value,_ in FUNCTIONS),'loader four function symbol readback')
    instructions=sorted(instructions,key=lambda x:x['offset'])
    for row in instructions:row.update(pc=base+row['offset'],hex=linked[row['offset']:row['offset']+row['bytes']].hex())
    return linked,dict(schema='native-Reset-C-ELF-readback-v1',ELF_bytes=len(data),ELF_sha256=sha(data),
        load_base=base,entry=base+25,linked_text_bytes=len(linked),linked_text_sha256=sha(linked),
        raw_text_sha256=sha(text),sections=sections,symbols=symbols,mapping_symbols=mapping,
        code_bytes=64,literal_bytes=12,instruction_count=28,instructions=instructions,calls=calls,
        literal_pools=[dict(address=base+i*8+4,bytes=4,target=v)for i,v in enumerate(S.TARGETS.values())],
        root_entry=base+24,root_bytes=52,root_instructions=22,root_frame_bytes=32,
        zero_value_offset_from_entry_SP=-28,PP_value_offset_from_entry_SP=-24,
        zero_store_preimage_origin='PUSH saved r2 (slot0 in this cell)',PP_store_preimage_origin='PUSH saved r3 entry cookie',
        exidx=dict(addend=addend,descriptor=descriptor,relocation_type=42,symbol_index=2,
                   target=base+24,mapped=False,verification_place_only=place,verification_PREL31=relocated),
        ARM_attributes_sha256=sha(content(by['.ARM.attributes'])),loader_sha256=S.LOADER_SHA,
        compiler_invoked=False,CPU_executed=False,original_MWC_matching=False,
        scope='Exact qualified LLVM profile only; annotations hashed, instructions structurally admitted, guest equivalence still separate')


def bounded_read(path,limit):
    need(path.is_file()and not path.is_symlink()and path.stat().st_size<=limit,'bounded regular build artifact '+path.name)
    return path.read_bytes()


def authenticate_build(build,reference,heartgold_ref):
    build=Path(build).resolve();tu,provenance=S.project_sources(reference,heartgold_ref)
    c=bounded_read(build/'candidate.c',64*1024);obj=bounded_read(build/'candidate.o',1024**2)
    recipe_raw=bounded_read(build/'source-recipe.json',64*1024);receipt_raw=bounded_read(build/'compiler-receipt.json',64*1024)
    recipe=json.loads(recipe_raw);receipt=json.loads(receipt_raw);log=bounded_read(build/'compiler.log',2*1024**2)
    need(c==tu.encode()and all(recipe.get(k)==v for k,v in provenance.items()),'literal TU and pinned reference/prototype/ABI recipe')
    need(recipe['schema']=='native-Reset-C-source-recipe-v1'and recipe['translation_unit_sha256']==sha(c)
         and recipe['translation_unit_bytes']==len(c)and recipe['compiler_sha256']==S.COMPILER_SHA
         and recipe['compiler_bytes']==S.COMPILER_BYTES and recipe['flags']==list(S.FLAGS)
         and recipe['load_base']==S.BASE and recipe['loader_sha256']==S.LOADER_SHA,'qualified compiler/flags/loader recipe')
    expected={str(p.relative_to(S.SOURCE)):S.file_sha(p)for p in(Path(S.__file__),Path(S.DEF.__file__),S.LOADER)}
    need(recipe['source_sha256']==expected,'current source recipe/lexical extractor/loader identities')
    need(receipt['schema']=='native-Reset-C-compiler-receipt-v1'and type(receipt['exit_code'])is int and receipt['exit_code']==0
         and receipt['timed_out']is False and receipt['log_truncated']is False and receipt['CPU_executed']is False
         and type(receipt['compiler_invocations'])is int and receipt['compiler_invocations']==1,'successful one-driver nonCPU compilation receipt')
    for key,value in dict(compiler_sha256=S.COMPILER_SHA,source_recipe_sha256=sha(recipe_raw),translation_unit_sha256=sha(c),
                          log_sha256=sha(log),ELF_bytes=len(obj),ELF_sha256=sha(obj)).items():
        need(receipt[key]==value,'compiler receipt artifact binding '+key)
    argv=receipt['argv']
    need(type(argv)is list and len(argv)>0 and Path(argv[0]).is_absolute()
         and argv[1:]==[*S.FLAGS,'-c',str(build/'candidate.c'),'-o',str(build/'candidate.o')],'exact recorded compiler argv')
    linked,result=inspect_elf(obj)
    result.update(source_recipe_sha256=sha(recipe_raw),compiler_receipt_sha256=sha(receipt_raw),
        translation_unit_sha256=sha(c),compiler_binary_currently_rehashed=False,
        source_sha256={str(p.relative_to(S.SOURCE)):S.file_sha(p)for p in(HERE,Path(S.__file__),Path(S.DEF.__file__),S.LOADER)})
    return linked,result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in('build-dir','reference','heartgold-ref','out-dir'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args()
    try:
        out=a.out_dir.resolve();need(out!=S.SOURCE and S.SOURCE not in out.parents and not out.exists()and not a.out_dir.is_symlink(),'fresh private readback directory')
        linked,result=authenticate_build(a.build_dir,a.reference,a.heartgold_ref);out.mkdir(parents=True)
        (out/'linked.bin').write_bytes(linked);S.save(out/'readback.json',result)
    except(ValueError,OSError,KeyError,IndexError,struct.error)as e:p.exit(2,str(e)+'\n')
    print('Qualified ELF/4internal BL/3guest thunk/exidx/32-byte ABI readback PASS; no compiler or CPU')


if __name__=='__main__':main()
