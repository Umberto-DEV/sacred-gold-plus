"""HG-T10 local script guard: pure member transform and hostile-input checks."""
import copy
import hashlib
import importlib
from pathlib import Path
import unittest

import ndspy.narc
import ndspy.rom

from sgp131 import gifts_audit, gifts_scripts


ROOT = Path(__file__).resolve().parents[2]
V4_ROOT = ROOT / 'local/experiments/balance493-2026-10-28'
ROM_SHA256 = {
    'EN': '179edfb1ca331503f438e98f3afccfb0ab85759bf9ab88fb86c735f5fcefbf90',
    'IT': '2a2f0b437fca524c18b71b20feb01a1f51351e61c7c897ce73d9b3be1ee3a156',
}


class LegendaryScenesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            cls.scenes = importlib.import_module('sgp131.legendary_scenes')
        except ModuleNotFoundError as error:
            if error.name != 'sgp131.legendary_scenes':
                raise
            cls.scenes = None
        metadata = ROOT / 'local/tools/pokeheartgold/tools/py_scripts/scrcmd.json'
        if not metadata.is_file():
            raise unittest.SkipTest('pinned script metadata unavailable')
        cls.commands = gifts_audit.load_commands(metadata)

    def member(self, language):
        if self.scenes is None:
            self.fail('sgp131.legendary_scenes is missing')
        scenes = self.scenes
        path = V4_ROOT / ('candidate-v4-%s.nds' % language)
        if not path.is_file():
            self.skipTest('immutable V4 candidate unavailable')
        data = path.read_bytes()
        self.assertEqual(hashlib.sha256(data).hexdigest(), ROM_SHA256[language])
        rom = ndspy.rom.NintendoDSRom(data)
        return bytes(ndspy.narc.NARC(rom.getFileByName(scenes.ARCHIVE)).files[scenes.MEMBER])

    def test_transform_adds_guard_and_preserves_all_old_edges_and_movements(self):
        scenes = self.scenes
        for language in ('EN', 'IT'):
            before = self.member(language)
            after = scenes.patch_member(before, self.commands)
            report = scenes.verify_member(before, after, self.commands)
            parsed = gifts_scripts.decode(after, self.commands, scenes.MEMBER)
            with self.subTest(language=language):
                self.assertEqual(report['bytes_added'], 18)
                self.assertEqual(report['entry_count'], 7)
                self.assertGreater(report['surviving_instructions'], 100)
                self.assertEqual(parsed.dati_movimento,
                                 {site + 18 if site >= 0x686 else site
                                  for site in gifts_scripts.decode(
                                      before, self.commands, scenes.MEMBER).dati_movimento})

    def test_transform_rejects_foreign_preimage_and_command_metadata(self):
        scenes = self.scenes
        before = self.member('EN')
        foreign = bytearray(before)
        foreign[-1] ^= 1
        with self.assertRaisesRegex(ValueError, 'preimage'):
            scenes.patch_member(bytes(foreign), self.commands)
        commands = copy.copy(self.commands)
        commands.metadata_sha256 = '0' * 64
        with self.assertRaisesRegex(ValueError, 'metadata'):
            scenes.patch_member(before, commands)

    def test_verifier_rejects_guard_branch_and_complement_mutants(self):
        scenes = self.scenes
        before = self.member('EN')
        after = scenes.patch_member(before, self.commands)
        for offset in (0x684, 0x720):
            mutant = bytearray(after)
            mutant[offset] ^= 1
            with self.subTest(offset=hex(offset)), self.assertRaises(ValueError):
                scenes.verify_member(before, bytes(mutant), self.commands)


if __name__ == '__main__':
    unittest.main()
