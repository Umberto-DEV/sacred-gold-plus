#!/usr/bin/env python3
"""B — warp scriptabile: porta il giocatore in una mappa arbitraria facendo eseguire al
gioco la sua PROPRIA procedura di cambio mappa.

Metodo (nessuna scrittura dello stato di campo gia' caricato):

  1. si legge `sFieldSysPtr` (letterale a 0x0203E304 dell'ARM9, ricavato da `sub_0203E2F4`
     che in pret e' `sFieldSysPtr->processManager->isPaused = TRUE`) e da li' `FieldSystem*`;
  2. si aspetta la condizione di overworld fermo di pret (`field_system.c:203`):
     `taskman == NULL` (+0x10), `runningFieldMap == TRUE` (+0x6C),
     `processManager->isPaused == 0` ([[fs+0]+8]);
  3. si scopre da soli un punto di aggancio per fotogramma: watchpoint di scrittura su
     `location->x` (`fs->location` e' a +0x20, `Location.x` a +0x08), che
     `FieldSystem_UpdateLocationToPlayerPosition` riscrive a ogni fotogramma
     (pret `src/field/fieldmap.c:374-385`); alla fermata si legge `lr`, che e' l'indirizzo
     di ritorno dentro il ciclo di campo: quello e' il punto di iniezione, a confine di
     istruzione e nello stesso tratto di codice da cui il gioco stesso chiama i warp;
  4. fermi su un breakpoint a quell'indirizzo, si salvano TUTTI i registri, si imposta
     `r0 = FieldSystem*`, `r1 = mapId`, `r2 = warpId`, `lr = 0x02000800|1` (indirizzo
     esca con breakpoint) e `pc = 0x02053E08|1` — cioe' si chiama
     `sub_02053E08(fieldSystem, mapId, warpId)`, la stessa funzione che il gioco usa per i
     pannelli-warp (`src/field/field_control.c:739`), che crea il TaskManager;
  5. alla fermata sull'esca si rimettono tutti i registri com'erano e si riprende: da quel
     momento e' il gioco a eseguire il task, quindi camera, NPC, eventi e musica sono
     costruiti dal gioco stesso.

Il warpId, se diverso da -1, fa risolvere X/Z AL GIOCO leggendo il warp event della mappa
di destinazione (`sub_02052F94`, pret `src/field_warp_tasks.c:206-212`): non si inventano
coordinate.

Uso:
  python3 warp.py --hg BIN --rom ROM --sram SAV --out DIR --mappa 116 --warp 0 --json F
"""
import argparse
import json
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rsp import Rsp, RspError  # noqa: E402

FIELDSYS_PTR = 0x0203E304      # letterale: indirizzo di sFieldSysPtr
SUB_02053E08 = 0x02053E08      # warp per pannello: (FieldSystem*, mapId, warpId)
ESCA = 0x02000800              # indirizzo di ritorno fittizio (mai eseguito: ci si ferma prima)
OFF_PROCMAN, OFF_TASKMAN, OFF_LOCATION = 0x00, 0x10, 0x20
OFF_PLAYERAVATAR, OFF_RUNNINGFIELDMAP = 0x40, 0x6C
OFF_ISPAUSED = 0x08
LOC_MAPID, LOC_WARPID, LOC_X, LOC_Z, LOC_DIR = 0x00, 0x04, 0x08, 0x0C, 0x10
VBLANK = 0x021D1138            # game_vblank_counter: il fotogramma DI GIOCO
REG_ORDER = ["r0", "r1", "r2", "r3", "r4", "r5", "r6", "r7", "r8", "r9", "r10",
             "r11", "r12", "sp", "lr", "pc", "cpsr"]


class Campo:
    """lettura dello stato di campo attraverso i soli pacchetti `m` dello stub"""

    def __init__(self, g):
        self.g = g
        self.ptr = g.u32(FIELDSYS_PTR)          # valore del letterale = &sFieldSysPtr
        self.fs = 0

    def aggiorna(self):
        self.fs = self.g.u32(self.ptr)
        return self.fs

    def stato(self):
        """Un pacchetto `m` per blocco, non uno per campo: ogni pacchetto inviato mentre
        l'emulatore corre costa un fotogramma, e il copione ne ha un numero finito."""
        if not self.fs:
            return {"fs": 0}
        b = self.g.mem(self.fs, 0x70)
        w = lambda o: int.from_bytes(b[o:o + 4], "little")   # noqa: E731
        pm = w(OFF_PROCMAN)
        s = {
            "fs": self.fs,
            "processManager": pm,
            "isPaused": self.g.u32(pm + OFF_ISPAUSED) if pm else None,
            "taskman": w(OFF_TASKMAN),
            "location": w(OFF_LOCATION),
            "runningFieldMap": w(OFF_RUNNINGFIELDMAP),
        }
        if s["location"]:
            d = self.g.mem(s["location"], 20)
            s["mapId"], s["warpId"], s["x"], s["z"], s["dir"] = [
                int.from_bytes(d[i:i + 4], "little", signed=True) for i in range(0, 20, 4)]
        return s

    def fermo(self):
        s = self.stato()
        return (s.get("fs") and s.get("taskman") == 0 and s.get("runningFieldMap") == 1
                and s.get("isPaused") == 0), s


