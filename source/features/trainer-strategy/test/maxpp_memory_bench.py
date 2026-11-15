"""Whole MaxPP source prediction and uninterrupted native CPU composition.

SDK arithmetic remains on the old oracle. RSB/ADC are scoped to the exact
signed DIV corpus; only observation admission metadata reaches the producer.
"""
from pathlib import Path
import hashlib
import importlib.util
import types


def load(path,name):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


F=load(Path(__file__).parents[1]/'tools/congela_maxpp_memory.py','whole_MaxPP_frozen')
A=load(Path(__file__).with_name('arm_thumb_maxpp_oracle.py'),'whole_MaxPP_finite_arithmetic')
P=load(Path(__file__).with_name('pp_memory_bench.py'),'whole_MaxPP_PP_parent')
L,R,M,need,wire=F.L,F.R,F.M,F.need,F.M.wire
SDK_CODE_SPANS=P.CODE_SPANS
CODE_SPANS=SDK_CODE_SPANS+(L.DIV[:2],)
READ_SITES=P.READ_SITES|frozenset(((0x2073352,4),))
WRITE_SITES=P.WRITE_SITES|frozenset(((0x207332c,4),))
BACKEND=P.BACKEND


def within(a,n,base,size):return base<=a and a+n<=base+size


def read_owner(pc,a,n):
    if(pc,n)not in READ_SITES:return False
    if pc==0x2073390:return a==F.DEST+6 and n==1
    if pc==0x20733b0:return a==0x20733bc and n==4
    if pc==0x207335c:return a==0x207336e and n==2
    if pc==0x207332a:return a in(R.TOP-24,R.TOP-20)and n==4
    if pc==0x2073352:return a in(R.TOP-16,R.TOP-12,R.TOP-8,R.TOP-4)and n==4
    if within(a,n,R.TOP-F.FRAME,F.FRAME):return True
    return P.read_owner(pc,a,n)


def write_owner(pc,a,n):
    if(pc,n)not in WRITE_SITES:return False
    if pc==0x2073314:return a in(R.TOP-24,R.TOP-20)and n==4
    if pc==0x207332c:return a in(R.TOP-16,R.TOP-12,R.TOP-8,R.TOP-4)and n==4
    if within(a,n,R.TOP-F.FRAME,F.FRAME):return True
    return n==4 and a in(R.ARC+28,R.ARC+36)and P.write_owner(pc,a,n)


def require_memory_delta(initial,final,stores):
    original=P.P.P.require_memory_delta
    return types.FunctionType(original.__code__,{**vars(P.P.P),'write_owner':write_owner})(initial,final,stores)


def division_static(pages):
    a,n,digest=L.DIV;b=M.read(pages,a,n);need(R.sha(b)==digest,'exact compiled/native signed DIV body')
    groups={}
    for pc in range(a,a+n,4):
        word=int.from_bytes(M.read(pages,pc,4),'little');group=A.D.validate_word(word);groups[pc]=group
        need(group in('data','branch','exchange'),'DIV is register-only code, no memory/PSR')
        if group=='branch':need(not word&(1<<24),'DIV has no linked call')
        if group=='exchange':need(pc==A.DIV_RETURN and word==0xe12fff1e,'DIV single exact BX return')
        if group=='data':
            op=(word>>21)&15;rd=(word>>12)&15
            need(rd!=13 and(op in(8,10)or rd!=15 or pc==0x20f2a04),'DIV has no SP write and only its identified computed PC write')
    need(len(groups)==131,'131 DIV instruction starts')
    return groups


