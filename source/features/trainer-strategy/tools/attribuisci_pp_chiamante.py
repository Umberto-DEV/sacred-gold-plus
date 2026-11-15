#!/usr/bin/env python3
"""Attribute native stack-destination move PP to the first custom slot in one CPU.

The earlier default-learnset occurrence of move310 is a different caller.
Only the selected post-CreateMon read is composed; other readers stay explicit.
"""
from pathlib import Path
import importlib.util,types,struct,json,gzip,mmap,copy,gc,sys

def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
H=load('pp_friendship_parent',Path(__file__).with_name('attribuisci_amicizia_chiamante.py'))
A=load('pp_reader_profile',Path(__file__).parents[1]/'test/pp_narc_bench.py');A.bind(H)
G,J,Z,Y,X,R,V,U,B,T,P,Q,N=H.G,H.J,H.Z,H.Y,H.X,H.R,H.V,H.U,H.B,H.T,H.P,H.Q,H.N
need,sha,OUTER,INNER,MON=H.need,H.sha,H.OUTER,H.INNER,H.MON
TOP=DEST=INNER-224
STOP,IP=0x2073320,0
COOKIES=[5,0,MON,0]+list(N.COOKIES[4:])
ALLOCATIONS=tuple((B.ARENA+a,n) for a,n in ((0,108),(128,236),(384,44),(448,404),(872,44),(936,44),(1000,44),(1064,44),(1128,44),(1192,44),(1256,44),(1320,56),(1392,44),(1456,44)))
CANARIES=tuple(span for a,n in ALLOCATIONS for span in ((a-8,8),(a+n,8)))
DEAD=ALLOCATIONS[2:]
PROJECTION=[(a,a+n) for a,n in CANARIES+DEAD]
FLOW=(0x20714E8,0x20714F0,0x207150A,0x207150E,0x2071516,0x207332C,0x2073314,0x20733B0,0x2073320,0x2073354,0x2073390,0x2073392,0x2073328,0x207333C,0x2073348,0x207334C,0x207151A,0x207151C,0x2071526,0x206ED70,0x207152A,0x2073A36)
FLOW_SP=(152,152,184,184,184,184,200,224,224,224,224,224,224,200,200,200,184,184,184,184,184,152)
from unicorn.arm_const import UC_ARM_REG_PC

def neighbors_before(r):return r.read_bytes(TOP+16,16)==r.before[TOP+16-0x2000000:TOP+32-0x2000000]


def resources(raw):
 import ndspy.narc
 members,receipt=P.RAW.raw_archive(raw,'a/0/1/1');fat=struct.unpack_from('<I',raw,0x48)[0];start,end=struct.unpack_from('<II',raw,fat+8*receipt['file_id']);archive=bytes(raw[start:end]);member=bytes(members[310]);need(receipt['file_id']==140 and len(members)==471 and len(archive)==11356 and sha(archive)=='beed8ddf861e575b9c38dfa65a6c0c51fb237305ddd73c393f5e2009fbc75260' and ndspy.narc.NARC(archive).files[310]==member,'move whole archive independent raw/ndspy identity');btaf=struct.unpack_from('<H',archive,12)[0];btaf_n=struct.unpack_from('<I',archive,btaf+4)[0];btnf=btaf+btaf_n;btnf_n=struct.unpack_from('<I',archive,btnf+4)[0];gmif=btnf+btnf_n;lo,hi=struct.unpack_from('<II',archive,btaf+12+310*8);position=gmif+8+lo;need((btaf,btaf_n,btnf,btnf_n,gmif,lo,hi,position)==(16,3780,3796,16,3812,4960,4976,8780) and len(member)==16 and sha(member)=='85ac8d2ffc1e263ba41dfed64ea9b07613bd3fe76e8a68ef13e93394179dc5c8' and member[6]==15 and archive[position:position+16]==member and start+position==receipt['member_rom_offsets'][310],'selected move16 independent metadata/member/PP')
 return {'11':dict(raw=archive,path='a/0/1/1',member=member,oracle=dict(narc=11,path='a/0/1/1',file_id=140,archive_rom_offset=start,archive_bytes=end-start,archive_sha256=sha(archive),member=310,member_bytes=16,member_sha256=sha(member),pp_offset=6,pp=15,member_archive_offset=position,member_rom_offset=start+position,btaf=btaf,btaf_bytes=btaf_n,btnf=btnf,btnf_bytes=btnf_n,gmif=gmif,count=471,start=lo,end=hi))}

def qualify(model,raw,*args):
 q,proof=H.qualify(model,raw,*args);view=P.G.S.SHARED.gifts_audit.Arm9View(raw);extra=[]
 for address,n in ((0x210F23C,4),(0x210F198,8)):
  blob=view.read(address,n);need(blob==P.G.piece(model['segments'],address,n),'PP route raw/section agreement');extra.append(dict(ram=hex(address),bytes=n,rom_offset=hex(view.offset(address,n)),sha256=sha(blob)))
 need(view.read(0x210F23C,4)==struct.pack('<I',0x210F198) and view.read(0x210F198,8)==b'a/0/1/1\0' and view.read(0x207336E,2)==struct.pack('<H',42),'PP path and selected attr5 jump-table data');need(all(pc in q['body_code'] for pc in FLOW+(0x206F0FE,)) and 0x207336E not in q['body_code'],'PP observer points qualified; switch data never admitted as instructions');q['pp_data']=tuple(R.DATA)+tuple((a,n,sha(view.read(a,n))) for a,n in ((0x210F23C,4),(0x210F198,8)));proof['native_pp_route']=extra;proof['native_pp_field']=dict(attribute=5,field_offset=6,dispatch_row_ram='0x207336e',dispatch_row_bytes=2,target_ram='0x2073390',source='move.c GetMoveAttr/GetMoveTblAttr/GetMoveMaxPP; original native MW reconstruction unavailable');return q,proof

