#!/usr/bin/env python3
"""Compila i blob nativi dai sorgenti spediti e li confronta con i blob
SPEDITI (`source/sgp12/build/**`), cioe' con quelli che `sgp12.costruisci`
scrive nella ROM.

**L'identita' byte per byte vale solo a parita' di toolchain.** I blob spediti
sono stati compilati da un compilatore preciso, che ogni manifesto dichiara
(`"compilatore"`). Un altro compilatore — un altro fornitore, un'altra versione
maggiore — genera codice diverso a parita' di sorgente: pretendere gli stessi
byte sarebbe una pretesa sul compilatore, non sul sorgente, e su Ubuntu
renderebbe la CI rossa per un motivo che non e' un difetto. Quando l'identita'
del compilatore corrente non e' quella del manifesto il confronto viene
dichiarato NON VALIDO (`confronto_valido: false`, con il motivo scritto per
esteso) e al suo posto resta la pretesa che si puo' onorare ovunque: il blob
ricompilato e' VALIDO — sta nel suo scomparto e non ha simboli esterni
(`carica_text.load_text` rifiuta gli uni e gli altri).

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
import re
import subprocess
import sys
from pathlib import Path

QUI = Path(__file__).resolve().parent
sys.path.insert(0, str(QUI))
from carica_text import load_text                                # noqa: E402

PACCHETTO = QUI.parent
# I byte SPEDITI: `source/sgp12/build/**`, cioe' esattamente cio' che
# `sgp12.costruisci` scrive nella ROM. Prima di questa correzione i quattro
# riferimenti erano sha256 CABLATI qui, presi dai manifesti dei pacchetti
# d'origine (PLUS-01, PLUS-03, NPC-03, WIFI-05): tutti e quattro descrivevano i
# blob PRE-`sorgenti-v-finale/`, quindi `tutti_identici` era false e il comando
# usciva 1 in ogni caso — un confronto che non poteva mai tornare, e che quindi
# non segnalava piu' niente. Ora il riferimento e' il file spedito, che e'
# anche l'unico che conti: se un blob cambia, si aggiorna quello e il confronto
# torna a dire qualcosa.
SOURCE = PACCHETTO.parent.parent
BUILD = SOURCE / "sgp12" / "build"


def identita(versione: str):
    """(fornitore, versione maggiore) da una riga `clang --version`.

    `Apple clang version 21.0.0 (clang-2100.3.34.2)` -> `('Apple', 21)`
    `Ubuntu clang version 18.1.3 (1ubuntu1)`         -> `('Ubuntu', 18)`
    `clang version 18.1.8`                           -> `('LLVM', 18)`

    Una riga che non si sa leggere da `(None, None)`: due identita' ignote non
    sono mai uguali (vedi `stessa_toolchain`), quindi nel dubbio il confronto
    byte per byte NON viene preteso."""
    m = re.match(r"^(?:([A-Za-z][\w.+-]*)\s+)?clang version (\d+)\.", (versione or "").strip())
    if not m:
        return (None, None)
    return (m.group(1) or "LLVM", int(m.group(2)))


def stessa_toolchain(a: str, b: str) -> bool:
    """Due righe di versione descrivono lo stesso compilatore? Solo fornitore e
    versione MAGGIORE contano: `21.0.0` e `21.1.2` dello stesso fornitore danno
    gli stessi byte per i nostri blob, `Apple 21` e `LLVM 18` no. Se anche una
    sola delle due non e' leggibile la risposta e' NO."""
    ia, ib = identita(a), identita(b)
    return ia == ib and ia != (None, None)


def descrivi(versione: str) -> str:
    fornitore, maggiore = identita(versione)
    if fornitore is None:
        return "compilatore non riconosciuto (%r)" % (versione or "")
    return "%s clang %d" % (fornitore, maggiore)

COMUNI = [
    "--target=armv5te-none-eabi", "-mcpu=arm946e-s", "-mthumb", "-Oz",
    "-ffreestanding", "-fno-builtin", "-fno-stack-protector", "-fno-unwind-tables",
    "-fno-asynchronous-unwind-tables", "-fno-jump-tables",
]

# nome -> sorgente, base del blob, -D, entrate, blob spedito, scomparto e
# manifesto spedito (da cui si legge l'identita' del compilatore di riferimento).
# `sorgenti_dir` sta solo dove i sorgenti NON sono in `sorgenti-v-finale/`.
BLOB = {
    "plus": dict(
        sorgente="plus_blob.c", base=0x023D8100,
        defs=["-DSGP_PLUS_BASE=0x23d8100u"],
        entrate=("sgp_trainer_hook", "sgp_wild_hook", "sgp_trainer_level",
                 "sgp_wild_level", "sgp_group_max"),
        spedito="plus/blob.bin", manifesto="plus/manifesto.json",
        max_byte=0x400),
    "salva": dict(
        sorgente="salva_blob.c", base=0x023D8220,
        defs=["-DSGP_PLUS_BASE=0x23d8100u", "-DSGP_BUF_ADDR=0x23d8f00u"],
        entrate=("sgp_gancio_carica", "sgp_gancio_salva"),
        spedito="plus/salva_blob.bin", manifesto="plus/manifesto.json",
        max_byte=0x2E0),
    "npc": dict(
        sorgente="npc_tetto.c", base=0x023D8900,
        defs=["-DSGP_PLUS_BASE=0x23d8100u", "-DSGP_STATO_NPC_ADDR=0x23d89e0u"],
        entrate=("sgp_npc_hook", "sgp_npc_tetto"),
        spedito="npc/blob.bin", manifesto="npc/manifesto.json",
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
        spedito="wifi/vfinale/blob.bin", manifesto="wifi/vfinale/manifesto.json",
        max_byte=0x1DB0),
    # Il blob delle Caramelle Rare non sta in `native-core/sorgenti-v-finale/`:
    # ha il suo pacchetto. Stava pero' fuori da QUESTO registro, cioe' fuori
    # dall'unico posto in cui la Classe A ricompila i sorgenti spediti e li
    # confronta con i byte che finiscono in ROM — era l'unico blob di codice
    # della 1.2.1 che nessun cancello ricompilava.
    "caramelle": dict(
        sorgente="caramelle.c", base=0x023DAC00,
        sorgenti_dir=SOURCE / "features" / "caramelle" / "sorgenti",
        defs=["-Wall", "-Wextra"],
        entrate=("sgp_caramelle_gancio", "sgp_caramelle_decidi"),
        spedito="caramelle/blob.bin", manifesto="caramelle/manifesto.json",
        max_byte=0xF0),
}


def sha(b):
    return hashlib.sha256(bytes(b)).hexdigest()


def versione_compilatore(cc="clang"):
    r = subprocess.run([cc, "--version"], text=True, capture_output=True)
    righe = (r.stdout or "").splitlines()
    return righe[0] if righe else ""


def compila(nome, spec, sorgenti, uscita, cc="clang", versione_cc=None):
    uscita.mkdir(parents=True, exist_ok=True)
    oggetto = uscita / (nome + ".o")
    sorgenti = spec.get("sorgenti_dir") or sorgenti
    comando = [cc] + COMUNI + spec["defs"] + [
        "-c", str(sorgenti / spec["sorgente"]), "-o", str(oggetto)]
    r = subprocess.run(comando, text=True, capture_output=True)
    (uscita / (nome + ".log")).write_text(r.stdout + r.stderr)
    if r.returncode != 0:
        raise SystemExit("%s: compilazione fallita\n%s%s" % (nome, r.stdout, r.stderr))
    # `load_text` e' anche il cancello dei simboli esterni: un oggetto che ne
    # porti uno solo non arriva mai a essere un blob (`ValueError`).
    blob, simboli = load_text(oggetto.read_bytes(), spec["base"], spec["entrate"])
    if len(blob) > spec["max_byte"]:
        raise SystemExit("%s: blob di %d B oltre i %d B riservati"
                         % (nome, len(blob), spec["max_byte"]))
    (uscita / (nome + ".bin")).write_bytes(blob)
    rif = BUILD / spec["spedito"]
    if not rif.exists():
        raise SystemExit("%s: manca il blob spedito %s" % (nome, rif))
    atteso = rif.read_bytes()

    # Identita' del compilatore: quella del manifesto spedito contro quella in
    # esecuzione adesso. Solo a parita' di identita' l'identita' dei BYTE e' una
    # pretesa sul sorgente; altrimenti e' una pretesa sul compilatore.
    man_path = BUILD / spec["manifesto"]
    if not man_path.exists():
        raise SystemExit("%s: manca il manifesto spedito %s" % (nome, man_path))
    cc_manifesto = json.loads(man_path.read_text()).get("compilatore") or ""
    cc_corrente = versione_cc if versione_cc is not None else versione_compilatore(cc)
    valido = stessa_toolchain(cc_manifesto, cc_corrente)
    motivo = None if valido else ("toolchain diversa: %s vs %s"
                                  % (descrivi(cc_corrente), descrivi(cc_manifesto)))

    return {
        "comando": comando,
        "byte": len(blob),
        "sha256": sha(blob),
        "spedito": spec["spedito"],
        "manifesto": spec["manifesto"],
        "applicato_byte": len(atteso) if atteso is not None else None,
        "applicato_sha256": sha(atteso) if atteso is not None else None,
        "identico_al_blob_applicato": atteso is not None and bytes(blob) == atteso,
        "delta_byte": len(blob) - len(atteso) if atteso is not None else None,
        "scomparto_byte": spec["max_byte"],
        # Vere a prescindere dal compilatore: le pretese che restano quando il
        # confronto byte per byte non e' valido.
        "valido": len(blob) <= spec["max_byte"] and len(blob) > 0,
        "compilatore_del_manifesto": cc_manifesto,
        "compilatore_corrente": cc_corrente,
        "confronto_valido": valido,
        "motivo_salto": motivo,
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
    cc_corrente = versione_compilatore(a.cc)
    esiti = {n: compila(n, BLOB[n], a.sorgenti, a.uscita, a.cc, cc_corrente)
             for n in quali}
    confrontati = {n: v for n, v in esiti.items() if v["confronto_valido"]}
    saltati = {n: v["motivo_salto"] for n, v in esiti.items() if not v["confronto_valido"]}
    # Il verdetto: identita' dove il confronto vale, validita' dove non vale.
    # `tutti_identici` resta e dice solo quello che dice il suo nome: non e'
    # piu' il verdetto, perche' su un'altra toolchain sarebbe falso per un
    # motivo che non e' un difetto.
    man = {
        "sorgenti": str(a.sorgenti),
        "compilatore": cc_corrente,
        "identita_compilatore": "%s clang %s" % identita(cc_corrente),
        "blob": esiti,
        "tutti_identici": all(v["identico_al_blob_applicato"] for v in esiti.values()),
        "confrontati": sorted(confrontati),
        "saltati": saltati,
        "verdetto": "ok" if (all(v["identico_al_blob_applicato"] for v in confrontati.values())
                             and all(v["valido"] for v in esiti.values())) else "rosso",
    }
    (a.uscita / "manifesto.json").write_text(json.dumps(man, indent=2) + "\n")
    print(json.dumps(man, indent=2))
    return 0 if man["verdetto"] == "ok" else 1


if __name__ == "__main__":
    sys.exit(main())
