#!/usr/bin/env python3
"""Attribute Grounding columns through the actual type-damage consumer."""
import importlib.util
import json
from pathlib import Path
import struct

spec=importlib.util.spec_from_file_location('grounding_shared',Path(__file__).with_name('attribuisci.py'))
G=importlib.util.module_from_spec(spec);spec.loader.exec_module(G)
from sgp131 import test_type_chart as D
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_THUMB,UC_HOOK_CODE,UC_HOOK_MEM_READ,UC_HOOK_MEM_WRITE
from unicorn.arm_const import (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3,
    UC_ARM_REG_SP,UC_ARM_REG_LR,UC_ARM_REG_PC,UC_ARM_REG_CPSR)
need,sha=G.need,G.sha
HELPER,HELPER_END=0x02251C74,0x02251D28
PARENT,PARENT_END=0x02251D28,0x02252054
APPLY,APPLY_END=0x022583B4,0x02258440
DIVIDE,DIVIDE_END=0x02253178,0x02253194
SIGNED,SIGNED_END=G.S.DIV,G.S.DIV_END
HELPER_SHA='0c2f127b2687c82b6fd9b8d97a590011ccaa2f1e84021c956f76edda763f821f'
OLD_HELPER_SHA='63908aa186c999cc59ea0a1875ddfad458c4f1d9e25f044d81824c26069a6802'
PARENT_SHA='3958c8527fe0b43de6b2514020eb8bc7de00a2a45761d59761f264e99ecfb443'
APPLY_SHA='2f27bcc0bcbdfb64629327b5ecaa26623afe0c4d2401ab3ff578e60b6546b686'
DIVIDE_SHA='f5cf038e36e912e23ea10bf74b1bb991fbc1eadb235f0c1be9f27e638de8bce5'
SOURCE=G.SOURCE


def old_columns(image):
    result=bytearray(image);at=G.T.GROUNDING_SITE-G.T.OVERLAY_BASE
    need(result[at:at+8]==G.T.GROUNDING_REPLACEMENT,'old-column counterproof preimage')
    result[at:at+8]=G.T.GROUNDING_PREIMAGE
    return bytes(result)


def expect_grounded(result,damage,flags):
    need((result['damage'],result['flags'])==(damage,flags),'grounded damage/status differs')


