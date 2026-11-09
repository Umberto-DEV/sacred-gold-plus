"""Current compact manuals using original illustrations and embedded fonts.

Facts remain caller-owned inputs. Every generated glyph is checked against the
exact original font subset. Illustrated PDF pages are copied without rasterizing.
"""
from __future__ import annotations
from collections import Counter, defaultdict
from io import BytesIO
from pathlib import Path
import hashlib
import re
import unicodedata
from xml.sax.saxutils import escape
from distribution import legacy_style, move_changes, reference_docs

ROOT = Path(__file__).resolve().parents[2]
ORIGINALS = {
    'Pokemon Changes.pdf': ('ca556989399a76f4cd99896d79ea5142a13a34cf862f9898a7e7787a04e25dfb', 41),
    'Evolution Changes.pdf': ('ec7e4b621de769639eee2363f09919e14e8ceec31b5f172d52e49008c878a5bf', 2),
    'Important Item Locations.pdf': ('85597de371b2b41e0071d7a9db38c9274298a04c40f87dae8e156e0e7f89056a', 5),
    'Special Event Guide.pdf': ('b672fb8d46a4bdc92bf3fe89b6d08f4a45ba6f370b8a8bb3cd095695c8ca58fd', 23),
    'Pokemon Locations.pdf': ('61fe3cc6cd975454855ccc9bb33fc23484919fbc1bc7a41c9200a595cfd0d477', 64),
}
TITLES = {'Special-Events': 'Special Events', 'Pokemon-Changes': 'Pokemon Changes',
    'Pokemon-Locations': 'Pokemon Locations', 'Evolutions': 'Evolution Changes',
    'Items-TMs': 'Important Items and TMs', 'Trainers': 'Trainers',
    'Game-Guide': 'Game Guide', 'Move-Changes': 'Move Changes'}
COVERS = {'Special-Events': 'Special Event Guide.pdf', 'Pokemon-Changes': 'Pokemon Changes.pdf',
    'Pokemon-Locations': 'Pokemon Locations.pdf', 'Evolutions': 'Evolution Changes.pdf',
    'Items-TMs': 'Important Item Locations.pdf'}
STATS = ('HP', 'Attack', 'Defense', 'Speed', 'Sp. Atk', 'Sp. Def')
# Distinct fishing areas share one displayed MapSection name. Their stable
# native map IDs are defined by pret/pokeheartgold include/constants/maps.h at
# the immutable revision cited in move_changes.SOURCES. Keep the player-facing
# floor/room name so different pools are not presented as contradictory rows.
FISHING_AREAS = {
    99: '1F', 153: 'B1F', 154: 'B2F',  # Union Cave
    121: '1F', 243: 'B2F',            # Whirl Islands
    145: '1F', 450: '2F', 451: 'B1F', # Cerulean Cave
    122: '1F', 459: 'Upper Mountainside', 462: 'Moltres Chamber',
    463: '2F', 464: '3F',             # Mt. Silver Cave
}
FIELD_LABELS = dict(effect='Effect', category='Category', power='Power', type='Type',
    accuracy='Accuracy', pp='PP', effect_chance='Stored effect chance', target='Target',
    priority='Priority', flags='Interactions', contest_effect='Contest effect',
    contest_type='Contest type', reserved='Reserved data')
NORMALIZATIONS = {'₧₦': 'Pokemon', '♀': ' female', '♂': ' male', '→': ' to ', '←': ' from ',
    '≥': 'at least ', '≤': 'at most ', '×': 'x', '–': '-', '—': '-', '‑': '-',
    '\u00a0': ' ', '\u202f': ' ', ';': ',', '“': '’', '”': '’', '‘': '’',
    "'": '’', '\\n': ' ', '\\r': ' '}
CREDITS = ('Sacred Gold by Drayano. Fairy foundation by mikelan / Mikelan98. '
    'Original Plus by NefariousnessNo3436. Original illustrations and guide credits '
    'remain with their contributors. Trainer reference by JD48096761, inspired by '
    'u/ittapubas. Current source continuation: https://github.com/Umberto-DEV/sacred-gold-plus')
GALLERY = ROOT / 'images/1.3.1/guide-EN.png'
GALLERY_SHA256 = '2701252bce0d43fd1d814d987100fbe0741eaabbb59c61124e198bb0472db227'

def _need(condition, message):
    if not condition:
        raise ValueError(message)

