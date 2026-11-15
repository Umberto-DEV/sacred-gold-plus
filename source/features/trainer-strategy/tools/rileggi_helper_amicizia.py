#!/usr/bin/env python3
"""Read the exact50-byte friendship helper and eight caller BLs across four images.

No CPU, compiler, installer or ROM writes. Outputs contain identities/hashes,
not extracted code or assets. Compressed images use decoded section locations.
"""
from pathlib import Path
import importlib.util,json,mmap,gc
s=importlib.util.spec_from_file_location('friendship_helper_parent',Path(__file__).with_name('attribuisci_amicizia_chiamante.py'));H=importlib.util.module_from_spec(s);s.loader.exec_module(H)
P,need,sha=H.P,H.need,H.sha
from sgp131 import trainer_fixes as recipe

def component(model,raw,role):
 need(role in ('retail','base11','v4','r4'),'finite helper lineage role');need(sha(Path(recipe.__file__).read_bytes())==H.RECIPE_SHA256,'helper recipe source drift');expected=H.emit_postform() if role=='r4' else recipe.FORM_STATS_BEFORE;blob=P.G.piece(model['segments'],recipe.FORM_STATS_HELPER,50);need(blob==expected,'historical helper full50 differs from expected before/after recipe');rows=[]
 for sites,target in ((recipe.FORM_SETTERS,recipe.SET_MON_DATA),(recipe.FRIENDSHIP_CALLERS,recipe.FORM_STATS_HELPER)):
  for pc in sites:
   data=P.G.piece(model['segments'],pc,4);instructions=list(H.R.Cs(H.R.CS_ARCH_ARM,H.R.CS_MODE_THUMB).disasm(data,pc))
   # Capstone operand detail is disabled; independently decode its printed target.
   need(len(instructions)==1 and instructions[0].size==4 and instructions[0].mnemonic=='bl' and int(instructions[0].op_str.lstrip('#'),0)==target and recipe.bl_decode(pc,data)==target,'historical setter/helper actual BL target');rows.append(dict(ram=hex(pc),bytes=4,sha256=sha(data),target=hex(target)))
 offset=None
 if role in ('v4','r4'):
  view=P.G.S.SHARED.gifts_audit.Arm9View(raw);need(view.read(recipe.FORM_STATS_HELPER,50)==blob,'helper independent raw readback');offset=hex(view.offset(recipe.FORM_STATS_HELPER,50))
 return dict(helper=dict(ram=hex(recipe.FORM_STATS_HELPER),bytes=50,sha256=sha(blob),rom_offset=offset,recipe='after' if role=='r4' else 'before'),callers=rows,read_bytes=82,mapping='decoded ARM9 sections; direct physical readback only V4/r4',cpu_executed=False)

def analyze(paths,language):
 H.R.W.require_host_budget();rows=[]
 for role in ('retail','base11','v4','r4'):
  path=paths[role];model=P.G.S.SHARED.read_current(path,language) if role=='r4' else P.G.S.SHARED.read_image(path,language,role)
  with path.open('rb') as f,mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as raw:part=component(model,raw,role)
  rows.append(dict(role=role,input=model['record'],component=part));del model;gc.collect();H.R.W.require_host_budget()
 return dict(schema='friendship-helper-lineage-v1',language=language,images=rows,recipe_source_sha256=H.RECIPE_SHA256,tool_sha256=sha(Path(__file__).read_bytes()),verifier_sha256=sha(Path(H.__file__).read_bytes()),cpu_executed=False,compiler_invoked=False,limits=['Exact50-byte helper and eight4-byte BLs only; no whole-image equivalence','Retail/base physical locations not inferred from decoded or compressed ARM9','No native compiler reconstruction, historical activation, installer execution or game write'])

def main():
 import argparse
 parser=argparse.ArgumentParser(description=__doc__)
 for name in ('retail','base','v4','rom','json'):parser.add_argument('--'+name,type=Path,required=True)
 parser.add_argument('--language',choices=('EN','IT'),required=True);args=parser.parse_args()
 try:
  need(not args.json.exists() and not args.json.is_symlink() and P.SOURCE not in args.json.resolve().parents and args.json.resolve()!=P.SOURCE,'fresh private output outside source required');paths=dict(retail=args.retail,base11=args.base,v4=args.v4,r4=args.rom);need(all(p.is_file() for p in paths.values()),'four local exact inputs required');result=analyze(paths,args.language);payload=(json.dumps(result,indent=2)+'\n').encode();need(len(payload)<=1024**2,'helper lineage report budget');args.json.parent.mkdir(parents=True,exist_ok=True)
  with args.json.open('xb') as f:f.write(payload)
 except ValueError as e:parser.exit(2,str(e)+'\n')
 print(args.language,'full50-byte helper and eight BLs verified across four images; no CPU')
if __name__=='__main__':main()
