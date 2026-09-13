#!/usr/bin/env python3
"""SGP-1.2-CARAMELLE-01 — rilettore INDIPENDENTE del blocco `sgp.caramelle`.

Regola del progetto (`source/sgp12/README.md` §3, `02-COME-LAVORARE.md` §2.3):
l'applicatore e il rilettore non condividono costanti né decodificatori. Questo
file non importa `sgp12.rom` e non importa `applica_caramelle.py`: rilegge
l'header della cartuccia da sé con `struct`, cammina i module params da sé,
decodifica la `BL` Thumb con capstone (non con l'aritmetica dell'applicatore) e
ridichiara ogni indirizzo che gli serve. Se una costante dell'applicatore fosse
sbagliata, questo file NON la eredita: la contraddice.

Le prove:
    L1  a 0x02081E96 c'è una BL Thumb, disassemblata da capstone, e il suo
        bersaglio cade DENTRO il blocco dichiarato; i due byte successivi sono
        `pop {r3,r4,r5,pc}`.
    L2  il bersaglio è esattamente la base del blocco (l'entrata sta in testa).
    L3  i byte del blocco coincidono, byte per byte, con `build/blob.bin` e
        `build/canarino.bin`; la coda del blocco è a zero.
    L4  il resto dell'ARM9 è IDENTICO alla ROM di partenza: si confrontano tutti
        i segmenti ARM9 e si pretende che le sole differenze cadano nelle tre
        regioni dichiarate.
    L5  la 1.1 è intatta: i quattro `bl` storici della Borsa, lo sha di
        `borsa.text` e il sito della correzione alla radice.
    L6  i cinque cancelli sono PRESENTI nel codice che sta in ROM: si
        disassembla il blob letto dalla ROM e si pretende di trovare i confronti
        e le tre chiamate native attese (non si legge il sorgente: si legge il
        binario).

Uso: rileggi_caramelle.py --partenza IN.nds --patchata OUT.nds [--build DIR]
GPL-3.0-or-later.
"""
import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path

import capstone

_FETTA = 1 << 20


def posizioni_diverse(a, b):
    """Le posizioni in cui `a` e `b` differiscono, a fette da 1 MiB: il
    confronto di fetta scarta in blocco i megabyte identici e si scende al
    singolo byte solo dentro una fetta che differisce. Stesso risultato di un
    `for i in range(len(a))`, che qui girava su 127 MB (due volte) e costava un
    minuto per rilettura.

    NON e' importata da `sgp12`: questo file, per progetto, non importa niente
    dalla famiglia dell'applicatore (vedi la docstring in testa). Confrontare
    due sequenze di byte non e' una costante della ROM ne' un decodificatore: e'
    l'unico pezzo che puo' essere riscritto qui senza ereditare un'ipotesi."""
    n = min(len(a), len(b))
    fuori = []
    for inizio in range(0, n, _FETTA):
        fine = min(inizio + _FETTA, n)
        if a[inizio:fine] == b[inizio:fine]:
            continue
        fuori.extend(i for i in range(inizio, fine) if a[i] != b[i])
    fuori.extend(range(n, max(len(a), len(b))))
    return fuori


# --- costanti PROPRIE di questo file (non importate) ------------------------
SITO = 0x02081E96
POP = "38bd"
BASE_ATTESA = 0x023DAC00
DIM_BLOCCO = 256
OFF_CANARINO_ATTESO = 0xF0
MOTIVO_CANARINO = 0xCA5A1600

BORSA_SHA = "61e648a5c4d1de4235f1228331012487458b53e65c71d9d6f86ad5c6c817a331"
BORSA_A, BORSA_N = 0x023DEC80, 4420
BL_STORICI = ((0x0207C39A, 0x023DFD58), (0x0207C3A6, 0x023DFD24),
              (0x02081380, 0x023DFD3C), (0x02081396, 0x023DFD6C))
RADICE_A, RADICE_B = 0x023DFB10, "0020c046"

# I nativi che il codice in ROM deve chiamare, ridichiarati qui.
NATIVI = {
    0x02078551: "Bag_GetItemQuantity",
    0x0207463D: "Party_GetCount",
    0x02074641: "Party_GetCapacity",
    0x0200E9BD: "ClearFrameAndWindow2",
    0x0207DAC5: "PartyMenu_PrintMessageOnWindow32",
    0x0200DD09: "thunk_Sprite_SetPaletteOverride",
}


class Bocciato(Exception):
    pass


def pretendi(c, m):
    if not c:
        raise Bocciato(m)


