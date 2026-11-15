"""Native nonbusy Wait/IRQ composition of the authenticated isolated Read bench.

Completion is a declared three-field model projection, not a full SDK state.
All source edits are exact, counted and exposed as receipts; parents stay intact.
"""
from pathlib import Path
import copy,importlib.util,struct,types


def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


H=load('wait_isolated_read_parent',Path(__file__).parents[1]/'tools/attribuisci_fs_read.py')
B=H.B
E=load('wait_source_engine',Path(__file__).with_name('caller_species_bench.py'))
need,sha=B.need,B.sha
PARENT_SHA='cac4ca24793210c4dfa37bd91bef98dc737cbaa96b95757bc6b38af69448252a'
ENGINE_SHA='b8d8819e366528c2d30dde0d0f45c0270ff9c0e3f00989868828af96643efc31'
need(sha(Path(B.__file__).read_bytes())==PARENT_SHA and sha(Path(E.__file__).read_bytes())==ENGINE_SHA,'Wait qualified source drift')
BASE,SIZE,CORE,WRAPPER,SEND,WAIT=B.BASE,B.SIZE,B.CORE,B.WRAPPER,B.SEND,B.WAIT
TOP,FRAME,FILE,DEST,U32=B.TOP,B.FRAME,B.FILE,B.DEST,B.U32
DISABLE,RESTORE=0x20D3A38,0x20D3A4C
WAIT_PATH=(*range(WAIT,0x20D8328,4),0x20D838C,0x20D8390,0x20D8394,0x20D8398,*range(0x20D83A8,0x20D83BC,4))
EXTRA_CODE=set(WAIT_PATH)|set(range(DISABLE,DISABLE+20,4))|set(range(RESTORE,RESTORE+24,4))
RECIPES=[]


def derive(function,edits,namespace):
    fn,receipt=types.FunctionType(E.rewrite.__code__,{**vars(E),'PINS':{'read_bench':PARENT_SHA}})(
        B,function,edits,{**namespace,'__source_kind__':'read_bench'})
    RECIPES.append(receipt);return fn


def check_fixture(f):
    need(B.u32s(f['entry']),'Wait fixture registers unsigned32')
    original=f['entry'][15];need(original&0x0FFFFFFF in (0x1F,0x9F),'Wait privileged SYS I0/I1 only')
    clone=copy.deepcopy(f);clone['entry'][15]&=~0x80
    result=B.check_fixture(clone);dst,n=f['entry'][1:3];sp=f['entry'][13]
    need(dst+n<=sp-48 or dst>=sp,'Wait output cannot overlap either nested saved frame')
    return result


def completion_bytes(before,error):
    need(type(error)is int and error in (0,1),'Wait finite completion error0/1')
    stat=struct.unpack_from('<I',before)[0]
    return struct.pack('<3I',stat&~0x4F,0,error)


def complete_model(regs,memory,events,error):
    a=FILE+12-FRAME;before=memory.hex();blob=completion_bytes(memory[a:a+12],error)
    memory[a:a+12]=blob
    events.append(dict(address=FILE+12,bytes=12,model_words=3,regs=list(regs),frame_before=before,frame_after=memory.hex()))


def complete_guest(u,regs,events,error):
    before=bytes(u.mem_read(FRAME,240));blob=completion_bytes(before[FILE+12-FRAME:FILE+24-FRAME],error)
    cpu=regs();u.mem_write(FILE+12,blob);need(cpu==regs(),'Completion projection must not change CPU registers')
    events.append(dict(address=FILE+12,bytes=12,model_words=3,regs=cpu,frame_before=before.hex(),frame_after=bytes(u.mem_read(FRAME,240)).hex()))


