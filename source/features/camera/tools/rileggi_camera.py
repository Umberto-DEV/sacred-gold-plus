#!/usr/bin/env python3
"""RILETTORE INDIPENDENTE della candidata C1.

Non importa l'applicatore. Riapre le due immagini da zero, ricava i segmenti
dell'ARM9 dai parametri di modulo con codice proprio, disassembla con capstone e
ricontrolla la mappa della riserva a mano. Riconosce da se' il modo (zona-1.2 o
in-luogo) seguendo il letterale CAM_EXC, non un'opzione.

    python3 tools/rileggi_camera.py <base.nds> <candidata.nds> [--json f]
                                    [--attese id:val,...]

Cancelli R0-R9, descritti in CRITERI.md §3.
"""
import argparse, hashlib, json, struct, sys
from pathlib import Path
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB

sys.path.insert(0, str(Path(__file__).resolve().parent))
import tabella as T

CAN11, ECC11, ECC11_N = 0x023DEB40, 0x023DEB6C, 32
COD, COD_N, COD_TESTO = 0x023DEB8C, 84, 62
LIT_EXC, LIT_EXC_END = 0x023DEBD4, 0x023DEBD8
REPEL, REPEL_N = 0x023DEBE0, 160
BORSA, BORSA_N, BSS_N = 0x023DEC80, 4420, 548
LIBERO11, LIBERO11_N, STATO = 0x023DFFE8, 20, 0x023DFFFC
SITO, LIT_SITO = 0x0203B400, 0x0203B418
MAPHDR, MAPHDR_N, STRIDE = 0x020F6BE0, 540, 24
ARENA_HI_LIT = 0x020D2BB0
ECC12, ECC12_N, CAN_ECC12, CAN_ECC12_N = 0x023D8040, 48, 0x023D8070, 16
CAN12, CAN12_N = 0x023D8000, 32
ECC11_NUOVA = 0x023DEB5C


class Immagine:
    """Cammina l'ARM9 senza riusare arm9.py: codice diverso, stesso risultato."""

    def __init__(self, path):
        self.raw = Path(path).read_bytes()
        off9 = struct.unpack_from('<I', self.raw, 0x20)[0]
        ram9 = struct.unpack_from('<I', self.raw, 0x28)[0]
        self.off9, self.ram9 = off9, ram9
        p = struct.unpack_from('<9I', self.raw, off9 + 0xBA0)
        tab0, tab1, dati0 = p[0], p[1], p[2]
        self.sez, q = [], off9 + tab0 - ram9
        while q < off9 + tab1 - ram9:
            self.sez.append(struct.unpack_from('<3I', self.raw, q)); q += 12
        self.seg, o = [(ram9, off9, dati0 - ram9)], off9 + dati0 - ram9
        for ram, size, _ in self.sez:
            self.seg.append((ram, o, size)); o += size
        self.fine_arm9 = o

    def b(self, ram, n):
        for base, o, size in self.seg:
            if base <= ram and ram + n <= base + size:
                return self.raw[o + ram - base: o + ram - base + n]
        raise KeyError('0x%08X+%d' % (ram, n))

    def w(self, ram):
        return struct.unpack('<I', self.b(ram, 4))[0]

    def o(self, ram):
        for base, of, size in self.seg:
            if base <= ram < base + size:
                return of + ram - base
        raise KeyError('0x%08X' % ram)


def sha(x):
    return hashlib.sha256(bytes(x)).hexdigest()