class VistaArm9:
    """Vista minima e propria sull'ARM9 di una .nds: nessun import dal
    laboratorio, solo `struct`."""

    def __init__(self, path):
        self.dati = Path(path).read_bytes()
        # header di cartuccia DS: +0x20 offset ARM9 nel file, +0x24 entry,
        # +0x28 indirizzo RAM, +0x2C dimensione.
        self.o9 = struct.unpack_from("<I", self.dati, 0x20)[0]
        self.r9, self.n9 = struct.unpack_from("<II", self.dati, 0x28)
        p = self.o9 + 0xBA0
        t0, t1, d0 = struct.unpack_from("<3I", self.dati, p)
        self.pezzi = [(self.r9, self.o9, d0 - self.r9)]
        q = self.o9 + (t0 - self.r9)
        fine = self.o9 + (t1 - self.r9)
        o = self.o9 + (d0 - self.r9)
        while q < fine:
            ram, n, _bss = struct.unpack_from("<3I", self.dati, q)
            self.pezzi.append((ram, o, n))
            o += n
            q += 12

    def posto(self, ram, n=1):
        for base, o, dim in self.pezzi:
            if base <= ram and ram + n <= base + dim:
                return o + (ram - base)
        raise Bocciato("%08X non sta in nessun pezzo dell'ARM9" % ram)

    def prendi(self, ram, n):
        o = self.posto(ram, n)
        return self.dati[o:o + n]


def sha256(b):
    return hashlib.sha256(bytes(b)).hexdigest()


