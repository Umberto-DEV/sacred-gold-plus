"""Strict onboarding readback checks without ROMs or runtime execution."""
import importlib.util
from pathlib import Path
import struct
import unittest
from localization import native_text
from sgp131 import onboarding_version as V, ui_verify

spec = importlib.util.spec_from_file_location('readback_onboarding', Path(__file__).with_name('readback_133.py'))
R = importlib.util.module_from_spec(spec); spec.loader.exec_module(R)


def encode(s):
    return [ord(c) for c in s] + [0xFFFF]


def bank(title):
    values = {k: 'string'+str(i) for i,k in enumerate(native_text.ONBOARDING_IDS)}
    values['p_titolo'] = values['c_titolo'] = title
    return native_text.pack_onboarding(values, encode, lambda words: len(words))


class BankReadback(unittest.TestCase):
    def test_mutations_refused_and_sixteen_byte_canary_preserved(self):
        old = bank(V.OLD_CORE_TITLE)
        new = V.transform(old, encode, lambda words: len(words))
        sentinel = bytes(range(16))
        self.assertEqual(R.verify_onboarding(old,new,sentinel,sentinel,'EN',encode)['profile'], 'onboarding-133-v1')
        ui_verify._verify_onboarding_bank(old,new,V._encoded(V.OLD_CORE_TITLE,encode),V._encoded(V.TITLE,encode))
        mutants = [old, new[:-1], b'\x01\x00'+new[2:], new[:-1]+b'\x01']
        changed = bytearray(new); changed[struct.unpack_from('<H',changed,2)[0]] ^= 1
        mutants.append(bytes(changed))
        for changed in mutants:
            with self.subTest(changed=changed[:4]), self.assertRaises(ValueError):
                R.verify_onboarding(old,changed,sentinel,sentinel,'EN',encode)
        with self.assertRaises(ValueError):
            R.verify_onboarding(old,new,sentinel,bytes(16),'EN',encode)
        with self.assertRaises(ValueError):
            ui_verify._verify_onboarding_bank(old,bytes(changed),V._encoded(V.OLD_CORE_TITLE,encode),V._encoded(V.TITLE,encode))
