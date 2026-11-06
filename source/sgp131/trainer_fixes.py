"""Guarded in-place repairs for trainer parties and their constructor.

SG-TR02 is a data/order mismatch.  Overlay 26 deliberately selects Wade's
``_3`` record (461) before ``_2`` (460).  Retail data rises across that order,
but Sacred Gold assigned level 52 to 461 and level 46 to 460.  Swapping the
two equal-sized party members restores 46 -> 52 -> 68 without changing the
selector, archive geometry, trainer headers, or any other trainer.

HG-B16 and SG-TR04 are constructor ordering defects shared by all four trainer
formats.  The game stores ``MON_DATA_FORM`` and then calls the common
Frustration helper, but never refreshes the party stats (HG-B16) or ability
(SG-TR04) for that form.  The reviewed replacement keeps the helper's exact
50-byte extent, calls
``UpdateMonAbility`` and ``CalcMonStats``, then preserves the Frustration
friendship rule through the native ``MonHasMove`` helper.  Its four incoming
calls and the four immediately preceding form setters remain unchanged.
"""
import hashlib
import struct

from sgp12.rom import Arm9, bl_decode


ARCHIVE = 'a/0/5/6'
ARCHIVE_SHA256 = '2cef901a8a5be153c62a40de47792776265bc91a90d6c52e565b1303d1865586'
ARCHIVE_AFTER_SHA256 = '964a3efd40d83ecb196035f257264ba0e76a55818ed0d13aadde15b890451da9'
MEMBERS = (460, 461)
CONTROL_MEMBER = 512
MEMBER_SHA256 = {
    460: 'b683829bc7aa1485ff67d6ca5ceaac21ec0330972ec6a112ab060b5b95711f20',
    461: 'f3c99029821cca06a916c90a06dfb13428eb4259d44723294ad4caf9e571cc4f',
    512: 'f3aab6bc0065e076a34674886d297aa794b5f0c9ba246fb46fe9d1b774d2d060',
}
EXPECTED = {
    460: ((168, 46), (166, 46), (284, 46), (291, 46)),
    461: ((168, 52), (166, 52), (284, 52), (291, 52)),
    512: ((168, 68), (166, 68), (284, 68), (291, 68)),
}
LANGUAGES = ('EN', 'IT')
FORM_STATS_HELPER = 0x02073AE4
FORM_STATS_BYTES = 0x32
CALC_MON_STATS = 0x0206E250
UPDATE_MON_ABILITY = 0x020722D4
MON_HAS_MOVE = 0x02071754
SET_MON_DATA = 0x0206EC40
FORM_SETTERS = (0x02073736, 0x02073840, 0x02073936, 0x02073A54)
FRIENDSHIP_CALLERS = (0x0207373C, 0x02073846, 0x0207393C, 0x02073A5A)
FORM_STATS_BEFORE = bytes.fromhex(
    'f8b5051c0024ff2000af3870261c211c281c36310022faf721fdda2800d13e70'
    '641c042cf3db281c092100aafbf796f8f8bd'
)
FORM_STATS_AFTER = bytes.fromhex(
    '38b5041cfef7f4fb201cfaf7affb201cda21fdf72dfe002801d0002000e0ff20'
    '0090201c092100aafbf798f838bdc046c046'
)


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _need(condition, message):
    if not condition:
        raise ValueError(message)


def _layout(raw):
    """Return (data offset, member spans) from the exact NARC container."""
    raw = bytes(raw)
    _need(len(raw) >= 0x30 and raw[:4] == b'NARC'
          and raw[4:6] in (b'\xfe\xff', b'\xff\xfe'), 'trainer party file is not NARC')
    size, header_size, blocks = struct.unpack_from('<IHH', raw, 8)
    _need(size == len(raw) and header_size == 0x10 and blocks == 3,
          'trainer party NARC header differs')
    magic, btaf_size, count = struct.unpack_from('<4sII', raw, 0x10)
    _need(magic == b'BTAF' and count > CONTROL_MEMBER
          and btaf_size == 12 + count * 8 and 0x10 + btaf_size <= len(raw),
          'trainer party allocation table differs')
    btnf = 0x10 + btaf_size
    _need(raw[btnf:btnf + 4] == b'BTNF' and btnf + 8 <= len(raw),
          'trainer party name block is absent')
    btnf_size = struct.unpack_from('<I', raw, btnf + 4)[0]
    gmif = btnf + btnf_size
    _need(btnf_size >= 8 and gmif + 8 <= len(raw) and raw[gmif:gmif + 4] == b'GMIF',
          'trainer party data block is absent')
    gmif_size = struct.unpack_from('<I', raw, gmif + 4)[0]
    data = gmif + 8
    _need(gmif + gmif_size == len(raw), 'trainer party data block size differs')
    spans = []
    previous_end = 0
    for index in range(count):
        start, end = struct.unpack_from('<II', raw, 0x1C + index * 8)
        _need(previous_end <= start <= end <= len(raw) - data,
              'trainer party member geometry differs at %d' % index)
        spans.append((data + start, data + end))
        previous_end = end
    return data, spans


