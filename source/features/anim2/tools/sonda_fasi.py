#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SGP-1.2.1-ANIM-FASI-01 — sonda dei siti di Start/Stop del moto di riposo.

Osserva (e, se richiesto, sopprime) le chiamate a `StopIdleBounceAnim`
(`ov12_02262014`) e a `StartIdleBounceAnim` (`ov12_02261FD4`) durante una lotta,
distinguendo i **nove siti** di chiamata dall'indirizzo di ritorno (`lr`).

I nove siti, con il nome ricavato dal disassemblato HGSS e dalla decompilazione
`pret/pokeplatinum` (confermati negli overlay EN e IT):

    0x02258E98  BattlerData_Delete            distruzione del lottatore
    0x02259338  BtlIOCmd_StopGaugeAnimation   ogni turno, 4 V-blank dopo la conferma
    0x02259596  BtlIOCmd_ClearTouchScreen     smontaggio dell'interfaccia bassa
    0x0225DFBE  BORSA                         Task_SetCommandSelection stato 6 case 2
    0x0225E00A  SQUADRA                       Task_SetCommandSelection stato 6 case 3
    0x0225E0B2  SAFARI/PARCO                  Task_SetCommandSelection stato 7
    0x0225E39E  CONFERMA-MOSSA                Task_ShowMoveSelectMenu stato 2
    0x0225E670  BERSAGLIO                     Task_ShowTargetSelectMenu stato 2
    0x0225FC0A  SI-NO                         Task_ShowYesNoMenu stato 3

Gli indirizzi valgono **identici per EN e IT**: gli overlay dei due binari sono
byte-identici nei punti osservati.

Politiche (`--politica`):

    nessuna  osserva e basta (corsa di riferimento)
    E2       sopprime i due stop BORSA e SQUADRA (Opzione 1)
    E4       sopprime anche CONFERMA-MOSSA, BERSAGLIO e SI-NO (Opzione 2)
    E4b      sopprime anche BtlIOCmd_StopGaugeAnimation

Sopprimere = al breakpoint in **testa** a `StopIdleBounceAnim` si mette
`pc = lr & ~1`, cioe' si fa ritornare subito la funzione senza eseguirne il
corpo. E' una forzatura **di banco**, non una modifica della ROM.

`--anima-avversario` riproduce l'Opzione 1b: al `pop` finale di
`StartIdleBounceAnim` inietta la stessa chiamata sul `BattlerData` del lottatore
avversario, cosi' che i due task del moto girino insieme.

`--siti-finti` e' la prova R6 del §6.3: a CPU ferma mette `pc` **sull'istruzione
`bl` di ciascuno dei nove siti**, uno alla volta, dopo aver riacceso il moto e
avergli fatto fare qualche giro. Cosi' `lr` lo calcola il processore e vale
davvero `sito + 5`, e si vede l'effetto della fermata sui campi del `Pokepic`.
Serve per i siti che una lotta selvatica non fa mai scattare.

`--gancio-task` e `--forza-subito`/`--siti-finti` puntano di default alla testa
di `sgp_idle_task5` (blocco v5c, simbolo in
`source/sgp12/build/anim2/manifesto.json`, bit Thumb tolto). Il vecchio blocco
v4 (`0x023D8BE4`) e' codice storico, morto dopo il passaggio ad anim2: un
breakpoint li' non scatta mai in una lotta reale.

Uso:
    sonda_fasi.py --hg BIN --rom ROM [--sram SAV] --out DIR --script S --json F
                  [--politica nessuna|E2|E4|E4b] [--anima-avversario]
                  [--porta N] [--secondi N] [--max-eventi N]
                  [--forza-subito] [--siti-finti --giri-prima N]
                  [--bs 0x... --gancio-task 0x...]

