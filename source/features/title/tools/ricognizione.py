#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SGP-1.2-TITOLO-01 — ricognizione della schermata del titolo.

Confronta membro per membro il NARC `a/0/4/6` (`demo/title/titledemo.narc`) fra
due ROM — tipicamente la 1.04 (titolo originale HeartGold) e la 1.2 di lavoro —
per far vedere quali membri la 1.1 ha riscritto per mettere il logo «SACRED
GOLD +» e il credito «A FAN»; poi disegna i tre livelli BG dello schermo alto in
PNG, e stampa la differenza cella per cella delle tilemap.

Corrispondenze prese da pret/pokeheartgold, `src/title_screen.c`
(`TitleScreenAnim_Load2dBgGfx`) e `filesystem.mk` (`titledemo.narc -> a/0/4/6`):

  SUB_3  sfondo        NCGR 34 + NSCR 35            (la corona di luce)
  SUB_2  logo          NCGR  3 + NSCR  0 + NCLR  4  (logo + «Developed by a fan»)
  SUB_1  credito       NCGR 15 + NSCR 17            («Developed by … A FAN»)
  MAIN                 Ho-Oh 3D + finestra «Tocca per iniziare» — NON si tocca

Durante il titolo `gSystem.screensFlipped = TRUE`: i livelli SUB stanno sullo
schermo ALTO.

  ricognizione.py --a ROM104 --b ROM12 --uscita DIR
