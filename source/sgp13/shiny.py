"""Guarded resident shiny routing and field-search installation."""
from pathlib import Path
import importlib.util
import subprocess
ROOT=Path(__file__).resolve().parents[1]
BASES={'native':0x023C9100,'search':0x023CE900}
LIMITS={'native':8192,'search':4096}
def compile_native(directory,part='native'):
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
    obj=directory/('shiny-'+part+'.o')
    flags=['--target=armv5te-none-eabi','-mcpu=arm946e-s','-mthumb','-Oz','-std=c11','-ffreestanding','-fno-builtin','-fno-stack-protector','-fno-jump-tables','-fno-unwind-tables','-fno-asynchronous-unwind-tables','-Wall','-Wextra','-Werror']
    subprocess.run(['clang',*flags,'-c',str(ROOT/'features/shiny'/f'{part}.c'),'-o',str(obj)],check=True,capture_output=True)
    spec=importlib.util.spec_from_file_location('shiny_loader',ROOT/'features/options/tools/carica_text.py')
    loader=importlib.util.module_from_spec(spec);spec.loader.exec_module(loader)
    blob,symbols=loader.load_text(obj.read_bytes(),BASES[part])
    if len(blob)>LIMITS[part]:raise ValueError(f'shiny {part} compartment overflow: {len(blob)}')
    return blob,symbols

import hashlib
import json
import struct
import tempfile

HOOKS={
    'arm9':{0x02000CC8:'sgp_shiny_boot',0x0203DE80:'sgp_shiny_continue',0x0203DEA6:'sgp_shiny_newgame',
            0x0203DED6:'sgp_shiny_delete',0x0203EE4A:'sgp_shiny_options',0x02055276:'sgp_shiny_leave',0x0203E0D0:'sgp_shiny_control',
            0x0206E142:'sgp_shiny_create',0x0206E1E4:'sgp_shiny_create',0x02050C8E:'sgp_shiny_outcome',
            0x0205E05E:'sgp_shiny_step',0x0205104C:'sgp_shiny_static',
            0x02043E52:'sgp_shiny_script',0x02043EAE:'sgp_shiny_script'},
    'overlay2':{0x02247D96:'sgp_shiny_regular',0x0224735C:'sgp_shiny_scent_abort'},
    'overlay1':{0x021FC450:'sgp_shiny_scent_cleanup'},
}
PATCHES={'overlay2':{0x02247D9A:bytes.fromhex('c046')},'overlay1':{0x021FC454:bytes.fromhex('2ee0')}}
RESERVES=((0x023C8100,4096),(0x023C9100,8192),(0x023CB100,256),(0x023CB200,1536),(0x023CE900,4096))

def sha(data):return hashlib.sha256(data).hexdigest()

def configuration(language,training_symbols,legacy_ui_symbols,native_symbols,search_symbols,core_symbols):
    """Serialize the 152-byte ABI 2 capabilities and canonical species bitmap."""
    if language not in ('EN','IT'):raise ValueError('shiny language')
    def entry(table,name):
        value=table.get(name)
        if type(value) is not int or not value&1 or not 0x02000000<value<0x02400000:
            raise ValueError('missing/invalid shiny capability '+name)
        return value
    words=[0x594E4853,(152<<16)|2]
    words.extend(entry(native_symbols,'sgp_shiny_'+n) for n in ('snapshot','candidate','apply'))
    words.extend(entry(core_symbols,'sgp_shiny_'+n) for n in ('valid','denominator','select','complete','draw','transform'))
    words.extend(entry(training_symbols,'training_'+n) for n in ('shiny_access','shiny_bind','read'))
    words.extend(entry(search_symbols,'sgp_shiny_'+n) for n in ('capture','dispatch'))
    words.extend(entry(legacy_ui_symbols,n) for n in ('sgp_ui_frame','opz_apri','opz_chiudi','opz_disegna'))
    words.append(int(language=='IT'))
    changes=json.loads((ROOT/'sgp13/data/species-changes.json').read_text())['changes']
    species=[x['species'] for x in changes]
    if (not 1<=len(species)<=493 or any(type(n)is not int or not 1<=n<=493 for n in species)
            or len(set(species))!=len(species)):
        raise ValueError('shiny native stat refresh requires 1..493 distinct species IDs in 1..493')
    bitmap=bytearray(64)
    for n in species:bitmap[n>>3]|=1<<(n&7)
    return struct.pack('<21IHH',*words,len(species),0)+bytes(bitmap)

def _images(data,directory,name):
    from sgp12.rom import Arm9,Rom
    path=Path(directory)/(name+'.nds');path.write_bytes(data)
    arm=Arm9(path);rom=Rom(data)
    return arm,{f'overlay{i}':rom.immagine_overlay(i) for i in (1,2)}

