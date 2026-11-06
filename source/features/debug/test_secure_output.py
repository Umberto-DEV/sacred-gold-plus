import ast
import os
from pathlib import Path
import stat
import tempfile
import unittest

from .secure_output import OutputRefused, PrivateDirectory, write_json_new


DEBUG = Path(__file__).resolve().parent
PRODUCERS = (
    'campo/avvio.py', 'campo/warp.py', 'campo/lotta_allenatore.py', 'campo/sonda.py',
    'campo/campagna_camera.py', 'campo/campagna_warp.py',
    'tools/warp.py', 'tools/leggi_campo.py', 'tools/bp_pokepic.py', 'tools/wp_demo.py',
    'tools/campagna_mappe.py', 'tools/ancore_warp.py', 'tools/verifica_gate.py',
)


class SecureDebugOutputTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='debug-output-')
        self.addCleanup(self.temp.cleanup)
        self.top = Path(self.temp.name).resolve()

    def test_private_no_replace_outputs_ignore_permissive_umask(self):
        root = self.top / 'run'
        previous = os.umask(0o022)
        try:
            with PrivateDirectory(root) as outputs:
                outputs.write_new('nested/result.bin', b'candidate')
        finally:
            os.umask(previous)
        self.assertEqual((root / 'result.bin').exists(), False)
        self.assertEqual((root / 'nested/result.bin').read_bytes(), b'candidate')
        self.assertEqual(root.stat().st_mode & 0o777, 0o700)
        self.assertEqual((root / 'nested').stat().st_mode & 0o777, 0o700)
        info = (root / 'nested/result.bin').stat()
        self.assertEqual(info.st_mode & 0o777, 0o600)
        self.assertEqual(info.st_nlink, 1)

    def test_links_and_existing_files_are_refused_without_touching_victim(self):
        root = self.top / 'run'
        victim = self.top / 'victim'
        victim.write_bytes(b'preserve')
        with PrivateDirectory(root) as outputs:
            (root / 'live').symlink_to(victim)
            (root / 'dangling').symlink_to(self.top / 'absent')
            os.link(victim, root / 'hard')
            (root / 'regular').write_bytes(b'existing')
            for name in ('live', 'dangling', 'hard', 'regular'):
                with self.subTest(name=name), self.assertRaises(FileExistsError):
                    outputs.write_new(name, b'bad')
        self.assertEqual(victim.read_bytes(), b'preserve')
        self.assertFalse((self.top / 'absent').exists())

    def test_held_directory_descriptor_defeats_parent_swap(self):
        root = self.top / 'run'
        outputs = PrivateDirectory(root)
        held = self.top / 'held'
        outside = self.top / 'outside'
        outside.mkdir(mode=0o700)
        root.rename(held)
        root.symlink_to(outside, target_is_directory=True)
        try:
            outputs.write_new('result', b'candidate')
        finally:
            outputs.close()
        self.assertEqual((held / 'result').read_bytes(), b'candidate')
        self.assertFalse((outside / 'result').exists())

    def test_json_and_relaxed_or_symlink_roots_fail_closed(self):
        reports = self.top / 'reports'
        reports.mkdir(mode=0o700)
        report = reports / 'report.json'
        write_json_new(report, {'ok': True})
        with self.assertRaises(FileExistsError):
            write_json_new(report, {'ok': False})
        reports.chmod(0o755)
        with self.assertRaises(OutputRefused):
            PrivateDirectory(reports)
        target = self.top / 'target'
        target.mkdir(mode=0o700)
        alias = self.top / 'alias'
        alias.symlink_to(target, target_is_directory=True)
        with self.assertRaises(OutputRefused):
            PrivateDirectory(alias)

    def test_all_runtime_wrappers_use_the_shared_no_replace_sink(self):
        for relative in PRODUCERS:
            path = DEBUG / relative
            source = path.read_text()
            tree = ast.parse(source)
            self.assertIn('secure_output import', source, relative)
            for node in ast.walk(tree):
                if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                        and node.func.id == 'open' and len(node.args) > 1
                        and isinstance(node.args[1], ast.Constant)
                        and 'w' in str(node.args[1].value)):
                    self.fail(f'{relative}:{node.lineno} retains a truncating open')
                if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                        and node.func.attr in ('write_text', 'write_bytes', 'makedirs',
                                               'copyfile', 'copy2')):
                    self.fail(f'{relative}:{node.lineno} retains an ordinary publication sink')


if __name__ == '__main__':
    unittest.main()
