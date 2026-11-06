import contextlib
import io
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from . import costruisci
from .rom import Rifiuto


class SecurePublicationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='sgp12-publish-')
        self.addCleanup(self.temp.cleanup)
        self.top = Path(self.temp.name)

    def target(self, name='output.nds'):
        directory = self.top / 'private'
        directory.mkdir(mode=0o700, exist_ok=True)
        directory.chmod(0o700)
        return directory / name

    def test_success_is_private_regular_and_single_link_under_umask_022(self):
        path = self.target()
        previous = os.umask(0o022)
        try:
            target = costruisci._PrivateTarget(path)
            try:
                target.publish(b'candidate')
            finally:
                target.close()
        finally:
            os.umask(previous)
        info = path.stat()
        self.assertEqual(path.read_bytes(), b'candidate')
        self.assertEqual(info.st_mode & 0o777, 0o600)
        self.assertEqual(info.st_nlink, 1)
        self.assertFalse(any(path.parent.glob('.output.nds.*')))

    def test_existing_regular_symlinks_and_hardlink_are_never_changed(self):
        victim = self.top / 'victim'
        victim.write_bytes(b'preserve')
        cases = {
            'regular': lambda path: path.write_bytes(b'existing'),
            'live-symlink': lambda path: path.symlink_to(victim),
            'dangling-symlink': lambda path: path.symlink_to(self.top / 'absent'),
            'hardlink': lambda path: os.link(victim, path),
        }
        for label, prepare in cases.items():
            with self.subTest(label=label):
                path = self.target(label + '.nds')
                prepare(path)
                before = victim.read_bytes()
                with self.assertRaisesRegex(Rifiuto, 'presente'):
                    costruisci._PrivateTarget(path)
                self.assertEqual(victim.read_bytes(), before)
                self.assertFalse((self.top / 'absent').exists())

    def test_parent_swap_cannot_redirect_publication(self):
        parent = self.top / 'private'
        parent.mkdir(mode=0o700)
        parent.chmod(0o700)
        target = costruisci._PrivateTarget(parent / 'output.nds')
        held = self.top / 'held'
        outside = self.top / 'outside'
        outside.mkdir()
        parent.rename(held)
        parent.symlink_to(outside, target_is_directory=True)
        try:
            target.publish(b'candidate')
        finally:
            target.close()
        self.assertEqual((held / 'output.nds').read_bytes(), b'candidate')
        self.assertFalse((outside / 'output.nds').exists())

    def test_log_directory_must_be_private_and_all_names_are_preflighted(self):
        log_dir = self.top / 'logs'
        log_dir.mkdir(mode=0o700)
        log_dir.chmod(0o755)
        with self.assertRaisesRegex(Rifiuto, 'privata'):
            costruisci._PrivateDirectory(log_dir, require_private=True)
        log_dir.chmod(0o700)
        (log_dir / '01-riserva.json').write_text('preserve')
        with patch('sgp12.costruisci.prepara_base') as prepare:
            with contextlib.redirect_stderr(io.StringIO()):
                result = costruisci.main([
                    '--base', str(self.top / 'base.nds'),
                    '--uscita', str(self.target('result.nds')),
                    '--log-dir', str(log_dir),
                ])
        self.assertEqual(result, 2)
        prepare.assert_not_called()
        self.assertEqual((log_dir / '01-riserva.json').read_text(), 'preserve')

    def test_input_output_alias_and_output_report_collision_stop_before_stage_zero(self):
        base = self.target('base.nds')
        base.write_bytes(b'original')
        with patch('sgp12.costruisci.prepara_base') as prepare:
            with contextlib.redirect_stderr(io.StringIO()):
                result = costruisci.main(['--base', str(base), '--uscita', str(base)])
        self.assertEqual(result, 2)
        prepare.assert_not_called()
        self.assertEqual(base.read_bytes(), b'original')

        output = self.target('collision.nds')
        with patch('sgp12.costruisci.prepara_base') as prepare:
            with contextlib.redirect_stderr(io.StringIO()):
                result = costruisci.main([
                    '--base', str(base), '--uscita', str(output), '--json', str(output),
                ])
        self.assertEqual(result, 2)
        prepare.assert_not_called()
        self.assertFalse(output.exists())

    def test_casefold_collision_stops_before_stage_zero(self):
        base = self.target('base.nds')
        base.write_bytes(b'original')
        output = self.target('Result.nds')
        report = self.target('result.nds')
        with patch('sgp12.costruisci.prepara_base') as prepare:
            with contextlib.redirect_stderr(io.StringIO()):
                result = costruisci.main([
                    '--base', str(base), '--uscita', str(output), '--json', str(report),
                ])
        self.assertEqual(result, 2)
        prepare.assert_not_called()
        self.assertFalse(output.exists())
        self.assertFalse(report.exists())

    def test_rejected_target_does_not_leak_directory_descriptors(self):
        path = self.target('existing.nds')
        path.write_bytes(b'preserve')
        before = len(os.listdir('/dev/fd'))
        for _ in range(100):
            with self.assertRaises(Rifiuto):
                costruisci._PrivateTarget(path)
        self.assertEqual(len(os.listdir('/dev/fd')), before)
        self.assertEqual(path.read_bytes(), b'preserve')

    def test_failed_partial_write_removes_owned_temporary(self):
        path = self.target('partial.nds')
        directory = costruisci._PrivateDirectory(path.parent)
        real_write = os.write
        calls = 0
        def interrupted(fd, data):
            nonlocal calls
            calls += 1
            if calls == 1:
                return real_write(fd, data[:3])
            raise OSError('simulated write failure')
        try:
            with patch('sgp12.costruisci.os.write', side_effect=interrupted):
                with self.assertRaisesRegex(OSError, 'simulated'):
                    directory.publish(path.name, b'candidate')
        finally:
            directory.close()
        self.assertFalse(path.exists())
        self.assertFalse(any(path.parent.glob('.partial.nds.*')))


if __name__ == '__main__':
    unittest.main()
