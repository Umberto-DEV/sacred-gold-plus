"""The same transaction must fit the freestanding resident ARM environment."""
import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class TransactionArm(unittest.TestCase):
    def test_no_runtime_or_data_dependencies(self):
        path = ROOT.parent / 'options/tools/carica_text.py'
        spec = importlib.util.spec_from_file_location('transaction_object', path)
        loader = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(loader)
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            unit = directory / 'transaction.c'
            unit.write_text(f'#include "{ROOT.parent / "training/sorgenti/core.c"}"\n'
                            f'#include "{ROOT / "transaction.c"}"\n')
            obj = directory / 'transaction.o'
            subprocess.run(['clang', '--target=armv5te-none-eabi', '-mcpu=arm946e-s',
                            '-mthumb', '-Os', '-ffreestanding', '-fno-builtin',
                            '-fno-stack-protector', '-fno-jump-tables', '-fno-unwind-tables',
                            '-fno-asynchronous-unwind-tables', '-Wall', '-Wextra', '-Werror',
                            '-c', str(unit), '-o', str(obj)], check=True, capture_output=True)
            blob, symbols = loader.load_text(obj.read_bytes(), 0x023D0100,
                                             ('sgp_training_transaction',))
            self.assertLess(len(blob), 0x2F00)
            self.assertTrue(symbols['sgp_training_transaction'] & 1)


if __name__ == '__main__':
    unittest.main()
