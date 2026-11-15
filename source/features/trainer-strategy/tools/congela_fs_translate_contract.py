#!/usr/bin/env python3
"""Freeze actual Translate entry and explicitly limited earlier model fields.

No new oracle, compiler, ROM decoding or CPU. Native R1/LR and saved24 are not
old-model invariants. Final-field agreement alone cannot identify their writer.
"""
from pathlib import Path
import argparse,importlib.util,json,struct

path=Path(__file__).with_name('congela_fs_send_native_contract.py')
spec=importlib.util.spec_from_file_location('translate_previous_freezer',path)
P=importlib.util.module_from_spec(spec);spec.loader.exec_module(P)
need,sha,wire,read_report=P.need,P.sha,P.wire,P.read_report
need(sha(path.read_bytes())=='9fc0aa6de882262a9ae7d01803554f66f8cbe2fd558ad99625c53cc289ae4233','Translate qualified parent exporter drift')
TOP,FILE,ARC,FRAME=P.TOP,P.FILE,P.ARC,P.TOP-416
COMPONENTS={
 'code':(0x20D68C0,396,'9c42ca76b2fa192199ad1687f07ea9bcf54a90f5b6fe950c6fd9cbb641fb719d'),
 'code_and_pool':(0x20D68C0,400,'f1df0f035e516cdfff9df4668530ca636f88b9a1a70d86804b9671c8bce7341a'),
 'table':(0x210E124,36,'a2a3fe2a981c9967141752f3228d54c59d73c639339443bbe0ef04f13319d287'),
 'default_gate':(0x20D6DB0,4,'462b796a6c11d4277cd269fd03b7c46c2e0de0394c8071aa4a7a8d079be7bb87')}


def stable_frame(frame):
    raw=bytes.fromhex(frame);need(len(raw)==416,'Translate exact earlier frame416')
    return[dict(offset=a,bytes=b-a,sha256=sha(raw[a:b]))for a,b in((0,80),(104,416))]


def stable_registers(regs):
    need(P.F.u32s(regs)and regs[0]in(0,1),'Translate typed earlier FSResult/full16')
    return{str(i):v for i,v in enumerate(regs)if i not in(1,14)}


def prefix_state(row):
    need(row['observe']is True and row['fault']is None and wire(row['policy'])==wire(dict(bypass_wakeup=False))and
         len(row['services'])==1,'Translate earlier normal Send domain')
    service=row['services'][0];value=row['fixture']['translated_result']
    need(type(value)is int and value in(0,1)and service['pc']=='0x20d68c0'and service['result_r0']==value and
         wire(row['model_stores'])==wire([dict(pc='0x20d68c0',address=FILE+20,bytes=4,before='02000000',value=value)]),
         'Translate earlier explicit model policy and sole old host write')
    positions=[i for i,e in enumerate(row['flow'])if e['pc']=='0x20d7754']
    need(len(positions)==1,'Translate single first native return after old model');prefix=row['flow'][:positions[0]]
    need(len(prefix)==93 and prefix[-1]['pc']=='0x20d7750','Translate exact native prefix before model')
    delivered=list(prefix[-1]['regs']);need(P.F.u32s(delivered),'Translate actual native BL context');delivered[14]=0x20D7754
    checkpoint=row['checkpoints']['translate_entry']
    need(wire(checkpoint['regs'])==wire(service['entry'])==wire(delivered)and delivered[0:2]==[FILE,4]and
         delivered[13:15]==[TOP-312,0x20D7754]and delivered[15]==0x2000001F,'Translate actual full16 BL delivery')
    frame=bytearray.fromhex(row['frame_before']);arc=bytearray.fromhex(row['archive_before'])
    need((len(frame),len(arc))==(416,92),'Translate complete initial owner windows')
    stores=row['stores'][:17]
    need(len(row['stores'])>17 and row['stores'][17]['pc']=='0x20d6864'and
         len(stores)==17 and all(w['bytes']==4 and w['pc']in{e['pc']for e in prefix}for w in stores),
         'Translate seventeen actual prefix stores precede Release')
    for w in stores:
        address=w['address']
        if FRAME<=address and address+4<=TOP:memory,i=frame,address-FRAME
        else:
            need(ARC<=address and address+4<=ARC+92,'Translate prefix word owner');memory,i=arc,address-ARC
        need(memory[i:i+4].hex()==w['before'],'Translate prefix native store preimage');struct.pack_into('<I',memory,i,w['value'])
    need(frame.hex()==service['frame_before']==checkpoint['frame']and arc.hex()==service['archive_before']==checkpoint['archive'],
         'Translate forward prefix produces actual model entry memory')
    need(row['guard_before']==row['guard_after']=='a5'*56 and struct.unpack_from('<I',frame,FILE-FRAME+20)[0]==2 and
         struct.unpack_from('<I',frame,FILE-FRAME+12)[0]==0x45 and struct.unpack_from('<I',arc,28)[0]==0x13 and
         struct.unpack_from('<I',arc,88)[0]==0,'Translate finite SYNC/busy/proc_flag0 and guard')
    return dict(entry=delivered,frame416_sha256=sha(frame),archive92_sha256=sha(arc),guard56_sha256=sha(bytes.fromhex(row['guard_before'])),
        observed_before_Send_whole_sha256=row['before_whole_ram_sha256'],prefix_native_contexts=93,prefix_native_stores=17,
        prefix_stores_sha256=sha(wire(stores).encode()),boundary_whole_sha_observed=False,
        required_whole_provenance='Reconstruct observed-before Send image, replay17 native writes, then overlay qualified new components')


