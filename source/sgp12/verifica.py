#!/usr/bin/env python3
"""sgp12.verifica — UN comando per verificare una ROM 1.2.2: confronta la ROM
data con quella che `costruisci.py` produce dalla stessa base (criterio 4),
esegue i rilettori disponibili in `sgp12.blocchi` sugli stadi che sanno
verificare, e T1-T5 (`verifiche/test_riserva.py`, NON toccato:
resta il rilettore indipendente della mappa della riserva).

Uso:
    python3 -m sgp12.verifica sgp-1.2.2-EN.nds --base base-1.1-EN.nds --lingua EN

Senza `--base` la ricostruzione e i rilettori sono saltati con motivo
esplicito (T1-T5 restano attivi: T1 non richiede una ROM).

Verdetto ed exit code (revisione 18/09/2026, W2C-6): una copertura non
completa NON e' piu' un VERDE silenzioso. Tre esiti, tre exit code:

    VERDE     0   tutto eseguito, niente di rosso
    PARZIALE  2   niente di rosso in quello che e' girato, ma uno o piu'
                  rilettori sono stati saltati (di solito: manca --base)
                  — non e' un verdetto sui blocchi saltati, vedi "copertura"
    ROSSO     1   almeno un rilettore rosso, la ricostruzione non combacia,
                  o T1-T5 e' fallito

Un `Rifiuto` sollevato durante la ricostruzione (base incompatibile, blocco
che rifiuta la propria preimmagine) non fa piu' uscire un traceback: diventa
una voce `rifiuto` dentro `costruzione_identica`, come fa `costruisci.py`
con il proprio `Rifiuto` a livello di riga di comando.

Nota sui rilettori `riserva`/`camera`/`npc`: sono scritti (per costruzione,
`02-COME-LAVORARE.md §2.3`) per confrontare una ROM con la ROM SUBITO PRIMA di
quel blocco, non con una ROM finale che ha gia' tutti gli 8 blocchi applicati
— dopo `camera`, per esempio, la zona 1.1 dentro la riserva cambia LEGITTIMAMENTE,
e il rilettore di `riserva` lo segnalerebbe come ROSSO pur non essendo un
errore. Qui si ricostruiscono gli stadi intermedi (le stesse `applica()`,
deterministiche) e si passano al rilettore giusto: verificano cosi' che la
LIBRERIA sia internamente coerente. La verifica che conta per il criterio 4 —
la ROM data e' quella che il toolchain produce — è `costruzione_identica`.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import traceback
from pathlib import Path

from .rom import Rifiuto, sha
from . import costruisci as costruisci_mod
from .blocchi import (riserva, camera, npc, plus_chunk, testi as testi_mod, anim,
                      opzioni, wifi, titolo, guida, caramelle, borsa, anim2, borsa_lotta, squadra_lotta, capacita_borsa)

SOURCE = Path(__file__).resolve().parents[1]
BUILD_DEFAULT = Path(__file__).resolve().parent / "build"
TEST_RISERVA = SOURCE / "verifiche/test_riserva.py"

# Tre esiti, tre exit code (vedi il docstring del modulo). PARZIALE e' nuovo:
# prima una copertura incompleta (rilettori saltati) restava VERDE/exit 0.
CODICI_USCITA = {"VERDE": 0, "PARZIALE": 2, "ROSSO": 1}


ORDINE_STADI = ("riserva", "camera", "plus_chunk", "testi", "npc", "anim", "opzioni",
                "wifi", "titolo", "credito", "guida", "caramelle", "borsa", "anim2", "borsa_lotta", "squadra_lotta", "capacita_borsa")


def _rilettori_di_libreria(base: bytes, build_dir: Path, lingua: str | None) -> dict:
    """Ricostruisce gli stadi intermedi da `base` e ci esegue sopra i
    rilettori: un'autoverifica della libreria, non della ROM passata a
    `verifica()` (vedi nota di modulo).

    A2 della revisione R1: un'eccezione dentro `applica()` o `rileggi()` NON e'
    piu' un «saltato» — i guasti piu' gravi che i rilettori sanno trovare (il
    rilettore NPC li segnala SOLLEVANDO: overlay di dimensione cambiata, ARM9
    spostato, contesto non unico) diventavano una riga in un JSON e il verdetto
    restava VERDE. Ora sono ROSSO, con la traccia, e la catena si ferma: gli
    stadi successivi non hanno piu' un ingresso di cui fidarsi."""
    out = {}
    manifest = build_dir / "riserva" / "MAPPA-RISERVA-ARM9.json"
    stato = {"rom": base, "interrotto": None}

    def stadio(nome, fn):
        """`fn(rom) -> (rom_dopo, esito_del_rilettore)`."""
        if stato["interrotto"]:
            out[nome] = {"esito": "ROSSO",
                         "motivo": "catena interrotta dallo stadio '%s'" % stato["interrotto"]}
            return
        try:
            dopo, esito = fn(stato["rom"])
        except Exception as e:
            out[nome] = {"esito": "ROSSO",
                         "eccezione": "%s: %s" % (type(e).__name__, e),
                         "traccia": traceback.format_exc().splitlines()[-12:]}
            stato["interrotto"] = nome
            return
        out[nome] = esito
        stato["rom"] = dopo

    stadio("riserva", lambda r: _con(riserva.applica(r, build_dir / "riserva", etichetta=lingua or ""),
                                     lambda d: riserva.rileggi(r, d, build_dir / "riserva")))
    stadio("camera", lambda r: _con(camera.applica(r), lambda d: camera.rileggi(r, d)))

    if not lingua:
        for nome in ORDINE_STADI[2:]:
            out[nome] = {"saltato": "serve --lingua per ricostruire lo stadio precedente"}
        return out

    stadio("plus_chunk", lambda r: _con(plus_chunk.applica(r, build_dir, manifest_path=manifest),
                                        lambda d: plus_chunk.rileggi(r, d, build_dir)))
    stadio("testi", lambda r: _con(testi_mod.applica(r, build_dir / "testi", lingua),
                                   lambda d: testi_mod.rileggi(r, d, build_dir / "testi", lingua)))
    stadio("npc", lambda r: _con(npc.applica(r, build_dir / "npc", manifest_path=manifest),
                                 lambda d: npc.rileggi(r, d, build_dir / "npc")))
    stadio("anim", lambda r: _con(anim.applica(r, build_dir / "anim", manifest_path=manifest, flags=0),
                                  lambda d: anim.rileggi(r, d, build_dir / "anim")))
    stadio("opzioni", lambda r: _con(opzioni.applica(r, build_dir / "opzioni", lingua=lingua,
                                                     manifest_path=manifest),
                                     lambda d: opzioni.rileggi(r, d, build_dir / "opzioni", lingua,
                                                               manifest_path=manifest)))
    stadio("wifi", lambda r: _con(wifi.applica(r, build_dir / "wifi", manifest_path=manifest),
                                  lambda d: wifi.rileggi(r, d, build_dir / "wifi")))
    stadio("titolo", lambda r: _con(titolo.applica(r), lambda d: titolo.rileggi(d)))
    stadio("credito", lambda r: _con(titolo.applica_credito(r),
                                     lambda d: titolo.rileggi_credito(r, d)))
    stadio("guida", lambda r: _con(guida.applica(r), lambda d: guida.rileggi(r, d)))
    stadio("caramelle", lambda r: _con(caramelle.applica(r, build_dir / "caramelle",
                                                         manifest_path=manifest),
                                       lambda d: caramelle.rileggi(r, d, build_dir / "caramelle")))
    stadio("borsa", lambda r: _con(borsa.applica(r, build_dir / "borsa", lingua,
                                                 manifest_path=manifest),
                                   lambda d: borsa.rileggi(r, d, build_dir / "borsa", lingua)))
    stadio("anim2", lambda r: _con(anim2.applica(r, build_dir / "anim2",
                                                 manifest_path=manifest),
                                   lambda d: anim2.rileggi(r, d, build_dir / "anim2")))
    stadio("borsa_lotta", lambda r: _con(borsa_lotta.applica(r, build_dir / "borsa_lotta",
                                                            manifest_path=manifest),
                                        lambda d: borsa_lotta.rileggi(r, d, build_dir / "borsa_lotta")))
    stadio("squadra_lotta", lambda r: _con(squadra_lotta.applica(r, build_dir / "squadra_lotta",
                                                            manifest_path=manifest),
                                        lambda d: squadra_lotta.rileggi(r, d, build_dir / "squadra_lotta")))
    stadio("capacita_borsa", lambda r: _con(capacita_borsa.applica(r, build_dir / "capacita_borsa",
                                                            manifest_path=manifest),
                                        lambda d: capacita_borsa.rileggi(r, d, build_dir / "capacita_borsa")))
    return out


