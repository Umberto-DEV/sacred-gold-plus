"""Declared member deltas for NitroFS archives that the UI stage appends exactly once.

Why this exists. The UI stage seeds `crc32(y9)`, the ROM length and the FAT positions of files
54 and 156 into resident ARM9 words that the runtime compares with the cartridge (module.c,
guide_resource.c) and appends its own copy of the Guide archive `a/0/2/7` (file 156). A stage
that appends a *second* copy of an archive after the UI (a text or script writer run after it)
moves FAT 156, changes the ROM length and orphans the UI copy.

The mechanical stages therefore stay what they already are, producers, but their archive
effect is expressed as an `ArchiveDelta`: the members they replace, each bound to the SHA-256
of the member in the exact V4 and to the replacement bytes. The UI stage applies all deltas
to the V4 archives it already rewrites (156) or appends once (every other archive), writes the
seeds once, and `ui_verify` replays the declaration with an independent parser. Nothing here
writes a cartridge; the module is pure and works on bytes in memory.

Several producers may act on one archive (keen-eye text lives in a/0/2/7, the gift script fixes
(`gifts-scripts`: ribbon repairs and the Eevee party guard) in a/0/1/2). Each member row carries its producer; `normalize`
merges deltas of one archive when their member sets are disjoint and refuses any overlap, so the order of
independent producers cannot change the result.

Trust. A delta is not trusted because a producer says so: the verifier checks (1) the before
hash of every member against the V4, (2) the after bytes against the declared hash, (3) that no
other member and no padding byte changed, (4) the semantic checker registered in `CHECKERS` for the
producer of each member (default deny, hostile inputs end as ValueError), and (5) for a receipt replay, that
re-running every named producer on the V4 yields exactly the recorded, merged record (`rederive`).
"""
from dataclasses import dataclass
from collections import namedtuple
import functools
import hashlib
import importlib.util
import json
import re
import struct
from pathlib import Path

from ndspy.narc import NARC

from . import ui_resource_verify

SCHEMA = 2
SOURCE = Path(__file__).resolve().parents[1]
# Default deny: only archives whose owners and consumers were reviewed may be declared.
ALLOWED_ARCHIVES = ('a/0/0/1', 'a/0/2/7', 'a/0/1/2', 'a/0/3/0',
                    'a/0/3/2', 'a/0/3/4', 'a/0/3/7')
UI_FILES = (27, 54, 156, 167)
GUIDE_FILE = 156
# Message banks ui_compile/guide_content read at compile time (item, pokemon, map, move names): the Guide copies
# them, so a declared change there would leave it stale. Refused until the Guide is built from the delta.
GUIDE_SOURCE_MEMBERS = (222, 237, 279, 750)
# guide_content.SCRIPT_PINS audits these a/0/1/2 script members at compile time (preimage hashes): a declared change
# would invalidate the Guide's audit, so it is refused until the pins are re-derived from the delta.
GUIDE_SCRIPT_MEMBERS = (131, 132, 152, 196, 890)
SCRIPTS_FILE_NAME = 'a/0/1/2'
MAX_MEMBER_BYTES = 1 << 20
PRODUCER_NAME = re.compile(r'[a-z0-9][a-z0-9-]{0,63}')
# Whole member 722 per language (retail bank with only row 51 replaced): pinned so that bytes after the last row,
# padding or any other slack cannot ride along with a row-correct bank. Re-derive from text.apply when text.py changes.
KEEN_EYE_MEMBER_SHA256 = {'EN': 'fa9a207b90c820fe8e3efbe968d50173ef2ac559985b4f7d10a5f374208bdb1e',
                          'IT': '6ad68cad754f4b7174cf6556d40330150c34ad5d18354c2e110c5d4b939ade1f'}
TEXT_SOURCE = ('features/modern-accuracy/text.py',
               'ba4391c28bcf11e80c864fbb8b71e73be6b7791cbbe398bad48b19c0736153fc')


def _need(ok, reason):
    if not ok:
        raise ValueError(reason)


