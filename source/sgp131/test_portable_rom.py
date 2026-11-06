"""Class B: the installer on the real V4 EN/IT ROMs, in memory only (nothing is written to disk).

Inputs are the private candidate ROMs; a missing input skips with a reason, and
SGP_PORTABLE_REQUIRE_INPUTS=1 turns the skip into a failure. A present input with the wrong
sha256 always fails. The compartment base comes from a reserve.allocate-shaped receipt under a
DECLARED test policy (portable_bench.declared_reserve: the slot of reserve-map.json, own version
and digest, refused by the real policy); the real policy cannot grant it yet.

  PYTHONPATH=source SGP_PORTABLE_REQUIRE_INPUTS=1 python -m unittest sgp131.test_portable_rom -v
"""
import copy
import hashlib
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

from sgp12.rom import bl_decode
from sgp131 import portable
from sgp131 import test_controls as _test_controls

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'source/features/portable-box/test'))
import portable_bench as pb  # noqa: E402
CANDIDATES = ROOT / 'local' / 'experiments' / 'balance493-2026-10-28'
INPUTS = {'EN': (os.environ.get('SGP_PORTABLE_ROM_EN') or CANDIDATES / 'candidate-v4-EN.nds', portable.V4_SHA256['EN']),
          'IT': (os.environ.get('SGP_PORTABLE_ROM_IT') or CANDIDATES / 'candidate-v4-IT.nds', portable.V4_SHA256['IT'])}
REQUIRE = os.environ.get('SGP_PORTABLE_REQUIRE_INPUTS') == '1'
LANGUAGES = ('EN', 'IT')
_ROMS, _INSTALLED = {}, {}


def rom(test, language):
    path, digest = INPUTS[language]
    path = Path(path)
    if not path.is_file():
        reason = '%s V4 input not present: %s' % (language, path)
        if REQUIRE:
            test.fail(reason)
        test.skipTest(reason)
    if language not in _ROMS:
        data = path.read_bytes()
        test.assertEqual(hashlib.sha256(data).hexdigest(), digest, language + ' input identity')
        _ROMS[language] = data
    return _ROMS[language]


PROOF = {'sha256': hashlib.sha256(b'synthetic unit-test context proof').hexdigest(),
         'origin': 'unit test fixture (synthetic, not a measurement)', 'status': 'synthetic'}
ACTIVE = dict(bridge=1, input=1, prompt=1)
CANDIDATE = hashlib.sha256(b'fixture: the inert candidate ROM of the portable installer test').hexdigest()


def measured_proof(language='EN', candidate=CANDIDATE):
    """A capture-shaped fixture (NOT real evidence), bound to a fixture candidate and a language."""
    return dict(PROOF, status='measured', origin='Android capture of the composed candidate, campaign receipt',
                capture_file='captures/portable-context.json', build_id='candidate-example-build',
                capture_rom_sha256=candidate, language=language)


def install(data, language, work, activation=None, defaults=True, v4=None, **kwargs):
    """portable.prepare under the declared test policy, with the declared slot and its preimage. `defaults`
    adds the synthetic proof the installed fixtures need to activate; refusal tests pass defaults=False."""
    if defaults and activation and any(activation.get(k) for k in ('bridge', 'input', 'prompt')):
        kwargs.setdefault('context_proof', PROOF)
        kwargs.setdefault('allow_synthetic_proof', True)
    if kwargs.get('context_proof') is not None:
        kwargs.setdefault('candidate_sha256', CANDIDATE)
    kwargs.setdefault('allocation', pb.declared_allocation(language))
    kwargs.setdefault('preimage_sha256', pb.preimage_of(v4 if v4 is not None else rom_for(language)))
    with pb.declared_reserve():
        return portable.prepare(data, language, work, activation=activation, **kwargs)


def rom_for(language):
    return _ROMS[language]


def verify(*args, **kwargs):
    with pb.declared_reserve():
        return portable.verify(*args, **kwargs)


def installed(test, language, activation=None):
    key = (language, tuple(sorted((activation or {}).items())))
    if key not in _INSTALLED:
        data = rom(test, language)
        with tempfile.TemporaryDirectory() as work:
            out, receipt = install(data, language, work, activation)
        _INSTALLED[key] = (data, out, receipt)
    return _INSTALLED[key]