def source_identities():
 result=H.source_identities()
 for p in (__file__,A.__file__):result[str(Path(p).resolve().relative_to(P.SOURCE))]=sha(Path(p).read_bytes())
 return result

def bindings():
 init,p1=A.rewrite(R,'Reader.__init__',[("narc in (55,56)","narc==11",1)],{},'narc_reader')
 snapshot,p2=A.rewrite(R,'Reader.run',[("self.setup();self.u.emu_start(ENTRY|1,STOP,count=20001);","",1),("list(N.COOKIES)","list(COOKIES)",1),("self.read_bytes(DEST-16,16)==b'\\xA5'*16 and self.read_bytes(DEST+size,124-size)==b'\\xA5'*(124-size)","neighbors_before(self)",1),("self.read_bytes(TOP-192,56)==bytes([self.fill])*56","self.read_bytes(TOP-192,56)==self.before[TOP-192-0x2000000:TOP-136-0x2000000]",1),("member=31","member=310",1)],dict(TOP=TOP,DEST=DEST,STOP=STOP,COOKIES=COOKIES,neighbors_before=neighbors_before),'narc_reader')
 native_edits=[(e['before'],e['after'].replace('355','310').replace('narc==2','narc==11').replace('0x210F1E0','0x210F198'),e['count']) for e in J.RECIPES[2]['edits']];native,p3=A.rewrite(R,'require_case',native_edits,dict(TOP=TOP,DEST=DEST,STOP=STOP,COOKIES=COOKIES,IP=IP),'narc_reader')
 run,p4=A.rewrite(V,'run_case',A.inherited(3,[("friendship_clobber=False):","friendship_clobber=False,pp_clobber=False):",1),("friendship_clobber=friendship_clobber)","friendship_clobber=friendship_clobber,pp_clobber=pp_clobber)",1),("return dict(friendship_reader=","return dict(pp_reader=driver.pp_result,pp_binding=driver.pp_binding,pp_flow=driver.pp_flow,pp_stores=driver.pp_stores,pp_checkpoint=driver.pp_checkpoint,pp_shadows=driver.pp_shadows,pp_clobber=driver.pp_clobber,friendship_reader=",1)]),dict(Driver=Driver,A=A,NAME_ARENA=X.NAME_ARENA,NAME_END=X.NAME_END),'message_caller')
 edits=A.inherited(4);i=next(i for i,e in enumerate(edits) if '+158' in e[0]);old,new,count=edits[i];edits[i]=(old,new.replace('+157',"+r['pp_reader']['instructions']+157"),count);parent,p5=A.rewrite(V,'require_case',edits,dict(A=A,V=V),'message_caller');names,p6=A.rewrite(X,'require_case',[],dict(require_parent=parent),'species_caller')
 dispatch,p7=A.rewrite(Y,'require_ctor_dispatch',A.inherited(6,[("expected_count=184+2*r['plus']","expected_count=183+2*r['plus']",1),("11:79+2*r['plus']","11:78+2*r['plus']",1)]),{},'header_caller')
 friendship,p8=A.rewrite(H,'require_friendship_context',[("value=35):","value=35,expected_create_packet=None):",1),("(transient if i<3 else r['mon_hex'][0])","(expected_create_packet if i==0 and expected_create_packet is not None else transient if i<3 else r['mon_hex'][0])",1)],{},'friendship_caller')
 return init,snapshot,native,run,names,dispatch,friendship,[p1,p2,p3,p4,p5,p6,p7,p8]

def bind_reader(driver):
 namespace=dict(vars(R));bound=type('PpReader',(R.Reader,),{});namespace.update(TOP=TOP,DEST=DEST,STOP=STOP,Reader=bound,DATA=driver.qualified['pp_data'])
 for name,method in vars(R.Reader).items():
  if isinstance(method,types.FunctionType):
   fn=types.FunctionType(method.__code__,namespace,method.__name__,method.__defaults__,method.__closure__);fn.__kwdefaults__=method.__kwdefaults__;setattr(bound,name,fn)
 fn=types.FunctionType(reader_init.__code__,{**reader_init.__globals__,**namespace},reader_init.__name__,reader_init.__defaults__,reader_init.__closure__);fn.__kwdefaults__=reader_init.__kwdefaults__;bound.__init__=fn
 r=bound(dict(segments=driver.bench.segments),driver.qualified['header_code'],driver.data['pp_reader'],11,fill=driver.poison,observe=driver.observe,clobber=driver.pp_clobber,variant='skip_close' if driver.pp_variant=='pp_skip_close' else 'current');r.u=driver.u;r.entry=r.regs();r.before=r.read_bytes(0x2000000,0x400000);return r

