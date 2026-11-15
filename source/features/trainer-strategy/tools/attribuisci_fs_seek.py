#!/usr/bin/env python3
"""Five native SET seeks with explicit FAT-backed property input projection.

Only FSFile.prop and read-position effects are modeled. Other known dispatcher
argument/command/queue effects are excluded; this is not full native SDK state.
"""
from pathlib import Path
import importlib.util,struct,types,copy


def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


H=load('fs_seek_close_parent',Path(__file__).with_name('attribuisci_fs_close.py'))
A=load('fs_seek_profile',Path(__file__).parents[1]/'test/fs_seek_bench.py');A.bind(H)
F,V,O,I,PP=H.H,H.H.H,H.H.H.H,H.H.H.H.O,H.H.H.H.O.H
R,P,B,T,need,sha=H.R,H.P,H.B,H.T,H.need,H.sha
TOP,DEST,STOP,FILE,ID,ARC,DIR=H.TOP,H.DEST,H.STOP,H.FILE,H.ID,H.ARC,H.DIR
ENTRY,END,POSITION=0x20D83DC,0x20D8448,FILE+44
SEEK_SHA='99e8a8db572238f5c2aa23d35ddfe505843277a0623dedfe207c2d5872236747'
READ,SEND=0x20D83CC,H.SEND
SDK={a:n for a,n in H.SDK.items()if a!=ENTRY}
SET_PCS=(ENTRY,0x20D83E0,0x20D83F8,0x20D83FC,0x20D8400,*range(0x20D8424,END,4))
CUR_PCS=(ENTRY,0x20D83E0,0x20D83E4,0x20D83E8,0x20D8404,0x20D8408,0x20D840C,*range(0x20D8424,END,4))
from unicorn.arm_const import UC_ARM_REG_PC
BINDINGS=[]


def binding(fn,namespace):
    BINDINGS.append(dict(parent_source_sha256=A.PARENT_SHA256,function=fn.__qualname__,code_unchanged=True,namespace=sorted(namespace)))
    return A.clone(fn,namespace)


def geometry(raw):
    members,receipt=P.RAW.raw_archive(raw,'a/0/1/1');fat,size=struct.unpack_from('<II',raw,0x48);fid=receipt['file_id']
    need(fid==140 and 8*(fid+1)<=size and fat+size<=len(raw),'Seek independent FAT row bounds and identity')
    top,bottom=struct.unpack_from('<II',raw,fat+8*fid)
    need(0<=top<bottom<0x80000000 and bottom<=len(raw)and bottom-top==11356 and len(members)==471 and
        sha(raw[top:bottom])==receipt['archive_sha256'],'Seek physical ROM geometry and whole archive identity')
    return dict(file_id=fid,fat_rom_offset=fat,fat_row_rom_offset=fat+8*fid,top=top,bottom=bottom,
        bytes=bottom-top,archive_sha256=receipt['archive_sha256'],scope='default ROM archive base0 property projection only; opaque ARC identity not reconstructed')


def prop_bytes(g,pos=None):return struct.pack('<4I',g['file_id'],g['top'],g['bottom'],g['top']if pos is None else pos)


def qualify(model,raw,*args):
    from capstone import Cs,CS_ARCH_ARM,CS_MODE_ARM
    q,proof=H.qualify(model,raw,*args);view=P.G.S.SHARED.gifts_audit.Arm9View(raw);blob=view.read(ENTRY,108)
    need(sha(blob)==SEEK_SHA and blob==P.G.piece(model['segments'],ENTRY,108),'Seek raw/decoded identity')
    code=list(Cs(CS_ARCH_ARM,CS_MODE_ARM).disasm(blob,ENTRY))
    need(len(code)==27 and [i.address for i in code]==list(range(ENTRY,END,4))and not any(i.mnemonic=='bl'for i in code),
        'Seek ARM extent without nested calls')
    q['fs_seek_code']={i.address:(4,False)for i in code};q['fs_file_geometry']=geometry(raw)
    proof['native_fs_seek']=dict(ram=hex(ENTRY),rom_offset=hex(view.offset(ENTRY,108)),bytes=108,sha256=sha(blob),
        starts=27,positive_SET_starts=list(map(hex,SET_PCS)),reader_peak=240,global_guest_peak=560,full_bound=608,
        file_geometry=q['fs_file_geometry'],limits='modeled property16/read-pos4 projection; known arg/stat/command/queue effects excluded')
    return q,proof


