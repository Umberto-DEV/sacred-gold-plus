"""ROM-free falsifiers for reference metadata triage; no production admission."""
import copy
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest

TOOL = Path(__file__).resolve().parents[1] / 'tools/confronta_metadata_pret.py'
spec = importlib.util.spec_from_file_location('pret_metadata', TOOL)
tool = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tool)


class MetadataTests(unittest.TestCase):
    def setUp(self):
        self.old = {'commands': [{'name': 'Unknown', 'args': [1]},
                                 {'name': 'End', 'args': [], 'is_abs_branch': True}],
                    'argtypes': {'var': 2}}

    def test_labels_only_does_not_promote_to_binary_proof(self):
        new = copy.deepcopy(self.old)
        new['commands'][0]['name'] = 'Known'
        result = tool.compare(self.old, new)
        self.assertEqual(result['status'], 'labels-only')
        self.assertEqual(result['renames'], [{'id': 0, 'before': 'Unknown', 'after': 'Known'}])
        self.assertFalse(result['production_admission'])
        self.assertFalse(result['rom_execution_proved'])

    def test_every_non_name_field_is_a_counterexample(self):
        for key, value in [('args', [2]), ('is_abs_branch', True),
                           ('switch_arg', 0), ('cases', {'1': [4]}), ('future_field', 1)]:
            with self.subTest(key=key):
                new = copy.deepcopy(self.old)
                new['commands'][0][key] = value
                self.assertEqual(tool.compare(self.old, new)['status'], 'incompatible')

    def test_argtypes_top_level_fields_count_and_order(self):
        mutations = []
        for change in ('argtypes', 'new_field', 'count', 'order'):
            new = copy.deepcopy(self.old)
            if change == 'argtypes':
                new['argtypes']['var'] = 4
            elif change == 'new_field':
                new['future_table'] = True
            elif change == 'count':
                new['commands'].pop()
            else:
                new['commands'].reverse()
            mutations.append(new)
        for new in mutations:
            self.assertEqual(tool.compare(self.old, new)['status'], 'incompatible')

    def test_identical_and_missing_names(self):
        self.assertEqual(tool.compare(self.old, copy.deepcopy(self.old))['status'], 'identical')
        for bad in ({}, {'commands': [{}]}, {'commands': [True]},
                    {'commands': [{'name': 1}]}, {'commands': 'x'}):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                tool.compare(self.old, bad)

    def test_duplicate_json_keys_are_not_silently_collapsed(self):
        with self.assertRaises(ValueError):
            tool.parse(b'{"commands": [], "commands": [{"name": "Other"}]}')

    def test_non_finite_and_over_budget_json_rejected(self):
        for raw in (b'{"commands": [], "unknown": NaN}', b' ' * (tool.MAX_BYTES + 1)):
            with self.subTest(size=len(raw)), self.assertRaises(ValueError):
                tool.parse(raw)

    def test_boolean_is_not_an_integer_argument_width(self):
        new = copy.deepcopy(self.old)
        new['commands'][0]['args'] = [True]
        self.assertEqual(tool.compare(self.old, new)['status'], 'incompatible')

    def test_cli_exit_codes_and_read_only_inputs(self):
        with tempfile.TemporaryDirectory() as directory:
            before, after = (Path(directory) / name for name in ('old.json', 'new.json'))
            raw = json.dumps(self.old).encode()
            before.write_bytes(raw)
            for content, expected in ((raw, 0), (b'{"commands": []}', 1), (b'{', 2)):
                with self.subTest(expected=expected):
                    after.write_bytes(content)
                    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                        code = tool.main(['--before', str(before), '--after', str(after)])
                    self.assertEqual(code, expected)
                    self.assertEqual(before.read_bytes(), raw)
                    self.assertEqual(after.read_bytes(), content)


if __name__ == '__main__':
    unittest.main()
