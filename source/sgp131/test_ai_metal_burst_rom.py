"""Native reproducer for AI-WEB-02, the Metal Burst ordering shortcuts.

The exact EN/IT V4 inputs are read without modification.  These tests execute
the real overlay-10 trainer-AI interpreter, Basic_CheckMetalBurst from member
0 of ``a/0/9/9``, and the real overlay-12 ``CheckSortSpeed`` implementation.
The item archive is supplied in its in-memory 0x24-byte-row layout so held-item
effects, Stall, Trick Room, Quick Claw, Custap and tie RNG take their native
branches.

Only dependencies that need a live BattleSystem are deterministic: normal
single-battle field sides and the RNG return.  Type-effectiveness helpers used
by the outer AI loop remain neutral as in the shared interpreter bench.  This
is CPU evidence, not a rendered battle or device acceptance test.
"""
from collections import Counter
import hashlib
import struct
import unittest

import ndspy.narc
import ndspy.rom
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1

from sgp12.rom import Rom
from . import ai_scoring as ai
from .test_ai_water_spout_rom import (
    BATTLER_STRIDE,
    BATTLE_SYSTEM_RANDOM,
    BS,
    CTX,
    INTERPRETER,
    KNOWN_ABILITIES,
    KNOWN_ITEMS,
    MOVES,
    SCRIPT_CURSOR,
    SPEED_ORDER,
    UNSIGNED_DIVIDE,
    WaterSpoutBench,
    artifacts,
    unicorn_works,
)


SCRIPT_OFFSET = 0x1DE0
SCRIPT_WORDS = (
    43, 0, 607,
    41, 0,
    19, 100, 602,
    85, 0, 107, 598,
    41, 1,
    19, 100, 7,
    85, 1, 107, 3,
    36, 0, 586,
    77,
)
JUMP_SITES = (0x1DFC, 0x1E0C, 0x1E20, 0x1E30)

OVERLAY12_BASE = 0x022378C0
OVERLAY12_SIZE = 226176
OVERLAY12_SHA256 = 'c426e8176612f5b9f5cd8d24099b1be57e1f3ce71f90dbf5a718cfe87092b982'
ITEM_ARCHIVE = 'a/0/1/7'
ITEM_ARCHIVE_SHA256 = 'df0e5b742b00569d80e0e5a2f9daab1a781aacd32a377ce503e7615157ef8eee'
ITEM_MEMBER_COUNT = 516
ITEM_MEMBER_SIZE = 34
ITEM_ROW_SIZE = 0x24

FIELD_SIDE = 0x0223AB1C
CHECK_ABILITY_ACTIVE = 0x02252324
GET_ITEM_VAR = 0x02257E74
SPEED_ORDER_RETURN = 0x0225035E
CURSOR_ADD = 0x0221EF24
CURSOR_ADD_RETURN = 0x0221EF2C

ITEM_DATA_RAM = 0x023C0000
ITEM_DATA_POINTER = 0x2120
PRIORITY_ROLLS = 0x310C
BATTLE_MON_BASE = MOVES - 0x0C
BATTLE_MON_SPEED = BATTLE_MON_BASE + 0x06
BATTLE_MON_STAT_CHANGES = BATTLE_MON_BASE + 0x18
BATTLE_MON_ABILITY = BATTLE_MON_BASE + 0x27
BATTLE_MON_ITEM = BATTLE_MON_BASE + 0x78

ITEM_NONE = 0
ITEM_SHINY_STONE = 107
ITEM_CUSTAP_BERRY = 210
ITEM_QUICK_CLAW = 217
ITEM_LAGGING_TAIL = 279
ITEM_FULL_INCENSE = 316
ABILITY_OTHER = 1
ABILITY_STALL = 100
TRICK_ROOM = 0x00070000


