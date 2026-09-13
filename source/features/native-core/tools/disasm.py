#!/usr/bin/env python3
"""SGP-1.2-QUALITA-NATIVO-01 — disassemblato dei siti di gancio (solo lettura)."""
import hashlib, json, struct, sys
from pathlib import Path
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_ARM

RADICE = Path(__file__).resolve().parents[4]   # radice del repo
W = RADICE / 'the private development workspace'
sys.path.insert(0, str(W / 'SGP-1.2-PLUS-02/tools'))
sys.path.insert(0, str(W / 'SGP-1.2-PRESTAZIONI-NPC-03/tools'))
from arm9 import Arm9
import overlay_patch as OP

USCITA = W / 'SGP-1.2-QUALITA-NATIVO-01/prove/estratti'
ROMS = RADICE / '$SGP_ROM_DIR'
MDT = Cs(CS_ARCH_ARM, CS_MODE_THUMB); MDT.detail = True
MDA = Cs(CS_ARCH_ARM, CS_MODE_ARM);   MDA.detail = True

def sha(b): return hashlib.sha256(bytes(b)).hexdigest()

class Modulo:
    """Vista di byte con base RAM."""
    def __init__(self, nome, base, dati):
        self.nome, self.base, self.d = nome, base, bytes(dati)
    def leggi(self, ram, n):
        o = ram - self.base
        assert 0 <= o and o + n <= len(self.d), '%s: 0x%08X fuori' % (self.nome, ram)
        return self.d[o:o+n]

def modulo_arm9(a):
    # unisce i segmenti in una lookup per indirizzo
    class M:
        nome = 'arm9'
        def leggi(_s, ram, n): return a.leggi(ram, n)
    return M()

def overlay(dati, oid):
    r = OP.Rom(dati)
    v, crudo, img = r.immagine_overlay(oid)
    return Modulo('ov%03d' % oid, v['ram'], img), v

def trova_overlay(dati, ram, n=4):
    """Overlay che contengono l'indirizzo."""
    r = OP.Rom(dati); out = []
    for i in range(r.n_overlay):
        v = r.voce_overlay(i)
        if v['ram'] <= ram and ram + n <= v['ram'] + v['ram_size']:
            out.append(i)
    return out

def righe(md, dati, base):
    out = []
    for i in md.disasm(dati, base):
        b = ' '.join('%02x' % x for x in i.bytes)
        out.append((i.address, i.size, b, i.mnemonic, i.op_str))
    return out

def finestra_thumb(mod, sito, prima=8, dopo=8):
    """Disassembla in Thumb ~`prima` istruzioni prima di `sito` e `dopo` dopo.
    Cerca l'allineamento: parte da sito-2*prima*2 e scende finche' la catena
    tocca esattamente `sito`."""
    span_pre = 4 * prima + 8
    for delta in range(span_pre, 0, -2):
        inizio = sito - delta
        try:
            dati = mod.leggi(inizio, delta + 4 * dopo + 8)
        except AssertionError:
            continue
        r = righe(MDT, dati, inizio)
        idx = [k for k, x in enumerate(r) if x[0] == sito]
        if not idx:
            continue
        k = idx[0]
        if k >= prima:
            return r[k-prima:k+dopo+1], k-(k-prima)
    # ripiego: nessun allineamento trovato, parte dal sito
    dati = mod.leggi(sito, 4 * dopo + 8)
    return righe(MDT, dati, sito), 0

def finestra_arm(mod, sito, prima=8, dopo=8):
    inizio = sito - 4 * prima
    dati = mod.leggi(inizio, 4 * (prima + dopo + 1))
    return righe(MDA, dati, inizio), prima

def stampa(f, titolo, r, k_sito, sito):
    f.write('\n%s\n' % titolo)
    f.write('%s\n' % ('-' * len(titolo)))
    for n, (a, sz, b, mn, ops) in enumerate(r):
        marca = '>>>' if a == sito else '   '
        f.write('%s 0x%08X  %-11s  %-8s %s\n' % (marca, a, b, mn, ops))

# --------------------------------------------------------------------- siti
SITI = [
    # (chiave, titolo, modulo, indirizzo, modo)
    ('trainer-1', 'gancio livello allenatore #1', 'arm9',  0x02073718, 'thumb'),
    ('trainer-2', 'gancio livello allenatore #2', 'arm9',  0x02073802, 'thumb'),
    ('trainer-3', 'gancio livello allenatore #3', 'arm9',  0x0207390C, 'thumb'),
    ('trainer-4', 'gancio livello allenatore #4', 'arm9',  0x02073A0C, 'thumb'),
    ('wild',      'gancio selvatici (ov002)',     'ov002', 0x02247D3A, 'thumb'),
    ('npc',       'gancio tetto NPC (ov001)',     'ov001', 0x021FA570, 'thumb'),
    ('wifi-g1',   'gancio WiFi G1 (arm9)',        'arm9',  0x020070A8, 'thumb'),
    ('wifi-g2',   'sito WiFi G2 (ov000, copia ROM)', 'ov000', 0x021FC150, 'arm'),
    ('wifi-g3',   'sito WiFi G3 (ov000, copia ROM)', 'ov000', 0x021EC4A4, 'arm'),
    ('salva-1',   'gancio chunk salvataggio #1 (SaveData_Init)', 'arm9', 0x020271F8, 'thumb'),
    ('salva-2',   'gancio chunk salvataggio #2 (SaveData_Save)', 'arm9', 0x02027456, 'thumb'),
    ('camera',    'sito accessore camera (arm9)', 'arm9',  0x0203B400, 'thumb'),
]