class Driver(H.Driver):
 latest=None
 def __init__(self,*args,pp_clobber=False,**kwargs):
  variant=kwargs.pop('variant','current');need(variant in ('current','pp_skip_close','pp_one') and type(pp_clobber)is bool,'finite custom PP controls');super().__init__(*args,variant='current',**kwargs);Driver.latest=self;self.pp_variant=variant;self.pp_clobber=pp_clobber;self.pp_reader=None;self.pp_active=False;self.pp_result=None;self.pp_binding=None;self.pp_flow=[];self.pp_flow_open=False;self.pp_flow_done=False;self.pp_shadows=[];self.pp_stores=[];self.pp_setter_open=False;self.pp_checkpoint=None
 def start_pp(self):
  regs=self.regs();need(self.pp_flow_open and not self.pp_flow_done and not any((self.friendship_active,self.growth_active,self.personal_active,self.prefix_active,self.header_active,self.name_active,self.message_active)) and len(self.friendship_checkpoints)==1 and len(self.name_results)==1 and len(self.events)==44 and regs==[DEST,11,310,0x2007509]+COOKIES+[IP,TOP,STOP|1,0x3F],'first CUSTOM PP reader actual occurrence/stack ABI');caller=self.pp_flow[0]['regs'];need(caller[:3]==[MON,310,0] and caller[13:15]==[INNER-152,0x2073A37],'custom PP source-bound caller entry');pending=self.audit.pending_native;need(not self.observe or (pending and pending[-1]['entry']=='0x20714e8' and pending[-1]['args']==caller[:4] and pending[-1]['lr']=='0x2073a37' and pending[-1]['sp']==INNER-152 and self.audit.pending_service is None),'custom PP observed native caller ownership and no pending SDK');before=self.read_bytes(0x2000000,0x400000);self.pp_reader=bind_reader(self);need(self.pp_reader.u is self.u and self.regs()==regs and before==self.read_bytes(0x2000000,0x400000),'PP observer binding changed CPU/RAM');self.pp_binding=dict(neutral=True,regs=regs,ram_sha256=sha(before),projected_ram_sha256=P.masked_hash(before,PROJECTION),canary_preimages=[dict(address=a,bytes=n,hex=self.read_bytes(a,n).hex()) for a,n in CANARIES],dead_before=[dict(address=a,bytes=n,hex=self.read_bytes(a,n).hex()) for a,n in DEAD],events_before=[list(e) for e in self.events],native_caller=dict(entry='0x20714e8',args=caller[:4],sp=caller[13],lr=hex(caller[14]),saved=caller[4:12]),upper_before=self.read_bytes(TOP+16,16).hex());self.pp_active=True
 def finish_pp(self):
  r=self.pp_reader;self.pp_result=pp_snapshot(r);self.pp_result.update(same_cpu=r.u is self.u,stack_frame_before=r.before[TOP-136-0x2000000:TOP-0x2000000].hex(),stack_guard_before=r.before[TOP-192-0x2000000:TOP-136-0x2000000].hex(),stack_guard_after=self.read_bytes(TOP-192,56).hex(),destination_before=r.before[DEST-0x2000000:DEST-0x2000000+16].hex(),dead_after=[dict(address=a,bytes=n,hex=self.read_bytes(a,n).hex()) for a,n in DEAD],upper_after=self.read_bytes(TOP+16,16).hex(),projected_ram_sha256=P.masked_hash(self.read_bytes(0x2000000,0x400000),PROJECTION));self.pp_active=False
 def step(self,u,pc,n,user):
  if self.pp_active and pc==STOP:self.finish_pp()
  if self.stage=='ctor' and pc==R.ENTRY and self.regs()[1:3]==[11,310] and self.pp_flow_open and self.pp_reader is None:self.start_pp()
  if self.pp_active:
   self.steps+=1;sp=self.regs()[13];need(self.steps<=3000000 and OUTER-608<=sp<=INNER,'custom PP native reader/caller existing stack bound');self.max_stack=max(self.max_stack,OUTER-sp);self.pp_reader.step(u,pc,n,user);return
  if self.stage=='ctor' and not self.pp_flow_done:
   if pc==FLOW[0] and self.regs()[:3]==[MON,310,0] and len(self.friendship_checkpoints)==1:
    need(not self.pp_flow_open and not self.pp_flow and self.word(B.PARTIES+0x1000+4)==0,'single first custom slot after CreateMon and before PartyAdd');self.pp_flow_open=True
   eligible=pc in FLOW and (pc!=0x206ED70 or self.regs()[1]==58)
   if self.pp_flow_open and eligible:
    need(len(self.pp_flow)<len(FLOW) and pc==FLOW[len(self.pp_flow)],'selected custom PP native flow sequence');event=dict(pc=hex(pc),regs=self.regs(),stage=self.stage)
    if pc==0x2073390:event.update(field_address=DEST+6,field_byte=self.read_bytes(DEST+6,1)[0])
    if pc==0x2071526 or pc==0x206ED70:event.update(value_pointer=self.regs()[2],value_byte=self.read_bytes(self.regs()[2],1)[0])
    if pc==0x2071526:self.pp_setter_open=True
    if pc==0x207152A:
     self.pp_setter_open=False;raw=self.read_bytes(MON,236);decoded=T.M.decode(raw);need(decoded['flags']==0 and decoded['checksum_ok'],'actual PP setter return encrypted packet');self.pp_checkpoint=dict(pc=hex(pc),mon_hex=raw.hex(),decoded=decoded,regs=self.regs(),same_cpu=True)
    self.pp_flow.append(event)
    if pc==0x2073A36:self.pp_flow_done=True;self.pp_flow_open=False
  if self.stage=='ctor' and pc==0x2073392 and self.pp_variant=='pp_one' and self.pp_flow_open and not self.pp_shadows:
   before=self.regs();need(before[0]==15 and self.pp_result is not None and self.read_bytes(DEST+6,1)==b'\x0f','PP shadow after actual LDRB from unchanged raw15');super().step(u,pc,n,user);u.reg_write(B.R[0],1);after=self.regs();expected=list(before);expected[0]=1;need(after==expected,'PP shadow changes only loaded R0');self.pp_shadows.append(dict(pc=hex(pc),register='r0',before=before,after=after,reason='first custom PP15 to valid1 after native LDRB; raw MoveTbl and default learnset unchanged'));return
  super().step(u,pc,n,user)
 def read(self,u,access,address,n,value,user):
  if self.pp_active:self.pp_reader.read(u,access,address,n,value,user);return
  super().read(u,access,address,n,value,user)
 def write(self,u,access,address,n,value,user):
  if self.pp_active:self.pp_reader.write(u,access,address,n,value,user);return
  if self.stage=='ctor' and self.pp_setter_open and u.reg_read(UC_ARM_REG_PC)==0x206F0FE:
   pid=self.word(MON);order=B.PERMUTATIONS[((pid>>13)&31)%24];target=MON+8+32*order.index(1)+8;need(n==1 and address==target,'custom PP actual slot0 byte store address');self.pp_stores.append(dict(pc='0x206f0fe',address=address,bytes=n,before=self.read_bytes(address,1)[0],value=value,regs=self.regs(),header_flags=int.from_bytes(self.read_bytes(MON+4,2),'little')))
  super().write(u,access,address,n,value,user)
