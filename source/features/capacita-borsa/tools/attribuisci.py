#!/usr/bin/env python3
"""Attribute the current expanded-Bag composite without weakening its test bench."""
import hashlib
import json
from pathlib import Path
import struct
import sys

SOURCE=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(SOURCE))
from sgp12.blocchi import capacita_borsa as LEGACY
from sgp131 import bag_alloc,bag_foreign
from sgp13 import training

BASE=0x023DBF00
BASE_SHA='e41d95a3a7f57e504697c83f754c6fbb57745291d149dcb9d94b4dcde5f3c1fb'
CURRENT_SHA='88a6736f0cecbc681864ac765c6309ad8480c406f3150fb54b6d1743f3468448'
SCHEMA='attribution-only-current-bag-v1'


def sha(data):return hashlib.sha256(data).hexdigest()


def need(ok,why):
    if not ok:raise ValueError(why)


def compose_current(base):
    """Build expected project code from a known compilation and two source recipes."""
    need(len(base)==3584 and sha(base)==BASE_SHA,'unknown baseline compilation')
    bag_alloc._constants()
    result=bytearray(base);patches=[]
    hook=training.entry_hook(bag_foreign.HOOK,bag_foreign.TRAINING_SAVE)
    need(hook==bag_foreign.HOOK_BYTES,'Training hook recipe drift')
    for owner,address,before,after in (
        ('bag-allocation',bag_alloc.ENTRY,bag_alloc.PREIMAGE,bag_alloc.POSTIMAGE),
        ('training',bag_foreign.HOOK,bytes.fromhex('38b50c1c051c6069'),hook)):
        offset=address-BASE
        need(0<=offset and offset+len(before)<=len(base) and len(before)==len(after),'patch extent')
        need(base[offset:offset+len(before)]==before,'patch preimage '+owner)
        result[offset:offset+len(after)]=after
        patches.append(dict(owner=owner,address=address,bytes=len(after),
            preimage_sha256=sha(before),postimage_sha256=sha(after)))
    need(sha(result)==CURRENT_SHA,'composed current code identity')
    return bytes(result),dict(base_sha256=BASE_SHA,current_sha256=CURRENT_SHA,patches=patches,
        source_sha256={str(p.relative_to(SOURCE)):sha(p.read_bytes()) for p in
            (SOURCE/'sgp131/bag_alloc.py',SOURCE/'sgp13/training.py',SOURCE/'sgp131/bag_foreign.py')})


def load_baseline(directory):
    manifest,blob=LEGACY._carica_build(directory)
    canonical=json.loads((SOURCE/'sgp12/build/capacita_borsa/manifesto.json').read_text())
    need(manifest['simboli']==canonical['simboli'] and
         manifest['opzioni_compilazione']==canonical['opzioni_compilazione'],
         'baseline symbol/flag drift')
    need(sha(blob)==BASE_SHA,'baseline binary drift')
    return manifest,blob


def write_bridge(base_build,work):
    """This artifact is for a strict bench, not for the production installer."""
    manifest,base=load_baseline(base_build)
    current,proof=compose_current(base)
    target=Path(work);target.mkdir(parents=True,exist_ok=True)
    bridge=json.loads(json.dumps(manifest));bridge['schema']=SCHEMA
    bridge['purpose']='attribution only; compiled baseline plus two source recipes; not an installer build'
    bridge['blob']={'byte':len(current),'sha256':sha(current)}
    origin=dict(method='compiled project baseline plus source recipes',
        base_origin=json.loads((Path(base_build)/'origine.json').read_text()),composition=proof)
    for name,data in (('blob.bin',current),('manifesto.json',(json.dumps(bridge,indent=2)+'\n').encode()),
                      ('origine.json',(json.dumps(origin,indent=2)+'\n').encode())):
        path=target/name
        need(not path.exists() or path.read_bytes()==data,'existing bridge artifact differs: '+name)
        path.write_bytes(data)
    (target/'SHA256SUMS').write_text(''.join(sha((target/name).read_bytes())+'  '+name+'\n'
        for name in ('blob.bin','manifesto.json','origine.json')))
    return bridge,proof


