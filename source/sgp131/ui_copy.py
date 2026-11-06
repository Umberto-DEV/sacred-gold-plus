"""Original EN/IT UIR1 copy and native-font geometry admission.

Pure functions: callers supply JSON text, a native encoder and 509 advances.
This does not extract assets, install a ROM, change the UIR1 compiler or format
runtime values. IDs are append-only; species remain in the separate 0x1001+ range.
Info is one B-only view, never paginated. Coordinates are local to the accepted
physical (8,8,240,176) Window; section headings consume a viewport slot.
"""
import json
import unicodedata

# Entry position + 1 is its immutable public resource ID. Append; never reorder.
_ENTRY_LAYOUT = """
TITLE title
VERSION version
SECTION_GAME section
SECTION_PLUS section
SECTION_SHINY section
ROW_TEXT label
ROW_SCENE label
ROW_STYLE label
ROW_AUDIO label
ROW_BUTTON label
ROW_FRAME label
ROW_DIFFICULTY label
ROW_WILD label
ROW_ANIMATION label
ROW_NPC label
ROW_WIFI label
ROW_MODE label
ROW_TARGET label
ROW_SEARCH label
VALUE_SLOW value
VALUE_MID value
VALUE_FAST value
VALUE_ON value
VALUE_OFF value
VALUE_SHIFT value
VALUE_SET value
VALUE_STEREO value
VALUE_MONO value
VALUE_NORMAL value
VALUE_BUTTON_NORMAL value
VALUE_L_EQUALS_A value
VALUE_PLUS value
VALUE_WILD_NORMAL value
VALUE_SMOOTH value
VALUE_ORIGINAL value
VALUE_CONN2 value
VALUE_CONN3 value
VALUE_CLASSIC value
VALUE_PRO value
VALUE_NONE value
VALUE_OPEN value
FRAME_01 value
FRAME_02 value
FRAME_03 value
FRAME_04 value
FRAME_05 value
FRAME_06 value
FRAME_07 value
FRAME_08 value
FRAME_09 value
FRAME_10 value
FRAME_11 value
FRAME_12 value
FRAME_13 value
FRAME_14 value
FRAME_15 value
FRAME_16 value
FRAME_17 value
FRAME_18 value
FRAME_19 value
FRAME_20 value
METHOD_LAND value
METHOD_SURF value
METHOD_OLD_ROD value
METHOD_GOOD_ROD value
METHOD_SUPER_ROD value
ACTION_APPLY action
ACTION_DISCARD action
ACTION_CONTINUE action
ACTION_CANCEL action
ACTION_PREPARE action
HEADING_TARGET heading
HEADING_METHOD heading
HEADING_VALUE heading
HEADING_EXIT heading
HEADING_APPLY heading
HEADING_ERROR heading
HEADING_INFO heading
HEADING_SEARCH heading
CONTEXT_ROOT context
FOOTER_ROOT footer
FOOTER_SELECTOR footer
FOOTER_INFO footer
FOOTER_SEARCH footer
FOOTER_CONFIRM footer
FOOTER_ERROR footer
STATUS_POKEMON status
STATUS_METHOD status
STATUS_READ_ONLY status
STATUS_SUCCESSES status
STATUS_ODDS status
STATUS_STEPS status
SEARCH_PENDING body
EXIT_PROMPT body
APPLY_PROMPT body
APPLY_SEARCH body
NO_CHANGES body
ERROR_OWNER body
NOTICE_UNAVAILABLE context
NOTICE_EMPTY context
NOTICE_METHOD context
NOTICE_NO_TARGET context
NOTICE_PRO context
NOTICE_CHARGE context
NOTICE_STALE body
NOTICE_BUSY body
NOTICE_FAILED body
INFO_TEXT preview_info
INFO_SCENE info
INFO_STYLE info
INFO_AUDIO info
INFO_BUTTON info
INFO_FRAME preview_info
INFO_DIFFICULTY info
INFO_WILD info
INFO_ANIMATION info
INFO_NPC info
INFO_WIFI info
INFO_MODE info
INFO_TARGET info
INFO_SEARCH info
INFO_SUCCESSES info
INFO_ODDS info
INFO_STEPS info
PREVIEW_TEXT body
GUIDE_CATEGORIES footer
GUIDE_LIST footer
GUIDE_PAGE footer
GUIDE_POSITION label
FORMAT_POOL pool
VALUE_PENDING value
VALUE_UNAVAILABLE value
CONTEXT_SEARCH context
GUIDE_TITLE label
GUIDE_OPEN label
GUIDE_BACK label
GUIDE_UP label
GUIDE_DOWN label
GUIDE_PREVIOUS label
GUIDE_NEXT label
GUIDE_LINK label
GUIDE_CLOSE label
GUIDE_SELECT label
GUIDE_PAGING label
""".strip().splitlines()
_LAYOUT = tuple(tuple(line.split()) for line in _ENTRY_LAYOUT)
LANGUAGES = ('EN', 'IT')
WINDOW = (8, 8, 240, 176)
VIEWPORT_Y = (36, 56, 76, 96, 116, 136)
# Separate fixed extents; a short neighbour never lends its region to long text.
HEADER_REGIONS = {'title': (9, 4, 176, 16), 'version': (183, 4, 48, 16),
                  'context': (8, 20, 193, 16), 'ordinal': (199, 20, 32, 16)}
