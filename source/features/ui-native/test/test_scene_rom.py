"""Prepared EN/IT native composition; no actual Field teardown/Android/save claim.
Real NNS/GF, FS path/dispatch/close, boot-font reference tuple, native decoder,
BG and common Scene execute together. CARD transport, retired parent handoff,
physical event delivery and hardware scheduling are explicit seams.
"""
import os
import tempfile
import unittest
from scene_bench import *

class SceneRomTests(unittest.TestCase):
    def test_cursor_work_does_not_repeat_guards_for_each_empty_plan_step(self):
        for role in (1,2):
            b=NativeSceneBench(self.compiled,self.fixtures['IT'],role=role)
            self.assertEqual(b.finish_init(),SCENE_READY)
            b.input();start=b.instructions;b.input(128);b.idle()
            self.assertLess(b.instructions-start,4000000,
                            'cursor work must batch finite admission, row and skipped-op scans')
            self.assertEqual(b.finish_exit(),SCENE_EXITED);b.borrowed_intact()

    @classmethod
    def setUpClass(cls):
        import ndspy.rom,ndspy.narc
        from test_painter_rom import NativePainterTests
        from sgp131 import guide_content
        NativePainterTests.setUpClass();cls.addClassCleanup(NativePainterTests.tearDownClass)
        cls.fixtures={}
        canonical=SOURCE.parent/'local/experiments/balance493-2026-10-28'
        charmap=SOURCE.parent/'local/tools/pokeheartgold/charmap.txt'
        for lang,painter in NativePainterTests.fixtures.items():
            path=canonical/f'candidate-v4-{lang}.nds';raw=path.read_bytes();rom=ndspy.rom.NintendoDSRom(raw)
            for a,n,want in (*FS_PINS,*ADMISSION_PINS,OPTIONS_SPEED_PIN):
                p,data=next((p,d) for p,d in painter[4] if p<=a<a+n<=p+len(d))
                assert hashlib.sha256(data[a-p:a-p+n]).hexdigest()==want
            fontarc=rom.getFileByName('a/0/1/6');gmif=16
            while fontarc[gmif:gmif+4]!=b'GMIF':gmif+=struct.unpack_from('<I',fontarc,gmif+4)[0]
            gmif+=8
            data,_=guide_content.build_from_rom(path,lang,charmap)
            fid=rom.filenames.idOf('a/0/2/7');narc=ndspy.narc.NARC(rom.files[fid]);narc.files[829]=data;guide_raw=narc.save()
            btaf=struct.unpack_from('<I',guide_raw,20)[0];btnf=struct.unpack_from('<I',guide_raw,16+btaf+4)[0]
            off=16+btaf+btnf+8+struct.unpack_from('<I',guide_raw,28+829*8)[0]
            config=bytearray(gb.config(data,fid,off,len(guide_raw)));struct.pack_into('<I',config,8,int(lang=='IT'))
            fntoff,fntn,fatoff,fatn=struct.unpack_from('<4I',raw,0x40)
            cls.fixtures[lang]=dict(painter=painter,gmif=gmif,guide_raw=guide_raw,guide_config=bytes(config),fat=raw[fatoff:fatoff+fatn],fnt=raw[fntoff:fntoff+fntn],guide=data)
        cls.tmp=tempfile.TemporaryDirectory(prefix='scene-native-');cls.addClassCleanup(cls.tmp.cleanup)
        cls.compiled,cls.receipt=compile_scene(Path(cls.tmp.name))
        evidence('compile',cls.receipt)
        cls.tmp64=tempfile.TemporaryDirectory(prefix='scene-native-64-');cls.addClassCleanup(cls.tmp64.cleanup)
        cls.compiled64,cls.receipt64=compile_scene(Path(cls.tmp64.name),work_calls=64)
        evidence('compile64',cls.receipt64)

    def _wait_buffers(self,b,bg):
        roots=[b.get(bg+16+4*i) for i in range(5)]
        sizes=(360,2048,2048,21120,21120)
        return tuple(bytes(b.u.mem_read(root,size)) for root,size in zip(roots,sizes) if root)

    def _wait_state(self,b,app,bg):
        return dict(phase=b.get(app+56),model_epoch=b.get(app+72),
                    next_version=b.get(app+76),visible_epoch=b.get(app+80),
                    submitted_epoch=b.get(app+84),front=b.get(bg+76),
                    pending=b.get(bg+80),pending_version=b.get(bg+84),
                    preparing=b.get(bg+88),versions=(b.get(bg+68),b.get(bg+72)),
                    allocations=b.allocations,fs_calls=tuple(b.fs_calls),
                    buffers=self._wait_buffers(b,bg))

    def _reach_wait_without_publication(self,b,phase):
        if phase=='first':
            for _ in range(1800):
                app=b.get(b.context+28)
                if app and b.get(app+56)==11:break  # SC_WAIT_FIRST
                self.assertEqual(b.scene('init',False),SCENE_MORE)
            self.assertTrue(app);self.assertEqual(b.get(app+56),11)
            return app,app+848,'init',SCENE_READY
        self.assertEqual(b.finish_init(),SCENE_READY)
        app=b.get(b.context+28)
        self.assertEqual(b.input(),SCENE_MORE)  # real release gate
        b.put(b.context+32,7)
        b.sample_data=(1,0,128,128,0,0);b.sample_event=1
        b.put(0x021D1150,128);b.put(0x021D1154,0);b.put(0x021D1140,0)
        self.assertEqual(b.scene('main',False),SCENE_MORE)
        for _ in range(600):
            if b.get(app+56)==16:break       # SC_WAIT
            self.assertEqual(b.scene('main',False),SCENE_MORE)
        self.assertEqual(b.get(app+56),16)
        return app,app+848,'main',SCENE_MORE

    def test_wait_matrix_preserves_buffers_rejects_late_vcount_and_recovers(self):
        """SG-UI-WAIT across both roles, both waits and calibrated work caps.

        The bench owns no hardware scheduler: suppressing the registered VBlank
        callback is explicit fault injection.  A callback sampled after the
        configured line must refuse without mutation; the same callback at the
        admitted line is the negative control and must recover the real scene.
        """
        for work_calls,compiled in ((4,self.compiled),(64,self.compiled64)):
            for role in (1,2):
                for phase in ('first','repaint'):
                    with self.subTest(work_calls=work_calls,role=role,phase=phase):
                        b=NativeSceneBench(compiled,self.fixtures['EN'],role=role)
                        app,bg,entry,recovered=self._reach_wait_without_publication(b,phase)
                        pending=b.get(bg+80);front=b.get(bg+76)
                        self.assertIn(pending,(0,1));self.assertNotEqual(pending,front)
                        stable=self._wait_state(b,app,bg)
                        for _ in range(32):
                            self.assertEqual(b.scene(entry,False),SCENE_MORE)
                            self.assertEqual(self._wait_state(b,app,bg),stable)

                        callback=b.get(0x021D110C);context=b.get(0x021D1110)
                        self.assertTrue(callback);self.assertEqual(context,bg)
                        b.put(0x04000006,241,2)  # deadline is line240
                        b.address(callback,context)
                        self.assertEqual(self._wait_state(b,app,bg),stable,
                                         'late VCOUNT must leave the pending frame untouched')

                        b.put(0x04000006,192,2)
                        b.address(callback,context)
                        self.assertEqual(b.get(bg+76),pending)
                        self.assertEqual(b.get(bg+80),2)
                        self.assertEqual(b.scene(entry,False),recovered)
                        self.assertEqual(b.get(app+56),14)  # SC_IDLE
                        self.assertEqual(b.finish_exit(),SCENE_EXITED)
                        self.assertEqual(bytes(b.u.mem_read(b.heap,92)),bytes(92))
                        self.assertEqual(b.get(b.context+28),0)
                        b.borrowed_intact()

    def test_final_native_bilingual_static_entry_exit_and_heap_margin(self):
        for lang,fixture in self.fixtures.items():
            for role in (1,2):
                b=NativeSceneBench(self.compiled,fixture,role=role)
                self.assertEqual(b.finish_init(),SCENE_READY)
                app=b.get(b.context+28);bg=app+848
                self.assertEqual(b.get(bg+172),0);self.assertEqual(b.get(bg+168),0x42414c4c)
                self.assertEqual(b.get(b.counts+76,2),8 if role==1 else 9)
                self.assertGreater(b.heap_free()[1],40000)
                self.assertEqual(b.get(0x04001000)&0x1f00,256)
                b.record('polish_ready',lang)
                print('final scene',lang,'role',role,'heap',b.get(b.heap+20),'free',b.heap_free(),flush=True)
                b.borrowed_intact();self.assertEqual(b.finish_exit(),SCENE_EXITED);b.borrowed_intact()
                self.assertEqual(bytes(b.u.mem_read(b.heap,92)),bytes(92));self.assertEqual(b.get(b.context+28),0)
                b.record('polish_exit',lang)
    def test_guide_entry_batches_progress_and_retires_all_owners(self):
        b=NativeSceneBench(self.compiled,self.fixtures['IT'],role=2)
        calls=0
        while True:
            calls+=1;result=b.scene()
            if result!=SCENE_MORE:break
            self.assertLess(calls,180)
        self.assertEqual(result,SCENE_READY)
        self.assertLessEqual(calls,90,'baseline took137 callbacks before the module loader')
        self.assertEqual(b.finish_exit(),SCENE_EXITED);b.borrowed_intact()
    def test_guide_first_cursor_change_seeds_hidden_from_the_presented_canvas(self):
        b=NativeSceneBench(self.compiled,self.fixtures['IT'],role=2)
        self.assertEqual(b.finish_init(),SCENE_READY)
        app=b.get(b.context+28);bg=app+848;front=b.get(bg+76)
        pixels=bytes(b.u.mem_read(b.get(bg+28+4*front),21120))
        b.input();b.input(128);b.idle()
        self.assertEqual(b.get(app+2428+48),2,'copy path, not a full hidden repaint')
        self.assertEqual(bytes(b.u.mem_read(b.get(bg+28+4*front),21120)),pixels,'old front stays immutable')
        self.assertEqual(b.finish_exit(),SCENE_EXITED);b.borrowed_intact()
    def test_new_key_is_accepted_as_soon_as_pending_frame_is_visible(self):
        b=NativeSceneBench(self.compiled,self.fixtures['EN'],role=1)
        self.assertEqual(b.finish_init(),SCENE_READY);app=b.get(b.context+28)
        b.input();b.input(128)
        for _ in range(200):
            if b.get(app+56)==16:break
            b.input()
        self.assertEqual(b.get(app+56),16)
        self.assertEqual(b.get(app+848+80),2,'VBlank already published the completed frame')
        epoch=b.get(app+72);b.input(64)
        self.assertEqual(b.get(app+72),epoch+1,'visible frame must not discard the next fresh key')
        b.idle();self.assertEqual(b.finish_exit(),SCENE_EXITED);b.borrowed_intact()

    def test_missing_vblank_publication_keeps_waiting_and_late_callback_recovers(self):
        """SG-UI-WAIT reproducer: Scene has no independent publication timeout.

        Suppress only the registered VBlank callback after a real Settings
        repaint reaches SC_WAIT.  Main-loop calls stay finite and preserve the
        prepared buffer, but cannot make it visible by themselves.  Executing
        that exact callback once is the negative control: it publishes the
        pending buffer and the next main call returns to SC_IDLE.
        """
        b=NativeSceneBench(self.compiled,self.fixtures['EN'],role=1)
        self.assertEqual(b.finish_init(),SCENE_READY)
        app=b.get(b.context+28);bg=app+848
        self.assertEqual(b.input(),SCENE_MORE)  # release gate, no repaint pending
        # Deliver one real key without letting the bench invoke VBlank after
        # the main callback.  This is the same resident physical boundary used
        # by input(), with publication as the only suppressed component.
        b.put(b.context+32,7)
        b.sample_data=(1,0,128,128,0,0);b.sample_event=1
        b.put(0x021D1150,128);b.put(0x021D1154,0);b.put(0x021D1140,0)
        self.assertEqual(b.scene('main',False),SCENE_MORE)
        for _ in range(600):
            if b.get(app+56)==16:break       # SC_WAIT
            self.assertEqual(b.scene('main',False),SCENE_MORE)
        self.assertEqual(b.get(app+56),16)
        pending=b.get(bg+80);front=b.get(bg+76)
        self.assertIn(pending,(0,1));self.assertNotEqual(pending,front)
        stable=(pending,front,b.get(app+72),b.get(app+80),b.allocations,len(b.fs_calls))
        for _ in range(256):
            self.assertEqual(b.scene('main',False),SCENE_MORE)
            self.assertEqual(b.get(app+56),16)
        self.assertEqual((b.get(bg+80),b.get(bg+76),b.get(app+72),b.get(app+80),
                          b.allocations,len(b.fs_calls)),stable)
        # Control: the still-registered callback alone resolves the wait.
        self.assertTrue(b.get(0x021D110C))
        b.put(0x04000006,192,2)
        b.address(b.get(0x021D110C),b.get(0x021D1110))
        self.assertEqual(b.get(bg+76),pending)
        self.assertEqual(b.scene('main',False),SCENE_MORE)
        self.assertEqual(b.get(app+56),14)    # SC_IDLE
        self.assertEqual(b.finish_exit(),SCENE_EXITED);b.borrowed_intact()

    def test_native_ui_reader_cancel_retries_failed_close_without_releasing_app(self):
        b=NativeSceneBench(self.compiled,self.fixtures['EN'],role=2)
        for _ in range(12):
            app=b.get(b.context+28)
            if app and b.get(app+104+616)==4:break
            self.assertEqual(b.scene(),SCENE_MORE)
        self.assertTrue(app);self.assertEqual(b.get(app+104+616),4)
        b.close_failures=2;token=bytes(b.u.mem_read(b.heap,92))
        for _ in range(2):
            self.assertEqual(b.scene('exit',False),SCENE_MORE)
            self.assertEqual(b.get(b.context+28),app)
            self.assertEqual(bytes(b.u.mem_read(b.heap,92)),token)
            self.assertEqual(b.get(app+104+8),rb.ARC)
        self.assertEqual(b.finish_exit(),SCENE_EXITED);b.borrowed_intact()
    def test_native_text_delay_pin_and_pre_app_failure_normal_boundary_retry(self):
        for lang,fixture in self.fixtures.items():
            b=NativeSceneBench(self.compiled,fixture,role=1)
            if lang=='EN':
                b.fail=ALLOC;self.assertEqual(b.scene(),SCENE_CLOSE)
                self.assertEqual(bytes(b.u.mem_read(b.heap,92)),bytes(92))
                self.assertEqual(b.finish_exit(),SCENE_EXITED);b.fail=None
            for speed,want in ((0,8),(1,4),(2,1)):
                b.put(b.options,speed,2);self.assertEqual(b.address(0x0202AD3D,b.options),want)
            b.put(b.options,0,2);b.alloc_failure=1
            self.assertEqual(b.scene(),SCENE_CLOSE);self.assertEqual(b.get(b.context+28),0)
            token=bytes(b.u.mem_read(b.heap,92));self.assertNotEqual(token,bytes(92))
            b.put(IME,0);self.assertEqual(b.scene('exit',False),SCENE_MORE)
            self.assertEqual(bytes(b.u.mem_read(b.heap,92)),token)
            b.put(IME,1);self.assertEqual(b.finish_exit(),SCENE_EXITED);b.borrowed_intact()
    def test_native_settings_it_root_static_native_lower_and_borrowed_args(self):
        b=NativeSceneBench(self.compiled,self.fixtures['IT'],role=1)
        self.assertEqual(b.finish_init(),SCENE_READY)
        self.assertEqual(b.get(b.counts+76,2),8);b.record('ready','IT')
        self.assertEqual(b.get(0x04001000)&0x1f00,256);self.assertEqual(b.get(b.get(b.context+28)+848+168),0x42414c4c)
        b.borrowed_intact();self.assertEqual(b.finish_exit(),SCENE_EXITED);b.borrowed_intact()
    def test_settings_preview_waits_for_info_visibility_and_uses_active_frame_delay(self):
        b=NativeSceneBench(self.compiled,self.fixtures['EN'],role=1)
        self.assertEqual(b.finish_init(),SCENE_READY)
        app=b.get(b.context+28);b.record('ready','EN');b.input();self.assertEqual(b.input(2048),SCENE_MORE)
        self.assertEqual(b.get(app+1436+212,1),2,'real Y opens Info')
        self.assertEqual(b.get(app+92),0)
        for _ in range(8):self.assertEqual(b.input(),SCENE_MORE)
        self.assertEqual(b.get(app+92),0,'preview cannot elapse before Info is presented')
        for _ in range(600):
            if b.get(app+56)==14:break
            self.assertEqual(b.scene('main'),SCENE_MORE)
        self.assertEqual(b.get(app+56),14);self.assertEqual(b.get(app+92),0)
        for _ in range(7):b.input()
        self.assertEqual(b.get(app+92),0);b.input();self.assertEqual(b.get(app+92),1)
        b.input(event=2,suspend=2);before=b.get(app+92)
        for _ in range(8):b.scene('main')
        self.assertEqual(b.get(app+92),before);self.assertEqual(b.acks,[2])
        self.assertEqual(b.finish_exit(),SCENE_EXITED);b.record('complete','EN')
    def test_settings_audio_busy_coalesces_and_exit_retries_rollback(self):
        b=NativeSceneBench(self.compiled,self.fixtures['EN'],role=1)
        self.assertEqual(b.scene(),SCENE_MORE)
        app=b.get(b.context+28);model=app+1436
        # Prepare initial selection through the real reducer before the first
        # plan exists; no Scene phase/front/epoch is bypassed or fabricated.
        b.call('settings_sample',model,0,1,0)
        self.assertEqual(b.call('settings_step',model,0,0),0,'initial release is consumed')
        for _ in range(3):
            b.call('settings_sample',model,0,1,0)
            self.assertEqual(b.call('settings_step',model,128,0),1)
        self.assertEqual(b.finish_init(),SCENE_READY);b.audio_pool()
        owner=app+1184;audio=owner+48
        def key(value):
            b.input();self.assertEqual(b.input(value),SCENE_MORE);b.idle()
        key(16) # Audio mono accepted through real Settings + owner code.
        self.assertEqual(b.get(0x021D05F0),1)
        self.assertEqual(b.get(audio+8),1);self.assertEqual(b.get(audio+28),1)
        key(32) # Draft returns to clean stereo while scheduler has no free node.
        self.assertEqual(b.get(audio+16),0);self.assertEqual(b.get(audio+8),1)
        generation=b.get(audio+20);queue=bytes(b.u.mem_read(0x021E1A60,36))
        for _ in range(3):self.assertEqual(b.input(),SCENE_MORE)
        self.assertEqual(b.get(audio+20),generation,'same pending intent coalesces')
        self.assertEqual(bytes(b.u.mem_read(0x021E1A60,36)),queue)
        self.assertEqual(b.input(2),SCENE_CLOSE,'clean B discards without applying')
        token=bytes(b.u.mem_read(b.heap,92));b.put(b.context+32,0)
        for _ in range(2):
            self.assertEqual(b.scene('exit',False),SCENE_MORE)
            self.assertEqual(b.get(b.context+28),app);self.assertEqual(bytes(b.u.mem_read(b.heap,92)),token)
            self.assertEqual(b.get(b.counts+76,2),8);self.assertEqual(b.get(0x02111944,1),2)
            self.assertEqual(b.get(0x021D05F0),1)
        # Scheduler makes one different free node available; pending node is
        # preserved. No ARM7 acknowledgment/audible completion is simulated.
        b.put(0x021E1A60,0x021E1D58);b.put(0x021E1A70,0x021E1D58)
        self.assertEqual(b.finish_exit(),SCENE_EXITED);self.assertEqual(b.get(0x021D05F0),0)
        self.assertEqual(b.get(b.context+28),0);self.assertEqual(bytes(b.u.mem_read(b.heap,92)),bytes(92))
        self.assertEqual(sum(p==0x020D579C for p,_ in b.audio_calls),2,'one preview and one rollback command')
        b.borrowed_intact();b.record('audio_complete','EN')
    def test_native_all_nine_root_acquisition_failures_close_only_owned_objects(self):
        b=NativeSceneBench(self.compiled,self.fixtures['EN'],role=2)
        # Injection targets allocations, not scheduler-visible phase numbers:
        # synchronous setup may cross several phases in one callback.
        initial=b.checkpoint()
        for target in range(1,10):
            with self.subTest(root=target):
                b.restore_checkpoint(initial);b.alloc_failure=target
                for _ in range(150):
                    result=b.scene()
                    if result!=SCENE_MORE:break
                self.assertEqual(result,SCENE_CLOSE,(target,b.get(b.context+48)))
                self.assertEqual(b.allocations,target,'the selected allocation actually failed')
                self.assertEqual(b.finish_exit(),SCENE_EXITED,(target,b.get(b.context+48)))
                self.assertEqual(bytes(b.u.mem_read(b.heap,92)),bytes(92))
                self.assertEqual(b.get(b.context+28),0);b.borrowed_intact()
    def test_free_app_before_destroy_refusal_keeps_resident_token_and_terminal_hold(self):
        b=NativeSceneBench(self.compiled,self.fixtures['EN'],role=2)
        self.assertEqual(b.scene(),SCENE_MORE)
        app=b.get(b.context+28);self.assertTrue(app)
        b.destroy_fault=True
        self.assertEqual(b.finish_exit(),SCENE_HOLD)
        self.assertEqual(b.get(b.context+28),0)
        token=bytes(b.u.mem_read(b.heap,92));self.assertNotEqual(token,bytes(92))
        b.u.mem_write(STACK-4096,bytes([0x69])*4096)
        b.put(b.counts+76,0,2)
        self.assertEqual(b.finish_exit(),SCENE_HOLD,'unknown ownership is terminal, not a retry promise')
        self.assertEqual(bytes(b.u.mem_read(b.heap,92)),token);b.borrowed_intact()
    def test_real_guide_initial_visibility_roots_font_and_reverse_cleanup(self):
        for lang,fixture in self.fixtures.items():
            with self.subTest(language=lang):
                b=NativeSceneBench(self.compiled,fixture,role=2)
                self.assertEqual(b.finish_init(),SCENE_READY,(b.get(b.context+48),b.get(b.get(b.context+28)+56),b.get(b.get(b.context+28)+76),b.get(b.get(b.context+28)+1628),b.trace[-20:]))
                app=b.get(b.context+28);bg=app+848
                self.assertEqual(b.get(bg+76),0);self.assertEqual(b.get(bg+72),0)
                self.assertEqual(b.get(app+2428+84+816+804),0,'untouched hidden history invalid')
                self.assertEqual(b.get(b.counts+76,2),9);self.assertEqual(b.get(0x02111944,1),2)
                self.assertGreater(b.heap_free()[1],40000);b.borrowed_intact();b.record('ready',lang)
                if lang=='EN':
                    version=b.get(bg+84);b.input();b.input()
                    self.assertEqual(b.get(bg+84),version,'same-model samples do not rebuild')
                    self.assertEqual(b.input(128),SCENE_MORE)
                    self.assertEqual(b.get(app+1512+2,2),1)
                    epoch=b.get(app+72);self.assertEqual(b.input(1),SCENE_MORE)
                    self.assertEqual(b.get(app+1512,2),0,'busy A cannot open unseen category')
                    self.assertEqual(b.get(app+72),epoch)
                    self.assertEqual(b.input(event=2,suspend=1),SCENE_MORE);self.assertEqual(b.acks,[1])
                    b.input(1,held=1);b.input();b.idle()
                    self.assertEqual(b.get(bg+76),1);self.assertEqual(b.get(app+2428+48),2,'first hidden use copies the validated front')
                    self.assertEqual(b.get(app+80),b.get(app+72))
                    b.input();b.input(128);b.idle()
                    self.assertEqual(b.get(bg+76),0,'released idle down publishes next buffer');self.assertEqual(b.get(app+2428+48),2,'cursor update copies the exact presented history')
                    b.borrowed_intact()
                    intact=b.checkpoint()
                    for pointer,value in ((0x021D110C,0x0201A0FD),(b.font+16,b.widths)):
                        b.put(pointer,value)
                        self.assertEqual(b.finish_exit(),SCENE_HOLD)
                        self.assertEqual(b.get(b.context+28),app);self.assertEqual(b.get(b.counts+76,2),9)
                        b.restore_checkpoint(intact)
                self.assertEqual(b.finish_exit(),SCENE_EXITED)
                self.assertEqual(b.get(b.context+28),0);self.assertEqual(bytes(b.u.mem_read(b.heap,92)),bytes(92))
                self.assertEqual(b.get(0x02111944,1),1);self.assertEqual(b.get(b.font+16),0)
                self.assertEqual(b.get(b.font+4),0x02026111);b.borrowed_intact();b.record('complete',lang)

