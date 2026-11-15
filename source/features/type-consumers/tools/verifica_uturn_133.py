#!/usr/bin/env python3
"""Finite native regression: authenticated r4 with a counterfactual 1.3.3 helper."""
import argparse
from collections import Counter
import importlib.util
import json
from pathlib import Path

spec = importlib.util.spec_from_file_location('uturn_native_legacy', Path(__file__).with_name('attribuisci_uturn.py'))
A = importlib.util.module_from_spec(spec); spec.loader.exec_module(A)
from sgp131 import uturn_flinch as N
from sgp12.rom import bl_thumb


def artifact(directory):
    directory = Path(directory)
    receipt = json.loads((directory / 'receipt.json').read_text())
    obj = (directory / 'uturn.o').read_bytes(); payload = (directory / 'native.bin').read_bytes()
    A.need(receipt['source_sha256'] == A.sha(N.NATIVE.read_bytes()) and receipt['compiler'] == dict(version=N.COMPILER_VERSION, executable_sha256=N.COMPILER_SHA256, flags=list(N.FLAGS)), 'candidate source/compiler receipt')
    A.need(A.sha(obj) == receipt['object_sha256'] and len(payload) == receipt['bytes'] == 74 and A.sha(payload) == receipt['payload_sha256'] == N.HELPER_SHA256, 'candidate object/payload identity')
    loader = N._module(A.G.SOURCE/'features/options/tools/carica_text.py', 'uturn_133_elf')
    names = ('uturn_snapshot_effect','uturn_effect_live_call','uturn_snapshot_modifier','uturn_modifier_live_call')
    raw, symbols = loader.load_text(obj, N.HELPER_ADDRESS, names)
    A.need(len(raw)==74 and [symbols[n]&~1 for n in names] == [N.HELPER_ADDRESS+x for x in (0,26,32,68)], 'candidate ELF geometry')
    rebuilt=bytearray(raw)
    for off,target in ((26,N.GET_EFFECT),(68,N.GET_MODIFIER)):
        A.need(raw[off:off+4] == bytes.fromhex('00f000f8'), 'candidate BL placeholder')
        rebuilt[off:off+4]=bl_thumb(N.HELPER_ADDRESS+off,target)
    A.need(bytes(rebuilt)==payload, 'candidate ELF fixups')
    return payload, receipt


def counterfactual(model,payload):
    A.need(len(payload)==74 and A.sha(payload)==N.HELPER_SHA256, 'candidate payload')
    old=A.G.piece(model['segments'],N.HELPER_ADDRESS,128)
    A.need(A.sha(old[:68])==A.U.HELPER_SHA256 and old[68:]==bytes(60),'legacy tail identity')
    segments=[]; count=0
    for address,data in model['segments']:
        if address<=N.HELPER_ADDRESS and N.HELPER_ADDRESS+128<=address+len(data):
            data=bytearray(data); offset=N.HELPER_ADDRESS-address
            before=bytes(data[offset-64:offset]); A.need(len(before)==64 and A.sha(before)=='77844c84762bcdf84e64503a1e0996c871c8ca1027846b8059e5b5b86a8688ce','foreign stub identity')
            data[offset:offset+128]=payload+bytes(54)
            A.need(bytes(data[offset-64:offset])==before,'foreign stub preservation')
            data=bytes(data); count+=1
        segments.append((address,data))
    A.need(count==1,'unique helper segment')
    return dict(model,segments=segments)


def semantic(r):
    return {k:r[k] for k in ('flinch','snapshot_after','seed_after','calls','modifier_abi_issues')}


def verify_rng(observation, expected):
    """Check native RNG call count and every exact seed transition."""
    calls=observation['rng_calls']; before=observation['seed_before']; after=observation['seed_after']
    A.need(type(expected) is int and expected in (0,1) and type(before) is int and 0<=before<=0xffffffff and type(after) is int and 0<=after<=0xffffffff,'RNG seed domain')
    A.need(len(calls)==expected and observation['calls']['rng']==expected,'RNG exact call count')
    current=before
    for call in calls:
        advanced=A.G.next_seed(current)
        A.need(call['before']==current and call['after']==advanced and call['value']==advanced>>16,'RNG recorded transition/value')
        current=advanced
    A.need(after==current,'RNG final seed')


