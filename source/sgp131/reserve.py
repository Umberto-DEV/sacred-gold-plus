"""Explicit resident policy for exact V4 inputs; never a payload installer.

Conditional subdivisions describe a future replacement of their parent ownership;
they are not additional simultaneous capacity. Proposed reservations do not grant
addresses. A reviewed reserved map may reserve them, but installation always
requires a later product installer/composition/lifecycle acceptance. This module
preserves every ROM byte and never lowers ArenaHi or repacks a cartridge.
"""
import hashlib
import json
from pathlib import Path
import re
import struct

from . import baseline
from sgp12.rom import valida_layout_arm9

SOURCE = Path(__file__).resolve().parents[1]
MAP = Path(__file__).parent / 'data/reserve-map.json'
REFERENCES = {
    'docs/arm9-reserve-map-1.3.json': '169453d2e24262c072e075a5a836343eba68cf95f392b848319517278265ea13',
    'docs/arm9-reserve-map.json': '49e15c1a2e430f7eba63ef8f603b2fdec6ecee0261aa55e359f9661ae8654408',
}
BASE, END = 0x023C8000, 0x023E0000
ARENA = [{'address': 0x020D2BB0, 'value': BASE},
         {'address': 0x020D2C5C, 'value': 0x0226EC40},
         {'address': 0x020D2C64, 'value': END}]
SUBDIVISIONS = {
    'shiny.api-config': (
        ('shiny.abi2.retained', 0x023CB100, 152, 'retained'),
        ('shiny.abi2.gap', 0x023CB198, 8, 'gap'),
        ('settings.descriptor', 0x023CB1A0, 80, 'payload'),
        ('settings.generation', 0x023CB1F0, 16, 'payload')),
    'training.extension': (
        ('training.ui', 0x023D6800, 1536, 'payload'),
        ('training.ui.guard', 0x023D6E00, 16, 'guard'),
        ('physical.code', 0x023D6E10, 1024, 'payload'),
        ('physical.slot', 0x023D7210, 48, 'payload'),
        ('narrative.spawn_table', 0x023D7240, 540, 'payload'),
        ('successor.guard', 0x023D745C, 16, 'guard'),
        # Exact SG-AI01 helper: the former zero remainder is now a named,
        # allocatable owner.  Installation still requires reserve.allocate
        # and the mechanics-stage confinement/readback checks.
        ('fairy-ai.code', 0x023D746C, 148, 'payload')),
    'plus-ui.extended': (
        ('ui.bridge.code', 0x023CB800, 8192, 'payload'),),
    'plus-ui.shiny-text': (
        ('ui.bridge.tail', 0x023CD800, 4080, 'payload'),
        ('ui.bridge.guard', 0x023CE7F0, 16, 'guard')),
    'field-guide.code': (
        ('fieldbook.code', 0x023D4000, 3072, 'payload'),
        ('fieldbook.guard', 0x023D4C00, 16, 'guard'),
        ('summary-controls.runtime', 0x023D4C10, 512, 'payload'),
        ('portable-box.runtime', 0x023D4E10, 3024, 'payload'),
        ('c8.module-stubs', 0x023D59E0, 192, 'payload'),
        ('modern-accuracy.code', 0x023D5AA0, 32, 'payload'),
        ('field-guide.code.preserved', 0x023D5AC0, 1344, 'preserved')),
    'field-guide.config-state': (
        ('guide.metadata.retained', 0x023D7B00, 16, 'retained'),
        ('guide.template', 0x023D7B10, 16, 'payload'),
        # Matches persistent.c's optional UI_PERSISTENT_RESIDENT_TOKEN_ADDRESS;
        # this typed 40-byte slot is symbolic, not installer admission.
        ('ui.bootstrap', 0x023D7B20, 40, 'payload'),
        ('ui.control', 0x023D7B48, 16, 'payload'),
        ('ui.bootstrap.guard', 0x023D7B58, 8, 'guard'),
        ('ui.module.seed', 0x023D7B60, 96, 'payload'),
        ('ui.resource.seed', 0x023D7BC0, 64, 'payload'),
        ('ui.guide.seed', 0x023D7C00, 64, 'payload'),
        ('guide.labels.retained', 0x023D7C40, 448, 'retained'),
        ('guide.field-state.retained', 0x023D7E00, 240, 'retained'),
        ('guide.canary.retained', 0x023D7EF0, 16, 'retained')),
}
# Requirements are names of missing installer proofs, never supplied evidence.
# No boolean, pointer-scan receipt or caller assertion can satisfy them here.
_GUIDE_RETIREMENT = (
    'cold-composed-native-and-installed-incoming-edges-verified',
    'old-guide-init-main-exit-and-font-callbacks-retired',
    'old-guide-res-references-retired',
    'old-fieldbook-hooks-retargeted',
    'guide-template-resident-callbacks-and-id-none')
