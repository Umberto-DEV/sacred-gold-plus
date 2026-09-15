"""Borsa in battaglia: legge i parametri dalla cache ItemData nativa.

Un solo BL in ov008, codice stateless in 256 byte della riserva ARM9.
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

BASE, SIZE, CAN_OFF = 0x023DBD00, 256, 240
SITE, PRE = 0x02223C30, bytes.fromhex('54f6aaf8')
SYMBOLS = ('sgp_borsa_attr_cache', 'sgp_borsa_attr_hook')
REPO = Path(__file__).resolve().parents[3]
SOURCES = ('source/features/borsa-lotta/sorgenti/borsa_cache.c',
           'source/features/borsa-lotta/tools/compila.py')
ARTIFACTS = ('blob.bin', 'canarino.bin', 'manifesto.json', 'origine.json')
HOOK = {'overlay': 8, 'sito': '0x02223c30', 'pre': '54f6aaf8',
        'bersaglio': 'sgp_borsa_attr_hook'}
# I getter, la dimensione della cache e il layout devono restare compatibili.
ANCHORS = (
    ('arm9', 0x02077C18, 144, '085e4636c57c4a2c851c9db0a9ab79b546ec191631cccce604590e000b628522'),
    ('arm9', 0x02077D88, 36, '25933cb336dc608f90949ce3e2b0208dc74accec22cbadf9dcec42867410d5e6'),
    ('arm9', 0x02078138, 40, '9771f26f0f87133a03d276c9e411f6667ab50715ee3b251f529679551a2d53af'),
    (12, 0x02257E74, 36, 'b36d37794c17bf965750821244c83a5f6e9db16cfba80b3c253d89f3c951285f'),
    (8, 0x02223BF4, 224, 'd4d9fa9e2c82bae76a475da2deae4593d53f7006a46b21fe6679facdcfee6033'),
)


def _sha(data):
    return hashlib.sha256(bytes(data)).hexdigest()


def _carica_build(build):
    build = Path(build)
    try:
        sums = ''.join(_sha((build / name).read_bytes()) + '  ' + name + '\n'
                       for name in ARTIFACTS)
        esigi((build / 'SHA256SUMS').read_text() == sums,
              'BORSA LOTTA: elenco SHA256SUMS non conforme')
        origin = json.loads((build / 'origine.json').read_text())
        esigi(origin == {
            'metodo': 'compilazione da sorgenti; nessuna estrazione ROM',
            'sorgenti': {name: _sha((REPO / name).read_bytes()) for name in SOURCES},
        }, 'BORSA LOTTA: provenienza obsoleta o sorgenti impreviste; ricompilare il bundle')
        man = json.loads((build / 'manifesto.json').read_text())
        blob, can = ((build / name).read_bytes() for name in ('blob.bin', 'canarino.bin'))
        esigi(man.get('schema') == 1 and int(man['base'], 16) == BASE,
              'BORSA LOTTA: schema/base del bundle errati')
        esigi(man.get('blocco_byte') == SIZE and man.get('canarino_offset') == CAN_OFF,
              'BORSA LOTTA: pianta del bundle errata')
        esigi(man.get('gancio') == HOOK, 'BORSA LOTTA: gancio del bundle errato')
        esigi(man['blob'] == {'byte': len(blob), 'sha256': _sha(blob)} and 0 < len(blob) <= CAN_OFF,
              'BORSA LOTTA: codice non conforme al manifesto')
        expected_can = b''.join((0xCA5A1900 | i).to_bytes(4, 'little') for i in range(4))
        esigi(can == expected_can and man['canarino'] == {'byte': 16, 'sha256': _sha(can)},
              'BORSA LOTTA: canarino non conforme')
        for name in SYMBOLS:
            entry = int(man['simboli'][name], 16)
            esigi(entry & 1 and BASE <= (entry & ~1) < BASE + len(blob),
                  'BORSA LOTTA: simbolo fuori codice o non Thumb: ' + name)
        block = blob + bytes(CAN_OFF - len(blob)) + can
        return man, block
    except (OSError, ValueError, TypeError, KeyError) as exc:
        raise Rifiuto('BORSA LOTTA: bundle incompleto o malformato: %s' % exc) from exc


def _controlla_mappa(m):
    own = [b for b in m['blocchi'] if b['nome'] == 'sgp.borsa_lotta']
    esigi(len(own) == 1 and int(own[0]['base'], 16) == BASE and own[0]['bytes'] == SIZE,
          'BORSA LOTTA: prenotazione mancante o incompatibile')
    for block in m['blocchi']:
        if block['nome'] == 'sgp.borsa_lotta':
            continue
        lo = int(block['base'], 16)
        esigi(lo >= BASE + SIZE or lo + block['bytes'] <= BASE,
              'BORSA LOTTA: sovrapposizione con ' + block['nome'])


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
    with tempfile.TemporaryDirectory(prefix='sgp-borsa-lotta-') as td:
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
                  'BORSA LOTTA: contratto nativo cambiato in %s a %#x' % (module, address))
        esigi(arm.leggi(BASE, SIZE) == bytes(SIZE), 'BORSA LOTTA: riserva non vergine')
        arm.scrivi(BASE, block)
        arm.salva(path)
        after_arm = path.read_bytes()
    target = int(man['simboli']['sgp_borsa_attr_hook'], 16)
    result, patch = overlay.applica(after_arm, 8, [(SITE, PRE)],
        [{'addr': SITE, 'pre': PRE, 'post': _bl(SITE, target)}], strategia='a')
    esigi(len(result) == len(rom), 'BORSA LOTTA: dimensione ROM cambiata')
    return result, {'strumento': 'sgp12.blocchi.borsa_lotta', 'esito': 'applicato',
                    'sha256_ingresso': _sha(rom), 'sha256_uscita': _sha(result),
                    'blocco_sha256': _sha(block), 'overlay_patch': patch}


def rileggi(prima, dopo, build_dir):
    path = Path(__file__).resolve().parents[2] / 'features/borsa-lotta/tools/rileggi.py'
    spec = importlib.util.spec_from_file_location('_sgp_borsa_lotta_reader', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.rileggi(prima, dopo, build_dir)
