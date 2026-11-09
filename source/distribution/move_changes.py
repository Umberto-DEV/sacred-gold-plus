"""Lossless, authenticated move-table comparisons for player reference guides.

No cartridge tables or text are embedded here. Read the caller's owned retail
image and exact released candidate in memory. The record schema and meanings
are attributed to pret/pokeheartgold at the immutable reference below; unknown
bits remain unknown. This audits move data, not every native battle-code fix.
"""
from __future__ import annotations

import copy
import hashlib
import struct

from ndspy.narc import NARC
from ndspy.rom import NintendoDSRom

from localization.messages import _TEXT
from translation.message_codec import Bank


LOCALES = ('EN', 'IT', 'FR', 'ES', 'DE')
ARCHIVE = 'a/0/1/1'
MESSAGE_ARCHIVE = 'a/0/2/7'
MEMBER_COUNT = 471
PLAYABLE_IDS = range(1, 468)
RECORD = struct.Struct('<H6BHb3BH')
FIELDS = ('effect', 'category', 'power', 'type', 'accuracy', 'pp',
          'effect_chance', 'target', 'priority', 'flags', 'contest_effect',
          'contest_type', 'reserved')
BATTLE_FIELDS = FIELDS[:10]
PRET_REVISION = '0985e8718df4f25e64d6507d89c0c97c0d288981'
PRET = 'https://github.com/pret/pokeheartgold/blob/' + PRET_REVISION + '/'
SOURCES = {
    'record_layout': PRET + 'include/move.h',
    'native_readers': PRET + 'src/move.c',
    'category_and_target': PRET + 'include/constants/moves.h',
    'effects': PRET + 'include/constants/move_effects.h',
    'flags': PRET + 'src/battle/battle_controller_player.c',
    'contact_flag': PRET + 'src/battle/overlay_12_0224E4FC.c',
    'will_o_wisp': 'source/sgp131/modern_moves.py',
    'fairy_type_9': 'source/sgp131/fairy_ai.py',
}

# These describe native effect selectors, not later-generation move defaults.
EFFECTS = {
    0: 'ordinary damaging hit',
    1: 'puts the target to sleep',
    3: 'restores HP equal to half the damage dealt',
    17: 'damaging hit that bypasses the ordinary accuracy/evasion check',
    18: 'lowers the target\'s Attack by one stage',
    23: 'lowers the target\'s accuracy by one stage',
    27: 'repeats the attack, then confuses the user',
    29: 'hits two to five times',
    30: 'changes the user\'s type to match one of its moves',
    31: 'damaging hit with a chance to make the target flinch',
    33: 'badly poisons the target',
    34: 'damaging hit that scatters prize money',
    42: 'damages and temporarily traps the target',
    43: 'damaging hit with an increased critical-hit ratio',
    45: 'damaging hit; the user takes crash damage if it misses',
    49: 'confuses the target',
    58: 'lowers the target\'s Attack by two stages',
    60: 'lowers the target\'s Speed by two stages',
    66: 'poisons the target',
    67: 'paralyzes the target',
    68: 'damaging hit with a chance to lower the target\'s Attack by one stage',
    69: 'damaging hit with a chance to lower the target\'s Defense by one stage',
    71: 'damaging hit with a chance to lower the target\'s Sp. Atk by one stage',
    76: 'damaging hit with a chance to confuse the target',
    86: 'temporarily disables the target\'s last move',
    93: 'changes the user\'s type to resist the last move used against it',
    105: 'damaging hit that can steal the target\'s held item',
    106: 'prevents the target from escaping',
    109: 'uses the native Ghost/non-Ghost Curse effect',
    119: 'power increases on consecutive successful uses',
    132: 'restores HP, with the amount depending on weather',
    148: 'delayed damaging attack',
    159: 'repeats a damaging attack while preventing sleep',
    164: 'starts hail',
    167: 'burns the target',
    223: 'uses the native Feint Protect/Detect effect',
    246: 'damages only after the user has used its other known moves',
    261: 'damages and traps the target; also affects targets using Dive',
}
CHANCE_EFFECTS = frozenset((31, 68, 69, 71, 76))
CATEGORIES = {0: 'Physical', 1: 'Special', 2: 'Status'}
TYPES = dict(enumerate(('Normal', 'Fighting', 'Flying', 'Poison', 'Ground',
                        'Rock', 'Bug', 'Ghost', 'Steel', 'Fairy', 'Fire',
                        'Water', 'Grass', 'Electric', 'Psychic', 'Ice',
                        'Dragon', 'Dark')))
