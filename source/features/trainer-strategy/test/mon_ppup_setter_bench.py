"""Finite full Mon62 transaction: party100/PID, Box128/checksum, direct leaf.

Source-led forecast and access owners precede the uninterrupted retained CPU.
No phase bridge, host cipher, service model or page reset occurs during CPU.
"""
from pathlib import Path
import importlib.util
import struct
import types


def load(path,name):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


F=load(Path(__file__).parents[1]/'tools/congela_mon_ppup_setter.py','whole_Mon_frozen')
G=load(Path(__file__).with_name('box_ppup_bench.py'),'Mon_retained_cipher_arithmetic')
A=F.Q.A
P=F.Q.C
L,R,M,need,wire=F.L,F.R,F.M,F.need,F.M.wire
BACKEND,PRODUCER_SHA=G.BACKEND,G.PRODUCER_SHA
CODE_SPANS=()
crypt=G.crypt


def source_identity_guard():
    need(R.sha(Path(P.__file__).read_bytes())==PRODUCER_SHA,'retained Mon8192 producer identity')
    A.source_identity_guard()


def read_owner(pc,a,n):
    if n==4:
        pools={0x20725d8:0x20725dc,0x20725e0:0x20725e4,0x201ff70:0x201ff74,
               0x201ff7a:0x201ff90,0x201ff80:0x201ff94,0x2072620:0x2072630}
        if pc in pools:return a==pools[pc]
        if pc==0x201ff78:return a==R.TOP-24
        pops={0x201ff66:(R.TOP-56,5),0x201ff68:(R.TOP-36,1),0x2072604:(R.TOP-24,2),
              0x207262c:(R.TOP-144,4),0x206f112:(R.TOP-48,6),0x206ed6e:(R.TOP-24,2),0x206eccc:(R.TOP-16,4)}
        if pc in pops:
            base,count=pops[pc];return a in range(base,base+4*count,4)
        if pc in(0x206ec52,0x206ecaa,0x206edf2,0x206ee04,0x206ee12,0x206ee20):return a==F.BOX
        if pc in(0x206edfe,0x206ee0c,0x206ee1a):return a==R.TOP-128
        if pc in(0x206ee28,0x206f104):return a==R.TOP-124
    if n==2:
        if pc in(0x206ec44,0x206eca0):return a==F.BOX+4
        if pc in(0x206ec5e,0x206ec72,0x206ecc2):return a==F.BOX+6
        if pc==0x201ff58:return a in range(F.BOX+8,F.BOX+236,2)
        if pc==0x20725f2:return a in range(F.BOX+8,F.BOX+136,2)
        if pc==0x206ee34:return a==0x206eeb8
    if n==1:
        if pc==0x206f106:return a==F.VALUE
        if pc==0x2072626:return a in range(0x20ff73b,0x20ff73f)
    return False


def write_owner(pc,a,n):
    if n==4:
        pushes={0x206ec40:(R.TOP-16,4),0x206ecd0:(R.TOP-24,2),0x206ede8:(R.TOP-48,6),
                0x2072608:(R.TOP-144,4),0x20725e8:(R.TOP-24,2),0x201ff44:(R.TOP-32,4),0x201ff46:(R.TOP-56,6)}
        if pc in pushes:
            base,count=pushes[pc];return a in range(base,base+4*count,4)
        if pc==0x201ff84:return a==R.TOP-24
        return(pc,a)in((0x206edec,R.TOP-124),(0x206edf4,R.TOP-128),(0x206ee18,R.TOP-120),(0x206f10a,R.TOP-124))
    if n==2:
        if pc==0x206ecbe:return a==F.BOX+6
        return pc==0x201ff5e and a in range(F.BOX+8,F.BOX+236,2)
    return n==1 and pc==0x206f10e and a==F.BOX+84


require_memory_delta=types.FunctionType(G.require_memory_delta.__code__,{**G.require_memory_delta.__globals__,
    'write_owner':write_owner,'M':M},argdefs=G.require_memory_delta.__defaults__)


