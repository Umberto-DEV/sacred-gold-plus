#!/usr/bin/env python3
"""APPLICATORE C1 — tabella delle eccezioni camera da 16 a 24 voci.

    python3 tools/applica_camera.py <base.nds> <uscita.nds> [--json log.json]
                                    [--tabella id:val,...] [--diagnostica]

DUE MODI, scelti LEGGENDO la base, non da un'opzione:

  «zona-1.2»  la base ha la riserva estesa di F0 (sezione di autoload 0x023D8000/32768).
              La tabella nuova, 48 B, va in zona 1.2 a 0x023D8040, seguita da 16 B di
              canarino 0xCA5A1100|i come prescrive MAPPA-RISERVA-ARM9.json. In zona 1.1
              cambiano SOLTANTO due letterali del pool (CAM_EXC, CAM_EXC_END): nessun
              blocco si muove, il canarino 1.1 resta di 32 B, la tabella vecchia resta
              dov'e' byte per byte e diventa un reperto morto.  72 byte scritti.

  «in-luogo»  la base e' una 1.1 senza riserva estesa. La tabella nuova, 48 B, entra in
              zona 1.1 a 0x023DEB5C consumando i 12 B di padding e l'ULTIMA PAROLA del
              canarino, che passa da 32 a 28 B; cambia un solo letterale (CAM_EXC).
              52 byte scritti. E' la strada di ripiego: si usa solo se F0 non ha ancora
              prodotto una candidata.

In nessuno dei due modi si scrive un byte di istruzione. Idempotente: sulla propria
uscita rifiuta con «gia' applicato» (G0, per primo). I cancelli sono in CRITERI.md §2 e
ogni rifiuto nomina il proprio.
"""
import argparse, hashlib, json, struct, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from arm9 import Arm9
import tabella as T

# --- zona 1.1, invariante nei due modi
RIS11_BASE, RIS11_N = 0x023DEB40, 5312
RIS11_SHA = '43cdd97ebb48ad43590274ae90d06352bbc5f5a85c8cb65c651d7f8b35e3e2d2'
CAN11, CAN11_N = 0x023DEB40, 32
PAD11, PAD11_N = 0x023DEB60, 12
ECC11, ECC11_N = 0x023DEB6C, 32
COD, COD_N = 0x023DEB8C, 84
COD_SHA = '0832f466100bf990210485f7d43a64d908985802b548709099a0d80d3f7cdd95'
LIT_EXC, LIT_EXC_END = 0x023DEBD4, 0x023DEBD8
POOL = {0x023DEBCC: 0x0203B269, 0x023DEBD0: 0x023DFFFC, LIT_EXC: ECC11,
        LIT_EXC_END: COD, 0x023DEBDC: 0x020F6BE0}
REPEL, REPEL_N = 0x023DEBE0, 160
BORSA, BORSA_N, BSS_N = 0x023DEC80, 4420, 548
LIBERO11, LIBERO11_N = 0x023DFFE8, 20
STATO = 0x023DFFFC
SITO, SITO_BYTE, LIT_SITO = 0x0203B400, bytes.fromhex('054b1847'), 0x0203B418
ARENA_HI_LIT, MAINEX_LIT = 0x020D2BB0, 0x020D2C64
MAPHDR, MAPHDR_N, STRIDE = 0x020F6BE0, 540, 24

# --- zona 1.2 (riserva estesa di SGP-1.2-RISERVA-01)
RIS12_BASE, RIS12_N = 0x023D8000, 32768
CAN12, CAN12_N = 0x023D8000, 32
HDR12, HDR12_N = 0x023D8020, 32
ECC12, ECC12_N = 0x023D8040, 48            # il blocco nuovo, ritagliato dal basso
CAN_ECC12, CAN_ECC12_N = 0x023D8070, 16    # canarino di coda, 0xCA5A1100|i
LIBERO12_DOPO = CAN_ECC12 + CAN_ECC12_N

# --- zona 1.1, modo di ripiego
ECC11_NUOVA, ECC11_NUOVA_N = 0x023DEB5C, 48
CAN11_RIDOTTO = 28


class Rifiuto(Exception):
    pass


def no(c, motivo):
    raise Rifiuto('%s: %s' % (c, motivo))


def sha(b):
    return hashlib.sha256(bytes(b)).hexdigest()