class SeekObserver:
    def __init__(self,driver,reader):
        self.driver,self.reader,self.active,self.current=driver,reader,False,None
        self.result=[];self.projection=dict(geometry=driver.qualified['fs_file_geometry'],events=[])
        self.parent_step,self.parent_write,self.parent_read,self.base_service=reader.step,reader.write,reader.read,reader.service
        self.root_step=types.MethodType(root_step,reader);self.root_write=driver.convert_observer.native_write
        reader.code={**reader.code,**driver.qualified['fs_seek_code']}
        reader.step,reader.write,reader.read,reader.service=self.step,self.write,self.read,self.service

    def properties(self):return self.reader.read_bytes(FILE+32,16)

    def projected_write(self,kind,address,blob):
        r=self.reader;before=r.read_bytes(address,len(blob));regs=r.regs();frame=r.read_bytes(DIR,240).hex()
        r.u.mem_write(address,blob)
        need(regs==r.regs(),'property projection changed CPU registers')
        event=dict(kind=kind,address=address,bytes=len(blob),before=before.hex(),after=blob.hex(),regs=regs,
            frame_before=frame,frame_after=r.read_bytes(DIR,240).hex(),model_index=len(r.models)-1)
        self.projection['events'].append(event);return event

    def step(self,u,pc,n,user):
        r=self.reader;g=self.projection['geometry']
        if pc==ENTRY:
            need(not self.active and len(self.result)<5 and r.open and r.file==FILE,'five selected native Seek lifetimes')
            original=r.regs();shadows=[]
            if self.driver.seek_variant=='first_cur'and not self.result:
                need(original[:3]==[FILE,12,0]and original[13:15]==[TOP-136,0x200735D]and
                    self.properties()==prop_bytes(g),'first CUR counter after projected initial position equals top')
                u.reg_write(B.R[2],1);shadows=[dict(pc=hex(ENTRY),before=original,after=r.regs(),
                    reason='first Seek origin SET0 toCUR1 only; initial pos equals top, same target hypothesis')]
            self.current=dict(original_entry=original,entry=r.regs(),returned=None,file_before=r.read_bytes(FILE,72).hex(),
                file_after=None,frame_before=r.read_bytes(DIR,240).hex(),frame_after=None,cursor_before=r.cursor,
                cursor_after=None,flow=[],stores=[],reads=[],shadows=shadows)
            self.result.append(self.current);self.active=True
        if self.active and pc==(self.current['entry'][14]&~1):
            pos=struct.unpack('<I',self.properties()[12:])[0]
            need(g['top']<=pos<=g['bottom'],'native Seek actual guest position within authenticated file')
            # Notification from the actual native store, never an expected offset.
            r.cursor=pos-g['top']
            self.current.update(returned=r.regs(),file_after=r.read_bytes(FILE,72).hex(),
                frame_after=r.read_bytes(DIR,240).hex(),cursor_after=r.cursor);self.active=False
        if self.active:
            if ENTRY<=pc<END:self.current['flow'].append(dict(pc=hex(pc),regs=r.regs()))
            self.root_step(u,pc,n,user);return
        self.parent_step(u,pc,n,user)

    def write(self,u,access,address,n,value,user):
        if self.active:
            pc=u.reg_read(UC_ARM_REG_PC)
            need(pc==0x20D843C and address==POSITION and n==4,'Seek native position word is its only write')
            if self.reader.observe:self.current['stores'].append(dict(pc=hex(pc),address=address,bytes=n,
                before=self.reader.read_bytes(address,n).hex(),value=value))
            self.root_write(u,access,address,n,value,user);return
        self.parent_write(u,access,address,n,value,user)

    def read(self,u,access,address,n,value,user):
        pc=u.reg_read(UC_ARM_REG_PC)
        if self.active:
            need(pc in(0x20D83F8,0x20D8404,0x20D8410,0x20D8424,0x20D8430)and n==4 and
                address in(FILE+36,FILE+40,FILE+44),'Seek only reads declared property words')
            self.current['reads'].append(dict(pc=hex(pc),address=address,bytes=n,hex=self.reader.read_bytes(address,n).hex()))
        self.parent_read(u,access,address,n,value,user)

    def service(self,pc):
        r=self.reader;g=self.projection['geometry']
        opened=pc==SEND and self.driver.fast_observer.active and not self.driver.close_observer.active
        if pc==READ:
            before_props=self.properties();file_before=r.read_bytes(FILE,72);fid,top,bottom,pos=struct.unpack('<4I',before_props)
            need((fid,top,bottom)==(g['file_id'],g['top'],g['bottom'])and r.cursor==pos-top and
                r.open and 0<=r.cursor and r.cursor+r.regs()[2]<=g['bytes'],
                'Read consumes actual native Seek position and authenticated physical geometry')
            destination,length=r.regs()[1:3]
            need(destination+length<=FILE or destination>=FILE+72,'Raw Read output cannot overlap its FSFile')
        self.base_service(pc)
        if opened:
            need(r.open and r.cursor==0 and r.archive is not None and sha(r.archive)==g['archive_sha256'],
                'Send6 selected raw archive before property input projection')
            event=self.projected_write('open-property-input',FILE+32,prop_bytes(g));r.models[-1]['property_projection']=event
        elif pc==READ:
            delivered=r.models[-1]
            need(delivered['name']=='FS_ReadFile'and delivered['requested_bytes']==delivered['delivered_bytes']==delivered['result_r0']==length and r.cursor==pos-top+length,'Read projection accepts only complete successful finite reads')
            need(r.read_bytes(FILE,72)==file_before,'Legacy raw Read backend unexpectedly changed FSFile before explicit position projection')
            need(r.cursor<=g['bytes'],'Read delivered cursor stays within physical geometry')
            event=self.projected_write('read-position-result',POSITION,struct.pack('<I',g['top']+r.cursor))
            r.models[-1]['property_projection']=event


