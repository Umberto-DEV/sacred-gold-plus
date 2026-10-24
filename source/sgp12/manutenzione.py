#!/usr/bin/env python3
"""Stadio finale 1.2.4 dalla 1.2.3, in streaming e senza ROM intermedie.

--verifica prepara e rilegge i tre overlay in memoria, senza scrivere ROM.
--uscita scrive una sola nuova ROM; ingresso e salvataggi non sono modificati.
"""
from __future__ import annotations

import argparse
import io
from dataclasses import dataclass
import json
from pathlib import Path
import struct

from .blz import blz_comprimi_ottimo, blz_decomprimi
from .rom import Rifiuto, esigi, sha, sha_file

SOURCE = Path(__file__).resolve().parents[1]
BUILD = Path(__file__).resolve().parent / 'build/manutenzione'
ROM_AMMESSE = {
    '05518fbab1d27b87a6ef7081b3d16661e4e163e44eca1546a632370b21f1d4b9': 'EN',
    '12112fdbdbaa4a9686bdc66f89eec6d49755973a607547d8a48d02d98ae14be0': 'IT',
}
OVERLAY = {
    1: (0x021E5900, '72509e73d0b31bc1b18f948651e68c154599e0c514c56a9bc1422514678f5f2a'),
    7: (0x0221BE20, '3bece308154d730f230031747309703e5b8c142992c0408b842fca2f859f6c3b'),
    12: (0x022378C0, '609546e8213bd5fbbcf125a3731ffce73f66d92afbe344f61712eacf64280c36'),
}
CORE_SHA = 'dc6f64e7a017636a6d52fc9a6a1d6ec8c61e60cd807938008dfa9b8135286564'
PARTI = {
    'copie': (0x023DBC60, 160, ('sgp_copia_inizio', 'sgp_copia_fine', 'sgp_idle_copie')),
    'cascata': (0x023D8040, 64, ('sgp_cerca_cascata',)),
}
CHUNK = 1 << 20


@dataclass(frozen=True)
class Cambio:
    offset: int
    prima: bytes
    dopo: bytes
    nome: str


def leggi(f, offset, size):
    esigi(offset >= 0 and size >= 0, 'lettura con estremi negativi')
    f.seek(offset)
    b = f.read(size)
    esigi(len(b) == size, 'file troncato durante ' + str(offset))
    return b


def bl(sito, destinazione):
    d = (destinazione & ~1) - (sito + 4)
    esigi(not (d & 1) and -0x400000 <= d < 0x400000, 'BL fuori portata')
    return struct.pack('<HH', 0xF000 | ((d >> 12) & 0x7FF), 0xF800 | ((d >> 1) & 0x7FF))


def destinazione_bl(sito, dati):
    """Decoder distinto dall'encoder, usato nella rilettura dei ganci."""
    hi, lo = struct.unpack('<HH', dati)
    esigi(hi & 0xF800 == 0xF000 and lo & 0xF800 == 0xF800, 'non è una BL Thumb')
    delta = ((hi & 0x7FF) << 12) + ((lo & 0x7FF) << 1)
    if delta >= 0x400000:
        delta -= 0x800000
    return sito + 4 + delta


def carica_build(build):
    build = Path(build)
    m = json.loads((build / 'manifesto.json').read_text())
    esigi(m['schema'] == 1 and set(m['parti']) == set(PARTI), 'schema build inatteso')
    esigi(sha((SOURCE / 'features/manutenzione/compila.py').read_bytes()) == m['compila_sha256'],
          'compilatore Python diverso dal manifesto: ricompilare')
    payload, simboli = {}, {}
    for nome, (base, size, nomi) in PARTI.items():
        p = m['parti'][nome]
        b = (build / (nome + '.bin')).read_bytes()
        esigi((p['base'], p['bytes'], len(b), p['limite_codice']) == (base, size, size, size-16),
              'layout build errato: ' + nome)
        esigi(0 < p['codice_bytes'] <= size-16 and sha(b) == p['sha256'], 'blob alterato: ' + nome)
        src = SOURCE / 'features/manutenzione/sorgenti' / (nome + '.S')
        esigi(p['sorgente'] == str(src.relative_to(SOURCE.parent)) and
              sha(src.read_bytes()) == p['sorgente_sha256'], 'sorgente diverso dal build: ' + nome)
        can = b''.join((0xCA5A2000 + (0x10 if nome == 'cascata' else 0) + i).to_bytes(4, 'little')
                       for i in range(4))
        esigi(b[-16:] == can and not any(b[p['codice_bytes']:-16]), 'canarino/padding errato')
        esigi(set(p['simboli']) == set(nomi), 'simboli build inattesi')
        for n in nomi:
            v = p['simboli'][n]
            esigi(v & 1 and base <= (v & ~1) < base+p['codice_bytes'], 'simbolo fuori dal codice')
            simboli[n] = v
        payload[nome] = b
    return payload, simboli


