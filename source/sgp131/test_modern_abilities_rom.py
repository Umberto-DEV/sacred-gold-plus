"""Class B: install the Keen Eye stage on V4 EN/IT copies in memory and run it.

The slot is the integrator's `modern-accuracy.code` entry, read from
sgp131/data/reserve-map.json (never hard-coded here); on V4 those bytes still
hold retired Guide code, so the results live only in memory and are never a
playable ROM. The installed ROM's own ARM9 and overlay 12 bytes are executed by
the accuracy bench; no payload is injected.

Inputs: SGP_ACCURACY_ROM_EN/IT (default V4 candidates), SGP_TEXT_CHARMAP or
$SGP_PRET_SOURCE/charmap.txt (default local/tools/pokeheartgold/charmap.txt).
Missing inputs skip; SGP_ACCURACY_REQUIRE_INPUTS=1 makes them fail.
"""
import hashlib
import json
import os
import struct
import sys
import tempfile
import unittest
from pathlib import Path

from sgp131 import modern_abilities as stage
from sgp131.blz_test_support import alternate_same_size_stream

TESTS = stage.FEATURE / 'test'
if str(TESTS) not in sys.path:
    sys.path.insert(0, str(TESTS))
import accuracy_bench as bench  # noqa: E402

_CACHE = {}


def reserved_slot():
    """The `modern-accuracy.code` payload entry of the reviewed reserve map."""
    found = []

    def walk(node):
        if isinstance(node, dict):
            if node.get('name') == 'modern-accuracy.code':
                found.append(node)
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)
    walk(json.loads((stage.SOURCE / 'sgp131/data/reserve-map.json').read_text()))
    if len(found) != 1 or found[0].get('kind') != 'payload':
        raise AssertionError('reserve map must hold exactly one modern-accuracy.code payload entry')
    return found[0]['start'], found[0]['bytes']


def forgeries(before, after):
    """Overlay 12 streams that decode to the same image but are not the writer's output."""
    fat = struct.unpack_from('<I', before, 0x48)[0]
    y9 = struct.unpack_from('<I', before, 0x50)[0] + 32 * 12
    fid = struct.unpack_from('<8I', before, y9)[6]
    start, end = struct.unpack_from('<II', after, fat + 8 * fid)
    stream = bytes(after[start:end])
    footer = bytearray(after)
    footer[end - 8] ^= 1
    w0, w1 = struct.unpack_from('<II', stream, len(stream) - 8)
    longer = stream[:-8] + b'\xFF' * 4 + struct.pack('<II', w0 + 4 + (4 << 24), (w1 - 4) & 0xFFFFFFFF)
    padded = bytearray(after)
    padded[start:start + len(longer)] = longer
    struct.pack_into('<I', padded, fat + 8 * fid + 4, start + len(longer))
    struct.pack_into('<I', padded, y9 + 28, struct.unpack_from('<I', padded, y9 + 28)[0] + 4)
    alternate = bytearray(after)
    alternate[start:end] = alternate_same_size_stream(stream)
    return {'footer_enc_len_plus_one': bytes(footer), 'padding_with_fat_y9_plus_four': bytes(padded),
            'alternate_safe_raw_prefix_cut': bytes(alternate)}


def charmap_path():
    configured = os.environ.get('SGP_TEXT_CHARMAP')
    if configured:
        return Path(configured)
    pret = os.environ.get('SGP_PRET_SOURCE')
    return Path(pret) / 'charmap.txt' if pret else bench.REPOSITORY / 'local/tools/pokeheartgold/charmap.txt'


