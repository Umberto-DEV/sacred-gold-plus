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
because they run our own compiled code under an ARM946E-S emulator; without a
usable compiler they are reported as skipped, not as failures.

Class B tests — the ones that open a real game file — are not run here. See
`source/README.md` for those.
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
    ("overlay in place",       SOURCE / "features/overlay/test", ["-m", "unittest", "discover", "-p", "test_*.py"]),
    ("save chunk",             SOURCE / "features/plus-chunk/test", ["-m", "unittest", "discover", "-p", "test_*.py"]),
]

CONTA = re.compile(r"^Ran (\d+) tests?", re.M)
SALTI = re.compile(r"skipped=(\d+)")


def esegui(nome, cwd, argv, env=None):
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
    print("  %-26s %3d run, %2d skipped   %s" % (nome, n - saltati, saltati,
                                                 "ok" if ok else "FAILED"))
    if not ok:
        print(uscita[-4000:])
    return ok, n, saltati


def compila_opzioni(tmp: Path) -> Path | None:
    """Build the options page payload and lay the shipped text blobs beside it."""
    uscita = tmp / "options"
    uscita.mkdir(parents=True, exist_ok=True)
    r = subprocess.run([sys.executable, str(SOURCE / "features/options/tools/compila.py"),
                        "--uscita", str(uscita)], text=True, capture_output=True)
    if r.returncode != 0:
        print("  options page             skipped: no usable ARM compiler")
        print("    " + (r.stderr.strip().splitlines() or ["(no output)"])[-1])
        return None
    for f in sorted((SOURCE / "features/options/prove/testi").iterdir()):
        shutil.copy2(f, uscita / f.name)
    return uscita


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--json", type=Path, help="write the counts to this file as well")
    a = ap.parse_args()

    print("Class A tests (no game file needed)\n")
    totale = saltati_tot = 0
    tutto_ok = True
    dettaglio = []

    for nome, cwd, argv in SUITE:
        ok, n, s = esegui(nome, cwd, argv)
        tutto_ok &= ok
        totale += n
        saltati_tot += s
        dettaglio.append({"suite": nome, "collected": n, "skipped": s, "ok": ok})

    with tempfile.TemporaryDirectory(prefix="sgp-class-a-") as d:
        tmp = Path(d)
        ok, n, s = esegui("native code (Unicorn)", SOURCE / "features/native-core/test",
                          ["-m", "unittest", "discover", "-p", "test_*.py"],
                          env={"SGP_SOLO_NUOVO": "1"})
        tutto_ok &= ok
        totale += n
        saltati_tot += s
        dettaglio.append({"suite": "native code (Unicorn)", "collected": n, "skipped": s, "ok": ok})

        build = compila_opzioni(tmp)
        if build is not None:
            ok, n, s = esegui("options page (Unicorn)", SOURCE / "features/options/test",
                              ["-m", "unittest", "discover", "-p", "test_*.py"],
                              env={"SGP_UI_BUILD": str(build)})
            tutto_ok &= ok
            totale += n
            saltati_tot += s
            dettaglio.append({"suite": "options page (Unicorn)", "collected": n,
                              "skipped": s, "ok": ok})

    print("\n%d tests collected, %d ran, %d skipped — %s"
          % (totale, totale - saltati_tot, saltati_tot, "PASS" if tutto_ok else "FAIL"))
    if a.json:
        a.json.write_text(json.dumps({"suites": dettaglio, "collected": totale,
                                      "skipped": saltati_tot, "ok": tutto_ok}, indent=2) + "\n")
    return 0 if tutto_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
