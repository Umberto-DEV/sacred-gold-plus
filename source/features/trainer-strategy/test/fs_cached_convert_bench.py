"""Complete Convert functional oracle plus finite ARM/IRQ source predictor.

P81 arithmetic and native runner design reused; prior modules remain immutable.
Predictions precede the CPU. Only enforcement sets reach the native producer.
"""
from pathlib import Path
import importlib.util
import struct


def load(path,name):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


F=load(Path(__file__).parents[1]/'tools/congela_fs_cached_convert.py','convert_bench_frozen')
A=load(Path(__file__).with_name('arm32_sync_oracle.py'),'convert_sync_arithmetic')
L,R,M=F.L,F.R,F.M
need,wire=F.need,M.wire
CODE_SPANS=L.CODE_SPANS


# Static memory classes decoded offline from the authenticated 922 ARM starts.
READ_SITES=frozenset((
    (0x20d1ed8,4),(0x20d1f0c,4),(0x20d1f30,4),(0x20d4a68,2),
    (0x20d4a7c,2),(0x20d4a94,2),(0x20d4ac8,2),(0x20d4ad8,2),
    (0x20d4b00,2),(0x20d4b2c,2),(0x20d4b50,2),(0x20d4b78,4),
    (0x20d4b94,2),(0x20d4bb4,2),(0x20d4bb8,2),(0x20d6874,4),
    (0x20d687c,4),(0x20d689c,4),(0x20d68bc,4),(0x20d68c8,4),
    (0x20d68cc,4),(0x20d68e4,4),(0x20d68f8,4),(0x20d6904,4),
    (0x20d6950,4),(0x20d6974,4),(0x20d697c,4),(0x20d6990,4),
    (0x20d69ac,4),(0x20d69d8,4),(0x20d69f4,4),(0x20d6a00,4),
    (0x20d6a18,4),(0x20d6a34,4),(0x20d6a48,4),(0x20d6a60,1),
    (0x20d6a64,1),(0x20d6a88,4),(0x20d6a9c,4),(0x20d6aa8,4),
    (0x20d6ab0,4),(0x20d6ac0,4),(0x20d6ac4,4),(0x20d6ae8,4),
    (0x20d6afc,4),(0x20d6b28,4),(0x20d6b48,4),(0x20d6b4c,4),
    (0x20d6b50,4),(0x20d6b5c,4),(0x20d6bf8,4),(0x20d6c04,2),
    (0x20d6c08,4),(0x20d6c30,4),(0x20d6c38,2),(0x20d6c40,4),
    (0x20d6c4c,2),(0x20d6c54,4),(0x20d6c58,4),(0x20d6c64,2),
    (0x20d6c68,4),(0x20d6c7c,4),(0x20d6c90,4),(0x20d6c94,4),
    (0x20d6ca0,4),(0x20d6cbc,4),(0x20d6cc0,1),(0x20d6cd8,4),
    (0x20d6ce8,4),(0x20d6cec,4),(0x20d6d0c,4),(0x20d6d10,4),
    (0x20d6d24,4),(0x20d6d30,4),(0x20d6d54,4),(0x20d6d58,4),
    (0x20d6d5c,4),(0x20d6d64,2),(0x20d6d80,4),(0x20d6d88,2),
    (0x20d6d90,2),(0x20d6d9c,4),(0x20d6da8,4),(0x20d6dbc,4),
    (0x20d6dc4,4),(0x20d6dcc,1),(0x20d6dec,1),(0x20d6e24,4),
    (0x20d6e3c,1),(0x20d6e60,2),(0x20d6e6c,4),(0x20d6e8c,4),
    (0x20d6ec0,4),(0x20d6ec4,4),(0x20d6ecc,4),(0x20d6f00,4),
    (0x20d6f28,4),(0x20d6f2c,4),(0x20d6f30,4),(0x20d6f34,4),
    (0x20d6f48,4),(0x20d6f4c,1),(0x20d6f5c,1),(0x20d6f74,4),
    (0x20d6f78,4),(0x20d6f80,4),(0x20d6f90,4),(0x20d7498,4),
    (0x20d74ac,4),(0x20d74c8,4),(0x20d74d4,4),(0x20d74ec,4),
    (0x20d74f0,4),(0x20d7508,4),(0x20d7520,4),(0x20d7530,4),
    (0x20d7548,4),(0x20d7560,4),(0x20d756c,4),(0x20d758c,4),
    (0x20d75a8,4),(0x20d75b4,4),(0x20d75c8,4),(0x20d75d8,4),
    (0x20d7608,4),(0x20d761c,4),(0x20d7620,4),(0x20d7638,4),
    (0x20d7644,4),(0x20d765c,4),(0x20d766c,4),(0x20d7684,4),
    (0x20d76ac,4),(0x20d774c,4),(0x20d7760,4),(0x20d7774,4),
    (0x20d7784,4),(0x20d7790,4),(0x20d77a4,4),(0x20d77b8,4),
    (0x20d77e0,4),(0x20d77e8,4),(0x20d77f4,4),(0x20d77f8,4),
    (0x20d7810,4),(0x20d7820,4),(0x20d783c,4),(0x20d7850,4),
    (0x20d7868,4),(0x20d787c,4),(0x20d7888,4),(0x20d789c,4),
    (0x20d78a8,4),(0x20d78d0,4),(0x20d78dc,4),(0x20d7900,4),
    (0x20d790c,4),(0x20d7928,4),(0x20d7fcc,1),(0x20d7fe8,4),
    (0x20d7ff0,4),(0x20d800c,4),(0x20d8014,4),(0x20d8020,1),
    (0x20d8054,4),(0x20d8058,4),(0x20d8074,4),(0x20d8090,1),
    (0x20d80b0,4),(0x20d80c4,4),(0x20d80fc,4),(0x20d81bc,4),
))
WRITE_SITES=frozenset((
    (0x20d1ecc,4),(0x20d1efc,4),(0x20d1f00,4),(0x20d1f04,4),
    (0x20d1f08,4),(0x20d1f1c,4),(0x20d1f20,4),(0x20d4a9c,2),
    (0x20d4ae0,2),(0x20d4b0c,2),(0x20d4b30,2),(0x20d4b54,2),
    (0x20d4b7c,4),(0x20d4ba0,2),(0x20d4bc8,2),(0x20d6864,4),
    (0x20d6884,4),(0x20d688c,4),(0x20d6894,4),(0x20d6898,4),
    (0x20d68a8,4),(0x20d68ac,4),(0x20d68c0,4),(0x20d68f4,4),
    (0x20d6948,4),(0x20d695c,4),(0x20d6a28,4),(0x20d6a3c,4),
    (0x20d6a40,4),(0x20d6a50,4),(0x20d6aa0,4),(0x20d6abc,4),
    (0x20d6af0,4),(0x20d6b58,4),(0x20d6bec,4),(0x20d6c00,4),
    (0x20d6c1c,4),(0x20d6c34,4),(0x20d6c50,2),(0x20d6c60,4),
    (0x20d6c70,4),(0x20d6c84,4),(0x20d6c9c,4),(0x20d6cac,4),
    (0x20d6ccc,4),(0x20d6cd4,4),(0x20d6d1c,1),(0x20d6d2c,4),
    (0x20d6d60,4),(0x20d6d70,2),(0x20d6d74,2),(0x20d6d78,4),
    (0x20d6d84,4),(0x20d6d8c,4),(0x20d6d98,2),(0x20d6da0,4),
    (0x20d6db0,4),(0x20d6e98,4),(0x20d6e9c,4),(0x20d6f04,4),
    (0x20d6f3c,4),(0x20d6f44,4),(0x20d6f84,4),(0x20d7484,4),
    (0x20d749c,4),(0x20d74d0,4),(0x20d7514,4),(0x20d7594,4),
    (0x20d75d4,4),(0x20d7640,4),(0x20d7658,4),(0x20d7694,4),
    (0x20d7744,4),(0x20d7788,4),(0x20d7798,4),(0x20d77a0,4),
    (0x20d77b0,4),(0x20d77f0,4),(0x20d7800,4),(0x20d780c,4),
    (0x20d782c,4),(0x20d7830,4),(0x20d7838,4),(0x20d7874,4),
    (0x20d78a4,4),(0x20d7f9c,4),(0x20d7fa0,4),(0x20d7fa4,4),
    (0x20d7fa8,4),(0x20d7fac,4),(0x20d7fb4,4),(0x20d7fb8,4),
    (0x20d7fc0,4),(0x20d7ff4,2),(0x20d7ff8,4),(0x20d7ffc,4),
    (0x20d8000,2),(0x20d8018,4),(0x20d807c,4),(0x20d8080,4),
    (0x20d8084,2),(0x20d8088,2),(0x20d80b8,4),(0x20d80bc,4),
    (0x20d80c8,4),(0x20d80d4,4),(0x20d80d8,4),(0x20d80e4,4),
    (0x20d80e8,4),(0x20d8180,4),
))