def _party(member):
    member = bytes(member)
    _need(len(member) == 32, 'Wade party member must contain four default-moves records')
    return tuple((struct.unpack_from('<H', member, offset + 4)[0] & 0x3FF,
                  struct.unpack_from('<H', member, offset + 2)[0])
                 for offset in range(0, len(member), 8))


def patch_archive(raw, *, archive_sha256=ARCHIVE_SHA256):
    """Swap Wade members 460/461 in place; never normalize the NARC."""
    raw = bytes(raw)
    _, spans = _layout(raw)
    _need(_sha(raw) == archive_sha256, 'trainer party archive differs from the pinned build')
    before = {}
    for index in (*MEMBERS, CONTROL_MEMBER):
        start, end = spans[index]
        before[index] = raw[start:end]
        _need(_sha(before[index]) == MEMBER_SHA256[index],
              'trainer party member %d differs from the pinned build' % index)
        _need(_party(before[index]) == EXPECTED[index],
              'trainer party member %d semantic preimage differs' % index)
    _need(len(before[460]) == len(before[461]), 'Wade party members are not equal-sized')
    result = bytearray(raw)
    a0, a1 = spans[460]
    b0, b1 = spans[461]
    result[a0:a1], result[b0:b1] = before[461], before[460]
    result = bytes(result)
    _need(_sha(result) == ARCHIVE_AFTER_SHA256,
          'Wade repair does not match the reviewed trainer archive')
    _, after_spans = _layout(result)
    _need(spans == after_spans, 'trainer party archive geometry changed')
    details = {
        'changed_members': [460, 461],
        'member_spans': {'460': list(spans[460]), '461': list(spans[461])},
        'before': {str(i): {'sha256': _sha(before[i]), 'party': [list(x) for x in _party(before[i])]}
                   for i in (*MEMBERS, CONTROL_MEMBER)},
        'after': {
            '460': {'sha256': _sha(before[461]), 'party': [list(x) for x in _party(before[461])]},
            '461': {'sha256': _sha(before[460]), 'party': [list(x) for x in _party(before[460])]},
            '512': {'sha256': _sha(before[512]), 'party': [list(x) for x in _party(before[512])]},
        },
        'archive_sha256_before': _sha(raw),
        'archive_sha256_after': _sha(result),
    }
    return result, details


def _fat_slot(data, file_id):
    fat_offset, fat_length = struct.unpack_from('<II', data, 0x48)
    _need(type(file_id) is int and 0 <= 8 * file_id <= fat_length - 8,
          'trainer party file is outside the FAT')
    start, end = struct.unpack_from('<II', data, fat_offset + 8 * file_id)
    _need(0 <= start < end <= len(data), 'trainer party FAT slot differs')
    return start, end


def _patch_form_stats(data):
    """Install the exact-size post-form ability/stat refresh helper."""
    arm = Arm9.from_bytes(bytes(data))
    before = arm.leggi(FORM_STATS_HELPER, FORM_STATS_BYTES)
    _need(before == FORM_STATS_BEFORE, 'trainer form-stat helper differs from the pinned build')
    _need([bl_decode(site, arm.leggi(site, 4)) for site in FORM_SETTERS]
          == [SET_MON_DATA] * len(FORM_SETTERS),
          'trainer form setters no longer precede the shared helper')
    _need([bl_decode(site, arm.leggi(site, 4)) for site in FRIENDSHIP_CALLERS]
          == [FORM_STATS_HELPER] * len(FRIENDSHIP_CALLERS),
          'trainer friendship helper callers differ')
    _need(bl_decode(FORM_STATS_HELPER + 4, FORM_STATS_AFTER[4:8]) == UPDATE_MON_ABILITY,
          'trainer form replacement no longer calls UpdateMonAbility')
    _need(bl_decode(FORM_STATS_HELPER + 0xA, FORM_STATS_AFTER[0xA:0xE]) == CALC_MON_STATS,
          'trainer form-stat replacement no longer calls CalcMonStats')
    _need(bl_decode(FORM_STATS_HELPER + 0x12, FORM_STATS_AFTER[0x12:0x16]) == MON_HAS_MOVE,
          'trainer form replacement no longer checks Frustration')
    _need(bl_decode(FORM_STATS_HELPER + 0x28, FORM_STATS_AFTER[0x28:0x2C]) == SET_MON_DATA,
          'trainer form-stat replacement no longer writes friendship')
    arm.scrivi(FORM_STATS_HELPER, FORM_STATS_AFTER)
    result = bytes(arm.raw)
    return result, {
        'address': FORM_STATS_HELPER,
        'bytes': FORM_STATS_BYTES,
        'sha256_before': _sha(before),
        'sha256_after': _sha(FORM_STATS_AFTER),
        'update_mon_ability': UPDATE_MON_ABILITY,
        'calc_mon_stats': CALC_MON_STATS,
        'mon_has_move': MON_HAS_MOVE,
        'form_setters': list(FORM_SETTERS),
        'friendship_callers': list(FRIENDSHIP_CALLERS),
    }