def item_resource(raw,nds):
    """Raw FAT/BTAF/GMIF readback of member50, separately checked with ndspy."""
    import ndspy.narc
    name='a/0/1/7';fid=nds.filenames.idOf(name)
    fat=struct.unpack_from('<I',raw,0x48)[0];start,end=struct.unpack_from('<II',raw,fat+8*fid)
    archive=bytes(raw[start:end]);need(archive==bytes(nds.files[fid]),'item FAT extent')
    need(archive[:4]==b'NARC' and struct.unpack_from('<IHH',archive,8)==(len(archive),16,3),'item NARC header')
    magic,fatsize,count=struct.unpack_from('<4sII',archive,16)
    need(magic==b'BTAF' and count==516 and fatsize==12+8*count,'item BTAF')
    names=16+fatsize;need(archive[names:names+4]==b'BTNF','item BTNF')
    image=names+struct.unpack_from('<I',archive,names+4)[0]
    need(archive[image:image+4]==b'GMIF' and image+struct.unpack_from('<I',archive,image+4)[0]==len(archive),'item GMIF')
    lo,hi=struct.unpack_from('<II',archive,28+8*50)
    need(0<=lo<hi and image+8+hi<=len(archive) and hi-lo==34,'item member bounds')
    record=archive[image+8+lo:image+8+hi]
    need(record==bytes(ndspy.narc.NARC(archive).files[50]),'raw/ndspy item member')
    return record,dict(name=name,file_id=fid,archive_sha256=sha(archive),members=count,
        member=50,member_bytes=34,member_sha256=sha(record),rom_offset=hex(start+image+8+lo),
        field_pocket_word=struct.unpack_from('<H',record,8)[0],
        decoded_pocket=(struct.unpack_from('<H',record,8)[0]>>7)&15)


def item_attributes(raw,segments,record):
    """Actual GetItemAttr+lookup+decoder; only NARC allocation/read and free transports are stubbed."""
    from unicorn import Uc,UC_ARCH_ARM,UC_MODE_THUMB,UC_HOOK_CODE,UC_HOOK_MEM_READ,UC_HOOK_MEM_WRITE
    from unicorn.arm_const import (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R4,
        UC_ARM_REG_R5,UC_ARM_REG_R6,UC_ARM_REG_R7,UC_ARM_REG_R8,UC_ARM_REG_R9,
        UC_ARM_REG_R10,UC_ARM_REG_R11,UC_ARM_REG_SP,UC_ARM_REG_LR,UC_ARM_REG_PC,UC_ARM_REG_CPSR)
    uc=Uc(UC_ARCH_ARM,UC_MODE_THUMB);uc.mem_map(0x02000000,0x400000)
    for address,offset,size in segments:
        if 0x02000000<=address and address+size<=0x02400000:uc.mem_write(address,bytes(raw[offset:offset+size]))
    data,stop,stack=0x02380000,0x023AF000,0x023B0000
    saved=(UC_ARM_REG_R4,UC_ARM_REG_R5,UC_ARM_REG_R6,UC_ARM_REG_R7,
           UC_ARM_REG_R8,UC_ARM_REG_R9,UC_ARM_REG_R10,UC_ARM_REG_R11)
    allrows=[]
    for attribute in (5,*range(14,59)):
        trace=[];state={'freed':True,'instructions':0,'stack_depth':0}
        def code(cpu,address,size,unused):
            state['instructions']+=1;state['stack_depth']=max(state['stack_depth'],stack-cpu.reg_read(UC_ARM_REG_SP))
            if address==0x02007524:
                args=[cpu.reg_read(r) for r in (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2)]
                need(args==[17,50,12],'actual item NARC/member/heap lookup')
                trace.append(dict(boundary='NARC allocation/read',arguments=args))
                cpu.mem_write(data,record+b'\xA5'*4);state['freed']=False
                cpu.reg_write(UC_ARM_REG_R0,data);cpu.reg_write(UC_ARM_REG_PC,cpu.reg_read(UC_ARM_REG_LR))
            elif address==0x0201AB80:
                args=[cpu.reg_read(r) for r in (UC_ARM_REG_R0,UC_ARM_REG_R1)]
                need(args==[12,data] and not state['freed'],'item free lifetime')
                trace.append(dict(boundary='Heap_FreeExplicit',arguments=args));state['freed']=True
                cpu.reg_write(UC_ARM_REG_R0,0);cpu.reg_write(UC_ARM_REG_PC,cpu.reg_read(UC_ARM_REG_LR))
            else:need(0x02077CE8<=address<0x02078138,'unexpected item getter execution')
        def read(cpu,access,address,size,value,unused):
            if data<=address<data+0x1000:
                need(not state['freed'] and address+size<=data+len(record),'item read outside live record')
        def write(cpu,access,address,size,value,unused):
            need(stack-256<=address and address+size<=stack,'item getter nonstack write')
        hooks=[uc.hook_add(UC_HOOK_CODE,code),uc.hook_add(UC_HOOK_MEM_READ,read),uc.hook_add(UC_HOOK_MEM_WRITE,write)]
        expected=[0xA5000000+i for i in range(8)]
        for register,value in zip(saved,expected):uc.reg_write(register,value)
        for register,value in ((UC_ARM_REG_R0,50),(UC_ARM_REG_R1,attribute),(UC_ARM_REG_R2,12),
                               (UC_ARM_REG_SP,stack),(UC_ARM_REG_LR,stop|1)):uc.reg_write(register,value)
        try:uc.emu_start(0x02077D89,stop,count=4096)
        finally:
            for hook in hooks:uc.hook_del(hook)
        need(uc.reg_read(UC_ARM_REG_PC)==stop and uc.reg_read(UC_ARM_REG_SP)==stack
             and uc.reg_read(UC_ARM_REG_CPSR)&32 and [uc.reg_read(r) for r in saved]==expected,'item getter return/ABI')
        need(state['freed'] and len(trace)==2 and bytes(uc.mem_read(data+34,4))==b'\xA5'*4,'item transport completion/canary')
        allrows.append(dict(attribute=attribute,result=uc.reg_read(UC_ARM_REG_R0),trace=trace,**state))
    return allrows