def source_result(ups):
    initial,plain,party=F.owned_mon(ups);final,updated,_=F.owned_mon(0)
    need(plain[:76]+b'\0'+plain[77:]==updated,'source only PP-Up changes in Box plaintext')
    need(final[136:]==initial[136:]and int.from_bytes(final[6:8],'little')==0x2a8,'source final party roundtrip/new Box key')
    return initial,plain,party,final,updated


def predict(f):
    source_identity_guard();ups=f['input_Up']
    parts={name:M.read(f['pages'],item[0],item[1])for name,item in{**L.THUMB,**L.DATA}.items()}
    need(f==F.make_input(parts,ups),'complete canonical Mon input/pages')
    result=A.run(f,(),F.RETURN,cap=8192,thumb_code=L.thumb_code(parts),read_guard=read_owner,write_guard=write_owner)
    need((len(result['flow']),len({x['pc']for x in result['flow']}),len(result['reads']),len(result['stores']),result['native_peak'])==
         (5827,173,1128,534,144),'manual Mon62 complete forecast')
    need(all(x['regs'][15]&32 for x in result['flow']),'Mon62 exclusively Thumb')
    initial,plain,party,final,updated=source_result(ups)
    expected=list(f['entry_regs']);expected[:4]=[0x2b9b,0,0x4aa02329,0x206eccd];expected[14]=0x201ff59;expected[15]=0x6000003f
    need(result['returned']==expected,'source Mon full16 void return')
    need(M.read(result['pages'],F.BOX,236)==final,'source Mon complete236 output')
    for a,n in((F.BOX-16,16),(F.BOX+236,16),(F.VALUE-16,36),(R.TOP-F.FRAME-F.GUARD,F.GUARD)):
        need(M.read(result['pages'],a,n)==M.read(f['pages'],a,n),'source Mon Value/guards preserved')
    phases=((F.BOX+136,initial[136:],party,0x4000),(F.BOX+8,initial[8:136],plain,0x2a8+ups),
            (F.BOX+136,party,final[136:],0x4000),(F.BOX+8,updated,final[8:136],0x2a8))
    expected_seeds=[];expected_payload=[]
    for base,before,after,key in phases:
        calculated,seeds=crypt(before,key);need(calculated==after,'independent complete cipher phase')
        expected_seeds.extend((R.TOP-24,4,old,new)for old,new in zip([key]+seeds[:-1],seeds))
        expected_payload.extend((base+i,2,before[i:i+2].hex(),int.from_bytes(after[i:i+2],'little'))for i in range(0,len(before),2))
    seedstores=[x for x in result['stores']if x['pc']==0x201ff84]
    need([(x['address'],x['bytes'],int.from_bytes(bytes.fromhex(x['before']),'little'),x['value'])for x in seedstores]==expected_seeds,'source four local-seed phases PID/old/PID/new')
    payload=[x for x in result['stores']if x['pc']==0x201ff5e]
    need([(x['address'],x['bytes'],x['before'],x['value'])for x in payload]==expected_payload,'source four complete cipher preimages and stores')
    # All transient plaintext is checked; final ciphertext equality alone
    # also accepts skipping both party phases or using a wrong key twice.
    checks=[x for x in result['reads']if x['pc']==0x20725f2]
    need([(x['address'],x['hex'])for x in checks]==[(F.BOX+8+i,data[i:i+2].hex())for data in(plain,updated)for i in range(0,128,2)],'source both checksum plaintext reads')
    accum=[]
    for data in(plain,updated):
        total=0
        for item, in struct.iter_unpack('<H',data):total=(total+item)&65535;accum.append(total)
    need([x['regs'][3]for x in result['flow']if x['pc']==0x20725fe]==accum,'source two u16 checksum accumulators')
    need([x for x in result['stores']if x['pc']==0x206f10e]==[dict(pc=0x206f10e,address=F.BOX+84,bytes=1,before=bytes([ups]).hex(),value=0)],'source exact PP-Up byte store')
    need([x for x in result['stores']if x['pc']==0x206ecbe]==[dict(pc=0x206ecbe,address=F.BOX+6,bytes=2,before=struct.pack('<H',0x2a8+ups).hex(),value=0x2a8)],'source native checksum header store')
    need([x for x in result['reads']if x['pc']==0x206f106]==[dict(pc=0x206f106,address=F.VALUE,bytes=1,hex='00')],'source Valueword read low byte only')
    need([x['hex']for x in result['reads']if x['pc']==0x206ecc2]==['a802'],'source updated header reload')
    sub=[x['regs'][:3]for x in result['flow']if x['pc']==0x2072608]
    need(sub==[[F.BOX,0x4000,i]for i in range(4)],'source real PID and four selectors')
    field=next(x['regs']for x in result['flow']if x['pc']==0x206f10e)
    need(field[:3]==[F.BOX+72,0,3]and field[4:8]==[F.VALUE,F.BOX+72,F.BOX+104,F.BOX+8]and field[13:]==[R.TOP-128,0x206ee27,0x3f],'source leaf62 field/SP/LR/flags')
    calls=[x for x in result['flow']if x['pc']in(0x20725d8,0x20725e0)]
    need([(x['pc'],x['regs'][:3],x['regs'][13],x['regs'][14])for x in calls]==[
        (0x20725e0,[F.BOX+136,100,0x4000],R.TOP-16,0x206ec5d),
        (0x20725e0,[F.BOX+8,128,0x2a8+ups],R.TOP-16,0x206ec69),
        (0x20725d8,[F.BOX+136,100,0x4000],R.TOP-16,0x206ecb5),
        (0x20725d8,[F.BOX+8,128,0x2a8],R.TOP-16,0x206eccd)],'source real four wrapper calls/ABI/lifetime')
    require_memory_delta(f['pages'],result['pages'],result['stores'])
    result.update(checksum=0x2a8,output_Mon_sha256=R.sha(final),party_plaintext_sha256=R.sha(party),
        final_frame_sha256=R.sha(M.read(result['pages'],R.TOP-F.FRAME,F.FRAME)))
    return result


