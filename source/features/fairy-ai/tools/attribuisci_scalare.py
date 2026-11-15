#!/usr/bin/env python3
"""Attribute the complete installed Fairy scalar path, including real ARM division."""
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import sys

PATH=Path(__file__).with_name('attribuisci.py')
_spec=importlib.util.spec_from_file_location('shared_fairy_attribution',PATH)
SHARED=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(SHARED)
SOURCE=SHARED.SOURCE
FUNCTION,END,SEAM=0x0225264C,0x02252698,0x0225268E
DIV,DIV_END=0x020F2998,0x020F2BA4
OLD_SHA='a15779cf82eb792be4ffff407f56ad25e7e02fce295d3553132ae135399193ca'
CURRENT_SHA='7d4c9e83bcae449232442a214987fc127830bf6001c6eaf4df0ae554a0796724'
DIV_SHA='e8183a62ffe6a54210cd7d025b01431ff792025c1b45a0e8537abd8cec16ccfb'
BASE=SHARED.BASE


def sha(data):return hashlib.sha256(data).hexdigest()


def need(ok,why):
    if not ok:raise ValueError(why)


def expect_score(result,expected):
    need(result['score']==expected,'score %d, expected %d'%(result['score'],expected))


class ScalarCPU:
    """Run supplied exact parent code; deliberate helper mutants are counterproofs only."""
    STACK,STOP=0x023B7000,0x023FF000
    def __init__(self,segments,image,*,expect_tail=True):
        from unicorn import Uc,UC_ARCH_ARM,UC_MODE_THUMB
        self.uc=Uc(UC_ARCH_ARM,UC_MODE_THUMB)
        for address,size in ((0x02000000,0x400000),(0x01FF8000,0x8000),(0x027E0000,0x20000)):
            self.uc.mem_map(address,size)
        for address,data in segments:self.uc.mem_write(address,data)
        self.uc.mem_write(SHARED.F.OVERLAY_BASE,image)
        self.window=bytes(image[FUNCTION-SHARED.F.OVERLAY_BASE:END-SHARED.F.OVERLAY_BASE])
        need(sha(self.window)==(CURRENT_SHA if expect_tail else OLD_SHA),'exact scalar parent fixture')
        need(all(SHARED.branch(self.window[offset:offset+4],FUNCTION+offset,'blx')==DIV
                 for offset in (32,52)),'actual ARM division targets')
        self.resident=bytes(self.uc.mem_read(BASE,148));self.math=bytes(self.uc.mem_read(DIV,DIV_END-DIV))
        need(sha(self.math)==DIV_SHA,'actual ARM division identity')
        self.chart=bytes(self.uc.mem_read(SHARED.CHART,336));self.expect_tail=expect_tail
        self.regions=[(address,address+len(data)) for address,data in segments]+[(SHARED.F.OVERLAY_BASE,SHARED.F.OVERLAY_BASE+len(image))]
        self.code_seen={};self.read_seen=set()

    def run(self,attack,type1,type2):
        from unicorn import UC_HOOK_CODE,UC_HOOK_MEM_READ,UC_HOOK_MEM_WRITE
        from unicorn.arm_const import (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3,
            UC_ARM_REG_R4,UC_ARM_REG_R5,UC_ARM_REG_R6,UC_ARM_REG_R7,UC_ARM_REG_R8,UC_ARM_REG_R9,
            UC_ARM_REG_R10,UC_ARM_REG_R11,UC_ARM_REG_SP,UC_ARM_REG_LR,UC_ARM_REG_PC,UC_ARM_REG_CPSR)
        need(all(type(v) is int and 0<=v<18 for v in (attack,type1,type2)),'fixture type domain0..17')
        u=self.uc;saved=(UC_ARM_REG_R4,UC_ARM_REG_R5,UC_ARM_REG_R6,UC_ARM_REG_R7,
                        UC_ARM_REG_R8,UC_ARM_REG_R9,UC_ARM_REG_R10,UC_ARM_REG_R11)
        expected=[0x44440000+i for i in range(8)]
        u.mem_write(self.STACK-4104,b'\xA5'*8+bytes(4096)+b'\xA5'*32)
        for register,value in zip(saved,expected):u.reg_write(register,value)
        for register,value in ((UC_ARM_REG_R0,attack),(UC_ARM_REG_R1,type1),(UC_ARM_REG_R2,type2),
                (UC_ARM_REG_R3,0x33333333),(UC_ARM_REG_SP,self.STACK),(UC_ARM_REG_LR,self.STOP|1)):
            u.reg_write(register,value)
        result=dict(types=[attack,type1,type2],instructions=0,arm_instructions=0,scalar_entries=0,
                    decoder_entries=0,post_bl_entries=0,stack_depth=0,division_calls=[],writes=dict(count=0,bytes=0))
        pending=None
        def code(cpu,address,size,unused):
            nonlocal pending
            result['instructions']+=1;sp=cpu.reg_read(UC_ARM_REG_SP);thumb=bool(cpu.reg_read(UC_ARM_REG_CPSR)&32)
            result['stack_depth']=max(result['stack_depth'],self.STACK-sp)
            self.code_seen[address]=(size,thumb)
            if address==0x02252692:
                result['post_bl_entries']+=1;raise ValueError('scalar tail returned after replacement BL')
            if pending and address==pending['return_pc']:
                need(thumb and [cpu.reg_read(r) for r in saved]==pending.pop('saved'),'division return ISA/callee ABI')
                numerator,denominator=pending['numerator'],pending['denominator']
                quotient,remainder=cpu.reg_read(UC_ARM_REG_R0),cpu.reg_read(UC_ARM_REG_R1)
                need((quotient,remainder)==(numerator//denominator,numerator%denominator),'real division quotient/remainder')
                pending.update(quotient=quotient,remainder=remainder,return_isa='Thumb')
                result['division_calls'].append(pending);pending=None
            if DIV<=address<DIV_END:
                need(not thumb and size==4,'division must execute ARM instructions')
                result['arm_instructions']+=1
                if address==DIV:
                    need(pending is None,'nested division not expected')
                    numerator,denominator=cpu.reg_read(UC_ARM_REG_R0),cpu.reg_read(UC_ARM_REG_R1)
                    need(0<=numerator<=1600 and denominator==10,'bounded scalar division operands')
                    pending=dict(numerator=numerator,denominator=denominator,entry_isa='ARM',sp_mod8=sp%8,
                        return_pc=cpu.reg_read(UC_ARM_REG_LR)&~1,call_site=hex((cpu.reg_read(UC_ARM_REG_LR)&~1)-4),saved=[cpu.reg_read(r) for r in saved])
                    need(pending['return_pc'] in (0x02252670,0x02252684) and sp==self.STACK-24,'division call frame')
            else:
                need(thumb and size in (2,4),'scalar instruction ISA')
                need(FUNCTION<=address<0x02252692 or BASE+60<=address<BASE+108
                     or BASE+118<=address<BASE+148,'unexpected scalar code %#x'%address)
            if address==BASE+60:
                result['scalar_entries']+=1
                need(sp==self.STACK-24 and struct.unpack('<I',cpu.mem_read(sp,4))[0]==attack
                     and cpu.reg_read(UC_ARM_REG_R5)==type1 and cpu.reg_read(UC_ARM_REG_R6)==type2,'inline scalar ABI')
                result['native_score']=cpu.reg_read(UC_ARM_REG_R1)
                need(0<=result['native_score']<=160,'native score range')
            if address==BASE+94:result['decoder_entries']+=1
        def write(cpu,access,address,size,value,unused):
            need(self.STACK-4096<=address and address+size<=self.STACK,'scalar nonstack guest write')
            result['writes']['count']+=1;result['writes']['bytes']+=size
        def read(cpu,access,address,size,value,unused):
            if any(a<=address and address+size<=b for a,b in self.regions):self.read_seen.update(range(address,address+size))
        hooks=[u.hook_add(UC_HOOK_CODE,code),u.hook_add(UC_HOOK_MEM_WRITE,write),u.hook_add(UC_HOOK_MEM_READ,read)]
        try:u.emu_start(FUNCTION|1,self.STOP,count=30000)
        finally:
            for hook in hooks:u.hook_del(hook)
        need(u.reg_read(UC_ARM_REG_PC)==self.STOP and u.reg_read(UC_ARM_REG_SP)==self.STACK
             and u.reg_read(UC_ARM_REG_CPSR)&32 and [u.reg_read(r) for r in saved]==expected,'scalar parent return/ABI')
        need(pending is None and result['scalar_entries']==int(self.expect_tail) and result['post_bl_entries']==0,'scalar call/return path')
        need(bytes(u.mem_read(self.STACK-4104,8))==b'\xA5'*8 and bytes(u.mem_read(self.STACK,32))==b'\xA5'*32,'scalar stack canaries')
        need(bytes(u.mem_read(BASE,148))==self.resident and bytes(u.mem_read(FUNCTION,76))==self.window
             and bytes(u.mem_read(DIV,DIV_END-DIV))==self.math and bytes(u.mem_read(SHARED.CHART,336))==self.chart,'scalar code/data changed')
        result.update(score=u.reg_read(UC_ARM_REG_R0),r3_after_return=u.reg_read(UC_ARM_REG_R3))
        need(0<=result['score']<=160 and result['r3_after_return']==attack,'scalar result/caller-saved homeword')
        return result

    def closure(self):
        def ranges(addresses):
            blocks=[]
            for address in sorted(addresses):
                if blocks and blocks[-1][1]==address:blocks[-1][1]+=1
                else:blocks.append([address,address+1])
            return [dict(ram=hex(a),bytes=b-a,sha256=sha(bytes(self.uc.mem_read(a,b-a)))) for a,b in blocks]
        code=set()
        for address,(size,thumb) in self.code_seen.items():code.update(range(address,address+size))
        return dict(executed_ranges=ranges(code),immutable_read_ranges=ranges(self.read_seen),
            division_sha256=sha(self.math),parent_sha256=sha(self.window),resident_sha256=sha(self.resident))


def verify_reused_build(directory):
    """Consume the canonical own-project artifact without compiling or copying it."""
    directory=Path(directory);receipt=json.loads((directory/'compile-retained.json').read_text())
    obj=(directory/'fairy-native.o').read_bytes();payload=(directory/'native.bin').read_bytes()
    need(receipt['performed'] is True and sha(obj)==receipt['object_sha256']
         and sha(payload)==SHARED.F.PAYLOAD_SHA256,'reused own-build identities')
    need(receipt['source_sha256']==sha(SHARED.F.NATIVE.read_bytes())
         and receipt['builder_sha256']==sha(Path(SHARED.F.__file__).read_bytes())
         and receipt['loader_sha256']==sha((SOURCE/'features/options/tools/carica_text.py').read_bytes()),'reused source/builder/loader drift')
    need(receipt['compiler']['version']==SHARED.F.COMPILER_VERSION
         and receipt['compiler']['executable_sha256']==SHARED.F.COMPILER_SHA256
         and receipt['compiler']['flags']==list(SHARED.F.FLAGS),'reused compiler contract')
    loader=SHARED.F._module(SOURCE/'features/options/tools/carica_text.py','scalar_reused_elf')
    raw,symbols=loader.load_text(obj,BASE,('fairy_flags_hook','fairy_scalar_tail','fairy_apply_call_1','fairy_apply_call_2'))
    need(symbols['fairy_scalar_tail']==BASE+60|1 and symbols['fairy_code']==BASE+94|1,'reused ELF scalar geometry')
    expected=bytearray(raw)
    for offset in (24,50):
        need(raw[offset:offset+4]==bytes.fromhex('00f000f8'),'reused ELF placeholder')
        expected[offset:offset+4]=SHARED.F.bl_thumb(BASE+offset,SHARED.APPLY|1)
    need(bytes(expected)==payload and payload.index(SHARED.F.PACKED_CODES)==108,'reused ELF post-link correspondence')
    return dict(local_compilation_performed=False,reused_build_verified=True,object_sha256=sha(obj),payload_sha256=sha(payload),
        source_sha256=receipt['source_sha256'],compiler_recorded=receipt['compiler'],retained_object='fairy-native.o')


def scalar_window(model,canonical=None):
    """Read actual regional references; canonicalize verified relocations in a copy."""
    import capstone
    from capstone.arm import ARM_REG_PC
    record=next(r for r in model['record']['overlays'] if r['id']==12);ram=int(record['ram'],16)
    relative=FUNCTION-SHARED.F.OVERLAY_BASE;function=ram+relative
    window=bytes(model['overlay'][relative:relative+76]);md=capstone.Cs(capstone.CS_ARCH_ARM,capstone.CS_MODE_THUMB);md.detail=True
    instruction=list(md.disasm(window[2:4],function+2))
    need(len(instruction)==1 and instruction[0].mnemonic=='ldr','scalar chart literal load')
    memory=instruction[0].operands[1].mem;pool=((function+6)&~3)+memory.disp
    need(memory.base==ARM_REG_PC and pool==function+72,'scalar chart pool address')
    chart=struct.unpack_from('<I',window,72)[0]
    need(chart==ram+SHARED.CHART-SHARED.F.OVERLAY_BASE,'scalar sparse chart pointer')
    targets=[SHARED.branch(window[o:o+4],function+o,'blx') for o in (32,52)]
    need(targets[0]==targets[1] and targets[0]%4==0,'scalar ARM division calls')
    target=targets[0]
    pieces=[bytes(data[target-address:target-address+524]) for address,data in model['segments']
            if address<=target and target+524<=address+len(data)]
    need(len(pieces)==1 and sha(pieces[0])==DIV_SHA,'regional ARM division code correspondence')
    normalized=bytearray(window)
    if canonical is not None:
        for offset in (32,52):normalized[offset:offset+4]=canonical[offset:offset+4]
        struct.pack_into('<I',normalized,72,SHARED.CHART)
    return window,bytes(normalized),dict(function_ram=hex(function),function_bytes=76,raw_sha256=sha(window),
        chart_literal_ram=hex(pool),chart_ram=hex(chart),division_ram=hex(target),division_bytes=524,
        division_sha256=sha(pieces[0]),call_sites=[hex(function+o) for o in (32,52)],
        comparison_relocation_offsets=[32,52,72] if canonical is not None else [],executed_bytes_modified=False)


def engine_chart(path,language,label):
    """Read the independent dense battle-engine representation, not the ASM vectors."""
    import mmap
    from sgp131 import type_chart
    # Caller has authenticated the complete file through the shared reader.
    with Path(path).open('rb') as handle,mmap.mmap(handle.fileno(),0,access=mmap.ACCESS_READ) as raw:
        data,record=SHARED.overlay(raw,18)
    need(int(record['ram'],16)==type_chart.OVERLAY_BASE and len(data)==type_chart.OVERLAY_SIZE,'dense engine chart geometry')
    matrix,trailer=type_chart.rows(data)
    cells={(a,b):m for a,b,m in matrix}
    cells.update({(a,b):m for a,b,m in trailer if a<18 and b<18})
    need(len(cells)==324 and all(v in (0,5,10,20) for v in cells.values()),'complete dense matrix/control representation')
    return data,cells,record


DUALS=((10,10,17,20),(10,15,15,80),(11,10,10,80),(10,11,11,20),(0,7,7,0),
       (10,15,11,40),(9,16,16,80),(17,9,9,20),(0,0,0,40),(9,17,1,160),
       (16,9,16,0),(16,16,9,0),(9,3,8,10),(9,8,3,10),(9,10,16,40),
       (9,0,0,40),(3,9,9,80),(8,9,9,80),(1,9,9,20),(6,9,9,20),(16,9,9,0),(10,12,15,160),(10,10,11,10),(0,7,5,0),(0,5,7,0))


def analyze(rom,v4,base,retail,language,build=None):
    import gc
    from sgp131 import type_chart
    reused=verify_reused_build(build) if build is not None else dict(local_compilation_performed=False,
        reused_build_verified=False,reason='readback only; own-build provenance not checked in this run')
    models={name:SHARED.read_image(path,language,name) for name,path in
            (('retail',retail),('base11',base),('v4',v4),('r4',rom))}
    old,current=models['v4'],models['r4'];offset=FUNCTION-SHARED.F.OVERLAY_BASE
    old_window=old['overlay'][offset:offset+76]
    need(sha(old_window)==OLD_SHA and sha(current['resident'])==SHARED.F.PAYLOAD_SHA256,'scalar preimage/current payload')
    expected=bytearray(old_window)
    expected[SEAM-FUNCTION:SEAM-FUNCTION+4]=SHARED.F.seam_bytes(BASE)[SEAM]
    need(bytes(expected)==current['overlay'][offset:offset+76] and sha(expected)==CURRENT_SHA,'whole scalar source-recipe reconstruction')
    scalar_records=[]
    for name,model in models.items():
        raw,normalized,record=scalar_window(model,old_window if name=='retail' else None)
        if name!='r4':need(normalized==old_window,'inherited scalar window after verified relocations')
        scalar_records.append(dict(input=name,**record))
    previous_dense,_,previous_record=engine_chart(v4,language,'v4')
    dense,cells,dense_record=engine_chart(rom,language,'r4')
    repaired,_=type_chart.patch_overlay(previous_dense)
    need(type_chart._chart_bytes(repaired)==type_chart._chart_bytes(dense),'independent engine chart source replay')
    caller_records=[]
    for site in (0x02244726,0x02258920,0x02258930):
        raw=current['overlay'][site-SHARED.F.OVERLAY_BASE:site-SHARED.F.OVERLAY_BASE+4]
        need(SHARED.branch(raw,site,'bl')==FUNCTION,'actual scalar caller')
        caller_records.append(dict(overlay=12,ram=hex(site),target=hex(FUNCTION),sha256=sha(raw)))
    native=ScalarCPU(old['segments'],old['overlay'],expect_tail=False)
    installed=ScalarCPU(current['segments'],current['overlay'])
    monotypes=[];policy_differences=[];ordinary=fairy=0
    for attack in range(18):
        for defender in range(18):
            before=native.run(attack,defender,defender);after=installed.run(attack,defender,defender)
            need(after['decoder_entries']==1,'monotype decoder must run once')
            engine_score=40*cells[(attack,defender)]//10
            if 9 in (attack,defender):
                fairy+=1;expect_score(after,engine_score)
            else:
                ordinary+=1;expect_score(after,before['score'])
                if after['score']!=engine_score:policy_differences.append(dict(attack=attack,defender=defender,
                    native_score=after['score'],dense_engine_score=engine_score))
            monotypes.append(dict(attack=attack,defender=defender,inherited=before,current=after,dense_engine_score=engine_score))
    need((ordinary,fairy)==(289,35),'monotype domain coverage')
    duals=[]
    for attack,type1,type2,score in DUALS:
        result=installed.run(attack,type1,type2);expect_score(result,score)
        need(result['decoder_entries']==(1 if type1==type2 else 2),'dual/monotype decoder count')
        duals.append(result)
    closures=dict(inherited=native.closure(),current=installed.closure())
    del native,installed;gc.collect()
    mutant=[]
    for address,data in current['segments']:
        if address<=BASE+76<address+len(data):
            data=bytearray(data);at=BASE+76-address
            need(SHARED.branch(bytes(data[at:at+2]),BASE+76,'beq')==BASE+90,'counterproof equal-defender branch')
            data[at:at+2]=bytes.fromhex('c046');data=bytes(data)
        mutant.append((address,data))
    cpu=ScalarCPU(mutant,current['overlay']);counter=cpu.run(9,16,16)
    need(counter['score']==160 and counter['decoder_entries']==2,'double-Fairy counterproof')
    try:expect_score(counter,80)
    except ValueError:pass
    else:raise ValueError('double-Fairy false semantic success')
    del cpu;gc.collect()
    return dict(schema='fairy-scalar-source-rom-v1',language=language,reused_build=reused,
        inputs=[model['record'] for model in models.values()],scalar_windows=scalar_records,
        current_parent_sha256=CURRENT_SHA,division_sha256=DIV_SHA,callers=caller_records,
        dense_chart=dict(v4=previous_record,r4=dense_record,source_recipe='sgp131/type_chart.py; chart region only'),
        coverage=dict(monotypes=324,ordinary_inherited_equivalence=ordinary,fairy_matches_dense_engine=fairy,
            literal_cases=len(duals),monotype_parent_invocations=648,current_literal_invocations=len(duals)),
        monotypes=monotypes,literal_cases=duals,closures=closures,ordinary_policy_differences=policy_differences,
        counterproof=dict(mutation='RAM-only equal-defender BEQ→NOP',required_score=80,result=counter,
            original_files_unchanged=True),
        source_sha256={str(p.relative_to(SOURCE)):sha(p.read_bytes()) for p in
            (Path(__file__),PATH,SHARED.F.NATIVE,SOURCE/'sgp131/type_chart.py')},
        limits=['valid types0..17 and fixed divisor10; not general signed division',
                'monotypes exhaustive,all5832 type triples not exercised',
                'caller links static; no natural AI/hazard/gameplay/RNG/SAVE/hardware',
                'ordinary native policy preserved,not declared identical to dense modern policy'])


def main():
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('rom','v4','base','retail','json'):parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--language',choices=('EN','IT'),required=True)
    parser.add_argument('--build',type=Path,help='canonical retained own-project build from the flags tool; never copied or rebuilt')
    parser.add_argument('--readback-only',action='store_true')
    args=parser.parse_args()
    if (args.build is None)==(not args.readback_only):parser.error('choose exactly one of --build DIR or --readback-only')
    protected=[args.rom,args.v4,args.base,args.retail]
    if args.build is not None:protected.extend(args.build/name for name in ('fairy-native.o','native.bin','compile-retained.json'))
    for path in protected:
        if args.json.resolve()==path.resolve() or (args.json.exists() and path.exists() and args.json.samefile(path)):
            parser.error('--json must not replace an input or reused build artifact')
    result=analyze(args.rom,args.v4,args.base,args.retail,args.language,args.build)
    args.json.parent.mkdir(parents=True,exist_ok=True);args.json.write_text(json.dumps(result,indent=2)+'\n')
    print(args.language,'scalar:324 monotypes +%d literals +guard counterproof PASS;'%len(result['literal_cases']),
          len(result['ordinary_policy_differences']),'ordinary native/dense differences; no compilation')


if __name__=='__main__':main()
