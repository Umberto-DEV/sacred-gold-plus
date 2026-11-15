#!/usr/bin/env python3
"""Attribute the first404-byte native growth-table read to actual EXP consumption.

Same initialized trainer31 caller CPU, explicit five FS models and remaining
constructor read models. No ROM, save or gameplay source is modified.
"""
from pathlib import Path
import importlib.util,types,struct,json,gzip,mmap,copy,gc,sys

def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
J=load('growth_personal_parent',Path(__file__).with_name('attribuisci_personale_chiamante.py'))
A=load('growth_reader_profile',Path(__file__).parents[1]/'test/growth_narc_bench.py');A.bind(J)
Z,Y,X,R,V,U,B,T,P,Q,N=J.Z,J.Y,J.X,J.R,J.V,J.U,J.B,J.T,J.P,J.Q,J.N
need,sha,OUTER,INNER=J.need,J.sha,J.OUTER,J.INNER
TOP,DEST,STOP,IP=INNER-320,B.ARENA+448,0x206FD2C,B.ARENA+216
PERSONAL=J.DEST
COOKIES=[DEST,4,4,0xFFFF0000]+list(N.COOKIES[4:])
CANARIES=J.CANARIES+((DEST-8,8),(DEST+404,8))
PROJECTION=[(a,a+n) for a,n in CANARIES]+[(PERSONAL,PERSONAL+44)]
PROFILE_DATA=((0x210F21C,4),(0x210F1D8,8))
MEMBER_SHA={4:'d57547b2a55109f3b92e6c4214dc79c8f92688205f7460e7fe868c3c363012af',2:'f3a821d7e60596706c3194766b2f9e87795d45450712432a8a8399b41c5ee1e7'}
from unicorn.arm_const import UC_ARM_REG_PC

def resources(raw,member=4):
 import ndspy.narc
 need(type(member)is int and member in (4,2),'finite growth resource member');members,receipt=P.RAW.raw_archive(raw,'a/0/0/3');fat=struct.unpack_from('<I',raw,0x48)[0];start,end=struct.unpack_from('<II',raw,fat+8*receipt['file_id']);archive=bytes(raw[start:end]);need(receipt['file_id']==132 and len(members)==8 and len(archive)==3348 and sha(archive)=='ce5c612e32e537da3cdf7808c3f21ab217e83a75ead56027d98a7d84bb1b55d6' and ndspy.narc.NARC(archive).files[member]==members[member],'growth whole archive raw/ndspy identity');btaf=struct.unpack_from('<H',archive,12)[0];btaf_n=struct.unpack_from('<I',archive,btaf+4)[0];btnf=btaf+btaf_n;btnf_n=struct.unpack_from('<I',archive,btnf+4)[0];gmif=btnf+btnf_n;lo,hi=struct.unpack_from('<II',archive,btaf+12+member*8);position=gmif+8+lo;payload=bytes(members[member]);need((btaf,btaf_n,btnf,btnf_n,gmif)==(16,76,92,16,108) and len(payload)==404 and sha(payload)==MEMBER_SHA[member] and archive[position:position+404]==payload and start+position==receipt['member_rom_offsets'][member],'growth selected member independent arithmetic')
 return {'3':dict(raw=archive,path='a/0/0/3',member=payload,oracle=dict(narc=3,path='a/0/0/3',file_id=132,archive_rom_offset=start,archive_bytes=end-start,archive_sha256=sha(archive),member=member,member_bytes=404,member_sha256=sha(payload),member_archive_offset=position,member_rom_offset=start+position,btaf=btaf,btaf_bytes=btaf_n,btnf=btnf,btnf_bytes=btnf_n,gmif=gmif,count=8,start=lo,end=hi))}

