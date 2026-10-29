# 1.3-dev systematic playtest — 28 October 2026

Aggiornamento del 29 ottobre 2026: la successiva
[verifica funzionale Android](android-1.3-dev-validation.md) conclude la campagna
corrente con 49 checkpoint accettati. Pin, conteggi, risultati e limiti di questa
tappa precedente restano quelli documentati sotto.

The later [v8 interface integration](ui-1.3-dev-validation.md) records the UI
follow-up and its final candidate; the v5 evidence below remains unchanged.

This is the follow-up to the [initial validation](validation-1.3-dev.md), carried
out under the [playtest plan](playtest-1.3-dev-plan.md). The resulting private
candidate is **v5**, still displayed as **1.3 DEV**. No release was published and
no published ZIP, tag or 1.2.5 input was changed. Work remains on `main`.

| Candidate | Bytes | SHA-256 |
| --- | ---: | --- |
| EN v5 | 137452904 | `06be019e5c8c8017984518488aaefea4458be92fa90fc3d37e9be8a7b0815486` |
| IT v5 | 142977384 | `b8ed7f72c95774956746a7d2cba7653eae1e327c49e9c4a2be86acba27703f18` |

## Corrections and measured cost

Rapid Guide navigation exposed a real input-loss problem in both languages.
The native lazy font reader fetched individual glyphs from the cartridge while
rendering long pages; a measured redraw blocked game vblank for 11 frames and
could miss a short button press. The Guide now owns a checked temporary glyph
cache while open. Allocation failure preserves the original renderer; an
already-cached font is borrowed without taking ownership. Exit restores the
native callback and clears the pointer before freeing owned memory.

This adds **196 bytes of compiled code**, **4 bytes of state** and **32,576 bytes
of temporary heap use** while the Guide is open. ROM file sizes are unchanged;
there is no save-format change or permanent cache allocation. In the matched
Italian traversal prefix (frames 4,270–17,040, identical input script), peak
stopped-vblank length fell **11 → 3 frames** and
extra stopped-vblank frames fell **3,447 → 690**. These are guest-frame
measurements, not a device FPS or battery benchmark.

Four new ARM tests cover allocation failure, ownership, unexpected headers and
idempotent cleanup. An independent check executed the original lazy and cached
native glyph decoders for all 509 glyphs in both languages: all 1,018 outputs
were identical. A fresh code review found no blocking defect.

The runtime diagnostic also had a false negative: changing PC samples at the
start of a stopped-vblank interval hid a later 8,360-frame exception loop.
It now checks the final constant-PC suffix independently and rejects sustained
fixed-PC loops outside the exception vector too. Six ROM-free regression tests
cover this behavior. Changing-PC `STALLO` remains inconclusive; a successful
process exit or diagnostic gate alone never proves that a menu or battle worked.
See [runtime gate semantics](test-bench.md). This correction affects developer
tools and adds no game overhead.

## Executed coverage