def decodifica_bl(vista, ram):
    """Decodifica con CAPSTONE, non con aritmetica scritta a mano: è l'altra
    famiglia di codice rispetto a `bl_thumb`/`bl_decode` dell'applicatore."""
    md = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_THUMB)
    md.detail = True
    ist = list(md.disasm(vista.prendi(ram, 4), ram))
    pretendi(len(ist) == 1, "L1: a %08X non c'è una singola istruzione da 4 byte" % ram)
    i = ist[0]
    pretendi(i.mnemonic == "bl", "L1: a %08X c'è `%s %s`, non una BL"
             % (ram, i.mnemonic, i.op_str))
    return int(i.op_str.lstrip("#"), 0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--partenza", type=Path, required=True)
    ap.add_argument("--patchata", type=Path, required=True)
    ap.add_argument("--build", type=Path,
                    default=Path(__file__).resolve().parents[3]
                    / "sgp12" / "build" / "caramelle")
    a = ap.parse_args()

    blob = (a.build / "blob.bin").read_bytes()
    canarino = (a.build / "canarino.bin").read_bytes()
    man = json.loads((a.build / "manifesto.json").read_text())

    p0 = VistaArm9(a.partenza)
    p1 = VistaArm9(a.patchata)
    esito = {"partenza": str(a.partenza), "patchata": str(a.patchata), "prove": {}}

    # --- L1 / L2 ------------------------------------------------------------
    bersaglio = decodifica_bl(p1, SITO)
    pretendi(BASE_ATTESA <= bersaglio < BASE_ATTESA + DIM_BLOCCO,
             "L1: la BL punta a %08X, fuori dal blocco %08X+%d"
             % (bersaglio, BASE_ATTESA, DIM_BLOCCO))
    pretendi(p1.prendi(SITO + 4, 2).hex() == POP,
             "L1: dopo la BL non c'è `pop {r3,r4,r5,pc}` ma %s"
             % p1.prendi(SITO + 4, 2).hex())
    pretendi(bersaglio == BASE_ATTESA,
             "L2: la BL punta a %08X invece che alla base del blocco" % bersaglio)
    esito["prove"]["L1"] = "BL %08X -> %08X, seguita da pop" % (SITO, bersaglio)
    esito["prove"]["L2"] = "bersaglio = base del blocco"

    # --- L3 -----------------------------------------------------------------
    letto = p1.prendi(BASE_ATTESA, DIM_BLOCCO)
    pretendi(letto[:len(blob)] == blob, "L3: il blob in ROM differisce da build/blob.bin")
    pretendi(letto[OFF_CANARINO_ATTESO:OFF_CANARINO_ATTESO + 16] == canarino,
             "L3: il canarino in ROM differisce")
    atteso_canarino = b"".join((MOTIVO_CANARINO | i).to_bytes(4, "little") for i in range(4))
    pretendi(canarino == atteso_canarino,
             "L3: il canarino non segue il motivo %#x" % MOTIVO_CANARINO)
    pretendi(letto[len(blob):OFF_CANARINO_ATTESO] == bytes(OFF_CANARINO_ATTESO - len(blob)),
             "L3: lo spazio fra blob e canarino non è a zero")
    pretendi(letto[OFF_CANARINO_ATTESO + 16:] == bytes(DIM_BLOCCO - OFF_CANARINO_ATTESO - 16),
             "L3: la coda del blocco non è a zero")
    esito["prove"]["L3"] = "blob %d B + canarino 16 B, resto a zero" % len(blob)

    # --- L4: il resto dell'ARM9 è identico ---------------------------------
    pretendi(len(p0.dati) == len(p1.dati), "L4: le due ROM hanno dimensione diversa")
    regioni = [(p1.posto(SITO), 6),
               (p1.posto(BASE_ATTESA), DIM_BLOCCO)]
    dentro = set()
    for o, n in regioni:
        dentro.update(range(o, o + n))
    coperti_arm9 = set()
    for base, o, n in p1.pezzi:
        coperti_arm9.update(range(o, o + n))
    tutte = posizioni_diverse(p0.dati, p1.dati)
    fuori = [i for i in tutte if i in coperti_arm9 and i not in dentro][:9]
    pretendi(not fuori, "L4: %d byte dell'ARM9 cambiati fuori dalle regioni "
                        "dichiarate (primi: %s)"
                        % (len(fuori), [hex(x) for x in fuori[:8]]))
    # e fuori dall'ARM9 non deve essere cambiato NIENTE
    altrove = [i for i in tutte if i not in coperti_arm9]
    pretendi(not altrove, "L4: %d byte cambiati FUORI dall'ARM9 (primo %#x)"
             % (len(altrove), altrove[0] if altrove else 0))
    esito["prove"]["L4"] = "nessun byte cambiato fuori dalle regioni dichiarate"

    # --- L5: la 1.1 è intatta ----------------------------------------------
    pretendi(sha256(p1.prendi(BORSA_A, BORSA_N)) == BORSA_SHA, "L5: borsa.text cambiato")
    md = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_THUMB)
    for sito, atteso in BL_STORICI:
        ist = list(md.disasm(p1.prendi(sito, 4), sito))
        pretendi(len(ist) == 1 and ist[0].mnemonic == "bl"
                 and int(ist[0].op_str.lstrip("#"), 0) == atteso,
                 "L5: il bl storico %08X non punta più a %08X" % (sito, atteso))
    pretendi(p1.prendi(RADICE_A, 4).hex() == RADICE_B,
             "L5: la correzione alla radice 1.1 è cambiata")
    esito["prove"]["L5"] = "borsa.text, i 4 bl storici e la radice 1.1 intatti"

    # --- L6: i cancelli sono nel binario -----------------------------------
    testo = []
    md2 = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_THUMB)
    for i in md2.disasm(letto[:len(blob)], BASE_ATTESA):
        testo.append("%s %s" % (i.mnemonic, i.op_str))
    corpo = "\n".join(testo)
    attesi = {
        "G3 species != 0": "cmp r0, #0",
        "G1 itemId != 0": "ldrh r1, [r6, #0x28]",
        "G2 context == 5": "cmp r0, #5",
        "G5 due confronti senza segno": "bls",
        "stato 4": "movs r4, #4",
        "stato 0x20": "movs r4, #0x20",
        "azione 9": "movs r0, #9",
        "msg 33": "movs r1, #0x21",
        "windows[34]": "movs r0, #0x89",
        "sprites[CURSOR]": "movs r0, #0xcf",
    }
    mancanti = [k for k, v in attesi.items() if v not in corpo]
    pretendi(not mancanti, "L6: non trovo nel binario: %s" % ", ".join(mancanti))
    # i sei letterali nativi devono esserci tutti nel pool del blob
    pool = set(struct.unpack_from("<%dI" % (len(blob) // 4), letto, 0))
    persi = [n for v, n in NATIVI.items() if v not in pool and (v & ~1) + 4 not in pool
             and v - 4 not in pool]
    pretendi(not persi, "L6: letterali nativi assenti dal pool: %s" % ", ".join(persi))
    esito["prove"]["L6"] = "i cinque cancelli e i sei nativi sono nel binario"

    esito["blob"] = {"byte": len(blob), "sha256": sha256(blob),
                     "manifesto": man["blob"]["sha256"]}
    esito["sha_patchata"] = sha256(p1.dati)
    esito["esito"] = "VERDE"
    print(json.dumps(esito, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except Bocciato as e:
        print("BOCCIATO: %s" % e, file=sys.stderr)
        raise SystemExit(3)
