"""Schema-3 packaging for the unchanged accepted five-language 1.3.2 game."""
import hashlib
import json
from pathlib import Path
import tempfile

import pack

PRIMARY_SOURCES = {'EN': 'clean-us', 'IT': 'clean-it', 'FR': 'clean-fr',
                   'ES': 'clean-es', 'DE': 'clean-de'}


def published_targets():
    """Package corrections cannot silently repin an accepted game."""
    return json.loads((pack.HERE / 'release-1.3.2.json').read_text())['targets']


def primary_patch_name(locale, version='1.3.2'):
    if locale not in PRIMARY_SOURCES:
        raise ValueError('Unknown player patch locale')
    return 'Sacred-Gold-Plus-' + pack.path_token(version) + '-' + locale + '.xdelta'


def updater_patch_name(locale, source_id, version='1.3.2'):
    if locale not in PRIMARY_SOURCES:
        raise ValueError('Unknown updater patch locale')
    return ('Sacred-Gold-Plus-' + pack.path_token(version) + '-' + locale
            + '-from-' + pack.path_token(source_id) + '.xdelta')


def asset_names(cfg):
    stem = 'Sacred-Gold-Plus-' + cfg['version'] + '-' + cfg['package_revision']
    return stem + '-Multilingual.zip', stem + '-Optional-Updaters.zip'


def _document_pins(rows, names, label):
    if (not isinstance(rows, list)
            or any(not isinstance(row, dict) or set(row) != {'name', 'sha256', 'bytes'}
                   or not pack._content_pin(row) or row['bytes'] > pack.MAX_REFERENCE_MEMBER_BYTES
                   for row in rows)
            or [row['name'] for row in rows] != names):
        raise ValueError('Missing or wrong player documents: ' + label)


def validate_contract(cfg):
    """Require accepted game identities and an explicit selection of player files."""
    locales = set(pack.MULTILINGUAL_LOCALES)
    if cfg.get('schema') != 3 or cfg.get('version') != '1.3.2' or cfg.get('package_revision') != 'r2':
        raise ValueError('Schema 3 requires the five-language 1.3.2 package revision r2')
    if 'references' in cfg or 'original_documents' in cfg:
        raise ValueError('Schema 3 does not import historical reference documents')
    targets = cfg.get('targets', {})
    if not isinstance(targets, dict) or set(targets) != locales:
        raise ValueError('Missing or extra player target locale')
    accepted = published_targets()
    for locale, row in targets.items():
        if (not pack._content_pin(row) or set(row) - {'sha256', 'bytes', 'name'}
                or any(row[key] != accepted[locale][key] for key in ('sha256', 'bytes'))):
            raise ValueError('Player target differs from the accepted 1.3.2 game: ' + locale)
        if 'name' in row:
            pack.member_names([row['name']])
            if Path(row['name']).name != row['name']:
                raise ValueError('Target name must be a basename')
    _validate_sources(cfg, locales)
    _validate_documents(cfg, locales)
    if cfg.get('cheats_policy') not in ('omit-unverified', 'verified-localized'):
        raise ValueError('Schema 3 omits unverified cheat catalogues')
    decoder = json.loads((pack.HERE / 'release-1.3.2.json').read_text())['rompatcher_commit']
    if cfg.get('rompatcher_commit') != decoder:
        raise ValueError('Player decoder differs from the accepted pinned decoder')


