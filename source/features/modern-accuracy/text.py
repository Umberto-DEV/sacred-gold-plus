"""Keen Eye (ability 51) description, EN/IT: one row of one message bank.

What changes: row 51 of message bank 722 (member 722 of the NitroFS archive
`a/0/2/7`, the ability descriptions). Nothing else: no name, no other row, no
other archive member. The retail row is identified by the SHA-256 of its
encoded words, never stored as text (game text stays out of git).

Where the text is drawn (read from the V4 EN/IT bytes, identical in both):

* Pokemon Summary, "Skills" page, in the ARM9. `sub_0208D178` loads bank 722
  (literal at 0x0208D46C), reads the ability row into a 128-character String
  and prints it with `AddTextPrinterParameterizedWithColor(window 7, font 0,
  x=3, y=0, speed 0xFF, colour 0x00010200)`. Window 7 of the page template
  at 0x02104D04 is `bg 1, x 0, y 19, w 19, h 4` tiles: 152 x 32 px.
* Battle Summary "Skills" page, overlay 8. `ov08_0221EC6C` loads the same bank
  (literal at 0x0221ECDC) and prints at x=0, y=0, font 0 into window
  `page * 22 + 2` of the 35-window template at 0x0222522C (entries 2 and 24:
  `bg 5, x 1, y 11, w 18, h 4` tiles): 144 x 32 px.

Font 0 has a 16 px line pitch and no letter or line spacing, so a 32 px window
holds exactly two lines. `CopyGlyphToWindow` clips at the window edge, so a
wider line is cut mid-glyph and a third line is not drawn at all. The ceiling
is therefore 2 lines, each at most 144 px (the narrower window). The longest
line of the other 123 retail descriptions is 136 px in both languages.

Other bank-722 matches in the images are bank-ID tables and instruction
bytes with no window (overlays 7, 26, 45, 49, 80), not display consumers.
"""
import hashlib
import importlib.util
import struct
from sgp12.blz import ndspy_load_overlays_sicuri
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[2]

ARCHIVE = 'a/0/2/7'
FONT_ARCHIVE = 'a/0/1/6'
BANK = 722
ROW = 51
ROWS = 124
NEWLINE = 0xE000
TERMINATOR = 0xFFFF
MAX_LINES = 2
MAX_WORDS = 127           # the summary String holds 128 words including the terminator
GLYPHS = 509

CHARMAP_SHA256 = '58861d34f40623fd2a9b29c10a79ee2ec872182285a288381759a3b251412ded'
FONT_SHA256 = '9a17de3036f4aac8540163e560a60d83b7facde78d0ec41e688374fdbf669e73'
WIDTHS_SHA256 = '9056ed8029423336c0c7d7cf88c8e04841f09849bf431ce6d1c6ebebd4358e84'

# SHA-256 of the retail row 51 as little-endian 16-bit words, terminator included.
PREIMAGE_SHA256 = {'EN': '1b755d85bc4a387a16cec2d87edcf71c7d26a684319df268e4ceeb38ad79dc58',
                   'IT': '214edbc42eb792d00bbecc124b639283aa350ae2a9130cef567834f182e8eaf8'}

# Authored here. Typographic apostrophe, as in the retail text. Every line is at most 136 px
# in the real font (the retail ceiling) and the meaning is two facts only: accuracy cannot be
# lowered, changes to the target's evasion are ignored. No promise about items, weather or
# abilities that act on evasion.
# Encoded row 51 after the change: pinned so `verify` never trusts the receipt alone.
NEW_SHA256 = {'EN': '8c39b696c87f9c656db94c41b4f9c3d3626c51c97ab1cf9d724668bd3493b4e9',
              'IT': '81caac546b3696eaed7a40329eac9bf5d97f59818699b77bd9cc30efa3830fa3'}

DESCRIPTIONS = {'EN': 'Prevents accuracy loss.\nIgnores evasion changes.',
                'IT': 'Evita cali di precisione e\nignora i cambi d’elusione.'}

WINDOWS = {
    'summary_skills': {'width_px': 152, 'height_px': 32, 'text_x': 3, 'usable_px': 149,
                       'template_address': 0x02104D04 + 7 * 8},
    'battle_summary_skills': {'width_px': 144, 'height_px': 32, 'text_x': 0, 'usable_px': 144,
                              'template_address': 0x0222522C + 2 * 8},
}

