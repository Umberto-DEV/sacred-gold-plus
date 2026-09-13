#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SGP-1.2-TITOLO-01 — confronto pixel fra due fotogrammi di `hg_runtime`.

I PPM del banco sono 256×384 (i due schermi impilati). Il confronto dice
quanti pixel cambiano, dentro quale rettangolo cadono, e se fuori da quel
rettangolo i due fotogrammi sono identici byte per byte. Converte anche in PNG
a 1× (niente ingrandimento: si guarda la dimensione vera).

  confronta.py prima.ppm dopo.ppm --png DIR --nome EN [--json FILE]
"""
import argparse
import json
import os
import struct
import sys
import zlib


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


def png(path, w, h, rgb):
    grezzo = bytearray()
    for y in range(h):
        grezzo.append(0)
        grezzo += rgb[y * w * 3:(y + 1) * w * 3]

    def blocco(t, d):
        c = struct.pack(">I", len(d)) + t + d
        return c + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)

    with open(path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n")
        f.write(blocco(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)))
        f.write(blocco(b"IDAT", zlib.compress(bytes(grezzo), 9)))
        f.write(blocco(b"IEND", b""))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("prima")
    ap.add_argument("dopo")
    ap.add_argument("--png")
    ap.add_argument("--nome", default="fotogramma")
    ap.add_argument("--json")
    a = ap.parse_args()

    w1, h1, a1 = leggi_ppm(a.prima)
    w2, h2, a2 = leggi_ppm(a.dopo)
    r = {"nome": a.nome, "dimensioni": [w1, h1], "stesse_dimensioni": (w1, h1) == (w2, h2)}
    if not r["stesse_dimensioni"]:
        print(json.dumps(r))
        return 1

    diversi = []
    for y in range(h1):
        b = y * w1 * 3
        if a1[b:b + w1 * 3] == a2[b:b + w1 * 3]:
            continue
        for x in range(w1):
            o = b + x * 3
            if a1[o:o + 3] != a2[o:o + 3]:
                diversi.append((x, y))
    r["pixel_diversi"] = len(diversi)
    if diversi:
        xs = [p[0] for p in diversi]
        ys = [p[1] for p in diversi]
        r["rettangolo"] = {"x0": min(xs), "x1": max(xs), "y0": min(ys), "y1": max(ys),
                           "larghezza": max(xs) - min(xs) + 1, "altezza": max(ys) - min(ys) + 1}
        r["schermo"] = "alto" if max(ys) < h1 // 2 else ("basso" if min(ys) >= h1 // 2 else "ENTRAMBI")
        # fuori dal rettangolo: identici?
        x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
        fuori = 0
        for (x, y) in diversi:
            if not (x0 <= x <= x1 and y0 <= y <= y1):
                fuori += 1
        r["pixel_diversi_fuori_dal_rettangolo"] = fuori
    else:
        r["rettangolo"] = None
        r["schermo"] = None
        r["pixel_diversi_fuori_dal_rettangolo"] = 0

    # identità fuori dalla banda di righe toccate
    if diversi:
        y0, y1 = r["rettangolo"]["y0"], r["rettangolo"]["y1"]
        sopra_ok = a1[:y0 * w1 * 3] == a2[:y0 * w1 * 3]
        sotto_ok = a1[(y1 + 1) * w1 * 3:] == a2[(y1 + 1) * w1 * 3:]
        r["resto_identico"] = bool(sopra_ok and sotto_ok)
        meta = h1 // 2
        r["schermo_basso_identico"] = bool(a1[meta * w1 * 3:] == a2[meta * w1 * 3:])
    else:
        r["resto_identico"] = True
        r["schermo_basso_identico"] = True

    if a.png:
        os.makedirs(a.png, exist_ok=True)
        meta = h1 // 2
        png(os.path.join(a.png, a.nome + "-prima-alto.png"), w1, meta, a1[:meta * w1 * 3])
        png(os.path.join(a.png, a.nome + "-dopo-alto.png"), w1, meta, a2[:meta * w1 * 3])
        png(os.path.join(a.png, a.nome + "-prima-intero.png"), w1, h1, a1)
        png(os.path.join(a.png, a.nome + "-dopo-intero.png"), w1, h1, a2)
        # mappa delle differenze: rosso dove cambia, grigio dove no
        d = bytearray()
        for y in range(h1):
            for x in range(w1):
                o = (y * w1 + x) * 3
                if a1[o:o + 3] != a2[o:o + 3]:
                    d += b"\xff\x00\x00"
                else:
                    v = (a1[o] + a1[o + 1] + a1[o + 2]) // 6
                    d += bytes((v, v, v))
        png(os.path.join(a.png, a.nome + "-differenze.png"), w1, h1, bytes(d))

    testo = json.dumps(r, indent=1, ensure_ascii=False)
    if a.json:
        open(a.json, "w", encoding="utf-8").write(testo + "\n")
    print(testo)
    return 0


if __name__ == "__main__":
    sys.exit(main())