class Driver(H.Driver):
    def __init__(self,*args,variant='current',**kwargs):
        need(variant in('current','first_cur'),'finite Seek origin controls')
        super().__init__(*args,variant='current',**kwargs);self.seek_variant,self.seek_result,self.fs_projection_result=variant,None,None

    def start_pp(self):
        super().start_pp();regs=self.regs();before=self.read_bytes(0x2000000,0x400000)
        self.seek_observer=SeekObserver(self,self.pp_reader);self.seek_result=self.seek_observer.result
        self.fs_projection_result=self.seek_observer.projection
        need(regs==self.regs()and before==self.read_bytes(0x2000000,0x400000),'Seek/projection attachment changed guest state')


root_step=binding(H.root_step,dict(SDK=SDK))
run_case,RUN_RECIPE=A.rewrite(H,PP.V,'run_case',A.edits(H.RUN_RECIPE)+[
    ('return dict(fs_close=','return dict(seek=driver.seek_result,fs_projection=driver.fs_projection_result,fs_close=',1)],
    dict(Driver=Driver,A=PP.A,TOP=TOP,NAME_ARENA=PP.X.NAME_ARENA,NAME_END=PP.X.NAME_END),'message_caller')


def source_identities():
    result=H.source_identities()
    for p in(__file__,A.__file__):result[str(Path(p).resolve().relative_to(P.SOURCE))]=sha(Path(p).read_bytes())
    return result


def resources(model,raw,language):
    data=I.resources(model,raw,language);g=geometry(raw);o=data['pp_reader']['11']['oracle']
    need(o['file_id']==g['file_id']and o['archive_rom_offset']==g['top']and o['archive_bytes']==g['bytes']and
        o['archive_sha256']==g['archive_sha256'],'Seek independent resource and physical FAT geometry agree')
    data['fs_geometry']=g;return data


def projected_file_after(blob,status,g):
    out=bytearray(F.file_after(blob,status));out[32:48]=prop_bytes(g);return bytes(out)


def projected_open_after(blob,status,g):
    out=bytearray(F.open_after(blob,status));out[FILE-ID+32:FILE-ID+48]=prop_bytes(g);return bytes(out)


def context_bindings():
    init,p1=A.rewrite(H,I,'require_init',A.edits(V.CONTEXT_RECIPES[0])+[
        ("len(p['models']) == 15","len(p['models']) == 10",1)],dict(ID=ID),'fs_init_caller')
    opened,p2=A.rewrite(H,O,'require_open',A.edits(F.CONTEXT_RECIPES[1])+[
        ("before[16:],0 if r['variant']=='status_zero' else 16)",
         "before[16:],0 if r['variant']=='status_zero' else 16,data['fs_geometry'])",1)],
        dict(require_init_native=init,expected_open=F.predict_open,DIR=DIR,open_after=projected_open_after),'fs_open_caller')
    converted=binding(V.require_convert,dict(require_open=opened))
    fast,p3=A.rewrite(H,F,'require_fast',[
        ('file_after(prior_file,status)',"projected_file_after(prior_file,status,data['fs_geometry'])",2),
        ("need(image==after and out['stores']", "image[FILE-DIR+32:FILE-DIR+48]=prop_bytes(data['fs_geometry'])\n    need(image==after and out['stores']",1)],
        dict(require_convert=converted,projected_file_after=projected_file_after,prop_bytes=prop_bytes),'fs_fast_caller')
    closed,p4=A.rewrite(H,H,'require_close',[
        ('H.require_fast(r,data)','require_fast(r,data)',1),
        ("struct.pack_into('<I',before,TOP-116-DIR,resource['oracle']['member_bytes'])",
         "struct.pack_into('<I',before,POSITION-DIR,data['fs_geometry']['top']+resource['oracle']['member_archive_offset']+resource['oracle']['member_bytes'])\n    struct.pack_into('<I',before,TOP-116-DIR,resource['oracle']['member_bytes'])",1)],
        dict(require_fast=fast,POSITION=POSITION),'fs_close_caller')
    return init,opened,converted,fast,closed,[p1,p2,p3,p4]


