"""Class B: install and independently read SG-SV01 on exact EN/IT V4 bytes.

Inputs are immutable and only patched in memory.  The executable policy itself
is covered by ``features/native-core/test/test_qualita.py`` in Unicorn.
"""
import hashlib
import importlib.util
import os
from pathlib import Path
import shutil
import struct
import tempfile
import unittest

from sgp12 import chunk as save_chunk
from sgp12.rom import Arm9
from . import plus_save as p


ROOT = Path(__file__).resolve().parents[2]
V4_ROOT = ROOT / 'local/experiments/balance493-2026-10-28'
INPUTS = {
    'EN': (os.environ.get('SGP_PLUS_SAVE_ROM_EN') or V4_ROOT / 'candidate-v4-EN.nds',
           '179edfb1ca331503f438e98f3afccfb0ab85759bf9ab88fb86c735f5fcefbf90'),
    'IT': (os.environ.get('SGP_PLUS_SAVE_ROM_IT') or V4_ROOT / 'candidate-v4-IT.nds',
           '2a2f0b437fca524c18b71b20feb01a1f51351e61c7c897ce73d9b3be1ee3a156'),
}
REQUIRE = os.environ.get('SGP_PLUS_SAVE_REQUIRE_INPUTS') == '1'

RAW_SAVE_FIXTURES = {
    'EN': (ROOT / 'local/experiments/save-ui-runtime-2026-10-28/'
                  'expanded-EN/save/imported.sav',
           '78eee1207d2721bc961a57ca3e216435ca9542f8c44a7483d43d9c6a087d83a3'),
    'IT': (ROOT / 'local/experiments/save-ui-runtime-2026-10-28/'
                  'expanded-IT/save/imported.sav',
           '88dde0da04c2f254106e95c45653594e74b97019191cba552bed096f6dd7b832'),
}
SAVE_BYTES = 512 * 1024
SECTOR_A = 0x0002F000
SECTOR_B = 0x0006F000
RECORD_BYTES = 32
STATE = 0x023D8700
BUFFER = 0x023D8F00
CRC_WRAPPER = (0x0201FF98, 24,
               '22609c73d37821e49e3723001f8f73d576f7ff0afba6973294c176a92c75bb3c')
CRC_DISPATCH = (0x020E3A2C, 44,
                'd3ef7a3df8801864e1d79f82423fb19d5a48e85cf3d7e1fe2ebe30c5a771e69e')
CRC_KERNEL = (0x020E38E0, 64,
              '0f9c8e17ba9064419713f6153facb368e43e58ea8d4872ab0f5cd32d98e21396')


def _sha(data):
    return hashlib.sha256(bytes(data)).hexdigest()


def _raw_fixture(case, language):
    path, digest = RAW_SAVE_FIXTURES[language]
    if not path.is_file():
        case.skipTest('private raw-save fixture unavailable: ' + str(path))
    data = path.read_bytes()
    case.assertEqual((len(data), _sha(data)), (SAVE_BYTES, digest))
    return path, data, digest


