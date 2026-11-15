"""Finite memory-archive API chain: independent semantics and ARM transcript.

Original ROM instructions and the compiled project caller are counted separately.
No natural CARD I/O, Thumb NARC parser, host completion or phase reinjection.
"""
from pathlib import Path
import importlib.util
import struct


def load(path,name):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


F=load(Path(__file__).parents[1]/'tools/congela_fs_memory_read.py','memory_read_bench_frozen')
A=load(Path(__file__).with_name('arm32_sync_oracle.py'),'memory_read_qualified_arithmetic')
L,R,M=F.L,F.R,F.M
need,wire=F.need,M.wire
DRIVER_SHA='96474b1b6cc63a7210be3761705bcbcd0398fefc7c61e53fff50cb770fb2198c'
CODE_SPANS=L.CODE_SPANS+((L.DRIVER,L.DRIVER_CODE),)


# Static memory classes decoded before arithmetic/CPU from1181 ARM starts.
READ_SITES=frozenset((
    (0x20d1ed8,4),(0x20d1f0c,4),(0x20d1f30,4),(0x20d4a68,2),
    (0x20d4a7c,2),(0x20d4a94,2),(0x20d4ac8,2),(0x20d4ad8,2),
    (0x20d4b00,2),(0x20d4b2c,2),(0x20d4b50,2),(0x20d4b78,4),
    (0x20d4b94,2),(0x20d4bb4,2),(0x20d4bb8,2),(0x20d6874,4),
    (0x20d687c,4),(0x20d689c,4),(0x20d68bc,4),(0x20d68c8,4),
    (0x20d68cc,4),(0x20d68e4,4),(0x20d68f8,4),(0x20d6904,4),
    (0x20d6950,4),(0x20d6974,4),(0x20d697c,4),(0x20d6990,4),
    (0x20d69ac,4),(0x20d69d8,4),(0x20d69f4,4),(0x20d6a00,4),
    (0x20d6a18,4),(0x20d6a34,4),(0x20d6a48,4),(0x20d6a60,1),
    (0x20d6a64,1),(0x20d6a88,4),(0x20d6a9c,4),(0x20d6aa8,4),
    (0x20d6ab0,4),(0x20d6ac0,4),(0x20d6ac4,4),(0x20d6ae8,4),
    (0x20d6afc,4),(0x20d6b28,4),(0x20d6b48,4),(0x20d6b4c,4),
    (0x20d6b50,4),(0x20d6b5c,4),(0x20d6b98,4),(0x20d6b9c,4),
    (0x20d6ba0,4),(0x20d6ba4,4),(0x20d6bb0,4),(0x20d6bbc,4),
    (0x20d6bf8,4),(0x20d6c04,2),(0x20d6c08,4),(0x20d6c30,4),
    (0x20d6c38,2),(0x20d6c40,4),(0x20d6c4c,2),(0x20d6c54,4),
    (0x20d6c58,4),(0x20d6c64,2),(0x20d6c68,4),(0x20d6c7c,4),
    (0x20d6c90,4),(0x20d6c94,4),(0x20d6ca0,4),(0x20d6cbc,4),
    (0x20d6cc0,1),(0x20d6cd8,4),(0x20d6ce8,4),(0x20d6cec,4),
    (0x20d6d0c,4),(0x20d6d10,4),(0x20d6d24,4),(0x20d6d30,4),
    (0x20d6d54,4),(0x20d6d58,4),(0x20d6d5c,4),(0x20d6d64,2),
    (0x20d6d80,4),(0x20d6d88,2),(0x20d6d90,2),(0x20d6d9c,4),
    (0x20d6da8,4),(0x20d6dbc,4),(0x20d6dc4,4),(0x20d6dcc,1),
    (0x20d6dec,1),(0x20d6e24,4),(0x20d6e3c,1),(0x20d6e60,2),
    (0x20d6e6c,4),(0x20d6e8c,4),(0x20d6ec0,4),(0x20d6ec4,4),
    (0x20d6ecc,4),(0x20d6f00,4),(0x20d6f28,4),(0x20d6f2c,4),
    (0x20d6f30,4),(0x20d6f34,4),(0x20d6f48,4),(0x20d6f4c,1),
    (0x20d6f5c,1),(0x20d6f74,4),(0x20d6f78,4),(0x20d6f80,4),
    (0x20d6f90,4),(0x20d734c,4),(0x20d7350,4),(0x20d7354,4),
    (0x20d7368,4),(0x20d7370,4),(0x20d7394,4),(0x20d7398,4),
    (0x20d73a4,4),(0x20d73bc,4),(0x20d73c0,4),(0x20d73c8,4),
    (0x20d73d0,4),(0x20d73d8,4),(0x20d744c,4),(0x20d7460,4),
    (0x20d7498,4),(0x20d74ac,4),(0x20d74c8,4),(0x20d74d4,4),
    (0x20d74ec,4),(0x20d74f0,4),(0x20d7508,4),(0x20d7520,4),
    (0x20d7530,4),(0x20d7548,4),(0x20d7560,4),(0x20d756c,4),
    (0x20d758c,4),(0x20d75a8,4),(0x20d75b4,4),(0x20d75c8,4),
    (0x20d75d8,4),(0x20d7608,4),(0x20d761c,4),(0x20d7620,4),
    (0x20d7638,4),(0x20d7644,4),(0x20d765c,4),(0x20d766c,4),
    (0x20d7684,4),(0x20d76ac,4),(0x20d774c,4),(0x20d7760,4),
    (0x20d7774,4),(0x20d7784,4),(0x20d7790,4),(0x20d77a4,4),
    (0x20d77b8,4),(0x20d77e0,4),(0x20d77e8,4),(0x20d77f4,4),
    (0x20d77f8,4),(0x20d7810,4),(0x20d7820,4),(0x20d783c,4),
    (0x20d7850,4),(0x20d7868,4),(0x20d787c,4),(0x20d7888,4),
    (0x20d789c,4),(0x20d78a8,4),(0x20d78d0,4),(0x20d78dc,4),
    (0x20d7900,4),(0x20d790c,4),(0x20d7928,4),(0x20d7fcc,1),
    (0x20d7fe8,4),(0x20d7ff0,4),(0x20d800c,4),(0x20d8014,4),
    (0x20d8020,1),(0x20d8054,4),(0x20d8058,4),(0x20d8074,4),
    (0x20d8090,1),(0x20d80b0,4),(0x20d80c4,4),(0x20d80fc,4),
    (0x20d810c,4),(0x20d8110,4),(0x20d8140,4),(0x20d816c,4),
    (0x20d817c,4),(0x20d81bc,4),(0x20d8210,4),(0x20d8220,4),
    (0x20d8234,4),(0x20d824c,4),(0x20d8258,4),(0x20d826c,4),
    (0x20d829c,4),(0x20d82b0,4),(0x20d82bc,4),(0x20d82d8,4),
    (0x20d82e8,4),(0x20d82f8,4),(0x20d830c,4),(0x20d8328,4),
    (0x20d8340,4),(0x20d8354,4),(0x20d8374,4),(0x20d83a4,4),
    (0x20d83a8,4),(0x20d83b8,4),(0x20d83cc,4),(0x20d83f8,4),
    (0x20d8404,4),(0x20d8410,4),(0x20d8424,4),(0x20d8430,4),
    (0x22f0810,4),(0x22f0834,4),(0x22f0868,4),
))
WRITE_SITES=frozenset((
    (0x20d1ecc,4),(0x20d1efc,4),(0x20d1f00,4),(0x20d1f04,4),
    (0x20d1f08,4),(0x20d1f1c,4),(0x20d1f20,4),(0x20d4a9c,2),
    (0x20d4ae0,2),(0x20d4b0c,2),(0x20d4b30,2),(0x20d4b54,2),
    (0x20d4b7c,4),(0x20d4ba0,2),(0x20d4bc8,2),(0x20d6864,4),
    (0x20d6884,4),(0x20d688c,4),(0x20d6894,4),(0x20d6898,4),
    (0x20d68a8,4),(0x20d68ac,4),(0x20d68c0,4),(0x20d68f4,4),
    (0x20d6948,4),(0x20d695c,4),(0x20d6a28,4),(0x20d6a3c,4),
    (0x20d6a40,4),(0x20d6a50,4),(0x20d6aa0,4),(0x20d6abc,4),
    (0x20d6af0,4),(0x20d6b58,4),(0x20d6b94,4),(0x20d6bac,4),
    (0x20d6bec,4),(0x20d6c00,4),(0x20d6c1c,4),(0x20d6c34,4),
    (0x20d6c50,2),(0x20d6c60,4),(0x20d6c70,4),(0x20d6c84,4),
    (0x20d6c9c,4),(0x20d6cac,4),(0x20d6ccc,4),(0x20d6cd4,4),
    (0x20d6d1c,1),(0x20d6d2c,4),(0x20d6d60,4),(0x20d6d70,2),
    (0x20d6d74,2),(0x20d6d78,4),(0x20d6d84,4),(0x20d6d8c,4),
    (0x20d6d98,2),(0x20d6da0,4),(0x20d6db0,4),(0x20d6e98,4),
    (0x20d6e9c,4),(0x20d6f04,4),(0x20d6f3c,4),(0x20d6f44,4),
    (0x20d6f84,4),(0x20d7340,4),(0x20d736c,4),(0x20d7384,4),
    (0x20d73a0,4),(0x20d73ac,4),(0x20d73b0,4),(0x20d73c4,4),
    (0x20d73cc,4),(0x20d73d4,4),(0x20d73dc,4),(0x20d7448,4),
    (0x20d7484,4),(0x20d749c,4),(0x20d74d0,4),(0x20d7514,4),
    (0x20d7594,4),(0x20d75d4,4),(0x20d7640,4),(0x20d7658,4),
    (0x20d7694,4),(0x20d7744,4),(0x20d7788,4),(0x20d7798,4),
    (0x20d77a0,4),(0x20d77b0,4),(0x20d77f0,4),(0x20d7800,4),
    (0x20d780c,4),(0x20d782c,4),(0x20d7830,4),(0x20d7838,4),
    (0x20d7874,4),(0x20d78a4,4),(0x20d7f9c,4),(0x20d7fa0,4),
    (0x20d7fa4,4),(0x20d7fa8,4),(0x20d7fac,4),(0x20d7fb4,4),
    (0x20d7fb8,4),(0x20d7fc0,4),(0x20d7ff4,2),(0x20d7ff8,4),
    (0x20d7ffc,4),(0x20d8000,2),(0x20d8018,4),(0x20d807c,4),
    (0x20d8080,4),(0x20d8084,2),(0x20d8088,2),(0x20d80b8,4),
    (0x20d80bc,4),(0x20d80c8,4),(0x20d80d4,4),(0x20d80d8,4),
    (0x20d80e4,4),(0x20d80e8,4),(0x20d8104,4),(0x20d8118,4),
    (0x20d8130,4),(0x20d8138,4),(0x20d814c,4),(0x20d8180,4),
    (0x20d8208,4),(0x20d820c,4),(0x20d822c,4),(0x20d8230,4),
    (0x20d823c,4),(0x20d8268,4),(0x20d8278,4),(0x20d82c0,4),
    (0x20d82dc,4),(0x20d82e4,4),(0x20d82f4,4),(0x20d82fc,4),
    (0x20d8348,4),(0x20d843c,4),(0x22f0800,4),(0x22f0818,4),
    (0x22f082c,4),(0x22f0840,4),(0x22f0854,4),(0x22f0860,4),
))

