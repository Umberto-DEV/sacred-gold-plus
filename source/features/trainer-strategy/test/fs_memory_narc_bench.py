"""Native Thumb NARC reader through all thirty ARM SDK bodies.

The source predictor composes finite instruction arithmetic; the producer is
one uninterrupted CPU run. Only fetch/access admission metadata reaches it.
"""
from pathlib import Path
import importlib.util
import struct
import types


def load(path,name):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


F=load(Path(__file__).parents[1]/'tools/congela_fs_memory_narc.py','native_narc_frozen')
A=load(Path(__file__).with_name('arm_thumb_narc_oracle.py'),'native_narc_source_arithmetic')
P=load(Path(__file__).with_name('fs_memory_read_bench.py'),'native_narc_parent_memory_owners')
L,R,M,need,wire=F.L,F.R,F.M,F.need,F.M.wire
CODE_SPANS=F.P.CODE_SPANS
THUMB_READ=frozenset((pc,n)for pc,n in((0x2007510,4),(0x2007514,4),(0x200751c,4),(0x2007366,4),(0x2007388,2),
    (0x2007392,4),(0x20073b4,4),(0x20073d0,4),(0x20073d6,4),(0x20073e2,4),(0x20073e8,4),(0x20073ea,4),
    (0x20073f8,4),(0x20073fa,4),(0x200740a,4)))
THUMB_WRITE=frozenset((pc,n)for pc,n in((0x2007508,4),(0x2007512,4),(0x200732c,4),(0x2007334,4),
    (0x2007336,4),(0x2007338,4),(0x200733a,4),(0x200733e,2),(0x2007344,4),(0x20073ee,4)))
READ_SITES=frozenset((pc,n)for pc,n in P.READ_SITES if pc<0x22f0000)|THUMB_READ
WRITE_SITES=frozenset((pc,n)for pc,n in P.WRITE_SITES if pc<0x22f0000)|THUMB_WRITE
BACKEND=P.BACKEND


def within(a,n,base,size):return base<=a and a+n<=base+size


def read_owner(pc,a,n):
    if(pc,n)not in READ_SITES:return False
    if within(a,n,R.TOP-F.FRAME,F.FRAME):return True
    if n==4 and(within(a,n,R.ARC,92)or within(a,n,F.ROOT,12)or within(a,n,R.FAT,4104)):return True
    if within(a,n,R.FNT,2902)or n==1 and within(a,n,F.PATH,8):return True
    if any(within(a,n,F.P.ARCHIVE_BASE+0x1093800+relative,size)for relative,size in L.WINDOWS):return True
    if n==4 and any(a==base for base,size,digest in L.DATA.values()):return True
    if n==4 and a in(0x210e124,0x210e12c,0x210e130,0x210e134,0x210e13c,0x210e140,0x210e144):return True
    return n==4 and any(a==base+size-F.P.POOLS[name]for name,(base,size,digest)in F.P.COMPONENTS.items()if name in F.P.POOLS)


def write_owner(pc,a,n):
    if(pc,n)not in WRITE_SITES:return False
    if within(a,n,R.TOP-F.FRAME,F.FRAME):return True
    if n==4 and a in(R.ARC+28,R.ARC+36):return P.write_owner(pc,a,n)
    return n==4 and within(a,n,F.DEST,16)and pc==0x20d4b7c


def require_memory_delta(initial,final,stores):
    fn=types.FunctionType(P.require_memory_delta.__code__,{**vars(P),'write_owner':write_owner})
    return fn(initial,final,stores)


