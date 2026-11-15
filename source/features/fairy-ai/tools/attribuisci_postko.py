#!/usr/bin/env python3
"""Read and execute the exact post-KO caller composition with explicit query models."""
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import sys
from types import SimpleNamespace

path=Path(__file__).with_name('attribuisci_scalare.py')
spec=importlib.util.spec_from_file_location('postko_scalar',path)
S=importlib.util.module_from_spec(spec);spec.loader.exec_module(S)
from sgp131 import ai_scoring as A
from sgp131 import test_ai_scoring_rom as B
from unicorn import UC_HOOK_CODE,UC_HOOK_MEM_READ,UC_HOOK_MEM_WRITE
from unicorn.arm_const import (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3,
    UC_ARM_REG_R4,UC_ARM_REG_R5,UC_ARM_REG_R6,UC_ARM_REG_R7,UC_ARM_REG_R8,UC_ARM_REG_R9,
    UC_ARM_REG_R10,UC_ARM_REG_R11,UC_ARM_REG_SP,UC_ARM_REG_LR,UC_ARM_REG_PC,UC_ARM_REG_CPSR)

FUNCTION,END=A.FUNCTION_START,A.FUNCTION_END
CURRENT_SHA='d2cfa7a4d31541559846b971bce5ad0547b0118cf12544d7ca52cdfe617369c2'
MASK,MASK_END=0x020726C0,0x020726E0
MASK_SHA='da266f8eefce9cbb52a195196c3e0897cbc84b5af29871c7bd834fa3e8992a78'
MONDATA,MONDATA_SIZE=0x0206E540,120
MONDATA_SHA='7d88f5974d9ca615e5602e1e9b89a594f6fc8e78d4c36cf5660f7cc9f12f02b0'
SAVED=(UC_ARM_REG_R4,UC_ARM_REG_R5,UC_ARM_REG_R6,UC_ARM_REG_R7,
       UC_ARM_REG_R8,UC_ARM_REG_R9,UC_ARM_REG_R10,UC_ARM_REG_R11)
COOKIES=[0x44440000+i for i in range(8)]
need,sha=S.need,S.sha


def memory_piece(segments,address,size):
    pieces=[bytes(data[address-start:address-start+size]) for start,data in segments
            if start<=address and address+size<=start+len(data)]
    need(len(pieces)==1,'native segment ownership');return pieces[0]


def require_narrow_scratch(result):
    need(all(stored==score&255 for (_,score,_),stored in zip(result['compares'],result['stored'])),
         'stage-two scratch must retain the low byte')


def mutant_overlay(image,kind):
    result=bytearray(image)
    need(sha(result[FUNCTION-A.OVERLAY_BASE:END-A.OVERLAY_BASE])==CURRENT_SHA,'counterproof current parent')
    for address,pre,post in A.PATCHES:
        at=address-A.OVERLAY_BASE
        need(result[at:at+len(post)]==post,'counterproof source site')
        result[at:at+len(pre)]=pre
    if kind=='wide_scratch':
        at=0x02258938-A.OVERLAY_BASE;result[at:at+4]=bytes.fromhex('c046c046')
    else:need(kind=='wrapping','unknown counterproof')
    return bytes(result)


