#!/usr/bin/env python3
"""SGP-1.2-OPZIONI-01 — codifica del testo della pagina nel charset HGSS e misura
della sua larghezza in pixel con il font 0 della ROM.

Il testo della pagina NON sta in un banco messaggi (`a/0/2/7`): sta in un **blob**
nel blocco della riserva ARM9, esattamente come la 1.1 fa per la guida EV/IV
(blob ITCM a `0x01FF9B70`, misurato da `source/quality-audit/misura_larghezza.py`)
e come la 1.2a fa per le due tabelle della difficoltà PLUS. Motivo tecnico, non
di gusto: il caricatore `carica_text.py` (derivato da `thumb_object.py` della 1.1)
**rifiuta ogni sezione allocata oltre `.text`**, quindi una `static const u16[]`
non può esistere nel payload; e toccare `a/0/2/7` significherebbe ricostruire il
NARC dei messaggi in due lingue e invalidare le patch xdelta esistenti.

La charmap è quella di pret/pokeheartgold @0985e871 (`charmap.txt`), letta a runtime
dal checkout se disponibile; in mancanza si usa la tabella minima qui sotto, che
copre ASCII stampabile + le accentate italiane. Un carattere non mappato è un
ERRORE: si rifiuta, non si sostituisce in silenzio (regola del contratto guida 1.1).

Uso:
  codifica_testo.py --testi <testi.json> --rom <rom.nds> --uscita <prove/testi.json>
"""
import argparse
import json
import sys
from pathlib import Path

RADICE = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(RADICE / "source" / "quality-audit"))

TERMINATORE = 0xFFFF
A_CAPO = 0xE000

# Tabella minima, verificata su charmap.txt di pret (righe 295, 305, 330, 331, 356,
# 436, 484): '0'=0x121 (0-9 contigui), 'A'=0x12B (A-Z contigui), 'a'=0x145
# (a-z contigui), '.'=0x1AE, ' '=0x1DE.
def _base():
    t = {}
    for i in range(10):
        t[chr(ord("0") + i)] = 0x121 + i
    for i in range(26):
        t[chr(ord("A") + i)] = 0x12B + i
        t[chr(ord("a") + i)] = 0x145 + i
    t[" "] = 0x1DE
    t["."] = 0x1AE
    t["\n"] = A_CAPO
    return t


CHARMAP_PACCHETTO = Path(__file__).resolve().parent.parent / "testi" / "charmap-sgp.tsv"


def carica_charmap(percorso=None):
    """Legge una charmap. Passa `--charmap <pret>/charmap.txt` dal checkout
    pinnato in `source/README.md`: la tabella non e' ridistribuita qui (vedi
    CREDITS.md). Se manca, resta la tabella minima incorporata, che basta ai
    test ma NON riproduce i blob dei testi spediti. Accetta sia il formato di
    pret («XXXX=c») sia quello ridotto («XXXX<TAB>c»)."""
    t = _base()
    if percorso is None and CHARMAP_PACCHETTO.is_file():
        percorso = CHARMAP_PACCHETTO
    if not percorso or not Path(percorso).is_file():
        return t, "tabella-minima"
    if str(percorso).endswith(".tsv"):
        for riga in Path(percorso).read_text(encoding="utf-8").splitlines():
            if riga.startswith("#") or "\t" not in riga:
                continue
            codice, _, glifo = riga.partition("\t")
            t[glifo] = int(codice, 16)
        t["\n"] = A_CAPO
        return t, str(percorso)
    for riga in Path(percorso).read_text(encoding="utf-8").splitlines():
        riga = riga.split("@")[0].rstrip("\n")
        if "=" not in riga:
            continue
        codice, _, glifo = riga.partition("=")
        codice = codice.strip()
        if len(codice) != 4:
            continue
        try:
            v = int(codice, 16)
        except ValueError:
            continue
        if len(glifo) == 1 and glifo != "\\":
            t.setdefault(glifo, v)
    t["\n"] = A_CAPO
    return t, str(percorso)


def codifica(testo, tabella):
    fuori = sorted({c for c in testo if c not in tabella})
    if fuori:
        raise ValueError("caratteri non mappati: " + " ".join(
            "%r(U+%04X)" % (c, ord(c)) for c in fuori))
    return [tabella[c] for c in testo] + [TERMINATORE]


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--testi", type=Path, required=True)
    ap.add_argument("--rom", type=Path, required=True)
    ap.add_argument("--charmap", type=Path, default=None)
    ap.add_argument("--limite", type=int, default=224)
    ap.add_argument("--uscita", type=Path, required=True)
    args = ap.parse_args()

    import misura_larghezza as ml

    tabella, fonte = carica_charmap(args.charmap)
    testi = json.loads(args.testi.read_text(encoding="utf-8"))
    widths = ml.load_width_table_from_rom(str(args.rom))

    fuori_limite = []
    out = {"schema": 1, "charmap": fonte, "limite_px": args.limite,
           "rom": args.rom.name, "voci": {}}
    for lingua, blocco in testi["testi"].items():
        out["voci"][lingua] = {}
        for chiave, testo in blocco.items():
            parole = codifica(testo, tabella)
            m = ml.measure(widths, parole, limit_px=args.limite)
            righe = [{"px": r["width_px"], "ignoti": r["unknown_codes"], "testo": l}
                     for r, l in zip(m["lines"], testo.split("\n"))]
            larghezza = max([r["px"] for r in righe] or [0])
            out["voci"][lingua][chiave] = {
                "parole": len(parole), "byte": 2 * len(parole),
                "righe": righe, "max_px": larghezza,
                "entro_limite": larghezza <= args.limite,
            }
            if larghezza > args.limite:
                fuori_limite.append(f"{lingua}/{chiave} = {larghezza}px")

    out["byte_totali_blob"] = sum(v["byte"] for L in out["voci"].values()
                                  for v in L.values())
    out["fuori_limite"] = fuori_limite
    args.uscita.parent.mkdir(parents=True, exist_ok=True)
    args.uscita.write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n",
                           encoding="utf-8")
    print(json.dumps({"limite_px": args.limite,
                      "byte_totali_blob": out["byte_totali_blob"],
                      "fuori_limite": fuori_limite,
                      "massimi": {L: max(v["max_px"] for v in b.values())
                                  for L, b in out["voci"].items()}}, indent=1))
    return 1 if fuori_limite else 0


if __name__ == "__main__":
    raise SystemExit(main())
