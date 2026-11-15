"""Independent functional/ARM oracles for one complete cached FindPath input.

This module predicts before the native guest. The FNT parser supplies a separate
functional result and logical read sequence; the qualified finite ARM arithmetic
helper supplies contexts and physical byte/halfword/word events.
"""
from pathlib import Path
import importlib.util
import struct


def load(path,name):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


F=load(Path(__file__).parents[1]/'tools/congela_fs_cached_findpath.py','cached_find_bench_frozen')
A=load(Path(__file__).with_name('arm32_cached_oracle.py'),'cached_find_arithmetic_oracle')
L,R,M=F.L,F.R,F.F
need,wire=F.need,M.wire
CODE_SPANS=tuple((a,n-4 if name in('seekdir','read_dir','translate')else n)
    for name,(a,n,_)in L.COMPONENTS.items()if name!='default_table')
EXPECTED_FUNCTION_COUNTS={'findpath':310,'translate':312,'seekdir':148,'read_dir':246,
                          'read_table':345,'read_memory':90,'copy':368,'strnicmp':80}


# Static authenticated instruction memory classes, not learned from a guest.
READ_SITES=frozenset((
    (0x020d4a68,2),
    (0x020d4a7c,2),
    (0x020d4a94,2),
    (0x020d4ac8,2),
    (0x020d4ad8,2),
    (0x020d4b00,2),
    (0x020d4b2c,2),
    (0x020d4b50,2),
    (0x020d4b78,4),
    (0x020d4b94,2),
    (0x020d4bb4,2),
    (0x020d4bb8,2),
    (0x020d68c8,4),
    (0x020d68cc,4),
    (0x020d68e4,4),
    (0x020d68f8,4),
    (0x020d6904,4),
    (0x020d6950,4),
    (0x020d6974,4),
    (0x020d697c,4),
    (0x020d6990,4),
    (0x020d69ac,4),
    (0x020d69d8,4),
    (0x020d69f4,4),
    (0x020d6a00,4),
    (0x020d6a18,4),
    (0x020d6a34,4),
    (0x020d6a48,4),
    (0x020d6a60,1),
    (0x020d6a64,1),
    (0x020d6a88,4),
    (0x020d6a9c,4),
    (0x020d6aa8,4),
    (0x020d6ab0,4),
    (0x020d6ac0,4),
    (0x020d6ac4,4),
    (0x020d6ae8,4),
    (0x020d6afc,4),
    (0x020d6b28,4),
    (0x020d6b48,4),
    (0x020d6b4c,4),
    (0x020d6b50,4),
    (0x020d6b5c,4),
    (0x020d6bf8,4),
    (0x020d6c04,2),
    (0x020d6c08,4),
    (0x020d6c30,4),
    (0x020d6c38,2),
    (0x020d6c40,4),
    (0x020d6c4c,2),
    (0x020d6c54,4),
    (0x020d6c58,4),
    (0x020d6c64,2),
    (0x020d6c68,4),
    (0x020d6c7c,4),
    (0x020d6c90,4),
    (0x020d6c94,4),
    (0x020d6ca0,4),
    (0x020d6cbc,4),
    (0x020d6cc0,1),
    (0x020d6cd8,4),
    (0x020d6ce8,4),
    (0x020d6cec,4),
    (0x020d6d0c,4),
    (0x020d6d10,4),
    (0x020d6d24,4),
    (0x020d6d30,4),
    (0x020d6d54,4),
    (0x020d6d58,4),
    (0x020d6d5c,4),
    (0x020d6d64,2),
    (0x020d6d80,4),
    (0x020d6d88,2),
    (0x020d6d90,2),
    (0x020d6d9c,4),
    (0x020d6da8,4),
    (0x020d6dbc,4),
    (0x020d6dc4,4),
    (0x020d6dcc,1),
    (0x020d6dec,1),
    (0x020d6e24,4),
    (0x020d6e3c,1),
    (0x020d6e60,2),
    (0x020d6e6c,4),
    (0x020d6e8c,4),
    (0x020d6ec0,4),
    (0x020d6ec4,4),
    (0x020d6ecc,4),
    (0x020d6f00,4),
    (0x020d6f28,4),
    (0x020d6f2c,4),
    (0x020d6f30,4),
    (0x020d6f34,4),
    (0x020d6f48,4),
    (0x020d6f4c,1),
    (0x020d6f5c,1),
    (0x020d6f74,4),
    (0x020d6f78,4),
    (0x020d6f80,4),
    (0x020d6f90,4),
    (0x020d7498,4),
))

