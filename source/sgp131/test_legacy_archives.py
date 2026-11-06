"""Class B: legacy script member deltas and the one-writer archive contract."""
import importlib.util
import copy
import hashlib
import os
from pathlib import Path
import struct
import tempfile
import unittest
from unittest import mock

from sgp131 import archives
from sgp131.test_legacy_scripts import inputs


class ProducerBoundary(unittest.TestCase):
    def test_member_delta_is_reviewable_without_writing_a_cartridge(self):
        # A missing producer or one returning a whole image cannot satisfy this boundary.
        data, raw, _ = inputs('EN')
        if importlib.util.find_spec('sgp131.legacy_archives') is None:
            delta = None
        else:
            from sgp131 import legacy_archives as LA
            delta = LA.derive_legacy_scripts(data, 'EN')
        self.assertIsInstance(delta, archives.ArchiveDelta)
        self.assertEqual([row.index for row in delta.members], [93, 141, 237, 757, 874, 932])
        self.assertEqual((delta.archive, delta.producers()), ('a/0/1/2', ['legacy-scripts']))
        self.assertLess(delta.total_after_bytes(),
                        sum(len(raw[i]) for i in (93, 141, 237, 757, 874, 932)) + 260)


class MemberDeltas(unittest.TestCase):
    def setUp(self):
        from sgp131 import legacy_archives, legacy_scripts
        self.A, self.S = legacy_archives, legacy_scripts

    def delta(self, language):
        return self.A.derive_legacy_scripts(inputs(language)[0], language)

    def test_both_languages_have_exactly_six_independently_checked_members(self):
        for language in ('EN', 'IT'):
            _, raw, commands = inputs(language)
            delta = self.delta(language)
            with self.subTest(language=language):
                self.assertEqual(self.A.script_members(), [93, 141, 237, 757, 874, 932])
                self.assertEqual({r.index: len(r.after) - len(raw[r.index]) for r in delta.members},
                                 {93: 4, 141: 0, 237: 6, 757: 142, 874: 20, 932: 82})
                for row in delta.members:
                    self.A.check_scripts(row.index, raw[row.index], row.after, language)
                    self.S.verify_member(raw[row.index], row.after, language, row.index, commands)
                    self.assertEqual(row.before_sha256, hashlib.sha256(raw[row.index]).hexdigest())

    def test_gift_and_legacy_deltas_merge_without_duplicate_archive_members(self):
        from sgp131 import gifts_archives
        for language in ('EN', 'IT'):
            data, raw, _ = inputs(language)
            a, b = self.delta(language), gifts_archives.derive_gifts_scripts(data, language)
            with mock.patch.dict(archives.PRODUCERS, self.A.PRODUCERS), \
                 mock.patch.dict(archives.CHECKERS, self.A.CHECKERS):
                merged = archives.normalize([a, b])
                reverse = archives.normalize([b, a])
                self.assertEqual([d.record() for d in merged], [d.record() for d in reverse])
                self.assertEqual(len(merged), 1)
                resolve, file = archives.from_cartridge(data)
                checked = archives.check_against(merged, resolve, file)
                combined = checked[0]
                rebuilt = archives.apply_members(file(combined.file_id), combined.replacements())
                archives.verify_members(file(combined.file_id), rebuilt, combined.replacements())
                new = archives.members(rebuilt)
                changed = {i for i, (old, after) in enumerate(zip(raw, new)) if old != after}
                with self.subTest(language=language):
                    self.assertEqual(changed, {93, 141, 225, 227, 232, 237, 243, 246,
                                               757, 874, 932, 938, 962})
                    self.assertEqual(len(raw), len(new))
                    replay = archives.rederive(data, language, None, [combined.record()])
                    self.assertEqual([d.record() for d in replay], [combined.record()])

    def test_checker_refuses_wrong_member_language_and_altered_replacements(self):
        _, raw, _ = inputs('EN')
        delta = self.delta('EN')
        for row in delta.members:
            for index, before, after, language in (
                (row.index, raw[row.index], raw[row.index], 'EN'),
                (row.index, raw[row.index], row.after + b'\0', 'EN'),
                (row.index, raw[row.index] + b'\0', row.after, 'EN'),
                (890, raw[row.index], row.after, 'EN'),
                (row.index, raw[row.index], row.after, 'FR'),
                ('93', None, bytearray(row.after), 'EN'),
            ):
                with self.subTest(member=row.index, index=index, language=language), self.assertRaises(ValueError):
                    self.A.check_scripts(index, before, after, language)

    def test_new_bag_checks_take_the_installed_wrappers_native_path(self):
        from sgp131.gifts_audit import Arm9View
        for language in ('EN', 'IT'):
            data, _, commands = inputs(language)
            table = set(struct.unpack('<120I', Arm9View(data).read(0x023DB300, 480)))
            after = next(r.after for r in self.delta(language).members if r.index == 757)
            with self.subTest(language=language):
                self.assertEqual(self.A._space_keys(after, commands), [0x06EC0F1D, 0x074BB361])
                self.assertFalse(table & {0x06EC0F1D, 0x074BB361})

    def test_native_standard_and_message_preimages_are_admission_guards(self):
        data, _, _ = inputs('EN')
        with mock.patch.object(self.A, 'STANDARD_PREIMAGE', '0' * 64):
            with self.assertRaisesRegex(ValueError, 'standard2009/2033'):
                self.A.derive_legacy_scripts(data, 'EN')
        with mock.patch.dict(self.A.MESSAGE_PREIMAGES, {'EN': '0' * 64}):
            with self.assertRaisesRegex(ValueError, 'message bank'):
                self.A.derive_legacy_scripts(data, 'EN')

    def test_a_permissive_key_collision_is_refused_by_the_producer(self):
        data, _, _ = inputs('EN')
        from sgp131.gifts_audit import Arm9View
        keys = struct.unpack('<120I', Arm9View(data).read(0x023DB300, 480))
        occupied = next(k for k in keys if k)
        with mock.patch.object(self.A, '_space_keys', lambda *args: [occupied]):
            with self.assertRaisesRegex(ValueError, 'permissive Bag key'):
                self.A.derive_legacy_scripts(data, 'EN')

    def test_foreign_metadata_and_guide_audited_members_are_refused(self):
        data, _, _ = inputs('EN')
        real_metadata = self.A._commands()
        foreign = copy.copy(real_metadata)
        foreign.metadata_sha256 = '0' * 64
        with mock.patch.object(self.A, '_commands', lambda: foreign):
            with self.assertRaisesRegex(ValueError, 'metadata'):
                self.A.derive_legacy_scripts(data, 'EN')
        with mock.patch.object(self.S, 'MEMBERS', (93, 141, 757, 890)):
            with self.assertRaisesRegex(ValueError, 'Guide'):
                self.A.derive_legacy_scripts(data, 'EN')

    def test_metadata_loader_rejects_changed_bytes_even_with_the_same_commands(self):
        pret = Path(os.environ.get('SGP_PRET_SOURCE') or self.A.ROOT / 'local' / 'tools' / 'pokeheartgold')
        source = pret / 'tools' / 'py_scripts' / 'scrcmd.json'
        inputs('EN')
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'tools' / 'py_scripts'
            target.mkdir(parents=True)
            (target / 'scrcmd.json').write_bytes(source.read_bytes() + b'\n')
            with mock.patch.dict(os.environ, {'SGP_PRET_SOURCE': directory}):
                with self.assertRaisesRegex(ValueError, 'pinned|SHA-256'):
                    self.A._commands()


