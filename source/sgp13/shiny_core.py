"""Compile the pure shiny core into its bounded resident Thumb compartment."""
import importlib.util
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
BASE = 0x023C8100
MAX_BYTES = 4096
ENTRIES = tuple('sgp_shiny_' + name for name in
                ('valid', 'denominator', 'select', 'complete', 'draw', 'transform'))


def compile_native(directory):
    """Return (blob, symbols); reject external dependencies and overflow."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    obj = directory / 'shiny-core.o'
    flags = ['--target=armv5te-none-eabi', '-mcpu=arm946e-s', '-mthumb',
             '-Oz', '-std=c99', '-ffreestanding', '-fno-builtin',
             '-fno-stack-protector', '-fno-jump-tables', '-fno-unwind-tables',
             '-fno-asynchronous-unwind-tables', '-Wall', '-Wextra', '-Werror']
    subprocess.run(['clang', *flags, '-c', str(ROOT / 'features/shiny/core.c'),
                    '-o', str(obj)], check=True, capture_output=True)
    spec = importlib.util.spec_from_file_location(
        'shiny_core_object_loader', ROOT / 'features/options/tools/carica_text.py')
    loader = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loader)
    blob, symbols = loader.load_text(obj.read_bytes(), BASE, ENTRIES)
    if len(blob) > MAX_BYTES:
        raise ValueError(f'shiny core compartment overflow: {len(blob)} > {MAX_BYTES} bytes')
    return blob, symbols
