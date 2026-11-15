#!/usr/bin/env python3
"""Read exact final Fairy flags code and execute its real native loop without stubs."""
import argparse
import hashlib
import json
import mmap
from pathlib import Path
import struct
import sys

SOURCE=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(SOURCE))
from sgp12 import blz
from sgp131 import baseline,gifts_audit
from sgp131 import fairy_ai as F
import capstone
import ndspy.code

BASE=0x023D746C
FUNCTION=0x02252054
FUNCTION_END=0x02252218
APPLY=0x022521C8
CHART=0x0226CC7C
CALLERS={10:(0x0221F78E,0x0221FA3A,0x0221FAC8,0x0221FC44,0x0221FCD4,0x0222017C,0x02220210),
         12:(0x022589FC,)}
BASES={'EN':('281c2d68e442479e679d8b7e36566ade614d236151c65c9684bad6985461827d',127104144),
       'IT':('7b61646c627eb67cd991dbc33d68519edd69395468ea8b326e867fe98e62d077',131906120)}
RETAILS={'EN':'65f02a56842b75aa92d775d56d657a56fe3fa993550b04dc20704ab82d760105',
         'IT':'013d04f5512b01ad98735a5f850dc039f0ee80bc57035b3a10e8b650be690ce1'}
CASES=((10,10,17,4),(10,15,15,2),(11,10,10,2),(10,11,11,4),(0,7,7,8),
       (10,15,11,0),(9,16,16,2),(17,9,9,4),(0,0,0,0),(9,17,1,2),
       (16,9,16,8),(16,16,9,8))


def sha(data):return hashlib.sha256(data).hexdigest()


def need(ok,why):
    if not ok:raise ValueError(why)


def branch(data,address,mnemonic):
    instructions=list(capstone.Cs(capstone.CS_ARCH_ARM,capstone.CS_MODE_THUMB).disasm(data,address))
    need(len(instructions)==1 and instructions[0].mnemonic==mnemonic,'unexpected Thumb branch')
    return int(instructions[0].op_str.lstrip('#'),0)


