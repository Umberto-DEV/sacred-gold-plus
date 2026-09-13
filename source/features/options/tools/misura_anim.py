#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SGP-1.2-RIFINITURA-01 — misura del moto in lotta da `frames.csv` e dai PPM.

Due sorgenti, e non si mescolano:

* i **numeri** (ampiezza, periodo, battito, ombra, attese) vengono dai `watch`
  del banco, cioe' dai byte veri del Pokepic letti a ogni fotogramma. Stimarli
  contando pixel sarebbe piu' debole e piu' facile da sbagliare.
* gli **artefatti** vengono dai pixel, perche' e' li' che vivono: si confrontano
  le quattro strisce di bordo del riquadro dello sprite fra gli istanti, e si
  cerca il bordo TAGLIATO (inchiostro appoggiato al bordo del riquadro) e lo
  SFARFALLIO (un pixel che cambia avanti e indietro fra fotogrammi adiacenti).

Uso:
  misura_anim.py numeri  CORSA/frames.csv [--json F]
  misura_anim.py bordi   CORSA --rect X0 Y0 X1 Y1 [--schermo alto|basso] [--json F]
"""
import argparse
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fotogrammi import leggi_ppm, ritaglia  # noqa: E402


def _num(v):
    try:
        return int(str(v), 0)
    except (TypeError, ValueError):
        return None


def _s16(v):
    if v is None:
        return None
    return v - 0x10000 if v >= 0x8000 else v


def serie(righe, colonna, segno=False):
    fuori = []
    for r in righe:
        v = _num(r.get(colonna))
        if v is None:
            continue
        fuori.append(_s16(v) if segno else v)
    return fuori


def periodo(vals):
    """Periodo in fotogrammi: distanza media fra due massimi consecutivi della
    serie. Robusto quanto basta su una sinusoide campionata a gradini interi."""
    if not vals:
        return None
    picchi = []
    for i in range(1, len(vals) - 1):
        if vals[i] == max(vals) and vals[i] >= vals[i - 1] and vals[i] > vals[i + 1]:
            picchi.append(i)
    if len(picchi) < 2:
        return None
    passi = [picchi[i + 1] - picchi[i] for i in range(len(picchi) - 1)]
    return round(sum(passi) / len(passi), 2)


def numeri(percorso, json_out=None):
    righe = list(csv.DictReader(open(percorso)))
    out = {"fotogrammi": len(righe), "colonne": list(righe[0].keys()) if righe else []}
    for etichetta in ("a0_yoff", "a1_yoff", "a0_shy", "a1_shy", "a0_shyoff",
                      "a1_shyoff", "a0_affw", "a0_affh", "a0_step", "a1_step",
                      "a0_active", "a1_active", "last_y", "last_s76", "last_cls",
                      "blinks", "rari", "hits", "hits_on", "hits_busy",
                      "chunk_anim"):
        if etichetta not in out["colonne"]:
            continue
        con_segno = etichetta.endswith(("yoff", "_shy", "_s76", "last_y"))
        v = serie(righe, etichetta, con_segno)
        if not v:
            continue
        d = {"min": min(v), "max": max(v), "escursione": max(v) - min(v),
             "primo": v[0], "ultimo": v[-1], "valori_distinti": len(set(v))}
        if etichetta in ("a0_yoff", "a1_yoff", "last_y"):
            d["periodo_fotogrammi"] = periodo(v)
            p = d["periodo_fotogrammi"]
            d["periodo_secondi"] = round(p / 60.0, 3) if p else None
            d["ampiezza_px"] = (max(v) - min(v)) / 2.0
        out[etichetta] = d
    if json_out:
        Path(json_out).write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps(out, indent=1))
    return out


def bordi(cartella, rect, schermo, json_out=None):
    x0, y0, x1, y1 = rect
    file = sorted(Path(cartella).glob("a0*.ppm"))
    if not file:
        file = sorted(Path(cartella).glob("*.ppm"))
    quadri = []
    for f in file:
        w, h, px = leggi_ppm(str(f))
        w, h, px = ritaglia(w, h, px, schermo)
        quadri.append((f.name, w, px))
    out = {"fotogrammi": [q[0] for q in quadri], "rect": rect, "schermo": schermo}

    def pixel(px, w, x, y):
        i = (y * w + x) * 3
        return tuple(px[i:i + 3])

    # 1. bordo tagliato: inchiostro appoggiato a una delle quattro strisce del
    #    riquadro. «Inchiostro» = pixel diverso dal colore piu' comune della
    #    striscia in TUTTI i fotogrammi (cioe' il fondo).
    tagli = {}
    for nome, lato in (("alto", [(x, y0) for x in range(x0, x1)]),
                       ("basso", [(x, y1 - 1) for x in range(x0, x1)]),
                       ("sinistro", [(x0, y) for y in range(y0, y1)]),
                       ("destro", [(x1 - 1, y) for y in range(y0, y1)])):
        conta = {}
        for _n, w, px in quadri:
            for x, y in lato:
                c = pixel(px, w, x, y)
                conta[c] = conta.get(c, 0) + 1
        fondo = max(conta, key=conta.get)
        diversi = []
        for n, w, px in quadri:
            k = sum(1 for x, y in lato if pixel(px, w, x, y) != fondo)
            if k:
                diversi.append({"fotogramma": n, "pixel": k})
        tagli[nome] = {"fondo": "#%02X%02X%02X" % fondo, "occorrenze": diversi}
    out["bordo_tagliato"] = tagli

    # 2. sfarfallio: un pixel che torna al valore di due fotogrammi prima dopo
    #    esserne cambiato. Su un moto verticale lento e' il segnale di un bordo
    #    che «sbatte» invece di scorrere.
    sfarf = 0
    for i in range(2, len(quadri)):
        _a, w, pa = quadri[i - 2]
        _b, _w, pb = quadri[i - 1]
        _c, _w2, pc = quadri[i]
        for y in range(y0, y1):
            for x in range(x0, x1):
                va, vb, vc = pixel(pa, w, x, y), pixel(pb, w, x, y), pixel(pc, w, x, y)
                if va == vc and va != vb:
                    sfarf += 1
    out["pixel_con_andata_e_ritorno"] = sfarf
    out["pixel_totali_confrontati"] = max(0, (len(quadri) - 2)) * (x1 - x0) * (y1 - y0)
    if json_out:
        Path(json_out).write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps({k: v for k, v in out.items() if k != "fotogrammi"}, indent=1))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("comando", choices=("numeri", "bordi"))
    ap.add_argument("percorso")
    ap.add_argument("--rect", nargs=4, type=int)
    ap.add_argument("--schermo", default="alto")
    ap.add_argument("--json")
    a = ap.parse_args()
    if a.comando == "numeri":
        numeri(a.percorso, a.json)
    else:
        if not a.rect:
            raise SystemExit("--rect X0 Y0 X1 Y1 obbligatorio")
        bordi(a.percorso, a.rect, a.schermo, a.json)


if __name__ == "__main__":
    main()
