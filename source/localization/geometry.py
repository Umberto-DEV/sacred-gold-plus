"""Bounded wrapping for authored ordinary field dialogue, not every text bank.

The common engine's DialogBox uses 27 tiles (216 px), two 16-pixel rows and
no automatic word wrapping. A first LF advances to row two; further lines
need the native scroll/wait character. Existing clear-page characters stay
between the same content. Words, colours and command arguments are unchanged.

Ownership comes from the actual 540 MapHeaders. Shared bank 3 also contains
battle copy, so only its authored tablet messages 1/2 are admitted. Training
menu choices, cursor-positioned text and size/unknown controls are untouched.
This is deliberately not a claim about Bag, battle, phone or other app layouts.

Variable bounds describe the current authored corpus: trainer/player names
reserve seven widest native glyphs, nicknames ten, and species/item/move/
pocket names use the localized message banks. Generic untyped placeholders
reserve the largest of those bounds. The explicit training messages use
unsigned 16-bit values from Script.buffer (opcode 198 in
sgp13/training_scripts.py); course field 1 may instead hold a stat name.
These bounds do not certify arbitrary user-authored variable substitutions.
"""
from dataclasses import dataclass, field
from functools import lru_cache
import hashlib
from pathlib import Path
import re
import struct
from typing import Callable

from ndspy.narc import NARC
from ndspy.rom import NintendoDSRom
from sgp131 import guide_content, ui_compile
from .messages import _TEXT

MAP_HEADERS, MAP_COUNT = 0x020F6BE0, 540
FONT_SHA256 = '9a17de3036f4aac8540163e560a60d83b7facde78d0ec41e688374fdbf669e73'
_TOKEN = re.compile(r'\{[^{}]*\}|\\[nrf]|\s+|[^{}\\\s]+')
_VARIABLE = re.compile(r'\{STRVAR_1:(?:(\d+):)?(\d+)(?:,0)?\}')
_ZERO_WIDTH = re.compile(r'\{(?:COLOR:[0-3]|YESNO:0)\}')
# sgp13/training.install appends the same 98 ordered entries to three banks.
_TRAINING_BASES = {385: 20, 557: 11, 630: 2}
_TRAINING_NUMBERS = frozenset({68, 69, 70, 71, 83, 84, 85, 86, 116})
_TRAINING_CHOICES = frozenset((*range(21, 30), *range(37, 42), 48, 49,
                               52, 53, 54, *range(57, 66), 73, 74, 76, 77,
                               79, 80, *range(91, 112)))


@dataclass(frozen=True)
class Context:
    field_banks: frozenset
    measure: Callable[[str], int]
    variable_widths: dict
    numeric_width: int
    stat_width: int
    limit: int = 216
    evidence: dict = field(default_factory=dict)


def _need(ok, reason):
    if not ok:
        raise ValueError('field dialogue geometry: ' + reason)


def _tokens(text):
    _need(isinstance(text, str), 'text type')
    tokens = _TOKEN.findall(text)
    _need(''.join(tokens) == text, 'unsupported text escape/token')
    return tokens


def field_banks(headers):
    """Read msgBank, not scriptsBank or translated map names."""
    _need(len(headers) == MAP_COUNT * 24, 'map header extent')
    return frozenset(struct.unpack_from('<H', headers, i * 24 + 10)[0]
                     for i in range(MAP_COUNT))


def context_from_rom(core: bytes, charmap: Path, *, messages=None) -> Context:
    """Read common-engine layout and localized names without writing a ROM.

    Pass the fully translated message NARC as ``messages`` before wrapping;
    this includes authored item/move names as well as official donor names.
    Input cartridge admission remains the enclosing composer's responsibility.
    """
    _need(hashlib.sha256(Path(charmap).read_bytes()).hexdigest() == guide_content.CHARMAP_SHA256,
          'charmap identity')
    rom = NintendoDSRom(core)
    sections = rom.loadArm9().sections
    def arm(address, size):
        matches = [bytes(s.data[address-s.ramAddress:address-s.ramAddress+size])
                   for s in sections if s.ramAddress <= address
                   and address+size <= s.ramAddress+len(s.data)]
        _need(len(matches) == 1, 'unmapped layout address')
        return matches[0]
    _need(arm(0x0205B520, 4) == bytes.fromhex('1b220192'), 'native 27-tile window preimage')
    banks = field_banks(arm(MAP_HEADERS, MAP_COUNT * 24))
    font = bytes(NARC(rom.getFileByName('a/0/1/6')).files[0])
    _need(hashlib.sha256(font).hexdigest() == FONT_SHA256, 'native font identity')
    metrics = ui_compile.module(ui_compile.SOURCE/'quality-audit/misura_larghezza.py',
                                'field_dialogue_metrics')
    widths = metrics.extract_width_table(font)
    chars, commands = _TEXT.load_charmap(charmap)
    codec = ui_compile.module(ui_compile.SOURCE/'features/options/tools/codifica_testo.py',
                             'field_dialogue_codec')
    table, _ = codec.carica_charmap(charmap)
    @lru_cache(maxsize=32768)
    def measure(text):
        result = metrics.measure(widths, codec.codifica(text, table))
        _need(not result['any_unknown_glyph'] and len(result['lines']) == 1,
              'literal glyph/line syntax')
        return result['max_width_px']
    archive_raw = messages if messages is not None else rom.getFileByName('a/0/2/7')
    archive = NARC(archive_raw).files
    _need(max(banks) < len(archive), 'map message bank outside archive')
    def maximum(indices, selected=None):
        values = []
        for bank in indices:
            rows = _TEXT.read_bank(archive[bank], chars, commands)
            for i, row in enumerate(rows):
                if selected is not None and i not in selected:
                    continue
                # Article/species and pocket banks contain native colour
                # wrappers (including 255); they have no horizontal advance.
                colours = all(command == 0xFF00 and len(args) == 1
                              for command, args in row['controls'])
                _need(colours and not row['unknown_codes'] and not row['malformed_controls'],
                      'native variable name syntax')
                measured = metrics.measure(widths, row['normalized'])
                _need(not measured['any_unknown_glyph'] and len(measured['lines']) == 1,
                      'native variable name geometry')
                values.append(measured['max_width_px'])
        _need(bool(values), 'missing localized variable names')
        return max(values)
    widest = max(widths)
    bounds = {3: max(7*widest, maximum((729,))),
              1: max(10*widest, maximum((237, 238))),
              6: maximum((750,)), 8: maximum((222, 223, 224)),
              31: maximum((226,))}
    bounds[0] = max(bounds.values())
    numeric = 5 * max(measure(str(i)) for i in range(10))
    stats = max(maximum((443,), set(range(6))), maximum((385,), set(range(60, 66))))
    evidence = dict(field_bank_count=len(banks), field_banks=sorted(banks), limit_px=216,
                    native_rows=2, variable_widths_px=bounds, training_u16_width_px=numeric,
                    training_stat_width_px=stats, font_sha256=FONT_SHA256,
                    names_archive_sha256=hashlib.sha256(archive_raw).hexdigest())
    return Context(banks, measure, bounds, numeric, stats, evidence=evidence)


