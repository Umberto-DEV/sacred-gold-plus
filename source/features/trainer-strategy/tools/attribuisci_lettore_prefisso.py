#!/usr/bin/env python3
"""Trace native party56/31 parsing inside the complete trainer31 caller.

Requires the user's exact ROM and retained project objects. The parser executes
in the caller's CPU with five opaque FS models; other constructor reads remain
explicit models. No game or input file is modified.
"""
from pathlib import Path
import importlib.util,types,struct,copy,collections,json,gzip,mmap,gc,sys

def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
Y=load('prefix_header_parent',Path(__file__).with_name('attribuisci_lettore_chiamante.py'))
A=load('prefix_caller_adapter',Path(__file__).parents[1]/'test/prefix_narc_bench.py');A.bind(Y)
X,R,V,U,B,T,P,Q,N=Y.X,Y.R,Y.V,Y.U,Y.B,Y.T,Y.P,Y.Q,Y.N
need,sha,OUTER,INNER=Y.need,Y.sha,Y.OUTER,Y.INNER
TOP=INNER-200;DEST=B.ARENA;STOP=0x226B4A6;IP=DEST+352
COOKIES=[B.SETUP,Q.NAME,DEST+128,4]+list(N.COOKIES[4:])
CANARIES=((DEST-8,8),(DEST+108,8),(DEST+120,8),(DEST+364,8))
from unicorn.arm_const import UC_ARM_REG_PC

def qualify(*args):return Y.qualify(*args)
def canaries_before(reader):
 return all(reader.read_bytes(a,n)==reader.before[a-0x2000000:a-0x2000000+n] for a,n in CANARIES[:2])
def bind_reader(driver):
 namespace=dict(vars(R));bound=type('PrefixReader',(R.Reader,),{});namespace.update(TOP=TOP,DEST=DEST,STOP=STOP,Reader=bound)
 for name,method in vars(R.Reader).items():
  if isinstance(method,types.FunctionType):
   fn=types.FunctionType(method.__code__,namespace,method.__name__,method.__defaults__,method.__closure__);fn.__kwdefaults__=method.__kwdefaults__;setattr(bound,name,fn)
 need({k for k in namespace if namespace[k]is not vars(R).get(k)}=={'TOP','DEST','STOP','Reader'},'prefix exact observer namespace')
 r=bound(dict(segments=driver.bench.segments),driver.qualified['header_code'],{'56':driver.data['header']['56']},56,fill=driver.poison,observe=driver.observe,clobber=driver.prefix_clobber,variant={'prefix_skip_close':'skip_close','prefix_short_read':'short_payload'}.get(driver.prefix_variant,'current'));r.u=driver.u;r.entry=r.regs();r.before=r.read_bytes(0x2000000,0x400000);return r

class Driver(Y.Driver):
 latest=None
 def __init__(self,*args,prefix_clobber=False,**kwargs):
  variant=kwargs.pop('variant','current');need(variant in ('current','prefix_skip_close','prefix_short_read') and type(prefix_clobber)is bool,'finite native prefix caller controls');super().__init__(*args,variant='current',**kwargs);Driver.latest=self;self.prefix_variant=variant;self.prefix_clobber=prefix_clobber;self.prefix_reader=None;self.prefix_active=False;self.prefix_result=None;self.prefix_binding=None;self.prefix_handback=None
 def start_prefix(self):
  regs=self.regs();need(self.stage=='ctor' and not self.audit.body and self.prefix_reader is None and not self.header_active and not self.message_active and not self.name_active and regs==[DEST,56,31,0x2007509]+COOKIES+[IP,TOP,STOP|1,0x3F],'native prefix actual activation and source-derived ABI')
  before=self.read_bytes(0x2000000,0x400000);self.prefix_reader=bind_reader(self);need(self.prefix_reader.u is self.u and regs==self.regs() and before==self.read_bytes(0x2000000,0x400000),'native prefix observer neutral binding');self.prefix_binding=dict(neutral=True,regs=regs,ram_sha256=sha(before),projected_ram_sha256=P.masked_hash(before,[(a,a+n) for a,n in CANARIES]),canary_preimages=[dict(address=a,bytes=n,hex=self.read_bytes(a,n).hex()) for a,n in CANARIES]);self.prefix_active=True
 def finish_prefix(self):
  r=self.prefix_reader;self.prefix_result=prefix_snapshot(r);self.prefix_result.update(same_cpu=r.u is self.u,stack_frame_before=r.before[TOP-136-0x2000000:TOP-0x2000000].hex(),stack_guard_before=r.before[TOP-192-0x2000000:TOP-136-0x2000000].hex(),destination_before=r.before[DEST-0x2000000:DEST-0x2000000+108].hex(),projected_ram_sha256=P.masked_hash(self.read_bytes(0x2000000,0x400000),[(a,a+n) for a,n in CANARIES]));self.prefix_active=False
 def step(self,u,pc,n,user):
  if self.prefix_active and pc==STOP:self.finish_prefix()
  if self.stage=='ctor' and pc==R.ENTRY and self.regs()[1:3]==[56,31]:self.start_prefix()
  if self.prefix_active:
   self.steps+=1;sp=self.regs()[13];need(self.steps<=3000000 and OUTER-608<=sp<=INNER,'native prefix full caller stack/instruction bounds');self.max_stack=max(self.max_stack,OUTER-sp);self.prefix_reader.step(u,pc,n,user);return
  if self.stage=='ctor' and pc==B.SEAM_RESUME:
   need(self.prefix_result is not None and self.prefix_handback is None,'single prefix return to constructor');self.prefix_handback=dict(pc=hex(pc),regs=self.regs(),buffer_hex=self.read_bytes(DEST,108).hex(),seed=self.word(0x21D15A8),unloads=self.audit.unloads)
  super().step(u,pc,n,user)
 def read(self,u,access,address,n,value,user):
  if self.prefix_active:self.prefix_reader.read(u,access,address,n,value,user);return
  super().read(u,access,address,n,value,user)
 def write(self,u,access,address,n,value,user):
  if self.prefix_active:self.prefix_reader.write(u,access,address,n,value,user);return
  super().write(u,access,address,n,value,user)

