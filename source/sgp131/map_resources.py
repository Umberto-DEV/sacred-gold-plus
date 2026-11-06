"""Strict, lossless HGSS map-resource envelopes for source-only authoring.

Native reference: pret/pokeheartgold 0985e8718df4f25e64d6507d89c0c97c0d288981,
include/map_matrix.h and src/map_matrix.c. The matrix loader's buffers hold
799 cells and 16 name bytes. Names are opaque bytes, not decoded text.

Land sections follow asm/overlay_01_021F4704.s: ov01_021F49FC reads the four
lengths, ov01_021F4AAC consumes the variable BGS prefix, then permissions,
buildings, model, collision follow. Fixed 0x800-byte permission reads in
ov01_021F4D88/ov01_021F4F0C and src/terrain_attributes.c mean absent permissions
are unsupported here. Other sections remain opaque, including empty payloads.
These codecs validate envelopes, not graphics, collision semantics or playability.
"""
from dataclasses import dataclass, replace
import struct
from typing import Optional, Tuple


def _integer(value: int, minimum: int, maximum: int, field: str) -> None:
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValueError(f'{field} must be an integer in {minimum}..{maximum}')


def _payload(value: bytes, field: str, maximum: int = 0xffffffff) -> None:
    if type(value) is not bytes:
        raise ValueError(f'{field} must be immutable bytes')
    if len(value) > maximum:
        raise ValueError(f'{field} is too long')


def _cells(values: Tuple[int, ...], count: int, maximum: int, field: str) -> None:
    if type(values) is not tuple or len(values) != count:
        raise ValueError(f'{field} must be a tuple of exactly {count} cells')
    for value in values:
        _integer(value, 0, maximum, field)


@dataclass(frozen=True)
class Matrix:
    """Row-major matrix; None retains an absent optional section on the wire.

    The engine accepts arbitrary nonzero presence flags. This authoring codec
    supports canonical 0/1 only and explicitly refuses other flag encodings.
    Land index 0xffff remains a valid sentinel, not an archive member lookup.
    """

    width: int
    height: int
    name: bytes
    headers: Optional[Tuple[int, ...]]
    altitudes: Optional[Tuple[int, ...]]
    lands: Tuple[int, ...]

    def __post_init__(self) -> None:
        _integer(self.width, 1, 255, 'width')
        _integer(self.height, 1, 255, 'height')
        count = self.width * self.height
        if count > 799:
            raise ValueError('matrix exceeds native capacity of 799 cells')
        _payload(self.name, 'name', 16)
        if self.headers is not None:
            _cells(self.headers, count, 65535, 'headers')
        if self.altitudes is not None:
            _cells(self.altitudes, count, 255, 'altitudes')
        _cells(self.lands, count, 65535, 'lands')

    @classmethod
    def parse(cls, data: bytes) -> 'Matrix':
        _payload(data, 'matrix')
        if len(data) < 5:
            raise ValueError('truncated matrix prefix')
        width, height, has_headers, has_altitudes, name_length = data[:5]
        if has_headers not in (0, 1) or has_altitudes not in (0, 1):
            raise ValueError('unsupported noncanonical matrix presence flag')
        count = width * height
        expected = 5 + name_length + count * (2 + 2 * has_headers + has_altitudes)
        if len(data) != expected:
            raise ValueError(f'matrix length {len(data)} does not match {expected}')
        cursor = 5 + name_length
        name = data[5:cursor]
        headers = None
        altitudes = None
        if has_headers:
            headers = struct.unpack_from(f'<{count}H', data, cursor)
            cursor += 2 * count
        if has_altitudes:
            altitudes = tuple(data[cursor:cursor + count])
            cursor += count
        lands = struct.unpack_from(f'<{count}H', data, cursor)
        return cls(width, height, name, headers, altitudes, lands)

    def encode(self) -> bytes:
        self.__post_init__()
        result = bytes((self.width, self.height, int(self.headers is not None),
                        int(self.altitudes is not None), len(self.name))) + self.name
        if self.headers is not None:
            result += struct.pack(f'<{len(self.headers)}H', *self.headers)
        if self.altitudes is not None:
            result += bytes(self.altitudes)
        return result + struct.pack(f'<{len(self.lands)}H', *self.lands)


@dataclass(frozen=True)
class LandData:
    """Lossless section payloads; the BGS signature and lengths are regenerated."""

    bgs: bytes
    permissions: bytes
    buildings: bytes
    model: bytes
    collision: bytes

    def __post_init__(self) -> None:
        _payload(self.bgs, 'bgs', 65535)
        for field in ('permissions', 'buildings', 'model', 'collision'):
            _payload(getattr(self, field), field)
        if len(self.permissions) != 2048:
            raise ValueError('unsupported HGSS permissions: expected 2048 bytes (32 x 32 u16 cells)')

    @classmethod
    def parse(cls, data: bytes) -> 'LandData':
        _payload(data, 'landdata')
        if len(data) < 20:
            raise ValueError('truncated landdata prefix')
        sizes = struct.unpack_from('<4I', data)
        signature, bgs_length = struct.unpack_from('<HH', data, 16)
        if signature != 0x1234:
            raise ValueError('unsupported landdata BGS signature')
        expected = 20 + bgs_length + sum(sizes)
        if len(data) != expected:
            raise ValueError(f'landdata length {len(data)} does not match {expected}')
        cursor = 20 + bgs_length
        bgs = data[20:cursor]
        sections = []
        for size in sizes:
            sections.append(data[cursor:cursor + size])
            cursor += size
        return cls(bgs, *sections)

    def encode(self) -> bytes:
        self.__post_init__()
        sections = (self.permissions, self.buildings, self.model, self.collision)
        return (struct.pack('<4IHH', *(len(s) for s in sections), 0x1234, len(self.bgs))
                + self.bgs + b''.join(sections))

    def with_permission(self, x: int, z: int, value: int) -> 'LandData':
        """Return one edited cell without changing BGS, graphics or collision."""
        _integer(x, 0, 31, 'x')
        _integer(z, 0, 31, 'z')
        _integer(value, 0, 65535, 'permission')
        offset = 2 * (z * 32 + x)
        permissions = (self.permissions[:offset] + struct.pack('<H', value)
                       + self.permissions[offset + 2:])
        return replace(self, permissions=permissions)
