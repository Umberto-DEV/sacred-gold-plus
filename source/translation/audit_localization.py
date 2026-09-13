#!/usr/bin/env python3
"""Read-only three-way localization audit. Never writes a ROM or a message archive.

The message cipher and 9-bit name packing follow pret/pokeheartgold msgenc.
Dependencies: ndspy 4.2.0. Read original SG+ 1.03, US and Italian ROMs.
"""
from pathlib import Path
import argparse
import collections
import hashlib
import json
import re
import struct
import xml.etree.ElementTree as ET
import ndspy.rom
import ndspy.narc

OUT = Path(__file__).resolve().parent
ROMDIR = None
PRET = None
NAMES = {'US':'Pokemon - HeartGold Version.nds', 'IT':'Pokemon - Versione Oro HeartGold.nds', 'SG':'Pokemon - Sacred Gold Plus.nds'}


def mapping():
    chars, commands = {}, {}
    for line in (PRET/'charmap.txt').read_text().splitlines():
        line = line.split('//')[0].lstrip()
        if not line or '=' not in line:
            continue
        code, text = line.split('=', 1)
        code = int(code, 16)
        if text.startswith('{') and text.endswith('}'):
            commands[code] = text[1:-1]
        else:
            chars[code] = text
    return chars, commands


CHARMAP, COMMANDS = {}, {}


def configure_from_args(description=None):
    """Configure paths explicitly; importing this module performs no file reads."""
    global OUT, ROMDIR, PRET, CHARMAP, COMMANDS
    parser = argparse.ArgumentParser(description=description or __doc__)
    parser.add_argument('--rom-dir', type=Path, required=True,
                        help='Directory containing the three original ROMs named in NAMES.')
    parser.add_argument('--pret-source', type=Path, required=True,
                        help='Local pret/pokeheartgold checkout with charmap.txt and GMM sources.')
    parser.add_argument('--output-dir', type=Path, default=OUT,
                        help='Local private output directory. Defaults to this script directory.')
    args = parser.parse_args()
    ROMDIR, PRET, OUT = args.rom_dir.resolve(), args.pret_source.resolve(), args.output_dir.resolve()
    for name, directory in [('ROM', ROMDIR), ('pret source', PRET)]:
        if not directory.is_dir():
            parser.error(f'{name} directory does not exist: {directory}')
    CHARMAP, COMMANDS = mapping()
    return args


def expand_name(words):
    if not words or words[0] != 0xF100:
        return words, False
    packed, bitcount, result = 0, 0, []
    for word in words[1:]:
        packed |= (word & 0x7FFF) << bitcount
        bitcount += 15
        while bitcount >= 9:
            code = packed & 0x1FF
            packed >>= 9
            bitcount -= 9
            if code == 0x1FF:
                return result + [0xFFFF], True
            result.append(code)
    raise ValueError('Compressed name missing terminator')


def render(words):
    words, compressed = expand_name(words)
    text, controls, unknown, normalized, malformed = [], [], [], [], []
    i = 0
    while i < len(words):
        c = words[i]
        normalized.append(c)
        i += 1
        if c == 0xFFFF:
            break
        if c == 0xFFFE:
            if i + 2 > len(words):
                malformed.append({'word_index':i-1,'reason':'truncated control header'})
                normalized.extend(words[i:])
                text.append('{INVALID_CONTROL_HEADER}')
                break
            command, count = words[i:i+2]
            args = words[i+2:i+2+count]
            if len(args) != count:
                malformed.append({'word_index':i-1,'reason':'truncated control arguments','command':command,'declared_arguments':count,'remaining_words':len(words)-i-2})
                normalized.extend(words[i:])
                text.append('{INVALID_CONTROL:'+','.join(f'{w:04X}' for w in words[i:])+'}')
                break
            normalized.extend([command, count, *args])
            controls.append([command, args])
            name = COMMANDS.get(command)
            if not name and command & 0xFF00 in (0x100, 0x300, 0x400, 0x3400):
                name = f'STRVAR_{command>>8:X}:{command&255}'
            text.append('{' + (name or f'CMD_{command:04X}') + (':' if args else '') + ','.join(map(str,args)) + '}')
            i += 2 + count
        elif c in CHARMAP:
            text.append(CHARMAP[c])
        else:
            unknown.append(c)
            text.append(f'<{c:04X}>')
    assert normalized[-1] == 0xFFFF, 'Missing string terminator'
    return {'text': ''.join(text), 'controls': controls, 'unknown_codes': unknown,'malformed_controls':malformed,
            'normalized': normalized, 'compressed_name': compressed}


def read_bank(data):
    count, key = struct.unpack_from('<HH', data)
    assert 4 + 8*count <= len(data)
    messages = []
    for index in range(count):
        table_key = (765*(index+1)*key) & 0xFFFF
        table_key |= table_key << 16
        offset, size = struct.unpack_from('<II',data,4+8*index)
        offset ^= table_key
        size ^= table_key
        assert offset >= 4 + 8*count and offset+size*2 <= len(data), (index, offset, size, len(data))
        encrypted = struct.unpack_from(f'<{size}H',data,offset)
        seed = ((index+1)*596947)&0xFFFF
        words = []
        for word in encrypted:
            words.append(word ^ seed)
            seed = (seed + 18749)&0xFFFF
        messages.append(render(words))
    return messages


def plain_words(text):
    text = re.sub(r'\{[^}]*\}', ' ', text).replace('\\n',' ').replace('\\r',' ').replace('\\f',' ')
    return re.findall(r"[A-Za-zÀ-ž]+(?:['’-][A-Za-zÀ-ž]+)?",text)


