"""Portable rejection tests for native Init effects, ABI and source binding."""
from pathlib import Path
import copy
import importlib.util
import struct
import unittest
from unittest.mock import patch


def tool():
    path = Path(__file__).parents[1] / 'tools/attribuisci_fs_init.py'
    spec = importlib.util.spec_from_file_location('fs_init_portable', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Portable(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.z = tool()

    def fixture(self, observe=True):
        z = self.z
        initial_frame = bytearray(range(136)); frame = bytearray(initial_frame)
        struct.pack_into('<III', frame, 124, 0x2007509, 5, z.STOP | 1)
        struct.pack_into('<I', frame, 120, 0)
        struct.pack_into('<6I', frame, 96, 0, 44, 0, z.H.MON, 0, 0x200751B)
        for offset, width, value in ((0, 4, z.DEST), (20, 4, 0), (16, 4, 0), (12, 4, 0), (8, 2, 0), (4, 4, 0)):
            frame[offset:offset + width] = value.to_bytes(width, 'little')
        before = bytes(frame[24:96]); after = bytearray(before)
        entry = [z.FILE, 0, 310, 0, 0x210F198, 310, z.H.MON, 0] + list(z.H.N.COOKIES[4:]) + [0, z.TOP - 136, 0x200734B, 0x1F]
        regs = list(entry); flow = []; stores = []
        # Expected ABI and field addresses are stated independently of the recipe table.
        fields = {0x20D7F9C: 0, 0x20D7FA0: 4, 0x20D7FA4: 28, 0x20D7FA8: 24,
                  0x20D7FAC: 8, 0x20D7FB4: 16, 0x20D7FB8: 12}
        for pc in range(0x20D7F98, 0x20D7FC0, 4):
            flow.append(dict(pc=hex(pc), regs=list(regs)))
            if pc == 0x20D7F98: regs[2] = 0
            if pc == 0x20D7FB0: regs[1] = 14
            if pc in fields:
                offset = fields[pc]; value = 14 if offset == 16 else 0
                stores.append(dict(pc=hex(pc), address=z.FILE + offset, bytes=4,
                    before=bytes(after[offset:offset + 4]).hex(), value=value, regs=list(regs)))
                struct.pack_into('<I', after, offset, value)
        returned = list(regs); returned[15] = 0x3F
        frame_after = bytearray(frame); frame_after[24:96] = after
        models = [dict(name='FS_OpenFile', args=[z.FILE, 0x210F198, 0, 0])] + [dict(name='remaining') for _ in range(13)]
        return dict(observe=observe, fs_init=dict(entry=entry, returned=returned,
            before=before.hex(), after=after.hex(), frame_before=frame.hex(), frame_after=frame_after.hex(),
            flow=flow, stores=stores if observe else [], shadows=[],
            ledger_before=dict(initialized=False, file=None, open=False),
            ledger_after=dict(initialized=True, file=z.FILE, open=False)),
            pp_reader=dict(stack_frame_before=initial_frame.hex(), models=models))

    def test_assigned28_preserved44_and_off_same_guest_effects(self):
        z = self.z
        for observe in (False, True):
            r = self.fixture(observe); self.assertTrue(z.require_init(r))
        self.assertEqual(sum(4 for _ in z.STORES), 28)
        self.assertEqual((z.FILE, z.FILE + 72), (z.TOP - 112, z.TOP - 40))

    def test_false_successes_rejected_with_unchanged_payload(self):
        z = self.z
        for key in ('missing_store', 'width', 'address', 'value', 'before', 'preserved', 'metadata',
                    'saved', 'r2', 'flags', 'lr', 'order', 'register', 'ledger', 'fake_model', 'open_r2', 'preimage', 'resealed_frame'):
            r = self.fixture(); f = r['fs_init']
            if key == 'missing_store': f['stores'].pop(5)
            elif key == 'width': f['stores'][0]['bytes'] = 2
            elif key == 'address': f['stores'][0]['address'] += 4
            elif key == 'value': f['stores'][5]['value'] = 0
            elif key == 'before': f['stores'][0]['before'] = '00000000'
            elif key in ('preserved', 'metadata', 'saved'):
                offset = 20 if key == 'preserved' else 0 if key == 'metadata' else 96
                a = bytearray.fromhex(f['frame_after']); a[24 + offset if key == 'preserved' else offset] ^= 1
                f['frame_after'] = a.hex()
                if key == 'preserved': f['after'] = a[24:96].hex()
            elif key in ('r2', 'flags', 'lr'): f['returned'][{'r2': 2, 'flags': 15, 'lr': 14}[key]] ^= 1
            elif key == 'order': f['flow'][0], f['flow'][1] = f['flow'][1], f['flow'][0]
            elif key == 'register': f['flow'][3]['regs'][12] ^= 1
            elif key == 'resealed_frame':
                for field in ('frame_before', 'frame_after'):
                    a = bytearray.fromhex(f[field]); a[10] ^= 1; f[field] = a.hex()
            elif key == 'ledger': f['ledger_before']['initialized'] = True
            elif key == 'fake_model': r['pp_reader']['models'][3]['name'] = 'FS_InitFile'
            elif key == 'open_r2': r['pp_reader']['models'][0]['args'][2] = 310
            else: r['pp_reader']['stack_frame_before'] = '00' * 136
            with self.subTest(key=key), self.assertRaises(ValueError): z.require_init(r)

    def test_parent_pin_and_finite_source_edit_drift(self):
        z = self.z
        with patch.object(z.A, 'PARENT_SHA256', '0' * 64), self.assertRaisesRegex(ValueError, 'source drift'):
            z.A.bind(z.H)
        with self.assertRaisesRegex(ValueError, 'recipe occurrence'):
            z.A.rewrite(z.H, z.R, 'require_case', [('missing_fs_source', '', 1)], {}, 'narc_reader')

    def test_no_new_cpu_or_guest_write_in_attachment_or_return(self):
        z = self.z
        self.assertFalse({'Uc', 'mem_write', 'reg_write', 'emu_start'} & set(z.InitObserver.__init__.__code__.co_names))
        self.assertFalse({'Uc', 'mem_write', 'emu_start'} & set(z.InitObserver.step.__code__.co_names))
        self.assertNotIn(z.ENTRY, z.H.B.STUBS)
        self.assertEqual(z.R.SDK[z.ENTRY], 'FS_InitFile')


if __name__ == '__main__': unittest.main()