def component_fields(receipt):
    need(receipt['case']=='P76'and receipt['new_CPU_executed']is False and receipt['new_compiler_invoked']is False and
         set(receipt['roms'])=={'EN','IT'},'Translate offline component receipt, not an execution')
    previous=None
    for language,item in receipt['roms'].items():
        regions=item['regions'];need(set(regions)==set(COMPONENTS),'Translate exact code/pool/table/gate regions')
        for name,(address,n,digest)in COMPONENTS.items():
            c=regions[name];need(c['ram']==hex(address)and c['bytes']==n and c['sha256']==digest and
                len(bytes.fromhex(c['local_hex']))==n and sha(bytes.fromhex(c['local_hex']))==digest,'Translate pinned component bytes')
        need(previous is None or wire(regions)==wire(previous),'Translate two-language component equality');previous=regions
        need(item['default_slot4']==dict(ram='0x210e134',target='0x20d6db0'),'Translate default slot and real handler')
    return{name:dict(ram=hex(a),bytes=n,sha256=d)for name,(a,n,d)in COMPONENTS.items()}


def freeze(parent_report,component_receipt):
    report=read_report(parent_report);receipt=read_report(component_receipt);components=component_fields(receipt)
    P.F.complete(report,'native-fs-send-native-callees-v1');n=len(report['groups'])
    need(len(report['fixtures'])==16 and len(report['cases'])==3*n and len(report['field_holdout'])==32 and
         len(report['observer_off'])==n and len(report['counters'])==16,'Translate complete earlier Send grid')
    cells=[];seen=set()
    for f in report['fixtures']:
        need(f['language']in('EN','IT')and all(type(f[k])is int for k in('ordinal','plus','seed','translated_result'))and
             f['translated_result']in(0,1),'Translate typed historical origin')
        identity=tuple(f[k]for k in('language','plus','seed','translated_result'));need(identity not in seen,'Translate unique historical origin');seen.add(identity)
        member=dict(language=f['language'],ordinal=f['ordinal']);gs=[g for g in report['groups']if member in g['members']]
        need(len(gs)==1,'Translate unique old group');g=gs[0]
        rows=[c['result']for c in report['cases']if c['group']==g['ordinal']and c['label']=='normal'];need(len(rows)==1,'Translate unique normal row')
        row=rows[0];inp=prefix_state(row);s=row['services'][0]
        need(type(row['fixture']['translated_result'])is int and row['fixture']['translated_result']==f['translated_result'],
             'Translate old model policy belongs to group identity')
        old_return=list(s['entry']);old_return[0]=f['translated_result']
        old_frame=bytearray.fromhex(s['frame_before']);struct.pack_into('<I',old_frame,FILE-FRAME+20,f['translated_result'])
        need(wire(s['returned'])==wire(old_return)and s['frame_after']==old_frame.hex()and s['archive_after']==s['archive_before'],
             'Translate earlier model changed only error4/R0')
        cells.append(dict(language=f['language'],ordinal=f['ordinal'],plus=f['plus'],seed=f['seed'],default_result=f['translated_result'],
            parent_group=g['ordinal'],input=inp,earlier_model_returned=s['returned'],expected_stable_registers=stable_registers(s['returned']),
            excluded_native_volatile_indices=[1,14],excluded_native_stack=dict(offset=80,bytes=24,reason='New native PUSH24, checked separately by source oracle'),
            expected_stable_frame_spans=stable_frame(s['frame_after']),expected_final_archive92_sha256=sha(bytes.fromhex(s['archive_after'])),
            expected_return_pc='0x20d7754',expected_FSResult=f['translated_result'],default_model=dict(target='0x20d6db0',RAM_writes=0,
                preserve_other_registers_and_CPSR=True,return_to_actual_LR=True),earlier_model_host_write=s['writes'][0]))
    return dict(schema='native-fs-translate-prospective-fields-v1',cells=cells,components=components,
        parent_report_sha256=sha(parent_report.read_bytes()),component_receipt_sha256=sha(component_receipt.read_bytes()),
        chronology='Before new Translate compiler/oracle/guest; inputs and body already inspected, not blind',
        comparison='Earlier-model stable fields only; native R1/LR and saved24 are explicit differences, not an ABI equivalence claim',
        limits=['Boundary whole identity must be forward-derived from observed-before image plus17 native stores; not a distinct whole capture',
            'Final field agreement may accept early_error; native error-store preimage and host ledger identify the writer separately',
            'Offline receipt does not replace independent ROM/ELF/source authentication; default handler remains a declared model'])


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in('parent-report','component-receipt','json'):parser.add_argument('--'+name,type=Path,required=True)
    a=parser.parse_args()
    try:
        source=Path(__file__).resolve().parents[3];need(a.json.resolve()!=source and source not in a.json.resolve().parents,'Translate private output outside source')
        result=freeze(a.parent_report,a.component_receipt)
        with a.json.open('x')as output:output.write(json.dumps(result,indent=2)+'\n')
    except(ValueError,KeyError,TypeError,OSError)as error:parser.exit(2,str(error)+'\n')
    print('Actual Translate entry and earlier stable fields frozen; native writer and activation not proved')


if __name__=='__main__':main()
