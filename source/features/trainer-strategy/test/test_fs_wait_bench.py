"""Portable source/state/ABI checks for Wait; no guest CPU execution."""
from pathlib import Path
import copy,importlib.util,struct,unittest
s=importlib.util.spec_from_file_location('wait_portable',Path(__file__).with_name('fs_wait_bench.py'))
B=importlib.util.module_from_spec(s);s.loader.exec_module(B)


def fixture():
    memory=bytearray([0x39])*240
    struct.pack_into('<4I',memory,B.FILE-B.FRAME+32,140,0x1000,0x1100,0x1010)
    struct.pack_into('<I',memory,B.FILE-B.FRAME+12,16)
    return dict(ordinal=6,entry=[B.FILE,B.DEST,16,0x123,0x2000001,310,0x2200000,0,
        0x88888801,0x99999902,0xAAAAAA03,0xBBBBBB04,0,B.TOP-136,0x2007403,0x6000001F],
        frame=memory.hex(),destination_before='A5'*16,payload='12'*16,provenance={'synthetic':True})


class Portable(unittest.TestCase):
    def test_source_recipes_and_finite_nonbusy_abi(self):
        f=fixture();r=B.predict(f)
        self.assertEqual(len(B.RECIPES),3);self.assertTrue(all(x['parent_sha256']==B.PARENT_SHA for x in B.RECIPES))
        self.assertEqual(len(r['flow']),65);self.assertEqual(len(r['stores']),16);self.assertEqual(len(r['services']),1)
        self.assertEqual(r['returned'][0],16);self.assertEqual(r['returned'][1:4],[0x6000009F,0x6000001F,0])
        self.assertEqual(r['returned'][4:12],f['entry'][4:12]);self.assertEqual(r['returned'][13:],[B.TOP-136,0x20D8394,0x2000003F])
        self.assertEqual(r['native_peak'],48)

    def test_irq1_restores_control_with_same_frame_and_payload(self):
        f=fixture();normal=B.predict(f);f['entry'][15]|=0x80;irq=B.predict(f)
        self.assertEqual(normal['frame_after'],irq['frame_after']);self.assertEqual(normal['destination_after'],irq['destination_after'])
        self.assertEqual(irq['returned'][2],0x6000009F);self.assertEqual(irq['returned'][15],0x200000BF)
        self.assertEqual(normal['flow']['0x20d3a44'][15]&0x80,0x80)
        self.assertEqual(normal['flow']['0x20d3a5c'][15]&0x80,0)
        self.assertEqual(irq['flow']['0x20d3a5c'][15]&0x80,0x80)

    def test_error1_preserves_payload_but_changes_exact_completion_word_and_return(self):
        f=fixture();a=B.predict(f);b=B.predict(f,error_value=1)
        self.assertEqual(b['returned'][0],0xFFFFFFFF);self.assertEqual(b['returned'][15],0x6000003F)
        self.assertEqual(a['destination_after'],b['destination_after'])
        x=bytearray.fromhex(a['frame_after']);y=bytearray.fromhex(b['frame_after']);offset=B.FILE+20-B.FRAME
        self.assertEqual(y[offset:offset+4],b'\x01\0\0\0');y[offset:offset+4]=x[offset:offset+4]
        self.assertEqual(x,y)

    def test_completion_model_changes_only_stat_command_error_and_no_register(self):
        f=fixture();memory=bytearray.fromhex(f['frame']);struct.pack_into('<3I',memory,B.FILE+12-B.FRAME,0x5F,14,0x1234)
        before=bytes(memory);regs=list(f['entry']);events=[];B.complete_model(regs,memory,events,0)
        expected=bytearray(before);struct.pack_into('<3I',expected,B.FILE+12-B.FRAME,16,0,0)
        self.assertEqual(memory,expected);self.assertEqual(regs,f['entry']);self.assertEqual(events[0]['model_words'],3)
        self.assertEqual(events[0]['regs'],regs);self.assertEqual(len(events),1)

    def test_finite_types_cpsr_and_nested_buffer_ownership_rejected(self):
        for value in(True,-1,2,0x100000000):
            with self.subTest(error=value),self.assertRaises(ValueError):B.predict(fixture(),error_value=value)
        for mode in('IRQ2','FIQ','Q','wide','saved48'):
            f=fixture()
            if mode=='IRQ2':f['entry'][15]^=1
            elif mode=='FIQ':f['entry'][15]|=0x40
            elif mode=='Q':f['entry'][15]|=1<<27
            elif mode=='wide':f['entry'][15]|=1<<32
            else:f['entry'][1]=f['entry'][13]-40
            with self.subTest(mode=mode),self.assertRaises(ValueError):B.predict(f)

    def test_send_false_ignored_and_clobber_does_not_fake_saved_or_irq_results(self):
        f=fixture();a=B.predict(f);b=B.predict(f,send_value=0);c=B.predict(f,clobber=True)
        self.assertEqual(a['returned'],b['returned']);self.assertEqual(a['frame_after'],b['frame_after'])
        self.assertEqual(a['returned'][1:12],c['returned'][1:12]);self.assertEqual(c['returned'][12],0xA500000C)
        self.assertEqual(c['returned'][14],0x20D8394);self.assertEqual(c['returned'][15],0x2000003F)


if __name__=='__main__':unittest.main()
