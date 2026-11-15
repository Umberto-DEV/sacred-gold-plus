#!/usr/bin/env python3
"""Attribute the exact Conversion2 replacement, native RNG and row transport."""
import importlib.util
import json
from pathlib import Path
import struct
import sys

SOURCE=Path(__file__).resolve().parents[3]
spec=importlib.util.spec_from_file_location('conversion_shared_scalar',SOURCE/'features/fairy-ai/tools/attribuisci_scalare.py')
S=importlib.util.module_from_spec(spec);spec.loader.exec_module(S)
from sgp131 import type_consumers as T,type_chart
from sgp131.test_fairy_ai_rom import Conversion2Native as C
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_THUMB,UC_HOOK_CODE,UC_HOOK_MEM_READ,UC_HOOK_MEM_WRITE
from unicorn.arm_const import (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3,
    UC_ARM_REG_R4,UC_ARM_REG_R5,UC_ARM_REG_R6,UC_ARM_REG_R7,UC_ARM_REG_R8,UC_ARM_REG_R9,
    UC_ARM_REG_R10,UC_ARM_REG_R11,UC_ARM_REG_SP,UC_ARM_REG_LR,UC_ARM_REG_PC,UC_ARM_REG_CPSR)
need,sha=S.need,S.sha
COMMAND,COMMAND_END=0x02240C98,0x02240E58
COMMAND_SHA='54720adb00d5dd7627ab0bc09d68bdf803956eb182233c740341476332de0748'
RNG,RNG_END=0x0223BD98,0x0223BDC4
RNG_SHA='29e88b6c3903a8d41c8471aebff5a8ae313f9a36682b73e57d04ddf085267cd8'
DIV,DIV_END=0x020F2BA4,0x020F2D88
DIV_SHA='3b0403581ea03e86bdfc0cde00ea2ca13f522291aec399b93ecdf2fef57944eb'
CHART_SHA='349a69b6b0029141811239f4b7a40ff53ab14e16607936dc75602c0b20179221'
SEED_OFFSET=0x2448
SAVED=(UC_ARM_REG_R4,UC_ARM_REG_R5,UC_ARM_REG_R6,UC_ARM_REG_R7,
       UC_ARM_REG_R8,UC_ARM_REG_R9,UC_ARM_REG_R10,UC_ARM_REG_R11)
COOKIES=[0x44440000+i for i in range(8)]
OUT=0x023B9000


def piece(segments,address,size):
    values=[bytes(data[address-a:address-a+size]) for a,data in segments if a<=address and address+size<=a+len(data)]
    need(len(values)==1,'Conversion2 ARM9 ownership');return values[0]


def next_seed(seed):return (seed*1103515245+24691)&0xFFFFFFFF


def require_rng_progress(result):
    state=result['seed_before']
    for call in result['rng_calls']:
        need(call['before']==state and call['after']==next_seed(state) and call['value']==call['after']>>16,
             'native RNG seed transition')
        state=call['after']
    need(result['seed_after']==state,'native RNG final state/neutral direct path')


def compile_object(work):
    work=Path(work);work.mkdir(parents=True,exist_ok=True)
    payload,receipt=T.compile_native(work,retain_object=True)
    obj=(work/receipt['retained_object']).read_bytes()
    loader=T._module(SOURCE/'features/options/tools/carica_text.py','conversion_attribution_elf')
    raw,symbols=loader.load_text(obj,T.CONVERSION_SITE,('conversion2_type_row','conversion2_random_call'))
    need(sha(obj)==receipt['object_sha256'] and len(raw)==64,'Conversion2 retained ELF identity')
    need(symbols['conversion2_type_row']==T.CONVERSION_SITE|1 and symbols['conversion2_random_call']==T.CONVERSION_SITE+14,'Conversion2 ELF geometry')
    need(raw[14:18]==bytes.fromhex('00f000f8'),'Conversion2 ELF placeholder')
    need(S.SHARED.branch(payload[14:18],T.CONVERSION_SITE+14,'bl')==RNG,'independent RNG BL target')
    need(all(raw[i]==payload[i] for i in range(64) if not 14<=i<18),'ELF changes outside external BL')
    need(struct.unpack_from('<3I',payload,52)==(325,DIV,T.MODERN_CHART),'Conversion2 literal words')
    proof=dict(performed=True,**receipt,builder_sha256=sha(Path(T.__file__).read_bytes()),
        loader_sha256=sha((SOURCE/'features/options/tools/carica_text.py').read_bytes()),
        post_link_changed_offsets=[i for i,(a,b) in enumerate(zip(raw,payload)) if a!=b],
        symbols={name:hex(symbols[name]) for name in ('conversion2_type_row','conversion2_random_call')})
    for name,data in (('native.bin',payload),('compile-retained.json',(json.dumps(proof,indent=2)+'\n').encode())):
        p=work/name
        need(not p.is_symlink() and (not p.exists() or p.is_file() and p.read_bytes()==data),'existing artifact differs; use a fresh work directory')
        if not p.exists():p.write_bytes(data)
    return payload,proof


