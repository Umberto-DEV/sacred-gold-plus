#!/usr/bin/env python3
"""Compose qualified FindPath into the complete initialized caller.

The BSS root is a one-time declared input. Find's Send4 remains an ID8 model;
native filesystem completion and natural boot are outside this composition.
"""
from pathlib import Path
import ast,copy,gc,gzip,importlib.util,json,mmap,struct,types


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


N=load('find_caller_isolated_parent',Path(__file__).with_name('attribuisci_fs_find.py'))
C=N.H
A=load('find_caller_ownership',Path(__file__).parents[1]/'test/fs_find_caller_bench.py')
F=N.B
P,B,T,R,need,sha=C.P,C.B,C.T,C.R,C.need,C.sha
TOP,DIR,FRAME,GUARD,FILE,ID,ARC=C.TOP,C.DIR,A.FRAME,A.GUARD,C.FILE,C.ID,C.ARC
PINS=dict(narc_reader='f21c05e1c12c8d7b77a5a18796c1a1da081ab5e3a0ae90b9856e5b2a8e29d42d',
    pp_caller='7294d729b42b81ebc9dd180d485ff8ad5c170d94191d8d483d9d6d1e2dad999f',
    message_caller='f326503b432d74296c4983ae52dfe50a3a9298df2ce21acf4697a783c3a50632',
    convert_caller='cda419aee381e5647a07868cf6ec34688d4dab2eddd824b463e00600215df829',
    open_caller='b8cdc185cb618790d2eb40a7a5ed7f455aeb7064a50729b07ad47ba3b9630e64',
    read_caller='0ec5cd58a22098274f4c1661f363c88f48864d10ef0e5bcb33a9fe155c92c11f')
need(sha(Path(N.__file__).read_bytes())=='639969848e10612d2edbb85703024ff880d74d43093d34c733ba66fb02ed1942',
     'Find caller qualified isolated CLI drift')
SDK={pc:name for pc,name in C.SDK.items()if pc!=F.ENTRY}
RECIPES=[];BINDINGS=[]
from unicorn.arm_const import UC_ARM_REG_PC


def derive(module,function,edits,namespace,kind):
    function,receipt=types.FunctionType(C.W.B.E.rewrite.__code__,{**vars(C.W.B.E),'PINS':PINS})(
        module,function,edits,{**namespace,'__source_kind__':kind})
    RECIPES.append(receipt);return function


def clone(function,namespace):
    BINDINGS.append(dict(function=function.__qualname__,namespace=sorted(namespace),code_unchanged=True))
    return C.H.A.clone(function,namespace)


# Only Find uses the larger source-owned stack domain. Other observers retain
# their old active/lifetime checks. The unrelated restore range stays296.
find_step=derive(R,'Reader.step',C.H.A.edits(C.H.V.RECIPES[1])+[
    ('TOP-240<=sp','TOP-280<=sp',1)],dict(TOP=TOP,SDK=SDK),'narc_reader')
find_write=derive(R,'Reader.write',[
    ('TOP-136<=address','TOP-280<=address',1)],dict(TOP=TOP),'narc_reader')
pp_snapshot=derive(R,'Reader.run',C.H.A.edits(C.H.V.RECIPES[2])+[
    ('self.read_bytes(TOP-296,56)==self.before[TOP-296-0x2000000:TOP-240-0x2000000]',
     'self.read_bytes(TOP-336,56)==self.before[TOP-336-0x2000000:TOP-280-0x2000000]',1)],
    dict(TOP=TOP,DEST=C.DEST,STOP=C.STOP,COOKIES=C.H.PP.COOKIES,neighbors_before=C.H.PP.neighbors_before),'narc_reader')
finish_native=derive(C.H.PP,'Driver.finish_pp',C.H.A.edits(C.H.V.RECIPES[3])+[
    ('stack_guard_before=r.before[TOP-296-0x2000000:TOP-240-0x2000000].hex()',
     'stack_guard_before=r.before[TOP-336-0x2000000:TOP-280-0x2000000].hex()',1),
    ('stack_guard_after=self.read_bytes(TOP-296,56).hex()','stack_guard_after=self.read_bytes(TOP-336,56).hex()',1),
    ('stack_guard_range=[TOP-296,TOP-240]','stack_guard_range=[TOP-336,TOP-280]',1),
    ('self.pp_result.update(stack240_before=',
     'self.pp_result.update(stack280_before=r.before[FRAME-0x2000000:TOP-0x2000000].hex(),stack280_after=self.read_bytes(FRAME,280).hex(),legacy_stack_guard_before=r.before[TOP-296-0x2000000:TOP-240-0x2000000].hex(),legacy_stack_guard_after=self.read_bytes(TOP-296,56).hex(),legacy_stack_guard_range=[TOP-296,TOP-240],local_restore_range=[TOP-296,TOP],stack240_before=',1)],
    dict(TOP=TOP,FRAME=FRAME,pp_snapshot=pp_snapshot),'pp_caller')


