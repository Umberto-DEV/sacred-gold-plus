"""Source-first LLVM caller forecast, native callees and per-build observations.

The retained native Reset benchmark is a source of qualified math and checks,
not a producer for this candidate. No guest phase resets or host callees exist.
"""
from pathlib import Path
import importlib.util
import struct
import types
from collections import Counter


def load(path,name):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


F=load(Path(__file__).parents[1]/'tools/congela_reset_c.py','LLVM_Reset_frozen')
P=load(Path(__file__).with_name('mon_reset_bench.py'),'LLVM_Reset_retained_native_checks')
L=F;R,M,need,wire=F.R,F.M,F.need,F.M.wire
A,C,BOX,MON=P.A,P.C,P.BOX,P.MON
CODE_SPANS=F.CODE_SPANS;BACKEND=P.BACKEND
source_stages,crypt,replay_prefix,main_view=P.source_stages,P.crypt,P.replay_prefix,P.main_view
contextual_mon_checks=types.FunctionType(P.contextual_mon_checks.__code__,{**P.contextual_mon_checks.__globals__,'F':F})


def source_identity_guard():P.source_identity_guard()


BOX_GUARDS=[]
for read,write in BOX.BOX_GUARDS:
    old=read.__globals__['F'];value=old.VALUE
    fixture=types.SimpleNamespace(BOX=F.BOX,VALUE=None if value is None else value-32)
    BOX_GUARDS.append((types.FunctionType(read.__code__,{**read.__globals__,'R':types.SimpleNamespace(TOP=R.TOP-64),'F':fixture}),
        types.FunctionType(write.__code__,{**write.__globals__,'R':types.SimpleNamespace(TOP=R.TOP-64),'F':fixture})))
BOX_F=types.SimpleNamespace(**{**vars(BOX.F),'MOVE_VALUE':F.MOVE_VALUE,'PP_VALUE':F.PP_VALUE,
    'FILE':F.FILE1,'LOCAL':F.LOCAL1,'DEST':F.DEST1})
BOX_R=types.SimpleNamespace(**{**vars(R),'TOP':F.CHILD_TOP})
box_read=types.FunctionType(BOX.read_owner.__code__,{**BOX.read_owner.__globals__,'R':BOX_R,'F':BOX_F,'BOX_GUARDS':BOX_GUARDS})
box_write=types.FunctionType(BOX.write_owner.__code__,{**BOX.write_owner.__globals__,'R':BOX_R,'F':BOX_F,'BOX_GUARDS':BOX_GUARDS})
MON_F=types.SimpleNamespace(BOX=F.BOX,VALUE=F.ZERO_VALUE)
mon_read=types.FunctionType(MON.read_owner.__code__,{**MON.read_owner.__globals__,'R':types.SimpleNamespace(TOP=F.CHILD_TOP),'F':MON_F})
mon_write=types.FunctionType(MON.write_owner.__code__,{**MON.write_owner.__globals__,'R':types.SimpleNamespace(TOP=F.CHILD_TOP),'F':MON_F})


def read_owner(pc,a,n):
    if 0x20714b0<=pc<0x20714e8:return False
    if P.overlaps(a,n,F.CHILD_TOP,32):
        return(n==4 and pc==F.BASE+74 and a in range(F.CHILD_TOP,R.TOP,4)or
               n==1 and(pc,a)in((0x206f106,F.ZERO_VALUE),(0x206f0f6,F.RESET_PP_VALUE)))
    if F.BASE<=pc<F.BASE+24:return n==4 and(pc,a)in tuple((F.BASE+i,F.BASE+i+4)for i in(0,8,16))
    if pc==0x2073390:return n==1 and a in(F.DEST1+6,F.DEST2+6)
    if n==4 and pc==0x206f0f4 and a==F.CHILD_TOP-124:return True
    if n==4 and pc==0x206f102 and a in range(F.CHILD_TOP-48,F.CHILD_TOP-24,4):return True
    return box_read(pc,a,n)or mon_read(pc,a,n)or n==4 and pc==0x20714e8 and a==0x20714ec


