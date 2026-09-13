#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SGP-1.2-TITOLO-02 — inventario degli indici di palette del titolo.

Per la ROM data: quali indici assoluti della NCLR (membro 4) sono davvero usati
dai tre livelli BG dello schermo alto del titolo, e quindi quali sono liberi.

  SUB_3 (NCGR 34 + NSCR 35, 4 bpp): indice = banco*16 + valore
  SUB_2 (NCGR  3 + NSCR  0, 8 bpp, palette estesa): indice = valore
  SUB_1 (NCGR 15 + NSCR 17, 4 bpp): indice = banco*16 + valore
"""
import argparse
import collections
import json
import sys

from ndspy.rom import NintendoDSRom
from ndspy import narc

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from ricognizione02 import leggi_ncgr, leggi_nscr, leggi_nclr, rgb, lum, pixel_tile  # noqa: E402


def usi(files, i_gfx, i_scr):
    bpp, tiles, _ = leggi_ncgr(files[i_gfx])
    w, h, celle, _ = leggi_nscr(files[i_scr])
    passo = 32 if bpp == 4 else 64
    c = collections.Counter()
    for cell in celle:
        t = cell & 0x3FF
        pl = (cell >> 12) & 0xF
        blob = tiles[t * passo:(t + 1) * passo]
        if len(blob) < passo:
            continue
        for v in pixel_tile(blob, bpp):
            if v == 0:
                continue
            c[(pl * 16 + v) if bpp == 4 else v] += 1
    return c


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rom", required=True)
    ap.add_argument("--json")
    a = ap.parse_args()
    files = [bytes(x) for x in narc.NARC(NintendoDSRom.fromFile(a.rom).getFileByName("a/0/4/6")).files]
    pal, _ = leggi_nclr(files[4])
    u3 = usi(files, 34, 35)
    u2 = usi(files, 3, 0)
    u1 = usi(files, 15, 17)
    tutti = collections.Counter()
    tutti.update(u3)
    tutti.update(u2)
    tutti.update(u1)
    liberi = [i for i in range(len(pal)) if i % 16 and tutti[i] == 0]
    print("indici usati: SUB3", len(u3), "SUB2", len(u2), "SUB1", len(u1),
          "totale distinti", len(tutti))
    print("liberi (non indice 0 di banco):", len(liberi))
    for b in range(16):
        riga = []
        for j in range(16):
            i = b * 16 + j
            m = "." if tutti[i] == 0 else ("3" if u3[i] else "") + ("2" if u2[i] else "") + ("1" if u1[i] else "")
            riga.append(f"{j:2d}{m:<4s}L{lum(pal[i]):3.0f}")
        print(f"banco {b:2d}: " + " ".join(riga))
    out = {
        "rom": a.rom,
        "usati_sub3": {str(k): v for k, v in sorted(u3.items())},
        "usati_sub2": {str(k): v for k, v in sorted(u2.items())},
        "usati_sub1": {str(k): v for k, v in sorted(u1.items())},
        "liberi": liberi,
        "palette": [{"i": i, "bgr15": f"{pal[i]:04X}", "rgb": rgb(pal[i]),
                     "lum": round(lum(pal[i]), 1), "usi": tutti[i]} for i in range(len(pal))],
    }
    if a.json:
        open(a.json, "w", encoding="utf-8").write(json.dumps(out, indent=1, ensure_ascii=False) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
