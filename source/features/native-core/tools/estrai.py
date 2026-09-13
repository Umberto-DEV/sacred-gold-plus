#!/usr/bin/env python3
"""SGP-1.2-QUALITA-NATIVO-01 — estrazione dei byte APPLICATI (solo lettura).

Riusa Arm9 (SGP-1.2-PLUS-02/tools/arm9.py) e Rom/blz (SGP-1.2-OVERLAY-01 via
SGP-1.2-PRESTAZIONI-NPC-03/tools/overlay_patch.py). Non scrive mai sulle ROM.
"""
import hashlib, json, struct, sys
from pathlib import Path

RADICE = Path('<home>/Developer/sacred-gold-plus')
W = RADICE / 'the private development workspace'
sys.path.insert(0, str(W / 'SGP-1.2-PLUS-02/tools'))
sys.path.insert(0, str(W / 'SGP-1.2-PRESTAZIONI-NPC-03/tools'))
from arm9 import Arm9                      # noqa: E402
import overlay_patch as OP                 # noqa: E402

USCITA = W / 'SGP-1.2-QUALITA-NATIVO-01/prove/estratti'
USCITA.mkdir(parents=True, exist_ok=True)
ROMS = RADICE / '$SGP_ROM_DIR'

def sha(b): return hashlib.sha256(bytes(b)).hexdigest()

# ------------------------------------------------------------- blocchi ARM9
# (nome_file, indirizzo, byte, descrizione)
BLOCCHI = [
    ('blocco-sgp.plus',        0x023D8100, 2048, 'blocco sgp.plus intero'),
    ('blob-plus',              0x023D8100,  592, 'blob PLUS (Thumb), +0x000'),
    ('tab-trainer',            0x023D8500,  256, 'tab_trainer, +0x400'),
    ('tab-wild',               0x023D8600,  256, 'tab_wild, +0x500'),
    ('stato-plus',             0x023D8700,   32, 'stato PLUS, +0x600'),
    ('canarino-plus',          0x023D8720,   16, 'canarino 0xCA5A1200|i, +0x620'),
    ('blob-salvataggio',       0x023D8730,  460, 'blob chunk salvataggio, +0x630'),
    ('blocco-sgp.salvataggio', 0x023D8F00,  256, 'blocco sgp.salvataggio'),
    ('canarino-salvataggio',   0x023D8FF0,   16, 'canarino 0xCA5A1300|i in sgp.salvataggio'),
    ('blocco-sgp.npc',         0x023D8900,  256, 'blocco sgp.npc'),
    ('blob-npc',               0x023D8900,  128, 'blob tetto NPC'),
    ('stato-npc',              0x023D89E0,   16, 'stato NPC'),
    ('canarino-npc',           0x023D8A00,   16, 'canarino.npc 0xCA5A1300|i'),
    ('blocco-sgp.wifi',        0x023DA000, 2048, 'blocco sgp.wifi'),
    ('veneer-g2',              0x023DA000,   24, 'veneer ARM G2'),
    ('veneer-g3',              0x023DA020,   28, 'veneer ARM G3'),
    ('stato-wifi',             0x023DA240,   32, 'stato W1'),
    ('blob-wifi_slot4',        0x023DA250,  660, 'blob wifi_slot4 (Thumb)'),
    ('camera-eccezioni-1.2',   0x023D8040,   48, 'tabella eccezioni camera, 24 voci u16'),
    ('canarino-camera',        0x023D8070,   16, 'canarino.camera 0xCA5A1100|i'),
    ('camera-codice',          0x023DEB8C,   84, 'gancio camera (zona 1.1) + pool'),
    ('camera-sito',            0x0203B400,    4, 'sito di gancio camera (ARM9 statico)'),
    ('camera-pool-letterale',  0x023DEBCC,   20, 'pool letterale del gancio camera'),
    ('camera-letterale-sito',  0x0203B418,    4, 'letterale del sito 0x0203B400'),
    ('intestazione-riserva',   0x023D8020,   32, 'intestazione riserva 1.2 (SGP2)'),
    ('canarino-basso',         0x023D8000,   32, 'canarino basso 0xCA5A1000|i'),
    ('canarino-1.1',           0x023DEB40,   32, 'canarino 1.1 0xCA5A0000|i'),
]