def qualify(model,raw,*args):
 q,proof=J.qualify(model,raw,*args);view=P.G.S.SHARED.gifts_audit.Arm9View(raw);extra=[]
 for address,n in PROFILE_DATA:
  blob=view.read(address,n);need(blob==P.G.piece(model['segments'],address,n),'growth native route raw/section disagreement');extra.append(dict(ram=hex(address),bytes=n,rom_offset=hex(view.offset(address,n)),sha256=sha(blob),kind='growth route data only'))
 need(view.read(0x210F21C,4)==struct.pack('<I',0x210F1D8) and view.read(0x210F1D8,8)==b'a/0/0/3\0','actual growth table row/path');q['growth_data']=tuple(R.DATA)+tuple((a,n,sha(view.read(a,n))) for a,n in PROFILE_DATA);proof['native_growth_path']=extra;return q,proof

def canaries_before(r):return all(r.read_bytes(a,n)==r.before[a-0x2000000:a-0x2000000+n] for a,n in CANARIES[-2:])

def bindings():
 init,p1=A.rewrite(R,'Reader.__init__',[("narc in (55,56)","narc==3",1)],{},'narc_reader')
 service,p2=A.rewrite(R,'Reader.service',[("0<size<=108","0<size<=404",1)],{},'narc_reader')
 snapshot,p3=A.rewrite(R,'Reader.run',[("self.setup();self.u.emu_start(ENTRY|1,STOP,count=20001);","",1),("list(N.COOKIES)","list(COOKIES)",1),("self.read_bytes(DEST-16,16)==b'\\xA5'*16 and self.read_bytes(DEST+size,124-size)==b'\\xA5'*(124-size)","canaries_before(self)",1),("self.read_bytes(TOP-192,56)==bytes([self.fill])*56","self.read_bytes(TOP-192,56)==self.before[TOP-192-0x2000000:TOP-136-0x2000000]",1),("member=31","member=self.entry[2]",1)],dict(TOP=TOP,DEST=DEST,STOP=STOP,COOKIES=COOKIES,canaries_before=canaries_before),'narc_reader')
 native,p4=A.rewrite(R,'require_case',[("def require_case(r,data,code):","def require_case(r,data,code,expected_seed,expected_member,expected_cookie3):",1),("narc in (55,56)","narc==3",1),("31","expected_member",23),("r['rng_after']==0x12345678","r['rng_after']==expected_seed",1),("cookies=list(N.COOKIES)","cookies=list(COOKIES)",1),("cookie3=0x33333303","cookie3=expected_cookie3",1),("0xCCCC000C","IP",3),("stack=bytearray([r['fill']])*136","stack=bytearray.fromhex(r['stack_frame_before']);need(len(stack)==136,'actual growth stack preimage size')",1),("path=0x210F038 if narc==55 else 0x210F030","path=0x210F1D8",1)],dict(TOP=TOP,DEST=DEST,STOP=STOP,COOKIES=COOKIES,IP=IP),'narc_reader')
 run,p5=A.rewrite(V,'run_case',A.inherited(3,[("personal_clobber=False):","personal_clobber=False,growth_clobber=False):",1),("personal_clobber=personal_clobber)","personal_clobber=personal_clobber,growth_clobber=growth_clobber)",1),("return dict(personal_reader=","return dict(growth_reader=driver.growth_result,growth_binding=driver.growth_binding,growth_shadows=driver.growth_shadows,growth_clobber=driver.growth_clobber,personal_reader=",1)]),dict(Driver=Driver,A=A,NAME_ARENA=X.NAME_ARENA,NAME_END=X.NAME_END),'message_caller')
 edits=A.inherited(4);i=next(i for i,e in enumerate(edits) if '+158' in e[0]);old,new,count=edits[i];edits[i]=(old,new.replace('+157',"+r['growth_reader']['instructions']+157"),count);parent,p6=A.rewrite(V,'require_case',edits,dict(A=A,V=V),'message_caller');names,p7=A.rewrite(X,'require_case',[],dict(require_parent=parent),'species_caller')
 dispatch,p8=A.rewrite(Y,'require_ctor_dispatch',A.inherited(6,[("expected_count=186+2*r['plus']","expected_count=185+2*r['plus']",1),("{2:77,3:24","{2:77,3:23",1)]),{},'header_caller')
 personal,p9=A.rewrite(J,'require_personal_context',[("*,curve=4):","*,curve=4,lookup_member=4):",1),("data['constructor']['archives'][3][curve],level*4","data['constructor']['archives'][3][lookup_member],level*4",1),("lookup['regs'][13:15]==[INNER-304,0x206FD2D]","lookup['regs'][13:15]==[INNER-304,r['growth_reader']['end'][14]] and lookup['regs'][1:3]==r['growth_reader']['end'][1:3]",1),("reads=[e for e in r['body']['models'] if e['name']=='ReadWholeNarcMemberByIdPair'];need(reads and reads[0]['args'][:3]==[table,3,curve] and reads[0]['bytes']==404 and reads[0]['sha256']==sha(data['constructor']['archives'][3][curve]),'first next model must deliver selected actual growth table')","need(r['growth_reader']['entry'][:3]==[table,3,lookup_member] and r['growth_reader']['destination_hex']==bytes(data['constructor']['archives'][3][lookup_member]).hex(),'native growth delivery must feed actual table lookup')",1)],{},'personal_caller')
 return init,service,snapshot,native,run,names,dispatch,personal,[p1,p2,p3,p4,p5,p6,p7,p8,p9]

