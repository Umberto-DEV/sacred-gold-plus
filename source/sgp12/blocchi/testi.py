#!/usr/bin/env python3
"""Blocco TESTI — le correzioni testuali della 1.2 dentro l'NARC dei messaggi
(nessun blocco ARM9, nessun overlay: solo un file dentro il filesystem della
ROM). Adattatore verso `features/texts/applica_testi.py::apply_to_rom_bytes`,
che e' gia' una funzione pura bytes-in/bytes-out.

**Due ingressi esterni**, nessuno dei quali sta in questo repository:

1. `charmap.txt`, dal checkout di `pret/pokeheartgold` al commit
   `0985e8718df4f25e64d6507d89c0c97c0d288981` (`source/README.md` spiega come
   prenderlo). Si indica con `SGP_PRET_SOURCE` o si mette in
   `sgp12/build/testi/pret-source/`.
2. `CORREZIONI.tsv`, la tabella che `applica_testi.py` consuma. Contiene il
   testo dei messaggi, che appartiene al gioco: qui e' pubblicato solo
   `build/testi/REGOLE.json` (il messaggio a cui ogni correzione appartiene,
   lo sha256 del testo che deve trovarci e le modifiche minime). Se il TSV non
   c'e', questo modulo lo **ricostruisce dalla ROM in ingresso** con
   `features/texts/genera_correzioni.py`, in un file temporaneo.
"""
from __future__ import annotations

import importlib.util
import json
import os
import sys
import tempfile
from pathlib import Path

from ..rom import esigi

_SOURCE = Path(__file__).resolve().parents[2]
_TEXTS = _SOURCE / "features/texts"

# Le righe che l'applicatore rifiuta e che la ROM spedita NON porta. Sono
# dichiarate qui, una per una, con il motivo misurato: e' l'unico modo per
# distinguere «questa correzione non ci sta, e lo sappiamo» da «ne abbiamo
# perse 234 e nessuno se n'e' accorto» (A3 della revisione R1). Qualunque
# altra riga rifiutata FERMA la costruzione.
#   chiave: (lingua, banco, id_messaggio) -> motivo
RIFIUTI_DICHIARATI = {
    ("EN", 219, 35): "msg_0219 (oaks_speech.c, introduzione), priorita' B: il testo proposto "
                     "misura 218 px contro un limite effettivo di 216 (contesto 216, gia' "
                     "spedito 213). Rifiutata dal cancello di larghezza dell'applicatore, non "
                     "da una scelta: riscriverla piu' corta e' lavoro della 1.3. La ROM 1.2.2 "
                     "spedisce quindi 212 correzioni su 213 in perimetro per l'inglese.",
}


def _carica(nome: str, percorso: Path):
    if str(_TEXTS) not in sys.path:
        sys.path.insert(0, str(_TEXTS))
    spec = importlib.util.spec_from_file_location(nome, percorso)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _pret_source(build: Path) -> Path:
    """Il `charmap.txt` del pret non e' redistribuito: si indica con
    `SGP_PRET_SOURCE` o si mette in `sgp12/build/testi/pret-source/`.

    E5 della revisione R3: la sua assenza dava dodici `FileNotFoundError` a
    meta' catena. Ora e' un rifiuto con scritto cosa manca e come si rimedia."""
    dalla_variabile = os.environ.get("SGP_PRET_SOURCE")
    p = Path(dalla_variabile) if dalla_variabile else build / "pret-source"
    esigi((p / "charmap.txt").is_file(),
          "TESTI: charmap.txt non trovato in %s. Serve un checkout di "
          "pret/pokeheartgold @0985e8718df4f25e64d6507d89c0c97c0d288981: "
          "indicarlo con SGP_PRET_SOURCE=<checkout> (vedi source/README.md). "
          "E' un ingresso esterno, non e' redistribuito qui." % p)
    return p


