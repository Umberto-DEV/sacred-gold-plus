#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SGP-1.2-TITOLO-02 — applicatore idempotente: rende leggibile il credito.

Il credito in basso a destra del titolo («Developed by  A FAN», livello BG SUB_1,
NCGR membro 15 + NSCR membro 17 del NARC `a/0/4/6`, 4 bpp, banco palette 7)
disegna i glifi con tre indici locali — 14 in alto, 13 in mezzo, 12 in basso — che
nella 1.04 erano tre grigio-bianchi. Rifacendo il logo, la 1.1 ha riscritto i
colori 124 e 125 della palette (membro 4) in due rossi scuri: due righe di glifo su
tre finiscono più scure del cielo e il credito non si legge.

Questo applicatore cambia **solo gli indici di colore dentro i tile del credito**:
nei 24 tile referenziati dalla tilemap, ogni pixel di valore 12 o 13 diventa 14 —
cioè il colore 126 `6FDF` (255,246,222), quello con cui la 1.1 già disegna la riga
alta di questi stessi glifi. Nessuna palette toccata, nessuna cella di tilemap
toccata, nessun colore nuovo nella scena, forma del testo invariata al pixel.

Attesi: 149 pixel, **119 byte**, tutti dentro il membro 15; lunghezza di membro,
NARC, FAT e ROM invariate. Membri 15 e 17 sono identici in EN e IT.

Non usa ndspy: legge da sé intestazione NDS, FNT, FAT e NARC, e scrive in luogo.

Uso:
  applica_credito.py --rom ROM --uscita NUOVA [--json REL.json]
  applica_credito.py --rom ROM --in-luogo    [--json REL.json]
  applica_credito.py --rom ROM --verifica
"""
import argparse
import hashlib
import json
import os
import shutil
import struct
import subprocess
import sys
import tempfile

NARC_TITOLO = "a/0/4/6"
MEMBRO_TILE = 15          # titledemo_00000015.NCGR — i tile del credito
MEMBRO_MAPPA = 17         # titledemo_00000017.NSCR — la tilemap del credito
MEMBRO_PALETTE = 4
MEMBRI_INTOCCABILI = (0, 3, 4, 17, 34, 35)
DA = (12, 13)             # indici locali da rimappare
A = 14                    # indice locale d'arrivo (colore 126)
BANCO_ATTESO = 7
N_MEMBRI = 44
LEN_M15, LEN_M17 = 3136, 1572

IMPRONTA_M15_PRIMA = "a3ee583fa79d1ff6"
IMPRONTA_M15_DOPO = "144f13ba71bdacad"   # membro 15 dopo la rimappatura (EN = IT)
BYTE_ATTESI = 119
PIXEL_ATTESI = 149

IMPRONTE_INTOCCABILI_ATTESE = {
    # membro 0: stato dopo SGP-1.2-TITOLO-01 (scritta sotto il logo rimossa)
    "0": "e1e290399f2d6c5a", "3": "b17f77a94af28317", "4": "a277c1cab3d63ba6",
    "17": "849671d31ebe2e8e", "34": "a9434280d1b0dd55", "35": "af9bc6319be3d608",
}


# ---------------------------------------------------------------- lettura NDS
def _u16(d, o):
    return struct.unpack_from("<H", d, o)[0]


def _u32(d, o):
    return struct.unpack_from("<I", d, o)[0]


def risolvi_id(f, percorso):
    """Risolve 'a/0/4/6' nell'id di file camminando la FNT. Nessun ndspy."""
    f.seek(0)
    testa = f.read(0x200)
    fnt_off, fnt_size = struct.unpack_from("<II", testa, 0x40)
    f.seek(fnt_off)
    fnt = f.read(fnt_size)
    dir_id = 0xF000
    for pezzo in percorso.split("/"):
        i = (dir_id & 0x0FFF) * 8
        sub_off = _u32(fnt, i)
        primo = _u16(fnt, i + 4)
        o, fid, trovato = sub_off, primo, None
        while True:
            t = fnt[o]
            o += 1
            if t == 0:
                break
            lung = t & 0x7F
            nome = fnt[o:o + lung].decode("ascii", "replace")
            o += lung
            if t & 0x80:
                sotto = _u16(fnt, o)
                o += 2
                if nome == pezzo:
                    trovato = ("dir", sotto)
                    break
            else:
                if nome == pezzo:
                    trovato = ("file", fid)
                    break
                fid += 1
        if trovato is None:
            raise SystemExit("percorso non trovato nella FNT: " + percorso)
        if trovato[0] == "dir":
            dir_id = trovato[1]
        else:
            return trovato[1]
    raise SystemExit("il percorso finisce su una cartella: " + percorso)