def bind_reader(driver):
 namespace=dict(vars(R));bound=type('GrowthReader',(R.Reader,),{});namespace.update(TOP=TOP,DEST=DEST,STOP=STOP,Reader=bound,DATA=driver.qualified['growth_data'])
 for name,method in vars(R.Reader).items():
  if isinstance(method,types.FunctionType):
   fn=types.FunctionType(method.__code__,namespace,method.__name__,method.__defaults__,method.__closure__);fn.__kwdefaults__=method.__kwdefaults__;setattr(bound,name,fn)
 for name,method in (('__init__',reader_init),('service',reader_service)):
  fn=types.FunctionType(method.__code__,{**method.__globals__,**namespace},method.__name__,method.__defaults__,method.__closure__);fn.__kwdefaults__=method.__kwdefaults__;setattr(bound,name,fn)
 r=bound(dict(segments=driver.bench.segments),driver.qualified['header_code'],driver.data['growth_reader'],3,fill=driver.poison,observe=driver.observe,clobber=driver.growth_clobber,variant='skip_close' if driver.growth_variant=='growth_skip_close' else 'current');r.u=driver.u;r.entry=r.regs();r.before=r.read_bytes(0x2000000,0x400000);return r

class Driver(J.Driver):
 latest=None
 def __init__(self,*args,growth_clobber=False,**kwargs):
  variant=kwargs.pop('variant','current');need(variant in ('current','growth_skip_close','growth_wrong_member') and type(growth_clobber)is bool,'finite growth caller controls');super().__init__(*args,variant='current',**kwargs);Driver.latest=self;self.growth_variant=variant;self.growth_clobber=growth_clobber;self.growth_reader=None;self.growth_active=False;self.growth_result=None;self.growth_binding=None;self.growth_shadows=[]
 def start_growth(self):
  before_regs=self.regs();want=T.expected(self.data['constructor'],self.plus)[0];need(self.stage=='ctor' and not self.personal_active and not self.prefix_active and not self.header_active and not self.name_active and not self.message_active and self.personal_result is not None and len(self.name_results)==1 and self.ctor_read_dispatch==[] and before_regs==[DEST,3,4,want['fields']['otid']&65535]+COOKIES+[IP,TOP,STOP|1,0x3F],'actual first growth caller/source ABI/occurrence');need(not self.observe or self.audit.pending_service is None,'growth owner cannot borrow pending constructor SDK call')
  if self.growth_variant=='growth_wrong_member':
   self.u.reg_write(B.R[2],2);after=self.regs();expected=list(before_regs);expected[2]=2;need(after==expected,'growth counter changes only already prepared member4 to2');self.growth_shadows.append(dict(pc=hex(R.ENTRY),register='r2',before=before_regs,after=after,reason='first native growth member4 to validmember2; getter curve and raw archive unchanged'))
  regs=self.regs();before=self.read_bytes(0x2000000,0x400000);self.growth_reader=bind_reader(self);need(self.growth_reader.u is self.u and self.regs()==regs and before==self.read_bytes(0x2000000,0x400000),'growth binding changed CPU/RAM');self.growth_binding=dict(neutral=True,regs=regs,ram_sha256=sha(before),projected_ram_sha256=P.masked_hash(before,PROJECTION),canary_preimages=[dict(address=a,bytes=n,hex=self.read_bytes(a,n).hex()) for a,n in CANARIES],dead_personal_before=self.read_bytes(PERSONAL,44).hex());self.growth_active=True
 def finish_growth(self):
  r=self.growth_reader;self.growth_result=growth_snapshot(r);self.growth_result.update(same_cpu=r.u is self.u,stack_frame_before=r.before[TOP-136-0x2000000:TOP-0x2000000].hex(),stack_guard_before=r.before[TOP-192-0x2000000:TOP-136-0x2000000].hex(),destination_before=r.before[DEST-0x2000000:DEST-0x2000000+404].hex(),dead_personal_after=self.read_bytes(PERSONAL,44).hex(),projected_ram_sha256=P.masked_hash(self.read_bytes(0x2000000,0x400000),PROJECTION));self.growth_active=False
 def step(self,u,pc,n,user):
  if self.growth_active and pc==STOP:self.finish_growth()
  if self.stage=='ctor' and pc==R.ENTRY and self.regs()[1]==3 and self.growth_reader is None:self.start_growth()
  if self.growth_active:
   self.steps+=1;sp=self.regs()[13];need(self.steps<=3000000 and OUTER-608<=sp<=INNER,'growth complete caller instruction/frame bound');self.max_stack=max(self.max_stack,OUTER-sp);self.growth_reader.step(u,pc,n,user);return
  super().step(u,pc,n,user)
 def read(self,u,access,address,n,value,user):
  if self.growth_active:self.growth_reader.read(u,access,address,n,value,user);return
  super().read(u,access,address,n,value,user)
 def write(self,u,access,address,n,value,user):
  if self.growth_active:self.growth_reader.write(u,access,address,n,value,user);return
  super().write(u,access,address,n,value,user)
