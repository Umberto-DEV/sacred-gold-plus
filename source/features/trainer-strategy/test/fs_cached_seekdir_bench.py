"""Source-only cached SeekDir success oracle and bounded native collector.

The predictor never imports Unicorn or disassembles code. Every context and
memory event follows the documented original SDK operations in execution order.
Synthetic CPU/stack/File inputs and captured resource slices remain distinct.
"""
from pathlib import Path
import importlib.util


def load(path,name):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


F=load(Path(__file__).parents[1]/'tools/congela_fs_cached_seekdir.py','cached_seekdir_frozen')
R=F.R
need=R.need
SELECTED=tuple(range(0x20d6bec,0x20d6c80,4))+tuple(range(0x20d6aa0,0x20d6adc,4))+tuple(range(0x20d6ae8,0x20d6af8,4))+tuple(range(0x20d6b50,0x20d6b60,4))+tuple(range(0x20d7484,0x20d749c,4))+(0x20d4a50,0x20d4a54,0x20d4a58,0x20d4a60,0x20d4a64,0x20d4ab8,0x20d4abc,0x20d4ac0,0x20d4b14,0x20d4b18,0x20d4b40,0x20d4b44,0x20d4b48,0x20d4b4c,0x20d4b68,0x20d4b6c,0x20d4b70,0x20d4b74,0x20d4b78,0x20d4b7c,0x20d4b80,0x20d4b84,0x20d4b88,0x20d4b8c,0x20d4b90,0x20d4b98,0x20d4b9c,0x20d4ba4,0x20d4ba8,0x20d4bb0)


def cmp(a,b,cpsr):
    value=(a-b)&0xffffffff
    overflow=((a^b)&(a^value)&0x80000000)!=0
    return (cpsr&0x0fffffff)|(value&0x80000000)|(int(value==0)<<30)|(int(a>=b)<<29)|(int(overflow)<<28)


def logical(value,cpsr):return (cpsr&0x3fffffff)|(value&0x80000000)|(int(value==0)<<30)


