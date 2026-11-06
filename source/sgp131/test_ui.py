"""ROM-free contracts on the observed host; frozen production proof is test_ui_rom.

The explicit test-only identity seam below grants no production assurance.
It never changes source/library pins, product code, or payload assertions.
"""
from contextlib import contextmanager, ExitStack
import json
from pathlib import Path
import tempfile
import sys
import time
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from . import ui, ui_compile, ui_verify

CONFIG = dict(schema=1, kind='test-candidate', scene_work_calls=4,
              scene_glyph_budget=8, scene_last_start_line=240)


@contextmanager
def nonproduction_host_compiler_contract(*, compiler=False):
    """Inject fixed observed host identities for this test, restoring on exit.

    Python-only mode starts no compiler, including version queries. Compiler
    mode still uses the real bounded process runner and all production checks;
    only expected executable identities are test dependencies. No public API,
    configuration, or environment variable enables this seam in production.
    """
    identities = dict(PYTHON_VERSION=sys.version.split()[0],
                      PYTHON_EXECUTABLE_SHA256=ui_compile.sha(Path(sys.executable).resolve().read_bytes()))
    original_toolchain = ui_compile._toolchain
    if compiler:
        executable = ui_compile.compiler_path(ui_compile.COMPILER_SHA256)
        ui_compile.require(executable is not None, 'clang unavailable for nonproduction contract')
        with tempfile.TemporaryDirectory(prefix='ui-test-identity-') as tmp:
            version = ui_compile._run([executable, '--version'], Path(tmp), set())
        identities.update(COMPILER_VERSION=version.splitlines()[0],
                          COMPILER_SHA256=ui_compile.sha(Path(executable).resolve().read_bytes()))

    def labeled_toolchain(directory):
        executable, receipt = original_toolchain(directory)
        return executable, {**receipt, 'assurance': 'nonproduction-host-compiler-contract'}

    with ExitStack() as stack:
        for name, value in identities.items():
            stack.enter_context(patch.object(ui_compile, name, value))
        if compiler:
            stack.enter_context(patch.object(ui_compile, '_toolchain', labeled_toolchain))
        yield


