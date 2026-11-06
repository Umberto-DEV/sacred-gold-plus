"""Pinned EN/IT prepared native field-menu execution, not native boot.

Native menu control/OAM setters, Window/String/font and NNS bodies execute.
Transport of font glyph bytes and GPU uploads, audio and unrelated field
producers are declared seams. No ROM/save/emulator outputs are produced.
"""
import hashlib
import json
import os
import struct
import tempfile
import unittest
from pathlib import Path
import ndspy.rom
import ndspy.narc
import ndspy.lz10
from sgp12.blz import ndspy_load_arm9_sicuro, ndspy_load_overlays_sicuri
from fieldbook_bench import *
from test_heap_rom import NativeHeapBench, ROM_PINS, PINS as HEAP_PINS
import heap_bench as hb
from test_font_rom import FONT_PINS
from module_bench import instruction_set
from physical_bench import bl
from unicorn import UC_HOOK_MEM_WRITE, UC_HOOK_MEM_READ

BG, MAP4, MAP5, FM, WIDTHS = 0x022C0000,0x023B1000,0x023B1800,0x023B2000,0x023B2200
# Filled with immutable actual-V4 identities, independently checked EN and IT.
FIELD_PINS = ((33665508, 11808, '00f0a3f68196cae03a76657c336aee0cf4d30fc73390f87e75c5bb63dc712be5'), (33704824, 12, 'ea86246099d773d932012fdb4a4ccbd73c4f769211571d4550e7374ab8dbbad5'), (33566512, 124, 'a2ae309673013ad8e280034ba879df833725456ffa6d2ec33ec0dd8a3050bdab'), (33710352, 420, '43f0bc7dc80b7f4641e780b1979f34989a995a824a5da6335f5725c51f020a94'), (33683848, 8, 'eadc60d9c7c44e97941833fd7f38ff10b1f8bcecbff004e2cd27fd936e246aff'), (33883724, 8, 'e777ca5564a66a27c64283fab4fee8810b682ce2b5847607a9baab2b9bb5d4d2'), (33801340, 556, '806d7b83b2b576ed71c97c652d36e6f183e9f1629a96e5de06c8a02bbd729167'), (35613440, 100, '71830a68ff6d9e99a908b2de50973c83f98ec9ba420036c0546983ee42a02659'), (36020096, 12864, '0db89ca6c02e1b79636e9ed6732e879f3186565dae6a0bfba7f2cecc4a7cc118'), (34404216, 32, 'fa1f4703770b9818cac772820911ddadf50590aaae44d61538ea567a5769793d'))
FONT_SHA = '9a17de3036f4aac8540163e560a60d83b7facde78d0ec41e688374fdbf669e73'
SDK_PINS=((0x020D4858,0x5c,'10577c29bdbc6913eba507a029157099a73f377ee8d0e6617ff2cc72def5f8a5'),
          (0x020D48B4,0x58,'57113ad4afc8448b8c9d1ba20af6e7c256a0371644b9d88fce20dfa5166e379e'),
          (0x02024B78,0x34,'fd174dee09f45afd2ab9537262c0f33b54ffe62d126f0bada3c91ac82f2437ac'),
          (0x020CF15C,0x1c,'61ab3afc5c6ae41a7c3f2499a438f9d266ff777d3b102cd07f614429ca52fedd'),
          (0x0203DEF0,0x4c,'d0a9e22ed12a31ce727d5d5e3219739506e6f727bb5d05f46ebf8b261d574e7a'),
          (0x0203DF64,0x18,'deb28c2fe5b1a382872f826071abeb44980a7ab7d297a262b4a02dc1dddf4dfb'),
          (0x0203DFB4,0x2c,'ca54c6afc9443151a7cc603123634fb431b641aed30007393c8cc17f98f83f33'),
          (0x020505C0,8,'c22299aa3c5e5ab2d071e405063f4728a464328e80208b2af841dba29112ac77'),
          (0x020F62FC,12,'fe37de5d32409280a9c5a7572173c861687262715ea1ac135b18b6a963dfa345'))