| Area | Accepted evidence | Scope and limitations |
| --- | --- | --- |
| Project suites | **616 executed and passed; 147 skipped**, 763 collected. Class A: 566/616 executed; Class B: 50/147. All registered 1.3 suites executed without skips. | Mandatory ARM compiler; actual private ROM inputs supplied. Historical fixture/intermediate-dependent skips remain skips. |
| Guide contents | All **429 entries per language**, 482 EN / 489 IT pages, 114 / 118 links, 1,582 / 1,597 cursor assertions. | Ordinary buttons/touch; category/list/detail/link/back and bounds. Not visual review of every page. |
| Guide determinism | EN repeat: entire **24,500-frame CSV and all captures byte-identical**. | Same frozen ROM, raw save, script, RTC and interpreter. |
| Guide lifetime | **64 opens/closes and 8 actual native Plus round trips per language**. | Reached-state assertions, cleared owned handles, restored font, intact guards/settings/expanded Bag and unchanged SRAM. |
| Native interface | EN/IT party, Summary, EV/IV reader, old help, Bag/pockets, Pokégear, Options/Plus and return to movement. | Summary stat pixels restored; observed native save arrays and SRAM unchanged. |
| Field integration | **12 maps × 2 languages**: Guide entry/exit, idle field task and released resources. | Declared native warp setup; Elm's story is completed with ordinary dialogue inputs. Explicit post-Guide movement is proved at Elm in both languages. |
| New Game | Fresh EN/IT no-SRAM starts through introduction, naming, Plus prompt, bedroom/stairs/mother, native SAVE and cold Continue. | IT recorded interactive exploration; EN fixed-script replay. Both reach map 63, preserve profile, have money 3000/party 0, idle field and byte-identical saved/cold SRAM. |
| Wild HUD | **57 real wild states: 49 v4 and 8 v5**, 9 species, 4 Unown forms; 10 deterministic replays. | 53 escapes, 2 Surf KOs, 2 captures with native SAVE/cold Continue. No caught-icon mismatch observed. |
| Trainer construction | **28 native constructions**, 168 valid Pokémon, **1,008 actual stats** independently checked. | Seven affected trainers, baseline/candidate Plus, EN/IT and candidate Normal. Normal moves unchanged. |
| Trainer behavior | **4,736 seeded native AI calls**, 20 damage/speed synergy scenarios; actual Rest/Chesto scripts in EN/IT. | Controlled copied battle state and declared allocator/archive/GUI seams. All nine new moves selected in sampled scenarios. |
| Completed trainer battles | Two six-Pokémon Bugsy wins: baseline and v4, same advanced roster and initial RNG. | Integration/stability evidence; not a level-appropriate balance playthrough. |
| EV/Day Care | 65 guarded snapshots; two simultaneous courses, cancellation, slot compaction, withdrawal, RTC forward/backward and playtime switching. | EN/IT course flows; Classic 510 accepted/511 rejected, Unlimited 1512, no-op/253 and insufficient-money rejection tested in EN. |
| Old raw saves | **7/7** baseline → v5 Continue → native SAVE → cold Continue cases. | EN/IT legacy, configured Plus, expanded Bag; advanced IT. Original fixtures unchanged. |
| Active courses | EN/IT two-course saves loaded in v5, saved normally and cold-restarted. | Jobs, credits, Pokémon, moves, money and settings retained. |

The field matrix covers Elm's lab, Olivine's Pokémon Center, Mahogany's shop,
four Mt. Mortar maps, three Rocket Base maps, Violet Mart and Dragon's Den.
Earlier Elm attempts stopped in an active story dialogue and were excluded.
The accepted repeats complete that dialogue, assert actual Guide entry/exit,
dismiss the bottom menu and prove avatar movement `(4,7) → (4,11) → (4,7)`.
Short directional inputs while the bottom menu still had focus were not accepted
as movement evidence. New Game starts use no warp, cheat, RAM edit or savestate;
their saves are newly created outputs, not modifications of an old fixture.

The wild campaign includes naturally reached post-capture encounters without a
debugger or map warp. Both historical caught and uncaught species render the
expected HUD. Capturing Burmy spends exactly one existing Master Ball, preserves
the original five party members, adds the native valid sixth Pokémon and persists
through SAVE/Continue. No additional wild-icon production patch was justified.
The previous trainer-icon extension remains separate from Pokédex data repair.

The old-save matrix compared profile/options/coins, party, native Bag,
variables/flags, Pokédex, Day Care, all PC Pokémon, existing Plus setting bytes
and the 2,380-byte expanded-Bag payload. Native initialization of a missing Plus
header is tracked separately. This is explicit fixture coverage, not universal
compatibility with every externally edited save.

## Team balance decision

Retain the nine intentional Plus substitutions. The native factory preserves
levels, generated personalities, IVs/EVs, species and items; actual stats agree
with the displayed levels. Rest heals Dewgong, triggers and consumes Chesto,
and a second Rest without the berry leaves it asleep. Curse's lower Speed
increases Steelix's native Gyro Ball power; Dragon Dance increases Gyarados's
physical Waterfall damage. Stage tests are separate from complete live animation
or turn-sequence tests.

Bugsy's Bug Bite materially increases pressure on Geodude and Flaaffy: in the
controlled level-21, neutral-nature, IV15/EV0 scenarios it deals **28–34/50 HP**
and **46–55/63 HP**, compared with Wing Attack's 14–17 and 23–27. Wing Attack is
retained. They are useful team members, not guaranteed solo answers.

