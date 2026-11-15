#!/usr/bin/env python3
"""Prepare/execute/verify original GetSubstruct on owned synthetic inputs.

130 calls: every PID-row/selector pair, ignored PID bits and observer OFF. No private
capture, SDK model, service response, compiler or ROM mutation is needed.
"""
from pathlib import Path
import argparse
import copy
import importlib.util
import json
import subprocess
import types


def load(path,name):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


HERE=Path(__file__).resolve();SOURCE=HERE.parents[3]
B=load(HERE.parents[1]/'test/mon_substruct_bench.py','substructure_whole_verifier')
Q=load(HERE.with_name('qualifica_mon_substruct.py'),'substructure_owned_qualification_metadata')
F,L,R,M,need=B.F,B.L,B.R,B.M,B.need
PIN='cb614ad23449d5852b40321dc409c4143872b35c'
REFERENCE={'src/pokemon.c':'1d784ece4650b84e426a437ee20e4a926475fc20ef761e67440d0c0136548fa3',
 'include/pokemon.h':'54a8f712af315e66776464ed2507e8970270524aa5b16ea8e610762b742ee1a1',
 'include/pokemon_types_def.h':'032888003b7a68733dedb83d55decc43cc4202b6ca66b284f62256aacb02e24d'}


def source_identities():
    found={};seen=set();pending=[B,Q]
    while pending:
        module=pending.pop()
        if id(module)in seen:continue
        seen.add(id(module));path=getattr(module,'__file__',None)
        if not path:continue
        p=Path(path).resolve()
        if SOURCE not in p.parents:continue
        found[str(p.relative_to(SOURCE))]=R.sha(p.read_bytes())
        pending.extend(value for value in vars(module).values()if isinstance(value,types.ModuleType))
    for p in(HERE,):found[str(p.relative_to(SOURCE))]=R.sha(p.read_bytes())
    return dict(sorted(found.items()))


def expected_owned_case(name):
    # Independent complete states of the two-instruction owned kernels.
    # The second instruction is BX LR, preserving these full16 states.
    cases={
        'ANDS-N-CV':(0x3000003f,{0:0x80000003,4:0x80000001},{0:0x80000001},0xb000003f),
        'ANDS-Z-CV':(0x3000003f,{0:0x80000000,4:1},{0:0},0x7000003f),
        'LDRB-unaligned-FF':(0xb000003f,{6:0x3000,0:3},{0:255},0xb000003f),
        'LDRB-destination-base':(0x7000003f,{0:0x3000,1:15},{0:128},0x7000003f),
        'LDRB-all-aliases':(0x1000003f,{1:0x1801},{1:254},0x1000003f),
        'LDRB-address-wrap32':(0xf000003f,{6:0xffffffff,0:0x3002},{0:129},0xf000003f)}
    flags,before,after,final_flags=cases[name]
    initial=[0x10000000+i*0x10101 for i in range(13)]+[0x4000,0x1101,flags]
    for i,value in before.items():initial[i]=value
    final=list(initial)
    for i,value in after.items():final[i]=value
    final[15]=final_flags
    flow=[dict(pc=0x1000,regs=initial),dict(pc=0x1002,regs=final)]
    return final,R.sha(json.dumps(flow,sort_keys=True).encode())


def verify_qualification(path):
    report=json.loads(Path(path).read_bytes())
    expected={str(p.relative_to(SOURCE)):R.sha(p.read_bytes())for p in(Q.HERE,Path(Q.A.__file__),Path(Q.T.__file__),Path(Q.T.K.__file__))}
    need(report['schema']=='native-mon-substructure-owned-kernels-v1'and type(report['CPU_model'])is int and report['CPU_model']==17,'qualified GetSubstruct instruction receipt')
    need(B.wire(report['source_sha256'])==B.wire(expected),'owned instruction qualification source drift')
    names={'ANDS-N-CV','ANDS-Z-CV','LDRB-unaligned-FF','LDRB-destination-base','LDRB-all-aliases','LDRB-address-wrap32'}
    rows=report['cases']
    need(type(rows)is list and len(rows)==6 and {x['name']for x in rows}==names,'complete six owned instruction kernels')
    for row in rows:
        need(row['full16_every_pc']is True and row['all_pages']is True and type(row['instructions'])is int and row['instructions']==2 and
             type(row['reads'])is int and row['reads']==int(row['name'].startswith('LDRB'))and type(row['stores'])is int and row['stores']==0,'completed owned instruction checks')
        need(type(row['returned'])is list and len(row['returned'])==16 and all(type(v)is int and 0<=v<=0xffffffff for v in row['returned']),'typed owned qualification full16')
        expected,flow_sha256=expected_owned_case(row['name'])
        need(B.wire(row['returned'])==B.wire(expected),'owned qualification expected full16')
        need(row['flow_sha256']==flow_sha256,'owned qualification exact two-step full16 flow digest')
    return report