def bindings():
 evidence,p1=A.rewrite(V.A,'constructor_evidence',A.inherited(0,[("'0x20d8b6c', 'ReadWholeNarcMemberByIdPair', '0x20d88c0'","'0x20d8b6c', '0x20d88c0'",1),(" and (prefix_models[8]['args'][:3] == [B.ARENA, 56, 31])","",1),("[['alloc', 11, 108, B.ARENA], ['alloc', 11, 236, B.ARENA + 128], ['read', 56, 31, B.ARENA, 108]]","[['alloc', 11, 108, B.ARENA], ['alloc', 11, 236, B.ARENA + 128]]",1)]),{},'constructor_oracle');A.constructor_evidence=evidence;A.CONSTRUCTOR_RECIPE=p1
 snapshot,p2=A.rewrite(R,'Reader.run',[("self.setup();self.u.emu_start(ENTRY|1,STOP,count=20001);","",1),("list(N.COOKIES)","list(COOKIES)",1),("self.read_bytes(DEST-16,16)==b'\\xA5'*16 and self.read_bytes(DEST+size,124-size)==b'\\xA5'*(124-size)","canaries_before(self)",1),("self.read_bytes(TOP-192,56)==bytes([self.fill])*56","self.read_bytes(TOP-192,56)==self.before[TOP-192-0x2000000:TOP-136-0x2000000]",1)],dict(TOP=TOP,DEST=DEST,STOP=STOP,COOKIES=COOKIES,canaries_before=canaries_before),'narc_reader')
 native,p3=A.rewrite(R,'require_case',[("def require_case(r,data,code):","def require_case(r,data,code,expected_seed):",1),("r['rng_after']==0x12345678","r['rng_after']==expected_seed",1),("cookies=list(N.COOKIES)","cookies=list(COOKIES)",1),("cookie3=0x33333303","cookie3=0x2007509",1),("0xCCCC000C","IP",3),("stack=bytearray([r['fill']])*136","stack=bytearray.fromhex(r['stack_frame_before']);need(len(stack)==136,'actual reader stack preimage size')",1)],dict(TOP=TOP,DEST=DEST,STOP=STOP,COOKIES=COOKIES,IP=IP),'narc_reader')
 run,p4=A.rewrite(V,'run_case',A.inherited(3,[("header_clobber=False):","header_clobber=False,prefix_clobber=False):",1),("header_clobber=header_clobber)","header_clobber=header_clobber,prefix_clobber=prefix_clobber)",1),("return dict(ctor_start_steps=","return dict(prefix_reader=driver.prefix_result,prefix_binding=driver.prefix_binding,prefix_handback=driver.prefix_handback,prefix_clobber=driver.prefix_clobber,ctor_start_steps=",1)]),dict(Driver=Driver,A=A,NAME_ARENA=X.NAME_ARENA,NAME_END=X.NAME_END),'message_caller')
 # Replace the already enumerated P50 formula edit before replaying it.
 edits=A.inherited(4);old=next(i for i,e in enumerate(edits) if 'body' in e[0] and '+158' in e[0]);before,after,count=edits[old];edits[old]=(before,after.replace("+157","+r['prefix_reader']['instructions']+157"),count)
 parent,p5=A.rewrite(V,'require_case',edits,dict(A=A,V=V),'message_caller');names,p6=A.rewrite(X,'require_case',[],dict(require_parent=parent),'species_caller')
 dispatch,p7=A.rewrite(Y,'require_ctor_dispatch',[("expected_count=188+2*r['plus']","expected_count=187+2*r['plus']",1),("len(prefix)==1 and len(records)==len(events)==1+len(body)","prefix==[] and len(records)==len(events)==len(body)",1),("{56:1,2:78","{2:78",1),("  if position==0:need(before[14]==0x226B4A7 and before[4:12]==[B.SETUP,Q.NAME,B.ARENA+128,4]+list(N.COOKIES[4:]),'qualified inherited prefix reader loop actual caller context')\n  else:need(","  need(",1)],{},'header_caller')
 return snapshot,native,run,names,dispatch,[p1,p2,p3,p4,p5,p6,p7]
