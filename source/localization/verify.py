"""Read back localized cartridges, including preservation outside owned resources."""
import struct
import zlib
import tempfile
from pathlib import Path
from sgp12.blz import ndspy_decomprimi_sicuro
from ndspy.narc import NARC
from ndspy.rom import NintendoDSRom
from sgp131 import guide_content, ui, ui_compile, ui_copy, ui_resource_verify
from translation.message_codec import Bank, unpack_name
from .catalogue import load_strings, ui_catalogue
from .guide import build_categories
from .inventory import check_layout, sha
from .messages import _TEXT
from . import keyboard, native_text, summary_labels, geometry


def _require(condition, reason):
    if not condition: raise ValueError('localized readback: ' + reason)


def verify(core, output, donor, reference, locale, recipe, charmap):
    check_layout(output)
    old, new, native, retail = map(NintendoDSRom, (core, output, donor, reference))
    _require(len(old.files) == len(new.files) == 513, 'file count')
    fat = struct.unpack_from('<I', core, 0x48)[0]
    locate = ui._arm_map(core)
    # A recipe cannot bind new footer copy to an older compiled descriptor.
    with tempfile.TemporaryDirectory(prefix='sgp-locale-ui-readback-') as scratch:
        compiled_ui=ui_compile.compile_payloads(recipe['ui_config'],Path(scratch))['dynamic54']['data']
    native_ui=ndspy_decomprimi_sicuro(old.files[54],len(compiled_ui))
    _require(bytes(native_ui)==compiled_ui,'common UI differs from current pinned compiler/catalogue')
    allowed = [(0x14, 0x15), (0x80, 0x84), (0x15E, 0x160),
               (locate(0x023D7B60+80, 4), locate(0x023D7B60+80, 4)+4),
               (locate(0x023D7BC0, 128), locate(0x023D7BC0, 128)+128)]
    at = locate(native_text.PC_LABEL_ADDRESS,24); allowed.append((at,at+24))
    at = locate(native_text.ONBOARDING_ADDRESS,native_text.ONBOARDING_BYTES); allowed.append((at,at+native_text.ONBOARDING_BYTES))
    at = locate(native_text.SUMMARY_ADDRESS,native_text.SUMMARY_BYTES); allowed.append((at,at+native_text.SUMMARY_BYTES))
    for address,size in summary_labels.owned_spans(locale):
        at=locate(address,size);allowed.append((at,at+size))
    for address, _ in keyboard.EDITS:
        at = locate(address, 28); allowed.append((at, at+28))
    members = {}
    for row in recipe['graphics']:
        members.setdefault(row['file'], set()).add(row['member'])
    members.setdefault('a/0/0/8', set()).add(236)
    members.setdefault('a/0/6/8', set()).add(123)
    paths = set(members) | {'a/0/2/7', 'a/0/3/8'}
    extents = []
    for path in paths:
        index = old.filenames.idOf(path)
        at = fat + 8 * index
        allowed.append((at, at+8))
        start, end = struct.unpack_from('<II', output, at)
        _require(len(core) <= start < end <= len(output), 'replacement extent')
        _require(output[start:end] == new.getFileByName(path), 'FAT readback')
        extents.append((start, end))
    cursor = 0
    for start, end in sorted(allowed):
        _require(cursor <= start < end <= len(core), 'preservation span overlap')
        _require(core[cursor:start] == output[cursor:start], 'unowned bytes changed')
        cursor = end
    _require(core[cursor:] == output[cursor:len(core)], 'unowned suffix changed')
    cursor = len(core)
    for start, end in sorted(extents):
        _require(start == (cursor+511)//512*512, 'append alignment/order')
        _require(output[cursor:start] == b'\xff'*(start-cursor), 'append padding')
        cursor = end
    _require(cursor == len(output) == struct.unpack_from('<I', output, 0x80)[0], 'total ROM length')
    _require(struct.unpack_from('<I', output, locate(0x023D7B60+80, 4))[0] == len(output), 'module ROM limit')
    for path, selected in members.items():
        before, after = NARC(old.getFileByName(path)), NARC(new.getFileByName(path))
        _require(len(before.files) == len(after.files), 'graphics member count')
        for index, (a, b) in enumerate(zip(before.files, after.files)):
            if index not in selected: _require(a == b, 'unowned graphical member')
            elif index not in ({236} if path == 'a/0/0/8' else {123} if path == 'a/0/6/8' else set()):
                row = next(r for r in recipe['graphics'] if r['file'] == path and r['member'] == index)
                expected = row.get('transform',{}).get('after_sha256',row['donor_sha256'])
                _require(sha(b) == expected, 'localized graphical member hash')
            else:
                _require(sha(b) == recipe['authored_badges'][path+':'+str(index)], 'authored badge hash')
    for index in range(513):
        if index not in {old.filenames.idOf(path) for path in paths}:
            _require(old.files[index] == new.files[index], 'gameplay file changed')
    chars, commands = _TEXT.load_charmap(charmap)
    strings, aliases, counts = load_strings(locale), {}, dict(retail=0, authored=0, protected=0)
    source_banks = NARC(old.getFileByName('a/0/2/7')).files
    result_banks = NARC(new.getFileByName('a/0/2/7')).files
    original_banks = NARC(retail.getFileByName('a/0/2/7')).files
    donor_banks = NARC(native.getFileByName('a/0/2/7')).files
    _require(len(source_banks) == len(result_banks) == 830, 'message-bank count')
    field_context=geometry.context_from_rom(output,charmap,messages=new.getFileByName('a/0/2/7'))
    field_counts={'checked':0,'outside-scope':0,'changed':0,'max_width_px':0}
    for bank in range(829):
        source = _TEXT.read_bank(source_banks[bank], chars, commands)
        result = _TEXT.read_bank(result_banks[bank], chars, commands)
        original = _TEXT.read_bank(original_banks[bank], chars, commands) if bank < len(original_banks) else []
        translated = _TEXT.read_bank(donor_banks[bank], chars, commands) if bank < len(donor_banks) else []
        _require(len(source) == len(result), 'message count')
        for index, (before, after) in enumerate(zip(source, result)):
            _require(not (after['unknown_codes'] or after['malformed_controls']), 'message glyph/control syntax')
            if bank == 802 and index == 175:
                _require(after['normalized'] == before['normalized'], 'US height formatter'); counts['protected'] += 1
                continue
            previous = original[index] if index < len(original) else None
            untouched = (bank, index) != (300,29) and previous is not None and (before['normalized'] == previous['normalized'] or
                         before['controls'] == previous['controls'] and before['text'].strip().casefold() == previous['text'].strip().casefold())
            if untouched:
                _require(index < len(translated) and after['normalized'] == translated[index]['normalized'], 'retail text mismatch')
                counts['retail'] += 1
            else:
                key = aliases.setdefault(before['text'], f'm:{bank}:{index}')
                _require(key in strings and after['controls'] == before['controls'], 'authored text/control mismatch '+key)
                proof=geometry.check(bank,strings[key],after['text'],field_context,message=index)
                field_counts[proof['status']]+=1
                if proof['status']=='checked':
                    field_counts['changed']+=int(proof['changed'])
                    field_counts['max_width_px']=max(field_counts['max_width_px'],proof['max_width_px'])
                counts['authored'] += 1
    codec = ui_compile.module(ui_compile.SOURCE/'features/options/tools/codifica_testo.py', 'locale_readback_codec')
    table, _ = codec.carica_charmap(charmap)
    encode = lambda text: codec.codifica(text, table)
    at = locate(native_text.PC_LABEL_ADDRESS,24)
    _require(output[at:at+24] == native_text.pc_label(encode), 'portable PC label')
    for (address, _), expected in zip(keyboard.EDITS, keyboard.rows(locale, encode)):
        _require(output[locate(address, 28):locate(address, 28)+28] == expected, 'accent row')
    _require(output[locate(0x020F5670, 1)] == 2, 'game/save language')
    if locale=='DE':
        for address,expected in ((summary_labels.LABELS_ADDRESS,summary_labels.LABELS_REPLACEMENT),(summary_labels.LEGEND_ADDRESS,summary_labels.LEGEND_REPLACEMENT)):
            at=locate(address,len(expected));_require(output[at:at+len(expected)]==expected,'German FP/DV label')
    font = bytes(NARC(old.getFileByName('a/0/1/6')).files[0]); widths = font[struct.unpack_from('<I',font,4)[0]:]
    font_metrics = ui_compile.module(ui_compile.SOURCE/'quality-audit/misura_larghezza.py','native_readback_metrics')
    metric = font_metrics.extract_width_table(font)
    expected_bank = native_text.pack_onboarding(native_text.onboarding_strings(locale),encode,lambda w:font_metrics.measure(metric,w)['max_width_px'])
    at = locate(native_text.ONBOARDING_ADDRESS,native_text.ONBOARDING_BYTES)
    _require(output[at:at+native_text.ONBOARDING_BYTES] == expected_bank, 'native onboarding bank')
    expected_summary=native_text.pack_summary(native_text.summary_strings(locale),encode,lambda w:font_metrics.measure(metric,w)['max_width_px'])
    at=locate(native_text.SUMMARY_ADDRESS,native_text.SUMMARY_BYTES)
    _require(output[at:at+native_text.SUMMARY_BYTES]==expected_summary,'native Summary guide bank')
    assets = bytes(NARC(old.getFileByName('a/0/3/8')).files[51][128:48448])
    names = Bank(result_banks[237]).words
    species = {i:tuple(unpack_name(names[i])) for i in range(1,494)}
    authored, _ = ui_copy.encode_catalogue(ui_catalogue(), locale, encode, widths)
    uir = ui_resource_verify._verify_parts(retail.getFileByName('a/0/3/8'),new.getFileByName('a/0/3/8'),locale,assets,species,authored,zlib.crc32(widths))
    config = struct.unpack_from('<16I',output,locate(0x023D7BC0,64))
    _require(config == tuple(uir['config_fields'].values()), 'UI descriptor')
    guide = result_banks[829]
    categories, guide_encode, _ = build_categories(new,locale,strings,charmap)
    guide_content.verify_content(guide,guide_content.encoded_graph(categories,guide_encode))
    at = fat+156*8; start,end = struct.unpack_from('<II',output,at)
    archive = new.getFileByName('a/0/2/7'); image = archive.index(b'GMIF')
    guide_start = struct.unpack_from('<I',archive,28+829*8)[0]+image+8
    cats,entries = struct.unpack_from('<HH',guide,8)
    g = struct.unpack_from('<16I',output,locate(0x023D7C00,64))
    _require(g == (0x31435247,1,{'FR':2,'ES':3,'DE':4}[locale],0,156,start,end,len(output),len(archive),guide_start,len(guide),zlib.crc32(guide),cats,entries,0,0), 'Guide descriptor')
    return dict(status='passed', sha256=sha(output), preserved_files=513-len(paths),
                changed_files=len(paths),messages=counts,field_geometry=field_counts,
                guide_entries=entries,ui_bytes=uir['member_bytes'])