Il copione (`--script`) si genera con `copioni.py`, che sta accanto a questo
file. La sonda non conosce le coordinate del menu: quelle stanno nel copione.

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
REPO = os.environ.get("SGP_REPO") or os.path.abspath(
    os.path.join(QUI, "..", "..", "..", ".."))
sys.path.insert(0, os.path.join(REPO, "source", "features", "debug", "tools"))
from rsp import Rsp, RspError  # noqa: E402

VBLANK = 0x021D1138        # contatore di V-blank del gioco
ESCA = 0x02000800          # indirizzo di ritorno fittizio per le iniezioni
START = 0x02261FD4         # ov12_02261FD4  StartIdleBounceAnim
START_FINE = 0x02262008    # `pop {r4,pc}` di StartIdleBounceAnim
STOP = 0x02262014          # ov12_02262014  StopIdleBounceAnim
STOP_END = 0x0226203A      # `pop` finale di StopIdleBounceAnim
HITS = 0x023DBBA4          # contatore di giri del task del moto (blocco v5)
HITS_ON = 0x023DBBA8       # giri con la funzione accesa
OD_POKEPIC, OD_TASK, OD_DEGREES = 0x20, 0x198, 0x19C

GET_MAX_BATTLERS = 0x0223A7F0   # BattleSystem_GetMaxBattlers
GET_BATTLER_DATA = 0x0223A7E8   # BattleSystem_GetBattlerData

SITI = {
    0x02258E98: "DISTRUZIONE",
    0x02259338: "IO-BARRA",
    0x02259596: "IO-SCHERMO-BASSO",
    0x0225DFBE: "BORSA",
    0x0225E00A: "SQUADRA",
    0x0225E0B2: "SAFARI",
    0x0225E39E: "CONFERMA-MOSSA",
    0x0225E670: "BERSAGLIO",
    0x0225FC0A: "SI-NO",
}

POLITICHE = {
    "nessuna": set(),
    "E2": {0x0225DFBE, 0x0225E00A},
    "E4": {0x0225DFBE, 0x0225E00A, 0x0225E39E, 0x0225E670, 0x0225FC0A},
    "E4b": {0x0225DFBE, 0x0225E00A, 0x0225E39E, 0x0225E670, 0x0225FC0A,
            0x02259338},
}

# campi del Pokepic che il moto scrive (o che ne dipendono), cfr. §2.1.0
CAMPI = [("yoff", 0x2E, 2, True), ("affw", 0x34, 2, False),
         ("affh", 0x36, 2, False), ("active", 0x58, 1, False),
         ("step", 0x5B, 1, False)]

REG_ORDER = ["r0", "r1", "r2", "r3", "r4", "r5", "r6", "r7", "r8", "r9", "r10",
             "r11", "r12", "sp", "lr", "pc", "cpsr"]


class RspSicuro(Rsp):
    """Rsp con una pausa dopo il `cont`: senza, lo stub perde fermate vicine."""

    pausa_cont = 0.02

    def cont_nowait(self):
        super().cont_nowait()
        time.sleep(self.pausa_cont)


def con_segno(v, bits):
    m = 1 << bits
    return v - m if v >= m // 2 else v


def chiama(g, fn, *argomenti):
    """Chiama `fn` nel gioco con la CPU ferma, e rimette i registri com'erano."""
    salvati = g.regs()
    g.add_bkpt(ESCA, 2)
    for i, v in enumerate(argomenti):
        g.set_reg(i, v & 0xFFFFFFFF)
    g.set_reg(14, ESCA | 1)
    g.set_reg(15, fn | 1)
    st = g.cont(attesa=30)
    ris = g.reg(0) if st.startswith("S05") and g.regs()["pc"] == ESCA else None
    ripristina(g, salvati)
    g.del_bkpt(ESCA, 2)
    return ris


def ripristina(g, salvati):
    for i, nome in enumerate(REG_ORDER):
        if nome != "pc":
            g.set_reg(i, salvati[nome])
    g.set_reg(15, salvati["pc"] | (1 if salvati["cpsr"] & 0x20 else 0))


