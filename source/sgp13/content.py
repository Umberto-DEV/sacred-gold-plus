"""Original guide prose plus evolution facts read from the actual input ROM."""
import importlib.util
import json
from pathlib import Path
import re
import struct

from .guide import build_content, TEXT_WIDTH

SOURCE = Path(__file__).resolve().parents[1]


def _module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def paginate(paragraphs, measure, reference=0):
    pages, current = [], []
    for paragraph in paragraphs:
        lines = []
        line = ''
        for word in paragraph.split():
            if measure(word) > TEXT_WIDTH:
                raise ValueError('Guide word exceeds native window: ' + word)
            candidate = (line + ' ' + word).strip()
            if measure(candidate) > TEXT_WIDTH:
                lines.append(line)
                line = word
            else:
                line = candidate
        if line:
            lines.append(line)
        if not lines:
            continue
        # Keep screen-sized paragraphs intact. Only an oversized paragraph
        # continues across screens; its tail may share with the next whole one.
        if current and (len(lines) > 7 or len(current) + len(lines) > 7):
            pages.append({'lines': current, 'reference': reference})
            current = []
        if len(lines) <= 7:
            current.extend(lines)
        else:
            for i in range(0, len(lines), 7):
                chunk = lines[i:i + 7]
                if len(chunk) == 7:
                    pages.append({'lines': chunk, 'reference': reference})
                else:
                    current = chunk
    if current:
        pages.append({'lines': current, 'reference': reference})
    if not pages:
        raise ValueError('empty Guide page')
    return pages

def evolution_entries(records, names, language, measure, linked_items):
    if len(records) < 494:
        raise ValueError('incomplete evolution archive')
    entries = []
    for species in range(1, 494):
        record = records[species]
        if len(record) < 42:
            raise ValueError('truncated evolution record')
        pages = []
        for offset in range(0, 42, 6):
            method, param, target = struct.unpack_from('<HHH', record, offset)
            if not method:
                continue
            if not 1 <= target <= 493:
                raise ValueError('invalid evolution target')
            detail = evolution_description(method, param, names, language)
            ref = 1000 + param if method in (6, 7, 16, 17, 18, 19) else 0
            if ref not in linked_items:
                ref = 0
            paragraphs = [('Diventa: ' if language == 'IT' else 'Evolves into: ') +
                          names('pokemon', target), '- ' + detail]
            pages.extend(paginate(paragraphs, measure, ref))
        if pages:
            entries.append({'id': species, 'title': f'{species:03d} ' + names('pokemon', species),
                            'pages': pages})
    return entries

def evolution_description(method, parameter, names, language):
    if language not in ('EN', 'IT'):
        raise ValueError('language')
    it = language == 'IT'
    p = parameter
    choose = lambda en, italian: italian if it else en
    level = choose(f'Level up to at least Lv.{p}', f'Fallo salire almeno al L.{p}')
    friendship = choose('Level up with high friendship', 'Fallo salire di livello con alta amicizia')
    if method == 1: return friendship + '.'
    if method == 2: return friendship + choose(' during the day.', ' di giorno.')
    if method == 3: return friendship + choose(' at night.', ' di notte.')
    if method in (4, 13): return level + '.'
    if method == 5: return choose('Trade this Pokemon.', 'Scambia questo Pokémon.')
    if method == 6:
        return choose('Trade while holding ', 'Scambialo mentre tiene ') + names('item', p) + '.'
    if method in (7, 16, 17):
        text = choose('Use ', 'Usa ') + names('item', p) + '.'
        if method == 16: text += choose(' Male only.', ' Solo maschio.')
        if method == 17: text += choose(' Female only.', ' Solo femmina.')
        return text
    if method in (8, 9, 10):
        relation = {8: ('higher than', 'maggiore di'), 9: ('equal to', 'uguale a'),
                    10: ('lower than', 'minore di')}[method]
        return level + choose(f'; Attack {relation[0]} Defense.', f'; Attacco {relation[1]} Difesa.')
    if method in (11, 12):
        return level + choose('. The branch depends on this Pokemon; changing its stats does not choose it.',
                              '. Il ramo dipende dal Pokémon; modificare le statistiche non lo cambia.')
    if method == 14:
        return choose(f'When Nincada evolves at Lv.{p}, keep an empty party slot and a regular Poke Ball in the Bag.',
                      f'Quando Nincada evolve al L.{p}, lascia un posto in squadra e una Poké Ball normale nella Borsa.')
    if method == 15:
        if p == 0: return choose('Level up.', 'Fallo salire di livello.')
        return choose(f'Level up with Beauty at least {p}.', f'Fallo salire di livello con Bellezza almeno {p}.')
    if method in (18, 19):
        return choose('Level up while holding ', 'Fallo salire di livello mentre tiene ') + names('item', p) + (
            choose(' during the day.', ' di giorno.') if method == 18 else choose(' at night.', ' di notte.'))
    if method == 20:
        return choose('Level up while knowing ', 'Fallo salire di livello conoscendo ') + names('move', p) + '.'
    if method == 21:
        return choose('Level up with ', 'Fallo salire di livello con ') + names('pokemon', p) + choose(' in the party.', ' in squadra.')
    if method in (22, 23):
        text = level + '.' if p else choose('Level up.', 'Fallo salire di livello.')
        return text + (choose(' Male only.', ' Solo maschio.') if method == 22 else choose(' Female only.', ' Solo femmina.'))
    raise ValueError(f'unverified evolution method {method}')


