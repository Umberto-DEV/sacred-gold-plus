"""Native Summary controls legend (L: EV, SELECT: Stat., R: IV) for V4-derived inputs.

The installed EV/IV viewer (ITCM payload at 0x01FF8620, reader at 0x01FF8658) is
never recompiled, moved or edited: it reads the raw physical keys, so L, R and
SELECT keep working when the saved button mode is L=A. This module only

  * pins the viewer, the Summary hooks, the window tables and every native
    function the legend calls (`measure` / `audit`): hashes of *byte intervals*
    (`intervals`) and the complete bytes of every instruction it patches. It
    never hashes the whole ROM, so it composes after any stage that leaves those
    intervals alone (the UI, the other c8 modules) and refuses one that touches them,
  * inventories the Summary's sub-screen window rectangles and tile ranges
    from the ROM tables (`inventory`), and refuses a geometry that collides,
  * compiles `features/summary-controls/runtime.c` for an *assigned* base and
    builds the guarded installer (`prepare` / `verify`).

Nothing here chooses a base address, a window rectangle or a base tile: they
arrive as arguments from a reviewed assignment and from a runtime measurement.
Without that evidence the installed payload is inert (activation flag 0).
"""
import copy
import hashlib
import importlib.util
import json
import re
import shutil
import struct
import subprocess
from sgp13.compiler import compiler_path, compiler_environment
import tempfile
from pathlib import Path

from . import baseline, reserve  # read-only: the reserve range and policy are imported, never duplicated
from sgp12.rom import valida_layout_arm9

SOURCE = Path(__file__).resolve().parents[1]
ABI_PATH = Path(__file__).parent / 'data' / 'controls-native-abi.json'
FEATURE = SOURCE / 'features' / 'summary-controls'
LANGUAGES = ('EN', 'IT')

# One line, native font 0. `compact` is the plan's 124 px band; `spaced` (132 px) separates the three
# commands with two spaces and needs a 17-tile window. Same text in EN and IT: key names and the
# EV/IV initials are international, and "Stat." is the abbreviation the plan fixes.
LEGEND = {'compact': 'L:EV SELECT:Stat. R:IV', 'spaced': 'L:EV  SELECT:Stat.  R:IV'}
VARIANTS = tuple(LEGEND)
TERMINATOR = 0xFFFF
STRING_MAGIC = 0xB6F8D2EC
HOOK_PREFIX = bytes.fromhex('004b1847')  # ldr r3, [pc]; bx r3; .word target
BG_TILE_LIMIT = 1024                      # 10-bit tilemap entry
SUB_BG = 4                                # window bgId of the lower-screen text layer

SPAN_DEFS = (
    ('viewer.payload', 0x01FF8620, 592),
    ('viewer.reset_header', 0x01FF8620, 56),
    ('viewer.reader', 0x01FF8658, 448),
    ('viewer.entries', 0x01FF881C, 84),
    ('viewer.label_wrapper', 0x01FF9348, 0x58),
    ('summary.init_windows', 0x0208C3E4, 0x48),
    ('summary.alloc_pages', 0x0208C42C, 0xB4),
    ('summary.teardown', 0x0208C4E0, 0x80),
    ('summary.exit', 0x0208C560, 0x1C),
    ('summary.dispatch', 0x0208CBD4, 0xB4),
    ('summary.stats_draw', 0x0208D180, 0x2F4),
    ('summary.page_change', 0x02089D68, 172),     # the function holding the BL site 0x02089D78, whole
    ('summary.input_main', 0x02088B48, 0x1D0),
    ('summary.init', 0x02088298, 0x18C),
)
HOOK_DEFS = {'input': 0x02088B40, 'redraw': 0x0208D178}
EDGE_TARGETS = {'teardown_callers': 0x0208C4E0, 'redraw_callers': 0x0208D178,
                'alloc_pages_callers': 0x0208C42C, 'dispatch_callers': 0x0208CBD4}
# Whole bodies of the ten native functions the legend calls: (address, bytes). The size is the function extent
# (first return past every forward branch, plus its literal pool); the byte after it starts the next function.
NATIVE_DEFS = {
    'add_window': (0x0201D4F8, 40), 'fill_window': (0x0201D978, 56),
    'copy_window': (0x0201D5C8, 80), 'clear_window': (0x0201D8C8, 28), 'delete_windows': (0x0201D54C, 44),
    'print': (0x020200FC, 84), 'get_mon': (0x0208A520, 68), 'get_box_data': (0x0206E640, 96),
    'heap_alloc': (0x0201AA8C, 64), 'heap_free': (0x0201AB0C, 116),
}
TABLE_DEFS = {'page0': (0x02104CC4, 8), 'page2': (0x02104C84, 8), 'page_skills': (0x02104D04, 18),
              'shared': (0x02104D94, 34)}
BG_DEFS = {'bg1': 0x021038E8, 'bg4': 0x0210393C}
LITERAL_DEFS = {'summary_object_bytes': (0x02088414, 0x7D8), 'page_offset': (0x0208C55C, 0x7BC),
                'state_offset': (0x02088CF8, 0x7BF), 'viewer_keys_raw': (0x01FF87F8, 0x021D1148)}

CHARMAP_SHA256 = '58861d34f40623fd2a9b29c10a79ee2ec872182285a288381759a3b251412ded'   # pret charmap.txt (rev 0985e87)
COMPILER_VERSION = 'Apple clang version 21.0.0 (clang-2100.4.1.1)'
COMPILER_SHA256 = 'fc5e3cbba6ad54059295cad716aacb05ace8235f5f7a6031f1d8c15d24bd6d66'
FLAGS = ['--target=armv5te-none-eabi', '-mcpu=arm946e-s', '-mthumb', '-Oz',
         '-ffreestanding', '-fno-builtin', '-fno-stack-protector', '-fomit-frame-pointer',
         '-fno-unwind-tables', '-fno-asynchronous-unwind-tables', '-Wall', '-Wextra',
         '-Werror', '-fno-jump-tables', '-fstack-usage', '-std=c11']
FREE_SPACE_FLOOR = 10 * 1024 ** 3


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _sha(data):
    return hashlib.sha256(bytes(data)).hexdigest()


