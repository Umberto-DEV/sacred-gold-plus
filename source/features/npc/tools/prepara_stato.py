#!/usr/bin/env python3
"""SGP-1.2-PRESTAZIONI-NPC-01 — savestate ancorato al confine di zona.

Avvia il gioco a freddo con la fixture, cammina verso sud e salva un savestate
`N` fotogrammi PRIMA che la Z del giocatore raggiunga la soglia del confine
(Z >= 384, il bordo Fiordoropoli / Percorso 34 di `12c` §4). Stampa solo numeri.

FASE 02b — `--congela ADDR:VAL:W` (stesso formato di `corsa_confine.py`),
applicato SUBITO DOPO l'avvio, PRIMA del preludio: serve perche' il campo
`tetto` della lista di richieste del gioco (CONTRATTO-P2.md) e' persistente
fra un fotogramma e l'altro (si azzera solo quando la lista si reinizializza,
non ogni fotogramma). Se l'attivazione derivata dal chunk D1 e' ACCESA fin dal
primo fotogramma di gioco (come l'ASSENTE di default), il nostro gancio
abbassa quel campo da subito e nessun freeze applicato PIU' TARDI (a ridosso
del confine) lo puo' far tornare a 10: bisogna decidere prima di camminare,
non prima di attraversare.

Uso:
  prepara_stato.py --rom ROM --sram SAV --out DIR --stato NOME.state
                   [--anticipo 12] [--soglia 384] [--max 900]
                   [--congela ADDR:VAL:W ...]
"""
import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from banco import Banco, W_MAPPA, W_PZ, W_PX, VBLANK  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--harness", default="<your build>/hg_runtime")
    ap.add_argument("--rom", required=True)
    ap.add_argument("--sram", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--stato", default="confine.state")
    ap.add_argument("--anticipo", type=int, default=12)
    ap.add_argument("--soglia", type=int, default=384)
    ap.add_argument("--max", type=int, default=900)
    ap.add_argument("--congela", action="append", default=[],
                    help="ADDR:VAL:W, applicato PRIMA del preludio (vedi docstring)")
    ap.add_argument("--json", default="")
    a = ap.parse_args()

    b = Banco(a.harness, a.rom, a.out, sram=a.sram)
    for spec in a.congela:
        addr, val, w = spec.split(":")
        b.cmd("freeze %s %s %s" % (addr, val, w))
    b.preludio()
    mappa0 = b.read(W_MAPPA)
    z0 = b.read(W_PZ)
    x0 = b.read(W_PX)

    # anello scorrevole di savestate: ne teniamo `anticipo`+1 e alla fine
    # promuoviamo quello giusto. `save` scrive dentro --out.
    anello = []
    trovato = None
    for i in range(a.max):
        nome = "anello-%02d.state" % (i % (a.anticipo + 1))
        b.cmd("save " + nome)
        anello.append((i, nome, b.read(W_PZ), b.read(W_MAPPA)))
        b.cmd("run 1 DOWN")
        z = b.read(W_PZ)
        if z is not None and z >= a.soglia:
            trovato = (i, z, b.read(W_MAPPA))
            break
    if trovato is None:
        b.chiudi()
        raise SystemExit("soglia Z=%d mai raggiunta in %d passi" % (a.soglia, a.max))

    i_sogl = trovato[0]
    i_vuole = max(0, i_sogl - a.anticipo)
    scelto = [r for r in anello if r[0] == i_vuole]
    if not scelto:
        b.chiudi()
        raise SystemExit("anello troppo corto")
    _, nome, z_scelto, mappa_scelto = scelto[0]
    # ricopia il savestate scelto col nome definitivo (il banco non rinomina:
    # lo facciamo sul filesystem, che e' un file opaco che non apriamo)
    src = Path(a.out) / nome
    dst = Path(a.out) / a.stato
    dst.write_bytes(src.read_bytes())

    esito = {
        "rom": str(a.rom), "sram": str(a.sram), "congela": a.congela,
        "mappa_iniziale": mappa0, "x_iniziale": x0, "z_iniziale": z0,
        "passi_fino_alla_soglia": i_sogl,
        "z_alla_soglia": trovato[1], "mappa_alla_soglia": trovato[2],
        "anticipo": a.anticipo,
        "stato_salvato": str(dst.name),
        "z_dello_stato": z_scelto, "mappa_dello_stato": mappa_scelto,
        "byte_stato": dst.stat().st_size,
    }
    b.chiudi()
    print(json.dumps(esito, indent=1))
    if a.json:
        Path(a.json).write_text(json.dumps(esito, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
