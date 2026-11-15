#!/usr/bin/env python3
"""Export historical input/model/checkpoint fields before composed ExecuteSync.

Standard library only. No new predictor, ROM or CPU. This export does not replace
raw/source authentication or prove its own chronology. Send whole-RAM boundary
identity is derived across a reviewed value-only model and readonly POP.
"""
from pathlib import Path
import argparse,gzip,hashlib,json,re,struct

TOP,FILE,ARC=0x23BEEC0,0x23BEDD0,0x21E3654
sha=lambda b:hashlib.sha256(b).hexdigest()
wire=lambda x:json.dumps(x,sort_keys=True,separators=(',',':'))


def need(value,message):
    if not value:raise ValueError(message)


def u32s(r):return type(r)is list and len(r)==16 and all(type(x)is int and 0<=x<2**32 for x in r)


def read_report(path):
    need(path.stat().st_size<=16*1024**2,'bounded historical file16MiB')
    with(gzip.open(path,'rb')if path.suffix=='.gz'else path.open('rb'))as stream:data=stream.read(16*1024**2+1)
    need(len(data)<=16*1024**2,'bounded historical decoded16MiB');return json.loads(data)


def send_boundary(row):
    need(row['observe']is True and type(row['fill'])is int and row['fill']==0xA5 and row['fault']is None and
        type(row['policy']['execute'])is int and row['policy']['execute']==1 and row['policy']['clobber']is False and
        len(row['services'])==1,'earlier normal Send domain')
    s=row['services'][0];entry=s['entry'];need(s['pc']=='0x20d7744'and u32s(entry)and
        entry[0]==FILE and entry[4]==ARC and entry[13]==TOP-304 and entry[14]==0x20D7928,'actual Send ExecuteSync boundary')
    frame=bytes.fromhex(s['frame_before']);arc=bytes.fromhex(s['archive_before']);guard=bytes.fromhex(row['guard_after'])
    need((len(frame),len(arc),len(guard))==(304,92,56)and s['frame_before']==s['frame_after']==row['frame_after']and
        s['archive_before']==s['archive_after']==row['archive_after']and row['guard_before']==row['guard_after'],
        'Send model and final frame/archive/guard are identical')
    need(struct.unpack_from('<I',frame,FILE-(TOP-304)+20)[0]==2,'Send initial error BUSY2, independent of Translate policy')
    positions=[i for i,e in enumerate(row['flow'])if e['pc']=='0x20d7924']
    need(len(positions)==1 and [e['pc']for e in row['flow'][positions[0]+1:]]==['0x20d7928'],
         'exact readonly Send tail after original BL')
    before=list(row['flow'][positions[0]]['regs']);need(u32s(before),'Send actual BL input16');before[14]=0x20D7928
    returned=list(entry);returned[0]=1
    need(wire(before)==wire(entry)and wire(s['returned'])==wire(returned)and
        wire(row['flow'][-1]['regs'])==wire(returned),'Send value-only model registers and original BL delivery')
    expected_reads=[dict(pc='0x20d7928',address=TOP-304+4*i,bytes=4,hex=frame[4*i:4*i+4].hex())for i in range(6)]
    need(wire(row['reads'][-6:])==wire(expected_reads)and not[e for e in row['stores']if int(e['pc'],16)>=0x20D7924],
         'Send original readonly POP reads and no later native stores')
    final=list(returned);saved=struct.unpack_from('<6I',frame);final[3:8]=saved[:5];final[13]+=24
    need(saved[-1]==0x20D80F8 and wire(row['returned'])==wire(final)and row['halt_pc']=='0x20d80f8','Send exact final POP context')
    digest=row['whole_ram_sha256'];need(type(digest)is str and re.fullmatch('[0-9a-f]{64}',digest),'Send observed whole final hash')
    return dict(checkpoint_regs=entry,frame304_sha256=sha(frame),guard56_sha256=sha(guard),archive92_sha256=sha(arc),
        derived_boundary_whole_ram_sha256=digest,whole_sha_is_readonly_transfer=True,whole_sha_captured_at_boundary=False)