def within(a,n,base,size):return base<=a and a+n<=base+size


def memory_sites(pages):
    sites={'read':set(),'write':set()}
    for base,size in CODE_SPANS:
        for pc in range(base,base+size,4):
            word=int.from_bytes(M.read(pages,pc,4),'little');group=A.validate_word(word)
            if group in('memory','block'):
                width=4 if group=='block'else(1 if word&(1<<22)else 4)if(word>>26)&3==1 else 2
                sites['read'if word&(1<<20)else'write'].add((pc,width))
    return sites


def read_owner(pc,a,n):
    if(pc,n)not in READ_SITES:return False
    if within(a,n,R.TOP-F.FRAME,F.FRAME):return True
    if n==4 and(within(a,n,R.ARC,92)or within(a,n,L.ROOT,12)):return True
    if within(a,n,R.FNT,2902)or n==1 and within(a,n,L.PATH,8):return True
    if n==4 and a in(0x210e12c,0x210e130,0x210e134):return True
    return n==4 and any(a==base+size-L.POOLS[name] for name,(base,size,_)in L.COMPONENTS.items()if name in L.POOLS)


def write_owner(pc,a,n):
    if(pc,n)not in WRITE_SITES:return False
    if within(a,n,R.TOP-F.FRAME,F.FRAME):return True
    if n==4 and a==R.ARC+28:return pc in(0x20d68f4,0x20d6a3c,0x20d6abc,0x20d6af0,0x20d7874,0x20d7640)
    if n==4 and a==R.ARC+36:return pc in(0x20d782c,0x20d6884)
    return n==4 and(pc,a)in((0x20d6f3c,F.RESULT),(0x20d6f44,F.RESULT+4))


