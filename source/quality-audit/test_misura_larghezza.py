#!/usr/bin/env python3
"""Unit tests for misura_larghezza.py. No ROM, save, BIOS or charmap file is
opened here: every fixture is a hardcoded list of integer character codes
(font metrics only, not narrative game text), taken from the three known 1.1
text refinements documented in the (superseded) `private development notes`
and reproduced against the shipped ROM's font table in this same package
(see misura_larghezza.py's module docstring for the extraction method)."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import misura_larghezza as mw  # noqa: E402

TERM = mw.TERMINATOR


def fixture_table():
    """A synthetic 509-byte width table with just the entries this test suite
    needs, taken from the real font table extracted in this session (font
    member 0 of $SGP_ROM_DIR/base-1.1-EN.nds). All other
    entries are 0 (unused by these tests)."""
    widths = {
        # code: width_px  (letter -> code -> width, from the real font table)
        304: 6,  # F
        345: 6,  # u
        338: 6,  # n
        350: 6,  # z
        333: 3,  # i
        339: 6,  # o
        327: 6,  # c
        325: 6,  # a
        332: 6,  # h
        329: 6,  # e
        336: 4,  # l
        326: 6,  # b
        348: 6,  # x
        314: 6,  # P
        301: 6,  # C
        320: 6,  # V
        344: 6,  # t
        328: 6,  # d
        330: 5,  # f
        343: 6,  # s
        331: 6,  # g
        342: 6,  # r
        478: 4,  # space
        430: 5,  # .
        435: 5,  # ' (U+2019, the game's apostrophe glyph)
    }
    table = bytearray(mw.WIDTH_TABLE_LEN)
    for code, width in widths.items():
        table[code] = width
    return bytes(table)


class ExtractWidthTableTest(unittest.TestCase):
    def test_takes_last_510_bytes_minus_padding(self):
        member = bytes(range(256)) * 200  # arbitrary, >= 510 bytes
        table = mw.extract_width_table(member)
        self.assertEqual(len(table), mw.WIDTH_TABLE_LEN)
        self.assertEqual(table, member[-510:-1])

    def test_rejects_short_member(self):
        with self.assertRaises(ValueError):
            mw.extract_width_table(b'\x00' * 100)


class KnownGuideLine11Test(unittest.TestCase):
    """The three 1.1 guide-line-11 fixes: 126 / 132 / 132 / 120 px, all under
    the 224 px ITCM guide window -- verified against the shipped ROM's own
    precomputed blob in the original session (0 differences on 24 lines)."""

    def test_all_four_known_variants_reproduce_documented_widths(self):
        table = fixture_table()
        check = mw.self_check(table)
        self.assertTrue(check['ok'], check['mismatches'])

    def test_each_variant_individually_and_fits_itcm_window(self):
        table = fixture_table()
        for name, (words, expected) in mw.KNOWN_LINE11_VARIANTS.items():
            with self.subTest(case=name):
                report = mw.measure(table, words, limit_px=mw.ITCM_GUIDE_PX)
                self.assertEqual(report['max_width_px'], expected)
                self.assertFalse(report['any_over_limit'])
                self.assertFalse(report['any_unknown_glyph'])

    def test_self_check_catches_a_drifted_table(self):
        table = bytearray(fixture_table())
        table[304] = 99  # corrupt the 'F' entry
        check = mw.self_check(bytes(table))
        self.assertFalse(check['ok'])
        self.assertTrue(check['mismatches'])


class VentodifataTest(unittest.TestCase):
    """Point 1 of the 1.1 refinements: 'Vento di Fata!' -> 'Ventodifata!'.
    No documented absolute pixel figure exists for this one (the doc only
    gives the byte cost), so the regression this test guards is structural:
    removing the two spaces around 'di' must shrink the width by exactly
    2x the space glyph's width, and the merged form must still measure
    (no unknown glyphs)."""
    V, e, n, t, o, d, i, f, a = 320, 329, 338, 344, 339, 328, 333, 330, 325
    SPACE = 478
    BANG = 430  # reusing '.' fixture width for '!' is wrong; test the delta only

    def test_removing_the_two_spaces_shrinks_width_by_two_spaces(self):
        table = fixture_table()
        with_spaces = [self.V, self.e, self.n, self.t, self.o, self.SPACE,
                       self.d, self.i, self.SPACE, self.f, self.a, self.t, self.a, TERM]
        merged = [self.V, self.e, self.n, self.t, self.o,
                  self.d, self.i, self.f, self.a, self.t, self.a, TERM]
        w_with_spaces = mw.measure(table, with_spaces)['max_width_px']
        w_merged = mw.measure(table, merged)['max_width_px']
        self.assertEqual(w_with_spaces - w_merged, 2 * table[self.SPACE])
        self.assertFalse(mw.measure(table, merged)['any_unknown_glyph'])


class ItsTargetTest(unittest.TestCase):
    """Point 3 of the 1.1 refinements: EN "it's target" -> "its target".
    Removing the single apostrophe glyph must shrink the width by exactly
    that glyph's width, and control sequences around text must be skipped
    (not counted, not crashing the parser)."""
    i, t, s, SPACE, a, r, g, e = 333, 344, 343, 478, 325, 342, 331, 329
    APOSTROPHE = 435

    def test_removing_apostrophe_shrinks_width_by_its_own_width(self):
        table = fixture_table()
        before = [self.i, self.t, self.APOSTROPHE, self.s, self.SPACE,
                  self.t, self.a, self.r, self.g, self.e, self.t, TERM]
        after = [self.i, self.t, self.s, self.SPACE,
                 self.t, self.a, self.r, self.g, self.e, self.t, TERM]
        w_before = mw.measure(table, before)['max_width_px']
        w_after = mw.measure(table, after)['max_width_px']
        self.assertEqual(w_before - w_after, table[self.APOSTROPHE])

    def test_control_sequence_is_skipped_not_summed(self):
        table = fixture_table()
        # STRVAR_1 with one argument, then "it", then terminator.
        words = [0xFFFE, 0x0100, 1, 7, self.i, self.t, TERM]
        report = mw.measure(table, words)
        self.assertEqual(len(report['lines']), 1)
        self.assertEqual(report['lines'][0]['code_count'], 2)
        self.assertEqual(report['max_width_px'], table[self.i] + table[self.t])


class LineSplittingTest(unittest.TestCase):
    def test_splits_on_all_three_line_break_codes(self):
        codes = [1, 0xE000, 2, 0x25BC, 3, 0x25BD, 4, TERM]
        lines = mw.split_lines(codes)
        self.assertEqual(lines, [[1], [2], [3], [4]])

    def test_unknown_glyph_reported_not_silently_zero(self):
        table = fixture_table()
        unknown_code = 0x0209  # just past the last real glyph (0x01EA) and the table (509 entries)
        words = [unknown_code, TERM]
        report = mw.measure(table, words)
        self.assertEqual(report['lines'][0]['width_px'], 0)
        self.assertEqual(report['lines'][0]['unknown_codes'], [unknown_code])
        self.assertTrue(report['any_unknown_glyph'])


if __name__ == '__main__':
    unittest.main()