def complete(r,schema):
    need(r['schema']==schema and r['cpu_executed']is True and r['compiler_invoked']is False and r['probe_only']is False,
         'complete earlier campaign, not probe')


def flat(r,plus,seed,label):
    matches=[c['result']for c in r['cases']if c['label']==label and
        c['result']['fixture']['plus']==plus and c['result']['fixture']['seed']==seed]
    need(len(matches)==1,'unique earlier flat policy/member');return matches[0]


def grouped(r,identity):
    language,plus,seed,value=identity
    fixtures=[f for f in r['fixtures']if(f['language'],f['plus'],f['seed'],f['translated_result'])==identity]
    need(len(fixtures)==1,'unique earlier four-label origin');f=fixtures[0]
    member=dict(language=language,ordinal=f['ordinal']);groups=[g for g in r['groups']if member in g['members']]
    need(len(groups)==1,'unique earlier member group');g=groups[0]
    rows=[c['result']for c in r['cases']if c['group']==g['ordinal']and c['label']=='normal']
    need(len(rows)==1 and rows[0]['observe']is True,'earlier normal group row')
    if r['schema']=='native-fs-exec-sync-join-isolated-v1':
        need('fill'not in rows[0],'join retains parent bytes, no new fill policy')
    else:
        need(type(rows[0].get('fill'))is int and rows[0]['fill']==0xA5,'earlier explicit baseline fill')
    return f,rows[0]


def checkpoint(pc,regs,frame,archive):
    raw=bytes.fromhex(frame);arc=bytes.fromhex(archive)
    need(u32s(regs)and len(raw)in(312,352,416)and len(arc)==92,'typed historical checkpoint/full memory window')
    return dict(pc=hex(pc),regs=regs,frame_bytes=len(raw),frame_sha256=sha(raw),archive92_sha256=sha(arc))


