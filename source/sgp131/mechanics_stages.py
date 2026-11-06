"""Mechanical 1.3.1 stages (4a) registered as strictly post-UI, confined, independently replayable.

The UI stage seeds `crc32(y9)`, the ROM length and the FAT positions of files 54 and 156
into resident ARM9 words that the runtime compares against the cartridge (module.c,
guide_resource.c). A stage that runs after UI may therefore only rewrite bytes it has
declared in advance, and those declarations may never reach the container (header, FAT,
y9), the UI-owned files (27, 54, 156, 167), the UI seeds or the resident reserve.

Registered stages wrap the real 4a APIs without changing them:
  moves      sgp131.modern_moves.apply/verify   -> 1 byte inside the a/0/1/1 slot (file 140)
  ai         ai_scoring plus type_chart         -> overlay 12 and the overlay 18 damage chart
  ai-immunities sgp131.ai_scoring.apply_dry_skin/verify_dry_skin
                                                -> overlay 10 plus a/0/9/9 (file 228), both in place
  abilities  sgp131.modern_abilities.apply_code/verify_code
                                                -> 28 B payload in the 32 B reserve slot `modern-accuracy.code` plus the
                                                   6 byte seam in overlay 12 (shared with `ai`), all in place
  legendary-scene-version sgp131.legendary_scene_version.apply/verify
                                                -> three exact selectors in compressed overlay 2, in place
  pokeathlon sgp131.pokeathlon.apply/verify -> overlay 99 stream rewritten inside its own slot
  traded-egg sgp131.traded_egg.apply/verify -> overlay 95 hatch palette helper inside its own slot
  bag-foreign sgp131.bag_foreign.apply/verify -> Training code successor inside its existing owner
  bag-view-position sgp131.bag_view_position.apply/verify -> two static ARM9 spans, no reserve/save change
  lottery-id sgp131.lottery_id.apply/verify -> one static ARM9 halfword, no reserve/save change
  battle-tower-wrap sgp131.battle_tower_wrap.apply/verify -> four static ARM9 halfwords, no reserve/save change
  battle-animation-facade sgp131.battle_animation_facade.apply/verify -> six timing bytes in a/0/1/0 member 263
  battle-animation-dynamicpunch sgp131.battle_animation_dynamicpunch.apply/verify -> one Delay byte in a/0/1/0 member 223
  battle-animation-helping-hand sgp131.battle_animation_helping_hand.apply/verify -> three loop-boundary bytes in a/0/1/0 member 270
  battle-animation-strength sgp131.battle_animation_strength.apply/verify -> one frame-count byte in a/0/1/0 member 70
  battle-animation-spit-up sgp131.battle_animation_spit_up.apply/verify -> cleanup in compressed overlay 7
  giratina-pc-form sgp131.giratina_pc_form.apply/verify -> PC-exit party reconciliation in compressed overlay 14
  invisible-grass sgp131.invisible_grass.apply/verify -> six Route 43/44 permission-grid words in a/0/6/5
  waterfall-facing sgp131.waterfall_facing.apply/verify -> successful overlay-1 descent seam plus 20 B resident wrapper
  follower-menu-jump sgp131.follower_menu_jump.apply/verify -> paused follower height helper in compressed overlay 1

`abilities` consumes the fixed modern-accuracy slot only after the independent cold UI reader proves complete Guide
retirement and reserve.allocate issues the genuine grant. Row-only substitutes remain explicitly caller-supplied tests;
controls, portable and rematches require the full freshly reissued receipt. Keen Eye's description is the keen-eye-text
archive producer, applied in the UI's single append.
`ai` and `abilities` both rewrite overlay 12 inside the same FAT slot; the later stage must provide a `peel` that takes itself
back out of an image, so the chain can reconstruct the intermediate images from the final one.

`gifts` is the one ARCHIVE-ONLY stage: two script fixes (six ribbon tails and the Eevee party guard, members of a/0/1/2) with no
ARM code, no reserve memory and no ARM9 region. It has no post-UI writer, no receipt of its own and no region to confine: its
whole effect is the `gifts-scripts` archive producer (sgp131/gifts_archives.py, registered by `archives.register_owner_producers`)
that the UI stage applies in its single append. It stays in the chain so that `through='gifts'` asks for that producer, and the
independent admission of the delta is the producer re-run on the V4 plus the member checker (`archives.rederive`). `writers()`
gives the stages that run and replay after the UI; `run_stage` and `verify_chain` refuse an archive-only stage.

`controls`, `portable` and `rematches` default to inert and accept activation only through immutable options carrying
candidate-bound runtime evidence. Overlay126 is prepared inert in the UI append; its resident stub and active byte are
installed as a confined mechanical stage after the genuine grant. The final identity stage changes only project-owned
title pixels. The builder clears all participating activation flags together and checks the complete captured inert hash.

`verify_chain` reconstructs the cold UI with explicit zero preimages for retired child slots, native hook preimages and
shared-overlay peeling. Appended activation bytes have fixed owner preimages. It then independently replays every stage.
"""
from collections import namedtuple
from contextlib import nullcontext
from dataclasses import dataclass
from typing import Callable
import hashlib
import json
import re
import struct
import tempfile
import zlib

Region = namedtuple('Region', 'start end label')

IMPLEMENTED = ('moves', 'ai', 'ai-immunities', 'abilities', 'gifts', 'legacy', 'legendary-scenes', 'legendary-scene-version', 'trainer-fixes', 'pokeathlon', 'traded-egg', 'bag-foreign', 'bag-view-position', 'lottery-id', 'battle-tower-wrap', 'battle-animation-facade', 'battle-animation-dynamicpunch', 'battle-animation-helping-hand', 'battle-animation-strength', 'battle-animation-spit-up', 'giratina-pc-form', 'invisible-grass', 'waterfall-facing', 'follower-menu-jump', 'controls', 'portable', 'rematches', 'uturn-flinch', 'identity')
PENDING = {}
ORDER = ('moves', 'ai', 'ai-immunities', 'abilities', 'gifts', 'legacy', 'legendary-scenes', 'legendary-scene-version', 'trainer-fixes', 'pokeathlon', 'traded-egg', 'bag-foreign', 'bag-view-position', 'lottery-id', 'battle-tower-wrap', 'battle-animation-facade', 'battle-animation-dynamicpunch', 'battle-animation-helping-hand', 'battle-animation-strength', 'battle-animation-spit-up', 'giratina-pc-form', 'invisible-grass', 'waterfall-facing', 'follower-menu-jump', 'controls', 'portable', 'rematches', 'uturn-flinch', 'identity')

SCHEMA = 1
RECEIPT_KEYS = {'schema', 'stage', 'language', 'input_sha256', 'output_sha256', 'input_bytes',
                'output_bytes', 'regions', 'changed_ranges', 'stage_receipt', 'stage_receipt_sha256'}
UI_FILES = (27, 54, 156, 167)
RESERVE = (0x023C8000, 0x18000)
MODULE_SEED, RESOURCE_SEED, GUIDE_SEED = 0x023D7B60, 0x023D7BC0, 0x023D7C00
MODULE_MAGIC, GUIDE_MAGIC = 0x314D4955, 0x31435247
HEADER_BYTES = 0x200
# ARM9 words the UI stage writes OUTSIDE the reserve: the template, three UI
# hooks and the four complete HF02 hooks delegated to event_flags.  ui_verify
# replays all of them independently.  A later stage may not claim these spans.
UI_HOOKS = (('Options template', 0x020FA354, 16), ('physical hook', 0x0201A556, 4),
            ('physical lid hook', 0x02000DB0, 4), ('Fieldbook task hook', 0x0203BFE4, 4),
            ('event flags getter hook', 0x0205045C, 8),
            ('event flags loader hook', 0x02027AD4, 8),
            ('event variable getter hook', 0x020403AC, 8),
            ('event SetVar hook', 0x02040F14, 8))
UI_RESERVE_SPANS = (('ui.bridge', 0x023CB800, 12272), ('fieldbook.code', 0x023D4000, 3072),
                    ('training.ui', 0x023D6800, 1536), ('physical.code', 0x023D6E10, 1024),
                    ('event-flags.runtime', 0x023CF900, 1536),
                    ('physical.slot', 0x023D7210, 48), ('settings.descriptor', 0x023CB1A0, 80),
                    ('settings.generation', 0x023CB1F0, 16),
                    ('training delegate bind', 0x023CB130, 4), ('guide.template', 0x023D7B10, 16),
                    ('ui.bootstrap', 0x023D7B20, 40), ('ui.control', 0x023D7B48, 16),
                    ('ui.module.seed', 0x023D7B60, 96), ('ui.resource.seed', 0x023D7BC0, 64),
                    ('ui.guide.seed', 0x023D7C00, 64))
CHUNK = 1 << 16


class CompositionError(ValueError):
    """A post-UI step changed bytes it did not declare, or broke a UI invariant."""


class StagePending(ValueError):
    """The stage is registered but its prerequisites are not delivered; never a silent skip."""

    def __init__(self, stage, reasons):
        self.stage, self.reasons = stage, tuple(reasons)
        super().__init__('unimplemented stage: %s (pending: %s)' % (stage, '; '.join(self.reasons)))


@dataclass(frozen=True)
class MechanicalStage:
    name: str
    apply: Callable          # (data, language) -> (bytes, raw receipt)
    verify: Callable         # (before, after, raw receipt) -> dict, the stage's own reader
    regions: Callable        # (rom) -> list[Region], physical byte spans the stage may change
    slot: str = None         # reserve slot name this stage may write (grant source: reserve.allocate), else None
    slot_payload: int = 0    # > 0: slot stage; bytes asked of reserve.allocate. apply gets row= and work_dir=
    archive_producers: tuple = ()   # archive producers (sgp131/archives.py) whose delta must travel in the UI receipt
    contextual: bool = False  # full reserve receipt and explicit charmap required by owner wrappers
    peel: Callable = None    # (after, before, regions) -> the image without this stage; needed to share a region
    invariants: Callable = None  # exceptional, stage-specific UI invariant reader; default remains check_ui_invariants

    regions_from_final: bool = False  # only fixed module regions depend on the appended FAT address
    cold_preimages: Callable = None   # (V4, final, regions) -> {exact declared (start,end): cold bytes}
    legacy_owners: tuple = ()  # named occupied roots in the legacy map; never unassigned free-space grants
    resident_owners: tuple = ()  # named current 1.3 roots; distinct from the immutable 1.2 legacy snapshot

    def __post_init__(self):
        # archive-only: apply, verify and regions are all absent, the effect is exactly the declared archive producers
        absent = [self.apply is None, self.verify is None, self.regions is None]
        if any(absent) and not all(absent):
            raise ValueError('stage %s: apply, verify and regions are all present or all absent' % self.name)
        if all(absent) and (not self.archive_producers or self.slot or self.slot_payload or self.peel
                            or self.legacy_owners or self.resident_owners):
            raise ValueError('archive-only stage %s needs archive producers and no slot or peel' % self.name)
        if self.slot and (self.legacy_owners or self.resident_owners):
            raise ValueError('stage %s cannot mix a conditional slot with resident reserve owners' % self.name)
        if self.legacy_owners and self.resident_owners:
            raise ValueError('stage %s cannot mix legacy and current resident reserve owners' % self.name)
        if (not isinstance(self.legacy_owners, tuple) or len(set(self.legacy_owners)) != len(self.legacy_owners)
                or any(not isinstance(name, str) or not name for name in self.legacy_owners)):
            raise ValueError('stage %s has invalid legacy reserve owners' % self.name)
        if (not isinstance(self.resident_owners, tuple) or len(set(self.resident_owners)) != len(self.resident_owners)
                or any(not isinstance(name, str) or not name for name in self.resident_owners)):
            raise ValueError('stage %s has invalid current resident reserve owners' % self.name)

    @property
    def archive_only(self):
        return self.apply is None

    @property
    def needs_row(self):
        return bool(self.slot) and self.slot_payload > 0

    @property
    def receipt_stage(self):
        return self.name


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def _fail(message):
    raise CompositionError(message)


