#!/usr/bin/env python3
"""SGP-1.2-BORSA-GEN-07 — rilettore INDIPENDENTE del blocco `sgp.borsa`.

Regola del progetto (`source/sgp12/README.md` §3): applicatore e rilettore non
condividono costanti ne' decodificatori. Questo file **non importa**
`applica_borsa.py` e non legge il suo rapporto. Rilegge l'intestazione della
cartuccia da se' con `struct`, cammina i module params da se', decodifica i due
trampolini con **capstone** (non con l'aritmetica dell'applicatore), ricalcola
l'impronta FNV-1a con un proprio ciclo, e ridigita ogni indirizzo e ogni
costante che gli servono. Se una costante dell'applicatore fosse sbagliata,
questo file NON la eredita: la contraddice.

Le uniche due cose importate da fuori sono `ndspy` (per estrarre `a/0/1/2`
dalla ROM: e' un lettore di contenitori NDS, non una conoscenza di questo
lavoro) e `scr_disasm` del pacchetto 01 — il disassemblatore **firmato**, col
cancello P1 di ri-serializzazione — che serve a RIFARE il censimento sulla ROM
letta. Rifarlo e' il punto: il confronto e' contro un censimento ricalcolato
sui byte, **non** contro il JSON che l'applicatore ha prodotto. La selezione
dei permissivi, la lista nera e il calcolo della chiave sono comunque riscritti
qui.

LE PROVE
--------
    L1  `gScriptCmdTable[125]` e `[127]` puntano DENTRO il blocco, col bit
        Thumb; le altre 851 voci sono bit per bit quelle della ROM di
        partenza.
    L2  i due trampolini, disassemblati da capstone, sono
        `push {r4, lr} / bl <corpo> / pop {r4, pc}` e la `bl` cade dentro il
        blocco.
    L3  i due puntatori agli originali a +0x5E0/+0x5E4 valgono gli indirizzi
        Thumb delle due `ScrCmd` vanilla, e la staffetta e' a zero.
    L4  il canarino: quattro parole 0xCA5A1700|i a +0x7F0.
    L5  la tabella si ricostruisce dal blocco: N voci non nulle in ordine
        crescente, poi solo zeri fino alla 120esima.
    L6  **ogni voce e' verificata sui byte di `a/0/1/2`**, senza
        disassemblatore: all'offset dichiarato c'e' davvero l'opcode 125 o
        127, e l'impronta FNV-1a sui <=32 byte che finiscono con l'istruzione
        (pavimento al byte 0 del membro, come fa `sgp_chiave`) e' quella
        scritta in tabella.
    L7  il censimento RIFATTO sulla ROM da' esattamente lo stesso insieme di
        siti permissivi della tabella, lista nera esclusa.
    L8  il blob in ROM e' quello di `build/blob.bin` e il resto del blocco
        (fra codice e puntatori, fra staffetta e tabella, fra tabella e
        canarino, e la coda) e' a zero.
    L9  TUTTO il resto dell'ARM9 e' identico alla ROM di partenza: le sole
        differenze stanno nel blocco (2048 B) e negli 8 byte delle due voci.
    L10 la catena a monte e' passata davvero: `a/0/1/2` misura 442 524 B con
        la firma finale del pacchetto 09; i membri 843/859/877 hanno lo sha
        del vanilla 1.03, i cinque membri delle appendici hanno le firme
        attese e il banco 199 di `a/0/2/7` ha 11 messaggi. E' la controprova,
        dal lato del rilettore, del cancello B3b dell'applicatore.

Uso: rileggi_borsa.py --partenza IN.nds --patchata OUT.nds [--build DIR]
                      [--censimento TSV] [--report F]
GPL-3.0-or-later.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import struct
import sys
from pathlib import Path

import capstone
import ndspy.narc
import ndspy.rom

QUI = Path(__file__).resolve().parent
PAC = QUI.parent
REPO = PAC.parents[2]

sys.path.insert(0, str(REPO / "source"))
sys.path.insert(0, str(QUI))

# `posizioni_diverse` confronta due sequenze di byte a fette da 1 MiB. Non
# porta nessuna conoscenza della ROM ne' di questo lavoro, e il coordinatore
# chiede espressamente quella di `sgp12.rom`: e' l'unica cosa che questo file
# prende dalla famiglia dell'applicatore.
from sgp12.rom import posizioni_diverse  # noqa: E402
import scr_disasm as SD  # noqa: E402

BUILD_DEFAULT = REPO / "source" / "sgp12" / "build" / "borsa"
CENSIMENTO_DEFAULT = PAC / "permissivi-1.2.tsv"
SCRCMD_DEFAULT = (Path(os.environ["SGP_PRET_SOURCE"]) / "tools/py_scripts/scrcmd.json"
                  if os.environ.get("SGP_PRET_SOURCE") else None)

# --- costanti RIDIGITATE (nessuna importata dall'applicatore) --------------
BASE_R = 0x023DAD00
DIM_R = 2048
OFF_ORIG_R = 0x5E0
OFF_STAFFETTA_R = 0x5F0
OFF_TAB_R = 0x600
N_TAB_R = 120
OFF_CAN_R = 0x7F0
MOTIVO_CAN_R = 0xCA5A1700
TAVOLA_R = 0x020FAD00
N_CMD_R = 853
IDX_GIVE_R = 125
IDX_SPACE_R = 127
VAN_GIVE_R = 0x0204E9D9
VAN_SPACE_R = 0x0204EA89
LUNG_R = 8
FIN_R = 32
NARC_R = "a/0/1/2"
PERMISSIVE_R = ("DONO_GRATUITO", "RACCOLTA_A_TERRA", "OGGETTO_NASCOSTO")
# Lista nera della revisione a mano (REVISIONE.md §2), ridigitata.
NERI_R = ((144, 127, 505), (904, 127, 660))
VOCI_ATTESE_R = 110
# Catena a monte, ridigitata (L10): lunghezza dell'archivio degli script dopo
# `premi_disfa`, sha256 dei tre membri riportati al vanilla 1.03, banco dei
# messaggi e numero di messaggi del banco 199 dopo `applica_199`.
ARCHIVIO_R = 442524
ARCHIVIO_SHA_R = "c7869d1f1328d95426ef31921eb783bc65d9fe9055263dfb1bc3652ebd2c51a0"
MEMBRI_VANILLA_R = (
    (843, 5468, "cb690bc3b229515e11dda13d691f354e0d39905597b7b2d2abd3bafb200862d1"),
    (859, 516, "5abff969bd83c4975cf0815c2f5c7c28d581cb2ecae994ca3049123918d41f9e"),
    (877, 457, "742f3f4fe75ecc952fa8fbbdc9ecee56c5f743f5199d864eb2725721cc2f4f00"),
)
MEMBRI_APPENDICI_R = (
    (3, 6163, "5c209d30c2e2166ffc77cbbe54c024823a96ea3fffc2800f11aecf0db303239a"),
    (141, 6652, "1c24e6a528f875e677eaa3d2dc8d9cc0eb5bcd0afb0a75f8cfbd98b850fcd50e"),
    (145, 1548, "d7dbc776615c591f2a276c9aadaa672536764c40d577c0848a30737b7539e71f"),
    (240, 1082, "df16804c1b9fd5b3ff0f3017b8bc9f79c016b6af354bf39f71dc0f0654704961"),
    (938, 2150, "c3aa275172ee98f5cbd193990055746b4969a7d6c60d3e996052774ea5f6ade5"),
)
MSG_NARC_R = "a/0/2/7"
BANCO_R = 199
MSG_ATTESI_R = 11


class Rosso(Exception):
    """Il rilettore non da' un verdetto quando non puo' darne uno."""


def _sha(b):
    return hashlib.sha256(bytes(b)).hexdigest()


def _fnv16(dati):
    h = 0x811C9DC5
    for x in dati:
        h = ((h ^ x) * 0x01000193) & 0xFFFFFFFF
    return h & 0xFFFF


class Vista:
    """Vista propria sull'ARM9 di una .nds: solo `struct`, niente `sgp12.rom`."""

    def __init__(self, dati: bytes):
        self.dati = dati
        self.o9 = struct.unpack_from("<I", dati, 0x20)[0]
        self.r9 = struct.unpack_from("<I", dati, 0x28)[0]
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
        raise Rosso("%08X non sta in nessun pezzo dell'ARM9" % ram)

    def prendi(self, ram, n):
        o = self.posto(ram, n)
        return self.dati[o:o + n]

    def parola(self, ram):
        return struct.unpack("<I", self.prendi(ram, 4))[0]


