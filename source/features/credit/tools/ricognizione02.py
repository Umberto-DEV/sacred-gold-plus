#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SGP-1.2-TITOLO-02 — ricognizione del credito in basso a destra (livello SUB_1).

Confronta, fra la 1.04 (titolo HeartGold originale, credito «Developed by GAME
FREAK inc.») e la 1.2 di lavoro (credito «Developed by  A FAN» rifatto dalla 1.1),
tutto ciò che serve per decidere come renderlo leggibile:

  * NCLR membro 4 — palette del BG SUB (caricata sia a offset 0, sia come palette
    estesa a 0x4000): 256 colori = 16 banchi da 16.
  * NCGR membro 15 (4 bpp) + NSCR membro 17 — il credito, banco palette 7.
  * NCGR membro 3 (8 bpp) + NSCR membro 0 — il logo, palette estesa: serve per
    sapere se gli indici 112…127 (banco 7) sono usati ANCHE dal logo.
  * NCGR 34 + NSCR 35 — lo sfondo (il cielo dietro al credito).

Corrispondenze da pret/pokeheartgold, src/title_screen.c (TitleScreenAnim_Load2dBgGfx):
  SUB_3 = NCGR 34 + NSCR 35 (16 bpp)      sfondo/corona
  SUB_2 = NCGR  3 + NSCR  0 (256 bpp, palette ESTESA a 0x4000, da NCLR 4)   logo
  SUB_1 = NCGR 15 + NSCR 17 (16 bpp, palette standard offset 0, da NCLR 4)  credito
  palette SUB_BG offset 0 e 0x4000: entrambe il NCLR 4.