def guarded(label, function, *args, wrap_value_errors=False):
    """Run an external reader/writer fail-closed.

    Any exception that is not already a refusal (struct.error on a mutated FNT, KeyError, IndexError, TypeError,
    UnicodeError, OverflowError, ...) becomes a CompositionError. ValueError keeps its own message, because the
    independent verifiers (ui_verify, the 4a readers) explain the refusal with it, unless `wrap_value_errors`.
    """
    try:
        return function(*args)
    except CompositionError:
        raise
    except ValueError as error:
        # UnicodeError is a ValueError subclass but carries no verifier explanation: still a fail-closed wrap
        if wrap_value_errors or isinstance(error, UnicodeError):
            raise CompositionError('fail-closed: %s refused: %s' % (label, error)) from error
        raise
    except Exception as error:  # noqa: BLE001 - deliberate: every unexpected failure is a refusal
        raise CompositionError('fail-closed: %s raised %s: %s' % (label, type(error).__name__, error)) from error


# ------------------------------------------------------------------- byte-level rules

def changed_ranges(a, b):
    """Maximal differing byte ranges between equal-length buffers, as (start, end)."""
    if len(a) != len(b):
        raise ValueError('buffers differ in length')
    found = []
    for base in range(0, len(a), CHUNK):
        if a[base:base + CHUNK] == b[base:base + CHUNK]:
            continue
        for i in range(base, min(base + CHUNK, len(a))):
            if a[i] != b[i]:
                if found and found[-1][1] == i:
                    found[-1] = (found[-1][0], i + 1)
                else:
                    found.append((i, i + 1))
    return found


def _check_regions(regions, size):
    for region in regions:
        if (not isinstance(region, Region) or type(region.start) is not int or type(region.end) is not int
                or not 0 <= region.start < region.end <= size):
            _fail('invalid declared region %r' % (region,))


def require_disjoint(region_lists):
    """Stage regions must be pairwise disjoint, otherwise intermediates cannot be reconstructed."""
    flat = []
    for regions in region_lists:
        for region in regions:
            if region.start >= region.end:
                _fail('empty or invalid declared region %r' % (region,))
            flat.append(region)
    flat.sort()
    for left, right in zip(flat, flat[1:]):
        if right.start < left.end:
            _fail('declared regions overlap: %s and %s' % (left.label, right.label))


def _span(region):
    return region.start, region.end


def check_sharing(stages, declared):
    """Disjoint regions, except that a later stage may re-declare an earlier stage's region byte for byte if it can peel.

    Partial overlaps and sharing without a peel stay refused: without one the intermediate images cannot be rebuilt.
    """
    first, unique = {}, []
    for stage, regions in zip(stages, declared):
        for region in regions:
            if region.start >= region.end:
                _fail('empty or invalid declared region %r' % (region,))
            if _span(region) in first:
                if getattr(stage, 'peel', None) is None:
                    _fail('declared regions overlap: %s and %s' % (first[_span(region)].label, region.label))
            else:
                first[_span(region)] = region
                unique.append(region)
    require_disjoint([unique])


def intermediate_images(before, final, stages, declared):
    """The n+1 images of a chain: the UI image, the output of each stage, `final`; rebuilt from `final` alone.

    Going backwards, a stage that can peel is taken out of its output; any other stage has its declared regions restored from
    the pristine input. The bottom must then be exactly `final` with every declared region restored, so a peel can neither
    leave bytes behind nor touch what is not declared.
    """
    check_sharing(stages, declared)
    overrides = {}
    by_stage = []
    for stage, regions in zip(stages, declared):
        callback = getattr(stage, 'cold_preimages', None)
        local = guarded(stage.name + ' cold preimages', callback, before, final, regions) if callback else {}
        if (type(local) is not dict or any(key not in {_span(r) for r in regions}
                or type(value) is not bytes or len(value) != key[1] - key[0]
                for key, value in local.items())):
            _fail('invalid fixed cold preimages for ' + stage.name)
        for key, value in local.items():
            if key in overrides and overrides[key] != value:
                _fail('inconsistent fixed cold preimages')
            overrides[key] = value
        by_stage.append(local)
    images = [None] * len(stages) + [final]
    for index in range(len(stages), 0, -1):
        stage, regions = stages[index - 1], declared[index - 1]
        peel = getattr(stage, 'peel', None)
        if peel is None:
            images[index - 1] = _restore(images[index], before, regions, by_stage[index-1])
            continue
        peeled = guarded(stage.name + ' peel', peel, images[index], before, regions)
        if type(peeled) is not bytes or len(peeled) != len(final):
            _fail('%s peel returned a mutable, non-bytes or resized ROM' % stage.name)
        images[index - 1] = peeled
    if images[0] != _restore(final, before, [r for regions in declared for r in regions], overrides):
        _fail('the chain does not peel back to the cold UI: a stage left bytes behind or touched undeclared ones')
    return images


def check_confined(prev, nxt, regions, label='stage'):
    """Equal length and every changed byte inside the declared regions."""
    if len(prev) != len(nxt):
        _fail('%s changed the ROM length (%d -> %d)' % (label, len(prev), len(nxt)))
    _check_regions(regions, len(prev))
    for start, end in changed_ranges(prev, nxt):
        if not any(r.start <= start and end <= r.end for r in regions):
            _fail('%s changed bytes outside declared regions: %#x..%#x' % (label, start, end))


# ---------------------------------------------------------- structured UI image rules

def _image(rom):
    from . import ui_verify
    if type(rom) is not bytes:
        _fail('exact immutable ROM bytes required')
    return guarded('cartridge reader', ui_verify.Image, rom, wrap_value_errors=True)


def ui_seed_state(rom):
    """Seed words read from the ARM9 mapped bytes next to the cartridge values they must match."""
    image = _image(rom)
    module = struct.unpack('<24I', image.arm(MODULE_SEED, 96))
    guide = struct.unpack('<16I', image.arm(GUIDE_SEED, 64))
    return image, module, guide


def check_ui_seeds(rom):
    """Self-consistency of the three UI seeds with the cartridge, as the runtime compares them."""
    image, module, guide = ui_seed_state(rom)
    if module[0] != MODULE_MAGIC or guide[0] != GUIDE_MAGIC:
        _fail('input is not a UI image: seed magic missing')
    y9 = image.chunk(image.y9, image.y9_bytes)
    expected = {
        'ui.module.seed crc32(y9)': (module[17], zlib.crc32(y9)),
        'ui.module.seed y9 offset': (module[18], image.y9),
        'ui.module.seed y9 length': (module[19], image.y9_bytes),
        'ui.module.seed ROM length': (module[20], len(rom)),
        'ui.module.seed FAT 54': (tuple(module[21:23]), tuple(image.files[54])),
        'ui.guide.seed file id': (guide[4], 156),
        'ui.guide.seed FAT 156': (tuple(guide[5:7]), tuple(image.files[156])),
        'ui.guide.seed ROM length': (guide[7], len(rom)),
        'ui.guide.seed file 156 length': (guide[8], image.files[156][1] - image.files[156][0]),
        'header ROM length 0x80': (struct.unpack_from('<I', rom, 0x80)[0], len(rom)),
    }
    for label, (seed, actual) in expected.items():
        if seed != actual:
            _fail('%s no longer matches the cartridge: seed %r, actual %r' % (label, seed, actual))
    return {'y9_crc32': '%08x' % zlib.crc32(y9), 'rom_bytes': len(rom),
            'fat54': list(image.files[54]), 'fat156': list(image.files[156])}


def _protected(image):
    spans = [Region(0, HEADER_BYTES, 'header'),
             Region(image.fat, image.fat + image.fat_bytes, 'FAT table'),
             Region(image.y9, image.y9 + image.y9_bytes, 'y9 table')]
    spans += [Region(*image.files[f], 'UI file %d' % f) for f in UI_FILES]
    spans += [Region(image.offset(address, size), image.offset(address, size) + size, 'UI hook ' + label)
              for label, address, size in UI_HOOKS]
    spans.append(Region(image.offset(*RESERVE), image.offset(*RESERVE) + RESERVE[1], 'resident reserve'))
    return spans


def reserve_grants(rom, stage_name, slot, allocation):
    """Physical spans of the reserve that `stage_name` may change: the one `reserve.allocate` row named `slot`.

    The grant is the full slot capacity (never the payload size, never a neighbour), must lie inside the
    reserve and must not overlap anything the UI stage writes. No row for the slot means no grant.
    """
    if isinstance(allocation, dict):
        allocation = allocation.get('assignments')
    if not isinstance(allocation, (list, tuple)):
        _fail('invalid reserve grant: allocation must contain reserve.allocate assignment rows')
    rows = [r for r in allocation if isinstance(r, dict) and r.get('name') == slot]
    if not rows:
        return ()
    if len(rows) != 1:
        _fail('invalid reserve grant: more than one row for slot %s' % slot)
    row = rows[0]
    start, nbytes, capacity = row.get('start'), row.get('bytes'), row.get('capacity')
    if (any(type(v) is not int for v in (start, nbytes, capacity)) or not 0 < nbytes <= capacity):
        _fail('invalid reserve grant for %s: %r' % (slot, row))
    base, size = RESERVE
    if start < base or start + capacity > base + size:
        _fail('reserve grant for %s lies outside the reserve: %#x+%d' % (slot, start, capacity))
    for label, address, length in UI_RESERVE_SPANS:
        if start < address + length and address < start + capacity:
            _fail('reserve grant for %s overlaps UI-written bytes (%s)' % (slot, label))
    image = _image(rom)
    at = image.offset(start, capacity)
    return (Region(at, at + capacity, 'reserve:' + slot),)


