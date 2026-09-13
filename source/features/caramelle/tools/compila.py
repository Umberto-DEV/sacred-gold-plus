#!/usr/bin/env python3
"""SGP-1.2-CARAMELLE-01 — compila il blob di `sgp.caramelle`.

Stessa catena dei cantieri 1.2 (`source/features/anim/tools/compila_anim4.py`,
`source/features/native-core/tools/compila_tutti.py`): **clang di sistema con
`-c`**, nessun linker (`ld.lld` non esiste in questo ambiente e non serve), e
`carica_text.load_text` estrae la sola `.text`, rifiutando qualunque sezione
allocata in più, qualunque simbolo esterno e qualunque rilocazione che non sia
una `BL` Thumb interna.

Uso: compila.py --uscita DIR [--base 0x023DAC00] [--cc clang]

Il blob spedito sta in `source/sgp12/build/caramelle/blob.bin`: questo comando
lo riproduce byte per byte dai sorgenti di `../sorgenti/`.
GPL-3.0-or-later.
"""
import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

PAC = Path(__file__).resolve().parent.parent          # source/features/caramelle
sys.path.insert(0, str(Path(__file__).resolve().parent))
from carica_text import load_text  # noqa: E402

SORGENTE = PAC / "sorgenti" / "caramelle.c"
ENTRATE = ("sgp_caramelle_gancio", "sgp_caramelle_decidi")

DEF_BASE = 0x023DAC00
BLOCCO = 0x100          # 256 B: la dimensione prenotata (PRENOTAZIONE.md)
OFF_CODICE = 0x000
OFF_CANARINO = 0x0F0    # il canarino sta DENTRO il blocco
N_CANARINO = 16
MAX_CODICE = OFF_CANARINO   # 240 B per il codice

CANARINO_MOTIVO = 0xCA5A1600


def sha(b):
    return hashlib.sha256(bytes(b)).hexdigest()


def canarino_bin():
    return b"".join((CANARINO_MOTIVO | i).to_bytes(4, "little")
                    for i in range(N_CANARINO // 4))


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--uscita", type=Path, required=True)
    ap.add_argument("--cc", default="clang")
    ap.add_argument("--opt", default="-Oz")
    ap.add_argument("--base", type=lambda x: int(x, 0), default=DEF_BASE)
    a = ap.parse_args()
    out = a.uscita
    out.mkdir(parents=True, exist_ok=True)

    codice = a.base + OFF_CODICE
    canarino = a.base + OFF_CANARINO

    comando = [
        a.cc, "--target=armv5te-none-eabi", "-mcpu=arm946e-s", "-mthumb", a.opt,
        "-ffreestanding", "-fno-builtin", "-fno-stack-protector",
        "-fno-unwind-tables", "-fno-asynchronous-unwind-tables",
        "-fno-jump-tables", "-Wall", "-Wextra",
        "-c", str(SORGENTE), "-o", str(out / "caramelle.o"),
    ]
    r = subprocess.run(comando, text=True, capture_output=True)
    (out / "compila.log").write_text(r.stdout + r.stderr)
    if r.returncode != 0:
        raise SystemExit("compilazione fallita; vedi compila.log\n" + r.stdout + r.stderr)
    avvisi = [x for x in (r.stdout + r.stderr).splitlines() if "warning:" in x]
    if avvisi:
        raise SystemExit("il compilatore ha avvisi, e in questo cantiere un avviso "
                         "è un errore:\n" + "\n".join(avvisi))

    blob, simboli = load_text((out / "caramelle.o").read_bytes(), codice, ENTRATE)
    if len(blob) > MAX_CODICE:
        raise SystemExit("il blob (%d B) non entra nei %d B prima del canarino"
                         % (len(blob), MAX_CODICE))
    for nome in ENTRATE:
        if simboli[nome] & 1 == 0:
            raise SystemExit("%s non ha il bit Thumb: %#x" % (nome, simboli[nome]))
    if simboli["sgp_caramelle_gancio"] & ~1 != codice:
        raise SystemExit(
            "sgp_caramelle_gancio non è al primo byte del blocco (%#x invece di %#x): "
            "il gancio nell'ARM9 deve poter puntare alla base senza sapere l'offset"
            % (simboli["sgp_caramelle_gancio"] & ~1, codice))

    can = canarino_bin()
    (out / "blob.bin").write_bytes(blob)
    (out / "canarino.bin").write_bytes(can)

    manifesto = {
        "pacchetto": "SGP-1.2-CARAMELLE-01",
        "funzione": "Caramella Rara riutilizzabile dal menu squadra (opzione (a) "
                    "di M-borsa-riuso-caramelle.md)",
        "comando": comando,
        "compilatore": subprocess.run([a.cc, "--version"], text=True,
                                      capture_output=True).stdout.splitlines()[0],
        "avvisi_compilatore": avvisi,
        "sorgente": {"file": SORGENTE.name, "sha256": sha(SORGENTE.read_bytes())},
        "indirizzi": {
            "base": hex(a.base),
            "codice": hex(codice),
            "canarino": hex(canarino),
            "blocco_byte": BLOCCO,
            "gancio_arm9": "0x02081E96",
        },
        "simboli": {k: hex(v) for k, v in sorted(simboli.items())},
        "blob": {"byte": len(blob), "sha256": sha(blob), "max": MAX_CODICE},
        "canarino": {"offset": hex(OFF_CANARINO), "byte": N_CANARINO,
                     "motivo": hex(CANARINO_MOTIVO), "sha256": sha(can)},
    }
    (out / "manifesto.json").write_text(json.dumps(manifesto, indent=2,
                                                   ensure_ascii=False) + "\n")
    print("blob %d B  sha %s" % (len(blob), sha(blob)[:16]))
    print("entrata sgp_caramelle_gancio = %s" % manifesto["simboli"]["sgp_caramelle_gancio"])


if __name__ == "__main__":
    main()
