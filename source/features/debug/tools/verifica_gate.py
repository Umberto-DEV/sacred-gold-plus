#!/usr/bin/env python3
"""Rilettore indipendente del gate mappe.

Non si fida di `campagna_mappe.py`: ricontrolla, corsa per corsa, che
  P1 l'iniezione sia davvero avvenuta (il passo «chiamata rientrata» c'e' nel json della corsa);
  P2 il fotogramma dopo il warp sia DIVERSO da quello prima (se la mappa non fosse cambiata i
     due sarebbero quasi identici: e' il controllo che smaschera una corsa in cui il warp non e'
     partito e che farebbe passare per «camera diversa» un semplice «mappa diversa»);
  P3 `rileva_crash.py` dica VIVO;
  P4 il fotogramma sia leggibile (colori distinti sullo schermo alto sopra una soglia);
e solo dopo ricalcola il verdetto base/candidata.

  python3 verifica_gate.py --corse DIR --etichetta-cand C1-02 --json out.json
"""
import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

RILEVA = Path(__file__).resolve().parents[3] / "verifiche" / "rileva_crash.py"
BERSAGLI = [(116, "diversi"), (247, "diversi"), (248, "diversi"), (249, "diversi"),
            (119, "diversi"), (250, "diversi"), (251, "diversi"), (252, "diversi"),
            (61, "uguali"), (226, "uguali")]
SOGLIA_COLORI = 64          # sotto questo un fotogramma e' una tinta piatta, non una scena
SOGLIA_CAMBIO = 5.0         # % minima di pixel diversi fra prima e dopo il warp


def alto(p):
    d = Path(p).read_bytes()
    i = d.index(b"255\n") + 4
    return d[i:i + 256 * 192 * 3]


def diff(a, b):
    x, y = alto(a), alto(b)
    n = sum(1 for j in range(0, len(x), 3) if x[j:j + 3] != y[j:j + 3])
    return round(100.0 * n / (256 * 192), 2)


def colori(p):
    x = alto(p)
    return len(set(x[j:j + 3] for j in range(0, len(x), 3)))


def controlla(d: Path):
    e = {"dir": str(d)}
    j = d / "warp.json"
    passi = []
    if j.exists():
        passi = [p["passo"] for p in json.loads(j.read_text()).get("passi", [])]
    e["P1_iniezione"] = "chiamata rientrata" in passi
    prima, dopo = d / "00-prima.ppm", d / "01-dopo-warp.ppm"
    if prima.exists() and dopo.exists():
        e["P2_cambio_percento"] = diff(prima, dopo)
        e["P2_cambiato"] = e["P2_cambio_percento"] >= SOGLIA_CAMBIO
        e["P4_colori"] = colori(dopo)
        e["P4_leggibile"] = e["P4_colori"] >= SOGLIA_COLORI
    else:
        e["P2_cambiato"] = e["P4_leggibile"] = False
    f = d / "frames.csv"
    if f.exists():
        r = subprocess.run([sys.executable, str(RILEVA), str(f)], capture_output=True, text=True)
        e["P3_crash"] = (r.stdout.split() or ["?"])[0]
    e["P3_vivo"] = e.get("P3_crash") == "VIVO"
    e["sha_dopo"] = hashlib.sha256(dopo.read_bytes()).hexdigest() if dopo.exists() else None
    e["tutte_verdi"] = all(e.get(k) for k in ("P1_iniezione", "P2_cambiato", "P3_vivo",
                                              "P4_leggibile"))
    return e


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corse", required=True)
    ap.add_argument("--etichetta-cand", default="C1-02")
    ap.add_argument("--json", required=True)
    a = ap.parse_args()
    D = Path(a.corse)
    esito, verdi = [], 0
    for mappa, atteso in BERSAGLI:
        r = {"mappa": mappa, "atteso": atteso}
        ok = True
        for et in ("base", a.etichetta_cand):
            c = controlla(D / f"{et}-{mappa}")
            r[et] = c
            if atteso == "diversi" and not c["tutte_verdi"]:
                ok = False
            if atteso == "uguali" and not (c["P1_iniezione"] and c["P3_vivo"] and c["P4_leggibile"]):
                ok = False
        sa, sb = r["base"]["sha_dopo"], r[a.etichetta_cand]["sha_dopo"]
        uguali = (sa is not None and sa == sb)
        r["fotogrammi_uguali"] = uguali
        if sa and sb and not uguali:
            r["percento_diverso"] = diff(D / f"base-{mappa}" / "01-dopo-warp.ppm",
                                         D / f"{a.etichetta_cand}-{mappa}" / "01-dopo-warp.ppm")
        r["verdetto"] = "VERDE" if (ok and ((atteso == "uguali") == uguali)) else "ROSSO"
        verdi += r["verdetto"] == "VERDE"
        esito.append(r)
        print(f"mappa {mappa:3d} atteso={atteso:8s} {r['verdetto']:5s} "
              f"P1 {r['base']['P1_iniezione']}/{r[a.etichetta_cand]['P1_iniezione']} "
              f"P2 {r['base'].get('P2_cambio_percento')}/{r[a.etichetta_cand].get('P2_cambio_percento')} "
              f"P3 {r['base'].get('P3_crash')}/{r[a.etichetta_cand].get('P3_crash')} "
              f"P4 {r['base'].get('P4_colori')}/{r[a.etichetta_cand].get('P4_colori')} "
              f"diff {r.get('percento_diverso', 0.0)}%")
    Path(a.json).write_text(json.dumps({"verdi": verdi, "totale": len(esito), "mappe": esito},
                                       indent=2))
    print(f"\n{verdi}/{len(esito)} verdi")
    return 0 if verdi == len(esito) else 1


if __name__ == "__main__":
    sys.exit(main())
