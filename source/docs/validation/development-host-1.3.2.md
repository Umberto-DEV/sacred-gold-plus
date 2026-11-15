# Development host qualification — 9 November 2026

The existing 1.3.2 game remains unchanged. This investigation rebuilt the host
measurement bench, qualified specific UI/state/animation contracts and exercised
one private, opt-in graphics variation. No performance repair was justified by
these cases. The graphics variation is a pipeline demonstration, not a release
or an aesthetic improvement claim.

The earlier [Options/Guide lifecycle report](ui-lifecycle-1.3.2.md) retains its
own results and limitations. Its Guide-navigation reload hypothesis was not
retested. Private protocols, commands, raw measurements, failed harness attempts
and receipts are retained under `local/validation/sviluppo-1.3.2/`, with one
directory per distinct question. Plans and assistant notes are not public source.

## Exact inputs and tools

Source base: `a912b3e155150e604d1bf5cb5bd5a18b8cf13b8a`, with the documented
build-time graphics extension in the working tree. The accepted
[r4 game contract](../../distribution/game-1.3.2-r4.json) is unchanged.

| Image | Bytes | SHA-256 |
| --- | ---: | --- |
| r4 EN baseline | 152786844 | `2e30d6960bb059615fca7527700d86f8282e82ccbe99bf62e22f027453dc3d3d` |
| r4 IT baseline | 159029760 | `13ebac02bdea3036511773587e6603ce6834e25f4b13d1a4662c3e954bfd5d4a` |
| Private silver-palette EN | 152786844 | `21e4b6fd853cb34f863426db48f319c8d3185299da910ae9e8d966a06ad93d4d` |
| Private silver-palette IT | 159029760 | `fc4c9f541ede75d2842fd3a8358fb6eda4842822ea79b9a57b9ecc0a4ee1dc05` |

The populated original raw-save fixture is
`84536ef9760569460d948302a8cac4c5e7e3a423a957e823185ac1dd516c2bfa`.
It contains five party Pokémon, 113 boxed Pokémon and three occupied expanded
Bag slots. All gameplay used copies. No personal installation, original-save
replacement, publication, release asset or tag change occurred.

Host: macOS ARM64, Python 3.14.7, Apple clang 21
`clang-2100.4.1.1`, installed SDK 27.2, CMake 4.4.3, Ninja 1.13.2 and Unicorn
2.1.4. Compiler identity is checked through the existing production guard.
The host runtime was rebuilt from `source/runtime` and the exact official
melonDS core `906e9ebb27da8c6a715cd7abab4abfe8a8d29427`, with only the two
approved observation patches. Interpreter and software renderer; FreeBIOS and
generated firmware; fixed default RTC `2026-09-05T12:00:00`. No Android or
Nintendo execution is represented by this configuration.

Runtime SHA-256:
`e66bd179962a4de2086a42494e59425214e4499bbaa3e53f76061832b3d2d472`.
The old reference runtime was `81e58a86e3d055696d7a661eca9e91e9e23f7a06a1dcd862badd78d4c58877e1`.

## Rebuilt bench and metric boundaries

The `banco-ricostruibile-2026-11-09` campaign records the detached core checkout,
exact patch verification, configuration, compiler/SDK probes and binary hashes.
Sixteen existing runtime contracts passed with no skips. Eight synthetic
wait-loop cases produced their expected outcomes: four branch cases passed and
four endian-error cases were rejected. Two initial SDK invocation failures
remain recorded; the installed SDK was then explicitly qualified.

An IT Continue → Guide → Down/Up → close anchor ran for 4,338 guest frames.
The old/new runtime and four new-runtime trace OFF/ON/ON/OFF replays had identical
common guest columns, captures and exported raw SRAM. Median host RunFrame time
was 2.183/2.180 ms OFF and 2.132/2.168 ms ON; overlapping drift does not establish
zero overhead or a speed improvement. The RunFrame timer excludes scene reads,
CSV, audio/output writing. Trace toggling does not isolate the fixed hooks or
the total observer cost. Guest CPU cycles, VRAM peak and display pacing remain
unmeasured. Map/X/Z readback matched the single fixture anchor 293/8/17; the
object-pool count is not a general semantic census.

## Functional map and focused contracts

The private functional map covers all 39 existing feature owners in 58 behavior
rows, with activation provenance, caller/lifecycle, ownership, known budgets,
HGSS reference boundaries, actual test evidence and gaps. It distinguishes
historical code, active shared helpers, installed inert code and host support.
It is not a coverage percentage or a justification to remove resident code.
Installer, readback and test independence was retained.

