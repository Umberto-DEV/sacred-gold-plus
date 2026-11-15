#!/usr/bin/env python3
"""Read a finite trainer profile across exact retail/base/v4/r4 inputs, without CPU.

Reports hashes and locations only. Extracted retail members stay private.
"""
from pathlib import Path
import importlib.util,json,mmap,sys
s=importlib.util.spec_from_file_location('constructor_dependency',Path(__file__).with_name('attribuisci_costruttore.py'));T=importlib.util.module_from_spec(s);s.loader.exec_module(T)
P,need=T.P,T.need
CALLER_ADDRESS,CALLER_BYTES=0x20733C0,176
CALLER_SHA256='76912054c0a5f1183697cc83d7fa853fffd712b1620b9b6054e06314968e867b'


def native_caller(model,raw,language,role):
 """Read a known caller window,without inventing compressed physical offsets."""
 if language=='IT' and role=='retail':return dict(attributed=False,reason='retail IT caller symbol/address not qualified; EN alias not read')
 blob=P.G.piece(model['segments'],CALLER_ADDRESS,CALLER_BYTES);digest=P.sha(blob);location=None
 if role in ('v4','r4'):
  view=P.G.S.SHARED.gifts_audit.Arm9View(raw);need(view.read(CALLER_ADDRESS,CALLER_BYTES)==blob,'independent raw caller readback');location=hex(view.offset(CALLER_ADDRESS,CALLER_BYTES))
 return dict(attributed=digest==CALLER_SHA256,ram=hex(CALLER_ADDRESS),bytes=CALLER_BYTES,sha256=digest,equal_to_qualified_current=digest==CALLER_SHA256,rom_offset=location,mapping='decoded ARM9 sections; independent raw physical readback only for v4/r4',scope='complete known code/alignment/pool window identity; no runtime activation or original compiler reconstruction')


def party_layout(header,payload):
 """Classify source-declared record bytes separately from an unknown trailer."""
 strides={0:8,1:16,2:10,3:18};need(len(header)==20 and header[0] in strides and 1<=header[3]<=6,'bounded trainer format/count/header');stride=strides[header[0]];used=stride*header[3];need(used<=len(payload),'party shorter than declared records');tail=payload[used:]
 return dict(format=header[0],count=header[3],record_bytes=stride,declared_bytes=used,declared_sha256=P.sha(payload[:used]),trailing_bytes=len(tail),trailing_sha256=P.sha(tail) if tail else None,trailing_all_zero=all(x==0 for x in tail) if tail else None,alignment4_padding_candidate=bool(tail) and len(tail)<4 and all(x==0 for x in tail) and len(payload)==((used+3)&~3))


