#!/usr/bin/env python3
"""Compila i quattro blob nativi della 1.2 da `sorgenti-v-finale/` e li confronta
byte per byte con i blob APPLICATI nelle ROM di lavoro.

Stessa toolchain dei pacchetti d'origine (clang di sistema, nessun linker,
`carica_text.load_text` sulla sola `.text` di un oggetto rilocabile) e gli
STESSI indirizzi con cui i blob in ROM sono stati compilati, letti dai
manifesti dei pacchetti che li hanno applicati:

    plus   SGP-1.2-PLUS-02/prove/build/manifesto.json
    salva  SGP-1.2-PLUS-03/prove/applica-salvataggio-EN.json
    npc    SGP-1.2-PRESTAZIONI-NPC-03/prove/build/manifesto.json
    wifi   SGP-1.2-WIFI-05/prove/build/manifesto.json

Uso:
    python3 tools/compila_tutti.py --uscita DIR [--sorgenti DIR] [--solo plus,npc]
"""
import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

QUI = Path(__file__).resolve().parent
sys.path.insert(0, str(QUI))
from carica_text import load_text                                # noqa: E402

PACCHETTO = QUI.parent

COMUNI = [
    "--target=armv5te-none-eabi", "-mcpu=arm946e-s", "-mthumb", "-Oz",
    "-ffreestanding", "-fno-builtin", "-fno-stack-protector", "-fno-unwind-tables",
    "-fno-asynchronous-unwind-tables", "-fno-jump-tables",
]

# nome -> (sorgente, base del blob, -D, entrate, byte applicati, sha256 applicato)
BLOB = {
    "plus": dict(
        sorgente="plus_blob.c", base=0x023D8100,
        defs=["-DSGP_PLUS_BASE=0x23d8100u"],
        entrate=("sgp_trainer_hook", "sgp_wild_hook", "sgp_trainer_level",
                 "sgp_wild_level", "sgp_group_max"),
        applicato_byte=592,
        applicato_sha="0d4079400623bcb3260defd0af7642cb5ff30e5e0050954fb48c483bc5f15057",
        max_byte=0x400),
    "salva": dict(
        sorgente="salva_blob.c", base=0x023D8220,
        defs=["-DSGP_PLUS_BASE=0x23d8100u", "-DSGP_BUF_ADDR=0x23d8f00u"],
        entrate=("sgp_gancio_carica", "sgp_gancio_salva"),
        applicato_byte=460,
        applicato_sha="35cccda383f33275036c40eee2a4ee8894a136838a48350d2f4db243514171b3",
        max_byte=0x2E0),
    "npc": dict(
        sorgente="npc_tetto.c", base=0x023D8900,
        defs=["-DSGP_PLUS_BASE=0x23d8100u", "-DSGP_STATO_NPC_ADDR=0x23d89e0u"],
        entrate=("sgp_npc_hook", "sgp_npc_tetto"),
        applicato_byte=128,
        applicato_sha="bda5f6de73a486c68a77be7e88f6e097c978fc4965b2abde95cf1a13d5f1a6a2",
        max_byte=0xE0),
    "wifi": dict(
        sorgente="wifi_slot4.c", base=0x023DA250,
        defs=["-Wall", "-DSGP_PLUS_BASE=0x23d8100u",
              "-DSGP_STATO_WIFI_ADDR=0x23da240u", "-DSGP_W1_DATI_ADDR=0x23da040u",
              "-DSGP_W1_VENEER_ADDR=0x23da000u", "-DSGP_W1_VENEER3_ADDR=0x23da020u",
              "-DSGP_DWC_LISTA_SITE=0x21fc150u", "-DSGP_DWC_CONNECT_SITE=0x21ec4a4u",
              "-DSGP_G3_PREIMMAGINE=0xe92d4000u"],
        entrate=("sgp_wfc_trampolino", "sgp_wfc_on_overlay", "sgp_wfc_on_connect",
                 "sgp_wfc_nibble", "sgp_wfc_slot_configurato", "sgp_wfc_servizio_da_lr"),
        applicato_byte=660,
        applicato_sha="13a2d94f6260779667f960bc469b2951c6d7ac688b53d6ee0291bae3ff782ac1",
        max_byte=0x1DB0),
}


def sha(b):
    return hashlib.sha256(bytes(b)).hexdigest()


def compila(nome, spec, sorgenti, uscita, cc="clang"):
    uscita.mkdir(parents=True, exist_ok=True)
    oggetto = uscita / (nome + ".o")
    comando = [cc] + COMUNI + spec["defs"] + [
        "-c", str(sorgenti / spec["sorgente"]), "-o", str(oggetto)]
    r = subprocess.run(comando, text=True, capture_output=True)
    (uscita / (nome + ".log")).write_text(r.stdout + r.stderr)
    if r.returncode != 0:
        raise SystemExit("%s: compilazione fallita\n%s%s" % (nome, r.stdout, r.stderr))
    blob, simboli = load_text(oggetto.read_bytes(), spec["base"], spec["entrate"])
    if len(blob) > spec["max_byte"]:
        raise SystemExit("%s: blob di %d B oltre i %d B riservati"
                         % (nome, len(blob), spec["max_byte"]))
    (uscita / (nome + ".bin")).write_bytes(blob)
    return {
        "comando": comando,
        "byte": len(blob),
        "sha256": sha(blob),
        "applicato_byte": spec["applicato_byte"],
        "applicato_sha256": spec["applicato_sha"],
        "identico_al_blob_applicato": sha(blob) == spec["applicato_sha"],
        "delta_byte": len(blob) - spec["applicato_byte"],
        "avvisi": [x for x in (r.stdout + r.stderr).splitlines() if x.strip()],
        "simboli": {k: hex(v) for k, v in sorted(simboli.items())},
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--uscita", type=Path, required=True)
    ap.add_argument("--sorgenti", type=Path, default=PACCHETTO / "sorgenti-v-finale")
    ap.add_argument("--cc", default="clang")
    ap.add_argument("--solo", default="")
    a = ap.parse_args()
    quali = [x for x in a.solo.split(",") if x] or list(BLOB)
    esiti = {n: compila(n, BLOB[n], a.sorgenti, a.uscita, a.cc) for n in quali}
    man = {
        "sorgenti": str(a.sorgenti),
        "compilatore": subprocess.run([a.cc, "--version"], text=True,
                                      capture_output=True).stdout.splitlines()[0],
        "blob": esiti,
        "tutti_identici": all(v["identico_al_blob_applicato"] for v in esiti.values()),
    }
    (a.uscita / "manifesto.json").write_text(json.dumps(man, indent=2) + "\n")
    print(json.dumps(man, indent=2))
    return 0 if man["tutti_identici"] else 1


if __name__ == "__main__":
    sys.exit(main())