| Case | Verified result | Boundary |
| --- | --- | --- |
| Font/topology work | Four prepared EN/IT Guide/Options ARM cases. Idle paint/font-check calls: zero; admission checks: four/two per tick. Named guard family: 32.586–34.161% of measured dispatches, below the predefined 50% dominance hypothesis. Observer/control effects and total dispatch counts match. | Prepared source-current native contract with explicit transport, input and scheduling seams; not a whole-game CPU profile. No guard removal or speedup. |
| Bag/Training save boundary | Exact r4 EN/IT payload qualification. Three modes plus three existing controls passed. Injected mirror-readback status 5 permits native-only commit; active Training/Shiny journals refuse conservatively. Retry reaches status 1, preserving extra slots and journal RAM. | Flash/OS and final native commit are seams; no hardware flash-fault or native generation-rollback proof. Successful receipt is `check-attempt3-bounded.json`. |
| Borrowed battle tables | Both 256-byte blocks and six overlay hooks match EN/IT. Bag/Party follow replacement contexts; protected old pages, OFF, NULL and address reuse preserve ABI and allow only stack writes. | Prepared ARM contexts, including an explicit native getter seam for Bag; not two natural battles. Earlier complete Party data comparisons were reused, not repeated. |
| ANIM2/copy ownership | Current code/tables/parameters/wrapper/hook readback and recompilation match. A 900-call idle → move gate → resume → OFF → ON sequence has a 48-tick period and maximum Y/scale deltas of one. Two complete B poses last 10/11 ticks at peak index 4. All 29 ANIM2 and eight copy-wrapper contracts pass without skips. | Synthetic task scheduling with native attribute code. Tick is not video frame. Natural battle cadence, continuous presentation pacing, readability and hardware remain unqualified. |

ANIM2 observer/control have identical complete RAM and attribute sequences;
319,778 dispatches and 40,714 confined writes were recorded. The initial probe
failed because it omitted the later wrapper's autoload placement. The corrected
probe places authenticated bytes and verifies the return PC on every call.
This was a harness failure, not a game finding.

## A minimal authored graphics pipeline

`sgp13.training.cap_graphics` generates the existing 32×32 4bpp Cap artwork.
Its new keyword-only `silver_mid_color` accepts a BGR555 integer; the default
`0x4E73` preserves all previous output. Gold is unchanged. Three focused tests
cover stable art/defaults, confined variation, invalid input and input immutability;
they are registered in the existing Class A runner. No runtime setting or
default build opts into the experiment.

The native item mapping is unchanged: items 113/114, NitroFS `a/0/1/8` file 147,
members 797–800. Generation and unchanged NARC roundtrip match both r4 images.
The private variation uses `0x4E74` for Silver color 2. Independent whole-ROM
and manual NARC readback find exactly one changed byte: EN 137333832 or IT
142494280, member 798 offset 44, `73` → `74`. All other 800 members and every
other cartridge byte, including code, IDs, FAT, parameters and Gold, are exact.
The editable private export contains only authored indices/colors; native
container headers and retail resources remain private. No 3D converter is
required for this 2D resource. VRAM transfer/peak was not measured.

On a copy of the populated save, normal Continue, walking to Blackthorn Mart,
the adviser's Original rules confirmation and one Silver Cap purchase succeeded.
The original had no Caps. The resulting item occupies expanded Items slot 168,
quantity one, with exactly 10,000 deducted. It appears with localized name and
native rendering. No RAM write, freeze, cheat, warp or test-save copy-back was used.

Cold baseline/variant replays in EN/IT show exactly 80 changed pixels, all within
the Cap icon at X14–29/Y245–252 in the combined framebuffer. Other pixels and
common guest-frame columns are identical. Two page visits per language agree.
Initial cold probes opened a different Bag page and therefore showed zero pixel
differences; those probes are retained. Only the corrected page-arrow replays
establish the Cap comparison. This is no visual-quality or general cache claim.

## Raw-save copies and target matrix

IT native SAVE advances generation 113 → 114; normal cold Continue succeeds in
both languages. EN native SAVE then advances 114 → 115 and another cold Continue
succeeds. All cold raw exports equal their input save byte-for-byte. Thirty-nine
focused checks pass: party, all boxed/storage data except native dirty-bitmap
reset, native inventory, existing expanded slots and Plus settings are preserved.
The original fixture hash remains unchanged.

Acquisition intentionally changes money, location, one expanded slot and the
explicitly enabled Training journal. The audit separately accounts for the
finite HF02 migration, native egg/friendship counters increasing by 11 during
walking, and temporary variable `0x4000` changing 0 → 1. The precise producer
of that temporary variable was not traced; the audit pins its exact value and
compares all other variables/flags. This is not a claim that every native save
byte stays constant during gameplay. The second EN save preserves these data,
jobs, rewards and shiny settings apart from native bookkeeping/playtime.