def sha256(value):
    return hashlib.sha256(value).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


# ------------------------------------------------------------------ independent archive reading

def _geometry(raw):
    """(spans relative to the member image, names block, member image, image offset in the file)."""
    return ui_resource_verify._archive(raw)


def _check_layout(spans, image):
    """Canonical ndspy layout: members contiguous after 4 byte alignment, zero padding, no tail."""
    cursor = 0
    for index, (start, end) in enumerate(spans):
        aligned = (cursor + 3) & ~3
        _need(start == aligned and image[cursor:aligned] == bytes(aligned - cursor),
              'archive member %d is not at the canonical aligned offset' % index)
        cursor = end
    aligned = (cursor + 3) & ~3
    _need(len(image) == aligned and image[cursor:] == bytes(aligned - cursor), 'archive tail/padding')


def members(raw):
    spans, _, image, _ = _geometry(bytes(raw))
    _check_layout(spans, image)
    return [bytes(image[a:b]) for a, b in spans]


# ----------------------------------------------------------------------------------- the delta

Member = namedtuple('Member', 'index before_sha256 after producer')


@dataclass(frozen=True)
class ArchiveDelta:
    archive: str
    file_id: int
    members: tuple          # sorted Member rows (index, before sha256 in the V4, replacement bytes, producer)
    evidence: tuple = ()    # sorted (producer, key, hex digest) triples: provenance only, never authority

    @classmethod
    def make(cls, archive, file_id, producer, old_raw, replacements, evidence=None):
        _need(isinstance(archive, str) and archive and type(file_id) is int and 0 <= file_id < 513, 'delta identity')
        _need(isinstance(producer, str) and PRODUCER_NAME.fullmatch(producer), 'producer name')
        _need(isinstance(replacements, dict) and replacements, 'a delta declares at least one member')
        old = members(old_raw)
        rows = []
        for index in sorted(replacements, key=lambda k: (type(k) is not int, k)):
            after = replacements[index]
            _need(type(index) is int and 0 <= index < len(old), 'member index outside the archive')
            _need(type(after) is bytes and 0 < len(after) <= MAX_MEMBER_BYTES, 'member payload size/type')
            _need(after != old[index], 'declared member is unchanged')
            rows.append(Member(index, sha256(old[index]), after, producer))
        pairs = tuple(sorted((producer, str(k), str(v)) for k, v in (evidence or {}).items()))
        return cls(archive, file_id, tuple(rows), pairs)

    def replacements(self):
        return {m.index: m.after for m in self.members}

    def producers(self):
        return sorted({m.producer for m in self.members})

    def total_after_bytes(self):
        return sum(len(m.after) for m in self.members)

    def record(self):
        evidence = {}
        for producer, key, value in self.evidence:
            evidence.setdefault(producer, {})[key] = value
        return {'schema': SCHEMA, 'archive': self.archive, 'file_id': self.file_id, 'producers': self.producers(),
                'members': [{'index': m.index, 'before_sha256': m.before_sha256, 'after_sha256': sha256(m.after),
                             'after_bytes': len(m.after), 'producer': m.producer} for m in self.members],
                'evidence': evidence}

    def sha256(self):
        return sha256(canonical(self.record()))


def _merge(a, b):
    _need(a.file_id == b.file_id and a.archive == b.archive, 'one file id, one archive name')
    seen = {m.index for m in a.members}
    _need(not seen & {m.index for m in b.members}, 'two producers declare the same archive member')
    _need(not set(a.producers()) & set(b.producers()), 'a producer declares an archive once')
    return ArchiveDelta(a.archive, a.file_id, tuple(sorted(a.members + b.members)),
                        tuple(sorted(a.evidence + b.evidence)))


def normalize(deltas):
    """Merge deltas of the same archive (disjoint members only) and order by file id: order-independent."""
    deltas = tuple(deltas)
    _need(all(isinstance(d, ArchiveDelta) for d in deltas), 'archive delta type')
    merged = {}
    for delta in deltas:
        merged[delta.file_id] = _merge(merged[delta.file_id], delta) if delta.file_id in merged else delta
    return tuple(merged[fid] for fid in sorted(merged))


