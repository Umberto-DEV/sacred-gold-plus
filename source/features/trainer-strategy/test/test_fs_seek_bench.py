"""Portable property projection, flag-domain and actual-cursor safeguards."""
from pathlib import Path
import importlib.util,types,struct,unittest
from unittest.mock import patch


def tool():
    p=Path(__file__).parents[1]/'tools/attribuisci_fs_seek.py';s=importlib.util.spec_from_file_location('seek_portable',p)
    m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


class Portable(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.z=tool()

    def data(self):
        z=self.z;raw=b'Z'*11356;g=dict(file_id=140,top=0x1093800,bottom=0x109645C,bytes=11356,archive_sha256=z.sha(raw))
        return dict(fs_geometry=g,pp_reader={'11':dict(raw=raw,oracle=dict(btaf=16,btnf=3796,btnf_bytes=16,member_archive_offset=8780,member_bytes=16))})

    def test_source_drift_and_missing_edits_rejected(self):
        z=self.z
        with patch.object(z.A,'PARENT_SHA256','0'*64),self.assertRaisesRegex(ValueError,'source drift'):z.A.bind(z.H)
        with self.assertRaisesRegex(ValueError,'recipe occurrence'):
            z.A.rewrite(z.H,z.R,'Reader.step',[('missingSeekSource','',1)],{},'narc_reader')

    def test_incoming_nzcv_only_is_free_and_first_cmp_removes_its_effect(self):
        z=self.z;data=self.data();offset,lr,saved,_=z.seek_specs(data)[0]
        base=[z.FILE,offset,0,0]+saved+list(z.PP.N.COOKIES[4:])+[0,z.TOP-136,lr,0x1F]
        canonical=z.expected_seek(dict(pp_clobber=False),data,0,base)
        for flags in range(16):
            entry=list(base);entry[15]|=flags<<28;p=z.expected_seek(dict(pp_clobber=False),data,0,entry)
            self.assertEqual(p['flow'][0]['regs'],entry)
            self.assertEqual(p['flow'][1:],canonical['flow'][1:]);self.assertEqual(p['returned'],canonical['returned'])
        bad=list(base);bad[15]|=1<<27
        with self.assertRaisesRegex(ValueError,'incoming NZCV'):z.expected_seek(dict(pp_clobber=False),data,0,bad)
        cur=list(base);cur[2]=1;p=z.expected_seek(dict(pp_clobber=False),data,0,cur,1)
        self.assertEqual(p['returned'],canonical['returned']);self.assertEqual(len(p['flow']),len(canonical['flow'])+2)

    def test_geometry_reads_fat_row_independently_and_rejects_short_table(self):
        z=self.z;top=0x1000;raw=bytearray(top+11356);raw[top:]=b'Z'*11356
        struct.pack_into('<II',raw,0x48,0x200,141*8);struct.pack_into('<II',raw,0x200+140*8,top,len(raw))
        receipt=dict(file_id=140,archive_sha256=z.sha(bytes(raw[top:])))
        with patch.object(z.P.RAW,'raw_archive',return_value=([b'']*471,receipt)):
            g=z.geometry(raw);self.assertEqual((g['file_id'],g['top'],g['bottom']),(140,top,len(raw)))
            struct.pack_into('<I',raw,0x4C,140*8)
            with self.assertRaisesRegex(ValueError,'row bounds'):z.geometry(raw)

    def fixture(self):
        z=self.z;data=self.data();g=data['fs_geometry'];memory={z.DIR+i:0x73 for i in range(240)};writes=[]
        def write(a,b):
            writes.append((a,bytes(b)))
            for i,v in enumerate(b):memory[a+i]=v
        def read(a,n):return bytes(memory.get(a+i,0)for i in range(n))
        write(z.FILE+32,z.prop_bytes(g,g['top']+12));writes.clear()
        vector=[z.FILE,z.TOP-116,2,0]+[1,2,3,4]+list(z.PP.N.COOKIES[4:])+[0,z.TOP-136,0x2007367,0x1F]
        keys=list(z.B.R)+[z.R.UC_ARM_REG_SP,z.R.UC_ARM_REG_LR,z.R.UC_ARM_REG_CPSR]
        u=types.SimpleNamespace(mem_write=write,reg_write=lambda key,value:vector.__setitem__(keys.index(key),value),reg_read=lambda key:vector[keys.index(key)])
        r=types.SimpleNamespace(u=u,regs=lambda:list(vector),read_bytes=read,file=z.FILE,open=True,cursor=12,archive=data['pp_reader']['11']['raw'],models=[],observe=True)
        o=z.SeekObserver.__new__(z.SeekObserver);o.reader=r;o.active=False;o.current=None;o.result=[]
        o.projection=dict(geometry=g,events=[]);o.driver=types.SimpleNamespace(fast_observer=types.SimpleNamespace(active=False),close_observer=types.SimpleNamespace(active=False),seek_variant='current')
        return o,r,vector,memory,writes,read,write

    def test_read_position_projection_has_precise_success_and_buffer_guards(self):
        z=self.z
        for variant in('valid','cursor','overlap','base_file_write','short_read'):
            o,r,vector,memory,writes,read,write=self.fixture();before=read(z.FILE,72)
            def base(pc):
                n=vector[2];write(vector[1],b'Q'*n);r.cursor+=n;vector[0]=n;vector[15]=0x3F
                if variant=='base_file_write':write(z.FILE,b'X')
                r.models.append(dict(name='FS_ReadFile',requested_bytes=n,delivered_bytes=n-1 if variant=='short_read'else n,result_r0=n))
            o.base_service=base
            if variant=='cursor':r.cursor=13
            if variant=='overlap':vector[1]=z.FILE+32
            if variant!='valid':
                with self.subTest(variant=variant),self.assertRaises(ValueError):o.service(z.READ)
                continue
            o.service(z.READ)
            self.assertEqual(read(z.POSITION,4),struct.pack('<I',o.projection['geometry']['top']+14))
            self.assertEqual(read(z.FILE,44)+read(z.FILE+48,24),before[:44]+before[48:])
            self.assertEqual(writes,[(z.TOP-116,b'QQ'),(z.POSITION,struct.pack('<I',o.projection['geometry']['top']+14))])
            self.assertEqual(len(o.projection['events']),1)

    def test_only_send6_projects_properties_not_send8(self):
        z=self.z;o,r,vector,memory,writes,read,write=self.fixture();o.driver.fast_observer.active=True
        g=o.projection['geometry'];r.open=False;r.cursor=None;before=read(z.DIR,240)
        def base(pc):r.open=True;r.cursor=0;r.models.append({})
        o.base_service=base;o.service(z.SEND)
        self.assertEqual(writes,[(z.FILE+32,z.prop_bytes(g))]);after=read(z.DIR,240);i=z.FILE+32-z.DIR
        self.assertEqual(after[:i]+after[i+16:],before[:i]+before[i+16:])
        writes.clear();o.driver.fast_observer.active=False;o.driver.close_observer.active=True;o.service(z.SEND)
        self.assertEqual(writes,[]);self.assertEqual(len(o.projection['events']),1)

    def test_projection_register_width_is_unsigned32_including_cpsr(self):
        z=self.z;frame=bytearray(240);address=z.POSITION;blob=struct.pack('<I',123)
        regs=[2,3,4,5]+list(range(6,14))+[14,z.TOP-136,0x2007367,0x3F]
        model=dict(result_r0=2,return_volatile=[3,4,5,14],return_saved=list(range(6,14)),return_sp=z.TOP-136,lr='0x2007367')
        after=bytearray(frame);after[address-z.DIR:address-z.DIR+4]=blob
        event=dict(kind='read-position-result',address=address,bytes=4,before='00000000',after=blob.hex(),regs=regs,
            frame_before=frame.hex(),frame_after=after.hex(),model_index=2)
        model['property_projection']=event
        self.assertEqual(z.checked_projection(event,'read-position-result',address,blob,frame,2,model),after)
        for value in(0x10000003F,-1,True):
            event['regs'][15]=value
            with self.subTest(value=value),self.assertRaises(ValueError):
                z.checked_projection(event,'read-position-result',address,blob,frame,2,model)

    def test_read_to_close_bridge_preserves_nzcv_and_unmodified_registers(self):
        z=self.z
        for flags in(0x2000003F,0xA000003F,0xF000003F):
            regs=list(range(16));regs[15]=flags;original=list(regs);mapped=z.read_to_close_entry(regs)
            self.assertEqual(regs,original);self.assertEqual(mapped[0],z.FILE);self.assertEqual(mapped[14],0x2007409)
            self.assertEqual(mapped[15],flags&~32);self.assertEqual(mapped[1:14],regs[1:14])
        bad=list(regs);bad[15]=0x10000003F
        with self.assertRaises(ValueError):z.read_to_close_entry(bad)

    def test_cursor_notification_uses_actual_guest_word_not_requested_offset(self):
        z=self.z;o,r,vector,memory,writes,read,write=self.fixture();g=o.projection['geometry']
        write(z.POSITION,struct.pack('<I',g['top']+3800));o.active=True;o.current=dict(entry=list(vector));events=[]
        o.parent_step=lambda *a:events.append('parent');o.root_step=lambda *a:events.append('root')
        o.step(r.u,vector[14]&~1,2,None)
        self.assertEqual(r.cursor,3800);self.assertEqual(o.current['cursor_after'],3800)
        self.assertEqual(events,['parent']);self.assertIs(o.active,False)


if __name__=='__main__':unittest.main()
