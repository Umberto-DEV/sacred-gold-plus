#!/usr/bin/env python3
"""Trace native initial friendship and its later owned Plus override in one CPU.

The second personal2/355 read feeds byte18/getter20/native SetBox9. Actual Mon
checkpoints distinguish transient value35 from final255; original inputs stay
read-only and all other reader/SDK boundaries retain their explicit owners.
"""
from pathlib import Path
import importlib.util,types,struct,json,gzip,mmap,copy,gc,sys

def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
G=load('friendship_growth_parent',Path(__file__).with_name('attribuisci_crescita_chiamante.py'))
A=load('friendship_profile',Path(__file__).parents[1]/'test/friendship_narc_bench.py');A.bind(G)
J,Z,Y,X,R,V,U,B,T,P,Q,N=G.J,G.Z,G.Y,G.X,G.R,G.V,G.U,G.B,G.T,G.P,G.Q,G.N
need,sha,OUTER,INNER=G.need,G.sha,G.OUTER,G.INNER
TOP,DEST,STOP,IP=INNER-312,B.ARENA+872,0x206FAA2,B.ARENA+216
MON=B.ARENA+128
COOKIES=[DEST,355,0xFFFF0000,0xFFFF0000]+list(N.COOKIES[4:])
CANARIES=G.CANARIES+((DEST-8,8),(DEST+44,8))
DEAD=((J.DEST,44),(G.DEST,404))
PROJECTION=[(a,a+n) for a,n in CANARIES]+[(a,a+n) for a,n in DEAD]
FLOW=(0x206FBE8,0x206FA8C,0x20725A4,0x206FAA2,0x206FAA8,0x206FB70,0x206FB72,0x206FBFA,0x206DF8E,0x206DF96,0x206ED70,0x206DF9A)
FLOW_SP=(280,296,312,312,296,312,312,296,280,280,280,280)
RECIPE_SHA256='bddb793ec901d9102a3d42d6a5278b78232f26641ecd59ebe9003fd51ec89c49'
from unicorn.arm_const import UC_ARM_REG_PC

def emit_postform():
 """Independent Thumb halfwords/PC-relative BL emission for the owned50B recipe."""
 base=0x2073AE4;out=bytearray()
 def h(value):out.extend(struct.pack('<H',value))
 def bl(target):
  pc=base+len(out);distance=target-(pc+4);need(distance%2==0 and -(1<<22)<=distance<(1<<22),'owned helper BL range/alignment');delta=distance>>1;out.extend(struct.pack('<HH',0xF000|((delta>>11)&0x7FF),0xF800|(delta&0x7FF)))
 h(0xB538);h(0x1C04);bl(0x20722D4);h(0x1C20);bl(0x206E250);h(0x1C20);h(0x21DA);bl(0x2071754);h(0x2800);h(0xD001);h(0x2000);h(0xE000);h(0x20FF);h(0x9000);h(0x1C20);h(0x2109);h(0xAA00);bl(0x206EC40);h(0xBD38);h(0x46C0);h(0x46C0);need(len(out)==50,'owned helper exact emitted extent');return bytes(out)

def qualify(model,raw,*args):
 q,proof=G.qualify(model,raw,*args)
 from sgp131 import trainer_fixes as recipe
 need(sha(Path(recipe.__file__).read_bytes())==RECIPE_SHA256,'owned trainer helper source drift');payload=emit_postform();view=P.G.S.SHARED.gifts_audit.Arm9View(raw);need(payload==recipe.FORM_STATS_AFTER==view.read(0x2073AE4,50)==P.G.piece(model['segments'],0x2073AE4,50),'owned helper independent emission/source recipe/raw/section readback');instructions=list(R.Cs(R.CS_ARCH_ARM,R.CS_MODE_THUMB).disasm(payload[:46],0x2073AE4));need(len(instructions)==19 and sum(i.size for i in instructions)==46 and payload[46:]==bytes.fromhex('c046c046') and all(q['body_code'].get(i.address)==(i.size,True) for i in instructions if i.address not in (0x2073AFE,0x2073B00)),'owned helper code versus written padding qualification');old=T.F.M.attest_post_form(model);proof['friendship_override_recipe']=dict(parent=old,independently_emitted_sha256=sha(payload),body_bytes=46,body_starts=19,padding_bytes=4,rom_offset=hex(view.offset(0x2073AE4,50)),source_sha256=RECIPE_SHA256,kind='owned Plus literal/guarded in-place installer; no native MW reconstruction or new compiler');need(all(pc in q['body_code'] for pc in FLOW+(0x2073A16,0x2073AE4,0x2073B0C,0x2073B10,0x2073A5E,0x2073A68,0x206F03E)),'friendship observer points must be existing qualified instructions');return q,proof