def legacy_owner_grants(rom, stage_name, names):
    """Physical grants for named occupied roots in the legacy ownership map.

    These are not allocations and cannot authorize an unowned/free span.  The
    reviewed map must contain each name exactly once in ``legacy_owners``;
    confinement still limits the writer to its smaller declared regions.
    """
    if not names:
        return ()
    try:
        from . import reserve
        policy = json.loads(reserve.MAP.read_text())
        owners = policy['legacy_owners']
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as error:
        raise CompositionError('fail-closed: reserve legacy owners unreadable: %s' % error) from error
    if not isinstance(owners, list):
        _fail('reserve legacy owners are not a list')
    image = _image(rom)
    grants = []
    for name in names:
        found = [row for row in owners if isinstance(row, dict) and row.get('name') == name]
        if len(found) != 1:
            _fail('legacy reserve owner %s is missing or duplicated' % name)
        row = found[0]
        start, capacity = row.get('start'), row.get('bytes')
        if (type(start) is not int or type(capacity) is not int or capacity <= 0
                or start < RESERVE[0] or start + capacity > RESERVE[0] + RESERVE[1]
                or not isinstance(row.get('owner'), str) or row['owner'] in ('', '(nessuno)')):
            _fail('legacy reserve owner %s is invalid' % name)
        for label, address, length in UI_RESERVE_SPANS:
            if start < address + length and address < start + capacity:
                _fail('legacy reserve owner %s overlaps UI-written bytes (%s)' % (name, label))
        at = image.offset(start, capacity)
        grants.append(Region(at, at + capacity, 'legacy-reserve:%s:%s' % (stage_name, name)))
    return tuple(grants)


def resident_owner_grants(rom, stage_name, names):
    """Physical grants for named, occupied roots in the current 1.3 reserve map.

    Unlike ``legacy_owner_grants``, these names come from the fixed ``roots``
    partition.  Only reserved roots owned by a real producer are eligible;
    guards, retained legacy space, metadata and unowned/free spans are not.
    """
    if not names:
        return ()
    try:
        from . import reserve
        policy = json.loads(reserve.MAP.read_text())
        roots = policy['roots']
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as error:
        raise CompositionError('fail-closed: reserve resident roots unreadable: %s' % error) from error
    if not isinstance(roots, list):
        _fail('reserve resident roots are not a list')
    image = _image(rom)
    grants = []
    for name in names:
        found = [row for row in roots if isinstance(row, dict) and row.get('name') == name]
        if len(found) != 1:
            _fail('resident reserve owner %s is missing or duplicated' % name)
        row = found[0]
        start, capacity = row.get('start'), row.get('bytes')
        if (type(start) is not int or type(capacity) is not int or capacity <= 0
                or start < RESERVE[0] or start + capacity > RESERVE[0] + RESERVE[1]
                or row.get('kind') != 'reserved'
                or not isinstance(row.get('owner'), str) or row['owner'] in ('', '(nessuno)')):
            _fail('resident reserve owner %s is invalid' % name)
        for label, address, length in UI_RESERVE_SPANS:
            if start < address + length and address < start + capacity:
                _fail('resident reserve owner %s overlaps UI-written bytes (%s)' % (name, label))
        at = image.offset(start, capacity)
        grants.append(Region(at, at + capacity, 'resident-reserve:%s:%s' % (stage_name, name)))
    return tuple(grants)


def reserve_slot(slot):
    """(parent, part) of the payload `slot` in the real reserve map, read from the policy file itself."""
    from . import reserve
    try:
        policy = json.loads(reserve.MAP.read_text())
        found = [(entry['parent'], part) for entry in policy['subdivisions'] for part in entry['parts']
                 if part.get('name') == slot and part.get('kind') == 'payload']
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as error:
        raise CompositionError('fail-closed: reserve map unreadable: %s' % error) from error
    if len(found) != 1:
        _fail('%s is not a payload slot of the reserve map' % slot)
    return found[0]


def _unproven(slot, detail):
    return CompositionError('reserve condition not proven: %s: %s' % (reserve_slot(slot)[0], detail))


def assigned_row(stage, allocation):
    """The one `reserve.allocate` row of a slot stage, checked against the map assignment it must equal.

    No row is a refusal that names the unproven condition; a row that moves, widens or renames the map slot is a refusal too.
    """
    slot = stage.slot
    _, part = reserve_slot(slot)
    if isinstance(allocation, dict):
        allocation = allocation.get('assignments')
    if allocation is not None and not isinstance(allocation, (list, tuple)):
        _fail('invalid reserve grant: allocation must be a list of reserve.allocate assignment rows')
    rows = [r for r in (allocation or ()) if isinstance(r, dict) and r.get('name') == slot]
    if not rows:
        raise _unproven(slot, 'no reserve.allocate assignment row for %s (run_stage allocation=, verify_chain allocation=)' % slot)
    if len(rows) != 1:
        _fail('invalid reserve grant: more than one row for slot %s' % slot)
    row = rows[0]
    start, nbytes, capacity = row.get('start'), row.get('bytes'), row.get('capacity')
    if any(type(v) is not int for v in (start, nbytes, capacity)) or not 0 < nbytes <= capacity:
        _fail('invalid reserve grant for %s: %r' % (slot, row))
    if (start, capacity) != (part['start'], part['bytes']):
        _fail('reserve grant for %s differs from the reserve map: %#x+%d, map %#x+%d'
              % (slot, start, capacity, part['start'], part['bytes']))
    if nbytes < stage.slot_payload:
        _fail('reserve grant for %s holds %d bytes, the payload needs %d' % (slot, nbytes, stage.slot_payload))
    return row


def resolve_allocation(base, names, allocation=None, registry=None, *, installed_ui=None,
                       charmap=None, work_dir=None, archive_deltas=(), overlay_deltas=()):
    """Reissue production grants against the exact cold UI; retain explicit abilities-only row fixtures.

    A full receipt is downstream provenance, never authority. Reissue it from immutable base+cold UI
    and the independently verified installer context, then require exact equality. Row-only substitutes
    remain explicitly caller-supplied for the preexisting abilities tests, and cannot reach c8 owners.
    """
    stages = [require_stage(name, registry) for name in names]
    needing = [stage for stage in stages if getattr(stage, 'slot_payload', 0) > 0]
    if not needing:
        if allocation is not None:
            raise ValueError('an allocation was given but no stage of this chain consumes a reserve slot')
        return None, None
    if allocation is not None and not isinstance(allocation, dict):
        if any(getattr(stage, 'contextual', False) for stage in needing):
            _fail('c8 owners require the full reserve allocation receipt, never assignment rows alone')
        for stage in needing:
            assigned_row(stage, allocation)
        return allocation, 'caller-supplied'
    from . import reserve
    requested = ({stage.slot: stage.slot_payload for stage in needing} if allocation is None
                 else allocation.get('requested'))
    if not isinstance(requested, dict):
        _fail('full reserve allocation receipt requires requested payloads')
    parents = ', '.join(sorted({reserve_slot(stage.slot)[0] for stage in needing}))
    try:
        conditional = any(stage.slot in reserve.FINAL_GUIDE_SLOTS for stage in needing)
        kwargs = (dict(installed_ui=installed_ui, charmap=charmap, work_dir=work_dir,
                       archive_deltas=archive_deltas, overlay_deltas=overlay_deltas)
                  if conditional and installed_ui is not None else {})
        fresh = reserve.allocate(base, requested, **kwargs)
    except CompositionError:
        raise
    except Exception as error:
        raise CompositionError('reserve condition not proven: %s: reserve.allocate refused (%s)' % (parents, error)) from error
    if allocation is not None and canonical(allocation) != canonical(fresh):
        _fail('supplied full reserve allocation differs from the freshly reissued cold UI grant')
    for stage in needing:
        assigned_row(stage, fresh)
    return fresh, 'reserve.allocate' if allocation is None else 'reserve.allocate-rederived'



def writers(names, registry=None):
    """The named stages that run and replay after the UI (the archive-only ones have no post-UI writer)."""
    return tuple(name for name in names if not getattr(require_stage(name, registry), 'archive_only', False))


def required_producers(names, registry=None):
    """Archive producers the named stages need in the UI receipt (the text of a stage travels as a delta)."""
    found = set()
    for name in names:
        found.update(getattr(require_stage(name, registry), 'archive_producers', ()))
    return tuple(sorted(found))


def _inside(span, grants):
    return any(g.start <= span[0] and span[1] <= g.end for g in grants)


def check_ui_invariants(prev, nxt, regions, grants=()):
    """Named post-UI invariants, checked before the generic confinement for precise errors.

    `regions` are the physical spans the stage declared; they must not touch the container, UI files,
    UI hooks, UI seeds or the reserve. The one exception is a reserve span fully inside `grants`
    (see `reserve_grants`): only that stage, only those slot bytes.
    """
    if len(prev) != len(nxt):
        _fail('ROM length changed (%d -> %d): header 0x80 and ui seeds would desynchronise'
              % (len(prev), len(nxt)))
    if prev[:HEADER_BYTES] != nxt[:HEADER_BYTES]:
        _fail('ROM header changed (ROM length 0x80 or CRC16 0x15E)')
    old, new = _image(prev), _image(nxt)
    _check_regions(regions, len(prev))
    if old.chunk(old.y9, old.y9_bytes) != new.chunk(new.y9, new.y9_bytes):
        _fail('y9 table changed: ui.module.seed crc32(y9) would no longer match')
    for fid in UI_FILES:
        if old.files[fid] != new.files[fid]:
            _fail('FAT entry %d changed: ui seeds pin file %d' % (fid, fid))
    if old.chunk(old.fat, old.fat_bytes) != new.chunk(new.fat, new.fat_bytes):
        _fail('FAT table changed')
    for name, address, size in (('ui.module.seed', MODULE_SEED, 96), ('ui.resource.seed', RESOURCE_SEED, 64),
                                ('ui.guide.seed', GUIDE_SEED, 64)):
        if old.arm(address, size) != new.arm(address, size):
            _fail('%s changed' % name)
    for label, address, size in UI_HOOKS:
        if old.arm(address, size) != new.arm(address, size):
            _fail('UI hook %s changed (%#x)' % (label, address))
    for fid in UI_FILES:
        if old.file(fid) != new.file(fid):
            _fail('UI-owned file %d bytes changed' % fid)
    protected = _protected(old)
    reserve = protected[-1]
    grants = list(grants)
    for region in regions:
        for guard in protected:
            if region.start < guard.end and guard.start < region.end:
                if guard is reserve and _inside((region.start, region.end), grants):
                    continue
                _fail('declared region %s overlaps protected %s' % (region.label, guard.label))
    for start, end in changed_ranges(prev, nxt):
        if reserve.start < end and start < reserve.end and not _inside((start, end), grants):
            _fail('resident reserve modified outside a declared slot: %#x..%#x' % (start, end))
    return check_ui_seeds(nxt)


# --------------------------------------------------------------------------- registry

def _file_id(image, name):
    from ndspy import fnt
    return fnt.load(image.chunk(image.fnt, image.fnt_bytes)).idOf(name)


def _moves_apply(data, language):
    from . import modern_moves
    return modern_moves.apply(data, language)


def _moves_verify(before, after, receipt):
    from . import modern_moves
    return modern_moves.verify(before, after, receipt)


def _moves_regions(rom):
    image = _image(rom)
    fid = _file_id(image, 'a/0/1/1')
    if fid != 140:
        _fail('a/0/1/1 is not file 140')
    return [Region(*image.files[fid], 'a/0/1/1 slot (file 140)')]