def checked(machine,operation,*,tail=False):
    """Add return/ABI/write-set checks to the existing strict capacity bench."""
    from unicorn import UC_HOOK_CODE,UC_HOOK_MEM_WRITE
    from unicorn.arm_const import (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3,
        UC_ARM_REG_R4,UC_ARM_REG_R5,UC_ARM_REG_R6,UC_ARM_REG_R7,UC_ARM_REG_R8,
        UC_ARM_REG_R9,UC_ARM_REG_R10,UC_ARM_REG_R11,UC_ARM_REG_SP,UC_ARM_REG_PC,UC_ARM_REG_CPSR)
    uc=machine.mu;stack=0x023B0000;stop=0x023AF000
    saved=(UC_ARM_REG_R4,UC_ARM_REG_R5,UC_ARM_REG_R6,UC_ARM_REG_R7,
           UC_ARM_REG_R8,UC_ARM_REG_R9,UC_ARM_REG_R10,UC_ARM_REG_R11)
    expected=[0xC4000000+i for i in range(8)]
    for reg,value in zip(saved,expected):uc.reg_write(reg,value)
    if tail:expected[:2]=[0xC4C4C4C4,0xC5C5C5C5]
    guard=b'\xA5\x5A\xC3\x3C'*4;uc.mem_write(stack+0x40,guard)
    # Sparse fixture regions, not game save layouts or universal stack limits.
    areas=(('stack',stack-0x2000,stack+0x20),('capacity state',0x023DD700,0x023DD700+4808),
           ('native Bag',0x0220D634,0x0220D634+1948),('model heap',0x02240000,0x02250000),
           ('out parameters',0x02360000,0x02360008),('Candy action',0x02320027,0x02320028),
           ('Candy search',0x02320038,0x0232003C))
    info={'instructions':0,'stack_depth':0,'writes':{},'events':[]}
    sites={0x02078188:'native Bag_New',0x0207879C:'native Save_Bag_Get',
        0x02078724:'native Bag_GetSlot',0x02078240:'native Bag_GetPocket',
        0x02078550:'native Bag_GetItemQuantity',0x02078434:'native Bag_TakeItem',
        0x02081E96:'Candy tail',0x023DAC00:'Candy shim',
        0x0207463C:'native Party_GetCount',0x02074640:'native Party_GetCapacity'}
    sites.update({(int(value,16) if isinstance(value,str) else value):name for name,value in machine.symbols.items()})
    sites={address&~1:name for address,name in sites.items()}
    def code(cpu,address,size,unused):
        info['instructions']+=1
        info['stack_depth']=max(info['stack_depth'],stack-cpu.reg_read(UC_ARM_REG_SP))
        if address in sites:
            need(len(info['events'])<96,'capacity event budget')
            info['events'].append(dict(site=hex(address),function=sites[address],
                arguments=[cpu.reg_read(r) for r in (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3)],
                sp=cpu.reg_read(UC_ARM_REG_SP)))
    def write(cpu,access,address,size,value,unused):
        found=[name for name,lo,hi in areas if lo<=address and address+size<=hi]
        need(len(found)==1,'capacity unexpected write %#x+%d'%(address,size))
        name=found[0];row=info['writes'].setdefault(name,{'count':0,'bytes':0,'low':address,'high':address+size})
        row['count']+=1;row['bytes']+=size;row['low']=min(row['low'],address);row['high']=max(row['high'],address+size)
    hooks=[uc.hook_add(UC_HOOK_CODE,code),uc.hook_add(UC_HOOK_MEM_WRITE,write)]
    try:result=operation()
    finally:
        for hook in hooks:uc.hook_del(hook)
    need(uc.reg_read(UC_ARM_REG_PC)==stop and uc.reg_read(UC_ARM_REG_SP)==stack
         and uc.reg_read(UC_ARM_REG_CPSR)&32 and [uc.reg_read(r) for r in saved]==expected
         and bytes(uc.mem_read(stack+0x40,16))==guard,'capacity actual return/ABI/canary')
    need(not machine.errors and not machine.original_saves and not machine.writes,'unexpected assert/save/flash write')
    return result,info


