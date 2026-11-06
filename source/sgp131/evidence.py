"""Validate external evidence against requirements owned by the builder.

Evidence declares schema, through, candidate_sha256 and a cases list. Each case
has id, status=pass, candidate_sha256 and a nonempty evidence reference/record.
Caller-supplied required_cases never overrides the builder's mandatory list.
"""
import hashlib
import re
from pathlib import PurePosixPath
from . import build


def validate_acceptance(report: dict, candidate_sha256: str, *, provenance=None) -> None:
    if not isinstance(report, dict) or type(report.get('schema')) is not int or report['schema'] not in (1, 2):
        raise ValueError('unsupported acceptance schema')
    if not isinstance(candidate_sha256, str) or not re.fullmatch('[0-9a-f]{64}', candidate_sha256):
        raise ValueError('invalid candidate hash')
    if report.get('candidate_sha256') != candidate_sha256:
        raise ValueError('acceptance candidate hash mismatch')
    stage = report.get('through')
    build.require_stage(stage)
    if stage in build.UI_CHAIN:
        if report['schema'] != 2 or not isinstance(provenance, dict) or provenance.get('through') != stage:
            raise ValueError('UI acceptance requires builder provenance and schema 2')
        expected = {'language': provenance['language'], 'input_sha256': provenance['input_sha256'],
                    'config_sha256': provenance['ui_inputs']['ui_config']['sha256'],
                    'charmap_sha256': provenance['ui_inputs']['charmap']['sha256']}
        if any(report.get(key) != value for key, value in expected.items()):
            raise ValueError('UI acceptance identity mismatch')
        _digest(report.get('observer_apk_sha256'))
        _observer(report, expected['input_sha256'], candidate_sha256)
        campaign = report.get('campaign')
        if not isinstance(campaign, dict) or set(campaign) != {'reference', 'sha256'}:
            raise ValueError('invalid UI campaign reference')
        _reference(campaign['reference'], 4096)
        _digest(campaign['sha256'])
    elif report['schema'] != 1:
        raise ValueError('baseline acceptance requires schema 1')
    required = set(build.REQUIRED_CASES[stage])
    cases = report.get('cases')
    if not isinstance(cases, list):
        raise ValueError('acceptance cases must be a list')
    seen = set()
    for case in cases:
        if not isinstance(case, dict) or not isinstance(case.get('id'), str):
            raise ValueError('invalid acceptance case')
        name = case['id']
        if name in seen:
            raise ValueError('duplicate acceptance case: ' + name)
        seen.add(name)
        if case.get('status') != 'pass':
            raise ValueError('failed or skipped acceptance case: ' + name)
        if case.get('candidate_sha256') != candidate_sha256:
            raise ValueError('case candidate hash mismatch: ' + name)
        if stage in build.UI_CHAIN:
            _reference(case.get('record_key'), 256)
            _reference(case.get('evidence'), 4096)
        if not isinstance(case.get('evidence'), str) or not case['evidence'].strip():
            raise ValueError('missing case evidence: ' + name)
    if not required <= seen:
        raise ValueError('missing mandatory acceptance cases: ' + ', '.join(sorted(required - seen)))


def validate_provenance(report: dict) -> None:
    """Shared minimum builder-receipt schema for normal use and journal replay.

This validates recorded provenance, not freshness. Publication separately
    compares its source map and original input with current immutable inputs;
    exact owned-pending cleanup may use the recorded map after sources change.
    """
    if not isinstance(report, dict) or type(report.get('schema')) is not int or report['schema'] not in (1, 2):
        raise ValueError('invalid receipt provenance schema')
    build.require_stage(report.get('through'))
    sources = report.get('source_sha256')
    if not isinstance(sources, dict) or not sources:
        raise ValueError('receipt source provenance must be a nonempty hash map')
    for name, digest in sources.items():
        if (not isinstance(name, str) or not name or '\\' in name
                or PurePosixPath(name).is_absolute() or '..' in PurePosixPath(name).parts
                or not isinstance(digest, str) or not re.fullmatch('[0-9a-f]{64}', digest)):
            raise ValueError('invalid receipt source provenance entry')
    if report['through'] in build.UI_CHAIN:
        _ui_provenance(report)
        return
    if report['schema'] != 1:
        raise ValueError('baseline receipt provenance schema')
    if report.get('receipts') != []:
        raise ValueError('baseline receipt list must be present and empty')
    expected = build.verify_composition(b'', b'', [])
    composition = report.get('composition')
    if (composition != expected or not isinstance(composition, dict)
            or any(type(composition[name]) is not type(value) for name, value in expected.items())):
        raise ValueError('invalid independent baseline composition result')


