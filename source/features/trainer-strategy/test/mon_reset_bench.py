"""Whole Reset source forecast and phase-specific owners, no phase bridge."""
from pathlib import Path
import importlib.util
import struct
import types
from collections import Counter


def load(path,name):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


F=load(Path(__file__).parents[1]/'tools/congela_mon_reset.py','whole_Reset_frozen')
BOX=load(Path(__file__).with_name('box_move_caller_bench.py'),'Reset_retained_Box_semantics')
MON=load(Path(__file__).with_name('mon_ppup_setter_bench.py'),'Reset_retained_Mon_owners')
A=load(Path(__file__).with_name('arm_thumb_mon_reset_oracle.py'),'whole_Reset_arithmetic')
C=load(Path(__file__).with_name('mon_reset_cpu.py'),'whole_Reset_CPU')
L,R,M,need,wire=F.L,F.R,F.M,F.need,F.M.wire
BACKEND=BOX.BACKEND
CODE_SPANS=L.CODE_SPANS
crypt=BOX.crypt


def source_identity_guard():
    BOX.source_identity_guard();MON.source_identity_guard();A.source_identity_guard();C.source_identity_guard()


BOX_GUARDS=[]
for read,write in BOX.BOX_GUARDS:
    old=read.__globals__['F'];value=old.VALUE
    fixture=types.SimpleNamespace(BOX=F.BOX,VALUE=None if value is None else value-24)
    for_reader={**read.__globals__,'R':types.SimpleNamespace(TOP=R.TOP-56),'F':fixture}
    for_writer={**write.__globals__,'R':types.SimpleNamespace(TOP=R.TOP-56),'F':fixture}
    BOX_GUARDS.append((types.FunctionType(read.__code__,for_reader),types.FunctionType(write.__code__,for_writer)))
BOX_F=types.SimpleNamespace(**{**vars(BOX.F),'MOVE_VALUE':F.MOVE_VALUE,'PP_VALUE':F.PP_VALUE,
    'FILE':F.FILE1,'LOCAL':F.LOCAL1,'DEST':F.DEST1})
BOX_R=types.SimpleNamespace(**{**vars(R),'TOP':F.CHILD_TOP})
box_read=types.FunctionType(BOX.read_owner.__code__,{**BOX.read_owner.__globals__,'R':BOX_R,'F':BOX_F,'BOX_GUARDS':BOX_GUARDS})
box_write=types.FunctionType(BOX.write_owner.__code__,{**BOX.write_owner.__globals__,'R':BOX_R,'F':BOX_F,'BOX_GUARDS':BOX_GUARDS})
MON_F=types.SimpleNamespace(BOX=F.BOX,VALUE=F.ZERO_VALUE)
mon_read=types.FunctionType(MON.read_owner.__code__,{**MON.read_owner.__globals__,'R':types.SimpleNamespace(TOP=F.CHILD_TOP),'F':MON_F})
mon_write=types.FunctionType(MON.write_owner.__code__,{**MON.write_owner.__globals__,'R':types.SimpleNamespace(TOP=F.CHILD_TOP),'F':MON_F})


def overlaps(a,n,b,size):return a<b+size and b<a+n


def read_owner(pc,a,n):
    # A legacy MAX fallback retains its old TOP. Explicitly protect the live
    # Reset frame before delegating to any child; only these native sites own it.
    if overlaps(a,n,F.CHILD_TOP,24):
        return(n==4 and pc==0x20714e6 and a in range(R.TOP-16,R.TOP,4)or
               n==1 and(pc,a)in((0x206f106,F.ZERO_VALUE),(0x206f0f6,F.RESET_PP_VALUE)))
    if pc==0x2073390:return n==1 and a in(F.DEST1+6,F.DEST2+6)
    if n==4 and pc==0x206f0f4 and a==F.CHILD_TOP-124:return True
    if n==4 and pc==0x206f102 and a in range(F.CHILD_TOP-48,F.CHILD_TOP-24,4):return True
    return box_read(pc,a,n)or mon_read(pc,a,n)or n==4 and pc==0x20714e8 and a==0x20714ec