"""
import argparse
import collections
import hashlib
import json
import os
import struct
import sys

from ndspy.rom import NintendoDSRom
from ndspy import narc

LIVELLI = {"SUB3-sfondo": (34, 35), "SUB2-logo": (3, 0), "SUB1-credito": (15, 17)}
NCLR = 4


def _sez(d):
    hs, ns = struct.unpack_from("<HH", d, 12)
    out, o = {}, hs
    for _ in range(ns):
        m = bytes(d[o:o + 4])
        sz = struct.unpack_from("<I", d, o + 4)[0]
        out[m] = (o, sz)
        o += sz
    return out


def nscr(d):
    o, sz = _sez(d)[b"NRCS"]
    w, h = struct.unpack_from("<HH", d, o + 8)
    ds = struct.unpack_from("<I", d, o + 16)[0]
    st = o + sz - ds
    return w, h, [struct.unpack_from("<H", d, st + i)[0] for i in range(0, ds, 2)], st


def ncgr(d):
    o, sz = _sez(d)[b"RAHC"]
    bd = struct.unpack_from("<I", d, o + 12)[0]
    ds = struct.unpack_from("<I", d, o + 24)[0]
    return (4 if bd == 3 else 8), bytes(d[o + sz - ds:o + sz])


def nclr(d):
    o, sz = _sez(d)[b"TTLP"]
    ds = struct.unpack_from("<I", d, o + 16)[0]
    st = o + sz - ds
    return [struct.unpack_from("<H", d, st + i)[0] for i in range(0, ds, 2)]


def disegna(files, i_gfx, i_scr, i_pal):
    bpp, tiles = ncgr(files[i_gfx])
    w, h, celle, _ = nscr(files[i_scr])
    pal = nclr(files[i_pal])
    buf = bytearray(w * h * 4)
    cw, passo = w // 8, (32 if bpp == 4 else 64)
    for ci, cell in enumerate(celle):
        tx, ty = (ci % cw) * 8, (ci // cw) * 8
        t, hf, vf, pl = cell & 0x3FF, (cell >> 10) & 1, (cell >> 11) & 1, (cell >> 12) & 0xF
        blob = tiles[t * passo:(t + 1) * passo]
        if len(blob) < passo:
            continue
        if bpp == 4:
            px = []
            for b in blob:
                px += [b & 0xF, b >> 4]
        else:
            px = list(blob)
        for y in range(8):
            for x in range(8):
                v = px[(7 - y if vf else y) * 8 + (7 - x if hf else x)]
                if v == 0:
                    continue
                idx = v if bpp == 8 else pl * 16 + v
                if idx >= len(pal):
                    continue
                c = pal[idx]
                o = ((ty + y) * w + (tx + x)) * 4
                buf[o], buf[o + 1], buf[o + 2], buf[o + 3] = (
                    (c & 31) * 255 // 31, ((c >> 5) & 31) * 255 // 31,
                    ((c >> 10) & 31) * 255 // 31, 255)
    return w, h, bytes(buf)


def png(path, w, h, rgba):
    import zlib
    g = bytearray()
    for y in range(h):
        g.append(0)
        g += rgba[y * w * 4:(y + 1) * w * 4]

    def bl(t, d):
        c = struct.pack(">I", len(d)) + t + d
        return c + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)

    with open(path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n")
        f.write(bl(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0)))
        f.write(bl(b"IDAT", zlib.compress(bytes(g), 9)))
        f.write(bl(b"IEND", b""))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--a", required=True, help="ROM di confronto (di norma la 1.04)")
    ap.add_argument("--b", required=True, help="ROM in esame (di norma la 1.2 di lavoro)")
    ap.add_argument("--uscita", required=True)
    a = ap.parse_args()
    os.makedirs(a.uscita, exist_ok=True)

    fa = [bytes(x) for x in narc.NARC(NintendoDSRom.fromFile(a.a).getFileByName("a/0/4/6")).files]
    fb = [bytes(x) for x in narc.NARC(NintendoDSRom.fromFile(a.b).getFileByName("a/0/4/6")).files]
    r = {"rom_a": os.path.abspath(a.a), "rom_b": os.path.abspath(a.b),
         "membri": [], "membri_cambiati": [], "tilemap": {}}
    for i in range(max(len(fa), len(fb))):
        x = fa[i] if i < len(fa) else b""
        y = fb[i] if i < len(fb) else b""
        v = {"i": i, "magic": x[:4].decode("ascii", "replace"),
             "len_a": len(x), "len_b": len(y),
             "sha_a": hashlib.sha256(x).hexdigest()[:16],
             "sha_b": hashlib.sha256(y).hexdigest()[:16]}
        r["membri"].append(v)
        if x != y:
            r["membri_cambiati"].append(i)

    for nome, (i_gfx, i_scr) in LIVELLI.items():
        wa, ha, ca, _ = nscr(fa[i_scr])
        wb, hb, cb, off = nscr(fb[i_scr])
        cw = wb // 8
        righe = {}
        for rr in range(len(cb) // cw):
            da = ca[rr * cw:(rr + 1) * cw]
            db = cb[rr * cw:(rr + 1) * cw]
            if da != db:
                col = [c for c in range(cw) if da[c] != db[c]]
                righe[str(rr)] = {"colonne": col,
                                  "a": [f"{da[c]:04X}" for c in col],
                                  "b": [f"{db[c]:04X}" for c in col]}
        uso = collections.Counter(c & 0x3FF for c in cb)
        r["tilemap"][nome] = {"membro_nscr": i_scr, "membro_ncgr": i_gfx,
                              "dimensione": [wb, hb], "larghezza_celle": cw,
                              "offset_dati_nel_membro": off,
                              "righe_diverse": righe,
                              "celle_vuote": uso.get(0, 0)}
        for tag, files in (("a", fa), ("b", fb)):
            try:
                w, h, rgba = disegna(files, i_gfx, i_scr, NCLR)
                png(os.path.join(a.uscita, f"{nome}-{tag}.png"), w, h, rgba)
            except Exception as e:  # pragma: no cover
                r["tilemap"][nome][f"disegno_{tag}"] = "errore: " + str(e)

    open(os.path.join(a.uscita, "ricognizione.json"), "w", encoding="utf-8").write(
        json.dumps(r, indent=1, ensure_ascii=False) + "\n")
    print("membri cambiati:", r["membri_cambiati"])
    for nome in LIVELLI:
        print(nome, "righe diverse:", sorted(r["tilemap"][nome]["righe_diverse"], key=int))
    return 0


if __name__ == "__main__":
    sys.exit(main())