class GroundingCPU(D.NativeDamage):
    """Keep the legacy five query models; execute the native division wrapper too."""
    def __init__(self,segments,image,dense,*,attested=True):
        for start,end,digest in ((PARENT,PARENT_END,PARENT_SHA),(APPLY,APPLY_END,APPLY_SHA),
                                 (DIVIDE,DIVIDE_END,DIVIDE_SHA)):
            need(sha(image[start-G.T.OVERLAY_BASE:end-G.T.OVERLAY_BASE])==digest,'current native damage dependency')
        actual=sha(image[HELPER-G.T.OVERLAY_BASE:HELPER_END-G.T.OVERLAY_BASE])
        need(actual==HELPER_SHA if attested else actual==OLD_HELPER_SHA,'current/counter Grounding helper')
        self.defender,self.effect=struct.unpack_from('<2I',image,0x02251D20-G.T.OVERLAY_BASE)
        need(sha(G.piece(segments,SIGNED,524))==G.S.DIV_SHA,'native signed math dependency')
        need(sha(G.type_chart._chart_bytes(dense))==G.CHART_SHA,'current dense chart')
        self.uc=Uc(UC_ARCH_ARM,UC_MODE_THUMB)
        for address,size in ((0x02000000,0x400000),(0x01FF8000,0x8000),(0x027E0000,0x20000)):self.uc.mem_map(address,size)
        self.frozen=[(a,bytes(b)) for a,b in segments]+[(G.T.OVERLAY_BASE,bytes(image)),(G.type_chart.OVERLAY_BASE,bytes(dense))]
        for address,data in self.frozen:self.uc.mem_write(address,data)
        self.current=None;self.pending_helper=None;self.pending_math=None;self.error=None
        self.code_seen={};self.read_seen=set()
        for address,name in self.STUBS.items():
            if name!='damage_divide':self.uc.hook_add(UC_HOOK_CODE,self._stub,None,address,address)
        self.uc.hook_add(UC_HOOK_CODE,self._code)
        self.uc.hook_add(UC_HOOK_MEM_READ,self._read)
        self.uc.hook_add(UC_HOOK_MEM_WRITE,self._write)

    def _dispatch(self,name):
        self.current['models'].append(dict(name=name,args=[self.reg(r) for r in (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3)]))
        return super()._dispatch(name)

    def _code(self,u,address,size,unused):
        r=self.current
        if r is None:return
        r['instructions']+=1;need(r['instructions']<=100000,'Grounding instruction budget')
        sp=self.reg(UC_ARM_REG_SP);thumb=bool(self.reg(UC_ARM_REG_CPSR)&32)
        r['stack_depth']=max(r['stack_depth'],D.STACK-sp)
        if self.pending_helper and address==self.pending_helper['return_pc']:
            need(thumb and sp==self.pending_helper['sp'] and [self.reg(v) for v in G.SAVED]==self.pending_helper.pop('saved'),
                 'Grounding helper return ABI')
            self.pending_helper['active']=self.reg(UC_ARM_REG_R0)
            need(self.pending_helper['active'] in (0,1),'Grounding boolean result')
            r['grounding_calls'].append(self.pending_helper);self.pending_helper=None
        if self.pending_math and address==self.pending_math['return_pc']:
            need(thumb and sp==self.pending_math['sp'] and [self.reg(v) for v in G.SAVED]==self.pending_math.pop('saved'),
                 'Grounding signed math return ABI')
            quotient,remainder=self.reg(UC_ARM_REG_R0),self.reg(UC_ARM_REG_R1)
            need((quotient,remainder)==divmod(self.pending_math['numerator'],self.pending_math['denominator']),
                 'actual signed division positive-domain quotient/remainder')
            self.pending_math.update(quotient=quotient,remainder=remainder)
            r['math_calls'].append(self.pending_math);self.pending_math=None
        if address in self.STUBS and self.STUBS[address]!='damage_divide':return
        self.code_seen[address]=(size,thumb)
        if SIGNED<=address<SIGNED_END:
            need(not thumb and size==4,'Grounding signed math ARM ISA')
        else:
            need(thumb and size in (2,4),'Grounding Thumb ISA')
            need(HELPER<=address<0x02251D20 or PARENT<=address<0x0225203C
                 or APPLY<=address<0x0225843C or DIVIDE<=address<DIVIDE_END,'unexpected Grounding code %#x'%address)
        if address==HELPER:
            need(self.pending_helper is None and self.reg(UC_ARM_REG_R0)==D.CTX
                 and self.reg(UC_ARM_REG_R1)==0 and self.reg(UC_ARM_REG_R2)==1,'Grounding helper caller ABI')
            index=self.reg(UC_ARM_REG_R3);need(index<325,'modern Grounding index domain')
            self.pending_helper=dict(index=index,return_pc=self.reg(UC_ARM_REG_LR)&~1,sp=sp,
                saved=[self.reg(v) for v in G.SAVED],reads=[])
            need(self.pending_helper['return_pc'] in (0x02251ECC,0x02251F26),'actual Grounding caller return')
        if address==APPLY:
            need(self.reg(UC_ARM_REG_R0)==D.CTX and self.reg(UC_ARM_REG_R1)==0
                 and self.reg(UC_ARM_REG_R2) in (0,5,10,20),'native Apply caller ABI')
            power,flag=struct.unpack('<2I',u.mem_read(sp,8))
            need(power==r['power'] and flag==D.FLAG,'native Apply stack args')
            r['apply_calls'].append(dict(effect=self.reg(UC_ARM_REG_R2),damage=self.reg(UC_ARM_REG_R3),power=power))
        if address==DIVIDE:r['damage_divide_entries']+=1
        if address==SIGNED:
            need(self.pending_math is None,'nested signed division')
            numerator,denominator=self.reg(UC_ARM_REG_R0),self.reg(UC_ARM_REG_R1)
            need(0<=numerator<=40000 and 1<=denominator<=100,'Grounding finite positive math domain')
            self.pending_math=dict(numerator=numerator,denominator=denominator,return_pc=self.reg(UC_ARM_REG_LR)&~1,
                sp=sp,saved=[self.reg(v) for v in G.SAVED])
            need(self.pending_math['return_pc'] in (0x02251E06,0x02251FFC,0x0225318C),'native signed math callers')

    def _read(self,u,access,address,size,value,unused):
        if self.current is None:return
        if any(a<=address and address+size<=a+len(b) for a,b in self.frozen):self.read_seen.update(range(address,address+size))
        if self.pending_helper and size==1:
            index=self.pending_helper['index']
            if address in (self.defender+3*index,self.effect+3*index):
                self.pending_helper['reads'].append(dict(ram=hex(address),value=u.mem_read(address,1)[0]))

    def _write(self,u,access,address,size,value,unused):
        allowed=D.STACK-4096<=address and address+size<=D.STACK
        allowed|=address in (D.STACK+8,D.STACK+12) and size==4
        allowed|=D.FLAG<=address and address+size<=D.FLAG+4
        need(allowed,'Grounding guest write outside stack/status')
        self.current['writes']['count']+=1;self.current['writes']['bytes']+=size

    def observe(self,scenario,*,ingrain=False,roost=False,miracle=False,damage=100,power=0):
        need(type(damage) is int and 0<=damage<=100 and type(power) is int and 0<=power<=255,'Grounding synthetic damage/power domain')
        need(0<=scenario.move_type<18 and 0<=scenario.target_type<18,'Grounding type domain')
        self.scenario=scenario;self.error=None;u=self.uc
        u.mem_write(D.CTX,bytes(0x4000));u.mem_write(D.STACK-4104,b'\xA5'*8+bytes(4096)+b'\xA5'*256)
        u.mem_write(D.CTX+0x180,struct.pack('<I',D.GRAVITY if scenario.gravity else 0))
        u.mem_write(D.CTX+0x2DC0+0xC0,struct.pack('<I',(0x400 if ingrain else 0)|(0x400000 if miracle else 0)))
        u.mem_write(D.CTX+0x1D4+0x40,struct.pack('<I',0x40 if roost else 0))
        # Move1's power/type PC literals are independently verified in the reader.
        u.mem_write(D.CTX+0x3E1+16,bytes([power]));u.mem_write(D.CTX+0x3E2+16,bytes([scenario.move_type]))
        u.mem_write(D.STACK,struct.pack('<4I',0,1,damage,D.FLAG));u.mem_write(D.STACK+16,D.CALLER_CANARY)
        before=bytes(u.mem_read(D.CTX,0x4000));caller=bytes(u.mem_read(D.STACK,256))
        for register,value in zip(G.SAVED,G.COOKIES):u.reg_write(register,value)
        for register,value in ((UC_ARM_REG_R0,0x02390000),(UC_ARM_REG_R1,D.CTX),(UC_ARM_REG_R2,1),
            (UC_ARM_REG_R3,scenario.move_type),(UC_ARM_REG_SP,D.STACK),(UC_ARM_REG_LR,D.STOP|1)):
            u.reg_write(register,value)
        r=dict(types=[scenario.move_type,scenario.target_type],item=scenario.item,gravity=scenario.gravity,
            ingrain=ingrain,roost=roost,miracle=miracle,power=power,initial_damage=damage,instructions=0,stack_depth=0,
            grounding_calls=[],apply_calls=[],math_calls=[],damage_divide_entries=0,models=[],writes=dict(count=0,bytes=0))
        self.current=r;self.pending_helper=self.pending_math=None
        try:u.emu_start(PARENT|1,D.STOP,count=100001)
        finally:self.current=None
        if self.error:raise self.error
        need(self.reg(UC_ARM_REG_PC)==D.STOP and self.reg(UC_ARM_REG_SP)==D.STACK
             and self.reg(UC_ARM_REG_CPSR)&32 and [self.reg(v) for v in G.SAVED]==G.COOKIES,'Grounding parent return ABI')
        need(self.pending_helper is None and self.pending_math is None,'unfinished native Grounding/math call')
        after=bytes(u.mem_read(D.CTX,0x4000));changed=[i for i,(a,b) in enumerate(zip(before,after)) if a!=b]
        need(set(changed)<=set(range(D.FLAG-D.CTX,D.FLAG-D.CTX+4)),'Grounding changed context outside status')
        final_caller=bytes(u.mem_read(D.STACK,256))
        need(final_caller[:8]==caller[:8] and final_caller[12:]==caller[12:] and
             bytes(u.mem_read(D.STACK-4104,8))==b'\xA5'*8,'Grounding incoming args/canaries')
        r.update(damage=self.reg(UC_ARM_REG_R0),flags=self.word(D.FLAG),
                 final_damage_homeword=self.word(D.STACK+8),context_changed_offsets=changed)
        need(r['final_damage_homeword']==r['damage'],'mutable damage argument homeword differs from return')
        need(all(bytes(u.mem_read(a,len(b)))==b for a,b in self.frozen),'Grounding modified initialized code/data')
        return r

    def closure(self):
        def ranges(values):
            blocks=[]
            for a in sorted(values):
                if blocks and blocks[-1][1]==a:blocks[-1][1]+=1
                else:blocks.append([a,a+1])
            return [dict(ram=hex(a),bytes=b-a,sha256=sha(bytes(self.uc.mem_read(a,b-a)))) for a,b in blocks]
        code=set()
        for a,(size,thumb) in self.code_seen.items():code.update(range(a,a+size))
        return dict(executed_ranges=ranges(code),immutable_read_ranges=ranges(self.read_seen),
            models={hex(a):name for a,name in self.STUBS.items() if name!='damage_divide'})


