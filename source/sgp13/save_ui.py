"""Truthful recoverable touch-save failure in a bounded overlay30 extension."""
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
BASE = 0x0225DCE8
ORIGINAL_SIZE = 1984
OVERLAY_SHA = 'cfb3e4edb36ea20bd254111aaaf9bf9ff4b97b285ed0ad4752c5def000738c08'
COMPRESSED_SHA = '1df8e09623ac2933c94b5eca072e9551b4ffb1aac7d0063d44370cceb6b5d5fe'
CHARMAP_SHA = '58861d34f40623fd2a9b29c10a79ee2ec872182285a288381759a3b251412ded'
BANK_SHA = {'EN': 'a8c407a961f30f8c18f0bf4ac7f9a6d704ac8f29849fae17726c2fc4b8912bf7',
            'IT': '4ac08018d028f1f9491eadd1f8dd39f8822adc3405fbe7bbc913e3dc2f1e41a8'}
TEXT = {'EN': 'Save failed.\nYour progress was not saved.',
        'IT': 'Salvataggio non riuscito.\nI progressi non sono stati salvati.'}
ENTRIES = ('sgp_saveui_save', 'sgp_saveui_failure', 'sgp_saveui_ack')


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def sha(data):
    return hashlib.sha256(data).hexdigest()


