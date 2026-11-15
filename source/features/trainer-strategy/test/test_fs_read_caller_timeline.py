"""Pure temporal Read checks: synthetic inputs, no ROM or guest execution."""
from pathlib import Path
import copy,importlib.util,struct,unittest
s=importlib.util.spec_from_file_location('read_caller_timeline',Path(__file__).parents[1]/'tools/attribuisci_fs_read_chiamante.py')
Z=importlib.util.module_from_spec(s);s.loader.exec_module(Z)


def fixture():
    memory=bytearray(b'\x39'*240)
    struct.pack_into('<4I',memory,Z.FILE-Z.DIR+32,140,0x1000,0x2000,0x100C)
    struct.pack_into('<3I',memory,Z.FILE-Z.DIR+12,16,0,0)
    entry=[Z.FILE,Z.TOP-116,2,0,0x210F198,310,0x2200080,0,
           0x88888801,0x99999902,0xAAAAAA03,0xBBBBBB04,0,Z.TOP-136,0x2007367,0x6000001F]
    f=dict(ordinal=0,entry=entry,frame=memory.hex(),destination_before='3939',payload='1000',position=12)
    want=Z.W.B.predict(f);page=bytearray(b'\x39'*4096)
    page[Z.DIR-Z.PAGE:Z.DIR-Z.PAGE+240]=memory
    after=bytearray(page);after[Z.DIR-Z.PAGE:Z.DIR-Z.PAGE+240]=bytes.fromhex(want['frame_after'])
    r=dict(fixture=copy.deepcopy(f),entry=entry,frame_before=f['frame'],frame_after=want['frame_after'],
           returned=want['returned'],destination_before='3939',destination_after='1000',
           page_before=page.hex(),page_after=after.hex(),outside_unchanged=True,
           outside_before_sha256='a'*64,outside_after_sha256='a'*64,policy=dict(error=0,send=1,clobber=False),
           native_peak=48,flow=[dict(pc=pc,regs=regs)for pc,regs in want['flow'].items()],
           stores=want['stores'],services=want['services'],completion=want['completion'],reads=[])
    # The read transcript is independently enumerated from the source fields.
    sp=entry[13]
    def read(pc,addresses,values):
        r['reads'].extend(dict(pc=hex(pc),address=a,bytes=4,hex=struct.pack('<I',v).hex())for a,v in zip(addresses,values))
    for pc,address,value in((Z.READ,Z.READ+12,Z.W.B.CORE),(0x20D810C,Z.FILE+44,0x100C),
         (0x20D8110,Z.FILE+40,0x2000),(0x20D8140,Z.FILE+12,16),(0x20D830C,Z.FILE+12,16),
         (0x20D83A8,Z.FILE+20,0)):
        read(pc,[address],[value])
    wait=want['flow'][hex(Z.W.B.WAIT)]
    read(0x20D83B8,[sp-48+4*i for i in range(6)],[*wait[4:9],wait[14]])
    read(0x20D816C,[Z.FILE+44],[0x100E])
    read(0x20D817C,[sp-24+4*i for i in range(6)],[0,*entry[4:8],entry[14]])
    return f,r


class TemporalRead(unittest.TestCase):
    def test_complete_context_and_page_are_accepted(self):
        f,r=fixture();Z.require_read_call(r,f,True,0,1,False)
    def test_boolean_is_not_a_register_value(self):
        for field in('entry','returned','flow'):
            with self.subTest(field=field):
                f,r=fixture()
                vector=r['flow'][0]['regs']if field=='flow'else r[field]
                vector[3]=False
                with self.assertRaises(ValueError):Z.require_read_call(r,f,True,0,1,False)

    def test_unreported_native_flow_change_is_rejected(self):
        f,r=fixture();r['flow'][9]['regs'][12]^=4
        with self.assertRaises(ValueError):Z.require_read_call(r,f,True,0,1,False)
    def test_rogue_page_write_outside_frame_and_payload_is_rejected(self):
        f,r=fixture();page=bytearray.fromhex(r['page_after']);page[100]^=1;r['page_after']=page.hex()
        with self.assertRaises(ValueError):Z.require_read_call(r,f,True,0,1,False)
    def test_outside_actual_byte_comparison_is_required(self):
        f,r=fixture();r['outside_unchanged']=False
        with self.assertRaises(ValueError):Z.require_read_call(r,f,True,0,1,False)


if __name__=='__main__':unittest.main()
