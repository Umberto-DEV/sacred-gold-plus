#!/usr/bin/env python3
"""Compose pinned LLVM code and the retained native memory fixture, no CPU.

The original Reset is authenticated as a reference and remains in its mapped
page; it is explicitly excluded from instruction admission. No ROM is changed.
"""
from pathlib import Path
import argparse
import importlib.util
import json


def load(path,name):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


HERE=Path(__file__).resolve();SOURCE=HERE.parents[3]
OLD=load(HERE.with_name('congela_mon_reset.py'),'compiled_Reset_retained_fixture')
ELF=load(HERE.with_name('rileggi_reset_c.py'),'compiled_Reset_ELF_readback')
N=OLD.L;R,M,need,sha=OLD.R,OLD.M,OLD.need,OLD.sha
BASE,ENTRY,RETURN,BOX=ELF.S.BASE,ELF.S.BASE+24,OLD.RETURN,OLD.BOX
STACK,FRAME,GUARD=1024,720,56
ROOT_FRAME=32;CHILD_TOP=R.TOP-ROOT_FRAME
ZERO_VALUE,RESET_PP_VALUE=R.TOP-28,R.TOP-24
MOVE_VALUE,PP_VALUE=R.TOP-44,R.TOP-64
FILE1,LOCAL1,DEST1=R.TOP-216,R.TOP-240,R.TOP-104
FILE2,LOCAL2,DEST2=R.TOP-184,R.TOP-208,R.TOP-72
PROFILES=dict(OLD.PROFILES);MATRIX=OLD.MATRIX
C_THUMB={
 'C_mon_thunk':(BASE,4,2,'8bdadb00ad3389fd9d10292c291d2b47f6d30d0531c80bbc0dbfbd0813d70c8c'),
 'C_set_thunk':(BASE+8,4,2,'8bdadb00ad3389fd9d10292c291d2b47f6d30d0531c80bbc0dbfbd0813d70c8c'),
 'C_max_thunk':(BASE+16,4,2,'8bdadb00ad3389fd9d10292c291d2b47f6d30d0531c80bbc0dbfbd0813d70c8c'),
 'C_reset':(BASE+24,52,22,'7474ad11f95ceeff10b749b3e6c1620fbf7d5e488849a08f532de6850d345830')}
C_DATA={
 'C_mon_target':(BASE+4,4,'d90ec72748b528a1ad133f93b125c7a17187e3211e6d4ba20ebdc804a0aee1bd'),
 'C_set_target':(BASE+12,4,'90c6e1ffeef60949c280807be3f48fbabd77199f7c0fc618bb4010a2a4414202'),
 'C_max_target':(BASE+20,4,'1aef11c74c9aebbfa5631a75d1020901fd50d2ee69e7c0b7b1f6406a8d729e80')}
THUMB={**{k:v for k,v in N.THUMB.items()if k!='reset'},**C_THUMB}
DATA={**N.DATA,**C_DATA};CODE_SPANS,SDK_CODE_SPANS=N.CODE_SPANS,N.SDK_CODE_SPANS


def instruction_parts(parts):
    need(type(parts)is dict and set(THUMB)<=set(parts),'complete admitted C/native instruction subset')
    return {name:parts[name]for name in THUMB}


def thumb_code(parts):
    from capstone import Cs,CS_ARCH_ARM,CS_MODE_THUMB
    # Both the source predictor and CPU producer supply admitted instructions.
    # The CPU intentionally supplies no inactive Reset or data-table entries.
    # The original Reset reference is authenticated separately by prepare().
    selected=instruction_parts(parts);code={}
    for name,(address,size,count,digest)in THUMB.items():
        blob=selected[name];need(type(blob)is bytes and len(blob)==size and sha(blob)==digest,'qualified C/native code component '+name)
        rows=list(Cs(CS_ARCH_ARM,CS_MODE_THUMB).disasm(blob,address))
        need(len(rows)==count and sum(i.size for i in rows)==size,'complete C Thumb instruction coverage '+name)
        for i in rows:need(i.address not in code,'disjoint C instruction starts');code[i.address]=bytes(i.bytes)
    need(len(code)==516 and sum(len(b)for b in code.values())==1140
         and not any(0x20714b0<=pc<0x20714e8 for pc in code),'compiled caller516starts and original Reset excluded')
    return code


