#!/usr/bin/env python3
"""ORACOLO — esegue il gancio camera VERO, preso dai byte della ROM, su una CPU
ARM946E-S emulata sull'host (Unicorn), entrando da 0x0203B400 come fa il gioco.

    python3 tools/oracolo.py <rom.nds> [--json f] [--attese id:val,...]

Per tutti i 540 mapId, con lo stato camera a 1 e poi a 0, confronta il valore di
ritorno con un oracolo indipendente scritto in Python (tabella + default 11 /
cameraType nativo).  Prova anche tre mapId fuori intervallo.

Nessun byte di ROM viene stampato: solo conteggi e i mapId in disaccordo.
"""
import argparse, json, struct, sys
from pathlib import Path
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB, UC_PROT_ALL
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_LR, UC_ARM_REG_SP, UC_ARM_REG_PC

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


def chiama(uc, mapid):
    uc.reg_write(UC_ARM_REG_R0, mapid & 0xFFFFFFFF)
    uc.reg_write(UC_ARM_REG_SP, PILA)
    uc.reg_write(UC_ARM_REG_LR, FINE | 1)
    uc.emu_start(SITO | 1, FINE, count=4000)
    return uc.reg_read(UC_ARM_REG_R0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('rom'); ap.add_argument('--json'); ap.add_argument('--attese', default='')
    a = ap.parse_args()

    attese = dict(T.CANONICA)
    if a.attese:
        attese = {int(k): int(v) for k, v in (p.split(':') for p in a.attese.split(','))}

    r, uc = carica(a.rom)
    nativo = {i: (r.u32(MAPHDR + STRIDE * i + WOFF) >> 12) & 0x3F for i in range(N)}

    fuori = {'rom': a.rom, 'errori': [], 'fuori_intervallo': []}
    for stato, nome in ((1, 'plus'), (0, 'classic')):
        uc.mem_write(STATO, struct.pack('<I', stato))
        sbagliati = []
        for i in range(N):
            atteso = (attese.get(i, T.PLUS_DEFAULT) if stato else nativo[i])
            visto = chiama(uc, i)
            if visto != atteso:
                sbagliati.append({'mapId': i, 'atteso': atteso, 'visto': visto})
        print('stato=%d (%s): %d/%d corretti%s'
              % (stato, nome, N - len(sbagliati), N,
                 '' if not sbagliati else '  SBAGLIATI: %s' % sbagliati[:8]))
        fuori['errori'] += [dict(x, stato=stato) for x in sbagliati]
        fuori['corretti_%s' % nome] = N - len(sbagliati)

    # fuori intervallo: deve intervenire il bounds-check VERO del gioco
    uc.mem_write(STATO, struct.pack('<I', 1))
    for i in (N, 1000, 0xFFFF):
        v = chiama(uc, i)
        fuori['fuori_intervallo'].append({'mapId': i, 'reso': v})
        print('mapId %6d fuori intervallo -> %d' % (i, v))

    # controllo che PUO' fallire: le 8 bersaglio con lo stato acceso
    print('\nle 8 mappe bersaglio, stato=1:')
    fuori['bersagli'] = []
    for i in sorted(T.NUOVE):
        v = chiama(uc, i)
        fuori['bersagli'].append({'mapId': i, 'reso': v, 'nativo': nativo[i],
                                  'atteso': attese.get(i, T.PLUS_DEFAULT)})
        print('   %3d  reso %2d   nativo %2d   atteso %2d   %s'
              % (i, v, nativo[i], attese.get(i, T.PLUS_DEFAULT), T.NOMI.get(i, '')))

    if a.json:
        Path(a.json).write_text(json.dumps(fuori, indent=1))
    return 0 if not fuori['errori'] else 1


if __name__ == '__main__':
    sys.exit(main())