def write_owner(pc,a,n):
    if 0x20714b0<=pc<0x20714e8:return False
    if P.overlaps(a,n,F.CHILD_TOP,32):
        return n==4 and(pc==F.ENTRY and a in range(F.CHILD_TOP,R.TOP,4)or
            (pc,a)in((F.BASE+38,F.ZERO_VALUE),(F.BASE+60,F.RESET_PP_VALUE)))
    if n==4 and pc==0x206f0fa and a==F.CHILD_TOP-124:return True
    return box_write(pc,a,n)or mon_write(pc,a,n)


require_memory_delta=types.FunctionType(BOX.require_memory_delta.__code__,{**BOX.require_memory_delta.__globals__,
    'write_owner':write_owner,'M':M},argdefs=BOX.require_memory_delta.__defaults__)


def causal_checks(f,result):
    ups=f['input_Up'];stages,plains,keys,party=source_stages(ups)
    flow,reads,stores=(result[k]for k in('flow','reads','stores'))
    def at(pc):return[x for x in flow if x['pc']==pc]
    # Indexes are fixed before candidate CPU and count the real extra thunk
    # literal reads and eight-word root PUSH, not a normalized native trace.
    child,view=main_view(f,result,0x20714f0,F.BASE+36,2,3806,8,2245)
    child_f=types.SimpleNamespace(**{**vars(BOX_F),'RETURN':F.BASE+36})
    child_delta=types.FunctionType(BOX.require_memory_delta.__code__,{**BOX.require_memory_delta.__globals__,'write_owner':box_write,'M':M},argdefs=BOX.require_memory_delta.__defaults__)
    check_box=types.FunctionType(BOX.causal_checks.__code__,{**BOX.causal_checks.__globals__,'R':BOX_R,'F':child_f,'require_memory_delta':child_delta})
    box_proof=check_box(child,view)
    need(len(view['flow'])==(17198 if ups==3 else 17169)and view['native_peak']==688,'compiled first Box complete path')
    need(child['entry_regs'][7]==f['entry_regs'][7]and child['entry_regs'][15]==0x2000003f,'C first Box precedes MOVS r7 zero and preserves carry')
    mon62_entry,mon62=main_view(f,result,0x206ec40,F.BASE+52,3809,1128,2254,534)
    mon62_proof=contextual_mon_checks(mon62_entry,mon62,stages[1],stages[2],plains[1],plains[2],party,62,0,F.ZERO_VALUE)
    mon58_entry,mon58=main_view(f,result,0x206ec40,F.BASE+74,6680,1128,4094,534)
    mon58_proof=contextual_mon_checks(mon58_entry,mon58,stages[2],stages[3],plains[2],plains[3],party,58,15,F.RESET_PP_VALUE)
    need([x for x in stores if x['pc']==F.BASE+38]==[dict(pc=F.BASE+38,address=F.ZERO_VALUE,bytes=4,before='00000000',value=0)],'compiled zero word writer including idempotent preimage')
    need([x for x in stores if x['pc']==F.BASE+60]==[dict(pc=F.BASE+60,address=F.RESET_PP_VALUE,bytes=4,
         before=struct.pack('<I',f['entry_regs'][3]).hex(),value=15)],'compiled PP word overwrites saved r3 cookie')
    need([x['regs'][7]for pc in(0x206ec40,)for x in at(pc)]==[0,0],'C r7 zero survives two Mon calls')
    need([x['regs'][:2]for x in at(0x207332c)]==[[310,ups],[310,0]],'two native MaxPP argument pairs')
    need(at(0x207332c)[1]['regs'][3]==0x207332d and at(0x207332c)[1]['regs'][15]==0x6000003f,'second MaxPP actual thunk r3 and C flags')
    need([(x['pc'],x['address'],x['hex'])for x in reads if x['pc']in(0x206f106,0x206f0f6)]==[
        (0x206f0f6,F.PP_VALUE,bytes([15+3*ups]).hex()),(0x206f106,F.ZERO_VALUE,'00'),(0x206f0f6,F.RESET_PP_VALUE,'0f')],'three native Value consumers with distinct lifetimes')
    need([(x['address'],x['before'],x['value'])for x in stores if x['pc']==0x206f0fe]==[(F.BOX+80,'0f',15+3*ups),(F.BOX+80,bytes([15+3*ups]).hex(),15)],'two same-PC PP writers')
    need([x['regs'][13]for x in at(0x206f0fe)]==[R.TOP-184,R.TOP-160],'two PP writer stack depths')
    need([x['regs'][:2]for x in at(BOX.A.BASE.DIV_ENTRY)]==[[15*20*ups,100],[0,100]],'actual DIV inputs')
    need([x['regs'][:2]for x in at(BOX.A.BASE.DIV_RETURN)]==[[3*ups,0],[0,0]],'actual DIV results')
    need([x for x in reads if x['pc']==0x2073390]==[dict(pc=0x2073390,address=d+6,bytes=1,hex='0f')for d in(F.DEST1,F.DEST2)],'two native PP15 buffer reads')
    counts=Counter(x['pc']for x in flow);sdk=F.OLD.P.P.SDK
    expected_entries=dict(open=1,fast=1,init=2,convert=1,find=1,send=10,execute=10,release=10,wakeup=10,next=10,disable=57,restore=57,
        fast_command=1,direct_command=1,findpath=1,translate=21,seekdir=4,read_dir=6,read_table=21,read_memory=21,copy=28,strnicmp=6,
        read_wrapper=7,read_core=7,wait=7,seek=5,close=1,read_command=7,read_callback=7,close_command=1)
    need({name:counts[item[0]]for name,item in sdk.COMPONENTS.items()if name!='default_table'}=={k:2*v for k,v in expected_entries.items()},'two complete SDK callgraphs')
    need(sum(n for pc,n in counts.items()if any(a<=pc<a+size for a,size in L.SDK_CODE_SPANS))==12318,'two complete SDK6159 bodies')
    callbacks=[]
    for local,dest in((F.LOCAL1,F.DEST1),(F.LOCAL2,F.DEST2)):
        destinations=(local+20,local+20,local+8,local+20,local+16,local+12,dest)
        callbacks.extend([R.ARC,d,0x1093800+offset,n]for d,(offset,n)in zip(destinations,F.OLD.P.P.NARC.WINDOWS))
    need([x['regs'][:4]for x in at(0x20d7448)]==callbacks,'fourteen real native memory callbacks')
    for file,dest,boundary_pc in((F.FILE1,F.DEST1,0x207151c),(F.FILE2,F.DEST2,F.BASE+60)):
        boundary=next(i for i,x in enumerate(stores)if x['pc']==boundary_pc);memory=replay_prefix(f['pages'],stores[:boundary])
        final_file=M.read(memory,file,72)
        need(all(R.u32(final_file,a)==v for a,v in((8,0),(12,0),(16,14),(20,0),(32,140),(36,0x1093800),(40,0x109645c),(44,0x1095a5c),(48,dest),(52,16),(56,16))),'closed native FILE before reuse')
        need(M.read(memory,dest,16)==M.read(f['pages'],sdk.MEMBER_SOURCE,16)
             and M.read(memory,R.ARC,92)==M.read(f['pages'],R.ARC,92),'real PP buffer and archive restored before reuse')
    second_sdk=next(i for i,x in enumerate(stores)if i>=2788 and any(a<=x['pc']<a+n for a,n in L.SDK_CODE_SPANS))
    before_init=replay_prefix(f['pages'],stores[:second_sdk])
    expected_file=[F.BOX,0,F.ZERO_VALUE,F.BOX+72,F.ZERO_VALUE,0x206ee27,F.BOX,0,F.BOX+40,
        0xa5a5a5a5,0,44,ups,310,f['entry_regs'][7],0x200751b,0x201ff45,58]
    need(M.read(before_init,F.FILE2,72)==struct.pack('<18I',*expected_file),'compiled second FILE preInit native prior-frame residues')
    need(sum(x['pc']==0x201ff84 for x in stores)==sum(x['pc']==0x201ff5e for x in stores)==840
         and sum(x['pc']==0x20725f2 for x in reads)==576,'whole transaction840 seed/payload and576checksum events')
    need([x['regs'][:3]for x in at(0x2072608)]==[[F.BOX,0x4000,i]for unused in range(5)for i in range(4)],'twenty native PID selectors')
    return dict(Box=box_proof,Mon62=mon62_proof,Mon58=mon58_proof,intermediate_keys=keys,
        second_FILE_preInit_sha256=R.sha(struct.pack('<18I',*expected_file)),native_calls=4,project_envelope_instructions=30,retained_Mon_veneer_instructions=2)