def offset_arm9(header, arm9, ram, n):
    """Segue le sezioni autoload senza leggere la ROM intera."""
    off, _, base, _ = struct.unpack_from('<4I', header, 0x20)
    tab0, tab1, dati0 = struct.unpack_from('<3I', arm9, 0xBA0)
    sezioni = [(base, off, dati0-base)]
    cursor = off + dati0-base
    for p in range(tab0-base, tab1-base, 12):
        dest, size, _ = struct.unpack_from('<3I', arm9, p)
        sezioni.append((dest, cursor, size))
        cursor += size
    for dest, posizione, size in sezioni:
        if dest <= ram and ram+n <= dest+size:
            return posizione+ram-dest
    raise Rifiuto(f'{ram:#x}+{n} non appartiene ad ARM9/autoload')


def controlla_cambi(f, cambi):
    precedente = 0
    for c in sorted(cambi, key=lambda c: c.offset):
        esigi(len(c.prima) == len(c.dopo) > 0, 'dimensione patch non conservata')
        esigi(c.offset >= precedente, 'patch sovrapposte')
        esigi(leggi(f, c.offset, len(c.prima)) == c.prima, 'preimmagine errata: ' + c.nome)
        precedente = c.offset + len(c.prima)


def prepara_stream(f, impronta, dimensione, build=BUILD):
    """Prepare the final release stage from the exact published 1.2.3 intermediate."""
    from ndspy.codeCompression import decompress
    esigi(impronta in ROM_AMMESSE, 'serve la 1.2.3 EN/IT ufficiale, integra e non già aggiornata')
    payload, sym = carica_build(build)
    cambi, overlay_report = [], []
    h = leggi(f, 0, 512)
    off9, n9 = struct.unpack_from('<I', h, 0x20)[0], struct.unpack_from('<I', h, 0x2C)[0]
    arm9 = leggi(f, off9, n9)
    core_off = offset_arm9(h, arm9, 0x023DB500, 1532)
    esigi(sha(leggi(f, core_off, 1532)) == CORE_SHA, 'ANIM2 non è la v5d attesa')
    for nome, (ram, n, _) in PARTI.items():
        pos = offset_arm9(h, arm9, ram, n)
        cambi.append(Cambio(pos, bytes(n), payload[nome], nome))
    # Il contatore usa una parola precedentemente riservata, già zero.
    esigi(leggi(f, offset_arm9(h, arm9, 0x023DBBC0, 4), 4) == bytes(4), 'contatore non vergine')
    fatoff, fatsz, y9off = struct.unpack_from('<3I', h, 0x48)
    fat = leggi(f, fatoff, fatsz)
    ganci = {
        1: [(0x021E6BBE, 0x020542E8, 'sgp_cerca_cascata')],
        7: [(0x0221FBAE, 0x0201AA8C, 'sgp_copia_inizio'),
            (0x0221FE36, 0x0201AB0C, 'sgp_copia_fine'),
            (0x0221FE6A, 0x0201AB0C, 'sgp_copia_fine')],
        12: [],
    }
    for oid, (ram, expected_sha) in OVERLAY.items():
        entry = leggi(f, y9off+oid*32, 32)
        e = struct.unpack('<8I', entry)
        esigi(e[0] == oid and e[1] == ram and e[7] & 0x01000000, 'overlay inatteso')
        start, end = struct.unpack_from('<II', fat, e[6]*8)
        packed = leggi(f, start, end-start)
        old = decompress(packed)
        esigi(len(old) == e[2] and sha(old) == expected_sha, f'ov{oid}: impronta inattesa')
        esigi(blz_decomprimi(packed) == old, f'ov{oid}: decoder discordi')
        new = bytearray(old)
        allowed = set()
        for sito, native, symbol in ganci[oid]:
            p = sito-ram
            esigi(old[p:p+4] == bl(sito, native), f'ov{oid}: BL nativa inattesa')
            new[p:p+4] = bl(sito, sym[symbol])
            allowed.update(range(p, p+4))
        if oid == 12:
            p = 0x0226200C-ram
            esigi(struct.unpack_from('<I', old, p)[0] == 0x023DB72D, 'task idle inatteso')
            struct.pack_into('<I', new, p, sym['sgp_idle_copie'])
            allowed.update(range(p, p+4))
        encoded = blz_comprimi_ottimo(new, bersaglio=len(packed))
        esigi(len(encoded) <= len(packed), f'ov{oid}: lo spazio in luogo non basta')
        check = decompress(encoded)
        esigi(check == new and len(check) == len(old), f'ov{oid}: rilettura BLZ fallita')
        esigi(all(a == b or i in allowed for i, (a, b) in enumerate(zip(old, check))),
              f'ov{oid}: modifiche fuori dai ganci')
        for sito, _, symbol in ganci[oid]:
            esigi(destinazione_bl(sito, check[sito-ram:sito-ram+4]) == (sym[symbol] & ~1),
                  f'ov{oid}: destinazione BL errata')
        if oid == 12:
            esigi(struct.unpack_from('<I', check, 0x0226200C-ram)[0] == sym['sgp_idle_copie'],
                  'rilettura puntatore idle fallita')
        cambi.append(Cambio(start, packed, encoded.ljust(len(packed), b'\xff'), f'ov{oid}'))
        if len(encoded) != len(packed):
            cambi.append(Cambio(fatoff+e[6]*8+4, struct.pack('<I', end),
                                struct.pack('<I', start+len(encoded)), f'FAT ov{oid}'))
            cambi.append(Cambio(y9off+oid*32+28, entry[28:32],
                                struct.pack('<I', (e[7] & 0xFF000000) | len(encoded)), f'y9 ov{oid}'))
        overlay_report.append({'id': oid, 'bytes_prima': len(packed), 'bytes_dopo': len(encoded),
                               'sha256_modulo_dopo': sha(check), 'rilettura': 'OK'})
    controlla_cambi(f, cambi)
    v = json.loads((Path(build) / 'versione.json').read_text())
    esigi(v['versione'] == '1.2.4' and v['intermedio'] == '1.2.3', 'versione build inattesa')
    titolo = v['titolo'][ROM_AMMESSE[impronta]]
    pos = offset_arm9(h, arm9, 0x023DA800, 1008)
    esigi(sha(leggi(f, pos, 1008)) == titolo['blob_prima_sha256'], 'blob titolo inatteso')
    cambi.append(Cambio(pos + titolo['offset'], bytes.fromhex(titolo['prima']),
                        bytes.fromhex(titolo['dopo']), 'titolo 1.2.4'))
    controlla_cambi(f, cambi)
    return cambi, {'versione': '1.2.4', 'lingua': ROM_AMMESSE[impronta],
                  'ingresso_sha256': impronta, 'dimensione_rom': dimensione,
                  'overlay': overlay_report,
                  'scritture': [{'offset': c.offset, 'bytes': len(c.dopo), 'nome': c.nome,
                                 'sha256': sha(c.dopo)} for c in cambi],
                  'totem': 'script invariato; cattura riuscita nella prova utente',
                  'fps': 'nessun confronto controllato prima/dopo'}