WRITE_SITES=frozenset((
    (0x020d4a9c,2),
    (0x020d4ae0,2),
    (0x020d4b0c,2),
    (0x020d4b30,2),
    (0x020d4b54,2),
    (0x020d4b7c,4),
    (0x020d4ba0,2),
    (0x020d4bc8,2),
    (0x020d68c0,4),
    (0x020d68f4,4),
    (0x020d6948,4),
    (0x020d695c,4),
    (0x020d6a28,4),
    (0x020d6a3c,4),
    (0x020d6a40,4),
    (0x020d6a50,4),
    (0x020d6aa0,4),
    (0x020d6abc,4),
    (0x020d6af0,4),
    (0x020d6b58,4),
    (0x020d6bec,4),
    (0x020d6c00,4),
    (0x020d6c1c,4),
    (0x020d6c34,4),
    (0x020d6c50,2),
    (0x020d6c60,4),
    (0x020d6c70,4),
    (0x020d6c84,4),
    (0x020d6c9c,4),
    (0x020d6cac,4),
    (0x020d6ccc,4),
    (0x020d6cd4,4),
    (0x020d6d1c,1),
    (0x020d6d2c,4),
    (0x020d6d60,4),
    (0x020d6d70,2),
    (0x020d6d74,2),
    (0x020d6d78,4),
    (0x020d6d84,4),
    (0x020d6d8c,4),
    (0x020d6d98,2),
    (0x020d6da0,4),
    (0x020d6db0,4),
    (0x020d6e98,4),
    (0x020d6e9c,4),
    (0x020d6f04,4),
    (0x020d6f3c,4),
    (0x020d6f44,4),
    (0x020d6f84,4),
    (0x020d7484,4),
))

def within(address,size,base,length):return base<=address and address+size<=base+length


def read_owner(pc,address,n):
    if (pc,n)not in READ_SITES:return False
    if n==4 and address in(0x20d6c80,0x20d6dac,0x20d6a4c,0x210e12c,0x210e130):return True
    if n==4 and address in(R.ARC+28,R.ARC+52,R.ARC+80,R.ARC+88):return True
    return (within(address,n,R.FILE,72)or within(address,n,R.TOP-280,280)or
            within(address,n,R.FNT,2902)or n==1 and within(address,n,F.PATH,8))


def write_owner(pc,address,n):
    if (pc,n)not in WRITE_SITES:return False
    if within(address,n,R.TOP-280,280):return True
    if n==4 and address==R.ARC+28:return pc in(0x20d68f4,0x20d6a3c,0x20d6abc,0x20d6af0)
    if n==4 and address==R.FILE+20:return pc==0x20d6a40
    if n in(2,4)and within(address,n,R.FILE+32,16):return True
    if n==4 and within(address,n,R.FILE+48,12):return True
    return n==4 and (pc,address)in((0x20d6f3c,F.RESULT),(0x20d6f44,F.RESULT+4))


def require_memory_delta(initial,final,stores):
    """Replay whole native events; byte diffs do not change the access width."""
    replay={address:bytearray(blob)for address,blob in initial.items()}
    for event in stores:
        pc,address,n,value=(event[k]for k in('pc','address','bytes','value'))
        need(all(type(x)is int for x in(pc,address,n,value))and n in(1,2,4)and
             0<=value<1<<(8*n),'typed native delta event')
        need(write_owner(pc,address,n),'source delta owner/site')
        need(M.read(replay,address,n).hex()==event['before'],'chronological store preimage')
        M.put(replay,address,value.to_bytes(n,'little'))
    need({a:bytes(b)for a,b in replay.items()}==final,'complete delta replay including untouched neighbors')