def verify_case_rng(row):
    """Finite expectations, including legitimate live-item RNG on repeat."""
    name=row['name'];opts=row['options']
    if name=='fallback':
        A.need(opts['incoming'] in (0,221),'fallback RNG item domain')
        expected=int(opts['incoming']==221)
        for role in ('original','legacy','new'):verify_rng(row[role],expected)
    elif name=='word':
        verify_rng(row['original'],0);verify_rng(row['new'],0)
        legacy_expected=opts['ordinary_word'] in (0,-200)
        A.need((row['legacy'] is not None)==legacy_expected,'legacy RNG evidence coverage')
        if legacy_expected:verify_rng(row['legacy'],int(opts['ordinary_word']==-200))
    else:
        first={'rock':1,'fang':1,'roll10':1,'target_ko':1,'bite':1,
               'empty':0,'klutz':0,'embargo':0,'damage0':0,'failure':0,'target_missing':0}
        if name=='marked_boundary':
            A.need(opts['ordinary_word'] in (0x10000,0x10038,0x1ff38),'marked RNG word domain')
            expected=int(opts['ordinary_word'] in (0x10038,0x1ff38)); repeat=0
        else:
            A.need(name in first,'RNG case name');expected=first[name]
            repeat=int(name in ('empty','klutz','embargo'))
        verify_rng(row['new'],expected);verify_rng(row['repeat'],repeat)
        A.need(row['repeat']['seed_before']==row['new']['seed_after'],'RNG first/repeat continuity')


def verify_report_rng(report):
    rows=report['cases']
    expected={'fallback':16,'word':14,'rock':1,'fang':1,'empty':1,'klutz':1,'embargo':1,
              'roll10':1,'damage0':1,'failure':1,'target_missing':1,'target_ko':1,'bite':1,'marked_boundary':12}
    A.need(Counter(row['name'] for row in rows)==expected,'RNG finite matrix coverage')
    for row in rows:verify_case_rng(row)
    return dict(cases=len(rows), oracle='exact native RNG calls, seed transitions and repeat continuity')