def source_identities():
    result=N.source_identities()
    for path in(__file__,A.__file__):result[str(Path(path).resolve().relative_to(P.SOURCE))]=sha(Path(path).read_bytes())
    return result


class Driver(C.Driver):
    latest=None
    def __init__(self,*args,native_find=True,send4_value=1,**kwargs):
        need(type(native_find)is bool and type(send4_value)is int and send4_value in(1,2)and
             (native_find or send4_value==1),'Find caller finite native/baseline and separate Send4 policy')
        super().__init__(*args,**kwargs)
        self.native_find,self.send4_value=native_find,send4_value
        self.root_input=None;self.root_fences=[];self.find_result=None
        Driver.latest=self

    def prepare(self,cpu):
        super().prepare(cpu)
        need(cpu is self.u and self.root_input is None and not self.api_calls,'Root input initialized once before every API')
        before=self.read_bytes(0x2000000,0x400000);regs=self.regs()
        need(self.read_bytes(A.CURRENT,12)==bytes(12),'Verified zero BSS preimage before declared root input')
        cpu.mem_write(A.CURRENT,A.ROOT)
        self.root_input=A.require_root_input(before,self.read_bytes(0x2000000,0x400000),regs,self.regs())

    def factory(self,*args):
        cpu=super().factory(*args);parent=cpu.emu_start
        def run(begin,end,*args,**kwargs):
            need(self.root_input is not None and len(self.root_fences)<3 and self.read_bytes(A.CURRENT,12)==A.ROOT,
                 'Root readonly precondition precedes original API/before capture')
            event=dict(number=len(self.root_fences),begin=hex(begin),root_before=self.read_bytes(A.CURRENT,12).hex(),
                       regs_before=self.regs(),root_after=None,regs_after=None)
            self.root_fences.append(event)
            try:return parent(begin,end,*args,**kwargs)
            finally:
                event.update(root_after=self.read_bytes(A.CURRENT,12).hex(),regs_after=self.regs())
                need(self.read_bytes(A.CURRENT,12)==A.ROOT,'Root input mutated during API; never repaired')
        cpu.emu_start=run;return cpu

    def start_pp(self):
        super().start_pp()
        if not self.native_find:return
        regs=self.regs();before=self.read_bytes(0x2000000,0x400000)
        self.find_observer=FindObserver(self,self.pp_reader);self.find_result=self.find_observer.result
        need(regs==self.regs()and before==self.read_bytes(0x2000000,0x400000),'Find observer attachment is CPU/RAM neutral')

    def finish_pp(self):
        if self.native_find:return finish_native(self)
        return super().finish_pp()