def _read(arm,overlays,kind,address,length):
    if kind=='arm9':return arm.leggi(address,length)
    record,_,image=overlays[kind];offset=address-record['ram']
    if offset<0 or offset+length>len(image):raise ValueError('shiny overlay range')
    return bytes(image[offset:offset+length])

def _guard(arm,overlays,language):
    if language not in ('EN','IT'):raise ValueError('shiny language')
    guards=json.loads((ROOT/'features/shiny/native-guards.json').read_text())['languages'][language]
    for g in guards['ranges']:
        if sha(_read(arm,overlays,g['kind'],int(g['address'],16),g['length']))!=g['sha256']:
            raise ValueError('shiny native ABI preimage '+g['kind']+':'+g['address'])
    for key,expected in guards['sites'].items():
        kind,address=key.split(':');payload=bytes.fromhex(expected)
        if _read(arm,overlays,kind,int(address,16),len(payload))!=payload:raise ValueError('shiny hook preimage '+key)
    for address,length in RESERVES:
        if arm.leggi(address,length)!=bytes(length):raise ValueError('shiny compartment occupied '+hex(address))
    return guards

def _payloads(directory,language,training_symbols,legacy_ui_symbols):
    from sgp13.shiny_core import compile_native as compile_core
    core,cs=compile_core(directory);native,ns=compile_native(directory,'native');search,ss=compile_native(directory,'search')
    config=configuration(language,training_symbols,legacy_ui_symbols,ns,ss,cs)
    payloads={0x023C8100:core,0x023C9100:native,0x023CE900:search,0x023CB100:config,0x023CB200:bytes(1536)}
    return payloads,{**cs,**ns,**ss},config

def install(data,language,training_symbols,legacy_ui_symbols,work_dir):
    """Install after species and Plus UI; native routes and metadata fail closed."""
    from sgp12.rom import bl_thumb
    from sgp12.blz import blz_comprimi_ottimo,blz_decomprimi
    from sgp13.resources import append_file
    directory=Path(work_dir)/'shiny';directory.mkdir(parents=True,exist_ok=True)
    arm,overlays=_images(data,directory,'before');_guard(arm,overlays,language)
    payloads,symbols,config=_payloads(directory,language,training_symbols,legacy_ui_symbols)
    for address,payload in payloads.items():arm.scrivi(address,payload)
    for address,name in HOOKS['arm9'].items():arm.scrivi(address,bl_thumb(address,symbols[name]))
    result=bytes(arm.raw)
    for kind in ('overlay1','overlay2'):
        record,_,before=overlays[kind];image=bytearray(before)
        for address,name in HOOKS[kind].items():
            offset=address-record['ram'];image[offset:offset+4]=bl_thumb(address,symbols[name])
        for address,payload in PATCHES[kind].items():
            offset=address-record['ram'];image[offset:offset+len(payload)]=payload
        compressed=blz_comprimi_ottimo(bytes(image))
        if isinstance(compressed,tuple):compressed=compressed[0]
        if len(compressed)>len(image)+16 or len(compressed)>0xFFFFFF or blz_decomprimi(compressed)!=bytes(image):
            raise ValueError('shiny overlay compressed size/roundtrip')
        result=bytearray(append_file(result,record['file_id'],compressed))
        struct.pack_into('<I',result,record['offset_voce']+28,(record['parola_comp']&0xFF000000)|len(compressed))
        result=bytes(result)
    receipt=readback(data,result,language,training_symbols,legacy_ui_symbols,directory)
    receipt.update(symbols={k:v for k,v in symbols.items() if k.startswith('sgp_shiny_')},
                   training_symbols={k:training_symbols[k] for k in ('training_shiny_access','training_shiny_bind','training_read')},
                   legacy_ui_symbols=legacy_ui_symbols,config_hex=config.hex(),
                   input_sha256=sha(data),output_sha256=sha(result),
                   bytes={hex(a):len(p) for a,p in payloads.items()},
                   provenance='Guarded native audit; explicit owner capabilities; original constructors and native slot builders')
    return result,receipt

