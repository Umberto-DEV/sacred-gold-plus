#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SGP-1.2-ANIM-SOLIDO-01 — i criteri 1, 2 e 6 di `10c` §4, misurati sui PIXEL.

I numeri (ampiezza in px, periodo, ombra) vengono dai byte del Pokepic
(`misura_v4.py`). Questi tre criteri no: sono definiti sui pixel del
rettangolo del lottatore, e vanno misurati su fotogrammi **adiacenti**.

  criterio 1 — fluidità: percentuale di finestre di 4 fotogrammi in cui il
               rettangolo non cambia di un solo pixel. Verde ≤ 25 %.
  criterio 2 — ampiezza percepita: pixel medi diversi fra due fotogrammi
               adiacenti, in percentuale del rettangolo. Verde 6–12 %.
  criterio 6 — artefatti: (a) **bordo tagliato**, inchiostro appoggiato a una
               delle quattro strisce di bordo del rettangolo (se il rettangolo
               è il riquadro dello sprite, vuol dire che lo sprite esce);
               (b) **sfarfallio**, pixel che cambiano e tornano indietro fra
               tre fotogrammi adiacenti (`va == vc != vb`) **oltre** quelli
               attesi dall'alternanza di posa.

Il rettangolo si può dare a mano o farlo dedurre: `--auto` prende la scatola
che contiene tutti i pixel che cambiano nella sequenza, allargata di
`--margine` px, e la riporta — così si vede su che cosa si è misurato.

Uso:
  misura_pixel.py CARTELLA [--rect X0 Y0 X1 Y1 | --auto] [--margine 6]
                  [--schermo alto|basso] [--json F] [--png F]
GPL-3.0-or-later.
"""
import argparse
import json
import sys
from pathlib import Path


def leggi_ppm(path):
    d = Path(path).read_bytes()
    if not d.startswith(b"P6"):
        raise SystemExit("%s non è un PPM binario" % path)
    campi, i = [], 2
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
    w, h, _mx = campi
    return w, h, d[i:i + w * h * 3]


def ritaglia(w, h, px, rect, schermo):
    x0, y0, x1, y1 = rect
    dy = 0 if schermo == "alto" else h // 2
    fuori = []
    for y in range(y0, y1):
        r = (y + dy) * w
        for x in range(x0, x1):
            o = (r + x) * 3
            fuori.append(px[o:o + 3])
    return fuori


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cartella")
    ap.add_argument("--glob", default="f*.ppm")
    ap.add_argument("--rect", nargs=4, type=int)
    ap.add_argument("--auto", action="store_true")
    ap.add_argument("--margine", type=int, default=6)
    ap.add_argument("--schermo", default="alto", choices=("alto", "basso"))
    ap.add_argument("--json")
    a = ap.parse_args()

    file = sorted(Path(a.cartella).glob(a.glob))
    if len(file) < 5:
        raise SystemExit("servono almeno 5 fotogrammi adiacenti: ne ho %d" % len(file))
    letti = [leggi_ppm(f) for f in file]
    w, h = letti[0][0], letti[0][1]
    alt = h // 2

    if a.auto or not a.rect:
        dy = 0 if a.schermo == "alto" else alt
        x0, y0, x1, y1 = w, alt, 0, 0
        base = letti[0][2]
        for _w, _h, px in letti[1:]:
            for y in range(alt):
                r = (y + dy) * w
                for x in range(w):
                    o = (r + x) * 3
                    if px[o:o + 3] != base[o:o + 3]:
                        x0, y0 = min(x0, x), min(y0, y)
                        x1, y1 = max(x1, x + 1), max(y1, y + 1)
        if x1 <= x0:
            raise SystemExit("nessun pixel cambia: non c'è niente da misurare")
        m = a.margine
        rect = (max(0, x0 - m), max(0, y0 - m), min(w, x1 + m), min(alt, y1 + m))
    else:
        rect = tuple(a.rect)

    quadri = [ritaglia(w, h, px, rect, a.schermo) for _w, _h, px in letti]
    n = len(quadri[0])

    # criterio 1 — finestre di 4 fotogrammi senza un solo pixel diverso
    finestre = 0
    ferme = 0
    for i in range(0, len(quadri) - 4):
        finestre += 1
        if all(quadri[i] == quadri[i + k] for k in (1, 2, 3)):
            ferme += 1
    c1 = round(100.0 * ferme / max(1, finestre), 1)

    # criterio 2 — pixel diversi fra fotogrammi adiacenti, in % del rettangolo
    diffs = []
    for i in range(len(quadri) - 1):
        d = sum(1 for u, v in zip(quadri[i], quadri[i + 1]) if u != v)
        diffs.append(d)
    c2 = round(100.0 * (sum(diffs) / len(diffs)) / n, 2)

    # criterio 6a — bordo tagliato: il fondo è il colore più frequente della
    # striscia su tutta la sequenza; se su una striscia compare inchiostro
    # diverso dal fondo, lo sprite tocca il bordo del rettangolo.
    x0, y0, x1, y1 = rect
    larg, altr = x1 - x0, y1 - y0
    strisce = {"alto": [(x, 0) for x in range(larg)],
               "basso": [(x, altr - 1) for x in range(larg)],
               "sinistra": [(0, y) for y in range(altr)],
               "destra": [(larg - 1, y) for y in range(altr)]}
    bordi = {}
    for nome, punti in strisce.items():
        conteggio = {}
        for q in quadri:
            for (x, y) in punti:
                c = q[y * larg + x]
                conteggio[c] = conteggio.get(c, 0) + 1
        fondo = max(conteggio, key=conteggio.get)
        diversi = sum(v for k, v in conteggio.items() if k != fondo)
        bordi[nome] = {"pixel_diversi_dal_fondo": diversi,
                       "totali": sum(conteggio.values())}
    c6a = sum(v["pixel_diversi_dal_fondo"] for v in bordi.values())

    # criterio 6b — sfarfallio: va == vc != vb su terne adiacenti
    sfarfallio = 0
    confronti = 0
    for i in range(len(quadri) - 2):
        qa, qb, qc = quadri[i], quadri[i + 1], quadri[i + 2]
        for j in range(n):
            confronti += 1
            if qa[j] == qc[j] and qa[j] != qb[j]:
                sfarfallio += 1
    c6b = round(100.0 * sfarfallio / max(1, confronti), 3)

    fuori = {
        "cartella": str(a.cartella), "fotogrammi": len(file),
        "rettangolo": list(rect), "schermo": a.schermo, "pixel_nel_rettangolo": n,
        "criterio1_fermi_pct": c1, "criterio1_verde": c1 <= 25.0,
        "criterio2_pixel_diversi_pct": c2, "criterio2_verde": 6.0 <= c2 <= 12.0,
        "criterio2_min": min(diffs), "criterio2_max": max(diffs),
        "criterio6a_bordo_tagliato": c6a, "criterio6a_verde": c6a == 0,
        "criterio6a_strisce": bordi,
        "criterio6b_sfarfallio_pct": c6b,
    }
    print(json.dumps(fuori, indent=2))
    if a.json:
        Path(a.json).write_text(json.dumps(fuori, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
