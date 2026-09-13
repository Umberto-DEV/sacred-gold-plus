#!/usr/bin/env python3
"""Blocco ``sgp.anim2``: moto su tutti i lottatori e sospensione nelle mosse.

Il blocco si applica dopo ``sgp.anim`` v4. La v4 resta intatta nella riserva;
i tre nuovi ganci di ov012 raggiungono la v5 e il vecchio gancio di coda torna
alla sua preimmagine vanilla. L'opzione condivisa ``anim`` resta spenta per
difetto nel chunk di ``sgp.plus``.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

from ..rom import Rifiuto

_SOURCE = Path(__file__).resolve().parents[2]
_TOOLS = _SOURCE / "features/anim2/tools"


def _carica(nome: str):
    if str(_TOOLS) not in sys.path:
        sys.path.insert(0, str(_TOOLS))
    p = _TOOLS / (nome + ".py")
    spec = importlib.util.spec_from_file_location("_sgp12_anim2_" + nome, p)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def applica(rom: bytes, build_dir, manifest_path=None) -> tuple[bytes, dict]:
    """Applica ARM9 e ov012 in memoria; non scrive file persistenti."""
    m = _carica("applica_anim2")
    try:
        return m.applica(bytes(rom), build_dir, manifest_path)
    except m.Rifiuto as exc:
        raise Rifiuto("ANIM2: %s" % exc) from exc


def rileggi(prima: bytes, dopo: bytes, build_dir) -> dict:
    """Rilegge blocco, ganci e ricompressione con il decoder indipendente."""
    m = _carica("rileggi_anim2")
    try:
        return m.rileggi(bytes(prima), bytes(dopo), build_dir)
    except Exception as exc:
        return {"esito_finale": "ROSSO", "problemi":
                ["%s: %s" % (type(exc).__name__, exc)]}
