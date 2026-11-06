"""Prepared actual native FS/NNS with new SGG1 generated only in RAM.
Only cartridge transport/arbitration is seamed. No FS success facades, Wait,
stack FSFile, ROM build, exported data, scene or hardware/cache claim.
"""
import os,hashlib,unittest
from guide_resource_bench import *
from sgp12.blz import ndspy_load_arm9_sicuro
from test_heap_rom import NativeHeapBench,ROM_PINS,PINS as HEAP_PINS
from test_resource_rom import FS_PINS,TRANSPORT,LOCK,UNLOCK,PULLED,SLEEP,CALLBACK
from module_bench import instruction_set
from test_bg_rom import NATIVE_INSTRUCTIONS as CHECKED_NATIVE_BG
RETURN=STOP+0x40
class NativeGuideBench(GuideBench,NativeHeapBench):
    def __init__(self,compiled,fixture):
        self.checked=False;self.peak_ledger=0;self.fs_calls=[];self.close_failures=0;self.open_fault=False;self.short=False;self.delay=False;self.pending=None;self.callback_return=None;self.failure_return=None;self.closes=[];self.transports=[];self.visited=set();self.fs_sp=[];self.close_returns=[]
        sections,fat,fnt,data,cfg,raw,graph=fixture
        self.data,self.cfg,self.raw,self.graph=data,cfg,raw,graph
        NativeHeapBench.__init__(self,compiled,sections)
        self.create(0x40000);self.app=self.alloc(1024);self.reader=self.app+32;self.lease=self.app+352
        self.u.mem_write(CFG,cfg);self.allowed.extend(((OUT,OUT+128),(ARC+12,ARC+40)))
        self.u.mem_write(FAT,fat);self.u.mem_write(FNT,fnt);self.archive()
        self.put(0x021e3628,ARC);self.put(0x021e362c,ARC);self.put(0x021e3630,0);self.put(0x021e3634,0)
        regions=[(a,a+n) for a,n,h in (*HEAP_PINS,*FS_PINS)]
        roots=[INIT,FAST,ASYNC,0x020d8104,CLOSE,SEEK,CPSR,CALLBACK,0x020d7edc,CREATE,ALLOC,FREE,DESTROY,DISABLE,RESTORE]
        # Explicit command-table handlers are indirect edges, not literal roots.
        roots += [0x020d7340,0x020d73c0,0x020d73e8,0x020d6b94,0x020d7484,0x020d84c4,0x020d8514,0x020d850c]
        self.fetch=instruction_set(self.u,roots,regions)
        # Reuse exact already-audited NNS instruction entries, not broad bodies or pools.
        self.fetch.update(p for p in CHECKED_NATIVE_BG if 0x020b4b68<=p<0x020b556c)
        self.checked=True
        self.u.mem_write(self.app,b'\0'*1024)
        self.u.mem_write(self.reader-16,b'\x96'*16);self.u.mem_write(self.reader+292,b'\x69'*16);self.guard_setup()
    def store(self,u,access,p,n,v,data):
        if p==self.counts+76:self.peak_ledger=max(self.peak_ledger,v)
        super().store(u,access,p,n,v,data)
    def native_allowed(self,p):return p in self.fetch if self.checked else NativeHeapBench.native_allowed(self,p)
    def callback(self,cb,arg,ret):
        assert cb==CALLBACK and arg==ARC and self.callback_return is None
        self.callback_return=ret;self.u.reg_write(UC_ARM_REG_R0,arg);self.u.reg_write(UC_ARM_REG_LR,RETURN);self.u.reg_write(UC_ARM_REG_PC,cb)
    def complete(self,error=0):
        assert self.pending is not None
        cb,arg,dst,data=self.pending;self.pending=None;self.u.mem_write(dst,data)
        self.address(0x020d7edc,ARC,error) if error else self.address(CALLBACK,ARC)
    def hook(self,u,p,n,data):
        check_compiled(self.code,p,n)
        if self.failure_return==p:
            self.failure_return=None;self.put(ARC+28,self.get(ARC+28)&~0x80)
        if self.close_returns and self.close_returns[-1][0]==p:
            ret,file=self.close_returns.pop();self.closes.append((file,u.reg_read(UC_ARM_REG_R0),self.get(file+8)))
        if p==RETURN:
            ret=self.callback_return;self.callback_return=None;self.ret(0);u.reg_write(UC_ARM_REG_PC,ret);return
        if p in (LOCK,UNLOCK,PULLED):self.instructions+=1;self.ret(0);return
        if p==SLEEP:raise AssertionError('Guide must poll, never native FS_Wait/Sleep')
        if p==TRANSPORT:
            self.instructions+=1
            dma,pos,dst,length=[u.reg_read(r) for r in (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3)]
            sp=u.reg_read(UC_ARM_REG_SP);cb,arg,async_=struct.unpack('<3I',bytes(u.mem_read(sp,12)))
            w=struct.unpack('<16I',self.cfg);root=self.get(self.reader+236)
            assert dma==0 and async_==1 and w[5]<=pos<=pos+length<=w[6]
            assert root<=dst<=dst+length<=root+len(self.data) and length<=131072
            self.transports.append((pos,dst,length));count=length-2 if self.short else length
            payload=self.raw[pos-w[5]:pos-w[5]+count]
            if self.delay:self.pending=(cb,arg,dst,payload);self.ret(0)
            else:self.u.mem_write(dst,payload);self.callback(cb,arg,u.reg_read(UC_ARM_REG_LR))
            return
        if self.checked and p in (INIT,FAST,ASYNC,CLOSE,SEEK) and CODE<=u.reg_read(UC_ARM_REG_LR)&~1<CODE+len(self.code):
            sp=u.reg_read(UC_ARM_REG_SP);self.fs_sp.append((p,sp));assert sp%8==0,'native FS boundary EABI8'
            assert self.get(IME)==1 and not u.reg_read(UC_ARM_REG_CPSR)&(128|32),'native FS IME/ARM/I0'
            assert u.reg_read(UC_ARM_REG_R0)==self.reader,'persistent FS file address'
            self.fs_calls.append((p,*[u.reg_read(r) for r in (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2)]))
            if p==INIT:assert self.get(self.reader+8)==0,'reinitialize bound file'
            if p==CLOSE:
                self.close_returns.append((u.reg_read(UC_ARM_REG_LR)&~1,self.reader))
                if self.close_failures:
                    self.close_failures-=1;self.put(ARC+28,self.get(ARC+28)|0x80);self.failure_return=u.reg_read(UC_ARM_REG_LR)&~1
            if p==FAST and self.open_fault:
                self.put(ARC+28,self.get(ARC+28)|0x80);self.failure_return=u.reg_read(UC_ARM_REG_LR)&~1
        if self.checked and p<CODE:
            assert p not in (0x0202551c,0x02096338,0x0201a910,0x0201aacc,0x020d82fc),'unsafe FS/allocator helper'
            assert p in self.fetch,f'undeclared native fetch {p:08x}'
            self.visited.add(p)
        HeapBench.hook(self,u,p,n,data)
    def call(self,name,*args):
        result=HeapBench.call(self,name,*args)
        if not name.startswith('ui_guide_'):return result
        assert bytes(self.u.mem_read(self.reader-16,16))==b'\x96'*16
        assert bytes(self.u.mem_read(self.reader+292,16))==b'\x69'*16
        if name!='ui_guide_init':assert bytes(self.u.mem_read(self.reader+72,8))==bytes.fromhex('1e695ca3e196a35c'),'FS72 guard'
        return result