class FindObserver:
    def __init__(self,driver,reader):
        self.driver,self.reader=driver,reader;self.active=False;self.result=None;self.before=None
        self.parent_step,self.parent_write,self.parent_read,self.parent_service=reader.step,reader.write,reader.read,reader.service
        self.root_step=types.MethodType(find_step,reader);self.root_write=types.MethodType(find_write,reader)
        reader.code={**reader.code,**driver.qualified['fs_find_code']}
        reader.step,reader.write,reader.read,reader.service=self.step,self.write,self.read,self.service

    def step(self,u,pc,n,user):
        r=self.reader
        if self.active and pc==0x20D81AC:
            after=r.read_bytes(F.BASE,F.SIZE);a=C.PAGE-F.BASE;b=a+4096
            self.result.update(returned=r.regs(),frame_after=r.read_bytes(FRAME,280).hex(),
                destination_after=r.read_bytes(ID,8).hex(),page_after=after[a:b].hex(),
                after_ram_sha256=sha(after),outside_before_sha256=sha(self.before[:a]+self.before[b:]),
                outside_after_sha256=sha(after[:a]+after[b:]),outside_unchanged=self.before[:a]+self.before[b:]==after[:a]+after[b:])
            self.before=None;self.active=False
        if pc==F.ENTRY:
            need(self.result is None and self.driver.convert_observer.active and not r.open and r.file==FILE and r.initialized,
                 'Find single actual native lifetime inside Convert, outer file still unopened')
            entry=r.regs();frame=r.read_bytes(FRAME,280)
            f=dict(entry=entry,frame=frame.hex(),path='a/0/1/1',current_dir=r.read_bytes(A.CURRENT,12).hex(),file_id=140,
                destination_before=r.read_bytes(ID,8).hex(),provenance='Actual same complete caller, initialized source root fixture, not natural boot')
            F.check_fixture(f);F.require_fnt(f,self.driver.data['find_fnt'])
            self.before=r.read_bytes(F.BASE,F.SIZE);a=C.PAGE-F.BASE
            self.result=dict(fixture=f,entry=entry,returned=None,frame_before=frame.hex(),frame_after=None,
                destination_after=None,flow=[],stores=[],reads=[],services=[],native_peak=0,
                page_before=self.before[a:a+4096].hex(),page_after=None,before_ram_sha256=sha(self.before),
                model_index=len(r.models),policy=dict(send=self.driver.send4_value,clobber=r.clobber))
            self.driver.find_result=self.result;self.active=True
        if self.active:
            self.result['native_peak']=max(self.result['native_peak'],DIR-r.regs()[13])
            if pc in self.driver.qualified['fs_find_code']:self.result['flow'].append(dict(pc=hex(pc),regs=r.regs()))
            self.root_step(u,pc,n,user);return
        self.parent_step(u,pc,n,user)

    def write(self,u,access,address,n,value,user):
        if not self.active:return self.parent_write(u,access,address,n,value,user)
        pc=u.reg_read(UC_ARM_REG_PC)
        need(F.write_allowed(pc,address,n),'Find caller native field/saved-stack write owner')
        if self.reader.observe:self.result['stores'].append(dict(pc=hex(pc),address=address,bytes=n,
            before=self.reader.read_bytes(address,n).hex(),value=value))
        self.root_write(u,access,address,n,value,user)

    def read(self,u,access,address,n,value,user):
        if not self.active:return self.parent_read(u,access,address,n,value,user)
        pc=u.reg_read(UC_ARM_REG_PC);need(F.read_allowed(pc,address,n),'Find caller native readonly field/pool/root/saved-stack owner')
        self.result['reads'].append(dict(pc=hex(pc),address=address,bytes=n,hex=self.reader.read_bytes(address,n).hex()))

    def service(self,pc):
        if pc!=F.SEND or not self.active:return self.parent_service(pc)
        from ndspy.fnt import load as load_fnt
        r,u=self.reader,self.reader.u;entry=r.regs();frame_before=r.read_bytes(FRAME,280).hex()
        need(entry[:2]==[DIR,4]and entry[13:15]==[FRAME,0x20D80F8]and not entry[15]&32,
             'Find caller native Send4 exact file/command/SP/LR/ISA')
        need(r.read_bytes(DIR+48,12)==A.ROOT and r.read_bytes(DIR+8,4)==struct.pack('<I',ARC),
             'Find caller native ARG root and opaque archive token')
        path,directory,dst=struct.unpack('<3I',r.read_bytes(DIR+60,12))
        need((path,directory,dst)==(F.PATH,0,ID)and r.read_bytes(path,8)==b'a/0/1/1\0',
             'Find caller actual ARG path/mode/result ownership')
        file_id=load_fnt(self.driver.data['find_fnt']).idOf(r.read_bytes(path,7).decode('ascii'))
        need(file_id==140,'Find caller independent raw-FNT actual path resolution')
        blob=struct.pack('<2I',ARC,file_id);u.mem_write(dst,blob);r.path='a/0/1/1'
        returned=F.B.boundary_regs(entry,self.driver.send4_value,r.clobber)
        for reg,value in zip(F.REGS,returned):u.reg_write(reg,value)
        event=dict(pc=hex(pc),entry=entry,returned=r.regs(),frame_before=frame_before,frame_after=r.read_bytes(FRAME,280).hex(),
            result=self.driver.send4_value,command=4,destination=dst,delivered_hex=blob.hex(),
            model_scope='ID8 only; no native command/error/queue/completion effects')
        self.result['services'].append(event)
        r.models.append(dict(event,name=SDK[F.SEND],args=entry[:4],sp=entry[13],lr=hex(entry[14]),saved=entry[4:12],
            result_r0=self.driver.send4_value,return_sp=returned[13],return_saved=returned[4:12],
            return_volatile=[returned[i]for i in(1,2,3,12)],path=r.path,opaque_archive_token=ARC,file_id=file_id,
            fnt_sha256=sha(self.driver.data['find_fnt']),cursor_before=r.cursor,cursor_after=r.cursor,
            open_before=r.open,open_after=r.open))
        u.reg_write(UC_ARM_REG_PC,entry[14])


run_case=derive(C.H.PP.V,'run_case',C.H.A.edits(C.RECIPES[1])+[
    ('retain_full_read_witness=False):','retain_full_read_witness=False,native_find=True,send4_value=1):',1),
    ('retain_full_read_witness=retain_full_read_witness)','retain_full_read_witness=retain_full_read_witness,native_find=native_find,send4_value=send4_value)',1),
    ('return dict(read_calls=',
     'return dict(find=driver.find_result,native_find=driver.native_find,send4_value=driver.send4_value,root_input=driver.root_input,root_fences=driver.root_fences,read_calls=',1)],
    dict(Driver=Driver,A=C.H.PP.A,TOP=TOP,NAME_ARENA=C.H.PP.X.NAME_ARENA,NAME_END=C.H.PP.X.NAME_END),'message_caller')


