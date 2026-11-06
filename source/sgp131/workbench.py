"""Private bounded successor workbench; baseline and UI composition, no emulator launcher.

build writes pending; only accept rotates verified candidate into fallback.
A prepared journal owns hardlink snapshots until every ROM/receipt pair has
been fsynced and checked. Interrupted transactions block use until recover.
Consumers must claim/release a lease around their owned emulator session; the
bench never terminates a process. Original baselines are read-only references.
"""
import argparse
from contextlib import contextmanager
import ctypes
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import uuid

from . import activation, baseline, build, evidence
from sgp13 import admission

MIN_FREE = 10 * 1024 ** 3
LANGUAGES = ('EN', 'IT')
SLOTS = ('candidate', 'fallback', 'pending')
SLOT_FILES = {f'{language}/{slot}.{suffix}' for language in LANGUAGES
              for slot in SLOTS for suffix in ('nds', 'json')}
ACCEPTANCE_LIMIT = 4 * 1024 * 1024
CONSUMERS_LIMIT = 1024 * 1024


def _json(data):
    return (json.dumps(data, sort_keys=True, indent=2) + '\n').encode()


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _hash_file(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def _no_symlink(path):
    path = Path(path).absolute()
    for part in (path, *path.parents):
        if part.is_symlink():
            raise ValueError('symlink is not a managed path: ' + str(part))
    return path


def _fsync_dir(path):
    fd = os.open(path, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _managed_dir_fd(config, relative='.'):
    current = os.dup(config['_root_fd'])
    try:
        for component in Path(relative).parts:
            if component in ('', '.'):
                continue
            if component == '..':
                raise ValueError('managed directory escapes root')
            child = os.open(component, os.O_RDONLY | os.O_DIRECTORY |
                            getattr(os, 'O_NOFOLLOW', 0), dir_fd=current)
            os.close(current)
            current = child
        _require_private_fd(current, directory=True)
        return current
    except Exception:
        os.close(current)
        raise


def _require_private_fd(fd, *, directory):
    info = os.fstat(fd)
    expected = stat.S_ISDIR if directory else stat.S_ISREG
    if not expected(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
        raise ValueError('private managed descriptor has unsafe owner or permissions')
    return info


def _open_file_at(directory_fd, name):
    fd = os.open(name, os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0), dir_fd=directory_fd)
    try:
        _require_private_fd(fd, directory=False)
        if os.fstat(fd).st_nlink < 1:
            raise ValueError('managed file has invalid link count')
        return fd
    except Exception:
        os.close(fd)
        raise


def _hash_at(directory_fd, name):
    fd = _open_file_at(directory_fd, name)
    try:
        digest = hashlib.sha256()
        for chunk in iter(lambda: os.read(fd, 1024 * 1024), b''):
            digest.update(chunk)
        return digest.hexdigest()
    finally:
        os.close(fd)


def _file_identity_at(directory_fd, name):
    fd = _open_file_at(directory_fd, name)
    try:
        before = os.fstat(fd)
        digest = hashlib.sha256()
        for chunk in iter(lambda: os.read(fd, 1024 * 1024), b''):
            digest.update(chunk)
        after = os.fstat(fd)
        identity = lambda value: (value.st_dev, value.st_ino, value.st_size)
        if identity(before) != identity(after):
            raise ValueError('managed file identity changed during capture')
        return {'device': after.st_dev, 'inode': after.st_ino,
                'bytes': after.st_size, 'sha256': digest.hexdigest()}
    finally:
        os.close(fd)


def _read_at(directory_fd, name, limit):
    fd = _open_file_at(directory_fd, name)
    try:
        info = os.fstat(fd)
        if info.st_size < 0 or info.st_size > limit:
            raise ValueError('managed metadata size limit')
        data = bytearray()
        while len(data) < info.st_size:
            chunk = os.read(fd, info.st_size - len(data))
            if not chunk:
                raise ValueError('managed metadata short read')
            data.extend(chunk)
        if os.read(fd, 1):
            raise ValueError('managed metadata grew')
        return bytes(data)
    finally:
        os.close(fd)


def _require_private(path, *, directory):
    info = os.stat(path, follow_symlinks=False)
    expected = stat.S_ISDIR if directory else stat.S_ISREG
    if not expected(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
        kind = 'directory' if directory else 'file'
        raise ValueError('private managed %s has unsafe owner or permissions: %s' % (kind, path))
    return info


def _identity(info):
    return {'device': info.st_dev, 'inode': info.st_ino}


def _require_root_identity(config, fd=None):
    expected = config.get('root_identity')
    if (not isinstance(expected, dict) or set(expected) != {'device', 'inode'}
            or type(expected['device']) is not int or type(expected['inode']) is not int):
        raise ValueError('workbench root identity is absent or malformed')
    info = os.fstat(fd) if fd is not None else _require_private(config['root'], directory=True)
    if _identity(info) != expected:
        raise ValueError('workbench root identity changed')
    return info


def _require_lock_identity(config, info):
    expected = config.get('lock_identity')
    if (not isinstance(expected, dict) or set(expected) != {'device', 'inode'}
            or type(expected['device']) is not int or type(expected['inode']) is not int
            or _identity(info) != expected):
        raise ValueError('workbench lock identity changed')


def _require_scratch_identity(config, fd=None):
    expected = config.get('scratch_identity')
    if (not isinstance(expected, dict) or set(expected) != {'device', 'inode'}
            or type(expected['device']) is not int or type(expected['inode']) is not int):
        raise ValueError('workbench scratch identity is absent or malformed')
    info = os.fstat(fd) if fd is not None else _require_private(config['scratch'], directory=True)
    if _identity(info) != expected:
        raise ValueError('workbench scratch identity changed')
    return info


def _mkdir_private(path):
    path = Path(path)
    path.mkdir(mode=0o700)
    os.chmod(path, 0o700)
    _require_private(path, directory=True)


def _write_new(path, data):
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, 'O_NOFOLLOW', 0)
    fd = os.open(path, flags, 0o600)
    try:
        os.fchmod(fd, 0o600)
        view = memoryview(data)
        while view:
            written = os.write(fd, view)
            if written <= 0:
                raise OSError('short private metadata write')
            view = view[written:]
        os.fsync(fd)
    finally:
        os.close(fd)
    _require_private(path, directory=False)
    _fsync_dir(Path(path).parent)


def _write_new_at(directory_fd, name, data):
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, 'O_NOFOLLOW', 0)
    fd = os.open(name, flags, 0o600, dir_fd=directory_fd)
    try:
        os.fchmod(fd, 0o600)
        view = memoryview(data)
        while view:
            written = os.write(fd, view)
            if written <= 0:
                raise OSError('short private metadata write')
            view = view[written:]
        os.fsync(fd)
        _require_private_fd(fd, directory=False)
    finally:
        os.close(fd)


def _atomic_json_at(directory_fd, name, data, *, replace):
    temporary = '.metadata-' + uuid.uuid4().hex
    _write_new_at(directory_fd, temporary, _json(data))
    try:
        if replace:
            os.replace(temporary, name, src_dir_fd=directory_fd, dst_dir_fd=directory_fd)
        else:
            os.link(temporary, name, src_dir_fd=directory_fd,
                    dst_dir_fd=directory_fd, follow_symlinks=False)
            os.unlink(temporary, dir_fd=directory_fd)
        os.fsync(directory_fd)
    finally:
        try:
            os.unlink(temporary, dir_fd=directory_fd)
        except FileNotFoundError:
            pass


def _exists_at(directory_fd, name):
    try:
        os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
        return True
    except FileNotFoundError:
        return False


def _atomic_json(path, data):
    path = _no_symlink(path)
    temporary = path.parent / ('.metadata-' + uuid.uuid4().hex)
    try:
        _write_new(temporary, _json(data))
        os.replace(temporary, path)
        _fsync_dir(path.parent)
    finally:
        temporary.unlink(missing_ok=True)


def _alive(pid, identity=None):
    if type(pid) is not int or pid <= 0:
        raise ValueError('invalid lock/consumer PID')
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        pass
    if identity is not None:
        current = _process_identity(pid)
        return True if current is None else current == identity
    return True


def _process_identity(pid):
    if type(pid) is not int or pid <= 0:
        raise ValueError('invalid process PID')
    proc = Path('/proc') / str(pid)
    if proc.exists():
        try:
            raw = (proc / 'stat').read_text()
            fields = raw[raw.rfind(')') + 2:].split()
            start = fields[19]
            boot = Path('/proc/sys/kernel/random/boot_id').read_text().strip()
            return 'linux:%s:%s' % (boot, start)
        except (OSError, IndexError, ValueError):
            return None
    if sys.platform == 'darwin':
        class ProcBsdInfo(ctypes.Structure):
            _fields_ = [
                ('words', ctypes.c_uint32 * 12),
                ('comm', ctypes.c_char * 16),
                ('name', ctypes.c_char * 32),
                ('tail_words', ctypes.c_uint32 * 6),
                ('start_sec', ctypes.c_uint64),
                ('start_usec', ctypes.c_uint64),
            ]
        try:
            library = ctypes.CDLL('/usr/lib/libproc.dylib')
            info = ProcBsdInfo()
            size = library.proc_pidinfo(pid, 3, 0, ctypes.byref(info), ctypes.sizeof(info))
            if size == ctypes.sizeof(info):
                return 'darwin:%d:%d:%d' % (info.start_sec, info.start_usec, info.words[5])
        except (OSError, AttributeError):
            return None
    try:
        result = subprocess.run(
            ['/bin/ps', '-o', 'lstart=', '-o', 'uid=', '-p', str(pid)],
            text=True, capture_output=True, timeout=2, check=False)
    except (OSError, subprocess.SubprocessError):
        return None
    value = ' '.join(result.stdout.split())
    return 'posix:' + value if result.returncode == 0 and value else None


def _load(config_path):
    config_path = _no_symlink(config_path)
    _require_private(config_path, directory=False)
    config = json.loads(config_path.read_text())
    if (config.get('schema') != 1 or not re.fullmatch('[0-9a-f]{32}', str(config.get('id', '')))
            or set(config.get('bases', {})) != set(LANGUAGES)):
        raise ValueError('invalid workbench configuration')
    root = _no_symlink(config['root'])
    _require_private(root, directory=True)
    _require_root_identity(config)
    marker = _no_symlink(root / '.owner.json')
    _require_private(marker, directory=False)
    if json.loads(marker.read_text()) != {'schema': 1, 'id': config['id']}:
        raise ValueError('workbench ownership mismatch')
    _require_lock_identity(config, _require_private(root / '.lock', directory=False))
    scratch = _no_symlink(config['scratch'])
    _require_private(scratch, directory=True)
    _require_scratch_identity(config)
    config['scratch'] = str(scratch)
    config['root'] = str(root)
    _guard_paths(config)
    return config


def _guard_paths(config):
    root = Path(config['root'])
    _require_private(root, directory=True)
    _require_root_identity(config)
    originals = [_no_symlink(config['bases'][language]['path']) for language in LANGUAGES]
    if originals[0] == originals[1] or (all(p.exists() for p in originals) and os.path.samefile(*originals)):
        raise ValueError('input alias between languages')
    for original in originals:
        if original == root or root in original.parents:
            raise ValueError('input must be outside workbench root')
    for name in (*SLOT_FILES, '.owner.json', '.lock', 'journal.json', 'consumers.json'):
        path = _no_symlink(root / name)
        if path.exists():
            if not path.is_file():
                raise ValueError('managed file path is not a file: ' + name)
            _require_private(path, directory=False)
            if any(original.exists() and os.path.samefile(path, original) for original in originals):
                raise ValueError('input/output hardlink alias')
    for language in LANGUAGES:
        folder = _no_symlink(root / language)
        _require_private(folder, directory=True)


@contextmanager
def _locked(config_path):
    config = _load(config_path)
    root_flags = os.O_RDONLY | os.O_DIRECTORY | getattr(os, 'O_NOFOLLOW', 0)
    root_fd = os.open(config['root'], root_flags)
    scratch_fd = -1
    try:
        _require_root_identity(config, root_fd)
        scratch_fd = os.open(config['scratch'], root_flags)
        _require_scratch_identity(config, scratch_fd)
        fd = os.open('.lock', os.O_RDWR | os.O_NOFOLLOW, 0o600,
                     dir_fd=root_fd)
    except Exception:
        if scratch_fd >= 0:
            os.close(scratch_fd)
        os.close(root_fd)
        raise
    try:
        os.fchmod(fd, 0o600)
        info = os.fstat(fd)
        _require_lock_identity(config, info)
        if info.st_uid != os.getuid() or info.st_mode & 0o077:
            raise ValueError('workbench lock is not private')
        if os.fstat(fd).st_nlink != 1:
            raise ValueError('lock file alias')
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise ValueError('another workbench writer holds the lock') from None
        owns_metadata = False
        try:
            # flock, not stale PID metadata, is the ownership authority. Once
            # this descriptor owns the flock, any old payload is reclaimable.
            os.read(fd, 4096)
            os.lseek(fd, 0, os.SEEK_SET)
            os.ftruncate(fd, 0)
            os.write(fd, _json({'pid': os.getpid(), 'session': uuid.uuid4().hex}))
            owns_metadata = True
            os.fsync(fd)
            config['_root_fd'] = root_fd
            config['_scratch_fd'] = scratch_fd
            _consumers(config)  # Malformed persisted leases never imply idle state.
            yield config
        finally:
            # A refused live metadata lock is preserved, even if flock itself
            # was released unexpectedly by its owner.
            if owns_metadata:
                os.ftruncate(fd, 0)
                os.fsync(fd)
            config.pop('_root_fd', None)
            config.pop('_scratch_fd', None)
            fcntl.flock(fd, fcntl.LOCK_UN)
    finally:
        os.close(fd)
        os.close(scratch_fd)
        os.close(root_fd)


def initialize(config_path: Path, bases: dict[str, Path], root: Path) -> dict:
    root, config_path = _no_symlink(root), _no_symlink(config_path)
    if set(bases) != set(LANGUAGES):
        raise ValueError('both EN and IT inputs are required')
    records = {}
    for language in LANGUAGES:
        path = _no_symlink(bases[language])
        if root == path or root in path.parents or config_path == path:
            raise ValueError('input/output alias or input inside workbench')
        data, observed_language, digest = admission.read_contract(
            path, baseline.input_contracts(), 'V1.3 V4 ROM')
        if observed_language != language:
            raise ValueError('input language mismatch')
        records[language] = {'path': str(path), 'sha256': digest, 'bytes': len(data)}
    if os.path.samefile(records['EN']['path'], records['IT']['path']):
        raise ValueError('input alias between languages')
    if config_path.exists() or root.exists():
        raise FileExistsError('initialization requires a new private workbench root and config')
    if root not in config_path.parents:
        raise ValueError('config must be inside the private workbench root')
    config = {'schema': 1, 'id': uuid.uuid4().hex, 'root': str(root), 'bases': records}
    scratch = root.parent / ('.sgp131-scratch-' + config['id'])
    if scratch.exists() or scratch.is_symlink():
        raise FileExistsError('initialization requires a new private scratch anchor')
    _mkdir_private(scratch)
    config['scratch'] = str(scratch)
    config['scratch_identity'] = _identity(_require_private(scratch, directory=True))
    root.mkdir(parents=True, mode=0o700)
    os.chmod(root, 0o700)
    config['root_identity'] = _identity(_require_private(root, directory=True))
    for language in LANGUAGES:
        _mkdir_private(root / language)
    _write_new(root / '.owner.json', _json({'schema': 1, 'id': config['id']}))
    _write_new(root / '.lock', b'')
    config['lock_identity'] = _identity(_require_private(root / '.lock', directory=False))
    current = root
    relative_parent = config_path.parent.relative_to(root)
    for part in relative_parent.parts:
        current = current / part
        if not current.exists():
            _mkdir_private(current)
        else:
            _require_private(current, directory=True)
    _write_new(config_path, _json(config))
    _fsync_dir(root.parent)
    return config


def _base(config, language):
    record = config['bases'][language]
    path = Path(record['path'])
    contracts = baseline.input_contracts()
    if (record.get('sha256') not in contracts
            or contracts[record['sha256']] != (language, record.get('bytes'))):
        raise ValueError('input must be an exact supported immutable size')
    data, observed_language, digest = admission.read_contract(
        path, contracts, 'V1.3 V4 ROM')
    if observed_language != language:
        raise ValueError('input language mismatch')
    if digest != record['sha256'] or len(data) != record['bytes']:
        raise ValueError('immutable input hash or size changed')
    return data


def _validate_receipt(config, report, language, status):
    if (not isinstance(report, dict) or report.get('schema') not in (1, 2)
            or report.get('workbench_id') != config['id']
            or report.get('language') != language or report.get('status') != status):
        raise ValueError('unowned or incoherent ROM/receipt pair')
    evidence.validate_provenance(report)
    if len(_json(report)) > build.RECEIPT_LIMIT:
        raise ValueError('serialized receipt size limit')
    # Baseline authorizes exactly zero changed bytes. Validate trusted identity
    # even for a self-consistent but edited ROM/report, before use or recovery.
    digest = config['bases'][language]['sha256']
    if (baseline.INPUT_HASHES.get(digest) != language
            or report.get('input_sha256') != digest
            or (report['through'] == 'baseline' and report.get('output_sha256') != digest)):
        raise ValueError('baseline identity hash mismatch')
    if report['through'] in build.UI_CHAIN and report['receipts'][0]['input_bytes'] != config['bases'][language]['bytes']:
        raise ValueError('UI input size identity mismatch')
    if report.get('required_cases') != list(build.REQUIRED_CASES[report['through']]):
        raise ValueError('receipt mandatory acceptance cases changed')
    if status == 'accepted':
        acceptance = report.get('acceptance')
        evidence.validate_acceptance(acceptance, report['output_sha256'], provenance=report)
        if acceptance['through'] != report['through']:
            raise ValueError('receipt acceptance stage mismatch')


def _ui_input_paths(config, inputs):
    root = Path(config['root'])
    managed = [root / name for name in SLOT_FILES]
    originals = [Path(v['path']) for v in config['bases'].values()]
    paths = [Path(record['path']) for record in inputs['records'].values()]
    for path in paths:
        if path == root or root in path.parents:
            raise ValueError('UI input must be outside workbench root')
        if any(other.exists() and os.path.samefile(path, other) for other in (*managed, *originals)):
            raise ValueError('UI input/output alias')
    for index, path in enumerate(paths):
        if any(os.path.samefile(path, other) for other in paths[:index]):
            raise ValueError('UI input alias')


def _mechanics_options(config, language, report, ui_inputs):
    present = {'mechanics_inputs', 'mechanics_options_sha256', 'activation'} & set(report)
    if not present:
        return None
    if present != {'mechanics_inputs', 'mechanics_options_sha256', 'activation'}:
        raise ValueError('mechanics input record required for publication')
    options, record = activation.snapshot_config(report['mechanics_inputs']['path'])
    if record != report['mechanics_inputs'] or record['options_sha256'] != report['mechanics_options_sha256']:
        raise ValueError('mechanics config identity changed')
    activation.validate_for_chain(options, language, build.mechanics_stages.chain_for(report['through']))
    _ui_input_paths(config, {'records': {**ui_inputs['records'], 'mechanics': record}})
    return options


def _ui_preflight(config, input_bytes, *, output=False):
    # Bound final pending data/receipt plus both journal serializations, owner
    # metadata and scratch before any compiler writes. The fixed compiler's
    # 100 MiB transient bound fits inside the 256 MiB planning reserve.
    sizes = [build.UI_SCRATCH_LIMIT]
    if output:
        sizes += [input_bytes + build.UI_APPEND_LIMIT, build.RECEIPT_LIMIT]
    journal_bound = bytes(build.RECEIPT_LIMIT + 16384)
    return _disk_budget(Path(config['root']), sizes, [journal_bound, journal_bound, bytes(4096)], 6)


@contextmanager
def _managed_scratch(config):
    """Reuse the initialization-pinned private scratch anchor under the writer lock."""
    fd = config['_scratch_fd']
    _require_scratch_identity(config, fd)
    if os.listdir(fd):
        raise ValueError('workbench scratch anchor is not empty')
    previous_cwd = os.open('.', os.O_RDONLY | os.O_DIRECTORY)
    os.fchdir(fd)
    try:
        # Relative paths and every descendant subprocess now resolve from the
        # pinned inode even if its directory entry is renamed or replaced.
        yield Path('.'), fd
    finally:
        build._remove_workspace_contents(fd)
        os.fsync(fd)
        _require_scratch_identity(config, fd)
        os.fchdir(previous_cwd)
        os.close(previous_cwd)


def _admit(config, language, report, payload):
    """Independent admission, live freshness and input identity, never inspect."""
    _validate_receipt(config, report, language, report['status'])
    if len(payload) != report['output_bytes'] or _sha(payload) != report['output_sha256']:
        raise ValueError('admission ROM/receipt hash mismatch')
    data = _base(config, language)
    if report['source_sha256'] != build.source_snapshot():
        raise ValueError('source provenance changed before admission')
    if report['through'] == 'baseline':
        build.verify_composition(data, payload, report['receipts'])
        return
    records = report['ui_inputs']
    inputs = build.snapshot_ui_inputs(records['charmap']['path'], records['ui_config']['path'])
    if inputs['records'] != records:
        raise ValueError('UI consumed input identity changed')
    _ui_input_paths(config, inputs)
    options = _mechanics_options(config, language, report, inputs)
    _ui_preflight(config, len(data))
    with _managed_scratch(config) as (scratch, scratch_fd):
        composition = build.verify_composition(data, payload, report['receipts'], through=report['through'],
                                               ui_inputs=inputs, scratch=scratch, scratch_fd=scratch_fd,
                                               **({'stage_options': options} if options is not None else {}))
    if options is not None:
        gate = activation.final_gate(payload, options, build.owner_receipts(report['receipts']), language=language)
        if gate != report['activation']:
            raise ValueError('mechanics final activation record differs')
        activation.refresh_config(report['mechanics_inputs'], options)
    if composition != report['composition']:
        raise ValueError('independent UI composition mismatch')
    if report['source_sha256'] != build.source_snapshot() or _base(config, language) != data:
        raise ValueError('source/input changed during admission')


def _cleanup_aliases(config, language):
    """Pending deletion cannot unlink a retained role through a hardlink alias."""
    root = Path(config['root'])
    for suffix in ('nds', 'json'):
        pending = _no_symlink(root / language / ('pending.' + suffix))
        if pending.exists():
            for other_language in LANGUAGES:
                for slot in ('candidate', 'fallback'):
                    for other_suffix in ('nds', 'json'):
                        other = _no_symlink(root / other_language / (slot + '.' + other_suffix))
                        if other.exists() and os.path.samefile(pending, other):
                            raise ValueError('pending cleanup aliases accepted role')


def _pair(config, language, slot):
    folder = Path(config['root']) / language
    rom, receipt = folder / (slot + '.nds'), folder / (slot + '.json')
    if not rom.exists() and not receipt.exists():
        return None
    if not rom.is_file() or not receipt.is_file():
        raise ValueError('incoherent ROM/receipt pair; recover required')
    if receipt.stat().st_size > build.RECEIPT_LIMIT:
        raise ValueError('receipt size limit')
    report = json.loads(receipt.read_text())
    _validate_receipt(config, report, language, 'pending' if slot == 'pending' else 'accepted')
    if (rom.stat().st_size != report.get('output_bytes')
            or _hash_file(rom) != report.get('output_sha256')):
        raise ValueError('ROM/receipt pair hash mismatch')
    return report


def _state(config, allow_journal=False):
    _guard_paths(config)
    root = Path(config['root'])
    if not allow_journal:
        if (root / 'journal.json').exists():
            raise ValueError('prepared journal blocks use; run recover')
        if _owned_transactions(config):
            raise ValueError('owned orphan transaction blocks use; run recover')
    return {language: {slot: _pair(config, language, slot) for slot in SLOTS}
            for language in LANGUAGES}


def _consumers(config):
    if '_root_fd' in config:
        if _exists_at(config['_root_fd'], 'consumers.json'):
            info = os.stat('consumers.json', dir_fd=config['_root_fd'], follow_symlinks=False)
            if info.st_nlink != 1:
                raise ValueError('consumer metadata alias')
            leases = json.loads(_read_at(config['_root_fd'], 'consumers.json', CONSUMERS_LIMIT))
        else:
            leases = {}
    else:
        path = Path(config['root']) / 'consumers.json'
        leases = json.loads(path.read_text()) if path.exists() else {}
    if not isinstance(leases, dict):
        raise ValueError('consumer leases must be a map')
    fields = {'session', 'pid', 'process_identity', 'language', 'slot', 'sha256'}
    for session, lease in leases.items():
        if (not isinstance(session, str) or not re.fullmatch('[0-9a-f]{32}', session)
                or not isinstance(lease, dict) or set(lease) != fields
                or lease.get('session') != session or lease.get('language') not in LANGUAGES
                or lease.get('slot') not in SLOTS or type(lease.get('pid')) is not int
                or not 0 < lease['pid'] < 2**31
                or not isinstance(lease.get('process_identity'), str)
                or not lease['process_identity'].startswith(('linux:', 'darwin:', 'posix:'))
                or not isinstance(lease.get('sha256'), str)
                or not re.fullmatch('[0-9a-f]{64}', lease['sha256'])):
            raise ValueError('malformed consumer lease record')
    return leases


def _idle(config, language, slots):
    for lease in _consumers(config).values():
        if (lease['language'] == language and lease['slot'] in slots
                and _alive(lease['pid'], lease['process_identity'])):
            raise ValueError('busy slot: consumer must stop and release its own lease')


def _disk_budget(root, payload_sizes, metadata, entry_count):
    """Additional on-disk peak, excluding already allocated input/slot bytes.

ROM backups and publication links share managed inodes: zero extra data.
Baseline scratch is zero. Round every new data/metadata file to filesystem
    blocks; include both the prepared journal and its atomic-write temporary,
    and one block per link/directory entry created by the transaction. This
    conservatively bounds baseline's actual writes; no caller supplies a peak.
    """
    block = os.statvfs(root).f_frsize
    rounded = lambda size: ((size + block - 1) // block) * block
    planned = sum(rounded(size) for size in payload_sizes)
    planned += sum(rounded(len(item)) for item in metadata)
    # Each data file has one snapshot and one publication link; plus the
    # transaction directory, its ownership marker and the journal entry.
    planned += (2 * entry_count + 3) * block
    free = shutil.disk_usage(root).free
    if free - planned < MIN_FREE:
        raise ValueError('disk budget would leave less than ten GiB free')
    return {'free_bytes': free, 'planned_peak_bytes': planned, 'minimum_free_bytes': MIN_FREE}


def _file_identity(path):
    path = _no_symlink(path)
    if not path.exists():
        return None
    if not path.is_file():
        raise ValueError('historical role path is not a file')
    before = path.stat()
    digest = _hash_file(path)
    after = path.stat()
    identity = lambda value: (value.st_dev, value.st_ino, value.st_size)
    if identity(before) != identity(after):
        raise ValueError('historical role identity changed during capture')
    return {'device': after.st_dev, 'inode': after.st_ino, 'bytes': after.st_size, 'sha256': digest}


def _assert_role_expectations(config, expected):
    root = Path(config['root'])
    for name, identity in expected.items():
        if _file_identity(root / name) != identity:
            raise ValueError('historical role identity/precondition changed: ' + name)


def _capture_accept_roles(config, language, slots):
    root = Path(config['root'])
    expected = {f'{language}/{slot}.{suffix}': _file_identity(root / language / (slot + '.' + suffix))
                for slot in SLOTS for suffix in ('nds', 'json')}
    # Bind the capture to the recorded pairs observed at accept entry. Both
    # file identities and absent roles must survive every later admission.
    for slot in SLOTS:
        if _pair(config, language, slot) != slots[slot]:
            raise ValueError('historical role changed before acceptance capture')
    _assert_role_expectations(config, expected)
    return expected


def _journal(config, writes, deletes, directory, operation, language, receipt, role_expectations=None):
    def before(name):
        if role_expectations is not None:
            identity = role_expectations[name]
            return identity['sha256'] if identity is not None else None
        path = Path(config['root']) / name
        return _hash_file(path) if path.exists() else None

    return {'schema': 1, 'id': config['id'], 'transaction': directory.name,
            'operation': operation, 'language': language,
            'base': dict(config['bases'][language]), 'receipt': receipt,
            'writes': {name: {'source': str(index), 'sha256': digest,
                              'before_sha256': before(name)}
                       for index, (name, digest) in enumerate(writes)},
            'deletes': {name: before(name) for name in deletes}}


def _transaction(config, payloads, deletes=(), before_publish=None, *, operation, language, role_expectations=None):
    root = Path(config['root'])
    root_fd = config['_root_fd']
    if _exists_at(root_fd, 'journal.json'):
        raise ValueError('recover prepared journal before mutation')
    if not set(payloads) <= SLOT_FILES or not set(deletes) <= SLOT_FILES:
        raise ValueError('transaction target outside managed slots')
    if operation == 'accept' and role_expectations is None:
        raise ValueError('accept requires captured historical role identities')
    if role_expectations is not None:
        _assert_role_expectations(config, role_expectations)
    directory = Path('.txn-' + uuid.uuid4().hex)
    marker = {'schema': 1, 'id': config['id'], 'directory': directory.name}
    source_expectations = {}
    writes = []
    for name, value in payloads.items():
        if isinstance(value, bytes):
            digest = _sha(value)
        elif role_expectations is not None:
            identity = role_expectations[str(value.relative_to(root))]
            if identity is None:
                raise ValueError('historical snapshot source was absent at capture')
            source_expectations[name] = identity
            digest = identity['sha256']
        else:
            digest = _hash_file(value)
        writes.append((name, digest))
    if operation == 'discard':
        receipt = json.loads((root / language / 'pending.json').read_text())
    else:
        slot = 'pending' if operation == 'build' else 'candidate'
        value = payloads[f'{language}/{slot}.json']
        receipt = json.loads(value if isinstance(value, bytes) else value.read_bytes())
    _validate_receipt(config, receipt, language, 'accepted' if operation == 'accept' else 'pending')
    if operation == 'discard':
        if _pair(config, language, 'pending') != receipt:
            raise ValueError('pending cleanup receipt changed')
        _cleanup_aliases(config, language)
    else:
        slot = 'pending' if operation == 'build' else 'candidate'
        value = payloads[f'{language}/{slot}.nds']
        _admit(config, language, receipt, value if isinstance(value, bytes) else value.read_bytes())
    if role_expectations is not None:
        _assert_role_expectations(config, role_expectations)
    journal = _journal(config, writes, deletes, directory, operation, language, receipt, role_expectations)
    sizes = [len(value) for value in payloads.values() if isinstance(value, bytes)]
    budget = _disk_budget(root, sizes, [_json(marker), _json(journal), _json(journal)], len(payloads))
    os.mkdir(directory.name, 0o700, dir_fd=root_fd)
    transaction_fd = _managed_dir_fd(config, directory.name)
    transaction_identity = _identity(os.fstat(transaction_fd))
    prepared = False
    try:
        _write_new_at(transaction_fd, 'owner.json', _json(marker))
        for index, (name, value) in enumerate(payloads.items()):
            if isinstance(value, bytes):
                _write_new_at(transaction_fd, str(index), value)
            else:
                value = _no_symlink(value)
                relative = str(value.relative_to(root))
                if relative not in SLOT_FILES:
                    raise ValueError('hardlinks restricted to managed slot backups')
                source_language, leaf = relative.split('/', 1)
                source_fd = _managed_dir_fd(config, source_language)
                try:
                    if name in source_expectations:
                        observed = _file_identity_at(source_fd, leaf)
                        if observed != source_expectations[name]:
                            raise ValueError('historical snapshot identity changed before staging')
                    os.link(leaf, str(index), src_dir_fd=source_fd,
                            dst_dir_fd=transaction_fd, follow_symlinks=False)
                finally:
                    os.close(source_fd)
        os.fsync(transaction_fd)
        _guard_paths(config)
        if before_publish:
            before_publish()
        if role_expectations is not None:
            _assert_role_expectations(config, role_expectations)
            for index, (name, _) in enumerate(writes):
                if (name in source_expectations
                        and _file_identity_at(transaction_fd, str(index)) != source_expectations[name]):
                    raise ValueError('historical snapshot identity changed before journal preparation')
        _atomic_json_at(root_fd, 'journal.json', journal, replace=False)
        prepared = True
        _apply_journal(config, journal, role_expectations=role_expectations)
        return budget
    finally:
        # After journal preparation the snapshots belong to recovery; a failed
        # mutation must never erase the only coherent ROM/receipt source pair.
        if not prepared and not _exists_at(root_fd, 'journal.json'):
            for name in os.listdir(transaction_fd):
                os.unlink(name, dir_fd=transaction_fd)
            os.fsync(transaction_fd)
            try:
                current = os.stat(directory.name, dir_fd=root_fd, follow_symlinks=False)
                if _identity(current) != transaction_identity:
                    raise ValueError('transaction directory identity changed before cleanup')
                os.rmdir(directory.name, dir_fd=root_fd)
                os.fsync(root_fd)
            except FileNotFoundError:
                pass
        os.close(transaction_fd)


def _apply_journal(config, journal, *, role_expectations=None):
    root = Path(config['root'])
    if (journal.get('schema') != 1 or journal.get('id') != config['id']
            or not re.fullmatch(r'\.txn-[0-9a-f]{32}', journal.get('transaction', ''))
            or not set(journal.get('writes', {})) <= SLOT_FILES
            or not set(journal.get('deletes', [])) <= SLOT_FILES):
        raise ValueError('invalid recovery journal')
    language = journal.get('language')
    if language not in LANGUAGES or not isinstance(journal.get('deletes'), dict):
        raise ValueError('invalid recovery transaction language/deletes')
    pair = lambda slot: {f'{language}/{slot}.nds', f'{language}/{slot}.json'}
    writes, deletes = set(journal['writes']), set(journal['deletes'])
    operation = journal.get('operation')
    if not ((operation == 'build' and writes == pair('pending') and not deletes)
            or (operation == 'accept' and writes in (pair('candidate'), pair('candidate') | pair('fallback'))
                and deletes == pair('pending'))
            or (operation == 'discard' and not writes and deletes == pair('pending'))):
        raise ValueError('invalid recovery transaction slot set')
    if journal.get('base') != config['bases'][language]:
        raise ValueError('recovery input metadata changed since transaction preparation')
    _validate_receipt(config, journal.get('receipt'), language,
                      'accepted' if operation == 'accept' else 'pending')
    for name, digest in journal['deletes'].items():
        path = _no_symlink(root / name)
        if not re.fullmatch('[0-9a-f]{64}', str(digest)):
            raise ValueError('invalid recovery deletion hash')
        if path.exists() and _hash_file(path) != digest:
            raise ValueError('recovery deletion hash changed; preserve foreign file')
    directory = _no_symlink(root / journal['transaction'])
    owner = _no_symlink(directory / 'owner.json')
    _require_private(directory, directory=True)
    _require_private(owner, directory=False)
    if json.loads(owner.read_text()) != {'schema': 1, 'id': config['id'], 'directory': directory.name}:
        raise ValueError('recovery directory ownership mismatch')
    for name, entry in journal['writes'].items():
        if (not isinstance(entry, dict) or set(entry) != {'source', 'sha256', 'before_sha256'}
                or not isinstance(entry['source'], str)
                or not isinstance(entry['sha256'], str) or not re.fullmatch('[0-9a-f]{64}', entry['sha256'])
                or (entry['before_sha256'] is not None
                    and (not isinstance(entry['before_sha256'], str)
                         or not re.fullmatch('[0-9a-f]{64}', entry['before_sha256'])))):
            raise ValueError('invalid recovery destination precondition')
        if not re.fullmatch(r'[0-9]+', entry['source']):
            raise ValueError('invalid recovery source')
        source = _no_symlink(directory / entry['source'])
        _require_private(source, directory=False)
        if any(Path(config['bases'][lang]['path']).exists() and os.path.samefile(source, config['bases'][lang]['path'])
               for lang in LANGUAGES):
            raise ValueError('recovery snapshot aliases original input')
        if _hash_file(source) != entry['sha256']:
            raise ValueError('recovery snapshot hash mismatch')
        target = _no_symlink(root / name)
        current = _hash_file(target) if target.exists() else None
        if current not in (entry['before_sha256'], entry['sha256']):
            raise ValueError('recovery destination precondition mismatch; preserve foreign file')
    # Check the desired pairs before changing a live slot. In particular no
    # incomplete journal or caller-edited report may promote a ROM on recovery.
    projected = {}
    for language in LANGUAGES:
        for slot in SLOTS:
            names = [f'{language}/{slot}.{suffix}' for suffix in ('nds', 'json')]
            changed = [name in journal['writes'] for name in names]
            if any(changed) and not all(changed):
                raise ValueError('recovery journal has incomplete pair')
            if all(changed):
                rom_entry, json_entry = (journal['writes'][name] for name in names)
                report = json.loads((directory / json_entry['source']).read_text())
                expected = 'pending' if slot == 'pending' else 'accepted'
                _validate_receipt(config, report, language, expected)
                projected[(language, slot)] = report
                if (report['output_sha256'] != rom_entry['sha256']
                        or report.get('output_bytes') != (directory / rom_entry['source']).stat().st_size):
                    raise ValueError('recovery ROM/receipt mismatch')
    # The same publication gate applies to initial commit and interrupted
    # replay. Preflight every target first, then recheck provenance before ANY
    # replacement or deletion. A stale partial transaction stays blocked with
    # its journal/snapshots intact; it never rolls roles forward or back merely
    # to manufacture consistency. Restore the recorded provenance/preconditions
    # before retrying, or arrange an explicitly reviewed repair outside replay.
    language = journal['language']
    if operation in ('build', 'accept'):
        slot = 'pending' if operation == 'build' else 'candidate'
        report = projected[(language, slot)]
        if report != journal['receipt']:
            raise ValueError('recovery publication receipt provenance mismatch')
        rom_entry = journal['writes'][f'{language}/{slot}.nds']
        _admit(config, language, report, (directory / rom_entry['source']).read_bytes())
    elif operation == 'discard':
        _cleanup_aliases(config, language)
    _idle(config, language, SLOTS if operation == 'accept' else ('pending',))
    # Independent compilation can take time. Recheck every live precondition
    # and exact snapshot after it, before the first publication/deletion.
    _guard_paths(config)
    _require_private(directory, directory=True)
    _require_private(owner, directory=False)
    if json.loads(owner.read_text()) != {'schema': 1, 'id': config['id'], 'directory': directory.name}:
        raise ValueError('recovery directory ownership changed')
    for name, entry in journal['writes'].items():
        source = _no_symlink(directory / entry['source'])
        _require_private(source, directory=False)
        if _hash_file(source) != entry['sha256']:
            raise ValueError('recovery snapshot hash changed after verification')
        target = _no_symlink(root / name)
        current = _hash_file(target) if target.exists() else None
        if current not in (entry['before_sha256'], entry['sha256']):
            raise ValueError('recovery destination precondition changed after verification')
    for name, digest in journal['deletes'].items():
        target = _no_symlink(root / name)
        if target.exists() and _hash_file(target) != digest:
            raise ValueError('recovery deletion hash changed after verification')
    if role_expectations is not None:
        _assert_role_expectations(config, role_expectations)
    # Every mutation below is relative to descriptors pinned by `_locked`.
    # A pathname swap after the last guard can no longer redirect publication.
    _require_root_identity(config, config['_root_fd'])
    transaction_fd = _managed_dir_fd(config, journal['transaction'])
    language_fds = {language: _managed_dir_fd(config, language) for language in LANGUAGES}
    try:
        marker = json.loads(_read_at(transaction_fd, 'owner.json', 4096))
        if marker != {'schema': 1, 'id': config['id'], 'directory': journal['transaction']}:
            raise ValueError('recovery directory ownership changed on pinned descriptor')
        for name, entry in journal['writes'].items():
            if _hash_at(transaction_fd, entry['source']) != entry['sha256']:
                raise ValueError('recovery snapshot changed on pinned descriptor')
            target_language, leaf = name.split('/', 1)
            try:
                current = _hash_at(language_fds[target_language], leaf)
            except FileNotFoundError:
                current = None
            if current not in (entry['before_sha256'], entry['sha256']):
                raise ValueError('recovery destination changed on pinned descriptor')
        for name, digest in journal['deletes'].items():
            target_language, leaf = name.split('/', 1)
            try:
                current = _hash_at(language_fds[target_language], leaf)
            except FileNotFoundError:
                current = None
            if current not in (None, digest):
                raise ValueError('recovery deletion changed on pinned descriptor')
        for name, entry in journal['writes'].items():
            target_language, leaf = name.split('/', 1)
            try:
                os.unlink('publish', dir_fd=transaction_fd)
            except FileNotFoundError:
                pass
            os.link(entry['source'], 'publish', src_dir_fd=transaction_fd,
                    dst_dir_fd=transaction_fd, follow_symlinks=False)
            os.replace('publish', leaf, src_dir_fd=transaction_fd,
                       dst_dir_fd=language_fds[target_language])
            os.fsync(language_fds[target_language])
        for name in journal['deletes']:
            target_language, leaf = name.split('/', 1)
            try:
                os.unlink(leaf, dir_fd=language_fds[target_language])
            except FileNotFoundError:
                pass
            os.fsync(language_fds[target_language])
        _state(config, allow_journal=True)
        os.unlink('journal.json', dir_fd=config['_root_fd'])
        os.fsync(config['_root_fd'])
        for name in os.listdir(transaction_fd):
            os.unlink(name, dir_fd=transaction_fd)
        os.fsync(transaction_fd)
        os.rmdir(journal['transaction'], dir_fd=config['_root_fd'])
        os.fsync(config['_root_fd'])
    finally:
        for fd in language_fds.values():
            os.close(fd)
        os.close(transaction_fd)


def build_candidate(config_path: Path, language: str, through: str, *, charmap=None, ui_config=None,
                    mechanics_config=None, mechanics_config_sha256=None) -> dict:
    if language not in LANGUAGES:
        raise ValueError('language must be EN or IT')
    build.require_stage(through)
    if mechanics_config is not None and through not in build.UI_CHAIN:
        raise ValueError('baseline has no mechanics config')
    if mechanics_config is None:
        if mechanics_config_sha256 is not None:
            raise ValueError('mechanics config hash without config')
        options, mechanics_record = None, None
    else:
        if (not isinstance(mechanics_config_sha256, str)
                or not re.fullmatch('[0-9a-f]{64}', mechanics_config_sha256)):
            raise ValueError('explicit reviewed mechanics config SHA-256 required')
        options, mechanics_record = activation.snapshot_config(mechanics_config)
        if mechanics_record['sha256'] != mechanics_config_sha256:
            raise ValueError('mechanics config differs from explicit reviewed SHA-256')
    activation.validate_for_chain(options, language, build.mechanics_stages.chain_for(through))
    with _locked(config_path) as config:
        state = _state(config)
        if state[language]['pending'] is not None:
            raise ValueError('pending candidate must be accepted or explicitly discarded first')
        _idle(config, language, ('pending',))
        data = _base(config, language)
        sources = build.source_snapshot()
        preflight = None
        if through in build.UI_CHAIN:
            inputs = build.snapshot_ui_inputs(charmap, ui_config)
            _ui_input_paths(config, inputs)
            if mechanics_record is not None:
                _ui_input_paths(config, {'records': {**inputs['records'], 'mechanics': mechanics_record}})
            preflight = _ui_preflight(config, len(data), output=True)
        # Baseline keeps its zero-scratch positional API.
        if through in build.UI_CHAIN:
            with _managed_scratch(config) as (scratch, scratch_fd):
                payload, report = build.compose(data, through, charmap, scratch, ui_config=ui_config,
                                                scratch_fd=scratch_fd,
                                                **({'stage_options': options} if options is not None else {}))
            if mechanics_record is not None:
                report['mechanics_inputs'] = mechanics_record
                if report.get('mechanics_options_sha256') != mechanics_record['options_sha256']:
                    raise ValueError('mechanics options were not consumed')
                activation.refresh_config(mechanics_record, options)
            if report['ui_inputs'] != inputs['records']:
                raise ValueError('UI input changed before composition')
        else:
            payload, report = build.compose(data, through, Path('unused-baseline-charmap'), Path('unused-scratch'))
        report.update({'workbench_id': config['id'], 'status': 'pending'})

        def unchanged():
            if mechanics_record is not None:
                activation.refresh_config(mechanics_record, options)
            if sources != build.source_snapshot() or sources != report['source_sha256']:
                raise ValueError('source changed before publication')
            if _base(config, language) != data:
                raise ValueError('input changed before publication')
            _admit(config, language, report, payload)

        budget = _transaction(config, {f'{language}/pending.nds': payload,
                                       f'{language}/pending.json': _json(report)},
                              before_publish=unchanged, operation='build', language=language)
        return {**report, 'path': str(Path(config['root']) / language / 'pending.nds'),
                'disk_budget': budget, **({'disk_preflight': preflight} if preflight else {})}


def accept(config_path: Path, evidence_path: Path, evidence_sha256: str) -> dict:
    if not isinstance(evidence_sha256, str) or not re.fullmatch('[0-9a-f]{64}', evidence_sha256):
        raise ValueError('explicit reviewed acceptance SHA-256 required')
    with _locked(config_path) as config:
        state = _state(config)
        raw, observed_evidence_sha256 = admission.read_bounded(
            _no_symlink(evidence_path), ACCEPTANCE_LIMIT, 'acceptance JSON')
        if observed_evidence_sha256 != evidence_sha256:
            raise ValueError('acceptance JSON differs from explicit reviewed SHA-256')
        def pairs(items):
            value = {}
            for key, item in items:
                if key in value:
                    raise ValueError('duplicate acceptance JSON key')
                value[key] = item
            return value
        try:
            acceptance = json.loads(raw, object_pairs_hook=pairs)
        except (UnicodeError, RecursionError) as error:
            raise ValueError('malformed acceptance JSON') from error
        digest = acceptance.get('candidate_sha256')
        matches = [language for language in LANGUAGES
                   if state[language]['pending'] and state[language]['pending']['output_sha256'] == digest]
        if len(matches) != 1:
            raise ValueError('evidence hash must identify exactly one pending candidate')
        language = matches[0]
        report = state[language]['pending']
        if acceptance.get('through') != report['through']:
            raise ValueError('acceptance stage mismatch')
        evidence.validate_acceptance(acceptance, digest, provenance=report)
        _idle(config, language, SLOTS)
        role_expectations = _capture_accept_roles(config, language, state[language])
        base = _base(config, language)
        pending = Path(config['root']) / language / 'pending.nds'
        _admit(config, language, report, pending.read_bytes())
        _assert_role_expectations(config, role_expectations)
        if report['source_sha256'] != build.source_snapshot():
            raise ValueError('sources changed since pending build')
        accepted = {**report, 'status': 'accepted', 'acceptance': acceptance,
                    'acceptance_file_sha256': observed_evidence_sha256}
        payloads = {f'{language}/candidate.nds': pending,
                    f'{language}/candidate.json': _json(accepted)}
        if state[language]['candidate']:
            for suffix in ('nds', 'json'):
                payloads[f'{language}/fallback.{suffix}'] = Path(config['root']) / language / ('candidate.' + suffix)

        def unchanged():
            if _base(config, language) != base or _hash_file(pending) != digest:
                raise ValueError('input or pending hash changed before acceptance')
            if report['source_sha256'] != build.source_snapshot():
                raise ValueError('source changed before acceptance')

        _transaction(config, payloads, (f'{language}/pending.nds', f'{language}/pending.json'), unchanged,
                     operation='accept', language=language, role_expectations=role_expectations)
        return {**accepted, 'path': str(Path(config['root']) / language / 'candidate.nds')}


def discard(config_path: Path, language: str) -> dict:
    """Prune only a coherent owned pending pair; retain both verified slots."""
    if language not in LANGUAGES:
        raise ValueError('language must be EN or IT')
    with _locked(config_path) as config:
        state = _state(config)
        if state[language]['pending'] is None:
            raise ValueError('no pending candidate to discard')
        _idle(config, language, ('pending',))
        _transaction(config, {}, (f'{language}/pending.nds', f'{language}/pending.json'),
                     operation='discard', language=language)
        return {'schema': 1, 'language': language, 'discarded_sha256': state[language]['pending']['output_sha256']}


def inspect(config_path: Path) -> dict:
    with _locked(config_path) as config:
        state = _state(config)
        for slots in state.values():
            for report in slots.values():
                if report and report['through'] in build.UI_CHAIN:
                    report['assurance'] = 'recorded-only'
        return {'schema': 1, 'root': config['root'], 'languages': state,
                'original_fallbacks': config['bases'], 'consumers': _consumers(config)}


def _owned_transactions(config):
    owned = []
    root_fd = config['_root_fd']
    for name in os.listdir(root_fd):
        if not re.fullmatch(r'\.txn-[0-9a-f]{32}', name):
            continue
        try:
            directory_fd = _managed_dir_fd(config, name)
        except (FileNotFoundError, NotADirectoryError, OSError, ValueError):
            continue
        try:
            record = json.loads(_read_at(directory_fd, 'owner.json', 4096))
            if record == {'schema': 1, 'id': config['id'], 'directory': name}:
                owned.append(name)
        except (FileNotFoundError, ValueError, UnicodeError):
            pass
        finally:
            os.close(directory_fd)
    return owned


def _remove_owned_transaction(config, name):
    if not re.fullmatch(r'\.txn-[0-9a-f]{32}', name):
        raise ValueError('invalid owned transaction name')
    root_fd = config['_root_fd']
    directory_fd = _managed_dir_fd(config, name)
    try:
        directory_identity = _identity(os.fstat(directory_fd))
        marker = json.loads(_read_at(directory_fd, 'owner.json', 4096))
        if marker != {'schema': 1, 'id': config['id'], 'directory': name}:
            raise ValueError('transaction ownership changed before cleanup')
        entries = os.listdir(directory_fd)
        if any(not re.fullmatch(r'(?:owner\.json|publish|[0-9]+)', entry)
               for entry in entries):
            raise ValueError('owned transaction contains unrecognized data; preserve it')
        for entry in entries:
            info = os.stat(entry, dir_fd=directory_fd, follow_symlinks=False)
            if (not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid()
                    or info.st_mode & 0o077):
                raise ValueError('owned transaction entry is unsafe; preserve it')
        current = os.stat(name, dir_fd=root_fd, follow_symlinks=False)
        if _identity(current) != directory_identity:
            raise ValueError('transaction directory identity changed before cleanup')
        for entry in entries:
            os.unlink(entry, dir_fd=directory_fd)
        os.fsync(directory_fd)
        current = os.stat(name, dir_fd=root_fd, follow_symlinks=False)
        if _identity(current) != directory_identity:
            raise ValueError('transaction directory identity changed during cleanup')
        os.rmdir(name, dir_fd=root_fd)
        os.fsync(root_fd)
    finally:
        os.close(directory_fd)


def recover(config_path: Path) -> dict:
    with _locked(config_path) as config:
        if _exists_at(config['_root_fd'], 'journal.json'):
            record = json.loads(_read_at(config['_root_fd'], 'journal.json', ACCEPTANCE_LIMIT))
            for language in LANGUAGES:
                _idle(config, language, SLOTS)
            _apply_journal(config, record)
        for name in _owned_transactions(config):
            _remove_owned_transaction(config, name)
        os.fsync(config['_root_fd'])
        return {'schema': 1, 'languages': _state(config), 'recovered': True}


def claim_consumer(config_path, language, slot, pid):
    """Verify exact bytes immediately before an owned consumer starts using them.

The caller must keep this lease until its process has stopped using the slot.
    This cooperative guard deliberately does not discover or kill other chats'
    processes. Every new launch must claim again, including after a restart.
    """
    identity = _process_identity(pid)
    if language not in LANGUAGES or slot not in SLOTS or not _alive(pid) or identity is None:
        raise ValueError('invalid or inactive consumer')
    with _locked(config_path) as config:
        state = _state(config)
        report = state[language][slot]
        if report is None:
            raise ValueError('consumer slot is empty')
        if report['through'] in build.UI_CHAIN:
            _admit(config, language, report, (Path(config['root']) / language / (slot + '.nds')).read_bytes())
            _guard_paths(config)
            if _pair(config, language, slot) != report:
                raise ValueError('consumer pair changed after admission')
        leases = _consumers(config)
        session = uuid.uuid4().hex
        lease = {'session': session, 'pid': pid, 'process_identity': identity,
                 'language': language, 'slot': slot,
                 'sha256': report['output_sha256']}
        consumers_existed = _exists_at(config['_root_fd'], 'consumers.json')
        previous_leases = dict(leases)
        leases[session] = lease
        _atomic_json_at(config['_root_fd'], 'consumers.json', leases, replace=True)
        try:
            _require_root_identity(config)
        except Exception:
            if consumers_existed:
                _atomic_json_at(config['_root_fd'], 'consumers.json', previous_leases, replace=True)
            else:
                os.unlink('consumers.json', dir_fd=config['_root_fd'])
                os.fsync(config['_root_fd'])
            raise
        return {**lease, 'path': str(Path(config['root']) / language / (slot + '.nds'))}


def release_consumer(config_path, language, session):
    with _locked(config_path) as config:
        leases = _consumers(config)
        lease = leases.get(session)
        if (not lease or lease['language'] != language or lease['pid'] != os.getpid()
                or lease['process_identity'] != _process_identity(os.getpid())):
            raise ValueError('only the owning session/process may release a consumer')
        del leases[session]
        _atomic_json_at(config['_root_fd'], 'consumers.json', leases, replace=True)
        _require_root_identity(config)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    for command in ('init', 'inspect', 'build', 'accept', 'recover', 'discard'):
        item = sub.add_parser(command)
        item.add_argument('--config', required=True, type=Path)
        if command == 'init':
            item.add_argument('--base-en', required=True, type=Path)
            item.add_argument('--base-it', required=True, type=Path)
            item.add_argument('--root', required=True, type=Path)
        elif command == 'build':
            item.add_argument('--language', required=True, choices=LANGUAGES)
            item.add_argument('--through', required=True, choices=build.STAGES)
            item.add_argument('--charmap', type=Path)
            item.add_argument('--ui-config', type=Path)
            item.add_argument('--mechanics-config', type=Path)
            item.add_argument('--mechanics-config-sha256')
        elif command == 'discard':
            item.add_argument('--language', required=True, choices=LANGUAGES)
        elif command == 'accept':
            item.add_argument('--evidence', required=True, type=Path)
            item.add_argument('--evidence-sha256', required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == 'init':
            result = initialize(args.config, {'EN': args.base_en, 'IT': args.base_it}, args.root)
        elif args.command == 'build':
            result = build_candidate(args.config, args.language, args.through, charmap=args.charmap,
                                     ui_config=args.ui_config, mechanics_config=args.mechanics_config,
                                     mechanics_config_sha256=args.mechanics_config_sha256)
        elif args.command == 'discard':
            result = discard(args.config, args.language)
        elif args.command == 'accept':
            result = accept(args.config, args.evidence, args.evidence_sha256)
        else:
            result = {'inspect': inspect, 'recover': recover}[args.command](args.config)
    except (ValueError, OSError, KeyError, TypeError) as exc:
        parser.exit(1, str(exc) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
