"""Emit latest-only localized project cheats after exact cartridge/static admission.

No historical third-party database is migrated. The original seven project
code streams are immutable; the money code is excluded without runtime proof.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import re
import textwrap
import unicodedata
import xml.etree.ElementTree as ET
import zlib

from ndspy.rom import NintendoDSRom
from sgp12.blz import ndspy_load_arm9_sicuro, ndspy_load_overlays_sicuri
from cheats.audit import analyze_cheat
from .catalogue import LOCALES, _pairs

VERSION = '1.3.2'
CODES = {
    'fast_text': '92002346 00000E41 12002346 00002100 D2000000 00000000 920202EE 00004819 120202EE 00001C0C 120202F0 00004818 1202031E 0000BD10 02020320 E7E53C2D 1202032E 0000D0DF 1202033A 0000E7F1 D2000000 00000000',
    'transitions': '9200FA78 00009A0C 1200FA78 00002200 1200FA9C 00002200 D2000000 00000000',
    'healing': '9206325E 0000F7FC 1206325E 0000E000 1206327A 0000E000 D2000000 00000000 9224BDCC 00002000 1224BDCC 00002001 D2000000 00000000',
    'outlines': '521FBC38 20204001 221FBC3A 00000010 D2000000 00000000',
    'rename': '9204D240 00002001 1204D240 00002000 D2000000 00000000',
    'money': '94000130 FFFB0000 6211186C 00000000 B211186C 00000000 0000D068 000F423F D2000000 00000000',
    'camera': '523DEBE0 002EB570 223DFFFC 00000000 D2000000 00000000',
}
# Complete affected instruction windows, measured on the supplied 1.3.2 EN
# candidate acfda601...ee5e. These strengthen the unchanged AR equality guards.
# Language variants must match these same English-engine contexts or omit a code.
CONTEXTS = {
    'fast_text': [
        ('ARM9:0', 0x02002346, 2, 'f4091d57f874f3f84389dbb9de171477bc50f5f0eb2bb0ad14194503e9ad5e62'),
        ('ARM9:0', 0x020202EE, 78, 'a1ffa365dc1fe62a27964bce087c029d87478a4217d1de3fb1d2e19f7a50fbd8')],
    'transitions': [('ARM9:0', 0x0200FA78, 38, 'bbcce86a13dcd50b3aca6aec97ea39a775cb9c5888e0d7c24c8f07399a9b0e69')],
    'healing': [
        ('ARM9:0', 0x0206325E, 30, '0f2ea58a25f4d668893430ee23e22208fb49c375af29857570ee946bb21ae938'),
        ('overlay:2', 0x0224BDCC, 2, '474f2af47544e9c7ce4338cabd43c5ca1c26432b7300ce387406157ea433891f')],
    'outlines': [('overlay:1', 0x021FBC38, 4, '3c4f3808685244b16539a5d5a22e0ce8ed3a29b8c8ed6502ce90e6eddba1f6be')],
    'rename': [('ARM9:0', 0x0204D240, 2, '3145e7a95720a1db303f2198e796ea848f52b6079b5bf4f47d32fad69c2bce77')],
    'camera': [
        ('ARM9:3', 0x023DEBE0, 4, 'aa8f3ec482df3ebc5782a8ed2e6b873694ad7243b5f5f37c87c5c8a4c4133caf'),
        ('ARM9:3', 0x023DFFFC, 1, '4bf5122f344554c53bde2ebb8cd2b7e3d1600ad631c385a5d7cce23c7785459a')],
}
BASE_KEYS = ('title folder readme_title intro validation controls persistence native_features '
             'xml_install mch_install mch_note included omitted runtime preimage preimages credits identity').split()
REQUIRED = set(BASE_KEYS) | {key + suffix for key in CODES for suffix in ('.name', '.note')}


def load_words(locale):
    if locale not in LOCALES:
        raise ValueError('unsupported cheat locale')
    path = Path(__file__).parent / 'locales' / locale / 'cheats.json'
    data = json.loads(path.read_text(), object_pairs_hook=_pairs)
    if (set(data) != {'schema', 'language', 'strings'} or data['schema'] != 1
            or data['language'] != locale or set(data['strings']) != REQUIRED
            or any(not isinstance(v, str) or not v.strip() for v in data['strings'].values())):
        raise ValueError('incomplete localized project cheat text')
    return {k: unicodedata.normalize('NFC', v) for k, v in data['strings'].items()}


def game_id(rom):
    if len(rom) < 512 or not re.fullmatch(rb'[A-Z0-9]{4}', rom[12:16]):
        raise ValueError('invalid cheat game header')
    return rom[12:16].decode('ascii') + ' ' + f'{(zlib.crc32(rom[:512]) ^ 0xffffffff):08X}'


def check_context(specification, sections):
    for region, address, size, expected in specification:
        matches = [data[address-base:address-base+size] for name, base, data in sections
                   if name == region and base <= address and address+size <= base+len(data)]
        if len(matches) != 1 or hashlib.sha256(matches[0]).hexdigest() != expected:
            return False
    return True


def select_codes(sections):
    """Omit unsafe/unproven entries; never rewrite guards to make a code match."""
    accepted, omitted = [], {'money': 'runtime'}
    for key, windows in CONTEXTS.items():
        if not check_context(windows, sections):
            omitted[key] = 'preimage'
            continue
        report = analyze_cheat(dict(folders=['project'], name=key, codes=CODES[key]), sections)
        valid = not report['issues'] and bool(report['equality_guards'])
        for guard in report['equality_guards']:
            address = int(guard['address'], 16)
            regions = {region for region, start, size, _ in windows
                       if start <= address and address+guard['bytes'] <= start+size}
            valid &= (guard['status'] == 'matching_source' and len(regions) == 1
                      and set(guard['matching_regions']) == regions)
        for write in report['writes']:
            if write['address'] is None:
                valid = False
                continue
            address = int(write['address'], 16)
            valid &= any(start <= address and address+write['bytes'] <= start+size
                         for _, start, size, _ in windows)
        if valid:
            accepted.append(key)
        else:
            omitted[key] = 'preimage'
    return accepted, omitted


def emit(locale, identity, accepted, omitted, output):
    """Serialize an admitted proof into three initially-disabled player files."""
    words = load_words(locale)
    if ('money' in accepted or not accepted or len(set(accepted)) != len(accepted)
            or not set(accepted) <= set(CONTEXTS) or set(accepted) & set(omitted)):
        raise ValueError('invalid admitted project cheat set')
    output = Path(output)
    if output.exists() or output.is_symlink():
        raise FileExistsError(output)
    fmt = lambda text: text.format(**identity, count=len(accepted))
    title, folder = fmt(words['title']), fmt(words['folder'])
    root = ET.Element('codelist')
    root.append(ET.Comment(fmt(words['identity'])))
    ET.SubElement(root, 'name').text = title
    game = ET.SubElement(root, 'game')
    ET.SubElement(game, 'name').text = title
    ET.SubElement(game, 'gameid').text = identity['gameid']
    category = ET.SubElement(game, 'folder')
    ET.SubElement(category, 'name').text = folder
    mch = ['# ' + title, '# SHA-256: ' + identity['sha256'], '# ' + identity['gameid'],
           *['# ' + line for line in textwrap.wrap(fmt(words['validation']), 90)],
           '', 'CAT ' + folder, '']
    readme = [fmt(words['readme_title']), '', fmt(words['identity']), '', words['intro'],
              words['validation'], words['controls'], words['persistence'], words['native_features'],
              '', words['xml_install'], words['mch_install'], '', words['included']]
    for key in accepted:
        name, note = words[key + '.name'], words[key + '.note']
        cheat = ET.SubElement(category, 'cheat')
        ET.SubElement(cheat, 'name').text = name
        ET.SubElement(cheat, 'note').text = note + ' ' + words['validation']
        ET.SubElement(cheat, 'codes').text = CODES[key]
        tokens = CODES[key].split()
        # ARCodeFile::Load has a 255-byte DESC field and 1024-byte line buffer.
        # Keep complete localized notes as bounded comments and in README.
        if len(name.encode('utf-8')) > 127 or len(words['mch_note'].encode('utf-8')) > 255:
            raise ValueError('localized MCH field exceeds native parser limit')
        mch += ['CODE 0 ' + name, 'DESC ' + words['mch_note']]
        mch += ['# ' + line for line in textwrap.wrap(note, 90)]
        mch += [' '.join(tokens[i:i+2]) for i in range(0, len(tokens), 2)] + ['']
        readme += ['', name, note]
    readme += ['', words['omitted']]
    for key, reason in sorted(omitted.items()):
        readme += [words[key + '.name'] + ': ' + words[reason]]
    readme += ['', words['preimages']]
    for key in accepted:
        readme += [words[key + '.name']]
        readme += [f'{region} 0x{address:08X} +{size} SHA-256 {digest}'
                   for region, address, size, digest in CONTEXTS[key]]
    readme += ['', words['credits'], '']
    ET.indent(root, space='  ')
    base = 'Sacred-Gold-Plus-' + identity['version'] + '-' + locale
    if len(folder.encode('utf-8')) > 127 or any(len(line.encode('utf-8')) > 1022 for line in mch):
        raise ValueError('localized MCH line exceeds native parser limit')
    payloads = {base + '.xml': '<?xml version="1.0" encoding="utf-8"?>\n' + ET.tostring(root, encoding='unicode') + '\n',
                base + '.mch': '\n'.join(mch), 'README.txt': '\n'.join(readme)}
    output.mkdir(parents=True, exist_ok=False)
    paths = []
    for name, text in payloads.items():
        path = output / name
        with path.open('x', encoding='utf-8', newline='\n') as stream:
            stream.write(text)
        paths.append(path)
    return paths


def generate(locale: str, rom: bytes, output: Path, *, contract: dict) -> list[Path]:
    """Admit an exact current target, verify every preimage, and emit no legacy DB."""
    target = contract.get('targets', {}).get(locale, {})
    if (locale not in LOCALES or contract.get('version') != VERSION or type(rom) is not bytes
            or len(rom) != target.get('bytes') or hashlib.sha256(rom).hexdigest() != target.get('sha256')):
        raise ValueError('current cheat target identity mismatch')
    native = NintendoDSRom(rom)
    main = ndspy_load_arm9_sicuro(native)
    sections = [('ARM9:' + str(i), s.ramAddress, bytes(s.data)) for i, s in enumerate(main.sections)]
    sections += [('overlay:' + str(i), s.ramAddress, bytes(s.data))
                 for i, s in ndspy_load_overlays_sicuri(native).items()]
    accepted, omitted = select_codes(sections)
    identity = dict(version=VERSION, locale=locale, gameid=game_id(rom), sha256=target['sha256'])
    return emit(locale, identity, accepted, omitted, output)