def _narc(percorso, nome):
    rom = ndspy.rom.NintendoDSRom.fromFile(str(percorso))
    grezzo = rom.getFileByName(nome)
    return ndspy.narc.NARC(grezzo).files, len(grezzo)


def _membri(percorso):
    return _narc(percorso, NARC_R)


def _censimento_ex_novo(percorso, scrcmd):
    """Rifa' il censimento sui byte della ROM letta. La selezione dei
    permissivi e la chiave sono ricalcolate QUI."""
    cmds = SD.Comandi(Path(scrcmd))
    files, dim = SD.carica_narc(str(percorso))
    membri = SD.disassembla_tutto(files, cmds)
    siti = SD.censisci(membri, raggio=0)
    fuori = set(NERI_R)
    out = []
    for s in siti:
        if s["opcode"] not in (IDX_GIVE_R, IDX_SPACE_R):
            continue
        if s["classe"] not in PERMISSIVE_R:
            continue
        if (s["membro"], s["opcode"], s["offset"]) in fuori:
            continue
        raw = membri[s["membro"]].raw
        fine = s["offset"] + LUNG_R
        n = FIN_R if fine > FIN_R else fine
        out.append((s["membro"], s["opcode"], s["offset"], _fnv16(raw[fine - n:fine])))
    return sorted(out), dim


