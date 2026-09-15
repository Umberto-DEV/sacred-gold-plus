"""Squadra in battaglia: legge i parametri dalla cache MoveTbl nativa.

Cinque BL in ov008, codice stateless in 256 byte della riserva ARM9.
"""
from __future__ import annotations
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import tempfile

from ..rom import Arm9, Rifiuto, Rom, esigi
from .. import overlay

BASE, SIZE, CAN_OFF = 0x023DBE00, 256, 240
HOOKS = [{'overlay': 8, 'sito': '0x221d3de', 'pre': '55f6a5ff', 'bersaglio': 'sgp_squadra_pp_hook'}, {'overlay': 8, 'sito': '0x221d3e8', 'pre': '55f694ff', 'bersaglio': 'sgp_squadra_attr_hook'}, {'overlay': 8, 'sito': '0x221d3f2', 'pre': '55f68fff', 'bersaglio': 'sgp_squadra_attr_hook'}, {'overlay': 8, 'sito': '0x221d3fc', 'pre': '55f68aff', 'bersaglio': 'sgp_squadra_attr_hook'}, {'overlay': 8, 'sito': '0x221d406', 'pre': '55f685ff', 'bersaglio': 'sgp_squadra_attr_hook'}]
SYMBOLS = ('sgp_squadra_attr_cache', 'sgp_squadra_attr_hook', 'sgp_squadra_pp_cache', 'sgp_squadra_pp_hook')
REPO = Path(__file__).resolve().parents[3]
SOURCES = ('source/features/squadra-lotta/sorgenti/squadra_cache.c',
           'source/features/squadra-lotta/tools/compila.py')
ARTIFACTS = ('blob.bin', 'canarino.bin', 'manifesto.json', 'origine.json')
# Getter mosse, caricamento MoveTbl e frame della scansione Squadra.
ANCHORS = [(12, 0x224868e, 36, 'b4fe6556387efbc5e85cdfc45d680092f9cde705c4f1400b964c0e5ac61a8112'), ('arm9', 34026240, 184, 'c8d498278d27f7cd82000f3ab88c53d0073b875eee7df8db84411c0803d16f20'), (8, 35770756, 692, '14f4c62e41f25d356782c0610187d1a65e69b93543fc1009a96cfa3daf78a1bd')]

def _sha(data):
    return hashlib.sha256(bytes(data)).hexdigest()


def _carica_build(build):
    build = Path(build)
    try:
        sums = ''.join(_sha((build / name).read_bytes()) + '  ' + name + '\n'
                       for name in ARTIFACTS)
        esigi((build / 'SHA256SUMS').read_text() == sums,
              'SQUADRA LOTTA: elenco SHA256SUMS non conforme')
        origin = json.loads((build / 'origine.json').read_text())
        esigi(origin == {
            'metodo': 'compilazione da sorgenti; nessuna estrazione ROM',
            'sorgenti': {name: _sha((REPO / name).read_bytes()) for name in SOURCES},
        }, 'SQUADRA LOTTA: provenienza obsoleta o sorgenti impreviste; ricompilare il bundle')
        man = json.loads((build / 'manifesto.json').read_text())
        blob, can = ((build / name).read_bytes() for name in ('blob.bin', 'canarino.bin'))
        esigi(man.get('schema') == 1 and int(man['base'], 16) == BASE,
              'SQUADRA LOTTA: schema/base del bundle errati')
        esigi(man.get('blocco_byte') == SIZE and man.get('canarino_offset') == CAN_OFF,
              'SQUADRA LOTTA: pianta del bundle errata')
        esigi(man.get('ganci') == HOOKS, 'SQUADRA LOTTA: gancio del bundle errato')
        esigi(man['blob'] == {'byte': len(blob), 'sha256': _sha(blob)} and 0 < len(blob) <= CAN_OFF,
              'SQUADRA LOTTA: codice non conforme al manifesto')
        expected_can = b''.join((0xCA5A1A00 | i).to_bytes(4, 'little') for i in range(4))
        esigi(can == expected_can and man['canarino'] == {'byte': 16, 'sha256': _sha(can)},
              'SQUADRA LOTTA: canarino non conforme')
        for name in SYMBOLS:
            entry = int(man['simboli'][name], 16)
            esigi(entry & 1 and BASE <= (entry & ~1) < BASE + len(blob),
                  'SQUADRA LOTTA: simbolo fuori codice o non Thumb: ' + name)
        block = blob + bytes(CAN_OFF - len(blob)) + can
        return man, block
    except (OSError, ValueError, TypeError, KeyError) as exc:
        raise Rifiuto('SQUADRA LOTTA: bundle incompleto o malformato: %s' % exc) from exc


