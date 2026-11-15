#!/usr/bin/env python3
"""Compare frozen ExecuteSync Release projections with later isolated native records.

Stdlib only, read-only. No project oracle is imported. This compares retained
receipt contracts; independent ROM/ELF readback and native trace qualification
remain prerequisites. Whole-RAM or complete-caller equivalence is not claimed.
"""
from pathlib import Path
import argparse,copy,gzip,hashlib,io,json,re,struct

FILE,ARC,TOP=0x23BEDD0,0x21E3654,0x23BEEC0
SP,FRAME,RETURN=TOP-312,TOP-328,0x20D7760
FIELD_PCS=(0x20D6884,0x20D6894,0x20D6898,0x20D68A8,0x20D68AC)
FIELD_ADDRESSES=(ARC+36,FILE,FILE+4,FILE+12,FILE+20)
wire=lambda x:json.dumps(x,sort_keys=True,separators=(',',':'))
sha=lambda b:hashlib.sha256(b).hexdigest()


def need(value,message):
    if not value:raise ValueError(message)


def blob(text,n,label):
    need(type(text)is str and len(text)==2*n and re.fullmatch('[0-9a-fA-F]*',text)is not None,'invalid '+label+' byte preimage')
    return bytes.fromhex(text)


def registers(value):
    need(type(value)is list and len(value)==16 and all(type(x)is int and 0<=x<=0xFFFFFFFF for x in value),'unsigned32 full16 register vector required')
    return value


def read_report(path,maximum=32*1024**2):
    need(path.stat().st_size<=8*1024**2,'stored report exceeds8MiB')
    raw=path.read_bytes()
    try:
        if raw[:2]==b'\x1f\x8b':
            with gzip.GzipFile(fileobj=io.BytesIO(raw))as fd:data=fd.read(maximum+1)
        else:data=raw
        need(len(data)<=maximum,'expanded report exceeds bound');result=json.loads(data)
    except(OSError,UnicodeError,ValueError)as error:raise ValueError('invalid or oversized report')from error
    need(type(result)is dict,'report must be a JSON object');return result,sha(raw)


def event_fields(event):
    need(type(event['address'])is type(event['bytes'])is type(event['value'])is int and event['bytes']==4 and
         0<=event['value']<=0xFFFFFFFF,'typed native/model word event required')
    blob(event['before'],4,'word');return {k:event[k]for k in('address','bytes','before','value')}