def prepara(base, build=BUILD):
    base = Path(base)
    with base.open('rb') as f:
        return prepara_stream(f, sha_file(base), base.stat().st_size, build)


def applica(rom, build=BUILD):
    """Final stage used by the public builder; no intermediate ROM files."""
    with io.BytesIO(rom) as f:
        cambi, report = prepara_stream(f, sha(rom), len(rom), build)
        controlla_cambi(f, cambi)
    out = bytearray(rom)
    for c in cambi:
        out[c.offset:c.offset+len(c.dopo)] = c.dopo
    return bytes(out), report


def rileggi(prima, dopo, build=BUILD):
    """Check every written region and every untouched byte, without calling applica."""
    esigi(len(prima) == len(dopo), 'dimensione finale cambiata')
    with io.BytesIO(prima) as f:
        cambi, _ = prepara_stream(f, sha(prima), len(prima), build)
    cursor = 0
    for c in sorted(cambi, key=lambda c: c.offset):
        esigi(dopo[cursor:c.offset] == prima[cursor:c.offset], 'byte estranei modificati')
        esigi(dopo[c.offset:c.offset+len(c.dopo)] == c.dopo, 'rilettura: ' + c.nome)
        cursor = c.offset+len(c.dopo)
    esigi(dopo[cursor:] == prima[cursor:], 'coda modificata')
    return {'esito': 'VERDE', 'regioni': len(cambi), 'uscita_sha256': sha(dopo)}