def audit():
    OUT.mkdir(parents=True, exist_ok=True)
    roms = {k:ndspy.rom.NintendoDSRom.fromFile(ROMDIR/n) for k,n in NAMES.items()}
    banks = {k:ndspy.narc.NARC(r.getFileByName('a/0/2/7')).files for k,r in roms.items()}
    decoded = {k:[read_bank(b) for b in archive] for k,archive in banks.items()}
    assert all(len(v)==829 for v in decoded.values())
    # Independent plaintext reference for simple names; all 468 retail move names
    # must agree with the decompilation's original GMM, not merely look plausible.
    gmm = ET.parse(PRET/'files/msgdata/msg/msg_0750.gmm').getroot()
    source_moves = [''.join(row.find('language').itertext()) for row in gmm.findall('row')]
    assert source_moves == [m['text'] for m in decoded['US'][750]]
    files = {int(p.name[4:8]):p.name for p in (PRET/'files/msgdata/msg').glob('msg_*.gmm')}
    alignment, modified, reusable, bank_rows, identical_banks = [], [], [], [], []
    counters = collections.Counter()
    for bi in range(829):
        u,it,sg = (decoded[k][bi] for k in ['US','IT','SG'])
        ui_aligned = len(u)==len(it)
        same_sg = [m['normalized'] for m in u] == [m['normalized'] for m in sg]
        if same_sg:
            identical_banks.append(bi)
        row = {'bank':bi,'source_name':files.get(bi),'US_count':len(u),'IT_count':len(it),'SG_count':len(sg),
               'SG_equals_US_all_messages':same_sg,'US_IT_equal_count':ui_aligned,
               'binary_SG_equals_US':banks['SG'][bi]==banks['US'][bi],
               'counts':collections.Counter()}
        if not ui_aligned or len(sg)!=len(u):
            alignment.append({k:v for k,v in row.items() if k!='counts'})
        for mi,msg in enumerate(sg):
            us = u[mi] if mi<len(u) else None
            italian = it[mi] if mi<len(it) else None
            unchanged = us is not None and msg['normalized']==us['normalized']
            controls_equal = bool(us is not None and italian is not None and us['controls']==italian['controls'])
            if unchanged and ui_aligned and controls_equal:
                status = 'unchanged_US_candidate_Italian_reuse'
                reusable.append({'bank':bi,'message':mi,'Italian_changes_text':italian['normalized']!=us['normalized']})
            elif unchanged:
                status = 'unchanged_US_alignment_or_control_review'
            else:
                status = 'SG_modified_or_added_preserve_and_translate'
                modified.append({'bank':bi,'message':mi,'source_name':files.get(bi),
                                 'US':None if us is None else us['text'], 'IT_reference':None if italian is None else italian['text'],
                                 'SG':msg['text'],'added_index':us is None,
                                 'US_IT_equal_count':ui_aligned,'SG_controls':msg['controls'],
                                 'US_controls':None if us is None else us['controls'], 'SG_malformed_controls':msg['malformed_controls'],
                                 'SG_word_count':len(plain_words(msg['text']))})
            counters[status]+=1
            row['counts'][status]+=1
        bank_rows.append(row)
    fonts={}
    for k,r in roms.items():
        data=r.getFileByName('a/0/1/6')
        archive=ndspy.narc.NARC(data)
        fonts[k]={'path':'a/0/1/6','sha256':hashlib.sha256(data).hexdigest(),'entries':len(archive.files),'sizes':[len(f) for f in archive.files]}
    accents={ch:[f'{code:04X}' for code,text in CHARMAP.items() if text==ch] for ch in 'àèéìòùÈÀÉÌÒÙ'}
    result={'scope':'Read only feasibility. No translated or modified ROM generated. SG+ 1.03 remains authoritative.',
            'archives':{k:{'bank_count':len(v),'message_count':sum(map(len,v)),
                           'narc_bytes':len(roms[k].getFileByName('a/0/2/7')),
                           'unknown_character_codes':sorted({c for bank in v for msg in bank for c in msg['unknown_codes']}),
                           'malformed_control_messages':[{'bank':bi,'message':mi,'issues':msg['malformed_controls']} for bi,bank in enumerate(v) for mi,msg in enumerate(bank) if msg['malformed_controls']]} for k,v in decoded.items()},
            'classification_counts':dict(counters),'banks_SG_unchanged_from_US':len(identical_banks),
            'banks_SG_modified_from_US':829-len(identical_banks),
            'banks_with_count_mismatch':alignment,'bank_rows':bank_rows,
            'modified_SG_messages':len(modified),'added_message_indices':sum(c['added_index'] for c in modified),
            'modified_SG_word_count':sum(c['SG_word_count'] for c in modified),
            'fonts':fonts,'accent_codes':accents,
            'source_validation':'All original US move-name strings match pret msg_0750.gmm exactly.'}
    (OUT/'localization_audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    (OUT/'SG_text_to_preserve_and_translate.json').write_text(json.dumps(modified,ensure_ascii=False,indent=2)+'\n')
    (OUT/'Italian_reuse_candidates.json').write_text(json.dumps(reusable,ensure_ascii=False,indent=2)+'\n')
    # Full decoded catalogs remain in this local analysis folder for repeatable
    # auditing. They are user-supplied game text, not a patch to distribute.
    (OUT/'decoded_catalogs.json').write_text(json.dumps({k:[[{'text':m['text'],'controls':m['controls']} for m in b] for b in v] for k,v in decoded.items()},ensure_ascii=False)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ['bank_rows','banks_with_count_mismatch']},ensure_ascii=False,indent=2))
    print('Banks with changed counts:', len(alignment))


if __name__=='__main__':
    configure_from_args()
    audit()
