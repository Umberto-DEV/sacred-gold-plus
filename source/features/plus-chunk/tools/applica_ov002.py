#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SGP-1.2-PLUS-03 — applicatore IN LUOGO: riporta il gancio selvatici di D1
dentro `ov002` SENZA rilocare l'overlay in coda alla ROM.

Perche'. SGP-1.2-PLUS-02 aveva ricompresso `ov002` con ndspy ottenendo 42 968 B
(quattro piu' dei 42 964 dello slot) e, non entrandoci, aveva RILOCATO l'overlay
in coda: la ROM era cresciuta di 43 336 B (EN) / 43 408 B (IT) e nel file
restavano DUE copie di `ov002`, la vecchia (non patchata) al suo posto e la nuova
in coda. SGP-1.2-OVERLAY-01 (RAPPORTO §3, §8) ha misurato che questa e' la strada
da non prendere. Il compressore ad analisi ottima di OVERLAY-01 centra invece
**esattamente** i 42 964 B, e allora l'overlay si riscrive nel suo slot e nella
ROM cambia solo il corpo dell'overlay.

Che cosa fa, in ordine:
  1. `deriloca_ov002.deriloca` — rimette voce FAT, voce y9, dimensione usata e
     CRC16 dell'header ai valori della base e taglia la coda. Lo slot originale
     contiene ancora, byte per byte, il corpo ORIGINALE dell'overlay (cancello
     D2), quindi dopo il taglio il gancio selvatici non c'e' piu': e' il
     presupposto perche' la patch seguente trovi la sua preimmagine.
  2. `SGP-1.2-OVERLAY-01/tools/overlay_patch.py` — scrive `BL sgp_wild_hook` a
     0x02247D3A dentro l'immagine decompressa, ricomprime BLZ centrando i 42 964 B
     e riscrive IN LUOGO.
  3. `SGP-1.2-OVERLAY-01/tools/overlay_rileggi.py` — rilettore indipendente.
  4. cancelli propri di questo applicatore (A0-A5 sotto).
  5. con `--in-luogo`: sostituisce la ROM condivisa solo se tutto e' verde, poi
     aggiorna `SHA256SUMS` e `LEGGIMI.md` della cartella ROM.

Cancelli:
  A0 idempotenza   — su una ROM gia' in luogo (ov002 NON rilocato) rifiuta e non
                     scrive un byte;
  A1 provenienza   — la base dichiarata e' una delle due `base-1.1-*.nds` note;
  A2 gancio vivo   — la postimmagine a 0x02247D3A e' `BL sgp_wild_hook`, e il
                     bersaglio decodificato dalla BL e' davvero 0x023D8340;
  A3 blocco intatto— il blocco `sgp.plus` (0x023D8100, 2048 B) e i quattro ganci
                     allenatore in arm9 non vengono toccati da questa fase;
  A4 portata       — fuori dal corpo di ov002, da voce FAT/y9 e dall'header non
                     cambia un byte, e la ROM torna lunga quanto la base;
  A5 zona 1.1      — `[0x023DEB40, 0x023E0000)` invariata.
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
OVERLAY = REPO / "source/features/overlay/tools"
ROM_DIR = Path(os.environ.get("SGP_ROM_DIR", "rom-dir-not-set"))

sys.path.insert(0, str(OVERLAY))
sys.path.insert(0, str(PACCHETTO / "tools"))
sys.path.insert(0, str(QUI))

from overlay_patch import Rifiuto, applica as overlay_applica, esigi, sha  # noqa: E402
from deriloca_ov002 import deriloca  # noqa: E402
from arm9 import Arm9  # noqa: E402

BASI = {
    "281c2d68e442479e679d8b7e36566ade614d236151c65c9684bad6985461827d": "base-1.1-EN",
    "7b61646c627eb67cd991dbc33d68519edd69395468ea8b326e867fe98e62d077": "base-1.1-IT",
}

