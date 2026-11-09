"""Font recovery checks use a tiny, generated Bitstream Vera subset."""
from io import BytesIO
from pathlib import Path
import hashlib
import tempfile
import unittest

import reportlab
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFontFile
from pypdf import PdfWriter
from pypdf.generic import (ArrayObject, DictionaryObject, DecodedStreamObject,
                          NameObject, NumberObject)

try:
    from distribution import legacy_style
except ImportError:
    legacy_style = None


def fixture_pdf(*, unicode_map=False):
    """PDF character 1 means A, 2 means B, 3 means space; not Unicode 1/2/3."""
    font_path = Path(reportlab.__file__).parent / 'fonts' / 'Vera.ttf'
    font = TTFontFile(str(font_path))
    subset = font.makeSubset([0, 65, 66, 32])
    writer = PdfWriter()
    stream = DecodedStreamObject()
    stream.set_data(subset)
    descriptor = DictionaryObject({NameObject('/FontFile2'): writer._add_object(stream)})
    encoding = DictionaryObject({NameObject('/BaseEncoding'): NameObject('/WinAnsiEncoding'),
                                 NameObject('/Differences'): ArrayObject([
                                     NumberObject(1), NameObject('/g99' if unicode_map else '/A'),
                                     NameObject('/g98' if unicode_map else '/B'), NameObject('/space')])})
    font_object = DictionaryObject({NameObject('/Type'): NameObject('/Font'),
        NameObject('/Subtype'): NameObject('/TrueType'),
        NameObject('/BaseFont'): NameObject('/TESTAB+FixtureBody'),
        NameObject('/FontDescriptor'): writer._add_object(descriptor),
        NameObject('/Encoding'): encoding, NameObject('/FirstChar'): NumberObject(1),
        NameObject('/LastChar'): NumberObject(3),
        NameObject('/Widths'): ArrayObject([NumberObject(684), NumberObject(686), NumberObject(318)])})
    if unicode_map:
        cmap = DecodedStreamObject()
        cmap.set_data(b'2 beginbfrange\n<01><02><0041>\n<03><03><0020>\nendbfrange')
        font_object[NameObject('/ToUnicode')] = writer._add_object(cmap)
    page = writer.add_blank_page(width=200, height=200)
    page[NameObject('/Resources')] = DictionaryObject({NameObject('/Font'): DictionaryObject({
        NameObject('/F1'): writer._add_object(font_object)})})
    output = BytesIO()
    writer.write(output)
    return output.getvalue()


class LegacyStyleTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(legacy_style, 'legacy font recovery module is missing')

    def test_pdf_encoding_recovers_real_letters_and_preserves_metrics(self):
        # A missing PDF-code-to-Unicode conversion would render control characters.
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'original.pdf'
            path.write_bytes(fixture_pdf())
            face = legacy_style.load_face(path, 'FixtureBody')
            face.require('A B')
            name = face.register()
            self.assertAlmostEqual(pdfmetrics.stringWidth('AB', name, 10), 13.701171875)
            self.assertEqual(set(face.codepoints), {32, 65, 66})

    def test_to_unicode_overrides_uninformative_subset_glyph_names(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'original.pdf'
            path.write_bytes(fixture_pdf(unicode_map=True))
            face = legacy_style.load_face(path, 'FixtureBody')
            face.require('AB')
            self.assertEqual(set(face.codepoints), {32, 65, 66})

    def test_missing_glyphs_and_wrong_original_are_refused(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'original.pdf'
            raw = fixture_pdf()
            path.write_bytes(raw)
            face = legacy_style.load_face(path, 'FixtureBody',
                                          expected_sha256=hashlib.sha256(raw).hexdigest())
            with self.assertRaisesRegex(ValueError, 'glyph'):
                face.require('C')
            with self.assertRaisesRegex(ValueError, 'identity'):
                legacy_style.load_face(path, 'FixtureBody', expected_sha256='0' * 64)
            with self.assertRaisesRegex(ValueError, 'font'):
                legacy_style.load_face(path, 'MissingFont')


if __name__ == '__main__':
    unittest.main()
