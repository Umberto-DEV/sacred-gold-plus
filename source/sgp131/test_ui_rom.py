"""Opt-in canonical EN/IT composition in RAM; no ROM output or emulator.

SGP131_BASE_EN/IT and SGP131_UI_CHARMAP identify original inputs. Set
SGP131_UI_REQUIRE_INPUTS=1 to make missing inputs failures. Optional
SGP131_UI_RECEIPTS is a private directory for small JSON evidence only.
"""
import copy
import hashlib
import json
import os
from pathlib import Path
import struct
import tempfile
import unittest

from . import ui, ui_compile, ui_verify, guide_content, reserve
from .test_ui import CONFIG


class CanonicalUiTests(unittest.TestCase):
    def language(self, language):
        path = os.environ.get('SGP131_BASE_' + language)
        charmap = os.environ.get('SGP131_UI_CHARMAP')
        if not path or not charmap:
            message = 'missing canonical ' + language + ' / external charmap'
            if os.environ.get('SGP131_UI_REQUIRE_INPUTS') == '1':
                self.fail(message)
            self.skipTest(message)
        path, charmap = Path(path), Path(charmap)
        original = path.read_bytes()
        original_sha = hashlib.sha256(original).hexdigest()
        with tempfile.TemporaryDirectory(prefix='ui-install-test-') as directory:
            work = Path(directory)
            (work / 'ui-candidate.json').write_text(json.dumps(CONFIG))
            with self.assertRaises(ValueError):
                ui.install(original, 'IT' if language == 'EN' else 'EN', charmap, work)
            after, receipt = ui.install(original, language, charmap, work)
            with self.assertRaises(ValueError):
                ui.install(after, language, charmap, work)  # no second cold reset
            verified = ui_verify.verify(original, after, language, charmap, work, receipt)
            self.assertEqual(receipt, verified)
            self.assertLessEqual(receipt['dynamic54']['bytes'], 65536)
            self.assertEqual(receipt['file_count'], 513)
            # Existing independent path contract reads the SAME original, never
            # a temporary copy; byte adapter equivalence covers all Guide text.
            content, old_receipt = guide_content.build_from_rom(path, language, charmap)
            view = ui_verify.Image(after)
            focus_site=0x0225A96E
            overlay=view.overlay(27);base=view.records[27][1]
            self.assertTrue(0x023D4000 <= ui_verify._branch(focus_site,overlay[focus_site-base:focus_site-base+4]) < 0x023D4C00,
                            'native per-frame focus must dispatch to the book-aware successor')
            self.assertEqual(view.arm(0x023D4C00, 5120), bytes(5120))
            closure = receipt['retirement']['guide']
            self.assertEqual(closure['legacy_code_bytes'], 6402)
            self.assertEqual(closure['incoming']['old_live_roots'], 9)
            self.assertEqual(closure['incoming']['retargeted_field_roots'], 6)
            requests = {'summary-controls.runtime': 512, 'portable-box.runtime': 3024,
                        'c8.module-stubs': 60, 'modern-accuracy.code': 28}
            for name, count in requests.items():
                with self.assertRaises(ValueError):
                    reserve.allocate(original, {name: count})
            grant = reserve.allocate(original, requests, installed_ui=after, charmap=charmap, work_dir=work)
            self.assertEqual(grant['schema'], 2)
            self.assertEqual(reserve.validate_allocation(grant, language), grant['assignments'])
            self.assertEqual(grant['installer_verification']['ui_sha256'], hashlib.sha256(after).hexdigest())
            for mutate in (lambda item: item['assignments'][0].update(capacity=528),
                           lambda item: item.update(installer_verification=True),
                           lambda item: item['installer_verification'].update(approved=True)):
                forged_grant = copy.deepcopy(grant)
                mutate(forged_grant)
                with self.assertRaises(ValueError):
                    reserve.validate_allocation(forged_grant, language)
            spans, _, image, base = ui_verify.ui_resource_verify._archive(view.file(156))
            lo, hi = spans[829]
            self.assertEqual(content, image[lo:hi])
            self.assertEqual(old_receipt['content_sha256'], receipt['resource']['guide_sha256'])
            mutations = []
            for label, address in [('old-template', 0x020FA354), ('foreign-hook', 0x0203BFE8),
                                   ('computed-navigation', 0x023D75AC), ('guard', 0x023CE7F0),
                                   ('protected-neighbor', 0x023D4C10), ('retired-portable-code', 0x023D4E10),
                                   ('fieldbook-guard', 0x023D4C00), ('old-guide-template', 0x023D7B10),
                                   ('cold-font-state', 0x023D7ED8), ('labels', 0x023D7C40),
                                   ('module-seed', 0x023D7B60+72), ('uir-seed', 0x023D7BC0+40),
                                   ('guide-seed', 0x023D7C00+20), ('training-original', 0x023CB1A0+48)]:
                mutations.append((label, view.offset(address, 4)))
            mutations += [('old54-id', view.y9+54*32), ('foreign-file-id', view.y9+54*32+24),
                          ('foreign-y9', view.y9+53*32+4), ('FAT-overlap', view.fat+54*8),
                          ('wrong-packed', view.files[54][0]+20), ('missing-member', view.files[156][0]+24),
                          ('old-member-content', view.files[167][0]+480), ('header-length', 0x80)]
            rejected = []
            for label, at in mutations:
                with self.subTest(language=language, mutation=label):
                    changed = bytearray(after)
                    changed[at] ^= 1
                    forged = copy.deepcopy(receipt)
                    forged['output_sha256'] = hashlib.sha256(changed).hexdigest()
                    # Caller tries both common self-certification loopholes.
                    forged['writes'].append(dict(offset=at, bytes=1, approved=True))
                    with self.assertRaises(ValueError):
                        ui_verify.verify(original, bytes(changed), language, charmap, work, forged)
                    del changed
                    rejected.append(label)
            forged = copy.deepcopy(receipt)
            forged['all_other_bytes_preserved'] = False
            with self.assertRaises(ValueError):
                ui_verify.verify(original, after, language, charmap, work, forged)
            config = dict(CONFIG, scene_work_calls=5)
            (work/'ui-candidate.json').write_text(json.dumps(config))
            with self.assertRaises(ValueError):
                ui_verify.verify(original, after, language, charmap, work, receipt)
            (work/'ui-candidate.json').write_text(json.dumps(CONFIG))
            self.assertEqual(sorted(p.name for p in work.iterdir()), ['ui-candidate.json'])
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), original_sha)
            evidence = dict(receipt=receipt, mutations_rejected=rejected+['forged-receipt','changed-config'],
                            guide_adapter_equivalent=True, original_unchanged=True,
                            generated_rom_files=0, compiler_scratch_removed=True)
            target = os.environ.get('SGP131_UI_RECEIPTS')
            if target:
                destination=Path(target)
                self.assertTrue(destination.is_dir())
                (destination/('ui-install-'+language+'.json')).write_text(json.dumps(evidence,sort_keys=True,indent=2)+'\n')
            print(json.dumps(dict(language=language, input_sha256=original_sha,
                                  output_sha256=receipt['output_sha256'], output_bytes=len(after),
                                  dynamic54=receipt['dynamic54'], mutations_rejected=len(rejected)+2,
                                  guide_adapter_equivalent=True, generated_rom_files=0),sort_keys=True))

    def test_en_canonical_install_and_independent_mutations(self):
        self.language('EN')

    def test_it_canonical_install_and_independent_mutations(self):
        self.language('IT')
