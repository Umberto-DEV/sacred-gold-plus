#!/usr/bin/env python3
"""Independent verifier for a run_probe.py output directory.

    verify_probe.py --run OUT_DIR --receipt RECEIPT.json

It recomputes every verdict from observations.json, the saved scripts and the captures; it
never trusts the tool's own result. It REFUSES:
  * an unchanged V4 capture presented as a remote box (canonical V4 ROM hash, ROM hash that
    differs from the install receipt, or a record whose magic is absent);
  * a PC image that only looks like the PC: the run must show phase PC_RUNNING under the
    record, the owner exit callback equal to the receipt's `sgp_box_pc_return`, the owner
    exit environment equal to the recorded PCBoxArgs, those PCBoxArgs holding
    (SaveData, menu input state, mode 2) and overlay 14 resident, all at one observation
    point, reproduced by an independent third pass;
  * synthetic or corrupted results: pointers outside main RAM, counters that do not
    balance, generations that go backwards, a discovery pass that disagrees with the run,
    altered scripts, blank captures or a PC capture equal to the party capture.
Exit status 0 = accepted, 2 = refused (the reasons go to stderr). Acceptance is evidence from
the harness core only: it is never ANDROID_ACCEPTED.

Authenticity limit: a runtime.log and an observations.json forged TOGETHER so that they are physically
coherent cannot be told from a real run by any offline check (the synthetic model in the tests is the
proof). Only re-running the harness on the same ROM, save and script and comparing the logs proves where
they come from; run_probe.py records the hashes of the inputs so that re-run is exact.
"""
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

V4_SHA256 = {'EN': '179edfb1ca331503f438e98f3afccfb0ab85759bf9ab88fb86c735f5fcefbf90',
             'IT': '2a2f0b437fca524c18b71b20feb01a1f51351e61c7c897ce73d9b3be1ee3a156'}
MAGIC = 0x31425053
RAM_LO, RAM_HI = 0x02000000, 0x02400000
WORDS = 16
NAMES = ['magic', 'generation', 'phase', 'requested', 'field', 'owner', 'args', 'pc_args', 'selection',
         'reason', 'prompt_shown', 'request_generation', 'allocs', 'frees', 'opens', 'failures']
PHASE = {'IDLE': 0, 'BOUND': 1, 'EXITING': 2, 'PC_RUNNING': 3}
OVERLAY14_BASE = 0x021E5900
HITBOX = ((124, 172), (168, 184))   # [x0, x1) x [y0, y1) on the lower screen


class Refusal(Exception):
    pass


