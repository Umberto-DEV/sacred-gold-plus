# Contributing to Sacred Gold Plus

This guide is for independent community contributors. The maintainer and coding
assistants work directly on `main`; contributors use a fork and propose a pull
request to `main`. A local Git worktree is optional and does not itself run
GitHub CI. Keep each proposal focused on one behavior or closely related set of
files. The [repository map](source/docs/architecture/README.md) identifies the
owning subsystem; [source/README.md](source/README.md) is the detailed build and
test reference.

For a reproducible problem, use the [bug report form](https://github.com/Umberto-DEV/sacred-gold-plus/issues/new/choose): give the exact version or candidate hash if known, language, emulator, expected and observed result, ordered steps and repeat count. Mark comparisons you have not tried as untested. For an early source proposal, use the optional change form; an issue is not a prerequisite for a PR. Use [Discussions](https://github.com/Umberto-DEV/sacred-gold-plus/discussions) for questions and ideas that do not yet have a reproducible failure. Do not upload private files or raw logs to any of these channels.

## 1. Start from current public source

Fork this repository on GitHub, then use a complete clone of your fork. The
current 1.3 composition reconstructs an authenticated historical ancestor, so
a shallow download or GitHub source ZIP is insufficient for that build.

```sh
git clone https://github.com/YOUR-NAME/sacred-gold-plus.git
cd sacred-gold-plus
git remote add upstream https://github.com/Umberto-DEV/sacred-gold-plus.git
git fetch upstream
git switch -c fix/short-description upstream/main
python3 -m venv .venv
.venv/bin/pip install -r source/requirements.txt
```

If you already have a full clone, you may instead create a worktree from its
current `upstream/main`:

```sh
git worktree add -b fix/short-description ../sgp-short-description upstream/main
```

These branch/worktree instructions are for external contributors only. Keep
private inputs and outputs outside both checkouts.

## 2. Change and check the source

Read the owning feature's README and its neighboring tests before editing. For
new ARM9 use, update both the [reservation register](source/docs/arm9-reserve-reservations.md)
and `source/docs/arm9-reserve-map.json`. Preserve input and preimage guards,
existing save layouts and identifiers. Include a regression test that fails on
the old behavior and passes on the changed source when the behavior is testable
without a ROM; say which additional game-dependent check is still needed.

From the repository root, run the same ROM-free runner as CI:

```sh
.venv/bin/python source/run_tests.py
```

This run takes roughly half an hour on the current hosted macOS image. An
ARM946E-S-capable clang is needed for the native suites. Running
`SGP_CI=1 .venv/bin/python source/run_tests.py` makes a missing compiler a failure, as
in CI. Read the per-suite results and skip reasons, not just the final PASS.
The [test guide](source/README.md#run-the-tests) explains Class A and Class B.
On systems without the required macOS production toolchain, run the available
source tests and let the hosted CI run its labeled compiler contracts; report
any local omissions rather than claiming a production build.

## 3. Build and test a private candidate when behavior changes

Use your own legally obtained HeartGold file, the exact pinned external inputs,
and a private directory outside the checkout. Follow the current
[1.3 composition guide](source/sgp131/README.md) for a pending candidate and
its independent readback. The 1.2.5 example in the general source guide builds
a predecessor, not the current 1.3.2 development source. A successful build or
readback is a file-level result; it is not runtime or release acceptance. If
you cannot meet the pinned production toolchain, report that limitation instead
of bypassing an identity check.

For a game change, compare the same scenario on the exact predecessor and your
candidate. Record language, source commit, input and candidate SHA-256, commands,
observed results, failed assertions and skipped checks. Test the changed path
and a nearby unaffected path. For event or shared runtime code, include a fresh
New Game route through Mom and any relevant late-game event, such as the Latios
totem, where you can reproduce it. A one-time successful event does not prove an
intermittent freeze absent.

Save compatibility is a release requirement. On **copies** of older raw `.sav`
files, check Continue, progress, Pokémon, inventory including expanded Bag
slots, Plus settings, native in-game SAVE, full emulator exit, cold restart and
Continue again. Cover English and Italian, saves without Plus data and saves
with Plus settings/Bag extensions when those fixtures are available. Keep the
original saves untouched. A savestate cannot replace this check. Record which
matrix cells you could not test; the maintainer completes missing acceptance
checks before any release. See the [validation evidence format](source/docs/validation/README.md)
and [runtime bench](source/docs/test-bench.md).

## 4. Prepare a public, reviewable proposal

Only authored source, build tools, tests and necessary documentation belong in
Git. Never commit or attach ROMs, saves, savestates, BIOS, firmware, dumps,
extracted game code/text/graphics, private paths, raw logs or `.xdelta` patches.
For a new public file, add its exact path to `.github/public-files.json` and
stage it explicitly. Inspect the whole staged diff, including workflows,
dependencies, generated blobs, licenses and credits:

```sh
git add path/to/reviewed-file .github/public-files.json
git diff --cached --check
git diff --cached
python3 .github/check_public.py
```

Use the real changed paths in `git add`; omit the manifest argument if no new
public file was added. The checker examines tracked files and is a privacy/file
contract, not a malware scanner or proof that code is correct. Commit and push
the contributor branch to your fork:

```sh
git commit -m "Describe the focused change"
git push -u origin fix/short-description
```

Enable Actions on the fork, and inspect
both **Public files** and **Class A tests** for the exact commit. Then open a
pull request from the fork branch to this repository's `main` using the
[PR template](.github/PULL_REQUEST_TEMPLATE.md). If GitHub requests approval
for a first-time contributor run, wait for maintainer review; the PR check can
also run against GitHub's test merge commit. A failed, skipped or unrun check
must be explained in the PR, never described as green coverage.

Fill in the template with the before/after reproducer, exact commit and
candidate hashes (hashes only), commands, per-language results, save-copy
coverage, skips and limits. For documentation-only changes, mark game-specific
fields `N/A` with a reason. Disclose reused work, permission to include it and
material AI assistance. The maintainer reviews the source, security-sensitive
workflow/dependency changes and CI result, then independently builds and tests
a candidate before accepting gameplay or release claims.

Do not upload a player release ZIP as a substitute for review. The current
packager targets the published 1.3.1 release; the 1.3.2 source has no accepted
player package. If a maintainer asks for an extra handoff, provide a text-only
manifest of source paths and SHA-256s, exact input fingerprints, tool versions,
candidate hash and redacted test results. Hashes identify bytes; they do not
certify an attachment as safe. Official release files are built only after
independent reconstruction and runtime/save acceptance and are never replaced
in place.
