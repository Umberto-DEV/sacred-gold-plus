#!/usr/bin/env python3
"""Attribute the U-turn snapshot and report the current unmarked fallback ABI failure."""
import importlib.util
import json
import mmap
from pathlib import Path
import struct

spec=importlib.util.spec_from_file_location('uturn_shared',Path(__file__).with_name('attribuisci.py'))
G=importlib.util.module_from_spec(spec);spec.loader.exec_module(G)
from sgp131 import uturn_flinch_r4 as U,uturn_script as SCRIPT
from sgp131 import test_type_consumers as C
from unicorn import UC_HOOK_CODE,UC_HOOK_MEM_READ,UC_HOOK_MEM_WRITE
from unicorn.arm_const import (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3,
    UC_ARM_REG_SP,UC_ARM_REG_LR,UC_ARM_REG_PC,UC_ARM_REG_CPSR)
need,sha=G.need,G.sha
CTX,BS=C.CTX,C.BATTLE_SYSTEM
STACK,STOP,CACHE=0x023B8000,0x023F0000,0x023A0000
ABILITY,HELD,ITEMVAR=0x022527CC,0x022555EC,0x02257E74
CACHE_SHA='276334b390f6072348f3de8c1971f60290bd350b60f57c19d0c7c6e6e09d908f'
MOVE_CACHE_SHA='c64da77ab5f1158520a0f17905d457f3104c32aae1513c622cec0daa9f3e1588'
NATIVE_WRITERS=((0x0224C73C,18,'ef761f31ba4750ad37cabcf07eca8e50161ecd81f2c8a1ea34e1cfe31222af62'),
    (0x0224C782,20,'d5e43c0c372b52205c2ef9358abcf806df386e4698d9f5e5c39f460471a664ce'),
    (0x0224CA1C,20,'58beb76f01aca9550cf02cbe84de8f1b3ab8ef19698ded8b30b485443a5361d2'),
    (0x0224CA34,18,'387911382e98a056c37fdc0a3a75cabb1af82cc7d98e730d040c2bd5af865b4d'))
WINDOWS=(
    (HELD,48,'130efe5affedc0a55af3dc086e60ec0f714bfab8f9cd3524a75a7417e88e7a89',((HELD,0x02255618),)),
    (U.GET_EFFECT,20,'e8d18db3ecd14ff4349bdfe20b17046fe13ac6d2ad2b17577e988319229a70ff',((U.GET_EFFECT,0x02255844),)),
    (U.GET_MODIFIER,76,'0f6ef687253851d32d5d8208c4f185621722af043e27194ac1683b124b32ac68',((U.GET_MODIFIER,0x02255886),)),
    (ITEMVAR,36,'b36d37794c17bf965750821244c83a5f6e9db16cfba80b3c253d89f3c951285f',((ITEMVAR,0x02257E94),)),
    (0x02077C18,152,'95199d54d478a42b955773da6ee972ed4380d1dd12bde6d29539467951ab5243',((0x02077C18,0x02077C28),(0x02077C30,0x02077C42),(0x02077C8A,0x02077C8E))),
    (0x02078160,8,'87557deab6cc3549ce6b09bc51f6514ff18103a93b774e1214e84808e1fa1034',((0x02078160,0x02078168),)),
    (0x02077DAC,156,'24675eabdfcf087e29accb67b413cd4e569e279f9e7bb27a06e57f376cbb824d',((0x02077DAC,0x02077DBE),(0x02077DE0,0x02077DE8))))


def take(image,address,size):return bytes(image[address-U.OVERLAY_BASE:address-U.OVERLAY_BASE+size])


def read_resources(rom,model):
    spec=importlib.util.spec_from_file_location('uturn_raw_narc',G.SOURCE/'features/borsa/tools/attribuisci.py')
    reader=importlib.util.module_from_spec(spec);spec.loader.exec_module(reader)
    with Path(rom).open('rb') as handle,mmap.mmap(handle.fileno(),0,access=mmap.ACCESS_READ) as raw:
        scripts,srec=reader.raw_archive(raw,SCRIPT.ARCHIVE);items,irec=reader.raw_archive(raw,'a/0/1/7');moves,mrec=reader.raw_archive(raw,'a/0/1/1')
    need(srec['file_id']==130 and len(scripts)==297,'battle script archive geometry')
    need(irec['file_id']==146 and len(items)==516 and all(len(b)==34 for b in items),'actual item archive geometry')
    need(mrec['file_id']==140 and len(moves)==471 and all(len(b)==16 for b in moves),'actual move archive geometry')
    need(moves[33][11]&32 and not moves[44][11]&32,'actual Tackle/Bite item-flinch eligibility')
    itemmap={item:struct.unpack('<4H',G.piece(model['segments'],0x02100194+8*item,8))[0] for item in (0,221,327)}
    need(itemmap=={0:0,221:199,327:305},'actual item ID→NARC member mapping')
    values={item:(items[member][2],items[member][3]) for item,member in itemmap.items()}
    need(values=={0:(0,0),221:(56,10),327:(56,10)},'actual flinch item attributes')
    irec.update(selected_items={str(item):dict(member=member,sha256=sha(items[member]),effect=values[item][0],modifier=values[item][1]) for item,member in itemmap.items()},
                cache_stride=36,raw_record_bytes=34,cache_padding_fixture_bytes=2)
    # Native cache addressing uses36; the preloader itself is outside this case.
    cache=b''.join(b+bytes(2) for b in items)
    move_cache=b''.join(moves[:468]);mrec.update(cache_bytes=7488,cache_sha256=sha(move_cache),eligibility={str(i):dict(sha256=sha(moves[i]),flags_byte=moves[i][11],item_flinch=bool(moves[i][11]&32)) for i in (33,44)})
    return dict(script=scripts[175],producer=scripts[175][SCRIPT.INSERT_AT:SCRIPT.INSERT_AT+104],cache=cache,itemmap=itemmap,move_cache=move_cache,
                record=dict(script_archive=srec,script_member=175,script_bytes=len(scripts[175]),script_sha256=sha(scripts[175]),items=irec,moves=mrec,cache_sha256=sha(cache)))


