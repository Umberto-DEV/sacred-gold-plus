#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""O1 — verifica che un copione di avvio arrivi davvero in overworld GIOCABILE.

Cancelli (CRITERI.md §1.3):
  O1.1  fs != 0, taskman == 0, runningFieldMap == 1, isPaused == 0, mapId atteso;
  O1.2  le coordinate X/Z CAMBIANO mentre il copione tiene premuto DOWN/UP
        (discriminante fra «overworld» e «menu disegnato sopra»);
  O1.3  3 corse identiche danno lo stesso mapId/X/Z al punto di controllo.

Uso:
  avvio.py --hg BIN --rom ROM --sram SAV --script S --out DIR --json F --mappa 96
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
from banco import Campo, RspSicuro as Rsp, RspError, attendi_overworld, leggibile  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hg", required=True)
    ap.add_argument("--rom", required=True)
    ap.add_argument("--sram", required=True)
    ap.add_argument("--script", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--json", required=True)
    ap.add_argument("--mappa", type=int, default=96)
    ap.add_argument("--porta", type=int, default=3333)
    ap.add_argument("--campionamento", type=float, default=45.0,
                    help="secondi di campionamento delle coordinate dopo l'overworld")
    a = ap.parse_args()

    os.makedirs(a.out, exist_ok=True)
    cmd = [a.hg, "--rom", a.rom, "--sram", a.sram, "--out", a.out,
           "--gdb-port", str(a.porta), "--script", a.script]
    t0 = time.time()
    proc = subprocess.Popen(cmd, stdout=open(os.path.join(a.out, "hg-stdout.log"), "w"),
                            stderr=open(os.path.join(a.out, "hg-stderr.log"), "w"))
    esito = {"comando": cmd, "mappa_attesa": a.mappa}
    try:
        g = Rsp(port=a.porta)
        g.cont_nowait()
        c = Campo(g)
        s = attendi_overworld(c, secondi=120.0)
        esito["overworld"] = leggibile(s)
        esito["t_overworld"] = round(time.time() - t0, 2)
        esito["O1_1"] = bool(Campo.fermo(s) and s.get("mapId") == a.mappa)
        print(f"overworld: mapId={s['mapId']} x={s['x']} z={s['z']} "
              f"t={esito['t_overworld']}s", flush=True)

        # O1.2 — il copione tiene DOWN poi UP: si campionano le coordinate
        posizioni = []
        scadenza = time.time() + a.campionamento
        while time.time() < scadenza:
            try:
                st = c.stato()
            except (RspError, OSError):
                break                      # il copione e' finito: fine del campionamento
            if st.get("fs") and "x" in st:
                p = (st["mapId"], st["x"], st["z"])
                if not posizioni or posizioni[-1] != p:
                    posizioni.append(p)
            if proc.poll() is not None:
                break
        esito["posizioni_campionate"] = posizioni
        esito["posizioni_distinte"] = len({p for p in posizioni})
        esito["O1_2"] = esito["posizioni_distinte"] > 1
        esito["controllo"] = {"mapId": s["mapId"], "x": s["x"], "z": s["z"]}
        esito["fine_sessione"] = "ok"
    except (RspError, OSError) as e:
        esito["fine_sessione"] = f"{type(e).__name__}: {e}"
    try:
        esito["rc"] = proc.wait(timeout=300)
    except subprocess.TimeoutExpired:
        proc.kill()
        esito["rc"] = "ucciso dopo 300 s"
    esito["secondi"] = round(time.time() - t0, 2)
    with open(a.json, "w") as f:
        json.dump(esito, f, indent=2, ensure_ascii=False)
    print(json.dumps({k: v for k, v in esito.items() if k != "posizioni_campionate"},
                     indent=2, ensure_ascii=False))
    return 0 if esito.get("O1_1") and esito.get("O1_2") else 1


if __name__ == "__main__":
    sys.exit(main())