def _validate_sources(cfg, locales):
    sources = cfg.get('sources')
    if not isinstance(sources, list):
        raise ValueError('Missing recognized player sources')
    registry, ids = pack.multilingual_source_registry(), []
    for row in sources:
        if (not isinstance(row, dict) or set(row) != {'id', 'label', 'sha256', 'bytes'}
                or not pack._content_pin(row) or not isinstance(row['label'], str)
                or not row['label'].strip()):
            raise ValueError('Invalid player source identity')
        source_id = pack.path_token(row['id'])
        if source_id not in registry or any(row[key] != registry[source_id][key] for key in ('sha256', 'bytes')):
            raise ValueError('Player source pin differs from recognized base: ' + source_id)
        ids.append(source_id)
    if len(ids) != len(set(ids)) or set(ids) != set(registry):
        raise ValueError('Missing, extra or duplicate recognized player source')
    routes = cfg.get('routes_by_target', {})
    if not isinstance(routes, dict) or set(routes) != locales:
        raise ValueError('Missing or extra updater route locale')
    for locale, actual in routes.items():
        if (not isinstance(actual, list) or not all(isinstance(value, str) for value in actual)
                or len(actual) != len(set(actual)) or set(actual) != set(ids)):
            raise ValueError('Missing, extra or duplicate universal updater route: ' + locale)


def _validate_documents(cfg, locales):
    metadata, localized = pack.language_metadata(), cfg.get('locales', {})
    if not isinstance(localized, dict) or set(localized) != locales:
        raise ValueError('Missing or extra player locale metadata')
    for locale, row in localized.items():
        if (not isinstance(row, dict) or set(row) != {'folder', 'documents', 'cheats'}
                or row['folder'] != metadata[locale]['folder']):
            raise ValueError('Wrong player locale folder: ' + locale)
        _document_pins(row['documents'], [f'{name}-1.3.2-{locale}.pdf'
                                        for name in pack.MULTILINGUAL_PDFS[:2]], locale)
        cheats = row['cheats']
        if not isinstance(cheats, list) or not cheats:
            raise ValueError('Missing localized Cheats contract: ' + locale)
        names = []
        for pin in cheats:
            if (not isinstance(pin, dict) or set(pin) != {'name', 'sha256', 'bytes'}
                    or not pack._content_pin(pin) or pin['bytes'] > pack.MAX_REFERENCE_MEMBER_BYTES
                    or not isinstance(pin['name'], str) or Path(pin['name']).name != pin['name']
                    or Path(pin['name']).suffix not in ('.txt', '.xml', '.mch', '.cht')):
                raise ValueError('Invalid localized Cheats pin: ' + locale)
            names.append(pin['name'])
        pack.member_names(names)
    _document_pins(cfg.get('shared_documents'), [f'{name}-1.3.2-EN.pdf'
                                              for name in pack.MULTILINGUAL_PDFS[2:]], 'shared EN guides')
    license_pin = cfg.get('license', {})
    if (not isinstance(license_pin, dict) or set(license_pin) != {'name', 'sha256', 'bytes'}
            or license_pin.get('name') != 'LICENSE.txt' or not pack._content_pin(license_pin)
            or license_pin['bytes'] > pack.MAX_REFERENCE_MEMBER_BYTES):
        raise ValueError('Invalid player license pin')


def document_members(guides, cfg):
    """Snapshot pinned current documents and Cheats using the existing safe reader."""
    members = {}
    for locale in pack.MULTILINGUAL_LOCALES:
        folder = cfg['locales'][locale]['folder']
        with pack.guide_directory_descriptor(guides / locale) as directory:
            for pin in cfg['locales'][locale]['documents']:
                raw = pack.guide_file_bytes(directory, pin['name'])
                pack.verify_bytes(raw, pin)
                if not raw.startswith(b'%PDF-'):
                    raise ValueError('Invalid localized PDF: ' + locale + '/' + pin['name'])
                pack.add_member(members, folder + '/' + pin['name'], raw)
            if locale == 'EN':
                for pin in cfg['shared_documents']:
                    raw = pack.guide_file_bytes(directory, pin['name'])
                    pack.verify_bytes(raw, pin)
                    if not raw.startswith(b'%PDF-'):
                        raise ValueError('Invalid shared EN PDF: ' + pin['name'])
                    pack.add_member(members, 'Originals/' + pin['name'], raw)
        with pack.guide_directory_descriptor(guides / locale / 'Cheats') as directory:
            for pin in cfg['locales'][locale]['cheats']:
                raw = pack.guide_file_bytes(directory, pin['name'])
                pack.verify_bytes(raw, pin)
                pack.add_member(members, folder + '/Cheats/' + pin['name'], raw)
    return members


