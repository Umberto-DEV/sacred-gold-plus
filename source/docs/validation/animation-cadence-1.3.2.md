# Natural battle cadence — 9 November 2026

The remaining host animation case is completed within the reduced development
scope. The maintainer excluded the new-area prototype; no new map or converter
is required. Android/Nintendo execution and physical display pacing remain
unverified. No animation repair or speed improvement was justified by this case.

## Exact identities and route

The unchanged [r4 game contract](../../distribution/game-1.3.2-r4.json) applies:

| Input | SHA-256 |
| --- | --- |
| EN ROM,152786844 bytes | `2e30d6960bb059615fca7527700d86f8282e82ccbe99bf62e22f027453dc3d3d` |
| IT ROM,159029760 bytes | `13ebac02bdea3036511773587e6603ce6834e25f4b13d1a4662c3e954bfd5d4a` |
| Original populated raw save | `84536ef9760569460d948302a8cac4c5e7e3a423a957e823185ac1dd516c2bfa` |
| E1 reference runtime | `e66bd179962a4de2086a42494e59425214e4499bbaa3e53f76061832b3d2d472` |
| E2 opt-in sampler runtime | `6dff1858099939a0517e48a293811a77cf3c6ee286ca443eafae84b8b7cefa9d` |

Source base remains `a912b3e155150e604d1bf5cb5bd5a18b8cf13b8a` plus the
reviewable working-tree tool changes. Compiler: authenticated Apple clang21
`clang-2100.4.1.1`, installed SDK27.2; Python3.14.7; interpreter/software renderer,
FreeBIOS/generated firmware, fixed RTC2026-09-05T12:00:00. Core pin remains
`906e9ebb27da8c6a715cd7abab4abfe8a8d29427` with the same two approved observation
patches. The complete core-tree guard passed at configure/build. E1 and E2 use
one canonical build tree; E1 is retained unchanged as the fallback.

The old National Park fixture is absent. Instead, a read-only audit qualified
the available save at Blackthorn Center map293,(8,17), with animation already ON,
native move animations ON, five party Pokémon,113 boxed and three expanded slots.
Normal Continue and walking reach the Center door, Blackthorn map89 and the
southern corridor at X664 into Route45 map47. Runtime reaches tall grass near
(647,212). Static warp/collision inspection was checked against actual movement;
it was not substituted for gameplay.

The recorded path includes a harmless blocked southward attempt and correction
before following the western exit. Each final replay is11804 guest frames from
raw cold boot, with no warp, RAM write/freeze, cheat or savestate load. The raw
input copy is read-only. English encounters Graveler45; Italian encounters
Grumpig46. Scene/RNG differ between languages, so controls are compared **within
each language**, not interpreted as identical encounters across languages.

The replay visits command, Bag and Party, switches normally to Typhlosion,
receives the opponent's native turn and selects Earthquake. English reaches
Graveler's KO and deletion; the Italian opponent remains present at the endpoint.
Sparse images verify the visible states. Some exploratory eight-frame touches
did not enter Party; a sixteen-frame hold did. The corrected input duration and
actual switch are recorded rather than described as the originally intended
Surf action. This does not establish an input defect in the game.

## Qualified observer

The [runtime sampler](../../runtime/README.md) is opt-in and OFF by default.
After `RunFrame`, it reads completed RGB buffers and bounded main-RAM fields;
it never calls guest code, RNG, filesystem APIs or MMIO. Its separate CSV records
full-screen/ROI hashes, four slot generations/phases/channels/private RNGs,
copy ownership and native battle RNG. Raw pointer admission is not a universal
lifetime proof; this experiment authenticates the installed layout.

The native RNG field was independently qualified in both actual overlay12
images: function at `0x0223BD98` loads/stores offset `0x2448`, multiplies
`0x41C64E6D`, adds `0x6073` and returns the upper16 bits. A44-byte window matches
between languages. Endpoint samples also match the independently retained
baseline main-RAM dumps at that field. ANIM2's private LCG is a different field.