BODY_WIDTH = 232
# label inset, label/value gap, each geometric arrow, trailing inset.
ROW_RESERVE = (4, 6, 10, 10, 4)
_ROW_NAMES = ('TEXT', 'SCENE', 'STYLE', 'AUDIO', 'BUTTON', 'FRAME',
              'DIFFICULTY', 'WILD', 'ANIMATION', 'NPC', 'WIFI', 'MODE', 'TARGET', 'SEARCH')
_VALUE_NAMES = (
    ('SLOW', 'MID', 'FAST'), ('ON', 'OFF'), ('SHIFT', 'SET'), ('STEREO', 'MONO'),
    ('BUTTON_NORMAL', 'L_EQUALS_A'), tuple('FRAME_%02d' % i for i in range(1, 21)),
    ('NORMAL', 'PLUS'), ('WILD_NORMAL', 'PLUS'), ('OFF', 'ON'),
    ('BUTTON_NORMAL', 'SMOOTH'), ('ORIGINAL', 'CONN2', 'CONN3'),
    ('CLASSIC', 'PRO'), ('NONE',), ('OPEN',))
_METHODS = ['METHOD_' + n for n in ('LAND', 'SURF', 'OLD_ROD', 'GOOD_ROD', 'SUPER_ROD')]
_STATUS = ['STATUS_SUCCESSES', 'STATUS_ODDS', 'STATUS_STEPS']


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate JSON key')
        result[key] = value
    return result


def _keys(value, keys):
    if type(value) is not dict or set(value) != set(keys):
        raise ValueError('invalid catalogue fields')


