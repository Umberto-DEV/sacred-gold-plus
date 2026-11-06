"""Guarded, append-only UI composition for exact V4 inputs, entirely in memory.

Only the returned immutable bytes are a candidate. This function does not write
ROMs, activate a workbench stage, accept runtime behavior, or reset a save.
"""
from pathlib import Path
import struct
import tempfile
import zlib

from ndspy import codeCompression
from ndspy import _common
from sgp12.blz import ndspy_decomprimi_sicuro
from sgp12.rom import Arm9, valida_layout_arm9
from sgp13 import event_flags

from . import archives, baseline, cartridge_deltas, reserve, ui_compile


def _decompress_overlay(encoded, expected):
    return ndspy_decomprimi_sicuro(encoded, expected)


def _bounded_image(data, capacity):
    if not 0 < len(data) <= capacity:
        raise ValueError('payload exceeds exact owner capacity')
    return data + bytes(capacity - len(data))


def _disjoint(spans):
    end = -1
    for lo, hi in sorted(spans):
        if not 0 <= lo < hi or lo < end:
            raise ValueError('overlapping or invalid writes')
        end = hi


def _arm_map(data):
    off, _, base, length = struct.unpack_from('<4I', data, 0x20)
    table, table_end, body, bss, _, packed = struct.unpack_from('<6I', data, off + 0xBA0)
    if base != 0x02000000 or packed or body != bss or not base < body <= table <= table_end <= base + length:
        raise ValueError('ARM9 initialized layout')
    _t0, _t1, _d0, sections, mapped = valida_layout_arm9(data, off, base, length)
    for address, _count, zero in sections:
        if zero != (32 if address == 0x027E0000 else 0):
            raise ValueError('autoload layout')
    def locate(address, size):
        found = [at + address - start for start, at, length in mapped
                 if start <= address and address + size <= start + length]
        if len(found) != 1:
            raise ValueError('unmapped write')
        return found[0]
    return locate


def _bl(site, target):
    delta = (target & ~1) - site - 4
    if not target & 1 or delta % 2 or not -0x400000 <= delta < 0x400000:
        raise ValueError('Thumb branch range/mode')
    return struct.pack('<HH', 0xF000 | (delta >> 12 & 2047), 0xF800 | (delta >> 1 & 2047))


def _replace_guide(raw, member):
    # Existing member829 is last. Preserve all preceding allocation entries,
    # names and GMIF bytes, including their padding; rebuild only the last span.
    table_bytes = struct.unpack_from('<I', raw, 20)[0]
    names_at = 16 + table_bytes
    image_at = names_at + struct.unpack_from('<I', raw, names_at + 4)[0]
    count = struct.unpack_from('<H', raw, 24)[0]
    if count != 830 or raw[image_at:image_at+4] != b'GMIF':
        raise ValueError('Guide archive geometry')
    start = struct.unpack_from('<I', raw, 28 + 829 * 8)[0]
    output = bytearray(raw[:image_at + 8 + start])
    output.extend(member)
    output.extend(bytes((-len(output)) % 4))
    struct.pack_into('<I', output, 28 + 829 * 8 + 4, start + len(member))
    struct.pack_into('<I', output, image_at + 4, len(output) - image_at)
    struct.pack_into('<I', output, 8, len(output))
    return bytes(output), image_at + 8 + start


