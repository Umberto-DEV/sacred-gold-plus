"""Whole original PP getter over the qualified native NARC/SDK chain.

Pure instruction/source prediction precedes an unchanged admitted CPU runner.
PP1 modifies only a declared input memory byte; no guest register is replaced.
"""
from pathlib import Path
import hashlib
import importlib.util
import types


def load(path,name):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


F=load(Path(__file__).parents[1]/'tools/congela_pp_memory.py','whole_PP_frozen')
A=load(Path(__file__).with_name('arm_thumb_pp_oracle.py'),'whole_PP_finite_arithmetic')
P=load(Path(__file__).with_name('fs_memory_narc_bench.py'),'whole_PP_native_NARC_parent')
L,R,M,need,wire=F.L,F.R,F.M,F.need,F.M.wire
CODE_SPANS=P.CODE_SPANS
READ_SITES=P.READ_SITES|frozenset(((0x20733b0,4),(0x207335c,2),(0x2073390,1),(0x207332a,4)))
WRITE_SITES=P.WRITE_SITES|frozenset(((0x2073314,4),))
BACKEND=P.BACKEND
PARENT_PRODUCER_SHA='87b92017d37bcda4e92deebb12db35bb4d9d448c4aac72911cce49de3b7b2531'


def within(a,n,base,size):return base<=a and a+n<=base+size


def read_owner(pc,a,n):
    if(pc,n)not in READ_SITES:return False
    if pc==0x2073390:return a==F.DEST+6 and n==1
    if pc==0x20733b0:return a==0x20733bc and n==4
    if pc==0x207335c:return a==0x207336e and n==2
    if pc==0x207332a:return a in(R.TOP-8,R.TOP-4)and n==4
    if within(a,n,R.TOP-F.FRAME,F.FRAME):return True
    return P.read_owner(pc,a,n)


def write_owner(pc,a,n):
    if(pc,n)not in WRITE_SITES:return False
    if pc==0x2073314:return a in(R.TOP-8,R.TOP-4)and n==4
    if within(a,n,R.TOP-F.FRAME,F.FRAME):return True
    return n==4 and a in(R.ARC+28,R.ARC+36)and P.write_owner(pc,a,n)


def require_memory_delta(initial,final,stores):
    # P85's replay implementation delegates to P84; replace its one owner
    # global directly, retaining typed/preimage/whole-map checks unchanged.
    fn=types.FunctionType(P.P.require_memory_delta.__code__,{**vars(P.P),'write_owner':write_owner})
    return fn(initial,final,stores)