def predict(f):
    need(type(f['precompleted_result'])is bool,'typed FindPath projection')
    expected=[R.FILE]+[0xB0000000+i*0x010101 for i in range(1,13)]+[R.TOP,F.RETURN,0x6000001f]
    need(f['entry_pc']==F.ENTRY and wire(f['entry_regs'])==wire(expected),'exact isolated FindPath entry ABI')
    for name,(address,size,digest)in L.COMPONENTS.items():
        need(R.sha(M.read(f['pages'],address,size))==digest,'exact oracle component '+name)
    sites={'read':set(),'write':set()}
    for base,size in CODE_SPANS:
        for pc in range(base,base+size,4):
            word=int.from_bytes(M.read(f['pages'],pc,4),'little');group=A.validate_word(word)
            if group in('memory','block'):
                width=4 if group=='block'else(1 if word&(1<<22)else 4)if(word>>26)&3==1 else 2
                sites['read'if word&(1<<20)else'write'].add((pc,width))
    need(sites['read']==READ_SITES and sites['write']==WRITE_SITES,'authenticated static memory site/width maps')
    need(R.sha(M.read(f['pages'],R.FNT,2902))==R.FNT_SHA and
         R.sha(M.read(f['pages'],R.FAT,4104))==R.FAT_SHA,'authenticated oracle table resources')
    initial_file=M.read(f['pages'],R.FILE,72);archive=M.read(f['pages'],R.ARC,92)
    need(R.u32(archive,28)==0x17 and R.u32(archive,52)==R.FNT and
         R.u32(archive,80)==0x20d7484 and R.u32(archive,88)&12==0,'cached RUNNING archive/commands2and3')
    need(M.read(f['pages'],F.PATH,8)==L.PATH+b'\0','exact normalized FindPath path')
    meta=L.resolve_path(M.read(f['pages'],R.FNT,2902),L.PATH)
    result=A.run(f,CODE_SPANS,F.RETURN,cap=8192,read_guard=read_owner,write_guard=write_owner)
    counts={name:0 for name in EXPECTED_FUNCTION_COUNTS}
    for item in result['flow']:
        owners=[name for name,(a,n,_)in L.COMPONENTS.items()if name in counts and a<=item['pc']<a+n]
        need(len(owners)==1,'one native function owner');counts[owners[0]]+=1
    need(counts==EXPECTED_FUNCTION_COUNTS and len(result['flow'])==1899,'independent source block count1899')
    entries={name:sum(x['pc']==L.COMPONENTS[name][0]for x in result['flow'])for name in counts}
    need(entries==dict(findpath=1,translate=8,seekdir=4,read_dir=4,read_table=15,read_memory=15,copy=15,strnicmp=4),'functional finite callgraph')
    copies=[dict(offset=x['regs'][0]-R.FNT,bytes=x['regs'][2])for x in result['flow']if x['pc']==0x20d4a50]
    need(copies==meta['table_reads'],'independent FNT logical reads vs native copy arguments')
    prop=meta['directory_property'];expected_file=bytearray(initial_file)
    struct.pack_into('<I',expected_file,20,0)
    expected_file[32:48]=struct.pack('<IHHII',R.ARC,prop['own_id'],prop['index'],R.FNT+prop['offset'],prop['parent'])
    expected_file[48:60]=struct.pack('<III',R.TOP-184,0,0)
    need(M.read(result['pages'],R.FILE,72)==bytes(expected_file),'functional complete File72')
    need(M.read(result['pages'],F.RESULT,8)==struct.pack('<II',R.ARC,meta['file_id']),'functional FileID8')
    need(M.read(result['pages'],R.ARC,92)==archive,'functional full archive restored to projected input')
    expected_regs=list(f['entry_regs']);expected_regs[:3]=[0,meta['file_id'],R.ARC]
    expected_regs[12]=0xffffffef;expected_regs[14]=1
    need(wire(result['returned'])==wire(expected_regs),'source full16 FindPath return including LR1')
    need(result['native_peak']==280,'source nested peak280')
    require_memory_delta(f['pages'],result['pages'],result['stores'])
    result.update(function_counts=counts,entry_counts=entries,logical_copies=copies,source_metadata=meta)
    return result


BACKEND=dict(unicorn='2.1.4',CPU_model=17,
    scope='CortexA15 backend executing ARMv5 code; not ARM946 timing/cache/IRQ')


def observation_policy(predicted):
    """Only enforcement metadata reaches the producer, never predicted state."""
    return dict(code_starts=frozenset(x['pc']for x in predicted['flow']),
        read_sites=frozenset((x['pc'],x['address'],x['bytes'])for x in predicted['reads']),
        write_sites=frozenset((x['pc'],x['address'],x['bytes'])for x in predicted['stores']))