reader_init,reader_service,growth_snapshot,require_growth_native,run_case,require_names,require_ctor_dispatch,require_personal_context,RECIPES=bindings()

def source_identities():
 result=J.source_identities()
 for p in (__file__,A.__file__):result[str(Path(p).resolve().relative_to(P.SOURCE))]=sha(Path(p).read_bytes())
 return result

def require_growth_context(r,data,member=4):
 p=r['growth_reader'];binding=r['growth_binding'];want=T.expected(data['constructor'],r['plus'])[0];cookie=want['fields']['otid']&65535
 need(type(member)is int and member in (4,2) and p is not None and p['same_cpu']is True and p['narc']==3 and p['member']==member and p['entry']==[DEST,3,member,cookie]+COOKIES+[IP,TOP,STOP|1,0x3F] and p['fill']==r['poison'] and p['clobber']is r['growth_clobber'] and type(r['growth_clobber'])is bool and p['rng_after']==want['ot_draws'][-1],'source-selected growth member and actual caller context')
 need(binding['neutral']is True and binding['regs']==p['entry'] and binding['ram_sha256']==p['unrelated_ram_sha256'] and binding['canary_preimages']==[dict(address=a,bytes=n,hex=('a5' if r['observe'] else '00')*n) for a,n in CANARIES],'growth neutral binding and eight exact allocation observer canaries')
 dead=(b'\xDD'*44 if r['observe'] else data['personal_reader']['2']['member']).hex();need(binding['dead_personal_before']==p['dead_personal_after']==dead and p['destination_before']=='00'*404 and len(bytes.fromhex(p['stack_frame_before']))==136 and len(bytes.fromhex(p['stack_guard_before']))==56,'growth actual freed personal observer poison and zeroed live destination provenance')
 need([list(e) for e in r['events'][:5]]==[['alloc',11,108,B.ARENA],['alloc',11,236,B.ARENA+128],['alloc',0,44,PERSONAL],['free',PERSONAL],['alloc',0,404,DEST]],'growth exact first allocation/free event chain without fabricated reads')
 need(p['destination_hex']==bytes(data['constructor']['archives'][3][member]).hex(),'source-selected growth delivery raw table member');return True