def rileggi(partenza: Path, patchata: Path, build: Path, censimento: Path, scrcmd: Path):
    esiti, verde = [], True

    def esito(nome, ok, dettaglio=""):
        nonlocal verde
        esiti.append({"prova": nome, "esito": "verde" if ok else "ROSSO",
                      "dettaglio": dettaglio})
        verde = verde and bool(ok)

    blob = (Path(build) / "blob.bin").read_bytes()
    d0 = Path(partenza).read_bytes()
    d1 = Path(patchata).read_bytes()
    p0, p1 = Vista(d0), Vista(d1)
    md = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_THUMB)

    # --- L1 -----------------------------------------------------------------
    v_give = p1.parola(TAVOLA_R + 4 * IDX_GIVE_R)
    v_space = p1.parola(TAVOLA_R + 4 * IDX_SPACE_R)
    dentro = lambda a: BASE_R <= (a & ~1) < BASE_R + DIM_R  # noqa: E731
    tab0 = p0.prendi(TAVOLA_R, 4 * N_CMD_R)
    tab1 = p1.prendi(TAVOLA_R, 4 * N_CMD_R)
    cambiate = [i for i in range(N_CMD_R) if tab0[4 * i:4 * i + 4] != tab1[4 * i:4 * i + 4]]
    esito("L1", dentro(v_give) and (v_give & 1) and dentro(v_space) and (v_space & 1)
          and cambiate == [IDX_GIVE_R, IDX_SPACE_R],
          "[125]=%#010x [127]=%#010x, voci cambiate %s (attese [125, 127])"
          % (v_give, v_space, cambiate))

    # --- L2: i trampolini, con capstone ------------------------------------
    corpi, righe = {}, {}
    for nome, valore in (("cmd125", v_give), ("cmd127", v_space)):
        ind = valore & ~1
        ist = list(md.disasm(p1.prendi(ind, 8), ind))
        righe[nome] = ["%s %s" % (i.mnemonic, i.op_str) for i in ist]
        bl = [i for i in ist if i.mnemonic == "bl"]
        corpi[nome] = int(bl[0].op_str.lstrip("#"), 0) if bl else None
    ok2 = True
    for nome in ("cmd125", "cmd127"):
        r = righe[nome]
        ok2 = ok2 and len(r) >= 3 and r[0].startswith("push") and "r4" in r[0] \
            and "lr" in r[0] and r[1].startswith("bl ") and r[2].startswith("pop") \
            and "pc" in r[2] and corpi[nome] is not None \
            and BASE_R <= corpi[nome] < BASE_R + DIM_R
    ok2 = ok2 and corpi["cmd125"] != corpi["cmd127"]
    esito("L2", ok2, "; ".join("%s: %s -> %s" % (n, " / ".join(righe[n][:3]),
                                                 "0x%08X" % corpi[n] if corpi[n] else "?")
                               for n in ("cmd127", "cmd125")))

    # --- L3: i puntatori agli originali e la staffetta ----------------------
    o127 = p1.parola(BASE_R + OFF_ORIG_R)
    o125 = p1.parola(BASE_R + OFF_ORIG_R + 4)
    staff = p1.prendi(BASE_R + OFF_STAFFETTA_R, 16)
    esito("L3", o127 == VAN_SPACE_R and o125 == VAN_GIVE_R and staff == bytes(16),
          "originali +0x5E0=%#010x (atteso %#010x), +0x5E4=%#010x (atteso %#010x); "
          "staffetta a zero: %s" % (o127, VAN_SPACE_R, o125, VAN_GIVE_R, staff == bytes(16)))

    # --- L4: canarino -------------------------------------------------------
    can = p1.prendi(BASE_R + OFF_CAN_R, 16)
    atteso = b"".join((MOTIVO_CAN_R | i).to_bytes(4, "little") for i in range(4))
    esito("L4", can == atteso, "canarino %s" % can.hex())

    # --- L5: la tabella ricostruita dal blocco ------------------------------
    parole = list(struct.unpack("<%dI" % N_TAB_R, p1.prendi(BASE_R + OFF_TAB_R, 4 * N_TAB_R)))
    nz = [w for w in parole if w]
    primo_zero = next((i for i, w in enumerate(parole) if w == 0), N_TAB_R)
    coda_pulita = all(w == 0 for w in parole[primo_zero:])
    crescente = all(nz[i] < nz[i + 1] for i in range(len(nz) - 1))
    esito("L5", coda_pulita and crescente and len(nz) == VOCI_ATTESE_R,
          "%d voci non nulle, coda a zero: %s, ordine crescente: %s"
          % (len(nz), coda_pulita, crescente))

    voci = [((w >> 16) & 0xFFFF, w & 0xFFFF) for w in nz]

    # --- L6: ogni voce verificata sui byte di a/0/1/2, senza disassemblatore -
    files, dim_archivio = _membri(patchata)
    trovate, orfane = [], []
    for off, imp in voci:
        cand = []
        for idx, raw in enumerate(files):
            fine = off + LUNG_R
            if fine > len(raw):
                continue
            op = struct.unpack_from("<H", raw, off)[0]
            if op not in (IDX_GIVE_R, IDX_SPACE_R):
                continue
            n = FIN_R if fine > FIN_R else fine
            if _fnv16(raw[fine - n:fine]) != imp:
                continue
            cand.append((idx, op))
        if len(cand) == 1:
            trovate.append((cand[0][0], cand[0][1], off, imp))
        else:
            orfane.append({"offset": off, "impronta": "%#06x" % imp,
                           "candidati": [[c[0], c[1]] for c in cand]})
    esito("L6", not orfane and len(trovate) == len(voci),
          "%d voci su %d ritrovate nei byte di %s, ciascuna in UN solo membro%s"
          % (len(trovate), len(voci), NARC_R,
             "" if not orfane else "; orfane/ambigue: %s" % json.dumps(orfane[:5])))

    # --- L7: il censimento rifatto sulla ROM -------------------------------
    atteso_set, dim2 = _censimento_ex_novo(patchata, scrcmd)
    letto_set = sorted(trovate)
    manca = [x for x in atteso_set if x not in letto_set]
    piu_ = [x for x in letto_set if x not in atteso_set]
    esito("L7", not manca and not piu_ and len(atteso_set) == VOCI_ATTESE_R,
          "censimento rifatto: %d siti permissivi (lista nera esclusa), archivio "
          "%d B; mancanti in tabella: %s; in tabella e non permissivi: %s"
          % (len(atteso_set), dim2, manca[:4], piu_[:4]))

    # --- L8: il blob e gli zeri --------------------------------------------
    blocco = p1.prendi(BASE_R, DIM_R)
    ok8 = (blocco[:len(blob)] == blob
           and blocco[len(blob):OFF_ORIG_R] == bytes(OFF_ORIG_R - len(blob))
           and blocco[OFF_ORIG_R + 8:OFF_STAFFETTA_R] == bytes(OFF_STAFFETTA_R - OFF_ORIG_R - 8)
           and blocco[OFF_STAFFETTA_R + 16:OFF_TAB_R] == bytes(OFF_TAB_R - OFF_STAFFETTA_R - 16)
           and blocco[OFF_TAB_R + 4 * N_TAB_R:OFF_CAN_R]
           == bytes(OFF_CAN_R - OFF_TAB_R - 4 * N_TAB_R)
           and blocco[OFF_CAN_R + 16:] == bytes(DIM_R - OFF_CAN_R - 16))
    esito("L8", ok8, "blob %d B + zeri + puntatori + staffetta + tabella + canarino, "
                     "sha256 del blocco %s" % (len(blob), _sha(blocco)[:16]))

    # --- L9: il resto dell'ARM9 e' identico --------------------------------
    dentro_file = set(range(p1.posto(BASE_R), p1.posto(BASE_R) + DIM_R))
    for idx in (IDX_GIVE_R, IDX_SPACE_R):
        a = p1.posto(TAVOLA_R + 4 * idx, 4)
        dentro_file |= set(range(a, a + 4))
    fuori = []
    if len(d0) == len(d1):
        fuori = [i for i in posizioni_diverse(d0, d1) if i not in dentro_file]
    esito("L9", len(d0) == len(d1) and not fuori,
          "nessun byte cambiato fuori dal blocco e dalle due voci"
          if not fuori else "primi fuori: %s" % [hex(x) for x in fuori[:8]])

    # --- L10: la catena a monte ---------------------------------------------
    guasti = []
    if dim_archivio != ARCHIVIO_R:
        guasti.append("%s misura %d B invece di %d" % (NARC_R, dim_archivio, ARCHIVIO_R))
    rom_patchata = ndspy.rom.NintendoDSRom.fromFile(str(patchata))
    script_raw = rom_patchata.getFileByName(NARC_R)
    if _sha(script_raw) != ARCHIVIO_SHA_R:
        guasti.append("%s sha %s invece di %s" %
                      (NARC_R, _sha(script_raw)[:12], ARCHIVIO_SHA_R[:12]))
    for idx, n, firma in MEMBRI_VANILLA_R:
        letto = bytes(files[idx])
        if len(letto) != n or _sha(letto) != firma:
            guasti.append("membro %d: %d B / %s invece di %d B / %s"
                          % (idx, len(letto), _sha(letto)[:12], n, firma[:12]))
    for idx, n, firma in MEMBRI_APPENDICI_R:
        letto = bytes(files[idx])
        if len(letto) != n or _sha(letto) != firma:
            guasti.append("appendici membro %d: %d B / %s invece di %d B / %s"
                          % (idx, len(letto), _sha(letto)[:12], n, firma[:12]))
    msg, _ = _narc(patchata, MSG_NARC_R)
    quanti = struct.unpack_from("<H", bytes(msg[BANCO_R]), 0)[0]
    if quanti != MSG_ATTESI_R:
        guasti.append("banco %d: %d messaggi invece di %d" % (BANCO_R, quanti, MSG_ATTESI_R))
    esito("L10", not guasti,
          "archivio %d B, tre membri al vanilla 1.03, cinque membri appendici, "
          "banco 199 con %d messaggi"
          % (dim_archivio, quanti) if not guasti else "; ".join(guasti))

    return {
        "esito_finale": "verde" if verde else "ROSSO",
        "partenza": {"file": str(partenza), "sha256": _sha(d0), "bytes": len(d0)},
        "patchata": {"file": str(patchata), "sha256": _sha(d1), "bytes": len(d1)},
        "archivio_a_0_1_2_byte": dim_archivio,
        "voci_tabella": [{"membro": m, "opcode": op, "offset": off,
                          "impronta": "%#06x" % imp}
                         for m, op, off, imp in sorted(trovate)],
        "prove": esiti,
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--partenza", type=Path, required=True)
    ap.add_argument("--patchata", type=Path, required=True)
    ap.add_argument("--build", type=Path, default=BUILD_DEFAULT)
    ap.add_argument("--censimento", type=Path, default=CENSIMENTO_DEFAULT)
    ap.add_argument("--scrcmd", type=Path, default=SCRCMD_DEFAULT)
    ap.add_argument("--report", type=Path, default=None)
    a = ap.parse_args(argv)

    if a.scrcmd is None:
        ap.error("--scrcmd oppure SGP_PRET_SOURCE e' obbligatorio")

    esito = rileggi(a.partenza, a.patchata, a.build, a.censimento, a.scrcmd)
    testo = json.dumps(esito, indent=2, ensure_ascii=False)
    if a.report:
        a.report.parent.mkdir(parents=True, exist_ok=True)
        a.report.write_text(testo + "\n", encoding="utf-8")
    for p in esito["prove"]:
        print("%-3s %-6s %s" % (p["prova"], p["esito"], p["dettaglio"]))
    print("ESITO: %s" % esito["esito_finale"])
    return 0 if esito["esito_finale"] == "verde" else 1


if __name__ == "__main__":
    raise SystemExit(main())
