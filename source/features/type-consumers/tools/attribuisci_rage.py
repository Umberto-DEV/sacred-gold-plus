#!/usr/bin/env python3
"""Attribute the Rage bit clear and execute its controller with native leaf calls."""
import importlib.util
import json
from pathlib import Path
import struct

spec=importlib.util.spec_from_file_location('rage_shared',Path(__file__).with_name('attribuisci.py'))
G=importlib.util.module_from_spec(spec);spec.loader.exec_module(G)
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_THUMB,UC_HOOK_CODE,UC_HOOK_MEM_READ,UC_HOOK_MEM_WRITE
from unicorn.arm_const import (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3,
    UC_ARM_REG_SP,UC_ARM_REG_LR,UC_ARM_REG_PC,UC_ARM_REG_CPSR)
need,sha=G.need,G.sha
ENTRY,END,SITE=0x0224930C,0x02249460,0x022493FC
CURRENT_SHA='b4c1fc5c7df7d0f3f0afdf2c9b7561d41c96c3d7974082108fabfc5930429be4'
SELECTED,SELECTED_END=0x022522F0,0x02252324
SELECTED_SHA='4fbf93c10a2686cd89db8d477ce416164fb974940ee4ca6ca1de256c5bc86eca'
MAX=0x0223A7F0
MAX_SHA='2640d5fd1ca49974c06fbe29394309f3a9b27280ff43b5c43bf5c93a93e4b1f7'
CTX,BS,STACK,STOP=0x02380000,0x02370000,0x023B8000,0x023F0000
RAGE=1<<23


def take(image,address,size):return bytes(image[address-G.T.OVERLAY_BASE:address-G.T.OVERLAY_BASE+size])


def counter_image(image,variant):
    result=bytearray(image);need(sha(take(result,ENTRY,340))==CURRENT_SHA,'current Rage counter preimage')
    if variant=='old':address,value=SITE,G.T.RAGE_PREIMAGE
    elif variant=='wrong_mask':address,value=SITE-4,bytes.fromhex('0120')
    else:raise ValueError('explicit Rage counter variant')
    result[address-G.T.OVERLAY_BASE:address-G.T.OVERLAY_BASE+2]=value
    return bytes(result)


def require_statuses(result,expected):
    need(result['statuses']==list(expected),'Rage status2 preservation oracle')


