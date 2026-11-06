#!/usr/bin/env python3
"""Bounded replay of the portable box on a private TEST save (for Codex; NOT run by c8-B).

    run_probe.py --rom ROM --receipt RECEIPT.json --fixture SAVE --harness HG_RUNTIME \
                 --out NEW_DIR --case bridge-prepared [--navigate OPEN_PARTY.script]

The tool verifies identities first (ROM against the receipt, fixture and harness
hashes recorded), writes a limited script (key/touch inputs, bounded waits, `read`
of the transient record and of the structures it names, captures, SRAM export), runs
the existing hg_runtime harness in a NEW directory and records observations.json.
It never writes a ROM or a save, loads no savestate and adds no debug command to the
game. `--case bridge-prepared` does not prove R or touch: after a normal party opening
it reads the record, then writes ONLY `requested = 1` into the compartment record
(the game validates owner/generation/args/phase and ignores a mismatch). The input
path (R, touch) is the separate cases `input-R` and `input-touch`.

Dynamic addresses (owner, args, PC args) cannot be computed inside a harness script, so
the tool runs a deterministic DISCOVERY pass first (same boot, reads only) and a second
pass that reads those addresses; verify_probe.py rejects the run unless both passes
agree on the discovered values.

Cases
  baseline         normal party opening, record read, no request (control; the unchanged
                   V4 ROM must also complete it, which is why verify_probe refuses it as a box)
  bridge-prepared  record read, requested=1, state 1 consumes it, native PC (mode 2) runs
  input-R          physical R on the ordinary party (needs input+prompt activation)
  input-touch      touch inside the proposed box hitbox (needs input+prompt activation)
  cycle            --cycles N (default 50) open/close loops with record reads at rest points
  save-continue    PC operation, native SAVE, cold Continue; exports both SRAM files

The navigation segment (menu -> Pokemon) depends on the fixture; a default is provided
as a starting point and is UNPROVEN: pass --navigate with a validated segment.
"""
import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
BOOT = ROOT / 'source' / 'runtime' / 'inputs' / 'cold-reload.script'
V4_SHA256 = {'EN': '179edfb1ca331503f438e98f3afccfb0ab85759bf9ab88fb86c735f5fcefbf90',
             'IT': '2a2f0b437fca524c18b71b20feb01a1f51351e61c7c897ce73d9b3be1ee3a156'}
RECORD_WORDS = 16
STATE_OFFSETS = {'magic': 0x00, 'generation': 0x04, 'phase': 0x08, 'requested': 0x0C, 'field': 0x10,
                 'owner': 0x14, 'args': 0x18, 'pc_args': 0x1C, 'selection': 0x20, 'reason': 0x24,
                 'prompt_shown': 0x28, 'request_generation': 0x2C, 'allocs': 0x30, 'frees': 0x34,
                 'opens': 0x38, 'failures': 0x3C}
DEFAULT_OPEN_PARTY = 'tap X 2 180\ntouch 64 30 2\nrun 240\n'   # UNPROVEN default; override with --navigate
CASES = ('baseline', 'bridge-prepared', 'input-R', 'input-touch', 'cycle', 'save-continue')
HITBOX_CENTER = (148, 176)   # inside [124,172) x [168,184)
OVERLAY14 = 0x021E5900
PC_CASES = ('bridge-prepared', 'input-R', 'input-touch')
READ = re.compile(r'^READ 0x([0-9a-f]+) 0x([0-9a-f]+)$', re.M)


class Refusal(Exception):
    pass