def predict(f):
    expected=[F.DEST,11,310,0x33333303]+[0xb0000000+i*0x010101 for i in range(4,13)]+[R.TOP,F.RETURN|1,0x6000003f]
    need(type(f['precompleted_destination'])is bool and f['entry_pc']==F.ENTRY and wire(f['entry_regs'])==wire(expected),'exact native NARC entry ABI')
    for name,(a,n,digest)in F.P.COMPONENTS.items():need(R.sha(M.read(f['pages'],a,n))==digest,'exact SDK component '+name)
    parts={name:M.read(f['pages'],a,n)for name,(a,n,count,digest)in L.THUMB.items()}
    thumb=L.thumb_code(parts)
    for name,(a,n,digest)in L.DATA.items():need(R.sha(M.read(f['pages'],a,n))==digest,'exact native NARC data '+name)
    need(R.sha(M.read(f['pages'],R.FNT,2902))==R.FNT_SHA and R.sha(M.read(f['pages'],R.FAT,4104))==R.FAT_SHA,'exact cached tables')
    need(R.sha(M.read(f['pages'],F.ROOT,12))==F.P.L.L.ROOT_SHA,'exact FS root')
    P.require_memory_archive(M.read(f['pages'],R.ARC,92))
    need(M.read(f['pages'],R.TOP-F.FRAME,F.FRAME)==b'\xa5'*F.FRAME,'native initializes FILE and parser locals')
    member=M.read(f['pages'],F.P.MEMBER_SOURCE,16)
    need(R.sha(member)==F.P.MEMBER_SHA and M.read(f['pages'],F.DEST,16)==(member if f['precompleted_destination']else b'\xa5'*16),'explicit destination projection')
    sites=types.FunctionType(P.memory_sites.__code__,{**vars(P),'CODE_SPANS':CODE_SPANS,'A':A.A})(f['pages'])
    need(sites==dict(read=set(READ_SITES-THUMB_READ),write=set(WRITE_SITES-THUMB_WRITE)),'authenticated SDK memory sites')
    result=A.run(f,CODE_SPANS,F.RETURN,thumb_code=thumb,read_guard=read_owner,write_guard=write_owner)
    counts={name:sum(a<=x['pc']<a+n-F.P.POOLS.get(name,0)for x in result['flow'])for name,(a,n,digest)in F.P.COMPONENTS.items()if name!='default_table'}
    entries={name:sum(x['pc']==F.P.COMPONENTS[name][0]for x in result['flow'])for name in counts}
    need(entries==dict(open=1,fast=1,init=2,convert=1,find=1,send=10,execute=10,release=10,wakeup=10,next=10,disable=57,restore=57,
        fast_command=1,direct_command=1,findpath=1,translate=21,seekdir=4,read_dir=6,read_table=21,read_memory=21,copy=28,strnicmp=6,
        read_wrapper=7,read_core=7,wait=7,seek=5,close=1,read_command=7,read_callback=7,close_command=1),'source complete NARC callgraph')
    need(len(result['flow'])==6262 and sum(counts.values())==6159 and sum(x['pc']in thumb for x in result['flow'])==103,'manual forecast6262 original ROM instructions')
    need((len(result['reads']),len(result['stores']),result['native_peak'])==(1732,1299,616),'manual forecast read/store/stack')
    lrs=(0x200734b,0x2007353,0x200735d,0x2007367,0x2007373,0x200737d,0x2007387,0x20073a1,0x20073ab,0x20073bb,0x20073c5,0x20073cf,0x20073e3,0x2007403,0x2007409)
    calls=[x for x in result['flow']if x['pc']in A.RETURNS and x['regs'][14]&1]
    need(len(calls)==15 and tuple(x['regs'][14]for x in calls)==lrs and all(x['regs'][0]==F.FILE and x['regs'][13]==F.LOCAL and not x['regs'][15]&32 for x in calls),'fifteen original native API entries/LR/SP/FILE')
    need(calls[1]['regs'][:4]==[F.FILE,F.PATH,0,0],'native Init clobbers R2 before Open')
    callbacks=[x for x in result['flow']if x['pc']==0x20d7448]
    destinations=(F.LOCAL+20,F.LOCAL+20,F.LOCAL+8,F.LOCAL+20,F.LOCAL+16,F.LOCAL+12,F.DEST)
    need([x['regs'][:4]for x in callbacks]==[[R.ARC,dest,0x1093800+relative,n]for dest,(relative,n)in zip(destinations,L.WINDOWS)],'seven source-selected memory callbacks36')
    advances=[x for x in result['stores']if x['pc']==0x20d6bac]
    need([(x['address'],x['before'],x['value'])for x in advances]==[(F.FILE+44,struct.pack('<I',0x1093800+a).hex(),0x1093800+a+n)for a,n in L.WINDOWS],'read advances old position before callbacks')
    seeks=[x['regs'][1:3]for x in calls if x['pc']==0x20d83dc]
    need(seeks==[[a,0]for a in(0xc,0x14,0xed8,0x9cc,0x224c)],'five native SET seeks')
    need(M.read(result['pages'],F.DEST,16)==member,'independent member16 output')
    final=M.read(result['pages'],F.FILE,72)
    need(all(R.u32(final,a)==v for a,v in((8,0),(12,0),(16,14),(20,0),(32,140),(36,0x1093800),(40,0x109645c),(44,0x1095a5c),(48,F.DEST),(52,16),(56,16))),'source closed final FILE lifetime/position/last request')
    need(M.read(result['pages'],R.ARC,92)==M.read(f['pages'],R.ARC,92),'whole projected archive restored')
    expected[:3]=[1,0,0x6000001f];expected[12]=F.DEST+16;expected[14]=0x20d76a4;expected[15]=0x2000003f
    need(wire(result['returned'])==wire(expected),'source original caller full16 return')
    require_memory_delta(f['pages'],result['pages'],result['stores'])
    result.update(function_counts=counts,entry_counts=entries,original_ROM_count=6262,Thumb_count=103,ARM_count=6159,
        API_entries=calls,static_memory_sites=dict(read=sorted(READ_SITES),write=sorted(WRITE_SITES)))
    return result