# Halfwords and literals that fix the print parameters, checked in the image itself.
ARM9_CODE_FACTS = {0x0208D3B4: 0x4A2D,   # ldr r2,[pc] -> bank literal
                   0x0208D3D4: 0x2100,   # movs r1,#0  (font 0, y 0)
                   0x0208D3D8: 0x20FF,   # movs r0,#0xff (speed)
                   0x0208D3EC: 0x3070,   # adds r0,#0x70 (window 7)
                   0x0208D3EE: 0x2303}   # movs r3,#3 (x)
ARM9_LITERALS = {0x0208D46C: BANK, 0x0208D458: 0x00010200}
OV8_CODE_FACTS = {0x0221EC7A: 0x2016,    # movs r0,#0x16 (windows per page)
                  0x0221EC9C: 0x2100,    # movs r1,#0 (font 0, y 0)
                  0x0221EC9E: 0x1CA0,    # adds r0,r4,#2 (window index + 2)
                  0x0221ECB4: 0x1C0B,    # adds r3,r1,#0 (x 0)
                  0x0221DC7A: 0x2123}    # movs r1,#0x23 (35 windows for this page set)
OV8_LITERALS = {0x0221ECDC: BANK, 0x0221DD08: 0x0222522C}


def row_sha256(words):
    return hashlib.sha256(struct.pack('<%dH' % len(words), *words)).hexdigest()


def crc16(data):
    """CRC-16 (poly 0xA001, init 0xFFFF) as stored in the DS cartridge header."""
    value = 0xFFFF
    for byte in data:
        value ^= byte
        for _ in range(8):
            value = (value >> 1) ^ 0xA001 if value & 1 else value >> 1
    return value


def load_charmap(path):
    """Return (char -> code, code -> char) from the pinned pret charmap."""
    path = Path(path)
    if not path.is_file():
        raise ValueError('charmap file not found')
    if hashlib.sha256(path.read_bytes()).hexdigest() != CHARMAP_SHA256:
        raise ValueError('charmap is not the pinned pret charmap')
    spec = importlib.util.spec_from_file_location(
        'modern_accuracy_codec', SOURCE / 'features/options/tools/codifica_testo.py')
    codec = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(codec)
    table, _ = codec.carica_charmap(path)
    inverse = {}
    for char, code in table.items():
        inverse.setdefault(code, char)
    return table, inverse


def make_encoder(table):
    def encode(value):
        unknown = sorted({c for c in value if c not in table})
        if unknown:
            raise ValueError('unmapped characters: ' + ''.join(unknown))
        return [table[c] for c in value] + [TERMINATOR]
    return encode


# Independent message reader (format only; it does not use translation.message_codec).
def row_span(raw, index):
    raw = bytes(raw)
    if len(raw) < 4:
        raise ValueError('truncated bank header')
    count, key = struct.unpack_from('<HH', raw)
    if not 0 <= index < count or 4 + 8 * count > len(raw):
        raise ValueError('row outside the bank')
    mask = (765 * (index + 1) * key) & 0xFFFF
    mask |= mask << 16
    offset, length = struct.unpack_from('<II', raw, 4 + 8 * index)
    offset ^= mask
    length ^= mask
    if offset < 4 + 8 * count or offset + 2 * length > len(raw):
        raise ValueError('row exceeds the bank')
    return offset, offset + 2 * length


def decode_row(raw, index):
    start, end = row_span(raw, index)
    seed = ((index + 1) * 596947) & 0xFFFF
    words = []
    for (word,) in struct.iter_unpack('<H', bytes(raw)[start:end]):
        words.append(word ^ seed)
        seed = (seed + 18749) & 0xFFFF
    return words


def font_widths(font_member):
    """Validated 509 glyph advances of font member 0 (index = glyph code - 1)."""
    font_member = bytes(font_member)
    if hashlib.sha256(font_member).hexdigest() != FONT_SHA256:
        raise ValueError('font member is not the pinned font 0')
    header, start, count = struct.unpack_from('<III', font_member)
    if (header, start, count) != (16, 32592, GLYPHS) or font_member[12:16] != bytes([16, 16, 2, 2]):
        raise ValueError('unexpected font header')
    widths = font_member[start:start + count]
    if len(widths) != GLYPHS or hashlib.sha256(widths).hexdigest() != WIDTHS_SHA256:
        raise ValueError('unexpected glyph advance table')
    return widths


def measure(words, widths):
    """Advance in pixels of each line of one message (font 0: no spacing)."""
    words = list(words)
    if not words or words[-1] != TERMINATOR or TERMINATOR in words[:-1]:
        raise ValueError('message must end with exactly one terminator')
    lines = [0]
    for word in words[:-1]:
        if word == NEWLINE:
            lines.append(0)
        elif 1 <= word <= len(widths):
            lines[-1] += widths[word - 1]
        else:
            raise ValueError('code %#06x has no glyph advance (control codes are not allowed)' % word)
    return lines


