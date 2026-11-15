#!/usr/bin/env python3
"""Replay seven derived SDK Read inputs in isolated native wrapper/core CPUs.

The full Seek parent is authenticated and replay-checked without guest execution.
Native Read runs use payload/position-only Send0 and abstract Wait BOOL models.
This is not a continuation of the complete parent CPU or completed SDK state.
"""
from pathlib import Path
import argparse, copy, gc, gzip, importlib.util, json, mmap, struct


def load(name, path):
    s = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m


H = load('read_seek_parent', Path(__file__).with_name('attribuisci_fs_seek.py'))
B = load('read_isolated_bench', Path(__file__).parents[1] / 'test/fs_read_bench.py')
C = load('read_recovered_builder', Path(__file__).with_name('compila_fs_read.py'))
need, sha = H.need, H.sha
PARENT_SHA = '5ce9e421b4dd786274d0a524d9bcba6ae6711bb1b2808d7cc2bde8277f9028f7'


def source_identities():
    result = H.source_identities()
    for p in (__file__, B.__file__, C.__file__):
        result[str(Path(p).resolve().relative_to(H.P.SOURCE))] = sha(Path(p).read_bytes())
    return result


def derive_fixtures(parent, raw_archive):
    """Invert only the authenticated NOclobber Read model; reconstruct pre-copy frames."""
    need(not parent['pp_clobber'] and parent['variant'] == 'current', 'Read fixtures require unchanged baseline')
    reads = [r for r in parent['pp_reader']['models'] if r['name'] == 'FS_ReadFile']
    need(len(reads) == 7 and len(parent['seek']) == 5, 'Read seven ABI calls and five seeks')
    fixtures = []; seek_for = {0:0, 1:1, 3:2, 4:3, 6:4}
    expected = [(12,B.TOP-116,2,0x2007367), (20,B.TOP-116,4,0x200737D),
        (24,B.TOP-128,2,0x2007387), (3800,B.TOP-116,4,0x20073AB),
        (2508,B.TOP-120,4,0x20073C5), (2512,B.TOP-124,4,0x20073CF),
        (8780,B.DEST,16,0x2007403)]
    for ordinal, record in enumerate(reads):
        event = record['property_projection']; pos, dst, length, lr = expected[ordinal]
        need((record['position'],record['destination'],record['requested_bytes'],int(record['lr'],16)) ==
             (pos,dst,length,lr), 'Read selected source caller/geometry ABI')
        if ordinal in seek_for:
            frame = bytearray.fromhex(parent['seek'][seek_for[ordinal]]['frame_after'])
            origin = 'Seek.frame_after[' + str(seek_for[ordinal]) + ']'
        else:
            frame = bytearray.fromhex(reads[ordinal-1]['property_projection']['frame_after'])
            origin = 'previous Read projection.frame_after'
        if ordinal == 6:
            struct.pack_into('<I',frame,B.TOP-116-B.FRAME,16)
            origin += ' + native STR payload length16 at0x020073EE'
        entry = list(event['regs']); entry[0] = B.FILE; entry[15] &= ~0x20
        need(entry[:4] == record['args'] and entry[4:12] == record['saved'] and
             entry[13] == record['sp'] and entry[14] == lr and entry[12] == 0,
             'Read source-bound register inversion, not a captured entry16')
        payload = raw_archive[pos:pos+length]
        need(len(payload) == length and sha(payload) == record['delivered_sha256'] and
             record['delivered_bytes'] == record['result_r0'] == length,
             'Read payload and successful parent delivery')
        before = (frame[dst-B.FRAME:dst-B.FRAME+length] if ordinal != 6 else
                  bytes.fromhex(parent['pp_reader']['destination_before'])[:length])
        # The recorded pre-projection frame is already after the old raw copy.
        postcopy = bytearray(frame)
        if ordinal != 6: postcopy[dst-B.FRAME:dst-B.FRAME+length] = payload
        need(postcopy.hex() == event['frame_before'], 'Read true pre-copy frame source inversion')
        f = dict(ordinal=ordinal, caller_lr=hex(lr), entry=entry, frame=frame.hex(),
            destination_before=bytes(before).hex(), payload=payload.hex(), position=pos,
            provenance=dict(registers='source-bound inversion of NOclobber post-model projection; R0 restored, T cleared',
                frame=origin, original_natural_capture=False))
        B.check_fixture(f); fixtures.append(f)
    return fixtures


