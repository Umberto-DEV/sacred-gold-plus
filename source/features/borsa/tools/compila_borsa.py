#!/usr/bin/env python3
"""SGP-1.2-BORSA-GEN-03 — compila il blob di `sgp.borsa`.

Stessa catena di `source/features/caramelle/tools/compila.py` (il blocco piu'
recente): **clang di sistema con `-c`**, nessun linker, e
`carica_text.load_text` — riusato dal pacchetto caramelle, non copiato — che
estrae la sola `.text` rifiutando qualunque sezione allocata in piu', qualunque
simbolo esterno e qualunque rilocazione che non sia una `BL` Thumb interna.

Il comando e' identico per fornitore e opzioni a quello registrato in
`source/sgp12/build/caramelle/manifesto.json`; l'unica aggiunta e'
`-DSGP_BORSA_BASE=...`, perche' il C deve conoscere gli indirizzi assoluti
della tabella, della staffetta e dei due puntatori agli originali (non possono
essere variabili C: sarebbero sezioni allocate fuori da .text, e `carica_text`
le rifiuta).

Uso: compila_borsa.py --uscita DIR [--base 0x023DAD00] [--cc clang]

GPL-3.0-or-later.
"""
import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

PAC = Path(__file__).resolve().parent.parent      # .../source/features/borsa
REPO = PAC.parents[2]
# `carica_text.py` e' spedito col pacchetto caramelle: si riusa quello, cosi'
# non esistono due lettori di ELF che possono divergere.
sys.path.insert(0, str(REPO / "source" / "features" / "caramelle" / "tools"))
from carica_text import load_text  # noqa: E402

SORGENTE = PAC / "sorgenti" / "borsa.c"
INTESTAZIONE = PAC / "sorgenti" / "sgp_borsa.h"
ENTRATE = ("sgp_borsa_cmd127", "sgp_borsa_cmd125",
           "sgp_borsa_has_space", "sgp_borsa_give_item")

DEF_BASE = 0x023DAD00
BLOCCO = 0x800            # 2048 B: la dimensione prenotata (PRENOTAZIONE.md §3)
OFF_CODICE = 0x000
OFF_ORIG = 0x5E0          # puntatori agli originali (2 parole + 8 B a zero)
OFF_STAFFETTA = 0x5F0     # staffetta 8 B + 8 B a zero
OFF_TABELLA = 0x600       # 120 voci u32
N_TABELLA = 120
OFF_CANARINO = 0x7F0
N_CANARINO = 16
MAX_CODICE = OFF_ORIG     # 1504 B per il codice

CANARINO_MOTIVO = 0xCA5A1700

