"""Verifiche leggere di rifiuto e scrittura streaming su file sintetici."""
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from compila import compila, SOURCE
sys.path.insert(0, str(SOURCE))
from sgp12 import manutenzione as m
from sgp12.rom import Rifiuto, sha_file


class ApplicatoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='sgp-stream-test-')
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.base, self.out = self.root/'in.bin', self.root/'out.bin'
        self.base.write_bytes(bytes(range(32)))
        self.hash = sha_file(self.base)
        self.cambi = [m.Cambio(7, bytes([7, 8, 9]), b'ABC', 'confine blocchi')]

    def test_scrittura_a_cavallo_del_blocco_e_byte_estranei_intatti(self):
        with patch.object(m, 'CHUNK', 8):
            result = m.scrivi(self.base, self.out, self.cambi, self.hash)
        self.assertEqual(self.out.read_bytes(), bytes(range(7))+b'ABC'+bytes(range(10, 32)))
        self.assertEqual(result, sha_file(self.out))
        self.assertEqual(sha_file(self.base), self.hash)

    def test_output_esistente_non_viene_sovrascritto(self):
        self.out.write_bytes(b'preesistente')
        with self.assertRaises(Rifiuto): m.scrivi(self.base, self.out, self.cambi, self.hash)
        self.assertEqual(self.out.read_bytes(), b'preesistente')

    def test_preimmagine_errata_non_crea_output(self):
        bad = [m.Cambio(7, b'err', b'ABC', 'errata')]
        with self.assertRaises(Rifiuto): m.scrivi(self.base, self.out, bad, self.hash)
        self.assertFalse(self.out.exists())

    def test_ingresso_cambiato_non_crea_output(self):
        self.base.write_bytes(b'cambiato')
        with self.assertRaises(Rifiuto): m.scrivi(self.base, self.out, self.cambi, self.hash)
        self.assertFalse(self.out.exists())

    def test_patch_sovrapposte_rifiutate(self):
        overlap = self.cambi + [m.Cambio(8, bytes([8]), b'D', 'overlap')]
        with self.assertRaises(Rifiuto): m.scrivi(self.base, self.out, overlap, self.hash)
        self.assertFalse(self.out.exists())

    def test_fallimento_scrittura_rimuove_solo_il_parziale_proprio(self):
        with patch.object(m, 'blocco_modificato', side_effect=OSError('disco pieno')):
            with self.assertRaises(OSError): m.scrivi(self.base, self.out, self.cambi, self.hash)
        self.assertFalse(self.out.exists())
        self.assertEqual(sha_file(self.base), self.hash)

    def test_rom_sconosciuta_rifiutata_prima_di_decodificare(self):
        with self.assertRaisesRegex(Rifiuto, '1.2.3'): m.prepara(self.base)

    def test_build_ricompilato_accettato_e_blob_corrotto_rifiutato(self):
        build = self.root / 'build'
        compila(build)
        m.carica_build(build)
        p = build / 'copie.bin'
        raw = bytearray(p.read_bytes()); raw[0] ^= 1; p.write_bytes(raw)
        with self.assertRaisesRegex(Rifiuto, 'blob alterato'): m.carica_build(build)

    def test_bl_note_decodificate_senza_usare_encoder(self):
        self.assertEqual(m.destinazione_bl(0x02000000, bytes.fromhex('00f000f8')), 0x02000004)
        self.assertEqual(m.destinazione_bl(0x02000000, bytes.fromhex('fff7feff')), 0x02000000)


if __name__ == '__main__': unittest.main()