prefix_snapshot,require_prefix_native,run_case,require_names,require_ctor_dispatch,RECIPES=bindings()

def require_prefix_context(r,data):
 p=r['prefix_reader'];binding=r['prefix_binding'];h=r['prefix_handback'];need(p is not None and p['same_cpu']is True and p['narc']==56 and p['fill']==r['poison'] and p['clobber']is r['prefix_clobber'] and type(r['prefix_clobber'])is bool and p['rng_after']==r['seed'] and binding['neutral']is True and binding['regs']==p['entry'] and binding['ram_sha256']==p['unrelated_ram_sha256'],'prefix actual CPU/fixture/phase context')
 need(p['destination_before']=='00'*108 and [list(e) for e in r['events'][:2]]==[['alloc',11,108,DEST],['alloc',11,236,DEST+128]],'prefix buffer prezero from actual original allocation model')
 expected=[dict(address=a,bytes=n,hex=('a5' if r['observe'] else '00')*n) for a,n in CANARIES];need(binding['canary_preimages']==expected,'prefix four exact allocation observer canary preimages')
 need(len(bytes.fromhex(p['stack_frame_before']))==136 and len(bytes.fromhex(p['stack_guard_before']))==56,'prefix actual preexisting stack dimensions')
 transition=r['body']['prefix_transition'];regs=h['regs'];need(h['pc']==transition['pc']==hex(B.SEAM_RESUME) and h['regs']==transition['regs'] and h['seed']==transition['seed']==r['seed'] and h['buffer_hex']==transition['buffer_hex']==p['destination_hex']==data['header']['56']['member'].hex() and h['unloads']==1 and regs[0]==p['end'][0] and regs[4:12]==COOKIES and regs[13]==INNER-152,'actual native reader result forwarded through module and unload to seam')
 return True

def require_case(r,data,q):
 require_names(r,data,q);Y.require_header_context(r,data);Y.require_header_native(r['header_reader'],data['header'],q['header_code'],r['seed']);require_ctor_dispatch(r,data);require_prefix_context(r,data);require_prefix_native(r['prefix_reader'],data['header'],q['header_code'],r['seed']);need(r['ctor_start_steps']==Y.prefix_hook_contract(data,q)['total_before_constructor'],'source-bound unchanged pre-constructor checkpoint');return True