def canaries_before(r):return all(r.read_bytes(a,n)==r.before[a-0x2000000:a-0x2000000+n] for a,n in CANARIES[-2:])

def bindings():
 init,p1=A.rewrite(R,'Reader.__init__',[("narc in (55,56)","narc==2",1)],{},'narc_reader')
 snapshot,p2=A.rewrite(R,'Reader.run',[("self.setup();self.u.emu_start(ENTRY|1,STOP,count=20001);","",1),("list(N.COOKIES)","list(COOKIES)",1),("self.read_bytes(DEST-16,16)==b'\\xA5'*16 and self.read_bytes(DEST+size,124-size)==b'\\xA5'*(124-size)","canaries_before(self)",1),("self.read_bytes(TOP-192,56)==bytes([self.fill])*56","self.read_bytes(TOP-192,56)==self.before[TOP-192-0x2000000:TOP-136-0x2000000]",1),("member=31","member=355",1)],dict(TOP=TOP,DEST=DEST,STOP=STOP,COOKIES=COOKIES,canaries_before=canaries_before),'narc_reader')
 native,p3=A.rewrite(R,'require_case',[(e['before'],e['after'],e['count']) for e in J.RECIPES[2]['edits']],dict(TOP=TOP,DEST=DEST,STOP=STOP,COOKIES=COOKIES,IP=IP),'narc_reader')
 run,p4=A.rewrite(V,'run_case',A.inherited(4,[("growth_clobber=False):","growth_clobber=False,friendship_clobber=False):",1),("growth_clobber=growth_clobber)","growth_clobber=growth_clobber,friendship_clobber=friendship_clobber)",1),("return dict(growth_reader=","return dict(friendship_reader=driver.friendship_result,friendship_binding=driver.friendship_binding,friendship_flow=driver.friendship_flow,friendship_stores=driver.friendship_stores,friendship_checkpoints=driver.friendship_checkpoints,friendship_shadows=driver.friendship_shadows,friendship_clobber=driver.friendship_clobber,growth_reader=",1)]),dict(Driver=Driver,A=A,NAME_ARENA=X.NAME_ARENA,NAME_END=X.NAME_END),'message_caller')
 edits=A.inherited(5);i=next(i for i,e in enumerate(edits) if '+158' in e[0]);old,new,count=edits[i];edits[i]=(old,new.replace('+157',"+r['friendship_reader']['instructions']+157"),count);parent,p5=A.rewrite(V,'require_case',edits,dict(A=A,V=V),'message_caller');names,p6=A.rewrite(X,'require_case',[],dict(require_parent=parent),'species_caller')
 dispatch,p7=A.rewrite(Y,'require_ctor_dispatch',A.inherited(7,[("expected_count=185+2*r['plus']","expected_count=184+2*r['plus']",1),("{2:77,3:23","{2:76,3:23",1)]),{},'header_caller')
 return init,snapshot,native,run,names,dispatch,[p1,p2,p3,p4,p5,p6,p7]

def bind_reader(driver):
 namespace=dict(vars(R));bound=type('FriendshipReader',(R.Reader,),{});namespace.update(TOP=TOP,DEST=DEST,STOP=STOP,Reader=bound,DATA=driver.qualified['personal_data'])
 for name,method in vars(R.Reader).items():
  if isinstance(method,types.FunctionType):
   fn=types.FunctionType(method.__code__,namespace,method.__name__,method.__defaults__,method.__closure__);fn.__kwdefaults__=method.__kwdefaults__;setattr(bound,name,fn)
 fn=types.FunctionType(reader_init.__code__,{**reader_init.__globals__,**namespace},reader_init.__name__,reader_init.__defaults__,reader_init.__closure__);fn.__kwdefaults__=reader_init.__kwdefaults__;bound.__init__=fn
 r=bound(dict(segments=driver.bench.segments),driver.qualified['header_code'],driver.data['personal_reader'],2,fill=driver.poison,observe=driver.observe,clobber=driver.friendship_clobber,variant='skip_close' if driver.friendship_variant=='friendship_skip_close' else 'current');r.u=driver.u;r.entry=r.regs();r.before=r.read_bytes(0x2000000,0x400000);return r