def observation_policy(predicted):
    return dict(code_starts=frozenset((x['pc'],bool(x['regs'][15]&32))for x in predicted['flow']),
        read_sites=frozenset((x['pc'],x['address'],x['bytes'])for x in predicted['reads']),
        write_sites=frozenset((x['pc'],x['address'],x['bytes'])for x in predicted['stores']))


def run(f,policy,observe=True):
    import unicorn as U
    from unicorn import arm_const as C
    need(type(observe)is bool and U.__version__==BACKEND['unicorn'],'qualified observer/backend')
    uc=U.Uc(U.UC_ARCH_ARM,U.UC_MODE_ARM);uc.ctl_set_cpu_model(C.UC_CPU_ARM_CORTEX_A15)
    need(uc.ctl_get_cpu_model()==17,'actual CPU17')
    registers=tuple(getattr(C,'UC_ARM_REG_R'+str(i))for i in range(13))+(C.UC_ARM_REG_SP,C.UC_ARM_REG_LR,C.UC_ARM_REG_CPSR)
    for a,b in f['pages'].items():uc.mem_map(a,4096);uc.mem_write(a,b)
    uc.reg_write(C.UC_ARM_REG_CPSR,f['entry_regs'][15])
    for r,v in zip(registers[:15],f['entry_regs'][:15]):uc.reg_write(r,v)
    code={pc:(4,False)for a,n in CODE_SPANS for pc in range(a,a+n,4)}
    thumb=L.thumb_code({name:M.read(f['pages'],a,n)for name,(a,n,count,digest)in L.THUMB.items()})
    code.update({a:(len(b),True)for a,b in thumb.items()})
    flow=[];reads=[];stores=[];seen=set();count=0;tc=0;callbacks=0;rc=0;wc=0;low=R.TOP;stopped=False
    def state():return [uc.reg_read(r)&0xffffffff for r in registers]
    def instruction(machine,address,size,user):
        nonlocal count,tc,callbacks,low,stopped
        callbacks+=1
        if address==F.RETURN:stopped=True;machine.emu_stop();return
        isa=bool(machine.reg_read(C.UC_ARM_REG_CPSR)&32)
        need(code.get(address)==(size,isa)and(address,isa)in policy['code_starts'],'native fetch start/width/ISA outside source route')
        need(bytes(machine.mem_read(address,size))==M.read(f['pages'],address,size),'native code bytes drift')
        count+=1;tc+=int(isa);need(count<=8192,'native instruction cap');seen.add(address);low=min(low,machine.reg_read(C.UC_ARM_REG_SP))
        if observe:flow.append(dict(pc=address,regs=state()))
    def access(machine,kind,address,size,value,user):
        nonlocal rc,wc
        pc=machine.reg_read(C.UC_ARM_REG_PC)
        if kind==U.UC_MEM_WRITE:
            need((pc,address,size)in policy['write_sites'],'native write outside source site/address/width');wc+=1
            if observe:stores.append(dict(pc=pc,address=address,bytes=size,before=bytes(machine.mem_read(address,size)).hex(),value=value&((1<<(8*size))-1)))
        else:
            need((pc,address,size)in policy['read_sites'],'native read outside source site/address/width');rc+=1
            if observe:reads.append(dict(pc=pc,address=address,bytes=size,hex=bytes(machine.mem_read(address,size)).hex()))
    uc.hook_add(U.UC_HOOK_CODE,instruction);uc.hook_add(U.UC_HOOK_MEM_READ|U.UC_HOOK_MEM_WRITE,access)
    fault=None
    try:uc.emu_start(F.ENTRY|1,0,timeout=1000000,count=8192)
    except(ValueError,U.UcError)as e:fault=type(e).__name__+': '+str(e)
    pages={a:bytes(uc.mem_read(a,4096))for a in f['pages']}
    return dict(schema='native-fs-memory-narc-raw-v1',observed=observe,initial=F.input_record(f),fault=fault,stopped=stopped,
        stop_pc=uc.reg_read(C.UC_ARM_REG_PC),returned=state(),flow=flow,reads=reads,stores=stores,
        executed_count=count,ARM_count=count-tc,Thumb_count=tc,unique_executed_starts=len(seen),callback_count=callbacks,
        read_count=rc,store_count=wc,stack_peak=R.TOP-low,models=[],runtime_host_writes=[],backend=BACKEND,
        final_map_sha256=M.map_digest(pages),final_pages=[dict(ram=a,hex=b.hex())for a,b in sorted(pages.items())])