reader_init,pp_snapshot,require_pp_native,run_case,require_names,require_ctor_dispatch,require_friendship_context,RECIPES=bindings()

def expected_mail(language):
 need(type(language)is int and language in (2,4),'finite native Mail language');data=bytearray(56);data[5:8]=bytes((language,7,255));data[8:30]=b'\xFF'*22
 for offset in (32,40,48):data[offset:offset+2]=b'\xFF'*2;data[offset+4:offset+8]=b'\xFF'*4
 return bytes(data)

def dead_payloads(data):
 personal=bytes(data['personal_reader']['2']['member']);learnset=bytes(data['constructor']['archives'][33][355]);need(len(learnset)==28,'source selected learnset28 within modeled zero44 allocation');mail=expected_mail(data['constructor']['language']);return [dict(address=a,bytes=n,hex=(data['growth_reader']['3']['member'] if a==G.DEST else learnset+bytes(44-len(learnset)) if a==B.ARENA+1192 else mail if n==56 else personal).hex()) for a,n in DEAD]

def expected_pp_packet(packet,value):
 need(type(value)is int and value in (1,15),'finite PP counter byte');raw=bytearray.fromhex(packet);pid,flags,checksum=struct.unpack_from('<IHH',raw);need(flags==0,'independent PP prediction outside encrypted transaction');blocks=bytearray(B._decrypt(raw[8:136],checksum));order=B.PERMUTATIONS[((pid>>13)&31)%24];blocks[32*order.index(1)+8]=value;new_checksum=sum(struct.unpack('<64H',blocks))&65535;struct.pack_into('<H',raw,6,new_checksum);raw[8:136]=B._decrypt(blocks,new_checksum);need(T.M.decode(bytes(raw))['checksum_ok'],'independent PP packet checksum');return raw.hex()