class ConversionCPU(C.Bench):
    """Reuse the legacy query controls, executing actual RNG instead of its old stub."""
    def __init__(self,segments,image,dense,*,attested=True,attested_helper=True):
        if attested_helper:
            need(sha(image[T.CONVERSION_SITE-T.OVERLAY_BASE:T.CONVERSION_SITE-T.OVERLAY_BASE+64])==T.PAYLOAD_SHA256,'current Conversion2 helper')
        self.row_count=struct.unpack_from('<I',image,T.CONVERSION_SITE-T.OVERLAY_BASE+52)[0]
        need(self.row_count in (112,325),'declared current/counter row domain')
        need(sha(type_chart._chart_bytes(dense))==CHART_SHA,'current dense chart')
        need(sha(image[COMMAND-T.OVERLAY_BASE:COMMAND_END-T.OVERLAY_BASE])==COMMAND_SHA,'current Conversion2 command')
        if attested:need(sha(image[RNG-T.OVERLAY_BASE:RNG_END-T.OVERLAY_BASE])==RNG_SHA,'current native RNG')
        need(struct.unpack_from('<3I',image,RNG-T.OVERLAY_BASE+32)==(SEED_OFFSET,1103515245,24691),'actual RNG literal words')
        need(sha(piece(segments,DIV,484))==DIV_SHA,'native unsigned divmod')
        self.regs=(UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3,*SAVED,
                   UC_ARM_REG_SP,UC_ARM_REG_LR,UC_ARM_REG_PC)
        (self.R0,self.R1,self.R2,self.R3,self.R4,self.R5,self.R6,self.R7,self.R8,self.R9,
         self.R10,self.R11,self.SP,self.LR,self.PC)=self.regs
        self.uc=Uc(UC_ARCH_ARM,UC_MODE_THUMB)
        for address,size in ((0x02000000,0x400000),(0x01FF8000,0x8000),(0x027E0000,0x20000)):self.uc.mem_map(address,size)
        self.frozen=[(a,bytes(d)) for a,d in segments]+[(T.OVERLAY_BASE,bytes(image)),(type_chart.OVERLAY_BASE,bytes(dense))]
        for address,data in self.frozen:self.uc.mem_write(address,data)
        self.overlay=image;self.current=None;self.error=None;self.pending_rng=None;self.pending_div=None
        self.code_seen={};self.read_seen=set()
        for address in C.STUBS:
            if address!=RNG:self.uc.hook_add(UC_HOOK_CODE,self._stub,None,address,address)
        self.uc.hook_add(UC_HOOK_CODE,self._code)
        self.uc.hook_add(UC_HOOK_MEM_READ,self._read)
        self.uc.hook_add(UC_HOOK_MEM_WRITE,self._write)

    def _stub(self,u,address,size,unused):
        if self.current is not None:self.current['models'].append(dict(ram=hex(address),args=[self.reg(r) for r in self.regs[:4]]))
        return super()._stub(u,address,size,unused)

    def _code(self,u,address,size,unused):
        r=self.current
        if r is None:return
        r['instructions']+=1;need(r['instructions']<=1000000,'Conversion2 instruction budget')
        sp=self.reg(self.SP);thumb=bool(self.reg(UC_ARM_REG_CPSR)&32)
        r['stack_depth']=max(r['stack_depth'],C.STACK-sp)
        if self.pending_rng and address==self.pending_rng['return_pc']:
            need(thumb and sp==self.pending_rng['sp'] and [self.reg(x) for x in SAVED]==self.pending_rng.pop('saved'),'native RNG return ABI')
            self.pending_rng.update(after=struct.unpack('<I',u.mem_read(C.BS+SEED_OFFSET,4))[0],value=self.reg(self.R0))
            r['rng_calls'].append(self.pending_rng);self.pending_rng=None
        if self.pending_div and address==self.pending_div['return_pc']:
            need(thumb and sp==self.pending_div['sp'] and [self.reg(x) for x in SAVED]==self.pending_div.pop('saved'),'native divmod return ABI')
            quotient,remainder=self.reg(self.R0),self.reg(self.R1)
            need((quotient,remainder)==divmod(self.pending_div['numerator'],self.row_count),'actual unsigned quotient/remainder')
            self.pending_div.update(quotient=quotient,remainder=remainder)
            r['division_calls'].append(self.pending_div);self.pending_div=None
        if address in C.STUBS and address!=RNG:return
        self.code_seen[address]=(size,thumb)
        if DIV<=address<DIV_END:need(not thumb and size==4,'unsigned divmod ARM ISA')
        else:
            need(thumb and size in (2,4),'Conversion2 Thumb ISA')
            need(COMMAND<=address<0x02240E3E or T.CONVERSION_SITE<=address<T.CONVERSION_SITE+52
                 or RNG<=address<0x0223BDB6,'unexpected Conversion2 code %#x'%address)
        if address==T.CONVERSION_SITE:
            r['helper_calls'].append(self.reg(self.R1))
            need(self.reg(self.R0)==C.BS,'row helper BattleSystem ABI')
        if address==RNG:
            need(self.pending_rng is None and self.reg(self.R0)==C.BS,'native RNG call ABI')
            self.pending_rng=dict(before=struct.unpack('<I',u.mem_read(C.BS+SEED_OFFSET,4))[0],
                return_pc=self.reg(self.LR)&~1,sp=sp,saved=[self.reg(x) for x in SAVED])
            need(self.pending_rng['return_pc']==T.CONVERSION_SITE+18,'native RNG caller')
        if address==DIV:
            need(self.pending_div is None and self.reg(self.R1)==self.row_count and self.reg(self.R0)<=65535,'native unsigned modulo domain')
            self.pending_div=dict(numerator=self.reg(self.R0),return_pc=self.reg(self.LR)&~1,sp=sp,saved=[self.reg(x) for x in SAVED])
            need(self.pending_div['return_pc']==T.CONVERSION_SITE+24,'native unsigned divmod caller')

    def _write(self,u,access,address,size,value,unused):
        r=self.current;allowed=C.STACK-4096<=address and address+size<=C.STACK
        allowed|=address==C.BS+SEED_OFFSET and size==4
        if r['mode']=='helper':allowed|=address in (OUT+16,OUT+48,OUT+80) and size==1
        else:allowed|=(address in (C.CTX+0x2D64,C.CTX+0x2D65) and size==1) or (address==C.CTX+0x130 and size==4)
        need(allowed,'Conversion2 unexpected guest write %#x'%address)
        r['writes']['count']+=1;r['writes']['bytes']+=size

    def _read(self,u,access,address,size,value,unused):
        if self.current is None:return
        if T.MODERN_CHART<=address<T.MODERN_CHART+978:
            need(address+size<=T.MODERN_CHART+975,'chart read crosses selectable records')
            self.current['rows'].update((address-T.MODERN_CHART+i)//3 for i in range(size))
        if any(a<=address and address+size<=a+len(b) for a,b in self.frozen):self.read_seen.update(range(address,address+size))

    def observe(self,*,index=None,seed=0,last_move_type=9,current_types=(0,0),require_rng=True):
        need(type(seed) is int and 0<=seed<=0xFFFFFFFF,'RNG seed domain')
        direct=index is not None
        if direct:need(type(index) is int and 0<=index<=0xFFFFFFFF,'row index domain')
        else:need(0<=last_move_type<18 and all(0<=v<18 for v in current_types),'command type domain')
        u=self.uc;u.mem_write(C.CTX,bytes(0x4000));u.mem_write(C.BS,bytes(0x2500))
        u.mem_write(C.BS+SEED_OFFSET,struct.pack('<I',seed))
        u.mem_write(C.STACK-4104,b'\xA5'*8+bytes(4096)+b'\xA5'*256)
        u.mem_write(OUT,b'\xA5'*96)
        if direct:
            u.mem_write(C.STACK,struct.pack('<I',OUT+80))
            args=(C.BS,index,OUT+16,OUT+48);entry=T.CONVERSION_SITE
        else:
            self.current_types=tuple(current_types)
            for offset,fmt,value in ((0x64,'I',0),(0x30C4,'H',1),(0x30CC,'H',0),
                                     (0x30D4,'H',last_move_type),(0x2DB0,'I',0x1000)):
                u.mem_write(C.CTX+offset,struct.pack('<'+fmt,value))
            args=(C.BS,C.CTX,0,0);entry=COMMAND
        before=bytes(u.mem_read(C.CTX,0x4000));caller=bytes(u.mem_read(C.STACK,256));bs=bytes(u.mem_read(C.BS,0x2500))
        for reg,value in zip(SAVED,COOKIES):u.reg_write(reg,value)
        for reg,value in zip(self.regs[:4],args):u.reg_write(reg,value)
        for reg,value in ((self.SP,C.STACK),(self.LR,C.STOP|1)):u.reg_write(reg,value)
        r=dict(mode='helper' if direct else 'command',index=index,seed_before=seed,instructions=0,stack_depth=0,
            helper_calls=[],rng_calls=[],division_calls=[],models=[],rows=set(),writes=dict(count=0,bytes=0))
        self.current=r;self.error=None;self.pending_rng=self.pending_div=None
        try:u.emu_start(entry|1,C.STOP,count=1000001)
        finally:self.current=None
        if self.error:raise self.error
        need(self.reg(self.PC)==C.STOP and self.reg(self.SP)==C.STACK and self.reg(UC_ARM_REG_CPSR)&32
             and [self.reg(v) for v in SAVED]==COOKIES,'Conversion2 return/ABI')
        need(self.pending_rng is None and self.pending_div is None,'unfinished native RNG/divmod')
        need(bytes(u.mem_read(C.STACK-4104,8))==b'\xA5'*8 and bytes(u.mem_read(C.STACK,256))==caller,'Conversion2 stack canaries/caller')
        need(all(bytes(u.mem_read(a,len(b)))==b for a,b in self.frozen),'Conversion2 modified initialized code/data')
        after=bytes(u.mem_read(C.CTX,0x4000));changed=[i for i,(a,b) in enumerate(zip(before,after)) if a!=b]
        need(set(changed)<=({0x130,0x131,0x132,0x133,0x2D64,0x2D65} if not direct else set()),'Conversion2 context write delta')
        bs_after=bytes(u.mem_read(C.BS,0x2500));need(all(a==b for i,(a,b) in enumerate(zip(bs,bs_after))
            if not SEED_OFFSET<=i<SEED_OFFSET+4),'Conversion2 BattleSystem outside seed changed')
        r.update(result=self.reg(self.R0),seed_after=struct.unpack('<I',u.mem_read(C.BS+SEED_OFFSET,4))[0],
            rows=sorted(r['rows']),context_changed_offsets=changed,types=list(u.mem_read(C.CTX+0x2D64,2)),
            snapshot_type=struct.unpack('<I',u.mem_read(C.CTX+0x130,4))[0])
        if direct:
            r['row']=[u.mem_read(OUT+offset,1)[0] for offset in (16,48,80)]
            need(all(u.mem_read(OUT+i,1)[0]==0xA5 for i in range(96) if i not in (16,48,80)),'row output byte canaries')
        if require_rng:require_rng_progress(r)
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
            models=[hex(a) for a in C.STUBS if a!=RNG],rng_seed_offset=hex(SEED_OFFSET))