def guide_private_inputs():
    """Admit actual private inputs before creating any native fixture.

    Missing prerequisites skip ordinary public runs. Explicitly required inputs
    fail. Every existing input is pinned even if another prerequisite is absent:
    a corrupt private file must never be hidden by a missing-input skip.
    """
    paths={lang:Path(os.environ.get('SGP_UI_GUIDE_RESOURCE_'+lang,
           str(SOURCE.parent/f'local/experiments/balance493-2026-10-28/candidate-v4-{lang}.nds')))
           for lang in ROM_PINS}
    charmap=Path(os.environ.get('SGP_UI_GUIDE_CHARMAP',str(SOURCE.parent/'local/tools/pokeheartgold/charmap.txt')))
    missing=[]
    for lang,path in paths.items():
        if not path.is_file():
            if path.exists():raise AssertionError(f'Guide {lang} ROM input not a file: {path}')
            missing.append(f'SGP_UI_GUIDE_RESOURCE_{lang} ({path})');continue
        digest=hashlib.sha256()
        with path.open('rb') as stream:
            for block in iter(lambda:stream.read(1024*1024),b''):digest.update(block)
        assert (path.stat().st_size,digest.hexdigest())==ROM_PINS[lang],f'Guide {lang} ROM identity'
    if charmap.is_file():
        assert hashlib.sha256(charmap.read_bytes()).hexdigest()==guide_content.CHARMAP_SHA256,'Guide charmap identity'
    elif charmap.exists():raise AssertionError(f'Guide charmap input not a file: {charmap}')
    else:missing.append(f'SGP_UI_GUIDE_CHARMAP ({charmap})')
    if missing:
        message='Guide private inputs missing: '+', '.join(missing)
        if os.environ.get('SGP_UI_GUIDE_RESOURCE_REQUIRE_INPUTS')=='1':raise AssertionError(message)
        raise unittest.SkipTest(message)
    return paths,charmap