def require_pp_context(r,data,value=15):
 p=r['pp_reader'];binding=r['pp_binding'];want=T.expected(data['constructor'],r['plus'])[0]
 need(value in (15,1) and p is not None and p['same_cpu']is True and p['narc']==11 and p['member']==310 and p['entry']==[DEST,11,310,0x2007509]+COOKIES+[IP,TOP,STOP|1,0x3F] and p['fill']==r['poison'] and p['clobber']is r['pp_clobber'] and type(r['pp_clobber'])is bool and p['rng_after']==want['ot_draws'][-1],'source-selected custom PP occurrence and complete actual reader context')
 need(binding['neutral']is True and binding['regs']==p['entry'] and binding['ram_sha256']==p['unrelated_ram_sha256'] and binding['canary_preimages']==[dict(address=a,bytes=n,hex=('a5' if r['observe'] else '00')*n) for a,n in CANARIES],'PP neutral binding and28 exact allocation canaries')
 dead=[dict(address=a,bytes=n,hex='dd'*n) for a,n in DEAD] if r['observe'] else dead_payloads(data);need(binding['dead_before']==p['dead_after']==dead and len(bytes.fromhex(p['destination_before']))==16 and len(bytes.fromhex(p['stack_frame_before']))==136 and len(bytes.fromhex(p['stack_guard_before']))==len(bytes.fromhex(p['stack_guard_after']))==56 and p['stack_guard_before']==p['stack_guard_after'] and len(bytes.fromhex(binding['upper_before']))==len(bytes.fromhex(p['upper_after']))==16 and binding['upper_before']==p['upper_after'] and bytes.fromhex(binding['upper_before'])[:8]==struct.pack('<II',0,0x207333D),'PP source-specific dead buffers and borrowed payload/upper caller saved frame')
 events=[list(e) for e in binding['events_before']];need(len(events)==44 and events==[list(e) for e in r['events'][:44]] and [(e[3],e[2]) for e in events if e[0]=='alloc']==list(ALLOCATIONS) and len([e for e in events if e[0]=='free'])==12 and {e[1] for e in events if e[0]=='free'}=={a for a,n in DEAD},'PP actual prior allocation/free/read ledger at selected custom boundary')
 create=r['friendship_checkpoints'][0];party_plain=B._decrypt(bytes.fromhex(create['mon_hex'])[136:],want['fields']['pid']);need(party_plain[20:76]==expected_mail(data['constructor']['language']),'native Mail_Init56 copied to actual party extension; msg_no zero is modeled allocation provenance')
 flow=r['pp_flow'];need(len(flow)==len(FLOW) and [e['pc'] for e in flow]==list(map(hex,FLOW)) and all(e['stage']=='ctor' and len(e['regs'])==16 and e['regs'][8:12]==list(N.COOKIES[4:]) and e['regs'][13]==INNER-offset and e['regs'][15]&32 for e,offset in zip(flow,FLOW_SP)),'complete custom PP22 source frames and high ABI cookies');by={int(e['pc'],16):e for e in flow};regs=lambda pc:by[pc]['regs'];caller=regs(FLOW[0]);need(caller[:3]==[MON,310,0] and caller[13:15]==[INNER-152,0x2073A37] and binding['native_caller']==dict(entry='0x20714e8',args=caller[:4],sp=caller[13],lr=hex(caller[14]),saved=caller[4:12]),'PP selected slot0 actual caller entry')
 thunk=list(caller);thunk[3]=0x20714F1;need(regs(0x20714F0)==thunk,'PP native MonSetMove veneer changes only R3 before tail entry')
 for pc,args,lr in ((0x2071516,[310,0],None),(0x207332C,[310,0],0x207151B),(0x2073314,[310,5],0x207333D),(0x20733B0,[310,DEST],STOP|1)):
  need(regs(pc)[:2]==args and (lr is None or regs(pc)[14]==lr),'PP source getter helper arguments/return '+hex(pc))
 need(regs(0x207150A)[:3]==[MON,62,0] and regs(0x207150E)[0]==0 and regs(STOP)==p['end'],'PP-Up0 actual getter and native reader return before stack reuse');loaded=by[0x2073390];before=regs(0x2073390);after=list(before);after[0]=15
 need(before==[DEST,42,p['end'][2],p['end'][3]]+COOKIES+[p['end'][12],TOP,0x2073329,0x3F] and loaded['field_address']==DEST+6 and loaded['field_byte']==data['pp_reader']['11']['member'][6]==15 and regs(0x2073392)==after,'PP native attr5 byte6 LDRB changes only R0 from actual unchanged MoveTbl')
 need(regs(0x2073354)==[DEST,5,p['end'][2],p['end'][3]]+COOKIES+[p['end'][12],TOP,0x2073329,0x3F] and regs(0x207333C)==[value,42,p['end'][2],p['end'][3],0,0,MON,0]+list(N.COOKIES[4:])+[p['end'][12],INNER-200,0x2073329,0x3F],'PP actual attr5 dispatch and GetMoveAttr restored caller frame/registers')
 need(regs(0x2073328)[0]==regs(0x207333C)[0]==value and regs(0x2073348)[:2]==[0,100] and regs(0x2073348)[4:6]==[value,0] and regs(0x207334C)[0]==0 and regs(0x207334C)[4:6]==[value,0] and regs(0x207151A)[0]==regs(0x207151C)[0]==value and regs(0x207151C)[1]==INNER-184,'actual loaded PP/GetMaxPP with zero PP-Ups/native divide and local byte store')
 for pc in (0x2071526,0x206ED70):
  e=by[pc];need(e['regs'][:3]==[MON,58,INNER-184] and e['value_pointer']==INNER-184 and e['value_byte']==value,'PP actual setter58 pointer/value')
 need(regs(0x206ED70)[14]==0x207152B,'PP actual setter58 callee LR');order=B.PERMUTATIONS[((want['fields']['pid']>>13)&31)%24];block=lambda index:MON+8+32*order.index(index);blockb=block(1);expected=[blockb,value,3,0x206ED8D,INNER-184,blockb,block(3),block(0)]+list(N.COOKIES[4:])+[0,INNER-304,0x206EE27,0x3F]
 need(r['pp_stores']==[dict(pc='0x206f0fe',address=blockb+8,bytes=1,before=15,value=value,regs=expected,header_flags=0)],'PP actual plaintext slot0 store before/value/full16 source ABI')
 checkpoint=r['pp_checkpoint'];raw=bytes.fromhex(checkpoint['mon_hex']);decoded=T.M.decode(raw);need(checkpoint['same_cpu']is True and checkpoint['pc']=='0x207152a' and checkpoint['regs']==regs(0x207152A) and decoded==checkpoint['decoded'] and decoded['flags']==0 and decoded['checksum_ok'] and decoded['pp'][0]==value and checkpoint['mon_hex']==H.expected_friendship_packet(r['mon_hex'][0],35),'PP quiescent native setter return complete predicted236-byte packet')
 api=next(e for e in r['body']['native_calls'] if e['entry']=='0x20714e8');need(api['args']==caller[:4] and api['sp']==caller[13] and api['saved']==caller[4:12] and api['lr']==hex(caller[14]) and api['return_sp']==regs(0x2073A36)[13] and api['return_saved']==regs(0x2073A36)[4:12] and api['result']==regs(0x2073A36)[:4],'PP own flow bound to independent original native caller ledger');return True

