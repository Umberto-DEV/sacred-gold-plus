"""Compile and install native training on the guarded 1.3 reserve expansion."""
from pathlib import Path
import hashlib
import importlib.util
import json
import re
import struct
import subprocess

ROOT=Path(__file__).resolve().parents[1]
BASE=0x023D0100
CONFIG=0x023D2F00
STATE=0x023D3000

def module(path,name):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def compile_native(directory):
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
    obj=directory/'training.o'
    flags=['--target=armv5te-none-eabi','-mcpu=arm946e-s','-mthumb','-Oz','-ffreestanding','-fno-builtin','-fno-stack-protector','-fno-jump-tables','-fno-unwind-tables','-fno-asynchronous-unwind-tables','-Wall','-Wextra','-Werror']
    subprocess.run(['clang',*flags,'-c',str(ROOT/'features/training-native/runtime.c'),'-o',str(obj)],check=True,capture_output=True)
    loader=module(ROOT/'features/options/tools/carica_text.py','training_loader')
    blob,symbols=loader.load_text(obj.read_bytes(),BASE,('training_script','training_save','training_phone'))
    if len(blob)>CONFIG-BASE:raise ValueError(f'training code overflow: {len(blob)} bytes')
    return blob,symbols

def entry_hook(site,target):
    """Eight bytes, all four argument registers intact, stack remains8-aligned."""
    from sgp12.rom import bl_thumb
    return b'\x10\xb5'+bl_thumb(site+2,target)+b'\x10\xbd'

def append_npc(member,script_id,x,z,sprite=324):
    nbg=struct.unpack_from('<I',member)[0];off=4+20*nbg
    count=struct.unpack_from('<I',member,off)[0];end=off+4+32*count
    if end+4>len(member):raise ValueError('event object bounds')
    objects=[struct.unpack_from('<14Hi',member,off+4+32*i) for i in range(count)]
    if any(o[12:14]==(x,z) for o in objects):raise ValueError('NPC destination occupied')
    ident=max([o[0] for o in objects],default=-1)+1
    if ident>=249:raise ValueError('NPC object id exhausted')
    npc=struct.pack('<14Hi',ident,sprite,0,0,0,script_id,1,0,0,0,0,0,x,z,0)
    result=member[:off]+struct.pack('<I',count+1)+member[off+4:end]+npc+member[end:]
    if result[off+4:end]!=member[off+4:end]:raise ValueError('old NPC data changed')
    return result

def cap_graphics(character,palette,gold=False):
    """Original 32x32 bottle-cap sprite inside a native build-time container."""
    if character[:4]!=b'RGCN' or len(character)!=560 or palette[:4]!=b'RLCN' or len(palette)!=552:raise ValueError('native item graphic container')
    pixels=[[0]*32 for _ in range(32)]
    for y in range(10,23):
        for x in range(7,25):
            if ((x-16)**2*2+(y-15)**2*5)<=170:
                pixels[y][x]=1 if y>=18 or x in (7,24) else 2
                if y>=18 and x%3==1:pixels[y][x]=3
    for y in range(11,16):
        for x in range(11,20):
            if (x-15)**2+(y-13)**2<=16:pixels[y][x]=3
    packed=bytearray()
    for ty in range(4):
        for tx in range(4):
            for y in range(8):
                for x in range(0,8,2):packed.append(pixels[ty*8+y][tx*8+x]|pixels[ty*8+y][tx*8+x+1]<<4)
    colors=(0,0x18C6,0x4E73,0x7FFF) if not gold else (0,0x08EA,0x16DB,0x3BDF)
    return character[:48]+packed,palette[:40]+struct.pack('<4H',*colors)+bytes(504)