class InstalledKeenEye(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.work = tempfile.TemporaryDirectory(prefix='modern-abilities-rom-')

    @classmethod
    def tearDownClass(cls):
        cls.work.cleanup()

    def inputs(self, language):
        path, digest = bench.input_path(language)
        charmap = charmap_path()
        if path is None or not charmap.is_file():
            if os.environ.get(bench.REQUIRE) == '1':
                self.fail('missing V4 %s input or charmap' % language)
            self.skipTest('private V4 %s ROM or pinned charmap not available' % language)
        if language not in _CACHE:
            data = path.read_bytes()
            self.assertEqual(hashlib.sha256(data).hexdigest(), digest)
            _CACHE[language] = data
        return _CACHE[language], charmap

    def slot(self, data):
        start, size = reserved_slot()
        at = stage._arm9_locate(stage._arm9_map(data), start, size)
        return {'name': 'modern-accuracy.code', 'start': start, 'bytes': size,
                'preimage_sha256': hashlib.sha256(data[at:at + size]).hexdigest()}

    def installed(self, language):
        data, charmap = self.inputs(language)
        key = ('installed', language)
        if key not in _CACHE:
            _CACHE[key] = stage.apply(data, language, Path(self.work.name), slot=self.slot(data), charmap=charmap)
        return data, charmap, _CACHE[key]

    def test_installed_rom_runs_new_semantics_from_its_own_bytes(self):
        rows = [(51, 12, 100, 33, 100), (109, 12, 100, 100, 100), (51, 0, 75, 100, 75),
                (109, 0, 75, 75, 75), (0, 12, 100, 33, 33)]
        for language in ('EN', 'IT'):
            data, _, (after, receipt) = self.installed(language)
            old = bench.Bench(data, bench.overlay_image(data))
            new = bench.Bench(after, bench.overlay_image(after))
            for ability, eva, accuracy, before_hits, after_hits in rows:
                case = {'abilities': {0: ability}, 'eva': {1: eva}, 'accuracy': accuracy}
                self.assertEqual(old.enumerate(case)['hits'], before_hits, (language, ability, eva))
                result = new.enumerate(case)
                self.assertEqual(result['hits'], after_hits, (language, ability, eva))
                self.assertEqual(result['rng_calls'], [1])
                self.assertTrue(result['preserved'])
            suppressed = {'abilities': {0: 51}, 'eva': {1: 12}, 'accuracy': 100,
                          'effect_flags': {0: bench.SUPPRESSED}}
            self.assertEqual(new.enumerate(suppressed)['hits'], 33, language)
            self.assertEqual(receipt['code']['native']['bytes'], 28)

    def test_verify_readback_and_description(self):
        for language in ('EN', 'IT'):
            data, charmap, (after, receipt) = self.installed(language)
            check = stage.verify(data, after, receipt, charmap=charmap)
            self.assertIn(check['overlay_changed_bytes'], range(1, 7))  # within the 6-byte seam
            self.assertTrue(check['arm9_changed_only_in_slot'])

    def test_refusals(self):
        data, charmap = self.inputs('EN')
        _, _, (after, _) = self.installed('EN')
        wrong = dict(self.slot(data), preimage_sha256='0' * 64)
        with self.assertRaisesRegex(ValueError, 'slot preimage'):
            stage.apply(data, 'EN', Path(self.work.name), slot=wrong, charmap=charmap)
        with self.assertRaises(ValueError):  # seam already patched
            stage.apply(after, 'EN', Path(self.work.name), slot=self.slot(after), charmap=charmap)
        small = dict(self.slot(data), bytes=16)
        at = stage._arm9_locate(stage._arm9_map(data), small["start"], 16)
        small['preimage_sha256'] = hashlib.sha256(data[at:at + 16]).hexdigest()
        with self.assertRaisesRegex(ValueError, 'exceeds the assigned slot'):
            stage.apply(data, 'EN', Path(self.work.name), slot=small, charmap=charmap)

    def test_verify_rejects_extra_change(self):
        data, charmap, (after, receipt) = self.installed('IT')
        segments = stage._arm9_map(after)
        start, size = reserved_slot()
        for address in (start + size, start - 1, 0x02000800):
            at = stage._arm9_locate(segments, address, 1)
            tampered = bytearray(after)
            tampered[at] ^= 0xFF
            with self.assertRaises(ValueError):
                stage.verify(data, bytes(tampered), receipt, charmap=charmap)
        tail = bytearray(after)
        at = stage._arm9_locate(segments, start, size) + size - 1
        tail[at] ^= 0x01
        with self.assertRaises(ValueError):
            stage.verify(data, bytes(tail), receipt)

    def test_reserved_slot_holds_payload_and_untouched_tail(self):
        start, size = reserved_slot()
        self.assertEqual((start % 4, size >= 28), (0, True))
        for language in ('EN', 'IT'):
            data, _, (after, receipt) = self.installed(language)
            at = stage._arm9_locate(stage._arm9_map(data), start, size)
            self.assertEqual(receipt['slot']['start'], start)
            self.assertEqual(hashlib.sha256(after[at:at + 28]).hexdigest(), stage.PAYLOAD_SHA256)
            self.assertEqual(after[at + 28:at + size], data[at + 28:at + size], 'slot tail preserved')

    def test_verify_rejects_noncanonical_overlay_streams(self):
        """Same decoded image, different stream: refused by both readers."""
        for language in ('EN', 'IT'):
            data, charmap, (after, receipt) = self.installed(language)
            for name, forged in forgeries(data, after).items():
                with self.subTest(language=language, forgery=name, path='full'):
                    with self.assertRaises(ValueError):
                        stage.verify(data, forged, receipt, charmap=charmap)

    def test_verify_code_rejects_noncanonical_overlay_streams(self):
        """Even with a receipt rewritten to the forged hash, the stream itself is refused."""
        for language in ('EN', 'IT'):
            data, _ = self.inputs(language)
            code, code_receipt = self.code(language)
            stage.verify_code(data, code, code_receipt)
            for name, forged in forgeries(data, code).items():
                with self.subTest(language=language, forgery=name, path='code'):
                    with self.assertRaises(ValueError):
                        stage.verify_code(data, forged, code_receipt)
                    rewritten = dict(code_receipt, output_sha256=hashlib.sha256(forged).hexdigest())
                    with self.assertRaises(ValueError) as caught:
                        stage.verify_code(data, forged, rewritten)
                    self.assertNotIn('receipt', str(caught.exception))

    def code(self, language):
        data, _ = self.inputs(language)
        key = ('code', language)
        if key not in _CACHE:
            _CACHE[key] = stage.apply_code(data, language, Path(self.work.name), slot=self.slot(data))
        return _CACHE[key]

    def test_code_only_path_is_in_place_and_leaves_messages_untouched(self):
        import ndspy.rom
        for language in ('EN', 'IT'):
            data, _ = self.inputs(language)
            after, receipt = self.code(language)
            self.assertEqual(len(after), len(data), 'code stage must not append')
            self.assertEqual(receipt['output_sha256'], hashlib.sha256(after).hexdigest())
            stage.verify_code(data, after, receipt)
            a, b = ndspy.rom.NintendoDSRom(data), ndspy.rom.NintendoDSRom(after)
            self.assertEqual(a.getFileByName('a/0/2/7'), b.getFileByName('a/0/2/7'))
            full, _ = self.installed(language)[2]
            self.assertEqual(bench.overlay_image(after), bench.overlay_image(full))
            new = bench.Bench(after, bench.overlay_image(after))
            case = {'abilities': {0: 51}, 'eva': {1: 12}, 'accuracy': 100}
            self.assertEqual(new.enumerate(case)['hits'], 100, language)
            with self.assertRaises(ValueError):
                stage.verify_code(data, after, dict(receipt, output_sha256='0' * 64))

    def test_composes_with_ai_scoring_in_either_order(self):
        try:
            from sgp131 import ai_scoring
        except ImportError as exc:  # explicit dependency, not a silent pass
            self.fail('ai_scoring stage missing: %r' % exc)
        for language in ('EN', 'IT'):
            data, charmap = self.inputs(language)
            slot = self.slot(data)
            first, _ = ai_scoring.apply(data, language)
            a, receipt_a = stage.apply(first, language, Path(self.work.name), slot=slot, charmap=charmap)
            stage.verify(first, a, receipt_a, charmap=charmap)
            _, _, (second, _) = self.installed(language)
            b, receipt_b = ai_scoring.apply(second, language)
            ai_scoring.verify(second, b, receipt_b)
            image_a, image_b = bench.overlay_image(a), bench.overlay_image(b)
            self.assertEqual(image_a, image_b, language + ' overlay 12 composition order')
            self.assertEqual(a, b, language + ' composed ROM differs by order')


if __name__ == '__main__':
    unittest.main()
