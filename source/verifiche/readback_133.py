#!/usr/bin/env python3
"""Check five candidate ROMs against r4; manifest paths are relative to the manifest.

Charmap and fresh JSON output paths are relative to the invocation directory.
This is a static readback, not a gameplay, save, device or timing test.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import stat
import struct
import zlib
from ndspy import _common, fnt
from ndspy.narc import NARC
from sgp131 import identity, ui_verify, ui_resource, mechanics_stages, onboarding_version as ONBOARDING, uturn_flinch as U, uturn_flinch_r4 as OLD

SOURCE=Path(__file__).resolve().parents[1]
ROOT=SOURCE.parent
TOOL=SOURCE/'features/type-consumers/tools/attribuisci_uturn.py'
spec=importlib.util.spec_from_file_location('five_native',TOOL)
A=importlib.util.module_from_spec(spec);spec.loader.exec_module(A)
sha=lambda b:hashlib.sha256(b).hexdigest()
CONTRACT_SHA='f26781f89b021cfc71bdc7199f2d4ee326eb3d3b1535d75fd50e023b6d261820'
CHARMAP_SHA='58861d34f40623fd2a9b29c10a79ee2ec872182285a288381759a3b251412ded'
LANGUAGES=('EN','IT','FR','ES','DE')

def need(ok,why):
    if not ok: raise ValueError(why)


def no_symlinks(path,allow_missing=False):
    path=Path(path)
    if not path.is_absolute():path=Path.cwd()/path
    current=Path(path.anchor)
    for part in path.parts[1:]:
        current=current/part
        try:mode=current.lstat().st_mode
        except FileNotFoundError:
            need(allow_missing,'missing path '+str(current));continue
        need(not stat.S_ISLNK(mode),'symlink path '+str(current))
    return Path(os.path.abspath(path))


class Input:
    def __init__(self,path):
        self.path=no_symlinks(path)
        st=self.path.stat();need(stat.S_ISREG(st.st_mode),'input must be a regular file')
        self.identity=(st.st_dev,st.st_ino);self.stamp=(st.st_size,st.st_mtime_ns)
    def check(self):
        no_symlinks(self.path);st=self.path.stat()
        need(stat.S_ISREG(st.st_mode) and (st.st_dev,st.st_ino)==self.identity and (st.st_size,st.st_mtime_ns)==self.stamp,'input changed '+str(self.path))
    def read(self,limit=None):
        self.check();need(limit is None or self.stamp[0]<=limit,'input exceeds size limit')
        with self.path.open('rb') as f:
            st=os.fstat(f.fileno());need((st.st_dev,st.st_ino)==self.identity,'input replaced')
            data=f.read() if limit is None else f.read(limit+1)
        need(limit is None or len(data)<=limit,'input exceeds size limit');self.check();return data


def pairs_unique(pairs):
    result={}
    for key,value in pairs:
        need(key not in result,'duplicate JSON key');result[key]=value
    return result


def load_json(ref,limit):
    return json.loads(ref.read(limit).decode('utf-8'),object_pairs_hook=pairs_unique)


def manifest_inputs(ref):
    data=load_json(ref,1024*1024)
    need(type(data) is dict and set(data)=={'schema','targets'} and data['schema']=='sgp-five-readback-inputs/1','manifest schema')
    targets=data['targets'];need(type(targets) is dict and set(targets)==set(LANGUAGES),'manifest languages')
    result={}
    for lang in LANGUAGES:
        item=targets[lang];need(type(item) is dict and set(item)=={'candidate','receipt','baseline'},'manifest target fields '+lang)
        need(all(type(v) is str and bool(v) and not v.isspace() and '\x00' not in v for v in item.values()),'manifest path value '+lang)
        result[lang]={k:Input(ref.path.parent/v) for k,v in item.items()}
    return result


def admit_output(path,inputs):
    path=no_symlinks(path,allow_missing=True)
    need(not path.exists() and not path.is_symlink(),'output must be fresh')
    need(path!=SOURCE and SOURCE not in path.parents,'output must be outside source')
    need(all(path!=ref.path for ref in inputs),'output aliases input')
    need(len({ref.identity for ref in inputs})==len(inputs),'input paths alias or hardlink')
    return path


def write_report(path,report):
    no_symlinks(path,allow_missing=True);path.parent.mkdir(parents=True,exist_ok=True)
    no_symlinks(path,allow_missing=True)
    flags=os.O_WRONLY|os.O_CREAT|os.O_EXCL|getattr(os,'O_NOFOLLOW',0)
    fd=os.open(path,flags,0o600)
    with os.fdopen(fd,'w',encoding='utf-8') as f:json.dump(report,f,indent=2);f.write('\n')


def read_receipt(ref,lang):
    data=load_json(ref,8*1024*1024)
    need(type(data) is dict and data.get('language')==lang and type(data.get('output_bytes')) is int and data['output_bytes']>0 and type(data.get('output_sha256')) is str and re.fullmatch('[0-9a-f]{64}',data['output_sha256']) is not None,'candidate receipt identity '+lang)
    need(type(data.get('schema')) is int and ((data['schema']==2 and data.get('through')=='identity') if lang in ('EN','IT') else data['schema']==1),'candidate receipt schema '+lang)
    return data


def authenticate_baseline(data,pin,lang):
    need((sha(data),len(data))==(pin['sha256'],pin['bytes']),'fallback identity '+lang)

def entries(member,lang):
    need(member[:4]==b'UIR2' and len(member)>=48448,'UIR header')
    directory,count,table,data,nbytes,fmt,entry,reserved=struct.unpack_from('<8I',member,96)
    need(directory==48448 and table==8*count and data==directory+table and fmt==1 and entry==8 and reserved==0 and data+nbytes<=len(member),'UIR directory')
    values={};cursor=data
    for i in range(count):
        key,n,off=struct.unpack_from('<HHI',member,directory+8*i)
        need(key not in values and n>0 and off==cursor and off+2*n<=data+nbytes,'UIR entry bounds')
        values[key]=struct.unpack_from('<%dH'%n,member,off);cursor+=2*n
    need(cursor==data+nbytes and member[cursor:]==bytes(len(member)-cursor),'UIR suffix')
    authored={k:v for k,v in values.items() if k<0x1000}
    species={k-0x1000:v for k,v in values.items() if k>=0x1000}
    widths=struct.unpack_from('<I',member,56)[0]
    need(ui_resource._pack_member(lang,member[128:48448],species,authored,widths)==member,'UIR complete canonical member')
    return authored,species,widths

def ui_delta(old,new,lang,words):
    a=NARC(old).files;b=NARC(new).files
    need(len(a)==len(b)==52 and a[:51]==b[:51],'UIR foreign members')
    before,species,widths=entries(bytes(a[51]),lang); after,species2,widths2=entries(bytes(b[51]),lang)
    need(species==species2 and widths==widths2 and before.get(2)==words[0] and after.get(2)==words[1], 'UIR version glyphs')
    need({k:v for k,v in before.items() if k!=2}=={k:v for k,v in after.items() if k!=2},'UIR foreign text')
    need(bytes(a[51])[128:48448]==bytes(b[51])[128:48448],'UIR assets')
    # Rebuild exact archive from its declared prefix; no unknown container edits.
    prefix=bytearray(old[:-len(a[51])]);need(len(prefix)==35380,'UIR prefix geometry')
    struct.pack_into('<I',prefix,8,len(prefix)+len(b[51]));struct.pack_into('<I',prefix,16+12+8*51+4,34912+len(b[51]))
    struct.pack_into('<I',prefix,len(prefix)-34912-4,34920+len(b[51]))
    need(bytes(prefix)+bytes(b[51])==new,'UIR archive container')
    receipt=ui_resource._receipt(new,lang,bytes(b[51])[128:48448],species2,after,widths2)
    return bytes.fromhex(receipt['config_hex'])

def verify_onboarding(before, after, old_canary, new_canary, lang, encode):
    need(lang in LANGUAGES and old_canary == new_canary and len(old_canary) == 16,
         'onboarding foreign canary')
    old_title = ONBOARDING.OLD_CORE_TITLE if lang in ('EN', 'IT') else ONBOARDING.OLD_REGIONAL_TITLE
    ONBOARDING.verify_transition(before, after, encode, old_title)
    return {'address': hex(ONBOARDING.ADDRESS), 'bytes': ONBOARDING.SIZE,
            'title_id': ONBOARDING.TITLE_ID, 'profile': 'onboarding-133-v1',
            'before_sha256': sha(before), 'after_sha256': sha(after)}

def check_targets(targets,contract,charmap,inputs):
    codec=U._module(SOURCE/'features/options/tools/codifica_testo.py','five_codec')
    charmap.check();table,_=codec.carica_charmap(charmap.path);charmap.check()
    words=tuple(tuple(codec.codifica(s,table)) for s in ('V1.3.2','V1.3.3'))
    rows=[];cross=[]
    for lang in ('EN','IT','FR','ES','DE'):
        refs=targets[lang];path=refs['candidate'].path;fallback=refs['baseline'].path
        record=read_receipt(refs['receipt'],lang); old=refs['baseline'].read();new=refs['candidate'].read()
        authenticate_baseline(old,contract[lang],lang)
        need(record['output_sha256']==sha(new) and record['output_bytes']==len(new),'candidate receipt '+lang)
        x,y=ui_verify.Image(old),ui_verify.Image(new)
        need(x.chunk(x.fnt,x.fnt_bytes)==y.chunk(y.fnt,y.fnt_bytes),'FNT/name IDs')
        names=fnt.load(x.chunk(x.fnt,x.fnt_bytes));titleid=names.idOf('a/0/4/6');need(titleid not in (None,167),'title file id')
        oldparts=identity.container.membri(old);newparts=identity.container.membri(new)
        off=oldparts[15][0]+848;newoff=newparts[15][0]+848
        need(len(oldparts[15][1])==len(newparts[15][1])==3136 and oldparts[17][1]==newparts[17][1] and new[newoff:newoff+384]==identity.pixels(),'title pixels and map')
        titleold=bytearray(x.file(titleid));titlenew=y.file(titleid);rel=off-x.files[titleid][0]
        need(0<=rel<=len(titleold)-384 and newoff-y.files[titleid][0]==rel,'title geometry')
        titleold[rel:rel+384]=identity.pixels();need(bytes(titleold)==titlenew,'title foreign bytes')
        uiconfig=ui_delta(x.file(167),y.file(167),lang,words)
        need(y.arm(0x023D7BC0,64)==uiconfig,'UIR descriptor')
        seeds=mechanics_stages.check_ui_seeds(new)
        need(x.arm(U.SLOT_START,64)==y.arm(U.SLOT_START,64) and sha(y.arm(U.SLOT_START,64))=='77844c84762bcdf84e64503a1e0996c871c8ca1027846b8059e5b5b86a8688ce','foreign64')
        need(sha(x.arm(U.HELPER_ADDRESS,68))==OLD.HELPER_SHA256 and x.arm(U.HELPER_ADDRESS+68,60)==bytes(60),'legacy helper')
        need(sha(y.arm(U.HELPER_ADDRESS,74))==U.HELPER_SHA256 and y.arm(U.HELPER_ADDRESS+74,54)==bytes(54),'candidate helper')
        need(x.overlay(12)==y.overlay(12),'parent/hooks/native overlay12 unchanged')
        need(A.take(y.overlay(12),U.FUNCTION,184)==U.FUNCTION_POSTIMAGE,'parent exact identity')
        model=dict(segments=[(a,y.chunk(o,n)) for a,o,n in y.mapped],overlay=y.overlay(12))
        refs['candidate'].check();resources=A.read_resources(path,model);refs['candidate'].check();oldmodel=dict(segments=[(a,x.chunk(o,n)) for a,o,n in x.mapped],overlay=x.overlay(12))
        refs['baseline'].check();original=A.read_resources(fallback,oldmodel);refs['baseline'].check()
        need(resources['script']==original['script'] and len(resources['script'])==800 and resources['cache']==original['cache'] and resources['move_cache']==original['move_cache'],'script/item/move resources')
        bench_closure=[]
        for address,n,digest,_ in A.WINDOWS:
            raw=A.take(model['overlay'],address,n) if address>=U.OVERLAY_BASE else A.G.piece(model['segments'],address,n)
            need(sha(raw)==digest,'native getter closure '+hex(address));bench_closure.append(sha(raw))
        need(sha(A.take(model['overlay'],A.G.RNG,44))==A.G.RNG_SHA and sha(A.G.piece(model['segments'],A.G.S.DIV,524))==A.G.S.DIV_SHA,'RNG/division native closure')
        cross.append((bench_closure,sha(resources['script']),sha(resources['cache']),sha(resources['move_cache'])))
        onboarding = verify_onboarding(x.arm(ONBOARDING.ADDRESS, ONBOARDING.SIZE),
                                       y.arm(ONBOARDING.ADDRESS, ONBOARDING.SIZE),
                                       x.arm(ONBOARDING.ADDRESS + ONBOARDING.SIZE, 16),
                                       y.arm(ONBOARDING.ADDRESS + ONBOARDING.SIZE, 16),
                                       lang, lambda value: codec.codifica(value, table))
        # Compare every mapped ARM9 byte with only exact owner spans masked.
        need([(a,n) for a,o,n in x.mapped]==[(a,n) for a,o,n in y.mapped],'ARM9 mapping')
        need(struct.unpack('<I',y.arm(0x023D7B60+80,4))[0]==len(new),'ROM limit descriptor')
        gx=struct.unpack('<16I',x.arm(0x023D7C00,64));gy=struct.unpack('<16I',y.arm(0x023D7C00,64))
        need(all(gx[i]==gy[i] for i in range(16) if i not in (5,6,7)),'Guide foreign descriptor')
        need(gy[5:8]==(*y.files[156],len(new)),'Guide extent descriptor')
        spans=((ONBOARDING.ADDRESS,ONBOARDING.SIZE),(U.HELPER_ADDRESS,128),(0x023D7B60+80,4),(0x023D7BC0,64),(0x023D7C00,64))
        for (addr,ao,n),(_,bo,_) in zip(x.mapped,y.mapped):
            left=bytearray(x.chunk(ao,n));right=bytearray(y.chunk(bo,n))
            for start,count in spans:
                if addr<=start and start+count<=addr+n:left[start-addr:start-addr+count]=right[start-addr:start-addr+count]
            need(left==right,'unknown ARM9 logical delta '+hex(addr))
        metadata=[]
        for i in range(129):
            need(x.records[i][:7]==y.records[i][:7] and x.records[i][7]>>24==y.records[i][7]>>24,'overlay metadata '+str(i))
            if y.records[i][7] & 0x01000000:
                need(y.records[i][7] & 0xFFFFFF == len(y.file(i)),'compressed overlay encoded size '+str(i))
            need(x.overlay(i)==y.overlay(i),'unknown decoded overlay '+str(i))
            if x.records[i][7]!=y.records[i][7] or x.file(i)!=y.file(i):metadata.append(i)
        for i in range(129,513):
            if i not in (titleid,167):need(x.file(i)==y.file(i),'unknown active file '+str(i))
        arm7off,_,arm7ram,arm7len=struct.unpack_from('<4I',old,0x30)
        n7off,_,n7ram,n7len=struct.unpack_from('<4I',new,0x30)
        need((arm7ram,arm7len)==(n7ram,n7len) and old[arm7off:arm7off+arm7len]==new[n7off:n7off+n7len],'ARM7 binary')
        # Header is exact except ROM size/CRC; capacity changes are not admitted.
        h=bytearray(new[:0x200]);h[0x80:0x84]=old[0x80:0x84];h[0x15e:0x160]=old[0x15e:0x160]
        need(bytes(h)==old[:0x200] and struct.unpack_from('<I',new,0x80)[0]==len(new) and struct.unpack_from('<H',new,0x15e)[0]==_common.crc16(new[:0x15e]),'header identity/size/CRC')
        rows.append(dict(onboarding=onboarding,language=lang,baseline_sha256=sha(old),candidate_sha256=sha(new),candidate_bytes=len(new),helper_sha256=U.HELPER_SHA256,parent_sha256=sha(A.take(y.overlay(12),U.FUNCTION,184)),script_sha256=sha(resources['script']),compression_changed_overlays=metadata,title_file_id=titleid,ui_seeds=seeds))
        del old,new,x,y,model,oldmodel
    need(all(v==cross[0] for v in cross[1:]),'five-target native closure/resources mismatch')
    for ref in inputs:ref.check()
    result=dict(schema='five-readback-133-v1',ok=True,targets=rows,limits=['Readback of active logical files and mapped ARM9; unindexed historical physical bytes and repacking gaps are not exhaustively compared.', 'Compression/FAT placement is reported separately from decoded owner data.', 'No gameplay, SAVE, cold restart, device, timing or complete-pivot proof.'])
    return result


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--manifest',type=Path,required=True);p.add_argument('--charmap',type=Path,required=True)
    group=p.add_mutually_exclusive_group(required=True);group.add_argument('--json',type=Path);group.add_argument('--output',type=Path)
    args=p.parse_args(argv);output=None
    try:
        manifest=Input(args.manifest);charmap=Input(args.charmap)
        targets=manifest_inputs(manifest)
        contract_ref=Input(SOURCE/'distribution/game-1.3.2-r4.json')
        inputs=[manifest,charmap,contract_ref]+[targets[lang][key] for lang in LANGUAGES for key in ('candidate','receipt','baseline')]
        output=admit_output(args.json or args.output,inputs)
        contract_bytes=contract_ref.read(1024*1024);need(sha(contract_bytes)==CONTRACT_SHA,'r4 contract identity')
        contract=json.loads(contract_bytes.decode('utf-8'),object_pairs_hook=pairs_unique)['targets']
        need(sha(charmap.read(1024*1024))==CHARMAP_SHA,'charmap identity')
        result=check_targets(targets,contract,charmap,inputs)
        result['provenance']=dict(manifest_sha256=sha(manifest.read(1024*1024)),charmap_sha256=CHARMAP_SHA,
                                  receipt_sha256={lang:sha(targets[lang]['receipt'].read(8*1024*1024)) for lang in LANGUAGES})
        write_report(output,result);print('five-target logical readback PASS');return 0
    except (ValueError,OSError,KeyError,TypeError,UnicodeError) as error:
        if output is not None:
            try:write_report(output,dict(schema='five-readback-133-v1',ok=False,error=str(error)))
            except OSError:pass
        print('readback FAIL: '+str(error),file=__import__('sys').stderr);return 1

if __name__=='__main__':raise SystemExit(main())
