#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SGP-1.2-OVERLAY-01 — RILETTORE INDIPENDENTE.

Riapre una ROM gia' prodotta, ritrova l'overlay, lo decomprime con un
decodificatore **scritto separatamente** da quello dell'applicatore e verifica
le postimmagini; poi controlla che header, FAT e tabella y9 siano coerenti fra
loro e con i byte del file.

*Non importa niente da `overlay_patch.py`*: nessuna costante, nessuna funzione.
Se i due strumenti hanno lo stesso errore, non e' perche' lo condividono.

Il decodificatore qui dentro e' di famiglia diversa: invece di decomprimere
all'indietro e in luogo come fa il gioco, **rovescia** la regione codificata e
la legge come un LZ77 in avanti su un buffer separato, poi rovescia il
risultato. In piu' verifica, con un conto suo, l'invariante che il gioco esige e
che un decodificatore su buffer separato non vedrebbe mai: **la destinazione non
deve mai scendere sotto la sorgente**, cioe' il flusso dev'essere decomprimibile
*in luogo*.

Uso:
    overlay_rileggi.py --rom prodotta.nds --overlay 12 \\
        --guardia 0x0226203C:38b5... --post 0x0226200C:a5ce2302 \\
        [--ingresso base.nds] [--json ricevuta.json]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path


class Rosso(Exception):
    """Il rilettore dice rosso."""


def pretendi(c, m):
    if not c:
        raise Rosso(m)


def impronta(b):
    return hashlib.sha256(bytes(b)).hexdigest()


# --------------------------------------------------------- CRC16 (bit a bit)
def crc16_header(dati):
    """Stesso CRC16 dell'header di cartuccia, scritto bit a bit invece che a
    nibble: se la tabella dell'applicatore fosse sbagliata, qui non lo sarebbe."""
    reg = 0xFFFF
    for b in dati:
        reg ^= b
        for _ in range(8):
            if reg & 1:
                reg = (reg >> 1) ^ 0xA001
            else:
                reg >>= 1
    return reg & 0xFFFF


# ------------------------------------------------------- decodificatore «B»
def srotola_blz(flusso):
    """Ritorna (immagine, diagnostica). Solleva Rosso se il flusso e' malformato
    o non decomprimibile in luogo."""
    n = len(flusso)
    pretendi(n >= 8 and n % 4 == 0, "BLZ: lunghezza %d non plausibile" % n)
    w0, w1 = struct.unpack("<II", flusso[n - 8:n])
    testa = w0 >> 24
    codificato = w0 & 0xFFFFFF
    aumento = w1
    pretendi(8 <= testa <= 11, "BLZ: hdr_len %d fuori da [8,11]" % testa)
    pretendi(testa <= codificato <= n, "BLZ: enc_len %d incoerente con n=%d" % (codificato, n))
    prefisso = flusso[:n - codificato]
    zona = flusso[n - codificato:n - testa]
    finale = n + aumento

    # rovesciata, `zona` e' una sequenza LZ77 in avanti
    z = bytes(reversed(zona))
    attesi = finale - len(prefisso)
    fuori = bytearray()
    i = 0
    # conti per l'invariante «in luogo»: nel gioco la sorgente scende da
    # (n - testa) e la destinazione da `finale`; qui li seguiamo a ritroso.
    src = n - testa
    dst = finale
    minimo_margine = dst - src
    while len(fuori) < attesi:
        pretendi(i < len(z), "BLZ: flusso finito prima dell'immagine (%d/%d)" % (len(fuori), attesi))
        flag = z[i]
        i += 1
        src -= 1
        for bit in range(8):
            if len(fuori) >= attesi:
                break
            if flag & (0x80 >> bit):
                pretendi(i + 1 < len(z), "BLZ: coppia troncata")
                b1, b2 = z[i], z[i + 1]
                i += 2
                src -= 2
                dist = (((b1 & 0x0F) << 8) | b2) + 3
                lung = (b1 >> 4) + 3
                pretendi(dist <= len(fuori),
                         "BLZ: distanza %d oltre i %d byte gia' prodotti "
                         "(il flusso riferisce byte MAI scritti)" % (dist, len(fuori)))
                p = len(fuori) - dist
                for k in range(lung):
                    fuori.append(fuori[p + k])
                dst -= lung
            else:
                pretendi(i < len(z), "BLZ: letterale troncato")
                fuori.append(z[i])
                i += 1
                src -= 1
                dst -= 1
            minimo_margine = min(minimo_margine, dst - src)
    pretendi(len(fuori) == attesi,
             "BLZ: prodotti %d byte invece di %d" % (len(fuori), attesi))
    pretendi(minimo_margine >= 0,
             "BLZ: il flusso NON e' decomprimibile in luogo (margine minimo %d): "
             "il gioco si sovrascriverebbe la sorgente" % minimo_margine)
    img = prefisso + bytes(reversed(fuori))
    pretendi(len(img) == finale, "BLZ: immagine %d B invece di %d" % (len(img), finale))
    return img, {"hdr_len": testa, "enc_len": codificato, "inc_len": aumento,
                 "prefisso_grezzo": len(prefisso), "dim_decompressa": finale,
                 "margine_minimo_in_luogo": minimo_margine}