def _bench_module():
    path = ROOT / 'source/features/native-core/test/banco.py'
    spec = importlib.util.spec_from_file_location('sgp131_plus_save_bench', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _bench(case, module, payload, symbols, save):
    try:
        bench = module.Banco()
    except RuntimeError as error:
        case.skipTest(str(error))
    bench.carica(p.BASE, payload)
    bench.simboli = symbols
    bench.carica(STATE, bytes(32))
    bench.carica(BUFFER, bytes(32))
    bench.settori = {
        SECTOR_A: bytes(save[SECTOR_A:SECTOR_A + RECORD_BYTES]),
        SECTOR_B: bytes(save[SECTOR_B:SECTOR_B + RECORD_BYTES]),
    }
    return bench


def image(case, language):
    path, digest = INPUTS[language]
    path = Path(path)
    if not path.is_file():
        reason = 'private %s V4 input missing: %s' % (language, path)
        if REQUIRE:
            case.fail(reason)
        case.skipTest(reason)
    raw = path.read_bytes()
    case.assertEqual(hashlib.sha256(raw).hexdigest(), digest)
    return raw


class PlusSaveRomTests(unittest.TestCase):
    def test_raw_save_crc_matches_the_exact_hgss_machine_kernel(self):
        module = _bench_module()
        for language in ('EN', 'IT'):
            _, save, _ = _raw_fixture(self, language)
            arm = Arm9.from_bytes(image(self, language))
            for address, length, digest in (CRC_WRAPPER, CRC_DISPATCH, CRC_KERNEL):
                with self.subTest(language=language, address=hex(address)):
                    self.assertEqual(_sha(arm.leggi(address, length)), digest)
            for offset in (SECTOR_A, SECTOR_B):
                record = save[offset:offset + RECORD_BYTES]
                with self.subTest(language=language, sector=hex(offset)):
                    self.assertEqual(record[16:20], b'SGP2')
                    expected = int.from_bytes(record[30:32], 'little')
                    self.assertEqual(module.crc16_ccitt(record[:30]), expected)
                    self.assertEqual(save_chunk.calcola_crc_gioco(record[:30]), expected)
                    self.assertTrue(save_chunk.unpack_footer(record).valido())

    def test_exact_compartment_en_it_and_independent_readback(self):
        for language in ('EN', 'IT'):
            before = image(self, language)
            with tempfile.TemporaryDirectory(prefix='plus-save-test-') as work:
                after, receipt = p.apply(before, language, work_dir=work)
            with self.subTest(language=language):
                self.assertEqual(p.verify(before, after, receipt)['payload_sha256'],
                                 p.PAYLOAD_SHA256)
                restored = bytearray(after)
                for start, end in p.spans(before):
                    restored[start:end] = before[start:end]
                self.assertEqual(bytes(restored), before)
                self.assertEqual(len(before), len(after))
                with self.assertRaisesRegex(ValueError, 'preimage'):
                    with tempfile.TemporaryDirectory(prefix='plus-save-repeat-') as work:
                        p.apply(after, language, work_dir=work)

    def test_verifier_rejects_extra_change_and_missing_fix_byte(self):
        before = image(self, 'EN')
        with tempfile.TemporaryDirectory(prefix='plus-save-test-') as work:
            after, receipt = p.apply(before, 'EN', work_dir=work)
        start, _ = p.span(before)
        damaged = bytearray(after)
        damaged[start] ^= 1
        with self.assertRaises(ValueError):
            p.verify(before, bytes(damaged), receipt)
        damaged = bytearray(after)
        damaged[0x300] ^= 1
        with self.assertRaisesRegex(ValueError, 'outside'):
            p.verify(before, bytes(damaged), receipt)
        damaged = bytearray(after)
        hook = p.spans(before)[1][0]
        damaged[hook] ^= 1
        with self.assertRaisesRegex(ValueError, 'hook'):
            p.verify(before, bytes(damaged), receipt)

    def test_raw_save_copies_cover_zero_partial_and_full_writes_then_cold_load(self):
        """Exercise the installed payload against exact older raw-save copies.

        The two fixtures already contain Plus settings and expanded Bag data.
        Only the two private 32-byte Plus records are ever copied back.  Thus
        this proves both partial-write recovery and byte-for-byte preservation
        of progress, party, boxes, inventory and Bag extensions outside those
        records; it is not a native in-game SAVE or a physical flash test.
        """
        module = _bench_module()
        cases = (
            ((0, 0), 3, (1, 1), (2, 2)),
            ((1, 0), 2, (0, 0), (3, 2)),
            ((0, 1), 2, (0, 0), (2, 3)),
            ((1, 1), 1, (0, 0), (3, 3)),
        )
        for language in ('EN', 'IT'):
            fixture, original, digest = _raw_fixture(self, language)
            before = image(self, language)
            with tempfile.TemporaryDirectory(prefix='plus-save-raw-rom-') as work:
                installed, receipt = p.apply(before, language, work_dir=work)
            arm = Arm9.from_bytes(installed)
            payload = arm.leggi(p.BASE, p.PAYLOAD_BYTES)
            self.assertEqual(_sha(payload), p.PAYLOAD_SHA256)
            symbols = receipt['compiled']['symbols']

            for outcomes, write_status, cold_flags, generations in cases:
                with self.subTest(language=language, outcomes=outcomes):
                    with tempfile.TemporaryDirectory(prefix='plus-save-raw-copy-') as work:
                        copy = Path(work) / (language + '.sav')
                        shutil.copyfile(fixture, copy)
                        save = bytearray(copy.read_bytes())
                        self.assertEqual(_sha(save), digest)

                        bench = _bench(self, module, payload, symbols, save)
                        bench.chiama(symbols[p.ENTRY_LOAD], (0x12345678,))
                        state = bytearray(bench.leggi(STATE, 32))
                        self.assertEqual((state[0], state[1], state[3]), (1, 1, 2))
                        state[0] = 0
                        state[1] = 0
                        bench.carica(STATE, state)
                        bench.scrittura_esiti = list(outcomes)
                        result = bench.chiama(symbols[p.ENTRY_SAVE], (0x12345678,))[0]
                        live = bench.leggi(STATE, 32)
                        self.assertEqual((result, live[5]), (2, write_status))

                        for offset in (SECTOR_A, SECTOR_B):
                            save[offset:offset + RECORD_BYTES] = bench.settori[offset]
                        copy.write_bytes(save)

                        changed = {index for index, pair in enumerate(zip(original, save))
                                   if pair[0] != pair[1]}
                        allowed = (set(range(SECTOR_A, SECTOR_A + RECORD_BYTES))
                                   | set(range(SECTOR_B, SECTOR_B + RECORD_BYTES)))
                        self.assertLessEqual(changed, allowed)
                        if outcomes == (0, 0):
                            self.assertFalse(changed)
                        self.assertEqual(_sha(fixture.read_bytes()), digest)

                        a_generation = struct.unpack_from('<I', save, SECTOR_A + 20)[0]
                        b_generation = struct.unpack_from('<I', save, SECTOR_B + 20)[0]
                        self.assertEqual((a_generation, b_generation), generations)

                        cold = _bench(self, module, payload, symbols, save)
                        cold.chiama(symbols[p.ENTRY_LOAD], (0x12345678,))
                        loaded = cold.leggi(STATE, 32)
                        self.assertEqual((loaded[0], loaded[1], loaded[3]),
                                         cold_flags + (2,))


if __name__ == '__main__':
    unittest.main()