def compile_native(directory):
    """Compile original overlay-local code, refusing non-text allocations."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    obj = directory / 'save-ui.o'
    flags = ['--target=armv5te-none-eabi', '-mcpu=arm946e-s', '-mthumb', '-Oz',
             '-ffreestanding', '-fno-builtin', '-fno-stack-protector', '-fno-jump-tables',
             '-fno-unwind-tables', '-fno-asynchronous-unwind-tables', '-Wall', '-Wextra', '-Werror']
    subprocess.run(['clang', *flags, '-c', str(ROOT / 'features/save-ui/runtime.c'),
                    '-o', str(obj)], check=True, capture_output=True)
    loader = module(ROOT / 'features/options/tools/carica_text.py', 'save_ui_loader')
    blob, symbols = loader.load_text(obj.read_bytes(), BASE, ENTRIES)
    raw_size = (ORIGINAL_SIZE + 8 + len(blob) + 31) & ~31
    if raw_size > ORIGINAL_SIZE + 512:
        raise ValueError('save UI overlay extension exceeds 512 bytes')
    return blob, {name: symbols[name] for name in ENTRIES}


def append_message(raw, words):
    """Append one entry without changing existing IDs or ciphertext payloads."""
    from translation.message_codec import Bank
    bank = Bank(raw)
    if len(bank.words) != 117 or bank.key != 53262:
        raise ValueError('save UI bank40 preimage count/key')
    bank.words.append(list(words))
    result = bank.save()
    if Bank(result).words[:-1] != bank.words[:-1]:
        raise ValueError('save UI existing message preservation')
    return result


def patch_overlay(before, blob, symbols):
    if len(before) != 1984 or sha(before) != OVERLAY_SHA:
        raise ValueError('save UI overlay30 preimage')
    result = bytearray(before)
    struct.pack_into('<I', result, 0x7b0, symbols['sgp_saveui_save'])
    result.extend(struct.pack('<II', symbols['sgp_saveui_failure'], symbols['sgp_saveui_ack']))
    result.extend(blob)
    result.extend(bytes((-len(result)) % 32))
    if len(result) > 2496:
        raise ValueError('save UI overlay extension exceeds 512 bytes')
    return bytes(result)


def _identity(data, language, charmap_path):
    import ndspy.rom
    import ndspy.narc
    if language not in ('EN', 'IT'):
        raise ValueError('save UI language')
    if sha(Path(charmap_path).read_bytes()) != CHARMAP_SHA:
        raise ValueError('save UI pinned charmap preimage')
    rom = ndspy.rom.NintendoDSRom(data)
    archive = ndspy.narc.NARC(rom.getFileByName('a/0/2/7'))
    if sha(archive.files[40]) != BANK_SHA[language]:
        raise ValueError('save UI bank40 language/preimage')
    guards = json.loads((ROOT / 'features/save-ui/native-guards.json').read_text())
    off9, ram9 = struct.unpack_from('<I', data, 0x20)[0], struct.unpack_from('<I', data, 0x28)[0]
    for address, guard in guards['arm9'].items():
        offset = off9 + int(address, 16) - ram9
        if sha(data[offset:offset + guard['size']]) != guard['sha256']:
            raise ValueError('save UI native ARM9 ABI preimage ' + address)
    from sgp12.rom import Rom
    record, _, overlay = Rom(data).immagine_overlay(1)
    for address, guard in guards['overlay1'].items():
        offset = int(address, 16) - record['ram']
        if sha(overlay[offset:offset + guard['size']]) != guard['sha256']:
            raise ValueError('save UI native Field ABI preimage ' + address)
    return rom, archive


def _encoded(charmap_path):
    encoder = module(ROOT / 'features/options/tools/codifica_testo.py', 'save_ui_encoder')
    table, _ = encoder.carica_charmap(charmap_path)
    return {lang: encoder.codifica(text, table) for lang, text in TEXT.items()}


def _slot(data, record):
    fat = struct.unpack_from('<I', data, 0x48)[0]
    entry = fat + 8 * record['file_id']
    start, end = struct.unpack_from('<II', data, entry)
    entries = [struct.unpack_from('<II', data, fat + i * 8)
               for i in range(struct.unpack_from('<I', data, 0x4c)[0] // 8)]
    next_start = min(a for a, b in entries if a > start)
    if end - start != 1544 or next_start - start != 2048:
        raise ValueError('save UI original overlay storage bounds')
    if sha(data[start:end]) != COMPRESSED_SHA or data[end:next_start] != bytes(504):
        raise ValueError('save UI original overlay/padding preimage')
    return entry, start, end, next_start


def apply(data, language, charmap_path):
    """Return (new ROM bytes, receipt); input is a verified pre-save-UI stage."""
    from sgp12.rom import Rom
    from sgp12.blz import blz_comprimi_ottimo, blz_decomprimi
    from sgp13.resources import append_file
    rom, archive = _identity(data, language, charmap_path)
    view = Rom(data)
    record, _, before = view.immagine_overlay(30)
    if (record['id'], record['file_id'], record['ram'], record['ram_size'], record['bss_size'],
        record['static_init_start'], record['static_init_end'], record['flag']) != (
            30, 30, 0x0225d520, 1984, 0, 0x0225dc80, 0x0225dc84, 1):
        raise ValueError('save UI overlay30 load preimage')
    entry, start, old_end, slot_end = _slot(data, record)
    with tempfile.TemporaryDirectory(prefix='sgp-save-ui-') as temp:
        blob, symbols = compile_native(temp)
    after = patch_overlay(bytes(before), blob, symbols)
    compressed = blz_comprimi_ottimo(after)
    if isinstance(compressed, tuple):
        compressed = compressed[0]
    if len(compressed) > 2048 or blz_decomprimi(compressed) != after:
        raise ValueError('save UI in-place BLZ bound/roundtrip')
    result = bytearray(data)
    result[start:start + len(compressed)] = compressed
    struct.pack_into('<II', result, entry, start, start + len(compressed))
    struct.pack_into('<I', result, record['offset_voce'] + 8, len(after))
    struct.pack_into('<I', result, record['offset_voce'] + 28,
                     (record['parola_comp'] & 0xff000000) | len(compressed))
    archive.files[40] = append_message(archive.files[40], _encoded(charmap_path)[language])
    result = append_file(bytes(result), rom.filenames.idOf('a/0/2/7'), archive.save())
    report = readback(data, result, language, charmap_path)
    report.update(input_sha256=sha(data), output_sha256=sha(result), symbols=symbols,
                  code_sha256=sha(blob), code_bytes=len(blob),
                  overlay_storage_start=start, overlay_storage_end=start + len(compressed),
                  overlay_slot_end=slot_end)
    return result, report


def readback(before, after, language, charmap_path):
    """Independently decode container, overlay and message preservation contracts.

    This rejects code mutations by comparing a fresh compilation, not by trusting
    an apply receipt. It also checks original-byte invariance separately.
    """
    import ndspy.rom
    import ndspy.narc
    import ndspy.codeCompression
    from sgp12.rom import Rom
    original, old_archive = _identity(before, language, charmap_path)
    updated = ndspy.rom.NintendoDSRom(after)
    old_rec, _, old_image = Rom(before).immagine_overlay(30)
    new_rec, _, native_image = Rom(after).immagine_overlay(30)
    if tuple(old_rec[key] for key in ('id', 'file_id', 'ram', 'ram_size', 'bss_size',
                                     'static_init_start', 'static_init_end', 'flag')) != (
            30, 30, 0x0225d520, 1984, 0, 0x0225dc80, 0x0225dc84, 1):
        raise ValueError('save UI readback original overlay load preimage')
    _slot(before, old_rec)
    if sha(bytes(old_image)) != OVERLAY_SHA:
        raise ValueError('save UI readback original overlay preimage')
    image = ndspy.codeCompression.decompress(updated.files[30])
    if bytes(native_image) != image:
        raise ValueError('save UI readback independent BLZ decoder mismatch')
    with tempfile.TemporaryDirectory(prefix='sgp-save-ui-readback-') as temp:
        blob, symbols = compile_native(temp)
    if not 1992 <= len(image) <= 2496 or len(image) % 32:
        raise ValueError('save UI readback overlay bounds')
    old_prefix = bytearray(image[:1984])
    old_prefix[0x7b0:0x7b4] = bytes(old_image)[0x7b0:0x7b4]
    if bytes(old_prefix) != bytes(old_image):
        raise ValueError('save UI readback original-byte preservation')
    if struct.unpack_from('<I', image, 0x7b0)[0] != symbols['sgp_saveui_save']:
        raise ValueError('save UI readback result handler pointer')
    if struct.unpack_from('<II', image, 1984) != (symbols['sgp_saveui_failure'], symbols['sgp_saveui_ack']):
        raise ValueError('save UI readback failure state pointers')
    if image[1992:1992 + len(blob)] != blob or any(image[1992 + len(blob):]):
        raise ValueError('save UI readback compiled branch/state/message/cleanup')
    for key in ('id', 'ram', 'bss_size', 'static_init_start', 'static_init_end', 'file_id', 'flag'):
        if old_rec[key] != new_rec[key]:
            raise ValueError('save UI readback overlay metadata ' + key)
    if new_rec['ram_size'] != len(image) or new_rec['dim_compressa'] != len(updated.files[30]) or len(updated.files[30]) > 2048:
        raise ValueError('save UI readback overlay storage/load size')
    # Growth must not add a conflict with another overlay's dynamic RAM range.
    view = Rom(before)
    for oid in range(view.n_overlay):
        if oid == 30:
            continue
        other = view.voce_overlay(oid)
        start, end = other['ram'], other['ram'] + other['ram_size'] + other['bss_size']
        old_overlap = start < old_rec['ram'] + 1984 and end > old_rec['ram']
        new_overlap = start < new_rec['ram'] + len(image) and end > new_rec['ram']
        if new_overlap and not old_overlap:
            raise ValueError('save UI readback new overlay overlap')
    archive = ndspy.narc.NARC(updated.getFileByName('a/0/2/7'))
    if len(archive.files) != len(old_archive.files) or any(
            a != b for i, (a, b) in enumerate(zip(old_archive.files, archive.files)) if i != 40):
        raise ValueError('save UI readback unrelated message members')
    reader = module(ROOT / 'quality-audit/hgss_text.py', 'save_ui_message_reader')
    old_words = reader.read_bank_raw(old_archive.files[40])
    words = reader.read_bank_raw(archive.files[40])
    if (struct.unpack_from('<H', archive.files[40], 2)[0] != 53262 or
            len(words) != 118 or words[:117] != old_words or words[117] != _encoded(charmap_path)[language]):
        raise ValueError('save UI readback message117/preservation')
    chars, commands = reader.load_charmap(charmap_path)
    decoded = reader.render(words[117], chars, commands)
    if (decoded['unknown_codes'] or decoded['malformed_controls'] or decoded['controls'] or
            decoded['text'] != TEXT[language].replace('\n', '\\n')):
        raise ValueError('save UI readback localized message decoding')
    fids = [30, original.filenames.idOf('a/0/2/7')]
    if len(original.files) != len(updated.files) or any(
            a != b for i, (a, b) in enumerate(zip(original.files, updated.files)) if i not in fids):
        raise ValueError('save UI readback unrelated files')
    if (original.arm9, original.arm7, original.iconBanner, original.arm7OverlayTable) != (
            updated.arm9, updated.arm7, updated.iconBanner, updated.arm7OverlayTable):
        raise ValueError('save UI readback native executables')
    # Compare every original cartridge byte, normalizing only documented
    # metadata and the installed compressed body. This also protects other y9
    # entries, unindexed bytes and unused slot tail.
    normalized = bytearray(after[:len(before)])
    fat = struct.unpack_from('<I', before, 0x48)[0]
    overlay_start = struct.unpack_from('<I', before, fat + 30 * 8)[0]
    allowed = [(0x14, 1), (0x80, 4), (0x15e, 2),
               (fat + 30 * 8 + 4, 4), (old_rec['offset_voce'] + 8, 4),
               (old_rec['offset_voce'] + 28, 4),
               (overlay_start, len(updated.files[30])),
               (fat + fids[1] * 8, 8)]
    for offset, size in allowed:
        normalized[offset:offset + size] = before[offset:offset + size]
    if normalized != before:
        raise ValueError('save UI readback unrelated cartridge bytes')
    new_start, new_end = struct.unpack_from('<II', after, fat + fids[1] * 8)
    if new_start != ((len(before) + 511) & ~511) or new_end != len(after):
        raise ValueError('save UI readback appended archive bounds')
    if after[len(before):new_start] != b'\xff' * (new_start - len(before)):
        raise ValueError('save UI readback appended alignment')
    from sgp12.rom import crc16
    capacity = before[0x14]
    while len(after) > (0x20000 << capacity):
        capacity += 1
    if (after[0x14] != capacity or struct.unpack_from('<I', after, 0x80)[0] != len(after) or
            struct.unpack_from('<H', after, 0x15e)[0] != crc16(after[:0x15e])):
        raise ValueError('save UI readback cartridge header')
    widths = module(ROOT / 'quality-audit/misura_larghezza.py', 'save_ui_widths')
    fonts = ndspy.narc.NARC(original.getFileByName('a/0/1/6'))
    metric = widths.extract_width_table(fonts.files[1])
    measured = widths.measure(metric, words[117], limit_px=216)
    if measured['any_unknown_glyph'] or measured['any_over_limit'] or len(measured['lines']) != 2:
        raise ValueError('save UI text exceeds native font1 window')
    return dict(overlay_raw_bytes=len(image), overlay_appended_bytes=len(image) - 1984,
                overlay_compressed_bytes=len(updated.files[30]), overlay_sha256=sha(image),
                overlay_compressed_sha256=sha(updated.files[30]),
                overlay_table_sha256=sha(after[new_rec['offset_voce']:new_rec['offset_voce'] + 32]),
                message_id=117, message_count=118, message_widths=[r['width_px'] for r in measured['lines']],
                message_bank_sha256=sha(archive.files[40]), changed_file_ids=fids)