def install(rom_path,output_path,language,charmap,work_dir):
    import ndspy.rom,ndspy.narc
    from sgp12.rom import Arm9,Rom,bl_thumb,bl_decode
    from sgp12.blz import blz_comprimi_ottimo
    from sgp13.resources import append_file
    from sgp13.training_scripts import service_script,append_script
    from sgp13 import consultant
    if language not in ('EN','IT'):raise ValueError('language')
    arm=Arm9(rom_path);guards=json.loads((ROOT/'features/training-native/native-guards.json').read_text())
    for address,digest in guards['arm'].items():
        if hashlib.sha256(arm.leggi(int(address,16),16)).hexdigest()!=digest:raise ValueError('training native ABI '+address)
    if arm.leggi(BASE,0x3F00)!=bytes(0x3F00):raise ValueError('training compartment occupied')
    old_load=arm.u32(0x02027AD8)
    if arm.leggi(0x02027AD4,4)!=b'\0K\x18G' or old_load!=0x023DCA99:raise ValueError('Bag load composition guard')
    if arm.u32(0x02027C1C)!=0x023DCACD:raise ValueError('Bag save composition guard')
    nr=ndspy.rom.NintendoDSRom(bytes(arm.raw));archives={};fids={}
    def archive(name):
        if name not in archives:fids[name]=nr.filenames.idOf(name);archives[name]=ndspy.narc.NARC(nr.files[fids[name]])
        return archives[name]
    text=module(ROOT/'translation/message_codec.py','training_messages');codec=module(ROOT/'features/options/tools/codifica_testo.py','training_encoder')
    table,_=codec.carica_charmap(charmap);words=lambda v:codec.codifica(v.replace("'",'’'),table)[:-1]
    def encode(value):
        # Native dialogue windows have two lines. 25BC clears on advance;
        # 25BD only scrolls one line and cannot delimit independent pages.
        pages=[]
        for page in value.split('\f'):
            lines=page.split('\n')
            pages.extend('\n'.join(lines[i:i+2]) for i in range(0,len(lines),2))
        value='\f'.join(pages)
        out=[]
        for token in re.split(r'(\{\d+\}|\n|\f)',value):
            if re.fullmatch(r'\{\d+\}',token):out.extend((0xFFFE,0x0100,1,int(token[1:-1])))
            elif token=='\n':out.append(0xE000)
            elif token=='\f':out.append(0x25BC)
            else:out.extend(words(token))
        return out+[65535]
    prose=json.loads((Path(__file__).with_name('data')/'training-text.json').read_text())[language]
    messages=archive('a/0/2/7');scripts=archive('a/0/1/2');events=archive('a/0/3/2')
    consultant_report=consultant.prepare(arm,archive(consultant.MODEL_ARCHIVE),events)
    receipts=[]
    for script_id,message_id,event_id,x,z in ((858,557,152,2,10),(942,630,263,2,10),(238,385,302,4,9)):
        for name,idx in [('a/0/1/2',script_id),('a/0/3/2',event_id)]:
            if hashlib.sha256(archive(name).files[idx]).hexdigest()!=guards['resources'][f'{name}:{idx}']:raise ValueError('training NPC preimage '+name)
        bank=text.Bank(messages.files[message_id]);before=[w[:]for w in bank.words];mapping={}
        for key,value in prose.items():mapping[key]=len(bank.words);bank.words.append(encode(value))
        if len(bank.words)>256:raise ValueError('NPC message byte index exhausted')
        scripts.files[script_id],entry=append_script(scripts.files[script_id],service_script(mapping,"daycare" if event_id==302 else "mart"))
        sprite=324 if event_id==302 else consultant.SPRITE_ID
        events.files[event_id]=append_npc(events.files[event_id],entry,x,z,sprite)
        messages.files[message_id]=bank.save()
        if text.Bank(messages.files[message_id]).words[:len(before)]!=before:raise ValueError('old messages changed')
        receipts.append(dict(script_member=script_id,message_member=message_id,event_member=event_id,entry=entry,x=x,z=z,sprite=sprite))
    for bankid,suffix in ((222,'name'),(221,'description')):
        bank=text.Bank(messages.files[bankid]);old=[w[:]for w in bank.words]
        for idx,color in ((113,'silver'),(114,'gold')):bank.words[idx]=encode(prose[f'cap_{color}_{suffix}'])
        messages.files[bankid]=bank.save()
        if any(a!=b for i,(a,b) in enumerate(zip(old,text.Bank(messages.files[bankid]).words)) if i not in (113,114)):raise ValueError('old item text changed')
    phone=text.Bank(messages.files[660]);phone_base=len(phone.words)
    for clock in range(2):
        for index in range(9):
            parts=[('Tempo reale (RTC).' if clock else 'Tempo di gioco.') if language=='IT' else ('Real-time course (RTC).' if clock else 'Playtime course.')]
            for slot,kind in enumerate((index%3,index//3)):
                if not kind:continue
                base=slot*5
                prefix=f'Posto {slot+1}: L.{{{base}}}' if language=='IT' else f'Slot {slot+1}: Lv.{{{base}}}'
                line=f'{{{base+1}}}: {{{base+2}}}/{{{base+3}}} EV' if kind==2 else ('Solo livelli.' if language=='IT' else 'Levels only.')
                remaining=(f'Corso: {{{base+4}}} s restanti.' if language=='IT' else f'Course: {{{base+4}}}s remaining.')
                parts.append(prefix+'\n'+line+'\f'+remaining)
            phone.words.append(encode('\f'.join(parts)+'\f')) # phone state needs a final player-advance wait
    if len(phone.words)>256:raise ValueError('phone message index overflow')
    messages.files[660]=phone.save()
    params=archive('a/0/1/7');icons=archive('a/0/1/8')
    if len(params.files)!=514 or any(len(p)!=34 for p in params.files):raise ValueError('item parameter layout')
    if arm.leggi(0x0210051C,16)!=bytes.fromhex('000019031a030000000019031a030000'):raise ValueError('reserved item IDs')
    cap_indices=[]
    for i in range(2):
        record=bytearray(34);struct.pack_into('<H',record,0,10000 if i==0 else 50000);params.files.append(bytes(record))
        char,pal=cap_graphics(icons.files[2],icons.files[3],bool(i));ci=len(icons.files);icons.files.extend((char,pal));cap_indices.append((ci,ci+1))
        arm.scrivi(0x0210051C+i*8,struct.pack('<4H',514+i,ci,ci+1,0))
    blob,symbols=compile_native(work_dir)
    payload=bytearray(0x2F00);payload[:len(blob)]=blob;struct.pack_into('<4I',payload,CONFIG-BASE,old_load,0x12C4,phone_base,language=='IT')
    struct.pack_into('<4H',payload,CONFIG-BASE+16,consultant.SPRITE_ID,consultant_report['member'],0,0)
    arm.scrivi(BASE,payload)
    hooks={0x02027AD4:'training_load',0x023DCC9C:'training_save',0x02078138:'training_items',0x02090A84:'training_ev_scalar',0x0208FD9C:'training_canuse',0x0206C078:'training_retrieve',0x0206C0E8:'training_growth'}
    for site,name in hooks.items():arm.scrivi(site,entry_hook(site,symbols[name]))
    if bl_decode(0x020183E0,arm.leggi(0x020183E0,4))!=0x0202CDBC:raise ValueError('native playtime call')
    arm.scrivi(0x020183E0,bl_thumb(0x020183E0,symbols['training_play']))
    if arm.u32(0x020FB4A8)!=0x0204EE21:raise ValueError('script490 original handler')
    arm.scrivi(0x020FB4A8,struct.pack('<I',symbols['training_script']))
    result=bytes(arm.raw)
    for name,arc in archives.items():
        encoded=arc.save();again=ndspy.narc.NARC(encoded)
        if again.files!=arc.files:raise ValueError('NARC readback '+name)
        result=append_file(result,fids[name],encoded)
    result=consultant.patch_overlay(result,symbols)
    for oid,site,name,size in ((12,0x022463E8,'training_battle',8),(101,0x021F3968,'training_phone',4)):
        view=Rom(result);v,_,original=view.immagine_overlay(oid);off=site-v['ram']
        if hashlib.sha256(original[off:off+16]).hexdigest()!=guards['overlays'][f'{oid}:{site:x}']:raise ValueError('overlay hook guard')
        patched=bytearray(original);patched[off:off+size]=entry_hook(site,symbols[name]) if size==8 else bl_thumb(site,symbols[name])
        compressed=blz_comprimi_ottimo(bytes(patched));compressed=compressed[0] if isinstance(compressed,tuple) else compressed
        result=bytearray(append_file(result,v['file_id'],compressed));struct.pack_into('<I',result,v['offset_voce']+28,(v['parola_comp']&0xff000000)|len(compressed))
        if Rom(result).immagine_overlay(oid)[2]!=patched:raise ValueError('overlay readback')
    Path(output_path).write_bytes(result)
    check=Arm9(output_path)
    if check.leggi(BASE,0x2F00)!=payload:raise ValueError('runtime readback')
    for site,name in hooks.items():
        if check.leggi(site,8)!=entry_hook(site,symbols[name]):raise ValueError('entry hook readback')
    report=dict(code_bytes=len(blob),symbols=symbols,npcs=receipts,consultant=consultant_report,phone_member=660,phone_first=phone_base,cap_icons=cap_indices,source_sha256=hashlib.sha256(Path(rom_path).read_bytes()).hexdigest(),output_sha256=hashlib.sha256(result).hexdigest())
    Path(work_dir,'training-report.json').write_text(json.dumps(report,indent=2))
    return report