def verify_build(work):
    work=Path(work);receipt=json.loads((work/'compile-retained.json').read_text())
    obj=(work/'type-consumers.o').read_bytes();payload=(work/'native.bin').read_bytes()
    need(receipt['performed'] is True and sha(obj)==receipt['object_sha256'] and sha(payload)==T.PAYLOAD_SHA256,'reused Conversion2 artifact identity')
    need(receipt['source_sha256']==sha(T.NATIVE.read_bytes()) and receipt['builder_sha256']==sha(Path(T.__file__).read_bytes())
         and receipt['loader_sha256']==sha((SOURCE/'features/options/tools/carica_text.py').read_bytes()),'reused Conversion2 source/builder/loader drift')
    need(receipt['compiler']['version']==T.COMPILER_VERSION and receipt['compiler']['executable_sha256']==T.COMPILER_SHA256
         and receipt['compiler']['flags']==list(T.FLAGS),'reused Conversion2 compiler record')
    loader=T._module(SOURCE/'features/options/tools/carica_text.py','conversion_reused_elf')
    raw,symbols=loader.load_text(obj,T.CONVERSION_SITE,('conversion2_type_row','conversion2_random_call'))
    need(symbols['conversion2_type_row']==T.CONVERSION_SITE|1 and symbols['conversion2_random_call']==T.CONVERSION_SITE+14
         and raw[14:18]==bytes.fromhex('00f000f8'),'reused Conversion2 ELF geometry')
    expected=bytearray(raw);expected[14:18]=T.bl_thumb(T.CONVERSION_SITE+14,RNG|1)
    need(bytes(expected)==payload,'reused Conversion2 ELF post-link correspondence')
    return dict(performed=False,reused_build_verified=True,object_sha256=sha(obj),payload_sha256=sha(payload),compiler_recorded=receipt['compiler'])


