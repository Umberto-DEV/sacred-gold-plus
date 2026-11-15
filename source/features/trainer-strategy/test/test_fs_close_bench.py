"""Portable Close role dispatch, cleanup ownership and residual ABI checks."""
from pathlib import Path
import importlib.util,types,unittest
from unittest.mock import patch


def tool():
    p=Path(__file__).parents[1]/'tools/attribuisci_fs_close.py';s=importlib.util.spec_from_file_location('close_portable',p)
    m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


class Portable(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.z=tool()

    def data(self):
        return {'pp_reader':{'11':dict(raw=b'Z'*9000,path='a/0/1/1',oracle=dict(btaf=16,btnf=3796,btnf_bytes=16,member_bytes=16,member_archive_offset=8780))}}

    def test_source_drift_and_missing_edit_rejected(self):
        z=self.z
        with patch.object(z.A,'PARENT_SHA256','0'*64),self.assertRaisesRegex(ValueError,'source drift'):z.A.bind(z.H)
        with self.assertRaisesRegex(ValueError,'recipe occurrence'):
            z.A.rewrite(z.H,z.R,'Reader.step',[('missingCloseSource','',1)],{},'narc_reader')

    def test_two_send_roles_share_address_and_no_expanded_guest_mask(self):
        z=self.z
        self.assertNotIn(z.ENTRY,z.SDK);self.assertEqual(z.SDK[z.SEND],'FSi_SendCommand')
        self.assertEqual(len(set(z.SDK.values())),4)
        self.assertEqual(z.SP,z.TOP-144);self.assertEqual(z.H.SP,z.TOP-176)
        self.assertEqual(z.H.H.H.H.OUTER-z.DIR,560)
        self.assertEqual(z.root_step.__code__,z.H.root_step.__code__)
        self.assertEqual(sum(b-a for a,b in z.H.H.H.H.PROJECTION),1124)

    def test_cleanup_preserves_sixty_bytes_and_argument_identity(self):
        z=self.z;before=bytes(range(72));after=z.cleanup_file(before)
        touched={i for off in(8,12,16)for i in range(off,off+4)}
        self.assertTrue(all(before[i]==after[i]for i in range(72)if i not in touched))
        self.assertEqual(z.struct.unpack_from('<III',after,8),(0,0,14))
        counter=z.cleanup_file(before,z.ARC)
        self.assertEqual(counter[:8]+counter[12:],after[:8]+after[12:])

    def test_native_close_retains_residual_lr_r1_and_new_flags(self):
        z=self.z
        for clobber in(False,True):
            for value in(1,2):
                r=dict(pp_clobber=clobber,close_value=value);p=z.expected_close(r,self.data())
                self.assertEqual(p['send']['entry'][:2],[z.FILE,8]);self.assertEqual(p['send']['entry'][13:15],[z.SP,0x20D82D0])
                self.assertEqual(p['returned'][:3],[1,0,0xA5000002 if clobber else 16])
                self.assertEqual(p['returned'][4],28);self.assertEqual(p['returned'][13:],[z.TOP-136,0x20D82D0,0x2000003F])
                counter=z.expected_close(r,self.data(),z.ARC)
                self.assertEqual(counter['returned'],p['returned'])
                self.assertEqual(next(e['regs'][0]for e in counter['flow']if e['pc']=='0x20d82e0'),z.ARC)

    def test_close_active_routes_native_once_then_delegates_other_send(self):
        z=self.z;events=[];r=types.SimpleNamespace(file=z.FILE,open=True,regs=lambda:[0]*16,read_bytes=lambda a,n:b'v'*n)
        o=z.CloseObserver.__new__(z.CloseObserver);o.reader=r;o.active=False;o.result=dict(entry=None,flow=[])
        o.driver=types.SimpleNamespace(fast_observer=types.SimpleNamespace(active=False),convert_observer=types.SimpleNamespace(ledger=lambda:{}),close_variant='current')
        o.root_step=lambda *a:events.append('root-native');o.parent_step=lambda *a:events.append('parent')
        o.step(None,z.ENTRY,4,None);self.assertEqual(events,['root-native']);self.assertIs(o.active,True)
        o.active=False;o.base_service=lambda pc:events.append('send-open-parent');o.service(z.SEND)
        self.assertEqual(events,['root-native','send-open-parent'])

    def test_send_close_updates_only_host_ledger_without_guest_cleanup(self):
        z=self.z
        for clobber in(False,True):
            data=self.data();resource=data['pp_reader']['11'];file=bytearray(range(72))
            for off,val in((8,z.ARC),(12,16),(16,14),(48,z.ARC),(52,140)):z.struct.pack_into('<I',file,off,val)
            memory={z.FILE+i:v for i,v in enumerate(file)};writes=[]
            read=lambda a,n:bytes(memory.get(a+i,0x73)for i in range(n))
            vec=z.expected_close(dict(pp_clobber=clobber,close_value=2),data)['send']['entry']
            keys=list(z.B.R)+[z.R.UC_ARM_REG_SP,z.R.UC_ARM_REG_LR,z.R.UC_ARM_REG_CPSR];regs=dict(zip(keys,vec))
            u=types.SimpleNamespace(reg_write=lambda k,v:regs.__setitem__(k,v),reg_read=lambda k:regs.get(k,0),mem_write=lambda a,b:writes.append((a,b)))
            r=types.SimpleNamespace(u=u,regs=lambda:[regs[k]for k in keys],read_bytes=read,initialized=True,file=z.FILE,open=True,
                archive=resource['raw'],cursor=8796,path='a/0/1/1',read_count=7,clobber=clobber,models=[],data={'11':resource})
            o=z.CloseObserver.__new__(z.CloseObserver);o.reader=r;o.active=True;o.driver=types.SimpleNamespace(close_value=2)
            o.service(z.SEND)
            self.assertEqual(writes,[]);self.assertEqual(read(z.FILE,72),file);self.assertIs(r.open,False)
            self.assertEqual(r.cursor,8796);self.assertEqual(r.models[0]['command'],8);self.assertEqual(r.models[0]['result_r0'],2)
            self.assertFalse(regs[z.R.UC_ARM_REG_CPSR]&32)
            r.open=True;regs[z.B.R[0]]=z.FILE;regs[z.B.R[1]]=7
            with self.assertRaises(ValueError):o.service(z.SEND)


if __name__=='__main__':unittest.main()
