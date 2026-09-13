#!/usr/bin/env python3
"""Build the combined native Summary and New Game guide composition from exact Community1 Plus bases."""
import argparse
import json
from pathlib import Path
import re
import struct
import subprocess
from build_lease_rom import BASES, HERE, ROOT, abi, digest, build_r5, require, replace_arm9, append_files, load_text, NintendoDSRom

CODE=0x01FF8880
TEXT=0x01FF9B10
STATE=0x01FF9FC0
END=0x01FFA000
SOURCES=['combined_guide.c','newgame_host.c','build_combined_guide.py','NEW-GAME-CONTRACT.md','new-game-resources.json','summary_guide.c','guide_present.c','lease.c','build_summary_guide.py','guide-abi.json','presentation-text.json','lease-abi.json','summary_pressure_test.h','guide-source-evidence.json']


def encode_line(text,charmap):
    require(all(c in charmap for c in text),'Unmapped guide glyph')
    return struct.pack('<'+'H'*(len(text)+1),*[charmap[c] for c in text],0xFFFF)


def texts(lang,charmap,rom):
    from ndspy.narc import NARC
    meta=json.loads((HERE/'presentation-text.json').read_text())
    require(digest(charmap.read_bytes())==meta['font']['charmap_sha256'],'Charmap differs')
    font=NARC(rom.getFileByName('a/0/1/6')).files[0]
    require(digest(font)==meta['font']['sha256'],'Font0 differs')
    cmap={m[2]:int(m[1],16) for line in charmap.read_text().splitlines() if (m:=re.match(r'^([0-9A-F]{4})=(.)$',line))}
    widths=font[32592:32592+509]
    d=meta['languages'][lang]
    lines=[];bounds=[]
    for panel in d['panels']:
        lines+=[panel['title'],*panel['body']['lines']];bounds += [160,224,224,224]
    lines += d['panels'][2]['body_l_equals_a']['lines'];bounds += [224]*3
    lines += [d['labels'][k]['text'] for k in ['open','back','next','done','close','reopen']];bounds += [78,70,62,62,62,96]
    lines += ['1/3','2/3','3/3'];bounds += [24]*3
    data=bytearray(4*len(lines));records=[]
    for i,(line,bound) in enumerate(zip(lines,bounds)):
        encoded=encode_line(line,cmap)
        width=sum(widths[cmap[c]-1] for c in line)
        require(width<=bound,'Guide line overflows native Window')
        struct.pack_into('<H',data,2*i,len(data));struct.pack_into('<H',data,48+2*i,width);data.extend(encoded)
        records.append({'id':i,'text':line,'width_px':width,'max_px':bound})
    return bytes(data),records


def check_budget(payload,text):
    require(payload and CODE+len(payload)<=TEXT,'Code/text overlap')
    require(text and TEXT+len(text)<=STATE,'Text/state overlap')
    require(688+2*289*32+2048+72+4<=22528,'Modal heap budget overflow')
    require(688+2*20*32+40<=2048,'Badge heap budget overflow')


def guide_abi(static):
    evidence=json.loads((HERE/'guide-abi.json').read_text())
    for name,item in evidence.items():
        offset=item['address']-0x02000000
        require(digest(static[offset:offset+item['bytes']])==item['sha256'],'Guide ABI differs: '+name)
    return evidence


OAK_TEMPLATE=0x106068
OAK_ORIGINAL=(0x021E5901,0x021E5995,0x021E5B49,53)
OAK_SYMBOLS=['oak_guide_init','oak_guide_main','oak_guide_exit']


def verify_oak_template(static):
    require(struct.unpack_from('<4I',static,OAK_TEMPLATE)==OAK_ORIGINAL,'Oak template differs')


def patch_oak_template(static,symbols,payload_bytes):
    verify_oak_template(static)
    for name in OAK_SYMBOLS:
        value=symbols[name]
        require(value&1 and CODE<=(value&~1)<CODE+payload_bytes,'Oak hook outside payload')
    struct.pack_into('<3I',static,OAK_TEMPLATE,*[symbols[name] for name in OAK_SYMBOLS])


def oak_abi(rom):
    import hashlib
    meta=json.loads((HERE/'new-game-resources.json').read_text())
    static=rom.loadArm9().sections[0].data
    verify_oak_template(static)
    for item in meta['helpers']:
        address=item['address'];address=int(address,16) if isinstance(address,str) else address
        require(hashlib.sha256(static[address-0x02000000:address-0x02000000+item['bytes']]).hexdigest()==item['sha256'],'Oak ABI differs: '+item['name'])
    overlays=rom.loadArm9Overlays()
    for index in [36,53,74]:
        require(digest(overlays[index].data)==meta['roms']['en']['overlays'][str(index)]['decompressed_sha256'],'Oak overlay differs')
    return {'template':OAK_ORIGINAL,'resources_sha256':digest((HERE/'new-game-resources.json').read_bytes())}


