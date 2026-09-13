#!/usr/bin/env python3
"""Check a genuine NULL from the native UI lease under bounded owned pressure."""
import argparse
import hashlib
import json
from pathlib import Path
from build_newgame_pressure import instrument_source
from run_newgame_guide import PREFIX, capture, current_build, loaded_code, run_new, sha, require
from newgame_oracle import heap, oak


def probe(rom, observer, out, baseline):
    meta=current_build(rom,observer)
    require(meta['pressure_test_instrumentation'] and meta['normal_summary_dispatch_preserved'], 'Not the separate Oak pressure instrument')
    source=rom.parent/'pressure.c'
    require(sha(source)==meta['prepared_source_sha256'] and source.read_text()==instrument_source(), 'Stale pressure source')
    commands=PREFIX+'run 180 B\n'+capture('failure-held')+'release\nrun 4 NONE\nrun 240\n'+capture('continuation')+'sram blank.sav\nquit\n'
    execution=run_new(rom,observer,out,commands)
    held=loaded_code(out,'failure-held',meta)
    require(held[0]==0x4F414B31 and held[1:3]==(0,0) and held[4]==7, 'No clean NULL release latch')
    require(held[8:11]==(1,0,1) and held[11]==0x01010101 and held[13:15]==(0,0), 'Native pressure allocation/NULL/canary/free result differs')
    require(heap(out/'failure-held.bin')==heap(baseline), 'Native pressure changed heap80 topology/counter')
    require(oak(out/'failure-held.bin')==oak(baseline), 'Native NULL changed Oak graphics/font/callback')
    for suffix in ['vram','pal']:
        require((out/f'failure-held.{suffix}').read_bytes()==(baseline.parent/f'{baseline.stem}-{suffix}.bin').read_bytes(), 'NULL changed video buffers')
    require((out/'blank.sav').read_bytes()==bytes([255])*524288,'NULL test wrote SRAM')
    continued=loaded_code(out,'continuation',meta)
    require(continued[4]==0 and continued[8]==1 and continued[1:3]==(0,0), 'Oak did not resume after NULL')
    current_build(rom,observer)
    result={'passed':True,'execution':execution,'language':meta['language'],'runner_sha256':sha(Path(__file__)),
        'build_sha256':sha(rom.parent/'build.json'),'prepared_source_sha256':sha(source),'markers':held,
        'pressure_allocation_bytes':174000,'actual_ui_request_bytes':22528,
        'actual_ui_result':None,'pressure_allocations':1,'canary_checks':1,'pressure_frees':1,
        'exact_heap_font_video_restore':True,'original_oak_continued':True,
        'instrument_only':'Summary retains r5 dispatch; this ROM is not counted as normal guide acceptance.'}
    (out/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['rom','observer','out','baseline']:
        p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();r=probe(a.rom,a.observer,a.out,a.baseline)
    print(json.dumps({k:r[k] for k in ['passed','language','actual_ui_result']}))