class PostKOCPU(B.Native):
    """Reuse the V4 scenario/service models; qualify current code with stricter boundaries."""
    def __init__(self,segments,image,*,attested=True,execute_effectiveness=False,attested_flags=True):
        need(len(image)==A.OVERLAY_SIZE,'post-KO overlay geometry')
        parent=image[FUNCTION-A.OVERLAY_BASE:END-A.OVERLAY_BASE]
        if attested:need(sha(parent)==CURRENT_SHA,'exact current post-KO parent')
        need(sha(image[S.FUNCTION-A.OVERLAY_BASE:S.END-A.OVERLAY_BASE])==S.CURRENT_SHA,'current scalar dependency')
        need(sha(memory_piece(segments,S.BASE,148))==S.SHARED.F.PAYLOAD_SHA256,'current resident helper')
        need(sha(memory_piece(segments,S.DIV,524))==S.DIV_SHA,'current ARM division')
        need(sha(memory_piece(segments,MASK,32))==MASK_SHA,'current native mask')
        need(sha(image[S.SHARED.CHART-A.OVERLAY_BASE:S.SHARED.CHART-A.OVERLAY_BASE+336])==
             '41c4a8c8f45ae719ee04912c7ae3b6e5ae75a83ec9a270e7555bd6eefa4943da','current sparse chart')
        if execute_effectiveness and attested_flags:
            need(sha(image[S.SHARED.FUNCTION-A.OVERLAY_BASE:S.SHARED.FUNCTION_END-A.OVERLAY_BASE])==
                 '8959c8bc6e0b1d6fa93cfe4a02068bf2c6441781f73c4d52777dfc29b69d0128','current native flags dependency')
        # Adapter retains only ARM9 initialization segments, never a complete ROM.
        entries=[];raw=bytearray()
        for address,data in segments:entries.append((address,len(raw),len(data)));raw.extend(data)
        super().__init__(SimpleNamespace(raw=bytes(raw),segmenti=entries),image,
                         execute_effectiveness=execute_effectiveness)
        self.frozen=[(address,bytes(data)) for address,data in segments]+[(A.OVERLAY_BASE,bytes(image))]
        self.immutable_regions=[(a,a+len(b)) for a,b in self.frozen]
        self.code_seen={};self.read_seen=set();self.current=None;self.pending=None;self.pending_flags=None
        self.uc.hook_add(UC_HOOK_CODE,self._closure)
        self.uc.hook_add(UC_HOOK_MEM_WRITE,self._guest_write)
        self.uc.hook_add(UC_HOOK_MEM_READ,self._read)

    def _dispatch(self,name):
        if self.current is not None:
            self.current['modeled_calls'].append(dict(name=name,args=[self.reg(r) for r in
                (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3)]))
        if name=='GetMonData' and self.reg(UC_ARM_REG_R1)==0x0A:return 0
        return super()._dispatch(name)

    def put(self,address,value):
        need(B.STACK_TOP-4096<=address and address+4<=B.STACK_TOP,'modeled output outside stack')
        super().put(address,value)

    def _closure(self,u,address,size,unused):
        r=self.current
        if r is None:return
        r['instructions']+=1;need(r['instructions']<=100000,'post-KO instruction budget')
        sp=self.reg(UC_ARM_REG_SP);thumb=bool(self.reg(UC_ARM_REG_CPSR)&32)
        r['stack_depth']=max(r['stack_depth'],B.STACK_TOP-sp)
        if address==FUNCTION:
            for register,value in zip(SAVED,COOKIES):u.reg_write(register,value)
        if self.pending and address==self.pending['return_pc']:
            need(thumb and sp==self.pending['sp'] and [self.reg(x) for x in SAVED]==self.pending.pop('saved'),
                 'scalar nested return/ABI')
            self.pending['score']=self.reg(UC_ARM_REG_R0)
            need(0<=self.pending['score']<=160,'nested scalar score range')
            r['scalar_calls'].append(self.pending);self.pending=None
        if self.pending_flags and address==self.pending_flags['return_pc']:
            need(thumb and sp==self.pending_flags['sp'] and [self.reg(x) for x in SAVED]==self.pending_flags.pop('saved'),
                 'native flags nested return/ABI')
            self.pending_flags['flags']=struct.unpack('<I',u.mem_read(self.pending_flags['flag_pointer'],4))[0]
            r['flag_calls'].append(self.pending_flags);self.pending_flags=None
        if address in B.STUBS and not (self.execute_effectiveness and address==S.SHARED.FUNCTION):return
        self.code_seen[address]=(size,thumb)
        if S.DIV<=address<S.DIV_END:
            need(not thumb and size==4,'post-KO ARM division ISA');r['arm_instructions']+=1
            if address==S.DIV:
                need(self.reg(UC_ARM_REG_R1)==10 and self.reg(UC_ARM_REG_R0)<=1600,'post-KO division domain')
                r['math_entries']+=1
        else:
            need(thumb and size in (2,4),'post-KO Thumb ISA')
            need(FUNCTION<=address<END or S.FUNCTION<=address<0x02252692
                 or MASK<=address<MASK_END or S.BASE+60<=address<S.BASE+108
                 or S.BASE+118<=address<S.BASE+148
                 or (self.execute_effectiveness and
                     (S.SHARED.FUNCTION<=address<S.SHARED.FUNCTION+452
                      or S.BASE<=address<S.BASE+60)), 'unexpected post-KO code %#x'%address)
        if address==S.FUNCTION:
            need(self.pending is None,'overlapping scalar calls')
            values=[self.reg(v) for v in (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2)]
            need(all(v<18 for v in values),'nested scalar type domain')
            self.pending=dict(types=values,return_pc=self.reg(UC_ARM_REG_LR)&~1,sp=sp,saved=[self.reg(x) for x in SAVED])
            need(self.pending['return_pc'] in (0x02258924,0x02258934),'actual scalar caller return')
        if address==S.BASE+60:r['scalar_tail_entries']+=1
        if address==S.SHARED.FUNCTION:
            r['native_flags_entries']+=1
            need(self.pending_flags is None,'overlapping native flags calls')
            args=struct.unpack('<5I',u.mem_read(sp,20));pointer=args[4]
            need(B.STACK_TOP-4096<=pointer and pointer+4<=B.STACK_TOP and self.reg(UC_ARM_REG_R0)==B.CTX
                 and self.reg(UC_ARM_REG_R2)<18 and self.reg(UC_ARM_REG_R3)==0 and args[:2]==(0,0),'native flags modeled ABI/domain')
            self.pending_flags=dict(return_pc=self.reg(UC_ARM_REG_LR)&~1,sp=sp,saved=[self.reg(x) for x in SAVED],
                move=self.reg(UC_ARM_REG_R1),move_type=self.reg(UC_ARM_REG_R2),defender_types=list(args[2:4]),
                flag_pointer=pointer,initial_flags=struct.unpack('<I',u.mem_read(pointer,4))[0])
            need(self.pending_flags['return_pc']==0x02258A00,'actual flags caller return')
        if address==S.BASE:r['flags_helper_entries']+=1
        if address==MASK:
            need(self.reg(UC_ARM_REG_R0)<6,'native mask party domain');r['mask_entries']+=1
        if address==0x02252692:raise ValueError('scalar post-BL entry')

    def _guest_write(self,u,access,address,size,value,unused):
        need(B.STACK_TOP-4096<=address and address+size<=B.STACK_TOP,'post-KO nonstack guest write')
        self.current['guest_writes']['count']+=1;self.current['guest_writes']['bytes']+=size

    def _read(self,u,access,address,size,value,unused):
        if any(a<=address and address+size<=b for a,b in self.immutable_regions):
            self.read_seen.update(range(address,address+size))

    def observe(self,scenario,*,require_narrow=True):
        r=dict(instructions=0,arm_instructions=0,stack_depth=0,scalar_calls=[],scalar_tail_entries=0,
            math_entries=0,mask_entries=0,native_flags_entries=0,flags_helper_entries=0,modeled_calls=[],flag_calls=[],
            guest_writes=dict(count=0,bytes=0))
        self.current=r;self.pending=None;self.pending_flags=None;self.seed=0
        self.uc.mem_write(B.STACK_TOP-4104,b'\xA5'*8)
        try:self._start(FUNCTION,(B.BS,scenario.battler),scenario)
        finally:self.current=None
        need(self.reg(UC_ARM_REG_PC)==B.STOP and self.reg(UC_ARM_REG_SP)==B.STACK_TOP
             and self.reg(UC_ARM_REG_CPSR)&32 and [self.reg(v) for v in SAVED]==COOKIES,'post-KO return/ABI')
        need(self.pending is None and self.pending_flags is None,'unfinished scalar/flags call')
        need(bytes(self.uc.mem_read(B.CTX,0x4000))==self.before,'post-KO changed context')
        need(bytes(self.uc.mem_read(B.STACK_TOP,256))==B.CANARY and
             bytes(self.uc.mem_read(B.STACK_TOP-4104,8))==b'\xA5'*8,'post-KO stack canaries')
        need(all(bytes(self.uc.mem_read(a,len(b)))==b for a,b in self.frozen),'post-KO changed loaded code/data')
        need(all(carry==(best>=score) for best,score,carry in self.compares),'post-KO compare carry')
        r.update(choice=self.reg(UC_ARM_REG_R0),compares=list(self.compares),stored=list(self.stored),
                 rng_model_seed=self.seed,query_log=list(self.log))
        need(len(r['compares'])==len(r['stored']),'post-KO comparison observations')
        if require_narrow:require_narrow_scratch(r)
        return r

    def closure(self):
        def ranges(addresses):
            rows=[]
            for a in sorted(addresses):
                if rows and rows[-1][1]==a:rows[-1][1]+=1
                else:rows.append([a,a+1])
            return [dict(ram=hex(a),bytes=b-a,sha256=sha(bytes(self.uc.mem_read(a,b-a)))) for a,b in rows]
        code=set()
        for a,(size,thumb) in self.code_seen.items():code.update(range(a,a+size))
        return dict(executed_ranges=ranges(code),immutable_read_ranges=ranges(self.read_seen),
                    models={hex(k):v for k,v in B.STUBS.items() if not(self.execute_effectiveness and k==S.SHARED.FUNCTION)})


