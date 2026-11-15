"""Finite relative FindPath source oracle; explicit root and Send4 ID model.

The global is a declared initialized BSS fixture, not ROM bytes or a boot capture.
Native queue, command/error stores and completion remain outside the Send model.
"""
from pathlib import Path
import importlib.util,struct


def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


B=load('find_qualified_read_base',Path(__file__).with_name('fs_read_bench.py'))
need,sha=B.need,B.sha
need(sha(Path(B.__file__).read_bytes())=='cac4ca24793210c4dfa37bd91bef98dc737cbaa96b95757bc6b38af69448252a',
     'Find qualified register/IRQ-mode initialization helpers drift')
ENTRY,END,LITERAL,SEND,CURRENT=0x20D7FC0,0x20D8100,0x20D8100,0x20D7788,0x21E362C
TOP,DIR,FRAME,ID,PATH,ARC=0x23BEEC0,0x23BEDD0,0x23BEDA8,0x23BEE28,0x210F198,0x21E3654
BASE,SIZE,REGS=B.BASE,B.SIZE,B.REGS


def check_fixture(f):
    r=f['entry'];need(B.u32s(r),'Find full unsigned32 entry registers')
    need(r[:4]==[DIR,PATH,ID,0]and r[13:16]==[DIR,0x20D81AC,0x1F],
         'Find finite actual ARM caller input, file-result mode and no incoming flags')
    memory=bytes.fromhex(f['frame']);need(len(memory)==280,'Find exact frame280')
    need(f['path']=='a/0/1/1'and f['current_dir']==struct.pack('<3I',ARC,0,0).hex()and
         type(f['file_id'])is int and f['file_id']==140,'Find declared root12/relative path/FNT file140 scope')
    need(f['destination_before']==memory[ID-FRAME:ID-FRAME+8].hex(),
         'Find result pointer and frame preimage agree')
    return memory