def analyze(paths,language,trainer,*,caller=False):
 need(type(caller)is bool,'caller lineage opt-in must be Boolean')
 profile=T.profile_for(trainer);rows=[]
 for role in ('retail','base11','v4','r4'):
  path=paths[role];model=P.G.S.SHARED.read_image(path,language,role);record={}
  with path.open('rb') as file,mmap.mmap(file.fileno(),0,access=mmap.ACCESS_READ) as raw:
   raw_members={}
   for narc in (55,56):
    files,receipt=P.RAW.raw_archive(raw,T.B.narc_path(narc));need(trainer<len(files),'missing trainer member');payload=bytes(files[trainer]);raw_members[narc]=payload;record[str(narc)]=dict(bytes=len(payload),sha256=P.sha(payload),rom_offset=hex(receipt['member_rom_offsets'][trainer]))
   record['56']['layout']=party_layout(raw_members[55],raw_members[56])
   # These Plus images use the EN native layout. Retail IT has another native
   # address map: never read its EN address as if it established that symbol.
   if role=='retail' and language=='IT':
    record['class_byte']=dict(attributed=False,reason='retail IT native symbol address not qualified here')
   else:
    need(P.G.piece(model['segments'],0x2073600,4)==bytes.fromhex('90fb0f02'),'class-table native pointer');address=0x20FFB90+profile['class_id'];payload=P.G.piece(model['segments'],address,1);need(payload==bytes([profile['gender_byte']]),'class flag differs from qualified profile');location=None
    if role in ('v4','r4'):
     view=P.G.S.SHARED.gifts_audit.Arm9View(raw);need(view.read(address,1)==payload,'raw/ndspy class readback');location=hex(view.offset(address,1))
    record['class_byte']=dict(attributed=True,ram=hex(address),rom_offset=location,sha256=P.sha(payload),value=payload[0],mapping='decoded ARM9 sections; raw physical crosscheck for v4/r4')
   if role=='r4':
    canonical=T.S.resources(raw,model)['records'][str(trainer)];need(record['56']['sha256']==canonical['spec']['source_sha256'],'current source preimage');need(bytes.fromhex(canonical['header'])[1]==profile['class_id'],'current header class')
   if caller:record['native_caller']=native_caller(model,raw,language,role)
  rows.append(dict(role=role,input=model['record'],resources=record))
 current=rows[-1]['resources'];comparisons={row['role']:{} for row in rows[:-1]}
 # Physical relocation is not a content difference.
 for row in rows[:-1]:
  for key in ('55','56'):comparisons[row['role']][key]=all(row['resources'][key][field]==current[key][field] for field in ('bytes','sha256'))
 if caller:
  for row in rows[:-1]:
   component=row['resources']['native_caller'];comparisons[row['role']]['native_caller']=component.get('equal_to_qualified_current')
 result=dict(schema='trainer-resource-lineage-v3' if caller else 'trainer-resource-lineage-v2',trainer=trainer,language=language,images=rows,content_equal_to_current=comparisons,compiler_invoked=False,cpu_executed=False,limits=['Exact header/party members and selected class flag only; not whole-ROM equivalence','Record strides correspond to native trainer structures; trailing bytes remain separately hashed; alignment4 is a candidate,not recovered authoring provenance','Retail IT native class symbol remains unattributed; no EN address alias','Physical offsets in compressed retail/base ARM9 are not invented; logical section mapping only','Project source/ELF reconstruction and constructor execution require the separate constructor verifier'])
 if caller:
  result['limits'][0]='Exact header/party members,selected class flag and opt-in caller176 window only; not whole-ROM equivalence'
  result['limits'].append('Opt-in caller176 identity is bounded to the qualified current hash; retail IT caller symbol remains unattributed; source/build reconstruction and runtime are separate')
 return result


def main():
 import argparse
 parser=argparse.ArgumentParser(description=__doc__)
 for key in ('rom','base','v4','retail','json'):parser.add_argument('--'+key,type=Path,required=True)
 parser.add_argument('--language',choices=('EN','IT'),required=True);parser.add_argument('--trainer',type=int,choices=tuple(T.PROFILES),default=21);parser.add_argument('--caller',action='store_true',help='add native caller176 lineage (schema v3); default output remains v2');args=parser.parse_args();paths=dict(retail=args.retail,base11=args.base,v4=args.v4,r4=args.rom)
 try:
  need(not args.json.exists() and not args.json.is_symlink(),'output must be fresh');need(P.SOURCE not in args.json.resolve().parents and args.json.resolve()!=P.SOURCE,'output must be outside source');need(all(path.is_file() for path in paths.values()),'history inputs must exist');result=analyze(paths,args.language,args.trainer,caller=True) if args.caller else analyze(paths,args.language,args.trainer);payload=(json.dumps(result,indent=2)+'\n').encode();need(len(payload)<=1024*1024,'history report budget');args.json.parent.mkdir(parents=True,exist_ok=True)
  with args.json.open('xb') as output:output.write(payload)
 except ValueError as error:parser.exit(2,str(error)+'\n')
 print(args.language,args.trainer,'exact resource lineage read back; no CPU execution')


if __name__=='__main__':main()
