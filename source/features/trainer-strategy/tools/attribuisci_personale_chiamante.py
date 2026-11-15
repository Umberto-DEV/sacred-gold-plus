#!/usr/bin/env python3
"""Attribute the first native personal-data read to actual growth/EXP consumption.

Finite trainer31, species355, attribute21 profile in one initialized caller CPU.
ROM inputs remain read-only. Native FS and other constructor reads remain models.
"""
from pathlib import Path
import importlib.util,types,struct,json,gzip,mmap,copy,gc,sys

def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
Z=load('personal_prefix_parent',Path(__file__).with_name('attribuisci_lettore_prefisso.py'))
A=load('personal_reader_profile',Path(__file__).parents[1]/'test/personal_narc_bench.py');A.bind(Z)
Y,X,R,V,U,B,T,P,Q,N=Z.Y,Z.X,Z.R,Z.V,Z.U,Z.B,Z.T,Z.P,Z.Q,Z.N
need,sha,OUTER,INNER=Z.need,Z.sha,Z.OUTER,Z.INNER
TOP,DEST,STOP,IP=INNER-320,B.ARENA+384,0x206FAA2,B.ARENA+216
COOKIES=[DEST,355,0xFFFF0000,0xFFFF0000]+list(N.COOKIES[4:])
CANARIES=Z.CANARIES+((DEST-8,8),(DEST+44,8))
PROFILE_DATA=((0x210F218,4),(0x210F1E0,8))
FLOW=(0x206FD00,0x206FBE8,0x206FA8C,0x20725A4,0x206FAA2,0x206FAA8,0x206FB74,0x206FB76,0x206FBFA,0x206FD0A,0x206FD0C,0x206FD30,0x206FD14,0x206FD5C,0x206DF7A,0x206DF82,0x206DF86)
FLOW_SP=(280,288,304,320,320,304,320,320,304,288,288,288,304,304,280,280,280)
from unicorn.arm_const import UC_ARM_REG_PC

def resources(raw):
 import ndspy.narc
 members,receipt=P.RAW.raw_archive(raw,'a/0/0/2');fat=struct.unpack_from('<I',raw,0x48)[0];start,end=struct.unpack_from('<II',raw,fat+8*receipt['file_id']);archive=bytes(raw[start:end]);need(receipt['file_id']==131 and len(members)==508 and len(archive)==26472 and sha(archive)=='91cd5b2bbd5d161f66aeec5b1b2122ee18946557fea1415c3ed433755960e3db' and ndspy.narc.NARC(archive).files[355]==members[355],'personal whole archive raw/ndspy identity');btaf=struct.unpack_from('<H',archive,12)[0];btaf_size=struct.unpack_from('<I',archive,btaf+4)[0];btnf=btaf+btaf_size;btnf_size=struct.unpack_from('<I',archive,btnf+4)[0];gmif=btnf+btnf_size;lo,hi=struct.unpack_from('<II',archive,btaf+12+355*8);position=gmif+8+lo;member=bytes(members[355]);need((btaf,btaf_size,btnf,btnf_size,gmif,lo,hi,position)==(16,4076,4092,20,4112,15620,15664,19740) and len(member)==44 and sha(member)=='1954a12fbe5fe597e544784d31c7f0a89b98b73c5e53ca1d768d481043749270' and member[19]==4 and archive[position:position+44]==member and start+position==receipt['member_rom_offsets'][355],'personal member independent raw offsets and growth field')
 return {'2':dict(raw=archive,path='a/0/0/2',member=member,oracle=dict(narc=2,path='a/0/0/2',file_id=131,archive_rom_offset=start,archive_bytes=len(archive),archive_sha256=sha(archive),member=355,member_bytes=44,member_sha256=sha(member),member_archive_offset=position,member_rom_offset=start+position,btaf=btaf,btaf_bytes=btaf_size,btnf=btnf,btnf_bytes=btnf_size,gmif=gmif,count=508,start=lo,end=hi))}

def qualify(model,raw,*args):
 q,proof=Z.qualify(model,raw,*args);view=P.G.S.SHARED.gifts_audit.Arm9View(raw);extra=[]
 for address,n in PROFILE_DATA:
  blob=view.read(address,n);need(blob==P.G.piece(model['segments'],address,n),'personal native path raw/section disagreement');extra.append(dict(ram=hex(address),bytes=n,rom_offset=hex(view.offset(address,n)),sha256=sha(blob),kind='personal path data only'))
 need(view.read(0x210F218,4)==struct.pack('<I',0x210F1E0) and view.read(0x210F1E0,8)==b'a/0/0/2\0','actual personal table/path selection');q['personal_data']=tuple(R.DATA)+tuple((a,n,sha(view.read(a,n))) for a,n in PROFILE_DATA);proof['native_personal_path']=extra
 need(all(pc in q['body_code'] for pc in FLOW),'personal field/EXP observer starts must already be qualified body code');return q,proof

