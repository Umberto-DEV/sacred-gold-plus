"""HG-B07: delayed Pressure PP must survive an immediate manual switch."""
import hashlib
import struct
import unittest

import ndspy.rom

from sgp131 import archives, mechanics_stages, pursuit_script, status_icon_script, uturn_script
from sgp131.test_legacy_scripts import inputs


SYNC_ATTACKER = (52, 8, 1, 52, 0)
SYNC_DEFENDER = (52, 8, 2, 52, 0)
SYNC_MSG_TEMP = (52, 8, 0xFF, 52, 0)

EXPECTED = {
    ('a/0/3/0', 89): (24, 44,
        '91ec5bf633f548c9d664bbb0affae5c4b5b86c9b1d92fe38eda5477f5d0c1554',
        '2b718ea1d3b1b97ba6f60fe828121152f494ddd2345737bf5aa1241867fb9959'),
    ('a/0/3/0', 144): (24, 44,
        'fc19e9888789e491c8cfd80dcf646aab4f6a1195c4d573c58866037fa7511c88',
        '4bbb8bad26252b35bd44d1816edb04c39f178f2c4e49eda0dda5593460b0da0d'),
    ('a/0/3/0', 227): (48, 68,
        'aa9b2b112d24996465122f8126840765910fff1b02df55758921e44572b9b4c2',
        '822bd719488011e36fc6c854198d924bcfdf518da735ca06ee699f181c1f6b19'),
    ('a/0/0/1', 139): (72, 92,
        '2ae643e8964525154b04686d72379e9889cad72ba90dfb0faf96f2207f28577a',
        'f1408fb6e82e5430bdd16f696d5d68c4f930e2e23725c78c8ad938c386e47804'),
    ('a/0/0/1', 146): (232, 252,
        '6b04238b8138556a891b579393c82d18262109c7526815abc9a4c5c45a0f055f',
        '2f8f0705793991ca0bb812337400c33bd07939926edaa6f0589fb7ef4ebb7548'),
}


