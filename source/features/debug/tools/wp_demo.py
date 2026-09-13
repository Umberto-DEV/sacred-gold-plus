#!/usr/bin/env python3
"""A2.6 — watchpoint di scrittura (pacchetto RSP `Z2`) su `hg_runtime-gdb`.

Un solo watchpoint per corsa, di proposito: il pacchetto di fermata del gdbstub di
melonDS 906e9ebb e' un `S05` nudo (GdbCmds.cpp:585-598, i rami `T%02Xwatch:` sono
commentati nel sorgente) e non dice quale watchpoint ha scattato. Con un watchpoint
per corsa l'attribuzione e' certa.

Uso:
  python3 wp_demo.py --hg BIN --rom ROM --out DIR --wp 0x023D8000 [--lung 4] ...
"""
import argparse
import json
import os
import subprocess
import sys
import time
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rsp import Rsp, RspError  # noqa: E402

VBLANK = 0x021D1138


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hg", required=True)
    ap.add_argument("--rom", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--script")
    ap.add_argument("--sram")
    ap.add_argument("--load")
    ap.add_argument("--frames", type=int)
    ap.add_argument("--wp", required=True)
    ap.add_argument("--lung", type=int, default=4)
    ap.add_argument("--porta", type=int, default=3333)
    ap.add_argument("--json", required=True)
    ap.add_argument("--attesa", type=float, default=600.0)
    ap.add_argument("--max-fermate", type=int, default=200,
                    help="oltre questo numero di fermate il watchpoint viene tolto e la corsa prosegue")
    args = ap.parse_args()

    wp = int(args.wp, 0)
    os.makedirs(args.out, exist_ok=True)
    cmd = [args.hg, "--rom", args.rom, "--out", args.out, "--gdb-port", str(args.porta)]
    for opt, val in (("--script", args.script), ("--sram", args.sram), ("--load", args.load)):
        if val:
            cmd += [opt, val]
    if args.frames:
        cmd += ["--frames", str(args.frames)]

    log = open(os.path.join(args.out, "hg-stdout.log"), "w")
    err = open(os.path.join(args.out, "hg-stderr.log"), "w")
    t0 = time.time()
    proc = subprocess.Popen(cmd, stdout=log, stderr=err)

    fermate = []
    pc_scrittori = Counter()
    tolto = False
    try:
        g = Rsp(port=args.porta)
        g.add_watch_write(wp, args.lung)
        while True:
            st = g.cont(attesa=args.attesa)
            if not st.startswith("S05"):
                break
            pc = g.reg(15)
            pc_scrittori[pc] += 1
            if len(fermate) < 40:
                fermate.append({"pc": f"0x{pc:08X}", "vblank": g.u32(VBLANK)})
            if sum(pc_scrittori.values()) >= args.max_fermate and not tolto:
                g.del_watch_write(wp, args.lung)   # basta: la corsa deve finire
                tolto = True
    except (RspError, OSError) as e:
        fine = f"{type(e).__name__}: {e}"
    else:
        fine = "fermata inattesa"
    try:
        rc = proc.wait(timeout=180)
    except subprocess.TimeoutExpired:
        proc.kill()
        rc = "ucciso dopo 180 s"
    dt = time.time() - t0

    esito = {
        "comando": cmd,
        "watchpoint": {"indirizzo": f"0x{wp:08X}", "lunghezza": args.lung, "tipo": "Z2 (scrittura)"},
        "rc_hg_runtime": rc,
        "secondi": round(dt, 2),
        "fermate_totali": sum(pc_scrittori.values()),
        "watchpoint_tolto_dopo_max": tolto,
        "pc_scrittori": {f"0x{k:08X}": v for k, v in pc_scrittori.most_common(20)},
        "prime_fermate": fermate,
        "fine_sessione": fine,
    }
    with open(args.json, "w") as f:
        json.dump(esito, f, indent=2)
    print(json.dumps(esito, indent=2)[:3000])
    return 0


if __name__ == "__main__":
    sys.exit(main())
