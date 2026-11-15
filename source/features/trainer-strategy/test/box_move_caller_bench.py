"""Full native Box move/PP caller: one lifecycle and source-led causal checks.

Canonical resources and owned input are frozen before prediction. Parent
Box guards are rebased to the actual caller frame; SDK guards remain finite
PC/width plus declared owners. Only admission sets reach the CPU producer.
"""
from pathlib import Path
import importlib.util
import struct
import types


def load(path,name):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


F=load(Path(__file__).parents[1]/'tools/congela_box_move_caller.py','complete_caller_frozen')
A=load(Path(__file__).with_name('arm_thumb_box_caller_oracle.py'),'complete_caller_arithmetic')
C=load(Path(__file__).with_name('box_move_caller_cpu.py'),'complete_caller_CPU')
S=load(Path(__file__).with_name('box_move_setter_bench.py'),'caller_retained_move_setter')
GET=load(Path(__file__).with_name('box_ppup_bench.py'),'caller_retained_getter')
MAX=load(Path(__file__).with_name('maxpp_memory_bench.py'),'caller_retained_MaxPP')
L,R,M,need,wire=F.L,F.R,F.M,F.need,F.M.wire
BACKEND=C.P.BACKEND
CODE_SPANS=L.CODE_SPANS
PINNED={S:'c82e50e378a00fc67df950f6063e2e4a1a4a4abf4a87a0543d2d95abbff52dda',GET:'b7017b3127aea073cf3aae7439ad5551ba54a63a538ed4378af165e8888e48f2'}
# Each standalone Box callee really enters with SP=TOP-32. Both setter Values
# are caller stack slots, never a host buffer. Union guards admit those two
# exact pointers; the actual instruction semantics and full16 route choose one.
BOX_GUARDS=[]
for module,values in((S,(F.MOVE_VALUE,F.PP_VALUE)),(S.G,(F.MOVE_VALUE,F.PP_VALUE)),(GET,(None,))):
    for value in values:
        fixture=types.SimpleNamespace(BOX=F.BOX,VALUE=value)
        namespace={**module.read_owner.__globals__,'R':types.SimpleNamespace(TOP=R.TOP-32),'F':fixture}
        read=types.FunctionType(module.read_owner.__code__,namespace)
        write=types.FunctionType(module.write_owner.__code__,{**module.write_owner.__globals__,'R':types.SimpleNamespace(TOP=R.TOP-32),'F':fixture})
        BOX_GUARDS.append((read,write))


def source_identity_guard():
    S.source_identity_guard();GET.source_identity_guard();A.source_identity_guard();C.source_identity_guard()
    for module,digest in PINNED.items():need(R.sha(Path(module.__file__).read_bytes())==digest,'pinned caller lifecycle helper drift')


def within(a,n,b,size):return b<=a and a+n<=b+size


def read_owner(pc,a,n):
    if pc==0x2071514:return n==2 and a==F.MOVE_VALUE
    if pc==0x207152a:return n==4 and a in range(R.TOP-32,R.TOP-20,4)
    if pc==0x207152c:return n==4 and a==R.TOP-20
    if any(read(pc,a,n)for read,write in BOX_GUARDS):return True
    if(pc,n)not in MAX.READ_SITES:return False
    if pc==0x2073390:return n==1 and a==F.DEST+6
    if within(a,n,R.TOP-F.FRAME,F.FRAME):return True
    return MAX.read_owner(pc,a,n)


def write_owner(pc,a,n):
    if pc==0x20714f0:return n==4 and a in range(R.TOP-16,R.TOP,4)
    if pc==0x20714f2:return n==4 and a in range(R.TOP-32,R.TOP-16,4)
    if pc==0x207151c:return n==1 and a==F.PP_VALUE
    if any(write(pc,a,n)for read,write in BOX_GUARDS):return True
    if(pc,n)not in MAX.WRITE_SITES:return False
    if within(a,n,R.TOP-F.FRAME,F.FRAME):return True
    return n==4 and a in(R.ARC+28,R.ARC+36)and MAX.write_owner(pc,a,n)


require_memory_delta=types.FunctionType(S.require_memory_delta.__code__,{**S.require_memory_delta.__globals__,'write_owner':write_owner,'M':M},argdefs=S.require_memory_delta.__defaults__)
crypt=GET.crypt


def source_result(ups):
    initial,plain=F.owned_box(ups);updated=bytearray(plain);updated[72]=15+15*20*ups//100
    key=sum(x[0]for x in struct.iter_unpack('<H',updated))&65535
    cipher,seeds=crypt(bytes(updated),key);final=initial[:6]+struct.pack('<H',key)+cipher
    expected={3:'401b0fa15982184e6650413627b5d3540372253de0664aed7ed928d845bc9c6b',0:F.BOX_SHA[0]}
    need(R.sha(final)==expected[ups],'independent whole caller output Box digest')
    return initial,plain,final,bytes(updated),key,seeds