def require_off_pair(on,off):
 parent=X.require_off_pair(on,off);header=R.require_off_pair(on['header_reader'],off['header_reader']);a,b=on['prefix_reader'],off['prefix_reader'];ignored={'observe','native_writes','unrelated_ram_sha256','ram_sha256','projected_ram_sha256'};need(a['observe']is True and b['observe']is False and b['native_writes']==[] and {k:v for k,v in a.items() if k not in ignored}=={k:v for k,v in b.items() if k not in ignored},'prefix functional OFF/ON transport/ABI/frame mismatch');need(a['projected_ram_sha256']==b['projected_ram_sha256'] and on['prefix_binding']['projected_ram_sha256']==off['prefix_binding']['projected_ram_sha256'],'prefix OFF/ON full phase RAM excluding only four source-proven allocation canaries');need(on['prefix_clobber']is off['prefix_clobber']is False,'prefix OFF control domain');
 for receipt in (on,off):
  pr=receipt['prefix_reader'];pb=receipt['prefix_binding'];need(pb['neutral']is True and pb['regs']==pr['entry'] and pb['ram_sha256']==pr['unrelated_ram_sha256'] and pb['canary_preimages']==[dict(address=a,bytes=n,hex=('a5' if receipt['observe'] else '00')*n) for a,n in CANARIES],'prefix OFF actual entry binding and source canary preimages')
 need(on['ctor_read_dispatch']==off['ctor_read_dispatch'] and on['header_binding']==off['header_binding'] and on['prefix_handback']['unloads']==1 and off['prefix_handback']['unloads']==0 and {k:v for k,v in on['prefix_handback'].items() if k!='unloads'}=={k:v for k,v in off['prefix_handback'].items() if k!='unloads'} and on['ctor_start_steps']==off['ctor_start_steps'],'prefix OFF/ON owners and actual handback unchanged');return dict(neutral=True,parent=parent,header=header,scope='actual prefix all transport/ABI/preexisting stack and phase RAM equal except four allocation observer canaries (32 bytes); inherited constructor scratch projection remains')

def source_identities():
 result=Y.source_identities()
 for path in (__file__,A.__file__):result[str(Path(path).resolve().relative_to(P.SOURCE))]=sha(Path(path).read_bytes())
 return result


def counter_binding():
 return A.rewrite(R,'require_counter',[("image=payload+b'\\xA5'","image=payload+bytes.fromhex(normal['destination_before'])[-1:]",1),("image!=data['56']['member']","image==data['56']['member']",1),("r['ram_sha256']!=normal['ram_sha256']","r['ram_sha256']==normal['ram_sha256']",1),("reason='native parser exact independently selected payload'","reason='native reader complete path/ownership/stack/frozen state'",1)],dict(TOP=TOP,DEST=DEST,require_case=lambda receipt,data,code:require_prefix_native(receipt,data,code,0x12345678)),'narc_reader')
require_prefix_counter,COUNTER_RECIPE=counter_binding()

def counter_record(r,data,q):
 disguised=copy.deepcopy(r);disguised['variant']='current';disguised['prefix_reader']['variant']='current';disguised['prefix_reader']['shadows']=[]
 try:require_case(disguised,data,q)
 except ValueError as e:return dict(variant=r['variant'],completed=True,result=r,tag_disguised=True,rejection=str(e))
 raise ValueError('native prefix caller counter accepted')

def require_counter(c,normal,data,q):
 require_case(normal,data,q);r=c['result'];p=r['prefix_reader'];variant=c['variant'];need(c['completed']is True and c['tag_disguised']is True and variant in ('prefix_skip_close','prefix_short_read') and r['variant']==variant and r['plus']==normal['plus']==1 and r['seed']==normal['seed']==0x12345678 and r['poison']==normal['poison']==0xC7 and r['observe']is True and r['prefix_clobber']is False,'prefix counter exact complete baseline domain')
 require_prefix_counter(dict(variant=p['variant'],result=p,tag_disguised=True,rejection=c['rejection']),normal['prefix_reader'],data['header'],q['header_code'])
 replay=copy.deepcopy(r);replay['variant']='current';require_names(replay,data,q);Y.require_header_context(replay,data);Y.require_header_native(replay['header_reader'],data['header'],q['header_code'],r['seed']);require_ctor_dispatch(replay,data);require_prefix_context(replay,data)
 need(p['variant']==('skip_close' if variant=='prefix_skip_close' else 'short_payload') and r['mon_hex']==normal['mon_hex'] and r['decoded']==normal['decoded'] and r['prefix']==normal['prefix'] and r['seed_after']==normal['seed_after'] and r['end']==normal['end'] and r['message']==normal['message'] and r['names']==normal['names'] and r['ctor_read_dispatch']==normal['ctor_read_dispatch'] and r['header_reader']==normal['header_reader'] and r['header_binding']==normal['header_binding'] and r['prefix_binding']==normal['prefix_binding'] and r['ctor_start_steps']==normal['ctor_start_steps'],'prefix late counter identical complete party/Trainer/seed and separate owners')
 need(r['instructions']==normal['instructions']-(variant=='prefix_skip_close') and r['functional_ram_sha256']==normal['functional_ram_sha256'] and r['unrelated_ram_sha256']==normal['unrelated_ram_sha256'],'prefix counter source step delta and declared final RAM projections')
 return True

