#!/usr/bin/env python3
"""Rilettore indipendente di ``sgp.anim2`` v5.

Usa il decoder BLZ in avanti del rilettore v4, famiglia distinta dal
compressore dell'applicatore. API: ``rileggi(prima, dopo, build_dir)``.
"""
import argparse
import hashlib
import json
import struct
import sys
import tempfile
from pathlib import Path

QUI = Path(__file__).resolve().parent
REPO = QUI.parents[3]
sys.path.insert(0, str(REPO / "source" / "features" / "anim" / "tools"))
from rileggi_anim4 import Arm9RO, tabelle, leggi_overlay, immagine_overlay  # noqa: E402

BASE, N_BLOCCO = 0x023DB500, 0x800
OFF_CAN, OFF_TAB, OFF_PAR, OFF_SITI = 0x600, 0x620, 0x640, 0x660
OFF_STATO, OFF_SLOT = 0x6A0, 0x6E0
G3, G1, G2, CODA = 0x0225DC8A, 0x0226200C, 0x02262016, 0x02262032
POST_CODA = bytes.fromhex("206a0421")


def sha(b):
    return hashlib.sha256(bytes(b)).hexdigest()


def posizioni_diverse(a, b):
    """Rende gli offset diversi sull'intero file, a fette da 1 MiB."""
    n = min(len(a), len(b))
    fuori = []
    passo = 1 << 20
    for inizio in range(0, n, passo):
        fine = min(inizio + passo, n)
        if a[inizio:fine] == b[inizio:fine]:
            continue
        fuori.extend(i for i in range(inizio, fine) if a[i] != b[i])
    fuori.extend(range(n, max(len(a), len(b))))
    return fuori


def bersaglio_bl(sito, dati):
    hi, lo = struct.unpack("<HH", bytes(dati))
    if (hi & 0xF800) != 0xF000 or (lo & 0xF800) != 0xF800:
        return None
    d = ((hi & 0x7FF) << 12) | ((lo & 0x7FF) << 1)
    if d & (1 << 22):
        d -= 1 << 23
    return (sito + 4 + d) & 0xFFFFFFFF


def _arm9(raw):
    td = tempfile.TemporaryDirectory()
    p = Path(td.name) / "rom.nds"
    p.write_bytes(raw)
    return td, Arm9RO(p)