def causal_checks(f,result):
    ups=f['input_Up'];answer=15+15*20*ups//100;initial,plain,final,updated,key,seeds=source_result(ups)
    flow=result['flow'];reads=result['reads'];stores=result['stores']
    def at(pc):return[x for x in flow if x['pc']==pc]
    expected=list(f['entry_regs']);expected[:4]=[seeds[-1]>>16,0,seeds[-2],F.RETURN|1]
    expected[12]=0;expected[14]=0x201ff59;expected[15]=0x6000003f
    need(result['returned']==expected,'source caller full16 void return')
    calls=[x for x in flow if x['pc']in(0x206ed70,0x206e640,0x207332c)]
    need([(x['pc'],x['regs'][:3],x['regs'][13],x['regs'][14])for x in calls]==[
        (0x206ed70,[F.BOX,54,F.MOVE_VALUE],R.TOP-32,0x2071503),
        (0x206e640,[F.BOX,62,0],R.TOP-32,0x207150f),
        (0x207332c,[310,ups,crypt(plain,0x2a8+ups)[1][-2]],R.TOP-32,0x207151b),
        (0x206ed70,[F.BOX,58,F.PP_VALUE],R.TOP-32,0x207152b)],'source four actual caller API boundaries')
    need([x['regs'][0]for x in at(0x207150e)]==[ups]and[x['regs'][1]for x in at(0x2071516)]==[ups],'source getter result actually reaches MaxPP')
    need([x['regs'][:2]for x in at(A.BASE.DIV_ENTRY)]==[[15*20*ups,100]],'source actual DIV arguments')
    need([x['regs'][:2]for x in at(A.BASE.DIV_RETURN)]==[[answer-15,0]],'source actual DIV quotient/remainder')
    need([x['regs'][0]for x in at(0x207151a)]==[answer],'source native MaxPP result before caller STRB')
    need([x for x in reads if x['pc']==0x206e986]==[dict(pc=0x206e986,address=F.BOX+84,bytes=1,hex=bytes([ups]).hex())],'source actual encrypted Box PP-Up selection')
    need([x for x in reads if x['pc']==0x2073390]==[dict(pc=0x2073390,address=F.DEST+6,bytes=1,hex='0f')],'source native PP15 buffer read')
    need([x for x in stores if x['pc']==0x207151c]==[dict(pc=0x207151c,address=F.PP_VALUE,bytes=1,before=bytes([f['entry_regs'][3]&255]).hex(),value=answer)],'source caller PP byte real stack writer/preimage')
    need([x for x in reads if x['pc']==0x206f0f6]==[dict(pc=0x206f0f6,address=F.PP_VALUE,bytes=1,hex=bytes([answer]).hex())],'source setter consumes caller stack byte')
    need([x for x in stores if x['pc']==0x206f0fe]==[dict(pc=0x206f0fe,address=F.BOX+80,bytes=1,before='0f',value=answer)],'source final PP store even idempotent')
    need([x for x in stores if x['pc']==0x206f0f0]==[dict(pc=0x206f0f0,address=F.BOX+72,bytes=2,before='3601',value=310)],'source first idempotent move store')
    oldkey=0x2a8+ups;_,oldseeds=crypt(plain,oldkey)
    need([x['value']for x in stores if x['pc']==0x206edd6]==[oldkey,key],'source two actual checksum header stores')
    checks=[x for x in reads if x['pc']==0x20725f2]
    need([(x['address'],x['hex'])for x in checks]==[(F.BOX+8+2*i,data[2*i:2*i+2].hex())for data in(plain,plain,plain,plain,updated)for i in range(64)],'source all320 checksum reads')
    payload=[x for x in stores if x['pc']==0x201ff5e]
    phases=((initial[8:],plain),(plain,initial[8:]),(initial[8:],plain),(plain,initial[8:]),(initial[8:],plain),(updated,final[8:]))
    need([(x['address'],x['bytes'],x['before'],x['value'])for x in payload]==[(F.BOX+8+2*i,2,before[2*i:2*i+2].hex(),int.from_bytes(after[2*i:2*i+2],'little'))for before,after in phases for i in range(64)],'source384 transient crypto stores across three calls')
    updates=[x for x in stores if x['pc']==0x201ff84]
    expected_updates=[]
    for seed,seq in[(oldkey,oldseeds)]*5+[(key,seeds)]:
        expected_updates.extend((R.TOP-56,4,before,after)for before,after in zip([seed]+seq[:-1],seq))
    need([(x['address'],x['bytes'],int.from_bytes(bytes.fromhex(x['before']),'little'),x['value'])for x in updates]==expected_updates,'source384 private seed updates with actual key lifetimes')
    need([x['regs'][:3]for x in at(0x2072608)]==[[F.BOX,0x4000,i]for _ in range(3)for i in range(4)],'source12 real PID selectors')
    # First native FS_InitFile sees residues written by Set54/Get62. It must
    # initialize its own seven fields without replacing that frame with zeros.
    init=at(0x20d7f98);need([(x['regs'][0],x['regs'][13],x['regs'][14])for x in init]==[(F.FILE,F.LOCAL,0x200734b),(F.FILE-128,F.FILE-128,0x20d8198)],'source client and temporary directory FILE entries')
    memory={a:bytearray(b)for a,b in f['pages'].items()}
    # No SDK instruction has run yet, so all writes so far are exactly the
    # first Box phases plus caller prologue and MaxPP/NARC prologues.
    first_sdk=next(i for i,x in enumerate(stores)if any(a<=x['pc']<a+n for a,n in L.SDK_CODE_SPANS))
    for x in stores[:first_sdk]:M.put(memory,x['address'],x['value'].to_bytes(x['bytes'],'little'))
    expected_file=[0xa5a5a5a5]*18
    for off,value in((16,F.MOVE_VALUE),(20,F.BOX+72),(24,F.MOVE_VALUE),(28,0x206ee27),(32,F.BOX),(36,0),(40,F.BOX+40)):expected_file[off//4]=value
    need(M.read(memory,F.FILE,72)==struct.pack('<18I',*expected_file),'source FILE pre-Init actual Box frame residue')
    need(M.read(result['pages'],F.BOX,136)==final,'source complete final Box')
    need(M.read(result['pages'],R.ARC,92)==M.read(f['pages'],R.ARC,92),'source memory archive restored')
    for a,n in((F.BOX-16,16),(F.BOX+136,16),(R.TOP-F.FRAME-F.GUARD,F.GUARD)):
        need(M.read(result['pages'],a,n)==M.read(f['pages'],a,n),'source caller guards unchanged')
    require_memory_delta(f['pages'],result['pages'],stores)
    return dict(PP=answer,checksum=key,output_Box_sha256=R.sha(final),seed63=seeds[-2],seed64=seeds[-1],pre_Init_FILE_sha256=R.sha(struct.pack('<18I',*expected_file)))


def predict(f):
    source_identity_guard();ups=f['input_Up'];parts=f['resource_parts']
    need(f==F.make_input(parts,ups),'complete canonical caller input/pages')
    need(R.sha(M.read(f['pages'],R.FAT,4104))==R.FAT_SHA and R.sha(M.read(f['pages'],R.FNT,2902))==R.FNT_SHA,'caller cached table identities')
    need(R.sha(M.read(f['pages'],F.P.ROOT,12))==F.P.SDK.L.L.ROOT_SHA,'caller FS root identity')
    code=L.thumb_code(parts);MAX.division_static(f['pages'])
    result=A.run(f,L.SDK_CODE_SPANS,F.RETURN,thumb_code=code,read_guard=read_owner,write_guard=write_owner)
    count=17198 if ups==3 else 17169;ARM=6205 if ups==3 else 6176
    need((len(result['flow']),len(result['reads']),len(result['stores']),result['native_peak'])==(count,3806,2245,688),'manual composed caller instruction/access/stack forecast')
    need(sum(not bool(x['regs'][15]&32)for x in result['flow'])==ARM and count-ARM==10993,'source caller ARM/Thumb classification')
    need(count+1<=32768,'source caller spare callback budget')
    result.update(causal=causal_checks(f,result),ARM_count=ARM,Thumb_count=10993)
    return result


observation_policy=C.P.observation_policy


def run(f,policy,observe=True):
    source_identity_guard()
    raw=C.bind(fixture=F,reader=L,memory=M,stack_top=R.TOP,code_spans=CODE_SPANS)(f,policy,observe)
    raw['schema']='native-box-move-caller-raw-v1';return raw


def require_run(f,raw,predicted=None):
    predicted=predict(f)if predicted is None else predicted
    need(raw.get('schema')=='native-box-move-caller-raw-v1','native caller raw schema')
    keys=('executed_count','ARM_count','Thumb_count','unique_executed_starts','callback_count','read_count','store_count','stack_peak','stop_pc')
    need(all(type(raw.get(k))is int for k in keys),'typed caller counters/PC')
    need(wire(raw['initial'])==wire(F.input_record(f)),'complete frozen caller input')
    need(wire(raw['backend'])==wire(BACKEND),'qualified caller backend')
    need(raw['fault']is None and raw['stop_pc']==F.RETURN,'native caller fault-free return PC')
    C.require_completion(raw,len(predicted['flow']))
    need(raw['models']==raw['runtime_host_writes']==[],'zero caller model/runtime host write')
    need(tuple(raw[k]for k in keys[:-1])==(len(predicted['flow']),predicted['ARM_count'],10993,len({x['pc']for x in predicted['flow']}),len(predicted['flow'])+1,3806,2245,688),'source caller counters')
    need(wire(raw['returned'])==wire(predicted['returned']),'source caller full16 void return')
    need(raw['final_map_sha256']==M.map_digest(predicted['pages']),'source caller final map hash')
    need(wire(raw['final_pages'])==wire([dict(ram=a,hex=b.hex())for a,b in sorted(predicted['pages'].items())]),'source caller all final pages')
    if raw['observed']is True:
        for key in('flow','reads','stores'):need(wire(raw[key])==wire(predicted[key]),'source caller native '+key)
    else:need(raw['observed']is False and raw['flow']==raw['reads']==raw['stores']==[],'caller OFF no observation projections')
    return predicted
