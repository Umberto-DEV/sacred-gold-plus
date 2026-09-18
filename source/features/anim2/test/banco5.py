#!/usr/bin/env python3
"""Banco Unicorn del blob v5, sopra ARM9 e ov012 veri del banco v4."""
import sys
import shutil
import tempfile
import struct
from pathlib import Path

QUI = Path(__file__).resolve().parent
REPO = QUI.parents[3]
sys.path.insert(0, str(REPO / "source" / "features" / "anim" / "test"))

from banco4 import Banco4, OD0, PIC0, TASK  # noqa: E402

BS = 0x02350000
ANIMSYS = 0x02351000
MGR = 0x02352000
MGR_BASE = 0x02353000


class Banco5(Banco4):
    def prepara(self, od=OD0, pic=PIC0, **kw):
        super().prepara(od, pic, **kw)
        self.wr(pic, (1).to_bytes(4, "little"))  # Pokepic.active, come Create
        # Barra sintetica, renderer originale: ManagedSprite -> Sprite.
        box = 0x02360000 + (od - OD0)
        self.wr(box, bytes(0x400))
        self.wr(od + 0x2C, box.to_bytes(4, "little"))
        self.wr(box, (box + 0x40).to_bytes(4, "little"))

    def __init__(self, build):
        # Banco4 usa il nome storico blob2.bin e lo crea accanto al build.
        # Il test non deve mai modificare source/sgp12/build: lavora su copia.
        with tempfile.TemporaryDirectory(prefix="sgp-anim2-banco-") as td:
            build_copia = Path(td)
            for p in Path(build).iterdir():
                if p.is_file():
                    shutil.copy2(p, build_copia / p.name)
            super().__init__(build_copia, 0x023DB500, 0x023DBB20,
                             0x023DBBA0, 0x023DBBE0)
            self.wr(0x023DBB60, (build_copia / "siti.bin").read_bytes())
        self.entrata = self.simboli["sgp_idle_task5"] & ~1
        self.stop_politica = self.simboli["sgp_stop_politica"] & ~1
        self.avvia_tutti = self.simboli["sgp_avvia_tutti"] & ~1
        self.stop_testa = self.simboli["sgp_stop_testa"] & ~1
        # Esegui anche la vera fermata del gioco attraverso la trampolina.
        delta = self.stop_testa - (0x02262016 + 4)
        self.wr(0x02262016, struct.pack("<HH", 0xF000 | ((delta >> 12) & 0x7FF),
                                       0xF800 | ((delta >> 1) & 0x7FF)))
        self.prepara_bs([OD0])

    def prepara_bs(self, battlers):
        self.wr(BS, bytes(0x220))
        self.wr(ANIMSYS, bytes(0x20))
        self.wr(MGR, bytes(0x20))
        self.wr(MGR_BASE, bytes(0x1D0 * 4))
        for i, od in enumerate(battlers[:4]):
            self.wr(BS + 0x34 + i * 4, int(od).to_bytes(4, "little"))
            self.wr(MGR_BASE + i * 0x1D0 + 0x20, (1).to_bytes(4, "little"))
        self.wr(BS + 0x44, len(battlers[:4]).to_bytes(4, "little"))
        self.wr(BS + 0x8C, ANIMSYS.to_bytes(4, "little"))
        self.wr(BS + 0x1C8, MGR.to_bytes(4, "little"))
        self.wr(MGR, MGR_BASE.to_bytes(4, "little"))
        self.wr(MGR + 9, bytes([len(battlers[:4])]))
        self.wr(self.stato + 0x28, BS.to_bytes(4, "little"))

    def mossa(self, active):
        self.wr(ANIMSYS + 0x10, int(bool(active)).to_bytes(4, "little"))

    def ingresso(self, indice, active):
        self.wr(MGR_BASE + indice * 0x1D0 + 0x20,
                (0 if active else 1).to_bytes(4, "little"))

    def politica(self, od, lr):
        return self.chiama(self.stop_politica, r0=od, r1=lr)

    # I parametri spediti stanno a `tabelle + 0x20` (par.bin, 32 B). I test li
    # leggono da li' invece di ricopiarli: cambiare una variante non deve
    # costringere a riscrivere le prove.
    def par(self, off):
        return self.u8(self.tabelle + 0x20 + off)
