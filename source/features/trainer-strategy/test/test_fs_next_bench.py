"""Next empty-archive dataflow and the inactive RUNNING branch."""
from pathlib import Path
import importlib.util,unittest


def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


M=load('next_empty_bench',Path(__file__).with_name('fs_next_bench.py'))
T=load('next_parent_fixture',Path(__file__).with_name('test_release_wakeup_bench.py'))


def fixture(value=0,guard=None):
    f=T.fixture(value,guard);r=M.Q.predict(f)
    return dict(entry=r['returned'],captured408=(M.Q.guard_before(f,0xA5)+bytes.fromhex(r['frame_after'])).hex(),
        archive_before=r['archive_after'],translated_result=value,parent_whole_ram_sha256='0'*64)


class Source(unittest.TestCase):
    def test_original_bridge_native_next_and_null_result(self):
        for value in(0,1):
            f=fixture(value);r=M.predict(f);expected=list(f['entry']);expected[0]=0;expected[14]=0x20D76A4
            self.assertEqual((len(r['flow']),len(r['stores']),len(r['reads']),r['steps'],r['native_peak']),(62,9,17,63,104))
            self.assertEqual(r['unique_native_starts'],62);self.assertEqual(r['returned'],expected);self.assertEqual(r['services'],[])
            entry=list(f['entry']);entry[0]=M.ARC;entry[14]=M.RETURN
            self.assertEqual(r['incoming_next'],entry)

    def test_running_and_not_running_converge_without_the_same_native_store(self):
        f=fixture();normal=M.predict(f);counter=M.predict(f,not_running=True)
        self.assertEqual((len(counter['flow']),len(counter['stores']),len(counter['reads']),counter['steps']),(56,8,15,57))
        for key in('returned','frame_after','archive_after'):self.assertEqual(normal[key],counter[key])
        self.assertEqual([e['pc']for e in normal['flow']if e['pc']not in{e['pc']for e in counter['flow']}],
            ['0x20d7638','0x20d763c','0x20d7640','0x20d7644','0x20d7648','0x20d764c'])
        self.assertEqual(normal['stores'][-1]['before'],'13000000');self.assertEqual(normal['stores'][-1]['value'],3)

    def test_parent408_and_only_live_caller312_preservation(self):
        f=fixture();r=M.predict(f);before=bytes.fromhex(r['frame_before']);after=bytes.fromhex(r['frame_after'])
        self.assertEqual(before[8:],bytes.fromhex(f['captured408']));self.assertEqual(after[104:],before[104:])
        self.assertEqual(after[:72],before[:72]);self.assertNotEqual(after[72:104],before[72:104])
        self.assertEqual([e['address']for e in r['stores'][:8]],[M.FRAME+72+4*i for i in range(8)])

    def test_new64_fill_preserves_every_captured_parent_byte(self):
        f=fixture(guard=bytes(range(56)));a=M.predict(f);b=M.predict(f,fill=0x39)
        self.assertEqual(bytes.fromhex(a['frame_before'])[8:],bytes.fromhex(b['frame_before'])[8:])
        self.assertEqual(bytes.fromhex(b['frame_before'])[:8],bytes([0x39])*8)
        self.assertEqual(M.guard_before(0x39),bytes([0x39])*56)
        self.assertEqual(a['flow'],b['flow']);self.assertEqual(a['stores'],b['stores']);self.assertEqual(a['reads'],b['reads'])

    def test_rotated_idle_test_changes_carry_until_final_cmp(self):
        a={e['pc']:e['regs']for e in M.predict(fixture())['flow']}
        b={e['pc']:e['regs']for e in M.predict(fixture(),not_running=True)['flow']}
        self.assertEqual(a['0x20d766c'][15],0x4000009F);self.assertEqual(b['0x20d766c'][15],0x6000009F)
        self.assertEqual(a['0x20d7680'][15],b['0x20d7680'][15]);self.assertEqual(a['0x20d7680'][15],0x6000009F)

    def test_strict_flags_checkpoint_and_no_callback_inputs(self):
        with self.assertRaises(ValueError):M.predict(fixture(),not_running=1)
        with self.assertRaises(ValueError):M.predict(fixture(),fill=True)
        f=fixture();f['entry'][0]=False
        with self.assertRaises(ValueError):M.predict(f)
        f=fixture();f['archive_before']=f['archive_before'][:176]+'00040000'
        with self.assertRaises(ValueError):M.predict(f)


if __name__=='__main__':unittest.main()
