"""Localized Guide presentation built from the common candidate's actual rules."""
import hashlib
import json
from pathlib import Path
import re
import struct

from ndspy.narc import NARC
from ndspy.rom import NintendoDSRom
from sgp13 import content as legacy
from sgp131 import guide_content, ui_compile
from .catalogue import load_strings
from .messages import _TEXT


def evolution_description(method, parameter, names, locale):
    if locale in ('EN', 'IT'):
        return legacy.evolution_description(method, parameter, names, locale)
    words = load_strings(locale, 'evolution')
    p = parameter
    if method in (1, 2, 3):
        return words[{1: 'friendship', 2: 'friendship_day', 3: 'friendship_night'}[method]]
    if method in (4, 13): return words['level'].format(p=p)
    if method == 5: return words['trade']
    if method == 6: return words['trade_item'].format(item=names('item', p))
    if method in (7, 16, 17):
        text = words['use_item'].format(item=names('item', p))
        return text + (' ' + words['male' if method == 16 else 'female'] if method != 7 else '')
    if method in (8, 9, 10):
        return words[{8: 'attack_gt', 9: 'attack_eq', 10: 'attack_lt'}[method]].format(p=p)
    if method in (11, 12): return words['level'].format(p=p) + ' ' + words['branch']
    if method == 14: return words['shedinja'].format(p=p)
    if method == 15: return words['beauty'].format(p=p) if p else words['level_any']
    if method in (18, 19):
        return words['hold_day' if method == 18 else 'hold_night'].format(item=names('item', p))
    if method == 20: return words['known_move'].format(move=names('move', p))
    if method == 21: return words['party_species'].format(species=names('pokemon', p))
    if method in (22, 23):
        return (words['level'].format(p=p) if p else words['level_any']) + ' ' + words['male' if method == 22 else 'female']
    raise ValueError('unverified evolution method ' + str(method))


def build_categories(rom, locale, strings, charmap):
    chars, commands = _TEXT.load_charmap(charmap)
    codec = ui_compile.module(ui_compile.SOURCE / 'features/options/tools/codifica_testo.py', 'locale_guide_codec')
    fonts = ui_compile.module(ui_compile.SOURCE / 'quality-audit/misura_larghezza.py', 'locale_guide_widths')
    table, _ = codec.carica_charmap(charmap)
    widths = fonts.extract_width_table(NARC(rom.getFileByName('a/0/1/6')).files[0])
    encode = lambda text: codec.codifica(text.replace("'", '’'), table)
    def measure(text):
        result = fonts.measure(widths, encode(text), limit_px=224)
        if any(row['unknown_codes'] for row in result['lines']):
            raise ValueError('unmeasurable Guide glyph')
        return max(row['width_px'] for row in result['lines'])
    archive = NARC(rom.getFileByName('a/0/2/7'))
    banks = {kind: _TEXT.read_bank(archive.files[bank], chars, commands)
             for kind, bank in [('item', 222), ('pokemon', 237), ('move', 750), ('map', 279)]}
    def names(kind, index):
        row = banks[kind][index]
        if row['unknown_codes'] or row['malformed_controls'] or row['controls']:
            raise ValueError('invalid localized native name')
        return row['text']
    records = ui_compile.evolution_records(rom)
    prose = json.loads(guide_content.PROSE.read_text())
    if locale in ('EN', 'IT'):
        categories = guide_content.make_categories(records, names, locale, measure, prose)
        return categories, encode, measure
    templates = load_strings(locale, 'evolution')
    items = {e['id'] for c in prose['categories'] if c['id'] == 2 for e in c['entries']}
    evolutions = []
    for species in range(1, 494):
        pages = []
        for offset in range(0, 42, 6):
            method, parameter, target = struct.unpack_from('<HHH', records[species], offset)
            if not method:
                continue
            if not 1 <= target <= 493:
                raise ValueError('invalid evolution target')
            reference = 1000 + parameter if method in (6, 7, 16, 17, 18, 19) else 0
            if reference not in items:
                reference = 0
            paragraphs = [templates['target'].format(species=names('pokemon', target)),
                          '- ' + evolution_description(method, parameter, names, locale)]
            pages.extend(legacy.paginate(paragraphs, measure, reference))
        if pages:
            evolutions.append(dict(id=species, title=names('pokemon', species), pages=pages))
    categories = [dict(id=1, title=templates['category'], entries=evolutions)]
    def expand(text):
        return re.sub(r'\{(pokemon|item|move|map):(\d+)\}',
                      lambda match: names(match[1], int(match[2])), text)
    for category in prose['categories']:
        entries = []
        for entry in category['entries']:
            pages = []
            for pi, page in enumerate(entry['pages']):
                paragraphs = [expand(strings[f'g:{entry["id"]}:{pi}:{si}'])
                              for si in range(len(page['EN']))]
                pages.extend(legacy.paginate(paragraphs, measure, page.get('reference', 0)))
            entries.append(dict(id=entry['id'], title=expand(strings[f'g:{entry["id"]}:title']), pages=pages))
        categories.append(dict(id=category['id'], title=strings[f'g:category:{category["id"]}'], entries=entries))
    return guide_content.arrange_categories(categories, lambda index: names('pokemon', index)), encode, measure


def compile_guide(data, locale, strings, charmap):
    categories, encode, measure = build_categories(NintendoDSRom(data), locale, strings, charmap)
    intended = guide_content.encoded_graph(categories, encode)
    resource = guide_content.build_content(categories, encode, measure)
    guide_content.verify_content(resource, intended)
    return resource, dict(locale=locale, bytes=len(resource), sha256=hashlib.sha256(resource).hexdigest(),
                          categories=len(categories), entries=sum(len(c['entries']) for c in categories))
