#!/usr/bin/env python3
"""ORACOLO — esegue il gancio camera VERO, preso dai byte della ROM, su una CPU
ARM946E-S emulata sull'host (Unicorn), entrando da 0x0203B400 come fa il gioco.

    python3 tools/oracolo.py <rom.nds> [--json f] [--attese id:val,...]

Per tutti i 540 mapId, con lo stato camera a 1 e poi a 0, confronta il valore di
ritorno con un oracolo indipendente scritto in Python (tabella + default 11 /
cameraType nativo).  Verifica anche quattro mapId fuori intervallo e lo stato nonzero 2.

Nessun byte di ROM viene stampato: solo conteggi e i mapId in disaccordo.
"""
import argparse, json, struct, sys
from pathlib import Path
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB, UC_PROT_ALL, UC_HOOK_CODE, UC_HOOK_MEM_WRITE
from unicorn.arm_const import (UC_ARM_REG_R0, UC_ARM_REG_LR, UC_ARM_REG_SP, UC_ARM_REG_PC,
    UC_ARM_REG_CPSR, UC_ARM_REG_R4, UC_ARM_REG_R5, UC_ARM_REG_R6, UC_ARM_REG_R7,
    UC_ARM_REG_R8, UC_ARM_REG_R9, UC_ARM_REG_R10, UC_ARM_REG_R11)

sys.path.insert(0, str(Path(__file__).resolve().parent))
from arm9 import Arm9
import tabella as T

SITO = 0x0203B400
STATO = 0x023DFFFC
MAPHDR, N, STRIDE, WOFF = 0x020F6BE0, 540, 24, 20
GF_ASSERT = 0x0202551C
FINE = 0x01000000          # indirizzo di ritorno fittizio, fuori dalla RAM del gioco
PILA = 0x027E0000


def carica(rom):
    r = Arm9(rom)
    uc = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
    # MainRAM 0x02000000..0x02400000 e la pila in DTCM
    uc.mem_map(0x02000000, 0x00400000, UC_PROT_ALL)
    uc.mem_map(0x027C0000, 0x00040000, UC_PROT_ALL)
    uc.mem_map(0x01000000, 0x00001000, UC_PROT_ALL)
    for base, off, size in r.segmenti:
        if 0x02000000 <= base < 0x02400000:
            uc.mem_write(base, bytes(r.raw[off:off + size]))
    # unico stub dichiarato: GF_AssertFail -> «bx lr»
    uc.mem_write(GF_ASSERT & ~1, b'\x70\x47')
    uc.mem_write(FINE, b'\x70\x47')
    return r, uc


SAVED = (UC_ARM_REG_R4, UC_ARM_REG_R5, UC_ARM_REG_R6, UC_ARM_REG_R7,
         UC_ARM_REG_R8, UC_ARM_REG_R9, UC_ARM_REG_R10, UC_ARM_REG_R11)


def esegui(uc, mapid):
    """Execute installed hook, validating return/ABI and recording native clamp.

    No installed helper is replaced. Only GF_AssertFail is stubbed by carica().
    Assertion UI, runtime lifetime and visual camera behavior are not exercised.
    """
    seen = {'assertions': 0, 'normalized': [], 'writes_outside_stack': []}
    def code(cpu, address, size, unused):
        if address == GF_ASSERT:
            seen['assertions'] += 1
        elif address == 0x023DEB92:  # return from native validator, before state read
            seen['normalized'].append(cpu.reg_read(UC_ARM_REG_R0))
    def write(cpu, access, address, size, value, unused):
        if not PILA-16 <= address <= PILA-size:
            seen['writes_outside_stack'].append([address,size])
    hooks = [uc.hook_add(UC_HOOK_CODE, code), uc.hook_add(UC_HOOK_MEM_WRITE, write)]
    sentinels = [0xA5000000+i for i in range(len(SAVED))]
    for reg,value in zip(SAVED,sentinels):
        uc.reg_write(reg,value)
    uc.reg_write(UC_ARM_REG_R0, mapid & 0xFFFFFFFF)
    uc.reg_write(UC_ARM_REG_SP, PILA)
    uc.reg_write(UC_ARM_REG_LR, FINE | 1)
    try:
        uc.emu_start(SITO | 1, FINE, count=4000)
    finally:
        for hook in hooks:
            uc.hook_del(hook)
    if not (uc.reg_read(UC_ARM_REG_PC)==FINE and uc.reg_read(UC_ARM_REG_SP)==PILA
            and uc.reg_read(UC_ARM_REG_CPSR)&32
            and [uc.reg_read(r) for r in SAVED]==sentinels
            and not seen['writes_outside_stack']):
        raise ValueError('camera return/Thumb/callee-saved ABI/stack write-set')
    seen['reso'] = uc.reg_read(UC_ARM_REG_R0)
    return seen