observation_policy=P.observation_policy


def run(f,policy,observe=True):
    source_identity_guard()
    producer=types.FunctionType(P.run.__code__,{**P.run.__globals__,'F':F,'L':L,'R':R,'M':M,'CODE_SPANS':()},argdefs=P.run.__defaults__)
    raw=producer(f,policy,observe);raw['schema']='native-Mon-PPUp-setter-raw-v1';return raw


def require_run(f,raw):
    predicted=predict(f);need(raw.get('schema')=='native-Mon-PPUp-setter-raw-v1','native Mon raw schema')
    keys=('executed_count','ARM_count','Thumb_count','unique_executed_starts','callback_count','read_count','store_count','stack_peak','stop_pc')
    need(all(type(raw[k])is int for k in keys),'typed Mon counters/PC')
    need(wire(raw['initial'])==wire(F.input_record(f)),'complete frozen Mon input')
    need(wire(raw['backend'])==wire(BACKEND),'qualified Mon backend')
    need(raw['fault']is None and raw['stopped']is True and raw['stop_pc']==F.RETURN,'native Mon Thumb return')
    need(raw['models']==raw['runtime_host_writes']==[],'zero Mon model/runtime host write')
    need(tuple(raw[k]for k in keys[:-1])==(5827,0,5827,173,5828,1128,534,144),'source Mon counters')
    need(wire(raw['returned'])==wire(predicted['returned']),'source Mon full16 void return')
    need(raw['final_map_sha256']==M.map_digest(predicted['pages']),'source Mon final map hash')
    need(wire(raw['final_pages'])==wire([dict(ram=a,hex=b.hex())for a,b in sorted(predicted['pages'].items())]),'source Mon all final pages')
    if raw['observed']is True:
        for key in('flow','reads','stores'):need(wire(raw[key])==wire(predicted[key]),'source Mon native '+key)
    else:need(raw['observed']is False and raw['flow']==raw['reads']==raw['stores']==[],'Mon OFF no observation projections')
    return predicted
