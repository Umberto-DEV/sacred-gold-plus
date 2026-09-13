#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""O3 (P15) — warp robusto + lotta allenatore + lettura dei livelli AL GANCIO.

Il gancio allenatori di D1 (`SGP-1.2-PLUS-01`/`PLUS-03`) e' una trampolina:
  0x023D82E6  dopo `ldrh r2,[r2,#2]`  -> r2 = livello NATIVO del record TRPOKE
  0x023D82FE  su `adds r2,r0,#0`      -> r0 = livello EFFETTIVO passato a CreateMon
Lo stato del blocco sta a 0x023D8700: `active_plus`, `active_wild`, e i contatori
`hits_trainer`/`hits_wild`.

Differenza rispetto a `SGP-1.2-PLUS-03/tools/livelli.py`:
  * il warp e' quello ROBUSTO di `banco.py` (attesa sullo stato, non sul tempo);
  * `active_plus/active_wild` si scrivono **prima** del warp (mandato) e si rileggono
    dopo, cosi' si vede se il warp li ha toccati;
  * si conta esplicitamente quante volte il gancio scatta: zero scatti = prova ROSSA,
    anche se a schermo si vedesse una lotta.

Uso:
  lotta_allenatore.py --hg BIN --rom ROM --sram SAV --script S --out DIR --json F
                      [--mappa 253] [--plus 0|1] [--secondi 200]
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time

QUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, QUI)
from banco import (Campo, RspSicuro, RspError, STATO_PLUS, warp_robusto,  # noqa: E402
                   stato_plus, attendi_overworld, leggibile)