def hex_int(value):
    _require(type(value) is str and re.fullmatch(r'0x[0-9A-Fa-f]{1,8}', value), 'bad hex field: %r' % (value,))
    return int(value, 16)


def _hx(value):
    return '0x%08X' % value


def load_abi():
    return json.loads(ABI_PATH.read_text())


# --- pure helpers ---------------------------------------------------------

def compare_pins(actual, expected, path=''):
    """Raise ValueError('<path>: ...') at the first difference between two pin trees."""
    if isinstance(expected, dict):
        _require(isinstance(actual, dict), '%s: expected an object' % (path or '<root>'))
        for key in sorted(set(expected) | set(actual)):
            here = '%s.%s' % (path, key) if path else key
            _require(key in actual, '%s: missing from the measurement' % here)
            _require(key in expected, '%s: not in the pin file' % here)
            compare_pins(actual[key], expected[key], here)
    elif isinstance(expected, list):
        _require(isinstance(actual, list) and len(actual) == len(expected), '%s: list differs' % path)
        for index, (a, e) in enumerate(zip(actual, expected)):
            compare_pins(a, e, '%s[%d]' % (path, index))
    else:
        _require(actual == expected, '%s: expected %r, found %r' % (path, expected, actual))


def encode_bl(site, target):
    delta = (target & ~1) - site - 4
    _require(target & 1 and delta % 2 == 0, 'Thumb BL needs an odd (Thumb) target')
    _require(-0x400000 <= delta < 0x400000, 'BL target out of Thumb range')
    return struct.pack('<HH', 0xF000 | (delta >> 12 & 0x7FF), 0xF800 | (delta >> 1 & 0x7FF))


def decode_bl(site, raw):
    _require(len(raw) == 4, 'BL is four bytes')
    high, low = struct.unpack('<HH', raw)
    _require(high & 0xF800 == 0xF000 and low & 0xF800 in (0xF800, 0xE800), 'not a Thumb BL/BLX pair')
    offset = (high & 0x7FF) << 12 | (low & 0x7FF) << 1
    if offset & 0x400000:
        offset -= 0x800000
    return (site + 4 + offset) & 0xFFFFFFFF | (1 if low & 0xF800 == 0xF800 else 0)


def encode_literal_hook(literal):
    return HOOK_PREFIX + struct.pack('<I', literal)


def decode_literal_hook(raw):
    _require(len(raw) == 8 and raw[:4] == HOOK_PREFIX, 'not a literal-pool hook (ldr r3,[pc]; bx r3)')
    return struct.unpack_from('<I', raw, 4)[0]


EVIDENCE_FIELDS = {'kind', 'capture_rom_sha256', 'build_id', 'language', 'geometry', 'views', 'button_modes',
                   'contexts', 'captures', 'free_tiles', 'hidden_windows'}
REQUIRED_VIEWS = {'stats', 'ev', 'iv'}
# gSystem.buttonMode has four values (pret system.h): Normal, Start=X, Swap X/Y and L=A. Only L=A hides L and R
# from the processed keys; the viewer reads the raw keys, so the legend is checked in Normal and L=A.
REQUIRED_BUTTON_MODES = {'normal', 'L=A'}
REQUIRED_CONTEXTS = {'field', 'pc'}
_HEX64 = re.compile(r'[0-9a-f]{64}')


def _is_sha256(value):
    return type(value) is str and _HEX64.fullmatch(value) is not None


def check_evidence(evidence, geometry, candidate_sha256, language):
    """A runtime-inventory record must be bound to the candidate ROM it was captured on, the language, the
    geometry, the views, the key modes and the captures.

    `candidate_sha256` is the sha256 of the inert candidate ROM that was played (what Codex measured), not of
    the stage input: the evidence names it as `capture_rom_sha256` and the two must be equal."""
    _require(_is_sha256(candidate_sha256), 'candidate_sha256 (the inert candidate ROM that was captured) is required')
    _require(type(evidence) is dict and evidence.get('kind') == 'summary-window-inventory',
             'evidence must be a summary-window-inventory record')
    _require(set(evidence) == EVIDENCE_FIELDS, 'evidence fields must be exactly %s' % sorted(EVIDENCE_FIELDS))
    _require(_is_sha256(evidence['capture_rom_sha256']), 'evidence capture_rom_sha256 must be a lowercase sha256')
    _require(evidence['capture_rom_sha256'] == candidate_sha256,
             'evidence belongs to another ROM (capture_rom_sha256 differs from candidate_sha256)')
    _require(type(evidence['build_id']) is str and evidence['build_id'].strip(), 'evidence build_id')
    _require(evidence['language'] == language, 'evidence belongs to another language')
    _require(evidence['geometry'] == geometry, 'evidence was measured for a different geometry')
    for field, required in (('views', REQUIRED_VIEWS), ('button_modes', REQUIRED_BUTTON_MODES),
                            ('contexts', REQUIRED_CONTEXTS)):
        _require(type(evidence[field]) is list and required <= set(evidence[field]),
                 'evidence must cover %s: %s' % (field, sorted(required)))
    captures = evidence['captures']
    _require(type(captures) is list and captures and all(
        type(c) is dict and set(c) == {'name', 'sha256'} and type(c['name']) is str and c['name']
        and _is_sha256(c['sha256']) for c in captures),
        'evidence needs capture references {name, sha256}')
    free = evidence['free_tiles']
    _require(type(free) is list and len(free) == 2 and all(type(v) is int for v in free), 'evidence free tiles')
    _require(type(evidence['hidden_windows']) is list and all(type(v) is str for v in evidence['hidden_windows']),
             'evidence hidden windows')