def notice_members(cfg):
    from player_notices import license_members, start_here
    with pack.guide_directory_descriptor(pack.HERE.parents[1]) as directory:
        license_bytes = pack.guide_file_bytes(directory, 'LICENSE')
    pack.verify_bytes(license_bytes, cfg['license'])
    members = {}
    folders = {locale: cfg['locales'][locale]['folder'] for locale in pack.MULTILINGUAL_LOCALES}
    for locale, folder in folders.items():
        for name, raw in license_members(locale, license_bytes).items():
            pack.add_member(members, folder + '/' + name, raw)
    pack.add_member(members, 'START-HERE.txt',
                    start_here(cfg['version'], cfg['package_revision'], folders, asset_names(cfg)[1]))
    return members


def _json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode()


def _inventoried(members, cfg):
    inventory = {name: dict(bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())
                 for name, raw in sorted(members.items())}
    pack.add_member(members, 'CONTENTS.json', _json_bytes(dict(
        schema=3, version=cfg['version'], package_revision=cfg['package_revision'], files=inventory,
        excluded_self_files=['CONTENTS.json', 'SHA256SUMS'])))
    pack.add_member(members, 'SHA256SUMS', ''.join(
        hashlib.sha256(raw).hexdigest() + '  ' + name + '\n'
        for name, raw in sorted(members.items())).encode())
    return members


def build(cfg, inputs, references, guides, output, rpjs, node='node', xdelta='xdelta3', contract=None):
    """Verify each universal route once, then write the primary and optional ZIPs."""
    from player_notices import updater_readme
    validate_contract(cfg)
    if output.exists():
        raise FileExistsError('Use a new output directory')
    paths = {key: Path(value) for key, value in json.loads(inputs.read_text()).items()}
    required = {row['id'] for row in cfg['sources']} | {'target-' + locale for locale in pack.MULTILINGUAL_LOCALES}
    if set(paths) != required:
        raise ValueError('Missing or extra player source/target input')

    def verify_inputs():
        for source in cfg['sources']:
            pack.verify_file(paths[source['id']], source)
        for locale, target in cfg['targets'].items():
            pack.verify_file(paths['target-' + locale], target)

    verify_inputs()
    primary = document_members(guides, cfg)
    notices = notice_members(cfg)
    for name, raw in notices.items():
        pack.add_member(primary, name, raw)
    sources = {row['id']: row for row in cfg['sources']}
    updaters = {name: raw for name, raw in notices.items() if name != 'START-HERE.txt'}
    manifests = {}
    for locale in pack.MULTILINGUAL_LOCALES:
        folder = cfg['locales'][locale]['folder']
        rows = [sources[source_id] for source_id in cfg['routes_by_target'][locale]]
        names = {row['id']: 'Patch/' + updater_patch_name(locale, row['id'], cfg['version']) for row in rows}
        pack.add_member(updaters, folder + '/README-Updater.txt',
                        updater_readme(locale, cfg['version'], cfg['targets'][locale], rows, names))
    with pack.pinned_git_snapshot(rpjs, cfg['rompatcher_commit']) as snapshot:
        output.mkdir(parents=True)
        with tempfile.TemporaryDirectory(prefix='sgp-package-', dir=output) as temporary:
            work = Path(temporary)
            for locale in pack.MULTILINGUAL_LOCALES:
                folder = cfg['locales'][locale]['folder']
                rows = []
                for source_id in cfg['routes_by_target'][locale]:
                    source = sources[source_id]
                    raw = pack._verified_route(source, cfg['targets'][locale], paths, locale,
                                               work, snapshot, node, xdelta)
                    relative = 'Patch/' + updater_patch_name(locale, source_id, cfg['version'])
                    pack.add_member(updaters, folder + '/' + relative, raw)
                    if source_id == PRIMARY_SOURCES[locale]:
                        pack.add_member(primary, folder + '/Patch/' + primary_patch_name(locale, cfg['version']), raw)
                    rows.append(dict(file=relative, source=source, bytes=len(raw),
                                     sha256=hashlib.sha256(raw).hexdigest()))
                    print(f'{locale}: {len(rows)}/{len(cfg["routes_by_target"][locale])} routes verified', flush=True)
                manifest = dict(schema=3, version=cfg['version'], package_revision=cfg['package_revision'],
                                language=locale, target=cfg['targets'][locale], patches=rows,
                                decoders=['xdelta3', 'RomPatcher.js'], rompatcher_commit=cfg['rompatcher_commit'])
                manifests[locale] = manifest
                pack.add_member(updaters, folder + '/manifest.json', _json_bytes(manifest))
        verify_inputs()
        return _write_outputs(cfg, output, primary, updaters, manifests, contract)


