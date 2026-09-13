#!/usr/bin/env python3
"""SGP-1.2-PRESTAZIONI-NPC-01 — corsa di attraversamento del confine e metrica gap.

Genera lo script di corsa (N andate e ritorni Fiordoropoli <-> Percorso 34 a
partire da un savestate ancorato al confine), esegue `hg_runtime` **non
interattivo** e calcola dal solo `frames.csv`:

  * i **giri** del ciclo principale del gioco (cambio di `main_loop_jumps`) e il
    **gap** in fotogrammi DS fra un giro e il successivo — la stessa metrica di
    `12b` §3.2 e di `SGP-1.2-PRESTAZIONI-R8-01/tools/attribuisci.py`;
  * il gap massimo dentro ogni finestra di transizione (riconosciuta dal cambio
    dell'id mappa) e fuori;
  * la traccia di identita' `keymask|mappa|X|Z` per fotogramma, con sha256, per
    il criterio di non regressione di `CRITERI.md`.

Opzioni di intervento, tutte esterne alla ROM (servono al confronto prima/dopo
senza modificare nessun binario):
  --congela ADDR:VAL:W   emette un `freeze` prima della corsa.

Non apre ROM ne' salvataggi: passa i nomi al banco e legge `frames.csv`.
"""
import argparse
import csv
import hashlib
import json
import subprocess
import sys
from pathlib import Path

W_MAPPA = 0x0227D4A0
W_PX = 0x0227D4A8
W_PZ = 0x0227D4AC
W_SITO = 0x02000E28


def genera_script(n, giu, su, pausa, congela, precorsa):
    r = [
        "watch mappa 0x%08X 4" % W_MAPPA,
        "watch px 0x%08X 4" % W_PX,
        "watch pz 0x%08X 4" % W_PZ,
        "watch sito 0x%08X 2" % W_SITO,
    ]
    r += ["run %d" % precorsa] if precorsa else []
    for spec in congela:
        addr, val, w = spec.split(":")
        r.append("freeze %s %s %s" % (addr, val, w))
    for _ in range(n):
        r += ["run %d DOWN" % giu, "run %d" % pausa,
              "run %d UP" % su, "run %d" % pausa]
    return "\n".join(r) + "\n"


def gaps(rows):
    loops = [int(x["main_loop_jumps"]) for x in rows]
    fr = [int(x["frame"]) for x in rows]
    tick = [i for i in range(1, len(loops)) if loops[i] != loops[i - 1]]
    return [(fr[tick[i]], tick[i] - tick[i - 1]) for i in range(1, len(tick))]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--harness", default="<your build>/hg_runtime")
    ap.add_argument("--rom", required=True)
    ap.add_argument("--load", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--json", required=True)
    ap.add_argument("--ripetizioni", type=int, default=3)
    ap.add_argument("--giu", type=int, default=40)
    ap.add_argument("--su", type=int, default=40)
    ap.add_argument("--pausa", type=int, default=70)
    ap.add_argument("--precorsa", type=int, default=0)
    ap.add_argument("--congela", action="append", default=[])
    ap.add_argument("--etichetta", default="")
    a = ap.parse_args()

    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    sc = out / "corsa.script"
    sc.write_text(genera_script(a.ripetizioni, a.giu, a.su, a.pausa,
                                a.congela, a.precorsa))
    cmd = [a.harness, "--rom", a.rom, "--out", str(out),
           "--load", a.load, "--script", str(sc), "--trace-pc"]
    p = subprocess.run(cmd, capture_output=True, text=True)
    (out / "stdout.log").write_text(p.stdout)
    (out / "stderr.log").write_text(p.stderr)

    rows = [r for r in csv.DictReader((out / "frames.csv").open())
            if r["frame"].isdigit()]
    g = gaps(rows)
    by = {int(r["frame"]): r for r in rows}

    # finestre di transizione: fotogrammi in cui l'id mappa cambia, +/- 12
    cambi = []
    prev = None
    for r in rows:
        m = int(r["mappa"], 16)
        if prev is not None and m != prev:
            cambi.append((int(r["frame"]), prev, m))
        prev = m
    fin = set()
    for f, _, _ in cambi:
        fin.update(range(f - 12, f + 13))

    dentro = [(f, x) for f, x in g if f in fin]
    fuori = [(f, x) for f, x in g if f not in fin]

    traccia = "\n".join(
        "%s|%s|%s|%s" % (r["keymask"], r["mappa"], r["px"], r["pz"])
        for r in rows)
    scanl = {r["scanlines"] for r in rows}
    siti = {r["sito"] for r in rows}

    esito = {
        "etichetta": a.etichetta,
        "comando": cmd,
        "congela": a.congela,
        "rc": p.returncode,
        "fotogrammi": len(rows),
        "giri": len(g),
        "cambi_mappa": [{"frame": f, "da": d, "a": v} for f, d, v in cambi],
        "gap_max_dentro_transizione": max([x for _, x in dentro], default=None),
        "gap_max_fuori_transizione": max([x for _, x in fuori], default=None),
        "istogramma_gap_dentro": {str(k): [x for _, x in dentro].count(k)
                                  for k in sorted(set(x for _, x in dentro))},
        "istogramma_gap_fuori": {str(k): [x for _, x in fuori].count(k)
                                 for k in sorted(set(x for _, x in fuori))},
        "gap_dentro": [{"frame": f, "gap": x} for f, x in dentro if x > 2],
        "precondizioni": {
            "P1_scanlines_263": sorted(scanl) == ["263"],
            "P7_sito_0x02000E28": sorted(siti),
        },
        "traccia_sha256": hashlib.sha256(traccia.encode()).hexdigest(),
        "traccia_righe": len(rows),
    }
    Path(a.json).write_text(json.dumps(esito, indent=1))
    breve = {k: v for k, v in esito.items() if k not in ("gap_dentro", "comando")}
    print(json.dumps(breve, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