require_init,require_open,require_convert,require_fast,require_close,CONTEXT_RECIPES=context_bindings()


def off_bindings():
    parent=binding(V.require_parent_off,dict(require_open=require_open))
    converted=binding(V.require_off_pair,dict(require_parent_off=parent,require_convert=require_convert))
    fast=binding(F.require_off_pair,dict(convert_off=converted,require_fast=require_fast))
    closed,recipe=A.rewrite(H,H,'require_off_pair',[
        ('H.require_off_pair(on,off,data)','require_fast_off(on,off,data)',1)],
        dict(require_fast_off=fast,require_close=require_close),'fs_close_caller')
    return closed,recipe


require_parent_off,OFF_RECIPE=off_bindings()


def read_specs(data):
    o=data['pp_reader']['11']['oracle'];local=TOP-136
    return ((12,local+20,2),(o['btaf']+4,local+20,4),(o['btaf']+8,local+8,2),
        (o['btnf']+4,local+20,4),(o['btaf']+12+310*8,local+16,4),
        (o['btaf']+16+310*8,local+12,4),(o['member_archive_offset'],DEST,o['member_bytes']))


def seek_specs(data):
    o=data['pp_reader']['11']['oracle'];mon=PP.MON
    return ((12,0x200735D,[0x210F198,310,mon,0],0),
        (o['btaf']+4,0x2007373,[o['btaf'],310,mon,0],14),
        (o['btnf']+4,0x20073A1,[o['btaf'],310,o['btnf'],0],26),
        (o['btaf']+12+310*8,0x20073BB,[o['btaf']+12,310,o['btnf'],o['btnf_bytes']],o['btnf']+8),
        (o['member_archive_offset'],0x20073E3,[o['btaf']+12,310,o['btnf'],o['btnf_bytes']],o['btaf']+20+310*8))


def cmp_flags(a,b):
    result=(a-b)&0xFFFFFFFF
    return ((result&0x80000000)|((result==0)<<30)|((a>=b)<<29)|
        (((a^b)&(a^result)&0x80000000)>>3)|0x1F)


def expected_seek(r,data,index,entry,origin=0):
    need(index in range(5)and origin in(0,1)and(origin==0 or index==0),'finite Seek path prediction')
    offset,lr,saved,previous=seek_specs(data)[index];g=data['fs_geometry'];clobber=r['pp_clobber']
    want=[FILE,offset,origin,0xA5000003 if clobber else 0]+saved+list(PP.N.COOKIES[4:])+[
        0xA500000C if clobber else 0,TOP-136,lr,0x1F]
    need(len(entry)==16 and all(type(v)is int and 0<=v<2**32 for v in entry)and entry[:15]==want[:15]and
        entry[15]&0x0FFFFFFF==0x1F,'Seek source caller ABI; incoming NZCV recorded but semantically overwritten by first CMP')
    regs=list(entry);flow=[];positions=SET_PCS if origin==0 else CUR_PCS
    for pc in positions:
        flow.append(dict(pc=hex(pc),regs=list(regs)))
        if pc==ENTRY:regs[15]=cmp_flags(regs[2],0)
        elif pc==0x20D83E4:regs[15]=cmp_flags(regs[2],1)
        elif pc==0x20D83F8:regs[2]=g['top']
        elif pc==0x20D8404:regs[2]=g['top']+previous
        elif pc in(0x20D83FC,0x20D8408):regs[1]=(regs[1]+regs[2])&0xFFFFFFFF
        elif pc==0x20D8424:regs[2]=g['top']
        elif pc==0x20D8428:regs[15]=cmp_flags(regs[1],regs[2])
        elif pc==0x20D8430:regs[2]=g['bottom']
        elif pc==0x20D8434:regs[15]=cmp_flags(regs[1],regs[2])
        elif pc==0x20D8440:regs[0]=1
        elif pc==0x20D8444:regs[15]|=32
    need(g['top']<g['top']+offset<g['bottom']and regs[1]==g['top']+offset,
        'Seek finite current geometry has no overflow or active clamp')
    return dict(flow=flow,returned=regs,offset=offset,previous=previous)


