"""SG-01a: bounded static reproducer for the Route 47 partner-heal lifetime."""
import os
import hashlib
from pathlib import Path
import unittest

import ndspy.narc
import ndspy.rom

from sgp131 import gifts_audit, gifts_scripts, safari_lifetime as S


ROOT = Path(__file__).resolve().parents[2]


class LifetimeOracle(unittest.TestCase):
    def test_close_before_field_unload_is_healthy(self):
        trace = ['NPCMsg', 'CloseMsg', 'FadeScreen', 'HealParty',
                 'ScrCmd_436', 'RestoreOverworld']
        self.assertEqual(S.classify_trace(trace), 'healthy')

    def test_close_after_field_reload_is_a_stale_owner_use(self):
        trace = ['NPCMsg', 'FadeScreen', 'HealParty', 'ScrCmd_436',
                 'RestoreOverworld', 'CloseMsg']
        self.assertEqual(S.classify_trace(trace), 'stale-window-close')

    def test_mutants_moving_close_across_unload_are_discriminated(self):
        affected_with_close_moved_before = [
            'NPCMsg', 'CloseMsg', 'FadeScreen', 'HealParty',
            'ScrCmd_436', 'RestoreOverworld']
        healthy_with_close_moved_after = [
            'NPCMsg', 'FadeScreen', 'HealParty', 'ScrCmd_436',
            'RestoreOverworld', 'CloseMsg']
        self.assertEqual(S.classify_trace(affected_with_close_moved_before), 'healthy')
        self.assertEqual(S.classify_trace(healthy_with_close_moved_after),
                         'stale-window-close')

    def test_unrelated_messages_without_field_unload_are_not_findings(self):
        self.assertEqual(S.classify_trace(['NPCMsg', 'WaitButton', 'CloseMsg']),
                         'healthy')

    def test_field_unload_without_a_later_close_is_not_the_close_defect(self):
        self.assertEqual(S.classify_trace(['OpenMsg', 'ScrCmd_436',
                                           'RestoreOverworld']),
                         'open-window-after-unload')

    def test_a_new_window_after_restore_has_a_fresh_owner(self):
        trace = ['OpenMsg', 'ScrCmd_436', 'RestoreOverworld',
                 'OpenMsg', 'CloseMsg']
        self.assertEqual(S.classify_trace(trace), 'healthy')

    def test_npc_message_does_not_reown_an_already_open_stale_window(self):
        trace = ['NPCMsg', 'ScrCmd_436', 'RestoreOverworld',
                 'NPCMsg', 'CloseMsg']
        self.assertEqual(S.classify_trace(trace), 'stale-window-close')


class ArchiveRegistration(unittest.TestCase):
    def test_safari_producer_is_registered_once_under_the_legacy_stage(self):
        from sgp131 import archives, mechanics_stages, safari_archives
        archives.register_owner_producers()
        self.assertIs(archives.PRODUCERS[safari_archives.SCRIPTS],
                      safari_archives.PRODUCERS[safari_archives.SCRIPTS])
        self.assertIs(archives.CHECKERS[safari_archives.SCRIPTS],
                      safari_archives.CHECKERS[safari_archives.SCRIPTS])
        self.assertEqual(mechanics_stages.REGISTRY['legacy'].archive_producers.count(
            safari_archives.SCRIPTS), 1)