# I due trampolini stanno in testa al blocco, a offset FISSI: l'applicatore
# scrive le due voci di gScriptCmdTable sapendo solo la base.
ENTRATE_FISSE = {"sgp_borsa_cmd127": 0x000, "sgp_borsa_cmd125": 0x008}


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

    comando = [
        a.cc, "--target=armv5te-none-eabi", "-mcpu=arm946e-s", "-mthumb", a.opt,
        "-ffreestanding", "-fno-builtin", "-fno-stack-protector",
        "-fno-unwind-tables", "-fno-asynchronous-unwind-tables",
        "-fno-jump-tables", "-Wall", "-Wextra",
        "-DSGP_BORSA_BASE=%#010xu" % a.base,
        "-c", str(SORGENTE), "-o", str(out / "borsa.o"),
    ]
    r = subprocess.run(comando, text=True, capture_output=True)
    (out / "compila.log").write_text(r.stdout + r.stderr)
    if r.returncode != 0:
        raise SystemExit("compilazione fallita; vedi compila.log\n" + r.stdout + r.stderr)
    avvisi = [x for x in (r.stdout + r.stderr).splitlines() if "warning:" in x]
    if avvisi:
        raise SystemExit("il compilatore ha avvisi, e in questo cantiere un avviso "
                         "e' un errore:\n" + "\n".join(avvisi))

    blob, simboli = load_text((out / "borsa.o").read_bytes(), codice, ENTRATE)
    if len(blob) > MAX_CODICE:
        raise SystemExit("il blob (%d B) non entra nei %d B prima dei puntatori "
                         "agli originali" % (len(blob), MAX_CODICE))
    for nome in ENTRATE:
        if simboli[nome] & 1 == 0:
            raise SystemExit("%s non ha il bit Thumb: %#x" % (nome, simboli[nome]))
    for nome, atteso in ENTRATE_FISSE.items():
        avuto = (simboli[nome] & ~1) - a.base
        if avuto != atteso:
            raise SystemExit(
                "%s e' a +%#x invece che a +%#x: le due voci di gScriptCmdTable "
                "devono poter essere scritte conoscendo solo la base del blocco"
                % (nome, avuto, atteso))

    can = canarino_bin()
    (out / "blob.bin").write_bytes(blob)
    (out / "canarino.bin").write_bytes(can)

    manifesto = {
        "pacchetto": "source/features/borsa",
        "funzione": "Borsa al tetto: l'oggetto donato o raccolto quando lo slot "
                    "e' al tetto viene comunque ricevuto e scartato "
                    "(U-borsa-progetto-esecutivo.md §4)",
        # Percorsi relativi: il manifesto deve essere riproducibile in ogni clone.
        "comando": comando[:comando.index("-c") + 1]
                   + ["source/features/borsa/sorgenti/borsa.c", "-o", "borsa.o"],
        "compilatore": subprocess.run([a.cc, "--version"], text=True,
                                      capture_output=True).stdout.splitlines()[0],
        "avvisi_compilatore": avvisi,
        "sorgente": {"file": SORGENTE.name, "sha256": sha(SORGENTE.read_bytes())},
        "intestazione": {"file": INTESTAZIONE.name,
                         "sha256": sha(INTESTAZIONE.read_bytes())},
        "indirizzi": {
            "base": hex(a.base),
            "codice": hex(codice),
            "originali": hex(a.base + OFF_ORIG),
            "staffetta": hex(a.base + OFF_STAFFETTA),
            "tabella": hex(a.base + OFF_TABELLA),
            "tabella_voci": N_TABELLA,
            "canarino": hex(a.base + OFF_CANARINO),
            "blocco_byte": BLOCCO,
            "ganci": {
                "gScriptCmdTable": "0x020FAD00",
                "voce_127": hex(0x020FAD00 + 4 * 127),
                "voce_125": hex(0x020FAD00 + 4 * 125),
                "valore_127": hex(a.base + ENTRATE_FISSE["sgp_borsa_cmd127"] + 1),
                "valore_125": hex(a.base + ENTRATE_FISSE["sgp_borsa_cmd125"] + 1),
                "originale_127": "0x0204EA89",
                "originale_125": "0x0204E9D9",
            },
        },
        "simboli": {k: hex(v) for k, v in sorted(simboli.items())},
        "blob": {"byte": len(blob), "sha256": sha(blob), "max": MAX_CODICE},
        "canarino": {"offset": hex(OFF_CANARINO), "byte": N_CANARINO,
                     "motivo": hex(CANARINO_MOTIVO), "sha256": sha(can)},
        "spazio": {
            "codice": "%d/%d B" % (len(blob), MAX_CODICE),
            "tabella": "%d B (%d voci u32)" % (N_TABELLA * 4, N_TABELLA),
            "staffetta_e_originali": "32 B",
            "canarino": "%d B" % N_CANARINO,
            "totale_blocco": BLOCCO,
        },
    }
    (out / "manifesto.json").write_text(json.dumps(manifesto, indent=2,
                                                   ensure_ascii=False) + "\n")
    print("blob %d/%d B  sha %s" % (len(blob), MAX_CODICE, sha(blob)[:16]))
    for nome in ENTRATE:
        print("  %-22s %s" % (nome, manifesto["simboli"][nome]))


if __name__ == "__main__":
    main()