ROOTS = [0x0201D40D,0x0201D521,0x0201D579,0x0201D979,0x02026355,0x02026381,
         0x02002F31,0x020200FD,0x02026111,0x020262B5,0x02024B79,0x0205064D,
         0x02050651,0x0201F989,0x0225BC85,0x0225A321,0x0225A8E9,0x0225B4AD,
         0x0225B399,0x0225B405,0x0225B4D9,0x0225C171,0x0203C47D,
         0x021F6B01,0x021F6B11,0x021F6B51,0x0225A2CD,
         0x0201AA8D,0x0201AB0D,hb.CREATE,hb.ALLOC,hb.FREE,hb.DISABLE,hb.RESTORE,
         0x020D3A9C,0x020D3A90,0x020B4E4C,
         # Audited indirect dispatch bodies: Window text, native glyph printer,
         # menu task case2 and input switch return branch.
         0x0201D685,0x0201D709,0x02020359,0x02020411,0x0225A847,
         # ARM SDK MIi_CpuClearFast / MIi_CpuCopyFast, reached by BX veneers.
         0x020D4858,0x020D48B4,
         # Text printer state0 jump-table arm (canonical uppercase has no controls).
         0x020022CD,0x02026187,0x0201DE67,0x0201D7F5,0x0201C32F,
         0x0201C19F,0x0201C193,0x0201C083,0x0201C077,0x020CF15C,
         0x020505C1,0x0203DEF1,0x0203DF65,0x0203DFB5]