_OPTIONS_RETIREMENT = (
    'cold-composed-native-and-installed-incoming-edges-verified',
    'old-options-init-main-exit-and-image-retired',
    'old-extended-controller-object-retired',
    'old-extended-open-and-computed-plus-e0-frame-routes-retired',
    'old-navigation-dispatch-entry-paths-excluded',
    'options-template-resident-callbacks-and-id-none',
    'old54-fallback-forbidden',
    'legacy-continue-newgame-shiny-navigation-context-preserved')
CONDITIONAL_REQUIREMENTS = {
    'plus-ui.extended': _OPTIONS_RETIREMENT,
    'plus-ui.shiny-text': _OPTIONS_RETIREMENT,
    'field-guide.code': _GUIDE_RETIREMENT,
    'field-guide.config-state': _GUIDE_RETIREMENT,
}
# One relocated authored image crosses the donor boundary without a gap. Its
# parts are metadata partitions, not separately placed or allocatable images.
CONDITIONAL_IMAGES = [
    {'name': 'ui.bridge', 'start': 0x023CB800, 'bytes': 12272,
     'parts': ['ui.bridge.code', 'ui.bridge.tail'], 'guard': 'ui.bridge.guard'}]

NATIVE = {'overlay_count': 129, 'file_count': 513,
          'static_initialized_end': 0x02111860, 'static_bss_end': 0x021E5900,
          'autoloads': [{'start': 0x01FF8000, 'bytes': 8192, 'bss': 0},
                        {'start': 0x027E0000, 'bytes': 96, 'bss': 32},
                        {'start': BASE, 'bytes': END - BASE, 'bss': 0}]}
GUARD_SPANS = ((BASE, 16), (0x023CFF00, 256), (0x023D0000, 16),
               (0x023D7F00, 256), (0x023CB100, 152), (0x023CB198, 8), (0x023D6800, 3328),
               (0x023D4000, 8192), (0x023CD800, 4096), (0x023D7B00, 1024),
               (0x023CB800, 8192))
DYNAMIC54 = {'id': 54, 'file_id': 54, 'base': 0x021E5900,
             'provisional_decoded_limit': 65536, 'bss': 0,
             'cache_alignment': 32, 'address_reserved': False}


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _canonical(value):
    try:
        return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
    except (TypeError, ValueError):
        raise ValueError('invalid non-JSON policy/allocation schema') from None


def _hash(value):
    return isinstance(value, str) and re.fullmatch('[0-9a-f]{64}', value) is not None


def _uint(value, positive=False):
    _require(type(value) is int and (1 if positive else 0) <= value <= 0xFFFFFFFF,
             'invalid unsigned numeric field')
    return value


def _span(record):
    _require(type(record) is dict, 'range must be an object')
    start, size = _uint(record.get('start'), True), _uint(record.get('bytes'), True)
    bss = _uint(record.get('bss', 0))
    _require(start % 4 == 0 and size % 4 == 0 and bss % 4 == 0,
             'unaligned resident/native range')
    _require(start + size + bss < 2**32, 'wrapped range')
    return start, start + size + bss


def _partition(parts, start, end):
    _require(type(parts) is list and parts, 'missing ownership partition')
    names, cursor = set(), start
    for part in parts:
        lo, hi = _span(part)
        name = part.get('name')
        _require(isinstance(name, str) and name and name not in names, 'duplicate/invalid owner or payload name')
        names.add(name)
        _require(lo == cursor and hi <= end, 'ownership gap, overlap, sort or containment error')
        cursor = hi
    _require(cursor == end, 'incomplete ownership coverage')