def native_wait(r,at,word,store):
    """Source/dataflow oracle for the finite nonbusy path, including IRQ leaves."""
    need(word(FILE+12)&1==0,'Wait oracle requires nonbusy completion input')
    at(WAIT);r[13]-=24
    for i,index in enumerate((4,5,6,7,8,14)):store(WAIT,r[13]+4*i,r[index])
    at(0x20D8300);r[6]=r[0]
    at(0x20D8304);r[5]=0
    at(0x20D8308);r[14]=0x20D830C
    at(DISABLE);r[0]=r[15]
    at(DISABLE+4);r[1]=r[0]|0x80
    at(DISABLE+8);r[15]=(r[15]&~0xFF)|(r[1]&0xFF)
    at(DISABLE+12);r[0]&=0x80
    at(DISABLE+16)
    at(0x20D830C);r[1]=word(FILE+12)
    at(0x20D8310);r[4]=r[0]
    at(0x20D8314)
    value=r[1]&1;r[15]=(r[15]&0x3FFFFFFF)|((value>>31)<<31)|(int(value==0)<<30)
    at(0x20D8318,False)
    at(0x20D831C);r[0]=r[5]
    at(0x20D8320);r[15]=B.cmp(r[0],0,r[15])
    at(0x20D8324)
    at(0x20D838C);r[0]=r[4]
    at(0x20D8390);r[14]=0x20D8394
    at(RESTORE);r[1]=r[15]
    at(RESTORE+4);r[2]=r[1]&~0x80
    at(RESTORE+8);r[2]|=r[0]
    at(RESTORE+12);r[15]=(r[15]&~0xFF)|(r[2]&0xFF)
    at(RESTORE+16);r[0]=r[1]&0x80
    at(RESTORE+20)
    at(0x20D8394);r[15]=B.cmp(r[5],0,r[15])
    at(0x20D8398)
    at(0x20D83A8);r[0]=word(FILE+20)
    at(0x20D83AC);r[15]=B.cmp(r[0],0,r[15])
    success=r[0]==0
    at(0x20D83B0,success)
    if success:r[0]=1
    at(0x20D83B4,not success)
    if not success:r[0]=0
    at(0x20D83B8)
    target=word(r[13]+20);need(target==0x20D8168,'Wait saved return to Read core')
    for i,index in enumerate((4,5,6,7,8)):r[index]=word(r[13]+4*i)
    r[13]+=24


predict_derived=derive('predict',[
    ('required = []; optional = []','required = []; optional = []; completion = []',1),
    ('service(SEND, send_value)','service(SEND, send_value); complete_model(r,memory,completion,wait_value)',1),
    ('service(WAIT, wait_value)','native_wait(r,at,word,store); wait_value = int(bool(r[0]))',1),
    ('services=services, returned=r','services=services, completion=completion, returned=r',1),
    ('native_peak=24','native_peak=48',1)],dict(check_fixture=check_fixture,complete_model=complete_model,native_wait=native_wait))


def predict(f,error_value=0,send_value=1,clobber=False):
    need(type(error_value)is int and error_value in (0,1),'Wait completion error finite')
    return predict_derived(f,error_value,send_value,clobber)


def read_allowed(pc,address,n,f):
    sp=f['entry'][13]
    return n==4 and ((pc==WRAPPER and address==WRAPPER+12)or
        (pc in (0x20D810C,0x20D816C)and address==FILE+44)or
        (pc==0x20D8110 and address==FILE+40)or
        (pc in (0x20D8140,0x20D830C)and address==FILE+12)or
        (pc==0x20D83A8 and address==FILE+20)or
        (pc==0x20D817C and sp-24<=address<sp)or
        (pc==0x20D83B8 and sp-48<=address<sp-24))


source=Path(B.__file__).read_text();a=source.index('        need(n == 4 and ((pc == WRAPPER');b=source.index('        if observe: reads.append',a)
run_derived=derive('run',[
    ('reads = []; services = []','reads = []; services = []; completion = []',1),
    ('steps = 0; returned = None','allowed |= EXTRA_CODE\n    steps = 0; returned = None',1),
    ('if pc in (SEND, WAIT):','if pc == SEND:',1),
    ('u.reg_write(UC_ARM_REG_PC, entry[14]); return','complete_guest(u,regs,completion,wait_value)\n            u.reg_write(UC_ARM_REG_PC, entry[14]); return',1),
    ('allowed_write = (pc == CORE','allowed_write = (pc == WAIT and f[\'entry\'][13]-48 <= address < f[\'entry\'][13]-24) or (pc == CORE',1),
    (source[a:b],"        need(read_allowed(pc,address,n,f), 'Wait/Read owned field/literal/saved reads')\n",1),
    ('policy=dict(wait=wait_value','policy=dict(error=wait_value',1),
    ('reads=reads, services=services, steps=steps','reads=reads, services=services, completion=completion, steps=steps',1),
    ('native_peak=24','native_peak=48',1)],dict(check_fixture=check_fixture,EXTRA_CODE=EXTRA_CODE,read_allowed=read_allowed,complete_guest=complete_guest))