FAIRY_AI_SLOT = 'fairy-ai.code'
FAIRY_AI_PAYLOAD_BYTES = 148


def _fairy_ai_slot(rom, row=None):
    """The fixed SG-AI01 owner and its independently expected zero preimage."""
    _, part = reserve_slot(FAIRY_AI_SLOT)
    start, capacity = (part['start'], part['bytes']) if row is None else (row['start'], row['capacity'])
    _image(rom).offset(start, capacity)
    return {'name': FAIRY_AI_SLOT, 'start': start, 'bytes': capacity,
            'preimage_sha256': _sha(bytes(capacity))}


def _ai_apply(data, language, *, row, work_dir):
    from . import ai_scoring, fairy_ai, type_chart
    first, scoring = ai_scoring.apply(data, language)
    second, chart = type_chart.apply(first, language)
    result, fairy = fairy_ai.apply_code(
        second, language, work_dir, slot=_fairy_ai_slot(second, row))
    return result, {
        'stage': 'ai', 'language': language,
        'input_sha256': _sha(data), 'output_sha256': _sha(result),
        'ai_scoring': scoring, 'damage_chart': chart, 'fairy_ai': fairy,
    }


def _ai_verify(before, after, receipt):
    from . import ai_scoring, fairy_ai, type_chart
    if not isinstance(receipt, dict) or receipt.get('input_sha256') != _sha(before) \
            or receipt.get('output_sha256') != _sha(after):
        _fail('combined AI/damage receipt hashes differ')
    intermediate, expected_scoring = ai_scoring.apply(before, receipt.get('language'))
    chart_image, expected_chart = type_chart.apply(intermediate, receipt.get('language'))
    import tempfile
    with tempfile.TemporaryDirectory(prefix='fairy-ai-replay-') as directory:
        result, expected_fairy = fairy_ai.apply_code(
            chart_image, receipt.get('language'), directory,
            slot=_fairy_ai_slot(chart_image))
    if result != after or canonical(receipt.get('ai_scoring')) != canonical(expected_scoring) \
            or canonical(receipt.get('damage_chart')) != canonical(expected_chart) \
            or canonical(receipt.get('fairy_ai')) != canonical(expected_fairy):
        _fail('combined AI/damage replay differs')
    scoring = ai_scoring.verify(before, intermediate, receipt['ai_scoring'])
    chart = type_chart.verify(intermediate, chart_image, receipt['damage_chart'])
    fairy = fairy_ai.verify_code(chart_image, after, receipt['fairy_ai'])
    return {'ok': True, 'ai_scoring': scoring, 'damage_chart': chart, 'fairy_ai': fairy}


def _ai_regions(rom):
    image = _image(rom)
    _, part = reserve_slot(FAIRY_AI_SLOT)
    at = image.offset(part['start'], part['bytes'])
    regions = [Region(at, at + part['bytes'], 'reserve:' + FAIRY_AI_SLOT)]
    for overlay in (12, 18):
        fid = image.records[overlay][6]
        if fid != overlay:
            _fail('overlay %d is not file %d' % (overlay, overlay))
        start, end = image.files[fid]
        if overlay == 12:
            end = min([a for a, _ in image.files if a > start] + [len(rom)])
        regions.append(Region(start, end, 'overlay %d slot (file %d)' % (overlay, overlay)))
    regions += [
        Region(image.fat + 12 * 8, image.fat + 13 * 8, 'overlay 12 FAT entry'),
        Region(image.y9 + 12 * 32 + 28, image.y9 + 13 * 32, 'overlay 12 y9 size word'),
        Region(image.offset(MODULE_SEED + 68, 4), image.offset(MODULE_SEED + 68, 4) + 4,
               'ui.module.seed derived y9 crc32'),
    ]
    return regions


def check_ai_ui_invariants(prev, nxt, regions, grants=()):
    """Allow SG-AI01's overlay-12 size delta and its one derived UI seed.

    This is deliberately narrower than the general post-UI rule: only FAT 12's
    end, y9 row 12's size word and Module96 word 17 may differ.  Every other
    container, seed, hook and UI-owned byte remains byte-identical.
    """
    if len(prev) != len(nxt) or prev[:HEADER_BYTES] != nxt[:HEADER_BYTES]:
        _fail('Fairy AI changed ROM length or header')
    old, new = _image(prev), _image(nxt)
    _check_regions(regions, len(prev))
    if (old.fat, old.fat_bytes, old.y9, old.y9_bytes) != (new.fat, new.fat_bytes, new.y9, new.y9_bytes):
        _fail('Fairy AI changed FAT/y9 placement')
    fat12 = (old.fat + 12 * 8, old.fat + 13 * 8)
    y912 = (old.y9 + 12 * 32 + 28, old.y9 + 13 * 32)
    if prev[old.fat:fat12[0]] != nxt[new.fat:fat12[0]] \
            or prev[fat12[1]:old.fat + old.fat_bytes] != nxt[fat12[1]:new.fat + new.fat_bytes]:
        _fail('Fairy AI changed a foreign FAT entry')
    if prev[old.y9:y912[0]] != nxt[new.y9:y912[0]] \
            or prev[y912[1]:old.y9 + old.y9_bytes] != nxt[y912[1]:new.y9 + new.y9_bytes]:
        _fail('Fairy AI changed a foreign y9 byte')
    old_row, new_row = old.records[12], new.records[12]
    if old_row[:7] != new_row[:7] or old_row[7] >> 24 != new_row[7] >> 24:
        _fail('Fairy AI changed overlay 12 geometry or flags beyond compressed size')
    if old.files[12][0] != new.files[12][0] or new.files[12][1] <= old.files[12][0]:
        _fail('Fairy AI moved or emptied overlay 12')
    for fid in UI_FILES:
        if old.files[fid] != new.files[fid] or old.file(fid) != new.file(fid):
            _fail('Fairy AI changed UI-owned file %d' % fid)
    seed_at = old.offset(MODULE_SEED, 96)
    if seed_at != new.offset(MODULE_SEED, 96) \
            or prev[seed_at:seed_at + 68] != nxt[seed_at:seed_at + 68] \
            or prev[seed_at + 72:seed_at + 96] != nxt[seed_at + 72:seed_at + 96]:
        _fail('Fairy AI changed ui.module.seed outside derived y9 crc32')
    for name, address, size in (('ui.resource.seed', RESOURCE_SEED, 64), ('ui.guide.seed', GUIDE_SEED, 64)):
        if old.arm(address, size) != new.arm(address, size):
            _fail('Fairy AI changed ' + name)
    for label, address, size in UI_HOOKS:
        if old.arm(address, size) != new.arm(address, size):
            _fail('Fairy AI changed UI hook ' + label)
    reserve_span = Region(old.offset(*RESERVE), old.offset(*RESERVE) + RESERVE[1], 'resident reserve')
    seed_crc_span = (seed_at + 68, seed_at + 72)
    grants = list(grants)
    for start, end in changed_ranges(prev, nxt):
        if (reserve_span.start < end and start < reserve_span.end
                and not (seed_crc_span[0] <= start and end <= seed_crc_span[1])
                and not _inside((start, end), grants)):
            _fail('Fairy AI modified resident reserve outside its grant')
    return check_ui_seeds(nxt)


def _cold_mechanical_y9_crc(before, final):
    """Cold-UI y9 CRC with all registered size-changing mechanics removed."""
    old, current = _image(before), _image(final)
    if (old.y9, old.y9_bytes) != (current.y9, current.y9_bytes):
        _fail('cold mechanical y9 placement differs')
    cold_y9 = bytearray(current.chunk(current.y9, current.y9_bytes))
    for overlay, fields in ((12, ((28, 32),)),
                            (95, ((8, 12), (28, 32)))):
        row = overlay * 32
        for start, end in fields:
            cold_y9[row + start:row + end] = old.chunk(
                old.y9 + row + start, end - start)
    return struct.pack('<I', zlib.crc32(cold_y9))


def _ai_cold(before, final, regions):
    result = _cold_slot(FAIRY_AI_SLOT)(before, final, regions)
    seed = [r for r in regions if r.label == 'ui.module.seed derived y9 crc32']
    if len(seed) != 1:
        _fail('Fairy AI cold seed declaration differs')
    result[_span(seed[0])] = _cold_mechanical_y9_crc(before, final)
    return result


def _ai_peel(after, before, regions):
    """Remove the combined AI stage and rebuild the exact cold-UI y9 seed."""
    out = bytearray(after)
    old = _image(before)
    for region in regions:
        if region.label == 'ui.module.seed derived y9 crc32':
            continue
        if region.label.startswith('reserve:'):
            out[region.start:region.end] = bytes(region.end - region.start)
        else:
            out[region.start:region.end] = before[region.start:region.end]
    struct.pack_into('<I', out, [r.start for r in regions
                                if r.label == 'ui.module.seed derived y9 crc32'][0],
                     zlib.crc32(out[old.y9:old.y9 + old.y9_bytes]))
    return bytes(out)


def _ai_immunities_apply(data, language):
    from . import ai_scoring
    return ai_scoring.apply_dry_skin(data, language)


def _ai_immunities_verify(before, after, receipt):
    from . import ai_scoring
    return ai_scoring.verify_dry_skin(before, after, receipt)


def _ai_immunities_regions(rom):
    image = _image(rom)
    overlay_file = image.records[10][6]
    if overlay_file != 10:
        _fail('overlay 10 is not file 10')
    archive_file = _file_id(image, 'a/0/9/9')
    if archive_file != 228:
        _fail('a/0/9/9 is not file 228')
    return [Region(*image.files[overlay_file], 'overlay 10 slot (file 10)'),
            Region(*image.files[archive_file], 'a/0/9/9 slot (file 228)')]


def _legacy_apply(data, language):
    from . import legacy_native
    return legacy_native.apply(data, language)


def _legacy_verify(before, after, receipt):
    from . import legacy_native
    return legacy_native.verify(before, after, receipt)


def _legacy_regions(rom):
    image = _image(rom)
    regions = []
    for overlay in (2, 101):
        if image.records[overlay][6] != overlay:
            _fail('legacy overlay/file identity differs')
        regions.append(Region(*image.files[overlay], 'legacy overlay %d slot' % overlay))
    at = image.offset(0x0202CE0E, 2)
    from . import (bag_alloc, gb_sounds_evolution, plus_save,
                   pokegear_autocull, soul_dew, wonder_card)
    save_ranges = plus_save.spans(rom)
    return regions + [Region(at, at + 2, 'native IGT comparison'),
                      *[Region(start, end, 'Soul Dew getter/slot')
                        for start, end in soul_dew.spans(rom)],
                      *[Region(start, end, 'Wonder Card decoration guard')
                        for start, end in wonder_card.spans(rom)],
                      *[Region(start, end, 'GB evolution audio reload')
                        for start, end in gb_sounds_evolution.spans(rom)],
                      Region(image.offset(pokegear_autocull.SLOT,
                                          pokegear_autocull.SLOT_BYTES),
                             image.offset(pokegear_autocull.SLOT,
                                          pokegear_autocull.SLOT_BYTES)
                             + pokegear_autocull.SLOT_BYTES,
                             'Pokégear AutoCull resident thunk'),
                      Region(*save_ranges[0], 'Plus save compartment'),
                      Region(*save_ranges[1], 'Plus save hook'),
                      Region(*bag_alloc.span(rom), 'expanded Bag constructor')]