def blocco_modificato(data, offset, cambi):
    b = bytearray(data)
    for c in cambi:
        lo, hi = max(offset, c.offset), min(offset+len(b), c.offset+len(c.dopo))
        if lo < hi:
            b[lo-offset:hi-offset] = c.dopo[lo-c.offset:hi-c.offset]
    return b


def scrivi(base, uscita, cambi, expected_sha):
    """Output esclusivo, pulizia dei soli parziali propri, rilettura completa a blocchi."""
    base, uscita = Path(base), Path(uscita)
    esigi(not uscita.exists(), 'output già presente: scegliere un nuovo nome')
    esigi(sha_file(base) == expected_sha, 'ingresso cambiato dopo la preparazione')
    with base.open('rb') as f:
        controlla_cambi(f, cambi)
    created = False
    try:
        with base.open('rb') as f, uscita.open('xb') as out:
            created = True
            offset = 0
            for b in iter(lambda: f.read(CHUNK), b''):
                out.write(blocco_modificato(b, offset, cambi))
                offset += len(b)
        esigi(sha_file(base) == expected_sha, 'ingresso cambiato durante la scrittura')
        with base.open('rb') as f, uscita.open('rb') as out:
            offset = 0
            for b in iter(lambda: f.read(CHUNK), b''):
                esigi(out.read(len(b)) == blocco_modificato(b, offset, cambi), 'rilettura output fallita')
                offset += len(b)
            esigi(out.read(1) == b'', 'dati estranei in coda')
    except BaseException:
        if created:
            uscita.unlink()
        raise
    return sha_file(uscita)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--base', type=Path, required=True)
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument('--verifica', action='store_true')
    group.add_argument('--uscita', type=Path)
    ap.add_argument('--build', type=Path, default=BUILD)
    ap.add_argument('--rapporto', type=Path)
    a = ap.parse_args()
    try:
        esigi(not a.uscita or not a.uscita.exists(), 'output già presente')
        esigi(not a.rapporto or not a.rapporto.exists(), 'rapporto già presente')
        esigi(not (a.rapporto and a.uscita and a.rapporto.resolve() == a.uscita.resolve()),
              'rapporto e ROM devono avere nomi diversi')
        cambi, report = prepara(a.base, a.build)
        if a.uscita:
            report['uscita_sha256'] = scrivi(a.base, a.uscita, cambi, report['ingresso_sha256'])
        if a.rapporto:
            with a.rapporto.open('x') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
                f.write('\n')
        print(json.dumps(report, indent=2, ensure_ascii=False))
    except (Rifiuto, OSError, ValueError, KeyError) as exc:
        ap.exit(1, f'RIFIUTO: {exc}\n')


if __name__ == '__main__':
    main()