def slot_read(rom,model):
    with Path(rom).open('rb') as handle,mmap.mmap(handle.fileno(),0,access=mmap.ACCESS_READ) as raw:
        view=G.S.SHARED.gifts_audit.Arm9View(raw);block=view.read(U.SLOT_START,192)
        need(block==G.piece(model['segments'],U.SLOT_START,192),'specific C8 raw/ndspy ARM9 mapping')
        return dict(slot_ram=hex(U.SLOT_START),slot_rom_offset=hex(view.offset(U.SLOT_START,192)),helper_ram=hex(U.HELPER_ADDRESS),
                    helper_rom_offset=hex(view.offset(U.HELPER_ADDRESS,128)),foreign64_sha256=sha(block[:64]),helper128_sha256=sha(block[64:]),
                    helper68_sha256=sha(block[64:132]),last60_zero=block[132:]==bytes(60))


def compile_object(work):
    work=Path(work);work.mkdir(parents=True,exist_ok=True);payload,receipt=U.compile_native(work,retain_object=True)
    obj=(work/receipt['retained_object']).read_bytes();loader=U._module(G.SOURCE/'features/options/tools/carica_text.py','uturn_attribution_elf')
    raw,symbols=loader.load_text(obj,U.HELPER_ADDRESS,('uturn_snapshot_effect','uturn_effect_live_call','uturn_snapshot_modifier','uturn_modifier_live_call'))
    need(symbols['uturn_snapshot_effect']==U.EFFECT_ENTRY and symbols['uturn_snapshot_modifier']==U.MODIFIER_ENTRY,'U-turn ELF entry geometry')
    for name,offset,target in (('uturn_effect_live_call',24,U.GET_EFFECT),('uturn_modifier_live_call',62,U.GET_MODIFIER)):
        need(symbols[name]&~1==U.HELPER_ADDRESS+offset and raw[offset:offset+4]==bytes.fromhex('00f000f8'),'U-turn ELF external placeholder')
        need(G.S.SHARED.branch(payload[offset:offset+4],U.HELPER_ADDRESS+offset,'bl')==target,'U-turn external BL target')
    need(all(a==b for i,(a,b) in enumerate(zip(raw,payload)) if not (24<=i<28 or 62<=i<66)),'U-turn changes outside two external fields')
    proof=dict(performed=True,**receipt,builder_sha256=sha(Path(U.__file__).read_bytes()),loader_sha256=sha((G.SOURCE/'features/options/tools/carica_text.py').read_bytes()),
               symbols={k:hex(v) for k,v in symbols.items()},post_link_changed_offsets=[i for i,(a,b) in enumerate(zip(raw,payload)) if a!=b])
    for name,data in (('native.bin',payload),('compile-retained.json',(json.dumps(proof,indent=2)+'\n').encode())):
        p=work/name;need(not p.is_symlink() and (not p.exists() or p.is_file() and p.read_bytes()==data),'existing U-turn artifact differs; use fresh directory')
        if not p.exists():p.write_bytes(data)
    return payload,proof


LEGACY_SOURCE_SHA = 'e191b1c267282826beab3a20b18eb53375538b396dcdcbda2c6a12407e23422a'
LEGACY_BUILDERS = frozenset((
    'be1e3fbce13842afd759a159d88421f38f39335c498df610973dc4aa777ae7fa',
    'e7b5eef0f9aacf0934bf6b4fd116944da41ca950c4d522de976bb2e05af38760',
))