class Driver(G.Driver):
 latest=None
 def __init__(self,*args,friendship_clobber=False,**kwargs):
  variant=kwargs.pop('variant','current');need(variant in ('current','friendship_skip_close','friendship_zero') and type(friendship_clobber)is bool,'finite friendship controls');super().__init__(*args,variant='current',**kwargs);Driver.latest=self;self.friendship_variant=variant;self.friendship_clobber=friendship_clobber;self.friendship_reader=None;self.friendship_active=False;self.friendship_result=None;self.friendship_binding=None;self.friendship_flow=[];self.friendship_flow_open=False;self.friendship_flow_done=False;self.friendship_shadows=[];self.friendship_stores=[];self.friendship_checkpoints=[];self.friendship_store_owner=None;self.friendship_override_open=False
 def field_address(self):
  pid=self.word(MON);order=B.PERMUTATIONS[((pid>>13)&31)%24];return MON+8+32*order.index(0)+12
 def start_friendship(self):
  regs=self.regs();need(self.growth_result is not None and not any((self.growth_active,self.personal_active,self.prefix_active,self.header_active,self.name_active,self.message_active)) and len(self.name_results)==1 and self.ctor_read_dispatch==[] and regs==[DEST,2,355,0x2007509]+COOKIES+[IP,TOP,STOP|1,0x3F],'second personal reader actual friendship source ABI/occurrence');need(not self.observe or self.audit.pending_service is None,'friendship reader cannot borrow constructor pending service');before=self.read_bytes(0x2000000,0x400000);self.friendship_reader=bind_reader(self);need(self.friendship_reader.u is self.u and self.regs()==regs and before==self.read_bytes(0x2000000,0x400000),'friendship observer binding changed CPU/RAM');self.friendship_binding=dict(neutral=True,regs=regs,ram_sha256=sha(before),projected_ram_sha256=P.masked_hash(before,PROJECTION),canary_preimages=[dict(address=a,bytes=n,hex=self.read_bytes(a,n).hex()) for a,n in CANARIES],dead_before=[dict(address=a,bytes=n,hex=self.read_bytes(a,n).hex()) for a,n in DEAD]);self.friendship_active=True
 def finish_friendship(self):
  r=self.friendship_reader;self.friendship_result=friendship_snapshot(r);self.friendship_result.update(same_cpu=r.u is self.u,stack_frame_before=r.before[TOP-136-0x2000000:TOP-0x2000000].hex(),stack_guard_before=r.before[TOP-192-0x2000000:TOP-136-0x2000000].hex(),destination_before=r.before[DEST-0x2000000:DEST-0x2000000+44].hex(),dead_after=[dict(address=a,bytes=n,hex=self.read_bytes(a,n).hex()) for a,n in DEAD],projected_ram_sha256=P.masked_hash(self.read_bytes(0x2000000,0x400000),PROJECTION));self.friendship_active=False
 def checkpoint(self,phase,pc):
  raw=self.read_bytes(MON,236);decoded=T.M.decode(raw);need(decoded['checksum_ok'] and decoded['flags']==0,'actual friendship full-Mon checkpoint flags/checksum');self.friendship_checkpoints.append(dict(phase=phase,pc=hex(pc),regs=self.regs(),mon_hex=raw.hex(),decoded=decoded,party_count=self.word(B.PARTIES+0x1000+4),same_cpu=True))
 def step(self,u,pc,n,user):
  if self.friendship_active and pc==STOP:self.finish_friendship()
  if self.stage=='ctor' and pc==R.ENTRY and self.regs()[1:3]==[2,355] and self.growth_result is not None and self.friendship_reader is None:self.start_friendship()
  if self.friendship_active:
   self.steps+=1;sp=self.regs()[13];need(self.steps<=3000000 and OUTER-608<=sp<=INNER,'friendship caller instruction/frame budget');self.max_stack=max(self.max_stack,OUTER-sp);self.friendship_reader.step(u,pc,n,user);return
  if self.stage=='ctor' and not self.friendship_flow_done:
   if pc==FLOW[0] and self.regs()[:2]==[355,20]:need(not self.friendship_flow_open and not self.friendship_flow,'single initial friendship getter');self.friendship_flow_open=True
   if self.friendship_flow_open and pc in FLOW:
    need(len(self.friendship_flow)<len(FLOW) and pc==FLOW[len(self.friendship_flow)],'first friendship native getter/setter sequence');event=dict(pc=hex(pc),regs=self.regs(),stage=self.stage)
    if pc==0x206FB70:event.update(field_address=DEST+18,field_byte=self.read_bytes(DEST+18,1)[0])
    if pc in (0x206DF96,0x206ED70):event.update(value_pointer=self.regs()[2],value=self.word(self.regs()[2]))
    if pc==0x206ED70:self.friendship_store_owner='initial'
    if pc==0x206DF9A:event.update(plain_friendship=self.read_bytes(self.field_address(),1)[0],header_flags=int.from_bytes(self.read_bytes(MON+4,2),'little'));self.friendship_store_owner=None;self.friendship_flow_done=True
    self.friendship_flow.append(event)
  if self.stage=='ctor' and pc==0x206FB72 and self.friendship_variant=='friendship_zero' and self.friendship_flow_open and not self.friendship_flow_done and not self.friendship_shadows:
   before=self.regs();need(before[5]==35 and before[4]==DEST,'friendship shadow actual native loaded35');super().step(u,pc,n,user);u.reg_write(B.R[5],0);after=self.regs();expected=list(before);expected[5]=0;need(after==expected,'friendship shadow changes only loaded R5');self.friendship_shadows.append(dict(pc=hex(pc),register='r5',before=before,after=after,reason='first native friendship35 to valid0; raw personal and LDRB unchanged'));return
  if self.stage=='ctor' and self.friendship_flow_done and self.word(B.PARTIES+0x1000+4)==0:
   if pc==0x2073A16:self.checkpoint('create_return',pc)
   if pc==0x2073AE4:self.friendship_override_open=True;self.checkpoint('owned_helper_entry',pc)
   if self.friendship_override_open and pc==0x2073B0C:self.checkpoint('before_override',pc);self.friendship_store_owner='override'
   if self.friendship_override_open and pc==0x2073B10:self.friendship_store_owner=None;self.checkpoint('after_override',pc)
   if self.friendship_override_open and pc==0x2073A5E:self.checkpoint('owned_helper_return',pc);self.friendship_override_open=False
  if self.stage=='ctor' and pc==0x2073A68 and len(self.friendship_checkpoints)==5:
   self.checkpoint('party_return',pc);self.friendship_checkpoints[-1]['party_slot_hex']=self.read_bytes(B.PARTIES+0x1000+8,236).hex()
  super().step(u,pc,n,user)
 def read(self,u,access,address,n,value,user):
  if self.friendship_active:self.friendship_reader.read(u,access,address,n,value,user);return
  super().read(u,access,address,n,value,user)
 def write(self,u,access,address,n,value,user):
  if self.friendship_active:self.friendship_reader.write(u,access,address,n,value,user);return
  if self.stage=='ctor' and self.friendship_store_owner is not None and u.reg_read(UC_ARM_REG_PC)==0x206F03E and self.word(B.PARTIES+0x1000+4)==0:
   need(n==1 and address==self.field_address(),'initial/owned friendship actual byte store address');self.friendship_stores.append(dict(owner=self.friendship_store_owner,pc='0x206f03e',address=address,bytes=n,before=self.read_bytes(address,1)[0],value=value,regs=self.regs(),header_flags=int.from_bytes(self.read_bytes(MON+4,2),'little')))
  super().write(u,access,address,n,value,user)