def predict(f):
    pp=f['input_PP'];need(type(pp)is int and pp in(15,1),'typed PP input projection')
    expected=[310,5]+[0xb0000000+i*0x010101 for i in range(2,13)]+[R.TOP,F.RETURN|1,0x6000003f]
    need(f['entry_pc']==F.ENTRY and wire(f['entry_regs'])==wire(expected),'exact native PP getter entry ABI')
    parts={}
    for name,(a,n,digest)in F.P.P.COMPONENTS.items():need(R.sha(M.read(f['pages'],a,n))==digest,'native SDK PP identity '+name)
    for name,item in{**L.L.THUMB,**L.L.DATA,**L.THUMB,**L.DATA}.items():
        a,n,digest=item[0],item[1],item[-1];b=M.read(f['pages'],a,n)
        need(R.sha(b)==digest,'exact original PP/NARC code/data '+name);parts[name]=b
    code=L.thumb_code(parts)
    need(R.sha(M.read(f['pages'],R.FAT,4104))==R.FAT_SHA and R.sha(M.read(f['pages'],R.FNT,2902))==R.FNT_SHA,'PP cached table identities')
    need(R.sha(M.read(f['pages'],F.ROOT,12))==F.P.P.L.L.ROOT_SHA,'PP root BSS fixture identity')
    P.P.require_memory_archive(M.read(f['pages'],R.ARC,92))
    need(M.read(f['pages'],R.TOP-F.FRAME,F.FRAME)==b'\xa5'*F.FRAME,'PP stack and native buffer initialized by guest')
    member=M.read(f['pages'],F.P.P.MEMBER_SOURCE,16);original=bytearray(member);original[6]=15
    need(R.sha(bytes(original))==F.P.P.MEMBER_SHA and member[6]==pp,'original member with only declared PP byte projected')
    projected=[]if pp==15 else[dict(address=F.P.P.MEMBER_SOURCE+6,bytes=1,before_hex='0f',after_hex='01',reason='Declared input memory counterfactual; original owned ROM unchanged')]
    need(wire(f['payload_projections'])==wire(projected),'exact PP source-memory projection provenance')
    result=A.run(f,CODE_SPANS,F.RETURN,thumb_code=code,read_guard=read_owner,write_guard=write_owner)
    counts={name:sum(a<=x['pc']<a+n-F.P.P.POOLS.get(name,0)for x in result['flow'])for name,(a,n,digest)in F.P.P.COMPONENTS.items()if name!='default_table'}
    entries={name:sum(x['pc']==F.P.P.COMPONENTS[name][0]for x in result['flow'])for name in counts}
    need(entries==dict(open=1,fast=1,init=2,convert=1,find=1,send=10,execute=10,release=10,wakeup=10,next=10,disable=57,restore=57,
        fast_command=1,direct_command=1,findpath=1,translate=21,seekdir=4,read_dir=6,read_table=21,read_memory=21,copy=28,strnicmp=6,
        read_wrapper=7,read_core=7,wait=7,seek=5,close=1,read_command=7,read_callback=7,close_command=1),'source unchanged PP native SDK callgraph')
    need(len(result['flow'])==6287 and sum(counts.values())==6159 and sum(x['pc']in code for x in result['flow'])==128,'manual PP forecast6287/6159ARM/128Thumb')
    need((len(result['reads']),len(result['stores']),result['native_peak'])==(1737,1301,640),'manual PP read/store/stack forecast')
    lrs=(0x200734b,0x2007353,0x200735d,0x2007367,0x2007373,0x200737d,0x2007387,0x20073a1,0x20073ab,0x20073bb,0x20073c5,0x20073cf,0x20073e3,0x2007403,0x2007409)
    calls=[x for x in result['flow']if x['pc']in A.RETURNS and x['regs'][14]&1]
    need(len(calls)==15 and tuple(x['regs'][14]for x in calls)==lrs and all(x['regs'][0]==F.FILE and x['regs'][13]==F.LOCAL for x in calls),'PP native API/client frame and fifteen actual LRs')
    need(calls[1]['regs'][:4]==[F.FILE,F.PATH,0,0],'PP native Init/Open volatile ABI')
    callbacks=[x for x in result['flow']if x['pc']==0x20d7448]
    destinations=(F.LOCAL+20,F.LOCAL+20,F.LOCAL+8,F.LOCAL+20,F.LOCAL+16,F.LOCAL+12,F.DEST)
    need([x['regs'][:4]for x in callbacks]==[[R.ARC,dest,0x1093800+a,n]for dest,(a,n)in zip(destinations,L.L.WINDOWS)],'PP source-selected seven native reads36')
    need([x['regs'][1:3]for x in calls if x['pc']==0x20d83dc]==[[a,0]for a in(0xc,0x14,0xed8,0x9cc,0x224c)],'PP five native SET seeks')
    reads=[x for x in result['reads']if x['pc']==0x2073390]
    need(reads==[dict(pc=0x2073390,address=F.DEST+6,bytes=1,hex=bytes([pp]).hex())],'native PP leaf reads the selected member byte6')
    need(M.read(result['pages'],F.DEST,16)==member,'PP native stack buffer contains full member')
    final=M.read(result['pages'],F.FILE,72)
    need(all(R.u32(final,a)==v for a,v in((8,0),(12,0),(16,14),(20,0),(32,140),(36,0x1093800),(40,0x109645c),(44,0x1095a5c),(48,F.DEST),(52,16),(56,16))),'PP final native closed FILE lifetime')
    need(M.read(result['pages'],R.ARC,92)==M.read(f['pages'],R.ARC,92),'PP full archive restored')
    expected[:4]=[pp,42,0x6000001f,0x2007509];expected[12]=R.TOP-8;expected[14]=0x2073329;expected[15]=0x3f
    need(wire(result['returned'])==wire(expected),'PP API scalar and complete return ABI')
    require_memory_delta(f['pages'],result['pages'],result['stores'])
    result.update(function_counts=counts,entry_counts=entries,original_ROM_count=6287,ARM_count=6159,Thumb_count=128,API_entries=calls)
    return result


def observation_policy(predicted):return P.observation_policy(predicted)


def run(f,policy,observe=True):
    need(hashlib.sha256(Path(P.__file__).read_bytes()).hexdigest()==PARENT_PRODUCER_SHA,'pinned native NARC CPU runner drift')
    # The parent producer constructs fetch widths from L.THUMB then calls
    # L.thumb_code. Supply the combined byte corpus, retaining the actual reader.
    resources=types.SimpleNamespace(**{**vars(L),'THUMB':{**L.L.THUMB,**L.THUMB}})
    fn=types.FunctionType(P.run.__code__,{**vars(P),'F':F,'L':resources,'CODE_SPANS':CODE_SPANS})
    raw=fn(f,policy,observe);raw['schema']='native-PP-memory-raw-v1';return raw


def require_run(f,raw):
    predicted=predict(f)
    need(raw.get('schema')=='native-PP-memory-raw-v1','native PP raw schema')
    keys=('executed_count','ARM_count','Thumb_count','unique_executed_starts','callback_count','read_count','store_count','stack_peak','stop_pc')
    need(all(type(raw[k])is int for k in keys),'typed PP native counters/PC')
    need(wire(raw['initial'])==wire(F.input_record(f)),'complete frozen PP input')
    need(wire(raw['backend'])==wire(BACKEND),'qualified PP backend')
    need(raw['fault']is None and raw['stopped']is True and raw['stop_pc']==F.RETURN,'native PP API return')
    need(raw['models']==raw['runtime_host_writes']==[],'zero PP service models/runtime host writes')
    need(tuple(raw[k]for k in keys[:-1])==(6287,6159,128,len({x['pc']for x in predicted['flow']}),6288,1737,1301,640),'source PP counters')
    need(wire(raw['returned'])==wire(predicted['returned']),'source full16 PP return ABI')
    need(raw['final_map_sha256']==M.map_digest(predicted['pages']),'source PP final map hash')
    need(wire(raw['final_pages'])==wire([dict(ram=a,hex=b.hex())for a,b in sorted(predicted['pages'].items())]),'source PP all final pages')
    if raw['observed']is True:
        for k in('flow','reads','stores'):need(wire(raw[k])==wire(predicted[k]),'source PP native '+k)
    else:need(raw['observed']is False and raw['flow']==raw['reads']==raw['stores']==[],'PP OFF no observation projections')
    return predicted