def normalize_text(text):
    """Explicit punctuation/diacritic substitutions, retaining unknown symbols.

    The original Calibri subset lacks accented Latin letters and ASCII quotes.
    Accents are transliterated. Unknown symbols survive so require() rejects them.
    """
    text = str(text)
    for old, new in NORMALIZATIONS.items():
        text = text.replace(old, new)
    text = unicodedata.normalize('NFKD', text)
    text = ''.join(char for char in text if not unicodedata.combining(char))
    return re.sub(r'[ \t]+', ' ', text).strip()

def learnset_edits(before, after):
    """Return changed moves and every old/new level, preserving repetitions."""
    def grouped(pairs):
        result = defaultdict(list)
        for level, move in pairs:
            result[move].append(level)
        return {move: tuple(sorted(levels)) for move, levels in result.items()}
    old, new = grouped(before), grouped(after)
    return [(move, old.get(move, ()), new.get(move, ())) for move in sorted(old.keys() | new.keys())
            if old.get(move, ()) != new.get(move, ())]

def evolution_edits(before, after):
    old = {tuple(row) for row in before}
    return [row for row in after if tuple(row) not in old]

def parse_evolution_records(records):
    """Include retail location methods 24..26 when reading the clean baseline."""
    import struct
    _need(len(records) >= 494, 'incomplete evolution archive')
    rows=[]
    for species in range(1,494):
        _need(len(records[species]) >= 42, 'truncated evolution record')
        for slot in range(7):
            method,parameter,target=struct.unpack_from('<3H',records[species],slot*6)
            if not method: continue
            _need(1 <= method <= 26 and 1 <= target <= 493, 'evolution method/target')
            rows.append((species,slot,method,parameter,target))
    return rows

def _name(facts, kind, number):
    return reference_docs._name(facts, kind, number)

def _types(facts, values, *, plus):
    names = [('Fairy' if plus and value == 9 else _name(facts, 'type', value).title()) for value in values]
    return ' / '.join(dict.fromkeys(names))

def species_blocks(before, after, facts, baseline):
    old = {row['id']: row for row in before}; blocks = []
    for row in after:
        previous = old[row['id']]; changes = []
        if tuple(previous['types']) != tuple(row['types']):
            changes.append('+Type: ' + _types(baseline, previous['types'], plus=False) + ' to ' + _types(facts, row['types'], plus=True))
        if tuple(previous['abilities']) != tuple(row['abilities']):
            abilities = lambda source, values: ' / '.join(_name(source, 'ability', value) for value in values if value) or 'None'
            changes.append('+Abilities: ' + abilities(baseline, previous['abilities']) + ' to ' + abilities(facts, row['abilities']))
        for index, (was, now) in enumerate(zip(previous['stats'], row['stats'])):
            if was != now:
                changes.append(f'+{STATS[index]}: {was} to {now}')
        edits = learnset_edits(previous['learnset'], row['learnset'])
        if edits:
            pieces = []; levels = lambda values: '/'.join(str(value) for value in values)
            for move, was, now in edits:
                name = _name(facts, 'move', move)
                if not was: pieces.append(name + ' added at Lv.' + levels(now))
                elif not now: pieces.append(name + ' removed from Lv.' + levels(was))
                else: pieces.append(name + ' Lv.' + levels(was) + ' to Lv.' + levels(now))
            changes.append('+Level-Up Moves: ' + ', '.join(pieces))
        if changes:
            blocks.append(('h2', f'{row["id"]:03d} ' + _name(facts, 'pokemon', row['id'])))
            blocks.extend(('bullet', text) for text in changes)
    return blocks

def proofed_paragraphs(entry):
    result = []
    for text in reference_docs._paragraphs(entry):
        if 'tree blocking Route 36' in text:
            text = text.replace('Super Rod', 'SquirtBottle')
        if 'show Cynthia a member of that Sinnoh' in text:
            text = text.replace('At Goldenrod’s Archaeology Center,',
                'After becoming Champion, at Goldenrod’s Archaeology Center,')
        result.append(text)
    return result

def evolution_condition(method, parameter, names):
    if method in (22, 23):
        gender = 'male' if method == 22 else 'female'
        return f'Level up {gender} at Lv.{parameter} or higher.' if parameter else f'Level up {gender}.'
    return reference_docs.evolution_description(method, parameter, names, 'EN')