def predict(f,send_value=1,clobber=False):
    memory=bytearray(check_fixture(f));r=list(f['entry']);flow=[];stores=[];reads=[];services=[]
    need(type(send_value)is int and send_value in(0,1,2)and type(clobber)is bool,'Find finite boundary policy')
    pc=ENTRY
    def at(address):
        nonlocal pc
        pc=address;flow.append(dict(pc=hex(pc),regs=list(r)))
    def read(address,n):
        if address==LITERAL:blob=struct.pack('<I',CURRENT)
        elif CURRENT<=address and address+n<=CURRENT+12:blob=bytes.fromhex(f['current_dir'])[address-CURRENT:address-CURRENT+n]
        elif PATH<=address and address+n<=PATH+8:blob=(f['path'].encode()+b'\0')[address-PATH:address-PATH+n]
        else:
            need(FRAME<=address and address+n<=FRAME+280,'Find source-owned stack load');blob=bytes(memory[address-FRAME:address-FRAME+n])
        reads.append(dict(pc=hex(pc),address=address,bytes=n,hex=blob.hex()));return int.from_bytes(blob,'little')
    def store(address,value):
        i=address-FRAME;need(0<=i and i+4<=280,'Find source-owned native word store')
        stores.append(dict(pc=hex(pc),address=address,bytes=4,before=bytes(memory[i:i+4]).hex(),value=value))
        struct.pack_into('<I',memory,i,value)
    def cmp(a,b):r[15]=B.cmp(a,b,r[15])

    at(ENTRY);r[13]-=28
    for j,index in enumerate((3,4,5,6,7,8,14)):store(r[13]+4*j,r[index])
    at(0x20D7FC4);r[13]-=12
    at(0x20D7FC8);r[7]=r[1]
    at(0x20D7FCC);r[1]=read(r[7],1)
    at(0x20D7FD0);r[8]=r[0]
    at(0x20D7FD4);r[6]=r[2]
    at(0x20D7FD8);cmp(r[1],47)
    at(0x20D7FDC);r[5]=r[3]
    at(0x20D7FE0);cmp(r[1],92)
    at(0x20D7FE4);need(not r[15]&(1<<30),'Find relative branch')
    at(0x20D800C);r[0]=read(LITERAL,4)
    at(0x20D8010);r[3]=r[13]
    at(0x20D8014)
    address=r[0];values=[read(address+4*j,4)for j in range(3)];r[:3]=values
    at(0x20D8018)
    for j,value in enumerate(r[:3]):store(r[3]+4*j,value)
    at(0x20D801C);r[4]=0
    for ordinal in(0,1):
        at(0x20D8020);r[0]=read(r[7]+r[4],1)
        at(0x20D8024);cmp(r[0],0)
        at(0x20D8028)
        if not r[15]&(1<<30):cmp(r[0],47)
        at(0x20D802C)
        if not r[15]&(1<<30):cmp(r[0],92)
        at(0x20D8030)
        if r[15]&(1<<30):
            need(ordinal==1,'Find exact two-character prefix scan');break
        at(0x20D8034);cmp(r[0],58)
        at(0x20D8038);need(not r[15]&(1<<30),'Find no archive-prefix branch')
        at(0x20D80A4);r[4]+=1
        at(0x20D80A8);cmp(r[4],3)
        at(0x20D80AC)
    at(0x20D80B0);r[1]=read(r[13],4)
    at(0x20D80B4);r[0]=r[13]
    at(0x20D80B8);store(r[8]+8,r[1])
    at(0x20D80BC);store(r[8]+60,r[7])
    at(0x20D80C0);r[3]=r[8]+48
    at(0x20D80C4)
    address=r[0];values=[read(address+4*j,4)for j in range(3)];r[:3]=values
    at(0x20D80C8)
    for j,value in enumerate(r[:3]):store(r[3]+4*j,value)
    at(0x20D80CC);cmp(r[5],0)
    at(0x20D80D0);r[0]=0
    at(0x20D80D4);store(r[8]+64,r[0])
    at(0x20D80D8);store(r[8]+68,r[6])
    at(0x20D80DC)
    at(0x20D80EC);r[0]=r[8]
    at(0x20D80F0);r[1]=4
    at(0x20D80F4);r[14]=0x20D80F8
    before=list(r);frame_before=memory.hex();a=ID-FRAME
    memory[a:a+8]=struct.pack('<2I',ARC,f['file_id'])
    r=B.boundary_regs(r,send_value,clobber)
    services.append(dict(pc=hex(SEND),entry=before,returned=list(r),frame_before=frame_before,
        frame_after=memory.hex(),result=send_value,command=4,destination=ID,
        delivered_hex=struct.pack('<2I',ARC,f['file_id']).hex(),model_scope='ID8 only; no native command/error/queue/completion effects'))
    at(0x20D80F8);r[13]+=12
    at(0x20D80FC)
    saved=[read(r[13]+4*j,4)for j in range(7)]
    r[3:9]=saved[:6];target=saved[-1];r[13]+=28
    need(target==f['entry'][14]and not target&1,'Find exact saved ARM return')
    need((len(flow),len(stores),len(reads))==(47,17,18),'Find finite native source transcript extents')
    return dict(flow=flow,stores=stores,reads=reads,services=services,returned=r,frame_after=memory.hex(),
                destination_after=struct.pack('<2I',ARC,f['file_id']).hex(),native_peak=40,stop=hex(target),
                unique_native_starts=42,steps=49)


def collect_conditional_capability():
    """Our own four ARM instructions distinguish skipped and executed CMPNE.

    Collector only; persist its result before calling require_conditional.
    No ROM code or game state participates in this CPU capability check.
    """
    from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM,UC_HOOK_CODE
    from unicorn.arm_const import UC_ARM_REG_CPSR
    rows=[]
    for character in(47,60):
        words=(0xE3A00000|character,0xE350002F,0x1350005C,0xE1A01001)
        code=struct.pack('<4I',*words);u=Uc(UC_ARCH_ARM,UC_MODE_ARM)
        need(u.ctl_get_cpu_model()==17,'Find conditional capability CPU17')
        u.mem_map(BASE,4096);u.mem_write(BASE,code);u.reg_write(UC_ARM_REG_CPSR,0x1F)
        initial=[0xA5000000+j for j in range(13)]+[BASE+2048,BASE+16,0x1F]
        for reg,value in zip(REGS[:-1],initial[:-1]):u.reg_write(reg,value)
        regs=lambda:[u.reg_read(reg)for reg in REGS];flow=[];fault=None
        def step(uc,pc,n,_):
            need(BASE<=pc<BASE+16 and (pc-BASE)%4==0 and n==4,'Find own-code capability exact four ARM starts')
            flow.append(dict(pc=hex(pc),regs=regs()))
        u.hook_add(UC_HOOK_CODE,step)
        try:u.emu_start(BASE,BASE+16,count=5,timeout=100000)
        except Exception as error:fault=dict(type=type(error).__name__,message=str(error))
        rows.append(dict(character=character,words=list(words),initial=initial,flow=flow,returned=regs(),fault=fault,
            before_memory_sha256=sha(code+bytes(4096-16)),after_memory_sha256=sha(bytes(u.mem_read(BASE,4096))),
            stopped_pc=u.reg_read(B.UC_ARM_REG_PC)))
        del u
    return rows