ABILITIES_SLOT = 'modern-accuracy.code'
ABILITIES_PAYLOAD_BYTES = 28      # payload SHA 9370a524..., asserted by modern_abilities.compile_native


def _abilities_slot(rom, row=None):
    """The fixed map slot and independently expected zero preimage after cold Guide retirement."""
    _, part = reserve_slot(ABILITIES_SLOT)
    start, capacity = (part['start'], part['bytes']) if row is None else (row['start'], row['capacity'])
    at = _image(rom).offset(start, capacity)
    return {'name': ABILITIES_SLOT, 'start': start, 'bytes': capacity, 'preimage_sha256': _sha(bytes(capacity))}


def _abilities_apply(data, language, *, row, work_dir):
    from . import modern_abilities
    return modern_abilities.apply_code(data, language, work_dir, slot=_abilities_slot(data, row))


def _abilities_verify(before, after, receipt):
    from . import modern_abilities
    if not isinstance(receipt, dict) or receipt.get('slot') != _abilities_slot(before):
        _fail('abilities receipt names a slot that is not the reserve map assignment over the input bytes')
    return modern_abilities.verify_code(before, after, receipt)


def _abilities_regions(rom):
    image = _image(rom)
    _, part = reserve_slot(ABILITIES_SLOT)
    at = image.offset(part['start'], part['bytes'])
    fid = image.records[12][6]
    if fid != 12:
        _fail('overlay 12 is not file 12')
    start = image.files[fid][0]
    capacity_end = min([a for a, _ in image.files if a > start] + [len(rom)])
    return [Region(at, at + part['bytes'], 'reserve:' + ABILITIES_SLOT),
            Region(start, capacity_end, 'overlay 12 slot (file 12)')]


def _abilities_peel(after, before, regions):
    """`after` without this stage: reserve slot back to the pristine bytes, the seam back to the original in overlay 12.

    The overlay is decoded, the six seam bytes reverted from the stage's own pinned constants and the stream written back
    with the canonical writer at the FAT length, exactly how `ai` and `abilities` write it.
    """
    from sgp12.blz import blz_comprimi_ottimo
    from sgp12.rom import Rom
    from . import modern_abilities as ma
    out = bytearray(after)
    overlay = None
    for region in regions:
        if region.label.startswith('reserve:'):
            out[region.start:region.end] = bytes(region.end - region.start)
        else:
            overlay = region
    if overlay is None:
        _fail('abilities peel needs the overlay 12 region')
    site = ma.SITE - ma.OV12_BASE
    logical = bytearray(Rom(after).immagine_overlay(12)[2])
    slot_start = reserve_slot(ABILITIES_SLOT)[1]['start']
    if bytes(logical[site:site + 6]) != ma.seam_bytes(slot_start):
        _fail('overlay 12 does not carry the abilities seam')
    logical[site:site + 6] = ma.SEAM_BEFORE
    current = _image(after)
    target = current.files[12][1] - current.files[12][0]
    stream = blz_comprimi_ottimo(bytes(logical), bersaglio=target)
    if len(stream) != target:
        _fail('peeled overlay 12 does not fit its FAT slot')
    out[overlay.start:overlay.start + target] = stream
    return bytes(out)


def _cold_slot(slot):
    def preimages(before, final, regions):
        image = _image(final)
        _, part = reserve_slot(slot)
        expected = (image.offset(part['start'], part['bytes']), part['bytes'])
        matched = [r for r in regions if r.label == 'reserve:' + slot]
        if len(matched) != 1 or (matched[0].start, matched[0].end-matched[0].start) != expected:
            _fail('cold reserve declaration differs from fixed map slot')
        return {_span(matched[0]): bytes(part['bytes'])}
    return preimages


def required_overlay_producers(names):
    return ('rematches-module',) if 'rematches' in names else ()


def _rematches_regions(rom):
    from . import rematches
    image = _image(rom)
    _, part = reserve_slot(rematches.SLOT_NAME)
    start, end = image.files[126]
    offset = rematches.DEFAULT_CODE_SIZE + rematches.ACTIVE_BYTE
    if end-start != rematches.DEFAULT_CODE_SIZE+rematches.DEFAULT_CONFIG_SIZE or start+offset >= end:
        _fail('rematches requires its fixed UI-appended module before declaration')
    stub = image.offset(part['start'], 64)
    seam = image.offset(int(rematches.load_abi()['seam']['address'], 16), 4)
    return [Region(stub,stub+64,'reserve:c8.module-stubs'),
            Region(seam,seam+4,'rematches native-reader seam'),
            Region(start+offset,start+offset+1,'rematches activation byte')]


def _rematches_cold(before, final, regions):
    expected = _rematches_regions(final)
    if regions != expected:
        _fail('rematches cold preimages require exact fixed regions')
    return {_span(expected[0]): bytes(64), _span(expected[2]): b'\0'}


def _rematches_delta(overlay_deltas, language):
    from . import cartridge_deltas as cd
    values = tuple(overlay_deltas or ())
    if len(values) != 1 or type(values[0]) is not cd.OverlayDelta:
        _fail('rematches requires the one V4-derived overlay delta')
    delta = values[0]
    from . import baseline
    if baseline.INPUT_HASHES.get(delta.input_sha256) != language:
        _fail('rematches overlay delta input/language differs')
    return delta


def _rematches_apply(data, language, *, allocation, charmap, work_dir, stage_options=None,
                     overlay_deltas=()):
    from . import cartridge_deltas as cd
    delta = _rematches_delta(overlay_deltas, language)
    return cd.install_prepared(data, language, work_dir, delta, allocation=allocation, stage_options=stage_options)


def _rematches_verify(before, after, receipt, *, charmap, stage_options=None, overlay_deltas=()):
    from . import cartridge_deltas as cd, activation
    activation.check_owner_options('rematches', receipt, stage_options, receipt.get('language'))
    delta = _rematches_delta(overlay_deltas, receipt.get('language'))
    with tempfile.TemporaryDirectory(prefix='rematches-stage-verify-') as scratch:
        return cd.verify_prepared(before, after, receipt, scratch, stage_options=stage_options, delta=delta)


def _rematches_peel(after, before, regions):
    from . import baseline, cartridge_deltas as cd, rematches
    if regions != _rematches_regions(after):
        _fail('rematches peel declaration differs from fixed module geometry')
    stub, seam, active = regions
    if after[active.start:active.end] not in (b'\0', b'\1'):
        _fail('rematches peel activation byte is not boolean')
    abi = rematches.load_abi()
    expected_seam = bytes.fromhex(abi['seam']['old_bytes'])
    if before[seam.start:seam.end] != expected_seam:
        _fail('rematches native seam preimage differs')
    out = bytearray(after)
    out[stub.start:stub.end] = bytes(64)
    out[seam.start:seam.end] = expected_seam
    out[active.start:active.end] = b'\0'
    language = baseline.identify(before)
    with tempfile.TemporaryDirectory(prefix='rematches-stage-peel-') as scratch:
        delta = cd.derive_rematches(before, language, scratch)
    image, row, writes = delta.image, delta.row, delta.resident_writes
    current = _image(after)
    module = bytearray(current.file(126))
    module[rematches.DEFAULT_CODE_SIZE + rematches.ACTIVE_BYTE] = 0
    if current.records[126] != row or bytes(module) != image:
        _fail('rematches peel module differs from fixed inert compilation')
    for address, original, authored in writes:
        if current.arm(address,len(authored)) != authored:
            _fail('rematches peel resident bytes differ from fixed compilation')
    return bytes(out)


def _uturn_apply(data, language, *, allocation, charmap, work_dir,
                 stage_options=None):
    from . import uturn_flinch
    return uturn_flinch.install(
        data, language, work_dir, allocation=allocation)


def _uturn_verify(before, after, receipt, *, charmap, stage_options=None):
    from . import uturn_flinch
    return uturn_flinch.verify_install(before, after, receipt)


def _uturn_regions(rom):
    from . import uturn_flinch
    image = _image(rom)
    helper = image.offset(uturn_flinch.HELPER_ADDRESS,
                          uturn_flinch.HELPER_CAPACITY)
    fid = image.records[12][6]
    if fid != 12:
        _fail('overlay 12 is not file 12')
    start = image.files[fid][0]
    capacity_end = min([a for a, _ in image.files if a > start] + [len(rom)])
    return [
        Region(helper, helper + uturn_flinch.HELPER_CAPACITY,
               'reserve:c8.module-stubs tail'),
        Region(start, capacity_end, 'overlay 12 slot (file 12)'),
        Region(image.fat + 12 * 8, image.fat + 13 * 8,
               'overlay 12 FAT entry'),
        Region(image.y9 + 12 * 32 + 28, image.y9 + 13 * 32,
               'overlay 12 y9 size word'),
        Region(image.offset(MODULE_SEED + 68, 4),
               image.offset(MODULE_SEED + 68, 4) + 4,
               'ui.module.seed derived y9 crc32'),
    ]


def _uturn_peel(after, before, regions):
    from . import uturn_flinch
    result = uturn_flinch.uninstall(after)
    check_confined(after, result, regions, 'uturn-flinch peel')
    return result


# Owner wrappers preserve inert defaults and bind active materialization to explicit runtime evidence.
def _owner_regions(rom, slot, hooks):
    image = _image(rom)
    _, part = reserve_slot(slot)
    at = image.offset(part['start'], part['bytes'])
    return [Region(at, at + part['bytes'], 'reserve:' + slot)] + [
        Region(image.offset(address, size), image.offset(address, size) + size, label)
        for address, size, label in hooks]


def _controls_regions(rom):
    from . import controls
    return _owner_regions(rom, controls.SLOT_NAME,
                          [(controls.hex_int(site), 4, 'controls hook ' + site) for site, _, _ in controls.SITES])


def _portable_regions(rom):
    from . import portable
    hooks = [(site, 4, 'portable hook ' + name) for name, site, _, _ in portable.BL_HOOKS]
    hooks.append((portable.CALLBACK, 8, 'portable callback entry'))
    return _owner_regions(rom, portable.SLOT_NAME, hooks)


def _controls_apply(data, language, *, allocation, charmap, work_dir, stage_options=None):
    from . import controls, activation
    if charmap is None:
        _fail('controls requires the explicit pinned charmap')
    row = controls.check_allocation(allocation, language)
    return controls.prepare(data, language, charmap, work_dir, allocation=allocation,
                            preimage_sha256=_sha(bytes(row['bytes'])),
                            **activation.owner_kwargs(stage_options, 'controls', language))


def _portable_apply(data, language, *, allocation, charmap, work_dir, stage_options=None):
    from . import portable, activation
    row = portable.check_allocation(allocation, language)
    return portable.prepare(data, language, work_dir, allocation=allocation,
                            preimage_sha256=_sha(bytes(row['bytes'])),
                            **activation.owner_kwargs(stage_options, 'portable', language))