def run(f,bodies,error_value=0,send_value=1,clobber=False,observe=True,fill=0xA5):
    need(type(error_value)is int and error_value in(0,1)and type(send_value)is int and send_value in(0,1)and
         type(clobber)is bool and type(observe)is bool,'Wait finite policies')
    return run_derived(f,bodies,error_value,send_value,clobber,observe,fill)


def require_reads(r,f,expected):
    pos=check_fixture(f)[2];bottom=check_fixture(f)[1];sp=f['entry'][13]
    def reads_for(pc,addresses,values):return [dict(pc=hex(pc),address=a,bytes=4,hex=struct.pack('<I',v).hex())for a,v in zip(addresses,values)]
    reads=reads_for(WRAPPER,[WRAPPER+12],[CORE])+reads_for(0x20D810C,[FILE+44],[pos])+reads_for(0x20D8110,[FILE+40],[bottom])
    stat=struct.unpack_from('<I',bytes.fromhex(f['frame']),FILE-FRAME+12)[0]
    reads+=reads_for(0x20D8140,[FILE+12],[stat])+reads_for(0x20D830C,[FILE+12],[(stat|4)&~0x4F])
    reads+=reads_for(0x20D83A8,[FILE+20],[r['policy']['error']])
    wait_entry=expected['flow'][hex(WAIT)];wait_saved=[*wait_entry[4:9],wait_entry[14]]
    reads+=reads_for(0x20D83B8,[sp-48+4*i for i in range(6)],wait_saved)
    if r['policy']['error']==0:reads+=reads_for(0x20D816C,[FILE+44],[pos+f['entry'][2]])
    reads+=reads_for(0x20D817C,[sp-24+4*i for i in range(6)],[0,*f['entry'][4:8],f['entry'][14]])
    need(r['reads']==reads,'Wait/Read exact ordered nineteen/eighteen owned reads and values')


a=source.index('        expected_reads = ');b=source.index("        need(r['steps'] ==",a)
require_result=derive('require_result',[
    ("predict(f, p['wait'], p['send'], p['clobber'])","predict(f, p['error'], p['send'], p['clobber'])",1),
    ("'native_peak', 'services')","'native_peak', 'services', 'completion')",1),
    ("Read CPU17 qualified complete34 hook delivery/order","Wait/Read CPU17 qualified complete65 hook delivery/order",1),
    (source[a:b],"        require_reads(r,f,expected)\n",1),
    ("len(r['flow']) + 3","len(r['flow']) + 2",1),
    ("r['steps'] == 37","r['steps'] == 67",1)],dict(predict=predict,check_fixture=check_fixture,require_reads=require_reads))


# IRQ leaf collector derived from the independently reviewed capability probe.
IRQ_STOP=0x2000100
def run_irq_pair(cpsr,bodies,observe=True):
 from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM,UC_HOOK_CODE,UC_HOOK_MEM_READ,UC_HOOK_MEM_WRITE
 from unicorn.arm_const import UC_ARM_REG_CPSR,UC_ARM_REG_PC
 u=Uc(UC_ARCH_ARM,UC_MODE_ARM);need(u.ctl_get_cpu_model()==17,'qualified IRQ CPU17')
 u.mem_map(BASE,SIZE);u.mem_write(BASE,b'\x39'*SIZE)
 for pc,blob in bodies.items():u.mem_write(pc,blob)
 u.reg_write(UC_ARM_REG_CPSR,cpsr)
 values=[0xA5000000+i for i in range(13)]+[0x23BEEC0,IRQ_STOP,cpsr]
 for reg,value in zip(B.REGS[:-1],values[:-1]):u.reg_write(reg,value)
 regs=lambda:[u.reg_read(r)for r in B.REGS]
 initial=regs();before=sha(bytes(u.mem_read(BASE,SIZE)));flow=[];steps=[];phase='disable';fault=None
 def step(uc,pc,n,_):
  allowed=range(0x20D3A38,0x20D3A4C,4)if phase=='disable'else range(0x20D3A4C,0x20D3A64,4)
  if pc not in allowed or n!=4:raise ValueError('IRQ leaf whitelist')
  steps.append((phase,pc))
  if observe:flow.append(dict(phase=phase,pc=hex(pc),regs=regs()))
 def memory(*_):raise ValueError('IRQ leaves must not access data memory')
 u.hook_add(UC_HOOK_CODE,step);u.hook_add(UC_HOOK_MEM_READ,memory);u.hook_add(UC_HOOK_MEM_WRITE,memory)
 try:
  u.emu_start(0x20D3A38,IRQ_STOP,timeout=100000,count=8)
  after_disable=regs();stop_disable=u.reg_read(UC_ARM_REG_PC)
  phase='restore';u.emu_start(0x20D3A4C,IRQ_STOP,timeout=100000,count=8)
  after_restore=regs();stop_restore=u.reg_read(UC_ARM_REG_PC)
 except Exception as error:
  fault=dict(type=type(error).__name__,message=str(error));after_disable=locals().get('after_disable');after_restore=regs();stop_disable=locals().get('stop_disable');stop_restore=u.reg_read(UC_ARM_REG_PC)
 result=dict(input_cpsr=cpsr,observe=observe,initial=initial,after_disable=after_disable,after_restore=after_restore,stop_disable=stop_disable,stop_restore=stop_restore,flow=flow,steps=steps,before_ram_sha256=before,after_ram_sha256=sha(bytes(u.mem_read(BASE,SIZE))),fault=fault)
 del u;return result