class CurrentCandidateReproducer(unittest.TestCase):
    def material(self, language):
        default = ROOT / 'local/roms/1.3.1-ui-update-test' / (
            f'Sacred-Gold-Plus-1.3.1-{language}.nds')
        rom = Path(os.environ.get('SGP_SAFARI_ROM_' + language) or default)
        metadata = Path(os.environ.get('SGP_PRET_SOURCE') or
                        ROOT / 'local/tools/pokeheartgold') / 'tools/py_scripts/scrcmd.json'
        if not rom.is_file() or not metadata.is_file():
            if os.environ.get('SGP_SAFARI_REQUIRE_INPUTS') == '1':
                self.fail('authenticated Safari candidate or command metadata unavailable')
            self.skipTest('authenticated Safari candidate or command metadata unavailable')
        data = rom.read_bytes()
        archive = ndspy.narc.NARC(
            ndspy.rom.NintendoDSRom(data).getFileByName(S.SCRIPT_ARCHIVE))
        return data, bytes(archive.files[S.SCRIPT_MEMBER]), gifts_audit.load_commands(metadata)

    def audit(self, language):
        default = ROOT / 'local/roms/1.3.1-ui-update-test' / (
            f'Sacred-Gold-Plus-1.3.1-{language}.nds')
        rom = Path(os.environ.get('SGP_SAFARI_ROM_' + language) or default)
        metadata = Path(os.environ.get('SGP_PRET_SOURCE') or
                        ROOT / 'local/tools/pokeheartgold') / 'tools/py_scripts/scrcmd.json'
        if not rom.is_file() or not metadata.is_file():
            if os.environ.get('SGP_SAFARI_REQUIRE_INPUTS') == '1':
                self.fail('authenticated Safari candidate or command metadata unavailable')
            self.skipTest('authenticated Safari candidate or command metadata unavailable')
        return S.audit_rom(rom, language, metadata)

    @staticmethod
    def expected_repair(before):
        repaired = bytearray(before)
        # Hand-checked complete rotations, applied from the highest offset so
        # each earlier interval remains at its original address.
        for insert, close in ((0x588, 0x5AC), (0x482, 0x4A6), (0x338, 0x35C)):
            repaired[insert:close + 2] = b'\x35\x00' + repaired[insert:close]
        # Export 7 now points from header word 6 to the appended 23-byte
        # GetPlayerXYZ/height-equality wrapper.  The signed branch in this
        # exact candidate returns to the original entry at 0x1BF.
        repaired[24:28] = (2222).to_bytes(4, 'little')
        repaired.extend(bytes.fromhex(
            'ad020480058006801100058000001c0001e0f8ffff0200'))
        return bytes(repaired)

    def test_current_en_and_it_bind_route47_to_the_pinned_script_and_event(self):
        for language in ('EN', 'IT'):
            report = self.audit(language)
            with self.subTest(language=language):
                self.assertEqual(report['map'], {
                    'id': 151, 'script_member': 260, 'init_member': 505,
                    'message_member': 407, 'event_member': 146})
                self.assertEqual(report['script_sha256'],
                                 '998ab0b338b5b8bf4faea7579f2baa01bb21e54bc4a426fae1e7157c0df0c497')
                self.assertEqual(report['event_sha256'],
                                 '2640403256c62fe47dc9e1579dfd181f4deb65218765ed075266ed73743a0a66')
                self.assertTrue(report['native_dispatch']['verified'])
                self.assertIn('GetPlayerXYZ',
                              report['native_dispatch']['handlers'])
                self.assertIn('CoordEvent_XZ_only',
                              report['native_dispatch']['callees'])
                self.assertTrue(report['source_model']['verified'])
                self.assertTrue(report['input_unchanged'])

    def test_mira_is_healthy_and_the_next_three_partner_heals_are_defective(self):
        expected = {'Mira': 'healthy', 'Buck': 'stale-window-close',
                    'Cheryl': 'stale-window-close', 'Marley': 'stale-window-close'}
        for language in ('EN', 'IT'):
            report = self.audit(language)
            with self.subTest(language=language):
                self.assertEqual({name: row['status']
                                  for name, row in report['paths'].items()}, expected)
                self.assertEqual({name: row['script_id']
                                  for name, row in report['paths'].items()},
                                 {'Mira': 7, 'Buck': 9, 'Cheryl': 14, 'Marley': 17})
                self.assertTrue(all(row['trigger_reaches_message']
                                    for row in report['paths'].values()))
                self.assertEqual(report['mutants'], {
                    'Mira_close_moved_after_unload': 'stale-window-close',
                    'Buck_close_moved_before_unload': 'healthy',
                })
                self.assertEqual(report['component_status'], 'demonstrated')
                self.assertEqual(report['runtime_blackout'], 'not-run')

    def test_repair_changes_only_the_closes_export_and_appended_height_guard(self):
        for language in ('EN', 'IT'):
            _data, before, commands = self.material(language)
            after = S.repair_member(before, commands)
            with self.subTest(language=language):
                self.assertEqual(after, self.expected_repair(before))
                self.assertEqual(len(after), len(before) + 23)
                self.assertEqual(hashlib.sha256(after).hexdigest(),
                                 'bcc71c8ce50440b37fc253f04897ef30e765508162d999c057a7bbe6b7ad01b2')

    def test_repaired_member_roundtrips_and_all_four_partner_paths_are_healthy(self):
        for language in ('EN', 'IT'):
            data, before, commands = self.material(language)
            after = S.repair_member(before, commands)
            parsed = gifts_scripts.decode(after, commands, S.SCRIPT_MEMBER)
            event = bytes(ndspy.narc.NARC(
                ndspy.rom.NintendoDSRom(data).getFileByName(S.EVENT_ARCHIVE)
            ).files[S.EVENT_MEMBER])
            paths = S._decoded_paths(parsed, S._event_triggers(event))
            with self.subTest(language=language):
                self.assertFalse(parsed.errori)
                self.assertTrue(parsed.riassembla()[0])
                self.assertEqual({name: row['status'] for name, row in paths.items()},
                                 {'Mira': 'healthy', 'Buck': 'healthy',
                                  'Cheryl': 'healthy', 'Marley': 'healthy'})
                S.verify_repair(before, after, commands)

    def test_repaired_mira_entry_rejects_the_lower_level_before_side_effects(self):
        """SG-02: entry 7 must gate the bridge battle on player height."""
        for language in ('EN', 'IT'):
            _data, before, commands = self.material(language)
            after = S.repair_member(before, commands)
            parsed = gifts_scripts.decode(after, commands, S.SCRIPT_MEMBER)
            start = parsed.entry[6]
            rows = []
            cursor = start
            while cursor in parsed.istruzioni and len(rows) < 4:
                row = parsed.istruzioni[cursor]
                rows.append(row)
                cursor = row.fine
            with self.subTest(language=language):
                self.assertEqual([row.nome for row in rows], [
                    'GetPlayerXYZ', 'CompareVarToValue', 'GoToIf', 'End'])
                self.assertEqual(rows[0].args, [0x8004, 0x8005, 0x8006])
                self.assertEqual(rows[1].args, [0x8005, 0])
                self.assertEqual(rows[2].args[0], 1)  # equality
                self.assertEqual(rows[2].rami[0][1], 447)
                self.assertEqual(parsed.istruzioni[447].nome,
                                 'StopBGM')

    def test_repair_refuses_reapplication_and_the_reader_rejects_foreign_bytes(self):
        _data, before, commands = self.material('EN')
        after = S.repair_member(before, commands)
        with self.assertRaisesRegex(ValueError, 'preimage'):
            S.repair_member(after, commands)
        foreign = bytearray(after)
        foreign[-1] ^= 1
        with self.assertRaisesRegex(ValueError, 'postimage|outside'):
            S.verify_repair(before, bytes(foreign), commands)

    def test_archive_producer_changes_only_script_member_260(self):
        from sgp131 import archives, safari_archives
        for language in ('EN', 'IT'):
            data, before, _commands = self.material(language)
            delta = safari_archives.derive_safari_scripts(data, language)
            with self.subTest(language=language):
                self.assertEqual((delta.archive, delta.producers()),
                                 (S.SCRIPT_ARCHIVE, [safari_archives.SCRIPTS]))
                self.assertEqual([member.index for member in delta.members],
                                 [S.SCRIPT_MEMBER])
                member = delta.members[0]
                self.assertEqual(member.before_sha256, hashlib.sha256(before).hexdigest())
                safari_archives.check_scripts(
                    member.index, before, member.after, language)
                changed = bytearray(member.after)
                changed[-1] ^= 1
                with self.assertRaises(ValueError):
                    safari_archives.check_scripts(
                        member.index, before, bytes(changed), language)
                old = archives.members(ndspy.rom.NintendoDSRom(data).getFileByName(
                    S.SCRIPT_ARCHIVE))
                self.assertEqual(hashlib.sha256(old[S.SCRIPT_MEMBER]).hexdigest(),
                                 S.SCRIPT_SHA256)

if __name__ == '__main__':
    unittest.main()
