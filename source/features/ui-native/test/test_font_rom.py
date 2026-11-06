"""Pinned prepared native font proof. Real decode/copy, independent native
String + synchronous AddTextPrinter reference. FS transport boundaries alone
are seamed for the accepted reader. This is not native boot or scene evidence.
"""
import os,unittest,tempfile,json
from font_bench import *
from sgp12.blz import ndspy_load_arm9_sicuro
from test_heap_rom import NativeHeapBench,ROM_PINS,PINS
FONT_PINS=(
(0x02002ca8,0x220,'d5ba07247c61fa79834b8789613d751adcc18c96b27e33706692d14121dde720'),
(0x020021a0,0xaf0,'3a23cdd4068ce58a7097cd63fcdabb855fd0630e6b03b5480286a2bafdea128d'),
(0x02002fac,0x84,'a57af1a1679d768297fb1e91036aeb12e80cae698fabb00c7a67fad9394a5726'),
(0x020f56d8,0x38,'e268e11b5e689c4ee93f9f4412c5a489bb8aaa635d9488c0772282e3d383ed56'),
(0x02020358,0x160,'aff6694ebed356deda0601ad0c7363f2a5530d832abbf90967bd3bbebcf0594d'),
(0x0202604c,0xc4,'6e9d0f4fd3281db86d83c41d527f41878986cf72831a309978a7756e0825cbc5'),
(0x020262b4,0x20,'8af51df686eac9853e600c5b603e6a0b0e8483d843700da036aed8e7e0ec0e54'),
(0x0201dacc,0x117c,'1eb2b53ec4cedd47ba4d120a73f47d7061c30f940e95113f1e0c902411a885ac'),
(0x020200fc,0x1ec,'92571819995728c01e4b9721c1ad56f2afddef1f4b9c0ef6d5e44a06e00c86f7'),
(0x020204b8,8,'2a728730a3b6ac6c58f22730207a21ae03f7860446f4128180f935cd1a740f77'),
(0x02020548,0x18,'e679456f3566e219ce46c2083912259993c2797d40c7dd6f31c7c4209b395bcd'),
(0x02026354,0x58,'32404d1ad48f04eb0a0c0cbece6dcaa996afa9b045d443b97385962376a8b2f1'),
(0x020269a0,0x64,'bd331553d1ffeb59dfc72a590a0c97ac63a305c239137330a1dba5c3584e540d'),
(0x02026aa4,0x20,'6714fbd809850cc33dacd3af6bee27e7e371ea7b13626767301792f00e3785c0'),
(CPSR,12,'9c3668b7089a9adbfd85879f1c4689241aea4f8bd7af68fb26cdf12657eda6ee'))
TRANSIENT=((FFLAGS,2),(COLORS,6),(LOOKUP,512),(WORK,130))
class NativeFontBench(FontBench,NativeHeapBench):
    def __init__(self,compiled,fixture):
        self.raw,self.config,self.widths,self.glyphs,sections=fixture
        self.font_calls=[];self.fs_calls=[];self.fs_fault=None;self.open_length=None;self.close_failures=0
        self.paint=False;self.reference=False;self.visited=set();self.irq_spans=[];self.actual_irq_spans=[];self.mask_count=0;self.mask_start=None;self.ref_alloc=[];self.ref_free=[];self.reference_cursor=None
        NativeHeapBench.__init__(self,compiled,sections)
        self.allowed.extend(((READER,READER+R_SIZE),(LEASE,LEASE+12),(SLICE,SLICE+8),(FL,FL+0x1200),(FM-32,FM+0x800),(PIX,PIX+PIX_BYTES),*[(p,p+n) for p,n in TRANSIENT],(WORK+0xb4,WORK+0xb5),(0x021d1f6c,0x021d1f6e)))
        self.u.mem_write(CONFIG,self.config);self.archive_fixture();assert self.create()==1
        self.prepare_font();self.put(0x0210f6d8,0x020f56d8)
        # Remove real ARM9 leftover slots: this is prepared work, not boot.
        self.u.mem_write(WORK+0xa0,bytes(20));self.put(FM+16,0)
        assert self.start()==MORE
        for _ in range(60):
            result=ResourceBench.step(self)
            if result!=MORE:break
        assert result==OK
        self.guarded_memory();self.guards_ready=True;self.fixture_token=self.token()
    def store(self,u,access,p,n,v,data):
        self.store_contexts.append((p,n,v,u.reg_read(UC_ARM_REG_PC),u.reg_read(UC_ARM_REG_CPSR)))
        self.writes.append((p,n,v))
        allowed=[(FJ,FJ+152),(SC,SC+652),(FL,FL+88),(PIX,PIX+PIX_BYTES),*[(a,a+b) for a,b in TRANSIENT]] if self.paint else self.allowed
        assert any(a<=p<p+n<=b for a,b in allowed) or STACK-2048<=p<p+n<=STACK,f'unexpected store {p:08x}/{n}'
    def native_allowed(self,p):
        ranges=((0x020021a0,0x02002c90),(0x02002e7c,0x02002ec8),(0x02002fac,0x02003030),
          (0x02020358,0x020204b8),(0x0202604c,0x02026110),(0x020262b4,0x020262d4),(0x0201dacc,0x0201ec48))
        if any(a<=p<b for a,b in ranges):return True
        if not self.paint:
            ranges=((0x020200fc,0x020202e8),(0x020204b8,0x020204c0),(0x02020548,0x02020560),
             (0x02026354,0x020263ac),(0x020269a0,0x02026a04),(0x02026aa4,0x02026ac4),(0x0201a910,0x0201abec))
            if any(a<=p<b for a,b in ranges):return True
        return HeapBench.native_allowed(self,p) or CPSR<=p<CPSR+12
    def hook(self,u,p,n,data):
        self.instructions+=1;self.visited.add(p);sp=u.reg_read(UC_ARM_REG_SP);self.low=min(self.low,sp)
        if p in tuple(self.symbols.get(name,0)&~1 for name in ('rcrc','ffit')):
            assert not u.reg_read(UC_ARM_REG_CPSR)&128 and self.get(IME)==1,'CRC/preflight IRQ enabled'
        if u.reg_read(UC_ARM_REG_CPSR)&128:self.mask_count+=1
        elif self.mask_count:self.actual_irq_spans.append(self.mask_count);self.mask_count=0
        assert STACK-2048<=sp<=STACK,'stack envelope'
        if p==STOP:u.emu_stop();return
        if p==CPSR:return
        if p in (INIT,OPEN,READ,CLOSE,SEEK):
            assert p==CPSR or not self.paint,'no FS during paint';ResourceBench.hook(self,u,p,n,data);return
        assert p not in (0x0202551c,0x02096338,0x02002d40,0x02002d7c,0x02002db4,0x02025ec0,0x02025ed8),'forbidden native service'
        if p in (DISABLE,RESTORE):
            assert not u.reg_read(UC_ARM_REG_CPSR)&32 and sp%8==0
            if p==DISABLE:self.mask_start=self.instructions
            elif self.mask_start is not None:self.irq_spans.append(self.instructions-self.mask_start+6);self.mask_start=None
        if p in (CREATE,ALLOC,FREE,DESTROY,0x0201aa8c,0x0201ab0c):
            assert not self.paint,'no allocation/free during restricted paint'
            if p in (CREATE,ALLOC,FREE,DESTROY):self.calls.append((p,tuple(u.reg_read(r) for r in (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2))))
        if self.reference and p==0x0201aa8c:self.ref_alloc.append((u.reg_read(UC_ARM_REG_R0),u.reg_read(UC_ARM_REG_R1)))
        if self.reference and p==0x0201ab0c:
            ptr=u.reg_read(UC_ARM_REG_R0);self.ref_free.append(ptr)
            self.reference_cursor=(self.get(ptr),self.get(ptr+12,2),self.get(ptr+14,2))
        if p in (RENDER,GENERATE,0x0201dacc,0x02026068,0x02020410):
            self.font_calls.append(p)
            if p in (RENDER,GENERATE):assert sp%8==0 and u.reg_read(UC_ARM_REG_CPSR)&32,'native font entry ABI'
            if self.paint:
                assert u.reg_read(UC_ARM_REG_CPSR)&128,'native paint masked'
                assert not self.get(FFLAGS,2)&17,'native input flags disabled'
        assert CODE<=p<CODE+len(self.code) or self.native_allowed(p),f'unexpected execution {p:08x}'
    def address(self,p,*args):
        seed=[0x44440000+i for i in range(8)]
        for r,v in zip(REGS,seed):self.u.reg_write(r,v)
        for i,r in enumerate((UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3)):self.u.reg_write(r,args[i] if i<len(args) else 0)
        top=STACK-32
        self.u.mem_write(top,struct.pack('<8I',*(list(args[4:])+[0]*(8-len(args[4:])))))
        self.u.reg_write(UC_ARM_REG_SP,top);self.u.reg_write(UC_ARM_REG_LR,STOP|1)
        cpsr=self.u.reg_read(UC_ARM_REG_CPSR)&0xdf;ime=self.get(IME);start=self.instructions;self.low=top
        self.u.mem_write(STACK-2048,b'\xa5'*64)
        self.u.emu_start(p,STOP,count=2000000)
        assert self.u.reg_read(UC_ARM_REG_PC)==STOP,'finite instruction cap'
        assert self.u.reg_read(UC_ARM_REG_SP)==top and [self.u.reg_read(r) for r in REGS]==seed,'ABI regs/stack'
        assert self.u.reg_read(UC_ARM_REG_CPSR)&0xdf==cpsr and self.get(IME)==ime,'CPSR/IME restoration'
        assert bytes(self.u.mem_read(STACK-2048,64))==b'\xa5'*64,'DTCM canary'
        self.metrics.append((p,top-self.low,self.instructions-start));return self.u.reg_read(UC_ARM_REG_R0)
    def step(self,budget=8):
        before=bytes(self.u.mem_read(0x02000000,0x400000));dtcm=bytes(self.u.mem_read(0x027e0000,0x4000));globals_before=self.globals();self.paint=True
        try:ret=FontBench.step(self,budget)
        finally:self.paint=False
        assert self.globals()==globals_before,'exact transient restore'
        after_dtcm=bytes(self.u.mem_read(0x027e0000,0x4000));lo=self.low-64-0x027e0000;hi=STACK-0x027e0000
        assert dtcm[:lo]==after_dtcm[:lo] and dtcm[hi:]==after_dtcm[hi:],'DTCM outside actual stack unchanged'
        after=bytes(self.u.mem_read(0x02000000,0x400000))
        ranges=((FL,88),(FJ,152),(SC,652),(PIX,PIX_BYTES))
        for p,n in ranges:
            a=p-0x02000000;before=before[:a]+after[a:a+n]+before[a+n:]
        assert before==after,'whole mapped main RAM write delta'
        return ret
    def topology(self,heap):
        result=[bytes(self.u.mem_read(heap,56))]
        for off in (0x24,0x2c):
            node=self.get(heap+off);seen=set()
            while node:
                assert node not in seen and len(seen)<128;seen.add(node)
                result.append((node,bytes(self.u.mem_read(node,16))));node=self.get(node+12)
        return result
    def reset(self,memory):
        self.u.mem_write(0x02000000,memory);self.u.mem_write(TOKEN,self.fixture_token);self.ref_alloc=[];self.ref_free=[];self.reference_cursor=None
        self.u.reg_write(UC_ARM_REG_CPSR,0x5f);self.put(IME,1)
    def reference_run(self,words,x,y,colors):
        self.request(words=words,x=x,y=y,colors=colors)
        heap38=self.get(self.handles+16);string_before=self.topology(heap38),self.get(self.counts+76,2)
        string=self.address(0x02026355,len(words),38);assert string
        assert self.get(string,2)==len(words) and self.get(string+2,2)==0 and self.get(string+4)==0xb6f8d2ec and self.get(string+8,2)==65535
        self.address(0x020269a1,string,SGG+0x200)
        assert self.get(string+2,2)==len(words)-1 and self.address(0x02026aa5,string)==string+8
        assert bytes(self.u.mem_read(string+8,len(words)*2))==struct.pack('<%dH'%len(words),*words)
        before=self.topology(TEMPLATES[0][0]),self.get(self.counts,2)
        self.put(FM,0);self.put(FM+4,0x02026069);self.put(FM+16,self.root()+12288)
        self.reference=True
        try:ret=self.address(0x020200fd,WIN,0,string,x,y,255,(colors[0]<<16)|(colors[2]<<8)|colors[1],0)
        finally:self.reference=False
        assert ret==8 and self.ref_alloc==[(0,52)] and len(self.ref_free)==1,'one actual reference printer allocation/free'
        # Freed payload bytes can differ, but native topology/count must restore.
        assert (self.topology(TEMPLATES[0][0]),self.get(self.counts,2))==before,'Heap0 topology/count restored'
        pixels=self.pixels();cursor=(self.reference_cursor[0]-(string+8))//2,*self.reference_cursor[1:]
        self.address(0x02026381,string)
        assert self.get(string+4)==0xb6f8d2ed
        assert (self.topology(heap38),self.get(self.counts+76,2))==string_before,'String heap topology/count restored'
        self.put(FM,1);self.put(FM+4,0x02026111);self.put(FM+16,0)
        return pixels,cursor
class FontRomTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        canonical=SOURCE.parent/'local/experiments/balance493-2026-10-28'
        paths={l:Path(os.environ.get('SGP_UI_FONT_'+l,str(canonical/f'candidate-v4-{l}.nds'))) for l in ROM_PINS}
        missing=[l for l,p in paths.items() if not p.is_file()]
        if missing:
            msg='canonical V4 font inputs missing: '+','.join(missing)
            if os.environ.get('SGP_UI_FONT_REQUIRE_INPUTS')=='1':raise AssertionError(msg)
            raise unittest.SkipTest(msg)
        import ndspy.rom,ndspy.narc
        cls.fixtures={};cls.guides={};cls.receipts=[]
        for lang,p in paths.items():
            raw=p.read_bytes();assert (len(raw),hashlib.sha256(raw).hexdigest())==ROM_PINS[lang]
            rom=ndspy.rom.NintendoDSRom(raw);ss=ndspy_load_arm9_sicuro(rom).sections
            for a,n,want in (*PINS,*FONT_PINS):
                section=next(s for s in ss if s.ramAddress<=a<a+n<=s.ramAddress+len(s.data))
                assert hashlib.sha256(section.data[a-section.ramAddress:a-section.ramAddress+n]).hexdigest()==want,f'native pin {a:08x}'
            from sgp131.guide_content import read_content
            guide=bytes(ndspy.narc.NARC(rom.files[156]).files[829]);read_content(guide)
            guide_pins={'EN':(113534,'71e3bc3bba6a6ddaeb38ea47184619ace5ae718ac34601821a5576db4e474e3d'),
                        'IT':(119048,'fe193a7ea1205c5b6a7ca85160db6b803f2044748e3a05b710983f16cb1f44ce')}
            assert (len(guide),hashlib.sha256(guide).hexdigest())==guide_pins[lang]
            cls.guides[lang]=guide
            font=ndspy.narc.NARC(rom.files[145]).files[0]
            assert struct.unpack_from('<III4B',font)==(16,0x7f50,509,16,16,2,2)
            widths=bytes(font[0x7f50:]);glyphs=bytes(font[16:0x7f50])
            assert zlib.crc32(widths)==0x885ab7fc and zlib.crc32(glyphs)==0xa8cd6456
            resource,receipt=ui_resource.compile_resource(raw,{1:(299,0xe000,509,65535)})
            config=bytes.fromhex(receipt['config_hex'])
            cls.fixtures[lang]=(resource,config,widths,glyphs,[(s.ramAddress,bytes(s.data)) for s in ss if 0x02000000<=s.ramAddress<0x02400000])
        cls.tmp=tempfile.TemporaryDirectory(prefix='font-b-');cls.addClassCleanup(cls.tmp.cleanup)
        cls.compiled=compile_font(Path(cls.tmp.name))
    def test_native_reference_pixels_and_cursor_both_languages(self):
        zeros=(224,*range(493,510))
        matrix=[('eos',(65535,),0,0,(1,15,2)),('one',(1,65535),0,0,(1,15,2)),
          ('509',(509,65535),240,160,(1,15,2)),('all_zero',zeros+(65535,),0,0,(1,15,2)),
          ('mixed8',(509,299,509,333,509,478,509,321,509,65535),1,7,(3,15,4)),
          ('latin',(299,321,333,478,*range(289,299),383,391,392,395,401,408,65535),7,1,(1,15,2)),
          ('lf',(299,0xe000,333,65535),0,0,(1,0,15)),
          ('emptylines',(0xe000,299,0xe000,0xe000,65535),0,0,(15,0,1)),
          ('tenlf',(0xe000,)*10+(65535,),0,0,(1,15,2)),
          ('8plus10lf',(0xe000,)*10+(299,)*8+(65535,),0,0,(3,15,4)),
          ('lfboundary',(299,)*8+(0xe000,333,65535),0,0,(1,15,2)),
          ('lastrow',(299,65535),234,160,(1,15,2)),
          ('3batches',(299,)*25+(65535,),0,0,(1,15,2)),
          ('nontile',(299,333,478,65535),1,1,(3,15,4))]
        for lang,fixture in self.fixtures.items():
            b=NativeFontBench(self.compiled,fixture);baseline=bytes(b.u.mem_read(0x02000000,0x400000))
            for label,words,x,y,colors in matrix:
                with self.subTest(lang=lang,case=label):
                    b.reset(baseline);pixels,cursor=b.reference_run(words,x,y,colors)
                    b.reset(baseline);initial=b.pixels();before=b.globals()
                    self.assertEqual(b.acquire(),F_READY)
                    self.assertEqual(b.begin(words=words,x=x,y=y,colors=colors),F_ACTIVE)
                    self.finish_comparison(b,lang,label,words,initial,pixels,cursor,before)
    def finish_comparison(self,b,lang,label,words,initial,pixels,cursor,before,pool=0):
        pool_before=bytes(b.u.mem_read(pool,256)) if pool else None
        start=len(b.metrics);irq_start=len(b.actual_irq_spans);steps=0
        while True:
            result=b.step();steps+=1
            if result!=F_ACTIVE:break
            self.assertLess(steps,20)
        # M1: freeze endpoints immediately after the active loop, BEFORE DONE
        # and each separate teardown call. Counts are instructions, not cycles.
        end=len(b.metrics);irq_end=len(b.actual_irq_spans)
        paint_metrics=b.metrics[start:end];paint_irq=b.actual_irq_spans[irq_start:irq_end]
        self.assertEqual(len(paint_metrics),steps)
        self.assertTrue(all(m[0]==b.symbols['ui_font_step'] for m in paint_metrics))
        self.assertEqual(result,F_DONE);self.assertEqual(b.pixels(),pixels,'full native pixel equality')
        self.assertEqual((b.get(FJ+60),b.get(FJ+12,2),b.get(FJ+14,2)),cursor,'native consumed/x/y')
        self.assertEqual(b.globals(),before)
        if pool:self.assertEqual(bytes(b.u.mem_read(pool,256)),pool_before,'immutable buffer root')
        cleanup=[]
        def measured(label,call,want):
            mi=len(b.metrics);ii=len(b.actual_irq_spans)
            self.assertEqual(call(),want)
            values=b.metrics[mi:];self.assertEqual(len(values),1)
            cleanup.append(dict(call=label,stack=values[0][1],instructions=values[0][2],
              irq_instructions=max(b.actual_irq_spans[ii:],default=0)))
        calls=len(b.font_calls);measured('absorbing_DONE',b.step,F_DONE)
        self.assertEqual(len(b.font_calls),calls)
        measured('ui_font_release',b.release,F_DONE)
        if pool:measured('ui_free38_buffer',lambda:b.call('ui_free38',TOKEN,pool),1)
        measured('ui_res_release',lambda:b.call('ui_res_release',READER),1)
        measured('ui_heap38_destroy',b.destroy,1)
        self.receipts.append(dict(language=lang,case=label,units=len(words),steps=steps,
          sha256=hashlib.sha256(pixels).hexdigest(),changed_bytes=sum(a!=z for a,z in zip(initial,pixels)),
          phase='active_paint_only',stack=max(m[1] for m in paint_metrics),
          instructions=max(m[2] for m in paint_metrics),irq_instructions=max(paint_irq,default=0),
          cleanup=cleanup,cleanup_inclusive_aggregate=dict(stack=max(m[1] for m in b.metrics[start:]),
            instructions=max(m[2] for m in b.metrics[start:]),irq_instructions=max(b.actual_irq_spans[irq_start:],default=0))))
    def test_native_formatted_buffer_pixels_and_cursor_both_languages(self):
        # Class B only: authored strings encode with the private character map;
        # none are retail text. This is a fixture encoder, not a runtime formatter.
        charmap=Path(os.environ.get('SGP_UI_FONT_CHARMAP',str(SOURCE.parent/'local/tools/pokeheartgold/charmap.txt')))
        if not charmap.is_file():
            if os.environ.get('SGP_UI_FONT_REQUIRE_INPUTS')=='1':self.fail('private font charmap missing')
            self.skipTest('private font charmap missing')
        spec=importlib.util.spec_from_file_location('font_characters',SOURCE/'quality-audit/hgss_text.py')
        mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
        chars,_=mod.load_charmap(charmap);codes={v:k for k,v in chars.items() if 1<=k<=509}
        authored=('4294967295','12/14','40/40','1/4096 0.0244%','12/14 40/40')
        for lang,fixture in self.fixtures.items():
            b=NativeFontBench(self.compiled,fixture);baseline=bytes(b.u.mem_read(0x02000000,0x400000))
            for label in authored:
                with self.subTest(lang=lang,text=label):
                    words=tuple(codes[c] for c in label)+(65535,)
                    b.reset(baseline);pixels,cursor=b.reference_run(words,1,1,(1,15,2))
                    b.reset(baseline);initial=b.pixels();before=b.globals();pool=b.allocate_pool()
                    self.assertEqual(b.acquire(),F_READY)
                    b.buffer_request(pool,words,x=1,y=1,cap=1,policy=0)
                    self.assertEqual(b.call('ui_font_begin',FL,FJ,REQ),F_ACTIVE)
                    self.assertEqual((b.get(FJ+96),b.get(FJ+100),b.get(FJ+104)),(TO,3,pool))
                    self.finish_comparison(b,lang,'buffer '+label,words,initial,pixels,cursor,before,pool)
                    self.receipts[-1]['charmap_sha256']=hashlib.sha256(charmap.read_bytes()).hexdigest()
                    self.receipts[-1]['encoded_words']=words
                    if len(label)>8:self.assertGreater(self.receipts[-1]['steps'],1)
    def test_native_refusals_cancellation_and_initial_masks(self):
        for lang,fixture in self.fixtures.items():
            b=NativeFontBench(self.compiled,fixture);baseline=bytes(b.u.mem_read(0x02000000,0x400000))
            for mask,ime in ((128,1),(0,0)):
                b.reset(baseline);b.u.reg_write(UC_ARM_REG_CPSR,0x5f|mask);b.put(IME,ime)
                before=bytes(b.u.mem_read(0x02000000,0x400000));self.assertEqual(b.acquire(),F_DEFER)
                self.assertEqual(bytes(b.u.mem_read(0x02000000,0x400000)),before)
            b.reset(baseline);self.assertEqual(b.acquire(),F_READY)
            for kw in ({'x':235},{'y':161},{'words':(0xe000,)*11+(65535,)},{'words':(0,65535)}):
                before=b.pixels();calls=len(b.font_calls);self.assertEqual(b.begin(**kw),F_REFUSE)
                self.assertEqual(b.pixels(),before);self.assertEqual(len(b.font_calls),calls)
            self.assertEqual(b.begin(words=(299,)*25+(65535,)),F_ACTIVE)
            for mask,ime in ((128,1),(0,0)):
                b.u.reg_write(UC_ARM_REG_CPSR,0x5f|mask);b.put(IME,ime)
                before=bytes(b.u.mem_read(0x02000000,0x400000));self.assertEqual(b.step(),F_DEFER)
                self.assertEqual(bytes(b.u.mem_read(0x02000000,0x400000)),before)
            b.u.reg_write(UC_ARM_REG_CPSR,0x5f);b.put(IME,1)
            self.assertEqual(b.step(),F_ACTIVE);self.assertEqual(b.cancel(),F_CANCEL)
            before=b.pixels();self.assertEqual(b.step(),F_REFUSE);self.assertEqual(b.pixels(),before)
            self.assertEqual(b.release(),F_DONE)
    def test_native_borrowed_cache_lifetime_ref_current_and_corruption(self):
        for lang,fixture in self.fixtures.items():
            b=NativeFontBench(self.compiled,fixture);baseline=bytes(b.u.mem_read(0x02000000,0x400000))
            for corrupt,known in ((False,False),(True,True),(False,True)):
                b.reset(baseline);b.u.mem_write(EXT,b.glyphs)
                b.put(FM,0);b.put(FM+4,0x02026069);b.put(FM+16,EXT)
                owner=TO+32;b.u.mem_write(owner,struct.pack('<5I',EXT,32576,1,1,77))
                if corrupt:b.put(EXT,b.get(EXT,1)^1,1)
                self.assertEqual(b.acquire(owner if known else 0),F_REFUSE if corrupt or not known else F_READY)
                if corrupt or not known:self.assertEqual(b.get(READER+676),0);self.assertEqual(b.get(WORK+0xb4,1),1)
                else:
                    self.assertEqual(b.begin(),F_ACTIVE);self.assertEqual(b.step(),F_DONE)
                    b.put(WORK+0xb4,4,1);self.assertEqual(b.release(),F_DONE)
                    self.assertEqual(b.get(WORK+0xb4,1),3);self.assertEqual(b.get(FM+16),EXT)
    def test_native_owned_and_borrowed_mutations_hold_roots(self):
        for lang,fixture in self.fixtures.items():
            b=NativeFontBench(self.compiled,fixture);baseline=bytes(b.u.mem_read(0x02000000,0x400000))
            for borrowed in (False,True):
                for addr,value,n in ((WORKPTR,0,4),(WORK+0x9c,FM+4,4),(FM+16,b.root()+16,4),
                                     (WORK+0xb4,1,1),(FW,17,1),(READER+620,2,4)):
                    b.reset(baseline)
                    if borrowed:
                        b.u.mem_write(EXT,b.glyphs);b.put(FM,0);b.put(FM+4,0x02026069);b.put(FM+16,EXT)
                        b.u.mem_write(TO+32,struct.pack('<5I',EXT,32576,1,1,77))
                    self.assertEqual(b.acquire(TO+32 if borrowed else 0),F_READY)
                    self.assertEqual(b.begin(),F_ACTIVE);b.put(addr,value,n)
                    before=b.pixels(),b.get(READER+676),b.get(READER+680),b.get(WORK+0xb4,1)
                    calls=len(b.font_calls);self.assertEqual(b.step(),F_HOLD);self.assertEqual(len(b.font_calls),calls)
                    self.assertEqual(b.cancel(),F_CANCEL);self.assertEqual(b.release(),F_HOLD)
                    self.assertEqual((b.pixels(),b.get(READER+676),b.get(READER+680),b.get(WORK+0xb4,1)),before)
    def test_actual_uir1_label_and_validated_large_sgg1_root_share_printer(self):
        for lang,fixture in self.fixtures.items():
            b=NativeFontBench(self.compiled,fixture);baseline=bytes(b.u.mem_read(0x02000000,0x400000))
            guide=self.guides[lang];nc=struct.unpack_from('<H',guide,8)[0];entry=12+nc*12
            page_table=struct.unpack_from('<I',guide,entry+12)[0]
            page=struct.unpack_from('<I',guide,page_table)[0]
            offsets=[struct.unpack_from('<I',guide,20)[0],struct.unpack_from('<I',guide,entry+8)[0],struct.unpack_from('<I',guide,page+4)[0]]
            for offset in offsets:
                words=[]
                for i in range(128):
                    word=struct.unpack_from('<H',guide,offset+i*2)[0];words.append(word)
                    if word==65535:break
                words=tuple(words);self.assertEqual(words[-1],65535)
                b.reset(baseline);pixels,cursor=b.reference_run(words,0,0,(1,15,2))
                b.reset(baseline);b.u.mem_write(SGG,guide);self.assertEqual(b.acquire(),F_READY)
                b.u.mem_write(TO,struct.pack('<5I',2,SGG,len(guide),1,1))
                b.u.mem_write(REQ,struct.pack('<8I8B',WIN,FRONT,PIX_BYTES,TO,offset,len(words),0,SC,0,0,1,1,15,2,0,0))
                self.assertEqual(b.call('ui_font_begin',FL,FJ,REQ),F_ACTIVE)
                while b.step()==F_ACTIVE:pass
                self.assertEqual(b.get(FJ+68),F_DONE);self.assertEqual(b.pixels(),pixels)
                self.assertEqual((b.get(FJ+60),b.get(FJ+12,2),b.get(FJ+14,2)),cursor)
                self.assertEqual(bytes(b.u.mem_read(SGG,len(guide))),guide,'SGG1 immutable root')
                self.assertEqual(b.release(),F_DONE)
            b.reset(baseline);pixels,cursor=b.reference_run((299,0xe000,509,65535),0,0,(1,15,2))
            b.reset(baseline);self.assertEqual(b.acquire(),F_READY);self.assertEqual(b.begin(kind=1),F_ACTIVE)
            self.assertEqual(b.step(),F_DONE);self.assertEqual(b.pixels(),pixels)
            self.assertEqual((b.get(FJ+60),b.get(FJ+12,2),b.get(FJ+14,2)),cursor)
            self.assertEqual(b.release(),F_DONE)
    def test_native_semantic_mutants_are_killed_by_effects(self):
        mutants=(
          ('fcopy((void *)FWORK,scratch->glyph,130);','/* omitted glyph restore */','restore','exact transient restore'),
          ('x+=((const unsigned char *)l->widths)[c-1];','x+=((const unsigned char *)l->widths)[c];','index','native batch must finish'),
          ('j->consumed=end[i];','j->consumed=xs[i]==j->expected_x?j->consumed:end[i];','zero','zero width must consume'),
          ('l->state=UI_FONT_READY;','l->state=UI_FONT_READY;ui_res_drop(&l->resource);','root','one live root lease'),
          ('--FREF;','FREF=1;','ref','current reference decrement'),
          ('m[4]=l->prior_cache;','/* omitted prior cache restore */','tuple','exact prior tuple'),
          ('p->unk1b=255;','p->unk1b=255;p->speed=128;','printer','native batch must finish'),
          ('*(volatile unsigned short *)0x02111886&=(unsigned short)~17u;','/* speed flags not disabled */','flags','native input flags disabled'),
          ('||(w->baseTile&0x8000)','', '8bpp','8bpp refuses before paint'))
        for old,new,label,message in mutants:
            with tempfile.TemporaryDirectory(prefix='font-mutant-') as directory:
                compiled=compile_font(Path(directory),(old,new))
                for lang,fixture in self.fixtures.items():
                    with self.subTest(lang=lang,mutant=label):
                        b=NativeFontBench(compiled,fixture)
                        def scenario():
                            self.assertEqual(b.acquire(),F_READY)
                            self.assertEqual(b.get(READER+676),1,'one live root lease')
                            if label=='8bpp':
                                b.put(WIN+10,0x8000,2)
                                self.assertEqual(b.begin(),F_REFUSE,'8bpp refuses before paint');return
                            glyph=next(i+1 for i in range(508) if b.widths[i]!=b.widths[i+1])
                            words=(509,)*9+(65535,) if label=='zero' else (glyph,65535)
                            self.assertEqual(b.begin(words=words),F_ACTIVE)
                            if label=='zero':
                                self.assertEqual(b.step(),F_ACTIVE)
                                self.assertEqual(b.get(FJ+60),8,'zero width must consume')
                            else:self.assertEqual(b.step(),F_DONE,'native batch must finish')
                            b.put(WORK+0xb4,4,1);self.assertEqual(b.release(),F_DONE)
                            self.assertEqual(b.get(WORK+0xb4,1),3,'current reference decrement')
                            self.assertEqual(b.get(FM+16),0,'exact prior tuple')
                        with self.assertRaisesRegex(AssertionError,message):scenario()
if __name__=='__main__':
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(FontRomTests)
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    print(json.dumps(getattr(FontRomTests,'receipts',[]),indent=2))
    raise SystemExit(not result.wasSuccessful())