def check_against(deltas, resolve, file):
    """Bind each delta to the exact V4 cartridge: allowed name, file id, before hashes, UI member."""
    for delta in normalize(deltas):
        _need(delta.archive in ALLOWED_ARCHIVES, 'archive not allowed for declared deltas: ' + delta.archive)
        _need(resolve(delta.archive) == delta.file_id and delta.file_id not in set(UI_FILES) - {GUIDE_FILE},
              'delta file id differs from the cartridge name table')
        old = members(file(delta.file_id))
        for member in delta.members:
            _need(type(member) is Member and type(member.index) is int and 0 <= member.index < len(old)
                  and sha256(old[member.index]) == member.before_sha256, 'delta before-hash differs from the V4 member')
            _need(type(member.after) is bytes and 0 < len(member.after) <= MAX_MEMBER_BYTES
                  and sha256(member.after) != member.before_sha256, 'declared member is empty, oversized or unchanged')
        if delta.file_id == GUIDE_FILE:
            # The last member of a/0/2/7 (829 in the V4) is replaced by the UI stage itself.
            _need(all(m.index != len(old) - 1 for m in delta.members), 'the Guide member belongs to the UI stage')
            _need(not {m.index for m in delta.members} & set(GUIDE_SOURCE_MEMBERS),
                  'the Guide is built from these name banks: a delta there would leave it stale')
        if delta.archive == SCRIPTS_FILE_NAME:
            _need(not {m.index for m in delta.members} & set(GUIDE_SCRIPT_MEMBERS),
                  'the Guide audits these script members: a delta there would invalidate its pins')
    return normalize(deltas)


# ------------------------------------------------------------------------------ the writer side

def apply_members(raw, replacements):
    """Replace members, retaining the exact original name block.

    Some pinned V4 archives use an older empty-name encoding which ndspy
    normalizes by four bytes. Only those complete pinned inputs may use this
    exception; malformed padding and all other noncanonical inputs stay refused.
    """
    raw = bytes(raw)
    if not replacements:
        return raw
    archive = NARC(raw)
    original_names = None
    if archive.save() != raw:
        _need(sha256(raw) in {
                  'a66f72f48341a1ec3131b521641ab6e671ad890d07676131b00fed2704ec3d4d',
                  'fad0200a3e7e56c0bf3a4ce4487937de16598cc4ba71b3741d8741bc3b890322',
                  '4bdd8f93da7831add2db84671be9cc4c5d3ab2f981c391f3f84ad4b451cc08aa',
                  'a26d5906856068e60e16ac0e311852ac5f9b48d5e7cde43cdca69f1a72207382',
              },
              'archive is not in the canonical layout: refusing to rewrite it')
        spans, original_names, image, _ = _geometry(raw)
        _check_layout(spans, image)
        _need(original_names == bytes.fromhex('42544e46100000000400000000000100'),
              'pinned archive name block differs')
    old = [bytes(m) for m in archive.files]
    for index, after in replacements.items():
        _need(type(index) is int and 0 <= index < len(old) and type(after) is bytes and after, 'replacement member')
        archive.files[index] = after
    out = archive.save()
    if original_names is not None:
        _, normalized_names, _, image_at = _geometry(out)
        names_at = image_at - 8 - len(normalized_names)
        out = out[:names_at] + original_names + out[names_at + len(normalized_names):]
        out = out[:8] + struct.pack('<I', len(out)) + out[12:]
        _need(_geometry(out)[1] == original_names, 'archive name block preservation')
    expected = [replacements.get(i, m) for i, m in enumerate(old)]
    _need(members(out) == expected, 'archive read-back after member replacement')
    return out


# ----------------------------------------------------------------------- the independent reader