def native_binding():
    removes=[" ('FS_SeekFile',0x200735D,[12,0],[path,310,c6,c7],None),\n",
        " ('FS_SeekFile',0x2007373,[o['btaf']+4,0],[o['btaf'],310,c6,c7],None),\n",
        " ('FS_SeekFile',0x20073A1,[o['btnf']+4,0],[o['btaf'],310,o['btnf'],c7],None),\n",
        " ('FS_SeekFile',0x20073BB,[o['btaf']+12+310*8,0],[o['btaf']+12,310,o['btnf'],o['btnf_bytes']],None),\n",
        " ('FS_SeekFile',0x20073E3,[o['member_archive_offset'],0],[o['btaf']+12,310,o['btnf'],o['btnf_bytes']],None),\n"]
    edits=A.edits(H.NATIVE_RECIPE)+[(s,'',1)for s in removes]+[
        ("len(r['models'])==15","len(r['models'])==10",1),
        ('fifteen native FS boundary calls','ten modeled FS boundaries plus five native seeks',1),
        ('  pc=next(a for a,v in SDK.items() if v==name);',
         "  if index in (2,3,5,6,8):need(read is not None,'native Seek source consumer index');cursor=read[0]\n  pc=next(a for a,v in SDK.items() if v==name);",1),
        ('cursor=0;opened=True',"cursor=0;opened=True;model_writes.append((file+32,prop_bytes(GEOMETRY)))",1),
        ("if dest!=DEST:model_writes.append((dest,blob))",
         "if dest!=DEST:model_writes.append((dest,blob))\n   model_writes.append((file+44,struct.pack('<I',GEOMETRY['top']+cursor)))",1),
        ('store(0x20073EE,local+20,4,size)',
         "for offset in (12,o['btaf']+4,o['btnf']+4,o['btaf']+12+310*8,o['member_archive_offset']):store(0x20D843C,file+44,4,GEOMETRY['top']+offset)\n store(0x20073EE,local+20,4,size)",1),
        ('len(expected)==38+len(STORES)+len(INNER_STORES)','len(expected)==43+len(STORES)+len(INNER_STORES)',1)]
    return A.rewrite(H,R,'require_case',edits,
        dict(TOP=TOP,DEST=DEST,STOP=STOP,COOKIES=PP.COOKIES,IP=PP.IP,STORES=I.STORES,INNER_STORES=I.STORES,
            SDK=SDK,DIR=DIR,ID=ID,SP=F.SP,CLOSE_SP=H.SP,ARC=ARC,FAST_VALUE=1,FIND_VALUE=1,STATUS=16,
            CLOSE_VALUE=1,CLOSE_ARC=0,EXPECTED_HOOKS=277,EXPECTED_PC_COUNT=201,GEOMETRY=None,prop_bytes=prop_bytes),'narc_reader')


require_native,NATIVE_RECIPE=native_binding()


def checked_projection(event,kind,address,blob,frame,model_index,model):
    i=address-DIR;before=bytes(frame[i:i+len(blob)]);after=bytearray(frame);after[i:i+len(blob)]=blob
    need(event['kind']==kind and event['address']==address and event['bytes']==len(blob)and
        event['before']==before.hex()and event['after']==blob.hex()and event['frame_before']==bytes(frame).hex()and
        event['frame_after']==after.hex()and event['model_index']==model_index and model['property_projection']==event,
        'Property projection exact before/after/full240 frame and model occurrence')
    regs=event['regs'];need(len(regs)==16 and all(type(v)is int and 0<=v<2**32 for v in regs)and regs[:4]==[model['result_r0']]+model['return_volatile'][:3]and
        regs[4:12]==model['return_saved']and regs[12]==model['return_volatile'][3]and
        regs[13:15]==[model['return_sp'],int(model['lr'],16)],'Property projection preserves declared full ABI values')
    return after


def read_to_close_entry(regs):
    need(len(regs)==16 and all(type(v)is int and 0<=v<2**32 for v in regs),'Read-to-Close full unsigned32 register vector')
    result=list(regs);result[0]=FILE;result[14]=0x2007409;result[15]&=~32
    return result