def require_conditional(rows):
    need([row['character']for row in rows]==[47,60],'Find conditional distinct skipped/executed grid')
    for row in rows:
        character=row['character'];words=[0xE3A00000|character,0xE350002F,0x1350005C,0xE1A01001]
        r=[0xA5000000+j for j in range(13)]+[BASE+2048,BASE+16,0x1F];expected=[]
        for j in range(4):
            expected.append(dict(pc=hex(BASE+4*j),regs=list(r)))
            if j==0:r[0]=character
            elif j==1:r[15]=B.cmp(character,47,r[15])
            elif j==2 and character!=47:r[15]=B.cmp(character,92,r[15])
        need(all(B.u32s(x['regs'])for x in row['flow'])and B.u32s(row['returned'])and
             row['words']==words and row['initial']==expected[0]['regs']and row['flow']==expected and
             row['returned']==r and row['fault']is None and row['stopped_pc']==BASE+16,
             'Find conditional full-register hook delivery and actual false/true effects')
        digest=sha(struct.pack('<4I',*words)+bytes(4096-16))
        need(row['before_memory_sha256']==row['after_memory_sha256']==digest,'Find own conditional probe writes no RAM')
    return True


def read_allowed(pc,address,n):
    return ((pc==0x20D7FCC and address==PATH and n==1)or
        (pc==0x20D800C and address==LITERAL and n==4)or
        (pc==0x20D8014 and address in(CURRENT,CURRENT+4,CURRENT+8)and n==4)or
        (pc==0x20D8020 and address in(PATH,PATH+1)and n==1)or
        (pc==0x20D80B0 and address==FRAME and n==4)or
        (pc==0x20D80C4 and address in(FRAME,FRAME+4,FRAME+8)and n==4)or
        (pc==0x20D80FC and DIR-28<=address<DIR and address%4==0 and n==4))


def write_allowed(pc,address,n):
    return n==4 and address%4==0 and ((pc==ENTRY and DIR-28<=address<DIR)or
        (pc==0x20D8018 and FRAME<=address<FRAME+12)or
        (pc==0x20D80B8 and address==DIR+8)or(pc==0x20D80BC and address==DIR+60)or
        (pc==0x20D80C8 and DIR+48<=address<DIR+60)or
        (pc==0x20D80D4 and address==DIR+64)or(pc==0x20D80D8 and address==DIR+68))


def initial_memory(f,body,fill):
    check_fixture(f)
    need(len(body)==324 and sha(body)=='baf1c233ca8efcaa3ca58e996fe2f01e437fad5753dca7bbe1e6e782dd9abcf8',
         'Find exact current body with data-only literal')
    need(type(fill)is int and fill in(0xA5,0x39),'Find finite isolated RAM preimage')
    memory=bytearray(bytes([fill])*SIZE)
    for address,blob in((ENTRY,body),(FRAME,bytes.fromhex(f['frame'])),(CURRENT,bytes.fromhex(f['current_dir'])),
                         (PATH,f['path'].encode()+b'\0')):
        memory[address-BASE:address-BASE+len(blob)]=blob
    return memory


