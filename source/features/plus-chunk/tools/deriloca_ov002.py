#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SGP-1.2-PLUS-03 — annulla la RILOCAZIONE IN CODA di un overlay ARM9.

SGP-1.2-PLUS-02 ha scritto il gancio selvatici in `ov002` ricomprimendolo con
ndspy (42 968 B, quattro byte piu' del corpo originale) e, non entrando nello
slot, l'ha RILOCATO IN CODA alla ROM, aggiornando voce FAT, voce y9 e header.
SGP-1.2-OVERLAY-01 (RAPPORTO §3, §8) ha poi misurato che la rilocazione e' una
strada da non prendere: la vecchia copia resta nella ROM e qualunque corsa che
riprenda da un savestate costruito su un'altra geometria legge ancora QUELLA.

Questo strumento riporta la ROM alla geometria originale SENZA toccare il
contenuto: rimette la voce FAT, la voce y9 e l'header a com'erano nella base
(che in quello slot ha ancora, byte per byte, il corpo originale dell'overlay) e
tronca la coda. Il risultato e' una ROM in cui l'overlay e' di nuovo NON
patchato: sopra ci si rifa' la patch IN LUOGO con
`SGP-1.2-OVERLAY-01/tools/overlay_patch.py`.

Cancelli (nessuna uscita se uno solo cade):
  D1  la ROM di ingresso ha davvero l'overlay rilocato (FAT oltre la fine
      dichiarata dall'header della base);
  D2  lo slot originale contiene ancora, byte per byte, il corpo della base;
  D3  fra la fine della base e l'inizio della copia in coda c'e' solo
      riempimento 0xFF (cioe' la coda contiene SOLO l'overlay rilocato);
  D4  dopo il taglio, la ROM e' lunga quanto la base;
  D5  fuori da header/FAT/y9/coda non si tocca un byte;
  D6  il CRC16 dell'header torna quello della base.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path

QUI = Path(__file__).resolve()
REPO = QUI.parents[4]
sys.path.insert(0, str(REPO / "source/features/overlay/tools"))
from overlay_patch import Rifiuto, crc16, esigi, sha  # noqa: E402


def u32(b, o):
    return struct.unpack_from("<I", b, o)[0]


def deriloca(dati, dati_base, oid, ricevuta=None):
    r = ricevuta if ricevuta is not None else {}
    r["strumento"] = "SGP-1.2-PLUS-03/tools/deriloca_ov002.py"
    r["ingresso_sha256"] = sha(dati)
    r["base_sha256"] = sha(dati_base)
    r["overlay"] = oid
    r["cancelli"] = {}

    fat_off = u32(dati, 0x48)
    y9_off = u32(dati, 0x50)
    y9_len = u32(dati, 0x54)
    esigi(fat_off == u32(dati_base, 0x48) and y9_off == u32(dati_base, 0x50)
          and y9_len == u32(dati_base, 0x54),
          "D0: FAT/y9 spostate rispetto alla base: non e' il caso previsto")

    voce = y9_off + 32 * oid
    esigi(u32(dati, voce) == oid, "D0: la voce y9 %d non dichiara id %d" % (oid, oid))
    fid = u32(dati, voce + 0x18)
    esigi(fid == u32(dati_base, voce + 0x18), "D0: file_id dell'overlay cambiato")

    fat = fat_off + 8 * fid
    inizio, fine = u32(dati, fat), u32(dati, fat + 4)
    b_inizio, b_fine = u32(dati_base, fat), u32(dati_base, fat + 4)
    usata_base = u32(dati_base, 0x80)

    # D1 --------------------------------------------------------------------
    esigi(inizio >= usata_base,
          "D1: l'overlay NON e' rilocato (FAT %#x < fine della base %#x): "
          "questo strumento non serve" % (inizio, usata_base))
    r["cancelli"]["D1_rilocato"] = {
        "fat_ingresso": [hex(inizio), hex(fine)],
        "fat_base": [hex(b_inizio), hex(b_fine)],
        "fine_dichiarata_base": hex(usata_base),
        "bytes_in_coda": len(dati) - usata_base,
    }

    # D2 --------------------------------------------------------------------
    slot_ing = bytes(dati[b_inizio:b_fine])
    slot_base = bytes(dati_base[b_inizio:b_fine])
    esigi(slot_ing == slot_base,
          "D2: lo slot originale [%#x,%#x) non contiene piu' il corpo della base"
          % (b_inizio, b_fine))
    r["cancelli"]["D2_slot_originale_intatto"] = {
        "intervallo": [hex(b_inizio), hex(b_fine)], "sha256": sha(slot_base)}

    # D3 --------------------------------------------------------------------
    riempimento = bytes(dati[usata_base:inizio])
    esigi(set(riempimento) <= {0xFF},
          "D3: fra %#x e %#x non c'e' solo riempimento 0xFF" % (usata_base, inizio))
    esigi(fine == len(dati),
          "D3: la copia in coda non finisce a fine ROM (%#x != %#x)" % (fine, len(dati)))
    r["cancelli"]["D3_coda_solo_overlay"] = {
        "riempimento_bytes": len(riempimento), "copia_in_coda": [hex(inizio), hex(fine)],
        "sha256_copia_in_coda": sha(dati[inizio:fine])}

    # ricostruzione ---------------------------------------------------------
    out = bytearray(dati[:usata_base])
    cambi = []
    for off, n, nome in ((fat, 8, "voce FAT"), (voce, 32, "voce y9"),
                         (0x80, 4, "header: dimensione usata")):
        if bytes(out[off:off + n]) != bytes(dati_base[off:off + n]):
            cambi.append({"cosa": nome, "offset": hex(off), "bytes": n,
                          "prima": bytes(out[off:off + n]).hex(),
                          "dopo": bytes(dati_base[off:off + n]).hex()})
            out[off:off + n] = dati_base[off:off + n]
    nuovo_crc = crc16(bytes(out[0:0x15E]))
    if struct.unpack_from("<H", out, 0x15E)[0] != nuovo_crc:
        cambi.append({"cosa": "header: CRC16", "offset": hex(0x15E), "bytes": 2,
                      "prima": bytes(out[0x15E:0x160]).hex(),
                      "dopo": struct.pack("<H", nuovo_crc).hex()})
        struct.pack_into("<H", out, 0x15E, nuovo_crc)
    r["scritture"] = cambi

    # D4 --------------------------------------------------------------------
    esigi(len(out) == len(dati_base),
          "D4: la ROM tagliata e' %d B, la base %d" % (len(out), len(dati_base)))
    r["cancelli"]["D4_lunghezza"] = {"uscita": len(out), "base": len(dati_base)}

    # D5 --------------------------------------------------------------------
    toccati = set()
    for c in cambi:
        o = int(c["offset"], 16)
        toccati |= set(range(o, o + c["bytes"]))
    diversi = [i for i in range(len(out)) if out[i] != dati[i]]
    esigi(set(diversi) <= toccati,
          "D5: %d byte diversi fuori da header/FAT/y9" % len(set(diversi) - toccati))
    r["cancelli"]["D5_portata"] = {"byte_diversi_sotto_il_taglio": len(diversi),
                                   "tutti_dichiarati": True}

    # D6 --------------------------------------------------------------------
    # NON si pretende il CRC16 della base: l'header di uscita differisce dalla
    # base in campi che NON sono di questo cantiere (0x2C `arm9_size`, allungato
    # da SGP-1.2-RISERVA-01 quando ha abbassato la base dell'autoload). Il
    # cancello e' che il CRC scritto sia quello GIUSTO per l'header scritto, e
    # che i campi dell'header diversi dalla base siano tutti dichiarati.
    esigi(crc16(bytes(out[0:0x15E])) == struct.unpack_from("<H", out, 0x15E)[0],
          "D6: il CRC16 scritto non e' quello dell'header scritto")
    diff_header = [hex(i) for i in range(0x160)
                   if out[i] != dati_base[i] and not (0x15E <= i < 0x160)]
    r["cancelli"]["D6_crc16"] = {
        "valore": hex(nuovo_crc),
        "crc16_base": hex(struct.unpack_from("<H", dati_base, 0x15E)[0]),
        "campi_header_diversi_dalla_base": diff_header,
        "nota": "differenze attese: 0x2C arm9_size (SGP-1.2-RISERVA-01)"}

    r["uscita_sha256"] = sha(out)
    r["uscita_bytes"] = len(out)
    return bytes(out), r


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--rom", required=True)
    ap.add_argument("--base", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--overlay", type=int, default=2)
    ap.add_argument("--json", default=None)
    a = ap.parse_args(argv)
    dati = Path(a.rom).read_bytes()
    base = Path(a.base).read_bytes()
    ric = {}
    try:
        out, ric = deriloca(dati, base, a.overlay, ric)
    except Rifiuto as e:
        ric["rifiuto"] = str(e)
        if a.json:
            Path(a.json).write_text(json.dumps(ric, indent=2, ensure_ascii=False))
        print("RIFIUTO: %s" % e, file=sys.stderr)
        return 2
    Path(a.out).write_bytes(out)
    if a.json:
        Path(a.json).write_text(json.dumps(ric, indent=2, ensure_ascii=False))
    print(json.dumps(ric, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
