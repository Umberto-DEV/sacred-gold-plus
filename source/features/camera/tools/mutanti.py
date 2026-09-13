#!/usr/bin/env python3
"""MUTANTI — ogni mutante deve essere ucciso da un cancello NOMINATO.

Un mutante ucciso dal cancello sbagliato conta come non ucciso: e' un cancello
che passa per caso, ed e' esattamente il difetto che i mutanti cercano.

    python3 tools/mutanti.py <base.nds> <dir di lavoro> [--json f]

I mutanti di tipo «tabella» passano per l'applicatore vero con una tabella
alterata; quelli di tipo «immagine» alterano la ROM d'ingresso o l'uscita e
vengono passati al rilettore o all'applicatore.  Nessun byte di ROM in uscita.
"""
import argparse, json, shutil, struct, subprocess, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from arm9 import Arm9
import tabella as T

PY = sys.executable
QUI = Path(__file__).resolve().parent


def tab_str(d):
    return ','.join('%d:%d' % (k, v) for k, v in sorted(d.items()))


def applica(base, uscita, tabella=None):
    cmd = [PY, str(QUI / 'applica_camera.py'), str(base), str(uscita)]
    if tabella is not None:
        cmd += ['--tabella', tabella]
    p = subprocess.run(cmd, capture_output=True, text=True)
    return p.returncode, p.stdout + p.stderr


