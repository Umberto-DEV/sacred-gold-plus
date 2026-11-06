"""Class B: exact EN/IT V4 -> complete inert chain with genuine Guide grants.

No test policy, substituted allocator, runtime proof, ROM output or save access.
Inputs use SGP131_BASE_EN/IT and SGP131_UI_CHARMAP; missing inputs fail when
SGP131_MECHANICS_REQUIRE_INPUTS=1. All candidate images remain in memory.
"""
import copy
import hashlib
import json
import os
from pathlib import Path
import struct
import tempfile
import unittest
import zlib
from unittest.mock import patch

from . import bag_alloc, baseline, build, mechanics_stages as stages, reserve, ui_verify
from .test_ui import CONFIG

_CACHE = {}
LANGUAGES = ('EN', 'IT')


def sha(data):
    return hashlib.sha256(data).hexdigest()


class FullProductionChain(unittest.TestCase):
    def candidate(self, language):
        if language in _CACHE:
            return _CACHE[language]
        path = os.environ.get('SGP131_BASE_' + language)
        charmap = os.environ.get('SGP131_UI_CHARMAP')
        if not path or not charmap:
            reason = 'missing exact V4 %s or pinned UI charmap' % language
            if os.environ.get('SGP131_MECHANICS_REQUIRE_INPUTS') == '1':
                self.fail(reason)
            self.skipTest(reason)
        base = Path(path).read_bytes()
        self.assertEqual(baseline.INPUT_HASHES.get(sha(base)), language)
        directory = tempfile.TemporaryDirectory(prefix='rematches-production-chain-')
        unittest.addModuleCleanup(directory.cleanup)
        top = Path(directory.name).resolve()
        config = top / 'ui-candidate.json'
        config.write_text(json.dumps(CONFIG))
        charmap = Path(charmap).resolve()
        snapshot = build.source_snapshot()
        output, report = build.compose(base, 'rematches', charmap, top / 'compose', ui_config=config)
        self.assertEqual(report['source_sha256'], snapshot)
        self.assertEqual(build.source_snapshot(), snapshot)
        self.assertFalse((top / 'compose').exists())
        inputs = build.snapshot_ui_inputs(charmap, config)
        names = stages.writers(stages.chain_for('rematches'))
        owners = [stages.require_stage(name) for name in names]
        regions = [list(owner.regions(output if owner.regions_from_final else base)) for owner in owners]
        cold = stages.intermediate_images(base, output, owners, regions)[0]
        result = (base, output, report, inputs, top, cold, owners, regions)
        _CACHE[language] = result
        print(json.dumps({'production_chain_language': language, 'input_sha256': sha(base),
                          'output_sha256': sha(output), 'cold_ui_sha256': sha(cold),
                          'bytes': len(output), 'evidence': 'static full chain; genuine Guide grant; all inert'}), flush=True)
        return result

    def replay(self, language, output=None, receipts=None, grant=None):
        base, final, report, inputs, top, _, _, _ = self.candidate(language)
        return build.verify_composition(base, final if output is None else output,
                  report['receipts'] if receipts is None else receipts, through='rematches',
                  ui_inputs=inputs, scratch=top / 'replay',
                  allocation=report['reserve_allocation']['receipt'] if grant is None else grant)

    def test_full_chain_replays_with_real_policy_and_fresh_bound_receipt(self):
        for language in LANGUAGES:
            with self.subTest(language=language):
                base, output, report, _, top, cold, _, _ = self.candidate(language)
                grant = report['reserve_allocation']['receipt']
                self.assertEqual(report['reserve_allocation']['source'], 'reserve.allocate')
                self.assertEqual(grant['schema'], 2)
                self.assertEqual(grant['input_sha256'], sha(base))
                self.assertEqual(grant['requested'], {'modern-accuracy.code': 28,
                    'summary-controls.runtime': 512, 'portable-box.runtime': 3024, 'c8.module-stubs': 64})
                self.assertEqual(grant['installer_verification']['ui_sha256'], sha(cold))
                self.assertEqual(grant['installer_verification']['kind'], 'cold-ui-guide-retirement-v1')
                self.assertEqual([r['stage'] for r in report['receipts']],
                                 ['ui', 'moves', 'ai', 'ai-immunities',
                                  'abilities', 'legacy',
                                  'legendary-scene-version', 'trainer-fixes',
                                  'pokeathlon', 'traded-egg', 'bag-foreign',
                                  'bag-view-position', 'lottery-id',
                                  'battle-tower-wrap',
                                  'battle-animation-facade',
                                  'battle-animation-dynamicpunch',
                                  'battle-animation-helping-hand',
                                  'battle-animation-strength',
                                  'battle-animation-spit-up',
                                  'giratina-pc-form', 'invisible-grass',
                                  'waterfall-facing', 'follower-menu-jump',
                                  'controls', 'portable', 'rematches'])
                image = ui_verify.Image(cold)
                self.assertEqual(image.arm(0x023D4C00, 3776), bytes(3776))
                self.assertEqual(ui_verify.Image(output).arm(
                    bag_alloc.ENTRY, len(bag_alloc.POSTIMAGE)), bag_alloc.POSTIMAGE)
                self.assertEqual(image.arm(bag_alloc.ENTRY, len(bag_alloc.PREIMAGE)),
                                 bag_alloc.PREIMAGE)
                self.assertNotEqual(ui_verify.Image(base).arm(0x023D4C00, 512), bytes(512))
                for row in grant['assignments']:
                    self.assertEqual(image.arm(row['start'], row['capacity']), bytes(row['capacity']))
                for name in ('sgp131/cartridge_deltas.py', 'sgp131/guide_retirement.py',
                             'features/rematch-variants/stub.S'):
                    source = Path(build.__file__).resolve().parents[1] / name
                    self.assertEqual(report['source_sha256'][name], sha(source.read_bytes()))
                with patch.object(reserve, 'allocate', wraps=reserve.allocate) as fresh:
                    self.assertEqual(self.replay(language), report['composition'])
                self.assertEqual(fresh.call_count, 1)
                self.assertEqual(fresh.call_args.kwargs['installed_ui'], cold)
                self.assertEqual(len(fresh.call_args.kwargs['overlay_deltas']), 1)
                self.assertFalse((top / 'replay').exists())

    def test_module_single_append_and_seeds_describe_the_final_cartridge(self):
        for language in LANGUAGES:
            with self.subTest(language=language):
                base, output, report, _, _, cold, _, _ = self.candidate(language)
                image = ui_verify.Image(output)
                fat, _, y9, y9_bytes = struct.unpack_from('<4I', output, 0x48)
                rows = report['receipts'][0]['appended']
                self.assertEqual([row['file_id'] for row in rows], [27, 54, 156, 167, 141, 126])
                cursor = len(base)
                for row in rows:
                    aligned = (cursor + 3) & ~3
                    self.assertEqual(output[cursor:aligned], bytes(aligned-cursor))
                    self.assertEqual(row['start'], aligned)
                    self.assertEqual(struct.unpack_from('<II', output, fat+8*row['file_id']),
                                     (row['start'], row['end']))
                    cursor = row['end']
                self.assertEqual(cursor, len(output))
                module = struct.unpack('<24I', image.arm(0x023D7B60, 96))
                guide = struct.unpack('<16I', image.arm(0x023D7C00, 64))
                self.assertEqual(module[17], zlib.crc32(output[y9:y9+y9_bytes]))
                self.assertEqual((module[18], module[19], module[20]), (y9, y9_bytes, len(output)))
                self.assertEqual(module[21:23], image.files[54])
                self.assertEqual(guide[5:8], (*image.files[156], len(output)))
                self.assertEqual(image.records[126], (126, 0x0226B000, 2048, 0, 0x0226B000, 0x0226B000, 126, 0))
                self.assertEqual(image.file(126)[1286], 0)
                self.assertEqual(len(output), len(cold))
                for raw in (r['stage_receipt'] for r in report['receipts'][1:] if r['stage'] in ('controls','portable','rematches')):
                    self.assertEqual(raw['function_state'], 'inert')

    def test_missing_extra_overlay_and_forged_grant_are_not_admitted(self):
        for language in LANGUAGES:
            with self.subTest(language=language):
                _, _, report, _, top, _, _, _ = self.candidate(language)
                for records in ([], [dict(report['receipts'][0]['overlay_deltas'][0], producer='unknown')],
                                report['receipts'][0]['overlay_deltas'] * 2):
                    receipts = copy.deepcopy(report['receipts'])
                    receipts[0]['overlay_deltas'] = records
                    with self.assertRaisesRegex(ValueError, 'omitted or extra'):
                        self.replay(language, receipts=receipts)
                    self.assertFalse((top / 'replay').exists())
                forged = copy.deepcopy(report['reserve_allocation']['receipt'])
                forged['installer_verification']['ui_sha256'] = '0' * 64
                with patch.object(reserve, 'allocate', wraps=reserve.allocate) as fresh:
                    with self.assertRaisesRegex(ValueError, 'freshly reissued'):
                        self.replay(language, grant=forged)
                self.assertEqual(fresh.call_count, 1)
                self.assertFalse((top / 'replay').exists())

    def test_mutations_fail_even_when_stage_hashes_are_refreshed(self):
        for language in LANGUAGES:
            with self.subTest(language=language):
                base, output, report, _, top, _, owners, regions = self.candidate(language)
                last = regions[-1]
                for label, at in (('unauthenticated active flag', last[2].start),
                                  ('compiled resident stub', last[0].start+8),
                                  ('native reader seam', last[1].start),
                                  ('undeclared module byte', ui_verify.Image(output).files[126][0]+32)):
                    changed = bytearray(output); changed[at] ^= 1
                    forged = copy.deepcopy(report['receipts'])
                    forged[-1]['output_sha256'] = sha(changed)
                    raw = forged[-1]['stage_receipt']
                    raw['output_sha256'] = sha(changed)
                    forged[-1]['stage_receipt_sha256'] = sha(stages.canonical(raw))
                    with self.subTest(mutation=label), self.assertRaises(ValueError):
                        self.replay(language, output=bytes(changed), receipts=forged)
                    self.assertFalse((top / 'replay').exists())
