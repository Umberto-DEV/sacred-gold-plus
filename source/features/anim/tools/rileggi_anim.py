#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""RILETTORE INDIPENDENTE — SGP-1.2-ANIM-B-02.

Non importa `applica_anim.py` ne' `overlay_patch.py`: rilegge i byte prodotti
con un traduttore ARM9 scritto qui, un decodificatore BLZ scritto QUI
(decoder «in avanti su buffer separato», famiglia diversa dal decoder
«all'indietro in luogo» usato da `overlay_patch.py` per applicare — stessa
idea di `SGP-1.2-PRESTAZIONI-NPC-02/tools/rileggi_npc.py`).

Cancelli (CRITERI.md §3):
  L1  il letterale a 0x0226200C e' il puntatore al blob (base|1): bit Thumb
      acceso, e il primo halfword del blob e' un `push {..,lr}` Thumb
      (0xB4xx con bit8 acceso) — non basta un valore qualunque con bit0=1
  L2  i byte del blob (fino a 0x2F0) hanno lo sha256 del blob compilato
  L3  il canarino (16 B a +0x2F0) e' intatto
  L4  lo stato (+0x340, 64 B) ha guardia==0x5A; riporta `flags`
  L4b il margine del blocco fuori da blob+canarino+tabelle+stato+slot e' zero
      (qui: [len(blob), 0x2F0), cioe' fra la fine del blob e il canarino)
  L5  (se mappa data) nessuna voce registrata si sovrappone al blocco
  L6  il resto dell'overlay 12 decompresso e' identico all'ingresso: SOLO i
      4 B del gancio a 0x0226200C cambiano (la firma del corpo vanilla a
      0x0226203C, 90 B, e la priorita' a 0x02262010 restano intatte)
  L7  il resto dell'ARM9/riserva e' identico all'ingresso: SOLO i 1024 B del
      blocco sgp.anim cambiano
  L8  (fuori da questo script: si esegue su EN e IT e si confrontano gli esiti)

Uso:
    rileggi_anim.py <ingresso.nds> <derivata.nds> --build <dir> [--manifest MAPPA.json] [--json out.json]
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


BLOCK_BASE, BLOCK_N = 0x023D8B00, 0x400
OFF_CODICE, MAX_CODICE = 0x000, 0x2F0
OFF_CANARINO, N_CANARINO = 0x2F0, 16
OFF_TABELLE = 0x300
OFF_STATO, N_STATO = 0x340, 64
OFF_SLOT, N_SLOT = 0x380, 128

OV_CAMPO = 12
A_GANCIO = 0x0226200C
PRE_GANCIO = bytes.fromhex("3d202602")
A_GUARDIA_CORPO = 0x0226203C
PRE_GUARDIA_CORPO_SHA = "0b247d4c37cd35bd205e6cd51ef496a0ced83064ad58060ccaf473e001c28883"
A_PRIORITA = 0x02262010
PRE_PRIORITA = bytes.fromhex("f2030000")


# ------------------------------------------------------------- traduttore ARM9
class Arm9RO:
    """Scritto da zero per questo rilettore: cammina i module params a 0xBA0,
    indipendente da `tools/arm9.py` (che l'applicatore usa per SCRIVERE)."""

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


# --------------------------------------------------- BLZ, decoder «in avanti»
def blz_forward(flusso):
    """Decoder scritto da zero: rovescia la parte codificata e la legge come
    un LZ77 IN AVANTI su un buffer separato (mai in luogo), poi rovescia il
    risultato. Verifica anche l'invariante che il gioco esige (distanza <=
    byte gia' prodotti)."""
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


def trova_overlay_per_guardie(dati, t, guardie):
    """Sceglie l'overlay SOLO per contenuto (mai per indirizzo): tutte le
    guardie devono combaciare nello stesso overlay."""
    n_ov = t["y9_len"] // 32
    trovati = []
    for oid in range(n_ov):
        e = leggi_overlay(dati, t, oid)
        ok = True
        img = None
        for addr, hx in guardie:
            if not (e["ram"] <= addr and addr + len(hx) <= e["ram"] + e["ram_size"]):
                ok = False
                break
            if img is None:
                try:
                    img = immagine_overlay(dati, e)
                except Rosso:
                    ok = False
                    break
            off = addr - e["ram"]
            if img[off:off + len(hx)] != hx:
                ok = False
                break
        if ok:
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
        print("  %-4s %-6s %s" % (nome, "verde" if ok_ else "ROSSO", dettaglio))
        return ok_

    tutto_verde = True

    man = json.loads((Path(a.build) / "manifesto.json").read_text())
    blob = (Path(a.build) / "blob.bin").read_bytes()
    canarino_atteso = (Path(a.build) / "canarino.bin").read_bytes()
    bersaglio = int(man["simboli"]["sgp_idle_task2"], 16)

    d = Arm9RO(a.derivata)
    b = Arm9RO(a.ingresso)

    # ---- L2: sha256 del codice a 0x023D8B00 -------------------------------
    codice = d.leggi(BLOCK_BASE + OFF_CODICE, len(blob))
    tutto_verde &= esito("L2", sha(codice) == sha(blob), "sha256 blob = %s" % sha(codice)[:16])

    # ---- L3: canarino -------------------------------------------------
    canarino = d.leggi(BLOCK_BASE + OFF_CANARINO, N_CANARINO)
    tutto_verde &= esito("L3", canarino == canarino_atteso,
                         "canarino a 0x%08X" % (BLOCK_BASE + OFF_CANARINO))

    # ---- L4: stato -----------------------------------------------------
    stato = d.leggi(BLOCK_BASE + OFF_STATO, N_STATO)
    guardia_ok = stato[1] == 0x5A
    tutto_verde &= esito("L4", guardia_ok, "flags=0x%02X guardia=0x%02X" % (stato[0], stato[1]))

    # ---- L4b: margine fra fine blob e canarino, a zero ---------------------
    margine = d.leggi(BLOCK_BASE + len(blob), OFF_CANARINO - len(blob))
    tutto_verde &= esito("L4b", margine == bytes(len(margine)),
                         "%d B fra blob e canarino a zero" % len(margine))

    # ---- L5: non sovrapposizione con la mappa, se data ---------------------
    if a.manifest:
        mappa = json.loads(Path(a.manifest).read_text())
        lo, hi = BLOCK_BASE, BLOCK_BASE + BLOCK_N
        sovrapposti = [x["nome"] for x in mappa["blocchi"]
                       if x["nome"] not in ("sgp.anim", "libero.1.2")
                       and int(x["base"], 16) < hi and int(x["base"], 16) + x.get("bytes", 0) > lo]
        tutto_verde &= esito("L5", not sovrapposti, "sovrapposizioni con la mappa: %s" % sovrapposti)

    # ---- L7: resto dell'ARM9/riserva identico -----------------------------
    pretendi(b.off9 == d.off9 and b.siz9 == d.siz9, "L7: l'immagine arm9 ha cambiato offset/dimensione")
    diversi = [i for i in range(b.siz9) if b.raw[b.off9 + i] != d.raw[d.off9 + i]]
    leciti = set(range(b.off(BLOCK_BASE, BLOCK_N), b.off(BLOCK_BASE, BLOCK_N) + BLOCK_N))
    fuori = [i for i in diversi if (b.off9 + i) not in leciti]
    if fuori:
        tutto_verde &= esito("L7", False, "%d byte arm9 diversi fuori dal blocco dichiarato, primo a 0x%X"
                             % (len(fuori), b.off9 + fuori[0]))
    else:
        tutto_verde &= esito("L7", True, "%d byte diversi, tutti dentro il blocco (1024 B)" % len(diversi))

    # ---- overlay: L1, L6 (scelta SOLO per guardia doppia) -------------------
    tb = tabelle(b.raw)
    tdd = tabelle(d.raw)
    guardie_ingresso = [(A_GANCIO, PRE_GANCIO)]
    trovati_b = trova_overlay_per_guardie(b.raw, tb, guardie_ingresso)
    # sull'ingresso il letterale non e' ancora toccato: ci aspettiamo PIU' di
    # un candidato per indirizzo (5, CONTRATTO-A1B.md §1.2) ma la seconda
    # guardia (firma del corpo vanilla) lo restringe a uno solo.
    trovati_b = [t for t in trovati_b if sha(t[2][A_GUARDIA_CORPO - t[1]["ram"]:
                                                A_GUARDIA_CORPO - t[1]["ram"] + 90]) == PRE_GUARDIA_CORPO_SHA]
    pretendi(len(trovati_b) == 1, "l'ingresso non ha un overlay unico con quella firma: %s" % [t[0] for t in trovati_b])
    oid, eb, img_b = trovati_b[0]
    pretendi(oid == OV_CAMPO, "l'overlay individuato (%d) non e' quello atteso (%d)" % (oid, OV_CAMPO))

    ed = leggi_overlay(d.raw, tdd, oid)
    img_d = immagine_overlay(d.raw, ed)
    pretendi(len(img_d) == len(img_b), "l'immagine dell'overlay cambia dimensione: %d -> %d" % (len(img_b), len(img_d)))

    off_g = A_GANCIO - ed["ram"]
    quattro = img_d[off_g:off_g + 4]
    valore = struct.unpack("<I", quattro)[0]
    thumb_ok = valore & 1 == 1
    primo_half = struct.unpack_from("<H", codice, 0)[0]
    push_lr_ok = (primo_half & 0xFE00) == 0xB400 and (primo_half & 0x0100) != 0
    tutto_verde &= esito("L1", valore == bersaglio and thumb_ok and push_lr_ok,
                         "0x%08X -> 0x%08X (atteso 0x%08X), bit_thumb=%d, primo_halfword=0x%04X e' push{..,lr}=%s"
                         % (A_GANCIO, valore, bersaglio, thumb_ok, primo_half, push_lr_ok))

    # L6: il resto dell'overlay decompresso e' identico (incluse priorita' e
    # firma del corpo vanilla, controllate esplicitamente)
    off_p = A_PRIORITA - ed["ram"]
    priorita_ok = img_d[off_p:off_p + 4] == PRE_PRIORITA
    off_corpo = A_GUARDIA_CORPO - ed["ram"]
    corpo_ok = sha(img_d[off_corpo:off_corpo + 90]) == PRE_GUARDIA_CORPO_SHA
    diff_ov = [i for i in range(len(img_b)) if img_b[i] != img_d[i]]
    inattesi_ov = [i for i in diff_ov if i not in range(off_g, off_g + 4)]
    if inattesi_ov or not priorita_ok or not corpo_ok:
        tutto_verde &= esito("L6", False, "priorita_intatta=%s corpo_intatto=%s, %d byte diversi FUORI dal gancio"
                             % (priorita_ok, corpo_ok, len(inattesi_ov)))
    else:
        # non tutti e 4 i byte del letterale devono necessariamente cambiare
        # (l'ultimo byte, 0x02, puo' restare identico per coincidenza fra
        # preimmagine e postimmagine): il cancello vero e' che NESSUN byte
        # diverso cada FUORI dai 4 del gancio (gia' verificato sopra, "inattesi_ov"),
        # e che ne cambi almeno uno (altrimenti la patch non sarebbe stata scritta).
        tutto_verde &= esito("L6", 1 <= len(diff_ov) <= 4,
                             "%d byte diversi, tutti dentro i 4 del gancio (+0x%X..+0x%X); priorita' e corpo vanilla intatti"
                             % (len(diff_ov), off_g, off_g + 4))

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