def pc_alias(data,function,offset,pool,expected):
    import capstone
    from capstone.arm import ARM_REG_PC
    md=capstone.Cs(capstone.CS_ARCH_ARM,capstone.CS_MODE_THUMB);md.detail=True
    ins=list(md.disasm(data[offset:offset+2],function+offset))
    need(len(ins)==1 and ins[0].mnemonic=='ldr','Grounding PC-relative load')
    mem=ins[0].operands[1].mem;target=((function+offset+4)&~3)+mem.disp
    need(mem.base==ARM_REG_PC and target==function+pool and struct.unpack_from('<I',data,pool)[0]==expected,
         'Grounding actual literal alias/value')
    return dict(load_ram=hex(function+offset),pool_ram=hex(target),value=hex(expected))


def static_windows(model,role,canonical_parent,canonical_divide):
    base=int(next(r['ram'] for r in model['record']['overlays'] if r['id']==12),16)
    at=HELPER-G.T.OVERLAY_BASE;helper=model['overlay'][at:at+180];fn=base+at
    pointers=(G.T.MODERN_CHART+1,G.T.MODERN_CHART+2) if role=='r4' else (
        base+G.S.SHARED.CHART-G.T.OVERLAY_BASE+1,base+G.S.SHARED.CHART-G.T.OVERLAY_BASE+2)
    aliases=[]
    for offset in (0x2A,0x50,0x6C,0x96):aliases.append(pc_alias(helper,fn,offset,172,pointers[0]))
    for offset in (0x32,0x74,0x9E):aliases.append(pc_alias(helper,fn,offset,176,pointers[1]))
    need(G.S.SHARED.branch(helper[10:14],fn+10,'bl')==base+0x02255830-G.T.OVERLAY_BASE,'helper native held-item target')
    normalized=bytearray(helper)
    if role!='r4':struct.pack_into('<2I',normalized,172,G.S.SHARED.CHART+1,G.S.SHARED.CHART+2)
    need(sha(normalized)==(HELPER_SHA if role=='r4' else OLD_HELPER_SHA),'Grounding full helper correspondence')
    at=PARENT-G.T.OVERLAY_BASE;parent=model['overlay'][at:at+812];parent_fn=base+at
    old_chart=base+G.S.SHARED.CHART-G.T.OVERLAY_BASE
    chart=struct.unpack_from('<I',parent,0x324)[0]
    need(chart==(old_chart if role=='retail' else G.T.MODERN_CHART),'native/inherited damage chart pointer')
    chart_aliases=[pc_alias(parent,parent_fn,o,0x324,chart) for o in (0x14C,0x154,0x220)]
    comparison=bytearray(parent);math_calls=[]
    for offset in (0xDA,0x2D0):
        target=G.S.SHARED.branch(parent[offset:offset+4],parent_fn+offset,'blx')
        need(target==SIGNED,'regional parent signed math call')
        comparison[offset:offset+4]=canonical_parent[offset:offset+4]
        math_calls.append(dict(site=hex(parent_fn+offset),target=hex(target)))
    struct.pack_into('<I',comparison,0x324,G.T.MODERN_CHART)
    need(sha(comparison)==PARENT_SHA,'full parent bounded regional/chart correspondence')
    power=pc_alias(parent,parent_fn,0x88,0x318,0x3E1) # 1DB0 -> 2040
    default_type=pc_alias(parent,parent_fn,0x7C,0x314,0x3E2)
    divide_at=DIVIDE-G.T.OVERLAY_BASE;divide=model['overlay'][divide_at:divide_at+28]
    divide_fn=base+divide_at
    need(G.S.SHARED.branch(divide[16:20],divide_fn+16,'blx')==SIGNED,'actual native DamageDivide math target')
    corrected=bytearray(divide)
    corrected[16:20]=canonical_divide[16:20]
    need(sha(corrected)==DIVIDE_SHA and sha(G.piece(model['segments'],SIGNED,524))==G.S.DIV_SHA,'regional native arithmetic identity')
    apply=model['overlay'][APPLY-G.T.OVERLAY_BASE:APPLY_END-G.T.OVERLAY_BASE]
    need(sha(apply)==APPLY_SHA,'native Apply140 continuity')
    return dict(helper_ram=hex(fn),helper_bytes=180,helper_raw_sha256=sha(helper),literal_aliases=aliases,
        parent_ram=hex(parent_fn),parent_bytes=812,parent_raw_sha256=sha(parent),parent_chart_ram=hex(chart),
        parent_comparison_only_fields=[0xDA,0x2D0,0x324],math_calls=math_calls,parent_chart_aliases=chart_aliases,
        power_alias=power,default_type_alias=default_type,divide_raw_sha256=sha(divide),divide_comparison_only_field=16,
        apply_sha256=sha(apply),executed_bytes_modified=False)


