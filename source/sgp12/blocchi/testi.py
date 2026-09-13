#!/usr/bin/env python3
"""Blocco TESTI — le correzioni testuali della 1.2 dentro l'NARC dei messaggi
(nessun blocco ARM9, nessun overlay: solo un file dentro il filesystem della
ROM). Adattatore verso `features/texts/applica_testi.py::apply_to_rom_bytes`,
che e' gia' una funzione pura bytes-in/bytes-out.

**Due ingressi esterni**, nessuno dei quali sta in questo repository:

1. `charmap.txt`, dal checkout di `pret/pokeheartgold` al commit
   `0985e8718df4f25e64d6507d89c0c97c0d288981` (`source/README.md` spiega come
   prenderlo). Si indica con `SGP_PRET_SOURCE` o si mette in
   `sgp12/build/testi/pret-source/`.
2. `CORREZIONI.tsv`, la tabella che `applica_testi.py` consuma. Contiene il
   testo dei messaggi, che appartiene al gioco: qui e' pubblicato solo
   `build/testi/REGOLE.json` (il messaggio a cui ogni correzione appartiene,
   lo sha256 del testo che deve trovarci e le modifiche minime). Se il TSV non
   c'e', questo modulo lo **ricostruisce dalla ROM in ingresso** con
   `features/texts/genera_correzioni.py`, in un file temporaneo.
"""
from __future__ import annotations

import importlib.util
import os
import sys
import tempfile
from pathlib import Path

_SOURCE = Path(__file__).resolve().parents[2]
_TEXTS = _SOURCE / "features/texts"


def _carica(nome: str, percorso: Path):
    if str(_TEXTS) not in sys.path:
        sys.path.insert(0, str(_TEXTS))
    spec = importlib.util.spec_from_file_location(nome, percorso)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _pret_source(build: Path) -> Path:
    dalla_variabile = os.environ.get("SGP_PRET_SOURCE")
    if dalla_variabile:
        return Path(dalla_variabile)
    return build / "pret-source"


def applica(rom: bytes, build, lingua: str) -> tuple[bytes, dict]:
    build = Path(build)
    m = _carica("orig_applica_testi", _TEXTS / "applica_testi.py")
    pret_source = _pret_source(build)
    correzioni = build / "CORREZIONI.tsv"
    temporaneo = None
    ricostruito = None

    if not correzioni.exists():
        gen = _carica("genera_correzioni", _TEXTS / "genera_correzioni.py")
        regole = build / "REGOLE.json"
        righe, ricostruito = gen.costruisci(rom, lingua, regole, pret_source)
        import json
        campi = json.loads(regole.read_text(encoding="utf-8"))["campi_tsv"]
        temporaneo = tempfile.NamedTemporaryFile("w", suffix=".tsv", delete=False)
        temporaneo.close()
        correzioni = Path(temporaneo.name)
        gen.scrivi_tsv(righe, campi, correzioni)

    try:
        nuovo, summary = m.apply_to_rom_bytes(rom, lingua, correzioni, pret_source)
    finally:
        if temporaneo is not None:
            Path(temporaneo.name).unlink(missing_ok=True)

    summary["strumento"] = "sgp12/blocchi/testi.py:applica (adattatore)"
    if ricostruito is not None:
        summary["correzioni_ricostruite"] = ricostruito
    if nuovo is None:
        summary["esito"] = "nessuna-correzione-applicabile"
        return rom, summary
    summary["esito"] = "applicato"
    return nuovo, summary
