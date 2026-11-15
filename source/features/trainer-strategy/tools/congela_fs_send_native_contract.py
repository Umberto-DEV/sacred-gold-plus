#!/usr/bin/env python3
"""Freeze actual earlier checkpoints and a labeled readonly Send POP projection.

Standard library only; no new predictor, ROM, image builder or CPU. The final
80F8 context is derived from the observed 7928 context and saved words. It is
not an already observed complete Send/native-callees execution.
"""
from pathlib import Path
import argparse,importlib.util,json,re,struct


path=Path(__file__).with_name('congela_fs_exec_sync_native_contract.py')
spec=importlib.util.spec_from_file_location('send_native_qualified_export',path)
F=importlib.util.module_from_spec(spec);spec.loader.exec_module(F)
sha,wire,need,read_report=F.sha,F.wire,F.need,F.read_report
need(sha(path.read_bytes())=='3b3882987508602966e89008d2538ceedd9bee39e9f35be01ae99875ac74e7e5','Send native qualified freezer drift')
TOP,FILE,ARC,ID,PATH=F.TOP,F.FILE,F.ARC,0x23BEE28,0x210F198
PHASE_PCS=dict(translate_entry=0x20D68C0,translate_return=0x20D7754,release_entry=0x20D6864,
    wake_entry=0x20D1ECC,wake_return=0x20D68B4,release_return=0x20D7760,next_entry=0x20D749C,
    next_return=0x20D7768,final=0x20D7928)


def project_send_pop(regs,frame,reads):
    need(F.u32s(regs)and regs[4]==ARC and regs[13]==TOP-304,'Send original POP full native input')
    raw=bytes.fromhex(frame);need(len(raw)==416,'Send full earlier frame416')
    saved=struct.unpack_from('<6I',raw,112)
    need(saved==(FILE+48,1,0,ID,PATH,0x20D80F8),'Send original saved words and Find return')
    expected=[dict(pc='0x20d7928',address=TOP-304+4*i,bytes=4,hex=raw[112+4*i:116+4*i].hex())for i in range(6)]
    need(wire(reads)==wire(expected),'Send exact earlier POP reads')
    out=list(regs);out[3:8]=saved[:5];out[13]+=24
    return out


def send_input(row):
    f=row['fixture'];boundary=F.send_boundary(row)
    need(F.u32s(f['entry'])and wire(row['entry'])==wire(f['entry'])==wire(row['flow'][0]['regs'])and
         row['flow'][0]['pc']=='0x20d7788'and f['entry'][13]==TOP-280,'Send actual entry before PUSH')
    need(type(f['frame'])is type(f['archive_before'])is str,'Send exact preimage strings')
    frame=bytes.fromhex(f['frame']);arc=bytes.fromhex(f['archive_before']);guard=bytes.fromhex(row['guard_before'])
    need(len(frame)==304 and len(arc)==92 and guard==b'\xa5'*56,'Send earlier frame304/archive92/guard56')
    for offset,value in((0,0),(4,0),(8,ARC),(12,0),(16,14),(20,0),(24,0),(28,0),
                         (48,ARC),(52,0),(56,0),(60,PATH),(64,0),(68,ID)):
        need(struct.unpack_from('<I',frame,FILE-(TOP-304)+offset)[0]==value,'Send exact earlier initial file fields')
    need(arc==bytes(28)+struct.pack('<I',3)+bytes(60),'Send actual initial idle archive')
    digest=row['before_whole_ram_sha256']
    need(type(digest)is str and re.fullmatch('[0-9a-f]{64}',digest),'Send actual BEFORE whole digest')
    return dict(checkpoint_regs=f['entry'],frame304_sha256=sha(frame),archive92_sha256=sha(arc),guard56_sha256=sha(guard),
        before_whole_ram_sha256=digest,whole_sha_captured_at_Send_entry=True,whole_sha_is_readonly_transfer=False),boundary


def checkpoint(pc,regs,frame,archive):
    need(F.u32s(regs)and len(bytes.fromhex(frame))==416 and len(bytes.fromhex(archive))==92,'Send checkpoint full16/frame416/archive92')
    return dict(pc=hex(pc),regs=regs,frame416_sha256=sha(bytes.fromhex(frame)),archive92_sha256=sha(bytes.fromhex(archive)))


def historical_checkpoints(phases):
    need(set(phases)==set(PHASE_PCS),'Send exact historical phase keyset')
    result={}
    for name,c in phases.items():
        need(c['pc']==hex(PHASE_PCS[name]),'Send exact historical phase PC')
        result['send_pop'if name=='final'else name]=checkpoint(PHASE_PCS[name],c['regs'],c['frame'],c['archive'])
    return result