def motivo_canarino(base_motivo, parole):
    return b''.join(struct.pack('<I', base_motivo | i) for i in range(parole))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('base'); ap.add_argument('uscita'); ap.add_argument('--json')
    ap.add_argument('--tabella', default='',
                    help='sostituisce le 24 voci; i cancelli restano TUTTI attivi')
    ap.add_argument('--diagnostica', action='store_true',
                    help='con --tabella, rilassa il SOLO cancello «contiene le 24 voci '
                         'canoniche». Serve alle ROM diagnostiche e a nient\'altro.')
    a = ap.parse_args()

    r = Arm9(a.base)
    log = {'base': a.base, 'sha256_base': sha(r.raw), 'uscita': a.uscita, 'cancelli': [],
           'diagnostica': bool(a.diagnostica), 'tabella_esplicita': bool(a.tabella)}

    def ok(c, msg=''):
        log['cancelli'].append({'cancello': c, 'esito': 'passato', 'nota': msg})
        print('  %-4s passato  %s' % (c, msg))

    if a.diagnostica and not a.tabella:
        print('RIFIUTATO — uso: --diagnostica vale solo insieme a --tabella')
        return 2
    nuova = ({int(k): int(v) for k, v in (x.split(':') for x in a.tabella.split(','))}
             if a.tabella else dict(T.CANONICA))

    # --- il modo si LEGGE dalla base
    sezioni = {s[0]: (s[1], s[2]) for s in r.sezioni}
    if sezioni.get(RIS12_BASE) == (RIS12_N, 0):
        modo, ecc, ecc_n = 'zona-1.2', ECC12, ECC12_N
    elif sezioni.get(RIS11_BASE) == (RIS11_N, 0):
        modo, ecc, ecc_n = 'in-luogo', ECC11_NUOVA, ECC11_NUOVA_N
    else:
        print('RIFIUTATO — G0: la base non ha ne\' la riserva 1.2 (0x%08X/%d) ne\' quella '
              '1.1 (0x%08X/%d): %s' % (RIS12_BASE, RIS12_N, RIS11_BASE, RIS11_N,
                                       [('0x%08X' % s[0], s[1], s[2]) for s in r.sezioni]))
        return 2
    log['modo'], log['tabella_a'] = modo, '0x%08X' % ecc
    print('MODO: %s   tabella a 0x%08X (%d B)' % (modo, ecc, ecc_n))

    try:
        # ---------------- G0 idempotenza, PER PRIMO
        if r.leggi(ecc, ecc_n) == T.codifica(nuova):
            print('GIA\' APPLICATO: la tabella a 0x%08X e\' gia\' quella attesa. '
                  'Non riscrivo nulla.' % ecc)
            log['esito'] = 'gia-applicato'
            if a.json:
                Path(a.json).write_text(json.dumps(log, indent=1))
            return 3
        ok('G0', 'non e\' gia\' applicato')

        # ---------------- G2 sito, letterale, gancio, pool
        if r.leggi(SITO, 4) != SITO_BYTE:
            no('G2', 'i 4 byte a 0x%08X non sono «05 4b 18 47»' % SITO)
        if r.u32(LIT_SITO) != (COD | 1):
            no('G2', 'il letterale 0x%08X non vale 0x%08X' % (LIT_SITO, COD | 1))
        s_cod = sha(r.leggi(COD, COD_N))
        if s_cod != COD_SHA:
            no('G2', 'sha256 del gancio %s, atteso %s' % (s_cod, COD_SHA))
        for ind, val in POOL.items():
            if r.u32(ind) != val:
                no('G2', 'pool: 0x%08X vale 0x%08X, atteso 0x%08X' % (ind, r.u32(ind), val))
        ok('G2', 'sito, letterale 0x%08X, gancio (84 B) e pool a 5 voci combaciano' % LIT_SITO)

        # ---------------- G3 canarino e padding della zona 1.1
        if r.leggi(CAN11, CAN11_N) != motivo_canarino(0xCA5A0000, 8):
            no('G3', 'il canarino 1.1 a 0x%08X non ha il motivo atteso' % CAN11)
        if set(r.leggi(PAD11, PAD11_N)) != {0}:
            no('G3', 'il padding a 0x%08X non e\' a zero' % PAD11)
        ok('G3', 'canarino 1.1 di 32 B + 12 B di padding a zero')

        # ---------------- G4 tabella vecchia
        vecchia, _ = T.decodifica(r.leggi(ECC11, ECC11_N))
        if vecchia != T.VECCHIE:
            no('G4', 'la tabella a 0x%08X non e\' quella attesa: %s' % (ECC11, vecchia))
        ok('G4', '16 voci attese a 0x%08X' % ECC11)

        # ---------------- G9a invarianti pubblici PRIMA della scrittura
        if r.u32(STATO) != 1:
            no('G9a', 'lo stato camera a 0x%08X vale %d, atteso 1' % (STATO, r.u32(STATO)))
        atteso_arena = RIS12_BASE if modo == 'zona-1.2' else RIS11_BASE
        if r.u32(ARENA_HI_LIT) != atteso_arena:
            no('G9a', 'il letterale d\'arena 0x%08X vale 0x%08X, atteso 0x%08X'
               % (ARENA_HI_LIT, r.u32(ARENA_HI_LIT), atteso_arena))
        if r.u32(MAINEX_LIT) != 0x023E0000:
            no('G9a', 'l\'estremo alto 0x%08X non vale 0x023E0000' % MAINEX_LIT)
        if set(r.leggi(LIBERO11, LIBERO11_N)) != {0}:
            no('G9a', 'i 20 B liberi a 0x%08X non sono a zero' % LIBERO11)
        ok('G9a', 'stato=1, arena 0x%08X, estremo alto, 20 B liberi a zero' % atteso_arena)

        # ---------------- G1 la zona 1.1, per intero: TUTTO IL RESTO.
        # Si esegue DOPO i cancelli fini: altrimenti li ucciderebbe lei tutti e nessuno
        # verrebbe mai provato (difetto trovato dai mutanti M8/M9/M12, vedi RAPPORTO).
        s_ris = sha(r.leggi(RIS11_BASE, RIS11_N))
        if s_ris != RIS11_SHA:
            no('G1', 'sha256 della zona 1.1 %s, atteso %s' % (s_ris, RIS11_SHA))
        ok('G1', 'zona 1.1 0x%08X/%d sha %s' % (RIS11_BASE, RIS11_N, s_ris[:16]))

        # ---------------- G11 la zona 1.2, se c'e'
        if modo == 'zona-1.2':
            if r.leggi(CAN12, CAN12_N) != motivo_canarino(0xCA5A1000, 8):
                no('G11', 'il canarino basso a 0x%08X non ha il motivo 0xCA5A1000|i' % CAN12)
            if r.leggi(HDR12, 4) != b'SGP2':
                no('G11', 'l\'intestazione a 0x%08X non porta il magic «SGP2»' % HDR12)
            if (r.u32(HDR12 + 8), r.u32(HDR12 + 12)) != (RIS12_BASE, 0x023E0000):
                no('G11', 'l\'intestazione dichiara una riserva diversa da [0x%08X,0x023E0000)'
                   % RIS12_BASE)
            n_libero = RIS11_BASE - ECC12
            libero = r.leggi(ECC12, n_libero)
            if set(libero) != {0}:
                no('G11', 'la zona libera 1.2 a 0x%08X non e\' tutta a zero (primo byte non '
                          'nullo a +%d): qualcun altro l\'ha gia\' occupata'
                   % (ECC12, next(i for i, x in enumerate(libero) if x)))
            ok('G11', 'canarino basso 0xCA5A1000|i, intestazione «SGP2», %d B liberi a zero'
               % n_libero)

        # ---------------- G5 forma della tabella nuova
        motivi = T.controlla(nuova)
        if motivi:
            no('G5', '; '.join(motivi))
        if len(nuova) * 2 != ecc_n:
            no('G5', '%d voci: la tabella deve averne esattamente %d' % (len(nuova), ecc_n // 2))
        if not a.diagnostica:
            for k, v in T.VECCHIE.items():
                if nuova.get(k) != v:
                    no('G5', 'la voce vecchia %d->%d e\' stata persa o alterata' % (k, v))
            for k, v in T.NUOVE.items():
                if nuova.get(k) != v:
                    no('G5', 'la voce nuova %d->%d manca' % (k, v))
        ok('G5', '%d voci, crescenti, nessun blocco di 16 condiviso' % len(nuova))

        # ---------------- G10 la mappa dei blocchi, senza buchi ne' sovrapposizioni
        if modo == 'zona-1.2':
            blocchi = [('canarino.basso', CAN12, CAN12_N),
                       ('intestazione', HDR12, HDR12_N),
                       ('camera.eccezioni.1.2', ECC12, ECC12_N),
                       ('canarino.camera', CAN_ECC12, CAN_ECC12_N),
                       ('libero.1.2', LIBERO12_DOPO, RIS11_BASE - LIBERO12_DOPO),
                       ('canarino.1.1', CAN11, CAN11_N),
                       ('padding', PAD11, PAD11_N),
                       ('camera.eccezioni.dismessa', ECC11, ECC11_N),
                       ('camera.codice', COD, COD_N)]
            primo, totale = RIS12_BASE, RIS12_N
        else:
            blocchi = [('canarino.1.1', CAN11, CAN11_RIDOTTO),
                       ('camera.eccezioni', ECC11_NUOVA, ECC11_NUOVA_N),
                       ('camera.codice', COD, COD_N)]
            primo, totale = RIS11_BASE, RIS11_N
        blocchi += [('repellente', REPEL, REPEL_N), ('borsa.text', BORSA, BORSA_N),
                    ('borsa.bss', BORSA + BORSA_N, BSS_N),
                    ('libero.1.1', LIBERO11, LIBERO11_N), ('camera.stato', STATO, 4)]
        p = primo
        for nome, b, n in blocchi:
            if b != p:
                no('G10', 'buco o sovrapposizione prima di «%s»: 0x%08X != 0x%08X' % (nome, b, p))
            p = b + n
        if p != primo + totale:
            no('G10', 'i blocchi sommano %d, non %d' % (p - primo, totale))
        ok('G10', '%d blocchi contigui, somma %d B' % (len(blocchi), totale))

        # ---------------- scrittura
        prima = bytes(r.raw)
        scritture = [(ecc, T.codifica(nuova)), (LIT_EXC, struct.pack('<I', ecc))]
        if modo == 'zona-1.2':
            scritture.append((CAN_ECC12, motivo_canarino(0xCA5A1100, CAN_ECC12_N // 4)))
            scritture.append((LIT_EXC_END, struct.pack('<I', ecc + ecc_n)))
        for ram, dati in scritture:
            r.scrivi(ram, dati)

        # ---------------- G6 portata
        leciti = set()
        for ram, dati in scritture:
            o = r.off(ram, len(dati))
            leciti |= set(range(o, o + len(dati)))
        diversi = [i for i in range(len(prima)) if prima[i] != r.raw[i]]
        fuori = [i for i in diversi if i not in leciti]
        if fuori:
            no('G6', '%d byte scritti fuori portata, il primo a offset 0x%X' % (len(fuori), fuori[0]))
        ok('G6', 'scritture solo in %s'
           % ', '.join('0x%08X+%d' % (x, len(d)) for x, d in scritture))

        # ---------------- G7 dimensione
        if len(r.raw) != len(prima):
            no('G7', 'la dimensione e\' cambiata')
        ok('G7', '%d byte, invariati' % len(r.raw))

        # ---------------- G8 conteggio
        massimo = sum(len(d) for _, d in scritture)
        if len(diversi) > massimo:
            no('G8', '%d byte diversi, il massimo dichiarato e\' %d' % (len(diversi), massimo))
        ok('G8', '%d byte diversi (<= %d)' % (len(diversi), massimo))

        # ---------------- G9 invarianti, DOPO la scrittura
        if r.u32(STATO) != 1:
            no('G9', 'lo stato camera non vale piu\' 1')
        for nome, ram, n in (('repellente', REPEL, REPEL_N), ('borsa.text', BORSA, BORSA_N),
                             ('borsa.bss', BORSA + BORSA_N, BSS_N),
                             ('map header', MAPHDR, MAPHDR_N * STRIDE)):
            o = r.off(ram, n)
            if bytes(r.raw[o:o + n]) != prima[o:o + n]:
                no('G9', '«%s» e\' cambiato' % nome)
        if r.u32(ARENA_HI_LIT) != atteso_arena:
            no('G9', 'il letterale d\'arena e\' cambiato')
        parole_can = CAN11_N // 4 if modo == 'zona-1.2' else CAN11_RIDOTTO // 4
        if r.leggi(CAN11, parole_can * 4) != motivo_canarino(0xCA5A0000, parole_can):
            no('G9', 'il canarino 1.1 non ha il motivo atteso dopo la scrittura')
        if modo == 'zona-1.2':
            if r.leggi(CAN12, CAN12_N) != motivo_canarino(0xCA5A1000, 8):
                no('G9', 'il canarino basso 1.2 e\' cambiato')
            if r.leggi(ECC11, ECC11_N) != prima[r.off(ECC11, ECC11_N):r.off(ECC11, ECC11_N) + ECC11_N]:
                no('G9', 'la tabella 1.1 dismessa doveva restare byte per byte dov\'era')
        ok('G9', 'stato=1, repellente, borsa, map header, arena e canarini (1.1 a %d B) intatti'
           % (parole_can * 4))

    except Rifiuto as e:
        print('RIFIUTATO — %s' % e)
        log['esito'], log['motivo'] = 'rifiutato', str(e)
        if a.json:
            Path(a.json).write_text(json.dumps(log, indent=1))
        return 2

    r.salva(a.uscita)
    log.update(esito='applicato', sha256_uscita=sha(Path(a.uscita).read_bytes()),
               byte_diversi=len(diversi), byte_scritti=massimo,
               tabella={str(k): v for k, v in sorted(nuova.items())},
               tabella_sha256=sha(T.codifica(nuova)),
               scritture=['0x%08X+%d' % (x, len(d)) for x, d in scritture])
    print('APPLICATO  %s  sha256 %s  (%d byte diversi)'
          % (a.uscita, log['sha256_uscita'], len(diversi)))
    if a.json:
        Path(a.json).write_text(json.dumps(log, indent=1))
    return 0


if __name__ == '__main__':
    sys.exit(main())
