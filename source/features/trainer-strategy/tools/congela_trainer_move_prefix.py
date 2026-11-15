#!/usr/bin/env python3
"""Freeze explicit owned state inside the first type3 trainer move loop.

This is a synthetic prefix entry, never a reconstructed lossless historical
checkpoint. Mon tail100 is an owned nonaccess pattern; record108 is read from
the exact supplied ROM. No constructor, predictor or CPU is executed.
"""
from pathlib import Path
import argparse
import importlib.util
import json
import struct
import types


def load(path,name):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


HERE=Path(__file__).resolve()
L=load(HERE.with_name('rileggi_trainer_move_prefix.py'),'trainer_prefix_frozen_resources')
P=load(HERE.with_name('congela_box_move_caller.py'),'trainer_prefix_retained_own_Box')
M,need,sha=P.M,P.need,P.sha
TOP,CALLER_FRAME=0x23fd000,152
SP=TOP-CALLER_FRAME
R=types.SimpleNamespace(**{**vars(P.R),'TOP':SP})
ENTRY,RETURN,BOX,RECORD=0x2073a22,0x2073a40,0x22f0000,0x22f0200
FRAME,GUARD=688,56
MOVE_VALUE,PP_VALUE,FILE,LOCAL,DEST=(SP-n for n in(12,32,184,208,72))
PROFILES=P.PROFILES
MATRIX=P.MATRIX
NEW_NAMES=set(L.NEW_THUMB)|set(L.NEW_DATA)|{'prefix_gate','trainer_header','trainer_record'}
base_input_record=types.FunctionType(P.input_record.__code__,{**P.input_record.__globals__,'R':R},argdefs=P.input_record.__defaults__)


def entry_regs():
    regs=[0xb0000000+i*0x010101 for i in range(13)]+[SP,0x0ddd0001,0x6000003f]
    regs[6]=BOX;return regs


def caller_frame():
    b=bytearray(b'\xa5'*152);struct.pack_into('<I',b,0x64,RECORD);struct.pack_into('<I',b,0x5c,0xdeadc0de);return bytes(b)


def owned_tail():return bytes((0x51+37*i)&255 for i in range(100))


def make_input(parts,ups=3):
    need(type(parts)is dict and NEW_NAMES<=set(parts),'complete prefix resources')
    L.record_layout(parts['trainer_header'],parts['trainer_record'])
    shared={name:b for name,b in parts.items()if name not in NEW_NAMES};f=P.make_input(shared,ups)
    pages={a:bytearray(b)for a,b in f['pages'].items()}
    def put(a,b):
        for base in range(a&~4095,(a+len(b)+4095)&~4095,4096):pages.setdefault(base,bytearray(b'\xa5'*4096))
        M.put(pages,a,b)
    regions=dict(mon=(BOX-16,268),record=(RECORD-16,140),native_stack=(SP-FRAME-GUARD,FRAME+GUARD),caller_frame=(SP,CALLER_FRAME),excluded_gate=L.GATE[:2],
        arc=(R.ARC,92),fat=(R.FAT,4104),fnt=(R.FNT,2902),root=(P.P.ROOT,12))
    regions.update({name:item[:2]for name,item in{**L.THUMB,**L.DATA}.items()})
    regions.update({'sdk_'+name:item[:2]for name,item in P.P.SDK.COMPONENTS.items()});regions['division']=L.C.MX.DIV[:2]
    regions.update({'payload_'+hex(a):(P.P.SDK.ARCHIVE_BASE+0x1093800+a,n)for a,n in P.P.NARC.WINDOWS});R.require_disjoint(regions)
    for name,item in{**L.NEW_THUMB,**L.NEW_DATA,'prefix_gate':L.GATE}.items():
        a,n,digest=item[0],item[1],item[-1];b=parts[name]
        need(type(b)is bytes and len(b)==n and sha(b)==digest,'prefix frozen new byte component '+name);put(a,b)
    box,_=P.owned_box(ups)
    # This prepares a new input before entry, not an in-execution replacement
    # of the earlier Box guard or an observed native party-tail checkpoint.
    put(BOX-16,b'\xd3'*16+box+owned_tail()+b'\xd3'*16)
    put(RECORD-16,b'\xd3'*16+parts['trainer_record']+b'\xd3'*16)
    need(M.read(pages,SP-FRAME-GUARD,FRAME+GUARD)==b'\xa5'*(FRAME+GUARD),'prefix native stack and lower guard start untouched')
    put(SP,caller_frame())
    f.update(resource_parts=parts,entry_pc=ENTRY,entry_regs=entry_regs(),pages={a:bytes(b)for a,b in pages.items()})
    return f


