#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""RILETTORE INDIPENDENTE — SGP-1.2-OPZIONI-04 (preparazione v2).

Non importa `applica_opzioni_v2.py` ne' `overlay_patch.py`: rilegge i byte
prodotti con un traduttore ARM9 scritto QUI, un decodificatore BLZ «in avanti
su buffer separato» scritto QUI (famiglia diversa dal decoder «all'indietro in
luogo» usato da `overlay_patch.py` per applicare) e un decodificatore di BL
Thumb-1 scritto da zero. Stessa disciplina di SGP-1.2-OPZIONI-02/tools/rileggi_opzioni.py,
di cui questo file NON e' una copia modificata ma una riscrittura per il
layout a DUE BLOCCHI della v2 (`PIANO-INIEZIONE.md` §1-2).

Cancelli:
  L1  i 4 B a 0x021E6820 (ov054) sono una BL il cui bersaglio == sgp_opz_hook
  L2  i 4 B a 0x021E5A34 e 0x021E5998 (ov036) valgono SGP_UI_TPL_ADDR e +16
  L3  sha256 di codice/tabella(lingua) in sgp.opzioni e di testi(lingua) in
      sgp.opzioni.testi == manifesto/build
  L4  lo stato (+0xF60, 96 B) e il margine fra stato e canarino (+0xFC0..+0xFF0,
      208 B) sono a zero all'iniezione
  L5  i DUE canarini (dentro ciascun blocco) sono intatti e i due blocchi non
      si sovrappongono fra loro ne' col resto della mappa (se data)
  L6  il resto di ov054 e ov036 decompressi e' identico all'ingresso (solo i
      ganci cambiano)
  L7  il resto dell'ARM9/riserva e' identico all'ingresso salvo i due blocchi
  L8  le risorse (+0xEC0, 84 B) coincidono con i 3 estratti dichiarati DI
      ov054 DELL'INGRESSO
  L9  ENTRAMBI i blocchi (sgp.opzioni e sgp.opzioni.testi) erano a ZERO
      nell'INGRESSO: e' il fatto che rende l'iniezione rifiutabile «per
      costruzione» su una ROM dove la v1 e' gia' applicata altrove, e qui si
      controlla che il rilettore veda la stessa storia dell'applicatore

Uso:
    rileggi_opzioni_v2.py <ingresso.nds> <derivata.nds> --build <dir> --lingua EN|IT \\
                          [--manifest MAPPA.json] [--json out.json]