def attendi_fermo(c, tentativi=60):
    s = None
    for _ in range(tentativi):
        c.aggiorna()
        ok, s = c.fermo()
        if ok:
            return s
    raise RspError(f"overworld mai fermo: ultimo stato {s}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hg", required=True)
    ap.add_argument("--rom", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--script", required=True)
    ap.add_argument("--sram")
    ap.add_argument("--load")
    ap.add_argument("--mappa", type=int, required=True)
    ap.add_argument("--warp", type=int, default=0)
    ap.add_argument("--porta", type=int, default=3333)
    ap.add_argument("--json", required=True)
    ap.add_argument("--tentativi-verifica", type=int, default=400)
    ap.add_argument("--fotogramma-iniezione", type=int, default=0,
                    help="inietta quando game_vblank_counter raggiunge questo valore: "
                         "rende l iniezione deterministica in fotogrammi di gioco, non "
                         "in secondi, cosi due corse su ROM diverse sono confrontabili")
    ap.add_argument("--attesa-vblank", type=int, default=20000)
    ap.add_argument("--aggancio", default=None,
                    help="indirizzo del punto di aggancio per fotogramma; se manca lo "
                         "scopre da solo con un watchpoint su location->x")
    ap.add_argument("--attesa-prologo", type=float, default=25.0,
                    help="secondi di emulazione libera prima di cercare l'overworld")
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    cmd = [args.hg, "--rom", args.rom, "--out", args.out, "--gdb-port", str(args.porta),
           "--script", args.script]
    if args.sram:
        cmd += ["--sram", args.sram]
    if args.load:
        cmd += ["--load", args.load]
    log = open(os.path.join(args.out, "hg-stdout.log"), "w")
    err = open(os.path.join(args.out, "hg-stderr.log"), "w")
    t0 = time.time()
    proc = subprocess.Popen(cmd, stdout=log, stderr=err)

    esito = {"comando": cmd, "mappa_richiesta": args.mappa, "warp_richiesto": args.warp,
             "passi": []}

    def passo(nome, **kw):
        kw["passo"] = nome
        kw["t"] = round(time.time() - t0, 2)
        esito["passi"].append(kw)
        print(f"[{kw['t']:7.2f}] {nome}: "
              + " ".join(f"{k}={v}" for k, v in kw.items() if k not in ("t", "passo")),
              file=sys.stderr, flush=True)

    try:
        g = Rsp(port=args.porta)
        g.cont_nowait()                       # lascia correre il prologo dello script
        time.sleep(args.attesa_prologo)

        c = Campo(g)
        passo("sFieldSysPtr", indirizzo=f"0x{c.ptr:08X}")
        prima = attendi_fermo(c)
        esito["prima"] = {k: (f"0x{v:08X}" if k in ("fs", "processManager", "taskman",
                                                    "location") and isinstance(v, int) else v)
                          for k, v in prima.items()}
        passo("overworld fermo", mapId=prima["mapId"], x=prima["x"], z=prima["z"])

        # 3. punto di aggancio per fotogramma: dato, oppure scoperto da soli
        loc = prima["location"]
        if args.aggancio:
            aggancio = int(args.aggancio, 0) & ~1
            passo("aggancio dato", aggancio=f"0x{aggancio:08X}")
        else:
            g.add_watch_write(loc + LOC_X, 4)
            st = g.attendi_fermata(attesa=120)
            if not st.startswith("S05"):
                raise RspError(f"watchpoint: fermata inattesa {st!r}")
            r = g.regs()
            g.del_watch_write(loc + LOC_X, 4)
            aggancio = r["lr"] & ~1
            passo("aggancio scoperto", lr=f"0x{r['lr']:08X}",
                  pc_scrittore=f"0x{r['pc']:08X}", aggancio=f"0x{aggancio:08X}")

        # 3-bis. il fotogramma di iniezione: deterministico in fotogrammi di gioco
        if args.fotogramma_iniezione:
            v = 0
            for _ in range(args.attesa_vblank):
                v = g.u32(VBLANK)
                if v >= args.fotogramma_iniezione:
                    break
            else:
                raise RspError("fotogramma di iniezione mai raggiunto")
            passo("fotogramma di iniezione raggiunto", vblank=v)

        # 4. iniezione della chiamata
        g.add_bkpt(aggancio, 2)
        st = g.attendi_fermata(attesa=120)   # il bersaglio sta gia' correndo: niente `c`
        if not st.startswith("S05"):
            raise RspError(f"aggancio: fermata inattesa {st!r}")
        ok, s = c.fermo()
        passo("fermo all'aggancio", condizione_ok=bool(ok), taskman=s.get("taskman"),
              runningFieldMap=s.get("runningFieldMap"), isPaused=s.get("isPaused"),
              mapId=s.get("mapId"))
        if not ok:
            raise RspError(f"condizione di overworld fermo non valida all'aggancio: {s}")

        salvati = g.regs()
        esito["registri_salvati"] = {k: f"0x{v:08X}" for k, v in salvati.items()}
        g.add_bkpt(ESCA, 2)
        g.set_reg(0, c.fs)
        g.set_reg(1, args.mappa & 0xFFFFFFFF)
        g.set_reg(2, args.warp & 0xFFFFFFFF)
        g.set_reg(14, ESCA | 1)
        g.set_reg(15, SUB_02053E08 | 1)
        passo("chiamata iniettata", funzione=f"0x{SUB_02053E08:08X}",
              r0=f"0x{c.fs:08X}", r1=args.mappa, r2=args.warp)

        st = g.cont(attesa=60)
        if not st.startswith("S05"):
            raise RspError(f"esca: fermata inattesa {st!r}")
        dopo_call = g.regs()
        if dopo_call["pc"] != ESCA:
            raise RspError(f"ritorno non all'esca: pc=0x{dopo_call['pc']:08X}")
        passo("chiamata rientrata", taskmanager_reso=f"0x{dopo_call['r0']:08X}")

        # 5. ripristino esatto dello stato interrotto
        for i, nome in enumerate(REG_ORDER):
            if nome == "pc":
                continue
            g.set_reg(i, salvati[nome])
        g.set_reg(15, salvati["pc"] | (1 if salvati["cpsr"] & 0x20 else 0))
        g.del_bkpt(ESCA, 2)
        g.del_bkpt(aggancio, 2)
        g.cont_nowait()
        passo("registri ripristinati")

        # 6. verifica: la mappa corrente cambia da sola, perche' e' il gioco a caricarla
        cambiata, s = None, None
        for _ in range(args.tentativi_verifica):
            c.aggiorna()
            s = c.stato()
            if s.get("mapId") == args.mappa:
                cambiata = True
                break
        esito["dopo"] = {k: (f"0x{v:08X}" if k in ("fs", "processManager", "taskman",
                                                   "location") and isinstance(v, int) else v)
                         for k, v in (s or {}).items()}
        esito["mappa_raggiunta"] = bool(cambiata)
        if cambiata:
            for _ in range(args.tentativi_verifica):
                c.aggiorna()
                ok, s = c.fermo()
                if ok and s.get("mapId") == args.mappa:
                    break
            esito["assestata"] = {k: (f"0x{v:08X}" if k in ("fs", "processManager",
                                      "taskman", "location") and isinstance(v, int)
                                      else v) for k, v in s.items()}
            passo("mappa assestata", fermo=bool(ok), mapId=s.get("mapId"),
                  x=s.get("x"), z=s.get("z"), vblank=g.u32(VBLANK))
        passo("verifica mappa", mapId=s.get("mapId") if s else None, atteso=args.mappa,
              raggiunta=bool(cambiata))
        esito["fine_sessione"] = "ok"
    except (RspError, OSError) as e:
        esito["fine_sessione"] = f"{type(e).__name__}: {e}"
    try:
        rc = proc.wait(timeout=300)
    except subprocess.TimeoutExpired:
        proc.kill()
        rc = "ucciso dopo 300 s"
    esito["rc_hg_runtime"] = rc
    esito["secondi"] = round(time.time() - t0, 2)
    with open(args.json, "w") as f:
        json.dump(esito, f, indent=2)
    print(json.dumps({k: v for k, v in esito.items() if k != "registri_salvati"}, indent=2))
    return 0 if esito.get("mappa_raggiunta") else 1


if __name__ == "__main__":
    sys.exit(main())
