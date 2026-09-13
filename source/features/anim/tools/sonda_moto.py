#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SGP-1.2-ANIM-SOLIDO-01 — sonda del CICLO DI VITA del moto di attesa in lotta.

Risponde, con i byte e non per deduzione, alle tre domande che la matrice di
robustezza di `CRITERI.md` mette prima di tutto:

  1. **quanti lottatori** il gioco anima (un lato o tutti), e in quali lotte;
  2. **quando** il gioco ferma il moto (`StopIdleBounceAnim`) e quante volte;
  3. **che cosa il gioco ripulisce da sé** quando lo ferma — cioè quale stato
     scritto da noi resterebbe addosso allo sprite.

Indirizzi, letti dal binario della 1.1 EN (`ov012`, non compresso in RAM):

  0x02261FD4  StartIdleBounceAnim(BattlerData* r0, BattleSystem* r1)
              - esce subito se `[r0+0x198] != 0` (task già avviato)
              - esce subito se `BattleSystem_GetBattleType(r1) & 0x220`
              - scrive `degrees = 180` in `[r0+0x19C]`, avvia il SysTask con
                priorità 1010 e la funzione presa dal letterale 0x0226200C
                (**l'unico in tutta la ROM**: verificato con una scansione di
                tutti i 130 moduli), poi `[r0+0x198] = task`
              - **un solo sito di chiamata**: 0x0225DC8A
  0x02262014  StopIdleBounceAnim(BattlerData* r0)
              - se `[r0+0x198] == 0` esce
              - `SysTask_Finish`, azzera `[r0+0x198]` e `degrees`,
                e chiama `Pokepic_SetAttr(pic, 4 /*YOFFSET*/, 0)`
              - **nove siti di chiamata**: 0x02258E98 0x02259338 0x02259596
                0x0225DFBE 0x0225E00A 0x0225E0B2 0x0225E39E 0x0225E670 0x0225FC0A
  0x0226203A  l'ultima istruzione di StopIdleBounceAnim (`pop {r4,pc}`):
              fermarsi qui dà lo stato del Pokepic DOPO la pulizia del gioco.

Per ogni fermata la sonda registra: `lr` (quale dei nove siti), il puntatore al
BattlerData, il Pokepic, e la fotografia dei campi del Pokepic che il nostro
task scrive (yOffset, ombra, scala affine, posa). Il confronto fra la fotografia
a 0x02262014 e quella a 0x0226203A è la prova diretta di che cosa il gioco
ripulisce e che cosa no.

Uso:
  sonda_moto.py --hg BIN --rom ROM [--sram SAV] --script S --out DIR --json F
                [--mappa N --warp N --aggancio 0x...] [--anim 0|1]
                [--porta N] [--secondi N]

GPL-3.0-or-later.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time

QUI = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(QUI, "..", "..", "..", ".."))
sys.path.insert(0, os.path.join(REPO, "source", "features", "debug", "campo"))
from banco import (Campo, RspSicuro, RspError, warp_robusto,  # noqa: E402
                   attendi_overworld, VBLANK)

ESCA = 0x02000800          # indirizzo di ritorno fittizio per le iniezioni
START_FINE = 0x02262008    # `pop {r4,pc}` di ov12_02261FD4
START = 0x02261FD4
STOP = 0x02262014
STOP_END = 0x0226203A
TASK = 0x0226203C

OD_POKEPIC, OD_TASK, OD_DEGREES = 0x20, 0x198, 0x19C

# campi del Pokepic che il moto scrive (o che ne dipendono)
CAMPI = [("yoff", 0x2E, 2, True), ("affw", 0x34, 2, False), ("affh", 0x36, 2, False),
         ("active", 0x58, 1, False), ("step", 0x5B, 1, False),
         ("shflag", 0x6C, 2, False), ("sh_h", 0x6E, 1, True),
         ("sh_x", 0x70, 2, True), ("sh_y", 0x72, 2, True),
         ("sh_xoff", 0x74, 2, True), ("sh_yoff", 0x76, 2, True)]

CHUNK_ANIM = 0x023D8716
STATO_ANIM = 0x023D8E40          # SgpAnim2State (64 B); hits a +0x04
SLOT_ANIM = 0x023D8E80           # 4 x SgpAnim2Slot da 32 B