class UiTests(unittest.TestCase):
    def test_configuration_is_explicit_and_rejects_boolean_or_extra_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / 'ui-candidate.json'
            with self.assertRaises(ValueError):
                ui_compile.read_config(Path(tmp))
            for value in ({**CONFIG, 'scene_work_calls': True},
                          {**CONFIG, 'scene_glyph_budget': 9},
                          {**CONFIG, 'scene_last_start_line': 262},
                          {**CONFIG, 'retired': True},
                          {k: v for k, v in CONFIG.items() if k != 'scene_last_start_line'}):
                p.write_text(json.dumps(value))
                with self.assertRaises(ValueError):
                    ui_compile.read_config(Path(tmp))
            p.write_text(json.dumps(CONFIG))
            self.assertEqual(ui_compile.read_config(Path(tmp)), CONFIG)

    def test_unknown_preimage_cannot_trigger_compilation(self):
        with patch.object(ui_compile, 'compile_payloads', side_effect=AssertionError('compiled')):
            with self.assertRaises(ValueError):
                ui.install(b'foreign', 'EN', Path('missing'), Path('missing'))
            with self.assertRaises(ValueError):
                ui_verify.verify(b'foreign', b'foreign', 'EN', Path('missing'), Path('missing'), {})

    def test_bounded_writer_rejects_overlap_and_guard_borrowing(self):
        with self.assertRaises(ValueError):
            ui._bounded_image(b'12345', 4)
        self.assertEqual(ui._bounded_image(b'12', 4), b'12\0\0')
        with self.assertRaises(ValueError):
            ui._disjoint([(4, 8), (7, 9)])

    def test_real_compiler_caps_and_exact_cross_component_symbols(self):
        with nonproduction_host_compiler_contract(compiler=True), tempfile.TemporaryDirectory() as tmp:
            compiled = ui_compile.compile_payloads(CONFIG, Path(tmp))
            for name, cap in [('bridge', 12272), ('physical', 1024), ('fieldbook', 3072),
                              ('training', 1536), ('dynamic54', 65536)]:
                self.assertLessEqual(len(compiled[name]['data']), cap)
            scene, tail = compiled['scene'], compiled['shiny']
            self.assertEqual(scene['receipt']['toolchain']['assurance'], 'nonproduction-host-compiler-contract')
            self.assertEqual(tail['base'], 0x021E5900 + (len(scene['data']) + 3 & ~3))
            self.assertEqual(compiled['dynamic54']['data'][tail['base'] - 0x021E5900:][:len(tail['data'])], tail['data'])
            self.assertEqual(tail['defines']['SGP_SETTINGS_UI_FINAL_CHECK'], scene['symbols']['settings_final_check'])
            self.assertEqual(scene['defines']['SGP_UI_SCENE_PHYSICAL_CONSUME'], compiled['physical']['symbols']['physical_consume'])
            self.assertEqual(list(Path(tmp).iterdir()), [])

    def test_actual_compiler_rejects_capacity_before_returning_bundle(self):
        with nonproduction_host_compiler_contract(compiler=True), tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, 'capacity overflow'):
                ui_compile._compile(Path(tmp), 'too-small', ['ui-native/fieldbook.c'],
                                    0x023D4000, 1, {})

    def test_library_drift_is_not_a_new_trusted_toolchain(self):
        with nonproduction_host_compiler_contract(), \
             patch.object(ui_compile, 'LIBRARY_PINS', {'ndspy.codeCompression': '0' * 64}):
            with self.assertRaisesRegex(ValueError, 'library source drift'):
                ui_compile.check_sources()

    def test_child_file_limit_is_exact_and_success_removes_diagnostics(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = ui_compile._run([sys.executable, '-I', '-S', '-c',
                'import resource; print(resource.getrlimit(resource.RLIMIT_FSIZE))'], Path(tmp), set())
            self.assertEqual(result.strip(), '(4194304, 4194304)')
            self.assertEqual(list(Path(tmp).iterdir()), [])

    def test_timeout_diagnostic_overflow_and_foreign_outputs_clean_up(self):
        cases = [('import time; time.sleep(10)', 'timeout'),
                 ('import os; os.write(1, b"x" * 70000)', 'diagnostic'),
                 ('from pathlib import Path; Path("foreign").write_text("x")', 'inventory'),
                 ('from pathlib import Path; Path("allowed.o").write_bytes(b"x" * 5000000)', 'compiler')]
        for body, reason in cases:
            with self.subTest(reason=reason), tempfile.TemporaryDirectory() as tmp:
                work=Path(tmp)
                with tempfile.TemporaryDirectory(dir=work) as child:
                    with self.assertRaises(ValueError):
                        ui_compile._run([sys.executable, '-I', '-S', '-c', body], Path(child),
                                        {'allowed.o'}, timeout=0.2 if reason=='timeout' else 5)
                    self.assertFalse((Path(child)/'diagnostics.txt').exists())
                    self.assertTrue(all(p.stat().st_size <= 4194304 for p in Path(child).iterdir()))
                self.assertEqual(list(work.iterdir()), [])

    def test_timeout_kills_descendant_in_same_process_group(self):
        child = 'import time; time.sleep(0.4); open("late", "w").write("escaped")'
        body = 'import subprocess,sys,time; subprocess.Popen([sys.executable,"-I","-S","-c",' + repr(child) + ']); time.sleep(10)'
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, 'timeout'):
                ui_compile._run([sys.executable, '-I', '-S', '-c', body], Path(tmp), set(), timeout=0.15)
            time.sleep(0.6)
            self.assertEqual(list(Path(tmp).iterdir()), [])

    def test_transient_disk_floor_refuses_before_any_compiler(self):
        floor, transient = 10 * 1024**3, 25 * 4 * 1024**2
        for free in (floor + 16 * 1024**2, floor + transient - 1):
            with nonproduction_host_compiler_contract(), self.subTest(free=free), tempfile.TemporaryDirectory() as tmp:
                with patch.object(ui_compile.shutil, 'disk_usage', return_value=SimpleNamespace(free=free)), \
                     patch.object(ui_compile, '_compile', side_effect=AssertionError('compiler started')) as compiler, \
                     patch.object(ui_compile, '_run', side_effect=AssertionError('compiler/version started')) as process:
                    with self.assertRaisesRegex(ValueError, 'disk budget'):
                        ui_compile.compile_payloads(CONFIG, Path(tmp))
                    compiler.assert_not_called()
                    process.assert_not_called()
                self.assertEqual(list(Path(tmp).iterdir()), [])

    def test_transient_disk_floor_admits_exact_conservative_boundary(self):
        class CompilerStarted(Exception):
            pass
        with nonproduction_host_compiler_contract(), tempfile.TemporaryDirectory() as tmp:
            free = 10 * 1024**3 + 25 * 4 * 1024**2
            with patch.object(ui_compile.shutil, 'disk_usage', return_value=SimpleNamespace(free=free)), \
                 patch.object(ui_compile, '_compile', side_effect=CompilerStarted) as compiler:
                with self.assertRaises(CompilerStarted):
                    ui_compile.compile_payloads(CONFIG, Path(tmp))
                self.assertEqual(compiler.call_count, 1)
            self.assertEqual(list(Path(tmp).iterdir()), [])

    def test_dependency_stdout_avoids_observed_atomic_temporary(self):
        original = ui_compile._run
        observed = []
        def run(command, directory, allowed, **kwargs):
            if '-MMD' in command:
                destination = command[command.index('-MF') + 1]
                observed.append(destination)
                if destination != '-':
                    # Deterministically hold root's actual dependency temporary
                    # across several inventory polls for the old invocation.
                    body = ('from pathlib import Path; import time; '
                            'Path("scene-1afc6dd5.d.tmp").write_text("dependency"); '
                            'time.sleep(0.2)')
                    original([sys.executable, '-I', '-S', '-c', body], directory, allowed)
                self.assertNotIn('scene.d', allowed)
                result = original(command, directory, allowed, **kwargs)
                self.assertIn('scene.c', result)
                self.assertFalse((directory/'scene.d').exists())
                return result
            return original(command, directory, allowed, **kwargs)
        with nonproduction_host_compiler_contract(compiler=True), \
             tempfile.TemporaryDirectory() as tmp, patch.object(ui_compile, '_run', run):
            directory = Path(tmp)
            part = ui_compile._compile(directory, 'scene', ['ui-native/fieldbook.c'], 0x023D4000, 3072, {})
            self.assertEqual(observed, ['-'])
            self.assertIn('fieldbook_create', part['symbols'])
            self.assertIn('fieldbook.h', (directory/'scene.d').read_text())
            self.assertEqual({p.name for p in directory.iterdir()}, {'scene.c','scene.o','scene.d','scene.su'})

    def test_dependency_temporaries_unknown_outputs_and_links_still_refuse(self):
        cases = [
            'from pathlib import Path; Path("scene-1afc6dd5.d.tmp").write_text("x")',
            'from pathlib import Path; Path("first.tmp").write_text("x"); Path("second.tmp").write_text("x")',
            'from pathlib import Path; Path("safe").write_text("x"); Path("allowed.o").symlink_to("safe")',
        ]
        for body in cases:
            with self.subTest(body=body), tempfile.TemporaryDirectory() as work:
                with tempfile.TemporaryDirectory(dir=work) as tmp:
                    with self.assertRaisesRegex(ValueError, 'inventory'):
                        ui_compile._run([sys.executable,'-I','-S','-c',body], Path(tmp), {'safe','allowed.o'})
                    self.assertFalse((Path(tmp)/'diagnostics.txt').exists())
                self.assertEqual(list(Path(work).iterdir()), [])

    def test_compiler_diagnostics_cannot_become_dependency_text(self):
        original = ui_compile._run
        def noisy(command, directory, allowed, **kwargs):
            result = original(command, directory, allowed, **kwargs)
            return result + 'unexpected compiler diagnostic\n' if '-MMD' in command else result
        with nonproduction_host_compiler_contract(compiler=True), \
             tempfile.TemporaryDirectory() as tmp, patch.object(ui_compile, '_run', noisy):
            directory = Path(tmp)
            with self.assertRaisesRegex(ValueError, 'dependency output grammar'):
                ui_compile._compile(directory, 'scene', ['ui-native/fieldbook.c'], 0x023D4000, 3072, {})
            self.assertFalse((directory/'scene.d').exists())
            self.assertFalse((directory/'diagnostics.txt').exists())

    def test_excess_active_file_count_refuses_even_known_names(self):
        body = 'from pathlib import Path; [Path("f"+str(i)).write_text("x") for i in range(25)]'
        with tempfile.TemporaryDirectory() as work:
            with tempfile.TemporaryDirectory(dir=work) as tmp:
                with self.assertRaisesRegex(ValueError, 'output count'):
                    ui_compile._run([sys.executable,'-I','-S','-c',body], Path(tmp),
                                    {'f'+str(i) for i in range(25)})
            self.assertEqual(list(Path(work).iterdir()), [])

    def test_source_drift_fails_before_compile(self):
        with nonproduction_host_compiler_contract(), \
             patch.object(ui_compile, 'SOURCE_PINS', {'nonexistent.c': '0' * 64}):
            with self.assertRaisesRegex(ValueError, 'missing pinned source: nonexistent.c'):
                ui_compile.check_sources()

    def test_changed_source_during_compile_rejects_result(self):
        original = ui_compile.check_sources
        calls = []
        def check():
            calls.append(1)
            if len(calls) > 1:
                raise ValueError('source changed during compile')
            return original()
        with nonproduction_host_compiler_contract(compiler=True), \
             tempfile.TemporaryDirectory() as tmp, patch.object(ui_compile, 'check_sources', side_effect=check):
            with self.assertRaisesRegex(ValueError, 'source changed'):
                ui_compile.compile_payloads(CONFIG, Path(tmp))
            self.assertEqual(list(Path(tmp).iterdir()), [])

    def test_production_refuses_python_version_before_compilation(self):
        with tempfile.TemporaryDirectory() as tmp, \
             patch.object(ui_compile.sys, 'version', '0.0.0 controlled wrong Python'), \
             patch.object(ui_compile, '_run', side_effect=AssertionError('compiler started')) as process:
            with self.assertRaisesRegex(ValueError, '^Python toolchain drift$'):
                ui_compile.compile_payloads(CONFIG, Path(tmp))
            process.assert_not_called()
            self.assertEqual(list(Path(tmp).iterdir()), [])

    def test_production_refuses_python_binary_before_compilation(self):
        with tempfile.TemporaryDirectory() as tmp:
            executable = Path(tmp)/'wrong-python'
            executable.write_bytes(b'controlled wrong Python executable')
            with patch.object(ui_compile.sys, 'version', ui_compile.PYTHON_VERSION), \
                 patch.object(ui_compile.sys, 'executable', str(executable)), \
                 patch.object(ui_compile, '_run', side_effect=AssertionError('compiler started')) as process:
                with self.assertRaisesRegex(ValueError, '^Python executable drift$'):
                    ui_compile.compile_payloads(CONFIG, Path(tmp))
                process.assert_not_called()
            self.assertEqual(list(Path(tmp).iterdir()), [executable])

    def test_production_refuses_clang_version(self):
        with tempfile.TemporaryDirectory() as tmp, \
             patch.object(ui_compile, '_run', return_value='controlled wrong clang version\n'):
            with self.assertRaisesRegex(ValueError, '^compiler version drift$'):
                ui_compile._toolchain(Path(tmp))

    def test_production_refuses_clang_binary(self):
        with tempfile.TemporaryDirectory() as tmp:
            executable = Path(tmp)/'wrong-clang'
            executable.write_bytes(b'controlled wrong clang executable')
            with patch.object(ui_compile.shutil, 'which', return_value=str(executable)), \
                 patch.object(ui_compile, '_run', return_value=ui_compile.COMPILER_VERSION+'\n'):
                with self.assertRaisesRegex(ValueError, '^compiler binary drift$'):
                    ui_compile._toolchain(Path(tmp))

    def test_wrong_compiler_is_rejected_before_its_version_probe_executes(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            marker = directory / 'EXECUTED'
            executable = directory / 'clang'
            executable.write_text('#!/bin/sh\ntouch "' + str(marker) + '"\n' +
                                  'echo "' + ui_compile.COMPILER_VERSION + '"\n')
            executable.chmod(0o700)
            with patch.object(ui_compile.shutil, 'which', return_value=str(executable)):
                with self.assertRaisesRegex(ValueError, 'compiler binary drift'):
                    ui_compile._toolchain(directory)
            self.assertFalse(marker.exists(), 'untrusted version probe executed')

    def test_compiler_rejects_writable_matching_executable_and_discards_injection(self):
        from sgp13 import compiler
        with tempfile.TemporaryDirectory() as tmp:
            fake = Path(tmp) / 'clang'
            fake.write_bytes(b'controlled compiler fixture')
            fake.chmod(0o700)
            digest = ui_compile.sha(fake.read_bytes())
            with patch.object(compiler.shutil, 'which', return_value=str(fake)):
                with self.assertRaisesRegex(ValueError, 'protected by root'):
                    compiler.compiler_path(digest)
        with patch.dict(compiler.os.environ, {'CCC_OVERRIDE_OPTIONS': '+-load',
                                             'DYLD_INSERT_LIBRARIES': '/tmp/untrusted',
                                             'CLANG_CONFIG_PATH': '/tmp/untrusted'}):
            environment = compiler.compiler_environment()
            self.assertFalse(set(environment) & {'CCC_OVERRIDE_OPTIONS', 'DYLD_INSERT_LIBRARIES',
                                                 'CLANG_CONFIG_PATH'})
            self.assertEqual(environment['CLANG_NO_DEFAULT_CONFIG'], '1')

    def test_all_five_native_stages_reject_wrong_compiler_without_execution(self):
        from sgp131 import modern_abilities, controls, portable, rematches
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            fake = directory / 'clang'
            marker = directory / 'EXECUTED'
            fake.write_text('#!/bin/sh\ntouch "' + str(marker) + '"\n')
            fake.chmod(0o700)
            operations = [lambda: ui_compile._toolchain(directory),
                          lambda: modern_abilities.compile_native(directory, 0x023D0000),
                          lambda: portable.compile_native(directory, 0x023D0000),
                          lambda: rematches._compiler(),
                          lambda: controls.compile_payload(directory, 0x023D0000, 'EN', None,
                              dict(bgId=controls.SUB_BG, left=1, top=18, width=16,
                                   height=2, palette=13, baseTile=955), codes=[65535])]
            with patch.object(ui_compile.shutil, 'which', return_value=str(fake)):
                for index, operation in enumerate(operations):
                    with self.subTest(stage=index), self.assertRaisesRegex(ValueError, 'compiler binary drift'):
                        operation()
            self.assertFalse(marker.exists())

    def test_real_compiler_discards_plugin_override_and_rejects_extended_acl(self):
        from sgp13 import compiler
        import subprocess
        with patch.dict(compiler.os.environ, {
                'CCC_OVERRIDE_OPTIONS': '+-Xclang +-load +-Xclang +/tmp/untrusted-plugin.so'}):
            result = compiler.run_compiler(['-###', '--target=armv5te-none-eabi',
                                           '-x', 'c', '-fsyntax-only', '/dev/null'],
                                          capture_output=True, text=True, check=True)
            self.assertNotIn('untrusted-plugin', result.stderr)
        with tempfile.TemporaryDirectory() as tmp:
            candidate = Path(tmp) / 'acl-fixture'
            candidate.write_text('fixture')
            compiler._reject_acl(candidate)
            subprocess.run(['chmod', '+a', 'everyone allow read', str(candidate)], check=True)
            with self.assertRaisesRegex(ValueError, 'extended ACL'):
                compiler._reject_acl(candidate)

    def test_nonproduction_context_restores_every_identity_after_exception(self):
        names = ('PYTHON_VERSION', 'PYTHON_EXECUTABLE_SHA256', 'COMPILER_VERSION',
                 'COMPILER_SHA256', '_toolchain', 'SOURCE_PINS', 'LIBRARY_PINS')
        prior = {name: getattr(ui_compile, name) for name in names}
        with self.assertRaisesRegex(RuntimeError, 'controlled exit'):
            with nonproduction_host_compiler_contract(compiler=True):
                raise RuntimeError('controlled exit')
        self.assertEqual({name: getattr(ui_compile, name) for name in names}, prior)

    def test_nonproduction_context_reaches_intended_guards_with_ci_python_identity(self):
        # Controlled observation, not a claim to run under the actual CI Python.
        with patch.object(ui_compile.sys, 'version', '3.13.15 controlled CI identity'):
            self.test_library_drift_is_not_a_new_trusted_toolchain()
            self.test_transient_disk_floor_refuses_before_any_compiler()