def fishing_groups(facts):
    """Aggregate native fishing slots and deduplicate identical map aliases."""
    by_map = defaultdict(dict); special = defaultdict(list); sections = {}
    for mid, section, bank, method, time, slot, species, low, high, rate in facts['encounters']:
        sections[mid] = section
        if method in (3, 4, 5): by_map[(mid, method)][slot] = species
        elif method == 10: special[(mid, time, 'Swarm')].append((slot, species))
        elif method in (11, 12): special[(mid, 4 if method == 11 else 5, 'Night')].append((slot, species))
    weights = facts['weights']['fish']
    _need(len(weights) == 5 and sum(weights) == 100, 'native fishing weights')
    seen, output = set(), []
    for (mid, method), slots in sorted(by_map.items()):
        _need(set(slots) == set(range(5)), 'incomplete five-slot fishing pool')
        variants = [('All times', slots)]
        for condition in ('Night', 'Swarm'):
            replacements = special.get((mid, method, condition))
            if replacements:
                changed = dict(slots); changed.update(replacements)
                if changed != slots: variants.append((condition, changed))
        for condition, pool in variants:
            counts = Counter()
            for slot, species in pool.items(): counts[species] += weights[slot]
            distribution = tuple(sorted(counts.items())); name = _name(facts, 'map', sections[mid])
            if mid in FISHING_AREAS:
                name += ' - ' + FISHING_AREAS[mid]
            key = (name, method, condition, distribution)
            if key not in seen:
                seen.add(key); output.append(dict(map=name, rod=method, condition=condition, species=distribution))
    return sorted(output, key=lambda row: (row['map'].casefold(), row['rod'], row['condition']))

def _category_blocks(facts, identity, count):
    categories = [category for category in facts['guide'] if category['id'] == identity]
    _need(len(categories) == 1 and len(categories[0]['entries']) == count, 'current Guide category count')
    entries = categories[0]['entries']; blocks = []; seen = set()
    extras = defaultdict(list)
    if identity == 3:
        canonical = [entry for entry in entries if entry['id'] < 5000]
        _need(len(canonical) == 38, '38 canonical current event topics required')
        signatures = {tuple(proofed_paragraphs(entry)) for entry in canonical}
        for entry in entries:
            if entry['id'] < 5000 or tuple(proofed_paragraphs(entry)) in signatures: continue
            # Two species aliases add genuine route details rather than copy a
            # topic verbatim. Fold them into their related canonical topic.
            _need(entry['id'] in (5485,5488), 'unclassified distinct event alias')
            target = 2146 if entry['id'] == 5485 else 2491
            extras[target].extend(entry['title'] + ': ' + p.lstrip('- ') for p in proofed_paragraphs(entry))
        entries = canonical
    for entry in sorted(entries, key=lambda entry: entry['id']):
        paragraphs = extras[entry['id']] + proofed_paragraphs(entry); signature = tuple(paragraphs)
        if identity == 3 and signature in seen: continue
        seen.add(signature); blocks.append(('h2', entry['title']))
        blocks.extend(('p', text) for text in paragraphs)
    if identity == 3: _need(len(seen) == 38, '38 distinct current event topics required')
    return blocks