def _training_index(bank, message):
    base = _TRAINING_BASES.get(bank)
    return message-base+20 if base is not None and message is not None and base <= message < base+98 else None


def _scope(bank, tokens, context, message):
    if bank not in context.field_banks:
        return 'non-field-bank'
    if bank == 3 and message not in (1, 2):
        return 'shared-battle-bank'
    if _training_index(bank, message) in _TRAINING_CHOICES:
        return 'training-menu-choice'
    for token in tokens:
        variable = _VARIABLE.fullmatch(token)
        if variable and int(variable[1] or 0) not in context.variable_widths:
            return 'unreviewed-variable-kind'
    if any(t.startswith('{') and not (_VARIABLE.fullmatch(t) or _ZERO_WIDTH.fullmatch(t))
           for t in tokens):
        return 'positioned-sized-or-unreviewed-control'
    return None


def _width(token, bank, context, message):
    variable = _VARIABLE.fullmatch(token)
    if variable:
        kind, slot = variable.groups()
        training = _training_index(bank, message)
        if kind is None and training in _TRAINING_NUMBERS:
            return max(context.numeric_width, context.stat_width) if (
                training in (83, 84) and int(slot) == 1) else context.numeric_width
        return context.variable_widths.get(int(kind or 0), context.variable_widths[0])
    if _ZERO_WIDTH.fullmatch(token):
        return 0
    return context.measure(token)


def _signature(text):
    # Clear pages remain anchored to exactly the same words and commands.
    return tuple(tuple(t for t in _tokens(page) if not t.isspace() and t not in (r'\n', r'\f'))
                 for page in text.split(r'\r'))


def layout(bank: int, text: str, context: Context, *, message=None) -> str:
    """Wrap an owned message; leave every excluded context byte-for-byte intact."""
    tokens = _tokens(text)
    if _scope(bank, tokens, context, message):
        return text
    output, word = [], []
    x = row = 0
    space = False
    def flush():
        nonlocal word, x, row, space
        if not word:
            return
        width = sum(_width(t, bank, context, message) for t in word)
        _need(width <= context.limit, f'unbreakable word/variable exceeds window at {bank}:{message}')
        gap = context.measure(' ') if space and x else 0
        if x + gap + width > context.limit:
            output.append(r'\n' if row == 0 else r'\f')
            row = 1
            x = gap = 0
        if gap:
            output.append(' ')
        output.extend(word)
        x += gap + width
        word = []
        space = False
    for token in tokens:
        if token.isspace():
            flush()
            space = True
        elif token in (r'\n', r'\r', r'\f'):
            flush()
            output.append(r'\f' if token == r'\n' and row else token)
            row = 0 if token == r'\r' else 1 if token == r'\n' else row
            x = 0
            space = False
        else:
            word.append(token)
    flush()
    result = ''.join(output)
    check(bank, text, result, context, message=message)
    return result


def check(bank: int, before: str, after: str, context: Context, *, message=None) -> dict:
    """Independent readback of content, clear pages, command order and geometry."""
    tokens = _tokens(before)
    reason = _scope(bank, tokens, context, message)
    if reason:
        _need(before == after, 'outside-scope text changed')
        return dict(status='outside-scope', reason=reason)
    _need(_signature(before) == _signature(after), 'content/clear-page/command invariant')
    widths, width, row = [], 0, 0
    for token in _tokens(after):
        if token in (r'\n', r'\r', r'\f'):
            widths.append(width)
            if token == r'\n':
                _need(row == 0, 'third unscrolled row')
                row = 1
            elif token == r'\r':
                row = 0
            width = 0
        else:
            width += context.measure(token) if token.isspace() else _width(token, bank, context, message)
        _need(width <= context.limit, 'line width exceeds window')
    widths.append(width)
    return dict(status='checked', lines=len(widths), max_width_px=max(widths),
                changed=before != after)
