#!/usr/bin/env python3
"""sgp12.costruisci — UN comando per costruire la ROM Sacred Gold Plus 1.2 da
una base 1.1, applicando tutti i blocchi in ordine:

    riserva -> camera -> plus+chunk -> testi -> npc -> anim -> opzioni -> wifi -> titolo -> credito -> guida

Uso:
    python3 -m sgp12.costruisci --base base-1.1-EN.nds --uscita sgp-1.2-EN.nds --lingua EN
    python3 -m sgp12.costruisci --base base-1.1-IT.nds --uscita sgp-1.2-IT.nds --lingua IT

`--build` (default: `sgp12/build/`) e' la cartella con i blob gia' validati di
ogni blocco (vedi README.md per la mappa) e `MAPPA-RISERVA-ARM9.json`.

Richiede `ndspy` (`source/requirements.txt`): riserva, plus e testi lo usano.
La ROM di partenza sta in una cartella privata, fuori da questo repository,
e si passa con `--base`.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from .rom import Rifiuto, sha
from .blocchi import riserva, camera, plus_chunk, testi, npc, anim, opzioni, wifi, titolo, guida

BUILD_DEFAULT = Path(__file__).resolve().parent / "build"


def costruisci(base: bytes, lingua: str, build_dir: Path, log_dir: Path | None = None) -> tuple[bytes, dict]:
    build_dir = Path(build_dir)
    manifest = build_dir / "riserva" / "MAPPA-RISERVA-ARM9.json"
    passi = []

    def registra(nome, t0, out, extra=None):
        passi.append({"blocco": nome, "secondi": round(time.time() - t0, 2),
                      "sha256": sha(out), "bytes": len(out), **(extra or {})})
        if log_dir:
            Path(log_dir).mkdir(parents=True, exist_ok=True)
            (Path(log_dir) / ("%02d-%s.json" % (len(passi), nome))).write_text(
                json.dumps(passi[-1], indent=2, ensure_ascii=False) + "\n")
            # ROM intermedia: serve a `verifica.py` per i rilettori pensati
            # per un confronto PASSO-PASSO (base immediatamente precedente),
            # non contro la ROM finale con tutti gli 8 blocchi applicati.
            (Path(log_dir) / ("%02d-%s.nds" % (len(passi), nome))).write_bytes(out)

    rom = base
    t0 = time.time()
    rom, _ = riserva.applica(rom, build_dir / "riserva", etichetta=lingua)
    registra("riserva", t0, rom)

    t0 = time.time()
    rom, _ = camera.applica(rom)
    registra("camera", t0, rom)

    t0 = time.time()
    rom, _ = plus_chunk.applica(rom, build_dir, manifest_path=manifest)
    registra("plus_chunk", t0, rom)

    t0 = time.time()
    rom, rep_testi = testi.applica(rom, build_dir / "testi", lingua)
    registra("testi", t0, rom, {"narc_modificato": rep_testi.get("narc_modificato")})

    t0 = time.time()
    rom, _ = npc.applica(rom, build_dir / "npc", manifest_path=manifest, attivo=1, tetto=1)
    registra("npc", t0, rom)

    t0 = time.time()
    rom, _ = anim.applica(rom, build_dir / "anim", manifest_path=manifest, flags=0)
    registra("anim", t0, rom)

    t0 = time.time()
    rom, _ = opzioni.applica(rom, build_dir / "opzioni", lingua=lingua, manifest_path=manifest)
    registra("opzioni", t0, rom)

    t0 = time.time()
    rom, _ = wifi.applica(rom, build_dir / "wifi", manifest_path=manifest)
    registra("wifi", t0, rom)

    t0 = time.time()
    rom, _ = titolo.applica(rom)
    registra("titolo", t0, rom)

    t0 = time.time()
    rom, _ = titolo.applica_credito(rom)
    registra("credito", t0, rom)

    t0 = time.time()
    rom, _ = guida.applica(rom)
    registra("guida", t0, rom)

    return rom, {"lingua": lingua, "base_sha256": sha(base), "uscita_sha256": sha(rom),
                "uscita_bytes": len(rom), "passi": passi}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base", required=True, help="base-1.1-{EN,IT}.nds")
    ap.add_argument("--uscita", required=True)
    ap.add_argument("--lingua", choices=("EN", "IT"))
    ap.add_argument("--build", default=str(BUILD_DEFAULT))
    ap.add_argument("--log-dir", default=None)
    ap.add_argument("--json", default=None)
    a = ap.parse_args(argv)

    lingua = a.lingua
    if lingua is None:
        nome = Path(a.base).name.upper()
        lingua = "IT" if "-IT" in nome else "EN"
        print("--lingua non data: dedotta '%s' dal nome del file base" % lingua)

    base = Path(a.base).read_bytes()
    try:
        rom, rapporto = costruisci(base, lingua, Path(a.build), Path(a.log_dir) if a.log_dir else None)
    except Rifiuto as e:
        print("RIFIUTO: %s" % e, file=sys.stderr)
        return 2

    Path(a.uscita).parent.mkdir(parents=True, exist_ok=True)
    Path(a.uscita).write_bytes(rom)
    testo = json.dumps(rapporto, indent=2, ensure_ascii=False) + "\n"
    if a.json:
        Path(a.json).write_text(testo)
    print(testo)
    print("COSTRUITA %s  sha256 %s" % (a.uscita, rapporto["uscita_sha256"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
