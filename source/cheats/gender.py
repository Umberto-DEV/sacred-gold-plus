"""Replace legacy wild gender/nature codes with guarded native-creation patches.

The input is the user's catalogue, never a ROM. Changes occur before native
Pokémon creation; no pointer to an existing encrypted Pokémon is written.
"""
import argparse
from pathlib import Path
import xml.etree.ElementTree as ET


def pid_gender(pid, ratio):
    if ratio == 0:
        return 'male'
    if ratio == 254:
        return 'female'
    if ratio == 255:
        return 'genderless'
    return 'female' if (pid & 255) < ratio else 'male'


def gender_code(gender, nature):
    if gender not in ('male', 'female') or not 0 <= nature <= 24:
        raise ValueError('gender must be male/female and nature must be 0..24')
    low = 255 if gender == 'male' else 0
    sex = 0 if gender == 'male' else 1
    return (
        '5206E108 B086B5F8 5206E14C B089B5F0 '
        '1206E110 00009C0C 1206E11A 00001C05 '
        '1206E15C 00009E0E 1206E15E 00009F0F '
        '94000130 FDFF0000 '
        f'1206E110 {0x2400 + nature:08X} 1206E11A {0x2500 + low:08X} '
        f'1206E15C {0x2600 + sex:08X} 1206E15E {0x2700 + nature:08X} '
        'D2000000 00000000'
    )


def nature_code(nature):
    if not 0 <= nature <= 24:
        raise ValueError('nature must be 0..24')
    return (
        '5206E108 B086B5F8 5206E14C B089B5F0 '
        '1206E110 00009C0C 1206E11A 00001C05 '
        '1206E15C 00009E0E 1206E15E 00009F0F '
        f'1206E110 {0x2400 + nature:08X} 1206E15E {0x2700 + nature:08X} '
        'D2000000 00000000'
    )


def legacy_code(gender, nature):
    """Exact legacy form, used only to recognize a supported migration input."""
    if gender not in ('male', 'female') or not 0 <= nature <= 24:
        raise ValueError('unsupported gender/nature')
    add = (75 if gender == 'male' else 50) + nature - (25 if nature >= 17 else 0)
    return ('020D3F60 E12FFF1E 94000130 FDFF0000 020D3F60 EA0BB366 '
            'E23C0D00 00000030 E59F001C E5900000 E59F4018 E7943000 '
            f'E2033A3E E1833523 {0xE2833000 + add:08X} E7843000 '
            'E12FFF1E 0211186C 0000F710 E1A00000')


def update_gender_catalogue(text, language):
    if language not in ('EN', 'IT'):
        raise ValueError('language must be EN or IT')
    root = ET.fromstring(text)
    games = root.findall('game')
    expected = 'IPKE ' + ('19D1EEBB' if language == 'EN' else '1C1F741C')
    if len(games) != 1 or games[0].findtext('gameid') != expected:
        raise ValueError('catalogue does not identify the supported SGP build')
    for number, gender in ((44, None), (45, 'male'), (46, 'female')):
        folders = [f for f in games[0].findall('folder')
                   if f.findtext('name', '').startswith(f'{number} - ')]
        if len(folders) != 1 or len(folders[0].findall('cheat')) != 25:
            raise ValueError(f'expected one folder {number} with 25 nature entries')
        make = (lambda n: gender_code(gender, n)) if gender else nature_code
        old = (lambda n: legacy_code(gender, n)) if gender else (lambda n: f'1206E120 {0x2400+n:08X}')
        choices = {old(n): n for n in range(25)}
        choices.update({make(n): n for n in range(25)})
        seen = set()
        for cheat in folders[0].findall('cheat'):
            code = ' '.join(cheat.findtext('codes', '').split()).upper()
            if code not in choices or choices[code] in seen:
                raise ValueError(f'unknown or duplicate nature code in folder {number}')
            nature = choices[code]
            seen.add(nature)
            cheat.find('codes').text = make(nature)
            note = cheat.find('note')
            if note is None:
                note = ET.SubElement(cheat, 'note')
            if gender:
                note.text = (
                    'Tieni premuto L prima di entrare nell’incontro. Rilascia L prima di disattivare '
                    'il codice; se hai usato quello precedente, riavvia il gioco. Usa una sola voce '
                    'dei gruppi 44–46 e non combinarla con codici cromatici/PID. Le specie monosesso '
                    'o asessuate mantengono il proprio genere. Funziona anche con Incantevole. '
                    'La distribuzione dei PID, e quindi dei cromatici, cambia.' if language == 'IT' else
                    'Hold L before entering the encounter. Release L before disabling the code; '
                    'restart the game if you used the previous code. Use only one entry from folders '
                    '44–46 and do not combine with shiny/PID codes. Single-gender and genderless '
                    'species keep their own gender. Also covers Cute Charm. PID distribution, and '
                    'therefore shiny outcomes, changes.'
                )
            else:
                note.text = (
                    'Natura dei selvatici, sempre attiva; funziona anche con Incantevole. Usa una sola '
                    'voce dei gruppi 44–46. Conserva il generatore PID e il genere nativi. Riavvia il '
                    'gioco dopo avere disattivato il codice o se hai usato la versione precedente.'
                    if language == 'IT' else
                    'Wild nature, always active; also covers Cute Charm. Use only one entry from '
                    'folders 44–46. Keeps native PID generation and gender. After disabling the code '
                    'or using the previous version, restart the game.'
                )
    ET.indent(root, space='  ')
    return '<?xml version="1.0" encoding="utf-8"?>\n' + ET.tostring(root, encoding='unicode') + '\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('catalogue', type=Path)
    parser.add_argument('--language', choices=('EN', 'IT'), required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.write_text(update_gender_catalogue(args.catalogue.read_text(encoding='utf-8'), args.language), encoding='utf-8')


if __name__ == '__main__':
    main()