def integration(rom,bridge,record,attributes):
    """Actual native Bag APIs and Candy hook; metadata/Mon/UI transports are declared models."""
    import gc,importlib.util
    directory=SOURCE/'features/caramelle/test';sys.path.insert(0,str(directory))
    path=directory/'test_caramelle.py'
    spec=importlib.util.spec_from_file_location('current_bag_candy_adapter',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    parent=module.CapacityCandyBench
    class Medicine(parent):
        POCKET=attributes[5]
        SUPPORT=tuple(a for a in parent.SUPPORT if a not in (0x0207463C,0x02074640))
        def __init__(self):
            super().__init__(rom,bridge)
            self.b.mu.mem_write(self.PARTY,struct.pack('<II',6,6))
            self.b.mu.mem_write(0x022F0000,record)
        def _support(self,cpu,address,size,unused):
            if address==0x02077DAC:
                from unicorn.arm_const import UC_ARM_REG_R0,UC_ARM_REG_R1
                field=cpu.reg_read(UC_ARM_REG_R1)
                need(field in attributes and field!=5,'unverified preloaded item attribute '+str(field))
                self.support_calls.append((address,cpu.reg_read(UC_ARM_REG_R0),field))
                self._return(attributes[field])
            else:super()._support(cpu,address,size,unused)
    rows=[]
    def call(x,address,*args):return checked(x.b,lambda:x.b.call(address,*args))
    for index in (0,40,41):
        for initial in (1,2):
            x=Medicine();steps=[]
            bag,proof=call(x,0x0207879C,0x02200000);steps.append(dict(operation='get Bag',**proof))
            # Exercise the fourth argument and stacked fifth argument through the 16-byte r3-preserving shim.
            pocket,proof=call(x,0x02078240,bag,50,0x02360000,0x02360004,12)
            slots,count=struct.unpack('<II',x.b.mu.mem_read(0x02360000,8))
            need(pocket==1 and count==42,'actual Medicine pocket/count')
            steps.append(dict(operation='get pocket/count',**proof))
            slot,proof=call(x,0x02078724,bag,1,index);need(slot==slots+4*index,'actual slot address')
            steps.append(dict(operation='get slot',**proof));x.b.mu.mem_write(slot,struct.pack('<HH',50,initial))
            before,proof=call(x,0x02078550,bag,50,12);steps.append(dict(operation='quantity before',**proof))
            taken,proof=call(x,0x02078434,bag,50,1,12);steps.append(dict(operation='take one',**proof))
            after,proof=call(x,0x02078550,bag,50,12);steps.append(dict(operation='quantity after',**proof))
            need((before,taken,after)==(initial,1,initial-1),'actual native/extra quantity')
            tail,proof=checked(x.b,lambda:x.candy_tail(bag),tail=True);steps.append(dict(operation='Candy tail',**proof))
            need(tail[:2]==((4 if after else 32),0) and (tail[2]==0 if after else tail[2]==0x7777),'actual Candy re-entry')
            quantity,proof=call(x,0x02078550,bag,50,12);steps.append(dict(operation='quantity after tail',**proof))
            need(quantity==after,'Candy tail consumed another item')
            need(not any(a in (0x02078550,0x02078434,0x0207463C,0x02074640) for a,*rest in x.support_calls),'native API substituted')
            rows.append(dict(case='consume',index=index,initial=initial,before=before,after=after,
                candy_state=tail[0],action=tail[1],steps=steps,support=x.support_calls))
            del x;gc.collect()
    for level in (99,100):
        x=Medicine();bag,first=call(x,0x0207879C,0x02200000)
        slot,second=call(x,0x02078724,bag,1,40);x.b.mu.mem_write(slot,struct.pack('<HH',50,1))
        result,proof=checked(x.b,lambda:x.can_use_at_level(level))
        quantity,last=call(x,0x02078550,bag,50,12)
        need(result==int(level==99) and quantity==1,'native level predicate/quantity')
        rows.append(dict(case='level predicate',level=level,result=result,quantity=quantity,
            steps=[first,second,proof,last],support=x.support_calls))
        del x;gc.collect()
    return rows


def constructors(raw,segments):
    """Actual Bag_New and current allocator guard; only Heap_Alloc is modeled."""
    from unicorn import Uc,UC_ARCH_ARM,UC_MODE_THUMB,UC_HOOK_CODE,UC_HOOK_MEM_WRITE
    from unicorn.arm_const import (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R4,UC_ARM_REG_R5,
        UC_ARM_REG_R6,UC_ARM_REG_R7,UC_ARM_REG_R8,UC_ARM_REG_R9,UC_ARM_REG_R10,
        UC_ARM_REG_R11,UC_ARM_REG_SP,UC_ARM_REG_LR,UC_ARM_REG_PC,UC_ARM_REG_CPSR)
    rows=[];stack,stop,buffer=0x023B0000,0x023AF000,0x02240000
    saved=(UC_ARM_REG_R4,UC_ARM_REG_R5,UC_ARM_REG_R6,UC_ARM_REG_R7,
           UC_ARM_REG_R8,UC_ARM_REG_R9,UC_ARM_REG_R10,UC_ARM_REG_R11)
    for allocation in (0,buffer):
        uc=Uc(UC_ARCH_ARM,UC_MODE_THUMB);uc.mem_map(0x02000000,0x400000)
        for address,offset,size in segments:
            if 0x02000000<=address and address+size<=0x02400000:uc.mem_write(address,bytes(raw[offset:offset+size]))
        uc.mem_write(buffer,b'\xA5'*(2380+16))
        expected=[0xD4000000+i for i in range(8)]
        for register,value in zip(saved,expected):uc.reg_write(register,value)
        for register,value in ((UC_ARM_REG_R0,12),(UC_ARM_REG_SP,stack),(UC_ARM_REG_LR,stop|1)):
            uc.reg_write(register,value)
        trace=[];state={'instructions':0,'stack_depth':0,'heap_writes':0,'heap_bytes':0}
        def code(cpu,address,size,unused):
            state['instructions']+=1;state['stack_depth']=max(state['stack_depth'],stack-cpu.reg_read(UC_ARM_REG_SP))
            if address==0x0201AA8C:
                arguments=[cpu.reg_read(UC_ARM_REG_R0),cpu.reg_read(UC_ARM_REG_R1)]
                need(arguments==[12,2380],'constructor allocation ABI')
                trace.append(dict(boundary='Heap_Alloc',arguments=arguments,result=allocation))
                cpu.reg_write(UC_ARM_REG_R0,allocation);cpu.reg_write(UC_ARM_REG_PC,cpu.reg_read(UC_ARM_REG_LR))
            else:need(0x02078188<=address<0x02078190 or BASE<=address<BASE+3584,'constructor unexpected code')
        def write(cpu,access,address,size,value,unused):
            if stack-256<=address and address+size<=stack:return
            need(allocation and buffer<=address and address+size<=buffer+2380,'constructor out-of-buffer write')
            state['heap_writes']+=1;state['heap_bytes']+=size
        uc.hook_add(UC_HOOK_CODE,code);uc.hook_add(UC_HOOK_MEM_WRITE,write)
        uc.emu_start(0x02078189,stop,count=20000)
        need(uc.reg_read(UC_ARM_REG_PC)==stop and uc.reg_read(UC_ARM_REG_SP)==stack
             and uc.reg_read(UC_ARM_REG_CPSR)&32 and [uc.reg_read(r) for r in saved]==expected
             and uc.reg_read(UC_ARM_REG_R0)==allocation and len(trace)==1,'constructor return/ABI')
        need(bytes(uc.mem_read(buffer,2380))==(bytes(2380) if allocation else b'\xA5'*2380)
             and bytes(uc.mem_read(buffer+2380,16))==b'\xA5'*16,'constructor initialization/canary')
        need(state['heap_bytes']==(2380 if allocation else 0),'constructor write extent')
        rows.append(dict(allocation='nonNULL' if allocation else 'NULL',trace=trace,**state))
    return rows


BASES={'EN':('281c2d68e442479e679d8b7e36566ade614d236151c65c9684bad6985461827d',127104144),
       'IT':('7b61646c627eb67cd991dbc33d68519edd69395468ea8b326e867fe98e62d077',131906120)}
RETAILS={'EN':'65f02a56842b75aa92d775d56d657a56fe3fa993550b04dc20704ab82d760105',
         'IT':'013d04f5512b01ad98735a5f850dc039f0ee80bc57035b3a10e8b650be690ce1'}
NATIVE_WINDOWS=((0x02078434,0x90),(0x02078550,0xF4))


def analyze(rom,base,retail,base_build,work,language):
    import gc,ndspy.rom
    from sgp12.rom import Arm9,Rifiuto
    pin=json.loads((SOURCE/'distribution/game-1.3.2-r4.json').read_text())['targets'][language]
    manifest,compiled=load_baseline(base_build)
    expected,composition=compose_current(compiled)
    native={};inputs=[];ranges=[];resource=None;attributes=None;ctor=None
    for label,path,digest,size in (('retail',retail,RETAILS[language],134217728),
            ('base11',base,*BASES[language]),('r4',rom,pin['sha256'],pin['bytes'])):
        arm=Arm9(path) if label=='r4' else None
        raw=arm.raw if arm else Path(path).read_bytes()
        need(len(raw)==size and sha(raw)==digest,'exact '+label+' input')
        nds=ndspy.rom.NintendoDSRom(raw);main=nds.loadArm9()
        def read(address,size):
            matches=[bytes(s.data[address-s.ramAddress:address-s.ramAddress+size])
                     for s in main.sections if s.ramAddress<=address and address+size<=s.ramAddress+len(s.data)]
            need(len(matches)==1,'ndspy address mapping')
            got=matches[0]
            if arm is None:return got
            need(got==arm.leggi(address,size),'raw/ndspy address mapping')
            offsets=[offset+address-start for start,offset,length in arm.segmenti
                     if start<=address and address+size<=start+length]
            need(len(offsets)==1,'raw physical extent')
            if label=='r4':ranges.append(dict(ram=hex(address),rom_offset=hex(offsets[0]),bytes=size,sha256=sha(got)))
            return got
        native[label]=[read(address,size) for address,size in NATIVE_WINDOWS]
        inputs.append(dict(input=label,sha256=digest,bytes=len(raw),native_window_sha256=[sha(b) for b in native[label]]))
        if label=='r4':
            need(read(BASE,11264)==expected+bytes(11264-len(expected)),'complete current Bag owner')
            # Independent encoding of the simple and r3-preserving tail dispatchers.
            for site,name in ((0x02078188,'new'),(0x0207879C,'get'),(0x02078724,'slot'),(0x02078240,'pocket')):
                target=int(manifest['simboli']['sgp_cap_'+name],16)
                hook=(struct.pack('<6HI',0xB408,0x4B02,0x469C,0xBC08,0x4760,0x46C0,target|1)
                      if name=='pocket' else struct.pack('<HHI',0x4B00,0x4718,target|1))
                need(read(site,len(hook))==hook,'native '+name+' dispatcher')
            need(read(0x023DCC9C,8)==bytes.fromhex('10b5f4f71dfc10bd'),'Training successor hook')
            # This comparison identifies the recipe target, not its complete SAVE implementation.
            import capstone
            dis=list(capstone.Cs(capstone.CS_ARCH_ARM,capstone.CS_MODE_THUMB).disasm(read(0x023DCC9E,4),0x023DCC9E))
            need(len(dis)==1 and dis[0].mnemonic=='bl' and int(dis[0].op_str.lstrip('#'),0)==0x023D14DC,'Training BL destination')
            record,resource=item_resource(raw,nds)
            need(resource['decoded_pocket']==1 and resource['member_sha256']=='60fdc4574595c465a91aa999bb35ed33290f66fc74242de8ad35b5f7e429e0d7','exact Candy resource')
            # Lookup row is read from the installed native literal, not inferred from item ID.
            table=struct.unpack('<I',read(0x02077D34,4))[0]
            need(table==0x02100194 and struct.unpack('<4H',read(table+50*8,8))==(50,90,91,68),'actual item lookup row')
            attributes=item_attributes(raw,arm.segmenti,record)
            values={x['attribute']:x['result'] for x in attributes}
            need((values[5],values[14],values[23],values[25])==(1,1,1,1),'actual Candy pocket/use/revive/level flags')
            ctor=constructors(raw,arm.segmenti)
            mapping=dict(segments=[dict(ram=hex(a),rom_offset=hex(o),bytes=n) for a,o,n in arm.segmenti],
                         arm9_header=struct.unpack_from('<4I',raw,0x20),compression='uncompressed ARM9 and autoload sections')
        del raw,arm,nds,main;gc.collect()
    need(native['retail']==native['base11']==native['r4'],'native Quantity/Take revision drift')
    bridge=Path(work)/'bridge-build';write_bridge(base_build,bridge)
    try:LEGACY._carica_build(bridge)
    except Rifiuto:installer_rejects=True
    else:raise ValueError('attribution bridge accepted as production build')
    flow=integration(rom,bridge,record,values)
    return dict(schema='bag-quantity-source-rom-v1',language=language,inputs=inputs,
        composition=composition,base_build=dict(compiler=manifest['compilatore'],flags=manifest['opzioni_compilazione'],
            origin=json.loads((Path(base_build)/'origine.json').read_text()),symbols=manifest['simboli']),
        mapping=mapping,ranges=ranges,resource=resource,item_attributes=attributes,constructors=ctor,
        verifier_sha256=sha(Path(__file__).read_bytes()),
        dependencies_sha256={str(p.relative_to(SOURCE)):sha(p.read_bytes()) for p in (
            SOURCE/'sgp12/rom.py',SOURCE/'features/caramelle/tools/carica_text.py',
            SOURCE/'features/capacita-borsa/test/banco.py',SOURCE/'features/caramelle/test/test_caramelle.py')},
        bridge=dict(schema=SCHEMA,production_loader_rejects=installer_rejects),integration=flow,
        conclusions=dict(binary_reconstruction='3584-byte composite and complete11264-byte initial owner',
            provenance='compiled project core plus allocation and Training hook source recipes; bounded native HGSS windows',
            execution='isolated native entry/quantity/consume/Candy re-entry; modeled metadata/heap/Mon/UI/flash transports',
            unproved=['natural gameplay','native SAVE/cold restart','encrypted personal Pokémon','hardware','complete Training SAVE implementation']))


def main():
    import argparse
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('rom','base','retail','base-build','work','json'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--language',choices=('EN','IT'),required=True)
    a=p.parse_args();result=analyze(a.rom,a.base,a.retail,a.base_build,a.work,a.language)
    a.json.parent.mkdir(parents=True,exist_ok=True);a.json.write_text(json.dumps(result,indent=2)+'\n')
    print(a.language, 'complete owner + two recipes + native resource + constructor/8 flow cases PASS')


if __name__=='__main__':main()