| Target/input class | Evidence in this investigation |
| --- | --- |
| Host, accepted r4 EN/IT UI | Earlier lifecycle/save matrix retained; new bench anchor and focused contracts above. |
| Host, private palette EN/IT | Whole-image readback, natural acquisition on one populated fixture copy, localized icon comparison and native SAVE/cold sequence above. |
| Legacy/no-Plus fixture | Earlier r4 lifecycle report's two-language copy checks; not an additional private-palette fixture or universal migration result. |
| FR/ES/DE | No new prototype or runtime claim. |
| Android | No connected device; no installation or new device check. |
| Nintendo models/loaders | No execution; no timing, loading or save-compatibility claim. |

The small-room prototype remains unimplemented: the prepared Map Studio
converter directory lacks `g3dcvtr`; the pinned apicula checkout has no qualified
Nitro reimport path. New map/header IDs, geometry/collision, matrix, connections,
warps and old-save entry have not been qualified. A 2D icon roundtrip or an
editor project does not establish a playable 3D area. No proprietary converter
was downloaded. The maintainer subsequently excluded the new-area prototype;
these historical gaps are no longer dependencies of the remaining work.

The subsequent [natural battle cadence report](animation-cadence-1.3.2.md)
closes the remaining host animation case with a separately qualified opt-in
observer. The prepared900-call results above retain their original scope.
Physical display pacing and Android/Nintendo remain unverified.

Reproduce the public recipe tests with:

```sh
PYTHONPATH=source .venv/bin/python -B -m unittest sgp13.test_training_graphics -v
```

Other exact commands and bounded logs remain with their named private campaigns.
Do not relabel historical evidence or these prepared contracts as release,
Android, Nintendo or full-playthrough acceptance.

Independent final review passed within this host scope, with no open findings.
The new test's Class A routing was corrected and exercised; environment,
structural inventory, working/index diff checks and the 1,167-file public
contract passed. No full suite was repeated. Cleanup removed only reproducible
build intermediates and replaced private PPM captures with verified lossless
PNG equivalents, retaining exact pixel data and reconstruction hashes.

## Source and native-component follow-up — 10 November 2026

A new read-only investigation authenticated the canonical retail, base1.1 and
unchanged r4 EN/IT files before and after inspection. It checked continuity of
the 28 recorded UI/mechanical receipt links per language through the exact r4
target hashes above. This reuses historical composition results; it is not a
new reconstruction or acceptance of the current source snapshot.

Each original r4 receipt records 816 source pins. The current snapshot has 817:
the authored Cap-art test is new; the downloader, its test and the opt-in Cap
recipe differ. All 79 C files, 54 headers and eight assembly files included in
those pins remain identical. These counts describe the receipt's source scope,
not the complete retail game or equivalence of every execution path.

The normalized inventory covers ARM9/ARM7 main sections and all 129 ARM9 overlays
in each of six exact images. ARM7 is identical across these inputs. Direct raw
header/table/FAT reads independently confirm overlay routing; section parsing
and decompression use ndspy 4.2.0, without a second decompression implementation.
No game bytes, extracted tree or replacement ROM were produced.

For EN, retail to base1.1 changes six existing logical components and adds one
section. The corresponding IT comparison changes 120 logical components and
11 metadata-only components and adds one section. These are **not bug counts**:
the regional retail executables differ. All 129 base1.1 overlays are identical
between EN/IT in logical content, runtime metadata, file IDs and packed flags;
the same holds for r4. Across languages 135/137 base1.1 components and 134/137 r4
components have identical logical content and selected runtime metadata.

Base1.1 to r4 changes 19 existing logical components per language, with a section
removed at one RAM start and a section added at another. Section identity uses
the starting address: this layout change does not demonstrate code deletion.
The inventory records component-relative difference ranges; it does not map all
differences to functions, distinguish all code from data, establish ABI safety
or certify a full source port. Full filesystem/NARC and inter-component gaps
are outside this inventory. No closed gameplay campaign was repeated.

While inspecting existing validation tools, a separate source defect was
reproduced in `verifiche/collauda_repellente.py`: C3 could pass with zero or one
retained PPM capture, provided its other gates passed. Three CLI regressions
failed on the previous implementation. C3 now rejects fewer than two captures;
`latest.ppm` still supplies no additional sample. All 12 tests in the existing
`verifiche.test_runtime_gate` suite pass, including unchanged-image and missing
rearm controls. This is synthetic tool evidence, not a new Repel gameplay test.
The gate still compares captured file hashes and does not independently prove
message content or the timing of the captures around expiry.

The new private campaign is `riconciliazione-source-rom-2026-11-10` under the
existing development-validation root. Its logs retain the initial failures,
bounded inventory, source/ROM identities and independent review. The inventory
took 3.001 s with 729.48 MiB sampled group RSS; sampling is not an absolute peak.
No compiler, dependency, source pin, save layout, personal installation or
release artifact changed.


## Battle Bag work observer — 10 November 2026