def verify_members(old_raw, new_raw, replacements):
    """Independent traversal: only the declared members differ, canonical layout, same name table."""
    old_spans, old_names, old_image, _ = _geometry(bytes(old_raw))
    new_spans, new_names, new_image, _ = _geometry(bytes(new_raw))
    _need(len(old_spans) == len(new_spans) and old_names == new_names, 'archive member count/name table')
    _check_layout(old_spans, old_image)
    _check_layout(new_spans, new_image)
    _need(all(type(i) is int and 0 <= i < len(old_spans) for i in replacements), 'declared member index')
    changed = []
    for index, ((a, b), (c, d)) in enumerate(zip(old_spans, new_spans)):
        before, after = old_image[a:b], new_image[c:d]
        expected = replacements.get(index, before)
        _need(after == expected, 'archive member %d differs from its declaration' % index)
        if after != before:
            changed.append(index)
    _need(changed == sorted(replacements), 'declared member left unchanged')
    return {'members': len(old_spans), 'changed': changed}


# ----------------------------------------------------------------------- producer checkers

def _text_module():
    relative, digest = TEXT_SOURCE
    path = SOURCE / relative
    _need(path.is_file() and sha256(path.read_bytes()) == digest, 'Keen Eye text source differs from its pin')
    spec = importlib.util.spec_from_file_location('sgp131_archives_keen_eye_text', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_FOREIGN = (TypeError, IndexError, KeyError, struct.error, OverflowError, AttributeError, UnicodeError, MemoryError)


def _guarded(function):
    """A checker fed hostile bytes/types ends as ValueError, never as the library's own exception."""
    @functools.wraps(function)
    def wrapper(*args):
        try:
            return function(*args)
        except _FOREIGN as error:
            raise ValueError('semantic checker refused hostile input: ' + type(error).__name__) from None
    return wrapper


@_guarded
def _keen_eye_text(index, before, after, language):
    """Member level restatement of text.verify, plus the whole member pinned by hash per language."""
    text = _text_module()
    _need(type(language) is str and language in text.DESCRIPTIONS and type(index) is int and index == text.BANK,
          'Keen Eye member/language')
    _need(type(before) is bytes and type(after) is bytes and len(before) >= 4 and len(after) >= 4, 'Keen Eye member bytes')
    _need(struct.unpack_from('<HH', before) == struct.unpack_from('<HH', after) and
          struct.unpack_from('<H', after)[0] == text.ROWS, 'bank row count or key changed')
    for row in range(text.ROWS):
        if row != text.ROW:
            _need(text.decode_row(before, row) == text.decode_row(after, row), 'row %d changed' % row)
    old_row, new_row = text.decode_row(before, text.ROW), text.decode_row(after, text.ROW)
    _need(text.row_sha256(old_row) == text.PREIMAGE_SHA256[language], 'row 51 is not the retail row')
    _need(text.row_sha256(new_row) == text.NEW_SHA256[language] and old_row != new_row,
          'row 51 is not the pinned new row')
    _need(sha256(after) == KEEN_EYE_MEMBER_SHA256[language], 'member 722 is not the pinned bank (trailing or foreign bytes)')


CHECKERS = {'keen-eye-text': _keen_eye_text}


def check_semantics(delta, old_raw, new_raw, language):
    register_owner_producers()
    old, new = members(old_raw), members(new_raw)
    for member in delta.members:
        checker = CHECKERS.get(member.producer)
        _need(checker is not None, 'no semantic checker registered for producer ' + str(member.producer))
        try:
            checker(member.index, old[member.index], new[member.index], language)
        except ValueError:
            raise
        except _FOREIGN as error:
            raise ValueError('semantic checker refused hostile input: ' + type(error).__name__) from None


# ------------------------------------------------------------------------------ the producers

def _jsonable(value):
    def default(item):
        if isinstance(item, (bytes, bytearray)):
            return bytes(item).hex()
        if isinstance(item, (set, frozenset)):
            return sorted(item)
        raise TypeError('receipt value is not JSON serialisable')
    return json.loads(json.dumps(value, default=default, allow_nan=False))


def derive(base, language, producer, archive, apply, verify):
    """Run an owner stage on the pristine V4 with its own writer and reader; keep only its archive effect."""
    from ndspy.rom import NintendoDSRom
    image, raw = apply(base, language)
    receipt = _jsonable(raw)
    verify(base, image, receipt)
    old_rom, new_rom = NintendoDSRom(bytes(base)), NintendoDSRom(bytes(image))
    fid = old_rom.filenames.idOf(archive)
    _need(new_rom.filenames.idOf(archive) == fid and len(old_rom.files) == len(new_rom.files), 'owner file table')
    for index, (a, b) in enumerate(zip(old_rom.files, new_rom.files)):
        _need(index == fid or a == b, 'owner stage changed file %d' % index)
    old, new = members(old_rom.files[fid]), members(new_rom.files[fid])
    _need(len(old) == len(new), 'owner stage changed the member count')
    changed = {i: n for i, (o, n) in enumerate(zip(old, new)) if o != n}
    return ArchiveDelta.make(archive, fid, producer, old_rom.files[fid], changed, evidence={
        'owner_input_sha256': sha256(base), 'owner_output_sha256': sha256(image),
        'owner_receipt_sha256': sha256(canonical(receipt))})


def derive_keen_eye(base, language, charmap):
    text = _text_module()
    return derive(base, language, 'keen-eye-text', text.ARCHIVE,
                  lambda data, lang: text.apply(data, lang, charmap),
                  lambda before, after, receipt: text.verify(before, after, receipt, charmap_path=charmap))


PRODUCERS = {'keen-eye-text': derive_keen_eye}
_OWNER_MODULES = ('gifts_archives', 'legacy_archives', 'safari_archives',
                  'legendary_archives', 'evolution_fixes',
                  'fishing', 'pursuit_script', 'status_icon_script',
                  'pressure_switch_scripts', 'gs_cup_guard',
                  'uturn_script')  # fixed owners exporting PRODUCERS/CHECKERS


def register_owner_producers():
    """Register the producers and checkers delivered by owner modules, once.

    Deferred because those modules import this one: registering at import time would break whichever
    side is imported first. A name already bound to a different callable is a refusal, not an override.
    """
    import importlib
    for name in _OWNER_MODULES:
        module = importlib.import_module(__package__ + '.' + name)
        for table, extra in ((PRODUCERS, module.PRODUCERS), (CHECKERS, module.CHECKERS)):
            for key, value in extra.items():
                _need(table.setdefault(key, value) is value, 'archive producer registered twice: ' + key)


RECORD_KEYS = {'schema', 'archive', 'file_id', 'producers', 'members', 'evidence'}


def rederive(base, language, charmap, records):
    """Replay a receipt: every producer it names re-runs on the V4; the merged result must equal the records."""
    _need(isinstance(records, list), 'recorded archive deltas must be a list')
    register_owner_producers()
    producers = []
    for record in records:
        _need(type(record) is dict and set(record) == RECORD_KEYS and type(record['schema']) is int
              and record['schema'] == SCHEMA, 'recorded archive delta shape')
        names = record['producers']
        _need(type(names) is list and names and all(type(n) is str and n in PRODUCERS for n in names),
              'no registered producer for the recorded delta')
        producers.extend(names)
    _need(len(set(producers)) == len(producers), 'a producer is recorded once')
    produced = []
    for name in producers:
        delta = PRODUCERS[name](base, language, charmap)
        _need(isinstance(delta, ArchiveDelta) and delta.producers() == [name], 'producer output for ' + name)
        produced.append(delta)
    merged = normalize(produced)
    _need([d.record() for d in merged] == records, 'recorded delta differs from the producers re-run on the V4')
    return merged


def from_cartridge(data):
    """(resolve, file) views of a cartridge for `check_against`."""
    from ndspy import fnt
    data = bytes(data)
    fnt_at, fnt_size, fat, fat_size = struct.unpack_from('<4I', data, 0x40)
    names = fnt.load(data[fnt_at:fnt_at + fnt_size])

    def file(fid):
        start, end = struct.unpack_from('<II', data, fat + 8 * fid)
        return data[start:end]
    return names.idOf, file