def require_irq_rows(rows,bodies):
    need(set(bodies)=={DISABLE,RESTORE} and sha(bodies[DISABLE])=='a8cdb747f9936730571b220bb9570615892665b120713ffc59b1cb2d7dee76ff' and sha(bodies[RESTORE])=='46b5111b6fad094dfff177dca974d33b477cb72772ecfe95b74b1c7f656bc4fd','IRQ exact two native body identities')
    expected_grid=[((flags<<28)|fiq|irq|0x1F,observe)for flags in(0,6,10,15)for fiq in(0,64)for irq in(0,128)for observe in(True,False)]
    need([(row['input_cpsr'],row['observe'])for row in rows]==expected_grid,'IRQ distinct32-row CPSR/observer grid')
    memory=bytearray(b'\x39'*SIZE)
    for pc,blob in bodies.items():memory[pc-BASE:pc-BASE+len(blob)]=blob
    digest=sha(memory)
    for row in rows:
        need(type(row['input_cpsr'])is int and type(row['observe'])is bool and
             all(B.u32s(row[k])for k in('initial','after_disable','after_restore'))and all(B.u32s(e['regs'])for e in row['flow']), 'IRQ full unsigned32 register and policy types')
        cpsr=row['input_cpsr'];r=[0xA5000000+i for i in range(13)]+[0x23BEEC0,IRQ_STOP,cpsr]
        need(row['initial']==r and row['fault']is None,'IRQ exact initial16/fault-free state')
        expected=[]
        def at(pc):expected.append(dict(phase='disable'if pc<RESTORE else'restore',pc=hex(pc),regs=list(r)))
        at(DISABLE);r[0]=r[15]
        at(DISABLE+4);r[1]=r[0]|0x80
        at(DISABLE+8);r[15]=(r[15]&~0xFF)|(r[1]&0xFF)
        at(DISABLE+12);r[0]&=0x80
        at(DISABLE+16)
        need(row['after_disable']==r and row['stop_disable']==IRQ_STOP,'IRQ full16 after Disable')
        at(RESTORE);r[1]=r[15]
        at(RESTORE+4);r[2]=r[1]&~0x80
        at(RESTORE+8);r[2]|=r[0]
        at(RESTORE+12);r[15]=(r[15]&~0xFF)|(r[2]&0xFF)
        at(RESTORE+16);r[0]=r[1]&0x80
        at(RESTORE+20)
        need(row['after_restore']==r and r[15]==cpsr and r[0]==128 and row['stop_restore']==IRQ_STOP,'IRQ restored I/F/mode/NZCV full16')
        need(row['before_ram_sha256']==row['after_ram_sha256']==digest,'IRQ exact unchanged whole4MiB memory')
        steps=[[e['phase'],int(e['pc'],16)]for e in expected]
        need([list(s)for s in row['steps']]==steps and row['flow']==(expected if row['observe']else[]),'IRQ exact5+6 full16 trace/11steps')
    for on,off in zip(rows[::2],rows[1::2]):
        need(all(on[k]==off[k]for k in('initial','after_disable','after_restore','after_ram_sha256','steps','stop_disable','stop_restore')),
             'IRQ observer neutral fullCPU/memory')
    return True