def verify_build(work):
    work=Path(work);proof=json.loads((work/'compile-retained.json').read_text());obj=(work/'uturn.o').read_bytes();payload=(work/'native.bin').read_bytes()
    need(sha(U.NATIVE.read_bytes())==proof['source_sha256']==LEGACY_SOURCE_SHA and proof['payload_sha256']==U.HELPER_SHA256 and proof['builder_sha256'] in LEGACY_BUILDERS and sha(Path(U.__file__).read_bytes()) in LEGACY_BUILDERS,'U-turn source/builder drift')
    need(proof['loader_sha256']==sha((G.SOURCE/'features/options/tools/carica_text.py').read_bytes()),'U-turn loader drift')
    need(proof['compiler']==dict(version=U.COMPILER_VERSION,executable_sha256=U.COMPILER_SHA256,flags=list(U.FLAGS)),'U-turn compiler receipt')
    need(sha(obj)==proof['object_sha256'] and sha(payload)==proof['payload_sha256']==U.HELPER_SHA256,'U-turn retained artifacts')
    loader=U._module(G.SOURCE/'features/options/tools/carica_text.py','uturn_reused_elf');raw,_=loader.load_text(obj,U.HELPER_ADDRESS,('uturn_snapshot_effect','uturn_snapshot_modifier'))
    rebuilt=bytearray(raw)
    from sgp12.rom import bl_thumb
    for offset,target in ((24,U.GET_EFFECT),(62,U.GET_MODIFIER)):rebuilt[offset:offset+4]=bl_thumb(U.HELPER_ADDRESS+offset,target)
    need(bytes(rebuilt)==payload,'U-turn reused ELF→payload')
    return payload,dict(performed=False,verified_retained_build=proof)


def counter_image(model,variant):
    result=dict(model);image=bytearray(model['overlay']);segments=list(model['segments'])
    if variant=='old_hooks':
        need(take(image,U.FUNCTION,184)==U.FUNCTION_POSTIMAGE,'U-turn old-hook fixture preimage')
        at=U.FUNCTION-U.OVERLAY_BASE;image[at:at+184]=U.FUNCTION_PREIMAGE
    elif variant=='no_clear':
        changed=[]
        for address,data in segments:
            if address<=U.HELPER_ADDRESS and U.HELPER_ADDRESS+68<=address+len(data):
                data=bytearray(data);at=U.HELPER_ADDRESS-address
                need(sha(data[at:at+68])==U.HELPER_SHA256,'U-turn clear counter preimage')
                data[at+52:at+54]=bytes.fromhex('c046');data=bytes(data)
            changed.append((address,data))
        segments=changed
    else:raise ValueError('explicit U-turn counter variant')
    result.update(overlay=bytes(image),segments=segments);return result


def require_consumed(result):need(result['snapshot_after']==0,'marked U-turn snapshot not consumed')


