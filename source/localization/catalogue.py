"""Load separate authored locale files and retain the existing UI's stable IDs."""
import copy
import json
from pathlib import Path
import re
import unicodedata

from sgp131 import ui_copy

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent
LOCALES = ('EN', 'IT', 'FR', 'ES', 'DE')


def _pairs(items):
    result = {}
    for key, value in items:
        if key in result:
            raise ValueError('duplicate locale key: ' + key)
        result[key] = value
    return result


def load_strings(locale, kind='strings'):
    if kind == 'strings':
        return {key: value for part in ('messages', 'ui', 'guide')
                for key, value in load_strings(locale, part).items()}
    if locale not in LOCALES or kind not in ('messages', 'ui', 'guide', 'documents', 'evolution'):
        raise ValueError('unsupported locale catalogue')
    path = HERE / 'locales' / locale / (kind + '.json')
    raw = path.read_bytes()
    if len(raw) > 2 * 1024 * 1024:
        raise ValueError('locale catalogue size')
    data = json.loads(raw, object_pairs_hook=_pairs)
    if (set(data) != {'schema', 'language', 'strings'} or data['schema'] != 1
            or data['language'] != locale or type(data['strings']) is not dict
            or any(type(key) is not str or type(value) is not str
                   for key, value in data['strings'].items())):
        raise ValueError('invalid locale catalogue')
    return {key: unicodedata.normalize('NFC', value).replace('\u00a0', ' ')
            for key, value in data['strings'].items()}


def footer_runs(text, expected_keys):
    matches = list(re.finditer(r'(?<!\S)([ABXY])\s+', text))
    if tuple(match[1] for match in matches) != tuple(expected_keys):
        raise ValueError('translated footer button mapping')
    runs = []
    prefix = text[:matches[0].start()].strip() if matches else text.strip()
    if prefix:
        runs.append(dict(key='', text=prefix))
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        label = text[match.end():end].strip()
        if not label:
            raise ValueError('empty translated button label')
        runs.extend([dict(key=match[1], text=match[1]), dict(key='', text=label)])
    reconstructed = ''
    for index, run in enumerate(runs):
        if index:
            reconstructed += ' ' if runs[index - 1]['key'] else '  '
        reconstructed += run['text']
    return reconstructed, runs


def ui_catalogue(locales=LOCALES):
    if not {'EN', 'IT'} <= set(locales) <= set(LOCALES):
        raise ValueError('shared UI catalogue needs EN/IT and declared locales')
    catalogue = json.loads((SOURCE / 'sgp131/data/ui-copy.json').read_text())
    for locale in locales:
        if locale in ('EN', 'IT'):
            continue
        strings = load_strings(locale, 'ui')
        for entry in catalogue['entries']:
            key = 'u:' + entry['name']
            if key not in strings:
                raise ValueError('missing UI translation: ' + locale + '/' + key)
            # This is a numeric formatter alphabet, not player-facing prose.
            value = entry['text']['EN'] if entry['name'] == 'FORMAT_POOL' else strings[key]
            if entry['name'] in catalogue['footer_runs']:
                expected = [run['key'] for run in catalogue['footer_runs'][entry['name']]['EN'] if run['key']]
                value, runs = footer_runs(value, expected)
                catalogue['footer_runs'][entry['name']][locale] = runs
            entry['text'][locale] = value
    return ui_copy.load_catalogue(json.dumps(catalogue, ensure_ascii=False))
