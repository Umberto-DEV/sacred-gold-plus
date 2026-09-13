#!/usr/bin/env python3
"""Focused existing-save and native touch/transition check; private artifacts only."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
from run_summary_guide import HERE, ROOT, enter, video, run, sha, require, current_build, loaded_code


def saved_fields(path):
    ram=path.read_bytes()
    # SaveData_Get/SaveArray_Get and the native size functions are pinned in
    # save-observer-abi.json. This is NOT the older fixture-specific mon base.
    base=struct.unpack_from('<I',ram,0x1d2228)[0]-0x02000000
    require(0<=base<=len(ram)-0x2330c,'SaveData outside main RAM')
    require(struct.unpack_from('<III',ram,base)==(1,1,0),'Not an existing normal save')
    fields={}
    for idx,name,size,keep in [(1,'options_profile_coins',48,38),(2,'party',1460,1456),
            (3,'bag',1952,1948),(4,'vars_flags',1104,1100),(6,'pokedex',836,832),
            (41,'all_pc_members',74496,0x12000)]:
        ident,actual,offset,crc,slot=struct.unpack_from('<IIIHH',ram,base+0x23014+idx*16)
        require((ident,actual,slot)==(idx,size,int(idx==41)),'Save array schema differs')
        start=base+0x10+offset
        require(0<=start<=len(ram)-size,'Save array outside RAM')
        fields[name]=ram[start:start+keep]
    return fields


def script(kind):
    names=['before','panel2','back-edges','touch-back','close-edges','touch-priority']
    s=enter(kind)+video('before')+'tap START 2 30\ntap A 2 20\n'+video('panel2')
    for x,y in [(15,168),(88,168),(50,159),(50,176)]:s+=f'touch {x} {y} 2\nrun 12\n'
    s+=video('back-edges')+'touch 16 160 2\nrun 20\n'+video('touch-back')
    for x,y in [(175,168),(240,168),(208,159),(208,176)]:s+=f'touch {x} {y} 2\nrun 12\n'
    s+=video('close-edges')+'tap A 2 20\ntouch 16 160\nrun 4 A+RIGHT\nrelease\nrun 20 NONE\n'+video('touch-priority')
    # Capture every emulated frame while B remains held, including hidden
    # transfer/restore phases and the first native OAM reappearance.
    for i in range(1,17):
        name=f'return-{i}';names.append(name);s+='run 1 B\n'+video(name)
    s+='run 30 NONE\ntap B 2 180\n'
    if kind=='party':s+='tap B 2 180\n'
    else:s+='tap B 8 240\ntap B 8 240\ntap DOWN 2 60\ntap A 8 360\ntap B 8 360\ntap B 8 360\n'
    s+=video('outside')+'sram unchanged.sav\ntouch 120 75 2\nrun 600\ntap A 8 600\ntap A 8 1600\n'+video('saved')+'sram normal-SAVE-TEST.sav\nquit\n'
    return s,names+['outside','saved']


def probe(rom,fixture,observer,out,kind,baseline):
    meta=current_build(rom,observer);require(not meta['pressure_test_instrumentation'],'Pressure ROM')
    runner=sha(Path(__file__));helper=sha(HERE/'run_summary_guide.py');abi=sha(HERE/'save-observer-abi.json')
    # Validate exact additional read-only observer ABI against this ROM.
    from ndspy.rom import NintendoDSRom
    arm=NintendoDSRom(rom.read_bytes()).loadArm9().sections[0].data
    for item in json.loads((HERE/'save-observer-abi.json').read_text())['ranges']:
        off=item['address']-0x02000000
        require(hashlib.sha256(arm[off:off+item['bytes']]).hexdigest()==item['sha256'],'SAVE ABI changed')
    commands,names=script(kind)
    execution=run(observer,rom,fixture,out,commands)
    markers={n:loaded_code(out,n,meta) for n in names}
    for n,panel in [('panel2',1),('back-edges',1),('touch-back',0),('close-edges',0),('touch-priority',0)]:
        require(markers[n][4:6]==(4,panel),'Touch boundary/precedence failed: '+n)
    require(all(m[14]==0 for m in markers.values()),'Ownership/canary error')
    require(markers['return-16'][1]==0 and markers['return-16'][4]==7,'Return never completed')
    require(markers['outside'][1:4]==(0,0,0),'Pointer survived teardown')
    from PIL import Image
    from run_summary_guide import return_graphics
    original=Image.open(out/'before.ppm')
    for i in range(1,17):
        name=f'return-{i}';frame=Image.open(out/(name+'.ppm'))
        if frame.getpixel((2,193))==original.getpixel((2,193)):
            return_graphics(out,'before',name)
    expected=saved_fields(baseline/'before.bin')
    for n in names:require(saved_fields(out/(n+'.bin'))==expected,'Identity/progression changed: '+n)
    require(sha(out/'unchanged.sav')==sha(fixture),'Guide changed SRAM before SAVE')
    saved=out/'normal-SAVE-TEST.sav';require(sha(saved)!=sha(fixture),'Normal SAVE did not execute')
    cold=run(observer,rom,saved,out/'cold-reload',
        (ROOT/'runtime/inputs/cold-reload.script').read_text()+video('cold')+'quit\n')
    require(saved_fields(out/'cold-reload/cold.bin')==expected,'Cold identity/progression changed')
    require(sha(out/'cold-reload/reloaded.sav')==sha(saved),'Cold SRAM roundtrip differs')
    loaded_code(out/'cold-reload','cold',meta);current_build(rom,observer)
    require((runner,helper,abi)==(sha(Path(__file__)),sha(HERE/'run_summary_guide.py'),sha(HERE/'save-observer-abi.json')),'Source changed during run')
    result={'passed':True,'kind':kind,'language':meta['language'],'execution':execution,'cold_execution':cold,
        'runner_sha256':runner,'helper_sha256':helper,'save_abi_sha256':abi,'build_manifest_sha256':sha(rom.parent/'build.json'),
        'observer_manifest_sha256':sha(observer.parent/'observer.json'),'baseline_ram_sha256':sha(baseline/'before.bin'),
        'fields_sha256':{k:hashlib.sha256(v).hexdigest() for k,v in expected.items()},
        'normal_save_sha256':sha(saved),'cold_sram_roundtrip':True,'markers':markers,
        'excluded_normal_save_fields':'IGT; array CRC/padding; PC bookkeeping. Entire party, profile/options/coins, bag, vars/flags, Pokedex and every PC Pokemon compared.',
        'config':'Core906e9ebb interpreter/software1x/fixed RTC/FreeBIOS/no cheats; existing normal save only.'}
    (out/'verification.json').write_text(json.dumps(result,indent=2)+'\n');return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ['rom','fixture','observer','out','baseline']:p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--kind',choices=['party','box'],required=True);a=p.parse_args()
    print(json.dumps(probe(a.rom,a.fixture,a.observer,a.out,a.kind,a.baseline)))
