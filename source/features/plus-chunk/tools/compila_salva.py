#!/usr/bin/env python3
"""SGP-1.2-PLUS-03 — compila il blob `sgp.salvataggio`.

Stessa toolchain e stesso modello di caricamento di `SGP-1.2-PLUS-01`: clang di
sistema, nessun linker, `carica_text.load_text` prende la sola `.text` di un
oggetto rilocabile e risolve le sole `BL` Thumb interne. Vincoli che ne
discendono (sono cancelli, non stile): una sola unità di traduzione, nessun
simbolo esterno, nessuna sezione allocata oltre `.text`.

Uso: compila_salva.py --uscita DIR [--codice 0x023D8F00 --stato 0x023D8700
                                    --buf 0x023D8FC0 --scratch 0x023D8FE0]
"""
import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

QUI = Path(__file__).resolve().parent
sys.path.insert(0, str(QUI))
from carica_text import load_text            # noqa: E402

SORGENTI = QUI.parent / "sorgenti"
ENTRATE = ("sgp_gancio_carica", "sgp_gancio_salva")

DEF_CODICE = 0x023D8730
DEF_STATO = 0x023D8700
DEF_BUF = 0x023D8F00
MAX_CODICE = 0x1D0         # sgp.plus +0x630 .. +0x800


def sha(b):
    return hashlib.sha256(b).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--uscita", type=Path, required=True)
    ap.add_argument("--cc", default="clang")
    ap.add_argument("--codice", type=lambda x: int(x, 0), default=DEF_CODICE)
    ap.add_argument("--stato", type=lambda x: int(x, 0), default=DEF_STATO)
    ap.add_argument("--buf", type=lambda x: int(x, 0), default=DEF_BUF)
    ap.add_argument("--max-codice", type=lambda x: int(x, 0), default=MAX_CODICE)
    a = ap.parse_args()
    out = a.uscita
    out.mkdir(parents=True, exist_ok=True)

    comando = [
        a.cc, "--target=armv5te-none-eabi", "-mcpu=arm946e-s", "-mthumb", "-Oz",
        "-ffreestanding", "-fno-builtin", "-fno-stack-protector", "-fno-unwind-tables",
        "-fno-asynchronous-unwind-tables", "-fno-jump-tables",
        f"-DSGP_STATO_ADDR={a.stato:#x}u",
        f"-DSGP_BUF_ADDR={a.buf:#x}u",
        "-c", str(SORGENTI / "salva_blob.c"), "-o", str(out / "salva_blob.o"),
    ]
    r = subprocess.run(comando, text=True, capture_output=True)
    (out / "compila.log").write_text(r.stdout + r.stderr)
    if r.returncode != 0:
        raise SystemExit("compilazione fallita; vedi compila.log\n" + r.stdout + r.stderr)

    blob, simboli = load_text((out / "salva_blob.o").read_bytes(), a.codice, ENTRATE)
    if len(blob) > a.max_codice:
        raise SystemExit("blob di %d B: non entra nei %d B riservati al codice "
                         "(il buffer comincia a +%#x)" % (len(blob), a.max_codice, a.max_codice))
    (out / "salva_blob.bin").write_bytes(blob)

    manifesto = {
        "pacchetto": "SGP-1.2-PLUS-03",
        "comando": comando,
        "compilatore": subprocess.run([a.cc, "--version"], text=True,
                                      capture_output=True).stdout.splitlines()[0],
        "indirizzi": {"codice": hex(a.codice), "stato": hex(a.stato),
                      "buffer": hex(a.buf)},
        "blob": {"byte": len(blob), "sha256": sha(blob), "spazio_riservato": a.max_codice},
        "simboli": {k: hex(v) for k, v in sorted(simboli.items())},
    }
    (out / "manifesto.json").write_text(json.dumps(manifesto, indent=2) + "\n")
    print(json.dumps(manifesto, indent=2))


if __name__ == "__main__":
    main()