def within(a,n,base,size):return base<=a and a+n<=base+size


def memory_sites(pages):
    sites={'read':set(),'write':set()}
    for base,size in CODE_SPANS:
        for pc in range(base,base+size,4):
            word=int.from_bytes(M.read(pages,pc,4),'little');group=A.validate_word(word)
            if group in('memory','block'):
                width=4 if group=='block'else(1 if word&(1<<22)else 4)if(word>>26)&3==1 else 2
                sites['read'if word&(1<<20)else'write'].add((pc,width))
    return sites


def read_owner(pc,a,n):
    if(pc,n)not in READ_SITES:return False
    if within(a,n,R.TOP-F.FRAME,F.FRAME)or n==4 and within(a,n,F.FILE,72):return True
    if n==4 and(within(a,n,R.ARC,92)or within(a,n,L.L.L.ROOT,12)):return True
    if within(a,n,R.FNT,2902)or n==1 and within(a,n,L.L.L.PATH,8):return True
    if n==4 and within(a,n,R.FAT,4104):return True
    if n==4 and(any(within(a,n,base,16)for base in(L.HEADER_SOURCE,L.MEMBER_SOURCE))or a in(L.DRIVER+108,L.DRIVER+112)):return True
    if n==4 and a in(0x210e124,0x210e12c,0x210e130,0x210e134,0x210e13c,0x210e140,0x210e144):return True
    return n==4 and any(a==base+size-L.POOLS[name]for name,(base,size,_)in L.COMPONENTS.items()if name in L.POOLS)


