"""ROM/CPU-free pre-guest field contract; native volatiles must survive the join."""
from pathlib import Path
import copy,gzip,importlib.util,json,struct,tempfile,unittest

PATH=Path(__file__).parents[1]/'tools/congela_fs_exec_sync_join_contract.py'
spec=importlib.util.spec_from_file_location('join_freeze',PATH);M=importlib.util.module_from_spec(spec);spec.loader.exec_module(M)
FILE,ARC,TOP=0x23BEDD0,0x21E3654,0x23BEEC0


def parent():
    fixtures=[];groups=[];cases=[]
    for group in range(4):
        members=[];error=group%2
        for language,ordinal in [('EN',group),('IT',group),('EN',group+4),('IT',group+4)]:
            member=dict(language=language,ordinal=ordinal);members.append(member)
            fixtures.append(dict(**member,plus=group//2,seed=group//2,translated_result=error))
        frame=bytearray([0xA5]*416);struct.pack_into('<2I',frame,104,ARC,0x20D7928)
        struct.pack_into('<I',frame,FILE-(TOP-416)+8,ARC)
        struct.pack_into('<I',frame,FILE-(TOP-416)+20,error)
        entry=[0,0x6000009F,0x6000001F,FILE+48,FILE,0,FILE,16,FILE,0x99999902,0xAAAAAA03,0xBBBBBB04,0,TOP-312,0x20D76A4,0x6000001F]
        row=dict(returned=entry,halt_pc='0x20d7768',frame_after=frame.hex(),guard_before='a5'*56,guard_after='a5'*56,
                 archive_after='00'*92,whole_ram_sha256='ab'*32,policy=dict(not_running=False),observe=True,fill=0xA5,services=[])
        groups.append(dict(ordinal=group,members=members))
        for label in ('normal','off','fill39','not_running'):
            cases.append(dict(group=group,label=label,result=copy.deepcopy(row)))
    return dict(schema='native-fs-next-isolated-v1',cpu_executed=True,compiler_invoked=False,probe_only=False,
                fixtures=fixtures,groups=groups,cases=cases)


class FreezeTests(unittest.TestCase):
    def freeze(self,value):
        with tempfile.TemporaryDirectory()as directory:
            path=Path(directory)/'parent.json.gz'
            with gzip.open(path,'wb')as stream:stream.write(json.dumps(value).encode())
            return M.freeze(path)

    def test_sixteen_cells_keep_native_volatiles_and_entire_frame(self):
        result=self.freeze(parent());self.assertEqual(len(result['cells']),16)
        for cell in result['cells']:
            before,after=cell['checkpoint_regs'],cell['expected_returned']
            self.assertEqual(after[1:3],[0x6000009F,0x6000001F])
            self.assertEqual(after[14],0x20D76A4)
            self.assertEqual(after[4],ARC);self.assertEqual(after[13],TOP-304)
            self.assertEqual(after[0],int(cell['stored_error']==0))
            self.assertEqual(after[15],0x6000001F if cell['stored_error']==0 else 0x2000001F)
            self.assertEqual([i for i in range(16)if before[i]!=after[i]],
                             [0,4,13]if cell['stored_error']==0 else[4,13,15])
            self.assertEqual(cell['expected_memory_unchanged'],True)

    def test_wrong_entry_pop_and_duplicate_members_rejected(self):
        for change in ('probe','r0','sp','target','truncated','error_type','duplicate'):
            value=parent();row=value['cases'][0]['result']
            if change=='probe':value['probe_only']=True
            elif change=='r0':row['returned'][0]=1
            elif change=='sp':row['returned'][13]+=4
            elif change=='target':
                raw=bytearray.fromhex(row['frame_after']);struct.pack_into('<I',raw,108,0x20D792C);row['frame_after']=raw.hex()
            elif change=='truncated':row['frame_after']=row['frame_after'][:-2]
            elif change=='error_type':value['fixtures'][0]['translated_result']=False
            else:value['groups'][0]['members'][0]=dict(value['groups'][0]['members'][1])
            with self.subTest(change=change),self.assertRaises(ValueError):self.freeze(value)


if __name__=='__main__':unittest.main()
