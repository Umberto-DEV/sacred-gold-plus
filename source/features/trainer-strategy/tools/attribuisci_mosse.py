#!/usr/bin/env python3
"""Follow trainer21's edited buffer through the actual four native move/PP setters.

The post-CreateMon boundary uses a copied, authenticated prior-case Pokemon fixture.
It does not construct Scyther or establish a natural trainer encounter.
"""
from pathlib import Path
import importlib.util,mmap,json,gzip,struct,copy
s=importlib.util.spec_from_file_location('positive_strategy_dependency',Path(__file__).with_name('attribuisci.py'));S=importlib.util.module_from_spec(s);s.loader.exec_module(S)
F,M,P,C,B=S.F,S.M,S.P,S.C,S.B;need=S.need
START,STOP=0x2073A22,0x2073A42
VARIANTS=('current','wrong_move','wrong_pp','preapplied_skip')


def load_fixture(report_path,model,raw):
 need(report_path.stat().st_size<=16*1024*1024,'fixture compressed size bound')
 with (gzip.open(report_path,'rb') if report_path.suffix=='.gz' else report_path.open('rb')) as file:payload=file.read(16*1024*1024+1)
 need(len(payload)<=16*1024*1024,'fixture expanded size bound');report=json.loads(payload);need(report['schema']=='rematch-complete-constructor-v1' and report['input']==json.loads(json.dumps(model['record'])),'fixture report exact input/schema identity');prior=report['positives'][0];F.require_complete(prior,F.resources(raw,model));fixture=bytes.fromhex(prior['first']['mon']['workspace_hex']);decoded=M.decode(fixture);need(decoded['flags']==0 and decoded['checksum_ok'] and len(fixture)==236,'fixture checked extent/checksum/quiescent flags');return fixture,dict(report_sha256=P.sha(report_path.read_bytes()),input=report['input'],positive_index=0,trainer=prior['trainer'],seed=prior['seed'],source_sha256=report['source_sha256'],mon_sha256=P.sha(fixture),species=decoded['species'],boundary='copy of prior first completed Mon;initialized post-CreateMon/held-item move boundary,not a constructed Scyther')


def with_pp_up(fixture,slot=1,value=2):
 need(slot==1 and value==2,'named PP-up fixture transform domain');pid,flags,checksum=struct.unpack_from('<IHH',fixture);blocks=bytearray(B._decrypt(fixture[8:136],checksum));order=B.PERMUTATIONS[((pid>>13)&31)%24];blocks[32*order.index(1)+12+slot]=value;new=sum(struct.unpack('<64H',blocks))&65535;out=bytearray(fixture);struct.pack_into('<H',out,6,new);out[8:136]=B._decrypt(bytes(blocks),new);need(M.decode(out)['checksum_ok'] and M.decode(out)['pp_ups'][slot]==value,'PP-up fixture reseal');return bytes(out)


