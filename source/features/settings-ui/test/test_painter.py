"""Class A actual ARM painter tests. Native seams are not native pixel proof."""
import unittest,tempfile
from painter_bench import *
class PainterTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.tmp=tempfile.TemporaryDirectory(prefix='settings-painter-a-');cls.compiled,cls.detail=compile_painter(Path(cls.tmp.name))
 @classmethod
 def tearDownClass(cls):cls.tmp.cleanup()
 def test_search_footer_with_extended_layout_id_paints(self):
  b=PainterBench(self.compiled);b.s.view=3;b.s.draft.shiny.target=0;p=b.build()
  self.assertGreaterEqual(ops(p,11)[0].a,12)
  self.assertEqual(b.finish_paint(),PREPARED)
 def test_hgss_focus_chosen_surfaces_and_command_rail(self):
  # Wrong materials/old18px focus lose native glyph containment and contrast.
  b=PainterBench(self.compiled);p=b.build()
  self.assertEqual(tuple(struct.unpack('<16H',b.u.mem_read(PCTX+3288,32))),
   (0,0x7bdf,0x2508,0x51a4,0x6f19,0x45ac,0x56b5,0x35ad,0x1cbb,0x63b8,0x7fff,0x564c,0x3adf,0x6b7a,0x28f6,0x5ef5))
  self.assertEqual([(o.y,o.h) for o in ops(p,3)],[(56,20)])
  self.assertEqual([(o.y,o.h,o.b) for o in ops(p,11)],[(156,16,8)])
  self.assertTrue(all(o.h==18 and o.w>=8 for o in ops(p,6)))
  self.assertEqual(b.finish_paint(),PREPARED)
 def test_footer_caps_are_neutral_clipped_and_use_full_reserved_envelopes(self):
  # Kills former green X, too-small planner advances, and printer-erased edges.
  b=PainterBench(self.compiled);p=b.build();o=ops(p,11)[0]
  self.assertEqual(b.finish_paint(),PREPARED)
  self.assertEqual(tuple(struct.unpack('<2H',b.u.mem_read(PCTX+3300,4))),(0x56b5,0x35ad))
  canvas=b.pixels(0);runs=footer_runs(b,o)
  # CRC-gated synthetic6px keys reserve16px, like the pinned native keys.
  self.assertEqual([r[1] for r in runs if r[-1]],[16,80,132,190])
  for words,x,y,colors,width,key in runs:
   if not key:continue
   self.assertEqual(colors,(2,1));left=x-5;w=width+10
   def color(xx,yy):
    off=(yy//8*30+xx//8)*32+yy%8*4+xx%8//2
    return canvas[off]>>(4*(xx%2))&15
   self.assertEqual([color(xx,y) for xx in range(left,left+w)],[2,2]+[6]*(w-4)+[2,2])
   self.assertEqual([color(xx,y+14) for xx in range(left,left+w)],[2,2]+[6]*(w-4)+[2,2])
   self.assertEqual([color(xx,y+15) for xx in range(left,left+w)],[2]*3+[7]*(w-4)+[2])
   self.assertEqual((color(left,y+5),color(left+w-1,y+5)),(6,6))
   self.assertEqual([color(xx,y+5) for xx in range(left+w,left+w+3)],[2,2,2],"three clear pixels after cap")
 def test_full_canvas_is_composed_before_ready_and_front_stays_immutable(self):
  b=PainterBench(self.compiled);p=b.build();before=b.globals()
  self.assertEqual(b.finish_paint(),PREPARED)
  self.assertEqual(b.globals(),before);self.assertEqual(b.get(fb.FL+84),0)
  self.assertEqual(b.get(PBG+76),2);self.assertEqual(b.get(PBG+80),0)
  self.assertEqual(b.get(PBG+68),1);self.assertTrue(any(x!=0x11 for x in b.pixels(0)))
  self.assertEqual(b.get(PCTX+92+1184),1);self.assertEqual(b.get(PCTX+92+1188),1)

class PainterContracts(unittest.TestCase):
 @classmethod
 def setUpClass(cls):PainterTests.setUpClass.__func__(cls)
 @classmethod
 def tearDownClass(cls):PainterTests.tearDownClass.__func__(cls)
 def test_packed_rect_matches_independent_pixels_at_parities_tiles_edges_and_masks(self):
  b=PainterBench(self.compiled);b.build();self.assertEqual(b.begin(),MORE)
  pixels=b.get(PBG+28);cases=0
  for x in (0,1,6,7,8,9,230,231,238,239):
   for width in sorted({1,2,3,7,8,9,min(17,240-x)}):
    if x+width>240:continue
    for y,height in ((0,1),(1,2),(6,3),(7,9),(8,8),(155,18),(175,1)):
     for edge,mask in ((0,FULL),(8,FULL),(8,0x155555)):
      initial=bytes((i*29+7)&255 for i in range(21120));expected=bytearray(initial)
      # Pixel oracle deliberately does not use packed production arithmetic.
      for yy in range(y,y+height):
       if mask>> (yy//8)&1:
        for xx in range(x,x+width):pixel_set(expected,xx,yy,edge if edge and (xx in (x,x+width-1) or yy in (y,y+height-1)) else 13)
      b.u.mem_write(pixels,initial);b.put(PCTX+64,TOKEN);b.put(PCTX+68,PBG)
      before=bytes(b.u.mem_read(pixels-16,16)),bytes(b.u.mem_read(pixels+21120,16)),b.pixels(1)
      b.call('sp_rect',PCTX,x,y,width,height,13,edge,mask)
      self.assertEqual(b.pixels(0),bytes(expected),(x,y,width,height,edge,mask))
      self.assertEqual((bytes(b.u.mem_read(pixels-16,16)),bytes(b.u.mem_read(pixels+21120,16)),b.pixels(1)),before)
      cases+=1;b.writes.clear();b.metrics.clear()
  self.assertGreater(cases,1000)
 def test_footer_corruption_refuses_before_acquisition_without_writing_sources(self):
  for change in ('glyph','eos','offset','variant','count','units'):
   b=PainterBench(self.compiled);p=b.build();o=ops(p,11)[0]
   if change=='glyph':b.put(b.pool+o.offset,509,2)
   elif change=='eos':b.put(b.pool+o.offset+2,1,2)
   elif change=='offset':o.offset=254
   elif change=='variant':o.a=11
   elif change=='count':o.b=7
   else:o.units-=1
   b.u.mem_write(PDES,bytes(p));before=(bytes(b.u.mem_read(PBG,176)),bytes(p),bytes(b.u.mem_read(b.pool,256)),bytes(b.u.mem_read(b.root,b.root_bytes)))
   result=b.begin()
   for _ in range(80):
    if result!=MORE:break
    result=b.step()
   self.assertEqual(result,REFUSE,change)
   self.assertEqual((bytes(b.u.mem_read(PBG,176)),bytes(b.u.mem_read(PDES,1184)),bytes(b.u.mem_read(b.pool,256)),bytes(b.u.mem_read(b.root,b.root_bytes))),before)
 def test_retained_replays_unchanged_shared_rows_against_independent_full(self):
  b=PainterBench(self.compiled)
  for row in (0,1,2,3,4,5,4,3):
   b.s.row=row;p=b.build(first=1);expected=synthetic_full_reference(b,p)
   self.assertEqual(b.finish_paint(),PREPARED)
   index=b.get(PBG+80);self.assertEqual(b.pixels(index),expected)
   self.assertEqual(b.get(PCTX+28),independent_closure(p,b.get(PCTX+24)))
   b.publish()
  self.assertNotEqual(b.get(PCTX+28),FULL)
 def test_refuses_bad_ops_before_native_preparation_and_preserves_plan_pool(self):
  b=PainterBench(self.compiled);p=b.build();old=bytes(b.u.mem_read(b.pool,256));native=bytes(b.u.mem_read(PBG,176))
  p.ops[0].units-=1;b.u.mem_write(PDES,bytes(p));self.assertEqual(b.begin(),MORE)
  result=MORE
  for _ in range(80):
   result=b.step()
   if result!=MORE:break
  self.assertEqual(result,REFUSE);self.assertEqual(bytes(b.u.mem_read(PBG,176)),native)
  self.assertEqual(bytes(b.u.mem_read(b.pool,256)),old);self.assertEqual(bytes(b.u.mem_read(PDES,1184)),bytes(p))
 def test_rejects_stale_binding_aliases_and_fresh_init_over_live(self):
  b=PainterBench(self.compiled);b.build();self.assertEqual(b.init_painter(),0)
  self.assertEqual(b.begin(),MORE);self.assertEqual(b.begin(),REFUSE)
  self.assertEqual(b.call('settings_paint_retire',PCTX),UNCHANGED)
  b.put(PREQ+28,2);self.assertEqual(b.call('settings_paint_begin',PCTX,PREQ),REFUSE)
  b.put(PREQ+28,1);b.put(PREQ+16,PCTX+92)
  self.assertEqual(b.call('settings_paint_begin',PCTX,PREQ),REFUSE)
  b.put(PREQ+16,PDES);b.put(PBUF+12,b.epoch+1)
  self.assertEqual(b.call('settings_paint_begin',PCTX,PREQ),REFUSE)
 def test_partial_retirement_cancels_job_and_requires_bg_retirement(self):
  b=PainterBench(self.compiled);b.build();self.assertEqual(b.begin(),MORE)
  for _ in range(200):
   self.assertEqual(b.step(),MORE)
   if b.get(PCTX+12)==6:break
  self.assertEqual(b.get(PCTX+12),6);self.assertNotEqual(b.get(fb.FL+84),0)
  self.assertEqual(b.call('settings_paint_retire',PCTX),FAILED)
  self.assertEqual(b.get(fb.FL+84),0);self.assertEqual(b.get(PCTX+92+1188),0)
  self.assertEqual(b.call('ui_bg_retire',TOKEN,PBG,1),1)
  self.assertEqual(b.call('settings_paint_retire',PCTX),UNCHANGED)
  self.assertEqual(b.get(PCTX+92+1192),FULL)
 def test_hold_is_sticky_even_after_job_cancel_and_bg_retirement(self):
  b=PainterBench(self.compiled);b.build();self.assertEqual(b.begin(),MORE)
  for _ in range(200):
   b.step()
   if b.get(PCTX+12)==6:break
  b.put(fb.FM+4,0);self.assertEqual(b.step(),HOLD)
  self.assertEqual(b.call('settings_paint_retire',PCTX),HOLD)
  self.assertEqual(b.call('ui_bg_retire',TOKEN,PBG,1),1)
  self.assertEqual(b.call('settings_paint_retire',PCTX),HOLD)
 def test_front_equality_skips_and_cursor_roundtrip_copies_only_changed_rows(self):
  b=PainterBench(self.compiled)
  b.build();b.finish_paint();b.publish();front=b.pixels(0)
  b.build();self.assertEqual(b.finish_paint(),UNCHANGED);self.assertEqual(b.get(PBG+80),2)
  b.s.row=1;b.build();b.finish_paint();b.publish()
  b.s.row=0;b.build();b.finish_paint();self.assertEqual(b.get(PCTX+48),0)
  self.assertNotEqual(b.get(PCTX+28),FULL);self.assertEqual(b.pixels(0),front)
 def test_invalid_budget_defer_and_palette_exact(self):
  b=PainterBench(self.compiled);self.assertEqual(tuple(struct.unpack('<16H',b.u.mem_read(PCTX+3288,32))),PALETTE)
  b.build();self.assertEqual(b.begin(),MORE);before=bytes(b.u.mem_read(PCTX,P_SIZE))
  self.assertEqual(b.step(0),REFUSE);self.assertEqual(b.step(9),REFUSE)
  b.put(IME,0);self.assertEqual(b.step(),MORE);b.put(IME,1)
  self.assertEqual(bytes(b.u.mem_read(PCTX,P_SIZE)),before)
 def test_frame_header_without_matching_frame_operation_refuses_before_acquire(self):
  b=PainterBench(self.compiled);p=b.build();p.frame=1;b.u.mem_write(PDES,bytes(p));self.assertEqual(b.begin(),MORE)
  result=MORE
  for _ in range(80):
   result=b.step()
   if result!=MORE:break
  self.assertEqual(result,REFUSE);self.assertEqual(b.get(PBG+88),2)
 def test_ready_refuses_real_live_job_and_never_commits_history(self):
  b=PainterBench(self.compiled);active_job_at_ready(b)
  self.assertEqual(b.get(PCTX+92+1188),0)
 def test_closure_can_honestly_expand_to_all_rows(self):
  b=PainterBench(self.compiled);b.s.view=2;b.s.row=1;p=b.build();p.ops[0].h=160
  b.u.mem_write(PDES,bytes(p));seed_completed(b,p,0,1);seed_completed(b,p,1,2)
  p.ops[2].flags|=32;b.u.mem_write(PDES,bytes(p));self.assertEqual(b.finish_paint(),PREPARED)
  self.assertEqual(b.get(PCTX+28),FULL)
 def test_seeded_retained_pixels_and_pool_source_immutable(self):
  b=PainterBench(self.compiled);seeded_retained(b)
  before=bytes(b.u.mem_read(b.pool,256)),bytes(b.u.mem_read(PDES,1184)),bytes(b.u.mem_read(b.root,b.root_bytes))
  self.assertEqual(b.step(),PREPARED)
  self.assertEqual((bytes(b.u.mem_read(b.pool,256)),bytes(b.u.mem_read(PDES,1184)),bytes(b.u.mem_read(b.root,b.root_bytes))),before)
 def test_meaningful_compiled_omission_mutants_are_killed(self):
  replay='o=&d->ops[p->op_cursor];\n  if(sp_text_kind(o)'
  changed_only='o=&d->ops[p->op_cursor];\n  if(!p->full){SettingsPaintHistory *h=&p->history[p->index];for(unsigned i=0;i<h->plan.count;++i)if(sr_equal(o,&h->plan.ops[i])){++p->op_cursor;return SETTINGS_PAINT_MORE;}}\n  if(sp_text_kind(o)'
  cases=(('all-ops',(replay,changed_only),seeded_retained,'all intersecting ops replayed'),
   ('closure',('p->paint_rows|=sr_rows(&d->ops[i]);','p->paint_rows|=0;'),seeded_retained,'write outside admitted rows'),
   ('history',('h->version=p->version;h->invalid_rows=0;h->valid=1;','h->version=p->version;h->invalid_rows=0;h->valid=0;'),seeded_retained,'completed history'),
   ('job-barrier',('if(p->font->job || p->job.phase==UI_FONT_ACTIVE)return sp_bad(p,1,14);','if(0)return sp_bad(p,1,14);'),active_job_at_ready,'no job at Ready'))
  for name,mutation,exercise,reason in cases:
   with self.subTest(mutation=name),tempfile.TemporaryDirectory(prefix='painter-mutant-') as d:
    exercise(PainterBench(self.compiled)) # Each mutant requires its own green baseline.
    compiled,_=compile_painter(Path(d),mutation)
    with self.assertRaisesRegex(AssertionError,reason):exercise(PainterBench(compiled))
 def test_copied_live_record_and_catalogue_inside_understated_pool_refuse(self):
  b=PainterBench(self.compiled);copy=0x02354000;b.u.mem_write(copy,bytes(b.u.mem_read(PCTX,P_SIZE)))
  self.assertEqual(b.call('settings_paint_step',copy,8),REFUSE)
  b.s.view=2;b.s.row=1;b.build();self.assertGreater(b.get(PDES+12),0)
  b.u.mem_write(b.pool+16,bytes(b.u.mem_read(PCAT,28)));b.put(PBUF+8,4)
  b.u.mem_write(PREQ,struct.pack('<10I',TOKEN,PBG,fb.FL,b.pool+16,PDES,PUIR,PBUF,1,0,1))
  before=bytes(b.u.mem_read(PBG,176));self.assertEqual(b.call('settings_paint_begin',PCTX,PREQ),REFUSE)
  self.assertEqual(bytes(b.u.mem_read(PBG,176)),before)
 def test_owner_loss_after_partial_clear_invalidates_without_pending(self):
  b=PainterBench(self.compiled);b.build();self.assertEqual(b.begin(),MORE)
  for _ in range(150):
   self.assertEqual(b.step(),MORE)
   if b.get(PCTX+32):break
  self.assertNotEqual(b.get(PCTX+32),0);b.put(PBUF+16,0)
  self.assertEqual(b.step(),FAILED);self.assertEqual(b.get(PBG+80),2)
  self.assertEqual(b.get(PCTX+92+1188),0);self.assertEqual(b.get(PCTX+92+1192),FULL)
 def test_request_descriptor_cannot_hide_in_dedicated_pool_tail(self):
  b=PainterBench(self.compiled);b.s.view=2;b.s.row=1;b.build()
  request=struct.pack('<10I',TOKEN,PBG,fb.FL,PCAT,PDES,PUIR,PBUF,1,0,1)
  b.u.mem_write(b.pool+128,request)
  self.assertEqual(b.call('settings_paint_begin',PCTX,b.pool+128),REFUSE)
 def test_disabled_lock_shackle_preserves_both_top_corner_backgrounds(self):
  b=PainterBench(self.compiled);b.s.snapshot.editable_rows=0
  p=b.build(first=1);self.assertEqual(len(ops(p,8)),6)
  expected=synthetic_full_reference(b,p)
  self.assertEqual(b.finish_paint(),PREPARED)
  self.assertEqual(b.pixels(0),expected,'disabled lock shackle versus independent full reference')
if __name__=='__main__':unittest.main()