def require_earlier(r,data,q,expected_create_packet=None):
 want=T.expected(data['constructor'],r['plus'])[0];seed=want['ot_draws'][-1];need(r['personal_shadows']==r['growth_shadows']==r['friendship_shadows']==[],'PP earlier native owners have no argument/value shadows');G.require_growth_context(r,data);G.require_growth_native(r['growth_reader'],data['growth_reader'],q['header_code'],seed,4,want['fields']['otid']&65535);G.require_personal_context(r,data);J.require_personal_native(r['personal_reader'],data['personal_reader'],q['header_code'],seed);require_friendship_context(r,data,expected_create_packet=expected_create_packet);H.require_friendship_native(r['friendship_reader'],data['personal_reader'],q['header_code'],seed);require_names(r,data,q);Y.require_header_context(r,data);Y.require_header_native(r['header_reader'],data['header'],q['header_code'],r['seed']);Z.require_prefix_context(r,data);Z.require_prefix_native(r['prefix_reader'],data['header'],q['header_code'],r['seed']);require_ctor_dispatch(r,data);need(r['ctor_start_steps']==Y.prefix_hook_contract(data,q)['total_before_constructor'],'source-bound unchanged PP caller prefix checkpoint')

def require_case(r,data,q):
 need('pp_expected_slot0' not in data and r['pp_shadows']==[],'positive PP caller has no value shadow or counter expectation');require_pp_context(r,data);require_pp_native(r['pp_reader'],data['pp_reader'],q['header_code'],T.expected(data['constructor'],r['plus'])[0]['ot_draws'][-1]);require_earlier(r,data,q);return True

def require_off_pair(on,off,data):
 parent=H.require_off_pair(on,off);a,b=on['pp_reader'],off['pp_reader'];ignored={'observe','native_writes','unrelated_ram_sha256','ram_sha256','projected_ram_sha256','dead_after'};need(on['pp_clobber']is off['pp_clobber']is False and on['pp_shadows']==off['pp_shadows']==[] and a['observe']is True and b['observe']is False and b['native_writes']==[],'PP OFF finite control domain')
 need({k:v for k,v in a.items() if k not in ignored}=={k:v for k,v in b.items() if k not in ignored} and a['projected_ram_sha256']==b['projected_ram_sha256'] and all(on[k]==off[k] for k in ('pp_flow','pp_stores','pp_checkpoint')),'PP OFF complete native transport/ABI/borrowed frame/consumer and phase1124B projection')
 for r in (on,off):
  p=r['pp_reader'];binding=r['pp_binding'];dead=[dict(address=a,bytes=n,hex='dd'*n) for a,n in DEAD] if r['observe'] else dead_payloads(data);need(binding['neutral']is True and binding['regs']==p['entry'] and binding['ram_sha256']==p['unrelated_ram_sha256'] and binding['canary_preimages']==[dict(address=a,bytes=n,hex=('a5' if r['observe'] else '00')*n) for a,n in CANARIES] and binding['dead_before']==p['dead_after']==dead,'PP OFF exact canary/dead payload provenance including Mail and learnset')
  need(len(bytes.fromhex(binding['upper_before']))==len(bytes.fromhex(p['upper_after']))==16 and binding['upper_before']==p['upper_after'] and bytes.fromhex(p['upper_after'])[:8]==struct.pack('<II',0,0x207333D),'PP OFF entire borrowed upper16 and saved caller pair')
 need(on['pp_binding']['projected_ram_sha256']==off['pp_binding']['projected_ram_sha256'] and all(on['pp_binding'][key]==off['pp_binding'][key] for key in ('events_before','native_caller','upper_before')),'PP OFF actual pre-state differs only224B allocation canaries and900B dead observer poison');return dict(neutral=True,parent=parent,scope='PP native transport/ABI/actual stack frame and16B live borrowed payload/consumer equal; phase excludes exact224B canaries+900B source-owned dead buffers, no stack/output mask; inherited final scratch projection')

def close_binding():
 return A.rewrite(R,'require_counter',[("def require_counter(c,normal,data,code):","def require_counter(c,normal,data,code,expected_seed):",1),("variant in ('skip_close','short_payload')","variant=='skip_close'",1),("require_case(normal,data,code)","require_pp_native(normal,data,code,expected_seed)",1),("normal['narc']==56","normal['narc']==11",1),("normal['member']==31","normal['member']==310",1),("require_case(disguised,data,code)","require_pp_native(disguised,data,code,expected_seed)",1)],dict(TOP=TOP,DEST=DEST,require_pp_native=require_pp_native),'narc_reader')
