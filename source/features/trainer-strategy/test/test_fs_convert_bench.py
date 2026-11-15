"""Portable duplex-Init routing, readonly guard and lower Find contracts."""
from pathlib import Path
import importlib.util,types,copy,unittest
from unittest.mock import patch


def tool():
    p=Path(__file__).parents[1]/'tools/attribuisci_fs_convert.py'
    s=importlib.util.spec_from_file_location('fs_convert_portable',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


class Portable(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.z=tool()

    def test_parent_source_and_exact_edit_drift_refused(self):
        z=self.z
        with patch.object(z.A,'PARENT_SHA256','0'*64),self.assertRaisesRegex(ValueError,'source drift'):z.A.bind(z.H)
        with self.assertRaisesRegex(ValueError,'recipe occurrence'):
            z.A.rewrite(z.H,z.R,'Reader.step',[('missingDirectorySource','',1)],{},'narc_reader')

    def test_guest560_and_readonly616_do_not_extend_global608(self):
        z=self.z;outer=z.H.H.OUTER
        self.assertEqual(outer-z.DIR,560);self.assertEqual(outer-(z.TOP-296),616)
        self.assertEqual(z.DIR+72,z.TOP-168);self.assertEqual(z.DIR+88,z.ID)
        self.assertEqual(z.TOP-288,outer-608)
        self.assertEqual(z.RECIPES[1]['edits'],[dict(before='TOP-192<=sp',after='TOP-240<=sp',count=1)])
        self.assertFalse(any('608'in e['before']for e in z.RECIPES[4]['edits']))
        self.assertEqual(sum(b-a for a,b in z.H.H.PROJECTION),1124)

    def test_readonly_guard8_is_checked_through_global_end(self):
        z=self.z;prefix=bytes(range(8)).hex();guard=prefix+'71'*48
        base=dict(guard8_global_before=prefix,guard8_global_after=prefix,
            pp_reader=dict(stack_guard_range=[z.TOP-296,z.DIR],stack_guard_before=guard,stack_guard_after=guard))
        self.assertTrue(z.require_readonly_guard(base))
        for key in('entry','end','phase_before','phase_after','length','range'):
            r=copy.deepcopy(base)
            if key=='entry':r['guard8_global_before']='ff'*8
            elif key=='end':r['guard8_global_after']='ff'*8
            elif key=='phase_before':r['pp_reader']['stack_guard_before']='ff'*8+guard[16:]
            elif key=='phase_after':r['pp_reader']['stack_guard_after']='ff'*8+guard[16:]
            elif key=='length':r['pp_reader']['stack_guard_before']=r['pp_reader']['stack_guard_after']=guard[:-2]
            else:r['pp_reader']['stack_guard_range']=[z.TOP-288,z.DIR]
            with self.subTest(key=key),self.assertRaises(ValueError):z.require_readonly_guard(r)

    def test_native_convert_restores_r3_and_returns_with_find_lr(self):
        z=self.z
        for clobber in(False,True):
            r=dict(find_value=2,pp_clobber=clobber);p=z.expected_convert(r)
            self.assertEqual(p['inner']['entry'][0],z.DIR)
            self.assertEqual(p['inner']['returned'][1:3],[14,0])
            self.assertEqual(p['inner']['returned'][13:],[z.DIR,z.INIT_RETURN,0x1F])
            self.assertEqual(p['find']['entry'][:4],[z.DIR,0x210F198,z.ID,0])
            self.assertEqual(p['find']['returned'][0],2)
            self.assertEqual(p['returned'][0],1);self.assertEqual(p['returned'][3:6],[0,z.FILE,310])
            self.assertEqual(p['returned'][13:],[z.ID,0x20D81AC,0x2000001F])
            self.assertEqual(p['returned'][1:3],[0xA5000001,0xA5000002]if clobber else[0x210F198,z.ID])
        with self.assertRaisesRegex(ValueError,'actual Open call context'):z.expected_convert(r,[0]*16)

    def test_inner_init_routes_once_without_outer_observer_or_host_rebinding(self):
        z=self.z;events=[]
        r=types.SimpleNamespace(file=z.FILE,initialized=True,regs=lambda:[z.DIR,0x210F198,0,0,0x210F198,z.ID,z.H.H.MON,0]+
            list(z.H.H.N.COOKIES[4:])+[0,z.DIR,z.INIT_RETURN,0x1F],read_bytes=lambda a,n:b'v'*n)
        observer=z.ConvertObserver.__new__(z.ConvertObserver);observer.reader=r;observer.active=True;observer.inner_active=False
        observer.result=dict(flow=[],inner_init=dict(entry=None,returned=None,flow=[],before=None,after=None,frame_before=None,frame_after=None))
        observer.driver=types.SimpleNamespace(convert_variant='current')
        observer.root_step=lambda *args:events.append('native-root')
        observer.parent_step=lambda *args:events.append('outer-observer')
        observer.step(None,z.INIT,4,None)
        self.assertEqual(events,['native-root']);self.assertIs(observer.inner_active,True)
        self.assertEqual(r.file,z.FILE);self.assertIs(r.initialized,True)

    def fixture(self,clobber=False):
        z=self.z;memory={};writes=[]
        def write(a,data):
            writes.append((a,bytes(data)))
            for i,v in enumerate(data):memory[a+i]=v
        def read(a,n):return bytes(memory.get(a+i,0x73)for i in range(n))
        write(0x210F198,b'a/0/1/1\0');write(z.DIR,bytes(range(72)));writes.clear()
        vector=[z.DIR,0x210F198,z.ID,0,0x210F198,z.ID,z.H.H.MON,0]+list(z.H.H.N.COOKIES[4:])+[0,z.DIR,0x20D81AC,0x1F]
        keys=list(z.B.R)+[z.R.UC_ARM_REG_SP,z.R.UC_ARM_REG_LR,z.R.UC_ARM_REG_CPSR];regs=dict(zip(keys,vector))
        u=types.SimpleNamespace(reg_write=lambda k,v:regs.__setitem__(k,v),reg_read=lambda k:regs.get(k,0),mem_write=write)
        r=types.SimpleNamespace(u=u,regs=lambda:[regs[k]for k in keys],read_bytes=read,initialized=True,file=z.FILE,
            open=False,cursor=None,path=None,archive=None,clobber=clobber,models=[],
            data={'11':dict(path='a/0/1/1',raw=b'project synthetic provider',oracle={'file_id':140})})
        observer=z.ConvertObserver.__new__(z.ConvertObserver);observer.reader=r;observer.active=True
        observer.driver=types.SimpleNamespace(find_value=2);observer.base_service=lambda pc:None
        return observer,r,regs,writes,read

    def test_find_model_writes_caller_id8_not_directory_and_returns_arm(self):
        z=self.z
        for clobber in(False,True):
            observer,r,regs,writes,read=self.fixture(clobber);before=read(z.DIR,72)
            observer.service(z.FIND)
            self.assertEqual(writes,[(z.ID,z.struct.pack('<II',z.ARC,140))])
            self.assertEqual(read(z.DIR,72),before);self.assertIs(r.open,False);self.assertIsNone(r.archive)
            self.assertEqual(r.file,z.FILE);self.assertEqual(r.models[0]['result_r0'],2)
            self.assertEqual(r.models[0]['name'],'FSi_FindPath');self.assertEqual(r.models[0]['dir_before_hex'],before.hex())
            self.assertFalse(regs[z.R.UC_ARM_REG_CPSR]&32)
        observer,r,regs,writes,read=self.fixture();regs[z.B.R[2]]=z.DIR
        with self.assertRaises(ValueError):observer.service(z.FIND)
        self.assertEqual(writes,[])


if __name__=='__main__':unittest.main()
