# U-turn and flinch-item fix — 1.3.3 candidate

This report separates source and counterfactual evidence from actual candidate
ROM validation. Final delivery identities and subsequent localized corrections
are consolidated in the [1.3.3 correction report](fixes-1.3.3.md). It does not establish a release, device acceptance or universal
save compatibility.

## Defects and implementation

The previous helper's unmarked modifier fallback altered the battler and flag
arguments before the native getter. With an incoming flinch item this could
return an incorrect modifier. Separately, testing only bit 16 allowed a negative
native `shellBellDamage` value such as −200 to be mistaken for a snapshot,
cleared and used to enter the flinch/RNG path.

The new helper is 74 bytes, SHA-256
`fd3e38715bd40098080f7375f3d16a96044d359dda4c5c1436cb9bbbf55f478c`.
The effect entry is unchanged; modifier entry remains at +32, with live calls
at +26 and +68. Fallback preserves the original `(context, battler, flag)`
arguments. Recognition requires `(word >> 16) == 1`; the modifier consumes the
recognized word once. The existing script producer, entry points, allocation,
save layout and identifiers are unchanged. The first 64 bytes of the shared
192-byte reserve belong to another owner; the helper occupies its existing
128-byte tail. Actual successor readback confirms the reserve, hooks and script
from the candidate bytes rather than inferring them from shared addresses.

The recognized range `0x00010000..0x0001FFFF` is disjoint from nonpositive
native values within the examined valid game-state writer and bounded-loop
domain. This argument does not cover corrupted state, arbitrary external script
writes or unbounded forced calls. The ordinary Shell Bell question remains open;
this fix does not establish a healing-loss result.

## Evidence

The pre-fix targeted regression produced failures for both fallback ABI and the
negative-value collision. After the change, 13 targeted helper and retained
compiler tests passed, covering four battlers, fallback arguments, state and RNG,
marker lifetime, boundary words, canaries and selected mutants. The separate
version and UI-copy suite passed 21 tests; six additional host tests passed.
Independent ELF readback confirmed the 74-byte payload and its layout. These are
bounded tests, not a full playthrough.

On authenticated EN and IT r4 inputs, 53 counterfactual cases per language
passed with the new helper applied in memory. Native getters, cache, RNG and
division execute; the producer uses a source-word interpreter and ability and
script transport are modeled. These runs do **not** constitute composed 1.3.3
ROMs or a complete natural pivot. Historical r4 results and identities retain
their own scope.
Eight focused host tests additionally check RNG call counts, seed transitions,
outputs and continuity across the first entry and repeat, including mutations
that preserve the final flinch result. A CPU-free recheck of the existing raw
observations passed all 53 cases in each language. It did not execute the game
again or change the scope of the counterfactual evidence.

In these raw observations, `flinch=true` records a request to the modeled
transport for script 14. It does not establish execution of that script, a
status-bit change or a skipped turn. The `original` comparison restores the
parent's original getter hooks within the r4 counterfactual; it is not a whole
retail playthrough. The fallback case with item 221 and roll 9 restores modifier
10 instead of 0, with one RNG call in both versions. The separate −200/item-0
case preserves the native word and avoids the legacy request and extra draw.
Their frequency and player-visible effects in normal battles remain unmeasured.

A bounded offline feasibility review on 15 November found an authenticated
raw-save replay reaching a normal Route 45 battle, a Party switch and an
Earthquake KO. It does not establish either defect's trigger. The historical
replay binaries are absent at their recorded paths; current runtime identities
retain their own scoped qualifications. No new guest run was performed. One
resumable starting case remains documented privately, pending a normal-input
continuation that produces the specified non-KO damage condition and makes its
causal state observable. This review adds no natural-battle acceptance.

## Active onboarding title and historical onboarding successors

The existing UI-owned 1008-byte bank at `0x023DA800` contains 29 indexed
strings. Active onboarding title entry 20 now reads `Sacred Gold Plus V1.3.3`;
the other 28 raw strings and the adjacent 16-byte canary are preserved. Retired
entry 0 remains inactive and historical. The DS header/banner is unversioned;
this is not a global replacement of historical version strings.

