import hashlib
from contextlib import contextmanager
import fcntl
import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch
from . import baseline, workbench
from .test_baseline import EN, IT, PINS
from .test_evidence import report_for


def accept_checked(config, path):
    path = Path(path)
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return workbench.accept(config, path, digest)


class WorkbenchTests(unittest.TestCase):
    def setUp(self):
        previous_umask = os.umask(0o077)
        self.addCleanup(os.umask, previous_umask)
        self.temp = tempfile.TemporaryDirectory(prefix='sgp131-test-')
        self.addCleanup(self.temp.cleanup)
        self.top = Path(self.temp.name).resolve()
        self.en = self.top / 'original-en.nds'
        self.it = self.top / 'original-it.nds'
        self.en.write_bytes(EN)
        self.it.write_bytes(IT)
        self.root = self.top / 'bench'
        self.config = self.root / 'config.json'
        self.pins = patch.dict(baseline.INPUT_HASHES, PINS, clear=True)
        self.pins.start()
        self.addCleanup(self.pins.stop)
        self.pin_sizes = patch.dict(
            baseline.INPUT_SIZES,
            {hashlib.sha256(EN).hexdigest(): len(EN),
             hashlib.sha256(IT).hexdigest(): len(IT)}, clear=True)
        self.pin_sizes.start()
        self.addCleanup(self.pin_sizes.stop)
        self.sources = patch('sgp131.build.source_snapshot', return_value={'fixture.py': 'a' * 64})
        self.sources.start()
        self.addCleanup(self.sources.stop)
        self.disk = patch('sgp131.workbench.shutil.disk_usage', return_value=shutil._ntuple_diskusage(10**12, 0, 10**12), create=True)
        # Start after initialization: the stub module need not import shutil yet.

    def init(self):
        result = workbench.initialize(self.config, {'EN': self.en, 'IT': self.it}, self.root)
        self.assertIsInstance(result, dict, 'initialize must create guarded private configuration')
        return result

    def pending(self):
        self.init()
        self.disk.start()
        self.addCleanup(self.disk.stop)
        result = workbench.build_candidate(self.config, 'EN', 'baseline')
        self.assertIsInstance(result, dict)
        self.assertEqual(Path(result['path']).name, 'pending.nds')
        return result

    def evidence(self, digest):
        path = self.top / 'evidence.json'
        path.write_text(json.dumps(report_for(digest)))
        return path

    def test_rejects_foreign_base_before_output(self):
        self.en.write_bytes(b'foreign')
        with self.assertRaisesRegex(ValueError, 'exact supported'):
            workbench.initialize(self.config, {'EN': self.en, 'IT': self.it}, self.root)
        self.assertFalse(self.root.exists())

    def test_private_modes_ignore_permissive_umask(self):
        previous = os.umask(0o022)
        try:
            self.pending()
        finally:
            os.umask(previous)
        for path in self.root.rglob('*'):
            with self.subTest(path=path.relative_to(self.root)):
                expected = 0o700 if path.is_dir() else 0o600
                self.assertEqual(path.stat().st_mode & 0o777, expected)

    def test_relaxed_config_or_root_permissions_are_refused(self):
        self.init()
        self.config.chmod(0o644)
        with self.assertRaisesRegex(ValueError, 'permissions'):
            workbench.inspect(self.config)
        self.config.chmod(0o600)
        self.root.chmod(0o755)
        with self.assertRaisesRegex(ValueError, 'permissions'):
            workbench.inspect(self.config)

    def test_rejects_input_output_alias_and_symlink(self):
        with self.assertRaisesRegex(ValueError, 'input|alias'):
            workbench.initialize(self.config, {'EN': self.en, 'IT': self.it}, self.top)
        self.root.symlink_to(self.top, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'symlink|alias'):
            workbench.initialize(self.config, {'EN': self.en, 'IT': self.it}, self.root)
        self.assertEqual(self.en.read_bytes(), EN)

    def test_pending_is_not_accepted_and_second_pending_refused(self):
        result = self.pending()
        self.assertEqual(Path(result['path']).read_bytes(), EN)
        self.assertFalse((self.root / 'EN/candidate.nds').exists())
        self.assertFalse((self.root / 'EN/fallback.nds').exists())
        self.assertEqual(self.en.read_bytes(), EN)
        self.assertNotEqual(os.stat(result['path']).st_ino, self.en.stat().st_ino)
        with self.assertRaisesRegex(ValueError, 'pending'):
            workbench.build_candidate(self.config, 'EN', 'baseline')

    def test_one_writer_and_busy_candidate_refuse(self):
        result = self.pending()
        accept_checked(self.config, self.evidence(result['output_sha256']))
        with workbench._locked(self.config):
            with self.assertRaisesRegex(ValueError, 'writer|lock'):
                workbench.build_candidate(self.config, 'EN', 'baseline')
        lease = workbench.claim_consumer(self.config, 'EN', 'candidate', os.getpid())
        workbench.build_candidate(self.config, 'EN', 'baseline')
        with self.assertRaisesRegex(ValueError, 'busy|consumer'):
            accept_checked(self.config, self.evidence(result['output_sha256']))
        workbench.release_consumer(self.config, 'EN', lease['session'])
        accept_checked(self.config, self.evidence(result['output_sha256']))

    def test_disk_budget_preserves_ten_gib(self):
        self.init()
        # Baseline output has exactly input length, and zero scratch. Journal
        # metadata is additionally budgeted. Even ignoring metadata, len(EN)-1
        # available above the reserve cannot hold the pending bytes.
        free = workbench.MIN_FREE + len(EN) - 1
        with patch('sgp131.workbench.shutil.disk_usage', return_value=shutil._ntuple_diskusage(free, 0, free)):
            with self.assertRaisesRegex(ValueError, 'space|budget'):
                workbench.build_candidate(self.config, 'EN', 'baseline')
        self.assertFalse((self.root / 'EN/pending.nds').exists())
        self.assertFalse((self.root / 'journal.json').exists())

    def test_source_change_aborts_publication(self):
        self.init()
        with patch('sgp131.build.source_snapshot', side_effect=[{'a': '1'}, {'a': '1'}, {'a': '2'}, {'a': '2'}]):
            with self.assertRaisesRegex(ValueError, 'source'):
                workbench.build_candidate(self.config, 'EN', 'baseline')
        self.assertFalse((self.root / 'EN/pending.nds').exists())
        self.assertFalse((self.root / 'journal.json').exists())
        self.assertEqual(self.en.read_bytes(), EN)

    def test_failure_preserves_last_good_and_foreign_files(self):
        result = self.pending()
        accept_checked(self.config, self.evidence(result['output_sha256']))
        sentinel = self.root / 'EN/unique-evidence.txt'
        sentinel.write_text('keep')
        with patch('sgp131.build.compose', side_effect=ValueError('injected installer failure')):
            with self.assertRaisesRegex(ValueError, 'injected'):
                workbench.build_candidate(self.config, 'EN', 'baseline')
        self.assertEqual((self.root / 'EN/candidate.nds').read_bytes(), EN)
        self.assertEqual(sentinel.read_text(), 'keep')
        self.assertFalse((self.root / 'EN/pending.nds').exists())
        self.assertFalse(any(self.root.glob('.scratch-*')))

    def test_recovery_matches_rom_and_receipt(self):
        result = self.pending()
        evidence = self.evidence(result['output_sha256'])
        real_replace = os.replace
        count = 0

        def interrupt(src, dst, *args, **kwargs):
            nonlocal count
            if Path(dst).name == 'candidate.json':
                count += 1
                raise OSError('simulated power loss')
            return real_replace(src, dst, *args, **kwargs)

        with patch('sgp131.workbench.os.replace', side_effect=interrupt):
            with self.assertRaisesRegex(OSError, 'power loss'):
                accept_checked(self.config, evidence)
        self.assertEqual(count, 1)
        with self.assertRaisesRegex(ValueError, 'recover|journal'):
            workbench.inspect(self.config)
        recovered = workbench.recover(self.config)
        self.assertIsInstance(recovered, dict)
        receipt = json.loads((self.root / 'EN/candidate.json').read_text())
        self.assertEqual(receipt['output_sha256'], hashlib.sha256((self.root / 'EN/candidate.nds').read_bytes()).hexdigest())
        self.assertEqual(receipt['status'], 'accepted')
        self.assertFalse((self.root / 'journal.json').exists())
        self.assertEqual(self.en.read_bytes(), EN)

    def test_accept_requires_exact_evidence_hash(self):
        self.pending()
        with self.assertRaisesRegex(ValueError, 'hash'):
            accept_checked(self.config, self.evidence('0' * 64))
        self.assertFalse((self.root / 'EN/candidate.nds').exists())
        self.assertTrue((self.root / 'EN/pending.nds').exists())

    def test_acceptance_json_is_bounded_nonaliased_and_duplicate_safe(self):
        result = self.pending()
        valid = self.evidence(result['output_sha256'])
        with self.assertRaisesRegex(ValueError, 'reviewed SHA-256'):
            workbench.accept(self.config, valid, '0' * 64)
        link = self.top / 'evidence-link.json'
        link.symlink_to(valid)
        with self.assertRaises((OSError, ValueError)):
            accept_checked(self.config, link)
        hard = self.top / 'evidence-hard.json'
        os.link(valid, hard)
        with self.assertRaisesRegex(ValueError, 'non-aliased'):
            accept_checked(self.config, hard)
        hard.unlink()

        oversized = self.top / 'evidence-oversized.json'
        with oversized.open('wb') as handle:
            handle.truncate(workbench.ACCEPTANCE_LIMIT + 1)
        with self.assertRaisesRegex(ValueError, 'limit'):
            accept_checked(self.config, oversized)

        duplicate = self.top / 'evidence-duplicate.json'
        duplicate.write_text('{"schema":1,"schema":1}')
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            accept_checked(self.config, duplicate)
        self.assertFalse((self.root / 'EN/candidate.nds').exists())

    def test_failed_candidate_never_becomes_fallback(self):
        result = self.pending()
        evidence = self.evidence(result['output_sha256'])
        accept_checked(self.config, evidence)
        workbench.build_candidate(self.config, 'EN', 'baseline')
        bad = report_for(result['output_sha256'])
        bad['cases'][0]['status'] = 'fail'
        evidence.write_text(json.dumps(bad))
        with self.assertRaises(ValueError):
            accept_checked(self.config, evidence)
        self.assertFalse((self.root / 'EN/fallback.nds').exists())
        evidence.write_text(json.dumps(report_for(result['output_sha256'])))
        accept_checked(self.config, evidence)
        self.assertEqual((self.root / 'EN/fallback.nds').read_bytes(), EN)
        self.assertEqual(json.loads((self.root / 'EN/fallback.json').read_text())['status'], 'accepted')

    def test_tampered_pending_input_and_symlink_slots_are_refused(self):
        result = self.pending()
        pending = Path(result['path'])
        pending.write_bytes(b'corrupt')
        with self.assertRaisesRegex(ValueError, 'hash|pair'):
            accept_checked(self.config, self.evidence(result['output_sha256']))
        pending.unlink()
        pending.symlink_to(self.en)
        with self.assertRaisesRegex(ValueError, 'symlink'):
            workbench.recover(self.config)
        self.assertEqual(self.en.read_bytes(), EN)

    def test_config_hash_does_not_admit_arbitrary_input(self):
        self.init()
        self.en.write_bytes(b'foreign')
        config = json.loads(self.config.read_text())
        config['bases']['EN']['sha256'] = hashlib.sha256(b'foreign').hexdigest()
        config['bases']['EN']['bytes'] = len(b'foreign')
        self.config.write_text(json.dumps(config))
        with self.assertRaisesRegex(ValueError, 'exact supported'):
            workbench.build_candidate(self.config, 'EN', 'baseline')

    def test_stale_pid_metadata_is_reclaimed_but_an_actual_flock_blocks(self):
        self.init()
        lock = self.root / '.lock'
        lock.write_bytes(json.dumps({'pid': os.getpid(), 'session': 'stale'}).encode())
        self.assertIsInstance(workbench.inspect(self.config), dict)
        self.assertEqual(lock.read_bytes(), b'')
        fd = os.open(lock, os.O_RDWR)
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            with self.assertRaisesRegex(ValueError, 'writer holds'):
                workbench.inspect(self.config)
        finally:
            fcntl.flock(fd, fcntl.LOCK_UN)
            os.close(fd)

    def test_root_identity_swap_is_rejected_after_load_and_inside_lock(self):
        self.init()
        held = self.top / 'held-bench'
        real_load = workbench._load
        def swap_after_load(path):
            config = real_load(path)
            self.root.rename(held)
            self.root.mkdir(mode=0o700)
            return config
        with patch('sgp131.workbench._load', side_effect=swap_after_load):
            with self.assertRaisesRegex(ValueError, 'identity'):
                workbench.inspect(self.config)
        self.root.rmdir()
        held.rename(self.root)

        real_state = workbench._state
        swapped = False
        def swap_inside_lock(config, *args, **kwargs):
            nonlocal swapped
            if not swapped:
                swapped = True
                self.root.rename(held)
                self.root.mkdir(mode=0o700)
            return real_state(config, *args, **kwargs)
        with patch('sgp131.workbench._state', side_effect=swap_inside_lock):
            with self.assertRaisesRegex(ValueError, 'identity'):
                workbench.inspect(self.config)
        self.root.rmdir()
        held.rename(self.root)

    def test_final_publication_is_pinned_when_root_path_is_swapped(self):
        self.init()
        held = self.top / 'held-final-root'
        replacement = self.top / 'replacement-root'
        real_guard = workbench._guard_paths
        swapped = False
        def swap_after_final_guard(config):
            nonlocal swapped
            real_guard(config)
            if not swapped and (self.root / 'journal.json').exists():
                swapped = True
                shutil.copytree(self.root, replacement, copy_function=shutil.copy2)
                self.root.rename(held)
                replacement.rename(self.root)
        with patch('sgp131.workbench._guard_paths', side_effect=swap_after_final_guard):
            with self.assertRaisesRegex(ValueError, 'identity'):
                workbench.build_candidate(self.config, 'EN', 'baseline')
        self.assertTrue(swapped)
        self.assertFalse((self.root / 'EN/pending.nds').exists())
        self.assertFalse((self.root / 'EN/pending.json').exists())
        self.assertTrue((held / 'EN/pending.nds').exists())
        shutil.rmtree(self.root)
        held.rename(self.root)

    def test_journal_preparation_cannot_overwrite_swapped_root(self):
        self.init()
        held = self.top / 'held-staging-root'
        replacement = self.top / 'replacement-staging-root'
        sentinel = b'{"foreign":"preserve"}\n'
        real_guard = workbench._guard_paths
        swapped = False
        def swap_after_staging_guard(config):
            nonlocal swapped
            real_guard(config)
            if not swapped and any(self.root.glob('.txn-*')):
                swapped = True
                shutil.copytree(self.root, replacement, copy_function=shutil.copy2)
                (replacement / 'journal.json').write_bytes(sentinel)
                (replacement / 'journal.json').chmod(0o600)
                self.root.rename(held)
                replacement.rename(self.root)
        with patch('sgp131.workbench._guard_paths', side_effect=swap_after_staging_guard):
            with self.assertRaisesRegex(ValueError, 'identity'):
                workbench.build_candidate(self.config, 'EN', 'baseline')
        self.assertTrue(swapped)
        self.assertEqual((self.root / 'journal.json').read_bytes(), sentinel)
        self.assertFalse((self.root / 'EN/pending.nds').exists())
        self.assertTrue((held / 'journal.json').exists())
        shutil.rmtree(self.root)
        held.rename(self.root)

    def test_recovery_orphan_cleanup_stays_on_pinned_root(self):
        config = self.init()
        orphan_name = '.txn-' + 'a' * 32
        orphan = self.root / orphan_name
        orphan.mkdir(mode=0o700)
        (orphan / 'owner.json').write_text(json.dumps(
            {'schema': 1, 'id': config['id'], 'directory': orphan_name}))
        (orphan / '0').write_bytes(b'owned snapshot')
        held = self.top / 'held-orphan-root'
        replacement = self.top / 'replacement-orphan-root'
        real_owned = workbench._owned_transactions
        swapped = False
        def swap_before_enumeration(loaded):
            nonlocal swapped
            if not swapped:
                swapped = True
                shutil.copytree(self.root, replacement, copy_function=shutil.copy2)
                (replacement / orphan_name / 'foreign-sentinel').write_bytes(b'preserve')
                self.root.rename(held)
                replacement.rename(self.root)
            return real_owned(loaded)
        with patch('sgp131.workbench._owned_transactions', side_effect=swap_before_enumeration):
            with self.assertRaisesRegex(ValueError, 'identity'):
                workbench.recover(self.config)
        self.assertTrue((self.root / orphan_name / 'foreign-sentinel').exists())
        self.assertFalse((held / orphan_name).exists())
        shutil.rmtree(self.root)
        held.rename(self.root)

    def test_recovery_never_replays_journal_from_swapped_root(self):
        journal_path, _, _ = self._interrupted_transaction_paths()
        foreign_journal = journal_path.read_bytes()
        journal_path.unlink()
        held = self.top / 'held-journal-root'
        replacement = self.top / 'replacement-journal-root'
        displaced = self.top / 'displaced-journal-root'
        real_locked = workbench._locked
        real_idle = workbench._idle
        restored = False
        @contextmanager
        def swapped_locked(path):
            with real_locked(path) as loaded:
                shutil.copytree(self.root, replacement, copy_function=shutil.copy2)
                (replacement / 'journal.json').write_bytes(foreign_journal)
                (replacement / 'journal.json').chmod(0o600)
                self.root.rename(held)
                replacement.rename(self.root)
                yield loaded
        def restore_if_foreign(*args, **kwargs):
            nonlocal restored
            if not restored:
                restored = True
                self.root.rename(displaced)
                held.rename(self.root)
            return real_idle(*args, **kwargs)
        with patch('sgp131.workbench._locked', side_effect=swapped_locked), \
                patch('sgp131.workbench._idle', side_effect=restore_if_foreign):
            with self.assertRaisesRegex(ValueError, 'identity'):
                workbench.recover(self.config)
        self.assertFalse(restored, 'pinned root has no journal, so replay must not begin')
        self.assertFalse((held / 'EN/candidate.nds').exists())
        self.assertEqual((self.root / 'journal.json').read_bytes(), foreign_journal)
        shutil.rmtree(self.root)
        held.rename(self.root)

    def test_consumer_claim_rolls_back_lease_after_root_swap(self):
        self.pending()
        held = self.top / 'held-consumer-root'
        replacement = self.top / 'replacement-consumer-root'
        real_atomic = workbench._atomic_json_at
        swapped = False
        def swap_before_commit(*args, **kwargs):
            nonlocal swapped
            if not swapped and args[1] == 'consumers.json':
                swapped = True
                shutil.copytree(self.root, replacement, copy_function=shutil.copy2)
                self.root.rename(held)
                replacement.rename(self.root)
            return real_atomic(*args, **kwargs)
        with patch('sgp131.workbench._atomic_json_at', side_effect=swap_before_commit):
            with self.assertRaisesRegex(ValueError, 'identity'):
                workbench.claim_consumer(self.config, 'EN', 'pending', os.getpid())
        self.assertTrue(swapped)
        self.assertFalse((held / 'consumers.json').exists())
        self.assertFalse((self.root / 'consumers.json').exists())
        shutil.rmtree(self.root)
        held.rename(self.root)

    def test_lock_inode_replacement_cannot_bypass_held_flock(self):
        self.init()
        lock = self.root / '.lock'
        old = self.root / '.lock-old'
        fd = os.open(lock, os.O_RDWR)
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        real_load = workbench._load
        def replace_after_load(path):
            config = real_load(path)
            lock.rename(old)
            lock.write_bytes(b'')
            lock.chmod(0o600)
            return config
        try:
            with patch('sgp131.workbench._load', side_effect=replace_after_load):
                with self.assertRaisesRegex(ValueError, 'lock identity'):
                    workbench.inspect(self.config)
        finally:
            fcntl.flock(fd, fcntl.LOCK_UN)
            os.close(fd)
        lock.unlink()
        old.rename(lock)

    def test_reused_pid_with_different_process_identity_is_not_busy(self):
        result = self.pending()
        lease = workbench.claim_consumer(self.config, 'EN', 'pending', os.getpid())
        path = self.root / 'consumers.json'
        leases = json.loads(path.read_text())
        leases[lease['session']]['process_identity'] = 'posix:stale-process-start'
        path.write_text(json.dumps(leases))
        self.assertEqual(workbench.discard(self.config, 'EN')['discarded_sha256'],
                         result['output_sha256'])
        self.assertFalse((self.root / 'EN/pending.nds').exists())

    def test_cross_uid_reused_pid_compares_identity_after_eperm(self):
        with patch('sgp131.workbench.os.kill', side_effect=PermissionError), \
             patch('sgp131.workbench._process_identity', return_value='linux:newboot:newstart'):
            self.assertFalse(workbench._alive(1234, 'linux:oldboot:oldstart'))
        with patch('sgp131.workbench.os.kill', side_effect=PermissionError), \
             patch('sgp131.workbench._process_identity', return_value=None):
            self.assertTrue(workbench._alive(1234, 'linux:oldboot:oldstart'))

    def test_dead_pid_metadata_remains_reclaimable(self):
        self.init()
        lock = self.root / '.lock'
        lock.write_bytes(json.dumps({'pid': 99999999, 'session': 'dead'}).encode())
        with patch('sgp131.workbench._alive', return_value=False):
            workbench.inspect(self.config)
        self.assertEqual(lock.read_bytes(), b'')

    def test_recovery_at_each_accept_publication_boundary(self):
        result = self.pending()
        path = self.evidence(result['output_sha256'])
        accept_checked(self.config, path)
        real_replace = os.replace
        for filename in ('candidate.nds', 'candidate.json', 'fallback.nds', 'fallback.json'):
            workbench.build_candidate(self.config, 'EN', 'baseline')
            def interrupt(src, dst, *args, **kwargs):
                if Path(dst).name == filename:
                    raise OSError('boundary interruption')
                return real_replace(src, dst, *args, **kwargs)
            with patch('sgp131.workbench.os.replace', side_effect=interrupt):
                with self.assertRaisesRegex(OSError, 'boundary'):
                    accept_checked(self.config, path)
            workbench.recover(self.config)
            state = workbench.inspect(self.config)['languages']['EN']
            self.assertIsNone(state['pending'])
            self.assertEqual(state['candidate']['status'], 'accepted')
            self.assertEqual(state['fallback']['status'], 'accepted')
            self.assertEqual((self.root / 'EN/candidate.nds').read_bytes(), EN)
            self.assertEqual((self.root / 'EN/fallback.nds').read_bytes(), EN)
            self.assertFalse(any(self.root.glob('.txn-*')))

    def test_recovery_at_pending_pair_boundary_and_corrupt_snapshot_refused(self):
        self.init()
        real_replace = os.replace
        def interrupt(src, dst, *args, **kwargs):
            if Path(dst).name == 'pending.json':
                raise OSError('pending interruption')
            return real_replace(src, dst, *args, **kwargs)
        with patch('sgp131.workbench.os.replace', side_effect=interrupt):
            with self.assertRaisesRegex(OSError, 'pending interruption'):
                workbench.build_candidate(self.config, 'IT', 'baseline')
        journal = json.loads((self.root / 'journal.json').read_text())
        snapshot = self.root / journal['transaction'] / journal['writes']['IT/pending.nds']['source']
        snapshot.write_bytes(b'broken')
        with self.assertRaisesRegex(ValueError, 'snapshot hash'):
            workbench.recover(self.config)
        self.assertTrue((self.root / 'journal.json').exists())
        snapshot.write_bytes(IT)
        workbench.recover(self.config)
        state = workbench.inspect(self.config)['languages']
        self.assertEqual(state['IT']['pending']['status'], 'pending')
        self.assertIsNone(state['EN']['pending'])
        self.assertEqual(self.it.read_bytes(), IT)

    def test_discard_pending_preserves_verified_slots_and_refuses_active_consumer(self):
        result = self.pending()
        accept_checked(self.config, self.evidence(result['output_sha256']))
        workbench.build_candidate(self.config, 'EN', 'baseline')
        discard = getattr(workbench, 'discard', None)
        self.assertTrue(callable(discard), 'bounded lifecycle needs an explicit guarded pending discard')
        lease = workbench.claim_consumer(self.config, 'EN', 'pending', os.getpid())
        with self.assertRaisesRegex(ValueError, 'busy|consumer'):
            discard(self.config, 'EN')
        workbench.release_consumer(self.config, 'EN', lease['session'])
        discard(self.config, 'EN')
        self.assertFalse((self.root / 'EN/pending.nds').exists())
        self.assertEqual((self.root / 'EN/candidate.nds').read_bytes(), EN)
        workbench.build_candidate(self.config, 'EN', 'baseline')

    def test_discard_recovers_after_half_deleted_pair(self):
        self.pending()
        discard = getattr(workbench, 'discard', None)
        self.assertTrue(callable(discard), 'discard must journal cleanup')
        real_unlink = os.unlink
        def interrupt(path, *args, **kwargs):
            if Path(path).name == 'pending.json':
                raise OSError('interrupted cleanup')
            return real_unlink(path, *args, **kwargs)
        with patch('sgp131.workbench.os.unlink', side_effect=interrupt):
            with self.assertRaisesRegex(OSError, 'interrupted cleanup'):
                discard(self.config, 'EN')
        workbench.recover(self.config)
        self.assertFalse((self.root / 'EN/pending.nds').exists())
        self.assertFalse((self.root / 'EN/pending.json').exists())
        self.assertFalse((self.root / 'journal.json').exists())
        self.assertEqual(self.en.read_bytes(), EN)

    def test_discard_refuses_corrupt_or_foreign_pending(self):
        self.pending()
        discard = getattr(workbench, 'discard', None)
        self.assertTrue(callable(discard), 'discard must check ownership and exact pair')
        pending = self.root / 'EN/pending.nds'
        pending.write_bytes(b'foreign')
        with self.assertRaisesRegex(ValueError, 'hash|pair'):
            discard(self.config, 'EN')
        self.assertEqual(pending.read_bytes(), b'foreign')

    def test_hardlink_input_alias_in_managed_slot_refused(self):
        self.pending()
        pending = self.root / 'EN/pending.nds'
        pending.unlink()
        os.link(self.en, pending)
        with self.assertRaisesRegex(ValueError, 'alias'):
            workbench.inspect(self.config)
        self.assertEqual(self.en.read_bytes(), EN)

    def test_source_and_input_changes_refuse_acceptance(self):
        result = self.pending()
        evidence = self.evidence(result['output_sha256'])
        with patch('sgp131.build.source_snapshot', return_value={'changed': 'b' * 64}):
            with self.assertRaisesRegex(ValueError, 'source'):
                accept_checked(self.config, evidence)
        self.en.write_bytes(EN + b'changed')
        with self.assertRaisesRegex(ValueError, 'exact supported'):
            accept_checked(self.config, evidence)
        self.assertTrue((self.root / 'EN/pending.nds').exists())
        self.assertFalse((self.root / 'EN/candidate.nds').exists())

    def test_recovery_refuses_journal_deleting_verified_slot(self):
        result = self.pending()
        accept_checked(self.config, self.evidence(result['output_sha256']))
        real_replace = os.replace
        def interrupt(src, dst, *args, **kwargs):
            if Path(dst).name == 'pending.json':
                raise OSError('interrupted build')
            return real_replace(src, dst, *args, **kwargs)
        with patch('sgp131.workbench.os.replace', side_effect=interrupt):
            with self.assertRaises(OSError):
                workbench.build_candidate(self.config, 'EN', 'baseline')
        path = self.root / 'journal.json'
        journal = json.loads(path.read_text())
        journal['deletes'] = {'EN/candidate.nds': hashlib.sha256(EN).hexdigest()}
        path.write_text(json.dumps(journal))
        with self.assertRaisesRegex(ValueError, 'journal|transaction'):
            workbench.recover(self.config)
        self.assertEqual((self.root / 'EN/candidate.nds').read_bytes(), EN)

    def test_failed_transaction_marker_write_removes_own_directory(self):
        self.init()
        real_write = workbench._write_new_at
        def fail_marker(directory_fd, name, data):
            if name == 'owner.json':
                raise OSError('marker write failed')
            return real_write(directory_fd, name, data)
        with patch('sgp131.workbench._write_new_at', side_effect=fail_marker):
            with self.assertRaisesRegex(OSError, 'marker write'):
                workbench.build_candidate(self.config, 'EN', 'baseline')
        self.assertFalse(any(self.root.glob('.txn-*')))
        self.assertFalse((self.root / 'EN/pending.nds').exists())

    def test_owned_orphan_blocks_build_until_recover_preserves_foreign_directory(self):
        config = self.init()
        orphan = self.root / ('.txn-' + 'a' * 32)
        orphan.mkdir()
        (orphan / 'owner.json').write_text(json.dumps({'schema': 1, 'id': config['id'], 'directory': orphan.name}))
        (orphan / '0').write_bytes(b'owned interrupted staging output')
        foreign = self.root / ('.txn-' + 'b' * 32)
        foreign.mkdir()
        (foreign / 'unique.txt').write_text('keep')
        with self.assertRaisesRegex(ValueError, 'recover|orphan'):
            workbench.build_candidate(self.config, 'EN', 'baseline')
        workbench.recover(self.config)
        self.assertFalse(orphan.exists())
        self.assertEqual((foreign / 'unique.txt').read_text(), 'keep')
        workbench.build_candidate(self.config, 'EN', 'baseline')

    def test_source_change_after_composition_aborts_publication(self):
        self.init()
        stable = {'fixture.py': 'a' * 64}
        with patch('sgp131.build.source_snapshot', side_effect=[stable, stable, stable, {'changed': 'b' * 64}]):
            with self.assertRaisesRegex(ValueError, 'source'):
                workbench.build_candidate(self.config, 'EN', 'baseline')
        self.assertFalse((self.root / 'EN/pending.nds').exists())
        self.assertFalse(any(self.root.glob('.txn-*')))

    def test_recovery_preserves_foreign_replacement_during_discard(self):
        self.pending()
        real_unlink = os.unlink
        def interrupt(path, *args, **kwargs):
            if Path(path).name == 'pending.json':
                raise OSError('interrupted cleanup')
            return real_unlink(path, *args, **kwargs)
        with patch('sgp131.workbench.os.unlink', side_effect=interrupt):
            with self.assertRaises(OSError):
                workbench.discard(self.config, 'EN')
        pending = self.root / 'EN/pending.nds'
        pending.write_bytes(b'foreign replacement')
        with self.assertRaisesRegex(ValueError, 'deletion hash'):
            workbench.recover(self.config)
        self.assertEqual(pending.read_bytes(), b'foreign replacement')

    def test_cli_baseline_cycle_both_languages(self):
        import contextlib
        import io
        def cli(*arguments):
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                workbench.main(list(arguments))
            return json.loads(output.getvalue())
        cli('init', '--config', str(self.config), '--root', str(self.root),
            '--base-en', str(self.en), '--base-it', str(self.it))
        result = cli('build', '--config', str(self.config), '--language', 'EN', '--through', 'baseline')
        cli('build', '--config', str(self.config), '--language', 'IT', '--through', 'baseline')
        accepted_evidence = self.evidence(result['output_sha256'])
        cli('accept', '--config', str(self.config), '--evidence', str(accepted_evidence),
            '--evidence-sha256', hashlib.sha256(accepted_evidence.read_bytes()).hexdigest())
        cli('discard', '--config', str(self.config), '--language', 'IT')
        cli('recover', '--config', str(self.config))
        state = cli('inspect', '--config', str(self.config))['languages']
        self.assertEqual(state['EN']['candidate']['status'], 'accepted')
        self.assertIsNone(state['IT']['pending'])

    def test_consumer_refuses_self_consistent_but_untrusted_pending_hash(self):
        self.pending()
        rom = self.root / 'EN/pending.nds'
        receipt = self.root / 'EN/pending.json'
        rom.write_bytes(b'foreign but self-consistent')
        report = json.loads(receipt.read_text())
        report['output_sha256'] = hashlib.sha256(rom.read_bytes()).hexdigest()
        report['output_bytes'] = rom.stat().st_size
        receipt.write_text(json.dumps(report))
        with self.assertRaisesRegex(ValueError, 'baseline|hash|identity'):
            workbench.claim_consumer(self.config, 'EN', 'pending', os.getpid())
        self.assertFalse((self.root / 'consumers.json').exists())

    def interrupted_accept(self, filename='candidate.nds'):
        result = self.pending()
        real_replace = os.replace
        def interrupt(src, dst, *args, **kwargs):
            if Path(dst).name == filename:
                raise OSError('review reproducer interruption')
            return real_replace(src, dst, *args, **kwargs)
        with patch('sgp131.workbench.os.replace', side_effect=interrupt):
            with self.assertRaisesRegex(OSError, 'review reproducer'):
                accept_checked(self.config, self.evidence(result['output_sha256']))
        return result

    def test_review_recovery_rechecks_changed_sources(self):
        self.interrupted_accept()
        journal = (self.root / 'journal.json').read_bytes()
        with patch('sgp131.build.source_snapshot', return_value={'changed.py': 'b' * 64}):
            with self.assertRaisesRegex(ValueError, 'source|provenance'):
                workbench.recover(self.config)
        self.assertEqual((self.root / 'journal.json').read_bytes(), journal)
        self.assertFalse((self.root / 'EN/candidate.nds').exists())
        self.assertTrue(any(self.root.glob('.txn-*')))
        workbench.recover(self.config)
        self.assertEqual(workbench.inspect(self.config)['languages']['EN']['candidate']['status'], 'accepted')

    def _interrupted_transaction_paths(self):
        self.interrupted_accept()
        journal_path = self.root / 'journal.json'
        journal = json.loads(journal_path.read_text())
        directory = self.root / journal['transaction']
        sources = [directory / entry['source'] for entry in journal['writes'].values()]
        return journal_path, directory, sources

    def test_recovery_refuses_relaxed_transaction_directory_before_publication(self):
        journal, directory, _ = self._interrupted_transaction_paths()
        original = journal.read_bytes()
        directory.chmod(0o755)
        with self.assertRaisesRegex(ValueError, 'permissions'):
            workbench.recover(self.config)
        self.assertEqual(journal.read_bytes(), original)
        self.assertFalse((self.root / 'EN/candidate.nds').exists())
        self.assertFalse((self.root / 'EN/candidate.json').exists())

    def test_recovery_refuses_relaxed_transaction_owner_before_publication(self):
        journal, directory, _ = self._interrupted_transaction_paths()
        original = journal.read_bytes()
        (directory / 'owner.json').chmod(0o644)
        with self.assertRaisesRegex(ValueError, 'permissions'):
            workbench.recover(self.config)
        self.assertEqual(journal.read_bytes(), original)
        self.assertFalse((self.root / 'EN/candidate.nds').exists())
        self.assertFalse((self.root / 'EN/candidate.json').exists())

    def test_recovery_refuses_relaxed_snapshot_before_publication(self):
        journal, _, sources = self._interrupted_transaction_paths()
        original = journal.read_bytes()
        sources[0].chmod(0o644)
        with self.assertRaisesRegex(ValueError, 'permissions'):
            workbench.recover(self.config)
        self.assertEqual(journal.read_bytes(), original)
        self.assertFalse((self.root / 'EN/candidate.nds').exists())
        self.assertFalse((self.root / 'EN/candidate.json').exists())

    def test_review_recovery_preserves_unrelated_write_target(self):
        self.interrupted_accept()
        target = self.root / 'EN/candidate.nds'
        target.write_bytes(b'unrelated replacement')
        journal = (self.root / 'journal.json').read_bytes()
        with self.assertRaisesRegex(ValueError, 'destination|target|precondition'):
            workbench.recover(self.config)
        self.assertEqual(target.read_bytes(), b'unrelated replacement')
        self.assertEqual((self.root / 'journal.json').read_bytes(), journal)
        self.assertFalse((self.root / 'EN/candidate.json').exists())

    def test_review_malformed_live_consumer_cannot_bypass_discard(self):
        self.pending()
        lease = workbench.claim_consumer(self.config, 'EN', 'pending', os.getpid())
        path = self.root / 'consumers.json'
        leases = json.loads(path.read_text())
        leases[lease['session']]['slot'] = 'pendng'
        path.write_text(json.dumps(leases))
        with self.assertRaisesRegex(ValueError, 'consumer|lease'):
            workbench.discard(self.config, 'EN')
        self.assertEqual((self.root / 'EN/pending.nds').read_bytes(), EN)
        self.assertFalse((self.root / 'journal.json').exists())

    def test_review_missing_provenance_refuses_consumer(self):
        self.pending()
        path = self.root / 'EN/pending.json'
        report = json.loads(path.read_text())
        for field in ('source_sha256', 'receipts', 'composition'):
            del report[field]
        path.write_text(json.dumps(report))
        with self.assertRaisesRegex(ValueError, 'provenance|source|receipt|composition'):
            workbench.claim_consumer(self.config, 'EN', 'pending', os.getpid())
        self.assertFalse((self.root / 'consumers.json').exists())

    def test_recovery_changed_input_and_partial_source_change_remain_blocked(self):
        self.interrupted_accept('candidate.json')
        original_journal = (self.root / 'journal.json').read_bytes()
        original_files = {p.name: p.read_bytes() for p in (self.root / 'EN').iterdir()}
        self.en.write_bytes(b'changed original')
        with self.assertRaisesRegex(ValueError, 'input|exact supported'):
            workbench.recover(self.config)
        self.assertEqual((self.root / 'journal.json').read_bytes(), original_journal)
        self.assertEqual({p.name: p.read_bytes() for p in (self.root / 'EN').iterdir()}, original_files)
        self.en.write_bytes(EN)
        with patch('sgp131.build.source_snapshot', return_value={'changed.py': 'b' * 64}):
            with self.assertRaisesRegex(ValueError, 'source|provenance'):
                workbench.recover(self.config)
        self.assertEqual({p.name: p.read_bytes() for p in (self.root / 'EN').iterdir()}, original_files)
        with self.assertRaisesRegex(ValueError, 'journal|recover'):
            workbench.inspect(self.config)
        workbench.recover(self.config)
        self.assertEqual(workbench.inspect(self.config)['languages']['EN']['candidate']['status'], 'accepted')

    def test_recovery_preflights_every_existing_candidate_and_fallback_destination(self):
        result = self.pending()
        evidence_path = self.evidence(result['output_sha256'])
        accept_checked(self.config, evidence_path)
        workbench.build_candidate(self.config, 'EN', 'baseline')
        accept_checked(self.config, evidence_path)
        real_replace = os.replace
        for filename in ('candidate.nds', 'candidate.json', 'fallback.nds', 'fallback.json'):
            workbench.build_candidate(self.config, 'EN', 'baseline')
            def interrupt(src, dst, *args, **kwargs):
                if Path(dst).name == 'candidate.nds':
                    raise OSError('before any publication')
                return real_replace(src, dst, *args, **kwargs)
            with patch('sgp131.workbench.os.replace', side_effect=interrupt):
                with self.assertRaises(OSError):
                    accept_checked(self.config, evidence_path)
            target = self.root / 'EN' / filename
            previous = target.read_bytes()
            target.unlink()  # Preserve the staged hardlink snapshots.
            target.write_bytes(b'unrelated replacement')
            before = {p.name: p.read_bytes() for p in (self.root / 'EN').iterdir()}
            journal = (self.root / 'journal.json').read_bytes()
            with self.subTest(filename=filename), self.assertRaisesRegex(ValueError, 'destination|target|precondition'):
                workbench.recover(self.config)
            self.assertEqual({p.name: p.read_bytes() for p in (self.root / 'EN').iterdir()}, before)
            self.assertEqual((self.root / 'journal.json').read_bytes(), journal)
            target.write_bytes(previous)
            workbench.recover(self.config)

    def test_recovery_preserves_foreign_pending_destination(self):
        self.init()
        real_replace = os.replace
        def interrupt(src, dst, *args, **kwargs):
            if Path(dst).name == 'pending.nds':
                raise OSError('before pending publication')
            return real_replace(src, dst, *args, **kwargs)
        with patch('sgp131.workbench.os.replace', side_effect=interrupt):
            with self.assertRaises(OSError):
                workbench.build_candidate(self.config, 'EN', 'baseline')
        target = self.root / 'EN/pending.nds'
        target.write_bytes(b'unrelated pending replacement')
        with self.assertRaisesRegex(ValueError, 'destination|target|precondition'):
            workbench.recover(self.config)
        self.assertEqual(target.read_bytes(), b'unrelated pending replacement')
        self.assertFalse((self.root / 'EN/pending.json').exists())

    def test_malformed_consumer_records_fail_closed_for_discard_and_recovery(self):
        import copy
        self.pending()
        lease = workbench.claim_consumer(self.config, 'EN', 'pending', os.getpid())
        path = self.root / 'consumers.json'
        valid = json.loads(path.read_text())
        invalid = [[], {'bad-session': valid[lease['session']]}]
        for field, value in (('language', 'XX'), ('slot', 'pendng'), ('pid', True),
                             ('pid', 0), ('pid', '1'), ('session', '0' * 32),
                             ('sha256', 'bad')):
            mutated = copy.deepcopy(valid)
            mutated[lease['session']][field] = value
            invalid.append(mutated)
        for record in invalid:
            path.write_text(json.dumps(record))
            for operation in (lambda: workbench.discard(self.config, 'EN'), lambda: workbench.recover(self.config)):
                with self.subTest(record=record), self.assertRaisesRegex(ValueError, 'consumer|lease'):
                    operation()
            self.assertEqual((self.root / 'EN/pending.nds').read_bytes(), EN)
            self.assertFalse((self.root / 'journal.json').exists())
        path.write_text(json.dumps(valid))
        workbench.release_consumer(self.config, 'EN', lease['session'])

    def test_recovery_rejects_malformed_lease_before_replay(self):
        self.interrupted_accept()
        (self.root / 'consumers.json').write_text(json.dumps({'broken': {'pid': os.getpid(), 'slot': 'pendng'}}))
        journal = (self.root / 'journal.json').read_bytes()
        with self.assertRaisesRegex(ValueError, 'consumer|lease'):
            workbench.recover(self.config)
        self.assertEqual((self.root / 'journal.json').read_bytes(), journal)
        self.assertFalse((self.root / 'EN/candidate.nds').exists())

    def test_discard_after_source_change_and_missing_original_preserves_accepted_roles(self):
        result = self.pending()
        evidence_path = self.evidence(result['output_sha256'])
        accept_checked(self.config, evidence_path)
        workbench.build_candidate(self.config, 'EN', 'baseline')
        accept_checked(self.config, evidence_path)
        workbench.build_candidate(self.config, 'EN', 'baseline')
        before = {name: (self.root / 'EN' / name).read_bytes()
                  for name in ('candidate.nds', 'candidate.json', 'fallback.nds', 'fallback.json')}
        self.en.unlink()
        with patch('sgp131.build.source_snapshot', return_value={'changed.py': 'b' * 64}):
            workbench.discard(self.config, 'EN')
        self.assertFalse((self.root / 'EN/pending.nds').exists())
        self.assertFalse(self.en.exists())
        self.assertEqual({name: (self.root / 'EN' / name).read_bytes() for name in before}, before)
        self.assertEqual(self.it.read_bytes(), IT)

    def test_discard_replay_after_source_change_and_missing_original_is_cleanup_only(self):
        self.pending()
        real_unlink = os.unlink
        def interrupt(path, *args, **kwargs):
            if Path(path).name == 'pending.json':
                raise OSError('interrupted discard')
            return real_unlink(path, *args, **kwargs)
        with patch('sgp131.workbench.os.unlink', side_effect=interrupt):
            with self.assertRaises(OSError):
                workbench.discard(self.config, 'EN')
        self.en.unlink()
        with patch('sgp131.build.source_snapshot', return_value={'changed.py': 'b' * 64}):
            workbench.recover(self.config)
        self.assertFalse((self.root / 'EN/pending.json').exists())
        self.assertFalse((self.root / 'EN/candidate.nds').exists())
        self.assertFalse(self.en.exists())

    def test_build_replay_rechecks_sources_and_original_before_any_write(self):
        self.init()
        real_replace = os.replace
        def interrupt(src, dst, *args, **kwargs):
            if Path(dst).name == 'pending.nds':
                raise OSError('interrupted build')
            return real_replace(src, dst, *args, **kwargs)
        with patch('sgp131.workbench.os.replace', side_effect=interrupt):
            with self.assertRaises(OSError):
                workbench.build_candidate(self.config, 'EN', 'baseline')
        journal = (self.root / 'journal.json').read_bytes()
        with patch('sgp131.build.source_snapshot', return_value={'changed.py': 'b' * 64}):
            with self.assertRaisesRegex(ValueError, 'source|provenance'):
                workbench.recover(self.config)
        self.en.write_bytes(b'changed original')
        with self.assertRaisesRegex(ValueError, 'input|exact supported'):
            workbench.recover(self.config)
        self.assertEqual((self.root / 'journal.json').read_bytes(), journal)
        self.assertFalse((self.root / 'EN/pending.nds').exists())
        self.en.write_bytes(EN)
        workbench.recover(self.config)
        self.assertEqual((self.root / 'EN/pending.nds').read_bytes(), EN)

    def test_replay_requires_full_receipt_schema_before_any_write(self):
        import copy
        self.interrupted_accept()
        path = self.root / 'journal.json'
        original = path.read_bytes()
        for field in ('source_sha256', 'receipts', 'composition'):
            record = copy.deepcopy(json.loads(original))
            del record['receipt'][field]
            path.write_text(json.dumps(record))
            before = path.read_bytes()
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, 'provenance|source|receipt|composition'):
                workbench.recover(self.config)
            self.assertFalse((self.root / 'EN/candidate.nds').exists())
            self.assertEqual(path.read_bytes(), before)
        path.write_bytes(original)
        workbench.recover(self.config)

    def test_discard_replay_refuses_changed_expected_base_metadata(self):
        self.pending()
        real_unlink = os.unlink
        def interrupt(path, *args, **kwargs):
            if Path(path).name == 'pending.json':
                raise OSError('interrupted discard')
            return real_unlink(path, *args, **kwargs)
        with patch('sgp131.workbench.os.unlink', side_effect=interrupt):
            with self.assertRaises(OSError):
                workbench.discard(self.config, 'EN')
        record = json.loads(self.config.read_text())
        record['bases']['EN']['path'] = str(self.it)
        # Different configuration metadata cannot redefine the prepared cleanup
        # provenance even if the original path is currently unavailable.
        record['bases']['IT']['path'] = str(self.top / 'unavailable-it.nds')
        self.config.write_text(json.dumps(record))
        with self.assertRaisesRegex(ValueError, 'metadata|identity|hash'):
            workbench.recover(self.config)
        self.assertTrue((self.root / 'EN/pending.json').exists())
        self.assertTrue((self.root / 'journal.json').exists())
        self.assertEqual(self.it.read_bytes(), IT)


