from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import textwrap
import unittest


RUNTIME = Path(__file__).resolve().parents[1]
PATCH_CORE = RUNTIME / "patch_core.py"
EXPECTED_REVISION = "906e9ebb27da8c6a715cd7abab4abfe8a8d29427"

ARM_PRISTINE = """\
#include "ARMJIT_Memory.h"
void first()
{
                // actually execute
                u32 icode = (CurInstr >> 6) & 0x3FF;
                ARMInterpreter::THUMBInstrTable[icode](this);
                // actually execute
                if (CheckCondition(CurInstr >> 28))
                    DoThing();
                else
                    AddCycles_C();
            }

            // TODO optimize this shit!!!
}
void second()
{
                // actually execute
                u32 icode = (CurInstr >> 6);
                ARMInterpreter::THUMBInstrTable[icode](this);
                // actually execute
                if (CheckCondition(CurInstr >> 28))
                    DoThing();
                else
                    AddCycles_C();
            }

            // TODO optimize this shit!!!
}
"""

NDS_PRISTINE = """\
#include "ARMJIT_Memory.h"
void NDS::MonitorARM9Jump(u32 addr)
{
}
"""


class PatchCoreCheckoutTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.source = self.root / "melonDS"
        (self.source / "src").mkdir(parents=True)
        (self.source / "src" / "ARM.cpp").write_text(ARM_PRISTINE)
        (self.source / "src" / "NDS.cpp").write_text(NDS_PRISTINE)
        (self.source / "CMakeLists.txt").write_text("add_library(core STATIC src/ARM.cpp)\n")

        self.pristine = self.root / "pristine"
        self.pristine.mkdir()
        (self.pristine / "ARM.cpp").write_text(ARM_PRISTINE)
        (self.pristine / "NDS.cpp").write_text(NDS_PRISTINE)
        (self.pristine / "CMakeLists.txt").write_text("add_library(core STATIC src/ARM.cpp)\n")

        fake_bin = self.root / "bin"
        fake_bin.mkdir()
        fake_git = fake_bin / "git"
        fake_git.write_text(textwrap.dedent(f"""\
            #!{sys.executable}
            import os
            from pathlib import Path
            import hashlib
            import sys

            args = sys.argv[1:]
            if args[-2:] == ["rev-parse", "HEAD"]:
                print("{EXPECTED_REVISION}")
            elif args[-2:] == ["rev-parse", "--show-toplevel"]:
                print(os.environ["FAKE_GIT_TOPLEVEL"])
            elif "ls-tree" in args:
                pristine = Path(os.environ["FAKE_GIT_PRISTINE"])
                records = []
                for name, fixture in [
                    ("CMakeLists.txt", "CMakeLists.txt"),
                    ("src/ARM.cpp", "ARM.cpp"),
                    ("src/NDS.cpp", "NDS.cpp"),
                ]:
                    data = (pristine / fixture).read_bytes()
                    oid = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\\0" + data).hexdigest()
                    records.append(f"100644 blob {{oid}}\\t{{name}}".encode())
                sys.stdout.buffer.write(b"\\0".join(records) + b"\\0")
            elif "cat-file" in args:
                wanted = args[-1]
                pristine = Path(os.environ["FAKE_GIT_PRISTINE"])
                for fixture in ["CMakeLists.txt", "ARM.cpp", "NDS.cpp"]:
                    data = (pristine / fixture).read_bytes()
                    oid = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\\0" + data).hexdigest()
                    if oid == wanted:
                        sys.stdout.buffer.write(data)
                        break
                else:
                    raise SystemExit(98)
            else:
                print("unexpected fake git arguments: " + repr(args), file=sys.stderr)
                raise SystemExit(97)
            """))
        fake_git.chmod(fake_git.stat().st_mode | stat.S_IXUSR)
        self.env = os.environ.copy()
        self.env["PATH"] = str(fake_bin) + os.pathsep + self.env.get("PATH", "")
        self.env["FAKE_GIT_TOPLEVEL"] = str(self.source)
        self.env["FAKE_GIT_PRISTINE"] = str(self.pristine)

    def run_patch(self, *extra: str) -> subprocess.CompletedProcess[str]:
        env = self.env.copy()
        return subprocess.run(
            [sys.executable, str(PATCH_CORE), "--source", str(self.source), *extra],
            text=True,
            capture_output=True,
            env=env,
        )

    def assert_pristine(self):
        self.assertEqual((self.source / "src" / "ARM.cpp").read_text(), ARM_PRISTINE)
        self.assertEqual((self.source / "src" / "NDS.cpp").read_text(), NDS_PRISTINE)

    def test_clean_checkout_patches_and_exact_patched_state_is_idempotent(self):
        first = self.run_patch()
        self.assertEqual(first.returncode, 0, first.stderr)
        arm_once = (self.source / "src" / "ARM.cpp").read_bytes()
        nds_once = (self.source / "src" / "NDS.cpp").read_bytes()

        second = self.run_patch()
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertEqual((self.source / "src" / "ARM.cpp").read_bytes(), arm_once)
        self.assertEqual((self.source / "src" / "NDS.cpp").read_bytes(), nds_once)

    def prepare_model_fixture(self):
        early = """        else
        {
            NDS.ARM9Timestamp = NDS.ARM9Target;
            return;
        }
                if (Halted == 1 && NDS.ARM9Timestamp < NDS.ARM9Target)
                {
                    NDS.ARM9Timestamp = NDS.ARM9Target;
                }
"""
        arm=ARM_PRISTINE.replace("void first()\n{", "template <CPUExecuteMode mode>\nvoid ARMv5::Execute()\n{\n"+early).replace("void second()", "template <CPUExecuteMode mode>\nvoid ARMv4::Execute()")
        nds=NDS_PRISTINE+"""
void NDS::RunFrameFixture()
{
            // we are running in sleep mode
                CurCPU = 0;

                if (CPUStop & CPUStop_GXStall)
                {
                    RunGX();
                }
                else if (CPUStop & CPUStop_DMA9)
                {
                    RunDMA();
                }
                else
                {
                    ARM9.Execute<cpuMode>();
                }

                RunTimers(0);
}
"""
        for name,data in (("ARM.cpp",arm),("NDS.cpp",nds)):
            (self.source/"src"/name).write_text(data)
            (self.pristine/name).write_text(data)

    def test_exact_model_upgrade_and_variant_isolation(self):
        self.prepare_model_fixture()
        self.assertEqual(self.run_patch("--work-observer").returncode,0)
        upgrade=self.run_patch("--work-observer","--model-budget")
        self.assertEqual(upgrade.returncode,0,upgrade.stderr)
        before={n:(self.source/"src"/n).read_bytes() for n in ("ARM.cpp","NDS.cpp")}
        self.assertEqual(before["ARM.cpp"].count(b"Timing.haltSkip"),2)
        self.assertEqual(before["NDS.cpp"].count(b"Timing.begin"),1)
        self.assertEqual(before["NDS.cpp"].count(b"Timing.end"),1)
        self.assertEqual(before["NDS.cpp"].count(b"Timing.fail"),1)
        for arguments in (("--verify-only",),("--verify-only","--work-observer")):
            self.assertNotEqual(self.run_patch(*arguments).returncode,0)
        exact=self.run_patch("--verify-only","--work-observer","--model-budget")
        self.assertEqual(exact.returncode,0,exact.stderr)
        again=self.run_patch("--work-observer","--model-budget")
        self.assertEqual(again.returncode,0,again.stderr)
        for n,data in before.items():self.assertEqual((self.source/"src"/n).read_bytes(),data)
        # A marker-like comment cannot make a modified derivative admissible.
        path=self.source/"src/ARM.cpp";path.write_bytes(before["ARM.cpp"]+b"\n// Timing.haltSkip spoof\n")
        self.assertNotEqual(self.run_patch("--verify-only","--work-observer","--model-budget").returncode,0)

    def test_model_upgrade_rejects_foreign_tree_before_any_mutation(self):
        self.prepare_model_fixture()
        self.assertEqual(self.run_patch("--work-observer").returncode,0)
        before={n:(self.source/"src"/n).read_bytes() for n in ("ARM.cpp","NDS.cpp")}
        (self.source/"CMakeLists.txt").write_text("# foreign build logic\n")
        result=self.run_patch("--work-observer","--model-budget")
        self.assertNotEqual(result.returncode,0)
        for n,data in before.items():self.assertEqual((self.source/"src"/n).read_bytes(),data)

    def test_model_budget_requires_explicit_work_before_any_mutation(self):
        result=self.run_patch("--model-budget")
        self.assertNotEqual(result.returncode,0)
        self.assertIn("requires --work-observer",result.stderr)
        self.assert_pristine()

    def test_explicit_work_variant_cannot_pass_default_verification(self):
        self.assertEqual(self.run_patch().returncode, 0)
        upgrade=self.run_patch("--work-observer")
        self.assertEqual(upgrade.returncode, 0, upgrade.stderr)
        self.assertEqual(self.run_patch("--work-observer", "--verify-only").returncode, 0)
        self.assertNotEqual(self.run_patch("--verify-only").returncode, 0)
        self.assertNotEqual(self.run_patch().returncode, 0)

    def test_work_upgrade_rejects_modified_legacy_tree_before_mutation(self):
        self.assertEqual(self.run_patch().returncode, 0)
        before=(self.source / "src/ARM.cpp").read_bytes()
        (self.source / "CMakeLists.txt").write_text("injected")
        self.assertNotEqual(self.run_patch("--work-observer").returncode, 0)
        self.assertEqual((self.source / "src/ARM.cpp").read_bytes(), before)

    def test_tracked_build_logic_is_rejected_before_source_mutation(self):
        (self.source / "CMakeLists.txt").write_text("message(FATAL_ERROR injected)\n")
        result = self.run_patch()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("checkout", result.stderr.lower())
        self.assert_pristine()

    def test_untracked_shadow_module_is_rejected_before_source_mutation(self):
        shadow = self.source / "cmake" / "CheckIPOSupported.cmake"
        shadow.parent.mkdir()
        shadow.write_text("message(FATAL_ERROR injected)\n")
        result = self.run_patch()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("checkout", result.stderr.lower())
        self.assert_pristine()

    def test_ignored_artifact_is_rejected_before_source_mutation(self):
        ignored = self.source / "build-evil" / "payload.exe"
        ignored.parent.mkdir()
        ignored.write_bytes(b"payload")
        result = self.run_patch()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("checkout", result.stderr.lower())
        self.assert_pristine()

    def test_marker_spoof_is_not_accepted_as_an_idempotent_patch(self):
        arm = self.source / "src" / "ARM.cpp"
        arm.write_text("// HG_RUNTIME_TRACE\n" + ARM_PRISTINE)
        result = self.run_patch()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("checkout", result.stderr.lower())
        self.assertEqual(arm.read_text(), "// HG_RUNTIME_TRACE\n" + ARM_PRISTINE)
        self.assertEqual((self.source / "src" / "NDS.cpp").read_text(), NDS_PRISTINE)

    def test_verify_only_rejects_a_late_untracked_shadow(self):
        patched = self.run_patch()
        self.assertEqual(patched.returncode, 0, patched.stderr)
        shadow = self.source / "cmake" / "CheckIPOSupported.cmake"
        shadow.parent.mkdir()
        shadow.write_text("message(FATAL_ERROR injected)\n")
        result = self.run_patch("--verify-only")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("checkout", result.stderr.lower())


class PatchCoreRealGitTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.source = Path(self.tmp.name) / "core"
        (self.source / "src").mkdir(parents=True)
        (self.source / "src" / "ARM.cpp").write_text(ARM_PRISTINE)
        (self.source / "src" / "NDS.cpp").write_text(NDS_PRISTINE)
        (self.source / "CMakeLists.txt").write_text("add_library(core STATIC src/ARM.cpp)\n")
        self.git("init", "-q")
        self.git("config", "user.name", "Runtime Test")
        self.git("config", "user.email", "runtime-test@example.invalid")
        self.git("add", ".")
        self.git("commit", "-q", "-m", "fixture")
        self.original = self.git("rev-parse", "HEAD").stdout.strip()

        spec = importlib.util.spec_from_file_location("runtime_patch_core_under_test", PATCH_CORE)
        assert spec is not None and spec.loader is not None
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)
        self.module.EXPECTED_REVISION = self.original

    def git(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", "-C", str(self.source), *args],
            text=True,
            capture_output=True,
            check=True,
        )

    def test_skip_worktree_cannot_hide_modified_build_logic(self):
        self.module.patch_core(self.source)
        self.git("update-index", "--skip-worktree", "CMakeLists.txt")
        (self.source / "CMakeLists.txt").write_text("message(FATAL_ERROR injected)\n")

        with self.assertRaises(self.module.CheckoutError):
            self.module.verify_checkout(self.source, require_patched=True)

    def test_hardlinked_source_is_rejected_before_patch(self):
        arm = self.source / "src" / "ARM.cpp"
        outside = Path(self.tmp.name) / "shared-ARM.cpp"
        outside.write_bytes(arm.read_bytes())
        arm.unlink()
        os.link(outside, arm)
        before = outside.read_bytes()

        with self.assertRaises(self.module.CheckoutError):
            self.module.patch_core(self.source)
        self.assertEqual(outside.read_bytes(), before)

    def test_replace_ref_cannot_substitute_the_pinned_tree(self):
        (self.source / "CMakeLists.txt").write_text("message(FATAL_ERROR injected)\n")
        self.git("add", "CMakeLists.txt")
        self.git("commit", "-q", "-m", "replacement")
        replacement = self.git("rev-parse", "HEAD").stdout.strip()
        self.git("reset", "-q", "--hard", self.original)
        self.git("replace", self.original, replacement)
        self.git("reset", "-q", "--hard", self.original)
        self.assertEqual(
            (self.source / "CMakeLists.txt").read_text(),
            "message(FATAL_ERROR injected)\n",
        )

        with self.assertRaises(self.module.CheckoutError):
            self.module.verify_checkout(self.source, require_patched=False)


if __name__ == "__main__":
    unittest.main()