def require_seek_projection(r,data,counter=False):
    g=data['fs_geometry'];p=r['pp_reader'];project=r['fs_projection'];calls=r['seek'];models=p['models']
    need(project['geometry']==g and len(project['events'])==8 and len(calls)==5 and len(models)==10 and
        r['send_value']==r['find_value']==r['open_fast_value']==1,'Seek five calls and eight declared field projection events')
    require_close(r,data)
    # Reconstruct the first projection at Send6 before native Fast's final stat store.
    start=bytearray.fromhex(r['fs_fast']['frame_before'])
    sequence=[(TOP-168+4*i,v)for i,v in enumerate((FILE,ARC,140,0))]+[
        (F.SP+4*i,v)for i,v in enumerate((FILE,0x20D82A4))]+[(FILE+off,v)for off,v in((8,ARC),(48,ARC),(52,140))]
    for address,value in sequence:struct.pack_into('<I',start,address-DIR,value)
    first=project['events'][0];need(first['regs']==models[1]['returned'],'Send6 property projection leaves actual model return vector intact')
    current=checked_projection(first,'open-property-input',FILE+32,prop_bytes(g),start,1,models[1])
    need(first['regs'][15]&0x0FFFFFFF==0x1F,'Send6 projection ARM mode retained')
    struct.pack_into('<I',current,FILE+12-DIR,16)
    need(current.hex()==r['fs_fast']['frame_after'],'Fast native status update follows property projection at its actual lifetime')
    gates={0:0,1:1,3:2,4:3,6:4};raw=data['pp_reader']['11']['raw']
    for ordinal,(position,destination,size)in enumerate(read_specs(data)):
        if ordinal in gates:
            index=gates[ordinal];call=calls[index];origin=1 if counter and index==0 else 0
            want=expected_seek(r,data,index,call['entry'],origin)
            original=list(call['entry']);original[2]=0
            need(call['original_entry']==original and call['flow']==want['flow']and call['returned']==want['returned'],
                'Seek original caller, actual origin path, complete post-CMP flow and native return')
            need(call['frame_before']==current.hex()and call['file_before']==bytes(current[FILE-DIR:FILE-DIR+72]).hex()and
                current[FILE-DIR+32:FILE-DIR+48]==prop_bytes(g,g['top']+want['previous'])and
                call['cursor_before']==want['previous'],'Seek exact current frame/property input from preceding model/native event')
            loaded=(0x20D8404,FILE+44,g['top']+want['previous'])if origin else(0x20D83F8,FILE+36,g['top'])
            reads=[dict(pc=hex(pc),address=a,bytes=4,hex=struct.pack('<I',v).hex())for pc,a,v in
                (loaded,(0x20D8424,FILE+36,g['top']),(0x20D8430,FILE+40,g['bottom']))]
            need(call['reads']==reads,'Seek actual native property loads and physical coordinate origin')
            stores=[dict(pc='0x20d843c',address=POSITION,bytes=4,before=bytes(current[POSITION-DIR:POSITION-DIR+4]).hex(),
                value=g['top']+want['offset'])]
            struct.pack_into('<I',current,POSITION-DIR,g['top']+want['offset'])
            need(call['stores']==(stores if r['observe']else[])and call['file_after']==bytes(current[FILE-DIR:FILE-DIR+72]).hex()and
                call['frame_after']==current.hex()and call['cursor_after']==want['offset'],
                'Seek one actual native store and host cursor derived from its guest result')
            shadows=[]
            if origin:
                post=list(original);post[2]=1;shadows=[dict(pc=hex(ENTRY),before=original,after=post,
                    reason='first Seek origin SET0 toCUR1 only; initial pos equals top, same target hypothesis')]
            need(call['shadows']==shadows,'Seek first-origin-only register shadow with complete unchanged caller prestate')
        if ordinal==6:struct.pack_into('<I',current,TOP-116-DIR,size)
        model=models[ordinal+2]
        need(model['name']=='FS_ReadFile'and model['position']==model['cursor_before']==position and
            model['destination']==destination and model['requested_bytes']==model['delivered_bytes']==model['result_r0']==size and
            model['cursor_after']==position+size and model['delivered_sha256']==sha(raw[position:position+size]),
            'Raw Read consumes native Seek cursor and delivers the independently selected whole-file slice')
        if destination!=DEST:current[destination-DIR:destination-DIR+size]=raw[position:position+size]
        need(current[POSITION-DIR:POSITION-DIR+4]==struct.pack('<I',g['top']+position),
            'Projected Read position is the actual preceding native/read position')
        event=project['events'][ordinal+1]
        current=checked_projection(event,'read-position-result',POSITION,struct.pack('<I',g['top']+position+size),
            current,ordinal+2,model)
        need(event['regs'][15]&0x0FFFFFFF==0x3F and(not r['pp_clobber']or event['regs'][15]==0xA000003F),
            'Read property result preserves Thumb mode and declared volatile clobber flags')
    need(read_to_close_entry(project['events'][-1]['regs'])==r['fs_close']['entry'],'Last Read to Close full16 source bridge preserves actual NZCV through ADDsp/BLX')
    need(current.hex()==r['fs_close']['frame_before'],'Complete Seek/Read projection timeline reaches actual native Close preimage')
    return True