def require_case(r,data,q):
 need(r['growth_shadows']==[],'positive growth caller has no member shadow');require_growth_context(r,data);want=T.expected(data['constructor'],r['plus'])[0];require_growth_native(r['growth_reader'],data['growth_reader'],q['header_code'],want['ot_draws'][-1],4,want['fields']['otid']&65535);require_personal_context(r,data);J.require_personal_native(r['personal_reader'],data['personal_reader'],q['header_code'],want['ot_draws'][-1]);require_names(r,data,q);Y.require_header_context(r,data);Y.require_header_native(r['header_reader'],data['header'],q['header_code'],r['seed']);Z.require_prefix_context(r,data);Z.require_prefix_native(r['prefix_reader'],data['header'],q['header_code'],r['seed']);require_ctor_dispatch(r,data);need(r['ctor_start_steps']==Y.prefix_hook_contract(data,q)['total_before_constructor'],'source-bound unchanged growth caller prefix checkpoint');return True

def require_off_pair(on,off):
 parent=J.require_off_pair(on,off);a,b=on['growth_reader'],off['growth_reader'];ignored={'observe','native_writes','unrelated_ram_sha256','ram_sha256','projected_ram_sha256','dead_personal_after'};need(on['growth_clobber']is off['growth_clobber']is False and on['growth_shadows']==off['growth_shadows']==[] and a['observe']is True and b['observe']is False and b['native_writes']==[],'growth OFF domain and logs')
 need({k:v for k,v in a.items() if k not in ignored}=={k:v for k,v in b.items() if k not in ignored} and a['projected_ram_sha256']==b['projected_ram_sha256'],'growth OFF complete native FS/ABI/frame evidence and post-phase108B projection')
 for r in (on,off):
  p=r['growth_reader'];binding=r['growth_binding'];dead='dd'*44 if r['observe'] else on['personal_reader']['destination_hex'];need(binding['neutral']is True and binding['regs']==p['entry'] and binding['ram_sha256']==p['unrelated_ram_sha256'] and binding['canary_preimages']==[dict(address=a,bytes=n,hex=('a5' if r['observe'] else '00')*n) for a,n in CANARIES] and binding['dead_personal_before']==p['dead_personal_after']==dead,'growth OFF actual binding/eightcanaries and source-specific freed personal bytes')
 need(on['growth_binding']['projected_ram_sha256']==off['growth_binding']['projected_ram_sha256'],'growth OFF pre-phase RAM differs outside64Bcanaries+44Bdeadpersonal');return dict(neutral=True,parent=parent,scope='growth complete native FS/ABI/preexisting frame and phase RAM equal except eight allocation canaries64B plus observer-only poison of freed personal44B; inherited final scratch projection remains')

def close_binding():
 return A.rewrite(R,'require_counter',[("def require_counter(c,normal,data,code):","def require_counter(c,normal,data,code,expected_seed,expected_cookie3):",1),("variant in ('skip_close','short_payload')","variant=='skip_close'",1),("require_case(normal,data,code)","require_growth_native(normal,data,code,expected_seed,4,expected_cookie3)",1),("normal['narc']==56","normal['narc']==3",1),("normal['member']==31","normal['member']==4",1),("require_case(disguised,data,code)","require_growth_native(disguised,data,code,expected_seed,4,expected_cookie3)",1)],dict(TOP=TOP,DEST=DEST,require_growth_native=require_growth_native),'narc_reader')
require_close_native,CLOSE_RECIPE=close_binding()

def counter_record(r,data,q):
 disguised=copy.deepcopy(r);disguised['variant']='current';disguised['growth_reader']['variant']='current';disguised['growth_reader']['shadows']=[];disguised['growth_shadows']=[]
 try:require_case(disguised,data,q)
 except ValueError as e:return dict(variant=r['variant'],result=r,completed=True,tag_disguised=True,rejection=str(e))
 raise ValueError('growth caller counter accepted')

