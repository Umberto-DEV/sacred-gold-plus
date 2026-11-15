#!/usr/bin/env python3
"""Freeze earlier native Release outputs before running the composed component.

Standard library only. This exports invariants, not a native validation verdict
or proof of chronology. Later preparation authenticates the complete ancestors.
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


def u32s(r):return len(r)==16 and all(type(v)is int and 0<=v<2**32 for v in r)


def freeze(paths):
    cells=[]
    for language in('EN','IT'):
        path=paths[language];r=read_report(path);digest=sha(path.read_bytes())
        need(r['schema']=='native-fs-release-isolated-v1'and r['language']==language and r['cpu_executed']is True and
            r['probe_only']is False and len(r['fixtures'])==8 and len(r['cases'])==48,'complete earlier native Release report')
        for i,f in enumerate(r['fixtures']):
            cell=r['cases'][i*6];need(cell['label']=='normal','earlier normal grid position');row=cell['result'];s=row['services'][0]
            before,after,arc_before,arc_after,guard=map(bytes.fromhex,(f['frame'],row['frame_after'],f['archive_before'],row['archive_after'],row['guard_before']))
            need(len(before)==len(after)==328 and len(arc_before)==len(arc_after)==92 and len(guard)==56 and
                row['guard_before']==row['guard_after']and row['frame_before']==f['frame']and
                u32s(f['entry'])and u32s(row['returned'])and u32s(s['entry']),'earlier typed entry/return/frame/archive/guard')
            need(s['pc']=='0x20d1ecc'and s['writes']==[]and s['frame_before']==s['frame_after']and
                s['archive_before']==s['archive_after'],'earlier empty modeled Wakeup boundary')
            wake=s['entry'];off=wake[0]-wake[13];frame=bytes.fromhex(s['frame_before'])
            need(len(frame)==328 and 0<=off<=320 and frame[off:off+8]==bytes(8),'earlier empty queue owner')
            need(all(type(f[k])is int for k in('plus','seed','translated_result')),'earlier strict fixture labels')
            cells.append(dict(language=language,ordinal=i,plus=f['plus'],seed=f['seed'],translated_result=f['translated_result'],parent_report_sha256=digest,
                entry=f['entry'],expected_returned=row['returned'],expected_halt_pc=row['halt_pc'],frame328_before_sha256=sha(before),
                expected_frame328_after_sha256=sha(after),archive92_before_sha256=sha(arc_before),expected_archive92_after_sha256=sha(arc_after),
                queue8_after=bytes(8).hex(),wake_entry=wake,native_stack24_words=[wake[j]for j in(3,4,5,6,7,14)],stack24_preimage=guard[-24:].hex()))
    return dict(schema='native-release-wakeup-prospective-composition-fields-v1',frozen_before_P71_guest=True,
        source='Earlier qualified P69 native Release with modeled empty Wakeup; independent of the new composed predictor',cells=cells,
        limits=['No blindness; previous sources and standalone native bodies are already known',
            'Field comparator alone accepts modeled bypass; native activation must be checked separately',
            'Do not compare old/new wholeRAM hashes without accounting for code104 vs modeledNOP4 and explicit guard preimage'])


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in('en-report','it-report','json'):p.add_argument('--'+key,type=Path,required=True)
    a=p.parse_args()
    try:
        source=Path(__file__).resolve().parents[3]
        need(a.json.resolve()!=source and source not in a.json.resolve().parents,'use private contract output outside source')
        r=freeze(dict(EN=a.en_report,IT=a.it_report))
        with a.json.open('x')as f:f.write(json.dumps(r,indent=2)+'\n')
    except(ValueError,KeyError,TypeError,OSError)as error:p.exit(2,str(error)+'\n')
    print('Earlier caller-output contract exported; retain its hash before the new guest')


if __name__=='__main__':main()