def predict(f):
    source_identity_guard();ups=f['input_Up'];parts=f['resource_parts']
    need(f==F.make_input(parts,ups),'complete canonical compiled C input/pages')
    need(R.sha(M.read(f['pages'],R.FAT,4104))==R.FAT_SHA and R.sha(M.read(f['pages'],R.FNT,2902))==R.FNT_SHA,'compiled C exact cached tables')
    need(R.sha(M.read(f['pages'],F.OLD.P.P.ROOT,12))==F.OLD.P.P.SDK.L.L.ROOT_SHA,'compiled C exact FS root')
    BOX.MAX.division_static(f['pages'])
    result=A.run(f,L.SDK_CODE_SPANS,F.RETURN,thumb_code=L.thumb_code(parts),read_guard=read_owner,write_guard=write_owner)
    count=35205 if ups==3 else 35176;arm=12381 if ups==3 else 12352
    need((len(result['flow']),len(result['reads']),len(result['stores']),result['native_peak'])==(count,7816,4628,720),'manual compiled C count/access/stack forecast')
    need(sum(not bool(x['regs'][15]&32)for x in result['flow'])==arm and count-arm==22824,'compiled C source ARM/Thumb counts')
    need(not any(0x20714b0<=x['pc']<0x20714e8 for x in result['flow']),'original Reset never fetched')
    expected=list(f['entry_regs']);expected[:4]=[0x2b9b,310,0,15];expected[12]=0;expected[14]=0x201ff59;expected[15]=0x6000003f
    need(result['returned']==expected,'compiled C own full16 return including volatile POP slots')
    final=F.OLD.MON.owned_mon(0)[0];need(M.read(result['pages'],F.BOX,236)==final,'compiled C complete Mon236 output')
    for a,n in((F.BOX-16,16),(F.BOX+236,16),(R.TOP-F.STACK-F.GUARD,F.GUARD),(R.ARC,92)):
        need(M.read(result['pages'],a,n)==M.read(f['pages'],a,n),'compiled C guards/archive unchanged')
    require_memory_delta(f['pages'],result['pages'],result['stores'])
    result.update(ARM_count=arm,Thumb_count=22824,output_Mon_sha256=R.sha(final),causal=causal_checks(f,result))
    return result


