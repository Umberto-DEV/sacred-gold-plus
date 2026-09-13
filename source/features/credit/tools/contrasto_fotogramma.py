#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SGP-1.2-TITOLO-02 — contrasto misurato sui FOTOGRAMMI VERI dell'emulatore.

Non sui disegni ricavati dai tile: sui PPM catturati da `hg_runtime-gdb`. La
maschera del testo (quali pixel appartengono ai glifi del credito) viene dal
livello SUB_1 ridisegnato dalla ROM; lo sfondo di confronto è, per ogni pixel di
testo, la mediana dei pixel NON di testo della stessa riga entro ±5 px.

Produce anche il ritaglio della zona del credito, a 1× e ingrandito, dai due
fotogrammi.

  contrasto_fotogramma.py --rom ROM --prima A.ppm --dopo B.ppm --png DIR
                          --nome EN [--json FILE]
"""
import argparse
import json
import os
import statistics
import struct
import sys
import zlib

QUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, QUI)
from rileggi_credito import scena, lum, wcag  # noqa: E402

X0, X1, Y0, Y1 = 144, 256, 168, 192     # ritaglio mostrato
YT0, YT1 = 176, 192                     # righe della tilemap del credito


def leggi_ppm(p):
    d = open(p, "rb").read()
    campi, i = [], 0
    while len(campi) < 4:
        while d[i:i + 1].isspace():
            i += 1
        if d[i:i + 1] == b"#":
            while d[i:i + 1] != b"\n":
                i += 1
            continue
        j = i
        while not d[j:j + 1].isspace():
            j += 1
        campi.append(d[i:j])
        i = j
    i += 1
    w, h = int(campi[1]), int(campi[2])
    return w, h, d[i:i + w * h * 3]


def png(path, w, h, rgb, zoom=1):
    if zoom > 1:
        nb = bytearray()
        for y in range(h):
            riga = bytearray()
            for x in range(w):
                riga += rgb[(y * w + x) * 3:(y * w + x) * 3 + 3] * zoom
            nb += riga * zoom
        rgb, w, h = bytes(nb), w * zoom, h * zoom
    g = bytearray()
    for y in range(h):
        g.append(0)
        g += rgb[y * w * 3:(y + 1) * w * 3]

    def bl(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)

    with open(path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n")
        f.write(bl(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)))
        f.write(bl(b"IDAT", zlib.compress(bytes(g), 9)))
        f.write(bl(b"IEND", b""))


def ritaglia(w, h, d, x0, y0, x1, y1):
    out = bytearray()
    for y in range(y0, y1):
        out += d[(y * w + x0) * 3:(y * w + x1) * 3]
    return bytes(out)


def misura(w, h, d, maschera):
    lt, wc, piu = [], [], 0
    for y in range(YT0, YT1):
        riga_testo = [x for x in range(X0, X1) if maschera[y][x]]
        if not riga_testo:
            continue
        fondo = [d[(y * w + x) * 3:(y * w + x) * 3 + 3] for x in range(X0, X1)
                 if not maschera[y][x]]
        for x in riga_testo:
            c = tuple(d[(y * w + x) * 3:(y * w + x) * 3 + 3])
            vicini = [tuple(d[(y * w + u) * 3:(y * w + u) * 3 + 3])
                      for u in range(max(X0, x - 5), min(X1, x + 6)) if not maschera[y][u]]
            base = vicini or fondo
            cs = (int(statistics.median(p[0] for p in base)),
                  int(statistics.median(p[1] for p in base)),
                  int(statistics.median(p[2] for p in base)))
            lt.append(lum(c))
            wc.append(wcag(c, cs))
            piu += 1 if lum(c) > lum(cs) else 0
    n = len(lt)
    return {"pixel_testo": n, "lum_testo_media": round(sum(lt) / n, 1),
            "lum_testo_min": round(min(lt), 1),
            "frazione_piu_chiari_dello_sfondo": round(piu / n, 3),
            "wcag_medio": round(sum(wc) / n, 2), "wcag_min": round(min(wc), 2)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rom", required=True, help="ROM con il credito (per la maschera del testo)")
    ap.add_argument("--prima", required=True)
    ap.add_argument("--dopo", required=True)
    ap.add_argument("--png")
    ap.add_argument("--nome", default="")
    ap.add_argument("--json")
    a = ap.parse_args()

    _files, _pal, liv = scena(a.rom)
    _w, _h, maschera = liv["SUB1"]
    masc = [[1 if maschera[y][x] else 0 for x in range(256)] for y in range(192)]

    r = {}
    for tag, p in (("prima", a.prima), ("dopo", a.dopo)):
        w, h, d = leggi_ppm(p)
        r[tag] = misura(w, h, d, masc)
        if a.png:
            os.makedirs(a.png, exist_ok=True)
            rit = ritaglia(w, h, d, X0, Y0, X1, Y1)
            nome = (a.nome + "-" if a.nome else "") + "credito-" + tag
            png(os.path.join(a.png, nome + "-1x.png"), X1 - X0, Y1 - Y0, rit)
            png(os.path.join(a.png, nome + "-6x.png"), X1 - X0, Y1 - Y0, rit, zoom=6)
    if a.png:
        # un solo PNG: PRIMA sopra, DOPO sotto, ingrandito 6×
        rit = []
        for p in (a.prima, a.dopo):
            w, h, d = leggi_ppm(p)
            rit.append(ritaglia(w, h, d, X0, Y0, X1, Y1))
        ww, hh = X1 - X0, Y1 - Y0
        sep = bytes([40, 40, 40]) * ww * 2
        insieme = rit[0] + sep + rit[1]
        nome = (a.nome + "-" if a.nome else "") + "credito-prima-sopra-dopo-sotto-6x.png"
        png(os.path.join(a.png, nome), ww, hh * 2 + 2, insieme, zoom=6)
    r["miglioramento_lum"] = round(r["dopo"]["lum_testo_media"] - r["prima"]["lum_testo_media"], 1)
    r["miglioramento_wcag"] = round(r["dopo"]["wcag_medio"] - r["prima"]["wcag_medio"], 2)
    testo = json.dumps(r, indent=1, ensure_ascii=False)
    if a.json:
        open(a.json, "w", encoding="utf-8").write(testo + "\n")
    print(testo)
    return 0


if __name__ == "__main__":
    sys.exit(main())
