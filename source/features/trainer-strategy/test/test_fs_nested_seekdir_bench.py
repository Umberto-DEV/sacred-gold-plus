"""Nested dispatch ABI and an input projection with convergent final state."""
from pathlib import Path
import copy,importlib.util,struct,unittest


def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


M=load('nested_seekdir_source_test',Path(__file__).with_name('fs_nested_seekdir_bench.py'))
F=load('nested_seekdir_synthetic_parent',Path(__file__).with_name('test_fs_default_findpath_bench.py'))


def fixture():
    old=F.fixture();p=M.H.predict(old)
    return dict(parent_default_fixture=old,entry=p['returned'],frame=p['guard_after'][-48:]+p['frame_after'],
                archive_before=p['archive_after'],guard='5a'*24+p['guard_after'][:64])


class Source(unittest.TestCase):
    def test_counts_full_stopped_abi_and_stored_command_remains4(self):
        f=fixture();before=copy.deepcopy(f);r=M.predict(f)
        self.assertEqual((len(r['flow']),len(r['stores']),len(r['reads']),r['steps'],r['native_peak']),(24,7,6,25,24))
        self.assertEqual(r['returned'][:2],[M.FILE,M.RETURN]);self.assertEqual(r['returned'][5:8],[M.ARC,4,2])
        self.assertEqual(r['returned'][13:16],[M.TOP-544,0x20D6984,0x6000001F])
        self.assertEqual(struct.unpack_from('<3I',bytes.fromhex(r['frame_after']),M.FILE-M.FRAME+12),(0x45,4,2))
        self.assertEqual(r['services'],[]);self.assertEqual(r['host_stores'],[]);self.assertEqual(f,before)

    def test_promoted_guard_is_written_but_new_guard_is_preserved(self):
        f=fixture();r=M.predict(f);a,b=bytes.fromhex(r['frame_before']),bytes.fromhex(r['frame_after'])
        self.assertEqual(a[:24],b'\xa7'*24);self.assertNotEqual(a[:24],b[:24]);self.assertEqual(a[24:],b[24:])
        self.assertEqual(r['guard_before'],r['guard_after']);self.assertEqual(r['guard_after'],'5a'*24+'a7'*32)
        self.assertEqual([s['address']for s in r['stores'][:6]],[M.TOP-544+4*i for i in range(6)])

    def test_clear_sync_changes_input_and_temporal_evidence_but_not_final(self):
        normal=M.predict(fixture());projected=M.predict(fixture(),True)
        for key in('entry','returned','frame_before','frame_after','archive_after','guard_before','guard_after','steps','native_peak'):
            if key=='entry':continue
            self.assertEqual(normal[key],projected[key])
        self.assertNotEqual(normal['archive_before'],projected['archive_before'])
        self.assertEqual([i for i,(a,b)in enumerate(zip(normal['stores'],projected['stores']))if a!=b],[6])
        self.assertEqual([i for i,(a,b)in enumerate(zip(normal['reads'],projected['reads']))if a!=b],[2])
        self.assertEqual([a['pc']for a,b in zip(normal['flow'],projected['flow'])if a!=b],['0x20d68e8','0x20d68ec'])
        self.assertEqual(normal['stores'][6]['before'],'13020000');self.assertEqual(projected['stores'][6]['before'],'13000000')
        self.assertEqual(projected['input_projection'][0]['stage'],'before CPU')

    def test_literal_table_slot_and_native_owners_are_exact(self):
        r=M.predict(fixture());self.assertEqual(r['reads'][-1]['address'],M.TABLE+8)
        self.assertTrue(M.read_allowed(0x20D697C,M.TABLE+8,4));self.assertFalse(M.read_allowed(0x20D697C,M.TABLE+16,4))
        self.assertTrue(M.write_allowed(0x20D68F4,M.ARC+28,4));self.assertFalse(M.write_allowed(0x20D68F4,M.FILE+20,4))
        self.assertFalse(M.write_allowed(M.ENTRY,M.TOP-548,4));self.assertFalse(M.write_allowed(M.ENTRY,M.TOP-520,4))

    def test_projected_archive_cannot_be_presented_as_canonical_fixture(self):
        with self.assertRaises(ValueError):M.predict(fixture(),clear_sync=1)
        f=fixture();arc=bytearray.fromhex(f['archive_before']);struct.pack_into('<I',arc,28,0x13);f['archive_before']=arc.hex()
        with self.assertRaises(ValueError):M.predict(f)
        f=fixture();f['entry'][1]=4
        with self.assertRaises(ValueError):M.predict(f)


if __name__=='__main__':unittest.main()