def extend(main,payload,symbols,text):
    static,itcm,dtcm=main.sections
    verify_oak_template(static.data)
    require(static.data[0x88424:0x8842c]==bytes.fromhex('38b50c1c7ef732ff'),'Main prologue differs')
    require(static.data[0x8856c:0x88574]==bytes.fromhex('38b5051c7ef78efe'),'Exit prologue differs')
    require(itcm.ramAddress==0x01FF8000 and len(itcm.data)==0x880 and itcm.bssSize==0,'Wrong r5 ITCM')
    require(digest(itcm.data[0x620:0x870])=='6865177a8e819d603bbcfd3bce5c324566780dd01aa4d6793d052a17b57bc1c0','r5 payload differs')
    require(static.data[0x88b40:0x88b48]==struct.pack('<HHI',0x4b00,0x4718,0x01ff883d),'r5 input differs')
    require(static.data[0x8d178:0x8d180]==struct.pack('<HHI',0x4b00,0x4718,0x01ff881d),'r5 redraw differs')
    require(struct.unpack_from('<I',static.data,0xd2c68)[0]==CODE,'r5 arena differs')
    check_budget(payload,text);abi(static.data);evidence=guide_abi(static.data)
    for name in ['eviv_hook','guide_exit_hook',*OAK_SYMBOLS]:
        value=symbols[name];require(value&1 and CODE<=(value&~1)<CODE+len(payload),'Hook not in Thumb payload')
    for off,name in [(0x88424,'eviv_hook'),(0x8856c,'guide_exit_hook')]:
        static.data[off:off+8]=struct.pack('<HHI',0x4b00,0x4718,symbols[name])
    patch_oak_template(static.data,symbols,len(payload))
    struct.pack_into('<I',static.data,0xd2c68,END)
    itcm.data.extend(payload);itcm.data.extend(bytes(TEXT-itcm.ramAddress-len(itcm.data)))
    itcm.data.extend(text);itcm.data.extend(bytes(END-itcm.ramAddress-len(itcm.data)))
    return evidence


def build(source,charmap,out,pressure=False):
    require(not out.exists(),'Output directory must be new')
    require(out.resolve().is_relative_to(Path('/private/tmp')),'Private output required')
    original=source.read_bytes();base_sha=digest(original)
    require(base_sha in BASES,'Unknown complete Plus base')
    lang,r5_sha=BASES[base_sha]
    source_rom=NintendoDSRom(original)
    oak_evidence=oak_abi(source_rom)
    abi(source_rom.loadArm9().sections[0].data);guide_abi(source_rom.loadArm9().sections[0].data)
    text,lines=texts(lang,charmap,source_rom)
    r5=build_r5(source,charmap,out/'r5');require(r5['rom_sha256']==r5_sha,'r5 reconstruction differs')
    prior=NintendoDSRom((out/'r5'/r5['rom_file']).read_bytes());main=prior.loadArm9()
    before=[bytes(s.data) for s in main.sections]
    obj=out/'guide.o'
    command=['clang','--target=armv5te-none-eabi','-mcpu=arm946e-s','-mthumb','-Os','-ffreestanding','-fno-builtin','-fno-stack-protector','-fno-unwind-tables','-fno-asynchronous-unwind-tables','-fno-jump-tables','-Wall','-Wextra','-Werror','-c',str(HERE/'combined_guide.c'),'-o',str(obj)]
    if pressure:command.insert(1,'-DGUIDE_PRESSURE_TEST=1')
    result=subprocess.run(command,capture_output=True,text=True);(out/'compile.log').write_text(result.stdout+result.stderr)
    require(result.returncode==0,'Native guide compilation failed')
    payload,symbols=load_text(obj.read_bytes(),CODE);evidence=extend(main,payload,symbols,text)
    arm9=main.save(compress=True)
    image=replace_arm9(original,arm9)
    image,_=append_files(image,{'a/0/2/7':prior.getFileByName('a/0/2/7')},reuse_existing=True)
    checked=NintendoDSRom(image);actual=checked.loadArm9()
    expected=bytearray(main.sections[0].data);table=0x02000000+sum(len(s.data) for s in main.sections)
    struct.pack_into('<II',expected,0xba0,table,table+24);struct.pack_into('<I',expected,0xbb4,0x02000000+len(arm9))
    require(actual.sections[0].data==expected and [bytes(s.data) for s in actual.sections[1:]]==[bytes(s.data) for s in main.sections[1:]],'Roundtrip differs')
    require(bytes(actual.sections[1].data[:0x880])==before[1] and bytes(actual.sections[2].data)==before[2],'Historical TCM changed')
    allowed=set(range(OAK_TEMPLATE,OAK_TEMPLATE+12))|set(range(0x88424,0x8842c))|set(range(0x8856c,0x88574))|set(range(0xd2c68,0xd2c6c))|set(range(0xba0,0xba8))|set(range(0xbb4,0xbb8))
    require({i for i,(a,b) in enumerate(zip(before[0],actual.sections[0].data)) if a!=b}<=allowed,'Unexpected ARM9 mutation')
    require(checked.files==prior.files and checked.arm7==prior.arm7 and checked.arm9OverlayTable==prior.arm9OverlayTable and checked.arm7OverlayTable==prior.arm7OverlayTable,'Unselected ROM changed')
    target=out/f'Native Combined Guide TEST {lang.upper()}.nds';target.write_bytes(image)
    require(digest(source.read_bytes())==base_sha,'Base input changed')
    meta={'kind':'private-native-combined-guide','language':lang,'rom_file':target.name,'rom_sha256':digest(image),'base_sha256':base_sha,'r5_sha256':r5_sha,
          'source_sha256':{name:digest((HERE/name).read_bytes()) for name in SOURCES},'compile_command':command,'object_sha256':digest(obj.read_bytes()),'payload_sha256':digest(payload),'payload_bytes':len(payload),'symbols':symbols,
          'text_sha256':digest(text),'text_bytes':len(text),'text_lines':lines,'abi':evidence,'oak_abi':oak_evidence,'memory':{'code_start':CODE,'text_start':TEXT,'state_start':STATE,'arena_low':END,'badge_bytes':2048,'modal_bytes':22528,'modal_tiles':289},'r5_and_other_rom_content_preserved':True,'pressure_test_instrumentation':pressure}
    (out/'build.json').write_text(json.dumps(meta,indent=2,ensure_ascii=False)+'\n');return meta

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['rom','charmap','out']:p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--pressure',action='store_true')
    a=p.parse_args();print(json.dumps(build(a.rom.resolve(),a.charmap.resolve(),a.out.resolve(),a.pressure)))
