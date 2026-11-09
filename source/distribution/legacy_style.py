"""Reuse original manual glyphs without distributing standalone fonts.

Historical PDFs contain symbol-encoded sparse TrueType subsets. Recovery changes
cmap/name metadata and supplies omitted unused bearings, retaining the original
outlines, advances and hinting. Call ``require`` before rendering any prose.
"""
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
import hashlib
import re
import struct

from pypdf import PdfReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase._glyphlist import _glyphname2unicode
from reportlab.pdfbase.ttfonts import TTFont


def _need(condition, reason):
    if not condition:
        raise ValueError(reason)


def _tables(raw):
    _need(len(raw) >= 12 and raw[:4] == b'\x00\x01\x00\x00', 'unsupported embedded font')
    count = struct.unpack_from('>H', raw, 4)[0]
    _need(12 + 16 * count <= len(raw), 'truncated embedded font directory')
    result = {}
    for index in range(count):
        tag, _, offset, size = struct.unpack_from('>4sIII', raw, 12 + 16 * index)
        _need(tag not in result and offset + size <= len(raw), 'invalid embedded font table')
        result[tag] = raw[offset:offset + size]
    return result


def _glyph_map(cmap):
    """Read bounded format 0/4/6 cmaps used by historical PDF subsets."""
    result = {}
    _need(len(cmap) >= 4, 'truncated font cmap')
    count = struct.unpack_from('>H', cmap, 2)[0]
    _need(4 + count * 8 <= len(cmap), 'truncated font cmap records')
    records = [struct.unpack_from('>HHI', cmap, 4 + 8 * i) for i in range(count)]
    for platform, encoding, offset in sorted(records, key=lambda row: row[0] == 3):
        _need(offset + 6 <= len(cmap), 'invalid font cmap offset')
        fmt, size = struct.unpack_from('>HH', cmap, offset)
        _need(offset + size <= len(cmap), 'truncated font cmap subtable')
        sub = cmap[offset:offset + size]
        if fmt == 0:
            _need(len(sub) >= 262, 'truncated format 0 cmap')
            result.update((i, sub[6 + i]) for i in range(256) if sub[6 + i])
        elif fmt == 6:
            _need(len(sub) >= 10, 'truncated format 6 cmap')
            first, number = struct.unpack_from('>HH', sub, 6)
            _need(10 + 2 * number <= len(sub), 'truncated format 6 glyphs')
            result.update((first + i, struct.unpack_from('>H', sub, 10 + 2 * i)[0])
                          for i in range(number) if struct.unpack_from('>H', sub, 10 + 2 * i)[0])
        elif fmt == 4:
            _need(len(sub) >= 16, 'truncated format 4 cmap')
            segments = struct.unpack_from('>H', sub, 6)[0] // 2
            _need(16 + 8 * segments <= len(sub), 'truncated format 4 segments')
            for i in range(segments):
                end = struct.unpack_from('>H', sub, 14 + 2 * i)[0]
                start = struct.unpack_from('>H', sub, 16 + 2 * segments + 2 * i)[0]
                delta = struct.unpack_from('>h', sub, 16 + 4 * segments + 2 * i)[0]
                range_address = 16 + 6 * segments + 2 * i
                shift = struct.unpack_from('>H', sub, range_address)[0]
                _need(start <= end, 'invalid format 4 range')
                for code in range(start, min(end, 65534) + 1):
                    if shift:
                        address = range_address + shift + 2 * (code - start)
                        _need(address + 2 <= len(sub), 'invalid format 4 glyph offset')
                        glyph = struct.unpack_from('>H', sub, address)[0]
                        if glyph:
                            glyph = (glyph + delta) & 65535
                    else:
                        glyph = (code + delta) & 65535
                    if glyph:
                        result[code] = glyph
    _need(result, 'embedded font cmap has no supported glyphs')
    return result


def _unicode_map(font):
    encoding = font.get('/Encoding')
    result = {}
    if encoding:
        encoding = encoding.get_object()
        base = encoding.get('/BaseEncoding') if isinstance(encoding, dict) else encoding
        _need(base in (None, '/WinAnsiEncoding'), 'unsupported PDF font encoding')
        for code in range(256):
            try:
                result[code] = ord(bytes([code]).decode('cp1252'))
            except UnicodeDecodeError:
                pass
        if isinstance(encoding, dict):
            code = 0
            for value in encoding.get('/Differences', []):
                if isinstance(value, int):
                    code = int(value)
                else:
                    result.pop(code, None)
                    name = str(value).lstrip('/')
                    if name in _glyphname2unicode:
                        result[code] = _glyphname2unicode[name]
                    elif re.fullmatch(r'uni[0-9A-Fa-f]{4}', name):
                        result[code] = int(name[3:], 16)
                    code += 1
    cmap = font.get('/ToUnicode')
    if cmap:
        text = cmap.get_object().get_data().decode('ascii')
        for block in re.findall(r'beginbfchar(.*?)endbfchar', text, re.S):
            for source, target in re.findall(r'<([0-9a-fA-F]+)>\s*<([0-9a-fA-F]+)>', block):
                decoded = bytes.fromhex(target).decode('utf-16-be')
                if len(decoded) == 1:
                    result[int(source, 16)] = ord(decoded)
        for block in re.findall(r'beginbfrange(.*?)endbfrange', text, re.S):
            for start, end, target in re.findall(
                    r'<([0-9a-fA-F]+)>\s*<([0-9a-fA-F]+)>\s*<([0-9a-fA-F]+)>', block):
                first, last, value = int(start, 16), int(end, 16), int(target, 16)
                _need(first <= last <= 255 and value + last - first <= 65535,
                      'unsupported PDF Unicode range')
                result.update((code, value + code - first) for code in range(first, last + 1))
    return result


