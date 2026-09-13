#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MUTANTI — SGP-1.2-ANIM-SOLIDO-01.

Un cancello verde su una cosa giusta non prova niente finché non si è visto
diventare rosso su una cosa sbagliata. Qui si costruiscono **dieci** varianti,
ciascuna con **un solo** guasto, e si pretende che almeno un cancello muoia.

| # | guasto | dove | chi dovrebbe ucciderlo |
|---|---|---|---|
| 1 | letterale G1 azzerato nell'INGRESSO | ingresso | applicatore A0/A1 (guardia) |
| 2 | sito G2 già occupato nell'INGRESSO | ingresso | applicatore S2 |
| 3 | blob spostato di 4 B nel blocco | uscita | rilettore L2 |
| 4 | letterale G1 senza bit Thumb | uscita | rilettore L1 |
| 5 | `BL` di G2 spostata di 4 B | uscita | rilettore L1b |
| 6 | coda della trampolina alterata (`movs r1,#4` → `#5`) | uscita | rilettore L1c |
| 7 | canarino alterato | uscita | rilettore L3 |
| 8 | **un byte della tavola `tab_u`** | uscita | rilettore **L9** (il buco che `SGP-1.2-RIFINITURA-01` aveva lasciato aperto) |
| 9 | letterale della priorità (0x3F2) alterato | uscita | rilettore L6 |
| 10 | voce intrusa nella mappa della riserva | manifesto | applicatore A4 |

Uso:
  mutanti4.py --base ROM --build DIR --manifest MAPPA.json --applicato ROM
              --tmp DIR [--json F]
