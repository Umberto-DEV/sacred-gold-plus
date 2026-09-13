#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""O2 — campagna di ripetizioni del warp robusto: N mappe x R ripetizioni.

Ogni corsa e' un processo `warp.py` indipendente (banco proprio, porta propria, copia
propria del salvataggio). Le corse girano a gruppi per non saturare la macchina: la
contesa di CPU non cambia l'esito (l'attesa e' sullo STATO, non sul tempo), ma allunga
i tempi di parete.

    campagna_warp.py --hg BIN --rom ROM --sram SAV --script S --out DIR --json F
                     --mappe 253,141,116,119,75 --ripetizioni 3 [--paralleli 4]
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

QUI = Path(__file__).resolve().parent


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hg", required=True)
    ap.add_argument("--rom", required=True)
    ap.add_argument("--sram", required=True)
    ap.add_argument("--script", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--json", required=True)
    ap.add_argument("--mappe", required=True)
    ap.add_argument("--warp", type=int, default=0)
    ap.add_argument("--ripetizioni", type=int, default=3)
    ap.add_argument("--paralleli", type=int, default=4)
    ap.add_argument("--porta0", type=int, default=4200)
    ap.add_argument("--etichetta", default="corsa")
    ap.add_argument("--colpi", type=int, default=3)
    a = ap.parse_args()

    mappe = [int(x) for x in a.mappe.split(",")]
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    lavori = []
    porta = a.porta0
    for m in mappe:
        for r in range(1, a.ripetizioni + 1):
            d = out / f"{a.etichetta}-{m}-{r}"
            d.mkdir(parents=True, exist_ok=True)
            sav = out / f"sav-{a.etichetta}-{m}-{r}.sav"
            shutil.copyfile(a.sram, sav)
            js = d / "warp.json"
            cmd = [sys.executable, str(QUI / "warp.py"), "--hg", a.hg, "--rom", a.rom,
                   "--sram", str(sav), "--out", str(d), "--script", a.script,
                   "--mappa", str(m), "--warp", str(a.warp), "--porta", str(porta),
                   "--colpi", str(a.colpi), "--json", str(js)]
            lavori.append((m, r, cmd, js, d))
            porta += 1

    esiti = []
    t0 = time.time()
    for i in range(0, len(lavori), a.paralleli):
        gruppo = lavori[i:i + a.paralleli]
        proc = [(m, r, js, d, subprocess.Popen(cmd, stdout=subprocess.DEVNULL,
                                               stderr=subprocess.DEVNULL))
                for m, r, cmd, js, d in gruppo]
        for m, r, js, d, p in proc:
            p.wait()
            try:
                j = json.loads(Path(js).read_text())
            except Exception as e:
                j = {"fine_sessione": f"json illeggibile: {e}"}
            riga = {"mappa": m, "ripetizione": r,
                    "assestata": j.get("assestata"),
                    "mappa_raggiunta": j.get("mappa_raggiunta"),
                    "colpi": j.get("colpi_aggancio_dopo_ripristino"),
                    "secondi_assestamento": j.get("secondi_assestamento"),
                    "aggancio": (j.get("aggancio") or {}).get("aggancio"),
                    "origine_aggancio": (j.get("aggancio") or {}).get("origine"),
                    "dopo": j.get("dopo"), "fine": j.get("fine_sessione"),
                    "rc": j.get("rc_hg_runtime"), "dir": str(d)}
            esiti.append(riga)
            print(f"mappa {m:5d} rip {r}: assestata={riga['assestata']} "
                  f"mapId={(riga['dopo'] or {}).get('mapId')} "
                  f"x={(riga['dopo'] or {}).get('x')} z={(riga['dopo'] or {}).get('z')} "
                  f"colpi={riga['colpi']} t={riga['secondi_assestamento']}", flush=True)

    ok = sum(1 for e in esiti if e["assestata"])
    # O2.2: coordinate identiche fra le ripetizioni della stessa mappa
    coerenza = {}
    for m in mappe:
        pos = {(e["dopo"] or {}).get("mapId"), } if False else set()
        for e in esiti:
            if e["mappa"] == m and e["assestata"]:
                d = e["dopo"] or {}
                pos.add((d.get("mapId"), d.get("x"), d.get("z")))
        coerenza[str(m)] = {"posizioni_distinte": len(pos), "posizioni": sorted(pos)}
    ris = {"rom": os.path.basename(a.rom), "mappe": mappe,
           "ripetizioni": a.ripetizioni, "assestate": ok, "totale": len(esiti),
           "coerenza_coordinate": coerenza, "secondi": round(time.time() - t0, 2),
           "corse": esiti}
    Path(a.json).write_text(json.dumps(ris, indent=2, ensure_ascii=False))
    print(f"\nASSESTATE {ok}/{len(esiti)} in {ris['secondi']}s")
    return 0 if ok == len(esiti) else 1


if __name__ == "__main__":
    sys.exit(main())