def _checksum(raw):
    raw += bytes((-len(raw)) % 4)
    return sum(struct.unpack('>' + 'I' * (len(raw) // 4), raw)) & 0xffffffff


def _sfnt(tables):
    tables = dict(tables)
    head = bytearray(tables[b'head'])
    struct.pack_into('>I', head, 8, 0)
    tables[b'head'] = bytes(head)
    count = len(tables)
    power = 2 ** (count.bit_length() - 1)
    header = struct.pack('>IHHHH', 0x10000, count, 16 * power,
                         power.bit_length() - 1, 16 * (count - power))
    directory, payload = bytearray(), bytearray()
    head_offset = None
    for tag, data in sorted(tables.items()):
        offset = 12 + 16 * count + len(payload)
        directory.extend(struct.pack('>4sIII', tag, _checksum(data), offset, len(data)))
        if tag == b'head':
            head_offset = offset
        payload.extend(data)
        payload.extend(bytes((-len(payload)) % 4))
    raw = bytearray(header + directory + payload)
    struct.pack_into('>I', raw, head_offset + 8, (0xB1B0AFBA - _checksum(raw)) & 0xffffffff)
    return bytes(raw)


def _restore(raw, mapping, name):
    tables = _tables(raw)
    segments = sorted(mapping.items()) + [(65535, 0)]
    count = len(segments)
    power = 2 ** (count.bit_length() - 1)
    sub = struct.pack('>7H', 4, 16 + 8 * count, 0, 2 * count,
                      2 * power, power.bit_length() - 1, 2 * (count - power))
    sub += struct.pack('>' + 'H' * count, *(code for code, _ in segments)) + b'\0\0'
    sub += struct.pack('>' + 'H' * count, *(code for code, _ in segments))
    sub += struct.pack('>' + 'H' * count, *((glyph - code) & 65535 for code, glyph in segments))
    sub += bytes(2 * count)
    tables[b'cmap'] = struct.pack('>HHHHI', 0, 1, 3, 1, 12) + sub
    encoded = name.encode('utf-16-be')
    tables[b'name'] = struct.pack('>HHH', 0, 1, 18) + struct.pack('>6H', 3, 1, 0x409, 6, len(encoded), 0) + encoded
    glyphs = struct.unpack_from('>H', tables[b'maxp'], 4)[0]
    metrics = struct.unpack_from('>H', tables[b'hhea'], 34)[0]
    _need(0 < metrics <= glyphs and len(tables[b'hmtx']) >= 4 * metrics,
          'invalid embedded font metrics')
    needed = 4 * metrics + 2 * (glyphs - metrics)
    _need(len(tables[b'hmtx']) <= needed, 'invalid embedded font bearings')
    tables[b'hmtx'] += bytes(needed - len(tables[b'hmtx']))
    return _sfnt(tables)


@dataclass(frozen=True)
class EmbeddedFace:
    """In-memory recovered subset; never distribute font_bytes separately."""
    name: str
    original_name: str
    font_bytes: bytes
    codepoints: frozenset

    def require(self, text):
        missing = sorted({ord(char) for char in text if char not in '\n\r\t'} - self.codepoints)
        _need(not missing, self.original_name + ' lacks glyphs: ' + ', '.join(f'U+{code:04X}' for code in missing))

    def register(self):
        if self.name not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont(self.name, BytesIO(self.font_bytes)))
        return self.name


def load_face(pdf_path, family, *, expected_sha256=None):
    """Recover one unique embedded family from a caller-authenticated original."""
    raw = Path(pdf_path).read_bytes()
    if expected_sha256 is not None:
        _need(hashlib.sha256(raw).hexdigest() == expected_sha256, 'original PDF identity mismatch')
    fonts = {}
    for page in PdfReader(BytesIO(raw)).pages:
        resources = page.get('/Resources', {}).get_object()
        for entry in resources.get('/Font', {}).values():
            font = entry.get_object()
            original = str(font.get('/BaseFont', '')).lstrip('/')
            if original.split('+')[-1] != family:
                continue
            descriptor = font.get('/FontDescriptor')
            _need(descriptor is not None and '/FontFile2' in descriptor.get_object(),
                  'original font is not embedded TrueType')
            embedded = descriptor.get_object()['/FontFile2'].get_data()
            glyphs = _glyph_map(_tables(embedded)[b'cmap'])
            codes = _unicode_map(font)
            first, last = int(font.get('/FirstChar', 0)), int(font.get('/LastChar', 255))
            mapping = {}
            for code in range(first, last + 1):
                if code not in codes:
                    continue
                glyph = glyphs.get(code + 0xf000) or glyphs.get(code) or glyphs.get(codes[code])
                if glyph:
                    mapping[codes[code]] = glyph
            _need(mapping, 'original font has no recoverable Unicode glyphs')
            identity = hashlib.sha256(embedded).hexdigest()
            fonts[identity] = (original, embedded, mapping)
    _need(len(fonts) == 1, 'missing or ambiguous original font: ' + family)
    identity, (original, embedded, mapping) = next(iter(fonts.items()))
    name = 'SGPLegacy-' + re.sub('[^A-Za-z0-9]', '', family) + '-' + identity[:12]
    return EmbeddedFace(name, original, _restore(embedded, mapping, name), frozenset(mapping))


def extract_cover_art(pdf_path):
    """Return the largest original first-page image with its original pixels."""
    images = list(PdfReader(pdf_path).pages[0].images)
    _need(images, 'original PDF cover has no illustration')
    return max(images, key=lambda entry: entry.image.width * entry.image.height).data
