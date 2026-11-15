#!/usr/bin/env python3
"""Freeze actual default-handler entry fields before a new native prefix run.

Standard library only. No default-entry whole-RAM capture exists in the parent:
its identity must be derived forward from observed RAM and native writes.
"""
from pathlib import Path
import argparse,importlib.util,json,struct

path=Path(__file__).with_name('congela_fs_send_translate_contract.py')
s=importlib.util.spec_from_file_location('default_findpath_parent_freezer',path)
P=importlib.util.module_from_spec(s);s.loader.exec_module(P)
need,sha,wire,read_report=P.need,P.sha,P.wire,P.read_report
need(sha(path.read_bytes())=='17ff65b2bef81fc582a193d00bdcca86b20530ff019c718b171e20fb922acf54','Default FindPath qualified exporter drift')
TOP,FILE,ARC,FRAME=P.P.TOP,P.P.FILE,P.P.ARC,P.P.FRAME


def prefix_state(row):
    need(row['observe']is True and row['fault']is None and wire(row['policy'])==wire(dict(early_error=False))and
         row['model_stores']==[]and len(row['services'])==1,'Default FindPath actual positive parent')
    service=row['services'][0];cp=row['checkpoints']['default_entry']
    need(service['pc']==cp['pc']=='0x20d6db0'and service['writes']==[]and service['early_error']is False and
         wire(service['entry'])==wire(cp['regs'])and service['frame_before']==cp['frame']and
         service['archive_before']==cp['archive'],'Default FindPath actual pre-model entry')
    positions=[i for i,e in enumerate(row['flow'])if e['pc']=='0x20d6984']
    need(positions==[117]and row['flow'][116]['pc']=='0x20d6980','Default FindPath finite native prefix117')
    delivered=list(row['flow'][116]['regs']);delivered[14]=0x20D6984
    need(wire(delivered)==wire(cp['regs'])and delivered[:2]==[FILE,0x20D6DB0]and
         delivered[13:16]==[TOP-336,0x20D6984,0x6000001F],'Default FindPath original BL delivery/full16')
    frame=bytearray.fromhex(row['frame_before']);archive=bytearray.fromhex(row['archive_before'])
    need((len(frame),len(archive))==(416,92),'Default FindPath initial parent owners')
    stores=row['stores'][:24];need(len(stores)==24 and stores[-1]['pc']=='0x20d68f4'and
         row['stores'][24]['pc']=='0x20d6a3c','Default FindPath native writes precede only model boundary')
    prefix_pcs={e['pc']for e in row['flow'][:117]}
    for w in stores:
        need(w['bytes']==4 and w['pc']in prefix_pcs,'Default FindPath upstream native word')
        a=w['address']
        if FRAME<=a and a+4<=TOP:m,i=frame,a-FRAME
        else:need(ARC<=a and a+4<=ARC+92,'Default FindPath upstream owner');m,i=archive,a-ARC
        need(m[i:i+4].hex()==w['before'],'Default FindPath forward native preimage');struct.pack_into('<I',m,i,w['value'])
    need(frame.hex()==cp['frame']and archive.hex()==cp['archive']and row['guard_before']==row['guard_after']=='a5'*56,
         'Default FindPath actual entry windows from ordered native writes')
    need(struct.unpack_from('<3I',frame,FILE-FRAME+12)==(0x45,4,2)and
         struct.unpack_from('<I',archive,28)[0]==0x213,'Default FindPath outer command4 and active Translate flags')
    return dict(entry=delivered,captured_frame416_sha256=sha(frame),captured_archive92_sha256=sha(archive),
        captured_guard56_sha256=sha(bytes.fromhex(row['guard_before'])),prefix_native_contexts=117,prefix_native_writes=24,
        prefix_stores_sha256=sha(wire(stores).encode()),observed_before_Send_whole_sha256=row['before_whole_ram_sha256'],
        observed_Translate_entry_whole_sha256=row['checkpoints']['translate_entry']['whole_ram_sha256'],
        default_entry_whole_observed=False)