def seek_code(q,counter=False):
    starts=set(SET_PCS)|set(CUR_PCS)if counter else set(SET_PCS)
    return {**H.close_code(q),**{pc:value for pc,value in q['fs_seek_code'].items()if pc in starts}}


def require_case(r,data,q):
    need(r['variant']=='current'and r['pp_shadows']==[],'positive Seek has no origin shadow')
    require_seek_projection(r,data);PP.require_pp_context(r,data)
    native=A.clone(require_native,dict(GEOMETRY=data['fs_geometry'],CLOSE_VALUE=r['close_value']))
    native(r['pp_reader'],data['pp_reader'],seek_code(q),T.expected(data['constructor'],r['plus'])[0]['ot_draws'][-1])
    PP.require_earlier(r,data,q);return True


def require_off_pair(on,off,data):
    parent=require_parent_off(on,off,data);require_seek_projection(on,data);require_seek_projection(off,data)
    need(on['variant']==off['variant']=='current'and on['fs_projection']==off['fs_projection']and
        all(b['stores']==[]and {k:v for k,v in a.items()if k!='stores'}=={k:v for k,v in b.items()if k!='stores'}
            for a,b in zip(on['seek'],off['seek'])),'Seek OFF actual cursor/positions/projection/timeline equal, only native store logs disabled')
    return dict(neutral=True,parent=parent,scope='Five native pos stores and eight model property writes equal; no new mask beyond inherited heap1124')


def counter_record(r,data,q):
    disguised=copy.deepcopy(r);disguised['variant']='current';disguised['seek'][0]['shadows']=[]
    try:require_case(disguised,data,q)
    except ValueError as error:return dict(variant=r['variant'],result=r,rejection=str(error),tag_disguised=True)
    raise ValueError('Seek CUR counter accepted')


def require_counter(counter,normal,data,q):
    require_case(normal,data,q);r=counter['result']
    need(counter['variant']==r['variant']=='first_cur'and r['plus']==normal['plus']==1 and
        r['seed']==normal['seed']==0x12345678 and r['poison']==normal['poison']==0xC7 and r['observe']is True and
        r['pp_clobber']is False and r['close_value']==normal['close_value']==1 and r['pp_shadows']==[],
        'Seek counter finite source fixture and first-origin-only policy')
    require_seek_projection(r,data,True);PP.require_pp_context(r,data)
    a,b=normal['pp_reader'],r['pp_reader']
    need({k:v for k,v in a.items()if k not in('instructions','observed_pcs')}==
        {k:v for k,v in b.items()if k not in('instructions','observed_pcs')}and
        {k:v for k,v in normal.items()if k not in('seek','pp_reader','variant','instructions')}==
        {k:v for k,v in r.items()if k not in('seek','pp_reader','variant','instructions')},
        'CUR counter complete source prestate, all memory/model/property/caller outputs remain identical')
    allowed={'entry','flow','reads','shadows'}
    need(r['seek'][1:]==normal['seek'][1:]and
        {k:v for k,v in r['seek'][0].items()if k not in allowed}==
        {k:v for k,v in normal['seek'][0].items()if k not in allowed}and
        r['instructions']==normal['instructions']+2,
        'Only first Seek origin path/load/shadow differs; same five native positions and qualified two-hook delta')
    native=A.clone(require_native,dict(GEOMETRY=data['fs_geometry'],EXPECTED_HOOKS=279,EXPECTED_PC_COUNT=206))
    native(b,data['pp_reader'],seek_code(q,True),T.expected(data['constructor'],1)[0]['ot_draws'][-1])
    replay=copy.deepcopy(r);replay['variant']='current';PP.require_earlier(replay,data,q)
    actual=counter_record(r,data,q)
    need(counter['tag_disguised']is True and counter['rejection']==actual['rejection']==
        'Seek source caller ABI; incoming NZCV recorded but semantically overwritten by first CMP',
        'CUR counter specifically rejected as positive SET caller ABI despite same final output')
    return True

