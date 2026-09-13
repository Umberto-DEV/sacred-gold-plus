#!/usr/bin/env python3
"""premi_rileggi.py — rilettore indipendente di SGP-1.2-BORSA-GEN-05.

Non importa `premi_disfa`, non riceve costanti da lui: riapre da zero la ROM
di PARTENZA (patchata REWARD-01) e quella di ARRIVO (prodotta da
`premi_disfa.py`) e verifica con `ndspy` da solo che:

  1. la ROM abbia la STESSA lunghezza, prima e dopo;
  2. OGNI byte fuori dalla vecchia estensione FAT del file NitroFS `a/0/1/2`
     sia IDENTICO fra le due ROM (nessun altro file si e' spostato, l'header
     e tutto il resto della cartuccia sono intatti);
  3. dentro il NARC `a/0/1/2`, i 965 membri combacino uno per uno con
     l'unica eccezione di 843, 859, 877;
  4. quei tre membri, nella ROM di arrivo, abbiano esattamente lunghezza e
     SHA-256 delle preimmagini vanilla gia' verificate dal pacchetto sorgente.

Se una sola di queste condizioni cade, esce con codice diverso da zero e
NON scrive nulla (e' un lettore, non tocca la ROM).

Uso:
    premi_rileggi.py PRIMA.nds DOPO.nds [--report report.json]
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import struct
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[3]
sys.path.insert(0, str(REPO_ROOT / 'source' / 'translation'))

import ndspy.narc  # noqa: E402
import ndspy.rom  # noqa: E402


def _carica_posizioni_diverse():
    """`sgp12.rom.posizioni_diverse` senza eseguire `sgp12/__init__.py` (che
    importa tutti i blocchi): confronto a blocchi da 1 MiB, C sotto, usato
    gia' da applica/rileggi della 1.2 per non ciclare byte a byte su ~130 MB
    in Python puro (ore anziche' secondi)."""
    percorso = REPO_ROOT / 'source' / 'sgp12' / 'rom.py'
    spec = importlib.util.spec_from_file_location('_sgp12_rom_standalone', percorso)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo.posizioni_diverse


posizioni_diverse = _carica_posizioni_diverse()

ARCHIVE_NAME = 'a/0/1/2'
MEMBRI_ATTESI_DIVERSI = (843, 859, 877)
N_MEMBERS_ATTESI = 965
VANILLA = {
    843: (5468, 'cb690bc3b229515e11dda13d691f354e0d39905597b7b2d2abd3bafb200862d1'),
    859: (516, '5abff969bd83c4975cf0815c2f5c7c28d581cb2ecae994ca3049123918d41f9e'),
    877: (457, '742f3f4fe75ecc952fa8fbbdc9ecee56c5f743f5199d864eb2725721cc2f4f00'),
}


def sha(data: bytes) -> str:
    return hashlib.sha256(bytes(data)).hexdigest()


def fat_entry(raw: bytes, file_id: int):
    fat_off, fat_len = struct.unpack_from('<II', raw, 0x48)
    n = fat_len // 8
    if not 0 <= file_id < n:
        raise ValueError('file_id %d fuori dalla FAT (%d voci)' % (file_id, n))
    return struct.unpack_from('<II', raw, fat_off + file_id * 8)


def rileggi(prima_bytes: bytes, dopo_bytes: bytes) -> dict:
    esiti = {'ok': True, 'problemi': []}

    def fallisce(msg):
        esiti['ok'] = False
        esiti['problemi'].append(msg)

    # 1. lunghezza ROM invariata
    esiti['rom_byte_prima'] = len(prima_bytes)
    esiti['rom_byte_dopo'] = len(dopo_bytes)
    if len(prima_bytes) != len(dopo_bytes):
        fallisce('lunghezza ROM cambiata: %d -> %d' % (len(prima_bytes), len(dopo_bytes)))

    # 2. estensione FAT del file NitroFS a/0/1/2 nella ROM di PARTENZA
    #    (e' quella che, in luogo, puo' solo restringersi: si esclude
    #    dal confronto byte a byte SOLO quella finestra, mai altro — e la
    #    voce di 8 byte della FAT stessa, che DEVE cambiare per dire che il
    #    file si e' accorciato: e' descrizione di a/0/1/2, non "qualcos'altro
    #    che si e' mosso". E' esclusa esplicitamente, non per distanza.)
    parsed_prima = ndspy.rom.NintendoDSRom(prima_bytes)
    idx = parsed_prima.filenames.idOf(ARCHIVE_NAME)
    if idx is None:
        fallisce('%s assente dalla ROM di partenza' % ARCHIVE_NAME)
        return esiti
    start, end = fat_entry(prima_bytes, idx)
    fat_off, _fat_len = struct.unpack_from('<II', prima_bytes, 0x48)
    entry_off = fat_off + idx * 8
    start_dopo, end_dopo = fat_entry(dopo_bytes, idx)
    esiti['finestra_a_0_1_2'] = {
        'file_id': idx, 'inizio': start, 'fine_prima': end, 'fine_dopo': end_dopo,
        'voce_fat_offset': entry_off,
    }
    if start_dopo != start:
        fallisce("%s: l'inizio della voce FAT e' cambiato (%d -> %d), non era in luogo"
                  % (ARCHIVE_NAME, start, start_dopo))
    if end_dopo > end:
        fallisce("%s: la voce FAT e' CRESCIUTA (%d -> %d), non si e' ristretta"
                  % (ARCHIVE_NAME, end, end_dopo))

    n = min(len(prima_bytes), len(dopo_bytes))
    # Intervalli esclusi dal confronto "tutto il resto", ordinati: la voce
    # FAT di 8 byte (vicino all'inizio del file) e la finestra del payload
    # (molto piu' avanti). Confronto a blocchi (posizioni_diverse, sgp12.rom)
    # su ciascuno dei tre segmenti restanti: [0,entry_off), [entry_off+8,
    # start), [end,n) — cosi' anche il resto della FAT e tutto ARM9/overlay
    # restano sotto controllo, non solo i dintorni del payload.
    segmenti = [(0, entry_off), (entry_off + 8, start), (end, n)]
    fuori_finestra_diversi = []
    for s0, s1 in segmenti:
        if s1 <= s0:
            continue
        fuori_finestra_diversi.extend(
            s0 + i for i in posizioni_diverse(prima_bytes[s0:s1], dopo_bytes[s0:s1]))
    # coda, se le lunghezze differiscono (non dovrebbe: punto 1 gia' fallisce)
    fuori_finestra_diversi += list(range(n, max(len(prima_bytes), len(dopo_bytes))))
    esiti['byte_diversi_fuori_a_0_1_2'] = len(fuori_finestra_diversi)
    if fuori_finestra_diversi:
        campione = fuori_finestra_diversi[:10]
        fallisce("%d byte diversi FUORI da %s e dalla sua voce FAT (es. offset %r): "
                  "qualcosa si e' spostato" % (len(fuori_finestra_diversi), ARCHIVE_NAME, campione))

    # 3 e 4. dentro il NARC: solo 843/859/877 cambiano e combaciano con le
    # firme post-condizione verificate, senza richiedere una ROM 1.03 esterna.
    narc_prima = ndspy.narc.NARC(parsed_prima.getFileByName(ARCHIVE_NAME))
    parsed_dopo = ndspy.rom.NintendoDSRom(dopo_bytes)
    narc_dopo = ndspy.narc.NARC(parsed_dopo.getFileByName(ARCHIVE_NAME))

    esiti['membri_prima'] = len(narc_prima.files)
    esiti['membri_dopo'] = len(narc_dopo.files)
    if len(narc_prima.files) != N_MEMBERS_ATTESI or len(narc_dopo.files) != N_MEMBERS_ATTESI:
        fallisce('numero di membri inatteso: prima=%d dopo=%d (attesi %d)'
                  % (len(narc_prima.files), len(narc_dopo.files), N_MEMBERS_ATTESI))

    n_membri = min(len(narc_prima.files), len(narc_dopo.files))
    cambiati = [i for i in range(n_membri) if bytes(narc_prima.files[i]) != bytes(narc_dopo.files[i])]
    esiti['membri_cambiati'] = cambiati
    if cambiati != list(MEMBRI_ATTESI_DIVERSI):
        fallisce('membri cambiati %r, attesi esattamente %r' % (cambiati, list(MEMBRI_ATTESI_DIVERSI)))

    esiti['membri'] = {}
    for m in MEMBRI_ATTESI_DIVERSI:
        dopo = bytes(narc_dopo.files[m]) if m < len(narc_dopo.files) else b''
        voce = {
            'prima_byte': len(narc_prima.files[m]) if m < len(narc_prima.files) else None,
            'prima_sha256': sha(narc_prima.files[m]) if m < len(narc_prima.files) else None,
            'dopo_byte': len(dopo),
            'dopo_sha256': sha(dopo),
        }
        attesi = VANILLA[m]
        voce['vanilla_byte'] = attesi[0]
        voce['vanilla_sha256'] = attesi[1]
        voce['dopo_uguale_a_vanilla'] = (len(dopo), sha(dopo)) == attesi
        if not voce['dopo_uguale_a_vanilla']:
            fallisce('membro %d: firma post-condizione vanilla inattesa' % m)
        esiti['membri'][m] = voce

    return esiti


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('prima', type=Path)
    parser.add_argument('dopo', type=Path)
    parser.add_argument('--report', type=Path, default=None)
    args = parser.parse_args(argv)

    esiti = rileggi(args.prima.read_bytes(), args.dopo.read_bytes())
    testo = json.dumps(esiti, indent=2, ensure_ascii=False, default=str)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(testo, encoding='utf-8')
    print(testo)
    return 0 if esiti['ok'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