def pret_disponibile(build) -> bool:
    """Per i test di classe B: dice se il charmap c'e', senza sollevare."""
    dalla_variabile = os.environ.get("SGP_PRET_SOURCE")
    p = Path(dalla_variabile) if dalla_variabile else Path(build) / "pret-source"
    return (p / "charmap.txt").is_file()


def _tabella_correzioni(rom: bytes, build: Path, lingua: str, pret_source: Path):
    """Ritorna `(percorso_tsv, temporaneo_o_None, rapporto_ricostruzione_o_None)`.

    Se `CORREZIONI.tsv` non c'e' (il caso pubblico: il TSV contiene il testo del
    gioco e non si pubblica), lo ricostruisce dalla ROM in ingresso a partire da
    `REGOLE.json`."""
    correzioni = build / "CORREZIONI.tsv"
    if correzioni.exists():
        return correzioni, None, None
    gen = _carica("genera_correzioni", _TEXTS / "genera_correzioni.py")
    regole = build / "REGOLE.json"
    righe, ricostruito = gen.costruisci(rom, lingua, regole, pret_source)
    campi = json.loads(regole.read_text(encoding="utf-8"))["campi_tsv"]
    temporaneo = tempfile.NamedTemporaryFile("w", suffix=".tsv", delete=False)
    temporaneo.close()
    correzioni = Path(temporaneo.name)
    gen.scrivi_tsv(righe, campi, correzioni)
    return correzioni, temporaneo, ricostruito


def applica(rom: bytes, build, lingua: str) -> tuple[bytes, dict]:
    build = Path(build)
    m = _carica("orig_applica_testi", _TEXTS / "applica_testi.py")
    pret_source = _pret_source(build)

    correzioni, temporaneo, ricostruito = _tabella_correzioni(rom, build, lingua, pret_source)
    try:
        nuovo, summary = m.apply_to_rom_bytes(rom, lingua, correzioni, pret_source)
    finally:
        if temporaneo is not None:
            Path(temporaneo.name).unlink(missing_ok=True)

    summary["strumento"] = "sgp12/blocchi/testi.py:applica (adattatore)"
    if ricostruito is not None:
        summary["correzioni_ricostruite"] = ricostruito

    # A3 della revisione R1. Questo blocco poteva non fare NULLA in silenzio:
    # `apply_to_rom_bytes` ritorna `(None, summary)` quando nessun banco e'
    # stato toccato, `genera_correzioni.costruisci` scarta senza rumore ogni
    # regola la cui impronta non combacia, e `process_bank` registra le righe
    # RIFIUTATA_* e tira dritto. Nessuno leggeva quei conteggi, e una ROM priva
    # di tutte le correzioni testuali usciva VERDE dal cancello (misurato:
    # invalidando le 235 impronte di REGOLE.json la ROM cambiava sha256 e
    # `verifica.py` la dichiarava VERDE lo stesso). Ora sono tre rifiuti.
    saltate = (ricostruito or {}).get("saltate") or []
    esigi(not saltate,
          "TESTI: %d regole non ricostruite dalla ROM in ingresso (la base non e' quella "
          "attesa, oppure REGOLE.json non e' allineato): %s"
          % (len(saltate), saltate[:5]))
    rifiutate = [r for r in summary.get("righe", []) if str(r.get("esito", "")).startswith("RIFIUTATA")]
    non_dichiarate = [r for r in rifiutate
                      if (lingua, r.get("banco"), r.get("messaggio")) not in RIFIUTI_DICHIARATI]
    esigi(not non_dichiarate,
          "TESTI: %d righe rifiutate dall'applicatore e NON dichiarate: %s. Una riga "
          "rifiutata e' una correzione che non entra nella ROM: o si corregge la riga, o la "
          "si dichiara in RIFIUTI_DICHIARATI con il motivo misurato."
          % (len(non_dichiarate),
             [(r.get("banco"), r.get("messaggio"), r.get("esito"), r.get("dettaglio")) for r in non_dichiarate[:5]]))
    summary["rifiuti_dichiarati"] = [
        {"banco": r["banco"], "messaggio": r["messaggio"], "esito": r["esito"],
         "motivo": RIFIUTI_DICHIARATI[(lingua, r["banco"], r["messaggio"])]} for r in rifiutate]
    esigi(nuovo is not None,
          "TESTI: nessuna correzione applicata (NARC invariato). Conteggi: %s"
          % summary.get("conteggi_esito", {}))

    summary["esito"] = "applicato"
    return nuovo, summary


