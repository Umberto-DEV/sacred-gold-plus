"""Whole native checksum, no new ISA, with owned odd/zero/overflow inputs."""
from pathlib import Path
import importlib.util
import types


def load(path,name):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


F=load(Path(__file__).parents[1]/'tools/congela_mon_checksum.py','whole_checksum_frozen')
C=load(Path(__file__).with_name('mon_cipher_bench.py'),'checksum_retained_producer_and_replay')
A,P=C.A,C.P
L,R,M,need,wire=F.L,F.R,F.M,F.need,F.M.wire
BACKEND,PRODUCER_SHA=C.BACKEND,C.PRODUCER_SHA
PARENT_SHA='c2bf2c798a59fab5466fc8776235f1665e88f08aa473ca2ef1ab33af810a17e1'
FRONTEND_SHA='d423e27c188173e8729a5ce56050d9574d0bf8a2f4155c60b19d43f46bcbc8c3'
CODE_SPANS=()


def source_identity_guard():
    need(R.sha(Path(C.__file__).read_bytes())==PARENT_SHA and R.sha(Path(A.__file__).read_bytes())==FRONTEND_SHA and
         R.sha(Path(P.__file__).read_bytes())==PRODUCER_SHA,'pinned checksum parent drift')
    A.source_identity_guard()


def read_owner(pc,a,n,*,halfwords=64):
    if pc==0x2072604 and n==4:return a in(R.TOP-8,R.TOP-4)
    return type(halfwords)is int and halfwords in(0,64)and pc==0x20725f2 and n==2 and a in range(F.BUF,F.BUF+2*halfwords,2)


def write_owner(pc,a,n):return pc==0x20725e8 and n==4 and a in(R.TOP-8,R.TOP-4)


require_memory_delta=types.FunctionType(C.require_memory_delta.__code__,{**vars(C),'write_owner':write_owner,'M':M},argdefs=C.require_memory_delta.__defaults__)


def source_math(data,size):
    need(type(data)is bytes and len(data)==129 and type(size)is int and size in(0,128,129),'finite owned checksum math input')
    return sum(int.from_bytes(data[i:i+2],'little')for i in range(0,2*(size//2),2))&65535


def predict(f):
    source_identity_guard()
    size,overflow=f['input_size'],f['overflow_input']
    parts={name:M.read(f['pages'],a,n)for name,(a,n,count,digest)in L.THUMB.items()}
    need(f==F.make_input(parts,size,overflow),'complete canonical checksum input/pages')
    thumb=L.thumb_code(parts);N=size//2;storage=M.read(f['pages'],F.BUF,129)
    result=A.run(f,(),F.RETURN,cap=1024,thumb_code=thumb,
        read_guard=lambda pc,a,n:read_owner(pc,a,n,halfwords=N),write_guard=write_owner)
    checksum=source_math(storage,size);count=8+8*N;unique=16 if N else 8
    need((len(result['flow']),len({x['pc']for x in result['flow']}),len(result['reads']),len(result['stores']),result['native_peak'])==
         (count,unique,N+2,2,8),'manual checksum forecast')
    need(all(x['regs'][15]&32 for x in result['flow']),'checksum exclusively Thumb')
    expected=list(f['entry_regs']);expected[:3]=[checksum,(checksum<<16)if N else size,N];expected[15]=0x3f if checksum else 0x4000003f
    need(result['returned']==expected,'source checksum full16 u32 return ABI')
    need([(x['pc'],x['address'],x['bytes'],x['value'])for x in result['stores']]==
         [(0x20725e8,R.TOP-8,4,f['entry_regs'][3]),(0x20725e8,R.TOP-4,4,f['entry_regs'][4])],'source two checksum saved words')
    payload=[x for x in result['reads']if x['pc']==0x20725f2]
    need([(x['address'],x['bytes'],x['hex'])for x in payload]==[(F.BUF+2*i,2,storage[2*i:2*i+2].hex())for i in range(N)],'source checksum ordered halfword reads/no tail')
    accum=[];value=0
    for i in range(N):value=(value+int.from_bytes(storage[2*i:2*i+2],'little'))&65535;accum.append(value)
    need([x['regs'][3]for x in result['flow']if x['pc']==0x20725fe]==accum,'source native per-iteration16bit truncation')
    for a,n in ((F.BUF-16,161),(R.TOP-64,56)):
        need(M.read(result['pages'],a,n)==M.read(f['pages'],a,n),'checksum input and guards unchanged')
    require_memory_delta(f['pages'],result['pages'],result['stores'])
    result.update(checksum=checksum,halfwords=N)
    return result


observation_policy=P.observation_policy


def run(f,policy,observe=True):
    source_identity_guard()
    producer=types.FunctionType(P.run.__code__,{**vars(P),'F':F,'L':L,'R':R,'M':M,'CODE_SPANS':()},argdefs=P.run.__defaults__)
    raw=producer(f,policy,observe);raw['schema']='native-mon-checksum-raw-v1';return raw


def require_run(f,raw):
    predicted=predict(f)
    need(raw.get('schema')=='native-mon-checksum-raw-v1','native checksum raw schema')
    keys=('executed_count','ARM_count','Thumb_count','unique_executed_starts','callback_count','read_count','store_count','stack_peak','stop_pc')
    need(all(type(raw[k])is int for k in keys),'typed checksum counters/PC')
    need(wire(raw['initial'])==wire(F.input_record(f)),'complete frozen checksum input')
    need(wire(raw['backend'])==wire(BACKEND),'qualified checksum backend')
    need(raw['fault']is None and raw['stopped']is True and raw['stop_pc']==F.RETURN,'native checksum Thumb return')
    need(raw['models']==raw['runtime_host_writes']==[],'zero checksum service model/runtime host write')
    N=predicted['halfwords'];count=8+8*N
    need(tuple(raw[k]for k in keys[:-1])==(count,0,count,16 if N else 8,count+1,N+2,2,8),'source checksum counters')
    need(wire(raw['returned'])==wire(predicted['returned']),'source checksum full16 return ABI')
    need(raw['final_map_sha256']==M.map_digest(predicted['pages']),'source checksum final map hash')
    need(wire(raw['final_pages'])==wire([dict(ram=a,hex=b.hex())for a,b in sorted(predicted['pages'].items())]),'source checksum all final pages')
    if raw['observed']is True:
        for key in('flow','reads','stores'):need(wire(raw[key])==wire(predicted[key]),'source checksum native '+key)
    else:need(raw['observed']is False and raw['flow']==raw['reads']==raw['stores']==[],'checksum OFF no observation projections')
    return predicted