def scopri_lottatori(g, bs):
    """BattleSystem_GetMaxBattlers + GetBattlerData per ogni indice."""
    n = chiama(g, GET_MAX_BATTLERS, bs)
    fuori = {"max_battlers": n, "lottatori": []}
    if not n or n > 8:
        return fuori
    for i in range(n):
        od = chiama(g, GET_BATTLER_DATA, bs, i)
        pic = g.u32(od + OD_POKEPIC) if od else 0
        fuori["lottatori"].append({"i": i, "od": "0x%08X" % (od or 0),
                                   "pic": "0x%08X" % pic,
                                   "task": "0x%08X" % (g.u32(od + OD_TASK)
                                                       if od else 0)})
    return fuori


def foto(g, pic):
    """I cinque campi del Pokepic che raccontano lo stato dello sprite."""
    if not pic:
        return None
    try:
        b = g.mem(pic, 0x80)
    except (RspError, OSError):
        return None
    return {n: (con_segno(int.from_bytes(b[o:o + l], "little"), l * 8) if sg
                else int.from_bytes(b[o:o + l], "little"))
            for n, o, l, sg in CAMPI}


def forza(g, bs, E):
    """Inietta `StartIdleBounceAnim(od_avversario, battleSystem)`.

    Presuppone la CPU ferma su un punto sicuro (il `pop` finale di
    StartIdleBounceAnim, oppure la testa del task del moto).
    """
    od_avv = E.get("od_avversario")
    if not od_avv:
        return {"riuscita": False, "motivo": "od_avversario sconosciuto"}
    salvati = g.regs()
    g.add_bkpt(ESCA, 2)
    g.set_reg(0, od_avv & 0xFFFFFFFF)
    g.set_reg(1, bs & 0xFFFFFFFF)
    g.set_reg(14, ESCA | 1)
    g.set_reg(15, START | 1)
    st = g.cont(attesa=30)
    esito = {"od_avversario": "0x%08X" % od_avv, "bs": "0x%08X" % bs,
             "fermata": st}
    if st.startswith("S05") and g.regs()["pc"] == ESCA:
        t = g.u32(od_avv + OD_TASK)
        esito["task_creato"] = "0x%08X" % t
        esito["riuscita"] = t != 0
        esito["pic_avversario"] = "0x%08X" % g.u32(od_avv + OD_POKEPIC)
    else:
        esito["riuscita"] = False
    ripristina(g, salvati)
    g.del_bkpt(ESCA, 2)
    return esito


def gira_il_moto(g, gancio, giri):
    """Lascia girare il task del moto `giri` volte, fermandosi alla sua testa.

    Serve perche' `StartIdleBounceAnim` riparte sempre da `unk19C = 180`, cioe'
    da `sin = 0`: senza qualche giro lo sprite sarebbe a riposo e la fermata non
    farebbe vedere niente.
    """
    g.add_bkpt(gancio, 2)
    fermate = [g.cont(attesa=30) for _ in range(giri)]
    g.del_bkpt(gancio, 2)
    return fermate


