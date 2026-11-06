import os
import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from . import admission


class AdmissionTests(unittest.TestCase):
    def test_contract_rejects_size_before_read(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'oversized.nds'
            with path.open('wb') as handle:
                handle.truncate(513 * 1024 * 1024)
            with mock.patch('sgp13.admission.os.read', side_effect=AssertionError('body read')):
                with self.assertRaisesRegex(ValueError, 'exact supported'):
                    admission.read_contract(path, {'0' * 64: ('EN', 16)}, 'ROM')

    def test_valid_contract_and_wrong_hash_control(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'input.bin'
            path.write_bytes(b'bounded fixture')
            import hashlib
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            data, identity, observed = admission.read_contract(
                path, {digest: ('EN', path.stat().st_size)}, 'ROM')
            self.assertEqual((data, identity, observed), (b'bounded fixture', 'EN', digest))
            with self.assertRaisesRegex(ValueError, 'exact supported'):
                admission.read_contract(path, {'0' * 64: ('EN', path.stat().st_size)}, 'ROM')

    def test_symlink_and_hardlink_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            original = root / 'original'
            original.write_bytes(b'x')
            hardlink = root / 'hardlink'
            os.link(original, hardlink)
            symlink = root / 'symlink'
            symlink.symlink_to(original)
            with self.assertRaises((OSError, ValueError)):
                admission.read_bounded(symlink, 10, 'input')
            with self.assertRaisesRegex(ValueError, 'non-aliased'):
                admission.read_bounded(hardlink, 10, 'input')

    def test_fifo_is_rejected_without_waiting_for_a_writer(self):
        with tempfile.TemporaryDirectory() as temp:
            fifo = Path(temp) / 'evidence.json'
            os.mkfifo(fifo, 0o600)
            with self.assertRaisesRegex(ValueError, 'regular'):
                admission.read_bounded(fifo, 1024, 'evidence')

    def test_exact_size_and_digest_are_bound_to_same_bytes(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'metadata.json'
            path.write_bytes(b'{}')
            import hashlib
            digest = hashlib.sha256(b'{}').hexdigest()
            data, observed = admission.read_bounded(
                path, 1024, 'metadata', exact_size=2, expected_sha256=digest)
            self.assertEqual((data, observed), (b'{}', digest))

    def test_path_swap_after_open_cannot_replace_consumed_bytes(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            path = root / 'input'
            replacement = root / 'replacement'
            path.write_bytes(b'authenticated')
            replacement.write_bytes(b'hostile-bytes')
            import hashlib
            digest = hashlib.sha256(b'authenticated').hexdigest()
            real_fstat = os.fstat
            calls = 0

            def stat_then_swap(fd):
                nonlocal calls
                info = real_fstat(fd)
                calls += 1
                if calls == 1:
                    os.replace(replacement, path)
                return info

            with mock.patch('sgp13.admission.os.fstat', side_effect=stat_then_swap):
                data, observed = admission.read_bounded(
                    path, 1024, 'input', expected_sha256=digest)
            self.assertEqual((data, observed), (b'authenticated', digest))
            self.assertEqual(path.read_bytes(), b'hostile-bytes')

    def test_growth_during_read_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'input'
            path.write_bytes(b'x')
            real_read = os.read
            calls = 0

            def read_then_grow(fd, count):
                nonlocal calls
                result = real_read(fd, count)
                calls += 1
                if calls == 1:
                    with path.open('ab') as handle:
                        handle.write(b'y')
                return result

            with mock.patch('sgp13.admission.os.read', side_effect=read_then_grow):
                with self.assertRaisesRegex(ValueError, 'grew|changed'):
                    admission.read_bounded(path, 1024, 'input')

    def test_source_snapshot_rejects_path_swap_symlink_and_oversized_file(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            source = root / 'source.py'
            replacement = root / 'replacement.py'
            source.write_bytes(b'authenticated source')
            replacement.write_bytes(b'hostile source')
            real_fstat = os.fstat
            calls = 0
            def stat_then_swap(fd):
                nonlocal calls
                info = real_fstat(fd)
                calls += 1
                if calls == 1:
                    os.replace(replacement, source)
                return info
            with mock.patch('sgp13.admission.os.fstat', side_effect=stat_then_swap):
                with self.assertRaisesRegex(ValueError, 'path/inode'):
                    admission.source_snapshot(root, [source])

            target = root / 'target.py'
            target.write_bytes(b'x')
            link = root / 'link.py'
            link.symlink_to(target)
            with self.assertRaises((OSError, ValueError)):
                admission.source_snapshot(root, [link])

            oversized = root / 'oversized.py'
            with oversized.open('wb') as handle:
                handle.truncate(admission.MAX_SOURCE_BYTES + 1)
            with self.assertRaisesRegex(ValueError, 'per-file'):
                admission.source_snapshot(root, [oversized])

            outside = root.parent / (root.name + '-outside.py')
            outside.write_bytes(b'outside')
            self.addCleanup(outside.unlink, missing_ok=True)
            lexical_escape = root / '..' / outside.name
            with self.assertRaisesRegex(ValueError, 'outside root'):
                admission.source_snapshot(root, [lexical_escape])

            fifo = root / 'blocked.py'
            os.mkfifo(fifo, 0o600)
            with self.assertRaisesRegex(ValueError, 'regular'):
                admission.source_snapshot(root, [fifo])

    def test_two_source_snapshots_miss_restored_intermediate_bytes(self):
        """Reproduce the build-wide check/use/check race without a ROM.

        ``build.build`` records one source snapshot before the stages and
        compares it with another after them.  The stages themselves reopen
        source pathnames.  A writer can therefore move the admitted inode
        aside, expose different bytes for one consumer, then restore the
        original inode before the second snapshot.
        """
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            source = root / 'stage.json'
            saved = root / 'admitted.json'
            source.write_bytes(b'{"value":"admitted"}')

            before = admission.source_snapshot(root, [source])
            source.rename(saved)
            source.write_bytes(b'{"value":"intermediate"}')
            consumed = source.read_bytes()
            source.unlink()
            saved.rename(source)
            after = admission.source_snapshot(root, [source])

            self.assertEqual(before, after)
            self.assertEqual(consumed, b'{"value":"intermediate"}')
            self.assertEqual(source.read_bytes(), b'{"value":"admitted"}')

    def test_two_source_snapshots_miss_a_restored_python_import(self):
        """Exercise the race through a real pathname-based Python loader.

        The production builder imports repository modules and those modules
        subsequently open more repository paths.  Hashing before and after
        cannot bind either operation when a same-account writer restores the
        admitted inode before the second snapshot.
        """
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            source = root / 'stage.py'
            saved = root / 'admitted.py'
            source.write_text("VALUE = 'admitted'\n")

            before = admission.source_snapshot(root, [source])
            source.rename(saved)
            source.write_text("VALUE = 'intermediate'\n")
            spec = importlib.util.spec_from_file_location(
                'sgp13_toctou_fixture', source)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            source.unlink()
            saved.rename(source)
            after = admission.source_snapshot(root, [source])

            self.assertEqual(module.VALUE, 'intermediate')
            self.assertEqual(before, after)
            self.assertEqual(source.read_text(), "VALUE = 'admitted'\n")

    def test_private_copy_modes_do_not_restrict_a_same_uid_writer(self):
        """Reject mode 0700/0400 as a proposed same-account boundary.

        File modes constrain other users.  A process with the owner's UID can
        restore its own write bit and alter the bytes, so a private copy is an
        availability/convenience measure rather than source authenticity.
        """
        with tempfile.TemporaryDirectory() as temp:
            private = Path(temp) / 'private'
            private.mkdir(mode=0o700)
            source = private / 'stage.py'
            source.write_text("VALUE = 'admitted'\n")
            source.chmod(0o400)
            script = (
                'import os,sys; p=sys.argv[1]; '
                'os.chmod(p, 0o600); '
                'open(p, "wb").write(b"VALUE = \'intermediate\'\\n")'
            )
            completed = subprocess.run(
                [sys.executable, '-I', '-c', script, str(source)],
                check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.assertEqual(completed.returncode, 0, completed.stderr.decode())
            self.assertEqual(source.read_text(), "VALUE = 'intermediate'\n")

    def test_source_snapshot_detects_unrestored_intermediate_bytes(self):
        """Negative control: a mutation left visible changes the digest."""
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            source = root / 'stage.json'
            source.write_bytes(b'{"value":"admitted"}')
            before = admission.source_snapshot(root, [source])
            source.write_bytes(b'{"value":"changed"}')
            after = admission.source_snapshot(root, [source])
            self.assertNotEqual(before, after)


if __name__ == '__main__':
    unittest.main()
