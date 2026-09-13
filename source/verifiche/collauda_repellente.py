#!/usr/bin/env python3
"""Cancello di collaudo: il ri-armo del repellente funziona in questa candidata?

Nasce dall'11/09/2026, quando il difetto e' rimasto invisibile per ore perche'
`rc` restava 0 e i fotogrammi sembravano fermi. Questo script decide da solo, e
NOMINA il cancello caduto.

Quattro cancelli, in ordine, ciascuno capace di fallire:
  C1  il gioco e' VIVO alla fine            (via verifiche/rileva_crash.py)
  C2  repelSteps SCENDE fino a zero          (se non scende, il percorso non cammina
                                              e nulla di cio' che segue prova niente)
  C3  qualcosa COMPARE a schermo allo scadere (il fotogramma dopo lo zero differisce
                                              da quello prima: se e' identico, il
                                              messaggio non c'e')
  C4  il RI-ARMO scatta: repelSteps torna >0 dopo essere arrivato a zero

C2 e' il presidio contro l'esito che non puo' fallire: senza di lui, "nessun crash"
su una corsa in cui il repellente non e' mai scaduto sarebbe un falso verde.

Uso:
  python3 collauda_repellente.py --corsa <dir>
dove <dir> contiene frames.csv con una colonna repelSteps (serve un `watch`) e i
fotogrammi .ppm. Esce 0 solo se tutti e quattro i cancelli passano.
"""
import argparse
import csv
import hashlib
import os
import subprocess
import sys

QUI = os.path.dirname(os.path.abspath(__file__))


def num(s):
    s = s.strip()
    return int(s, 16) if s.lower().startswith("0x") else int(s)


def sha(p):
    with open(p, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()[:12]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corsa", required=True)
    a = ap.parse_args()
    d = a.corsa
    csvp = os.path.join(d, "frames.csv")
    if not os.path.exists(csvp):
        print(f"CADUTO  C0  nessun frames.csv in {d}: la corsa non ha prodotto dati")
        return 1

    # C1 -- il gioco e' vivo
    r = subprocess.run([sys.executable, os.path.join(QUI, "rileva_crash.py"), csvp],
                       capture_output=True, text=True)
    esito = r.stdout.split()[0] if r.stdout.split() else "?"
    print(r.stdout.rstrip())
    if esito != "VIVO":
        print(f"CADUTO  C1  il gioco non e' vivo alla fine della corsa ({esito})")
        return 1
    print("passato C1  il gioco e' vivo")

    righe = list(csv.DictReader(open(csvp)))
    if "repelSteps" not in righe[0]:
        print("CADUTO  C2  manca la colonna repelSteps: aggiungere un `watch`. "
              "Senza, 'nessun crash' non proverebbe nulla sul repellente")
        return 1

    # C2 -- il contatore scende fino a zero
    vals = [(num(r["frame"]), num(r["repelSteps"])) for r in righe]
    picco = max(v for _, v in vals)
    zero = None
    for i in range(1, len(vals)):
        if vals[i][1] == 0 and vals[i - 1][1] > 0:
            zero = vals[i][0]
            break
    if picco == 0:
        print("CADUTO  C2  repelSteps non e' mai stato armato (sempre 0)")
        return 1
    if zero is None:
        print(f"CADUTO  C2  repelSteps ha raggiunto {picco} ma non e' mai sceso a zero: "
              f"il percorso non fa camminare abbastanza. Nulla di cio' che segue e' provato")
        return 1
    print(f"passato C2  repelSteps {picco} -> 0 al fotogramma {zero}")

    # C3 -- qualcosa compare a schermo
    ppm = sorted(f for f in os.listdir(d) if f.endswith(".ppm") and f != "latest.ppm")
    distinti = {sha(os.path.join(d, f)) for f in ppm}
    if len(ppm) >= 2 and len(distinti) == 1:
        print(f"CADUTO  C3  tutti i {len(ppm)} fotogrammi sono byte-identici: "
              f"a schermo non e' comparso nulla")
        return 1
    print(f"passato C3  {len(ppm)} fotogrammi, {len(distinti)} distinti")

    # C4 -- il ri-armo
    dopo = [v for f, v in vals if f > zero]
    if not dopo or max(dopo) == 0:
        print(f"CADUTO  C4  dopo lo scadere repelSteps resta 0: IL RI-ARMO NON SCATTA")
        return 1
    print(f"passato C4  ri-armo osservato: repelSteps torna a {max(dopo)}")
    print("\nTUTTI I CANCELLI PASSATI")
    return 0


if __name__ == "__main__":
    sys.exit(main())