def spara_sito(g, sito, od, bs, gancio=None, giri=0):
    """Esegue **il `bl` vero** del sito indicato, con la CPU ferma.

    E' la prova di banco che `T-animazioni-progetto.md` §6.3 R6 chiede («test di
    banco che chiami `0x02262014` da tutti e nove i siti»): non si salta dentro
    `StopIdleBounceAnim`, si mette `pc` **sull'istruzione `bl` del sito**, cosi'
    che `lr` lo calcoli il processore e sia quello vero (`sito + 5`, bit Thumb
    compreso). Si rientra a `sito + 4` e si rimettono i registri com'erano.

    Prima di sparare si riaccende il moto (se spento), altrimenti lo `stop`
    sarebbe a vuoto e non si vedrebbe l'effetto sullo sprite.
    """
    esito = {"sito": "0x%08X" % sito, "nome": SITI.get(sito, "?")}
    if g.u32(od + OD_TASK) == 0:
        chiama(g, START, od, bs)
        esito["riacceso"] = "0x%08X" % g.u32(od + OD_TASK)
    if gancio and giri:
        esito["giri_prima"] = len(gira_il_moto(g, gancio, giri))
    pic = g.u32(od + OD_POKEPIC)
    esito["pic"] = "0x%08X" % pic
    esito["task_prima"] = "0x%08X" % g.u32(od + OD_TASK)
    # le due mezze-parole del `bl`: servono a provare che il sito e' davvero una
    # chiamata a StopIdleBounceAnim, e che EN e IT hanno gli stessi byte.
    b = g.mem(sito, 4)
    alta, bassa = int.from_bytes(b[:2], "little"), int.from_bytes(b[2:], "little")
    off = (((alta & 0x7FF) << 12) | ((bassa & 0x7FF) << 1))
    if off & (1 << 22):
        off -= 1 << 23
    esito["bl"] = "%04X %04X" % (alta, bassa)
    esito["bl_bersaglio"] = "0x%08X" % (sito + 4 + off)
    esito["pokepic_prima"] = foto(g, pic)
    salvati = g.regs()
    g.add_bkpt(STOP, 2)
    g.add_bkpt(sito + 4, 2)
    g.set_reg(0, od & 0xFFFFFFFF)
    g.set_reg(15, sito | 1)
    st = g.cont(attesa=30)
    r = g.regs()
    esito["fermata_stop"] = st
    esito["pc_alla_fermata"] = "0x%08X" % r["pc"]
    esito["lr"] = "0x%08X" % r["lr"]
    esito["lr_atteso"] = "0x%08X" % (sito + 5)
    esito["lr_corretto"] = r["lr"] == sito + 5 and r["pc"] == STOP
    st2 = g.cont(attesa=30)
    esito["fermata_ritorno"] = st2
    esito["pc_al_ritorno"] = "0x%08X" % g.regs()["pc"]
    esito["task_dopo"] = "0x%08X" % g.u32(od + OD_TASK)
    esito["pokepic_dopo"] = foto(g, pic)
    g.del_bkpt(sito + 4, 2)
    g.del_bkpt(STOP, 2)
    ripristina(g, salvati)
    return esito


def argomenti():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--hg", required=True, help="hg_runtime-gdb")
    ap.add_argument("--rom", required=True)
    ap.add_argument("--sram")
    ap.add_argument("--out", required=True)
    ap.add_argument("--script", required=True)
    ap.add_argument("--json", required=True)
    ap.add_argument("--porta", type=int, default=4101)
    ap.add_argument("--secondi", type=float, default=300.0)
    ap.add_argument("--politica", default="nessuna", choices=list(POLITICHE))
    ap.add_argument("--anima-avversario", action="store_true")
    ap.add_argument("--max-eventi", type=int, default=600)
    ap.add_argument("--forza-subito", action="store_true",
                    help="forza il moto sull'avversario al primo giro del task")
    ap.add_argument("--giri-prima", type=int, default=5,
                    help="giri del task del moto prima di sparare un sito")
    ap.add_argument("--siti-finti", action="store_true",
                    help="spara a CPU ferma il `bl` di tutti e nove i siti "
                         "(prova R6: `lr` vero e effetto sullo sprite)")
    ap.add_argument("--bs", default="0x022C0264",
                    help="BattleSystem*, usato solo con --forza-subito")
    ap.add_argument("--gancio-task", default="0x023DB750",
                    help="testa di sgp_idle_task5 (blocco v5c; simbolo "
                         "`sgp_idle_task5` in source/sgp12/build/anim2/"
                         "manifesto.json, bit Thumb tolto)")
    return ap.parse_args()


