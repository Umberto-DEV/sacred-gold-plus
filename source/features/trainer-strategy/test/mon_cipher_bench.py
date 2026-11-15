"""Whole native MonEncryptSegment: source math, precise owners, unchanged CPU loop.

All input bytes are synthetic except authenticated owned-ROM code/pools. Only
fetch/access admission sets reach the CPU producer, never expected responses.
"""
from pathlib import Path
import hashlib
import importlib.util
import struct
import types


def load(path,name):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


F=load(Path(__file__).parents[1]/'tools/congela_mon_cipher.py','whole_cipher_frozen')
A=load(Path(__file__).with_name('arm_thumb_cipher_oracle.py'),'whole_cipher_arithmetic')
P=load(Path(__file__).with_name('fs_memory_narc_bench.py'),'cipher_retained_CPU_loop')
L,R,M,need,wire=F.L,F.R,F.M,F.need,F.M.wire
BACKEND=P.BACKEND
PRODUCER_SHA='87b92017d37bcda4e92deebb12db35bb4d9d448c4aac72911cce49de3b7b2531'
CODE_SPANS=()
CIPHER_SHA={0xfc0:'304084f487616715a01a681ca2380bf2abe1913467b8ba72d03379eb3623dcdb',
            0xfc1:'6d807a7bcfda32aec1d1064084a70cc0a33a72db07b8593433ac32ee1be0c0c5'}


def read_owner(pc,a,n):
    if n==4:
        if pc==0x20725d8:return a==0x20725dc
        if pc==0x201ff78:return a==R.TOP-8
        if pc==0x201ff7a:return a==0x201ff90
        if pc==0x201ff80:return a==0x201ff94
        if pc==0x201ff66:return a in range(R.TOP-40,R.TOP-20,4)
        if pc==0x201ff68:return a==R.TOP-20
    return pc==0x201ff58 and n==2 and a in range(F.BUF,F.BUF+128,2)


def write_owner(pc,a,n):
    if n==4:
        if pc==0x201ff44:return a in range(R.TOP-16,R.TOP,4)
        if pc==0x201ff46:return a in range(R.TOP-40,R.TOP-16,4)
        if pc==0x201ff84:return a==R.TOP-8
    return pc==0x201ff5e and n==2 and a in range(F.BUF,F.BUF+128,2)


def source_math(data,seed):
    need(type(data)is bytes and len(data)==128 and type(seed)is int and seed in F.PROFILES.values(),'finite owned cipher math input')
    out=bytearray();seeds=[]
    for value, in struct.iter_unpack('<H',data):
        seed=(seed*1103515245+24691)&0xffffffff;seeds.append(seed)
        out.extend(struct.pack('<H',value^(seed>>16)))
    return bytes(out),seeds


def require_memory_delta(initial,final,stores):
    need(type(final)is dict and set(final)==set(initial),'cipher exact mapped owners')
    replay={a:bytearray(b)for a,b in initial.items()}
    for x in stores:
        pc,a,n=x['pc'],x['address'],x['bytes']
        need(all(type(v)is int for v in(pc,a,n,x['value']))and write_owner(pc,a,n),'cipher store owner/site')
        need(0<=x['value']<1<<(8*n)and M.read(replay,a,n).hex()==x['before'],'cipher chronological store preimage')
        M.put(replay,a,x['value'].to_bytes(n,'little'))
    need({a:bytes(b)for a,b in replay.items()}==final,'cipher whole-map store replay')
    inverse={a:bytearray(b)for a,b in final.items()}
    for x in reversed(stores):
        need(M.read(inverse,x['address'],x['bytes'])==x['value'].to_bytes(x['bytes'],'little'),'cipher inverse store value')
        M.put(inverse,x['address'],bytes.fromhex(x['before']))
    need({a:bytes(b)for a,b in inverse.items()}==initial,'cipher whole-map inverse replay')