def _move_blocks(audit):
    _need(audit['coverage']['playable_examined'] == 467 and len(audit['rows']) == 52,
          'complete current move comparison required')
    blocks = [('p', 'All 467 moves were checked against unmodified HeartGold. These are the 52 changed definitions, including inherited Plus changes. They apply in both difficulty modes and all five languages.'),
        ('p', 'Names below are the actual English game names. Accuracy 0 skips the ordinary accuracy check. PP means base PP before PP Ups. The game retains selected older mechanics, so later-generation move descriptions may differ.'),
        ('p', 'Forty-nine complete current records already match Plus 1.01. Moonblast and Play Rough use corrected damaging effects by Plus 1.1. Will-O-Wisp accuracy increased from 75 to 85 in 1.3.1. Earlier Plus versions do not establish which changes originated in Sacred Gold.')]
    for row in audit['rows']:
        old, new = row['before'], row['after']; title = f'{row["id"]:03d} ' + old['name']
        if old['name'] != new['name']: title += ' to ' + new['name']
        blocks.append(('h2', title))
        for delta in row['deltas']:
            field = delta['field']
            if field == 'name': continue
            if field == 'flags':
                toggled = delta['before'] ^ delta['after']
                for flag, label in move_changes.FLAGS.items():
                    if toggled & flag:
                        was = 'yes' if delta['before'] & flag else 'no'
                        now = 'yes' if delta['after'] & flag else 'no'
                        blocks.append(('bullet', f'+{label.capitalize()}: {was} to {now}'))
                unknown = toggled & ~sum(move_changes.FLAGS)
                if unknown:
                    was = 'set' if delta['before'] & unknown else 'clear'
                    now = 'set' if delta['after'] & unknown else 'clear'
                    blocks.append(('bullet', f'+Unclassified internal flag 0x{unknown:02X}: {was} to {now}.'))
            else:
                was = delta['before_text'].replace('???', 'untyped (retail type 9)')
                blocks.append(('bullet', '+' + FIELD_LABELS[field] + ': ' + was + ' to ' + delta['after_text']))
        if old['name'] != new['name']:
            current_type = audit['type_names']['after'][new['type']]
            blocks.append(('p', f'Current: {current_type}, {move_changes.CATEGORIES[new["category"]]}, power {new["power"]}, accuracy {move_changes.describe_value("accuracy", new["accuracy"])}, PP {new["pp"]}, priority {new["priority"]:+d}, {move_changes.describe_value("target", new["target"])}.'))
            blocks.append(('p', 'Current effect: ' + row['after_effect'] + '.'))
    blocks.extend([('h2', 'Details that differ from later games'),
        ('p', 'Baby Eyes has priority +6. Drain Kiss restores half the damage dealt and does not make contact. Dazzle Gleam targets one selected battler. Moonblast has a 10% Sp. Atk drop. Fairy Wind has accuracy 0, so there is no ordinary accuracy roll. Play Rough has a 10% Attack drop. Magical Leaf is Ice type.'),
        ('p', 'The stored effect-chance byte is shown whenever it changes. Direct status effects do not use it as a separate damaging-hit probability. Internal flag 0x40 is included without assigning it an unverified gameplay meaning.')])
    return blocks

DEFAULT_LOCATION_NOTES = (
    'The illustrated area pages are the original Sacred Gold / Storm Silver reference. This package targets Sacred Gold Plus based on HeartGold. Storm Silver alternatives do not describe another included variant.',
    'Use the current fishing lists for every Old Rod, Good Rod and Super Rod percentage. Ordinary grass, Surf, Rock Smash and radio area guidance remains useful. Wild level scaling is a separate Plus option, so encountered levels may differ from the historical pages.',
    'Listed species probabilities are ordinary base odds. Lead abilities and other encounter-generation modifiers can affect outcomes. Wednesday radio uses Meridian Sound and Thursday radio uses Pastoral Sound. Respect time-of-day and encounter eligibility requirements.',
    'The daily fishing outbreaks are Whiscash in Violet City, Qwilfish on Route 32, Remoraid on Route 44 and Relicanth on Route 12. Their swarm pools apply only during the corresponding outbreak.',
    'The original guide excludes Headbutt trees. Its area pages do not provide complete Safari object-gate or Bug-Catching Contest instructions.')

GAME_TEXT = [
    ('h2', 'Guide and summary controls'),
    ('p', 'Open Guide from the field menu. Choose Training, Evolutions, Special Pokemon or Items and TMs. A opens an entry or link, B returns, and L/R or Left/Right jumps five entries in lists. Returning from a link restores the previous position. The Guide contains 467 entries.'),
    ('p', 'In the Pokemon summary, L shows EVs, R shows IVs and SELECT returns to ordinary stats. From the ordinary field party menu, R opens the native PC storage interface when the current context allows it.'),
    ('h2', 'Options and Plus settings'),
    ('p', 'In Options, press SELECT for the current Game, Plus and Shiny settings. Up/Down selects a row, Left/Right changes its value, and L/R moves between sections. A opens or confirms a selector, Y opens Info, X asks to Apply, and B goes back. At the root, B lets you apply, discard or continue editing pending changes. Settings use physical buttons, not touch.'),
    ('p', 'Trainer difficulty and wild level scaling are independent choices. Plus also controls battle motion, character loading and the Wi-Fi slot. Levels remain capped at 100. Native audio, text speed, battle style, controls and frame settings remain available.'),
    ('h2', 'Bag, camera and everyday play'),
    ('p', 'The main Bag pocket has 252 slots, with expanded capacity in other pockets. Consecutive Rare Candy use keeps the party menu open and retains normal move-learning and evolution prompts. The classic camera is used in 52 interiors and caves, while the wider Plus view remains outdoors.'),
    ('h2', 'Shiny profiles and Search'),
    ('p', 'Classic uses 1/512 for eligible generation. Pro starts at 1/4096 for the chosen target, then improves to 1/2048 after 10 successes, 1/1024 after 20 and 1/512 after 40. The next generated encounter uses the completed threshold. Catching or defeating the target advances the chain. Another ordinary species, escape, loss or draw breaks it. No threshold guarantees a shiny.'),
    ('p', 'Search chooses an already-seen species from the current area and method, respecting time, terrain, forms, owned rods and progression. It requires 40 valid steps. Prepare the hunt in settings, confirm Apply and return to a free field. A successful Search spends the charge. Changing mode or target resets chain and charge, while cancelling preserves them.'),
    ('p', 'A normal SAVE retains mode, target, chain and random state. A cold restart resets the step charge. Eggs, gifts, starters, trades, Mystery Gift, roamers, trainer Pokemon, Safari, contests, doubles and forced events retain their separate native paths. Eligible ordinary statics use base odds without a chain bonus. Existing Pokemon are never rerolled.'),
    ('gallery', str(GALLERY)),
    ('caption', 'Historical public gallery: English 1.3.1 Guide presentation, captured 6 November 2026. This image illustrates the interface and is not a new 1.3.2 runtime test.'),
    ('h1', 'Training')]