def analyze(rom, language, objects, strategy_object, readback_only=False):
    import mmap, unicorn
    R.W.require_host_budget(); sources = source_identities()
    model = P.G.S.SHARED.read_current(rom, language)
    with rom.open('rb') as f, mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as raw:
        q, proof = qualify(model,raw,language,objects,strategy_object)
        result = dict(schema='trainer31-native-fs-seek-v1',language=language,input=model['record'],
            source_sha256=sources,proof=proof,recipes=[RUN_RECIPE,*CONTEXT_RECIPES,OFF_RECIPE,NATIVE_RECIPE],namespace_bindings=BINDINGS,cpu_executed=False,
            conditional_policy=dict(unicorn_version=unicorn.__version__,cpu_model=17,
                false_EQ_hook=True,fast_false_EQ_hooks=8,close_false_EQ_hooks=1,seek_false_MOV_hooks_per_SET=2,scope='code-hook delivery; false ARM effects remain suppressed'))
        if not readback_only:
            data = resources(model,raw,language)
            positives, guards, controls, off, counters = [], [], [], [], []
            for plus in (0,1):
                for seed in (0x12345678,0x12345679):
                    r = run_case(model,raw,language,q,data,plus,seed)
                    require_case(r,data,q); positives.append(r)
                    print(language,'native Seek caller',plus,hex(seed),'verified',flush=True)
                r = run_case(model,raw,language,q,data,plus,0x12345678,observe=False)
                off.append(dict(result=r,proof=require_off_pair(positives[-2],r,data)))
            normal = next(r for r in positives if r['plus']==1 and r['seed']==0x12345678)
            r = run_case(model,raw,language,q,data,1,0x12345678,poison=0x39)
            require_case(r,data,q); need(r['mon_hex']==normal['mon_hex'],'Seek alternate preimage fill changes party'); guards.append(r)
            for kwargs in (dict(pp_clobber=True),dict(close_value=2)):
                r = run_case(model,raw,language,q,data,1,0x12345678,**kwargs)
                require_case(r,data,q)
                need(r['mon_hex']==normal['mon_hex'] and r['prefix']==normal['prefix'] and
                     r['seed_after']==normal['seed_after'] and r['functional_ram_sha256']==normal['functional_ram_sha256'] and
                     r['pp_reader']['ram_sha256']==normal['pp_reader']['ram_sha256'],
                     'Seek lower volatile/noncanonical truthy policy preserves output and phase RAM')
                controls.append(r)
            r = run_case(model,raw,language,q,data,1,0x12345678,variant='first_cur')
            counter = counter_record(r,data,q); require_counter(counter,normal,data,q); counters.append(counter)
            result.update(cpu_executed=True,positives=positives,guards=guards,volatile_controls=controls,
                observer_off=off,counters=counters,resources=dict(pp=data['pp_reader']['11']['oracle']),
                limits=['Initialized trainer31 caller and selected custom PP310 file lifetime only',
                        'Native Init/Open/Convert/Fast/Seek/Close; FindPath/SendCommand/Read are explicit models',
                        'Opaque ARC token is not native FSArchive state; no invented FSFile fields',
                        'Counter first origin SET0 toCUR1 with initial pos==top; same position and output, different native branch path',
                        'Exact240-byte frame/56-byte actual guard including8 unmasked readonly bytes; guestglobal560 within608; heap1124B OFF projection only',
                        'Recovered assembly bytes do not reconstruct original SDK compiler provenance',
                        'Only modeled prop16/open and pos4/read effects; known arg/stat/command/queue SDK effects excluded',
                        'Incoming Seek NZCV recorded, not source-attributed; first CMP overwrites them',
                        'No natural encounter/full battle/UI/SAVE/cold/hardware or performance claim'])
        need(source_identities()==sources,'Seek sources changed during campaign'); R.W.require_host_budget()
    return result


def main():
    import argparse,json,gzip
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('rom','objects','strategy-object','json'): parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--language',choices=('EN','IT'),required=True)
    parser.add_argument('--readback-only',action='store_true')
    args = parser.parse_args()
    try:
        need(not args.json.exists() and not args.json.is_symlink() and P.SOURCE not in args.json.resolve().parents,
             'fresh private output outside source required')
        result = analyze(args.rom,args.language,args.objects,args.strategy_object,args.readback_only)
        payload = json.dumps(result,separators=(',',':')).encode(); need(len(payload)<=32*1024**2,'Seek expanded report budget')
        blob = gzip.compress(payload,mtime=0) if args.json.suffix=='.gz' else payload
        need(len(blob)<=8*1024**2,'Seek stored report budget')
        args.json.parent.mkdir(parents=True,exist_ok=True)
        with args.json.open('xb')as f:f.write(blob)
    except ValueError as error: parser.exit(2,str(error)+'\n')
    print(args.language,'Seek readback verified' if args.readback_only else 'native Seek caller and explicit lower models verified')


if __name__=='__main__':main()