def overlay(raw,oid):
    fat,fat_bytes,y9,y9_bytes=struct.unpack_from('<4I',raw,0x48)
    need(y9_bytes%32==0 and oid<y9_bytes//32 and y9+y9_bytes<=len(raw),'y9 extent')
    record_at=y9+oid*32;row=struct.unpack_from('<8I',raw,record_at)
    need(row[0]==oid and (row[6]+1)*8<=fat_bytes,'overlay ID/file ID')
    start,end=struct.unpack_from('<II',raw,fat+row[6]*8)
    need(0<=start<end<=len(raw),'overlay FAT extent')
    stream=raw[start:end]
    if row[7]>>24&1:
        need(len(stream)==row[7]&0xFFFFFF,'overlay compressed size')
        footer=blz.blz_verifica_dimensione(stream,row[2])
        decoded=blz.blz_decomprimi(stream,row[2])
    else:
        need(len(stream)==row[2],'uncompressed overlay size');decoded=stream;footer=None
    def file_callback(overlay_id,file_id):
        need(overlay_id==oid and file_id==row[6],'ndspy overlay callback identity')
        return stream
    independent=ndspy.code.loadOverlayTable(raw[y9:y9+y9_bytes],file_callback,idsToLoad={oid})[oid]
    need(bytes(independent.data)==decoded and independent.ramAddress==row[1]
         and independent.ramSize==row[2] and independent.bssSize==row[3], 'independent overlay mapping/BLZ')
    return decoded,dict(id=oid,y9_record_offset=hex(record_at),y9_words=list(row),
        file_id=row[6],rom_start=hex(start),rom_end=hex(end),stored_bytes=len(stream),
        stored_sha256=sha(stream),decoded_bytes=len(decoded),decoded_sha256=sha(decoded),
        ram=hex(row[1]),bss_bytes=row[3],compression='BLZ' if footer else 'none',
        footer=footer,footer_hex=stream[-8:].hex() if footer else None)


def normalized_flags_window(image,ram):
    """Normalize only three independently decoded table-pointer literals in a copy."""
    from capstone.arm import ARM_REG_PC
    lo,hi=FUNCTION-F.OVERLAY_BASE,FUNCTION_END-F.OVERLAY_BASE
    function=ram+lo;chart=ram+(CHART-F.OVERLAY_BASE)
    md=capstone.Cs(capstone.CS_ARCH_ARM,capstone.CS_MODE_THUMB);md.detail=True
    pool={};loads=[]
    for instruction_offset,pool_offset,column in ((0x78,0x120,0),(0x130,0x16C,1),
            (0x138,0x170,2),(0x154,0x16C,1),(0x15C,0x170,2)):
        address=function+instruction_offset
        instructions=list(md.disasm(image[lo+instruction_offset:lo+instruction_offset+2],address))
        need(len(instructions)==1 and instructions[0].mnemonic=='ldr','native literal load')
        ins=instructions[0];mem=ins.operands[1].mem
        literal=((address+4)&~3)+mem.disp
        need(mem.base==ARM_REG_PC and literal==function+pool_offset,'native PC-relative literal target')
        value=struct.unpack_from('<I',image,literal-ram)[0]
        need(value==chart+column,'native sparse chart column pointer')
        pool[pool_offset]=(value,column)
        loads.append(dict(instruction_ram=hex(address),literal_ram=hex(literal),target_ram=hex(value),column=column))
    normalized=bytearray(image[lo:hi])
    for offset,(actual,column) in pool.items():struct.pack_into('<I',normalized,offset,CHART+column)
    return bytes(normalized),dict(function_ram=hex(function),chart_ram=hex(chart),verified_literal_loads=loads,
        comparison_only_pointer_offsets=[hex(x) for x in sorted(pool)],executed_bytes_modified=False)


def read_image(path,language,label):
    if label=='retail':digest,size=RETAILS[language],134217728
    elif label=='base11':digest,size=BASES[language]
    elif label=='v4':digest,size=next((h,n) for h,n in baseline.INPUT_SIZES.items() if baseline.INPUT_HASHES[h]==language)
    else:
        need(label=='r4','unknown input role')
        pin=json.loads((SOURCE/'distribution/game-1.3.2-r4.json').read_text())['targets'][language]
        digest,size=pin['sha256'],pin['bytes']
    with Path(path).open('rb') as file,mmap.mmap(file.fileno(),0,access=mmap.ACCESS_READ) as raw:
        need(len(raw)==size and sha(raw)==digest,'exact '+label+' '+language+' input')
        off,entry,ram,length=struct.unpack_from('<4I',raw,0x20)
        settings=struct.unpack_from('<I',raw,0x70)[0]
        main=ndspy.code.MainCodeFile(raw[off:off+length],ram,settings)
        segments=[(s.ramAddress,bytes(s.data)) for s in main.sections]
        view=gifts_audit.Arm9View(raw) if label in ('v4','r4') else None
        mapped=[(address,data) for address,data in segments if address<=BASE and BASE+148<=address+len(data)]
        resident=mapped[0][1][BASE-mapped[0][0]:BASE-mapped[0][0]+148] if mapped else None
        if view:
            need(resident==view.read(BASE,148),'raw/ndspy resident mapping')
            resident_offset=hex(view.offset(BASE,148))
        else:resident_offset=None
        images={};records=[]
        for oid in (10,12):
            images[oid],record=overlay(raw,oid);records.append(record)
        expected_ram=0x02237860 if language=='IT' and label=='retail' else F.OVERLAY_BASE
        need(int(records[1]['ram'],16)==expected_ram and records[1]['decoded_bytes']==0x37380,'overlay12 geometry')
        data=images[12]
        normalized,literal_proof=normalized_flags_window(data,expected_ram)
        record=dict(input=label,language=language,sha256=digest,bytes=size,overlays=records,
            header=dict(game_code=raw[12:16].decode('ascii'),revision=raw[0x1E],arm9_file_offset=hex(off),
                arm9_entry=hex(entry),arm9_ram=hex(ram),arm9_stored_bytes=length,
                fat_offset=hex(struct.unpack_from('<I',raw,0x48)[0]),y9_offset=hex(struct.unpack_from('<I',raw,0x50)[0])),
            resident_rom_offset=resident_offset,resident_bytes=len(resident) if resident is not None else None,
            resident_sha256=sha(resident) if resident is not None else None,
            flags_function_sha256=sha(data[FUNCTION-F.OVERLAY_BASE:FUNCTION_END-F.OVERLAY_BASE]),
            normalized_flags_function_sha256=sha(normalized),literal_mapping=literal_proof,
            apply_sha256=sha(data[APPLY-F.OVERLAY_BASE:FUNCTION_END-F.OVERLAY_BASE]),
            chart_sha256=sha(data[CHART-F.OVERLAY_BASE:CHART-F.OVERLAY_BASE+336]),
            arm9_segments=[dict(ram=hex(address),bytes=len(data)) for address,data in segments])
        del view
    return dict(record=record,segments=segments,overlays=images,overlay=images[12],resident=resident,normalized_flags_window=normalized)


def read_current(path,language):
    model=read_image(path,language,'r4');data=model['overlay']
    need(sha(model['resident'])==F.PAYLOAD_SHA256,'current resident payload')
    for site,target in ((0x022520C6,BASE),(0x0225268E,BASE+60)):
        need(branch(data[site-F.OVERLAY_BASE:site-F.OVERLAY_BASE+4],site,'bl')==target,'current resident seam')
    need(branch(data[0x02252138-F.OVERLAY_BASE:0x0225213A-F.OVERLAY_BASE],0x02252138,'bne')==0x022520CC,'current backedge')
    need(data[0x02252202-F.OVERLAY_BASE:0x02252204-F.OVERLAY_BASE]==bytes.fromhex('0c20'),'current HG-B13 mask')
    return model


def expect_flags(result,expected):
    need(result['flags']==expected,'flags %#x, expected %#x'%(result['flags'],expected))


class FlagsCPU:
    """Execute supplied installed segments; no game service or combiner is stubbed.

    The CLI authenticates these inputs before constructing the CPU. Supplying a
    deliberately mutated overlay is useful only for a labeled counterproof.
    """
    CTX,FLAGS,STACK,STOP=0x02350000,0x02390000,0x023B7000,0x023FF000
    def __init__(self,segments,image):
        from unicorn import Uc,UC_ARCH_ARM,UC_MODE_THUMB
        self.uc=Uc(UC_ARCH_ARM,UC_MODE_THUMB)
        for address,size in ((0x02000000,0x400000),(0x01FF8000,0x8000),(0x027E0000,0x20000)):
            self.uc.mem_map(address,size)
        for address,data in segments:self.uc.mem_write(address,data)
        self.uc.mem_write(F.OVERLAY_BASE,image)
        self.resident=bytes(self.uc.mem_read(BASE,148));self.window=bytes(image[FUNCTION-F.OVERLAY_BASE:FUNCTION_END-F.OVERLAY_BASE])
        self.apply_sha256=sha(image[APPLY-F.OVERLAY_BASE:FUNCTION_END-F.OVERLAY_BASE])
        self.regions=[(a,a+len(b)) for a,b in segments]+[(F.OVERLAY_BASE,F.OVERLAY_BASE+len(image))]
        self.uc.mem_write(self.CTX,bytes(0x4000))

    def run(self,attack,type1,type2,initial):
        from unicorn import UC_HOOK_CODE,UC_HOOK_MEM_READ,UC_HOOK_MEM_WRITE
        from unicorn.arm_const import (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3,
            UC_ARM_REG_R4,UC_ARM_REG_R5,UC_ARM_REG_R6,UC_ARM_REG_R7,UC_ARM_REG_R8,UC_ARM_REG_R9,
            UC_ARM_REG_R10,UC_ARM_REG_R11,UC_ARM_REG_SP,UC_ARM_REG_LR,UC_ARM_REG_PC,UC_ARM_REG_CPSR)
        need(all(type(v) is int and 0<=v<18 for v in (attack,type1,type2)),'fixture requires valid type IDs0..17')
        need(type(initial) is int and 0<=initial<=0xFFFFFFFF,'32-bit initial flags')
        u=self.uc;saved=(UC_ARM_REG_R4,UC_ARM_REG_R5,UC_ARM_REG_R6,UC_ARM_REG_R7,
                        UC_ARM_REG_R8,UC_ARM_REG_R9,UC_ARM_REG_R10,UC_ARM_REG_R11)
        expected=[0x44440000+i for i in range(8)]
        u.mem_write(self.STACK-4096,bytes(4096+20))
        arguments=struct.pack('<5I',0,0,type1,type2,self.FLAGS)
        u.mem_write(self.STACK,arguments);u.mem_write(self.STACK+20,b'\xA5'*8)
        u.mem_write(self.FLAGS-8,b'\xA5'*20);u.mem_write(self.FLAGS,struct.pack('<I',initial))
        for register,value in zip(saved,expected):u.reg_write(register,value)
        for register,value in ((UC_ARM_REG_R0,self.CTX),(UC_ARM_REG_R1,1),(UC_ARM_REG_R2,attack),
                (UC_ARM_REG_R3,0),(UC_ARM_REG_SP,self.STACK),(UC_ARM_REG_LR,self.STOP|1)):
            u.reg_write(register,value)
        result=dict(types=[attack,type1,type2],initial_flags=initial,instructions=0,helper_entries=0,
                    split_entries=0,stack_depth=0,apply_calls=[],writes={})
        reads=set();code_bytes=set()
        def code(cpu,address,size,unused):
            result['instructions']+=1;sp=cpu.reg_read(UC_ARM_REG_SP)
            result['stack_depth']=max(result['stack_depth'],self.STACK-sp)
            need(cpu.reg_read(UC_ARM_REG_CPSR)&32 and size in (2,4),'unexpected instruction ISA')
            need(FUNCTION<=address<FUNCTION_END or BASE<=address<BASE+60
                 or BASE+94<=address<BASE+108 or BASE+118<=address<BASE+148,'unexpected flags code %#x'%address)
            code_bytes.update(range(address,address+size))
            if address==0x022520C8:
                result['split_entries']+=1;raise ValueError('entered BL suffix')
            if address==BASE:
                result['helper_entries']+=1
                inputs=struct.unpack('<I',cpu.mem_read(sp+12,4))[0],struct.unpack('<I',cpu.mem_read(sp+48,4))[0],struct.unpack('<I',cpu.mem_read(sp+52,4))[0]
                need(inputs==(attack,type1,type2) and cpu.reg_read(UC_ARM_REG_R6)==self.FLAGS,'helper private ABI')
                result['helper_sp_delta']=self.STACK-sp
            if address==APPLY:
                effect,pointer=cpu.reg_read(UC_ARM_REG_R0),cpu.reg_read(UC_ARM_REG_R1)
                need(effect in (0,5,20) and pointer==self.FLAGS,'actual combiner arguments')
                need(len(result['apply_calls'])<8,'combiner call budget')
                result['apply_calls'].append(dict(effect=effect,flags_pointer=hex(pointer),sp_mod8=sp%8,
                    lr=hex(cpu.reg_read(UC_ARM_REG_LR))))
        def write(cpu,access,address,size,value,unused):
            if self.STACK-4096<=address and address+size<=self.STACK:name='stack'
            elif self.STACK+4<=address and address+size<=self.STACK+16:name='incoming argument home words'
            elif self.FLAGS<=address and address+size<=self.FLAGS+4:name='flags'
            else:raise ValueError('unexpected flags write %#x+%d'%(address,size))
            row=result['writes'].setdefault(name,dict(count=0,bytes=0,low=address,high=address+size))
            row['count']+=1;row['bytes']+=size;row['low']=min(row['low'],address);row['high']=max(row['high'],address+size)
        def read(cpu,access,address,size,value,unused):
            if any(a<=address and address+size<=b for a,b in self.regions):reads.update(range(address,address+size))
        hooks=[u.hook_add(UC_HOOK_CODE,code),u.hook_add(UC_HOOK_MEM_WRITE,write),u.hook_add(UC_HOOK_MEM_READ,read)]
        try:u.emu_start(FUNCTION|1,self.STOP,count=30000)
        finally:
            for hook in hooks:u.hook_del(hook)
        need(u.reg_read(UC_ARM_REG_PC)==self.STOP and u.reg_read(UC_ARM_REG_SP)==self.STACK
             and u.reg_read(UC_ARM_REG_CPSR)&32 and [u.reg_read(r) for r in saved]==expected,'flags parent return/ABI')
        need(bytes(u.mem_read(self.STACK,20))==arguments and bytes(u.mem_read(self.STACK+20,8))==b'\xA5'*8,'incoming arguments/canary')
        need(result['helper_entries']==1 and result['split_entries']==0,'single helper entry')
        need(bytes(u.mem_read(self.FLAGS-8,8))==b'\xA5'*8 and bytes(u.mem_read(self.FLAGS+4,8))==b'\xA5'*8,'flags buffer canary')
        need(bytes(u.mem_read(BASE,148))==self.resident and bytes(u.mem_read(FUNCTION,FUNCTION_END-FUNCTION))==self.window,'executed code changed')
        def ranges(addresses):
            blocks=[]
            for address in sorted(addresses):
                if blocks and blocks[-1][1]==address:blocks[-1][1]+=1
                else:blocks.append([address,address+1])
            return [dict(ram=hex(a),bytes=b-a,sha256=sha(bytes(u.mem_read(a,b-a)))) for a,b in blocks]
        result.update(flags=struct.unpack('<I',u.mem_read(self.FLAGS,4))[0],actual_apply_sha256=self.apply_sha256,
                      executed_ranges=ranges(code_bytes),immutable_read_ranges=ranges(reads))
        return result


def compile_object(work):
    """Keep the own-project ELF and independently check the two post-link fixes."""
    work=Path(work);work.mkdir(parents=True,exist_ok=True)
    payload,receipt=F.compile_native(work,BASE,retain_object=True)
    obj=(work/receipt['retained_object']).read_bytes()
    loader=F._module(SOURCE/'features/options/tools/carica_text.py','fairy_attribution_elf')
    unpatched,symbols=loader.load_text(obj,BASE,('fairy_flags_hook','fairy_scalar_tail','fairy_apply_call_1','fairy_apply_call_2'))
    need(sha(obj)==receipt['object_sha256'] and len(unpatched)==148,'retained ELF identity')
    need(symbols['fairy_flags_hook']==BASE|1 and symbols['fairy_scalar_tail']==BASE+60|1
         and symbols['fairy_code']==BASE+94|1,'ELF function geometry')
    allowed=set()
    for i,name in enumerate(('fairy_apply_call_1','fairy_apply_call_2')):
        offset=(symbols[name]&~1)-BASE
        need(offset==(24,50)[i] and unpatched[offset:offset+4]==bytes.fromhex('00f000f8'),'ELF external-call placeholder')
        need(branch(payload[offset:offset+4],BASE+offset,'bl')==APPLY,'independent post-link native target')
        allowed.update(range(offset,offset+4))
    delta=[i for i,(a,b) in enumerate(zip(unpatched,payload)) if a!=b]
    need(set(delta)<=allowed and payload.index(F.PACKED_CODES)==108,'ELF to installed-code delta/data geometry')
    need(all(unpatched[i]==payload[i] for i in range(148) if i not in allowed),'post-link changes outside two BLs')
    proof=dict(performed=True,**receipt,post_link_changed_offsets=delta,
        relevant_symbols={name:hex(symbols[name]) for name in
            ('fairy_flags_hook','fairy_scalar_tail','fairy_code','fairy_apply_call_1','fairy_apply_call_2')},
        builder_sha256=sha(Path(F.__file__).read_bytes()),
        loader_sha256=sha((SOURCE/'features/options/tools/carica_text.py').read_bytes()))
    for name,data in (('native.bin',payload),('compile-retained.json',(json.dumps(proof,indent=2)+'\n').encode())):
        target=work/name
        need(not target.exists() or target.is_file() and target.read_bytes()==data,
             'existing own-build artifact differs; use a fresh work directory: '+name)
        if not target.exists():target.write_bytes(data)
    return payload,proof


def analyze(rom,v4,base,retail,language,work=None):
    import gc
    from sgp131 import ai_scoring,reserve
    if work is None:
        compiled=None;compiler=dict(performed=False,reason='readback only; no local compilation or retained ELF proof',
            source_sha256=sha(F.NATIVE.read_bytes()))
    else:compiled,compiler=compile_object(work)
    models={name:read_image(path,language,name) for name,path in
            (('retail',retail),('base11',base),('v4',v4),('r4',rom))}
    current=models['r4'];old=models['v4'];actual=current['overlay']
    need(sha(current['resident'])==F.PAYLOAD_SHA256,'current helper identity')
    if compiled is not None:need(compiled==current['resident'],'source/object/ROM helper correspondence')
    need(old['resident']==bytes(148),'V4 exact zero slot preimage')
    need(('fairy-ai.code',BASE,148,'payload') in reserve.SUBDIVISIONS['training.extension'],'reserve owner assignment')
    scored,score_receipt=ai_scoring.patch_effectiveness_overlay(old['overlay'])
    expected,seam_receipt=F.patch_overlay(scored,BASE)
    lo,hi=FUNCTION-F.OVERLAY_BASE,FUNCTION_END-F.OVERLAY_BASE
    need(actual[lo:hi]==expected[lo:hi],'whole final flags function from both source owners')
    scalar_at=F.SCALAR_SITE-F.OVERLAY_BASE
    need(actual[scalar_at:scalar_at+4]==expected[scalar_at:scalar_at+4],'scalar seam readback only')
    need(all(model['normalized_flags_window']==old['normalized_flags_window'] for name,model in models.items() if name!='r4'),
         'retail/base/V4 flags correspondence after verified literal relocation')
    chart_at=CHART-F.OVERLAY_BASE
    charts=[model['overlay'][chart_at:chart_at+336] for model in models.values()]
    need(all(c==charts[0] for c in charts) and charts[0][-3:]==bytes.fromhex('ffff00'),'native sparse-chart continuity/sentinel')
    caller_rows=[]
    for oid,sites in CALLERS.items():
        row=next(r for r in current['record']['overlays'] if r['id']==oid);ram=int(row['ram'],16)
        for address in sites:
            raw=current['overlays'][oid][address-ram:address-ram+4]
            need(branch(raw,address,'bl')==FUNCTION,'current upstream caller')
            caller_rows.append(dict(overlay=oid,ram=hex(address),decoded_offset=hex(address-ram),target=hex(FUNCTION),sha256=sha(raw)))
    need(branch(actual[F.FLAGS_SITE-F.OVERLAY_BASE:F.FLAGS_SITE-F.OVERLAY_BASE+4],F.FLAGS_SITE,'bl')==BASE,'flags seam target')
    need(branch(actual[F.LOOP_SITE-F.OVERLAY_BASE:F.LOOP_SITE-F.OVERLAY_BASE+2],F.LOOP_SITE,'bne')==F.LOOP_TARGET,'backedge target')
    runs=[];cpu=FlagsCPU(current['segments'],actual)
    for attack,type1,type2,literal in CASES:
        for initial in (0,0xA5000000):
            result=cpu.run(attack,type1,type2,initial);expect_flags(result,initial|literal);runs.append(result)
    del cpu;gc.collect()
    mutant=bytearray(actual);at=0x02252202-F.OVERLAY_BASE
    need(mutant[at:at+2]==bytes.fromhex('0c20'),'HG-B13 counterproof preimage');mutant[at]=4
    cpu=FlagsCPU(current['segments'],bytes(mutant));counter=[]
    for attack,type1,type2,literal in CASES:
        result=cpu.run(attack,type1,type2,0)
        if (attack,type1,type2) in ((16,9,16),(16,16,9)):
            need(result['flags']==10,'old-mask counterproof outcome')
            try:expect_flags(result,literal)
            except ValueError:pass
            else:raise ValueError('old-mask false semantic success')
        else:expect_flags(result,literal)
        counter.append(dict(types=[attack,type1,type2],flags=result['flags'],required=literal,
            expected_oracle_pass=result['flags']==literal,actual_apply_sha256=result['actual_apply_sha256']))
    del cpu;gc.collect()
    records=[models[name]['record'] for name in ('retail','base11','v4','r4')]
    return dict(schema='fairy-flags-source-rom-v1',language=language,inputs=records,compile=compiler,
        reserve=dict(owner='fairy-ai.code',parent='training.extension',ram=hex(BASE),bytes=148),
        source_recipes=dict(immunity_precedence=score_receipt,seams_and_backedge=seam_receipt,
            scoped_window=dict(ram=hex(FUNCTION),bytes=hi-lo,sha256=sha(actual[lo:hi]),
                changed_addresses=[hex(F.OVERLAY_BASE+i) for i in range(lo,hi) if old['overlay'][i]!=actual[i]]),
            scalar_scope='four-byte seam and148-byte payload only; full scalar execution excluded'),
        callers=caller_rows,execution=runs,counterproof=dict(mutation='RAM-only old HG-B13 mask12→4',
            original_input_files_unchanged=True,legacy_ten_oracles_pass=True,new_two_immunity_oracles_reject=True,results=counter),
        source_sha256={str(p.relative_to(SOURCE)):sha(p.read_bytes()) for p in
            (Path(__file__),F.NATIVE,Path(F.__file__),SOURCE/'sgp131/ai_scoring.py',
             SOURCE/'sgp131/mechanics_stages.py',SOURCE/'sgp131/reserve.py',SOURCE/'sgp12/blz.py')},
        limits=['synthetic context,move1,no ability/item effects,types0..17 only',
                'eight callers statically linked,not naturally exercised',
                'no full scalar run,SAVE,hardware,RNG decision or performance claim'])


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('rom','v4','base','retail','json'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--language',choices=('EN','IT'),required=True)
    p.add_argument('--work',type=Path,help='rebuild and retain own-project ELF here; requires the pinned compiler')
    p.add_argument('--readback-only',action='store_true',help='verify exact installed bytes and execution without claiming a local rebuild')
    a=p.parse_args()
    if (a.work is None)==(not a.readback_only):p.error('choose exactly one of --work DIR or --readback-only')
    result=analyze(a.rom,a.v4,a.base,a.retail,a.language,a.work)
    a.json.parent.mkdir(parents=True,exist_ok=True);a.json.write_text(json.dumps(result,indent=2)+'\n')
    print(a.language,'flags final composition:24 invocations + HG-B13 counterproof PASS;',
          'source/ELF rebuilt' if result['compile']['performed'] else 'readback only, no local rebuild')


if __name__=='__main__':main()
