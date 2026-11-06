import unittest,tempfile
from render_bench import *
class RenderTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.tmp=tempfile.TemporaryDirectory(prefix='settings-render-');cls.compiled=compile_render(Path(cls.tmp.name))
 @classmethod
 def tearDownClass(cls):cls.tmp.cleanup()
 def test_footer_runs_are_atomic_bounded_and_require_authored_separators(self):
  for position,value in ((0,111),(1,111),(8,111),(7,0xe000)):
   words,widths=synthetic();raw=list(words[81]);raw[position]=value;words[81]=tuple(raw)
   b=RenderBench(self.compiled,(words,widths));b.u.mem_write(OUT,b'X'*C.sizeof(Plan));b.u.mem_write(POOL,b'Y'*4096)
   b.build(0);self.assertEqual(bytes(b.u.mem_read(OUT,C.sizeof(Plan))),b'X'*C.sizeof(Plan));self.assertEqual(bytes(b.u.mem_read(POOL,4096)),b'Y'*4096)
  b=RenderBench(self.compiled);p=b.build();o=ops(p,11)[0]
  self.assertEqual((o.b,o.y,o.h),(8,156,16))
  words=struct.unpack('<%dH'%o.units,bytes(b.u.mem_read(POOL+o.offset,o.units*2)))
  self.assertEqual(words.count(65535),8)
  b.put(REQ+20,p.pool_used-2);before=bytes(b.u.mem_read(OUT,C.sizeof(Plan)))+bytes(b.u.mem_read(POOL,4096));b.build(0)
  self.assertEqual(bytes(b.u.mem_read(OUT,C.sizeof(Plan)))+bytes(b.u.mem_read(POOL,4096)),before)
 def test_root_heading_consumes_slot_and_cursor_stays_on_control(self):
  b=RenderBench(self.compiled);p=b.build()
  self.assertEqual(p.view,0)
  headings=[o for o in ops(p,1) if o.flags&32]
  self.assertEqual([(o.id,o.y) for o in headings],[(3,38)])
  self.assertEqual([(o.row,o.y,o.h) for o in ops(p,3)],[(0,56,20)])
 def test_every_root_row_and_boundary_is_visible(self):
  b=RenderBench(self.compiled)
  for mode,total in ((0,12),(1,14)):
   b.s.draft.shiny.mode=mode
   for row in range(total):
    b.s.row=row;p=b.build()
    bands=ops(p,3);self.assertEqual(len(bands),1);self.assertEqual(bands[0].row,row)
    self.assertLessEqual(bands[0].y+bands[0].h,160)
    ordinal=[o for o in ops(p,2) if o.y==20][0]
    self.assertEqual((ordinal.a,ordinal.b),(row+1,total))
    for o in ops(p):self.assertLessEqual(o.x+o.w,240);self.assertLessEqual(o.y+o.h,176)
 def test_selector_and_search_readonly_semantics(self):
  b=RenderBench(self.compiled);b.s.view=1;b.s.selector_row=5;b.s.selector_cursor=19;b.s.selector_pending=19
  p=b.build();self.assertEqual([(o.id,o.y) for o in ops(p,1) if o.row==5],[(56+i,38+20*i) for i in range(6)])
  b.s.view=3;b.s.row=13;p=b.build()
  self.assertEqual([(o.row,o.a,o.b) for o in ops(p,2) if o.y>=32],[(3,0,0),(4,1,4096),(5,40,40)])
  for o in ops(p):
   if o.row in (3,4,5):self.assertTrue(o.flags&8);self.assertNotIn(o.kind,(3,4,5,7))
 def test_all_views_info_preview_and_confirm_defaults(self):
  b=RenderBench(self.compiled)
  for view in range(7):
   b.s.view=view;b.s.row=0;b.s.selector_row=0;b.s.selector_cursor=0;b.s.selector_pending=0
   b.s.choice=2 if view==4 else 1 if view==5 else 0
   p=b.build();self.assertEqual(p.view,view)
  b.s.view=2;b.s.row=5;b.s.draft.native.frame=19;p=b.build()
  self.assertEqual([(o.choice,o.y,o.h) for o in ops(p,10)],[(19,104,48)])
 def test_frame_preview_is_inside_native_ring_and_text_preview_stays_unframed(self):
  # Native UiBgFrame{3,15,25,4}: Window physical origin8,8;
  # ring spans x-2..x+w+2/y-1..y+h, inner width25*8=200.
  inner=(3*8-8,15*8-8,25*8,4*8)
  words,widths=synthetic();words[125]=tuple([100]*50)+(65535,)
  b=RenderBench(self.compiled,(words,widths));b.s.view=2;b.s.row=5
  for frame in (0,19):
   b.s.draft.native.frame=frame
   for prefix in (0,1,49,50,0xffffffff):
    b.put(REQ+36,prefix);p=b.build();o=ops(p,9)[0]
    self.assertEqual((o.x,o.y,o.w,o.h),inner)
    self.assertEqual(ops(p,10)[0].choice,frame)
    glyphs=struct.unpack('<%dH'%o.units,bytes(b.u.mem_read(POOL+o.offset,o.units*2)))
    self.assertEqual(glyphs[-1],65535)
    self.assertLessEqual(o.x+sum(widths[g-1] for g in glyphs[:-1]),inner[0]+inner[2])
  b.s.row=0;p=b.build();o=ops(p,9)[0]
  self.assertEqual((o.x,o.y,o.w,o.h),(12,112,216,32));self.assertFalse(ops(p,10))
 def test_frame_preview_refuses_border_overlap_without_publishing(self):
  words,widths=synthetic();words[125]=tuple([100]*51)+(65535,) #204px
  b=RenderBench(self.compiled,(words,widths));b.s.view=2;b.s.row=0;b.build()
  before=bytes(b.u.mem_read(OUT,C.sizeof(Plan)))+bytes(b.u.mem_read(POOL,4096))
  b.s.row=5;b.build(0)
  self.assertEqual(bytes(b.u.mem_read(OUT,C.sizeof(Plan)))+bytes(b.u.mem_read(POOL,4096)),before)
 def test_notice_context_preserves_six_search_fields(self):
  for notice,identity in ((1,99),(2,100),(3,103),(4,102),(5,101),(6,104)):
   b=RenderBench(self.compiled);b.s.view=3;b.s.row=13;b.s.notice=notice;p=b.build()
   self.assertIn(identity,[o.id for o in ops(p,1) if o.y==20])
   self.assertEqual(sorted(set(o.y for o in ops(p,1) if 32<=o.y<160)),[38,58,78,98,118,138])
 def test_u32_decimal_fraction_carries_capacity_and_alphabet(self):
  b=RenderBench(self.compiled);b.allowed=[(POOL,POOL+4096)]
  for value in (0,1,4294967295,*[10**i for i in range(10)],*[10**i-1 for i in range(1,10)]):
   for fraction in (0,1):
    b.u.mem_write(REQ,struct.pack('<7I',CAT,POOL,4096,9,value,4294967295,fraction))
    n=b.call('settings_render_format',REQ)
    text=str(value)+('/4294967295' if fraction else '')
    expected=[300+int(c) if c!='/' else 310 for c in text]+[65535]
    self.assertEqual(n,len(expected));self.assertEqual(list(struct.unpack('<%dH'%n,bytes(b.u.mem_read(POOL,n*2)))),expected)
  for capacity in (0,3,4,4097):
   b.u.mem_write(REQ,struct.pack('<7I',CAT,POOL,capacity,9,4294967295,1,1))
   before=bytes(b.u.mem_read(POOL,64));self.assertEqual(b.call('settings_render_format',REQ),0);self.assertEqual(bytes(b.u.mem_read(POOL,64)),before)
 def test_target_action_does_not_claim_left_right_edits(self):
  b=RenderBench(self.compiled);b.s.row=12;p=b.build()
  self.assertTrue(any(o.kind==7 and o.row==12 for o in ops(p)))
  self.assertFalse(any(o.kind in (4,5) and o.row==12 for o in ops(p)))
 def test_empty_method_and_preview_bad_glyph_refuse_or_explain(self):
  b=RenderBench(self.compiled);b.s.view=3;b.s.row=13;b.s.snapshot.shiny.method_mask=0;p=b.build()
  self.assertIn(132,[o.id for o in ops(p,1) if o.row==1])
  self.assertTrue(all(o.flags&4 for o in ops(p) if o.row==1 and o.kind in (4,5)))
  words,widths=synthetic();words[125]=(0,65535)
  b=RenderBench(self.compiled,(words,widths));b.s.view=2;b.put(REQ+36,0);b.build(0)
 def test_dirty_rejects_invalid_geometry_before_shifts(self):
  b=RenderBench(self.compiled);p=b.build();q=Plan.from_buffer_copy(bytes(p));q.ops[0].h=0
  self.assertEqual(b.dirty(q,p),(0x3fffff,1))
 def test_catalogue_and_output_extent_refusals_never_publish(self):
  for words in ({1:(0,65535)},{1:(510,65535)},{1:(5,0xe000,5,65535)},{1:(5,65535,6,65535)},{1:(5,6)},
                {130:tuple([300]*14)+ (65535,)},{125:(5,0xe000,65535)}):
   data,widths=synthetic();data.update(words);b=RenderBench(self.compiled,(data,widths))
   if 125 in words:b.s.view=2
   b.u.mem_write(OUT,b'X'*C.sizeof(Plan));b.u.mem_write(POOL,b'Y'*4096);b.build(0)
   self.assertEqual(bytes(b.u.mem_read(OUT,C.sizeof(Plan))),b'X'*C.sizeof(Plan));self.assertEqual(bytes(b.u.mem_read(POOL,4096)),b'Y'*4096)
  for offset,value in ((8,STATE),(8,DATA),(8,CAT),(8,REQ),(8,WIDTHS),(8,POOL),(12,C.sizeof(Plan)-1),(16,OUT),(16,DATA),(20,4097),(24,0),(28,18),(32,21)):
   b=RenderBench(self.compiled);b.put(REQ+offset,value);b.build(0)
  for offset,value in ((4,0xffffffff),(8,0xffffffff),(12,638),(16,0x04000000),(20,508),(24,0)):
   b=RenderBench(self.compiled);b.put(CAT+offset,value);b.build(0)
 def test_three_alternating_histories_match_tile_row_semantics(self):
  b=RenderBench(self.compiled);histories=[None,None];plans=[]
  for row,mode in ((0,1),(1,1),(6,1),(11,1),(11,0),(11,1)):
   b.s.row=row;b.s.draft.shiny.mode=mode;plans.append(b.build())
  def row_semantics(p,tile):
   return frozenset((o.a,o.b,o.id,o.units,o.flags,o.x,o.y,o.w,o.h,o.kind,o.row,o.choice)
    for o in ops(p) if ((36+(o.y-36)//20*20) if o.row!=255 and 36<=o.y<156 else o.y)<8*(tile+1) and (((36+(o.y-36)//20*20)+20) if o.row!=255 and 36<=o.y<156 else o.y+o.h)>8*tile)
  for i,p in enumerate(plans):
   prior=histories[i%2]
   expected=0x3fffff if prior is None else sum(1<<t for t in range(22) if row_semantics(prior,t)!=row_semantics(p,t))
   self.assertEqual(b.dirty(prior,p)[0],expected);histories[i%2]=p
  # One touched row remains invalid even when semantic model returns to history.
  self.assertEqual(b.dirty(histories[0],histories[0],1<<8),(1<<8,0))
  old=histories[0];new=Plan.from_buffer_copy(bytes(old));new.pool_epoch+=1
  for o in new.ops:o.offset+=10
  self.assertEqual(b.dirty(old,new),(0,0))
 def test_controller_selector_cancel_info_return_and_sparse_methods(self):
  b=RenderBench(self.compiled)
  def step(key):
   b.s.sample_ready=1;b.s.release_gate=0;b.u.mem_write(STATE,bytes(b.s));b.allowed=[(STATE,STATE+C.sizeof(State))]
   b.call('settings_step',STATE,key,0);b.s=State.from_buffer_copy(bytes(b.u.mem_read(STATE,C.sizeof(State))))
  for row in range(13):
   b.s.view=0;b.s.row=row;step(1);self.assertEqual(b.s.view,1);p=b.build()
   self.assertEqual(p.view,1);step(2);self.assertEqual((b.s.view,b.s.row),(0,row));b.build()
   step(2048);self.assertEqual(b.s.view,2);b.build();step(2);self.assertEqual((b.s.view,b.s.row),(0,row))
  b.s.row=13;step(1);step(128);step(1)
  self.assertEqual((b.s.view,b.s.selector_row),(1,14));p=b.build()
  self.assertEqual([o.id for o in ops(p,1) if o.y>=32 and o.y<160],[62,64,66])
  step(2);self.assertEqual(b.s.view,3)
 def test_pool_exact_capacity_preview_extremes_and_disabled_owners(self):
  b=RenderBench(self.compiled);p=b.build();b.put(REQ+20,p.pool_used);b.build();b.put(REQ+20,p.pool_used-2);b.build(0)
  b=RenderBench(self.compiled);b.s.view=2
  for prefix in (0,1,0xffffffff):
   b.put(REQ+36,prefix);p=b.build();o=ops(p,9)[0]
   self.assertEqual(o.a,min(prefix,len(b.words[125])-1));self.assertEqual(b.get(POOL+o.offset+(o.units-1)*2,2),65535)
  b=RenderBench(self.compiled);b.s.snapshot.editable_rows=0;p=b.build()
  self.assertTrue(ops(p,8));self.assertTrue(all(o.flags&4 for o in ops(p,4)+ops(p,5)))
 def test_empty_confirmation_and_error_reasons_are_truthful(self):
  b=RenderBench(self.compiled);b.s.view=5;b.s.choice=1;p=b.build()
  self.assertIn(97,[o.id for o in ops(p,1)])
  for status,reason in ((2,105),(6,106),(7,107)):
   b.s.view=6;b.s.owner_status=status;p=b.build()
   self.assertIn(98,[o.id for o in ops(p,1)]);self.assertIn(reason,[o.id for o in ops(p,1)])
 def test_frame_changes_force_recomposition(self):
  b=RenderBench(self.compiled);b.s.view=2;b.s.row=5;p=b.build()
  b.s.draft.native.frame=19;q=b.build();self.assertEqual(b.dirty(p,q),(0x3fffff,1))
  b.s.row=0;r=b.build();self.assertEqual(b.dirty(q,r),(0x3fffff,1))
 def test_cross_view_chrome_forces_full_but_same_view_cursor_stays_partial(self):
  b=RenderBench(self.compiled);b.s.row=1;root=b.build()
  b.s.view=2;info=b.build();self.assertEqual(info.frame,0)
  b.s.view=1;b.s.selector_row=1;b.s.selector_origin=0
  b.s.selector_cursor=0;b.s.selector_pending=0;selector=b.build()
  self.assertEqual(selector.frame,0)
  self.assertEqual(b.dirty(info,selector),(0x3fffff,1),'empty body chrome changes between views')
  # Chrome identity is view-dependent even where semantic operations coincide.
  for old_view in range(7):
   for new_view in range(7):
    a=Plan.from_buffer_copy(bytes(root));a.view=old_view
    c=Plan.from_buffer_copy(bytes(root));c.view=new_view
    self.assertEqual(b.dirty(a,c),(0,0) if old_view==new_view else (0x3fffff,1))
  b.s.view=0;b.s.row=2;changed=b.build()
  rows,full=b.dirty(root,changed)
  self.assertEqual(full,0);self.assertNotIn(rows,(0,0x3fffff))
 def test_selector_origin_and_count_domains_refuse(self):
  b=RenderBench(self.compiled);b.s.view=1;b.s.selector_row=0;b.s.selector_origin=3;b.build(0)
  b=RenderBench(self.compiled);b.s.snapshot.shiny.counts[0]=13;b.build(0)
  b=RenderBench(self.compiled);b.s.snapshot.shiny.target=494;b.build(0)
 def test_search_charge_snapshot_and_pending_truth_without_mutation(self):
  b=RenderBench(self.compiled);b.s.view=3;b.s.row=13
  for charge in (0,39,40):
   b.s.snapshot.shiny.charge=charge;p=b.build()
   self.assertEqual([(o.a,o.b) for o in ops(p,2) if o.row==5],[(charge,40)])
  b.s.draft.shiny.target=25;p=b.build()
  self.assertEqual([(o.a,o.b) for o in ops(p,2) if o.row==5],[(0,40)])
  b.s.view=0;b.s.draft.shiny.search=1;p=b.build()
  self.assertIn(131,[o.id for o in ops(p,1) if o.row==13])
  b.s.draft.shiny.search=0;p=b.build();self.assertIn(41,[o.id for o in ops(p,1) if o.row==13])
 def test_scroll_retains_position_across_pro_hide_and_group_jumps(self):
  b=RenderBench(self.compiled);b.s.row=13;p=b.build();self.assertEqual(p.first,11)
  b.put(REQ+28,p.first);b.s.row=11;b.s.draft.shiny.mode=0;q=b.build()
  self.assertEqual(q.first,9);self.assertEqual([o.row for o in ops(q,3)],[11])
  b.s.row=6;r=b.build();self.assertEqual([o.row for o in ops(r,3)],[6]);self.assertLessEqual(r.first,8)
  b.s.row=0;t=b.build();self.assertEqual(t.first,1)
 def test_refusals_are_atomic(self):
  for field,value in [('view',7),('row',14),('notice',8),('search_row',3)]:
   b=RenderBench(self.compiled);b.build();setattr(b.s,field,value)
   before=bytes(b.u.mem_read(OUT,C.sizeof(Plan)))+bytes(b.u.mem_read(POOL,4096));b.build(0)
   self.assertEqual(bytes(b.u.mem_read(OUT,C.sizeof(Plan)))+bytes(b.u.mem_read(POOL,4096)),before)
  b=RenderBench(self.compiled);b.put(REQ+20,4);b.build(0)
  b=RenderBench(self.compiled);b.put(REQ+16,STATE);b.build(0)
 def test_dirty_each_buffer_semantic_values_and_partial_history(self):
  b=RenderBench(self.compiled);a=b.build();self.assertEqual(b.dirty(None,a),(0x3fffff,1))
  self.assertEqual(b.dirty(a,a),(0,0))
  b.s.row=1;c=b.build();mask,full=b.dirty(a,c)
  self.assertEqual(mask, sum(1<<i for i in (2,3,4,7,8,9,10,11)));self.assertEqual(full,0)
  c.pool_epoch+=1
  for o in c.ops:o.offset+=2
  self.assertEqual(b.dirty(c,c),(0,0))
  b.s.view=3;d=b.build();b.s.snapshot.shiny.charge=39;e=b.build()
  mask,full=b.dirty(d,e);self.assertEqual(mask,0xe0e00);self.assertEqual(full,0)
  self.assertEqual(b.dirty(e,e,0x1234),(0x1234,0))
  self.assertEqual(b.dirty(e,e,0x3fffff),(0x3fffff,1))
if __name__=='__main__':unittest.main()
