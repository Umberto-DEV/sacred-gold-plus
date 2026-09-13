#!/usr/bin/env python3
"""Blocco TITOLO — rimozione della scritta duplicata «Developed by a fan» dal
titolo (NARC `a/0/4/6`, membro 0, tilemap SUB_2, righe 22-23 colonne 9-22: 56
byte da `0x011A..0x0135` a `0x0000`). SGP-1.2-TITOLO-01, applicato in luogo
(§7 del suo RAPPORTO.md).

**Adattatore**, non una porta: `features/title/tools/applica_titolo.py` non
usa ndspy (legge/scrive da se' intestazione NDS, FNT, FAT, NARC) ed e' gia'
idempotente e verificato (cancelli A0-A8, rilettore indipendente L1-L7,
mutanti M1-M3, corse a runtime P1-P7 — vedi il suo RAPPORTO.md). Non tocca
nessuna riserva ARM9/overlay: e' indipendente dagli altri sette blocchi e puo'
stare in qualunque punto della catena di `costruisci.py` (per convenzione,
ultimo: e' l'unico che lavora su un file system NARC invece che su ARM9).

**`applica_credito`/`rileggi_credito`** (SGP-1.2-INTEGRAZIONE-FINALE-02,
13/09/2026): stesso NARC `a/0/4/6`, ma membro 15 (tile del credito) invece del
membro 0 — indipendente dal passo sopra, si applica dopo senza precondizioni
incrociate. Adattatore verso `features/credit/tools/applica_credito.py`
(anch'esso senza ndspy, idempotente, cancelli A0-A8) per la scrittura;
`rileggi_credito.py` (che QUELLO usa ndspy: NintendoDSRom + narc, ridisegna i
tre livelli BG e misura il contrasto — famiglia di decoder indipendente da
`applica_credito.py`) resta per sottoprocesso, come `opzioni.rileggi`.
"""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from ..rom import sha

_SOURCE = Path(__file__).resolve().parents[2]
_TITOLO01 = _SOURCE / "features/title/tools"
_TITOLO02 = _SOURCE / "features/credit/tools"


def _carica(nome, percorso):
    if str(percorso.parent) not in sys.path:
        sys.path.insert(0, str(percorso.parent))
    spec = importlib.util.spec_from_file_location(nome, percorso)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def applica(rom: bytes) -> tuple[bytes, dict]:
    log = {"strumento": "sgp12/blocchi/titolo.py:applica (adattatore)"}
    m = _carica("orig_applica_titolo", _TITOLO01 / "applica_titolo.py")
    with tempfile.NamedTemporaryFile(suffix=".nds") as tf:
        tf.write(rom)
        tf.flush()
        prima = m.cancelli_lettura(tf.name)
        cambiati = m.applica(tf.name)
        dopo = m.cancelli_lettura(tf.name)
        finale = Path(tf.name).read_bytes()
    log["byte_cambiati"] = cambiati
    log["stato_prima"] = prima["stato"]
    log["stato_dopo"] = dopo["stato"]
    log["cancelli_dopo_tutti_verdi"] = dopo["tutti_verdi"]
    log["uscita_sha256"] = sha(finale)
    log["esito"] = "applicato" if cambiati else "gia-applicato"
    return finale, log


def rileggi(derivata: bytes) -> dict:
    """Rilettore, stile sgp12 ({esito_finale, cancelli}): richiama
    `cancelli_lettura()` dello stesso adattatore (vedi docstring di modulo:
    e' gia' un rilettore indipendente dall'`applica()` di TITOLO-01 — usa la
    propria parentela FNT/FAT/NARC per riconoscere lo stato, non riusa un
    percorso di scrittura)."""
    m = _carica("orig_applica_titolo_r", _TITOLO01 / "applica_titolo.py")
    with tempfile.NamedTemporaryFile(suffix=".nds") as tf:
        tf.write(derivata)
        tf.flush()
        r = m.cancelli_lettura(tf.name)
    esiti = [{"cancello": k, "esito": "verde" if v else "ROSSO"} for k, v in r["cancelli"].items()]
    stato_ok = r["stato"] == "già-applicato"
    esiti.append({"cancello": "STATO", "esito": "verde" if stato_ok else "ROSSO", "dettaglio": r["stato"]})
    tutto = r["tutti_verdi"] and stato_ok
    return {"esito_finale": "verde" if tutto else "ROSSO", "cancelli": esiti, "dettagli": r}


# ------------------------------------------------------------- blocco CREDITO
def applica_credito(rom: bytes) -> tuple[bytes, dict]:
    """Adattatore verso `SGP-1.2-TITOLO-02/tools/applica_credito.py::applica`
    (idempotente: la seconda chiamata cambia 0 byte, vedi `cancelli_lettura`)."""
    log = {"strumento": "sgp12/blocchi/titolo.py:applica_credito (adattatore)"}
    m = _carica("orig_applica_credito", _TITOLO02 / "applica_credito.py")
    with tempfile.NamedTemporaryFile(suffix=".nds") as tf:
        tf.write(rom)
        tf.flush()
        prima = m.cancelli_lettura(tf.name)
        cambiati = m.applica(tf.name)
        dopo = m.cancelli_lettura(tf.name)
        finale = Path(tf.name).read_bytes()
    log["byte_cambiati"] = cambiati
    log["stato_prima"] = prima["stato"]
    log["stato_dopo"] = dopo["stato"]
    log["cancelli_prima"] = prima["cancelli"]
    log["cancelli_dopo"] = dopo["cancelli"]
    log["cancelli_dopo_tutti_verdi"] = dopo["tutti_verdi"]
    log["uscita_sha256"] = sha(finale)
    log["esito"] = "applicato" if cambiati else "gia-applicato"
    return finale, log


def rileggi_credito(ingresso: bytes, derivata: bytes) -> dict:
    """Rilettore INDIPENDENTE per sottoprocesso (stesso schema di
    `opzioni.rileggi`): richiama `SGP-1.2-TITOLO-02/tools/rileggi_credito.py`,
    che non importa `applica_credito.py` e usa ndspy (NintendoDSRom + narc)
    per ridisegnare i tre livelli BG e misurare il contrasto — famiglia di
    decoder indipendente. Richiede l'interprete ndspy (README.md)."""
    with tempfile.NamedTemporaryFile(suffix=".nds") as ti, \
         tempfile.NamedTemporaryFile(suffix=".nds") as td:
        ti.write(ingresso)
        ti.flush()
        td.write(derivata)
        td.flush()
        cmd = [sys.executable, str(_TITOLO02 / "rileggi_credito.py"),
               "--rom", td.name, "--base", ti.name]
        r = subprocess.run(cmd, capture_output=True, text=True)
    try:
        rep = json.loads(r.stdout)
    except Exception:
        return {"esito_finale": "ROSSO", "cancelli": [],
                "strumento": "rileggi_credito.py (adattatore)",
                "errore": (r.stdout + r.stderr)[-4000:], "returncode": r.returncode}
    verde = bool(rep.get("tutti_verdi")) and r.returncode == 0
    cancelli = [{"cancello": k, "esito": "verde" if v else "ROSSO"} for k, v in rep.get("cancelli", {}).items()]
    return {"esito_finale": "verde" if verde else "ROSSO", "cancelli": cancelli,
            "strumento": "rileggi_credito.py (adattatore)", "returncode": r.returncode, "dettagli": rep}