def input_record(f):
    data=base_input_record(f);data['tail_first16_hex']=data.pop('box_guard16_after')
    data.update(data_provenance='Owned synthetic prefix entry/Box136/tail100 pattern/frame152; exact ROM-derived record108/memory archive; no lossless historical checkpoint or personal save',
        function_top=TOP,entry_sp=SP,caller_frame_bytes=CALLER_FRAME,native_peak_budget=FRAME,total_envelope_to_function_top=840,guarded_envelope_to_function_top=896,
        stop_gate=RETURN,gate_instruction_executed=False,tail100_sha256=sha(M.read(f['pages'],BOX+136,100)),
        mon_guard16_after=M.read(f['pages'],BOX+236,16).hex(),record108_sha256=sha(M.read(f['pages'],RECORD,108)),
        record_guard16_before=M.read(f['pages'],RECORD-16,16).hex(),record_guard16_after=M.read(f['pages'],RECORD+108,16).hex(),
        caller_frame152_sha256=sha(M.read(f['pages'],SP,152)),current_pointer_word_hex=M.read(f['pages'],SP+0x64,4).hex(),cursor_word_hex=M.read(f['pages'],SP+0x5c,4).hex())
    return data


def freeze(receipt,parts):
    return dict(schema='native-trainer-first-move-prefix-input-v1',resources_receipt_sha256=sha((json.dumps(receipt,indent=2)+'\n').encode()),
        source_identities={str(p.relative_to(HERE.parents[3])):sha(p.read_bytes())for p in(HERE,Path(L.__file__),Path(P.__file__))},
        provenance='New explicit owned prefix fixture; earlier P55 packet/late registers are not composed into a fictitious lossless checkpoint',
        policy=dict(models=0,runtime_host_writes=0,instruction_cap=32768,timeout_us=1000000,spare_gate_callback_required=True,
            entry_pc=ENTRY,entry_sp=SP,function_top=TOP,caller_frame_bytes=152,native_stack_bytes=688,lower_guard_bytes=56,
            Mon=BOX,Box_bytes=136,nonaccess_tail_bytes=100,record=RECORD,record_bytes=108,current_pointer=SP+0x64,cursor=SP+0x5c,
            move_Value=MOVE_VALUE,PP_Value=PP_VALUE,client_file=FILE,parser_local=LOCAL,native_buffer=DEST,
            stop_gate=RETURN,stop_is_function_return=False,branch_at_gate_executed=False),
        fixtures={name:input_record(make_input(parts,ups))for name,ups in PROFILES.items()},
        matrix=[dict(name=name,input_profile=key,observed=observe)for name,key,observe in MATRIX])


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in('rom','json'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args()
    try:
        out=a.json.resolve();source=HERE.parents[3]
        need(out!=source and source not in out.parents and not out.exists()and not out.is_symlink(),'fresh private prefix input contract')
        receipt,parts=L.prepare(a.rom)
        with out.open('x')as f:json.dump(freeze(receipt,parts),f,indent=2);f.write('\n')
    except(ValueError,OSError,EOFError)as e:p.exit(2,str(e)+'\n')
    print('Two explicit prefix inputs and three-cell plan frozen; no prediction, CPU or compiler')


if __name__=='__main__':main()