def canaries_before(reader):return all(reader.read_bytes(a,n)==reader.before[a-0x2000000:a-0x2000000+n] for a,n in CANARIES[-2:])

def bindings():
 init,p1=A.rewrite(R,'Reader.__init__',[("narc in (55,56)","narc==2",1)],{},'narc_reader')
 snapshot,p2=A.rewrite(R,'Reader.run',A.inherited(1,[("member=31","member=355",1)]),dict(TOP=TOP,DEST=DEST,STOP=STOP,COOKIES=COOKIES,canaries_before=canaries_before),'narc_reader')
 native,p3=A.rewrite(R,'require_case',A.inherited(2,[("narc in (55,56)","narc==2",1),("31","355",23),("path=0x210F038 if narc==55 else 0x210F030","path=0x210F1E0",1)]),dict(TOP=TOP,DEST=DEST,STOP=STOP,COOKIES=COOKIES,IP=IP),'narc_reader')
 run,p4=A.rewrite(V,'run_case',A.inherited(3,[("prefix_clobber=False):","prefix_clobber=False,personal_clobber=False):",1),("prefix_clobber=prefix_clobber)","prefix_clobber=prefix_clobber,personal_clobber=personal_clobber)",1),("return dict(prefix_reader=","return dict(personal_reader=driver.personal_result,personal_binding=driver.personal_binding,personal_flow=driver.personal_flow,personal_shadows=driver.personal_shadows,personal_clobber=driver.personal_clobber,prefix_reader=",1)]),dict(Driver=Driver,A=A,NAME_ARENA=X.NAME_ARENA,NAME_END=X.NAME_END),'message_caller')
 edits=A.inherited(4);i=next(i for i,e in enumerate(edits) if '+158' in e[0]);old,new,count=edits[i];edits[i]=(old,new.replace('+157',"+r['personal_reader']['instructions']+157"),count);parent,p5=A.rewrite(V,'require_case',edits,dict(A=A,V=V),'message_caller');names,p6=A.rewrite(X,'require_case',[],dict(require_parent=parent),'species_caller')
 dispatch,p7=A.rewrite(Y,'require_ctor_dispatch',A.inherited(6,[("expected_count=187+2*r['plus']","expected_count=186+2*r['plus']",1),("{2:78,3:24","{2:77,3:24",1)]),{},'header_caller')
 return init,snapshot,native,run,names,dispatch,[p1,p2,p3,p4,p5,p6,p7]

def bind_reader(driver):
 namespace=dict(vars(R));bound=type('PersonalReader',(R.Reader,),{});namespace.update(TOP=TOP,DEST=DEST,STOP=STOP,Reader=bound,DATA=driver.qualified['personal_data'])
 for name,method in vars(R.Reader).items():
  if isinstance(method,types.FunctionType):
   fn=types.FunctionType(method.__code__,namespace,method.__name__,method.__defaults__,method.__closure__);fn.__kwdefaults__=method.__kwdefaults__;setattr(bound,name,fn)
 fn=types.FunctionType(reader_init.__code__,{**reader_init.__globals__,'Reader':bound},reader_init.__name__,reader_init.__defaults__,reader_init.__closure__);fn.__kwdefaults__=reader_init.__kwdefaults__;bound.__init__=fn
 r=bound(dict(segments=driver.bench.segments),driver.qualified['header_code'],driver.data['personal_reader'],2,fill=driver.poison,observe=driver.observe,clobber=driver.personal_clobber,variant='skip_close' if driver.personal_variant=='personal_skip_close' else 'current');r.u=driver.u;r.entry=r.regs();r.before=r.read_bytes(0x2000000,0x400000);return r

