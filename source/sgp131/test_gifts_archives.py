"""Class B: the gift-script fixes as a producer of archive member deltas (never append after the UI)."""
import copy
import hashlib
import os
from pathlib import Path
import unittest
from unittest import mock

from sgp131 import archives, gifts_archives as GA, gifts_scripts as S
from sgp131.test_gifts_audit_rom import INPUTS
from sgp131.test_gifts_scripts import model_party_gift

ROOT = Path(__file__).resolve().parents[2]
CHARMAP = Path(os.environ.get('SGP_PRET_SOURCE') or ROOT / 'local' / 'tools' / 'pokeheartgold') / 'charmap.txt'
EEVEE = 227
EXPECTED_MEMBERS = [225, 227, 232, 243, 246, 938, 962]
_CACHE = {}


def v4(language):
    path, digest = INPUTS[language]
    if not Path(path).is_file():
        if os.environ.get('SGP_GIFT_REQUIRE_INPUTS') == '1':
            raise AssertionError(f'SGP_GIFT_REQUIRE_INPUTS=1 and the {language} V4 candidate is missing')
        raise unittest.SkipTest(f'{language} V4 candidate not found')
    if language not in _CACHE:
        data = Path(path).read_bytes()
        assert hashlib.sha256(data).hexdigest() == digest
        _CACHE[language] = data
    return _CACHE[language]


def delta(language):
    key = (GA.SCRIPTS, language)
    if key not in _CACHE:
        _CACHE[key] = GA.PRODUCERS[GA.SCRIPTS](v4(language), language, CHARMAP)
    return _CACHE[key]


def need_pret():
    """The pinned pret checkout (charmap, scrcmd.json): skip without it, fail with SGP_GIFT_REQUIRE_INPUTS=1."""
    if not (GA._pret() / 'tools' / 'py_scripts' / 'scrcmd.json').is_file() or not CHARMAP.is_file():
        if os.environ.get('SGP_GIFT_REQUIRE_INPUTS') == '1':
            raise AssertionError('SGP_GIFT_REQUIRE_INPUTS=1 and the pinned pret checkout is missing')
        raise unittest.SkipTest('pinned pret checkout not found')


def flipped(raw):
    return raw[:-1] + bytes([raw[-1] ^ 1])


class DefaultPretPath(unittest.TestCase):
    """Without SGP_PRET_SOURCE the pret checkout is <repo>/local/tools/pokeheartgold (ROOT is already the repo root)."""

    def test_default_pret_is_under_the_repository_root(self):
        repo_root = Path(__file__).resolve().parents[2]
        with mock.patch.dict(os.environ):
            os.environ.pop('SGP_PRET_SOURCE', None)
            self.assertEqual(GA._pret(), repo_root / 'local' / 'tools' / 'pokeheartgold')
            self.assertEqual(GA._pret(), GA.ROOT / 'local' / 'tools' / 'pokeheartgold')

    def test_the_environment_variable_still_wins(self):
        with mock.patch.dict(os.environ, {'SGP_PRET_SOURCE': '/somewhere/else'}):
            self.assertEqual(GA._pret(), Path('/somewhere/else'))

    def test_every_gift_module_resolves_the_same_default(self):
        """No gift module may build the default from ROOT.parent: they all agree on <repo>/local/tools/pokeheartgold."""
        sgp131 = Path(__file__).resolve().parent
        for path in sorted(sgp131.glob('gifts*.py')):
            self.assertFalse('ROOT.parent' in path.read_text(), path.name)


