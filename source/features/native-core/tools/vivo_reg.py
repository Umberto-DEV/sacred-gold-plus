#!/usr/bin/env python3
"""Vivezza di UN registro dopo un indirizzo, con esplorazione dei rami (BFS)."""
import sys
from pathlib import Path
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB
from capstone.arm import ARM_CC_AL, ARM_CC_INVALID
R = Path(__file__).resolve().parents[4]   # radice del repo
W = R / 'the private development workspace'
sys.path.insert(0, str(W / 'SGP-1.2-PLUS-02/tools'))
sys.path.insert(0, str(W / 'SGP-1.2-PRESTAZIONI-NPC-03/tools'))
from arm9 import Arm9
import overlay_patch as OP
ROMS = R / '$SGP_ROM_DIR'
MD = Cs(CS_ARCH_ARM, CS_MODE_THUMB); MD.detail = True

def lettore(nome, rom):
    if nome == 'arm9':
        a = Arm9(ROMS / rom); return lambda x, n: a.leggi(x, n)
    oid = int(nome[2:]); r = OP.Rom((ROMS / rom).read_bytes())
    v, _, img = r.immagine_overlay(oid)
    return lambda x, n: img[x - v['ram']: x - v['ram'] + n]

def vivo(leggi, start, reg, limite=400):
    visti, coda, esito = set(), [start], []
    while coda:
        pc = coda.pop(0)
        if pc in visti: continue
        n = 0
        while n < 60:
            if pc in visti: break
            visti.add(pc)
            try: b = leggi(pc, 4)
            except Exception: break
            ins = next(MD.disasm(b, pc), None)
            if ins is None: break
            letti, scrit = ins.regs_access()
            nl = [ins.reg_name(x) for x in letti]; ns = [ins.reg_name(x) for x in scrit]
            if ins.mnemonic.startswith('bl'):      # chiamata: reg 0-3 = argomenti possibili
                esito.append(('CHIAMATA (r0-r3 potenziali argomenti)', '0x%08X %s %s' % (pc, ins.mnemonic, ins.op_str)))
                # dopo una BL r0-r3 sono comunque clobberati dal callee
                break
            if reg in nl:
                esito.append(('LETTO', '0x%08X %s %s' % (pc, ins.mnemonic, ins.op_str))); break
            if reg in ns:
                esito.append(('SCRITTO (morto)', '0x%08X %s %s' % (pc, ins.mnemonic, ins.op_str))); break
            if ins.mnemonic == 'pop' and 'pc' in ns:
                esito.append(('RITORNO (morto)', '0x%08X %s %s' % (pc, ins.mnemonic, ins.op_str))); break
            if ins.mnemonic in ('bx',):
                esito.append(('BX (morto)', '0x%08X %s %s' % (pc, ins.mnemonic, ins.op_str))); break
            if ins.mnemonic == 'b':
                try: t = int(ins.op_str.lstrip('#'), 0)
                except ValueError: break
                if ins.cc not in (ARM_CC_AL, ARM_CC_INVALID): coda.append(t)
                else: pc = t; n += 1; continue
            pc += ins.size; n += 1
    return esito

for etichetta, mod, rom, start, reg in (
        ('NPC 0x021FA570 -> r3', 'ov001', 'sgp-1.2-EN.nds', 0x021FA574, 'r3'),
        ('NPC 0x021FA570 -> r1', 'ov001', 'sgp-1.2-EN.nds', 0x021FA574, 'r1'),
        ('NPC 0x021FA570 -> r2', 'ov001', 'sgp-1.2-EN.nds', 0x021FA574, 'r2'),
        ('WIFI G1 0x020070A8 -> r1 (caduta fittizia)', 'arm9', 'sgp-1.2-EN.nds', 0x020070AC, 'r1'),
        ('WILD 0x02247D3A -> r7', 'ov002', 'sgp-1.2-EN.nds', 0x02247D3E, 'r7'),
        ('WILD 0x02247D3A -> r0', 'ov002', 'sgp-1.2-EN.nds', 0x02247D3E, 'r0'),
):
    leggi = lettore(mod, rom)
    print('==', etichetta)
    for k, v in vivo(leggi, start, reg)[:6]:
        print('   %-38s %s' % (k, v))
