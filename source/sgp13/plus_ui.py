"""Native Plus-page presentation update, preserving the existing input/save logic."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import struct
import subprocess

import ndspy.narc
import ndspy.rom
from sgp12.rom import Arm9, Rom, bl_decode, bl_thumb
from sgp12.blz import blz_comprimi_ottimo
from .resources import append_file

ROOT = Path(__file__).resolve().parents[1]
FEATURE = ROOT / 'features/plus-ui'
BASE, CODE_BYTES, LABELS, SIZE = 0x023D7700, 384, 0x023D7880, 1024
NAV_BASE, NAV_SIZE = 0x023D7500, 512
OLD_CODE_SHA = '7fe2f381043e993168c6359accd5fa154498e5e35e9c368035bb700b23daf7c4'
OLD_TEMPLATES = bytes.fromhex('099e3d02139e3d021d9e3d02ffffffff2d9e3d02379e3d02419e3d02ffffffff')
FONT_PALETTE = bytes.fromhex('13376b29f55e9d08bf5e450fb347c07def765f5e7f730000000000000000ff7f')
VERSION = '1.3'
# Verified native printer ownership ABI, identical in EN and IT. Includes the
# task-table literal, bounds-sensitive active check and destructor wrappers.
PRINTER_ARM9_GUARDS = (
    (0x02020020, 136, 'cd10ae805fabf73580e2584b749afdf46d2224d1d8b1d6664cc288d5738b9d29'),
    (0x0201F988, 4, '68d3b0c15dab971249281e462c8832009358b360143b445577a9d310e9d3ab41'),
    (0x0200BCDC, 42, '2509d4930b96e6670b82d3fb5727a463798df88b48a3b3c6c62f628c8bf900b7'),
)
PREVIEW_ADDRESS, PREVIEW_SIZE = 0x021E61A8, 144
PREVIEW_SHA = 'cb0558b11c904f46772cc27ffd74d07035067ba0414d3452ae2699ecd817bcce'


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def compile_native(work_dir):
    out = Path(work_dir)
    out.mkdir(parents=True, exist_ok=True)
    env = {**os.environ, 'SGP_UI_SORGENTI': str(FEATURE)}
    subprocess.run([os.sys.executable, str(ROOT / 'features/options/tools/compila.py'),
                    '--uscita', str(out)], env=env, capture_output=True, check=True)
    manifest = json.loads((out / 'manifesto.json').read_text())
    code = (out / 'ui_blob.bin').read_bytes()
    obj = out / 'context.o'
    subprocess.run(['clang', '--target=armv5te-none-eabi', '-mcpu=arm946e-s', '-mthumb', '-Oz',
                    '-ffreestanding', '-fno-builtin', '-fno-stack-protector', '-fno-jump-tables',
                    '-fno-unwind-tables', '-fno-asynchronous-unwind-tables', '-Wall', '-Wextra',
                    '-Werror', '-c', str(FEATURE / 'context.c'), '-o', str(obj)],
                   check=True, capture_output=True)
    loader = module(ROOT / 'features/options/tools/carica_text.py', 'plus_context_loader')
    helper, symbols = loader.load_text(obj.read_bytes(), BASE, ('plus_context',))
    if len(code) > 0xec0 or len(helper) > CODE_BYTES or symbols['plus_context'] != BASE | 1:
        raise ValueError('Plus presentation allocation exceeded')
    return code, {k: int(v, 16) for k, v in manifest['simboli'].items()}, helper


def compile_navigation(work_dir, controller_symbols):
    out = Path(work_dir)
    out.mkdir(parents=True, exist_ok=True)
    obj = out / 'navigation.o'
    subprocess.run(['clang', '--target=armv5te-none-eabi', '-mcpu=arm946e-s', '-mthumb', '-Oz',
                    '-ffreestanding', '-fno-builtin', '-fno-stack-protector', '-fno-jump-tables',
                    '-fno-unwind-tables', '-fno-asynchronous-unwind-tables', '-Wall', '-Wextra',
                    '-Werror', '-DSGP_UI_STATO_ADDR=0x023D9F60u',
                    f"-DSGP_OPZ_APRI={controller_symbols['opz_apri']:#x}u",
                    f"-DSGP_FRAME={controller_symbols['sgp_ui_frame']:#x}u",
                    '-c', str(FEATURE / 'navigation.c'), '-o', str(obj)],
                   check=True, capture_output=True)
    loader = module(ROOT / 'features/options/tools/carica_text.py', 'plus_navigation_loader')
    code, symbols = loader.load_text(obj.read_bytes(), NAV_BASE,
                                    ('plus_button', 'plus_navigation', 'plus_navigation_hook'))
    if len(code) > NAV_SIZE or symbols['plus_button'] != NAV_BASE | 1:
        raise ValueError('Plus navigation allocation exceeded')
    return code, symbols


EXT_BASE, EXT_SIZE, EXT_TEXT, EXT_TEXT_SIZE = 0x023CB800, 8192, 0x023CD800, 4096


def compile_extended(work_dir):
    out = Path(work_dir); out.mkdir(parents=True, exist_ok=True)
    obj = out / 'extended.o'
    subprocess.run(['clang', '--target=armv5te-none-eabi', '-mcpu=arm946e-s', '-mthumb', '-Oz',
                    '-ffreestanding', '-fno-builtin', '-fno-stack-protector', '-fno-jump-tables',
                    '-fno-unwind-tables', '-fno-asynchronous-unwind-tables', '-Wall', '-Wextra',
                    '-Werror', '-DSGP_UI_STATO_ADDR=0x023D9F60u',
                    '-c', str(FEATURE / 'extended.c'), '-o', str(obj)],
                   check=True, capture_output=True)
    loader = module(ROOT / 'features/options/tools/carica_text.py', 'plus_extended_loader')
    code, symbols = loader.load_text(obj.read_bytes(), EXT_BASE, ('extended_frame', 'extended_open'))
    if len(code) > EXT_SIZE:
        raise ValueError('Plus extended controller allocation exceeded')
    return code, symbols


def labels(rom_path, language, charmap):
    if language not in ('EN', 'IT'):
        raise ValueError('language')
    codec = module(ROOT / 'features/options/tools/codifica_testo.py', 'plus_context_encoder')
    widths = module(ROOT / 'quality-audit/misura_larghezza.py', 'plus_context_widths')
    table, _ = codec.carica_charmap(charmap)
    metric = widths.load_width_table_from_rom(rom_path)
    rows = json.loads((FEATURE / 'context-text.json').read_text())[language]
    if len(rows) != 5 or any(len(row) != 2 for row in rows):
        raise ValueError('five pairs of context lines required')
    data = bytearray(20)
    for index, text in enumerate(line for row in rows for line in row):
        words = codec.codifica(text.replace("'", '’'), table)
        measured = widths.measure(metric, words, limit_px=216)
        if len(words) > 64 or len(measured['lines']) != 1 or any(
                l['unknown_codes'] or l['width_px'] > 216 for l in measured['lines']):
            raise ValueError('Plus context line exceeds native frame')
        struct.pack_into('<H', data, index * 2, len(data))
        data += struct.pack('<%dH' % len(words), *words)
    if len(data) > SIZE - CODE_BYTES:
        raise ValueError('Plus context labels exceed allocation')
    return bytes(data), lambda text: codec.codifica(text, table)


def shiny_labels(rom_path, language, charmap):
    if language not in ('EN', 'IT'):
        raise ValueError('shiny text language')
    codec = module(ROOT / 'features/options/tools/codifica_testo.py', 'shiny_text_encoder')
    widths = module(ROOT / 'quality-audit/misura_larghezza.py', 'shiny_text_widths')
    messages = module(ROOT / 'translation/message_codec.py', 'shiny_names_reader')
    table, _ = codec.carica_charmap(charmap)
    metric = widths.load_width_table_from_rom(rom_path)
    catalog = json.loads((FEATURE / 'shiny-text.json').read_text())
    if list(catalog['EN']) != list(catalog['IT']):
        raise ValueError('shiny bilingual text IDs differ')
    texts = catalog[language]
    headers = {'PLUS', 'SHINY', 'HUNT_TITLE', 'TARGET_TITLE', 'RULES_TITLE'}
    rows = {'MODE', 'TARGET', 'SUCCESS', 'ODDS', 'HUNT', 'CHOOSE', 'METHOD', 'CHARGE', 'SEARCH', 'RULES'}
    values = {'CLASSIC', 'PRO', 'NONE', 'UNAVAILABLE', 'QUEUED', 'LAND', 'SURF', 'OLD_ROD', 'GOOD_ROD', 'SUPER_ROD'}
    data = bytearray(len(texts) * 2); measured = {}
    def width(words, limit):
        result = widths.measure(metric, words, limit_px=limit)
        if len(result['lines']) != 1 or any(line['unknown_codes'] or line['width_px'] > limit for line in result['lines']):
            raise ValueError('shiny text width exceeds native row')
        return result['lines'][0]['width_px']
    for index, (key, text) in enumerate(texts.items()):
        words = codec.codifica(text.replace("'", '’'), table)
        if len(words) > 64:
            raise ValueError('shiny text width/code-unit allocation')
        limit = 144 if key in headers else (114 if key in rows else (76 if key in values else (176 if key.startswith('RULE_') else 216)))
        try:
            measured[key] = width(words, limit) if text else 0
        except ValueError as exc:
            raise ValueError(f'{language} {key}: {exc}') from exc
        struct.pack_into('<H', data, 2 * index, len(data))
        data += struct.pack('<%dH' % len(words), *words)
    if len(data) > EXT_TEXT_SIZE:
        raise ValueError('shiny text bank allocation exceeded')
    rom = ndspy.rom.NintendoDSRom.fromFile(rom_path)
    bank = messages.Bank(ndspy.narc.NARC(rom.getFileByName('a/0/2/7')).files[237])
    name_limit = 166 - measured['TARGET'] - 8
    names = [width(bank.words[species], name_limit) for species in range(1, 494)]
    for left, right in (('MODE', 'UNAVAILABLE'), ('METHOD', 'SUPER_ROD'), ('HUNT', 'QUEUED')):
        if measured[left] + measured[right] + 8 > 166:
            raise ValueError('shiny row label/value width overlap')
    return bytes(data), {'bytes': len(data), 'string_count': len(texts),
                         'max_species_width': max(names), 'species_names_checked': 493,
                         'known_glyphs': True, 'widths': measured}


def version_title(before, encode, language):
    # Rebuild the small existing string table with identical IDs and non-title
    # strings except the clipped EN migration note; deduplicate shared text.
    # Save layouts are not involved.
    if language not in ('EN', 'IT'):
        raise ValueError('Plus migration note language')
    count = 29
    strings = []
    for index in range(count):
        offset = struct.unpack_from('<H', before, index * 2)[0]
        if offset < count * 2 or offset & 1 or offset >= len(before):
            raise ValueError('old Plus string offset')
        end = offset
        while end + 2 <= len(before) and before[end:end+2] != b'\xff\xff':
            end += 2
        if end + 2 > len(before):
            raise ValueError('old Plus string terminator')
        strings.append(before[offset:end+2])
    old_title = struct.pack('<%dH' % len(encode('Sacred Gold Plus 1.2.5')),
                            *encode('Sacred Gold Plus 1.2.5'))
    if strings[0] != old_title or strings[20] != old_title:
        raise ValueError('old Plus title preimage')
    note = {'EN': 'Press SELECT in OPTIONS to change them.',
            'IT': 'Si cambiano dalle OPZIONI con SELECT.'}[language]
    words = encode(note)
    if strings[25] != struct.pack('<%dH' % len(words), *words):
        raise ValueError('old Plus migration note preimage')
    if language == 'EN':
        words = encode('Change them in OPTIONS with SELECT.')
        strings[25] = struct.pack('<%dH' % len(words), *words)
    words = encode('Sacred Gold Plus V' + VERSION)
    strings[0] = strings[20] = struct.pack('<%dH' % len(words), *words)
    result = bytearray(count * 2)
    seen = {}
    for index, text in enumerate(strings):
        if text not in seen:
            seen[text] = len(result)
            result += text
        struct.pack_into('<H', result, index * 2, seen[text])
    if len(result) > len(before):
        raise ValueError('Plus title bank overflow')
    return bytes(result) + bytes(len(before) - len(result))


def install(input_path, output_path, language, charmap, work_dir):
    arm = Arm9(input_path)
    if hashlib.sha256(arm.leggi(0x023D9000, 0xec0)).hexdigest() != OLD_CODE_SHA:
        raise ValueError('old Plus controller preimage')
    if arm.leggi(0x023D9F40, 32) != OLD_TEMPLATES:
        raise ValueError('old Plus templates preimage')
    if arm.leggi(BASE, SIZE) != bytes(SIZE):
        raise ValueError('Plus context region occupied')
    if arm.leggi(NAV_BASE, NAV_SIZE) != bytes(NAV_SIZE):
        raise ValueError('Plus navigation region occupied')
    for address, size in ((EXT_BASE, EXT_SIZE), (EXT_TEXT, EXT_TEXT_SIZE), (0x023CE800, 256)):
        if arm.leggi(address, size) != bytes(size):
            raise ValueError('Plus extension region occupied')
    adjacent = arm.leggi(NAV_BASE - 16, 16)
    rom = ndspy.rom.NintendoDSRom(bytes(arm.raw))
    palette = ndspy.narc.NARC(rom.getFileByName('a/0/1/6')).files[7]
    if palette[40:72] != FONT_PALETTE:
        raise ValueError('native font palette preimage')
    v, _, overlay = Rom(arm.raw).immagine_overlay(54)
    for address, size, digest in PRINTER_ARM9_GUARDS:
        if hashlib.sha256(arm.leggi(address, size)).hexdigest() != digest:
            raise ValueError('native printer ABI preimage: ' + hex(address))
    preview_offset = PREVIEW_ADDRESS - v['ram']
    if hashlib.sha256(overlay[preview_offset:preview_offset+PREVIEW_SIZE]).hexdigest() != PREVIEW_SHA:
        raise ValueError('native Options preview ABI preimage')
    site, old = 0x021E6820, 0x023D9974
    offset = site - v['ram']
    if bl_decode(site, overlay[offset:offset+4]) != old:
        raise ValueError('old Plus menu hook preimage')
    code, symbols, helper = compile_native(work_dir)
    extension, ext_symbols = compile_extended(work_dir)
    nav_code, nav_symbols = compile_navigation(work_dir, {
        **symbols, 'opz_apri': ext_symbols['extended_open'],
        'sgp_ui_frame': ext_symbols['extended_frame']})
    navigation = nav_code + bytes(NAV_SIZE - len(nav_code))
    text, encode = labels(input_path, language, charmap)
    ext_text, ext_text_report = shiny_labels(input_path, language, charmap)
    ext_owned = extension + bytes(EXT_SIZE - len(extension))
    ext_labels = ext_text + bytes(EXT_TEXT_SIZE - len(ext_text))
    title = version_title(arm.leggi(0x023DA800, 1008), encode, language)
    owned = helper + bytes(CODE_BYTES - len(helper)) + text
    owned += bytes(SIZE - len(owned))
    new_code = code + bytes(0xec0 - len(code))
    templates = b''.join(struct.pack('<4I', symbols['sgp_' + mode + '_init'],
                                    symbols['sgp_' + mode + '_main'],
                                    symbols['sgp_' + mode + '_exit'], 0xffffffff)
                         for mode in ('cont', 'new'))
    arm.scrivi(BASE, owned)
    arm.scrivi(EXT_BASE, ext_owned)
    arm.scrivi(EXT_TEXT, ext_labels)
    arm.scrivi(NAV_BASE, navigation)
    arm.scrivi(0x023D9000, new_code)
    arm.scrivi(0x023D9F40, templates)
    arm.scrivi(0x023DA800, title)
    changed = bytearray(overlay)
    changed[offset:offset+4] = bl_thumb(site, nav_symbols['plus_navigation_hook'])
    compressed = blz_comprimi_ottimo(bytes(changed))
    if isinstance(compressed, tuple):
        compressed = compressed[0]
    raw = bytearray(append_file(bytes(arm.raw), v['file_id'], compressed))
    struct.pack_into('<I', raw, v['offset_voce'] + 28,
                     (v['parola_comp'] & 0xff000000) | len(compressed))
    Path(output_path).write_bytes(raw)
    check = Arm9(output_path)
    for address, expected in ((BASE, owned), (NAV_BASE, navigation), (0x023D9000, new_code),
                              (0x023D9F40, templates), (0x023DA800, title),
                              (EXT_BASE, ext_owned), (EXT_TEXT, ext_labels), (0x023CE800, bytes(256))):
        if check.leggi(address, len(expected)) != expected:
            raise ValueError('Plus presentation readback')
    if Rom(raw).immagine_overlay(54)[2] != bytes(changed):
        raise ValueError('Plus menu hook readback')
    if check.leggi(NAV_BASE - 16, 16) != adjacent:
        raise ValueError('Plus navigation lower neighbor changed')
    return {'code_bytes': len(code), 'helper_bytes': len(helper), 'label_bytes': len(text),
            'navigation_bytes': len(nav_code), 'navigation_symbols': nav_symbols,
            'extended_bytes': len(extension), 'extended_symbols': ext_symbols,
            'shiny_text': ext_text_report,
            'extended_sha256': hashlib.sha256(ext_owned).hexdigest(),
            'shiny_text_sha256': hashlib.sha256(ext_labels).hexdigest(),
            'version': VERSION, 'symbols': symbols, 'settings_layout_unchanged': True}