Five-image readback passed on these exact onboarding successors. The later
[final delivery report](fixes-1.3.3.md) identifies DE/FR Training successors;
the table and save cycles here retain their historical identities. An additional whole-file
comparison against each corresponding first, pre-onboarding candidate found no
changes outside the bank, including unindexed gaps. The unchanged battle helper
and other code bytes support retaining the EN/IT 53-case counterfactual results
above with their original models and limits; they do not establish a natural
battle or pivot.

| Language | Successor SHA-256 | Bytes | Scoped readback |
| --- | --- | ---: | --- |
| EN | `d6fbdf8bd0aec528a336713b497847da36b467001b2f550c9cc583679c3e5c7d` | 152786844 | PASS |
| IT | `1a889803ff3598c3bab89f036c007cd4c0163a1b2f80377794c9e46baccd34cd` | 159029760 | PASS |
| FR | `e8d895f054160195ec8ee06c9328d8333d41c328a54e1da4c231a4ad77e4fe14` | 162560728 | PASS |
| ES | `0642b270a151aeedb202fc9d3b578a54158817c98ebd06c58d7c3564cb0b1b40` | 162490072 | PASS |
| DE | `cb9459d04d207f16a60f5dab868c5fee16b1696f9cccb1d0c4e507d38d2370ca` | 162932492 | PASS |

These identities are in the [current candidate contract](../../distribution/game-1.3.3.json).
EN and FR Continue prompts were visually reviewed on host save copies without
SAVE or confirmation. New Game uses the statically identified shared title path;
it was not visually exercised in that capture. This does not qualify all five
languages visually, a physical device, firmware or natural gameplay.

Seven successor Continue/native SAVE/cold cycles passed on five original
fixtures: legacy and advanced fixtures each on EN and IT, and one regional
fixture each for FR, ES and DE. Saved, cold and post-UI exports were byte
identical in each case; original fixtures and working copies remained unchanged.
Checks cover progress, party, storage, Bag and existing Plus settings, with the
recorded native bookkeeping and HF02 migration exceptions. Loaded, saved and
cold screens were reviewed for all seven cases; Options and Guide body screens
were reviewed in five languages. Guide-body review is not a version-label
observation. This finite host coverage is not universal save compatibility or
native-speaker certification.

Five private same-language 1.3.2-r4 to current successor deltas passed xdelta3
and independently pinned RomPatcher.js decoding, each checked against its full
successor SHA-256 and size. Patch sizes are 691 bytes EN, 695 IT and 730 each
FR/ES/DE. This is transport validation, not release packaging or installation.
Source CI is a separate check from gameplay acceptance; see the
[public workflow](../../../.github/workflows/public-checks.yml).

The source-only EOF maintenance removed two final LF bytes and updated six
dependent pins. Two owned builders reproduced seven previously authenticated
native text bodies totaling 1616 bytes. That maintenance did not read a ROM or
execute a guest and does not establish a complete original retail C build.

## First candidate: exact r4 update transport

For the first, pre-onboarding candidate, a separate private transport test
generated one same-language delta from each exact 1.3.2-r4 target to that candidate. All five passed sequential
xdelta3 and independently pinned RomPatcher.js decoding, each checked against
the full candidate SHA-256 and size. The unchanged distribution tools used
xdelta3 3.1.0, Node 24.14.0 and RomPatcher.js commit
`3183884086825c3a57c72026234debcef1e2240c`. Delta sizes are 651 bytes EN,
655 IT and 692 each FR/ES/DE. The ten ROM inputs and productive sources passed
their before/after identity checks; temporary decoded ROMs were removed.

These are five private update-transport results, not approved release packages
or clean-ROM/earlier-version routes. No new ARM9 build, SAVE cycle or gameplay
run was needed. File reconstruction does not establish installation or game
acceptance; natural-battle and physical-device gates remain pending.

| First-candidate language | SHA-256 | Bytes | Scoped readback |
| --- | --- | ---: | --- |
| EN | `f8786377cdec82e776a0287843c319ab166175bc2b4fb194d2be76d6bae399bf` | 152786844 | PASS |
| IT | `c7d912cea2cd5b7330cca79bbc12ba0b33d4593b2987e8fb0f46d21df36b4b70` | 159029760 | PASS |
| FR | `7bd441e66b6bb84083a1c1382f71c5e157ee350eaa4ac0b6776ef064c07e4b00` | 162560728 | PASS |
| ES | `6843aeca9ac6e0643078438bfe047a0af4a8325b3f6e757e52a76568579a3e8b` | 162490072 | PASS |
| DE | `8bb92680124bc5ee51178c4f5e90c91878acc7397e933725ffbb9581b201795b` | 162932492 | PASS |