def compare_pair(model,native,preceding_guard):
    """Expected bytes/events come only from the earlier model's captured service."""
    m,n=model,native;entry=registers(m['entry']);registers(n['entry']);old_return=registers(m['returned']);new_return=registers(n['returned'])
    need(m['pc']=='0x20d6864'and entry==n['entry']and entry[0]==FILE and type(entry[1])is int and entry[1]in(0,1)and
         entry[13:16]==[SP,RETURN,0x2000001F],'same finite actual Release input ABI required')
    before=blob(m['frame_before'],312,'model frame');after=blob(m['frame_after'],312,'model frame')
    new_before=blob(n['frame_before'],328,'native frame');new_after=blob(n['frame_after'],328,'native frame')
    archive_before=blob(m['archive_before'],92,'model archive');archive_after=blob(m['archive_after'],92,'model archive')
    need(type(preceding_guard)is bytes and len(preceding_guard)==56,'captured preceding guard56 required')
    need(new_before[:16]==preceding_guard[-16:]and new_before[16:]==before,'same captured parent frame before native call required')
    need(new_after[16:]==after,'captured parent frame contract differs')
    f=n['fixture'];need(wire(f['entry'])==wire(entry)and f['frame']==n['frame_before']and
         blob(f['archive_before'],92,'native archive')==archive_before and wire(f['translated_result'])==wire(entry[1]),'native fixture must retain the captured model preimage')
    need(blob(n['archive_after'],92,'native archive')==archive_after,'captured archive contract differs')
    need(new_after[:16]==struct.pack('<4I',*(entry[i]for i in(4,5,6,14))),'new native stack16 must contain the actual saved words')
    need(n['observe']is True and n['fault']is None and wire(n['steps'])==wire(36)and wire(n['native_peak'])==wire(16)and
         len(n['stores'])==9 and len(n['reads'])==7 and len(n['flow'])==34,'complete selected native observation required')
    for j,index in enumerate((4,5,6,14)):
        event=n['stores'][j];expected=dict(address=FRAME+4*j,bytes=4,before=new_before[4*j:4*j+4].hex(),value=entry[index])
        need(event['pc']=='0x20d6864'and wire(event_fields(event))==wire(expected),'new native PUSH transcript differs')
    need(len(m['writes'])==5,'five frozen field projections required')
    for pc,address,old,new in zip(FIELD_PCS,FIELD_ADDRESSES,m['writes'],n['stores'][4:]):
        need(old['pc']=='0x20d6864'and new['pc']==hex(pc)and type(old['address'])is int and old['address']==address and
             wire(event_fields(old))==wire(event_fields(new)),'frozen/native field-store contract differs')
    witness=[e for e in n['flow']if e['pc']=='0x20d68ac'];need(len(witness)==1,'actual native error-store instruction witness required')
    r=registers(witness[0]['regs']);need(r[4:6]==[entry[1],FILE],'native STR error must consume actual R1-derived R4 and FILE R5')
    need(len(n['services'])==1,'one empty-Wakeup boundary required');service=n['services'][0]
    need(service['pc']=='0x20d1ecc'and type(service['writes'])is list and service['writes']==[]and
         blob(service['frame_before'],328,'Wakeup frame')==blob(service['frame_after'],328,'Wakeup frame')==new_after and
         blob(service['archive_before'],92,'Wakeup archive')==blob(service['archive_after'],92,'Wakeup archive')==archive_after,
         'Wakeup must retain the actual full native frame/archive with zero model writes')
    need(new_return[4:12]==entry[4:12]and new_return[13]==entry[13]and old_return[4:12]==entry[4:12]and old_return[13]==entry[13],
         'callee-saved registers and SP must be preserved')
    need(new_return[0]==0x80 and new_return[14]==0x20D68BC and new_return[15]&0x0FFFFFFF==entry[15]&0x0FFFFFFF and
         n['stop']==n['halt_pc']==hex(RETURN)and wire(n['halt_regs'])==wire(new_return),'native void return/control-state contract differs')
    need(blob(n['guard_before'],56,'native guard')==blob(n['guard_after'],56,'native guard'),'isolated lower guard must be unchanged')
    names=['R'+str(i)for i in range(13)]+['SP','LR','CPSR']
    delta=[dict(register=names[i],model=old_return[i],native=new_return[i])for i in range(16)if old_return[i]!=new_return[i]]
    return dict(matched_parent_frame_bytes=312,matched_archive_bytes=92,matched_field_stores=5,new_native_stack_bytes=16,
        frame_sha256=sha(after),archive_sha256=sha(archive_after),abi_differences=delta,
        full_register_equivalence_claimed=False,whole_ram_equivalence_claimed=False)


OLD_POLICIES=[('normal',{}),('off',dict(observe=False)),('translate_failure',dict(result=1)),('release_error_fault',dict(release_error=1)),
    ('void_ones',dict(void_value=0xFFFFFFFF)),('void_file',dict(void_value=FILE)),('clobber',dict(clobber=True)),('fill39',dict(fill=0x39))]
NEW_POLICIES=[('normal',{}),('off',dict(observe=False)),('stale_error2',dict(stale_error=True)),('void_ones',dict(wake_value=0xFFFFFFFF)),
    ('clobber',dict(clobber=True)),('fill39',dict(fill=0x39))]


def grid(report,fixtures,policies,baseline):
    need(type(report['cases'])is list and len(report['cases'])==len(fixtures)*len(policies),'complete distinct matrix grid required')
    for ordinal,f in enumerate(fixtures):
        need(type(f['ordinal'])is int and f['ordinal']==ordinal,'ordered distinct fixture ordinals required')
        for i,(label,options)in enumerate(policies):
            c=report['cases'][ordinal*len(policies)+i];r=c['result'];policy={**baseline,**{k:v for k,v in options.items()if k in baseline}}
            need(c['label']==label and wire(r['fixture'])==wire(f)and
                 wire((r['policy'],r['observe'],r['fill']))==wire((policy,options.get('observe',True),options.get('fill',0xA5))),
                 'matrix labels/policies/typed fixture grid differ')


def require_fault_contract(normal,fault):
    """The negative must differ for the declared stored-error reason only."""
    need(normal['pc']=='0x20d6864'and registers(normal['entry'])[1]==0 and len(normal['writes'])==5,
         'normal frozen Release contract required for the negative control')
    frame=bytearray(blob(normal['frame_after'],312,'normal frozen frame'))
    need(frame[92:96]==bytes(4)and event_fields(normal['writes'][-1])['value']==0,
         'normal frozen error must be success0')
    expected=copy.deepcopy(normal);struct.pack_into('<I',frame,92,1);expected['frame_after']=frame.hex();expected['writes'][-1]['value']=1
    need(wire(fault)==wire(expected),'fault must be exactly the declared error-only frozen contract')
    return True