def _digest(value):
    if not isinstance(value, str) or not re.fullmatch('[0-9a-f]{64}', value):
        raise ValueError('invalid UI identity hash')


def _reference(value, limit):
    if (not isinstance(value, str) or not value.strip() or len(value) > limit
            or any(ord(c) < 32 for c in value) or '\\' in value
            or '..' in PurePosixPath(value).parts or PurePosixPath(value).is_absolute()):
        raise ValueError('invalid bounded UI evidence reference')


def _activation_provenance(report):
    from . import activation
    fields = {'activation', 'mechanics_options_sha256'} & set(report)
    if not fields:
        if 'mechanics_inputs' in report:
            raise ValueError('mechanics inputs require activation provenance')
        return
    if fields != {'activation', 'mechanics_options_sha256'}:
        raise ValueError('partial activation provenance')
    _digest(report['mechanics_options_sha256'])
    result = report['activation']
    if (type(result) is not dict or set(result) != {'schema', 'active_owners', 'candidate_sha256', 'all_inert_sha256'}
            or type(result['schema']) is not int or result['schema'] != 1
            or type(result['active_owners']) is not list
            or any(type(name) is not str for name in result['active_owners'])
            or result['active_owners'] != [name for name in activation.OWNERS if name in result['active_owners']]):
        raise ValueError('invalid activation provenance record')
    _digest(result['all_inert_sha256'])
    if result['active_owners']:
        _digest(result['candidate_sha256'])
        if result['candidate_sha256'] != result['all_inert_sha256']:
            raise ValueError('activation inert root mismatch')
    elif result['candidate_sha256'] is not None:
        raise ValueError('inert owners cannot claim an activation candidate')
    if 'mechanics_inputs' in report:
        record = report['mechanics_inputs']
        if (type(record) is not dict or set(record) != {'path', 'bytes', 'sha256', 'options_sha256'}
                or type(record['path']) is not str or not PurePosixPath(record['path']).is_absolute()
                or '..' in PurePosixPath(record['path']).parts or '\\' in record['path']
                or type(record['bytes']) is not int or not 0 < record['bytes'] <= activation.MAX_CONFIG_BYTES):
            raise ValueError('invalid mechanics input provenance')
        _digest(record['sha256'])
        if record['options_sha256'] != report['mechanics_options_sha256']:
            raise ValueError('mechanics options hash mismatch')