require_close_native,CLOSE_RECIPE=close_binding()

def counter_record(r,data,q):
 disguised=copy.deepcopy(r);disguised['variant']='current';disguised['pp_reader']['variant']='current';disguised['pp_reader']['shadows']=[];disguised['pp_shadows']=[]
 try:require_case(disguised,data,q)
 except ValueError as e:return dict(variant=r['variant'],result=r,completed=True,tag_disguised=True,rejection=str(e))
 raise ValueError('custom PP counter accepted')

def require_counter(c,normal,data,q):
 require_case(normal,data,q);r=c['result'];variant=c['variant'];need('pp_expected_slot0' not in data and c['completed']is c['tag_disguised']is True and variant in ('pp_skip_close','pp_one') and r['variant']==variant and r['plus']==normal['plus']==1 and r['seed']==normal['seed']==0x12345678 and r['poison']==normal['poison']==0xC7 and r['observe']is True and r['pp_clobber']is False,'PP complete counter fixture domain');value=1 if variant=='pp_one' else 15;require_pp_context(r,data,value);seed=T.expected(data['constructor'],1)[0]['ot_draws'][-1];need(r['pp_binding']==normal['pp_binding'] and all(r['pp_reader'][k]==normal['pp_reader'][k] for k in ('stack_frame_before','stack_guard_before','destination_before','upper_after')),'PP counter source-bound entire pre-state/frame/payload identical before mutation')
 expected_data=data;create=None
 if variant=='pp_skip_close':
  need(r['pp_shadows']==[] and r['pp_reader']['variant']=='skip_close','PP Close sole mutation');require_close_native(dict(variant='skip_close',result=r['pp_reader'],tag_disguised=True,rejection=c['rejection']),normal['pp_reader'],data['pp_reader'],q['header_code'],seed);need(r['mon_hex']==normal['mon_hex'] and r['names']==normal['names'] and r['raw_ram_sha256']==normal['raw_ram_sha256'],'PP Close same final party/all name evidence/whole RAM')
 else:
  need(r['pp_reader']==normal['pp_reader'] and len(r['pp_shadows'])==1,'PP counter same native delivery before single loaded-value shadow');before=next(e['regs'] for e in r['pp_flow'] if e['pc']=='0x2073392');after=list(before);after[0]=1;need(r['pp_shadows']==[dict(pc='0x2073392',register='r0',before=before,after=after,reason='first custom PP15 to valid1 after native LDRB; raw MoveTbl and default learnset unchanged')],'PP exact R0-only post-LDRB shadow')
  need(r['mon_hex']==[expected_pp_packet(normal['mon_hex'][0],1)]+normal['mon_hex'][1:] and J.names_without_scope_hashes(r['names'])==J.names_without_scope_hashes(normal['names']) and r['friendship_checkpoints'][0]==normal['friendship_checkpoints'][0],'PP independently predicted one-field complete packet; first nickname/CreateMon precede mutation')
  require_pp_native(r['pp_reader'],data['pp_reader'],q['header_code'],seed);expected_data=dict(data,pp_expected_slot0=1);create=normal['friendship_checkpoints'][0]['mon_hex']
 replay=copy.deepcopy(r);replay['variant']='current';require_earlier(replay,expected_data,q,expected_create_packet=create)
 need(r['instructions']==normal['instructions']-(variant=='pp_skip_close') and r['prefix']==normal['prefix'] and r['seed_after']==normal['seed_after'] and r['message']==normal['message'],'PP counter actual hook delta,prepared Trainer,seed and message preserved')
 for key in ('header_reader','prefix_reader','personal_reader','personal_binding','personal_shadows','growth_reader','growth_binding','growth_shadows','friendship_reader','friendship_binding','friendship_flow','friendship_shadows','ctor_read_dispatch'):need(r[key]==normal[key],'PP counter prior/remaining owner unchanged '+key)
 disguised=copy.deepcopy(r);disguised['variant']='current';disguised['pp_shadows']=[];disguised['pp_reader']['variant']='current';disguised['pp_reader']['shadows']=[]
 try:require_case(disguised,data,q)
 except ValueError as e:need(str(e)==c['rejection']==('PP actual attr5 dispatch and GetMoveAttr restored caller frame/registers' if value==1 else 'native reader complete path/ownership/stack/frozen state'),'PP source-bound counter rejection identity')
 else:raise ValueError('PP counter replay accepted')
 return True