def main():
    a = argomenti()
    sopprimi = POLITICHE[a.politica]
    os.makedirs(a.out, exist_ok=True)
    cmd = [a.hg, "--rom", a.rom, "--out", a.out, "--gdb-port", str(a.porta),
           "--script", a.script]
    if a.sram:
        cmd += ["--sram", a.sram]
    t0 = time.time()
    proc = subprocess.Popen(
        cmd, stdout=open(os.path.join(a.out, "hg-stdout.log"), "w"),
        stderr=open(os.path.join(a.out, "hg-stderr.log"), "w"))
    E = {"comando": cmd, "politica": a.politica,
         "anima_avversario": bool(a.anima_avversario), "eventi": [],
         "conteggi": {"start": 0, "start_effettivi": 0, "stop": 0,
                      "stop_effettivi": 0, "stop_soppressi": 0, "stop_end": 0}}
    try:
        g = RspSicuro(port=a.porta)
        if a.siti_finti:
            gancio = int(str(a.gancio_task), 0) & ~1
            g.add_bkpt(gancio, 2)
            E["siti_finti_fermata"] = g.cont(attesa=60)
            g.del_bkpt(gancio, 2)
            bs = int(str(a.bs), 0)
            E["lottatori"] = scopri_lottatori(g, bs)
            od = int(E["lottatori"]["lottatori"][0]["od"], 16)
            gancio = int(str(a.gancio_task), 0) & ~1
            E["siti_finti"] = [spara_sito(g, s, od, bs, gancio, a.giri_prima)
                               for s in sorted(SITI)]
        if a.forza_subito:
            # si aspetta il primo giro del NOSTRO task, che e' un punto sicuro
            # dentro la lotta, e li' si inietta l'avvio sull'avversario.
            gancio = int(str(a.gancio_task), 0) & ~1
            g.add_bkpt(gancio, 2)
            st = g.cont(attesa=60)
            E["forza_subito"] = {"fermata": st, "pc": "0x%08X" % g.regs()["pc"]}
            g.del_bkpt(gancio, 2)
            bs = int(str(a.bs), 0)
            E["lottatori"] = scopri_lottatori(g, bs)
            lott = E["lottatori"]["lottatori"]
            senza_task = [x for x in lott if x["task"] == "0x00000000"]
            E["od_avversario"] = int((senza_task[-1] if senza_task
                                      else lott[-1])["od"], 16)
            E["forzatura_iniziale"] = forza(g, bs, E)
        for bp in (START, START_FINE, STOP, STOP_END):
            g.add_bkpt(bp, 2)
        g.cont_nowait()
        scadenza = time.time() + a.secondi
        pendenti = {}
        attesa_fine_start = False
        while time.time() < scadenza and len(E["eventi"]) < a.max_eventi:
            try:
                st = g.attendi_fermata(
                    attesa=min(20.0, max(1.0, scadenza - time.time())))
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
                hits = g.u32(HITS)
                if pc == START:
                    od = r["r0"]
                    pic = g.u32(od + OD_POKEPIC) if od else 0
                    gia = g.u32(od + OD_TASK) if od else 0
                    ev = {"tipo": "start", "vblank": vb, "hits": hits,
                          "lr": "0x%08X" % r["lr"], "od": "0x%08X" % od,
                          "pic": "0x%08X" % pic, "bs": "0x%08X" % r["r1"],
                          "task_prima": "0x%08X" % gia, "effettivo": gia == 0}
                    E["conteggi"]["start"] += 1
                    if gia == 0:
                        E["conteggi"]["start_effettivi"] += 1
                    if "lottatori" not in E and r["r1"]:
                        E["lottatori"] = scopri_lottatori(g, r["r1"])
                        altri = [x["od"] for x in E["lottatori"]["lottatori"]
                                 if int(x["od"], 16) != od]
                        if altri:
                            E["od_avversario"] = int(altri[0], 16)
                    if a.anima_avversario and gia == 0 and od:
                        E["ultimo_bs"] = r["r1"]
                        attesa_fine_start = True
                elif pc == START_FINE:
                    ev = {"tipo": "start_fine", "vblank": vb, "hits": hits}
                    if attesa_fine_start and a.anima_avversario:
                        ev["forzatura"] = forza(g, E.get("ultimo_bs", 0), E)
                        attesa_fine_start = False
                elif pc == STOP:
                    od = r["r0"]
                    sito = (r["lr"] & ~1) - 4      # il `bl` sta 4 byte prima
                    pic = g.u32(od + OD_POKEPIC) if od else 0
                    task = g.u32(od + OD_TASK) if od else 0
                    ev = {"tipo": "stop", "vblank": vb, "hits": hits,
                          "lr": "0x%08X" % r["lr"], "sito": "0x%08X" % sito,
                          "nome": SITI.get(sito, "?"), "od": "0x%08X" % od,
                          "pic": "0x%08X" % pic, "task": "0x%08X" % task,
                          "effettivo": task != 0, "pokepic_prima": foto(g, pic)}
                    E["conteggi"]["stop"] += 1
                    if task != 0:
                        E["conteggi"]["stop_effettivi"] += 1
                    if sito in sopprimi:
                        g.set_reg(15, r["lr"] & ~1)
                        ev["soppresso"] = True
                        E["conteggi"]["stop_soppressi"] += 1
                    else:
                        ev["soppresso"] = False
                        pendenti[od] = ev
                else:
                    od = r["r4"]
                    pic = g.u32(od + OD_POKEPIC) if od else 0
                    ev = {"tipo": "stop_fine", "vblank": vb, "hits": hits,
                          "od": "0x%08X" % od, "pokepic_dopo": foto(g, pic)}
                    E["conteggi"]["stop_end"] += 1
                    prec = pendenti.pop(od, None)
                    if prec is not None:
                        prec["pokepic_dopo"] = ev["pokepic_dopo"]
                E["eventi"].append(ev)
            except (RspError, OSError) as e:
                E["errore_ciclo"] = "%s: %s" % (type(e).__name__, e)
                break
            try:
                g.cont_nowait()
            except (RspError, OSError):
                break
            if proc.poll() is not None:
                break
        E["fine"] = "ok"
    except (RspError, OSError) as e:
        E["fine"] = "%s: %s" % (type(e).__name__, e)
    try:
        E["rc"] = proc.wait(timeout=120)
    except subprocess.TimeoutExpired:
        proc.kill()
        E["rc"] = "ucciso"
    E["secondi"] = round(time.time() - t0, 2)
    riepiloga(E)
    with open(a.json, "w") as f:
        json.dump(E, f, indent=2, ensure_ascii=False)
    print(json.dumps({k: v for k, v in E.items() if k != "eventi"},
                     indent=2, ensure_ascii=False))
    return 0


def riepiloga(E):
    """Conteggi per sito e lista dei lottatori che hanno avuto un moto vivo."""
    E["siti_stop"] = {}
    for e in E["eventi"]:
        if e["tipo"] != "stop":
            continue
        k = "%s %s" % (e["sito"], e["nome"])
        d = E["siti_stop"].setdefault(k, {"totali": 0, "effettivi": 0,
                                          "soppressi": 0, "lr": e["lr"]})
        d["totali"] += 1
        d["effettivi"] += 1 if e.get("effettivo") else 0
        d["soppressi"] += 1 if e.get("soppresso") else 0
    E["siti_mancanti"] = ["0x%08X %s" % (k, v) for k, v in sorted(SITI.items())
                          if not any(e["tipo"] == "stop" and
                                     int(e["sito"], 16) == k
                                     for e in E["eventi"])]
    E["battler_animati"] = sorted({e["od"] for e in E["eventi"]
                                   if e["tipo"] == "start" and
                                   e.get("effettivo")})


if __name__ == "__main__":
    sys.exit(main())
