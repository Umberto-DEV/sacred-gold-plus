#!/usr/bin/env python3
"""A2.4/A2.5 — breakpoint su Pokepic_IsAnimFinished (0x020085DC) con conteggio per fotogramma.

Avvia `hg_runtime-gdb --gdb-port N` su uno script di corsa, si connette con il client RSP
minimo (tools/rsp.py), arma un breakpoint hardware e conta le fermate attribuendole al
fotogramma corrente, letto dalla RAM del gioco (game_vblank_counter = 0x021D1138) con il
pacchetto `m` dello stesso stub: nessun dato arriva da fuori il protocollo.

Uso:
  python3 bp_pokepic.py --hg BIN --rom ROM --script S --out DIR [--sram SAV] [--load ST]
                        [--bp 0x020085DC] [--porta 3333] [--json FILE] [--max-frames N]
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
    ap.add_argument("--trace-pc", action="store_true")
    ap.add_argument("--bp", default="0x020085DC")
    ap.add_argument("--porta", type=int, default=3333)
    ap.add_argument("--json", required=True)
    ap.add_argument("--attesa", type=float, default=None,
                    help="secondi massimi fra un `c` e la fermata successiva (default: senza limite)")
    args = ap.parse_args()

    bp = int(args.bp, 0)
    os.makedirs(args.out, exist_ok=True)
    cmd = [args.hg, "--rom", args.rom, "--out", args.out,
           "--gdb-port", str(args.porta)]
    if args.script:
        cmd += ["--script", args.script]
    if args.sram:
        cmd += ["--sram", args.sram]
    if args.load:
        cmd += ["--load", args.load]
    if args.frames:
        cmd += ["--frames", str(args.frames)]
    if args.trace_pc:
        cmd += ["--trace-pc"]

    log = open(os.path.join(args.out, "hg-stdout.log"), "w")
    err = open(os.path.join(args.out, "hg-stderr.log"), "w")
    t0 = time.time()
    proc = subprocess.Popen(cmd, stdout=log, stderr=err)

    per_frame = Counter()
    hits = 0
    pc_diversi = Counter()
    primo_stop = None
    try:
        g = Rsp(port=args.porta)
        g.add_bkpt(bp, 2)               # THUMB: kind = 2 byte
        while True:
            st = g.cont(attesa=args.attesa)
            if not st.startswith("S05"):
                print(f"fermata inattesa: {st!r}", file=sys.stderr)
                break
            hits += 1
            pc = g.reg(15)
            pc_diversi[pc] += 1
            f = g.u32(VBLANK)
            per_frame[f] += 1
            if primo_stop is None:
                primo_stop = {"pc": pc, "vblank": f, "stato": st}
    except (RspError, OSError) as e:
        fine = f"{type(e).__name__}: {e}"
    else:
        fine = "fermata inattesa"
    try:
        rc = proc.wait(timeout=120)
    except subprocess.TimeoutExpired:
        proc.kill()
        rc = f"ucciso dopo 120 s ({fine})"

    dt = time.time() - t0

    frames_con = sorted(per_frame)
    esito = {
        "comando": cmd,
        "breakpoint": f"0x{bp:08X}",
        "rc_hg_runtime": rc,
        "secondi": round(dt, 2),
        "fermate_totali": hits,
        "primo_stop": primo_stop,
        "pc_riportati": {f"0x{k:08X}": v for k, v in pc_diversi.items()},
        "fotogrammi_con_almeno_una_chiamata": len(frames_con),
        "vblank_min": frames_con[0] if frames_con else None,
        "vblank_max": frames_con[-1] if frames_con else None,
        "max_chiamate_in_un_fotogramma": max(per_frame.values()) if per_frame else 0,
        "istogramma_chiamate_per_fotogramma":
            dict(sorted(Counter(per_frame.values()).items())),
        "per_fotogramma": {str(k): per_frame[k] for k in frames_con},
        "fine_sessione": fine,
    }
    with open(args.json, "w") as f:
        json.dump(esito, f, indent=2)
    e2 = dict(esito)
    e2.pop("per_fotogramma")
    print(json.dumps(e2, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