def predict(f):
    ups,pp=f['input_Up'],f['input_PP']
    need(type(ups)is int and type(pp)is int and(ups,pp)in F.PROFILES.values(),'typed MaxPP profile')
    expected=[310,ups]+[0xb0000000+i*0x010101 for i in range(2,13)]+[R.TOP,F.RETURN|1,0x6000003f]
    need(f['entry_pc']==F.ENTRY and wire(f['entry_regs'])==wire(expected),'exact whole MaxPP entry ABI')
    for name,(a,n,digest)in F.SDK.COMPONENTS.items():need(R.sha(M.read(f['pages'],a,n))==digest,'exact MaxPP SDK body '+name)
    parts={}
    for name,item in{**F.NARC.THUMB,**F.NARC.DATA,**F.P.L.THUMB,**F.P.L.DATA,'maxpp':L.MAXPP}.items():
        a,n,digest=item[0],item[1],item[-1];b=M.read(f['pages'],a,n)
        need(R.sha(b)==digest,'exact MaxPP caller/child/data '+name);parts[name]=b
    code=L.thumb_code(parts);division_static(f['pages'])
    need(R.sha(M.read(f['pages'],R.FAT,4104))==R.FAT_SHA and R.sha(M.read(f['pages'],R.FNT,2902))==R.FNT_SHA,'MaxPP cached table identities')
    need(R.sha(M.read(f['pages'],F.ROOT,12))==F.SDK.L.L.ROOT_SHA,'MaxPP root BSS fixture identity')
    P.P.P.require_memory_archive(M.read(f['pages'],R.ARC,92))
    need(M.read(f['pages'],R.TOP-F.FRAME,F.FRAME)==b'\xa5'*F.FRAME,'native MaxPP/child stack starts untouched')
    member=M.read(f['pages'],F.SDK.MEMBER_SOURCE,16);original=bytearray(member);original[6]=15
    need(R.sha(bytes(original))==F.SDK.MEMBER_SHA and member[6]==pp,'original member with only declared MaxPP source projection')
    projected=[]if pp==15 else[dict(address=F.SDK.MEMBER_SOURCE+6,bytes=1,before_hex='0f',after_hex='01',reason='Declared input memory counterfactual; original owned ROM unchanged')]
    need(wire(f['payload_projections'])==wire(projected),'MaxPP source input provenance')
    # The full SDK corpus is decoded by the unchanged validator. The separate
    # DIV classifier above may use RSB/ADC, but no DIV span reaches this check
    # or the SDK selector in the source interpreter.
    memory=P.P.P
    sites=types.FunctionType(memory.memory_sites.__code__,{**vars(memory),'CODE_SPANS':SDK_CODE_SPANS,'A':A.A})(f['pages'])
    expected_sites={kind:{(pc,n)for pc,n in values if any(a<=pc<a+size for a,size in SDK_CODE_SPANS)}for kind,values in(('read',P.READ_SITES),('write',P.WRITE_SITES))}
    need(sites==expected_sites,'unchanged old-SDK memory instruction corpus')
    result=A.run(f,SDK_CODE_SPANS,F.RETURN,thumb_code=code,read_guard=read_owner,write_guard=write_owner)
    clamped=min(ups,3);numerator=pp*20*clamped;quotient,remainder=divmod(numerator,100);answer=(pp+quotient)&255
    div_count=46 if numerator==900 else 17;thumb_count=146 if ups==4 else 145;count=6159+div_count+thumb_count
    need((len(result['flow']),len(result['reads']),len(result['stores']),result['native_peak'])==(count,1741,1305,656),'independent MaxPP flow/read/store/stack forecast')
    need(sum(x['pc']in code for x in result['flow'])==thumb_count and sum(L.DIV[0]<=x['pc']<L.DIV[0]+524 for x in result['flow'])==div_count,'MaxPP/DIV instruction classification')
    counts={name:sum(a<=x['pc']<a+n-F.SDK.POOLS.get(name,0)for x in result['flow'])for name,(a,n,digest)in F.SDK.COMPONENTS.items()if name!='default_table'}
    entries={name:sum(x['pc']==F.SDK.COMPONENTS[name][0]for x in result['flow'])for name in counts}
    need(sum(counts.values())==6159 and entries==dict(open=1,fast=1,init=2,convert=1,find=1,send=10,execute=10,release=10,wakeup=10,next=10,disable=57,restore=57,
        fast_command=1,direct_command=1,findpath=1,translate=21,seekdir=4,read_dir=6,read_table=21,read_memory=21,copy=28,strnicmp=6,
        read_wrapper=7,read_core=7,wait=7,seek=5,close=1,read_command=7,read_callback=7,close_command=1),'MaxPP unchanged SDK callgraph')
    calls=[x for x in result['flow']if x['pc']in A.P.RETURNS and x['regs'][14]&1]
    need(len(calls)==15 and all(x['regs'][0]==F.FILE and x['regs'][13]==F.LOCAL for x in calls),'MaxPP native FS frame/lifetime')
    div_entries=[x for x in result['flow']if x['pc']==A.DIV_ENTRY]
    div_returns=[x for x in result['flow']if x['pc']==A.DIV_RETURN]
    need(len(div_entries)==len(div_returns)==1 and div_entries[0]['regs'][:2]==[numerator,100]and div_entries[0]['regs'][14]==0x207334d,'actual MaxPP signed DIV arguments/LR')
    need(div_returns[0]['regs'][:2]==[quotient,remainder]and div_returns[0]['regs'][12]==0 and div_returns[0]['regs'][15]==0x6000001f,'source DIV quotient/remainder/sign flags')
    computed=[x for x in result['flow']if x['pc']==0x20f2a04]
    need((len(computed)==1 and result['flow'][result['flow'].index(computed[0])+1]['pc']==0x20f2b5c)if numerator==900 else not computed,'DIV unrolled dispatch versus quick path')
    need([e for e in result['reads']if e['pc']==0x2073390]==[dict(pc=0x2073390,address=F.DEST+6,bytes=1,hex=bytes([pp]).hex())],'MaxPP child consumes actual source PP byte')
    need(M.read(result['pages'],F.DEST,16)==member,'MaxPP native child buffer16')
    final=M.read(result['pages'],F.FILE,72)
    need(all(R.u32(final,a)==v for a,v in((8,0),(12,0),(16,14),(20,0),(32,140),(36,0x1093800),(40,0x109645c),(44,0x1095a5c),(48,F.DEST),(52,16),(56,16))),'MaxPP final closed FILE')
    need(M.read(result['pages'],R.ARC,92)==M.read(f['pages'],R.ARC,92),'MaxPP full archive restored')
    expected[:3]=[answer,remainder,0x54 if numerator==900 else 0x6000001f];expected[12]=0;expected[14]=0x207334d;expected[15]=0x3f
    need(wire(result['returned'])==wire(expected),'whole MaxPP u8 result/full16 ABI')
    require_memory_delta(f['pages'],result['pages'],result['stores'])
    result.update(function_counts=counts,entry_counts=entries,original_ROM_count=count,SDK_count=6159,DIV_count=div_count,
        ARM_count=6159+div_count,Thumb_count=thumb_count,division_entry=div_entries[0],division_return=div_returns[0])
    return result