def _validate(catalogue):
    _keys(catalogue, ('schema', 'entries', 'rows', 'methods', 'status', 'footer_runs'))
    if type(catalogue['schema']) is not int or catalogue['schema'] != 1:
        raise ValueError('catalogue schema')
    entries = catalogue['entries']
    if type(entries) is not list or len(entries) != len(_LAYOUT):
        raise ValueError('missing authored copy')
    for identity, (entry, (name, role)) in enumerate(zip(entries, _LAYOUT), 1):
        _keys(entry, ('id', 'name', 'role', 'text'))
        if type(entry['id']) is not int or entry['id'] != identity or identity > 0xFFF:
            raise ValueError('unstable/duplicate authored ID')
        if type(entry['name']) is not str or entry['name'] != name or entry['role'] != role:
            raise ValueError('unstable/duplicate name or geometry role')
        _keys(entry['text'], LANGUAGES)
        for value in entry['text'].values():
            if type(value) is not str or not value or value != value.strip():
                raise ValueError('copy must be a nonempty trimmed string')
            if any(unicodedata.category(c).startswith('C') and c != '\n' for c in value):
                raise ValueError('forbidden text control')
    footers = {e['name']: e for e in entries if e['name'].startswith('FOOTER_')}
    _keys(catalogue['footer_runs'], footers)
    for name, entry in footers.items():
        _keys(catalogue['footer_runs'][name], LANGUAGES)
        for language, runs in catalogue['footer_runs'][name].items():
            if type(runs) is not list or not 1 <= len(runs) <= 8:
                raise ValueError('footer run count')
            for run in runs: _keys(run, ('key', 'text'))
            reconstructed = ''
            for index, run in enumerate(runs):
                _keys(run, ('key', 'text'))
                key, text = run['key'], run['text']
                if key not in ('', 'A', 'B', 'X', 'Y') or type(text) is not str or not text or text != text.strip():
                    raise ValueError('footer run')
                if key and (text != key or index + 1 == len(runs) or runs[index+1]['key']):
                    raise ValueError('footer key/label')
                if index: reconstructed += ' ' if runs[index-1]['key'] else '  '
                reconstructed += text
            if reconstructed != entry['text'][language]:
                raise ValueError('footer layout differs from authored copy')
    rows = catalogue['rows']
    if type(rows) is not list or len(rows) != 14:
        raise ValueError('missing owner row')
    for index, (row, name, values) in enumerate(zip(rows, _ROW_NAMES, _VALUE_NAMES)):
        _keys(row, ('row', 'label', 'info', 'values', 'presentation'))
        expected = list(values) if index == 5 else ['VALUE_' + v for v in values]
        policy = 'selector' if index == 5 else 'species' if index == 12 else 'action' if index == 13 else 'auto'
        if (type(row['row']) is not int or row['row'] != index or row['label'] != 'ROW_' + name or
                row['info'] != 'INFO_' + name or type(row['values']) is not list or row['values'] != expected or
                row['presentation'] != policy):
            raise ValueError('owner row/value domain mismatch')
    if type(catalogue['methods']) is not list or catalogue['methods'] != _METHODS:
        raise ValueError('owner method domain mismatch')
    if type(catalogue['status']) is not list or catalogue['status'] != _STATUS:
        raise ValueError('read-only search status mismatch')
    return catalogue


def load_catalogue(raw):
    """Validate strict JSON, complete languages, immutable IDs and owner domains."""
    if type(raw) is not str:
        raise ValueError('catalogue JSON must be text')
    try:
        result = json.loads(raw, object_pairs_hook=_pairs,
                            parse_constant=lambda value: (_ for _ in ()).throw(ValueError('nonfinite JSON')))
    except (TypeError, json.JSONDecodeError) as error:
        raise ValueError('invalid catalogue JSON') from error
    return _validate(result)


def ids(catalogue):
    """Return stable symbolic-name -> integer IDs after full schema admission."""
    _validate(catalogue)
    return {e['name']: e['id'] for e in catalogue['entries']}


def _encoded(text, encode):
    try:
        words = encode(text)
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError('unmapped authored character') from error
    if type(words) not in (list, tuple) or not words or words[-1] != 65535:
        raise ValueError('encoder must supply final EOS')
    if any(type(w) is not int for w in words) or any(not (1 <= w <= 509 or w == 0xE000) for w in words[:-1]):
        raise ValueError('unknown glyph, early EOS or text control')
    return tuple(words)


def _lines(text, encode, widths):
    words = _encoded(text, encode)
    lines = [[]]
    for word in words[:-1]:
        if word == 0xE000:
            lines.append([])
        else:
            lines[-1].append(word)
    if any(not line or len(line) > 128 for line in lines) or len(lines) > 11:
        raise ValueError('text exceeds rendered glyph/line bounds')
    return words, [sum(widths[w - 1] for w in line) for line in lines]