reader_init,friendship_snapshot,require_friendship_native,run_case,require_names,require_ctor_dispatch,RECIPES=bindings()

def source_identities():
 result=G.source_identities()
 for p in (__file__,A.__file__,P.SOURCE/'sgp131/trainer_fixes.py'):result[str(Path(p).resolve().relative_to(P.SOURCE))]=sha(Path(p).read_bytes())
 return result

def expected_friendship_packet(packet,value):
 need(type(value)is int and 0<=value<=255,'friendship byte domain');raw=bytearray.fromhex(packet);pid,flags,checksum=struct.unpack_from('<IHH',raw);need(flags==0,'independent friendship packet must be encrypted outside transaction');blocks=bytearray(B._decrypt(raw[8:136],checksum));order=B.PERMUTATIONS[((pid>>13)&31)%24];blocks[32*order.index(0)+12]=value;new_checksum=sum(struct.unpack('<64H',blocks))&65535;struct.pack_into('<H',raw,6,new_checksum);raw[8:136]=B._decrypt(blocks,new_checksum);need(T.M.decode(bytes(raw))['checksum_ok'],'independent friendship re-encryption checksum');return raw.hex()

def require_friendship_context(r,data,value=35):
 p=r['friendship_reader'];binding=r['friendship_binding'];want=T.expected(data['constructor'],r['plus'])[0];cookie=want['fields']['otid']&65535
 need(value in (35,0) and p is not None and p['same_cpu']is True and p['narc']==2 and p['member']==355 and p['entry']==[DEST,2,355,0x2007509]+COOKIES+[IP,TOP,STOP|1,0x3F] and p['fill']==r['poison'] and p['clobber']is r['friendship_clobber'] and type(r['friendship_clobber'])is bool and p['rng_after']==want['ot_draws'][-1],'source-selected initial friendship reader actual context')
 need(binding['neutral']is True and binding['regs']==p['entry'] and binding['ram_sha256']==p['unrelated_ram_sha256'] and binding['canary_preimages']==[dict(address=a,bytes=n,hex=('a5' if r['observe'] else '00')*n) for a,n in CANARIES],'friendship neutral binding and ten exact allocation observer canaries')
 dead=[dict(address=a,bytes=n,hex=((b'\xDD'*n) if r['observe'] else (data['personal_reader']['2']['member'] if a==J.DEST else data['growth_reader']['3']['member'])).hex()) for a,n in DEAD]
 need(binding['dead_before']==p['dead_after']==dead and p['destination_before']=='00'*44 and len(bytes.fromhex(p['stack_frame_before']))==136 and len(bytes.fromhex(p['stack_guard_before']))==56,'friendship actual two freed buffers and zeroed live allocation provenance')
 need([list(e) for e in r['events'][:7]]==[['alloc',11,108,B.ARENA],['alloc',11,236,MON],['alloc',0,44,J.DEST],['free',J.DEST],['alloc',0,404,G.DEST],['free',G.DEST],['alloc',0,44,DEST]],'friendship exact allocation/free event chain')
 flow=r['friendship_flow'];need(len(flow)==len(FLOW) and [e['pc'] for e in flow]==list(map(hex,FLOW)) and all(e['stage']=='ctor' and len(e['regs'])==16 and e['regs'][8:12]==list(N.COOKIES[4:]) and e['regs'][13]==INNER-offset and e['regs'][15]&32 for e,offset in zip(flow,FLOW_SP)),'complete friendship getter/setter source frames and high ABI cookies');by={int(e['pc'],16):e for e in flow};regs=lambda pc:by[pc]['regs']
 for pc,args,lr in ((0x206FBE8,[355,20],0x206DF8F),(0x206FA8C,[355,0],0x206FBF3),(0x20725A4,[355,DEST],STOP|1),(0x206FAA8,[DEST,20],0x206FBFB)):
  need(regs(pc)[:2]==args and regs(pc)[14]==lr,'friendship source arguments/return '+hex(pc))
 need(regs(STOP)==p['end'],'friendship actual native reader return');loaded=by[0x206FB70];after=regs(0x206FB72);expected=list(loaded['regs']);expected[5]=35
 need(after==expected and loaded['field_address']==DEST+18 and loaded['field_byte']==data['personal_reader']['2']['member'][18]==35 and after[:8]==[0xA8,20,p['end'][2],cookie,DEST,35,20,0xFFFF0000] and after[12:15]==[p['end'][12],TOP,0x206FBFB],'friendship native attr20 LDRB changes only R5 from actual byte18')
 need(regs(0x206FBFA)[0]==regs(0x206DF8E)[0]==value and regs(0x206FBFA)[14]==0x206FBFB and regs(0x206DF8E)[14]==0x206FBC1,'friendship actual getter result')
 for pc in (0x206DF96,0x206ED70):
  e=by[pc];need(e['regs'][:3]==[MON,9,INNER-272] and e['value_pointer']==INNER-272 and e['value']==value,'friendship native SetBox9 local input')
 need(regs(0x206ED70)[14]==0x206DF9B and by[0x206DF9A]['plain_friendship']==value and by[0x206DF9A]['header_flags']==2 and regs(0x206DF9A)==[1,24,3,cookie,cookie,MON,0xFFFF0000,0xFFFF0000]+list(N.COOKIES[4:])+[p['end'][12],INNER-280,0x206EE27,0x3F],'friendship initial setter readback in box-decrypted transaction')
 order=B.PERMUTATIONS[((want['fields']['pid']>>13)&31)%24];blocka=MON+8+32*order.index(0);stores=r['friendship_stores'];need(len(stores)==2,'friendship exactly initial and owned actual stores')
 for e,owner,v,sp,ptr,flags in zip(stores,('initial','override'),(value,255),(INNER-320,INNER-216),(INNER-272,INNER-168),(2,0)):
  blockb=MON+8+32*order.index(1);blockd=MON+8+32*order.index(3);expected=[v,24,3,cookie if owner=='initial' else MON,ptr,blockb,blockd,blocka]+list(N.COOKIES[4:])+[p['end'][12] if owner=='initial' else 0,sp,0x206EE27,0x3F]
  need(e['owner']==owner and e['pc']=='0x206f03e' and e['address']==blocka+12 and e['bytes']==1 and e['before']==(0 if owner=='initial' else value) and e['value']==v and e['header_flags']==flags and e['regs']==expected,'friendship native store exact before/ABI/owner/frame/transaction')
 phases=('create_return','owned_helper_entry','before_override','after_override','owned_helper_return','party_return');pcs=(0x2073A16,0x2073AE4,0x2073B0C,0x2073B10,0x2073A5E,0x2073A68);points=r['friendship_checkpoints'];need(len(points)==6,'friendship six actual full-Mon checkpoints');transient=expected_friendship_packet(r['mon_hex'][0],value)
 for i,(point,phase,pc) in enumerate(zip(points,phases,pcs)):
  raw=bytes.fromhex(point['mon_hex']);decoded=T.M.decode(raw);need(len(raw)==236 and point['same_cpu']is True and point['phase']==phase and point['pc']==hex(pc) and point['decoded']==decoded and decoded['checksum_ok'] and decoded['flags']==0 and decoded['friendship']==(value if i<3 else 255) and point['mon_hex']==(transient if i<3 else r['mon_hex'][0]) and point['party_count']==int(i==5) and len(point['regs'])==16 and point['regs'][6]==MON and point['regs'][8:12]==list(N.COOKIES[4:]) and point['regs'][13]==INNER-(168 if i in (2,3) else 152) and point['regs'][15]&32,'friendship actual transient/owned/final packet and ABI')
 need(points[-1]['party_slot_hex']==r['mon_hex'][0] and points[-1]['regs'][0]==1 and points[1]['regs'][0]==MON and points[1]['regs'][14]==0x2073A5F and points[2]['regs'][:3]==[MON,9,INNER-168] and points[2]['regs'][14]==0x201FF59,'friendship actual owned setter arguments and PartyAdd slot');post=r['body']['post_form_calls'];need(post[2]['args'][1]==218 and post[2]['result'][0]==0 and post[3]['args'][1]==9 and post[3]['value_byte']==255 and post[3]['sp']==INNER-168,'owned Plus selected no218 branch to setter9/255');return True