class Pins(unittest.TestCase):
    def test_audit_accepts_both_inputs_and_they_agree(self):
        reports = {language: portable.audit_native(rom(self, language), language) for language in LANGUAGES}
        self.assertEqual({k: v for k, v in reports['EN'].items() if k != 'language'},
                         {k: v for k, v in reports['IT'].items() if k != 'language'}, 'every pinned span is identical in EN and IT')
        self.assertGreaterEqual(len(reports['EN']['spans']), 20)

    def test_audit_rejects_a_changed_byte_in_every_pinned_span(self):
        data = rom(self, 'EN')
        segments = portable.arm9_segments(data)
        for name, span in portable.abi()['languages']['EN']['spans'].items():
            broken = bytearray(data)
            at = portable.locate(segments, span['address'], 1)
            broken[at] ^= 0x01
            with self.assertRaises(ValueError, msg=name):
                portable.audit_native(bytes(broken), 'EN')
        for name, native in portable.abi()['languages']['EN']['natives'].items():
            broken = bytearray(data)
            broken[portable.locate(segments, native['address'], 1)] ^= 0x01
            with self.assertRaises(ValueError, msg=name):
                portable.audit_native(bytes(broken), 'EN')

    def test_font_prompt_geometry_fits_with_the_real_font_widths(self):
        """Window 160x16, suffix at local x 112: widths come from the real font (member[-510:-1])."""
        import ndspy.narc
        import ndspy.rom
        charmap_path = ROOT / 'local/tools/pokeheartgold/charmap.txt'
        if not charmap_path.is_file():
            reason = 'pret charmap not present: %s' % charmap_path
            if REQUIRE:
                self.fail(reason)
            self.skipTest(reason)
        charmap = {}
        for line in charmap_path.read_text(encoding='utf8').splitlines():
            if '=' in line and not line.startswith('//'):
                key, value = line.lstrip().split('=', 1)
                if len(key) == 4:
                    charmap.setdefault(value, int(key, 16))
        for language, prompt in (('EN', 'Choose a Pokémon.'), ('IT', 'Scegli un Pokémon.')):
            data = rom(self, language)
            archive = ndspy.narc.NARC(ndspy.rom.NintendoDSRom(data).getFileByName('a/0/1/6'))
            member = archive.files[1]                                   # font id 1
            widths = member[-510:-1]
            width = lambda text: sum(widths[charmap[c]] for c in text)
            self.assertEqual(hashlib.sha256(member).hexdigest()[:16], '9a17de3036f4aac8')
            self.assertEqual(member, archive.files[0], 'font 0 and font 1 are the same member')
            self.assertEqual(width(prompt), {'EN': 97, 'IT': 98}[language])
            self.assertEqual(width('R: Box'), 33)
            self.assertLess(width(prompt), 112 - 8, 'a clear gap before the suffix')
            self.assertLessEqual(112 + width('R: Box'), 160 - 8, 'margin inside the 160 px window')
            # screen coordinates: window origin (16,168); hitbox [124,172) x [168,184); Cancel touch starts at x 200
            self.assertTrue(16 + 112 >= 124 + 4 and 16 + 112 + 33 <= 172, 'suffix lies inside the hitbox')
            self.assertLess(172, 200 - 8, 'hitbox is separated from Cancel')


class Install(unittest.TestCase):
    def test_only_owned_ranges_change_and_hooks_decode(self):
        for language in LANGUAGES:
            data, out, receipt = installed(self, language)
            self.assertEqual(len(out), len(data))
            changed = portable._changed(data, out)
            segments = portable.arm9_segments(out)
            owned = set()
            for start, length in receipt['write_ranges']:
                at = portable.locate(segments, start, length)
                owned.update(range(at, at + length))
            self.assertTrue(changed and set(changed) <= owned)
            self.assertEqual(len(receipt['write_ranges']), 5)
            for name, hook in receipt['hooks'].items():
                site = hook['site']
                self.assertEqual(bl_decode(site, portable.read_ram(out, segments, site, 4)), hook['new_target'])
                self.assertEqual(bl_decode(site, portable.read_ram(data, segments, site, 4)), hook['old_target'])
            verdict = verify(data, out, receipt)
            self.assertEqual((verdict['verified'], verdict['stray_bytes']), (True, 0))
            self.assertEqual(receipt['config']['values'],
                             {'bridge': 0, 'input': 0, 'prompt': 0, 'travel_mask': 3, 'context_proof': 0})
            self.assertIsNone(receipt['context_proof'])
            self.assertEqual(receipt['assignment']['name'], portable.SLOT_NAME)
            self.assertEqual((receipt['base'], receipt['function_state']), (pb.SLOT_START, 'inert'))
            self.assertEqual((receipt['candidate_sha256'], receipt['capture_rom_sha256'], receipt['candidate_relation']),
                             (None, None, None))

    def test_install_is_deterministic_and_activation_changes_only_config_words(self):
        for language in LANGUAGES:
            data, out, receipt = installed(self, language)
            _, active, active_receipt = installed(self, language, ACTIVE)
            diffs = [i for i, (a, b) in enumerate(zip(out, active)) if a != b]
            self.assertEqual(len(diffs), 4, 'bridge, input, prompt and context_proof words, nothing else')
            with tempfile.TemporaryDirectory() as work:
                again, _ = install(data, language, work)
            self.assertEqual(again, out)
            self.assertEqual(active_receipt['config']['values']['input'], 1)
            self.assertEqual(verify(data, active, active_receipt, require_measured=False)['activation']['prompt'], 1)

    def test_en_and_it_payloads_are_identical(self):
        en, it = installed(self, 'EN')[2], installed(self, 'IT')[2]
        self.assertEqual(en['compartment']['payload_sha256'], it['compartment']['payload_sha256'])
        self.assertEqual(en['symbols'], it['symbols'])
        self.assertLessEqual(en['compartment']['bytes'], 4096)

    def test_no_file_is_left_in_the_work_directory(self):
        data = rom(self, 'EN')
        with tempfile.TemporaryDirectory() as work:
            install(data, 'EN', work)
            self.assertEqual(list(Path(work).iterdir()), [])