The new C++ contracts first failed for the missing API, then passed. Expanded
tests cover RGB/alpha/ROI boundaries, invalid/truncated pointers, inactive/unused
slots, recycled pointers, mismatched BattleSystem generations, native RNG and
the OFF/timing gate. All16 existing runtime test methods pass without skips.
The original37 prepared ARM animation/copy contracts are reused, not rerun or
relabeled as natural-battle timing.

Seven bounded replays passed: EN E1; EN E2 OFF/ON/ON/OFF; IT E2 OFF/ON. Per
language, every non-timing guest CSV column, sparse capture, final4MiB main RAM
and exported SRAM is identical. The two English sampled timelines are identical
except host sampling time. Each ON run contains5792 consecutive post-frame rows,
frames6013–11804. Independent RGB decoding of final checkpoint images reproduces
all three FNV hashes. Hash equality alone is not used to replace byte comparisons.

## Results and interpretation

Windows were fixed from the reference command log before metric extraction:
command600frames, steady Bag300, steady Party300, followed by switch/native-turn,
move-selection and Earthquake-resolution windows. ROI is X0,Y16,W256,H128 on
the upper screen. It includes battlers and HUD; it is not a per-Pokémon mask.

| Stable window, EN/IT | Measured result |
| --- | --- |
| Command,600frames | Both battlers advance phase every2guestframes; cycle96frames. |
| Bag,300frames | Both phases retain2frame cadence and96frame cycles. |
| Party,300frames | Both phases retain2frame cadence and96frame cycles. |
| Owned channels | Maximum adjacent Y and scale delta1 in all three windows. |
| RGB succession | Equal-ROI-hash runs have median2frames, maximum14. Phase continues during long equal-hash runs. |
| RNG | Native battle RNG constant within each stable window; private LCG values change. |

The96frame cycle confirms the earlier48tick contract in these natural scenes.
Equal-hash runs while phase advances are consistent with quantized channel/pose
plateaus; they do not demonstrate dropped guest frames. Full per-frame RGB was
not retained, so those run lengths remain hash observations with collision
limits, rather than byte-equality proof for every frame. A nominal
frame rate is not used to claim physical presentation times or comfort.

The switch/native-turn window contains64frames with live copy ownership and
longer phase gaps. Native move/suspension and menu-entry windows also have
longer intervals; combining them with steady idle would mislabel intentional
suspension or scheduler work as an idle-cadence regression. English KO releases
the opponent slot; the player remains active at the bounded endpoint. This is
not a full capture/Safari/doubles/battle-end campaign or a write-ownership trace.

Sampling has measurable host cost. English OFF elapsed25.258/25.166s and ON
26.893/26.972s; mean difference1.721s includes drift, CSV and observer overhead.
Sampler medians are0.355/0.356ms, with about2.083/2.082s summed over5792 samples.
Italian median is0.360ms. Existing RunFrame timing excludes this work and shows
overlapping variation. These are tool costs, not faster/slower game animation,
Nintendo CPU cycles, display pacing or input latency.

Original save and ROM hashes remain unchanged; raw SRAM exports match their
input in every replay. No native SAVE is newly claimed here: the r4 raw-save
matrix in the [UI report](ui-lifecycle-1.3.2.md) and the distinct private palette
SAVE/cold evidence in the [host report](development-host-1.3.2.md) retain their
original identities and limits. The observer changes no game/save format.

## Scope and retained evidence

The canonical private campaign is
`local/validation/sviluppo-1.3.2/anim-naturale-2026-11-09/`: protocol, route/tool
analyses, commands, hashes, windows, raw CSV, bounded receipts, captures and
independent review. One producer,a sampled2GiB RSS guard and64MiB campaign budget;
all replays finish below180s and12000frames. Sparse captures are losslessly
canonicalized as PNG with original PPM reconstruction hashes. Duplicate RAM
dumps are removed only after exact hash comparison; canonical baselines remain.

Host completion means the natural route, emulated image succession/cadence and
observer controls above are qualified. Physical display refresh/scanout,
input-to-photon latency, subjective readability, audio synchronization,
Android and Nintendo remain unverified. The new-area prototype is excluded,
not passed. No release, personal installation or game performance claim follows.

Independent final review passed within this host scope, with no open findings.
Environment, inventory, source hashes, diff/public checks and cleanup are recorded
separately; none extends the physical-target matrix.