def fit_report(words, widths):
    """Measure against both real windows; refuse anything that would be clipped."""
    lines = measure(words, widths)
    if len(words) > MAX_WORDS:
        raise ValueError('message does not fit the 128-word summary string')
    if len(lines) > MAX_LINES:
        raise ValueError('%d lines: the 32 px windows show two' % len(lines))
    windows = {}
    for name, window in WINDOWS.items():
        fits = max(lines) <= window['usable_px']
        windows[name] = {'fits': fits, 'lines': len(lines), 'max_px': max(lines),
                         'usable_px': window['usable_px'], 'width_px': window['width_px'],
                         'height_px': window['height_px'], 'text_x': window['text_x']}
        if not fits:
            raise ValueError('line of %d px exceeds the %s window (%d px usable)'
                             % (max(lines), name, window['usable_px']))
    return {'lines': lines, 'line_count': len(lines), 'max_px': max(lines), 'words': len(words),
            'fits': True, 'windows': windows}


def _bank_class():
    import sys
    if str(SOURCE) not in sys.path:
        sys.path.insert(0, str(SOURCE))
    from translation.message_codec import Bank
    return Bank


def patch_bank(raw_bank, language, encode, *, expected_sha=None, widths=None):
    """Return (new bank bytes, receipt) with only row 51 replaced.

    `expected_sha` overrides the pinned retail row hash (tests with synthetic banks).
    With `widths` (509 advances) the new row is measured and must fit both windows.
    """
    if language not in DESCRIPTIONS:
        raise ValueError('language must be EN or IT')
    Bank = _bank_class()
    raw = bytes(raw_bank)
    bank = Bank(raw)
    if len(bank.words) != ROWS:
        raise ValueError('ability description bank must have 124 rows')
    if Bank.from_words(bank.words, key=bank.key).save() != raw:
        raise ValueError('bank layout is not the canonical one: refusing to rewrite it')
    old_sha = row_sha256(bank.words[ROW])
    words = encode(DESCRIPTIONS[language])
    if not words or words[-1] != TERMINATOR or any(not isinstance(w, int) or not 0 <= w <= 0xFFFF for w in words):
        raise ValueError('encoder returned an invalid message')
    new_sha = row_sha256(words)
    if old_sha == new_sha:
        raise ValueError('row 51 already has the new description')
    if old_sha != (expected_sha or PREIMAGE_SHA256[language]):
        raise ValueError('row 51 is not the expected %s retail description' % language)
    report = None
    if widths is not None:
        if len(widths) != GLYPHS:
            raise ValueError('glyph advance table must have 509 entries')
        report = fit_report(words, widths)
    others = [w.copy() for i, w in enumerate(bank.words) if i != ROW]
    bank.replace(ROW, words)
    patched = bank.save()
    check = Bank(patched)
    if [w for i, w in enumerate(check.words) if i != ROW] != others or check.words[ROW] != words \
            or check.key != bank.key or len(check.words) != ROWS:
        raise ValueError('rewritten bank does not read back')
    receipt = {'language': language, 'archive': ARCHIVE, 'bank': BANK, 'row': ROW,
               'old_sha256': old_sha, 'new_sha256': new_sha, 'new_words': len(words),
               'rows_identical': ROWS - 1,
               'bank_bytes_before': len(raw), 'bank_bytes_after': len(patched),
               'bank_sha256_before': hashlib.sha256(raw).hexdigest(),
               'bank_sha256_after': hashlib.sha256(patched).hexdigest()}
    if report:
        receipt.update(lines_px=report['lines'], line_count=report['line_count'],
                       max_px=report['max_px'], windows=report['windows'])
        ceiling = 0
        for index, other in enumerate(bank.words):
            if index != ROW:
                ceiling = max(ceiling, max(measure(other, widths)))
        receipt['retail_ceiling_px'] = ceiling
    return patched, receipt


def _check_facts(blob, base, facts, literals, label):
    for address, expected in facts.items():
        found = struct.unpack_from('<H', blob, address - base)[0]
        if found != expected:
            raise ValueError('%s halfword at %#x is %#06x, expected %#06x' % (label, address, found, expected))
    for address, expected in literals.items():
        found = struct.unpack_from('<I', blob, address - base)[0]
        if found != expected:
            raise ValueError('%s literal at %#x is %#x, expected %#x' % (label, address, found, expected))


