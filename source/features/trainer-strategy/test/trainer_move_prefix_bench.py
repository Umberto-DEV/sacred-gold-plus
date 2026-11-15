"""One source-predicted type3 first-slot prefix and one uninterrupted CPU run.

Contextual child views below replay source-predicted writes solely for semantic
checks. They never execute a separate CPU or replace state in the producer.
The full prefix still compares every full16/access/page end to end.
"""
from pathlib import Path
import importlib.util
import struct
import types


def load(path,name):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


F=load(Path(__file__).parents[1]/'tools/congela_trainer_move_prefix.py','whole_first_move_prefix_frozen')
P=load(Path(__file__).with_name('box_move_caller_bench.py'),'whole_first_move_retained_caller')
L,R,M,need,wire=F.L,F.R,F.M,F.need,F.M.wire
A,C,BACKEND=P.A,P.C,P.BACKEND
CODE_SPANS=L.CODE_SPANS
PARENT_SHA='7d60999401120eaaf98b1384008db860b4b26402cd117a4abe7a7e800ffec07d'
BOX_GUARDS=[]
for module,values in((P.S,(F.MOVE_VALUE,F.PP_VALUE)),(P.S.G,(F.MOVE_VALUE,F.PP_VALUE)),(P.GET,(None,))):
    for value in values:
        fixture=types.SimpleNamespace(BOX=F.BOX,VALUE=value);top=types.SimpleNamespace(TOP=F.SP-32)
        BOX_GUARDS.append((types.FunctionType(module.read_owner.__code__,{**module.read_owner.__globals__,'R':top,'F':fixture}),
            types.FunctionType(module.write_owner.__code__,{**module.write_owner.__globals__,'R':top,'F':fixture})))
parent_read=types.FunctionType(P.read_owner.__code__,{**P.read_owner.__globals__,'F':F,'R':R,'BOX_GUARDS':BOX_GUARDS})
parent_write=types.FunctionType(P.write_owner.__code__,{**P.write_owner.__globals__,'F':F,'R':R,'BOX_GUARDS':BOX_GUARDS})


def source_identity_guard():
    need(R.sha(Path(P.__file__).read_bytes())==PARENT_SHA,'pinned complete caller bench drift')
    P.source_identity_guard()


def read_owner(pc,a,n):
    if pc==0x2073a22:return n==4 and a==F.SP+0x64
    if pc in(0x2073a28,0x2073a36):return n==4 and a==F.SP+0x5c
    if pc==0x2073a2c:return n==2 and a==F.RECORD+8
    if pc==0x20714e8:return n==4 and a==0x20714ec
    # The parent SDK's older standalone guard can mention its former TOP.
    # Only the three explicit prefix loads may touch this upper caller frame.
    if a<F.TOP and F.SP<a+n:return False
    return parent_read(pc,a,n)


def write_owner(pc,a,n):
    if pc in(0x2073a26,0x2073a3c):return n==4 and a==F.SP+0x5c
    return parent_write(pc,a,n)


require_memory_delta=types.FunctionType(P.require_memory_delta.__code__,{**P.require_memory_delta.__globals__,'write_owner':write_owner,'M':M},argdefs=P.require_memory_delta.__defaults__)
child_fixture=types.SimpleNamespace(**{**vars(F),'RETURN':0x2073a36})
child_checks=types.FunctionType(P.causal_checks.__code__,{**P.causal_checks.__globals__,'F':child_fixture,'R':R,'require_memory_delta':require_memory_delta})