def _controlla_mappa(m):
    own = [b for b in m['blocchi'] if b['nome'] == 'sgp.squadra_lotta']
    esigi(len(own) == 1 and int(own[0]['base'], 16) == BASE and own[0]['bytes'] == SIZE,
          'SQUADRA LOTTA: prenotazione mancante o incompatibile')
    for block in m['blocchi']:
        if block['nome'] == 'sgp.squadra_lotta':
            continue
        lo = int(block['base'], 16)
        esigi(lo >= BASE + SIZE or lo + block['bytes'] <= BASE,
              'SQUADRA LOTTA: sovrapposizione con ' + block['nome'])


def _bl(site, target):
    delta = (target & ~1) - (site + 4)
    esigi(not delta & 1 and -0x400000 <= delta < 0x400000, 'BL Thumb fuori portata')
    return struct.pack('<HH', 0xF000 | ((delta >> 12) & 0x7FF),
                       0xF800 | ((delta >> 1) & 0x7FF))


def applica(rom, build_dir, manifest_path=None):
    rom = bytes(rom)
    man, block = _carica_build(build_dir)
    if manifest_path is not None:
        _controlla_mappa(json.loads(Path(manifest_path).read_text()))
    container = Rom(rom)
    with tempfile.TemporaryDirectory(prefix='sgp-squadra-lotta-') as td:
        path = Path(td) / 'input.nds'
        path.write_bytes(rom)
        arm = Arm9(path)
        for module, address, size, expected in ANCHORS:
            if module == 'arm9':
                data = arm.leggi(address, size)
            else:
                info, _, image = container.immagine_overlay(module)
                off = address - info['ram']
                data = image[off:off + size]
            esigi(_sha(data) == expected,
                  'SQUADRA LOTTA: contratto nativo cambiato in %s a %#x' % (module, address))
        esigi(arm.leggi(BASE, SIZE) == bytes(SIZE), 'SQUADRA LOTTA: riserva non vergine')
        arm.scrivi(BASE, block)
        arm.salva(path)
        after_arm = path.read_bytes()
    guards = [(int(h['sito'], 16), bytes.fromhex(h['pre'])) for h in HOOKS]
    patches = [{'addr': site, 'pre': pre,
                'post': _bl(site, int(man['simboli'][h['bersaglio']], 16))}
               for h, (site, pre) in zip(HOOKS, guards)]
    result, patch = overlay.applica(after_arm, 8, guards, patches, strategia='a')
    esigi(len(result) == len(rom), 'SQUADRA LOTTA: dimensione ROM cambiata')
    return result, {'strumento': 'sgp12.blocchi.squadra_lotta', 'esito': 'applicato',
                    'sha256_ingresso': _sha(rom), 'sha256_uscita': _sha(result),
                    'blocco_sha256': _sha(block), 'overlay_patch': patch}


def rileggi(prima, dopo, build_dir):
    path = Path(__file__).resolve().parents[2] / 'features/squadra-lotta/tools/rileggi.py'
    spec = importlib.util.spec_from_file_location('_sgp_squadra_lotta_reader', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.rileggi(prima, dopo, build_dir)
