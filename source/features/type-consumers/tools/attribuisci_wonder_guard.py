#!/usr/bin/env python3
"""Attribute the current Wonder Guard charge gate using actual move-cache data."""
import importlib.util
import json
import mmap
from pathlib import Path
import struct

spec=importlib.util.spec_from_file_location('wonder_grounding',Path(__file__).with_name('attribuisci_grounding.py'))
H=importlib.util.module_from_spec(spec);spec.loader.exec_module(H)
SOURCE=H.SOURCE
need,sha=H.need,H.sha
from unicorn.arm_const import (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3,
    UC_ARM_REG_SP,UC_ARM_REG_LR,UC_ARM_REG_PC,UC_ARM_REG_CPSR)
GATE,GATE_END=0x02258440,0x022584AC
GATE_SHA='acc3b85b54aba24a607d4130b98a5e2fe07caf235a3cb2b933173fe8734b6b9e'
OLD_GATE_SHA='1d833b36828c4421006a0e6ef5a3843420c62ae19c075823c4f45e1d91457a42'
FLAGS,FLAGS_END=0x02252054,0x02252218
FLAGS_SHA='8959c8bc6e0b1d6fa93cfe4a02068bf2c6441781f73c4d52777dfc29b69d0128'
CTX,STACK,STOP,FLAG=H.D.CTX,H.D.STACK,H.D.STOP,H.D.FLAG
MOVE_DATA,MOVE_COUNT=0x3DE,468
CHARGED=0x200
MOVE_CACHE_SHA='c64da77ab5f1158520a0f17905d457f3104c32aae1513c622cec0daa9f3e1588'


def read_moves(rom):
    """Reuse the independently qualified raw/ndspy NARC reader on a small mapped slice."""
    spec=importlib.util.spec_from_file_location('wonder_narc_reader',SOURCE/'features/borsa/tools/attribuisci.py')
    reader=importlib.util.module_from_spec(spec);spec.loader.exec_module(reader)
    with Path(rom).open('rb') as handle,mmap.mmap(handle.fileno(),0,access=mmap.ACCESS_READ) as raw:
        members,record=reader.raw_archive(raw,'a/0/1/1')
    need(record['file_id']==140 and record['archive_sha256']=='beed8ddf861e575b9c38dfa65a6c0c51fb237305ddd73c393f5e2009fbc75260',
         'current move archive identity')
    need(len(members)==471 and all(len(x)==16 for x in members),'move archive/cache geometry')
    owners={effect:[i for i,data in enumerate(members) if struct.unpack_from('<H',data)[0]==effect] for effect in (272,273)}
    need(owners=={272:[467],273:[424]},'actual effect ownership across all archive members')
    need((struct.unpack_from('<H',members[424])[0],members[424][3],members[424][4])==(273,65,10),'actual Fire Fang record')
    need((struct.unpack_from('<H',members[467])[0],members[467][3],members[467][4])==(272,120,7),'actual Shadow Force record')
    table=b''.join(members[:MOVE_COUNT]);record.update(cache_records=MOVE_COUNT,cache_bytes=len(table),cache_sha256=sha(table),
        effect_owners={str(k):v for k,v in owners.items()},
        selected_members={str(i):dict(sha256=sha(members[i]),effect=struct.unpack_from('<H',members[i])[0],power=members[i][3],type=members[i][4])
                          for i in (19,33,52,117,422,423,424,467)})
    return table,record


def counter_image(image,variant):
    result=bytearray(image);at=GATE-H.G.T.OVERLAY_BASE
    need(sha(result[at:at+108])==GATE_SHA,'current charge-gate counterproof preimage')
    if variant=='old':result[at+0x4C:at+0x4E]=H.G.T.FIRE_FANG_PREIMAGE
    elif variant=='shortcut':result[at+0x50:at+0x52]=bytes.fromhex('05e0')
    else:raise ValueError('unknown charge-gate counterproof')
    return bytes(result)


def expect_immune(result,expected):
    need(result['immune'] is expected,'Wonder Guard immunity differs')