def analyze(rom,language,objects,strategy_object,*,readback_only=False):
 R.W.require_host_budget();sources=source_identities();model=P.G.S.SHARED.read_current(rom,language);positive=[];guards=[];controls=[];off=[];counters=[]
 with rom.open('rb') as f,mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as raw:
  q,proof=qualify(model,raw,language,objects,strategy_object)
  if readback_only:
   table=resources(raw);need(source_identities()==sources,'pp readback source drift');return dict(schema='trainer31-native-pp-readback-v1',language=language,input=model['record'],source_sha256=sources,proof=proof,recipes=RECIPES,pp_reader=table['11']['oracle'],cpu_executed=False,compiler_invoked=False,limits=['Offline exact-code/object/path/member identity only; no native activation or semantic execution in this mode'])
  data=dict(preparation=Q.resources(raw),constructor=T.resources(model,raw,language,trainer=31),message=V.M.resources(raw),names=X.W.resources(raw),header=R.resources(raw),personal_reader=J.resources(raw),growth_reader=G.resources(raw),growth_counter=G.resources(raw,2),pp_reader=resources(raw))
  for plus in (0,1):
   for seed in (0x12345678,0x12345679):
    r=run_case(model,raw,language,q,data,plus,seed);require_case(r,data,q);positive.append(r);print(language,'native custom move310/PP caller',plus,hex(seed),'verified',flush=True)
   r=run_case(model,raw,language,q,data,plus,observe=False);off.append(dict(result=r,proof=require_off_pair(positive[-2],r,data)))
  normal=next(r for r in positive if r['plus']==1 and r['seed']==0x12345678);r=run_case(model,raw,language,q,data,poison=0x39);require_case(r,data,q);need(r['mon_hex']==normal['mon_hex'],'pp native actual stack preimage poison independence');guards.append(r)
  r=run_case(model,raw,language,q,data,pp_clobber=True);require_case(r,data,q);need(r['mon_hex']==normal['mon_hex'] and r['prefix']==normal['prefix'] and r['seed_after']==normal['seed_after'] and r['functional_ram_sha256']==normal['functional_ram_sha256'] and r['pp_reader']['ram_sha256']==normal['pp_reader']['ram_sha256'],'pp FS volatile clobber same game state and entire reader phase RAM');controls.append(r)
  for variant in ('pp_skip_close','pp_one'):
   r=run_case(model,raw,language,q,data,variant=variant);c=counter_record(r,data,q);require_counter(c,normal,data,q);counters.append(c)
  need(source_identities()==sources,'pp source drift during campaign');R.W.require_host_budget()
 return dict(schema='trainer31-native-pp-caller-v1',language=language,input=model['record'],source_sha256=sources,proof=proof,recipes=RECIPES,close_recipe=CLOSE_RECIPE,semantic_counter=dict(result_source_sha256=A.RESULT_SOURCE_SHA256,complete_result_bytecode_unchanged=True,namespace_delta=['T'],expected_delta='first record PPslot0=1 only; raw archives/evidence/dispatch unchanged',flag='pp_expected_slot0 int1 only within validated counter; positive refuses presence'),prefix_hook_source_contract=Y.prefix_hook_contract(data,q),resources=dict(preparation=data['preparation'],constructor=T.resource_summary(data['constructor'],[r['body'] for r in positive+guards+controls]),message=data['message']['oracle'],names=data['names']['oracle'],header=data['header']['55']['oracle'],party_reader=data['header']['56']['oracle'],personal_reader=data['personal_reader']['2']['oracle'],growth_reader=data['growth_reader']['3']['oracle'],pp_reader=data['pp_reader']['11']['oracle']),positives=positive,guards=guards,volatile_controls=controls,observer_off=off,counters=counters,compiler_invoked=False,limits=['Initialized trainer31 caller, first CUSTOM move310/slot0 PP read only; other183/185 ReadWhole calls remain explicit models','Default learnset310 is a different earlier caller; no first-ID-only attribution','Five opaque FS services and original heap models; original MW compiler/FSFile layout unavailable','Actual stack destination16B, reader frame136/guard56 preimages; phase OFF excludes exactly224B canaries+900B source-owned dead buffers','Counter changes only R0 after actual PP15 load; raw archives/evidence/dispatch remain unchanged, host counter expectation changes only first record PP0','No natural encounter/card/full battle/UI/save/hardware proof'])


def main():
 import argparse
 parser=argparse.ArgumentParser(description=__doc__)
 for name in ('rom','objects','strategy-object','json'):parser.add_argument('--'+name,type=Path,required=True)
 parser.add_argument('--language',choices=('EN','IT'),required=True);parser.add_argument('--readback-only',action='store_true')
 args=parser.parse_args()
 try:
  need(not args.json.exists() and not args.json.is_symlink(),'output must be fresh');output=args.json.resolve();need(P.SOURCE not in output.parents and output!=P.SOURCE,'output must be outside source');need(args.objects.resolve() not in output.parents and args.strategy_object.resolve().parent not in output.parents,'output must be outside retained object directories');need(all(p.is_file() for p in (args.rom,args.strategy_object,args.objects/'rematch-variants.o',args.objects/'rematch-stub.o')),'pp caller inputs must exist');result=analyze(args.rom,args.language,args.objects,args.strategy_object,readback_only=args.readback_only);payload=(json.dumps(result,separators=(',',':'))+'\n').encode();need(len(payload)<=32*1024**2,'expanded pp caller report budget');blob=gzip.compress(payload,mtime=0) if args.json.suffix=='.gz' else payload;need(len(blob)<=8*1024**2,'stored pp caller report budget');R.W.require_host_budget();args.json.parent.mkdir(parents=True,exist_ok=True)
  with args.json.open('xb') as f:f.write(blob)
 except ValueError as e:parser.exit(2,str(e)+'\n')
 print(args.language,'pp readback verified without CPU' if args.readback_only else 'native custom move310 stack reader and PP setter caller verified; other reads and native FS models remain explicit')
if __name__=='__main__':main()