def install(data: bytes, language: str, charmap: Path, work_dir: Path,
            archive_deltas=(), overlay_deltas=()) -> tuple[bytes, dict]:
    """`archive_deltas` declare the member changes of mechanical stages (archives.ArchiveDelta).

    Each changed archive is rebuilt from the exact V4 once: a/0/2/7 inside the Guide rewrite below,
    every other declared archive as one more appended body after file 167. Seeds are written once.
    """
    if type(data) is not bytes or baseline.identify(data) != language:
        raise ValueError('exact immutable input/language required')
    reserve.audit(data)  # metadata/preimages, never an allocation permission flag
    config = ui_compile.read_config(work_dir)
    ui_compile.check_sources()
    compiled = ui_compile.compile_payloads(config, work_dir)
    deltas = archives.check_against(archive_deltas, *archives.from_cartridge(data))
    resources = ui_compile.resources(data, language, charmap, deltas)
    locate = _arm_map(data)
    overlays = cartridge_deltas.check_against(overlay_deltas, data, language, work_dir)
    fat, fat_size, y9, y9_size = struct.unpack_from('<4I', data, 0x48)
    if (fat_size, y9_size) != (513 * 8, 129 * 32):
        raise ValueError('filesystem/table identity')
    def file(fid):
        a, b = struct.unpack_from('<II', data, fat + fid * 8)
        return data[a:b]
    output = bytearray(data)
    writes = []
    def write(at, value):
        if at < 0 or at + len(value) > len(data):
            raise ValueError('write outside initialized cartridge')
        writes.append((at, at + len(value)))
        output[at:at+len(value)] = value
    def arm(address, value):
        write(locate(address, len(value)), value)
    symbols = {k: v.get('symbols', {}) for k, v in compiled.items()}
    with tempfile.TemporaryDirectory(prefix='event-flags-', dir=work_dir) as flag_dir:
        flag_writes, _flag_receipt = event_flags.prepare_upgrade(
            Arm9.from_bytes(data), flag_dir, language,
            symbols['training']['training_ui_load'])
    for address, value in sorted(flag_writes.items()):
        arm(address, value)
    for name in ('bridge', 'physical', 'training', 'fieldbook'):
        part = compiled[name]
        arm(part['base'], _bounded_image(part['data'], part['capacity']))
    arm(0x023D4C00, bytes(3776))  # verified cold retirement before conditional grants
    template = lambda role: struct.pack('<4I', symbols['bridge']['ui_bridge_' + role + '_init'],
                                       symbols['bridge']['ui_bridge_main'], symbols['bridge']['ui_bridge_exit'], 0xFFFFFFFF)
    arm(0x020FA354, template('settings'))
    arm(0x023D7B10, template('guide'))
    for address, count in ((0x023D7B20, 40), (0x023D7B48, 16), (0x023D7210, 48), (0x023CB1F0, 16)):
        arm(address, bytes(count))
    d = [0x31544955, (80 << 16) | 1, (52 << 16) | 152, 3]
    d += [symbols['shiny']['sgp_shiny_ui_' + n] for n in ('peek', 'prepare', 'commit')]
    d += [symbols['training']['training_ui_' + n] for n in ('peek', 'validate', 'store', 'load', 'bind')]
    d += [0x023D1321, 0x023D1A45, 0x023D1B1D, 0x023CB1F0, 0, 0, 0, 0]
    arm(0x023CB1A0, struct.pack('<20I', *d))
    arm(0x023CB130, struct.pack('<I', symbols['training']['training_ui_bind']))
    for address, component, name in ((0x0201A556, 'physical', 'physical_after_native_mapping'),
                                      (0x02000DB0, 'physical', 'physical_lid_action'),
                                      (0x0203BFE4, 'fieldbook', 'fieldbook_task_input')):
        arm(address, _bl(address, symbols[component][name]))
    old27 = struct.unpack_from('<8I', data, y9 + 27 * 32)
    encoded27 = file(27)
    overlay27 = bytearray(_decompress_overlay(encoded27, old27[2]))
    if len(overlay27) != old27[2]:
        raise ValueError('overlay27 expanded size')
    for address, name in ((0x0225A0C6, 'fieldbook_create'), (0x0225A40E, 'fieldbook_touch'),
                           (0x0225A856, 'fieldbook_touch'), (0x0225A860, 'fieldbook_dpad'),
                           (0x0225A96E, 'fieldbook_focus')):
        overlay27[address-old27[1]:address-old27[1]+4] = _bl(address, symbols['fieldbook'][name])
    struct.pack_into('<I', overlay27, 0x0225A184-old27[1], symbols['fieldbook']['fieldbook_frame'])
    dynamic = compiled['dynamic54']['data']
    packed27 = codeCompression.compress(bytes(overlay27))
    packed54 = codeCompression.compress(dynamic)
    if (_decompress_overlay(packed27, len(overlay27)) != overlay27
            or _decompress_overlay(packed54, len(dynamic)) != dynamic):
        raise ValueError('compression roundtrip')
    changes = {d.file_id: d for d in deltas}
    base156 = file(156)
    if archives.GUIDE_FILE in changes:
        base156 = archives.apply_members(base156, changes[archives.GUIDE_FILE].replacements())
    guide_file, guide_member_offset = _replace_guide(base156, resources['guide'])
    replacements = {27: packed27, 54: packed54, 156: guide_file, 167: resources['uir']}
    for delta in deltas:
        if delta.file_id not in replacements:
            replacements[delta.file_id] = archives.apply_members(file(delta.file_id), delta.replacements())
    for delta in overlays:
        if delta.file_id in replacements:
            raise ValueError("overlay/archive file ownership overlap")
        replacements[delta.file_id] = delta.image
        write(y9 + 126 * 32, struct.pack("<8I", *delta.row))
    locations = {}
    for fid, value in replacements.items():
        output.extend(bytes((-len(output)) % 4))
        a = len(output)
        output.extend(value)
        locations[fid] = (a, len(output))
        write(fat + 8 * fid, struct.pack('<II', *locations[fid]))
    write(y9 + 27 * 32 + 28, struct.pack('<I', (old27[7] & 0xFE000000) | 0x01000000 | len(packed27)))
    size = len(dynamic)
    write(y9 + 54 * 32, struct.pack('<8I', 54, 0x021E5900, size, 0,
                                  0x021E5900 + size, 0x021E5900 + size, 54, 0x01000000 | len(packed54)))
    write(0x80, struct.pack('<I', len(output)))
    if len(output) > (128 * 1024 << data[0x14]):
        raise ValueError('candidate exceeds unchanged cartridge capacity')
    m = [0x314D4955, 2, 0, 0, 54, 54, 0x021E5900, size, 0,
         0x021E5900 + size, 0x021E5900 + size, 0x01000000 | len(packed54), zlib.crc32(dynamic)]
    m += [symbols['scene']['ui_scene_' + n] - 0x021E5900 for n in ('init', 'main', 'exit')]
    m += [zlib.crc32(packed54), zlib.crc32(output[y9:y9+y9_size]), y9, y9_size, len(output),
          *locations[54], 129]
    arm(0x023D7B60, struct.pack('<24I', *m))
    arm(0x023D7BC0, bytes.fromhex(resources['uir_receipt']['config_hex']))
    cats, entries = struct.unpack_from('<HH', resources['guide'], 8)
    g = [0x31435247, 1, int(language == 'IT'), 0, 156, *locations[156], len(output),
         len(guide_file), guide_member_offset, len(resources['guide']), zlib.crc32(resources['guide']),
         cats, entries, 0, 0]
    arm(0x023D7C00, struct.pack('<16I', *g))
    write(0x15E, struct.pack('<H', _common.crc16(output[:0x15E])))
    _disjoint(writes)
    after = bytes(output)
    del output
    ui_compile.check_sources()
    from . import ui_verify
    extra = {'archive_deltas': deltas} if deltas else {}
    if overlays:
        extra['overlay_deltas'] = overlays
    receipt = ui_verify.verify(data, after, language, charmap, work_dir, **extra)
    return after, receipt