class Loop(S.Hook):
 latest=None
 def __init__(self,*args,**kwargs):
  self.move=None;self.record_reads=[];self.loop_variant='current';self.loop_shadows=[];self.counter_done=False;super().__init__(*args,**kwargs);Loop.latest=self
 def step(self,u,a,n,unused):
  if self.move is None:return super().step(u,a,n,unused)
  if a==STOP:
   need(not self.move.pending_native and self.move.pending_service is None,'move loop incomplete return');u.emu_stop();return
  if self.loop_variant=='preapplied_skip' and a==0x2073A32 and self.reg(2)==1:
   need(not self.counter_done and P.G.S.SHARED.branch(bytes(u.mem_read(a,4)),a,'bl')==0x20714E8,'named skipped move call preimage');self.counter_done=True;self.loop_shadows.append(dict(kind='pc',pc=hex(a),before=hex(a),after='0x2073a36',reason='skip slot1 only on preapplied fixture'));u.reg_write(P.UC_ARM_REG_PC,0x2073A37);return
  if self.loop_variant=='wrong_move' and a==0x2073A32 and self.reg(2)==1:
   need(not self.counter_done and self.reg(1)==450,'wrong-move argument preimage');self.counter_done=True;self.loop_shadows.append(dict(kind='r1',pc=hex(a),before=450,after=206));u.reg_write(B.R[1],206)
  event=self.move.pending_service;M.First.step(self.move,u,a,n,unused)
  if event and a==event['return_pc'] and self.loop_variant=='wrong_pp' and event['args'][2]==450:
   need(not self.counter_done,'wrong PP shadow repeated');ptr=event['output_pointer']+6;old=bytes(u.mem_read(ptr,1));need(old==b'\x14','wrong PP exact copied-resource preimage');u.mem_write(ptr,b'\x15');self.counter_done=True;self.loop_shadows.append(dict(kind='ram',pc=hex(a),address=hex(ptr),before='14',after='15',reason='after exact raw copy validation,before native PP read'))
  if a in B.STUBS:
   event=self.move.pending_service;args=event['args'];need(event['name']=='ReadWholeNarcMemberByIdPair' and args[1]==11 and event['bytes']==16,'only reused16-byte move member model is allowed');payload=self.move.bench.archives.files(B.narc_path(args[1]))[args[2]];u.mem_write(args[0],bytes(payload));u.reg_write(B.R[0],B.LOADER_RESULT);u.reg_write(P.UC_ARM_REG_PC,u.reg_read(C.UC_ARM_REG_LR))
 def write(self,u,access,a,n,value,unused):
  if self.move is None:return super().write(u,access,a,n,value,unused)
  M.First.write(self.move,u,access,a,n,value,unused)
 def read(self,u,access,a,n,value,unused):
  if self.move is None:return super().read(u,access,a,n,value,unused)
  M.First.read(self.move,u,access,a,n,value,unused)
  if B.ARENA<=a and a+n<=B.ARENA+108:self.record_reads.append(dict(pc=hex(u.reg_read(P.UC_ARM_REG_PC)),offset=a-B.ARENA,bytes=n,value=int.from_bytes(u.mem_read(a,n),'little')))


def run_case(model,raw,language,code,data,fixture,plus=1,variant='current',poison=False,pp_up=False,preapplied=None):
 need(plus in (0,1) and variant in VARIANTS and (variant=='current' or plus==1 and not poison and not pp_up),'move fixture domain');need(type(poison)is bool and type(pp_up)is bool,'move guard domains')
 with P.patch.object(S,'Hook',Loop):prefix=S.run_group(model,code,data,21,plus)
 S.require_group(prefix,data);h=Loop.latest;u=h.cpu;before_observe=(P.sha(bytes(u.mem_read(0x2000000,0x400000))),[u.reg_read(r) for r in B.R]);prefix=copy.deepcopy(prefix);need(before_observe==(P.sha(bytes(u.mem_read(0x2000000,0x400000))),[u.reg_read(r) for r in B.R]),'move prefix observer neutrality')
 prefix_checkpoint=dict(regs=[u.reg_read(r) for r in B.R]+[u.reg_read(P.UC_ARM_REG_SP),u.reg_read(C.UC_ARM_REG_LR),u.reg_read(P.UC_ARM_REG_CPSR)],pc=u.reg_read(P.UC_ARM_REG_PC),ram_sha256=before_observe[0],mon_sha256=P.sha(bytes(u.mem_read(S.MON,236))),frame64_hex=bytes(u.mem_read(S.STACK-152+0x64,4)).hex())
 source_fixture=fixture
 if pp_up:fixture=with_pp_up(fixture)
 if variant=='preapplied_skip':need(preapplied is not None and M.decode(preapplied)['checksum_ok'],'preapplied fixture needs checked prior actual output');fixture=preapplied
 bench=P.Adapter(model,raw,language);bench.module_code={};audit=M.First(bench,21,plus=plus);audit.uc=u;audit.mon=True;audit.mon_allowed,audit.mon_data=M.qualify(model,language);audit.mon_variant='current';audit.poison=poison;audit.pending_native=[];audit.live={};audit.next_arena=B.ARENA+512;audit.instructions=0;audit.max_stack=0
 bridge=[]
 def initialize(address,payload,reason):
  bridge.append(dict(address=hex(address),bytes=len(payload),before_sha256=P.sha(bytes(u.mem_read(address,len(payload)))),after_sha256=P.sha(payload),reason=reason));u.mem_write(address,payload)
 initialize(S.MON,fixture,'checked copied Mon fixture'+(';PP-up slot1=2' if pp_up else ';preapplied output fixture' if variant=='preapplied_skip' else ''))
 old_sp=u.reg_read(P.UC_ARM_REG_SP);old_cpsr=u.reg_read(P.UC_ARM_REG_CPSR);u.reg_write(P.UC_ARM_REG_CPSR,0xB000003F);u.reg_write(P.UC_ARM_REG_SP,S.STACK-152);initialize(S.STACK-152+0x64,struct.pack('<I',S.BUFFER+90),'initialized native current-record pointer for last trainer21 member');h.move=audit;h.loop_variant=variant
 before=bytes(u.mem_read(0x2000000,0x400000));entry=audit.regs();u.emu_start(START|1,STOP,count=500000);need(u.reg_read(P.UC_ARM_REG_PC)==STOP,'move loop actual stop boundary');final=bytes(u.mem_read(S.MON,236));ignored=((S.STACK-512,S.STACK),(S.MON,S.MON+236));frozen=P.masked_hash(before,ignored);need(frozen==P.masked_hash(bytes(u.mem_read(0x2000000,0x400000)),ignored),'unrelated move-loop RAM changed');need(not audit.live and not audit.pending_native and audit.pending_service is None,'move modeled resource/native return closure');need((variant=='current')== (not h.counter_done),'named move counter was not exercised')
 return dict(language=language,plus=plus,variant=variant,poison=poison,pp_up=pp_up,prefix=prefix,prefix_observer_neutral=True,prefix_checkpoint=prefix_checkpoint,source_fixture_sha256=P.sha(source_fixture),fixture_sha256=P.sha(fixture),before=fixture.hex(),after=final.hex(),decoded_before=M.decode(fixture),decoded_after=M.decode(final),bridge=bridge,register_initialization=dict(old_sp=old_sp,new_sp=S.STACK-152,old_cpsr=old_cpsr,new_cpsr=0xB000003F),entry=entry,end=audit.regs(),reads=h.record_reads,calls=audit.native_calls,models=audit.mon_models,shadows=h.loop_shadows,instructions=audit.instructions,max_stack=audit.max_stack,code=[dict(ram=hex(a),bytes=n,thumb=t) for a,n,t in sorted(audit.mon_code)],buffer_sha256=P.sha(bytes(u.mem_read(S.BUFFER,108))),unrelated_ram_sha256=frozen,unrelated_ram_unchanged=True)


