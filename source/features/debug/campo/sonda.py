#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""O5/O6 — warp robusto + sonda: campiona (mapId, X, Z) per tutta la corsa.

Serve a due cose:
  * dimostrare con NUMERI quali caselle sono state provate e se il `mapId` cambia mai
    camminando (O5.4: «se nessun confine e' raggiungibile, dimostralo con le coordinate»);
  * riconoscere un cambio di mappa avvenuto CAMMINANDO (O6.2: entrare nella Centrale
    Elettrica dall'esterno) e annotare il fotogramma di gioco in cui avviene.

Uso:
  sonda.py --hg BIN --rom ROM --sram SAV --script S --out DIR --json F
           [--mappa 75] [--warp 0] [--fotogramma 3600]
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
from banco import (Campo, RspSicuro, RspError, VBLANK, warp_robusto,  # noqa: E402
                   attendi_overworld, leggibile)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hg", required=True)
    ap.add_argument("--rom", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--script", required=True)
    ap.add_argument("--sram")
    ap.add_argument("--mappa", type=int, default=0)
    ap.add_argument("--warp", type=int, default=0)
    ap.add_argument("--aggancio", default="0x0205C692")
    ap.add_argument("--fotogramma", type=int, default=3600)
    ap.add_argument("--porta", type=int, default=3333)
    ap.add_argument("--json", required=True)
    ap.add_argument("--secondi", type=float, default=240.0)
    a = ap.parse_args()

    os.makedirs(a.out, exist_ok=True)
    cmd = [a.hg, "--rom", a.rom, "--out", a.out, "--gdb-port", str(a.porta),
           "--script", a.script]
    if a.sram:
        cmd += ["--sram", a.sram]
    t0 = time.time()
    proc = subprocess.Popen(cmd, stdout=open(os.path.join(a.out, "hg-stdout.log"), "w"),
                            stderr=open(os.path.join(a.out, "hg-stderr.log"), "w"))
    esito = {"comando": cmd, "passi": [], "tracciato": []}

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
        if a.mappa:
            esito["warp"] = warp_robusto(g, c, a.mappa, a.warp, aggancio=a.aggancio,
                                         fotogramma=a.fotogramma, passo=passo)
        else:
            esito["partenza"] = leggibile(attendi_overworld(c, secondi=120.0))
        scadenza = time.time() + a.secondi
        ultimo = None
        while time.time() < scadenza:
            try:
                s = c.stato()
                v = g.u32(VBLANK)
            except (RspError, OSError):
                break
            if s.get("fs") and "x" in s:
                p = (s["mapId"], s["x"], s["z"])
                if p != ultimo:
                    esito["tracciato"].append({"vblank": v, "mapId": p[0],
                                               "x": p[1], "z": p[2]})
                    ultimo = p
            if proc.poll() is not None:
                break
        mappe = sorted({r["mapId"] for r in esito["tracciato"]})
        esito["mappe_toccate"] = mappe
        if esito["tracciato"]:
            xs = [r["x"] for r in esito["tracciato"]]
            zs = [r["z"] for r in esito["tracciato"]]
            esito["estremi"] = {"x_min": min(xs), "x_max": max(xs),
                                "z_min": min(zs), "z_max": max(zs),
                                "caselle_distinte": len({(r["mapId"], r["x"], r["z"])
                                                         for r in esito["tracciato"]})}
        esito["cambi_mappa"] = [r for i, r in enumerate(esito["tracciato"])
                                if i and r["mapId"] != esito["tracciato"][i - 1]["mapId"]]
        passo("sonda", mappe=mappe, estremi=esito.get("estremi"),
              cambi=len(esito["cambi_mappa"]))
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
    print(json.dumps({k: v for k, v in esito.items()
                      if k not in ("passi", "tracciato")}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