def _controls_verify(before, after, receipt, *, charmap, stage_options=None):
    from . import controls, activation
    if charmap is None:
        _fail('controls requires the explicit pinned charmap')
    activation.check_owner_options('controls', receipt, stage_options, receipt.get('language'))
    return controls.verify(before, after, receipt, charmap=charmap)


def _portable_verify(before, after, receipt, *, charmap, stage_options=None):
    from . import portable, activation
    activation.check_owner_options('portable', receipt, stage_options, receipt.get('language'))
    return portable.verify(before, after, receipt)


def _identity_apply(data, language):
    from . import identity
    return identity.apply(data, language)


def _identity_verify(before, after, receipt):
    from . import identity
    return identity.verify(before, after, receipt)


def _trainer_fixes_apply(data, language):
    from . import trainer_fixes
    return trainer_fixes.apply(data, language)


def _trainer_fixes_verify(before, after, receipt):
    from . import trainer_fixes
    return trainer_fixes.verify(before, after, receipt)


def _trainer_fixes_regions(rom):
    from . import trainer_fixes
    return [Region(start, end, label) for start, end, label in trainer_fixes.spans(rom)]


def _legendary_scene_version_apply(data, language):
    from . import legendary_scene_version
    return legendary_scene_version.apply(data, language)


def _legendary_scene_version_verify(before, after, receipt):
    from . import legendary_scene_version
    return legendary_scene_version.verify(before, after, receipt)


def _legendary_scene_version_regions(rom):
    from . import legendary_scene_version
    return [Region(start, end, label)
            for start, end, label in legendary_scene_version.spans(rom)]


def _legendary_scene_version_peel(after, before, regions):
    from . import legendary_scene_version
    expected = _legendary_scene_version_regions(before)
    if regions != expected:
        _fail('legendary-scene-version peel declaration differs')
    peeled = legendary_scene_version.peel(after)
    check_confined(after, peeled, regions, 'legendary-scene-version peel')
    return peeled


def _pokeathlon_apply(data, language):
    from . import pokeathlon
    return pokeathlon.apply(data, language)


def _pokeathlon_verify(before, after, receipt):
    from . import pokeathlon
    return pokeathlon.verify(before, after, receipt)


def _pokeathlon_regions(rom):
    image = _image(rom)
    fid = image.records[99][6]
    if fid != 99:
        _fail('overlay 99 is not file 99')
    return [Region(*image.files[fid], 'overlay 99 slot (file 99)')]


def _traded_egg_apply(data, language):
    from . import traded_egg
    return traded_egg.apply(data, language)


def _traded_egg_verify(before, after, receipt):
    from . import traded_egg
    return traded_egg.verify(before, after, receipt)


def _traded_egg_regions(rom):
    from . import traded_egg
    return [Region(start, end, label) for start, end, label in traded_egg.spans(rom)]


def _traded_egg_cold(before, final, regions):
    """Derive the shared cold-UI Module96 CRC after all y9-size mechanics."""
    seed = [region for region in regions
            if region.label == 'ui.module.seed derived y9 crc32']
    if len(seed) != 1:
        _fail('traded-egg cold seed declaration differs')
    return {_span(seed[0]): _cold_mechanical_y9_crc(before, final)}


def _traded_egg_peel(after, before, regions):
    """Remove HG-T12 and rebuild the exact cold-UI y9-derived seed."""
    seed = [region for region in regions
            if region.label == 'ui.module.seed derived y9 crc32']
    if len(seed) != 1:
        _fail('traded-egg peel seed declaration differs')
    out = bytearray(after)
    for region in regions:
        if region != seed[0]:
            out[region.start:region.end] = before[region.start:region.end]
    image = _image(bytes(out))
    struct.pack_into('<I', out, seed[0].start,
                     zlib.crc32(out[image.y9:image.y9 + image.y9_bytes]))
    return bytes(out)


def check_traded_egg_ui_invariants(prev, nxt, regions, grants=()):
    """Permit only overlay-95 geometry plus Module96's derived y9 CRC."""
    if grants:
        _fail('traded-egg owns no resident reserve grant')
    if len(prev) != len(nxt) or prev[:HEADER_BYTES] != nxt[:HEADER_BYTES]:
        _fail('traded-egg changed ROM length or header')
    old, new = _image(prev), _image(nxt)
    _check_regions(regions, len(prev))
    if (old.fat, old.fat_bytes, old.y9, old.y9_bytes) != \
            (new.fat, new.fat_bytes, new.y9, new.y9_bytes):
        _fail('traded-egg changed FAT/y9 placement')
    fat = (old.fat + 95 * 8, old.fat + 96 * 8)
    y9_size = (old.y9 + 95 * 32 + 8, old.y9 + 95 * 32 + 12)
    y9_word = (old.y9 + 95 * 32 + 28, old.y9 + 96 * 32)
    if prev[old.fat:fat[0]] != nxt[new.fat:fat[0]] \
            or prev[fat[1]:old.fat + old.fat_bytes] != nxt[fat[1]:new.fat + new.fat_bytes]:
        _fail('traded-egg changed a foreign FAT entry')
    for start, end in ((old.y9, y9_size[0]), (y9_size[1], y9_word[0]),
                       (y9_word[1], old.y9 + old.y9_bytes)):
        if prev[start:end] != nxt[start:end]:
            _fail('traded-egg changed a foreign y9 byte')
    old_row, new_row = old.records[95], new.records[95]
    if old_row[:2] != new_row[:2] or old_row[3:7] != new_row[3:7] \
            or old_row[7] >> 24 != new_row[7] >> 24:
        _fail('traded-egg changed overlay 95 geometry beyond sizes')
    for fid in UI_FILES:
        if old.files[fid] != new.files[fid] or old.file(fid) != new.file(fid):
            _fail('traded-egg changed UI-owned file %d' % fid)
    seed_at = old.offset(MODULE_SEED, 96)
    if seed_at != new.offset(MODULE_SEED, 96) \
            or prev[seed_at:seed_at + 68] != nxt[seed_at:seed_at + 68] \
            or prev[seed_at + 72:seed_at + 96] != nxt[seed_at + 72:seed_at + 96]:
        _fail('traded-egg changed ui.module.seed outside derived y9 crc32')
    for name, address, size in (('ui.resource.seed', RESOURCE_SEED, 64),
                                ('ui.guide.seed', GUIDE_SEED, 64)):
        if old.arm(address, size) != new.arm(address, size):
            _fail('traded-egg changed ' + name)
    for label, address, size in UI_HOOKS:
        if old.arm(address, size) != new.arm(address, size):
            _fail('traded-egg changed UI hook ' + label)
    return check_ui_seeds(nxt)


def _bag_foreign_apply(data, language):
    from . import bag_foreign
    return bag_foreign.apply(data, language)


def _bag_foreign_verify(before, after, receipt):
    from . import bag_foreign
    return bag_foreign.verify(before, after, receipt)


def _bag_foreign_regions(rom):
    from . import bag_foreign
    return [Region(start, end, 'Training code SG-BAG-FOREIGN successor')
            for start, end in bag_foreign.spans(rom)]


def _bag_view_position_apply(data, language):
    from . import bag_view_position
    return bag_view_position.apply(data, language)


def _bag_view_position_verify(before, after, receipt):
    from . import bag_view_position
    return bag_view_position.verify(before, after, receipt)


def _bag_view_position_regions(rom):
    from . import bag_view_position
    return [Region(start, end, 'BagView compact-position repair')
            for start, end in bag_view_position.spans(rom)]


def _lottery_id_apply(data, language):
    from . import lottery_id
    return lottery_id.apply(data, language)


def _lottery_id_verify(before, after, receipt):
    from . import lottery_id
    return lottery_id.verify(before, after, receipt)


def _lottery_id_regions(rom):
    from . import lottery_id
    return [Region(start, end, 'Lottery Number high-half destination')
            for start, end in lottery_id.spans(rom)]


def _battle_tower_wrap_apply(data, language):
    from . import battle_tower_wrap
    return battle_tower_wrap.apply(data, language)


def _battle_tower_wrap_verify(before, after, receipt):
    from . import battle_tower_wrap
    return battle_tower_wrap.verify(before, after, receipt)


def _battle_tower_wrap_regions(rom):
    from . import battle_tower_wrap
    return [Region(start, end, 'Battle Tower full-width round selection')
            for start, end in battle_tower_wrap.spans(rom)]


def _battle_animation_facade_apply(data, language):
    from . import battle_animation_facade
    return battle_animation_facade.apply(data, language)


def _battle_animation_facade_verify(before, after, receipt):
    from . import battle_animation_facade
    return battle_animation_facade.verify(before, after, receipt)


def _battle_animation_facade_regions(rom):
    from . import battle_animation_facade
    return [Region(start, end, 'Facade task/audio launch interval')
            for start, end in battle_animation_facade.changed_regions(rom)]


def _battle_animation_dynamicpunch_apply(data, language):
    from . import battle_animation_dynamicpunch
    return battle_animation_dynamicpunch.apply(data, language)


def _battle_animation_dynamicpunch_verify(before, after, receipt):
    from . import battle_animation_dynamicpunch
    return battle_animation_dynamicpunch.verify(before, after, receipt)


def _battle_animation_dynamicpunch_regions(rom):
    from . import battle_animation_dynamicpunch
    return [Region(start, end, 'DynamicPunch second-shake launch Delay')
            for start, end in battle_animation_dynamicpunch.changed_regions(rom)]


def _battle_animation_helping_hand_apply(data, language):
    from . import battle_animation_helping_hand
    return battle_animation_helping_hand.apply(data, language)


def _battle_animation_helping_hand_verify(before, after, receipt):
    from . import battle_animation_helping_hand
    return battle_animation_helping_hand.verify(before, after, receipt)


def _battle_animation_helping_hand_regions(rom):
    from . import battle_animation_helping_hand
    return [Region(start, end, 'Helping Hand loop Delay placement')
            for start, end in battle_animation_helping_hand.changed_regions(rom)]


def _battle_animation_strength_apply(data, language):
    from . import battle_animation_strength
    return battle_animation_strength.apply(data, language)


def _battle_animation_strength_verify(before, after, receipt):
    from . import battle_animation_strength
    return battle_animation_strength.verify(before, after, receipt)


def _battle_animation_strength_regions(rom):
    from . import battle_animation_strength
    return [Region(start, end, 'Strength shrink phase frame count')
            for start, end in battle_animation_strength.changed_regions(rom)]


def _battle_animation_spit_up_apply(data, language):
    from . import battle_animation_spit_up
    return battle_animation_spit_up.apply(data, language)


def _battle_animation_spit_up_verify(before, after, receipt):
    from . import battle_animation_spit_up
    return battle_animation_spit_up.verify(before, after, receipt)


def _battle_animation_spit_up_regions(rom):
    from . import battle_animation_spit_up
    return [Region(start, end, 'Spit Up overlay 7 cleanup and BLZ stream')
            for start, end in battle_animation_spit_up.changed_regions(rom)]


def _giratina_pc_form_apply(data, language):
    from . import giratina_pc_form
    return giratina_pc_form.apply(data, language)