def freeze(paths):
    keys={'send_en','send_it','exec_en','exec_it','composition_report','next_report','join_report'}
    need(set(paths)==keys,'exact historical input families');reports={k:read_report(v)for k,v in paths.items()}
    for language in('en','it'):
        complete(reports['send_'+language],'native-fs-send-isolated-v1');complete(reports['exec_'+language],'native-fs-exec-sync-isolated-v1')
        need(reports['send_'+language]['language']==reports['exec_'+language]['language']==language.upper(),'earlier language binding')
    q,n,j=(reports[k]for k in('composition_report','next_report','join_report'))
    for r,schema in((q,'native-release-wakeup-composed-v1'),(n,'native-fs-next-isolated-v1'),(j,'native-fs-exec-sync-join-isolated-v1')):complete(r,schema)
    need(len(j['fixtures'])==16,'sixteen earlier output origins');cells=[];seen=set()
    for f in j['fixtures']:
        need(f['language']in('EN','IT')and all(type(f[k])is int for k in('ordinal','plus','seed','translated_result'))and
            f['translated_result']in(0,1),'typed earlier origin and model policy')
        identity=(f['language'],f['plus'],f['seed'],f['translated_result']);need(identity not in seen,'no duplicate earlier origins');seen.add(identity)
        language=f['language'].lower();value=f['translated_result'];sr=flat(reports['send_'+language],f['plus'],f['seed'],'normal')
        boundary=send_boundary(sr);er=flat(reports['exec_'+language],f['plus'],f['seed'],'normal'if value==0 else'translate_failure')
        need(wire(er['policy'])==wire(dict(result=value,void_value=0,clobber=False,release_error=None)),'earlier default Translate projection policy')
        t=er['services'][0];need(t['pc']=='0x20d68c0'and t['result_r0']==value and len(t['writes'])==1,'earlier single Translate projection')
        projected=list(boundary['checkpoint_regs']);projected[4]=FILE;projected[1]=4;projected[13]-=8;projected[14]=0x20D7754
        need(wire(t['entry'])==wire(projected),'earlier original wrapper reaches Translate input')
        projected[0]=value;need(wire(t['returned'])==wire(projected),'earlier default Translate preserves other regs/CPSR')
        need(wire(t['writes'])==wire([dict(pc='0x20d68c0',address=FILE+20,bytes=4,before='02000000',value=value)]),
             'earlier Translate sole four-byte host write')
        qf,qr=grouped(q,identity);nf,nr=grouped(n,identity);jf,jr=grouped(j,identity)
        qarchive=qr['fixture']['archive_before']
        need(qf['archive_before']==qarchive,'Release source archive agrees across grouped aliases')
        need(qr['halt_pc']=='0x20d7760'and nr['halt_pc']=='0x20d7768'and jr['halt_pc']=='0x20d7928','original earlier return gates')
        need(wire(qr['entry'])==wire(er['services'][1]['entry'])and qr['frame_before'][-624:]==er['services'][1]['frame_before']and
            qarchive==er['services'][1]['archive_before'],'Release input agrees with previous Translate projection')
        need(nf['captured408']==qr['guard_after']+qr['frame_after']and wire(nf['entry'])==wire(qr['returned'])and
            nf['archive_before']==qr['archive_after'],'observed Release/Wakeup to Next handoff')
        need(wire(jr['entry'])==wire(nr['returned'])and jr['frame_before']==jr['frame_after']==nr['frame_after']and
            jr['archive_before']==jr['archive_after']==nr['archive_after'],'observed Next to stored-error join handoff')
        wb=qr['boundaries'][0];need(len(qr['boundaries'])==1 and wb['native']is True,'actual earlier nested Wake boundary')
        phases=dict(translate_entry=checkpoint(0x20D68C0,t['entry'],t['frame_before'],t['archive_before']),
            translate_return=checkpoint(0x20D7754,t['returned'],t['frame_after'],t['archive_after']),
            release_entry=checkpoint(0x20D6864,qr['entry'],qr['frame_before'],qarchive),
            wake_entry=checkpoint(0x20D1ECC,wb['entry'],wb['frame_before'],wb['archive_before']),
            wake_return=checkpoint(0x20D68B4,wb['returned'],wb['frame_after'],wb['archive_after']),
            release_return=checkpoint(0x20D7760,qr['returned'],qr['frame_after'],qr['archive_after']),
            next_entry=checkpoint(0x20D749C,nr['incoming_next'],nr['frame_before'],nr['archive_before']),
            next_return=checkpoint(0x20D7768,nr['returned'],nr['frame_after'],nr['archive_after']),
            final=checkpoint(0x20D7928,jr['returned'],jr['frame_after'],jr['archive_after']))
        cells.append(dict(language=f['language'],ordinal=f['ordinal'],plus=f['plus'],seed=f['seed'],translated_result=value,
            send_ordinal=sr['fixture']['ordinal'],input=boundary,translate_policy=dict(result=value,preserve_other_regs_and_CPSR=True),
            translate_host_write=t['writes'][0],checkpoints=phases,final_guard56_sha256=sha(bytes.fromhex(jr['guard_after']))))
    return dict(schema='native-fs-exec-sync-native-callees-prospective-fields-v1',cells=cells,
        report_sha256={k:sha(p.read_bytes())for k,p in paths.items()},
        source='Historical actual Send inputs, default Translate projection and native Release/Wake/Next/join checkpoints; no new predictor',
        chronology='Export before new composed predictor/guest; sources/body already inspected, not blind',
        limits=['Send boundary whole SHA is a readonly transfer of final RAM, not a distinct capture',
                'Extra112 bytes require parent whole-image reconstruction proof; no future stack bytes pre-applied',
                'One explicit Translate model; model policy belongs to the complete interaction identity',
                'Fields alone do not prove one CPU activation, complete Translate, Send POP, natural completion or hardware'])


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in('send-en','send-it','exec-en','exec-it','composition-report','next-report','join-report','json'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args()
    try:
        source=Path(__file__).resolve().parents[3];need(a.json.resolve()!=source and source not in a.json.resolve().parents,'fresh private output outside source')
        result=freeze({k:v for k,v in vars(a).items()if k!='json'})
        with a.json.open('x')as output:output.write(json.dumps(result,indent=2)+'\n')
    except(ValueError,KeyError,TypeError,OSError)as error:p.exit(2,str(error)+'\n')
    print('Historical inputs/model policy/native checkpoint fields exported; composed guest not proved')


if __name__=='__main__':main()