def readback(before,after,language,training_symbols,legacy_ui_symbols,work_dir):
    """Fresh-compile validation plus independent original-byte preservation."""
    from sgp12.rom import bl_decode
    import ndspy.codeCompression
    from sgp12.rom import crc16
    directory=Path(work_dir);directory.mkdir(parents=True,exist_ok=True)
    old,oldov=_images(before,directory,'readback-before');new,newov=_images(after,directory,'readback-after')
    _guard(old,oldov,language)
    payloads,symbols,config=_payloads(directory,language,training_symbols,legacy_ui_symbols)
    restored=bytearray(after[:len(before)])
    for address,length in RESERVES:
        p=payloads[address]
        if new.leggi(address,length)!=p+bytes(length-len(p)):raise ValueError('shiny payload readback '+hex(address))
        offset=old.off(address,length);restored[offset:offset+length]=before[offset:offset+length]
    for address,name in HOOKS['arm9'].items():
        if bl_decode(address,new.leggi(address,4))!=(symbols[name]&~1):raise ValueError('shiny ARM9 hook readback '+hex(address))
        offset=old.off(address,4);restored[offset:offset+4]=before[offset:offset+4]
    fat=struct.unpack_from('<I',after,0x48)[0]
    for kind in ('overlay1','overlay2'):
        record,_,old_image=oldov[kind];updated,_,new_image=newov[kind];image=bytearray(new_image)
        for k in ('id','ram','ram_size','bss_size','static_init_start','static_init_end','file_id','flag'):
            if record[k]!=updated[k]:raise ValueError('shiny overlay load identity '+kind)
        start,end=struct.unpack_from('<II',after,fat+record['file_id']*8)
        if start<len(before) or start%512 or not start<end<=len(after):raise ValueError('shiny overlay append bounds')
        if ndspy.codeCompression.decompress(after[start:end])!=bytes(image):raise ValueError('shiny independent overlay decode')
        if updated['parola_comp']&0xFFFFFF!=end-start:raise ValueError('shiny compressed metadata')
        for address,name in HOOKS[kind].items():
            offset=address-record['ram']
            if bl_decode(address,image[offset:offset+4])!=(symbols[name]&~1):raise ValueError('shiny overlay hook readback')
            image[offset:offset+4]=old_image[offset:offset+4]
        for address,payload in PATCHES[kind].items():
            offset=address-record['ram']
            if image[offset:offset+len(payload)]!=payload:raise ValueError('shiny abort branch readback')
            image[offset:offset+len(payload)]=old_image[offset:offset+len(payload)]
        if bytes(image)!=bytes(old_image):raise ValueError('shiny unowned overlay bytes changed')
        for offset,length in ((fat+record['file_id']*8,8),(record['offset_voce']+28,4)):
            restored[offset:offset+length]=before[offset:offset+length]
    if struct.unpack_from('<H',after,0x15E)[0]!=crc16(after[:0x15E]):raise ValueError('shiny header CRC')
    for offset,length in ((0x14,1),(0x80,4),(0x15E,2)):restored[offset:offset+length]=before[offset:offset+length]
    if bytes(restored)!=before:raise ValueError('shiny unowned cartridge bytes changed')
    return {'verified':True,'hooks':{k:{hex(a):v for a,v in sites.items()} for k,sites in HOOKS.items()},
            'runtime_bytes':1536,'config_bytes':len(config),'overlay_byte_preservation':True,'cartridge_byte_preservation':True}

def verify(data,language,receipt,work_dir):
    """Validate installed hooks/config/payloads after subsequent build stages."""
    from sgp12.rom import bl_decode
    directory=Path(work_dir);directory.mkdir(parents=True,exist_ok=True)
    arm,overlays=_images(data,directory,'verify')
    payloads,symbols,config=_payloads(directory,language,receipt['training_symbols'],receipt['legacy_ui_symbols'])
    for address,length in RESERVES:
        if arm.leggi(address,length)!=payloads[address]+bytes(length-len(payloads[address])):raise ValueError('shiny final payload '+hex(address))
    for kind,sites in HOOKS.items():
        for address,name in sites.items():
            if bl_decode(address,_read(arm,overlays,kind,address,4))!=(symbols[name]&~1):raise ValueError('shiny final hook '+hex(address))
    for kind,sites in PATCHES.items():
        for address,payload in sites.items():
            if _read(arm,overlays,kind,address,len(payload))!=payload:raise ValueError('shiny final branch '+hex(address))
    guards=json.loads((ROOT/'features/shiny/native-guards.json').read_text())['languages'][language]
    # Normalize only our independently checked hook bytes before rechecking
    # original native function hashes. Later build stages may not alter them.
    for g in guards['ranges']:
        start=int(g['address'],16);end=start+g['length']
        block=bytearray(_read(arm,overlays,g['kind'],start,g['length']))
        for key,expected in guards['sites'].items():
            kind,address=key.split(':');address=int(address,16);raw=bytes.fromhex(expected)
            if kind!=g['kind']:continue
            if address not in HOOKS.get(kind,{}) and address not in PATCHES.get(kind,{}):continue
            lo=max(start,address);hi=min(end,address+len(raw))
            if lo<hi:block[lo-start:hi-start]=raw[lo-address:hi-address]
        if sha(block)!=g['sha256']:raise ValueError('shiny final native ABI '+g['address'])
    return {'verified':True,'config_bytes':len(config),'hook_count':sum(map(len,HOOKS.values()))}