def rileggi(prima, dopo, build_dir):
    prima, dopo = bytes(prima), bytes(dopo)
    p = Path(build_dir)
    man = json.loads((p / "manifesto.json").read_text())
    blob = (p / "blob.bin").read_bytes()
    can = (p / "canarino.bin").read_bytes()
    tab, par, siti = ((p / n).read_bytes() for n in ("tab_u.bin", "par.bin", "siti.bin"))
    td0, a = _arm9(prima)
    td1, b = _arm9(dopo)
    try:
        zona0, zona1 = a.leggi(BASE, N_BLOCCO), b.leggi(BASE, N_BLOCCO)
        esiti = []

        def ck(nome, ok, dettaglio):
            esiti.append({"cancello": nome, "esito": "verde" if ok else "ROSSO",
                          "dettaglio": dettaglio})

        ck("L0", zona0 == bytes(N_BLOCCO), "blocco di ingresso vergine")
        ck("L1", zona1[:len(blob)] == blob,
           "codice %d B sha256 %s" % (len(blob), sha(zona1[:len(blob)])))
        ck("L2", zona1[OFF_CAN:OFF_CAN + 16] == can,
           "canarino sha256 " + sha(zona1[OFF_CAN:OFF_CAN + 16]))
        ck("L3", zona1[OFF_TAB:OFF_TAB + 32] == tab and
           zona1[OFF_PAR:OFF_PAR + 32] == par and
           zona1[OFF_SITI:OFF_SITI + 64] == siti,
           "tab/par/siti riletti byte per byte")
        margini = (zona1[len(blob):OFF_CAN] + zona1[OFF_CAN + 16:OFF_TAB] +
                   zona1[OFF_TAB + 32:OFF_PAR] + zona1[OFF_PAR + 32:OFF_SITI] +
                   zona1[OFF_SITI + 64:OFF_STATO])
        ck("L4", margini == bytes(len(margini)) and zona1[OFF_STATO + 1] == 0x5A and
           zona1[OFF_STATO:OFF_STATO + 1] == b"\0" and
           zona1[OFF_STATO + 2:OFF_SLOT + 128] == bytes(OFF_SLOT + 128 - OFF_STATO - 2),
           "margini zero; stato/slot dinamici iniziali zero; guardia 0x5A")

        diff9 = [i for i in range(a.siz9) if a.raw[a.off9 + i] != b.raw[b.off9 + i]]
        leciti9 = set(range(a.off(BASE) - a.off9, a.off(BASE) - a.off9 + N_BLOCCO))
        fuori9 = [i for i in diff9 if i not in leciti9]
        ck("L5", not fuori9, "%d byte ARM9 diversi, tutti in sgp.anim2" % len(diff9))

        ta, tb = tabelle(prima), tabelle(dopo)
        ea, eb = leggi_overlay(prima, ta, 12), leggi_overlay(dopo, tb, 12)
        ia, ib = immagine_overlay(prima, ea), immagine_overlay(dopo, eb)
        off = lambda addr: addr - eb["ram"]
        att = {G3: int(man["simboli"]["sgp_avvia_tutti"], 16) & ~1,
               G2: int(man["simboli"]["sgp_stop_testa"], 16) & ~1}
        ganci_ok = (struct.unpack_from("<I", ib, off(G1))[0] ==
                    int(man["simboli"]["sgp_idle_task5"], 16) and
                    bersaglio_bl(G3, ib[off(G3):off(G3) + 4]) == att[G3] and
                    bersaglio_bl(G2, ib[off(G2):off(G2) + 4]) == att[G2] and
                    ib[off(CODA):off(CODA) + 4] == POST_CODA)
        ck("L6-ganci", ganci_ok, "G3/G1/G2 puntano ai simboli; coda v4 ritirata")
        diffov = [i for i, (x, y) in enumerate(zip(ia, ib)) if x != y]
        finestre = set()
        for x in (G3, G1, G2, CODA):
            finestre.update(range(off(x), off(x) + 4))
        inattesi = [i for i in diffov if i not in finestre]
        ck("L6", len(ia) == len(ib) and not inattesi and 1 <= len(diffov) <= 16,
           "%d byte overlay decompresso diversi; inattesi=%d" % (len(diffov), len(inattesi)))
        # Capienza fisica fino al file successivo nella FAT (l'overlay e'
        # allineato: puo' avere qualche byte oltre la sua fine logica).
        inizi = []
        for i in range(ta["fat_len"] // 8):
            s = struct.unpack_from("<I", prima, ta["fat"] + i * 8)[0]
            if s > ea["inizio"]:
                inizi.append(s)
        fine_slot = min(inizi) if inizi else len(prima)
        margine_blz = fine_slot - eb["inizio"] - eb["dim"]
        stessa_struttura = (len(prima) == len(dopo) and
                            a.off9 == b.off9 and a.siz9 == b.siz9 and
                            ta == tb and ea["id"] == eb["id"] == 12 and
                            ea["file_id"] == eb["file_id"] and
                            ea["ram"] == eb["ram"] and
                            ea["ram_size"] == eb["ram_size"] and
                            ea["voce"] == eb["voce"] and
                            ea["fat_voce"] == eb["fat_voce"] and
                            ea["inizio"] == eb["inizio"] and
                            ea["fine"] == eb["fine"])
        ck("L7-BLZ", stessa_struttura and margine_blz >= 0,
           "ricompressione in luogo; margine slot %d B" % margine_blz)

        # Confronto dell'intera immagine. Le sole finestre consentite sono il
        # blocco ARM9, il corpo logico di ov012 e le due voci di metadati che
        # descrivono la ricompressione. La coda fisica fra la fine FAT di ov012
        # e il file successivo resta fuori dalle finestre e deve essere intatta.
        leciti_file = set(range(a.off(BASE), a.off(BASE) + N_BLOCCO))
        leciti_file.update(range(ea["inizio"], ea["fine"]))
        leciti_file.update(range(ea["fat_voce"], ea["fat_voce"] + 8))
        leciti_file.update(range(ea["voce"] + 28, ea["voce"] + 32))
        diff_file = posizioni_diverse(prima, dopo)
        fuori_file = [i for i in diff_file if i not in leciti_file]
        coda_ok = (stessa_struttura and ea["fine"] <= fine_slot and
                   prima[ea["fine"]:fine_slot] == dopo[ea["fine"]:fine_slot])
        ck("L8-file", stessa_struttura and coda_ok and not fuori_file,
           "intero file confinato alle regioni dichiarate; coda FAT %d B immutata; "
           "byte inattesi=%d" % (max(0, fine_slot - ea["fine"]), len(fuori_file)))
        verde = all(x["esito"] == "verde" for x in esiti)
        return {"esito_finale": "verde" if verde else "ROSSO", "cancelli": esiti,
                "overlay_byte_diversi": len(diffov), "overlay_inattesi": len(inattesi),
                "margine_blz_byte": margine_blz,
                "sha256_prima": sha(prima), "sha256_dopo": sha(dopo)}
    finally:
        td0.cleanup()
        td1.cleanup()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("prima")
    ap.add_argument("dopo")
    ap.add_argument("--build", required=True)
    ap.add_argument("--json")
    a = ap.parse_args()
    r = rileggi(Path(a.prima).read_bytes(), Path(a.dopo).read_bytes(), a.build)
    if a.json:
        Path(a.json).write_text(json.dumps(r, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(r, indent=2, ensure_ascii=False))
    return 0 if r["esito_finale"] == "verde" else 1


if __name__ == "__main__":
    raise SystemExit(main())