class RageCPU:
    """Full BeforeTurn body, starting in state1, with all reached callees native.

    Construction requires authenticated code windows; the CLI additionally pins
    whole inputs. Controlled battle/action words are explicit synthetic inputs.
    No selected-move, max-battler or random Python service replaces guest code.
    """
    def __init__(self,segments,image,*,variant='current'):
        body=bytearray(take(image,ENTRY,340));off=SITE-ENTRY
        if variant=='old':
            need(body[off:off+2]==G.T.RAGE_PREIMAGE,'old Rage AND fixture');body[off:off+2]=G.T.RAGE_REPLACEMENT
        elif variant=='wrong_mask':
            need(body[off-4:off-2]==bytes.fromhex('0120'),'wrong Rage mask fixture');body[off-4:off-2]=bytes.fromhex('0220')
        else:need(variant=='current','explicit Rage variant required')
        need(sha(body)==CURRENT_SHA,'current/counter Rage controller identity')
        for address,size,digest in ((SELECTED,52,SELECTED_SHA),(MAX,4,MAX_SHA),(G.RNG,44,G.RNG_SHA)):
            need(sha(take(image,address,size))==digest,'native Rage leaf identity '+hex(address))
        self.uc=u=Uc(UC_ARCH_ARM,UC_MODE_THUMB)
        for address,size in ((0x02000000,0x400000),(0x01FF8000,0x8000),(0x027E0000,0x20000)):u.mem_map(address,size)
        self.frozen=[(a,bytes(b)) for a,b in segments]+[(G.T.OVERLAY_BASE,bytes(image))]
        for address,data in self.frozen:u.mem_write(address,data)
        self.variant=variant;self.current=None;self.code_seen={};self.pending=None
        u.hook_add(UC_HOOK_CODE,self._code);u.hook_add(UC_HOOK_MEM_READ,self._read);u.hook_add(UC_HOOK_MEM_WRITE,self._write)

    def reg(self,r):return self.uc.reg_read(r)
    def word(self,a):return int.from_bytes(self.uc.mem_read(a,4),'little')

    def _code(self,u,address,size,unused):
        r=self.current
        if r is None:return
        r['instructions']+=1;need(r['instructions']<=10000,'Rage instruction budget')
        sp=self.reg(UC_ARM_REG_SP)
        need(bool(self.reg(UC_ARM_REG_CPSR)&32) and size in (2,4),'Rage Thumb ISA')
        allowed=(ENTRY<=address and address+size<=0x0224944C and
                 all(address+size<=lo or address>=hi for lo,hi in ((0x02249332,0x0224933A),(0x0224933A,0x022493D4))))
        allowed|=SELECTED<=address and address+size<=SELECTED+44
        allowed|=MAX<=address and address+size<=MAX+4
        allowed|=G.RNG<=address and address+size<=0x0223BDB6
        need(allowed,'unexpected Rage code or literal/jump-table PC '+hex(address))
        self.code_seen[address]=(size,True);r['stack_depth']=max(r['stack_depth'],STACK-sp)
        if self.pending and address==self.pending['return_pc']:
            call=self.pending
            need(sp==call['sp'] and [self.reg(x) for x in G.SAVED]==call.pop('saved'),'Rage leaf return ABI')
            call['value']=self.reg(UC_ARM_REG_R0)
            if call['name']=='selected':
                call['move']=call['value'];need(call['move']==r['effective_moves'][call['battler']],'native selected move result')
                r['selected_calls'].append(call)
            elif call['name']=='rng':
                call['after']=self.word(BS+G.SEED_OFFSET)
                need(call['after']==G.next_seed(call['before']) and call['value']==call['after']>>16,'native Rage RNG transition')
                r['rng_calls'].append(call)
            else:need(call['value']==r['battlers'],'native maximum battlers result')
            r['leaf_calls'].append(call);self.pending=None
        if address in (MAX,SELECTED,G.RNG):
            name={MAX:'max',SELECTED:'selected',G.RNG:'rng'}[address]
            need(self.pending is None,'nested unexpected Rage leaf')
            call=dict(name=name,return_pc=self.reg(UC_ARM_REG_LR)&~1,sp=sp,saved=[self.reg(x) for x in G.SAVED])
            if name=='selected':
                battler=self.reg(UC_ARM_REG_R1)
                need(self.reg(UC_ARM_REG_R0)==CTX and 0<=battler<r['battlers'] and call['return_pc']==0x022493F0,'native selected-move call ABI')
                call['battler']=battler
            else:
                need(self.reg(UC_ARM_REG_R0)==BS and call['return_pc']==(0x0224931C if name=='max' else 0x0224941C),'native max/RNG call ABI')
                if name=='rng':call['before']=self.word(BS+G.SEED_OFFSET)
            self.pending=call
        if address==SITE:
            need(self.reg(UC_ARM_REG_R0)==(RAGE if self.variant!='wrong_mask' else RAGE>>1),'actual Rage bit mask')
            r['bit_operations'].append(dict(mask=self.reg(UC_ARM_REG_R0),before=self.reg(UC_ARM_REG_R1)))
        if address==SITE+2:r['bit_operations'][-1]['after']=self.reg(UC_ARM_REG_R1)

    def _read(self,u,access,address,size,value,unused):
        if self.current is None:return
        if size==4 and any(address==CTX+0x2DB0+0xC0*i for i in range(4)):
            self.current['status_reads'].append(dict(pc=hex(self.reg(UC_ARM_REG_PC)),ram=hex(address),value=self.word(address)))

    def _write(self,u,access,address,size,value,unused):
        r=self.current
        if r is None:return
        stack=STACK-4096<=address and address+size<=STACK
        status=size==4 and any(address==CTX+0x2DB0+0xC0*i for i in range(r['battlers']))
        tail=(address in (CTX+8,CTX+0x28) and size==4) or (CTX+0x310C<=address and address+size<=CTX+0x3114 and size==2)
        rng=address==BS+G.SEED_OFFSET and size==4
        need(stack or status or tail or rng,'Rage write outside declared state '+hex(address))
        if status:
            need(self.reg(UC_ARM_REG_PC)==0x02249400,'actual Rage store instruction')
            r['status_writes'].append(dict(pc=hex(self.reg(UC_ARM_REG_PC)),ram=hex(address),value=value))
        r['write_count']+=1

    def observe(self,statuses,moves,*,positions=None,selections=None,seed=0):
        n=len(statuses);positions=tuple(positions or (1,)*n);selections=tuple(selections or (1,)*n)
        need(1<=n<=4 and len(moves)==len(positions)==len(selections)==n,'Rage battler geometry')
        need(all(type(s) is int and 0<=s<=0xFFFFFFFF for s in statuses),'Rage unsigned status word')
        need(all(type(v) is int and 0<=v<=0xFFFF for v in moves) and all(type(v) is int and 0<=v<=4 for v in positions),'Rage move/position domain')
        need(all(type(v) is int and 0<=v<=4 for v in selections) and type(seed) is int and 0<=seed<=0xFFFFFFFF,'Rage selection/seed domain')
        u=self.uc;u.mem_write(CTX,bytes(0x4000));u.mem_write(BS,bytes(0x3000));u.mem_write(STACK-4104,b'\xA5'*8+bytes(4096)+b'\xA5'*256)
        def put(a,v):u.mem_write(a,struct.pack('<I',v))
        put(CTX+0x28,1);put(BS+0x44,n);put(BS+G.SEED_OFFSET,seed)
        all_status=list(statuses)+[RAGE|(1<<21)]*(4-n)
        for i,status in enumerate(all_status):put(CTX+0x2DB0+0xC0*i,status)
        for i,(move,pos,selection) in enumerate(zip(moves,positions,selections)):
            put(CTX+0x21B0+16*i,pos);put(CTX+0x21B4+16*i,selection)
            if pos:u.mem_write(CTX+0x2D4A+0xC0*i+2*pos,struct.pack('<H',move))
        before=bytes(u.mem_read(CTX,0x4000));bs_before=bytes(u.mem_read(BS,0x3000))
        effective=[move if pos and selection==1 else 0 for move,pos,selection in zip(moves,positions,selections)]
        r=dict(variant=self.variant,battlers=n,before=list(statuses),moves=list(moves),positions=list(positions),selections=list(selections),effective_moves=effective,
            seed_before=seed,instructions=0,stack_depth=0,leaf_calls=[],selected_calls=[],rng_calls=[],bit_operations=[],status_reads=[],status_writes=[],write_count=0)
        for reg,value in zip(G.SAVED,G.COOKIES):u.reg_write(reg,value)
        for reg,value in zip((UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3),(BS,CTX,0,0)):u.reg_write(reg,value)
        u.reg_write(UC_ARM_REG_SP,STACK);u.reg_write(UC_ARM_REG_LR,STOP|1);self.current=r;self.pending=None
        try:u.emu_start(ENTRY|1,STOP,count=10001)
        finally:self.current=None
        need(self.reg(UC_ARM_REG_PC)==STOP and self.reg(UC_ARM_REG_SP)==STACK and self.reg(UC_ARM_REG_CPSR)&32 and [self.reg(x) for x in G.SAVED]==G.COOKIES,'Rage parent return ABI')
        need(self.pending is None,'unfinished native Rage call')
        after=bytes(u.mem_read(CTX,0x4000));bs_after=bytes(u.mem_read(BS,0x3000))
        allowed=set(range(8,12))|set(range(0x28,0x2C))|set(range(0x310C,0x3114))
        for i in range(n):allowed.update(range(0x2DB0+0xC0*i,0x2DB4+0xC0*i))
        changed=[i for i,(a,b) in enumerate(zip(before,after)) if a!=b]
        need(set(changed)<=allowed,'Rage changed other context/action/inactive battler')
        need(all(a==b for i,(a,b) in enumerate(zip(bs_before,bs_after)) if not G.SEED_OFFSET<=i<G.SEED_OFFSET+4),'Rage changed BattleSystem outside RNG')
        need(bytes(u.mem_read(STACK-4104,8))==b'\xA5'*8 and bytes(u.mem_read(STACK,256))==b'\xA5'*256,'Rage stack/caller canaries')
        need(all(bytes(u.mem_read(a,len(b)))==b for a,b in self.frozen),'Rage changed initialized code/data')
        expected_selected=[i for i,s in enumerate(statuses) if s&RAGE]
        need([c['battler'] for c in r['selected_calls']]==expected_selected,'Rage selected-move call count/order')
        need([c['name'] for c in r['leaf_calls']]==['max']+['selected']*len(expected_selected)+['rng']*4,'Rage actual leaf sequence')
        state=seed;randoms=[]
        for call in r['rng_calls']:
            need(call['before']==state,'Rage RNG chain');state=G.next_seed(state);randoms.append(state>>16)
        r.update(statuses=[self.word(CTX+0x2DB0+0xC0*i) for i in range(n)],seed_after=self.word(BS+G.SEED_OFFSET),
                 quick_claw_rng=list(struct.unpack('<4H',u.mem_read(CTX+0x310C,8))),context_changed_offsets=changed,
                 command=self.word(CTX+8),state=self.word(CTX+0x28))
        need(r['quick_claw_rng']==randoms and r['seed_after']==state and (r['command'],r['state'])==(8,0),'Rage native controller tail')
        return r