def require(condition, message):
    if not condition:
        raise Refusal(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def parse_reads(log):
    """Ordered [(address, value)] from harness `read` output."""
    return [(int(a, 16), int(v, 16)) for a, v in READ.findall(log)]


def reads(address, count=RECORD_WORDS, width=4):
    return 'read 0x%08X %d %d\n' % (address, width, count)


def pc_block(area, discovered):
    """What every PC-reaching case observes at the same point: record, owner span, PCBoxArgs, overlay 14."""
    text = 'capture pc.ppm\n' + reads(area)
    if discovered:
        text += reads(discovered['owner'] + 0x34C, 16)           # inhibit flags .. owner+0x38B (0x354 callback, 0x380 environment)
        if discovered.get('pc_args'):
            text += reads(discovered['pc_args'], 3)              # SaveData, menu input state, mode
        text += reads(OVERLAY14, 4)                              # overlay 14 resident only while the PC runs
    return text


def case_script(case, receipt, discovered=None, navigate=DEFAULT_OPEN_PARTY, cycles=50):
    """Limited script text for `case`. `discovered` = {'owner':..,'args':..,'pc_args':..} for later passes."""
    area = receipt['state']['address']
    boot = BOOT.read_text().splitlines()
    cut = next(i for i, line in enumerate(boot) if 'town-reloaded' in line) + 1
    text = '\n'.join(boot[:cut]) + '\n' + navigate
    text += 'run 120\n' + reads(area) + 'capture party.ppm\n'
    if discovered:
        text += reads(discovered['owner'] + 0x34C, 16)
        text += reads(discovered['args'], 17)
    after_pc = 'tap B 2 240\nrun 240\ncapture party-after.ppm\n' + reads(area) + 'tap B 2 180\nrun 240\ncapture field.ppm\n' + reads(area)
    if case == 'baseline':
        return text + 'tap B 2 180\nrun 240\nstatus\nquit\n'
    if case == 'bridge-prepared':
        text += 'write 0x%08X 1 4\nrun 30\nrun 240\n' % (area + STATE_OFFSETS['requested'])
        return text + pc_block(area, discovered) + after_pc + 'status\nquit\n'
    if case == 'input-R':
        return text + 'tap R 2 300\n' + pc_block(area, discovered) + after_pc + 'quit\n'
    if case == 'input-touch':
        return text + 'touch %d %d 2\nrun 300\n' % HITBOX_CENTER + pc_block(area, discovered) + after_pc + 'quit\n'
    if case == 'cycle':
        body = ''
        for index in range(cycles):
            body += 'tap R 2 300\ntap B 2 240\nrun 240\n' + reads(area)
        return text + body + 'status\nquit\n'
    if case == 'save-continue':
        text += 'tap R 2 300\ntap B 2 240\nrun 240\ntap B 2 180\nrun 120\n'
        return text + 'sram before-save.sav\ntouch 120 75 2\nrun 600\ntap A 8 600\ntap A 8 1600\nsram after-save.sav\nquit\n'
    raise Refusal('unknown case ' + case)


def run_harness(harness, rom, fixture, out, script):
    out.mkdir(parents=True, exist_ok=False)
    (out / 'commands.script').write_text(script)
    hashes = {'rom': sha(rom), 'fixture': sha(fixture), 'harness': sha(harness)}
    with (out / 'runtime.log').open('w') as log:
        result = subprocess.run([str(harness), '--rom', str(rom), '--sram', str(fixture), '--out', str(out),
                                 '--script', str(out / 'commands.script'), '--trace-pc'],
                                stdout=log, stderr=subprocess.STDOUT, timeout=900)
    text = (out / 'runtime.log').read_text()
    require(result.returncode == 0 and 'ERROR ' not in text, 'harness failed; inspect the private runtime.log')
    require(hashes == {'rom': sha(rom), 'fixture': sha(fixture), 'harness': sha(harness)}, 'an input changed during the run')
    return {'hashes': hashes, 'script_sha256': sha(out / 'commands.script'), 'log_sha256': sha(out / 'runtime.log'),
            'reads': parse_reads(text)}


def _records(values, receipt):
    """16-word record reads at the record address, in order (same grouping as verify_probe)."""
    area, out, block = receipt['state']['address'], [], []
    for address, value in values:
        if block and address == block[-1][0] + 4:
            block.append((address, value))
        else:
            if len(block) == RECORD_WORDS and block[0][0] == area:
                out.append({name: block[offset // 4][1] for name, offset in STATE_OFFSETS.items()})
            block = [(address, value)]
    if len(block) == RECORD_WORDS and block[0][0] == area:
        out.append({name: block[offset // 4][1] for name, offset in STATE_OFFSETS.items()})
    return out


def discover(values, receipt):
    """owner / args / pc_args from the first record read of a discovery pass."""
    records = _records(values, receipt)
    require(records, 'the record was not read')
    require(records[0]['magic'] == 0x31425053, 'record magic missing: ROM is not the installed portable ROM')
    return records[0]


def probe(args):
    receipt = json.loads(Path(args.receipt).read_text())
    rom, fixture, harness, out = (Path(p).resolve() for p in (args.rom, args.fixture, args.harness, args.out))
    require(args.case in CASES, 'unknown case')
    require(not out.exists(), 'output directory must be new')
    require(sha(rom) == receipt['output_sha256'], 'ROM hash differs from the receipt (an unchanged V4 ROM is not the portable ROM)')
    require(sha(rom) not in V4_SHA256.values(), 'canonical V4 ROM refused')
    navigate = Path(args.navigate).read_text() if args.navigate else DEFAULT_OPEN_PARTY
    # pass 1: discovery (reads only, same boot, deterministic)
    first = run_harness(harness, rom, fixture, out / 'pass1', case_script('baseline', receipt, None, navigate))
    record = discover(first['reads'], receipt)
    discovered = {'owner': record['owner'], 'args': record['args'], 'pc_args': 0}
    require(record['phase'] == 1, 'party not bound after the normal opening (phase %d)' % record['phase'])
    second = run_harness(harness, rom, fixture, out / 'pass2',
                         case_script(args.case, receipt, discovered, navigate, args.cycles))
    pc_words, third = None, None
    if args.case in PC_CASES:
        at_pc = [r for r in _records(second['reads'], receipt) if r['phase'] == 3]
        if at_pc and at_pc[0]['pc_args']:
            discovered['pc_args'] = at_pc[0]['pc_args']
            third = run_harness(harness, rom, fixture, out / 'pass3', case_script(args.case, receipt, discovered, navigate, args.cycles))
            pc_words = [v for a, v in third['reads'] if a in (at_pc[0]['pc_args'] + 4 * i for i in range(3))][:3]
    observations = {
        'tool': 'run_probe.py', 'case': args.case, 'receipt_sha256': sha(args.receipt),
        'language': receipt['language'], 'rom_sha256': second['hashes']['rom'],
        'fixture_sha256': second['hashes']['fixture'], 'harness_sha256': second['hashes']['harness'],
        'navigation_sha256': hashlib.sha256(navigate.encode()).hexdigest(),
        'pass1': {'reads': first['reads'], 'script_sha256': first['script_sha256'], 'log_sha256': first['log_sha256']},
        'pass2': {'reads': second['reads'], 'script_sha256': second['script_sha256'], 'log_sha256': second['log_sha256']},
        'discovered': discovered, 'state_address': receipt['state']['address'],
        'pass3': None if third is None else {'reads': third['reads'], 'script_sha256': third['script_sha256'],
                                             'log_sha256': third['log_sha256']},
        'pc_args_words': pc_words,
        'captures': sorted(p.name for p in (out / 'pass2').glob('*.ppm')),
        'claims': ['harness-core run only; no Android/device claim',
                   'bridge-prepared does not prove R or touch; verify_probe re-reads every runtime.log'],
    }
    (out / 'observations.json').write_text(json.dumps(observations, indent=1) + '\n')
    return observations


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    for name in ('rom', 'receipt', 'fixture', 'harness', 'out'):
        parser.add_argument('--' + name, required=True)
    parser.add_argument('--case', required=True, choices=CASES)
    parser.add_argument('--navigate')
    parser.add_argument('--cycles', type=int, default=50)
    try:
        result = probe(parser.parse_args(argv))
    except Refusal as error:
        print('REFUSED: %s' % error, file=sys.stderr)
        return 2
    print(json.dumps({'case': result['case'], 'observations': 'observations.json'}))
    return 0


if __name__ == '__main__':
    sys.exit(main())