def require_fnt(f,fnt):
    from ndspy.fnt import load as load_fnt
    check_fixture(f);need(type(fnt)is bytes and 0<len(fnt)<=1024**2,'Find bounded raw-FNT fixture')
    file_id=load_fnt(fnt).idOf(f['path'])
    need(type(file_id)is int and file_id==f['file_id'],'Find raw-FNT path must independently select ID140')
    return file_id


def run(f,body,fnt,send_value=1,clobber=False,observe=True,fill=0xA5):
    """Collect one isolated wrapper; source semantics are checked separately."""
    from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM,UC_HOOK_CODE,UC_HOOK_MEM_READ,UC_HOOK_MEM_WRITE
    from unicorn.arm_const import UC_ARM_REG_CPSR,UC_ARM_REG_PC
    from ndspy.fnt import load as load_fnt
    import unicorn
    need(unicorn.__version__=='2.1.4','Find qualified Unicorn hook policy')
    before=initial_memory(f,body,fill)
    need(type(fnt)is bytes and 0<len(fnt)<=1024**2 and type(send_value)is int and send_value in(0,1,2)and
         type(clobber)is type(observe)is bool,'Find finite FNT/policies')
    require_fnt(f,fnt);folders=load_fnt(fnt)
    u=Uc(UC_ARCH_ARM,UC_MODE_ARM);need(u.ctl_get_cpu_model()==17,'Find CPU17 instruction semantics')
    u.mem_map(BASE,SIZE);u.mem_write(BASE,bytes(before));u.reg_write(UC_ARM_REG_CPSR,f['entry'][15])
    for reg,value in zip(REGS[:-1],f['entry'][:-1]):u.reg_write(reg,value)
    regs=lambda:[u.reg_read(reg)for reg in REGS]
    entry=regs();flow=[];stores=[];reads=[];services=[];seen=set();steps=0;peak=0;returned=None;fault=None
    stop=f['entry'][14]

    def step(uc,pc,n,_):
        nonlocal steps,peak,returned
        steps+=1;need(steps<=100,'Find isolated instruction cap')
        if pc==stop:
            returned=regs();u.emu_stop();return
        if pc==SEND:
            native=regs();frame_before=bytes(u.mem_read(FRAME,280)).hex()
            need(native[0:2]==[DIR,4]and native[13:15]==[DIR-40,0x20D80F8]and not native[15]&32,
                 'Find actual native Send4 file/command/SP/LR/ISA')
            root=bytes(u.mem_read(DIR+48,12));path_pointer,directory,result=struct.unpack('<3I',bytes(u.mem_read(DIR+60,12)))
            arc=struct.unpack('<I',bytes(u.mem_read(DIR+8,4)))[0]
            need(root==bytes.fromhex(f['current_dir'])and path_pointer==PATH and directory==0 and result==ID and arc==ARC,
                 'Find actual native root/ARG/output pointer before modeled resolution')
            path=bytes(u.mem_read(path_pointer,8));need(path==b'a/0/1/1\0','Find model consumes the entire actual path')
            file_id=folders.idOf(path[:-1].decode('ascii'));need(file_id==f['file_id'],'Find actual ARG path resolves raw FNT ID')
            blob=struct.pack('<2I',arc,file_id);u.mem_write(result,blob)
            after=B.boundary_regs(native,send_value,clobber)
            for reg,value in zip(REGS,after):u.reg_write(reg,value)
            services.append(dict(pc=hex(SEND),entry=native,returned=regs(),frame_before=frame_before,
                frame_after=bytes(u.mem_read(FRAME,280)).hex(),result=send_value,command=4,destination=result,
                delivered_hex=blob.hex(),model_scope='ID8 only; no native command/error/queue/completion effects'))
            u.reg_write(UC_ARM_REG_PC,native[14]);return
        need(ENTRY<=pc<END and(pc-ENTRY)%4==0 and n==4 and not regs()[15]&32,
             'Find only admitted ARM starts, never literal/other branches')
        need(bytes(u.mem_read(pc,4))==body[pc-ENTRY:pc-ENTRY+4],'Find live code identity')
        seen.add(pc);peak=max(peak,DIR-regs()[13])
        if observe:flow.append(dict(pc=hex(pc),regs=regs()))

    def write(uc,access,address,n,value,_):
        pc=uc.reg_read(UC_ARM_REG_PC);need(write_allowed(pc,address,n),'Find native write owner/word width')
        if observe:stores.append(dict(pc=hex(pc),address=address,bytes=n,before=bytes(u.mem_read(address,n)).hex(),value=value))

    def read(uc,access,address,n,value,_):
        pc=uc.reg_read(UC_ARM_REG_PC);need(read_allowed(pc,address,n),'Find native read owner/width')
        if observe:reads.append(dict(pc=hex(pc),address=address,bytes=n,hex=bytes(u.mem_read(address,n)).hex()))

    u.hook_add(UC_HOOK_CODE,step);u.hook_add(UC_HOOK_MEM_WRITE,write);u.hook_add(UC_HOOK_MEM_READ,read)
    try:u.emu_start(ENTRY,BASE+SIZE,timeout=1000000,count=100)
    except Exception as error:fault=dict(type=type(error).__name__,message=str(error))
    halt=regs();after=bytes(u.mem_read(BASE,SIZE))
    result=dict(fixture=f,policy=dict(send=send_value,clobber=clobber),observe=observe,fill=fill,entry=entry,
        returned=returned,flow=flow,stores=stores,reads=reads,services=services,steps=steps,native_peak=peak,
        observed_pcs=sorted(seen),cpu_model=u.ctl_get_cpu_model(),fault=fault,halt_regs=halt,
        halt_pc=hex(u.reg_read(UC_ARM_REG_PC)),stop=hex(stop),frame_after=after[FRAME-BASE:FRAME-BASE+280].hex(),
        destination_after=after[ID-BASE:ID-BASE+8].hex(),before_whole_ram_sha256=sha(before),whole_ram_sha256=sha(after),
        current_dir_after=after[CURRENT-BASE:CURRENT-BASE+12].hex(),path_after=after[PATH-BASE:PATH-BASE+8].hex(),
        fnt_sha256=sha(fnt),fnt_model_path=f['path'],fnt_model_file_id=f['file_id'])
    del u;return result


