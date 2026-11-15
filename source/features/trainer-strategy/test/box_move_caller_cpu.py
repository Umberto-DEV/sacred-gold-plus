"""One uninterrupted complete caller CPU run, fixed local limit32768.

The qualified producer body differs only in two instruction-cap constants.
Mapping and register initialization precede its sole emu_start; no runtime
host writes, phase reset or callee model is introduced.
"""
from pathlib import Path
import ast
import hashlib
import importlib.util
import inspect
import types


def load(path,name):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


P=load(Path(__file__).with_name('fs_memory_narc_bench.py'),'caller_pinned_native_producer')
need=P.need
PARENT_SHA='87b92017d37bcda4e92deebb12db35bb4d9d448c4aac72911cce49de3b7b2531'
CAP=32768


def audit_source_delta():
    old=ast.parse(inspect.getsource(P.run));new=ast.parse(inspect.getsource(_run_cpu))
    old.body[0].name=new.body[0].name='normalized_run';changes=0
    class Delta(ast.NodeTransformer):
        def visit_Constant(self,node):
            nonlocal changes
            if type(node.value)is int and node.value==8192:changes+=1;return ast.copy_location(ast.Constant(32768),node)
            return node
    old=Delta().visit(old)
    need(changes==2 and ast.dump(old,include_attributes=False)==ast.dump(new,include_attributes=False),'exact caller two-node producer delta')
    return changes


def source_identity_guard():
    need(hashlib.sha256(Path(P.__file__).read_bytes()).hexdigest()==PARENT_SHA,'pinned caller native producer drift')
    audit_source_delta()


def require_completion(raw,source_steps):
    need(type(source_steps)is int and 0<source_steps<CAP,'caller spare return-gate callback budget')
    need(raw.get('stopped')is True,'caller observed return-gate callback')
    need(type(raw.get('executed_count'))is int and type(raw.get('callback_count'))is int and
         raw['executed_count']==source_steps and raw['callback_count']==source_steps+1,'caller complete native instruction/gate counters')


def _run_cpu(f,policy,observe=True):
    import unicorn as U
    from unicorn import arm_const as C
    need(type(observe)is bool and U.__version__==BACKEND['unicorn'],'qualified observer/backend')
    uc=U.Uc(U.UC_ARCH_ARM,U.UC_MODE_ARM);uc.ctl_set_cpu_model(C.UC_CPU_ARM_CORTEX_A15)
    need(uc.ctl_get_cpu_model()==17,'actual CPU17')
    registers=tuple(getattr(C,'UC_ARM_REG_R'+str(i))for i in range(13))+(C.UC_ARM_REG_SP,C.UC_ARM_REG_LR,C.UC_ARM_REG_CPSR)
    for a,b in f['pages'].items():uc.mem_map(a,4096);uc.mem_write(a,b)
    uc.reg_write(C.UC_ARM_REG_CPSR,f['entry_regs'][15])
    for r,v in zip(registers[:15],f['entry_regs'][:15]):uc.reg_write(r,v)
    code={pc:(4,False)for a,n in CODE_SPANS for pc in range(a,a+n,4)}
    thumb=L.thumb_code({name:M.read(f['pages'],a,n)for name,(a,n,count,digest)in L.THUMB.items()})
    code.update({a:(len(b),True)for a,b in thumb.items()})
    flow=[];reads=[];stores=[];seen=set();count=0;tc=0;callbacks=0;rc=0;wc=0;low=R.TOP;stopped=False
    def state():return [uc.reg_read(r)&0xffffffff for r in registers]
    def instruction(machine,address,size,user):
        nonlocal count,tc,callbacks,low,stopped
        callbacks+=1
        if address==F.RETURN:stopped=True;machine.emu_stop();return
        isa=bool(machine.reg_read(C.UC_ARM_REG_CPSR)&32)
        need(code.get(address)==(size,isa)and(address,isa)in policy['code_starts'],'native fetch start/width/ISA outside source route')
        need(bytes(machine.mem_read(address,size))==M.read(f['pages'],address,size),'native code bytes drift')
        count+=1;tc+=int(isa);need(count<=32768,'native instruction cap');seen.add(address);low=min(low,machine.reg_read(C.UC_ARM_REG_SP))
        if observe:flow.append(dict(pc=address,regs=state()))
    def access(machine,kind,address,size,value,user):
        nonlocal rc,wc
        pc=machine.reg_read(C.UC_ARM_REG_PC)
        if kind==U.UC_MEM_WRITE:
            need((pc,address,size)in policy['write_sites'],'native write outside source site/address/width');wc+=1
            if observe:stores.append(dict(pc=pc,address=address,bytes=size,before=bytes(machine.mem_read(address,size)).hex(),value=value&((1<<(8*size))-1)))
        else:
            need((pc,address,size)in policy['read_sites'],'native read outside source site/address/width');rc+=1
            if observe:reads.append(dict(pc=pc,address=address,bytes=size,hex=bytes(machine.mem_read(address,size)).hex()))
    uc.hook_add(U.UC_HOOK_CODE,instruction);uc.hook_add(U.UC_HOOK_MEM_READ|U.UC_HOOK_MEM_WRITE,access)
    fault=None
    try:uc.emu_start(F.ENTRY|1,0,timeout=1000000,count=32768)
    except(ValueError,U.UcError)as e:fault=type(e).__name__+': '+str(e)
    pages={a:bytes(uc.mem_read(a,4096))for a in f['pages']}
    return dict(schema='native-fs-memory-narc-raw-v1',observed=observe,initial=F.input_record(f),fault=fault,stopped=stopped,
        stop_pc=uc.reg_read(C.UC_ARM_REG_PC),returned=state(),flow=flow,reads=reads,stores=stores,
        executed_count=count,ARM_count=count-tc,Thumb_count=tc,unique_executed_starts=len(seen),callback_count=callbacks,
        read_count=rc,store_count=wc,stack_peak=R.TOP-low,models=[],runtime_host_writes=[],backend=BACKEND,
        final_map_sha256=M.map_digest(pages),final_pages=[dict(ram=a,hex=b.hex())for a,b in sorted(pages.items())])

def bind(*,fixture,reader,memory,stack_top,code_spans):
    """Bind case-owned geometry/admission; receive no expected register values."""
    source_identity_guard()
    need(type(stack_top)is int and type(code_spans)is tuple,'typed complete caller producer geometry')
    namespace={**P.run.__globals__,'F':fixture,'L':reader,'M':memory,
               'R':types.SimpleNamespace(TOP=stack_top),'CODE_SPANS':code_spans}
    return types.FunctionType(_run_cpu.__code__,namespace,argdefs=_run_cpu.__defaults__)