rc 0 se TUTTI sono uccisi.
GPL-3.0-or-later.
"""
import argparse
import json
import shutil
import struct
import subprocess
import sys
from pathlib import Path

QUI = Path(__file__).resolve().parent
sys.path.insert(0, str(QUI))
from arm9 import Arm9                    # noqa: E402
import overlay_patch as ovp              # noqa: E402

BLOCK_BASE = 0x023D8B00
OFF_CANARINO, OFF_TABELLE = 0x2F0, 0x300
A_G1, A_G2, A_PRIO = 0x0226200C, 0x02262032, 0x02262010
OV = 12


def applicatore(args):
    return [sys.executable, str(QUI / "applica_anim4.py")] + args


def rilettore(args):
    return [sys.executable, str(QUI / "rileggi_anim4.py")] + args


def scrivi_overlay(src, dst, patch):
    dati = Path(src).read_bytes()
    v, _crudo, img = ovp.Rom(dati).immagine_overlay(OV)
    pre = []
    for addr, nuovo in patch:
        off = addr - v["ram"]
        pre.append({"addr": addr, "pre": bytes(img[off:off + len(nuovo)]),
                    "post": bytes(nuovo)})
    fuori, _r = ovp.applica(dati, OV, [(A_PRIO, bytes(img[A_PRIO - v["ram"]:
                                                          A_PRIO - v["ram"] + 4]))],
                            pre, strategia="auto")
    Path(dst).write_bytes(fuori)


def scrivi_arm9(src, dst, indirizzo, dati):
    shutil.copyfile(src, dst)
    r = Arm9(dst)
    r.scrivi(indirizzo, bytes(dati))
    r.salva(dst)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True)
    ap.add_argument("--build", required=True)
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--applicato", required=True)
    ap.add_argument("--tmp", required=True)
    ap.add_argument("--json")
    a = ap.parse_args()
    tmp = Path(a.tmp)
    tmp.mkdir(parents=True, exist_ok=True)
    man = json.loads((Path(a.build) / "manifesto.json").read_text())
    esiti = []

    def prova(n, descrizione, cmd, atteso_rosso=True):
        r = subprocess.run(cmd, capture_output=True, text=True)
        morto = r.returncode != 0
        esiti.append({"mutante": n, "guasto": descrizione, "rc": r.returncode,
                      "ucciso": morto,
                      "messaggio": (r.stdout + r.stderr).strip().splitlines()[-1][:200]
                      if (r.stdout + r.stderr).strip() else ""})
        print("  M%-3d %-58s %s" % (n, descrizione,
                                    "UCCISO" if morto else "**SOPRAVVISSUTO**"))
        return morto

    # ---- 1: letterale G1 azzerato nell'ingresso ---------------------------
    m1 = tmp / "m1.nds"
    scrivi_overlay(a.base, m1, [(A_G1, b"\x00\x00\x00\x00")])
    prova(1, "G1 azzerato nell'ingresso",
          applicatore(["--base", str(m1), "--out", str(tmp / "o1.nds"),
                       "--build", a.build, "--sostituisci", "--niente-registro"]))

    # ---- 2: sito G2 gia' occupato nell'ingresso ---------------------------
    m2 = tmp / "m2.nds"
    scrivi_overlay(a.base, m2, [(A_G2, b"\x00\xbf\x00\xbf")])
    prova(2, "sito G2 gia' occupato nell'ingresso",
          applicatore(["--base", str(m2), "--out", str(tmp / "o2.nds"),
                       "--build", a.build, "--sostituisci", "--niente-registro"]))

    # ---- 3..9: guasti nell'USCITA, il rilettore deve vederli ---------------
    blob = (Path(a.build) / "blob.bin").read_bytes()
    canarino = (Path(a.build) / "canarino.bin").read_bytes()
    tab = (Path(a.build) / "tab_u.bin").read_bytes()

    m3 = tmp / "m3.nds"
    scrivi_arm9(a.applicato, m3, BLOCK_BASE, b"\x00\x00\x00\x00" + blob[:len(blob) - 4])
    prova(3, "blob spostato di 4 B nel blocco",
          rilettore([a.base, str(m3), "--build", a.build]))

    m4 = tmp / "m4.nds"
    g1 = int(man["simboli"]["sgp_idle_task2"], 16) & ~1
    scrivi_overlay(a.applicato, m4, [(A_G1, struct.pack("<I", g1))])
    prova(4, "letterale G1 senza bit Thumb",
          rilettore([a.base, str(m4), "--build", a.build]))

    m5 = tmp / "m5.nds"
    dati = Path(a.applicato).read_bytes()
    v, _c, img = ovp.Rom(dati).immagine_overlay(OV)
    bl = bytes(img[A_G2 - v["ram"]:A_G2 - v["ram"] + 4])
    hi, lo = struct.unpack("<HH", bl)
    scrivi_overlay(a.applicato, m5, [(A_G2, struct.pack("<HH", hi, (lo + 2) & 0xFFFF))])
    prova(5, "BL di G2 spostata di 4 B",
          rilettore([a.base, str(m5), "--build", a.build]))

    m6 = tmp / "m6.nds"
    tr = (int(man["simboli"]["sgp_idle_stop"], 16) & ~1) - BLOCK_BASE
    guasto = bytearray(blob)
    # nella coda della trampolina, `movs r1,#4` (0x2104) -> `movs r1,#5` (0x2105)
    i = guasto.index(b"\x20\x6a\x04\x21\x00\x22\x10\xbd", tr)
    guasto[i + 2] = 0x05
    scrivi_arm9(a.applicato, m6, BLOCK_BASE, bytes(guasto))
    prova(6, "coda della trampolina alterata (movs r1,#4 -> #5)",
          rilettore([a.base, str(m6), "--build", a.build]))

    m7 = tmp / "m7.nds"
    scrivi_arm9(a.applicato, m7, BLOCK_BASE + OFF_CANARINO,
                bytes([canarino[0] ^ 1]) + canarino[1:])
    prova(7, "canarino alterato di un bit",
          rilettore([a.base, str(m7), "--build", a.build]))

    m8 = tmp / "m8.nds"
    scrivi_arm9(a.applicato, m8, BLOCK_BASE + OFF_TABELLE,
                bytes([tab[0], tab[1] + 1]) + tab[2:])
    prova(8, "un byte della tavola tab_u",
          rilettore([a.base, str(m8), "--build", a.build]))

    m9 = tmp / "m9.nds"
    scrivi_overlay(a.applicato, m9, [(A_PRIO, b"\xf1\x03\x00\x00")])
    prova(9, "letterale della priorita' del task alterato",
          rilettore([a.base, str(m9), "--build", a.build]))

    # ---- 10: voce intrusa nella mappa della riserva ------------------------
    mappa = json.loads(Path(a.manifest).read_text())
    mappa["blocchi"].append({"nome": "intruso.test", "base": hex(BLOCK_BASE + 0x10),
                             "bytes": 16, "zona": "1.2"})
    m10 = tmp / "mappa-intrusa.json"
    m10.write_text(json.dumps(mappa, indent=2))
    prova(10, "voce intrusa nella mappa della riserva",
          applicatore(["--base", a.base, "--out", str(tmp / "o10.nds"),
                       "--build", a.build, "--manifest", str(m10),
                       "--sostituisci", "--niente-registro"]))

    vivi = [e for e in esiti if not e["ucciso"]]
    fuori = {"totali": len(esiti), "uccisi": len(esiti) - len(vivi),
             "sopravvissuti": [e["mutante"] for e in vivi], "dettaglio": esiti}
    print("\n%d/%d mutanti uccisi" % (fuori["uccisi"], fuori["totali"]))
    if a.json:
        Path(a.json).write_text(json.dumps(fuori, indent=2, ensure_ascii=False) + "\n")
    return 0 if not vivi else 1


if __name__ == "__main__":
    sys.exit(main())