def _unique(pairs):
    result = {}
    for key, value in pairs:
        _require(key not in result, 'duplicate JSON field/payload name')
        result[key] = value
    return result


def _read_json(data):
    return json.loads(data, object_pairs_hook=_unique)


def validate_policy(policy):
    """Validate trusted source policy and immutable historical reference schema."""
    fields = {'schema', 'version', 'status', 'installation_authorized', 'base', 'end', 'arena',
              'references', 'roots', 'legacy_owners', 'subdivisions', 'conditional_images',
              'guards', 'native', 'dynamic54', 'limits'}
    _require(type(policy) is dict and set(policy) == fields, 'policy must have the exact schema fields')
    _require(type(policy.get('schema')) is int and policy['schema'] == 1, 'policy schema')
    _require(policy.get('version') == 'sgp131-resident-12'
             and policy.get('status') == 'reserved'
             and policy.get('installation_authorized') is False, 'policy status or installation authority')
    _uint(policy.get('base')); _uint(policy.get('end'))
    _require((policy['base'], policy['end']) == (BASE, END), 'reserve expansion/retirement forbidden')
    _require(_canonical(policy.get('arena')) == _canonical(ARENA), 'arena preimage policy changed')
    expected_refs = [{'path': path, 'sha256': digest} for path, digest in REFERENCES.items()]
    _require(policy.get('references') == expected_refs, 'historical reference schema/pins changed')
    references = []
    for ref in expected_refs:
        raw = (SOURCE / ref['path']).read_bytes()
        _require(_sha(raw) == ref['sha256'], 'historical source reference hash changed')
        references.append(_read_json(raw))
    current, legacy = references
    expected = [{'name': b['name'], 'start': int(b['base'], 16), 'bytes': b['bytes'],
                 'owner': b['owner'], 'kind': b['kind']} for b in current['blocks']]
    expected.append({'name': 'legacy.1.2', 'start': 0x023D8000, 'bytes': 32768,
                     'owner': 'inherited-1.2', 'kind': 'retained'})
    roots = policy.get('roots')
    _partition(roots, BASE, END)
    _require(roots == expected, 'inherited owner retirement or donor change forbidden')
    inherited = [{'name': b['nome'], 'start': int(b['base'], 16), 'bytes': b['bytes'],
                  'owner': b['proprietario']} for b in legacy['blocchi']]
    submitted = policy.get('legacy_owners')
    _require(type(submitted) is list and len(submitted) == len(inherited), 'legacy owner list schema')
    for owner in submitted:
        _require(type(owner) is dict and set(owner) == {'name', 'start', 'bytes', 'owner'}
                 and type(owner['name']) is str and type(owner['owner']) is str, 'legacy owner record schema')
        lo, hi = _span(owner)
        _require(0x023D8000 <= lo < hi <= END, 'legacy owner outside preserved parent')
    _require(submitted == inherited, 'legacy owner snapshot changed')
    subdivisions = policy.get('subdivisions')
    _require(type(subdivisions) is list and len(subdivisions) == len(SUBDIVISIONS), 'unauthorized subdivision/donor')
    parents, names, leaves = set(), set(), {}
    root_by_name = {r['name']: r for r in roots}
    for entry in subdivisions:
        _require(type(entry) is dict, 'subdivision must be an object')
        parent = entry.get('parent')
        _require(type(parent) is str and parent in SUBDIVISIONS and parent not in parents, 'unauthorized or duplicate donor')
        fields = {'parent', 'parts'}
        if parent in CONDITIONAL_REQUIREMENTS:
            fields.add('requires')
            requirements = entry.get('requires')
            _require(type(requirements) is list
                     and all(type(item) is str for item in requirements)
                     and tuple(requirements) == CONDITIONAL_REQUIREMENTS[parent],
                     'conditional retirement requirements missing or changed')
        _require(set(entry) == fields, 'subdivision schema; self-reported proof forbidden')
        parents.add(parent)
        donor = root_by_name[parent]
        _partition(entry['parts'], donor['start'], donor['start'] + donor['bytes'])
        actual = []
        for part in entry['parts']:
            _require(set(part) == {'name', 'start', 'bytes', 'kind'}
                     and type(part['name']) is str and type(part['kind']) is str,
                     'subdivision range schema')
            _require(part['name'] not in names, 'duplicate payload name')
            names.add(part['name'])
            leaves[part['name']] = part
            actual.append((part['name'], part['start'], part['bytes'], part['kind']))
        _require(tuple(actual) == SUBDIVISIONS[parent], 'fixed subdivision address/capacity changed')
    images = policy.get('conditional_images')
    _require(type(images) is list and len(images) == 1, 'conditional image schema')
    for image in images:
        _require(type(image) is dict and set(image) == {'name', 'start', 'bytes', 'parts', 'guard'},
                 'conditional image record schema')
        start, end = _span(image)
        _require(type(image['name']) is str and type(image['parts']) is list
                 and all(type(name) is str for name in image['parts'])
                 and type(image['guard']) is str, 'conditional image names/parts schema')
        _require(_canonical(images) == _canonical(CONDITIONAL_IMAGES),
                 'fixed contiguous conditional image changed')
        cursor = start
        for name in image['parts']:
            part = leaves[name]
            _require(part['kind'] == 'payload' and part['start'] == cursor,
                     'conditional image gap, overlap or guard borrowing')
            cursor += part['bytes']
        guard = leaves[image['guard']]
        _require(cursor == end == guard['start'] and guard['kind'] == 'guard'
                 and guard['bytes'] == 16
                 and end + guard['bytes'] == root_by_name['plus-ui.shiny-state']['start'],
                 'conditional image end/guard/XSTATE boundary changed')
    _require(_canonical(policy.get('native')) == _canonical(NATIVE), 'native reference bounds changed')
    guards = policy.get('guards')
    _require(type(guards) is list and len(guards) == len(GUARD_SPANS), 'guard schema')
    for guard, (start, size) in zip(guards, GUARD_SPANS):
        _span(guard)
        _require(set(guard) == {'start', 'bytes', 'sha256'} and guard['start'] == start
                 and guard['bytes'] == size and type(guard['sha256']) is dict
                 and set(guard['sha256']) == {'EN', 'IT'}
                 and all(_hash(v) for v in guard['sha256'].values()), 'native guard reference schema')
    _require(_canonical(policy.get('dynamic54')) == _canonical(DYNAMIC54), 'dynamic54 is not an allocation grant')
    _require(type(policy.get('limits')) is list and policy['limits']
             and all(type(x) is str and x for x in policy['limits']), 'missing policy limits')


