"""Finite Scene behavior; synthetic native services remain explicit seams."""
import os
import tempfile
import unittest
from scene_bench import *

class SceneTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory(prefix='scene-a-');cls.addClassCleanup(cls.temp.cleanup)
        cls.compiled,cls.receipt=compile_scene(Path(cls.temp.name),scaffold=os.environ.get('SGP_UI_SCENE_RED')=='1')
    def test_execution_wait_preserves_context_token_and_step(self):
        b=SceneBench(self.compiled);b.put(IME,0)
        before=bytes(b.u.mem_read(b.context,64)),bytes(b.u.mem_read(b.heap,92)),b.get(STEP)
        self.assertEqual(b.scene(),SCENE_MORE)
        self.assertEqual((bytes(b.u.mem_read(b.context,64)),bytes(b.u.mem_read(b.heap,92)),b.get(STEP)),before)
    def test_invalid_context_never_claims_successful_exit(self):
        b=SceneBench(self.compiled);b.put(b.context,0x31435355)
        self.assertEqual(b.scene('exit'),SCENE_HOLD)
        self.assertEqual(b.get(b.context+28),0)
    def test_full_image_has_required_real_callbacks_and_final_gate(self):
        code,symbols=self.compiled
        self.assertLessEqual(len(code),65536)
        for name in ('ui_scene_init','ui_scene_main','ui_scene_exit','settings_final_check'):
            self.assertIn(name,symbols);self.assertEqual(symbols[name]&1,1)
        self.assertEqual(self.receipt['undefined'],[])

if __name__=='__main__':unittest.main()