def write_owner(pc,a,n):
    if overlaps(a,n,F.CHILD_TOP,24):
        return n==4 and(pc==0x20714b0 and a in range(R.TOP-16,R.TOP,4)or
                         (pc,a)in((0x20714c2,F.ZERO_VALUE),(0x20714d8,F.RESET_PP_VALUE)))
    if n==4 and pc==0x206f0fa and a==F.CHILD_TOP-124:return True
    return box_write(pc,a,n)or mon_write(pc,a,n)


require_memory_delta=types.FunctionType(BOX.require_memory_delta.__code__,{**BOX.require_memory_delta.__globals__,
    'write_owner':write_owner,'M':M},argdefs=BOX.require_memory_delta.__defaults__)


def source_stages(ups):
    initial,plain,party=F.MON.owned_mon(ups)
    plains=[plain];stages=[initial];keys=[0x2a8+ups]
    for offset,value in((72,15+15*20*ups//100),(76,0),(72,15)):
        changed=bytearray(plains[-1]);changed[offset]=value;changed=bytes(changed)
        key=sum(x[0]for x in struct.iter_unpack('<H',changed))&65535
        cipher,seeds=crypt(changed,key);keys.append(key);plains.append(changed)
        stages.append(initial[:6]+struct.pack('<H',key)+cipher+initial[136:])
    need(keys==([0x2ab,0x2b4,0x2b1,0x2a8]if ups==3 else[0x2a8]*4),'independent Reset intermediate keys')
    if ups==3:
        need(R.sha(stages[2][:136])=='e4658ab3939f77d4ab5fcd78735710a20b6fc043ce60c4ccbab4f7fa5344bf63','independent PP24/Up0 intermediate Box hash')
    need(stages[-1]==F.MON.owned_mon(0)[0],'independent Reset final Mon')
    return stages,plains,keys,party


def replay_prefix(pages,stores):
    memory={a:bytearray(b)for a,b in pages.items()}
    for x in stores:
        need(M.read(memory,x['address'],x['bytes']).hex()==x['before'],'source-view prefix preimage')
        M.put(memory,x['address'],x['value'].to_bytes(x['bytes'],'little'))
    return {a:bytes(b)for a,b in memory.items()}


def main_view(f,result,start_pc,end_pc,read_start,read_count,store_start,store_count):
    starts=[i for i,x in enumerate(result['flow'])if x['pc']==start_pc]
    # Mon62/58 share the API entry; the next selected return chooses its own
    # source interval. These views never execute a child or repair CPU memory.
    end=next(i for i,x in enumerate(result['flow'])if x['pc']==end_pc)
    start=max(i for i in starts if i<end)
    memory=replay_prefix(f['pages'],result['stores'][:store_start])
    final=replay_prefix(memory,result['stores'][store_start:store_start+store_count])
    entry=dict(f,entry_pc=start_pc,entry_regs=result['flow'][start]['regs'],pages=memory)
    flow=result['flow'][start:end]
    view=dict(flow=flow,reads=result['reads'][read_start:read_start+read_count],stores=result['stores'][store_start:store_start+store_count],
        returned=result['flow'][end]['regs'],stop_pc=end_pc,pages=final,
        native_peak=entry['entry_regs'][13]-min(x['regs'][13]for x in flow))
    return entry,view


def contextual_mon_checks(entry,view,before,after,old_plain,new_plain,party,attr,value,value_address):
    need((len(view['flow']),len(view['reads']),len(view['stores']),view['native_peak'])==(5827,1128,534,144),'contextual Mon complete source counts')
    need(entry['entry_regs'][:3]==[F.BOX,attr,value_address]and entry['entry_regs'][13]==F.CHILD_TOP,'contextual Mon actual entry ABI')
    need(M.read(entry['pages'],F.BOX,236)==before and M.read(view['pages'],F.BOX,236)==after,'contextual Mon before/after236')
    oldkey=int.from_bytes(before[6:8],'little');newkey=int.from_bytes(after[6:8],'little')
    phases=((F.BOX+136,before[136:],party,0x4000),(F.BOX+8,before[8:136],old_plain,oldkey),
            (F.BOX+136,party,after[136:],0x4000),(F.BOX+8,new_plain,after[8:136],newkey))
    payload=[];seed_updates=[]
    for address,pre,post,key in phases:
        calculated,seeds=crypt(pre,key);need(calculated==post,'contextual Mon independent cipher phase')
        payload.extend((address+i,2,pre[i:i+2].hex(),int.from_bytes(post[i:i+2],'little'))for i in range(0,len(pre),2))
        seed_updates.extend((F.CHILD_TOP-24,4,before_seed,after_seed)for before_seed,after_seed in zip([key]+seeds[:-1],seeds))
    need([(x['address'],x['bytes'],x['before'],x['value'])for x in view['stores']if x['pc']==0x201ff5e]==payload,'contextual Mon four payload phases/preimages')
    need([(x['address'],x['bytes'],int.from_bytes(bytes.fromhex(x['before']),'little'),x['value'])for x in view['stores']if x['pc']==0x201ff84]==seed_updates,'contextual Mon four native seed phases')
    need([(x['address'],x['hex'])for x in view['reads']if x['pc']==0x20725f2]==[(F.BOX+8+i,data[i:i+2].hex())for data in(old_plain,new_plain)for i in range(0,128,2)],'contextual Mon both checksum plaintext reads')
    read_pc,write_pc,offset=(0x206f106,0x206f10e,84)if attr==62 else(0x206f0f6,0x206f0fe,80)
    need([x for x in view['reads']if x['pc']==read_pc]==[dict(pc=read_pc,address=value_address,bytes=1,hex=bytes([value]).hex())],'contextual Mon actual guest Value low byte')
    need([x for x in view['stores']if x['pc']==write_pc]==[dict(pc=write_pc,address=F.BOX+offset,bytes=1,before=bytes([old_plain[offset-8]]).hex(),value=value)],'contextual Mon exact field writer')
    field=next(x['regs']for x in view['flow']if x['pc']==write_pc)
    need(field[:3]==[F.BOX+72,value,3]and field[4:8]==[value_address,F.BOX+72,F.BOX+104,F.BOX+8]and field[13:]==[F.CHILD_TOP-128,0x206ee27,0x3f],'contextual Mon leaf Value/SP/LR/flags')
    need([x for x in view['stores']if x['pc']==0x206ecbe]==[dict(pc=0x206ecbe,address=F.BOX+6,bytes=2,before=struct.pack('<H',oldkey).hex(),value=newkey)],'contextual Mon header key writer')
    need([x['hex']for x in view['reads']if x['pc']==0x206ecc2]==[struct.pack('<H',newkey).hex()],'contextual Mon new header reload')
    need(M.read(entry['pages'],F.ZERO_VALUE,8)==M.read(view['pages'],F.ZERO_VALUE,8),'contextual Mon preserves both live Reset words')
    _,seeds=crypt(new_plain,newkey);expected=list(entry['entry_regs'])
    expected[:4]=[seeds[-1]>>16,0,seeds[-2],0x206eccd];expected[14]=0x201ff59;expected[15]=0x6000003f
    need(view['returned']==expected,'contextual Mon full16 void return')
    return dict(attribute=attr,old_key=oldkey,new_key=newkey,value_address=value_address,output_Mon_sha256=R.sha(after))


def causal_checks(f,result):
    ups=f['input_Up'];stages,plains,keys,party=source_stages(ups)
    flow,reads,stores=(result[k]for k in('flow','reads','stores'))
    def at(pc):return[x for x in flow if x['pc']==pc]
    need([x['regs'][:3]for x in at(0x20714e8)]==[[F.BOX,310,0]],'Reset actual first veneer entry')
    child,view=main_view(f,result,0x20714f0,0x20714be,1,3806,4,2245)
    child_f=types.SimpleNamespace(**{**vars(BOX_F),'RETURN':0x20714be})
    child_delta=types.FunctionType(BOX.require_memory_delta.__code__,{**BOX.require_memory_delta.__globals__,'write_owner':box_write,'M':M},argdefs=BOX.require_memory_delta.__defaults__)
    check_box=types.FunctionType(BOX.causal_checks.__code__,{**BOX.causal_checks.__globals__,'R':BOX_R,'F':child_f,'require_memory_delta':child_delta})
    box_proof=check_box(child,view)
    need(len(view['flow'])==(17198 if ups==3 else 17169)and view['native_peak']==688,'contextual first Box complete source counts')
    mon62_entry,mon62=main_view(f,result,0x206ec40,0x20714ce,3807,1128,2250,534)
    mon62_proof=contextual_mon_checks(mon62_entry,mon62,stages[1],stages[2],plains[1],plains[2],party,62,0,F.ZERO_VALUE)
    mon58_entry,mon58=main_view(f,result,0x206ec40,0x20714e4,6676,1128,4090,534)
    mon58_proof=contextual_mon_checks(mon58_entry,mon58,stages[2],stages[3],plains[2],plains[3],party,58,15,F.RESET_PP_VALUE)
    need([x for x in stores if x['pc']==0x20714c2]==[dict(pc=0x20714c2,address=F.ZERO_VALUE,bytes=4,before='a5a5a5a5',value=0)],'native Reset zero word publication')
    need([x for x in stores if x['pc']==0x20714d8]==[dict(pc=0x20714d8,address=F.RESET_PP_VALUE,bytes=4,before='a5a5a5a5',value=15)],'native Reset PP word publication')
    need([(x['pc'],x['address'],x['hex'])for x in reads if x['pc']in(0x206f106,0x206f0f6)]==[
        (0x206f0f6,F.PP_VALUE,bytes([15+3*ups]).hex()),(0x206f106,F.ZERO_VALUE,'00'),(0x206f0f6,F.RESET_PP_VALUE,'0f')],'three distinct PP/PP-Up Value contexts')
    need([(x['address'],x['before'],x['value'])for x in stores if x['pc']==0x206f0fe]==[(F.BOX+80,'0f',15+3*ups),(F.BOX+80,bytes([15+3*ups]).hex(),15)],'two same-PC PP field stores in order')
    need([x['regs'][13]for x in at(0x206f0fe)]==[R.TOP-176,R.TOP-152],'two same-PC PP field stack depths')
    need([x['regs'][:2]for x in at(BOX.A.BASE.DIV_ENTRY)]==[[15*20*ups,100],[0,100]],'two actual native DIV input pairs')
    need([x['regs'][:2]for x in at(BOX.A.BASE.DIV_RETURN)]==[[3*ups,0],[0,0]],'two actual native DIV quotient/remainder pairs')
    need([x for x in reads if x['pc']==0x2073390]==[dict(pc=0x2073390,address=dest+6,bytes=1,hex='0f')for dest in(F.DEST1,F.DEST2)],'two real PP15 native buffer reads')
    need(at(0x20714d2)[0]['regs'][:2]==[310,0]and at(0x20714d2)[0]['regs'][15]==0x4000003f,'Reset native MOVS0 reaches second MaxPP')
    counts=Counter(x['pc']for x in flow);sdk=F.P.P.SDK
    expected_entries=dict(open=1,fast=1,init=2,convert=1,find=1,send=10,execute=10,release=10,wakeup=10,next=10,disable=57,restore=57,
        fast_command=1,direct_command=1,findpath=1,translate=21,seekdir=4,read_dir=6,read_table=21,read_memory=21,copy=28,strnicmp=6,
        read_wrapper=7,read_core=7,wait=7,seek=5,close=1,read_command=7,read_callback=7,close_command=1)
    need({name:counts[item[0]]for name,item in sdk.COMPONENTS.items()if name!='default_table'}=={k:2*v for k,v in expected_entries.items()},'two complete native SDK callgraphs')
    sdk_steps=sum(n for pc,n in counts.items()if any(a<=pc<a+size for a,size in L.SDK_CODE_SPANS))
    need(sdk_steps==12318,'two native SDK6159 bodies')
    callbacks=[]
    for local,dest in((F.LOCAL1,F.DEST1),(F.LOCAL2,F.DEST2)):
        destinations=(local+20,local+20,local+8,local+20,local+16,local+12,dest)
        callbacks.extend([R.ARC,d,0x1093800+offset,n]for d,(offset,n)in zip(destinations,F.P.P.NARC.WINDOWS))
    need([x['regs'][:4]for x in at(0x20d7448)]==callbacks,'fourteen actual memory read callbacks')
    for file,dest,boundary_pc in((F.FILE1,F.DEST1,0x207151c),(F.FILE2,F.DEST2,0x20714d8)):
        boundary=next(i for i,x in enumerate(stores)if x['pc']==boundary_pc);memory=replay_prefix(f['pages'],stores[:boundary])
        final_file=M.read(memory,file,72)
        need(all(R.u32(final_file,a)==v for a,v in((8,0),(12,0),(16,14),(20,0),(32,140),(36,0x1093800),(40,0x109645c),(44,0x1095a5c),(48,dest),(52,16),(56,16))),'contextual native closed FILE before reuse')
        need(M.read(memory,dest,16)==M.read(f['pages'],sdk.MEMBER_SOURCE,16)and M.read(memory,R.ARC,92)==M.read(f['pages'],R.ARC,92),'contextual NARC buffer/archive completion before reuse')
    second_sdk=next(i for i,x in enumerate(stores)if i>=2784 and any(a<=x['pc']<a+n for a,n in L.SDK_CODE_SPANS))
    before_init=replay_prefix(f['pages'],stores[:second_sdk])
    # Unwritten Mon locals retain the first NARC's six saved registers;
    # two deeper words retain the last Box PP cipher frame. They are not A5.
    expected_file=[F.BOX,0,F.ZERO_VALUE,F.BOX+72,F.ZERO_VALUE,0x206ee27,F.BOX,0,F.BOX+40,
        0xa5a5a5a5,0,44,ups,310,f['entry_regs'][7],0x200751b,0x201ff45,58]
    need(M.read(before_init,F.FILE2,72)==struct.pack('<18I',*expected_file),'second FILE pre-Init actual prior Box/Mon residues')
    need(sum(x['pc']==0x201ff84 for x in stores)==sum(x['pc']==0x201ff5e for x in stores)==840 and sum(x['pc']==0x20725f2 for x in reads)==576,'whole Reset840 seed/payload576checksum events')
    need([x['regs'][:3]for x in at(0x2072608)]==[[F.BOX,0x4000,i]for unused in range(5)for i in range(4)],'twenty actual PID block selectors')
    return dict(Box=box_proof,Mon62=mon62_proof,Mon58=mon58_proof,intermediate_keys=keys,second_FILE_preInit_sha256=R.sha(struct.pack('<18I',*expected_file)))


def predict(f):
    source_identity_guard();ups=f['input_Up'];parts=f['resource_parts']
    need(f==F.make_input(parts,ups),'complete canonical Reset input/pages')
    need(R.sha(M.read(f['pages'],R.FAT,4104))==R.FAT_SHA and R.sha(M.read(f['pages'],R.FNT,2902))==R.FNT_SHA,'Reset exact cached table identities')
    need(R.sha(M.read(f['pages'],F.P.P.ROOT,12))==F.P.P.SDK.L.L.ROOT_SHA,'Reset exact FS root identity')
    BOX.MAX.division_static(f['pages'])
    result=A.run(f,L.SDK_CODE_SPANS,F.RETURN,thumb_code=L.thumb_code(parts),read_guard=read_owner,write_guard=write_owner)
    count=35199 if ups==3 else 35170;arm=12381 if ups==3 else 12352
    need((len(result['flow']),len(result['reads']),len(result['stores']),result['native_peak'])==(count,7808,4624,712),'manual whole Reset forecast')
    need(sum(not bool(x['regs'][15]&32)for x in result['flow'])==arm and count-arm==22818,'Reset source ARM/Thumb counts')
    expected=list(f['entry_regs']);expected[:4]=[0x2b9b,0,0x4aa02329,0x206eccd];expected[12]=0;expected[14]=0x201ff59;expected[15]=0x6000003f
    need(result['returned']==expected,'source Reset full16 void return')
    final=F.MON.owned_mon(0)[0];need(M.read(result['pages'],F.BOX,236)==final,'source Reset complete Mon236 output')
    need(M.read(result['pages'],R.ARC,92)==M.read(f['pages'],R.ARC,92),'source Reset archive restored')
    for a,n in((F.BOX-16,16),(F.BOX+236,16),(R.TOP-F.FRAME-F.GUARD,F.GUARD)):
        need(M.read(result['pages'],a,n)==M.read(f['pages'],a,n),'source Reset guards unchanged')
    require_memory_delta(f['pages'],result['pages'],result['stores'])
    result.update(ARM_count=arm,Thumb_count=22818,output_Mon_sha256=R.sha(final),causal=causal_checks(f,result))
    return result


observation_policy=C.P.observation_policy


def run(f,policy,observe=True):
    source_identity_guard()
    raw=C.bind(fixture=F,reader=L,memory=M,stack_top=R.TOP,code_spans=CODE_SPANS)(f,policy,observe)
    raw['schema']='native-Mon-Reset-raw-v1';return raw


def require_run(f,raw,predicted=None):
    predicted=predict(f)if predicted is None else predicted
    need(raw.get('schema')=='native-Mon-Reset-raw-v1','native Reset raw schema')
    keys=('executed_count','ARM_count','Thumb_count','unique_executed_starts','callback_count','read_count','store_count','stack_peak','stop_pc')
    need(all(type(raw.get(k))is int for k in keys),'typed Reset counters/PC')
    need(wire(raw['initial'])==wire(F.input_record(f)),'complete frozen Reset input')
    need(wire(raw['backend'])==wire(BACKEND),'qualified Reset backend')
    need(raw['fault']is None and raw['stop_pc']==F.RETURN,'native Reset fault-free return PC')
    C.require_completion(raw,len(predicted['flow']))
    need(raw['models']==raw['runtime_host_writes']==[],'zero Reset model/runtime host write')
    need(tuple(raw[k]for k in keys[:-1])==(len(predicted['flow']),predicted['ARM_count'],22818,len({x['pc']for x in predicted['flow']}),len(predicted['flow'])+1,7808,4624,712),'source Reset counters')
    need(wire(raw['returned'])==wire(predicted['returned']),'source Reset full16 void return')
    need(raw['final_map_sha256']==M.map_digest(predicted['pages']),'source Reset final map hash')
    need(wire(raw['final_pages'])==wire([dict(ram=a,hex=b.hex())for a,b in sorted(predicted['pages'].items())]),'source Reset all final pages')
    if raw['observed']is True:
        for key in('flow','reads','stores'):need(wire(raw[key])==wire(predicted[key]),'source Reset native '+key)
    else:need(raw['observed']is False and raw['flow']==raw['reads']==raw['stores']==[],'Reset OFF no observation projections')
    return predicted
