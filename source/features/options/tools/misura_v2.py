#!/usr/bin/env python3
"""SGP-1.2-OPZIONI-03 — misura in pixel dei testi v2, con un limite PER CLASSE.

La v1 aveva un solo limite (224 px, la larghezza della finestra grande). La v2 ha
tre limiti diversi, perche' il layout e' diverso:

  etichetta   <= G_NOME_MAX   px   (voce della pagina: x=20, valore a destra)
  valore      <= G_VAL_MAX    px
  riga piena  <= G_RIGA_MAX   px   (titolo, aiuto, suggerimento: x=20 nella riga)
  continua    <= C_RIGA_MAX   px   (schermata al Continua, finestra 30x22)

I numeri arrivano da sorgenti/sgp_ui.h e sono passati da riga di comando, cosi'
non possono divergere in silenzio dal codice.

Uso: misura_v2.py --testi testi/testi.json --rom ROM --uscita prove/testi.json
                  [--nome 104 --val 44 --riga 148 --continua 224]
"""
import argparse
import json
import sys
from pathlib import Path

RADICE = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(RADICE / "source" / "quality-audit"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from codifica_testo import carica_charmap, codifica       # noqa: E402

# classe di ogni chiave: da che limite e' governata
def classe(chiave):
    if chiave.endswith("_nome"):
        return "nome"
    if chiave == "p_suggerimento":
        return "suggerimento"
    if chiave.startswith(("x_", "w_", "n_")):
        return "valore"
    # v3: le due meta' della riga dei comandi hanno un limite loro — meta' della
    # riga utile — perche' sono disegnate una a sinistra e una a destra nelle
    # stesse due colonne delle voci, e sono i due bersagli del tocco.
    if chiave in ("p_aiuto_a", "p_aiuto_b"):
        return "comando"
    if chiave.startswith("c_"):
        return "continua"
    return "riga"


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--testi", type=Path, required=True)
    ap.add_argument("--rom", type=Path, required=True)
    ap.add_argument("--charmap", type=Path, default=None)
    ap.add_argument("--nome", type=int, default=114)
    ap.add_argument("--val", type=int, default=44)
    ap.add_argument("--riga", type=int, default=166)
    ap.add_argument("--suggerimento", type=int, default=108)
    ap.add_argument("--comando", type=int, default=80)
    ap.add_argument("--continua", type=int, default=224)
    ap.add_argument("--uscita", type=Path, required=True)
    args = ap.parse_args()

    import misura_larghezza as ml

    limiti = {"nome": args.nome, "valore": args.val,
              "riga": args.riga, "continua": args.continua,
              "suggerimento": args.suggerimento, "comando": args.comando}
    tabella, fonte = carica_charmap(args.charmap)
    testi = json.loads(args.testi.read_text(encoding="utf-8"))
    widths = ml.load_width_table_from_rom(str(args.rom))

    fuori = []
    out = {"schema": 3, "charmap": fonte, "limiti_px": limiti,
           "rom": args.rom.name, "voci": {}}
    for lingua, blocco in testi["testi"].items():
        out["voci"][lingua] = {}
        for chiave, testo in blocco.items():
            cl = classe(chiave)
            lim = limiti[cl]
            parole = codifica(testo, tabella)
            m = ml.measure(widths, parole, limit_px=lim)
            px = max([r["width_px"] for r in m["lines"]] or [0])
            ignoti = sum(len(r["unknown_codes"]) for r in m["lines"])
            out["voci"][lingua][chiave] = {
                "testo": testo, "classe": cl, "limite": lim, "px": px,
                "byte": 2 * len(parole), "ignoti": ignoti,
                "entro_limite": px <= lim and ignoti == 0,
            }
            if px > lim or ignoti:
                fuori.append(f"{lingua}/{chiave} = {px}px > {lim}"
                             + (f" ignoti={ignoti}" if ignoti else ""))
    out["byte_totali_blob"] = {L: sum(v["byte"] for v in b.values())
                               for L, b in out["voci"].items()}
    out["fuori_limite"] = fuori
    args.uscita.parent.mkdir(parents=True, exist_ok=True)
    args.uscita.write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n",
                           encoding="utf-8")
    for L, b in out["voci"].items():
        print(f"--- {L}")
        for k, v in b.items():
            segno = " " if v["entro_limite"] else "!"
            print(f" {segno} {k:16s} {v['px']:4d}/{v['limite']:3d}  {v['testo']}")
    print(json.dumps({"byte": out["byte_totali_blob"], "fuori_limite": fuori},
                     indent=1, ensure_ascii=False))
    return 1 if fuori else 0


if __name__ == "__main__":
    raise SystemExit(main())
