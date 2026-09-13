#!/usr/bin/env python3
"""Cold-boot bounded lease gate: no guide UI, cheats, RAM writes, normal SAVE or state reuse."""
import argparse
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[0]
sys.path.insert(0,str(ROOT/'native-eviv'))
from run_probe import run, sha, same_region, inspect
from run_box_probe import open_summary, read_data, FIXTURE_SHA as BOX_SHA
from run_probe import FIXTURE_SHA as PARTY_SHA
from lease_oracle import markers, state, require


def current_build(path, rom):
    """Reject stale source/object/ROM combinations before running any gameplay."""
    from thumb_object import load_text
    from ndspy.rom import NintendoDSRom
    meta=json.loads(path.read_text())
    require(meta['kind']=='private-native-guide-lease-gate-not-guide-ui','Wrong lease build kind')
    for name,expected in meta['source_sha256'].items():
        require(Path(name).name==name,'Invalid build source filename')
        require(sha(HERE/name)==expected,'Stale build source: '+name)
    require(sha(rom)==meta['rom_sha256'],'Stale build ROM')
    obj=path.parent/'lease.o'
    require(sha(obj)==meta['object_sha256'],'Stale compiled object')
    payload,symbols=load_text(obj.read_bytes(),meta['memory']['code_start'])
    import hashlib
    require(hashlib.sha256(payload).hexdigest()==meta['payload_sha256'],'Stale compiled payload')
    require(symbols==meta['symbols'],'Compiled symbols differ')
    itcm=NintendoDSRom(rom.read_bytes()).loadArm9().sections[1]
    offset=meta['memory']['code_start']-itcm.ramAddress
    require(itcm.data[offset:offset+len(payload)]==payload,'ROM does not contain compiled payload')
    require(itcm.data[0x1f00:0x2000]==bytes(256),'Markers not zero-initialized by autoload')
    return {'build_sha256':sha(path),'source_sha256':meta['source_sha256'],
            'payload_sha256':meta['payload_sha256'],'object_sha256':meta['object_sha256']}


def snapshot(name):
    return f'capture {name}.ppm\ndump {name}.bin\ndumpitcm {name}.itcm\n'


def script(kind):
    if kind == 'box':
        text = open_summary()
    else:
        text = (ROOT/'runtime/inputs/cold-reload.script').read_text()
        text += ('touch 40 75 2\nrun 240\ntouch 64 30 2\nrun 120\n'
                 'touch 184 40 2\nrun 360\ntap RIGHT 2 300\n')
    text += snapshot('before')
    # One new press, held for 120 frames: must execute just one cycle.
    text += 'run 120 START\nrun 2 NONE\n' + snapshot('cycle-1')
    for i in range(2,11):
        text += 'tap START 2 30\n' + snapshot(f'cycle-{i}')
    text += 'tap L 2 120\n' + snapshot('ev')
    text += 'tap R 2 120\n' + snapshot('iv')
    text += 'tap SELECT 2 120\n' + snapshot('restored')
    text += 'tap RIGHT 2 120\ntap LEFT 2 120\n' + snapshot('page-return')
    text += 'tap A+START 2 120\n' + snapshot('a-open')
    text += 'tap B 2 120\n' + snapshot('a-return')
    text += 'tap B+START 2 180\n' + snapshot('outside')
    return text + 'sram unchanged.sav\nquit\n'


