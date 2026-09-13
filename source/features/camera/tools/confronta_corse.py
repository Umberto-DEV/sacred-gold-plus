#!/usr/bin/env python3
"""Verdetti sulle corse: chi deve essere identico a chi, e chi deve differire.

    python3 tools/confronta_corse.py <dir delle corse> [--json f]

Ogni riga e' un'asserzione dichiarata PRIMA (CRITERI.md §6). Un confronto che
«deve differire» e' un controllo che puo' fallire: senza, «identici» sarebbe un
esito che non puo' fallire.
"""
import argparse, hashlib, json, sys
from pathlib import Path

ASSERZIONI = [
    # (nome, corsa A, corsa B, fotogramma, 'uguali'|'diversi', perche')
    ('C-1 non-regressione, campo', 'nb-F0', 'nb-cand', '01-campo.ppm', 'uguali',
     'la mappa 60 non e\' toccata: la candidata deve essere indistinguibile dalla base'),
    ('C-1 non-regressione, campo fermo', 'nb-F0', 'nb-cand', '02-campo-fermo.ppm', 'uguali', ''),
    ('C-1 non-regressione, titolo', 'nb-F0', 'nb-cand', '00-titolo.ppm', 'uguali', ''),
    ('C-1 non-regressione, laboratorio', 'lab-F0', 'lab-cand', '10-lab.ppm', 'uguali',
     'la mappa 61 non e\' fra le 24 eccezioni: nessun cambiamento'),
    ('C-1 non-regressione, laboratorio fermo', 'lab-F0', 'lab-cand', '11-lab-fermo.ppm', 'uguali', ''),
    ('C-3 il cheat globale funziona ancora', 'lab-cand', 'lab-cand-classic', '10-lab.ppm', 'diversi',
     'con Classic la mappa 61 torna al nativo 4: se non differisse, il gancio non e\' chiamato'),
    ('C-4a la tabella governa la camera (profilo 0)', 'lab-cand', 'lab-d61-0', '10-lab.ppm', 'diversi',
     'un\'eccezione 61->0 deve cambiare lo schermo rispetto al Plus 11'),
    ('C-4b la tabella governa la camera (profilo 4)', 'lab-cand', 'lab-d61-4', '10-lab.ppm', 'diversi',
     'un\'eccezione 61->4 deve cambiare lo schermo rispetto al Plus 11'),
    ('C-4c due strade allo stesso profilo 4', 'lab-cand-classic', 'lab-d61-4', '10-lab.ppm', 'uguali',
     'Classic globale (nativo 4) ed eccezione 61->4 devono dare LO STESSO schermo: '
     'e\' il controllo che puo\' fallire'),
    ('C-4d due strade allo stesso profilo 4, fermo', 'lab-cand-classic', 'lab-d61-4',
     '11-lab-fermo.ppm', 'uguali', ''),
    ('C-4e i due profili non si confondono', 'lab-d61-0', 'lab-d61-4', '10-lab.ppm', 'diversi',
     'profilo 0 e profilo 4 devono essere schermi diversi'),
    ('C-5 percorso-lotta identico', 'pl-base', 'pl-cand', 'frames.csv', 'uguali',
     '31 298 fotogrammi di lotta, menu e transizioni: nessuna differenza'),
    ('C-5 percorso-lotta, prima della lotta', 'pl-base', 'pl-cand', 'PRIMA-LOTTA.ppm', 'uguali', ''),
    ('C-5 percorso-lotta, in lotta', 'pl-base', 'pl-cand', 'IN-LOTTA.ppm', 'uguali', ''),
    ('C-1 IT, non-regressione', 'it-base', 'it-cand', '01-campo.ppm', 'uguali',
     'ROM IT, salvataggio reale della Thor'),
    ('C-1 IT, non-regressione fermo', 'it-base', 'it-cand', '02-campo-fermo.ppm', 'uguali', ''),
]


def sha(p):
    try:
        return hashlib.sha256(Path(p).read_bytes()).hexdigest()
    except FileNotFoundError:
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('corse'); ap.add_argument('--json')
    a = ap.parse_args()
    D = Path(a.corse)
    fuori, rosso, saltate = [], [], []
    for nome, x, y, f, atteso, perche in ASSERZIONI:
        sx, sy = sha(D / x / f), sha(D / y / f)
        if sx is None or sy is None:
            saltate.append(nome)
            print('  SALTATA  %-42s (manca %s)' % (nome, f if sx is None else f))
            fuori.append({'asserzione': nome, 'esito': 'SALTATA'})
            continue
        uguali = sx == sy
        ok = uguali if atteso == 'uguali' else not uguali
        print('  %-7s  %-42s %s %s %s  [%s]'
              % ('VERDE' if ok else 'ROSSO', nome, x, '==' if uguali else '!=', y, atteso))
        fuori.append({'asserzione': nome, 'a': x, 'b': y, 'fotogramma': f,
                      'atteso': atteso, 'sha_a': sx[:16], 'sha_b': sy[:16],
                      'esito': 'VERDE' if ok else 'ROSSO', 'perche': perche})
        if not ok:
            rosso.append(nome)
    print('\n%d asserzioni, %d verdi, %d rosse, %d saltate'
          % (len(ASSERZIONI), len(ASSERZIONI) - len(rosso) - len(saltate), len(rosso), len(saltate)))
    if a.json:
        Path(a.json).write_text(json.dumps({'asserzioni': fuori, 'rosse': rosso,
                                            'saltate': saltate}, indent=1))
    return 1 if rosso else 0


if __name__ == '__main__':
    sys.exit(main())
