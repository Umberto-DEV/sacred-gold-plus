import sys, unittest, struct
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
try:
    from sgp13.guide import build_content, validate_content
except ImportError:
    build_content = validate_content = None

class ContentTests(unittest.TestCase):
    def build(self, pages=None, title='One'):
        self.assertTrue(callable(build_content), 'Guide compiler is missing')
        return build_content([dict(id=1,title='Category',entries=[dict(id=9,title=title,pages=pages or [['First'],['Second']])])], lambda s: [ord(c) for c in s]+[65535], lambda s: len(s)*6)
    def test_valid_binary_has_independently_readable_offsets(self):
        b=self.build()
        self.assertEqual(b[:4],b'SGG1')
        self.assertEqual(struct.unpack_from('<I',b,4)[0],len(b))
        self.assertEqual(struct.unpack_from('<HH',b,8),(1,1))
        self.assertEqual(validate_content(b)['entries'],1)
    def test_page_overflow_refused(self):
        self.assertTrue(callable(build_content),'Guide compiler is missing')
        with self.assertRaisesRegex(ValueError,'lines'): self.build([['x']*8])
    def test_measured_width_overflow_refused(self):
        self.assertTrue(callable(build_content),'Guide compiler is missing')
        with self.assertRaisesRegex(ValueError,'width'): self.build(title='x'*35)
    def test_detail_text_preserves_eight_pixel_inner_margins(self):
        self.build([['x'*34]])  # 204px fits between the inner margins.
        with self.assertRaisesRegex(ValueError,'width'): self.build([['x'*35]])
    def test_bad_page_offset_refused(self):
        b=bytearray(self.build()); struct.pack_into('<I',b,36,0xfffffff0)
        with self.assertRaises(ValueError): validate_content(b)
    def test_reference_resolves_or_is_refused(self):
        self.assertTrue(callable(build_content),'Guide compiler is missing')
        with self.assertRaises(ValueError): self.build([{'lines':['See item.'],'reference':500}])
        b=self.build([{'lines':['Same entry.'],'reference':9}])
        self.assertEqual(validate_content(b)['entries'],1)
    def test_empty_category_refused(self):
        self.assertTrue(callable(build_content),'Guide compiler is missing')
        with self.assertRaises(ValueError): build_content([dict(id=1,title='Category',entries=[])],lambda s:[1,65535],lambda s:10)
    def test_fourth_training_category_roundtrips_and_excess_is_rejected(self):
        categories=[dict(id=i,title='Category',entries=[dict(id=4000+i,title='Entry',pages=[['Help']])]) for i in range(1,5)]
        encode=lambda s:[ord(c) for c in s]+[65535]
        blob=build_content(categories,encode,lambda s:len(s)*6)
        self.assertEqual(validate_content(blob)['categories'],4)
        self.assertEqual(struct.unpack_from('<H',blob,12+3*12)[0],4)
        categories.append(dict(id=5,title='Extra',entries=[dict(id=4005,title='Extra',pages=[['Help']])]))
        with self.assertRaises(ValueError): build_content(categories,encode,lambda s:len(s)*6)
if __name__=='__main__': unittest.main()
