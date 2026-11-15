#!/usr/bin/env python3
"""Export earlier caller/empty-archive invariants without a Next oracle or ROM.

Standard library only. Keep a dated receipt/hash before the new guest. The output
does not prove chronology or authenticate a native campaign by itself.
"""
from pathlib import Path
import argparse,gzip,hashlib,json,struct


sha=lambda b:hashlib.sha256(b).hexdigest()


def need(value,message):
    if not value:raise ValueError(message)


def u32s(r):return len(r)==16 and all(type(x)is int and 0<=x<2**32 for x in r)


def read_report(path):
    need(path.stat().st_size<=16*1024**2,'bounded compressed parent16MiB')
    with(gzip.open(path,'rb')if path.suffix=='.gz'else path.open('rb'))as f:data=f.read(16*1024**2+1)
    need(len(data)<=16*1024**2,'bounded decoded parent16MiB');return json.loads(data)


def freeze(path):
    r=read_report(path);digest=sha(path.read_bytes());n=len(r['groups']);cells=[]
    need(r['schema']=='native-release-wakeup-composed-v1'and r['cpu_executed']is True and r['compiler_invoked']is False and
        r['probe_only']is False and len(r['fixtures'])==16 and n>0 and len(r['cases'])==n*4,'complete earlier native composition report')
    need(all(type(g['ordinal'])is int for g in r['groups'])and sorted(g['ordinal']for g in r['groups'])==list(range(n)),
        'earlier ordered complete group identifiers')
    need({(f['language'],f['ordinal'])for f in r['fixtures']}=={(language,i)for language in('EN','IT')for i in range(8)},'earlier16 provenance identities')
    for f in r['fixtures']:
        need(type(f['ordinal'])is int and all(type(f[k])is int for k in('plus','seed','translated_result')),'earlier strict fixture labels')
        matches=[g for g in r['groups']if dict(language=f['language'],ordinal=f['ordinal'])in g['members']]
        need(len(matches)==1,'earlier provenance member belongs to one group');g=matches[0];cell=r['cases'][g['ordinal']*4];row=cell['result']
        need(cell['label']=='normal'and cell['group']==g['ordinal']and row['policy']==dict(bypass_wakeup=False)and
            row['observe']is True and type(row['fill'])is int and row['fill']==0xA5 and row['services']==[],'earlier native normal cell')
        frame=bytes.fromhex(row['frame_after']);guard=bytes.fromhex(row['guard_after']);arc=bytearray.fromhex(row['archive_after']);entry=row['returned']
        need(len(frame)==352 and len(guard)==56 and row['guard_before']==row['guard_after']and len(arc)==92 and u32s(entry)and
            row['halt_pc']=='0x20d7760','earlier exact checkpoint/frame/guard/archive')
        need(struct.unpack_from('<I',arc,28)[0]==0x13 and struct.unpack_from('<I',arc,36)[0]==0 and struct.unpack_from('<I',arc,88)[0]==0,
            'earlier running empty archive and no IDLE callback proc_flag88')
        file_offset=entry[4]-(entry[13]-40)
        need(40<=file_offset<=280,'original bridge file belongs to live caller frame')
        archive_pointer=struct.unpack_from('<I',frame,file_offset+8)[0]
        incoming=list(entry);incoming[0]=archive_pointer;incoming[14]=0x20D7768;struct.pack_into('<I',arc,28,3)
        cells.append(dict(language=f['language'],ordinal=f['ordinal'],plus=f['plus'],seed=f['seed'],translated_result=f['translated_result'],
            parent_report_sha256=digest,parent_group=g['ordinal'],checkpoint_pc=row['halt_pc'],checkpoint_regs=entry,
            parent_frame352_sha256=sha(frame),parent_guard56_sha256=sha(guard),parent_archive92_sha256=sha(bytes.fromhex(row['archive_after'])),
            parent_whole_ram_sha256=row['whole_ram_sha256'],expected_next_entry=incoming,expected_live_caller312_sha256=sha(frame[40:]),
            expected_archive92_after_sha256=sha(bytes(arc)),expected_R0=0,expected_return_pc='0x20d7768',expected_I_bit=0,callee_saved_indices=[*range(4,12),13]))
    return dict(schema='native-fs-next-empty-prospective-fields-v1',source='Earlier native composition output plus the original two-instruction bridge; no Next predictor',cells=cells,
        chronology='Retain the export and command receipt before the new guest; export alone proves no inspection/compilation chronology',
        limits=['Live caller312 is frozen; lower40 earlier stack bytes are dead and reusable',
                'Earlier frame352+guard56 is an observed span; other bytes require explicit provenance',
                'Known inputs/sources; no blind, callback, nonempty queue, natural boot, card or hardware result'])


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--parent-report',type=Path,required=True);p.add_argument('--json',type=Path,required=True);a=p.parse_args()
    try:
        source=Path(__file__).resolve().parents[3]
        need(a.json.resolve()!=source and source not in a.json.resolve().parents,'use fresh private output outside source')
        r=freeze(a.parent_report)
        with a.json.open('x')as f:f.write(json.dumps(r,indent=2)+'\n')
    except(ValueError,KeyError,TypeError,OSError)as error:p.exit(2,str(error)+'\n')
    print('Earlier field invariants exported; native Next activation remains unproved')


if __name__=='__main__':main()