# ---------------------------------------------------------------- rilettore
def rileggi(ingresso: bytes, derivata: bytes, build, lingua: str) -> dict:
    """Rilettore INDIPENDENTE dei testi: `features/texts/rileggi_testi.py`, che
    non importa nulla da `applica_testi.py` (condivide solo il codec dei
    messaggi) e riscrive da zero la resa testuale, la tabella dei limiti di
    larghezza e la lettura della variante corta.

    Era gia' nel repository e non era collegato a nessun cancello (A3 della
    revisione R1: `verifica.py` dichiarava «per i testi non c'e' rilettore» e
    si affidava a `costruzione_identica`, che pero' ricostruisce con gli
    STESSI ingressi, quindi combacia sempre).

    Una differenza rispetto al comportamento dello strumento da riga di
    comando: qui `NON_ANCORA_APPLICATA` e' un PROBLEMA. Lo strumento la
    classifica come non-problema perche' nasce per fotografare un lavoro in
    corso; dopo `applica()` una riga non applicata vuol dire una correzione
    persa."""
    build = Path(build)
    rl = _carica("orig_rileggi_testi", _TEXTS / "rileggi_testi.py")
    pret_source = _pret_source(build)
    correzioni, temporaneo, _ = _tabella_correzioni(ingresso, build, lingua, pret_source)
    try:
        chars, commands = rl.build_charmap(pret_source)
        righe = rl.load_rows(correzioni, lingua)
        rapporto, righe_rapporto, problemi = rl.compare_roms(
            ingresso, derivata, lingua, righe, chars, commands)
        larghezza, problemi_larghezza = rl.check_widths(ingresso, derivata, righe)
    finally:
        if temporaneo is not None:
            Path(temporaneo.name).unlink(missing_ok=True)

    problemi = list(problemi) + list(problemi_larghezza)
    conteggi = {}
    for r in righe_rapporto:
        conteggi[r["esito"]] = conteggi.get(r["esito"], 0) + 1
    # `NON_ANCORA_APPLICATA` e' un problema, TRANNE per le righe che
    # `RIFIUTI_DICHIARATI` dichiara non applicabili con il motivo misurato: sono
    # le stesse che `applica()` lascia passare, e la dichiarazione sta in un
    # posto solo. Una riga non applicata e non dichiarata e' una correzione
    # persa, e rende ROSSO il rilettore.
    non_applicate, dichiarate = [], []
    for r in righe_rapporto:
        if r["esito"] != "NON_ANCORA_APPLICATA":
            continue
        chiave = (lingua, r["banco"], r["messaggio"])
        (dichiarate if chiave in RIFIUTI_DICHIARATI else non_applicate).append(
            "%d#%d" % (r["banco"], r["messaggio"]))
    if non_applicate:
        problemi.append("RIGHE_NON_APPLICATE_NON_DICHIARATE_%d" % len(non_applicate))
    verde = not problemi
    return {"esito_finale": "verde" if verde else "ROSSO",
            "righe_in_perimetro": len(righe),
            "esiti": conteggi,
            "non_applicate_non_dichiarate": non_applicate[:20],
            "non_applicate_dichiarate": dichiarate,
            "confronto_rom": rapporto,
            "font_self_check_ok": larghezza.get("font_self_check_ok"),
            "problemi": problemi}