These are the historical first-candidate identities, not the current candidate
contract. Their readback covers active logical files and mapped ARM9, including the helper,
parent and script identities; unindexed historical physical bytes and repacking
gaps were not exhaustively compared. Compression and FAT placement are assessed
separately from decoded owner data. These byte and data checks do not establish
a complete natural pivot: the native behavior evidence above remains an EN/IT
counterfactual with the stated models.

## Reproduce the EN/IT counterfactual

From the repository root, prepare the [source dependencies](../../requirements.txt):
ndspy 4.2.0, Unicorn 2.1.4 and Capstone 5.0.9. The recorded production setup
uses Python 3.14.7 (executable SHA-256
`87d4df53fd91304be5bac391fb204643c36b7df2023c04a0953bcbc7d4fdf634`) and
Apple clang 21.0.0 (clang-2100.4.1.1), SHA-256
`fc5e3cbba6ad54059295cad716aacb05ace8235f5f7a6031f1d8c15d24bd6d66`.
The compiler flags are `--target=armv5te-none-eabi -mcpu=arm946e-s -mthumb
-ffreestanding -fno-builtin -x assembler-with-cpp`. The source
[uturn.S](../../features/type-consumers/uturn.S) SHA-256 is
`6a79cb34abdb4a968b70d30b55d1d89917499c153010a05e3dd72586b458afbb`.
Use a fresh private artifact directory and set `ARTIFACT_DIR` to its path:

```sh
mkdir -p "$ARTIFACT_DIR"
export ARTIFACT_DIR
PYTHONPATH=source .venv/bin/python - <<'PYCODE'
import json, os
from pathlib import Path
from sgp131 import uturn_flinch as U
work = Path(os.environ['ARTIFACT_DIR'])
payload, receipt = U.compile_native(work, retain_object=True)
with (work / 'native.bin').open('xb') as out:
    out.write(payload)
with (work / 'receipt.json').open('x') as out:
    json.dump(receipt, out, indent=2)
    out.write('\n')
PYCODE
```

This produces `uturn.o`, `native.bin` and `receipt.json`. The recorded object
SHA-256 is `5bea843a0ef60ee6ecf1a5ec6c722142f472a148cdd955521a8d7bdde9d4f090`;
the 74-byte fixed-up payload SHA-256 is
`fd3e38715bd40098080f7375f3d16a96044d359dda4c5c1436cb9bbbf55f478c`.
The artifact reader checks source, compiler receipt, ELF symbols, placeholders,
fixups and payload, not just filenames. The helper begins at `0x023D5A20`,
within its 128-byte tail; the preceding 64-byte foreign stub is checked intact.
The two overlay-12 hook sites are `0x0224E084` and `0x0224E090`; the existing
script member 175 SHA-256 is
`eaa254c435e16397b233c8f3e796f1655003358e4252bcc57352f3ca89b58c9a`.

Supply the exact authenticated r4, V4, base 1.1 and retail images for the same
language. The exact role hashes and sizes are enforced by the
[attribution reader](../../features/fairy-ai/tools/attribuisci.py) and its
referenced baseline and r4 contract; r4 is the historical input, not the new
candidate. The Plus 1.1 base here is the authenticated Plus input for this
role; do not substitute a plain Sacred Gold 1.1 image. These are the four
recorded input identities for each language:

| Language | Input role | SHA-256 | Bytes |
| --- | --- | --- | ---: |
| EN | Retail | `65f02a56842b75aa92d775d56d657a56fe3fa993550b04dc20704ab82d760105` | 134217728 |
| EN | Plus 1.1 base | `281c2d68e442479e679d8b7e36566ade614d236151c65c9684bad6985461827d` | 127104144 |
| EN | V4 | `179edfb1ca331503f438e98f3afccfb0ab85759bf9ab88fb86c735f5fcefbf90` | 147345256 |
| EN | 1.3.2 r4 | `2e30d6960bb059615fca7527700d86f8282e82ccbe99bf62e22f027453dc3d3d` | 152786844 |
| IT | Retail | `013d04f5512b01ad98735a5f850dc039f0ee80bc57035b3a10e8b650be690ce1` | 134217728 |
| IT | Plus 1.1 base | `7b61646c627eb67cd991dbc33d68519edd69395468ea8b326e867fe98e62d077` | 131906120 |
| IT | V4 | `2a2f0b437fca524c18b71b20feb01a1f51351e61c7c897ce73d9b3be1ee3a156` | 153228136 |
| IT | 1.3.2 r4 | `13ebac02bdea3036511773587e6603ce6834e25f4b13d1a4662c3e954bfd5d4a` | 159029760 |

