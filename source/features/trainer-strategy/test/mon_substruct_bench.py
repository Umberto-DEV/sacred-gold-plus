"""Whole GetSubstruct over the finite PID-row/selector domain, no Box reads."""
from pathlib import Path
import importlib.util
import types


def load(path,name):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


F=load(Path(__file__).parents[1]/'tools/congela_mon_substruct.py','whole_substruct_frozen')
C=load(Path(__file__).with_name('mon_cipher_bench.py'),'substruct_retained_producer_and_replay')
A=load(Path(__file__).with_name('arm_thumb_substruct_oracle.py'),'whole_substruct_arithmetic')
P=C.P
L,R,M,need,wire=F.L,F.R,F.M,F.need,F.M.wire
BACKEND,PRODUCER_SHA=C.BACKEND,C.PRODUCER_SHA
PARENT_SHA='c2bf2c798a59fab5466fc8776235f1665e88f08aa473ca2ef1ab33af810a17e1'
CODE_SPANS=()
TABLE=0x20ff733


def source_identity_guard():
    need(R.sha(Path(C.__file__).read_bytes())==PARENT_SHA and
         R.sha(Path(P.__file__).read_bytes())==PRODUCER_SHA,'pinned GetSubstruct parent drift')
    A.source_identity_guard()


def read_owner(pc,a,n,*,table_index=None):
    if pc==0x2072620 and n==4:return a==0x2072630
    if pc==0x207262c and n==4:return a in range(R.TOP-16,R.TOP,4)
    return type(table_index)is int and 0<=table_index<128 and pc==0x2072626 and n==1 and a==TABLE+table_index


def write_owner(pc,a,n):return pc==0x2072608 and n==4 and a in range(R.TOP-16,R.TOP,4)


require_memory_delta=types.FunctionType(C.require_memory_delta.__code__,{**vars(C),'write_owner':write_owner,'M':M},argdefs=C.require_memory_delta.__defaults__)


def source_offset(table,pid,which):
    need(type(table)is bytes and len(table)==128 and type(pid)is int and 0<=pid<=0xffffffff and
         type(which)is int and 0<=which<=3,'typed GetSubstruct source lookup')
    row=(pid&0x3e000)>>13;offset=table[4*row+which]
    need(offset in(0,32,64,96),'source offset within a physical32byte block')
    return row,offset


def predict(f):
    source_identity_guard();pid,which=f['input_PID'],f['input_which']
    parts={name:M.read(f['pages'],item[0],item[1])for name,item in {**L.THUMB,**L.DATA}.items()}
    need(f==F.make_input(parts,pid,which),'complete canonical GetSubstruct input/pages')
    row,offset=source_offset(parts['offsets'],pid,which);thumb=L.thumb_code(parts)
    result=A.run(f,(),F.RETURN,cap=64,thumb_code=thumb,
        read_guard=lambda pc,a,n:read_owner(pc,a,n,table_index=4*row+which),write_guard=write_owner)
    need((len(result['flow']),len({x['pc']for x in result['flow']}),len(result['reads']),len(result['stores']),result['native_peak'])==
         (17,17,6,4,16),'manual GetSubstruct forecast')
    need(all(x['regs'][15]&32 for x in result['flow']),'GetSubstruct exclusively Thumb')
    expected=list(f['entry_regs']);expected[:3]=[F.BOX+8+offset,4*row,which];expected[15]=0x3f
    need(result['returned']==expected,'source GetSubstruct full16 return ABI')
    need(F.BOX+8<=expected[0]and expected[0]+32<=F.BOX+136,'source returned whole32byte block inside storage')
    need([(x['pc'],x['address'],x['bytes'],x['value'])for x in result['stores']]==
         [(0x2072608,R.TOP-16+4*i,4,f['entry_regs'][reg])for i,reg in enumerate((4,5,6,14))],'source four GetSubstruct saved words')
    need([(x['pc'],x['address'],x['bytes'])for x in result['reads']]==
         [(0x2072620,0x2072630,4),(0x2072626,TABLE+4*row+which,1)]+
         [(0x207262c,R.TOP-16+4*i,4)for i in range(4)],'source exact literal/table/POP reads and no Box access')
    need(result['reads'][0]['hex']==TABLE.to_bytes(4,'little').hex()and result['reads'][1]['hex']==bytes([offset]).hex(),'source exact unaligned table pointer/byte')
    for a,n in ((F.BOX-16,168),(R.TOP-72,56)):
        need(M.read(result['pages'],a,n)==M.read(f['pages'],a,n),'GetSubstruct opaque storage and guards unchanged')
    require_memory_delta(f['pages'],result['pages'],result['stores'])
    result.update(row=row,selector=which,offset=offset,table_read_address=TABLE+4*row+which)
    return result


observation_policy=P.observation_policy


def run(f,policy,observe=True):
    source_identity_guard()
    producer=types.FunctionType(P.run.__code__,{**vars(P),'F':F,'L':L,'R':R,'M':M,'CODE_SPANS':()},argdefs=P.run.__defaults__)
    raw=producer(f,policy,observe);raw['schema']='native-mon-substructure-raw-v1';return raw


def require_run(f,raw):
    predicted=predict(f)
    need(raw.get('schema')=='native-mon-substructure-raw-v1','native GetSubstruct raw schema')
    keys=('executed_count','ARM_count','Thumb_count','unique_executed_starts','callback_count','read_count','store_count','stack_peak','stop_pc')
    need(all(type(raw[k])is int for k in keys),'typed GetSubstruct counters/PC')
    need(wire(raw['initial'])==wire(F.input_record(f)),'complete frozen GetSubstruct input')
    need(wire(raw['backend'])==wire(BACKEND),'qualified GetSubstruct backend')
    need(raw['fault']is None and raw['stopped']is True and raw['stop_pc']==F.RETURN,'native GetSubstruct Thumb return')
    need(raw['models']==raw['runtime_host_writes']==[],'zero GetSubstruct service model/runtime host write')
    need(tuple(raw[k]for k in keys[:-1])==(17,0,17,17,18,6,4,16),'source GetSubstruct counters')
    need(wire(raw['returned'])==wire(predicted['returned']),'source GetSubstruct full16 return ABI')
    need(raw['final_map_sha256']==M.map_digest(predicted['pages']),'source GetSubstruct final map hash')
    need(wire(raw['final_pages'])==wire([dict(ram=a,hex=b.hex())for a,b in sorted(predicted['pages'].items())]),'source GetSubstruct all final pages')
    if raw['observed']is True:
        for key in('flow','reads','stores'):need(wire(raw[key])==wire(predicted[key]),'source GetSubstruct native '+key)
    else:need(raw['observed']is False and raw['flow']==raw['reads']==raw['stores']==[],'GetSubstruct OFF no observation projections')
    return predicted