class Driver(Z.Driver):
 latest=None
 def __init__(self,*args,personal_clobber=False,**kwargs):
  variant=kwargs.pop('variant','current');need(variant in ('current','personal_skip_close','personal_curve2') and type(personal_clobber)is bool,'finite personal caller controls');super().__init__(*args,variant='current',**kwargs);Driver.latest=self;self.personal_variant=variant;self.personal_clobber=personal_clobber;self.personal_reader=None;self.personal_active=False;self.personal_result=None;self.personal_binding=None;self.personal_flow=[];self.personal_shadows=[];self.personal_flow_done=False
 def start_personal(self):
  regs=self.regs();need(not self.header_active and not self.prefix_active and not self.message_active and not self.name_active and self.prefix_handback is not None and len(self.name_results)==1 and self.ctor_read_dispatch==[] and regs==[DEST,2,355,0x2007509]+COOKIES+[IP,TOP,STOP|1,0x3F],'personal first body call actual source ABI/occurrence');need(not self.observe or self.audit.pending_service is None,'personal reader cannot borrow outstanding constructor SDK service');before=self.read_bytes(0x2000000,0x400000);self.personal_reader=bind_reader(self);need(self.personal_reader.u is self.u and self.regs()==regs and self.read_bytes(0x2000000,0x400000)==before,'personal observer binding changed CPU/RAM');self.personal_binding=dict(neutral=True,regs=regs,ram_sha256=sha(before),projected_ram_sha256=P.masked_hash(before,[(a,a+n) for a,n in CANARIES]),canary_preimages=[dict(address=a,bytes=n,hex=self.read_bytes(a,n).hex()) for a,n in CANARIES]);self.personal_active=True
 def finish_personal(self):
  r=self.personal_reader;self.personal_result=personal_snapshot(r);self.personal_result.update(same_cpu=r.u is self.u,stack_frame_before=r.before[TOP-136-0x2000000:TOP-0x2000000].hex(),stack_guard_before=r.before[TOP-192-0x2000000:TOP-136-0x2000000].hex(),destination_before=r.before[DEST-0x2000000:DEST-0x2000000+44].hex(),projected_ram_sha256=P.masked_hash(self.read_bytes(0x2000000,0x400000),[(a,a+n) for a,n in CANARIES]));self.personal_active=False
 def step(self,u,pc,n,user):
  if self.personal_active and pc==STOP:self.finish_personal()
  if self.stage=='ctor' and pc==R.ENTRY and self.regs()[1:3]==[2,355] and self.personal_reader is None:self.start_personal()
  if self.personal_active:
   self.steps+=1;sp=self.regs()[13];need(self.steps<=3000000 and OUTER-608<=sp<=INNER,'personal full caller instruction/stack bound');self.max_stack=max(self.max_stack,OUTER-sp);self.personal_reader.step(u,pc,n,user);return
  if self.stage=='ctor' and not self.personal_flow_done and pc in FLOW:
   need(len(self.personal_flow)<len(FLOW) and pc==FLOW[len(self.personal_flow)],'first personal getter/growth/EXP selected native path order');event=dict(pc=hex(pc),regs=self.regs(),stage=self.stage)
   if pc==0x206FB74:event.update(field_address=DEST+19,field_byte=self.read_bytes(DEST+19,1)[0])
   if pc==0x206FD5C:event.update(table=self.regs()[4],offset=self.regs()[0],word=self.word(self.regs()[4]+self.regs()[0]))
   if pc==0x206DF82:event.update(value_pointer=self.regs()[2],value=self.word(self.regs()[2]))
   self.personal_flow.append(event)
   if pc==0x206DF86:self.personal_flow_done=True
  if self.stage=='ctor' and pc==0x206FB76 and self.personal_variant=='personal_curve2' and not self.personal_shadows:
   before=self.regs();need(before[5]==4 and before[4]==DEST,'personal curve shadow actual native field load');super().step(u,pc,n,user);u.reg_write(B.R[5],2);after=self.regs();expected=list(before);expected[5]=2;need(after==expected,'personal shadow changes only already loaded growth result');self.personal_shadows.append(dict(pc=hex(pc),register='r5',before=before,after=after,reason='first native personal growth4 to validcurve2; original member and native LDRB unchanged'));return
  super().step(u,pc,n,user)
 def read(self,u,access,address,n,value,user):
  if self.personal_active:self.personal_reader.read(u,access,address,n,value,user);return
  super().read(u,access,address,n,value,user)
 def write(self,u,access,address,n,value,user):
  if self.personal_active:self.personal_reader.write(u,access,address,n,value,user);return
  super().write(u,access,address,n,value,user)
reader_init,personal_snapshot,require_personal_native,run_case,require_names,require_ctor_dispatch,RECIPES=bindings()

def source_identities():
 result=Z.source_identities()
 for p in (__file__,A.__file__):result[str(Path(p).resolve().relative_to(P.SOURCE))]=sha(Path(p).read_bytes())
 return result