def write_owner(pc,a,n):
    if(pc,n)not in WRITE_SITES:return False
    if within(a,n,R.TOP-F.FRAME,F.FRAME):return True
    if n==4 and a==R.ARC+28:return pc in(0x20d68f4,0x20d6a3c,0x20d6abc,0x20d6af0,0x20d7874,0x20d7640)
    if n==4 and a==R.ARC+36:return pc in(0x20d782c,0x20d6884)
    if n==4 and any(within(a,n,base,16)for base in(L.HEADER_DEST,L.MEMBER_DEST)):return pc==0x20d4b7c
    if n==4 and(pc,a)in tuple((L.DRIVER+offset,L.RESULT+index*4)for index,offset in enumerate((0x18,0x2c,0x40,0x54,0x60))):return True
    if n!=4 or not within(a,n,F.FILE,72):return False
    off=a-F.FILE
    if off in(0,4,12,16,20):return pc in(0x20d688c,0x20d6894,0x20d6898,0x20d68a8,0x20d68ac,
        0x20d6a40,0x20d7798,0x20d77a0,0x20d77b0,0x20d77f0,0x20d7830,0x20d7838,0x20d78a4,0x20d8268,0x20d814c,0x20d82e4,0x20d82f4)
    return(pc,off)in((0x20d822c,8),(0x20d8230,48),(0x20d823c,52),(0x20d73a0,48),(0x20d73ac,52),
        (0x20d73b0,56),(0x20d73c4,36),(0x20d73cc,44),(0x20d73d4,40),(0x20d73dc,32),
        (0x20d8118,48),(0x20d8130,52),(0x20d8138,56),(0x20d6bac,44),(0x20d843c,44),(0x20d82dc,8))