class Producers(unittest.TestCase):
    languages = ('EN', 'IT')

    def setUp(self):
        need_pret()
        for language in self.languages:
            v4(language)

    def test_the_only_producer_is_the_script_one_and_no_message_bank_is_declared(self):
        self.assertEqual((sorted(GA.PRODUCERS), sorted(GA.CHECKERS)), ([GA.SCRIPTS], [GA.SCRIPTS]))
        self.assertEqual(GA.script_members(), EXPECTED_MEMBERS)
        for language in self.languages:
            d = delta(language)
            with self.subTest(language=language):
                self.assertEqual([m.index for m in d.members], EXPECTED_MEMBERS)
                self.assertEqual((d.archive, d.producers()), ('a/0/1/2', [GA.SCRIPTS]))
                self.assertFalse({m.index for m in d.members} & set(archives.GUIDE_SCRIPT_MEMBERS))

    def test_bug13101_all_eleven_real_eevee_movements_remain_halfword_aligned(self):
        for language in self.languages:
            data = v4(language)
            resolve, file = archives.from_cartridge(data)
            raw = archives.members(file(resolve('a/0/1/2')))[227]
            fixed = S.transform_party_guard(raw, language, GA._commands())
            old = S.decode(raw, GA._commands(), 227)
            new = S.decode(fixed, GA._commands(), 227)
            with self.subTest(language=language):
                self.assertEqual(len(old.dati_movimento), 11)
                self.assertTrue(all(p % 2 == 0 for p in old.dati_movimento))
                self.assertTrue(all(p % 2 == 0 for p in new.dati_movimento),
                                f'BUG-131-01 unaligned movement pointers: {sorted(new.dati_movimento)}')

    def test_bug13101_real_paths_zero_to_six_keep_messages_nickname_flags_and_buffers(self):
        recipe, commands = S.load_guard_recipe(), GA._commands()
        for language in self.languages:
            data = v4(language)
            resolve, file = archives.from_cartridge(data)
            raw = archives.members(file(resolve('a/0/1/2')))[227]
            fixed = S.transform_party_guard(raw, language, commands)
            for count in range(7):
                for choice in (0, 1):
                    old = model_party_gift(raw, commands, recipe['entry'], count, choice)
                    new = model_party_gift(fixed, commands, recipe['entry'], count, choice)
                    with self.subTest(language=language, count=count, choice=choice):
                        if count < 6:
                            for key in ('variables', 'buffers', 'messages', 'effects'):
                                self.assertEqual(new[key], old[key])
                            self.assertEqual(sum(n == 'BufferPlayersName' for n, _ in new['calls']), 2)
                            self.assertIn(('GiveMon', [133, 5, 0, 0, 0, 0x800C]), new['effects'])
                        else:
                            self.assertEqual(new['effects'], [])
                            self.assertEqual(new['buffers'], {0: 'untouched'})
                            self.assertEqual(new['variables'], {0x8005: 6, 0x800C: 0xA55A, 0x4000: 0xA55A})
                            self.assertEqual(new['messages'], [('MsgBoxExtern', [25, 39], {0: 'untouched'})])
                            self.assertFalse(any(n == 'BufferPlayersName' for n, _ in new['calls']))

    def test_the_delta_binds_to_the_v4_cartridge_and_merges_with_the_producer_of_another_archive(self):
        for language in self.languages:
            data = v4(language)
            resolve, file = archives.from_cartridge(data)
            keen = archives.PRODUCERS['keen-eye-text'](data, language, CHARMAP)
            checked = archives.check_against([delta(language), keen], resolve, file)
            with self.subTest(language=language):
                self.assertEqual([d.archive for d in checked], sorted((d.archive for d in checked), key=lambda a: resolve(a)))
                self.assertEqual(sorted(d.archive for d in checked), ['a/0/1/2', 'a/0/2/7'])
                for d in checked:
                    raw = archives.apply_members(file(d.file_id), d.replacements())
                    archives.verify_members(file(d.file_id), raw, d.replacements())
                records = [d.record() for d in checked]
                merged = archives.normalize([keen, delta(language)])
                self.assertEqual([d.record() for d in merged], records, 'the order of independent producers does not matter')

    def test_every_member_passes_the_checker_of_its_own_producer(self):
        for language in self.languages:
            resolve, file = archives.from_cartridge(v4(language))
            d = delta(language)
            old = archives.members(file(d.file_id))
            for member in d.members:
                with self.subTest(language=language, member=member.index):
                    GA.CHECKERS[GA.SCRIPTS](member.index, old[member.index], member.after, language)

    def test_the_checker_refuses_forged_foreign_and_guide_members(self):
        data = v4('EN')
        resolve, file = archives.from_cartridge(data)
        scripts = archives.members(file(resolve('a/0/1/2')))
        d = delta('EN')
        eevee = next(m for m in d.members if m.index == EEVEE)
        ribbon = next(m for m in d.members if m.index == 225)
        for label, args in (('a flipped byte in the Eevee member', (EEVEE, scripts[EEVEE], flipped(eevee.after))),
                            ('a trailing byte', (EEVEE, scripts[EEVEE], eevee.after + b'\0')),
                            ('the member unchanged', (EEVEE, scripts[EEVEE], scripts[EEVEE])),
                            ('the Eevee bytes on a ribbon member', (225, scripts[225], eevee.after)),
                            ('the ribbon bytes on the Eevee member', (EEVEE, scripts[EEVEE], ribbon.after)),
                            ('the Eevee bytes on another member', (98, scripts[98], eevee.after)),
                            ('a ribbon tail altered', (225, scripts[225], flipped(ribbon.after))),
                            ('a member the module does not name', (100, scripts[100], scripts[100] + b'\0')),
                            ('a member the Guide audits', (890, scripts[890], scripts[890])),
                            ('hostile types', ('x', None, 5))):
            with self.subTest(label), self.assertRaises(ValueError):
                GA.check_scripts(args[0], args[1], args[2], 'EN')
        with self.assertRaises(ValueError):
            GA.check_scripts(EEVEE, scripts[EEVEE], eevee.after, 'FR')

    def test_a_producer_refuses_a_guide_audited_member(self):
        guard = copy.deepcopy(S.load_guard_recipe())
        guard['member'] = 890
        with mock.patch.object(S, 'load_guard_recipe', lambda *a: guard):
            with self.assertRaisesRegex(ValueError, 'Guide'):
                GA.script_members()

    def test_the_producers_are_registered_by_name_and_replay_to_the_same_record(self):
        for language in self.languages:
            data = v4(language)
            records = [d.record() for d in archives.normalize([delta(language)])]
            with self.subTest(language=language):
                archives.register_owner_producers()
                self.assertIs(archives.PRODUCERS[GA.SCRIPTS], GA.PRODUCERS[GA.SCRIPTS])
                self.assertIs(archives.CHECKERS[GA.SCRIPTS], GA.CHECKERS[GA.SCRIPTS])
                replay = archives.rederive(data, language, CHARMAP, records)
                self.assertEqual([d.record() for d in replay], records)

    def test_the_delta_costs_no_appended_copy_of_an_archive(self):
        # the producer's effect is member bytes only: far smaller than the 450 KB a/0/1/2 copy an append would add
        for language in self.languages:
            d = delta(language)
            self.assertLess(d.total_after_bytes(), 20000)
            sizes = {m.index: len(m.after) for m in d.members}
            raw = archives.members(archives.from_cartridge(v4(language))[1](d.file_id))
            self.assertEqual({i: n - len(raw[i]) for i, n in sizes.items()},
                             {225: 6, 227: 34, 232: 6, 243: 6, 246: 6, 938: 6, 962: 6})

    # ---- every rule of the checker and the producer has a case where ONLY that rule can refuse
    def test_the_checker_runs_the_independent_read_back_not_only_the_byte_comparison(self):
        data = v4('EN')
        resolve, file = archives.from_cartridge(data)
        scripts = archives.members(file(resolve('a/0/1/2')))
        eevee = next(m for m in delta('EN').members if m.index == EEVEE)
        def second_call_refuses(real, message):
            calls = []

            def fake(*args, **kwargs):
                calls.append(1)
                if len(calls) > 1:          # the first call is the one inside the pure function itself
                    raise ValueError(message)
                return real(*args, **kwargs)
            return fake
        with mock.patch.object(S, 'verify_party_guard', second_call_refuses(S.verify_party_guard, 'read-back refused')):
            with self.assertRaisesRegex(ValueError, 'read-back refused'):
                GA.check_scripts(EEVEE, scripts[EEVEE], eevee.after, 'EN')
        ribbon = next(m for m in delta('EN').members if m.index == 225)
        with mock.patch.object(S, 'verify_member', second_call_refuses(S.verify_member, 'ribbon read-back refused')):
            with self.assertRaisesRegex(ValueError, 'ribbon read-back refused'):
                GA.check_scripts(225, scripts[225], ribbon.after, 'EN')

    def test_the_producer_refuses_a_native_message_bank_that_is_not_the_pinned_one(self):
        guard = copy.deepcopy(S.load_guard_recipe())
        guard['message']['bank_sha256']['EN'] = '0' * 64
        with mock.patch.object(S, 'load_guard_recipe', lambda *a: guard):
            with self.assertRaisesRegex(ValueError, 'native party-full message bank'):
                GA.apply_scripts(v4('EN'), 'EN')

    def test_a_changed_command_table_is_refused(self):
        import shutil
        import tempfile
        with tempfile.TemporaryDirectory() as pret:
            target = Path(pret) / 'tools' / 'py_scripts'
            target.mkdir(parents=True)
            source = GA._pret() / 'tools' / 'py_scripts' / 'scrcmd.json'
            (target / 'scrcmd.json').write_bytes(source.read_bytes() + b'\n')
            with mock.patch.dict(os.environ, {'SGP_PRET_SOURCE': pret}):
                with self.assertRaisesRegex(ValueError, 'metadata SHA-256'):
                    GA._commands()

    def test_the_guide_pinned_script_members_stay_native(self):
        self.assertFalse(set(GA.script_members()) & set(archives.GUIDE_SCRIPT_MEMBERS))
        self.assertNotIn(890, GA.script_members())


if __name__ == '__main__':
    unittest.main()