def qualify(model,raw,language,objects,strategy_object,read_recipe,wait_recipe,recipe_dir):
    from capstone import Cs,CS_ARCH_ARM,CS_MODE_ARM
    q,proof=C.qualify(model,raw,language,objects,strategy_object,read_recipe,wait_recipe)
    view=P.G.S.SHARED.gifts_audit.Arm9View(raw);body=view.read(F.ENTRY,324)
    need(body==P.G.piece(model['segments'],F.ENTRY,324)==N.L.object_text(recipe_dir/'fs-find-path.o',324,N.L.C.BODIES['path'][2]),
         'Find caller independent physical/decoded/recovered ELF body')
    receipt=json.loads((recipe_dir/'manifesto.json').read_bytes())
    need(receipt['builder_sha256']==sha(Path(N.L.C.__file__).read_bytes())and
         receipt['recipe_sha256']==sha((Path(__file__).parents[1]/'sorgenti/fs-find.S').read_bytes())and
         receipt['source_recipe']==N.L.C.RECIPE and receipt['objects']['path']['object_sha256']==sha((recipe_dir/'fs-find-path.o').read_bytes())and
         receipt['reference']['pin']==N.L.C.D.C.PIN and receipt['reference']['layout_passed']is True and
         receipt['recipe_is_recovered']is True and receipt['original_compiler_reconstructed']is False,
         'Find caller retained original-header/compiler/recipe receipt')
    arm9=struct.unpack_from('<I',raw,0x20)[0];params=struct.unpack_from('<9I',raw,arm9+0xBA0)
    need(struct.unpack_from('<I',body,320)[0]==A.CURRENT and params[3]<=A.CURRENT and A.CURRENT+12<=params[4]and not view.has(A.CURRENT,12),
         'Find caller root is BSS; no initialized ROM mapping')
    code=list(Cs(CS_ARCH_ARM,CS_MODE_ARM).disasm(body[:320],F.ENTRY));need(len(code)==80,'Find caller ARM instruction extent')
    q['fs_find_code']={i.address:(4,False)for i in code}
    off,size=struct.unpack_from('<2I',raw,0x40);need(0<size<=1024**2 and off+size<=len(raw),'Find caller FNT bounds')
    proof['native_find_in_caller']=dict(component=dict(ram=hex(F.ENTRY),rom_offset=hex(view.offset(F.ENTRY,324)),bytes=324,
        instruction_bytes=320,sha256=sha(body),object_sha256=sha((recipe_dir/'fs-find-path.o').read_bytes())),
        recipe_receipt_sha256=sha((recipe_dir/'manifesto.json').read_bytes()),recipe_receipt=receipt,
        global_input=dict(address=hex(A.CURRENT),bytes=12,kind='BSS',static_start=hex(params[3]),static_end=hex(params[4]),
            initialized_ROM_mapping=False,source_derived_root_fixture=True,boot_observed=False),
        FNT=dict(rom_offset=hex(off),bytes=size,sha256=sha(raw[off:off+size])),
        forecasts=dict(hooks=779,executed_PCs=308,native_stores=186,binary_Find_starts=80,executed_Find_starts=42),
        ownership=A.coverage(),SDK_models=dict(Send=10),model_scope='Send4 ID8; Send0 payload/position/completion12; no native queue/card/archive completion')
    return q,proof


def resources(model,raw,language):
    data=C.H.resources(model,raw,language);off,size=struct.unpack_from('<2I',raw,0x40)
    data['find_fnt']=bytes(raw[off:off+size]);return data


# Replace the old Find model transition with source-derived native semantics;
# retain the original Convert instruction loop and aggregate/saved ABI rules.
_old_find="""if r['pp_clobber']:
                for i in(1,2,3,12):regs[i]=0xA5000000+i
                regs[15]=0xA000001F
            regs[0]=r['find_value'];find=dict(pc=hex(FIND),entry=before,returned=list(regs))"""
expected_convert=derive(C.H.V,'expected_convert',[
    (_old_find,"need(before==r['find']['fixture']['entry'],'Find caller actual entry follows source Convert BL');native=F.predict(r['find']['fixture'],r['send4_value'],r['pp_clobber']);regs[:]=native['returned'];find=native['services'][0]",1)],dict(F=F),'convert_caller')
expected_open=clone(C.H.F.predict_open,dict(expected_convert=expected_convert))