def probe(rom, fixture, observer, out, kind, expected_rom_sha, red=False):
    require(sha(rom)==expected_rom_sha,'Wrong complete ROM hash')
    require(sha(fixture)==(BOX_SHA if kind=='box' else PARTY_SHA),'Wrong fixture hash')
    meta=json.loads((observer.parent/'observer.json').read_text())
    require(sha(observer)==meta['binary_sha256'],'Observer hash mismatch')
    provenance=None if red else current_build(rom.parent/'build.json',rom)
    execution=run(observer,rom,fixture,out,script(kind))
    result={'execution':execution, 'kind':kind, 'expected_red':red, 'build_provenance':provenance,
            'runner_sha256':sha(Path(__file__)), 'oracle_sha256':sha(HERE/'lease_oracle.py'),
            'observer_manifest_sha256':sha(observer.parent/'observer.json')}
    import hashlib
    before_itcm=(out/'before.itcm').read_bytes()
    require(hashlib.sha256(before_itcm[0x620:0x870]).hexdigest()=='6865177a8e819d603bbcfd3bce5c324566780dd01aa4d6793d052a17b57bc1c0','Observer does not see intact r5 code')
    result['runtime_r5_payload_verified']=True
    if not red:
        build_meta=json.loads((rom.parent/'build.json').read_text())
        start=build_meta['memory']['code_start']&0x7fff
        size=build_meta['payload_bytes']
        for name in ['before','cycle-10','outside']:
            code=(out/(name+'.itcm')).read_bytes()[start:start+size]
            require(hashlib.sha256(code).hexdigest()==build_meta['payload_sha256'],'Executed code differs from compiled probe')
        result['runtime_probe_payload_verified']=True
    try:
        results=[markers((out/f'cycle-{i}.itcm').read_bytes(),i) for i in range(1,11)]
    except ValueError as exc:
        result['failure']=str(exc)
        (out/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
        raise
    require(not red,'Unchanged r5 unexpectedly executes lease probe')
    initial=state((out/'before.bin').read_bytes())
    for i in range(1,11):
        require(state((out/f'cycle-{i}.bin').read_bytes()) == initial,f'Cycle {i} changed heap/Summary resources')
        require(results[i-1]['heap']==initial['heap'] and results[i-1]['summary']==initial['summary'], 'Dynamic pointer differs')
    names=['before']+[f'cycle-{i}' for i in range(1,11)]+['ev','iv','restored','page-return','a-open','a-return','outside']
    data=[read_data(out/(n+'.bin')) if kind=='box' else inspect((out/(n+'.bin')).read_bytes())['raw'] for n in names]
    require(all(x==data[0] for x in data),'Pokemon/party/box bytes changed')
    require(sha(out/'unchanged.sav')==sha(fixture),'SRAM changed')
    regions=[(4,22,143,38),(4,48,143,135),(152,6,248,20),(0,192,256,384)]
    for name in ['cycle-10','restored','page-return','a-return']:
        require(all(same_region(out,'before',name,r) for r in regions),'Stable screen regions changed: '+name)
    require(not same_region(out,'before','a-open',(0,192,256,384)),'A failed to open original move details')
    require(markers((out/'outside.itcm').read_bytes(),10)==results[-1],'A/B priority unexpectedly ran a lease')
    # Real EV/IV remains effective, not merely unchanged normal rendering.
    for name in ['ev','iv']:
        require(not same_region(out,'before',name,(4,48,143,135)), 'Original EV/IV input stopped working')
    import struct
    outside=(out/'outside.bin').read_bytes()
    require(struct.unpack_from('<I',outside,0x1d110c)[0]!=0x020885DD,'B failed to leave Summary')
    result.update({'cycles':results,'heap_before':initial,'heap_restored_each_cycle':True,
        'pokemon_party_box_preserved':True,'sram_preserved':True,'stable_regions_preserved':True,
        'original_eviv_works':True,'directions_and_exit_work':True,'a_b_priority_over_start_works':True,
        'config':'Core906e9ebb, interpreter, software1x, fixed RTC, FreeBIOS, no cheats',
        'limits':['No guide UI, SAVE/cold-reload regression, GUI, Android, handheld or performance claim.']})
    (out/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ['rom','fixture','observer','out']: p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--kind',choices=['party','box'],required=True)
    p.add_argument('--rom-sha',required=True)
    p.add_argument('--red',action='store_true')
    a=p.parse_args()
    print(json.dumps(probe(a.rom,a.fixture,a.observer,a.out,a.kind,a.rom_sha,a.red)))