def _con(applicato, rileggi):
    """`applica()` ritorna `(rom, log)`; qui si tiene la ROM e ci si esegue il
    rilettore, che e' l'unica cosa che entra nel rapporto."""
    dopo = applicato[0]
    return dopo, rileggi(dopo)


def _verifica_costruzione(rom: bytes, base: bytes, lingua: str, build_dir: Path) -> dict:
    """Isolata da `verifica()` per essere testabile da sola, senza ROM: prima
    un `Rifiuto` sollevato da `costruisci()` (base incompatibile, blocco che
    rifiuta la propria preimmagine) usciva come traceback fino a `main()`.
    Qui diventa una voce `rifiuto`, come fa `costruisci.py` in riga di
    comando col proprio `Rifiuto` (W2C-6)."""
    try:
        ricostruita, rapporto = costruisci_mod.costruisci(base, lingua, build_dir)
    except Rifiuto as e:
        return {"identico": False, "rifiuto": "%s: %s" % (type(e).__name__, e)}
    return {
        "identico": ricostruita == rom,
        "base_sha256": sha(base), "rom_sha256": sha(rom),
        "ricostruita_sha256": rapporto["uscita_sha256"],
        "passi": rapporto["passi"],
    }


def verifica(rom_path: Path, base_path: Path | None, build_dir: Path, lingua: str | None = None) -> dict:
    rom = Path(rom_path).read_bytes()
    esiti = {"rom": str(rom_path), "rom_sha256": sha(rom), "rilettori": {}}

    if base_path is not None:
        base = Path(base_path).read_bytes()
        if lingua:
            esiti["costruzione_identica"] = _verifica_costruzione(rom, base, lingua, build_dir)
        else:
            esiti["costruzione_identica"] = {"saltato": "serve --lingua per ricostruire da --base"}
        esiti["rilettori"].update(_rilettori_di_libreria(base, build_dir, lingua))
    else:
        esiti["costruzione_identica"] = {"saltato": "manca --base"}
        for nome in ORDINE_STADI:
            esiti["rilettori"][nome] = {"saltato": "manca --base"}

    for nome in ORDINE_STADI:
        esiti["rilettori"].setdefault(nome, {"saltato": "manca --base/--lingua"})

    # T1-T5: eseguiti SEMPRE (T1 non richiede una ROM), con SGP_RISERVA_ROM
    # per T2-T5 sulla ROM data (non su una ricostruita: e' lei che si verifica).
    env = dict(os.environ)
    env["SGP_RISERVA_ROM"] = str(rom_path.resolve())
    # E3 della revisione R3: `TestGuardiaModalitaCompleta` esiste per trasformare
    # l'assenza della ROM in un fallimento invece che in otto skip silenziosi, ma
    # nessuno impostava mai la variabile che la arma — ne' `run_tests.py` ne' la
    # CI. Qui la ROM c'e' per definizione: e' il posto giusto in cui armarla, e da
    # ora T2-T5 non possono saltare senza far fallire questo comando.
    env["SGP_RISERVA_COMPLETA"] = "1"
    r = subprocess.run([sys.executable, "-m", "unittest", str(TEST_RISERVA), "-v"],
                       capture_output=True, text=True, env=env, cwd=str(SOURCE))
    esiti["T1_T5"] = {"returncode": r.returncode, "stderr_ultime_righe": r.stderr.splitlines()[-20:]}

    riletture_rosse = [n for n, v in esiti["rilettori"].items() if isinstance(v, dict) and
                       (v.get("verdetto") == "ROSSO" or v.get("esito_finale") == "ROSSO"
                        or str(v.get("esito", "")).startswith("ROSSO"))]
    riletture_saltate = [n for n, v in esiti["rilettori"].items()
                         if isinstance(v, dict) and "saltato" in v]
    costruzione_ok = esiti["costruzione_identica"].get("identico", True)  # True se saltata: non e' lei a bocciare
    esiti["riletture_rosse"] = riletture_rosse
    esiti["riletture_saltate"] = riletture_saltate
    # Un verdetto VERDE con dei rilettori saltati non e' un verdetto sui
    # blocchi: lo dice qui, invece di lasciarlo dedurre (A2 della revisione R1).
    esiti["copertura"] = "completa" if not riletture_saltate else \
        "PARZIALE: %d rilettori saltati (%s)" % (len(riletture_saltate), ", ".join(riletture_saltate))
    esiti["verdetto"] = _verdetto_finale(r.returncode, riletture_rosse, costruzione_ok, riletture_saltate)
    return esiti