def real_artifacts(case, language):
    """Authenticate and return every guest artifact used by the real bench."""
    raw, overlay10, member = artifacts(case, language)
    entry, _, overlay12 = Rom(raw).immagine_overlay(12)
    case.assertEqual((entry['ram'], entry['ram_size']),
                     (OVERLAY12_BASE, OVERLAY12_SIZE))
    case.assertEqual(hashlib.sha256(overlay12).hexdigest(), OVERLAY12_SHA256)

    rom = ndspy.rom.NintendoDSRom(raw)
    archive = bytes(rom.getFileByName(ITEM_ARCHIVE))
    case.assertEqual(hashlib.sha256(archive).hexdigest(), ITEM_ARCHIVE_SHA256)
    members = ndspy.narc.NARC(archive).files
    case.assertEqual(len(members), ITEM_MEMBER_COUNT)
    case.assertTrue(all(len(part) == ITEM_MEMBER_SIZE for part in members))

    # LoadAllItemData exposes the aligned FIMG rows as ItemData[516].  ndspy
    # removes each member's two padding bytes, so restore them explicitly.
    item_data = b''.join(
        bytes(part) + b'\xff' * (ITEM_ROW_SIZE - len(part))
        for part in members
    )
    case.assertEqual(len(item_data), ITEM_MEMBER_COUNT * ITEM_ROW_SIZE)

    # Independent archive preimages: ID 107 is a no-effect evolution stone,
    # whereas the two lagging items have hold effect 107.
    for index, effect, modifier in (
            (107, 0, 0),       # Shiny Stone
            (188, 45, 4),      # Custap Berry
            (195, 52, 20),     # Quick Claw
            (257, 107, 0),     # Lagging Tail
            (294, 107, 0)):    # Full Incense
        case.assertEqual(tuple(members[index][2:4]), (effect, modifier))

    return raw, overlay10, member, overlay12, item_data