def canarino(base_motivo, parole):
    return b''.join(struct.pack('<I', base_motivo | i) for i in range(parole))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('base'); ap.add_argument('cand')
    ap.add_argument('--json'); ap.add_argument('--attese', default='')
    a = ap.parse_args()
    attese = (dict(T.CANONICA) if not a.attese else
              {int(k): int(v) for k, v in (p.split(':') for p in a.attese.split(','))})

    b, c = Immagine(a.base), Immagine(a.cand)
    esiti, rosso = [], []

    def R(nome, cond, nota):
        esiti.append({'cancello': nome, 'esito': 'VERDE' if cond else 'ROSSO', 'nota': nota})
        print('  %-3s %-6s %s' % (nome, 'VERDE' if cond else 'ROSSO', nota))
        if not cond:
            rosso.append(nome)

    # --- il modo si deduce dal letterale, non da un'opzione
    ecc = c.w(LIT_EXC)
    modo = 'zona-1.2' if ecc == ECC12 else ('in-luogo' if ecc == ECC11_NUOVA else 'IGNOTO')
    print('MODO dedotto dal letterale CAM_EXC (0x%08X = 0x%08X): %s' % (LIT_EXC, ecc, modo))

    # R0
    ris = c.sez[-1]
    atteso_ris = (0x023D8000, 32768, 0) if modo == 'zona-1.2' else (0x023DEB40, 5312, 0)
    R('R0', len(b.raw) == len(c.raw) and len(c.sez) == 3 and ris == atteso_ris
      and modo != 'IGNOTO',
      'dimensioni uguali (%d B), 3 sezioni, riserva 0x%08X/%d bss %d' % ((len(c.raw),) + ris))

    # R1
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    ist = [(i.mnemonic, i.op_str) for i in md.disasm(c.b(SITO, 4), SITO)]
    R('R1', ist == [('ldr', 'r3, [pc, #0x14]'), ('bx', 'r3')] and c.w(LIT_SITO) == (COD | 1),
      'sito = %s ; letterale 0x%08X = 0x%08X'
      % ('; '.join('%s %s' % x for x in ist), LIT_SITO, c.w(LIT_SITO)))

    # R2 — il codice: 80 byte identici alla base, cambiano solo i letterali previsti
    cod_c, cod_b = c.b(COD, COD_N), b.b(COD, COD_N)
    pool = [struct.unpack_from('<I', cod_c, COD_TESTO + 2 + 4 * i)[0] for i in range(5)]
    fine = ecc + (ECC12_N if modo == 'zona-1.2' else 48)
    pool_atteso = [0x0203B269, STATO, ecc, fine, MAPHDR]
    n_ist = sum(1 for _ in md.disasm(cod_c[:COD_TESTO], COD))
    dive = [COD + i for i in range(COD_N) if cod_c[i] != cod_b[i]]
    ammessi = set(range(LIT_EXC, LIT_EXC + 4)) | (set(range(LIT_EXC_END, LIT_EXC_END + 4))
                                                  if modo == 'zona-1.2' else set())
    R('R2', pool == pool_atteso and n_ist == 31 and dive and set(dive) <= ammessi,
      'pool %s ; %d istruzioni Thumb ; %d byte diversi dalla base, tutti nei letterali'
      % (['0x%08X' % x for x in pool], n_ist, len(dive)))

    # R3 — la tabella, dove il letterale dice che sia
    tab = c.b(ecc, fine - ecc)
    dec, voci = T.decodifica(tab)
    cresc = all(voci[i] < voci[i + 1] for i in range(len(voci) - 1))
    R('R3', dec == attese and cresc and len(voci) == 24,
      '%d voci a 0x%08X, crescenti=%s ; %s'
      % (len(voci), ecc, cresc, ', '.join('%d->%d' % (k, dec[k]) for k in sorted(dec))))

    # R4 — i canarini
    if modo == 'zona-1.2':
        ok4 = (c.b(CAN12, CAN12_N) == canarino(0xCA5A1000, 8)
               and c.b(CAN11, 32) == canarino(0xCA5A0000, 8)
               and c.b(CAN_ECC12, CAN_ECC12_N) == canarino(0xCA5A1100, 4))
        nota4 = ('basso 0xCA5A1000|0..7 a 0x%08X ; di coda 0xCA5A1100|0..3 a 0x%08X ; '
                 '1.1 di 32 B INTATTO a 0x%08X' % (CAN12, CAN_ECC12, CAN11))
    else:
        ok4 = c.b(CAN11, 28) == canarino(0xCA5A0000, 7)
        nota4 = '1.1 ridotto a 28 B, motivo 0xCA5A0000|0..6'
    R('R4', ok4, nota4)

    # R5 — i blocchi che non si devono toccare
    uguali = all(c.b(x, n) == b.b(x, n) for x, n in
                 ((REPEL, REPEL_N), (BORSA, BORSA_N), (BORSA + BORSA_N, BSS_N),
                  (LIBERO11, LIBERO11_N)))
    dismessa = c.b(ECC11, ECC11_N) == b.b(ECC11, ECC11_N) if modo == 'zona-1.2' else True
    R('R5', uguali and dismessa and set(c.b(BORSA + BORSA_N, BSS_N)) == {0}
      and set(c.b(LIBERO11, LIBERO11_N)) == {0} and c.w(STATO) == 1
      and c.w(ARENA_HI_LIT) == b.w(ARENA_HI_LIT),
      'repellente/borsa/bss/20 B liberi/arena identici alla base ; stato camera = %d%s'
      % (c.w(STATO), ' ; tabella 1.1 dismessa intatta' if modo == 'zona-1.2' else ''))

    # R6
    R('R6', c.b(MAPHDR, MAPHDR_N * STRIDE) == b.b(MAPHDR, MAPHDR_N * STRIDE),
      'le %d parole della tabella dei map header sono identiche alla base' % MAPHDR_N)

    # R7
    R('R7', b.raw[:b.off9] + b.raw[b.fine_arm9:] == c.raw[:c.off9] + c.raw[c.fine_arm9:],
      'fuori dall\'ARM9 (%d B) la ROM e\' identica alla base'
      % (len(c.raw) - (c.fine_arm9 - c.off9)))

    # R8 — l'insieme esatto dei byte diversi
    diversi = [i for i in range(len(b.raw)) if b.raw[i] != c.raw[i]]
    leciti = set(range(c.o(ecc), c.o(ecc) + (fine - ecc))) | set(range(c.o(LIT_EXC), c.o(LIT_EXC) + 4))
    if modo == 'zona-1.2':
        leciti |= set(range(c.o(CAN_ECC12), c.o(CAN_ECC12) + CAN_ECC12_N))
        leciti |= set(range(c.o(LIT_EXC_END), c.o(LIT_EXC_END) + 4))
    R('R8', diversi and set(diversi) <= leciti,
      '%d byte diversi dalla base, tutti dentro tabella, canarino di coda o letterali'
      % len(diversi))

    # R9 — il gancio, riletto per quel che FA: il ramo Plus non legge i map header
    testo = list(md.disasm(cod_c[:COD_TESTO], COD))
    prima_del_salto = [i for i in testo if i.address < 0x023DEBBA]
    legge_header = any(i.mnemonic.startswith('ldr') and '#0x14]' in i.op_str
                       for i in prima_del_salto)
    R('R9', not legge_header,
      'nel ramo Plus (0x%08X..0x023DEBB9) NON c\'e\' nessuna lettura «ldr r0,[r0,#0x14]»: '
      'modificare sMapHeaders[].cameraType non puo\' cambiare la camera con il Plus acceso'
      % COD)

    print('\nESITO: %s' % ('VERDE' if not rosso else 'ROSSO (%s)' % ', '.join(rosso)))
    if a.json:
        Path(a.json).write_text(json.dumps(
            {'base': a.base, 'candidata': a.cand, 'modo': modo,
             'sha256_base': sha(b.raw), 'sha256_candidata': sha(c.raw),
             'byte_diversi': len(diversi), 'tabella_a': '0x%08X' % ecc,
             'tabella': {str(k): v for k, v in sorted(dec.items())},
             'cancelli': esiti, 'esito': 'VERDE' if not rosso else 'ROSSO'}, indent=1))
    return 0 if not rosso else 1


if __name__ == '__main__':
    sys.exit(main())
