#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SGP-1.2-TITOLO-02 — rilettore INDIPENDENTE del credito del titolo.

Non importa `applica_credito.py` e non ne riusa una riga: arriva al NARC per
un'altra strada (ndspy: `NintendoDSRom` + `narc.NARC`), ha il proprio lettore di
NSCR/NCGR/NCLR, **ridisegna** i tre livelli BG dello schermo alto del titolo e
**misura** il contrasto fra ogni pixel del credito e lo sfondo che gli sta sotto.

Cancelli L1…L7 di `CRITERI.md`. Esce 0 se tutti verdi, 1 altrimenti.

  rileggi_credito.py --rom ROM --base ROM_DI_PARTENZA [--json FILE|-] [--png DIR]
"""
import argparse
import hashlib
import json
import os
import struct
import sys
import zlib

from ndspy.rom import NintendoDSRom
from ndspy import narc

NARC_TITOLO = "a/0/4/6"
LIVELLI = {"SUB3": (34, 35), "SUB2": (3, 0), "SUB1": (15, 17)}
NCLR = 4
MEMBRI_INTOCCABILI = (0, 3, 4, 17, 34, 35)
INDICI_SCURI = (124, 125)          # i due colori che la 1.1 ha reso rossi scuri
RIGHE_CREDITO = (22, 23)           # righe della tilemap: y 176…191
Y0, Y1 = 176, 192
SOGLIA_LUM_TESTO = 200.0
SOGLIA_WCAG_MEDIO = 3.5
SOGLIA_WCAG_P10 = 2.0


# ------------------------------------------------- lettore Nitro (proprio)
def _sz(d):
    hs, ns = struct.unpack_from("<HH", d, 12)
    out, o = {}, hs
    for _ in range(ns):
        m = bytes(d[o:o + 4])
        s = struct.unpack_from("<I", d, o + 4)[0]
        out[m] = (o, s)
        o += s
    return out


def nscr(d):
    o, s = _sz(d)[b"NRCS"]
    w, h = struct.unpack_from("<HH", d, o + 8)
    ds = struct.unpack_from("<I", d, o + 16)[0]
    st = o + s - ds
    return w, h, [struct.unpack_from("<H", d, st + i)[0] for i in range(0, ds, 2)]


def ncgr(d):
    o, s = _sz(d)[b"RAHC"]
    bpp = 4 if struct.unpack_from("<I", d, o + 12)[0] == 3 else 8
    ds = struct.unpack_from("<I", d, o + 24)[0]
    return bpp, bytes(d[o + s - ds:o + s])


def nclr(d):
    o, s = _sz(d)[b"TTLP"]
    ds = struct.unpack_from("<I", d, o + 16)[0]
    st = o + s - ds
    return [struct.unpack_from("<H", d, st + i)[0] for i in range(0, ds, 2)]


def rgb(c):
    return ((c & 31) * 255 // 31, ((c >> 5) & 31) * 255 // 31, ((c >> 10) & 31) * 255 // 31)


def lum(c):
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def _l(v):
    v /= 255.0
    return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4


def wcag(a, b):
    la = 0.2126 * _l(a[0]) + 0.7152 * _l(a[1]) + 0.0722 * _l(a[2])
    lb = 0.2126 * _l(b[0]) + 0.7152 * _l(b[1]) + 0.0722 * _l(b[2])
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def livello(files, i_gfx, i_scr, pal):
    """(w, h, indici[y][x]) — 0 dove il livello è trasparente."""
    bpp, tiles = ncgr(files[i_gfx])
    w, h, celle = nscr(files[i_scr])
    idx = [[0] * w for _ in range(h)]
    cw, passo = w // 8, (32 if bpp == 4 else 64)
    for ci, cell in enumerate(celle):
        t = cell & 0x3FF
        blob = tiles[t * passo:(t + 1) * passo]
        if len(blob) < passo:
            continue
        hf, vf, pl = (cell >> 10) & 1, (cell >> 11) & 1, (cell >> 12) & 0xF
        if bpp == 4:
            px = []
            for b in blob:
                px += [b & 0xF, b >> 4]
        else:
            px = list(blob)
        tx, ty = (ci % cw) * 8, (ci // cw) * 8
        for y in range(8):
            for x in range(8):
                v = px[(7 - y if vf else y) * 8 + (7 - x if hf else x)]
                if v:
                    idx[ty + y][tx + x] = (pl * 16 + v) if bpp == 4 else v
    return w, h, idx


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


def scena(rom):
    files = [bytes(x) for x in narc.NARC(NintendoDSRom.fromFile(rom).getFileByName(NARC_TITOLO)).files]
    pal = nclr(files[NCLR])
    liv = {k: livello(files, g, s, pal) for k, (g, s) in LIVELLI.items()}
    return files, pal, liv


def colore(idx, pal, y, x, liv):
    """RGB composito dello sfondo in (y,x): SUB_3 sotto, SUB_2 sopra."""
    c = (0, 0, 0)
    for k in ("SUB3", "SUB2"):
        w, h, m = liv[k]
        if y < h and x < w and m[y][x]:
            c = rgb(pal[m[y][x]])
    return c


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rom", required=True)
    ap.add_argument("--base", required=True, help="ROM di partenza, per la forma e le impronte")
    ap.add_argument("--json")
    ap.add_argument("--png")
    ap.add_argument("--nome", default="")
    a = ap.parse_args()

    fr, palr, livr = scena(a.rom)
    fb, palb, livb = scena(a.base)
    r = {"rom": os.path.abspath(a.rom), "base": os.path.abspath(a.base), "cancelli": {}}

    # L1 — struttura
    r["cancelli"]["L1_struttura"] = (
        len(fr) == 44 and len(fr[15]) == 3136 and len(fr[17]) == 1572
        and ncgr(fr[15])[0] == 4)

    w, h, cred = livr["SUB1"]
    _wb, _hb, credb = livb["SUB1"]

    # L2 — nessun pixel del credito usa più i colori scuri 124/125
    usati = {}
    for y in range(h):
        for x in range(w):
            if cred[y][x]:
                usati[cred[y][x]] = usati.get(cred[y][x], 0) + 1
    r["indici_usati_dal_credito"] = {str(k): v for k, v in sorted(usati.items())}
    r["cancelli"]["L2_niente_indici_scuri"] = not any(i in usati for i in INDICI_SCURI)

    # L3 — la maschera (forma) del testo è identica
    diff_forma = sum(1 for y in range(h) for x in range(w)
                     if bool(cred[y][x]) != bool(credb[y][x]))
    r["pixel_di_forma_diversi"] = diff_forma
    r["cancelli"]["L3_forma_identica"] = (diff_forma == 0)

    # L4 — membri intoccabili
    r["impronte"] = {str(i): hashlib.sha256(fr[i]).hexdigest()[:16] for i in MEMBRI_INTOCCABILI}
    r["impronte_base"] = {str(i): hashlib.sha256(fb[i]).hexdigest()[:16] for i in MEMBRI_INTOCCABILI}
    r["cancelli"]["L4_membri_intoccabili"] = (r["impronte"] == r["impronte_base"])

    # L5 / L6 — contrasto, pixel per pixel, contro lo sfondo che sta sotto
    def misura(cr, pal, liv):
        lt, dv, wc, piu_chiari = [], [], [], 0
        for y in range(h):
            for x in range(w):
                if not cr[y][x]:
                    continue
                ct = rgb(pal[cr[y][x]])
                cs = colore(cr, pal, y, x, liv)
                lt.append(lum(ct))
                dv.append(lum(ct) - lum(cs))
                wc.append(wcag(ct, cs))
                piu_chiari += 1 if lum(ct) > lum(cs) else 0
        n = len(lt)
        wcs = sorted(wc)
        return {
            "pixel_testo": n,
            "lum_testo_media": round(sum(lt) / n, 1),
            "lum_testo_min": round(min(lt), 1),
            "delta_lum_medio": round(sum(dv) / n, 1),
            "frazione_piu_chiari_dello_sfondo": round(piu_chiari / n, 3),
            "wcag_medio": round(sum(wc) / n, 2),
            "wcag_min": round(wcs[0], 2),
            "wcag_p10": round(wcs[n // 10], 2),
        }

    m_r = misura(cred, palr, livr)
    m_b = misura(credb, palb, livb)
    r["contrasto_dopo"] = m_r
    r["contrasto_prima"] = m_b
    r["cancelli"]["L5_tutti_chiari_e_sopra_lo_sfondo"] = (
        m_r["lum_testo_min"] >= SOGLIA_LUM_TESTO
        and m_r["frazione_piu_chiari_dello_sfondo"] == 1.0)
    r["cancelli"]["L6_contrasto"] = (
        m_r["lum_testo_media"] >= SOGLIA_LUM_TESTO
        and m_r["wcag_medio"] >= SOGLIA_WCAG_MEDIO
        and m_r["wcag_p10"] >= SOGLIA_WCAG_P10)

    # L7 — fuori dalle righe del credito nulla è cambiato, su tutti e tre i livelli
    fuori = 0
    for k in LIVELLI:
        ww, hh, mr = livr[k]
        _w2, _h2, mb = livb[k]
        for y in range(hh):
            for x in range(ww):
                if Y0 <= y < Y1 and k == "SUB1":
                    continue
                if mr[y][x] != mb[y][x]:
                    fuori += 1
    r["pixel_diversi_fuori_dal_credito"] = fuori
    r["cancelli"]["L7_nulla_altrove"] = (fuori == 0)

    if a.png:
        os.makedirs(a.png, exist_ok=True)
        x0, x1 = 144, 256
        for tag, cr, pal, liv in (("dopo", cred, palr, livr), ("prima", credb, palb, livb)):
            ww = x1 - x0
            hh = Y1 - 168
            buf = bytearray(ww * hh * 4)
            for y in range(168, Y1):
                for x in range(x0, x1):
                    c = rgb(pal[cr[y][x]]) if cr[y][x] else colore(cr, pal, y, x, liv)
                    o = ((y - 168) * ww + (x - x0)) * 4
                    buf[o], buf[o + 1], buf[o + 2], buf[o + 3] = c[0], c[1], c[2], 255
            nome = (a.nome + "-" if a.nome else "") + f"credito-{tag}"
            png(os.path.join(a.png, nome + "-1x.png"), ww, hh, bytes(buf))
            png(os.path.join(a.png, nome + "-6x.png"), ww, hh, bytes(buf), zoom=6)

    r["tutti_verdi"] = all(r["cancelli"].values())
    testo = json.dumps(r, indent=1, ensure_ascii=False)
    if a.json and a.json != "-":
        open(a.json, "w", encoding="utf-8").write(testo + "\n")
    print(testo)
    return 0 if r["tutti_verdi"] else 1


if __name__ == "__main__":
    sys.exit(main())