observation_policy=C.P.observation_policy


def run(f,policy,observe=True):
    source_identity_guard();raw=C.bind(fixture=F,reader=L,memory=M,stack_top=R.TOP,code_spans=CODE_SPANS)(f,policy,observe)
    raw['schema']='compiled-Reset-C-raw-v1';return raw


def require_run(f,raw,predicted=None):
    p=predict(f)if predicted is None else predicted
    need(raw.get('schema')=='compiled-Reset-C-raw-v1','compiled C raw schema')
    keys=('executed_count','ARM_count','Thumb_count','unique_executed_starts','callback_count','read_count','store_count','stack_peak','stop_pc')
    need(all(type(raw.get(k))is int for k in keys),'typed compiled C counts/PC')
    need(wire(raw['initial'])==wire(F.input_record(f))and wire(raw['backend'])==wire(BACKEND),'compiled C input/backend binding')
    need(raw['fault']is None and raw['stop_pc']==F.RETURN and raw['models']==raw['runtime_host_writes']==[],'compiled C return with zero host model/write')
    C.require_completion(raw,len(p['flow']))
    need(tuple(raw[k]for k in keys[:-1])==(len(p['flow']),p['ARM_count'],22824,len({x['pc']for x in p['flow']}),len(p['flow'])+1,7816,4628,720),'compiled C all counters')
    need(wire(raw['returned'])==wire(p['returned']),'compiled C full16 return')
    need(raw['final_map_sha256']==M.map_digest(p['pages'])and wire(raw['final_pages'])==wire([dict(ram=a,hex=b.hex())for a,b in sorted(p['pages'].items())]),'compiled C all final pages/hash')
    if raw['observed']is True:
        for key in('flow','reads','stores'):need(wire(raw[key])==wire(p[key]),'compiled C complete native '+key)
    else:need(raw['observed']is False and raw['flow']==raw['reads']==raw['stores']==[],'compiled C OFF no trace projections')
    return p
