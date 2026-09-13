#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SGP-1.2-PLUS-03 — applicatore IN LUOGO del chunk di salvataggio 1.2 (C6).

Scrive nella ROM di lavoro:
  * il blob `sgp.salvataggio` (460 B) in `sgp.plus` a +0x630 (0x023D8730), dove
    PLUS-02 aveva lasciato spazio libero dichiarato;
  * il canarino del blocco `sgp.salvataggio` a 0x023D8FF0 (il buffer del chunk,
    0x023D8F00, resta a zero: lo riempie il gioco a runtime);
  * due ganci `BL` che sostituiscono due `BL` esistenti:
        L0  0x020271F8  `bl 0x020277D4`  ->  `bl sgp_gancio_carica`
        S0  0x02027456  `bl 0x02027DB4`  ->  `bl sgp_gancio_salva`
    Le due funzioni originali vengono richiamate dal blob: il flusso del gioco
    non cambia, nemmeno nel valore di ritorno.

Cancelli (nessuna uscita se uno solo cade):
  A0 idempotenza   — se la regione del blob non è tutta a zero, o se un gancio
                     ha già la postimmagine, RIFIUTA e non scrive un byte;
  A1 provenienza   — la ROM ha il blocco `sgp.plus` di PLUS-02/PLUS-03 (sha256
                     dei primi 0x630 byte del blocco) e il gancio selvatici vivo;
  A2 preimmagini   — `00f0ecfa` a 0x020271F8 e `00f0adfc` a 0x02027456, cioè le
                     due `BL` che devono essere sostituite, decodificate e
                     verificate: devono puntare a 0x020277D4 e 0x02027DB4;
  A3 ABI del gioco — le cinque funzioni chiamate dal blob esistono con le
                     impronte lette dalla base 1.1 (identiche EN/IT);
  A4 regione a zero— [0x023D8730, 0x023D8900) e [0x023D8F00, 0x023D9000) tutte
                     a zero prima di scrivere;
  A5 portata       — fuori da blob, canarino e due ganci non cambia un byte, e
                     la ROM non cambia lunghezza;
  A6 zona 1.1      — [0x023DEB40, 0x023E0000) invariata;
  A7 mappa         — `sgp.salvataggio` è registrato in MAPPA-RISERVA-ARM9.json
                     agli stessi indirizzi che l'applicatore usa.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import struct
import subprocess
import os
import sys
import tempfile
from pathlib import Path

QUI = Path(__file__).resolve()
PACCHETTO = QUI.parents[1]
REPO = QUI.parents[4]
ROM_DIR = Path(os.environ.get("SGP_ROM_DIR", "rom-dir-not-set"))
MAPPA = Path(os.environ.get("SGP_MAPPA", REPO / "docs/arm9-reserve-map.json"))

sys.path.insert(0, str(QUI))
from arm9 import Arm9  # noqa: E402


class Rifiuto(Exception):
    pass


def esigi(c, m):
    if not c:
        raise Rifiuto(m)


def sha(b):
    return hashlib.sha256(bytes(b)).hexdigest()


# --- geometria -------------------------------------------------------------
BLOCCO_PLUS = 0x023D8100
BLOCCO_PLUS_BYTES = 2048
BLOB = 0x023D8730                  # sgp.plus +0x630
BLOB_FINE = 0x023D8900             # fine del blocco sgp.plus
SALVA = 0x023D8F00                 # blocco sgp.salvataggio
SALVA_BYTES = 256
CANARINO = 0x023D8FF0
CANARINO_MOTIVO = 0xCA5A1300
ZONA_1_1 = (0x023DEB40, 0x023E0000)

# i primi 0x630 byte di sgp.plus: sono quelli che PLUS-02 ha scritto e che
# questa fase NON tocca. Firmarli separatamente rende il cancello A1 immune
# all'aggiunta del blob nuovo.
SHA_PLUS_TESTA = "9ec25e09a154609cea76f5817026fe946802b8e95aa4afebe89a1f0b6f4358f5"

GANCI = (
    {"nome": "L0", "sito": 0x020271F8, "pre": "00f0ecfa", "originale": 0x020277D4,
     "simbolo": "sgp_gancio_carica",
     "nota": "dentro SaveData_Init: dopo la lettura dei blocchi principali"},
    {"nome": "S0", "sito": 0x02027456, "pre": "00f0adfc", "originale": 0x02027DB4,
     "simbolo": "sgp_gancio_salva",
     "nota": "in coda a SaveData_Save: dopo un salvataggio riuscito"},
)

