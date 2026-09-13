#!/usr/bin/env python3
"""Legge lo stato di campo (mappa corrente, X/Z, direzione) di una corsa, senza toccarla.

Serve a verificare, per esempio, che un salvataggio fatto DENTRO una delle mappe bersaglio
riparta davvero da quella mappa a freddo.

  python3 leggi_campo.py --hg BIN --rom ROM --sram SAV --out DIR --script S --json F
"""
import argparse
import json
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rsp import Rsp, RspError  # noqa: E402
from warp import Campo, attendi_fermo  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hg", required=True)
    ap.add_argument("--rom", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--script", required=True)
    ap.add_argument("--sram")
    ap.add_argument("--porta", type=int, default=3333)
    ap.add_argument("--json", required=True)
    ap.add_argument("--attesa", type=float, default=14.0)
    a = ap.parse_args()

    os.makedirs(a.out, exist_ok=True)
    cmd = [a.hg, "--rom", a.rom, "--out", a.out, "--gdb-port", str(a.porta),
           "--script", a.script]
    if a.sram:
        cmd += ["--sram", a.sram]
    p = subprocess.Popen(cmd, stdout=open(os.path.join(a.out, "hg-stdout.log"), "w"),
                         stderr=open(os.path.join(a.out, "hg-stderr.log"), "w"))
    esito = {"comando": cmd}
    try:
        g = Rsp(port=a.porta)
        g.cont_nowait()
        time.sleep(a.attesa)
        c = Campo(g)
        s = attendi_fermo(c)
        esito["campo"] = {k: (f"0x{v:08X}" if k in ("fs", "processManager", "taskman",
                                                    "location") and isinstance(v, int) else v)
                          for k, v in s.items()}
        esito["mapId"] = s["mapId"]
        print(f"mapId={s['mapId']} x={s['x']} z={s['z']} dir={s['dir']}", flush=True)
    except (RspError, OSError) as e:
        esito["errore"] = f"{type(e).__name__}: {e}"
        print(esito["errore"], file=sys.stderr)
    try:
        esito["rc"] = p.wait(timeout=180)
    except subprocess.TimeoutExpired:
        p.kill()
        esito["rc"] = "ucciso"
    with open(a.json, "w") as f:
        json.dump(esito, f, indent=2)
    return 0


if __name__ == "__main__":
    sys.exit(main())
