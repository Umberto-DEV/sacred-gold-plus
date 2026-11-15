#!/usr/bin/env python3
"""Read custom-move310 provenance across exact retail/base/V4/r4 images, without CPU.

Outputs identities, offsets and hashes only. No extracted move record or code is
shipped. This is readback correspondence, not historical activation or MW rebuild.
"""
from pathlib import Path
import importlib.util,json,mmap,struct,gc
s=importlib.util.spec_from_file_location('pp_lineage_parent',Path(__file__).with_name('attribuisci_pp_chiamante.py'));H=importlib.util.module_from_spec(s);s.loader.exec_module(H)
P,need,sha=H.P,H.need,H.sha
CODE_ADDRESS,CODE_BYTES=0x2073314,172
CODE_SHA256='99de7e2671a8c7730c644f2164710140e845378654db6072a88c5ad004289026'

def component(model,raw,role):
 import ndspy.narc
 need(role in ('retail','base11','v4','r4'),'finite PP lineage role');code=P.G.piece(model['segments'],CODE_ADDRESS,CODE_BYTES);table=struct.unpack('<I',P.G.piece(model['segments'],0x2007520,4))[0];row=table+4*11;pointer=struct.unpack('<I',P.G.piece(model['segments'],row,4))[0];need(P.G.piece(model['segments'],pointer,8)==b'a/0/1/1\0','historical actual NARC11 route');members,receipt=P.RAW.raw_archive(raw,'a/0/1/1');need(310<len(members) and len(members[310])==16,'historical move310 member extent');fat=struct.unpack_from('<I',raw,0x48)[0];start,end=struct.unpack_from('<II',raw,fat+8*receipt['file_id']);archive=bytes(raw[start:end]);need(len(archive)<=2*1024**2 and ndspy.narc.NARC(archive).files[310]==members[310],'historical move raw/ndspy agreement');btaf=struct.unpack_from('<H',archive,12)[0];btnf=btaf+struct.unpack_from('<I',archive,btaf+4)[0];gmif=btnf+struct.unpack_from('<I',archive,btnf+4)[0];lo,hi=struct.unpack_from('<II',archive,btaf+12+8*310);position=gmif+8+lo;member=bytes(members[310]);need(hi-lo==16 and archive[position:position+16]==member and start+position==receipt['member_rom_offsets'][310],'historical PP manual NARC arithmetic');physical=None
 if role in ('v4','r4'):
  view=P.G.S.SHARED.gifts_audit.Arm9View(raw);need(view.read(CODE_ADDRESS,CODE_BYTES)==code,'PP native window independent raw/section readback');physical=hex(view.offset(CODE_ADDRESS,CODE_BYTES))
 return dict(native_window=dict(ram=hex(CODE_ADDRESS),bytes=CODE_BYTES,sha256=sha(code),equal_to_qualified_current=sha(code)==CODE_SHA256,rom_offset=physical,scope='whole code/data/padding window identity only; no additional instruction admission'),route=dict(table_ram=hex(table),row_ram=hex(row),path_ram=hex(pointer),path='a/0/1/1'),resource=dict(file_id=receipt['file_id'],archive_rom_offset=start,archive_bytes=len(archive),archive_sha256=sha(archive),members=len(members),member=310,member_bytes=16,member_sha256=sha(member),pp_offset=6,pp=member[6],member_archive_offset=position,member_rom_offset=start+position,btaf=btaf,btnf=btnf,gmif=gmif,start=lo,end=hi),cpu_executed=False)

def analyze(paths,language):
 H.R.W.require_host_budget();rows=[]
 for role in ('retail','base11','v4','r4'):
  path=paths[role];model=P.G.S.SHARED.read_current(path,language) if role=='r4' else P.G.S.SHARED.read_image(path,language,role)
  with path.open('rb') as f,mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as raw:part=component(model,raw,role)
  rows.append(dict(role=role,input=model['record'],component=part));del model;gc.collect();H.R.W.require_host_budget()
 current=rows[-1]['component'];need(current['native_window']['equal_to_qualified_current'] and current['resource']['member_sha256']=='85ac8d2ffc1e263ba41dfed64ea9b07613bd3fe76e8a68ef13e93394179dc5c8' and current['resource']['pp']==15,'current PP lineage baseline');comparisons={r['role']:dict(member_equal=r['component']['resource']['member_sha256']==current['resource']['member_sha256'],archive_equal=r['component']['resource']['archive_sha256']==current['resource']['archive_sha256'],native_window_equal=r['component']['native_window']['equal_to_qualified_current']) for r in rows[:-1]}
 return dict(schema='custom-pp310-lineage-v1',language=language,images=rows,equal_to_current=comparisons,tool_sha256=sha(Path(__file__).read_bytes()),verifier_sha256=sha(Path(H.__file__).read_bytes()),cpu_executed=False,compiler_invoked=False,limits=['Only move310 member/PP and qualified-address172B native window; whole archives separately identified','A differing historical code window remains an unattributed correspondence; no forced address alias','No original MW binary reconstruction, historical activation or whole-image equivalence','Compressed/autoload physical code offsets are not inferred; direct readback only V4/r4'])

def main():
 import argparse
 parser=argparse.ArgumentParser(description=__doc__)
 for name in ('retail','base','v4','rom','json'):parser.add_argument('--'+name,type=Path,required=True)
 parser.add_argument('--language',choices=('EN','IT'),required=True);args=parser.parse_args()
 try:
  need(not args.json.exists() and not args.json.is_symlink() and P.SOURCE not in args.json.resolve().parents and args.json.resolve()!=P.SOURCE,'fresh private output outside source required');paths=dict(retail=args.retail,base11=args.base,v4=args.v4,r4=args.rom);need(all(p.is_file() for p in paths.values()),'four local exact inputs required');result=analyze(paths,args.language);payload=(json.dumps(result,indent=2)+'\n').encode();need(len(payload)<=1024**2,'PP lineage report budget');args.json.parent.mkdir(parents=True,exist_ok=True)
  with args.json.open('xb') as f:f.write(payload)
 except ValueError as e:parser.exit(2,str(e)+'\n')
 print(args.language,'move310 provider/native-window lineage read without CPU')
if __name__=='__main__':main()
