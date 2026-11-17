# 1.3.3 corrections and validation

This report connects the 1.3.3 corrections to their source owners, exact game
identities and observed results. It describes prepared candidates, not publication,
a personal installation or physical-device acceptance. Detailed historical
experiments keep their original identities and limits.

## Exact game targets

The five delivery targets are:

| Language | SHA-256 | Bytes |
| --- | --- | ---: |
| EN | `d6fbdf8bd0aec528a336713b497847da36b467001b2f550c9cc583679c3e5c7d` | 152786844 |
| IT | `1a889803ff3598c3bab89f036c007cd4c0163a1b2f80377794c9e46baccd34cd` | 159029760 |
| FR | `df8b6aad56a3422fef5597f9d8e4123b58e9f60d62e5510b5a319009bf1069b8` | 162560728 |
| ES | `0642b270a151aeedb202fc9d3b578a54158817c98ebd06c58d7c3564cb0b1b40` | 162490072 |
| DE | `26d2a09913a52fc1728dbf682dc94ec49ac6fb8d2817cde4debde7159e42ae2a` | 162932492 |

EN, IT and ES retain the onboarding-successor bytes. FR and DE add only the
localized Training corrections described below. Recomposition reproduced their
recorded full-file and receipt hashes exactly. The machine-readable
[game contract](../../distribution/game-1.3.3.json) identifies game outputs;
package and patch verification are separate from gameplay acceptance.

FR/ES/DE compose regional presentation around the authenticated English Plus
core. These are five presentation targets, not five separately rebuilt regional
retail engines or a complete compilation of original HGSS from C.

## U-turn and flinch-item helper: two corrected decisions

The [helper source](../../features/type-consumers/uturn.S) and
[composition module](../../sgp131/uturn_flinch.py) correct two defects in the
existing Plus helper:

| Trigger in the examined domain | Before | After |
| --- | --- | --- |
| Unmarked modifier fallback | Native getter could receive altered battler/flag arguments. In the item-221, roll-9 counterfactual the modifier was 0. | Original `(context, battler, flag)` arguments survive; modifier is 10 in that case. Both versions draw RNG once; the modeled script requests change from `[]` to `[14]`. |
| Native negative damage word, such as −200, with no item | A bit-16 test could consume the damage as a snapshot and enter the flinch/RNG path. | Snapshot recognition requires upper 16 bits equal to 1. The native word remains −200 instead of being cleared to 0; requests change from `[14]` to `[]`, and RNG draws from 1 to 0 in this case. |

The resulting 74-byte payload has SHA-256
`fd3e38715bd40098080f7375f3d16a96044d359dda4c5c1436cb9bbbf55f478c`.
It stays within the existing 128-byte reserve; the preceding 64 bytes belong to
another owner and remain unchanged. Entry points, producer, save layout and
identifiers are unchanged. The marker-domain argument covers the examined valid
writers and bounded loops; it does not cover corrupted state or arbitrary
external writes.

The pre-fix targeted regression failed both defects. Thirteen helper/compiler
tests passed after correction. Native counterfactuals passed 53 cases on each
of the authenticated EN and IT r4 inputs, with the new helper applied in memory.
Native getters, cache, RNG and division execute; the producer is interpreted and
ability/script transport is modeled. Eight focused host tests and a CPU-free
recheck of the existing raw observations strengthen RNG count, seed, output and
repeat-continuity checks.

Here `flinch=true` means a request for modeled script 14. It does not prove that
the script executed, a status changed or a target lost its turn. Frequency and
player-visible impact in natural battles remain unmeasured. No complete natural
pivot or ordinary Shell Bell healing-loss result is established. The unchanged
helper and closure bytes in successor readback support reuse of those finite
results, without creating a new natural-battle result. Commands, input hashes
and historical evidence are in the
[U-turn validation report](uturn-fix-1.3.3.md).

## BLZ: reject a truncated compressed pair

The shared [host decoder](../../sgp12/blz.py) and retained copies in
[overlay](../../features/overlay/tools/overlay_patch.py),
[NPC](../../features/npc/tools/overlay_patch.py) and
[animation](../../features/anim/tools/overlay_patch.py) now require two bytes
inside the compressed region before reading a back-reference pair.

Previously, a token with only one compressed byte remaining could borrow its
second byte from the uncompressed prefix. Four authored malformed streams passed
the trailer/size gates and were accepted before correction. The malformed streams previously decoded to 17 bytes. The guard
`src - stop >= 2` rejects them before either pair byte is read; a complete
16-byte control and a 96-byte compressor round-trip retain their bytes. Complete pairs,
literals, distance/length checks and existing allocation guards are preserved.

The [parameterized regression](../../sgp12/test_lib.py) covers all four decoder
copies, the four malformed streams, a complete pair with a raw prefix, and
compressor round-trips. The targeted decoder/preflight suite passed 14 test
methods. Those are finite parser cases, not a claim that every decoder input is
safe. This correction changes host build tools; it is not an installed game-code
fix, crash-frequency measurement or gameplay performance result.