def predict(f):
    need(type(f['own_id'])is int and f['own_id']in(0,1) and type(f['precompleted_prop'])is bool,'typed isolated fixture')
    pages={a:bytearray(b)for a,b in f['pages'].items()};regs=list(f['entry_regs'])
    need(len(regs)==16 and all(type(x)is int and 0<=x<=0xffffffff for x in regs),'full16 typed source entry')
    need(regs[0]==R.FILE and regs[13]==R.TOP and regs[14]==F.RETURN and regs[15]==0x6000001f,'source entry ABI')
    need(int.from_bytes(F.read(pages,R.ARC+80,4),'little')==0x20d7484,'native memory callback required')
    flow=[];stores=[];reads=[];pc=F.ENTRY
    def at(address):
        nonlocal pc
        pc=address;flow.append(dict(pc=address,regs=list(regs)))
    def read(address,n=4):
        blob=F.read(pages,address,n);reads.append(dict(pc=pc,address=address,bytes=n,hex=blob.hex()))
        return int.from_bytes(blob,'little')
    def put(address,value,n=4):
        blob=value.to_bytes(n,'little');stores.append(dict(pc=pc,address=address,bytes=n,before=F.read(pages,address,n).hex(),value=value))
        F.put(pages,address,blob)
    def push(address,indices):
        at(address);regs[13]-=4*len(indices)
        for i,index in enumerate(indices):put(regs[13]+4*i,regs[index])
    def pop(address,indices,target):
        at(address);values=[read(regs[13]+4*i)for i in range(len(indices)+1)]
        for index,value in zip(indices,values):regs[index]=value
        regs[13]+=4*len(values);need(values[-1]==target,'source POP PC original return')
    def comparison(address,index,value):at(address);regs[15]=cmp(regs[index],value,regs[15])
    def tst(address,index,mask):at(address);regs[15]=logical(regs[index]&mask,regs[15])

    push(0x20d6bec,(4,5,6,14))
    at(0x20d6bf0);regs[13]-=16
    at(0x20d6bf4);regs[6]=regs[0]
    at(0x20d6bf8);regs[4]=read(regs[6]+8)
    at(0x20d6bfc);regs[5]=regs[6]+48
    at(0x20d6c00);put(regs[13],regs[4])
    at(0x20d6c04);regs[1]=read(regs[5]+4,2);need(regs[1]==f['own_id'],'source own_id binding')
    at(0x20d6c08);regs[2]=read(regs[4]+52)
    at(0x20d6c0c);regs[0]=regs[13]
    at(0x20d6c10);regs[3]=regs[2]+(regs[1]<<3)
    at(0x20d6c14);regs[1]=regs[13]+8
    at(0x20d6c18);regs[2]=8
    at(0x20d6c1c);put(regs[13]+4,regs[3])
    at(0x20d6c20);regs[14]=0x20d6c24

    push(0x20d6aa0,(3,4,5,6,7,8,9,14))
    at(0x20d6aa4);regs[7]=regs[0]
    at(0x20d6aa8);regs[4]=read(regs[7])
    at(0x20d6aac);regs[6]=regs[2]
    at(0x20d6ab0);regs[2]=read(regs[4]+28)
    at(0x20d6ab4);regs[0]=regs[4]
    at(0x20d6ab8);regs[2]|=0x200
    at(0x20d6abc);put(regs[4]+28,regs[2])
    at(0x20d6ac0);regs[2]=read(regs[7]+4)
    at(0x20d6ac4);regs[5]=read(regs[4]+80)
    at(0x20d6ac8);regs[3]=regs[6]
    at(0x20d6acc);regs[14]=0x20d6ad0

    push(0x20d7484,(3,14))
    at(0x20d7488);regs[0]=regs[2]
    at(0x20d748c);regs[2]=regs[3]
    at(0x20d7490);regs[14]=0x20d7494

    need(regs[0]==R.FNT+8*f['own_id'] and regs[1]==R.TOP-24 and regs[2]==8 and
         regs[0]%4==regs[1]%4==0,'finite aligned eight-byte copy')
    comparison(0x20d4a50,2,0);at(0x20d4a54);at(0x20d4a58)
    tst(0x20d4a60,1,1);at(0x20d4a64)
    at(0x20d4ab8);regs[12]=regs[1]^regs[0]
    tst(0x20d4abc,12,1);at(0x20d4ac0)
    tst(0x20d4b14,12,2);at(0x20d4b18)
    comparison(0x20d4b40,2,2);at(0x20d4b44)
    tst(0x20d4b48,1,2);at(0x20d4b4c)
    at(0x20d4b68);regs[3]=regs[2]&~3;regs[15]=logical(regs[3],regs[15])
    at(0x20d4b6c)
    at(0x20d4b70);regs[2]-=regs[3]
    at(0x20d4b74);regs[12]=regs[3]+regs[1]
    for _ in range(2):
        at(0x20d4b78);regs[3]=read(regs[0]);regs[0]+=4
        at(0x20d4b7c);put(regs[1],regs[3]);regs[1]+=4
        at(0x20d4b80);regs[15]=cmp(regs[1],regs[12],regs[15])
        at(0x20d4b84)
    tst(0x20d4b88,2,2);at(0x20d4b8c);at(0x20d4b90);at(0x20d4b98);at(0x20d4b9c)
    tst(0x20d4ba4,2,1);at(0x20d4ba8);at(0x20d4bb0)

    at(0x20d7494);regs[0]=0
    pop(0x20d7498,(3,),0x20d6ad0)
    comparison(0x20d6ad0,0,0);at(0x20d6ad4);at(0x20d6ad8)
    at(0x20d6ae8);regs[1]=read(regs[4]+28)
    at(0x20d6aec);regs[1]&=~0x200
    at(0x20d6af0);put(regs[4]+28,regs[1])
    at(0x20d6af4)
    at(0x20d6b50);regs[1]=read(regs[7]+4)
    at(0x20d6b54);regs[1]+=regs[6]
    at(0x20d6b58);put(regs[7]+4,regs[1])
    pop(0x20d6b5c,(3,4,5,6,7,8,9),0x20d6c24)

    at(0x20d6c24);regs[3]=regs[0];regs[15]=logical(regs[3],regs[15])
    at(0x20d6c28)
    at(0x20d6c2c);regs[12]=regs[6]+32
    at(0x20d6c30);regs[:3]=[read(regs[5]+4*i)for i in range(3)]
    at(0x20d6c34)
    for i in range(3):put(regs[12]+4*i,regs[i])
    at(0x20d6c38);regs[0]=read(regs[5]+6,2)
    comparison(0x20d6c3c,0,0)
    need(regs[15]&0x40000000,'fresh directory index required before LDREQ')
    at(0x20d6c40);regs[0]=read(regs[5]+8)
    need(regs[0]==0,'fresh directory position required before CMPEQ')
    comparison(0x20d6c44,0,0);at(0x20d6c48)
    need(regs[0]==0 and regs[15]&0x40000000,'finite fresh directory path')
    at(0x20d6c4c);regs[0]=read(regs[13]+12,2)
    at(0x20d6c50);put(regs[6]+38,regs[0],2)
    at(0x20d6c54);regs[1]=read(regs[4]+52)
    at(0x20d6c58);regs[0]=read(regs[13]+8)
    at(0x20d6c5c);regs[0]+=regs[1]
    at(0x20d6c60);put(regs[6]+40,regs[0])
    at(0x20d6c64);regs[1]=read(regs[13]+14,2)
    at(0x20d6c68);regs[0]=read(0x20d6c80)
    at(0x20d6c6c);regs[0]&=regs[1]
    at(0x20d6c70);put(regs[6]+44,regs[0])
    at(0x20d6c74);regs[0]=regs[3]
    at(0x20d6c78);regs[13]+=16
    pop(0x20d6c7c,(4,5,6),F.RETURN)
    need((len(flow),len(stores),len(reads))==(100,27,35)and set(x['pc']for x in flow)==set(SELECTED),'finite full source transcript')
    return dict(flow=flow,stores=stores,reads=reads,returned=list(regs),stop_pc=F.RETURN,
                native_peak=72,pages={a:bytes(b)for a,b in pages.items()})