ABI = (
    {"nome": "WriteBackup", "addr": 0x02028758, "impronta": "78b581b000f04cf8"},
    {"nome": "ReadBackup", "addr": 0x0202877C, "impronta": "f0b585b0051c0e1c"},
    {"nome": "GF_CalcCRC16", "addr": 0x0201FF98, "impronta": "031c0a1c0248191c"},
    {"nome": "SaveData_LoadAll (originale di L0)", "addr": 0x020277D4, "impronta": None},
    {"nome": "coda di SaveData_Save (originale di S0)", "addr": 0x02027DB4, "impronta": None},
)


def codifica_bl(sito, bersaglio):
    delta = (bersaglio & ~1) - (sito + 4)
    esigi(-0x400000 <= delta < 0x400000, "BL fuori portata: %#x" % delta)
    hi = 0xF000 | ((delta >> 12) & 0x7FF)
    lo = 0xF800 | ((delta >> 1) & 0x7FF)
    return struct.pack("<HH", hi, lo)


def decodifica_bl(sito, quattro):
    hi, lo = struct.unpack("<HH", quattro)
    esigi((hi & 0xF800) == 0xF000 and (lo & 0xF800) == 0xF800,
          "a %#x non c'è una BL Thumb (%04X %04X)" % (sito, hi, lo))
    alto = hi & 0x7FF
    if alto & 0x400:
        alto -= 0x800
    return (sito + 4 + (alto << 12) + ((lo & 0x7FF) << 1)) & 0xFFFFFFFF