def prepare(args):
    receipt,parts=L.prepare(args.rom)
    need(B.wire(json.loads(args.input_contract.read_bytes()))==B.wire(F.freeze(receipt,parts)),'exact frozen substructure contract')
    ref=args.reference.resolve()
    need(subprocess.check_output(['git','-C',str(ref),'rev-parse','HEAD'],text=True).strip()==PIN and
         not subprocess.check_output(['git','-C',str(ref),'status','--porcelain']),'clean pinned substructure source reference')
    for name,digest in REFERENCE.items():need(R.sha((ref/name).read_bytes())==digest,'substructure reference drift '+name)
    source_table=L.source_offsets((ref/'src/pokemon.c').read_text())
    need(source_table==parts['offsets'],'complete C source array / installed table128')
    qualification=verify_qualification(args.qualification)
    inputs={name:F.make_input(parts,pid,which)for name,(pid,which)in F.PROFILES.items()}
    predictions={name:B.predict(f)for name,f in inputs.items()}
    bindings=dict(source_sha256=source_identities(),input_contract_sha256=R.file_sha(args.input_contract),
        reference_pin=PIN,reference_files=REFERENCE,source_table_sha256=R.sha(source_table),
        instruction_qualification_sha256=R.file_sha(args.qualification),qualification_source_sha256=qualification['source_sha256'],
        original_C_compiler_reconstructed=False,compiler_invoked=False,
        runtime_models=0,retained_CPU_producer_sha256=B.PRODUCER_SHA)
    return receipt,inputs,predictions,bindings


