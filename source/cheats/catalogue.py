"""Apply the supported SGP catalogue migrations to a supplied release input."""
import argparse
from pathlib import Path
import xml.etree.ElementTree as ET
from selector import update_catalogue
from gender import update_gender_catalogue

# Clean-ROM DeSmuME/No$GBA workaround. Its 020DDDC8 guard does not match SGP;
# the other blocks can still modify the game, so this is not a harmless no-op.
OBSOLETE_OVERLAY_PATCH = (
    '5201A570 E002D1F8 0201A570 E00246C0 D2000000 00000000 '
    '520DDDC8 1AFFFFF5 020DDDC8 E1A00000 D2000000 00000000 '
    '520DE16C 1AFFFFFC 020DE16C E1A00000 D2000000 00000000 '
    '521E5B74 D10A2800 021E5B74 E00A2800 D2000000 00000000 '
    '52260C20 4F35B5F8 02260C20 477020AA D2000000 00000000'
)


def remove_obsolete_overlay_patch(text):
    root = ET.fromstring(text)
    for folder in root.iter('folder'):
        for cheat in list(folder.findall('cheat')):
            if ' '.join(cheat.findtext('codes', '').split()).upper() == OBSOLETE_OVERLAY_PATCH:
                folder.remove(cheat)
    ET.indent(root, space='  ')
    return '<?xml version="1.0" encoding="utf-8"?>\n' + ET.tostring(root, encoding='unicode') + '\n'


def migrate(text, language):
    return remove_obsolete_overlay_patch(update_gender_catalogue(update_catalogue(text, language), language))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('catalogue', type=Path)
    parser.add_argument('--language', choices=('EN', 'IT'), required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.write_text(migrate(args.catalogue.read_text(encoding='utf-8'), args.language), encoding='utf-8')


if __name__ == '__main__':
    main()