class Refusals(unittest.TestCase):
    def test_base_comes_only_from_a_reserve_receipt_and_the_preimage_is_enforced(self):
        data, out, receipt = installed(self, 'EN')
        pre = receipt['compartment']['preimage_sha256']
        alloc = pb.declared_allocation('EN')
        with tempfile.TemporaryDirectory() as work, pb.declared_reserve():
            with self.assertRaises(ValueError):
                portable.prepare(data, 'EN', work, allocation=None, preimage_sha256=pre)
            with self.assertRaises(TypeError):
                portable.prepare(data, 'EN', work, preimage_sha256=pre)              # allocation: keyword-only, required
            with self.assertRaises(TypeError):
                portable.prepare(data, 'EN', work, allocation=alloc)                  # preimage: keyword-only, required
            with self.assertRaises(TypeError):
                portable.prepare(data, 'EN', work, base=pb.SLOT_START, preimage_sha256=pre)   # the free-form base is gone
            for name, bad in (('free-form dict', {'start': pb.SLOT_START, 'bytes': pb.SLOT_BYTES, 'name': portable.SLOT_NAME}),
                              ('integer address', pb.SLOT_START), ('other language', pb.declared_allocation('IT')),
                              ('moved', pb.declared_allocation('EN', assignments=[dict(alloc['assignments'][0], start=pb.SLOT_START + 4)])),
                              ('too small for the compartment', pb.declared_allocation(
                                  'EN', size=1024, requested={portable.SLOT_NAME: 1024},
                                  assignments=[dict(alloc['assignments'][0], bytes=1024)]))):
                with self.subTest(name), self.assertRaises(ValueError):
                    portable.prepare(data, 'EN', work, allocation=bad, preimage_sha256=pre)
            small = pb.declared_allocation('EN', size=1024, requested={portable.SLOT_NAME: 1024},
                                           assignments=[dict(alloc['assignments'][0], bytes=1024)])
            with self.assertRaisesRegex(ValueError, 'exceeds the reserve assignment'):
                portable.prepare(data, 'EN', work, allocation=small, preimage_sha256=pre)
            for bad_pre in ('0' * 64, '', None, 'zz' * 32, pre[:-1], pre.upper() + '0'):
                with self.assertRaises(ValueError):
                    portable.prepare(data, 'EN', work, allocation=alloc, preimage_sha256=bad_pre)
            for bad_candidate in ('ABC', 'a' * 63, 'A' * 64, 7):
                with self.assertRaisesRegex(ValueError, 'candidate_sha256 must be'):
                    portable.prepare(data, 'EN', work, allocation=alloc, preimage_sha256=pre, candidate_sha256=bad_candidate)
            out2, _ = portable.prepare(data, 'EN', work, allocation=alloc, preimage_sha256=pre)
            self.assertEqual(out2, out)
            for language in ('FR', '', None):
                with self.assertRaises(ValueError):
                    portable.prepare(data, language, work, allocation=alloc, preimage_sha256=pre)
            for activation in ({'unknown': 1}, {'bridge': 2}, {'travel_mask': -1}, {'travel_mask': 256}, {'context_proof': 1}):
                with self.assertRaises(ValueError):
                    portable.prepare(data, 'EN', work, allocation=alloc, preimage_sha256=pre, activation=activation)

    def test_the_real_policy_refuses_the_installer_today(self):
        """No test double: the product map cannot grant portable-box.runtime, and a genuine receipt of another owner
        does not help. This is the fail-closed state until Codex lifts the conditional owner (INTEGRATION.md)."""
        from sgp131 import reserve
        data, _out, receipt = installed(self, 'EN')
        pre = receipt['compartment']['preimage_sha256']
        with pb.real_reserve():
            with self.assertRaisesRegex(ValueError, 'conditional'):
                reserve.allocate(data, {portable.SLOT_NAME: 3024})                  # the allocator itself refuses
            genuine = reserve.allocate(data, {'training.ui': 1536})                # a real receipt, for somebody else
            self.assertEqual(portable.check_allocation(genuine, 'EN', 'training.ui')['start'], 0x023D6800)
            with tempfile.TemporaryDirectory() as work:
                for allocation in (genuine, pb.declared_allocation('EN')):
                    with self.subTest(requested=sorted(allocation['requested'])), self.assertRaises(ValueError):
                        portable.prepare(data, 'EN', work, allocation=allocation, preimage_sha256=pre)

    def test_activation_needs_a_context_proof_and_a_coherent_word_set(self):
        data, out, receipt = installed(self, 'EN')
        real = measured_proof('EN')
        def prepare(activation, **kw):
            with tempfile.TemporaryDirectory() as work:
                return install(data, 'EN', work, activation, defaults=False, **kw)
        for activation in (dict(bridge=1), dict(input=1, bridge=1), dict(bridge=1, input=1, prompt=1)):
            with self.assertRaises(ValueError, msg='no proof: %r' % activation):
                prepare(activation)
            with self.assertRaises(ValueError, msg='synthetic proof without the test switch'):
                prepare(activation, context_proof=PROOF, allow_synthetic_proof=False)
        # a measured proof is accepted; the word and the receipt carry it, with the candidate it is bound to
        out_real, receipt_real = prepare(dict(bridge=1, input=1, prompt=1), context_proof=real)
        self.assertEqual(receipt_real['config']['values']['context_proof'], 1)
        self.assertEqual(receipt_real['context_proof'], dict(real, accepted_as='measured'))
        self.assertEqual((receipt_real['candidate_sha256'], receipt_real['capture_rom_sha256'], receipt_real['function_state']),
                         (CANDIDATE, CANDIDATE, 'active'))
        self.assertEqual(verify(data, out_real, receipt_real)['context_proof'], 'measured')
        _, receipt_syn = prepare(dict(bridge=1), context_proof=PROOF, allow_synthetic_proof=True)
        self.assertEqual(receipt_syn['context_proof']['accepted_as'], 'synthetic-for-test')
        self.assertIsNone(receipt_syn['capture_rom_sha256'])
        # C3: the proof is bound to the candidate that was captured and to the language
        with self.assertRaisesRegex(ValueError, 'another ROM'):
            prepare(dict(bridge=1), context_proof=real, candidate_sha256=hashlib.sha256(b'other ROM').hexdigest())
        with self.assertRaisesRegex(ValueError, 'candidate_sha256'):
            with tempfile.TemporaryDirectory() as work, pb.declared_reserve():
                portable.prepare(data, 'EN', work, allocation=pb.declared_allocation('EN'), preimage_sha256=pb.preimage_of(data),
                                 activation=dict(bridge=1), context_proof=real)
        with self.assertRaisesRegex(ValueError, 'another language'):
            prepare(dict(bridge=1), context_proof=measured_proof('IT'))
        for lacking in ('capture_file', 'capture_rom_sha256', 'build_id', 'language'):
            incomplete = {k: v for k, v in real.items() if k != lacking}
            with self.assertRaises(ValueError, msg='a measured proof lacks ' + lacking):
                prepare(dict(bridge=1), context_proof=incomplete)
        for bad_field in (dict(real, capture_rom_sha256='abc'), dict(real, capture_rom_sha256='A' * 64), dict(real, capture_file=''),
                          dict(real, build_id=' '), dict(real, capture_file=3)):
            with self.assertRaises(ValueError, msg=repr(bad_field)):
                prepare(dict(bridge=1), context_proof=bad_field)
        for bad in (None, {}, dict(real, sha256='abc'), dict(real, sha256='G' * 64), dict(real, origin=''), dict(real, origin=3),
                    dict(real, status='measure'), dict(real, status=None), dict(real, extra=1), 'proof'):
            with self.assertRaises(ValueError, msg=repr(bad)):
                prepare(dict(bridge=1), context_proof=bad)
        # incoherent word sets: a label or a key that triggers nothing
        for activation in (dict(prompt=1), dict(prompt=1, bridge=1), dict(prompt=1, input=1), dict(input=1)):
            with self.assertRaises(ValueError, msg=repr(activation)):
                prepare(activation, context_proof=real)
        # an inert install may carry a proof (the word stays recorded) but activates nothing
        _, inert = prepare(None, context_proof=real)
        self.assertEqual((inert['config']['values']['bridge'], inert['config']['values']['context_proof']), (0, 1))
        self.assertEqual(inert['function_state'], 'inert')

    def test_a_candidate_that_is_the_stage_inert_output_is_recognised_from_the_bytes(self):
        data = rom(self, 'EN')
        with tempfile.TemporaryDirectory() as work:
            inert, _r = install(data, 'EN', work)
            stage_candidate = hashlib.sha256(inert).hexdigest()
            out, receipt = install(data, 'EN', work, dict(bridge=1), context_proof=measured_proof('EN', stage_candidate),
                                   candidate_sha256=stage_candidate)
        self.assertEqual(receipt['candidate_relation'], 'stage-inert-output')
        self.assertEqual(verify(data, out, receipt)['candidate_relation'], 'stage-inert-output')
        with self.assertRaisesRegex(ValueError, 'candidate relation'):
            verify(data, out, dict(receipt, candidate_relation='composed-candidate'))
        # the usual case: the candidate is a composed ROM, which this module cannot recompute
        with tempfile.TemporaryDirectory() as work:
            out2, receipt2 = install(data, 'EN', work, dict(bridge=1), context_proof=measured_proof('EN'))
        self.assertEqual(receipt2['candidate_relation'], 'composed-candidate')
        verify(data, out2, receipt2)

    def test_function_state_is_explicit_and_recomputed_from_the_installed_bytes(self):
        for activation in (None, ACTIVE):
            data, out, receipt = installed(self, 'EN', activation)
            state = 'active' if activation else 'inert'
            self.assertEqual(receipt['function_state'], state)
            for forged in (dict(receipt, function_state='inert' if activation else 'active'), dict(receipt, function_state=None),
                           {k: v for k, v in receipt.items() if k != 'function_state'}):
                with self.assertRaisesRegex(ValueError, 'function_state'):
                    verify(data, out, forged, require_measured=False)
            # flip the installed bridge word, keep every hash consistent: the bytes win over the receipt
            segments = portable.arm9_segments(out)
            at = portable.locate(segments, receipt['config']['address'] + portable.CONFIG_OFFSETS['bridge'], 4)
            bad = bytearray(out)
            bad[at:at + 4] = (0 if activation else 1).to_bytes(4, 'little')
            comp = receipt['compartment']
            forged = copy.deepcopy(receipt)
            forged['output_sha256'] = hashlib.sha256(bytes(bad)).hexdigest()
            forged['compartment']['payload_sha256'] = hashlib.sha256(
                portable.read_ram(bytes(bad), segments, comp['start'], comp['bytes'])).hexdigest()
            with self.assertRaises(ValueError):
                verify(data, bytes(bad), forged, require_measured=False)

    def test_verify_rechecks_the_reserve_allocation_of_the_receipt(self):
        data, out, receipt = installed(self, 'EN')
        allocation = receipt['allocation']
        cases = {'no allocation': {k: v for k, v in receipt.items() if k != 'allocation'},
                 'other policy digest': dict(receipt, allocation=dict(allocation, policy_sha256='1' * 64)),
                 'other language': dict(receipt, allocation=pb.declared_allocation('IT')),
                 'assignment moved': dict(receipt, assignment=dict(receipt['assignment'], start=receipt['assignment']['start'] + 4)),
                 'base moved': dict(receipt, base=receipt['base'] + 4)}
        for name, forged in cases.items():
            with self.subTest(name), self.assertRaises((ValueError, KeyError, TypeError)):
                verify(data, out, forged)
        with pb.real_reserve(), self.assertRaisesRegex(ValueError, 'policy in force'):
            portable.verify(data, out, receipt)           # made under the test double: the real policy refuses it

    def test_receipts_carry_no_process_state(self):
        for activation in (None, ACTIVE):
            _d, _o, receipt = installed(self, 'IT', activation)
            blob = json.dumps(receipt, sort_keys=True)
            for word in ('SOURCE_READY', 'ANDROID', 'android', 'not run', "'status': 'SOURCE"):
                self.assertNotIn(word, blob, word)

    def test_wrong_preimages_are_rejected_before_any_output(self):
        data, out, receipt = installed(self, 'EN')
        segments = portable.arm9_segments(data)
        for site in (portable.STATE1_BL, portable.LAUNCH_BL, portable.PRINT32_BL, portable.CALLBACK, 0x0203E868, 0x0207DA64):
            broken = bytearray(data)
            broken[portable.locate(segments, site, 1)] ^= 0x01
            with tempfile.TemporaryDirectory() as work:
                with self.assertRaises(ValueError):
                    install(bytes(broken), 'EN', work, preimage_sha256=receipt['compartment']['preimage_sha256'])
        with tempfile.TemporaryDirectory() as work:
            with self.assertRaises(ValueError):
                install(out, 'EN', work, preimage_sha256=receipt['compartment']['preimage_sha256'])     # already installed: not the pinned bytes

    def test_verify_rejects_tampering(self):
        for language in LANGUAGES:
            data, out, receipt = installed(self, language)
            segments = portable.arm9_segments(out)
            targets = {'compartment byte': receipt['base'] + 0x70, 'bl hook': portable.STATE1_BL,
                       'callback hook literal': portable.CALLBACK + 4, 'trampoline': receipt['compartment']['trampoline'] + 4,
                       'config word': receipt['config']['address'] + 4, 'state magic': receipt['state']['address']}
            for name, address in targets.items():
                with self.subTest(language=language, tamper=name):
                    bad = bytearray(out)
                    bad[portable.locate(segments, address, 1)] ^= 0x7F
                    broken = dict(receipt, output_sha256=hashlib.sha256(bytes(bad)).hexdigest())
                    with self.assertRaises(ValueError):
                        verify(data, bytes(bad), broken)
            stray = bytearray(out)
            stray[portable.locate(segments, 0x0203E000, 1)] ^= 0xFF
            with self.assertRaises(ValueError):
                verify(data, bytes(stray), dict(receipt, output_sha256=hashlib.sha256(bytes(stray)).hexdigest()))
            with self.assertRaises(ValueError):
                verify(data, out, dict(receipt, input_sha256='0' * 64))
            with self.assertRaises(ValueError):
                verify(data, out, dict(receipt, output_sha256='0' * 64))

    def test_verify_refuses_a_synthetic_proof_unless_the_caller_is_a_test(self):
        for language in LANGUAGES:
            data, out, receipt = installed(self, language, ACTIVE)
            self.assertEqual(receipt['context_proof']['accepted_as'], 'synthetic-for-test')
            with self.assertRaises(ValueError):
                verify(data, out, receipt)                       # default: measured proofs only
            with self.assertRaises(ValueError):
                verify(data, out, receipt, require_measured=True)
            self.assertEqual(verify(data, out, receipt, require_measured=False)['context_proof'], 'synthetic-for-test')
            forged = copy.deepcopy(receipt)
            forged['context_proof']['accepted_as'] = 'measured'            # relabelled receipt: its form no longer validates
            with self.assertRaises(ValueError):
                verify(data, out, forged)
            data, out, inert = installed(self, language)
            self.assertIsNone(verify(data, out, inert)['context_proof'])

    def test_verify_rejects_a_forged_but_self_consistent_receipt(self):
        """A tampered image whose receipt hashes were recomputed must still fail the independent readback."""
        for language in LANGUAGES:
            data, out, receipt = installed(self, language)
            segments = portable.arm9_segments(out)
            comp = receipt['compartment']
            for name, address in (('compiled code', receipt['base'] + 0x70), ('trampoline', comp['trampoline'] + 4),
                                  ('config word', receipt['config']['address'] + 4)):
                with self.subTest(language=language, tamper=name):
                    bad = bytearray(out)
                    bad[portable.locate(segments, address, 1)] ^= 0x5A
                    forged = copy.deepcopy(receipt)
                    forged['output_sha256'] = hashlib.sha256(bytes(bad)).hexdigest()
                    forged['compartment']['payload_sha256'] = hashlib.sha256(
                        portable.read_ram(bytes(bad), segments, comp['start'], comp['bytes'])).hexdigest()
                    with self.assertRaises(ValueError):
                        verify(data, bytes(bad), forged, require_measured=False)