def _trainer_blocks(facts):
    names = lambda kind, number: _name(facts, kind, number)
    blocks = [('p', 'Current native parties. Each Pokemon lists Normal and Plus levels, its held item and moves. Plus-only move substitutions are explicit. Level-up means the game generates moves from the species and level.')]
    for trainer in facts['trainers']:
        if not trainer['party']: continue
        trainer_name = names('trainer', trainer['id']).replace('???', '(chosen name)')
        blocks.append(('h2', f'#{trainer["id"]:03d} ' + names('class', trainer['class']) + ' ' + trainer_name))
        for mon in trainer['party']:
            label = names('pokemon', mon['species']) + (f' (form {mon["form"]})' if mon['form'] else '')
            item = names('item', mon['item']) if mon['item'] else 'None'
            moves = ' / '.join(names('move', move) for move in mon['moves'] if move) or 'Level-up moves'
            blocks.append(('p', f'{label} - Lv.{mon["level"]}, Plus Lv.{mon["plus_level"]} - Item: {item} - {moves}'))
            if mon['plus_moves'] != mon['moves']:
                blocks.append(('p', 'Plus moves: ' + ' / '.join(names('move', move) for move in mon['plus_moves'] if move)))
    return blocks

def build_guide_texts(facts, baseline, move_audit, *, location_notes):
    """Build inspectable plain-text blocks before any PDF is created."""
    _need([r['id'] for r in facts['species']] == list(range(1, 494)) and
          [r['id'] for r in baseline['species']] == list(range(1, 494)), 'all 493 species required')
    texts = {name: [('h1', TITLES[name]), ('p', 'Sacred Gold Plus 1.3.2 - current English reference.')] for name in TITLES}
    names = lambda kind, number: _name(facts, kind, number)
    texts['Pokemon-Changes'].extend([
        ('p', 'Differences from unmodified HeartGold, including inherited Sacred Gold and early Plus changes. All 493 species were checked. Only changed type, ability, base-stat and level-up entries are listed. Move definitions are covered separately in Move Changes.'),
        ('p', 'Changes apply in both difficulties. Existing Pokemon keep their identity, IVs, EVs, moves and ability slot. Base-stat changes do not grant EVs or IVs.')])
    texts['Pokemon-Changes'].extend(species_blocks(baseline['species'], facts['species'], facts, baseline))
    texts['Evolutions'].append(('p', 'Current evolution methods that differ from unmodified HeartGold. Trade alternatives and changed requirements supersede the original guide. Existing native trade routes remain available where retained by the game.'))
    for species, slot, method, parameter, target in evolution_edits(baseline['evolutions'], facts['evolutions']):
        texts['Evolutions'].append(('h2', names('pokemon', species) + ' to ' + names('pokemon', target)))
        texts['Evolutions'].append(('bullet', '+ ' + evolution_condition(method, parameter, names)))
    texts['Evolutions'].append(('h2', 'Other current requirements'))
    for species, slot, method, parameter, target in facts['evolutions']:
        if species in (349, 412, 415, 458):
            texts['Evolutions'].append(('p', names('pokemon', species) + ' to ' + names('pokemon', target) + ': ' + evolution_condition(method, parameter, names)))
    texts['Items-TMs'].append(('p', 'All 156 current in-game Guide entries for important items, services and TMs. These instructions replace the older locations.'))
    texts['Items-TMs'].extend(_category_blocks(facts, 2, 156))
    texts['Special-Events'].extend([
        ('p', 'Read these current instructions first. The 38 distinct current Special Pokemon topics appear once each. Original illustrated event pages follow with their original numbering. Wherever wording differs, follow the current instructions here.'),
        ('p', 'Save before one-opportunity routes: static Latios, Celebi, Jirachi and the Tohjo shiny final-form choice. The old cover promise of endless retries does not apply to every route. Spiritomb consumes an Odd Keystone each attempt. Arceus capture and flee/defeat endings differ, so do not assume an automatic retry.')])
    texts['Special-Events'].extend(_category_blocks(facts, 3, 76))
    texts['Special-Events'].extend([('h1', 'Original illustrated event reference'),
        ('p', 'The following pages preserve original illustrations and route guidance. Current requirements, including SquirtBottle for Sudowoodo and Champion status for Cynthia, appear in the current section above.')])
    notes = [location_notes] if isinstance(location_notes, str) else list(location_notes)
    _need(notes and all(isinstance(note, str) and note.strip() for note in notes), 'reviewed location notes required')
    texts['Pokemon-Locations'].extend(('p', note) for note in notes)
    texts['Pokemon-Locations'].extend([
        ('h1', 'Current fishing percentages'),
        ('p', 'These lists supersede every rod percentage in the original pages. Identical species are combined across the five slots: 40%, 30%, 15%, 10% and 5%. These are species probabilities after a successful bite, before applicable lead-ability and other encounter modifiers, rather than the chance to get a bite.'),
        ('p', 'Identical map aliases are combined. Night lines replace the daytime pool at night. Swarm lines apply only during the announced outbreak: Whiscash in Violet City, Qwilfish on Route 32, Remoraid on Route 44 or Relicanth on Route 12.')])
    previous_map = None
    for group in fishing_groups(facts):
        if group['map'] != previous_map:
            texts['Pokemon-Locations'].append(('h2', group['map'])); previous_map = group['map']
        rod = {3: 'Old Rod', 4: 'Good Rod', 5: 'Super Rod'}[group['rod']]
        condition = '' if group['condition'] == 'All times' else ' (' + group['condition'] + ')'
        distribution = ', '.join(names('pokemon', species) + f' {weight}%' for species, weight in group['species'])
        texts['Pokemon-Locations'].append(('p', rod + condition + ': ' + distribution))
    texts['Pokemon-Locations'].extend([('h1', 'Original illustrated location reference'),
        ('p', 'Every original map page follows. Use the grass, Surf, Rock Smash, radio and illustrated area guidance alongside the current notes. For every fishing percentage, use the current lists above. The original guide excludes Headbutt trees and does not fully describe Safari object gates or the Bug-Catching Contest.')])
    texts['Trainers'].extend(_trainer_blocks(facts))
    texts['Game-Guide'].extend(GAME_TEXT)
    texts['Game-Guide'].extend(_category_blocks(facts, 4, 6))
    texts['Game-Guide'].extend([('h2', 'Continue an existing adventure'),
        ('p', 'Keep your language, installed ROM filename and path, emulator association and raw .sav. Save in-game, close fully and back up the active save and installed ROM. Test the successor on a separate save copy through Continue, native SAVE and a cold restart. Replace only the ROM, keeping the personal save in its original place. No new game or settings reset is required.')])
    texts['Move-Changes'].extend(_move_blocks(move_audit))
    for name in texts: texts[name].extend([('h2', 'Credits'), ('p', CREDITS)])
    return texts

