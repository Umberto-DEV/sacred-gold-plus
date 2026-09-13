#!/usr/bin/env python3
"""Reusable pixel-width measurer for HGSS/Sacred Gold Plus dialogue text.

Written for SGP-1.2-LINGUA-01 (12 September 2026) to fill the gap noted in
`private development notes (ex 15-LINGUA-QA-E-TRADUZIONI.md)` section 3: no reusable pixel-width
tool existed before this file, and the "132 px su 224" figure quoted in the
superseded `private development notes` was computed ad hoc in a
session script that was never saved to the repository.

## What this measures

HGSS/Plus encodes text as 16-bit "words" (see
`source/translation/message_codec.py`): normal glyphs are single
character codes, control sequences are `0xFFFE, command, argc, arg...`, and a
message ends with `0xFFFF`. This module works directly on that decoded word
stream (`Bank(...).words[i]`, or the `normalized` field produced by
`source/translation/audit_localization.py`'s `render()`), so it needs
**no charmap and no pret/pokeheartgold checkout** -- only the numeric codes
already available from `message_codec.Bank`.

## The width table

Each glyph's on-screen advance width in pixels is a single byte in a table
embedded at the tail of font member 0 of the `a/0/1/6` NARC (the font is
shared identically between the EN and IT ROMs; member 0 and member 1 are
byte-identical in both, sha256 prefix `9a17de3036f4aac8`, matching the
`FONT_SHA` guard referenced in project history).

Empirically confirmed in this session against the shipped ROM
(`$SGP_ROM_DIR/base-1.1-EN.nds`, font member 0, 33101
bytes): the table is the **last 510 bytes of the font member, minus one
trailing unused/padding byte** -- i.e. `member_bytes[-510:-1]`, 509 bytes,
one byte per character code, indexed directly by the character's charmap
code (0x0000-0x01FC covers every printable glyph; codes above that,
including the line-break codes below, have no entry and are treated as
zero-width / "unknown").

This is one byte earlier than the offset informally noted in the superseded
`LINGUA-RIFINITURE-1.1.md` ("offset 32592, 509 byte"): 32592 = 33101 - 509
(the naive "last 509 bytes"), but the byte-exact fit -- reproducing all four
previously-verified widths for the guide-line-11 variants (126 / 132 / 132 /
120 px) -- is `33101 - 510 = 32591` through `33099` inclusive, i.e.
`data[-510:-1]`. See `test_misura_larghezza.py` for the reproduction, and
`KNOWN_LINE11_VARIANTS` below for the exact word codes used.

Line breaks are ordinary charmap codes, not control commands: `0xE000` = '\\n'
(new line within the same window), `0x25BC` = '\\r', `0x25BD` = '\\f' (per
pret/pokeheartgold `charmap.txt`, revision `0985e8718df4f25e64d6507d89c0c97c0d288981`).
All three are far outside the 509-entry table and are always treated as
zero-width line separators here, never summed into a line's width.

## Window limits

Confirmed by reproduction in this package:
  - `ITCM_GUIDE_PX = 224` -- the native EV/IV help blob in ITCM
    (`0x01FF9B70`), used to compute the guide-line-11 widths above.
Documented but NOT independently pixel-verified in this package (carried over
from `private development notes`, flagged there as "conservative"):
  - `DIALOGUE_WINDOW_PX_HYPOTHESIS = 216` -- ordinary dialogue window.
Not inventoried at all (mark any check against these as a hypothesis in
reports): Pokedex summary / search filters, Bag/Pouch list rows, Pokemon
Summary nickname/species fields, Trainer Card, other narrow menus. Each needs
its own measurement (a known-good in-game screenshot or ROM layout constant)
before a script can treat it as ground truth.

## No game text is embedded here

Every literal string in this module is either a control-flow constant, a
single ASCII/Latin-1 punctuation glyph used as a *font metrics* fixture (not
narrative text), or documentation of the codec. No dialogue, message, or
other narrative content from the ROM is stored in this file.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Iterable, Optional

WIDTH_TABLE_LEN = 509
FONT_MEMBER_TAIL = WIDTH_TABLE_LEN + 1  # trailing padding byte not part of the table
CONTROL_MARKER = 0xFFFE
TERMINATOR = 0xFFFF
# '\n' / '\r' / '\f' per pret/pokeheartgold charmap.txt -- ordinary charmap
# codes (not 0xFFFE control sequences), always outside the width table.
NEWLINE_CODES = frozenset({0xE000, 0x25BC, 0x25BD})

ITCM_GUIDE_PX = 224
DIALOGUE_WINDOW_PX_HYPOTHESIS = 216
KNOWN_LIMITS_PX = {
    'itcm_guide': (ITCM_GUIDE_PX, 'verified: reproduces 4/4 known guide-line-11 widths'),
    'dialogue_window': (DIALOGUE_WINDOW_PX_HYPOTHESIS, 'hypothesis: LOCALIZATION.md calls it "conservative", not pixel-verified here'),
}


def extract_width_table(font_member0: bytes) -> bytes:
    """Return the 509-byte glyph width table from a raw font-member-0 buffer.

    Table = the last 510 bytes of the member, dropping the final byte
    (unused/padding). Raises ValueError if the member is too short to
    contain the table at all -- a real font member 0 is 33101 bytes.
    """
    if len(font_member0) < FONT_MEMBER_TAIL:
        raise ValueError(
            f'Font member too short for a width table: {len(font_member0)} bytes, '
            f'need at least {FONT_MEMBER_TAIL}'
        )
    return bytes(font_member0[-FONT_MEMBER_TAIL:-1])


def load_width_table_from_rom(rom_path, member_index: int = 0) -> bytes:
    """Open `rom_path`, read the `a/0/1/6` font NARC, return member `member_index`'s
    width table. Requires ndspy. Only reads binary structure; prints/returns no
    game text."""
    import ndspy.narc
    import ndspy.rom

    rom = ndspy.rom.NintendoDSRom.fromFile(str(rom_path))
    narc = ndspy.narc.NARC(rom.getFileByName('a/0/1/6'))
    if not 0 <= member_index < len(narc.files):
        raise ValueError(f'Font NARC has {len(narc.files)} members, asked for {member_index}')
    return extract_width_table(narc.files[member_index])


def glyph_width(table: bytes, code: int) -> Optional[int]:
    """Width in pixels of one character code, or None if `code` has no entry
    in `table` (control/newline codes, or any glyph code >= len(table) --
    e.g. kana/Hangul ranges never measured by this tool)."""
    if 0 <= code < len(table):
        return table[code]
    return None


def split_lines(words: Iterable[int]):
    """Split a decoded message's word stream into visual lines of plain
    character codes, dropping control sequences and the terminator.

    `words` is the full stream as produced by `message_codec.Bank(...).words[i]`
    or the `normalized` field of `audit_localization.render()`: literal codes,
    `0xFFFE, command, argc, arg...` control sequences, ending in `0xFFFF`.
    Returns a list of lists of int codes (one list per line); a line can be
    empty (e.g. two consecutive line breaks).
    """
    words = list(words)
    lines: list[list[int]] = [[]]
    i = 0
    while i < len(words):
        word = words[i]
        if word == TERMINATOR:
            break
        if word == CONTROL_MARKER:
            if i + 2 >= len(words):
                break  # truncated/malformed control at the tail; nothing more to measure
            argc = words[i + 2]
            i += 3 + argc
            continue
        if word in NEWLINE_CODES:
            lines.append([])
            i += 1
            continue
        lines[-1].append(word)
        i += 1
    return lines


def line_width(table: bytes, line_codes: Iterable[int]):
    """Sum glyph widths for one line. Returns (width_px, unknown_codes) where
    unknown_codes lists codes with no table entry, contributing 0 px each --
    callers should treat a non-empty unknown_codes as "cannot certify this
    line's width", not as "this line is short"."""
    width = 0
    unknown = []
    for code in line_codes:
        w = glyph_width(table, code)
        if w is None:
            unknown.append(code)
        else:
            width += w
    return width, unknown


