"""Explicit successor SGG1 compiler. No ROM/save installation or legacy override.

All text/name/font extraction remains in RAM. This unit retains the seven-line,
208-pixel geometry and 128 KiB resource limit. Encoded immutable strings, pages
and complete page tables can share offsets; runtime navigation state cannot.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import re
import struct
import unicodedata

from sgp13 import content as legacy
from sgp13 import guide
from sgp13.content import paginate

SOURCE = Path(__file__).resolve().parents[1]
PROSE = Path(__file__).with_name('data') / 'guide.json'
CAP = 131072
SUBJECTS_PATH = Path(__file__).with_name('data') / 'guide-subjects.json'
SUBJECTS = json.loads(SUBJECTS_PATH.read_text())
GROUPS = {int(target): tuple(members) for target, members in SUBJECTS['groups'].items()}
ALIASES = {species: target for target, members in GROUPS.items() for species in members}
ALIASES.update({int(species): target for species, target in SUBJECTS['additional_aliases'].items()})
SINGLE_SUBJECTS = tuple(SUBJECTS['single_subjects'])
ROM_PINS = {
    'EN': ('179edfb1ca331503f438e98f3afccfb0ab85759bf9ab88fb86c735f5fcefbf90', 147345256),
    'IT': ('2a2f0b437fca524c18b71b20feb01a1f51351e61c7c897ce73d9b3be1ee3a156', 153228136),
}
CHARMAP_SHA256 = '58861d34f40623fd2a9b29c10a79ee2ec872182285a288381759a3b251412ded'
# Audited unchanged script preimages, not extracted script content.
SCRIPT_PINS = {
    131: '99a3498483e0245cdd52e5e375e07ef336b083577579599419e073377b8965d6',
    132: 'c2b24b0535379dc86cea4f4b00ac6530894aa415aad47543c4d6d8837009e64b',
    890: '1fe860e2fcff9dc334d8e9f9d729119f95de0500790954493c72b6eb2d823fe9',
    152: '230d83fbe3efb652851bf3ac1f04ee4f961cf7ef2ae1b257da090eb83a3d5eac',
    196: '561e9fe0d3ce5af480c641925ae5ce5f7f2f402d24c07fca28d39b46f61a6388',
}
NATIVE_PINS = (
    (0x02046a1c, 256, 'c2752fcc1cfe271d3c96e2801c9919b9b2a08521c3467731ab27dee217cc7bfb'),
    (0x0208e9e0, 124, 'e2707b95ee09fcdd30a37ec31bab145d6864f2b80129ea98a63383329e1d3d81'),
    (0x02044fac, 56, '2e091d3a87535f3b7d94411bdcd567941769a1749e891a2df6cafd8313304594'),
    (0x02029f48, 22, 'e4d38cb92abe8c2d98a9ad1d314201da3fd6e255f6e819bee8c66385c8dd723c'),
    (0x02029f74, 52, 'f2622cee751fa5722cfcc908d883cae3972529798f5bef61e89598fc21dc9926'),
    (0x02029d50, 36, '2dc83e6ac8a9eeb5a03fc9c8ab6d9956564969a101260298a1232ac37cd8b7c9'),
    (0x02042000, 50, 'f7ae9a452218597a1bed43b622f8645d2321c30264b69baaea8bd45a16e7ce17'),
    (0x0205e400, 32, '781c2e215f8808e453b05dd85639baa55a06d2bb55f69e3b95dd204700b9e10b'),
)
EXCLUSIONS = (151, 251, 385, 386, 489, 490, 491, 492, 493)
FACT_GATE = {
    'profile': 'v4-audited-sinjoh-dex-darkrai-1',
    'excluded_claims': ['Arceus durable one-shot closure', 'Arceus safe restart/replay/retry',
                        'six event flags prove six captures', 'Shaymin activation proves capture',
                        'whiteout/interruption retry guarantee', 'old level-1 Arceus gift ritual'],
    'arceus_6131_incident': 'separate unresolved event/save incident; no repair in content',
    'other_topics': 'retained authored facts; no independent 38-topic sweep',
}


def _digest(data):
    return hashlib.sha256(data).hexdigest()


def sort_key(name, entry_id):
    """Locale-independent primary, sex token, normalized display, stable ID.

    NFKD/casefold removes marks; apostrophes join letters, other punctuation
    becomes whitespace. Sex signs are meaningful secondary tokens. NFKC display
    is the final textual tie-break, preserving punctuation and accents.
    """
    base = unicodedata.normalize('NFKD', name).casefold()
    sex = tuple('female' if c == '♀' else 'male' for c in base if c in '♀♂')
    chars = []
    for char in base:
        if unicodedata.combining(char) or char in "'’‘ʼ♀♂":
            continue
        chars.append(' ' if unicodedata.category(char).startswith('P') else char)
    return (' '.join(''.join(chars).split()), sex,
            unicodedata.normalize('NFKC', name).casefold(), entry_id)


def arrange_categories(categories, names, aliases=None):
    """Copy and index a graph without any ownership/save/Dex input."""
    aliases = ALIASES if aliases is None else aliases
    result = copy.deepcopy(categories)
    bycat = {c['id']: c for c in result}
    if len(bycat) != len(result) or set(bycat) != {1, 2, 3, 4}:
        raise ValueError('successor category IDs')
    entries = [e for c in result for e in c['entries']]
    byid = {e['id']: e for e in entries}
    if len(byid) != len(entries):
        raise ValueError('entry ID collision')
    for entry in bycat[1]['entries']:
        if not 1 <= entry['id'] <= 493:
            raise ValueError('evolution species ID')
        entry['title'] = names(entry['id'])
    for species, target in sorted(aliases.items()):
        if not 1 <= species <= 493 or target not in byid:
            raise ValueError('alias species/destination')
        alias_id = 5000 + species
        if alias_id in byid:
            raise ValueError('alias ID collision')
        entry = dict(id=alias_id, title=names(species), pages=copy.deepcopy(byid[target]['pages']))
        byid[alias_id] = entry
        bycat[3]['entries'].append(entry)
    for cid in (1, 3):
        bycat[cid]['entries'].sort(key=lambda e: sort_key(e['title'], e['id']))
    return [bycat[cid] for cid in (4, 1, 3, 2)]


def _words(value, encode, measure):
    if not isinstance(value, str) or not value.strip() or '\n' in value or '\r' in value:
        raise ValueError('empty/multiline Guide string')
    if measure(value) > 208:
        raise ValueError('text width exceeds native window')
    words = tuple(encode(value))
    if (not 2 <= len(words) <= 128 or words[-1] != 65535 or
            any(type(w) is not int or not 1 <= w <= 509 for w in words[:-1])):
        raise ValueError('encoded single-line glyph bounds/EOS')
    return words


def encoded_graph(categories, encode):
    """Semantic oracle for independent readback: no packed offsets involved."""
    return [dict(id=c['id'], title=tuple(encode(c['title'])), entries=[
        dict(id=e['id'], title=tuple(encode(e['title'])), pages=[
            dict(lines=[tuple(encode(s)) for s in p['lines']], reference=p.get('reference', 0))
            for p in e['pages']]) for e in c['entries']]) for c in categories]


def build_content(categories, encode, measure):
    """Compile shared immutable SGG1 bytes; validate all graph words and links."""
    count = sum(len(c['entries']) for c in categories)
    if not 1 <= len(categories) <= 4 or not 1 <= count <= 4096:
        raise ValueError('category/entry count')
    out = bytearray(12 + len(categories) * 12 + count * 16)
    struct.pack_into('<4sIHH', out, 0, b'SGG1', 0, len(categories), count)
    strings, pages, tables = {}, {}, {}

    def extend(payload):
        if len(out) + len(payload) > CAP:
            raise ValueError('Guide resource exceeds 128 KiB heap budget')
        out.extend(payload)

    def align():
        extend(bytes(-len(out) % 4))

    def string(value):
        words = _words(value, encode, measure)
        if words not in strings:
            strings[words] = len(out)
            extend(struct.pack('<%dH' % len(words), *words))
        return strings[words]

    def page(value):
        lines, ref = value['lines'], value.get('reference', 0)
        if not 1 <= len(lines) <= 7 or type(ref) is not int or not 0 <= ref <= 65535:
            raise ValueError('page lines/reference')
        key = tuple(_words(s, encode, measure) for s in lines), ref
        if key not in pages:
            align()
            offset = pages[key] = len(out)
            extend(struct.pack('<HH', len(lines), ref) + bytes(4 * len(lines)))
            for index, line in enumerate(lines):
                struct.pack_into('<I', out, offset + 4 + 4 * index, string(line))
        return pages[key]

    def table(values):
        if not 1 <= len(values) <= 255:
            raise ValueError('page count')
        offsets = tuple(page(p) for p in values)
        if offsets not in tables:
            align()
            tables[offsets] = len(out)
            extend(struct.pack('<%dI' % len(offsets), *offsets))
        return tables[offsets]

    ids, category_ids, index = set(), set(), 0
    for ci, category in enumerate(categories):
        cid = category['id']
        if type(cid) is not int or not 1 <= cid <= 65535 or cid in category_ids or not category['entries']:
            raise ValueError('empty/duplicate category')
        category_ids.add(cid)
        title = string(category['title'])
        struct.pack_into('<HHII', out, 12 + 12 * ci, cid, len(category['entries']), index, title)
        for entry in category['entries']:
            eid = entry['id']
            if type(eid) is not int or not 1 <= eid <= 65535 or eid in ids:
                raise ValueError('entry ID collision')
            ids.add(eid)
            title, pt = string(entry['title']), table(entry['pages'])
            struct.pack_into('<HHHHII', out, 12 + 12 * len(categories) + 16 * index,
                             eid, cid, len(entry['pages']), 0, title, pt)
            index += 1
    if len(out) > CAP:
        raise ValueError('Guide resource exceeds 128 KiB heap budget')
    struct.pack_into('<I', out, 4, len(out))
    guide.validate_content(out)
    verify_content(out, encoded_graph(categories, encode))
    return bytes(out)


def read_content(data):
    """Independent bounded traversal, without packer structs/caches/receipt offsets.

    Exact immutable aliases are legal. Partial/typed overlaps, pointer cycles,
    dangling links, orphan bytes and non-alignment/trailing padding fail closed.
    X links are not recursively followed: existing canonical links are cyclic.
    """
    def require(ok):
        if not ok:
            raise ValueError('invalid successor Guide content')

    require(12 <= len(data) <= 131072)
    magic, size, nc, ne = struct.unpack_from('<4sIHH', data, 0)
    require(magic == b'SGG1' and size == len(data) and 1 <= nc <= 4 and 1 <= ne <= 4096)
    prefix = 12 + 12 * nc + 16 * ne
    require(prefix <= size)
    ranges = {}

    def claim(start, length, kind, alignment):
        require(prefix <= start and start % alignment == 0 and length > 0 and start + length <= size)
        old = ranges.get(start)
        require(old is None or old == (length, kind))
        ranges[start] = (length, kind)

    def string(start):
        require(prefix <= start < size and start % 2 == 0)
        words = []
        for i in range(128):
            require(start + 2 * i + 2 <= size)
            word = struct.unpack_from('<H', data, start + 2 * i)[0]
            words.append(word)
            if word == 65535:
                require(i > 0)
                claim(start, 2 * len(words), 'string', 2)
                return tuple(words)
            require(1 <= word <= 509)
        require(False)

    result, ids, refs, catids, total = [], set(), set(), set(), 0
    for ci in range(nc):
        cid, number, first, title = struct.unpack_from('<HHII', data, 12 + ci * 12)
        require(cid > 0 and cid not in catids and number > 0 and first == total and first + number <= ne)
        catids.add(cid)
        category = dict(id=cid, title=string(title), entries=[])
        for index in range(first, first + number):
            eid, ecid, np, reserved, title, pt = struct.unpack_from('<HHHHII', data, 12 + 12 * nc + index * 16)
            require(eid > 0 and eid not in ids and ecid == cid and 1 <= np <= 255 and reserved == 0)
            ids.add(eid)
            entry = dict(id=eid, title=string(title), pages=[])
            claim(pt, np * 4, 'table', 4)
            for pi in range(np):
                po = struct.unpack_from('<I', data, pt + pi * 4)[0]
                require(prefix <= po and po % 4 == 0 and po + 4 <= size)
                nl, ref = struct.unpack_from('<HH', data, po)
                require(1 <= nl <= 7)
                claim(po, 4 + nl * 4, 'page', 4)
                if ref:
                    refs.add(ref)
                lines = [string(struct.unpack_from('<I', data, po + 4 + li * 4)[0]) for li in range(nl)]
                entry['pages'].append(dict(lines=lines, reference=ref))
            category['entries'].append(entry)
        total += number
        result.append(category)
    require(total == ne and refs <= ids)
    cursor = prefix
    for start, (length, kind) in sorted(ranges.items()):
        require(start >= cursor)
        if start > cursor:
            require(kind in ('table', 'page') and 0 < start - cursor <= 3 and start % 4 == 0
                    and bytes(data[cursor:start]) == bytes(start - cursor))
        cursor = start + length
    require(cursor == size)
    return result


def verify_content(data, intended):
    if read_content(data) != intended:
        raise ValueError('Guide semantic readback mismatch')


def load_inputs(rom_path, language, charmap):
    """Read pinned V4 inputs and return in-memory names, evolution records, codec/font."""
    import ndspy.narc
    import ndspy.rom
    from sgp12.rom import Arm9

    if language not in ROM_PINS:
        raise ValueError('language')
    raw = Path(rom_path).read_bytes()
    if (_digest(raw), len(raw)) != ROM_PINS[language]:
        raise ValueError('canonical V4 ROM identity')
    if _digest(Path(charmap).read_bytes()) != CHARMAP_SHA256:
        raise ValueError('pinned external charmap identity')
    rom = ndspy.rom.NintendoDSRom(raw)
    scripts = ndspy.narc.NARC(rom.getFileByName('a/0/1/2')).files
    for member, digest in SCRIPT_PINS.items():
        if _digest(scripts[member]) != digest:
            raise ValueError('audited event script preimage')
    arm = Arm9(rom_path)
    for address, length, digest in NATIVE_PINS:
        if _digest(arm.leggi(address, length)) != digest:
            raise ValueError('audited native event preimage')
    pointer = struct.unpack('<I', arm.leggi(0x02029d70, 4))[0]
    if struct.unpack('<9H', arm.leggi(pointer, 18)) != EXCLUSIONS:
        raise ValueError('audited Dex exclusions')
    del arm, scripts, raw
    text = legacy._module(SOURCE / 'quality-audit/hgss_text.py', 'successor_guide_text')
    font = legacy._module(SOURCE / 'quality-audit/misura_larghezza.py', 'successor_guide_widths')
    codec = legacy._module(SOURCE / 'features/options/tools/codifica_testo.py', 'successor_guide_codec')
    chars, commands = text.load_charmap(charmap)
    table, _ = codec.carica_charmap(charmap)
    widths = font.load_width_table_from_rom(rom_path)
    archive = ndspy.narc.NARC(rom.getFileByName('a/0/2/7'))
    banks = {kind: text.read_bank(archive.files[index], chars, commands)
             for kind, index in (('item', 222), ('pokemon', 237), ('move', 750), ('map', 279))}

    def names(kind, index):
        row = banks[kind][index]
        if row['controls'] or row['unknown_codes'] or row['malformed_controls']:
            raise ValueError('unexpected control in native name')
        return row['text']

    def encode(value):
        return codec.codifica(value.replace("'", '’'), table)

    def measure(value):
        measured = font.measure(widths, encode(value), limit_px=224)
        if any(line['unknown_codes'] for line in measured['lines']):
            raise ValueError('unmeasurable native glyph')
        return max(line['width_px'] for line in measured['lines'])

    evolutions = ndspy.narc.NARC(rom.getFileByName('a/0/3/4')).files
    return names, evolutions, encode, measure


def make_categories(records, names, language, measure, prose):
    """Build intended graph from actual rules and original bilingual prose."""
    if language not in ('EN', 'IT'):
        raise ValueError('language')
    def expand(value):
        return re.sub(r'\{(pokemon|item|move|map):(\d+)\}',
                      lambda match: names(match[1], int(match[2])), value)
    item_ids = {e['id'] for c in prose['categories'] if c['id'] == 2 for e in c['entries']}
    categories = [dict(id=1, title='Evoluzioni' if language == 'IT' else 'Evolutions',
                       entries=legacy.evolution_entries(records, names, language, measure, item_ids))]
    for category in prose['categories']:
        entries = []
        for entry in category['entries']:
            pages = []
            for page in entry['pages']:
                pages.extend(paginate([expand(p) for p in page[language]], measure, page.get('reference', 0)))
            entries.append(dict(id=entry['id'], title=expand(entry['title'][language]), pages=pages))
        categories.append(dict(id=category['id'], title=category['title'][language], entries=entries))
    return arrange_categories(categories, lambda species: names('pokemon', species))


def build_from_rom(rom_path, language, charmap, prose_path=None):
    """Return (bytes, deterministic JSON-serializable receipt), without writing files."""
    names, records, encode, measure = load_inputs(rom_path, language, charmap)
    prose_raw = Path(prose_path or PROSE).read_bytes()
    prose = json.loads(prose_raw)
    categories = make_categories(records, names, language, measure, prose)
    special = next(c['entries'] for c in categories if c['id'] == 3)
    expected_special = {2000 + s for s in SINGLE_SUBJECTS} | set(GROUPS) | {5000 + s for s in ALIASES}
    if len(special) != 76 or {e['id'] for e in special} != expected_special:
        raise ValueError('audited special-subject graph changed')
    if [len(c['entries']) for c in categories] != [6, 229, 76, 156]:
        raise ValueError('canonical V4 graph coverage changed')
    blob = build_content(categories, encode, measure)
    strings, pages, tables = set(), set(), set()
    for c in categories:
        strings.add(tuple(encode(c['title'])))
        for e in c['entries']:
            strings.add(tuple(encode(e['title'])))
            table = []
            for p in e['pages']:
                lines = tuple(tuple(encode(s)) for s in p['lines'])
                strings.update(lines)
                page = lines, p.get('reference', 0)
                pages.add(page)
                table.append(page)
            tables.add(tuple(table))
    texts = [c['title'] for c in categories] + [e['title'] for c in categories for e in c['entries']]
    body = [s for c in categories for e in c['entries'] for p in e['pages'] for s in p['lines']]
    receipt = dict(schema=1, format='SGG1', language=language, input_rom_sha256=ROM_PINS[language][0],
                   input_rom_bytes=ROM_PINS[language][1], charmap_sha256=CHARMAP_SHA256,
                   compiler_sha256=_digest(Path(__file__).read_bytes()), prose_sha256=_digest(prose_raw),
                   subjects_sha256=_digest(SUBJECTS_PATH.read_bytes()),
                   content_sha256=_digest(blob), bytes=len(blob), cap=CAP, headroom=CAP - len(blob),
                   categories=[dict(id=c['id'], entries=len(c['entries'])) for c in categories],
                   records=sum(len(c['entries']) for c in categories), canonical_special_records=38,
                   aliases={str(5000 + s): target for s, target in sorted(ALIASES.items())},
                   covered_special_species=len(set(SINGLE_SUBJECTS) | set(ALIASES)),
                   visible_pages=sum(len(e['pages']) for c in categories for e in c['entries']),
                   unique_strings=len(strings), unique_pages=len(pages), unique_page_tables=len(tables),
                   body_lines=len(body), visible_words=sum(len(s.split()) for s in body),
                   visible_links=sum(bool(p.get('reference', 0)) for c in categories for e in c['entries'] for p in e['pages']),
                   max_title_width=max(map(measure, texts)), max_body_width=max(map(measure, body)),
                   body_lines_per_page=7, text_width=208, independent_semantic_readback=True,
                   event_preimages_verified=True, fact_gate=copy.deepcopy(FACT_GATE))
    return blob, receipt