def _policy():
    raw = MAP.read_bytes()
    policy = _read_json(raw)
    validate_policy(policy)
    return policy, _sha(raw)


def _chunk(data, offset, length):
    _require(type(offset) is int and type(length) is int and offset >= 0 and length >= 0
             and offset + length <= len(data), 'ROM metadata/file range out of bounds')
    return data[offset:offset + length]


def _decode(data, policy):
    """Read numeric metadata and hashes only; no extraction or ROM mutation."""
    _chunk(data, 0, 0x160)
    u32 = lambda offset: struct.unpack('<I', _chunk(data, offset, 4))[0]
    off9, ram9, len9 = u32(0x20), u32(0x28), u32(0x2C)
    _chunk(data, off9, len9)
    _require(ram9 == 0x02000000, 'unexpected ARM9 base')
    params = struct.unpack('<9I', _chunk(data, off9 + 0xBA0, 36))
    t0, t1, data0, bss0, bss1 = params[:5]
    _require(params[5] == 0 and params[7:] == (0xDEC00621, 0x2106C0DE), 'ARM9 module parameters/compression')
    _require(ram9 + 0xBC4 <= data0 == bss0 <= bss1 <= 0xFFFFFFFF
             and data0 <= t0 <= t1 <= ram9 + len9 and (t1 - t0) % 12 == 0,
             'ARM9 static/autoload metadata bounds')
    _vt0, _vt1, _vd0, rows, mapped = valida_layout_arm9(data, off9, ram9, len9)
    sections = [{'start': ram9, 'bytes': data0 - ram9, 'bss': bss1 - bss0}]
    sections.extend({'start': start, 'bytes': size, 'bss': bss}
                    for start, size, bss in rows)
    def read(address, length):
        matches = [(offset + address - start) for start, offset, size in mapped
                   if start <= address and address + length <= start + size]
        _require(len(matches) == 1, 'native guard/literal unmapped or aliased')
        return _chunk(data, matches[0], length)
    fat, fat_size, fnt, fnt_size = u32(0x48), u32(0x4C), u32(0x40), u32(0x44)
    _require(fat_size % 8 == 0 and fat_size > 0, 'malformed FAT size')
    fat_bytes = _chunk(data, fat, fat_size)
    files = []
    for at in range(fat, fat + fat_size, 8):
        start, end = struct.unpack('<2I', _chunk(data, at, 8))
        _require(start <= end, 'invalid FAT file range')
        files.append(_sha(_chunk(data, start, end - start)))
    y9, y9_size = u32(0x50), u32(0x54)
    _require(y9_size % 32 == 0, 'malformed ARM9 overlay table')
    overlays = []
    for at in range(y9, y9 + y9_size, 32):
        oid, start, size, bss, _, _, fid, _ = struct.unpack('<8I', _chunk(data, at, 32))
        overlays.append({'id': oid, 'file_id': fid, 'start': start, 'bytes': size, 'bss': bss})
    return {'sections': sections, 'overlays': overlays,
            'arena': [{'address': row['address'], 'value': struct.unpack('<I', read(row['address'], 4))[0]}
                      for row in policy['arena']],
            'guard_sha256': {str(g['start']): _sha(read(g['start'], g['bytes'])) for g in policy['guards']},
            'owner_sha256': {r['name']: _sha(read(r['start'], r['bytes'])) for r in policy['roots']},
            'preservation': {'arm7_sha256': _sha(_chunk(data, u32(0x30), u32(0x3C))),
                             'fnt_sha256': _sha(_chunk(data, fnt, fnt_size)),
                             'fat_sha256': _sha(fat_bytes), 'files_sha256': _sha(_canonical(files)),
                             'file_count': len(files), 'arm7_overlay_bytes': u32(0x5C)}}


