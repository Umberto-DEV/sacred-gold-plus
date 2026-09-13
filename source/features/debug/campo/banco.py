#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SGP-1.2-CHIUSURA-01 — nucleo comune: stato di campo, avvio, warp ROBUSTO.

Differenze rispetto a `SGP-1.2-RUNTIME-02/tools/warp.py` (che NON viene toccato):

1. **La CPU non resta mai ferma per sbaglio.** In RUNTIME-02 la scoperta dell'aggancio
   avviene con un watchpoint di scrittura: alla fermata la CPU e' HALTED, e il codice
   successivo (attesa del fotogramma di iniezione, poi `add_bkpt` + `attendi_fermata`)
   presuppone invece che stia correndo. Con la CPU ferma il breakpoint non puo' scattare
   mai: e' la causa esatta di D4/D5 (`non scatta durante i 40000 fotogrammi di attesa`).
   Qui dopo ogni fermata si riprende esplicitamente con `cont()`.

2. **L'aggancio si SCOPRE per ogni ROM**, non si cabla. `0x0205C692` e' l'indirizzo
   scoperto sull'ARM9 EN: non c'e' nessuna garanzia che l'ARM9 IT abbia lo stesso
   indirizzo. Se `--aggancio` non e' dato, lo si ricava dal watchpoint su `location->x`
   e lo si dichiara nel JSON.

3. **L'attesa e' sullo STATO, non sul tempo.** Dopo il ripristino dei registri il
   breakpoint di aggancio resta ARMATO e si conta quante volte scatta: ogni scatto e'
   un fotogramma del ciclo di campo. Il warp e' `assestato` quando valgono tutte e tre:
   (a) `location->mapId` == mappa richiesta,
   (b) l'aggancio e' scattato >= N volte dopo il ripristino (il ciclo di campo gira),
   (c) `taskman == 0 and runningFieldMap == 1 and isPaused == 0` (nessun menu /
       applicazione di campo aperta).
   Fermi sul breakpoint la lettura dello stato e' gratis e coerente: non consuma
   fotogrammi del copione e non corre in parallelo al gioco.