def require_earlier(r,data,q):
 want=T.expected(data['constructor'],r['plus'])[0];seed=want['ot_draws'][-1];G.require_growth_context(r,data);G.require_growth_native(r['growth_reader'],data['growth_reader'],q['header_code'],seed,4,want['fields']['otid']&65535);G.require_personal_context(r,data);J.require_personal_native(r['personal_reader'],data['personal_reader'],q['header_code'],seed);require_names(r,data,q);Y.require_header_context(r,data);Y.require_header_native(r['header_reader'],data['header'],q['header_code'],r['seed']);Z.require_prefix_context(r,data);Z.require_prefix_native(r['prefix_reader'],data['header'],q['header_code'],r['seed']);require_ctor_dispatch(r,data);need(r['ctor_start_steps']==Y.prefix_hook_contract(data,q)['total_before_constructor'],'source-bound unchanged friendship caller prefix checkpoint')

def require_case(r,data,q):
 need(r['friendship_shadows']==[],'positive friendship caller has no value shadow');require_friendship_context(r,data);require_friendship_native(r['friendship_reader'],data['personal_reader'],q['header_code'],T.expected(data['constructor'],r['plus'])[0]['ot_draws'][-1]);require_earlier(r,data,q);return True

def require_off_pair(on,off):
 parent=G.require_off_pair(on,off);a,b=on['friendship_reader'],off['friendship_reader'];ignored={'observe','native_writes','unrelated_ram_sha256','ram_sha256','projected_ram_sha256','dead_after'};need(on['friendship_clobber']is off['friendship_clobber']is False and on['friendship_shadows']==off['friendship_shadows']==[] and a['observe']is True and b['observe']is False and b['native_writes']==[],'friendship OFF finite domain')
 need({k:v for k,v in a.items() if k not in ignored}=={k:v for k,v in b.items() if k not in ignored} and a['projected_ram_sha256']==b['projected_ram_sha256'] and all(on[k]==off[k] for k in ('friendship_flow','friendship_stores','friendship_checkpoints')),'friendship OFF complete transport/ABI/frame/transient/override evidence and phase528B projection')
 for r in (on,off):
  p=r['friendship_reader'];binding=r['friendship_binding'];dead=[dict(address=a,bytes=n,hex=('dd'*n if r['observe'] else (on['personal_reader']['destination_hex'] if a==J.DEST else on['growth_reader']['destination_hex']))) for a,n in DEAD];need(binding['neutral']is True and binding['regs']==p['entry'] and binding['ram_sha256']==p['unrelated_ram_sha256'] and binding['canary_preimages']==[dict(address=a,bytes=n,hex=('a5' if r['observe'] else '00')*n) for a,n in CANARIES] and binding['dead_before']==p['dead_after']==dead,'friendship OFF exact ten canaries and two source-specific dead allocations')
 need(on['friendship_binding']['projected_ram_sha256']==off['friendship_binding']['projected_ram_sha256'],'friendship OFF pre-phase differs outside80B canaries and448B freed buffers');return dict(neutral=True,parent=parent,scope='native reader full FS/ABI/frame and friendship/transient/owned override checkpoints equal; phase excludes exact80B canaries+448B dead-buffer observer poison; inherited final scratch projection')

