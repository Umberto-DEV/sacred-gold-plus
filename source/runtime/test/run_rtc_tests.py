"""Compile and execute the actual C++17 RTC tests without a ROM or core build."""
import os
from pathlib import Path
import shlex
import subprocess
import tempfile

with tempfile.TemporaryDirectory(prefix='hg-rtc-test-') as temporary:
    binary = Path(temporary) / 'rtc_config_test'
    subprocess.run([*shlex.split(os.environ.get('CXX', 'c++')), '-std=c++17',
                    '-Wall', '-Wextra', '-Werror',
                    str(Path(__file__).with_name('rtc_config_test.cpp')),
                    '-o', str(binary)], check=True, timeout=60)
    subprocess.run([str(binary)], check=True, timeout=10)
