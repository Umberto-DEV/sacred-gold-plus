#!/usr/bin/env python3
"""Inspect every captured entry/exit frame and Oak's original native fade."""
import argparse
import json
from pathlib import Path
import struct
from PIL import Image, ImageChops
from run_newgame_guide import PREFIX, capture, current_build, loaded_code, run_new, sha, require


def lower(path):
    return Image.open(path).convert('RGB').crop((0,192,256,384))


def classification(frame, panel):
    if ImageChops.difference(frame,panel).getbbox() is None:
        return 'complete-panel'
    if all(low == high for low,high in frame.getextrema()):
        return 'uniform-hidden'
    raise ValueError('Partial or stale screen during guide transfer')


def verify_existing(root):
    records={}
    for lang in ['en','it']:
        for mode in ['skip','full']:
            out=root/f'newgame-{mode}-{lang}-test'
            require(json.loads((out/'verification.json').read_text())['passed'],'Unverified transition source')
            panel1=lower(out/'panel1.ppm')
            final=lower(out/('panel3.ppm' if mode=='full' else 'panel1.ppm'))
            entry=[classification(lower(out/f'entry-{i}.ppm'),panel1) for i in range(12)]
            leave=[classification(lower(out/f'return-{i}.ppm'),final) for i in range(20)]
            records[f'{mode}-{lang}']={'entry':entry,'return':leave,'runtime_sha256':sha(out/'verification.json')}
    result={'passed':True,'runner_sha256':sha(Path(__file__)),'cases':records,'frames':128}
    (root/'newgame-transitions.json').write_text(json.dumps(result,indent=2)+'\n')
    return result


def fade(rom, observer, out):
    meta=current_build(rom,observer)
    commands=PREFIX+'run 180\nrun 40 B\n'+capture('held')+'release\n'
    for i in range(80):
        commands+=f'run 1 NONE\ncapture fade-{i}.ppm\ndumpitcm fade-{i}.itcm\ndumpbus fade-{i}.regs 0x04001000 0x70\n'
    commands+='run 160\n'+capture('native')+'quit\n'
    result={'execution':run_new(rom,observer,out,commands)}
    values=[]
    for i in range(80):
        marker=loaded_code(out,f'fade-{i}',meta)
        require(marker[0]==0x4F414B31 and marker[1:3]==(0,0) and marker[8:11]==(1,1,0) and marker[14]==0,'Owner/lease changed during original fade')
        regs=(out/f'fade-{i}.regs').read_bytes()
        values.append(struct.unpack_from('<H',regs,0x6c)[0])
    require(0x8010 in values and (0 in values or 0x8000 in values),'Original black-to-visible fade not observed')
    require(any(value not in [0,0x8000,0x8010] for value in values),'Native fade had no intermediate brightness')
    current_build(rom,observer)
    result.update({'passed':True,'language':meta['language'],'runner_sha256':sha(Path(__file__)),
                   'brightness_by_frame':values,'frames':80,'lease_absent_every_frame':True})
    (out/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path)
    for name in ['rom','observer','out']:
        p.add_argument('--'+name,type=Path)
    a=p.parse_args()
    r=verify_existing(a.root) if a.root else fade(a.rom,a.observer,a.out)
    print(json.dumps({'passed':r['passed'],'frames':r['frames']}))
