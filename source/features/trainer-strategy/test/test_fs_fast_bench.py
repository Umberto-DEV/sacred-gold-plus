"""Portable native Fast ownership, ABI and command-model contracts."""
from pathlib import Path
import importlib.util,types,unittest,copy
from unittest.mock import patch


def tool():
    p=Path(__file__).parents[1]/'tools/attribuisci_fs_fast.py';s=importlib.util.spec_from_file_location('fast_portable',p)
    m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


class Portable(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.z=tool()

    def test_source_drift_and_missing_edit_rejected(self):
        z=self.z
        with patch.object(z.A,'PARENT_SHA256','0'*64),self.assertRaisesRegex(ValueError,'source drift'):z.A.bind(z.H)
        with self.assertRaisesRegex(ValueError,'recipe occurrence'):
            z.A.rewrite(z.H,z.R,'Reader.step',[('nonexistentFastSource','',1)],{},'narc_reader')

    def test_dead_directory_overlap_does_not_expand_bound_or_mask(self):
        z=self.z
        self.assertEqual(z.SP-z.DIR,64);self.assertEqual(z.ID-z.DIR,88)
        self.assertEqual(z.H.H.H.OUTER-z.DIR,560);self.assertEqual(z.TOP-296,z.H.H.H.OUTER-616)
        self.assertNotIn(z.ENTRY,z.SDK);self.assertEqual(z.SDK[z.SEND],'FSi_SendCommand')
        self.assertEqual(z.root_step.__code__,z.H.reader_step.__code__)
        self.assertEqual(sum(b-a for a,b in z.H.H.H.PROJECTION),1124)

    def test_return_restores_lr_but_keeps_volatile_policy_and_native_status(self):
        z=self.z
        for clobber in(False,True):
            r=dict(send_value=2,pp_clobber=clobber);out=z.expected_fast(r)
            self.assertEqual(out['entry'][:4],[z.FILE,z.ARC,140,0])
            self.assertEqual(out['send']['entry'][:4],[z.FILE,6,140,0])
            self.assertEqual(out['send']['entry'][13:15],[z.SP,0x20D8244])
            self.assertEqual(out['returned'][0:4],[1,16,0xA5000002 if clobber else 140,0xA5000003 if clobber else 0])
            self.assertEqual(out['returned'][13:],[z.ID,z.RETURN,0x2000001F])
        with self.assertRaises(ValueError):z.expected_fast(r,[0]*16)

    def test_file_update_preserves_other56_bytes(self):
        z=self.z;before=bytes(range(72));after=z.file_after(before)
        expected={i for off in(8,12,48,52)for i in range(off,off+4)}
        self.assertTrue(all(after[i]==before[i]for i in range(72)if i not in expected))
        self.assertEqual(z.struct.unpack_from('<II',after,48),(z.ARC,140))
        self.assertEqual(z.struct.unpack_from('<I',after,12),(16,))
        zero=z.file_after(before,0)
        self.assertEqual(zero[:12]+zero[16:],after[:12]+after[16:])

    def test_native_fast_routes_once_without_opaque_fast_model(self):
        z=self.z;events=[];r=types.SimpleNamespace(file=z.FILE,open=False,regs=lambda:[0]*16,read_bytes=lambda a,n:b'v'*n)
        o=z.FastObserver.__new__(z.FastObserver);o.reader=r;o.driver=types.SimpleNamespace(open_observer=types.SimpleNamespace(active=True),convert_observer=types.SimpleNamespace(ledger=lambda:{}),fast_variant='current')
        o.active=False;o.result=dict(entry=None,flow=[]);o.root_step=lambda *a:events.append('root-native');o.parent_step=lambda *a:events.append('opaque-parent')
        o.step(None,z.ENTRY,4,None)
        self.assertEqual(events,['root-native']);self.assertIs(o.active,True)

    def test_send_opens_host_ledger_without_guest_file_or_archive_write(self):
        z=self.z
        for clobber in(False,True):
            memory={};writes=[]
            def write(a,b):
                writes.append((a,bytes(b)))
                for i,v in enumerate(b):memory[a+i]=v
            def read(a,n):return bytes(memory.get(a+i,0x73)for i in range(n))
            file=bytearray(range(72))
            for off,v in((8,z.ARC),(48,z.ARC),(52,140)):z.struct.pack_into('<I',file,off,v)
            write(z.FILE,file);write(z.ID,z.struct.pack('<II',z.ARC,140));writes.clear()
            vec=z.expected_fast(dict(pp_clobber=clobber,send_value=2))['send']['entry'];keys=list(z.B.R)+[z.R.UC_ARM_REG_SP,z.R.UC_ARM_REG_LR,z.R.UC_ARM_REG_CPSR];regs=dict(zip(keys,vec))
            u=types.SimpleNamespace(reg_write=lambda k,v:regs.__setitem__(k,v),reg_read=lambda k:regs.get(k,0),mem_write=write)
            r=types.SimpleNamespace(u=u,regs=lambda:[regs[k]for k in keys],read_bytes=read,initialized=True,file=z.FILE,
                open=False,archive=None,cursor=None,path='a/0/1/1',clobber=clobber,models=[],data={'11':dict(path='a/0/1/1',raw=b'project synthetic archive')})
            o=z.FastObserver.__new__(z.FastObserver);o.reader=r;o.driver=types.SimpleNamespace(send_value=2);o.active=True
            o.service(z.SEND)
            self.assertEqual(writes,[]);self.assertEqual(read(z.FILE,72),file)
            self.assertIs(r.open,True);self.assertEqual(r.cursor,0);self.assertEqual(r.models[0]['result_r0'],2)
            self.assertEqual(regs[z.R.UC_ARM_REG_LR],0x20D8244);self.assertFalse(regs[z.R.UC_ARM_REG_CPSR]&32)
            r.open=False;r.archive=None;regs[z.B.R[1]]=14
            with self.assertRaises(ValueError):o.service(z.SEND)


if __name__=='__main__':unittest.main()