def s(v, bits):
    m = 1 << bits
    return v - m if v >= m // 2 else v


def foto(g, pic):
    """Fotografia dei campi del Pokepic, in una sola lettura di memoria."""
    if not pic:
        return None
    b = g.mem(pic, 0x80)
    out = {}
    for nome, off, ln, segno in CAMPI:
        v = int.from_bytes(b[off:off + ln], "little")
        out[nome] = s(v, ln * 8) if segno else v
    return out


def stato_anim(g):
    try:
        b = g.mem(STATO_ANIM, 0x40)
    except (RspError, OSError):
        return None
    w = lambda o: int.from_bytes(b[o:o + 4], "little")   # noqa: E731
    return {"flags": b[0], "guard": b[1], "ampiezza": b[2], "rr": b[3],
            "hits": w(4), "hits_on": w(8), "hits_busy": w(0x0C),
            "last_y": s(int.from_bytes(b[0x10:0x12], "little"), 16),
            "last_step": b[0x12], "last_idx": b[0x13],
            "blinks": w(0x14), "rari": w(0x18),
            "last_s76": s(int.from_bytes(b[0x1C:0x1E], "little"), 16),
            "last_cls": b[0x1E], "last_slot": b[0x1F]}


def slot_anim(g):
    try:
        b = g.mem(SLOT_ANIM, 0x80)
    except (RspError, OSError):
        return None
    fuori = []
    for i in range(4):
        v = b[i * 32:(i + 1) * 32]
        w = lambda o: int.from_bytes(v[o:o + 4], "little")   # noqa: E731
        fuori.append({"i": i, "od": f"0x{w(0):08X}", "pic": f"0x{w(4):08X}",
                      "rng": f"0x{w(8):08X}",
                      "base76": s(int.from_bytes(v[0x0C:0x0E], "little"), 16),
                      "last76": s(int.from_bytes(v[0x0E:0x10], "little"), 16),
                      "blink_left": v[0x10], "blink_wait": v[0x11],
                      "blink_cnt": v[0x12], "usato": v[0x13]})
    return fuori