def require_parent_cells(rows):
    need([(r['plus'], r['seed']) for r in rows] ==
         [(p,s) for p in (0,1) for s in (0x12345678,0x12345679)],
         'Read parent requires four distinct ordered positive cells')


def prepare(rom, language, parent_report, objects, strategy_object):
    need(sha(Path(H.__file__).read_bytes()) == PARENT_SHA, 'qualified Seek parent drift')
    report = json.loads(gzip.decompress(parent_report.read_bytes()))
    need(report['schema'] == 'trainer31-native-fs-seek-v1' and report['language'] == language and
         report['cpu_executed'] is True and report['source_sha256'] == H.source_identities(),
         'Read parent report schema/source identities')
    need(report['recipes'] == [H.RUN_RECIPE,*H.CONTEXT_RECIPES,H.OFF_RECIPE,H.NATIVE_RECIPE] and
         report['namespace_bindings'] == H.BINDINGS, 'Read parent composition identities')
    model = H.P.G.S.SHARED.read_current(rom, language)
    need(report['input'] == json.loads(json.dumps(model['record'])), 'Read parent/current full input identity')
    with rom.open('rb') as fd, mmap.mmap(fd.fileno(),0,access=mmap.ACCESS_READ) as raw:
        q, proof = H.qualify(model,raw,language,objects,strategy_object)
        need(json.loads(json.dumps(proof)) == report['proof'], 'Read parent full source/ROM/recipe proof')
        data = H.resources(model,raw,language)
        require_parent_cells(report['positives'])
        for row in report['positives']: H.require_case(row,data,q)
        baseline = next(r for r in report['positives'] if r['plus'] == 1 and r['seed'] == 0x12345678)
        fixtures = derive_fixtures(baseline,data['pp_reader']['11']['raw'])
        bodies = {}; code = {}
        view = H.P.G.S.SHARED.gifts_audit.Arm9View(raw)
        for role,(address,n,digest) in C.BODIES.items():
            blob = view.read(address,n)
            need(sha(blob) == digest and blob == H.P.G.piece(model['segments'],address,n), 'Read raw/decoded body identity')
            bodies[address] = blob; code[role] = dict(ram=hex(address),rom_offset=hex(view.offset(address,n)),bytes=n,sha256=digest)
    result = dict(input=model['record'],parent_report_sha256=sha(parent_report.read_bytes()),
        parent_source_sha256=report['source_sha256'],code=code,fixtures=fixtures,
        derivation_scope='Seven baseline NOclobber ABI records; registers source-inverted and pre-copy frames reconstructed, not full original CPU snapshots')
    del model,data,q,report; gc.collect()
    return result,bodies


def save(path, result):
    path = Path(path); need(not path.exists() and not path.is_symlink() and H.P.SOURCE not in path.resolve().parents,
        'fresh private output outside source required')
    data = json.dumps(result,separators=(',',':')).encode(); need(len(data) <= 8*1024**2, 'Read report size budget')
    data = gzip.compress(data,mtime=0) if path.suffix == '.gz' else data
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('xb') as fd: fd.write(data)


