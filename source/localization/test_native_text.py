"""Native command copy cannot change its String layout or an unknown object."""
import unittest
from . import native_text

class NativeTextTests(unittest.TestCase):
    def test_pc_command_preserves_header_and_refuses_other_preimages(self):
        chars={'R':0x13C,':':0x1C4,' ':0x1DE,'P':0x13A,'C':0x12D}
        encode=lambda text:[chars[c] for c in text]+[65535]
        before=native_text.PC_LABEL_PREIMAGE
        after=native_text.apply(before,lambda a,n:0,encode)
        self.assertEqual(after[:8],before[:8])
        self.assertEqual(len(after),24)
        self.assertNotEqual(after,before)
        with self.assertRaises(ValueError):native_text.apply(bytes(24),lambda a,n:0,encode)

class OnboardingTests(unittest.TestCase):
    def test_table_ids_deduplicate_and_refuse_overflow_or_wide_copy(self):
        import struct
        values={key:'same' for key in native_text.ONBOARDING_IDS}
        encode=lambda text:[ord(c) for c in text]+[65535]
        blob=native_text.pack_onboarding(values,encode,lambda w:len(w)-1)
        self.assertEqual(len(blob),1008)
        self.assertEqual(set(struct.unpack_from('<29H',blob)),{58})
        with self.assertRaisesRegex(ValueError,'geometry'):
            native_text.pack_onboarding(values,encode,lambda w:205)
        values={key:key+':'+('x'*24) for key in native_text.ONBOARDING_IDS}
        with self.assertRaisesRegex(ValueError,'budget'):
            native_text.pack_onboarding(values,encode,lambda w:1)
