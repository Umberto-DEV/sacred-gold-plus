"""Closed static lineage for the two 1.3.1 native menu input corrections.

These are NOT new runtime observations. Only two LDR immediates in overlay54
and its two Module96 CRC32 fields differ from the measured predecessor. The
whole back-projected image must equal that predecessor, including Portable.
No caller can supply an extra window, mask, candidate or activation profile.
"""
import hashlib
import json

SCENE = 'features/ui-native/scene.c'
SCENE_SHA256 = '2559f576012335564fb8ac18f4496d12228160de7ef4030791394dbd8f542b8d'
CASES = {
    "EN": {
        "measured_inert_sha256": "d2101c0e812802e03caa2fe9013d0bfbf947d19698b9cbc0bf62e36121d1b068",
        "inert_sha256": "949aafe759ab110a16d3d1fe17246bb7817c66c5b1257a20a69f9e50183d404e",
        "output_sha256": "185dc5c53a75652c021ced65157e1c3388cd661ebe90775e5b49314aee753b08",
        "bytes": 152786376,
        "options_sha256": "f5f4167fc946353cc0c4b78630badfd420b6a327d12ae713495e6f502cc67ea0",
        "windows": [
            [
                1209424,
                "3cbeb697",
                "13043bc0"
            ],
            [
                1209440,
                "9dcb6935",
                "347d18ac"
            ],
            [
                147405474,
                "0a",
                "4a"
            ],
            [
                147405479,
                "4a",
                "8a"
            ]
        ]
    },
    "IT": {
        "measured_inert_sha256": "fd347c3887fee90cd817cb3634cc120ce40ff3418dfa2d538ac9044800ae6da5",
        "inert_sha256": "e74f2368656010c420596ab222fd4cea4cffa217bd55d36c8968425ee31e4372",
        "output_sha256": "b68ddd5691538c3895b75f3f20db5a163b2bd8376629f59d2a9d55dc05935bce",
        "bytes": 159029292,
        "options_sha256": "2a37494b3b63f33ea7987467973b9b7a1b20d0ad3db657492bd6bd696fc8d610",
        "windows": [
            [
                1209424,
                "3cbeb697",
                "13043bc0"
            ],
            [
                1209440,
                "9dcb6935",
                "347d18ac"
            ],
            [
                153288354,
                "0a",
                "4a"
            ],
            [
                153288359,
                "4a",
                "8a"
            ]
        ]
    }
}


def _case(language, options_sha256, output_sha256, output_bytes):
    case = CASES.get(language) if type(language) is str else None
    if (case is None or type(output_bytes) is not int
            or (options_sha256, output_sha256, output_bytes) !=
            (case['options_sha256'], case['output_sha256'], case['bytes'])):
        raise ValueError('activation: final all-inert ROM differs from the common captured candidate; unknown static UI input derivation identity')
    return case


def record(language, options_sha256, output_sha256, output_bytes):
    case = _case(language, options_sha256, output_sha256, output_bytes)
    return {'schema': 2, 'active_owners': ['portable'],
            'candidate_sha256': case['measured_inert_sha256'],
            'all_inert_sha256': case['inert_sha256'],
            'derivation': {'id': 'native-menu-input-2026-11-06',
                           'method': 'exact-byte-backprojection',
                           'runtime_acceptance': 'not-run',
                           'scene_sha256': SCENE_SHA256,
                           'restored_sha256': case['measured_inert_sha256'],
                           'changed_bytes': 10}}


def derive(final_rom, projected, options, language):
    from . import ui_compile
    sha = lambda raw: hashlib.sha256(raw).hexdigest()
    options_sha = sha(options.wire)
    output_sha = sha(final_rom)
    case = _case(language, options_sha, output_sha, len(final_rom))
    if (options.active_owners != ('portable',)
            or options.candidate_sha256 != case['measured_inert_sha256']
            or sha(projected) != case['inert_sha256']
            or ui_compile.SOURCE_PINS.get(SCENE) != SCENE_SHA256):
        raise ValueError('activation: static UI input derivation context mismatch')
    restored = bytearray(projected)
    end = 0
    for start, old_hex, new_hex in case['windows']:
        old, new = bytes.fromhex(old_hex), bytes.fromhex(new_hex)
        if (start < end or len(old) != len(new)
                or restored[start:start + len(new)] != new):
            raise ValueError('activation: static UI input derivation preimage mismatch')
        end = start + len(new)
        restored[start:end] = old
    if sha(restored) != case['measured_inert_sha256']:
        raise ValueError('activation: static UI input backprojection mismatch')
    return record(language, options_sha, output_sha, len(final_rom))


def validate_report(report):
    expected = record(report.get('language'), report.get('mechanics_options_sha256'),
                      report.get('output_sha256'), report.get('output_bytes'))
    if (report.get('through') != 'identity'
            or json.dumps(report.get('activation'), sort_keys=True, allow_nan=False) !=
            json.dumps(expected, sort_keys=True, allow_nan=False)):
        raise ValueError('activation: static UI input derivation receipt mismatch')
    receipts = report.get('receipts')
    if type(receipts) is not list or not receipts or type(receipts[0]) is not dict:
        raise ValueError('activation: missing static UI input stage provenance')
    stage = receipts[0]
    payloads = stage.get('payloads')
    if type(payloads) is not dict or type(payloads.get('scene')) is not dict:
        raise ValueError('activation: missing static UI input compiler provenance')
    maps = (report.get('source_sha256'), stage.get('source_sha256'),
            payloads['scene'].get('sources'))
    if any(type(sources) is not dict or sources.get(SCENE) != SCENE_SHA256 for sources in maps):
        raise ValueError('activation: static UI input source provenance mismatch')