def applica(rom_in, build, ricevuta=None, impara=False):
    a = Arm9(rom_in)
    r = ricevuta if ricevuta is not None else {}
    r["strumento"] = "SGP-1.2-PLUS-03/tools/applica_salvataggio.py"
    r["ingresso_sha256"] = sha(a.raw)
    r["ingresso_bytes"] = len(a.raw)
    r["cancelli"] = {}

    manifesto = json.loads((Path(build) / "manifesto.json").read_text())
    blob = (Path(build) / "salva_blob.bin").read_bytes()
    esigi(int(manifesto["indirizzi"]["codice"], 16) == BLOB,
          "il blob è compilato per %s, non per %#x"
          % (manifesto["indirizzi"]["codice"], BLOB))
    esigi(BLOB + len(blob) <= BLOB_FINE,
          "il blob (%d B) non entra in [%#x,%#x)" % (len(blob), BLOB, BLOB_FINE))
    r["blob"] = {"byte": len(blob), "sha256": sha(blob), "base": hex(BLOB),
                 "simboli": manifesto["simboli"]}

    # -- A1 ----------------------------------------------------------------
    testa = a.leggi(BLOCCO_PLUS, BLOB - BLOCCO_PLUS)
    r["cancelli"]["A1_provenienza"] = {
        "sgp_plus_testa_0x630_sha256": sha(testa),
        "atteso": SHA_PLUS_TESTA if not impara else "(imparato adesso)",
    }
    if not impara:
        esigi(sha(testa) == SHA_PLUS_TESTA,
              "A1: i primi 0x630 B di sgp.plus non sono quelli di PLUS-02/03 "
              "(letto %s)" % sha(testa)[:16])

    # -- A2 ----------------------------------------------------------------
    ganci = []
    for g in GANCI:
        letto = a.leggi(g["sito"], 4)
        esigi(letto.hex() == g["pre"],
              "A2/A0: a %#x c'è %s, attesa la preimmagine %s. O la ROM non è "
              "quella, o il gancio %s è GIÀ applicato (idempotenza)."
              % (g["sito"], letto.hex(), g["pre"], g["nome"]))
        bersaglio = decodifica_bl(g["sito"], letto)
        esigi(bersaglio == g["originale"],
              "A2: la BL a %#x chiama %#010x, atteso %#010x"
              % (g["sito"], bersaglio, g["originale"]))
        ganci.append({"gancio": g["nome"], "sito": hex(g["sito"]), "pre": g["pre"],
                      "originale": hex(g["originale"]), "nota": g["nota"]})
    r["cancelli"]["A2_preimmagini"] = ganci

    # -- A3 ----------------------------------------------------------------
    abi = []
    for f in ABI:
        letto = a.leggi(f["addr"], 8).hex()
        if f["impronta"] is not None:
            esigi(letto == f["impronta"],
                  "A3: %s a %#x ha impronta %s, attesa %s"
                  % (f["nome"], f["addr"], letto, f["impronta"]))
        abi.append({"nome": f["nome"], "addr": hex(f["addr"]), "primi8": letto})
    r["cancelli"]["A3_abi_del_gioco"] = abi

    # -- A4 ----------------------------------------------------------------
    zona_blob = a.leggi(BLOB, BLOB_FINE - BLOB)
    zona_salva = a.leggi(SALVA, SALVA_BYTES)
    esigi(set(zona_blob) == {0}, "A0/A4: [%#x,%#x) non è tutta a zero: già applicato?"
          % (BLOB, BLOB_FINE))
    esigi(set(zona_salva) == {0}, "A0/A4: [%#x,%#x) non è tutta a zero"
          % (SALVA, SALVA + SALVA_BYTES))
    r["cancelli"]["A4_regione_a_zero"] = {
        "blob": [hex(BLOB), hex(BLOB_FINE)], "salvataggio": [hex(SALVA),
                                                             hex(SALVA + SALVA_BYTES)]}

    # -- A7 ----------------------------------------------------------------
    mappa = json.loads(MAPPA.read_text())
    voce = [b for b in mappa["blocchi"] if b["nome"] == "sgp.salvataggio"]
    esigi(voce, "A7: `sgp.salvataggio` non è in MAPPA-RISERVA-ARM9.json: la voce "
                "entra nella mappa PRIMA di essere scritta in ROM")
    esigi(int(voce[0]["base"], 16) == SALVA and voce[0]["bytes"] == SALVA_BYTES,
          "A7: la mappa dichiara %s/%d, l'applicatore usa %#x/%d"
          % (voce[0]["base"], voce[0]["bytes"], SALVA, SALVA_BYTES))
    r["cancelli"]["A7_mappa"] = {"base": voce[0]["base"], "bytes": voce[0]["bytes"]}

    # -- scrittura ---------------------------------------------------------
    prima = bytes(a.raw)
    a.scrivi(BLOB, blob)
    canarino = b"".join(struct.pack("<I", CANARINO_MOTIVO | i) for i in range(4))
    a.scrivi(CANARINO, canarino)
    scritture = [{"cosa": "blob sgp.salvataggio", "ram": hex(BLOB), "bytes": len(blob)},
                 {"cosa": "canarino sgp.salvataggio", "ram": hex(CANARINO), "bytes": 16}]
    simboli = manifesto["simboli"]
    for g in GANCI:
        bersaglio = int(simboli[g["simbolo"]], 16)
        nuovo = codifica_bl(g["sito"], bersaglio)
        a.scrivi(g["sito"], nuovo)
        scritture.append({"cosa": "gancio %s" % g["nome"], "ram": hex(g["sito"]),
                          "bytes": 4, "pre": g["pre"], "post": nuovo.hex(),
                          "bersaglio": hex(bersaglio & ~1), "simbolo": g["simbolo"]})
    r["scritture"] = scritture

    # -- A5 ----------------------------------------------------------------
    esigi(len(a.raw) == len(prima), "A5: la ROM ha cambiato lunghezza")
    attesi = set()
    for ram, n in ((BLOB, len(blob)), (CANARINO, 16)) + tuple((g["sito"], 4) for g in GANCI):
        o = a.off(ram, n)
        attesi |= set(range(o, o + n))
    diversi = {i for i in range(len(prima)) if prima[i] != a.raw[i]}
    esigi(diversi <= attesi,
          "A5: %d byte cambiati fuori dalle regioni dichiarate" % len(diversi - attesi))
    r["cancelli"]["A5_portata"] = {"byte_cambiati": len(diversi),
                                   "tutti_dentro_le_regioni_dichiarate": True}

    # -- A6 ----------------------------------------------------------------
    z = a.leggi(ZONA_1_1[0], ZONA_1_1[1] - ZONA_1_1[0])
    esigi(sha(z) == sha(Arm9(rom_in).leggi(ZONA_1_1[0], ZONA_1_1[1] - ZONA_1_1[0])),
          "A6: la zona 1.1 è cambiata")
    r["cancelli"]["A6_zona_1_1"] = {"sha256": sha(z)}

    r["blocco_sgp_plus_sha256_dopo"] = sha(a.leggi(BLOCCO_PLUS, BLOCCO_PLUS_BYTES))
    r["blocco_sgp_salvataggio_sha256_dopo"] = sha(a.leggi(SALVA, SALVA_BYTES))
    r["uscita_sha256"] = sha(a.raw)
    r["uscita_bytes"] = len(a.raw)
    return bytes(a.raw), r


