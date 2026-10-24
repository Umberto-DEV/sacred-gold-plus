import hashlib
from pathlib import Path
import tempfile
import unittest
import zipfile
import pack

class PackageTests(unittest.TestCase):
    def test_original_document_corruption_is_rejected(self):
        with self.assertRaises(ValueError): pack.verify_bytes(b'bad', {'bytes':3,'sha256':'0'*64})
    def test_archives_are_reproducible_and_read_back(self):
        with tempfile.TemporaryDirectory() as temp:
            a,b=Path(temp)/'a.zip',Path(temp)/'b.zip'
            members={'guide.txt':b'guide','Patch/a.xdelta':b'patch'}
            pack.write_zip(a,members);pack.write_zip(b,members)
            self.assertEqual(a.read_bytes(),b.read_bytes())
            with zipfile.ZipFile(a) as z:self.assertEqual(set(z.namelist()),set(members))
    def test_existing_archive_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/'a.zip';p.write_bytes(b'keep')
            with self.assertRaises(FileExistsError):pack.write_zip(p,{'guide':b'text'})
            self.assertEqual(p.read_bytes(),b'keep')
    def test_all_previously_supported_inputs_and_124_are_present(self):
        ids={x['id'] for x in pack.config()['sources']}
        self.assertEqual(len(ids),21)
        self.assertTrue({'clean-us','clean-it','plus-1.01','plus-1.02','plus-1.03','plus-1.2.3-en','plus-1.2.3-it','plus-1.2.4-en','plus-1.2.4-it'}<=ids)
