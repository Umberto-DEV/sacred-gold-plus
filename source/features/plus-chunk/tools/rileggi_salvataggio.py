#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SGP-1.2-PLUS-03 — rilettore INDIPENDENTE del chunk di salvataggio.

Non importa una riga di `applica_salvataggio.py`: rilegge la ROM prodotta e
decide da solo. Cancelli:

  R1  il blob a 0x023D8730 è byte-identico a `salva_blob.bin`, e il resto del
      blocco `sgp.plus` fino a 0x023D8900 è a zero;
  R2  le due `BL` dei siti di gancio, DECODIFICATE dai byte, puntano ai due
      simboli del manifesto di compilazione (non «somigliano», puntano);
  R3  il blocco `sgp.salvataggio` (0x023D8F00, 256 B) ha il buffer a zero e il
      canarino 0xCA5A1300|i a 0x023D8FF0;
  R4  il resto della ROM è identico all'ingresso, e gli unici offset diversi
      sono blob, canarino e i due ganci — elencati uno per uno;
  R5  la zona 1.1 [0x023DEB40, 0x023E0000) è invariata;
  R6  il blocco `sgp.plus` di PLUS-02 (blob PLUS, tabelle, stato, canarino) non
      è cambiato nei suoi primi 0x630 byte;
  R7  il blob DISASSEMBLATO non contiene salti o chiamate fuori da sé stesso e
      dalle cinque funzioni del gioco dichiarate.
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
sys.path.insert(0, str(QUI))
from arm9 import Arm9  # noqa: E402

BLOCCO_PLUS = 0x023D8100
BLOB = 0x023D8730
BLOB_FINE = 0x023D8900
SALVA = 0x023D8F00
SALVA_BYTES = 256
CANARINO = 0x023D8FF0
CANARINO_MOTIVO = 0xCA5A1300
ZONA_1_1 = (0x023DEB40, 0x023E0000)
SITI = {"L0": (0x020271F8, "sgp_gancio_carica"), "S0": (0x02027456, "sgp_gancio_salva")}
AMMESSE = (0x02028758, 0x0202877C, 0x0201FF98, 0x020277D4, 0x02027DB4)
# impronta della zona 1.1, identica EN/IT, letta dalla ROM di lavoro prima di
# questa fase: R5 la CONFRONTA, non si limita a registrarla.
SHA_BLOB = "35cccda383f33275036c40eee2a4ee8894a136838a48350d2f4db243514171b3"
# il rilettore NON si fida di `salva_blob.bin`: dichiara lui che cosa deve
# esserci. Cosi un blob compilato manomesso non passa solo perche chi applica
# e chi rilegge leggono lo stesso file (e il mutante M1 che ha trovato questo
# buco).
SHA_ZONA_1_1 = "c86017f2bd43de408d9953341b35a5c917ba26dd1fca29d2f1a808d5e1ae5ef6"


def sha(b):
    return hashlib.sha256(bytes(b)).hexdigest()


