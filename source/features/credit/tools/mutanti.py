#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SGP-1.2-TITOLO-02 — i tre mutanti di `CRITERI.md` §5.

Ognuno è una correzione PLAUSIBILE ma SBAGLIATA del credito del titolo. Il
rilettore indipendente deve dichiararli rossi: se un mutante passa, il rilettore
non sta guardando quello che dice di guardare.

  M1  rimappa solo l'indice 13 e dimentica il 12      -> L2 / L5 / L6
  M2  rimappa 12 e 13 ma spegne un pixel (12 -> 0)    -> L3 (la forma cambia)
  M3  rimappa bene, ma tocca anche un tile NON usato
      e schiarisce la voce 124 della palette          -> L4 (membri intoccabili)

Lavora su copie nella cartella di lavoro; non tocca gli originali.

  mutanti.py --rom ROM_CORRETTA --rom-prima ROM_1.2 --lavoro DIR [--json FILE]
"""
import argparse
import json
import os
import shutil
import struct
import subprocess
import sys

QUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, QUI)
import applica_credito as A       # noqa: E402  (solo per trovare i membri nel file)


def rimappa(path, da, a_, spegni_un_pixel=False, anche_tile_non_usati=False):
    """Riscrive i nibble del membro 15 secondo una regola (giusta o storta)."""
    with open(path, "r+b") as f:
        off15, m15, _ = A.leggi_membro(f, 15)
        _o17, m17, _ = A.leggi_membro(f, 17)
        d_off, d_len, _bpp = A.dati_ncgr(m15)
        usati = sorted({c & 0x3FF for c in A.celle_nscr(m17) if c & 0x3FF})
        tile = range(d_len // 32) if anche_tile_non_usati else usati
        primo_spento = [not spegni_un_pixel]
        for t in tile:
            for k in range(32):
                b = m15[d_off + t * 32 + k]
                lo, hi = b & 0xF, b >> 4
                nlo = a_ if lo in da else lo
                nhi = a_ if hi in da else hi
                if not primo_spento[0] and lo == 12:
                    nlo = 0            # M2: spegne un pixel del glifo
                    primo_spento[0] = True
                if (nlo, nhi) != (lo, hi):
                    f.seek(off15 + d_off + t * 32 + k)
                    f.write(bytes([(nhi << 4) | nlo]))
        f.flush()


def tocca_palette(path, indice, valore):
    with open(path, "r+b") as f:
        off4, m4, _ = A.leggi_membro(f, 4)
        o, sz = A.sezione(m4, b"TTLP")
        ds = struct.unpack_from("<I", m4, o + 16)[0]
        st = o + sz - ds
        f.seek(off4 + st + indice * 2)
        f.write(struct.pack("<H", valore))
        f.flush()


def rilettore(rom, base):
    r = subprocess.run([sys.executable, os.path.join(QUI, "rileggi_credito.py"),
                        "--rom", rom, "--base", base, "--json", "-"],
                       capture_output=True, text=True)
    try:
        return r.returncode, json.loads(r.stdout)
    except Exception:
        return 2, {"errore": (r.stdout + r.stderr)[-400:]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rom", required=True, help="ROM già corretta (uscita dell'applicatore)")
    ap.add_argument("--rom-prima", required=True, help="ROM 1.2 non ancora corretta")
    ap.add_argument("--lavoro", required=True)
    ap.add_argument("--json")
    a = ap.parse_args()
    os.makedirs(a.lavoro, exist_ok=True)

    esiti = {}
    ricette = [
        ("M1", "rimappa solo l'indice 13: metà glifo resta rosso scuro",
         dict(da=(13,), a_=14), None, ["L2_niente_indici_scuri", "L5_tutti_chiari_e_sopra_lo_sfondo",
                                       "L6_contrasto"]),
        ("M2", "rimappa 12 e 13 ma spegne un pixel del glifo",
         dict(da=(12, 13), a_=14, spegni_un_pixel=True), None, ["L3_forma_identica"]),
        ("M3", "rimappa anche i tile non usati e schiarisce la voce 124 della palette",
         dict(da=(12, 13), a_=14, anche_tile_non_usati=True), (124, 0x7FFF),
         ["L4_membri_intoccabili"]),
    ]
    for nome, descr, kw, pal, attesi in ricette:
        p = os.path.join(a.lavoro, nome + ".nds")
        shutil.copy2(a.rom_prima, p)
        rimappa(p, **kw)
        if pal:
            tocca_palette(p, *pal)
        rc, det = rilettore(p, a.rom_prima)
        rossi = [k for k, v in det.get("cancelli", {}).items() if not v]
        ucciso = (rc != 0) and any(x in rossi for x in attesi)
        esiti[nome] = {"descrizione": descr, "uscita_rilettore": rc,
                       "cancelli_rossi": rossi, "cancelli_attesi_rossi": attesi,
                       "ucciso": ucciso}
        print(f"{nome}: ucciso={ucciso} rossi={rossi}")

    rc, det = rilettore(a.rom, a.rom_prima)
    esiti["controprova_rom_corretta"] = {"uscita_rilettore": rc,
                                         "tutti_verdi": det.get("tutti_verdi")}
    print("controprova ROM corretta: verde =", det.get("tutti_verdi"))
    rc0, det0 = rilettore(a.rom_prima, a.rom_prima)
    esiti["controprova_rom_non_corretta"] = {"uscita_rilettore": rc0,
                                             "cancelli_rossi": [k for k, v in det0.get("cancelli", {}).items() if not v]}
    print("controprova ROM NON corretta: rossi =", esiti["controprova_rom_non_corretta"]["cancelli_rossi"])

    tutti = (all(v["ucciso"] for k, v in esiti.items() if k.startswith("M"))
             and esiti["controprova_rom_corretta"]["tutti_verdi"] is True
             and rc0 != 0)
    esiti["tutti_uccisi"] = tutti
    testo = json.dumps(esiti, indent=1, ensure_ascii=False)
    if a.json:
        open(a.json, "w", encoding="utf-8").write(testo + "\n")
    return 0 if tutti else 1


if __name__ == "__main__":
    sys.exit(main())