def causal_checks(f,result):
    reads,stores,flow=result['reads'],result['stores'],result['flow'];ups=f['input_Up']
    head=reads[:4];tail=reads[-1]
    expected_reads=[dict(pc=0x2073a22,address=F.SP+0x64,bytes=4,hex=struct.pack('<I',F.RECORD).hex()),
        dict(pc=0x2073a28,address=F.SP+0x5c,bytes=4,hex=struct.pack('<I',F.RECORD).hex()),
        dict(pc=0x2073a2c,address=F.RECORD+8,bytes=2,hex='3601'),
        dict(pc=0x20714e8,address=0x20714ec,bytes=4,hex='f1140702')]
    need(head==expected_reads and tail==dict(pc=0x2073a36,address=F.SP+0x5c,bytes=4,hex=struct.pack('<I',F.RECORD).hex()),'source actual pointer/cursor/move/veneer reads')
    need(stores[0]==dict(pc=0x2073a26,address=F.SP+0x5c,bytes=4,before='dec0adde',value=F.RECORD)and
         stores[-1]==dict(pc=0x2073a3c,address=F.SP+0x5c,bytes=4,before=struct.pack('<I',F.RECORD).hex(),value=F.RECORD+2),'source two real cursor writers/preimages')
    pre=(0x2073a22,0x2073a24,0x2073a26,0x2073a28,0x2073a2a,0x2073a2c,0x2073a2e,0x2073a30,0x2073a32,0x20714e8,0x20714ea)
    post=(0x2073a36,0x2073a38,0x2073a3a,0x2073a3c,0x2073a3e)
    need(tuple(x['pc']for x in flow[:11])==pre and tuple(x['pc']for x in flow[-5:])==post and flow[11]['pc']==0x20714f0,'source prefix/veneer/whole caller/postfix order')
    need(flow[0]['regs']==f['entry_regs'],'source exact synthetic prefix entry')
    veneer=flow[9]['regs'];child=flow[11]['regs'];need(veneer[:3]==[F.BOX,310,0]and veneer[7]==0 and veneer[13]==F.SP and veneer[14]==0x2073a37,'source actual Mon wrapper entry ABI')
    need(child[:3]==[F.BOX,310,0]and child[3]==0x20714f1 and child[7]==0 and child[13:]==[F.SP,0x2073a37,0x4000003f],'source literal veneer actual Box entry')
    # Derived views of a single source trace: native Box entry/return, with
    # preceding cursor publication already present. No callee is rerun.
    initial={a:bytearray(b)for a,b in f['pages'].items()};M.put(initial,stores[0]['address'],stores[0]['value'].to_bytes(4,'little'))
    final={a:bytearray(b)for a,b in initial.items()}
    for x in stores[1:-1]:M.put(final,x['address'],x['value'].to_bytes(x['bytes'],'little'))
    child_input={**f,'entry_pc':0x20714f0,'entry_regs':child,'pages':{a:bytes(b)for a,b in initial.items()}}
    child_result=dict(flow=flow[11:-5],reads=reads[4:-1],stores=stores[1:-1],returned=flow[-5]['regs'],
        pages={a:bytes(b)for a,b in final.items()},stop_pc=0x2073a36,native_peak=result['native_peak'])
    need((len(child_result['flow']),len(child_result['reads']),len(child_result['stores']))==((17198 if ups==3 else 17169),3806,2245),'source complete contextual child extent')
    causal=child_checks(child_input,child_result)
    expected=list(f['entry_regs']);expected[0]=F.RECORD+2;expected[1]=0;expected[2]=causal['seed63'];expected[3]=0x2073a37
    expected[7]=1;expected[12]=0;expected[14]=0x201ff59;expected[15]=0x8000003f
    need(result['returned']==expected,'source prefix stop-gate full16 state')
    caller_final=bytearray(F.caller_frame());struct.pack_into('<I',caller_final,0x5c,F.RECORD+2)
    need(M.read(result['pages'],F.SP,152)==bytes(caller_final),'source all152 caller-frame bytes with cursor-only mutation')
    for a,n in((F.BOX-16,16),(F.BOX+136,116),(F.RECORD-16,140),(F.SP-F.FRAME-F.GUARD,F.GUARD)):
        need(M.read(result['pages'],a,n)==M.read(f['pages'],a,n),'source Mon tail/record/guards unchanged')
    need(all(not(x['address']<F.BOX+236 and F.BOX+136<x['address']+x['bytes'])for x in reads+stores),'source owned tail100 has zero accesses')
    require_memory_delta(f['pages'],result['pages'],stores)
    return dict(**causal,cursor=F.RECORD+2,slot_index=1,child_entry_full16=child,child_return_full16=child_result['returned'],
        prefix_stop_is_function_return=False,tail100_accesses=0)


