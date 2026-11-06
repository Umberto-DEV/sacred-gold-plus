"""Class A: authored synthetic bytes only; no game resources or names."""
import hashlib
import struct
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch
import zlib

from . import ui_resource as compiler, ui_resource_verify as readback


class VersionedNativeBallTests(unittest.TestCase):
    def test_one_versioned_resource_keeps_old_font_offsets_and_bounded_ball(self):
        self.assertEqual((compiler.MEMBER_MAGIC, compiler.CONFIG_MAGIC, compiler.VERSION), (b'UIR2', b'URC2', 2))
        self.assertEqual((compiler.ASSET_BYTES, compiler.TEXT_DIRECTORY_OFFSET, compiler.MAX_MEMBER_BYTES), (48320, 48448, 69632))


# Fixture quantities match the schema, but every byte/string is newly authored.
ASSETS = bytes((i * 13 + 7) % 256 for i in range(48320))
NAMES = {i: (1 + i % 509,) * (8 if i <= 142 else 7) + (65535,)
         for i in range(1, 494)}
WIDTHS_CRC = 0x12345678
AUTHORED = {5: (3, 0xE000, 509, 65535), 1: (1, 2, 65535)}


def old_archive():
    """Handwritten 51-member NARC with 34,912 synthetic GMIF bytes."""
    spans = [(i * 680, (i + 1) * 680) for i in range(50)] + [(34000, 34912)]
    table = b''.join(struct.pack('<II', *s) for s in spans)
    names = b'BTNF' + struct.pack('<I', 16) + bytes(8)
    data = bytes((i * 19 + 11) % 256 for i in range(34912))
    return (struct.pack('<4sHHIHH', b'NARC', 0xFFFE, 0x100, 35372, 16, 3)
            + struct.pack('<4sIHH', b'BTAF', 420, 51, 0) + table + names
            + struct.pack('<4sI', b'GMIF', 34920) + data)


def manual_resource(authored=AUTHORED):
    """Independent literal fixture writer; never calls a production packer."""
    pairs = sorted(list(authored.items()) + [(4096 + i, w) for i, w in NAMES.items()])
    directory, text = bytearray(), bytearray()
    for key, words in pairs:
        directory.extend(struct.pack('<HHI', key, len(words), 48448 + 8 * len(pairs) + len(text)))
        text.extend(struct.pack('<%dH' % len(words), *words))
    length = (48448 + len(directory) + len(text) + 3) & ~3
    head = bytearray(128)
    struct.pack_into('<4sHH14I', head, 0, b'UIR2', 2, 128, length, 0, 48320,
                     20, 128, 608, 576, 32, 12288, 32576, 44864, 32, WIDTHS_CRC, 7)
    head[64:96] = hashlib.sha256(ASSETS).digest()
    struct.pack_into('<8I', head, 96, 48448, len(pairs), len(directory),
                     48448 + len(directory), len(text), 1, 8, 0)
    member = bytes(head + ASSETS + directory + text)
    member += bytes(length - len(member))
    old = old_archive()
    out = bytearray(old[:16])
    struct.pack_into('<I', out, 8, 35380 + length)
    out.extend(struct.pack('<4sIHH', b'BTAF', 428, 52, 0))
    out.extend(old[28:436])
    out.extend(struct.pack('<II', 34912, 34912 + length))
    out.extend(old[436:452])
    out.extend(struct.pack('<4sI', b'GMIF', 34920 + length))
    out.extend(old[460:])
    out.extend(member)
    return bytes(out)