def analyze(rom,language,parent_report,objects,strategy_object,raw_dir,prepare_only=False):
    sources = source_identities(); receipt,bodies = prepare(rom,language,parent_report,objects,strategy_object)
    result = dict(schema='native-fs-read-isolated-v1',language=language,source_sha256=sources,**receipt,
        cpu_executed=False,runs=[],limits=[
            'Isolated wrapper/core CPUs, not the full parent caller or natural activation',
            'Payload/position-only Send0 and abstract Wait BOOL; known error/command/queue/SYNC-clear effects excluded',
            'Native stat20 decimal is the retained SYNC store, not completed SDK state',
            'Seven finite successful lengths; no EOF/negative/overflow/async/full filesystem coverage',
            'Recovered assembly is not original MW provenance; no game/ROM/save/ABI change'])
    if not prepare_only:
        need(not raw_dir.exists() and H.P.SOURCE not in raw_dir.resolve().parents,'fresh private raw directory')
        raw_dir.mkdir(parents=True)
        policies = [('normal',{}),('off',dict(observe=False)),('wait_false',dict(wait_value=0)),
                    ('send_false',dict(send_value=0)),('clobber',dict(clobber=True)),
                    ('fill',dict(fill=0x39)),('wait_truthy2',dict(wait_value=2))]
        for name,options in policies:
            for f in receipt['fixtures']:
                r = B.run(f,bodies,**options); raw_path = raw_dir / (name+'-'+str(f['ordinal'])+'.json.gz')
                save(raw_path,r)  # Preserve raw observations before applying semantic oracles.
                B.require_result(r,bodies); result['runs'].append(dict(kind=name,result=r))
            print(language,'isolated Read',name,'seven inputs verified',flush=True)
        result['cpu_executed'] = True; require_matrix(result,bodies)
    need(sources == source_identities(),'Read source drift during run')
    return result


def require_matrix(report,bodies):
    need(report['cpu_executed'] is True and len(report['runs']) == 49 and len(report['fixtures']) == 7,
         'Read complete finite matrix')
    by_kind = {}
    policies = {'normal':(1,1,False,True,0xA5), 'off':(1,1,False,False,0xA5),
        'wait_false':(0,1,False,True,0xA5), 'send_false':(1,0,False,True,0xA5),
        'clobber':(1,1,True,True,0xA5), 'fill':(1,1,False,True,0x39),
        'wait_truthy2':(2,1,False,True,0xA5)}
    for row in report['runs']:
        kind,r = row['kind'],row['result']; need(kind in policies,'Read finite run kind')
        values = (r['policy']['wait'],r['policy']['send'],r['policy']['clobber'],r['observe'],r['fill'])
        need(values == policies[kind] and r['fixture'] == report['fixtures'][r['fixture']['ordinal']], 'Read fixture/policy binding')
        by_kind.setdefault(kind,[]).append(r); B.require_result(r,bodies)
    need(set(by_kind)==set(policies) and all([r['fixture']['ordinal'] for r in rows] == list(range(7)) for rows in by_kind.values()),'Read seven inputs per policy')
    for i,normal in enumerate(by_kind['normal']):
        for kind in ('off','send_false','wait_truthy2'):
            other = by_kind[kind][i]
            need(all(other[k] == normal[k] for k in ('returned','frame_after','destination_after','whole_ram_sha256')),
                 'Read OFF/SendFALSE/noncanonical truthy preserves output state')
        other = by_kind['wait_false'][i]
        need(other['returned'][0] == 0xFFFFFFFF and normal['returned'][0] == normal['fixture']['entry'][2] and
             all(other[k] == normal[k] for k in ('frame_after','destination_after','whole_ram_sha256')),
             'Read WaitFALSE same payload/position/RAM with native failure return')
    return True


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('rom','parent-report','objects','strategy-object','json'):
        p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--language',choices=('EN','IT'),required=True); p.add_argument('--raw-dir',type=Path)
    p.add_argument('--prepare-only',action='store_true'); a=p.parse_args()
    try:
        need(a.prepare_only or a.raw_dir is not None,'--raw-dir required for native CPU runs')
        need(not a.json.exists(),'fresh private JSON output')
        result=analyze(a.rom,a.language,a.parent_report,a.objects,a.strategy_object,a.raw_dir,a.prepare_only)
        save(a.json,result)
    except ValueError as e: p.exit(2,str(e)+'\n')
    print(a.language,'Read inputs prepared without CPU' if a.prepare_only else 'isolated native Read matrix verified')


if __name__ == '__main__': main()
