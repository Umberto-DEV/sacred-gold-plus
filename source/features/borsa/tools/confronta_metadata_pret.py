#!/usr/bin/env python3
"""Compare caller-supplied PRET command metadata without changing production pins.

This checks JSON structure and label changes, never cartridge code or execution.
No ROM, upstream import, network or third-party package is used.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

MAX_BYTES = 2 * 1024 * 1024


def _pairs(items):
    result = {}
    for key, value in items:
        if key in result:
            raise ValueError('duplicate JSON key: ' + key)
        result[key] = value
    return result


def _nonfinite(value):
    raise ValueError('non-finite JSON value: ' + value)


def parse(raw):
    if len(raw) > MAX_BYTES:
        raise ValueError('metadata exceeds 2 MiB')
    try:
        return json.loads(raw.decode('utf-8'), object_pairs_hook=_pairs,
                          parse_constant=_nonfinite)
    except RecursionError as error:
        raise ValueError('metadata nesting exceeds parser capacity') from error


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)


def _without_names(document):
    if type(document) is not dict or type(document.get('commands')) is not list:
        raise ValueError('metadata requires a commands list')
    commands = document['commands']
    if any(type(c) is not dict or type(c.get('name')) is not str or not c['name']
           for c in commands):
        raise ValueError('every command requires a nonempty string name')
    return {**document, 'commands': [{k: v for k, v in c.items() if k != 'name'}
                                    for c in commands]}


def compare(before, after):
    old_structure, new_structure = _without_names(before), _without_names(after)
    same_structure = _canonical(old_structure) == _canonical(new_structure)
    identical = _canonical(before) == _canonical(after)
    renames = [{'id': i, 'before': old['name'], 'after': new['name']}
               for i, (old, new) in enumerate(zip(before['commands'], after['commands']))
               if old['name'] != new['name']]
    return {'schema': 1, 'status': 'identical' if identical else
            'labels-only' if same_structure else 'incompatible',
            'command_counts': [len(before['commands']), len(after['commands'])],
            'all_non_name_fields_equal': same_structure, 'renames': renames,
            'production_admission': False, 'rom_execution_proved': False}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--before', type=Path, required=True, help='existing reference JSON')
    parser.add_argument('--after', type=Path, required=True, help='candidate reference JSON')
    args = parser.parse_args(argv)
    try:
        raws = []
        for path in (args.before, args.after):
            with path.open('rb') as stream:
                raws.append(stream.read(MAX_BYTES + 1))
        result = compare(*(parse(raw) for raw in raws))
        result['input_sha256'] = [hashlib.sha256(raw).hexdigest() for raw in raws]
    except (OSError, ValueError, RecursionError) as error:
        print(str(error), file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2))
    return 1 if result['status'] == 'incompatible' else 0


if __name__ == '__main__':
    raise SystemExit(main())