class RealMetalBurstBench(WaterSpoutBench):
    """Execute Metal Burst AI and the candidate's native speed comparator."""

    def _hook(self, uc, address, size, user):
        if address == SPEED_ORDER:
            self.calls['sort_entry'] += 1
            return  # Let the overlay-12 guest function execute.
        if address == UNSIGNED_DIVIDE:
            self.calls['divide'] += 1
            return  # Custap's native max-HP division must execute too.
        if address == BATTLE_SYSTEM_RANDOM:
            self.calls['rng'] += 1
        super()._hook(uc, address, size, user)

    def __init__(self, raw, overlay10, member, overlay12, item_data):
        self.case = None
        self.calls = {}
        self.order = []
        self.zero_cursor = []
        self.zero_cursor_pending = False
        super().__init__(raw, overlay10, member, faster=False,
                         script_offset=SCRIPT_OFFSET)
        self.mu.mem_write(OVERLAY12_BASE, overlay12)
        self.mu.mem_write(ITEM_DATA_RAM, item_data)
        for address in (FIELD_SIDE, CHECK_ABILITY_ACTIVE, GET_ITEM_VAR,
                        SPEED_ORDER_RETURN, CURSOR_ADD, CURSOR_ADD_RETURN,
                        INTERPRETER):
            self.mu.hook_add(UC_HOOK_CODE, self._real_hook,
                             begin=address, end=address)

    def _real_hook(self, uc, address, size, user):
        if address == INTERPRETER:
            self._install_case(uc)
        elif address == FIELD_SIDE:
            self.calls['field_side'] += 1
            self._return(uc.reg_read(UC_ARM_REG_R1) & 1)
        elif address == CHECK_ABILITY_ACTIVE:
            self.calls['check_ability'] += 1
        elif address == GET_ITEM_VAR:
            self.calls['get_item'] += 1
        elif address == SPEED_ORDER_RETURN:
            self.calls['sort_return'] += 1
            self.order.append(uc.reg_read(UC_ARM_REG_R0))
        elif address == CURSOR_ADD:
            if uc.reg_read(UC_ARM_REG_R1) == 0:
                self.zero_cursor_pending = True
                cursor = struct.unpack('<I',
                                       uc.mem_read(CTX + SCRIPT_CURSOR, 4))[0]
                self.zero_cursor.append([cursor, None])
        elif address == CURSOR_ADD_RETURN and self.zero_cursor_pending:
            cursor = struct.unpack('<I',
                                   uc.mem_read(CTX + SCRIPT_CURSOR, 4))[0]
            self.zero_cursor[-1][1] = cursor
            self.zero_cursor_pending = False

    def _install_case(self, uc):
        case = self.case
        uc.mem_write(BS + 0x2C, struct.pack('<I', 1))  # normal single battle
        for battler, speed, ability, item in (
                (0, case['target_speed'], case['target_ability'],
                 case['target_item']),
                (1, case['attacker_speed'], case['attacker_ability'],
                 case['attacker_item'])):
            offset = battler * BATTLER_STRIDE
            uc.mem_write(CTX + offset + BATTLE_MON_SPEED,
                         struct.pack('<I', speed))
            uc.mem_write(CTX + offset + BATTLE_MON_STAT_CHANGES,
                         bytes((6,)) * 8)
            uc.mem_write(CTX + offset + BATTLE_MON_ABILITY, bytes((ability,)))
            uc.mem_write(CTX + offset + BATTLE_MON_ITEM,
                         struct.pack('<H', item))
        uc.mem_write(CTX + KNOWN_ABILITIES,
                     bytes((case['target_ability'], case['attacker_ability'])))
        uc.mem_write(CTX + KNOWN_ITEMS,
                     struct.pack('<HH', case['target_item'],
                                 case['attacker_item']))
        uc.mem_write(CTX + ITEM_DATA_POINTER,
                     struct.pack('<I', ITEM_DATA_RAM))
        uc.mem_write(CTX + PRIORITY_ROLLS,
                     struct.pack('<4H', *case['priority_rolls']))

    def run_case(self, *, attacker_speed=200, target_speed=100,
                 attacker_item=ITEM_NONE, target_item=ITEM_NONE,
                 attacker_ability=0, target_ability=ABILITY_OTHER,
                 attacker_hp=100, target_hp=100, field_condition=0,
                 priority_rolls=(1, 1, 1, 1), random_value=0):
        self.case = {
            'attacker_speed': attacker_speed,
            'target_speed': target_speed,
            'attacker_item': attacker_item,
            'target_item': target_item,
            'attacker_ability': attacker_ability,
            'target_ability': target_ability,
            'priority_rolls': priority_rolls,
        }
        self.calls = {
            'sort_entry': 0,
            'sort_return': 0,
            'divide': 0,
            'rng': 0,
            'field_side': 0,
            'get_item': 0,
            'check_ability': 0,
        }
        self.order = []
        self.zero_cursor = []
        self.zero_cursor_pending = False
        result = self.run(
            attacker_hp=attacker_hp,
            target_hp=target_hp,
            move=368,
            move_effect=227,
            field_condition=field_condition,
            random_value=random_value,
            attacker_item=attacker_item,
            target_known_item=target_item,
            attacker_ability=attacker_ability,
            target_known_ability=target_ability,
        )
        result['order'] = self.order[-1] if self.order else None
        result['calls'] = dict(self.calls)
        result['zero_cursor'] = tuple(tuple(pair) for pair in self.zero_cursor)
        return result