class WonderCPU(H.GroundingCPU):
    """Current native consumers; reuse the qualified damage boundaries and five queries."""
    def __init__(self,segments,image,dense,moves,*,variant='current'):
        super().__init__(segments,image,dense)
        gate=bytearray(image[GATE-H.G.T.OVERLAY_BASE:GATE_END-H.G.T.OVERLAY_BASE])
        if variant=='old':
            need(gate[0x4C:0x4E]==H.G.T.FIRE_FANG_PREIMAGE and gate[0x50:0x52]==bytes.fromhex('05d1'),'old literal fixture')
            gate[0x4C:0x4E]=H.G.T.FIRE_FANG_REPLACEMENT
        elif variant=='shortcut':
            need(gate[0x4C:0x4E]==H.G.T.FIRE_FANG_REPLACEMENT and gate[0x50:0x52]==bytes.fromhex('05e0'),'shortcut fixture')
            gate[0x50:0x52]=bytes.fromhex('05d1')
        else:need(variant=='current','explicit charge-gate variant required')
        need(sha(gate)==GATE_SHA,'current/counter charge-gate identity')
        need(sha(image[FLAGS-H.G.T.OVERLAY_BASE:FLAGS_END-H.G.T.OVERLAY_BASE])==FLAGS_SHA,'current shared flags composition')
        need(sha(H.G.piece(segments,H.G.S.BASE,148))==H.G.S.SHARED.F.PAYLOAD_SHA256,'current flags resident helper')
        need(len(moves)==MOVE_COUNT*16 and sha(moves)==MOVE_CACHE_SHA,'actual battle-cache prefix identity')
        self.moves=bytes(moves);self.variant=variant;self.pending_gate=None;self.wonder=True

    def _dispatch(self,name):
        if name=='ability_if_not_ignored' and self.reg(UC_ARM_REG_R3)==25:
            need(self.reg(UC_ARM_REG_R0)==CTX and self.reg(UC_ARM_REG_R1)==0 and self.reg(UC_ARM_REG_R2)==1,'Wonder Guard query ABI')
            self.current['models'].append(dict(name=name,args=[self.reg(r) for r in (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3)]))
            return int(self.wonder)
        return super()._dispatch(name)

    def _code(self,u,address,size,unused):
        r=self.current
        if r is None:return
        sp=self.reg(UC_ARM_REG_SP);thumb=bool(self.reg(UC_ARM_REG_CPSR)&32)
        if self.pending_gate and address==self.pending_gate['return_pc']:
            need(thumb and sp==self.pending_gate['sp'] and [self.reg(v) for v in H.G.SAVED]==self.pending_gate.pop('saved'),'native charge-gate return ABI')
            value=self.reg(UC_ARM_REG_R0);need(value in (0,1,512),'actual noncanonical charge boolean')
            self.pending_gate['result']=value;r['gate_calls'].append(self.pending_gate);self.pending_gate=None
        if GATE<=address<GATE+98:
            r['instructions']+=1;need(r['instructions']<=100000,'Wonder instruction budget')
            need(thumb and size==2,'charge-gate Thumb ISA')
            r['stack_depth']=max(r['stack_depth'],STACK-sp);self.code_seen[address]=(size,thumb)
            if address==GATE:
                move=self.reg(UC_ARM_REG_R1)
                need(self.pending_gate is None and self.reg(UC_ARM_REG_R0)==CTX and move==r['move'],'actual charge-gate ABI')
                self.pending_gate=dict(move=move,effect=struct.unpack('<H',u.mem_read(CTX+MOVE_DATA+16*move,2))[0],
                    battle_status=self.word(CTX+0x213C),return_pc=self.reg(UC_ARM_REG_LR)&~1,sp=sp,
                    saved=[self.reg(v) for v in H.G.SAVED],reads=[])
                need(self.pending_gate['return_pc']==(0x02251F68 if r['mode']=='damage' else 0x0225214E),'actual charge-gate caller return')
            return
        if r['mode']=='damage':return super()._code(u,address,size,unused)
        r['instructions']+=1;need(r['instructions']<=100000,'Wonder flags instruction budget')
        r['stack_depth']=max(r['stack_depth'],STACK-sp)
        if address in self.STUBS and self.STUBS[address]!='damage_divide':return
        need(thumb and size in (2,4),'Wonder flags Thumb ISA')
        flags_code=(FLAGS<=address<FLAGS_END and all(address+size<=lo or address>=hi
                     for lo,hi in ((0x02252170,0x02252178),(0x022521C0,0x022521C8))))
        need(flags_code or H.G.S.BASE<=address<H.G.S.BASE+60
             or H.G.S.BASE+94<=address<H.G.S.BASE+108 or H.G.S.BASE+118<=address<H.G.S.BASE+148,'unexpected Wonder flags code %#x'%address)
        self.code_seen[address]=(size,thumb)
        if address==H.G.S.BASE:r['flags_helper_entries']+=1
        if address==0x022520C8:raise ValueError('entered retired BL suffix')
        if address==0x022521C8:
            need(self.reg(UC_ARM_REG_R0) in (0,5,20) and self.reg(UC_ARM_REG_R1)==FLAG,'actual flags combiner ABI')
            r['flags_apply_calls'].append(self.reg(UC_ARM_REG_R0))

    def _read(self,u,access,address,size,value,unused):
        super()._read(u,access,address,size,value,unused)
        if self.pending_gate and address in (CTX+MOVE_DATA+16*self.pending_gate['move'],CTX+0x213C):
            self.pending_gate['reads'].append(dict(ram=hex(address),bytes=size,value=int.from_bytes(u.mem_read(address,size),'little')))

    def _write(self,u,access,address,size,value,unused):
        if self.current['mode']=='damage':return super()._write(u,access,address,size,value,unused)
        allowed=STACK-4096<=address and address+size<=STACK
        allowed|=address in (STACK+4,STACK+8,STACK+12) and size==4
        allowed|=FLAG<=address and address+size<=FLAG+4
        need(allowed,'Wonder flags write outside stack/status')
        self.current['writes']['count']+=1;self.current['writes']['bytes']+=size

    def observe(self,mode,move,target,*,wonder=True,charged=False):
        need(mode in ('damage','flags') and type(move) is int and 0<=move<MOVE_COUNT
             and type(target) is int and 0<=target<18,'Wonder fixture domain')
        u=self.uc;self.wonder=bool(wonder);self.error=None
        effect=struct.unpack_from('<H',self.moves,16*move)[0];power=self.moves[16*move+3];kind=self.moves[16*move+4]
        self.scenario=H.D.DamageScenario(kind,target)
        u.mem_write(CTX,bytes(0x4000));u.mem_write(CTX+MOVE_DATA,self.moves)
        u.mem_write(CTX+0x213C,struct.pack('<I',CHARGED if charged else 0))
        u.mem_write(STACK-4104,b'\xA5'*8+bytes(4096)+b'\xA5'*256)
        if mode=='damage':
            u.mem_write(STACK,struct.pack('<4I',0,1,100,FLAG));args=(0x02370000,CTX,move,0);entry=H.PARENT
        else:
            u.mem_write(STACK,struct.pack('<5I',25 if wonder else 0,0,target,target,FLAG));args=(CTX,move,0,0);entry=FLAGS
        before=bytes(u.mem_read(CTX,0x4000));caller=bytes(u.mem_read(STACK,256))
        for register,value in zip(H.G.SAVED,H.G.COOKIES):u.reg_write(register,value)
        for register,value in zip((UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3),args):u.reg_write(register,value)
        u.reg_write(UC_ARM_REG_SP,STACK);u.reg_write(UC_ARM_REG_LR,STOP|1)
        r=dict(mode=mode,move=move,effect=effect,power=power,type=kind,target_type=target,wonder=wonder,charged=charged,
            variant=self.variant,instructions=0,stack_depth=0,gate_calls=[],grounding_calls=[],apply_calls=[],math_calls=[],
            flags_apply_calls=[],flags_helper_entries=0,damage_divide_entries=0,models=[],writes=dict(count=0,bytes=0))
        self.current=r;self.pending_gate=self.pending_helper=self.pending_math=None
        try:u.emu_start(entry|1,STOP,count=100001)
        finally:self.current=None
        if self.error:raise self.error
        need(self.reg(UC_ARM_REG_PC)==STOP and self.reg(UC_ARM_REG_SP)==STACK and self.reg(UC_ARM_REG_CPSR)&32
             and [self.reg(v) for v in H.G.SAVED]==H.G.COOKIES,'Wonder parent return ABI')
        need(self.pending_gate is None and self.pending_helper is None and self.pending_math is None,'unfinished native Wonder call')
        after=bytes(u.mem_read(CTX,0x4000));changed=[i for i,(a,b) in enumerate(zip(before,after)) if a!=b]
        need(set(changed)<=set(range(FLAG-CTX,FLAG-CTX+4)),'Wonder modified context/move-cache outside status')
        end=bytes(u.mem_read(STACK,256));result=self.reg(UC_ARM_REG_R0)
        if mode=='damage':
            need(end[:8]==caller[:8] and end[12:]==caller[12:] and self.word(STACK+8)==result,'Wonder mutable damage/caller words')
        else:need(end==caller,'Wonder flags incoming arguments/canary')
        need(bytes(u.mem_read(STACK-4104,8))==b'\xA5'*8,'Wonder lower stack canary')
        need(all(bytes(u.mem_read(a,len(b)))==b for a,b in self.frozen),'Wonder changed initialized code/data')
        status=self.word(FLAG);r.update(result=result,status=status,immune=bool(status&((1<<18) if mode=='damage' else 8)),
            context_changed_offsets=changed,move_cache_sha256=sha(bytes(u.mem_read(CTX+MOVE_DATA,len(self.moves)))))
        need(r['move_cache_sha256']==sha(self.moves),'actual move-cache prefix changed')
        return r