def require_find(r,data,source_frame=None):
    out=r['find'];C.require_register_vectors(out)
    need(type(r['send4_value'])is int and r['send4_value']in(1,2)and N.wire(out['policy'])==N.wire(dict(send=r['send4_value'],clobber=r['pp_clobber'])),
         'Find caller finite separate Send4 policy')
    f=out['fixture'];F.check_fixture(f);F.require_fnt(f,data['find_fnt'])
    if source_frame is not None:need(f['frame']==source_frame.hex(),'Find contextual preimage independently reconstructed from chronological Init/Convert stores')
    want=F.predict(f,r['send4_value'],r['pp_clobber'])
    need(out['entry']==f['entry']and out['frame_before']==f['frame']and type(out['model_index'])is int and out['model_index']==0,'Find exact single actual entry/frame/model occurrence')
    for key in('returned','frame_after','destination_after','flow','reads','services','native_peak'):
        need(N.wire(out[key])==N.wire(want[key]),'Find caller source '+key)
    need(N.wire(out['stores'])==N.wire(want['stores']if r['observe']else[]),'Find caller seventeen ordered native stores or OFF transcript')
    before,after=bytes.fromhex(out['page_before']),bytes.fromhex(out['page_after']);i=FRAME-C.PAGE
    need(len(before)==len(after)==4096 and before[i:i+280].hex()==f['frame'],'Find page binds actual280 preimage')
    expected=bytearray(before);expected[i:i+280]=bytes.fromhex(want['frame_after'])
    need(after==bytes(expected),'Find source-owned page delta280 with other bytes preserved')
    need(out['outside_unchanged']is True and out['outside_before_sha256']==out['outside_after_sha256']and
         len(out['outside_before_sha256'])==64,'Find actual outside-page comparison and matching digest')
    model=r['pp_reader']['models'][0];service=want['services'][0]
    entry,returned=service['entry'],service['returned']
    expected_model=dict(service,name=SDK[F.SEND],args=entry[:4],sp=FRAME,lr='0x20d80f8',saved=entry[4:12],
        result_r0=r['send4_value'],return_sp=FRAME,return_saved=entry[4:12],
        return_volatile=[returned[i]for i in(1,2,3,12)],path='a/0/1/1',opaque_archive_token=ARC,file_id=140,
        fnt_sha256=sha(data['find_fnt']),cursor_before=None,cursor_after=None,open_before=False,open_after=False)
    need(N.wire(model)==N.wire(expected_model),'Find caller sole Send4 exact native ABI/raw-FNT/ID8/lifetime')
    return want


require_readonly_guard=derive(C.H.V,'require_readonly_guard',[
    ('[TOP-296,DIR]','[TOP-336,FRAME]',1),
    ("p['stack_guard_before'][:16]==p['stack_guard_after'][:16]","p['stack_guard_before'][80:96]==p['stack_guard_after'][80:96]",1)],dict(FRAME=FRAME),'convert_caller')


PINS.update(fs_init_caller='691b7c423019b92cda65259e124829a92579b181582056b946312f3904feeef8',
    fs_fast_caller='638ffa44edd4f5226a55001466439de15cce441019b2bad02d5e188942cb8bc0',
    fs_seek_caller=C.SEEK_PIN)
require_init=derive(C.H.I,'require_init',C.H.A.edits(C.H.CONTEXT_RECIPES[0])+[
    ("p['models'][0]['name'] == 'FSi_FindPath'","p['models'][0]['name'] == 'FSi_SendCommand'",1),
    ("p['models'][0]['args'][2] == ID","p['models'][0]['args'][2] == 0",1)],dict(ID=ID),'fs_init_caller')
require_open=derive(C.H.O,'require_open',C.H.A.edits(C.H.CONTEXT_RECIPES[1])+[
    ('[TOP - 296, DIR]','[TOP - 336, FRAME]',1),
    ("['FSi_FindPath', 'FSi_SendCommand']","['FSi_SendCommand', 'FSi_SendCommand']",1),
    ("models[0]['before_hex'] == before[:8].hex()","models[0]['frame_before'][2*(ID-FRAME):2*(ID-FRAME+8)] == before[:8].hex()",1),
    ("models[0]['delivered_sha256'] == sha(blob)","sha(bytes.fromhex(models[0]['delivered_hex'])) == sha(blob)",1)],
    dict(require_init_native=require_init,expected_open=expected_open,FRAME=FRAME,open_after=C.H.projected_open_after),'open_caller')
require_convert=derive(C.H.V,'require_convert',[
    ("after=bytearray(init_after);after[88:96]=struct.pack('<II',ARC,140)",
     "source_frame=bytes.fromhex(p['stack280_before'])[:40]+bytes(init_after);native=require_find(r,data,source_frame);after=bytearray.fromhex(native['frame_after'])[40:]",1),
    ("first['name']=='FSi_FindPath'","first['name']=='FSi_SendCommand'",1),
    ("first['dir_before_hex']==directory.hex()","bytes.fromhex(first['frame_before'])[DIR-FRAME:DIR-FRAME+72].hex()==native['services'][0]['frame_before'][2*(DIR-FRAME):2*(DIR-FRAME+72)]",1)],
    dict(expected_convert=expected_convert,require_open=require_open,require_find=require_find,FRAME=FRAME,require_readonly_guard=require_readonly_guard),'convert_caller')
require_fast=clone(C.H.require_fast,dict(require_convert=require_convert))


def native_prefix(r):
    old=C.native_prefix();native=F.predict(r['find']['fixture'],r['send4_value'],r['pp_clobber'])
    stores=[{k:v for k,v in e.items()if k!='before'}for e in native['stores']]
    result=old[:36]+stores+old[36:];need(len(result)==63,'Find caller chronological native prefix63');return result


