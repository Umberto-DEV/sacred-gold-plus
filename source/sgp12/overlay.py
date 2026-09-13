#!/usr/bin/env python3
"""sgp12.overlay — applicatore condiviso di patch di byte dentro gli overlay
ARM9 (compressi BLZ) di HGSS, che lascia la ROM valida.

Consolidamento di `SGP-1.2-OVERLAY-01/tools/overlay_patch.py` (805 righe,
copiate IDENTICHE byte per byte — stesso sha1 — dentro ANIM-B-02, ANIM-B-03,
PRESTAZIONI-NPC-02, PRESTAZIONI-NPC-03 e OPZIONI-02): qui vive una volta sola,
usata da `sgp12.blocchi.npc/anim/opzioni/wifi`.

**Non usa `ndspy.rom.save()`**, misurato rompere la ROM anche senza cambiare
niente (SGP-1.2-ANIM-B-01/RAPPORTO.md §8): legge e scrive i byte della ROM da
se'.

Uso tipico da riga di comando:

    python3 -m sgp12.overlay --rom in.nds --out out.nds --overlay 12 \\
        --guardia 0x0226203C:0bb5... \\
        --patch 0x0226200C:3d206202:51883d02
"""
from __future__ import annotations

import argparse
import json
import struct
import sys
from pathlib import Path

from .rom import Rifiuto, Rom, crc16, esigi, sha, analizza_guardia, analizza_patch
from .blz import blz_comprimi_ottimo, blz_decomprimi, blz_leggi_trailer

__all__ = [
    "Rifiuto", "esigi", "sha", "Rom", "crc16",
    "analizza_guardia", "analizza_patch",
    "blz_decomprimi", "blz_comprimi_ottimo", "blz_leggi_trailer",
    "scegli_overlay", "applica", "main",
]


def scegli_overlay(rom: Rom, guardie, oid=None):
    """Sceglie l'overlay. Con `oid` dato lo verifica; con `oid` None lo cerca.

    In entrambi i casi la guardia DEVE combaciare: e' il contenuto che decide,
    mai l'indirizzo (piu' overlay possono condividere lo stesso indirizzo RAM)."""
    esigi(guardie, "serve almeno una --guardia: l'overlay si sceglie per contenuto")
    candidati = []
    for i in range(rom.n_overlay):
        v = rom.voce_overlay(i)
        if not all(v["ram"] <= a and a + len(h) <= v["ram"] + v["ram_size"] for a, h in guardie):
            continue
        try:
            _, _, img = rom.immagine_overlay(i)
        except Rifiuto:
            continue
        if all(img[a - v["ram"]:a - v["ram"] + len(h)] == h for a, h in guardie):
            candidati.append(i)
    if oid is None:
        esigi(len(candidati) == 1,
              "la guardia non individua un overlay solo: candidati %s" % (candidati,))
        return candidati[0], candidati
    esigi(oid in candidati,
          "l'overlay %d NON supera la guardia (la superano: %s)" % (oid, candidati))
    return oid, candidati