def _audit(data, policy, digest):
    _require(type(data) is bytes, 'input must be immutable bytes')
    language = baseline.identify(data)
    meta = _decode(data, policy)
    _require(type(meta) is dict and set(meta) == {'sections', 'overlays', 'arena', 'guard_sha256',
                                                'owner_sha256', 'preservation'}, 'decoded metadata schema')
    sections = meta['sections']
    _require(type(sections) is list and len(sections) == 4, 'ARM9 section count')
    static = sections[0]
    lo, hi = _span(static)
    _require(lo == 0x02000000 and lo + static['bytes'] == NATIVE['static_initialized_end']
             and hi == NATIVE['static_bss_end'], 'static initialized/BSS bounds changed')
    _require(sections[1:] == NATIVE['autoloads'], 'autoload/reserve extent changed')
    for i, section in enumerate(sections):
        _require(set(section) == {'start', 'bytes', 'bss'}, 'ARM9 section record schema')
        lo, hi = _span(section)
        if i != 3:
            _require(hi <= BASE or lo >= END, 'section/autoload BSS overlaps reserve')
        for other in sections[:i]:
            a, b = _span(other)
            _require(hi <= a or lo >= b, 'ARM9 section overlap')
    overlays = meta['overlays']
    _require(type(overlays) is list and len(overlays) == NATIVE['overlay_count'], 'overlay count')
    ids, files = set(), set()
    for index, overlay in enumerate(overlays):
        _require(type(overlay) is dict and set(overlay) == {'id', 'file_id', 'start', 'bytes', 'bss'},
                 'overlay record schema')
        lo, hi = _span(overlay)
        oid, fid = _uint(overlay.get('id')), _uint(overlay.get('file_id'))
        _require(oid == index and oid not in ids and fid not in files and fid < NATIVE['file_count'],
                 'overlay ID/file ID changed or duplicated')
        ids.add(oid); files.add(fid)
        _require(NATIVE['static_bss_end'] <= lo < hi <= ARENA[1]['value'],
                 'overlay initialized/BSS outside native pre-arena RAM')
        _require(hi <= BASE or lo >= END, 'overlay initialized/BSS overlaps reserve')
    _require(_canonical(meta['arena']) == _canonical(ARENA), 'arena literal preimage changed')
    _require(type(meta['guard_sha256']) is dict
             and set(meta['guard_sha256']) == {str(g['start']) for g in policy['guards']}, 'guard hash schema')
    for guard in policy['guards']:
        _require(meta['guard_sha256'].get(str(guard['start'])) == guard['sha256'][language],
                 'native guard/ABI/donor preimage changed: ' + hex(guard['start']))
    preserve = meta['preservation']
    _require(type(preserve) is dict and set(preserve) == {'file_count', 'arm7_overlay_bytes',
             'arm7_sha256', 'fnt_sha256', 'fat_sha256', 'files_sha256'}, 'preservation schema fields')
    _require(_uint(preserve.get('file_count')) == NATIVE['file_count']
             and _uint(preserve.get('arm7_overlay_bytes')) == 0
             and all(_hash(preserve.get(name)) for name in
                     ('arm7_sha256', 'fnt_sha256', 'fat_sha256', 'files_sha256')), 'preservation metadata schema')
    owners = meta['owner_sha256']
    _require(type(owners) is dict and set(owners) == {r['name'] for r in policy['roots']}
             and all(_hash(v) for v in owners.values()), 'inherited owner hash schema')
    return {'schema': 1, 'language': language, 'input_sha256': _sha(data),
            'policy_version': policy['version'], 'policy_sha256': digest, 'status': policy['status'],
            'base': BASE, 'end': END, 'owned_bytes': END - BASE, 'free_bytes': 0,
            'sections': sections, 'overlays': overlays, 'overlay_count': len(overlays),
            'arena': meta['arena'], 'guard_sha256': meta['guard_sha256'],
            'owner_sha256': owners, 'preservation': preserve, 'legacy_owner_count': len(policy['legacy_owners']),
            'address_reserved': policy['status'] == 'reserved', 'installed': False,
            'installation_authorized': False, 'dynamic54': policy['dynamic54'],
            'conditional_images': policy['conditional_images'],
            'conditional_reservations': [entry for entry in policy['subdivisions']
                                         if entry['parent'] in CONDITIONAL_REQUIREMENTS],
            'limits': policy['limits']}