require_timeline=derive(C,'require_timeline',[
    ('writes=native_prefix()','writes=native_prefix(r)',1),('len(writes)==169','len(writes)==186',1)],
    dict(H=types.SimpleNamespace(**{**vars(C.H),'require_fast':require_fast}),native_prefix=native_prefix),'read_caller')
require_native=derive(R,'require_case',C.H.A.edits(C.RECIPES[-1])+[
    ("r['max_stack']==240","r['max_stack']==280",1)],
    {**C.require_native.__globals__,'EXPECTED_HOOKS':779,'EXPECTED_PC_COUNT':308},'narc_reader')


def complete_code(q,r):
    executed={int(e['pc'],16)for e in F.predict(r['find']['fixture'],r['send4_value'],r['pp_clobber'])['flow']}
    need(len(executed)==42 and executed<=set(q['fs_find_code']),'Find source42 executed starts, not full80 binary coverage')
    return{**C.complete_code(q),**{pc:q['fs_find_code'][pc]for pc in executed}}


def require_root(r):
    root=r['root_input'];need(root['address']==A.CURRENT and root['bytes']==12 and root['before']==bytes(12).hex()and
        root['after']==A.ROOT.hex()and root['changed_bytes']==4 and root['initialized_once']is True and F.B.u32s(root['registers']),
        'Find caller one-time declared BSS root input identity')
    fences=r['root_fences'];need(len(fences)==len(r['api_calls'])==3,'Find caller all three root fences')
    for index,(event,api)in enumerate(zip(fences,r['api_calls'])):
        need(F.B.u32s(event['regs_before']),'Find root pre-fence actual unsigned32 registers')
        entry=list(event['regs_before'])
        if index==1:entry[4:12]=C.H.PP.N.COOKIES
        need(entry==api['entry'],'Find root pre-fence bound to actual API entry, only source wrapper cookies at API1')
        need(type(event['number'])is int and event['number']==index and event['begin']==api['begin']and event['root_before']==event['root_after']==A.ROOT.hex()and
             event['regs_after']==api['end']and F.B.u32s(event['regs_before']),'Find caller readonly root at every actual API return')
    return True


def require_case(r,data,q,allow_error=False,allow_find2=False):
    C.require_register_vectors(r)
    need(r['native_find']is True and type(r['send4_value'])is int and r['send4_value']==(2 if allow_find2 else 1)and
         r['variant']==('first_error1'if allow_error else'current')and r['pp_shadows']==[],
         'Find caller positive/counter finite policy without shadows')
    require_root(r);require_find(r,data);require_timeline(r,data,q);C.H.PP.require_pp_context(r,data)
    p=r['pp_reader'];want=F.predict(r['find']['fixture'],r['send4_value'],r['pp_clobber'])
    need(p['stack280_before'][80:]==p['stack240_before']and p['stack280_after'][80:]==p['stack240_after']and
         p['stack280_after'][:80]==want['frame_after'][:80]and p['local_restore_range']==[TOP-296,TOP]and
         p['legacy_stack_guard_range']==[TOP-296,TOP-240]and
         p['legacy_stack_guard_before'][:32]==p['legacy_stack_guard_after'][:32]and
         p['legacy_stack_guard_before'][32:]==p['stack280_before'][:80]and
         p['legacy_stack_guard_after'][32:]==p['stack280_after'][:80],
         'Find lower40 source frame persists; legacy guard16 readonly/40 now stack; local296 unchanged')
    native=C.H.A.clone(require_native,dict(CLOSE_VALUE=r['close_value']))
    native(p,data['pp_reader'],complete_code(q,r),T.expected(data['constructor'],r['plus'])[0]['ot_draws'][-1])
    replay=dict(r,variant='current')if allow_error else r
    C.H.PP.require_earlier(replay,data,q);return True


def require_off_pair(on,off,data,q):
    require_root(off)
    parent=C.H.A.clone(C.require_off_pair,dict(require_case=require_case,require_timeline=require_timeline,
        require_native=require_native,complete_code=lambda q:complete_code(q,off)))(on,off,data,q)
    a,b=copy.deepcopy(on['find']),copy.deepcopy(off['find'])
    need(b['stores']==[],'Find OFF native store transcript absent');a.pop('stores');b.pop('stores')
    for obj in(a,b):
        for key in('before_ram_sha256','after_ram_sha256','outside_before_sha256','outside_after_sha256'):obj.pop(key)
    need(a==b and on['send4_value']==off['send4_value']==1 and on['native_find']is off['native_find']is True,
         'Find OFF actual ABI/source/page/frame/services unchanged without new masks')
    return dict(neutral=True,parent=parent,ownership=A.coverage(),scope='Existing608/1124 projections unchanged; actual Find280/page4096/readonly root/guard56')


counter_record=clone(C.counter_record,dict(require_case=require_case))
require_counter=clone(C.require_counter,dict(require_case=require_case,counter_record=counter_record))


