#!/usr/bin/env python3
"""Freeze earlier Release empty-Wakeup field invariants using only the stdlib.

Run before inspecting/building/running the new Wakeup body. The subsequent native
CLI separately authenticates all parent receipts. This export alone certifies no
native execution, chronology, ROM identity or original compiler provenance.
"""
from pathlib import Path
import argparse,gzip,hashlib,json


sha=lambda b:hashlib.sha256(b).hexdigest()


def need(value,message):
    if not value:raise ValueError(message)


def read_report(path):
    need(path.stat().st_size<=16*1024**2,'bounded compressed parent16MiB')
    with(gzip.open(path,'rb')if path.suffix=='.gz'else path.open('rb'))as f:data=f.read(16*1024**2+1)
    need(len(data)<=16*1024**2,'bounded decoded parent16MiB');return json.loads(data)


def freeze(paths):
    cells=[];digests={}
    for language in('EN','IT'):
        p=paths[language];r=read_report(p);digest=sha(p.read_bytes());digests[language]=digest
        need(r['schema']=='native-fs-release-isolated-v1'and r['language']==language and r['cpu_executed']is True and
             r['probe_only']is False and len(r['fixtures'])==8 and len(r['cases'])==48,'complete earlier Release8/48 report')
        for i,f in enumerate(r['fixtures']):
            row=r['cases'][i*6];need(row['label']=='normal','earlier positive grid position')
            s=row['result']['services'][0];frame=bytes.fromhex(s['frame_before']);archive=bytes.fromhex(s['archive_before']);entry=s['entry']
            need(s['pc']=='0x20d1ecc'and len(frame)==328 and len(archive)==92 and len(entry)==16 and
                all(type(v)is int and 0<=v<2**32 for v in entry)and s['writes']==[]and
                s['frame_before']==s['frame_after']and s['archive_before']==s['archive_after'],'earlier empty value-only service invariants')
            queue=entry[0];frame_address=entry[13];off=queue-frame_address
            need(0<=off<=320 and frame[off:off+8]==bytes(8),'earlier queue owner/empty bytes')
            cells.append(dict(language=language,ordinal=i,plus=f['plus'],seed=f['seed'],translated_result=f['translated_result'],entry=entry,
                parent_report_sha256=digest,caller_frame_bytes=328,caller_frame_before_sha256=sha(frame),expected_caller_frame_after_sha256=sha(frame),
                archive_bytes=92,archive_before_sha256=sha(archive),expected_archive_after_sha256=sha(archive),input_queue_address=queue,
                input_queue8=bytes(8).hex(),held_out_from_first_guest_probe=i==7))
    return dict(schema='os-wakeup-empty-prospective-field-contract-v1',parent_reports_sha256=digests,cells=cells,
        source='Earlier qualified Release MODEL records; authenticate them separately in the native CLI',
        chronology='Freeze and retain this file/hash before inspecting the next component; the file does not prove its own creation time',
        limits=['Earlier field/control invariants can also be satisfied by a no-op; require a separate native activation transcript',
                'Ordinal7 reservation is not blind and may duplicate another input; group by complete CPU state, not labels'])


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in('en-report','it-report','json'):p.add_argument('--'+key,type=Path,required=True)
    a=p.parse_args()
    try:
        need('source'not in a.json.resolve().parts,'contract contains local fixture hashes; use a private output path')
        r=freeze(dict(EN=a.en_report,IT=a.it_report))
        with a.json.open('x')as f:f.write(json.dumps(r,indent=2)+'\n')
    except(ValueError,KeyError,TypeError,OSError)as error:p.exit(2,str(error)+'\n')
    print('Earlier field contract frozen; native activation remains unproved')


if __name__=='__main__':main()