def require_personal_context(r,data,*,curve=4):
 p=r['personal_reader'];b=r['personal_binding'];want=T.expected(data['constructor'],r['plus'])[0];need(p is not None and p['same_cpu']is True and p['narc']==2 and p['member']==355 and p['fill']==r['poison'] and p['clobber']is r['personal_clobber'] and type(r['personal_clobber'])is bool and p['destination_before']=='00'*44 and p['rng_after']==want['ot_draws'][-1] and b['neutral']is True and b['regs']==p['entry'] and b['ram_sha256']==p['unrelated_ram_sha256'],'personal actual CPU/fixture/zero allocation/context/RNG binding')
 need(b['canary_preimages']==[dict(address=a,bytes=n,hex=('a5' if r['observe'] else '00')*n) for a,n in CANARIES] and len(bytes.fromhex(p['stack_frame_before']))==136 and len(bytes.fromhex(p['stack_guard_before']))==56,'personal exact allocation observer preimages and preexisting stack bounds')
 need([list(e) for e in r['events'][:3]]==[['alloc',11,108,B.ARENA],['alloc',11,236,B.ARENA+128],['alloc',0,44,DEST]],'personal zeroed destination bound to original first body allocation; no fake read event')
 flow=r['personal_flow'];need(len(flow)==len(FLOW) and [e['pc'] for e in flow]==list(map(hex,FLOW)) and all(e['stage']=='ctor' and len(e['regs'])==16 for e in flow),'complete first native personal/getter/growth/EXP trace')
 need(len(FLOW_SP)==len(FLOW) and all(e['regs'][8:12]==list(N.COOKIES[4:]) and e['regs'][13]==INNER-offset and e['regs'][15]&32 for e,offset in zip(flow,FLOW_SP)),'source-bound personal flow high cookies/frames/Thumb state');by={int(e['pc'],16):e for e in flow};regs=lambda pc:by[pc]['regs'];level=want['fields']['level'];exp=struct.unpack_from('<I',data['constructor']['archives'][3][curve],level*4)[0];table=DEST+64
 need(regs(0x206FBFA)[0]==regs(0x206FD0A)[0]==regs(0x206FD0C)[0]==curve,'native personal growth byte and actual getter result')
 for pc,args,sp,lr in ((0x206FD00,[355,level],INNER-280,0x206DF7B),(0x206FBE8,[355,21],INNER-288,0x206FD0B),(0x206FA8C,[355,0],INNER-304,0x206FBF3),(0x20725A4,[355,DEST],TOP,STOP|1),(0x206FAA8,[DEST,21],INNER-304,0x206FBFB),(0x206FD30,[curve,level],INNER-288,0x206FD11),(0x206FD14,[curve,table],INNER-304,0x206FD5B)):
  v=regs(pc);need(v[:2]==args and v[13]==sp and v[14]==lr and v[15]&32,'source-derived personal helper actual arguments/frame/return '+hex(pc))
 need(regs(STOP)==p['end'],'actual personal reader return before allocator epilogue')
 loaded=by[0x206FB74];after=regs(0x206FB76);expected_after=list(loaded['regs']);expected_after[5]=loaded['field_byte'];need(after==expected_after,'native personal LDRB changes only R5, preserves all other registers and flags');need(loaded['field_address']==DEST+19 and loaded['field_byte']==data['personal_reader']['2']['member'][19]==4 and regs(0x206FB74)[4]==DEST and after[4:8]==[DEST,4,21,0xFFFF0000] and after[:4]==[0xAC,21,p['end'][2],want['fields']['otid']&65535] and after[12:15]==[p['end'][12],TOP,0x206FBFB],'native attr21 dispatch reads byte19 from actual personal buffer')
 need(regs(0x206FBFA)[0]==regs(0x206FD0A)[0]==regs(0x206FD0C)[0]==curve and regs(0x206FBFA)[13:15]==[INNER-304,0x206FBFB] and regs(0x206FD0A)[13:15]==[INNER-288,0x206FBC1] and regs(0x206FD0C)[1]==level,'native personal growth byte and actual getter result')
 lookup=by[0x206FD5C];need(lookup['regs'][4]==lookup['table']==table and lookup['regs'][0]==lookup['offset']==level*4 and lookup['regs'][5:7]==[level,curve] and lookup['regs'][13:15]==[INNER-304,0x206FD2D] and lookup['regs'][15]&32 and lookup['word']==exp and regs(0x206DF7A)[0]==exp and regs(0x206DF7A)[13:15]==[INNER-280,0x206FD65],'actual native growth table lookup and EXP return')
 setter=by[0x206DF82];need(setter['regs'][:3]==[B.ARENA+128,8,INNER-272] and setter['value_pointer']==INNER-272 and setter['value']==exp and regs(0x206DF86)[13]==INNER-280,'actual native EXP local and SetBoxMonData attr8 return')
 reads=[e for e in r['body']['models'] if e['name']=='ReadWholeNarcMemberByIdPair'];need(reads and reads[0]['args'][:3]==[table,3,curve] and reads[0]['bytes']==404 and reads[0]['sha256']==sha(data['constructor']['archives'][3][curve]),'first next model must deliver selected actual growth table')
 return True

