#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""O2 — warp con attesa SULLO STATO. Copia evoluta di
`SGP-1.2-RUNTIME-02/tools/warp.py`, che NON viene modificato.

Vedi `tools/banco.py` per il metodo e per le tre differenze sostanziali
(CPU mai lasciata ferma, aggancio scoperto per ROM, assestamento sullo stato).

Uso:
  warp.py --hg BIN --rom ROM --sram SAV --script S --out DIR --json F
          --mappa 253 [--warp 0] [--aggancio 0x…] [--colpi 3] [--porta 3333]
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time

QUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, QUI)
import banco  # noqa: E402
from banco import Campo, RspSicuro, RspError, warp_robusto  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hg", required=True)
    ap.add_argument("--rom", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--script", required=True)
    ap.add_argument("--sram")
    ap.add_argument("--mappa", type=int, required=True)
    ap.add_argument("--warp", type=int, default=0)
    ap.add_argument("--aggancio", default=None)
    ap.add_argument("--colpi", type=int, default=3)
    ap.add_argument("--porta", type=int, default=3333)
    ap.add_argument("--json", required=True)
    ap.add_argument("--budget", type=float, default=240.0)
    ap.add_argument("--fotogramma", type=int, default=0,
                    help="inietta quando game_vblank_counter raggiunge questo "
                         "valore: allinea due corse su ROM diverse")
    a = ap.parse_args()

    os.makedirs(a.out, exist_ok=True)
    cmd = [a.hg, "--rom", a.rom, "--out", a.out, "--gdb-port", str(a.porta),
           "--script", a.script]
    if a.sram:
        cmd += ["--sram", a.sram]
    t0 = time.time()
    proc = subprocess.Popen(cmd, stdout=open(os.path.join(a.out, "hg-stdout.log"), "w"),
                            stderr=open(os.path.join(a.out, "hg-stderr.log"), "w"))
    esito = {"comando": cmd, "passi": []}

    def passo(nome, **kw):
        kw["passo"] = nome
        kw["t"] = round(time.time() - t0, 2)
        esito["passi"].append(kw)
        print("[%7.2f] %s: %s" % (kw["t"], nome,
              " ".join("%s=%s" % (k, v) for k, v in kw.items()
                       if k not in ("t", "passo"))), file=sys.stderr, flush=True)

    try:
        g = RspSicuro(port=a.porta)
        g.cont_nowait()
        c = Campo(g)
        esito.update(warp_robusto(g, c, a.mappa, a.warp, aggancio=a.aggancio,
                                  colpi_minimi=a.colpi, budget_secondi=a.budget,
                                  fotogramma=a.fotogramma, passo=passo))
        esito["fine_sessione"] = "ok"
    except (RspError, OSError) as e:
        esito["fine_sessione"] = "%s: %s" % (type(e).__name__, e)
        passo("errore", errore=esito["fine_sessione"])
    try:
        esito["rc_hg_runtime"] = proc.wait(timeout=300)
    except subprocess.TimeoutExpired:
        proc.kill()
        esito["rc_hg_runtime"] = "ucciso dopo 300 s"
    esito["secondi"] = round(time.time() - t0, 2)
    with open(a.json, "w") as f:
        json.dump(esito, f, indent=2, ensure_ascii=False)
    print(json.dumps({k: v for k, v in esito.items() if k != "passi"}, indent=2,
                     ensure_ascii=False))
    return 0 if esito.get("assestata") else 1


if __name__ == "__main__":
    sys.exit(main())
