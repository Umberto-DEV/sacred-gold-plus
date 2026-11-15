#!/usr/bin/env python3
"""Exact final-ROM attribution of the installed, initially inert Summary legend."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import sys
import ndspy.rom
from unicorn import UC_HOOK_CODE,UC_HOOK_MEM_READ,UC_HOOK_MEM_WRITE
from unicorn.arm_const import UC_ARM_REG_CPSR

SOURCE=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(SOURCE))
from sgp131 import controls as C

BASE,SIZE,CAPACITY=0x023D4C10,484,512
IMAGE_SHA='59f08b81ac5a3d32a0925ae7cf98bd8e0af6ff886a41abb39f25b2f9f333cec2'


def sha(data):return hashlib.sha256(data).hexdigest()


def need(ok,why):
    if not ok:raise ValueError(why)


def inspect_cold_record(record):
    need(len(record)==32 and record==bytes(32),'initial record must be zero, including owner/window/enabled')


def derive(image,sites):
    result={}
    for site,name,native in C.SITES:
        address=C.hex_int(site);wrapper=C.decode_bl(address,sites[site])
        at=(wrapper&~1)-BASE
        need(wrapper&1 and 32<=at and at+20<=len(image),'wrapper target range')
        need(image[at:at+4]==C.WRAPPER_PROLOGUE,'wrapper prologue')
        callee=C.decode_bl((wrapper&~1)+4,image[at+4:at+8])
        need(BASE+32<=callee<BASE+len(image) and callee&1,'wrapper callee range')
        key='sgp_summary_controls_update' if name=='sgp_sc_redraw' else 'sgp_summary_controls_destroy'
        need(result.setdefault(name,wrapper)==wrapper and result.setdefault(key,callee)==callee,'wrapper disagreement')
    return result


def isolated(raw,symbols):
    path=SOURCE/'features/summary-controls/test/bench.py'
    spec=importlib.util.spec_from_file_location('summary_controls_final_bench',path)
    B=importlib.util.module_from_spec(spec);spec.loader.exec_module(B)
    machine=B.Bench(raw,payload=None,base=BASE)  # installed bytes, no replacement
    uc=machine.uc
    permitted={0x0201D8C8:'clear',0x0201D54C:'delete',0x0208D178:'draw',0x0208C4E0:'teardown'}
    calls=[]
    for address,name in permitted.items():
        def handler(args,sp,name=name):
            calls.append([name,*args]);return 0x76543210
        machine.stub(address,handler)
    cases=[]
    def invoke(name,address,arg,owner=0,window=0):
        uc.mem_write(BASE,bytes(32));machine.set_state(owner=owner,window=window)
        before=bytes(uc.mem_read(BASE,32));calls.clear()
        observed={'nonstack_writes':[],'state_reads':[],'instructions':0}
        def code(cpu,a,n,unused):
            need(BASE+32<=a<BASE+SIZE or a in permitted,'undeclared executed native boundary')
            observed['instructions']+=1
        def read(cpu,access,a,n,value,unused):
            if BASE<=a<BASE+32:observed['state_reads'].append([a-BASE,n])
        def write(cpu,access,a,n,value,unused):
            stack=B.STACK_TOP-0x100
            need(stack-128<=a and a+n<=stack or BASE<=a and a+n<=BASE+32,'unexpected installed-code write')
            if BASE<=a<BASE+32:observed['nonstack_writes'].append([a-BASE,n])
        hooks=[uc.hook_add(UC_HOOK_CODE,code),uc.hook_add(UC_HOOK_MEM_READ,read)]
        # Bench.call poisons the stack before execution; attach write observer afterwards.
        # Ignore its host mem_write initialization (Unicorn hooks observe guest writes only).
        hooks.append(uc.hook_add(UC_HOOK_MEM_WRITE,write))
        try:value,preserved=machine.call(address,arg,count=4000)
        finally:
            for hook in hooks:uc.hook_del(hook)
        need(preserved and uc.reg_read(UC_ARM_REG_CPSR)&32,'Thumb/callee-saved/SP/canary')
        need(not machine.log and not machine.allocs and not machine.frees and not machine.errors,'unexpected bench transport')
        state=list(machine.state());result=dict(case=name,result=value,state=state,calls=list(calls),
            stack_depth=machine.last_stack_bytes,**observed)
        if name in ('update-null','update-poison','destroy-zero','destroy-other'):
            need(not calls and bytes(uc.mem_read(BASE,32))==before and not observed['nonstack_writes'],'cold/off path effect')
        elif name=='destroy-matching-off':
            need([c[0] for c in calls]==['clear','delete'] and calls[0][1]==window
                 and calls[1][1:3]==[window,1] and state[0]==state[2]==0,'OFF ownership counterexample')
        else:
            expected='draw' if name=='redraw-cold' else 'teardown'
            need(len(calls)==1 and calls[0][0]==expected and calls[0][1]==arg
                 and value==0x76543210 and not observed['nonstack_writes'],'native forwarding')
        cases.append(result)
    update,destroy=symbols['sgp_summary_controls_update'],symbols['sgp_summary_controls_destroy']
    invoke('update-null',update,0);invoke('update-poison',update,1)
    invoke('destroy-zero',destroy,1)
    invoke('destroy-other',destroy,0x02390000,owner=0x02391000,window=0x02392000)
    invoke('destroy-matching-off',destroy,0x02390000,owner=0x02390000,window=0x02392000)
    invoke('redraw-cold',symbols['sgp_sc_redraw'],1)
    invoke('teardown-cold',symbols['sgp_sc_teardown'],1)
    return cases


def analyze(rom,language,charmap,work):
    pin=json.loads((SOURCE/'distribution/game-1.3.2-r4.json').read_text())['targets'][language]
    raw=Path(rom).read_bytes();need(len(raw)==pin['bytes'] and sha(raw)==pin['sha256'],'exact r4 identity')
    segments=C._arm9_segments(raw);main=ndspy.rom.NintendoDSRom(raw).loadArm9()
    ranges=[]
    def read(a,n):
        blob=C.read(raw,a,n,segments)
        found=[s for s in main.sections if s.ramAddress<=a and a+n<=s.ramAddress+len(s.data)]
        need(len(found)==1,'ndspy section ambiguity')
        s=found[0];need(blob==bytes(s.data[a-s.ramAddress:a-s.ramAddress+n]),'raw/ndspy disagreement')
        ranges.append(dict(ram=hex(a),rom_offset=hex(C.rom_offset(raw,a,n,segments)),bytes=n,sha256=sha(blob)))
        return blob
    slot=read(BASE,CAPACITY);image=slot[:SIZE]
    need(sha(image)==IMAGE_SHA and slot[SIZE:]==bytes(CAPACITY-SIZE),'image/slot tail')
    inspect_cold_record(image[:32])
    sites={site:read(C.hex_int(site),4) for site,name,native in C.SITES}
    symbols=derive(image,sites)
    abi=C.load_abi()
    # Normalize only the three already-derived BLs in small comparison windows.
    # CPU execution below always uses the actual final image, without normalization.
    for name,item in abi['spans'].items():
        a,n=C.hex_int(item['address']),item['bytes'];span=bytearray(read(a,n))
        for site,entry,native in C.SITES:
            offset=C.hex_int(site)-a
            if 0<=offset and offset+4<=n:span[offset:offset+4]=C.encode_bl(C.hex_int(site),native|1)
        need(sha(span)==item['sha256'],'normalized span '+name)
    for category in ('natives','tables','bg'):
        for name,item in abi[category].items():
            a=C.hex_int(item['address']);n=item.get('bytes',8*item.get('entries',0))
            if category=='bg':n=28
            need(sha(read(a,n))==item['sha256'],'native/data pin '+category+'.'+name)
    for name,item in abi['hooks'].items():
        need(read(C.hex_int(item['address']),8)==bytes.fromhex(item['bytes']),'viewer hook '+name)
    for name,item in abi['literals'].items():
        need(struct.unpack('<I',read(C.hex_int(item['address']),4))[0]==C.hex_int(item['value']),'viewer literal '+name)
    del main
    words=C._payload_words(image);magic=4*words.index(C.STRING_MAGIC,8)
    count,maxcount=struct.unpack_from('<HH',image,magic-4)
    need(count==maxcount==len(C.LEGEND['compact'])+1,'installed String count')
    codes=struct.unpack_from('<%dH'%count,image,magic+4)
    charmap_sha=C.check_charmap(charmap)
    need(list(codes)==C.encode_legend(language,charmap,'compact'),'legend encoding')
    work=Path(work);work.mkdir(parents=True,exist_ok=True)
    rebuilt,info=C.compile_payload(work,BASE,language,None,C.PROPOSAL,enabled=0,variant='compact',codes=codes)
    need(rebuilt==image and info['symbols']==symbols,'current source/recipe rebuild')
    (work/('manifesto-'+language+'.json')).write_text(json.dumps(info,indent=2)+'\n')
    # This is project code produced by this invocation, not an extracted ROM range.
    output=work/'rebuilt-controls.bin'
    if output.exists():need(output.read_bytes()==rebuilt,'existing reconstructed blob differs')
    else:output.write_bytes(rebuilt)
    return dict(language=language,rom_sha256=pin['sha256'],bytes=len(raw),ranges=ranges,
        symbols=symbols,reconstruction=info,charmap_sha256=charmap_sha,execution=isolated(raw,symbols),
        limits=['Initial record and exercised paths only; OFF alone does not prevent matching-owner destroy.',
                'Four native transports stubbed; no native window/render/callback lifetime execution.',
                'No gameplay, activation, geometry, save or performance acceptance.',
                'Raw mapping shares project layout validation; ndspy is separate.',
                'Native span normalization changes only comparison copies, never executed bytes.'])


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--rom',type=Path,required=True);ap.add_argument('--language',choices=('EN','IT'),required=True)
    ap.add_argument('--charmap',type=Path,required=True);ap.add_argument('--work',type=Path,required=True)
    ap.add_argument('--json',type=Path,required=True)
    a=ap.parse_args();report=analyze(a.rom,a.language,a.charmap,a.work)
    a.json.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(language=a.language,cases=len(report['execution']),status='PASS')))


if __name__=='__main__':main()
