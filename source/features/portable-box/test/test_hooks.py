"""Installer on the real V4 ROMs: owned bytes only, hook decoding, trampoline, refusals, and the
full party -> PC -> party cycle run from the bytes the INSTALLER wrote (not the bench helpers).

The compartment base is the `portable-box.runtime` slot of the reserve map, granted by a DECLARED test
policy (portable_bench.declared_reserve); the real policy cannot grant it yet (INTEGRATION.md).
"""
import argparse
import copy
import hashlib
import importlib.util
import json
import struct
import tempfile
import unittest
from pathlib import Path

import portable_bench as pb
from portable_bench import World, TASK, FIELD, OWNER, PARTY
from sgp12.rom import bl_decode
from sgp131 import portable
from test_runtime import Cycle, STATE1_REQUEST_EXIT, PHASE, ALL_ON

LANGUAGES = ('EN', 'IT')
_INSTALLED = {}
SYNTHETIC_PROOF = {'sha256': hashlib.sha256(b'synthetic unit-test context proof').hexdigest(),
                   'origin': 'unit test fixture (synthetic, not a measurement)', 'status': 'synthetic'}
INSTALL_ACTIVE = dict(bridge=1, input=1, prompt=1)
CANDIDATE = hashlib.sha256(b'fixture: the inert candidate ROM of the portable hooks test').hexdigest()


def installed(test, language, activation=None):
    key = (language, tuple(sorted((activation or {}).items())))
    if key not in _INSTALLED:
        data, segments, _ = pb.rom(test, language)
        with tempfile.TemporaryDirectory() as work, pb.declared_reserve():
            active = bool(activation and any(activation.get(k) for k in ('bridge', 'input', 'prompt')))
            out, receipt = portable.prepare(data, language, work, allocation=pb.declared_allocation(language),
                                            preimage_sha256=pb.preimage_of(data), activation=activation,
                                            context_proof=SYNTHETIC_PROOF if active else None,
                                            candidate_sha256=CANDIDATE if active else None, allow_synthetic_proof=active)
        _INSTALLED[key] = (data, out, receipt)
    return _INSTALLED[key]


class HookDecoding(unittest.TestCase):
    def test_hook_sites_decode_to_the_installed_entries(self):
        for language in LANGUAGES:
            data, out, receipt = installed(self, language)
            segments = portable.arm9_segments(out)
            symbols = receipt['symbols']
            expected = {'state1': 'sgp_box_party_main', 'launch': 'sgp_box_launch_app', 'print32': 'sgp_box_prompt_print'}
            for name, entry in expected.items():
                site = receipt['hooks'][name]['site']
                self.assertEqual(bl_decode(site, portable.read_ram(out, segments, site, 4)), symbols[entry] & ~1, name)
            tramp = receipt['compartment']['trampoline']
            self.assertEqual(portable.read_ram(out, segments, portable.CALLBACK, 8),
                             portable.callback_hook(tramp))
            self.assertEqual(portable.read_ram(out, segments, tramp, portable.TRAMPOLINE_BYTES),
                             portable.callback_trampoline(tramp, symbols['sgp_box_party_return']))
            # the byte after the displaced span is untouched, the second half of the old BL is dead code
            self.assertEqual(portable.read_ram(out, segments, portable.CALLBACK + 8, 4),
                             portable.read_ram(data, segments, portable.CALLBACK + 8, 4))

    def test_compartment_state_starts_clean_and_inert(self):
        for language in LANGUAGES:
            data, out, receipt = installed(self, language)
            segments = portable.arm9_segments(out)
            area = receipt['state']['address']
            words = struct.unpack('<24I', portable.read_ram(out, segments, area, 96))
            self.assertEqual(words[0], 0x31425053)
            self.assertEqual(words[1:16], (0,) * 15, 'record starts zero')
            self.assertEqual(words[16], 0x31434253)
            self.assertEqual(words[17:22], (0, 0, 0, 0, 3), 'bridge/input/prompt/reserved off, travel mask 3')