def audit(data: bytes) -> dict:
    """Inventory exact V4 static/autoload/overlay BSS, arena and existing owners."""
    policy, digest = _policy()
    return _audit(data, policy, digest)


FINAL_GUIDE_SLOTS = frozenset(('summary-controls.runtime','portable-box.runtime',
                              'c8.module-stubs','modern-accuracy.code'))
_ALLOCATION_FIELDS = {'schema','input_sha256','language','policy_version','policy_sha256',
                     'audit_sha256','requested','assignments','preservation','address_reserved',
                     'installed','installation_authorized'}
_INSTALLER_FIELDS = {'kind','input_sha256','ui_sha256','guide_retirement_sha256','implementation_sha256'}


def _installer_sources():
    # The grant is invalidated by changes to either writer, final reader,
    # separately reviewed retirement closure, or its immutable edge inventory.
    return {name:_sha((Path(__file__).parent/name).read_bytes()) for name in
            ('ui.py','ui_verify.py','guide_retirement.py','guide_incoming.py','ui_compile.py','reserve.py')}


def allocate(data: bytes, payloads: dict[str,int], *, installed_ui=None, charmap=None,
             work_dir=None, archive_deltas=(), overlay_deltas=()) -> dict:
    """Grant fixed map slots, with conditional Guide grants only after final readback.

    The pristine path stays fail-closed. `installed_ui` is exact immutable cold UI
    bytes; no receipt, boolean, caller row or pointer inventory supplies authority.
    For conditional requests this function independently reruns the whole final
    installer verifier and separately reviewed Guide source/compiled closure.
    """
    policy,digest=_policy();checked=_audit(data,policy,digest)
    _require(type(payloads) is dict,'payload requests must be a plain unique-name dictionary')
    slots={part['name']:(entry['parent'],part) for entry in policy['subdivisions']
           for part in entry['parts'] if part['kind']=='payload'}
    assignments=[];conditional=False
    for name,size in payloads.items():
        _require(type(name) is str and name in slots,'unknown or unassignable payload owner')
        _uint(size,True);parent,slot=slots[name]
        if parent in CONDITIONAL_REQUIREMENTS:
            _require(name in FINAL_GUIDE_SLOTS,'conditional payload requires a separately reviewed final installer verifier: '+name)
            conditional=True
        _require(size<=slot['bytes'],'payload capacity overflow: '+name)
        assignments.append(dict(name=name,parent=parent,start=slot['start'],bytes=size,capacity=slot['bytes']))
    proof=None
    if conditional:
        _require(type(installed_ui) is bytes and charmap is not None and work_dir is not None,
                 'conditional payload requires exact cold UI and independent final installer verifier')
        from . import ui_verify
        sources=_installer_sources()
        extra={'archive_deltas':archive_deltas}
        if overlay_deltas:extra['overlay_deltas']=overlay_deltas
        verified=ui_verify.verify(data,installed_ui,checked['language'],Path(charmap),Path(work_dir),**extra)
        closure=verified['retirement']['guide']
        _require(closure['input_sha256']==checked['input_sha256'] and closure['ui_sha256']==_sha(installed_ui)
                 and closure['policy_parent']=='field-guide.code','final Guide retirement image binding')
        _require(sources==_installer_sources(),'installer changed while deriving grant')
        proof=dict(kind='cold-ui-guide-retirement-v1',input_sha256=checked['input_sha256'],
                   ui_sha256=_sha(installed_ui),guide_retirement_sha256=_sha(_canonical(closure)),
                   implementation_sha256=sources)
    else:
        _require(installed_ui is None and charmap is None and work_dir is None and not archive_deltas and not overlay_deltas,
                 'unexpected conditional verifier context for ordinary allocation')
    assignments.sort(key=lambda row:row['start'])
    result=dict(schema=2 if conditional else 1,input_sha256=checked['input_sha256'],language=checked['language'],
                policy_version=policy['version'],policy_sha256=digest,audit_sha256=_sha(_canonical(checked)),
                requested=dict(sorted(payloads.items())),assignments=assignments,preservation=checked['preservation'],
                address_reserved=policy['status']=='reserved',installed=False,installation_authorized=False)
    if conditional:result['installer_verification']=proof
    validate_allocation(result,checked['language'])
    return result