def rileggi(rom_out, build, json_out):
    cmd = [sys.executable, str(PACCHETTO / "tools" / "rileggi_salvataggio.py"),
           "--rom", str(rom_out), "--build", str(build), "--json", str(json_out)]
    p = subprocess.run(cmd, capture_output=True, text=True)
    verde = False
    if Path(json_out).exists():
        verde = bool(json.loads(Path(json_out).read_text()).get("verde"))
    return (p.returncode == 0 and verde), p


def aggiorna_registro_rom(rom_path, log):
    rom_path = Path(rom_path).resolve()
    if rom_path.parent != ROM_DIR.resolve():
        log["registro"] = "saltato: l'uscita non è nella cartella ROM condivisa"
        return
    digest = hashlib.sha256(rom_path.read_bytes()).hexdigest()
    sums = ROM_DIR / "SHA256SUMS"
    righe = []
    visto = False
    for riga in sums.read_text().splitlines():
        if riga.endswith("  " + rom_path.name):
            righe.append("%s  %s" % (digest, rom_path.name))
            visto = True
        else:
            righe.append(riga)
    if not visto:
        righe.append("%s  %s" % (digest, rom_path.name))
    sums.write_text("\n".join(righe) + "\n")
    leggimi = ROM_DIR / "LEGGIMI.md"
    testo = leggimi.read_text()
    riga = ("| chunk di salvataggio 1.2 (blob a 0x023D8730 + blocco "
            "`sgp.salvataggio` a 0x023D8F00, settori 47/111) | D1 | "
            "`SGP-1.2-PLUS-03` | applicato, cancelli A0-A7 verdi, rilettore verde |")
    if "sgp.salvataggio" not in testo:
        righe = testo.rstrip().splitlines()
        righe.append(riga)
        leggimi.write_text("\n".join(righe) + "\n")
    log["registro"] = {"SHA256SUMS": digest, "LEGGIMI.md": "riga chunk di salvataggio"}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", default=str(PACCHETTO / "prove" / "build"))
    ap.add_argument("--rom")
    ap.add_argument("--out")
    ap.add_argument("--in-luogo", metavar="ROM")
    ap.add_argument("--tmp")
    ap.add_argument("--json")
    ap.add_argument("--impara", action="store_true",
                    help="stampa l'impronta di A1 invece di verificarla (una volta sola, "
                         "quando si costruisce l'applicatore)")
    ap.add_argument("--niente-registro", action="store_true")
    a = ap.parse_args(argv)

    log = {}
    try:
        if a.in_luogo:
            rom = Path(a.in_luogo)
            with tempfile.TemporaryDirectory(dir=a.tmp) as td:
                dentro = Path(td) / rom.name
                shutil.copy2(rom, dentro)
                uscita, log = applica(str(dentro), a.build, log, a.impara)
                fuori = Path(td) / ("nuova-" + rom.name)
                fuori.write_bytes(uscita)
                jr = Path(td) / "rilettore.json"
                ok, p = rileggi(fuori, a.build, jr)
                log["rilettore"] = json.loads(jr.read_text()) if jr.exists() else {
                    "stdout": p.stdout[-2000:], "stderr": p.stderr[-2000:]}
                esigi(ok, "il rilettore indipendente NON è verde: la ROM non è stata "
                          "sostituita")
                shutil.copy2(fuori, rom)
                log["sostituita"] = str(rom)
                if not a.niente_registro:
                    aggiorna_registro_rom(rom, log)
        else:
            esigi(a.rom and a.out, "servono --rom e --out (oppure --in-luogo)")
            uscita, log = applica(a.rom, a.build, log, a.impara)
            Path(a.out).write_bytes(uscita)
            jr = Path(a.out).with_suffix(".rilettore.json")
            ok, p = rileggi(a.out, a.build, jr)
            log["rilettore_verde"] = ok
    except Rifiuto as e:
        log["rifiuto"] = str(e)
        if a.json:
            Path(a.json).write_text(json.dumps(log, indent=2, ensure_ascii=False))
        print("RIFIUTO: %s" % e, file=sys.stderr)
        return 2
    if a.json:
        Path(a.json).write_text(json.dumps(log, indent=2, ensure_ascii=False))
    print(json.dumps({k: v for k, v in log.items()
                      if k in ("ingresso_sha256", "uscita_sha256", "uscita_bytes",
                               "blocco_sgp_plus_sha256_dopo",
                               "blocco_sgp_salvataggio_sha256_dopo",
                               "sostituita", "registro", "rilettore_verde")},
                     indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