def applica(dati_rom, oid, guardie, patch, strategia="auto", ricevuta=None,
            forza_ricompressione=False, consenti_riloco=False):
    """Ritorna (byte della ROM di uscita, ricevuta dict).

    `strategia`:
      * `a`    — ricomprimi BLZ (l'overlay resta compresso);
      * `b`    — scrivi decompresso e spegni il bit 24 nella tabella y9;
      * `auto` — `a` se il flusso ricompresso entra nello spazio disponibile,
                 altrimenti `a` con riloco in coda; `b` solo se richiesta.
    """
    rom = Rom(dati_rom)
    r = ricevuta if ricevuta is not None else {}
    r["strumento"] = "sgp12/overlay.py"
    r["ingresso_sha256"] = sha(dati_rom)
    r["ingresso_bytes"] = len(dati_rom)
    r["cancelli"] = {}

    scelto, candidati = scegli_overlay(rom, guardie, oid)
    v, crudo, img = rom.immagine_overlay(scelto)
    r["cancelli"]["C1_guardia"] = {
        "overlay": scelto, "candidati": candidati,
        "guardie": [{"addr": hex(a), "bytes": len(h), "hex": h.hex()} for a, h in guardie],
    }
    r["overlay"] = {
        "id": scelto, "file_id": v["file_id"], "ram": hex(v["ram"]),
        "ram_size": v["ram_size"], "bss_size": v["bss_size"],
        "compresso_in_ingresso": v["compresso"], "flag_in_ingresso": v["flag"],
        "dim_compressa_dichiarata": v["dim_compressa"],
        "file_bytes_in_ingresso": len(crudo),
        "immagine_bytes": len(img), "immagine_sha256_prima": sha(img),
    }

    esigi(v["id"] == scelto, "C2: la voce %d dichiara id %d" % (scelto, v["id"]))
    esigi(len(img) == v["ram_size"],
          "C2: l'immagine decompressa e' %d B ma ram_size dichiara %d"
          % (len(img), v["ram_size"]))
    if v["compresso"]:
        t = blz_leggi_trailer(crudo[:v["dim_compressa"]])
        r["overlay"]["trailer_blz_ingresso"] = {
            "hdr_len": t[0], "enc_len": t[1], "inc_len": t[2],
            "prefisso_grezzo": t[3], "dim_decompressa": t[4]}

    nuova = bytearray(img)
    scritture = []
    for p in patch:
        off = p["addr"] - v["ram"]
        esigi(0 <= off and off + len(p["pre"]) <= len(img),
              "C3: la patch a %#x non sta dentro ov%03d [%#x,%#x)"
              % (p["addr"], scelto, v["ram"], v["ram"] + v["ram_size"]))
        trovato = bytes(nuova[off:off + len(p["pre"])])
        esigi(trovato == p["pre"],
              "C3 PREIMMAGINE: a %#x c'e' %s, attesa %s. O la ROM non e' quella, "
              "o la patch e' gia' applicata (idempotenza), o la preimmagine e' sbagliata."
              % (p["addr"], trovato.hex(), p["pre"].hex()))
        nuova[off:off + len(p["post"])] = p["post"]
        scritture.append({"addr": hex(p["addr"]), "offset_nel_modulo": off,
                          "bytes": len(p["pre"]),
                          "prima": p["pre"].hex(), "dopo": p["post"].hex()})
    r["patch"] = scritture
    r["overlay"]["immagine_sha256_dopo"] = sha(nuova)

    capienza = rom.capienza_slot(v["file_id"])
    fat = rom.voce_fat(v["file_id"])
    r["overlay"]["slot_bytes"] = capienza
    r["overlay"]["fat_in_ingresso"] = [hex(fat["inizio"]), hex(fat["fine"])]

    invariato = bytes(nuova) == bytes(img)
    if strategia in ("a", "auto"):
        if invariato and not forza_ricompressione:
            corpo = bytes(crudo)
            modo = "a-corpo-originale (immagine invariata)"
        else:
            corpo = blz_comprimi_ottimo(bytes(nuova), bersaglio=len(crudo))
            esigi(blz_decomprimi(corpo) == bytes(nuova),
                  "C4: decompresso -> ricompresso -> decompresso NON coincide")
            t = blz_leggi_trailer(corpo)
            r["cancelli"]["C4_roundtrip_blz"] = {
                "compresso_bytes": len(corpo), "hdr_len": t[0], "enc_len": t[1],
                "inc_len": t[2], "prefisso_grezzo": t[3], "dim_decompressa": t[4],
                "identico": True,
                "bersaglio": len(crudo), "bersaglio_centrato": len(corpo) == len(crudo)}
            modo = "a-ricompresso"
        nuovo_flag = (v["flag"] | 1) & 0xFF
    elif strategia == "b":
        corpo = bytes(nuova)
        nuovo_flag = v["flag"] & ~1 & 0xFF
        modo = "b-decompresso"
    else:
        raise Rifiuto("strategia sconosciuta: %r" % strategia)

    esigi(len(corpo) <= 0xFFFFFF,
          "la dimensione da scrivere nella voce y9 (%d) non entra in 24 bit" % len(corpo))

    out = bytearray(rom.d)
    cambiati = []

    if len(corpo) <= capienza:
        inizio = fat["inizio"]
        vecchi = fat["bytes"]
        out[inizio:inizio + len(corpo)] = corpo
        if len(corpo) < vecchi:
            out[inizio + len(corpo):inizio + vecchi] = b"\xFF" * (vecchi - len(corpo))
        toccati_fino = inizio + max(len(corpo), vecchi)
        cambiati.append(("corpo overlay", inizio, toccati_fino))
        collocazione = "in luogo"
    else:
        esigi(consenti_riloco,
              "C6: il corpo nuovo e' %d B e lo slot del file ne tiene %d. Rilocare "
              "l'overlay in coda NON e' sicuro (misurato: la NitroSDK tiene la FAT "
              "in RAM letta a freddo all'avvio). Serve un corpo che entri nello slot."
              % (len(corpo), capienza))
        while len(out) % 512:
            out.append(0xFF)
        inizio = len(out)
        out += corpo
        cambiati.append(("corpo overlay (in coda)", inizio, inizio + len(corpo)))
        collocazione = "rilocato in coda (NON RACCOMANDATO)"

    fine = inizio + len(corpo)
    struct.pack_into("<II", out, fat["offset_voce"], inizio, fine)
    cambiati.append(("voce FAT", fat["offset_voce"], fat["offset_voce"] + 8))
    nuova_parola = (len(corpo) & 0xFFFFFF) | (nuovo_flag << 24)
    struct.pack_into("<I", out, v["offset_voce"] + 28, nuova_parola)
    cambiati.append(("voce y9 (dim+flag)", v["offset_voce"] + 28, v["offset_voce"] + 32))

    usato_prima = struct.unpack_from("<I", rom.d, 0x80)[0]
    usato = max(usato_prima, fine)
    if usato != usato_prima:
        struct.pack_into("<I", out, 0x80, usato)
        cambiati.append(("header total_used", 0x80, 0x84))
    cap = rom.d[0x14]
    while len(out) > (0x20000 << cap):
        cap += 1
    esigi(cap <= 12, "l'uscita supera il limite di 512 MiB della cartuccia")
    if cap != rom.d[0x14]:
        out[0x14] = cap
        cambiati.append(("header capienza", 0x14, 0x15))
    nuovo_crc = crc16(bytes(out[:0x15E]))
    if nuovo_crc != struct.unpack_from("<H", rom.d, 0x15E)[0]:
        struct.pack_into("<H", out, 0x15E, nuovo_crc)
        cambiati.append(("header CRC16", 0x15E, 0x160))

    r["strategia"] = {"chiesta": strategia, "usata": modo, "collocazione": collocazione,
                      "corpo_bytes": len(corpo), "flag_y9": nuovo_flag,
                      "parola_y9": hex(nuova_parola)}
    r["regioni_cambiate"] = [{"cosa": c, "da": hex(a), "a": hex(b), "bytes": b - a}
                             for c, a, b in cambiati]

    coperto = [(a, b) for _, a, b in cambiati]
    diversi = []
    n = min(len(rom.d), len(out))
    da = 0
    for a, b in sorted(coperto):
        if a > da:
            if rom.d[da:min(a, n)] != out[da:min(a, n)]:
                diversi.append((da, min(a, n)))
        da = max(da, b)
    if da < n and rom.d[da:n] != out[da:n]:
        diversi.append((da, n))
    esigi(not diversi,
          "C5: la ROM cambia FUORI dalle regioni dichiarate: %s" % (diversi,))
    r["cancelli"]["C5_resto_identico"] = {
        "regioni_dichiarate": len(cambiati),
        "byte_aggiunti_in_coda": len(out) - len(rom.d),
        "byte_diversi_fuori": 0}

    r["uscita_bytes"] = len(out)
    r["uscita_sha256"] = sha(out)
    return bytes(out), r


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--rom", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--overlay", required=True,
                    help="id dell'overlay, oppure `auto` per sceglierlo per guardia")
    ap.add_argument("--guardia", action="append", default=[], metavar="ADDR:HEX")
    ap.add_argument("--patch", action="append", default=[], metavar="ADDR:PRE:POST")
    ap.add_argument("--strategia", choices=("auto", "a", "b"), default="auto")
    ap.add_argument("--forza-ricompressione", action="store_true")
    ap.add_argument("--consenti-riloco", action="store_true")
    ap.add_argument("--json", default=None)
    ap.add_argument("--zitto", action="store_true")
    a = ap.parse_args(argv)

    oid = None if a.overlay.strip().lower() == "auto" else int(a.overlay, 0)
    guardie = [analizza_guardia(s) for s in a.guardia]
    patch = [analizza_patch(s) for s in a.patch]

    dati = Path(a.rom).read_bytes()
    out, r = applica(dati, oid, guardie, patch, a.strategia,
                     forza_ricompressione=a.forza_ricompressione,
                     consenti_riloco=a.consenti_riloco)
    r["ingresso"] = a.rom
    r["uscita"] = a.out
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_bytes(out)
    testo = json.dumps(r, indent=2, ensure_ascii=False) + "\n"
    if a.json:
        Path(a.json).write_text(testo)
    if not a.zitto:
        print(testo)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Rifiuto as e:
        print("RIFIUTO: %s" % e, file=sys.stderr)
        raise SystemExit(2)