def close_binding():
 return A.rewrite(R,'require_counter',[("def require_counter(c,normal,data,code):","def require_counter(c,normal,data,code,expected_seed):",1),("variant in ('skip_close','short_payload')","variant=='skip_close'",1),("require_case(normal,data,code)","require_friendship_native(normal,data,code,expected_seed)",1),("normal['narc']==56","normal['narc']==2",1),("normal['member']==31","normal['member']==355",1),("require_case(disguised,data,code)","require_friendship_native(disguised,data,code,expected_seed)",1)],dict(TOP=TOP,DEST=DEST,require_friendship_native=require_friendship_native),'narc_reader')
require_close_native,CLOSE_RECIPE=close_binding()

def counter_record(r,data,q):
 disguised=copy.deepcopy(r);disguised['variant']='current';disguised['friendship_reader']['variant']='current';disguised['friendship_reader']['shadows']=[];disguised['friendship_shadows']=[]
 try:require_case(disguised,data,q)
 except ValueError as e:return dict(variant=r['variant'],result=r,completed=True,tag_disguised=True,rejection=str(e))
 raise ValueError('friendship caller counter accepted')

def require_counter(c,normal,data,q):
 require_case(normal,data,q);r=c['result'];variant=c['variant'];need(c['completed']is c['tag_disguised']is True and variant in ('friendship_skip_close','friendship_zero') and r['variant']==variant and r['plus']==normal['plus']==1 and r['seed']==normal['seed']==0x12345678 and r['poison']==normal['poison']==0xC7 and r['observe']is True and r['friendship_clobber']is False,'friendship complete counter fixture domain');value=0 if variant=='friendship_zero' else 35;require_friendship_context(r,data,value);seed=T.expected(data['constructor'],1)[0]['ot_draws'][-1];need(r['friendship_binding']==normal['friendship_binding'] and all(r['friendship_reader'][k]==normal['friendship_reader'][k] for k in ('stack_frame_before','stack_guard_before','destination_before')),'friendship counter exact shared pre-state before mutation')
 if variant=='friendship_skip_close':
  need(r['friendship_shadows']==[] and r['friendship_reader']['variant']=='skip_close','friendship Close sole mutation');require_close_native(dict(variant='skip_close',result=r['friendship_reader'],tag_disguised=True,rejection=c['rejection']),normal['friendship_reader'],data['personal_reader'],q['header_code'],seed)
 else:
  need(r['friendship_reader']==normal['friendship_reader'] and len(r['friendship_shadows'])==1,'friendship zero keeps exact reader before one post-LDRB shadow');before=next(e['regs'] for e in r['friendship_flow'] if e['pc']=='0x206fb72');after=list(before);after[5]=0;need(r['friendship_shadows']==[dict(pc='0x206fb72',register='r5',before=before,after=after,reason='first native friendship35 to valid0; raw personal and LDRB unchanged')],'friendship exact R5-only35 to0 mutation');require_friendship_native(r['friendship_reader'],data['personal_reader'],q['header_code'],seed)
  for a,b in zip(r['friendship_checkpoints'][:3],normal['friendship_checkpoints'][:3]):need(a['mon_hex']==expected_friendship_packet(b['mon_hex'],0),'friendship counter transient independently re-encrypted exact one-field packet')
 replay=copy.deepcopy(r);replay['variant']='current';require_earlier(replay,data,q);need(r['mon_hex']==normal['mon_hex'] and r['seed_after']==normal['seed_after'] and r['prefix']==normal['prefix'] and r['names']==normal['names'] and r['message']==normal['message'] and r['raw_ram_sha256']==normal['raw_ram_sha256'] and r['instructions']==normal['instructions']-(variant=='friendship_skip_close'),'friendship counter final party/Trainer/seed/all names/whole RAM restored or unchanged')
 for key in ('header_reader','prefix_reader','personal_reader','personal_binding','personal_shadows','growth_reader','growth_binding','growth_shadows','ctor_read_dispatch'):need(r[key]==normal[key],'friendship counter prior/native modeled owner unchanged '+key)
 disguised=copy.deepcopy(r);disguised['variant']='current';disguised['friendship_shadows']=[];disguised['friendship_reader']['variant']='current';disguised['friendship_reader']['shadows']=[]
 try:require_case(disguised,data,q)
 except ValueError as e:need(str(e)==c['rejection']==('friendship actual getter result' if value==0 else 'native reader complete path/ownership/stack/frozen state'),'friendship counter source-bound rejection identity')
 else:raise ValueError('friendship counter replay accepted')
 return True