def estremi_file(f, fid):
    f.seek(0)
    testa = f.read(0x200)
    fat_off, _ = struct.unpack_from("<II", testa, 0x48)
    f.seek(fat_off + fid * 8)
    return struct.unpack("<II", f.read(8))


def sezioni_narc(blob):
    if blob[:4] != b"NARC":
        raise SystemExit("non è un NARC: " + repr(blob[:4]))
    hdrsize, nsec = struct.unpack_from("<HH", blob, 12)
    out, off = {}, hdrsize
    for _ in range(nsec):
        magic = bytes(blob[off:off + 4])
        size = _u32(blob, off + 4)
        out[magic] = off
        off += size
    return out


def posizione_membro(f, indice):
    """(offset assoluto del membro nel file, lunghezza, numero di membri)."""
    fid = risolvi_id(f, NARC_TITOLO)
    st, en = estremi_file(f, fid)
    f.seek(st)
    blob = f.read(en - st)
    sez = sezioni_narc(blob)
    btaf = sez[b"BTAF"]
    nfiles = _u32(blob, btaf + 8)
    if indice >= nfiles:
        raise SystemExit("membro fuori dal NARC")
    m_st, m_en = struct.unpack_from("<II", blob, btaf + 12 + indice * 8)
    return st + sez[b"GMIF"] + 8 + m_st, m_en - m_st, nfiles


def leggi_membro(f, indice):
    off, lun, n = posizione_membro(f, indice)
    f.seek(off)
    return off, f.read(lun), n


def sezione(d, magic):
    hdrsize, nsec = struct.unpack_from("<HH", d, 12)
    off = hdrsize
    for _ in range(nsec):
        m = bytes(d[off:off + 4])
        size = _u32(d, off + 4)
        if m == magic:
            return off, size
        off += size
    raise SystemExit("sezione assente: " + repr(magic))


def dati_ncgr(d):
    """(offset dei dati dentro il membro, lunghezza, bpp)."""
    o, sz = sezione(d, b"RAHC")
    bpp = 4 if _u32(d, o + 12) == 3 else 8
    ds = _u32(d, o + 24)
    return o + sz - ds, ds, bpp


def celle_nscr(d):
    o, sz = sezione(d, b"NRCS")
    ds = _u32(d, o + 16)
    st = o + sz - ds
    return [_u16(d, st + i) for i in range(0, ds, 2)]


def colori_nclr(d):
    o, sz = sezione(d, b"TTLP")
    ds = _u32(d, o + 16)
    st = o + sz - ds
    return [_u16(d, st + i) for i in range(0, ds, 2)]


def lum15(c):
    r, g, b = (c & 31) * 255 // 31, ((c >> 5) & 31) * 255 // 31, ((c >> 10) & 31) * 255 // 31
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


