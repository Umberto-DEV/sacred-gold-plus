#!/usr/bin/env python3
"""Read rematch consumer dependency lineage from exact retail/base/V4/r4 inputs."""
from pathlib import Path
import importlib.util,json,mmap,struct
s=importlib.util.spec_from_file_location('rematch_lineage_dependency',Path(__file__).with_name('attribuisci.py'));P=importlib.util.module_from_spec(s);s.loader.exec_module(P)
WINDOWS=((0x20735F8,12,'class_getter'),(0x201FD2C,12,'seed_getter'),(0x201FD38,12,'seed_setter'),(0x201FD44,36,'lcg'),(0x2073A98,76,'pid_override_window'),(0x20F2998,524,'signed_divider'),(0x206DE38,32,'create_mon_entry'),(0x23D6000,580,'strategy_code'),(0x23D6600,512,'strategy_config'),(0x23D8100,256,'plus_blob'),(0x23D8500,256,'trainer_level_table'))

def analyze(paths,language,*,firstmon=False,complete=False):
 windows_spec=WINDOWS
 if firstmon or complete:
  manifest=json.loads((Path(__file__).parents[1]/'test'/('complete-qualification.json' if complete else 'firstmon-qualification.json')).read_text());windows_spec=tuple((int(r['start'],16),int(r['end'],16)-int(r['start'],16),kind+':'+r['start']) for kind in ('code','data') for r in manifest[kind])
 current=P.G.S.SHARED.read_current(paths['r4'],language);records=[]
 for role in ('retail','base11','v4','r4'):
  model=current if role=='r4' else P.G.S.SHARED.read_image(paths[role],language,role);windows=[]
  for address,size,name in windows_spec:
   try:raw=P.G.piece(model['segments'],address,size)
   except ValueError:windows.append(dict(name=name,ram=hex(address),bytes=size,mapped=False));continue
   expected=P.G.piece(current['segments'],address,size);one=dict(name=name,ram=hex(address),bytes=size,mapped=True,sha256=P.sha(raw),same_as_r4=raw==expected)
   if firstmon or complete:one['different_byte_offsets']=[i for i,(x,y) in enumerate(zip(raw,expected)) if x!=y]
   if name in ('class_getter','seed_getter','seed_setter','lcg'):
    at={'class_getter':8,'seed_getter':8,'seed_setter':8,'lcg':24}[name];value=struct.unpack_from('<I',raw,at)[0];target=struct.unpack_from('<I',expected,at)[0];copy=bytearray(raw);copy[at:at+4]=expected[at:at+4]
    # Comparison only: the original mapped bytes are never changed/executed here.
    one['comparison_only_literal']=dict(offset=hex(at),value=hex(value),r4_value=hex(target),other_bytes_same=bytes(copy)==expected)
    if name=='class_getter':
     one['covered_table_entries']=list(P.G.piece(model['segments'],value+66,2));P.need(one['covered_table_entries']==[0,1],'native class entries differ')
   windows.append(one)
  get=struct.unpack('<I',P.G.piece(model['segments'],0x201FD34,4))[0];put=struct.unpack('<I',P.G.piece(model['segments'],0x201FD40,4))[0];rng=struct.unpack('<I',P.G.piece(model['segments'],0x201FD5C,4))[0]
  P.need(get==put==rng,'native seed literal bindings disagree within an input')
  records.append(dict(input=role,identity=model['record'],windows=windows,native_seed_state_ram=hex(get+4),seed_rom_offset=None))
 return dict(schema='rematch-complete-lineage-v1' if complete else 'rematch-firstmon-lineage-v1' if firstmon else 'rematch-consumer-lineage-v1',language=language,records=records,limits=['No execution or native MW rebuild; windows are byte comparisons,not inferred function extents','Only the named literal field is normalized in a temporary comparison copy; no general BSS/language relocation claim','An absent mapping is not zero padding; source and execution attribution remain in the consumer case'])


def main():
 import argparse
 parser=argparse.ArgumentParser(description=__doc__)
 for name in ('rom','v4','base','retail','json'):parser.add_argument('--'+name,type=Path,required=True)
 parser.add_argument('--language',choices=('EN','IT'),required=True);parser.add_argument('--firstmon',action='store_true',help='compare the196 sparse first-Pokemon code/data windows without normalization');parser.add_argument('--complete',action='store_true',help='compare231 sparse full-constructor code/data windows without normalization');a=parser.parse_args()
 try:
  P.need(not(a.firstmon and a.complete),'select only one sparse case')
  P.need(not a.json.exists() and not a.json.is_symlink(),'--json must be a fresh nonexistent file')
  P.need(P.SOURCE not in a.json.resolve().parents and a.json.resolve()!=P.SOURCE,'--json must be outside source')
  result=analyze(dict(r4=a.rom,v4=a.v4,base11=a.base,retail=a.retail),a.language,firstmon=a.firstmon,complete=a.complete)
  a.json.parent.mkdir(parents=True,exist_ok=True)
  with a.json.open('x') as f:json.dump(result,f,indent=2);f.write('\n')
 except ValueError as e:parser.exit(2,str(e)+'\n')
 print(a.language,'231 sparse complete-constructor windows' if a.complete else '196 sparse firstmon windows' if a.firstmon else 'eleven consumer dependency windows','across four exact inputs recorded; comparison only')


if __name__=='__main__':main()
