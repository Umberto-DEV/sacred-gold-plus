"""Native field Guide content compiler; consumes private game text at build time."""
from __future__ import annotations
import struct

TEXT_WIDTH = 208

HEADER = struct.Struct('<4sIHH')
CATEGORY = struct.Struct('<HHII')  # id,count,first entry,title
ENTRY = struct.Struct('<HHHHII') # id,category id,pages,reserved,title,page table

def build_content(categories, encode, measure):
    """Pack categories/entries/pages. encode(str)->u16 words including EOS;
    measure(str)->font0 pixel width. Empty categories are never published."""
    n = sum(len(c['entries']) for c in categories)
    if not 1 <= len(categories) <= 4 or not 1 <= n <= 4096:
        raise ValueError('category/entry count')
    out = bytearray(HEADER.size + CATEGORY.size*len(categories) + ENTRY.size*n)
    HEADER.pack_into(out,0,b'SGG1',0,len(categories),n)
    def string(s, limit):
        if '\n' in s or measure(s)>limit: raise ValueError('text width exceeds native window')
        words=list(encode(s))
        if not words or words[-1]!=65535 or 65535 in words[:-1] or len(words)>128:
            raise ValueError('encoded string bounds/EOS')
        off=len(out); out.extend(struct.pack('<%dH'%len(words),*words)); return off
    seen=set(); cats=set(); index=0
    for ci,c in enumerate(categories):
        if not c['entries'] or c['id'] in cats: raise ValueError('empty/duplicate category')
        cats.add(c['id'])
        co=HEADER.size+CATEGORY.size*ci
        CATEGORY.pack_into(out,co,c['id'],len(c['entries']),index,string(c['title'],208))
        for e in c['entries']:
            if e['id'] in seen: raise ValueError('duplicate entry ID')
            seen.add(e['id']); pages=e['pages']
            if not 1<=len(pages)<=255: raise ValueError('page count')
            title=string(e['title'],208)
            while len(out)%4: out.append(0)
            ptable=len(out); out.extend(bytes(4*len(pages)))
            eo=HEADER.size+CATEGORY.size*len(categories)+ENTRY.size*index
            ENTRY.pack_into(out,eo,e['id'],c['id'],len(pages),0,title,ptable)
            for pi,page in enumerate(pages):
                lines=page['lines'] if isinstance(page,dict) else page
                reference=page.get('reference',0) if isinstance(page,dict) else 0
                if not 1<=len(lines)<=7: raise ValueError('page lines outside 1..7')
                while len(out)%4: out.append(0)
                po=len(out); struct.pack_into('<I',out,ptable+pi*4,po)
                out.extend(struct.pack('<HH',len(lines),reference)+bytes(4*len(lines)))
                for li,line in enumerate(lines): struct.pack_into('<I',out,po+4+li*4,string(line,TEXT_WIDTH))
            index+=1
    struct.pack_into('<I',out,4,len(out)); validate_content(out)
    return bytes(out)

def validate_content(data):
    """Independent traversal; rejects malformed offsets before installing ROM data."""
    def need(ok):
        if not ok: raise ValueError('invalid Guide content')
    need(len(data)>=12)
    magic,size,nc,ne=struct.unpack_from('<4sIHH',data)
    need(magic==b'SGG1' and size==len(data) and 1<=nc<=4 and 1<=ne<=4096)
    end=12+nc*12+ne*16; need(end<=size)
    def string(off):
        need(end<=off<size and off%2==0)
        for i in range(128):
            need(off+2*i+2<=size)
            if struct.unpack_from('<H',data,off+2*i)[0]==65535:return
        need(False)
    ids=set(); cat_ids=set(); references=set(); total=0
    for i in range(nc):
        cid,count,first,title=struct.unpack_from('<HHII',data,12+i*12)
        need(cid not in cat_ids and count and first==total and first+count<=ne)
        cat_ids.add(cid); total+=count; string(title)
        for j in range(first,first+count):
            eid,ecid,np,res,title,pt=struct.unpack_from('<HHHHII',data,12+nc*12+j*16)
            need(eid not in ids and ecid==cid and 1<=np<=255 and not res)
            ids.add(eid); string(title); need(end<=pt and pt%4==0 and pt+np*4<=size)
            for p in range(np):
                po=struct.unpack_from('<I',data,pt+p*4)[0]
                need(end<=po and po%4==0 and po+4<=size)
                nl,ref=struct.unpack_from('<HH',data,po); need(1<=nl<=7 and po+4+nl*4<=size)
                if ref: references.add(ref)
                for line in range(nl): string(struct.unpack_from('<I',data,po+4+line*4)[0])
    need(total==ne and references<=ids)
    return dict(categories=nc,entries=ne,bytes=size)

