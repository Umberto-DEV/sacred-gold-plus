#!/usr/bin/env python3
"""Suite host (unittest), SENZA ROM: esercita solo la logica pura di
`applica_guida.py`/`rileggi_guida.py` (riconoscimento di stato, confini della
regione patchata, forma delle istruzioni sostitute) con byte sintetici, mai
un file .nds vero (per quello vedi `sgp12/test_lib.py::TestBloccoGuida`,
che usa `base-1.1-{EN,IT}.nds`, e la corsa `hg_runtime` in `prove/`).

Uso:
    python3 -m unittest discover -s test -p 'test_*.py' -v
"""
import hashlib
import struct
import sys
import unittest
from pathlib import Path

QUI = Path(__file__).resolve().parent
sys.path.insert(0, str(QUI.parent / "tools"))
import applica_guida as ag  # noqa: E402


def _sha(b):
    return hashlib.sha256(bytes(b)).hexdigest()


class TestBytesSpenti(unittest.TestCase):
    """`SPENTA_BYTES` e' costruita e verificata (assert) al caricamento del
    modulo stesso (`_spenta_bytes()`): se il modulo importa senza eccezioni,
    quel controllo e' gia' passato. Qui verifichiamo la FORMA delle
    istruzioni, non solo lo sha256 (un mutante che cambiasse l'sha atteso
    insieme al blob passerebbe lo sha ma non la lettura Thumb)."""

    def test_lunghezza_e_sha(self):
        self.assertEqual(len(ag.SPENTA_BYTES), ag.PATCH_N)
        self.assertEqual(_sha(ag.SPENTA_BYTES), ag.SPENTA_SHA)

    def test_le_prime_quattro_istruzioni_sono_quelle_attese(self):
        movs_r0_1, str_badge, str_pending, b_target = struct.unpack_from("<HHHH", ag.SPENTA_BYTES, 0)
        self.assertEqual(movs_r0_1, 0x2001, "movs r0,#1")
        # str r0,[r7,#imm5*4]: 0110 0 iiiii 111 000 = 0x6000 | (imm5<<6) | (7<<3) | 0
        self.assertEqual(str_badge, 0x6000 | (11 << 6) | (7 << 3) | 0, "str r0,[r7,#0x2C] (P->badge)")
        self.assertEqual(str_pending, 0x6000 | (12 << 6) | (7 << 3) | 0, "str r0,[r7,#0x30] (P->pending)")
        # b #imm11: 1110 0 offset11, offset11 = (target - (addr+4)) / 2
        self.assertEqual(b_target & 0xF800, 0xE000, "b incondizionata Thumb")

    def test_il_resto_e_nop_mov_r8_r8(self):
        resto = ag.SPENTA_BYTES[8:]
        self.assertEqual(len(resto) % 2, 0)
        self.assertTrue(all(resto[i:i + 2] == b"\xC0\x46" for i in range(0, len(resto), 2)),
                        "il riempimento dopo la 'b' deve essere tutto NOP (mov r8,r8)")

    def test_branch_target_e_0x1ff8b18(self):
        # PC per una Thumb B e' indirizzo_istruzione+4; l'istruzione e' la 4a
        # (byte 6..8) della regione che comincia a PATCH_ADDR.
        b_instr_addr = ag.PATCH_ADDR + 6
        b_instr = struct.unpack_from("<H", ag.SPENTA_BYTES, 6)[0]
        offset11 = b_instr & 0x7FF
        # rappresentazione a complemento a 2 su 11 bit
        if offset11 & 0x400:
            offset11 -= 0x800
        target = (b_instr_addr + 4) + offset11 * 2
        self.assertEqual(target, 0x01FF8B18)


class TestStato(unittest.TestCase):
    def test_spenta_e_riconosciuta(self):
        self.assertEqual(ag.stato_da_bytes(ag.SPENTA_BYTES), "spenta")

    def test_originale_sintetico_e_riconosciuto(self):
        # Non serve la vera preimmagine (96 B reali della ROM) per esercitare
        # la LOGICA di stato_da_bytes: basta un blob il cui sha coincida con
        # ORIGINALE_SHA per la durata del test.
        sintetico = b"\x11" * ag.PATCH_N
        with _patched(ag, "ORIGINALE_SHA", _sha(sintetico)):
            self.assertEqual(ag.stato_da_bytes(sintetico), "originale")

    def test_un_byte_diverso_e_ignoto(self):
        alterato = bytearray(ag.SPENTA_BYTES)
        alterato[0] ^= 0xFF
        self.assertEqual(ag.stato_da_bytes(bytes(alterato)), "ignoto")

    def test_originale_e_spenta_non_si_confondono(self):
        self.assertNotEqual(ag.ORIGINALE_SHA, ag.SPENTA_SHA)


class TestFirmaLingua(unittest.TestCase):
    def test_en_it_non_si_confondono(self):
        self.assertNotEqual(ag.LINGUA_FIRMA["EN"], ag.LINGUA_FIRMA["IT"])

    def test_riconosci_lingua_usa_solo_i_primi_1098_byte(self):
        class FintoArm9:
            def __init__(self, campione):
                self._campione = campione

            def leggi(self, ram, n):
                assert ram == ag.TEXT and n == ag.TEXT_SIGNATURE_N
                return self._campione

        campione = b"\x00" * ag.TEXT_SIGNATURE_N
        with _patched(ag, "LINGUA_FIRMA", {"XX": _sha(campione)}):
            self.assertEqual(ag.riconosci_lingua(FintoArm9(campione)), "XX")
        self.assertIsNone(ag.riconosci_lingua(FintoArm9(b"\x01" * ag.TEXT_SIGNATURE_N)))


class TestCostanti(unittest.TestCase):
    def test_regione_di_96_byte(self):
        self.assertEqual(ag.PATCH_N, 96)

    def test_regione_dentro_la_finestra_storica_r5(self):
        # 0x01FF8620-0x01FFA000: riserva r5 storica (non la riserva 1.2).
        self.assertTrue(0x01FF8620 <= ag.PATCH_ADDR < ag.PATCH_ADDR + ag.PATCH_N <= 0x01FFA000)

    def test_regione_prima_della_zona_testi(self):
        self.assertLess(ag.PATCH_ADDR + ag.PATCH_N, ag.TEXT)


class _patched:
    """Sostituisce temporaneamente un attributo del modulo (niente
    `unittest.mock` per restare senza dipendenze extra)."""

    def __init__(self, modulo, nome, valore):
        self.modulo, self.nome, self.valore = modulo, nome, valore

    def __enter__(self):
        self.precedente = getattr(self.modulo, self.nome)
        setattr(self.modulo, self.nome, self.valore)

    def __exit__(self, *exc):
        setattr(self.modulo, self.nome, self.precedente)


if __name__ == "__main__":
    unittest.main()
