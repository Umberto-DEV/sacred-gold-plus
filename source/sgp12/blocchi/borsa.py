#!/usr/bin/env python3
"""Blocco BORSA composto: premi, messaggio 199, appendici e gancio ARM9.

Il blocco riceve la ROM nello stato prodotto dai blocchi 1.2 precedenti. Le
prime tre trasformazioni liberano e riusano spazio nei due NARC; l'ultima
installa ``sgp.borsa`` nella riserva ARM9. Ogni passaggio e' fail-closed e il
rilettore conserva quattro verdetti indipendenti, oltre al confronto esatto
con la ricostruzione attesa.
"""
from __future__ import annotations

import hashlib
import importlib.util
import os
import sys
import tempfile
from pathlib import Path

from ..rom import Rifiuto, esigi

_SOURCE = Path(__file__).resolve().parents[2]
_FEATURE = _SOURCE / "features" / "borsa"
_TOOLS = _FEATURE / "tools"


def _carica(nome: str):
    if str(_TOOLS) not in sys.path:
        sys.path.insert(0, str(_TOOLS))
    percorso = _TOOLS / (nome + ".py")
    spec = importlib.util.spec_from_file_location("_sgp12_borsa_" + nome, percorso)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def _pret_source(build: Path) -> Path:
    dalla_variabile = os.environ.get("SGP_PRET_SOURCE")
    p = Path(dalla_variabile) if dalla_variabile else build / "pret-source"
    esigi((p / "charmap.txt").is_file(),
          "BORSA: charmap.txt non trovato in %s. Indicare il checkout "
          "pret/pokeheartgold con SGP_PRET_SOURCE=<checkout>." % p)
    esigi((p / "tools/py_scripts/scrcmd.json").is_file(),
          "BORSA: tools/py_scripts/scrcmd.json non trovato nel checkout pret %s."
          % p)
    return p


def pret_disponibile(build) -> bool:
    build = Path(build)
    dalla_variabile = os.environ.get("SGP_PRET_SOURCE")
    p = Path(dalla_variabile) if dalla_variabile else build / "pret-source"
    return ((p / "charmap.txt").is_file()
            and (p / "tools/py_scripts/scrcmd.json").is_file())


def _sha(dati: bytes) -> str:
    return hashlib.sha256(bytes(dati)).hexdigest()


def _primi_tre_stadi(rom: bytes, lingua: str, pret: Path):
    premi = _carica("premi_disfa")
    testo = _carica("applica_199")
    appendici = _carica("applica_appendici")
    try:
        dopo_premi, rapporto_premi = premi.disfa_rom(rom)
        dopo_testo, rapporto_testo = testo.applica_bank199_bytes(
            dopo_premi, lingua, pret)
        esigi(dopo_testo is not None,
              "BORSA/testo199: il messaggio era gia' applicato in uno stato "
              "che richiedeva ancora premi_disfa")
        dopo_appendici, rapporto_appendici = appendici.applica(
            dopo_testo, pret / "tools/py_scripts/scrcmd.json")
    except (premi.Rifiuto, testo.Rifiuto, appendici.Rifiuto) as exc:
        raise Rifiuto("BORSA: %s" % exc) from exc
    return (dopo_premi, dopo_testo, dopo_appendici,
            rapporto_premi, rapporto_testo, rapporto_appendici)