def overflow_scenario():
    return B.Scenario([B.Slot(1,(0,0),hp=0),B.Slot(0,(0,0)),
        B.Slot(464,(4,5),moves=B.full_moves(2)),B.Slot(0x1EE,(1,1)),
        B.Slot(68,(1,1),moves=B.full_moves(4)),B.Slot(0,(0,0))],target_types=(5,8),
        superefficient=set(B.full_moves(2))|set(B.full_moves(4)))


def regional_window(model,canonical):
    import capstone
    base=int(next(x['ram'] for x in model['record']['overlays'] if x['id']==12),16)
    start=FUNCTION-A.OVERLAY_BASE;window=model['overlay'][start:start+928];normalized=bytearray(window)
    calls=[];md=capstone.Cs(capstone.CS_ARCH_ARM,capstone.CS_MODE_THUMB)
    for instruction in md.disasm(canonical,FUNCTION):
        if instruction.mnemonic!='bl':continue
        target=int(instruction.op_str.lstrip('#'),16)
        if target not in (MONDATA,MASK):continue
        offset=instruction.address-FUNCTION;actual=S.SHARED.branch(window[offset:offset+4],base+start+offset,'bl')
        need(actual==target,'regional post-KO external call target')
        normalized[offset:offset+4]=canonical[offset:offset+4]
        calls.append(dict(offset=offset,target=hex(target)))
    need(len(calls)==12,'regional external call coverage')
    for address,size,digest in ((MONDATA,MONDATA_SIZE,MONDATA_SHA),(MASK,32,MASK_SHA)):
        need(sha(memory_piece(model['segments'],address,size))==digest,'regional external body correspondence')
    need(bytes(normalized)==canonical,'retail post-KO bounded relocation correspondence')
    return dict(function_ram=hex(base+start),bytes=928,raw_sha256=sha(window),
        comparison_only_call_fields=calls,executed_bytes_modified=False,
        get_mon_data_bounded_bytes=120,get_mon_data_sha256=MONDATA_SHA,mask_bytes=32,mask_sha256=MASK_SHA)


