#!/usr/bin/env python3
"""Compila soltanto i piccoli wrapper; nessuna ROM, download o linker."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

QUI = Path(__file__).resolve().parent
SOURCE = QUI.parents[1]
sys.path.insert(0, str(SOURCE / "features/anim/tools"))
from carica_text import load_text

PARTI = {
    "copie": (0x023DBC60, 144,
              ("sgp_copia_inizio", "sgp_copia_fine", "sgp_idle_copie")),
    "cascata": (0x023D8040, 48, ("sgp_cerca_cascata",)),
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def compila(uscita: Path, cc="clang") -> dict:
    uscita = Path(uscita)
    uscita.mkdir(parents=True, exist_ok=True)
    m = {"schema": 1, "stato": "candidato; verifica in gioco non eseguita",
         "compilatore": subprocess.check_output([cc, "--version"], text=True).splitlines()[0],
         "parti": {}}
    with tempfile.TemporaryDirectory(prefix="sgp-manutenzione-") as td:
        for nome, (base, limite, entrate) in PARTI.items():
            src = QUI / "sorgenti" / (nome + ".S")
            obj = Path(td) / (nome + ".o")
            subprocess.run([cc, "--target=armv5te-none-eabi", "-mcpu=arm946e-s",
                            "-mthumb", "-c", str(src), "-o", str(obj)], check=True)
            blob, simboli = load_text(obj.read_bytes(), base, entrate)
            if len(blob) > limite:
                raise ValueError(f"{nome}: {len(blob)} B superano {limite} B")
            can = b"".join((0xCA5A2000 + (0x10 if nome == "cascata" else 0) + i)
                           .to_bytes(4, "little") for i in range(4))
            payload = blob.ljust(limite, b"\0") + can
            (uscita / (nome + ".bin")).write_bytes(payload)
            m["parti"][nome] = {"base": base, "bytes": len(payload),
                "codice_bytes": len(blob), "limite_codice": limite, "sha256": sha(payload),
                "sorgente": str(src.relative_to(SOURCE.parent)), "sorgente_sha256": sha(src.read_bytes()),
                "simboli": {n: simboli[n] for n in entrate}}
    m["compila_sha256"] = sha(Path(__file__).read_bytes())
    (uscita / "manifesto.json").write_text(json.dumps(m, indent=2, ensure_ascii=False) + "\n")
    return m


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--uscita", type=Path, required=True)
    args = ap.parse_args()
    m = compila(args.uscita)
    for n, p in m["parti"].items():
        print(f"{n}: {p['codice_bytes']}/{p['limite_codice']} B codice; {p['bytes']} B con canarino")