def _original_paths(originals):
    paths = ({name: Path(originals[name]) for name in ORIGINALS} if isinstance(originals, dict)
             else {name: Path(originals) / name for name in ORIGINALS})
    from pypdf import PdfReader
    for name, path in paths.items():
        expected, pages = ORIGINALS[name]
        _need(path.is_file() and not path.is_symlink(), 'missing regular original PDF: ' + name)
        _need(hashlib.sha256(path.read_bytes()).hexdigest() == expected, 'original PDF identity: ' + name)
        _need(len(PdfReader(path).pages) == pages, 'original PDF page count: ' + name)
    return paths

def _font_text(text, face):
    text = normalize_text(text)
    if 0x2019 not in face.codepoints and 0x27 in face.codepoints:
        text = text.replace('’', "'")
    face.require(text)
    return text

def _body_pdf(blocks, title, body, hand):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
    from reportlab.lib.utils import ImageReader
    bodyname, handname = body.register(), hand.register()
    output = BytesIO(); story = []
    normal = ParagraphStyle('LegacyBody', fontName=bodyname, fontSize=10.2, leading=12.4,
        spaceAfter=3, textColor='black')
    bullet = ParagraphStyle('LegacyBullet', parent=normal, leftIndent=9, spaceAfter=1.5)
    caption = ParagraphStyle('LegacyCaption', parent=normal, fontSize=8, leading=10)
    for role, value in blocks:
        if role == 'gallery':
            raw = Path(value).read_bytes()
            _need(hashlib.sha256(raw).hexdigest() == GALLERY_SHA256, 'historical gallery image identity')
            width, height = ImageReader(BytesIO(raw)).getSize()
            story += [Spacer(1, 7), Image(BytesIO(raw), width=230, height=230*height/width), Spacer(1, 4)]
            continue
        text = _font_text(value, body)
        style = bullet if role == 'bullet' else caption if role == 'caption' else normal
        if role in ('h1', 'h2'):
            try:
                heading = _font_text(value, hand); chosen, text = handname, heading
            except ValueError:
                chosen = bodyname
            style = ParagraphStyle('LegacyHeading', parent=normal, fontName=chosen,
                fontSize=17 if role == 'h1' else 12.5, leading=21 if role == 'h1' else 16,
                spaceBefore=12 if role == 'h1' else 7, spaceAfter=4, keepWithNext=True)
        story.append(Paragraph(escape(text).replace('\n', '<br/>'), style))
    def footer(canvas, document):
        text = _font_text(f'Sacred Gold Plus 1.3.2 - {title} - {document.page + 1}', body)
        canvas.setFont(bodyname, 8); canvas.setFillColorRGB(0, 0, 0)
        canvas.drawCentredString(A4[0]/2, 28, text)
    document = SimpleDocTemplate(output, pagesize=A4, leftMargin=49, rightMargin=49,
        topMargin=42, bottomMargin=43, title='Sacred Gold Plus 1.3.2 - ' + title,
        author='Sacred Gold Plus contributors', invariant=1, pageCompression=1)
    document.build(story, onFirstPage=footer, onLaterPages=footer)
    return output.getvalue()

