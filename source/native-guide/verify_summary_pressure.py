#!/usr/bin/env python3
"""Exercise actual UI allocation NULL using a separately compiled native pressure probe."""
import json
from pathlib import Path
from run_summary_guide import current_build, enter, video, run, loaded_code, sha, require, same_region
from lease_oracle import state
from verify_summary_guide import check_data, UPPER


def probe(rom,fixture,observer,out,kind,baseline):
    meta=current_build(rom,observer)
    require(meta['pressure_test_instrumentation'],'Normal ROM is not a pressure probe')
    source_sha=sha(Path(__file__))
    script=enter(kind)+video('before')+'run 60 START\n'+video('failure')+'run 30 NONE\n'+video('return')
    script+='tap L 2 30\n'+video('ev')+'tap R 2 30\n'+video('iv')+'tap SELECT 2 30\n'+video('stats')
    script+='tap B 2 180\n'+video('outside')+'sram unchanged.sav\nquit\n'
    execution=run(observer,rom,fixture,out,script)
    current_build(rom,observer);require(sha(Path(__file__))==source_sha,'Pressure runner changed during execution')
    result={'execution':execution,'kind':kind,'language':meta['language'],'build_sha256':sha(rom.parent/'build.json'),
            'source_sha256':meta['source_sha256'],'runner_sha256':source_sha,
            'instrumentation':'Compile-time-only native22528byte pressure lease, then the real UI lease request, canaries and matching native free.'}
    try:
        markers={n:loaded_code(out,n,meta) for n in ['before','failure','return','ev','iv','stats','outside']}
        failed=markers['failure']
        require(failed[1]==0 and failed[2]==0 and failed[4]==7 and failed[8]==1 and failed[10]==1,'UI did not handle its real allocation failure')
        require(failed[14]==0 and failed[15]==0x01010101,'Native pressure/NULL/canary/free counts differ')
        require(state((out/'failure.bin').read_bytes())==state((baseline/'before.bin').read_bytes()),'Pressure left heap/resources changed')
        require(state((out/'before.bin').read_bytes())==state((out/'return.bin').read_bytes()),'Badge not safely restored after NULL')
        for n in ['return','stats']:require(all(same_region(out,'before',n,r) for r in UPPER),'Original stats changed after failure')
        for n in ['ev','iv']:require(not same_region(out,'before',n,UPPER[1]),'Original EV/IV controls unusable after failure')
        require(markers['outside'][1:4]==(0,0,0) and markers['outside'][9]==markers['outside'][13],'NULL cleanup/exit left ownership')
        check_data(out,list(markers),kind);require(sha(out/'unchanged.sav')==sha(fixture),'Pressure changed SRAM')
        result.update({'passed':True,'markers':markers,'pressure_allocations':1,'real_ui_nulls':1,'pressure_frees':1,'guard_checks':1,
                       'exact_heap_resources_restored':True,'normal_input_display_preserved':True,'sram_pokemon_party_box_unchanged':True})
    except Exception as exc:
        result.update({'passed':False,'failure':str(exc)});(out/'verification.json').write_text(json.dumps(result,indent=2)+'\n');raise
    (out/'verification.json').write_text(json.dumps(result,indent=2)+'\n');return result


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser(description=__doc__)
    for n in ['rom','fixture','observer','out','baseline']:p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--kind',choices=['party','box'],required=True);a=p.parse_args()
    print(json.dumps(probe(a.rom,a.fixture,a.observer,a.out,a.kind,a.baseline)))