def scenarios():
    return (
        ('fire_neutral',424,0,True,False,True,1),
        ('fire_resisted',424,11,True,False,True,1),
        ('fire_super',424,12,True,False,False,1),
        ('fire_without_wg',424,0,False,False,False,None),
        ('shadow_charge',467,11,True,False,False,0),
        ('shadow_impact',467,11,True,True,True,512),
        ('fly_charge',19,0,True,False,False,0),
        ('fly_impact',19,0,True,True,True,512),
        ('ordinary_tackle',33,0,True,False,True,1),
        ('ordinary_without_wg',33,0,False,False,False,None),
    )


def gate_window(model,role):
    base=int(next(r['ram'] for r in model['record']['overlays'] if r['id']==12),16)
    at=GATE-H.G.T.OVERLAY_BASE;function=base+at
    gate=model['overlay'][at:at+108]
    need(sha(gate)==(GATE_SHA if role=='r4' else OLD_GATE_SHA),'entire charge gate identity')
    aliases=[H.pc_alias(gate,function,4,100,MOVE_DATA),H.pc_alias(gate,function,0x52,104,0x213C)]
    need(gate[0x50:0x52]==H.G.T.FIRE_FANG_BRANCH_PREIMAGE and
         H.G.S.SHARED.branch(gate[0x50:0x52],function+0x50,'bne')==function+0x5E,'actual retained charge branch')
    return dict(function_ram=hex(function),bytes=108,code_bytes=98,alignment_bytes=2,literal_bytes=8,
        raw_sha256=sha(gate),literal_aliases=aliases,branch_ram=hex(function+0x50),branch_target=hex(function+0x5E))


