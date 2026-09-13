#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""RILETTORE INDIPENDENTE — SGP-1.2-PRESTAZIONI-NPC-02.

Non importa `applica_npc.py` ne' `overlay_patch.py`: rilegge i byte prodotti
con un traduttore ARM9 scritto qui, un decodificatore BLZ scritto QUI (decoder
«in avanti su buffer separato», di famiglia diversa dal decoder «all'indietro
in luogo» usato da `overlay_patch.py` per applicare — stessa idea del decoder
B di `SGP-1.2-OVERLAY-01/tools/overlay_rileggi.py`) e un decodificatore di BL
Thumb-1 scritto da zero. Se i due strumenti condividessero un errore, non
sarebbe perche' condividono il codice.

Cancelli (CRITERI.md §3, numerati come PIANO-INIEZIONE.md §3):
  L1  i 4 B a 0x021FA570 sono una BL il cui bersaglio == sgp_npc_hook (manifesto)
  L2  i 100 B di codice hanno lo sha256 del blob compilato
  L3  i byte `e0 30 00 68` (istruzioni sostituite) compaiono dentro la trampolina
  L4  lo stato ha guardia==0x5A; riporta tetto e il SEME di attivo (fase 02b:
      il gancio lo sovrascrive a runtime dal chunk D1, questo cancello e'
      statico e vede solo il valore scritto dall'applicatore all'iniezione)
  L5  il canarino e' intatto e il blocco non si sovrappone a nessun altro (mappa, se data)
  L6  il resto dell'overlay 1 decompresso e' identico all'ingresso (solo i 4 B del gancio cambiano)
  L7  l'ARM9/riserva e' identico all'ingresso salvo i 256+16 B del blocco+canarino
  L8  (fuori da questo script: si esegue su EN e IT e si confrontano gli esiti)

Uso:
    rileggi_npc.py <ingresso.nds> <derivata.nds> --build <dir> [--manifest MAPPA.json] [--json out.json]
