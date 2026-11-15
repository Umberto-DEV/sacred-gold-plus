#!/usr/bin/env python3
"""Qualify an owned 100-byte cipher loop; no ROM instructions or data.

Four bounded CPU17 runs compare an independent scalar full-state forecast,
the retained Thumb interpreter and the retained uninterrupted producer. This
qualifies the 50-halfword loop geometry, not a DS timing or save-file claim.
"""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import struct
import types


def load(path,name):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


HERE=Path(__file__).resolve();SOURCE=HERE.parents[3]
A=load(HERE.parents[1]/'test/arm_thumb_box_move_oracle.py','party100_retained_Thumb')
C=load(HERE.parents[1]/'test/fs_memory_narc_bench.py','party100_retained_producer')
M,need=C.M,C.need
BUFFER=0x3020
ENTRY,RETURN=0x1000,0x1100
WORDS=(0x435a,0x1912,0x0c17,0x8801,0x4079,0x8001,0x3002,0x42b0,0xd1f6,0x4770)
PRODUCER_SHA='87b92017d37bcda4e92deebb12db35bb4d9d448c4aac72911cce49de3b7b2531'


def owned_plaintext():
    """New project-owned bytes, not an extracted/legalized party/save record."""
    return bytes((0x73+29*i+(i*i)//3)&255 for i in range(100))


def crypt100(payload,key):
    need(type(payload)is bytes and len(payload)==100,'owned party payload exactly100 bytes')
    need(type(key)is int and 0<=key<2**32,'owned party unsigned32 seed')
    out=bytearray();seeds=[]
    for i in range(0,100,2):
        key=(1103515245*key+24691)&0xffffffff;seeds.append(key)
        out.extend((int.from_bytes(payload[i:i+2],'little')^(key>>16)).to_bytes(2,'little'))
    return bytes(out),seeds


def kernel(payload,key):
    crypt100(payload,key)  # type/extent contract; no instruction prediction
    pages={a:bytearray(b'\xa5'*4096)for a in(0x1000,0x3000)}
    code={ENTRY+2*i:struct.pack('<H',word)for i,word in enumerate(WORDS)}
    for a,b in code.items():M.put(pages,a,b)
    M.put(pages,BUFFER-16,b'\xd3'*16+payload+b'\xd3'*16)
    regs=[0xb0000000+i*0x10101 for i in range(13)]+[0x4000,RETURN|1,0x6000003f]
    regs[0]=BUFFER;regs[2]=key;regs[3]=1103515245;regs[4]=24691;regs[6]=BUFFER+100
    return dict(entry_pc=ENTRY,entry_regs=regs,pages={a:bytes(b)for a,b in pages.items()}),code,RETURN


def hard_prediction(f):
    """Independent nine-operation scalar model, never calling the interpreter."""
    regs=list(f['entry_regs']);pages={a:bytearray(b)for a,b in f['pages'].items()}
    need(f['entry_pc']==ENTRY and regs[0]==BUFFER and regs[3:5]==[1103515245,24691]
         and regs[6]==BUFFER+100 and regs[13:]==[0x4000,RETURN|1,0x6000003f],'owned loop geometry')
    flow=[];reads=[];stores=[]
    def before(offset):flow.append(dict(pc=ENTRY+offset,regs=list(regs)))
    def nz(value):return (value&0x80000000)|(int(value==0)<<30)
    def logical(value):regs[15]=(regs[15]&0x3fffffff)|nz(value)
    def add(a,b):
        value=(a+b)&0xffffffff
        regs[15]=(regs[15]&0x0fffffff)|nz(value)|(int(a+b>0xffffffff)<<29)|((~(a^b)&(a^value)&0x80000000)>>3)
        return value
    for i in range(50):
        before(0);regs[2]=(regs[2]*regs[3])&0xffffffff;logical(regs[2])
        before(2);regs[2]=add(regs[2],regs[4])
        before(4);regs[7]=regs[2]>>16
        regs[15]=(regs[15]&0x1fffffff)|nz(regs[7])|(((regs[2]>>15)&1)<<29)
        before(6);b=bytes(pages[0x3000][regs[0]-0x3000:regs[0]-0x3000+2])
        reads.append(dict(pc=ENTRY+6,address=regs[0],bytes=2,hex=b.hex()));regs[1]=int.from_bytes(b,'little')
        before(8);regs[1]^=regs[7];logical(regs[1])
        before(10);stores.append(dict(pc=ENTRY+10,address=regs[0],bytes=2,before=b.hex(),value=regs[1]))
        pages[0x3000][regs[0]-0x3000:regs[0]-0x3000+2]=regs[1].to_bytes(2,'little')
        before(12);regs[0]=add(regs[0],2)
        before(14);v=(regs[0]-regs[6])&0xffffffff
        regs[15]=(regs[15]&0x0fffffff)|nz(v)|(int(regs[0]>=regs[6])<<29)|(((regs[0]^regs[6])&(regs[0]^v)&0x80000000)>>3)
        before(16)
    before(18)
    need(regs[15]==0x6000003f and regs[0]==BUFFER+100,'owned loop exact exit')
    return dict(flow=flow,reads=reads,stores=stores,returned=regs,stop_pc=RETURN,native_peak=0,pages={a:bytes(b)for a,b in pages.items()})


def source_ids():
    return {str(p.relative_to(SOURCE)):hashlib.sha256(p.read_bytes()).hexdigest()for p in(HERE,Path(A.__file__),Path(C.__file__))}


def inputs():
    plain=owned_plaintext();cipher=crypt100(plain,0x4000)[0]
    return (('PID-encrypt',plain,0x4000,True),('PID-decrypt',cipher,0x4000,True),
            ('checksum-key-counter',plain,0x2ab,True),('PID-encrypt-OFF',plain,0x4000,False))


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def cell_receipt(name,observe,p):
    return dict(name=name,observed=observe,instructions=len(p['flow']),reads=len(p['reads']),stores=len(p['stores']),
        unique_starts=len({x['pc']for x in p['flow']}),source_full16_every_pc=True,native_full16_every_pc=observe,all_final_pages=True,
        returned=p['returned'],source_flow_sha256=digest(p['flow']),source_reads_sha256=digest(p['reads']),source_stores_sha256=digest(p['stores']),
        native_projection_sha256={k:digest(p[k])for k in('flow','reads','stores')}if observe else None,
        final_map_sha256=M.map_digest(p['pages']),payload_sha256=hashlib.sha256(M.read(p['pages'],BUFFER,100)).hexdigest())


def expected_receipt():
    """CPU-free completed receipt expectation, useful for cached qualification."""
    rows=[cell_receipt(name,observe,hard_prediction(kernel(payload,key)[0]))for name,payload,key,observe in inputs()]
    return dict(schema='native-Mon-party100-owned-v1',ROM_loaded=False,CPU_model=17,
        scope='Owned50-halfword loop only; no native ROM body, save semantics, DS hardware or timing claim',
        source_sha256=source_ids(),cases=rows)


def qualify():
    need(hashlib.sha256(Path(C.__file__).read_bytes()).hexdigest()==PRODUCER_SHA,'retained8192 producer identity')
    A.source_identity_guard();rows=[]
    for name,payload,key,observe in inputs():
        f,code,stop=kernel(payload,key);hard=hard_prediction(f)
        allow_read=lambda pc,a,n:pc==ENTRY+6 and n==2 and a in range(BUFFER,BUFFER+100,2)
        allow_write=lambda pc,a,n:pc==ENTRY+10 and n==2 and a in range(BUFFER,BUFFER+100,2)
        source=A.run(f,(),stop,cap=1024,thumb_code=code,read_guard=allow_read,write_guard=allow_write)
        for k in hard:need(source[k]==hard[k],'independent scalar/interpreter '+name+'/'+k)
        need(M.read(hard['pages'],BUFFER,100)==crypt100(payload,key)[0],'independent whole100 math')
        # Bind geometry and fetch metadata only. No predicted values or pages
        # are made available to the retained producer namespace.
        reader=types.SimpleNamespace(TOP=0x4000)
        loader=types.SimpleNamespace(THUMB={str(pc):(pc,2,1,'owned')for pc in code},thumb_code=lambda parts:{int(pc):blob for pc,blob in parts.items()})
        frozen=types.SimpleNamespace(ENTRY=ENTRY,RETURN=RETURN,input_record=lambda item:dict(entry_pc=item['entry_pc'],entry_regs=item['entry_regs'],initial_map_sha256=M.map_digest(item['pages'])))
        run=types.FunctionType(C.run.__code__,{**C.run.__globals__,'F':frozen,'L':loader,'R':reader,'CODE_SPANS':()})
        raw=run(f,C.observation_policy(source),observe=observe)
        need(raw['fault']is None and raw['stopped']is True and raw['stop_pc']==stop,'owned CPU stopped without fault')
        need((raw['executed_count'],raw['ARM_count'],raw['Thumb_count'],raw['callback_count'],raw['read_count'],raw['store_count'],raw['stack_peak'],raw['unique_executed_starts'])==(451,0,451,452,50,50,0,10),'owned exact CPU counters')
        need(raw['models']==raw['runtime_host_writes']==[],'no owned service/runtime host writes')
        need(raw['returned']==hard['returned'] and raw['final_map_sha256']==M.map_digest(hard['pages'])and raw['final_pages']==[dict(ram=a,hex=b.hex())for a,b in sorted(hard['pages'].items())],'owned complete CPU endpoint/pages')
        for k in('flow','reads','stores'):need(raw[k]==(hard[k]if observe else []),'owned observed/OFF '+name+'/'+k)
        rows.append(cell_receipt(name,observe,hard))
    receipt=expected_receipt();need(rows==receipt['cases'],'all owned qualification rows');return receipt


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--json',type=Path,required=True);a=p.parse_args()
    try:
        out=a.json.resolve();need(SOURCE not in out.parents and out!=SOURCE and not out.exists()and not out.is_symlink(),'fresh private owned100 qualification')
        receipt=qualify()
        with out.open('x')as f:json.dump(receipt,f,indent=2);f.write('\n')
    except(ValueError,OSError)as e:p.exit(2,str(e)+'\n')
    print('Four owned100 loop cells PASS: scalar/full16/access/preimage/pages/OFF; no ROM')


if __name__=='__main__':main()