def require_run(f,raw):
    predicted=predict(f)
    need(raw.get('schema')=='native-fs-memory-narc-raw-v1','native raw schema')
    keys=('executed_count','ARM_count','Thumb_count','unique_executed_starts','callback_count','read_count','store_count','stack_peak','stop_pc')
    need(all(type(raw[k])is int for k in keys),'typed native counters/PC')
    need(wire(raw['initial'])==wire(F.input_record(f)),'complete frozen native NARC input')
    need(wire(raw['backend'])==wire(BACKEND),'qualified backend')
    need(raw['fault']is None and raw['stopped']is True and raw['stop_pc']==F.RETURN,'original native Thumb return')
    need(raw['models']==raw['runtime_host_writes']==[],'zero service model/runtime host write')
    need(tuple(raw[k]for k in keys[:-1])==(6262,6159,103,len({x['pc']for x in predicted['flow']}),6263,1732,1299,616),'source counters')
    need(wire(raw['returned'])==wire(predicted['returned']),'source full16 native return ABI')
    need(raw['final_map_sha256']==M.map_digest(predicted['pages']),'source final map hash')
    need(wire(raw['final_pages'])==wire([dict(ram=a,hex=b.hex())for a,b in sorted(predicted['pages'].items())]),'source all final pages')
    if raw['observed']is True:
        for k in('flow','reads','stores'):need(wire(raw[k])==wire(predicted[k]),'source native '+k)
    else:need(raw['observed']is False and raw['flow']==raw['reads']==raw['stores']==[],'OFF no observation projections')
    return predicted
