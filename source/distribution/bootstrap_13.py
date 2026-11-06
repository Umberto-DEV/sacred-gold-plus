#!/usr/bin/env python3
"""Reconstruct the historical HF01 V1.3 V4 input from authenticated public sources.

Only the pinned, already-published commit is read. No fetch, branch, checkout,
worktree, ref update, game update or save operation is performed. HF01 is a
build intermediate; the current sgp131 composer upgrades it to HF02.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import signal
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
MANIFEST = HERE / 'bootstrap-13-v4.json'
MANIFEST_SHA256 = '9ca6f2413492f955e8b5a5d3f30ed8f3a54f78e629285801b68227832a95e7c3'
PUBLISHED_COMMIT = 'd2bb1f24dad5f88d39325089cf461643d5f99a1a'
PYTHON_VERSION = '3.14.7'
PYTHON_SHA256 = '87d4df53fd91304be5bac391fb204643c36b7df2023c04a0953bcbc7d4fdf634'
SPACE_FLOOR = 10 * 1024**3
PEAK_BUDGET = 4 * 1024**3


def digest(path):
    result = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for part in iter(lambda: stream.read(1024 * 1024), b''):
            result.update(part)
    return result.hexdigest()


def need(condition, reason):
    if not condition:
        raise ValueError(reason)


def load_manifest():
    raw = MANIFEST.read_bytes()
    need(hashlib.sha256(raw).hexdigest() == MANIFEST_SHA256, 'bootstrap manifest changed')
    document = json.loads(raw)
    need(document['schema'] == 1 and document['source_commit'] == PUBLISHED_COMMIT,
         'unsupported historical source identity')
    need(document['core_source_count'] == len(document['files']) == 208, 'historical source count')
    entries = {**document['files'], **document['additional_dependencies']}
    need(len(entries) == len(document['files']) + len(document['additional_dependencies']), 'duplicate source path')
    need(sum(x['bytes'] for x in entries.values()) <= 8 * 1024**2, 'source byte budget')
    for name, info in entries.items():
        path = PurePosixPath(name)
        need(not path.is_absolute() and str(path) == name and '\\' not in name
             and all(part not in ('.', '..') and not part.startswith('.') for part in path.parts),
             'invalid staged source path')
        need(path.suffix in ('.py', '.c', '.h', '.json', '.bin')
             and 0 < info['bytes'] <= 2 * 1024**2
             and re.fullmatch('[0-9a-f]{64}', info['sha256'])
             and re.fullmatch('[0-9a-f]{40}', info['git_blob']), 'invalid staged source pin')
        need(path.name.lower() not in ('agents.md', 'claude.md', 'skill.md'), 'assistant source refused')
    return document, entries


def git_bytes(repository, arguments, limit):
    env = {key: value for key, value in os.environ.items() if not key.startswith('GIT_')}
    env.update(GIT_NO_REPLACE_OBJECTS='1', GIT_NO_LAZY_FETCH='1', GIT_CONFIG_NOSYSTEM='1',
               GIT_CONFIG_GLOBAL=os.devnull, LC_ALL='C')
    result = subprocess.run(['git', '-C', str(repository), '-c', 'core.fsmonitor=false',
                             '-c', 'protocol.allow=never', *arguments],
                            env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
    need(result.returncode == 0, 'pinned Git object unavailable; use a complete repository with the published ancestor')
    need(len(result.stdout) <= limit, 'Git object exceeds its pinned byte bound')
    return result.stdout


def new_path(path):
    path = Path(path).absolute()
    need(not os.path.lexists(path), 'output already exists; choose a new path')
    need(path.parent.is_dir(), 'output parent must already exist')
    return path.parent.resolve() / path.name


def source_payloads(repository):
    document, entries = load_manifest()
    raw_commit = git_bytes(repository, ['cat-file', 'commit', PUBLISHED_COMMIT], 1024 * 1024)
    need(hashlib.sha1(b'commit ' + str(len(raw_commit)).encode() + b'\0' + raw_commit).hexdigest()
         == PUBLISHED_COMMIT, 'published commit object identity')
    payloads = {}
    for name, info in sorted(entries.items()):
        object_name = PUBLISHED_COMMIT + ':source/' + name
        size = git_bytes(repository, ['cat-file', '-s', object_name], 32)
        need(size.strip() == str(info['bytes']).encode(), 'published source size differs: ' + name)
        raw = git_bytes(repository, ['cat-file', 'blob', object_name], info['bytes'])
        oid = hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()
        need(len(raw) == info['bytes'] and oid == info['git_blob']
             and hashlib.sha256(raw).hexdigest() == info['sha256'], 'published source identity differs: ' + name)
        payloads[name] = raw
    return document, entries, payloads


def stage_sources(repository, destination):
    destination = new_path(destination)
    document, entries, payloads = source_payloads(repository)
    destination.mkdir(mode=0o700)
    try:
        for name, raw in payloads.items():
            target = destination / 'source' / name
            target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
            with target.open('xb') as stream:
                stream.write(raw)
            target.chmod(0o400)
        receipt = {'schema': 1, 'source_commit': PUBLISHED_COMMIT,
                   'manifest_sha256': MANIFEST_SHA256, 'files': entries,
                   'core_source_count': document['core_source_count'],
                   'scope': 'Verified published source staging only; no ROM build or runtime acceptance'}
        (destination / 'source-receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    except BaseException:
        shutil.rmtree(destination)
        raise
    return document, receipt


def authenticate_file(path, contract, label):
    path = Path(path).resolve(strict=True)
    need(path.is_file() and path.stat().st_size == contract['bytes']
         and digest(path) == contract['sha256'], label + ' identity differs')
    return path


def publish_new(source, output):
    output = new_path(output)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(prefix='.' + output.name + '.', dir=output.parent, delete=False) as target:
            temporary = Path(target.name)
            with Path(source).open('rb') as stream:
                shutil.copyfileobj(stream, target, 1024 * 1024)
            target.flush()
            os.fsync(target.fileno())
        need(digest(temporary) == digest(source), 'publication copy differs')
        os.link(temporary, output)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def build_v4(args):
    document, _entries = load_manifest()
    output, report = new_path(args.output), new_path(args.report)
    need(output != report, 'ROM and report paths must differ')
    base = authenticate_file(args.base, document['inputs'][args.language], '1.2.5 input')
    charmap = Path(args.charmap).resolve(strict=True)
    commands = charmap.parent / 'tools/py_scripts/scrcmd.json'
    need(digest(charmap) == document['external']['charmap_sha256'], 'charmap identity differs')
    need(digest(commands) == document['external']['scrcmd_sha256'], 'script-command metadata differs')
    need(sys.version.split()[0] == PYTHON_VERSION and digest(Path(sys.executable).resolve()) == PYTHON_SHA256,
         'Python toolchain identity differs')
    # Authenticate before the historical compiler driver can execute clang.
    sys.path.insert(0, str(ROOT / 'source'))
    from sgp13.compiler import compiler_path, compiler_environment
    compiler = Path(compiler_path())
    environment = compiler_environment()
    environment['PATH'] = str(compiler.parent) + os.pathsep + '/usr/bin:/bin'
    environment.update(PYTHONDONTWRITEBYTECODE='1', PYTHONNOUSERSITE='1')
    work = Path(args.work_dir).resolve(strict=True)
    need(work.is_dir() and work.stat().st_uid == os.getuid() and not work.stat().st_mode & 0o077,
         'work directory must be private and owned by this user')
    need(shutil.disk_usage(work).free >= SPACE_FLOOR + PEAK_BUDGET,
         'need 10 GiB free plus the 4 GiB sequential build budget')
    with tempfile.TemporaryDirectory(prefix='sgp-v4-bootstrap-', dir=work) as scratch_name:
        scratch = Path(scratch_name)
        _document, staged = stage_sources(args.repository, scratch / 'published')
        environment['PYTHONPATH'] = str(scratch / 'published/source')
        built, legacy_report = scratch / 'v4.nds', scratch / 'v4.json'
        log_path = scratch / 'builder.log'
        command = [sys.executable, '-B', '-m', 'sgp13.build', '--base', str(base),
                   '--out', str(built), '--charmap', str(charmap),
                   '--work-dir', str(scratch / 'build'), '--report', str(legacy_report)]
        with log_path.open('xb') as log:
            process = subprocess.Popen(command, cwd=scratch, env=environment, stdout=log,
                                       stderr=subprocess.STDOUT, start_new_session=True)
            try:
                returncode = process.wait(timeout=600)
            except BaseException:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
                raise
        need(log_path.stat().st_size <= 4 * 1024**2, 'historical build log exceeded budget')
        if returncode:
            raise ValueError('historical builder failed: ' + log_path.read_text(errors='replace')[-5000:])
        authenticate_file(built, document['outputs'][args.language], 'V4 output')
        legacy = json.loads(legacy_report.read_text())
        core = {name: info['sha256'] for name, info in document['files'].items()}
        need(legacy['source_sha256'] == core, 'historical builder source snapshot differs')
        need(legacy['output_sha256'] == document['outputs'][args.language]['sha256'], 'legacy receipt output differs')
        need(digest(base) == document['inputs'][args.language]['sha256'], 'original input changed')
        receipt = {'schema': 1, 'language': args.language, 'source_commit': PUBLISHED_COMMIT,
                   'manifest_sha256': MANIFEST_SHA256, 'source_files': staged['files'],
                   'input': document['inputs'][args.language], 'output': document['outputs'][args.language],
                   'python_sha256': PYTHON_SHA256, 'compiler_sha256': digest(compiler),
                   'external': document['external'], 'legacy_receipt': legacy,
                   'scope': 'Exact legacy V4 file reconstruction only; HF01 is an intermediate, not an installed-game update or runtime acceptance'}
        receipt_path = scratch / 'receipt.json'
        receipt_path.write_text(json.dumps(receipt, indent=2) + '\n')
        publish_new(built, output)
        publish_new(receipt_path, report)
    return receipt


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    stage = sub.add_parser('stage')
    stage.add_argument('--repository', type=Path, default=ROOT)
    stage.add_argument('--output-dir', type=Path, required=True)
    build = sub.add_parser('build')
    build.add_argument('--repository', type=Path, default=ROOT)
    build.add_argument('--language', required=True, choices=('EN', 'IT'))
    for name in ('base', 'charmap', 'output', 'report', 'work-dir'):
        build.add_argument('--' + name, required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == 'stage':
            _document, result = stage_sources(args.repository, args.output_dir)
            print(json.dumps({'source_commit': result['source_commit'], 'files': len(result['files'])}))
        else:
            result = build_v4(args)
            print(json.dumps({'language': result['language'], 'output': result['output']}))
    except (ValueError, OSError, subprocess.SubprocessError) as error:
        parser.exit(1, str(error) + '\n')


if __name__ == '__main__':
    main()
