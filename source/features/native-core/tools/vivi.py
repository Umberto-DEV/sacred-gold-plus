#!/usr/bin/env python3
"""Vivezza di registri e flag NZCV subito dopo ogni sito di gancio.

Cammina la caduta naturale (fallthrough) dal sito, in Thumb/ARM, e per ogni
registro dice se e' LETTO prima di essere SCRITTO; per i flag dice se una
istruzione li LEGGE (condizionale o adc/sbc) prima che un'altra li riscriva.
Sola lettura.
"""
import sys, json
from pathlib import Path
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_ARM
from capstone.arm import ARM_REG_CPSR, ARM_CC_AL, ARM_CC_INVALID

R = Path(__file__).resolve().parents[4]   # radice del repo
W = R / 'the private development workspace'
sys.path.insert(0, str(W / 'SGP-1.2-PLUS-02/tools'))
sys.path.insert(0, str(W / 'SGP-1.2-PRESTAZIONI-NPC-03/tools'))
from arm9 import Arm9
import overlay_patch as OP

ROMS = R / '$SGP_ROM_DIR'
MDT = Cs(CS_ARCH_ARM, CS_MODE_THUMB); MDT.detail = True
MDA = Cs(CS_ARCH_ARM, CS_MODE_ARM);   MDA.detail = True

SITI = [
    ('trainer-1', 'arm9',  0x02073718, 'thumb'),
    ('trainer-2', 'arm9',  0x02073802, 'thumb'),
    ('trainer-3', 'arm9',  0x0207390C, 'thumb'),
    ('trainer-4', 'arm9',  0x02073A0C, 'thumb'),
    ('wild',      'ov002', 0x02247D3A, 'thumb'),
    ('npc',       'ov001', 0x021FA570, 'thumb'),
    ('wifi-g1',   'arm9',  0x020070A8, 'thumb'),
    ('salva-1',   'arm9',  0x020271F8, 'thumb'),
    ('salva-2',   'arm9',  0x02027456, 'thumb'),
]
# lunghezza dei byte SOSTITUITI (sempre 4: un BL Thumb)
DOPO = 4

def modulo(et, nome):
    p = ROMS / ('sgp-1.2-%s.nds' % et if not et.startswith('base') else 'base-1.1-%s.nds' % et.split('-')[1])
    if nome == 'arm9':
        a = Arm9(p)
        return lambda ram, n: a.leggi(ram, n)
    oid = int(nome[2:])
    r = OP.Rom(p.read_bytes()); v, _, img = r.immagine_overlay(oid)
    return lambda ram, n: img[ram - v['ram']: ram - v['ram'] + n]

def analizza(leggi, sito, modo, n=14):
    md = MDT if modo == 'thumb' else MDA
    dati = leggi(sito + DOPO, 4 * n + 8)
    righe = list(md.disasm(dati, sito + DOPO))[:n]
    scritti, out = set(), []
    flag_letti_da, flag_scritti_da = None, None
    for ins in righe:
        letti, scrit = ins.regs_access()
        nomi_l = [ins.reg_name(x) for x in letti]
        nomi_s = [ins.reg_name(x) for x in scrit]
        legge_cpsr = 'cpsr' in nomi_l or (ins.cc not in (ARM_CC_AL, ARM_CC_INVALID))
        scrive_cpsr = 'cpsr' in nomi_s or ins.update_flags
        if legge_cpsr and flag_letti_da is None and flag_scritti_da is None:
            flag_letti_da = '0x%08X %s %s' % (ins.address, ins.mnemonic, ins.op_str)
        if scrive_cpsr and flag_scritti_da is None:
            flag_scritti_da = '0x%08X %s %s' % (ins.address, ins.mnemonic, ins.op_str)
        vivi = [x for x in nomi_l if x.startswith('r') and x not in scritti and x != 'pc']
        out.append({'i': '0x%08X  %-8s %s' % (ins.address, ins.mnemonic, ins.op_str),
                    'legge': nomi_l, 'scrive': nomi_s,
                    'letti_prima_di_essere_scritti': vivi})
        for x in nomi_s:
            scritti.add(x)
        if ins.mnemonic in ('bx', 'pop') and 'pc' in nomi_s:
            break
        if ins.mnemonic == 'b' and ins.cc in (ARM_CC_AL, ARM_CC_INVALID):
            break
    # registri vivi = letti prima di essere scritti, su tutta la finestra
    scritti2, vivi_tot = set(), []
    for ins in righe:
        letti, scrit = ins.regs_access()
        for x in [ins.reg_name(y) for y in letti]:
            if x.startswith('r') and x not in scritti2 and x not in vivi_tot:
                vivi_tot.append(x)
        for x in [ins.reg_name(y) for y in scrit]:
            scritti2.add(x)
        if ins.mnemonic in ('bx', 'pop') and 'pc' in [ins.reg_name(y) for y in scrit]:
            break
        if ins.mnemonic == 'b' and ins.cc in (ARM_CC_AL, ARM_CC_INVALID):
            break
    return out, vivi_tot, flag_letti_da, flag_scritti_da

for chiave, mod, sito, modo in SITI:
    leggi = modulo('EN', mod)
    out, vivi, fl, fs = analizza(leggi, sito, modo)
    print('=' * 78)
    print('%s @ 0x%08X (%s, %s)' % (chiave, sito, mod, modo))
    print('  registri VIVI dopo il sito (letti prima di essere riscritti): %s' % ', '.join(vivi))
    print('  primo lettore di NZCV : %s' % (fl or 'NESSUNO nella finestra'))
    print('  primo scrittore NZCV  : %s' % (fs or 'nessuno'))
    print('  -> flag NZCV VIVI?    : %s' % ('SI' if fl else 'NO'))
    for x in out[:6]:
        print('     %s   [letti %s]' % (x['i'], ','.join(x['legge'])))