TARGETS = {
    0: 'a single selected adjacent target', 1: 'one selected target (special selector)',
    2: 'a random opponent', 4: 'adjacent opponents', 8: 'all adjacent battlers',
    16: 'the user', 32: 'the user\'s side', 64: 'the whole field',
    128: 'the opposing side', 256: 'an ally',
    512: 'one selected target on the user\'s side', 1024: 'the target in front',
}
FLAGS = {
    1: 'makes contact', 2: 'subject to Protect/Detect',
    4: 'reflectable by Magic Coat', 8: 'stealable by Snatch',
    16: 'copyable by Mirror Move', 32: 'eligible for held-item flinching',
}
FAIRY_NAMES = dict(EN='Fairy', IT='Folletto', FR='Fée', ES='Hada', DE='Fee')


def _need(condition, message):
    if not condition:
        raise ValueError(message)


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def parse_moves(records):
    """Parse all 471 sixteen-byte records without dropping unknown fields."""
    _need(len(records) == MEMBER_COUNT, 'move archive must have 471 members')
    rows = []
    for identity, raw in enumerate(records):
        _need(len(raw) == RECORD.size, f'move {identity} must have 16 bytes')
        rows.append(dict(id=identity, **dict(zip(FIELDS, RECORD.unpack(raw))),
                         record_hex=bytes(raw).hex()))
    return rows


def describe_value(field, value, *, type_names=None):
    """Return authored English field meanings, retaining unclassified values."""
    if field == 'effect':
        return EFFECTS.get(value, f'unclassified native effect {value}')
    if field == 'category':
        return CATEGORIES.get(value, f'unclassified category {value}')
    if field == 'type':
        if type_names is not None and 0 <= value < len(type_names):
            return type_names[value]
        return TYPES.get(value, f'unclassified type {value}')
    if field == 'accuracy':
        return f'{value}%' if value else '0 (no ordinary accuracy check)'
    if field == 'effect_chance':
        return f'{value}%'
    if field == 'priority':
        return f'{value:+d}' if value else '0'
    if field == 'target':
        return TARGETS.get(value, f'unclassified target mask 0x{value:04X}')
    if field == 'flags':
        parts = [meaning for flag, meaning in FLAGS.items() if value & flag]
        unknown = value & ~sum(FLAGS)
        if unknown:
            parts.append(f'unclassified 0x{unknown:02X}')
        return '; '.join(parts) or 'none'
    return str(value)


def effect_description(move):
    """Describe actual selectors/chances, without importing modern defaults."""
    text = describe_value('effect', move['effect'])
    if move['effect'] in CHANCE_EFFECTS:
        text += f" ({move['effect_chance']}%)"
    return text


def type_names_for(names, locale, *, plus):
    """Name Plus type 9 from its actual engine identity, not stale '???' text.

    Fairy is presented by graphics; the ordinary bank 735 retains the retail
    mystery label. Preserve that native string for a genuine retail comparison.
    """
    _need(locale in LOCALES and len(names) >= 18, 'type-name locale/table')
    result = list(names)
    if plus:
        result[9] = FAIRY_NAMES[locale]
    return result


def compare_moves(before, after, *, playable_only=True):
    """Return every changed semantic field and byte in stable move-ID order.

    Names are compared when supplied. Descriptions are supporting editorial
    evidence, not a substitute for numeric gameplay facts. Dummy ID 0 and
    nonplayable members 468..470 are available via playable_only=False.
    """
    _need(len(before) == len(after) == MEMBER_COUNT, 'comparison requires 471 rows')
    result = []
    for identity in (PLAYABLE_IDS if playable_only else range(MEMBER_COUNT)):
        old, new = before[identity], after[identity]
        _need(old['id'] == new['id'] == identity, 'move rows are not in ID order')
        fields = FIELDS + (('name',) if 'name' in old and 'name' in new else ())
        deltas = [dict(field=field, before=old[field], after=new[field])
                  for field in fields if old[field] != new[field]]
        if not deltas:
            continue
        oldraw, newraw = bytes.fromhex(old['record_hex']), bytes.fromhex(new['record_hex'])
        result.append(dict(id=identity, before=copy.deepcopy(old), after=copy.deepcopy(new),
                           deltas=deltas, changed_bytes=[dict(offset=i, before=a, after=b)
                               for i, (a, b) in enumerate(zip(oldraw, newraw)) if a != b]))
    return result


def read_move_facts(data, charmap, *, descriptions=False):
    """Read data/native names in memory; never write or extract a cartridge."""
    rom = NintendoDSRom(data)
    raw = rom.getFileByName(ARCHIVE)
    records = NARC(raw).files
    rows = parse_moves(records)
    messages = NARC(rom.getFileByName(MESSAGE_ARCHIVE)).files
    chars, commands = _TEXT.load_charmap(charmap)

    def decode(words, *, plain=True):
        item = _TEXT.render(list(words), chars, commands)
        _need(not item['unknown_codes'] and not item['malformed_controls']
              and (not plain or not item['controls']), 'invalid move name/text')
        return item['text']

    names = [decode(words) for words in Bank(messages[750]).words]
    types = [decode(words) for words in Bank(messages[735]).words]
    _need(len(names) >= 468 and len(types) >= 18, 'incomplete native move/type names')
    prose = ([decode(words, plain=False) for words in Bank(messages[749]).words]
             if descriptions else None)
    for row in rows:
        if row['id'] < len(names):
            row['name'] = names[row['id']]
        if prose is not None and row['id'] < len(prose):
            row['description'] = prose[row['id']]
    return dict(moves=rows, type_names=types, sha256=_sha(data), bytes=len(data),
                archive_sha256=_sha(raw), records_sha256=_sha(b''.join(records)))


