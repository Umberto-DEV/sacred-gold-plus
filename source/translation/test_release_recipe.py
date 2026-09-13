import json
import tempfile
import unittest
from pathlib import Path

from release_recipe import load_recipe


class RecipeTests(unittest.TestCase):
    def test_split_bank_has_same_semantics_as_inline_recipe(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root/'messages-it').mkdir()
            rows = [{'bank': 3, 'message': 5, 'text': 'Example'}]
            (root/'messages-it/0003.json').write_text(json.dumps(rows))
            (root/'recipe.json').write_text(json.dumps({'language': 'it', 'message_files': ['messages-it/0003.json']}))
            self.assertEqual(load_recipe(root/'recipe.json'), {'language': 'it', 'messages': rows})

    def test_external_wrong_language_and_duplicate_paths_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for names in [['../private.json'], ['messages-en/0003.json'], ['messages-it/0003.json', 'messages-it/0003.json']]:
                (root/'messages-it').mkdir(exist_ok=True)
                (root/'messages-it/0003.json').write_text('[]')
                (root/'recipe.json').write_text(json.dumps({'language': 'it', 'message_files': names}))
                with self.assertRaises(ValueError):
                    load_recipe(root/'recipe.json')


if __name__ == '__main__':
    unittest.main()