def controls(raws,inputs):
    need(set(raws)=={name for name,_,_ in F.MATRIX},'complete130call GetSubstruct matrix')
    for name,key,observe in F.MATRIX:
        raw=raws[name];need(raw['observed']is observe,'GetSubstruct observer cell binding');B.require_run(inputs[key],raw)
    base,alias,off=(raws[n]for n in('R03W1','IgnoredPID_R03W1','R03W1_OFF'))
    for key in('returned','stop_pc','final_map_sha256','final_pages','executed_count','read_count','store_count'):
        need(B.wire(base[key])==B.wire(off[key]),'GetSubstruct OFF neutrality '+key)
        need(B.wire(base[key])==B.wire(alias[key]),'GetSubstruct ignored-PID final convergence '+key)
    need(base['initial']==off['initial'],'GetSubstruct OFF same complete input')
    need(base['initial']['initial_map_sha256']==alias['initial']['initial_map_sha256'],'ignored-PID same initial memory')
    a,b=base['initial']['entry_regs'],alias['initial']['entry_regs']
    need(a[:1]+a[2:]==b[:1]+b[2:]and a[1]^b[1]==0x80000001,'only two ignored PID argument bits change')
    need(base['flow']!=alias['flow']and base['reads']==alias['reads']and base['stores']==alias['stores'],'real ignored-PID prefix kept, identical accesses')
    def joined(raw):
        i=next(i for i,x in enumerate(raw['flow'])if x['pc']==0x2072624);return raw['flow'][i:]
    need(joined(base)==joined(alias),'ignored-PID full16 join after LSLr1')
    def context(raw,pc):return next(x for x in raw['flow']if x['pc']==pc)['regs']
    need(context(base,0x2072610)[15]^context(alias,0x2072610)[15]==0x80000000,'ignored-PID real intermediate N flag difference')
    coverage=[]
    for row in range(32):
        for which in range(4):
            raw=raws[f'R{row:02d}W{which}'];coverage.append(raw['reads'][1]['address'])
            need(raw['returned'][1:3]==[4*row,which],'native table row/selector ABI')
    need(coverage==list(range(B.TABLE,B.TABLE+128)),'all128 source-selected table bytes actually read')
    for which in range(4):
        zero,duplicate=raws[f'R00W{which}'],raws[f'R24W{which}']
        need(zero['returned'][0]==duplicate['returned'][0]and zero['returned'][1]==0 and duplicate['returned'][1]==96,'same pointer is not row modulo24 ABI')
        need([i for i,(a,b)in enumerate(zip(zero['returned'],duplicate['returned']))if a!=b]==[1],'duplicate table row full16 differs onlyR1')
        need(zero['reads'][1]['address']+96==duplicate['reads'][1]['address']and zero['reads'][1]['hex']==duplicate['reads'][1]['hex'],'duplicate row actual distinct read address')
    cases=[]
    def altered(name,reason,edit,raw=base,fixture='R03W1'):
        forged=copy.deepcopy(raw);edit(forged);cases.append((name,inputs[fixture],forged,reason))
    duplicate=raws['R24W1']
    altered('row24_normalized_R1_same_pointer','source GetSubstruct full16 return ABI',lambda x:x['returned'].__setitem__(1,0),duplicate,'R24W1')
    altered('row24_normalized_read_same_pointer','source GetSubstruct native reads',lambda x:x['reads'][1].__setitem__('address',B.TABLE+1),duplicate,'R24W1')
    altered('aligned_odd_table_literal','source GetSubstruct native reads',lambda x:x['reads'][0].__setitem__('hex',(B.TABLE&~3).to_bytes(4,'little').hex()))
    altered('word_instead_of_byte_load','source GetSubstruct native reads',lambda x:x['reads'][1].update(bytes=4,hex='60000000'))
    altered('AND_replaced_by_EOR','source GetSubstruct native flow',lambda x:context(x,0x2072614).__setitem__(0,0x38000))
    altered('mask_ignores_bit17','source GetSubstruct native flow',lambda x:context(x,0x2072618).__setitem__(4,15),raws['R31W0'],'R31W0')
    altered('transposed_row_selector_address','source GetSubstruct native reads',lambda x:x['reads'][1].__setitem__('address',B.TABLE+6),raws['R02W1'],'R02W1')
    altered('wrong_saved_preimage','source GetSubstruct native stores',lambda x:x['stores'][0].__setitem__('before','00000000'))
    altered('missing_POP_word','source GetSubstruct native reads',lambda x:x['reads'].pop())
    altered('wrong_native_LR','source GetSubstruct full16 return ABI',lambda x:x['returned'].__setitem__(14,0x201ff59))
    altered('unattributed_Box_header_read','source GetSubstruct native reads',lambda x:x['reads'].append(dict(pc=0x2072626,address=F.BOX,bytes=1,hex='a5')))
    altered('assert_BL_admitted','source GetSubstruct native flow',lambda x:x['flow'].insert(10,dict(pc=0x207261c,regs=list(x['flow'][10]['regs']))))
    altered('alignment_admitted_as_code','source GetSubstruct native flow',lambda x:x['flow'][-1].__setitem__('pc',0x207262e))
    altered('ignored_PID_input_camouflage','source GetSubstruct native flow',lambda x:x.__setitem__('initial',copy.deepcopy(base['initial'])),alias)
    altered('ignored_PID_prefix_normalized','source GetSubstruct native flow',lambda x:x.__setitem__('flow',copy.deepcopy(base['flow'])),alias,'IgnoredPID_R03W1')
    altered('bool_selector_metadata','complete frozen GetSubstruct input',lambda x:x['initial'].__setitem__('input_which',True))
    altered('signed_PID_metadata','complete frozen GetSubstruct input',lambda x:x['initial'].__setitem__('input_PID',-2147459071),alias,'IgnoredPID_R03W1')
    altered('readonly_table_write','source GetSubstruct native stores',lambda x:x['stores'].append(dict(pc=0x2072608,address=B.TABLE,bytes=1,before='00',value=32)))
    altered('missing_dataBlocks_header_offset','source GetSubstruct full16 return ABI',lambda x:x['returned'].__setitem__(0,x['returned'][0]-8))
    rejected=[]
    for name,f,raw,reason in cases:
        try:B.require_run(f,raw)
        except ValueError as e:
            need(str(e)==reason,'cause-specific GetSubstruct forgery '+name+': '+str(e));rejected.append(dict(name=name,reason=str(e)))
        else:raise ValueError('accepted forged GetSubstruct evidence '+name)
    return dict(grid_calls=128,table_bytes_observed=128,ignored_PID_pairs=1,OFF_pairs=1,duplicate_row_pairs=4,
        ignored_PID_full16_join_pc=0x2072624,total_native_instructions=2210,forgeries=rejected)