def _giratina_pc_form_verify(before, after, receipt):
    from . import giratina_pc_form
    return giratina_pc_form.verify(before, after, receipt)


def _giratina_pc_form_regions(rom):
    from . import giratina_pc_form
    return [Region(start, end, 'Giratina PC-exit party-stat reconciliation')
            for start, end in giratina_pc_form.changed_regions(rom)]


def _invisible_grass_apply(data, language):
    from . import invisible_grass
    return invisible_grass.apply(data, language)


def _invisible_grass_verify(before, after, receipt):
    from . import invisible_grass
    return invisible_grass.verify(before, after, receipt)


def _invisible_grass_regions(rom):
    from . import invisible_grass
    return [Region(start, end, 'Route 43/44 invisible-grass permission run')
            for start, end in invisible_grass.changed_regions(rom)]


def _waterfall_facing_apply(data, language):
    from . import waterfall_facing
    return waterfall_facing.apply(data, language)


def _waterfall_facing_verify(before, after, receipt):
    from . import waterfall_facing
    return waterfall_facing.verify(before, after, receipt)


def _waterfall_facing_regions(rom):
    from . import waterfall_facing
    return [Region(start, end, label)
            for start, end, label in waterfall_facing.spans(rom)]


def _follower_menu_jump_apply(data, language):
    from . import follower_menu_jump
    return follower_menu_jump.apply(data, language)


def _follower_menu_jump_verify(before, after, receipt):
    from . import follower_menu_jump
    return follower_menu_jump.verify(before, after, receipt)


def _follower_menu_jump_regions(rom):
    from . import follower_menu_jump
    return [Region(start, end, label)
            for start, end, label in follower_menu_jump.spans(rom)]


def _follower_menu_jump_peel(after, before, regions):
    from . import follower_menu_jump
    expected = _follower_menu_jump_regions(before)
    if [(row.start, row.end) for row in regions] != [
            (row.start, row.end) for row in expected]:
        _fail('follower-menu-jump peel declaration differs')
    peeled = follower_menu_jump.peel(after)
    check_confined(after, peeled, regions, 'follower-menu-jump peel')
    return peeled


def _identity_regions(rom):
    from . import identity
    at, size = identity.span(rom)
    return [Region(at, at + size, 'project-owned title version pixels')]


REGISTRY = {
    'identity': MechanicalStage('identity', _identity_apply, _identity_verify, _identity_regions),
    'moves': MechanicalStage('moves', _moves_apply, _moves_verify, _moves_regions),
    'ai': MechanicalStage('ai', _ai_apply, _ai_verify, _ai_regions,
                          slot=FAIRY_AI_SLOT, slot_payload=FAIRY_AI_PAYLOAD_BYTES,
                          cold_preimages=_ai_cold, peel=_ai_peel,
                          invariants=check_ai_ui_invariants),
    'ai-immunities': MechanicalStage('ai-immunities', _ai_immunities_apply,
                                     _ai_immunities_verify, _ai_immunities_regions),
    'abilities': MechanicalStage('abilities', _abilities_apply, _abilities_verify, _abilities_regions,
                                 slot=ABILITIES_SLOT, slot_payload=ABILITIES_PAYLOAD_BYTES,
                                 archive_producers=('keen-eye-text',), peel=_abilities_peel,
                                 cold_preimages=_cold_slot(ABILITIES_SLOT)),
    # script fixes only: the producer is registered by archives.register_owner_producers (gifts_archives)
    'gifts': MechanicalStage('gifts', None, None, None, archive_producers=('gifts-scripts',)),
    # Scripts travel in the UI append; only the bounded Lullaby overlay edit runs afterwards.
    'legacy': MechanicalStage('legacy', _legacy_apply, _legacy_verify, _legacy_regions,
                               archive_producers=('legacy-events', 'legacy-scripts',
                                                  'poison-follower-script', 'gs-cup-guard',
                                                  'safari-scripts',
                                                  'evolution-fixes', 'fishing-encounters',
                                                  'pursuit-script', 'status-icon-script',
                                                  'pressure-switch-effects',
                                                  'pressure-switch-subscripts'),
                               legacy_owners=('sgp.plus', 'sgp.capacita_borsa',
                                              'sgp.soul_dew', 'sgp.wonder_card',
                                              'sgp.gb_sounds_evolution',
                                              'sgp.pokegear_autocull')),
    'legendary-scenes': MechanicalStage(
        'legendary-scenes', None, None, None,
        archive_producers=('legendary-scenes-scripts',)),
    'legendary-scene-version': MechanicalStage(
        'legendary-scene-version', _legendary_scene_version_apply,
        _legendary_scene_version_verify, _legendary_scene_version_regions,
        peel=_legendary_scene_version_peel),
    'trainer-fixes': MechanicalStage('trainer-fixes', _trainer_fixes_apply,
                                     _trainer_fixes_verify, _trainer_fixes_regions),
    'pokeathlon': MechanicalStage('pokeathlon', _pokeathlon_apply,
                                  _pokeathlon_verify, _pokeathlon_regions),
    'traded-egg': MechanicalStage('traded-egg', _traded_egg_apply,
                                  _traded_egg_verify, _traded_egg_regions,
                                  cold_preimages=_traded_egg_cold,
                                  peel=_traded_egg_peel,
                                  invariants=check_traded_egg_ui_invariants),
    'bag-foreign': MechanicalStage('bag-foreign', _bag_foreign_apply,
                                   _bag_foreign_verify, _bag_foreign_regions,
                                   resident_owners=('training.code',)),
    'bag-view-position': MechanicalStage('bag-view-position', _bag_view_position_apply,
                                         _bag_view_position_verify, _bag_view_position_regions),
    'lottery-id': MechanicalStage('lottery-id', _lottery_id_apply,
                                  _lottery_id_verify, _lottery_id_regions),
    'battle-tower-wrap': MechanicalStage(
        'battle-tower-wrap', _battle_tower_wrap_apply,
        _battle_tower_wrap_verify, _battle_tower_wrap_regions),
    'battle-animation-facade': MechanicalStage(
        'battle-animation-facade', _battle_animation_facade_apply,
        _battle_animation_facade_verify, _battle_animation_facade_regions),
    'battle-animation-dynamicpunch': MechanicalStage(
        'battle-animation-dynamicpunch', _battle_animation_dynamicpunch_apply,
        _battle_animation_dynamicpunch_verify, _battle_animation_dynamicpunch_regions),
    'battle-animation-helping-hand': MechanicalStage(
        'battle-animation-helping-hand', _battle_animation_helping_hand_apply,
        _battle_animation_helping_hand_verify, _battle_animation_helping_hand_regions),
    'battle-animation-strength': MechanicalStage(
        'battle-animation-strength', _battle_animation_strength_apply,
        _battle_animation_strength_verify, _battle_animation_strength_regions),
    'battle-animation-spit-up': MechanicalStage(
        'battle-animation-spit-up', _battle_animation_spit_up_apply,
        _battle_animation_spit_up_verify, _battle_animation_spit_up_regions),
    'giratina-pc-form': MechanicalStage(
        'giratina-pc-form', _giratina_pc_form_apply,
        _giratina_pc_form_verify, _giratina_pc_form_regions),
    'invisible-grass': MechanicalStage(
        'invisible-grass', _invisible_grass_apply,
        _invisible_grass_verify, _invisible_grass_regions),
    'waterfall-facing': MechanicalStage(
        'waterfall-facing', _waterfall_facing_apply,
        _waterfall_facing_verify, _waterfall_facing_regions,
        legacy_owners=('sgp.waterfall_facing',)),
    'follower-menu-jump': MechanicalStage(
        'follower-menu-jump', _follower_menu_jump_apply,
        _follower_menu_jump_verify, _follower_menu_jump_regions,
        peel=_follower_menu_jump_peel),
    'controls': MechanicalStage('controls', _controls_apply, _controls_verify, _controls_regions,
                                slot='summary-controls.runtime', slot_payload=512, contextual=True,
                                cold_preimages=_cold_slot('summary-controls.runtime')),
    'portable': MechanicalStage('portable', _portable_apply, _portable_verify, _portable_regions,
                                slot='portable-box.runtime', slot_payload=3024, contextual=True,
                                cold_preimages=_cold_slot('portable-box.runtime')),
    'rematches': MechanicalStage('rematches', _rematches_apply, _rematches_verify, _rematches_regions,
                                 slot='c8.module-stubs', slot_payload=64, contextual=True,
                                 regions_from_final=True, cold_preimages=_rematches_cold, peel=_rematches_peel),
    'uturn-flinch': MechanicalStage(
        'uturn-flinch', _uturn_apply, _uturn_verify, _uturn_regions,
        slot='c8.module-stubs', slot_payload=192, contextual=True,
        archive_producers=('uturn-item-snapshot',), peel=_uturn_peel,
        invariants=check_ai_ui_invariants),
}


def check_registry_consistency(order=None, implemented=None, pending=None, registry=None):
    """ORDER, IMPLEMENTED, PENDING and REGISTRY must describe the same stages, implemented ones as a prefix."""
    order = ORDER if order is None else order
    implemented = IMPLEMENTED if implemented is None else implemented
    pending = PENDING if pending is None else pending
    registry = REGISTRY if registry is None else registry
    if set(implemented) & set(pending):
        raise ValueError('a stage cannot be both implemented and pending')
    if len(set(order)) != len(order) or set(order) != set(implemented) | set(pending):
        raise ValueError('ORDER differs from IMPLEMENTED + PENDING')
    if tuple(implemented) != tuple(n for n in order if n in implemented):
        raise ValueError('IMPLEMENTED is not in ORDER order')
    cut = min([order.index(n) for n in pending] or [len(order)])
    if any(order.index(n) >= cut for n in implemented):
        raise ValueError('a pending stage precedes an implemented one: chain_for is a prefix rule')
    if set(registry) != set(implemented):
        raise ValueError('REGISTRY differs from IMPLEMENTED')


def require_stage(name, registry=None):
    registry = REGISTRY if registry is None else registry
    if name in registry:
        return registry[name]
    if name in PENDING:
        raise StagePending(name, PENDING[name])
    raise ValueError('unknown mechanical stage: ' + str(name))


check_registry_consistency()


def chain_for(through):
    """Mechanical stages composed after UI for `through`: the implemented prefix ending at it."""
    if through in ('baseline', 'ui'):
        return ()
    if through in IMPLEMENTED:
        return IMPLEMENTED[:IMPLEMENTED.index(through) + 1]
    require_stage(through)  # StagePending for pending, ValueError for unknown
    raise ValueError('not a mechanical stage: ' + str(through))


# -------------------------------------------------------------------------- receipts

def _default(value):
    if isinstance(value, (bytes, bytearray)):
        return bytes(value).hex()
    if isinstance(value, (set, frozenset)):
        return sorted(value)
    raise TypeError('receipt value is not JSON serialisable: %r' % type(value).__name__)


def _jsonable(raw):
    return json.loads(json.dumps(raw, default=_default, allow_nan=False))