def _write_outputs(cfg, output, primary, updaters, manifests, contract):
    verified_routes = sum(len(row['patches']) for row in manifests.values())
    manifest = dict(schema=3, version=cfg['version'], package_revision=cfg['package_revision'],
                    targets=cfg['targets'], routes_by_target=cfg['routes_by_target'], routes=verified_routes,
                    primary_sources=PRIMARY_SOURCES, encoder_source_window_bytes=pack.MULTILINGUAL_SOURCE_WINDOW,
                    decoders=['xdelta3', 'RomPatcher.js'], rompatcher_commit=cfg['rompatcher_commit'])
    pack.add_member(updaters, 'manifest.json', _json_bytes(manifest))
    pack.add_member(updaters, 'README.txt', (
        'Sacred Gold Plus ' + cfg['version'] + ' optional updater patches\n\n'
        'Choose the desired output language, then the patch matching the exact source ROM\n'
        'SHA-256 and byte size in that language folder\'s manifest.json. All recognized\n'
        'sources can produce every current target language. These are input identities,\n'
        'not additional output game versions. Back up the installed ROM and raw save;\n'
        'retain the installed filename/path and save association when updating.\n\n'
        'Read README-Updater.txt in your desired output language folder. Installation\n'
        'and news PDFs, and the shared English gameplay PDFs in Originals/, are in\n'
        'the main download: ' + asset_names(cfg)[0] + '\n').encode())
    _inventoried(updaters, cfg)
    if (len([name for name in primary if name.endswith('.xdelta')]) != 5
            or any(name.endswith('.json') or '/Documents/' in name for name in primary)):
        raise ValueError('Invalid primary player package layout')
    results = []
    for name, root, members, routes in (
            (asset_names(cfg)[0], 'Sacred Gold Plus ' + cfg['version'] + '/', primary, 5),
            (asset_names(cfg)[1], 'Sacred Gold Plus ' + cfg['version'] + ' Optional Updaters/', updaters, verified_routes)):
        archive = output / name
        pack.write_zip(archive, {root + member: raw for member, raw in members.items()})
        if archive.stat().st_size >= pack.MAX_RELEASE_ASSET_BYTES:
            raise ValueError('Player ZIP must be under the GitHub 2 GiB asset limit')
        results.append(dict(file=archive.name, bytes=archive.stat().st_size, sha256=pack.digest(archive),
                            members=len(members), routes=routes))
    (output / 'SHA256SUMS').write_text(''.join(row['sha256'] + '  ' + row['file'] + '\n' for row in results))
    (output / 'verification.json').write_bytes(_json_bytes(dict(
        version=cfg['version'], package_revision=cfg['package_revision'], assets=results,
        status=cfg.get('status', 'file-reconstruction-verified'), open_gates=cfg.get('open_gates', []),
        contract_sha256=pack.digest(contract), verified_routes=verified_routes, primary_routes=5,
        primary_sources=PRIMARY_SOURCES, targets=cfg['targets'],
        scope='File reconstruction with two decoders; unchanged 1.3.2 targets. No new ROM build, game runtime or save compatibility test.')))
    return results
