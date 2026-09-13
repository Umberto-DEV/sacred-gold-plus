#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SGP-1.2-TITOLO-01 — i tre mutanti di `CRITERI.md` §4.

Ognuno è una modifica PLAUSIBILE ma SBAGLIATA della schermata del titolo. Il
rilettore indipendente deve dichiararli rossi. Se un mutante passa, il rilettore
non sta guardando quello che dice di guardare.

  M1  azzera 27 celle su 28 (dimentica l'ultima)      -> deve cadere su L2
  M2  azzera anche 3 celle della coda del logo        -> deve cadere su L3/L7
  M3  azzera il credito in basso a destra (membro 17) -> deve cadere su L4/L5
      lasciando in piedi la scritta sotto il logo

Lavora sempre su copie in una cartella di lavoro; non tocca l'originale.

  mutanti.py --rom ROM --lavoro DIR [--json FILE]
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
import applica_titolo as A       # noqa: E402  (solo per posizione_membro/offset)

LARG = 32


def _offset_celle_membro(f, membro, celle):
    """Offset assoluti nel file delle celle (riga, colonna) del membro NSCR dato."""
    off, lun, _ = A.posizione_membro(f, membro)
    f.seek(off)
    d = f.read(lun)
    nrcs_off, nrcs_size = A.sezioni_narc_nscr(d)
    ds = struct.unpack_from("<I", d, nrcs_off + 16)[0]
    st = nrcs_off + nrcs_size - ds
    return [off + st + 2 * (r * LARG + c) for (r, c) in celle]


def scrivi(path, membro, celle, valore=0x0000):
    with open(path, "r+b") as f:
        for o in _offset_celle_membro(f, membro, celle):
            f.seek(o)
            f.write(struct.pack("<H", valore))


def rilettore(rom):
    r = subprocess.run([sys.executable, os.path.join(QUI, "rileggi_titolo.py"),
                        "--rom", rom, "--json", "-"], capture_output=True, text=True)
    try:
        return r.returncode, json.loads(r.stdout)
    except Exception:
        return 2, {"errore": (r.stdout + r.stderr)[-400:]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rom", required=True, help="ROM GIA' corretta (uscita dell'applicatore)")
    ap.add_argument("--rom-prima", required=True, help="ROM 1.2 non ancora corretta")
    ap.add_argument("--lavoro", required=True)
    ap.add_argument("--json")
    a = ap.parse_args()
    os.makedirs(a.lavoro, exist_ok=True)

    bers = [(r, c) for r in (22, 23) for c in range(9, 23)]
    ricette = [
        ("M1", "27 celle su 28: resta l'ultima lettera", a.rom_prima, 0, bers[:-1], ["L2_bersaglio_azzerato"]),
        ("M2", "28 celle + 3 celle della coda del logo (riga 20, col 24-26)", a.rom_prima, 0,
         bers + [(20, 24), (20, 25), (20, 26)], ["L3_resto_mappa_intatto", "L7_logo_identico"]),
        ("M3", "azzera il credito in basso a destra e lascia la scritta sotto il logo",
         a.rom_prima, 17, [(r, c) for r in (22, 23) for c in range(19, 32)],
         ["L4_membri_intoccabili", "L5_credito_basso_destra_intatto"]),
    ]

    esiti = {}
    for nome, descr, sorgente, membro, celle, attesi in ricette:
        p = os.path.join(a.lavoro, nome + ".nds")
        shutil.copy2(sorgente, p)
        scrivi(p, membro, celle)
        rc, det = rilettore(p)
        rossi = [k for k, v in det.get("cancelli", {}).items() if not v]
        ucciso = (rc != 0) and any(x in rossi for x in attesi)
        esiti[nome] = {"descrizione": descr, "membro": membro, "n_celle": len(celle),
                       "uscita_rilettore": rc, "cancelli_rossi": rossi,
                       "cancelli_attesi_rossi": attesi, "ucciso": ucciso}
        print(f"{nome}: ucciso={ucciso} rossi={rossi}")

    # controprova: la ROM corretta deve essere VERDE
    rc, det = rilettore(a.rom)
    esiti["controprova_rom_corretta"] = {"uscita_rilettore": rc,
                                         "tutti_verdi": det.get("tutti_verdi")}
    print("controprova ROM corretta: verde =", det.get("tutti_verdi"))

    tutti = all(v["ucciso"] for k, v in esiti.items() if k.startswith("M")) \
        and esiti["controprova_rom_corretta"]["tutti_verdi"] is True
    esiti["tutti_uccisi"] = tutti
    testo = json.dumps(esiti, indent=1, ensure_ascii=False)
    if a.json:
        open(a.json, "w", encoding="utf-8").write(testo + "\n")
    return 0 if tutti else 1


if __name__ == "__main__":
    sys.exit(main())