A bounded response uses Flaaffy's Thunder Wave and ThunderShock, then a free
Geodude entry after Flaaffy faints. Paralysis puts Scyther's Speed below both;
the weakest ThunderShock plus two weakest Rock Throws exceeds its HP including
Sitrus healing. Actual encounter/evolution/learnset data confirms Mareep,
Geodude and these moves are available before Bugsy. Native follow-up AI checks
sampled 128 seeds and actual Sitrus healing was executed. This response assumes
hits and no criticals, allows a faint, and does not cover the resource cost of
Bugsy's previous five Pokémon. It is not a deathless-run recommendation or a
proof that every team can win.

The v5 Guide-only change leaves the checked battle archives, overlays and
native strategy regions byte-identical to v4 in both languages. Fresh v5 IT
Lance construction/entry also passed. Completed battle and most training
observations made on v4 are carried forward only across those explicit byte
comparisons; they are not relabeled as fresh v5 playthroughs.

## Method, references and rejected experiments

Boundary values, equivalence classes and state transitions follow the test-design
approach described by [ISTQB CTFL 4.0.1](https://istqb.org/wp-content/uploads/2024/11/ISTQB_CTFL_Syllabus_v4.0.1.pdf).
Applied examples include owned/unowned HUD states, exact EV limits, payment
rejection, menu ownership and save/reload transitions.

[Redux's trainer documentation](https://smilingzero.github.io/BlazeBlack2ReduxWiki/genTrainerChange/)
and [changelog](https://github.com/SmilingZero/BlazeBlack2ReduxWiki/blob/main/docs/changelog.md)
informed the comparison of real stats, early-game pressure and available team
responses. The project is not claimed to have Redux's full campaign coverage.
The explicit prerequisites, seeded decisions and expected actions in
[pokeemerald-expansion's AI tests](https://github.com/rh-hideout/pokeemerald-expansion/blob/master/test/battle/ai/ai_double_ace.c)
informed the native AI scenarios. No GBA/Gen V code or test outcome is treated
as evidence that a DS patch works.

The bench uses a pinned melonDS core, interpreter/software renderer, generated
firmware, fixed RTC and copies of raw saves. Ordinary-input campaigns are
separated from declared native map-change/trainer-selection setup and Unicorn
instruction tests. REA methodology was used for explicit evidence and guarded
native entry points; its native engine was not available. The existing
Capstone, Unicorn, disassembly and melonDS tools supplied the actual evidence.

Rejected experiments are retained privately. Initial Guide oracle mistakes
(footer touch and link-scroll expectations) were corrected independently of the
real font issue. Earlier stress attempts did not prove native Plus entry; the
accepted repeats assert its actual state address. Early debugger warps after a
capture produced exceptions in both the candidate and 1.2.5; normal-input
controls remained healthy, and waiting for the field to settle removed the
observed exception in the subsequent Elm setup. The exact underlying warp
failure is not established as a production regression. Such runs are excluded
from passing gameplay counts and now rejected by the repaired crash gate.

## Limits and publication status

No unresolved production defect was reproduced in the accepted completed
campaigns. This is a private development result, not a certification that every
possible game state is safe. Remaining scope includes a complete adventure,
level-appropriate full Gym/League battles, exhaustive AI/accuracy/critical/status
outcomes, Safari-specific gameplay, wireless/Pokéwalker interoperability,
physical consoles/mobile JIT configurations, real multi-hour elapsed waits,
egg hatching and physical power-loss tests. Historical skipped suites are not
credited as passed. The title remains 1.3 DEV and publication remains separate.

Rebuild with [the 1.3 builder](../sgp13/README.md), retaining its source/ROM hash
receipt; run `source/run_tests.py --richiedi-compilatore` with the documented
private inputs. The new font ownership and runtime-gate tests are registered in
that runner. Runtime scripts, raw traces, original fixtures and the full private
reports stay outside Git; the [bench documentation](test-bench.md) describes the
public harness and diagnostic commands.