# -------------------------------------------------------------- lettura ROM
def tabelle(dati):
    p = lambda o: struct.unpack("<I", dati[o:o + 4])[0]
    return {
        "arm9_off": p(0x20), "arm9_ram": p(0x28), "arm9_len": p(0x2C),
        "fat": p(0x48), "fat_len": p(0x4C), "y9": p(0x50), "y9_len": p(0x54),
        "usato": p(0x80), "capienza": dati[0x14],
        "crc": struct.unpack("<H", dati[0x15E:0x160])[0],
    }


def leggi_overlay(dati, t, oid):
    off = t["y9"] + oid * 32
    campi = struct.unpack("<8I", dati[off:off + 32])
    e = {"id": campi[0], "ram": campi[1], "ram_size": campi[2], "bss": campi[3],
         "sis": campi[4], "sie": campi[5], "file_id": campi[6],
         "flag": campi[7] >> 24, "dim": campi[7] & 0xFFFFFF, "voce": off}
    f = t["fat"] + e["file_id"] * 8
    s, fi = struct.unpack("<II", dati[f:f + 8])
    e["fat_voce"] = f
    e["inizio"] = s
    e["fine"] = fi
    return e


def immagine(dati, e):
    corpo = dati[e["inizio"]:e["fine"]]
    if e["flag"] & 1:
        pretendi(e["dim"] <= len(corpo),
                 "y9 dichiara %d B compressi, la FAT ne da' %d" % (e["dim"], len(corpo)))
        return srotola_blz(corpo[:e["dim"]])
    return bytes(corpo), {"compresso": False}


def esa(s):
    s = s.strip()
    if s.lower().startswith("0x"):
        s = s[2:]
    return bytes.fromhex(s)