Set the path variables below to owned files and choose a fresh JSON path
outside the source tree:

```sh
PYTHONPATH=source .venv/bin/python source/features/type-consumers/tools/verifica_uturn_133.py \
  --language EN --rom "$R4_ROM" --v4 "$V4_ROM" --base "$BASE11_ROM" \
  --retail "$RETAIL_ROM" --artifact "$ARTIFACT_DIR" --json "$REPORT_JSON"
```

Then set the four ROM variables to the matching Italian identities and choose a
new report path:

```sh
PYTHONPATH=source .venv/bin/python source/features/type-consumers/tools/verifica_uturn_133.py \
  --language IT --rom "$R4_ROM" --v4 "$V4_ROM" --base "$BASE11_ROM" \
  --retail "$RETAIL_ROM" --artifact "$ARTIFACT_DIR" --json "$REPORT_JSON"
```

Exit 0 means this finite in-memory counterfactual passed; any refusal is nonzero.
The tool reads the supplied images and writes only the new report: it neither
creates a candidate ROM nor changes a save. Its modeled producer and ability /
script transport and its executed native components are described above.

## Reproduce the five-candidate static readback

The public [readback tool](../../verifiche/readback_133.py) accepts a strict
manifest with exactly these five targets. This example uses placeholder
filenames; replace them with the owned candidate, corresponding composition
receipt and historical 1.3.2 r4 baseline for each language. Each manifest path
is relative to the manifest's directory. The candidate receipt must identify
its actual language, output hash and size; an input or core hash is not a
substitute for the candidate output identity.

```json
{
  "schema": "sgp-five-readback-inputs/1",
  "targets": {
    "EN": {"candidate": "EN.nds", "receipt": "EN.json", "baseline": "r4-EN.nds"},
    "IT": {"candidate": "IT.nds", "receipt": "IT.json", "baseline": "r4-IT.nds"},
    "FR": {"candidate": "FR.nds", "receipt": "FR.json", "baseline": "r4-FR.nds"},
    "ES": {"candidate": "ES.nds", "receipt": "ES.json", "baseline": "r4-ES.nds"},
    "DE": {"candidate": "DE.nds", "receipt": "DE.json", "baseline": "r4-DE.nds"}
  }
}
```

From the repository root, choose an existing manifest, the pinned CRLF charmap
and a fresh report path outside `source/`:

```sh
PYTHONPATH=source .venv/bin/python -B source/verifiche/readback_133.py \
  --manifest "$MANIFEST" --charmap "$CHARMAP" --json "$REPORT_JSON"
```

`--output` is an alternative to `--json`; supply one only. Charmap and report
paths resolve relative to the invocation directory. The charmap SHA-256 is
`58861d34f40623fd2a9b29c10a79ee2ec872182285a288381759a3b251412ded`.
Inputs must be distinct regular files without symlink components; the output
must be fresh and must not alias an input. The tool authenticates baselines
against the unchanged [r4 game contract](../../distribution/game-1.3.2-r4.json)
and checks each candidate's own receipt. It requires the project dependencies
above but does not invoke a compiler or emulator. An exit of 0 denotes a
passing scoped static readback; a refusal or failure exits nonzero.

For the first, pre-onboarding candidate, the reviewed public interface repeated
the five-candidate readback successfully:
its schema, result, five targets and limitations match the earlier report, with
additional provenance. The run took 4.813 seconds and sampled process-group
RSS peaked at 1357.56 MiB; this is not total unique host memory. The earlier
readback remains separate evidence. Active logical files and mapped ARM9 are
covered, while unindexed historical physical bytes and repacking gaps are not
exhaustively compared. Static readback does not prove gameplay, a complete
pivot, SAVE, cold restart, device behavior or timing.

## First candidate: raw-save and visual checks

