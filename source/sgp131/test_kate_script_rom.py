"""HG-F19: reproduce and repair Ace Trainer Kate's side-interaction path.

The Route 34 coordinate trigger is valid only for the straight approach.  The
same object is also directly interactable.  In the inherited script that path
faces Kate toward the player but, while the sisters state is still one,
displays her post-battle apology and ends.  A later coordinate trigger then
starts the battle from the orientation mutated by that conversation.

The bounded model below executes decoded, authenticated script commands.  It
does not emulate rendering, movement scheduling or a complete battle.
"""
import hashlib
import struct
import unittest

import ndspy.narc
import ndspy.rom

from sgp131 import gifts_scripts as GS
from sgp131.test_legacy_scripts import inputs


MEMBER = 237
MEMBER_SHA256 = '3a038af0fa5797f18ec350982e5850c0d9ba875f34f77026182fd2c6f5bf3040'
EVENT_MEMBER = 35
EVENT_SHA256 = '3a6c30a161df82064fd247355fe8bf1074e9e6a6f5c2b4d2ff92ed2a3f95b3e8'

KATE_COORD_ENTRY = 5
KATE_OBJECT_ENTRY = 8
KATE_STATE = 0x4097
KATE_TRAINER = 118
KATE_PRE_BATTLE_MSG = 28
KATE_REWARD_MSG = 30
KATE_POST_BATTLE_MSG = 32
POWER_HERB = 271

OBJECT_ROW = (7, 327, 0, 0, 0, 9, 0, 0, 0, 0, 0, 0, 370, 476, 0)
COORD_ROWS = (
    (5, 370, 472, 1, 1, 0, 0, 0x4097),
    (6, 370, 473, 1, 1, 0, 1, 0x4097),
)


def _sha(raw):
    return hashlib.sha256(bytes(raw)).hexdigest()


def _events(data):
    rom = ndspy.rom.NintendoDSRom(data)
    raw = bytes(ndspy.narc.NARC(rom.getFileByName('a/0/3/2')).files[EVENT_MEMBER])
    if _sha(raw) != EVENT_SHA256:
        raise AssertionError('Route 34 event member differs from the pinned V4')
    offset, groups = 0, []
    for size, fmt in ((20, '<HHiiiH2x'), (32, '<6Hh3HhhHHi'),
                      (12, '<4Hi'), (16, '<8H')):
        count = struct.unpack_from('<I', raw, offset)[0]
        offset += 4
        groups.append([struct.unpack_from(fmt, raw, offset + row * size)
                       for row in range(count)])
        offset += count * size
    if offset != len(raw) or tuple(map(len, groups)) != (6, 18, 3, 3):
        raise AssertionError('Route 34 event geometry differs')
    return groups


class ScriptPath:
    """Execute only the commands reached by the three Kate states."""

    UI = {'PlaySE', 'LockAll', 'FacePlayer', 'ScrCmd_609', 'ApplyMovement',
          'StopBGM', 'PlayBGM', 'WaitMovement', 'CloseMsg', 'WaitButton',
          'ReleaseAll'}

    def __init__(self, raw, commands, state, *, won=True, space=True):
        self.member = GS.decode(raw, commands, MEMBER)
        self.vars = {KATE_STATE: state}
        self.won, self.space = won, space
        self.cmp = -1
        self.messages, self.battles, self.gives, self.log = [], [], [], []

    def _condition(self, code):
        return {0: self.cmp < 0, 1: self.cmp == 0, 2: self.cmp > 0,
                3: self.cmp <= 0, 4: self.cmp >= 0, 5: self.cmp != 0}[code]

    def run(self, entry, steps=160):
        pc = self.member.entry[entry]
        for _ in range(steps):
            ins = self.member.istruzioni.get(pc)
            if ins is None:
                raise AssertionError('Kate model left decoded code at %#x' % pc)
            name, args = ins.nome, ins.args
            self.log.append((ins.off, name, tuple(args)))
            pc = ins.fine
            target = ins.rami[0][1] if ins.rami else None
            if name == 'End':
                return self
            if name == 'GoTo':
                pc = target
            elif name == 'GoToIf':
                if self._condition(args[0]):
                    pc = target
            elif name == 'CompareVarToValue':
                value = self.vars.get(args[0], 0)
                self.cmp = (value > args[1]) - (value < args[1])
            elif name == 'SetVar':
                self.vars[args[0]] = args[1]
            elif name == 'NPCMsg':
                self.messages.append(args[0])
            elif name == 'TrainerBattle':
                self.battles.append(args[0])
            elif name == 'CheckBattleWon':
                self.vars[args[0]] = int(self.won)
            elif name == 'HasSpaceForItem':
                self.vars[args[2]] = int(self.space)
            elif name == 'CallStd':
                if args[0] == 2033:
                    self.gives.append((self.vars.get(0x8004),
                                       self.vars.get(0x8005)))
                elif args[0] != 2009:
                    raise AssertionError('unexpected Kate standard %d' % args[0])
            elif name == 'WhiteOut':
                if self.won:
                    raise AssertionError('winning Kate path reached WhiteOut')
                return self
            elif name not in self.UI:
                raise AssertionError('unsupported Kate command ' + name)
        raise AssertionError('Kate model did not terminate')