class SceneFix1Tests(unittest.TestCase):
    """Only the two reviewed input compositions; reuse one real prepared front."""
    @classmethod
    def setUpClass(cls):
        SceneRomTests.setUpClass.__func__(cls)
        cls.b=NativeSceneBench(cls.compiled,cls.fixtures['EN'],role=2)
        assert cls.b.finish_init()==SCENE_READY
        cls.b.record('fix1_ready','EN')
        cls.initial=cls.b.checkpoint()
    def setUp(self):
        self.b.restore_checkpoint(self.initial)
        self.app=self.b.get(self.b.context+28);self.model=self.app+1512
    def settle(self):
        b=self.b
        for _ in range(1600):
            if b.get(self.app+56)==14 and b.get(self.app+80)==b.get(self.app+72):return
            self.assertEqual(b.scene('main'),SCENE_MORE)
        self.fail('finite visible semantic settlement')
    def test_01_ack_refusal_retries_and_invalid_owner_holds(self):
        b=self.b;token=bytes(b.u.mem_read(b.heap,92));b.physical_suspend=1;b.physical_folded=True
        for _ in range(2):
            self.assertEqual(b.input(event=2,suspend=1),SCENE_MORE,'folded valid owner is retryable')
            self.assertEqual(b.get(b.context+44),0);self.assertEqual(b.get(self.app+100),1)
            self.assertEqual(b.get(b.context+28),self.app);self.assertEqual(bytes(b.u.mem_read(b.heap,92)),token)
        refused=b.checkpoint();b.physical_valid=False
        self.assertEqual(b.input(event=2,suspend=1),SCENE_HOLD,'invalid next consume after ACK0 fails closed')
        self.assertEqual(b.get(b.context+28),self.app);self.assertEqual(bytes(b.u.mem_read(b.heap,92)),token)
        b.restore_checkpoint(refused);b.physical_folded=False;b.physical_suspend=2
        self.assertEqual(b.input(event=2,suspend=1),SCENE_MORE,'reclose superseded the consumed generation')
        self.assertEqual(b.input(event=2,suspend=2),SCENE_MORE)
        b.input(flags=1);b.input();self.assertEqual(b.get(self.model+92),0)
        self.assertEqual(b.get(self.app+100),0);self.assertEqual(b.get(b.context+44),0)
        b.physical_valid=False
        self.assertEqual(b.input(event=2,suspend=3),SCENE_HOLD,'actual invalid consume fails closed')
        self.assertEqual(b.get(b.context+28),self.app);self.assertEqual(bytes(b.u.mem_read(b.heap,92)),token)
    def test_02_lower_touch_inert_all_depths_and_concurrent_physical_keys(self):
        b=self.b
        lower=lambda:bytes(b.u.mem_read(0x06200000,1472))+bytes(b.u.mem_read(0x0620f000,2048))+bytes(b.u.mem_read(0x05000400,32))
        frozen=lower()
        for depth in range(3):
            b.input(down=1,held=0x1000)
            self.assertEqual(b.get(self.model+92),0,'touch held does not delay physical rearm')
            cursor=bytes(b.u.mem_read(self.model,10));epoch=b.get(self.app+72)
            for x,y in ((20,60),(150,60),(20,100),(150,100),(20,140),(150,140)):
                for xx,yy,down in ((x,y,1),(239,155,1),(x,y,0)):
                    self.assertEqual(b.input(x=xx,y=yy,down=down,held=0x1000 if down else 0),SCENE_MORE)
                    self.assertEqual(bytes(b.u.mem_read(self.model,10)),cursor)
                    self.assertEqual(b.get(self.app+72),epoch);self.assertEqual(b.get(self.model+104),0)
            if depth<2:
                self.assertEqual(b.input(1,x=150,y=140,down=1,held=0x1001),SCENE_MORE)
                self.assertEqual(b.get(self.model,2),depth+1)
                self.settle();b.input(down=1,held=0x1000)
            self.assertEqual(lower(),frozen)
        b.input(256,down=1,held=0x1100);self.settle();self.assertEqual(lower(),frozen)
        self.assertEqual(b.finish_exit(),SCENE_EXITED);b.borrowed_intact()
    def test_03_invalid_physical_owner_holds_with_touch_inert(self):
        b=self.b;b.input(down=1,held=0x1000);token=bytes(b.u.mem_read(b.heap,92));b.physical_valid=False
        self.assertEqual(b.input(x=150,y=140),SCENE_HOLD)
        self.assertEqual(b.get(self.app+4980+12),0);self.assertEqual(b.get(b.context+44),1)
        self.assertEqual(b.get(self.model,2),0);self.assertEqual(b.get(b.context+28),self.app)
        self.assertEqual(bytes(b.u.mem_read(b.heap,92)),token)
    def test_06_it_real_new_layout_heap_and_cleanup(self):
        b=NativeSceneBench(self.compiled,self.fixtures['IT'],role=2)
        self.assertEqual(b.finish_init(),SCENE_READY)
        app=b.get(b.context+28);self.assertEqual(b.get(app-28)+16,4996+32)
        self.assertEqual(b.get(b.counts+76,2),9);self.assertGreater(b.heap_free()[1],40000)
        b.record('fix1_ready','IT');b.borrowed_intact()
        self.assertEqual(b.finish_exit(),SCENE_EXITED);b.borrowed_intact()
        b.record('fix1_complete','IT')

    def test_07_en_current_dependency_lifecycle(self):
        b=self.b;self.assertEqual(b.get(self.app-28)+16,4996+32)
        self.assertEqual(b.get(b.counts+76,2),9);b.record('fix1_current_ready','EN')
        self.assertEqual(b.finish_exit(),SCENE_EXITED);b.borrowed_intact()
        b.record('fix1_current_complete','EN')

if __name__=='__main__':unittest.main()