class PoisonFollowerDelta(unittest.TestCase):
    """HG-F05: poison survival must let LockAll finish an active follower jump."""

    def test_survival_standard_enters_lockall_without_forcing_follower_reset(self):
        from sgp131 import gifts_scripts, legacy_archives as LA
        for language in ('EN', 'IT'):
            data, members, commands = inputs(language)
            before = members[3]
            parsed = gifts_scripts.decode(before, commands, 3)
            entry = parsed.entry[3]
            self.assertEqual((entry, struct.unpack_from('<H', before, entry)[0]),
                             (0x584, 609))

            after = next(row.after for row in LA.derive_poison_follower(data, language).members)
            fixed = gifts_scripts.decode(after, commands, 3)
            fixed_entry = fixed.entry[3]
            with self.subTest(language=language):
                self.assertEqual(struct.unpack_from('<H', after, fixed_entry)[0], 96)
                self.assertEqual(fixed_entry, entry + 2)
                self.assertEqual(len(after), len(before))

    def test_exact_component_delta_checker_archive_replay_and_native_contract(self):
        from sgp131 import legacy_archives as LA
        records = []
        for language in ('EN', 'IT'):
            data, members, _ = inputs(language)
            delta = LA.derive_poison_follower(data, language)
            self.assertEqual((delta.archive, delta.producers(), [r.index for r in delta.members]),
                             ('a/0/1/2', ['poison-follower-script'], [3]))
            row = delta.members[0]
            before, after = members[3], row.after
            with self.subTest(language=language):
                self.assertEqual(row.before_sha256, LA.STANDARD_PREIMAGE)
                self.assertEqual(hashlib.sha256(after).hexdigest(), LA.POISON_AFTER)
                self.assertEqual(after[:12] + after[16:], before[:12] + before[16:])
                self.assertEqual(struct.unpack_from('<i', before, 12)[0], 1396)
                self.assertEqual(struct.unpack_from('<i', after, 12)[0], 1398)
                self.assertEqual(LA._poison_executable_sha256(data),
                                 LA.POISON_EXECUTABLE_SHA256)
                LA.check_poison_follower(3, before, after, language)

                resolve, file = archives.from_cartridge(data)
                self.assertEqual(archives.check_against((delta,), resolve, file), (delta,))
                rebuilt = archives.apply_members(file(delta.file_id), delta.replacements())
                self.assertEqual(len(rebuilt), len(file(delta.file_id)))
                archives.verify_members(file(delta.file_id), rebuilt, delta.replacements())
                archives.check_semantics(delta, file(delta.file_id), rebuilt, language)
                replay = archives.rederive(data, language, None, [delta.record()])
                self.assertEqual([item.record() for item in replay], [delta.record()])
            records.append(delta.record())
        self.assertEqual(records[0], records[1])

    def test_mutants_wrong_identity_language_and_executable_contract_are_refused(self):
        from sgp131 import legacy_archives as LA
        data, members, _ = inputs('EN')
        row = LA.derive_poison_follower(data, 'EN').members[0]
        before, after = members[3], row.after
        cases = (
            (4, before, after, 'EN'),
            (3, before, after, 'FR'),
            (3, before + b'\0', after, 'EN'),
            (3, before, after + b'\0', 'EN'),
            (3, before, after[:0x584] + b'\0' + after[0x585:], 'EN'),
            ('3', None, bytearray(after), 'EN'),
        )
        for index, old, new, language in cases:
            with self.subTest(index=index, language=language), self.assertRaises(ValueError):
                LA.check_poison_follower(index, old, new, language)
        with mock.patch.object(LA, 'POISON_EXECUTABLE_SHA256', '0' * 64):
            with self.assertRaisesRegex(ValueError, 'executable contract'):
                LA.derive_poison_follower(data, 'EN')