def compare_reports(old,new,old_digest,new_digest):
    need(old['schema']=='native-fs-exec-sync-isolated-v1'and new['schema']=='native-fs-release-isolated-v1'and
         old['language']==new['language']and old['language']in('EN','IT')and
         old['cpu_executed']is new['cpu_executed']is True and old['probe_only']is new['probe_only']is False,
         'same-language complete ExecuteSync/Release reports required')
    need(new['proof']['parent_report_sha256']==old_digest and wire(old['proof']['parent_input'])==wire(new['proof']['parent_input']),
         'native report must name the exact frozen model report and same ROM proof')
    a,b=old['source_sha256'],new['source_sha256']
    need(len(a)==74 and len(b)==79 and set(a)<set(b)and all(a[k]==b[k]for k in a)and
         all(type(v)is str and re.fullmatch('[0-9a-f]{64}',v)for v in list(a.values())+list(b.values())),
         'qualified source ancestry74→79 required; capture drift must remain explicit')
    old_f,new_f=old['fixtures'],new['fixtures'];need(len(old_f)==4 and len(new_f)==8,'four parent cells/eight Release inputs required')
    need(all(f['provenance']['parent_report_sha256']==old_digest for f in new_f)and
         all(f['provenance']['parent_report_sha256']==old['proof']['parent_report_sha256']for f in old_f),
         'every fixture must bind its exact parent report digest')
    cells=[(p,s)for p in(0,1)for s in(0x12345678,0x12345679)]
    need(wire([(f['plus'],f['seed'])for f in old_f])==wire(cells)and
         wire([(f['plus'],f['seed'],f['translated_result'])for f in new_f])==wire([(p,s,v)for p,s in cells for v in(0,1)]),
         'distinct Plus/seed/translated-result input cells required')
    grid(old,old_f,OLD_POLICIES,dict(result=0,void_value=0,clobber=False,release_error=None))
    grid(new,new_f,NEW_POLICIES,dict(wake_value=0,clobber=False,stale_error=False))
    pairs=[];negative=[]
    for i,f in enumerate(old_f):
        for value,offset in((0,0),(1,2)):
            old_row=old['cases'][i*8+offset]['result'];m=old_row['services'][1];n=new['cases'][(i*2+value)*6]['result']
            guard=blob(old_row['guard_before'],56,'parent guard');need(old_row['guard_before']==old_row['guard_after'],'parent guard must be preserved')
            proof=compare_pair(m,n,guard);pairs.append(dict(plus=f['plus'],seed=f['seed'],translated_result=value,proof=proof))
        normal=old['cases'][i*8]['result']['services'][1];fault=old['cases'][i*8+3]['result']['services'][1]
        require_fault_contract(normal,fault)
        native=new['cases'][i*2*6]['result'];guard=blob(old['cases'][i*8]['result']['guard_before'],56,'parent guard')
        try:compare_pair(fault,native,guard)
        except ValueError as error:
            need(str(error)=='captured parent frame contract differs','negative control rejected for an unrelated reason')
            negative.append(dict(plus=f['plus'],seed=f['seed'],rejection=str(error),native_void_r0=native['returned'][0]))
        else:raise ValueError('faulty frozen model accepted as native field equivalence')
    return dict(schema='native-release-frozen-contract-holdout-v1',language=old['language'],model_report_sha256=old_digest,native_report_sha256=new_digest,
        input_sha256=old['proof']['parent_input']['sha256'],matched_pairs=pairs,rejected_fault_contracts=negative,
        oracle_modules_imported=0,guest_calls=0,compiler_calls=0,whole_ram_equivalence_claimed=False,complete_caller_equivalence_claimed=False,
        limits=['Retrospective comparison of the earlier retained contract, not a preregistered blind experiment',
                'Receipt provenance and field/frame/stack/ABI comparison; independent ROM/ELF and original trace qualification remain required',
                'Volatile register differences are reported, not requalified by this field-contract comparison',
                'Whole isolated RAM differs in code/setup/extra stack; full CPU register equality is deliberately not claimed',
                'Wakeup remains modeled; no natural filesystem completion, original MW rebuild, SAVE or hardware claim'])


def analyze(model_report,native_report):
    old,a=read_report(model_report);new,b=read_report(native_report);return compare_reports(old,new,a,b)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--model-report',type=Path,required=True);p.add_argument('--native-report',type=Path,required=True)
    p.add_argument('--json',action='store_true');a=p.parse_args()
    try:r=analyze(a.model_report,a.native_report)
    except(ValueError,KeyError,TypeError,OSError)as error:p.exit(2,str(error)+'\n')
    if a.json:print(json.dumps(r,indent=2,sort_keys=True))
    else:print(r['language'],len(r['matched_pairs']),'frozen/native frame contracts matched;',len(r['rejected_fault_contracts']),'faulty contracts rejected; isolated scope only')


if __name__=='__main__':main()