def make_input(parts,ups=3):
    need(type(parts)is dict,'typed composed C parts')
    native={k:v for k,v in parts.items()if k not in C_THUMB and k not in C_DATA}
    f=OLD.make_input(native,ups);pages={a:bytearray(b)for a,b in f['pages'].items()}
    need(set(parts)==set(native)|set(C_THUMB)|set(C_DATA),'complete C/native part namespace')
    regions=dict(mon=(BOX-16,268),stack=(R.TOP-STACK-GUARD,STACK+GUARD),stop=(RETURN,4),
        archive=(R.ARC,92),fat=(R.FAT,4104),fnt=(R.FNT,2902),root=(OLD.P.P.ROOT,12),inactive_Reset=(0x20714b0,56))
    regions.update({k:v[:2]for k,v in{**THUMB,**DATA}.items()})
    regions.update({'sdk_'+k:v[:2]for k,v in OLD.P.P.SDK.COMPONENTS.items()});regions['division']=N.C.MX.DIV[:2]
    regions.update({'payload_'+hex(a):(OLD.P.P.SDK.ARCHIVE_BASE+0x1093800+a,n)for a,n in OLD.P.P.NARC.WINDOWS})
    R.require_disjoint(regions)
    for name,item in{**C_THUMB,**C_DATA}.items():
        a,n,digest=item[0],item[1],item[-1];blob=parts[name]
        need(type(blob)is bytes and len(blob)==n and sha(blob)==digest,'exact composed C bytes '+name)
        for page in range(a&~4095,(a+n+4095)&~4095,4096):pages.setdefault(page,bytearray(b'\xa5'*4096))
        M.put(pages,a,blob)
    need(M.read(pages,R.TOP-STACK-GUARD,STACK+GUARD)==b'\xa5'*(STACK+GUARD),'C stack1024/guard56 untouched')
    need(len(pages)==27,'compiled C exact27-page geometry')
    f.update(resource_parts=parts,entry_pc=ENTRY,pages={a:bytes(b)for a,b in pages.items()})
    return f


def input_record(f):
    pages=f['pages'];mon,plain,party=OLD.MON.owned_mon(f['input_Up'])
    need(f['input_PP']==15 and f['payload_projections']==[],'compiled C unprojected PP15')
    return dict(input_Up=f['input_Up'],input_move=310,input_slot=0,input_PP=15,entry_pc=f['entry_pc'],entry_regs=f['entry_regs'],
        register_format='R0..R14 then CPSR; PC separate',
        data_provenance='Retained owned encrypted Mon236 and original PP15 archive; no save/player input',
        resource_parts_sha256={n:sha(b)for n,b in sorted(f['resource_parts'].items())},
        mon236_sha256=sha(mon),Box_plaintext128_sha256=sha(plain),party_plaintext100_sha256=sha(party),
        archive_projections=f['archive_projections'],payload_projections=f['payload_projections'],
        original_member_sha256=OLD.P.P.SDK.MEMBER_SHA,initial_map_sha256=M.map_digest(pages),
        pages=[dict(ram=a,bytes=len(b),sha256=sha(b))for a,b in sorted(pages.items())],
        stack1024_sha256=sha(M.read(pages,R.TOP-STACK,STACK)),guard56_hex=M.read(pages,R.TOP-STACK-GUARD,GUARD).hex(),
        C_Value_words_initial_hex=M.read(pages,ZERO_VALUE,8).hex(),
        mon_guard16_before=M.read(pages,BOX-16,16).hex(),mon_guard16_after=M.read(pages,BOX+236,16).hex(),
        inactive_native_Reset_mapped=True,inactive_native_Reset_fetch_admitted=False)


def prepare(rom,build_dir,reference,heartgold_ref,it_rom=None):
    receipt,parts=N.prepare(rom,it_rom);linked,readback=ELF.authenticate_build(build_dir,reference,heartgold_ref)
    for name,item in{**C_THUMB,**C_DATA}.items():
        a,n=item[:2];blob=linked[a-BASE:a-BASE+n];need(sha(blob)==item[-1],'C readback-to-fixture component '+name);parts[name]=blob
    code=thumb_code(parts)
    return dict(schema='compiled-Reset-C-resources-v1',native_reference=receipt,C_readback=readback,
        Thumb_starts=len(code),Thumb_bytes=1140,CPU_executed=False,compiler_invoked=False,
        original_Reset_fetch_admitted=False),parts


def freeze(receipt,parts):
    return dict(schema='compiled-Reset-C-input-v1',resources_receipt_sha256=sha((json.dumps(receipt,indent=2)+'\n').encode()),
        policy=dict(models=0,runtime_host_writes=0,instruction_cap=65536,unchanged_ARM_cap=8192,timeout_us=1000000,
            stack_top=R.TOP,stack_bytes=STACK,guard_bytes=GUARD,expected_peak=FRAME,root_frame_bytes=ROOT_FRAME,
            Zero_Value=ZERO_VALUE,PP_Value=RESET_PP_VALUE,first_FILE=FILE1,second_FILE=FILE2,stop_pc=RETURN,
            original_Reset_fetch_admitted=False),fixtures={k:input_record(make_input(parts,v))for k,v in PROFILES.items()},
        matrix=[dict(name=name,input_profile=key,observed=observe)for name,key,observe in MATRIX])


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in('rom','build-dir','reference','heartgold-ref','json'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args()
    try:
        out=a.json.resolve();need(SOURCE not in out.parents and out!=SOURCE and not out.exists()and not out.is_symlink(),'fresh private C input contract')
        receipt,parts=prepare(a.rom,a.build_dir,a.reference,a.heartgold_ref);ELF.S.save(out,freeze(receipt,parts))
    except(ValueError,OSError,EOFError,KeyError)as e:p.exit(2,str(e)+'\n')
    print('C code/native archive/owned Mon236/stack1024+guard56 frozen; no compiler or CPU')


if __name__=='__main__':main()