def require_memory_delta(initial,final,stores):
    replay={a:bytearray(b)for a,b in initial.items()}
    for e in stores:
        pc,a,n,value=(e[k]for k in('pc','address','bytes','value'))
        need(all(type(x)is int for x in(pc,a,n,value))and n in(1,2,4)and 0<=value<1<<(8*n),'typed native delta event')
        need(write_owner(pc,a,n),'source delta owner/site')
        need(M.read(replay,a,n).hex()==e['before'],'chronological store preimage');M.put(replay,a,value.to_bytes(n,'little'))
    need({a:bytes(b)for a,b in replay.items()}==final,'whole map chronological replay')


def predict(f):
    need(type(f['precompleted_result'])is bool,'typed result projection')
    expected=[F.RESULT,L.PATH]+[0xB0000000+i*0x010101 for i in range(2,13)]+[R.TOP,F.RETURN,0x6000001f]
    need(f['entry_pc']==F.ENTRY and wire(f['entry_regs'])==wire(expected),'exact complete Convert entry ABI')
    for name,(a,n,digest)in L.COMPONENTS.items():need(R.sha(M.read(f['pages'],a,n))==digest,'exact composed component '+name)
    need(R.sha(M.read(f['pages'],R.FNT,2902))==R.FNT_SHA and R.sha(M.read(f['pages'],R.FAT,4104))==R.FAT_SHA,'exact cached tables')
    need(R.sha(M.read(f['pages'],L.ROOT,12))==L.ROOT_SHA and M.read(f['pages'],L.PATH,8)==L.PATH_BYTES,'root/path input identity')
    archive=M.read(f['pages'],R.ARC,92)
    need(R.u32(archive,28)==7 and R.u32(archive,88)in(0,2)and archive[4:28]==b'\0'*24 and archive[32:40]==b'\0'*8,'quiescent ARC/proc projection')
    meta=L.L.resolve_path(M.read(f['pages'],R.FNT,2902),L.PATH_BYTES[:-1]);sites=memory_sites(f['pages'])
    need(sites==dict(read=set(READ_SITES),write=set(WRITE_SITES)),'authenticated static site/width maps')
    result=A.run(f,CODE_SPANS,F.RETURN,read_guard=lambda pc,a,n:(pc,n)in sites['read']and read_owner(pc,a,n),
        write_guard=lambda pc,a,n:(pc,n)in sites['write']and write_owner(pc,a,n))
    names=set(L.COMPONENTS)-{'default_table'}
    counts={name:sum(a<=x['pc']<a+n-L.POOLS.get(name,0)for x in result['flow'])for name,(a,n,_)in L.COMPONENTS.items()if name in names}
    entries={name:sum(x['pc']==L.COMPONENTS[name][0]for x in result['flow'])for name in names}
    need(entries==dict(init=1,convert=1,find=1,send=1,execute=1,release=1,wakeup=1,next=1,disable=5,restore=5,
        findpath=1,translate=11,seekdir=4,read_dir=6,read_table=20,read_memory=20,copy=20,strnicmp=6),'source complete API callgraph')
    copies=[dict(offset=x['regs'][0]-R.FNT,bytes=x['regs'][2])for x in result['flow']if x['pc']==0x20d4a50]
    need(copies==meta['table_reads'],'functional FNT logical reads / native copy arguments')
    prop=meta['directory_property'];file=bytearray(b'\xa5'*72)
    for off,value in((0,0),(4,0),(8,R.ARC),(12,0),(16,4),(20,0),(24,0),(28,0),(60,L.PATH),(64,0),(68,F.RESULT)):
        struct.pack_into('<I',file,off,value)
    file[32:48]=struct.pack('<IHHII',R.ARC,prop['own_id'],prop['index'],R.FNT+prop['offset'],prop['parent'])
    file[48:60]=struct.pack('<III',R.TOP-368,0,0)
    need(M.read(result['pages'],F.FILE,72)==bytes(file),'functional complete scratch File72 / partial Init lifetime')
    need(M.read(result['pages'],F.RESULT,8)==struct.pack('<II',R.ARC,140),'functional ID140 output')
    need(M.read(result['pages'],R.ARC,92)==archive,'functional full ARC quiescence restored')
    expected[0:3]=[1,0x6000009f,0x6000001f];expected[12]=0xfffffff0;expected[14]=0x20d76a4;expected[15]=0x2000001f
    need(wire(result['returned'])==wire(expected),'source complete Convert full16 return')
    need(result['native_peak']==464,'source complete frame464')
    require_memory_delta(f['pages'],result['pages'],result['stores'])
    need((len(result['flow']),len({x['pc']for x in result['flow']}),len(result['reads']),len(result['stores']))==(2744,596,819,616),'pre-CPU source count signature')
    result.update(function_counts=counts,entry_counts=entries,logical_copies=copies,source_metadata=meta,
        static_memory_sites={k:sorted(v)for k,v in sites.items()})
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
    return dict(schema='native-fs-cached-convert-raw-v1',observed=observe,initial=F.input_record(f),
        fault=fault,stopped=stopped,stop_pc=uc.reg_read(C.UC_ARM_REG_PC),returned=state(),flow=flow,reads=reads,stores=stores,
        native_count=count,unique_native_starts=len(seen),callback_count=callbacks,read_count=read_count,store_count=store_count,
        native_peak=R.TOP-low,models=[],runtime_host_writes=[],backend=backend,
        final_map_sha256=M.map_digest(pages),final_pages=[dict(ram=a,hex=b.hex())for a,b in sorted(pages.items())])