"""
import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path


class Rosso(Exception):
    pass


def pretendi(c, m):
    if not c:
        raise Rosso(m)


def sha(b):
    return hashlib.sha256(bytes(b)).hexdigest()


BLOCK_BASE, BLOCK_N = 0x023D8900, 0x100
OFF_BLOB, N_BLOB_SLOT = 0x000, 0x0E0
OFF_STATO, N_STATO = 0x0E0, 16
CANARY_BASE, N_CANARY = BLOCK_BASE + BLOCK_N, 16
CANARY_MOTIVO = 0xCA5A1300

OV_CAMPO = 1
A_CONTESTO = 0x021FA564
PRE_CONTESTO = bytes.fromhex("f8b500910121009809024458")
A_GANCIO = 0x021FA570
PRE_GANCIO = bytes.fromhex("e0300068")


# ------------------------------------------------------------- traduttore ARM9
class Arm9RO:
    """Scritto da zero per questo rilettore: cammina i module params a 0xBA0,
    esattamente come il caricatore del gioco (indipendente da `tools/arm9.py`,
    che l'applicatore usa per SCRIVERE)."""

    def __init__(self, path):
        self.raw = Path(path).read_bytes()
        self.off9 = struct.unpack_from("<I", self.raw, 0x20)[0]
        self.ram9 = struct.unpack_from("<I", self.raw, 0x28)[0]
        self.siz9 = struct.unpack_from("<I", self.raw, 0x2C)[0]
        tab0, tab1, dati0 = struct.unpack_from("<3I", self.raw, self.off9 + 0xBA0)
        self.segmenti = [(self.ram9, self.off9, dati0 - self.ram9)]
        p = self.off9 + (tab0 - self.ram9)
        fine = self.off9 + (tab1 - self.ram9)
        off = self.off9 + (dati0 - self.ram9)
        while p < fine:
            ram, size, _bss = struct.unpack_from("<3I", self.raw, p)
            self.segmenti.append((ram, off, size))
            off += size
            p += 12

    def off(self, ram, n=1):
        for base, o, size in self.segmenti:
            if base <= ram and ram + n <= base + size:
                return o + (ram - base)
        raise Rosso("0x%08X+%d non e' dentro nessun segmento ARM9" % (ram, n))

    def leggi(self, ram, n):
        o = self.off(ram, n)
        return bytes(self.raw[o:o + n])


# ------------------------------------------------------------------ BL Thumb
def bl_decode(sito, quattro_byte):
    hi, lo = struct.unpack("<HH", quattro_byte)
    if hi & 0xF800 != 0xF000 or lo & 0xF800 != 0xF800:
        return None
    addend = ((hi & 0x7FF) << 12) | ((lo & 0x7FF) << 1)
    if addend & 0x400000:
        addend -= 0x800000
    return (sito + 4 + addend) & 0xFFFFFFFE


# --------------------------------------------------- BLZ, decoder «in avanti»
def blz_forward(flusso):
    """Decoder scritto da zero: rovescia la parte codificata e la legge come
    un LZ77 IN AVANTI su un buffer separato (mai in luogo), poi rovescia il
    risultato. Verifica anche l'invariante che il gioco esige (distanza <=
    byte gia' prodotti): un flusso che la violasse non sarebbe decomprimibile
    in luogo dal vero decodificatore della NitroSDK."""
    n = len(flusso)
    pretendi(n >= 8 and n % 4 == 0, "BLZ: lunghezza %d non plausibile" % n)
    w0, w1 = struct.unpack("<II", flusso[n - 8:n])
    hdr_len = w0 >> 24
    enc_len = w0 & 0xFFFFFF
    inc_len = w1
    pretendi(8 <= hdr_len <= 11, "BLZ: hdr_len %d fuori da [8,11]" % hdr_len)
    pretendi(hdr_len <= enc_len <= n, "BLZ: enc_len %d incoerente con n=%d" % (enc_len, n))
    prefisso = flusso[:n - enc_len]
    zona = flusso[n - enc_len:n - hdr_len]
    finale = n + inc_len

    z = bytes(reversed(zona))
    attesi = finale - len(prefisso)
    fuori = bytearray()
    i = 0
    while len(fuori) < attesi:
        pretendi(i < len(z), "BLZ: flusso finito prima dell'immagine (%d/%d)" % (len(fuori), attesi))
        flag = z[i]
        i += 1
        for bit in range(8):
            if len(fuori) >= attesi:
                break
            if flag & (0x80 >> bit):
                pretendi(i + 1 < len(z), "BLZ: coppia troncata")
                b1, b2 = z[i], z[i + 1]
                i += 2
                dist = (((b1 & 0x0F) << 8) | b2) + 3
                lung = (b1 >> 4) + 3
                pretendi(dist <= len(fuori),
                         "BLZ: distanza %d oltre i %d byte gia' prodotti" % (dist, len(fuori)))
                p = len(fuori) - dist
                for k in range(lung):
                    fuori.append(fuori[p + k])
            else:
                pretendi(i < len(z), "BLZ: letterale troncato")
                fuori.append(z[i])
                i += 1
    pretendi(len(fuori) == attesi, "BLZ: prodotti %d byte invece di %d" % (len(fuori), attesi))
    return prefisso + bytes(reversed(fuori))


def tabelle(dati):
    p = lambda o: struct.unpack_from("<I", dati, o)[0]
    return {"fat": p(0x48), "fat_len": p(0x4C), "y9": p(0x50), "y9_len": p(0x54)}


def leggi_overlay(dati, t, oid):
    off = t["y9"] + oid * 32
    campi = struct.unpack_from("<8I", dati, off)
    e = {"id": campi[0], "ram": campi[1], "ram_size": campi[2], "file_id": campi[6],
         "flag": campi[7] >> 24, "dim": campi[7] & 0xFFFFFF, "voce": off}
    fo = t["fat"] + e["file_id"] * 8
    s, fi = struct.unpack_from("<II", dati, fo)
    e["fat_voce"], e["inizio"], e["fine"] = fo, s, fi
    return e


def immagine_overlay(dati, e):
    corpo = dati[e["inizio"]:e["fine"]]
    if e["flag"] & 1:
        pretendi(e["dim"] <= len(corpo), "y9 dichiara %d B compressi, la FAT ne da' %d" % (e["dim"], len(corpo)))
        return blz_forward(bytes(corpo[:e["dim"]]))
    return bytes(corpo)


def trova_overlay_per_guardia(dati, t, addr, hx):
    n_ov = t["y9_len"] // 32
    trovati = []
    for oid in range(n_ov):
        e = leggi_overlay(dati, t, oid)
        if not (e["ram"] <= addr and addr + len(hx) <= e["ram"] + e["ram_size"]):
            continue
        try:
            img = immagine_overlay(dati, e)
        except Rosso:
            continue
        off = addr - e["ram"]
        if img[off:off + len(hx)] == hx:
            trovati.append((oid, e, img))
    return trovati


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("ingresso")
    ap.add_argument("derivata")
    ap.add_argument("--build", required=True)
    ap.add_argument("--manifest")
    ap.add_argument("--json")
    a = ap.parse_args()

    esiti = []

    def esito(nome, ok_, dettaglio=""):
        esiti.append({"cancello": nome, "esito": "verde" if ok_ else "ROSSO", "dettaglio": dettaglio})
        print("  %-3s %-6s %s" % (nome, "verde" if ok_ else "ROSSO", dettaglio))
        return ok_

    tutto_verde = True

    man = json.loads((Path(a.build) / "manifesto.json").read_text())
    blob = (Path(a.build) / "blob.bin").read_bytes()
    bersaglio = int(man["simboli"]["sgp_npc_hook"], 16) & ~1

    d = Arm9RO(a.derivata)
    b = Arm9RO(a.ingresso)

    # ---- L2: sha256 del codice a 0x023D8900 -------------------------------
    codice = d.leggi(BLOCK_BASE + OFF_BLOB, len(blob))
    tutto_verde &= esito("L2", sha(codice) == sha(blob), "sha256 blob = %s" % sha(codice)[:16])

    # ---- L4: stato -----------------------------------------------------
    stato = d.leggi(BLOCK_BASE + OFF_STATO, N_STATO)
    guardia_ok = stato[2] == 0x5A
    tutto_verde &= esito("L4", guardia_ok,
                         "seme_attivo=%d tetto=%d guardia=0x%02X" % (stato[0], stato[1], stato[2]))

    # ---- resto del blocco (padding fra codice e stato, margine finale) a zero
    padding_ok = d.leggi(BLOCK_BASE + len(blob), OFF_STATO - len(blob)) == bytes(OFF_STATO - len(blob)) and \
        d.leggi(BLOCK_BASE + OFF_STATO + N_STATO, BLOCK_N - OFF_STATO - N_STATO) == bytes(BLOCK_N - OFF_STATO - N_STATO)
    tutto_verde &= esito("L4b", padding_ok, "padding del blocco fuori da blob+stato e' a zero")

    # ---- L5: canarino e non sovrapposizione -------------------------------
    canarino_atteso = b"".join(struct.pack("<I", CANARY_MOTIVO | i) for i in range(N_CANARY // 4))
    canarino = d.leggi(CANARY_BASE, N_CANARY)
    tutto_verde &= esito("L5", canarino == canarino_atteso, "canarino a 0x%08X" % CANARY_BASE)
    if a.manifest:
        mappa = json.loads(Path(a.manifest).read_text())
        lo, hi = BLOCK_BASE, CANARY_BASE + N_CANARY
        sovrapposti = [x["nome"] for x in mappa["blocchi"]
                       if x["nome"] not in ("sgp.npc", "canarino.npc", "libero.1.2")
                       and int(x["base"], 16) < hi and int(x["base"], 16) + x.get("bytes", 0) > lo]
        tutto_verde &= esito("L5b", not sovrapposti, "sovrapposizioni con la mappa: %s" % sovrapposti)

    # ---- L7: resto dell'ARM9/riserva identico -----------------------------
    pretendi(b.off9 == d.off9 and b.siz9 == d.siz9, "L7: l'immagine arm9 ha cambiato offset/dimensione")
    diversi = [i for i in range(b.siz9) if b.raw[b.off9 + i] != d.raw[d.off9 + i]]
    leciti = set(range(b.off(BLOCK_BASE, BLOCK_N), b.off(BLOCK_BASE, BLOCK_N) + BLOCK_N)) | \
             set(range(b.off(CANARY_BASE, N_CANARY), b.off(CANARY_BASE, N_CANARY) + N_CANARY))
    fuori = [i for i in diversi if (b.off9 + i) not in leciti]
    if fuori:
        tutto_verde &= esito("L7", False, "%d byte arm9 diversi fuori dal blocco dichiarato, primo a 0x%X"
                             % (len(fuori), b.off9 + fuori[0]))
    else:
        tutto_verde &= esito("L7", True, "%d byte diversi, tutti dentro blocco (256) + canarino (16)" % len(diversi))

    # ---- overlay: L1, L3, L6 ------------------------------------------------
    tb = tabelle(b.raw)
    tdd = tabelle(d.raw)
    trovati_b = trova_overlay_per_guardia(b.raw, tb, A_CONTESTO, PRE_CONTESTO)
    pretendi(len(trovati_b) == 1, "l'ingresso non ha un overlay unico con quel contesto: %s" % [t[0] for t in trovati_b])
    oid, eb, img_b = trovati_b[0]
    pretendi(oid == OV_CAMPO, "l'overlay individuato (%d) non e' quello atteso (%d)" % (oid, OV_CAMPO))

    ed = leggi_overlay(d.raw, tdd, oid)
    img_d = immagine_overlay(d.raw, ed)
    pretendi(len(img_d) == len(img_b), "l'immagine dell'overlay cambia dimensione: %d -> %d" % (len(img_b), len(img_d)))

    off_g = A_GANCIO - ed["ram"]
    quattro = img_d[off_g:off_g + 4]
    t = bl_decode(A_GANCIO, quattro)
    tutto_verde &= esito("L1", t == bersaglio,
                         "0x%08X -> %s (atteso %s)" % (A_GANCIO, hex(t) if t is not None else "non-BL", hex(bersaglio)))

    # L3: le due istruzioni sostitute compaiono dentro la trampolina (nel blob)
    tutto_verde &= esito("L3", PRE_GANCIO in codice, "e0 30 00 68 presente nella trampolina")

    # L6: tutto il resto dell'overlay decompresso e' identico
    diff_ov = [i for i in range(len(img_b)) if img_b[i] != img_d[i]]
    inattesi_ov = [i for i in diff_ov if i not in range(off_g, off_g + 4)]
    if inattesi_ov:
        tutto_verde &= esito("L6", False, "%d byte diversi nell'overlay FUORI dal gancio, primo a +0x%X"
                             % (len(inattesi_ov), inattesi_ov[0]))
    else:
        tutto_verde &= esito("L6", diff_ov == list(range(off_g, off_g + 4)),
                             "solo i 4 B del gancio cambiano (%d byte diversi totali)" % len(diff_ov))

    print("ESITO FINALE:", "verde" if tutto_verde else "ROSSO")
    if a.json:
        Path(a.json).write_text(json.dumps({"esito_finale": "verde" if tutto_verde else "ROSSO",
                                            "cancelli": esiti}, indent=2, ensure_ascii=False) + "\n")
    return 0 if tutto_verde else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Rosso as e:
        print("ROSSO: %s" % e, file=sys.stderr)
        sys.exit(3)
