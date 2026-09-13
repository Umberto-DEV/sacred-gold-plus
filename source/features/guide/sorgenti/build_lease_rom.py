#!/usr/bin/env python3
"""Compose unchanged r5 plus a private NNS lease gate from exact Plus EN/IT bases."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
sys.path.insert(0,str(ROOT/'native-eviv'))
from build_test_rom import build as build_r5
from rom_container import append_files
from native_image import require, replace_arm9
from thumb_object import load_text
from ndspy.rom import NintendoDSRom

PROBE_BASE=0x01FF8880
MARKER=0x01FF9F00
ARENA_END=0x01FFA000
BASES={
 '3ed4ea0291092d46def2f71454821bbde7832014ec020680468af7bfca686248':('en','a1d7ed3ecb8aa98f96f65c17015cb49df5bda84323459cb17fd3d4c4501f556e'),
 '217daa45f4945abd3feda6f583f5163db029d1aa361c33c18f12b32ad4eca4a4':('it','96c41b594349e22c34789a52123327093b78e92a5be926f4e3000dd32a8e8ed3')}

def digest(data): return hashlib.sha256(data).hexdigest()

def abi(static):
    evidence=json.loads((HERE/'lease-abi.json').read_text())
    for name,item in evidence.items():
        offset=item['address']-0x02000000
        require(digest(static[offset:offset+item['bytes']])==item['sha256'],'ABI preimage differs: '+name)
    return evidence


def extend(main,payload,entry):
    require(len(main.sections)==3,'Unexpected sections')
    static,itcm,dtcm=main.sections
    require(static.ramAddress==0x02000000 and len(static.data)==0x111860,'Wrong static extent')
    require(itcm.ramAddress==0x01FF8000 and len(itcm.data)==0x880 and itcm.bssSize==0,'Wrong r5 ITCM extent')
    require(dtcm.ramAddress==0x027e0000 and len(dtcm.data)==0x60 and dtcm.bssSize==0x20,'Wrong DTCM extent')
    require(static.data[0x88b40:0x88b48]==struct.pack('<HHI',0x4b00,0x4718,0x01ff883d),'Wrong r5 input hook')
    require(static.data[0x8d178:0x8d180]==struct.pack('<HHI',0x4b00,0x4718,0x01ff881d),'Wrong r5 redraw hook')
    require(digest(itcm.data[0x620:0x870])=='6865177a8e819d603bbcfd3bce5c324566780dd01aa4d6793d052a17b57bc1c0','Wrong r5 payload')
    require(itcm.data[0x870:]==bytes(16),'Wrong r5 alignment padding')
    require(struct.unpack_from('<I',static.data,0xd2c68)[0]==PROBE_BASE,'Wrong r5 arenaLow')
    require(payload and PROBE_BASE+len(payload)<=MARKER,'Probe code overlaps marker reservation')
    require(entry&1 and PROBE_BASE<=(entry&~1)<PROBE_BASE+len(payload),'Entry outside Thumb payload')
    evidence=abi(static.data)
    # All validation precedes mutation, including full helper function preimages.
    static.data[0x88b40:0x88b48]=struct.pack('<HHI',0x4b00,0x4718,entry)
    struct.pack_into('<I',static.data,0xd2c68,ARENA_END)
    itcm.data.extend(payload)
    itcm.data.extend(bytes(ARENA_END-itcm.ramAddress-len(itcm.data)))
    return evidence


def build(source,charmap,out):
    require(not out.exists(),'Output directory must be new')
    source_bytes=source.read_bytes();source_sha=digest(source_bytes)
    require(source_sha in BASES,'Unknown complete Plus base')
    require(out.resolve().is_relative_to(Path('/private/tmp')),'Private output must be under /private/tmp')
    lang,expected_r5=BASES[source_sha]
    original=NintendoDSRom(source_bytes)
    abi(original.loadArm9().sections[0].data)
    # Original builder and loader are imported byte-identically, never relaxed.
    r5=build_r5(source,charmap,out/'r5')
    require(r5['rom_sha256']==expected_r5,'Fresh r5 reconstruction hash differs')
    r5_bytes=(out/'r5'/r5['rom_file']).read_bytes()
    main=NintendoDSRom(r5_bytes).loadArm9()
    before=[bytes(s.data) for s in main.sections]
    obj=out/'lease.o'
    command=['clang','--target=armv5te-none-eabi','-mcpu=arm946e-s','-mthumb','-Oz',
       '-ffreestanding','-fno-builtin','-fno-stack-protector','-fno-unwind-tables',
       '-fno-asynchronous-unwind-tables','-fno-jump-tables','-Wall','-Wextra','-Werror',
       '-c',str(HERE/'lease_probe.c'),'-o',str(obj)]
    compilation=subprocess.run(command,text=True,capture_output=True)
    (out/'compile.log').write_text(compilation.stdout+compilation.stderr)
    require(compilation.returncode==0,'Probe ARM compilation failed')
    payload,symbols=load_text(obj.read_bytes(),PROBE_BASE)
    evidence=extend(main,payload,symbols['eviv_hook'])
    # Keep the exact original ARM9 extent guard, then append r5 messages.
    arm9=main.save(compress=True)
    result=replace_arm9(source_bytes,arm9)
    result,_=append_files(result,{'a/0/2/7':NintendoDSRom(r5_bytes).getFileByName('a/0/2/7')},reuse_existing=True)
    check=NintendoDSRom(result);actual=check.loadArm9()
    # ndspy.save rewrites only the autoload table addresses and compressed end.
    require(main.codeSettingsOffs==0xba0,'Unexpected code settings location')
    expected_static=bytearray(main.sections[0].data)
    table=0x02000000+sum(len(s.data) for s in main.sections)
    struct.pack_into('<II',expected_static,0xba0,table,table+24)
    struct.pack_into('<I',expected_static,0xbb4,0x02000000+len(arm9))
    require(bytes(actual.sections[0].data)==bytes(expected_static)
            and [bytes(s.data) for s in actual.sections[1:]]==[bytes(s.data) for s in main.sections[1:]],'ARM9 roundtrip differs')
    require(bytes(actual.sections[1].data[:0x880])==before[1] and bytes(actual.sections[2].data)==before[2], 'r5 ITCM or DTCM changed')
    changed={i for i,(a,b) in enumerate(zip(before[0],actual.sections[0].data)) if a!=b}
    require(changed <= set(range(0x88b40,0x88b48))|set(range(0xd2c68,0xd2c6c))|set(range(0xba0,0xba8))|set(range(0xbb4,0xbb8)),'Unexpected static change')
    r5nds=NintendoDSRom(r5_bytes)
    require(check.files==r5nds.files and check.arm7==r5nds.arm7 and check.arm9OverlayTable==r5nds.arm9OverlayTable
            and check.arm7OverlayTable==r5nds.arm7OverlayTable,'Unselected ROM content changed')
    target=out/f'Native Lease TEST {lang.upper()}.nds';target.write_bytes(result)
    require(digest(source.read_bytes())==source_sha,'Base input changed')
    meta={'kind':'private-native-guide-lease-gate-not-guide-ui','language':lang,'base_sha256':source_sha,
          'r5_sha256':expected_r5,'rom_file':target.name,'rom_sha256':digest(result),
          'source_sha256':{p.name:digest(p.read_bytes()) for p in [HERE/'lease.c',HERE/'lease_probe.c',Path(__file__),HERE/'lease-abi.json']},
          'payload_sha256':digest(payload),'payload_bytes':len(payload),'object_sha256':digest(obj.read_bytes()),
          'symbols':symbols,'compile_command':command,'abi_preimages':evidence,
          'memory':{'code_start':PROBE_BASE,'code_end':PROBE_BASE+len(payload),'marker_start':MARKER,'marker_bytes':256,'arena_low_after':ARENA_END},
          'r5_payload_and_redraw_hook_preserved':True,'unselected_rom_data_preserved':True}
    (out/'build.json').write_text(json.dumps(meta,indent=2)+'\n')
    return meta

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ['rom','charmap','out']:p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();print(json.dumps(build(a.rom.resolve(),a.charmap.resolve(),a.out.resolve())))
