"""Compile the production sources together exactly as a resident Thumb payload.

The existing object loader rejects undefined symbols, non-Thumb relocations,
external data and runtime/libc dependencies; its relocation test exercises the
actual generated machine object, not a source-string approximation.
"""
import importlib.util
import pathlib
import subprocess
import tempfile
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]

class ArmBuild(unittest.TestCase):
    def test_freestanding_thumb_has_no_external_symbols_or_data(self):
        loader_path=ROOT.parent/'options/tools/carica_text.py'
        spec=importlib.util.spec_from_file_location('training_object_reader',loader_path)
        loader=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(loader)
        with tempfile.TemporaryDirectory() as tmp:
            folder=pathlib.Path(tmp)
            unity=folder/'training.c'
            unity.write_text(''.join('#include "'+str(p)+'"\n' for p in sorted((ROOT/'sorgenti').glob('*.c'))))
            obj=folder/'training.o'
            subprocess.run(['clang','--target=armv5te-none-eabi','-mcpu=arm946e-s',
                            '-mthumb','-ffreestanding','-fno-builtin','-fno-stack-protector',
                            '-fno-jump-tables','-fno-unwind-tables','-fno-asynchronous-unwind-tables',
                            '-std=c99','-Os','-Wall','-Wextra','-Werror','-c',str(unity),'-o',str(obj)],
                           check=True,capture_output=True)
            try:
                text,symbols=loader.load_text(obj.read_bytes(),0x023d0000,
                    entries=('sgp_train_iv_preview','sgp_train_ev_delta','sgp_train_advance',
                             'sgp_train_project','sgp_train_decode','sgp_train_encode','sgp_train_select'))
            except ValueError as error:
                self.fail(str(error))
            self.assertGreater(len(text),0)
            self.assertTrue(all(symbols[n]&1 for n in symbols if n.startswith('sgp_train_') and '.' not in n))
