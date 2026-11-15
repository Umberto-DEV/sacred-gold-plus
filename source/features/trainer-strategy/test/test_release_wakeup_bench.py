"""Composition must preserve caller results and still prove native activation."""
from pathlib import Path
import importlib.util,unittest


def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


M=load('release_wakeup_composed',Path(__file__).with_name('fs_release_wakeup_bench.py'))
T=load('release_wakeup_parent_fixture',Path(__file__).with_name('test_fs_release_bench.py'))


def fixture(result=0,guard=None):
    f=T.fixture(result);guard=bytes([0xA5])*56 if guard is None else guard
    return dict(f,frame=(guard[-24:]+bytes.fromhex(f['frame'])).hex(),captured_parent_guard56=guard.hex())


class Composition(unittest.TestCase):
    def test_full_native_context_and_original_release_result(self):
        for value in(0,1):
            f=fixture(value);r=M.predict(f);p=M.E.predict(M.release_fixture(f))
            self.assertEqual((len(r['flow']),len(r['stores']),len(r['reads']),r['steps'],r['native_peak']),(55,15,14,56,40))
            self.assertEqual(len({e['pc']for e in r['flow']}),44)
            self.assertEqual(r['returned'],p['returned']);self.assertEqual(bytes.fromhex(r['frame_after'])[24:].hex(),p['frame_after'])
            self.assertEqual(r['archive_after'],p['archive_after']);self.assertEqual(r['services'],[])

    def test_same_code_bypass_converges_caller_but_misses_native_stack(self):
        f=fixture();native=M.predict(f);counter=M.predict(f,bypass_wakeup=True)
        self.assertEqual((len(counter['flow']),len(counter['stores']),len(counter['reads']),counter['steps'],counter['native_peak']),(34,9,7,36,16))
        self.assertEqual(counter['returned'],native['returned']);self.assertEqual(counter['archive_after'],native['archive_after'])
        self.assertEqual(bytes.fromhex(counter['frame_after'])[24:],bytes.fromhex(native['frame_after'])[24:])
        self.assertEqual([i for i,(a,b)in enumerate(zip(bytes.fromhex(counter['frame_after']),bytes.fromhex(native['frame_after'])))if a!=b],list(range(24)))
        self.assertEqual(len(counter['services']),1);self.assertFalse(counter['boundaries'][0]['native'])

    def test_actual_nested_volatile_return_then_epilogue_convergence(self):
        f=fixture();r=M.predict(f);boundary=r['boundaries'][0]
        self.assertTrue(boundary['native']);self.assertEqual(boundary['entry'][13],M.TOP-328)
        self.assertEqual(boundary['returned'][:3],[0x80,0x6000009F,0x6000009F])
        self.assertEqual(boundary['returned'][14],0x20D1F30)
        self.assertEqual(r['returned'][2],0x6000001F)
        native_pcs=[e['pc']for e in r['flow']]
        self.assertEqual(native_pcs.count('0x20d3a38'),2);self.assertEqual(native_pcs.count('0x20d3a4c'),2)

    def test_captured_guard_equation_with_nonuniform_original(self):
        f=fixture(guard=bytes(range(56)));M.predict(f)
        for fill in(0xA5,0x39):self.assertEqual(M.guard_before(f,fill),bytes([fill])*24+bytes(range(32)))
        self.assertEqual(bytes.fromhex(f['frame'])[:24],bytes(range(32,56)))
        bad=dict(f);bad['frame']='00'+bad['frame'][2:]
        with self.assertRaises(ValueError):M.predict(bad)

    def test_typed_policy_and_actual_release_input(self):
        with self.assertRaises(ValueError):M.predict(fixture(),bypass_wakeup=1)
        bad=fixture();bad['entry'][15]|=128
        with self.assertRaises(ValueError):M.predict(bad)


if __name__=='__main__':unittest.main()