class InstalledRomRuns(unittest.TestCase):
    """Unicorn on the PATCHED ROM image: the bytes the installer wrote, with their own symbols."""

    def world(self, language, activation):
        data, out, receipt = installed(self, language, activation)
        return World(self, language, True, activation, installed=(out, receipt))

    def test_installed_rom_runs_a_full_cycle_and_is_inert_by_default(self):
        for language in LANGUAGES:
            w = self.world(language, INSTALL_ACTIVE)
            cycle = Cycle(w)
            self.assertEqual(w.state('generation'), 1)
            self.assertEqual(cycle.accept_request(), STATE1_REQUEST_EXIT)
            cycle.party_exits()
            cycle.callback()
            self.assertEqual(w.state('phase'), PHASE['PC_RUNNING'])
            cycle.pc_exits()
            self.assertEqual(w.state('phase'), PHASE['BOUND'])
            self.assertEqual(w.errors, [])
            quiet = self.world(language, None)
            quiet.open_party()
            quiet.set_state('requested', 1)
            self.assertEqual(quiet.blob_call('sgp_box_party_main', PARTY), quiet.main_normal_return, 'inert: request ignored')
            self.assertEqual(quiet.launches[0][0], pb.PARTY_TEMPLATE)

    def test_reserved_refresh_word_has_no_effect(self):
        for language in LANGUAGES:
            runs = []
            for value in (0, 1):
                w = self.world(language, INSTALL_ACTIVE)
                w.set_cfg('refresh_field_data', value)
                cycle = Cycle(w)
                cycle.accept_request()
                cycle.party_exits()
                cycle.callback()
                cycle.pc_exits()
                runs.append([e for e in w.events if e[0] not in ('ext',)])
            self.assertEqual(runs[0], runs[1])
            self.assertFalse(any(e[0] == 'ext' for e in runs[0]))


PROBE_TOOLS = Path(__file__).resolve().parents[1] / 'tools'
OVERLAY14_WORDS = struct.unpack('<4I', bytes.fromhex(portable.abi()['overlay14']['head16_hex']))