def require_memory_delta(initial,final,stores):
    replay={a:bytearray(b)for a,b in initial.items()}
    for e in stores:
        pc,a,n,value=(e[k]for k in('pc','address','bytes','value'))
        need(all(type(x)is int for x in(pc,a,n,value))and n in(1,2,4)and 0<=value<1<<(8*n),'typed native delta event')
        need(write_owner(pc,a,n),'source delta owner/site')
        need(M.read(replay,a,n).hex()==e['before'],'chronological store preimage');M.put(replay,a,value.to_bytes(n,'little'))
    need({a:bytes(b)for a,b in replay.items()}==final,'whole map chronological replay')


def require_memory_archive(archive):
    need(type(archive)is bytes and len(archive)==92,'typed archive92')
    need(R.u32(archive,28)==7 and R.u32(archive,40)==L.ARCHIVE_BASE and R.u32(archive,72)==0x20d7448 and
         R.u32(archive,88)in(0,2)and archive[4:28]==b'\0'*24 and archive[32:40]==b'\0'*8 and R.u32(archive,48)==4104,'explicit hybrid memory archive input')


def predict(f):
    need(type(f['precompleted_buffers'])is bool,'typed buffer projection')
    path,root=L.L.L.PATH,L.L.L.ROOT
    expected=[F.FILE,path,L.HEADER_DEST,L.MEMBER_DEST]+[0xB0000000+i*0x010101 for i in range(4,13)]+[R.TOP,F.RETURN,0x6000001f]
    need(f['entry_pc']==F.ENTRY and wire(f['entry_regs'])==wire(expected),'exact memory caller entry ABI')
    for name,(a,n,digest)in L.COMPONENTS.items():need(R.sha(M.read(f['pages'],a,n))==digest,'exact memory Read native component '+name)
    need(R.sha(M.read(f['pages'],L.DRIVER,116))==DRIVER_SHA,'exact compiled project caller')
    need(R.sha(M.read(f['pages'],R.FNT,2902))==R.FNT_SHA and R.sha(M.read(f['pages'],R.FAT,4104))==R.FAT_SHA,'exact cached table bytes')
    need(R.sha(M.read(f['pages'],root,12))==L.L.L.ROOT_SHA and M.read(f['pages'],path,8)==L.L.L.PATH_BYTES,'exact root/path')
    header,member=M.read(f['pages'],L.HEADER_SOURCE,16),M.read(f['pages'],L.MEMBER_SOURCE,16)
    need(R.sha(header)==L.HEADER_SHA and R.sha(member)==L.MEMBER_SHA,'owned header/member source windows')
    archive=M.read(f['pages'],R.ARC,92)
    require_memory_archive(archive)
    client=M.read(f['pages'],F.FILE,72);initial_client=bytearray(b'\xa5'*72)
    for off in(0,4,8,12,24,28):struct.pack_into('<I',initial_client,off,0)
    struct.pack_into('<I',initial_client,16,14);need(client==bytes(initial_client),'source-initialized client72')
    need(M.read(f['pages'],L.HEADER_DEST,16)==(header if f['precompleted_buffers']else b'\xa5'*16)and
         M.read(f['pages'],L.MEMBER_DEST,16)==(member if f['precompleted_buffers']else b'\xa5'*16),'explicit initial destination projection')
    fnt=L.L.L.L.resolve_path(M.read(f['pages'],R.FNT,2902),L.L.L.PATH_BYTES[:-1])
    fat=L.L.fat_metadata(M.read(f['pages'],R.FAT,4104),fnt['file_id'],4104);top,bottom=fat['top'],fat['bottom'];selected=top+0x224c
    need(top+L.ARCHIVE_BASE==L.HEADER_SOURCE and selected+L.ARCHIVE_BASE==L.MEMBER_SOURCE,'nonwrapping memory payload translation')
    sites=memory_sites(f['pages']);need(sites==dict(read=set(READ_SITES),write=set(WRITE_SITES)),'authenticated memory Read static site/width maps')
    result=A.run(f,CODE_SPANS,F.RETURN,read_guard=read_owner,write_guard=write_owner)
    counts={name:sum(a<=x['pc']<a+n-L.POOLS.get(name,0)for x in result['flow'])for name,(a,n,_)in L.COMPONENTS.items()if name!='default_table'}
    counts['project_caller']=sum(L.DRIVER<=x['pc']<L.DRIVER+108 for x in result['flow'])
    entries={name:sum(x['pc']==L.COMPONENTS[name][0]for x in result['flow'])for name in counts if name!='project_caller'}
    need(entries==dict(open=1,fast=1,init=1,convert=1,find=1,send=5,execute=5,release=5,wakeup=5,next=5,disable=27,restore=27,
        fast_command=1,direct_command=1,findpath=1,translate=16,seekdir=4,read_dir=6,read_table=21,read_memory=21,copy=23,strnicmp=6,
        read_wrapper=2,read_core=2,wait=2,seek=1,close=1,read_command=2,read_callback=2,close_command=1),'source complete API chain callgraph')
    need(counts['project_caller']==27 and sum(counts.values())==4279,'manual before-oracle total4279/4252ROM/27project')
    copies=[dict(address=x['regs'][0],bytes=x['regs'][2])for x in result['flow']if x['pc']==0x20d4a50]
    logical=[dict(address=R.FNT+x['offset'],bytes=x['bytes'])for x in fnt['table_reads']]+[
        dict(address=R.FAT+1120,bytes=8),dict(address=L.HEADER_SOURCE,bytes=16),dict(address=L.MEMBER_SOURCE,bytes=16)]
    need(copies==logical,'functional FNT/FAT/payload reads versus native copies')
    # Explicit old-position argument and BEFORE-callback position advancement.
    calls=[x['regs'][:4]for x in result['flow']if x['pc']==0x20d7448]
    need(calls==[[R.ARC,L.HEADER_DEST,top,16],[R.ARC,L.MEMBER_DEST,selected,16]],'source callback uses old position and requested length')
    advances=[e for e in result['stores']if e['pc']==0x20d6bac]
    need([(e['address'],e['before'],e['value'])for e in advances]==[(F.FILE+44,struct.pack('<I',top).hex(),top+16),
         (F.FILE+44,struct.pack('<I',selected).hex(),selected+16)],'native Read command position writes')
    positions=[i for i,x in enumerate(result['flow'])if x['pc']==0x20d6bac]
    blxs=[i for i,x in enumerate(result['flow'])if x['pc']==0x20d6bb8]
    callbacks=[i for i,x in enumerate(result['flow'])if x['pc']==0x20d7448]
    need(all(a<b<c for a,b,c in zip(positions,blxs,callbacks)),'position advance precedes callback')
    # Convert DIR is live before the first Fast PUSH, then becomes reusable.
    boundary=next(i for i,e in enumerate(result['stores'])if e['pc']==0x20d8208);need(boundary==624,'driver6/Open2/Convert616 prefix stores')
    checkpoint={a:bytearray(b)for a,b in f['pages'].items()}
    for e in result['stores'][:boundary]:M.put(checkpoint,e['address'],e['value'].to_bytes(e['bytes'],'little'))
    prop=fnt['directory_property'];directory=bytearray(b'\xa5'*72)
    for off,value in((0,0),(4,0),(8,R.ARC),(12,0),(16,4),(20,0),(24,0),(28,0),(60,path),(64,0),(68,R.TOP-40)):
        struct.pack_into('<I',directory,off,value)
    directory[32:48]=struct.pack('<IHHII',R.ARC,prop['own_id'],prop['index'],R.FNT+prop['offset'],prop['parent'])
    directory[48:60]=struct.pack('<III',R.TOP-408,0,0)
    need(M.read(checkpoint,R.TOP-128,72)==bytes(directory)and M.read(checkpoint,R.TOP-40,8)==struct.pack('<II',R.ARC,140)and
         M.read(checkpoint,F.FILE,72)==client,'functional new Convert boundary while live')
    # Reconstruct each real return boundary using unique project STR sites.
    expected_file=bytearray(client)
    for off,value in((8,R.ARC),(12,16),(16,6),(20,0)):struct.pack_into('<I',expected_file,off,value)
    expected_file[32:48]=struct.pack('<4I',140,top,bottom,top);expected_file[48:60]=struct.pack('<3I',top,bottom,140)
    replay_pages={a:bytearray(b)for a,b in f['pages'].items()};phase=0;phase_rows=[]
    return_sites={L.DRIVER+offset:index for index,offset in enumerate((0x18,0x2c,0x40,0x54,0x60))}
    phase_returns=(1,16,1,16,1)
    for index,e in enumerate(result['stores']):
        if e['pc']in return_sites:
            need(return_sites[e['pc']]==phase,'ordered five native API returns')
            if phase in(1,3):
                destination=L.HEADER_DEST if phase==1 else L.MEMBER_DEST
                position=top+16 if phase==1 else selected+16
                struct.pack_into('<II',expected_file,12,16,0)
                struct.pack_into('<I',expected_file,20,0);struct.pack_into('<I',expected_file,44,position)
                expected_file[48:60]=struct.pack('<3I',destination,16,16)
            elif phase==2:struct.pack_into('<I',expected_file,44,selected)
            elif phase==4:
                for off,value in((8,0),(12,0),(16,14)):struct.pack_into('<I',expected_file,off,value)
            need(M.read(replay_pages,F.FILE,72)==bytes(expected_file),'functional per-API client72 lifetime')
            need(M.read(replay_pages,R.ARC,92)==archive,'per-API full projected ARC quiescence')
            need(e['value']==phase_returns[phase]and e['address']==L.RESULT+phase*4,'independent native API result record')
            if phase>=1:need(M.read(replay_pages,L.HEADER_DEST,16)==header,'native header read complete')
            if phase>=3:need(M.read(replay_pages,L.MEMBER_DEST,16)==member,'native member read complete')
            phase_rows.append(dict(phase=phase,return_store_index=index,return_pc=e['pc'],result=e['value'],file72_sha256=R.sha(bytes(expected_file))))
            phase+=1
        M.put(replay_pages,e['address'],e['value'].to_bytes(e['bytes'],'little'))
    need(phase==5 and M.read(result['pages'],L.RESULT,20)==struct.pack('<5I',*phase_returns),'five native API returns')
    need(M.read(result['pages'],F.FILE,72)==bytes(expected_file),'functional final closed client72')
    need(M.read(result['pages'],L.HEADER_DEST,16)==header and M.read(result['pages'],L.MEMBER_DEST,16)==member and member[6]==15,'independent authenticated output32/PP scalar')
    expected[:4]=[L.RESULT,0,0x6000001f,0];expected[12]=L.MEMBER_DEST+16;expected[14]=0x20d76a4;expected[15]=0x2000001f
    need(wire(result['returned'])==wire(expected),'source project caller complete full16 return')
    need(result['native_peak']==504,'source driver24 plus Open480 frame');require_memory_delta(f['pages'],result['pages'],result['stores'])
    need(len(result['flow'])==4279,'manual total instruction forecast')
    result.update(function_counts=counts,entry_counts=entries,logical_copies=copies,source_metadata=dict(FNT=fnt,FAT=fat),
        convert_boundary_stores=boundary,API_phases=phase_rows,original_rom_count=4252,project_caller_count=27,
        static_memory_sites={k:sorted(v)for k,v in sites.items()})
    return result


