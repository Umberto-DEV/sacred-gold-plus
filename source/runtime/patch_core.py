#!/usr/bin/env python3
"""Add observation-only ARM9 instruction counters to the pinned melonDS source."""
import argparse
import pathlib
import subprocess

parser=argparse.ArgumentParser()
parser.add_argument('--source',type=pathlib.Path,required=True,help='Separate melonDS checkout at the pinned revision')
args=parser.parse_args()
revision=subprocess.check_output(['git','-C',str(args.source),'rev-parse','HEAD'],text=True).strip()
expected='906e9ebb27da8c6a715cd7abab4abfe8a8d29427'
if revision!=expected:raise SystemExit(f'Expected source {expected}, got {revision}')
def patch_mainloop():
    p=args.source/'src/NDS.cpp'
    s=p.read_text()
    if 'HGTrace::MainLoopJumps' in s:
        print('Main-loop jump hook already present')
        return
    old='#include "ARMJIT_Memory.h"'
    assert s.count(old)==1
    s=s.replace(old,old+'\n#ifdef HG_RUNTIME_TRACE\n#include "hg_trace.h"\n#endif')
    old='void NDS::MonitorARM9Jump(u32 addr)\n{'
    assert s.count(old)==1
    s=s.replace(old,old+'\n#ifdef HG_RUNTIME_TRACE\n    if (HGTrace::Enabled && (addr & ~1u) == 0x02000DAC) ++HGTrace::MainLoopJumps;\n#endif')
    p.write_text(s)
    print('Patched NDS branch-target observation at 02000DAC')
patch_mainloop()
p=args.source/'src/ARM.cpp'
s=p.read_text()
if 'HG_RUNTIME_TRACE' in s:
    print('Trace hooks already present')
    raise SystemExit(0)
old='#include "ARMJIT_Memory.h"'
assert s.count(old)==1
s=s.replace(old,old+'\n#ifdef HG_RUNTIME_TRACE\n#include "hg_trace.h"\n#endif')
old='''                // actually execute
                if (CheckCondition(CurInstr >> 28))'''
new='''                // actually execute
#ifdef HG_RUNTIME_TRACE
                const u32 hgAddress = R[15] - 8;
                const bool hgTrace = HGTrace::Enabled &&
                    (hgAddress == 0x020D3FA8 || hgAddress == 0x020DE16C);
                const u32 hgR10Before = hgTrace ? R[10] : 0;
                const bool hgCondition = hgTrace && CheckCondition(CurInstr >> 28);
#endif
                if (CheckCondition(CurInstr >> 28))'''
assert s.count(old)==2
s=s.replace(old,new,1)
old='''                else
                    AddCycles_C();
            }

            // TODO optimize this shit!!!'''
new='''                else
                    AddCycles_C();
#ifdef HG_RUNTIME_TRACE
                if (hgTrace)
                    HGTrace::Record(hgAddress, hgCondition, hgR10Before, R[10], CurInstr);
#endif
            }

            // TODO optimize this shit!!!'''
assert s.count(old)==2
s=s.replace(old,new,1)
p.write_text(s)
print('Patched ARM9 interpreter with two observation-only PC hooks')
