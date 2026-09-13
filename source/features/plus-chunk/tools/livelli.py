#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SGP-1.2-PLUS-03 — legge i livelli avversari AL GANCIO, con il gdbstub.

Il gancio allenatori di D1 è una trampolina: la prima istruzione carica il
livello NATIVO del record TRPOKE, l'ultima mette in r2 il livello EFFETTIVO che
va a `CreateMon`. Mettendo un breakpoint su due indirizzi noti si leggono i due
numeri per ogni membro del gruppo, **con la stessa tecnica a PLUS spento e a
PLUS acceso**: così i sei livelli nativi e i sei livelli PLUS vengono dallo
stesso strumento e sono confrontabili.

    0x023D82E6  subito dopo `ldrh r2,[r2,#2]`  ->  r2 = livello BASE
    0x023D82FE  su `adds r2,r0,#0`             ->  r0 = livello EFFETTIVO
    0x023D8346  gancio selvatici, su `adds r0,r7,#0` -> r7 = livello BASE
    0x023D834C  gancio selvatici, su `adds r7,r0,#0` -> r0 = livello EFFETTIVO

Fa anche il warp (stessa procedura di SGP-1.2-RUNTIME-02/tools/warp.py: si
chiama `sub_02053E08(fieldSystem, mapId, warpId)`, cioè la funzione che il gioco
usa per i pannelli-warp) quando `--mappa` è dato.

Uso:
  livelli.py --hg BIN --rom ROM --sram SAV --script S --out DIR --json F
             [--mappa 135] [--plus 1] [--aggancio 0x0205C692] [--fotogramma 3400]
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time

QUI = os.path.dirname(os.path.abspath(__file__))
SOURCE = os.path.abspath(os.path.join(QUI, "..", "..", ".."))
sys.path.insert(0, os.path.join(SOURCE, "features", "debug", "tools"))
from rsp import Rsp, RspError  # noqa: E402

FIELDSYS_PTR = 0x0203E304
SUB_02053E08 = 0x02053E08
ESCA = 0x02000800
VBLANK = 0x021D1138
STATO = 0x023D8700

TRN_PRE, TRN_POST = 0x023D82E6, 0x023D82FE
WLD_PRE, WLD_POST = 0x023D8346, 0x023D834C
REG_ORDER = ["r0", "r1", "r2", "r3", "r4", "r5", "r6", "r7", "r8", "r9", "r10",
             "r11", "r12", "sp", "lr", "pc", "cpsr"]


def stato(g):
    b = g.mem(STATO, 32)
    return {"active_plus": b[0], "active_wild": b[1], "cap": b[2],
            "load_status": b[3], "guard": b[4],
            "hits_trainer": int.from_bytes(b[8:12], "little"),
            "hits_wild": int.from_bytes(b[12:16], "little"),
            "chunk": b[16:32].hex()}