def find2_counter(r,normal,data,q):
    require_case(r,data,q,allow_find2=True);require_case(normal,data,q)
    need(r['plus']==normal['plus']==1 and r['seed']==normal['seed']==0x12345678 and r['observe']is True and
         r['pp_clobber']is False and r['poison']==normal['poison']==0xC7 and r['read_send_value']==r['close_value']==1,
         'Find2 finite isolated Send4 return policy')
    need(r['find']['returned'][0]==2 and normal['find']['returned'][0]==1 and
         r['find']['frame_after']==normal['find']['frame_after']and r['convert']['returned']==normal['convert']['returned']and
         r['convert']['flow'][13:]==normal['convert']['flow'][13:]and
         all(r[k]==normal[k]for k in('mon_hex','prefix','seed_after','pp_flow','pp_stores','pp_checkpoint',
             'fs_fast','seek','read_calls','fs_close','raw_ram_sha256','functional_ram_sha256')),
         'Find2 actual unnormalized native return then Convert1; later source path and final outputs/RAM equal')
    disguised=copy.deepcopy(r);disguised['send4_value']=1;disguised['find']['policy']['send']=1
    try:require_case(disguised,data,q)
    except ValueError as error:return dict(result=r,policy_disguised=True,rejection=str(error))
    raise ValueError('Find2 native return accepted as positive after policy disguise')


def require_baseline(candidate,baseline,data,q,first,second):
    require_case(candidate,data,q);C.require_case(baseline,data,q);require_root(baseline)
    need(baseline['native_find']is False and baseline['find']is None and candidate['plus']==baseline['plus']==1 and
         candidate['seed']==baseline['seed']==0x12345678 and candidate['poison']==baseline['poison']==0xC7 and
         candidate['root_input']==baseline['root_input'],'Find matched P64 model/root-input baseline domain')
    need(type(first)is type(second)is bytes and len(first)==len(second)==0x400000 and
         sha(first)==baseline['raw_ram_sha256']and sha(second)==candidate['raw_ram_sha256'],
         'Find independently retained exact whole final4MiB pair bound to actual caller hashes')
    spans=[];start=None
    for i,(a,b)in enumerate(zip(first,second)):
        if a!=b and start is None:start=i
        if a==b and start is not None:spans.append([F.BASE+start,F.BASE+i]);start=None
    if start is not None:spans.append([F.BASE+start,F.BASE+len(first)])
    need(all(candidate[k]==baseline[k]for k in('mon_hex','prefix','seed_after','pp_flow','pp_stores','pp_checkpoint')),
         'Find native/model same final party/Trainer/RNG and actual PP consumer')
    for key in('fs_fast','fs_close'):
        need(all(candidate[key][k]==baseline[key][k]for k in('entry','returned','flow')),
             'Find native/model Fast and Close exact architectural contexts, frames compared separately')
    for a,b in zip(candidate['seek']+candidate['read_calls'],baseline['seek']+baseline['read_calls']):
        need(all(a[k]==b[k]for k in('entry','returned','flow','cursor_before','cursor_after')),
             'Find native/model later Seek/Read actual architectural contexts and cursor')
    need(candidate['instructions']==baseline['instructions']+47,'Find same whole caller plus47 native hooks')
    return dict(whole_final_ram_equal=first==second,changed_ranges=spans,changed_bytes=sum(a!=b for a,b in zip(first,second)),
        baseline_sha256=sha(first),candidate_sha256=sha(second),added_hooks=47,root_input_same=True)