The explicit runtime derivative adds a bounded ARM9 interpreter dispatch
observer for authenticated battle Bag sites, OFF by default. It copies entry
registers, matches returns by PC/SP/CPSR mode and records incomplete or invalid
spans. It does not read or write guest memory. Enabling it requires a separate
strict core patch selection; the normal verifier rejects that derivative.
Eighteen explicit runtime/CLI tests pass without skips. Independent review
found and corrected an incorrect Thumb anchor in a fixture and an unfinished
observation that previously exited successfully without a report. Failure now
returns an error after attempting diagnostic output.

Current E3c executable SHA256 is
`a23cf932fbb87fb7da8f5aecab9a0eb9d6479885d5e2b98f33399357919a2a8e`.
Earlier E1/E2/E3/E3b reports keep their original identities. Exact EN/IT
observer OFF/ON controls preserve guest columns, pixels and SRAM. For a private
192-byte helper experiment, 2,420 per-frame RGB/ANIM/RNG samples per language
match the r4 controls. Two normal battles per language include field exit,
a new encounter and second Bag entry; sparse checkpoint pixels and SRAM match.
These routes do not establish physical display/audio pacing or a full playthrough.

The r4 helper was rebuilt to its exact162-byte payload. Attribution confirms
the BattleContext owns the resident ItemData and the Bag helper owns no heap.
A first166-byte experiment was rejected because a fallback control changed
pixels and teardown by one guest frame; its positive results were not reused
as acceptance of its successor. The private192-byte successor changes only
the admitted cache continuation, preserving original fallback instructions,
callsite, stack and overlay hook. Its ROM changes are confined to the existing
256-byte ARM9 grant. EN SHA256:
`d242bf3df9a28342e3fd3c25a11cc0f1f67d440152f25976f75e5731298fc6cc`;
IT SHA256: `6987e0b8d50ea5bbc7e402f72bc1dff653a6398818731674bad08e27bee48eb1`.

The pure helper differential covers537item IDs/513resident records and21guard
cases per language, plus6,000 seeded prepared ARM cases. Ten new independent EN
pairs, five in each order, reduce the observed421-slot list span from153,896
to140,003 same-mode dispatches, with identical checkpoint pixels, SRAM and
observed Bag-endpoint frames. Independent readback reconstructs4MiB final RAM for all20runs:
bytes outside the owner match, and the entire owner including padding/canary
matches each ROM. Guest semantic columns match; changed ARM9 boundary PCs are
recorded separately. The three-native-fallback control, small5-slot and valid
maximum515-slot inventories, and animationOFF retain their guardrails. Maximum
mixed-I/O list spans include other scheduled work and do not measure only the
helper's reduction.

A dispatch is one interpreter step, including each half of a Thumb BL and
failed ARM conditions. Same-mode spans may include unobserved threads; they
are not busy CPU time, hardware cycles or cache miss counts. The measured
helper stack-write footprint is an isolated prepared ARM result, not a global
stack bound. Payload grows by30bytes inside the same grant: no reassignable
RAM, VRAM or ROM space is demonstrated. No game source/default, accepted r4,
save layout, release asset or personal installation changes here. Eight successor raw-save cells (legacy, populated Plus/Bag, prepared5-slot
and maximum515-slot inventories in EN/IT) pass Continue, one native SAVE and
a cold process restart, with25 protected-field criteria each. Generation
increments once, progress/Pokémon/settings/registered and extended Bag slots
are preserved, and cold exports match the newly saved raw bytes. Original
fixtures remain unchanged. Both languages have separately reviewed captures.
This does not establish universal compatibility or active Training-job coverage.
Android/hardware cells remain separately pending.


### Separate Android AVD follow-up

The same exact private EN/IT successor images were exercised on the existing
API35 ARM64 AVD with4KiB pages. Installed APK53 is SHA256
`8ace1b87edb37a4368f16b0e8b42e28e0d05235f2ae7722feb4c3266a7145187`.
Its guest software renderer and threaded rendering are configured, and the
JIT option remains enabled. Effective native FastMemory status was not queried;
a startup ftruncate warning alone does not establish mapping/JIT success or failure. ROMs
and copied raw saves were isolated through a normal SAF directory grant,
without an APK update, personal installation or settings reset. Only one ROM
was active on the temporary path, with hashes checked before each replacement.

Normal Continue and field encounters lead to Bag/HP-PP selection, closure,
reopening and the native Party page in both languages. Encounter/input/RTC
conditions differ between runs; these are functional observations, not a
causal Android speed comparison. A short Party input in the r4 control was
rejected because its capture still showed the command page.

Four successor raw-save cells, EN/IT with legacy and populated Plus/Bag inputs,
complete native SAVE and a cold process Continue. Native generations1→2 and
113→114, protected data and existing settings are preserved. Each cell passes
24 existing checks on data/identity, some conditional, plus an actual cold-file
byte comparison. These are100 case criteria, not100 independent properties.
Android provides disk readback here; no guest SRAM-memory/UI export is claimed.
Source fixtures remain unchanged. Captures and independent strict decoding
corroborate the completed saves and resumed field states.