def require_case(r,data,q):
 need(r['personal_shadows']==[],'positive personal caller has no growth shadow');require_personal_context(r,data);require_personal_native(r['personal_reader'],data['personal_reader'],q['header_code'],T.expected(data['constructor'],r['plus'])[0]['ot_draws'][-1]);require_names(r,data,q);Y.require_header_context(r,data);Y.require_header_native(r['header_reader'],data['header'],q['header_code'],r['seed']);Z.require_prefix_context(r,data);Z.require_prefix_native(r['prefix_reader'],data['header'],q['header_code'],r['seed']);require_ctor_dispatch(r,data);need(r['ctor_start_steps']==Y.prefix_hook_contract(data,q)['total_before_constructor'],'source-bound unchanged personal caller prefix checkpoint');return True

def require_off_pair(on,off):
 parent=Z.require_off_pair(on,off);a,b=on['personal_reader'],off['personal_reader'];ignored={'observe','native_writes','unrelated_ram_sha256','ram_sha256','projected_ram_sha256'};need(on['personal_clobber']is off['personal_clobber']is False and on['personal_shadows']==off['personal_shadows']==[] and a['observe']is True and b['observe']is False and b['native_writes']==[],'personal OFF domain and logs')
 need({k:v for k,v in a.items() if k not in ignored}=={k:v for k,v in b.items() if k not in ignored} and a['projected_ram_sha256']==b['projected_ram_sha256'] and on['personal_flow']==off['personal_flow'],'personal OFF complete FS/ABI/preimage/growth/EXP and phase RAM projection')
 for r in (on,off):
  p=r['personal_reader'];binding=r['personal_binding'];need(binding['neutral']is True and binding['regs']==p['entry'] and binding['ram_sha256']==p['unrelated_ram_sha256'] and binding['canary_preimages']==[dict(address=a,bytes=n,hex=('a5' if r['observe'] else '00')*n) for a,n in CANARIES],'personal OFF actual binding and six allocation canary preimages')
 need(on['personal_binding']['projected_ram_sha256']==off['personal_binding']['projected_ram_sha256'],'personal OFF pre-phase RAM differs outside source-proven48B canaries');return dict(neutral=True,parent=parent,scope='personal all transport/ABI/actual stack/growth/EXP and phase RAM equal except six source-known allocation canaries48B; inherited final scratch projection remains')

def counter_binding():
 return A.rewrite(R,'require_counter',[("def require_counter(c,normal,data,code):","def require_counter(c,normal,data,code,expected_seed):",1),("variant in ('skip_close','short_payload')","variant=='skip_close'",1),("require_case(normal,data,code)","require_personal_native(normal,data,code,expected_seed)",1),("normal['narc']==56","normal['narc']==2",1),("normal['member']==31","normal['member']==355",1),("require_case(disguised,data,code)","require_personal_native(disguised,data,code,expected_seed)",1)],dict(TOP=TOP,DEST=DEST,require_personal_native=require_personal_native),'narc_reader')
require_close_native,CLOSE_RECIPE=counter_binding()

def expected_exp_packet(packet,new_exp):
 raw=bytearray.fromhex(packet);pid,flags,checksum=struct.unpack_from('<IHH',raw);blocks=bytearray(B._decrypt(raw[8:136],checksum));order=B.PERMUTATIONS[((pid>>13)&31)%24];struct.pack_into('<I',blocks,32*order.index(0)+8,new_exp);new_checksum=sum(struct.unpack('<64H',blocks))&65535;struct.pack_into('<H',raw,6,new_checksum);raw[8:136]=B._decrypt(blocks,new_checksum);need(T.M.decode(bytes(raw))['checksum_ok'],'independent counter re-encryption checksum');return bytes(raw).hex()

def counter_record(r,data,q):
 disguised=copy.deepcopy(r);disguised['variant']='current';disguised['personal_reader']['variant']='current';disguised['personal_reader']['shadows']=[];disguised['personal_shadows']=[]
 try:require_case(disguised,data,q)
 except ValueError as e:return dict(variant=r['variant'],result=r,completed=True,tag_disguised=True,rejection=str(e))
 raise ValueError('personal caller counter accepted')