def require_run(f,raw):
    predicted=predict(f)
    need(raw.get('schema')=='native-fs-cached-convert-raw-v1','native raw schema')
    need(all(type(raw[k])is int for k in('native_count','unique_native_starts','callback_count','read_count','store_count','native_peak','stop_pc')),'typed native counters/PC')
    need(wire(raw['initial'])==wire(F.input_record(f)),'complete frozen Convert input')
    need(wire(raw.get('backend'))==wire(BACKEND),'qualified backend identity')
    need(raw['fault']is None and raw['stopped']is True and raw['stop_pc']==F.RETURN,'finite native original POP return')
    need(raw['models']==raw['runtime_host_writes']==[],'zero native service model/host writes')
    need((raw['native_count'],raw['unique_native_starts'],raw['callback_count'],raw['read_count'],raw['store_count'],raw['native_peak'])==(len(predicted['flow']),len({x['pc']for x in predicted['flow']}),len(predicted['flow'])+1,len(predicted['reads']),len(predicted['stores']),predicted['native_peak']),'source count/owner/budget')
    need(wire(raw['returned'])==wire(predicted['returned']),'source full16 Convert return ABI')
    need(raw['final_map_sha256']==M.map_digest(predicted['pages']),'source complete final map hash')
    need(wire(raw['final_pages'])==wire([dict(ram=a,hex=b.hex())for a,b in sorted(predicted['pages'].items())]),'source all final pages')
    if raw['observed']is True:
        for key in('flow','reads','stores'):need(wire(raw[key])==wire(predicted[key]),'source native '+key)
    else:need(raw['observed']is False and raw['flow']==raw['reads']==raw['stores']==[],'OFF no observation projections')
    return predicted