def build_from_rom(rom_path, language, charmap, prose_path=None):
    """Return (SGG1 bytes, evidence). Only own prose and generators are public."""
    import ndspy.narc
    import ndspy.rom
    if language not in ('EN', 'IT'):
        raise ValueError('language')
    text = _module(SOURCE / 'quality-audit/hgss_text.py', 'guide_messages')
    widths_module = _module(SOURCE / 'quality-audit/misura_larghezza.py', 'guide_widths')
    codec = _module(SOURCE / 'features/options/tools/codifica_testo.py', 'guide_encoder')
    rom = ndspy.rom.NintendoDSRom.fromFile(rom_path)
    archive = ndspy.narc.NARC(rom.getFileByName('a/0/2/7'))
    chars, commands = text.load_charmap(charmap)
    table, _ = codec.carica_charmap(charmap)
    widths = widths_module.load_width_table_from_rom(rom_path)
    # HGSS provides a typographic apostrophe, not ASCII U+0027.
    encode = lambda value: codec.codifica(value.replace("'", '’'), table)

    def measure(value):
        result = widths_module.measure(widths, encode(value), limit_px=224)
        if any(line['unknown_codes'] for line in result['lines']):
            raise ValueError('unmeasurable native glyph')
        return max(line['width_px'] for line in result['lines'])

    banks = {kind: text.read_bank(archive.files[index], chars, commands)
             for kind, index in (('item', 222), ('pokemon', 237), ('move', 750), ('map', 279))}

    def names(kind, index):
        row = banks[kind][index]
        if row['controls'] or row['unknown_codes'] or row['malformed_controls']:
            raise ValueError('unexpected control in native name')
        return row['text']

    def expand(value):
        return re.sub(r'\{(pokemon|item|move|map):(\d+)\}',
                      lambda match: names(match[1], int(match[2])), value)

    path = Path(prose_path) if prose_path else Path(__file__).with_name('data') / 'guide.json'
    prose = json.loads(path.read_text())
    categories = []
    item_ids = {entry['id'] for entry in prose['categories'][0]['entries']}
    evolutions = ndspy.narc.NARC(rom.getFileByName('a/0/3/4')).files
    categories.append({'id': 1, 'title': 'Evoluzioni' if language == 'IT' else 'Evolutions',
                       'entries': evolution_entries(evolutions, names, language, measure, item_ids)})
    for category in prose['categories']:
        entries = []
        for entry in category['entries']:
            pages = []
            for page in entry['pages']:
                pages.extend(paginate([expand(p) for p in page[language]], measure, page.get('reference', 0)))
            entries.append({'id': entry['id'], 'title': expand(entry['title'][language]), 'pages': pages})
        categories.append({'id': category['id'], 'title': category['title'][language], 'entries': entries})
    blob = build_content(categories, encode, measure)
    return blob, {'language': language, 'bytes': len(blob),
                  'categories': [{'id': c['id'], 'entries': len(c['entries'])} for c in categories],
                  'pages': sum(len(e['pages']) for c in categories for e in c['entries'])}
