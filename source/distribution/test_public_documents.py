"""Only individually reviewed, hash-pinned guide PDFs may enter public source."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location(
    'public_check', Path(__file__).resolve().parents[2] / '.github/check_public.py')
public_check = importlib.util.module_from_spec(spec)
spec.loader.exec_module(public_check)


class PublicDocumentTests(unittest.TestCase):
    def test_ascii_pdf_cannot_bypass_the_catalogue_through_text_decoding(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            (root / '.github').mkdir()
            (root / 'guides/current').mkdir(parents=True)
            name = 'guides/current/Unreviewed.pdf'
            (root / name).write_bytes(b'%PDF-1.4\nASCII-only unknown document\n%%EOF\n')
            (root / '.github/public-files.json').write_text(json.dumps([
                '.github/public-files.json', name]))
            with self.assertRaisesRegex(ValueError, 'reviewed|PDF|document'):
                public_check.check(root)

    def test_pdf_admission_requires_exact_reviewed_bytes_and_approved_directory(self):
        raw = b'%PDF-1.4\nreviewed synthetic document\n%%EOF\n'
        name = 'guides/current/Move-Changes-1.3.2-EN.pdf'
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'guides').mkdir()
            (root / 'guides/catalogue.json').write_text(json.dumps({
                'schema': 1, 'files': {name: {
                    'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}}}))
            admission = getattr(public_check, 'reviewed_guide_pdf', lambda *args: False)
            self.assertTrue(admission(root, name, raw))
            self.assertFalse(admission(root, name, raw + b'changed'))
            self.assertFalse(admission(root, 'guides/current/Unknown.pdf', raw))
            self.assertFalse(admission(root, 'source/unreviewed.pdf', raw))

    def test_a_pin_cannot_disguise_non_pdf_bytes(self):
        raw = b'private binary disguised as a document'
        name = 'guides/originals/Example.pdf'
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'guides').mkdir()
            (root / 'guides/catalogue.json').write_text(json.dumps({
                'schema': 1, 'files': {name: {
                    'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}}}))
            admission = getattr(public_check, 'reviewed_guide_pdf', lambda *args: False)
            self.assertFalse(admission(root, name, raw))


if __name__ == '__main__':
    unittest.main()
