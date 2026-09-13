#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SGP-1.2-TITOLO-01 — applicatore idempotente.

Toglie la scritta «Developed by a fan» che sta SOTTO il logo della schermata del
titolo (schermo alto), lasciando quella in basso a destra, cioè al posto del
credito originale «Developed by GAME FREAK inc.».

Che cosa scrive, esattamente: 28 celle (56 byte) della tilemap del livello BG
SUB_2 del titolo — membro 0 del NARC `a/0/4/6` (`demo/title/titledemo.narc`),
righe 22 e 23, colonne 9…22 di una mappa 32×32 — da `0x011A…0x0135` a `0x0000`.
`0x0000` è il valore che quelle stesse celle avevano nella 1.04, prima che la 1.1
aggiungesse la scritta: la rimozione riporta i byte al valore originale.

Non tocca nient'altro: né il NCGR del logo (membro 3), né la palette (membro 4),
né il credito in basso (membri 15/17), né lo sfondo (34/35), né lo schermo
inferiore animato, né ARM9/overlay, né la lunghezza di NARC, FAT, ROM.

Non usa ndspy: legge da sé l'intestazione NDS, la FNT, la FAT e il NARC, e scrive
IN LUOGO i 56 byte. La ROM non viene mai ricostruita.

Uso:
  applica_titolo.py --rom ROM --uscita NUOVA [--json REL.json]
  applica_titolo.py --rom ROM --in-luogo    [--json REL.json]   (sostituisce ROM
      solo dopo che il rilettore indipendente è verde; aggiorna SHA256SUMS
      accanto alla ROM se esiste)
  applica_titolo.py --rom ROM --verifica     (non scrive niente, dice lo stato)
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
MEMBRO_MAPPA = 0          # titledemo_00000000.NSCR — tilemap del livello SUB_2
MEMBRO_TILE = 3           # titledemo_00000003.NCGR — grafica del logo
MEMBRI_INTOCCABILI = (3, 4, 15, 17, 34, 35)
RIGHE = (22, 23)
COLONNE = range(9, 23)    # 9…22 compresi
LARGHEZZA_MAPPA = 32      # celle per riga
CELLE_ATTESE_PRIMA = tuple(range(0x011A, 0x0136))   # 28 valori consecutivi
CELLA_DOPO = 0x0000

IMPRONTA_M0_PRIMA = "d93d022ed8f33591"   # sha256[:16] del membro 0 nella 1.1/1.2
IMPRONTA_M0_DOPO = None                  # calcolata sotto, dopo la sostituzione


# ---------------------------------------------------------------- lettura NDS
def _u16(d, o):
    return struct.unpack_from("<H", d, o)[0]


def _u32(d, o):
    return struct.unpack_from("<I", d, o)[0]


def risolvi_id(f, percorso):
    """Risolve 'a/0/4/6' nell'id di file, camminando la FNT. Nessun ndspy."""
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
        o = sub_off
        fid = primo
        trovato = None
        while True:
            t = fnt[o]
            o += 1
            if t == 0:
                break
            lung = t & 0x7F
            nome = fnt[o:o + lung].decode("ascii", "replace")
            o += lung
            if t & 0x80:            # sottocartella
                sotto = _u16(fnt, o)
                o += 2
                if nome == pezzo:
                    trovato = ("dir", sotto)
                    break
            else:                   # file
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
    fat_off, _fat_size = struct.unpack_from("<II", testa, 0x48)
    f.seek(fat_off + fid * 8)
    return struct.unpack("<II", f.read(8))


def sezioni_narc(blob, base):
    """{magic: (offset assoluto nel file, dimensione)} per le sezioni del NARC."""
    if blob[:4] != b"NARC":
        raise SystemExit("non è un NARC: " + repr(blob[:4]))
    hdrsize, nsec = struct.unpack_from("<HH", blob, 12)
    out, off = {}, hdrsize
    for _ in range(nsec):
        magic = bytes(blob[off:off + 4])
        size = _u32(blob, off + 4)
        out[magic] = (base + off, size, off)
        off += size
    return out


def posizione_membro(f, indice):
    """(offset assoluto del membro nel file, lunghezza, numero di membri)."""
    fid = risolvi_id(f, NARC_TITOLO)
    st, en = estremi_file(f, fid)
    f.seek(st)
    blob = f.read(en - st)
    sez = sezioni_narc(blob, st)
    btaf_abs, _sz, btaf_rel = sez[b"BTAF"]
    nfiles = _u32(blob, btaf_rel + 8)
    if indice >= nfiles:
        raise SystemExit("membro fuori dal NARC")
    m_st, m_en = struct.unpack_from("<II", blob, btaf_rel + 12 + indice * 8)
    _gmif_abs, _gmif_sz, gmif_rel = sez[b"GMIF"]
    dati = st + gmif_rel + 8 + m_st
    return dati, m_en - m_st, nfiles