Seven case-language cycles passed on the exact five pre-onboarding candidates: the same legacy
and advanced fixtures were each tested with EN and IT, plus one distinct fixture
for each of FR, ES and DE. These are five unique original fixtures, not seven.
Each used a copy through Continue, native SAVE and cold restart. In every cycle,
the save exports after SAVE, cold restart and UI use were byte-identical;
original fixtures and input working copies remained unchanged.

The checks preserved profile data apart from normal playtime, party and boxed
Pokémon, storage bytes apart from the native dirty-bitmap reset, Bag and existing
Plus settings, and progress flags and variables through lossless HF02 migration.
All seven cases migrated to HF02. The advanced fixture contains five party
Pokémon, 113 boxed Pokémon and three occupied expanded Bag slots; it was used
for both EN and IT and is one fixture. The test does not cover every possible
save or expanded slot.

Visual review covered the loaded, saved and cold field screens for all seven
cycles, and the native Options and Guide screens for all five languages. This
was a host interpreter and software-renderer check, not native-speaker language
certification. Full natural pivot and battle coverage, candidate gameplay timing
and physical-device validation remain pending.

## Host composition verifier

Two earlier EN inert composition attempts stopped under sampled RSS guards:
2165.5 MiB against 2048 MiB, and 4480.4 MiB against 4096 MiB. Neither attempt
produced a ROM. These are historical stops, not measurements of the revised
verifier or of an accepted candidate.

The host chain verifier now reconstructs stage boundaries in two reverse passes.
The first records hashes of the actual boundaries and checks the reconstructed
cold UI before calling the independent UI verifier. The second compares each
boundary with the first pass and checks stage receipts, grants, invariants,
confinement and owner readers. Both passes check the global reconstruction
byte for byte. The host admission path also extracts only the cold UI image.
The compatibility API `intermediate_images` still returns the complete list and
therefore retains an image per stage when explicitly used.

The number of reverse reconstruction steps is linear in the stage count;
small boundary hashes and receipt metadata remain proportional to that count.
Stage readers now run in reverse order. If multiple stages are invalid, a later
stage may supply the first diagnostic; the checks within each stage and the UI
gate remain in place.

A suite of 104 synthetic tests passed, including comparisons with the previous
algorithm, rejection cases and fault injections. In a `tracemalloc` test using
24 stages and 256 KiB images, the bounded verifier peaked at 802,787 bytes,
compared with 6,823,488 bytes for the previous list-based verifier; a three-stage
bounded run peaked at 790,472 bytes. These figures measure Python allocations in
that synthetic test, not whole-process RSS, a complete ROM build or Nintendo DS
memory or performance.

Four EN/IT host compositions of the first, pre-onboarding candidate completed
under the 4096 MiB sampled RSS guard:

| Host composition | Elapsed seconds | Sampled process-group peak RSS (MiB) |
| --- | ---: | ---: |
| EN inert | 457.401 | 3852.2 |
| IT inert | 473.861 | 3974.3 |
| EN player | 458.502 | 3502.56 |
| IT player | 472.729 | 3754.39 |

For the current onboarding successor, EN/IT inert compositions took
457.602/471.648 seconds with sampled peaks 3448.86/3778.66 MiB; EN/IT player
compositions took 460.335/470.630 seconds with sampled peaks 3516.34/3659.48 MiB.
FR/ES/DE composition took 7.661/7.595/7.792 seconds with sampled peaks
2191.69/2194.56/2200.12 MiB respectively.

These are host elapsed times and sampled process-group RSS, not total unique
host memory, DS memory or gameplay performance. Compiler descendants outside
the sampled process group and sampling intervals limit the RSS measurement.

## Plus ownership context

An inventory review covered 70 existing contract records across 41 distinct
owners; this is not a complete ROM inventory or 70 new semantic qualifications.
The older standalone Guide's ARM9 code and data are distinct from the current
overlay-54 and resident components. Guide and Settings share current bridge,
font and resource dependencies. The focused review proposed no gameplay patch.

These are five Plus candidates; FR/ES/DE derive from the EN gameplay core with
their localization inputs, rather than five rebuilt regional retail engines.
The helper grows from 68 to 74 bytes within the same 128-byte reserve. The
effect wrapper's 4-byte push and modifier wrapper's 8-byte push are unchanged
between helper versions. Neither this layout nor unchanged total ROM sizes
establishes a reduction in game memory. No reduction in crashes or freezes,
gameplay latency, FPS cost or energy use has been demonstrated.