def _digest(value):
    if not isinstance(value, str) or not re.fullmatch('[0-9a-f]{64}', value):
        raise ValueError('invalid receipt hash')


def validate_receipt(receipt, name, language=None):
    """Shape and self-consistency of one wrapped stage receipt; no ROM needed."""
    if not isinstance(receipt, dict) or set(receipt) != RECEIPT_KEYS:
        raise ValueError('mechanics receipt keys differ from the schema')
    if (type(receipt['schema']) is not int or receipt['schema'] != SCHEMA or receipt['stage'] != name
            or (language is not None and receipt['language'] != language)
            or receipt['language'] not in ('EN', 'IT')):
        raise ValueError('mechanics receipt stage/schema/language mismatch for ' + str(name))
    _digest(receipt['input_sha256'])
    _digest(receipt['output_sha256'])
    for key in ('input_bytes', 'output_bytes'):
        if type(receipt[key]) is not int or receipt[key] <= 0:
            raise ValueError('mechanics receipt size invalid: ' + key)
    regions = receipt['regions']
    if not isinstance(regions, list) or not regions:
        raise ValueError('mechanics receipt regions must be a nonempty list')
    for item in regions:
        if (not isinstance(item, dict) or set(item) != {'start', 'end', 'label'}
                or type(item['start']) is not int or type(item['end']) is not int
                or not 0 <= item['start'] < item['end'] or not isinstance(item['label'], str)):
            raise ValueError('mechanics receipt region invalid')
    changed = receipt['changed_ranges']
    if not isinstance(changed, list) or not changed:
        raise ValueError('mechanics receipt changed_ranges must be a nonempty list')
    previous_end = -1
    for pair in changed:
        if (not isinstance(pair, list) or len(pair) != 2 or any(type(v) is not int for v in pair)
                or not 0 <= pair[0] < pair[1] or pair[0] <= previous_end
                or not any(r['start'] <= pair[0] and pair[1] <= r['end'] for r in regions)):
            raise ValueError('mechanics receipt changed_ranges invalid or outside the declared regions')
        previous_end = pair[1]
    raw = receipt['stage_receipt']
    if not isinstance(raw, dict):
        raise ValueError('embedded stage receipt must be an object')
    _digest(receipt['stage_receipt_sha256'])
    if _sha(canonical(raw)) != receipt['stage_receipt_sha256']:
        raise ValueError('stage receipt hash mismatch')


def _wrap(name, language, before, after, regions, raw):
    changed = [list(pair) for pair in changed_ranges(before, after)]
    return {'schema': SCHEMA, 'stage': name, 'language': language,
            'input_sha256': _sha(before), 'output_sha256': _sha(after),
            'input_bytes': len(before), 'output_bytes': len(after),
            'regions': [{'start': r.start, 'end': r.end, 'label': r.label} for r in regions],
            'changed_ranges': changed, 'stage_receipt': raw, 'stage_receipt_sha256': _sha(canonical(raw))}


def run_stage(name, data, language, *, invariants=None, registry=None, allocation=None, work_dir=None,
              charmap=None, stage_options=None, overlay_deltas=()):
    """Apply one mechanical stage to an UI image: own writer, own reader, confinement, UI invariants.

    `allocation` is the list of assignment rows of `reserve.allocate` (the only source of reserve grants). A slot stage
    refuses without its row; `work_dir` is the scratch directory for a stage that compiles (a temporary one by default).
    """
    stage = require_stage(name, registry)  # pending stages fail before data is read
    if getattr(stage, 'archive_only', False):
        _fail('%s has no post-UI writer: its effect is the archive delta the UI stage applies' % name)
    invariants = (getattr(stage, 'invariants', None) or check_ui_invariants) if invariants is None else invariants
    if getattr(stage, 'contextual', False) and not isinstance(allocation, dict):
        _fail('%s requires the full reserve allocation receipt, never assignment rows alone' % name)
    row = assigned_row(stage, allocation) if getattr(stage, 'slot_payload', 0) > 0 else None
    if type(data) is not bytes:
        raise ValueError('exact immutable ROM bytes required')
    if row is None:
        output, raw = guarded(name + ' writer', stage.apply, data, language)
    else:
        with (tempfile.TemporaryDirectory(prefix='mechanics-') if work_dir is None else nullcontext(work_dir)) as directory:
            kwargs = ({'allocation': allocation, 'charmap': charmap, 'work_dir': directory, 'stage_options': stage_options}
                      if getattr(stage, 'contextual', False) else {'row': row, 'work_dir': directory})
            if stage.name == 'rematches':
                kwargs['overlay_deltas'] = overlay_deltas
            output, raw = guarded(name + ' writer', lambda d, lang: stage.apply(d, lang, **kwargs), data, language)
    if type(output) is not bytes:
        raise CompositionError('%s returned a mutable or non-bytes ROM' % name)
    if output == data:
        raise CompositionError('%s made no change' % name)
    regions = list(guarded(name + ' declaration', stage.regions, data))
    raw = guarded(name + ' receipt', _jsonable, raw)
    if getattr(stage, 'contextual', False):
        if raw.get('allocation') != allocation:
            _fail('%s owner receipt allocation differs from the granted receipt' % name)
        verify_kwargs = {'charmap': charmap, 'stage_options': stage_options}
        if stage.name == 'rematches':
            verify_kwargs['overlay_deltas'] = overlay_deltas
        guarded(name + ' reader', lambda a, b, r: stage.verify(a, b, r, **verify_kwargs), data, output, raw)
    else:
        guarded(name + ' reader', stage.verify, data, output, raw)
    _run_invariants(invariants, data, output, regions, _grants(stage, data, allocation))
    check_confined(data, output, regions, name)
    return output, _wrap(name, language, data, output, regions, raw)


def _grants(stage, rom, allocation):
    grants = legacy_owner_grants(rom, stage.name, getattr(stage, 'legacy_owners', ()))
    grants += resident_owner_grants(rom, stage.name, getattr(stage, 'resident_owners', ()))
    slot = getattr(stage, 'slot', None)
    if slot and allocation is not None:
        grants += reserve_grants(rom, stage.name, slot, allocation)
    return grants


def _run_invariants(invariants, prev, nxt, regions, grants):
    if grants:
        return guarded('UI invariants', invariants, prev, nxt, regions, grants)
    return guarded('UI invariants', invariants, prev, nxt, regions)


# ------------------------------------------------------------------- chain replay

def _restore(rom, source, spans, cold_preimages=None):
    out = bytearray(rom)
    for span in spans:
        fixed = (cold_preimages or {}).get(_span(span))
        if fixed is not None:
            if type(fixed) is not bytes or len(fixed) != span.end-span.start or span.end > len(out):
                _fail('invalid fixed cold restoration')
            out[span.start:span.end] = fixed
            continue
        if span.end > len(source) or span.end > len(out):
            _fail('declared region %s lies beyond the pristine input' % span.label)
        out[span.start:span.end] = source[span.start:span.end]
    return bytes(out)


def verify_chain(before, final, names, receipts, verify_ui, *, invariants=None, registry=None,
                 allocation=None, charmap=None, stage_options=None, overlay_deltas=()):
    """Independent admission of `final` = UI(before) + the named mechanical stages, in order.

    `verify_ui(ui_image)` must be the existing independent UI verifier (it raises on any byte
    outside the UI policy); it receives the image rebuilt by restoring every declared region
    from `before`, so a stage can only have touched what it declared. Every external reader is
    fail-closed: an unexpected exception type is a refusal, never a crash or a pass.
    """
    caller_invariants = invariants
    names = list(names)
    if len(set(names)) != len(names):
        raise ValueError('duplicate mechanical stage')
    stages = [require_stage(n, registry) for n in names]
    if any(getattr(stage, 'archive_only', False) for stage in stages):
        _fail('an archive-only stage has no post-UI writer to replay: pass mechanics_stages.writers(names)')
    if not isinstance(receipts, list) or len(receipts) != len(stages):
        _fail('mechanics receipt count %s does not match %d stages'
              % (len(receipts) if isinstance(receipts, list) else '?', len(stages)))
    from . import baseline
    try:
        expected_language = baseline.identify(before)
    except ValueError:
        expected_language = None  # synthetic unit fixtures have no cartridge identity
    for receipt, name in zip(receipts, names):
        validate_receipt(receipt, name, expected_language)
    for stage in stages:
        if getattr(stage, 'contextual', False) and not isinstance(allocation, dict):
            _fail('%s requires the full reserve allocation receipt' % stage.name)
        if getattr(stage, 'slot_payload', 0) > 0:
            assigned_row(stage, allocation)       # an unproven reserve condition is refused before any ROM work
    declared = [list(guarded(stage.name + ' declaration', stage.regions, final if getattr(stage, 'regions_from_final', False) else before)) for stage in stages]
    for stage, regions in zip(stages, declared):
        _check_regions(regions, len(final) if getattr(stage, 'regions_from_final', False) else len(before))
    images = intermediate_images(before, final, stages, declared)
    ui_image = images[0]
    ui_result = guarded('UI verifier', verify_ui, ui_image)
    previous, hashes = ui_image, []
    for index, (stage, regions, receipt) in enumerate(zip(stages, declared, receipts)):
        step = images[index + 1]
        if receipt['input_sha256'] != _sha(previous) or receipt['output_sha256'] != _sha(step):
            _fail('receipt for %s does not describe this step of the final ROM' % stage.name)
        if [dict(start=r.start, end=r.end, label=r.label) for r in regions] != receipt['regions']:
            _fail('receipt regions for %s differ from the stage declaration' % stage.name)
        if list(guarded(stage.name + ' declaration', stage.regions, previous)) != regions:
            _fail('%s declaration moved between the input and the intermediate image' % stage.name)
        if step == previous:
            _fail('%s left its declared region unchanged' % stage.name)
        if receipt['changed_ranges'] != [list(pair) for pair in changed_ranges(previous, step)]:
            _fail('receipt changed_ranges for %s differ from the bytes actually changed' % stage.name)
        policy = (getattr(stage, 'invariants', None) or check_ui_invariants) if caller_invariants is None else caller_invariants
        _run_invariants(policy, previous, step, regions, _grants(stage, previous, allocation))
        check_confined(previous, step, regions, stage.name)
        raw = receipt['stage_receipt']
        if getattr(stage, 'contextual', False):
            if raw.get('allocation') != allocation:
                _fail('%s owner receipt allocation differs from the granted receipt' % stage.name)
            verify_kwargs = {'charmap': charmap, 'stage_options': stage_options}
            if stage.name == 'rematches':
                verify_kwargs['overlay_deltas'] = overlay_deltas
            guarded(stage.name + ' reader', lambda a, b, r: stage.verify(a, b, r, **verify_kwargs), previous, step, raw)
        else:
            guarded(stage.name + ' reader', stage.verify, previous, step, raw)
        hashes.append(receipt['stage_receipt_sha256'])
        previous = step
    if previous != final:
        _fail('final ROM differs from the chain reconstruction outside the declared regions')
    return {'stages': names, 'ui': ui_result, 'stage_receipt_sha256': hashes,
            'ui_image_sha256': _sha(ui_image), 'output_sha256': _sha(final)}