def check_geometry(geometry, inventory, evidence=None, active=False, candidate_sha256=None, language=None):
    """Validate a legend window against the Summary's sub-screen inventory.

    Tile collisions with a native window are always fatal. A rectangle over a native window is fatal
    unless the runtime evidence names that window as hidden/unused in every supported view; activation
    additionally needs the free-tile claim. The evidence is bound (check_evidence) to the candidate ROM,
    language, exact geometry, the three views, the key modes and the contexts, and cites its captures by hash.
    """
    fields = {'bgId', 'left', 'top', 'width', 'height', 'palette', 'baseTile'}
    _require(type(geometry) is dict and set(geometry) == fields, 'geometry needs exactly %s' % sorted(fields))
    _require(all(type(geometry[f]) is int for f in fields), 'geometry values must be integers')
    _require(geometry['bgId'] == SUB_BG, 'the legend lives on the lower-screen text layer (bgId 4)')
    _require(geometry['height'] == 2 and 1 <= geometry['width'] <= 28, 'window must be 2 tiles high, 1..28 wide')
    _require(0 <= geometry['left'] and geometry['left'] + geometry['width'] <= 32, 'window leaves the tilemap horizontally')
    _require(0 <= geometry['top'] and geometry['top'] + geometry['height'] <= 24, 'window leaves the lower screen')
    _require(0 <= geometry['palette'] < 16, 'palette 0..15')
    count = geometry['width'] * geometry['height']
    low, high = geometry['baseTile'], geometry['baseTile'] + count - 1
    limit = inventory.get('tile_limit', BG_TILE_LIMIT)
    _require(0 <= low and high < limit, 'tile range %d..%d leaves the 10-bit tilemap entry (limit %d)' % (low, high, limit))
    for owner in inventory['tiles']:
        _require(high < owner['lo'] or low > owner['hi'],
                 'tile range %d..%d overlaps native %s (%d..%d)' % (low, high, owner['name'], owner['lo'], owner['hi']))
    right, bottom = geometry['left'] + geometry['width'], geometry['top'] + geometry['height']
    overlapping = sorted({w['name'] for w in inventory['rects']
                          if geometry['left'] < w['left'] + w['width'] and w['left'] < right
                          and geometry['top'] < w['top'] + w['height'] and w['top'] < bottom})
    proven = False
    if evidence is not None:
        check_evidence(evidence, geometry, candidate_sha256, language)
        free = evidence['free_tiles']
        _require(free[0] <= low and high <= free[1], 'evidence does not declare free tiles %d..%d' % (low, high))
        missing = [name for name in overlapping if name not in set(evidence['hidden_windows'])]
        _require(not missing, 'rectangle overlaps native window(s) without a hidden proof: %s' % ', '.join(missing))
        proven = True
    elif active:
        raise ValueError('activation needs runtime inventory evidence (none supplied)')
    return {'tiles': [low, high], 'rect': [geometry['left'], geometry['top'], right, bottom],
            'overlapping_windows': overlapping, 'proven': proven}


def legend_text(language, variant='compact'):
    _require(language in LANGUAGES, 'unsupported language: %r' % (language,))
    _require(variant in LEGEND, 'unsupported legend variant: %r' % (variant,))
    return LEGEND[variant]


