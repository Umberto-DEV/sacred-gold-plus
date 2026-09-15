"""Read-only AR code and ROM-section analysis helpers.

Extracted unchanged from the audit used for Community 1. Dynamic pointer and
overlay lifetime behavior still require execution; static equality is not proof
that every cheat effect works in game. Importing performs no file reads.
"""
import collections
import re
import struct
import ndspy.rom

def rom_sections(path):
    r = ndspy.rom.NintendoDSRom.fromFile(path)
    main = r.loadArm9()
    sections = [('ARM9:' + str(i), s.ramAddress, bytes(s.data)) for i, s in enumerate(main.sections)]
    sections.extend(('overlay:' + str(i), s.ramAddress, bytes(s.data)) for i, s in r.loadArm9Overlays().items())
    return sections


def read_sources(sections, addr, size):
    return [{'region': name, 'value': int.from_bytes(data[addr - start:addr - start + size], 'little')}
            for name, start, data in sections if start <= addr and addr + size <= start + len(data)]


def decode(code):
    """Decode AR instructions, skipping E payload rather than treating it as opcodes."""
    tokens = code.split()
    issues = []
    if not tokens:
        issues.append('empty_code')
    if len(tokens) % 2:
        issues.append('odd_word_count')
    if any(not re.fullmatch(r'[0-9A-Fa-f]{8}', token) for token in tokens):
        issues.append('invalid_hex_word')
    # Current Android JNI splits only on ASCII spaces, not generic whitespace.
    if any(ch in code for ch in '\t\r\n'):
        issues.append('android_non_space_separator')
    if issues:
        return [], issues
    pairs = [(int(tokens[i], 16), int(tokens[i + 1], 16)) for i in range(0, len(tokens), 2)]
    instructions = []
    i = 0
    while i < len(pairs):
        a, b = pairs[i]
        op = a >> 24
        ins = {'line': i + 1, 'a': a, 'b': b, 'op': op}
        if op >= 0xC0 and op not in [0xC0, 0xC5, 0xC6, *range(0xD0, 0xDD), *range(0xE0, 0x100)]:
            issues.append(f'unsupported_opcode:{a:08X}')
        if op == 0xD4 and (a & 0xFF) > 8:
            issues.append(f'unsupported_D4_operation:{a:08X}')
        if op >> 4 == 0xE:
            needed_lines = (b + 7) // 8
            remaining_lines = len(pairs) - i - 1
            ins['payload_declared_bytes'] = b
            ins['payload_available_bytes'] = remaining_lines * 8
            if remaining_lines < needed_lines:
                issues.append(f'truncated_E_payload:line={i+1}:declared={b}:available={remaining_lines*8}')
            payload = b''.join(struct.pack('<II', *p) for p in pairs[i + 1:i + 1 + needed_lines])
            ins['payload_hex'] = payload[:b].hex()
            i += needed_lines
        instructions.append(ins)
        i += 1
    return instructions, issues