def freeze(parent_report):
    r=read_report(parent_report)
    need(r['schema']=='native-fs-send-translate-native-v1'and r['cpu_executed']is True and r['compiler_invoked']is False and
         r['probe_only']is False and len(r['fixtures'])==16 and len(r['groups'])==4 and len(r['cases'])==12 and
         len(r['field_holdout'])==48 and len(r['observer_off'])==4 and len(r['counters'])==4,'Default FindPath complete parent grid')
    cells=[];seen=set()
    for f in r['fixtures']:
        identity=tuple(f[k]for k in('language','ordinal','plus','seed','translated_result'))
        need(f['language']in('EN','IT')and all(type(f[k])is int for k in('ordinal','plus','seed','translated_result'))and
             f['translated_result']in(0,1)and identity not in seen,'Default FindPath unique typed origin');seen.add(identity)
        g,row=P.group_row(r,f)
        cells.append(dict(language=f['language'],ordinal=f['ordinal'],plus=f['plus'],seed=f['seed'],
            ancestral_result_policy=f['translated_result'],parent_group=g['ordinal'],
            parent_send_fixture_sha256=sha(wire(f).encode()),input=prefix_state(row)))
    return dict(schema='native-fs-default-findpath-prospective-input-v1',cells=cells,parent_report_sha256=sha(parent_report.read_bytes()),
        chronology='Before new prefix oracle/compiler/guest; source and previous raw known, not blind',
        comparison='Actual entry only; no previous native prefix output or default-entry whole capture exists',
        limits=['No final FSResult comparison against the old model; prefix stops before nested Translate',
            'New frame520/guard56 adds104 bytes derived from authenticated whole ancestor, not captured here',
            'Ancestral result0/1 is provenance only, not an external policy of the zero-model prefix'])


def compare_input(cell,f,row):
    for key in('language','ordinal','plus','seed'):
        need(type(cell[key])is type(f[key])and cell[key]==f[key],'Default FindPath frozen origin')
    need(cell['ancestral_result_policy']==f['parent_send_fixture']['translated_result']and
         cell['parent_send_fixture_sha256']==sha(wire(f['parent_send_fixture']).encode()),'Default FindPath original fixture binding')
    inp=cell['input'];need(wire(row['entry'])==wire(f['entry'])==wire(inp['entry']),'Default FindPath frozen full16 input')
    frame=bytes.fromhex(row['frame_before']);need(len(frame)==520 and sha(frame[104:])==inp['captured_frame416_sha256']and
        sha(frame[48:104])==inp['captured_guard56_sha256']and sha(bytes.fromhex(row['archive_before']))==inp['captured_archive92_sha256'],
        'Default FindPath actual captured windows without mask or invented lower fill')
    need(f['observed_before_Send_whole_sha256']==inp['observed_before_Send_whole_sha256']and
         sha(wire(f['prefix_stores']).encode())==inp['prefix_stores_sha256']and inp['default_entry_whole_observed']is False,
         'Default FindPath forward provenance, not an observed default whole capture')
    return dict(passed=True,actual_input_registers=16,captured_frame_bytes=416,captured_archive_bytes=92,captured_guard_bytes=56,
                derived_additional_bytes=104,output_or_activation_proved_here=False)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in('parent-report','json'):p.add_argument('--'+key,type=Path,required=True)
    a=p.parse_args()
    try:
        source=Path(__file__).resolve().parents[3];need(source not in a.json.resolve().parents and source!=a.json.resolve(),'Default FindPath private output')
        r=freeze(a.parent_report)
        with a.json.open('x')as out:out.write(json.dumps(r,indent=2)+'\n')
    except(ValueError,KeyError,TypeError,OSError)as error:p.exit(2,str(error)+'\n')
    print('Actual default entry and forward native journal frozen; output and activation remain unproved')


if __name__=='__main__':main()
