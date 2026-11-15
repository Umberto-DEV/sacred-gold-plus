"""Portable behavior tests for the finite Thumb caller bridge oracle."""
from pathlib import Path
import importlib.util,struct,unittest
s=importlib.util.spec_from_file_location('read_caller_bench',Path(__file__).with_name('fs_read_caller_bench.py'))
B=importlib.util.module_from_spec(s);s.loader.exec_module(B)


class Bridge(unittest.TestCase):
    def accepted(self,code,pc,entry,frame):
        try:return B.advance_bridge(code,pc,entry,frame)
        except ValueError as error:self.fail('Valid finite source bridge rejected: '+str(error))

    def test_ignored_read_failure_is_overwritten_before_next_seek(self):
        # Synthetic program: LDR r4,[sp,#20]; ADD r0,sp,#24;
        # ADDS r1,r4,#4; MOVS r2,#0; BLX Seek. A missing ADDS flag
        # update or a retained R0=-1 would change the next native ABI.
        code={0x2007366:struct.pack('<H',0x9C05),0x2007368:struct.pack('<H',0xA806),
              0x200736A:struct.pack('<H',0x1D21),0x200736C:struct.pack('<H',0x2200),
              0x200736E:struct.pack('<HH',0xF0D1,0xE836)}
        frame=bytearray(240);struct.pack_into('<I',frame,124,16)
        want=[0x23BEE50,20,0,0,16,310,0x2200080,0,0x88888801,0x99999902,
              0xAAAAAA03,0xBBBBBB04,0x20D8104,0x23BEE38,0x2007373,0x4000001F]
        for value,cpsr in((2,0x2000003F),(0xFFFFFFFF,0x6000003F)):
            entry=[value,0x6000009F,0x6000001F,0,0x210F198,310,0x2200080,0,
                   0x88888801,0x99999902,0xAAAAAA03,0xBBBBBB04,0x20D8104,
                   0x23BEE38,0x2007367,cpsr]
            result=B.advance_bridge(code,0x2007366,entry,bytes(frame))
            self.assertIsInstance(result,dict)
            self.assertEqual(result['target'],0x20D83DC)
            self.assertEqual(result['entry'],want)
            self.assertEqual(result['frame'],frame.hex())

    def test_member_bounds_branch_skips_assert_and_derives_btnf_seek(self):
        # Missing unsigned halfword load, wrong signed GT, or wrong register
        # addition would select the assertion path or the wrong metadata block.
        code={pc:struct.pack('<H',op)for pc,op in(
            (0x2007386,0xA802),(0x2007388,0x8800),(0x200738A,0x42A8),
            (0x200738C,0xDC01),(0x2007392,0x9805),(0x2007394,0x2200),
            (0x2007396,0x1826),(0x2007398,0xA806),(0x200739A,0x1D31))}
        code[0x200739C]=struct.pack('<HH',0xF0D1,0xE81E)
        frame=bytearray(240);struct.pack_into('<H',frame,112,471);struct.pack_into('<I',frame,124,3780)
        entry=[2,0x6000009F,0x6000001F,0,16,310,0x2200080,0,0x88888801,
               0x99999902,0xAAAAAA03,0xBBBBBB04,0x20D8104,0x23BEE38,0x2007387,0x2000003F]
        result=self.accepted(code,0x2007386,entry,frame)
        self.assertEqual(result['entry'],[0x23BEE50,3800,0,0,16,310,3796,0,
            0x88888801,0x99999902,0xAAAAAA03,0xBBBBBB04,0x20D8104,0x23BEE38,0x20073A1,0x1F])
        self.assertNotIn('0x200738e',[e['pc']for e in result['flow']])

    def test_eight_byte_member_stride_sets_exact_btaf_row_and_saved_context(self):
        # A four-byte stride or a flag-setting error changes the actual Seek ABI.
        code={pc:struct.pack('<H',op)for pc,op in(
            (0x20073AA,0x340C),(0x20073AC,0x00E9),(0x20073AE,0xA806),
            (0x20073B0,0x1861),(0x20073B2,0x2200),(0x20073B4,0x9F05))}
        code[0x20073B6]=struct.pack('<HH',0xF0D1,0xE812)
        frame=bytearray(240);struct.pack_into('<I',frame,124,16)
        entry=[4,0x6000009F,0x6000001F,0,16,310,3796,0,0x88888801,
               0x99999902,0xAAAAAA03,0xBBBBBB04,0x20D8104,0x23BEE38,0x20073AB,0x2000003F]
        result=self.accepted(code,0x20073AA,entry,frame)
        self.assertEqual(result['entry'],[0x23BEE50,2508,0,0,28,310,3796,16,
            0x88888801,0x99999902,0xAAAAAA03,0xBBBBBB04,0x20D8104,0x23BEE38,0x20073BB,0x4000001F])

    def test_payload_length_is_derived_stored_and_consumed_by_final_read(self):
        # Omitting SUBS/STR or taking the wrong NE branch would change length,
        # source flags, or read an unavailable assertion call.
        code={pc:struct.pack('<H',op)for pc,op in(
            (0x20073E2,0x981E),(0x20073E4,0x2800),(0x20073E6,0xD102),
            (0x20073E8,0x9903),(0x20073EA,0x9804),(0x20073EC,0x1A08),
            (0x20073EE,0x9005),(0x20073F0,0x2800),(0x20073F2,0xD101),
            (0x20073F8,0x9900),(0x20073FA,0x9A05),(0x20073FC,0xA806))}
        # Hand-encoded BLX across the 0x7400 PC alignment boundary.
        code[0x20073FE]=struct.pack('<HH',0xF0D0,0xEFE6)
        frame=bytearray(240);struct.pack_into('<I',frame,104,0x23BEEC0)
        struct.pack_into('<II',frame,116,4976,4960);struct.pack_into('<I',frame,124,0x12345678)
        entry=[1,0x1095A4C,0x109645C,0,28,310,3796,16,0x88888801,
               0x99999902,0xAAAAAA03,0xBBBBBB04,0x20D8104,0x23BEE38,0x20073E3,0x8000003F]
        result=self.accepted(code,0x20073E2,entry,frame)
        self.assertEqual(result['target'],0x20D83CC)
        self.assertEqual(result['entry'],[0x23BEE50,0x23BEEC0,16,0,28,310,3796,16,
            0x88888801,0x99999902,0xAAAAAA03,0xBBBBBB04,0x20D8104,0x23BEE38,0x2007403,0x2000001F])
        self.assertEqual(result['stores'],[dict(pc='0x20073ee',address=0x23BEE4C,bytes=4,before='78563412',value=16)])
        self.assertEqual(struct.unpack_from('<I',bytes.fromhex(result['frame']),124)[0],16)


class PageWitness(unittest.TestCase):
    def test_page_witness_preserves_bytes_outside_frame_and_output(self):
        # A whole-page mask would accept this unrelated byte; exact composition
        # must reject it while accepting the independently constructed image.
        before=bytes([0x39])*4096;frame=bytes([0xA5])*240;payload=bytes([0x12])*16
        after=bytearray(before);after[0xDD0:0xEC0]=frame;after[0xEC0:0xED0]=payload
        self.assertTrue(B.require_page(before,bytes(after),frame,0x23BEEC0,payload))
        after[0x100]^=1
        with self.assertRaises(ValueError):B.require_page(before,bytes(after),frame,0x23BEEC0,payload)

    def test_output_copy_cannot_mask_a_wrong_native_frame_prediction(self):
        before=bytes([0x39])*4096;frame=bytes([0xA5])*240;payload=b'\x12\x34'
        after=bytearray(before);after[0xDD0:0xEC0]=frame;after[0xDD8:0xDDA]=payload
        # A contradictory frame must fail instead of being silently overwritten
        # by the payload patch at the same owned bytes.
        with self.assertRaises(ValueError):B.require_page(before,bytes(after),frame,0x23BEDD8,payload)


if __name__=='__main__':unittest.main()
