"""Portable source, frame and lower-model contracts; no guest execution."""
from pathlib import Path
import importlib.util, types, unittest
from unittest.mock import patch


def tool():
    p = Path(__file__).parents[1] / 'tools/attribuisci_fs_open.py'
    s = importlib.util.spec_from_file_location('fs_open_portable', p)
    m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
    return m


class Portable(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.z = tool()

    def test_parent_and_finite_edit_drift_refused(self):
        z = self.z
        with patch.object(z.A, 'PARENT_SHA256', '0'*64), self.assertRaisesRegex(ValueError, 'source drift'): z.A.bind(z.O)
        with self.assertRaisesRegex(ValueError, 'recipe occurrence'):
            z.A.rewrite(z.O, z.R, 'Reader.write', [('missingOpenSource', '', 1)], {}, 'narc_reader')

    def test_exact_stack_extent_and_no_heap_projection_extension(self):
        z = self.z
        self.assertEqual(z.O.H.OUTER - (z.TOP - 152), 472)
        self.assertEqual(z.O.H.OUTER - (z.TOP - 208), 528)
        self.assertLessEqual(528, 608)
        self.assertEqual(z.ID + 16, z.TOP - 136)
        self.assertEqual(z.FILE + 72, z.TOP - 40)
        self.assertEqual(sum(b-a for a,b in z.H.PROJECTION), 1124)
        self.assertFalse(any(a < z.TOP and b > z.TOP - 208 for a,b in z.H.PROJECTION))

    def test_attachment_only_clones_local_sdk_and_never_creates_a_cpu(self):
        z = self.z; before = dict(z.R.SDK)
        r = types.SimpleNamespace(code={})
        for name in ('step','service','write','read'):
            setattr(r, name, types.MethodType(getattr(z.R.Reader,name), r))
        init = types.SimpleNamespace(base_step=r.step, base_write=r.write)
        d = types.SimpleNamespace(fs_observer=init, qualified={'fs_open_code':{z.ENTRY:(4,False)}})
        with patch.object(z.R, 'Uc') as factory: observer = z.OpenObserver(d,r)
        factory.assert_not_called()
        self.assertIs(r.step.__self__, observer)
        self.assertNotIn(z.ENTRY, init.base_step.__func__.__globals__['SDK'])
        self.assertNotIn(z.O.ENTRY, init.base_step.__func__.__globals__['SDK'])
        self.assertEqual(init.base_step.__func__.__globals__['SDK'][z.CONVERT], 'FS_ConvertPathToFileID')
        self.assertEqual(z.R.SDK, before)
        self.assertFalse({'Uc','mem_write','reg_write','emu_start'} & set(z.OpenObserver.__init__.__code__.co_names))

    def fixture(self, clobber=False):
        z = self.z; memory = {}; writes = []
        def store(a, data):
            writes.append((a, bytes(data)))
            for i,v in enumerate(data): memory[a+i]=v
        def read(a,n): return bytes(memory.get(a+i, 0x79) for i in range(n))
        store(0x210F198, b'a/0/1/1\0'); store(z.FILE, bytes(range(72))); writes.clear()
        vector = [z.ID, 0x210F198, 0, 0, z.FILE, 310, z.H.MON, 0] + list(z.H.N.COOKIES[4:]) + [0,z.ID,0x20D828C,0x1F]
        keys = list(z.B.R) + [z.O.H.R.UC_ARM_REG_SP, z.O.H.R.UC_ARM_REG_LR, z.UC_ARM_REG_CPSR]
        regs = dict(zip(keys,vector))
        u = types.SimpleNamespace(reg_write=lambda k,v:regs.__setitem__(k,v), reg_read=lambda k:regs.get(k,0), mem_write=store)
        r = types.SimpleNamespace(u=u, regs=lambda:[regs[k]for k in keys], read_bytes=read,
            initialized=True,file=z.FILE,open=False,cursor=None,path=None,archive=None,clobber=clobber,models=[],
            data={'11':dict(path='a/0/1/1',raw=b'project synthetic provider',oracle={'file_id':140})})
        observer = z.OpenObserver.__new__(z.OpenObserver)
        observer.active=True; observer.reader=r; observer.driver=types.SimpleNamespace(open_fast_value=2)
        return observer,r,regs,writes,read

    def test_lower_models_write_only_id8_and_return_arm_with_value_contract(self):
        z = self.z
        for clobber in (False,True):
            observer,r,regs,writes,read = self.fixture(clobber); before = read(z.FILE,72)
            observer.service(z.CONVERT)
            self.assertEqual(writes,[(z.ID,z.struct.pack('<II',z.ARC,140))])
            self.assertFalse(regs[z.UC_ARM_REG_CPSR]&32)
            self.assertEqual(r.models[0]['result_r0'],1)
            for key,value in zip(z.B.R[:4],(z.FILE,z.ARC,140,0xA5000003 if clobber else 0)):regs[key]=value
            regs[z.O.H.R.UC_ARM_REG_LR]=0x20D82A4; regs[z.UC_ARM_REG_CPSR]=0x2000001F
            observer.service(z.FAST)
            self.assertTrue(r.open); self.assertEqual(r.cursor,0)
            self.assertEqual(r.models[-1]['result_r0'],2)
            self.assertFalse(regs[z.UC_ARM_REG_CPSR]&32)
            self.assertEqual(read(z.FILE,72),before)
            self.assertEqual(len(writes),1)
            self.assertEqual([e['name']for e in r.models],['FS_ConvertPathToFileID','FS_OpenFileFast'])

    def test_wrong_output_pointer_refused_before_any_write(self):
        z = self.z; observer,r,regs,writes,read = self.fixture()
        regs[z.B.R[0]]=z.FILE
        with self.assertRaisesRegex(ValueError,'output buffer'):observer.service(z.CONVERT)
        self.assertEqual(writes,[])

    def test_counter_is_unqualified_before_observing_false_condition_hooks(self):
        z = self.z
        with patch.object(z,'FALSE_CONDITIONAL_HOOKS',None), self.assertRaisesRegex(ValueError,'qualify conditional-false'):
            z.expected_open(dict(open_fast_value=1,pp_clobber=False),'fs_open_false')
        for value in (0,True,3):
            with patch.object(z.O.Driver,'__init__') as parent, self.assertRaisesRegex(ValueError,'finite Open controls'):
                z.Driver(open_fast_value=value)
            parent.assert_not_called()

    def test_legacy136_postimage_cannot_disagree_with_extended152(self):
        z = self.z
        r = dict(fs_open=dict(entry=[],returned=[],flow=[]), pp_reader=dict(
            stack152_before='00'*152,stack_frame_before='00'*136,
            stack_guard_range=[z.TOP-208,z.ID],stack_guard_before='00'*56,
            stack_guard_after='00'*56,stack152_after='00'*152,stack_frame_hex='01'+'00'*135))
        with patch.object(z,'require_init_native'), patch.object(z,'expected_open',return_value=dict(entry=[],returned=[],flow=[])):
            with self.assertRaisesRegex(ValueError,'postimages agree'):z.require_open(r,{})


if __name__ == '__main__': unittest.main()