def _wrap(text, encode, widths, max_width=BODY_WIDTH):
    result = []
    for paragraph in text.split('\n'):
        if not paragraph or paragraph != paragraph.strip() or '  ' in paragraph:
            raise ValueError('invalid body paragraph whitespace')
        line = ''
        for word in paragraph.split(' '):
            candidate = word if not line else line + ' ' + word
            words = _encoded(candidate, encode)
            if 0xE000 in words or len(words) - 1 > 128 or sum(widths[w - 1] for w in words[:-1]) > max_width:
                if not line:
                    raise ValueError('unbreakable authored word exceeds width')
                result.append(line)
                line = word
                raw = _encoded(word, encode)
                if 0xE000 in raw or len(raw) - 1 > 128 or sum(widths[w - 1] for w in raw[:-1]) > max_width:
                    raise ValueError('unbreakable authored word exceeds width')
            else:
                line = candidate
        result.append(line)
    return '\n'.join(result)


def encode_catalogue(catalogue, language, encode, widths):
    """Return (ID -> EOS-terminated native words, geometry receipt).

    Admission uses actual encoded advances, never character-count estimates.
    Scalar alternatives reserve 8px per choice and 3px between choice bands;
    arrows each reserve10px. Long domains use the current value and A selector.
    Native species widths are supplied/verified separately by Class B/the scene.
    """
    _validate(catalogue)
    if type(language) is not str or language not in LANGUAGES:
        raise ValueError('catalogue language')
    if type(widths) not in (bytes, tuple, list) or len(widths) != 509 or any(type(w) is not int or not 0 <= w <= 16 for w in widths):
        raise ValueError('expected 509 native glyph advances')
    authored, measured, texts = {}, {}, {}
    for entry in catalogue['entries']:
        name, role, text = entry['name'], entry['role'], entry['text'][language]
        # Shared preview must fit the native frame's narrower200px inner area.
        width = 200 if name == 'PREVIEW_TEXT' else BODY_WIDTH
        if role in ('info', 'preview_info', 'body'):
            text = _wrap(text, encode, widths, width)
        words, line_widths = _lines(text, encode, widths)
        limit = 2 if name == 'PREVIEW_TEXT' else 4 if role == 'preview_info' else 7 if role in ('info', 'body') else 1
        if len(line_widths) > limit or max(line_widths) > width:
            raise ValueError('copy exceeds geometry: ' + name)
        if name in catalogue['footer_runs']:
            runs = catalogue['footer_runs'][name][language]
            for run in runs:
                if len(_encoded(run['text'], encode)) != len(run['text']) + 1:
                    raise ValueError('footer boundary needs one native glyph per authored character')
        authored[entry['id']] = words
        measured[name] = dict(role=role, line_widths=line_widths, glyph_units=len(words))
        texts[name] = text
    def width(name):
        return measured[name]['line_widths'][0]
    if any(max(e['line_widths']) > 200 for e in measured.values() if e['role'] == 'context'):
        raise ValueError('context exceeds fixed header region')
    # Synthetic numeric strings use only the explicit authored FORMAT_POOL alphabet.
    pool = set(next(e['text'][language] for e in catalogue['entries'] if e['name'] == 'FORMAT_POOL'))
    if not set('0123456789/:% ').issubset(pool):
        raise ValueError('missing runtime glyph alphabet')
    ordinal_width = max(_lines('%d/%d' % (position, total), encode, widths)[1][0]
                        for total in (12, 14) for position in range(1, total + 1))
    title = width('TITLE') + 8 + width('VERSION')
    context = width('CONTEXT_ROOT') + 8 + ordinal_width
    if (width('TITLE') > HEADER_REGIONS['title'][2] or
            width('VERSION') > HEADER_REGIONS['version'][2] or
            width('CONTEXT_ROOT') > HEADER_REGIONS['context'][2] or
            width('CONTEXT_SEARCH') > HEADER_REGIONS['context'][2] or
            ordinal_width > HEADER_REGIONS['ordinal'][2] or title > 240 or context > 240):
        raise ValueError('header title/context overlaps version/ordinal')
    rows = []
    for row in catalogue['rows']:
        choice_widths = [width(n) for n in row['values']]
        all_width = 17 + width(row['label']) + 13 + sum(w + 7 for w in choice_widths) + 3 * (len(choice_widths) - 1)
        current_width = 17 + width(row['label']) + 8 + max(choice_widths) + 7
        policy = row['presentation']
        if policy == 'auto':
            policy = 'alternatives' if all_width <= 224 else 'selector'
        required = all_width if policy == 'alternatives' else current_width
        if required > 224:
            raise ValueError('current value exceeds row geometry: ' + row['label'])
        rows.append(dict(row=row['row'], label_px=width(row['label']), value_px=choice_widths,
                         all_required_px=all_width, current_required_px=current_width,
                         required_px=required, presentation=policy))
    report = dict(language=language, entries=measured, rows=rows, window=list(WINDOW),
                  title_y=4, context_y=20, viewport_y=list(VIEWPORT_Y), footer_y=156,
                  header_regions={name: list(region) for name, region in HEADER_REGIONS.items()},
                  body_width=232, font_height=16, selected_band_height=20,
                  title_version_px=title, context_ordinal_px=context,
                  authored_entries=len(authored), authored_text_bytes=sum(2 * len(v) for v in authored.values()),
                  authored_directory_bytes=8 * len(authored),
                  authored_budget_bytes=sum(2 * len(v) + 8 for v in authored.values()))
    return authored, report