def scenarios():
    import copy
    rows=[('overflow_180_320',overflow_scenario(),4)]
    neutral=overflow_scenario();neutral.target_types=(0,0)
    rows.append(('ordinary_nooverflow',neutral,4))
    tie=B.both_320();tie.no_score=set();tie.superefficient=set(B.full_moves(2))|set(B.full_moves(4))
    rows.append(('tie_320_first',tie,2));rows.append(('stale_64_fallback',B.both_320(),4))
    order=overflow_scenario();order.superefficient=set();order.no_score={B.full_moves(2)[0]}
    order.damage={m:100 for m in B.full_moves(4)}|{m:90 for m in B.full_moves(2)}
    rows.append(('elimination_order',order,2))
    fallback=overflow_scenario();fallback.superefficient=set(B.full_moves(2))
    rows.append(('high_without_effective_move',fallback,2))
    for battle_type in (0,8,16,24):
        barred=B.Scenario([B.Slot(1,(1,1),hp=0),B.Slot(0x1EE,(1,1)),B.Slot(0,(1,1)),
            B.Slot(25,(1,1),moves=B.full_moves(3)),B.Slot(26,(1,1),moves=B.full_moves(4)),
            B.Slot(27,(0,0),moves=B.full_moves(5))],target_types=(5,8),battle_type=battle_type,
            partner=3,current={1:3,3:6},pending={1:4,3:6},superefficient=set(B.full_moves(5)))
        rows.append(('exclusions_shape_%d'%battle_type,barred,5))
    rows.extend([('empty',B.Scenario([]),6),('one_current',B.Scenario([B.Slot(1,(0,0))]),6),
        ('one_reserve',B.Scenario([B.Slot(1,(0,0),hp=0),B.Slot(25,(1,1),moves=B.full_moves(1))],
            superefficient=set(B.full_moves(1))),1)])
    return rows