"""
#
# ===========================================================================
# v3 — SGP-1.2-RIFINITURA-01. Derivato RIGA PER RIGA dall'omonimo strumento di
# SGP-1.2-OPZIONI-04 (che resta invariato e continua ad applicare la v2). Le
# uniche differenze volute:
#   1. la PIANTA del blocco. Il blocco resta lo stesso (0x023D9000, 4096 B) e
#      il canarino resta a +0xFF0: cambia il confine fra il codice e i dati di
#      servizio, perche' il codice della v3 e' 3652 B contro i 3412 della v2 e
#      3584 non bastavano piu'. I 208 B mai usati fra la fine dello stato e il
#      canarino diventano margine del codice:
#          codice +0x000 3776 · ris +0xEC0 96 · tab +0xF20 32
#          tpl    +0xF40   32 · stato +0xF60 96 · libero +0xFC0 48
#   2. gli offset di L4 e L8 seguono la nuova pianta.
# Tutto il resto — cancelli, ganci, preimmagini, canarini, --in-luogo — e'
# identico: se diverge, e' un difetto, non una variante.
# ===========================================================================

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


BLOCK_BASE, BLOCK_N = 0x023D9000, 4096
CANARY_OFF, N_CANARY = 0xFF0, 16
CANARY_MOTIVO = 0xCA5A1400

TESTI_BASE, TESTI_N = 0x023DA800, 1024
TESTI_CANARY_OFF = 0x3F0
TESTI_CANARY_MOTIVO = 0xCA5A1500

PIANTA = [("codice", 0x000, 0xEC0), ("ris", 0xEC0, 0x60), ("tab", 0xF20, 0x20),
          ("tpl", 0xF40, 0x20), ("stato", 0xF60, 0x60)]
MARGINE_OFF, MARGINE_N = 0xFC0, 0x30   # fra la fine di "stato" (0xFC0) e il canarino (0xFF0)

OV_A, SITO_A, PRE_A = 54, 0x021E6820, bytes.fromhex("041c898c")
OV_B, SITO_B1, SITO_B2 = 36, 0x021E5A34, 0x021E5998
RISORSE = [(0x021E6CD8, 40), (0x021E6C48, 16), (0x021E6E3C, 28)]


# ------------------------------------------------------------- traduttore ARM9
class Arm9RO:
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
                pretendi(dist <= len(fuori), "BLZ: distanza %d oltre i %d byte gia' prodotti" % (dist, len(fuori)))
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


def trova_overlay_per_ram(dati, t, ram_atteso):
    n_ov = t["y9_len"] // 32
    for oid in range(n_ov):
        e = leggi_overlay(dati, t, oid)
        if e["ram"] == ram_atteso and e["id"] == oid:
            yield oid, e


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("ingresso")
    ap.add_argument("derivata")
    ap.add_argument("--build", required=True)
    ap.add_argument("--lingua", required=True, choices=("EN", "IT"))
    ap.add_argument("--manifest")
    ap.add_argument("--json")
    ap.add_argument("--sostituisce", metavar="BUILD_PRECEDENTE",
                    help="l'INGRESSO ha gia' una versione precedente di questa stessa "
                         "pagina (i suoi artefatti stanno qui): L9 pretende allora che "
                         "l'ingresso contenga ESATTAMENTE quella versione, e L1/L2 "
                         "confrontano la preimmagine con i ganci di quella versione")
    a = ap.parse_args()

    esiti = []

    def esito(nome, ok_, dettaglio=""):
        esiti.append({"cancello": nome, "esito": "verde" if ok_ else "ROSSO", "dettaglio": dettaglio})
        print("  %-3s %-6s %s" % (nome, "verde" if ok_ else "ROSSO", dettaglio))
        return ok_

    tutto_verde = True

    man = json.loads((Path(a.build) / "manifesto.json").read_text())
    blob = (Path(a.build) / "ui_blob.bin").read_bytes()
    testi = (Path(a.build) / f"testi-{a.lingua}.bin").read_bytes()
    tab = (Path(a.build) / f"voci-{a.lingua}.bin").read_bytes()
    bersaglio = int(man["simboli"]["sgp_opz_hook"], 16) & ~1
    ind = {k: int(v, 16) for k, v in man["indirizzi"].items()}

    # v3 — sostituzione di una versione precedente della STESSA pagina. La
    # preimmagine attesa nell'ingresso non e' piu' quella vanilla: e' quella che
    # la versione precedente ci aveva scritto. Si ricava dai suoi artefatti, non
    # si scrive a mano.
    bersaglio_prec = None          # None = l'ingresso deve essere vanilla
    prec_blob = prec_testi = None
    if a.sostituisce:
        pman = json.loads((Path(a.sostituisce) / "manifesto.json").read_text())
        bersaglio_prec = int(pman["simboli"]["sgp_opz_hook"], 16) & ~1
        prec_blob = (Path(a.sostituisce) / "ui_blob.bin").read_bytes()
        prec_testi = (Path(a.sostituisce) / f"testi-{a.lingua}.bin").read_bytes()
    pretendi(ind["codice"] == BLOCK_BASE, "il manifesto non e' compilato per 0x%08X" % BLOCK_BASE)
    pretendi(ind["testi"] == TESTI_BASE, "il manifesto non e' compilato per 0x%08X (testi)" % TESTI_BASE)

    b = Arm9RO(a.ingresso)
    d = Arm9RO(a.derivata)

    # ---- L9: i due blocchi erano a zero nell'ingresso -----------------------
    if a.sostituisce:
        blocco_in = b.leggi(BLOCK_BASE, BLOCK_N)
        testi_in = b.leggi(TESTI_BASE, TESTI_N)
        tutto_verde &= esito("L9", blocco_in[:len(prec_blob)] == prec_blob
                             and testi_in[:len(prec_testi)] == prec_testi,
                             "l'ingresso conteneva ESATTAMENTE la versione precedente "
                             "dichiarata (codice %d B, testi %d B): e' quella che si "
                             "sostituisce" % (len(prec_blob), len(prec_testi)))
    else:
        tutto_verde &= esito("L9", b.leggi(BLOCK_BASE, BLOCK_N) == bytes(BLOCK_N)
                             and b.leggi(TESTI_BASE, TESTI_N) == bytes(TESTI_N),
                             "sgp.opzioni e sgp.opzioni.testi erano a zero nell'ingresso "
                             "(nessuna v1/v2 gia' presente li')")

    # ---- L3: sha256 di codice/tab(lingua) nel blocco 1, testi(lingua) nel 2 -
    letto_codice = d.leggi(BLOCK_BASE + 0x000, len(blob))
    letto_tab = d.leggi(BLOCK_BASE + 0xF20, len(tab))
    letto_testi = d.leggi(TESTI_BASE + 0x000, len(testi))
    ok_l3 = (sha(letto_codice) == sha(blob) and sha(letto_tab) == sha(tab) and sha(letto_testi) == sha(testi))
    tutto_verde &= esito("L3", ok_l3,
                         "codice=%s tab=%s testi(%s)=%s" %
                         (sha(letto_codice)[:12], sha(letto_tab)[:12], a.lingua, sha(letto_testi)[:12]))

    # ---- L4: stato (+0xF60, 96B) e margine (+0xFC0, 48B) a zero ------------
    stato = d.leggi(BLOCK_BASE + 0xF60, 0x60)
    margine = d.leggi(BLOCK_BASE + MARGINE_OFF, MARGINE_N)
    tutto_verde &= esito("L4", stato == bytes(0x60) and margine == bytes(MARGINE_N),
                         "stato e margine fra stato e canarino a zero all'iniezione")

    # ---- L5: i due canarini e non sovrapposizione ---------------------------
    canarino_atteso = b"".join(struct.pack("<I", CANARY_MOTIVO | i) for i in range(N_CANARY // 4))
    canarino = d.leggi(BLOCK_BASE + CANARY_OFF, N_CANARY)
    ok_can1 = esito("L5a", canarino == canarino_atteso, "canarino sgp.opzioni a 0x%08X" % (BLOCK_BASE + CANARY_OFF))
    canarino_t_atteso = b"".join(struct.pack("<I", TESTI_CANARY_MOTIVO | i) for i in range(N_CANARY // 4))
    canarino_t = d.leggi(TESTI_BASE + TESTI_CANARY_OFF, N_CANARY)
    ok_can2 = esito("L5b", canarino_t == canarino_t_atteso,
                    "canarino sgp.opzioni.testi a 0x%08X" % (TESTI_BASE + TESTI_CANARY_OFF))
    tutto_verde &= ok_can1 & ok_can2
    tutto_verde &= esito("L5c", BLOCK_BASE + BLOCK_N <= TESTI_BASE or TESTI_BASE + TESTI_N <= BLOCK_BASE,
                         "i due blocchi non si sovrappongono")
    if a.manifest:
        mappa = json.loads(Path(a.manifest).read_text())
        zone = [(BLOCK_BASE, BLOCK_N, {"sgp.opzioni"}), (TESTI_BASE, TESTI_N, {"sgp.opzioni.testi"})]
        sovrapposti = []
        for lo, hi_n, nomi in zone:
            hi = lo + hi_n
            for x in mappa["blocchi"]:
                if x["nome"] in nomi or x["nome"].startswith("libero"):
                    continue
                if int(x["base"], 16) < hi and int(x["base"], 16) + x.get("bytes", 0) > lo:
                    sovrapposti.append(x["nome"])
        tutto_verde &= esito("L5d", not sovrapposti, "sovrapposizioni con la mappa: %s" % sovrapposti)

    # ---- L7: resto dell'ARM9/riserva identico -------------------------------
    pretendi(b.off9 == d.off9 and b.siz9 == d.siz9, "L7: l'immagine arm9 ha cambiato offset/dimensione")
    diversi = [i for i in range(b.siz9) if b.raw[b.off9 + i] != d.raw[d.off9 + i]]
    leciti = set(range(b.off(BLOCK_BASE, BLOCK_N), b.off(BLOCK_BASE, BLOCK_N) + BLOCK_N)) | \
             set(range(b.off(TESTI_BASE, TESTI_N), b.off(TESTI_BASE, TESTI_N) + TESTI_N))
    fuori = [i for i in diversi if (b.off9 + i) not in leciti]
    if fuori:
        tutto_verde &= esito("L7", False, "%d byte arm9 diversi fuori dai due blocchi, primo a 0x%X"
                             % (len(fuori), b.off9 + fuori[0]))
    else:
        tutto_verde &= esito("L7", True, "%d byte diversi, tutti dentro i due blocchi (4096+1024)" % len(diversi))

    # ---- overlay: L1, L2, L6, L8 --------------------------------------------
    tb, tdd = tabelle(b.raw), tabelle(d.raw)

    trovati_b54 = list(trova_overlay_per_ram(b.raw, tb, 0x021E5900))
    cand54 = [(oid, e) for oid, e in trovati_b54 if oid == OV_A]
    pretendi(len(cand54) == 1, "overlay %d non trovato per id/ram nell'ingresso" % OV_A)
    _, eb54 = cand54[0]
    img_b54 = immagine_overlay(b.raw, eb54)
    off_a = SITO_A - eb54["ram"]
    if bersaglio_prec is None:
        pretendi(img_b54[off_a:off_a + 4] == PRE_A,
                 "l'ingresso non ha piu' la preimmagine A attesa")
    else:
        # Sostituzione: nell'ingresso il sito A deve essere la BL della versione
        # PRECEDENTE, e nient'altro. Si decodifica invece di ri-codificare: cosi'
        # il rilettore non condivide con l'applicatore nemmeno il codificatore.
        pretendi(bl_decode(SITO_A, bytes(img_b54[off_a:off_a + 4])) == bersaglio_prec,
                 "l'ingresso non ha il gancio A della versione precedente "
                 "(atteso un BL verso %#010x)" % bersaglio_prec)

    ed54 = leggi_overlay(d.raw, tdd, OV_A)
    img_d54 = immagine_overlay(d.raw, ed54)
    pretendi(len(img_d54) == len(img_b54), "ov054 cambia dimensione decompressa: %d -> %d" % (len(img_b54), len(img_d54)))

    quattro_a = img_d54[off_a:off_a + 4]
    bersaglio_a = bl_decode(SITO_A, quattro_a)
    tutto_verde &= esito("L1", bersaglio_a == bersaglio,
                         "0x%08X -> %s (atteso %s)" % (SITO_A, hex(bersaglio_a) if bersaglio_a is not None else "non-BL", hex(bersaglio)))

    diff54 = [i for i in range(len(img_b54)) if img_b54[i] != img_d54[i]]
    inattesi54 = [i for i in diff54 if i not in range(off_a, off_a + 4)]
    if inattesi54:
        tutto_verde &= esito("L6a", False, "%d byte diversi in ov054 FUORI dal gancio, primo a +0x%X"
                             % (len(inattesi54), inattesi54[0]))
    else:
        # v3: l'invariante e' «nessun byte cambia FUORI dalla finestra del
        # gancio», non «cambiano esattamente quattro byte». Sostituendo una
        # versione precedente, la vecchia e la nuova BL condividono dei byte e i
        # diversi sono meno di quattro: la v2 dava ROSSO qui per un motivo che
        # non era un difetto. Si pretende comunque che la finestra sia cambiata,
        # altrimenti il gancio non e' stato riscritto affatto.
        tutto_verde &= esito("L6a", not inattesi54 and len(diff54) > 0,
                             "i soli byte diversi in ov054 stanno nei 4 B del gancio A "
                             "(%d diversi su 4)" % len(diff54))

    ris_atteso = b"".join(bytes(img_b54[ram - eb54["ram"]: ram - eb54["ram"] + n]) for ram, n in RISORSE)
    ris_letto = d.leggi(BLOCK_BASE + 0xEC0, len(ris_atteso))
    tutto_verde &= esito("L8", ris_letto == ris_atteso,
                         "%d B di risorse letti dal blocco == estratti da ov054 dell'ingresso" % len(ris_atteso))

    trovati_b36 = list(trova_overlay_per_ram(b.raw, tb, 0x021E5900))
    cand36 = [(oid, e) for oid, e in trovati_b36 if oid == OV_B]
    pretendi(len(cand36) == 1, "overlay %d non trovato per id/ram nell'ingresso" % OV_B)
    _, eb36 = cand36[0]
    img_b36 = immagine_overlay(b.raw, eb36)
    off_b1 = SITO_B1 - eb36["ram"]
    off_b2 = SITO_B2 - eb36["ram"]

    ed36 = leggi_overlay(d.raw, tdd, OV_B)
    img_d36 = immagine_overlay(d.raw, ed36)
    pretendi(len(img_d36) == len(img_b36), "ov036 cambia dimensione decompressa: %d -> %d" % (len(img_b36), len(img_d36)))

    tpl0, tpl1 = ind["tpl"], ind["tpl"] + 16
    v_b1 = struct.unpack_from("<I", img_d36, off_b1)[0]
    v_b2 = struct.unpack_from("<I", img_d36, off_b2)[0]
    tutto_verde &= esito("L2", v_b1 == tpl0 and v_b2 == tpl1,
                         "B1=0x%08X (atteso 0x%08X) B2=0x%08X (atteso 0x%08X)" % (v_b1, tpl0, v_b2, tpl1))

    diff36 = [i for i in range(len(img_b36)) if img_b36[i] != img_d36[i]]
    finestre36 = set(range(off_b1, off_b1 + 4)) | set(range(off_b2, off_b2 + 4))
    inattesi36 = [i for i in diff36 if i not in finestre36]
    if inattesi36:
        tutto_verde &= esito("L6b", False, "%d byte diversi in ov036 FUORI dai due ganci, primo a +0x%X"
                             % (len(inattesi36), inattesi36[0]))
    else:
        tutto_verde &= esito("L6b", set(diff36).issubset(finestre36) and len(diff36) > 0,
                             "%d byte diversi in ov036, tutti dentro le finestre degli 8 B di B1/B2" % len(diff36))

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