Rejected attempts remain explicit. The first bounded AVD session expired
before an IT SAVE began. One legacy attempt stayed on the overwrite prompt;
another was paused while the native message still said it was saving lots of
data, producing a partial test copy that the strict reader rejected. Neither
was accepted as compatibility evidence or attributed to a game defect. The
completed legacy cases wait for the field/menu and verify CRC/generation before
exiting. Both AVD instances were stopped; no QEMU/controller was left running, and no
scheduled or background service was added.

Simpleperf task-clock access was denied. Process/thread accounting and meminfo
were readable, while Perfetto source enumeration alone grants no valid GPU
measurement. Observed thread names do not uniquely identify all worker roles.
Exact frontend pacing/audio-latency policy and hardware counters remain
unqualified. No Android CPU/GPU, Nintendo cache/TCM, physical display/audio or
input-to-photon benefit follows from these results. Physical Android and real Nintendo
targets remain pending; the released r4 and default game source stay unchanged.

### Continuation audit: sanitizer and corrected native-page control

The unchanged complete C++ observer test was additionally compiled with the
exact installed compiler/SDK under AddressSanitizer and UndefinedBehaviorSanitizer.
It passed with no diagnostics. Separate negative controls produced the expected
heap-buffer-overflow and signed-overflow diagnostics, confirming instrumentation.
Leak detection was disabled on this Darwin host. This covers the host observer
test, not the fixed-address ARM game helper or general game safety; sanitizer
execution times are not performance comparisons.

An image audit invalidated one earlier host control: the old sampler captures
named `party.png` still showed the battle command page. Equal hashes had not
established the intended native Party endpoint. Those captures and the erroneous
claim are retained with an explicit correction. Four new runs, r4/successor in
EN/IT, use the touch Back control and verify the second Bag teardown before
opening the actual five-member Party page. Each completes 8,478 guest frames
and 2,466 sampler rows. Checkpoint images, SRAM, non-timer sampler fields and
RAM outside the owner agree within language; independent review passes.
These runs replace only that missing control, not the ten paired list trials.
The separately witnessed Android Party results remain in their original scope.

Offline analysis of these four runs separates the Bag model/input-ready markers
from the first bottom-framebuffer hash exactly matching a retained reference
image. The reference-hash criterion occurs 35–36 guest frames after the Bag
injection command and 48–49 for Party, identically in r4 and its successor
within each language. This is a hash indicator corroborated at the retained
checkpoint, not retained RGB for every earlier matching frame. It does not
identify first partial pixels, scanout or earliest usable Party input. No
qualified Party input-ready marker or physical input-to-photon timing is claimed.
The work-count reduction did not change these specific guest-frame criteria;
it does not establish normal UI responsiveness or a hardware latency gain.

The subsequent native-input witness uses the unchanged E3c read/watch commands
and discovers the live Party task independently in every process. Four new
EN/IT r4/successor runs observe the game's sampled key edges, rather than only
the harness key mask. The first DOWN enables D-pad mode, the second changes
native focus 0→2, and B produces selection6, closing states25/26 and task unlink.
State, images, SRAM and RAM outside the owner agree within language. A ready
predicate at the end of a frame can precede the displayed page; it is not an
observed first executed polling instruction or a first-pixel endpoint.
This does not mean every underlying call has an identical frame stamp: some
native allocation/free calls occur one guest frame earlier, with the same
arguments/results and ordering. No heap-peak or reusable-memory benefit
is inferred from that change.

An additional EN control/successor comparison waits exactly16 neutral guest
frames after the second DOWN, requiring unchanged focus/readiness and no new
sampled key. Both then display the focus on Gastly. Immediate captures had
still shown the old focus. This establishes a bounded visual witness, without
identifying the precise pipeline delay or an input defect. The first successor
attempt exceeded the cumulative evidence-storage budget at final validation;
it remains rejected, with its complete raw evidence retained losslessly and
missing producer timing/RSS explicitly unknown. Only that successor was retried
under a larger budget declared before execution. The original paired list and
SAVE campaigns were not repeated.

### Android accounting and frontend presentation follow-up

Four fresh EN processes in A-B-B-A order use the same installed APK, renderer,
settings and protected input-save copy. Nine ten-second idle windows and24
visually checked Bag open/close cycles expose process and per-thread CPU tick
accounting plus sparse PSS/RSS readings. The first A's three contiguous windows
are a local A/A check, not three independent process replicas. CPU values use
the measured uptime interval and verified tick rate; non-atomic read skew,
timestamp quantization, thread churn and signed process/thread residuals remain
explicit. Memory readings are not peaks. Encounter/RNG/warmup differences and
the small process count prevent a causal ROM improvement or regression claim.