def validate_allocation(allocation,language):
    """Validate grant STRUCTURE/policy/bindings and return fixed assignment rows.

    JSON hashes are not signatures. This does not authenticate caller JSON or
    certify that an installer verifier ran. Production composition MUST reissue
    via allocate with exact base+installed_ui+context and compare the full grant,
    before writing child slots. Owner modules use this only as downstream shape /
    policy constraints on that freshly derived grant, never installation admission.
    """
    _require(type(allocation) is dict,'allocation must be a plain dictionary')
    _allocation_json_tree(allocation)
    schema=allocation.get('schema')
    _require(type(schema) is int and schema in (1,2),'allocation schema')
    _require(set(allocation)==_ALLOCATION_FIELDS|({'installer_verification'} if schema==2 else set()),'allocation exact fields')
    policy,digest=_policy()
    _require(allocation['policy_version']==policy['version'] and allocation['policy_sha256']==digest,'allocation policy binding')
    _require(type(language) is str and language in ('EN','IT') and _hash(allocation['input_sha256']) and
             allocation['language']==language and baseline.INPUT_HASHES.get(allocation['input_sha256'])==language,
             'allocation canonical input/language binding')
    preservation=allocation['preservation']
    _require(_hash(allocation['audit_sha256']) and type(preservation) is dict and
             set(preservation)=={'arm7_sha256','fnt_sha256','fat_sha256','files_sha256','file_count','arm7_overlay_bytes'} and
             all(_hash(preservation[key]) for key in ('arm7_sha256','fnt_sha256','fat_sha256','files_sha256')) and
             type(preservation['file_count']) is int and preservation['file_count']==513 and
             type(preservation['arm7_overlay_bytes']) is int and preservation['arm7_overlay_bytes']==0,
             'allocation audit/preservation schema')
    _require(allocation['address_reserved'] is True and allocation['installed'] is False and
             allocation['installation_authorized'] is False,'allocation metadata flags')
    requested=allocation['requested'];_require(type(requested) is dict,'allocation requested schema')
    slots={part['name']:(entry['parent'],part) for entry in policy['subdivisions']
           for part in entry['parts'] if part['kind']=='payload'}
    rows=[];conditional=False
    for name,size in requested.items():
        _require(type(name) is str and name in slots,'unknown allocation owner')
        _uint(size,True);parent,part=slots[name]
        if parent in CONDITIONAL_REQUIREMENTS:
            _require(schema==2 and name in FINAL_GUIDE_SLOTS,'unverified conditional allocation owner')
            conditional=True
        _require(size<=part['bytes'],'allocation capacity')
        rows.append(dict(name=name,parent=parent,start=part['start'],bytes=size,capacity=part['bytes']))
    rows.sort(key=lambda row:row['start'])
    _require(type(allocation['assignments']) is list and all(type(row) is dict and
             set(row)=={'name','parent','start','bytes','capacity'} and
             all(type(row[field]) is int for field in ('start','bytes','capacity'))
             for row in allocation['assignments']) and allocation['assignments']==rows,
             'allocation assignments differ from fixed policy')
    _require(conditional==(schema==2),'allocation proof/schema mismatch')
    if conditional:
        proof=allocation['installer_verification']
        _require(type(proof) is dict and set(proof)==_INSTALLER_FIELDS,'installer proof exact fields')
        _require(proof['kind']=='cold-ui-guide-retirement-v1' and proof['input_sha256']==allocation['input_sha256']
                 and _hash(proof['ui_sha256']) and _hash(proof['guide_retirement_sha256']) and
                 proof['implementation_sha256']==_installer_sources(),'installer proof identity/source bindings')
    return rows