def _charmap_module():
    path = SOURCE / 'features/options/tools/codifica_testo.py'
    spec = importlib.util.spec_from_file_location('summary_controls_codifica', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def check_charmap(charmap):
    """The legend codes come from this file: it must be the pinned pret charmap (recorded in the receipt)."""
    digest = _sha(Path(charmap).read_bytes())
    _require(digest == CHARMAP_SHA256, 'charmap differs from the pinned pret charmap (sha256 %s)' % digest)
    return digest


def encode_legend(language, charmap, variant='compact'):
    """Legend as 16-bit charmap codes plus 0xFFFF, one line, no substitution."""
    module = _charmap_module()
    table, source = module.carica_charmap(Path(charmap))
    _require(source != 'tabella-minima', 'charmap file not readable: %s' % charmap)
    return module.codifica(legend_text(language, variant), table)


def font_widths(data):
    """The 509 glyph advances of native font 0 (a/0/1/6 member 0), read from the ROM image."""
    import ndspy.narc
    import ndspy.rom
    narc = ndspy.narc.NARC(ndspy.rom.NintendoDSRom(bytes(data)).getFileByName('a/0/1/6'))
    member = narc.files[0]
    _require(len(member) == 33101, 'font member 0 is not the 33101-byte HGSS font')
    return bytes(member[-510:-1])


def string_object(codes):
    """Native String: maxsize, size, magic, then the 16-bit codes (padded to 4 bytes)."""
    codes = list(codes)
    _require(codes and codes[-1] == TERMINATOR and TERMINATOR not in codes[:-1], 'codes must end with one 0xFFFF')
    blob = struct.pack('<HHI', len(codes), len(codes), STRING_MAGIC) + struct.pack('<%dH' % len(codes), *codes)
    return blob + bytes(-len(blob) % 4)


def measure_advance(table, codes):
    total = 0
    for code in codes:
        if code == TERMINATOR:
            break
        _require(code < len(table), 'glyph code 0x%04X has no width entry' % code)
        total += table[code]
    return total


# --- ROM readers (bytes in memory only) -----------------------------------

def _arm9_segments(data):
    offset, _, base, length = struct.unpack_from('<4I', data, 0x20)
    table, table_end, body, _bss, _, packed = struct.unpack_from('<6I', data, offset + 0xBA0)
    _require(base == 0x02000000 and not packed and base < body <= table <= table_end <= base + length,
             'ARM9 initialized layout')
    _t0, _t1, _d0, _sections, segments = valida_layout_arm9(
        data, offset, base, length)
    return segments


def rom_offset(data, address, size=1, segments=None):
    found = [rom + address - start for start, rom, count in (segments or _arm9_segments(data))
             if start <= address and address + size <= start + count]
    _require(len(found) == 1, 'address 0x%08X+%d is not in exactly one ARM9 segment' % (address, size))
    return found[0]


def read(data, address, size, segments=None):
    at = rom_offset(data, address, size, segments)
    return bytes(data[at:at + size])


def _word(data, address, segments=None):
    return struct.unpack('<I', read(data, address, 4, segments))[0]


def _bl_edges(data, segments):
    """Every complete Thumb BL in the static ARM9: target -> sorted call sites."""
    edges = {}
    start, rom, count = segments[0]
    raw = data[rom:rom + count]
    for index in range(0, count - 3, 2):
        high, low = struct.unpack_from('<HH', raw, index)
        if high & 0xF800 == 0xF000 and low & 0xF800 == 0xF800:
            offset = (high & 0x7FF) << 12 | (low & 0x7FF) << 1
            if offset & 0x400000:
                offset -= 0x800000
            site = start + index
            edges.setdefault(site + 4 + offset & 0xFFFFFFFF, []).append(site)
    return edges


def measure(data):
    """Measure every pin from ROM bytes: the shape stored in controls-native-abi.json."""
    segments = _arm9_segments(data)
    rd = lambda address, size: read(data, address, size, segments)
    spans = {name: {'address': _hx(address), 'bytes': size, 'sha256': _sha(rd(address, size))}
             for name, address, size in SPAN_DEFS}
    hooks = {}
    for name, address in HOOK_DEFS.items():
        raw = rd(address, 8)
        hooks[name] = {'address': _hx(address), 'bytes': raw.hex(), 'target': _hx(decode_literal_hook(raw))}
    edges_all = _bl_edges(data, segments)
    edges = {name: [_hx(site) for site in sorted(edges_all.get(target, ()))] for name, target in EDGE_TARGETS.items()}
    natives = {name: {'address': _hx(address), 'bytes': size, 'sha256': _sha(rd(address, size))}
               for name, (address, size) in NATIVE_DEFS.items()}
    tables = {name: {'address': _hx(address), 'entries': count, 'sha256': _sha(rd(address, 8 * count))}
              for name, (address, count) in TABLE_DEFS.items()}
    bg = {}
    for name, address in BG_DEFS.items():
        x, y, size, base, scr, color, screen, char, ext, prio, over, _d, mosaic = struct.unpack('<4I8BI', rd(address, 28))
        bg[name] = {'address': _hx(address), 'sha256': _sha(rd(address, 28)), 'screen_base': screen,
                    'char_base': char, 'color_mode': color, 'size': scr, 'priority': prio}
    literals = {name: {'address': _hx(address), 'value': _hx(_word(data, address, segments))}
                for name, (address, _value) in LITERAL_DEFS.items()}
    return {'spans': spans, 'hooks': hooks, 'edges': edges, 'natives': natives, 'tables': tables, 'bg': bg,
            'literals': literals}


def expected_pins(abi=None):
    abi = abi or load_abi()
    return {key: abi[key] for key in ('spans', 'hooks', 'edges', 'natives', 'tables', 'bg', 'literals')}


def intervals(abi=None):
    """Every byte interval this module relies on, with its role: the explicit composition contract.

    `read` intervals are pinned by hash (spans, hook words, whole native bodies, window tables, background
    descriptors) or by value (literals); `write` intervals are the three BL sites (4 bytes each). The
    payload slot is the fourth write interval and comes from the reserve assignment, not from this list.
    Nothing outside these intervals is read, hashed or rewritten, except the scan of the static ARM9 for BL
    callers of the four hooked functions (`edges`), which is a completeness predicate, not a hash."""
    abi = abi or load_abi()
    rows = [(name, hex_int(item['address']), item['bytes'], 'read') for name, item in abi['spans'].items()]
    rows += [('hooks.' + name, hex_int(item['address']), 8, 'read') for name, item in abi['hooks'].items()]
    rows += [('natives.' + name, hex_int(item['address']), item['bytes'], 'read') for name, item in abi['natives'].items()]
    rows += [('tables.' + name, hex_int(item['address']), 8 * item['entries'], 'read') for name, item in abi['tables'].items()]
    rows += [('bg.' + name, hex_int(item['address']), 28, 'read') for name, item in abi['bg'].items()]
    rows += [('literals.' + name, hex_int(item['address']), 4, 'read') for name, item in abi['literals'].items()]
    rows += [('site.' + site, hex_int(site), 4, 'write') for site, _name, _target in SITES]
    return [{'name': name, 'start': start, 'end': start + size, 'role': role} for name, start, size, role in rows]


def audit(data, language, abi=None):
    """Compare the pinned byte intervals with `data`; raise ValueError naming the offending pin.

    The input does not have to be the exact V4 candidate: any image whose pinned intervals are intact is
    accepted, so the legend composes after the UI and the other stages. The language is the caller's
    declaration (the pins are identical in EN and IT); the evidence is bound to it separately."""
    abi = abi or load_abi()
    _require(language in LANGUAGES, 'unsupported language: %r' % (language,))
    measured = measure(data)
    expected = expected_pins(abi)
    # Literal values double as semantic checks: object size, page/state offsets, raw-key literal.
    for name, (address, value) in LITERAL_DEFS.items():
        _require(expected['literals'][name] == {'address': _hx(address), 'value': _hx(value)},
                 'literals.%s: pin file disagrees with the contract' % name)
    try:
        compare_pins(measured, expected)
    except ValueError as error:
        raise ValueError('a pinned interval was touched by another stage or the base is not supported: %s' % error) from None
    return measured


COEXISTING_TABLES = ('page_skills', 'shared')  # window arrays alive together on the Skills page


def inventory(data):
    """Lower-screen (bgId 4) tile ranges of every Summary window table, and the rectangles of
    the windows that coexist with the Skills page (its own array plus the 34 shared ones).
    Other pages' arrays are deleted by sub_0208C4E0 before they are created, so they never
    share the screen with the legend, but their tile ranges are still kept out as a margin.
    """
    segments = _arm9_segments(data)
    tiles, rects = [], []
    for table, (address, count) in TABLE_DEFS.items():
        raw = read(data, address, 8 * count, segments)
        for index in range(count):
            bg, left, top, width, height, _pal, base = struct.unpack_from('<6BH', raw, 8 * index)
            if bg != SUB_BG:
                continue
            name = '%s.%d' % (table, index)
            tiles.append({'name': name, 'lo': base, 'hi': base + width * height - 1})
            if table in COEXISTING_TABLES:
                rects.append({'name': name, 'left': left, 'top': top, 'width': width, 'height': height})
    return {'bg': SUB_BG, 'tile_limit': BG_TILE_LIMIT, 'tiles': tiles, 'rects': rects}


def _loader():
    path = SOURCE / 'features/options/tools/carica_text.py'
    spec = importlib.util.spec_from_file_location('summary_controls_loader', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


STATE_BYTES = 0x20
STATE_ENABLED = 0x10
WRAPPER_PROLOGUE = bytes.fromhex('10b50400')  # push {r4, lr}; movs r4, r0
ENTRIES = ('sgp_summary_controls_update', 'sgp_summary_controls_destroy', 'sgp_sc_redraw', 'sgp_sc_teardown')


def compile_payload(work, base, language, charmap, geometry, enabled=0, abi=None, variant='compact', codes=None):
    """Compile runtime.c for an assigned `base`; return (image, info).

    `codes` (the installed String, read back by `verify`) replaces the charmap encoding when given.
    `image` = the 32-byte resident record (zero but for the enabled word) followed
    by the position-fixed code and the legend String. `geometry` is validated by
    the caller (check_geometry); here it is only range-checked. Scratch lives
    under `work` and is removed on return.
    """
    abi = abi or load_abi()
    _require(type(base) is int and base % 4 == 0 and 0x02000000 <= base < 0x02400000, 'compile base must be aligned main RAM')
    _require(enabled in (0, 1), 'enabled is a flag')
    fields = {'bgId', 'left', 'top', 'width', 'height', 'palette', 'baseTile'}
    _require(type(geometry) is dict and set(geometry) == fields and geometry['bgId'] == SUB_BG, 'geometry shape')
    codes = list(codes) if codes is not None else encode_legend(language, charmap, variant)
    compiler = compiler_path(COMPILER_SHA256)
    _require(compiler is not None, 'clang unavailable')
    work = Path(work)
    _require(shutil.disk_usage(work).free >= FREE_SPACE_FLOOR, 'free-space floor (10 GiB)')
    version = subprocess.run([compiler, '--version'], env=compiler_environment(), capture_output=True, text=True, check=True).stdout.splitlines()[0]
    _require(version == COMPILER_VERSION, 'compiler version drift: ' + version)
    executable = _sha(Path(compiler).resolve().read_bytes())
    _require(executable == COMPILER_SHA256, 'compiler binary drift')
    config = '\n'.join([
        '#define SGP_SC_BASE 0x%08Xu' % base,
        '#define SGP_SC_LEFT %d' % geometry['left'], '#define SGP_SC_TOP %d' % geometry['top'],
        '#define SGP_SC_WIDTH %d' % geometry['width'], '#define SGP_SC_HEIGHT %d' % geometry['height'],
        '#define SGP_SC_PALETTE %d' % geometry['palette'], '#define SGP_SC_BASE_TILE %d' % geometry['baseTile'],
        '#define SGP_SC_TEXT_COUNT %d' % len(codes),
        '#define SGP_SC_TEXT_ASM "%s"' % ', '.join('0x%04X' % c for c in codes), ''])
    source = (FEATURE / 'runtime.c').read_bytes()
    header = (FEATURE / 'abi.h').read_bytes()
    with tempfile.TemporaryDirectory(prefix='summary-controls-', dir=work) as scratch:
        scratch = Path(scratch)
        (scratch / 'sgp_sc_config.h').write_text(config)
        obj = scratch / 'runtime.o'
        result = subprocess.run([compiler, *FLAGS, '-I', str(scratch), '-I', str(FEATURE), '-c',
                                 str(FEATURE / 'runtime.c'), '-o', str(obj)],
                                cwd=scratch, env=compiler_environment(), capture_output=True, text=True, timeout=60)
        _require(result.returncode == 0 and not result.stderr, 'runtime compile failed: ' + result.stderr)
        raw = obj.read_bytes()
        usage = (scratch / 'runtime.su').read_text()
    text, symbols = _loader().load_text(raw, base + STATE_BYTES, ENTRIES)
    text += bytes(-len(text) % 4)
    state = bytearray(STATE_BYTES)
    struct.pack_into('<I', state, STATE_ENABLED, enabled)
    image = bytes(state) + text
    stack = {}
    for row in (line.split('\t') for line in usage.splitlines() if line.strip()):
        stack[row[0].rsplit(':', 1)[-1]] = int(row[1])
    return image, {'base': base, 'language': language, 'bytes': len(image), 'code_bytes': len(text),
                   'string_codes': len(codes), 'variant': variant, 'symbols': {name: symbols[name] for name in ENTRIES},
                   'stack_bytes': stack, 'enabled': enabled, 'geometry': dict(geometry),
                   'image_sha256': _sha(image), 'source_sha256': _sha(source), 'abi_header_sha256': _sha(header),
                   'compiler': {'version': version, 'executable_sha256': executable, 'flags': FLAGS}}


SITES = (('0x0208CC5A', 'sgp_sc_redraw', 0x0208D178), ('0x02089D78', 'sgp_sc_teardown', 0x0208C4E0),
         ('0x0208C564', 'sgp_sc_teardown', 0x0208C4E0))
PROPOSAL = {'bgId': 4, 'left': 1, 'top': 18, 'width': 16, 'height': 2, 'palette': 13, 'baseTile': 955}


SLOT_NAME = 'summary-controls.runtime'
ALLOCATION_FIELDS = {'schema', 'input_sha256', 'language', 'policy_version', 'policy_sha256', 'audit_sha256', 'requested',
                     'assignments', 'preservation', 'address_reserved', 'installed', 'installation_authorized'}


def _reserve_policy():
    """(policy, sha256 of the policy file) in force. Tests replace this one function with a declared test policy."""
    raw = reserve.MAP.read_bytes()
    policy = json.loads(raw)
    reserve.validate_policy(policy)
    return policy, hashlib.sha256(raw).hexdigest()


def check_allocation(allocation, language, name=SLOT_NAME):
    """Accept a base only from a `reserve.allocate` receipt; return the assignment for `name`.

    The receipt is re-derived against the reserve policy in force: the same policy file, an input that is an
    exact V4 of this language, every requested name a non-conditional payload slot of that policy, and the
    assignment list identical to what `reserve.allocate` computes. The ROM bytes are not needed (the
    installer may run after other stages); the audit hash inside the receipt is only shape-checked."""
    if type(allocation) is dict and type(allocation.get('schema')) is int and allocation['schema'] == 2:
        # Downstream structure/policy constraint only. The builder MUST reissue this grant against the
        # exact pristine and cold-UI images; a JSON proof/hash is not authentication or authorization.
        validate = getattr(reserve, 'validate_allocation', None)
        _require(callable(validate), 'bound reserve allocation verifier unavailable')
        rows = validate(allocation, language)
        selected = [row for row in rows if row['name'] == name]
        _require(len(selected) == 1, 'allocation receipt does not request %s' % name)
        row = selected[0]
        _require(row['start'] % 4 == 0 and row['bytes'] % 4 == 0 and reserve.BASE <= row['start']
                 and row['start'] + row['bytes'] <= reserve.END, 'assignment outside the reserve range or unaligned')
        return dict(row)
    _require(type(allocation) is dict and set(allocation) == ALLOCATION_FIELDS,
             'the base must come from a reserve.allocate receipt (exact fields %s)' % sorted(ALLOCATION_FIELDS))
    policy, digest = _reserve_policy()
    _require(allocation['schema'] == 1 and allocation['policy_sha256'] == digest
             and allocation['policy_version'] == policy['version'],
             'allocation receipt was not issued under the reserve policy in force')
    _require(allocation['address_reserved'] is True and allocation['installed'] is False
             and allocation['installation_authorized'] is False, 'allocation receipt flags')
    _require(allocation['language'] == language and baseline.INPUT_HASHES.get(allocation['input_sha256']) == language,
             'allocation receipt belongs to another ROM or language')
    _require(_is_sha256(allocation['audit_sha256']), 'allocation audit hash')
    requested = allocation['requested']
    _require(type(requested) is dict and name in requested, 'allocation receipt does not request %s' % name)
    conditional = policy.get('conditional_parents', reserve.CONDITIONAL_REQUIREMENTS)
    slots = {part['name']: (entry['parent'], part) for entry in policy['subdivisions']
             for part in entry['parts'] if part['kind'] == 'payload'}
    expected = []
    for slot_name, size in requested.items():
        _require(type(slot_name) is str and slot_name in slots, 'the reserve policy has no payload slot %s' % slot_name)
        _require(type(size) is int and 0 < size, 'requested size')
        parent, slot = slots[slot_name]
        _require(parent not in conditional, 'slot %s belongs to a conditional owner (%s): the reserve refuses it' % (slot_name, parent))
        _require(size <= slot['bytes'], 'requested size exceeds the slot capacity')
        expected.append({'name': slot_name, 'parent': parent, 'start': slot['start'], 'bytes': size, 'capacity': slot['bytes']})
    expected.sort(key=lambda row: row['start'])
    _require(allocation['assignments'] == expected, 'allocation assignments differ from what the reserve policy grants')
    row = next(item for item in expected if item['name'] == name)
    _require(row['start'] % 4 == 0 and row['bytes'] % 4 == 0 and reserve.BASE <= row['start']
             and row['start'] + row['bytes'] <= reserve.END, 'assignment outside the reserve range or unaligned')
    return dict(row)


def _check_slot(slot):
    _require(type(slot) is dict and set(slot) == {'name', 'parent', 'start', 'bytes', 'capacity', 'preimage_sha256'},
             'slot record')
    _require(_is_sha256(slot['preimage_sha256']), 'slot preimage hash')


def inert_view(data, receipt):
    """The same image with this stage's activation word cleared (a pure function: `data` is not modified).

    The builder's mandatory final gate is `sha256(inert_view(final_rom, receipt)) == candidate_sha256` (see
    `candidate_gate`): it proves the ROM about to be activated is the inert candidate the proof was captured on."""
    slot = receipt['slot']
    _require(type(slot) is dict and type(slot.get('start')) is int, 'receipt slot')
    at = rom_offset(data, slot['start'] + STATE_ENABLED, 4)
    view = bytearray(data)
    view[at:at + 4] = bytes(4)
    return bytes(view)


def candidate_gate(final_rom, receipt):
    """Final gate before activation: the final ROM with the activation word cleared must be the declared candidate."""
    candidate = receipt.get('candidate_sha256')
    _require(candidate is not None, 'the receipt declares no candidate: nothing to gate')
    _require(_sha(inert_view(final_rom, receipt)) == candidate,
             'the final ROM with the activation word cleared is not the candidate the proof was captured on')


def slot_preimage_from_v4(v4, language, allocation):
    """The expected preimage of the assigned slot, taken from the exact V4 image (never from the stage input).

    This helper is for direct V4 fixtures.  The production UI intentionally retires the former Guide bytes and clears
    this slot; a post-UI caller must pin the all-zero postimage explicitly as `preimage_sha256`.  Any other predecessor
    that writes the slot likewise needs its exact post-stage hash rather than a hash derived from the stage input."""
    _require(type(v4) is bytes and baseline.INPUT_HASHES.get(_sha(v4)) == language, 'the V4 image must be the exact V4 of this language')
    assignment = check_allocation(allocation, language)
    return _sha(read(v4, assignment['start'], assignment['bytes']))


def _bind_candidate(candidate_sha256, active, inert_sha256):
    """candidate_relation: whether the declared candidate IS this stage's inert output or a composed ROM."""
    if candidate_sha256 is None:
        return None
    return 'stage-inert-output' if candidate_sha256 == inert_sha256 else 'composed-candidate'


def prepare(data, language, charmap, work, *, allocation=None, preimage_sha256=None, geometry=None, active=False,
            evidence=None, candidate_sha256=None, variant='compact'):
    """Compile the legend for the reserve-assigned slot and install it into a copy of `data`.

    `allocation` is a `reserve.allocate` receipt naming `summary-controls.runtime`: this function never
    chooses an address, and the slot's current bytes must hash to `preimage_sha256`. Without `active`
    (default) the payload is installed inert (flag 0) with the unproven proposal geometry; activation
    needs a geometry, runtime inventory evidence and `candidate_sha256`, the inert candidate ROM the
    evidence was captured on (`evidence['capture_rom_sha256']` must equal it). `data` may be any image
    whose pinned intervals are intact (`audit`). Returns (new ROM bytes, receipt); `verify` has passed.
    """
    _require(allocation is not None, 'a reserve allocation receipt is required: the installer never chooses a base')
    _require(_is_sha256(preimage_sha256), 'the assignment must state the sha256 of the bytes it replaces')
    if active:
        _require(geometry is not None and evidence is not None,
                 'activation needs geometry and runtime evidence (window/tile inventory)')
        _require(_is_sha256(candidate_sha256), 'activation needs candidate_sha256: the inert candidate ROM that was captured')
    _require(candidate_sha256 is None or _is_sha256(candidate_sha256), 'candidate_sha256 must be a lowercase sha256')
    _require(type(data) is bytes, 'immutable bytes required')
    assignment = check_allocation(allocation, language)
    base = dict(assignment, preimage_sha256=preimage_sha256)
    abi = load_abi()
    audit(data, language, abi)  # every pinned interval, before anything else
    segments = _arm9_segments(data)
    slot_at = rom_offset(data, base['start'], base['bytes'], segments)
    _require(_sha(data[slot_at:slot_at + base['bytes']]) == base['preimage_sha256'], 'assigned slot preimage mismatch')
    source = 'assigned' if geometry is not None else 'proposal'
    geometry = dict(PROPOSAL if geometry is None else geometry)
    placement = check_geometry(geometry, inventory(data), evidence, active=active, candidate_sha256=candidate_sha256,
                               language=language)
    charmap_sha256 = check_charmap(charmap)
    codes = encode_legend(language, charmap, variant)
    advance = measure_advance(font_widths(data), codes)
    window = 8 * geometry['width']
    _require(advance <= window, 'legend text (%d px) does not fit the %d px window: it would be truncated' % (advance, window))
    image, info = compile_payload(work, base['start'], language, charmap, geometry, enabled=int(active), abi=abi, variant=variant)
    _require(len(image) <= base['bytes'], 'payload (%d bytes) exceeds the assigned slot (%d bytes)' % (len(image), base['bytes']))
    out = bytearray(data)
    out[slot_at:slot_at + len(image)] = image
    sites = []
    for site, name, native in SITES:
        at = rom_offset(data, hex_int(site), 4, segments)
        _require(decode_bl(hex_int(site), bytes(data[at:at + 4])) & ~1 == native, 'call site %s no longer reaches %#x' % (site, native))
        out[at:at + 4] = encode_bl(hex_int(site), info['symbols'][name])
        sites.append(site)
    out = bytes(out)
    pins_after = measure(out)
    receipt = {'schema': 2, 'language': language, 'input_sha256': _sha(data), 'output_sha256': _sha(out),
               'allocation': copy.deepcopy(allocation), 'slot': base, 'payload': info, 'sites': sites,
               'enabled': int(active), 'function_state': 'active' if active else 'inert',
               'candidate_sha256': candidate_sha256,
               'capture_rom_sha256': evidence['capture_rom_sha256'] if evidence else None,
               'candidate_relation': _bind_candidate(candidate_sha256, active, _sha(inert_view(out, {'slot': base}))),
               'geometry': geometry, 'geometry_source': source, 'placement': placement, 'variant': variant,
               'text_advance_px': advance, 'window_px': window, 'charmap_sha256': charmap_sha256,
               'evidence': evidence, 'evidence_sha256': _sha(json.dumps(evidence, sort_keys=True).encode()) if evidence else None,
               'pins_after': {'spans': {n: pins_after['spans'][n] for n in pins_after['spans'] if n.startswith('viewer.')},
                              'hooks': pins_after['hooks']}}
    receipt['verification'] = verify(data, out, receipt, charmap=charmap)
    return out, receipt


def _payload_words(image):
    return struct.unpack('<%dI' % (len(image) // 4), image)


def verify(before, after, receipt, charmap=None):
    """Independent readback of a `prepare` result; raise ValueError on any deviation.

    The payload is recompiled for the receipt's base, geometry and activation flag from the String read back from the
    installed bytes and compared with them (as `portable.verify` does). With `charmap` (the pinned pret file) the
    installed String is also compared with the legend text of `receipt['variant']`, and the receipt's charmap hash is
    checked; without it the text itself is not verified."""
    abi = load_abi()
    language = receipt['language']
    _require(type(receipt.get('sites')) is list and [s for s, _n, _t in SITES] == receipt['sites'], 'receipt sites')
    audit(before, language, abi)
    _require(len(before) == len(after), 'ROM length changed')
    _require(before[:0x200] == after[:0x200], 'NDS header changed')
    _require(_sha(before) == receipt['input_sha256'] and _sha(after) == receipt['output_sha256'], 'receipt hashes')
    base = receipt['slot']
    _check_slot(base)
    assignment = check_allocation(receipt.get('allocation'), language)   # the base still comes from the reserve policy in force
    _require({k: base[k] for k in assignment} == assignment, 'slot differs from the reserve assignment')
    segments = _arm9_segments(before)
    _require(_arm9_segments(after) == segments, 'ARM9 layout changed')
    slot_at = rom_offset(before, base['start'], base['bytes'], segments)
    _require(_sha(before[slot_at:slot_at + base['bytes']]) == base['preimage_sha256'], 'slot preimage')
    payload = receipt['payload']
    size = payload['bytes']
    _require(0 < size <= base['bytes'] and size % 4 == 0, 'payload size')
    image = bytes(after[slot_at:slot_at + size])
    _require(_sha(image) == payload['image_sha256'], 'installed payload identity')
    _require(after[slot_at + size:slot_at + base['bytes']] == before[slot_at + size:slot_at + base['bytes']], 'slot tail changed')
    flag = struct.unpack_from('<I', image, STATE_ENABLED)[0]
    _require(flag in (0, 1), 'activation flag must be 0 or 1')
    state = 'active' if flag else 'inert'   # recomputed from the installed bytes, never from the receipt
    _require(flag == receipt['enabled'] == payload['enabled'] and state == receipt.get('function_state'), 'activation flag')
    candidate = receipt.get('candidate_sha256')
    _require(candidate is None or _is_sha256(candidate), 'candidate_sha256')
    evidence = receipt.get('evidence')
    _require(state == 'inert' or (evidence is not None and candidate is not None),
             'an active legend needs its runtime evidence and its candidate ROM')
    if evidence is not None:
        check_evidence(evidence, receipt['geometry'], candidate, language)
        _require(receipt.get('capture_rom_sha256') == evidence['capture_rom_sha256'] == candidate,
                 'receipt capture_rom_sha256 differs from candidate_sha256')
    else:
        _require(receipt.get('capture_rom_sha256') is None, 'capture_rom_sha256 without evidence')
    _require(receipt.get('candidate_relation') == _bind_candidate(candidate, flag, _sha(inert_view(after, receipt))),
             'candidate relation differs from the installed bytes')
    _require(receipt.get('evidence_sha256') == (_sha(json.dumps(evidence, sort_keys=True).encode()) if evidence else None),
             'evidence hash differs from the receipt evidence')
    # Recompile from the installed String with the receipt's geometry, variant and flag: a geometry or flag that the
    # receipt claims but the bytes do not carry cannot pass.
    words = _payload_words(image)
    _require(STRING_MAGIC in words[STATE_BYTES // 4:], 'installed payload carries no legend String')
    string_at = 4 * words.index(STRING_MAGIC, STATE_BYTES // 4)
    maxsize, count = struct.unpack_from('<HH', image, string_at - 4)
    codes = struct.unpack_from('<%dH' % count, image, string_at + 4)
    _require(maxsize == count and count == len(LEGEND[receipt['variant']]) + 1 == payload['string_codes'],
             'legend variant differs from the installed String length')
    with tempfile.TemporaryDirectory(prefix='controls-verify-') as scratch:
        fresh, _info = compile_payload(Path(scratch), base['start'], language, None, receipt['geometry'], enabled=flag, abi=abi,
                                       variant=receipt['variant'], codes=codes)
    _require(fresh == image, 'recompiled payload differs from the installed bytes (geometry, flag or code)')
    if charmap is not None:
        _require(receipt.get('charmap_sha256') == check_charmap(charmap), 'receipt charmap hash differs')
        _require(list(codes) == encode_legend(language, charmap, receipt['variant']),
                 'installed legend text differs from the charmap encoding of the variant')
    _require(image[:STATE_ENABLED] == bytes(STATE_ENABLED) and image[STATE_ENABLED + 4:STATE_BYTES] == bytes(STATE_BYTES - STATE_ENABLED - 4),
             'resident record must start zeroed')
    allowed = set(range(slot_at, slot_at + size))
    reached = {}
    for site, name, native in SITES:
        at = rom_offset(before, hex_int(site), 4, segments)
        _require(decode_bl(hex_int(site), bytes(before[at:at + 4])) & ~1 == native, 'site preimage %s' % site)
        reached[site] = decode_bl(hex_int(site), bytes(after[at:at + 4]))
        allowed.update(range(at, at + 4))
    # Entry points come from the installed bytes, not from the receipt: each call site must land on a
    # wrapper (push {r4, lr}; movs r4, r0; bl <entry>) inside the image, and the entries it calls are the
    # update/destroy functions the receipt names.
    derived = {}
    for site, name, native in SITES:
        wrapper = reached[site]
        _require(wrapper & 1 and base['start'] + STATE_BYTES <= wrapper < base['start'] + size, 'site %s leaves the image' % site)
        at_wrapper = wrapper - 1 - base['start']
        _require(image[at_wrapper:at_wrapper + 4] == WRAPPER_PROLOGUE, 'site %s does not reach a legend wrapper' % site)
        callee = decode_bl(wrapper - 1 + 4, image[at_wrapper + 4:at_wrapper + 8])
        _require(base['start'] + STATE_BYTES <= callee < base['start'] + size and callee & 1, 'wrapper callee outside the image')
        kind = 'update' if name == 'sgp_sc_redraw' else 'destroy'
        _require(derived.setdefault(name, wrapper) == wrapper and derived.setdefault(kind, callee) == callee,
                 'call sites disagree about the wrapper of %s' % name)
    _require({'sgp_sc_redraw': derived['sgp_sc_redraw'], 'sgp_sc_teardown': derived['sgp_sc_teardown'],
              'sgp_summary_controls_update': derived['update'], 'sgp_summary_controls_destroy': derived['destroy']}
             == {k: payload['symbols'][k] for k in ENTRIES}, 'receipt symbols differ from the installed bytes')
    outside = 0
    start, rom, count = segments[0]
    for lo_, hi_ in ((rom, rom + count),) + tuple((r, r + c) for _s, r, c in segments[1:]):
        if before[lo_:hi_] == after[lo_:hi_]:
            continue
        outside += sum(1 for i in range(lo_, hi_) if before[i] != after[i] and i not in allowed)
    _require(outside == 0, 'ARM9 changed outside the slot and the three call sites: %d byte(s)' % outside)
    tail_start = min(rom for _s, rom, _c in segments)
    _require(before[:tail_start] == after[:tail_start], 'bytes before the ARM9 changed')
    end_arm9 = max(rom + c for _s, rom, c in segments)
    _require(before[end_arm9:] == after[end_arm9:], 'bytes after the ARM9 changed (overlays, FAT, ARM7, banner)')
    # The viewer is byte-identical and every hook still points where the pin file says.
    pins = measure(after)
    for name in ('viewer.payload', 'viewer.reader', 'viewer.reset_header', 'viewer.entries'):
        _require(pins['spans'][name] == abi['spans'][name], 'viewer changed: ' + name)
    _require(pins['hooks'] == abi['hooks'], 'viewer hooks changed')
    _require(pins['literals'] == abi['literals'], 'viewer literals changed')
    _require(pins['natives'] == abi['natives'] and pins['tables'] == abi['tables'], 'natives or tables changed')
    # Payload contents: only pinned native entries, nothing that reads the keys.
    words = _payload_words(image)
    natives = {hex_int(item['address']) | 1 for item in abi['natives'].values()} | {0x0208D179, 0x0208C4E1}
    absolute = {w for w in words if 0x01FF8000 <= w < 0x02400000 and w & 1
                and not base['start'] <= w < base['start'] + size}
    _require(absolute <= natives, 'payload references an unpinned native address: %s' % sorted(hex(x) for x in absolute - natives))
    _require(not [w for w in words if 0x021D1100 <= w < 0x021D1180], 'payload references gSystem')
    return {'enabled': receipt['enabled'], 'function_state': state, 'candidate_sha256': candidate,
            'candidate_relation': receipt['candidate_relation'], 'payload_bytes': size, 'payload_sha256': payload['image_sha256'],
            'slot': [base['start'], base['start'] + base['bytes']], 'sites': list(receipt['sites']),
            'arm9_changed_outside_assignment': outside, 'viewer_unchanged': True,
            'natives_referenced': sorted(hex(x) for x in absolute)}