def require(condition, message):
    if not condition:
        raise Refusal(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def groups(reads):
    """Split ordered (address, value) reads into the contiguous blocks each `read` command produced."""
    out = []
    for address, value in reads:
        if out and address == out[-1][-1][0] + 4:
            out[-1].append((address, value))
        else:
            out.append([(address, value)])
    return out


def record_groups(reads, area):
    """[(index in groups(), record dict)] for the 16-word reads of the record at `area`."""
    out = []
    for index, block in enumerate(groups(reads)):
        if block[0][0] == area and len(block) == WORDS:
            out.append((index, {name: block[i][1] for i, name in enumerate(NAMES)}))
    return out


def sane_pointer(value):
    return RAM_LO <= value < RAM_HI and value % 4 == 0


def check_record(record, label):
    require(record['magic'] == MAGIC, '%s: record magic %#x (not the installed portable ROM)' % (label, record['magic']))
    require(record['phase'] in PHASE.values(), '%s: phase out of range' % label)
    require(record['requested'] in (0, 1) and record['prompt_shown'] in (0, 1), '%s: flag out of range' % label)
    require(record['allocs'] >= record['frees'], '%s: frees exceed allocs' % label)
    for name in ('field', 'owner', 'args', 'pc_args'):
        value = record[name]
        require(value == 0 or sane_pointer(value), '%s: %s is not a plausible RAM pointer (%#x)' % (label, name, value))


def image_stats(path):
    from PIL import Image
    image = Image.open(path).convert('RGB')
    colors = image.getcolors(maxcolors=1 << 20) or []
    return {'colors': len(colors), 'sha256': hashlib.sha256(image.tobytes()).hexdigest()}


READ = re.compile(r'^READ 0x([0-9a-f]+) 0x([0-9a-f]+)$', re.M)
ABI = Path(__file__).resolve().parents[3] / 'sgp131' / 'data' / 'portable-native-abi.json'
PC_CASES = ('bridge-prepared', 'input-R', 'input-touch')


def log_reads(run, obs, name):
    """The reads of one pass, re-parsed from the harness's own runtime.log (never from observations.json)."""
    log = Path(run) / name / 'runtime.log'
    require(log.is_file(), '%s: runtime.log is missing' % name)
    require(sha(log) == obs[name]['log_sha256'], '%s: runtime.log differs from the hash recorded by the run' % name)
    reads = [(int(a, 16), int(v, 16)) for a, v in READ.findall(log.read_text())]
    require([list(r) for r in obs[name]['reads']] == [list(r) for r in reads],
            '%s: observations.json disagrees with runtime.log (forged or edited)' % name)
    return reads


def overlay14_words():
    head = json.loads(ABI.read_text())['overlay14']
    return [int.from_bytes(bytes.fromhex(head['head16_hex'])[i:i + 4], 'little') for i in range(0, 16, 4)]


def script_writes(run, names):
    return [line for name in names for line in (Path(run) / name / 'commands.script').read_text().splitlines()
            if line.startswith('write')]


def input_in_script(run, name, case):
    """The command that raises the request must be in the script: `tap R` or a touch inside the hitbox."""
    lines = (Path(run) / name / 'commands.script').read_text().splitlines()
    start = next((i for i, line in enumerate(lines) if line.strip() == 'capture party.ppm'), None)
    if start is None:
        return False
    for line in lines[start + 1:]:
        parts = line.split()
        if case == 'input-R' and parts[:2] == ['tap', 'R']:
            return True
        if case == 'input-touch' and len(parts) >= 3 and parts[0] == 'touch':
            x, y = int(parts[1]), int(parts[2])
            if HITBOX[0][0] <= x < HITBOX[0][1] and HITBOX[1][0] <= y < HITBOX[1][1]:
                return True
    return False


def verify_pc_observation(run, obs, receipt, area, pass3_reads, second):
    d = obs['discovered']
    third_groups = record_groups(pass3_reads, area)
    require([r for _i, r in third_groups] == second, 'pass 3 does not reproduce pass 2')
    pc_at = [(i, r) for i, r in third_groups if r['phase'] == PHASE['PC_RUNNING']]
    require(pc_at and pc_at[0][1]['opens'] >= 1,
            'the PC was never observed running under the record (a PC-looking image is not enough)')
    index, pc = pc_at[0]
    require(pc['pc_args'] != 0 and pc['args'] == 0, 'PC phase without owned PCBoxArgs / with a live party args')
    block = groups(pass3_reads)
    owner_span, pc_span, overlay = block[index + 1], block[index + 2], block[index + 3]
    owner = d['owner']
    require(owner_span[0][0] == owner + 0x34C and len(owner_span) == 16, 'owner span misplaced')
    word = {a: v for a, v in owner_span}
    require(word[owner + 0x354] == receipt['symbols']['sgp_box_pc_return'],
            'owner exit callback is not the receipt pc_return pointer')
    require(word[owner + 0x380] == pc['pc_args'], 'owner exit environment is not the recorded PCBoxArgs')
    require(pc_span[0][0] == pc['pc_args'] and len(pc_span) == 3, 'PCBoxArgs span misplaced')
    words = [v for _a, v in pc_span]
    require(words[2] == 2 and sane_pointer(words[0]) and sane_pointer(words[1]), 'PCBoxArgs are not (SaveData, input, mode 2)')
    require(obs.get('pc_args_words') == words, 'PCBoxArgs words in observations.json differ from the log')
    require(overlay[0][0] == OVERLAY14_BASE and [v for _a, v in overlay] == overlay14_words(),
            'overlay 14 head differs from the pinned bytes (not resident, or not the PC overlay)')


def verify(run, receipt_path):
    run = Path(run)
    receipt = json.loads(Path(receipt_path).read_text())
    obs = json.loads((run / 'observations.json').read_text())
    case = obs['case']
    require(obs['rom_sha256'] not in V4_SHA256.values(), 'canonical V4 capture presented as a remote box')
    require(obs['rom_sha256'] == receipt['output_sha256'], 'ROM hash does not match the receipt')
    require(obs['receipt_sha256'] == sha(receipt_path), 'receipt hash differs from the one used by the run')
    require(obs['language'] == receipt['language'], 'language differs from the receipt')
    require(obs['state_address'] == receipt['state']['address'], 'record address differs from the receipt')
    passes = ['pass1', 'pass2'] + (['pass3'] if obs.get('pass3') else [])
    for name in passes:
        require(sha(run / name / 'commands.script') == obs[name]['script_sha256'], name + ' script was altered')
    reads = {name: log_reads(run, obs, name) for name in passes}      # everything below comes from the logs
    area = obs['state_address']
    first = [r for _i, r in record_groups(reads['pass1'], area)]
    second_groups = record_groups(reads['pass2'], area)
    second = [r for _i, r in second_groups]
    require(first and second, 'no record observations')
    for index, record in enumerate(first + second):
        check_record(record, 'record %d' % index)
    d = obs['discovered']
    require((d['owner'], d['args']) == (second[0]['owner'], second[0]['args']) == (first[0]['owner'], first[0]['args']),
            'discovery pass and run disagree on owner/args (non-deterministic or synthetic)')
    require(first[0]['phase'] == PHASE['BOUND'] and first[0]['generation'] >= 1, 'ordinary party was not bound')
    generations = [r['generation'] for r in second]
    require(generations == sorted(generations), 'generation went backwards')
    if case == 'baseline':
        return {'case': case, 'accepted': True, 'note': 'control only; not a portable box proof'}
    if case in PC_CASES:
        writes = script_writes(run, passes)
        if case == 'bridge-prepared':
            require(set(writes) == {'write 0x%08X 1 4' % (area + 0x0C)}, 'bridge-prepared may write only requested=1')
        else:
            require(not writes, 'the input path must not write the record (that is the bridge-prepared case)')
            require(input_in_script(run, 'pass2', case), 'the script never presses R / touches the box (%s)' % case)
            require(first[0]['prompt_shown'] == 1 and first[0]['requested'] == 0,
                    'the suffix was not recorded as shown (or a request was already pending) before the input')
        require(obs.get('pass3'), 'independent third pass missing')
        verify_pc_observation(run, obs, receipt, area, reads['pass3'], second)
        after = second[-1]
        require(after['phase'] in (PHASE['IDLE'], PHASE['BOUND']) and after['pc_args'] == 0 and after['allocs'] == after['frees'],
                'record not at rest after the PC (leak or stuck phase)')
        for name in ('party.ppm', 'pc.ppm', 'party-after.ppm'):
            require((run / 'pass2' / name).is_file(), 'missing capture ' + name)
        stats = {n: image_stats(run / 'pass2' / n) for n in ('party.ppm', 'pc.ppm', 'party-after.ppm')}
        require(all(s['colors'] > 8 for s in stats.values()), 'blank or near-blank capture')
        require(stats['pc.ppm']['sha256'] != stats['party.ppm']['sha256'], 'PC capture equals the party capture')
        return {'case': case, 'accepted': True, 'opens': after['opens'], 'generation': generations[-1]}
    if case == 'cycle':
        cycles = [r for r in second if r['opens'] > 0]
        require(len(cycles) >= 50, 'fewer than 50 cycle observations')
        require(all(r['allocs'] == r['frees'] for r in cycles), 'alloc/free imbalance at a rest point')
        require(len({(r['phase'], r['pc_args'], r['requested']) for r in cycles}) == 1, 'rest points differ (progressive residue)')
        require([r['opens'] for r in cycles] == list(range(1, len(cycles) + 1)), 'open count does not follow the cycles one by one')
        return {'case': case, 'accepted': True, 'cycles': len(cycles)}
    if case == 'save-continue':
        before, after = run / 'pass2' / 'before-save.sav', run / 'pass2' / 'after-save.sav'
        require(before.is_file() and after.is_file(), 'missing SRAM exports')
        require(sha(before) != sha(after), 'native SAVE did not change the SRAM')
        return {'case': case, 'accepted': True,
                'note': 'full logical comparison of party/boxes belongs to the save comparer, not to this tool'}
    raise Refusal('unknown case ' + case)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--run', required=True)
    parser.add_argument('--receipt', required=True)
    args = parser.parse_args(argv)
    try:
        result = verify(args.run, args.receipt)
    except (Refusal, KeyError, IndexError, FileNotFoundError, json.JSONDecodeError) as error:
        print('REFUSED: %s: %s' % (type(error).__name__, error), file=sys.stderr)
        return 2
    print(json.dumps(result))
    return 0


if __name__ == '__main__':
    sys.exit(main())