def names_without_scope_hashes(names):
 result=copy.deepcopy(names)
 for name in result[1:]:
  for transition in name['transitions']:transition.pop('ram_sha256')
 return result

def require_counter(c,normal,data,q):
 require_case(normal,data,q);r=c['result'];variant=c['variant'];need(c['completed']is c['tag_disguised']is True and variant in ('personal_skip_close','personal_curve2') and r['variant']==variant and r['plus']==normal['plus']==1 and r['seed']==normal['seed']==0x12345678 and r['poison']==normal['poison']==0xC7 and r['observe']is True and r['personal_clobber']is False,'personal complete counter baseline')
 curve=2 if variant=='personal_curve2' else 4;require_personal_context(r,data,curve=curve);seed=T.expected(data['constructor'],1)[0]['ot_draws'][-1]
 if variant=='personal_skip_close':
  need(r['personal_shadows']==[] and r['personal_reader']['variant']=='skip_close','personal Close counter only reader mutation');require_close_native(dict(variant='skip_close',result=r['personal_reader'],tag_disguised=True,rejection=c['rejection']),normal['personal_reader'],data['personal_reader'],q['header_code'],seed);need(r['mon_hex']==normal['mon_hex'] and r['instructions']==normal['instructions']-1,'personal Close leak same complete party and one skipped FS fetch')
 else:
  need(r['personal_reader']==normal['personal_reader'] and r['personal_binding']==normal['personal_binding'] and len(r['personal_shadows'])==1,'growth counter keeps exact native personal delivery and one post-load shadow');shadow=r['personal_shadows'][0];before=next(e['regs'] for e in r['personal_flow'] if e['pc']=='0x206fb76');after=list(before);after[5]=2;need(shadow==dict(pc='0x206fb76',register='r5',before=before,after=after,reason='first native personal growth4 to validcurve2; original member and native LDRB unchanged'),'only actual first loaded growth result4 to2 changed')
  level=T.expected(data['constructor'],1)[0]['fields']['level'];exp=struct.unpack_from('<I',data['constructor']['archives'][3][2],4*level)[0];need(r['mon_hex']==[expected_exp_packet(normal['mon_hex'][0],exp)]+normal['mon_hex'][1:] and r['instructions']==normal['instructions'],'growth counter exact independently predicted EXP-only packet and unchanged native path count')
  require_personal_native(r['personal_reader'],data['personal_reader'],q['header_code'],seed)
 expected_data=copy.deepcopy(data)
 if curve==2:
  personal=bytearray(expected_data['constructor']['personal']['355']);personal[19]=2;expected_data['constructor']['personal']['355']=bytes(personal)
 replay=copy.deepcopy(r);replay['variant']='current';require_names(replay,expected_data,q);Y.require_header_context(replay,data);Y.require_header_native(replay['header_reader'],data['header'],q['header_code'],r['seed']);Z.require_prefix_context(replay,data);Z.require_prefix_native(replay['prefix_reader'],data['header'],q['header_code'],r['seed']);require_ctor_dispatch(replay,data)
 need(r['prefix']==normal['prefix'] and r['seed_after']==normal['seed_after'] and r['ctor_start_steps']==normal['ctor_start_steps'] and len(r['names'])==len(normal['names'])==6 and (r['names']==normal['names'] if variant=='personal_skip_close' else names_without_scope_hashes(r['names'])==names_without_scope_hashes(normal['names'])) and r['message']==normal['message'] and r['header_reader']==normal['header_reader'] and r['prefix_reader']==normal['prefix_reader'],'personal counter unrelated native owners/Trainer/seed unchanged')
 disguised=copy.deepcopy(r);disguised['variant']='current';disguised['personal_shadows']=[];disguised['personal_reader']['variant']='current';disguised['personal_reader']['shadows']=[]
 try:require_case(disguised,data,q)
 except ValueError as e:need(str(e)==c['rejection']==('native personal growth byte and actual getter result' if curve==2 else 'native reader complete path/ownership/stack/frozen state'),'personal counter predicted pure rejection identity')
 else:raise ValueError('personal counter replay accepted')
 return True

