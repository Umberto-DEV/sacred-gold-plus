#!/usr/bin/env python3
"""PASSO 1 — che cosa c'e' davvero a 0x023DEB8C nella ROM 1.1 spedita.

Disassembla gli 84 byte del blocco camera, ne estrae il pool di letterali, segue
il letterale dell'accessore a 0x0203B418 e legge i 32 byte a 0x023DEB6C e a
0x023DFFDC (le due posizioni che i documenti si contendono).

    python3 tools/disassembla.py <rom.nds> [--json uscita.json]

Stampa SOLO byte del blocco della riserva (codice scritto da questo progetto,
non contenuto del gioco), indirizzi e numeri: nessun asset, nessun testo, nessun
dato di gioco.
"""
import argparse, hashlib, json, struct, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from arm9 import Arm9
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB

CAM_COD, CAM_COD_N = 0x023DEB8C, 84
ECC_AUDIT, ECC_N = 0x023DEB6C, 32
ECC_DOC02 = 0x023DFFDC
CAM_STATE = 0x023DFFFC
CANARINO = 0x023DEB40
SITO, LIT = 0x0203B400, 0x0203B418
TAB, TAB_N, STRIDE, WOFF = 0x020F6BE0, 540, 24, 20


def esa(b, per_riga=16):
    return [' '.join('%02x' % x for x in b[i:i + per_riga]) for i in range(0, len(b), per_riga)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('rom')
    ap.add_argument('--json')
    a = ap.parse_args()

    r = Arm9(a.rom)
    out = {'rom': a.rom, 'sha256_rom': hashlib.sha256(r.raw).hexdigest(),
           'sezioni_autoload': [{'ram': '0x%08X' % s[0], 'bytes': s[1], 'bss': s[2]} for s in r.sezioni]}

    print('ROM            %s' % Path(a.rom).name)
    print('sha256         %s' % out['sha256_rom'])
    print('sezioni autoload ARM9: %d' % len(r.sezioni))
    for s in r.sezioni:
        print('   ram 0x%08X  %6d B  bss %d' % s)

    # --- il sito dell'accessore
    sito = r.leggi(SITO, 4)
    lit = r.u32(LIT)
    out['sito'] = {'ram': '0x%08X' % SITO, 'byte': sito.hex(),
                   'letterale_ram': '0x%08X' % LIT, 'letterale_valore': '0x%08X' % lit,
                   'tabella_nativa': '0x%08X' % TAB,
                   'punta_al_blocco': (lit & ~1) == CAM_COD, 'thumb': bool(lit & 1)}
    print('\n--- sito accessore 0x%08X' % SITO)
    print('   byte           %s' % ' '.join('%02x' % x for x in sito))
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    for i in md.disasm(sito, SITO):
        print('   0x%08X  %-6s %s' % (i.address, i.mnemonic, i.op_str))
    print('   letterale 0x%08X = 0x%08X   (tabella nativa = 0x%08X)' % (LIT, lit, TAB))
    print('   -> punta al blocco 0x%08X ? %s   (bit Thumb: %s)'
          % (CAM_COD, (lit & ~1) == CAM_COD, bool(lit & 1)))

    # --- il blocco camera
    cod = r.leggi(CAM_COD, CAM_COD_N)
    out['codice'] = {'ram': '0x%08X' % CAM_COD, 'bytes': CAM_COD_N,
                     'sha256': hashlib.sha256(cod).hexdigest(), 'esa': esa(cod)}
    print('\n--- blocco camera 0x%08X, %d B  sha256 %s'
          % (CAM_COD, CAM_COD_N, out['codice']['sha256']))
    for n, riga in enumerate(esa(cod)):
        print('   0x%08X  %s' % (CAM_COD + 16 * n, riga))

    print('\n--- disassemblato Thumb')
    righe, pool_da = [], None
    for i in md.disasm(cod, CAM_COD):
        righe.append('0x%08X  %-6s %s' % (i.address, i.mnemonic, i.op_str))
    # il pool: tutte le parole in coda che sono indirizzi plausibili
    testo = []
    for i in md.disasm(cod, CAM_COD):
        testo.append((i.address, i.size, i.mnemonic, i.op_str))
    # trova la fine del testo: ultimo pop/bx prima di parole allineate a 4
    # semplicemente: le ultime 5 parole sono il pool atteso.  Le rileggiamo tutte
    # e riportiamo quelle referenziate dai ldr [pc,...]
    pool = {}
    for addr, size, mn, ops in testo:
        if mn.startswith('ldr') and '[pc' in ops:
            # capstone risolve gia' l'indirizzo nel commento? no: lo calcoliamo
            try:
                off = int(ops.split('#')[-1].rstrip(']'), 0)
            except ValueError:
                continue
            pc = (addr + 4) & ~3
            src = pc + off
            if CAM_COD <= src < CAM_COD + CAM_COD_N:
                pool[src] = struct.unpack_from('<I', cod, src - CAM_COD)[0]
    for riga in righe:
        a_ = int(riga[2:10], 16)
        marca = ''
        if a_ in pool:
            marca = ''
        print('   ' + riga)
    print('\n--- pool di letterali referenziati da ldr [pc,#…]')
    for k in sorted(pool):
        print('   0x%08X : 0x%08X' % (k, pool[k]))
    out['pool'] = {'0x%08X' % k: '0x%08X' % v for k, v in sorted(pool.items())}
    out['disasm'] = righe

    # --- le due posizioni contese per la tabella eccezioni
    def leggi_voci(base):
        b = r.leggi(base, ECC_N)
        v = struct.unpack('<16H', b)
        return b, v

    print('\n--- candidate tabella eccezioni')
    out['eccezioni'] = {}
    for nome, base in (('audit 01 §4.1', ECC_AUDIT), ('doc 02 §3.2', ECC_DOC02)):
        try:
            b, v = leggi_voci(base)
        except KeyError as e:
            print('   %-14s 0x%08X  NON MAPPATO (%s)' % (nome, base, e))
            out['eccezioni']['0x%08X' % base] = {'mappato': False}
            continue
        dec = {(x >> 4): (x & 15) for x in v}
        crescente = all(v[i] <= v[i + 1] for i in range(15))
        print('   %-14s 0x%08X  sha %s' % (nome, base, hashlib.sha256(b).hexdigest()[:16]))
        print('                  esa %s' % esa(b)[0])
        print('                      %s' % esa(b)[1])
        print('                  u16 crescenti: %s' % crescente)
        print('                  decodifica (id<<4)|val: %s'
              % ', '.join('%d->%d' % (k, dec[k]) for k in sorted(dec)))
        out['eccezioni']['0x%08X' % base] = {
            'mappato': True, 'sha256': hashlib.sha256(b).hexdigest(),
            'esa': esa(b), 'crescente': crescente,
            'decodifica': {str(k): dec[k] for k in sorted(dec)}}

    # --- stato camera e canarino
    st = r.u32(CAM_STATE)
    can = r.leggi(CANARINO, 32)
    atteso = b''.join(struct.pack('<I', 0xCA5A0000 | i) for i in range(8))
    print('\n--- stato camera 0x%08X = 0x%08X   (cheat 223DFFFC)' % (CAM_STATE, st))
    print('--- canarino 0x%08X   motivo 0xCA5A0000|i atteso: %s' % (CANARINO, can == atteso))
    out['stato_camera'] = '0x%08X' % st
    out['canarino_ok'] = can == atteso

    # --- il letterale d'arena
    arena = r.u32(0x020D2BB0)
    print('--- letterale arena alta 0x020D2BB0 = 0x%08X' % arena)
    out['arena_hi'] = '0x%08X' % arena

    if a.json:
        Path(a.json).write_text(json.dumps(out, indent=1))
    return 0


if __name__ == '__main__':
    sys.exit(main())
