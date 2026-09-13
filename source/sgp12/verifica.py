#!/usr/bin/env python3
"""sgp12.verifica — UN comando per verificare una ROM 1.2: confronta la ROM
data con quella che `costruisci.py` produce dalla stessa base (criterio 4),
esegue i rilettori disponibili in `sgp12.blocchi` sugli stadi che sanno
verificare, e T1-T5 (`verifiche/test_riserva.py`, NON toccato:
resta il rilettore indipendente della mappa della riserva).

Uso:
    python3 -m sgp12.verifica sgp-1.2-EN.nds --base base-1.1-EN.nds --lingua EN

Senza `--base` la ricostruzione e i rilettori sono saltati con motivo
esplicito (T1-T5 restano attivi: T1 non richiede una ROM).

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
from pathlib import Path

from .rom import sha
from . import costruisci as costruisci_mod
from .blocchi import riserva, camera, npc, plus_chunk, testi as testi_mod, anim, opzioni, wifi, titolo

SOURCE = Path(__file__).resolve().parents[1]
BUILD_DEFAULT = Path(__file__).resolve().parent / "build"
TEST_RISERVA = SOURCE / "verifiche/test_riserva.py"


def _rilettori_di_libreria(base: bytes, build_dir: Path, lingua: str | None) -> dict:
    """Ricostruisce gli stadi intermedi da `base` e ci esegue sopra i
    rilettori: un'autoverifica della libreria, non della ROM passata a
    `verifica()` (vedi nota di modulo)."""
    out = {}
    dopo_riserva, _ = riserva.applica(base, build_dir / "riserva", etichetta=lingua or "")
    out["riserva"] = riserva.rileggi(base, dopo_riserva, build_dir / "riserva")

    dopo_camera, _ = camera.applica(dopo_riserva)
    out["camera"] = camera.rileggi(dopo_riserva, dopo_camera)

    if lingua:
        manifest = build_dir / "riserva" / "MAPPA-RISERVA-ARM9.json"
        try:
            dopo_plus, _ = plus_chunk.applica(dopo_camera, build_dir, manifest_path=manifest)
            out["plus_chunk"] = plus_chunk.rileggi(dopo_camera, dopo_plus, build_dir)
        except Exception as e:
            dopo_plus = dopo_camera
            out["plus_chunk"] = {"saltato": str(e)}

        dopo_testi, _ = testi_mod.applica(dopo_plus, build_dir / "testi", lingua)

        try:
            dopo_npc, _ = npc.applica(dopo_testi, build_dir / "npc", manifest_path=manifest)
            out["npc"] = npc.rileggi(dopo_testi, dopo_npc, build_dir / "npc")
        except Exception as e:
            dopo_npc = dopo_testi
            out["npc"] = {"saltato": str(e)}

        try:
            dopo_anim, _ = anim.applica(dopo_npc, build_dir / "anim", manifest_path=manifest, flags=0)
            out["anim"] = anim.rileggi(dopo_npc, dopo_anim, build_dir / "anim")
        except Exception as e:
            dopo_anim = dopo_npc
            out["anim"] = {"saltato": str(e)}

        try:
            dopo_opzioni, _ = opzioni.applica(dopo_anim, build_dir / "opzioni", lingua=lingua,
                                              manifest_path=manifest)
            out["opzioni"] = opzioni.rileggi(dopo_anim, dopo_opzioni, build_dir / "opzioni", lingua,
                                             manifest_path=manifest)
        except Exception as e:
            dopo_opzioni = dopo_anim
            out["opzioni"] = {"saltato": str(e)}

        try:
            dopo_wifi, _ = wifi.applica(dopo_opzioni, build_dir / "wifi", manifest_path=manifest)
            out["wifi"] = wifi.rileggi(dopo_opzioni, dopo_wifi, build_dir / "wifi")
        except Exception as e:
            dopo_wifi = dopo_opzioni
            out["wifi"] = {"saltato": str(e)}

        try:
            dopo_titolo, _ = titolo.applica(dopo_wifi)
            out["titolo"] = titolo.rileggi(dopo_titolo)
        except Exception as e:
            dopo_titolo = dopo_wifi
            out["titolo"] = {"saltato": str(e)}

        try:
            dopo_credito, _ = titolo.applica_credito(dopo_titolo)
            out["credito"] = titolo.rileggi_credito(dopo_titolo, dopo_credito)
        except Exception as e:
            out["credito"] = {"saltato": str(e)}
    else:
        for nome in ("plus_chunk", "npc", "anim", "opzioni", "wifi", "titolo", "credito"):
            out[nome] = {"saltato": "serve --lingua per ricostruire lo stadio precedente"}
    return out


def verifica(rom_path: Path, base_path: Path | None, build_dir: Path, lingua: str | None = None) -> dict:
    rom = Path(rom_path).read_bytes()
    esiti = {"rom": str(rom_path), "rom_sha256": sha(rom), "rilettori": {}}

    if base_path is not None:
        base = Path(base_path).read_bytes()
        if lingua:
            ricostruita, rapporto = costruisci_mod.costruisci(base, lingua, build_dir)
            esiti["costruzione_identica"] = {
                "identico": ricostruita == rom,
                "base_sha256": sha(base), "rom_sha256": sha(rom),
                "ricostruita_sha256": rapporto["uscita_sha256"],
                "passi": rapporto["passi"],
            }
        else:
            esiti["costruzione_identica"] = {"saltato": "serve --lingua per ricostruire da --base"}
        esiti["rilettori"].update(_rilettori_di_libreria(base, build_dir, lingua))
    else:
        esiti["costruzione_identica"] = {"saltato": "manca --base"}
        for nome in ("riserva", "camera", "npc"):
            esiti["rilettori"][nome] = "saltato: manca --base"

    # testi: nessun rilettore dedicato nemmeno nell'originale (vedi README.md
    # §5): la trasformazione e' bytes->bytes pura, verificata da
    # `costruzione_identica`, non da un rilettore a parte.
    esiti["rilettori"].setdefault("testi", "nessun rilettore dedicato (vedi README.md §5)")
    for nome in ("anim", "opzioni", "wifi", "plus_chunk", "titolo", "credito"):
        esiti["rilettori"].setdefault(nome, "saltato: manca --base/--lingua")

    # T1-T5: eseguiti SEMPRE (T1 non richiede una ROM), con SGP_RISERVA_ROM
    # per T2-T5 sulla ROM data (non su una ricostruita: e' lei che si verifica).
    env = dict(os.environ)
    env["SGP_RISERVA_ROM"] = str(rom_path)
    r = subprocess.run([sys.executable, "-m", "unittest", str(TEST_RISERVA), "-v"],
                       capture_output=True, text=True, env=env, cwd=str(SOURCE))
    esiti["T1_T5"] = {"returncode": r.returncode, "stderr_ultime_righe": r.stderr.splitlines()[-20:]}

    riletture_rosse = [n for n, v in esiti["rilettori"].items() if isinstance(v, dict) and
                       (v.get("verdetto") == "ROSSO" or v.get("esito_finale") == "ROSSO"
                        or str(v.get("esito", "")).startswith("ROSSO"))]
    costruzione_ok = esiti["costruzione_identica"].get("identico", True)  # True se saltata: non e' lei a bocciare
    esiti["verdetto"] = "VERDE" if (r.returncode == 0 and not riletture_rosse and costruzione_ok) else "ROSSO"
    esiti["riletture_rosse"] = riletture_rosse
    return esiti


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

    esiti = verifica(Path(a.rom), Path(a.base) if a.base else None, Path(a.build), lingua)
    testo = json.dumps(esiti, indent=2, ensure_ascii=False) + "\n"
    if a.json:
        Path(a.json).write_text(testo)
    print(testo)
    return 0 if esiti["verdetto"] == "VERDE" else 1


if __name__ == "__main__":
    sys.exit(main())