def chiama(uc, mapid):
    return esegui(uc, mapid)['reso']


def verifica(rom, attese=None):
    attese = dict(T.CANONICA) if attese is None else attese
    r,uc = carica(rom)
    nativo = {i: (r.u32(MAPHDR+STRIDE*i+WOFF)>>12)&0x3F for i in range(N)}
    report = {'rom_sha256': __import__('hashlib').sha256(r.raw).hexdigest(),
              'errori': [], 'fuori_intervallo': [], 'cases': 0, 'bersagli': []}
    for stato,nome in ((1,'plus'), (0,'classic'), (2,'nonzero')):
        uc.mem_write(STATO, struct.pack('<I',stato))
        errors = 0
        for i in (*range(N),N,1000,0xFFFF,0xFFFFFFFF):
            normalized = i if i<N else 1
            expected = attese.get(normalized,T.PLUS_DEFAULT) if stato else nativo[normalized]
            seen = esegui(uc,i)
            ok = (seen['reso']==expected and seen['normalized']==[normalized]
                  and seen['assertions']==int(i>=N))
            report['cases'] += 1
            if not ok:
                report['errori'].append(dict(mapId=i,stato=stato,atteso=expected,**seen))
                errors += int(i<N)
            if i>=N:
                report['fuori_intervallo'].append(dict(mapId=i,stato=stato,**seen))
            if stato==1 and i in T.NUOVE:
                report['bersagli'].append(dict(mapId=i,reso=seen['reso'],nativo=nativo[i],atteso=expected))
        report['corretti_'+nome] = N-errors
    return report


def falsifica(rom):
    """Five local RAM mutants; restore each range, never write a ROM/save."""
    r,uc=carica(rom)
    mutants=(('clamp-map1-to-map0',0x0203B276,b'\x00\x20',540,1),
        ('exception-start-skips-first',0x023DEBD4,struct.pack('<I',0x023D8A12),2,1),
        ('first-exception-value',0x023D8A10,struct.pack('<H',(2<<4)|5),2,1),
        ('state-pool-byte-offset',0x023DEBD0,struct.pack('<I',STATO+1),0,1),
        ('hook-target',0x0203B418,struct.pack('<I',GF_ASSERT|1),2,1))
    result=[]
    for name,address,patch,mapid,state in mutants:
        original=bytes(uc.mem_read(address,len(patch)))
        uc.mem_write(STATO,struct.pack('<I',state));uc.mem_write(address,patch)
        # Unicorn translation cache must not retain pre-mutation instructions.
        uc.ctl_remove_cache(address,address+len(patch))
        normalized=mapid if mapid<N else 1
        expected=T.CANONICA.get(normalized,T.PLUS_DEFAULT)
        try:
            seen=esegui(uc,mapid)
            rejected=not (seen['reso']==expected and seen['normalized']==[normalized]
                          and seen['assertions']==int(mapid>=N))
            reason='observation mismatch' if rejected else 'ACCEPTED'
        except Exception as error:
            rejected=True;reason=type(error).__name__+': '+str(error)
        finally:
            uc.mem_write(address,original)
            uc.ctl_remove_cache(address,address+len(patch))
        result.append(dict(mutant=name,rejected=rejected,reason=reason))
    return result


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('rom');ap.add_argument('--json');ap.add_argument('--attese',default='')
    a=ap.parse_args()
    attese = None
    if a.attese:
        attese={int(k):int(v) for k,v in (p.split(':') for p in a.attese.split(','))}
    report=verifica(a.rom,attese)
    if a.json:
        Path(a.json).write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
    return int(bool(report['errori']))


if __name__=='__main__':
    sys.exit(main())
