"""Class B: actual guarded Mew script members and pending-movement lifecycle.

The lifecycle check is symbolic, using actual decoded script commands. Native
crash/recovery evidence comes from separate input-driven emulator campaigns.
No extracted bytes or private game fixture is stored in the repository.
"""
import hashlib
import os
from pathlib import Path
import struct
import unittest

from sgp13 import mew

BASE_DIR = os.environ.get('SGP13_BASE_DIR')
PRET = os.environ.get('SGP_PRET_SOURCE')


@unittest.skipUnless(BASE_DIR and PRET, 'private 1.2.5 EN/IT bases and reference metadata not supplied')
class MewRom(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.commands, cls.metadata_hash = mew.load_commands(Path(PRET) / 'tools/py_scripts/scrcmd.json')

    def member(self, language):
        import ndspy.rom
        import ndspy.narc
        data = (Path(BASE_DIR) / f'sgp-1.2.5-{language}.nds').read_bytes()
        rom = ndspy.rom.NintendoDSRom(data)
        archive = ndspy.narc.NARC(rom.getFileByName('a/0/1/2'))
        return data, rom, archive

    def completed_before_end(self, raw, script):
        # A pending incoming movement must never outlive its script task.
        # The three actual event paths are linear, without branch simulation.
        member = mew.decoder().Membro(mew.MEMBER, raw, self.commands).cammina()
        self.assertFalse(member.errori)
        cursor = member.entry[script - 1]
        pending = 0
        for _ in range(100):
            ins = member.istruzioni[cursor]
            self.assertFalse(ins.rami and ins.nome != 'ApplyMovement', 'unexpected event control flow')
            if ins.nome == 'ApplyMovement':
                pending += 1
            elif ins.nome == 'WaitMovement':
                pending = 0
            elif ins.nome == 'End':
                return pending == 0
            cursor = ins.fine
        self.fail('event did not end')

    def test_real_members_finish_each_incoming_movement_and_each_wait_mutant_fails(self):
        for language in ('EN', 'IT'):
            _, _, archive = self.member(language)
            original = bytes(archive.files[mew.MEMBER])
            patched = mew.patch_member(original, language, self.commands)
            for index, site in enumerate(mew.SITES):
                with self.subTest(language=language, script=index + 3):
                    self.assertFalse(self.completed_before_end(original, index + 3))
                    self.assertTrue(self.completed_before_end(patched, index + 3))
                    mutant = bytearray(patched)
                    # Replace only this added WaitMovement with Nop; preserve
                    # all relative offsets and every other instruction.
                    struct.pack_into('<H', mutant, site + 2 * index, 0)
                    self.assertFalse(self.completed_before_end(bytes(mutant), index + 3))
                    for other in set((3, 4, 5)) - {index + 3}:
                        self.assertTrue(self.completed_before_end(bytes(mutant), other))

    def test_complete_member_guard_rejects_foreign_and_second_application(self):
        for language in ('EN', 'IT'):
            _, _, archive = self.member(language)
            original = bytes(archive.files[mew.MEMBER])
            patched = mew.patch_member(original, language, self.commands)
            changed = bytearray(original)
            changed[-1] ^= 1
            for raw in (patched, bytes(changed)):
                with self.subTest(language=language, length=len(raw)):
                    with self.assertRaisesRegex(ValueError, 'preimage'):
                        mew.patch_member(raw, language, self.commands)

    def test_actual_rom_readback_changes_only_script115(self):
        import ndspy.rom
        import ndspy.narc
        for language in ('EN', 'IT'):
            data, original_rom, original_archive = self.member(language)
            result, report = mew.apply(data, language, self.commands)
            updated = ndspy.rom.NintendoDSRom(result)
            file_id = original_rom.filenames.idOf('a/0/1/2')
            self.assertEqual([i for i, (a, b) in enumerate(zip(original_rom.files, updated.files)) if a != b], [file_id])
            archive = ndspy.narc.NARC(updated.files[file_id])
            self.assertEqual([i for i, (a, b) in enumerate(zip(original_archive.files, archive.files)) if a != b], [115])
            self.assertEqual((updated.arm9, updated.arm7, updated.iconBanner),
                             (original_rom.arm9, original_rom.arm7, original_rom.iconBanner))
            self.assertEqual(report['output_member_bytes'], report['input_member_bytes'] + 6)
            self.assertEqual(report['output_member_sha256'], hashlib.sha256(archive.files[115]).hexdigest())
            with self.assertRaisesRegex(ValueError, 'preimage'):
                mew.apply(result, language, self.commands)


if __name__ == '__main__':
    unittest.main()