def forza_avversario(g, od_nostro, battle_system, passo, od_avv):
    """Inietta `ov12_02261FD4(od_avversario, battleSystem)` — la STESSA
    funzione che il gioco chiama per il lottatore del giocatore. Non tocca la
    ROM: e' una forzatura del banco, dichiarata, che serve a mettere sotto il
    nostro codice anche gli sprite di FRONTE.

    La CPU e' ferma sul breakpoint di `ov12_02261FD4`: si salvano i registri,
    si mette `lr` su un'esca, si salta alla funzione, si aspetta l'esca e si
    rimette tutto com'era — lo stesso schema del warp di `SGP-1.2-CHIUSURA-01`.
    """
    if not od_avv:
        od_avv = od_nostro + 0x240      # ripiego: il passo fra due OpponentData
    od_avv = int(str(od_avv), 0) if isinstance(od_avv, str) else od_avv
    # PRIMA si lascia finire la chiamata vera del gioco (siamo fermi sull'ENTRATA
    # di ov12_02261FD4: dirottare il PC qui vorrebbe dire perdere l'avvio del
    # lottatore del giocatore). Ci si rimette sul `pop` finale.
    g.add_bkpt(START_FINE, 2)
    st = g.cont(attesa=30)
    if not (st.startswith("S05") and g.regs()["pc"] == START_FINE):
        g.del_bkpt(START_FINE, 2)
        passo("avversario NON forzato", motivo="mai arrivati alla fine di Start")
        return {"riuscita": False, "motivo": "fine di Start non raggiunta"}
    g.del_bkpt(START_FINE, 2)
    salvati = g.regs()
    g.add_bkpt(ESCA, 2)
    g.set_reg(0, od_avv & 0xFFFFFFFF)
    g.set_reg(1, battle_system & 0xFFFFFFFF)
    g.set_reg(14, ESCA | 1)
    g.set_reg(15, START | 1)
    st = g.cont(attesa=30)
    esito = {"od_avversario": f"0x{od_avv:08X}",
             "battle_system": f"0x{battle_system:08X}", "fermata": st}
    if st.startswith("S05") and g.regs()["pc"] == ESCA:
        esito["task_creato"] = f"0x{g.u32(od_avv + OD_TASK):08X}"
        esito["riuscita"] = g.u32(od_avv + OD_TASK) != 0
    else:
        esito["riuscita"] = False
    for i, nome in enumerate(["r0", "r1", "r2", "r3", "r4", "r5", "r6", "r7", "r8",
                              "r9", "r10", "r11", "r12", "sp", "lr", "pc", "cpsr"]):
        if nome != "pc":
            g.set_reg(i, salvati[nome])
    g.set_reg(15, salvati["pc"] | (1 if salvati["cpsr"] & 0x20 else 0))
    g.del_bkpt(ESCA, 2)
    passo("avversario forzato", **esito)
    return esito


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hg", required=True)
    ap.add_argument("--rom", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--script", required=True)
    ap.add_argument("--sram")
    ap.add_argument("--mappa", type=int, default=0)
    ap.add_argument("--warp", type=int, default=0)
    ap.add_argument("--aggancio", default="0x0205C692")
    ap.add_argument("--fotogramma", type=int, default=0)
    ap.add_argument("--anim", type=int, default=-1,
                    help="se 0/1 scrive l'interruttore 0x023D8716 prima del warp")
    ap.add_argument("--porta", type=int, default=3333)
    ap.add_argument("--json", required=True)
    ap.add_argument("--secondi", type=float, default=300.0)
    ap.add_argument("--max-eventi", type=int, default=400)
    ap.add_argument("--anima-avversario", action="store_true",
                    help="FORZATURA DI BANCO, non una modifica della ROM: dopo che "
                         "il gioco ha avviato il moto sul lottatore del giocatore, "
                         "inietta la STESSA chiamata del gioco "
                         "(ov12_02261FD4) anche sull'OpponentData dell'avversario. "
                         "Serve a provare il nostro codice su sprite di FRONTE "
                         "(quelli alti e larghi), che HGSS non anima mai da se'.")
    a = ap.parse_args()

    os.makedirs(a.out, exist_ok=True)
    cmd = [a.hg, "--rom", a.rom, "--out", a.out, "--gdb-port", str(a.porta),
           "--script", a.script]
    if a.sram:
        cmd += ["--sram", a.sram]
    t0 = time.time()
    proc = subprocess.Popen(cmd, stdout=open(os.path.join(a.out, "hg-stdout.log"), "w"),
                            stderr=open(os.path.join(a.out, "hg-stderr.log"), "w"))
    E = {"comando": cmd, "anim_richiesto": a.anim, "eventi": [], "passi": [],
         "conteggi": {"start": 0, "start_effettivi": 0, "stop": 0,
                      "stop_effettivi": 0, "stop_end": 0}}

    def passo(nome, **kw):
        kw["passo"] = nome
        kw["t"] = round(time.time() - t0, 2)
        E["passi"].append(kw)
        print("[%7.2f] %s: %s" % (kw["t"], nome,
              " ".join("%s=%s" % (k, v) for k, v in kw.items()
                       if k not in ("t", "passo"))), file=sys.stderr, flush=True)

    try:
        g = RspSicuro(port=a.porta)
        g.cont_nowait()
        c = Campo(g)

        def prima_del_warp(gg, cc, st):
            if a.anim >= 0:
                gg.write_mem(CHUNK_ANIM, bytes([a.anim & 1]))
                passo("interruttore scritto", anim=gg.mem(CHUNK_ANIM, 1)[0])

        if a.mappa:
            E["warp"] = warp_robusto(g, c, a.mappa, a.warp, aggancio=a.aggancio,
                                     fotogramma=a.fotogramma, passo=passo,
                                     su_overworld=prima_del_warp)
            if not E["warp"].get("assestata"):
                raise RspError("warp non assestato")
        else:
            attendi_overworld(c, secondi=150.0)
            if a.anim >= 0:
                g.write_mem(CHUNK_ANIM, bytes([a.anim & 1]))
            passo("overworld raggiunto", anim=g.mem(CHUNK_ANIM, 1)[0])

        for bp in (START, STOP, STOP_END):
            g.add_bkpt(bp, 2)
        g.cont_nowait()

        pendenti = {}
        scadenza = time.time() + a.secondi
        while time.time() < scadenza and len(E["eventi"]) < a.max_eventi:
            try:
                st = g.attendi_fermata(attesa=min(15.0,
                                                  max(1.0, scadenza - time.time())))
            except (RspError, OSError):
                if proc.poll() is not None:
                    break
                continue
            if not st.startswith("S05"):
                continue
            try:
                r = g.regs()
                pc = r["pc"]
                vb = g.u32(VBLANK)
                if pc == START:
                    od = r["r0"]
                    pic = g.u32(od + OD_POKEPIC) if od else 0
                    gia = g.u32(od + OD_TASK) if od else 0
                    ev = {"tipo": "start", "vblank": vb, "lr": f"0x{r['lr']:08X}",
                          "od": f"0x{od:08X}", "pic": f"0x{pic:08X}",
                          "task_prima": f"0x{gia:08X}",
                          "effettivo": gia == 0, "pokepic": foto(g, pic)}
                    E["conteggi"]["start"] += 1
                    if gia == 0:
                        E["conteggi"]["start_effettivi"] += 1
                    if a.anima_avversario and gia == 0 and od:
                        E["forzatura"] = forza_avversario(g, od, r["r1"], passo,
                                                          E.get("od_avversario"))
                elif pc == STOP:
                    od = r["r0"]
                    pic = g.u32(od + OD_POKEPIC) if od else 0
                    task = g.u32(od + OD_TASK) if od else 0
                    ev = {"tipo": "stop", "vblank": vb, "lr": f"0x{r['lr']:08X}",
                          "od": f"0x{od:08X}", "pic": f"0x{pic:08X}",
                          "task": f"0x{task:08X}", "effettivo": task != 0,
                          "pokepic_prima": foto(g, pic)}
                    E["conteggi"]["stop"] += 1
                    if task != 0:
                        E["conteggi"]["stop_effettivi"] += 1
                    if task == 0 and E.get("od_avversario") is None:
                        # il primo `stop` a vuoto della lotta e' quello
                        # dell'avversario: e' il modo piu' semplice per avere il
                        # suo OpponentData senza cablare un offset
                        E["od_avversario"] = od
                    pendenti[od] = ev
                else:  # STOP_END
                    od = r["r4"]
                    pic = g.u32(od + OD_POKEPIC) if od else 0
                    ev = {"tipo": "stop_fine", "vblank": vb, "od": f"0x{od:08X}",
                          "pic": f"0x{pic:08X}", "pokepic_dopo": foto(g, pic)}
                    E["conteggi"]["stop_end"] += 1
                    prec = pendenti.pop(od, None)
                    if prec is not None:
                        prec["pokepic_dopo"] = ev["pokepic_dopo"]
                        ev["abbinato"] = True
                ev["stato_anim"] = stato_anim(g)
                E["eventi"].append(ev)
            except (RspError, OSError):
                break
            try:
                g.cont_nowait()
            except (RspError, OSError):
                break
            if proc.poll() is not None:
                break

        try:
            E["stato_finale"] = stato_anim(g)
            E["slot_finali"] = slot_anim(g)
            E["vblank_finale"] = g.u32(VBLANK)
        except (RspError, OSError):
            pass
        E["fine"] = "ok"
    except (RspError, OSError) as e:
        E["fine"] = "%s: %s" % (type(e).__name__, e)
        passo("errore", errore=E["fine"])
    try:
        E["rc"] = proc.wait(timeout=400)
    except subprocess.TimeoutExpired:
        proc.kill()
        E["rc"] = "ucciso"
    E["secondi"] = round(time.time() - t0, 2)

    # sintesi: quanti BattlerData distinti hanno ricevuto il task
    od_animati = sorted({e["od"] for e in E["eventi"]
                         if e["tipo"] == "start" and e.get("effettivo")})
    E["battler_animati"] = od_animati
    E["n_battler_animati"] = len(od_animati)
    E["siti_stop"] = {}
    for e in E["eventi"]:
        if e["tipo"] == "stop":
            k = e["lr"]
            E["siti_stop"].setdefault(k, {"totali": 0, "effettivi": 0})
            E["siti_stop"][k]["totali"] += 1
            if e.get("effettivo"):
                E["siti_stop"][k]["effettivi"] += 1

    with open(a.json, "w") as f:
        json.dump(E, f, indent=2, ensure_ascii=False)
    print(json.dumps({k: v for k, v in E.items() if k not in ("passi", "eventi")},
                     indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