def offset_celle(f):
    """Offset assoluti, nel file, delle 28 celle bersaglio (u16 ciascuna)."""
    m0_off, m0_len, _ = posizione_membro(f, MEMBRO_MAPPA)
    f.seek(m0_off)
    m0 = f.read(m0_len)
    if bytes(m0[:4]) != b"RCSN":
        raise SystemExit("il membro 0 non è un NSCR")
    sez = sezioni_narc_nscr(m0)
    nrcs_off, nrcs_size = sez
    w, h = struct.unpack_from("<HH", m0, nrcs_off + 8)
    datasize = _u32(m0, nrcs_off + 12 + 4)
    dstart = nrcs_off + nrcs_size - datasize
    fuori = []
    for r in RIGHE:
        for c in COLONNE:
            fuori.append(m0_off + dstart + 2 * (r * LARGHEZZA_MAPPA + c))
    return fuori, m0_off, m0_len, (w, h, datasize, dstart)


def sezioni_narc_nscr(m0):
    hdrsize, nsec = struct.unpack_from("<HH", m0, 12)
    off = hdrsize
    for _ in range(nsec):
        magic = bytes(m0[off:off + 4])
        size = _u32(m0, off + 4)
        if magic == b"NRCS":
            return off, size
        off += size
    raise SystemExit("sezione NRCS assente")


# ---------------------------------------------------------------- cancelli
def celle_attuali(f):
    fuori, m0_off, m0_len, info = offset_celle(f)
    vals = []
    for o in fuori:
        f.seek(o)
        vals.append(_u16(f.read(2), 0))
    return vals, fuori, m0_off, m0_len, info


def impronta_membro(f, indice):
    off, lun, _ = posizione_membro(f, indice)
    f.seek(off)
    return hashlib.sha256(f.read(lun)).hexdigest()


def cancelli_lettura(percorso):
    """A0…A4 + A7 (parte statica). Ritorna (stato, rapporto)."""
    r = {"cancelli": {}}
    with open(percorso, "rb") as f:
        _dati, _lun, nfiles = posizione_membro(f, MEMBRO_MAPPA)
        r["cancelli"]["A0_narc_44_membri"] = (nfiles == 44)
        r["n_membri"] = nfiles

        m0_sha = impronta_membro(f, MEMBRO_MAPPA)
        r["sha256_membro0"] = m0_sha
        vals, fuori, m0_off, m0_len, info = celle_attuali(f)
        r["offset_prima_cella"] = fuori[0]
        r["offset_ultima_cella"] = fuori[-1]
        r["celle"] = [f"{v:04X}" for v in vals]

        prima = (tuple(vals) == CELLE_ATTESE_PRIMA)
        dopo = all(v == CELLA_DOPO for v in vals)
        r["stato"] = "da-applicare" if prima else ("già-applicato" if dopo else "sconosciuto")
        r["cancelli"]["A1_impronta_membro0_nota"] = (m0_sha[:16] == IMPRONTA_M0_PRIMA) or dopo
        r["cancelli"]["A2_celle_attese"] = prima or dopo

        # A3: i tile del bersaglio non sono usati altrove nella mappa
        _f2, _o, _l, (w, h, datasize, dstart) = fuori, m0_off, m0_len, info
        f.seek(m0_off + dstart)
        mappa = f.read(datasize)
        usati = {}
        for i in range(0, datasize, 2):
            t = _u16(mappa, i) & 0x3FF
            usati[t] = usati.get(t, 0) + 1
        bersaglio = set(v & 0x3FF for v in vals) if prima else set(CELLE_ATTESE_PRIMA)
        altrove = {f"{t:03X}": usati.get(t, 0) for t in sorted(bersaglio) if usati.get(t, 0) > 1}
        r["cancelli"]["A3_tile_esclusivi"] = (not altrove) if prima else True
        r["tile_usati_altrove"] = altrove

        # A4: il tile 0 del NCGR del logo è tutto a zero (trasparente)
        m3_off, m3_len, _ = posizione_membro(f, MEMBRO_TILE)
        f.seek(m3_off)
        m3 = f.read(m3_len)
        rahc_off, rahc_size = None, None
        hdrsize, nsec = struct.unpack_from("<HH", m3, 12)
        off = hdrsize
        for _ in range(nsec):
            magic = bytes(m3[off:off + 4])
            size = _u32(m3, off + 4)
            if magic == b"RAHC":
                rahc_off, rahc_size = off, size
                break
            off += size
        bitdepth = _u32(m3, rahc_off + 12)
        bpp = 4 if bitdepth == 3 else 8
        ds = _u32(m3, rahc_off + 24)
        d0 = rahc_off + rahc_size - ds
        n = 32 if bpp == 4 else 64
        r["cancelli"]["A4_tile0_trasparente"] = all(b == 0 for b in m3[d0:d0 + n])

        r["impronte_intoccabili"] = {str(i): impronta_membro(f, i)[:16]
                                     for i in MEMBRI_INTOCCABILI}
    r["tutti_verdi"] = all(r["cancelli"].values())
    return r


