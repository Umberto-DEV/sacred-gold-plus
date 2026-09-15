#!/usr/bin/env python3
"""Genera due aperture Squadra da avvio freddo sulla fixture Parco Nazionale."""
import argparse
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO / 'source/features/anim2/tools'))
from copioni import watch, PROLOGO_FREDDO, tocca, indietro, SQUADRA


def genera(off=False):
    prologo = PROLOGO_FREDDO
    if off:
        prologo = prologo.replace('write 0x023D8716 1 1', 'write 0x023D8716 0 1')
    return (watch() + prologo + tocca(SQUADRA, 180, 'squadra.ppm') + 'run 240\n' +
            indietro(nome='ritorno.ppm') + tocca(SQUADRA, 180, 'squadra2.ppm') +
            indietro(nome='ritorno2.ppm') + 'status\nquit\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('uscita', type=Path)
    parser.add_argument('--off', action='store_true')
    args = parser.parse_args()
    args.uscita.write_text(genera(args.off))