def canar(b, motivo):
    n = len(b) // 4
    atteso = b''.join(struct.pack('<I', motivo | i) for i in range(n))
    return bytes(b) == atteso

MOTIVI = {'canarino-basso': 0xCA5A1000, 'canarino-camera': 0xCA5A1100,
          'canarino-plus': 0xCA5A1200, 'canarino-npc': 0xCA5A1300,
          'canarino-salvataggio': 0xCA5A1300, 'canarino-1.1': 0xCA5A0000}

def estrai_rom(etichetta, rom_path):
    a = Arm9(rom_path)
    res = {'rom': str(rom_path), 'sha256_rom': sha(a.raw), 'bytes_rom': len(a.raw),
           'sezioni_autoload': [{'ram': '0x%08X' % s[0], 'bytes': s[1], 'bss': s[2]} for s in a.sezioni],
           'blocchi': {}}
    for nome, ram, n, desc in BLOCCHI:
        try:
            b = a.leggi(ram, n)
        except KeyError as e:
            res['blocchi'][nome] = {'errore': str(e)}
            continue
        f = USCITA / ('%s-%s.bin' % (nome, etichetta))
        f.write_bytes(b)
        v = {'ram': '0x%08X' % ram, 'bytes': n, 'sha256': sha(b),
             'descrizione': desc, 'file': f.name,
             'tutto_zero': all(x == 0 for x in b)}
        if nome in MOTIVI:
            v['canarino_corretto'] = canar(b, MOTIVI[nome])
        res['blocchi'][nome] = v
    return a, res

# ------------------------------------------------------------------ overlay
def img_overlay(dati, oid):
    r = OP.Rom(dati)
    v, crudo, img = r.immagine_overlay(oid)
    return v, img

def main():
    indice = {'strumento': 'SGP-1.2-QUALITA-NATIVO-01 estrai.py', 'rom': {}}
    arm9 = {}
    for et, nome in (('EN', 'sgp-1.2-EN.nds'), ('IT', 'sgp-1.2-IT.nds'),
                     ('base-EN', 'base-1.1-EN.nds'), ('base-IT', 'base-1.1-IT.nds')):
        p = ROMS / nome
        if et.startswith('base'):
            a = Arm9(p)
            indice['rom'][et] = {'rom': str(p), 'sha256_rom': sha(a.raw),
                                 'bytes_rom': len(a.raw),
                                 'sezioni_autoload': [{'ram': '0x%08X' % s[0], 'bytes': s[1], 'bss': s[2]} for s in a.sezioni]}
        else:
            a, r = estrai_rom(et, p)
            indice['rom'][et] = r
        arm9[et] = a
    (USCITA / 'ESTRATTI.json').write_text(json.dumps(indice, indent=1, ensure_ascii=False))
    # confronto EN/IT
    conf = {}
    for nome, ram, n, desc in BLOCCHI:
        e = indice['rom']['EN']['blocchi'].get(nome, {})
        i = indice['rom']['IT']['blocchi'].get(nome, {})
        conf[nome] = {'ram': '0x%08X' % ram, 'bytes': n,
                      'sha_EN': e.get('sha256'), 'sha_IT': i.get('sha256'),
                      'uguali': e.get('sha256') == i.get('sha256')}
    (USCITA / 'CONFRONTO-EN-IT.json').write_text(json.dumps(conf, indent=1))
    for k, v in conf.items():
        print('%-26s %-12s %5d  %-8s %s' % (k, v['ram'], v['bytes'],
              'UGUALI' if v['uguali'] else 'DIVERSI', (v['sha_EN'] or '?')[:16]))

main()