def old_helper(model):
    import capstone
    from capstone.arm import ARM_REG_PC
    base=int(next(r['ram'] for r in model['record']['overlays'] if r['id']==12),16)
    at=T.CONVERSION_SITE-T.OVERLAY_BASE;function=base+at
    raw=model['overlay'][at:at+64];normalized=bytearray(raw)
    rng_target=S.SHARED.branch(raw[12:16],function+12,'bl')
    need(rng_target==base+(RNG-T.OVERLAY_BASE),'historical helper actual RNG target')
    math_target=S.SHARED.branch(raw[18:22],function+18,'blx')
    need(math_target==DIV and sha(piece(model['segments'],DIV,484))==DIV_SHA,'historical helper actual ARM math')
    md=capstone.Cs(capstone.CS_ARCH_ARM,capstone.CS_MODE_THUMB);md.detail=True;aliases=[]
    for offset,pool,column in ((0x1C,0x34,0),(0x22,0x38,1),(0x28,0x3C,2)):
        ins=list(md.disasm(raw[offset:offset+2],function+offset));need(len(ins)==1 and ins[0].mnemonic=='ldr','historical chart PC load')
        mem=ins[0].operands[1].mem;target=((function+offset+4)&~3)+mem.disp
        need(mem.base==ARM_REG_PC and target==function+pool,'historical chart literal alias')
        pointer=struct.unpack_from('<I',raw,pool)[0]
        need(pointer==base+S.SHARED.CHART-T.OVERLAY_BASE+column,'historical sparse chart pointer')
        struct.pack_into('<I',normalized,pool,S.SHARED.CHART+column)
        aliases.append(dict(load_ram=hex(function+offset),pool_ram=hex(target),value_ram=hex(pointer)))
    normalized[18:22]=T.CONVERSION_PREIMAGE[18:22]
    need(bytes(normalized)==T.CONVERSION_PREIMAGE,'historical helper bounded correspondence')
    return dict(function_ram=hex(function),raw_sha256=sha(raw),bytes=64,rng_target=hex(rng_target),math_target=hex(math_target),
        aliases=aliases,comparison_only_fields=[18,52,56,60],executed_bytes_modified=False)