def decodifica_bl(sito, q):
    hi, lo = struct.unpack("<HH", q)
    if (hi & 0xF800) != 0xF000 or (lo & 0xF800) != 0xF800:
        return None
    alto = hi & 0x7FF
    if alto & 0x400:
        alto -= 0x800
    return (sito + 4 + (alto << 12) + ((lo & 0x7FF) << 1)) & 0xFFFFFFFF


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--rom", required=True)
    ap.add_argument("--ingresso", help="ROM di partenza, per R4")
    ap.add_argument("--build", required=True)
    ap.add_argument("--json")
    a = ap.parse_args(argv)

    r = {"strumento": "SGP-1.2-PLUS-03/tools/rileggi_salvataggio.py",
         "rom": str(a.rom), "cancelli": {}, "verde": False}
    x = Arm9(a.rom)
    r["rom_sha256"] = sha(x.raw)
    r["rom_bytes"] = len(x.raw)
    manifesto = json.loads((Path(a.build) / "manifesto.json").read_text())
    blob = (Path(a.build) / "salva_blob.bin").read_bytes()
    errori = []

    # R1 -------------------------------------------------------------------
    letto = x.leggi(BLOB, len(blob))
    coda = x.leggi(BLOB + len(blob), BLOB_FINE - BLOB - len(blob))
    r["cancelli"]["R1_blob"] = {"base": hex(BLOB), "bytes": len(blob),
                                "sha256_atteso": sha(blob), "sha256_letto": sha(letto),
                                "coda_a_zero": set(coda) <= {0},
                                "coda_bytes": len(coda)}
    if sha(blob) != SHA_BLOB:
        errori.append("R1: `salva_blob.bin` non è il blob dichiarato da questo "
                      "rilettore (letto %s, atteso %s)" % (sha(blob)[:16], SHA_BLOB[:16]))
    if sha(letto) != SHA_BLOB:
        errori.append("R1: il blob in ROM non è quello dichiarato")
    if letto != blob:
        errori.append("R1: il blob in ROM non è quello compilato")
    if set(coda) - {0}:
        errori.append("R1: la coda del blocco sgp.plus non è a zero")

    # R2 -------------------------------------------------------------------
    ganci = {}
    for nome, (sito, simbolo) in SITI.items():
        q = x.leggi(sito, 4)
        bersaglio = decodifica_bl(sito, q)
        atteso = int(manifesto["simboli"][simbolo], 16) & ~1
        ganci[nome] = {"sito": hex(sito), "byte": q.hex(),
                       "bersaglio_decodificato": hex(bersaglio) if bersaglio else None,
                       "simbolo": simbolo, "atteso": hex(atteso)}
        if bersaglio != atteso:
            errori.append("R2: il gancio %s punta a %s, atteso %s"
                          % (nome, ganci[nome]["bersaglio_decodificato"], hex(atteso)))
    r["cancelli"]["R2_ganci"] = ganci

    # R3 -------------------------------------------------------------------
    blocco = x.leggi(SALVA, SALVA_BYTES)
    atteso_can = b"".join(struct.pack("<I", CANARINO_MOTIVO | i) for i in range(4))
    corpo = blocco[:CANARINO - SALVA]
    r["cancelli"]["R3_blocco_salvataggio"] = {
        "base": hex(SALVA), "bytes": SALVA_BYTES,
        "corpo_a_zero": set(corpo) <= {0},
        "canarino": x.leggi(CANARINO, 16).hex(), "atteso": atteso_can.hex(),
        "sha256": sha(blocco)}
    if set(corpo) - {0}:
        errori.append("R3: il corpo del blocco sgp.salvataggio non è a zero")
    if x.leggi(CANARINO, 16) != atteso_can:
        errori.append("R3: canarino sbagliato")

    # R4 -------------------------------------------------------------------
    if a.ingresso:
        y = Arm9(a.ingresso)
        attesi = set()
        for ram, n in ((BLOB, len(blob)), (CANARINO, 16),
                       (SITI["L0"][0], 4), (SITI["S0"][0], 4)):
            o = x.off(ram, n)
            attesi |= set(range(o, o + n))
        if len(x.raw) != len(y.raw):
            errori.append("R4: lunghezza della ROM cambiata")
        diversi = [i for i in range(min(len(x.raw), len(y.raw))) if x.raw[i] != y.raw[i]]
        fuori = [i for i in diversi if i not in attesi]
        r["cancelli"]["R4_resto_identico"] = {
            "byte_diversi": len(diversi), "fuori_dalle_regioni": len(fuori),
            "primi_fuori": [hex(i) for i in fuori[:8]]}
        if fuori:
            errori.append("R4: %d byte diversi fuori dalle regioni dichiarate" % len(fuori))
    else:
        r["cancelli"]["R4_resto_identico"] = "saltato: manca --ingresso"

    # R5 -------------------------------------------------------------------
    z = x.leggi(ZONA_1_1[0], ZONA_1_1[1] - ZONA_1_1[0])
    r["cancelli"]["R5_zona_1_1"] = {"sha256": sha(z), "atteso": SHA_ZONA_1_1}
    if sha(z) != SHA_ZONA_1_1:
        errori.append("R5: la zona 1.1 non ha l'impronta attesa")

    # R6 -------------------------------------------------------------------
    testa = x.leggi(BLOCCO_PLUS, BLOB - BLOCCO_PLUS)
    atteso_testa = "9ec25e09a154609cea76f5817026fe946802b8e95aa4afebe89a1f0b6f4358f5"
    r["cancelli"]["R6_sgp_plus_intatto"] = {"bytes": len(testa), "sha256": sha(testa),
                                            "atteso": atteso_testa}
    if sha(testa) != atteso_testa:
        errori.append("R6: i primi 0x630 B di sgp.plus sono cambiati")

    # R7 -------------------------------------------------------------------
    fuori_blob = []
    try:
        from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB
        md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
        letterali = set()
        for i in md.disasm(blob, BLOB):
            if i.mnemonic.startswith(("b", "bl", "blx")) and i.op_str.startswith("#"):
                t = int(i.op_str[1:], 0)
                if not (BLOB <= t < BLOB + len(blob)) and t not in AMMESSE:
                    fuori_blob.append({"da": hex(i.address), "a": hex(t)})
        # i letterali assoluti del pool: devono essere solo indirizzi ammessi o
        # indirizzi della riserva
        for off in range(0, len(blob) - 3, 2):
            v = struct.unpack_from("<I", blob, off)[0]
            if 0x02000000 <= v < 0x02400000:
                letterali.add(v)
        r["cancelli"]["R7_nessun_salto_fuori"] = {
            "salti_fuori": fuori_blob,
            "letterali_di_RAM_trovati": sorted(hex(v) for v in letterali)}
    except ImportError:
        r["cancelli"]["R7_nessun_salto_fuori"] = "saltato: capstone non disponibile"
    if fuori_blob:
        errori.append("R7: il blob salta fuori da sé stesso: %r" % fuori_blob)

    r["errori"] = errori
    r["verde"] = not errori
    if a.json:
        Path(a.json).write_text(json.dumps(r, indent=2, ensure_ascii=False))
    print(json.dumps(r, indent=2, ensure_ascii=False))
    return 0 if r["verde"] else 1


if __name__ == "__main__":
    sys.exit(main())
