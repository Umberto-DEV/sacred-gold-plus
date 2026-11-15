#!/usr/bin/env python3
"""Exact camera source/readback attribution; emit metadata, never game bytes."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys
import ndspy.rom

sys.path.insert(0,str(Path(__file__).resolve().parent))
from rileggi_camera import Immagine, canarino
import tabella as T
from oracolo import verifica, falsifica

REPO=Path(__file__).resolve().parents[4]
BASES={'EN':('281c2d68e442479e679d8b7e36566ade614d236151c65c9684bad6985461827d',127104144),
       'IT':('7b61646c627eb67cd991dbc33d68519edd69395468ea8b326e867fe98e62d077',131906120)}
RETAILS={'EN':'65f02a56842b75aa92d775d56d657a56fe3fa993550b04dc20704ab82d760105',
         'IT':'013d04f5512b01ad98735a5f850dc039f0ee80bc57035b3a10e8b650be690ce1'}
COD=0x023DEB8C


def sha(data):
    return hashlib.sha256(data).hexdigest()


def need(ok,reason):
    if not ok:
        raise ValueError(reason)


def analyze(base,rom,retail,built_base,built_r4,language):
    pin=json.loads((REPO/'source/distribution/game-1.3.2-r4.json').read_text())['targets'][language]
    records=[];windows=[]
    for label,path,digest,size in (('base11',base,*BASES[language]),
          ('r4',rom,pin['sha256'],pin['bytes'])):
        raw=Immagine(path)
        need(len(raw.raw)==size and sha(raw.raw)==digest,label+' exact input identity')
        main=ndspy.rom.NintendoDSRom(raw.raw).loadArm9()
        def read(a,n,main=main):
            for section in main.sections:
                k=a-section.ramAddress
                if 0<=k and k+n<=len(section.data):
                    return bytes(section.data[k:k+n])
            raise ValueError('ndspy address range')
        fields={}
        for name,a,n in (('hook',0x0203B400,28),('validator',0x0203B268,18),
                ('callers',0x020530F4,44),('body',COD,84),('state',0x023DFFFC,1),
                ('headers',0x020F6BE0,540*24)):
            data=raw.b(a,n);need(data==read(a,n),'raw/ndspy disagreement '+name)
            fields[name]=dict(ram=hex(a),rom_offset=hex(raw.o(a)),bytes=n,sha256=sha(data))
        need(raw.b(0x0203B400,4)==bytes.fromhex('054b1847') and raw.w(0x0203B418)==COD|1,'entry shim')
        expected=Path(built_base if label=='base11' else built_r4).read_bytes()
        need(len(expected)==84 and raw.b(COD,84)==expected,'source build/readback '+label)
        start,end=struct.unpack('<II',raw.b(COD+0x48,8))
        need((start,end)==((0x023DEB6C,0x023DEB8C) if label=='base11' else (0x023D8A10,0x023D8A98)), 'exception extent')
        blob=raw.b(start,end-start);need(blob==read(start,len(blob)),'exception mapping')
        decoded,words=T.decodifica(blob)
        need(len(decoded)==len(words) and all(a<b for a,b in zip(words,words[1:])),'sorted unique exception IDs')
        expected_table=T.VECCHIE if label=='base11' else T.CANONICA
        need(decoded==expected_table,'public policy vs installed exceptions')
        need(raw.b(0x023DFFFC,1)==b'\x01','initial state byte')
        if label=='r4':
            need(raw.b(end,16)==read(end,16)==canarino(0xCA5A1100,4),'table canary')
        fields['exceptions']=dict(ram=hex(start),rom_offset=hex(raw.o(start)),bytes=len(blob),entries=len(words),sha256=sha(blob))
        records.append(dict(input=label,sha256=digest,bytes=size,ranges=fields))
        windows.append({(a,n):raw.b(a,n) for a,n in ((COD,84),(0x020530F4,44),(0x0203B268,18))})
        del raw, main
    need({i for i,(a,b) in enumerate(zip(windows[0][COD,84],windows[1][COD,84])) if a!=b}=={0x48,0x49,0x4C,0x4D},'pool-only body delta')
    retail_raw=Path(retail).read_bytes()
    need(len(retail_raw)==134217728 and sha(retail_raw)==RETAILS[language],'retail identity')
    native=ndspy.rom.NintendoDSRom(retail_raw).loadArm9()
    def native_read(a,n):
        for section in native.sections:
            k=a-section.ramAddress
            if 0<=k and k+n<=len(section.data):return bytes(section.data[k:k+n])
        raise ValueError('retail address range')
    # The windows are authenticated, rather than interpreting arbitrary halfwords as callers.
    for a,n,digest in ((0x020530F4,44,'2bc9be117d5169ba402beb652c815a01f362672e78cca0d36bc95739722ff1ab'),
                       (0x0203B268,18,'c32286b7bac5e5751f7b26d0f2d1bbeae47983ea1f9ce1414d3f75c359bba4ac')):
        need(sha(native_read(a,n))==digest and all(sha(w[a,n])==digest for w in windows),'native caller/validator provenance')
    retail_digest=sha(retail_raw)
    del retail_raw, native
    return dict(language=language,inputs=records,retail_sha256=retail_digest,
        body_delta_offsets=[72,73,76,77],execution=verifica(rom),falsifiers=falsifica(rom),
        limits=['Isolated hook execution; only assertion transport is stubbed.',
                'Public expected policy is shared with the historical writer; no visual/geometric validation.',
                'No natural caller activation or save lifetime observation.',
                'Raw decoder shares project layout validation; ndspy is the separate decoder.',
                'Compiler identity describes this reconstruction, not the unauthenticated historical assembler.'])


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    for name in ('base','rom','retail','built-base','built-r4'):
        ap.add_argument('--'+name,type=Path,required=True)
    ap.add_argument('--language',choices=('EN','IT'),required=True)
    ap.add_argument('--json',type=Path,required=True)
    a=ap.parse_args()
    report=analyze(a.base,a.rom,a.retail,a.built_base,a.built_r4,a.language)
    a.json.write_text(json.dumps(report,indent=2)+'\n')
    need(not report['execution']['errori'],'isolated execution failure')
    need(all(m['rejected'] for m in report['falsifiers']),'accepted RAM mutant')
    print(json.dumps(dict(language=a.language,cases=report['execution']['cases'],status='PASS')))


if __name__=='__main__':
    main()
