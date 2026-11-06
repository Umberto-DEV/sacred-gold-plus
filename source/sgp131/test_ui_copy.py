"""Class A: authored catalogue behavior with a local codec and fixed fake metrics.

The fake only supplies glyphs/metrics; the real validator and wrapping run.
Native font, source identities, compiler and species checks are Class B.
"""
import copy
import importlib.util
import json
from pathlib import Path
import unittest

MODULE = Path(__file__).with_name('ui_copy.py')
PROSE = Path(__file__).with_name('data') / 'ui-copy.json'


class AuthoredCatalogueTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(MODULE.is_file(), 'missing authored EN/IT catalogue validator')
        spec = importlib.util.spec_from_file_location('copy_under_test', MODULE)
        self.ui = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.ui)
        self.raw = PROSE.read_text()
        self.catalogue = self.ui.load_catalogue(self.raw)
        chars = sorted(set(''.join(e['text'][l] for e in self.catalogue['entries'] for l in ('EN', 'IT'))))
        self.table = {c: i + 1 for i, c in enumerate(chars) if c != '\n'}
        self.table['\n'] = 0xE000
        self.encode = lambda text: [self.table[c] for c in text] + [65535]
        self.widths = (4,) * 509

    def texts(self, language):
        return {e['name']: e['text'][language] for e in self.catalogue['entries']}

    def test_footer_layout_metadata_reconstructs_copy_and_rejects_corruption(self):
        for change in ('missing','key','label','count'):
            c=copy.deepcopy(self.catalogue)
            if change=='missing':del c['footer_runs']['FOOTER_ROOT']
            elif change=='key':c['footer_runs']['FOOTER_ROOT']['EN'][0]['key']='Z'
            elif change=='label':c['footer_runs']['FOOTER_ROOT']['EN'][1]['text']='Different'
            else:c['footer_runs']['FOOTER_ROOT']['EN']*=2
            with self.subTest(change=change),self.assertRaises(ValueError):self.ui.load_catalogue(json.dumps(c))
    def test_x_is_explicit_apply_and_y_is_info_in_persistent_controls(self):
        for language, apply in (('EN', 'X Apply'), ('IT', 'X Applica')):
            text = self.texts(language)
            self.assertIn(apply, text['FOOTER_ROOT'])
            self.assertIn('Y Info', text['FOOTER_ROOT'])
            self.assertNotIn('A Apply', text['FOOTER_ROOT'])
            self.assertIn('L/R', text['CONTEXT_ROOT'])
            self.assertIn('B', text['FOOTER_INFO'])
            self.assertNotIn('A', text['FOOTER_INFO'])

    def test_exit_discard_names_unsaved_changes_and_continue_is_available(self):
        for language, discard, pending in (('EN', 'Discard', 'changes'), ('IT', 'Scarta', 'modifiche')):
            text = self.texts(language)
            self.assertEqual(text['ACTION_DISCARD'], discard)
            self.assertIn(pending, text['EXIT_PROMPT'].lower())
            self.assertTrue(text['ACTION_CONTINUE'])
            self.assertIn('B', text['FOOTER_CONFIRM'])

    def test_search_needs_40_steps_and_future_apply_not_start(self):
        for language, action, apply, exit_word in (('EN', 'Prepare search', 'Apply', 'exit'), ('IT', 'Prepara ricerca', 'Applica', 'esci')):
            text = self.texts(language)
            self.assertEqual(text['ACTION_PREPARE'], action)
            self.assertIn('40', text['NOTICE_CHARGE'])
            self.assertIn(apply, text['SEARCH_PENDING'])
            self.assertIn(exit_word, text['SEARCH_PENDING'].lower())
            self.assertNotIn('Start', text['ACTION_PREPARE'])
            self.assertNotIn('Avvia', text['ACTION_PREPARE'])
            self.assertIn('40', text['INFO_SEARCH'])

    def test_owner_error_says_none_applied_and_gives_recovery(self):
        for language, none, back in (('EN', 'No changes applied', 'B'), ('IT', 'Nessuna modifica applicata', 'B')):
            text = self.texts(language)
            self.assertIn(none, text['ERROR_OWNER'])
            self.assertIn(back, text['ERROR_OWNER'])
            self.assertTrue(text['NOTICE_UNAVAILABLE'])
            self.assertTrue(text['NOTICE_EMPTY'])
            self.assertTrue(text['NOTICE_NO_TARGET'])
            self.assertTrue(text['NOTICE_METHOD'])

    def test_pending_search_and_unavailable_values_are_readable_in_root_rows(self):
        for language in ('EN', 'IT'):
            text = self.texts(language)
            self.assertIn('VALUE_PENDING', text)
            self.assertIn('VALUE_UNAVAILABLE', text)
            self.assertIn('CONTEXT_SEARCH', text)
            self.assertNotIn('L/R', text['CONTEXT_SEARCH'])

    def test_navigation_notices_fit_single_context_line_without_hiding_search(self):
        for language in ('EN', 'IT'):
            _, report = self.ui.encode_catalogue(self.catalogue, language, self.encode, self.widths)
            for name in ('UNAVAILABLE', 'EMPTY', 'METHOD', 'NO_TARGET', 'PRO', 'CHARGE'):
                entry = report['entries']['NOTICE_' + name]
                self.assertEqual(entry['role'], 'context')
                self.assertEqual(len(entry['line_widths']), 1)
                self.assertLessEqual(entry['line_widths'][0], 200)

    def test_ordinal_reserve_covers_every_classic_and_pro_position(self):
        widths = list(self.widths)
        widths[self.table['3'] - 1] = 16
        _, report = self.ui.encode_catalogue(self.catalogue, 'EN', self.encode, widths)
        # 13/14 is wider than14/14 in this deliberately nonuniform font.
        context_width = 4 * len(self.texts('EN')['CONTEXT_ROOT'])
        self.assertEqual(report['context_ordinal_px'], context_width + 8 + 32)

    def test_owner_domains_keep_stereo_zero_and_server_logical_values(self):
        rows = self.catalogue['rows']
        self.assertEqual(len(rows), 14)
        self.assertEqual(rows[3]['values'], ['VALUE_STEREO', 'VALUE_MONO'])
        self.assertEqual(rows[10]['values'], ['VALUE_ORIGINAL', 'VALUE_CONN2', 'VALUE_CONN3'])
        self.assertEqual(rows[11]['values'], ['VALUE_CLASSIC', 'VALUE_PRO'])
        self.assertEqual(rows[5]['values'], ['FRAME_%02d' % i for i in range(1, 21)])
        self.assertEqual(self.catalogue['methods'], ['METHOD_LAND', 'METHOD_SURF', 'METHOD_OLD_ROD', 'METHOD_GOOD_ROD', 'METHOD_SUPER_ROD'])
        self.assertEqual(self.catalogue['status'], ['STATUS_SUCCESSES', 'STATUS_ODDS', 'STATUS_STEPS'])

    def test_wrapped_info_is_single_view_with_preview_space(self):
        for language in ('EN', 'IT'):
            authored, report = self.ui.encode_catalogue(self.catalogue, language, self.encode, self.widths)
            self.assertEqual(len(authored), len(self.catalogue['entries']))
            for entry in self.catalogue['entries']:
                lines = report['entries'][entry['name']]['line_widths']
                self.assertLessEqual(len(lines), 4 if entry['role'] == 'preview_info' else 7 if entry['role'] in ('info', 'body') else 1)
                self.assertTrue(all(w <= 232 for w in lines))
            self.assertLessEqual(report['title_version_px'], 240)
            self.assertLessEqual(report['context_ordinal_px'], 240)
            self.assertEqual(report['rows'][5]['presentation'], 'selector')
            self.assertEqual(report['window'], [8, 8, 240, 176])
            self.assertEqual(report['viewport_y'], [36, 56, 76, 96, 116, 136])

    def test_shared_preview_wraps_inside_frame_and_refuses_three_lines(self):
        candidate = copy.deepcopy(self.catalogue)
        preview = next(e for e in candidate['entries'] if e['name'] == 'PREVIEW_TEXT')
        for language in ('EN', 'IT'):
            # 212px before wrapping: fits the old232px body, crosses the200px inner.
            preview['text'][language] = 'A' * 34 + ' ' + 'B' * 18
            authored, report = self.ui.encode_catalogue(candidate, language, self.encode, self.widths)
            self.assertEqual(report['entries']['PREVIEW_TEXT']['line_widths'], [136, 72])
            self.assertIn(0xE000, authored[preview['id']])
            preview['text'][language] = ' '.join(['A' * 40] * 3)
            with self.assertRaisesRegex(ValueError, 'copy exceeds geometry: PREVIEW_TEXT'):
                self.ui.encode_catalogue(candidate, language, self.encode, self.widths)

    def test_missing_language_duplicate_id_name_and_bad_types_fail_closed(self):
        mutations = [lambda c: c['entries'][0]['text'].pop('IT'),
                     lambda c: c['entries'][0].update(id=True),
                     lambda c: c['entries'][0].update(id=4096),
                     lambda c: c['entries'][1].update(id=c['entries'][0]['id']),
                     lambda c: c['entries'][1].update(name=c['entries'][0]['name']),
                     lambda c: c['entries'][0]['text'].update(EN=7),
                     lambda c: c['entries'].pop(),
                     lambda c: c.update(schema=True),
                     lambda c: c['rows'][0].update(row=True),
                     lambda c: c['rows'][0].update(values=['VALUE_FAST']),
                     lambda c: c['entries'][0].update(role='unknown')]
        for mutate in mutations:
            candidate = copy.deepcopy(self.catalogue); mutate(candidate)
            with self.subTest(mutate=mutate), self.assertRaises(ValueError):
                self.ui.load_catalogue(json.dumps(candidate))
        with self.assertRaises(ValueError):
            self.ui.load_catalogue('{"schema":1,"schema":1}')

    def test_unknown_glyph_early_eos_and_encoder_type_are_rejected(self):
        for words in ([1, 65535, 65535], [0, 65535], [510, 65535], [True, 65535], [1], 'abc'):
            with self.subTest(words=words), self.assertRaises(ValueError):
                self.ui.encode_catalogue(self.catalogue, 'EN', lambda t: words, self.widths)
        with self.assertRaises(ValueError):
            self.ui.encode_catalogue(self.catalogue, 'FR', self.encode, self.widths)
        for widths in ((4,) * 508, (True,) * 509, (17,) * 509):
            with self.assertRaises(ValueError):
                self.ui.encode_catalogue(self.catalogue, 'EN', self.encode, widths)

    def test_too_many_lines_unbreakable_text_and_wide_controls_are_rejected(self):
        for text in ('word\n' * 7 + 'word', 'a' * 129):
            candidate = copy.deepcopy(self.catalogue)
            next(e for e in candidate['entries'] if e['name'] == 'INFO_MODE')['text']['EN'] = text
            with self.assertRaises(ValueError):
                self.ui.encode_catalogue(candidate, 'EN', self.encode, self.widths)
        candidate = copy.deepcopy(self.catalogue)
        next(e for e in candidate['entries'] if e['name'] == 'FOOTER_ROOT')['text']['EN'] = 'a' * 59
        with self.assertRaises(ValueError):
            self.ui.encode_catalogue(candidate, 'EN', self.encode, self.widths)

    def test_header_text_cannot_invade_fixed_version_or_ordinal_regions(self):
        for name, count in [('TITLE', 47), ('CONTEXT_ROOT', 51)]:
            candidate = copy.deepcopy(self.catalogue)
            next(e for e in candidate['entries'] if e['name'] == name)['text']['EN'] = 'a' * count
            with self.subTest(name=name), self.assertRaises(ValueError):
                self.ui.encode_catalogue(candidate, 'EN', self.encode, self.widths)

    def test_native_width_row_policy_uses_selector_when_choices_do_not_fit(self):
        # Increasing actual glyph advances changes admission/presentation, not text/font size.
        authored, report = self.ui.encode_catalogue(self.catalogue, 'EN', self.encode, self.widths)
        for row in report['rows']:
            self.assertLessEqual(row['required_px'], 240)
        self.assertEqual(authored[self.ui.ids(self.catalogue)['VERSION']][-1], 65535)
        pool = self.texts('EN')['FORMAT_POOL']
        self.assertTrue(set('0123456789/:% ').issubset(pool))
        self.assertEqual(self.ui.c_header(self.catalogue), (MODULE.parents[1] / 'features/settings-ui/catalog.h').read_text())


if __name__ == '__main__':
    unittest.main()