# --------------------------------------------------------------------- main
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--rom", required=True, help="la ROM PRODOTTA, da rileggere")
    ap.add_argument("--ingresso", default=None, help="la ROM di partenza, per il confronto")
    ap.add_argument("--overlay", required=True)
    ap.add_argument("--guardia", action="append", default=[], metavar="ADDR:HEX")
    ap.add_argument("--post", action="append", default=[], metavar="ADDR:HEX",
                    help="postimmagine attesa nell'overlay decompresso (ripetibile)")
    ap.add_argument("--json", default=None)
    a = ap.parse_args(argv)

    d = Path(a.rom).read_bytes()
    t = tabelle(d)
    r = {"strumento": "SGP-1.2-OVERLAY-01/tools/overlay_rileggi.py",
         "rom": a.rom, "rom_sha256": impronta(d), "rom_bytes": len(d), "verde": False}

    # -- V1: header coerente ----------------------------------------------
    atteso = crc16_header(d[:0x15E])
    pretendi(atteso == t["crc"],
             "V1: CRC16 dell'header %04X, ne serve %04X" % (t["crc"], atteso))
    pretendi(t["usato"] <= len(d),
             "V1: total_used %#x oltre la fine del file (%#x)" % (t["usato"], len(d)))
    pretendi(len(d) <= (0x20000 << t["capienza"]),
             "V1: il file (%d) non entra nella capienza dichiarata" % len(d))
    r["header"] = {"crc16": "%04X" % t["crc"], "total_used": hex(t["usato"]),
                   "capienza": t["capienza"], "bytes": len(d)}

    # -- V2: FAT senza sovrapposizioni e dentro il file --------------------
    n_file = t["fat_len"] // 8
    voci = []
    for i in range(n_file):
        s, f = struct.unpack("<II", d[t["fat"] + i * 8:t["fat"] + i * 8 + 8])
        if s == 0 and f == 0:
            continue
        pretendi(s <= f <= len(d), "V2: file %d ha estensione [%#x,%#x) fuori dal file" % (i, s, f))
        voci.append((s, f, i))
    voci.sort()
    for (s1, f1, i1), (s2, f2, i2) in zip(voci, voci[1:]):
        pretendi(f1 <= s2, "V2: i file %d [%#x,%#x) e %d [%#x,%#x) si sovrappongono"
                 % (i1, s1, f1, i2, s2, f2))
    r["fat"] = {"voci": n_file, "non_vuote": len(voci), "sovrapposizioni": 0}

    # -- V3: l'overlay c'e', la guardia combacia ---------------------------
    oid = int(a.overlay, 0)
    n_ov = t["y9_len"] // 32
    pretendi(0 <= oid < n_ov, "V3: overlay %d fuori dalla tabella (%d voci)" % (oid, n_ov))
    e = leggi_overlay(d, t, oid)
    pretendi(e["id"] == oid, "V3: la voce %d dichiara id %d" % (oid, e["id"]))
    img, diag = immagine(d, e)
    pretendi(len(img) == e["ram_size"],
             "V3: immagine %d B, ram_size dichiara %d" % (len(img), e["ram_size"]))
    if e["flag"] & 1:
        pretendi(e["dim"] == e["fine"] - e["inizio"],
                 "V3: y9 dichiara %d B compressi, la FAT ne riserva %d"
                 % (e["dim"], e["fine"] - e["inizio"]))
    else:
        pretendi(e["dim"] == e["fine"] - e["inizio"],
                 "V3: y9 dichiara %d B, la FAT ne riserva %d"
                 % (e["dim"], e["fine"] - e["inizio"]))
    pretendi(e["ram"] <= e["sis"] <= e["sie"] <= e["ram"] + e["ram_size"],
             "V3: static_init [%#x,%#x) fuori dal modulo [%#x,%#x)"
             % (e["sis"], e["sie"], e["ram"], e["ram"] + e["ram_size"]))
    r["overlay"] = {"id": oid, "file_id": e["file_id"], "ram": hex(e["ram"]),
                    "ram_size": e["ram_size"], "compresso": bool(e["flag"] & 1),
                    "flag": e["flag"], "dim_dichiarata": e["dim"],
                    "fat": [hex(e["inizio"]), hex(e["fine"])],
                    "immagine_sha256": impronta(img), "blz": diag}

    for g in a.guardia:
        ad, hx = g.split(":", 1)
        ad = int(ad, 0)
        hx = esa(hx)
        o = ad - e["ram"]
        pretendi(0 <= o and o + len(hx) <= len(img), "V4: guardia %#x fuori dal modulo" % ad)
        pretendi(bytes(img[o:o + len(hx)]) == hx,
                 "V4 GUARDIA: a %#x c'e' %s, attesa %s"
                 % (ad, bytes(img[o:o + len(hx)]).hex(), hx.hex()))

    # -- V5: postimmagini --------------------------------------------------
    post = []
    for s in a.post:
        ad, hx = s.split(":", 1)
        ad = int(ad, 0)
        hx = esa(hx)
        o = ad - e["ram"]
        pretendi(0 <= o and o + len(hx) <= len(img), "V5: postimmagine %#x fuori dal modulo" % ad)
        trovato = bytes(img[o:o + len(hx)])
        pretendi(trovato == hx,
                 "V5 POSTIMMAGINE: a %#x c'e' %s, attesa %s" % (ad, trovato.hex(), hx.hex()))
        post.append({"addr": hex(ad), "bytes": len(hx), "vale": hx.hex()})
    r["postimmagini"] = post

    # -- V6: confronto con la ROM d'ingresso -------------------------------
    if a.ingresso:
        i = Path(a.ingresso).read_bytes()
        ti = tabelle(i)
        ei = leggi_overlay(i, ti, oid)
        imi, _ = immagine(i, ei)
        diff = [k for k in range(min(len(imi), len(img))) if imi[k] != img[k]]
        # V7: se sono state dichiarate le postimmagini, i byte cambiati
        # nell'overlay devono essere TUTTI dentro quelle. Un byte cambiato
        # altrove (una corruzione, un'altra patch non dichiarata) e' rosso.
        if a.post:
            coperti = set()
            for s2 in a.post:
                ad, hx = s2.split(":", 1)
                ad = int(ad, 0) - e["ram"]
                coperti.update(range(ad, ad + len(esa(hx))))
            fuori = [k for k in diff if k not in coperti]
            if fuori:
                raise Rosso("V7: %d byte dell'overlay cambiano FUORI dalle "
                            "postimmagini dichiarate, il primo a %#x"
                            % (len(fuori), e["ram"] + fuori[0]))
        pretendi(len(imi) == len(img),
                 "V7: l'immagine cambia dimensione (%d -> %d)" % (len(imi), len(img)))
        r["confronto_immagine"] = {
            "ingresso_sha256": impronta(i), "ingresso_bytes": len(i),
            "immagine_ingresso_sha256": impronta(imi),
            "byte_diversi_nell_overlay": len(diff),
            "tutti_dentro_le_postimmagini": bool(a.post),
            "indirizzi": [hex(e["ram"] + k) for k in diff[:64]],
        }
        # regioni della ROM cambiate, calcolate qui e non prese dall'applicatore
        blocchi = []
        n = min(len(i), len(d))
        k = 0
        while k < n:
            if i[k] != d[k]:
                j = k
                while j < n and i[j] != d[j]:
                    j += 1
                blocchi.append((k, j))
                k = j
            else:
                k += 1
        r["confronto_rom"] = {
            "blocchi_diversi": [{"da": hex(x), "a": hex(y), "bytes": y - x} for x, y in blocchi[:40]],
            "n_blocchi": len(blocchi),
            "byte_aggiunti_in_coda": len(d) - len(i),
        }

    r["verde"] = True
    testo = json.dumps(r, indent=2, ensure_ascii=False) + "\n"
    if a.json:
        Path(a.json).write_text(testo)
    print(testo)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Rosso as ex:
        print("ROSSO: %s" % ex, file=sys.stderr)
        raise SystemExit(3)
