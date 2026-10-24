"""Data-only 1.2.5 stage: show the release in the always-accessible Plus menu.

Three menu text bytes and the upper-screen version graphics may change. All executable code,
ROM identity and save layouts remain byte-identical to the published 1.2.4.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import struct

from .manutenzione import offset_arm9
from . import titolo_versione
from .rom import Rifiuto, esigi, posizioni_diverse, sha

VERSIONE = '1.2.5'
ROM_AMMESSE = {
    'd5b20e8f3e4c273a529533a327ada7d5ac4c7847328af3bd5f4db8f95de7d548': 'EN',
    'd76b7afe6c0f515c96492bd0cffbb3e88e5d8a827b7abc32dc510be5161c0cd0': 'IT',
}
TESTI_SHA = {
    'EN': '9532b13328c2eea25a93d5beeb1d2834de7d9f6aab693327484152601e34040b',
    'IT': '1d26d66fa423a38c89fc7521ad75c878da1373e86a7fa99035c7b9f63c34466b',
}
TITOLO_124 = bytes.fromhex(
    '3d0145014701560149014801de013101530150014801de013a01500159015701'
    'de012201ae012301ae012501ffff')


def aggiorna_testi(prima: bytes, lingua: str) -> bytes:
    esigi(lingua in TESTI_SHA and len(prima) == 1008 and sha(prima) == TESTI_SHA[lingua],
          'serve il banco testi 1.2.4 integro della lingua richiesta')
    titolo = struct.unpack_from('<H', prima, 20 * 2)[0]
    esigi(prima[titolo:titolo+len(TITOLO_124)] == TITOLO_124, 'titolo precedente inatteso')
    dopo = bytearray(prima)
    # Both existing UI paths now read the same versioned title. No new string,
    # window, allocation or code; the obsolete short title remains untouched.
    dopo[:2] = prima[40:42]
    struct.pack_into('<H', dopo, titolo + len(TITOLO_124) - 4, 0x126)  # glyph '5'
    return bytes(dopo)


def verifica_testi(prima: bytes, dopo: bytes, lingua: str) -> dict:
    """Independent expectations, no call to the applier or its patch plan."""
    esigi(lingua in TESTI_SHA and len(prima) == len(dopo) == 1008 and
          sha(prima) == TESTI_SHA[lingua], 'banco di partenza/dimensione non validi')
    posizione = 504 if lingua == 'EN' else 518
    atteso = (0x13d, 0x145, 0x147, 0x156, 0x149, 0x148, 0x1de, 0x131,
              0x153, 0x150, 0x148, 0x1de, 0x13a, 0x150, 0x159, 0x157,
              0x1de, 0x122, 0x1ae, 0x123, 0x1ae, 0x126, 0xffff)
    for index in (0, 20):
        p = int.from_bytes(dopo[index*2:index*2+2], 'little')
        esigi(p == posizione, 'puntatore titolo mancante o errato')
        parole = tuple(int.from_bytes(dopo[i:i+2], 'little') for i in range(p, p+46, 2))
        esigi(parole == atteso, 'versione del titolo errata')
    diversi = posizioni_diverse(prima, dopo)
    esigi(set(diversi) == {0, 1, posizione+42}, 'modifiche fuori dai tre byte del titolo')
    return {'esito': 'VERDE', 'versione': VERSIONE, 'lingua': lingua,
            'byte_modificati': diversi, 'codice_e_formato_sav': 'INVARIATI'}


def _banco(rom):
    impronta = sha(rom)
    esigi(impronta in ROM_AMMESSE, 'serve la ROM 1.2.4 EN/IT ufficiale e integra')
    off, size = struct.unpack_from('<I', rom, 0x20)[0], struct.unpack_from('<I', rom, 0x2c)[0]
    pos = offset_arm9(rom[:512], rom[off:off+size], 0x023da800, 1008)
    return pos, ROM_AMMESSE[impronta]


def applica(prima: bytes) -> tuple[bytes, dict]:
    pos, lingua = _banco(prima)
    banco = aggiorna_testi(prima[pos:pos+1008], lingua)
    dopo = prima[:pos] + banco + prima[pos+1008:]
    dopo = titolo_versione.applica(dopo)
    return dopo, rileggi(prima, dopo)


def rileggi(prima: bytes, dopo: bytes) -> dict:
    pos, lingua = _banco(prima)
    esigi(len(prima) == len(dopo), 'dimensione ROM cambiata')
    # Remove only the independently checked menu text from the comparison.
    # The title reader rejects changes anywhere except its two graphic regions,
    # including code, game identity, file layout and all save machinery.
    senza_testi = dopo[:pos] + prima[pos:pos+1008] + dopo[pos+1008:]
    titolo_report = titolo_versione.rileggi(prima, senza_testi)
    report = verifica_testi(prima[pos:pos+1008], dopo[pos:pos+1008], lingua)
    return {**report, 'ingresso_sha256': sha(prima), 'uscita_sha256': sha(dopo),
            'dimensione_rom': len(dopo), 'offset_banco': pos, 'titolo': titolo_report}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--base', type=Path, required=True, help='1.2.4 ufficiale EN/IT')
    ap.add_argument('--uscita', type=Path, required=True, help='nuovo file, mai sovrascritto')
    ap.add_argument('--rapporto', type=Path)
    args = ap.parse_args(argv)
    try:
        out, report = applica(args.base.read_bytes())
        with args.uscita.open('xb') as f:
            f.write(out)
        # Read disk output back too, without opening any .sav file.
        rileggi(args.base.read_bytes(), args.uscita.read_bytes())
        if args.rapporto:
            with args.rapporto.open('x') as f:
                f.write(json.dumps(report, indent=2) + '\n')
        print(json.dumps(report, indent=2))
    except (Rifiuto, OSError) as exc:
        ap.exit(1, str(exc) + '\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
