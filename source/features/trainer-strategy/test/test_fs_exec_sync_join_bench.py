"""The real NextNULL consumer must read the stored error and restore saved R4."""
from pathlib import Path
import copy,importlib.util,struct,unittest
from unittest.mock import patch


def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


M=load('sync_join_bench',Path(__file__).with_name('fs_exec_sync_join_bench.py'))
T=load('sync_join_prior_fixture',Path(__file__).with_name('test_fs_next_bench.py'))


def fixture(value=0):
    parent=T.fixture(value)
    # Earlier synthetic tests never read the original ExecuteSync saved pair.
    # Populate that pair here; actual private fixtures come unchanged from raw.
    captured=bytearray.fromhex(parent['captured408']);struct.pack_into('<2I',captured,96,M.ARC,M.RETURN)
    parent['captured408']=captured.hex();row=M.N.predict(parent)
    return dict(entry=row['returned'],frame=row['frame_after'],guard=M.N.guard_before(0xA5).hex(),
                archive_before=row['archive_after'],translated_result=value,parent_fixture=parent,parent_whole_ram_sha256='0'*64)


class JoinSource(unittest.TestCase):
    def test_both_errors_from_same_null_input_with_actual_native_volatiles(self):
        for error in(0,1):
            f=fixture(error);r=M.predict(f)
            self.assertEqual(r['returned'][0],int(error==0))
            self.assertEqual(r['returned'][1:3],f['entry'][1:3]);self.assertEqual(r['returned'][14],0x20D76A4)
            self.assertEqual(r['returned'][4],M.ARC);self.assertEqual(r['returned'][13],M.TOP-304)
            self.assertEqual(r['returned'][15],0x6000001F if error==0 else 0x2000001F)
            self.assertEqual([int(e['pc'],16)for e in r['flow']],list(M.PCS))
            self.assertEqual((r['steps'],len(r['reads']),r['stores'],r['services'],r['native_peak']),(8,3,[],[],0))
            self.assertEqual([e['address']for e in r['reads']],[M.FILE+20,M.SP,M.SP+4])

    def test_false_condition_is_recorded_and_zero_writes_mean_unchanged_full_frame(self):
        for error in(0,1):
            f=fixture(error);r=M.predict(f)
            self.assertEqual(r['frame_after'],f['frame']);self.assertEqual(r['archive_after'],f['archive_before'])
            rows={int(e['pc'],16):e['regs']for e in r['flow']}
            self.assertEqual(rows[0x20D7778][0],error)
            self.assertEqual(rows[0x20D777C][0],error)
            self.assertEqual(rows[0x20D7780][0],1)
            self.assertEqual(rows[0x20D7784][0],int(error==0))

    def test_invalid_non_null_sp_pop_and_stored_error_rejected(self):
        for change in('r0','sp','r4','lr','pop','error'):
            f=fixture()
            if change in('r0','sp','r4','lr'):f['entry'][{'r0':0,'sp':13,'r4':4,'lr':14}[change]]+=4
            else:
                raw=bytearray.fromhex(f['frame']);struct.pack_into('<I',raw,108 if change=='pop'else M.FILE-M.FRAME+20,2)
                f['frame']=raw.hex()
            with self.subTest(change=change),self.assertRaises(ValueError):M.predict(f)

    def test_guard_metadata_must_match_parent_image_not_only_its_length(self):
        f=fixture();image=bytearray([0xA5])*M.SIZE
        image[M.FRAME-M.BASE:M.TOP-M.BASE]=bytes.fromhex(f['frame'])
        image[M.ARC-M.BASE:M.ARC-M.BASE+92]=bytes.fromhex(f['archive_before'])
        f['parent_whole_ram_sha256']=M.sha(bytes(image))
        # Isolate the guard binding after the existing parent has been rebuilt.
        with patch.object(M.N,'initial_memory',return_value=bytes(image)),patch.object(M,'BODIES',{}),patch.object(M.N,'BODIES',{}):
            self.assertEqual(M.parent_memory(f,{}),bytes(image))
            f['guard']='39'*56
            with self.assertRaisesRegex(ValueError,'guard.*image'):
                M.parent_memory(f,{})


if __name__=='__main__':unittest.main()
