#!/usr/bin/env python3
"""SGP-1.2-PRESTAZIONI-NPC-01 — quanti fotogrammi restano senza NPC.

Dal savestate ancorato al confine cammina verso sud finche' l'id mappa cambia,
poi cattura N fotogrammi consecutivi (PPM) e, se gli si passa una corsa di
riferimento, conta **per fotogramma** i pixel diversi dallo schermo superiore
del riferimento. Il numero di fotogrammi consecutivi con differenza > soglia e'
la finestra in cui gli NPC non sono ancora disegnati.

Legge anche, a ogni fotogramma, lo stato del gancio (giri/clamp/salvato) se gli
si passa --stato: serve a distinguere «spento» da «mai raggiunto»
(CONTRATTO-D1 §2.2 di SGP-1.2-PLUS-01).

Le catture restano nella cartella della corsa: sono immagini dello schermo, non
contenuto della ROM, ma non vengono aperte nel contesto del modello — se ne
stampano solo i numeri.
"""
import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from banco import Banco, W_MAPPA, W_PZ  # noqa: E402


def leggi_ppm(p):
    d = Path(p).read_bytes()
    if not d.startswith(b"P6"):
        raise SystemExit("atteso PPM binario: " + str(p))
    # intestazione: P6\n<larg> <alt>\n<max>\n
    i, campi = 2, []
    while len(campi) < 3:
        while i < len(d) and d[i:i + 1].isspace():
            i += 1
        if d[i:i + 1] == b"#":
            while d[i:i + 1] not in (b"\n", b""):
                i += 1
            continue
        j = i
        while j < len(d) and not d[j:j + 1].isspace():
            j += 1
        campi.append(int(d[i:j]))
        i = j
    i += 1
    larg, alt = campi[0], campi[1]
    return larg, alt, d[i:i + larg * alt * 3]


def diversi(a, b, soglia=8):
    la, ha, da = leggi_ppm(a)
    lb, hb, db = leggi_ppm(b)
    if (la, ha) != (lb, hb):
        raise SystemExit("dimensioni diverse")
    # solo schermo superiore (meta' alta): e' quello dove si vedono gli NPC
    n = la * (ha // 2) * 3
    c = 0
    for k in range(0, n, 3):
        if (abs(da[k] - db[k]) + abs(da[k + 1] - db[k + 1])
                + abs(da[k + 2] - db[k + 2])) > soglia:
            c += 1
    return c, la * (ha // 2)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--harness", default="<your build>/hg_runtime")
    ap.add_argument("--rom", required=True)
    ap.add_argument("--load", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--json", required=True)
    ap.add_argument("--fotogrammi", type=int, default=20)
    ap.add_argument("--stato", type=lambda x: int(x, 0), default=0)
    ap.add_argument("--riferimento", default="",
                    help="cartella di una corsa precedente con le stesse catture")
    ap.add_argument("--soglia", type=int, default=8)
    a = ap.parse_args()

    b = Banco(a.harness, a.rom, a.out, load=a.load)
    m0 = b.read(W_MAPPA)
    passi = 0
    while passi < 200:
        b.cmd("run 1 DOWN")
        passi += 1
        if b.read(W_MAPPA) != m0:
            break
    else:
        b.chiudi()
        raise SystemExit("nessun cambio di mappa in 200 passi")
    cambio = {"passi": passi, "da": m0, "a": b.read(W_MAPPA), "z": b.read(W_PZ)}

    righe = []
    for i in range(a.fotogrammi):
        nome = "f%02d.ppm" % i
        b.cmd("capture " + nome)
        r = {"i": i, "file": nome, "z": b.read(W_PZ), "mappa": b.read(W_MAPPA)}
        if a.stato:
            r["stato"] = {
                "attivo_tetto_guardia": "0x%08X" % b.read(a.stato),
                "salvato_clamp": "0x%08X" % b.read(a.stato + 4),
                "giri": b.read(a.stato + 8),
            }
        righe.append(r)
        b.cmd("run 1")
    b.chiudi()

    if a.riferimento:
        for r in righe:
            c, tot = diversi(Path(a.out) / r["file"],
                             Path(a.riferimento) / r["file"], a.soglia)
            r["pixel_diversi"] = c
            r["pixel_totali"] = tot
            r["percentuale"] = round(100.0 * c / tot, 3)

    esito = {"rom": a.rom, "cambio_mappa": cambio,
             "riferimento": a.riferimento, "soglia": a.soglia,
             "fotogrammi": righe}
    Path(a.json).write_text(json.dumps(esito, indent=1))
    print(json.dumps({"cambio_mappa": cambio,
                      "diff": [(r["i"], r.get("percentuale")) for r in righe],
                      "stato_finale": righe[-1].get("stato")}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
