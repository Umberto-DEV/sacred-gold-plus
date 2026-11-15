"""Complete native Box PP write, two checksums and a new encryption key.

This context retains the qualified producer and arithmetic. It neither widens
the earlier getter fixtures nor substitutes its expected PP/key into the CPU.
"""
from pathlib import Path
import importlib.util
import struct
import types


def load(path,name):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


F=load(Path(__file__).parents[1]/'tools/congela_box_pp_setter.py','whole_setter_frozen')
G=load(Path(__file__).with_name('box_ppup_bench.py'),'setter_retained_Box_primitives')
A=load(Path(__file__).with_name('arm_thumb_box_setter_oracle.py'),'whole_setter_arithmetic')
P=G.P
L,R,M,need,wire=F.L,F.R,F.M,F.need,F.M.wire
BACKEND,PRODUCER_SHA=G.BACKEND,G.PRODUCER_SHA
PARENT_SHA='b7017b3127aea073cf3aae7439ad5551ba54a63a538ed4378af165e8888e48f2'
CODE_SPANS=()


def source_identity_guard():
    need(R.sha(Path(G.__file__).read_bytes())==PARENT_SHA and R.sha(Path(P.__file__).read_bytes())==PRODUCER_SHA,'pinned setter producer/primitives drift')
    A.source_identity_guard()


def read_owner(pc,a,n):
    if n==4:
        pools={0x20725d8:0x20725dc,0x20725e0:0x20725e4,0x201ff70:0x201ff74,
               0x201ff7a:0x201ff90,0x201ff80:0x201ff94,0x2072620:0x2072630}
        if pc in pools:return a==pools[pc]
        if pc==0x201ff78:return a==R.TOP-24
        pops={0x201ff66:(R.TOP-56,5),0x201ff68:(R.TOP-36,1),0x2072604:(R.TOP-24,2),
              0x207262c:(R.TOP-136,4),0x206f102:(R.TOP-40,6),0x206ede4:(R.TOP-16,4)}
        if pc in pops:
            base,count=pops[pc];return a in range(base,base+4*count,4)
        if pc in(0x206edf2,0x206ee04,0x206ee12,0x206ee20):return a==F.BOX
        if pc in(0x206edfe,0x206ee0c,0x206ee1a):return a==R.TOP-120
        if pc in(0x206ee28,0x206f0f4):return a==R.TOP-116
    if n==2:
        if pc in(0x206ed74,0x206edc4):return a==F.BOX+4
        if pc in(0x206ed80,0x206ed96,0x206edda):return a==F.BOX+6
        if pc in(0x201ff58,0x20725f2):return a in range(F.BOX+8,F.BOX+136,2)
        if pc==0x206ee34:return a==0x206eeb0
    if n==1:
        if pc==0x206f0f6:return a==F.VALUE
        if pc==0x2072626:return a in range(0x20ff73b,0x20ff73f)
    return False


def write_owner(pc,a,n):
    if n==4:
        pushes={0x206ed70:(R.TOP-16,4),0x206ede8:(R.TOP-40,6),0x2072608:(R.TOP-136,4),
                0x20725e8:(R.TOP-24,2),0x201ff44:(R.TOP-32,4),0x201ff46:(R.TOP-56,6)}
        if pc in pushes:
            base,count=pushes[pc];return a in range(base,base+4*count,4)
        if pc==0x201ff84:return a==R.TOP-24
        return (pc,a)in((0x206edec,R.TOP-116),(0x206edf4,R.TOP-120),(0x206ee18,R.TOP-112),(0x206f0fa,R.TOP-116))
    if n==2:
        if pc==0x206edd6:return a==F.BOX+6
        return pc==0x201ff5e and a in range(F.BOX+8,F.BOX+136,2)
    return n==1 and pc==0x206f0fe and a==F.BOX+80


require_memory_delta=types.FunctionType(G.require_memory_delta.__code__,{**G.require_memory_delta.__globals__,
    'write_owner':write_owner,'M':M},argdefs=G.require_memory_delta.__defaults__)
