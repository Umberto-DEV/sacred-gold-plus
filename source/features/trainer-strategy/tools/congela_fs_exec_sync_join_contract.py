#!/usr/bin/env python3
"""Export NextNULL checkpoint/BOOL/POP invariants without the new join predictor.

Standard library only, no ROM or CPU. Export before the new guest and retain its
receipt. This file alone proves neither campaign authenticity nor chronology.
"""
from pathlib import Path
import argparse,gzip,hashlib,json,re,struct

sha=lambda b:hashlib.sha256(b).hexdigest()
TOP,FILE,ARC=0x23BEEC0,0x23BEDD0,0x21E3654


def need(value,message):
    if not value:raise ValueError(message)


def u32s(r):
    return type(r)is list and len(r)==16 and all(type(x)is int and 0<=x<2**32 for x in r)


def read_report(path):
    need(path.stat().st_size<=16*1024**2,'bounded parent file16MiB')
    with(gzip.open(path,'rb')if path.suffix=='.gz'else path.open('rb'))as stream:data=stream.read(16*1024**2+1)
    need(len(data)<=16*1024**2,'bounded decoded parent16MiB');return json.loads(data)


def freeze(path):
    r=read_report(path);digest=sha(path.read_bytes());n=len(r['groups']);cells=[]
    need(r['schema']=='native-fs-next-isolated-v1'and r['cpu_executed']is True and r['compiler_invoked']is False and
        r['probe_only']is False and n>0 and len(r['fixtures'])==16 and len(r['cases'])==n*4,'complete earlier native Next report')
    need(all(type(g['ordinal'])is int for g in r['groups'])and sorted(g['ordinal']for g in r['groups'])==list(range(n)),
        'earlier ordered group identifiers')
    need({(f['language'],f['ordinal'])for f in r['fixtures']}=={(language,i)for language in('EN','IT')for i in range(8)},
        'earlier16 unique provenance identities')
    members=[(m['language'],m['ordinal'])for g in r['groups']for m in g['members']]
    need(len(members)==16 and len(set(members))==16 and set(members)=={(f['language'],f['ordinal'])for f in r['fixtures']},
        'earlier groups partition the sixteen origins')
    for f in r['fixtures']:
        need(all(type(f[k])is int for k in('ordinal','plus','seed','translated_result'))and f['translated_result']in(0,1),
            'earlier typed fixture labels and finite error')
        g=next(g for g in r['groups']if dict(language=f['language'],ordinal=f['ordinal'])in g['members'])
        cell=r['cases'][g['ordinal']*4];row=cell['result'];entry=row['returned']
        need(cell['group']==g['ordinal']and cell['label']=='normal'and row['observe']is True and
            type(row['fill'])is int and row['fill']==0xA5 and row['policy']==dict(not_running=False)and row['services']==[],
            'earlier normal native domain')
        need(u32s(entry)and entry[0]==0 and entry[4]==FILE and entry[13]==TOP-312 and entry[15]==0x6000001F and
            row['halt_pc']=='0x20d7768','earlier actual NextNULL entry context')
        frame=bytes.fromhex(row['frame_after']);guard=bytes.fromhex(row['guard_after']);archive=bytes.fromhex(row['archive_after'])
        need(len(frame)==416 and len(guard)==56 and row['guard_before']==row['guard_after']and len(archive)==92,
            'earlier complete observed frame416/guard56/archive92')
        pop=struct.unpack_from('<2I',frame,104)
        error=struct.unpack_from('<I',frame,FILE-(TOP-416)+20)[0]
        need(pop==(ARC,0x20D7928)and error==f['translated_result']and
            struct.unpack_from('<I',frame,FILE-(TOP-416)+8)[0]==ARC,'original stored error and POP saved pair')
        whole=row['whole_ram_sha256'];need(type(whole)is str and re.fullmatch('[0-9a-f]{64}',whole),'earlier whole-RAM digest')
        returned=list(entry);returned[0]=int(error==0);returned[4]=pop[0];returned[13]+=8
        returned[15]=0x6000001F if error==0 else 0x2000001F
        cells.append(dict(language=f['language'],ordinal=f['ordinal'],plus=f['plus'],seed=f['seed'],translated_result=f['translated_result'],
            parent_report_sha256=digest,parent_group=g['ordinal'],checkpoint_pc=row['halt_pc'],checkpoint_regs=entry,
            frame416_sha256=sha(frame),guard56_sha256=sha(guard),archive92_sha256=sha(archive),
            parent_whole_ram_sha256=whole,stored_error=error,expected_returned=returned,expected_return_pc='0x20d7928',
            expected_memory_unchanged=True))
    return dict(schema='native-fs-exec-sync-join-prospective-fields-v1',cells=cells,
        source='Actual earlier native NextNULL contexts and original saved POP pair; BOOL from stored error==SUCCESS',
        chronology='Export before new predictor/guest; body already inspected, known inputs/sources, not blind',
        limits=['Field contract alone does not prove seven instructions or three reads executed',
                'Initial join RAM must separately bind parent whole-RAM hash plus authenticated code/gate overlay',
                'No Async, original Send POP, full caller, natural completion, save or hardware coverage'])


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--parent-report',type=Path,required=True)
    p.add_argument('--json',type=Path,required=True);a=p.parse_args()
    try:
        source=Path(__file__).resolve().parents[3]
        need(a.json.resolve()!=source and source not in a.json.resolve().parents,'fresh private output outside source')
        result=freeze(a.parent_report)
        with a.json.open('x')as output:output.write(json.dumps(result,indent=2)+'\n')
    except(ValueError,KeyError,TypeError,OSError)as error:p.exit(2,str(error)+'\n')
    print('Earlier native fields exported; original join activation remains unproved')


if __name__=='__main__':main()