def analyze(rom,language,objects,strategy_object,*,readback_only=False):
 R.W.require_host_budget();sources=source_identities();model=P.G.S.SHARED.read_current(rom,language);positive=[];guards=[];controls=[];off=[];counters=[]
 with rom.open('rb') as f,mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as raw:
  q,proof=qualify(model,raw,language,objects,strategy_object)
  if readback_only:
   table=J.resources(raw);need(source_identities()==sources,'friendship readback source drift');return dict(schema='trainer31-native-friendship-readback-v1',language=language,input=model['record'],source_sha256=sources,proof=proof,recipes=RECIPES,friendship_reader=table['2']['oracle'],cpu_executed=False,compiler_invoked=False,limits=['Offline exact-code/object/path/member identity only; no native activation or semantic execution in this mode'])
  data=dict(preparation=Q.resources(raw),constructor=T.resources(model,raw,language,trainer=31),message=V.M.resources(raw),names=X.W.resources(raw),header=R.resources(raw),personal_reader=J.resources(raw),growth_reader=G.resources(raw),growth_counter=G.resources(raw,2))
  for plus in (0,1):
   for seed in (0x12345678,0x12345679):
    r=run_case(model,raw,language,q,data,plus,seed);require_case(r,data,q);positive.append(r);print(language,'native friendship35/override255 caller',plus,hex(seed),'verified',flush=True)
   r=run_case(model,raw,language,q,data,plus,observe=False);off.append(dict(result=r,proof=require_off_pair(positive[-2],r)))
  normal=next(r for r in positive if r['plus']==1 and r['seed']==0x12345678);r=run_case(model,raw,language,q,data,poison=0x39);require_case(r,data,q);need(r['mon_hex']==normal['mon_hex'],'friendship native actual stack preimage poison independence');guards.append(r)
  r=run_case(model,raw,language,q,data,friendship_clobber=True);require_case(r,data,q);need(r['mon_hex']==normal['mon_hex'] and r['prefix']==normal['prefix'] and r['seed_after']==normal['seed_after'] and r['functional_ram_sha256']==normal['functional_ram_sha256'] and r['friendship_reader']['ram_sha256']==normal['friendship_reader']['ram_sha256'],'friendship FS volatile clobber same game state and entire reader phase RAM');controls.append(r)
  for variant in ('friendship_skip_close','friendship_zero'):
   r=run_case(model,raw,language,q,data,variant=variant);c=counter_record(r,data,q);require_counter(c,normal,data,q);counters.append(c)
  need(source_identities()==sources,'friendship source drift during campaign');R.W.require_host_budget()
 return dict(schema='trainer31-native-friendship-caller-v1',language=language,input=model['record'],source_sha256=sources,proof=proof,recipes=RECIPES,close_recipe=CLOSE_RECIPE,prefix_hook_source_contract=Y.prefix_hook_contract(data,q),resources=dict(preparation=data['preparation'],constructor=T.resource_summary(data['constructor'],[r['body'] for r in positive+guards+controls]),message=data['message']['oracle'],names=data['names']['oracle'],header=data['header']['55']['oracle'],party_reader=data['header']['56']['oracle'],personal_reader=data['personal_reader']['2']['oracle'],growth_reader=data['growth_reader']['3']['oracle']),positives=positive,guards=guards,volatile_controls=controls,observer_off=off,counters=counters,compiler_invoked=False,limits=['Initialized trainer31 caller, second personal2/355/44 initial friendship only; other184/186 reads retain original models','Five opaque FS services and original heap models; original MW compiler/FSFile layout unavailable','Native initial getter20/SetBox9 value35 and owned Plus literal50B override255 distinguished; counter0 transient is overwritten before PartyAdd','No natural encounter/card/full battle/UI/save/hardware proof','Reader frame136/guard56 actual preimages; phase OFF excludes exact80B canaries+448B dead-buffer observer poison'])