class NativeFlinch(C.FlinchBench):
    """Installed parent/helper and item/RNG/division code; two declared services.

    The producer is a source-word interpreter using real native getter results.
    It is not native battle-script dispatch. The known fallback ABI violation is
    recorded, then its actual getter/data path is executed rather than stubbed.
    """
    def __init__(self,model,resources,*,variant='current',code_profile='legacy68'):
        from sgp131 import uturn_flinch as CURRENT
        profiles={'legacy68': (68,U.HELPER_SHA256,30,68,52),
                  'current74': (74,CURRENT.HELPER_SHA256,32,74,64)}
        need(code_profile in profiles,'explicit U-turn code profile')
        length,digest,effect_end,modifier_end,clear=profiles[code_profile]
        need(code_profile=='legacy68' or variant=='current','counter variant requires legacy profile')
        self.code_profile=code_profile;self.helper_extent=(effect_end,modifier_end);self.clear_offset=clear
        image=model['overlay'];helper=bytearray(G.piece(model['segments'],U.HELPER_ADDRESS,128))
        need(variant in ('current','old_hooks','no_clear'),'explicit U-turn variant')
        if variant=='no_clear':
            need(helper[52:54]==bytes.fromhex('c046'),'clear counter fixture')
            helper[52:54]=bytes.fromhex('9c50')
        need(sha(helper[:length])==digest and helper[length:]==bytes(128-length),'profiled U-turn helper owner identity')
        need(take(image,U.FUNCTION,184)==(U.FUNCTION_PREIMAGE if variant=='old_hooks' else U.FUNCTION_POSTIMAGE),'whole U-turn parent identity')
        for address,n,digest,_ in WINDOWS:
            raw=take(image,address,n) if address>=U.OVERLAY_BASE else G.piece(model['segments'],address,n)
            need(sha(raw)==digest,'U-turn native item closure '+hex(address))
        need(sha(take(image,G.RNG,44))==G.RNG_SHA and sha(G.piece(model['segments'],G.S.DIV,524))==G.S.DIV_SHA,'qualified U-turn RNG/signed division')
        need(resources['producer']==SCRIPT.INSERT and len(resources['cache'])==516*36 and len(resources['move_cache'])==7488,'U-turn producer/cache fixture geometry')
        need(sha(resources['cache'])==CACHE_SHA and sha(resources['move_cache'])==MOVE_CACHE_SHA and resources['itemmap']=={0:0,221:199,327:305},'U-turn actual resource binding')
        super().__init__(image)
        self.uc.mem_map(0x01FF8000,0x8000);self.uc.mem_map(0x027E0000,0x20000)
        self.frozen=[(a,bytes(b)) for a,b in model['segments']]+[(U.OVERLAY_BASE,bytes(image))]
        for a,b in self.frozen:self.uc.mem_write(a,b)
        self.resources=resources;self.variant=variant;self.cache=resources['cache'];self.itemmap=resources['itemmap'];self.current=None
        self.uc.mem_write(CACHE,self.cache+b'\xA5'*8)
        self.uc.hook_add(UC_HOOK_CODE,self._code);self.uc.hook_add(UC_HOOK_MEM_READ,self._read);self.uc.hook_add(UC_HOOK_MEM_WRITE,self._write)

    def reg(self,r):return self.uc.reg_read(r)

    def _seam(self,u,address,size,unused):
        if address in (U.GET_EFFECT,U.GET_MODIFIER,G.RNG,G.S.DIV):return
        if address==C.READ_BATTLE_SCRIPT:
            need([self.reg(r) for r in (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2)]==[CTX,1,14],'flinch script transport ABI')
        return super()._seam(u,address,size,unused)

    def _code(self,u,address,size,unused):
        r=self.current
        if r is None:return
        r['instructions']+=1;need(r['instructions']<=10000,'U-turn instruction budget')
        sp=self.reg(UC_ARM_REG_SP);thumb=bool(self.reg(UC_ARM_REG_CPSR)&32);r['stack_depth']=max(r['stack_depth'],STACK-sp)
        for key in ('pending_item','pending_rng','pending_div'):
            call=r.get(key)
            if call and address==call['return_pc']:
                need(sp==call['sp'] and [self.reg(v) for v in G.SAVED]==call.pop('saved'),'U-turn native return ABI')
                if key=='pending_item':
                    call['value']=self.reg(UC_ARM_REG_R0)
                    need(call['value']==self.cache[36*call['member']+call['attribute']+1],'actual native item attribute value');r['item_queries'].append(call)
                elif key=='pending_rng':
                    call.update(after=self.word(BS+G.SEED_OFFSET),value=self.reg(UC_ARM_REG_R0))
                    need(call['after']==G.next_seed(call['before']) and call['value']==call['after']>>16,'actual U-turn RNG transition');r['rng_calls'].append(call)
                else:
                    call.update(quotient=self.reg(UC_ARM_REG_R0),remainder=self.reg(UC_ARM_REG_R1))
                    need((call['quotient'],call['remainder'])==divmod(call['numerator'],100),'actual U-turn divmod');r['division_calls'].append(call)
                r[key]=None
        if address==ABILITY:
            need(thumb and [self.reg(v) for v in (UC_ARM_REG_R0,UC_ARM_REG_R1)]==[CTX,self.attacker],'ability query ABI')
            r['models'].append(dict(name='ability',result=self.active_ability));self._return(u,self.active_ability);return
        if address==C.READ_BATTLE_SCRIPT:r['models'].append(dict(name='script transport'));return
        if G.S.DIV<=address<G.S.DIV_END:need(not thumb and size==4,'U-turn native ARM division ISA')
        else:
            need(thumb and size in (2,4),'U-turn native Thumb ISA')
            allowed=U.FUNCTION<=address and address+size<=0x0224E11A
            allowed|=(U.HELPER_ADDRESS<=address and address+size<=U.HELPER_ADDRESS+self.helper_extent[0]) or (U.HELPER_ADDRESS+32<=address and address+size<=U.HELPER_ADDRESS+self.helper_extent[1])
            allowed|=G.RNG<=address and address+size<=0x0223BDB6
            allowed|=any(lo<=address and address+size<=hi for _,_,_,ranges in WINDOWS for lo,hi in ranges)
            need(allowed,'unexpected U-turn code/table/padding PC '+hex(address))
        r['code'].add((address,size,thumb))
        if address in (U.GET_EFFECT,U.GET_MODIFIER):
            args=[self.reg(v) for v in (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2)]
            if address==U.GET_EFFECT:
                need(args[:2]==[CTX,self.attacker],'native effect getter ABI');self.calls['effect']+=1
            else:
                self.calls['modifier']+=1
                if args!=[CTX,self.attacker,0]:r['modifier_abi_issues'].append(dict(args=args,expected=[CTX,self.attacker,0]))
        if address==ITEMVAR:
            item,attr=self.reg(UC_ARM_REG_R1),self.reg(UC_ARM_REG_R2)
            need(self.reg(UC_ARM_REG_R0)==CTX and item in self.itemmap and attr in (1,2) and r.get('pending_item') is None,'native item lookup domain')
            r['pending_item']=dict(item=item,attribute=attr,member=self.itemmap[item],return_pc=self.reg(UC_ARM_REG_LR)&~1,sp=sp,saved=[self.reg(v) for v in G.SAVED])
        if address==0x02078160:
            need(self.reg(UC_ARM_REG_R0)==CACHE and self.reg(UC_ARM_REG_R1) in self.itemmap.values(),'native item cache address ABI/bounds')
        if address==0x02077DAC:
            need(self.reg(UC_ARM_REG_R0) in [CACHE+36*m for m in self.itemmap.values()] and self.reg(UC_ARM_REG_R1) in (1,2),'native item decoder ABI/bounds')
        if address==G.RNG:
            need(self.reg(UC_ARM_REG_R0)==BS and r.get('pending_rng') is None,'native U-turn RNG ABI');self.calls['rng']+=1
            r['pending_rng']=dict(before=self.word(BS+G.SEED_OFFSET),return_pc=self.reg(UC_ARM_REG_LR)&~1,sp=sp,saved=[self.reg(v) for v in G.SAVED])
        if address==G.S.DIV:
            need(self.reg(UC_ARM_REG_R1)==100 and r.get('pending_div') is None,'native flinch denominator')
            r['pending_div']=dict(numerator=self.reg(UC_ARM_REG_R0),return_pc=self.reg(UC_ARM_REG_LR)&~1,sp=sp,saved=[self.reg(v) for v in G.SAVED])

    def _read(self,u,access,address,size,value,unused):
        if self.current and CACHE<=address<CACHE+len(self.cache)+8:
            offset=address-CACHE
            need(size==1 and offset<len(self.cache) and offset%36 in (2,3),'item cache read outside attributes1/2')
            self.current['cache_reads'].append(dict(offset=offset,value=int.from_bytes(u.mem_read(address,size),'little')))

    def _write(self,u,access,address,size,value,unused):
        r=self.current
        if r is None:return
        stack=STACK-4096<=address and address+size<=STACK
        state=r['phase']=='parent' and size==4 and address in (CTX+0x2EC+28*self.attacker,CTX+8,CTX+12,CTX+0x88,CTX+0x94,BS+G.SEED_OFFSET)
        need(stack or state,'U-turn write outside stack/declared state '+hex(address))
        pc=self.reg(UC_ARM_REG_PC)&~1
        if U.HELPER_ADDRESS<=pc<U.HELPER_ADDRESS+128 and not stack:
            need(pc==U.HELPER_ADDRESS+self.clear_offset and address==CTX+0x2EC+28*self.attacker and size==4 and value==0,'U-turn helper clear store')

    def _execute(self,entry,args,phase):
        u=self.uc;u.mem_write(STACK-4104,b'\xA5'*8+bytes(4096)+b'\xA5'*256)
        for reg,value in zip(G.SAVED,G.COOKIES):u.reg_write(reg,value)
        for reg,value in zip((UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3),args):u.reg_write(reg,value)
        u.reg_write(UC_ARM_REG_SP,STACK);u.reg_write(UC_ARM_REG_LR,STOP|1)
        self.calls=dict(effect=0,modifier=0,rng=0,script=[])
        r=dict(phase=phase,instructions=0,stack_depth=0,item_queries=[],modifier_abi_issues=[],rng_calls=[],division_calls=[],cache_reads=[],models=[],code=set())
        ctx_before=bytes(u.mem_read(CTX,0x4000));bs_before=bytes(u.mem_read(BS,0x3000));self.current=r
        try:u.emu_start(entry|1,STOP,count=10001)
        finally:self.current=None
        need(self.reg(UC_ARM_REG_PC)==STOP and self.reg(UC_ARM_REG_SP)==STACK and self.reg(UC_ARM_REG_CPSR)&32 and [self.reg(v) for v in G.SAVED]==G.COOKIES,'U-turn outer return ABI')
        need(all(r.get(k) is None for k in ('pending_item','pending_rng','pending_div')),'unfinished native U-turn call')
        allowed=set()
        if phase=='parent':
            for offset in (0x2EC+28*self.attacker,8,12,0x88,0x94):allowed.update(range(offset,offset+4))
        after=bytes(u.mem_read(CTX,0x4000));need(all(a==b for i,(a,b) in enumerate(zip(ctx_before,after)) if i not in allowed),'U-turn changed unrelated context')
        bs_after=bytes(u.mem_read(BS,0x3000));need(all(a==b for i,(a,b) in enumerate(zip(bs_before,bs_after)) if not (phase=='parent' and G.SEED_OFFSET<=i<G.SEED_OFFSET+4)),'U-turn changed unrelated BS state')
        need(bytes(u.mem_read(CACHE,len(self.cache)+8))==self.cache+b'\xA5'*8,'U-turn mutated item cache/canary')
        need(bytes(u.mem_read(STACK-4104,8))==b'\xA5'*8 and bytes(u.mem_read(STACK,256))==b'\xA5'*256,'U-turn stack/caller canary')
        need(all(bytes(u.mem_read(a,len(b)))==b for a,b in self.frozen),'U-turn mutated initialized code/data')
        r.update(result=self.reg(UC_ARM_REG_R0),calls=dict(self.calls));r['code']=[dict(ram=hex(a),bytes=n,thumb=t) for a,n,t in sorted(r['code'])];return r

    def _produce(self,outgoing,klutz,embargo):
        self._word(CTX+0x2DB8+192*self.attacker,outgoing);self.active_ability=103 if klutz else 0
        self._word(CTX+0x2DCC+192*self.attacker,(1<<19) if embargo else 0)
        vars={68:0,9:0};words=struct.unpack('<26I',self.resources['producer']);pc=0;calls=[]
        while pc<26:
            opcode=words[pc];pc+=1
            if opcode==50:
                operation,var,value=words[pc:pc+3];pc+=3
                need(var in vars and operation in (7,10,14),'snapshot UpdateVar domain')
                vars[var]=value if operation==7 else vars[var]|value if operation==10 else (vars[var]<<value)&0xFFFFFFFF
            elif opcode==166:
                flag,side,effect,skip=words[pc:pc+4];pc+=4;need((flag,side,effect,skip)==(0,1,56,2),'snapshot effective check')
                call=self._execute(U.GET_EFFECT,(CTX,self.attacker,0,0),'getter');calls.append(call)
                if call['result']==56:pc+=skip
            elif opcode==59:pc+=words[pc]+1
            elif opcode==168:
                side,var=words[pc:pc+2];pc+=2;need((side,var)==(1,9),'snapshot modifier command')
                call=self._execute(U.GET_MODIFIER,(CTX,self.attacker,0,0),'getter');calls.append(call);vars[9]=call['result']
            elif opcode==57:
                operation,dest,source=words[pc:pc+3];pc+=3;need((operation,dest,source)==(10,68,9),'snapshot OR variables');vars[dest]|=vars[source]
            else:raise ValueError('unsupported snapshot opcode')
        need(pc==26 and 0<=vars[68]<=0x1FFFF,'snapshot word domain')
        self._word(CTX+0x134,vars[9]);self._word(CTX+0x2EC+28*self.attacker,vars[68])
        return dict(mode='source-word interpreter, native item getters; not native script dispatch',snapshot=vars[68],native_getters=calls)

    def observe(self,*,pivot=True,outgoing=221,incoming=0,roll=9,attacker=0,target=1,klutz=False,embargo=False,move_status=0,damage=1,eligible=True,target_hp=100,ordinary_word=0):
        need(type(pivot) is bool and type(outgoing) is int and outgoing in self.itemmap and type(incoming) is int and incoming in self.itemmap and type(roll) is int and 0<=roll<65536 and type(attacker) is int and 0<=attacker<4 and type(target) is int and target in (0,1,2,3,255),'U-turn fixture domain')
        need(all(type(v) is bool for v in (klutz,embargo,eligible)) and all(type(v) is int and 0<=v<=0xFFFFFFFF for v in (move_status,damage,target_hp)),'U-turn state field domain')
        need(type(ordinary_word) is int and -(1<<31)<=ordinary_word<=0xFFFFFFFF,'native signed field fixture domain')
        u=self.uc;u.mem_write(CTX,bytes(0x4000));u.mem_write(BS,bytes(0x3000));self.attacker=attacker
        u.mem_write(CTX+0x3DE,self.resources['move_cache'])
        self._word(CTX+0x2120,CACHE);self._word(CTX+0x64,attacker);self._word(CTX+0x6C,target)
        self._word(CTX+8,8);self._word(CTX+0x216C,move_status);self._word(CTX+0x3044,33 if eligible else 44)
        self._word(CTX+0x2EC+28*attacker,ordinary_word)
        if target!=255:
            self._word(CTX+0x2D8+28*target,damage);self._word(CTX+0x2D8C+192*target,target_hp)
        producer=self._produce(outgoing,klutz,embargo) if pivot else None
        self._word(CTX+0x2DB8+192*attacker,incoming);self._word(CTX+0x2DCC+192*attacker,0);self.active_ability=0
        seed=((roll<<16)-24691)*pow(1103515245,-1,1<<32)&0xFFFFFFFF;self._word(BS+G.SEED_OFFSET,seed)
        result=self.repeat_parent();result.update(pivot=pivot,outgoing=outgoing,incoming=incoming,roll=roll,producer=producer,seed_before=seed)
        return result

    def repeat_parent(self):
        snapshot=self.word(CTX+0x2EC+28*self.attacker);seed=self.word(BS+G.SEED_OFFSET)
        result=self._execute(U.FUNCTION,(BS,CTX,0,0),'parent')
        need(result['result'] in (0,1),'native flinch boolean')
        result.update(flinch=bool(result['result']),snapshot_before=snapshot,snapshot_after=self.word(CTX+0x2EC+28*self.attacker),seed_before=seed,seed_after=self.word(BS+G.SEED_OFFSET))
        need(len(result['rng_calls'])==len(result['division_calls'])==result['calls']['rng']<=1,'flinch RNG/division call count')
        need(result['seed_after']==(G.next_seed(seed) if result['rng_calls'] else seed),'flinch final seed/neutral gate')
        return result