TRAMPOLINE = [
    ('sgp_trainer_hook',   0x023D82E4, 'thumb', 'SGP-1.2-PLUS-02', 96),
    ('sgp_wild_hook',      0x023D8340, 'thumb', 'SGP-1.2-PLUS-02', 96),
    ('sgp_npc_hook',       0x023D8970, 'thumb', 'SGP-1.2-PRESTAZIONI-NPC-02', 84),
    ('sgp_wfc_trampolino', 0x023DA4B4, 'thumb', 'SGP-1.2-WIFI-04', 48),
    ('sgp_gancio_carica',  0x023D8730, 'thumb', 'SGP-1.2-PLUS-03', 64),
    ('sgp_gancio_salva',   0x023D8858, 'thumb', 'SGP-1.2-PLUS-03', 64),
    ('camera-codice',      0x023DEB8C, 'thumb', 'SGP-1.1-CAMTOGGLE-01 (zona 1.1)', 84),
]

def main():
    indice = {'strumento': 'SGP-1.2-QUALITA-NATIVO-01 disasm.py', 'file': {}, 'siti': {}}
    rom_dati, mods = {}, {}
    for et, nome in (('EN', 'sgp-1.2-EN.nds'), ('IT', 'sgp-1.2-IT.nds'),
                     ('base-EN', 'base-1.1-EN.nds'), ('base-IT', 'base-1.1-IT.nds')):
        d = (ROMS / nome).read_bytes()
        rom_dati[et] = d
        a = Arm9(ROMS / nome)
        m = {'arm9': modulo_arm9(a)}
        for oid in (0, 1, 2):
            m['ov%03d' % oid] = overlay(d, oid)[0]
        mods[et] = m
    # controllo: quale overlay contiene davvero ogni indirizzo
    indice['overlay_candidati'] = {}
    for chiave, tit, mod, ram, modo in SITI:
        if mod.startswith('ov'):
            indice['overlay_candidati'][chiave] = trova_overlay(rom_dati['EN'], ram)

    for chiave, tit, mod, ram, modo in SITI:
        f = USCITA / ('disasm-%s.txt' % chiave)
        with f.open('w') as fh:
            fh.write('# %s — %s @ 0x%08X (%s, modulo %s)\n' % (chiave, tit, ram, modo.upper(), mod))
            fh.write('# 8 istruzioni prima, il sito (>>>), 8 dopo. Lavoro vs base 1.1.\n')
            per_et = {}
            for et in ('EN', 'base-EN', 'IT', 'base-IT'):
                m = mods[et][mod]
                try:
                    r, k = (finestra_thumb if modo == 'thumb' else finestra_arm)(m, ram)
                except AssertionError as e:
                    fh.write('\n%s: NON MAPPATO (%s)\n' % (et, e)); continue
                stampa(fh, '== %s (%s)' % (et, mod), r, k, ram)
                sito_b = m.leggi(ram, 4)
                per_et[et] = {'byte_sito_4': sito_b.hex(),
                              'istruzione_sito': next(('%s %s' % (x[3], x[4]) for x in r if x[0] == ram), None),
                              'successiva': next(('0x%08X %s %s' % (x[0], x[3], x[4]) for x in r if x[0] > ram), None)}
            fh.write('\n== confronto byte del sito (4 B)\n')
            for et, v in per_et.items():
                fh.write('   %-8s %s   %s\n' % (et, v['byte_sito_4'], v['istruzione_sito']))
        indice['siti'][chiave] = {'titolo': tit, 'ram': '0x%08X' % ram, 'modo': modo,
                                  'modulo': mod, 'file': f.name, 'per_rom': per_et}
        print('scritto', f.name)

    # trampoline nei blob
    f = USCITA / 'disasm-trampoline.txt'
    with f.open('w') as fh:
        fh.write('# trampoline dentro i blob della riserva (indirizzi dai manifesti "simboli")\n')
        for nome, ram, modo, pacc, n in TRAMPOLINE:
            for et in ('EN', 'IT'):
                m = mods[et]['arm9']
                d = m.leggi(ram, n)
                fh.write('\n== %s @ 0x%08X (%s) — %s — %s, %d B  sha %s\n'
                         % (nome, ram, modo, pacc, et, n, sha(d)[:16]))
                for a, sz, b, mn, ops in righe(MDT if modo == 'thumb' else MDA, d, ram):
                    fh.write('   0x%08X  %-11s  %-8s %s\n' % (a, b, mn, ops))
        indice['trampoline'] = [{'nome': x[0], 'ram': '0x%08X' % x[1], 'modo': x[2],
                                 'pacchetto': x[3], 'bytes': x[4]} for x in TRAMPOLINE]
    print('scritto', f.name)

    # veneer ARM WiFi
    f = USCITA / 'disasm-veneer-wifi.txt'
    with f.open('w') as fh:
        for nome, ram, n in (('veneer G2', 0x023DA000, 24), ('veneer G3', 0x023DA020, 28)):
            for et in ('EN', 'IT'):
                d = mods[et]['arm9'].leggi(ram, n)
                fh.write('\n== %s @ 0x%08X (ARM) — %s, %d B  sha %s\n' % (nome, ram, et, n, sha(d)[:16]))
                for a, sz, b, mn, ops in righe(MDA, d, ram):
                    fh.write('   0x%08X  %-11s  %-8s %s\n' % (a, b, mn, ops))
                fh.write('   parole: %s\n' % ' '.join('0x%08X' % x for x in struct.unpack('<%dI' % (n//4), d)))
    print('scritto', f.name)
    indice['veneer'] = {'file': 'disasm-veneer-wifi.txt'}
    (USCITA / 'INDICE.json').write_text(json.dumps(indice, indent=1, ensure_ascii=False))
    print(json.dumps(indice['overlay_candidati'], indent=1))

main()