def add_provenance(rows, ancestry):
    """Annotate matching supplied tables, without inventing introduction dates."""
    output = copy.deepcopy(rows)
    for row in output:
        identity = row['id']
        matching = [entry['id'] for entry in ancestry
                    if all(entry['moves'][identity][field] == row['after'][field]
                           for field in FIELDS)]
        per_field = {delta['field']: [entry['id'] for entry in ancestry
                     if entry['moves'][identity].get(delta['field']) == delta['after']]
                     for delta in row['deltas']}
        wisp = (identity == 261 and len(row['deltas']) == 1 and
                row['deltas'][0] == dict(field='accuracy', before=75, after=85))
        row['provenance'] = dict(
            matching_supplied_versions=matching,
            earliest_matching_supplied_version=matching[0] if matching else None,
            matching_versions_by_field=per_field,
            original_sacred_gold_attribution='not established without an authenticated original Sacred Gold comparison',
            source=('source/sgp131/modern_moves.py' if wisp else ARCHIVE))
    return output


def audit_moves(candidate, retail, charmap, contract, locale, *, ancestry=(), descriptions=False):
    """Authenticate complete inputs and return an auditable 1..467 change set.

    Optional ancestry entries are {'id': contract source ID, 'data': bytes} in
    chronological order. An observed match is not proof of who authored it.
    """
    # Keep the renderer independent: it can import this module without a cycle.
    from distribution.reference_docs import validate_inputs
    validate_inputs(locale, candidate, retail, contract)
    current = read_move_facts(candidate, charmap, descriptions=descriptions)
    original = read_move_facts(retail, charmap, descriptions=descriptions)
    current_types = type_names_for(current['type_names'], locale, plus=True)
    sources = {entry['id']: entry for entry in contract['sources']}
    history = []
    for entry in ancestry:
        identity, data = entry['id'], entry['data']
        source = sources.get(identity, {})
        _need((_sha(data), len(data)) == (source.get('sha256'), source.get('bytes')),
              'ancestry identity does not match contract: ' + identity)
        history.append(dict(id=identity, **read_move_facts(data, charmap)))
    rows = add_provenance(compare_moves(original['moves'], current['moves']), history)
    for row in rows:
        row['before_effect'] = effect_description(row['before'])
        row['after_effect'] = effect_description(row['after'])
        for delta in row['deltas']:
            delta['before_text'] = describe_value(delta['field'], delta['before'], type_names=original['type_names'])
            delta['after_text'] = describe_value(delta['field'], delta['after'], type_names=current_types)
    nonplayable = [row for row in compare_moves(original['moves'], current['moves'], playable_only=False)
                   if row['id'] not in PLAYABLE_IDS]
    identity = lambda facts: {key: facts[key] for key in ('sha256', 'bytes', 'archive_sha256', 'records_sha256')}
    return dict(schema=1, locale=locale, version=contract['version'],
                candidate=identity(current), retail=identity(original),
                ancestry=[dict(id=entry['id'], **identity(entry)) for entry in history],
                coverage=dict(archive=ARCHIVE, archive_members=471, record_bytes=16,
                              playable_ids=[1, 467], playable_examined=467,
                              changed_playable=len(rows), changed_nonplayable=len(nonplayable)),
                rows=rows, nonplayable_changes=nonplayable, sources=SOURCES,
                type_names=dict(before=original['type_names'], after=current_types),
                scope='Shared move data in both difficulty settings; names are locale-specific. Native battle-code and script bug repairs are separate evidence.')


def verify_shared_move_tables(facts_by_locale):
    """Require all five complete numeric tables to match, including dummy rows."""
    _need(set(facts_by_locale) == set(LOCALES), 'all five locale tables required')
    reference = facts_by_locale['EN']['moves']
    _need(len(reference) == MEMBER_COUNT, 'EN table must have 471 rows')
    for locale in LOCALES:
        rows = facts_by_locale[locale]['moves']
        _need(len(rows) == MEMBER_COUNT, locale + ' table must have 471 rows')
        for identity, (old, new) in enumerate(zip(reference, rows)):
            _need(all(old[field] == new[field] for field in FIELDS),
                  f'{locale} move {identity} differs from shared EN data')
    return dict(equal=True, locales=list(LOCALES), members_per_locale=MEMBER_COUNT,
                playable_per_locale=467, fields=list(FIELDS))
