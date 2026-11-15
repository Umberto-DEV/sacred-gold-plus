"""Full encrypted Box getter: contextual owners and source lifecycle forecasts.

The unchanged producer receives only instruction/access admission sets, never
expected data. The oracle reads native intermediate state; no parent fixture
is widened or normalized to make this composition resemble standalone calls.
"""
from pathlib import Path
import importlib.util
import struct
import types


def load(path,name):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


F=load(Path(__file__).parents[1]/'tools/congela_box_ppup.py','whole_box_frozen')
C=load(Path(__file__).with_name('mon_cipher_bench.py'),'box_retained_producer_and_replay')
A=load(Path(__file__).with_name('arm_thumb_box_oracle.py'),'whole_box_arithmetic')
P=C.P
L,R,M,need,wire=F.L,F.R,F.M,F.need,F.M.wire
BACKEND,PRODUCER_SHA=C.BACKEND,C.PRODUCER_SHA
PARENT_SHA='c2bf2c798a59fab5466fc8776235f1665e88f08aa473ca2ef1ab33af810a17e1'
CODE_SPANS=()


def source_identity_guard():
    need(R.sha(Path(C.__file__).read_bytes())==PARENT_SHA and R.sha(Path(P.__file__).read_bytes())==PRODUCER_SHA,'pinned Box producer/replay drift')
    A.source_identity_guard()


def read_owner(pc,a,n):
    if n==4:
        pools={0x20725d8:0x20725dc,0x20725e0:0x20725e4,0x201ff70:0x201ff74,
               0x201ff7a:0x201ff90,0x201ff80:0x201ff94,0x2072620:0x2072630}
        if pc in pools:return a==pools[pc]
        if pc==0x201ff78:return a==R.TOP-24
        pops={0x201ff66:(R.TOP-56,5),0x201ff68:(R.TOP-36,1),0x2072604:(R.TOP-24,2),
              0x207262c:(R.TOP-64,4),0x206ec3a:(R.TOP-36,5),0x206e69e:(R.TOP-16,4)}
        if pc in pops:
            base,count=pops[pc];return a in range(base,base+4*count,4)
        if pc in(0x206e6ac,0x206e6be,0x206e6cc,0x206e6da):return a==F.BOX
        if pc in(0x206e6b8,0x206e6c6,0x206e6d4):return a==R.TOP-48
        if pc in(0x206e6e2,0x206e97e):return a==R.TOP-44
    if n==2:
        if pc in(0x206e644,0x206e688):return a==F.BOX+4
        if pc in(0x206e650,0x206e666,0x206e690):return a==F.BOX+6
        if pc in(0x201ff58,0x20725f2):return a in range(F.BOX+8,F.BOX+136,2)
        if pc==0x206e6ee:return a==0x206e772
    if n==1:
        if pc==0x206e986:return a==F.BOX+84
        if pc==0x2072626:return a in range(0x20ff733+8,0x20ff733+12)
    return False


def write_owner(pc,a,n):
    if n==4:
        pushes={0x206e640:(R.TOP-16,4),0x206e6a0:(R.TOP-36,5),0x2072608:(R.TOP-64,4),
                0x20725e8:(R.TOP-24,2),0x201ff44:(R.TOP-32,4),0x201ff46:(R.TOP-56,6)}
        if pc in pushes:
            base,count=pushes[pc];return a in range(base,base+4*count,4)
        if pc==0x201ff84:return a==R.TOP-24
        return (pc,a)in((0x206e6a4,R.TOP-44),(0x206e6aa,R.TOP-40),(0x206e6ae,R.TOP-48),(0x206e982,R.TOP-44))
    return n==2 and pc==0x201ff5e and a in range(F.BOX+8,F.BOX+136,2)


require_memory_delta=types.FunctionType(C.require_memory_delta.__code__,{**C.require_memory_delta.__globals__,
    'write_owner':write_owner,'M':M},argdefs=C.require_memory_delta.__defaults__)


def crypt(data,seed):
    out=bytearray();seeds=[]
    for value, in struct.iter_unpack('<H',data):
        seed=(seed*1103515245+24691)&0xffffffff;seeds.append(seed);out.extend(struct.pack('<H',value^(seed>>16)))
    return bytes(out),seeds


