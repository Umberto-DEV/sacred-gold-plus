"""Allocation-boundary regressions for every ndspy BLZ entry point."""
import struct
from types import SimpleNamespace
import unittest
from unittest import mock

from . import fishing, lullaby, ui, ui_verify
from sgp12 import blz
from sgp12.rom import Rifiuto


MALICIOUS = bytes.fromhex("08000008ffffffff")


def overlay_rom(base, size):
    data = bytearray(0x800)
    fat, y9, start = 0x200, 0x400, 0x600
    struct.pack_into("<II", data, 0x48, fat, 24)
    struct.pack_into("<II", data, 0x50, y9, 96)
    struct.pack_into("<8I", data, y9 + 2 * 32,
                     2, base, size, 0, 0, 0, 2, 0x01000008)
    struct.pack_into("<II", data, fat + 2 * 8, start, start + len(MALICIOUS))
    data[start:start + len(MALICIOUS)] = MALICIOUS
    return bytes(data)


class BlzSecurity(unittest.TestCase):
    def test_ndspy_rom_wrappers_preflight_before_decoder_calls(self):
        arm9 = SimpleNamespace(arm9=MALICIOUS, loadArm9=mock.Mock())
        with self.assertRaises(Rifiuto):
            blz.ndspy_load_arm9_sicuro(arm9)
        arm9.loadArm9.assert_not_called()

        table = struct.pack("<8I", 2, 0x02200000, 0x1000, 0, 0, 0, 0,
                            0x01000008)
        overlays = SimpleNamespace(arm9OverlayTable=table, files=[MALICIOUS],
                                   loadArm9Overlays=mock.Mock())
        with self.assertRaises(Rifiuto):
            blz.ndspy_load_overlays_sicuri(overlays)
        overlays.loadArm9Overlays.assert_not_called()

        ram = 0x02000000
        clean_image = bytearray(0xBE0)
        struct.pack_into('<3I', clean_image, 0xBA0,
                         ram + 0xBD4, ram + 0xBE0, ram + 0xBC4)
        struct.pack_into('<3I', clean_image, 0xBD4, 0x023D8000, 16, 0)
        clean = SimpleNamespace(arm9=bytes(clean_image), arm9RamAddress=ram,
                                loadArm9=mock.Mock(return_value="ok"))
        self.assertEqual(blz.ndspy_load_arm9_sicuro(clean), "ok")
        clean.loadArm9.assert_called_once_with()

    def test_fishing_and_lullaby_preflight_before_ndspy(self):
        cases = ((fishing._read, (overlay_rom(fishing.OVERLAYS[2][0],
                                             fishing.OVERLAYS[2][1]), 2)),
                 (lullaby._read, (overlay_rom(lullaby.BASE, lullaby.SIZE),)))
        for function, arguments in cases:
            with self.subTest(function=function.__module__):
                with mock.patch("ndspy.codeCompression.decompress") as decoder:
                    with self.assertRaises(Rifiuto):
                        function(*arguments)
                decoder.assert_not_called()

    def test_ui_writer_preflights_before_ndspy(self):
        with mock.patch.object(ui.codeCompression, "decompress") as decoder:
            with self.assertRaises(Rifiuto):
                ui._decompress_overlay(MALICIOUS, 0x1000)
        decoder.assert_not_called()

    def test_ui_verifier_preflights_before_ndspy(self):
        image = ui_verify.Image.__new__(ui_verify.Image)
        image.records = {27: (27, 0, 0x1000, 0, 0, 0, 7, 0x01000000)}
        image.file = lambda _identity: MALICIOUS
        with mock.patch.object(ui_verify.codeCompression, "decompress") as decoder:
            with self.assertRaises(ValueError) as caught:
                image.overlay(27)
        self.assertIsInstance(caught.exception.__cause__, Rifiuto)
        decoder.assert_not_called()


if __name__ == "__main__":
    unittest.main()