def tool(name):
    spec = importlib.util.spec_from_file_location(name, PROBE_TOOLS / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


AREA, OWNER_ADDR, ARGS_ADDR, NEW_ARGS, PC_ADDR = 0x023C9DC4, 0x02311000, 0x02320000, 0x02320100, 0x02320200
PC_RETURN, NATIVE_CB_PTR, SAVE_PTR, INPUT_PTR = 0x023C9F41, 0x0203CA9D, 0x02390000, 0x0231010C


def fake_reads(script, flips=()):
    """SYNTHETIC harness: answers `read` commands from a tiny model of the record. It exists to test
    the plumbing of run_probe/verify_probe; a crafted model proves consistency checks, not the game."""
    state = dict(magic=0x31425053, generation=1, phase=1, requested=0, field=0x02310000, owner=OWNER_ADDR, args=ARGS_ADDR,
                 pc_args=0, selection=2, reason=0, prompt_shown=1, request_generation=0, allocs=0, frees=0, opens=0, failures=0)
    names = list(state)
    state['_pass3'] = ('read 0x%08X 4 3' % PC_ADDR) in script
    cycle_mode = 'capture pc.ppm' not in script and script.count('tap R 2 300') > 1
    in_pc, out, images = False, [], {}
    for line in script.splitlines():
        parts = line.split()
        if not parts:
            continue
        if parts[0] == 'write' and int(parts[1], 16) == AREA + 0x0C:
            state['requested'] = 1
        elif parts[0] == 'tap' and parts[1] == 'R' or parts[0] == 'touch' and int(parts[1]) == 148:
            state['requested'] = 1
            if cycle_mode:       # each tap R is one complete open/close cycle in the synthetic model
                state.update(requested=0, opens=state['opens'] + 1, allocs=state['allocs'] + 2, frees=state['frees'] + 2,
                             generation=state['generation'] + 1)
        elif parts[0] == 'capture':
            if parts[1] == 'pc.ppm' and state['requested']:
                state.update(phase=3, requested=0, args=0, pc_args=PC_ADDR, allocs=1, opens=state['opens'] + 1)
                in_pc = True
            elif parts[1] == 'party-after.ppm' and in_pc:
                state.update(phase=1, pc_args=0, args=NEW_ARGS, allocs=2, frees=2, generation=2)
                in_pc = False
            images[parts[1]] = in_pc
        elif parts[0] == 'read':
            address, width, count = int(parts[1], 16), int(parts[2]), int(parts[3])
            for i in range(count):
                a = address + width * i
                if AREA <= a < AREA + 64:
                    value = state[names[(a - AREA) // 4]]
                elif a == OWNER_ADDR + 0x354:
                    value = PC_RETURN if in_pc else NATIVE_CB_PTR
                elif a == OWNER_ADDR + 0x380:
                    value = PC_ADDR if in_pc else state['args']
                elif a == OWNER_ADDR + 0x34C:
                    value = 0x180
                elif PC_ADDR <= a < PC_ADDR + 12:
                    value = (SAVE_PTR, INPUT_PTR, 2)[(a - PC_ADDR) // 4]
                elif 0x021E5900 <= a < 0x021E5910:
                    value = OVERLAY14_WORDS[(a - 0x021E5900) // 4] if in_pc else 0
                else:
                    value = 0
                for flip in flips:
                    value = flip(a, value, state, in_pc)
                out.append((a, value))
    return out, images


class Probes(unittest.TestCase):
    """run_probe builds a limited script and verify_probe refuses fakes. Synthetic harness: plumbing only."""

    def setUp(self):
        self.run_probe, self.verify_probe = tool('run_probe'), tool('verify_probe')
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.rom, self.fixture, self.harness = (self.dir / n for n in ('rom.nds', 'fixture.sav', 'harness'))
        self.rom.write_bytes(b'portable rom stand-in')
        self.fixture.write_bytes(b'fixture')
        self.harness.write_bytes(b'harness')
        self.receipt = {'output_sha256': hashlib.sha256(self.rom.read_bytes()).hexdigest(), 'language': 'EN',
                        'state': {'address': AREA}, 'symbols': {'sgp_box_pc_return': PC_RETURN}}
        self.receipt_path = self.dir / 'receipt.json'
        self.receipt_path.write_text(json.dumps(self.receipt))
        self.counter = 0

    def tearDown(self):
        self.tmp.cleanup()

    def fake_subprocess(self, flips=(), tamper_images=False):
        """SYNTHETIC harness process: writes READ lines to the log it is given and PPM/SRAM files to --out."""
        import types

        def run(command, stdout=None, stderr=None, timeout=None):
            from PIL import Image
            args = dict(zip(command[1::2], command[2::2]))
            out, script = Path(args['--out']), Path(args['--script']).read_text()
            reads, images = fake_reads(script, flips)
            for name, in_pc in images.items():
                image = Image.new('RGB', (64, 48), (0, 0, 0))
                for x in range(64):
                    for y in range(48):
                        image.putpixel((x, y), ((x * 7 + (50 if in_pc and not tamper_images else 0)) % 256, y * 5 % 256, (x + y) * 3 % 256))
                image.save(out / name, format='PPM')
            for name in ('before-save.sav', 'after-save.sav'):
                if name in script:
                    (out / name).write_bytes(name.encode())
            stdout.write(''.join('READ 0x%08x 0x%x\n' % (a, v) for a, v in reads))
            stdout.flush()
            return types.SimpleNamespace(returncode=0)
        return types.SimpleNamespace(run=run, STDOUT=-2)

    def probe(self, case, flips=(), tamper_images=False, rom=None, cycles=50):
        self.counter += 1
        out = self.dir / ('run%d' % self.counter)
        self.run_probe.subprocess = self.fake_subprocess(flips, tamper_images)
        args = argparse.Namespace(rom=rom or self.rom, receipt=self.receipt_path, fixture=self.fixture,
                                  harness=self.harness, out=out, case=case, navigate=None, cycles=cycles)
        self.run_probe.probe(args)
        return out

    def test_bridge_prepared_run_is_accepted_and_scripts_are_limited(self):
        out = self.probe('bridge-prepared')
        result = self.verify_probe.verify(out, self.receipt_path)
        self.assertTrue(result['accepted'])
        verbs = set()
        for name in ('pass1', 'pass2', 'pass3'):
            for line in (out / name / 'commands.script').read_text().splitlines():
                if line.strip():
                    verbs.add(line.split()[0])
        self.assertLessEqual(verbs, {'run', 'tap', 'touch', 'capture', 'read', 'write', 'sram', 'status', 'quit'},
                             'no dump, no savestate, no debug command')
        writes = [l for n in ('pass1', 'pass2', 'pass3') for l in (out / n / 'commands.script').read_text().splitlines() if l.startswith('write')]
        self.assertEqual(set(writes), {'write 0x%08X 1 4' % (AREA + 0x0C)}, 'only `requested = 1`')
        self.assertEqual(self.dir.joinpath('rom.nds').read_bytes(), b'portable rom stand-in')

    def test_input_cycle_and_baseline_cases_are_accepted(self):
        for case in ('baseline', 'input-R', 'input-touch'):
            out = self.probe(case)
            self.assertTrue(self.verify_probe.verify(out, self.receipt_path)['accepted'], case)

    def test_cycle_input_and_save_cases_and_their_refusals(self):
        out = self.probe('cycle')
        self.assertEqual(self.verify_probe.verify(out, self.receipt_path)['cycles'], 50)
        out = self.probe('cycle', cycles=49)
        with self.assertRaises(self.verify_probe.Refusal):
            self.verify_probe.verify(out, self.receipt_path)               # fewer than 50 observations
        out = self.probe('cycle', flips=(lambda a, v, s, pc: v + 1 if a == AREA + 0x30 and s['opens'] == 30 else v,))
        with self.assertRaises(self.verify_probe.Refusal):
            self.verify_probe.verify(out, self.receipt_path)               # alloc/free imbalance at a rest point
        with self.assertRaises(self.run_probe.Refusal):
            self.probe('cycle', flips=(lambda a, v, s, pc: 0 if a == AREA + 8 and s['generation'] == 1 else v,))   # never bound
        out = self.probe('cycle', flips=(lambda a, v, s, pc: 1 if a == AREA + 0x0C and s['opens'] == 20 else v,))
        with self.assertRaises(self.verify_probe.Refusal):
            self.verify_probe.verify(out, self.receipt_path)               # progressive residue (a pending request)
        out = self.probe('cycle', flips=(lambda a, v, s, pc: 3 if a == AREA + 0x38 and s['opens'] == 25 else v,))
        with self.assertRaises(self.verify_probe.Refusal):
            self.verify_probe.verify(out, self.receipt_path)               # open count does not follow the cycles
        out = self.probe('input-R', flips=(lambda a, v, s, pc: 0 if a == AREA + 0x28 else v,))
        with self.assertRaises(self.verify_probe.Refusal):
            self.verify_probe.verify(out, self.receipt_path)               # suffix never shown
        out = self.probe('input-touch', flips=(lambda a, v, s, pc: 0 if a == AREA + 0x38 else v,))
        with self.assertRaises(self.verify_probe.Refusal):
            self.verify_probe.verify(out, self.receipt_path)               # request never reached the PC
        out = self.probe('save-continue')
        self.assertTrue(self.verify_probe.verify(out, self.receipt_path)['accepted'])
        (out / 'pass2' / 'after-save.sav').write_bytes((out / 'pass2' / 'before-save.sav').read_bytes())
        with self.assertRaises(self.verify_probe.Refusal):
            self.verify_probe.verify(out, self.receipt_path)               # SAVE changed nothing
        (out / 'pass2' / 'after-save.sav').unlink()
        with self.assertRaises(self.verify_probe.Refusal):
            self.verify_probe.verify(out, self.receipt_path)               # export missing

    def test_forged_receipt_and_structural_corruptions_are_refused(self):
        forged = dict(self.receipt, output_sha256=self.verify_probe.V4_SHA256['EN'])
        out, obs = self.mutated()
        obs['rom_sha256'] = self.verify_probe.V4_SHA256['EN']
        (out / 'observations.json').write_text(json.dumps(obs))
        self.receipt_path.write_text(json.dumps(forged))
        with self.assertRaises(self.verify_probe.Refusal):
            self.verify_probe.verify(out, self.receipt_path)               # canonical V4 even with a forged receipt
        self.receipt_path.write_text(json.dumps(self.receipt))
        cases = {
            'pass 3 differs from pass 2': lambda a, v, s, pc: 7 if s['_pass3'] and a == AREA + 0x20 else v,
            'party args still live in the PC phase': lambda a, v, s, pc: ARGS_ADDR if a == AREA + 0x18 and s['phase'] == 3 else v,
            'owner span moved': lambda a, v, s, pc: v,
        }
        for name, flip in list(cases.items())[:2]:
            with self.subTest(name):
                out = self.probe('bridge-prepared', flips=(flip,))
                with self.assertRaises(self.verify_probe.Refusal):
                    self.verify_probe.verify(out, self.receipt_path)
        out = self.probe('bridge-prepared')
        obs = json.loads((out / 'observations.json').read_text())
        for blanking in ('party.ppm', 'pc.ppm', 'party-after.ppm'):
            from PIL import Image
            saved = (out / 'pass2' / blanking).read_bytes()
            Image.new('RGB', (64, 48), (0, 0, 0)).save(out / 'pass2' / blanking, format='PPM')
            with self.assertRaises(self.verify_probe.Refusal):
                self.verify_probe.verify(out, self.receipt_path)           # blank capture
            (out / 'pass2' / blanking).write_bytes(saved)
        (out / 'pass2' / 'pc.ppm').unlink()
        with self.assertRaises(self.verify_probe.Refusal):
            self.verify_probe.verify(out, self.receipt_path)               # missing capture
        # restructured reads: a shorter record block is not a record
        out, obs = self.mutated()
        obs['pass3']['reads'] = [r for r in obs['pass3']['reads'] if r[0] != AREA + 0x3C]
        self.refuse(out, obs)
        out, obs = self.mutated()
        obs['pass2']['reads'] = []
        self.refuse(out, obs)
        out, obs = self.mutated()
        obs['pass1']['reads'] = []
        self.refuse(out, obs)

    def test_verdict_is_recomputed_from_the_runtime_log_not_from_observations(self):
        # coherent forged observations (every pass agrees) that the log does not support
        out, obs = self.mutated()
        def forge(reads):
            return [[a, v + 1 if a == AREA + 0x20 else v] for a, v in reads]       # selection differs in every pass
        for name in ('pass1', 'pass2', 'pass3'):
            obs[name]['reads'] = forge(obs[name]['reads'])
        self.refuse(out, obs)
        # a log edited after the run: the recorded hash no longer matches
        out, obs = self.mutated()
        log = out / 'pass2' / 'runtime.log'
        log.write_text(log.read_text() + 'READ 0x00000000 0x0\n')
        with self.assertRaises(self.verify_probe.Refusal):
            self.verify_probe.verify(out, self.receipt_path)
        # a missing log
        out, obs = self.mutated()
        (out / 'pass3' / 'runtime.log').unlink()
        with self.assertRaises(self.verify_probe.Refusal):
            self.verify_probe.verify(out, self.receipt_path)
        # fully fabricated: observations claim a PC phase that never appears in the real log
        out, obs = self.mutated('input-R', flips=(lambda a, v, s, pc: 1 if a == AREA + 8 and v == 3 else v,))
        with self.assertRaises(self.verify_probe.Refusal):
            self.verify_probe.verify(out, self.receipt_path)

    def rewrite_logs(self, out, obs, edit, passes=('pass2', 'pass3')):
        """Apply `edit(index, address, value) -> value` to the READ lines of the given passes and keep every hash and
        the observations consistent: a corruption that no hash or cross-check would reveal by itself."""
        for name in passes:
            log = out / name / 'runtime.log'
            lines, new, reads = log.read_text().splitlines(), [], []
            record = 0
            for line in lines:
                parts = line.split()
                if parts[0] == 'READ':
                    address, value = int(parts[1], 16), int(parts[2], 16)
                    record += address == AREA
                    value = edit(record, address, value)
                    line = 'READ 0x%08x 0x%x' % (address, value)
                    reads.append([address, value])
                new.append(line)
            log.write_text('\n'.join(new) + '\n')
            obs[name]['reads'] = reads
            obs[name]['log_sha256'] = hashlib.sha256(log.read_bytes()).hexdigest()
        (out / 'observations.json').write_text(json.dumps(obs))

    def test_log_consistent_corruptions_are_each_refused(self):
        cases = {
            'magic of a later record': lambda a, v: 0 if a == AREA else v,
            'phase out of range': lambda a, v: 9 if a == AREA + 8 else v,
            'request flag out of range': lambda a, v: 2 if a == AREA + 0x0C else v,
            'frees exceed allocs': lambda a, v: 7 if a == AREA + 0x34 else v,
            'pointer outside RAM': lambda a, v: 0x08000000 if a == AREA + 0x10 else v,
            'misaligned pointer': lambda a, v: 0x02311001 if a == AREA + 0x14 else v,
        }
        for name, fn in cases.items():
            with self.subTest(name):
                out, obs = self.mutated()
                # corrupt only records after the first two (the first feeds discovery and the cross-pass checks)
                self.rewrite_logs(out, obs, lambda record, address, value, fn=fn: fn(address, value) if record >= 3 else value)
                with self.assertRaises(self.verify_probe.Refusal):
                    self.verify_probe.verify(out, self.receipt_path)

    def test_unbound_first_record_and_extra_writes_are_refused_in_isolation(self):
        out, obs = self.mutated()
        self.rewrite_logs(out, obs, lambda record, address, value: 0 if address == AREA + 8 and record == 1 else value,
                          passes=('pass1', 'pass2', 'pass3'))
        with self.assertRaises(self.verify_probe.Refusal) as caught:
            self.verify_probe.verify(out, self.receipt_path)
        self.assertIn('not bound', str(caught.exception))
        out, obs = self.mutated()
        script = out / 'pass2' / 'commands.script'
        script.write_text(script.read_text() + 'write 0x%08X 4 4\n' % (AREA + 0x30))
        obs['pass2']['script_sha256'] = hashlib.sha256(script.read_bytes()).hexdigest()
        (out / 'observations.json').write_text(json.dumps(obs))
        with self.assertRaises(self.verify_probe.Refusal) as caught:
            self.verify_probe.verify(out, self.receipt_path)
        self.assertIn('may write only requested', str(caught.exception))

    def test_isolated_identity_and_log_hash_refusals(self):
        out, obs = self.mutated()
        log = out / 'pass2' / 'runtime.log'
        log.write_text(log.read_text() + '# trailing note that changes the hash but no READ line\n')
        with self.assertRaises(self.verify_probe.Refusal) as caught:
            self.verify_probe.verify(out, self.receipt_path)
        self.assertIn('runtime.log differs', str(caught.exception))
        out, obs = self.mutated()
        forged = dict(self.receipt, output_sha256=self.verify_probe.V4_SHA256['EN'])
        self.receipt_path.write_text(json.dumps(forged))
        obs['rom_sha256'] = self.verify_probe.V4_SHA256['EN']
        obs['receipt_sha256'] = hashlib.sha256(self.receipt_path.read_bytes()).hexdigest()
        (out / 'observations.json').write_text(json.dumps(obs))
        with self.assertRaises(self.verify_probe.Refusal) as caught:
            self.verify_probe.verify(out, self.receipt_path)
        self.assertIn('canonical V4', str(caught.exception))
        self.receipt_path.write_text(json.dumps(self.receipt))
        out, obs = self.mutated()
        obs['state_address'] = AREA + 0x40
        (out / 'observations.json').write_text(json.dumps(obs))
        with self.assertRaises(self.verify_probe.Refusal) as caught:
            self.verify_probe.verify(out, self.receipt_path)
        self.assertIn('record address', str(caught.exception))

    def test_input_cases_must_show_the_pc_and_must_not_write_requested(self):
        for case in ('input-R', 'input-touch'):
            out = self.probe(case)
            self.assertTrue(self.verify_probe.verify(out, self.receipt_path)['accepted'], case)
            for name in ('pass1', 'pass2', 'pass3'):
                script = (out / name / 'commands.script').read_text()
                self.assertNotIn('\nwrite ', script, 'the input path must not use the probe write')
            self.assertTrue((out / 'pass3').is_dir() and (out / 'pass2' / 'pc.ppm').is_file())
            # opens>=1 and prompt shown but no PC observation under the record: refused
            weak = self.probe(case, flips=(lambda a, v, s, pc: 1 if a == AREA + 8 and v == 3 else v,))
            with self.assertRaises(self.verify_probe.Refusal):
                self.verify_probe.verify(weak, self.receipt_path)
            # the input run is refused if its script wrote requested
            tampered, obs = self.mutated(case)
            script_path = tampered / 'pass2' / 'commands.script'
            script_path.write_text(script_path.read_text() + 'write 0x%08X 1 4\n' % (AREA + 0x0C))
            obs['pass2']['script_sha256'] = hashlib.sha256(script_path.read_bytes()).hexdigest()
            self.refuse(tampered, obs)
            # PCBoxArgs or callback altered
            for flip in (lambda a, v, s, pc: 1 if a == PC_ADDR + 8 else v,
                         lambda a, v, s, pc: 0 if a == OWNER_ADDR + 0x354 and pc else v):
                bad = self.probe(case, flips=(flip,))
                with self.assertRaises(self.verify_probe.Refusal):
                    self.verify_probe.verify(bad, self.receipt_path)

    def test_input_cases_must_contain_the_input_command(self):
        for case, drop in (('input-R', 'tap R 2 300\n'), ('input-touch', 'touch 148 176 2\nrun 300\n')):
            out, obs = self.mutated(case)
            script = out / 'pass2' / 'commands.script'
            script.write_text(script.read_text().replace(drop, 'run 300\n'))
            obs['pass2']['script_sha256'] = hashlib.sha256(script.read_bytes()).hexdigest()
            self.refuse(out, obs)
        for x, y in ((123, 176), (172, 176), (148, 167), (148, 184), (0, 0), (230, 170)):
            out, obs = self.mutated('input-touch')
            script = out / 'pass2' / 'commands.script'
            script.write_text(script.read_text().replace('touch 148 176 2', 'touch %d %d 2' % (x, y)))
            obs['pass2']['script_sha256'] = hashlib.sha256(script.read_bytes()).hexdigest()
            self.refuse(out, obs)
        out, obs = self.mutated('input-touch')       # a tap R in an input-touch script is not a touch in the box
        script = out / 'pass2' / 'commands.script'
        script.write_text(script.read_text().replace('touch 148 176 2', 'tap R 2 300'))
        obs['pass2']['script_sha256'] = hashlib.sha256(script.read_bytes()).hexdigest()
        self.refuse(out, obs)

    def test_overlay14_must_match_the_pinned_head(self):
        for word in range(4):
            out = self.probe('bridge-prepared', flips=(lambda a, v, s, pc, w=word: v ^ 1 if a == 0x021E5900 + 4 * w and pc else v,))
            with self.assertRaises(self.verify_probe.Refusal):
                self.verify_probe.verify(out, self.receipt_path)

    def test_unchanged_V4_capture_is_refused_as_a_remote_box(self):
        v4 = self.dir / 'v4.nds'
        v4.write_bytes(b'v4')
        with self.assertRaises(self.run_probe.Refusal):
            self.probe('bridge-prepared', rom=v4)                          # ROM differs from the install receipt
        out = self.probe('bridge-prepared')
        obs = json.loads((out / 'observations.json').read_text())
        for language, digest in self.verify_probe.V4_SHA256.items():
            obs['rom_sha256'] = digest
            (out / 'observations.json').write_text(json.dumps(obs))
            with self.assertRaises(self.verify_probe.Refusal):
                self.verify_probe.verify(out, self.receipt_path)
        # an unchanged V4 ROM has no record: the first read shows no magic and the probe stops at discovery
        with self.assertRaises(self.run_probe.Refusal):
            self.probe('bridge-prepared', flips=(lambda a, v, s, pc: 0 if AREA <= a < AREA + 4 else v,))

    def mutated(self, case='bridge-prepared', **kw):
        out = self.probe(case, **kw)
        return out, json.loads((out / 'observations.json').read_text())

    def refuse(self, out, obs):
        (out / 'observations.json').write_text(json.dumps(obs))
        with self.assertRaises(self.verify_probe.Refusal):
            self.verify_probe.verify(out, self.receipt_path)

    def test_pc_looking_image_without_pc_state_is_refused(self):
        # the run never shows phase PC_RUNNING under the record: only a PC-like picture
        out = self.probe('bridge-prepared', flips=(lambda a, v, s, pc: 1 if a == AREA + 8 and v == 3 else v,))
        with self.assertRaises(self.verify_probe.Refusal):
            self.verify_probe.verify(out, self.receipt_path)

    def test_corrupted_synthetic_results_are_refused(self):
        cases = {
            'mode is not 2': lambda a, v, s, pc: 1 if a == PC_ADDR + 8 else v,
            'wrong exit callback': lambda a, v, s, pc: 0x0203CA9D if a == OWNER_ADDR + 0x354 else v,
            'overlay 14 absent': lambda a, v, s, pc: 0 if a == 0x021E5900 else v,
            'exit environment is not the PC args': lambda a, v, s, pc: ARGS_ADDR if a == OWNER_ADDR + 0x380 else v,
            'pointer outside RAM': lambda a, v, s, pc: 0x08000000 if a == AREA + 0x14 else v,
            'frees exceed allocs': lambda a, v, s, pc: 9 if a == AREA + 0x34 else v,
            'generation backwards': lambda a, v, s, pc: 0 if a == AREA + 4 and s['generation'] == 2 else v,
            'phase out of range': lambda a, v, s, pc: 9 if a == AREA + 8 and v == 3 else v,
            'leak after the PC': lambda a, v, s, pc: 5 if a == AREA + 0x30 and s['phase'] == 1 and s['generation'] == 2 else v,
        }
        for name, flip in cases.items():
            with self.subTest(name):
                out = self.probe('bridge-prepared', flips=(flip,))
                with self.assertRaises(self.verify_probe.Refusal):
                    self.verify_probe.verify(out, self.receipt_path)
        out, obs = self.mutated(tamper_images=True)
        with self.assertRaises(self.verify_probe.Refusal):
            self.verify_probe.verify(out, self.receipt_path)               # PC capture equals the party capture

    def test_tampered_run_directories_are_refused(self):
        out, obs = self.mutated()
        edits = {
            'receipt hash': lambda o: o.update(receipt_sha256='0' * 64),
            'language': lambda o: o.update(language='IT'),
            'record address': lambda o: o.update(state_address=AREA + 4),
            'owner discovery': lambda o: o['discovered'].update(owner=OWNER_ADDR + 4),
            'pc words': lambda o: o.update(pc_args_words=[1, 2, 2]),
            'third pass': lambda o: o.update(pass3=None),
            'rom hash': lambda o: o.update(rom_sha256='1' * 64),
        }
        for name, edit in edits.items():
            with self.subTest(name):
                out, obs = self.mutated()
                edit(obs)
                self.refuse(out, obs)
        out, obs = self.mutated()
        (out / 'pass2' / 'commands.script').write_text('quit\n')
        with self.assertRaises(self.verify_probe.Refusal):
            self.verify_probe.verify(out, self.receipt_path)               # altered script

    def test_run_probe_refuses_existing_output_unknown_case_and_wrong_rom(self):
        out = self.probe('baseline')
        with self.assertRaises(Exception):
            self.run_probe.probe(argparse.Namespace(rom=self.rom, receipt=self.receipt_path, fixture=self.fixture,
                                                    harness=self.harness, out=out, case='baseline', navigate=None, cycles=1))
        with self.assertRaises(self.run_probe.Refusal):
            self.probe('no-such-case')
        wrong = self.dir / 'other.nds'
        wrong.write_bytes(b'other')
        with self.assertRaises(self.run_probe.Refusal):
            self.probe('baseline', rom=wrong)


if __name__ == '__main__':
    unittest.main()