# Native installer. Runtime addresses are owned by the 1.3 reserve map.
BASE=0x023D4000
CODE_LIMIT=0x2000
CONFIG_BASE=0x023D7B00
CONFIG_SIZE=0x400
GAP_BASE=BASE+CODE_LIMIT
GAP_SIZE=CONFIG_BASE-GAP_BASE
OWNED_RANGES=((BASE,CODE_LIMIT),(CONFIG_BASE,CONFIG_SIZE))
STATE=0x023D7E00
CANARY=b'SGP-GUIDE-CANARY'
OVERLAY27_SHA='2f7d803fb6ac52e3729a3f67d75f5788e6ff7da91fbc932042bb07e13b165344'

def compile_native(output_dir):
    import subprocess, importlib.util
    from pathlib import Path
    root=Path(__file__).resolve().parents[1]
    out=Path(output_dir);out.mkdir(parents=True,exist_ok=True)
    cmd=['clang','--target=armv5te-none-eabi','-mcpu=arm946e-s','-mthumb','-Oz','-ffreestanding','-fno-builtin','-fno-stack-protector','-fno-unwind-tables','-fno-asynchronous-unwind-tables','-fno-jump-tables','-Wall','-Werror','-c',str(root/'features/field-guide/sorgenti/guide.c'),'-o',str(out/'guide.o')]
    subprocess.run(cmd,check=True,capture_output=True)
    spec=importlib.util.spec_from_file_location('guide_text_loader',root/'features/options/tools/carica_text.py')
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    blob,symbols=mod.load_text((out/'guide.o').read_bytes(),BASE,('guide_init','guide_main','guide_exit'))
    if len(blob)>CODE_LIMIT:raise ValueError('Guide code compartment overflow')
    return blob,symbols