def predict(f):
    source_identity_guard();ups=f['input_Up'];parts=f['resource_parts'];need(f==F.make_input(parts,ups),'complete canonical synthetic prefix input/pages')
    need(R.sha(M.read(f['pages'],R.FAT,4104))==R.FAT_SHA and R.sha(M.read(f['pages'],R.FNT,2902))==R.FNT_SHA,'first-slot cached FAT/FNT identities')
    need(R.sha(M.read(f['pages'],F.P.P.ROOT,12))==F.P.P.SDK.L.L.ROOT_SHA,'first-slot FS root identity')
    code=L.thumb_code(parts);P.MAX.division_static(f['pages'])
    result=A.run(f,L.SDK_CODE_SPANS,F.RETURN,thumb_code=code,read_guard=read_owner,write_guard=write_owner)
    count=17214 if ups==3 else 17185;ARM=6205 if ups==3 else 6176
    need((len(result['flow']),len(result['reads']),len(result['stores']),result['native_peak'])==(count,3811,2247,688),'manual first-slot prefix instruction/access/stack forecast')
    need(sum(not bool(x['regs'][15]&32)for x in result['flow'])==ARM and count-ARM==11009,'source first-slot ARM/Thumb classification')
    need(len({x['pc']for x in result['flow']})==(1267 if ups==3 else 1238),'source first-slot uniquePC forecast')
    need(count+1<=32768,'source prefix spare stop-gate callback budget')
    result.update(causal=causal_checks(f,result),ARM_count=ARM,Thumb_count=11009)
    return result


observation_policy=P.observation_policy


def run(f,policy,observe=True):
    source_identity_guard();raw=C.bind(fixture=F,reader=L,memory=M,stack_top=F.SP,code_spans=CODE_SPANS)(f,policy,observe)
    raw['schema']='native-trainer-first-move-prefix-raw-v1';return raw


def require_run(f,raw,predicted=None):
    predicted=predict(f)if predicted is None else predicted
    need(raw.get('schema')=='native-trainer-first-move-prefix-raw-v1','native first-slot prefix raw schema')
    keys=('executed_count','ARM_count','Thumb_count','unique_executed_starts','callback_count','read_count','store_count','stack_peak','stop_pc')
    need(all(type(raw.get(k))is int for k in keys),'typed first-slot prefix counters/PC')
    need(wire(raw['initial'])==wire(F.input_record(f)),'complete frozen first-slot prefix input')
    need(wire(raw['backend'])==wire(BACKEND),'qualified first-slot backend')
    need(raw['fault']is None and raw['stop_pc']==F.RETURN,'native first-slot fault-free stop PC')
    C.require_completion(raw,len(predicted['flow']))
    need(raw['models']==raw['runtime_host_writes']==[],'zero first-slot model/runtime host write')
    need(tuple(raw[k]for k in keys[:-1])==(len(predicted['flow']),predicted['ARM_count'],11009,len({x['pc']for x in predicted['flow']}),len(predicted['flow'])+1,3811,2247,688),'source first-slot prefix counters')
    need(wire(raw['returned'])==wire(predicted['returned']),'source first-slot prefix gate full16')
    need(raw['final_map_sha256']==M.map_digest(predicted['pages']),'source first-slot final map hash')
    need(wire(raw['final_pages'])==wire([dict(ram=a,hex=b.hex())for a,b in sorted(predicted['pages'].items())]),'source first-slot all final pages')
    if raw['observed']is True:
        for key in('flow','reads','stores'):need(wire(raw[key])==wire(predicted[key]),'source first-slot native '+key)
    else:need(raw['observed']is False and raw['flow']==raw['reads']==raw['stores']==[],'first-slot OFF no observations')
    return predicted