SITO_W0 = 0x02247D3A
PRE_W0 = bytes.fromhex("04a80078")
POST_W0 = bytes.fromhex("90f101fb")
SGP_WILD_HOOK = 0x023D8340
GUARDIA_OV002 = (0x02246C94, bytes.fromhex("00880328"))
BLOCCO = 0x023D8100
BLOCCO_BYTES = 2048
BLOCCO_SHA = "180775ce80f69a60f9533e1f989261779fa85634cfac40895e7bf537231ba534"
GANCI_T = (0x02073718, 0x02073802, 0x0207390C, 0x02073A0C)
ZONA_1_1 = (0x023DEB40, 0x023E0000)


def bersaglio_bl(indirizzo, quattro_byte):
    """Decodifica una BL Thumb-1 (due mezze parole) e ritorna l'indirizzo chiamato."""
    hi, lo = struct.unpack("<HH", quattro_byte)
    esigi((hi & 0xF800) == 0xF000 and (lo & 0xF800) == 0xF800,
          "A2: a %#x non c'e' una BL Thumb (%04X %04X)" % (indirizzo, hi, lo))
    alto = hi & 0x7FF
    if alto & 0x400:
        alto -= 0x800
    return (indirizzo + 4 + (alto << 12) + ((lo & 0x7FF) << 1)) & 0xFFFFFFFF


def applica_tutto(dati, dati_base, ricevuta=None):
    r = ricevuta if ricevuta is not None else {}
    r["strumento"] = "SGP-1.2-PLUS-03/tools/applica_ov002.py"
    r["ingresso_sha256"] = sha(dati)
    r["ingresso_bytes"] = len(dati)
    r["cancelli"] = {}

    # A1 -------------------------------------------------------------------
    nome_base = BASI.get(sha(dati_base))
    esigi(nome_base is not None,
          "A1: la base data non e' una base-1.1 nota (sha %s)" % sha(dati_base)[:16])
    r["cancelli"]["A1_provenienza"] = {"base": nome_base, "sha256": sha(dati_base)}

    # 1 + A0 ---------------------------------------------------------------
    r["fase_1_deriloca"] = {}
    try:
        intermedia, _ = deriloca(dati, dati_base, 2, r["fase_1_deriloca"])
    except Rifiuto as e:
        if str(e).startswith("D1:"):
            raise Rifiuto("A0 IDEMPOTENZA: ov002 non e' rilocato, questa ROM e' "
                          "gia' passata da qui (o non e' mai passata da PLUS-02). "
                          "Nessun byte scritto. [%s]" % e)
        raise
    r["cancelli"]["A0_idempotenza"] = {
        "ingresso_era_rilocato": True,
        "nota": "su una ROM gia' in luogo il cancello D1 di deriloca_ov002 "
                "rifiuta e questo applicatore non scrive nulla"}

    # 2 --------------------------------------------------------------------
    r["fase_2_overlay_patch"] = {}
    uscita, _ = overlay_applica(
        intermedia, None,
        guardie=[GUARDIA_OV002, (SITO_W0, PRE_W0)],
        patch=[{"addr": SITO_W0, "pre": PRE_W0, "post": POST_W0}],
        strategia="a", ricevuta=r["fase_2_overlay_patch"])

    a_out = Arm9(_scrivi_tmp(uscita))
    a_in = Arm9(_scrivi_tmp(dati))
    _pulisci_tmp()   # Arm9 legge tutto in memoria: le copie servono solo qui

    # A2 -------------------------------------------------------------------
    letto = _leggi_overlay(uscita, SITO_W0, 4)
    esigi(letto == POST_W0,
          "A2: a %#x c'e' %s, attesa %s" % (SITO_W0, letto.hex(), POST_W0.hex()))
    bers = bersaglio_bl(SITO_W0, letto)
    esigi(bers == SGP_WILD_HOOK,
          "A2: la BL a %#x chiama %#010x, atteso sgp_wild_hook %#010x"
          % (SITO_W0, bers, SGP_WILD_HOOK))
    r["cancelli"]["A2_gancio_vivo"] = {
        "sito": hex(SITO_W0), "pre": PRE_W0.hex(), "post": POST_W0.hex(),
        "bersaglio_decodificato": hex(bers), "atteso": hex(SGP_WILD_HOOK)}

    # A3 -------------------------------------------------------------------
    blocco = a_out.leggi(BLOCCO, BLOCCO_BYTES)
    esigi(hashlib.sha256(blocco).hexdigest() == BLOCCO_SHA,
          "A3: il blocco sgp.plus non ha l'impronta attesa")
    esigi(blocco == a_in.leggi(BLOCCO, BLOCCO_BYTES), "A3: il blocco e' cambiato")
    ganci = {}
    for g in GANCI_T:
        prima, dopo = a_in.leggi(g, 4), a_out.leggi(g, 4)
        esigi(prima == dopo, "A3: il gancio allenatore a %#x e' cambiato" % g)
        ganci[hex(g)] = dopo.hex()
    r["cancelli"]["A3_blocco_e_ganci_intatti"] = {
        "sgp_plus_sha256": BLOCCO_SHA, "ganci_allenatore": ganci}

    # A4 -------------------------------------------------------------------
    esigi(len(uscita) == len(dati_base),
          "A4: l'uscita e' %d B, la base %d" % (len(uscita), len(dati_base)))
    diversi = sum(1 for i in range(len(uscita)) if uscita[i] != intermedia[i])
    regioni = r["fase_2_overlay_patch"]["regioni_cambiate"]
    coperti = sum(x["bytes"] for x in regioni)
    esigi(diversi <= coperti,
          "A4: %d byte diversi ma le regioni dichiarate ne coprono %d" % (diversi, coperti))
    r["cancelli"]["A4_portata"] = {
        "uscita_bytes": len(uscita), "base_bytes": len(dati_base),
        "byte_diversi_dalla_intermedia": diversi,
        "regioni_dichiarate": regioni,
        "coda_rimossa_bytes": len(dati) - len(uscita)}

    # A5 -------------------------------------------------------------------
    z_in = a_in.leggi(ZONA_1_1[0], ZONA_1_1[1] - ZONA_1_1[0])
    z_out = a_out.leggi(ZONA_1_1[0], ZONA_1_1[1] - ZONA_1_1[0])
    esigi(z_in == z_out, "A5: la zona 1.1 e' cambiata")
    r["cancelli"]["A5_zona_1_1"] = {
        "intervallo": [hex(ZONA_1_1[0]), hex(ZONA_1_1[1])],
        "sha256": hashlib.sha256(z_out).hexdigest()}

    r["uscita_sha256"] = sha(uscita)
    r["uscita_bytes"] = len(uscita)
    return uscita, r