def _ui_provenance(report):
    from . import ui_compile
    if report['schema'] != 2 or len(build.canonical(report)) > build.RECEIPT_LIMIT:
        raise ValueError('invalid UI receipt schema/size')
    _activation_provenance(report)
    records = report.get('ui_inputs')
    if not isinstance(records, dict) or set(records) != {'charmap', 'ui_config'}:
        raise ValueError('missing UI consumed input provenance')
    for key, limit in (('charmap', build.CHARMAP_LIMIT), ('ui_config', build.UI_CONFIG_LIMIT)):
        record = records[key]
        if (not isinstance(record, dict) or set(record) != {'path', 'bytes', 'sha256'}
                or not isinstance(record['path'], str) or not PurePosixPath(record['path']).is_absolute()
                or '..' in PurePosixPath(record['path']).parts or '\\' in record['path']
                or type(record['bytes']) is not int or not 0 < record['bytes'] <= limit):
            raise ValueError('invalid UI consumed input provenance')
        _digest(record['sha256'])
    from . import mechanics_stages
    names = mechanics_stages.writers(mechanics_stages.chain_for(report['through']))   # archive-only stages: no receipt
    receipts = report.get('receipts')
    if (not isinstance(receipts, list) or len(receipts) != 1 + len(names)
            or not all(isinstance(item, dict) for item in receipts)):
        raise ValueError('UI requires exactly one stage receipt' if not names else
                         'UI chain requires one UI receipt and one receipt per mechanical stage')
    stage = receipts[0]
    if names:  # mechanical stages keep the ROM length and chain by hash from the UI output to the report
        previous, size = stage.get('output_sha256'), stage.get('output_bytes')
        for name, item in zip(names, receipts[1:]):
            mechanics_stages.validate_receipt(item, name, report.get('language'))
            if (item['input_sha256'] != previous or item['input_bytes'] != size
                    or item['output_bytes'] != size):
                raise ValueError('mechanics receipt chain break at ' + name)
            previous = item['output_sha256']
        if previous != report.get('output_sha256') or size != report.get('output_bytes'):
            raise ValueError('mechanics receipt chain does not end at the reported output')
    if (type(stage.get('schema')) is not int or stage['schema'] != 1 or stage.get('stage') != 'ui'
            or stage.get('language') != report.get('language')
            or stage.get('input_sha256') != report.get('input_sha256')
            or (not names and stage.get('output_sha256') != report.get('output_sha256'))
            or type(stage.get('output_bytes')) is not int
            or (not names and stage['output_bytes'] != report.get('output_bytes'))
            or type(stage.get('input_bytes')) is not int or stage['input_bytes'] <= 0
            or not stage['input_bytes'] < stage['output_bytes'] <= stage['input_bytes'] + build.UI_APPEND_LIMIT
            or stage.get('charmap_sha256') != records['charmap']['sha256']
            or type(stage.get('file_count')) is not int or stage['file_count'] != 513
            or stage.get('all_other_bytes_preserved') is not True):
        raise ValueError('UI stage receipt identity/policy mismatch')
    for key in ('input_sha256', 'output_sha256', 'config_sha256', 'policy_sha256'):
        _digest(stage.get(key))
    config = ui_compile.validate_config(stage.get('config'))
    if hashlib.sha256(build.canonical(config)).hexdigest() != stage['config_sha256']:
        raise ValueError('UI configuration identity mismatch')
    if (not isinstance(stage.get('source_sha256'), dict) or not stage['source_sha256']
            or not isinstance(stage.get('payloads'), dict) or not stage['payloads']):
        raise ValueError('UI compiler source/toolchain provenance missing')
    _source_map(stage['source_sha256'])
    for payload in stage['payloads'].values():
        if (not isinstance(payload, dict) or not isinstance(payload.get('sources'), dict)
                or not payload['sources'] or not isinstance(payload.get('toolchain'), dict)
                or not payload['toolchain']):
            raise ValueError('UI compiler dependency/toolchain provenance missing')
        _source_map(payload['sources'])
        _digest(payload['toolchain'].get('executable_sha256'))
    if build.canonical(report.get('composition')) != build.canonical(build.composition_for(receipts)):
        raise ValueError('invalid independent UI composition result')


def _observer(report, before_sha256, after_sha256):
    observer = report.get('observer')
    if not isinstance(observer, dict) or set(observer) != {'device', 'settings', 'method', 'before', 'after'}:
        raise ValueError('UI same-observer before/after binding required')
    for key in ('device', 'settings', 'method'):
        _reference(observer[key], 4096)
    for phase, digest in (('before', before_sha256), ('after', after_sha256)):
        record = observer[phase]
        if (not isinstance(record, dict) or set(record) != {'sha256', 'apk_sha256', 'capture'}
                or record['sha256'] != digest or record['apk_sha256'] != report['observer_apk_sha256']):
            raise ValueError('UI before/after image or observer APK mismatch')
        _reference(record['capture'], 4096)


def _source_map(sources):
    for name, digest in sources.items():
        if (not isinstance(name, str) or not name or '\\' in name
                or PurePosixPath(name).is_absolute() or '..' in PurePosixPath(name).parts
                or any(ord(c) < 32 for c in name)):
            raise ValueError('invalid UI compiler source provenance')
        _digest(digest)
