#!/usr/bin/env python3
"""SGP-1.2-RIFINITURA-01 (v3) — compila il payload dell'interfaccia.

Stessa toolchain di D1 (`SGP-1.2-PLUS-01/tools/compila.py`): clang di sistema,
**nessun linker**, si carica la sola `.text` di un oggetto rilocabile con
`carica_text.py`. I due cancelli del caricatore sono quelli di D1:
  1. nessuna sezione allocata oltre `.text` → niente costanti nel C;
  2. nessun simbolo esterno → un'unica unita' di traduzione.

Uso: compila.py --uscita DIR [--cc clang] [--codice 0x… --testi 0x… --tab 0x…
                --stato 0x… --tpl 0x… --stato-d1 0x…]
"""
import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from carica_text import load_text                       # noqa: E402

import os
# I mutanti compilano una COPIA dei sorgenti: la cartella e' scambiabile.
SORGENTI = Path(os.environ.get("SGP_UI_SORGENTI",
                               Path(__file__).resolve().parent.parent / "sorgenti"))
ENTRATE = ("sgp_ui_frame", "sgp_opz_hook",
           "sgp_cont_init", "sgp_cont_main", "sgp_cont_exit",
           "sgp_new_init", "sgp_new_main", "sgp_new_exit")

# Base = il blocco `sgp.opzioni` assegnato dall'orchestratore
# (`docs/arm9-reserve-reservations.md`): **0x023D9000**.
#
# DUE BLOCCHI. Nei 4096 B assegnati ci stanno codice (3412), risorse (84),
# tabella (24), template (32), stato (76) e canarino (16) = 3644. **Non** ci sta
# anche il blob dei testi (946 B in italiano): 4590 > 4096. Il blocco
# `sgp.wifi` comincia a 0x023DA000 e il contratto W1 dichiara FERMO l'indirizzo
# 0x023DA240, quindi `sgp.opzioni` non puo' crescere. Il blob dei testi va
# quindi in un blocco proprio, `sgp.opzioni.testi`, 1024 B a **0x023DA800** —
# il primo indirizzo libero DOPO `sgp.wifi`, che non sposta nessuno.
# **Da ratificare dall'orchestratore**: PIANO-INIEZIONE.md §1.
#
# Pianta del blocco (4096 B a partire da `codice`). Gli scarti NON sono
# arrotondamenti di comodo: sono il margine di crescita, e il controllo di
# sovrapposizione sotto e' il cancello che nella v1 ha gia' scoperto un difetto
# reale (il blob dei testi finiva dentro il codice).
# v3 (SGP-1.2-RIFINITURA-01). Il blocco resta lo STESSO (0x023D9000, 4096 B) e
# gli scomparti restano gli stessi cinque: cambia solo il CONFINE fra il codice e
# i dati di servizio. Il codice della v3 (bersagli del tocco, due meta' della riga
# dei comandi, default effettivi del chunk) e' 3652 B contro i 3412 della v2, e
# 3584 non bastavano piu'. Nel blocco c'erano 208 B mai usati fra la fine dello
# stato (+0xF20) e il canarino (+0xFF0): il confine si sposta li', invece di
# contorcere il codice per rientrare in un numero tondo. Nessun byte esce dal
# blocco, il canarino resta dov'e', e gli scomparti restano allineati a 32 B.
#     codice +0x000 3776 B (era 3584)   ris +0xEC0 96   tab +0xF20 32 (voci=24)
#     tpl    +0xF40   32                stato +0xF60 96  libero +0xFC0 48
DEF = {"codice": 0x023D9000, "ris": 0x023D9EC0, "tab": 0x023D9F20,
       "tpl": 0x023D9F40, "stato": 0x023D9F60, "testi": 0x023DA800,
       "stato_d1": 0x023D8700, "stato_npc": 0x023D89E0,
       "stato_anim": 0x023D8E40, "stato_wifi": 0x023DA240}
# solo le aree DENTRO il blocco entrano nel controllo di sovrapposizione: gli
# stati altrui stanno in blocchi di altri proprietari.
# blocco 1: sgp.opzioni (0x023D9000, 4096 B) — codice e dati di servizio
PIANTA = [("codice", 0xEC0), ("ris", 0x60), ("tab", 0x20),
          ("tpl", 0x20), ("stato", 0x60)]
# blocco 2: sgp.opzioni.testi (0x023DA800, 1024 B) — il blob della lingua
PIANTA_TESTI = [("testi", 0x3F0)]
BLOCCO_TESTI_BYTE = 1024
CANARINO = 0x10          # 16 B di canarino in coda al blocco
BLOCCO_BYTE = 5120