def read_allowed(pc,address,size,own_id):
    words={0x20d6bf8:(R.FILE+8,),0x20d6c08:(R.ARC+52,),
        0x20d6c30:(R.FILE+48,R.FILE+52,R.FILE+56),0x20d6c40:(R.FILE+56,),
        0x20d6c54:(R.ARC+52,),0x20d6c58:(R.TOP-24,),0x20d6c68:(0x20d6c80,),
        0x20d6c7c:tuple(range(R.TOP-16,R.TOP,4)),0x20d6aa8:(R.TOP-32,),
        0x20d6ab0:(R.ARC+28,),0x20d6ae8:(R.ARC+28,),
        0x20d6ac0:(R.TOP-28,),0x20d6b50:(R.TOP-28,),0x20d6ac4:(R.ARC+80,),
        0x20d6b5c:tuple(range(R.TOP-64,R.TOP-32,4)),0x20d7498:(R.TOP-72,R.TOP-68),
        0x20d4b78:(R.FNT+8*own_id,R.FNT+8*own_id+4)}
    halves={0x20d6c04:R.FILE+52,0x20d6c38:R.FILE+54,0x20d6c4c:R.TOP-20,0x20d6c64:R.TOP-18}
    return size==4 and address in words.get(pc,()) or size==2 and address==halves.get(pc)


def write_allowed(pc,address,size):
    words={0x20d6bec:tuple(range(R.TOP-16,R.TOP,4)),0x20d6c00:(R.TOP-32,),
        0x20d6c1c:(R.TOP-28,),0x20d6c34:(R.FILE+32,R.FILE+36,R.FILE+40),
        0x20d6c60:(R.FILE+40,),0x20d6c70:(R.FILE+44,),
        0x20d6aa0:tuple(range(R.TOP-64,R.TOP-32,4)),0x20d6abc:(R.ARC+28,),
        0x20d6af0:(R.ARC+28,),0x20d6b58:(R.TOP-28,),0x20d7484:(R.TOP-72,R.TOP-68),
        0x20d4b7c:(R.TOP-24,R.TOP-20)}
    return size==4 and address in words.get(pc,()) or size==2 and pc==0x20d6c50 and address==R.FILE+38


BACKEND=dict(unicorn='2.1.4',CPU_model=17,
    scope='CortexA15 backend executing ARMv5 code; not ARM946 timing/cache/IRQ')