# ---------------------------------------------------------------- il contratto
def bersagli(f):
    """Offset assoluti dei byte da cambiare e loro valore nuovo.

    Ritorna (lista di (offset, vecchio, nuovo), info)."""
    off15, m15, _ = leggi_membro(f, MEMBRO_TILE)
    _off17, m17, _ = leggi_membro(f, MEMBRO_MAPPA)
    d_off, d_len, bpp = dati_ncgr(m15)
    celle = celle_nscr(m17)
    usati = sorted({c & 0x3FF for c in celle if c & 0x3FF})
    banchi = sorted({(c >> 12) & 0xF for c in celle if c & 0x3FF})
    lavoro = []
    pixel = 0
    for t in usati:
        base = d_off + t * 32
        for k in range(32):
            b = m15[base + k]
            lo, hi = b & 0xF, b >> 4
            nlo = A if lo in DA else lo
            nhi = A if hi in DA else hi
            if (nlo, nhi) != (lo, hi):
                pixel += (lo in DA) + (hi in DA)
                lavoro.append((off15 + base + k, b, (nhi << 4) | nlo))
    # sconfinamenti: nibble 12/13 nei tile NON referenziati
    fuori = 0
    for t in range(d_len // 32):
        if t in usati:
            continue
        for k in range(32):
            b = m15[d_off + t * 32 + k]
            if (b & 0xF) in DA or (b >> 4) in DA:
                fuori += 1
    info = {"bpp": bpp, "n_tile": d_len // 32, "tile_usati": usati,
            "banchi": banchi, "offset_dati_nel_membro": d_off,
            "pixel_da_cambiare": pixel, "byte_da_cambiare": len(lavoro),
            "byte_con_12_13_fuori_dai_tile_usati": fuori,
            "offset_membro15": off15, "len_membro15": len(m15), "len_membro17": len(m17)}
    return lavoro, info


def impronta_membro(f, i):
    _o, d, _n = leggi_membro(f, i)
    return hashlib.sha256(d).hexdigest()


def cancelli_lettura(percorso):
    r = {"cancelli": {}}
    with open(percorso, "rb") as f:
        _o, m15, nfiles = leggi_membro(f, MEMBRO_TILE)
        r["n_membri"] = nfiles
        r["cancelli"]["A0_narc_44_membri"] = (nfiles == N_MEMBRI)
        sha15 = hashlib.sha256(m15).hexdigest()
        r["sha256_membro15"] = sha15
        lavoro, info = bersagli(f)
        r["info"] = info
        gia = (len(lavoro) == 0)
        r["stato"] = ("già-applicato" if gia and sha15[:16] == IMPRONTA_M15_DOPO
                      else ("da-applicare" if sha15[:16] == IMPRONTA_M15_PRIMA
                            else ("già-applicato" if gia else "sconosciuto")))
        r["cancelli"]["A1_impronta_membro15_nota"] = sha15[:16] in (IMPRONTA_M15_PRIMA,
                                                                    IMPRONTA_M15_DOPO)
        r["cancelli"]["A2_ncgr_4bpp_96_tile_24_celle_banco7"] = (
            info["bpp"] == 4 and info["n_tile"] == 96 and len(info["tile_usati"]) == 24
            and info["banchi"] == [BANCO_ATTESO] and info["len_membro15"] == LEN_M15
            and info["len_membro17"] == LEN_M17)
        r["cancelli"]["A3_nessun_12_13_fuori_dai_tile_usati"] = (
            info["byte_con_12_13_fuori_dai_tile_usati"] == 0)

        _o4, m4, _ = leggi_membro(f, MEMBRO_PALETTE)
        pal = colori_nclr(m4)
        L = {i: round(lum15(pal[i]), 1) for i in (124, 125, 126)}
        r["luminanze_palette"] = L
        r["cancelli"]["A4_difetto_e_rimedio"] = (L[126] >= 200 and L[124] < 120 and L[125] < 120)

        r["impronte_intoccabili"] = {str(i): impronta_membro(f, i)[:16]
                                     for i in MEMBRI_INTOCCABILI}
        r["cancelli"]["A7_membri_intoccabili"] = (
            r["impronte_intoccabili"] == IMPRONTE_INTOCCABILI_ATTESE)
    r["tutti_verdi"] = all(r["cancelli"].values())
    return r


# ---------------------------------------------------------------- scrittura
def applica(percorso):
    cambiati = 0
    with open(percorso, "r+b") as f:
        lavoro, _info = bersagli(f)
        for off, vecchio, nuovo in lavoro:
            f.seek(off)
            if f.read(1)[0] != vecchio:
                raise SystemExit("byte inatteso a 0x%X" % off)
            f.seek(off)
            f.write(bytes([nuovo]))
            cambiati += 1
        f.flush()
        os.fsync(f.fileno())
    return cambiati


def diff_byte(a, b):
    n, lo, hi = 0, None, None
    with open(a, "rb") as fa, open(b, "rb") as fb:
        base = 0
        while True:
            da, db = fa.read(1 << 20), fb.read(1 << 20)
            if not da and not db:
                break
            if len(da) != len(db):
                return -1, None, None
            if da != db:
                for i, (x, y) in enumerate(zip(da, db)):
                    if x != y:
                        n += 1
                        o = base + i
                        lo = o if lo is None else min(lo, o)
                        hi = o if hi is None else max(hi, o)
            base += len(da)
    return n, lo, hi


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for blocco in iter(lambda: f.read(1 << 20), b""):
            h.update(blocco)
    return h.hexdigest()


def aggiorna_sha256sums(rom):
    d = os.path.dirname(os.path.abspath(rom))
    f = os.path.join(d, "SHA256SUMS")
    if not os.path.exists(f):
        return False
    nome = os.path.basename(rom)
    nuovo = sha256(rom)
    righe, visto = [], False
    for riga in open(f, encoding="utf-8").read().splitlines():
        if riga.strip().endswith(" " + nome):
            righe.append(f"{nuovo}  {nome}")
            visto = True
        else:
            righe.append(riga)
    if not visto:
        righe.append(f"{nuovo}  {nome}")
    open(f, "w", encoding="utf-8").write("\n".join(righe) + "\n")
    return True


def rilettore(rom, base):
    qui = os.path.dirname(os.path.abspath(__file__))
    cmd = [sys.executable, os.path.join(qui, "rileggi_credito.py"),
           "--rom", rom, "--base", base, "--json", "-"]
    r = subprocess.run(cmd, capture_output=True, text=True)
    try:
        return r.returncode == 0, json.loads(r.stdout)
    except Exception:
        return False, {"errore": r.stdout[-2000:] + r.stderr[-2000:]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rom", required=True)
    ap.add_argument("--uscita")
    ap.add_argument("--in-luogo", action="store_true", dest="in_luogo")
    ap.add_argument("--verifica", action="store_true")
    ap.add_argument("--json")
    a = ap.parse_args()

    rel = {"rom": os.path.abspath(a.rom), "contratto": {
        "narc": NARC_TITOLO, "membro": MEMBRO_TILE,
        "regola": "nei tile referenziati dalla tilemap 17: nibble 12 o 13 -> 14",
        "byte_attesi": BYTE_ATTESI, "pixel_attesi": PIXEL_ATTESI}}
    rel["prima"] = cancelli_lettura(a.rom)

    if a.verifica:
        rel["esito"] = "solo-verifica"
        _stampa(rel, a.json)
        return 0 if rel["prima"]["tutti_verdi"] else 1

    if not rel["prima"]["tutti_verdi"]:
        rel["esito"] = "cancelli-rossi-non-applico"
        _stampa(rel, a.json)
        return 1
    if not (a.uscita or a.in_luogo):
        raise SystemExit("serve --uscita FILE oppure --in-luogo")

    tmp = tempfile.mkdtemp(prefix="titolo02-", dir=os.environ.get("SCRATCH") or None)
    try:
        lavoro = os.path.join(tmp, os.path.basename(a.rom))
        shutil.copy2(a.rom, lavoro)
        _cambiati = applica(lavoro)
        n, lo, hi = diff_byte(a.rom, lavoro)
        off15 = rel["prima"]["info"]["offset_membro15"]
        rel["byte_cambiati"] = n
        rel["intervallo_byte"] = [lo, hi]
        rel["dimensione_invariata"] = os.path.getsize(a.rom) == os.path.getsize(lavoro)
        gia = rel["prima"]["stato"] == "già-applicato"
        rel["cancelli_scrittura"] = {
            "A5_solo_119_byte": (n == BYTE_ATTESI) or (n == 0 and gia),
            "A5_byte_dentro_il_membro15": (lo is None or (lo >= off15 and hi < off15 + LEN_M15)),
            "A5_dimensione_invariata": rel["dimensione_invariata"],
            "A6_idempotente": (applica(lavoro) == 0),
        }
        rel["dopo"] = cancelli_lettura(lavoro)
        rel["cancelli_scrittura"]["A2b_nessun_12_13_residuo"] = (
            rel["dopo"]["info"]["byte_da_cambiare"] == 0)
        rel["cancelli_scrittura"]["A7_membri_intoccabili"] = rel["dopo"]["cancelli"]["A7_membri_intoccabili"]
        verde, det = rilettore(lavoro, a.rom)
        rel["rilettore"] = det
        rel["cancelli_scrittura"]["A8_rilettore_verde"] = verde
        rel["sha256_ingresso"] = sha256(a.rom)
        rel["sha256_uscita"] = sha256(lavoro)
        rel["sha256_membro15_dopo"] = rel["dopo"]["sha256_membro15"]
        rel["tutti_verdi"] = all(rel["cancelli_scrittura"].values()) and rel["dopo"]["tutti_verdi"]

        if not rel["tutti_verdi"]:
            rel["esito"] = "rosso-non-sostituisco"
            _stampa(rel, a.json)
            return 1
        if a.in_luogo:
            shutil.copy2(lavoro, a.rom)
            rel["sha256sums_aggiornato"] = aggiorna_sha256sums(a.rom)
            rel["esito"] = "applicato-in-luogo"
        else:
            shutil.copy2(lavoro, a.uscita)
            rel["esito"] = "scritto-in-" + a.uscita
        _stampa(rel, a.json)
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def _stampa(rel, dove):
    testo = json.dumps(rel, indent=1, ensure_ascii=False)
    if dove and dove != "-":
        open(dove, "w", encoding="utf-8").write(testo + "\n")
    print(testo)


if __name__ == "__main__":
    sys.exit(main())