def command_seed_for_row(index):
    need(0<=index<325,'seed fixture row domain')
    return (((index<<16)-24691)*pow(1103515245,-1,2**32))&0xFFFFFFFF


def analyze(rom,v4,base,retail,language,work=None,build=None):
    import gc
    if work is not None:
        payload,compiler=compile_object(work);compiler['reused_build_verified']=False
    elif build is not None:
        compiler=verify_build(build);payload=(Path(build)/'native.bin').read_bytes()
    else:payload=None;compiler=dict(performed=False,reused_build_verified=False,reason='readback only; no ELF build claim')
    models={name:S.SHARED.read_image(p,language,name) for name,p in
        (('retail',retail),('base11',base),('v4',v4),('r4',rom))}
    records=[];regional=[]
    for name,x in models.items():
        need(sha(x['overlay'][COMMAND-T.OVERLAY_BASE:COMMAND_END-T.OVERLAY_BASE])==COMMAND_SHA,'native command448 continuity')
        need(sha(x['overlay'][RNG-T.OVERLAY_BASE:RNG_END-T.OVERLAY_BASE])==RNG_SHA,'native RNG44 continuity')
        if name!='r4':regional.append(dict(input=name,**old_helper(x)))
        records.append(x['record'])
    current=models['r4'];actual=current['overlay'][T.CONVERSION_SITE-T.OVERLAY_BASE:T.CONVERSION_SITE-T.OVERLAY_BASE+64]
    need(sha(actual)==T.PAYLOAD_SHA256 and (payload is None or actual==payload),'exact current replacement readback')
    before,_,before_record=S.engine_chart(v4,language,'v4');dense,cells,dense_record=S.engine_chart(rom,language,'r4')
    repaired,_=type_chart.patch_overlay(before)
    need(type_chart._chart_bytes(repaired)==type_chart._chart_bytes(dense),'modern chart source recipe replay')
    matrix,trailer=type_chart.rows(dense);rows=matrix+trailer;need(len(rows)==325,'complete selectable row domain')
    for site in (0x02240D32,0x02240DB0,0x02240E28):
        need(S.SHARED.branch(current['overlay'][site-T.OVERLAY_BASE:site-T.OVERLAY_BASE+4],site,'bl')==T.CONVERSION_SITE,'actual command helper caller')
    table=0x0226C6C8;slot=table+93*4
    need(struct.unpack_from('<I',current['overlay'],slot-T.OVERLAY_BASE)[0]==COMMAND|1,'actual opcode93 dispatch pointer')
    cpu=ConversionCPU(current['segments'],current['overlay'],dense);direct=[]
    for index,expected in enumerate(rows):
        result=cpu.observe(index=index,seed=0)
        need(result['result']==1 and result['row']==list(expected) and not result['rng_calls']
             and result['rows']==[index],'direct row domain/output/RNG neutrality')
        direct.append(result)
    randoms=[]
    for index,seed in ((325,0),(325,0x12345678),(325,0xFFFFFFFF),(65535,0),(65535,0x12345678),(65535,0xFFFFFFFF),(0xFFFFFFFF,0)):
        result=cpu.observe(index=index,seed=seed);row=(next_seed(seed)>>16)%325
        need(result['result']==0 and result['row']==list(rows[row]) and len(result['rng_calls'])==1
             and len(result['division_calls'])==1 and result['rows']==[row],'random row ABI/domain')
        randoms.append(result)
    commands=[]
    for defender in (3,8,10):
        index=rows.index((9,defender,5));seed=command_seed_for_row(index)
        result=cpu.observe(seed=seed,last_move_type=9)
        need(result['result']==0 and result['types']==[defender,defender] and result['snapshot_type']==defender
             and len(result['rng_calls'])==1 and result['helper_calls']==[65535],'Fairy resistance command')
        commands.append(dict(name='fairy_resistance_%d'%defender,result=result))
    index=rows.index((10,10,5));seed=command_seed_for_row(index);result=cpu.observe(seed=seed,last_move_type=10)
    need(result['types']==[10,10] and result['snapshot_type']==10 and len(result['rng_calls'])==1,'Fire control command')
    commands.append(dict(name='fire_control',result=result))
    result=cpu.observe(seed=0,last_move_type=16,current_types=(8,9));expected_seed=0
    for _ in range(1001):expected_seed=next_seed(expected_seed)
    need(result['result']==0 and result['types']==[0,0] and result['snapshot_type']==0
         and len(result['rng_calls'])==1001 and len(result['helper_calls'])==1326 and result['seed_after']==expected_seed
         and result['helper_calls'][1000:]==list(range(326)),'failed exhaustive command/native state transport')
    commands.append(dict(name='all_resistances_already_current',result=result))
    closure=cpu.closure();del cpu;gc.collect()
    mutant=bytearray(current['overlay']);at=0x0223BDA8-T.OVERLAY_BASE
    need(mutant[at:at+2]==bytes.fromhex('8150'),'seed-store counterproof preimage');mutant[at:at+2]=bytes.fromhex('c046')
    cpu=ConversionCPU(current['segments'],bytes(mutant),dense,attested=False)
    wrong_state=cpu.observe(index=325,seed=0,require_rng=False)
    need(wrong_state['row']==randoms[0]['row'] and wrong_state['result']==randoms[0]['result'] and wrong_state['seed_after']==0,'same-row wrong-state counterproof')
    try:require_rng_progress(wrong_state)
    except ValueError:pass
    else:raise ValueError('same-output RNG false success')
    del cpu;gc.collect()
    mutant=bytearray(current['overlay']);struct.pack_into('<I',mutant,T.CONVERSION_SITE-T.OVERLAY_BASE+52,112)
    cpu=ConversionCPU(current['segments'],bytes(mutant),dense,attested_helper=False)
    wrong_domain=cpu.observe(index=112,seed=0)
    need(wrong_domain['result']==0 and wrong_domain['row']!=list(rows[112]),'truncated-domain counterproof')
    del cpu;gc.collect()
    return dict(schema='conversion2-source-rom-v1',language=language,compile=compiler,inputs=records,old_helpers=regional,
        current_helper_sha256=T.PAYLOAD_SHA256,command_sha256=COMMAND_SHA,rng_sha256=RNG_SHA,divmod_sha256=DIV_SHA,
        chart=dict(v4=before_record,r4=dense_record,current_chart_sha256=sha(type_chart._chart_bytes(dense)),selectable_rows=325,
                   matrix_rows=322,controls=[list(row) for row in trailer]),
        dispatch=dict(opcode=93,table_ram=hex(table),slot_ram=hex(slot),target=hex(COMMAND|1),observed=False),
        helper_call_sites=['0x02240D32','0x02240DB0','0x02240E28'],
        direct_rows=direct,random_rows=randoms,commands=commands,closure=closure,
        counters=dict(same_row_wrong_rng_state=wrong_state,truncated_row_domain=wrong_domain),
        coverage=dict(direct_rows=325,random_cases=7,commands=5,counter_invocations=2),
        source_sha256={str(p.relative_to(SOURCE)):sha(p.read_bytes()) for p in
            (Path(__file__),Path(T.__file__),T.NATIVE,Path(type_chart.__file__),SOURCE/'sgp131/test_fairy_ai_rom.py')},
        limits=['five non-RNG service/query models; no actual script cursor/ability/precondition implementation',
                'command entered explicitly; opcode93 table static, not natural move/script dispatcher activation',
                'synthetic BattleSystem/context; no allocation, save, RNG session continuity, timing or hardware proof',
                'Grounding/FireFang/Rage and other same-owner helpers excluded; native MW toolchain not reconstructed'])


def main():
    import argparse
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('rom','v4','base','retail','json'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--language',choices=('EN','IT'),required=True)
    modes=p.add_mutually_exclusive_group(required=True)
    modes.add_argument('--work',type=Path,help='compile with protected toolchain and retain own-project ELF')
    modes.add_argument('--build',type=Path,help='verify and reuse canonical build; never compile or copy')
    modes.add_argument('--readback-only',action='store_true')
    args=p.parse_args();protected=[args.rom,args.v4,args.base,args.retail]
    for directory in (args.work,args.build):
        if directory is not None:protected.extend(directory/n for n in ('type-consumers.o','native.bin','compile-retained.json'))
    for file in protected:
        if args.json.resolve()==file.resolve() or (args.json.exists() and file.exists() and args.json.samefile(file)):
            p.error('--json must not replace inputs or build artifacts')
    result=analyze(args.rom,args.v4,args.base,args.retail,args.language,args.work,args.build)
    args.json.parent.mkdir(parents=True,exist_ok=True);args.json.write_text(json.dumps(result,indent=2)+'\n')
    print(args.language,'Conversion2:325 direct +7 random +5 commands +2 semantic counterexamples PASS')


if __name__=='__main__':main()