def analyze(rom,v4,base,retail,language):
    import gc
    models={name:H.G.S.SHARED.read_image(path,language,name) for name,path in
        (('retail',retail),('base11',base),('v4',v4),('r4',rom))}
    windows=[dict(input=name,**gate_window(model,name)) for name,model in models.items()]
    current,old=models['r4'],models['v4'];at=GATE-H.G.T.OVERLAY_BASE
    before=old['overlay'][at:at+108];expected=bytearray(before)
    need(expected[0x4C:0x4E]==H.G.T.FIRE_FANG_PREIMAGE,'source effect preimage')
    expected[0x4C:0x4E]=H.G.T.FIRE_FANG_REPLACEMENT
    need(bytes(expected)==current['overlay'][at:at+108],'whole gate source recipe reconstruction')
    moves,move_record=read_moves(rom)
    previous,_,previous_record=H.G.S.engine_chart(v4,language,'v4')
    dense,_,dense_record=H.G.S.engine_chart(rom,language,'r4')
    replay,_=H.G.type_chart.patch_overlay(previous)
    need(H.G.type_chart._chart_bytes(replay)==H.G.type_chart._chart_bytes(dense),'current chart source correspondence')
    callers=[]
    for site,owner in ((0x02251F64,'damage'),(0x0225214A,'flags')):
        raw=current['overlay'][site-H.G.T.OVERLAY_BASE:site-H.G.T.OVERLAY_BASE+4]
        need(H.G.S.SHARED.branch(raw,site,'bl')==GATE,'actual current Wonder Guard caller')
        callers.append(dict(site=hex(site),target=hex(GATE),consumer=owner,sha256=sha(raw)))
    cpu=WonderCPU(current['segments'],current['overlay'],dense,moves);runs=[]
    for mode in ('damage','flags'):
        for name,move,target,wonder,charged,immune,gate in scenarios():
            result=cpu.observe(mode,move,target,wonder=wonder,charged=charged);expect_immune(result,immune)
            need([c['result'] for c in result['gate_calls']]==([] if gate is None else [gate]),'actual gate return/call count '+name)
            if mode=='flags':need(not result['models'] and result['flags_helper_entries']==1,'current native flags path, no service stub')
            runs.append(dict(name=name,result=result))
    closure=cpu.closure();del cpu;gc.collect()
    counter=[]
    for variant in ('old','shortcut'):
        cpu=WonderCPU(current['segments'],counter_image(current['overlay'],variant),dense,moves,variant=variant)
        for mode in ('damage','flags'):
            for name,move,target,required in (('fire_neutral',424,0,True),('shadow_charge',467,11,False)):
                result=cpu.observe(mode,move,target)
                wrong=result['immune'] is not required
                need(wrong if variant=='old' or name=='shadow_charge' else not wrong,'counterexample must discriminate the intended branch')
                if wrong:
                    try:expect_immune(result,required)
                    except ValueError:pass
                    else:raise ValueError('Wonder false semantic success')
                counter.append(dict(variant=variant,name=name,required_immune=required,oracle_rejected=wrong,result=result))
        del cpu;gc.collect()
    return dict(schema='wonder-guard-source-rom-v1',language=language,compilation_performed=False,
        provenance='one source halfword in inherited native code; no new compiled payload',
        inputs=[model['record'] for model in models.values()],gate_windows=windows,
        source_recipe=dict(declared_bytes=2,changed_ram=[hex(GATE+i) for i,(a,b) in enumerate(zip(before,expected)) if a!=b],
            current_gate_sha256=GATE_SHA,retained_branch_ram='0x02258490'),
        move_archive=move_record,chart=dict(v4=previous_record,r4=dense_record),callers=callers,
        runs=runs,closure=closure,counterproofs=counter,
        coverage=dict(positive_parent_entries=len(runs),counter_parent_entries=len(counter),scenario_count=10,consumers=2),
        source_sha256={str(p.relative_to(SOURCE)):sha(p.read_bytes()) for p in
            (Path(__file__),Path(H.__file__),Path(H.G.__file__),Path(H.G.S.__file__),Path(H.G.S.SHARED.__file__),
             Path(H.G.T.__file__),SOURCE/'features/borsa/tools/attribuisci.py',SOURCE/'sgp131/test_fairy_ai_rom.py')},
        limits=['five damage query models with Wonder Guard ability supplied; flags abilities supplied on stack',
                '471 archive records identified, only first468 copied to battle-cache; selected moves/states exercised',
                'isolated consumer entries, not a natural charge/controller/Power Herb sequence',
                'immunity status is not HP storage; damage and flags consumers encode it differently',
                'historical512 campaign retains older inputs; no full old campaign repeated',
                'original native compiler, save/device/timing and whole AI choice unqualified'])


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
    print(args.language,'Wonder Guard:',len(result['runs']),'current +',len(result['counterproofs']),'counter/control entries PASS; no compilation')


if __name__=='__main__':main()
