#!/usr/bin/env python3
"""Blocco CARAMELLE — la Caramella Rara resta nel menu squadra dopo l'uso
(blocco `sgp.caramelle`, 256 B a 0x023DAC00) e UN gancio di 6 byte nell'ARM9
statico, a 0x02081E96. Porta a `sgp12` di
`source/features/caramelle/tools/applica_caramelle.py` (SGP-1.2-CARAMELLE-01).

DOVE E PERCHE'. La funzione «uso ripetuto» della 1.1 vive su quattro ganci, e i
due che decidono «resto o esco» stanno dentro
`PartyMenu_ItemUseFunc_WaitTextPrinterThenExit` (0x02081378). La Caramella Rara
non passa mai di li': la sua catena finisce in
`PartyMenu_ItemUseFunc_LevelUpLearnMovesLoop` (0x02081C50), sotto-stato 6, che
rende BEGIN_EXIT di suo. Il gancio e' quindi nell'ultimo punto utile di quel
sotto-stato, dopo `GetMonEvolution`: la routine scrive lei
`args->selectedAction` e rende lei lo stato, cosi' il caso «esci» non IMITA il
vanilla, lo E'.

I sei byte a 0x02081E96 sostituiscono `cmp r0,#0 / beq / movs r0,#9` con una
`BL` verso l'entrata del blocco (4 B) piu' `pop {r3,r4,r5,pc}` (2 B). I dieci
byte 0x02081E9A..0x02081EA3 restano scritti come erano ma diventano
irraggiungibili. **`borsa.text` non viene ne' letto ne' chiamato**: e'
congelato dalla regola della zona 1.1, e la sequenza di rientro — la stessa di
`UX105_BAG_Tail` — e' ripetuta qui con letterali propri, cosi' le due funzioni
possono morire separatamente.

E' l'ultimo blocco della catena: non dipende da nessun altro e nessuno dipende
da lui; l'unico vincolo e' che `riserva` sia gia' passato (il blocco dev'essere
a zero).

EN e IT: **un solo blob, un solo gancio**. Gli indirizzi ARM9 statici e i byte
di ogni funzione nominata sono identici nelle due lingue (misurato su quattro
ROM, 1.1 e 1.2 per lingua), e l'offset nel file del gancio e' lo stesso.

`rileggi()` e' scritto QUI, indipendente da `applica()`: ha una propria vista
sull'ARM9 (`struct` a mano, niente `rom.py`), decodifica la BL con capstone
invece che con l'aritmetica dell'applicatore, e ridichiara ogni indirizzo che
gli serve. Se una costante di `applica()` fosse sbagliata, questo file NON la
eredita: la contraddice. `verifica.py` chiama questo.
"""
from __future__ import annotations

import hashlib
import json
import struct
import tempfile
from pathlib import Path

from ..rom import (Arm9, Rifiuto, bl_decode, bl_thumb, esigi, esigi_manifesto_descrive,
                   posizioni_diverse, sha)

# ------------------------------------------------------------------ applica
GANCIO = 0x02081E96
GANCIO_PRE = bytes.fromhex("002801d00920")                 # 6 B
# La coda intera del sotto-stato 6 (18 B): serve al controllo negativo G4 —
# se comparisse due volte nell'ARM9 statico non sapremmo di patchare il posto
# giusto.
GANCIO_CODA = bytes.fromhex("002801d0092000e0002027310870202038bd")
POP_R3R4R5PC = bytes.fromhex("38bd")

BLOCK_BASE, BLOCK_N = 0x023DAC00, 0x100
OFF_CODICE = 0x000
OFF_CANARINO, N_CANARINO = 0x0F0, 16
MAX_CODICE = OFF_CANARINO                                  # 240 B
CANARINO_MOTIVO = 0xCA5A1600
ZONA_1_2 = (0x023D8000, 0x023DEB40)

