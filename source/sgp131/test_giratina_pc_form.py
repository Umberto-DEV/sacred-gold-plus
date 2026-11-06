"""Exact producer/verifier tests for HG-F16 Giratina PC form statistics."""
import hashlib
from pathlib import Path
import unittest

from sgp12.blz import blz_decomprimi
from sgp12.rom import Rom, bl_decode


ROOT = Path(__file__).resolve().parents[2]
V4_ROOT = ROOT / 'local/experiments/balance493-2026-10-28'
V4 = {
    'EN': ('179edfb1ca331503f438e98f3afccfb0ab85759bf9ab88fb86c735f5fcefbf90',
           147345256,
           '4202846876957138d3f4bb7e7c0f0e09ee9c81f210e1797fbb053013c6514237'),
    'IT': ('2a2f0b437fca524c18b71b20feb01a1f51351e61c7c897ce73d9b3be1ee3a156',
           153228136,
           '8f0678f66b0cb9337537dba9c819470bf9108c105113e0d6f02bfb5f7d01c1c4'),
}


def implementation(case):
    try:
        from . import giratina_pc_form
    except ImportError as error:
        case.fail('HG-F16 producer is not implemented: ' + str(error))
    return giratina_pc_form


def candidate(case, language):
    path = V4_ROOT / ('candidate-v4-%s.nds' % language)
    if not path.is_file():
        case.skipTest('immutable V4 candidate unavailable: ' + str(path))
    data = path.read_bytes()
    case.assertEqual((hashlib.sha256(data).hexdigest(), len(data)),
                     V4[language][:2])
    return data


class GiratinaPcFormProducerTests(unittest.TestCase):
    def test_exact_overlay_postimage_keeps_rom_geometry_and_blz_slot(self):
        """Catches relocation, y9/FAT edits and any logical byte outside the two seams."""
        G = implementation(self)
        for language, (_input_sha, _size, output_sha) in V4.items():
            before = candidate(self, language)
            after, receipt = G.apply(before, language)
            old_rom, new_rom = Rom(before), Rom(after)
            old_v, old_stream, old_image = old_rom.immagine_overlay(14)
            new_v, new_stream, new_image = new_rom.immagine_overlay(14)
            with self.subTest(language=language):
                self.assertEqual(hashlib.sha256(after).hexdigest(), output_sha)
                self.assertEqual(len(after), len(before))
                self.assertEqual(old_v, new_v)
                self.assertEqual(old_v['ram'], 0x021E5900)
                self.assertEqual(old_v['ram_size'], 0x13A80)
                self.assertEqual(old_v['dim_compressa'], 51584)
                self.assertEqual(len(old_stream), len(new_stream), 51584)
                self.assertEqual(hashlib.sha256(old_image).hexdigest(),
                                 'd515fb04f06371d854ae5ecaed717ceb8338afde422f497bb3dc8590cc81ead5')
                self.assertEqual(hashlib.sha256(new_image).hexdigest(),
                                 '39981ee7a81c78093e8b6b31b793a7bd9d482b57440ffe94612f798234146e4e')
                self.assertEqual(hashlib.sha256(new_stream).hexdigest(),
                                 '85b374d5dba3bc983aa03f99bf2968db8cd637d1314ff6305e2f7a68b8de6306')
                self.assertEqual(blz_decomprimi(new_stream, 0x13A80), new_image)
                self.assertEqual(new_image[0x88:0x90],
                                 bytes.fromhex('004b184765931f02'))
                self.assertEqual(new_image[0x13A64:0x13A80], bytes.fromhex(
                    '10b5041c0df692ff01b48068002178f6e3fc01bc0049084791591e02'))
                restored = bytearray(new_image)
                restored[0x88:0x90] = old_image[0x88:0x90]
                restored[0x13A64:0x13A80] = old_image[0x13A64:0x13A80]
                self.assertEqual(bytes(restored), old_image)
                self.assertEqual(G.verify(before, after, receipt), receipt['verification'])

    def test_hook_replays_displaced_prologue_and_calls_nonforcing_party_repair(self):
        """Catches wrong resume, wrong work offset, force-origin, or ARM-state literals."""
        G = implementation(self)
        before = candidate(self, 'EN')
        after, _receipt = G.apply(before, 'EN')
        v, _stream, image = Rom(after).immagine_overlay(14)
        hook = image[0x88:0x90]
        stub = image[0x13A64:0x13A80]
        self.assertEqual(int.from_bytes(hook[4:], 'little'), 0x021F9365)
        self.assertEqual(bl_decode(0x021F9368, stub[4:8]), 0x02007290)
        self.assertEqual(stub[8:14], bytes.fromhex('01b480680021'))
        self.assertEqual(bl_decode(0x021F9372, stub[14:18]), 0x02071D3C)
        self.assertEqual(stub[18:24], bytes.fromhex('01bc00490847'))
        self.assertEqual(int.from_bytes(stub[24:], 'little'), 0x021E5991)
        self.assertEqual((v['static_init_start'], v['static_init_end']),
                         (0x021F9360, 0x021F9364))

    def test_changed_regions_is_the_exact_compressed_overlay_slot(self):
        """Catches an under-declared confinement span for recompressed BLZ bytes."""
        G = implementation(self)
        for language in V4:
            before = candidate(self, language)
            rom = Rom(before)
            v = rom.voce_overlay(14)
            fat = rom.voce_fat(v['file_id'])
            self.assertEqual(G.changed_regions(before),
                             ((fat['inizio'], fat['fine']),))

    def test_preimage_language_reapply_and_verifier_mutants_fail_closed(self):
        """Catches applying to a foreign language/image or accepting undeclared edits."""
        G = implementation(self)
        before = candidate(self, 'EN')
        after, receipt = G.apply(before, 'EN')
        with self.assertRaisesRegex(ValueError, 'language anchor'):
            G.apply(before, 'IT')
        with self.assertRaisesRegex(ValueError, 'preimage|overlay'):
            G.apply(after, 'EN')

        rom = Rom(before)
        v, stream, image = rom.immagine_overlay(14)
        mutant_image = bytearray(image)
        mutant_image[0x88] ^= 1
        with self.assertRaisesRegex(ValueError, 'preimage|overlay'):
            G.patch_overlay_image(bytes(mutant_image))

        outside = bytearray(after)
        outside[0x300] ^= 1
        forged = dict(receipt)
        forged['output_sha256'] = hashlib.sha256(outside).hexdigest()
        with self.assertRaisesRegex(ValueError, 'outside|identity'):
            G.verify(before, bytes(outside), forged)

        for key, value in (
                ('stage', 'foreign'), ('overlay_id', 15),
                ('compressed_postimage_sha256', '0' * 64)):
            forged = dict(receipt)
            forged[key] = value
            with self.subTest(key=key), self.assertRaisesRegex(
                    ValueError, 'receipt identity'):
                G.verify(before, after, forged)

        self.assertEqual(hashlib.sha256(candidate(self, 'EN')).hexdigest(), V4['EN'][0])


if __name__ == '__main__':
    unittest.main()