def predict(f):
    source_identity_guard();ups=f['input_PPUp']
    parts={name:M.read(f['pages'],item[0],item[1])for name,item in {**L.THUMB,**L.DATA}.items()}
    need(f==F.make_input(parts,ups),'complete canonical encrypted Box input/pages')
    result=A.run(f,(),F.RETURN,cap=4096,thumb_code=L.thumb_code(parts),read_guard=read_owner,write_guard=write_owner)
    need((len(result['flow']),len({x['pc']for x in result['flow']}),len(result['reads']),len(result['stores']),result['native_peak'])==
         (3259,153,642,307,64),'manual full Box getter forecast')
    need(all(x['regs'][15]&32 for x in result['flow']),'Box getter exclusively Thumb')
    box,plain=F.owned_box(ups);cipher,seeds=crypt(plain,0x2ab)
    need(cipher==box[8:]and crypt(cipher,0x2ab)[0]==plain,'source independent XOR lifecycle')
    expected=list(f['entry_regs']);expected[:4]=[ups,0,seeds[-2],0x206e69d];expected[14]=0x201ff59;expected[15]=0x3f
    need(result['returned']==expected,'source full Box getter full16 return')
    frame=[0,F.BOX+8,0x201ff45,ups,F.BOX,0,f['entry_regs'][7],0x206e69d,
           F.BOX+8,128,seeds[-1],0x201ff45,*f['entry_regs'][4:7],f['entry_regs'][14]]
    need(M.read(result['pages'],R.TOP-64,64)==struct.pack('<16I',*frame),'source final overlapping64byte stack lifetimes')
    need(M.read(result['pages'],F.BOX,136)==box,'whole Box136 restored exactly')
    for a,n in((F.BOX-16,16),(F.BOX+136,16),(R.TOP-120,56)):
        need(M.read(result['pages'],a,n)==M.read(f['pages'],a,n),'Box getter guards preserved')
    updates=[x for x in result['stores']if x['pc']==0x201ff84]
    one=[(R.TOP-24,4,before,after)for before,after in zip([0x2ab]+seeds[:-1],seeds)]
    need([(x['address'],x['bytes'],int.from_bytes(bytes.fromhex(x['before']),'little'),x['value'])for x in updates]==one+one,
         'source two independently restarted64seed updates')
    payload=[x for x in result['stores']if x['pc']==0x201ff5e]
    phase=lambda before,after:[(F.BOX+8+2*i,2,before[2*i:2*i+2].hex(),int.from_bytes(after[2*i:2*i+2],'little'))for i in range(64)]
    need([(x['address'],x['bytes'],x['before'],x['value'])for x in payload]==phase(cipher,plain)+phase(plain,cipher),
         'source all128 transient payload writes')
    checksum=[x for x in result['reads']if x['pc']==0x20725f2]
    need([(x['address'],x['hex'])for x in checksum]==[(F.BOX+8+2*i,plain[2*i:2*i+2].hex())for i in range(64)],'source native checksum reads decrypted payload')
    accum=[];s=0
    for value, in struct.iter_unpack('<H',plain):s=(s+value)&65535;accum.append(s)
    need([x['regs'][3]for x in result['flow']if x['pc']==0x20725fe]==accum and s==0x2ab,'source every checksum narrowing')
    sub=[x['regs']for x in result['flow']if x['pc']==0x2072608]
    need(len(sub)==4 and[subrow[:3]for subrow in sub]==[[F.BOX,0x4000,i]for i in range(4)],'source actual headerPID four selectors')
    fields=[x['regs']for x in result['flow']if x['pc']==0x206e986]
    need(len(fields)==1 and fields[0][:8]==[F.BOX+72,F.BOX+104,3,0x206e65d,0,F.BOX+8,F.BOX+72,F.BOX+40]
         and fields[0][13:]==[R.TOP-48,0x206e6e1,0x3f],'source exact field-load context')
    need([x for x in result['reads']if x['pc']==0x206e986]==[dict(pc=0x206e986,address=F.BOX+84,bytes=1,hex=bytes([ups]).hex())],
         'source PP-Up byte access distinct from currentPP')
    normalize=[x for x in result['stores']if x['pc']==0x206e982]
    need(normalize==[dict(pc=0x206e982,address=R.TOP-44,bytes=4,before='3e000000',value=0)],'source transient normalized attribute writer')
    require_memory_delta(f['pages'],result['pages'],result['stores'])
    result.update(PPUp=ups,checksum=s,seed63=seeds[-2],seed64=seeds[-1],plaintext_sha256=R.sha(plain))
    return result


observation_policy=P.observation_policy


def run(f,policy,observe=True):
    source_identity_guard()
    producer=types.FunctionType(P.run.__code__,{**P.run.__globals__,'F':F,'L':L,'R':R,'M':M,'CODE_SPANS':()},argdefs=P.run.__defaults__)
    raw=producer(f,policy,observe);raw['schema']='native-box-ppup-raw-v1';return raw


def require_run(f,raw):
    predicted=predict(f);need(raw.get('schema')=='native-box-ppup-raw-v1','native Box raw schema')
    keys=('executed_count','ARM_count','Thumb_count','unique_executed_starts','callback_count','read_count','store_count','stack_peak','stop_pc')
    need(all(type(raw[k])is int for k in keys),'typed Box counters/PC')
    need(wire(raw['initial'])==wire(F.input_record(f)),'complete frozen Box input')
    need(wire(raw['backend'])==wire(BACKEND),'qualified Box backend')
    need(raw['fault']is None and raw['stopped']is True and raw['stop_pc']==F.RETURN,'native Box Thumb return')
    need(raw['models']==raw['runtime_host_writes']==[],'zero Box model/runtime host write')
    need(tuple(raw[k]for k in keys[:-1])==(3259,0,3259,153,3260,642,307,64),'source Box counters')
    need(wire(raw['returned'])==wire(predicted['returned']),'source Box full16 return')
    need(raw['final_map_sha256']==M.map_digest(predicted['pages']),'source Box final map hash')
    need(wire(raw['final_pages'])==wire([dict(ram=a,hex=b.hex())for a,b in sorted(predicted['pages'].items())]),'source Box all final pages')
    if raw['observed']is True:
        for k in('flow','reads','stores'):need(wire(raw[k])==wire(predicted[k]),'source Box native '+k)
    else:need(raw['observed']is False and raw['flow']==raw['reads']==raw['stores']==[],'Box OFF no observation projections')
    return predicted