class Composition(unittest.TestCase):
    """The portable box pins hook-site intervals only: it composes after a stage that leaves them alone."""

    @staticmethod
    def earlier_stage(data):
        """Synthetic earlier stage: the UI's ARM9 footprint (sgp131/ui.py, byte for byte as written) filled with
        arbitrary bytes, plus a longer cartridge. A declared test double, not the UI."""
        out = bytearray(data)
        segments = portable.arm9_segments(data)
        for name, start, size in _test_controls.Intervals.UI_WRITES:
            at = portable.locate(segments, start, size)
            out[at:at + size] = hashlib.shake_128(name.encode()).digest(size)
        out += hashlib.shake_128(b'appended cartridge tail').digest(4096)
        return bytes(out)

    def test_installs_and_verifies_after_the_ui_footprint(self):
        for language in LANGUAGES:
            data = rom(self, language)
            stage = self.earlier_stage(data)
            self.assertNotEqual(stage, data)
            with self.subTest(language=language), tempfile.TemporaryDirectory() as work:
                out, receipt = install(stage, language, work)
                self.assertEqual(verify(stage, out, receipt)['stray_bytes'], 0)
                self.assertEqual(receipt['input_sha256'], hashlib.sha256(stage).hexdigest())
                changed = portable._changed(stage, out)
                segments = portable.arm9_segments(out)
                owned = set()
                for start, length in receipt['write_ranges']:
                    at = portable.locate(segments, start, length)
                    owned.update(range(at, at + length))
                self.assertTrue(changed and set(changed) <= owned)

    def test_refuses_a_stage_that_touched_a_pinned_interval(self):
        data = rom(self, 'EN')
        segments = portable.arm9_segments(data)
        pins = portable.abi()['languages']['EN']
        sites = [(name, span['address'], span['bytes']) for name, span in pins['spans'].items()]
        sites += [(name, native['address'], native['prefix_bytes']) for name, native in pins['natives'].items()]
        self.assertGreater(len(sites), 30)
        for name, address, size in sites:
            for position in (address, address + size - 1):
                with self.subTest(interval=name, at=hex(position)):
                    touched = bytearray(self.earlier_stage(data))
                    touched[portable.locate(segments, position, 1)] ^= 0x01
                    with self.assertRaisesRegex(ValueError, 'mismatch'):
                        portable.audit_native(bytes(touched), 'EN')