def analyze_cheat(c, sections, reference_sections=None):
    instructions, issues = decode(c['codes'])
    result = dict(c)
    result['issues'] = issues
    result['android_imported'] = bool(c['folders'])
    if not c['folders']:
        result['issues'].append('android_importer_ignores_root_cheat')
    result['instruction_count'] = len(instructions)
    result['opcode_counts'] = dict(collections.Counter(f'{i["op"]:02X}' for i in instructions))
    guards, writes, reference_differences = [], [], []
    offset = 0
    local_writes = {}
    for ins in instructions:
        a, b, op = ins['a'], ins['b'], ins['op']
        addr = a & 0x0FFFFFFF
        typ = op >> 4
        if typ in (5, 9):
            size = 4 if typ == 5 else 2
            address = addr or offset
            if address is not None:
                sources = read_sources(sections, address, size)
                mask = 0xFFFFFFFF if typ == 5 else (~(b >> 16)) & 0xFFFF
                expected = b if typ == 5 else b & 0xFFFF
                matches = [v['region'] for v in sources if (v['value'] & mask) == expected]
                local = None
                if all(address + j in local_writes for j in range(size)):
                    local = int.from_bytes(bytes(local_writes[address+j] for j in range(size)), 'little')
                status = ('matching_source' if matches else 'matching_prior_write' if local is not None and (local & mask) == expected
                          else 'no_source_match' if sources else 'runtime_or_unmapped')
                guards.append({'line': ins['line'], 'address': f'{address:08X}', 'bytes': size,
                               'mask': f'{mask:08X}', 'expected': f'{expected:08X}', 'status': status,
                               'matching_regions': matches,
                               'source_values': [{'region': v['region'], 'value': f'{v["value"]:0{size*2}X}'} for v in sources]})
        payload = None
        if typ in (0, 1, 2):
            size = {0: 4, 1: 2, 2: 1}[typ]
            payload = (b & ((1 << (8 * size)) - 1)).to_bytes(size, 'little')
        elif typ == 0xE:
            payload = bytes.fromhex(ins['payload_hex'])
        if payload is not None:
            address = None if offset is None else (addr + offset) & 0xFFFFFFFF
            entry = {'line': ins['line'], 'address': None if address is None else f'{address:08X}',
                     'relative_address': f'{addr:08X}', 'bytes': len(payload), 'data_hex': payload.hex()}
            writes.append(entry)
            if address is not None:
                for j, byte in enumerate(payload):
                    local_writes[address + j] = byte
                if reference_sections:
                    current = read_sources(sections, address, len(payload))
                    reference = {v['region']: v['value'] for v in read_sources(reference_sections, address, len(payload))}
                    for v in current:
                        if v['region'] in reference and v['value'] != reference[v['region']]:
                            reference_differences.append({'line': ins['line'], 'address': f'{address:08X}',
                                                          'bytes': len(payload), 'region': v['region'],
                                                          'current': f'{v["value"]:X}', 'reference': f'{reference[v["region"]]:X}'})
        if typ == 0xB:
            offset = None  # Pointer contents belong to the running game.
        elif op == 0xD3:
            offset = b
        elif op == 0xDC:
            offset = None if offset is None else (offset + b) & 0xFFFFFFFF
        elif op == 0xD2:
            offset = 0
        elif op in (0xD6, 0xD7, 0xD8):
            writes.append({'line': ins['line'], 'address': None if offset is None else f'{(b+offset)&0xFFFFFFFF:08X}',
                           'relative_address': f'{b:08X}', 'bytes': {0xD6:4, 0xD7:2, 0xD8:1}[op], 'data_register': True})
            offset = None if offset is None else offset + {0xD6:4, 0xD7:2, 0xD8:1}[op]
    # Several cheats deliberately check for a previously installed patch in a
    # restore branch. A guard not present in pristine ROM data is therefore not
    # automatically broken. Match a single constant write elsewhere in the same
    # cheat, combined with unchanged bytes of each source region.
    for guard in guards:
        if guard['status'] != 'no_source_match':
            continue
        address, size = int(guard['address'], 16), guard['bytes']
        mask, expected = int(guard['mask'], 16), int(guard['expected'], 16)
        matching_lines = []
        for write in writes:
            if write['address'] is None or 'data_hex' not in write:
                continue
            waddr = int(write['address'], 16)
            payload = bytes.fromhex(write['data_hex'])
            if not (waddr < address + size and address < waddr + len(payload)):
                continue
            for source in guard['source_values']:
                candidate = bytearray(int(source['value'], 16).to_bytes(size, 'little'))
                for j in range(size):
                    if waddr <= address + j < waddr + len(payload):
                        candidate[j] = payload[address + j - waddr]
                if (int.from_bytes(candidate, 'little') & mask) == expected:
                    matching_lines.append(write['line'])
        if matching_lines:
            guard['status'] = 'matching_write_elsewhere_in_cheat'
            guard['matching_write_lines'] = sorted(set(matching_lines))
    result['equality_guards'] = guards
    result['writes'] = writes
    result['write_site_differences_vs_HG_US'] = reference_differences
    return result


def main():
    """Inspect a user-supplied catalogue against a local ROM; no inputs are bundled."""
    import argparse
    import json
    from pathlib import Path
    import xml.etree.ElementTree as ET
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('catalogue', type=Path)
    parser.add_argument('--rom', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    sections = rom_sections(args.rom)
    report = []
    for folder in ET.parse(args.catalogue).iter('folder'):
        for cheat in folder.findall('cheat'):
            report.append(analyze_cheat({
                'folders': [folder.findtext('name', '')],
                'name': cheat.findtext('name', ''),
                'note': cheat.findtext('note', ''),
                'codes': cheat.findtext('codes', ''),
            }, sections))
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(f'{len(report)} codes; {sum(bool(c["issues"]) for c in report)} syntax failures')
    return int(any(c['issues'] for c in report))


if __name__ == '__main__':
    raise SystemExit(main())