def require_case(r,data,moves,fixture):
 need(r['variant']=='current' and r['language'] in ('EN','IT') and r['plus'] in (0,1) and type(r['poison'])is bool and type(r['pp_up'])is bool and not r['shadows'],'normal move fixture domain');S.require_group(r['prefix'],data);need(r['prefix']['trainer']==21 and r['prefix']['plus']==r['plus'] and r['prefix_observer_neutral'],'move prefix exact trainer/mode/observer');expected_fixture=with_pp_up(fixture) if r['pp_up'] else fixture;need(r['source_fixture_sha256']==P.sha(fixture) and r['fixture_sha256']==P.sha(expected_fixture) and r['before']==expected_fixture.hex(),'move fixture provenance/initialized boundary')
 checkpoint=r['prefix_checkpoint'];need(checkpoint['pc']==S.END and checkpoint['regs'][:12]==r['prefix']['calls'][-1]['regs'] and checkpoint['regs'][13]==S.STACK and checkpoint['regs'][15]==0x3F and checkpoint['mon_sha256']==P.sha(bytes(236)) and len(bytes.fromhex(checkpoint['frame64_hex']))==4 and len(checkpoint['ram_sha256'])==64,'exact P33 prefix checkpoint before initialized boundary');expected_bridge=[dict(address=hex(S.MON),bytes=236,before_sha256=checkpoint['mon_sha256'],after_sha256=P.sha(expected_fixture),reason='checked copied Mon fixture'+(';PP-up slot1=2' if r['pp_up'] else '')),dict(address=hex(S.STACK-152+0x64),bytes=4,before_sha256=P.sha(bytes.fromhex(checkpoint['frame64_hex'])),after_sha256=P.sha(struct.pack('<I',S.BUFFER+90)),reason='initialized native current-record pointer for last trainer21 member')];need(r['bridge']==expected_bridge,'exact two initialized host writes at the documented boundary');need(r['register_initialization']==dict(old_sp=S.STACK,new_sp=S.STACK-152,old_cpsr=checkpoint['regs'][15],new_cpsr=0xB000003F),'exact initialized stack/mode transition');entry=list(checkpoint['regs']);entry[13]=S.STACK-152;entry[15]=0xB000003F;need(r['entry']==entry,'move entry registers derive only from declared prefix transition')
 actual=M.decode(bytes.fromhex(r['after']));before=M.decode(expected_fixture);need(r['decoded_before']==before and r['decoded_after']==actual and actual['checksum_ok'] and actual['flags']==0,'independent move record decode/checksum/flags');buffer=bytes.fromhex(data['records']['21']['after' if r['plus'] else 'before']);wanted=list(struct.unpack_from('<4H',buffer,98));pp=[moves[move][6]+(moves[move][6]*20*before['pp_ups'][i])//100 for i,move in enumerate(wanted)];expected=dict(before,moves=wanted,pp=pp);expected.pop('checksum');observed=dict(actual);observed.pop('checksum');need(observed==expected,'move/PP/raw resource and every other field oracle');original_raw=bytes.fromhex(r['before']);final_raw=bytes.fromhex(r['after']);pid=struct.unpack_from('<I',original_raw)[0];clear=bytearray(B._decrypt(original_raw[8:136],struct.unpack_from('<H',original_raw,6)[0]));order=B.PERMUTATIONS[((pid>>13)&31)%24];base=32*order.index(1);clear[base:base+8]=struct.pack('<4H',*wanted);clear[base+8:base+12]=bytes(pp);need(final_raw[:6]==original_raw[:6] and final_raw[136:]==original_raw[136:] and B._decrypt(final_raw[8:136],struct.unpack_from('<H',final_raw,6)[0])==bytes(clear),'all decrypted128-byte block data and100-byte party tail outside moves/PP invariant');need(r['buffer_sha256']==P.sha(buffer) and r['prefix']['final']==buffer.hex() and r['unrelated_ram_unchanged'],'unchanged actual selected buffer/frozen memory')
 calls=r['calls'];need(len(calls)==4,'four actual native move calls')
 for slot,e in enumerate(calls):need(e['entry']=='0x20714e8' and e['args'][:3]==[S.MON,wanted[slot],slot] and e['lr']=='0x2073a37' and e['return_pc']==0x2073A36 and e['sp']==e['return_sp']==S.STACK-152 and e['saved']==e['return_saved'],'four completed move setter arguments/caller ABI')
 need(r['reads']==[dict(pc='0x2073a2c',offset=98+2*i,bytes=2,value=m) for i,m in enumerate(wanted)],'four actual native record move loads');need(len(r['models'])==4,'four exact move-resource reads')
 for e,move in zip(r['models'],wanted):need(e['name']=='ReadWholeNarcMemberByIdPair' and e['args'][:3]==[S.STACK-224,11,move] and e['bytes']==16 and e['sha256']==e['output_sha256']==P.sha(moves[move]) and e['result']==B.LOADER_RESULT and e['sp']==e['return_sp'] and e['saved']==e['return_saved'],'move raw16-byte model read/return ABI')
 need(0<r['instructions']<=500000 and 152<=r['max_stack']<=512,'move instruction/stack bounds');need(r['entry'][13]==r['end'][13]==S.STACK-152 and r['end'][7]==4 and r['entry'][4:7]==r['end'][4:7] and r['entry'][8:12]==r['end'][8:12],'move native caller SP/live regs/loop counter');need({START,0x2073A2C,0x2073A32,0x20714E8,0x20714F0,0x207333C}<=set(int(e['ram'],16) for e in r['code']) and STOP not in {int(e['ram'],16) for e in r['code']},'move native caller/veneer/body/resource instruction coverage');return True


def analyze(rom,language,object_path,fixture_report):
 recipe=F.attest_recipe_sources();model=P.G.S.SHARED.read_current(rom,language)
 with rom.open('rb') as file,mmap.mmap(file.fileno(),0,access=mmap.ACCESS_READ) as raw:
  proof=M.attest_strategy_object(model,raw,object_path);code=S.qualify(model,proof);data=S.resources(raw,model);fixture,fixture_receipt=load_fixture(fixture_report,model,raw);moves,receipt=P.RAW.raw_archive(raw,'a/0/1/1');positives=[run_case(model,raw,language,code,data,fixture,plus) for plus in (0,1)]
  for r in positives:require_case(r,data,moves,fixture)
  guards=[run_case(model,raw,language,code,data,fixture,poison=True)]+[run_case(model,raw,language,code,data,fixture,plus,pp_up=True) for plus in (0,1)]
  for r in guards:require_case(r,data,moves,fixture)
  need(guards[0]['after']==positives[1]['after'],'SDK volatile poison exact output neutrality');counters=[]
  for variant in VARIANTS[1:]:
   r=run_case(model,raw,language,code,data,fixture,variant=variant,preapplied=bytes.fromhex(positives[1]['after']))
   if variant=='preapplied_skip':need(r['after']==positives[1]['after'] and len(r['calls'])==3,'same-output missing call counter premise')
   try:require_case(dict(r,variant='current',shadows=[]),data,moves,fixture)
   except ValueError as e:r['rejection']=str(e)
   else:raise ValueError('move counter accepted')
   counters.append(r)
  used=sorted(set(m for r in positives for m in r['decoded_after']['moves']));members={str(i):dict(bytes=len(moves[i]),sha256=P.sha(moves[i]),rom_offset=hex(receipt['member_rom_offsets'][i]),pp=moves[i][6]) for i in used};view=P.G.S.SHARED.gifts_audit.Arm9View(raw);locations=[]
  for a,n in ((START,STOP-START),(0x20714E8,76),(0x207332C,64)):
   blob=view.read(a,n);need(blob==C.bench_bytes(model,a,n),'move raw independent ARM9 readback');locations.append(dict(ram=hex(a),bytes=n,rom_offset=hex(view.offset(a,n)),sha256=P.sha(blob)))
 return dict(schema='strategy-native-moves-v1',language=language,input=model['record'],recipe_sources=recipe,strategy_elf=proof,fixture=fixture_receipt,locations=locations,move_members=members,positives=positives,guards=guards,counters=counters,source_sha256={str(p.relative_to(P.SOURCE)):P.sha(p.read_bytes()) for p in (Path(__file__),Path(S.__file__),Path(M.__file__))},conclusions=dict(native_four_move_consumption_observed=True,constructed_scyther=False,complete_constructor_executed=False,natural_activation_observed=False),limits=['The copied Mon fixture has species22; this verifies native setters,not construction of trainer21 Scyther','P33 six hooks share the actual buffer; a documented host boundary initializes the post-CreateMon/held-item Mon and native current-record pointer','Only four exact raw16-byte member copies are modeled; no SDK FS execution or heap services are exercised','Stops02073A42 before capsule/form/postform/PartyAdd; no battle/SAVE/hardware claim'])


def main():
 import argparse
 p=argparse.ArgumentParser(description=__doc__)
 for k in ('rom','strategy-object','fixture-report','json'):p.add_argument('--'+k,type=Path,required=True)
 p.add_argument('--language',choices=('EN','IT'),required=True);a=p.parse_args()
 try:
  need(not a.json.exists() and not a.json.is_symlink(),'output must be fresh');need(P.SOURCE not in a.json.resolve().parents and a.json.resolve()!=P.SOURCE,'output must be outside source');need(a.strategy_object.resolve().parent not in a.json.resolve().parents,'output must be outside retained objects');need(all(x.is_file() for x in (a.rom,a.strategy_object,a.fixture_report)),'move inputs must exist');r=analyze(a.rom,a.language,a.strategy_object,a.fixture_report);payload=(json.dumps(r,separators=(',',':'))+'\n').encode();need(len(payload)<=16*1024*1024,'move output budget');a.json.parent.mkdir(parents=True,exist_ok=True)
  with a.json.open('xb') as file:
   if a.json.suffix=='.gz':
    with gzip.GzipFile(fileobj=file,mode='wb',filename='',mtime=0) as out:out.write(payload)
   else:file.write(payload)
 except ValueError as e:p.exit(2,str(e)+'\n')
 print(a.language,'native four-move/PP loop verified with copied Mon fixture; full trainer construction remains outside scope')


if __name__=='__main__':main()