class PostReview(unittest.TestCase):
    """Corrections after K-review: I3 candidate gate, I5 independent preimage, M1 forged fields, M5 compiler pin."""

    def active(self, data, candidate=CANDIDATE, language='EN'):
        with tempfile.TemporaryDirectory() as work:
            return install(data, language, work, dict(bridge=1), context_proof=measured_proof(language, candidate),
                           candidate_sha256=candidate)

    def test_the_final_candidate_gate_refuses_an_invented_candidate(self):
        data = rom(self, 'EN')
        invented = 'ab' * 32
        out, receipt = self.active(data, invented)
        self.assertEqual(receipt['candidate_relation'], 'composed-candidate', 'the installer alone cannot tell')
        with self.assertRaisesRegex(ValueError, 'not the candidate'):
            portable.candidate_gate(out, receipt)
        genuine = hashlib.sha256(portable.inert_view(out, receipt)).hexdigest()
        out2, receipt2 = self.active(data, genuine)
        self.assertEqual(out2, out)
        portable.candidate_gate(out2, receipt2)
        with self.assertRaisesRegex(ValueError, 'no candidate'):
            portable.candidate_gate(out2, dict(receipt2, candidate_sha256=None))

    def test_inert_view_clears_only_the_four_activation_words_and_is_pure(self):
        data, out, receipt = installed(self, 'EN', ACTIVE)
        snapshot = bytes(out)
        view = portable.inert_view(out, receipt)
        self.assertEqual(out, snapshot)
        segments = portable.arm9_segments(out)
        words = [portable.locate(segments, receipt['config']['address'] + portable.CONFIG_OFFSETS[k], 4)
                 for k in ('bridge', 'input', 'prompt', 'context_proof')]
        changed = portable._changed(out, view)
        self.assertTrue(changed and set(changed) <= {w + i for w in words for i in range(4)})
        self.assertEqual(portable.inert_view(view, receipt), view, 'idempotent')
        _d, inert, inert_receipt = installed(self, 'EN')
        self.assertEqual(portable.inert_view(inert, inert_receipt), inert, 'an inert image is its own view')
        self.assertEqual(view, inert, 'the inert view of the active image is the inert install of the same stage')
        # travel_mask is configuration, not activation: it survives the view
        at = portable.locate(segments, receipt['config']['address'] + portable.CONFIG_OFFSETS['travel_mask'], 4)
        self.assertEqual(view[at:at + 4], out[at:at + 4])

    def test_the_expected_preimage_comes_from_the_v4_not_from_the_stage_input(self):
        v4 = rom(self, 'EN')
        allocation = pb.declared_allocation('EN')
        with pb.declared_reserve():
            expected = portable.slot_preimage_from_v4(v4, 'EN', allocation)
            self.assertEqual(expected, pb.preimage_of(v4))
            stage = Composition.earlier_stage(v4)
            with self.assertRaisesRegex(ValueError, 'exact V4'):
                portable.slot_preimage_from_v4(stage, 'EN', allocation)
        residue = bytearray(stage)
        residue[portable.locate(portable.arm9_segments(v4), pb.SLOT_START, 1) + 8] ^= 0x55     # a stage left residue in the slot
        with tempfile.TemporaryDirectory() as work, self.assertRaisesRegex(ValueError, 'preimage mismatch'):
            install(bytes(residue), 'EN', work, preimage_sha256=expected)
        # the preimage covers the whole assignment, not only the compartment
        tail = bytearray(stage)
        tail[portable.locate(portable.arm9_segments(v4), pb.SLOT_START + pb.SLOT_BYTES - 1, 1)] ^= 0x55
        with tempfile.TemporaryDirectory() as work, self.assertRaisesRegex(ValueError, 'preimage mismatch'):
            install(bytes(tail), 'EN', work, preimage_sha256=expected)

    def test_verify_refuses_forged_candidate_and_capture_fields(self):
        data = rom(self, 'EN')
        out, receipt = self.active(data)
        other = hashlib.sha256(b'another candidate').hexdigest()
        proof = receipt['context_proof']
        cases = {
            'top-level capture differs (X4)': dict(receipt, capture_rom_sha256=other),
            'top-level capture dropped': dict(receipt, capture_rom_sha256=None),
            'candidate differs from the proof': dict(receipt, candidate_sha256=other),
            'proof of another candidate': dict(receipt, context_proof=dict(proof, capture_rom_sha256=other)),
            'proof of another language': dict(receipt, context_proof=dict(proof, language='IT')),
            'proof dropped from an active receipt': dict(receipt, context_proof=None),
            'slot preimage differs (E07)': dict(receipt, compartment=dict(receipt['compartment'], preimage_sha256='1' * 64)),
        }
        for name, forged in cases.items():
            with self.subTest(name), self.assertRaises(ValueError):
                verify(data, out, forged)

    def test_the_compiler_is_pinned(self):
        from unittest import mock
        fake = Path(tempfile.mkdtemp(prefix='fake-clang-')) / 'clang'
        fake.write_text('#!/bin/sh\necho "Apple clang version 99.0.0 (fake)"\n')
        fake.chmod(0o755)
        with tempfile.TemporaryDirectory() as work, mock.patch.object(portable.shutil, 'which', lambda name: str(fake)):
            with self.assertRaisesRegex(ValueError, 'compiler'):
                portable.compile_native(work, pb.SLOT_START)
        fake.unlink()
        fake.parent.rmdir()
        # each pin on its own: a copy of the real compiler passes the binary pin, so patch the expected values
        for constant, message in (('COMPILER_VERSION', 'version drift'), ('COMPILER_SHA256', 'binary drift')):
            with mock.patch.object(portable, constant, 'x' * 8):
                with tempfile.TemporaryDirectory() as work, self.assertRaisesRegex(ValueError, message):
                    portable.compile_native(work, pb.SLOT_START)