class EventDeltas(unittest.TestCase):
    """H1: ordinary Plus interactions must not enter the hidden-item flag path."""

    CASES = {71: (7, 19, 433, 454), 440: (5, 14, 50, 24)}

    def setUp(self):
        from sgp131 import legacy_archives
        self.A = legacy_archives

    @staticmethod
    def event_members(data):
        import ndspy.rom
        rom = ndspy.rom.NintendoDSRom(data)
        fid = rom.filenames.idOf('a/0/3/2')
        return fid, archives.members(bytes(rom.files[fid]))

    @staticmethod
    def background(member, row):
        count = struct.unpack_from('<I', member)[0]
        if not 0 <= row < count or 4 + count * 20 > len(member):
            raise ValueError('background row outside member')
        return struct.unpack_from('<HHiiiH2x', member, 4 + row * 20)

    def test_two_pinned_members_change_only_the_event_type_halfword(self):
        records = []
        for language in ('EN', 'IT'):
            data = inputs(language)[0]
            fid, old = self.event_members(data)
            delta = self.A.derive_legacy_events(data, language)
            self.assertEqual((delta.archive, delta.file_id, delta.producers()),
                             ('a/0/3/2', fid, ['legacy-events']))
            self.assertEqual([row.index for row in delta.members], [71, 440])
            for declared in delta.members:
                row, script, x, z = self.CASES[declared.index]
                before, after = old[declared.index], declared.after
                at = 4 + row * 20 + 2
                with self.subTest(language=language, member=declared.index):
                    self.assertEqual(self.background(before, row), (script, 2, x, z, 0, 0))
                    self.assertEqual(self.background(after, row), (script, 1, x, z, 0, 0))
                    self.assertEqual(after[:at] + after[at + 2:], before[:at] + before[at + 2:])
                    self.assertEqual(declared.before_sha256, hashlib.sha256(before).hexdigest())
                    self.A.check_events(declared.index, before, after, language)
            records.append(delta.record())
        self.assertEqual(records[0], records[1])

    def test_real_hidden_items_and_all_unrelated_event_members_remain_unchanged(self):
        data = inputs('EN')[0]
        fid, old = self.event_members(data)
        delta = self.A.derive_legacy_events(data, 'EN')
        resolve, file = archives.from_cartridge(data)
        self.assertEqual(archives.check_against((delta,), resolve, file), (delta,))
        rebuilt = archives.apply_members(file(fid), delta.replacements())
        archives.verify_members(file(fid), rebuilt, delta.replacements())
        archives.check_semantics(delta, file(fid), rebuilt, 'EN')
        new = archives.members(rebuilt)
        self.assertEqual([i for i, (a, b) in enumerate(zip(old, new)) if a != b], [71, 440])
        # Retail hidden-item row 6 in Azalea stays type 2 with its 8000+ script id.
        self.assertEqual(self.background(old[71], 6), self.background(new[71], 6))
        self.assertEqual(self.background(new[71], 6)[:2], (8006, 2))
        replay = archives.rederive(data, 'EN', None, [delta.record()])
        self.assertEqual([item.record() for item in replay], [delta.record()])

    def test_checker_refuses_wrong_identity_geometry_or_extra_edits(self):
        data = inputs('EN')[0]
        _, old = self.event_members(data)
        delta = self.A.derive_legacy_events(data, 'EN')
        for declared in delta.members:
            cases = (
                (declared.index, old[declared.index], old[declared.index], 'EN'),
                (declared.index, old[declared.index], declared.after + b'\0', 'EN'),
                (declared.index, old[declared.index] + b'\0', declared.after, 'EN'),
                (72, old[declared.index], declared.after, 'EN'),
                (declared.index, old[declared.index], declared.after, 'FR'),
            )
            for index, before, after, language in cases:
                with self.subTest(member=declared.index, index=index, language=language), self.assertRaises(ValueError):
                    self.A.check_events(index, before, after, language)


if __name__ == '__main__':
    unittest.main()