def predict(f):
    seed=f['input_seed'];need(type(seed)is int and seed in F.PROFILES.values(),'finite cipher seed argument')
    parts={name:M.read(f['pages'],item[0],item[1])for name,item in {**L.THUMB,**L.DATA}.items()}
    canonical=F.make_input(parts,seed)
    need(f==canonical,'complete canonical cipher input/pages')
    thumb=L.thumb_code(parts)
    result=A.run(f,(),F.RETURN,cap=4096,thumb_code=thumb,read_guard=read_owner,write_guard=write_owner)
    expected,seeds=source_math(bytes(range(128)),seed)
    need(R.sha(expected)==CIPHER_SHA[seed],'independent fixed cipher digest')
    need((len(result['flow']),len({x['pc']for x in result['flow']}),len(result['reads']),len(result['stores']),result['native_peak'])==(1293,33,263,138,40),'manual cipher forecast')
    need(all(x['regs'][15]&32 for x in result['flow']),'cipher exclusively Thumb')
    expected_regs=list(f['entry_regs']);expected_regs[:4]=[int.from_bytes(expected[-2:],'little'),0x7f7e,seeds[-2],F.RETURN|1]
    expected_regs[14]=0x201ff59;expected_regs[15]=0x6000003f
    need(result['returned']==expected_regs,'source cipher full16 void return ABI')
    updates=[x for x in result['stores']if x['pc']==0x201ff84]
    need([(x['address'],x['bytes'],int.from_bytes(bytes.fromhex(x['before']),'little'),x['value'])for x in updates]==
         [(R.TOP-8,4,before,after)for before,after in zip([seed]+seeds[:-1],seeds)],'source all64 local seed updates')
    payload=[x for x in result['stores']if x['pc']==0x201ff5e]
    need([(x['address'],x['bytes'],x['before'],x['value'])for x in payload]==
         [(F.BUF+2*i,2,bytes(range(128))[2*i:2*i+2].hex(),int.from_bytes(expected[2*i:2*i+2],'little'))for i in range(64)],'source all64 ciphertext writes')
    entries=[x for x in result['flow']if x['pc']==0x201ff78]
    need(len(entries)==64 and all(x['regs'][0]==R.TOP-8 and x['regs'][13]==R.TOP-40 and x['regs'][14]==0x201ff59 for x in entries),'source64 private LCG calls/seedpointer/SP/LR')
    need(M.read(result['pages'],F.BUF,128)==expected and R.u32(M.read(result['pages'],R.TOP-8,4),0)==seeds[-1],'source buffer and seed64')
    for a,n in ((F.BUF-16,16),(F.BUF+128,16),(R.TOP-96,56),(F.GLOBAL,4)):
        need(M.read(result['pages'],a,n)==M.read(f['pages'],a,n),'cipher guards/global sentinel unchanged')
    require_memory_delta(f['pages'],result['pages'],result['stores'])
    result.update(ciphertext_sha256=R.sha(expected),seed63=seeds[-2],seed64=seeds[-1])
    return result


observation_policy=P.observation_policy


def run(f,policy,observe=True):
    need(hashlib.sha256(Path(P.__file__).read_bytes()).hexdigest()==PRODUCER_SHA,'retained cipher CPU producer drift')
    producer=types.FunctionType(P.run.__code__,{**vars(P),'F':F,'L':L,'R':R,'M':M,'CODE_SPANS':()},argdefs=P.run.__defaults__)
    raw=producer(f,policy,observe);raw['schema']='native-mon-cipher-raw-v1';return raw


def require_run(f,raw):
    predicted=predict(f)
    need(raw.get('schema')=='native-mon-cipher-raw-v1','native cipher raw schema')
    keys=('executed_count','ARM_count','Thumb_count','unique_executed_starts','callback_count','read_count','store_count','stack_peak','stop_pc')
    need(all(type(raw[k])is int for k in keys),'typed cipher counters/PC')
    need(wire(raw['initial'])==wire(F.input_record(f)),'complete frozen cipher input')
    need(wire(raw['backend'])==wire(BACKEND),'qualified cipher backend')
    need(raw['fault']is None and raw['stopped']is True and raw['stop_pc']==F.RETURN,'native cipher Thumb return')
    need(raw['models']==raw['runtime_host_writes']==[],'zero cipher service model/runtime host write')
    need(tuple(raw[k]for k in keys[:-1])==(1293,0,1293,33,1294,263,138,40),'source cipher counters')
    need(wire(raw['returned'])==wire(predicted['returned']),'source cipher full16 return ABI')
    need(raw['final_map_sha256']==M.map_digest(predicted['pages']),'source cipher final map hash')
    need(wire(raw['final_pages'])==wire([dict(ram=a,hex=b.hex())for a,b in sorted(predicted['pages'].items())]),'source cipher all final pages')
    if raw['observed']is True:
        for key in('flow','reads','stores'):need(wire(raw[key])==wire(predicted[key]),'source cipher native '+key)
    else:need(raw['observed']is False and raw['flow']==raw['reads']==raw['stores']==[],'cipher OFF no observation projections')
    return predicted