## Training menus: seven catalogue aliases corrected

The native renderer uses font 4 and fixed 96×32 px windows. `stat7` has seven
choices; `service6` has six. Ordinary field dialogue's 216 px bound does not
apply. Measurements below use the actual authenticated font's advances.

| Locale / alias | Before | Advance | After | Advance / margin |
| --- | --- | ---: | --- | ---: |
| DE `m:385:64` | Spezial-Verteidigung | 129 px | Sp.-Vert. | 61 / 35 px |
| DE `m:385:24` | Kronkorken kaufen | 116 px | Kronk. kaufen | 87 / 9 px |
| DE `m:385:25` | Kronkorken abholen | 122 px | Kronk. abholen | 93 / 3 px |
| DE `m:385:27` | So funktioniert’s | 109 px | So geht’s | 60 / 36 px |
| FR `m:385:21` | Entraîner les IV | 104 px | Entraîner IV | 80 / 16 px |
| FR `m:385:24` | Acheter des Capsules | 134 px | Acheter Caps. | 88 / 8 px |
| FR `m:385:25` | Réclamer les Capsules | 137 px | Réclamer Caps. | 93 / 3 px |

Each alias has counterparts in banks 557 and 630. Independent cartridge readback
finds exactly 12 changed word streams in DE and 9 in FR against their original
onboarding successors. Only message archive/FAT 156 changes among 513 logical
files. The other 512 payloads, native core, font, scripts, message IDs, menu values
and unowned common-prefix bytes are preserved. Derived header/Guide descriptors,
archive geometry and append padding are checked separately. The stat value order
`0,1,2,4,5,3,255` and service values `0..5` remain unchanged.

The [portable checker](../../localization/TRAINING-FIT.md) authenticates the ROM,
explicit language identity, charmap, native dispatch/renderer chain, overlay
layouts, font, script mapping and aliases. Installed strings and optional
catalogue proposals have independent results: a corrected proposal cannot hide
an old installed overflow. Nineteen owned synthetic tests and the 77-test
localization suite pass without embedding extracted font advances or bitmaps.

Both finite profiles pass for all five exact target identities above. This is
10 profile/language cells, not a scan of every menu. Unchanged Spanish Buy/Claim
labels measure 96/96 px, French Info 95/96 and German Special Attack 95/96;
these controls are not newly demonstrated overflows. Advance width is not an
analytical ink bound. Native-speaker certification remains outside this result.
Source ownership, exact aliases, reproduction and historical composition details
are in the [localization report](../localization.md).

## Observed menu and save coverage

On exact DE `26d2a099…ae2a`, a normal Continue route showed the service and stat
menus, all cursor positions and Back/Leave. A native SAVE, process exit and cold
Continue on a genuine prepared German copy preserved five party Pokémon,
113 boxed Pokémon, three expanded Bag slots, money, Plus settings and the
Training policy/reward ledger. That copy's earlier explicit Legacy/reward setup
is separate from preservation across the update. No purchase, claim or IV/EV
application was selected. The earlier stat-only DE `44d398bb…8ce0` had two
separate raw-save cycles; those results are historical and are not relabeled as
current-target cycles.

On exact FR `df8b6aad…69b8`, the same bounded menu tour and SAVE/cold sequence
preserved the prepared advanced copy, generation 116→117. That copy had been
written by the German test candidate; it is a host presentation fixture, not
proof of a normal language-switch update route. A separate original French
fixture without Plus data passed Continue/SAVE/cold Continue, generation 1→2,
with one party Pokémon preserved. Neither cycle selected a purchase, claim or
IV/EV application. The labels appeared complete in observed host images; this
is not an analytical ink or hardware qualification.

The earlier five onboarding successors passed seven raw-save/cold cycles on
five unique original fixtures: two fixtures each exercised EN and IT, and one
regional fixture exercised each of FR, ES and DE. That evidence retains its
original identities. All original save fixtures were preserved. These cases
do not establish universal save compatibility or cover every expanded Bag slot.

## Active 1.3.3 labels

The shared Continue/New Game onboarding title is `Sacred Gold Plus V1.3.3`,
entry 20 in the 29-entry, 1008-byte bank at `0x023DA800`. Readback verified the
new title, the other 28 unchanged raw strings and the adjacent 16-byte canary
in all five onboarding successors. The final DE/FR readers preserve that bank
byte for byte, supporting the same title on their exact successors.

The Plus interface's active `VERSION` entry (UI resource key 2) is `V1.3.3` in
all five languages. Source copy and scoped candidate readback agree; the final
DE/FR message changes preserve that UI resource and its descriptor. EN/FR
Continue prompts received host visual review in the onboarding campaign;
New Game's shared title route is statically linked rather than newly played.
Options/Guide body review alone is not a version-label observation.

Retired onboarding entry 0 remains historical and inactive. Historical source
versions and old experiment strings are not globally replaced. The DS header
and banner are unversioned. These checks do not establish a physical-device
installation, complete natural battle acceptance, reduced crash frequency,
gameplay speed, battery use or game-memory improvement.