CASES = (
    # name, real-guest inputs, CheckSortSpeed R0, current score, fixed score
    ('none-fast', {}, 0, 90, 90),
    ('none-slow', {'attacker_speed': 100, 'target_speed': 200}, 1, 100, 100),
    ('tie-rng-even', {'attacker_speed': 100, 'target_speed': 100,
                      'random_value': 0}, 0, 90, 90),
    ('tie-rng-odd', {'attacker_speed': 100, 'target_speed': 100,
                     'random_value': 1}, 2, 100, 100),
    ('trick-room-fast', {'field_condition': TRICK_ROOM}, 1, 100, 100),
    ('trick-room-slow', {'attacker_speed': 100, 'target_speed': 200,
                         'field_condition': TRICK_ROOM}, 0, 90, 90),
    ('shiny-attacker-fast', {'attacker_item': ITEM_SHINY_STONE}, 0, 100, 90),
    ('shiny-target-slow', {'attacker_speed': 100, 'target_speed': 200,
                           'target_item': ITEM_SHINY_STONE}, 1, 90, 100),
    ('tail-attacker-fast', {'attacker_item': ITEM_LAGGING_TAIL}, 1, 100, 100),
    ('incense-target-slow', {'attacker_speed': 100, 'target_speed': 200,
                             'target_item': ITEM_FULL_INCENSE}, 0, 90, 90),
    ('both-tail-fast', {'attacker_item': ITEM_LAGGING_TAIL,
                        'target_item': ITEM_LAGGING_TAIL}, 1, 100, 100),
    ('both-tail-slow', {'attacker_speed': 100, 'target_speed': 200,
                        'attacker_item': ITEM_LAGGING_TAIL,
                        'target_item': ITEM_LAGGING_TAIL}, 0, 90, 90),
    ('tail-incense-fast', {'attacker_item': ITEM_LAGGING_TAIL,
                           'target_item': ITEM_FULL_INCENSE}, 1, 100, 100),
    ('incense-tail-slow', {'attacker_speed': 100, 'target_speed': 200,
                           'attacker_item': ITEM_FULL_INCENSE,
                           'target_item': ITEM_LAGGING_TAIL}, 0, 90, 90),
    ('stall-attacker', {'attacker_ability': ABILITY_STALL}, 1, 100, 100),
    ('stall-target', {'attacker_speed': 100, 'target_speed': 200,
                      'target_ability': ABILITY_STALL}, 0, 90, 90),
    ('stall-attacker-tail-target', {'attacker_ability': ABILITY_STALL,
                                    'target_item': ITEM_LAGGING_TAIL}, 0, 100, 90),
    ('tail-attacker-stall-target', {'attacker_item': ITEM_LAGGING_TAIL,
                                    'target_ability': ABILITY_STALL}, 1, 90, 100),
    ('both-stall-fast', {'attacker_ability': ABILITY_STALL,
                         'target_ability': ABILITY_STALL}, 1, 90, 100),
    ('both-stall-slow', {'attacker_speed': 100, 'target_speed': 200,
                         'attacker_ability': ABILITY_STALL,
                         'target_ability': ABILITY_STALL}, 0, 90, 90),
    ('shiny-attacker-tail-target', {'attacker_item': ITEM_SHINY_STONE,
                                    'target_item': ITEM_LAGGING_TAIL}, 0, 100, 90),
    ('tail-attacker-shiny-target', {'attacker_speed': 100,
                                    'target_speed': 200,
                                    'attacker_item': ITEM_LAGGING_TAIL,
                                    'target_item': ITEM_SHINY_STONE}, 1, 90, 100),
    ('shiny-attacker-stall-target', {'attacker_item': ITEM_SHINY_STONE,
                                     'target_ability': ABILITY_STALL}, 0, 90, 90),
    ('stall-attacker-shiny-target', {'attacker_speed': 100,
                                     'target_speed': 200,
                                     'attacker_ability': ABILITY_STALL,
                                     'target_item': ITEM_SHINY_STONE}, 1, 90, 100),
    ('quick-claw-attacker-active', {'attacker_speed': 100,
                                    'target_speed': 200,
                                    'attacker_item': ITEM_QUICK_CLAW,
                                    'priority_rolls': (1, 0, 1, 1)}, 0, 90, 90),
    ('quick-claw-attacker-inactive', {'attacker_speed': 100,
                                      'target_speed': 200,
                                      'attacker_item': ITEM_QUICK_CLAW,
                                      'priority_rolls': (1, 1, 1, 1)}, 1, 100, 100),
    ('quick-claw-target-active', {'attacker_item': ITEM_NONE,
                                  'target_item': ITEM_QUICK_CLAW,
                                  'priority_rolls': (0, 1, 1, 1)}, 1, 100, 100),
    ('custap-attacker-active', {'attacker_speed': 100,
                                'target_speed': 200,
                                'attacker_item': ITEM_CUSTAP_BERRY,
                                'attacker_hp': 25}, 0, 90, 90),
    ('custap-attacker-inactive', {'attacker_speed': 100,
                                  'target_speed': 200,
                                  'attacker_item': ITEM_CUSTAP_BERRY,
                                  'attacker_hp': 26}, 1, 100, 100),
    ('custap-target-active', {'target_item': ITEM_CUSTAP_BERRY,
                              'target_hp': 25}, 1, 100, 100),
)