def run(model,resources,payload):
    new=counterfactual(model,payload); old=A.counter_image(model,'old_hooks')
    def observe(which,opts):
        m,variant,profile={'legacy':(model,'current','legacy68'),'original':(old,'old_hooks','legacy68'),'new':(new,'current','current74')}[which]
        return A.NativeFlinch(m,resources,variant=variant,code_profile=profile).observe(**opts)
    rows=[]
    for battler in range(4):
        for item in (0,221):
            for roll in (9,10):
                opts=dict(pivot=False,incoming=item,roll=roll,attacker=battler,target=(battler+1)%4)
                base=observe('original',opts); current=observe('legacy',opts); fixed=observe('new',opts)
                A.need(semantic(fixed)==semantic(base),'fallback original equivalence')
                rows.append(dict(name='fallback',options=opts,original=base,legacy=current,new=fixed))
    words=[0,-1,-199,-200,-65536,-65537,-2147483648,-67107840,0xffff,0x20000,0x30038,0x80010a38,0xffff0a38,0x7fffffff]
    for word in words:
        opts=dict(pivot=False,incoming=0,ordinary_word=word,damage=0xffffff38,roll=99)
        base=observe('original',opts); fixed=observe('new',opts)
        A.need(semantic(fixed)==semantic(base),'unmarked word equivalence')
        legacy=observe('legacy',opts) if word in (0,-200) else None
        rows.append(dict(name='word',options=opts,original=base,legacy=legacy,new=fixed,
                         legacy_not_run_reason=None if legacy is not None else 'synthetic word may yield an out-of-domain legacy item lookup'))
    cases=[('rock',dict(outgoing=221,incoming=0)),('fang',dict(outgoing=327,incoming=0)),('empty',dict(outgoing=0,incoming=221)),('klutz',dict(outgoing=221,incoming=221,klutz=True)),('embargo',dict(outgoing=221,incoming=221,embargo=True)),('roll10',dict(roll=10)),('damage0',dict(damage=0)),('failure',dict(move_status=1)),('target_missing',dict(target=255)),('target_ko',dict(target_hp=0)),('bite',dict(eligible=False))]
    for name,opts in cases:
        bench=A.NativeFlinch(new,resources,code_profile='current74'); result=bench.observe(**opts)
        A.require_consumed(result); A.need(not result['modifier_abi_issues'],'snapshot fallback ABI')
        expected=name in ('rock','fang')
        A.need(result['flinch']==expected,'snapshot/gate result '+name)
        again=bench.repeat_parent(); A.need(again['snapshot_before']==0 and not again['modifier_abi_issues'],'once consumption '+name)
        rows.append(dict(name=name,options=opts,new=result,repeat=again))
    for battler in range(4):
        for word,expected in ((0x10000,False),(0x10038,False),(0x1ff38,True)):
            opts=dict(pivot=False,incoming=0,ordinary_word=word,attacker=battler,target=(battler+1)%4)
            bench=A.NativeFlinch(new,resources,code_profile='current74'); result=bench.observe(**opts)
            A.need(result['flinch']==expected and result['snapshot_after']==0 and not result['modifier_abi_issues'],'marked boundary and consumption')
            again=bench.repeat_parent(); A.need(again['snapshot_before']==0 and not again['flinch'] and not again['modifier_abi_issues'],'marked once')
            rows.append(dict(name='marked_boundary',options=opts,new=result,repeat=again))
    collision=next(r for r in rows if r['name']=='word' and r['options']['ordinary_word']==-200)
    A.need(collision['legacy']['flinch'] and not collision['original']['flinch'] and not collision['new']['flinch'],'legacy collision demonstrated')
    A.need(any(r['legacy']['modifier_abi_issues'] for r in rows if r['name']=='fallback'),'legacy ABI defect demonstrated')
    return rows


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('rom','v4','base','retail','artifact','json'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--language',choices=('EN','IT'),required=True);a=p.parse_args()
    out=a.json.resolve(); source=A.G.SOURCE.resolve()
    A.need(not a.json.is_symlink() and not out.exists() and out!=source and source not in out.parents,'fresh private output required')
    for path in (a.rom,a.v4,a.base,a.retail,a.artifact/'native.bin',a.artifact/'uturn.o',a.artifact/'receipt.json'):
        A.need(out!=path.resolve(),'output overlaps input')
    payload,receipt=artifact(a.artifact)
    models={role:A.G.S.SHARED.read_image(path,a.language,role) for role,path in (('retail',a.retail),('base11',a.base),('v4',a.v4),('r4',a.rom))}
    for role,model in models.items():
        raw=A.take(model['overlay'],A.U.FUNCTION,184); normal=bytearray(raw)
        if role=='retail' and a.language=='IT':
            address=int(model['record']['overlays'][1]['ram'],16)+A.U.FUNCTION-A.U.OVERLAY_BASE
            A.need(A.G.S.SHARED.branch(raw[0x52:0x56],address+0x52,'blx')==A.G.S.DIV,'retail IT division target')
            normal[0x52:0x56]=A.U.FUNCTION_PREIMAGE[0x52:0x56]
        A.need(bytes(normal)==(A.U.FUNCTION_POSTIMAGE if role=='r4' else A.U.FUNCTION_PREIMAGE),'native parent identity')
    current=models['r4'];resources=A.read_resources(a.rom,current); prior=A.read_resources(a.v4,models['v4'])
    A.need(A.SCRIPT.patch_member(prior['script'])==resources['script'],'script reconstruction')
    results=run(current,resources,payload)
    rng_oracle=verify_report_rng(dict(cases=results))
    report=dict(schema='uturn-133-counterfactual-v1',language=a.language,inputs=[m['record'] for m in models.values()],artifact=receipt,resources=resources['record'],cases=results,rng_oracle=rng_oracle,compatibility_green=True,limits=['Counterfactual helper on authenticated r4, not a composed candidate.', 'Producer is source-word interpreter; ability and script transport are models. Native getters, cache, RNG and division execute.', 'Not a complete natural pivot, P100, save, device or timing qualification.'])
    out.parent.mkdir(parents=True,exist_ok=True)
    with out.open('x') as f:json.dump(report,f,indent=2);f.write('\n')
    print(a.language,'finite counterfactual regression PASS')

if __name__=='__main__':main()
