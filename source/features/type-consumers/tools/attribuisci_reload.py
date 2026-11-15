#!/usr/bin/env python3
"""Reconstruct Transform reload source/ELF and execute exact current guarded reloads."""
import importlib.util
import json
from pathlib import Path
import struct

spec=importlib.util.spec_from_file_location('reload_shared',Path(__file__).with_name('attribuisci.py'))
G=importlib.util.module_from_spec(spec);spec.loader.exec_module(G)
from sgp131 import transform_reload as T
from sgp131 import test_transform_reload as C
from unicorn import UC_HOOK_MEM_READ,UC_HOOK_MEM_WRITE
from unicorn.arm_const import (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3,
    UC_ARM_REG_SP,UC_ARM_REG_LR,UC_ARM_REG_PC,UC_ARM_REG_CPSR)
need,sha=G.need,G.sha
CTX,BS,MON,STACK,STOP=C.CTX,C.BSYS,C.MON,C.STACK,C.STOP
ENTRY=T.RELOAD_ADDRESS
MASK=0x020726C0
MASK_SHA='da266f8eefce9cbb52a195196c3e0897cbc84b5af29871c7bd834fa3e8992a78'
GET_SHA='7d88f5974d9ca615e5602e1e9b89a594f6fc8e78d4c36cf5660f7cc9f12f02b0'


def take(image,address,size):return bytes(image[address-T.OVERLAY_BASE:address-T.OVERLAY_BASE+size])