def analyze(rom,v4,base,retail,language,payload,compiler):
    import gc
    models={name:G.S.SHARED.read_image(path,language,name) for name,path in (('retail',retail),('base11',base),('v4',v4),('r4',rom))}
    windows=[]
    for role,model in models.items():
        raw=take(model['overlay'],U.FUNCTION,184);normal=bytearray(raw);address=int(model['record']['overlays'][1]['ram'],16)+U.FUNCTION-U.OVERLAY_BASE;fields=[]
        if role=='retail' and language=='IT':
            # Verify the regional BLX against its invariant ARM target, then
            # normalize its four-byte field using the canonical preimage.
            need(G.S.SHARED.branch(raw[0x52:0x56],address+0x52,'blx')==G.S.DIV,'retail IT flinch ARM target')
            need(sha(G.piece(model['segments'],G.S.DIV,524))==G.S.DIV_SHA,'retail IT flinch ARM division identity')
            normal[0x52:0x56]=U.FUNCTION_PREIMAGE[0x52:0x56];fields=[dict(offset='0x52',target=hex(G.S.DIV))]
        need(bytes(normal)==(U.FUNCTION_POSTIMAGE if role=='r4' else U.FUNCTION_PREIMAGE),'entire U-turn parent correspondence')
        windows.append(dict(input=role,ram=hex(address),bytes=184,sha256=sha(raw),comparison_only_fields=fields))
    writers=[]
    for role,model in models.items():
        shift=int(model['record']['overlays'][1]['ram'],16)-U.OVERLAY_BASE
        for address,n,digest in NATIVE_WRITERS:
            need(sha(take(model['overlay'],address,n))==digest,'native signed field writer '+role)
            writers.append(dict(input=role,ram=hex(address+shift),bytes=n,sha256=digest,activation='static, native signed field ownership; writer not executed'))
    current=models['r4'];need(payload==G.piece(current['segments'],U.HELPER_ADDRESS,68),'compiled helper matches installed bytes')
    variable_bindings=[]
    for var,address,n,digest in ((9,0x02245602,8,'dedbb58e8dcd4478551b32597c68c1954cf41976151ae1cfa28b4db2598bd236'),
                                 (68,0x02245810,16,'f4673d6496e3575be129c22341a240bfe320b7bd9644f68617016904961f452f')):
        need(sha(take(current['overlay'],address,n))==digest,'native script variable case body')
        relative=struct.unpack('<h',take(current['overlay'],0x0224553E+2*var,2))[0]
        need(0x02245540+relative==address,'native script variable jump-table binding')
        variable_bindings.append(dict(var=var,case_ram=hex(address),bytes=n,sha256=digest,activation='static, pointer function not executed'))
    controller=take(current['overlay'],0x0224CAA4,0x1D4)
    need(sha(controller)=='cd50feef51bf0b3baa916cdf82ed907d94d4b57b44ecebff84b4b54f62970e1d','current AfterDamage caller window')
    callers=[]
    for site in (0x0224CB8A,0x0224CC64):
        raw=take(current['overlay'],site,4);need(G.S.SHARED.branch(raw,site,'bl')==U.FUNCTION,'current AfterDamage→flinch BL')
        callers.append(dict(site=hex(site),target=hex(U.FUNCTION),activation='static AfterDamage message-type0/1,state6; outer controller not executed'))
    replay,_=U.patch_overlay(models['v4']['overlay']);need(take(replay,U.FUNCTION,184)==take(current['overlay'],U.FUNCTION,184),'source two-seam parent reconstruction')
    old_resources=read_resources(v4,models['v4']);resources=read_resources(rom,current)
    need(SCRIPT.patch_member(old_resources['script'])==resources['script'],'exact source script-member reconstruction')
    resident=dict(v4=slot_read(v4,models['v4']),r4=slot_read(rom,current))
    need(G.piece(models['v4']['segments'],U.HELPER_ADDRESS,128)==bytes(128) and G.piece(current['segments'],U.HELPER_ADDRESS,128)==payload+bytes(60),'U-turn tail128 reconstruction')
    cases=[('rock_out_empty_in',dict(outgoing=221,incoming=0)),('fang_out_empty_in',dict(outgoing=327,incoming=0)),('empty_out_rock_in',dict(outgoing=0,incoming=221)),
           ('roll10',dict(roll=10)),('no_damage',dict(damage=0)),('move_failure',dict(move_status=1)),('no_target',dict(target=255)),('not_eligible',dict(eligible=False)),
           ('target_ko',dict(target_hp=0)),('klutz',dict(klutz=True)),('embargo',dict(embargo=True))]
    runs=[]
    for name,options in cases:
        result=NativeFlinch(current,resources).observe(**options);require_consumed(result)
        required=name in ('rock_out_empty_in','fang_out_empty_in')
        need(result['flinch']==required and not result['modifier_abi_issues'],'marked flinch scenario '+name)
        runs.append(dict(name=name,result=result));gc.collect()
    failures=[]
    for attacker in range(4):
        live=NativeFlinch(current,resources).observe(pivot=False,incoming=221,attacker=attacker,target=(attacker+1)%4)
        old=NativeFlinch(counter_image(current,'old_hooks'),resources,variant='old_hooks').observe(pivot=False,incoming=221,attacker=attacker,target=(attacker+1)%4)
        need(live['modifier_abi_issues'] and not live['flinch'] and old['flinch'],'observed fallback ABI/semantic failure')
        failures.append(dict(attacker=attacker,current=live,native_baseline=old));gc.collect()
    counter=NativeFlinch(counter_image(current,'no_clear'),resources,variant='no_clear').observe()
    need(counter['flinch'] and counter['snapshot_after']==0x10A38,'same-output no-clear counterexample')
    try:require_consumed(counter)
    except ValueError:pass
    else:raise ValueError('false snapshot lifetime success')
    collision_options=dict(pivot=False,incoming=0,ordinary_word=-200,damage=0xFFFFFF38,roll=99)
    collision=NativeFlinch(current,resources).observe(**collision_options)
    collision_old=NativeFlinch(counter_image(current,'old_hooks'),resources,variant='old_hooks').observe(**collision_options)
    need(collision['flinch'] and collision['snapshot_after']==0 and not collision['modifier_abi_issues'] and not collision_old['flinch'] and collision_old['snapshot_after']==0xFFFFFF38,'native negative field/marker collision')
    return dict(schema='uturn-source-rom-v1',language=language,inputs=[m['record'] for m in models.values()],compile=compiler,parent_windows=windows,resident=resident,callers=callers,native_field_writers=writers,script_variable_bindings=variable_bindings,
        resources=resources['record'],runs=runs,fallback_failures=failures,no_clear_counterproof=counter,marker_collision=dict(current=collision,native_baseline=collision_old),
        compatibility_gates=dict(marked_snapshot=True,ordinary_fallback_abi=False,ordinary_flinch_equivalence=False,marker_authentication=False),
        source_sha256={str(p.relative_to(G.SOURCE)):sha(p.read_bytes()) for p in (Path(__file__),Path(U.__file__),Path(SCRIPT.__file__),U.NATIVE,G.SOURCE/'sgp131/test_type_consumers.py')},
        limits=['source-word producer interpreter uses native getters, but native battle-script dispatch is unqualified',
                'ability and script-loading transports are models; item cache prepared from raw34-byte records with2synthetic padding bytes',
                'native getters/itemlookup/RNG/division execute; invalid flags observed only on bounded recorded inputs',
                'isolated TryItemFlinch, not natural pivot/UI/controller/whole battle/SAVE/cold/device/timing',
                'current fallback defect is reported, not repaired; CLI exits1 for failed compatibility gates'])