def spans(data):
    """Physical ROM spans of Wade's records and the fixed-size helper."""
    import ndspy.rom
    rom = ndspy.rom.NintendoDSRom(bytes(data))
    file_id = rom.filenames.idOf(ARCHIVE)
    start, end = _fat_slot(data, file_id)
    _, members = _layout(bytes(data[start:end]))
    result = [(start + members[i][0], start + members[i][1], 'Wade trainer party %d' % i)
              for i in MEMBERS]
    arm = Arm9.from_bytes(bytes(data))
    helper = arm.off(FORM_STATS_HELPER, FORM_STATS_BYTES)
    result.append((helper, helper + FORM_STATS_BYTES, 'trainer alternate-form post-form helper'))
    return result


def apply(data, language):
    import ndspy.rom
    _need(language in LANGUAGES, 'unknown trainer-fixes language')
    data = bytes(data)
    rom = ndspy.rom.NintendoDSRom(data)
    file_id = rom.filenames.idOf(ARCHIVE)
    start, end = _fat_slot(data, file_id)
    patched, details = patch_archive(data[start:end])
    _need(len(patched) == end - start, 'trainer party archive changed size')
    result = data[:start] + patched + data[end:]
    result, form_stats = _patch_form_stats(result)
    receipt = {
        'stage': 'trainer-fixes',
        'language': language,
        'input_sha256': _sha(data),
        'output_sha256': _sha(result),
        'archive': ARCHIVE,
        'file_id': file_id,
        'rom_slot': [start, end],
        'form_stats': form_stats,
        **details,
    }
    receipt['verification'] = verify(data, result, receipt)
    return result, receipt


def _ranges(a, b):
    _need(len(a) == len(b), 'ROM size changed')
    found = []
    for index, (old, new) in enumerate(zip(a, b)):
        if old != new:
            if found and found[-1][1] == index:
                found[-1][1] = index + 1
            else:
                found.append([index, index + 1])
    return found


def verify(before, after, receipt):
    """Independent cartridge readback and confinement for the two-member swap."""
    import ndspy.narc
    import ndspy.rom
    before, after = bytes(before), bytes(after)
    _need(len(before) == len(after), 'trainer-fixes changed ROM size')
    old, new = ndspy.rom.NintendoDSRom(before), ndspy.rom.NintendoDSRom(after)
    file_id = old.filenames.idOf(ARCHIVE)
    _need(new.filenames.idOf(ARCHIVE) == file_id and len(old.files) == len(new.files),
          'trainer party file identity changed')
    start, end = _fat_slot(before, file_id)
    _need(_fat_slot(after, file_id) == (start, end), 'trainer party FAT slot changed')
    expected_archive, details = patch_archive(before[start:end])
    expected = before[:start] + expected_archive + before[end:]
    expected, form_stats = _patch_form_stats(expected)
    _need(after == expected, 'trainer repairs differ from the declared result')
    old_members = ndspy.narc.NARC(before[start:end]).files
    new_members = ndspy.narc.NARC(after[start:end]).files
    _need(len(old_members) == len(new_members), 'trainer party member count changed')
    changed_members = [i for i, (a, b) in enumerate(zip(old_members, new_members)) if a != b]
    _need(changed_members == [460, 461], 'trainer party members changed outside Wade')
    _need(bytes(new_members[461]) == bytes(old_members[460])
          and bytes(new_members[460]) == bytes(old_members[461]), 'Wade party swap readback differs')
    changed_files = [i for i, (a, b) in enumerate(zip(old.files, new.files)) if a != b]
    _need(changed_files == [file_id], 'NitroFS files changed outside the trainer party archive')
    allowed = [(s, e) for s, e, _ in spans(before)]
    differing = _ranges(before, after)
    _need(all(any(start_ <= a and b <= end_ for start_, end_ in allowed)
              for a, b in differing), 'ROM bytes changed outside Wade party members')
    _need(isinstance(receipt, dict) and receipt.get('stage') == 'trainer-fixes'
          and receipt.get('language') in LANGUAGES
          and receipt.get('input_sha256') == _sha(before)
          and receipt.get('output_sha256') == _sha(after)
          and receipt.get('archive') == ARCHIVE
          and receipt.get('file_id') == file_id
          and receipt.get('rom_slot') == [start, end]
          and receipt.get('archive_sha256_before') == details['archive_sha256_before']
          and receipt.get('archive_sha256_after') == details['archive_sha256_after']
          and receipt.get('form_stats') == form_stats,
          'trainer-fixes receipt differs from the cartridge')
    return {
        'changed_files': changed_files,
        'changed_members': changed_members,
        'changed_ranges': differing,
        'archive_sha256_before': details['archive_sha256_before'],
        'archive_sha256_after': details['archive_sha256_after'],
        'form_stats': form_stats,
    }