TRN_PRE, TRN_POST = 0x023D82E6, 0x023D82FE
WLD_PRE, WLD_POST = 0x023D8346, 0x023D834C


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hg", required=True)
    ap.add_argument("--rom", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--script", required=True)
    ap.add_argument("--sram")
    ap.add_argument("--mappa", type=int, default=0)
    ap.add_argument("--warp", type=int, default=0)
    ap.add_argument("--plus", type=int, default=0)
    ap.add_argument("--porta", type=int, default=3333)
    ap.add_argument("--json", required=True)
    ap.add_argument("--secondi", type=float, default=220.0)
    ap.add_argument("--fotogramma", type=int, default=3600,
                    help="fotogramma di gioco dell iniezione del warp")
    ap.add_argument("--aggancio", default="0x0205C692",
                    help="dato = corsa deterministica in fotogrammi (vedi banco.py)")
    a = ap.parse_args()

    os.makedirs(a.out, exist_ok=True)
    cmd = [a.hg, "--rom", a.rom, "--out", a.out, "--gdb-port", str(a.porta),
           "--script", a.script]
    if a.sram:
        cmd += ["--sram", a.sram]
    t0 = time.time()
    proc = subprocess.Popen(cmd, stdout=open(os.path.join(a.out, "hg-stdout.log"), "w"),
                            stderr=open(os.path.join(a.out, "hg-stderr.log"), "w"))
    esito = {"comando": cmd, "plus_richiesto": a.plus, "mappa": a.mappa,
             "passi": [], "trainer": [], "wild": []}

    def passo(nome, **kw):
        kw["passo"] = nome
        kw["t"] = round(time.time() - t0, 2)
        esito["passi"].append(kw)
        print("[%7.2f] %s: %s" % (kw["t"], nome,
              " ".join("%s=%s" % (k, v) for k, v in kw.items()
                       if k not in ("t", "passo"))), file=sys.stderr, flush=True)

    try:
        g = RspSicuro(port=a.porta)
        g.cont_nowait()
        c = Campo(g)

        # 1. stato del blocco scritto PRIMA del warp (mandato), da CPU ferma sul
        #    ciclo di campo: la scrittura non consuma fotogrammi.
        def prima_del_warp(gg, cc, s):
            gg.write_mem(STATO_PLUS, bytes([a.plus & 1, a.plus & 1]))
            esito["stato_prima_del_warp"] = stato_plus(gg)
            passo("stato scritto prima del warp", **esito["stato_prima_del_warp"])

        # 2. warp robusto
        if a.mappa:
            esito["warp"] = warp_robusto(g, c, a.mappa, a.warp, aggancio=a.aggancio,
                                         fotogramma=a.fotogramma,
                                         passo=passo, su_overworld=prima_del_warp)
            if not esito["warp"].get("assestata"):
                raise RspError("warp non assestato: la prova non parte")
        else:
            attendi_overworld(c, secondi=120.0)
            g.write_mem(STATO_PLUS, bytes([a.plus & 1, a.plus & 1]))
            esito["stato_prima_del_warp"] = stato_plus(g)
            passo("stato scritto (senza warp)", **esito["stato_prima_del_warp"])
        esito["stato_dopo_il_warp"] = stato_plus(g)
        passo("stato dopo il warp", **esito["stato_dopo_il_warp"])

        # 3. ganci armati, il copione cammina e preme A
        for bp in (TRN_PRE, TRN_POST, WLD_PRE, WLD_POST):
            g.add_bkpt(bp, 2)
        g.cont_nowait()
        scadenza = time.time() + a.secondi
        base_trn = base_wld = None
        scatti = {"TRN_PRE": 0, "TRN_POST": 0, "WLD_PRE": 0, "WLD_POST": 0, "altri": 0}
        while time.time() < scadenza:
            try:
                st = g.attendi_fermata(attesa=min(20.0, max(1.0, scadenza - time.time())))
            except (RspError, OSError):
                # Un timeout di lettura NON e' un errore: vuol dire solo che in quella
                # finestra il gancio non e' scattato. Trattarlo come fatale (prima
                # stesura di questo copione) fa smettere di ascoltare il client mentre
                # il banco e' ancora vivo: quando poi il breakpoint scatta davvero,
                # `Enter(stay=true)` ferma la CPU e NESSUNO la fa ripartire — il banco
                # resta congelato sullo stesso fotogramma. E' successo, ed e' la stessa
                # famiglia di errore di D4/D5 (CPU ferma che nessuno riprende).
                if proc.poll() is not None:
                    break
                continue
            if not st.startswith("S05"):
                continue
            try:
                r = g.regs()
            except (RspError, OSError):
                break
            pc = r["pc"]
            if pc == TRN_PRE:
                scatti["TRN_PRE"] += 1
                base_trn = r["r2"] & 0xFFFF
            elif pc == TRN_POST:
                scatti["TRN_POST"] += 1
                esito["trainer"].append({"base": base_trn, "effettivo": r["r0"] & 0xFF})
                passo("gancio allenatore", base=base_trn, effettivo=r["r0"] & 0xFF)
            elif pc == WLD_PRE:
                scatti["WLD_PRE"] += 1
                base_wld = r["r7"] & 0xFF
            elif pc == WLD_POST:
                scatti["WLD_POST"] += 1
                esito["wild"].append({"base": base_wld, "effettivo": r["r0"] & 0xFF})
                passo("gancio selvatici", base=base_wld, effettivo=r["r0"] & 0xFF)
            else:
                scatti["altri"] += 1
            try:
                g.cont_nowait()
            except (RspError, OSError):
                break
            if proc.poll() is not None:
                break
        esito["scatti_gancio"] = scatti
        try:
            esito["stato_finale"] = stato_plus(g)
        except (RspError, OSError):
            esito["stato_finale"] = None
        esito["fine_sessione"] = "ok"
    except (RspError, OSError) as e:
        esito["fine_sessione"] = "%s: %s" % (type(e).__name__, e)
        passo("errore", errore=esito["fine_sessione"])
    try:
        esito["rc_hg_runtime"] = proc.wait(timeout=300)
    except subprocess.TimeoutExpired:
        proc.kill()
        esito["rc_hg_runtime"] = "ucciso dopo 300 s"
    esito["secondi"] = round(time.time() - t0, 2)
    with open(a.json, "w") as f:
        json.dump(esito, f, indent=2, ensure_ascii=False)
    print(json.dumps({k: v for k, v in esito.items() if k != "passi"}, indent=2,
                     ensure_ascii=False))
    return 0 if esito.get("trainer") else 1


if __name__ == "__main__":
    sys.exit(main())
