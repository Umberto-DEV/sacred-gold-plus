import unittest
from guide_bench import *
class CatalogueTests(unittest.TestCase):
 def test_nine_append_labels_preserve_original_copy(self):
  obj=json.loads((SOURCE/'sgp131/data/ui-copy.json').read_text())
  self.assertEqual(len(obj['entries']),144)
  self.assertEqual([e['name'] for e in obj['entries'][133:]],['GUIDE_'+s for s in ('TITLE','OPEN','BACK','UP','DOWN','PREVIOUS','NEXT','LINK','CLOSE','SELECT','PAGING')])
  self.assertEqual(hashlib.sha256(json.dumps(obj['entries'][:133],sort_keys=True,ensure_ascii=False).encode()).hexdigest(),'07c4894f22a2a0082429c185b2dda5704644160ec8717cb0d3d1af02d8d238aa')
 def test_exact_context_labels_follow_approved_bilingual_copy(self):
  entries={e['name']:e['text'] for e in json.loads((SOURCE/'sgp131/data/ui-copy.json').read_text())['entries']}
  for key,en,it in (('OPEN','Open','Apri'),('BACK','Back','Indietro'),('PREVIOUS','Previous','Prec.'),('NEXT','Next','Succ.'),('LINK','Link','Vedi'),('CLOSE','Close','Esci'),('SELECT','Select','Scelta'),('PAGING','Page','Pagina')):
   self.assertEqual(entries['GUIDE_'+key],{'EN':en,'IT':it})
class RenderTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.tmp=tempfile.TemporaryDirectory(prefix='guide-render-');cls.compiled,cls.detail=compile_ui(Path(cls.tmp.name),'render')
 @classmethod
 def tearDownClass(cls):cls.tmp.cleanup()
 def test_upper_rail_has_four_complete_context_slots_and_no_lower_ops(self):
  b=RenderBench(self.compiled)
  for depth in range(3):
   p=b.build();ops=list(p.ops[:p.count])
   self.assertLessEqual(p.count,32);self.assertLessEqual(p.pool_used,1024)
   self.assertTrue(all(o.screen==0 for o in ops))
   self.assertFalse(any(o.kind==3 for o in ops))
   labels=[o for o in ops if o.kind==4 and o.y>=144]
   self.assertEqual([(o.x,o.y) for o in labels],[(36,144),(148,144),(36,160),(148,160)])
   self.assertTrue(all(o.w<=84 and o.h==16 for o in labels))
   keys=[o for o in ops if o.kind==1 and o.y>=144]
   self.assertEqual([(o.x,o.y) for o in keys],[(8,144),(120,144),(8,160),(120,160)])
   self.assertTrue(all(o.w<=24 for o in keys))
   if depth==0:self.assertTrue(labels[1].flags&4)
   if depth==2:self.assertTrue(labels[0].flags&4)
   b.action(1)
 def test_seven_detail_lines_and_five_twenty_pixel_rows(self):
  b=RenderBench(self.compiled);b.action(1);p=b.build()
  self.assertEqual([o.y for o in p.ops[:p.count] if o.kind==1 and 32<=o.y<144],[40,60,80,100,120])
  band=[o for o in p.ops[:p.count] if o.kind==2][0]
  self.assertEqual((band.y,band.h),(36,20))
  b.action(1);p=b.build()
  self.assertEqual([o.y for o in p.ops[:p.count] if o.kind==1 and 32<=o.y<144],[32,48,64,80,96,112,128])
 def test_retained_cursor_masks_and_old_pool_never_dereferenced(self):
  b=RenderBench(self.compiled);b.action(1);a=b.build();b.action(128);p=b.build()
  upper,lower,full=b.dirty(a,p);self.assertFalse(full);self.assertNotEqual(upper,0);self.assertEqual(lower,0)
  b.u.mem_write(POOL,b'\xfa'*1024);self.assertEqual(b.dirty(a,p),(upper,lower,full))
  b.action(1);q=b.build();self.assertEqual(b.dirty(p,q),(0x3fffff,0,1))
 def test_bad_font_width_refuses_without_output_or_pool_write(self):
  b=RenderBench(self.compiled);b.build();b.u.mem_write(WIDTHS,bytes(509));b.build(expect=0)
 def test_complete_extended_settings_catalogue_boundary(self):
  # Real Settings planner accepts appended637 entries;638 refuses.
  import render_bench as sr
  words,widths=sr.synthetic()
  words.update({i:(1,65535) for i in range(134,145)})
  with tempfile.TemporaryDirectory() as d: compiled=sr.compile_render(Path(d))
  b=sr.RenderBench(compiled,(words,widths));b.build()
  b.put(sr.CAT+12,638);b.build(expect=0)
 def test_two_title_runs_preserve_every_glyph_and_overflow_is_atomic(self):
  # Literal widths distinguish a useful word split from an early space whose
  # suffix is too wide. Keeping that early split would refuse valid208px text.
  encode=lambda text:[ord(c)%400+1 for c in text]+[65535]
  for text,widths in (('A'*52,[160,48]),('A '+'A'*50,[160,48]),('A'*25+' '+'A'*26,[104,104])):
   with self.subTest(title=text):
    data=gb.guide_content.build_content([dict(id=4,title='A',entries=[dict(id=1,title=text,pages=[dict(lines=['B'],reference=0)])])],encode,lambda t:len(t)*4)
    b=RenderBench(self.compiled,data);b.action(1);b.action(1);p=b.build()
    title=[o for o in p.ops[:p.count] if o.screen==0 and o.x==8 and o.y<32]
    self.assertEqual([o.y for o in title],[0,16]);self.assertEqual([o.w for o in title],widths)
    glyphs=[]
    for o in title:
     run=struct.unpack('<%dH'%o.text.units,bytes(b.u.mem_read(POOL+o.text.offset,o.text.units*2)))
     self.assertEqual(run[-1],65535);glyphs.extend(run[:-1])
    self.assertEqual(glyphs,encode(text)[:-1])
  # SGG admits208px; a wider native advance must still refuse atomically.
  data=gb.guide_content.build_content([dict(id=4,title='A',entries=[dict(id=1,title='A'*52,pages=[dict(lines=['B'],reference=0)])])],encode,lambda t:len(t)*4)
  b=RenderBench(self.compiled,data);b.action(1);b.action(1);b.build()
  b.u.mem_write(WIDTHS+65,b'\x05');b.build(expect=0)
 def test_output_pool_cannot_alias_heap_token_or_live_guide_config(self):
  b=RenderBench(self.compiled)
  for out,pool in ((TOKEN,POOL),(PLAN,TOKEN),(0x0235e000,POOL),(PLAN,0x0235e000)):
   before=b.token(),bytes(b.u.mem_read(0x0235e000,64)),bytes(b.u.mem_read(PLAN,800)),bytes(b.u.mem_read(POOL,1024))
   self.assertEqual(b.call('guide_ui_build',STATE,b.lease,ULEASE,WIDTHS,out,pool,1),0)
   self.assertEqual((b.token(),bytes(b.u.mem_read(0x0235e000,64)),bytes(b.u.mem_read(PLAN,800)),bytes(b.u.mem_read(POOL,1024))),before)
