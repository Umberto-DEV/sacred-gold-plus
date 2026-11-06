"""Pinned native font geometry and complete paired rendering; no Android claim."""
import unittest
from guide_bench import *
class NativeGuideTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  # Reuse exact native font/BG inputs and independent complete UIR verification.
  import test_painter_rom as settings_native
  cls.settings_native=settings_native.NativePainterTests
  cls.settings_native.setUpClass();cls.fixtures=cls.settings_native.fixtures
  cls.tmp=tempfile.TemporaryDirectory(prefix='guide-native-');cls.compiled,cls.detail=compile_ui(Path(cls.tmp.name),'painter')
  from sgp131.guide_content import build_from_rom
  canonical=SOURCE.parent/'local/experiments/balance493-2026-10-28'
  charmap=Path(os.environ.get('SGP_PRET_SOURCE',str(SOURCE.parent/'local/tools/pokeheartgold')))/'charmap.txt'
  cls.guides={l:build_from_rom(Path(os.environ.get('SGP131_BASE_'+l,str(canonical/f'candidate-v4-{l}.nds'))),l,charmap)[0] for l in cls.fixtures}
  artifact=os.environ.get('SGP_GUIDE_ARTIFACTS')
  if artifact:Path(artifact,'task-guide-ui-inputs.json').write_text(json.dumps(dict(uir=cls.settings_native.input_receipts,guide={l:dict(bytes=len(d),sha256=hashlib.sha256(d).hexdigest()) for l,d in cls.guides.items()}),indent=2)+'\n')
 @classmethod
 def tearDownClass(cls):cls.tmp.cleanup();cls.settings_native.tearDownClass()
 def test_complete_bilingual_font_geometry_and_native_controller_graph(self):
  records={}
  for lang,fixture in self.fixtures.items():
   data=self.guides[lang];graph=gb.guide_content.read_content(data);widths=fixture[2]
   self.assertEqual([c['id'] for c in graph],[4,1,3,2]);self.assertEqual(sum(len(c['entries']) for c in graph),467)
   b=ControllerBench(self.compiled,data);max_title=max_line=pages=references=0
   by_id={e['id']:(ci,row) for ci,c in enumerate(graph) for row,e in enumerate(c['entries'])}
   for ci,c in enumerate(graph):
    for row,e in enumerate(c['entries']):
     max_title=max(max_title,sum(widths[g-1] for g in e['title'][:-1]));self.assertLessEqual(max_title,208)
     s=State();s.cursor=View(1,ci,row,min(max(0,row-4),max(0,len(c['entries'])-5)),0);b.set_state(s)
     self.assertEqual(b.action(1),1)
     for page,p in enumerate(e['pages']):
      s=b.state();s.cursor.page=page;b.set_state(s);pages+=1
      self.assertLessEqual(len(p['lines']),7)
      for line in p['lines']:
       wide=sum(widths[g-1] for g in line[:-1]);max_line=max(max_line,wide);self.assertLessEqual(wide,208)
      if p['reference']:
       references+=1;before=bytes(b.state().cursor);self.assertEqual(b.action(1),1)
       dest=b.state();self.assertEqual((dest.cursor.category,dest.cursor.row),by_id[p['reference']])
       self.assertEqual(b.action(2),1);self.assertEqual(bytes(b.state().cursor),before)
     self.assertEqual(b.action(2),1);self.assertEqual(b.state().cursor.depth,1)
   records[lang]=dict(entries=467,pages=pages,references=references,max_title=max_title,max_line=max_line)
  artifact=os.environ.get('SGP_GUIDE_ARTIFACTS')
  if artifact:Path(artifact,'task-guide-ui-geometry-controller.json').write_text(json.dumps(records,indent=2)+'\n')
 def test_native_independent_model_reference_and_retained_both_histories(self):
  records=[]
  for lang,fixture in self.fixtures.items():
   b=NativeGuidePainter(self.compiled,fixture,self.guides[lang]);graph=gb.guide_content.read_content(b.data)
   # Finite prepared model states, then real reference A/B controller actions.
   candidates=[(sum(b.widths[g-1] for g in e['title'][:-1]),ci,row,page) for ci,c in enumerate(graph) for row,e in enumerate(c['entries']) for page,p in enumerate(e['pages'])]
   longest=max(candidates);saved=None
   for scene in range(9):
    if scene==1:b.action(1)
    elif scene in (2,3,4):
     b.action(128)
     if scene==4:
      s=b.state();s.touch_target=6;b.u.mem_write(GSTATE,bytes(s))
    elif scene==5:
     _,ci,row,page=longest;s=State();s.cursor=View(2,ci,row,min(max(0,row-4),max(0,len(graph[ci]['entries'])-5)),page)
     b.u.mem_write(GSTATE,bytes(s));saved=bytes(s.cursor)
    elif scene==6:self.assertEqual(b.action(1),1)
    elif scene==7:
     self.assertEqual(b.action(2),1);self.assertEqual(bytes(b.state().cursor),saved)
    elif scene==8:
     s=State();s.cursor=View(2,0,0,0,0);b.u.mem_write(GSTATE,bytes(s));self.assertEqual(len(graph[0]['entries'][0]['pages'][0]['lines']),7)
    plan=b.build();index=0 if b.get(pb.PBG+76)!=0 else 1
    if scene==0:
     before=bytes(b.u.mem_read(GCTX,2552));b.put(GDES+20,33)
     self.assertEqual(b.begin(index),0);self.assertEqual(bytes(b.u.mem_read(GCTX,2552)),before)
     b.put(GDES+20,plan.count)
    expected=native_pair_reference(b,index)
    b.finish_paint(index);actual=b.pair_pixels(index)
    self.assertEqual(actual,expected,(lang,scene,'independent native full pair'))
    full=b.get(GCTX+48);self.assertEqual(b.get(pb.PBG+80),index)
    self.assertEqual(b.get(pb.PBG+84),b.version)
    if scene in (2,3,4):self.assertEqual(full,2,'cursor change inherits the exact presented list')
    if scene in (0,1):self.assertEqual(full,1,'initial or changed view requires FULL')
    records.append(dict(language=lang,scene=scene,index=index,version=b.version,full=full,upper_sha256=hashlib.sha256(actual[0]).hexdigest(),lower_sha256=hashlib.sha256(actual[1]).hexdigest(),ops=plan.count,pool=plan.pool_used))
    before=bytes(b.u.mem_read(GCTX,2552));self.assertEqual(b.begin(1-index),0,'pending pair immutable')
    self.assertEqual(bytes(b.u.mem_read(GCTX,2552)),before)
    b.publish();self.assertEqual(b.begin(index),0,'front index immutable')
    self.assertEqual(bytes(b.u.mem_read(CODE,len(b.code))),b.code,'entire compiled payload immutable')
    if os.environ.get('SGP_GUIDE_ARTIFACTS') and scene in (0,8):native_pair_image(b,index,Path(os.environ['SGP_GUIDE_ARTIFACTS'],f'task-guide-ui-native-{lang}-scene{scene}.png'))
    b.writes.clear();b.store_contexts.clear()
    print(f'Guide native {lang} scene{scene} pair{index} version{b.get(pb.PBG+68+4*index)} FULL{full}',flush=True)
  artifact=os.environ.get('SGP_GUIDE_ARTIFACTS')
  if artifact:Path(artifact,'task-guide-ui-native-pairs.json').write_text(json.dumps(records,indent=2)+'\n')
 def test_final_native_root_list_detail_static_lower_both_languages(self):
  for lang,fixture in self.fixtures.items():
   b=NativeGuidePainter(self.compiled,fixture,self.guides[lang]);static=None
   for depth in range(3):
    if depth:b.action(1)
    p=b.build();index=depth%2;expected=native_pair_reference(b,index)
    b.finish_paint(index);actual=b.pair_pixels(index)
    self.assertEqual(actual,expected,(lang,depth))
    if static is None:static=actual[1]
    self.assertEqual(actual[1],static);self.assertEqual(b.get(GCTX+28),0)
    self.assertTrue(all(o.screen==0 and o.kind!=3 for o in p.ops[:p.count]))
    b.publish();print('final Guide',lang,'depth',depth,'ops',p.count,'pool',p.pool_used,'lower',hashlib.sha256(static).hexdigest(),flush=True)
    b.writes.clear();b.store_contexts.clear();b.metrics.clear()
   self.assertEqual(b.call('guide_paint_retire',GCTX),3)
   self.assertEqual(b.call('ui_bg_retire',TOKEN,pb.PBG,1),1)
 def test_live_sys_request_is_copied_before_caller_frame_reuse(self):
  fixture=self.fixtures['EN'];b=NativeGuidePainter(self.compiled,fixture,self.guides['EN']);b.build()
  request=0x027e3100;b.u.mem_write(request,struct.pack('<10I',TOKEN,pb.PBG,fb.FL,b.lease,GDES,GUIR,GBUF,1,0,1))
  self.assertEqual(b.call('guide_paint_begin',GCTX,request),1)
  b.u.mem_write(request,b'\xa5'*40)
  result=1
  for _ in range(2000):
   if result!=1:break
   result=b.call('guide_paint_step',GCTX,8)
  self.assertEqual(result,2);self.assertEqual(b.get(pb.PBG+80),0);self.assertEqual(b.get(pb.PBG+84),1)
  b.publish();b.action(1);b.build()
  b.u.mem_write(request,struct.pack('<10I',TOKEN,pb.PBG,fb.FL,b.lease,GDES,GUIR,GBUF,1,1,2))
  self.assertEqual(b.call('guide_paint_begin',GCTX,request),1);b.u.mem_write(request,b'\x5a'*40)
  for _ in range(200):
   self.assertEqual(b.call('guide_paint_step',GCTX,8),1)
   if b.get(GCTX+12)==6:break
  self.assertEqual(b.get(GCTX+12),6);self.assertNotEqual(b.get(fb.FL+84),0)
  self.assertEqual(b.call('guide_paint_retire',GCTX),4,'partial lifecycle cannot be reused')
  self.assertEqual(b.get(fb.FL+84),0);self.assertEqual(b.get(pb.PBG+80),2)
  for index in (0,1):
   self.assertEqual(b.get(GCTX+84+816*index+804),0)
   self.assertEqual(b.get(GCTX+84+816*index+808),0x3fffff)
   self.assertEqual(b.get(GCTX+84+816*index+812),0x3fffff)
  self.assertEqual(b.call('ui_bg_retire',TOKEN,pb.PBG,1),1)
  self.assertEqual(b.call('guide_paint_retire',GCTX),3)
  self.assertEqual(bytes(b.u.mem_read(CODE,len(b.code))),b.code)

 def test_every_bilingual_native_width_plan_and_pool_bound(self):
  records={}
  with tempfile.TemporaryDirectory(prefix='guide-plans-final-') as d:planner,planner_detail=compile_ui(Path(d),'render')
  for lang,fixture in self.fixtures.items():
   b=RenderBench(planner,self.guides[lang],fixture[:3]);graph=gb.guide_content.read_content(b.data)
   max_ops=max_pool=builds=0
   for ci,c in enumerate(graph):
    for row,e in enumerate(c['entries']):
     s=State();s.cursor=View(1,ci,row,min(max(0,row-4),max(0,len(c['entries'])-5)),0);b.set_state(s)
     p=b.build();builds+=1;max_ops=max(max_ops,p.count);max_pool=max(max_pool,p.pool_used)
     for page,data in enumerate(e['pages']):
      s.cursor.depth=2;s.cursor.page=page;b.set_state(s);p=b.build();builds+=1
      max_ops=max(max_ops,p.count);max_pool=max(max_pool,p.pool_used)
      body=[o for o in p.ops[:p.count] if o.screen==0 and 32<=o.y<144 and o.kind==1]
      self.assertEqual(len(body),len(data['lines']))
      self.assertEqual([o.y for o in body],[32+16*i for i in range(len(data['lines']))])
      self.assertTrue(all(o.w<=208 for o in body))
      if data['reference']:
       s.back_count=8;b.set_state(s);limited=b.build();builds+=1
       link=next(o for o in limited.ops[:limited.count] if o.kind==4 and o.x==36 and o.y==160)
       self.assertTrue(link.flags&4);s.back_count=0
   self.assertLessEqual(max_ops,32);self.assertLessEqual(max_pool,1024)
   records[lang]=dict(builds=builds,max_ops=max_ops,max_pool=max_pool,payload_sha256=hashlib.sha256(planner[0]).hexdigest())
   print(f'Guide complete {lang} plans{builds} ops{max_ops} pool{max_pool}',flush=True)
  artifact=os.environ.get('SGP_GUIDE_ARTIFACTS')
  if artifact:Path(artifact,'task-guide-ui-complete-plans.json').write_text(json.dumps(records,indent=2)+'\n')
 def test_guide_reader_and_real_owner_aliases_refuse_before_paint(self):
  b=NativeGuidePainter(self.compiled,self.fixtures['EN'],self.guides['EN']);b.build()
  request=struct.pack('<10I',TOKEN,pb.PBG,fb.FL,b.lease,GDES,GUIR,GBUF,1,0,1)
  # A copied request cannot hide in the closed persistent Guide FSFile either.
  saved=bytes(b.u.mem_read(b.reader,80));b.u.mem_write(b.reader,request)
  before=bytes(b.u.mem_read(GCTX,2552))
  self.assertEqual(b.call('guide_paint_begin',GCTX,b.reader),0)
  self.assertEqual(bytes(b.u.mem_read(GCTX,2552)),before);b.u.mem_write(b.reader,saved)
  baseline=b.snapshot()
  for place in (b.pool+1000,GDES+760,fb.FL+32,GUIR,GBUF):
   snapshot=bytes(b.u.mem_read(place,40));b.u.mem_write(place,request)
   before=bytes(b.u.mem_read(GCTX,2552));self.assertEqual(b.call('guide_paint_begin',GCTX,place),0)
   self.assertEqual(bytes(b.u.mem_read(GCTX,2552)),before);b.restore(baseline)
  for offset,value in ((0,TOKEN+4),(4,pb.PBG+4),(8,fb.FL+4),(12,b.lease+4),(16,GDES+4),(20,GBUF),(24,GUIR),(28,2),(32,2),(36,0)):
   malformed=bytearray(request);struct.pack_into('<I',malformed,offset,value);b.u.mem_write(GREQ,bytes(malformed))
   before=bytes(b.u.mem_read(GCTX,2552));self.assertEqual(b.call('guide_paint_begin',GCTX,GREQ),0)
   self.assertEqual(bytes(b.u.mem_read(GCTX,2552)),before);b.restore(baseline)