def main():
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('rom','v4','base','retail','json'):parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--language',choices=('EN','IT'),required=True)
    group=parser.add_mutually_exclusive_group(required=True);group.add_argument('--work',type=Path);group.add_argument('--build',type=Path);group.add_argument('--readback-only',action='store_true');args=parser.parse_args()
    protected=[args.rom,args.v4,args.base,args.retail];artifact_dir=args.work or args.build
    if artifact_dir:protected.extend(artifact_dir/name for name in ('uturn.o','native.bin','compile-retained.json'))
    for path in protected:
        if args.json.resolve()==path.resolve() or (args.json.exists() and path.exists() and args.json.samefile(path)):parser.error('--json must not replace an input or retained artifact')
    if args.work:payload,compiler=compile_object(args.work)
    elif args.build:payload,compiler=verify_build(args.build)
    else:
        model=G.S.SHARED.read_current(args.rom,args.language);payload=G.piece(model['segments'],U.HELPER_ADDRESS,68);compiler=dict(performed=False,available=False,reason='explicit readback-only mode')
    result=analyze(args.rom,args.v4,args.base,args.retail,args.language,payload,compiler)
    args.json.parent.mkdir(parents=True,exist_ok=True);args.json.write_text(json.dumps(result,indent=2)+'\n')
    print(args.language,'U-turn source/readback verified; fallback ABI, ordinary equivalence and marker authentication FAIL; no game fix applied')
    raise SystemExit(1)


if __name__=='__main__':main()
