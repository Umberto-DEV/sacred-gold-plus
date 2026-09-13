#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SGP-1.2-RIFINITURA-01 — breakpoint su PlaySE, per vedere se i suoni scattano.

Derivato da `SGP-1.2-RUNTIME-02/tools/bp_pokepic.py` (che resta invariato): stessa
impostazione, stesso client RSP, stesso modo di attribuire le fermate al
fotogramma leggendo `game_vblank_counter` dalla RAM con il pacchetto `m`. L'unica
differenza voluta: qui si registra anche **r0**, che per `PlaySE(u32 id)` e' l'id
del suono. Serve al cancello A3a: «i suoni di scorrimento, conferma e annulla
scattano davvero» non si dimostra leggendo il sorgente, si dimostra fermando il
processore su quella chiamata e guardendo che id passa.

Uso: bp_playse.py --hg BIN --rom ROM --script S --out DIR --json F [--sram SAV]
                  [--bp 0x0200604C] [--porta 3334] [--da VBLANK] [--a VBLANK]
"""
import argparse
import json
import os
import subprocess
import sys
import time
from collections import Counter

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "SGP-1.2-RUNTIME-02", "tools"))
from rsp import Rsp, RspError  # noqa: E402

VBLANK = 0x021D1138
NOSTRI = {1500: "scorrimento", 1562: "conferma", 2368: "annullamento"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hg", required=True)
    ap.add_argument("--rom", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--script")
    ap.add_argument("--sram")
    ap.add_argument("--bp", default="0x0200604C")
    ap.add_argument("--porta", type=int, default=3334)
    ap.add_argument("--json", required=True)
    ap.add_argument("--attesa", type=float, default=None)
    args = ap.parse_args()

    bp = int(args.bp, 0)
    os.makedirs(args.out, exist_ok=True)
    cmd = [args.hg, "--rom", args.rom, "--out", args.out, "--gdb-port", str(args.porta)]
    if args.script:
        cmd += ["--script", args.script]
    if args.sram:
        cmd += ["--sram", args.sram]

    log = open(os.path.join(args.out, "hg-stdout.log"), "w")
    err = open(os.path.join(args.out, "hg-stderr.log"), "w")
    t0 = time.time()
    proc = subprocess.Popen(cmd, stdout=log, stderr=err)

    eventi = []
    try:
        g = Rsp(port=args.porta)
        g.add_bkpt(bp, 2)
        while True:
            st = g.cont(attesa=args.attesa)
            if not st.startswith("S05"):
                break
            eventi.append({"vblank": g.u32(VBLANK), "id": g.reg(0), "pc": g.reg(15)})
    except (RspError, OSError) as e:
        fine = f"{type(e).__name__}: {e}"
    else:
        fine = "fermata inattesa"
    try:
        rc = proc.wait(timeout=180)
    except subprocess.TimeoutExpired:
        proc.kill()
        rc = f"ucciso dopo 180 s ({fine})"

    per_id = Counter(e["id"] for e in eventi)
    esito = {
        "comando": cmd,
        "breakpoint": f"0x{bp:08X}",
        "rc_hg_runtime": rc,
        "secondi": round(time.time() - t0, 2),
        "chiamate_totali": len(eventi),
        "per_id": {str(k): v for k, v in sorted(per_id.items())},
        "per_id_nostri": {NOSTRI[k]: v for k, v in sorted(per_id.items()) if k in NOSTRI},
        "sequenza": [{"vblank": e["vblank"], "id": e["id"],
                      "nome": NOSTRI.get(e["id"], "")} for e in eventi],
        "fine_sessione": fine,
    }
    with open(args.json, "w") as f:
        json.dump(esito, f, indent=2)
    e2 = dict(esito)
    e2["sequenza"] = e2["sequenza"][-40:]
    print(json.dumps(e2, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