def _verdetto_finale(t1_t5_returncode: int, riletture_rosse: list, costruzione_ok: bool,
                     riletture_saltate: list) -> str:
    """W2C-6: prima una copertura PARZIALE (rilettori saltati, tipicamente per
    mancanza di --base) produceva comunque VERDE/exit 0 se nessuno dei
    rilettori ESEGUITI era rosso — il rilievo A5 di `A8b/REPORT.md`. Isolata
    dal resto di `verifica()` per essere testabile a tavolino, con liste e
    booleani finti, senza ROM ne' sottoprocessi. Precedenza: un rosso vince
    sempre su un saltato, un saltato vince su tutto verde."""
    if t1_t5_returncode != 0 or riletture_rosse or not costruzione_ok:
        return "ROSSO"
    if riletture_saltate:
        return "PARZIALE"
    return "VERDE"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("rom")
    ap.add_argument("--base", default=None)
    ap.add_argument("--lingua", choices=("EN", "IT"), default=None)
    ap.add_argument("--build", default=str(BUILD_DEFAULT))
    ap.add_argument("--json", default=None)
    a = ap.parse_args(argv)

    lingua = a.lingua
    if lingua is None and a.base:
        lingua = "IT" if "-IT" in Path(a.base).name.upper() else "EN"

    try:
        esiti = verifica(Path(a.rom), Path(a.base) if a.base else None, Path(a.build), lingua)
    except Rifiuto as e:
        # Difesa aggiuntiva, come costruisci.py: `_verifica_costruzione` gia'
        # cattura il caso previsto (Rifiuto durante la ricostruzione), ma se
        # un percorso futuro ne lasciasse sfuggire uno, qui esce una diagnosi
        # JSON invece di un traceback.
        diagnosi = {"rom": a.rom, "verdetto": "ROSSO",
                   "rifiuto": "%s: %s" % (type(e).__name__, e)}
        testo = json.dumps(diagnosi, indent=2, ensure_ascii=False) + "\n"
        if a.json:
            Path(a.json).write_text(testo)
        print(testo)
        print("RIFIUTO: %s" % e, file=sys.stderr)
        return CODICI_USCITA["ROSSO"]

    testo = json.dumps(esiti, indent=2, ensure_ascii=False) + "\n"
    if a.json:
        Path(a.json).write_text(testo)
    print(testo)
    return CODICI_USCITA[esiti["verdetto"]]


if __name__ == "__main__":
    sys.exit(main())