def analyze(rom,language,objects,strategy_object):
 R.W.require_host_budget();sources=source_identities();model=P.G.S.SHARED.read_current(rom,language);positive=[];guards=[];controls=[];off=[];counters=[]
 with rom.open('rb') as f,mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as raw:
  q,proof=qualify(model,raw,language,objects,strategy_object);data=dict(preparation=Q.resources(raw),constructor=T.resources(model,raw,language,trainer=31),message=V.M.resources(raw),names=X.W.resources(raw),header=R.resources(raw))
  for plus in (0,1):
   for seed in (0x12345678,0x12345679):
    r=run_case(model,raw,language,q,data,plus,seed);require_case(r,data,q);positive.append(r);print(language,'native prefix full caller',plus,hex(seed),'verified',flush=True)
   r=run_case(model,raw,language,q,data,plus,observe=False);off.append(dict(result=r,proof=require_off_pair(positive[-2],r)))
  normal=next(r for r in positive if r['plus']==1 and r['seed']==0x12345678);r=run_case(model,raw,language,q,data,poison=0x39);require_case(r,data,q);need(r['mon_hex']==normal['mon_hex'],'native prefix caller stack poison independence');guards.append(r)
  r=run_case(model,raw,language,q,data,prefix_clobber=True);require_case(r,data,q);need(r['mon_hex']==normal['mon_hex'] and r['prefix']==normal['prefix'] and r['seed_after']==normal['seed_after'] and r['functional_ram_sha256']==normal['functional_ram_sha256'] and r['prefix_reader']['ram_sha256']==normal['prefix_reader']['ram_sha256'],'native prefix FS volatile control same declared game state and entire reader phase RAM');controls.append(r)
  for variant in ('prefix_skip_close','prefix_short_read'):
   r=run_case(model,raw,language,q,data,variant=variant);c=counter_record(r,data,q);require_counter(c,normal,data,q);counters.append(c)
  need(source_identities()==sources,'native prefix caller source drift during campaign');R.W.require_host_budget()
 return dict(schema='trainer31-native-prefix-caller-v1',language=language,input=model['record'],source_sha256=sources,proof=proof,recipes=RECIPES,counter_recipe=COUNTER_RECIPE,prefix_hook_source_contract=Y.prefix_hook_contract(data,q),resources=dict(preparation=data['preparation'],constructor=T.resource_summary(data['constructor'],[r['body'] for r in positive+guards+controls]),message=data['message']['oracle'],names=data['names']['oracle'],header=data['header']['55']['oracle'],party_reader=data['header']['56']['oracle']),positives=positive,guards=guards,volatile_controls=controls,observer_off=off,counters=counters,compiler_invoked=False,limits=['Initialized trainer31 caller, Plus0/1, two seeds/two poisons; native header55 and initial party56 only','Remaining187 Normal/189 Plus ReadWhole calls use original explicit models; five FS services retain opaque state','Original native compiler and native FSFile layout unavailable; no original native binary reconstruction claimed','No natural encounter, whole battle, hardware, raw-save, UI or error-path proof','Actual prefix preexisting frame and phase RAM frozen before module return; OFF projection excludes four known allocation canaries (32 bytes)'])

def main():
 import argparse
 parser=argparse.ArgumentParser(description=__doc__)
 for name in ('rom','objects','strategy-object','json'):parser.add_argument('--'+name,type=Path,required=True)
 parser.add_argument('--language',choices=('EN','IT'),required=True);args=parser.parse_args()
 try:
  need(not args.json.exists() and not args.json.is_symlink(),'output must be fresh');output=args.json.resolve();need(P.SOURCE not in output.parents and output!=P.SOURCE,'output must be outside source');need(args.objects.resolve() not in output.parents and args.strategy_object.resolve().parent not in output.parents,'output must be outside retained object directories');need(all(p.is_file() for p in (args.rom,args.strategy_object,args.objects/'rematch-variants.o',args.objects/'rematch-stub.o')),'native prefix caller inputs must exist');result=analyze(args.rom,args.language,args.objects,args.strategy_object);payload=(json.dumps(result,separators=(',',':'))+'\n').encode();need(len(payload)<=32*1024**2,'expanded prefix caller report budget');blob=gzip.compress(payload,mtime=0) if args.json.suffix=='.gz' else payload;need(len(blob)<=8*1024**2,'stored prefix caller report budget');R.W.require_host_budget();args.json.parent.mkdir(parents=True,exist_ok=True)
  with args.json.open('xb') as f:f.write(blob)
 except ValueError as e:parser.exit(2,str(e)+'\n')
 print(args.language,'native party parser/caller composition verified; other reads and FS SDK models remain explicit')
if __name__=='__main__':main()