def analyze(rom,language,objects,strategy_object,read_recipe,wait_recipe,recipe_dir,raw_dir=None,readback_only=False,probe=False):
    import unicorn
    need(not(readback_only and probe),'Find readback-only and probe are mutually exclusive')
    R.W.require_host_budget();sources=source_identities();model=P.G.S.SHARED.read_current(rom,language)
    if not readback_only:
        need(raw_dir is not None and not raw_dir.exists()and P.SOURCE not in raw_dir.resolve().parents,'Find fresh private raw directory required before CPU')
        raw_dir.mkdir(parents=True)
    with rom.open('rb')as fd,mmap.mmap(fd.fileno(),0,access=mmap.ACCESS_READ)as raw:
        q,proof=qualify(model,raw,language,objects,strategy_object,read_recipe,wait_recipe,recipe_dir)
        result=dict(schema='trainer31-native-fs-find-caller-v1',language=language,input=model['record'],source_sha256=sources,
            proof=proof,recipes=RECIPES,namespace_bindings=BINDINGS,cpu_executed=False,compiler_invoked=False,
            conditional_policy=dict(unicorn_version=unicorn.__version__,cpu_model=17,cpu_name='Cortex-A15',
                native_instruction_semantics=True,ARM946_silicon_or_timing=False,Find_hooks=47,all_reader_hooks=779))
        if not readback_only:
            data=resources(model,raw,language);serial=0;finals={}
            def run(label,plus=1,seed=0x12345678,retain_final=False,**kwargs):
                nonlocal serial
                serial+=1;path=raw_dir/('%02d-%s.json.gz'%(serial,label))
                try:observed=run_case(model,raw,language,q,data,plus,seed,**kwargs)
                except Exception as error:
                    d=Driver.latest
                    C.write_private(path,dict(label=label,completed=False,error_type=type(error).__name__,error=str(error),
                        stage=getattr(d,'stage',None),regs=d.regs()if d is not None else None,find=getattr(d,'find_result',None),
                        read_calls=getattr(d,'read_result',None),root_input=getattr(d,'root_input',None),root_fences=getattr(d,'root_fences',None)))
                    raise
                C.write_private(path,dict(label=label,completed=True,result=observed))
                if retain_final:
                    blob=Driver.latest.read_bytes(F.BASE,F.SIZE);need(sha(blob)==observed['raw_ram_sha256'],'Find retained actual final RAM hash')
                    with(raw_dir/(label+'-final.bin.gz')).open('xb')as out:out.write(gzip.compress(blob,mtime=0))
                    finals[label]=blob
                print(language,label,'raw saved before oracle',flush=True);return observed
            positives=[];off=[];guards=[];controls=[];counters=[]
            grid=[(1,0x12345678)]if probe else[(p,s)for p in(0,1)for s in(0x12345678,0x12345679)]
            for plus,seed in grid:
                label='positive-%d-%08x'%(plus,seed)
                observed=run(label,plus,seed,retain_final=(plus==1 and seed==0x12345678))
                require_case(observed,data,q);positives.append(observed)
                print(language,'native Find caller verified',plus,hex(seed),flush=True)
            normal=next(r for r in positives if r['plus']==1 and r['seed']==0x12345678)
            baseline=run('matched-model',native_find=False,retain_final=True)
            paired=require_baseline(normal,baseline,data,q,finals['matched-model'],finals['positive-1-12345678'])
            del finals;gc.collect()
            if not probe:
                for plus in(0,1):
                    observed=run('off-'+str(plus),plus,observe=False)
                    base=next(r for r in positives if r['plus']==plus and r['seed']==0x12345678)
                    off.append(dict(result=observed,proof=require_off_pair(base,observed,data,q)))
                observed=run('fill39',poison=0x39);require_case(observed,data,q)
                need(observed['mon_hex']==normal['mon_hex'],'Find alternate preimage preserves party');guards.append(observed)
                for label,kwargs in(('clobber',dict(pp_clobber=True)),('close2',dict(close_value=2)),('read-send0',dict(read_send_value=0))):
                    observed=run(label,**kwargs);require_case(observed,data,q)
                    need(all(observed[k]==normal[k]for k in('mon_hex','prefix','seed_after','functional_ram_sha256','raw_ram_sha256')),
                         'Find lower boundary control preserves party/seed/final RAM');controls.append(observed)
                observed=run('first-error1',variant='first_error1');counter=counter_record(observed,data,q)
                require_counter(counter,normal,data,q);counters.append(counter)
                observed=run('find2',send4_value=2);counters.append(find2_counter(observed,normal,data,q))
            result.update(cpu_executed=True,probe_only=probe,positives=positives,observer_off=off,guards=guards,
                volatile_controls=controls,counters=counters,matched_baseline=dict(result=baseline,proof=paired),
                limits=['Initialized trainer31/PP310 caller with one-time declared BSS root12, not natural boot/full-battle/SAVE/hardware',
                    'Ten remaining SDK boundaries are Send4,6,0x7,8; Send4 is ID8-only raw-FNT model',
                    'Send0 payload/position/completion12 only; native command/queue/archive/card/thread completion excluded',
                    'Find47 hooks42 starts/80 binary ARM starts; frame280/global600 within608, local296/OFF1124 unchanged',
                    'Recovered exact ARM recipes; original native compiler/objects unavailable',
                    'Unicorn2.1.4 CPU17 Cortex-A15 instruction semantics; no ARM946 silicon/timing claim'])
        need(source_identities()==sources,'Find caller sources changed during execution');R.W.require_host_budget()
    return result


def main():
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    for name in('rom','objects','strategy-object','read-recipe','wait-recipe','recipe-dir','json'):parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--language',choices=('EN','IT'),required=True);parser.add_argument('--raw-dir',type=Path)
    mode=parser.add_mutually_exclusive_group();mode.add_argument('--readback-only',action='store_true');mode.add_argument('--probe',action='store_true')
    args=parser.parse_args()
    try:
        need(not args.json.exists()and not args.json.is_symlink()and P.SOURCE not in args.json.resolve().parents,'Find fresh private report outside source required')
        result=analyze(args.rom,args.language,args.objects,args.strategy_object,args.read_recipe,args.wait_recipe,args.recipe_dir,
            args.raw_dir,args.readback_only,args.probe);C.write_private(args.json,result)
    except ValueError as error:parser.exit(2,str(error)+'\n')
    print(args.language,'Find caller readback verified'if args.readback_only else'Find caller verified; scope recorded')


if __name__=='__main__':main()