def require_counter(c,normal,data,q):
 require_case(normal,data,q);r=c['result'];variant=c['variant'];need(c['completed']is c['tag_disguised']is True and variant in ('growth_skip_close','growth_wrong_member') and r['variant']==variant and r['plus']==normal['plus']==1 and r['seed']==normal['seed']==0x12345678 and r['poison']==normal['poison']==0xC7 and r['observe']is True and r['growth_clobber']is False,'growth complete counter fixture domain');member=2 if variant=='growth_wrong_member' else 4;require_growth_context(r,data,member);require_personal_context(r,data,lookup_member=member);want=T.expected(data['constructor'],1)[0];seed,cookie=want['ot_draws'][-1],want['fields']['otid']&65535
 expected_binding=copy.deepcopy(normal['growth_binding'])
 if member==2:expected_binding['regs'][2]=2
 need(r['growth_binding']==expected_binding and all(r['growth_reader'][key]==normal['growth_reader'][key] for key in ('stack_frame_before','stack_guard_before','destination_before')),'growth counter actual pre-phase RAM/frame identical except declared member register')
 if variant=='growth_skip_close':
  need(r['growth_shadows']==[] and r['growth_reader']['variant']=='skip_close','growth Close sole mutation');require_close_native(dict(variant='skip_close',result=r['growth_reader'],tag_disguised=True,rejection=c['rejection']),normal['growth_reader'],data['growth_reader'],q['header_code'],seed,cookie);need(r['mon_hex']==normal['mon_hex'] and r['instructions']==normal['instructions']-1 and r['names']==normal['names'],'growth Close same complete party/names and skipped FS hook')
 else:
  need(r['growth_reader']['variant']=='current' and len(r['growth_shadows'])==1,'growth wrong member only argument shadow');shadow=r['growth_shadows'][0];after=r['growth_reader']['entry'];before=list(after);before[2]=4;need(shadow==dict(pc=hex(R.ENTRY),register='r2',before=before,after=after,reason='first native growth member4 to validmember2; getter curve and raw archive unchanged'),'growth argument4 to2 exact16-register source/prepared context');require_growth_native(r['growth_reader'],data['growth_counter'],q['header_code'],seed,2,cookie)
  exp=struct.unpack_from('<I',data['constructor']['archives'][3][2],want['fields']['level']*4)[0];need(r['mon_hex']==[J.expected_exp_packet(normal['mon_hex'][0],exp)]+normal['mon_hex'][1:] and r['instructions']==normal['instructions'] and len(r['names'])==len(normal['names'])==6 and J.names_without_scope_hashes(r['names'])==J.names_without_scope_hashes(normal['names']),'growth wrong table independently predicted EXP-only packet/native path and name evidence')
 expected_data=copy.deepcopy(data)
 if member==2:
  personal=bytearray(expected_data['constructor']['personal']['355']);personal[19]=2;expected_data['constructor']['personal']['355']=bytes(personal)
 replay=copy.deepcopy(r);replay['variant']='current';require_names(replay,expected_data,q);J.require_personal_native(replay['personal_reader'],data['personal_reader'],q['header_code'],seed);Y.require_header_context(replay,data);Y.require_header_native(replay['header_reader'],data['header'],q['header_code'],r['seed']);Z.require_prefix_context(replay,data);Z.require_prefix_native(replay['prefix_reader'],data['header'],q['header_code'],r['seed']);require_ctor_dispatch(replay,data)
 need(r['prefix']==normal['prefix'] and r['seed_after']==normal['seed_after'] and r['ctor_start_steps']==normal['ctor_start_steps'] and r['personal_reader']==normal['personal_reader'] and r['personal_binding']==normal['personal_binding'] and r['personal_shadows']==normal['personal_shadows']==[] and r['message']==normal['message'] and r['header_reader']==normal['header_reader'] and r['prefix_reader']==normal['prefix_reader'],'growth counter earlier native owners/Trainer/personal/seed unchanged')
 disguised=copy.deepcopy(r);disguised['variant']='current';disguised['growth_shadows']=[];disguised['growth_reader']['variant']='current';disguised['growth_reader']['shadows']=[]
 try:require_case(disguised,data,q)
 except ValueError as e:need(str(e)==c['rejection']==('source-selected growth member and actual caller context' if member==2 else 'native reader complete path/ownership/stack/frozen state'),'growth counter predicted source-bound rejection')
 else:raise ValueError('growth counter replay accepted')
 return True

