"""Evolution repairs are exact member deltas and the Guide consumes the same records."""
import hashlib
import struct
import unittest

import ndspy.rom

from sgp131 import archives, mechanics_stages
from sgp131.test_legacy_scripts import inputs


class EvolutionDeltas(unittest.TestCase):
    CASES = {
        349: ((15, 0, 350), (15, 170, 350)),       # Feebas: beauty 170
        412: ((23, 0, 413), (23, 20, 413)),        # Burmy female: level 20
        415: ((23, 0, 416), (23, 21, 416)),        # Combee female: level 21
        458: ((21, 100, 226), (21, 223, 226)),     # Mantyke: Remoraid in party
    }

    @staticmethod
    def members(data):
        rom = ndspy.rom.NintendoDSRom(data)
        fid = rom.filenames.idOf('a/0/3/4')
        return fid, archives.members(bytes(rom.files[fid]))

    def test_both_languages_repair_only_four_pinned_records(self):
        from sgp131 import evolution_fixes as E
        records = []
        for language in ('EN', 'IT'):
            data = inputs(language)[0]
            fid, old = self.members(data)
            delta = E.derive(data, language)
            self.assertEqual((delta.archive, delta.file_id, delta.producers()),
                             ('a/0/3/4', fid, ['evolution-fixes']))
            self.assertEqual([row.index for row in delta.members], sorted(self.CASES))
            for declared in delta.members:
                before, after = old[declared.index], declared.after
                expected_before, expected_after = self.CASES[declared.index]
                with self.subTest(language=language, member=declared.index):
                    self.assertEqual(struct.unpack_from('<3H', before), expected_before)
                    self.assertEqual(struct.unpack_from('<3H', after), expected_after)
                    self.assertEqual(after[:2] + after[4:], before[:2] + before[4:])
                    self.assertEqual(declared.before_sha256, hashlib.sha256(before).hexdigest())
                    E.check(declared.index, before, after, language)
            records.append(delta.record())
        self.assertEqual(records[0], records[1])

    def test_archive_roundtrip_rederive_and_semantics(self):
        from sgp131 import evolution_fixes as E
        data = inputs('EN')[0]
        delta = E.derive(data, 'EN')
        resolve, file = archives.from_cartridge(data)
        self.assertEqual(archives.check_against((delta,), resolve, file), (delta,))
        rebuilt = archives.apply_members(file(delta.file_id), delta.replacements())
        self.assertEqual(archives.verify_members(file(delta.file_id), rebuilt, delta.replacements())['changed'],
                         sorted(self.CASES))
        archives.check_semantics(delta, file(delta.file_id), rebuilt, 'EN')
        replay = archives.rederive(data, 'EN', None, [delta.record()])
        self.assertEqual([item.record() for item in replay], [delta.record()])

    def test_checker_rejects_wrong_identity_threshold_or_extra_edit(self):
        from sgp131 import evolution_fixes as E
        data = inputs('EN')[0]
        _, old = self.members(data)
        delta = E.derive(data, 'EN')
        for declared in delta.members:
            cases = (
                (declared.index, old[declared.index], old[declared.index], 'EN'),
                (declared.index, old[declared.index], declared.after + b'\0', 'EN'),
                (declared.index, old[declared.index] + b'\0', declared.after, 'EN'),
                (0, old[declared.index], declared.after, 'EN'),
                (declared.index, old[declared.index], declared.after, 'FR'),
            )
            for index, before, after, language in cases:
                with self.subTest(member=declared.index, index=index, language=language), \
                        self.assertRaises(ValueError):
                    E.check(index, before, after, language)

    def test_legacy_stage_owns_evolution_archive_once(self):
        stage = mechanics_stages.require_stage('legacy')
        self.assertIn('evolution-fixes', stage.archive_producers)
        self.assertEqual(stage.archive_producers.count('evolution-fixes'), 1)


class GuideSource(unittest.TestCase):
    def test_guide_reads_the_repaired_evolution_members(self):
        from sgp131 import evolution_fixes as E, ui_compile
        data = inputs('EN')[0]
        delta = E.derive(data, 'EN')
        rom = ndspy.rom.NintendoDSRom(data)
        records = ui_compile.evolution_records(rom, (delta,))
        for index, (_before, expected) in EvolutionDeltas.CASES.items():
            with self.subTest(member=index):
                self.assertEqual(struct.unpack_from('<3H', records[index]), expected)


if __name__ == '__main__':
    unittest.main()