def read_window_facts(rom):
    """Re-read both window templates and the print parameters from a parsed image."""
    arm9 = bytes(rom.arm9)
    _check_facts(arm9, rom.arm9RamAddress, ARM9_CODE_FACTS, ARM9_LITERALS, 'ARM9')
    overlay = ndspy_load_overlays_sicuri(rom, [8])[8]
    ov8 = bytes(overlay.data)
    _check_facts(ov8, overlay.ramAddress, OV8_CODE_FACTS, OV8_LITERALS, 'overlay 8')

    def entry(blob, base, address):
        bg, left, top, width, height, palette, block = struct.unpack_from('<6BH', blob, address - base)
        return [bg, left, top, width, height, palette, block]

    summary = entry(arm9, rom.arm9RamAddress, WINDOWS['summary_skills']['template_address'])
    battle = [entry(ov8, overlay.ramAddress, 0x0222522C + 2 * 8),
              entry(ov8, overlay.ramAddress, 0x0222522C + 24 * 8)]
    expected = {'summary_skills': summary, 'battle_summary_skills': battle[0]}
    for name, template in expected.items():
        window = WINDOWS[name]
        if (template[3] * 8, template[4] * 8) != (window['width_px'], window['height_px']):
            raise ValueError('%s template is %dx%d tiles' % (name, template[3], template[4]))
    if battle[0][:6] != battle[1][:6]:
        raise ValueError('battle summary page sets differ in geometry')
    return {'summary_skills': {'template': summary, 'text_x': 3, 'bank_literal': BANK},
            'battle_summary_skills': {'templates': battle, 'text_x': 0, 'bank_literal': BANK}}


def _read(data):
    from ndspy.narc import NARC
    from ndspy.rom import NintendoDSRom
    rom = NintendoDSRom(bytes(data))
    file_id = rom.filenames.idOf(ARCHIVE)
    font = NARC(rom.files[rom.filenames.idOf(FONT_ARCHIVE)]).files[0]
    return rom, file_id, NARC(rom.files[file_id]), font_widths(font), bytes(font)


def apply(data, language, charmap_path):
    """Return (image with the new row 51, receipt). `data` is not modified."""
    if language not in DESCRIPTIONS:
        raise ValueError('language must be EN or IT')
    import sys
    if str(SOURCE) not in sys.path:
        sys.path.insert(0, str(SOURCE))
    from sgp13.resources import append_file
    table, _ = load_charmap(charmap_path)
    data = bytes(data)
    rom, file_id, narc, widths, font = _read(data)
    facts = read_window_facts(rom)
    original_narc = bytes(rom.files[file_id])
    if narc.save() != original_narc:
        raise ValueError('the message archive is not in the canonical layout')
    if len(narc.files) <= BANK:
        raise ValueError('archive has no member 722')
    patched, receipt = patch_bank(narc.files[BANK], language, make_encoder(table), widths=widths)
    narc.files[BANK] = patched
    payload = narc.save()
    image = append_file(data, file_id, payload)
    start = struct.unpack_from('<I', image, struct.unpack_from('<I', image, 0x48)[0] + 8 * file_id)[0]
    for name, found in facts.items():
        receipt['windows'][name].update(found)
    receipt.update(file_id=file_id, archive_bytes_before=len(original_narc), archive_bytes_after=len(payload),
                   archive_sha256_before=hashlib.sha256(original_narc).hexdigest(),
                   archive_sha256_after=hashlib.sha256(payload).hexdigest(),
                   appended_offset=start, image_bytes_before=len(data), image_bytes_after=len(image),
                   image_sha256_before=hashlib.sha256(data).hexdigest(),
                   image_sha256_after=hashlib.sha256(image).hexdigest(),
                   font={'sha256': hashlib.sha256(font).hexdigest(), 'widths_sha256': WIDTHS_SHA256,
                         'header': [16, 32592, GLYPHS, 16, 16, 2, 2]},
                   charmap_sha256=CHARMAP_SHA256)
    return image, receipt


def _differences(before, after, allowed):
    """Count bytes of `before` that differ in `after` outside the allowed (start, end) ranges."""
    cursor, count = 0, 0
    before, after = memoryview(before), memoryview(after)
    for start, end in sorted(allowed) + [(len(before), len(before))]:
        if before[cursor:start] != after[cursor:start]:
            count += sum(1 for a, b in zip(before[cursor:start], after[cursor:start]) if a != b)
        cursor = max(cursor, end)
    return count


