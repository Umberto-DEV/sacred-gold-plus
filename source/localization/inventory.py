"""Identify exact retail donors and inventory presentation conflicts without text exports."""
import hashlib
import json
from pathlib import Path
import struct
import zlib

from ndspy.narc import NARC
from ndspy.rom import NintendoDSRom
from translation.message_codec import Bank, unpack_name

LANGUAGES = Path(__file__).with_name('languages.json')
MESSAGES = 'a/0/2/7'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def identify(data, contracts):
    digest = sha(data)
    matches = [locale for locale, row in contracts.items()
               if row['sha256'] == digest and row['bytes'] == len(data)]
    if len(matches) != 1:
        raise ValueError('unsupported retail identity')
    locale = matches[0]
    row = contracts[locale]
    if len(data) < 512 or data[12:16] != row['game_code'].encode() or data[30] != row['revision']:
        raise ValueError('retail header disagrees with identity')
    return locale


def crc16(data):
    value = 0xffff
    for byte in data:
        value ^= byte
        for _ in range(8):
            value = (value >> 1) ^ 0xa001 if value & 1 else value >> 1
    return value


def check_layout(data, *, check_crc=True):
    if len(data) < 512:
        raise ValueError('truncated NDS header')
    if check_crc and (crc16(data[:0x15e]) != struct.unpack_from('<H', data, 0x15e)[0]
                      or crc16(data[0xc0:0x15c]) != struct.unpack_from('<H', data, 0x15c)[0]):
        raise ValueError('NDS header/logo CRC')
    for offset in (0x20, 0x30):
        start, _, _, length = struct.unpack_from('<IIII', data, offset)
        if not 512 <= start < start + length <= len(data):
            raise ValueError('ARM image bounds')
    start, length = struct.unpack_from('<II', data, 0x48)
    if not length or length % 8 or not 512 <= start < start + length <= len(data):
        raise ValueError('FAT table bounds')
    extents = [struct.unpack_from('<II', data, offset)
               for offset in range(start, start + length, 8)]
    if any(not 0 <= a <= b <= len(data) for a, b in extents):
        raise ValueError('FAT member bounds')
    used = sorted((a, b) for a, b in extents if a < b)
    if any(b > c for (_, b), (c, _) in zip(used, used[1:])):
        raise ValueError('FAT member overlap')


def inspect_input(path):
    path = Path(path)
    if path.is_symlink() or not path.is_file():
        raise ValueError('retail input must be a regular file')
    data = path.read_bytes()
    contracts = {key: row['retail'] for key, row in json.loads(LANGUAGES.read_text())['languages'].items()}
    locale = identify(data, contracts)
    check_layout(data)
    rom = NintendoDSRom(data)
    archive = NARC(rom.getFileByName(MESSAGES))
    return dict(locale=locale, bytes=len(data), sha256=sha(data),
                sha1=hashlib.sha1(data).hexdigest(), crc32=f'{zlib.crc32(data):08X}',
                game_code=rom.idCode.decode(), revision=data[30],
                files=len(rom.files), message_banks=len(archive.files))


def message_action(core, original, donor):
    if original is not None and unpack_name(core) == unpack_name(original):
        if donor is None:
            raise ValueError('missing retail donor message')
        return 'retail'
    return 'authored'


def _member_rows(core, original, donor):
    if all(raw.startswith(b'NARC') for raw in (core, original, donor)):
        archives = [NARC(raw).files for raw in (core, original, donor)]
        if len({len(parts) for parts in archives}) == 1:
            return [dict(member=i, before_sha256=sha(c), retail_sha256=sha(d),
                         action='retail' if c == o else 'review')
                    for i, (c, o, d) in enumerate(zip(*archives)) if d != o]
        return [dict(member=None, before_sha256=sha(core), retail_sha256=sha(donor),
                     action='review', reason='archive member counts differ')]
    return [dict(member=None, before_sha256=sha(core), retail_sha256=sha(donor),
                 action='retail' if core == original else 'review')]


def inventory(core, retail):
    """Return hashes/IDs/actions only. No extracted game corpus enters source."""
    if 'EN' not in retail:
        raise ValueError('English retail reference required')
    parsed = {locale: NintendoDSRom(data) for locale, data in retail.items()}
    game = NintendoDSRom(core)
    original = parsed['EN']
    core_members = NARC(game.getFileByName(MESSAGES)).files
    # The historical Guide is an owned SGG1 resource appended to the text NARC.
    # It is rebuilt by the Guide compiler, never decoded/copied as a message bank.
    binary_members = [i for i, raw in enumerate(core_members) if raw.startswith(b'SGG1')]
    core_banks = [None if i in binary_members else Bank(raw).words
                  for i, raw in enumerate(core_members)]
    original_banks = [Bank(raw).words for raw in NARC(original.getFileByName(MESSAGES)).files]
    locales = {}
    for locale, donor in parsed.items():
        donor_banks = [Bank(raw).words for raw in NARC(donor.getFileByName(MESSAGES)).files]
        messages = []
        for bank, values in enumerate(core_banks):
            if values is None:
                continue
            old = original_banks[bank] if bank < len(original_banks) else []
            translated = donor_banks[bank] if bank < len(donor_banks) else []
            for index, words in enumerate(values):
                before = old[index] if index < len(old) else None
                target = translated[index] if index < len(translated) else None
                try:
                    action = message_action(words, before, target)
                except ValueError:
                    action = 'gap'
                if action != 'retail':
                    normalized = unpack_name(words)
                    digest = sha(struct.pack(f'<{len(normalized)}H', *normalized))
                    messages.append(dict(bank=bank, message=index, action=action, before_sha256=digest))
        resources = []
        for i, raw in enumerate(original.files):
            name = original.filenames.filenameOf(i)
            # Overlay executables have FAT IDs but no NitroFS filename. Their
            # native text needs explicit address/range review, not donor copying.
            if name is None or name == MESSAGES:
                continue
            other = donor.getFileByName(name)
            if raw != other:
                resources.append(dict(file=name, members=_member_rows(game.getFileByName(name), raw, other)))
        locales[locale] = dict(retail_sha256=sha(retail[locale]),
                               message_count=sum(len(bank) for bank in core_banks if bank is not None),
                               changed_messages=messages, resources=resources)
    return dict(schema=1, core_sha256=sha(core), binary_message_members=binary_members, locales=locales)