_UI = {}


def ui_output(test, language):
    """The REAL sgp131.ui.install output for a V4 input (read-only use of the UI stage, in memory, ~5 s)."""
    if language not in _UI:
        from sgp131 import ui
        from sgp131.test_ui import CONFIG
        data = rom(test, language)
        with tempfile.TemporaryDirectory(prefix='portable-ui-') as work:
            (Path(work) / 'ui-candidate.json').write_text(json.dumps(CONFIG))
            _UI[language] = ui.install(data, language, ROOT / 'local/tools/pokeheartgold/charmap.txt', Path(work))[0]
    return _UI[language]


class RealUiComposition(unittest.TestCase):
    """The portable box installs after the real UI stage and leaves it alone (hook sites are disjoint)."""

    def test_installs_verifies_and_changes_only_owned_ranges_after_the_real_ui(self):
        for language in LANGUAGES:
            after_ui = ui_output(self, language)
            with self.subTest(language=language), tempfile.TemporaryDirectory() as work:
                # UI retirement clears the legacy Guide suffix. The production
                # portable stage already requires an independently known empty
                # slot, rather than the legacy V4 code this fixture used before.
                expected = bytes(pb.SLOT_BYTES)
                segments = portable.arm9_segments(after_ui)
                self.assertEqual(portable.read_ram(after_ui, segments, pb.SLOT_START, pb.SLOT_BYTES), expected)
                preimage = hashlib.sha256(expected).hexdigest()
                changed = bytearray(after_ui)
                changed[portable.locate(segments, pb.SLOT_START, 1)] = 1
                with self.assertRaisesRegex(ValueError, 'assigned compartment preimage mismatch'):
                    install(bytes(changed), language, work, preimage_sha256=preimage)
                out, receipt = install(after_ui, language, work, preimage_sha256=preimage)
                self.assertEqual(verify(after_ui, out, receipt)['stray_bytes'], 0)
                self.assertEqual(receipt['input_sha256'], hashlib.sha256(after_ui).hexdigest())
                self.assertEqual(len(out), len(after_ui))


if __name__ == '__main__':
    unittest.main()