def freeze(paths):
    need(set(paths)=={'send_en','send_it','native_report'},'Send exact historical report families')
    reports={k:read_report(p)for k,p in paths.items()};r=reports['native_report']
    F.complete(r,'native-fs-exec-sync-native-callees-v1')
    need(len(r['fixtures'])==16 and len(r['cases'])==3*len(r['groups'])and
         len(r['field_holdout'])==32 and len(r['observer_off'])==len(r['groups'])and len(r['counters'])==16,
         'Send complete earlier native normal/OFF/counter grid')
    for language in('en','it'):
        sr=reports['send_'+language];F.complete(sr,'native-fs-send-isolated-v1')
        need(sr['language']==language.upper(),'Send earlier report language')
        need(sha(paths['send_'+language].read_bytes())==r['proof']['historical_reports']['send_'+language]['sha256'],
             'Send report identity bound by native parent')
    cells=[];seen=set()
    for f in r['fixtures']:
        need(f['language']in('EN','IT')and all(type(f[k])is int for k in('ordinal','plus','seed','translated_result'))and
             f['translated_result']in(0,1),'Send typed native provenance origin')
        identity=tuple(f[k]for k in('language','plus','seed','translated_result'))
        need(identity not in seen,'Send unique provenance origin');seen.add(identity)
        sr=F.flat(reports['send_'+f['language'].lower()],f['plus'],f['seed'],'normal');inp,boundary=send_input(sr)
        need(wire(sr['fixture'])==wire(f['send_fixture'])and wire(f['entry'])==wire(boundary['checkpoint_regs'])and
             sha(bytes.fromhex(f['captured304']))==boundary['frame304_sha256']and
             sha(bytes.fromhex(f['archive_before']))==boundary['archive92_sha256']and
             f['parent_whole_ram_sha256']==boundary['derived_boundary_whole_ram_sha256'],'Send actual source-to-native boundary linkage')
        member=dict(language=f['language'],ordinal=f['ordinal'])
        groups=[g for g in r['groups']if member in g['members']];need(len(groups)==1,'Send unique native member group');g=groups[0]
        rows=[c['result']for c in r['cases']if c['group']==g['ordinal']and c['label']=='normal'];need(len(rows)==1,'Send unique native normal')
        n=rows[0];need(n['observe']is True and n['fault']is None and wire(n['policy'])==wire(dict(bypass_wakeup=False))and
             len(n['services'])==1 and len(n['model_stores'])==1 and n['halt_pc']=='0x20d7928','Send earlier single-model native domain')
        need(wire(n['entry'])==wire(f['entry'])and bytes.fromhex(n['frame_before'])[-304:]==bytes.fromhex(f['captured304'])and
             n['archive_before']==f['archive_before'],'Send native actual entry and memory windows')
        need(type(n['fixture']['translated_result'])is int and n['fixture']['translated_result']==f['translated_result']and
             wire(n['model_stores'])==wire([dict(pc='0x20d68c0',address=FILE+20,bytes=4,before='02000000',value=f['translated_result'])]),
             'Send native actual Translate policy and sole host write')
        phases={'exec_entry':checkpoint(0x20D7744,n['entry'],n['frame_before'],n['archive_before'])}
        phases.update(historical_checkpoints(n['checkpoints']))
        need(wire(phases['send_pop']['regs'])==wire(n['returned'])and n['halt_regs']==n['returned']and
             phases['send_pop']['frame416_sha256']==sha(bytes.fromhex(n['frame_after']))and
             phases['send_pop']['archive92_sha256']==sha(bytes.fromhex(n['archive_after'])),'Send actual final native context')
        projected=project_send_pop(n['returned'],n['frame_after'],sr['reads'][-6:])
        phases['final']=checkpoint(0x20D80F8,projected,n['frame_after'],n['archive_after'])
        phases['final']['derived_from_readonly_POP']=True
        phases['final']['observed_in_new_composition']=False
        cells.append(dict(language=f['language'],ordinal=f['ordinal'],plus=f['plus'],seed=f['seed'],translated_result=f['translated_result'],
            send_ordinal=sr['fixture']['ordinal'],input=inp,checkpoints=phases,translate_host_write=n['model_stores'][0],
            final_guard56_sha256=sha(bytes.fromhex(n['guard_after']))))
    return dict(schema='native-fs-send-native-callees-prospective-fields-v1',cells=cells,
        report_sha256={k:sha(p.read_bytes())for k,p in paths.items()},
        source='Actual Send entry/before digest and native ExecuteSync checkpoints; final context derived solely by readonly POP',
        chronology='Export before new Send composition predictor/guest; known inputs/bodies, not blind',
        limits=['The projected final context is not a previously observed full Send/native-callees run',
                'Initial frame304 has ancestral captured/filled provenance; extra112 bytes still require exact whole-image proof',
                'One explicit Translate projection remains; natural filesystem/card/thread and hardware not established'])


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in('send-en','send-it','native-report','json'):parser.add_argument('--'+name,type=Path,required=True)
    a=parser.parse_args()
    try:
        source=Path(__file__).resolve().parents[3]
        need(a.json.resolve()!=source and source not in a.json.resolve().parents,'Send fresh private output outside source')
        result=freeze({k:v for k,v in vars(a).items()if k!='json'})
        with a.json.open('x')as output:output.write(json.dumps(result,indent=2)+'\n')
    except(ValueError,KeyError,TypeError,OSError)as error:parser.exit(2,str(error)+'\n')
    print('Historical fields and labeled POP projection frozen; new one-context Send not yet observed')


if __name__=='__main__':main()
