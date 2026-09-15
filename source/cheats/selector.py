"""Add the melonDS Pokémon/level picker to a supplied SGP cheat catalogue.

The catalogue itself is an external release input. No ROM is read here.
"""
import argparse
from pathlib import Path
import xml.etree.ElementTree as ET


LEGACY_SPECIES_CODES = frozenset(['94000130 FCFF0000 6211186C 00000000 B211186C 00000000 0000DCF4 01ED0001 0000DCF8 00640002 D2000000 00000000 94000130 FDFF0000 6211186C 00000000 B211186C 00000000 DA000000 0000DCF6 C0000000 00000027 D7000000 00032A48 D2000000 00000000 94000130 FDFF0000 6211186C 00000000 B211186C 00000000 DB000000 0000DCFA C0000000 0000000B D8000000 00032A3C D2000000 00000000', '94000130 FCFF0000 6211186C 00000000 B211186C 00000000 0000DCF4 01ED0001 D2000000 00000000 94000130 FDFF0000 6211186C 00000000 B211186C 00000000 DA000000 0000DCF6 C0000000 00000027 D7000000 00032A48 D2000000 00000000', '94000130 FCFF0000 6211186C 00000000 B211186C 00000000 0000DCF4 01ED0001 D2000000 00000000 94000130 FEFF0000 6211186C 00000000 B211186C 00000000 DA000000 0000DCF6 C0000000 00000027 D7000000 00032A48 D2000000 00000000'])

def selector_code(species, level):
    if not (1 <= species <= 493 and 1 <= level <= 100):
        raise ValueError('species must be 1..493 and level 1..100')
    prefix = '52246C94 28038800 6211186C 00000000 B211186C 00000000 '
    return (prefix + f'D5000000 {species:08X} C0000000 00000027 D7000000 00032A48 D2000000 00000000 '
            + prefix + f'D5000000 {level:08X} C0000000 0000000B D8000000 00032A3C D2000000 00000000')


def update_catalogue(text, language):
    if language not in ('EN', 'IT'):
        raise ValueError('language must be EN or IT')
    root = ET.fromstring(text)
    games = root.findall('game')
    expected = 'IPKE ' + ('19D1EEBB' if language == 'EN' else '1C1F741C')
    if len(games) != 1 or games[0].findtext('gameid') != expected:
        raise ValueError('catalogue does not identify the supported SGP build')
    folders = [f for f in games[0].findall('folder') if f.findtext('name', '').startswith('40 - ')]
    if len(folders) != 1:
        raise ValueError('expected exactly one wild encounter folder 40')
    folder = folders[0]
    preserved = [c for c in folder.findall("cheat")
                 if " ".join(c.findtext("codes", "").split()).upper() not in LEGACY_SPECIES_CODES
                 and " ".join(c.findtext("codes", "").split()).upper() != selector_code(25, 5)]
    folder.clear()
    italian = language == 'IT'
    ET.SubElement(folder, 'name').text = ('40 - Selvatici · scegli Pokémon e livello' if italian else '40 - Wild encounters · choose Pokémon and level')
    cheat = ET.SubElement(folder, 'cheat')
    ET.SubElement(cheat, 'name').text = ('Scegli Pokémon e livello' if italian else 'Choose Pokémon and level')
    ET.SubElement(cheat, 'note').text = (
        'Richiede melonDS con selettore Sacred Gold Plus. Tocca la voce per scegliere fra 493 Pokémon '
        'con ricerca per nome o numero Pokédex e impostare il livello 1–100. La scelta iniziale è '
        'Pikachu, livello 5. In melonDS 2.1.1 il selettore parte spento: L+R attiva/disattiva; rilascia i tasti fra due pressioni. Non usa le Ball della Borsa. Solo erba alta; spegni Livelli selvatici nelle '
        'opzioni del gioco. Unown richiede un puzzle completato nelle Rovine d’Alfa. '
        'Sui melonDS senza selettore questo codice imposta direttamente Pikachu al livello 5; '
        'le cartelle 49–59 restano disponibili per la scelta manuale.' if italian else
        'Requires melonDS with the Sacred Gold Plus selector. Tap this entry to search 493 Pokémon '
        'by name or Pokédex number and choose a level from 1 to 100. The initial choice is Pikachu, '
        'level 5. In melonDS 2.1.1 the selector starts off: L+R toggles it on/off; release both buttons between presses. Does not use Bag Balls. Tall grass only; turn Wild levels off in the game options. '
        'Unown requires a completed Ruins of Alph puzzle. On melonDS without the selector this code '
        'directly sets Pikachu at level 5; folders 49–59 remain available for manual selection.'
    )
    ET.SubElement(cheat, 'codes').text = selector_code(25, 5)
    folder.extend(preserved)
    ET.indent(root, space='  ')
    return '<?xml version="1.0" encoding="utf-8"?>\n' + ET.tostring(root, encoding='unicode') + '\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('catalogue', type=Path)
    parser.add_argument('--language', choices=('EN', 'IT'), required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.write_text(update_catalogue(args.catalogue.read_text(encoding='utf-8'), args.language), encoding='utf-8')


if __name__ == '__main__':
    main()