def sha(b):
    return hashlib.sha256(b).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--uscita", type=Path, required=True)
    ap.add_argument("--cc", default="clang")
    for k, v in DEF.items():
        ap.add_argument("--" + k.replace("_", "-"), type=lambda x: int(x, 0), default=v)
    args = ap.parse_args()
    out = args.uscita
    out.mkdir(parents=True, exist_ok=True)

    comando = [
        args.cc, "--target=armv5te-none-eabi", "-mcpu=arm946e-s", "-mthumb", "-Oz",
        "-ffreestanding", "-fno-builtin", "-fno-stack-protector", "-fno-unwind-tables",
        "-fno-asynchronous-unwind-tables", "-fno-jump-tables", "-Wall",
        f"-DSGP_UI_ADDR={args.codice:#x}u",
        f"-DSGP_UI_TESTI_ADDR={args.testi:#x}u",
        f"-DSGP_UI_TAB_ADDR={args.tab:#x}u",
        f"-DSGP_UI_STATO_ADDR={args.stato:#x}u",
        f"-DSGP_UI_TPL_ADDR={args.tpl:#x}u",
        f"-DSGP_UI_RIS_ADDR={args.ris:#x}u",
        f"-DSGP_STATO_D1_ADDR={args.stato_d1:#x}u",
        f"-DSGP_STATO_NPC_ADDR={args.stato_npc:#x}u",
        f"-DSGP_STATO_ANIM_ADDR={args.stato_anim:#x}u",
        f"-DSGP_STATO_WIFI_ADDR={args.stato_wifi:#x}u",
        "-c", str(SORGENTI / "ui_blob.c"), "-o", str(out / "ui_blob.o"),
    ]
    r = subprocess.run(comando, text=True, capture_output=True)
    (out / "compila.log").write_text(r.stdout + r.stderr)
    if r.returncode != 0:
        raise SystemExit("compilazione fallita; vedi compila.log\n" + r.stdout + r.stderr)

    blob, simboli = load_text((out / "ui_blob.o").read_bytes(), args.codice, ENTRATE)
    (out / "ui_blob.bin").write_bytes(blob)

    # G0 — nessuna area del blocco puo' sovrapporsi a un'altra, e il codice deve
    # stare nel suo scomparto. Un byte di troppo qui e' un guasto silenzioso a
    # runtime: il testo finirebbe dentro le istruzioni.
    aree = [(getattr(args, k), k, t) for k, t in PIANTA]
    aree.sort()
    for (a1, n1, t1), (a2, n2, _) in zip(aree, aree[1:]):
        if a1 + t1 > a2:
            raise SystemExit(f"G0: {n1} ({a1:#x}+{t1:#x}) invade {n2} ({a2:#x})")
    if len(blob) > dict(PIANTA)["codice"]:
        raise SystemExit(f"G0: il codice e' {len(blob)} B, lo scomparto e' "
                         f"{dict(PIANTA)['codice']} B")
    if aree[-1][0] + aree[-1][2] > args.codice + BLOCCO_BYTE - CANARINO:
        raise SystemExit("G0: la pianta invade il canarino di coda del blocco "
                         "di %d B" % BLOCCO_BYTE)
    if args.testi + dict(PIANTA_TESTI)["testi"] > args.testi + BLOCCO_TESTI_BYTE - CANARINO:
        raise SystemExit("G0: il blob dei testi invade il canarino del suo blocco")
    for a, n, t in aree:
        if not (args.testi + BLOCCO_TESTI_BYTE <= a or a + t <= args.testi):
            raise SystemExit("G0: %s si sovrappone al blocco dei testi" % n)

    manifesto = {
        "pacchetto": "SGP-1.2-OPZIONI-03",
        "comando": comando,
        "compilatore": subprocess.run([args.cc, "--version"], text=True,
                                      capture_output=True).stdout.splitlines()[0],
        "indirizzi": {k: hex(getattr(args, k)) for k in DEF},
        "zona": "PROVA — il blocco definitivo lo assegna la fase di iniezione "
                "(PIANO-INIEZIONE.md); gli indirizzi sono parametrici (-D).",
        "blob": {"byte": len(blob), "sha256": sha(blob)},
        "pianta": {n: {"ram": hex(getattr(args, n)), "byte": t}
                   for n, t in PIANTA + PIANTA_TESTI},
        "blocco_byte": BLOCCO_BYTE,
        "blocco_testi_byte": BLOCCO_TESTI_BYTE,
        "simboli": {k: hex(v) for k, v in sorted(simboli.items())},
        "avvisi_compilatore": [l for l in (r.stdout + r.stderr).splitlines() if l.strip()],
    }
    (out / "manifesto.json").write_text(json.dumps(manifesto, indent=1) + "\n")
    print(json.dumps({"blob": manifesto["blob"],
                      "compilatore": manifesto["compilatore"],
                      "avvisi": len(manifesto["avvisi_compilatore"])}, indent=1))
    print("simboli:", json.dumps(manifesto["simboli"], indent=1))


if __name__ == "__main__":
    main()
