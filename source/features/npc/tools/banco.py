#!/usr/bin/env python3
"""SGP-1.2-PRESTAZIONI-NPC-01 — pilotaggio di hg_runtime in modo interattivo.

Derivato dalla classe `Banco` di
`the private frame-profiling package` (stesso protocollo,
stesso preludio), estratto qui perche' lo usano piu' strumenti di questo pacchetto.

Non apre mai ROM, salvataggi o dump: li passa come nomi di file al banco e legge
solo le righe di testo che il banco stampa.
"""
import re
import subprocess
import time
from pathlib import Path

# preludio identico a R8-01 (schermate iniziali fino all'overworld con --sram)
PRELUDIO = [
    "run 1",
    "run 1799",
    "tap A 2 180",
    "tap A 2 360",
    "tap A 2 900",
    "run 300",
]

# sonde di posizione usate da 12b/12c
W_MAPPA = 0x0227D4A0
W_PX = 0x0227D4A8
W_PZ = 0x0227D4AC
W_SITO_CADENZA = 0x02000E28
VBLANK = 0x021D1138

RE_STATUS = re.compile(
    r"STATUS frame=(\d+) .*arm9_pc=0x([0-9a-f]+) .*render_polygons=(\d+)")


class Banco:
    def __init__(self, harness, rom, out, sram=None, load=None, extra=()):
        self.out = Path(out)
        self.out.mkdir(parents=True, exist_ok=True)
        cmd = [str(harness), "--rom", str(rom), "--out", str(out), "--interactive"]
        if sram:
            cmd += ["--sram", str(sram)]
        if load:
            cmd += ["--load", str(load)]
        cmd += list(extra)
        self.cmdline = cmd
        self.p = subprocess.Popen(cmd, stdin=subprocess.PIPE,
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT, text=True, bufsize=1)
        self.log = open(self.out / "stdout.log", "w")
        self._attendi_ready()

    def _attendi_ready(self):
        righe = []
        for line in self.p.stdout:
            self.log.write(line)
            righe.append(line.rstrip("\n"))
            if line.startswith("READY"):
                return righe
            if line.startswith("ERROR "):
                continue
        raise RuntimeError("banco terminato: " + "\n".join(righe[-8:]))

    def cmd(self, testo):
        t0 = time.perf_counter()
        self.p.stdin.write(testo + "\n")
        self.p.stdin.flush()
        righe = self._attendi_ready()
        return time.perf_counter() - t0, righe

    def read(self, addr, width=4):
        _, righe = self.cmd("read 0x%08X %d" % (addr, width))
        for r in righe:
            if r.startswith("READ "):
                return int(r.split()[2], 16)
        return None

    def status(self):
        _, righe = self.cmd("status")
        for r in righe:
            m = RE_STATUS.search(r)
            if m:
                return int(m.group(1)), int(m.group(2), 16), int(m.group(3))
        return None, None, None

    def preludio(self):
        for c in PRELUDIO:
            self.cmd(c)

    def chiudi(self):
        try:
            self.p.stdin.write("quit\n")
            self.p.stdin.flush()
            self.p.wait(timeout=60)
        except Exception:
            self.p.kill()
        self.log.close()