def personal_lineage(paths,language):
 """Offline exact-code and actual data-route audit; no historical execution."""
 import ndspy.narc
 rows=[]
 for role,path in paths.items():
  model=P.G.S.SHARED.read_current(path,language) if role=='r4' else P.G.S.SHARED.read_image(path,language,role)
  with path.open('rb') as f,mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as raw:
   code=[]
   for address,n,count,digest in R.SPANS:
    blob=P.G.piece(model['segments'],address,n);instructions=list(R.Cs(R.CS_ARCH_ARM,R.CS_MODE_THUMB).disasm(blob,address));need(sha(blob)==digest and len(instructions)==count and sum(i.size for i in instructions)==n,'historical personal parser code correspondence');code.append(dict(ram=hex(address),bytes=n,starts=count,sha256=digest))
   table=struct.unpack('<I',P.G.piece(model['segments'],0x2007520,4))[0];row=table+8;pointer=struct.unpack('<I',P.G.piece(model['segments'],row,4))[0];name=P.G.piece(model['segments'],pointer,8);need(name==b'a/0/0/2\0','historical actual personal path route');members,receipt=P.RAW.raw_archive(raw,name[:-1].decode());fat=struct.unpack_from('<I',raw,0x48)[0];start,end=struct.unpack_from('<II',raw,fat+8*receipt['file_id']);archive=bytes(raw[start:end]);member=bytes(members[355]);need(receipt['file_id']==131 and len(members)==508 and len(member)==44 and sha(member)=='1954a12fbe5fe597e544784d31c7f0a89b98b73c5e53ca1d768d481043749270' and member[19]==4 and ndspy.narc.NARC(archive).files[355]==member,'historical personal raw/ndspy/member correspondence');expected_sha={'retail':'6e533889d97eee45db41affe61ceec2e05d7e8dac54126adefbb65eb1f664197','base11':'5f193d2eacddf0ffef9daf7acebd35dcdb21c30f59ab497759c3b7cc335f2d40','v4':'91cd5b2bbd5d161f66aeec5b1b2122ee18946557fea1415c3ed433755960e3db','r4':'91cd5b2bbd5d161f66aeec5b1b2122ee18946557fea1415c3ed433755960e3db'};need(sha(archive)==expected_sha[role],'historical whole personal archive revision identity')
   btaf=struct.unpack_from('<H',archive,12)[0];btaf_n=struct.unpack_from('<I',archive,btaf+4)[0];btnf=btaf+btaf_n;btnf_n=struct.unpack_from('<I',archive,btnf+4)[0];gmif=btnf+btnf_n;lo,hi=struct.unpack_from('<II',archive,btaf+12+355*8);position=gmif+8+lo;need(archive[position:position+hi-lo]==member and start+position==receipt['member_rom_offsets'][355],'historical personal independent NARC arithmetic')
   rows.append(dict(role=role,input=model['record'],code=code,actual_route=dict(table_ram=hex(table),row_ram=hex(row),path_ram=hex(pointer),path='a/0/0/2'),resource=dict(file_id=131,archive_rom_offset=start,archive_bytes=end-start,archive_sha256=sha(archive),count=508,member=355,member_bytes=44,member_sha256=sha(member),member_archive_offset=position,member_rom_offset=start+position,growth_offset=19,growth=4,btaf=btaf,btaf_bytes=btaf_n,btnf=btnf,btnf_bytes=btnf_n,gmif=gmif,start=lo,end=hi),cpu_executed=False,limits=['Code/source-route/member correspondence only; no historical SDK/caller execution or original compiler reconstruction; no inferred direct physical code offsets for compressed images']))
  del model;gc.collect();R.W.require_host_budget()
 return rows

