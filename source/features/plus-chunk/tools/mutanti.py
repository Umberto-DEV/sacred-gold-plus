#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SGP-1.2-PLUS-03 — mutanti: ogni cancello deve poter fallire.

Un cancello che non ha mai visto cadere niente non è un cancello. Qui si
sabotano, uno alla volta, l'ingresso, l'uscita, il blob compilato e la mappa
della riserva, e si chiede a `applica_salvataggio.py` / `rileggi_salvataggio.py`
di accorgersene. Un mutante che SOPRAVVIVE è un difetto del collaudo, e viene
stampato come tale.

Uso:  mutanti.py --rom <ROM di lavoro> --build <dir> --tmp <scratchpad> --json F
"""
from __future__ import annotations

import argparse
import json
import shutil
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

QUI = Path(__file__).resolve()
PACCHETTO = QUI.parents[1]
REPO = QUI.parents[4]
MAPPA = Path(os.environ.get("SGP_MAPPA", REPO / "docs/arm9-reserve-map.json"))
sys.path.insert(0, str(QUI))
from arm9 import Arm9  # noqa: E402

BLOB = 0x023D8730
CANARINO = 0x023D8FF0
SITO_L0 = 0x020271F8
SITO_S0 = 0x02027456
ZONA_1_1 = 0x023DEB40


def esegui(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True)
    return p.returncode, (p.stdout + p.stderr)


def applica(rom_in, rom_out, build, mappa=None):
    cmd = [sys.executable, str(PACCHETTO / "tools" / "applica_salvataggio.py"),
           "--rom", str(rom_in), "--out", str(rom_out), "--build", str(build)]
    env = None
    return esegui(cmd)


def rileggi(rom_out, rom_in, build):
    cmd = [sys.executable, str(PACCHETTO / "tools" / "rileggi_salvataggio.py"),
           "--rom", str(rom_out), "--ingresso", str(rom_in), "--build", str(build)]
    return esegui(cmd)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--rom", required=True)
    ap.add_argument("--build", default=str(PACCHETTO / "prove" / "build"))
    ap.add_argument("--tmp", default=None)
    ap.add_argument("--json", default=None)
    a = ap.parse_args(argv)

    esiti = []
    with tempfile.TemporaryDirectory(dir=a.tmp) as td:
        td = Path(td)
        buono_in = td / "in.nds"
        shutil.copy2(a.rom, buono_in)
        buono_out = td / "out.nds"
        rc, log = applica(buono_in, buono_out, a.build)
        assert rc == 0, "il controllo di riferimento non passa:\n" + log[-2000:]
        rc, log = rileggi(buono_out, buono_in, a.build)
        assert rc == 0, "il rilettore non è verde sul riferimento:\n" + log[-2000:]
        esiti.append({"mutante": "M0 (controllo, nessuna mutazione)",
                      "atteso": "applicatore e rilettore VERDI",
                      "esito": "verde", "ucciso": None})

        build_dir = Path(a.build)

        def prova(nome, atteso, *, muta_in=None, muta_out=None, muta_build=None,
                  muta_mappa=None):
            lavoro = td / ("mut-" + nome.split()[0])
            lavoro.mkdir(exist_ok=True)
            rin = lavoro / "in.nds"
            shutil.copy2(a.rom, rin)
            bdir = lavoro / "build"
            shutil.copytree(build_dir, bdir)
            mappa_orig = None
            if muta_in:
                x = Arm9(rin)
                muta_in(x)
                x.salva(rin)
            if muta_build:
                muta_build(bdir)
            if muta_mappa:
                mappa_orig = MAPPA.read_text()
                MAPPA.write_text(muta_mappa(json.loads(mappa_orig)))
            try:
                rout = lavoro / "out.nds"
                rc, log = applica(rin, rout, bdir)
                dove = None
                if rc != 0:
                    dove = "applicatore: " + log.strip().splitlines()[-1][:160]
                else:
                    if muta_out:
                        x = Arm9(rout)
                        muta_out(x)
                        x.salva(rout)
                    rc2, log2 = rileggi(rout, rin, bdir)
                    if rc2 != 0:
                        try:
                            errori = json.loads(log2)["errori"]
                        except Exception:
                            errori = [log2.strip().splitlines()[-1][:160]]
                        dove = "rilettore: " + "; ".join(errori)[:200]
            finally:
                if mappa_orig is not None:
                    MAPPA.write_text(mappa_orig)
            esiti.append({"mutante": nome, "atteso": atteso,
                          "ucciso": dove is not None, "da": dove})

        # M1 -- il blob compilato alterato di un byte
        def m1(bdir):
            p = bdir / "salva_blob.bin"
            d = bytearray(p.read_bytes())
            d[0x40] ^= 0xFF
            p.write_bytes(bytes(d))
        prova("M1 blob compilato alterato di un byte", "R1 o R7", muta_build=m1)

        # M2 -- il blob scritto spostato di 2 byte nel blocco
        def m2(x):
            pass

        def m2out(x):
            d = x.leggi(BLOB, 464)
            x.scrivi(BLOB, b"\x00\x00" + d[:462])
        prova("M2 blob spostato di 2 B nel blocco", "R1", muta_out=m2out)

        # M3 -- gancio L0 rimesso alla preimmagine (come se non fosse applicato)
        def m3(x):
            x.scrivi(SITO_L0, bytes.fromhex("00f0ecfa"))
        prova("M3 gancio L0 non applicato", "R2", muta_out=m3)

        # M4 -- i due ganci scambiati fra loro
        def m4(x):
            a4 = x.leggi(SITO_L0, 4)
            b4 = x.leggi(SITO_S0, 4)
            x.scrivi(SITO_L0, b4)
            x.scrivi(SITO_S0, a4)
        prova("M4 i due ganci scambiati", "R2", muta_out=m4)

        # M5 -- canarino del blocco azzerato
        def m5(x):
            x.scrivi(CANARINO, b"\x00" * 16)
        prova("M5 canarino di sgp.salvataggio azzerato", "R3", muta_out=m5)

        # M6 -- un byte alterato nella zona 1.1
        def m6(x):
            v = x.leggi(ZONA_1_1 + 0x100, 1)
            x.scrivi(ZONA_1_1 + 0x100, bytes([v[0] ^ 0xFF]))
        prova("M6 un byte alterato nella zona 1.1", "R5", muta_out=m6)

        # M7 -- voce `sgp.salvataggio` tolta dalla mappa della riserva
        def m7(d):
            d["blocchi"] = [b for b in d["blocchi"] if b["nome"] != "sgp.salvataggio"]
            return json.dumps(d, indent=1, ensure_ascii=False)
        prova("M7 voce sgp.salvataggio assente dalla mappa", "A7", muta_mappa=m7)

        # M8 -- l'ABI del gioco cambiata sotto i piedi (ReadBackup diverso)
        def m8(x):
            x.scrivi(0x0202877C, b"\x00\x00")
        prova("M8 impronta di ReadBackup alterata nell'ingresso", "A3", muta_in=m8)

        # M9 -- il blob PLUS di PLUS-02 alterato (provenienza)
        def m9(x):
            v = x.leggi(0x023D8100, 1)
            x.scrivi(0x023D8100, bytes([v[0] ^ 0xFF]))
        prova("M9 blob PLUS di PLUS-02 alterato", "A1", muta_in=m9)

        # M10 -- il sito del gancio S0 già patchato (idempotenza)
        def m10(x):
            x.scrivi(SITO_S0, bytes.fromhex("deadbeef"))
        prova("M10 preimmagine del gancio S0 assente (idempotenza)", "A2/A0", muta_in=m10)

        # M11 -- blocco sgp.salvataggio non a zero nell'ingresso
        def m11(x):
            x.scrivi(0x023D8F00, b"\x01" * 4)
        prova("M11 blocco sgp.salvataggio non a zero", "A0/A4", muta_in=m11)

    vivi = [e for e in esiti if e.get("ucciso") is False]
    ris = {"totale": len(esiti) - 1, "uccisi": len([e for e in esiti if e.get("ucciso")]),
           "vivi": len(vivi), "esiti": esiti}
    if a.json:
        Path(a.json).write_text(json.dumps(ris, indent=2, ensure_ascii=False))
    print(json.dumps(ris, indent=2, ensure_ascii=False))
    return 1 if vivi else 0


if __name__ == "__main__":
    sys.exit(main())