class NativeFieldbookBench(FieldbookBench):
    def __init__(self,compiled,fixture):
        self.sections,self.graphics,self.font,self.labels,self.font_offset=fixture
        arm=[(p,d) for p,d in self.sections if 0x02000000<=p<0x021E0000 or p>=0x023C0000]
        h=NativeHeapBench((b'',{}),arm)
        raw=h.address(hb.ALLOC,hb.PARENT,0x18D00,4);assert raw
        assert h.address(hb.CREATE,raw,0x18D00,0)==raw
        for p,v in ((hb.BASE+16,raw),(hb.BASE+116+16,hb.PARENT),(hb.BASE+228+16,raw)):h.put(p,v)
        h.put(hb.BASE+662+8,4,1)
        memory=list(self.sections)+[(p,bytes(h.u.mem_read(p,n))) for p,n in
            [(hb.META,28),(hb.BASE,824),(0x021D84B0,16),(hb.PARENT,0x100000),*hb.TEMPLATES]]
        super().__init__(compiled,memory)
        self.native_events=[];self.uploads=[];self.glyph_reads=[];self.rendered=[];self.writes=[]
        self.string_result=None;self.label_buffer=None;self.pixel_plane=None;self.irq_run=0;self.irq_max=0
        self.previous_pc=None
        self.heap8=raw;self.ready=False;self.button_busy=False;self.show_task=True
        self.u.mem_map(0x06200000,0x10000)
        self.u.mem_write(LABELS,self.labels)
        self.u.mem_write(STATE,bytes(240));self.put(MENU+0x460,BG)
        self.u.mem_write(BG,bytes(360));self.put(BG,8)
        for i,mp in ((4,MAP4),(5,MAP5)):
            q=BG+8+i*44;self.put(q,mp);self.put(q+4,2048)
            self.u.mem_write(q+20,bytes([0,1,0,32]))
        self.put(0x04001008,0x0D02,2);self.put(0x0400100A,0x0E00,2)
        self.u.mem_write(MAP4,self.graphics[9][36:36+2048]);self.u.mem_write(MAP5,bytes(2048))
        self.u.mem_write(0x06200000,self.graphics[8][48:48+0x1800])
        self.u.mem_write(0x05000400,self.graphics[7][40:40+512])
        self.u.mem_write(MENU+0x4CC,self.graphics[14][40:40+64])
        for i in range(5):self.put(MENU+0x3b4+i*4,0x022B0900+i*0x100)
        self.put(FIELD+0x6c,1)
        self.put(FIELD,0x022A2800);self.u.mem_write(0x022A2800,bytes(16))
        self.put(0x0211188C,0x02111890);self.u.mem_write(0x02111890,bytes(0xB8))
        self.put(0x0211192C,FM);self.put(0x02111944,1,1)
        self.put(FM,1);self.put(FM+4,0x02026111)
        for off,v in ((8,3),(12,64),(0x54,0x023B2600),(0x58,0),(0x5c,16),(0x60,0x7f50),(0x64,509),
                      (0x68,0x02021010),(0x6c,0),(0x70,0x020262B5),(0x74,WIDTHS),(0x78,self.font_offset)):self.put(FM+off,v)
        self.u.mem_write(WIDTHS,self.font[0x7f50:]);self.put(0x0210F6D8,0x020F56D8);self.put(0x02111886,0,2)
        self.u.mem_write(0x021D1F6C,bytes(552))
        # Exactly declared future patches in the in-memory V4 fixture only.
        for a,name in [(0x0225A40E,'fieldbook_touch'),(0x0225A856,'fieldbook_touch'),
                       (0x0225A860,'fieldbook_dpad'),(0x0225A96E,'fieldbook_focus')]:
            self.u.mem_write(a,bl(a,self.symbols[name]))
        self.fetch=instruction_set(self.u,ROOTS,[(a,a+n) for a,n,_ in (*HEAP_PINS,*FONT_PINS,*FIELD_PINS,*SDK_PINS)])
        self.compiled_fetch=instruction_set(self.u,[a for n,a in self.symbols.items() if not n.startswith('$')],[(CODE,CODE+len(self.code))])
        self.allowed=[(STATE,STATE+32),(MENU,MENU+0x540),(FIELD,FIELD+0x200),(ENV,ENV+0x400),
            (0x022A2800,0x022A2810),(hb.BASE,hb.BASE+824),(hb.PARENT,hb.PARENT+0x18E00),*[(p,p+n) for p,n in hb.TEMPLATES],
            (0x021D84B0,0x021D84C0),(BG,BG+360),(MAP4,MAP4+2048),(MAP5,MAP5+2048),
            (0x022B0000,0x022B0E00),(0x022D0000,0x022D0240),(FM,FM+124),
            (0x02111890,0x02111948),(0x02111886,0x02111888),(0x021D1F6C,0x021D21C0),
            (0x04000208,0x0400020C),(0x04001050,0x04001056),(0x050004A0,0x050004C0),
            (0x05000600,0x050006E0),(0x06200000,0x06210000)]
        self.readable=self.allowed+[(a,a+n) for a,n,_ in (*HEAP_PINS,*FONT_PINS,*FIELD_PINS,*SDK_PINS)]+[
            (CODE,CODE+len(self.code)),(LABELS,LABELS+448),(TEMPLATE,TEMPLATE+16),
            (hb.META,hb.META+28),(SYS,SYS+0x70),(TM,TM+28),(TASK,TASK+28),(CONTROL_TASK,CONTROL_TASK+28),(CONTROL,CONTROL+16),
            (0x021D4158,0x021D415C),(0x0211188C,0x02111890),(0x0210F6D8,0x0210F6DC),
            (WIDTHS,WIDTHS+len(self.font)-0x7f50),(0x020F56D8,0x020F5710),
            (0x04001008,0x0400100C),(0x05000400,0x05000600)]
        self.u.hook_add(UC_HOOK_MEM_WRITE,self.store);self.u.hook_add(UC_HOOK_MEM_READ,self.read)
        self.ready=True
    def framebuffer(self):
        """CPU reconstruction of the prepared BG4/BG5 planes; OAM is a seam."""
        pixels=bytearray()
        tiles=bytes(self.u.mem_read(0x06200000,0x10000));palette=struct.unpack('<256H',bytes(self.u.mem_read(0x05000400,512)))
        maps=[struct.unpack('<1024H',bytes(self.u.mem_read(p,2048))) for p in (MAP4,MAP5)]
        for y in range(192):
            for x in range(256):
                color=0
                for entries in maps:
                    entry=entries[(y//8)*32+x//8]
                    if entries is maps[1] and entry==0:continue
                    px=(7-x%8) if entry&1024 else x%8;py=(7-y%8) if entry&2048 else y%8
                    byte=tiles[(entry&1023)*32+py*4+px//2];index=(byte>>(4*(px%2)))&15
                    if index:color=palette[(entry>>12)*16+index]
                pixels.extend(((color&31)*255//31,((color>>5)&31)*255//31,((color>>10)&31)*255//31))
        return bytes(pixels)
    def read(self,u,access,p,n,v,d):
        assert any(a<=p<p+n<=z for a,z in self.readable) or STACK-2016<=p<p+n<=STACK,f'read {p:08x}/{n} at {u.reg_read(UC_ARM_REG_PC):08x}'
        if 0x04000000<=p<0x05000000:
            assert p in (0x04000208,0x04001008,0x0400100A,0x04001050),f'undeclared MMIO read {p:08x}'
    def store(self,u,access,p,n,v,d):
        pc=u.reg_read(UC_ARM_REG_PC);self.writes.append((p,n,v,pc))
        assert any(a<=p<p+n<=z for a,z in self.allowed) or STACK-2016<=p<p+n<=STACK,f'write {p:08x}/{n} at {pc:08x}'
        if CODE<=pc<CODE+len(self.code):
            spans=[(STATE,STATE+32),(FIELD+0xd0,FIELD+0xd4),(ENV+0x26,ENV+0x28),
                   (ENV+0x354,ENV+0x358),(MENU+20,MENU+24),(0x050004a0,0x050004c0)]
            if self.label_buffer:spans.append(self.label_buffer)
            if self.pixel_plane:spans.append(self.pixel_plane)
            assert any(a<=p<p+n<=z for a,z in spans) or STACK-2016<=p<p+n<=STACK,f'authored write {p:08x}/{n} at {pc:08x}'
    def hook(self,u,p,n,d):
        previous=self.previous_pc;self.previous_pc=p
        self.instructions+=1;sp=u.reg_read(UC_ARM_REG_SP);self.low=min(self.low,sp)
        masked=bool(u.reg_read(UC_ARM_REG_CPSR)&128)
        self.irq_run=self.irq_run+1 if masked else 0;self.irq_max=max(self.irq_max,self.irq_run)
        if CODE<=p<CODE+len(self.code):assert not masked and self.get(IME)==1,'authored entry with IRQ enabled'
        assert STACK-2016<=sp<=STACK,'native stack envelope'
        if p==STOP:u.emu_stop();return
        if not hasattr(self,'fetch'):return
        args=[u.reg_read(r) for r in [UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3]]
        caller=u.reg_read(UC_ARM_REG_LR)&~1
        if previous is not None and CODE<=previous<CODE+len(self.code) and not CODE<=p<CODE+len(self.code) and CODE<=caller<CODE+len(self.code):
            assert sp%8==0,f'authored native call ABI8 {p:08x}'
        if p==0x02026354:self.string_result=u.reg_read(UC_ARM_REG_LR)&~1
        if p==self.string_result:
            self.label_buffer=(args[0],args[0]+72);self.string_result=None
        if p==0x02026380:self.label_buffer=None
        if p==0x0201D978:
            win=args[0];pixels=self.get(win+12);size=self.get(win+7,1)*self.get(win+8,1)*32
            if STACK-2016<=win<STACK:
                assert bytes(u.mem_read(win+4,6))==bytes([4,12,17,8,4,5]) and size==1024
                assert self.heap8+56<=pixels<pixels+size<=self.heap8+0x18d00
                self.pixel_plane=(pixels,pixels+size)
        if p==0x0201D520:self.pixel_plane=None
        if p in (0x0202551C,0x02096338,0x021E5900,0x021F6B50,0x02024950):raise AssertionError(f'forbidden native {p:08x}')
        if p in [a&~1 for a in ROOTS]:
            self.native_events.append((p,tuple(args)))
            assert sp%8==0,f'native ABI8 {p:08x}'
        if p==0x0200787C:
            source,offset,size,dest=args
            # The native File seeks in the NARC; self.font is its member0.
            # +0x78 contains that member's archive offset, not a glyph offset.
            assert source==0x023B2600 and offset>=self.font_offset+16 and offset+size<=self.font_offset+0x7f50 and size==64
            member=offset-self.font_offset
            self.u.mem_write(dest,self.font[member:member+size]);self.glyph_reads.append((offset,size));self.ret();return
        # Native SDK transfer boundaries: coherent RAM -> emulated VRAM/palette.
        transfers={0x020CFD70:0x05000600,0x020D0284:0x06200000,0x020D0344:0x06200000,
                   0x020CFF84:0x0620D000,0x020D0044:0x0620E000}
        if p in transfers:
            src,offset,size=args[:3];dest=transfers[p]+offset
            assert size and size<=2048 and dest+size<= (0x05000700 if p==0x020CFD70 else 0x06210000)
            self.u.mem_write(dest,bytes(self.u.mem_read(src,size)));self.uploads.append((p,src,dest,size));self.ret();return
        if p in (0x020D2894,0x020D28B8):self.ret();return # coherent cache seam
        if p==0x0202457C:
            modes=[self.get(0x022B0000+i*0x100+0x30) for i in range(9)]
            self.rendered.append(modes);self.ret();return # OAM/GPU submission only
        if p in (0x0200604C,0x0225BDFC,0x0225A530):self.ret();return # audio/registered-item widget
        if p==0x02050590:self.ret(int(self.show_task));return # outer task scheduler producer
        if p in (0x0203E13C,0x0200FB5C):self.ret(1);return # movement/fade producer
        if p in (0x02025204,0x02025224):self.ret(0xffffffff);return # unrelated native hitbox table input
        if p==0x0205C6D4:self.ret(0);return # avatar movement producer
        if p in (0x0203DF8C,0x0203C3CC):self.ret(0);return # field availability producer
        if p==0x0207879C:self.ret(0);return # unrelated native touch-widget save getter (no hit)
        if p==0x0203C460:self.ret();return # outer field menu close boundary
        if p==0x021E636C:
            assert self.get(STATE+4)==self.get(STATE+8)==self.get(STATE+12)==0,'no overlay roots at retirement'
            self.native_events.append((p,tuple(args)));self.ret();return # parent retirement boundary
        if p==0x02006FF8:
            assert args[:2]==[1,2];self.native_events.append((p,tuple(args)));self.ret(1);return # overlay transport, never old54
        if p==0x0200724C:
            assert args[2]==11 and args[0] in (TEMPLATE,0x02206378)
            if args[0]==TEMPLATE:assert args[1]==0
            self.native_events.append((p,tuple(args)));self.ret(0x022A2810);return # app manager allocation/scheduling
        assert p in self.fetch or p in self.compiled_fetch,f'undeclared native instruction {p:08x}'

class FieldbookRomTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        paths={l:Path(os.environ.get('SGP_FIELDBOOK_'+l,str(SOURCE.parent/'local/experiments/balance493-2026-10-28'/f'candidate-v4-{l}.nds'))) for l in ROM_PINS}
        # Existing wrong inputs are failures even when another optional input is missing.
        for l,p in paths.items():
            if p.exists():
                with p.open('rb') as f:digest=hashlib.file_digest(f,'sha256').hexdigest()
                assert (p.stat().st_size,digest)==ROM_PINS[l],f'V4 {l} identity'
        missing=[l for l,p in paths.items() if not p.is_file()]
        if missing:
            msg='canonical fieldbook inputs missing: '+','.join(missing)
            if os.environ.get('SGP_FIELDBOOK_REQUIRE_INPUTS')=='1':raise AssertionError(msg)
            raise unittest.SkipTest(msg)
        cmap=Path(os.environ.get('SGP_PRET_SOURCE',str(SOURCE.parent/'local/tools/pokeheartgold')))/'charmap.txt'
        if not cmap.is_file():
            if os.environ.get('SGP_FIELDBOOK_REQUIRE_INPUTS')=='1':raise AssertionError('canonical charmap missing')
            raise unittest.SkipTest('canonical charmap missing')
        spec=importlib.util.spec_from_file_location('fieldbook_codec',SOURCE/'features/options/tools/codifica_testo.py')
        codec=importlib.util.module_from_spec(spec);spec.loader.exec_module(codec);table,_=codec.carica_charmap(cmap)
        cls.fixtures={};cls.metrics=[];cls.observations=[]
        for lang,p in paths.items():
            r=ndspy.rom.NintendoDSRom.fromFile(p);sections=[(s.ramAddress,bytes(s.data)) for s in ndspy_load_arm9_sicuro(r).sections if 0x02000000<=s.ramAddress<0x02400000]
            sections += [(o.ramAddress,bytes(o.data)) for o in ndspy_load_overlays_sicuri(r,[1,27]).values()]
            for a,n,want in (*HEAP_PINS,*FONT_PINS,*FIELD_PINS,*SDK_PINS):
                base,data=next((base,data) for base,data in sections if base<=a<a+n<=base+len(data))
                assert hashlib.sha256(data[a-base:a-base+n]).hexdigest()==want,f'{lang} native pin {a:08x}'
            arc=ndspy.narc.NARC(r.getFileByName('a/0/1/4'));graphics={i:ndspy.lz10.decompress(arc.files[i]) if arc.files[i][0]==0x10 else bytes(arc.files[i]) for i in (7,8,9,14)}
            font=bytes(ndspy.narc.NARC(r.files[145]).files[0]);assert hashlib.sha256(font).hexdigest()==FONT_SHA
            font_archive=bytes(r.files[145]);btnf=16+struct.unpack_from('<I',font_archive,20)[0]
            fimg=btnf+struct.unpack_from('<I',font_archive,btnf+4)[0]
            font_offset=fimg+8+struct.unpack_from('<I',font_archive,28)[0]
            assert font_archive[fimg:fimg+4]==b'GMIF' and font_archive[font_offset:font_offset+len(font)]==font,'native FAT member offset'
            # Exact inherited field label: the successor must uppercase it.
            words=codec.codifica('Guida' if lang=='IT' else 'Guide',table)
            labels=struct.pack('<H',2)+struct.pack('<%dH'%len(words),*words)
            cls.fixtures[lang]=(sections,graphics,font,labels,font_offset)
        cls.temp=tempfile.TemporaryDirectory(prefix='fieldbook-native-');cls.addClassCleanup(cls.temp.cleanup)
        cls.compiled=compile_fieldbook(cls.temp.name)
    @classmethod
    def tearDownClass(cls):
        proof=os.environ.get('SGP_FIELDBOOK_PROOF_DIR')
        if proof:
            Path(proof,'fieldbook-native-observations.json').write_text(json.dumps({
                'payload_bytes':len(cls.compiled[0]),'payload_sha256':hashlib.sha256(cls.compiled[0]).hexdigest(),
                'metrics':cls.metrics,'observations':cls.observations,
                'native_pins':(*HEAP_PINS,*FONT_PINS,*FIELD_PINS,*SDK_PINS)},indent=2)+'\n')
    def record(self,lang,b):
        self.metrics.extend((lang,*m) for m in b.metrics)
        self.observations.append({'language':lang,'max_irq_masked_instructions':b.irq_max,
            'glyph_reads':len(b.glyph_reads),'uploads':len(b.uploads),'submissions':len(b.rendered),
            'string_news':sum(p==0x02026354 for p,args in b.native_events),
            'string_deletes':sum(p==0x02026380 for p,args in b.native_events),
            'window_adds':sum(p==0x0201d40c for p,args in b.native_events),
            'window_removes':sum(p==0x0201d520 for p,args in b.native_events)})
    def test_native_constructor_label_window_font_and_heap_counts(self):
        for lang,fixture in self.fixtures.items():
            b=NativeFieldbookBench(self.compiled,fixture)
            before=b.get(hb.BASE+340,2),b.get(hb.BASE+340+16,2)
            b.call('fieldbook_create',MENU)
            self.assertEqual(b.get(STATE+4),MENU)
            self.assertEqual((b.get(hb.BASE+340,2),b.get(hb.BASE+340+16,2)),before)
            self.assertGreater(len(b.glyph_reads),0)
            self.assertEqual(bytes(b.u.mem_read(MENU+0x464,6)),bytes([5,11,21,9,2,4]))
            self.record(lang,b)
    def test_native_focus_and_real_render_submission(self):
        for lang,fixture in self.fixtures.items():
            b=NativeFieldbookBench(self.compiled,fixture);b.call('fieldbook_create',MENU)
            b.put(SYS+0x48,16);b.call('fieldbook_dpad',MENU)
            self.assertEqual([b.get(0x022B0000+i*0x100+0x30) for i in range(9)],[1]*9)
            b.put(SYS+0x48,0);b.call('fieldbook_frame',TASK,MENU)
            self.assertEqual(b.rendered[-1],[1]*9)
            # No unchanged-frame allocation or font work.
            before=len(b.uploads),len(b.glyph_reads),len([p for p,args in b.native_events if p==0x0201d40c])
            b.call('fieldbook_frame',TASK,MENU)
            self.assertEqual((len(b.uploads),len(b.glyph_reads),len([p for p,args in b.native_events if p==0x0201d40c])),before)
            self.record(lang,b)
    def test_native_book_selection_clears_palette_even_for_retired_slots(self):
        for lang,fixture in self.fixtures.items():
            for previous,key in ((3,16),(6,128)):
                b=NativeFieldbookBench(self.compiled,fixture);b.call('fieldbook_create',MENU)
                b.put(MENU+20,previous)
                # Even when slot availability drops to zero, a stale OBJ
                # palette must lose its previous selected colour.
                b.put(MENU+0x470+8*previous,0,1)
                b.u.mem_write(0x05000600+32*previous,b'\xff\x7f'*16)
                b.put(SYS+0x48,key);b.call('fieldbook_dpad',MENU)
                self.assertEqual(bytes(b.u.mem_read(0x05000600+32*previous,32)),
                                 bytes(b.u.mem_read(MENU+0x4cc,32)))
                self.assertEqual([b.get(0x022B0000+i*0x100+0x30) for i in range(9)],[1]*9)
    def test_native_press_orders_cancel_and_resident_return(self):
        self.pending_proofs=[]
        for lang,fixture in self.fixtures.items():
            for first in ('menu','task','touch'):
                b=NativeFieldbookBench(self.compiled,fixture);b.call('fieldbook_create',MENU)
                b.put(SYS+0x48,16);b.call('fieldbook_frame',TASK,MENU)
                b.put(SYS+0x48,1)
                if first=='menu':b.call('fieldbook_frame',TASK,MENU)
                pending_start=len(b.rendered)
                if first=='touch':
                    b.put(SYS+0x48,0);b.put(SYS+0x60,120,2);b.put(SYS+0x62,150,2);b.put(SYS+0x64,1,2)
                    b.call('fieldbook_frame',TASK,MENU)
                self.assertEqual(b.call('fieldbook_task_input',TM),0)
                self.assertEqual(b.get(FIELD+0xd0,2),32)
                b.put(SYS+0x48,0);b.put(SYS+0x64,0,2)
                remaining=b.get(STATE+28)
                self.assertEqual(remaining,8 if first=='touch' else 9)
                for _ in range(remaining):
                    self.assertEqual(b.call('fieldbook_task_input',TM),0)
                    b.call('fieldbook_frame',TASK,MENU)
                pending=b.rendered[pending_start:]
                self.assertEqual(len(pending),9,'exact pending submission delta')
                self.assertEqual(pending,[[1]*9 for _ in range(9)],'every pending sprite semi mode')
                self.pending_proofs.append({'language':lang,'dispatch':first,
                    'submissions':len(pending),'sprite_modes':pending})
                self.assertEqual(b.call('fieldbook_task_input',TM),1)
                self.assertEqual(b.get(MENU+0x51c)&32,0)
                self.assertEqual(b.get(ENV+0x354),b.symbols['fieldbook_launch'])
                b.call('fieldbook_launch',TM)
                self.assertIn((TEMPLATE,0,11),[args[:3] for p,args in b.native_events if p==0x0200724c])
                b.put(0x022A2800+4,0);b.call('fieldbook_return',TM)
                self.assertEqual(b.get(ENV+0x26,2),15)
                self.assertIn((1,2),[args[:2] for p,args in b.native_events if p==0x02006ff8])
                self.record(lang,b)
            for key in (2,1024):
                b=NativeFieldbookBench(self.compiled,fixture);b.call('fieldbook_create',MENU)
                b.put(SYS+0x48,16);b.call('fieldbook_dpad',MENU)
                b.put(SYS+0x48,1);b.call('fieldbook_task_input',TM)
                b.put(SYS+0x48,key);self.assertEqual(b.call('fieldbook_task_input',TM),1)
                self.assertEqual(b.get(FIELD+0xd0,2),0)
                self.assertEqual(b.get(ENV+0x26,2),16)
                self.record(lang,b)
    def test_native_image_geometry_palette_label_and_immutable_options(self):
        for lang,fixture in self.fixtures.items():
            b=NativeFieldbookBench(self.compiled,fixture)
            b.u.mem_write(0x06200000+0x162*32,b'\xa7'*(18*32))
            options=bytes(b.u.mem_read(0x06200000+0x162*32,18*32))
            before4=bytes(b.u.mem_read(MAP4,2048));before5=bytes(b.u.mem_read(MAP5,2048))
            labels=bytes(b.u.mem_read(LABELS,len(b.labels)))
            b.call('fieldbook_create',MENU)
            self.assertEqual((b.get(0x04001008,2)&3,b.get(0x0400100a,2)&3),(2,0))
            self.assertEqual({w>>12 for w in struct.unpack('<1024H',before4)},{0})
            words=(305,319,307,302,299 if lang=='IT' else 303,65535)
            self.assertEqual(b.glyph_reads,[(b.font_offset+16+(c-1)*64,64) for c in words[:-1]])
            rows=[]
            for y in range(16):
                rows.append(any(b.get(0x022D0000+((y//8)*9+x//8)*32+(y%8)*4+(x%8)//2,1) for x in range(72)))
            self.assertGreaterEqual(sum(rows),10,'whole native uppercase glyph height')
            self.assertEqual(bytes(b.u.mem_read(LABELS,len(b.labels))),labels)
            for addr,before,x,y,w,h in ((MAP4,before4,12,17,8,4),(MAP5,before5,11,21,9,2)):
                after=bytes(b.u.mem_read(addr,2048))
                for j in range(32):
                    for i in range(32):
                        p=2*(j*32+i)
                        if not (x<=i<x+w and y<=j<y+h):self.assertEqual(after[p:p+2],before[p:p+2])
            self.assertEqual(bytes(b.u.mem_read(0x06200000+0x162*32,18*32)),options)
            # Independently read the tiled native upload; all 2048 pixels have
            # bounded 4bpp coordinates, background corners and a two-pixel frame.
            def pixel(x,y):
                p=0x06200000+0x186*32+((y//8)*8+x//8)*32+(y%8)*4+(x%8)//2
                return (b.get(p,1)>>(4*(x%2)))&15
            self.assertEqual([pixel(x,y) for x,y in ((8,6),(47,6),(8,31),(47,31))],[1]*4)
            self.assertEqual([pixel(x,y) for x,y in ((9,7),(46,7),(9,30),(46,30))],[9]*4)
            native_pal=struct.unpack('<16H',b.graphics[14][40:72]);bg=b.get(0x05000406,2)
            dim=lambda c:sum(((((c>>s)&31)*6+((bg>>s)&31)*9)>>4)<<s for s in (0,5,10))
            self.assertEqual(b.get(0x050004b2,2),dim(native_pal[9]))
            b.put(SYS+0x48,16);b.call('fieldbook_dpad',MENU);b.put(SYS+0x48,0);b.call('fieldbook_frame',TASK,MENU)
            self.assertEqual(b.get(0x050004b2,2),0x0c7e)
            self.assertTrue(any(b.u.mem_read(0x06200000+0x174*32,18*32)))
            proof=Path(os.environ['SGP_FIELDBOOK_PROOF_DIR']) if os.environ.get('SGP_FIELDBOOK_PROOF_DIR') else None
            if proof:
                from PIL import Image
                proof.mkdir(parents=True,exist_ok=True)
                Image.frombytes('RGB',(256,192),b.framebuffer()).save(proof/f'fieldbook-native-{lang}.png')
            self.record(lang,b)
    def test_native_two_effect_omission_mutants_with_green_control(self):
        fixture=self.fixtures['EN']
        def focus(compiled):
            b=NativeFieldbookBench(compiled,fixture);b.call('fieldbook_create',MENU)
            b.put(SYS+0x48,16);b.call('fieldbook_dpad',MENU)
            return [b.get(0x022B0000+i*0x100+0x30) for i in range(9)]
        def cancel(compiled):
            b=NativeFieldbookBench(compiled,fixture);b.call('fieldbook_create',MENU)
            b.put(SYS+0x48,16);b.call('fieldbook_dpad',MENU)
            b.put(SYS+0x48,1);b.call('fieldbook_task_input',TM)
            b.put(SYS+0x48,2);b.call('fieldbook_frame',TASK,MENU)
            return b.get(FIELD+0xd0,2)
        self.assertEqual(focus(self.compiled),[1]*9);self.assertEqual(cancel(self.compiled),0)
        for mutation,probe,wrong in ((('if(s)Mode(s,1);','(void)s;'),focus,[0]*9),
            (('U16(fs,0xd0)=0;','(void)fs;'),cancel,32)):
            with tempfile.TemporaryDirectory(prefix='fieldbook-native-mutant-') as directory:
                self.assertEqual(probe(compile_fieldbook(directory,mutation=mutation)),wrong)