def scenarios():
    # All default fixtures retain historical Move1 power0; explicit power cases follow.
    rows=[('ground_flying',D.DamageScenario(4,2),{},0,8),
          ('iron_ball',D.DamageScenario(4,2,item=D.IRON_BALL_EFFECT),{},100,0),
          ('gravity',D.DamageScenario(4,2,gravity=True),{},100,0),
          ('both',D.DamageScenario(4,2,item=D.IRON_BALL_EFFECT,gravity=True),{},100,0),
          ('other_item',D.DamageScenario(4,2,item=105),{},0,8),
          ('ground_poison',D.DamageScenario(4,3),{},200,0),
          ('fire_flying',D.DamageScenario(10,2),{},100,0),
          ('electric_ground',D.DamageScenario(13,4),{},0,8),
          ('fairy_dragon',D.DamageScenario(9,16),{},200,0),
          ('ghost_steel',D.DamageScenario(7,8),{},100,0),
          ('ingrain',D.DamageScenario(4,2),dict(ingrain=True),100,0),
          ('roost_ground',D.DamageScenario(4,2),dict(roost=True),100,0),
          ('roost_electric',D.DamageScenario(13,2),dict(roost=True),100,0),
          ('miracle_eye',D.DamageScenario(14,17),dict(miracle=True),100,0),
          ('powered_weakness',D.DamageScenario(4,3),dict(power=50),200,2),
          ('powered_resistance',D.DamageScenario(10,11),dict(power=50),50,4),
          ('minimum_damage',D.DamageScenario(10,11),dict(power=50,damage=1),1,4)]
    return rows


