"""Class B compiled planner + pinned EN/IT UIR1/native width/glyph data in RAM.
Not printer, pixel, native scene, timing or save-compatibility evidence.
"""
import os,json
from render_bench import *
import unittest
sys.path.insert(0,str(SOURCE))
from sgp131 import ui_copy,ui_resource,ui_resource_verify
from sgp131.test_ui_copy_rom import PINS,CHARMAP_SHA,WIDTHS_SHA,digest
from ndspy.narc import NARC
from ndspy.rom import NintendoDSRom

def fixture(language):
 path=os.environ.get('SGP131_BASE_'+language) or os.environ.get('SGP_UI_RESOURCE_'+language)
 charmap=os.environ.get('SGP131_UI_COPY_CHARMAP') or str(Path(os.environ.get('SGP_PRET_SOURCE','/missing'))/'charmap.txt')
 if not path or not Path(path).is_file() or not Path(charmap).is_file():
  message='missing canonical '+language+' ROM / external charmap for native render-plan data'
  if os.environ.get('SGP_UI_RENDER_REQUIRE_INPUTS')=='1':raise AssertionError(message)
  raise unittest.SkipTest(message)
 path=Path(path);charmap=Path(charmap)
 assert (digest(path),path.stat().st_size)==PINS[language]
 assert digest(charmap)==CHARMAP_SHA
 native=path.read_bytes();rom=NintendoDSRom(native)
 font=bytes(NARC(rom.getFileByName('a/0/1/6')).files[0])
 assert hashlib.sha256(font).hexdigest()=='9a17de3036f4aac8540163e560a60d83b7facde78d0ec41e688374fdbf669e73'
 widths=font[struct.unpack_from('<I',font,4)[0]:]
 assert len(widths)==509 and hashlib.sha256(widths).hexdigest()==WIDTHS_SHA
 spec=importlib.util.spec_from_file_location('render_native_codec',SOURCE/'features/options/tools/codifica_testo.py');codec=importlib.util.module_from_spec(spec);spec.loader.exec_module(codec)
 table,_=codec.carica_charmap(charmap)
 catalogue=ui_copy.load_catalogue((SOURCE/'sgp131/data/ui-copy.json').read_text())
 authored,geometry=ui_copy.encode_catalogue(catalogue,language,lambda t:codec.codifica(t,table),widths)
 replacement,receipt=ui_resource.compile_resource(native,authored)
 assert ui_resource_verify.verify_resource(native,replacement,authored)==receipt
 member=bytes(NARC(replacement).files[51]);count=struct.unpack_from('<I',member,100)[0]
 words={}
 for i in range(count):
  identity,n,offset=struct.unpack_from('<HHI',member,48448+8*i)
  words[identity]=struct.unpack_from('<%dH'%n,member,offset)
 assert digest(path)==PINS[language][0] and digest(charmap)==CHARMAP_SHA
 return words,widths,member,geometry,receipt
class NativeRenderTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.tmp=tempfile.TemporaryDirectory(prefix='settings-render-native-');cls.compiled=compile_render(Path(cls.tmp.name))
 @classmethod
 def tearDownClass(cls):cls.tmp.cleanup()
 def check_language(self,language):
  words,widths,member,geometry,receipt=fixture(language)
  b=RenderBench(self.compiled,(words,widths));b.u.mem_write(DATA,member)
  b.u.mem_write(CAT,struct.pack('<7I',DATA,len(member),48448,len(words),WIDTHS,509,7))
  plans=0;largest=0;pool_by_view={}
  def build():
   nonlocal plans,largest
   p=b.build();plans+=1;largest=max(largest,p.count);pool_by_view[p.view]=max(pool_by_view.get(p.view,0),p.pool_used);self.assertLessEqual(p.pool_used,256)
   for o in ops(p):
    self.assertLessEqual(o.x+o.w,240);self.assertLessEqual(o.y+o.h,176)
    if o.kind in (1,2,9) and o.y not in (4,20):
     self.assertGreaterEqual(o.y,36);self.assertLessEqual(o.y+o.h,156,'body stays outside context/footer')
    if o.kind==1:
     line=0
     for g in words[o.id][:-1]:
      if g==0xe000:self.assertLessEqual(line,o.w);line=0
      else:line+=widths[g-1]
     self.assertLessEqual(line,o.w)
   return p
  for mode,count in ((0,12),(1,14)):
   b.s.draft.shiny.mode=mode
   for row in range(count):
    b.s.row=row;p=build();self.assertEqual([o.row for o in ops(p,3)],[row])
  # Every six-slot viewport, every local64 disable pattern, both modes.
  # Flattening is explicitly authored here, independent of production helpers.
  for mode,count in ((0,12),(1,14)):
   b.s.draft.shiny.mode=mode
   flattened=[None,*range(6),None,*range(6,11),None,*range(11,count)]
   for first in range(len(flattened)-5):
    visible=[r for r in flattened[first:first+6] if r is not None]
    b.s.row=visible[0];b.put(REQ+28,first)
    for disabled in range(64):
     b.s.snapshot.editable_rows=16383
     for slot,row in enumerate(flattened[first:first+6]):
      if row is not None and disabled>>slot&1:b.s.snapshot.editable_rows &= ~(1<<row)
     p=build();self.assertEqual(p.first,first);self.assertLessEqual(p.count,48)
  self.assertEqual(largest,47)
  b.s.snapshot.editable_rows=16383;b.put(REQ+28,0)
  b.s.draft.shiny.mode=1
  for row,field,maxval in ((0,'text',2),(1,'scene',1),(2,'style',1),(3,'audio',1),(4,'button',1),(5,'frame',19)):
   b.s.row=row
   for value in range(maxval+1):setattr(b.s.draft.native,field,value);build()
  for row,field,maxval in ((6,'difficulty',1),(7,'wild',1),(8,'animation',1),(9,'npc',1),(10,'wifi',2)):
   b.s.row=row
   for value in range(maxval+1):setattr(b.s.draft.plus,field,value);build()
  b.s.row=12
  # Every493 species name is admitted with actual native widths, including
  # the longest spelling; this checks data, not their on-device pixels.
  longest=max(range(1,494),key=lambda sp:sum(widths[g-1] for g in words[4096+sp][:-1]))
  for species in (1,493,longest):b.s.draft.shiny.target=species;build()
  for sp in range(1,494):
   self.assertLessEqual(sum(widths[g-1] for g in words[4096+sp][:-1])+34+geometry['rows'][12]['label_px'],240)
  b.s.draft.shiny.target=493
  b.s.view=1
  for row,count in ((0,3),(5,20),(10,3),(12,3),(14,3)):
   b.s.selector_row=row
   for cursor in (0,count-1):
    b.s.selector_cursor=cursor;b.s.selector_pending=([0,25,493][cursor] if row==12 else [0,2,4][cursor] if row==14 else cursor)
    build()
  b.s.view=2
  for row in range(14):
   b.s.row=row
   for prefix in (0,0xffffffff) if row in (0,5) else (0,):
    b.put(REQ+36,prefix);build()
  # Geometry reference is the accepted native ring, not the plan's own width.
  # UiBgFrame{3,15,25,4} has absolute inner24,120,200,32, Window origin8,8.
  inner=(16,112,200,32)
  b.s.row=5
  for frame in (0,19):
   b.s.draft.native.frame=frame
   for prefix in (0,1,len(words[125])-2,0xffffffff):
    b.put(REQ+36,prefix);p=build();o=ops(p,9)[0]
    self.assertEqual((o.x,o.y,o.w,o.h),inner)
    self.assertEqual(ops(p,10)[0].choice,frame)
    glyphs=struct.unpack('<%dH'%o.units,bytes(b.u.mem_read(POOL+o.offset,o.units*2)))
    x,y=inner[:2]
    for glyph in glyphs[:-1]:
     if glyph==0xe000:x=inner[0];y+=16
     else:x+=widths[glyph-1]
     self.assertLessEqual(x,216);self.assertLessEqual(y+16,152)
    self.assertEqual(glyphs[-1],65535)
  b.s.row=0;p=build();o=ops(p,9)[0]
  self.assertEqual((o.x,o.y,o.w,o.h),(12,112,216,32));self.assertFalse(ops(p,10))
  b.s.view=3;b.s.row=13
  for notice in range(7):
   b.s.notice=notice;p=build()
   self.assertEqual(sorted(set(o.y for o in ops(p,1) if 32<=o.y<160)),[38,58,78,98,118,138])
  b.s.notice=0
  for view in (4,5):
   b.s.view=view;b.s.choice=2 if view==4 else 1
   for groups in range(8):
    for pending in (0,1):
     b.s.dirty_groups=groups;b.s.draft.shiny.search=pending;build()
  b.s.view=6
  for status in (0,2,6,7):b.s.owner_status=status;build()
  for name in ('UNAVAILABLE','EMPTY','METHOD','NO_TARGET','PRO','CHARGE'):
   entry=geometry['entries']['NOTICE_'+name]
   self.assertEqual(entry['role'],'context');self.assertEqual(len(entry['line_widths']),1);self.assertLessEqual(entry['line_widths'][0],200)
  print(json.dumps(dict(language=language,plans=plans,max_ops=largest,pool_by_view=pool_by_view,plan_bytes=C.sizeof(Plan),code_bytes=len(self.compiled[0]),max_instructions=max(x[1] for x in b.metrics),max_stack=max(x[2] for x in b.metrics),longest_species=longest,receipt=receipt,member_sha256=hashlib.sha256(member).hexdigest(),font_sha256=hashlib.sha256(widths).hexdigest(),inputs_unchanged=True,native_pixels=False),sort_keys=True))
 def test_english_native_catalogue_plans(self):self.check_language('EN')
 def test_italian_native_catalogue_plans(self):self.check_language('IT')
if __name__=='__main__':unittest.main()