def observation_policy(predicted):return P.observation_policy(predicted)


def run(f,policy,observe=True):
    need(hashlib.sha256(Path(P.P.__file__).read_bytes()).hexdigest()==P.PARENT_PRODUCER_SHA,'pinned uninterrupted NARC CPU producer drift')
    resources=types.SimpleNamespace(**{**vars(L),'THUMB':{**F.NARC.THUMB,**F.P.L.THUMB,'maxpp':L.MAXPP}})
    fn=types.FunctionType(P.P.run.__code__,{**vars(P.P),'F':F,'L':resources,'CODE_SPANS':CODE_SPANS})
    raw=fn(f,policy,observe);raw['schema']='native-MaxPP-memory-raw-v1';return raw


def require_run(f,raw):
    predicted=predict(f)
    need(raw.get('schema')=='native-MaxPP-memory-raw-v1','native MaxPP raw schema')
    keys=('executed_count','ARM_count','Thumb_count','unique_executed_starts','callback_count','read_count','store_count','stack_peak','stop_pc')
    need(all(type(raw[k])is int for k in keys),'typed MaxPP counters/PC')
    need(wire(raw['initial'])==wire(F.input_record(f)),'complete frozen MaxPP input')
    need(wire(raw['backend'])==wire(BACKEND),'qualified MaxPP backend')
    need(raw['fault']is None and raw['stopped']is True and raw['stop_pc']==F.RETURN,'whole original MaxPP API return')
    need(raw['models']==raw['runtime_host_writes']==[],'zero MaxPP service models/runtime host writes')
    need(tuple(raw[k]for k in keys[:-1])==(len(predicted['flow']),predicted['ARM_count'],predicted['Thumb_count'],len({x['pc']for x in predicted['flow']}),len(predicted['flow'])+1,1741,1305,656),'source MaxPP counters')
    need(wire(raw['returned'])==wire(predicted['returned']),'source MaxPP full16 return ABI')
    need(raw['final_map_sha256']==M.map_digest(predicted['pages']),'source MaxPP final map hash')
    need(wire(raw['final_pages'])==wire([dict(ram=a,hex=b.hex())for a,b in sorted(predicted['pages'].items())]),'source MaxPP all final pages')
    if raw['observed']is True:
        for key in('flow','reads','stores'):need(wire(raw[key])==wire(predicted[key]),'source MaxPP native '+key)
    else:need(raw['observed']is False and raw['flow']==raw['reads']==raw['stores']==[],'MaxPP OFF empty observation ledgers')
    return predicted