def _allocation_json_tree(value, parents=None):
    """Reject normalization of tuples/subclasses in integer-only receipt JSON."""
    kind = type(value)
    if kind in (dict, list):
        parents = set() if parents is None else parents
        _require(id(value) not in parents, 'cyclic allocation JSON tree')
        parents.add(id(value))
        try:
            if kind is dict:
                _require(all(type(key) is str for key in value), 'allocation JSON keys must be builtin strings')
                children = value.values()
            else:
                children = value
            for child in children:
                _allocation_json_tree(child, parents)
        finally:
            parents.remove(id(value))
    else:
        _require(kind in (str, int, bool, type(None)), 'non-builtin/non-integer allocation JSON value')


def apply(data: bytes, allocation: dict, **installer_context) -> tuple[bytes, dict]:
    """Re-derive allocation, then independently read back an unchanged image.

No payload bytes, canaries, descriptors, ROM metadata or hooks are installed.
    This is policy assignment evidence only, never product activation authority.
    """
    _require(type(allocation) is dict and type(allocation.get('requested')) is dict,
             'partial or forged allocation')
    try:
        _allocation_json_tree(allocation)
    except RecursionError:
        raise ValueError('allocation JSON tree exceeds supported depth') from None
    expected = allocate(data, allocation['requested'], **installer_context)
    _require(_canonical(allocation) == _canonical(expected), 'forged/mismatched allocation')
    readback = audit(data)
    _require(readback['policy_sha256'] == expected['policy_sha256']
             and _sha(_canonical(readback)) == expected['audit_sha256'], 'policy/audit changed during readback')
    return data, {'schema': 1, 'input_sha256': _sha(data), 'output_sha256': _sha(data),
                  'policy_sha256': expected['policy_sha256'], 'policy_version': expected['policy_version'],
                  'allocation_sha256': _sha(_canonical(expected)), 'byte_identical': True,
                  'preservation': readback['preservation'], 'address_reserved': expected['address_reserved'],
                  'installed': False, 'installation_authorized': False,
                  'validation': 'ownership assignment metadata only; no product payload installation'}