crypt=G.crypt


def source_result(value):
    need(type(value)is int and value in(23,24),'finite setter source Value')
    initial,plain=F.G.owned_box(3);updated=bytearray(plain);updated[72]=value;updated=bytes(updated)
    checksum=sum(x[0]for x in struct.iter_unpack('<H',updated))&65535
    cipher,seeds=crypt(updated,checksum);box=initial[:6]+struct.pack('<H',checksum)+cipher
    expected={24:'401b0fa15982184e6650413627b5d3540372253de0664aed7ed928d845bc9c6b',
              23:'8cc5a0fe1b2e992e59ae979d2886d1600d00e526d3fd10f33f1044a8665b321b'}
    need(R.sha(box)==expected[value]and checksum==0x29c+value,'independent setter final Box digest/checksum')
    return initial,plain,box,updated,checksum,seeds


def predict(f):
    source_identity_guard();value=f['input_PP']
    parts={name:M.read(f['pages'],item[0],item[1])for name,item in {**L.THUMB,**L.DATA}.items()}
    need(f==F.make_input(parts,value),'complete canonical setter input/pages')
    result=A.run(f,(),F.RETURN,cap=4096,thumb_code=L.thumb_code(parts),read_guard=read_owner,write_guard=write_owner)
    need((len(result['flow']),len({x['pc']for x in result['flow']}),len(result['reads']),len(result['stores']),result['native_peak'])==
         (3780,154,709,312,136),'manual complete Box setter forecast')
    need(all(x['regs'][15]&32 for x in result['flow']),'setter exclusively Thumb')
    initial,plain,final,updated,checksum,seeds=source_result(value);_,oldseeds=crypt(plain,0x2ab)
    expected=list(f['entry_regs']);expected[:4]=[seeds[-1]>>16,0,seeds[-2],0x206ede5]
    expected[14]=0x201ff59;expected[15]=0x6000003f
    need(result['returned']==expected,'source setter full16 void return')
    frame=[F.VALUE,F.BOX+72,F.VALUE,0x206ee27,F.BOX,0,F.BOX+40]+[0xa5a5a5a5]*13+[
           0x201ff45,58,F.BOX,F.VALUE,f['entry_regs'][7],0x206ede5,F.BOX+8,128,seeds[-1],0x201ff45,
           *f['entry_regs'][4:7],f['entry_regs'][14]]
    need(len(frame)==34 and M.read(result['pages'],R.TOP-136,136)==struct.pack('<34I',*frame),
         'source setter final136byte overlapping frame')
    need(M.read(result['pages'],F.BOX,136)==final,'source whole setter output Box')
    for a,n in((F.BOX-16,16),(F.BOX+136,16),(F.VALUE-16,33),(R.TOP-192,56)):
        need(M.read(result['pages'],a,n)==M.read(f['pages'],a,n),'setter input Value/guards preserved')
    def seed_updates(key,seq):return[(R.TOP-24,4,before,after)for before,after in zip([key]+seq[:-1],seq)]
    updates=[x for x in result['stores']if x['pc']==0x201ff84]
    need([(x['address'],x['bytes'],int.from_bytes(bytes.fromhex(x['before']),'little'),x['value'])for x in updates]==
         seed_updates(0x2ab,oldseeds)+seed_updates(checksum,seeds),'source setter old decrypt/new encrypt keys')
    payload=[x for x in result['stores']if x['pc']==0x201ff5e]
    def phase(before,after):return[(F.BOX+8+2*i,2,before[2*i:2*i+2].hex(),int.from_bytes(after[2*i:2*i+2],'little'))for i in range(64)]
    need([(x['address'],x['bytes'],x['before'],x['value'])for x in payload]==phase(initial[8:],plain)+phase(updated,final[8:]),
         'source setter128 decrypt/encrypt payload writes')
    pp=[x for x in result['stores']if x['pc']==0x206f0fe]
    need(pp==[dict(pc=0x206f0fe,address=F.BOX+80,bytes=1,before='0f',value=value)],'source exact single PP byte write')
    header=[x for x in result['stores']if x['pc']==0x206edd6]
    need(header==[dict(pc=0x206edd6,address=F.BOX+6,bytes=2,before='ab02',value=checksum)],'source native checksum header write')
    checks=[x for x in result['reads']if x['pc']==0x20725f2]
    expected_checks=[(F.BOX+8+2*i,data[2*i:2*i+2].hex())for data in(plain,updated)for i in range(64)]
    need([(x['address'],x['hex'])for x in checks]==expected_checks,'source two native checksum plaintext reads')
    accum=[]
    for data in(plain,updated):
        total=0
        for item, in struct.iter_unpack('<H',data):total=(total+item)&65535;accum.append(total)
    need([x['regs'][3]for x in result['flow']if x['pc']==0x20725fe]==accum,'source two native u16 checksum accumulators')
    field=[x['regs']for x in result['flow']if x['pc']==0x206f0fe]
    need(len(field)==1 and field[0][:8]==[F.BOX+72,value,3,0x206ed8d,F.VALUE,F.BOX+72,F.BOX+104,F.BOX+8]
         and field[0][13:]==[R.TOP-120,0x206ee27,0x3f],'source PP store full context')
    sub=[x['regs'][:3]for x in result['flow']if x['pc']==0x2072608]
    need(sub==[[F.BOX,0x4000,i]for i in range(4)],'source setter actual headerPID selectors')
    need([x for x in result['reads']if x['pc']==0x206f0f6]==[dict(pc=0x206f0f6,address=F.VALUE,bytes=1,hex=bytes([value]).hex())],
         'source actual separate Value byte read')
    need([x['hex']for x in result['reads']if x['pc']==0x206edda]==[struct.pack('<H',checksum).hex()],
         'source encryption key reloaded from updated header')
    require_memory_delta(f['pages'],result['pages'],result['stores'])
    result.update(PP=value,checksum=checksum,seed63=seeds[-2],seed64=seeds[-1],output_Box_sha256=R.sha(final))
    return result