def install(rom_path,output_path,content,language,charmap,work_dir):
    """Install on expanded v2 reserve; preserve file IDs and existing NARC members.
    Private ROM/compiled payloads remain in caller-supplied work_dir/output_path."""
    from pathlib import Path
    import hashlib,sys,importlib.util,json
    import ndspy.rom,ndspy.narc
    from sgp12.rom import Arm9,Rom,bl_thumb,bl_decode
    from sgp12.blz import blz_comprimi_ottimo
    from sgp13.resources import append_file
    validate_content(content)
    if len(content)>0x20000:raise ValueError('Guide resource exceeds 128 KiB heap budget')
    if language not in ('EN','IT'):raise ValueError('language')
    arm=Arm9(rom_path);view=Rom(arm.raw);v,_,overlay=view.immagine_overlay(27)
    root=Path(__file__).resolve().parents[1]
    guards=json.loads((root/'features/field-guide/native-guards.json').read_text())
    for address,digest in guards.items():
        if address.startswith('0x') and hashlib.sha256(arm.leggi(int(address,16),16)).hexdigest()!=digest:
            raise ValueError('native ABI guard '+address)
    fv,_,field_overlay=view.immagine_overlay(1)
    for address,digest in guards['field_overlay_abi'].items():
        off=int(address,16)-fv['ram']
        if hashlib.sha256(field_overlay[off:off+16]).hexdigest()!=digest:raise ValueError('field ABI guard '+address)
    if hashlib.sha256(overlay).hexdigest()!=OVERLAY27_SHA:raise ValueError('overlay27 source guard')
    for address,size in OWNED_RANGES:
        if arm.leggi(address,size)!=bytes(size):raise ValueError('Guide owned range already occupied: '+hex(address))
    foreign_gap=arm.leggi(GAP_BASE,GAP_SIZE)
    if arm.leggi(0x0203bfe4,4)!=bytes.fromhex('00f04afa'):raise ValueError('StartMenu dispatch guard')
    blob,symbols=compile_native(work_dir)
    root=Path(__file__).resolve().parents[1]
    spec=importlib.util.spec_from_file_location('guide_codec',root/'features/options/tools/codifica_testo.py')
    codec=importlib.util.module_from_spec(spec);spec.loader.exec_module(codec)
    table,_=codec.carica_charmap(charmap)
    labels=(['Guide','B Back','A Open','L Page R','Choose a topic.','X Open reference','X Link','Page','Entry','L','R','L/R: 5 entries'] if language=='EN' else ['Guida','B Indietro','A Apri','L Pagina R','Scegli una voce.','X Apri rimando','X Info','Pagina','Voce','L','R','L/R: 5 voci'])
    text=bytearray(2*len(labels))
    for i,label in enumerate(labels):
        struct.pack_into('<H',text,i*2,len(text));words=codec.codifica(label,table);text.extend(struct.pack('<%dH'%len(words),*words))
    if len(text)>448:raise ValueError('Guide UI labels overflow')
    # Read-only ndspy indexing; never save/repack a ROM.
    nr=ndspy.rom.NintendoDSRom(bytes(arm.raw));fid=nr.filenames.idOf('a/0/2/7')
    # Pin the native field background, shared tile range and icon palettes.
    graphics=ndspy.narc.NARC(nr.getFileByName('a/0/1/4'))
    for member_id,digest in guards['field_resources'].items():
        if hashlib.sha256(graphics.files[int(member_id)]).hexdigest()!=digest:
            raise ValueError('field graphics guard '+member_id)
    archive=ndspy.narc.NARC(nr.files[fid]);old_members=list(archive.files);member=len(old_members);archive.files.append(content)
    narc=archive.save();again=ndspy.narc.NARC(narc)
    if again.files[:-1]!=old_members or again.files[-1]!=content:raise ValueError('NARC append readback')
    code=blob+bytes(CODE_LIMIT-len(blob));payload=bytearray(CONFIG_SIZE)
    struct.pack_into('<8I',payload,0,member,len(content),language=='IT',0,symbols['guide_init'],symbols['guide_main'],symbols['guide_exit'],0xffffffff)
    vo,_,opt=view.immagine_overlay(54)
    def optread(addr,n):return opt[addr-vo['ram']:addr-vo['ram']+n]
    # Native Options resource recipes: banks, modes and five BgTemplates.
    resource=optread(0x021e6cd8,40)+optread(0x021e6c48,16)+optread(0x021e6e20,140)
    if len(resource)!=196 or hashlib.sha256(resource).hexdigest()!=guards['options_resource']:raise ValueError('native Options resource guard')
    payload[0x40:0x40+196]=resource;payload[0x140:0x140+len(text)]=text
    payload[0x3f0:0x400]=CANARY
    arm.scrivi(BASE,code);arm.scrivi(CONFIG_BASE,payload);arm.scrivi(0x0203bfe4,bl_thumb(0x0203bfe4,symbols['guide_task_input']))
    patched=bytearray(overlay);hooks=[]
    for site,target,name in [(0x0225a0c6,0x0225bc84,'guide_field_create'),(0x0225a40e,0x0225b4d8,'guide_touch_input'),(0x0225a856,0x0225b4d8,'guide_touch_input'),(0x0225a860,0x0225b404,'guide_dpad')]:
        off=site-v['ram'];pre=bytes(patched[off:off+4])
        if bl_decode(site,pre)!=target:raise ValueError('overlay call guard '+hex(site))
        post=bl_thumb(site,symbols[name]);patched[off:off+4]=post;hooks.append((site,pre.hex(),post.hex()))
    off=0x0225a184-v['ram'];pre=struct.unpack_from('<I',patched,off)[0]
    if pre!=0x0225a321:raise ValueError('field callback guard')
    struct.pack_into('<I',patched,off,symbols['guide_field_frame'])
    compressed=blz_comprimi_ottimo(bytes(patched))
    # sgp12 compressor returns its bytes and diagnostic metadata.
    if isinstance(compressed,tuple):compressed=compressed[0]
    data=append_file(bytes(arm.raw),fid,narc)
    data=bytearray(append_file(data,v['file_id'],compressed))
    struct.pack_into('<I',data,v['offset_voce']+28,(v['parola_comp']&0xff000000)|len(compressed))
    Path(output_path).write_bytes(data)
    check=Arm9(output_path);cv,_,co=Rom(data).immagine_overlay(27)
    if Rom(data).file_bytes(fid)!=narc or co!=bytes(patched) or check.leggi(BASE,CODE_LIMIT)!=code or check.leggi(CONFIG_BASE,CONFIG_SIZE)!=payload:raise ValueError('installed Guide readback')
    if check.leggi(GAP_BASE,GAP_SIZE)!=foreign_gap:raise ValueError('foreign Teams/training gap changed')
    if bl_decode(0x0203bfe4,check.leggi(0x0203bfe4,4))!=(symbols['guide_task_input']&~1):raise ValueError('task hook readback')
    if check.leggi(0x023d7f00,256)!=arm.leggi(0x023d7f00,256):raise ValueError('reserve boundary changed')
    return dict(code_bytes=len(blob),owned_ranges=OWNED_RANGES,preserved_gap=(GAP_BASE,GAP_SIZE),content=validate_content(content),member=member,symbols=symbols,hooks=hooks,overlay_compressed=len(compressed),state=hex(STATE),canary=hex(STATE+240))