def window(model,role):
    base=int(model['record']['overlays'][1]['ram'],16);address=base+ENTRY-G.T.OVERLAY_BASE
    raw=take(model['overlay'],ENTRY,340);normalized=bytearray(raw);fields=[]
    if role=='retail' and model['record']['language']=='IT':
        need(sha(raw)=='9a8f7305065f91a46e40b7fd1f425b59b3749b5e82d7ec232e3d4015401c90ba','retail IT Rage window')
        need(G.S.SHARED.branch(raw[0x40:0x44],address+0x40,'bl')==0x020726C0,'retail IT ARM9 mask call')
        need(sha(G.piece(model['segments'],0x020726C0,32))=='da266f8eefce9cbb52a195196c3e0897cbc84b5af29871c7bd834fa3e8992a78','retail IT ARM9 mask identity')
        from sgp12.rom import bl_thumb
        normalized[0x40:0x44]=bl_thumb(ENTRY+0x40,0x020726C0);fields=[dict(offset='0x40',bytes=4,target='0x020726c0')]
    need(sha(normalized)==(CURRENT_SHA if role=='r4' else G.T.RAGE_FUNCTION_SHA256),'entire Rage normalized identity')
    need(struct.unpack_from('<5I',raw,320)==(0x21E8,0x3108,0x2DAC,0x2DB0,0x310C),'Rage literal pool')
    need(struct.unpack_from('<4H',raw,38)==(6,160,222,252),'Rage state jump table')
    aliases=[]
    for instruction_offset,pool_offset,value in ((0xD0,0x14C,0x2DB0),(0xE8,0x14C,0x2DB0),(0xF2,0x14C,0x2DB0)):
        opcode=struct.unpack_from('<H',raw,instruction_offset)[0]
        target=((address+instruction_offset+4)&~3)+(opcode&255)*4
        need(opcode&0xF800==0x4800 and target==address+pool_offset and struct.unpack_from('<I',raw,pool_offset)[0]==value,'Rage PC-relative status alias')
        aliases.append(dict(instruction_ram=hex(address+instruction_offset),literal_ram=hex(target),context_offset=hex(value)))
    return dict(function_ram=hex(address),bytes=340,code_extent_bytes=320,jump_table_bytes=8,literal_bytes=20,
        raw_sha256=sha(raw),normalized_sha256=sha(normalized),comparison_only_fields=fields,status_aliases=aliases,executed_bytes_modified=False)