class MetalBurstRomTests(unittest.TestCase):
    def setUp(self):
        if not unicorn_works():
            self.skipTest('local Unicorn engine SIGILLs before guest execution')

    def test_real_script_and_speed_dependencies_are_authenticated(self):
        for language in ('EN', 'IT'):
            _, _, member, _, _ = real_artifacts(self, language)
            with self.subTest(language=language):
                self.assertEqual(struct.unpack_from('<25i', member, SCRIPT_OFFSET),
                                 SCRIPT_WORDS)

    def test_current_shortcuts_and_four_jump_fix_follow_real_order_matrix(self):
        for language in ('EN', 'IT'):
            raw, overlay10, member, overlay12, item_data = real_artifacts(
                self, language)
            fixed, report = ai.patch_metal_burst_member(member)
            self.assertEqual(report['member_offsets'], list(JUMP_SITES))
            self.assertEqual(report['changed_offsets'],
                             [0x1DFC, 0x1DFD, 0x1E0C, 0x1E0D,
                              0x1E20, 0x1E30])
            current_bench = RealMetalBurstBench(
                raw, overlay10, member, overlay12, item_data)
            fixed_bench = RealMetalBurstBench(
                raw, overlay10, fixed, overlay12, item_data)

            for name, kwargs, order, before_score, after_score in CASES:
                with self.subTest(language=language, case=name, phase='current'):
                    before = current_bench.run_case(**kwargs)
                    self.assertEqual(before['score'], before_score)
                    self.assertEqual((before['state'], before['slot']), (2, 4))
                with self.subTest(language=language, case=name, phase='fixed'):
                    after = fixed_bench.run_case(**kwargs)
                    self.assertEqual(after['order'], order)
                    self.assertEqual(after['score'], after_score)
                    self.assertEqual(after_score, 90 if order == 0 else 100)
                    self.assertEqual((after['state'], after['slot']), (2, 4))
                    self.assertEqual((after['calls']['sort_entry'],
                                      after['calls']['sort_return']), (1, 1))

                    if name.startswith('tie-rng-'):
                        self.assertEqual(after['calls']['rng'], 1)
                    if name.startswith('custap-'):
                        self.assertEqual(after['calls']['divide'], 1)

    def test_four_zero_jumps_preserve_cursor_and_termination(self):
        expected_cursor = (
            (0x1E00 // 4, 0x1E00 // 4),
            (0x1E10 // 4, 0x1E10 // 4),
            (0x1E24 // 4, 0x1E24 // 4),
            (0x1E34 // 4, 0x1E34 // 4),
        )
        for language in ('EN', 'IT'):
            raw, overlay10, member, overlay12, item_data = real_artifacts(
                self, language)
            fixed, _ = ai.patch_metal_burst_member(member)
            self.assertEqual(tuple(struct.unpack_from('<I', fixed, site)[0]
                                   for site in JUMP_SITES), (0, 0, 0, 0))
            bench = RealMetalBurstBench(
                raw, overlay10, fixed, overlay12, item_data)
            result = bench.run_case(
                attacker_item=ITEM_SHINY_STONE,
                target_item=ITEM_SHINY_STONE,
                attacker_ability=ABILITY_STALL,
                target_ability=ABILITY_STALL,
            )
            reads = Counter(offset for offset, size in result['script_reads']
                            if size == 4 and offset in JUMP_SITES)
            with self.subTest(language=language):
                self.assertEqual(reads, Counter({site: 1 for site in JUMP_SITES}))
                self.assertEqual(result['zero_cursor'], expected_cursor)
                self.assertEqual((result['order'], result['score']), (1, 100))
                self.assertEqual((result['state'], result['slot']), (2, 4))
                self.assertEqual((result['calls']['sort_entry'],
                                  result['calls']['sort_return']), (1, 1))
                self.assertGreaterEqual(result['calls']['get_item'], 20)
                self.assertEqual(result['calls']['check_ability'], 2)
                self.assertEqual(result['calls']['field_side'], 2)


if __name__ == '__main__':
    unittest.main()