def growth_lineage(paths,language):
 rows=[]
 for role,path in paths.items():
  model=P.G.S.SHARED.read_current(path,language) if role=='r4' else P.G.S.SHARED.read_image(path,language,role)
  with path.open('rb') as f,mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as raw:
   code=[]
   for address,n,count,digest in R.SPANS:
    blob=P.G.piece(model['segments'],address,n);instructions=list(R.Cs(R.CS_ARCH_ARM,R.CS_MODE_THUMB).disasm(blob,address));need(sha(blob)==digest and len(instructions)==count and sum(i.size for i in instructions)==n,'historical growth native reader code correspondence');code.append(dict(ram=hex(address),bytes=n,starts=count,sha256=digest))
   table=struct.unpack('<I',P.G.piece(model['segments'],0x2007520,4))[0];row=table+12;pointer=struct.unpack('<I',P.G.piece(model['segments'],row,4))[0];need(P.G.piece(model['segments'],pointer,8)==b'a/0/0/3\0','historical actual growth route');values={}
   for member in (4,2):
    r=resources(raw,member)['3'];values[str(member)]=dict(oracle=r['oracle'],exp27=struct.unpack_from('<I',r['member'],27*4)[0],exp29=struct.unpack_from('<I',r['member'],29*4)[0])
   rows.append(dict(role=role,input=model['record'],code=code,actual_route=dict(table_ram=hex(table),row_ram=hex(row),path_ram=hex(pointer),path='a/0/0/3'),resources=values,cpu_executed=False,limits=['Historical raw/code/path correspondence only, no historical caller/SDK execution or native compiler reconstruction; no inferred direct physical code offsets for compressed images']))
  del model;gc.collect();R.W.require_host_budget()
 return rows