class GuideResourceRomTests(unittest.TestCase):
    def test_maximum_member_is_one_async_request_with_pending_cancel_error_and_canaries(self):
        fixture=list(self.fixtures['IT']);data=bytearray(fixture[3]);data.extend(bytes(131072-len(data)))
        struct.pack_into('<I',data,4,len(data));data[-4:]=b'\x55\x66\x77\x88';data=bytes(data)
        cfg=bytearray(fixture[4]);off=struct.unpack_from('<I',cfg,36)[0];raw=fixture[5][:off]+data
        top=struct.unpack_from('<I',cfg,20)[0]
        for at,value in ((24,top+len(raw)),(32,len(raw)),(40,len(data)),(44,zlib.crc32(data))):struct.pack_into('<I',cfg,at,value)
        fixture[3:6]=[data,bytes(cfg),raw]
        for mode in ('success','short','error','cancel'):
            b=NativeGuideBench(self.compiled,fixture);b.start()
            while b.get(b.reader+220)!=4:self.assertEqual(b.call('ui_guide_step',b.reader,4096),MORE)
            b.delay=True;b.short=mode=='short';self.assertEqual(b.call('ui_guide_step',b.reader,4096),MORE)
            self.assertEqual(b.get(b.reader+260),131072,'one request, not one scheduler roundtrip per4KiB')
            root=b.get(b.reader+236);guards=bytes(b.u.mem_read(root-32,32)),bytes(b.u.mem_read(root+131072,32))
            if mode=='cancel':self.assertEqual(b.call('ui_guide_cancel',b.reader),MORE)
            self.assertEqual(b.call('ui_guide_pump',b.reader,4096,4),MORE)
            self.assertEqual(b.call('ui_guide_release',b.reader),0)
            self.assertFalse(b.closes,'pending CARD request retains its persistent file')
            b.complete(error=5 if mode=='error' else 0);b.delay=False
            self.assertEqual(b.finish(),READY if mode=='success' else FAILED,mode)
            self.assertEqual((bytes(b.u.mem_read(root-32,32)),bytes(b.u.mem_read(root+131072,32))),guards)
            if mode=='success':self.assertEqual(bytes(b.u.mem_read(root,131072)),data)
            self.assertEqual(b.call('ui_guide_release',b.reader),RELEASED)
    @classmethod
    def setUpClass(cls):
        paths,charmap=guide_private_inputs()
        import ndspy.rom,ndspy.narc
        cls.fixtures={}
        for lang,pin in ROM_PINS.items():
            path=paths[lang];input_bytes=path.read_bytes()
            assert (len(input_bytes),hashlib.sha256(input_bytes).hexdigest())==pin,f'Guide {lang} ROM identity'
            rom=ndspy.rom.NintendoDSRom(input_bytes);sections=ndspy_load_arm9_sicuro(rom).sections
            fntoff,fntbytes,fatoff,fatbytes=struct.unpack_from('<4I',input_bytes,0x40)
            for a,n,want in (*HEAP_PINS,*FS_PINS):
                s=next(s for s in sections if s.ramAddress<=a<a+n<=s.ramAddress+len(s.data))
                assert hashlib.sha256(bytes(s.data[a-s.ramAddress:a-s.ramAddress+n])).hexdigest()==want
            data,receipt=guide_content.build_from_rom(path,lang,charmap);graph=guide_content.read_content(data)
            fid=rom.filenames.idOf('a/0/2/7');narc=ndspy.narc.NARC(rom.files[fid]);old=narc.files[:829]
            narc.files[829]=data;raw=narc.save();assert ndspy.narc.NARC(raw).files[:829]==old
            btaf=struct.unpack_from('<I',raw,20)[0];btnf=struct.unpack_from('<I',raw,16+btaf+4)[0]
            gmif=16+btaf+btnf+8;start,end=struct.unpack_from('<II',raw,28+829*8)
            assert raw[gmif+start:gmif+end]==data
            cfg=bytearray(config(data,fid,gmif+start,len(raw)));struct.pack_into('<I',cfg,8,int(lang=='IT'))
            cls.fixtures[lang]=([(s.ramAddress,bytes(s.data)) for s in sections if 0x02000000<=s.ramAddress<0x02400000],input_bytes[fatoff:fatoff+fatbytes],input_bytes[fntoff:fntoff+fntbytes],data,bytes(cfg),raw,graph)
        cls.temp=tempfile.TemporaryDirectory();cls.addClassCleanup(cls.temp.cleanup);cls.compiled=compile_guide(Path(cls.temp.name))
    def benches(self):
        for lang,fixture in self.fixtures.items():yield lang,NativeGuideBench(self.compiled,fixture)
    def test_actual_high_arena_cache_crosses_heap_ceiling_and_releases(self):
        for lang,b in self.benches():
            with self.subTest(lang=lang):
                b.relocate_archive_cache(0x023be564)
                self.assertEqual(b.get(ARC+44),0x023be580)
                self.assertEqual(b.get(ARC+52),0x023bf588)
                before=bytes(b.u.mem_read(0x023be564,7040))
                self.assertEqual(b.start(),MORE)
                self.assertEqual(b.finish(),READY)
                self.assertEqual(b.call('ui_guide_acquire',b.reader,b.lease),1)
                self.assertEqual(b.call('ui_guide_category',b.lease,0,OUT),1)
                self.assertEqual(b.call('ui_guide_drop',b.lease),1)
                self.assertEqual(b.call('ui_guide_release',b.reader),RELEASED)
                self.assertEqual(bytes(b.u.mem_read(0x023be564,7040)),before)
                self.assertEqual(b.get(ARC+68),0x023be564)
                self.assertEqual(b.get(b.reader+8),0)
                self.assertEqual(b.free(b.app),1);self.assertEqual(b.destroy(),1)
    def test_all_compiled_categories_entries_pages_lines_and_refs_match_independent_readback(self):
        for lang,b in self.benches():
            with self.subTest(lang=lang):
                self.assertEqual(b.start(),MORE);self.assertEqual(b.finish(),READY)
                self.assertEqual(b.call('ui_guide_acquire',b.reader,b.lease),1)
                total=0
                for ci,cat in enumerate(b.graph):
                    self.assertEqual(b.call('ui_guide_category',b.lease,ci,OUT),1)
                    self.assertEqual((b.get(OUT),b.get(OUT+8)),(cat['id'],len(cat['entries'])))
                    self.check_text(b,OUT+16,cat['title'])
                    for ei,entry in enumerate(cat['entries']):
                        self.assertEqual(b.call('ui_guide_entry',b.lease,ci,ei,OUT),1)
                        self.assertEqual((b.get(OUT),b.get(OUT+8),b.get(OUT+12)),(entry['id'],len(entry['pages']),total))
                        self.check_text(b,OUT+16,entry['title'])
                        self.assertEqual(b.call('ui_guide_find',b.lease,entry['id'],OUT+64),1);self.assertEqual(b.get(OUT+64),total)
                        for pi,page in enumerate(entry['pages']):
                            self.assertEqual(b.call('ui_guide_page',b.lease,total,pi,OUT),1)
                            self.assertEqual((b.get(OUT+8),b.get(OUT+12)),(len(page['lines']),page['reference']))
                            for li,line in enumerate(page['lines']):
                                self.assertEqual(b.call('ui_guide_line',b.lease,total,pi,li,OUT),1);self.check_text(b,OUT,line)
                        total+=1
                self.assertEqual(total,467)
                before=bytes(b.u.mem_read(OUT,80));self.assertEqual(b.call('ui_guide_find',b.lease,65535,OUT),0)
                self.assertEqual(bytes(b.u.mem_read(OUT,80)),before)
                self.assertEqual(b.call('ui_guide_release',b.reader),0)
                self.assertEqual(b.call('ui_guide_drop',b.lease),1);self.assertEqual(b.call('ui_guide_release',b.reader),RELEASED)
                self.assertEqual(b.free(b.app),1);self.assertEqual(b.destroy(),1)
                self.assertTrue(all(sp%8==0 for p,sp in b.fs_sp))
    def drive(self,b,phase):
        for _ in range(200):
            if b.get(b.reader+220)==phase:return
            self.assertEqual(b.call('ui_guide_step',b.reader,4096),MORE)
        self.fail('phase not reached')
    def test_final_entry_exit_guards_and_native_views_after_quiet_fresh_fix(self):
        for lang,fixture in self.fixtures.items():
            b=NativeGuideBench(self.compiled,fixture)
            self.assertEqual(b.start(),MORE);self.assertEqual(b.finish(),READY)
            self.assertEqual(b.call('ui_guide_acquire',b.reader,b.lease),1)
            for ci,cat in enumerate(b.graph):
                self.assertEqual(b.call('ui_guide_category',b.lease,ci,OUT),1);self.check_text(b,OUT+16,cat['title'])
                for ei in (0,len(cat['entries'])-1):
                    e=cat['entries'][ei];self.assertEqual(b.call('ui_guide_entry',b.lease,ci,ei,OUT),1)
                    self.check_text(b,OUT+16,e['title']);index=b.get(OUT+12)
                    self.assertEqual(b.call('ui_guide_line',b.lease,index,0,0,OUT),1);self.check_text(b,OUT,e['pages'][0]['lines'][0])
            self.assertEqual(b.call('ui_guide_drop',b.lease),1);self.assertEqual(b.call('ui_guide_release',b.reader),RELEASED)
            b.put(CFG+12,2);b.put(b.reader+8,ARC);calls=len(b.fs_calls)
            self.assertEqual(b.call('ui_guide_begin',b.reader,CFG,TOKEN),HOLD)
            self.assertEqual(b.get(b.reader+8),ARC);self.assertEqual(len(b.fs_calls),calls)
            for operation in ('begin','release'):
                b=NativeGuideBench(self.compiled,fixture);self.assertEqual(b.call('ui_guide_init',b.reader),1)
                b.put(b.reader+8,ARC);calls=len(b.fs_calls)
                result=b.call('ui_guide_begin',b.reader,CFG,TOKEN) if operation=='begin' else b.call('ui_guide_release',b.reader)
                self.assertEqual(result,HOLD);self.assertEqual(b.get(b.reader+8),ARC);self.assertEqual(len(b.fs_calls),calls)
    def test_native_missing_category_semantic_mutant_is_detected_after_real_load(self):
        # The native load succeeds; a valid typed view cannot silently disappear.
        old='if(!ggr_output(l,out,sizeof(*out))||index>=l->reader->config.categories)return 0;'
        new='if(1||!ggr_output(l,out,sizeof(*out))||index>=l->reader->config.categories)return 0;'
        with tempfile.TemporaryDirectory() as d:
            mutant=compile_guide(Path(d),(old,new))
            for lang,fixture in self.fixtures.items():
                for compiled,want in ((self.compiled,1),(mutant,0)):
                    b=NativeGuideBench(compiled,fixture);self.assertEqual(b.start(),MORE);self.assertEqual(b.finish(),READY)
                    self.assertEqual(b.call('ui_guide_acquire',b.reader,b.lease),1)
                    before=bytes(b.u.mem_read(OUT,32));result=b.call('ui_guide_category',b.lease,0,OUT)
                    if want:self.assertEqual(result,1)
                    else:
                        with self.assertRaisesRegex(AssertionError,'valid category must remain visible'):
                            self.assertEqual(result,1,'valid category must remain visible')
                        self.assertEqual(bytes(b.u.mem_read(OUT,32)),before)
                    self.assertEqual(b.call('ui_guide_drop',b.lease),1);self.assertEqual(b.call('ui_guide_release',b.reader),RELEASED)
    def test_actual_close_false_retries_same_persistent_file_after_stack_poison(self):
        for lang,b in self.benches():
            self.assertEqual(b.start(),MORE);self.drive(b,6);root=b.get(b.reader+236);b.close_failures=5
            for _ in range(5):
                self.assertEqual(b.call('ui_guide_step',b.reader,4096),MORE)
                self.assertEqual(b.get(b.reader+236),root);self.assertEqual(b.get(b.reader+8),ARC)
                self.assertEqual(b.call('ui_guide_release',b.reader),0)
                b.u.mem_write(STACK-768,b'\xdd'*640)
            self.assertEqual(b.finish(),READY)
            self.assertEqual(b.closes,[(b.reader,0,ARC)]*5+[(b.reader,1,0)])
            self.assertEqual(b.call('ui_guide_release',b.reader),RELEASED)
            self.assertEqual(b.free(b.app),1);self.assertEqual(b.destroy(),1)
    def test_actual_delayed_read_cancel_drains_and_failed_open_keeps_association(self):
        for lang,fixture in self.fixtures.items():
            for kind in ('pending_cancel','open_fail','error'):
                with self.subTest(lang=lang,kind=kind):
                    b=NativeGuideBench(self.compiled,fixture);b.delay=True;b.open_fault=kind=='open_fail'
                    self.assertEqual(b.start(),MORE)
                    if kind=='open_fail':
                        self.assertEqual(b.call('ui_guide_step',b.reader,4096),MORE)
                        self.assertEqual(b.get(b.reader+8),ARC);self.assertEqual(b.get(b.reader+12)&16,0)
                    else:
                        self.drive(b,5);root=b.get(b.reader+236)
                        self.assertIsNotNone(b.pending)
                        for _ in range(4):
                            self.assertEqual(b.call('ui_guide_step',b.reader,4096),MORE)
                            b.u.mem_write(STACK-768,b'\xdd'*640)
                        self.assertEqual(b.call('ui_guide_release',b.reader),0)
                        if kind=='pending_cancel':self.assertEqual(b.call('ui_guide_cancel',b.reader),MORE)
                        b.complete(error=3 if kind=='error' else 0)
                        self.assertEqual(b.get(b.reader+236),root)
                    self.assertEqual(b.finish(),FAILED)
                    self.assertEqual(b.closes[-1],(b.reader,1,0))
                    self.assertEqual(b.call('ui_guide_release',b.reader),RELEASED)
                    self.assertEqual(b.free(b.app),1);self.assertEqual(b.destroy(),1)
    def test_actual_root_exhaustion_and_prefix_ownership_hold(self):
        for lang,fixture in self.fixtures.items():
            for kind in ('exhaustion','prefix'):
                b=NativeGuideBench(self.compiled,fixture);before=b.totals(),b.registry()
                self.assertEqual(b.start(),MORE);self.drive(b,3)
                if kind=='exhaustion':
                    filler=b.alloc(0x3c000);self.assertTrue(filler)
                    self.assertEqual(b.finish(),FAILED);self.assertEqual(b.get(b.reader+236),0)
                    self.assertEqual(b.call('ui_guide_release',b.reader),RELEASED)
                    self.assertEqual(b.free(filler),1)
                    self.assertEqual((b.totals(),b.registry()),before)
                    self.assertEqual(b.free(b.app),1);self.assertEqual(b.destroy(),1)
                else:
                    self.assertEqual(b.call('ui_guide_step',b.reader,4096),MORE)
                    root=b.get(b.reader+236);old=b.get(root-4);b.put(root-4,0)
                    calls=len(b.fs_calls);self.assertEqual(b.call('ui_guide_step',b.reader,4096),HOLD)
                    self.assertEqual(b.call('ui_guide_release',b.reader),HOLD)
                    self.assertEqual(b.get(b.counts+76,2),2);self.assertEqual(len(b.fs_calls),calls)
                    self.assertEqual(b.get(b.reader+236),root);b.put(root-4,old)
    def test_actual_partial_transport_crc_and_unknown_source_hold(self):
        for lang,fixture in self.fixtures.items():
            for kind in ('partial','crc','source'):
                b=NativeGuideBench(self.compiled,fixture)
                if kind=='crc':b.put(CFG+44,b.get(CFG+44)^1)
                b.short=kind=='partial';self.assertEqual(b.start(),MORE)
                if kind=='source':
                    self.drive(b,4);root=b.get(b.reader+236);b.put(ARC+80,0)
                    before=len(b.fs_calls);self.assertEqual(b.call('ui_guide_step',b.reader,4096),HOLD)
                    self.assertEqual(b.call('ui_guide_release',b.reader),HOLD)
                    self.assertEqual(len(b.fs_calls),before);self.assertEqual(b.get(b.reader+236),root)
                else:
                    self.assertEqual(b.finish(),FAILED);self.assertEqual(b.call('ui_guide_acquire',b.reader,b.lease),0)
                    self.assertEqual(b.call('ui_guide_release',b.reader),RELEASED)
                    self.assertEqual(b.free(b.app),1);self.assertEqual(b.destroy(),1)
    def check_text(self,b,record,want):
        owner,off,units,policy=struct.unpack('<4I',bytes(b.u.mem_read(record,16)))
        self.assertEqual(owner,b.lease+16);self.assertEqual(policy,0);self.assertEqual(units,len(want))
        root=b.get(owner+4);self.assertEqual(struct.unpack('<%dH'%units,bytes(b.u.mem_read(root+off,2*units))),want)