def run(f,observe=True):
    """Execute original authenticated pages, with no model or runtime host write.

    Faults are data in the raw record. The caller saves it before judging it.
    OFF retains only enforcement/counters and final bytes, without flow ledgers.
    """
    import unicorn as U
    from unicorn import arm_const as A
    need(type(observe)is bool,'typed observation switch')
    need(U.__version__==BACKEND['unicorn'],'qualified Unicorn version')
    uc=U.Uc(U.UC_ARCH_ARM,U.UC_MODE_ARM);uc.ctl_set_cpu_model(A.UC_CPU_ARM_CORTEX_A15)
    actual_backend=dict(unicorn=U.__version__,CPU_model=uc.ctl_get_cpu_model(),scope=BACKEND['scope'])
    need(F.wire(actual_backend)==F.wire(BACKEND),'actual backend identity')
    regs=tuple(getattr(A,'UC_ARM_REG_R'+str(i))for i in range(13))+(A.UC_ARM_REG_SP,A.UC_ARM_REG_LR,A.UC_ARM_REG_CPSR)
    for address,blob in f['pages'].items():uc.mem_map(address,4096);uc.mem_write(address,blob)
    uc.reg_write(A.UC_ARM_REG_CPSR,f['entry_regs'][15])
    for register,value in zip(regs[:15],f['entry_regs'][:15]):uc.reg_write(register,value)
    flow=[];reads=[];stores=[];seen=set();count=0;callback_count=0;read_count=0;store_count=0;low=R.TOP;stopped=False
    def state():return [uc.reg_read(r)&0xffffffff for r in regs]
    def code(machine,address,size,user):
        nonlocal count,callback_count,low,stopped
        callback_count+=1
        if address==F.RETURN:
            stopped=True;machine.emu_stop();return
        need(size==4 and address in SELECTED,'nonselected native instruction')
        count+=1;need(count<=256,'native instruction budget')
        seen.add(address);low=min(low,machine.reg_read(A.UC_ARM_REG_SP))
        if observe:flow.append(dict(pc=address,regs=state()))
    def access(machine,kind,address,size,value,user):
        nonlocal read_count,store_count
        pc=machine.reg_read(A.UC_ARM_REG_PC)
        if kind==U.UC_MEM_WRITE:
            need(write_allowed(pc,address,size),'native write outside exact owner/site')
            store_count+=1
            if observe:stores.append(dict(pc=pc,address=address,bytes=size,before=bytes(machine.mem_read(address,size)).hex(),value=value&((1<<(8*size))-1)))
        else:
            need(read_allowed(pc,address,size,f['own_id']),'native read outside exact input/site')
            read_count+=1
            if observe:reads.append(dict(pc=pc,address=address,bytes=size,hex=bytes(machine.mem_read(address,size)).hex()))
    uc.hook_add(U.UC_HOOK_CODE,code)
    uc.hook_add(U.UC_HOOK_MEM_READ|U.UC_HOOK_MEM_WRITE,access)
    fault=None
    try:uc.emu_start(F.ENTRY,0,timeout=1000000,count=256)
    except (ValueError,U.UcError)as error:fault=type(error).__name__+': '+str(error)
    final_pages={a:bytes(uc.mem_read(a,4096))for a in f['pages']}
    return dict(schema='native-fs-cached-seekdir-raw-v1',observed=observe,initial=F.input_record(f),
        fault=fault,stopped=stopped,stop_pc=uc.reg_read(A.UC_ARM_REG_PC),returned=state(),
        flow=flow,reads=reads,stores=stores,native_count=count,unique_native_starts=len(seen),
        callback_count=callback_count,read_count=read_count,store_count=store_count,native_peak=R.TOP-low,
        final_map_sha256=F.map_digest(final_pages),final_pages=[dict(ram=a,hex=b.hex())for a,b in sorted(final_pages.items())],
        models=[],runtime_host_writes=[],backend=actual_backend)


def require_run(f,raw):
    predicted=predict(f)
    need(F.wire(raw.get('backend'))==F.wire(BACKEND),'qualified backend identity')
    need(F.wire(raw['initial'])==F.wire(F.input_record(f)),'frozen complete input')
    need(raw['fault']is None and raw['stopped']is True and raw['stop_pc']==F.RETURN,'native finite original return')
    need(raw['models']==raw['runtime_host_writes']==[],'zero model/host ledger')
    need((raw['native_count'],raw['unique_native_starts'],raw['callback_count'],raw['read_count'],raw['store_count'],raw['native_peak'])==(100,96,101,35,27,72),'native exact counts/bounds')
    need(F.wire(raw['returned'])==F.wire(predicted['returned']),'source full16 returned ABI')
    need(F.wire(raw['final_pages'])==F.wire([dict(ram=a,hex=b.hex())for a,b in sorted(predicted['pages'].items())]),'source entire mapped pages')
    need(raw['final_map_sha256']==F.map_digest(predicted['pages']),'source complete final map hash')
    if raw['observed']is True:
        for key,label in(('flow','contexts'),('reads','reads'),('stores','native stores')):
            need(F.wire(raw[key])==F.wire(predicted[key]),'source '+label)
    else:
        need(raw['observed']is False and raw['flow']==raw['reads']==raw['stores']==[],'OFF no observation projections')
    return predicted