def analyze(rom,language,objects,strategy_object,*,history=None,readback_only=False):
 R.W.require_host_budget();sources=source_identities();hist=growth_lineage(history,language) if history else None;model=P.G.S.SHARED.read_current(rom,language);positive=[];guards=[];controls=[];off=[];counters=[]
 with rom.open('rb') as f,mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as raw:
  q,proof=qualify(model,raw,language,objects,strategy_object)
  if readback_only:
   table=resources(raw);counter=resources(raw,2);need(source_identities()==sources,'growth readback source drift');return dict(schema='trainer31-native-growth-readback-v1',language=language,input=model['record'],source_sha256=sources,proof=proof,recipes=RECIPES,history=hist,growth_reader=table['3']['oracle'],growth_counter=counter['3']['oracle'],cpu_executed=False,compiler_invoked=False,limits=['Offline exact-code/object/path/member identity only; no native activation or semantic execution in this mode'])
  data=dict(preparation=Q.resources(raw),constructor=T.resources(model,raw,language,trainer=31),message=V.M.resources(raw),names=X.W.resources(raw),header=R.resources(raw),personal_reader=J.resources(raw),growth_reader=resources(raw),growth_counter=resources(raw,2))
  for plus in (0,1):
   for seed in (0x12345678,0x12345679):
    r=run_case(model,raw,language,q,data,plus,seed);require_case(r,data,q);positive.append(r);print(language,'native growth404/EXP caller',plus,hex(seed),'verified',flush=True)
   r=run_case(model,raw,language,q,data,plus,observe=False);off.append(dict(result=r,proof=require_off_pair(positive[-2],r)))
  normal=next(r for r in positive if r['plus']==1 and r['seed']==0x12345678);r=run_case(model,raw,language,q,data,poison=0x39);require_case(r,data,q);need(r['mon_hex']==normal['mon_hex'],'growth native actual stack preimage poison independence');guards.append(r)
  r=run_case(model,raw,language,q,data,growth_clobber=True);require_case(r,data,q);need(r['mon_hex']==normal['mon_hex'] and r['prefix']==normal['prefix'] and r['seed_after']==normal['seed_after'] and r['functional_ram_sha256']==normal['functional_ram_sha256'] and r['growth_reader']['ram_sha256']==normal['growth_reader']['ram_sha256'],'growth FS volatile clobber same game state and entire reader phase RAM');controls.append(r)
  for variant in ('growth_skip_close','growth_wrong_member'):
   r=run_case(model,raw,language,q,data,variant=variant);c=counter_record(r,data,q);require_counter(c,normal,data,q);counters.append(c)
  need(source_identities()==sources,'growth source drift during campaign');R.W.require_host_budget()
 return dict(schema='trainer31-native-growth-caller-v1',language=language,input=model['record'],source_sha256=sources,proof=proof,history=hist,recipes=RECIPES,close_recipe=CLOSE_RECIPE,prefix_hook_source_contract=Y.prefix_hook_contract(data,q),resources=dict(preparation=data['preparation'],constructor=T.resource_summary(data['constructor'],[r['body'] for r in positive+guards+controls]),message=data['message']['oracle'],names=data['names']['oracle'],header=data['header']['55']['oracle'],party_reader=data['header']['56']['oracle'],personal_reader=data['personal_reader']['2']['oracle'],growth_reader=data['growth_reader']['3']['oracle'],growth_counter=data['growth_counter']['3']['oracle']),positives=positive,guards=guards,volatile_controls=controls,observer_off=off,counters=counters,compiler_invoked=False,limits=['Initialized trainer31 caller, first growth3/4/404 only, explicit wrong-member2 counter; other185/187 reads retain original models','Five opaque FS services and original heap models; original native compiler/FSFile layout unavailable','Actual17-step getter/lookup/EXP setter flow keeps getter4 separate from delivered table4/2; no ROM/data fixture change','No natural encounter/card/full battle/UI/save/hardware proof','Reader frame136/guard56 captured before LoadGrowthTable POP; OFF phase excludes exact64B allocation canaries+44B dead-personal observer poison'])

def main():
 import argparse
 parser=argparse.ArgumentParser(description=__doc__)
 for name in ('rom','objects','strategy-object','json'):parser.add_argument('--'+name,type=Path,required=True)
 parser.add_argument('--language',choices=('EN','IT'),required=True);parser.add_argument('--readback-only',action='store_true')
 for name in ('retail','base','v4'):parser.add_argument('--'+name,type=Path)
 args=parser.parse_args()
 try:
  need(not args.json.exists() and not args.json.is_symlink(),'output must be fresh');output=args.json.resolve();need(P.SOURCE not in output.parents and output!=P.SOURCE,'output must be outside source');need(args.objects.resolve() not in output.parents and args.strategy_object.resolve().parent not in output.parents,'output must be outside retained object directories');need(all(p.is_file() for p in (args.rom,args.strategy_object,args.objects/'rematch-variants.o',args.objects/'rematch-stub.o')),'growth caller inputs must exist');extra=(args.retail,args.base,args.v4);need(not any(extra) or all(extra),'provide all three optional historical inputs');history=dict(retail=args.retail,base11=args.base,v4=args.v4,r4=args.rom) if all(extra) else None;result=analyze(args.rom,args.language,args.objects,args.strategy_object,history=history,readback_only=args.readback_only);payload=(json.dumps(result,separators=(',',':'))+'\n').encode();need(len(payload)<=32*1024**2,'expanded growth caller report budget');blob=gzip.compress(payload,mtime=0) if args.json.suffix=='.gz' else payload;need(len(blob)<=8*1024**2,'stored growth caller report budget');R.W.require_host_budget();args.json.parent.mkdir(parents=True,exist_ok=True)
  with args.json.open('xb') as f:f.write(blob)
 except ValueError as e:parser.exit(2,str(e)+'\n')
 print(args.language,'growth readback verified without CPU' if args.readback_only else 'first native growth404 reader/EXP caller verified; other reads and native FS models remain explicit')
if __name__=='__main__':main()
