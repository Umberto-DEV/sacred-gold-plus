"""Release integration, on tiny synthetic inputs only."""
import io
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from sgp12 import manutenzione as m
from sgp12 import verifica
from sgp12.rom import Rifiuto

class IntegrazioneTests(unittest.TestCase):
    def test_stage_is_part_of_public_verifier(self):
        self.assertEqual(verifica.ORDINE_STADI[-1], 'manutenzione')

    def test_memory_applier_preserves_other_bytes(self):
        change = m.Cambio(2, b'cd', b'XY', 'test')
        with patch.object(m, 'prepara_stream', return_value=([change], {})):
            out, _ = m.applica(b'abcdef')
        self.assertEqual(out, b'abXYef')

    def test_memory_applier_rejects_wrong_preimage(self):
        change = m.Cambio(2, b'zz', b'XY', 'test')
        with patch.object(m, 'prepara_stream', return_value=([change], {})):
            with self.assertRaises(Rifiuto): m.applica(b'abcdef')

    def test_reader_rejects_corruption_inside_and_outside_patch(self):
        change = m.Cambio(2, b'cd', b'XY', 'test')
        with patch.object(m, 'prepara_stream', return_value=([change], {})):
            self.assertEqual(m.rileggi(b'abcdef', b'abXYef')['esito'], 'VERDE')
            for bad in (b'abXZef', b'abXYez', b'abXYef!'):
                with self.subTest(bad=bad):
                    with self.assertRaises(Rifiuto): m.rileggi(b'abcdef', bad)