def analyze(rom,v4,base,retail,language):
    import gc
    models={name:G.S.SHARED.read_image(p,language,name) for name,p in
        (('retail',retail),('base11',base),('v4',v4),('r4',rom))}
    current,old=models['r4'],models['v4'];offset=HELPER-G.T.OVERLAY_BASE
    canonical_parent=current['overlay'][PARENT-G.T.OVERLAY_BASE:PARENT_END-G.T.OVERLAY_BASE]
    canonical_divide=current['overlay'][DIVIDE-G.T.OVERLAY_BASE:DIVIDE_END-G.T.OVERLAY_BASE]
    need(sha(canonical_parent)==PARENT_SHA and sha(canonical_divide)==DIVIDE_SHA,'canonical native normalization windows')
    records=[dict(input=name,**static_windows(x,name,canonical_parent,canonical_divide)) for name,x in models.items()]
    original=old['overlay'][offset:offset+180];expected=bytearray(original)
    need(expected[172:180]==G.T.GROUNDING_PREIMAGE,'source Grounding literal preimage')
    expected[172:180]=G.T.GROUNDING_REPLACEMENT
    need(bytes(expected)==current['overlay'][offset:offset+180],'whole helper source recipe reconstruction')
    previous,_,before_record=G.S.engine_chart(v4,language,'v4');dense,_,dense_record=G.S.engine_chart(rom,language,'r4')
    repaired,_=G.type_chart.patch_overlay(previous)
    need(G.type_chart._chart_bytes(repaired)==G.type_chart._chart_bytes(dense),'modern chart source replay')
    calls=[]
    for site,target in ((0x02251EC8,HELPER),(0x02251F22,HELPER),(0x02251EE2,APPLY),(0x02251F3C,APPLY),(0x022583D8,DIVIDE)):
        need(G.S.SHARED.branch(current['overlay'][site-G.T.OVERLAY_BASE:site-G.T.OVERLAY_BASE+4],site,'bl')==target,'actual damage dependency caller')
        calls.append(dict(site=hex(site),target=hex(target)))
    upstream=[]
    for owner,base_address,sites in (
        (10,0x0221BE20,(0x0221D2BC,0x0221D366,0x0221F426,0x0221F696,0x0221F87E,0x0221F8B4,0x0221FDA2,0x0221FE44)),
        (12,G.T.OVERLAY_BASE,(0x02243542,0x0224B4EC,0x022536C6,0x02258B48))):
        for site in sites:
            raw=current['overlays'][owner][site-base_address:site-base_address+4]
            need(G.S.SHARED.branch(raw,site,'bl')==PARENT,'actual upstream damage caller')
            upstream.append(dict(overlay=owner,ram=hex(site),target=hex(PARENT),sha256=sha(raw)))
    cpu=GroundingCPU(current['segments'],current['overlay'],dense);runs=[]
    for name,scenario,state,damage,flags in scenarios():
        result=cpu.observe(scenario,**state);expect_grounded(result,damage,flags)
        if name in ('iron_ball','gravity'):
            need(len(result['grounding_calls'])==1 and result['grounding_calls'][0]['index']==72 and
                 result['grounding_calls'][0]['active']==0 and [r['value'] for r in result['grounding_calls'][0]['reads']]==[2,0],
                 'actual modern Flying/immunity column reads')
        runs.append(dict(name=name,result=result))
    closure=cpu.closure();del cpu;gc.collect()
    cpu=GroundingCPU(current['segments'],old_columns(current['overlay']),dense,attested=False);counter=[]
    for scenario in (D.DamageScenario(4,2,item=D.IRON_BALL_EFFECT),D.DamageScenario(4,2,gravity=True)):
        result=cpu.observe(scenario)
        need(result['damage']==0 and result['flags']==8 and len(result['grounding_calls'])==1
             and result['grounding_calls'][0]['index']==72 and result['grounding_calls'][0]['active']==1
             and result['grounding_calls'][0]['reads'][0]['value']==17,'mixed-index wrong-column counterproof')
        try:expect_grounded(result,100,0)
        except ValueError:pass
        else:raise ValueError('same-index Grounding false success')
        counter.append(result)
    del cpu;gc.collect()
    return dict(schema='grounding-source-rom-v1',language=language,compilation_performed=False,
        reason='source-owned data pointer replacement in inherited native code; no new object',
        inputs=[x['record'] for x in models.values()],native_windows=records,
        source_recipe=dict(declared_bytes=8,changed_ram=[hex(HELPER+i) for i,(a,b) in enumerate(zip(original,expected)) if a!=b],
                           current_helper_sha256=HELPER_SHA),
        chart=dict(v4=before_record,r4=dense_record,sha256=G.CHART_SHA),dependency_calls=calls,upstream_callers=upstream,
        runs=runs,closure=closure,counterproofs=counter,coverage=dict(positive_parent_entries=len(runs),counter_parent_entries=len(counter)),
        source_sha256={str(p.relative_to(SOURCE)):sha(p.read_bytes()) for p in
            (Path(__file__),Path(G.__file__),Path(G.S.__file__),Path(G.S.SHARED.__file__),
             Path(G.T.__file__),Path(D.__file__),SOURCE/'sgp131/type_chart.py')},
        limits=['five query models, attackerNormal/targetmonotype,no real ability/item lookup',
                'base damage100 or1; Move1 power0 or50 and fixed status flags0',
                'native Math observed positive bounded inputs; no general signed wrapper proof',
                'all type/status combinations, natural caller activation, SAVE/timing/hardware not qualified',
                'inherited modern parent chart pointer source/toolchain not reconstructed'])


def main():
    import argparse
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('rom','v4','base','retail','json'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--language',choices=('EN','IT'),required=True);args=p.parse_args()
    for file in (args.rom,args.v4,args.base,args.retail):
        if args.json.resolve()==file.resolve() or (args.json.exists() and file.exists() and args.json.samefile(file)):
            p.error('--json must not replace an input')
    result=analyze(args.rom,args.v4,args.base,args.retail,args.language)
    args.json.parent.mkdir(parents=True,exist_ok=True);args.json.write_text(json.dumps(result,indent=2)+'\n')
    print(args.language,'Grounding:',len(result['runs']),'positive +',len(result['counterproofs']),'old-column counterexamples PASS; no compilation')


if __name__=='__main__':main()