def compile_object(work):
    work=Path(work);work.mkdir(parents=True,exist_ok=True)
    payload,receipt=T.compile_native(work,retain_object=True);obj=(work/receipt['retained_object']).read_bytes()
    loader=T._module(G.SOURCE/'features/options/tools/carica_text.py','reload_attribution_elf')
    loaded,symbols=loader.load_text(obj,ENTRY,('reload_mon_data',))
    need(loaded==payload and sha(obj)==receipt['object_sha256'] and symbols['reload_mon_data']==ENTRY|1,'Reload ELF→payload identity')
    shoff=struct.unpack_from('<I',obj,32)[0];count=struct.unpack_from('<H',obj,48)[0]
    sections=[struct.unpack_from('<10I',obj,shoff+40*i) for i in range(count)]
    proof=dict(performed=True,**receipt,builder_sha256=sha(Path(T.__file__).read_bytes()),
        loader_sha256=sha((G.SOURCE/'features/options/tools/carica_text.py').read_bytes()),
        symbols={k:hex(v) for k,v in symbols.items()},elf_section_types=[s[1] for s in sections],
        relocation_records=sum(s[5]//s[9] for s in sections if s[1] in (4,9) and s[9]),post_loader_payload_changes=0)
    for name,data in (('native.bin',payload),('compile-retained.json',(json.dumps(proof,indent=2)+'\n').encode())):
        p=work/name;need(not p.is_symlink() and (not p.exists() or p.is_file() and p.read_bytes()==data),'existing reload artifact differs; use a fresh directory')
        if not p.exists():p.write_bytes(data)
    return payload,proof


def verify_build(work):
    work=Path(work);proof=json.loads((work/'compile-retained.json').read_text());obj=(work/'reload_transform.o').read_bytes();payload=(work/'native.bin').read_bytes()
    need(proof['source_sha256']==sha(T.NATIVE.read_bytes()) and proof['builder_sha256']==sha(Path(T.__file__).read_bytes()),'Reload source/builder drift')
    need(proof['loader_sha256']==sha((G.SOURCE/'features/options/tools/carica_text.py').read_bytes()),'Reload ELF loader drift')
    need(proof['compiler']==dict(version=T.COMPILER_VERSION,executable_sha256=T.COMPILER_SHA256,flags=list(T.FLAGS)),'Reload retained compiler contract')
    need(sha(obj)==proof['object_sha256'] and sha(payload)==proof['payload_sha256']==T.PAYLOAD_SHA256,'Reload retained artifacts')
    loader=T._module(G.SOURCE/'features/options/tools/carica_text.py','reload_reused_elf');raw,symbols=loader.load_text(obj,ENTRY,('reload_mon_data',))
    need(raw==payload and symbols['reload_mon_data']==ENTRY|1,'Reload reused ELF geometry')
    return payload,dict(performed=False,verified_retained_build=proof)


def counter_image(image,variant):
    result=bytearray(image);at=ENTRY-T.OVERLAY_BASE
    need(sha(result[at:at+340])==T.PAYLOAD_SHA256,'current reload counter preimage')
    if variant=='native_old':result[at:at+340]=T.RELOAD_PREIMAGE
    elif variant in ('first_guard','second_guard'):
        offset,expected=(0x26,bytes.fromhex('1dd1')) if variant=='first_guard' else (0xA4,bytes.fromhex('2dd1'))
        need(result[at+offset:at+offset+2]==expected,'reload guard counter preimage');result[at+offset:at+offset+2]=bytes.fromhex('c046')
    else:raise ValueError('explicit reload counter variant')
    return bytes(result)


def require_common_only(result):need(result['fields']==[161,9,163,164],'transformed reload queried more than common fields')


class ReloadCPU(C.ReloadBench):
    """Reuse the existing two leaf models, with current image and strict boundaries."""
    def __init__(self,segments,image,*,variant='current'):
        body=bytearray(take(image,ENTRY,340));self.variant=variant
        if variant=='native_old':need(bytes(body)==T.RELOAD_PREIMAGE,'native reload counter identity')
        else:
            if variant in ('first_guard','second_guard'):
                offset,expected=(0x26,bytes.fromhex('1dd1')) if variant=='first_guard' else (0xA4,bytes.fromhex('2dd1'))
                need(body[offset:offset+2]==bytes.fromhex('c046'),'named reload guard fixture');body[offset:offset+2]=expected
            else:need(variant=='current','explicit Reload variant required')
            need(sha(body)==T.PAYLOAD_SHA256,'current/counter reload body identity')
        need(take(image,T.LITERAL_ADDRESS,52)==T.LITERAL_PREIMAGE,'preserved native reload literal closure')
        need(sha(G.piece(segments,MASK,32))==MASK_SHA,'native reload Mask identity')
        super().__init__(take(image,ENTRY,340))
        self.uc.mem_map(0x01FF8000,0x8000);self.uc.mem_map(0x027E0000,0x20000)
        self.frozen=[(a,bytes(b)) for a,b in segments]+[(T.OVERLAY_BASE,bytes(image))]
        for a,b in self.frozen:self.uc.mem_write(a,b)
        self.defaults=dict(self.fields);self.current=None;self.pending_mask=None
        self.uc.hook_add(UC_HOOK_MEM_WRITE,self._write);self.uc.hook_add(UC_HOOK_MEM_READ,self._read)

    def reg(self,r):return self.uc.reg_read(r)

    def _hook(self,u,address,size,unused):
        r=self.current
        if r is None:return
        r['instructions']+=1;need(r['instructions']<=20000,'reload instruction budget')
        need(self.reg(UC_ARM_REG_CPSR)&32 and size in (2,4),'reload Thumb ISA')
        sp=self.reg(UC_ARM_REG_SP);r['stack_depth']=max(r['stack_depth'],STACK-sp)
        if self.pending_mask and address==self.pending_mask['return_pc']:
            call=self.pending_mask;need(sp==call['sp'] and [self.reg(v) for v in G.SAVED]==call.pop('saved'),'native reload Mask return ABI')
            call['value']=self.reg(UC_ARM_REG_R0);need(call['value']==1<<call['slot'],'native reload Mask result')
            r['native_mask_calls'].append(call);self.pending_mask=None
        if address in (T.GET_PARTY_MON,T.GET_MON_DATA):
            args=[self.reg(v) for v in (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2)]
            if address==T.GET_PARTY_MON:need(args==[BS,r['battler'],r['party_slot']],'reload PartyMon query ABI')
            else:need(args[0]==MON and args[1] in self.fields and args[2]==0,'reload GetMonData/null pointer ABI')
            r['models'].append(dict(ram=hex(address),args=args,return_pc=hex(self.reg(UC_ARM_REG_LR)&~1)))
            return super()._hook(u,address,size,unused)
        end=ENTRY+(340 if self.variant=='native_old' else 0x10E)
        allowed=ENTRY<=address and address+size<=end
        allowed|=self.variant=='native_old' and MASK<=address and address+size<=MASK+32
        need(allowed,'unexpected reload code/literal/padding PC '+hex(address))
        r['code'].add((address,size))
        if address==MASK:
            slot=self.reg(UC_ARM_REG_R0);need(0<=slot<4 and self.pending_mask is None,'native reload Mask slot domain')
            self.pending_mask=dict(slot=slot,sp=sp,return_pc=self.reg(UC_ARM_REG_LR)&~1,saved=[self.reg(v) for v in G.SAVED])

    def _write(self,u,access,address,size,value,unused):
        r=self.current
        if r is None:return
        stack=STACK-4096<=address and address+size<=STACK
        relative=address-(CTX+C.BATMON+0xC0*r['battler'])
        field=(size==2 and relative in (*range(2,20,2),)) or (size==1 and relative in range(44,54)) or (size==4 and relative in (76,80,100))
        need(stack or field,'reload write outside selected fields/stack '+hex(address))
        if field:r['writes'].append(dict(offset=relative,bytes=size,value=value))

    def _read(self,u,access,address,size,value,unused):
        r=self.current
        if r is not None and address==CTX+C.BATMON+0xC0*r['battler']+112 and size==4:
            r['status_reads'].append(dict(pc=hex(self.reg(UC_ARM_REG_PC)),value=int.from_bytes(u.mem_read(address,4),'little')))

    def observe(self,transformed,*,mimic=0,battler=0,party_slot=0,equal_stats=False):
        need(type(transformed) is bool and type(equal_stats) is bool and type(mimic) is int and 0<=mimic<16 and type(battler) is int and 0<=battler<4 and type(party_slot) is int and 0<=party_slot<6,'reload fixture domain')
        u=self.uc;u.mem_write(CTX,b'\xCC'*0x4000);u.mem_write(BS,b'\xA5'*0x100);u.mem_write(MON,b'\xA5'*0x100)
        u.mem_write(STACK-4104,b'\xA5'*8+bytes(4096)+b'\xA5'*256)
        base=CTX+C.BATMON+0xC0*battler
        self.fields=dict(self.defaults)
        if equal_stats:self.fields.update({165+i:301+i for i in range(5)})
        for i in range(5):u.mem_write(base+2+2*i,struct.pack('<H',301+i))
        for i in range(4):
            u.mem_write(base+12+2*i,struct.pack('<H',401+i));u.mem_write(base+44+i,bytes((11+i,)));u.mem_write(base+48+i,bytes((i,)))
        u.mem_write(base+52,bytes((49,100)))
        for offset,value in ((76,77),(80,155),(100,123456),(112,C.TRANSFORM if transformed else 0),(140,mimic<<2)):u.mem_write(base+offset,struct.pack('<I',value))
        before=bytes(u.mem_read(CTX,0x4000));self.calls=[];self.pending_mask=None
        for reg,value in zip(G.SAVED,G.COOKIES):u.reg_write(reg,value)
        for reg,value in zip((UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3),(BS,CTX,battler,party_slot)):u.reg_write(reg,value)
        u.reg_write(UC_ARM_REG_SP,STACK);u.reg_write(UC_ARM_REG_LR,STOP|1)
        r=dict(transformed=transformed,mimic=mimic,battler=battler,party_slot=party_slot,equal_stats=equal_stats,variant=self.variant,instructions=0,stack_depth=0,models=[],native_mask_calls=[],writes=[],status_reads=[],code=set())
        self.current=r
        try:u.emu_start(ENTRY|1,STOP,count=20001)
        finally:self.current=None
        need(self.reg(UC_ARM_REG_PC)==STOP and self.reg(UC_ARM_REG_SP)==STACK and self.reg(UC_ARM_REG_CPSR)&32 and [self.reg(v) for v in G.SAVED]==G.COOKIES,'reload parent return ABI')
        need(self.pending_mask is None,'unfinished native reload Mask')
        after=bytes(u.mem_read(CTX,0x4000));allowed=set()
        for offset,n in ((2,18),(44,10),(76,8),(100,4)):allowed.update(range(C.BATMON+0xC0*battler+offset,C.BATMON+0xC0*battler+offset+n))
        need(all(a==b for i,(a,b) in enumerate(zip(before,after)) if i not in allowed),'reload changed other battler/species/type/ability/form/status')
        need(bytes(u.mem_read(BS,0x100))==b'\xA5'*0x100 and bytes(u.mem_read(MON,0x100))==b'\xA5'*0x100,'reload mutated modeled BS/PartyMon')
        need(bytes(u.mem_read(STACK-4104,8))==b'\xA5'*8 and bytes(u.mem_read(STACK,256))==b'\xA5'*256,'reload stack/caller canaries')
        need(all(bytes(u.mem_read(a,len(b)))==b for a,b in self.frozen),'reload changed initialized code/data')
        need([c for c in self.calls if c[0]=='party']==[('party',battler,party_slot)],'one reload PartyMon lookup')
        def word(offset):return int.from_bytes(u.mem_read(base+offset,4),'little')
        r.update(fields=[c[1] for c in self.calls if c[0]=='data'],state=dict(stats=list(struct.unpack('<5H',u.mem_read(base+2,10))),moves=list(struct.unpack('<4H',u.mem_read(base+12,8))),
            pp=list(u.mem_read(base+44,4)),ppups=list(u.mem_read(base+48,4)),level_friendship=list(u.mem_read(base+52,2)),hp_max=[word(76),word(80)],exp=word(100)))
        r['code']=[dict(ram=hex(a),bytes=n) for a,n in sorted(r['code'])];return r


def window(model,role):
    base=int(model['record']['overlays'][1]['ram'],16);address=base+ENTRY-T.OVERLAY_BASE;raw=take(model['overlay'],ENTRY,340);normal=bytearray(raw);fields=[]
    need(take(model['overlay'],T.LITERAL_ADDRESS,52)==T.LITERAL_PREIMAGE,'all input-role native literal closure')
    if role=='retail' and model['record']['language']=='IT':
        need(sha(raw)=='7eb5f715160303534482dc3a3cf74d7f8b6b42ba194821a0e5da7f41468b16b2','retail IT native reload identity')
        from sgp12.rom import bl_thumb
        for offset in (0x1C,0x30,0x44,0x58,0x6C,0x80,0x94,0xA8,0xBC,0xF0,0x10A,0x11A,0x12A,0x142):
            target=MASK if offset==0xF0 else T.GET_MON_DATA
            need(G.S.SHARED.branch(raw[offset:offset+4],address+offset,'bl')==target,'retail IT reload ARM9 target')
            need(sha(G.piece(model['segments'],target,32 if target==MASK else 120))==(MASK_SHA if target==MASK else GET_SHA),'retail IT reload ARM9 signature')
            normal[offset:offset+4]=bl_thumb(ENTRY+offset,target);fields.append(dict(offset=hex(offset),target=hex(target)))
    need(sha(normal)==(T.PAYLOAD_SHA256 if role=='r4' else T.RELOAD_PREIMAGE_SHA256),'whole normalized reload body')
    return dict(ram=hex(address),bytes=340,raw_sha256=sha(raw),normalized_sha256=sha(normal),preserved_pool_bytes=52,preserved_pool_sha256=T.LITERAL_SHA256,comparison_only_fields=fields)


def analyze(rom,v4,base,retail,language,payload,compiler):
    import gc
    models={name:G.S.SHARED.read_image(path,language,name) for name,path in (('retail',retail),('base11',base),('v4',v4),('r4',rom))}
    windows=[dict(input=name,**window(m,name)) for name,m in models.items()];current=models['r4']
    need(payload==take(current['overlay'],ENTRY,340),'exact installed reload compiled/readback bytes')
    replay,receipt=T.patch_overlay(models['v4']['overlay'],payload)
    need(take(replay,ENTRY,392)==take(current['overlay'],ENTRY,392),'source installer full reload+literal closure')
    callers=[]
    for site in (0x02245442,0x02245CDA,0x0224604C,0x02246358):
        raw=take(current['overlay'],site,4);need(G.S.SHARED.branch(raw,site,'bl')==ENTRY,'actual reload static caller')
        callers.append(dict(ram=hex(site),target=hex(ENTRY),sha256=sha(raw),activation='static only'))
    runs=[];cpu=ReloadCPU(current['segments'],current['overlay']);old=ReloadCPU(current['segments'],counter_image(current['overlay'],'native_old'),variant='native_old')
    for mask in range(16):
        result=cpu.observe(False,mimic=mask,battler=mask%4,party_slot=mask%6);native=old.observe(False,mimic=mask,battler=mask%4,party_slot=mask%6)
        need(result['state']==native['state'] and result['fields']==native['fields'],'ordinary reload native equivalence')
        need(result['state']['stats']==[101,102,103,104,105] and result['state']['exp']==654321,'ordinary stats/experience reload')
        need(result['state']['moves']==[401+i if mask&(1<<i) else 501+i for i in range(4)],'ordinary Mimic slot protection')
        runs.append(dict(name='ordinary_mimic_'+str(mask),result=result,native=native))
    for mask in (0,1,2,4,8,15):
        result=cpu.observe(True,mimic=mask,battler=mask%4,party_slot=mask%6);require_common_only(result)
        need(result['state']==dict(stats=[301,302,303,304,305],moves=[401,402,403,404],pp=[11,12,13,14],ppups=[0,1,2,3],level_friendship=[50,101],hp_max=[83,166],exp=123456),'transformed reload state')
        runs.append(dict(name='transform_mimic_'+str(mask),result=result))
    equal=cpu.observe(True,equal_stats=True);require_common_only(equal);runs.append(dict(name='equal_stats',result=equal));del cpu,old;gc.collect()
    counters=[]
    for variant in ('native_old','first_guard','second_guard'):
        cpu=ReloadCPU(current['segments'],counter_image(current['overlay'],variant),variant=variant)
        result=cpu.observe(True,equal_stats=variant=='first_guard')
        try:require_common_only(result)
        except ValueError:pass
        else:raise ValueError('false transformed query success')
        same=result['state']==equal['state'];need(same==(variant=='first_guard'),'equal-state counter discriminant')
        counters.append(dict(variant=variant,oracle_rejected=True,same_final_state=same,result=result));del cpu;gc.collect()
    return dict(schema='transform-reload-source-rom-v1',language=language,inputs=[m['record'] for m in models.values()],windows=windows,compile=compiler,source_recipe=receipt,
        callers=callers,runs=runs,counterproofs=counters,coverage=dict(current_positive_entries=23,native_ordinary_comparisons=16,counter_entries=3),
        source_sha256={str(p.relative_to(G.SOURCE)):sha(p.read_bytes()) for p in (Path(__file__),Path(T.__file__),T.NATIVE,G.SOURCE/'features/options/tools/carica_text.py',G.SOURCE/'sgp131/test_transform_reload.py')},
        limits=['PartyMon lookup and GetMonData are controlled models, not encrypted/native lookup execution',
                'four static callers; direct isolated reload, not natural level-up/move-learning/controller',
                'finite initialized field values, Mimic masks0..15 and battlers/party slots; no universal battle history',
                'own assembly rebuilt; original native C/compiler reconstruction absent',
                'no SAVE/cold, device, timing or memory reclamation claim'])


def main():
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('rom','v4','base','retail','json'):parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--language',choices=('EN','IT'),required=True)
    group=parser.add_mutually_exclusive_group(required=True);group.add_argument('--work',type=Path);group.add_argument('--build',type=Path);group.add_argument('--readback-only',action='store_true');args=parser.parse_args()
    protected=[args.rom,args.v4,args.base,args.retail]
    artifact_dir=args.work or args.build
    if artifact_dir:
        protected.extend(artifact_dir/name for name in ('native.bin','reload_transform.o','compile-retained.json'))
    for path in protected:
        if args.json.resolve()==path.resolve() or (args.json.exists() and path.exists() and args.json.samefile(path)):
            parser.error('--json must not replace an input or retained artifact')
    if args.work:payload,compiler=compile_object(args.work)
    elif args.build:payload,compiler=verify_build(args.build)
    else:payload=T.PAYLOAD_SHA256;compiler=dict(performed=False,available=False,reason='explicit readback-only mode')
    if args.readback_only:
        m=G.S.SHARED.read_current(args.rom,args.language);payload=take(m['overlay'],ENTRY,340);need(sha(payload)==T.PAYLOAD_SHA256,'readback-only current reload');del m
    result=analyze(args.rom,args.v4,args.base,args.retail,args.language,payload,compiler)
    args.json.parent.mkdir(parents=True,exist_ok=True);args.json.write_text(json.dumps(result,indent=2)+'\n')
    print(args.language,'Reload:23 current +16 native comparisons +3 counter entries PASS; compiler performed',compiler['performed'])


if __name__=='__main__':main()