def measure(table: bytes, words: Iterable[int], limit_px: Optional[int] = None) -> dict:
    """Measure every visual line of a decoded message.

    Returns {'lines': [{'width_px', 'code_count', 'unknown_codes', 'over_limit'}],
    'max_width_px', 'limit_px', 'any_over_limit', 'any_unknown_glyph'}.
    `over_limit`/`any_over_limit` are None when `limit_px` is None.
    """
    lines = []
    for codes in split_lines(words):
        width, unknown = line_width(table, codes)
        over = None if limit_px is None else width > limit_px
        lines.append({
            'width_px': width,
            'code_count': len(codes),
            'unknown_codes': unknown,
            'over_limit': over,
        })
    return {
        'lines': lines,
        'max_width_px': max((l['width_px'] for l in lines), default=0),
        'limit_px': limit_px,
        'any_over_limit': None if limit_px is None else any(l['over_limit'] for l in lines),
        'any_unknown_glyph': any(l['unknown_codes'] for l in lines),
    }


# --- Self-check fixture -----------------------------------------------------
# The four guide-line-11 variants from the superseded LINGUA-RIFINITURE-1.1.md,
# as raw charmap codes (no charmap.txt needed to reproduce this check). Widths
# there were independently confirmed against the shipped ROM's own precomputed
# blob (0 differences on 24 lines); reproducing them here is the regression
# guard for this module's width-table offset.
_TERM = [TERMINATOR]
KNOWN_LINE11_VARIANTS = {
    # "Funziona anche nel box."
    'current_singular_box': (
        [304, 345, 338, 350, 333, 339, 338, 325, 478, 325, 338, 327, 332, 329,
         478, 338, 329, 336, 478, 326, 339, 348, 430] + _TERM,
        126,
    ),
    # "Funzionano anche nel PC."
    'proposed_plural_pc': (
        [304, 345, 338, 350, 333, 339, 338, 325, 338, 339, 478, 325, 338, 327,
         332, 329, 478, 338, 329, 336, 478, 314, 301, 430] + _TERM,
        132,
    ),
    # "Funzionano anche col PC."
    'proposed_plural_pc_col': (
        [304, 345, 338, 350, 333, 339, 338, 325, 338, 339, 478, 325, 338, 327,
         332, 329, 478, 327, 339, 336, 478, 314, 301, 430] + _TERM,
        132,
    ),
    # "Funziona anche col PC."
    'current_singular_pc_col': (
        [304, 345, 338, 350, 333, 339, 338, 325, 478, 325, 338, 327, 332, 329,
         478, 327, 339, 336, 478, 314, 301, 430] + _TERM,
        120,
    ),
}


