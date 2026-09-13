#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SGP-1.2-TITOLO-01 — rilettore INDIPENDENTE.

Non importa `applica_titolo.py` e non ne riusa una riga: arriva al NARC per
un'altra strada (ndspy: `NintendoDSRom` + `narc.NARC`, cioè FNT/FAT/NARC
ricostruiti da una libreria di terzi, non dal parser dell'applicatore), ha il
proprio lettore di NSCR/NCGR/NCLR e ridisegna il livello per guardare i pixel.

Cancelli L1…L7 di `CRITERI.md`. Esce 0 se tutti verdi, 1 altrimenti.

  rileggi_titolo.py --rom ROM [--json FILE|-] [--png DIR]
"""
import argparse
import hashlib
import json
import os
import struct
import sys

from ndspy.rom import NintendoDSRom
from ndspy import narc

NARC_TITOLO = "a/0/4/6"
BERSAGLIO = [(r, c) for r in (22, 23) for c in range(9, 23)]
LARG = 32

# riferimenti presi dalla base 1.1 (`base-1.1-EN.nds` / `base-1.1-IT.nds`, membri
# identici nelle due lingue) PRIMA di toccare qualunque cosa — vedi RAPPORTO §2
SHA_MEMBRO0_BASE = "d93d022ed8f335914fbb4ebc4e06d6fcfc4f85c104cacfce76af813d1b98c6c5"
SHA_996_CELLE = "df9abb32908d750e211063a72f446b7f44cb45081402ec22550a352fa16e1410"
SHA_CREDITO_B = "7aa6c533e332f3a273d8d29cc6233eb1"
SHA_RENDER_SOPRA_176 = "a9fc98ea07671f542a2e00f7dcfe01694747018411370152a0508c5010e72e56"
IMPRONTE_MEMBRI = {
    3: "b17f77a94af28317", 4: "a277c1cab3d63ba6", 15: "a3ee583fa79d1ff6",
    17: "849671d31ebe2e8e", 34: "a9434280d1b0dd55", 35: "af9bc6319be3d608",
}


# ------------------------------------------------- lettore Nitro (mio, a parte)
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
    return w, h, [struct.unpack_from("<H", d, st + i)[0] for i in range(0, ds, 2)]


def ncgr(d):
    o, sz = _sez(d)[b"RAHC"]
    bd = struct.unpack_from("<I", d, o + 12)[0]
    ds = struct.unpack_from("<I", d, o + 24)[0]
    st = o + sz - ds
    return (4 if bd == 3 else 8), bytes(d[st:st + ds])


def nclr(d):
    o, sz = _sez(d)[b"TTLP"]
    ds = struct.unpack_from("<I", d, o + 16)[0]
    st = o + sz - ds
    return [struct.unpack_from("<H", d, st + i)[0] for i in range(0, ds, 2)]


def disegna(files):
    """Ridisegna il livello SUB_2 (NCGR 3 + NSCR 0 + NCLR 4). RGBA grezzo, 256x256."""
    bpp, tiles = ncgr(files[3])
    w, h, celle = nscr(files[0])
    pal = nclr(files[4])
    buf = bytearray(w * h * 4)
    cw = w // 8
    passo = 32 if bpp == 4 else 64
    for ci, cell in enumerate(celle):
        tx, ty = (ci % cw) * 8, (ci // cw) * 8
        t = cell & 0x3FF
        hf, vf, pl = (cell >> 10) & 1, (cell >> 11) & 1, (cell >> 12) & 0xF
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
                buf[o] = (c & 31) * 255 // 31
                buf[o + 1] = ((c >> 5) & 31) * 255 // 31
                buf[o + 2] = ((c >> 10) & 31) * 255 // 31
                buf[o + 3] = 255
    return w, h, bytes(buf)


def png(path, w, h, rgba):
    import zlib
    grezzo = bytearray()
    for y in range(h):
        grezzo.append(0)
        grezzo += rgba[y * w * 4:(y + 1) * w * 4]

    def blocco(t, d):
        c = struct.pack(">I", len(d)) + t + d
        return c + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)

    with open(path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n")
        f.write(blocco(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0)))
        f.write(blocco(b"IDAT", zlib.compress(bytes(grezzo), 9)))
        f.write(blocco(b"IEND", b""))


# ------------------------------------------------------------------- cancelli
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rom", required=True)
    ap.add_argument("--json")
    ap.add_argument("--png")
    a = ap.parse_args()

    rom = NintendoDSRom.fromFile(a.rom)
    n = narc.NARC(rom.getFileByName(NARC_TITOLO))
    files = [bytes(x) for x in n.files]
    r = {"rom": os.path.abspath(a.rom), "cancelli": {}}

    r["cancelli"]["L1_narc"] = (len(files) == 44 and len(files[0]) == 2084)

    w, h, celle = nscr(files[0])
    bers = [celle[rr * LARG + cc] for (rr, cc) in BERSAGLIO]
    r["celle_bersaglio"] = [f"{v:04X}" for v in bers]
    r["cancelli"]["L2_bersaglio_azzerato"] = all(v == 0 for v in bers)

    ind = set(rr * LARG + cc for (rr, cc) in BERSAGLIO)
    altre = b"".join(struct.pack("<H", v) for i, v in enumerate(celle) if i not in ind)
    r["sha_996_celle"] = hashlib.sha256(altre).hexdigest()
    r["cancelli"]["L3_resto_mappa_intatto"] = (r["sha_996_celle"] == SHA_996_CELLE)

    impronte = {i: hashlib.sha256(files[i]).hexdigest()[:16] for i in IMPRONTE_MEMBRI}
    r["impronte_membri"] = {str(k): v for k, v in impronte.items()}
    r["cancelli"]["L4_membri_intoccabili"] = (impronte == IMPRONTE_MEMBRI)

    _w17, _h17, c17 = nscr(files[17])
    cred = b"".join(struct.pack("<H", c17[rr * LARG + cc])
                    for rr in (22, 23) for cc in range(19, 32))
    r["sha_credito_B"] = hashlib.sha256(cred).hexdigest()[:32]
    r["cancelli"]["L5_credito_basso_destra_intatto"] = (r["sha_credito_B"] == SHA_CREDITO_B)

    lw, lh, rgba = disegna(files)
    accesi_sotto = sum(1 for y in range(176, lh) for x in range(lw)
                       if rgba[(y * lw + x) * 4 + 3])
    r["pixel_accesi_sotto_y176"] = accesi_sotto
    r["cancelli"]["L6_niente_sotto_y176"] = (accesi_sotto == 0)

    sopra = hashlib.sha256(rgba[:lw * 176 * 4]).hexdigest()
    r["sha_render_sopra_y176"] = sopra
    r["cancelli"]["L7_logo_identico"] = (sopra == SHA_RENDER_SOPRA_176)

    r["sha_membro0"] = hashlib.sha256(files[0]).hexdigest()
    r["membro0_e_la_base"] = (r["sha_membro0"] == SHA_MEMBRO0_BASE)

    if a.png:
        os.makedirs(a.png, exist_ok=True)
        png(os.path.join(a.png, "sub2-logo.png"), lw, lh, rgba)

    r["tutti_verdi"] = all(r["cancelli"].values())
    testo = json.dumps(r, indent=1, ensure_ascii=False)
    if a.json and a.json != "-":
        open(a.json, "w", encoding="utf-8").write(testo + "\n")
    print(testo)
    return 0 if r["tutti_verdi"] else 1


if __name__ == "__main__":
    sys.exit(main())
