"""License preservation and usable locale entry points need no game inputs."""

from pathlib import Path
import unittest

import player_notices as notices


FOLDERS = dict(zip(notices.LOCALES, ('EN-English', 'IT-Italiano', 'FR-Francais',
                                   'ES-Espanol', 'DE-Deutsch')))
UPDATER = 'Sacred-Gold-Plus-1.3.2-r2-Optional-Updaters.zip'


class PlayerNoticesTests(unittest.TestCase):
    def test_every_locale_has_same_complete_unchanged_english_license(self):
        original = (Path(__file__).resolve().parents[2] / 'LICENSE').read_bytes()
        explanations = []
        for locale in notices.LOCALES:
            with self.subTest(locale=locale):
                members = notices.license_members(locale, original)
                self.assertEqual(set(members), {'Credits-and-Licenses/ABOUT.txt',
                                               'Credits-and-Licenses/LICENSE.txt'})
                self.assertEqual(members['Credits-and-Licenses/LICENSE.txt'], original)
                text = members['Credits-and-Licenses/ABOUT.txt'].decode('utf-8')
                explanations.append(text)
                self.assertIn('GPL-3.0-or-later', text)
                self.assertIn('LICENSE.txt', text)
                self.assertIn('Originals/', text)
                self.assertIn(notices.PROJECT_URL, text)
                self.assertIn(notices.ORIGINAL_PLUS_URL, text)
        self.assertEqual(len(set(explanations)), 5)

    def test_authors_credit_condition_survives_in_every_language(self):
        for locale in notices.LOCALES:
            text = notices.localized_notice(locale).decode('utf-8')
            with self.subTest(locale=locale):
                for credit in ('Drayano', 'mikelan / Mikelan98', 'NefariousnessNo3436',
                               '@JD48096761', 'u/ittapubas', '@Umberto-DEV'):
                    self.assertIn(credit, text)

    def test_altered_missing_or_translated_license_is_rejected(self):
        original = (Path(__file__).resolve().parents[2] / 'LICENSE').read_bytes()
        for content in (b'', b'translated license', original + b'\n',
                        b'X' + original[1:], bytearray(original)):
            with self.subTest(content_type=type(content).__name__, size=len(content)):
                with self.assertRaisesRegex(ValueError, 'unchanged English'):
                    notices.license_members('IT', content)

    def test_unsupported_locale_never_falls_back_to_english(self):
        with self.assertRaisesRegex(ValueError, 'Unsupported'):
            notices.localized_notice('PT')

    def test_start_here_names_actual_installation_paths_and_optional_download(self):
        text = notices.start_here('1.3.2', 'r2', FOLDERS, UPDATER).decode('utf-8')
        for locale, folder in FOLDERS.items():
            with self.subTest(locale=locale):
                self.assertIn(folder + '/Installation-1.3.2-' + locale + '.pdf', text)
                self.assertIn(folder + '/Credits-and-Licenses/', text)
        self.assertEqual(text.count(UPDATER), 5)
        self.assertEqual(text.count('.sav'), 5)
        self.assertNotIn('Documents/', text)
        self.assertNotIn('.json', text)

    def test_entry_point_rejects_missing_locales_and_path_or_line_injection(self):
        cases = [dict(FOLDERS), dict(FOLDERS), dict(FOLDERS)]
        cases[0].pop('DE')
        cases[1]['DE'] = '../DE'
        cases[2]['DE'] = FOLDERS['EN'].upper()
        for folders in cases:
            with self.subTest(folders=folders), self.assertRaises(ValueError):
                notices.start_here('1.3.2', 'r2', folders, UPDATER)
        for field, value in (('version', '1.3.2\nextra'), ('revision', '../r2'),
                             ('updater', '../../Updater.zip'), ('updater', 'Updater.txt')):
            args = ['1.3.2', 'r2', FOLDERS, UPDATER]
            args[{'version': 0, 'revision': 1, 'updater': 3}[field]] = value
            with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                notices.start_here(*args)

    def test_optional_updater_table_keeps_full_hashes_and_matching_patch_paths(self):
        sources = [{'id': 'clean-us', 'sha256': '1' * 64, 'bytes': 134217728},
                   {'id': 'plus-1.03', 'sha256': '2' * 64, 'bytes': 152688624}]
        patches = {'clean-us': 'Patch/from-clean-us.xdelta',
                   'plus-1.03': 'Patch/from-plus-1.03.xdelta'}
        target = {'sha256': 'a' * 64, 'bytes': 12345}
        for locale in notices.LOCALES:
            with self.subTest(locale=locale):
                text = notices.updater_readme(locale, '1.3.2', target, sources, patches).decode()
                self.assertIn('a' * 64, text)
                self.assertIn('12345', text)
                for source in sources:
                    self.assertIn(source['id'] + ' | ' + source['sha256'] + ' | '
                                  + str(source['bytes']) + ' | ' + patches[source['id']], text)
        for bad in ({'clean-us': '../bad.xdelta'}, {'clean-us': 'Patch/x.xdelta\nextra'}):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                notices.updater_readme('EN', '1.3.2', target, sources[:1], bad)

    def test_updater_source_size_is_required_and_must_be_a_positive_byte_count(self):
        target = {'sha256': 'a' * 64, 'bytes': 12345}
        source = {'id': 'clean-us', 'sha256': '1' * 64}
        patches = {'clean-us': 'Patch/from-clean-us.xdelta'}
        for value in (None, 0, -1, True, '134217728'):
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, 'source'):
                notices.updater_readme('EN', '1.3.2', target,
                                       [dict(source, bytes=value)], patches)

    def test_shared_about_identifies_guides_as_part_of_the_main_download(self):
        scopes = {'EN': 'In the main download, Originals/',
                  'IT': 'Nel download principale, Originals/',
                  'FR': 'Dans le téléchargement principal, Originals/',
                  'ES': 'En el paquete principal, Originals/',
                  'DE': 'Im Hauptdownload enthält Originals/'}
        for locale, scope in scopes.items():
            with self.subTest(locale=locale):
                self.assertIn(scope, notices.localized_notice(locale).decode('utf-8'))


if __name__ == '__main__':
    unittest.main()
