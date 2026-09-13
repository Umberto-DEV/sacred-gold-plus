#!/usr/bin/env python3
"""Check original CPU Window bitmaps and shared font state in bound runtime dumps."""
import argparse
import json
from pathlib import Path
import struct
from run_summary_guide import sha, require


def snapshot(path):
    ram=path.read_bytes()
    def view(addr,n):
        require(0x02000000<=addr<=0x02400000-n,'Pointer outside observed RAM')
        return ram[addr-0x02000000:addr-0x02000000+n]
    def word(addr):return struct.unpack('<I',view(addr,4))[0]
    s=word(0x021D1110);require(word(0x021D110C)==0x020885DD,'Not Summary')
    records=view(s+4,34*16)+view(word(s+0x224),word(s+0x228)*16)
    windows=[]
    for i in range(0,len(records),16):
        w=records[i:i+16];ptr=struct.unpack_from('<I',w,12)[0]
        if ptr:windows.append(view(ptr,w[7]*w[8]*32))
    f=word(0x0211188C)
    return {'windows':windows,'font_work':view(f,188),'colors':view(0x021D1F6E,6),'lookup':view(0x021D1F94,512)}


def verify(root):
    results={}
    for kind in ['party','box']:
        for lang in ['en','it']:
            out=root/f'final-{kind}-{lang}-r7'
            require(json.loads((out/'verification.json').read_text())['passed'],'Unverified dump source')
            comparisons=[]
            for i in range(1,11):
                before='ev' if i==2 else 'iv' if i==3 else 'before'
                after=f'clean-{i}'
                a,b=snapshot(out/(before+'.bin')),snapshot(out/(after+'.bin'))
                # Native r5 redraws leave their own last-glyph scratch. Check
                # its full restoration for matching pre-entry EV/IV captures.
                require(a['windows']==b['windows'],'CPU Window changed: '+str(out)+' '+after)
                if i>=4:
                    # SELECT performs a native r5 redraw with a different last
                    # glyph. Its glyph scratch is not the initial game's glyph.
                    a=snapshot(out/(f'open-{i}'+'.bin'))
                require(a==b,'Shared font changed: '+str(out)+' '+after)
                comparisons.append({'before':before,'after':after,'windows':len(a['windows'])})
            for n in ['panel1','panel2','panel3']:
                require(snapshot(out/(n+'.bin'))==snapshot(out/'before.bin'),'Modal modified original Window/font: '+n)
            results[f'{kind}-{lang}']={'passed':True,'comparisons':comparisons,'modal_panels':3,
                'runtime_verification_sha256':sha(out/'verification.json')}
    report={'passed':True,'runner_sha256':sha(Path(__file__)),'results':results}
    (root/'buffers-verification.json').write_text(json.dumps(report,indent=2)+'\n')
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path)
    print(json.dumps(verify(p.parse_args().root)))
