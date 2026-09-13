#!/usr/bin/env python3
"""Run the Class A test suites — the ones that need no game file.

These are exactly the suites GitHub Actions runs on every push and pull
request, so a green run here is a green run there. From the repository root:

    python3 -m venv .venv
    .venv/bin/pip install -r source/requirements.txt
    .venv/bin/python source/run_tests.py

It prints one line per suite with how many tests ran, how many were skipped
and why, then a total. It exits non-zero if any suite fails.

Two suites need a C compiler with the ARM target (`clang --target=armv5te-none-eabi`)
because they run our own compiled code under an ARM946E-S emulator. A MISSING
compiler makes the options-page suite SKIPPED, with its test count, and it
stays in the summary and in the JSON — it used to vanish from both. With
`--richiedi-compilatore` (or `SGP_CI=1`, which continuous integration sets) a
missing compiler is a failure instead: on a machine that is supposed to have
one, a silently skipped suite is 95 tests nobody notices. A compiler that is
present but cannot BUILD the shipped sources is never a skip: that is a defect,
and it fails here as it would anywhere else.

A suite that collects no test at all is a FAILURE. `unittest discover` on a
folder with no test file prints "Ran 0 tests ... OK" and exits 0, so deleting
three suites used to leave the run green.

Class B tests — the ones that open a real game file — are listed and run apart,
because they skip wherever Class A runs and must never be counted as Class A
coverage. They are still part of the ONE final verdict printed at the end: the
Class A line used to be the last thing on screen and was printed before the
Class B suites had even run, so a red Class B suite left the exit code and the
JSON red while the output ended on the word PASS. See `source/README.md`.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SOURCE = Path(__file__).resolve().parent
ROOT = SOURCE.parent

# (name, working directory, unittest arguments)
SUITE = [
    ("sgp12 library",          SOURCE, ["-m", "unittest", "sgp12.test_lib"]),
    ("ARM9 reserve register",  SOURCE, ["-m", "unittest", "verifiche.test_riserva"]),
    ("text codec / translation", SOURCE, ["-m", "unittest", "discover", "-s", "translation", "-p", "test_*.py"]),
    ("text width measurement", SOURCE, ["-m", "unittest", "discover", "-s", "quality-audit", "-p", "test_*.py"]),
    ("EV/IV guide (1.1)",      SOURCE, ["-m", "unittest", "discover", "-s", "native-guide", "-p", "test_*.py"]),
    ("EV/IV reader (1.1)",     SOURCE, ["-m", "unittest", "discover", "-s", "native-eviv", "-p", "test_*.py"]),
    ("guide label patch",      SOURCE / "features/guide/test", ["-m", "unittest", "discover", "-p", "test_*.py"]),
    ("save chunk",             SOURCE / "features/plus-chunk/test", ["-m", "unittest", "discover", "-p", "test_*.py"]),
    ("full bag build metadata", SOURCE / "features/borsa/test", ["-m", "unittest", "discover", "-p", "test_build.py"]),
    ("battle motion build policy", SOURCE / "features/anim2/test", ["-m", "unittest", "discover", "-p", "test_metadata.py"]),
]

# Class B, listed apart on purpose. These need a real game file (SGP_ROM_DIR) and
# therefore skip everywhere Class A runs — including CI. They used to sit in the
# list above, where "0 run, 3 skipped ok" counted as a pass: the whole BLZ codec
# and in-place overlay applicator, 31 tests, could not fail anything. They are
# run and reported, but they are never counted as Class A coverage.
SUITE_CLASSE_B = [
    ("overlay in place",       SOURCE / "features/overlay/test", ["-m", "unittest", "discover", "-p", "test_*.py"]),
    # The rare-candy suite runs the shipped ARM9 under Unicorn starting from the
    # hook site itself, so it needs the built ROMs (SGP_ROM_DIR). Without them it
    # skips with a reason, and it is never counted as Class A coverage.
    ("rare candy (Unicorn)",   SOURCE / "features/caramelle/test", ["-m", "unittest", "discover", "-p", "test_*.py"]),
    ("full bag pipeline",      SOURCE / "features/borsa/test", ["-m", "unittest", "discover", "-p", "test_composta.py"]),
    ("full bag (Unicorn)",     SOURCE / "features/borsa/test", ["-m", "unittest", "discover", "-p", "test_borsa_nucleo.py"]),
    ("battle motion (Unicorn)", SOURCE / "features/anim2/test", ["-m", "unittest", "discover", "-p", "test_blob5.py"]),
    ("battle motion reader mutants", SOURCE / "features/anim2/test", ["-m", "unittest", "discover", "-p", "test_mutanti_anim2.py"]),
]

CONTA = re.compile(r"^Ran (\d+) tests?", re.M)
SALTI = re.compile(r"skipped=(\d+)")


def esegui(nome, cwd, argv, env=None, classe_b=False):
    amb = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    amb.update(env or {})
    r = subprocess.run([sys.executable, *argv], cwd=str(cwd), env=amb,
                       text=True, capture_output=True)
    uscita = r.stdout + r.stderr
    m = CONTA.search(uscita)
    n = int(m.group(1)) if m else 0
    s = SALTI.search(uscita)
    saltati = int(s.group(1)) if s else 0
    # A module-level skip reports "Ran 0 tests" with skipped=N: those N tests
    # were collected, not run.
    n = max(n, saltati)
    ok = r.returncode == 0
    if not classe_b and n == 0:
        # `unittest discover` on a folder with no test file exits 0. A suite
        # that collects nothing is not a suite that passes.
        ok = False
        print("  %-26s   no test collected — the suite is empty or was not found" % nome)
    print("  %-26s %3d run, %2d skipped   %s" % (nome, n - saltati, saltati,
                                                 "ok" if ok else "FAILED"))
    if not ok:
        print(uscita[-4000:])
    return ok, n, saltati


def compila_opzioni(tmp: Path):
    """Build the options page payload and lay the shipped text blobs beside it.

    Returns `(folder or None, reason or None, missing_compiler)`. The reason is
    kept so the summary can say why the suite did not run: it used to be printed
    and then dropped, and the suite disappeared from the totals and from the
    JSON.

    The third value is the one that matters. A missing compiler and a *broken
    build* are not the same event: the first is "this machine cannot run the
    suite" — a skip, unless CI says every machine must have one; the second is
    "the shipped sources no longer compile", which is a failure everywhere, on
    every machine, CI or not. Both used to take the same branch and be reported
    as "no usable ARM compiler", so a real compile error was quietly downgraded
    to a skip on every developer machine."""
    uscita = tmp / "options"
    uscita.mkdir(parents=True, exist_ok=True)
    if shutil.which("clang") is None:
        return None, "no ARM compiler: clang is not on PATH", True
    r = subprocess.run([sys.executable, str(SOURCE / "features/options/tools/compila.py"),
                        "--uscita", str(uscita)], text=True, capture_output=True)
    if r.returncode != 0:
        tutto = r.stdout + r.stderr
        motivo = (r.stderr.strip().splitlines() or ["(no output)"])[-1]
        # The child runs clang itself: if *it* is the one that cannot find it,
        # that is still a missing compiler, not a broken source tree.
        assente = ("FileNotFoundError" in tutto
                   or "No such file or directory: 'clang'" in tutto
                   or "command not found" in tutto)
        if assente:
            return None, "no ARM compiler: " + motivo, True
        return None, "the shipped options sources do not build: " + motivo, False
    for f in sorted((SOURCE / "features/options/prove/testi").iterdir()):
        shutil.copy2(f, uscita / f.name)
    return uscita, None, False


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--json", type=Path, help="write the counts to this file as well")
    ap.add_argument("--richiedi-compilatore", action="store_true",
                    help="fail if the ARM compiler is missing instead of skipping "
                         "the options-page suite (continuous integration sets SGP_CI=1 "
                         "for the same effect)")
    a = ap.parse_args()
    esigi_compilatore = a.richiedi_compilatore or bool(os.environ.get("SGP_CI"))

    print("Class A tests (no game file needed)\n")
    totale = saltati_tot = 0
    classe_a_ok = True
    dettaglio = []

    # If a game file is available, the reserve suite must not be allowed to skip
    # T2-T5 quietly: arming SGP_RISERVA_COMPLETA turns a missing ROM into a
    # failure. Without a ROM those eight tests are Class B and skip by design.
    ambiente_riserva = {"SGP_RISERVA_COMPLETA": "1"} if os.environ.get("SGP_RISERVA_ROM") else None

    for nome, cwd, argv in SUITE:
        ok, n, s = esegui(nome, cwd, argv,
                          env=ambiente_riserva if nome == "ARM9 reserve register" else None)
        classe_a_ok &= ok
        totale += n
        saltati_tot += s
        dettaglio.append({"suite": nome, "collected": n, "skipped": s, "ok": ok})

    with tempfile.TemporaryDirectory(prefix="sgp-class-a-") as d:
        tmp = Path(d)
        ok, n, s = esegui("native code (Unicorn)", SOURCE / "features/native-core/test",
                          ["-m", "unittest", "discover", "-p", "test_*.py"])
        classe_a_ok &= ok
        totale += n
        saltati_tot += s
        dettaglio.append({"suite": "native code (Unicorn)", "collected": n, "skipped": s, "ok": ok})

        build, motivo, compilatore_assente = compila_opzioni(tmp)
        if build is not None:
            ok, n, s = esegui("options page (Unicorn)", SOURCE / "features/options/test",
                              ["-m", "unittest", "discover", "-p", "test_*.py"],
                              env={"SGP_UI_BUILD": str(build)})
            classe_a_ok &= ok
            totale += n
            saltati_tot += s
            dettaglio.append({"suite": "options page (Unicorn)", "collected": n,
                              "skipped": s, "ok": ok})
        else:
            # The suite still has a line, a count and a JSON entry: it used to
            # disappear from all three, and the run said PASS with 95 tests gone.
            n = conta_soltanto("options page (Unicorn)", SOURCE / "features/options/test")
            # A missing compiler is a skip (a failure only where CI says every
            # machine must have one). A build that *fails* is never a skip: the
            # shipped sources not compiling is a defect on any machine.
            ok = compilatore_assente and not esigi_compilatore
            print("  %-26s %3d run, %2d skipped   %s"
                  % ("options page (Unicorn)", 0, n, "skipped" if ok else "FAILED"))
            print("    " + motivo)
            if not ok and compilatore_assente:
                print("    --richiedi-compilatore / SGP_CI=1: a missing compiler is a failure here")
            elif not compilatore_assente:
                print("    this is a build failure, not a missing tool: it fails everywhere")
            classe_a_ok &= ok
            totale += n
            saltati_tot += n
            dettaglio.append({"suite": "options page (Unicorn)", "collected": n,
                              "skipped": n, "ok": ok, "motivo": motivo,
                              "compilatore_assente": compilatore_assente})

    print("\nClass A: %d tests collected, %d ran, %d skipped — %s"
          % (totale, totale - saltati_tot, saltati_tot,
             "pass" if classe_a_ok else "FAIL"))

    print("\nClass B suites (need a game file: they skip here and in CI)\n")
    dettaglio_b = []
    classe_b_ok = True
    totale_b = saltati_b = 0
    for nome, cwd, argv in SUITE_CLASSE_B:
        ok, n, s = esegui(nome, cwd, argv, classe_b=True)
        classe_b_ok &= ok
        totale_b += n
        saltati_b += s
        dettaglio_b.append({"suite": nome, "collected": n, "skipped": s, "ok": ok})
    print("  Class B: %d tests collected, %d ran, %d skipped — %s"
          % (totale_b, totale_b - saltati_b, saltati_b, "pass" if classe_b_ok else "FAIL"))
    print("  (not counted as Class A coverage: set SGP_ROM_DIR to run them)")

    # ONE verdict, printed after everything, and it counts Class B too. The
    # Class A line above used to be the last word and was printed BEFORE the
    # Class B suites ran: a red Class B suite changed the exit code and the JSON
    # but the run still ended on the word PASS. Whoever read the output instead
    # of the exit code read the wrong answer.
    tutto_ok = classe_a_ok and classe_b_ok
    print("\n%d tests collected in all (Class A %d + Class B %d) — %s"
          % (totale + totale_b, totale, totale_b, "PASS" if tutto_ok else "FAIL"))

    if a.json:
        a.json.write_text(json.dumps({"suites": dettaglio, "classe_b": dettaglio_b,
                                      "collected": totale, "skipped": saltati_tot,
                                      "classe_a_ok": classe_a_ok,
                                      "collected_classe_b": totale_b,
                                      "skipped_classe_b": saltati_b,
                                      "classe_b_ok": classe_b_ok,
                                      "ok": tutto_ok}, indent=2) + "\n")
    return 0 if tutto_ok else 1


def conta_soltanto(nome, cwd):
    """How many tests the suite would collect, without running it: so a suite
    that cannot run still shows its size instead of vanishing."""
    codice = ("import unittest,sys;"
              "print('COLLECTED', unittest.defaultTestLoader.discover('.', pattern='test_*.py').countTestCases())")
    r = subprocess.run([sys.executable, "-c", codice], cwd=str(cwd),
                       text=True, capture_output=True,
                       env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))
    for riga in (r.stdout + r.stderr).splitlines():
        if riga.startswith("COLLECTED "):
            return int(riga.split()[1])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
