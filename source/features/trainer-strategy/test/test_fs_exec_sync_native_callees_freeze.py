"""A final Send digest can transfer only across the exact readonly tail."""
from pathlib import Path
import copy,importlib.util,struct,unittest

P=Path(__file__).parents[1]/'tools/congela_fs_exec_sync_native_contract.py'
s=importlib.util.spec_from_file_location('native_sync_freeze',P);M=importlib.util.module_from_spec(s);s.loader.exec_module(M)
TOP,FILE,ARC=0x23BEEC0,0x23BEDD0,0x21E3654


def row():
    frame=bytearray([0xA5])*304
    struct.pack_into('<6I',frame,0,FILE+48,1,0,0x23BEE28,0x210F198,0x20D80F8)
    for offset,value in((0,ARC+32),(4,0),(8,ARC),(12,0x45),(16,4),(20,2)):
        struct.pack_into('<I',frame,FILE-(TOP-304)+offset,value)
    entry=[FILE,0x2000009F,0x2000001F,FILE+48,ARC,0,FILE,16,FILE,0x99999902,0xAAAAAA03,0xBBBBBB04,0,TOP-304,0x20D7928,0x2000001F]
    at_call=list(entry);at_call[14]=0x20D78D8
    returned=list(entry);returned[0]=1
    final=list(returned);final[3:8]=list(struct.unpack_from('<5I',frame));final[13]+=24
    service=dict(pc='0x20d7744',entry=entry,returned=returned,result=1,
        frame_before=frame.hex(),frame_after=frame.hex(),archive_before='00'*92,archive_after='00'*92)
    reads=[dict(pc='0x20d7928',address=TOP-304+4*i,bytes=4,hex=frame[4*i:4*i+4].hex())for i in range(6)]
    return dict(observe=True,fill=0xA5,fault=None,policy=dict(execute=1,clobber=False),services=[service],
        flow=[dict(pc='0x20d7924',regs=at_call),dict(pc='0x20d7928',regs=returned)],
        reads=reads,stores=[],frame_after=frame.hex(),archive_after='00'*92,guard_before='a5'*56,guard_after='a5'*56,
        returned=final,halt_pc='0x20d80f8',whole_ram_sha256='ab'*32)


class Transfer(unittest.TestCase):
    def test_join_has_no_fill_policy_but_older_families_require_one(self):
        f=dict(language='EN',ordinal=0,plus=0,seed=1,translated_result=0)
        r=dict(schema='native-fs-exec-sync-join-isolated-v1',fixtures=[f],
               groups=[dict(ordinal=0,members=[dict(language='EN',ordinal=0)])],
               cases=[dict(group=0,label='normal',result=dict(observe=True))])
        self.assertEqual(M.grouped(r,('EN',0,1,0))[0],f)
        r['cases'][0]['result']['fill']=0xA5
        with self.assertRaises(ValueError):M.grouped(r,('EN',0,1,0))
        r['schema']='native-release-wakeup-composed-v1';M.grouped(r,('EN',0,1,0))
        del r['cases'][0]['result']['fill']
        with self.assertRaises(ValueError):M.grouped(r,('EN',0,1,0))

    def test_memory_hash_is_explicitly_derived_not_captured_at_boundary(self):
        result=M.send_boundary(row())
        self.assertTrue(result['whole_sha_is_readonly_transfer'])
        self.assertFalse(result['whole_sha_captured_at_boundary'])
        self.assertEqual(result['derived_boundary_whole_ram_sha256'],'ab'*32)
        self.assertEqual(result['checkpoint_regs'][13],TOP-304)

    def test_last_pc_alone_does_not_prove_readonly_tail(self):
        value=row();value['flow'].insert(1,dict(pc='0x20d7788',regs=value['flow'][0]['regs']))
        with self.assertRaisesRegex(ValueError,'exact readonly Send tail'):M.send_boundary(value)

    def test_service_regs_pop_reads_and_final_bytes_are_bound(self):
        for change in('before_frame','before_arc','service_regs','pop_hex','pop_address','final_regs','guard','busy','policy_bool'):
            value=row();before=copy.deepcopy(value)
            if change=='before_frame':
                raw=bytearray.fromhex(value['services'][0]['frame_before']);raw[0]^=1;value['services'][0]['frame_before']=raw.hex()
            elif change=='before_arc':value['services'][0]['archive_after']='01'+value['services'][0]['archive_after'][2:]
            elif change=='service_regs':value['services'][0]['entry'][14]+=4
            elif change=='pop_hex':value['reads'][-1]['hex']='00000000'
            elif change=='pop_address':value['reads'][-1]['address']+=4
            elif change=='final_regs':value['returned'][4]^=4
            elif change=='guard':value['guard_after']='39'*56
            elif change=='busy':
                frame=bytearray.fromhex(value['frame_after']);struct.pack_into('<I',frame,FILE-(TOP-304)+20,0)
                value['frame_after']=value['services'][0]['frame_before']=value['services'][0]['frame_after']=frame.hex()
            else:value['policy']['execute']=True
            self.assertNotEqual(M.wire(value),M.wire(before),'negative fixture must actually change')
            with self.subTest(change=change),self.assertRaises(ValueError):M.send_boundary(value)


if __name__=='__main__':unittest.main()