def self_check(table: bytes) -> dict:
    """Recompute the four known guide-line-11 widths from `KNOWN_LINE11_VARIANTS`
    and compare to their documented values. Use this after loading a table from
    a live ROM to catch a font/table change or an offset regression before
    trusting any measurement. Returns {'ok': bool, 'mismatches': [...]}."""
    mismatches = []
    for name, (words, expected) in KNOWN_LINE11_VARIANTS.items():
        report = measure(table, words)
        got = report['max_width_px']
        if got != expected:
            mismatches.append({'case': name, 'expected': expected, 'got': got})
    return {'ok': not mismatches, 'mismatches': mismatches}


def _cli(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--rom', type=Path, help='ROM to read the font table from.')
    parser.add_argument('--font-member', type=int, default=0)
    parser.add_argument('--self-check', action='store_true',
                        help='Only run the known-widths regression check and exit.')
    parser.add_argument('--bank', type=int, help='Message bank index in a/0/2/7 (0-828).')
    parser.add_argument('--message', type=int, help='Message index within the bank.')
    parser.add_argument('--limit', type=int, default=None, help='Pixel limit to flag overflow.')
    args = parser.parse_args(argv)

    if not args.rom:
        parser.error('--rom is required (also for --self-check, to load a real table).')
    table = load_width_table_from_rom(args.rom, args.font_member)

    check = self_check(table)
    print('self_check:', check)
    if args.self_check:
        return 0 if check['ok'] else 1
    if not check['ok']:
        print('WARNING: width table failed the known-widths self-check; '
              'measurements below may not be trustworthy.', file=sys.stderr)

    if args.bank is None or args.message is None:
        return 0

    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'translation'))
    import message_codec  # noqa: E402
    import ndspy.narc
    import ndspy.rom

    rom = ndspy.rom.NintendoDSRom.fromFile(str(args.rom))
    narc = ndspy.narc.NARC(rom.getFileByName('a/0/2/7'))
    bank = message_codec.Bank(narc.files[args.bank])
    words = bank.words[args.message]
    report = measure(table, words, args.limit)
    # Only counts/booleans are printed -- no decoded text.
    print(json.dumps({
        'bank': args.bank, 'message': args.message,
        'line_count': len(report['lines']),
        'widths_px': [l['width_px'] for l in report['lines']],
        'limit_px': report['limit_px'],
        'any_over_limit': report['any_over_limit'],
        'any_unknown_glyph': report['any_unknown_glyph'],
    }, indent=2))
    return 1 if report['any_over_limit'] else 0


if __name__ == '__main__':
    sys.exit(_cli())