Uscita: ricognizione02.json + PNG dei livelli e ritagli del credito.
"""
import argparse
import collections
import hashlib
import json
import os
import struct
import sys
import zlib

from ndspy.rom import NintendoDSRom
from ndspy import narc

NCLR_MEMBRO = 4
LIV = {
    "SUB3-sfondo": {"ncgr": 34, "nscr": 35},
    "SUB2-logo": {"ncgr": 3, "nscr": 0},
    "SUB1-credito": {"ncgr": 15, "nscr": 17},
}


def sezioni(d):
    hs, ns = struct.unpack_from("<HH", d, 12)
    out, o = {}, hs
    for _ in range(ns):
        m = bytes(d[o:o + 4])
        sz = struct.unpack_from("<I", d, o + 4)[0]
        out[m] = (o, sz)
        o += sz
    return out


def leggi_nscr(d):
    o, sz = sezioni(d)[b"NRCS"]
    w, h = struct.unpack_from("<HH", d, o + 8)
    ds = struct.unpack_from("<I", d, o + 16)[0]
    st = o + sz - ds
    return w, h, [struct.unpack_from("<H", d, st + i)[0] for i in range(0, ds, 2)], st


def leggi_ncgr(d):
    o, sz = sezioni(d)[b"RAHC"]
    bd = struct.unpack_from("<I", d, o + 12)[0]
    ds = struct.unpack_from("<I", d, o + 24)[0]
    st = o + sz - ds
    return (4 if bd == 3 else 8), bytes(d[st:st + ds]), st


def leggi_nclr(d):
    o, sz = sezioni(d)[b"TTLP"]
    ds = struct.unpack_from("<I", d, o + 16)[0]
    st = o + sz - ds
    return [struct.unpack_from("<H", d, st + i)[0] for i in range(0, ds, 2)], st


def rgb(c):
    return ((c & 31) * 255 // 31, ((c >> 5) & 31) * 255 // 31, ((c >> 10) & 31) * 255 // 31)


def lum(c):
    r, g, b = rgb(c)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def pixel_tile(blob, bpp):
    if bpp == 4:
        px = []
        for b in blob:
            px += [b & 0xF, b >> 4]
        return px
    return list(blob)


def disegna(files, i_gfx, i_scr, pal, forza_8bpp_diretto=True):
    """Ridisegna un livello BG. Ritorna (w, h, rgba, indici) dove `indici` è la
    matrice degli indici di palette (0 = trasparente)."""
    bpp, tiles, _ = leggi_ncgr(files[i_gfx])
    w, h, celle, _ = leggi_nscr(files[i_scr])
    buf = bytearray(w * h * 4)
    idxm = [[0] * w for _ in range(h)]
    cw, passo = w // 8, (32 if bpp == 4 else 64)
    for ci, cell in enumerate(celle):
        tx, ty = (ci % cw) * 8, (ci // cw) * 8
        t = cell & 0x3FF
        hf, vf, pl = (cell >> 10) & 1, (cell >> 11) & 1, (cell >> 12) & 0xF
        blob = tiles[t * passo:(t + 1) * passo]
        if len(blob) < passo:
            continue
        px = pixel_tile(blob, bpp)
        for y in range(8):
            for x in range(8):
                v = px[(7 - y if vf else y) * 8 + (7 - x if hf else x)]
                if v == 0:
                    continue
                idx = v if bpp == 8 else pl * 16 + v
                idxm[ty + y][tx + x] = idx
                if idx >= len(pal):
                    continue
                r, g, b = rgb(pal[idx])
                o = ((ty + y) * w + (tx + x)) * 4
                buf[o], buf[o + 1], buf[o + 2], buf[o + 3] = r, g, b, 255
    return w, h, bytes(buf), idxm


def png(path, w, h, rgba, zoom=1):
    if zoom > 1:
        nb = bytearray()
        for y in range(h):
            riga = bytearray()
            for x in range(w):
                riga += rgba[(y * w + x) * 4:(y * w + x) * 4 + 4] * zoom
            nb += riga * zoom
        rgba, w, h = bytes(nb), w * zoom, h * zoom
    g = bytearray()
    for y in range(h):
        g.append(0)
        g += rgba[y * w * 4:(y + 1) * w * 4]

    def bl(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)

    with open(path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n")
        f.write(bl(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0)))
        f.write(bl(b"IDAT", zlib.compress(bytes(g), 9)))
        f.write(bl(b"IEND", b""))


def componi(files, pal, x0, y0, x1, y1):
    """Compone SUB3 (sotto) + SUB2 + SUB1 (sopra) nel rettangolo dato."""
    strati = []
    for nome in ("SUB3-sfondo", "SUB2-logo", "SUB1-credito"):
        w, h, rgba, idxm = disegna(files, LIV[nome]["ncgr"], LIV[nome]["nscr"], pal)
        strati.append((w, h, rgba, idxm))
    w = x1 - x0
    h = y1 - y0
    out = bytearray(w * h * 4)
    for y in range(y0, y1):
        for x in range(x0, x1):
            col = (0, 0, 0)
            for sw, sh, rgba, _ in strati:
                if y < sh and x < sw and rgba[(y * sw + x) * 4 + 3]:
                    col = tuple(rgba[(y * sw + x) * 4:(y * sw + x) * 4 + 3])
            o = ((y - y0) * w + (x - x0)) * 4
            out[o], out[o + 1], out[o + 2], out[o + 3] = col[0], col[1], col[2], 255
    return w, h, bytes(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--a", required=True, help="ROM 1.04 (titolo originale)")
    ap.add_argument("--b", required=True, help="ROM 1.2 di lavoro")
    ap.add_argument("--uscita", required=True)
    a = ap.parse_args()
    os.makedirs(a.uscita, exist_ok=True)

    fa = [bytes(x) for x in narc.NARC(NintendoDSRom.fromFile(a.a).getFileByName("a/0/4/6")).files]
    fb = [bytes(x) for x in narc.NARC(NintendoDSRom.fromFile(a.b).getFileByName("a/0/4/6")).files]
    r = {"rom_a": os.path.abspath(a.a), "rom_b": os.path.abspath(a.b)}

    pa, off_pa = leggi_nclr(fa[NCLR_MEMBRO])
    pb, off_pb = leggi_nclr(fb[NCLR_MEMBRO])
    r["nclr"] = {
        "membro": NCLR_MEMBRO, "colori": len(pa), "offset_dati_nel_membro": off_pb,
        "diversi": [{"i": i, "a": f"{pa[i]:04X}", "b": f"{pb[i]:04X}",
                     "a_rgb": rgb(pa[i]), "b_rgb": rgb(pb[i])}
                    for i in range(len(pa)) if pa[i] != pb[i]],
    }
    for tag, pal in (("a", pa), ("b", pb)):
        r["nclr"][f"banco7_{tag}"] = [
            {"idx": 112 + j, "bgr15": f"{pal[112 + j]:04X}", "rgb": rgb(pal[112 + j]),
             "lum": round(lum(pal[112 + j]), 1)} for j in range(16)]

    # --- uso degli indici da parte del logo (SUB_2, 8 bpp) e del credito ---
    for tag, files in (("a", fa), ("b", fb)):
        bpp3, tiles3, _ = leggi_ncgr(files[3])
        w0, h0, celle0, _ = leggi_nscr(files[0])
        usati = collections.Counter()
        for cell in celle0:
            t = cell & 0x3FF
            blob = tiles3[t * 64:(t + 1) * 64]
            for v in blob:
                if v:
                    usati[v] += 1
        r.setdefault("logo_indici", {})[tag] = {
            "bpp": bpp3,
            "indici_usati_min_max": [min(usati) if usati else None, max(usati) if usati else None],
            "usa_112_127": {str(i): usati[i] for i in range(112, 128) if usati[i]},
            "totale_indici_distinti": len(usati),
        }
        # credito
        bpp15, tiles15, off15 = leggi_ncgr(files[15])
        w17, h17, celle17, off17 = leggi_nscr(files[17])
        cw = w17 // 8
        uso_tile = collections.Counter()
        banchi = collections.Counter()
        celle_cred = []
        for ci, cell in enumerate(celle17):
            if cell & 0x3FF:
                uso_tile[cell & 0x3FF] += 1
                banchi[(cell >> 12) & 0xF] += 1
                celle_cred.append({"riga": ci // cw, "col": ci % cw, "cella": f"{cell:04X}"})
        idx_usati = collections.Counter()
        for t in uso_tile:
            for v in pixel_tile(tiles15[t * 32:(t + 1) * 32], 4):
                idx_usati[v] += 1
        r.setdefault("credito", {})[tag] = {
            "bpp": bpp15, "n_tile_nel_ncgr": len(tiles15) // 32,
            "offset_dati_ncgr_nel_membro": off15, "offset_dati_nscr_nel_membro": off17,
            "celle_non_vuote": len(celle_cred), "banchi_palette": dict(banchi),
            "tile_usati": sorted(uso_tile), "n_tile_usati": len(uso_tile),
            "tile_usati_piu_volte": {str(k): v for k, v in uso_tile.items() if v > 1},
            "indici_nei_tile_usati": {str(k): v for k, v in sorted(idx_usati.items())},
            "celle": celle_cred,
        }

    # --- disegni ---
    for tag, files, pal in (("a", fa, pa), ("b", fb, pb)):
        for nome in LIV:
            w, h, rgba, _ = disegna(files, LIV[nome]["ncgr"], LIV[nome]["nscr"], pal)
            png(os.path.join(a.uscita, f"{nome}-{tag}.png"), w, h, rgba)
        # composito del rettangolo del credito, 1x e 6x
        x0, y0, x1, y1 = 144, 168, 256, 192
        w, h, comp = componi(files, pal, x0, y0, x1, y1)
        png(os.path.join(a.uscita, f"credito-composito-{tag}-1x.png"), w, h, comp)
        png(os.path.join(a.uscita, f"credito-composito-{tag}-6x.png"), w, h, comp, zoom=6)

    # --- contrasto del credito sul cielo, per ciascuna ROM ---
    for tag, files, pal in (("a", fa, pa), ("b", fb, pb)):
        _, _, _, idx_cred = disegna(files, 15, 17, pal)
        w3, h3, rgba3, _ = disegna(files, 34, 35, pal)
        _, _, _, idx_logo = disegna(files, 3, 0, pal)
        testo, sfondo = [], []
        for y in range(160, 192):
            for x in range(0, 256):
                if idx_cred[y][x]:
                    testo.append(lum(pal[idx_cred[y][x]]))
                else:
                    # sotto: logo se acceso, altrimenti sfondo
                    if idx_logo[y][x]:
                        sfondo.append(lum(pal[idx_logo[y][x]]))
                    elif rgba3[(y * w3 + x) * 4 + 3]:
                        px = rgba3[(y * w3 + x) * 4:(y * w3 + x) * 4 + 3]
                        sfondo.append(0.2126 * px[0] + 0.7152 * px[1] + 0.0722 * px[2])
        r.setdefault("contrasto", {})[tag] = {
            "pixel_testo": len(testo),
            "lum_testo_media": round(sum(testo) / len(testo), 1) if testo else None,
            "lum_testo_min": round(min(testo), 1) if testo else None,
            "lum_testo_max": round(max(testo), 1) if testo else None,
            "pixel_sfondo_nella_fascia": len(sfondo),
            "lum_sfondo_media": round(sum(sfondo) / len(sfondo), 1) if sfondo else None,
        }

    r["sha"] = {f"membro{i}": {"a": hashlib.sha256(fa[i]).hexdigest()[:16],
                               "b": hashlib.sha256(fb[i]).hexdigest()[:16]}
                for i in (0, 3, 4, 15, 17, 34, 35)}

    with open(os.path.join(a.uscita, "ricognizione02.json"), "w", encoding="utf-8") as f:
        f.write(json.dumps(r, indent=1, ensure_ascii=False) + "\n")
    print("palette: colori diversi 1.04→1.2:", len(r["nclr"]["diversi"]))
    print("logo usa indici 112-127 (a):", r["logo_indici"]["a"]["usa_112_127"])
    print("logo usa indici 112-127 (b):", r["logo_indici"]["b"]["usa_112_127"])
    print("credito a: tile", r["credito"]["a"]["n_tile_usati"], "indici", r["credito"]["a"]["indici_nei_tile_usati"])
    print("credito b: tile", r["credito"]["b"]["n_tile_usati"], "indici", r["credito"]["b"]["indici_nei_tile_usati"])
    print("contrasto:", json.dumps(r["contrasto"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
