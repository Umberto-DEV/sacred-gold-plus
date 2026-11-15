#!/usr/bin/env python3
"""Freeze actual Send final fields and isolated Translate whole-RAM boundaries.

Standard library only: no new oracle, ROM decoder, compiler or CPU. These
checks identify compatible fields; they do not identify their native writer.
"""
from pathlib import Path
import argparse,importlib.util,json

path=Path(__file__).with_name('congela_fs_translate_contract.py')
spec=importlib.util.spec_from_file_location('send_translate_previous_freezer',path)
P=importlib.util.module_from_spec(spec);spec.loader.exec_module(P)
need,sha,wire,read_report=P.need,P.sha,P.wire,P.read_report
need(sha(path.read_bytes())=='d7b3f162ee2272743ced2ae91b2bb0b272ec251b1e17128662ddfb9b61c68a91','Send Translate previous exporter drift')


def group_row(report,fixture,label='normal'):
    member={k:fixture[k]for k in('language','ordinal')}
    groups=[g for g in report['groups']if member in g['members']]
    need(len(groups)==1,'Send Translate single origin group')
    rows=[c['result']for c in report['cases']if c['group']==groups[0]['ordinal']and c['label']==label]
    need(len(rows)==1,'Send Translate single actual row')
    return groups[0],rows[0]


def freeze(send_report,translate_report):
    send,translate=read_report(send_report),read_report(translate_report)
    P.P.F.complete(send,'native-fs-send-native-callees-v1')
    P.P.F.complete(translate,'native-fs-translate-isolated-v1')
    for r in(send,translate):
        need(len(r['fixtures'])==16 and len(r['groups'])==4 and len(r['cases'])==12 and
             len(r['observer_off'])==4,'Send Translate complete actual grids')
    need(translate['proof']['parent_report_sha256']==sha(send_report.read_bytes()),'Send Translate direct report lineage')
    cells=[];seen=set()
    for f in send['fixtures']:
        identity=tuple(f[k]for k in('language','ordinal','plus','seed','translated_result'))
        need(identity not in seen,'Send Translate unique actual origin');seen.add(identity)
        matches=[x for x in translate['fixtures']if(x['language'],x['ordinal'])==identity[:2]]
        need(len(matches)==1,'Send Translate exact origin join');tf=matches[0]
        need(wire(tf['parent_send_fixture'])==wire(f)and tf['default_result']==f['translated_result'],
             'Send Translate literal input/default policy join')
        sg,s=group_row(send,f);tg,t=group_row(translate,tf)
        P.prefix_state(s)
        need(t['observe']is True and t['fault']is None and t['policy']=={'early_error':False}and
             len(t['services'])==1 and t['model_stores']==[]and t['steps']==41 and
             len(t['flow'])==39 and len(t['stores'])==9 and len(t['reads'])==14,
             'Send Translate isolated actual value-only default policy')
        need(t['entry']==s['services'][0]['entry']and t['frame_before']==s['services'][0]['frame_before']and
             t['archive_before']==s['services'][0]['archive_before'],'Send Translate actual entry boundary fields')
        need(len(s['returned'])==16 and len(bytes.fromhex(s['frame_after']))==416 and
             len(bytes.fromhex(s['archive_after']))==92,'Send Translate complete final fields')
        cells.append(dict(language=f['language'],ordinal=f['ordinal'],plus=f['plus'],seed=f['seed'],
            translated_result=f['translated_result'],send_group=sg['ordinal'],translate_group=tg['ordinal'],
            entry=f['entry'],parent_fixture_sha256=sha(wire(f).encode()),
            parent_before_whole_ram_sha256=s['before_whole_ram_sha256'],
            expected_final=dict(returned=s['returned'],frame416_sha256=sha(bytes.fromhex(s['frame_after'])),
                archive92_sha256=sha(bytes.fromhex(s['archive_after'])),stop=s['stop'],
                guard56_sha256=sha(bytes.fromhex(s['guard_after']))),
            translate=dict(entry=t['entry'],returned=t['returned'],
                actual_before_whole_ram_sha256=t['before_whole_ram_sha256'],actual_after_whole_ram_sha256=t['whole_ram_sha256'],
                entry_frame416_sha256=sha(bytes.fromhex(t['frame_before'])),entry_archive92_sha256=sha(bytes.fromhex(t['archive_before'])),
                return_frame416_sha256=sha(bytes.fromhex(t['frame_after'])),return_archive92_sha256=sha(bytes.fromhex(t['archive_after'])))))
    return dict(schema='native-fs-send-translate-prospective-fields-v1',cells=cells,
        send_report_sha256=sha(send_report.read_bytes()),translate_report_sha256=sha(translate_report.read_bytes()),
        chronology='Before new combined oracle/collector/guest; known source and previous raw, not blind',
        comparison='All16 final registers/frame416/archive92; actual isolated whole boundary hashes, no masks',
        limits=['Final fields and boundary hashes can accept early_error; native store preimage identifies writer separately',
                'Whole hashes at Translate entry/return are actual isolated observations; combined boundary equality must be tested',
                'Declared default FSResult model remains; no natural filesystem/IRQ delivery/hardware claim'])


def compare(cell,fixture,row):
    for key in('language','ordinal','plus','seed','translated_result'):
        need(type(cell[key])is type(fixture[key])and cell[key]==fixture[key],'Send Translate frozen origin/policy')
    need(cell['parent_fixture_sha256']==sha(wire(fixture).encode())and wire(row['entry'])==wire(cell['entry']),
         'Send Translate frozen literal initial fixture')
    final=cell['expected_final']
    need(wire(row['returned'])==wire(final['returned'])and row['halt_pc']==final['stop'],
         'Send Translate frozen all16 final registers/stop')
    for field,key in(('frame_after','frame416_sha256'),('archive_after','archive92_sha256'),('guard_after','guard56_sha256')):
        need(sha(bytes.fromhex(row[field]))==final[key],'Send Translate frozen complete '+field)
    need(sha(bytes.fromhex(row['guard_before']))==final['guard56_sha256'],'Send Translate frozen original guard')
    child=cell['translate']
    for phase,prefix,registers,digest in(('translate_entry','entry',child['entry'],child['actual_before_whole_ram_sha256']),
                                        ('translate_return','return',child['returned'],child['actual_after_whole_ram_sha256'])):
        cp=row['checkpoints'][phase]
        pc='0x20d68c0'if phase=='translate_entry'else'0x20d7754'
        need(cp['pc']==pc and wire(cp['regs'])==wire(registers)and cp['whole_ram_sha256']==digest and
             sha(bytes.fromhex(cp['frame']))==child[prefix+'_frame416_sha256']and
             sha(bytes.fromhex(cp['archive']))==child[prefix+'_archive92_sha256'],
             'Send Translate frozen actual whole boundary '+phase)
    return dict(passed=True,final_registers=16,frame_bytes=416,archive_bytes=92,actual_whole_boundaries=2,
                writer_or_activation_proved_here=False,fields_can_accept_early_error=True)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in('send-report','translate-report','json'):p.add_argument('--'+key,type=Path,required=True)
    a=p.parse_args()
    try:
        source=Path(__file__).resolve().parents[3]
        need(source not in a.json.resolve().parents and source!=a.json.resolve(),'Send Translate private frozen output')
        result=freeze(a.send_report,a.translate_report)
        with a.json.open('x')as output:output.write(json.dumps(result,indent=2)+'\n')
    except(ValueError,KeyError,TypeError,OSError)as error:p.exit(2,str(error)+'\n')
    print('Actual final16/frame416/archive92 and Translate whole boundaries frozen; no new guest')


if __name__=='__main__':main()