class UIWorkbenchTests(unittest.TestCase):
    """Synthetic bytes and policy seam; filesystem fault injection, no device proof."""
    setUp = WorkbenchTests.setUp
    init = WorkbenchTests.init

    def ui_setup(self):
        from .test_build import UI_MAP, UI_CONFIG, synthetic_install, synthetic_ui
        self.charmap = self.top / 'charmap.txt'; self.charmap.write_bytes(UI_MAP)
        self.ui_config = self.top / 'ui.json'; self.ui_config.write_text(json.dumps(UI_CONFIG))
        for context in (patch('sgp131.guide_content.CHARMAP_SHA256', hashlib.sha256(UI_MAP).hexdigest()),
                        patch('sgp131.ui.install', side_effect=synthetic_install),
                        patch('sgp131.ui_verify.verify', side_effect=synthetic_ui), self.disk):
            context.start(); self.addCleanup(context.stop)
        self.init()

    def ui_build(self, language='EN'):
        return workbench.build_candidate(self.config, language, 'ui', charmap=self.charmap, ui_config=self.ui_config)

    def ui_evidence(self, result):
        from .test_evidence import ui_report_for
        path = self.top / 'evidence-ui.json'; path.write_text(json.dumps(ui_report_for(result)))
        return path

    def snapshot(self):
        return {str(p.relative_to(self.root)): p.read_bytes() for p in self.root.rglob('*')
                if p.is_file() and p.name != '.lock'}

    def test_ui_build_both_languages_and_inspect_without_compiling(self):
        self.ui_setup()
        for language in ('EN', 'IT'):
            result = self.ui_build(language)
            self.assertEqual(result['language'], language)
            self.assertEqual(result['status'], 'pending')
            self.assertGreaterEqual(result['disk_preflight']['planned_peak_bytes'], 256 * 1024**2 + 16 * 1024**2)
        with patch('sgp131.ui_verify.verify', side_effect=AssertionError('inspect must not compile')):
            state = workbench.inspect(self.config)['languages']
        self.assertEqual(state['EN']['pending']['assurance'], 'recorded-only')
        self.assertFalse(any(self.root.glob('.scratch-*')))

    def test_ui_scratch_stays_outside_swapped_workbench_root(self):
        from . import build
        self.ui_setup()
        held = self.top / 'held-ui-root'
        replacement = self.top / 'replacement-ui-root'
        real_workspace = build.ui_workspace
        observed = []
        swapped = False
        @contextmanager
        def swap_root(scratch, inputs, directory_fd=None):
            nonlocal swapped
            scratch = Path(scratch)
            observed.append(scratch)
            self.assertEqual(scratch, Path('.'))
            if not swapped:
                swapped = True
                shutil.copytree(self.root, replacement, copy_function=shutil.copy2)
                foreign = replacement / '.scratch-foreign'
                foreign.mkdir()
                (foreign / 'sentinel').write_bytes(b'preserve')
                self.root.rename(held)
                replacement.rename(self.root)
            with real_workspace(scratch, inputs, directory_fd) as charmap:
                yield charmap
        with patch('sgp131.build.ui_workspace', side_effect=swap_root):
            with self.assertRaisesRegex(ValueError, 'identity'):
                self.ui_build()
        self.assertGreaterEqual(len(observed), 1)
        self.assertEqual((self.root / '.scratch-foreign/sentinel').read_bytes(), b'preserve')
        self.assertFalse(any(held.glob('.scratch-*')))
        shutil.rmtree(self.root)
        held.rename(self.root)

    def test_mechanics_chain_builds_admits_claims_and_accepts(self):
        from . import build, mechanics_stages
        from .test_evidence import ui_report_for
        from .test_mechanics_stages import FakeStage
        self.ui_setup()
        fakes = {'moves': FakeStage('moves', 3, 6, 0x41), 'ai': FakeStage('ai', 10, 14, 0x42)}
        with patch.dict(mechanics_stages.REGISTRY, fakes, clear=True), \
                patch('sgp131.mechanics_stages.check_ui_invariants', side_effect=lambda *a: {}):
            result = workbench.build_candidate(self.config, 'EN', 'ai', charmap=self.charmap, ui_config=self.ui_config)
            self.assertEqual((result['through'], result['status']), ('ai', 'pending'))
            self.assertEqual([r['stage'] for r in result['receipts']], ['ui', 'moves', 'ai'])
            self.assertEqual(workbench.inspect(self.config)['languages']['EN']['pending']['assurance'], 'recorded-only')
            lease = workbench.claim_consumer(self.config, 'EN', 'pending', os.getpid())
            workbench.release_consumer(self.config, 'EN', lease['session'])
            acceptance = ui_report_for(result)
            template = acceptance['cases'][0]
            acceptance['through'] = 'ai'
            acceptance['cases'] = [dict(template, id=name, record_key=name) for name in build.REQUIRED_CASES['ai']]
            path = self.top / 'evidence-ai.json'; path.write_text(json.dumps(acceptance))
            accepted = accept_checked(self.config, path)
            self.assertEqual(accepted['status'], 'accepted')
            # recorded UI input size must equal the configured base size, also for a chain
            pending_json = self.root / 'IT/pending.json'
            second = workbench.build_candidate(self.config, 'IT', 'ai', charmap=self.charmap, ui_config=self.ui_config)
            original = pending_json.read_text()
            record = json.loads(original)
            record['receipts'][0]['input_bytes'] += 1
            record['composition'] = build.composition_for(record['receipts'])
            pending_json.write_text(json.dumps(record))
            with self.assertRaisesRegex(ValueError, 'input size|identity'):
                workbench.claim_consumer(self.config, 'IT', 'pending', os.getpid())
            pending_json.write_text(original)
            workbench.discard(self.config, 'IT')
            # one mechanical case missing: acceptance refused, nothing published
            second = workbench.build_candidate(self.config, 'IT', 'ai', charmap=self.charmap, ui_config=self.ui_config)
            incomplete = ui_report_for(second)
            incomplete['through'] = 'ai'
            incomplete['cases'] = [dict(template, id=name, record_key=name, candidate_sha256=second['output_sha256'])
                                   for name in build.REQUIRED_CASES['ai'][:-1]]
            path.write_text(json.dumps(incomplete))
            with self.assertRaisesRegex(ValueError, 'mandatory|case'):
                accept_checked(self.config, path)

    def test_ui_missing_inputs_and_disk_floor_precede_installer(self):
        self.ui_setup()
        with patch('sgp131.ui.install', side_effect=AssertionError('must reject before compiler')):
            with self.assertRaisesRegex(ValueError, 'explicit'):
                workbench.build_candidate(self.config, 'EN', 'ui')
            free = workbench.MIN_FREE + 200 * 1024**2
            with patch('sgp131.workbench.shutil.disk_usage', return_value=shutil._ntuple_diskusage(free, 0, free)):
                with self.assertRaisesRegex(ValueError, 'budget'):
                    self.ui_build()
        self.assertFalse(any(self.root.glob('.scratch-*')))
        self.assertFalse((self.root / 'EN/pending.nds').exists())

    def test_ui_accept_and_consumer_independently_refuse_forged_policy(self):
        from . import build
        self.ui_setup(); result = self.ui_build()
        rom = self.root / 'EN/pending.nds'; receipt = self.root / 'EN/pending.json'
        for payload in (EN + b'outside policy', EN + b'forged authored UI'):
            rom.write_bytes(payload)
            report = json.loads(receipt.read_text())
            report['output_sha256'] = hashlib.sha256(payload).hexdigest(); report['output_bytes'] = len(payload)
            stage = report['receipts'][0]; stage['output_sha256'] = report['output_sha256']; stage['output_bytes'] = len(payload)
            stage['writes'] = ['caller allows everything']; report['composition'] = build.ui_composition(stage)
            receipt.write_text(json.dumps(report))
            for action in (lambda: workbench.claim_consumer(self.config, 'EN', 'pending', os.getpid()),
                           lambda: accept_checked(self.config, self.ui_evidence(report))):
                with self.subTest(payload=payload), self.assertRaisesRegex(ValueError, 'policy'):
                    action()
            self.assertFalse((self.root / 'EN/candidate.nds').exists())
            self.assertFalse((self.root / 'journal.json').exists())

    def test_ui_source_and_external_drift_refuse_admission_but_allow_owned_cleanup(self):
        self.ui_setup(); first = self.ui_build(); accept_checked(self.config, self.ui_evidence(first))
        self.ui_build(); accept_checked(self.config, self.ui_evidence(first)); result = self.ui_build()
        accepted = {n: (self.root / 'EN' / n).read_bytes() for n in ('candidate.nds', 'candidate.json', 'fallback.nds', 'fallback.json')}
        for changed in ('sources', 'config', 'charmap', 'input'):
            old_config, old_map = self.ui_config.read_bytes(), self.charmap.read_bytes()
            if changed == 'config': self.ui_config.write_text('{}')
            if changed == 'charmap': self.charmap.write_bytes(b'drift')
            if changed == 'input': self.en.write_bytes(b'drift')
            with patch('sgp131.build.source_snapshot', return_value={'changed.py': 'b' * 64} if changed == 'sources' else {'fixture.py': 'a' * 64}):
                with self.subTest(changed=changed), self.assertRaises(ValueError):
                    workbench.claim_consumer(self.config, 'EN', 'pending', os.getpid())
                with self.subTest(changed=changed), self.assertRaises(ValueError):
                    accept_checked(self.config, self.ui_evidence(result))
            self.ui_config.write_bytes(old_config); self.charmap.write_bytes(old_map); self.en.write_bytes(EN)
        self.en.unlink(); self.ui_config.unlink(); self.charmap.unlink()
        with patch('sgp131.ui_verify.verify', side_effect=AssertionError('cleanup must not compile')):
            workbench.discard(self.config, 'EN')
        self.assertEqual({n: (self.root / 'EN' / n).read_bytes() for n in accepted}, accepted)

    def test_ui_replay_source_drift_preserves_every_byte_until_restored(self):
        self.ui_setup()
        real_replace = os.replace
        for operation in ('build', 'accept'):
            if operation == 'accept': result = self.ui_build()
            for filename in (('pending.nds', 'pending.json') if operation == 'build' else ('candidate.nds', 'candidate.json')):
                def interrupt(src, dst, *args, **kwargs):
                    if Path(dst).name == filename: raise OSError('synthetic publication interruption')
                    return real_replace(src, dst, *args, **kwargs)
                with patch('sgp131.workbench.os.replace', side_effect=interrupt):
                    with self.assertRaisesRegex(OSError, 'synthetic'):
                        result = self.ui_build() if operation == 'build' else accept_checked(self.config, self.ui_evidence(result))
                before = self.snapshot()
                with patch('sgp131.build.source_snapshot', return_value={'changed.py': 'b' * 64}):
                    with self.assertRaisesRegex(ValueError, 'source'):
                        workbench.recover(self.config)
                self.assertEqual(self.snapshot(), before)
                workbench.recover(self.config)
                if operation == 'build': workbench.discard(self.config, 'EN')
                elif filename == 'candidate.nds': result = self.ui_build()

    def test_ui_replay_rejects_self_consistent_forged_staged_pair_before_mutation(self):
        from . import build
        self.ui_setup(); real_replace = os.replace
        def interrupt(src, dst, *args, **kwargs):
            if Path(dst).name == 'pending.nds': raise OSError('synthetic interruption')
            return real_replace(src, dst, *args, **kwargs)
        with patch('sgp131.workbench.os.replace', side_effect=interrupt):
            with self.assertRaises(OSError): self.ui_build()
        path = self.root / 'journal.json'; journal = json.loads(path.read_text()); directory = self.root / journal['transaction']
        rom_entry = journal['writes']['EN/pending.nds']; report_entry = journal['writes']['EN/pending.json']
        payload = EN + b'forged authored UI'; (directory / rom_entry['source']).write_bytes(payload)
        report = json.loads((directory / report_entry['source']).read_text())
        report.update(output_sha256=hashlib.sha256(payload).hexdigest(), output_bytes=len(payload))
        report['receipts'][0].update(output_sha256=report['output_sha256'], output_bytes=len(payload))
        report['composition'] = build.ui_composition(report['receipts'][0])
        raw = workbench._json(report); (directory / report_entry['source']).write_bytes(raw)
        rom_entry['sha256'] = report['output_sha256']; report_entry['sha256'] = hashlib.sha256(raw).hexdigest(); journal['receipt'] = report
        path.write_text(json.dumps(journal)); before = self.snapshot()
        with self.assertRaisesRegex(ValueError, 'policy'): workbench.recover(self.config)
        self.assertEqual(self.snapshot(), before)

    def test_ui_cleanup_replay_missing_inputs_and_alias_refusal_preserve_roles(self):
        self.ui_setup(); first = self.ui_build(); accept_checked(self.config, self.ui_evidence(first)); self.ui_build()
        pending = self.root / 'EN/pending.nds'; saved = pending.read_bytes(); pending.unlink(); os.link(self.root / 'EN/candidate.nds', pending)
        with self.assertRaisesRegex(ValueError, 'alias'): workbench.discard(self.config, 'EN')
        pending.unlink(); pending.write_bytes(saved)
        real_unlink = os.unlink
        def interrupt(path, *args, **kwargs):
            if Path(path).name == 'pending.json': raise OSError('synthetic discard interruption')
            return real_unlink(path, *args, **kwargs)
        with patch('sgp131.workbench.os.unlink', side_effect=interrupt):
            with self.assertRaises(OSError): workbench.discard(self.config, 'EN')
        self.en.unlink(); self.ui_config.unlink(); self.charmap.unlink()
        with patch('sgp131.ui_verify.verify', side_effect=AssertionError('cleanup must not compile')):
            workbench.recover(self.config)
        self.assertFalse((self.root / 'EN/pending.json').exists())
        self.assertTrue((self.root / 'EN/candidate.nds').exists())

    def test_ui_compiler_failure_cleans_only_owned_scratch(self):
        self.ui_setup(); sentinel = self.root / '.scratch-foreign'; sentinel.mkdir(); (sentinel / 'keep').write_text('unique')
        def failure(before, language, charmap, work_dir):
            (work_dir / 'compiler-diagnostic').write_text('bounded test failure')
            raise ValueError('synthetic compiler failure')
        with patch('sgp131.ui.install', side_effect=failure):
            with self.assertRaisesRegex(ValueError, 'compiler'): self.ui_build()
        self.assertEqual((sentinel / 'keep').read_text(), 'unique')
        self.assertEqual(list(self.root.glob('.scratch-*')), [sentinel])

    def test_ui_consumer_rechecks_live_pair_after_long_verification(self):
        from .test_build import synthetic_ui
        self.ui_setup(); self.ui_build()
        pending = self.root / 'EN/pending.nds'
        def mutate(*args, **kwargs):
            result = synthetic_ui(*args, **kwargs)
            pending.write_bytes(EN + b'mutated during verification')
            return result
        with patch('sgp131.ui_verify.verify', side_effect=mutate):
            with self.assertRaisesRegex(ValueError, 'hash|pair'):
                workbench.claim_consumer(self.config, 'EN', 'pending', os.getpid())
        self.assertFalse((self.root / 'consumers.json').exists())

    def test_ui_replay_rechecks_snapshot_after_long_verification(self):
        from .test_build import synthetic_ui
        self.ui_setup(); real_replace = os.replace
        def interrupt(src, dst, *args, **kwargs):
            if Path(dst).name == 'pending.nds': raise OSError('synthetic interruption')
            return real_replace(src, dst, *args, **kwargs)
        with patch('sgp131.workbench.os.replace', side_effect=interrupt):
            with self.assertRaises(OSError): self.ui_build()
        journal = json.loads((self.root / 'journal.json').read_text())
        source = self.root / journal['transaction'] / journal['writes']['EN/pending.nds']['source']
        def mutate(*args, **kwargs):
            result = synthetic_ui(*args, **kwargs)
            source.write_bytes(EN + b'mutated during verification')
            return result
        with patch('sgp131.ui_verify.verify', side_effect=mutate):
            with self.assertRaisesRegex(ValueError, 'snapshot|hash'):
                workbench.recover(self.config)
        self.assertFalse((self.root / 'EN/pending.nds').exists())
        self.assertTrue((self.root / 'journal.json').exists())

    def test_ui_replay_external_input_drift_and_live_lease_leave_journal_untouched(self):
        self.ui_setup(); result = self.ui_build(); real_replace = os.replace
        def interrupt(src, dst, *args, **kwargs):
            if Path(dst).name == 'candidate.nds': raise OSError('synthetic interruption')
            return real_replace(src, dst, *args, **kwargs)
        with patch('sgp131.workbench.os.replace', side_effect=interrupt):
            with self.assertRaises(OSError): accept_checked(self.config, self.ui_evidence(result))
        before = self.snapshot()
        for path, value in ((self.ui_config, b'{}'), (self.charmap, b'drift'), (self.en, b'drift')):
            saved = path.read_bytes(); path.write_bytes(value)
            with self.subTest(path=path), self.assertRaises(ValueError): workbench.recover(self.config)
            self.assertEqual(self.snapshot(), before); path.write_bytes(saved)
        session = 'f' * 32
        lease = {session: {'session': session, 'pid': os.getpid(),
                          'process_identity': workbench._process_identity(os.getpid()),
                          'language': 'EN', 'slot': 'pending',
                          'sha256': result['output_sha256']}}
        (self.root / 'consumers.json').write_text(json.dumps(lease)); busy = self.snapshot()
        with self.assertRaisesRegex(ValueError, 'busy'): workbench.recover(self.config)
        self.assertEqual(self.snapshot(), busy)
        (self.root / 'consumers.json').unlink(); workbench.recover(self.config)

    def test_ui_original_or_managed_input_alias_refused_before_compiler(self):
        self.ui_setup()
        alias = self.top / 'alias.txt'; os.link(self.en, alias)
        with patch('sgp131.guide_content.CHARMAP_SHA256', hashlib.sha256(EN).hexdigest()):
            with self.assertRaisesRegex(ValueError, 'alias'):
                workbench.build_candidate(self.config, 'EN', 'ui', charmap=alias, ui_config=self.ui_config)
        self.assertFalse(any(self.root.glob('.scratch-*')))

    def test_immutable_input_size_drift_is_refused_before_snapshot_read(self):
        config = self.init(); self.en.write_bytes(EN + b'oversized')
        with patch('pathlib.Path.read_bytes', side_effect=AssertionError('must stat bound input before read')):
            with self.assertRaisesRegex(ValueError, 'input|supported|size'):
                workbench._base(config, 'EN')

    def test_ui_cli_requires_and_consumes_explicit_paths(self):
        import contextlib
        import io
        self.ui_setup(); output = io.StringIO()
        with contextlib.redirect_stdout(output):
            workbench.main(['build', '--config', str(self.config), '--language', 'IT', '--through', 'ui',
                            '--charmap', str(self.charmap), '--ui-config', str(self.ui_config)])
        report = json.loads(output.getvalue())
        self.assertEqual(report['language'], 'IT')
        self.assertEqual(report['status'], 'pending')
        self.assertEqual(Path(report['path']).read_bytes(), IT + b'fixed authored UI')

    def coherent_historical_substitution(self, pending, role='candidate'):
        """External injection only; keep old role inodes out of the injected edit."""
        import copy
        from . import build
        from .test_evidence import ui_report_for
        payload = EN + b'coherent forged historical UI'
        report = copy.deepcopy(pending)
        for field in ('path', 'disk_budget', 'disk_preflight'):
            report.pop(field, None)
        report.update(status='accepted', output_sha256=hashlib.sha256(payload).hexdigest(), output_bytes=len(payload))
        report['receipts'][0].update(output_sha256=report['output_sha256'], output_bytes=len(payload))
        report['composition'] = build.ui_composition(report['receipts'][0])
        report['acceptance'] = ui_report_for(report)
        rom, receipt = self.root / 'EN' / (role + '.nds'), self.root / 'EN' / (role + '.json')
        rom.unlink(missing_ok=True); receipt.unlink(missing_ok=True)
        rom.write_bytes(payload); receipt.write_bytes(workbench._json(report))
        # Establish coherent recorded metadata; no transformation admission.
        self.assertEqual(workbench._pair(json.loads(self.config.read_text()), 'EN', role), report)
        return {str(p.relative_to(self.root)): p.read_bytes() for p in (rom, receipt)}

    def test_accept_refuses_coherent_candidate_substitution_before_journal(self):
        from .test_build import synthetic_ui
        self.ui_setup(); first = self.ui_build(); accept_checked(self.config, self.ui_evidence(first))
        self.ui_build(); accept_checked(self.config, self.ui_evidence(first))
        other = self.ui_build('IT'); accept_checked(self.config, self.ui_evidence(other))
        result = self.ui_build(); before = self.snapshot(); calls = 0; injected = {}
        def substitute(*args, **kwargs):
            nonlocal calls, injected
            verified = synthetic_ui(*args, **kwargs); calls += 1
            if calls == 1: injected = self.coherent_historical_substitution(result)
            return verified
        with patch('sgp131.ui_verify.verify', side_effect=substitute):
            with self.assertRaisesRegex(ValueError, 'historical|role|precondition|identity'):
                accept_checked(self.config, self.ui_evidence(result))
        after = self.snapshot()
        self.assertEqual(after, {**before, **injected})
        self.assertFalse((self.root / 'journal.json').exists())
        self.assertFalse(any(self.root.glob('.txn-*')))

    def test_accept_refuses_candidate_appearing_during_pending_admission(self):
        from .test_build import synthetic_ui
        self.ui_setup(); result = self.ui_build(); before = self.snapshot(); injected = {}; calls = 0
        def appear(*args, **kwargs):
            nonlocal calls, injected
            verified = synthetic_ui(*args, **kwargs); calls += 1
            if calls == 1: injected = self.coherent_historical_substitution(result)
            return verified
        with patch('sgp131.ui_verify.verify', side_effect=appear):
            with self.assertRaisesRegex(ValueError, 'historical|role|precondition|identity'):
                accept_checked(self.config, self.ui_evidence(result))
        self.assertEqual(self.snapshot(), {**before, **injected})
        self.assertFalse((self.root / 'journal.json').exists())
        self.assertFalse(any(self.root.glob('.txn-*')))

    def test_accept_refuses_fallback_appearing_during_transaction_admission(self):
        from .test_build import synthetic_ui
        self.ui_setup(); first = self.ui_build(); accept_checked(self.config, self.ui_evidence(first))
        result = self.ui_build(); before = self.snapshot(); injected = {}; calls = 0
        def appear(*args, **kwargs):
            nonlocal calls, injected
            verified = synthetic_ui(*args, **kwargs); calls += 1
            if calls == 2: injected = self.coherent_historical_substitution(result, 'fallback')
            return verified
        with patch('sgp131.ui_verify.verify', side_effect=appear):
            with self.assertRaisesRegex(ValueError, 'historical|role|precondition|identity'):
                accept_checked(self.config, self.ui_evidence(result))
        self.assertEqual(self.snapshot(), {**before, **injected})
        self.assertFalse((self.root / 'journal.json').exists())
        self.assertFalse(any(self.root.glob('.txn-*')))


    def test_accept_rechecks_captured_identity_after_prepared_journal_admission(self):
        from .test_build import synthetic_ui
        self.ui_setup(); first = self.ui_build(); accept_checked(self.config, self.ui_evidence(first))
        self.ui_build(); accept_checked(self.config, self.ui_evidence(first))
        result = self.ui_build()
        before = {str(p.relative_to(self.root)): p.read_bytes() for folder in ('EN', 'IT')
                  for p in (self.root / folder).iterdir() if p.is_file()}
        candidate = self.root / 'EN/candidate.nds'; original_inode = candidate.stat().st_ino
        calls = 0; injected_inode = None
        def replace_same_bytes(*args, **kwargs):
            nonlocal calls, injected_inode
            verified = synthetic_ui(*args, **kwargs); calls += 1
            if calls == 3:
                for suffix in ('nds', 'json'):
                    path = self.root / 'EN' / ('candidate.' + suffix)
                    data = path.read_bytes(); path.unlink(); path.write_bytes(data)
                injected_inode = candidate.stat().st_ino
            return verified
        with patch('sgp131.ui_verify.verify', side_effect=replace_same_bytes):
            with self.assertRaisesRegex(ValueError, 'historical|role|identity'):
                accept_checked(self.config, self.ui_evidence(result))
        self.assertIsNotNone(injected_inode)
        self.assertNotEqual(injected_inode, original_inode)
        # The external injection replaced inodes only. No role bytes were
        # changed by the workbench; prepared recovery retains its snapshots.
        self.assertEqual({str(p.relative_to(self.root)): p.read_bytes() for folder in ('EN', 'IT')
                          for p in (self.root / folder).iterdir() if p.is_file()}, before)
        self.assertEqual(candidate.stat().st_ino, injected_inode)
        self.assertTrue((self.root / 'journal.json').exists())
        self.assertTrue(any(self.root.glob('.txn-*')))