def require_completed_report(report,records,bindings,checks):
    need(report['schema']=='native-mon-substructure-report-v1'and report['mode']=='matrix'and report['CPU_executed']is True and
         report['verdict']=='PASS within full32x4 selectors/one ignored-PID alias/native GetSubstruct scope','completed original substructure matrix report')
    need(B.wire(report['raw'])==B.wire(records)and B.wire(report['bindings'])==B.wire(bindings)and
         B.wire(report['controls'])==B.wire(checks),'substructure original raw hashes/bindings/controls')


def save(path,value):
    with path.open('x')as out:json.dump(value,out,indent=2);out.write('\n')


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--mode',choices=('prepare','matrix','verify'),required=True)
    for n in('rom','reference','input-contract','qualification','out-dir'):p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--raw-dir',type=Path);a=p.parse_args()
    try:
        out=a.out_dir.resolve();need(out!=SOURCE and SOURCE not in out.parents and not out.exists(),'fresh private substructure output directory')
        need((a.raw_dir is not None)==(a.mode=='verify'),'raw-dir only and required for verify')
        receipt,inputs,predictions,bindings=prepare(a);out.mkdir(parents=True)
        prepared=dict(schema='native-mon-substructure-prepared-v1',resources=receipt,bindings=bindings,
            predictions={name:dict(instructions=len(x['flow']),reads=len(x['reads']),stores=len(x['stores']),peak=x['native_peak'],row=x['row'],selector=x['selector'],offset=x['offset'],table_read_address=x['table_read_address'],returned=x['returned'])for name,x in predictions.items()},CPU_executed=False)
        save(out/'prepared.json',prepared)
        if a.mode=='prepare':print('GetSubstruct source/bytes/frozen/math prepared; no CPU/compiler');return
        raws={};records=[]
        for name,key,observe in F.MATRIX:
            need(source_identities()==bindings['source_sha256'],'substructure source drift before cell')
            if a.mode=='matrix':
                raw=B.run(inputs[key],B.observation_policy(predictions[key]),observe);save(out/(name+'.json'),raw)
            else:raw=json.loads((a.raw_dir/(name+'.json')).read_bytes())
            need(source_identities()==bindings['source_sha256'],'substructure source drift after cell')
            raws[name]=raw;B.require_run(inputs[key],raw)
            records.append(dict(name=name,file=name+'.json',sha256=R.file_sha((out if a.mode=='matrix'else a.raw_dir)/(name+'.json'))))
        if a.mode=='verify':
            old=json.loads((a.raw_dir/'prepared.json').read_bytes());need(B.wire(old)==B.wire(prepared),'substructure original prepared bindings/predictions')
        checks=controls(raws,inputs)
        if a.mode=='verify':
            old_report=json.loads((a.raw_dir/'report.json').read_bytes())
            require_completed_report(old_report,records,bindings,checks)
        need(source_identities()==bindings['source_sha256'],'substructure source drift before report')
        save(out/('verification.json'if a.mode=='verify'else'report.json'),dict(schema='native-mon-substructure-report-v1',mode=a.mode,CPU_executed=a.mode=='matrix',bindings=bindings,raw=records,controls=checks,verdict='PASS within full32x4 selectors/one ignored-PID alias/native GetSubstruct scope'))
    except(ValueError,OSError,KeyError,EOFError,subprocess.CalledProcessError)as e:p.exit(2,str(e)+'\n')
    print('Whole native substructure '+a.mode+' PASS; 130 calls, zero models/runtime host writes')


if __name__=='__main__':main()