_TMP = []


def _pulisci_tmp():
    # Perdita corretta il 13/09/2026: i file temporanei .nds (126 MB l'uno) restavano in TemporaryItems.
    import os
    for nome in _TMP:
        try:
            os.unlink(nome)
        except OSError:
            pass
    _TMP.clear()


import atexit as _atexit
_atexit.register(_pulisci_tmp)


def _scrivi_tmp(dati):
    f = tempfile.NamedTemporaryFile(suffix=".nds", delete=False)
    f.write(dati)
    f.close()
    _TMP.append(f.name)
    return f.name


def _leggi_overlay(dati_rom, indirizzo, n):
    from overlay_patch import Rom
    rom = Rom(dati_rom)
    v, _crudo, img = rom.immagine_overlay(2)
    off = indirizzo - v["ram"]
    return bytes(img[off:off + n])


def rileggi(rom_out, rom_in, json_out):
    cmd = [sys.executable, str(OVERLAY / "overlay_rileggi.py"),
           "--rom", str(rom_out), "--ingresso", str(rom_in), "--overlay", "2",
           "--guardia", "0x02246C94:00880328",
           "--post", "0x02247D3A:" + POST_W0.hex(),
           "--json", str(json_out)]
    p = subprocess.run(cmd, capture_output=True, text=True)
    verde = False
    if Path(json_out).exists():
        verde = bool(json.loads(Path(json_out).read_text()).get("verde"))
    return p.returncode == 0 and verde, p


