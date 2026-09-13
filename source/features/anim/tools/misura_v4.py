#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SGP-1.2-ANIM-SOLIDO-01 — misura del moto **dentro la finestra giusta**.

`SGP-1.2-RIFINITURA-01/tools/misura_anim.py` misura tutta la corsa. Va bene
per una corsa che è quasi tutta lotta; non va bene qui, dove la corsa comincia
in overworld e passa da un warp: **fuori dalla lotta gli indirizzi del Pokepic
contengono altro** (sono heap riusato), e infilarli nella statistica produce
numeri come «ampiezza 6555 px». Non è un difetto della ROM: è una misura fatta
dove il dato non esiste.

Qui la finestra è definita dal **contatore del task**: i fotogrammi in cui
`hits` cresce sono, per definizione, quelli in cui il task di quel lottatore
esiste ed è vivo. È lo stesso criterio con cui il gioco decide di disegnarlo.

Uso:
  misura_v4.py CORSA/frames.csv [--json F] [--prefisso a0] [--margine 2]

GPL-3.0-or-later.
"""
import argparse
import csv
import json
import sys


def num(v):
    try:
        return int(str(v), 0)
    except (TypeError, ValueError):
        return None


def s16(v):
    return None if v is None else (v - 0x10000 if v >= 0x8000 else v)


def finestra(righe):
    """Gli indici in cui `hits` cresce: il task e' vivo."""
    h = [num(r.get("hits")) for r in righe]
    vivi = [i for i in range(1, len(h))
            if h[i] is not None and h[i - 1] is not None and h[i] > h[i - 1]]
    if not vivi:
        return []
    return list(range(vivi[0], vivi[-1] + 1))


def periodo(vals):
    if not vals:
        return None
    m = max(vals)
    picchi = [i for i in range(1, len(vals) - 1)
              if vals[i] == m and vals[i] >= vals[i - 1] and vals[i] > vals[i + 1]]
    if len(picchi) < 2:
        return None
    passi = [picchi[i + 1] - picchi[i] for i in range(len(picchi) - 1)]
    return round(sum(passi) / len(passi), 2)


def serie(righe, col, segno=False):
    fuori = []
    for r in righe:
        v = num(r.get(col))
        if v is None:
            continue
        fuori.append(s16(v) if segno else v)
    return fuori


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("frames")
    ap.add_argument("--json")
    ap.add_argument("--prefisso", default="a0")
    a = ap.parse_args()

    tutte = list(csv.DictReader(open(a.frames)))
    idx = finestra(tutte)
    if not idx:
        print("nessuna finestra: il task non gira mai in questa corsa", file=sys.stderr)
        righe = []
    else:
        righe = [tutte[i] for i in idx]
    out = {"fotogrammi_totali": len(tutte), "finestra": [idx[0], idx[-1]] if idx else None,
           "fotogrammi_in_finestra": len(righe)}

    p = a.prefisso
    y = serie(righe, p + "_yoff", True)
    if y:
        out["yoffset"] = {
            "min": min(y), "max": max(y), "ampiezza_px": (max(y) - min(y)) / 2.0,
            "periodo_fotogrammi": periodo(y),
            "periodo_secondi": round(periodo(y) / 60.0, 3) if periodo(y) else None,
            "salto_massimo_px": max(abs(y[i + 1] - y[i]) for i in range(len(y) - 1)),
            "fermi_su_finestre_di_4": None,
        }
        # criterio 1 (fluidita'): quante finestre di 4 fotogrammi non cambiano
        ferme = sum(1 for i in range(0, len(y) - 4, 4)
                    if len(set(y[i:i + 4])) == 1)
        totali = max(1, len(range(0, len(y) - 4, 4)))
        out["yoffset"]["fermi_su_finestre_di_4"] = round(100.0 * ferme / totali, 1)
    for nome, col, segno in (("shadow_y", p + "_shy", True),
                             ("shadow_yoff", p + "_shyoff", True),
                             ("affineW", p + "_affw", False),
                             ("affineH", p + "_affh", False),
                             ("posa", p + "_step", False),
                             ("animActive", p + "_active", False),
                             ("shadow_flags", p + "_shflag", False)):
        v = serie(righe, col, segno)
        if v:
            out[nome] = {"min": min(v), "max": max(v), "escursione": max(v) - min(v),
                         "distinti": sorted(set(v))[:8]}
    if "shadow_flags" in out:
        f = out["shadow_flags"]["min"]
        out["classe_di_taglia"] = (f >> 5) & 3
        out["ombra_disegnata"] = bool((f & 3) != 0 and ((f >> 5) & 3) != 0)
    for col in ("hits", "hits_on", "hits_busy", "blinks", "stopvisti", "puliti",
                "last_cls", "chunk_anim"):
        v = serie(righe, col)
        if v:
            out[col] = {"primo": v[0], "ultimo": v[-1]}
    # controlli finali, fuori dalla finestra: lo stato dopo la fermata
    if idx and idx[-1] + 4 < len(tutte):
        coda = tutte[idx[-1] + 1:idx[-1] + 60]
        out["dopo_la_fermata"] = {
            k: (s16(num(coda[-1].get(c))) if sg else num(coda[-1].get(c)))
            for k, c, sg in (("yoff", p + "_yoff", True), ("affw", p + "_affw", False),
                             ("affh", p + "_affh", False), ("step", p + "_step", False),
                             ("shyoff", p + "_shyoff", True))}
    print(json.dumps(out, indent=2))
    if a.json:
        open(a.json, "w").write(json.dumps(out, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
