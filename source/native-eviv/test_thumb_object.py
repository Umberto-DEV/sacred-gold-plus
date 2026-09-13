from pathlib import Path
import struct
import subprocess
import tempfile
import unittest

from thumb_object import load_text


class ThumbObjectTests(unittest.TestCase):
    def compile(self, source):
        with tempfile.TemporaryDirectory(prefix='sgpc-thumb-test-') as tmp:
            src, obj = Path(tmp) / 'fixture.s', Path(tmp) / 'fixture.o'
            src.write_text('.syntax unified\n.thumb\n.text\n' + source)
            subprocess.run(['clang', '--target=armv5te-none-eabi', '-mcpu=arm946e-s',
                            '-c', str(src), '-o', str(obj)], check=True, capture_output=True)
            return obj.read_bytes()

    def internal(self):
        return self.compile('''.global show_eviv
.type show_eviv,%function
.thumb_func
show_eviv:
movs r0,#7
bx lr
.global eviv_hook
.type eviv_hook,%function
.thumb_func
eviv_hook:
bl show_eviv
bx lr
''')

    def test_internal_backward_bl_resolves_without_external_linker(self):
        payload, names = load_text(self.internal(), 0x01FF8620)
        # BL at offset 4 uses architectural PC 8; target 0 means displacement -8.
        self.assertEqual(payload[:4], bytes.fromhex('07207047'))
        self.assertEqual(payload[4:8], bytes.fromhex('fff7fcff'))
        self.assertEqual(names['eviv_hook'], 0x01FF8625)

    def test_external_bl_and_separate_allocated_data_are_rejected(self):
        for extra in ['bl outside\nbx lr\n', 'bx lr\n.data\n.word 42\n']:
            obj = self.compile('.global eviv_hook\n.type eviv_hook,%function\n'
                               '.thumb_func\neviv_hook:\n' + extra)
            with self.assertRaises(ValueError):
                load_text(obj, 0x01FF8620)

    def test_unsupported_text_relocation_table_is_not_silently_ignored(self):
        obj = bytearray(self.internal())
        shoff = struct.unpack_from('<I', obj, 32)[0]
        count = struct.unpack_from('<H', obj, 48)[0]
        changed = 0
        for i in range(count):
            at = shoff + i * 40
            if struct.unpack_from('<I', obj, at + 4)[0] == 9:
                struct.pack_into('<I', obj, at + 4, 4)  # RELA not supported here.
                changed += 1
        self.assertEqual(changed, 1)
        with self.assertRaises(ValueError):
            load_text(bytes(obj), 0x01FF8620)

    def test_truncated_header_and_bad_section_index_fail_explicitly(self):
        obj = bytearray(self.internal())
        struct.pack_into('<H', obj, 50, 0xFFFF)
        for bad in [b'\x7fELF\x01\x01\x01', bytes(obj)]:
            with self.assertRaises(ValueError):
                load_text(bad, 0x01FF8620)


if __name__ == '__main__':
    unittest.main()