class KateScriptRomTests(unittest.TestCase):
    def test_v4_binds_the_route_and_reproduces_side_apology_before_battle(self):
        for language in ('EN', 'IT'):
            data, members, commands = inputs(language)
            self.assertEqual(_sha(members[MEMBER]), MEMBER_SHA256)
            groups = _events(data)
            self.assertEqual(groups[1][7], OBJECT_ROW)
            self.assertEqual(tuple(groups[3][1:]), COORD_ROWS)

            direct = ScriptPath(members[MEMBER], commands, 1).run(KATE_OBJECT_ENTRY)
            straight = ScriptPath(members[MEMBER], commands, 1).run(KATE_COORD_ENTRY)
            with self.subTest(language=language):
                self.assertEqual(direct.messages, [KATE_POST_BATTLE_MSG])
                self.assertEqual(direct.battles, [])
                self.assertEqual(straight.messages[:2],
                                 [KATE_PRE_BATTLE_MSG, KATE_REWARD_MSG])
                self.assertEqual(straight.battles, [KATE_TRAINER])

    def test_repair_routes_all_four_states_without_changing_other_entries(self):
        from sgp131 import legacy_scripts

        for language in ('EN', 'IT'):
            _data, members, commands = inputs(language)
            before = members[MEMBER]
            after = legacy_scripts.patch_member(before, language, MEMBER, commands)
            old, new = GS.decode(before, commands, MEMBER), GS.decode(after, commands, MEMBER)
            with self.subTest(language=language):
                self.assertEqual(len(after), len(before) + 6)
                self.assertEqual(new.entry,
                                 [offset + (6 if offset >= 0x2BF else 0)
                                  for offset in old.entry])

                before_sisters = ScriptPath(after, commands, 0).run(KATE_OBJECT_ENTRY)
                pre = ScriptPath(after, commands, 1).run(KATE_OBJECT_ENTRY)
                reward = ScriptPath(after, commands, 2).run(KATE_OBJECT_ENTRY)
                done = ScriptPath(after, commands, 3).run(KATE_OBJECT_ENTRY)
                self.assertEqual((before_sisters.messages, before_sisters.battles,
                                  before_sisters.gives),
                                 ([KATE_POST_BATTLE_MSG], [], []))
                self.assertEqual((pre.messages[:2], pre.battles, pre.gives),
                                 ([KATE_PRE_BATTLE_MSG, KATE_REWARD_MSG],
                                  [KATE_TRAINER], [(POWER_HERB, 1)]))
                self.assertEqual((reward.messages, reward.battles, reward.gives),
                                 ([KATE_REWARD_MSG, KATE_POST_BATTLE_MSG],
                                  [], [(POWER_HERB, 1)]))
                self.assertEqual((done.messages, done.battles, done.gives),
                                 ([KATE_POST_BATTLE_MSG], [], []))

                # The normal straight approach and both sisters remain exact.
                straight_after = ScriptPath(after, commands, 1).run(KATE_COORD_ENTRY)
                straight_before = ScriptPath(before, commands, 1).run(KATE_COORD_ENTRY)
                self.assertEqual(([name for _, name, _ in straight_after.log],
                                  straight_after.messages, straight_after.battles,
                                  straight_after.gives, straight_after.vars),
                                 ([name for _, name, _ in straight_before.log],
                                  straight_before.messages, straight_before.battles,
                                  straight_before.gives, straight_before.vars))
                for entry in (6, 7):
                    self.assertEqual(new.entry[entry], old.entry[entry])

    def test_repair_rejects_reapplication_and_foreign_preimages(self):
        from sgp131 import legacy_scripts

        _data, members, commands = inputs('EN')
        repaired = legacy_scripts.patch_member(members[MEMBER], 'EN', MEMBER, commands)
        with self.assertRaises(ValueError):
            legacy_scripts.patch_member(repaired, 'EN', MEMBER, commands)
        foreign = bytearray(members[MEMBER])
        foreign[0x2B5] ^= 1
        with self.assertRaises(ValueError):
            legacy_scripts.patch_member(bytes(foreign), 'EN', MEMBER, commands)


if __name__ == '__main__':
    unittest.main()