def applica(rom: bytes, build_dir, lingua: str,
            manifest_path=None) -> tuple[bytes, dict]:
    """Applica i quattro stadi, senza scrivere file persistenti."""
    esigi(lingua in ("EN", "IT"), "BORSA: lingua non supportata: %r" % lingua)
    build = Path(build_dir)
    pret = _pret_source(build)
    (dopo_premi, dopo_testo, dopo_appendici,
     rapporto_premi, rapporto_testo, rapporto_appendici) = _primi_tre_stadi(
         rom, lingua, pret)

    arm9 = _carica("applica_borsa")
    try:
        with tempfile.NamedTemporaryFile(suffix=".nds") as ingresso:
            ingresso.write(dopo_appendici)
            ingresso.flush()
            finale, rapporto_arm9 = arm9.applica(
                Path(ingresso.name), build, _FEATURE / "permissivi-1.2.tsv",
                pret / "tools/py_scripts/scrcmd.json", manifest_path)
    except arm9.Rifiuto as exc:
        raise Rifiuto("BORSA/ARM9: %s" % exc) from exc

    return finale, {
        "strumento": "sgp12/blocchi/borsa.py:applica",
        "esito": "applicato",
        "lingua": lingua,
        "sha256_ingresso": _sha(rom),
        "sha256_uscita": _sha(finale),
        "stadi": {
            "premi": rapporto_premi,
            "testo199": rapporto_testo,
            "appendici": rapporto_appendici,
            "arm9": rapporto_arm9,
        },
    }


def rileggi(prima: bytes, dopo: bytes, build_dir, lingua: str) -> dict:
    """Rilegge i quattro passaggi e boccia anche un solo byte inatteso."""
    build = Path(build_dir)
    problemi = []
    rapporto = {
        "strumento": "sgp12/blocchi/borsa.py:rileggi",
        "lingua": lingua,
        "sha256_prima": _sha(prima),
        "sha256_dopo": _sha(dopo),
        "problemi": problemi,
        "rilettori": {},
    }
    try:
        esigi(lingua in ("EN", "IT"), "lingua non supportata: %r" % lingua)
        pret = _pret_source(build)
        (dopo_premi, dopo_testo, dopo_appendici,
         _rp, _rt, _ra) = _primi_tre_stadi(prima, lingua, pret)

        premi_r = _carica("premi_rileggi")
        testo_r = _carica("rileggi_199")
        appendici_r = _carica("rileggi_appendici")
        arm9_a = _carica("applica_borsa")
        arm9_r = _carica("rileggi_borsa")

        rapporto["rilettori"]["premi"] = premi_r.rileggi(prima, dopo_premi)
        rapporto["rilettori"]["testo199"] = testo_r.rileggi_bytes(
            dopo_premi, dopo_testo, lingua, pret)

        with tempfile.TemporaryDirectory(prefix="sgp-borsa-rileggi-") as td:
            td = Path(td)
            p2, p3, p4 = td / "testo.nds", td / "appendici.nds", td / "finale.nds"
            p2.write_bytes(dopo_testo)
            p3.write_bytes(dopo_appendici)
            p4.write_bytes(dopo)
            rapporto["rilettori"]["appendici"] = appendici_r.rileggi(p2, p3, pret)
            atteso, _ = arm9_a.applica(
                p3, build, _FEATURE / "permissivi-1.2.tsv",
                pret / "tools/py_scripts/scrcmd.json", None)
            rapporto["rilettori"]["arm9"] = arm9_r.rileggi(
                p3, p4, build, _FEATURE / "permissivi-1.2.tsv",
                pret / "tools/py_scripts/scrcmd.json")

        if not rapporto["rilettori"]["premi"].get("ok"):
            problemi.append("RILETTORE_PREMI_ROSSO")
        if not rapporto["rilettori"]["testo199"].get("ok"):
            problemi.append("RILETTORE_TESTO199_ROSSO")
        if not rapporto["rilettori"]["appendici"].get("ok"):
            problemi.append("RILETTORE_APPENDICI_ROSSO")
        if rapporto["rilettori"]["arm9"].get("esito_finale") != "verde":
            problemi.append("RILETTORE_ARM9_ROSSO")
        if atteso != dopo:
            problemi.append("USCITA_DIVERSA_DALLA_RICOSTRUZIONE_ATTESA")
    except Exception as exc:
        # Un rilettore deve dare ROSSO anche su input malformato, non perdere
        # il verdetto dietro un traceback. Il tipo conserva l'origine.
        problemi.append("%s: %s" % (type(exc).__name__, exc))

    rapporto["esito_finale"] = "verde" if not problemi else "ROSSO"
    return rapporto