GPL-3.0-or-later, come il resto del kit del banco.
"""
from __future__ import annotations

import os
import sys
import time

QUI = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(QUI, "..", "..", "..", ".."))
sys.path.insert(0, os.path.join(REPO, "SGP-1.2-RUNTIME-02/tools"))
from rsp import Rsp, RspError  # noqa: E402  (client RSP di RUNTIME-02, riusato tale quale)

# --- indirizzi gia' stabiliti dai cantieri precedenti -------------------------
FIELDSYS_PTR = 0x0203E304      # letterale di sFieldSysPtr (RUNTIME-02 §B)
SUB_02053E08 = 0x02053E08      # warp da pannello: (FieldSystem*, mapId, warpId)
ESCA = 0x02000800              # indirizzo di ritorno fittizio
VBLANK = 0x021D1138            # game_vblank_counter
STATO_PLUS = 0x023D8700        # blocco di stato sgp.plus (PLUS-03)

OFF_PROCMAN, OFF_TASKMAN, OFF_LOCATION = 0x00, 0x10, 0x20
OFF_RUNNINGFIELDMAP = 0x6C
OFF_ISPAUSED = 0x08
LOC_X = 0x08

REG_ORDER = ["r0", "r1", "r2", "r3", "r4", "r5", "r6", "r7", "r8", "r9", "r10",
             "r11", "r12", "sp", "lr", "pc", "cpsr"]


class RspSicuro(Rsp):
    """`Rsp` di RUNTIME-02 + l'unica correzione che serve per non stallare.

    **Difetto del core 906e9ebb, letto nei byte** (`src/debug/GdbStub.cpp:291-354`):

        r = poll(&pfd, 1, wait ? -1 : 0);
        if (r == 0) return StubState::None;   // <-- guarda SOLO il socket

    `Poll` consulta il descrittore, **non** il proprio `RecvBuffer`. Se due pacchetti
    del client finiscono in una sola `recv()` — cosa che capita ogni volta che il
    client manda un pacchetto "senza risposta" (`c`) e subito dopo un altro —
    `ParseAndSetupPacket` consuma il primo e **lascia il secondo nel buffer**; al giro
    dopo il socket e' vuoto, `poll()` rende 0, e quel secondo pacchetto non viene
    analizzato **mai piu'**. Il client aspetta una risposta che non arrivera': e'
    esattamente il `TimeoutError: timed out` osservato (misurato: 2 corse su 3 con le
    due `send` nello stesso millisecondo, 0 su 10 quando sono separate).

    L'unico punto in cui il client manda un pacchetto e non ne legge la risposta e'
    `cont_nowait`. Basta quindi dare al banco il tempo di consumarlo (>= un confine di
    fotogramma, che e' dove `CheckGdbIncoming` chiama `Poll`) prima di mandare altro.
    Nessuna modifica al binario del banco, nessuna modifica a `SGP-1.2-RUNTIME-02`.
    """

    pausa_cont = 0.10        # secondi: >= un confine di fotogramma, con margine

    def cont_nowait(self):
        super().cont_nowait()
        time.sleep(self.pausa_cont)


class Campo:
    """Stato di campo letto dai soli pacchetti `m` dello stub."""

    def __init__(self, g):
        self.g = g
        self.ptr = g.u32(FIELDSYS_PTR)
        self.fs = 0

    def stato(self):
        self.fs = self.g.u32(self.ptr)
        if not self.fs:
            return {"fs": 0}
        b = self.g.mem(self.fs, 0x70)
        w = lambda o: int.from_bytes(b[o:o + 4], "little")   # noqa: E731
        pm = w(OFF_PROCMAN)
        s = {"fs": self.fs, "processManager": pm,
             "isPaused": self.g.u32(pm + OFF_ISPAUSED) if pm else None,
             "taskman": w(OFF_TASKMAN), "location": w(OFF_LOCATION),
             "runningFieldMap": w(OFF_RUNNINGFIELDMAP)}
        if s["location"]:
            d = self.g.mem(s["location"], 20)
            (s["mapId"], s["warpId"], s["x"], s["z"], s["dir"]) = [
                int.from_bytes(d[i:i + 4], "little", signed=True) for i in range(0, 20, 4)]
        return s

    @staticmethod
    def fermo(s):
        """La tripla di pret `field_system.c:203`: overworld fermo, nessun menu aperto."""
        return bool(s.get("fs") and s.get("taskman") == 0
                    and s.get("runningFieldMap") == 1 and s.get("isPaused") == 0)


def leggibile(s):
    return {k: (f"0x{v:08X}" if k in ("fs", "processManager", "taskman", "location")
                and isinstance(v, int) else v) for k, v in (s or {}).items()}


def attendi_overworld(c, secondi=90.0):
    """Ritenta finche' la tripla di `fermo` vale, con un budget di tempo di parete.

    Non un numero fisso di tentativi: ogni giro costa ~3 fotogrammi, e quanti
    fotogrammi al secondo macini dipende dalla mappa e dal carico della macchina.
    """
    s = None
    scadenza = time.time() + secondi
    while time.time() < scadenza:
        try:
            s = c.stato()
        except RspError:
            continue
        if Campo.fermo(s):
            return s
    raise RspError(f"overworld mai fermo in {secondi}s: ultimo stato {s}")


def scopri_aggancio(g, location, attesa=120.0):
    """Scopre il punto di ritorno dentro il ciclo di campo, per QUESTA ROM.

    Watchpoint di scrittura su `location->x`, che
    `FieldSystem_UpdateLocationToPlayerPosition` riscrive a ogni fotogramma di campo.
    Alla fermata `lr` e' l'indirizzo di ritorno dentro il ciclo.

    **La CPU resta ferma alla fermata**: chi chiama DEVE riprendere (qui lo si fa
    subito con `cont_nowait` dopo aver tolto il watchpoint). E' esattamente il passo
    che mancava in RUNTIME-02 e la causa di D4/D5.
    """
    g.add_watch_write(location + LOC_X, 4)
    st = g.attendi_fermata(attesa=attesa)
    if not st.startswith("S05"):
        g.del_watch_write(location + LOC_X, 4)
        raise RspError(f"watchpoint: fermata inattesa {st!r}")
    r = g.regs()
    g.del_watch_write(location + LOC_X, 4)
    agg = r["lr"] & ~1
    return agg, {"lr": f"0x{r['lr']:08X}", "pc_scrittore": f"0x{r['pc']:08X}",
                 "aggancio": f"0x{agg:08X}"}


def warp_robusto(g, c, mappa, warp=0, aggancio=None, colpi_minimi=3,
                 budget_secondi=240.0, max_giri=4000, passo=lambda *a, **k: None,
                 in_corsa=True, fotogramma=0, su_overworld=None):
    """Esegue il warp e non torna finche' lo STATO non dice che e' assestato.

    `in_corsa=True`  -> la CPU sta correndo (il copione macina fotogrammi).
    Restituisce un dizionario di esito.
    """
    esito = {"mappa_richiesta": mappa, "warp_richiesto": warp,
             "colpi_minimi": colpi_minimi}

    # --- 1. aggancio -------------------------------------------------------
    # Due modi, e la differenza NON e' cosmetica.
    #
    # (a) `aggancio` DATO: si arma subito il breakpoint e si aspetta la prima fermata.
    #     Da quel momento in poi la CPU avanza SOLO quando il client dice `c`, quindi
    #     il numero di fotogrammi consumati e' deterministico e due corse su ROM
    #     diverse arrivano alla cattura del copione allo STESSO fotogramma. E' l'unico
    #     modo in cui un confronto pixel-per-pixel ha senso.
    #
    # (b) `aggancio` SCOPERTO col watchpoint: la CPU corre libera per tutto il tempo
    #     che il watchpoint impiega a scattare — MISURATO ~16 s, cioe' ~11 000
    #     fotogrammi — e a quel punto il copione e' gia' andato ben oltre la sua
    #     finestra di cattura. Serve a PROVARE qual e' l'aggancio su una ROM nuova,
    #     non a fare campagne confrontabili.
    if aggancio:
        agg = int(str(aggancio), 0) & ~1
        esito["aggancio"] = {"aggancio": f"0x{agg:08X}", "origine": "dato"}
        passo("aggancio dato", aggancio=f"0x{agg:08X}")
        g.add_bkpt(agg, 2)
        # prima fermata sul ciclo di campo = il gioco e' in overworld, e da qui in poi
        # ogni fotogramma passa dal client
        prima = None
        scadenza = time.time() + budget_secondi
        while time.time() < scadenza:
            st = g.attendi_fermata(attesa=budget_secondi)
            if not st.startswith("S05"):
                continue
            prima = c.stato()
            if Campo.fermo(prima):
                break
            g.cont_nowait()
        if prima is None or not Campo.fermo(prima):
            raise RspError(f"ciclo di campo mai fermo sull'aggancio: {prima}")
        esito["prima"] = leggibile(prima)
        passo("overworld fermo sull'aggancio", mapId=prima.get("mapId"),
              x=prima.get("x"), z=prima.get("z"), vblank=g.u32(VBLANK))
        armato = True
    else:
        prima = attendi_overworld(c)
        esito["prima"] = leggibile(prima)
        passo("overworld fermo", mapId=prima.get("mapId"), x=prima.get("x"),
              z=prima.get("z"))
        agg, det = scopri_aggancio(g, prima["location"])
        det["origine"] = "scoperto"
        esito["aggancio"] = det
        passo("aggancio scoperto", **det)
        g.cont_nowait()          # <<< il passo che mancava in RUNTIME-02
        armato = False
    esito["aggancio_indirizzo"] = f"0x{agg:08X}"

    # gancio per chi deve scrivere in RAM PRIMA del warp (stato del chunk plus):
    # qui la CPU e' ferma sul ciclo di campo, quindi la scrittura non consuma
    # fotogrammi e non puo' finire a meta' di un fotogramma di gioco.
    if su_overworld is not None:
        su_overworld(g, c, prima)

    # --- 1-bis. allineamento in FOTOGRAMMI DI GIOCO ------------------------
    # serve solo quando due corse su ROM diverse vanno confrontate pixel per pixel:
    # iniettando allo stesso `game_vblank_counter` tutta la linea del tempo successiva
    # (caricamento della mappa, animazioni, cattura del copione) e' allineata, e ogni
    # differenza fra i due fotogrammi e' attribuibile alla ROM, non al momento.
    if fotogramma:
        # Due fasi. (1) corsa libera fino a poco prima del bersaglio: ogni lettura di
        # `m` costa un fotogramma, quindi si avanza veloce ma si arriva "circa".
        # (2) ultimi fotogrammi UNO ALLA VOLTA fermandosi sull'aggancio: cosi'
        # l'iniezione cade sul fotogramma di gioco ESATTO, identico sulle due ROM.
        if armato:
            g.del_bkpt(agg, 2)
            g.cont_nowait()
        v = 0
        scadenza = time.time() + budget_secondi
        while time.time() < scadenza:
            v = g.u32(VBLANK)
            if v >= fotogramma - 8:
                break
        else:
            raise RspError("fotogramma di iniezione mai raggiunto")
        g.add_bkpt(agg, 2)
        armato = True
        st = g.attendi_fermata(attesa=budget_secondi)
        if not st.startswith("S05"):
            raise RspError(f"aggancio dopo l'allineamento: fermata inattesa {st!r}")
        while g.u32(VBLANK) < fotogramma:
            st = g.cont(attesa=budget_secondi)
            if not st.startswith("S05"):
                raise RspError(f"allineamento fine: fermata inattesa {st!r}")
        esito["vblank_allineamento"] = g.u32(VBLANK)
        passo("allineato al fotogramma", vblank=esito["vblank_allineamento"],
              atteso=fotogramma)

    # --- 2. fermarsi sull'aggancio ----------------------------------------
    if not armato:
        g.add_bkpt(agg, 2)
        st = g.attendi_fermata(attesa=budget_secondi)
        if not st.startswith("S05"):
            raise RspError(f"aggancio: fermata inattesa {st!r}")
    s = c.stato()
    if not Campo.fermo(s):
        raise RspError(f"condizione di overworld fermo non valida all'aggancio: {s}")
    esito["vblank_iniezione"] = g.u32(VBLANK)
    passo("fermo all'aggancio", mapId=s.get("mapId"), vblank=esito["vblank_iniezione"])

    # --- 3. iniezione della chiamata --------------------------------------
    salvati = g.regs()
    g.add_bkpt(ESCA, 2)
    g.set_reg(0, c.fs)
    g.set_reg(1, mappa & 0xFFFFFFFF)
    g.set_reg(2, warp & 0xFFFFFFFF)
    g.set_reg(14, ESCA | 1)
    g.set_reg(15, SUB_02053E08 | 1)
    passo("chiamata iniettata", funzione=f"0x{SUB_02053E08:08X}", r1=mappa, r2=warp)
    st = g.cont(attesa=60)
    if not st.startswith("S05"):
        raise RspError(f"esca: fermata inattesa {st!r}")
    dopo = g.regs()
    if dopo["pc"] != ESCA:
        raise RspError(f"ritorno non all'esca: pc=0x{dopo['pc']:08X}")
    esito["taskmanager_reso"] = f"0x{dopo['r0']:08X}"
    passo("chiamata rientrata", taskmanager=esito["taskmanager_reso"])

    # --- 4. ripristino esatto dei registri --------------------------------
    for i, nome in enumerate(REG_ORDER):
        if nome != "pc":
            g.set_reg(i, salvati[nome])
    g.set_reg(15, salvati["pc"] | (1 if salvati["cpsr"] & 0x20 else 0))
    g.del_bkpt(ESCA, 2)
    passo("registri ripristinati")

    # --- 5. ATTESA SULLO STATO (il cuore di questo cantiere) ---------------
    # il breakpoint di aggancio resta armato: ogni fermata = un fotogramma del ciclo
    # di campo. Si conta, si legge lo stato da fermi, e si esce solo quando tutte e
    # tre le condizioni valgono insieme.
    t0 = time.time()
    colpi = 0
    colpi_su_bersaglio = 0
    ultimo = None
    assestato = False
    scaduto = False
    for _ in range(max_giri):
        resta = budget_secondi - (time.time() - t0)
        if resta <= 0:
            scaduto = True
            break
        try:
            st = g.cont(attesa=max(1.0, min(60.0, resta)))
        except RspError:
            scaduto = True
            break
        if not st.startswith("S05"):
            continue
        colpi += 1
        ultimo = c.stato()
        if ultimo.get("mapId") == mappa and Campo.fermo(ultimo):
            colpi_su_bersaglio += 1
            if colpi_su_bersaglio >= colpi_minimi:
                assestato = True
                break
        else:
            colpi_su_bersaglio = 0
    esito["colpi_aggancio_dopo_ripristino"] = colpi
    esito["colpi_consecutivi_su_bersaglio"] = colpi_su_bersaglio
    esito["secondi_assestamento"] = round(time.time() - t0, 2)
    esito["scaduto"] = scaduto
    esito["dopo"] = leggibile(ultimo)
    esito["assestata"] = bool(assestato)
    esito["mappa_raggiunta"] = bool(ultimo and ultimo.get("mapId") == mappa)
    passo("assestamento", assestata=esito["assestata"], colpi=colpi,
          mapId=(ultimo or {}).get("mapId"), x=(ultimo or {}).get("x"),
          z=(ultimo or {}).get("z"), secondi=esito["secondi_assestamento"])

    # la pulizia non deve poter cancellare l'esito gia' misurato: se il gioco e' morto
    # (controprova O2.3, mappa inesistente) il banco chiude il socket proprio qui.
    try:
        g.del_bkpt(agg, 2)
        if in_corsa:
            g.cont_nowait()
    except (RspError, OSError) as e:
        esito["pulizia"] = f"{type(e).__name__}: {e}"
    return esito


def stato_plus(g):
    b = g.mem(STATO_PLUS, 32)
    return {"active_plus": b[0], "active_wild": b[1], "cap": b[2], "load_status": b[3],
            "guard": b[4], "hits_trainer": int.from_bytes(b[8:12], "little"),
            "hits_wild": int.from_bytes(b[12:16], "little"), "chunk": b[16:32].hex()}