def analyze(rom,v4,base,retail,language):
    models={name:G.S.SHARED.read_image(path,language,name) for name,path in (('retail',retail),('base11',base),('v4',v4),('r4',rom))}
    windows=[dict(input=name,**window(m,name)) for name,m in models.items()]
    current=models['r4'];before=take(models['v4']['overlay'],ENTRY,340);expected=bytearray(before);offset=SITE-ENTRY
    need(expected[offset:offset+2]==G.T.RAGE_PREIMAGE,'source Rage preimage');expected[offset:offset+2]=G.T.RAGE_REPLACEMENT
    need(bytes(expected)==take(current['overlay'],ENTRY,340),'whole Rage controller source reconstruction')
    payload=take(current['overlay'],G.T.CONVERSION_SITE,G.T.CONVERSION_BYTES)
    replay,receipt=G.T.patch_overlay(models['v4']['overlay'],payload)
    need(take(replay,ENTRY,340)==bytes(expected) and receipt['rage_status2']['address']==SITE,'actual shared type-consumer source recipe')
    for role,model in models.items():
        for addr,size,digest in ((SELECTED,52,SELECTED_SHA),(MAX,4,MAX_SHA),(G.RNG,44,G.RNG_SHA)):
            need(sha(take(model['overlay'],addr,size))==digest,'incremental native Rage leaf identity '+role)
    need(take(current['overlay'],0x0226CAAC,4)==struct.pack('<I',ENTRY|1),'actual controller dispatch pointer')
    cpu=RageCPU(current['segments'],current['overlay']);runs=[]
    cases=[('bit_'+str(i),(RAGE|(1<<i),),(33,),dict(positions=(1+i%4,),seed=i)) for i in range(32)]
    cases += [('all_bits',(0xFFFFFFFF,),(33,),{}),('rage_selected',(RAGE|(1<<21),),(99,),{}),
              ('rage_absent',(0xFF7FFFFF,),(33,),{}),('zero_position',(RAGE|(1<<21),),(99,),dict(positions=(0,))),
              ('non_fight',(RAGE|(1<<21),),(99,),dict(selections=(2,))),
              ('two_battlers',(RAGE|(1<<21),0xFFFFFFFF),(33,99),dict(positions=(4,1),seed=0x12345678)),
              ('three_battlers',(RAGE,RAGE|(1<<31),0xFF7FFFFF),(99,33,33),dict(positions=(2,3,4))),
              ('mixed_four',(RAGE|(1<<21),RAGE|0x80000001,1<<21,0xFFFFFFFF),(33,99,33,33),dict(positions=(1,2,3,4),seed=0xFFFFFFFF))]
    for name,statuses,moves,options in cases:
        result=cpu.observe(statuses,moves,**options)
        required=[s&~RAGE if s&RAGE and move!=99 else s for s,move in zip(statuses,result['effective_moves'])]
        require_statuses(result,required);runs.append(dict(name=name,required_statuses=required,result=result))
    closure=dict(code=[dict(ram=hex(a),bytes=size,thumb=t) for a,(size,t) in sorted(cpu.code_seen.items())],models=[],max_stack_bytes=max(r['result']['stack_depth'] for r in runs))
    del cpu
    counters=[]
    for variant in ('old','wrong_mask'):
        cpu=RageCPU(current['segments'],counter_image(current['overlay'],variant),variant=variant)
        result=cpu.observe((0xFFFFFFFF,),(33,))
        try:require_statuses(result,(0xFF7FFFFF,))
        except ValueError:pass
        else:raise ValueError('false Rage semantic success')
        counters.append(dict(variant=variant,oracle_rejected=True,result=result));del cpu
    return dict(schema='rage-source-rom-v1',language=language,compilation_performed=False,inputs=[m['record'] for m in models.values()],windows=windows,
        source_recipe=dict(declared_bytes=2,changed_ram=[hex(SITE),hex(SITE+1)],current_sha256=CURRENT_SHA,
            shared_recipe_receipt=receipt['rage_status2'],conversion_payload_reused_sha256=sha(payload)),
        dispatch=dict(slot='0x0226caac',target='0x0224930d',kind='static pointer; dispatcher activation not exercised'),
        native_leaves=[dict(ram=hex(a),bytes=n,sha256=h) for a,n,h in ((MAX,4,MAX_SHA),(SELECTED,52,SELECTED_SHA),(G.RNG,44,G.RNG_SHA))],
        runs=runs,counterproofs=counters,closure=closure,coverage=dict(positive_entries=len(runs),counter_entries=2,service_models=0),
        source_sha256={str(p.relative_to(G.SOURCE)):sha(p.read_bytes()) for p in (Path(__file__),Path(G.__file__),Path(G.S.__file__),Path(G.S.SHARED.__file__),Path(G.T.__file__),G.SOURCE/'sgp131/fairy_ai.py',G.SOURCE/'sgp131/mechanics_stages.py')},
        limits=['synthetic state1 controller entry; Focus Punch/state0 and natural dispatcher/input are not executed',
                'all reached leaf functions native, but initialized battle/action words are fixtures',
                'bit operation algebra follows bound raw mask/load/store; finite full-controller entries are not all battle histories',
                'original native compiler unavailable; source two-byte recipe reconstructed, not native C recompilation',
                'Transform downstream, encrypted PartyMon, SAVE/cold, timing and physical device not qualified'])


def main():
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('rom','v4','base','retail','json'):parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--language',choices=('EN','IT'),required=True);args=parser.parse_args()
    for path in (args.rom,args.v4,args.base,args.retail):
        if args.json.resolve()==path.resolve() or (args.json.exists() and path.exists() and args.json.samefile(path)):
            parser.error('--json must not replace an input')
    result=analyze(args.rom,args.v4,args.base,args.retail,args.language)
    args.json.parent.mkdir(parents=True,exist_ok=True);args.json.write_text(json.dumps(result,indent=2)+'\n')
    print(args.language,'Rage:',len(result['runs']),'current +2 counter entries PASS; all reached leaves native')


if __name__=='__main__':main()