# Invarianti della 1.1 che questo blocco NON deve toccare: `borsa.text`, i
# quattro `bl` storici della Borsa nell'ARM9 statico, e il sito della
# correzione alla radice. Sono misurati su base-1.1 e 1.2, EN e IT, identici.
BORSA_TEXT = (0x023DEC80, 4420,
              "61e648a5c4d1de4235f1228331012487458b53e65c71d9d6f86ad5c6c817a331")
BORSA_BL = {0x0207C39A: 0x023DFD58, 0x0207C3A6: 0x023DFD24,
            0x02081380: 0x023DFD3C, 0x02081396: 0x023DFD6C}
RADICE_1_1 = (0x023DFB10, bytes.fromhex("0020c046"))

ENTRATE_ATTESE = ("sgp_caramelle_gancio", "sgp_caramelle_decidi")


def _carica_build(build_dir):
    build = Path(build_dir)
    man = json.loads((build / "manifesto.json").read_text())
    blob = (build / "blob.bin").read_bytes()
    canarino = (build / "canarino.bin").read_bytes()
    esigi(int(man["indirizzi"]["base"], 16) == BLOCK_BASE,
          "BUILD: manifesto compilato per un'altra base (%s)" % man["indirizzi"]["base"])
    esigi(int(man["indirizzi"]["canarino"], 16) == BLOCK_BASE + OFF_CANARINO,
          "BUILD: il manifesto mette il canarino altrove")
    esigi(int(man["indirizzi"]["gancio_arm9"], 16) == GANCIO,
          "BUILD: il manifesto dichiara un gancio diverso da %#x" % GANCIO)
    esigi(man["indirizzi"]["blocco_byte"] == BLOCK_N, "BUILD: dimensione del blocco diversa")
    esigi_manifesto_descrive(man, blob, blocco="sgp.caramelle")
    esigi_manifesto_descrive(man, canarino, "canarino", "canarino.bin", "sgp.caramelle")
    esigi(len(blob) <= MAX_CODICE, "BUILD: il blob non entra prima del canarino")
    esigi(len(canarino) == N_CANARINO, "BUILD: canarino di dimensione sbagliata")
    atteso = b"".join((CANARINO_MOTIVO | i).to_bytes(4, "little") for i in range(N_CANARINO // 4))
    esigi(canarino == atteso, "BUILD: il canarino non segue il motivo %#x" % CANARINO_MOTIVO)
    for nome in ENTRATE_ATTESE:
        esigi(nome in man["simboli"], "BUILD: simbolo mancante: %s" % nome)
    bersaglio = int(man["simboli"]["sgp_caramelle_gancio"], 16)
    esigi(bersaglio & 1 == 1, "BUILD: l'entrata non ha il bit Thumb")
    esigi(bersaglio & ~1 == BLOCK_BASE + OFF_CODICE,
          "BUILD: l'entrata non e' al primo byte del blocco: il gancio deve poter "
          "puntare alla base senza sapere l'offset")
    # ogni simbolo dichiarato deve cadere dentro il blob
    for nome, valore in man["simboli"].items():
        v = int(valore, 16) & ~1
        esigi(BLOCK_BASE + OFF_CODICE <= v < BLOCK_BASE + OFF_CODICE + len(blob),
              "BUILD: il simbolo '%s' (%s) cade fuori dal blob di sgp.caramelle" % (nome, valore))
    return man, blob, canarino, bersaglio


def _verifica_manifest_mappa(manifest_path, log):
    if not manifest_path:
        log["manifest_controllato"] = False
        return
    mappa = json.loads(Path(manifest_path).read_text())
    lo, hi = BLOCK_BASE, BLOCK_BASE + BLOCK_N
    visto = False
    for b in mappa["blocchi"]:
        base = int(b["base"], 16)
        n = b.get("bytes", 0)
        if b["nome"] == "sgp.caramelle":
            esigi(base == BLOCK_BASE and n == BLOCK_N,
                  "A4/mappa: voce 'sgp.caramelle' diversa da quella attesa")
            visto = True
            continue
        if b["nome"].startswith("libero"):
            # Un blocco «libero» che copra ancora questa area vuol dire che il
            # registro non e' stato ridotto quando il blocco e' stato prenotato:
            # e' esattamente il difetto che il registro esiste per impedire.
            esigi(not (base < hi and base + n > lo),
                  "A4/mappa: '%s' copre ancora %08X..%08X: la prenotazione di "
                  "sgp.caramelle non e' stata scalata dal serbatoio libero"
                  % (b["nome"], lo, hi))
            continue
        esigi(not (base < hi and base + n > lo), "A4/mappa: sovrapposizione con '%s'" % b["nome"])
    esigi(visto, "A4/mappa: nessuna voce 'sgp.caramelle' nel registro della riserva")
    log["manifest_controllato"] = True


def applica(rom: bytes, build, manifest_path=None) -> tuple[bytes, dict]:
    log = {"strumento": "sgp12/blocchi/caramelle.py:applica", "cancelli": []}

    def ok(c, msg=""):
        log["cancelli"].append({"cancello": c, "esito": "passato", "nota": msg})

    man, blob, canarino, bersaglio = _carica_build(build)
    _verifica_manifest_mappa(manifest_path, log)
    ok("A4", "nessuna sovrapposizione, prenotazione presente nel registro")

    log["sha256_ingresso"] = sha(rom)
    log["blob_byte"] = len(blob)
    log["bersaglio"] = "0x%08X" % bersaglio

    with tempfile.NamedTemporaryFile(suffix=".nds") as tf:
        tf.write(rom)
        tf.flush()
        r = Arm9(tf.name)
    prima = bytes(r.raw)

    # --- G2: il blocco sta nella zona 1.2 della riserva ---------------------
    esigi(ZONA_1_2[0] <= BLOCK_BASE and BLOCK_BASE + BLOCK_N <= ZONA_1_2[1],
          "G2: il blocco esce dalla zona 1.2 della riserva")
    ok("G2", "il blocco cade nella zona 1.2")

    # --- G0: idempotenza ----------------------------------------------------
    # Riapplicare non deve rifare nulla, e soprattutto non deve trasformare una
    # ROM gia' buona in una diversa. Si riconosce lo stato «gia' applicato» dai
    # byte: BL al bersaglio giusto, pop al suo posto, blocco identico.
    gia = bl_decode(GANCIO, r.leggi(GANCIO, 4))
    if gia is not None:
        esigi(gia == (bersaglio & ~1),
              "G0: a %08X c'e' gia' una BL, ma verso %08X invece che %08X: questa "
              "ROM e' stata patchata da qualcos'altro" % (GANCIO, gia, bersaglio & ~1))
        esigi(r.leggi(GANCIO + 4, 2) == POP_R3R4R5PC, "G0: BL presente ma senza il pop")
        esigi(r.leggi(BLOCK_BASE + OFF_CODICE, len(blob)) == blob,
              "G0: il gancio c'e' ma il blob in ROM e' diverso da build/blob.bin")
        esigi(r.leggi(BLOCK_BASE + OFF_CANARINO, N_CANARINO) == canarino,
              "G0: il gancio c'e' ma il canarino e' diverso")
        log.update(esito="gia-applicato", byte_diversi=0, stato_ingresso="applicato",
                   uscita_sha256=log["sha256_ingresso"])
        ok("G0", "gia' applicato e identico: nessuna scrittura")
        return rom, log
    ok("G0", "la ROM non era patchata")

    # --- G3: preimmagini ----------------------------------------------------
    pre = r.leggi(GANCIO, len(GANCIO_PRE))
    esigi(pre == GANCIO_PRE, "G3: preimmagine del gancio diversa: %s invece di %s"
          % (pre.hex(), GANCIO_PRE.hex()))
    esigi(r.leggi(BLOCK_BASE, BLOCK_N) == bytes(BLOCK_N), "G3: il blocco non e' tutto a zero")
    ok("G3", "preimmagine vanilla al gancio, 256 B a zero nel blocco")

    # --- G4: motivo unico nell'ARM9 statico ---------------------------------
    base_s, off_s, dim_s = r.segmenti[0]
    statico = bytes(r.raw[off_s:off_s + dim_s])
    n = statico.count(GANCIO_CODA)
    esigi(n == 1, "G4: la coda del sotto-stato 6 compare %d volte nell'ARM9 statico, non una" % n)
    ok("G4", "la coda del sotto-stato 6 e' unica nell'ARM9 statico")

    # --- G5: invarianti della 1.1 ------------------------------------------
    b_ram, b_n, b_sha = BORSA_TEXT
    esigi(sha(r.leggi(b_ram, b_n)) == b_sha,
          "G5: borsa.text non ha lo sha atteso: la 1.1 non e' quella che crediamo")
    for sito, atteso in sorted(BORSA_BL.items()):
        t = bl_decode(sito, r.leggi(sito, 4))
        esigi(t == atteso, "G5: il bl storico %08X punta a %s invece che a %08X"
              % (sito, "%08X" % t if t else "niente", atteso))
    esigi(r.leggi(RADICE_1_1[0], 4) == RADICE_1_1[1],
          "G5: il sito della correzione alla radice 1.1 e' cambiato")
    ok("G5", "borsa.text, i 4 bl storici e la radice 1.1 intatti")

    # --- scrittura ----------------------------------------------------------
    r.scrivi(BLOCK_BASE + OFF_CODICE, blob)
    r.scrivi(BLOCK_BASE + OFF_CANARINO, canarino)
    r.scrivi(GANCIO, bl_thumb(GANCIO, bersaglio) + POP_R3R4R5PC)

    # --- G6: controllo positivo ---------------------------------------------
    t = bl_decode(GANCIO, r.leggi(GANCIO, 4))
    esigi(t == (bersaglio & ~1), "G6: la BL scritta punta a %s, non a %08X"
          % ("%08X" % t if t else "niente", bersaglio & ~1))
    esigi(r.leggi(GANCIO + 4, 2) == POP_R3R4R5PC, "G6: il pop non e' al suo posto")
    esigi(r.leggi(BLOCK_BASE + OFF_CODICE, len(blob)) == blob, "G6: blob riletto diverso")
    esigi(r.leggi(BLOCK_BASE + OFF_CANARINO, N_CANARINO) == canarino, "G6: canarino riletto diverso")
    ok("G6", "BL, pop, blob e canarino riletti dai byte")

    # --- G7: un lettore con l'attesa sbagliata dice no ----------------------
    esigi(r.leggi(GANCIO, len(GANCIO_PRE)) != GANCIO_PRE,
          "G7: dopo la scrittura la preimmagine combacia ancora: non si e' scritto nulla")
    ok("G7", "la preimmagine non combacia piu'")

    # --- G8: conteggio esatto ----------------------------------------------
    dopo = bytes(r.raw)
    esigi(len(dopo) == len(prima), "G8: la ROM ha cambiato dimensione")
    leciti = set(range(r.off(GANCIO), r.off(GANCIO) + 6))
    leciti |= set(range(r.off(BLOCK_BASE), r.off(BLOCK_BASE) + BLOCK_N))
    # `posizioni_diverse` (in `sgp12/rom.py`): confronto a fette da 1 MiB, e il
    # byte per byte solo dentro la fetta che differisce. Qui c'era un
    # `for i in range(len(prima))` su 127 MB, ripetuto a ogni applicazione: lo
    # stesso risultato, un minuto di attesa in piu'. La funzione non porta
    # nessuna conoscenza della ROM — confronta due sequenze di byte — quindi non
    # e' una costante condivisa fra applicatore e rilettore.
    diversi = posizioni_diverse(prima, dopo)
    fuori = [i for i in diversi if i not in leciti]
    esigi(not fuori, "G8: %d byte cambiati FUORI dalle due regioni dichiarate (primo: %#x)"
          % (len(fuori), fuori[0] if fuori else 0))
    ok("G8", "%d byte cambiati, tutti dentro il gancio (6 B) e il blocco (256 B)" % len(diversi))

    log.update(esito="applicato", byte_diversi=len(diversi), stato_ingresso="vergine",
               uscita_sha256=sha(dopo))
    return dopo, log


# ---------------------------------------------------------------- rilettore
# Da qui in giu' NON si usa `Arm9`, `bl_thumb` ne' `bl_decode`: vista propria
# sull'ARM9, decodifica della BL con capstone. E' l'altra famiglia di codice.
POP_HEX = "38bd"
BASE_ATTESA = 0x023DAC00
DIM_BLOCCO = 256
OFF_CANARINO_ATTESO = 0xF0
MOTIVO_CANARINO = 0xCA5A1600
BORSA_SHA_R = "61e648a5c4d1de4235f1228331012487458b53e65c71d9d6f86ad5c6c817a331"
BORSA_A_R, BORSA_N_R = 0x023DEC80, 4420
BL_STORICI = ((0x0207C39A, 0x023DFD58), (0x0207C3A6, 0x023DFD24),
              (0x02081380, 0x023DFD3C), (0x02081396, 0x023DFD6C))
RADICE_A_R, RADICE_B_R = 0x023DFB10, "0020c046"
SITO_R = 0x02081E96

# I nativi che il codice in ROM deve chiamare, ridichiarati qui.
NATIVI = {
    0x02078551: "Bag_GetItemQuantity",
    0x0207463D: "Party_GetCount",
    0x02074641: "Party_GetCapacity",
    0x0200E9BD: "ClearFrameAndWindow2",
    0x0207DAC5: "PartyMenu_PrintMessageOnWindow32",
    0x0200DD09: "thunk_Sprite_SetPaletteOverride",
}


class _Vista:
    """Vista minima e propria sull'ARM9 di una .nds: solo `struct`."""

    def __init__(self, dati: bytes):
        self.dati = dati
        self.o9 = struct.unpack_from("<I", dati, 0x20)[0]
        self.r9, self.n9 = struct.unpack_from("<II", dati, 0x28)
        t0, t1, d0 = struct.unpack_from("<3I", dati, self.o9 + 0xBA0)
        self.pezzi = [(self.r9, self.o9, d0 - self.r9)]
        q = self.o9 + (t0 - self.r9)
        fine = self.o9 + (t1 - self.r9)
        o = self.o9 + (d0 - self.r9)
        while q < fine:
            ram, n, _bss = struct.unpack_from("<3I", dati, q)
            self.pezzi.append((ram, o, n))
            o += n
            q += 12

    def posto(self, ram, n=1):
        for base, o, dim in self.pezzi:
            if base <= ram and ram + n <= base + dim:
                return o + (ram - base)
        raise Rifiuto("%08X non sta in nessun pezzo dell'ARM9" % ram)

    def prendi(self, ram, n):
        o = self.posto(ram, n)
        return self.dati[o:o + n]


def _sha256(b):
    return hashlib.sha256(bytes(b)).hexdigest()


def rileggi(ingresso: bytes, derivata: bytes, build) -> dict:
    """L1-L6, sullo stampo di `features/caramelle/tools/rileggi_caramelle.py`."""
    build = Path(build)
    man = json.loads((build / "manifesto.json").read_text())
    blob = (build / "blob.bin").read_bytes()
    canarino = (build / "canarino.bin").read_bytes()

    esiti, verde = [], True

    def esito(nome, ok_, dettaglio=""):
        nonlocal verde
        esiti.append({"cancello": nome, "esito": "verde" if ok_ else "ROSSO",
                      "dettaglio": dettaglio})
        verde = verde and ok_

    try:
        import capstone
    except ImportError:                                        # pragma: no cover
        # M1 della revisione R1, stessa regola di `camera.py`: senza capstone il
        # rilettore RIFIUTA invece di dare un verdetto. Un rilettore che si
        # ammorbidisce quando manca una dipendenza non e' un rilettore.
        raise Rifiuto("rilettore caramelle: serve capstone (source/requirements.txt); "
                      "senza, non c'e' una seconda famiglia di decodifica e il "
                      "verdetto non varrebbe niente")

    p0 = _Vista(ingresso)
    p1 = _Vista(derivata)

    # --- L1 / L2 ------------------------------------------------------------
    md = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_THUMB)
    ist = list(md.disasm(p1.prendi(SITO_R, 4), SITO_R))
    ok_bl = len(ist) == 1 and ist[0].mnemonic == "bl"
    bersaglio = int(ist[0].op_str.lstrip("#"), 0) if ok_bl else None
    esito("L1", ok_bl and BASE_ATTESA <= bersaglio < BASE_ATTESA + DIM_BLOCCO
          and p1.prendi(SITO_R + 4, 2).hex() == POP_HEX,
          "a %08X una BL dentro il blocco, seguita da pop {r3,r4,r5,pc}" % SITO_R)
    esito("L2", bersaglio == BASE_ATTESA,
          "la BL punta alla base del blocco (%s)" % ("0x%08X" % bersaglio if bersaglio else "?"))

    # --- L3: i byte del blocco ---------------------------------------------
    letto = p1.prendi(BASE_ATTESA, DIM_BLOCCO)
    atteso_canarino = b"".join((MOTIVO_CANARINO | i).to_bytes(4, "little") for i in range(4))
    esito("L3", letto[:len(blob)] == blob
          and letto[OFF_CANARINO_ATTESO:OFF_CANARINO_ATTESO + 16] == canarino
          and canarino == atteso_canarino
          and letto[len(blob):OFF_CANARINO_ATTESO] == bytes(OFF_CANARINO_ATTESO - len(blob))
          and letto[OFF_CANARINO_ATTESO + 16:] == bytes(DIM_BLOCCO - OFF_CANARINO_ATTESO - 16),
          "blob %d B + canarino 16 B a +0x%X, il resto a zero" % (len(blob), OFF_CANARINO_ATTESO))

    # --- L4: niente cambia fuori dalle due regioni --------------------------
    dentro = set(range(p1.posto(SITO_R), p1.posto(SITO_R) + 6))
    dentro |= set(range(p1.posto(BASE_ATTESA), p1.posto(BASE_ATTESA) + DIM_BLOCCO))
    fuori = []
    if len(p0.dati) == len(p1.dati):
        fuori = [i for i in posizioni_diverse(p0.dati, p1.dati) if i not in dentro][:9]
    esito("L4", len(p0.dati) == len(p1.dati) and not fuori,
          "nessun byte cambiato fuori dalle regioni dichiarate"
          if not fuori else "primi fuori: %s" % [hex(x) for x in fuori[:8]])

    # --- L5: la 1.1 e' intatta ----------------------------------------------
    ok5 = _sha256(p1.prendi(BORSA_A_R, BORSA_N_R)) == BORSA_SHA_R
    for sito, atteso in BL_STORICI:
        i2 = list(md.disasm(p1.prendi(sito, 4), sito))
        ok5 = ok5 and len(i2) == 1 and i2[0].mnemonic == "bl" \
            and int(i2[0].op_str.lstrip("#"), 0) == atteso
    ok5 = ok5 and p1.prendi(RADICE_A_R, 4).hex() == RADICE_B_R
    esito("L5", ok5, "borsa.text, i 4 bl storici e la correzione alla radice 1.1 intatti")

    # --- L6: i cancelli sono nel binario, non nel sorgente -------------------
    corpo = "\n".join("%s %s" % (i.mnemonic, i.op_str)
                      for i in md.disasm(bytes(letto[:len(blob)]), BASE_ATTESA))
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
    pool = set(struct.unpack_from("<%dI" % (len(blob) // 4), bytes(letto), 0))
    persi = [n for v, n in NATIVI.items()
             if v not in pool and (v & ~1) + 4 not in pool and v - 4 not in pool]
    esito("L6", not mancanti and not persi,
          "i cinque cancelli e i sei nativi sono nel binario"
          if not (mancanti or persi) else "mancanti: %s; nativi persi: %s" % (mancanti, persi))

    return {"esito_finale": "verde" if verde else "ROSSO", "cancelli": esiti,
            "blob": {"byte": len(blob), "sha256": _sha256(blob),
                     "manifesto": man["blob"]["sha256"]}}
