#!/usr/bin/env python3
"""Bounded real-core acceptance; screenshots/raw game data stay in private output."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
from run_summary_guide import HERE, ROOT, enter, video, run, sha, require, current_build, loaded_code, same_region, return_graphics
from lease_oracle import state
from run_probe import inspect, FIXTURE_SHA as PARTY_SHA
from run_box_probe import read_data, FIXTURE_SHA as BOX_SHA

UPPER=[(4,22,143,38),(4,48,143,135),(152,6,248,20)]


def scenario(kind):
    names=[]
    def snap(name):
        names.append(name);return video(name)
    s=enter(kind)+snap('before')
    # Ten complete modal cycles. First covers all panels and both held entry/A.
    s+='run 120 START\n'+snap('panel1')+'run 4 NONE\nrun 120 A\n'+snap('panel2')
    s+='run 4 NONE\ntap LEFT 2 20\n'+snap('back1')
    s+='touch 16 160 2\nrun 20\n'+snap('disabled-back')
    s+='touch 128 168 2\nrun 20\n'+snap('touch-next')+'tap RIGHT 2 20\n'+snap('panel3')
    s+='touch 159 175\nrun 40\n'+snap('clean-1')+'release\nrun 30\n'+snap('cycle-1')
    for i in range(2,11):
        if i in [2,3]:s+=('tap L 2 30\n' if i==2 else 'tap R 2 30\n')+snap('ev' if i==2 else 'iv')
        if i==4:s+='tap SELECT 2 30\n'
        s+='tap START 2 20\n'+snap(f'open-{i}')+'run 20 B\n'+snap(f'clean-{i}')+'run 30 NONE\n'+snap(f'cycle-{i}')
    # Exact drawn entry bounds: four just-outside edges leave it closed.
    for x,y in [(167,150),(248,150),(200,143),(200,160)]:s+=f'touch {x} {y} 2\nrun 20\n'
    s+=snap('badge-edges')
    # Entry by minimum inside corner, held touch cannot advance.
    s+='touch 168 144\nrun 60\n'+snap('held-touch-entry')+'release\nrun 4\n'
    # Four edges of Next are inactive; minimum included point activates once.
    for x,y in [(95,168),(160,168),(128,159),(128,176)]:s+=f'touch {x} {y} 2\nrun 20\n'
    s+=snap('next-edges')+'touch 96 160\nrun 60\n'+snap('held-touch-next')+'release\nrun 4\n'
    # Left wins over A/Right; B wins over Left/A/Right.
    s+='tap LEFT+RIGHT+A 2 20\n'+snap('left-priority')+'tap A 2 20\n'
    s+='run 30 B+LEFT+RIGHT+A\n'+snap('b-priority')+'run 30 NONE\n'
    # Real START=X mapping, prepared synthetically in gSystem only.
    s+='write 0x021d1140 1 4\ntap START 2 20\n'+snap('start-equals-x')
    s+='tap B 2 30\nwrite 0x021d1140 0 4\nrun 4\n'
    # Real L=A variant, synthetic preparation explicitly separate from options UI.
    s+='write 0x021d1140 3 4\ntap START 2 20\ntap A 2 20\ntap A 2 20\n'+snap('l-equals-a')
    s+='tap B 2 30\nwrite 0x021d1140 0 4\nrun 4\n'
    # Touch Close right/bottom inclusive pixels; touch entry maximum inside corner.
    s+='touch 247 159 2\nrun 20\n'+snap('touch-max-entry')
    s+='touch 239 175\nrun 30\n'+snap('held-close')+'release\nrun 30\n'
    # Original r5 controls and page/move-detail priority after all guide cleanup.
    s+='tap L 2 30\n'+snap('post-ev')+'tap R 2 30\n'+snap('post-iv')+'tap SELECT 2 30\n'+snap('post-stats')
    s+='tap RIGHT 2 60\n'+snap('other-page')+'tap START 2 20\n'+snap('other-page-start')
    s+='tap LEFT 2 60\ntap A+START 2 60\n'+snap('move-detail')+'tap START 2 20\n'+snap('move-start')
    s+='tap B 2 60\n'+snap('move-return')
    if kind=='box':s+='tap UP 2 40\ntap DOWN 2 40\n'+snap('box-members')
    s+='tap B+START 2 180\n'+snap('outside')
    if kind=='party':s+='touch 64 30 2\nrun 120\ntouch 184 40 2\nrun 360\ntap RIGHT 2 120\n'
    else:s+='tap A 2 360\ntap RIGHT 2 120\n'
    s+=snap('reentered')+'tap B 2 180\n'+snap('final-outside')+'sram unchanged.sav\nquit\n'
    return s,names


def digest(data):return hashlib.sha256(data).hexdigest()


def check_data(out,names,kind):
    values=[read_data(out/(n+'.bin')) if kind=='box' else inspect((out/(n+'.bin')).read_bytes())['raw'] for n in names]
    require(all(v==values[0] for v in values),'Fixture Pokemon/party/storage changed')
    return digest(repr(values[0]).encode())


def probe(rom,fixture,observer,out,kind,baseline):
    meta=current_build(rom,observer)
    require(not meta['pressure_test_instrumentation'],'Instrumented ROM in normal acceptance')
    require(sha(fixture)==(BOX_SHA if kind=='box' else PARTY_SHA),'Wrong fixture')
    script,names=scenario(kind)
    runner_sha=sha(Path(__file__));helper_sha=sha(HERE/'run_summary_guide.py')
    execution=run(observer,rom,fixture,out,script)
    require(sha(Path(__file__))==runner_sha and sha(HERE/'run_summary_guide.py')==helper_sha,'Runtime source changed during execution')
    current_build(rom,observer)
    result={'execution':execution,'kind':kind,'language':meta['language'],'build_sha256':sha(rom.parent/'build.json'),
            'source_sha256':meta['source_sha256'],'observer_manifest_sha256':sha(observer.parent/'observer.json'),
            'runner_sha256':runner_sha,'input_helper_sha256':helper_sha}
    try:
        markers={n:loaded_code(out,n,meta) for n in names}
        require(all(m[0]==0x47554931 and not m[14] for m in markers.values()),'Guide ownership canary/error')
        for n,panel in [('panel1',0),('panel2',1),('back1',0),('disabled-back',0),('touch-next',1),('panel3',2),('held-touch-entry',0),('next-edges',0),('held-touch-next',1),('left-priority',0),('start-equals-x',0),('l-equals-a',2),('touch-max-entry',0)]:
            require(markers[n][4]==4 and markers[n][5]==panel,f'Wrong modal panel/input: {n}')
        for n in ['b-priority','held-close']:
            require(markers[n][4]==7 and markers[n][1]==0,f'Exit release latch failed: {n}')
        original=state((baseline/'before.bin').read_bytes())
        initial=state((out/'before.bin').read_bytes())
        before_ram=(out/'before.bin').read_bytes()
        badge_context=markers['before'][1]-0x02000000
        expected_vram=bytearray((out/'before.vram').read_bytes())
        expected_vram[960*32:980*32]=before_ram[badge_context+688:badge_context+688+640]
        expected_map=bytearray((out/'before.map').read_bytes())
        for i in range(20):
            offset=2*((18+i//10)*32+21+i%10)
            expected_map[offset:offset+2]=before_ram[badge_context+1328+2*i:badge_context+1330+2*i]
        for i in range(1,11):
            clean=f'clean-{i}';m=markers[clean]
            require(m[1]==0 and m[2]==0 and m[4]==7 and m[8]==i and m[9]==m[13],f'Live resource or wrong count after cycle{i}')
            require(state((out/(clean+'.bin')).read_bytes())==original,f'Exact original heap/resources not restored at cycle{i}')
            require(state((out/f'cycle-{i}.bin').read_bytes())==initial,f'Badge heap/resources drift at cycle{i}')
            require((out/(clean+'.vram')).read_bytes()==expected_vram,'Original GPU characters not restored')
            require((out/(clean+'.map')).read_bytes()==expected_map,'Original GPU map not restored')
            require((out/(clean+'.regs')).read_bytes()[:4]==(out/'before.regs').read_bytes()[:4],'Visibility not restored')
            return_graphics(out,'before',clean)
            if i>1:require(markers[f'open-{i}'][4:6]==(4,0),'Reopen did not start at panel1')
        for a,b in [('before','cycle-1'),('ev','cycle-2'),('iv','cycle-3'),('before','post-stats')]:
            require(all(same_region(out,a,b,r) for r in UPPER),f'Prior Stats/EV/IV display changed: {a} -> {b}')
        for n in ['post-ev','post-iv']:require(not same_region(out,'before',n,UPPER[1]),'r5 control stopped working')
        require(markers['badge-edges'][8]==10 and markers['badge-edges'][4]==0,'Outside entry edge opened guide')
        for n in ['other-page','other-page-start','move-detail','move-start']:
            require(markers[n][1]==0 and markers[n][4]==0 and markers[n][11]==0,f'Badge present in forbidden mode: {n}')
        require(markers['other-page-start'][8]==markers['other-page'][8],'Other page captured START')
        require(markers['move-start'][8]==markers['move-detail'][8],'Move detail captured START')
        require(markers['move-return'][11]==1 and markers['reentered'][11]==1,'Badge did not return after host transition')
        for n in ['outside','final-outside']:
            require(markers[n][1]==0 and markers[n][2]==0 and markers[n][3]==0 and markers[n][9]==markers[n][13],'Pointer/allocation survived Summary Exit')
            require(struct.unpack_from('<I',(out/(n+'.bin')).read_bytes(),0x1d110c)[0]!=0x020885DD,'Original Summary exit failed')
        data_sha=check_data(out,names,kind)
        require(sha(out/'unchanged.sav')==sha(fixture),'SRAM changed')
        # CPU map and GPU map agree once scheduled transfers have settled.
        for n in names:
            ram=(out/(n+'.bin')).read_bytes()
            if struct.unpack_from('<I',ram,0x1d110c)[0]!=0x020885DD:continue
            summary=struct.unpack_from('<I',ram,0x1d1110)[0]-0x2000000
            bg=struct.unpack_from('<I',ram,summary)[0]-0x2000000
            tilemap=struct.unpack_from('<I',ram,bg+0xb8)[0]-0x2000000
            require(ram[tilemap:tilemap+2048]==(out/(n+'.map')).read_bytes(),'CPU/GPU map mismatch: '+n)
        result.update({'passed':True,'cycles':10,'markers':markers,'wrapper_allocation_counter':original['counter'],
            'exact_heap_and_resources_restored_each_cycle':True,'pokemon_party_storage_sha256':data_sha,'sram_unchanged':True,
            'native_font_panels':3,'button_mode_tests':'Synthetic gSystem.buttonMode1 and3, restored0; no options UI claim',
            'config':'Core906e9ebb interpreter/software1x/fixed RTC/FreeBIOS/no cheats',
            'limits':['Private existing party1/box1 fixtures; no GUI/Android/handheld/FPS/NewGame claim.']})
    except Exception as exc:
        result.update({'passed':False,'failure':str(exc)})
        (out/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
        raise
    (out/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ['rom','fixture','observer','out','baseline']:p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--kind',choices=['party','box'],required=True);a=p.parse_args()
    print(json.dumps(probe(a.rom,a.fixture,a.observer,a.out,a.kind,a.baseline)))