def words(data):
    return struct.unpack('<%dI' % (len(data) // 4), data)


class PressureSwitchScripts(unittest.TestCase):
    @staticmethod
    def archive(data, name):
        rom = ndspy.rom.NintendoDSRom(data)
        fid = rom.filenames.idOf(name)
        return fid, bytes(rom.files[fid])

    def test_both_languages_install_only_five_authenticated_members(self):
        from sgp131 import pressure_switch_scripts as P
        records = []
        for language in ('EN', 'IT'):
            data = inputs(language)[0]
            effect = P.derive_effects(data, language)
            subs = P.derive_subscripts(data, language)
            resolve, file = archives.from_cartridge(data)
            self.assertEqual(archives.check_against(
                (effect, subs), resolve, file), (subs, effect))
            self.assertEqual((effect.archive, effect.file_id, effect.producers()),
                             ('a/0/3/0', 159, ['pressure-switch-effects']))
            self.assertEqual((subs.archive, subs.file_id, subs.producers()),
                             ('a/0/0/1', 130, ['pressure-switch-subscripts']))
            self.assertEqual([row.index for row in effect.members], [89, 144, 227])
            self.assertEqual([row.index for row in subs.members], [139, 146])
            for delta in (effect, subs):
                _, raw = self.archive(data, delta.archive)
                before = archives.members(raw)
                rebuilt = archives.apply_members(raw, delta.replacements())
                self.assertEqual(archives.verify_members(
                    raw, rebuilt, delta.replacements()),
                    {'members': len(before),
                     'changed': [row.index for row in delta.members]})
                for row in delta.members:
                    expected = EXPECTED[(delta.archive, row.index)]
                    old = before[row.index]
                    self.assertEqual((len(old), len(row.after),
                                      hashlib.sha256(old).hexdigest(),
                                      hashlib.sha256(row.after).hexdigest()), expected)
                    P.check(row.index, old, row.after, language)
            receipt = [subs.record(), effect.record()]
            replay = archives.rederive(data, language, None, receipt)
            self.assertEqual([delta.record() for delta in replay], receipt)
            records.append((effect.record(), subs.record()))
        self.assertEqual(records[0], records[1])

    def test_sync_commands_are_on_success_paths_and_preserve_status(self):
        from sgp131 import pressure_switch_scripts as P
        data = inputs('EN')[0]
        _, effect_raw = self.archive(data, 'a/0/3/0')
        _, sub_raw = self.archive(data, 'a/0/0/1')
        effect = archives.members(effect_raw)
        subs = archives.members(sub_raw)
        counter = words(P.patch_member('a/0/3/0', 89, effect[89]))
        mirror = words(P.patch_member('a/0/3/0', 144, effect[144]))
        metal = words(P.patch_member('a/0/3/0', 227, effect[227]))
        magic = words(P.patch_member('a/0/0/1', 139, subs[139]))
        snatch = words(P.patch_member('a/0/0/1', 146, subs[146]))
        self.assertEqual(counter, (50, 10, 6, 2048, 90) + SYNC_ATTACKER + (224,))
        self.assertEqual(mirror, (50, 10, 6, 2048, 91) + SYNC_ATTACKER + (224,))
        self.assertEqual(metal,
                         (147, 5, 50, 10, 6, 2048) + SYNC_ATTACKER
                         + (224, 50, 10, 10, 64, 224))
        self.assertEqual(magic[12:17], SYNC_DEFENDER)
        self.assertEqual(magic[17], 131)
        self.assertEqual(snatch[:9], (17, 14, 30, 15) + SYNC_MSG_TEMP)
        # ADD zero to BMON_DATA_STATUS is a semantic no-op whose consumer
        # still performs the existing BattleMon-to-PartyMon copy.
        for command in (SYNC_ATTACKER, SYNC_DEFENDER, SYNC_MSG_TEMP):
            self.assertEqual(command[0:2], (52, 8))
            self.assertEqual(command[3:], (52, 0))

    def test_subscripts_merge_with_existing_disjoint_repairs(self):
        from sgp131 import pressure_switch_scripts as P
        data = inputs('EN')[0]
        _, raw = self.archive(data, 'a/0/0/1')
        merged = archives.normalize((
            pursuit_script.derive(data, 'EN'),
            status_icon_script.derive(data, 'EN'),
            uturn_script.derive(data, 'EN'),
            P.derive_subscripts(data, 'EN'),
        ))
        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0].producers(), [
            'pressure-switch-subscripts', 'pursuit-script',
            'status-icon-script', 'uturn-item-snapshot'])
        self.assertEqual([row.index for row in merged[0].members],
                         [139, 146, 153, 175, 221])
        rebuilt = archives.apply_members(raw, merged[0].replacements())
        self.assertEqual(archives.verify_members(
            raw, rebuilt, merged[0].replacements()),
            {'members': 297, 'changed': [139, 146, 153, 175, 221]})

    def test_writer_checker_and_registry_fail_closed(self):
        from sgp131 import pressure_switch_scripts as P
        data = inputs('EN')[0]
        for archive, index in EXPECTED:
            _, raw = self.archive(data, archive)
            before = archives.members(raw)[index]
            after = P.patch_member(archive, index, before)
            with self.assertRaises(ValueError):
                P.patch_member(archive, index, after)
            for at in (0, len(after) // 2, len(after) - 1):
                mutant = bytearray(after)
                mutant[at] ^= 1
                with self.subTest(archive=archive, index=index, at=at), \
                        self.assertRaises(ValueError):
                    P.check(index, before, bytes(mutant), 'EN')
        _, effect_raw = self.archive(data, 'a/0/3/0')
        _, sub_raw = self.archive(data, 'a/0/0/1')
        effect_before = archives.members(effect_raw)[89]
        sub_before = archives.members(sub_raw)[139]
        with self.assertRaises(ValueError):
            P.check_effects(139, sub_before,
                            P.patch_member('a/0/0/1', 139, sub_before), 'EN')
        with self.assertRaises(ValueError):
            P.check_subscripts(89, effect_before,
                               P.patch_member('a/0/3/0', 89, effect_before), 'EN')
        stage = mechanics_stages.require_stage('legacy')
        self.assertEqual(stage.archive_producers.count('pressure-switch-effects'), 1)
        self.assertEqual(stage.archive_producers.count('pressure-switch-subscripts'), 1)


if __name__ == '__main__':
    unittest.main()