BACKEND=dict(unicorn='2.1.4',CPU_model=17,
    scope='CortexA15 backend executing ARMv5 code; not ARM946 timing/cache/IRQ')


def observation_policy(predicted):
    """Only enforcement metadata reaches the producer, never predicted state."""
    return dict(code_starts=frozenset(x['pc']for x in predicted['flow']),
        read_sites=frozenset((x['pc'],x['address'],x['bytes'])for x in predicted['reads']),
        write_sites=frozenset((x['pc'],x['address'],x['bytes'])for x in predicted['stores']))


def run(f,policy,observe=True):
    import unicorn as U
    from unicorn import arm_const as C
    need(type(observe)is bool and U.__version__==BACKEND['unicorn'],'qualified observer/backend version')
    uc=U.Uc(U.UC_ARCH_ARM,U.UC_MODE_ARM);uc.ctl_set_cpu_model(C.UC_CPU_ARM_CORTEX_A15)
    backend=dict(unicorn=U.__version__,CPU_model=uc.ctl_get_cpu_model(),scope=BACKEND['scope'])
    need(wire(backend)==wire(BACKEND),'actual backend identity')
    registers=tuple(getattr(C,'UC_ARM_REG_R'+str(i))for i in range(13))+(C.UC_ARM_REG_SP,C.UC_ARM_REG_LR,C.UC_ARM_REG_CPSR)
    for address,blob in f['pages'].items():uc.mem_map(address,4096);uc.mem_write(address,blob)
    uc.reg_write(C.UC_ARM_REG_CPSR,f['entry_regs'][15])
    for register,value in zip(registers[:15],f['entry_regs'][:15]):uc.reg_write(register,value)
    flow=[];reads=[];stores=[];seen=set();count=0;rom_count=0;project_count=0;callbacks=0;read_count=0;store_count=0;low=R.TOP;stopped=False
    def state():return [uc.reg_read(register)&0xffffffff for register in registers]
    def instruction(machine,address,size,user):
        nonlocal count,rom_count,project_count,callbacks,low,stopped
        callbacks+=1
        if address==F.RETURN:stopped=True;machine.emu_stop();return
        need(size==4 and address in policy['code_starts'],'native instruction outside exact source route')
        count+=1;need(count<=8192,'native instruction cap')
        if L.DRIVER<=address<L.DRIVER+108:project_count+=1
        else:rom_count+=1
        seen.add(address);low=min(low,machine.reg_read(C.UC_ARM_REG_SP))
        if observe:flow.append(dict(pc=address,regs=state()))
    def access(machine,kind,address,size,value,user):
        nonlocal read_count,store_count
        pc=machine.reg_read(C.UC_ARM_REG_PC)
        if kind==U.UC_MEM_WRITE:
            need((pc,address,size)in policy['write_sites'],'native write outside exact source site/address/width')
            store_count+=1
            if observe:stores.append(dict(pc=pc,address=address,bytes=size,before=bytes(machine.mem_read(address,size)).hex(),value=value&((1<<(8*size))-1)))
        else:
            need((pc,address,size)in policy['read_sites'],'native read outside exact source site/address/width')
            read_count+=1
            if observe:reads.append(dict(pc=pc,address=address,bytes=size,hex=bytes(machine.mem_read(address,size)).hex()))
    uc.hook_add(U.UC_HOOK_CODE,instruction);uc.hook_add(U.UC_HOOK_MEM_READ|U.UC_HOOK_MEM_WRITE,access)
    fault=None
    try:uc.emu_start(F.ENTRY,0,timeout=1000000,count=8192)
    except(ValueError,U.UcError)as error:fault=type(error).__name__+': '+str(error)
    pages={address:bytes(uc.mem_read(address,4096))for address in f['pages']}
    return dict(schema='native-fs-memory-read-raw-v1',observed=observe,initial=F.input_record(f),
        fault=fault,stopped=stopped,stop_pc=uc.reg_read(C.UC_ARM_REG_PC),returned=state(),flow=flow,reads=reads,stores=stores,
        executed_count=count,rom_instruction_count=rom_count,project_instruction_count=project_count,unique_executed_starts=len(seen),callback_count=callbacks,read_count=read_count,store_count=store_count,
        stack_peak=R.TOP-low,models=[],runtime_host_writes=[],backend=backend,
        final_map_sha256=M.map_digest(pages),final_pages=[dict(ram=a,hex=b.hex())for a,b in sorted(pages.items())])


