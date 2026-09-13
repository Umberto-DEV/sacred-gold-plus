#!/usr/bin/env python3
"""PASSO 2 — cameraType nativo per mappa, letto dalla ROM e confrontato con pret.

Legge la tabella dei map header nell'ARM9 statico (base 0x020F6BE0, 540 record da
24 B, la parola a +20 con cameraType nei bit 12-17 e mapType nei bit 8-11) e la
confronta, record per record, con `src/data/map_headers.h` di pret/pokeheartgold
(costanti da `include/constants/maps.h`).

    python3 tools/mappe.py <rom.nds> --pret <dir con maps.h e map_headers.h> \
                           [--json uscita.json] [--ids 119,250,...]

Stampa solo numeri e nomi simbolici: nessun byte di asset del gioco.
"""
import argparse, json, re, struct, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from arm9 import Arm9

TAB, N, STRIDE, WOFF = 0x020F6BE0, 540, 24, 20
MAPTYPE = {0: 'INVALID', 1: 'CITY_TOWN', 2: 'ROUTE', 3: 'CAVE', 4: 'INTERIOR',
           5: 'POKEMON_CENTER', 6: 'UNDERGROUND'}


def leggi_pret(d):
    """(id -> nome, id -> (mapType, cameraType)) dal sorgente pret."""
    testo_ids = (Path(d) / 'maps.h').read_text()
    ids = {}
    for m in re.finditer(r'^#define\s+(MAP_[A-Z0-9_]+)\s+(\d+)\b', testo_ids, re.M):
        ids[m.group(1)] = int(m.group(2))
    mt_const = {'MAP_TYPE_INVALID': 0, 'MAP_TYPE_CITY_TOWN': 1, 'MAP_TYPE_ROUTE': 2,
                'MAP_TYPE_CAVE': 3, 'MAP_TYPE_INTERIOR': 4, 'MAP_TYPE_POKEMON_CENTER': 5,
                'MAP_TYPE_UNDERGROUND': 6}
    testo = (Path(d) / 'map_headers.h').read_text()
    rec = {}
    for m in re.finditer(r'\[(MAP_[A-Z0-9_]+)\]\s*=\s*\{(.*?)\n\s*\}', testo, re.S):
        nome, corpo = m.group(1), m.group(2)
        if nome not in ids:
            continue
        ct = re.search(r'\.cameraType\s*=\s*([A-Za-z0-9_]+)', corpo)
        ms = re.search(r'\.mapsec\s*=\s*([A-Za-z0-9_]+)', corpo)
        mt = re.search(r'\.mapType\s*=\s*([A-Za-z0-9_]+)', corpo)
        if not ct or not mt:
            continue
        rec[ids[nome]] = (nome, mt_const[mt.group(1)], int(ct.group(1), 0),
                          ms.group(1) if ms else '?')
    return ids, rec


def leggi_rom(rom):
    r = Arm9(rom)
    fuori = {}
    for i in range(N):
        w = r.u32(TAB + STRIDE * i + WOFF)
        fuori[i] = ((w >> 8) & 0xF, (w >> 12) & 0x3F, w)
    return fuori


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('rom')
    ap.add_argument('--pret', required=True)
    ap.add_argument('--json')
    ap.add_argument('--ids', default='119,250,251,252,116,247,248,249')
    a = ap.parse_args()

    ids, pret = leggi_pret(a.pret)
    rom = leggi_rom(a.rom)
    bersagli = [int(x) for x in a.ids.split(',') if x.strip()]
    ecc16 = [2, 4, 5, 135, 176, 221, 226, 239, 244, 282, 340, 379, 396, 404, 486, 526]

    out = {'rom': a.rom, 'tabella': '0x%08X' % TAB, 'record': N,
           'pret_record': len(pret)}

    # --- confronto completo ROM vs pret
    dis_ct = [i for i in range(N) if i in pret and pret[i][2] != rom[i][1]]
    dis_mt = [i for i in range(N) if i in pret and pret[i][1] != rom[i][0]]
    print('record ROM: %d   record pret: %d' % (N, len(pret)))
    print('cameraType diversi da pret: %d   mapType diversi da pret: %d'
          % (len(dis_ct), len(dis_mt)))
    if dis_ct:
        print('   id con cameraType diverso (primi 40): %s' % dis_ct[:40])
    out['disallineati_cameraType'] = dis_ct
    out['disallineati_mapType'] = dis_mt
    out['valore_massimo_cameraType'] = max(v[1] for v in rom.values())
    print('cameraType massimo nella ROM: %d  (bounds del gioco: < 17)'
          % out['valore_massimo_cameraType'])

    def riga(i):
        nome = pret[i][0] if i in pret else '(non in pret)'
        return (i, nome, MAPTYPE.get(rom[i][0], '?'), rom[i][1],
                pret[i][2] if i in pret else None,
                pret[i][3] if i in pret else '?')

    print('\n--- le 8 mappe bersaglio di C1')
    print('%5s  %-42s %-10s %7s %8s  %s' % ('id', 'nome pret', 'mapType', 'camROM', 'camPret', 'mapsec'))
    out['bersagli'] = []
    for i in bersagli:
        t = riga(i)
        print('%5d  %-42s %-10s %7d %8s  %s' % t)
        out['bersagli'].append({'id': t[0], 'nome': t[1], 'mapType': t[2],
                                'cameraType_rom': t[3], 'cameraType_pret': t[4],
                                'mapsec': t[5]})

    print('\n--- le 16 eccezioni gia\' presenti nella tabella della 1.1')
    print('%5s  %-42s %-10s %7s %8s  %s' % ('id', 'nome pret', 'mapType', 'camROM', 'camPret', 'mapsec'))
    out['eccezioni16'] = []
    ecc_val = {2:4,4:4,5:4,135:1,176:0,221:3,226:4,239:10,244:12,282:7,340:13,379:3,396:12,404:4,486:10,526:10}
    for i in ecc16:
        t = riga(i)
        print('%5d  %-42s %-10s %7d %8s  %s' % t)
        out['eccezioni16'].append({'id': t[0], 'nome': t[1], 'mapType': t[2],
                                   'cameraType_rom': t[3], 'cameraType_pret': t[4],
                                   'mapsec': t[5], 'valore_eccezione_1_1': ecc_val[i]})

    if a.json:
        Path(a.json).write_text(json.dumps(out, indent=1))
    return 0 if not dis_ct and not dis_mt else 0


if __name__ == '__main__':
    sys.exit(main())