The cumulative `gfxinfo` probe does not identify Bag-frame timings. A separate
capability probe found real data on the exact BLAST SurfaceView layer. Two
supplementary r4/successor windows retain eleven overlapping read-only polls
each, with pending fences excluded explicitly and no history reset. Their
reference semantics distinguish desired, actual and ready timestamps in a
128-slot ring whose dump contains127 records. This follows the
[AOSP 15 FrameTracker reference](https://android.googlesource.com/platform/frameworks/native/+/refs/tags/android-15.0.0_r1/services/surfaceflinger/FrameTracker.cpp),
corroborated by the actual output format; the installed system binary was not
rebuilt to prove a matching source identity.

Independent merging verifies complete overlap in these two windows, with450
and427 new completed presentation records. These are virtual frontend
presentation observations, with distinct encounters and no accepted causal
benefit. They do not count produced/repeated/dropped guest frames, measure
RunFrame duration, GPU work, physical scanout, audio or input-to-photon latency.
The owned AVD stopped normally and the input raw-save hash remained unchanged.


## Native heap and bank qualification — 10 November 2026

A separately selected developer profile observes the six native ARM ExpHeap
APIs and common lifecycle entries. It adds bounded entry/exit order, parent,
CPSR and stack-context checks without guest memory reads, writes or clocks in
the interpreter observer. The exact E4d executable is
`09e12c130a222a3ff8c2d43098697e89ff05066a30cc942465b093be6959ccf7`.
The earlier E3c evidence retains its own identity.

The EN r4 pilot compares E3c OFF, E4 OFF and E4 Native ON. Across 8,478 frames,
2,466 sampler rows, ten RGB captures and start/end MainRAM and SRAM, guest
invariants agree; host timers are excluded. Fifteen runtime tests, three CLI
tests and the complete C++ test under ASan/UBSan pass. Darwin leak detection
is disabled. This does not sanitize the game ARM code or prove hardware timing.

Read-only metadata decoding and authenticated ARM routines execute only on
private memory clones. Sixty qualification cases, 1,764 native operations and
fourteen rejected invalid operands cover allocation, merge, resize, group and
alignment behavior on EN/IT code. A separate allocator model and independent
raw decoder reproduce the pilot's 3,756 API calls: 3,360 on heap5 and 396 on a
disjoint heap0. All eleven expected metadata checkpoints agree. Thread records
are read from MainRAM; DTCM stack addresses are checked as numeric intervals,
with no invented DTCM unwind. Six IRQ-enabled explicit frees remain permitted;
no general absence of preemption is claimed.

The 3,361 heap5 transaction states include the initial state. The maximum
occupied region is 358,280 bytes during Party opening; the minimum largest
free NNS payload is 312,240 bytes during teardown. These are extremes of the
complete Bag-plus-Party pilot, not a Bag-only or global transient peak.
Completed API states exclude intermediate stores, arbitrary writers, DMA/ARM7
and unknown lifecycle. Capture hashes, frame epochs and the complete checkpoint
set are checked separately from allocator semantics; a void Free return value
is not interpreted as freed bytes.

Nine passive VRAM control watches cover frames 6,013–8,478. The decoder agrees
with 2,312 configurations of the pinned core's actual bank-mapping functions,
including aliases, collisions and partially exposed banks. The pilot has seven
segments and two mappings. All 656 KiB remain assigned as physical backing;
128 KiB belong to ARM7. The submenu moves 32 KiB to LCDC. Those values are
configured capacity, not live allocations, free storage or reclaimable bytes.
The command capture at frame6,012 has no register sample and remains unknown.

Failed probe runs remain rejected: a duplicate dump name, then an exceeded
storage budget. The latter did not return exit/time/RSS receipts; those values
remain unknown after lossless recovery. A fresh bounded run supplied the accepted
receipt. Earlier protocol prose misstated the default RTC as2000; actual pinned
source, arguments and every session record prove2026-09-05 12:00:00. The erratum
preserves the historical records and changes no measured timeline.

No game ROM, personal installation, save fixture or distributed asset changed.
The same pilot also qualifies the exact private successor and Italian observer
controls, as recorded below. Physical Android/Nintendo targets, audio and
presentation remain pending.


The completed EN/IT comparison has nine admitted acquisitions and two retained
rejections. Within each language, r4 and the private successor have identical
allocator state sequences and all eleven MainRAM checkpoints outside the exact
256-byte owner. Sampler pixels/RNG/input and configured bank budgets agree.
Four EN allocations and six IT allocations plus two frees occur one guest frame
earlier; five EN and six IT sampled ARM9 PCs differ. Equal transaction peaks do
not assert identical occupancy or buffer duration at every frame.

| Complete Bag-plus-Party window, r4 and successor | Native API calls | Heap5 states | Max occupied region bytes | Min largest NNS payload bytes |
| --- | ---: | ---: | ---: | ---: |
| EN |3756|3361|358280|312240|
| IT |3738|3343|358428|312232|

The maximum in both languages belongs to Party opening. The two Bag-only
phases peak at347276/347288 bytes EN and347280/347292 bytes IT, with carried
initial states included. Languages are not causal replicas of each other.
No heap or VRAM bytes were recovered or made reassignable by this candidate.
Independent models and reviews reproduce both curves, metadata, frame epochs,
thread boundaries and the exact input/visual controls in each language.

This closes the new host resource question for the declared pilot and fixture.
It does not complete the entire graphics clause: scene transfer work, global
GPU lifetime and costs outside the changed lookup remain unmeasured on host.
Those are explicit limits, rather than hardware-blocked measurements or implied
zero cost. No new transfer campaign is needed to maintain the limited lookup
claim; a new graphics/lifetime hypothesis would require its own observer and
acceptance tests. All original fixtures and game source remain unchanged.


## Queued graphics pilot — 10 November 2026

An additional opt-in Graphics profile qualifies a scoped EN r4 Bag-plus-Party
window on exact E5 `11225bcbd851b9fbb0be711775c1df9ee63c1c779fcde907fa03558d2bfe1f84`.
Reused E4OFF versus E5OFF and E5OFF versus GraphicsON preserve8478 guest frame
rows,2466 sampler rows,10RGB captures, start/end MainRAM and SRAM. Eleven E5
MainRAM checkpoints also agree. Host timer fields are excluded; two new runs
are observer controls, not performance replicas.

The2921 observed events comprise2505 spans and416 context markers. Six NNS
requests, all type35/512B, account for3072B; corresponding FIFO slots and six
synchronous channel3 DMA copies reconcile exactly. Enqueue-to-source-completion
lags are3,3,2,2,1,1 guest frames. Another85 observed GXS_LoadOBJ copies outside
the NNS tree request34336B. All91 observed SubOBJ DMA edges request37408B:
these include the six queued copies and cannot be added to them again.
Specific callers of the85 extra copies are not yet attributed. Their raw LR
contains a destination offset; explicit post-call return PCs are essential.

All events run in System mode on the main thread. The1193 GF/NNS drains are
callbacks called by Main after its VBlank wait; they are not an IRQ count.
Queue, thread, exact live code/table pins and eleven epochs reconcile with a
separate FIFO oracle.32 semantic falsifiers,15 deterministic-route falsifiers,
full/wrapped/identical queue tasks and zero-size CPU cases pass. Runtime tests,
binary CLI checks and nested DMA/CPU/IRQ/Init sanitizer controls pass.
Independent source and raw reviews retain the rejected qualifier assumptions.

These are source-consumer and request counts in the software model. Constant
64 interpreter dispatches per observed DMA edge do not measure DMA busy time,
DS cycles or bandwidth. Direct BG/palette/OAM, VBlank/FIFO waiting, live VRAM,
global graphics completion and physical display remain open. This closes only
the declared queue/SubOBJ slice; further host work remains in the same pilot.
No game source, original save, ROM installation or published artifact changed.


## Direct transfer and waiting pilot — 10 November 2026

Exact E6 `cd806fce161899ea61f632943fd6d58a81253d0d37c59bca413df5cf73452d34`
extends the same interpreter/software-renderer pilot with an explicitly
selected model-clock derivative, four-owner wait/censor tracking, primitive
copy census, OAM store oracle and bounded predicate/callback observations.
The baseline and private H4B images retain their exact identities above.
EN was qualified before expanding to the other three cells. Eight new E6
acquisitions include four OFF/ON pairs; older same-ROM OFF controls are reused.
No game source, original save or installed ROM was changed.

Each pair preserves 8,478 frame rows, 2,466 framebuffer/state/RNG samples,
10 exact RGB captures, SRAM and all 11 MainRAM checkpoints. C/B comparisons
within each language also agree outside the exact 256-byte code owner at all
11 checkpoints, with 28 changed bytes inside it and 5 EN/6 IT ARM9 PC differences
reported separately. The sample matches are hash/state observations, rather
than full per-frame image dumps. No cross-language causal comparison is made.

| Scoped observation, C and B | EN | IT |
| --- | ---: | ---: |
| Work events | 58209 | 58206 |
| Primitive graphic requested bytes | 5309376 | 5309952 |
| CPU16/OAM bytes = observed STRH store bytes | 2405088 | 2405088 |
| GX-branch raw timestamp advance | 0 | 0 |
| DMA9-branch raw timestamp advance | 5912808 | 5913630 |
| B minus C Execute residual | -52800 | -45070 |
| B minus C Halt1 skips | +52800 | +45070 |

OAM is included in primitive traffic and must not be added a second time.
The six NNS type35 requests/3,072 bytes are another included subset. Raw ARM9
timestamp advances partition 2,762,857,080 ticks per cell, ClockShift1 and
carry3 to3. Execute residual is not CPU busy time, DMA9 is the entire selected
core branch, and these are not measured hardware cycles. All reached DMA/GX
predicates have zero busy outcomes despite nonzero modeled DMA work; these
observations cannot be substituted for each other.

The 58 cumulative observations agree finally and at phase boundaries within
each language. Six transient frames per language differ. Two DMA32/SubOBJ
requests move one frame earlier: 512 bytes each in EN, 128 each in IT.
Per-mode site sequences and per-site aligned arguments/mode/LR/SP/results
agree; global IRQ/System interleaving differs. Phase intervals are scripted
checkpoint separations, not opening latencies. Lower modeled residual moves
into HaltSkip without changing the full frame budget or proving a UI speedup.
System-mode dispatch changes are -28688 EN and -26932 IT. Only -27786 is
assigned to the two observed list spans; the remaining -902/+854 is not
attributed or presented as another benefit.

All 11,930 bank sessions close, use NONE0 and reach four roles; Tex/TexPltt
remain static/synthetic controls. All 5,965 async submissions are size zero,
so the capture establishes no nonzero async completion. CPU16/RAM retains
68 unknown-source calls/4,352 bytes. Primary graphic rows are known, but global
coverage, source-free safety, live VRAM, bus traffic and scanout are not claimed.
Registry/TCB/heap ownership and code pins are verified at 11 quiescent snapshots,
not inferred for every instant between dumps. Waits retain left/right censoring;
known frame intervals are inclusive and are not exclusive blocked time.

Source, sanitizer and binary CLI checks are supplemented by 29 Clock/Wait
falsifiers, 26 graphic groups plus four independent type35 fixtures, eight
context, six registry and 15 route cases. Rejected validator assumptions and
independent closure reviews are preserved. These are bounded contracts, not
universal coverage. No heap or VRAM bytes were recovered. H4B remains private.

The two DMA shifts did not move the observed Bag poll or sampled reference
image in either language. The eligible poll is not proof of the first input
actually sampled; an image sample cannot establish the first partial effect
or input-to-photons latency. The separate Party input run is kept separate
from these image timings.

## Native asset I/O pilot — 10 November 2026

On the EN r4 control
`2e30d6960bb059615fca7527700d86f8282e82ccbe99bf62e22f027453dc3d3d`,
exact E7b `bd061f3bb5bfb8d70090a43f994c99edb07f273b72f2f612575e2685852cba11`
captured the fresh direct-boot guest route through both Bag openings and the
native Party control. E6 OFF→E7b OFF and E7b OFF→ON preserved all 8,478 guest
frame rows, 2,466 samples, ten RGB checkpoints, eleven MainRAM dumps and raw
SRAM. Host timer fields were excluded from equality. The bounded observer
emitted 80,611 records. An earlier 65,536-record acquisition was rejected
when its buffer filled, and its partial raw was retained separately.

| Script interval | Completed reads | Logical bytes | LZ output bytes | Backward overlay decode bytes |
| --- | ---: | ---: | ---: | ---: |
| Cold prefix through battle setup | 6,951 | 3,866,905 | 361,986 | 1,426,451 |
| Each Bag opening | 240 | 68,816 | 1,608 | 40,263 |
| Pocket change | 318 | 14,034 | 0 | 0 |
| First close and restoration | 1,005 | 64,277 | 54,372 | 58,398 |
| Second close and restoration | 958 | 61,269 | 54,372 | 58,398 |
| Party control | 720 | 105,450 | 4,248 | 40,263 |
| Final restoration | 958 | 61,269 | 54,372 | 58,398 |

The idle and navigation intervals registered zero reads in this capture. Across
the route, 11,367 sync and 23 async requests each matched a ROM and CARD
submission, completion notification and successful wait. No short, failed,
zero-length or outstanding read was observed. The 4,310,836 completed bytes
are one logical producer total; the API, archive and CARD rows are not additive.
The FAT/FNT reads are observed during cold initialization; the warm table is in
RAM. The two Bag openings had the same ordered offset, length, mode and caller
sequence. Each includes one overlay image (29,352 bytes), 47 Font 4 glyph
reads (3,008 bytes) and zero NARC17 reads. These observations are separate from
the 31 fixed whole-member requests reconstructed offline in EN/IT.

The lifecycle replay joined successful image read, wait and start for 34 loads
(27 game-managed and seven direct SDK), and found 30 completed unloads and two
game unload requests that found no matching entry. Registry changes matched
eleven RAM dumps at nine distinct guest frames. Overlay 8 and 10 load at the same address;
their expanded contents cannot coexist in that allocation. The 211 LZ calls
and 33 overlay decompressions are bounded to the two pinned native routines.
The backward counts are actual store sites and agree with the compressed image
footers. Decoder dispatch does not include other threads, IRQ work or waits.

This is one EN r4 route, with offline asset witnesses on the four EN/IT r4/H4B
cells. The capture excludes emulator setup copies before the first guest frame.
Logical bytes are not physical bus or disk traffic, and request-to-notify frame
deltas are not exclusive I/O time. No new game optimization, recovered capacity,
hardware performance or installation result follows from this measurement.
