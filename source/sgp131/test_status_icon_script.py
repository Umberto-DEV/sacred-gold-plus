"""HG-B06: volatile ability cures must not hide a persistent status icon."""
import hashlib
import struct
import unittest

import ndspy.rom

from sgp131 import archives, mechanics_stages, pursuit_script, uturn_script
from sgp131.test_legacy_scripts import inputs


CONFUSION = 0x7
ATTRACT = 0xF0000
NIGHTMARE = 0x08000000


def execute(member, message, status, status2):
    code = struct.unpack('<%dI' % (len(member) // 4), member)
    pc, emissions, waits = 0, [], 0
    for _ in range(64):
        op = code[pc]
        if op == 18:
            pc += 6
        elif op == 14:
            pc += 1
        elif op == 30:
            waits += 1
            pc += 2
        elif op == 32:
            operation, variable, value, displacement = code[pc + 1:pc + 5]
            if (operation, variable) != (0, 22):
                raise AssertionError('foreign comparison')
            pc += 5
            if message == value:
                pc += displacement
        elif op == 66:
            emissions.append(code[pc + 2])
            pc += 3
        elif op == 52:
            operation, battler, variable, value = code[pc + 1:pc + 5]
            if battler != 0xFF:
                raise AssertionError('foreign battler')
            if variable == 52 and operation == 7:
                status = value
            elif variable == 53 and operation == 11:
                status2 &= ~value & 0xFFFFFFFF
            else:
                raise AssertionError('foreign update')
            pc += 5
        elif op == 59:
            pc += 2 + code[pc + 1]
        elif op == 224:
            return status, status2, emissions, waits
        else:
            raise AssertionError('foreign opcode %d' % op)
    raise AssertionError('unterminated script')


class StatusIconScriptDelta(unittest.TestCase):
    @staticmethod
    def archive(data):
        rom = ndspy.rom.NintendoDSRom(data)
        fid = rom.filenames.idOf('a/0/0/1')
        return fid, bytes(rom.files[fid])

    def test_both_languages_install_the_pinned_branch_repair(self):
        from sgp131 import status_icon_script as S
        records = []
        for language in ('EN', 'IT'):
            data = inputs(language)[0]
            fid, raw = self.archive(data)
            before = archives.members(raw)[221]
            delta = S.derive(data, language)
            after = delta.members[0].after
            self.assertEqual((fid, hashlib.sha256(raw).hexdigest()),
                             (130, S.ARCHIVE_SHA256))
            self.assertEqual((len(before), hashlib.sha256(before).hexdigest()),
                             (236, S.BEFORE_SHA256))
            self.assertEqual((len(after), hashlib.sha256(after).hexdigest()),
                             (252, S.AFTER_SHA256))
            self.assertEqual((delta.archive, delta.file_id, delta.producers()),
                             ('a/0/0/1', 130, ['status-icon-script']))
            self.assertEqual([row.index for row in delta.members], [221])
            rebuilt = archives.apply_members(raw, delta.replacements())
            self.assertEqual((len(rebuilt), hashlib.sha256(rebuilt).hexdigest()),
                             (53920, S.AFTER_ARCHIVE_SHA256))
            self.assertEqual(archives.verify_members(
                raw, rebuilt, delta.replacements()),
                {'members': 297, 'changed': [221]})
            S.check(221, before, after, language)
            records.append(delta.record())
        self.assertEqual(records[0], records[1])

    def test_volatile_cures_preserve_status_and_skip_only_visual_clear(self):
        from sgp131 import status_icon_script as S
        data = inputs('EN')[0]
        before = archives.members(self.archive(data)[1])[221]
        after = S.patch_member(before)
        statuses = (0, 3, 8, 16, 32, 64, 0x380)
        for message, target in ((5, CONFUSION), (6, ATTRACT)):
            for status in statuses:
                other = NIGHTMARE | (ATTRACT if message == 5 else CONFUSION)
                initial2 = target | other
                with self.subTest(message=message, status=status):
                    old = execute(before, message, status, initial2)
                    new = execute(after, message, status, initial2)
                    self.assertEqual(old[:2], (status, other))
                    self.assertEqual(new[:2], (status, other))
                    self.assertEqual(old[2:], ([0], 1))
                    self.assertEqual(new[2:], ([], 1))

    def test_persistent_cures_keep_icon_clear_wait_and_mutations(self):
        from sgp131 import status_icon_script as S
        data = inputs('EN')[0]
        before = archives.members(self.archive(data)[1])[221]
        after = S.patch_member(before)
        cases = ((0, 3, NIGHTMARE | CONFUSION, CONFUSION),
                 (1, 8, 0, 0), (2, 16, 0, 0),
                 (3, 64, 0, 0), (4, 32, 0, 0))
        for message, status, status2, remaining in cases:
            with self.subTest(message=message):
                expected = (0, remaining, [0], 1)
                self.assertEqual(execute(before, message, status, status2), expected)
                self.assertEqual(execute(after, message, status, status2), expected)

    def test_archive_merge_preserves_other_members_and_existing_fixes(self):
        from sgp131 import status_icon_script as S
        data = inputs('EN')[0]
        raw = self.archive(data)[1]
        deltas = archives.normalize((pursuit_script.derive(data, 'EN'),
                                     uturn_script.derive(data, 'EN'),
                                     S.derive(data, 'EN')))
        self.assertEqual(len(deltas), 1)
        self.assertEqual(deltas[0].producers(),
                         ['pursuit-script', 'status-icon-script',
                          'uturn-item-snapshot'])
        self.assertEqual([row.index for row in deltas[0].members],
                         [153, 175, 221])
        rebuilt = archives.apply_members(raw, deltas[0].replacements())
        self.assertEqual(archives.verify_members(
            raw, rebuilt, deltas[0].replacements()),
            {'members': 297, 'changed': [153, 175, 221]})

    def test_writer_checker_and_owner_fail_closed(self):
        from sgp131 import status_icon_script as S
        data = inputs('EN')[0]
        before = archives.members(self.archive(data)[1])[221]
        after = S.patch_member(before)
        with self.assertRaises(ValueError):
            S.patch_member(after)
        for at in (0, 28, 44, 60, 100, 180, len(after) - 1):
            mutant = bytearray(after)
            mutant[at] ^= 1
            with self.subTest(at=at), self.assertRaises(ValueError):
                S.check(221, before, bytes(mutant), 'EN')
        stage = mechanics_stages.require_stage('legacy')
        self.assertEqual(stage.archive_producers.count('status-icon-script'), 1)


if __name__ == '__main__':
    unittest.main()