def campo(g, ptr):
    fs = g.u32(ptr)
    if not fs:
        return {"fs": 0}
    b = g.mem(fs, 0x70)
    w = lambda o: int.from_bytes(b[o:o + 4], "little")     # noqa: E731
    pm = w(0)
    s = {"fs": fs, "taskman": w(0x10), "location": w(0x20),
         "runningFieldMap": w(0x6C),
         "isPaused": g.u32(pm + 8) if pm else None}
    if s["location"]:
        d = g.mem(s["location"], 20)
        s["mapId"], s["warpId"], s["x"], s["z"], s["dir"] = [
            int.from_bytes(d[i:i + 4], "little", signed=True) for i in range(0, 20, 4)]
    return s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hg", required=True)
    ap.add_argument("--rom", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--script", required=True)
    ap.add_argument("--sram")
    ap.add_argument("--load")
    ap.add_argument("--mappa", type=int, default=0)
    ap.add_argument("--warp", type=int, default=0)
    ap.add_argument("--plus", type=int, default=0, help="1 = accende PLUS in RAM")
    ap.add_argument("--porta", type=int, default=3333)
    ap.add_argument("--json", required=True)
    ap.add_argument("--aggancio", default="0x0205C692")
    ap.add_argument("--fotogramma", type=int, default=3400)
    ap.add_argument("--attesa-prologo", type=float, default=25.0)
    ap.add_argument("--gia-in-overworld", action="store_true",
                    help="con --load: il banco parte gia' in overworld e fermo. "
                         "Non lo si lascia correre prima di iniettare: altrimenti "
                         "con --load macina migliaia di fotogrammi al secondo e il "
                         "copione finisce prima che il client si sia agganciato.")
    ap.add_argument("--secondi", type=float, default=240.0,
                    help="quanto stare in ascolto dei breakpoint")
    a = ap.parse_args()

    os.makedirs(a.out, exist_ok=True)
    cmd = [a.hg, "--rom", a.rom, "--out", a.out, "--gdb-port", str(a.porta),
           "--script", a.script]
    if a.sram:
        cmd += ["--sram", a.sram]
    if a.load:
        cmd += ["--load", a.load]
    log = open(os.path.join(a.out, "hg-stdout.log"), "w")
    err = open(os.path.join(a.out, "hg-stderr.log"), "w")
    t0 = time.time()
    proc = subprocess.Popen(cmd, stdout=log, stderr=err)
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
        g = Rsp(port=a.porta)
        if not a.gia_in_overworld:
            g.cont_nowait()
            time.sleep(a.attesa_prologo)
        ptr = g.u32(FIELDSYS_PTR)
        esito["stato_iniziale"] = stato(g)
        passo("stato all'avvio", **esito["stato_iniziale"])

        if a.mappa:
            for _ in range(200):
                s = campo(g, ptr)
                if s.get("fs") and s.get("taskman") == 0 and s.get("runningFieldMap") == 1 \
                        and s.get("isPaused") == 0:
                    break
            esito["prima"] = s
            passo("overworld fermo", mapId=s.get("mapId"), x=s.get("x"), z=s.get("z"))
            for _ in range(20000):
                if g.u32(VBLANK) >= a.fotogramma:
                    break
            aggancio = int(a.aggancio, 0) & ~1
            g.add_bkpt(aggancio, 2)
            st = (g.cont(attesa=120) if a.gia_in_overworld
                  else g.attendi_fermata(attesa=120))
            if not st.startswith("S05"):
                raise RspError("aggancio: fermata inattesa %r" % st)
            salvati = g.regs()
            g.add_bkpt(ESCA, 2)
            fs = g.u32(ptr)
            g.set_reg(0, fs)
            g.set_reg(1, a.mappa)
            g.set_reg(2, a.warp)
            g.set_reg(14, ESCA | 1)
            g.set_reg(15, SUB_02053E08 | 1)
            st = g.cont(attesa=60)
            if not st.startswith("S05"):
                raise RspError("esca: fermata inattesa %r" % st)
            for i, nome in enumerate(REG_ORDER):
                if nome != "pc":
                    g.set_reg(i, salvati[nome])
            g.set_reg(15, salvati["pc"] | (1 if salvati["cpsr"] & 0x20 else 0))
            g.del_bkpt(ESCA, 2)
            g.del_bkpt(aggancio, 2)
            g.cont_nowait()
            for _ in range(400):
                s = campo(g, ptr)
                if s.get("mapId") == a.mappa:
                    break
            esito["dopo_warp"] = s
            esito["mappa_raggiunta"] = s.get("mapId") == a.mappa
            passo("warp", mappa=s.get("mapId"), raggiunta=esito["mappa_raggiunta"],
                  x=s.get("x"), z=s.get("z"))

        # PLUS acceso/spento, scritto in RAM PRIMA che la squadra venga creata
        g.write_mem(STATO, bytes([a.plus & 1, a.plus & 1]))
        esito["stato_prima_dei_breakpoint"] = stato(g)
        passo("stato impostato", **esito["stato_prima_dei_breakpoint"])

        for bp in (TRN_PRE, TRN_POST, WLD_PRE, WLD_POST):
            g.add_bkpt(bp, 2)
        g.cont_nowait()
        scadenza = time.time() + a.secondi
        base_corrente = None
        base_wild = None
        while time.time() < scadenza:
            try:
                st = g.attendi_fermata(attesa=min(20, max(1, scadenza - time.time())))
            except RspError:
                continue
            if not st.startswith("S05"):
                continue
            r = g.regs()
            pc = r["pc"]
            if pc == TRN_PRE:
                base_corrente = r["r2"] & 0xFFFF
            elif pc == TRN_POST:
                esito["trainer"].append({"base": base_corrente, "effettivo": r["r0"] & 0xFF})
                passo("gancio allenatore", base=base_corrente, effettivo=r["r0"] & 0xFF)
            elif pc == WLD_PRE:
                base_wild = r["r7"] & 0xFF
            elif pc == WLD_POST:
                esito["wild"].append({"base": base_wild, "effettivo": r["r0"] & 0xFF})
                passo("gancio selvatici", base=base_wild, effettivo=r["r0"] & 0xFF)
            g.cont_nowait()
        esito["stato_finale"] = stato(g)
        esito["fine_sessione"] = "ok"
    except (RspError, OSError) as e:
        esito["fine_sessione"] = "%s: %s" % (type(e).__name__, e)
    try:
        rc = proc.wait(timeout=300)
    except subprocess.TimeoutExpired:
        proc.kill()
        rc = "ucciso dopo 300 s"
    esito["rc_hg_runtime"] = rc
    esito["secondi"] = round(time.time() - t0, 2)
    with open(a.json, "w") as f:
        json.dump(esito, f, indent=2, ensure_ascii=False)
    print(json.dumps({k: v for k, v in esito.items() if k != "passi"}, indent=2,
                     ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
