#!/usr/bin/env python3
"""SGP-1.2-PRESTAZIONI-NPC-02 — compila il blob del tetto NPC per il blocco
`sgp.npc` VERO della riserva ARM9 (0x023D8900, mappa Revisione 02 + questo
pacchetto), non piu' per la zona di prova del pilota (0x023DE800/0x023DE880
di SGP-1.2-PRESTAZIONI-NPC-01).

Stessa catena di compilazione di `SGP-1.2-PRESTAZIONI-NPC-01/tools/compila.py`
e di `SGP-1.2-PLUS-01/tools/compila.py` (CONTRATTO-D1 §5): clang di sistema,
`--target=armv5te-none-eabi -mthumb -Oz`, nessun linker, la sola `.text` di un
oggetto rilocabile caricata da `carica_text.py`. Il sorgente C
(`sorgenti/npc_tetto.c`) e' COPIATO INVARIATO da NPC-01: la logica e' gia'
provata (CONTRATTO-P2.md), cambia solo dove viene collocata.

Uso: compila.py --uscita DIR [--codice 0x…] [--stato 0x…] [--cc clang]
"""
import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from carica_text import load_text            # noqa: E402

SORGENTI = Path(__file__).resolve().parent.parent / "sorgenti"
ENTRATE = ("sgp_npc_hook", "sgp_npc_tetto")

# Blocco `sgp.npc`, primo spazio libero allineato a 0x100 DOPO i blocchi
# registrati in MAPPA-RISERVA-ARM9.json alla data del 12/09 (letta con questo
# pacchetto): l'ultimo blocco della zona 1.2 e' `sgp.plus` a 0x023D8100/2048,
# che finisce esattamente a 0x023D8900 = inizio di `libero.1.2`. Nessun altro
# cantiere concorrente ha registrato un blocco dopo. Vedi
# `prove/riserva-VOCE-NPC.json` per la voce pronta (non ancora scritta in
# mappa: la scrive l'applicatore quando gira IN LUOGO, PIANO-INIEZIONE.md §1).
DEF_CODICE = 0x023D8900      # +0x000 del blocco, slot 0xE0 (224 B, blob reale ~100 B)
DEF_STATO = 0x023D89E0       # +0x0E0 del blocco, 16 B (fino a 0x023D89F0)
# 0x023D89F0..0x023D8A00 (16 B): margine, a zero, non assegnato.
# 0x023D8A00: canarino.npc (16 B, motivo 0xCA5A1300|idx — 0xCA5A1000/1100/1200
# sono gia' presi da canarino.basso/canarino.camera/canarino di sgp.plus).


def sha(b):
    return hashlib.sha256(b).hexdigest()


def compila(uscita, codice=DEF_CODICE, stato=DEF_STATO, cc="clang"):
    uscita = Path(uscita)
    uscita.mkdir(parents=True, exist_ok=True)
    comando = [
        cc, "--target=armv5te-none-eabi", "-mcpu=arm946e-s", "-mthumb", "-Oz",
        "-ffreestanding", "-fno-builtin", "-fno-stack-protector",
        "-fno-unwind-tables", "-fno-asynchronous-unwind-tables", "-fno-jump-tables",
        f"-DSGP_NPC_STATO_ADDR={stato:#x}u",
        "-c", str(SORGENTI / "npc_tetto.c"), "-o", str(uscita / "npc_tetto.o"),
    ]
    r = subprocess.run(comando, text=True, capture_output=True)
    (uscita / "compila.log").write_text(r.stdout + r.stderr)
    if r.returncode != 0:
        raise SystemExit("compilazione fallita\n" + r.stdout + r.stderr)
    blob, simboli = load_text((uscita / "npc_tetto.o").read_bytes(), codice, ENTRATE)
    if len(blob) > 0xE0:
        raise SystemExit("blob %d B non entra nello slot di 224 B riservato in sgp.npc" % len(blob))
    (uscita / "blob.bin").write_bytes(blob)
    manifesto = {
        "pacchetto": "SGP-1.2-PRESTAZIONI-NPC-02",
        "comando": comando,
        "compilatore": subprocess.run([cc, "--version"], text=True,
                                      capture_output=True).stdout.splitlines()[0],
        "indirizzi": {
            "codice": hex(codice), "stato": hex(stato),
            "blocco": "sgp.npc, 0x023D8900, 256 B (prove/riserva-VOCE-NPC.json)",
        },
        "blob": {"byte": len(blob), "sha256": sha(blob)},
        "stato_byte": 16,
        "occupazione_totale_byte": len(blob) + 16,
        "simboli": {k: hex(v) for k, v in sorted(simboli.items())},
    }
    (uscita / "manifesto.json").write_text(json.dumps(manifesto, indent=2) + "\n")
    return manifesto


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--uscita", type=Path, required=True)
    ap.add_argument("--cc", default="clang")
    ap.add_argument("--codice", type=lambda x: int(x, 0), default=DEF_CODICE)
    ap.add_argument("--stato", type=lambda x: int(x, 0), default=DEF_STATO)
    a = ap.parse_args()
    m = compila(a.uscita, a.codice, a.stato, a.cc)
    print(json.dumps(m, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