def _new_cover(title, originals, body, hand):
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.utils import ImageReader
    output = BytesIO(); page = canvas.Canvas(output, pagesize=A4, invariant=1, pageCompression=1)
    art = legacy_style.extract_cover_art(originals['Pokemon Changes.pdf'])
    reader = ImageReader(BytesIO(art)); width, height = reader.getSize()
    ratio = min(340/width, 300/height); width *= ratio; height *= ratio
    page.drawImage(reader, (A4[0]-width)/2, 370-height/2, width=width, height=height, mask='auto')
    for face, size, y, text in [(hand, 23, 748, 'Sacred Gold Plus 1.3.2'),
        (hand, 27, 660, title), (body, 12, 160, 'Current English reference'),
        (body, 10, 140, 'Original guide artwork and contributor credits retained')]:
        value = _font_text(text, face); page.setFont(face.register(), size)
        page.drawCentredString(A4[0]/2, y, value)
    page.showPage(); page.save()
    return output.getvalue()

def _cover_annotation(name, body, size):
    from reportlab.pdfgen import canvas
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.platypus import Paragraph
    text = 'Sacred Gold Plus 1.3.2 - current instructions follow. The historical introduction above is superseded by the current guide.'
    if name == 'Special-Events':
        text += ' Save before Latios, Celebi, Jirachi and the Tohjo choice: these are one-opportunity routes. The older endless-retry wording is superseded.'
    elif name == 'Pokemon-Changes':
        text += ' Use Move Changes for current move values. Strength has 75 power.'
    elif name == 'Pokemon-Locations':
        text += ' Use the current fishing lists for all rod percentages. Original map illustrations are retained.'
    output = BytesIO(); page = canvas.Canvas(output, pagesize=size, invariant=1, pageCompression=1)
    page.setFillColorRGB(1, 1, 1); page.setStrokeColorRGB(0, 0, 0)
    page.rect(45, 25, size[0]-90, 74, fill=1, stroke=1)
    paragraph = Paragraph(escape(_font_text(text, body)), ParagraphStyle('LegacyCoverNote',
        fontName=body.register(), fontSize=9.2, leading=11.5, textColor='black'))
    width, height = paragraph.wrap(size[0]-108, 65)
    _need(height <= 65, 'cover annotation exceeds reserved area')
    paragraph.drawOn(page, 54, 91-height)
    page.showPage(); page.save()
    return output.getvalue()

