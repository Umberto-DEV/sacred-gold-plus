#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SGP-1.2-RIFINITURA-01 — fotogrammi: PPM (256x384 di hg_runtime) -> PNG, a 1x.

Nessuna dipendenza esterna (zlib e struct della libreria standard). Serve a
guardare i fotogrammi **alla dimensione vera** (1x), che e' il metro chiesto dal
mandato: l'ingrandimento 3x usato dalle revisioni precedenti nasconde i difetti
di contrasto e ne inventa altri.

  png      SRC.ppm DST.png [alto|basso|intero]
  affianca DST.png SRC.ppm[:alto|basso] ...        (1x, separatore di 2 px)
  zoom     SRC.ppm DST.png N [alto|basso|intero]   (solo per la lettura umana)
  palette  SRC.ppm [alto|basso|intero]             (istogramma dei colori)
  riga     SRC.ppm Y [alto|basso]                  (i colori di una riga)
"""
import struct
import sys
import zlib

W_SEP = 2
SEP = (96, 96, 96)


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
    return w, h, bytearray(d[i:i + w * h * 3])


def ritaglia(w, h, px, quale):
    if quale == "intero":
        return w, h, px
    meta = h // 2
    if quale == "alto":
        return w, meta, px[:w * meta * 3]
    if quale == "basso":
        return w, meta, px[w * meta * 3:]
    raise SystemExit("quale = alto|basso|intero")


def scrivi_png(p, w, h, px):
    grezzo = bytearray()
    for y in range(h):
        grezzo.append(0)
        grezzo += px[y * w * 3:(y + 1) * w * 3]

    def blocco(tipo, dati):
        c = struct.pack(">I", len(dati)) + tipo + dati
        return c + struct.pack(">I", zlib.crc32(tipo + dati) & 0xFFFFFFFF)

    with open(p, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n")
        f.write(blocco(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)))
        f.write(blocco(b"IDAT", zlib.compress(bytes(grezzo), 9)))
        f.write(blocco(b"IEND", b""))


def carica(spec):
    if ":" in spec:
        p, quale = spec.rsplit(":", 1)
    else:
        p, quale = spec, "intero"
    w, h, px = leggi_ppm(p)
    return ritaglia(w, h, px, quale)


def affianca(dst, spec):
    img = [carica(s) for s in spec]
    H = max(h for _, h, _ in img)
    Wt = sum(w for w, _, _ in img) + W_SEP * (len(img) - 1)
    out = bytearray(b"\x00" * (Wt * H * 3))
    x0 = 0
    for k, (w, h, px) in enumerate(img):
        for y in range(h):
            s = y * w * 3
            d = (y * Wt + x0) * 3
            out[d:d + w * 3] = px[s:s + w * 3]
        x0 += w
        if k != len(img) - 1:
            for y in range(H):
                for x in range(W_SEP):
                    d = (y * Wt + x0 + x) * 3
                    out[d:d + 3] = bytes(SEP)
            x0 += W_SEP
    scrivi_png(dst, Wt, H, out)


def zoom(w, h, px, n):
    out = bytearray(b"\x00" * (w * n * h * n * 3))
    for y in range(h):
        for x in range(w):
            c = px[(y * w + x) * 3:(y * w + x) * 3 + 3]
            for dy in range(n):
                for dx in range(n):
                    d = ((y * n + dy) * w * n + x * n + dx) * 3
                    out[d:d + 3] = c
    return w * n, h * n, out


def main():
    a = sys.argv[1:]
    if not a:
        raise SystemExit(__doc__)
    cmd = a[0]
    if cmd == "png":
        w, h, px = leggi_ppm(a[1])
        w, h, px = ritaglia(w, h, px, a[3] if len(a) > 3 else "intero")
        scrivi_png(a[2], w, h, px)
    elif cmd == "affianca":
        affianca(a[1], a[2:])
    elif cmd == "zoom":
        w, h, px = leggi_ppm(a[1])
        w, h, px = ritaglia(w, h, px, a[4] if len(a) > 4 else "intero")
        w, h, px = zoom(w, h, px, int(a[3]))
        scrivi_png(a[2], w, h, px)
    elif cmd == "palette":
        w, h, px = leggi_ppm(a[1])
        w, h, px = ritaglia(w, h, px, a[2] if len(a) > 2 else "intero")
        c = {}
        for i in range(0, len(px), 3):
            k = tuple(px[i:i + 3])
            c[k] = c.get(k, 0) + 1
        for k, v in sorted(c.items(), key=lambda t: -t[1])[:24]:
            print("#%02X%02X%02X  %6d  %5.2f%%" % (k[0], k[1], k[2], v, 100.0 * v / (w * h)))
    elif cmd == "riga":
        w, h, px = leggi_ppm(a[1])
        w, h, px = ritaglia(w, h, px, a[3] if len(a) > 3 else "intero")
        y = int(a[2])
        run, prec = 0, None
        for x in range(w):
            k = tuple(px[(y * w + x) * 3:(y * w + x) * 3 + 3])
            if k != prec:
                if prec is not None:
                    print("x=%3d..%3d  #%02X%02X%02X" % (x - run, x - 1, *prec))
                prec, run = k, 1
            else:
                run += 1
        print("x=%3d..%3d  #%02X%02X%02X" % (w - run, w - 1, *prec))
    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    main()