observation_policy=P.observation_policy


def run(f,policy,observe=True):
    source_identity_guard()
    producer=types.FunctionType(P.run.__code__,{**P.run.__globals__,'F':F,'L':L,'R':R,'M':M,'CODE_SPANS':()},argdefs=P.run.__defaults__)
    raw=producer(f,policy,observe);raw['schema']='native-box-pp-setter-raw-v1';return raw


def require_run(f,raw):
    predicted=predict(f);need(raw.get('schema')=='native-box-pp-setter-raw-v1','native setter raw schema')
    keys=('executed_count','ARM_count','Thumb_count','unique_executed_starts','callback_count','read_count','store_count','stack_peak','stop_pc')
    need(all(type(raw[k])is int for k in keys),'typed setter counters/PC')
    need(wire(raw['initial'])==wire(F.input_record(f)),'complete frozen setter input')
    need(wire(raw['backend'])==wire(BACKEND),'qualified setter backend')
    need(raw['fault']is None and raw['stopped']is True and raw['stop_pc']==F.RETURN,'native setter Thumb return')
    need(raw['models']==raw['runtime_host_writes']==[],'zero setter model/runtime host write')
    need(tuple(raw[k]for k in keys[:-1])==(3780,0,3780,154,3781,709,312,136),'source setter counters')
    need(wire(raw['returned'])==wire(predicted['returned']),'source setter full16 void return')
    need(raw['final_map_sha256']==M.map_digest(predicted['pages']),'source setter final map hash')
    need(wire(raw['final_pages'])==wire([dict(ram=a,hex=b.hex())for a,b in sorted(predicted['pages'].items())]),'source setter all final pages')
    if raw['observed']is True:
        for key in('flow','reads','stores'):need(wire(raw[key])==wire(predicted[key]),'source setter native '+key)
    else:need(raw['observed']is False and raw['flow']==raw['reads']==raw['stores']==[],'setter OFF no observation projections')
    return predicted