class ResourceCompilerTests(unittest.TestCase):
    def test_foreign_input_rejected_without_writes(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch('builtins.open', side_effect=AssertionError('compiler wrote/read a file')):
                with self.assertRaisesRegex(ValueError, 'exact supported'):
                    compiler.compile_resource(b'foreign', AUTHORED)
            self.assertEqual(list(Path(directory).iterdir()), [])

    def test_pack_small_exact_layout_matches_handwritten_bytes(self):
        member = compiler._pack_member('EN', ASSETS, NAMES, AUTHORED, WIDTHS_CRC)
        self.assertEqual(member, manual_resource()[35380:])

    def test_append_preserves_all_old_members_and_gmif(self):
        member = manual_resource()[35380:]
        original = old_archive()
        self.assertEqual(compiler._append_member(original, member), manual_resource())
        self.assertEqual(original, old_archive())

    def test_no_authored_and_it_language(self):
        en = compiler._pack_member('EN', ASSETS, NAMES, {}, WIDTHS_CRC)
        self.assertEqual(len(en), 60564)
        self.assertEqual(struct.unpack_from('<III', en, 96), (48448, 493, 3944))
        it = compiler._pack_member('IT', ASSETS, NAMES, {}, WIDTHS_CRC)
        self.assertEqual(struct.unpack_from('<I', it, 12)[0], 1)
        self.assertEqual(en[:12] + en[16:], it[:12] + it[16:])

    def test_authored_order_is_canonical_and_inputs_are_unchanged(self):
        labels = dict(AUTHORED)
        names = dict(NAMES)
        first = compiler._pack_member('EN', ASSETS, names, labels, WIDTHS_CRC)
        second = compiler._pack_member('EN', ASSETS, names, dict(reversed(list(labels.items()))), WIDTHS_CRC)
        self.assertEqual(first, second)
        self.assertEqual(labels, AUTHORED)
        self.assertEqual(names, NAMES)

    def test_actual_cap_boundary_and_excess(self):
        # 3*(8+4096) exceeds the cap. Two maximum strings plus 308 bytes fit exactly.
        exact = {1: (1,) * 2047 + (65535,), 2: (2,) * 2047 + (65535,),
                 3: (3,) * 425 + (65535,)}
        member = compiler._pack_member('EN', ASSETS, NAMES, exact, WIDTHS_CRC)
        self.assertEqual(len(member), 69632)
        exact[3] = (3,) * 426 + (65535,)
        with self.assertRaisesRegex(ValueError, 'cap'):
            compiler._pack_member('EN', ASSETS, NAMES, exact, WIDTHS_CRC)

    def test_large_directory_and_maximum_count(self):
        authored = {i: (1, 65535) for i in range(1, 532)}
        member = compiler._pack_member('EN', ASSETS, NAMES, authored, WIDTHS_CRC)
        self.assertEqual(struct.unpack_from('<I', member, 100)[0], 1024)
        authored[532] = (1, 65535)
        with self.assertRaisesRegex(ValueError, 'entries'):
            compiler._pack_member('EN', ASSETS, NAMES, authored, WIDTHS_CRC)

    def test_bad_authored_ids_and_domains(self):
        for key in (0, -1, 4096, 4097, 69632, True, '1'):
            with self.subTest(key=key), self.assertRaises(ValueError):
                compiler._pack_member('EN', ASSETS, NAMES, {key: (1, 65535)}, WIDTHS_CRC)
        for words in ((), (1,), (65535, 1, 65535), (0, 65535), (510, 65535),
                      (0xF100, 65535), (0xFFFE, 65535), (0xF0FD, 65535),
                      (0x25BC, 65535), (0x25BD, 65535), (True, 65535),
                      (-1, 65535), (69632, 65535), (1,) * 2048 + (65535,)):
            with self.subTest(words=words[:3]), self.assertRaises(ValueError):
                compiler._pack_member('EN', ASSETS, NAMES, {1: words}, WIDTHS_CRC)
        for words in ((65535,), (1, 0xE000, 509, 65535)):
            self.assertTrue(compiler._pack_member('EN', ASSETS, NAMES, {1: words}, WIDTHS_CRC))

    def test_bad_species_assets_language_and_old_archive(self):
        for species in ({}, {**NAMES, 494: (1, 65535)}, {k: v for k, v in NAMES.items() if k != 493},
                        {**NAMES, 1: (0xE000, 65535)}):
            with self.subTest(species=len(species)), self.assertRaises(ValueError):
                compiler._pack_member('EN', ASSETS, species, {}, WIDTHS_CRC)
        for lang, assets in (('FR', ASSETS), ('EN', ASSETS[:-1])):
            with self.assertRaises(ValueError):
                compiler._pack_member(lang, assets, NAMES, {}, WIDTHS_CRC)
        for at, value in ((8, 35371), (20, 419), (24, 50), (28, 0xFFFFFFFF)):
            old = bytearray(old_archive())
            struct.pack_into('<I', old, at, value)
            with self.subTest(at=at), self.assertRaises(ValueError):
                compiler._append_member(bytes(old), manual_resource()[35380:])


class ResourceReadbackTests(unittest.TestCase):
    def verify(self, replacement, authored=AUTHORED, language='EN', assets=ASSETS, names=NAMES):
        return readback._verify_parts(old_archive(), replacement, language, assets, names, authored, WIDTHS_CRC)

    def test_rejects_missing_resource(self):
        with self.assertRaises(ValueError):
            self.verify(old_archive())

    def test_independently_authored_fixture_and_config(self):
        with patch.object(compiler, '_pack_member', side_effect=AssertionError('shared packer')):
            receipt = self.verify(manual_resource())
        self.assertEqual(receipt['member_bytes'], 60596)
        self.assertEqual(receipt['species_text_bytes'], 8172)
        self.assertEqual(receipt['authored_text_bytes'], 14)
        self.assertEqual(receipt['budget_remaining'], 9036)
        config = bytes.fromhex(receipt['config_hex'])
        fields = struct.unpack('<16I', config)
        self.assertEqual(fields[:9], (0x32435255, 2, 0, 95976, 468, 51, 35380, 60596, 48320))
        self.assertEqual(fields[9:], (zlib.crc32(manual_resource()[:468]),
                                     zlib.crc32(manual_resource()[35380:]), WIDTHS_CRC, 509, 64, 7, 0))

    def test_every_header_field_rejects_mutation(self):
        for offset in (0, 4, 6, 8, 12, 16, 20, 24, 28, 32, 36, 40, 44, 48,
                       52, 56, 60, 64, 95, 96, 100, 104, 108, 112, 116, 120, 124):
            damaged = bytearray(manual_resource())
            damaged[35380 + offset] ^= 1
            with self.subTest(offset=offset), self.assertRaises(ValueError):
                self.verify(bytes(damaged))

    def test_directory_domain_bounds_contiguity_and_units_mutants(self):
        start = 35380 + 48448
        for offset, fmt, value in ((0, 'H', 0), (0, 'H', 5), (0, 'H', 0x1000),
                                  (0, 'H', 0x11EE), (2, 'H', 0), (2, 'H', 2049),
                                  (4, 'I', 128), (4, 'I', 0xFFFFFFFE),
                                  (4, 'I', 48857), (12, 'I', 48860), (12, 'I', 48870), (12, 'I', 48872)):
            damaged = bytearray(manual_resource())
            struct.pack_into('<' + fmt, damaged, start + offset, value)
            with self.subTest(offset=offset, value=value), self.assertRaises(ValueError):
                self.verify(bytes(damaged))

    def test_semantic_text_asset_and_language_mutants_without_receipt_trust(self):
        original = manual_resource()
        text_start = 35380 + struct.unpack_from('<I', original, 35380 + 108)[0]
        for position, value in ((text_start, 3), (text_start, 0), (text_start + 2, 65535), (text_start + 4, 1),
                                (text_start + 6, 0xF100), (text_start + 14, 7),
                                (35380 + 128, 9)):
            damaged = bytearray(original)
            struct.pack_into('<H', damaged, position, value)
            # A forger can freely recompute CRCs; readback receives no authorizing receipt.
            self.assertIsInstance(zlib.crc32(damaged[35380:]), int)
            with self.subTest(position=position, value=value), self.assertRaises(ValueError):
                self.verify(bytes(damaged))
        with self.assertRaises(ValueError):
            self.verify(original, language='IT')
        with self.assertRaises(ValueError):
            self.verify(original, authored={**AUTHORED, 1: (2, 2, 65535)})
        with self.assertRaises(ValueError):
            self.verify(original, names={**NAMES, 493: (2, 65535)})

    def test_all_51_members_and_nonmember_gmif_bytes_are_preserved(self):
        for i in range(51):
            damaged = bytearray(manual_resource())
            at = 468 + i * 680
            damaged[at] ^= 1
            with self.subTest(member=i), self.assertRaises(ValueError):
                self.verify(bytes(damaged))
        damaged = bytearray(manual_resource())
        damaged[28:36], damaged[36:44] = damaged[36:44], damaged[28:36]
        with self.assertRaises(ValueError):
            self.verify(bytes(damaged))

    def test_nonmember_gmif_gap_bytes_are_preserved(self):
        original = bytearray(old_archive())
        replacement = bytearray(manual_resource())
        # The first two image bytes are outside every member after this span change.
        struct.pack_into('<I', original, 28, 2)
        struct.pack_into('<I', replacement, 28, 2)
        report = readback._verify_parts(bytes(original), bytes(replacement), 'EN', ASSETS, NAMES, AUTHORED, WIDTHS_CRC)
        self.assertEqual(report['species_entries'], 493)
        replacement[468] ^= 1
        with self.assertRaisesRegex(ValueError, 'GMIF'):
            readback._verify_parts(bytes(original), bytes(replacement), 'EN', ASSETS, NAMES, AUTHORED, WIDTHS_CRC)

    def test_prefix_and_trailing_padding_and_hidden_bytes(self):
        for offset in (0, 4, 8, 12, 14, 16, 20, 24, 26, 28, 436, 444, 452, 460, 464):
            damaged = bytearray(manual_resource())
            damaged[offset] ^= 1
            with self.subTest(offset=offset), self.assertRaises(ValueError):
                self.verify(bytes(damaged))
        # One EOS-only label makes two bytes of alignment padding.
        padded = manual_resource({1: (65535,)})
        self.verify(padded, authored={1: (65535,)})
        damaged = bytearray(padded)
        damaged[-1] = 1
        with self.assertRaises(ValueError):
            self.verify(bytes(damaged), authored={1: (65535,)})
        with self.assertRaises(ValueError):
            self.verify(manual_resource() + b'\0\0\0\0')

    def test_valid_maximum_cap_and_entry_count_independently_read_back(self):
        exact = {1: (1,) * 2047 + (65535,), 2: (2,) * 2047 + (65535,),
                 3: (3,) * 425 + (65535,)}
        report = self.verify(manual_resource(exact), authored=exact)
        self.assertEqual(report['member_bytes'], 69632)
        self.assertEqual(report['budget_remaining'], 0)
        many = {i: (1, 65535) for i in range(1, 532)}
        self.assertEqual(self.verify(manual_resource(many), authored=many)['text_entries'], 1024)

    def test_recomputed_asset_label_still_cannot_replace_input_assets(self):
        damaged = bytearray(manual_resource())
        damaged[35380 + 128] ^= 1
        damaged[35380 + 64:35380 + 96] = hashlib.sha256(damaged[35380 + 128:35380 + 48448]).digest()
        with self.assertRaisesRegex(ValueError, 'asset slice'):
            self.verify(bytes(damaged))

    def test_missing_species_and_hidden_string_even_with_consistent_geometry(self):
        damaged = bytearray(manual_resource())
        # Last name is no longer a species key, but the entry count and data are unchanged.
        struct.pack_into('<H', damaged, 35380 + 48448 + 8 * 494, 4095)
        with self.assertRaises(ValueError):
            self.verify(bytes(damaged))
        for offset, value in ((100, 1025), (104, 0xFFFFFFF8), (108, 0xFFFFFFFE),
                              (112, 1), (112, 0xFFFFFFFE)):
            damaged = bytearray(manual_resource())
            struct.pack_into('<I', damaged, 35380 + offset, value)
            with self.subTest(offset=offset, value=value), self.assertRaises(ValueError):
                self.verify(bytes(damaged))

    def test_public_readback_does_not_accept_synthetic_rom(self):
        with self.assertRaisesRegex(ValueError, 'exact supported'):
            readback.verify_resource(b'foreign', manual_resource(), AUTHORED)