def rileggi(base, cand, attese=None):
    cmd = [PY, str(QUI / 'rileggi_camera.py'), str(base), str(cand)]
    if attese is not None:
        cmd += ['--attese', attese]
    p = subprocess.run(cmd, capture_output=True, text=True)
    return p.returncode, p.stdout + p.stderr


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('base'); ap.add_argument('lavoro'); ap.add_argument('--json')
    a = ap.parse_args()
    L = Path(a.lavoro); L.mkdir(parents=True, exist_ok=True)
    base = Path(a.base)

    # la candidata sana, che serve da ingresso ai mutanti «di immagine»
    sana = L / 'sana.nds'
    rc, _ = applica(base, sana)
    assert rc == 0, 'la candidata sana non si applica'

    mutanti = []

    def tabella_mutata(nome, d, cancello):
        rc, out = applica(base, L / ('m-%s.nds' % nome), tab_str(d))
        ucciso = rc == 2 and (cancello + ':') in out
        mutanti.append({'mutante': nome, 'tipo': 'tabella', 'cancello_atteso': cancello,
                        'rc': rc, 'ucciso': ucciso,
                        'riga': next((l for l in out.splitlines() if 'RIFIUTATO' in l), out.strip()[:120])})

    # --- M1..M7: la tabella
    m = dict(T.CANONICA); m[116] = 20
    tabella_mutata('M2-valore-oltre-15', m, 'G5')
    m = dict(T.CANONICA); m.pop(119)
    tabella_mutata('M4-manca-una-nuova', m, 'G5')
    m = dict(T.CANONICA); m[226] = 11
    tabella_mutata('M5-vecchia-alterata', m, 'G5')
    m = dict(T.CANONICA); m.pop(2)
    tabella_mutata('M6-23-voci', m, 'G5')
    m = dict(T.CANONICA); m[300] = 0
    tabella_mutata('M7-25-voci', m, 'G5')
    m = dict(T.CANONICA); m[117] = 4                  # 116 e 117 nello stesso blocco di 16
    m.pop(2)
    tabella_mutata('M3-blocco-condiviso', m, 'G5')
    m = dict(T.CANONICA); m[600] = 0; m.pop(2)
    tabella_mutata('M1-id-fuori-intervallo', m, 'G5')

    # --- M8: preimmagine sbagliata (tabella vecchia alterata nella ROM d'ingresso)
    r = Arm9(base); r.scrivi(0x023DEB6C, struct.pack('<H', (3 << 4) | 4)); r.salva(L / 'm8.nds')
    rc, out = applica(L / 'm8.nds', L / 'm-M8.nds')
    mutanti.append({'mutante': 'M8-preimmagine-tabella-vecchia', 'tipo': 'immagine',
                    'cancello_atteso': 'G4', 'rc': rc, 'ucciso': rc == 2 and 'G4:' in out,
                    'riga': next((l for l in out.splitlines() if 'RIFIUTATO' in l), '')})

    # --- M9: canarino 1.1 alterato nella ROM d'ingresso
    r = Arm9(base); r.scrivi(0x023DEB40, b'\x00\x00\x00\x00'); r.salva(L / 'm9.nds')
    rc, out = applica(L / 'm9.nds', L / 'm-M9.nds')
    mutanti.append({'mutante': 'M9-canarino-alterato', 'tipo': 'immagine',
                    'cancello_atteso': 'G3', 'rc': rc, 'ucciso': rc == 2 and 'G3:' in out,
                    'riga': next((l for l in out.splitlines() if 'RIFIUTATO' in l), '')})

    # --- M10: il gancio alterato (un byte di codice)
    r = Arm9(base); r.scrivi(0x023DEB9B, b'\xff'); r.salva(L / 'm10.nds')
    rc, out = applica(L / 'm10.nds', L / 'm-M10.nds')
    mutanti.append({'mutante': 'M10-gancio-alterato', 'tipo': 'immagine',
                    'cancello_atteso': 'G2', 'rc': rc, 'ucciso': rc == 2 and 'G2:' in out,
                    'riga': next((l for l in out.splitlines() if 'RIFIUTATO' in l), '')})

    # --- M11: il sito dell'accessore non innestato
    r = Arm9(base); r.scrivi(0x0203B400, b'\x08\xb5\xff\xf7'); r.salva(L / 'm11.nds')
    rc, out = applica(L / 'm11.nds', L / 'm-M11.nds')
    mutanti.append({'mutante': 'M11-sito-non-innestato', 'tipo': 'immagine',
                    'cancello_atteso': 'G2', 'rc': rc, 'ucciso': rc == 2 and 'G2:' in out,
                    'riga': next((l for l in out.splitlines() if 'RIFIUTATO' in l), '')})

    # --- M12: stato camera spento nella ROM d'ingresso -> G9a (invariante PRE-scrittura)
    r = Arm9(base); r.scrivi(0x023DFFFC, b'\x00\x00\x00\x00'); r.salva(L / 'm12.nds')
    rc, out = applica(L / 'm12.nds', L / 'm-M12.nds')
    mutanti.append({'mutante': 'M12-stato-spento', 'tipo': 'immagine',
                    'cancello_atteso': 'G9a', 'rc': rc, 'ucciso': rc == 2 and 'G9a:' in out,
                    'riga': next((l for l in out.splitlines() if 'RIFIUTATO' in l), '')})

    # --- M13: riapplicazione: deve fermarla G0, non un altro cancello
    rc, out = applica(sana, L / 'm-M13.nds')
    mutanti.append({'mutante': 'M13-riapplicazione', 'tipo': 'immagine',
                    'cancello_atteso': 'G0', 'rc': rc,
                    'ucciso': rc == 3 and "GIA' APPLICATO" in out,
                    'riga': next((l for l in out.splitlines() if 'APPLICATO' in l), '')})

    # --- M14..M18: mutanti che il RILETTORE deve uccidere sull'USCITA
    def uscita_mutata(nome, ram, dati, cancello):
        shutil.copy(sana, L / ('u-%s.nds' % nome))
        r = Arm9(L / ('u-%s.nds' % nome)); r.scrivi(ram, dati); r.salva(L / ('u-%s.nds' % nome))
        rc, out = rileggi(base, L / ('u-%s.nds' % nome))
        rossi = [l.split()[0] for l in out.splitlines() if ' ROSSO ' in l]
        mutanti.append({'mutante': nome, 'tipo': 'uscita', 'cancello_atteso': cancello,
                        'rc': rc, 'ucciso': rc == 1 and cancello in rossi,
                        'riga': 'ROSSI: %s' % ','.join(rossi)})

    uscita_mutata('M14-letterale-non-aggiornato', 0x023DEBD4, struct.pack('<I', 0x023DEB6C), 'R0')
    uscita_mutata('M15-letterale-fine-alterato', 0x023DEBD8, struct.pack('<I', 0x023D8090), 'R2')
    uscita_mutata('M16-una-voce-sbagliata', 0x023D8040 + 8, struct.pack('<H', 0x7741), 'R3')
    uscita_mutata('M17-canarino-1.1-invaso', 0x023DEB50, b'\xff\xff\xff\xff', 'R4')
    uscita_mutata('M29-canarino-di-coda-mancante', 0x023D8070, b'\x00\x00\x00\x00', 'R4')
    uscita_mutata('M30-tabella-1.1-dismessa-toccata', 0x023DEB6C, b'\xff\xff', 'R5')
    uscita_mutata('M18-repellente-alterato', 0x023DEBE0, b'\x00', 'R5')
    uscita_mutata('M19-map-header-alterato', 0x020F6BE0 + 24 * 119 + 20, b'\x00\xb0\x00\x00', 'R6')
    uscita_mutata('M20-stato-spento', 0x023DFFFC, b'\x00\x00\x00\x00', 'R5')

    # --- M21: un byte fuori dall'ARM9 -> R7
    p = L / 'u-M21.nds'
    shutil.copy(sana, p)
    b = bytearray(p.read_bytes()); b[len(b) - 1] ^= 0xFF; p.write_bytes(bytes(b))
    rc, out = rileggi(base, p)
    rossi = [l.split()[0] for l in out.splitlines() if ' ROSSO ' in l]
    mutanti.append({'mutante': 'M21-byte-fuori-arm9', 'tipo': 'uscita', 'cancello_atteso': 'R7',
                    'rc': rc, 'ucciso': rc == 1 and 'R7' in rossi, 'riga': 'ROSSI: %s' % ','.join(rossi)})

    # --- M24: un byte della riserva che nessun cancello fine copre -> lo prende G1
    r = Arm9(base); r.scrivi(0x023DEF00, b'\xff'); r.salva(L / 'm24.nds')
    rc, out = applica(L / 'm24.nds', L / 'm-M24.nds')
    mutanti.append({'mutante': 'M24-riserva-alterata-altrove', 'tipo': 'immagine',
                    'cancello_atteso': 'G1', 'rc': rc, 'ucciso': rc == 2 and 'G1:' in out,
                    'riga': next((l for l in out.splitlines() if 'RIFIUTATO' in l), '')})

    # --- M25: canarino basso 1.2 alterato -> G11
    r = Arm9(base); r.scrivi(0x023D8000, b'\xff'); r.salva(L / 'm25.nds')
    rc, out = applica(L / 'm25.nds', L / 'm-M25.nds')
    mutanti.append({'mutante': 'M25-canarino-basso-1.2', 'tipo': 'immagine',
                    'cancello_atteso': 'G11', 'rc': rc, 'ucciso': rc == 2 and 'G11:' in out,
                    'riga': next((l for l in out.splitlines() if 'RIFIUTATO' in l), '')})

    # --- M26: qualcuno ha gia' occupato la zona libera 1.2 -> G11
    r = Arm9(base); r.scrivi(0x023D9000, b'\x01'); r.salva(L / 'm26.nds')
    rc, out = applica(L / 'm26.nds', L / 'm-M26.nds')
    mutanti.append({'mutante': 'M26-zona-1.2-gia-occupata', 'tipo': 'immagine',
                    'cancello_atteso': 'G11', 'rc': rc, 'ucciso': rc == 2 and 'G11:' in out,
                    'riga': next((l for l in out.splitlines() if 'RIFIUTATO' in l), '')})

    # --- M27: intestazione SGP2 rovinata -> G11
    r = Arm9(base); r.scrivi(0x023D8020, b'XXXX'); r.salva(L / 'm27.nds')
    rc, out = applica(L / 'm27.nds', L / 'm-M27.nds')
    mutanti.append({'mutante': 'M27-intestazione-rovinata', 'tipo': 'immagine',
                    'cancello_atteso': 'G11', 'rc': rc, 'ucciso': rc == 2 and 'G11:' in out,
                    'riga': next((l for l in out.splitlines() if 'RIFIUTATO' in l), '')})

    # --- M28: letterale d'arena non abbassato (base incoerente) -> G9a
    r = Arm9(base); r.scrivi(0x020D2BB0, struct.pack('<I', 0x023DEB40)); r.salva(L / 'm28.nds')
    rc, out = applica(L / 'm28.nds', L / 'm-M28.nds')
    mutanti.append({'mutante': 'M28-arena-non-abbassata', 'tipo': 'immagine',
                    'cancello_atteso': 'G9a', 'rc': rc, 'ucciso': rc == 2 and 'G9a:' in out,
                    'riga': next((l for l in out.splitlines() if 'RIFIUTATO' in l), '')})

    # --- M22: la scappatoia diagnostica non deve valere da sola
    import subprocess as _s
    q = _s.run([PY, str(QUI / 'applica_camera.py'), str(base), str(L / 'm-M22.nds'),
                '--diagnostica'], capture_output=True, text=True)
    mutanti.append({'mutante': 'M22-diagnostica-senza-tabella', 'tipo': 'uso',
                    'cancello_atteso': 'uso', 'rc': q.returncode,
                    'ucciso': q.returncode == 2 and 'vale solo insieme' in q.stdout,
                    'riga': q.stdout.strip().splitlines()[0] if q.stdout.strip() else ''})

    # --- M23: --diagnostica rilassa SOLO il cancello canonico, non la forma
    m = dict(T.CANONICA); m[116] = 20
    q = _s.run([PY, str(QUI / 'applica_camera.py'), str(base), str(L / 'm-M23.nds'),
                '--tabella', tab_str(m), '--diagnostica'], capture_output=True, text=True)
    mutanti.append({'mutante': 'M23-diagnostica-non-rilassa-la-forma', 'tipo': 'uso',
                    'cancello_atteso': 'G5', 'rc': q.returncode,
                    'ucciso': q.returncode == 2 and 'G5:' in q.stdout,
                    'riga': next((l for l in q.stdout.splitlines() if 'RIFIUTATO' in l), '')})

    vivi = [m['mutante'] for m in mutanti if not m['ucciso']]
    for m in mutanti:
        print('  %-32s %-4s  %s  %s' % (m['mutante'], m['cancello_atteso'],
                                        'UCCISO' if m['ucciso'] else 'VIVO  ', m['riga'][:90]))
    print('\n%d mutanti, %d uccisi, %d vivi' % (len(mutanti), len(mutanti) - len(vivi), len(vivi)))
    if a.json:
        Path(a.json).write_text(json.dumps(
            {'generati': len(mutanti), 'uccisi': len(mutanti) - len(vivi),
             'sopravvissuti': vivi, 'mutanti': mutanti}, indent=1))
    return 0 if not vivi else 1


if __name__ == '__main__':
    sys.exit(main())