def require_run(f,raw):
    predicted=predict(f)
    need(raw.get('schema')=='native-fs-memory-read-raw-v1','native raw schema')
    need(all(type(raw[k])is int for k in('executed_count','rom_instruction_count','project_instruction_count','unique_executed_starts','callback_count','read_count','store_count','stack_peak','stop_pc')),'typed native counters/PC')
    need(wire(raw['initial'])==wire(F.input_record(f)),'complete frozen memory Read input')
    need(wire(raw.get('backend'))==wire(BACKEND),'qualified backend identity')
    need(raw['fault']is None and raw['stopped']is True and raw['stop_pc']==F.RETURN,'finite compiled test caller POP return')
    need(raw['models']==raw['runtime_host_writes']==[],'zero native service model/host writes')
    need((raw['executed_count'],raw['unique_executed_starts'],raw['callback_count'],raw['read_count'],raw['store_count'],raw['stack_peak'])==(len(predicted['flow']),len({x['pc']for x in predicted['flow']}),len(predicted['flow'])+1,len(predicted['reads']),len(predicted['stores']),predicted['native_peak']),'source count/owner/budget')
    need((raw['rom_instruction_count'],raw['project_instruction_count'])==(4252,27),'original ROM versus project caller instruction counts')
    need(wire(raw['returned'])==wire(predicted['returned']),'source full16 memory Read return ABI')
    need(raw['final_map_sha256']==M.map_digest(predicted['pages']),'source complete final map hash')
    need(wire(raw['final_pages'])==wire([dict(ram=a,hex=b.hex())for a,b in sorted(predicted['pages'].items())]),'source all final pages')
    if raw['observed']is True:
        for key in('flow','reads','stores'):need(wire(raw[key])==wire(predicted[key]),'source native '+key)
    else:need(raw['observed']is False and raw['flow']==raw['reads']==raw['stores']==[],'OFF no observation projections')
    return predicted