IMPRONTE_INTOCCABILI_ATTESE = {
    "3": "b17f77a94af28317", "4": "a277c1cab3d63ba6",
    "15": "a3ee583fa79d1ff6", "17": "849671d31ebe2e8e",
    "34": "a9434280d1b0dd55", "35": "af9bc6319be3d608",
}


# ---------------------------------------------------------------- scrittura
def applica(percorso):
    """Scrive i 56 byte IN LUOGO nel file indicato. Ritorna il numero di byte cambiati."""
    cambiati = 0
    with open(percorso, "r+b") as f:
        vals, fuori, _m0_off, _m0_len, _info = celle_attuali(f)
        if all(v == CELLA_DOPO for v in vals):
            return 0
        if tuple(vals) != CELLE_ATTESE_PRIMA:
            raise SystemExit("celle inattese, non applico: " + " ".join(f"{v:04X}" for v in vals))
        for o in fuori:
            f.seek(o)
            vecchio = f.read(2)
            nuovo = struct.pack("<H", CELLA_DOPO)
            if vecchio != nuovo:
                f.seek(o)
                f.write(nuovo)
                cambiati += sum(1 for a, b in zip(vecchio, nuovo) if a != b)
        f.flush()
        os.fsync(f.fileno())
    return cambiati


def diff_byte(a, b):
    """Numero di byte diversi e (min,max) offset, leggendo a blocchi."""
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
    righe = []
    visto = False
    for riga in open(f, encoding="utf-8").read().splitlines():
        if riga.strip().endswith(" " + nome) or riga.strip().endswith("  " + nome):
            righe.append(f"{nuovo}  {nome}")
            visto = True
        else:
            righe.append(riga)
    if not visto:
        righe.append(f"{nuovo}  {nome}")
    open(f, "w", encoding="utf-8").write("\n".join(righe) + "\n")
    return True


def rilettore(rom):
    qui = os.path.dirname(os.path.abspath(__file__))
    r = subprocess.run([sys.executable, os.path.join(qui, "rileggi_titolo.py"),
                        "--rom", rom, "--json", "-"],
                       capture_output=True, text=True)
    try:
        return r.returncode == 0, json.loads(r.stdout)
    except Exception:
        return False, {"errore": r.stdout + r.stderr}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rom", required=True)
    ap.add_argument("--uscita")
    ap.add_argument("--in-luogo", action="store_true", dest="in_luogo")
    ap.add_argument("--verifica", action="store_true")
    ap.add_argument("--json")
    a = ap.parse_args()

    rel = {"rom": os.path.abspath(a.rom)}
    rel["prima"] = cancelli_lettura(a.rom)
    rel["prima"]["cancelli"]["A7_membri_intoccabili"] = (
        rel["prima"]["impronte_intoccabili"] == IMPRONTE_INTOCCABILI_ATTESE)
    rel["prima"]["tutti_verdi"] = all(rel["prima"]["cancelli"].values())

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

    tmp = tempfile.mkdtemp(prefix="titolo01-", dir=os.environ.get("SCRATCH", None))
    try:
        lavoro = os.path.join(tmp, os.path.basename(a.rom))
        shutil.copy2(a.rom, lavoro)
        cambiati = applica(lavoro)
        n, lo, hi = diff_byte(a.rom, lavoro)
        rel["byte_cambiati"] = n
        rel["intervallo_byte"] = [lo, hi]
        rel["dimensione_invariata"] = os.path.getsize(a.rom) == os.path.getsize(lavoro)
        rel["cancelli_scrittura"] = {
            "A5_solo_56_byte": (n == 56 or (n == 0 and rel["prima"]["stato"] == "già-applicato")),
            "A5_byte_contigui": (lo is None or (hi - lo + 1) <= 56 + 2 * LARGHEZZA_MAPPA * 2),
            "A5_dimensione_invariata": rel["dimensione_invariata"],
        }
        # A6 — idempotenza
        rel["cancelli_scrittura"]["A6_idempotente"] = (applica(lavoro) == 0)
        rel["dopo"] = cancelli_lettura(lavoro)
        rel["dopo"]["cancelli"]["A7_membri_intoccabili"] = (
            rel["dopo"]["impronte_intoccabili"] == IMPRONTE_INTOCCABILI_ATTESE)
        rel["cancelli_scrittura"]["A2b_celle_azzerate"] = (rel["dopo"]["stato"] == "già-applicato")
        verde_ril, det = rilettore(lavoro)
        rel["rilettore"] = det
        rel["cancelli_scrittura"]["A8_rilettore_verde"] = verde_ril
        rel["sha256_uscita"] = sha256(lavoro)
        rel["sha256_ingresso"] = sha256(a.rom)
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