def native_flags_scenarios():
    return [('fairy_flags_connected',B.Scenario([B.Slot(1,(0,0),hp=0),
        B.Slot(25,(9,9),moves=(5,0,0,0))],target_types=(16,16),move_type={5:9}),1),
        ('immune_move_then_ice',B.Scenario([B.Slot(1,(0,0),hp=0),
        B.Slot(25,(16,15),moves=(5,6,0,0)),B.Slot(26,(10,10),moves=(9,0,0,0))],
        target_types=(9,16),move_type={5:16,6:15,9:10}),1)]


def require_native_flags_case(name,result):
    expected={'fairy_flags_connected':[(9,2)],'immune_move_then_ice':[(16,8),(15,2)]}[name]
    need([(call['move_type'],call['flags']) for call in result['flag_calls']]==expected,
         'native flags sequence/output '+name)
    need(result['native_flags_entries']==len(expected) and result['flags_helper_entries']==len(expected),
         'native flags exact entry count')


def analyze(rom,v4,base,retail,language,build=None):
    import gc
    reused=S.verify_reused_build(build) if build is not None else dict(local_compilation_performed=False,
        reused_build_verified=False,reason='readback only; own-build receipt not verified in this run')
    models={name:S.SHARED.read_image(path,language,name) for name,path in
        (('retail',retail),('base11',base),('v4',v4),('r4',rom))}
    old,current=models['v4'],models['r4'];start=FUNCTION-A.OVERLAY_BASE
    old_window=old['overlay'][start:start+928];need(sha(old_window)==A.FUNCTION_SHA256,'source post-KO preimage')
    expected=bytearray(old_window)
    for address,pre,post in A.PATCHES:
        at=address-FUNCTION;need(expected[at:at+len(pre)]==pre,'source patch site');expected[at:at+len(post)]=post
    need(bytes(expected)==current['overlay'][start:start+928] and sha(expected)==CURRENT_SHA,'complete post-KO reconstruction')
    regional=[]
    for name in ('retail','base11','v4'):regional.append(dict(input=name,**regional_window(models[name],old_window)))
    for site in (0x02258920,0x02258930):
        need(S.SHARED.branch(current['overlay'][site-A.OVERLAY_BASE:site-A.OVERLAY_BASE+4],site,'bl')==S.FUNCTION,'current scalar call')
    callers=[]
    for owner,base_address,site in ((10,0x0221BE20,0x022205FE),(12,A.OVERLAY_BASE,0x0225F8E8)):
        data=current['overlays'][owner][site-base_address:site-base_address+4]
        need(S.SHARED.branch(data,site,'bl')==FUNCTION,'current upstream post-KO caller')
        callers.append(dict(overlay=owner,ram=hex(site),target=hex(FUNCTION),sha256=sha(data)))
    cpu=PostKOCPU(current['segments'],current['overlay']);runs=[]
    for name,scenario,choice in scenarios():
        result=cpu.observe(scenario);need(result['choice']==choice,'post-KO literal choice '+name)
        need(sum(call['name']=='GetRandomOpposingBattlerId' for call in result['modeled_calls'])==1,'one modeled RNG selection')
        runs.append(dict(name=name,result=result))
    baseline=next(z['result'] for z in runs if z['name']=='ordinary_nooverflow')
    closure=cpu.closure();del cpu;gc.collect()
    cpu=PostKOCPU(current['segments'],current['overlay'],execute_effectiveness=True);connected=[]
    for name,scenario,choice in native_flags_scenarios():
        result=cpu.observe(scenario);need(result['choice']==choice and result['native_flags_entries']>0
            and result['flags_helper_entries']==result['native_flags_entries'],'native flags caller connection '+name)
        require_native_flags_case(name,result)
        connected.append(dict(name=name,result=result))
    connected_closure=cpu.closure();del cpu;gc.collect()
    cpu=PostKOCPU(current['segments'],mutant_overlay(current['overlay'],'wrapping'),attested=False)
    wrapping=cpu.observe(overflow_scenario());need(wrapping['choice']==2 and [c[1] for c in wrapping['compares']]==[180,64],'wrapping counterproof')
    ordinary=cpu.observe(next(s for n,s,c in scenarios() if n=='ordinary_nooverflow'))
    need(all(ordinary[k]==baseline[k] for k in ('choice','compares','stored','query_log','rng_model_seed')),'ordinary differential preserves transport/order/model RNG')
    del cpu;gc.collect()
    cpu=PostKOCPU(current['segments'],mutant_overlay(current['overlay'],'wide_scratch'),attested=False)
    wide=cpu.observe(B.both_320(),require_narrow=False)
    need(wide['choice']==2 and wide['stored']==[320,320,320],'superseded wide scratch counterproof')
    try:require_narrow_scratch(wide)
    except ValueError:pass
    else:raise ValueError('wide scratch false success')
    del cpu;gc.collect()
    mutant=bytearray(current['overlay']);mask_at=0x02252202-A.OVERLAY_BASE
    need(mutant[mask_at]==12,'old-mask semantic counterproof preimage');mutant[mask_at]=4
    cpu=PostKOCPU(current['segments'],bytes(mutant),execute_effectiveness=True,attested_flags=False)
    oldmask=cpu.observe(native_flags_scenarios()[1][1])
    need(oldmask['choice']==1 and [(q['move_type'],q['flags']) for q in oldmask['flag_calls']]==[(16,10)],
         'old mask reproduces same-choice false success')
    try:require_native_flags_case('immune_move_then_ice',oldmask)
    except ValueError:pass
    else:raise ValueError('same-choice old-mask false success')
    del cpu;gc.collect()
    return dict(schema='postko-source-rom-v1',language=language,reused_build=reused,
        inputs=[model['record'] for model in models.values()],regional_windows=regional,
        parent_sha256=CURRENT_SHA,parent_ram=hex(FUNCTION),parent_bytes=928,
        source_sites=[dict(ram=hex(a),declared_bytes=len(pre)) for a,pre,post in A.PATCHES],
        changed_ram=[hex(FUNCTION+i) for i,(a,b) in enumerate(zip(old_window,expected)) if a!=b],
        callers=callers,scalar_call_sites=['0x02258920','0x02258930'],
        runs=runs,native_flags_runs=connected,closures=dict(default=closure,native_flags=connected_closure),
        counters=dict(wrapping=wrapping,ordinary_differential=ordinary,superseded_wide_scratch=wide,old_flags_mask_same_choice=oldmask),
        coverage=dict(current_modeled_flags=len(runs),current_native_flags=len(connected),counter_invocations=4),
        source_sha256={str(p.relative_to(S.SOURCE)):sha(p.read_bytes()) for p in
            (Path(__file__),Path(B.__file__),Path(A.__file__),path)},
        limits=['query/party/mon/damage and RNG selector remain declared models',
                'two native flags scenes; no exhaustive context/abilities/items/move coverage',
                'fixed synthetic decisions, no random campaign repeat or natural battle',
                'native source toolchain not reconstructed; no frame/SAVE/cold/device qualification'])


def main():
    import argparse
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('rom','v4','base','retail','json'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--language',choices=('EN','IT'),required=True)
    p.add_argument('--build',type=Path,help='reuse canonical Fairy own-project object and receipt; never compile')
    p.add_argument('--readback-only',action='store_true');args=p.parse_args()
    if (args.build is None)==(not args.readback_only):p.error('choose exactly one of --build DIR or --readback-only')
    protected=[args.rom,args.v4,args.base,args.retail]
    if args.build is not None:protected.extend(args.build/n for n in ('fairy-native.o','native.bin','compile-retained.json'))
    for file in protected:
        if args.json.resolve()==file.resolve() or (args.json.exists() and file.exists() and args.json.samefile(file)):
            p.error('--json must not replace inputs or build artifacts')
    result=analyze(args.rom,args.v4,args.base,args.retail,args.language,args.build)
    args.json.parent.mkdir(parents=True,exist_ok=True);args.json.write_text(json.dumps(result,indent=2)+'\n')
    print(args.language,'post-KO:',len(result['runs']),'default +',len(result['native_flags_runs']),
          'native-flags scenes +4 counter/differential invocations PASS; no compilation')


if __name__=='__main__':main()
