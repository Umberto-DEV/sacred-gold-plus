#!/usr/bin/env python3
"""Reject any partially recomposed return frame in the final bound captures."""
import argparse
import json
from pathlib import Path
from PIL import Image
from run_summary_guide import require, return_graphics, sha


def verify(root):
    results={}
    for kind in ['party','box']:
        for lang in ['en','it']:
            out=root/f'save-{kind}-{lang}-r6'
            require(json.loads((out/'verification.json').read_text())['passed'],'Unverified runtime dump')
            modal=Image.open(out/'touch-priority.ppm').crop((0,192,256,384)).tobytes()
            frames=[]
            for i in range(1,17):
                name=f'return-{i}';im=Image.open(out/(name+'.ppm')).crop((0,192,256,384))
                if im.tobytes()==modal:state='complete modal'
                elif len(im.getcolors(49152) or [])==1:state='hidden backdrop'
                else:
                    return_graphics(out,'before',name)
                    state='native with original OAM'
                frames.append(state)
            require('native with original OAM' in frames,'Never returned')
            results[f'{kind}-{lang}']={'passed':True,'frames':frames,'runtime_verification_sha256':sha(out/'verification.json')}
    result={'passed':True,'runner_sha256':sha(Path(__file__)),'results':results}
    (root/'transitions-verification.json').write_text(json.dumps(result,indent=2)+'\n');return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path)
    print(json.dumps(verify(p.parse_args().root)))
