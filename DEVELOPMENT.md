# Development

How this repository is organized, how changes get in, and how a release is cut.
For the player-facing side, see [README](README.md). To contribute, start with
[CONTRIBUTING](CONTRIBUTING.md).

## Branches, pull requests, releases

| | What it is |
| --- | --- |
| `main` | The development trunk, and it is always green: sources, tools, tests, development documentation and the current release package. Protected — changes arrive through pull requests with a passing CI run and a review, and the history stays linear. |
| `feature/…`, `fix/…` | One branch per contribution, from a fork or from this repository. Short-lived; deleted after the merge. |
| `vX.Y` tag + GitHub release | The finished version. The release page carries the player ZIPs as attachments. |
| `vX.Y-rcN` tag + release marked **pre-release** | A preview. Prepared by hand and attached like any other release. |

There is no nightly build. **The game cannot be built on GitHub**: producing a
ROM requires the player's own game file, which never enters this repository, a
CI runner, or any service. CI checks the sources and runs the tests that need
no game file; everything that touches a ROM runs on the contributor's machine
and is reported in the pull request.

The released bytes are immutable. A published asset is never overwritten with
different bytes; a correction becomes a new release.

## The two classes of test

**Class A — no game file.** Text codec, pixel-width measurement, BLZ round
trips, the save-chunk format, the ARM9 reserve register, and the behaviour of
our own compiled ARM code under an emulator (Unicorn). These run in CI on every
push to any branch and on every pull request against `main`, and you can run
exactly the same set locally:

```sh
python3 -m venv .venv
.venv/bin/pip install -r source/requirements.txt
.venv/bin/python source/run_tests.py
```

The script prints one line per suite with how many tests ran and how many were
skipped, then a total. A suite that needs a C compiler with the ARM target
(`clang --target=armv5te-none-eabi`) reports itself as skipped rather than
failing when no usable compiler is present.

**Class B — with a game file.** Rebuilding the 1.2 ROM from a 1.1 base and
checking it byte for byte, the reserve checks T2–T5 against real bytes, the
block readers, and the runtime runs on the headless emulator. These need a ROM
you obtained yourself, in a private folder outside this checkout, and they
never run in CI. Point the tools at it:

```sh
export SGP_ROM_DIR=/path/to/your/private/roms     # base-1.1-EN.nds, base-1.1-IT.nds
export SGP_PRET_SOURCE=/path/to/pokeheartgold     # the checkout holding charmap.txt

cd source
python3 -m sgp12.costruisci --base "$SGP_ROM_DIR/base-1.1-EN.nds" \
        --uscita /tmp/sgp-1.2-EN.nds --lingua EN
python3 -m sgp12.verifica /tmp/sgp-1.2-EN.nds \
        --base "$SGP_ROM_DIR/base-1.1-EN.nds" --lingua EN
python3 -m unittest sgp12.test_lib -v            # the skipped tests now run
SGP_RISERVA_ROM=/tmp/sgp-1.2-EN.nds python3 -m unittest verifiche.test_riserva -v
```

The pull request template asks you to write down which Class B tests you ran
and what they said. "Not run" is an acceptable answer; a claim that was not
actually checked is not.

Full instructions: [docs/rebuilding-1.2.md](docs/rebuilding-1.2.md) and
[source/README.md](source/README.md).

## How the repository reads

```
source/            everything needed to rebuild and check the game
  sgp12/           the library: one command builds 1.2 from a 1.1 base, one checks it
    blocchi/       one module per feature, each with apply() and an independent read-back
    build/         the validated payloads each block writes (our own compiled code)
  features/        one self-contained folder per feature: native sources, tools, tests
  verifiche/       the reserve checks T1-T5 and the automatic runtime gates
  native-guide/    the in-game EV/IV guide (from 1.1)
  native-eviv/     the EV/IV reader (from 1.1)
  translation/     message codec, release recipes, container helpers
  quality-audit/   text width measurement against the game font
  recipes/ ui/     the localization recipes and interface manifests
  runtime/         the headless melonDS harness: sources and build instructions
  scripts/         the 1.04 variant builders, kept for the older route
  run_tests.py     the Class A suites, the same ones CI runs
docs/              development documentation (reserve map, contracts, bench, rebuild)
release/1.2/       the reviewed player package: patches, cheats, manuals, checksums
.github/           the public-file contract, the checks workflow and the templates
```

Two habits are worth knowing before reading the code.

**Applier and read-back are two files, on purpose.** Every feature has an
applier that verifies the preimage byte for byte before writing and refuses if
the bytes are already in their post state, and a read-back that opens the
produced ROM and reads the layout out again without reusing the applier's
logic. If they shared a wrong constant, the proof would be worth nothing.

**Mutants.** Each feature carries deliberately wrong variants that its tests
must kill. A test that also passes on a mutant is decoration, not a test.

## Adding a feature

1. Open an issue or a short proposal first and agree on the behaviour.
2. If the feature needs space in the ARM9 reserve, claim it in
   [docs/arm9-reserve-reservations.md](docs/arm9-reserve-reservations.md) and add
   its entry to `docs/arm9-reserve-map.json` in the same change. The reserve is
   contended and the register is what keeps two features from writing over each
   other. Read [docs/arm9-reserve-map.md](docs/arm9-reserve-map.md) first —
   in particular the rule that anything with a public address anchors to the
   high end.
3. Put the native sources, the applier, the read-back and the tests under
   `source/features/<name>/`, and wire the block into `source/sgp12/blocchi/`
   so `sgp12.costruisci` applies it in order.
4. Write the acceptance criteria before the run, not after. Run the
   counter-proof — the same script on the unfixed ROM — first, and check that
   it fails: if the fixed and unfixed ROMs give the same answer, one of the two
   is not measuring anything.
5. Keep `source/run_tests.py` green, and say in the pull request which Class B
   tests you ran.

## Release procedure

See [MAINTAINING.md](MAINTAINING.md).