def analyze(rom,language,objects,strategy_object,*,history=None,readback_only=False):
 R.W.require_host_budget();sources=source_identities();hist=personal_lineage(history,language) if history else None;model=P.G.S.SHARED.read_current(rom,language);positive=[];guards=[];controls=[];off=[];counters=[]
 with rom.open('rb') as f,mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as raw:
  q,proof=qualify(model,raw,language,objects,strategy_object);data=dict(preparation=Q.resources(raw),constructor=T.resources(model,raw,language,trainer=31),message=V.M.resources(raw),names=X.W.resources(raw),header=R.resources(raw),personal_reader=resources(raw))
  if readback_only:
   need(source_identities()==sources,'personal readback source drift');return dict(schema='trainer31-native-personal-readback-v1',language=language,input=model['record'],source_sha256=sources,proof=proof,recipes=RECIPES,history=hist,personal_reader=data['personal_reader']['2']['oracle'],cpu_executed=False,compiler_invoked=False,limits=['Offline installed-code/object/path/member identity only; no native activation or semantic execution in this mode'])
  for plus in (0,1):
   for seed in (0x12345678,0x12345679):
    r=run_case(model,raw,language,q,data,plus,seed);require_case(r,data,q);positive.append(r);print(language,'native personal/growth/EXP caller',plus,hex(seed),'verified',flush=True)
   r=run_case(model,raw,language,q,data,plus,observe=False);off.append(dict(result=r,proof=require_off_pair(positive[-2],r)))
  normal=next(r for r in positive if r['plus']==1 and r['seed']==0x12345678);r=run_case(model,raw,language,q,data,poison=0x39);require_case(r,data,q);need(r['mon_hex']==normal['mon_hex'],'personal caller preexisting stack poison independence');guards.append(r)
  r=run_case(model,raw,language,q,data,personal_clobber=True);require_case(r,data,q);need(r['mon_hex']==normal['mon_hex'] and r['prefix']==normal['prefix'] and r['seed_after']==normal['seed_after'] and r['functional_ram_sha256']==normal['functional_ram_sha256'] and r['personal_reader']['ram_sha256']==normal['personal_reader']['ram_sha256'],'personal FS volatile control same game state/entire reader phase RAM');controls.append(r)
  for variant in ('personal_skip_close','personal_curve2'):
   r=run_case(model,raw,language,q,data,variant=variant);counter=counter_record(r,data,q);require_counter(counter,normal,data,q);counters.append(counter)
  need(source_identities()==sources,'personal caller source drift during campaign');R.W.require_host_budget()
 return dict(schema='trainer31-native-personal-caller-v1',language=language,input=model['record'],source_sha256=sources,proof=proof,history=hist,recipes=RECIPES,close_recipe=CLOSE_RECIPE,prefix_hook_source_contract=Y.prefix_hook_contract(data,q),resources=dict(preparation=data['preparation'],constructor=T.resource_summary(data['constructor'],[r['body'] for r in positive+guards+controls]),message=data['message']['oracle'],names=data['names']['oracle'],header=data['header']['55']['oracle'],party_reader=data['header']['56']['oracle'],personal_reader=data['personal_reader']['2']['oracle']),positives=positive,guards=guards,volatile_controls=controls,observer_off=off,counters=counters,compiler_invoked=False,limits=['Initialized trainer31 caller/first personal2/355 only, Plus0/1/two seeds/two poisons','Five FS opaque services, original heap and186 Normal/188 Plus other ReadWhole models remain','Attribute21 byte19 growth4 traced through native getter, selected growth table/model and actual EXP setter; growth4 to2 counter changes only one loaded register result','Original native compiler and native FSFile layout unavailable; no natural encounter/card/full battle/UI/save/hardware proof','Actual reader frame136+guard56 captured before allocator return; OFF phase excludes exact six allocation canaries48B'])

def main():
 import argparse
 parser=argparse.ArgumentParser(description=__doc__)
 for name in ('rom','objects','strategy-object','json'):parser.add_argument('--'+name,type=Path,required=True)
 parser.add_argument('--language',choices=('EN','IT'),required=True);parser.add_argument('--readback-only',action='store_true')
 for name in ('retail','base','v4'):parser.add_argument('--'+name,type=Path)
 args=parser.parse_args()
 try:
  need(not args.json.exists() and not args.json.is_symlink(),'output must be fresh');output=args.json.resolve();need(P.SOURCE not in output.parents and output!=P.SOURCE,'output must be outside source');need(args.objects.resolve() not in output.parents and args.strategy_object.resolve().parent not in output.parents,'output must be outside retained object directories');need(all(p.is_file() for p in (args.rom,args.strategy_object,args.objects/'rematch-variants.o',args.objects/'rematch-stub.o')),'personal caller inputs must exist');extra=(args.retail,args.base,args.v4);need(not any(extra) or all(extra),'provide all three optional historical inputs');history=dict(retail=args.retail,base11=args.base,v4=args.v4,r4=args.rom) if all(extra) else None;result=analyze(args.rom,args.language,args.objects,args.strategy_object,history=history,readback_only=args.readback_only);payload=(json.dumps(result,separators=(',',':'))+'\n').encode();need(len(payload)<=32*1024**2,'expanded personal caller report budget');blob=gzip.compress(payload,mtime=0) if args.json.suffix=='.gz' else payload;need(len(blob)<=8*1024**2,'stored personal caller report budget');R.W.require_host_budget();args.json.parent.mkdir(parents=True,exist_ok=True)
  with args.json.open('xb') as f:f.write(blob)
 except ValueError as e:parser.exit(2,str(e)+'\n')
 print(args.language,'personal readback verified without CPU' if args.readback_only else 'first native personal reader/growth/EXP attribution verified; other readers and native FS models remain explicit')
if __name__=='__main__':main()