def aggiorna_registro_rom(rom_path, log):
    """Aggiorna la riga di SHA256SUMS del file prodotto e la riga «difficolta' Plus»
    di LEGGIMI.md. Non tocca nessun'altra riga."""
    rom_path = Path(rom_path).resolve()
    if rom_path.parent != ROM_DIR.resolve():
        log["registro"] = "saltato: l'uscita non e' nella cartella ROM condivisa"
        return
    digest = hashlib.sha256(rom_path.read_bytes()).hexdigest()
    sums = ROM_DIR / "SHA256SUMS"
    righe = sums.read_text().splitlines()
    nuove, visto = [], False
    for riga in righe:
        if riga.endswith("  " + rom_path.name):
            nuove.append("%s  %s" % (digest, rom_path.name))
            visto = True
        else:
            nuove.append(riga)
    if not visto:
        nuove.append("%s  %s" % (digest, rom_path.name))
    sums.write_text("\n".join(nuove) + "\n")
    leggimi = ROM_DIR / "LEGGIMI.md"
    testo = leggimi.read_text()
    vecchia = [r for r in testo.splitlines() if r.startswith("| difficoltà Plus")]
    nuova = ("| difficoltà Plus (blocco `sgp.plus` a 0x023D8100 + gancio selvatici "
             "in `ov002`, scritto IN LUOGO) | D1 | `SGP-1.2-PLUS-03` | applicato, "
             "cancelli A0-A5 verdi, rilettore verde, gancio vivo a freddo |")
    if vecchia:
        testo = testo.replace(vecchia[0], nuova)
        leggimi.write_text(testo)
    log["registro"] = {"SHA256SUMS": digest, "LEGGIMI.md": "riga difficoltà Plus aggiornata"}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True, help="base-1.1-{EN,IT}.nds")
    ap.add_argument("--rom", help="ROM di ingresso (con --out)")
    ap.add_argument("--out", help="ROM di uscita")
    ap.add_argument("--in-luogo", metavar="ROM",
                    help="applica sulla ROM condivisa: copia in scratchpad, applica, "
                         "rilegge, sostituisce SOLO se tutto e' verde")
    ap.add_argument("--tmp", help="cartella di scratchpad")
    ap.add_argument("--json", default=None)
    ap.add_argument("--niente-registro", action="store_true")
    a = ap.parse_args(argv)

    log = {}
    base = Path(a.base).read_bytes()
    try:
        if a.in_luogo:
            rom = Path(a.in_luogo)
            with tempfile.TemporaryDirectory(dir=a.tmp) as td:
                dentro = Path(td) / rom.name
                shutil.copy2(rom, dentro)
                uscita, log = applica_tutto(dentro.read_bytes(), base, log)
                fuori = Path(td) / ("nuova-" + rom.name)
                fuori.write_bytes(uscita)
                jr = Path(td) / "rilettore.json"
                ok, p = rileggi(fuori, dentro, jr)
                log["rilettore"] = json.loads(jr.read_text()) if jr.exists() else {
                    "stdout": p.stdout[-2000:], "stderr": p.stderr[-2000:]}
                esigi(ok, "il rilettore indipendente NON e' verde: la ROM non e' stata "
                          "sostituita")
                shutil.copy2(fuori, rom)
                log["sostituita"] = str(rom)
                if not a.niente_registro:
                    aggiorna_registro_rom(rom, log)
        else:
            esigi(a.rom and a.out, "servono --rom e --out (oppure --in-luogo)")
            uscita, log = applica_tutto(Path(a.rom).read_bytes(), base, log)
            Path(a.out).write_bytes(uscita)
            jr = Path(a.out).with_suffix(".rilettore.json")
            ok, p = rileggi(a.out, a.rom, jr)
            log["rilettore_verde"] = ok
    except Rifiuto as e:
        log["rifiuto"] = str(e)
        if a.json:
            Path(a.json).write_text(json.dumps(log, indent=2, ensure_ascii=False))
        print("RIFIUTO: %s" % e, file=sys.stderr)
        return 2
    finally:
        for t in _TMP:
            Path(t).unlink(missing_ok=True)
    if a.json:
        Path(a.json).write_text(json.dumps(log, indent=2, ensure_ascii=False))
    print(json.dumps({k: v for k, v in log.items()
                      if k in ("ingresso_sha256", "uscita_sha256", "uscita_bytes",
                               "sostituita", "registro")}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