def verify(before, after, receipt, *, charmap_path=None):
    """Independent read-back of `apply`: structure, rows, members, geometry, measures."""
    from ndspy.narc import NARC
    from ndspy.rom import NintendoDSRom
    before, after = bytes(before), bytes(after)
    language = receipt.get('language')
    if language not in DESCRIPTIONS:
        raise ValueError('receipt language')
    if len(after) <= len(before) or len(before) < 0x200:
        raise ValueError('the new image must be an append-only extension')
    fat, fat_size = struct.unpack_from('<II', before, 0x48)
    old_rom, new_rom = NintendoDSRom(before), NintendoDSRom(after)
    file_id = old_rom.filenames.idOf(ARCHIVE)
    if new_rom.filenames.idOf(ARCHIVE) != file_id or len(old_rom.files) != len(new_rom.files):
        raise ValueError('file table changed')
    start = (len(before) + 511) & ~511
    end = len(after)
    entry = fat + 8 * file_id
    if struct.unpack_from('<II', after, entry) != (start, end):
        raise ValueError('archive FAT entry does not point at the appended archive')
    if struct.unpack_from('<I', after, 0x80)[0] != end:
        raise ValueError('declared cartridge length')
    capacity = before[0x14]
    while end > (0x20000 << capacity):
        capacity += 1
    if after[0x14] != capacity:
        raise ValueError('cartridge capacity byte')
    if struct.unpack_from('<H', after, 0x15E)[0] != crc16(after[:0x15E]):
        raise ValueError('header CRC')
    if set(after[len(before):start]) - {0xFF}:
        raise ValueError('padding before the appended archive is not 0xFF')
    outside = _differences(before, after, [(0x14, 0x15), (0x80, 0x84), (0x15E, 0x160), (entry, entry + 8)])
    if outside:
        raise ValueError('%d bytes changed outside the header and the archive FAT entry' % outside)
    for index, (old, new) in enumerate(zip(old_rom.files, new_rom.files)):
        if index != file_id and old != new:
            raise ValueError('file %d changed' % index)
    old_narc, new_narc = NARC(old_rom.files[file_id]), NARC(new_rom.files[file_id])
    if new_rom.files[file_id] != after[start:end] or len(old_narc.files) != len(new_narc.files):
        raise ValueError('archive member count or location')
    members = 0
    for index, (old, new) in enumerate(zip(old_narc.files, new_narc.files)):
        if index == BANK:
            continue
        if bytes(old) != bytes(new):
            raise ValueError('archive member %d changed' % index)
        members += 1
    old_bank, new_bank = bytes(old_narc.files[BANK]), bytes(new_narc.files[BANK])
    if struct.unpack_from('<HH', old_bank) != struct.unpack_from('<HH', new_bank) or \
            struct.unpack_from('<H', new_bank)[0] != ROWS:
        raise ValueError('bank row count or key changed')
    for index in range(ROWS):
        if index != ROW and decode_row(old_bank, index) != decode_row(new_bank, index):
            raise ValueError('row %d changed' % index)
    old_row, new_row = decode_row(old_bank, ROW), decode_row(new_bank, ROW)
    if row_sha256(old_row) != receipt.get('old_sha256') or row_sha256(old_row) != PREIMAGE_SHA256[language]:
        raise ValueError('the before image does not hold the retail row 51')
    if row_sha256(new_row) != receipt.get('new_sha256') or row_sha256(new_row) != NEW_SHA256[language] \
            or old_row == new_row:
        raise ValueError('row 51 in the after image is not the receipt row')
    if charmap_path is not None:
        _, inverse = load_charmap(charmap_path)
        if any(w not in inverse for w in new_row[:-1]) or \
                ''.join(inverse[w] for w in new_row[:-1]) != DESCRIPTIONS[language]:
            raise ValueError('row 51 does not decode to the expected description')
    widths = font_widths(NARC(new_rom.files[new_rom.filenames.idOf(FONT_ARCHIVE)]).files[0])
    report = fit_report(new_row, widths)
    if report['lines'] != receipt.get('lines_px') or report['line_count'] != receipt.get('line_count'):
        raise ValueError('measures differ from the receipt')
    facts = read_window_facts(new_rom)
    ceiling = max(max(measure(decode_row(new_bank, i), widths)) for i in range(ROWS) if i != ROW)
    if report['max_px'] > ceiling or ceiling != receipt.get('retail_ceiling_px'):
        raise ValueError('line exceeds the retail ceiling or the receipt ceiling is wrong')
    return {'language': language, 'rows_identical': ROWS - 1, 'members_identical': members,
            'files_identical': len(old_rom.files) - 1, 'bytes_changed_outside_expected': outside,
            'lines_px': report['lines'], 'line_count': report['line_count'],
            'retail_ceiling_px': ceiling, 'windows': report['windows'], 'window_facts': facts,
            'archive_bytes_after': end - start, 'appended_offset': start}