def render_current_guides(candidate, retail, charmap, contract, originals, output, *, location_notes):
    """Create eight authenticated deterministic manuals, refusing existing output.

    The caller starts its artifact operation before invoking this authoring API.
    Original cover art/text is retained with an explicit current-version note.
    """
    from ndspy.narc import NARC
    from ndspy.rom import NintendoDSRom
    from pypdf import PdfReader, PdfWriter
    reference_docs.validate_inputs('EN', candidate, retail, contract)
    _need(contract['version'] == '1.3.2', 'illustrated guide version must be 1.3.2')
    destination = Path(output)
    if destination.exists() or destination.is_symlink(): raise FileExistsError(destination)
    paths = _original_paths(originals)
    facts = reference_docs.read_facts(candidate, charmap)
    baseline = reference_docs.read_facts(retail, charmap, include_guide=False)
    baseline['evolutions'] = parse_evolution_records(NARC(NintendoDSRom(retail).getFileByName('a/0/3/4')).files)
    move_audit = move_changes.audit_moves(candidate, retail, charmap, contract, 'EN')
    texts = build_guide_texts(facts, baseline, move_audit, location_notes=location_notes)
    body = legacy_style.load_face(paths['Pokemon Changes.pdf'], 'Calibri')
    hand = legacy_style.load_face(paths['Special Event Guide.pdf'], 'SegoePrint')
    for blocks in texts.values():
        for role, text in blocks:
            if role != 'gallery': _font_text(text, body)
    outputs = {}
    for name, blocks in texts.items():
        writer = PdfWriter()
        if name in COVERS:
            cover = PdfReader(paths[COVERS[name]]).pages[0]
            size = (float(cover.mediabox.width), float(cover.mediabox.height))
            cover.merge_page(PdfReader(BytesIO(_cover_annotation(name, body, size))).pages[0])
            writer.add_page(cover)
        else:
            writer.add_page(PdfReader(BytesIO(_new_cover(TITLES[name], paths, body, hand))).pages[0])
        for page in PdfReader(BytesIO(_body_pdf(blocks, TITLES[name], body, hand))).pages: writer.add_page(page)
        if name in ('Special-Events', 'Pokemon-Locations'):
            for page in PdfReader(paths[COVERS[name]]).pages[1:]: writer.add_page(page)
        writer.add_metadata({'/Title': 'Sacred Gold Plus 1.3.2 - ' + TITLES[name],
            '/Author': 'Sacred Gold Plus contributors', '/Producer': 'Sacred Gold Plus illustrated reference generator'})
        stream = BytesIO(); writer.write(stream)
        outputs[name + '-1.3.2-EN.pdf'] = stream.getvalue()
    destination.mkdir(parents=True, exist_ok=False)
    for name, data in outputs.items():
        with (destination/name).open('xb') as stream: stream.write(data)
    return [destination/name for name in outputs]

def main(argv=None):
    """Regenerate current manuals from owned ROMs and public original guides."""
    import argparse
    import json
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate', required=True, type=Path)
    parser.add_argument('--retail', required=True, type=Path)
    parser.add_argument('--charmap', required=True, type=Path)
    parser.add_argument('--originals', type=Path, default=ROOT/'guides/originals')
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--contract', type=Path, default=Path(__file__).with_name('release-1.3.2-r4.json'))
    parser.add_argument('--location-notes', type=Path)
    arguments = parser.parse_args(argv)
    notes = DEFAULT_LOCATION_NOTES
    if arguments.location_notes:
        notes = json.loads(arguments.location_notes.read_text())
        if isinstance(notes, dict): notes = notes['location_notes']
    paths = render_current_guides(arguments.candidate.read_bytes(), arguments.retail.read_bytes(),
        arguments.charmap, json.loads(arguments.contract.read_text()), arguments.originals,
        arguments.output, location_notes=notes)
    print(json.dumps([dict(name=path.name, bytes=path.stat().st_size,
        sha256=hashlib.sha256(path.read_bytes()).hexdigest()) for path in paths], indent=2))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
