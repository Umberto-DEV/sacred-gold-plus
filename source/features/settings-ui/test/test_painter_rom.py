"""Pinned prepared native CPU/reference proof; no scene installation/timing."""
import os,unittest
from painter_bench import *
from sgp12.blz import ndspy_load_arm9_sicuro
class NativePainterTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  from ndspy.rom import NintendoDSRom
  from ndspy.narc import NARC
  sys.path.insert(0,str(SOURCE))
  from sgp131 import ui_copy,ui_resource,ui_resource_verify
  from sgp131.test_ui_copy_rom import CHARMAP_SHA
  canonical=SOURCE.parent/'local/experiments/balance493-2026-10-28'
  charmap=Path(os.environ.get('SGP_PRET_SOURCE',str(SOURCE.parent/'local/tools/pokeheartgold')))/'charmap.txt'
  paths={l:Path(os.environ.get('SGP131_BASE_'+l,str(canonical/f'candidate-v4-{l}.nds'))) for l in nh.ROM_PINS}
  if not charmap.is_file() or any(not p.is_file() for p in paths.values()):
   if os.environ.get('SGP_UI_PAINTER_REQUIRE_INPUTS')=='1':raise AssertionError('required native inputs missing')
   raise unittest.SkipTest('canonical native painter inputs unavailable')
  assert hashlib.sha256(charmap.read_bytes()).hexdigest()==CHARMAP_SHA
  spec=importlib.util.spec_from_file_location('painter_codec',SOURCE/'features/options/tools/codifica_testo.py');codec=importlib.util.module_from_spec(spec);spec.loader.exec_module(codec);table,_=codec.carica_charmap(charmap)
  catalogue=ui_copy.load_catalogue((SOURCE/'sgp131/data/ui-copy.json').read_text())
  cls.fixtures={};cls.input_receipts={}
  for l,p in paths.items():
   raw=p.read_bytes();assert (len(raw),hashlib.sha256(raw).hexdigest())==nh.ROM_PINS[l]
   rom=NintendoDSRom(raw);sections=ndspy_load_arm9_sicuro(rom).sections
   for a,n,want in nb.BG_PINS+nh.PINS+nf.FONT_PINS:
    section=next(s for s in sections if s.ramAddress<=a<a+n<=s.ramAddress+len(s.data));assert hashlib.sha256(section.data[a-section.ramAddress:a-section.ramAddress+n]).hexdigest()==want
   font=bytes(NARC(rom.getFileByName('a/0/1/6')).files[0]);assert hashlib.sha256(font).hexdigest()=='9a17de3036f4aac8540163e560a60d83b7facde78d0ec41e688374fdbf669e73'
   widths=font[0x7f50:];authored,geometry=ui_copy.encode_catalogue(catalogue,l,lambda t:codec.codifica(t,table),widths)
   resource,receipt=ui_resource.compile_resource(raw,authored);assert ui_resource_verify.verify_resource(raw,resource,authored)==receipt
   cls.fixtures[l]=(resource,bytes.fromhex(receipt['config_hex']),widths,font[16:0x7f50],[(s.ramAddress,bytes(s.data)) for s in sections])
   cls.input_receipts[l]=dict(rom_sha256=hashlib.sha256(raw).hexdigest(),resource_receipt=receipt,preview_widths=geometry['entries']['PREVIEW_TEXT']['line_widths'])
  cls.tmp=tempfile.TemporaryDirectory(prefix='settings-painter-native-');cls.compiled,cls.detail=compile_painter(Path(cls.tmp.name))
 @classmethod
 def tearDownClass(cls):cls.tmp.cleanup()
 def test_native_all_twelve_footer_variants_have_intact_neutral_caps(self):
  # Literal native font measurements, independent of production descriptors.
  widths={'EN':(214,196,43,158,200,43),'IT':(215,189,64,174,216,64)}
  for lang,fixture in self.fixtures.items():
   b=NativePainterBench(self.compiled,fixture)
   for turn,view in enumerate((0,1,2,3,4,6,0)):
    b.s.view=view;b.s.row=1;b.s.selector_row=1;b.s.selector_cursor=0;b.s.selector_pending=0;b.s.choice=0
    p=b.build();o=ops(p,11)[0];runs=footer_runs(b,o);index=turn%2
    total=sum(r[4]+(13 if r[-1] else 9 if i+1<len(runs) else 0) for i,r in enumerate(runs))
    self.assertEqual(total,widths[lang][turn%6]);self.assertLessEqual(total,232)
    reference=b.full_reference(p,index);self.assertEqual(b.finish_paint(index),PREPARED)
    actual=b.frame_result(index);self.assertEqual(actual['pixels'],reference['pixels'])
    self.assertEqual(struct.unpack_from('<2H',actual['palette'],12),(0x56b5,0x35ad))
    canvas=actual['pixels']
    def color(xx,yy):
     off=(yy//8*30+xx//8)*32+yy%8*4+xx%8//2
     return canvas[off]>>(4*(xx%2))&15
    for words,x,y,colors,width,key in runs:
     if not key:continue
     self.assertEqual(width,6);self.assertEqual(colors,(2,1));left=x-5
     self.assertEqual([color(xx,y) for xx in range(left,left+16)],[2,2]+[6]*12+[2,2])
     self.assertEqual([color(xx,y+14) for xx in range(left,left+16)],[2,2]+[6]*12+[2,2])
     self.assertEqual([color(xx,y+15) for xx in range(left,left+16)],[2,2,2]+[7]*12+[2])
     self.assertEqual([color(xx,y+5) for xx in range(left+16,left+19)],[2,2,2])
    b.publish();b.writes.clear();b.store_contexts.clear();b.metrics.clear()
 def test_native_cross_view_chrome_both_buffer_parities(self):
  artifact=os.environ.get('SGP_UI_PAINTER_ARTIFACTS');records=[]
  for lang,fixture in self.fixtures.items():
   for parity in (0,1):
    with self.subTest(language=lang,parity=parity):
     b=NativePainterBench(self.compiled,fixture);b.s.row=1;failures=[]
     resource_before=hashlib.sha256(b.u.mem_read(b.root,b.root_bytes)).hexdigest()
     def press(key):
      b.u.mem_write(PSTATE,bytes(b.s))
      for held,new in ((0,0),(key,key)):
       b.call('settings_sample',PSTATE,held,1,0)
       result=b.call('settings_step',PSTATE,new,0)
      self.assertEqual(result,1,'real controller transition')
      b.s=State.from_buffer_copy(bytes(b.u.mem_read(PSTATE,C.sizeof(State))))
     for turn,(name,key,view) in enumerate((('root-before',0,0),('scene-info',2048,2),('root-return',2,0),('scene-selector',1,1))):
      if key:press(key)
      self.assertEqual(b.s.view,view);self.assertEqual(b.s.row,1)
      p=b.build();self.assertEqual(p.frame,0)
      index=parity^(turn&1)
      sources=bytes(p),bytes(b.u.mem_read(b.pool,256)),b.globals()
      reference=b.full_reference(p,index);start=len(b.metrics);jobs=b.paint_jobs
      self.assertEqual(b.finish_paint(index),PREPARED)
      actual=b.frame_result(index);mismatches=[k for k in actual if actual[k]!=reference[k]]
      self.assertEqual((bytes(b.u.mem_read(PDES,1184)),bytes(b.u.mem_read(b.pool,256)),b.globals()),sources)
      self.assertEqual(hashlib.sha256(b.u.mem_read(b.root,b.root_bytes)).hexdigest(),resource_before)
      self.assertEqual(b.get(PCTX+28),independent_closure(p,b.get(PCTX+24)))
      witness=struct.unpack_from('<H',actual['rgb555'],2*(108*256+108))[0]
      expected=struct.unpack_from('<H',reference['rgb555'],2*(108*256+108))[0]
      metrics=b.metrics[start:]
      record=dict(language=lang,parity=parity,turn=turn,case=name,view=view,index=index,
       initial_rows=b.get(PCTX+24),paint_rows=b.get(PCTX+28),full=b.get(PCTX+48),
       witness_rgb555=witness,reference_witness_rgb555=expected,reference_equal=not mismatches,mismatches=mismatches,
       plan_sha256=hashlib.sha256(bytes(p)).hexdigest(),hashes={k:hashlib.sha256(v).hexdigest() for k,v in actual.items()},
       max_paint_instructions=max(m[2] for m in metrics),max_paint_stack=max(m[1] for m in metrics),
       total_paint_instructions=sum(m[2] for m in metrics),paint_calls=len(metrics),native_jobs=b.paint_jobs-jobs)
      records.append(record);print(json.dumps(record,sort_keys=True),flush=True)
      if mismatches:failures.append((name,mismatches,witness,expected))
      if turn==3:
       self.assertEqual(expected,0x51a4,'independent selector blue at absolute108,108')
       if b.get(PCTX+48)!=1 or b.get(PCTX+28)!=FULL:failures.append(('view change requires FULL',b.get(PCTX+48),b.get(PCTX+28)))
       if artifact:save_artifact(Path(artifact),lang,'cross-view-selector-parity'+str(parity),actual['rgb555'],0)
      b.publish();self.assertEqual(b.get(PBG+76),index)
      b.writes.clear();b.store_contexts.clear();b.metrics.clear()
     self.assertEqual(b.call('settings_paint_retire',PCTX),UNCHANGED)
     self.assertEqual(b.call('ui_bg_retire',TOKEN,PBG,1),1);self.assertEqual(b.call('ui_bg_destroy',TOKEN,PBG,1),1)
     self.assertEqual(b.call('ui_font_release',fb.FL),fb.F_DONE)
     self.assertEqual(b.free(b.pool),1);self.assertEqual(b.call('ui_res_release',rb.READER),1);self.assertEqual(b.destroy(),1)
     if artifact:
      out=Path(artifact);out.mkdir(parents=True,exist_ok=True)
      (out/'cross-view-evidence.json').write_text(json.dumps(dict(records=records,inputs=self.input_receipts,binary=self.detail,source_sha256=source_pins()),indent=2))
     self.assertFalse(failures,'native cross-view chrome versus independent full: '+str(failures))
 def test_native_retained_search_numeric_pool_reuse_three_updates_per_buffer(self):
  records=[]
  for lang,fixture in self.fixtures.items():
   b=NativePainterBench(self.compiled,fixture);b.s.view=3;b.s.row=13;b.s.search_row=1
   b.s.snapshot.shiny.chain=40
   prior={}
   # Snapshot denominator is u16; use its actual maximum, not silently
   # truncated u32 input. The standalone formatter tests own the u32 domain.
   for turn,denominator in enumerate((0xffff,0xfffe,64,128,8,16)):
    with self.subTest(language=lang,turn=turn,denominator=denominator):
     b.s.snapshot.shiny.denominator=denominator;p=b.build();index=turn%2
     number=next(o for o in ops(p,2) if o.y==118)
     self.assertEqual(number.b,denominator)
     before=bytes(b.u.mem_read(b.pool,256)),bytes(p),b.globals()
     reference=b.full_reference(p,index);start=len(b.metrics)
     self.assertEqual(b.finish_paint(index),PREPARED);actual=b.frame_result(index)
     for key in actual:self.assertEqual(actual[key],reference[key],key)
     self.assertEqual((bytes(b.u.mem_read(b.pool,256)),bytes(b.u.mem_read(PDES,1184)),b.globals()),before)
     if index in prior:
      offset,epoch,units,version=prior[index]
      self.assertEqual(number.offset,offset);self.assertGreater(b.epoch,epoch)
      self.assertLess(number.units,units);self.assertEqual(b.get(PCTX+48),0,'retained same-view update')
      self.assertNotIn(b.get(PCTX+28),(0,FULL));self.assertGreater(b.version,version)
     self.assertEqual(b.get(PCTX+28),independent_closure(p,b.get(PCTX+24)))
     self.assertEqual(b.get(PCTX+92+index*1196+1184),b.version)
     self.assertEqual(b.get(PCTX+92+index*1196+1188),1)
     metrics=b.metrics[start:]
     rec=dict(language=lang,case='retained-search-number',turn=turn,index=index,denominator=denominator,
      offset=number.offset,units=number.units,pool_epoch=b.epoch,version=b.version,full=b.get(PCTX+48),
      initial_rows=b.get(PCTX+24),paint_rows=b.get(PCTX+28),reference_equal=True,
      hashes={key:hashlib.sha256(value).hexdigest() for key,value in actual.items()},
      plan_sha256=hashlib.sha256(bytes(p)).hexdigest(),pool_sha256=hashlib.sha256(before[0]).hexdigest(),
      max_paint_stack=max(m[1] for m in metrics),max_paint_instructions=max(m[2] for m in metrics))
     records.append(rec);print(json.dumps(rec,sort_keys=True),flush=True)
     prior[index]=(number.offset,b.epoch,number.units,b.version);b.publish()
     b.writes.clear();b.store_contexts.clear();b.metrics.clear()
   self.assertEqual(b.call('settings_paint_retire',PCTX),UNCHANGED)
   self.assertEqual(b.call('ui_bg_retire',TOKEN,PBG,1),1)
   self.assertEqual(b.call('ui_bg_destroy',TOKEN,PBG,1),1)
   self.assertEqual(b.call('ui_font_release',fb.FL),fb.F_DONE)
   self.assertEqual(b.free(b.pool),1);self.assertEqual(b.call('ui_res_release',rb.READER),1);self.assertEqual(b.destroy(),1)
  artifact=os.environ.get('SGP_UI_PAINTER_ARTIFACTS')
  if artifact:
   out=Path(artifact);out.mkdir(parents=True,exist_ok=True)
   (out/'numeric-evidence.json').write_text(json.dumps(dict(records=records,inputs=self.input_receipts,binary=self.detail,source_sha256=source_pins()),indent=2))
 def test_native_corpus_pixels_maps_palettes_rgb_and_artifacts_both_languages(self):
  artifact=os.environ.get('SGP_UI_PAINTER_ARTIFACTS');records=[]
  for lang,fixture in self.fixtures.items():
   b=NativePainterBench(self.compiled,fixture);base=bytes(b.s)
   # Fixed viewport1 makes y32/y54 and y120/y142 share tile rows6/17.
   cases=[('root',0,1,0xffffffff,{}),('root-next',1,1,0xffffffff,{}),
    ('shared-row6',0,1,0xffffffff,{'text':1}),('root-scene',1,1,0xffffffff,{'scene':1}),
    ('root-button',4,1,0xffffffff,{}),('root-frame',5,1,0xffffffff,{}),
    ('shared-row17',4,1,0xffffffff,{'button':1}),('root-frame19',5,1,0xffffffff,{'frame':19}),
    ('root-initial',0,0,0xffffffff,{}),('plus-boundary',6,4,0xffffffff,{}),
    ('long-label',8,8,0xffffffff,{}),
    ('classic-last',11,0,0xffffffff,{'mode':0}),('pro-last',13,0,0xffffffff,{}),
    ('long-selector',12,0,0xffffffff,{'view':1}),('search',13,0,0xffffffff,{'view':3}),
    ('disabled',13,0,0xffffffff,{'view':3,'disabled':1}),
    ('exit-confirm',13,0,0xffffffff,{'view':4}),('apply-confirm',13,0,0xffffffff,{'view':5}),
    ('error',13,0,0xffffffff,{'view':6}),('text-prefix0',0,0,0,{'view':2}),
    ('text-prefix1',0,0,1,{'view':2}),('frame0',5,0,0xffffffff,{'view':2}),
    ('text-full',0,0,0xffffffff,{'view':2,'text':2}),('frame19',5,0,0xffffffff,{'view':2,'frame':19}),
    ('frame-prefix-lf',5,0,-1,{'view':2,'frame':19})]
   for name,row,first,prefix,fields in cases:
    with self.subTest(language=lang,case=name):
     b.s=State.from_buffer_copy(base);b.s.row=row;b.s.view=fields.get('view',0)
     for f in ('text','scene','style','audio','button','frame'):
      if f in fields:setattr(b.s.draft.native,f,fields[f])
     if 'mode' in fields:b.s.draft.shiny.mode=fields['mode']
     if b.s.view==1:
      names=[];count=b.get(b.root+100)
      for identity,units,offset in struct.iter_unpack('<HHI',bytes(b.u.mem_read(b.root+48448,count*8))):
       if identity>4096:
        words=struct.unpack('<%dH'%units,b.u.mem_read(b.root+offset,units*2));names.append((sum(b.widths[g-1] for g in words[:-1]),identity-4096))
      longest=max(names)[1];b.s.snapshot.candidates[0][0]=longest
      b.s.selector_row=12;b.s.selector_origin=493;b.s.selector_cursor=1;b.s.selector_pending=longest
     if b.s.view==3:
      b.s.search_row=1;b.s.snapshot.shiny.denominator=0xffff;b.s.snapshot.shiny.chain=40
      if fields.get('disabled'):
       b.s.snapshot.editable_rows=0;b.s.snapshot.shiny.available=0;b.s.snapshot.shiny.denominator=64;b.s.snapshot.shiny.chain=0;b.s.snapshot.shiny.charge=0
     if b.s.view in (4,5):b.s.dirty_groups=7;b.s.draft.shiny.search=1;b.s.choice=2 if b.s.view==4 else 1
     if b.s.view==6:b.s.owner_status=2
     if prefix==-1:
      count=b.get(b.root+100)
      _,units,offset=next(e for e in struct.iter_unpack('<HHI',bytes(b.u.mem_read(b.root+48448,count*8))) if e[0]==125)
      words=struct.unpack('<%dH'%units,b.u.mem_read(b.root+offset,units*2));prefix=words.index(0xe000)+1 if 0xe000 in words else (units-1)//2
     p=b.build(first,prefix);index=0 if b.get(PBG+76)!=0 else 1
     pool_before=bytes(b.u.mem_read(b.pool,256));plan_before=bytes(p);resource_before=hashlib.sha256(b.u.mem_read(b.root,b.root_bytes)).hexdigest()
     reference=b.full_reference(p,index);before=b.globals();mi=len(b.metrics);jobs_before=b.paint_jobs
     self.assertEqual(b.finish_paint(index),PREPARED);actual=b.frame_result(index)
     for key in actual:self.assertEqual(actual[key],reference[key],key)
     self.assertEqual(b.globals(),before);self.assertEqual(bytes(b.u.mem_read(PDES,1184)),plan_before)
     self.assertEqual(bytes(b.u.mem_read(b.pool,256)),pool_before);self.assertEqual(hashlib.sha256(b.u.mem_read(b.root,b.root_bytes)).hexdigest(),resource_before)
     self.assertEqual(b.get(PCTX+28),independent_closure(p,b.get(PCTX+24)))
     paint_metrics=b.metrics[mi:];rowmask=b.get(PCTX+28)
     rec=dict(language=lang,case=name,index=index,version=b.version,operations=p.count,initial_rows=b.get(PCTX+24),paint_rows=rowmask,
      plan_sha256=hashlib.sha256(plan_before).hexdigest(),pool_sha256=hashlib.sha256(pool_before).hexdigest(),pool_epoch=b.epoch,
      pixel_sha256=hashlib.sha256(actual['pixels']).hexdigest(),map_sha256=hashlib.sha256(actual['map']).hexdigest(),rgb555_sha256=hashlib.sha256(actual['rgb555']).hexdigest(),
      palette_sha256=hashlib.sha256(actual['palette']).hexdigest(),reference_equal=True,
      max_paint_instructions=max(m[2] for m in paint_metrics),max_paint_stack=max(m[1] for m in paint_metrics),paint_calls=len(paint_metrics),total_paint_instructions=sum(m[2] for m in paint_metrics),native_jobs=b.paint_jobs-jobs_before,pool_used=p.pool_used)
     records.append(rec)
     if artifact and name in ('root','root-initial','plus-boundary','long-label','long-selector','search','disabled','exit-confirm','apply-confirm','error','frame0','frame19','text-prefix0','text-prefix1','text-full','shared-row6','shared-row17','frame-prefix-lf'):
      save_artifact(Path(artifact),lang,name,actual['rgb555'],rowmask if name.startswith('shared-row') else 0)
     b.publish();self.assertEqual(b.get(PBG+76),index)
     print(json.dumps(rec,sort_keys=True),flush=True)
     b.writes.clear();b.store_contexts.clear();b.metrics.clear()
   # All resources can be released only after font/callback/BG retirement.
   self.assertEqual(b.call('settings_paint_retire',PCTX),UNCHANGED)
   self.assertEqual(b.call('ui_bg_retire',TOKEN,PBG,1),1)
   self.assertEqual(b.call('ui_bg_destroy',TOKEN,PBG,1),1)
   self.assertEqual(b.call('ui_font_release',fb.FL),fb.F_DONE)
   self.assertEqual(b.free(b.pool),1);self.assertEqual(b.call('ui_res_release',rb.READER),1);self.assertEqual(b.destroy(),1)
  if artifact:
   out=Path(artifact);(out/'evidence.json').write_text(json.dumps(dict(records=records,inputs=self.input_receipts,binary=self.detail,source_sha256=source_pins(),native_prepared=True,installed_scene=False),indent=2))
   save_contact_sheets(out)

def source_pins():
 paths=[SOURCE/'features/settings-ui'/n for n in ('painter.h','painter.c','render.h','render.c','state.c','controller.h','catalog.h')]+[SOURCE/'features/ui-native'/n for n in ('heap.c','heap_internal.h','heap.h','resource.c','resource.h','font.c','font.h','bg.c','bg.h','native_abi.h')]+[HERE/n for n in ('painter_bench.py','test_painter.py','test_painter_rom.py')]
 return {str(p.relative_to(SOURCE)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}

def save_artifact(out,language,name,rgb555,mask):
 from PIL import Image,ImageDraw
 out.mkdir(parents=True,exist_ok=True)
 values=struct.unpack('<49152H',rgb555);rgb=bytes(v for n in values for v in ((n&31)*255//31,((n>>5)&31)*255//31,((n>>10)&31)*255//31))
 upper=Image.frombytes('RGB',(256,192),rgb);pair=Image.new('RGB',(256,384),'black');pair.paste(upper,(0,0));pair.save(out/f'{language}-{name}-1x.png')
 if mask:
  overlay=upper.copy();d=ImageDraw.Draw(overlay)
  for r in range(22):
   if mask>>r&1:d.rectangle((8,8+8*r,247,15+8*r),outline=(220,25,100),width=1)
  overlay.resize((768,576),Image.Resampling.NEAREST).save(out/f'{language}-{name}-dirty-3x.png')

def save_contact_sheets(out):
 from PIL import Image,ImageDraw
 for lang in ('EN','IT'):
  names=('root','long-selector','search','disabled','exit-confirm','apply-confirm','error','frame0','frame19','text-prefix0','text-prefix1','text-full')
  sheet=Image.new('RGB',(256*4,214*3),(24,24,24));d=ImageDraw.Draw(sheet)
  for i,name in enumerate(names):
   path=out/f'{lang}-{name}-1x.png'
   with Image.open(path) as im:sheet.paste(im.crop((0,0,256,192)),((i%4)*256,(i//4)*214))
   d.text(((i%4)*256+4,(i//4)*214+195),f'{lang} {name}',fill='white')
  sheet.resize((3072,1926),Image.Resampling.NEAREST).save(out/f'{lang}-contact-3x.png')
if __name__=='__main__':unittest.main()