def c_header(catalogue):
    """Public symbolic IDs plus explicit controller-domain mapping macros."""
    mapping = ids(catalogue)
    lines = ['/* Original UI copy IDs. Generated by sgp131.ui_copy.c_header. */',
             '#ifndef SGP_SETTINGS_UI_CATALOG_H', '#define SGP_SETTINGS_UI_CATALOG_H',
             'enum SgpUiCopyId {']
    lines += ['    SGP_UI_%s = 0x%03X,' % (name, identity) for name, identity in mapping.items()]
    lines += ['};', '/* SettingsRow order; native logical values index each domain. */']
    layouts = []
    for name, languages in catalogue['footer_runs'].items():
        for language in LANGUAGES:
            runs = languages[language]; offset = 0; fields = []
            for index, run in enumerate(runs):
                if index: offset += 1 if runs[index-1]['key'] else 2
                fields += [offset, len(run['text']), 'ABXY'.find(run['key'])+1 if run['key'] else 0]
                offset += len(run['text'])
            layouts.append([mapping[name], offset+1, len(runs)] + fields + [0]*(24-len(fields)))
    lines.append('/* Authored footer ID, source units, count, then (offset,length,key) runs. */')
    cases = []
    for index, row in enumerate(layouts):
        padded = bytes(row + [0])
        values = [int.from_bytes(padded[k:k+4], 'little') for k in range(0,28,4)]
        cases.append('case %d: '%index + ''.join('p[%d]=0x%08xu;'%(i,v) for i,v in enumerate(values)) + 'return 1;')
    lines.append('#define SGP_UI_FOOTER_LAYOUT_CASES ' + ' '.join(cases))
    def macro(name, names):
        lines.append('#define SGP_UI_' + name + ' { ' + ', '.join('SGP_UI_' + n for n in names) + ' }')
    macro('ROW_LABEL_IDS', [r['label'] for r in catalogue['rows']])
    macro('ROW_INFO_IDS', [r['info'] for r in catalogue['rows']])
    for name, row in zip(_ROW_NAMES, catalogue['rows']):
        macro(name + '_VALUE_IDS', row['values'])
    macro('METHOD_IDS', catalogue['methods'])
    macro('READ_ONLY_STATUS_IDS', catalogue['status'])
    lines += ['/* FRAME_01..20 map logical frame0..19. Target species use0x1000+species.',
              ' * Only VALUE_NONE belongs to this catalogue. Read-only status has no arrows.',
              ' * Headings consume viewport slots. Info has B only; no pagination.',
              ' * FORMAT_POOL supplies numeric formatter glyphs; it is never a visible row. */',
              '#define SGP_UI_SPECIES_ID(species) (0x1000u + (species))',
              '#endif', '']
    return '\n'.join(lines)