def run(f,policy,observe=True):
    import unicorn as U
    from unicorn import arm_const as C
    need(type(observe)is bool and U.__version__==BACKEND['unicorn'],'qualified observer/backend version')
    uc=U.Uc(U.UC_ARCH_ARM,U.UC_MODE_ARM);uc.ctl_set_cpu_model(C.UC_CPU_ARM_CORTEX_A15)
    backend=dict(unicorn=U.__version__,CPU_model=uc.ctl_get_cpu_model(),scope=BACKEND['scope'])
    need(wire(backend)==wire(BACKEND),'actual backend identity')
    registers=tuple(getattr(C,'UC_ARM_REG_R'+str(i))for i in range(13))+(C.UC_ARM_REG_SP,C.UC_ARM_REG_LR,C.UC_ARM_REG_CPSR)
    for address,blob in f['pages'].items():uc.mem_map(address,4096);uc.mem_write(address,blob)
    uc.reg_write(C.UC_ARM_REG_CPSR,f['entry_regs'][15])
    for register,value in zip(registers[:15],f['entry_regs'][:15]):uc.reg_write(register,value)
    flow=[];reads=[];stores=[];seen=set();count=0;callbacks=0;read_count=0;store_count=0;low=R.TOP;stopped=False
    def state():return [uc.reg_read(register)&0xffffffff for register in registers]
    def instruction(machine,address,size,user):
        nonlocal count,callbacks,low,stopped
        callbacks+=1
        if address==F.RETURN:stopped=True;machine.emu_stop();return
        need(size==4 and address in policy['code_starts'],'native instruction outside exact source route')
        count+=1;need(count<=8192,'native instruction cap')
        seen.add(address);low=min(low,machine.reg_read(C.UC_ARM_REG_SP))
        if observe:flow.append(dict(pc=address,regs=state()))
    def access(machine,kind,address,size,value,user):
        nonlocal read_count,store_count
        pc=machine.reg_read(C.UC_ARM_REG_PC)
        if kind==U.UC_MEM_WRITE:
            need((pc,address,size)in policy['write_sites'],'native write outside exact source site/address/width')
            store_count+=1
            if observe:stores.append(dict(pc=pc,address=address,bytes=size,before=bytes(machine.mem_read(address,size)).hex(),value=value&((1<<(8*size))-1)))
        else:
            need((pc,address,size)in policy['read_sites'],'native read outside exact source site/address/width')
            read_count+=1
            if observe:reads.append(dict(pc=pc,address=address,bytes=size,hex=bytes(machine.mem_read(address,size)).hex()))
    uc.hook_add(U.UC_HOOK_CODE,instruction);uc.hook_add(U.UC_HOOK_MEM_READ|U.UC_HOOK_MEM_WRITE,access)
    fault=None
    try:uc.emu_start(F.ENTRY,0,timeout=1000000,count=8192)
    except(ValueError,U.UcError)as error:fault=type(error).__name__+': '+str(error)
    pages={address:bytes(uc.mem_read(address,4096))for address in f['pages']}
    return dict(schema='native-fs-cached-findpath-raw-v1',observed=observe,initial=F.input_record(f),
        fault=fault,stopped=stopped,stop_pc=uc.reg_read(C.UC_ARM_REG_PC),returned=state(),flow=flow,reads=reads,stores=stores,
        native_count=count,unique_native_starts=len(seen),callback_count=callbacks,read_count=read_count,store_count=store_count,
        native_peak=R.TOP-low,models=[],runtime_host_writes=[],backend=backend,
        final_map_sha256=M.map_digest(pages),final_pages=[dict(ram=a,hex=b.hex())for a,b in sorted(pages.items())])


def require_run(f,raw):
    predicted=predict(f)
    need(raw.get('schema')=='native-fs-cached-findpath-raw-v1','native raw schema')
    need(all(type(raw[k])is int for k in('native_count','unique_native_starts','callback_count','read_count','store_count','native_peak','stop_pc')),'typed native counters/PC')
    need(wire(raw['initial'])==wire(F.input_record(f)),'complete frozen FindPath input')
    need(wire(raw.get('backend'))==wire(BACKEND),'qualified backend identity')
    need(raw['fault']is None and raw['stopped']is True and raw['stop_pc']==F.RETURN,'finite native original POP return')
    need(raw['models']==raw['runtime_host_writes']==[],'zero native service model/host writes')
    need((raw['native_count'],raw['unique_native_starts'],raw['callback_count'],raw['read_count'],raw['store_count'],raw['native_peak'])==(1899,351,1900,570,421,280),'source count/owner/budget')
    need(wire(raw['returned'])==wire(predicted['returned']),'source full16 FindPath return ABI')
    need(raw['final_map_sha256']==M.map_digest(predicted['pages']),'source complete final map hash')
    need(wire(raw['final_pages'])==wire([dict(ram=a,hex=b.hex())for a,b in sorted(predicted['pages'].items())]),'source all eleven final pages')
    if raw['observed']is True:
        for key in('flow','reads','stores'):need(wire(raw[key])==wire(predicted[key]),'source native '+key)
    else:need(raw['observed']is False and raw['flow']==raw['reads']==raw['stores']==[],'OFF no observation projections')
    return predicted
