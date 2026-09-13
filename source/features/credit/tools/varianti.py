#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SGP-1.2-TITOLO-02 — simulazione fuori ROM delle varianti di colore del credito.

Non scrive nella ROM: ricostruisce in memoria il livello SUB_1 con una diversa
mappatura degli indici di palette e/o un diverso banco, compone SUB_3+SUB_2+SUB_1
nel rettangolo del credito e misura il contrasto (luminanza e rapporto WCAG) fra i
pixel del testo e lo sfondo che sta esattamente sotto ciascuno di essi.

Varianti:
  V0  com'è oggi (1.2)                         banco 7, indici 12/13/14
  V1  solo tilemap: banco 7 -> 15              tile invariati
  V2  banco 7 -> 0 e tile 14->1, 13->2, 12->3  gradiente chiaro «caldo»
  V4  solo tile: 12,13 -> 14                   banco 7 invariato, testo pieno
  VA  riferimento: il credito della 1.04
"""
import argparse
import json
import os
import sys

from ndspy.rom import NintendoDSRom
from ndspy import narc

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ricognizione02 import (leggi_ncgr, leggi_nscr, leggi_nclr, rgb, lum,  # noqa: E402
                            pixel_tile, disegna, png)

RETT = (144, 168, 256, 192)  # x0, y0, x1, y1 — la zona del credito


def lin(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4


def wcag(c1, c2):
    L1 = 0.2126 * lin(c1[0]) + 0.7152 * lin(c1[1]) + 0.0722 * lin(c1[2])
    L2 = 0.2126 * lin(c2[0]) + 0.7152 * lin(c2[1]) + 0.0722 * lin(c2[2])
    a, b = max(L1, L2), min(L1, L2)
    return (a + 0.05) / (b + 0.05)


def credito_idx(files, mappa_tile=None, banco=None):
    """Matrice degli indici assoluti del livello SUB_1 applicando la variante."""
    bpp, tiles, _ = leggi_ncgr(files[15])
    w, h, celle, _ = leggi_nscr(files[17])
    idxm = [[0] * w for _ in range(h)]
    cw = w // 8
    for ci, cell in enumerate(celle):
        t = cell & 0x3FF
        if not t:
            continue
        hf, vf = (cell >> 10) & 1, (cell >> 11) & 1
        pl = banco if banco is not None else (cell >> 12) & 0xF
        px = pixel_tile(tiles[t * 32:(t + 1) * 32], 4)
        tx, ty = (ci % cw) * 8, (ci // cw) * 8
        for y in range(8):
            for x in range(8):
                v = px[(7 - y if vf else y) * 8 + (7 - x if hf else x)]
                if v == 0:
                    continue
                if mappa_tile:
                    v = mappa_tile.get(v, v)
                idxm[ty + y][tx + x] = pl * 16 + v
    return idxm


def fondo(files, pal):
    """RGB dello sfondo (SUB_3 sotto, SUB_2 sopra) per ogni pixel."""
    w3, h3, rgba3, _ = disegna(files, 34, 35, pal)
    w2, h2, rgba2, _ = disegna(files, 3, 0, pal)
    out = [[(0, 0, 0)] * w3 for _ in range(h3)]
    for y in range(h3):
        for x in range(w3):
            c = (0, 0, 0)
            if rgba3[(y * w3 + x) * 4 + 3]:
                c = tuple(rgba3[(y * w3 + x) * 4:(y * w3 + x) * 4 + 3])
            if y < h2 and x < w2 and rgba2[(y * w2 + x) * 4 + 3]:
                c = tuple(rgba2[(y * w2 + x) * 4:(y * w2 + x) * 4 + 3])
            out[y][x] = c
    return out


def misura(idxm, fnd, pal):
    lt, ls, wc = [], [], []
    for y in range(len(idxm)):
        for x in range(len(idxm[0])):
            i = idxm[y][x]
            if not i:
                continue
            ct = rgb(pal[i])
            cs = fnd[y][x]
            lt.append(0.2126 * ct[0] + 0.7152 * ct[1] + 0.0722 * ct[2])
            ls.append(0.2126 * cs[0] + 0.7152 * cs[1] + 0.0722 * cs[2])
            wc.append(wcag(ct, cs))
    n = len(lt)
    return {
        "pixel_testo": n,
        "lum_testo_media": round(sum(lt) / n, 1),
        "lum_sfondo_media": round(sum(ls) / n, 1),
        "delta_lum_medio": round(sum(abs(a - b) for a, b in zip(lt, ls)) / n, 1),
        "wcag_medio": round(sum(wc) / n, 2),
        "wcag_min": round(min(wc), 2),
        "wcag_p10": round(sorted(wc)[n // 10], 2),
        "frazione_wcag_sotto_3": round(sum(1 for v in wc if v < 3.0) / n, 3),
        "frazione_wcag_sotto_4_5": round(sum(1 for v in wc if v < 4.5) / n, 3),
    }


def componi_png(path, idxm, fnd, pal, zoom):
    x0, y0, x1, y1 = RETT
    w, h = x1 - x0, y1 - y0
    buf = bytearray(w * h * 4)
    for y in range(y0, y1):
        for x in range(x0, x1):
            c = rgb(pal[idxm[y][x]]) if idxm[y][x] else fnd[y][x]
            o = ((y - y0) * w + (x - x0)) * 4
            buf[o], buf[o + 1], buf[o + 2], buf[o + 3] = c[0], c[1], c[2], 255
    png(path, w, h, bytes(buf), zoom=zoom)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rom", required=True, help="ROM 1.2 di lavoro (copia)")
    ap.add_argument("--rom104", required=True)
    ap.add_argument("--uscita", required=True)
    a = ap.parse_args()
    os.makedirs(a.uscita, exist_ok=True)

    fb = [bytes(x) for x in narc.NARC(NintendoDSRom.fromFile(a.rom).getFileByName("a/0/4/6")).files]
    fa = [bytes(x) for x in narc.NARC(NintendoDSRom.fromFile(a.rom104).getFileByName("a/0/4/6")).files]
    palb, _ = leggi_nclr(fb[4])
    pala, _ = leggi_nclr(fa[4])
    fndb = fondo(fb, palb)
    fnda = fondo(fa, pala)

    var = {
        "V0-oggi": (None, None),
        "V1-banco15": (None, 15),
        "V2-banco0-gradiente": ({14: 1, 13: 2, 12: 3}, 0),
        "V4-solo-tile-14": ({12: 14, 13: 14}, None),
    }
    out = {}
    for nome, (mt, bk) in var.items():
        idxm = credito_idx(fb, mt, bk)
        out[nome] = misura(idxm, fndb, palb)
        componi_png(os.path.join(a.uscita, f"{nome}-1x.png"), idxm, fndb, palb, 1)
        componi_png(os.path.join(a.uscita, f"{nome}-6x.png"), idxm, fndb, palb, 6)
    idxa = credito_idx(fa)
    out["VA-1.04-originale"] = misura(idxa, fnda, pala)
    componi_png(os.path.join(a.uscita, "VA-1.04-originale-6x.png"), idxa, fnda, pala, 6)

    with open(os.path.join(a.uscita, "varianti.json"), "w", encoding="utf-8") as f:
        f.write(json.dumps(out, indent=1, ensure_ascii=False) + "\n")
    for k, v in out.items():
        print(f"{k:24s} lum testo {v['lum_testo_media']:6.1f} sfondo {v['lum_sfondo_media']:6.1f} "
              f"Δ {v['delta_lum_medio']:6.1f}  WCAG med {v['wcag_medio']:5.2f} min {v['wcag_min']:5.2f} "
              f"p10 {v['wcag_p10']:5.2f}  <3: {v['frazione_wcag_sotto_3']:.0%}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