def require_result(result,body,fnt):
    f=result['fixture'];p=result['policy'];require_fnt(f,fnt)
    need(type(p['send'])is int and p['send']in(0,1,2)and type(p['clobber'])is bool and
         type(result['observe'])is bool and type(result['steps'])is int,'Find strict result/policy types')
    expected=predict(f,p['send'],p['clobber'])
    need(result['fault']is None and result['halt_pc']==expected['stop']and result['halt_regs']==result['returned']and
         result['entry']==f['entry']and B.u32s(result['entry'])and result['cpu_model']==17 and B.u32s(result['returned'])and B.u32s(result['halt_regs']),
         'Find fault-free actual original ARM return and full register widths')
    for key in('returned','frame_after','destination_after','native_peak','stop','steps','services'):
        need(result[key]==expected[key],'Find source-derived '+key)
    for event in result['services']:
        need(B.u32s(event['entry'])and B.u32s(event['returned']),'Find actual Send full unsigned32 registers')
    need(result['observed_pcs']==sorted({int(x['pc'],16)for x in expected['flow']})and len(result['observed_pcs'])==42,
         'Find finite42 unique starts, all47 hooks including one false CMPNE')
    for key in('flow','stores','reads'):
        need(result[key]==(expected[key]if result['observe']else[]),'Find exact source '+key+' or OFF trace')
    need(all(B.u32s(x['regs'])for x in result['flow']),'Find actual hook full unsigned32 registers')
    memory=initial_memory(f,body,result['fill'])
    need(result['before_whole_ram_sha256']==sha(memory),'Find exact initialized whole4MiB input')
    memory[FRAME-BASE:FRAME-BASE+280]=bytes.fromhex(expected['frame_after'])
    need(result['whole_ram_sha256']==sha(memory),'Find exact reconstructed whole4MiB native/model delta')
    need(result['current_dir_after']==f['current_dir']and result['path_after']==(f['path'].encode()+b'\0').hex()and
         result['fnt_sha256']==sha(fnt)and result['fnt_model_path']==f['path']and result['fnt_model_file_id']==140,
         'Find source globals/path remain readonly; exact FNT provider identity')
    return True
