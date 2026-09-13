#!/usr/bin/env python3
"""sgp12.riserva — infrastruttura MECCANICA della riserva ARM9 (mappa,
prenotazioni, canarini): lettura delle sezioni di autoload e generazione dei
canarini di guardia.

**Scelta deliberata**: qui NON vive l'impronta del manifest (`sha256({schema,
riserva, zone})`) ne' le costanti di layout di un blocco specifico. Quelle
restano scritte IN OGNI cantiere (applicatore, rilettore, `test_riserva.py`)
in modo indipendente, per costruzione: e' il principio di
`02-COME-LAVORARE.md §2.3` — "se applicatore e rilettore condividessero
un'implementazione sbagliata la prova sarebbe nulla" — e vale anche per
`sgp12`. Consolidare quel pezzo qui toglierebbe la sua unica proprieta' utile.
Quello che invece E' sicuro condividere e' puramente meccanico: come si legge
una sezione di autoload (`ndspy.code`, usato identico in tre punti) e la
formula banale del canarino (un solo one-liner, gia' identica ovunque).
"""
from __future__ import annotations

import struct

MAINEX_LO, MAINEX_HI = 0x02380000, 0x02400000


def canarino(motivo_alto: int, n_parole: int) -> bytes:
    """`motivo_alto | i` per i in range(n_parole), u32 LE. Stessa formula (un
    one-liner) gia' identica in RISERVA-01/CAMERA-01/PLUS-03/PRESTAZIONI-NPC-*."""
    return b"".join(struct.pack("<I", motivo_alto | i) for i in range(n_parole))


def leggi_sezioni_autoload(rom_path):
    """Sezioni di autoload ARM9 (`ndspy.code.MainCodeFile`), a partire dai soli
    campi di header 0x20 (arm9 rom_off/entry/ram/size). Usata da
    `sgp12.blocchi.riserva` e da `verifiche/riserva_arm9.py`/`test_riserva.py`
    (questi ultimi restano non toccati: leggono da soli, di proposito)."""
    import ndspy.code
    with open(rom_path, "rb") as fh:
        testa = fh.read(0x200)
        rom_off, _entry, ram, size = struct.unpack_from("<IIII", testa, 0x20)
        fh.seek(rom_off)
        blob = fh.read(size)
    return ndspy.code.MainCodeFile(blob, ram).sections


def trova_sezione_riserva(sezioni):
    """La sezione di autoload dentro [MAINEX_LO, MAINEX_HI), o None."""
    for s in sezioni:
        if MAINEX_LO <= s.ramAddress < MAINEX_HI:
            return s
    return None