def main():
 import argparse
 parser=argparse.ArgumentParser(description=__doc__)
 for name in ('rom','objects','strategy-object','json'):parser.add_argument('--'+name,type=Path,required=True)
 parser.add_argument('--language',choices=('EN','IT'),required=True);parser.add_argument('--readback-only',action='store_true')
 args=parser.parse_args()
 try:
  need(not args.json.exists() and not args.json.is_symlink(),'output must be fresh');output=args.json.resolve();need(P.SOURCE not in output.parents and output!=P.SOURCE,'output must be outside source');need(args.objects.resolve() not in output.parents and args.strategy_object.resolve().parent not in output.parents,'output must be outside retained object directories');need(all(p.is_file() for p in (args.rom,args.strategy_object,args.objects/'rematch-variants.o',args.objects/'rematch-stub.o')),'friendship caller inputs must exist');result=analyze(args.rom,args.language,args.objects,args.strategy_object,readback_only=args.readback_only);payload=(json.dumps(result,separators=(',',':'))+'\n').encode();need(len(payload)<=32*1024**2,'expanded friendship caller report budget');blob=gzip.compress(payload,mtime=0) if args.json.suffix=='.gz' else payload;need(len(blob)<=8*1024**2,'stored friendship caller report budget');R.W.require_host_budget();args.json.parent.mkdir(parents=True,exist_ok=True)
  with args.json.open('xb') as f:f.write(blob)
 except ValueError as e:parser.exit(2,str(e)+'\n')
 print(args.language,'friendship readback verified without CPU' if args.readback_only else 'native initial friendship35 and owned Plus override255 caller verified; other reads and native FS models remain explicit')
if __name__=='__main__':main()
