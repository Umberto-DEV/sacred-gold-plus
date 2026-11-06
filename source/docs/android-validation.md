# Android validation evidence

## Current release: bounded post-release smoke — 6 November 2026

This later execution is separate from the historical 1.3 DEV campaign below.
It does not relabel old EN/IT tests or physical-device scenes as acceptance of
the latest candidate. The exact public APK was freshly downloaded and hashed.

| Identity | Tested value |
| --- | --- |
| Released Android source | `ac42561495ee6351d7f119f68760509c268f582e` |
| Embedded core | `06f3df985f67416368e0716174b7f06934a10229` |
| Public APK | SHA-256 `d3cf208e4380c4e3060ca9f33a10d8d6d1c4621c3f36c1a037bbfff11a01a928`, 20,786,147 bytes |
| Package / version code | `me.magnum.melonds.nightly` / 52 |
| UD certificate SHA-256 | `832a0223e29802245c0e9f8ca24c8358e7d21cfe0dbea347845fda751f950d86` |
| Android documentation checkpoint | `7fa279ee61cac3087ee6fd4ef82f899722513bb4`; CI `42270884861` succeeded; this documentation head did not replace the APK |
| Runtime | Android 15/API35 ARM64 emulator, measured 16,384-byte pages |
| Game copy | EN 1.3.1 ROM SHA-256 `185dc5c53a75652c021ced65157e1c3388cd661ebe90775e5b49314aee753b08`, using a separate copied raw save |

The public UD 51→52 update preserved three library records, logical contents
of 15 database tables, protected preferences, runtime permissions, persisted
URI grants, UID and first-install identity. After normal first launch,
`last_version` advanced 51→52; regenerable cache/profile changes were listed
separately. The test then used normal Continue, native SAVE and a distinct
cold process returning through Continue to the same field. The selected save
generation advanced 205→206. Twenty-five semantic checks passed, including
complete party, all 540 box slots, native and expanded Bag, progress/state
arrays and Plus settings. Expected native RTC/new-console, berry-pot,
roamer and playtime/journal changes were retained explicitly; native playtime
and journal advanced by the same 596 seconds. The copied raw hash remained
unchanged across cold Continue. Originals were preserved.

Guide category/list/detail and Options/Shiny pages rendered. A 100 ms virtual
Down press moved the Guide selection 1/4→2/4; that is a bounded input
observation, not a comparison with native-menu responsiveness. The fixture had
no active Day Care course or Pro shiny hunt. This is one EN game/save smoke,
not a full compatibility matrix, physical device update, new IT acceptance,
DSi/multiplayer qualification, complete playthrough or power-loss test.
See the [exact APK report](https://github.com/Umberto-DEV/melonDS-android/blob/main/docs/current/POST-RELEASE-SMOKE.md)
and [current UI/candidate evidence](ui-1.3.1-validation.md) for their own limits.

## Historical Android campaign and target

The 29 October candidate/device checkpoint is retained in the
[device report](device-validation.md). Hashes, counts and limits below refer
to their identified revisions. The historical Android functional campaign
closed with **49 accepted checkpoints: 45 native SAVE/cold cycles and four
refusals preserving the entire input file**. Its matrix separates Android
scenes, ARM execution and data checks. It validated a private **1.3 DEV**
candidate; it did not publish a release or replace existing tags, ZIPs or assets.

Earlier [v5 playtests](gameplay-validation.md),
[v8 interface checks](interface-validation.md),
[stability diagnosis](stability-investigation-1.3.1.md) and
[initial v4 validation](validation.md) retain independent pins and counts.
The target below was an **Android 13/API33 ARM64 AVD**, using an acquired APK
and **Software 1×**. It was not physical Compute 6× acceptance or a GPU,
driver, FPS or latency comparison. Bench shader/GLES problems were tracked
separately from ROM defects.

## Historical candidates and evidence transfer

| Language | Campaign v3 candidate SHA-256 | Closing status |
| --- | --- | --- |
| EN | `1ed3c886f26ac01c64e7c4f102c38659af6cec81d5c317ba3cf31c67447fe9d5` | Build, review and eight v3 Android checkpoints accepted: migration, Options/Plus, Protein, Kelpsy, Pro charge, two captures and Technician withdrawal; all with SAVE/cold. |
| IT | `2f1b0857f1b57703c635d9076aec8f650a8e9aec8f3335e3a271098a261a45f8` | Entire ROM identical to the already executed v2. Tests on this hash apply to the exact final bytes of this historical campaign. |

The 49 checkpoints comprise 25 on v1, 16 on v2 bytes (seven EN, nine IT) and
eight EN v3. They are 45 SAVE/cold checkpoints plus four save refusals with the
entire input file preserved. Checkpoint count differs from feature count.

Additional **UI-only** Bugsy checks used Normal IT (Scyther 21 with Agility
and Wing Attack) and Plus EN (Scyther 23 actually using Bug Bite). All six Plus
levels were readable and differed from Normal. Battle endings and subsequent
field dialogue were documented; final images still had dialogue open and do
not prove free movement. No battle SAVE was made: both exported files were
byte-identical to their inputs. This does not establish RAM state or durable
victories and does not increase the 49-checkpoint total. False Swipe was not
observed; forcing its selection was not required.

EN v2→v3 changed **77 bytes only in the Options text bank**: one sentence,
its offsets and padding. Every external byte, including code, configuration,
resources and ROM metadata, remained identical; IT had no differences. This
supports retaining unchanged-path evidence and replaying the affected EN text
path, rather than claiming every Android test was repeated on EN v3. That path
was actually replayed: complete note, acceptance and field, SAVE export before
termination, cold Continue to the field and matching save files. Its fixture
has empty party/PC, so it does not independently prove populated Pokémon
preservation.

| Earlier checkpoint in this campaign | EN SHA-256 | IT SHA-256 |
| --- | --- | --- |
| v2 | `fe182440f43cb95442fcb2a965ba68a4bf6b4b2e22ccc616f1df3a9bf2fc1106` | Entire ROM identical to campaign v3 IT above. |
| Balance493 v1 | `a290df71a54ea016f4e19cd9e6f8f94e1f8d1f675b4d2dcd209c058d4f6a5b12` | `f7585f5248f483a4bbe12424954a805a86ff9d744f58b62a135e750a7f00099e` |

These v1/v2/v3 labels belong to this campaign and do not rename v3/v4/v8
candidates from other campaigns. Earlier v1→v2 changed Training, high-event
flags and Continue composition. Evidence transfer from v1 is limited to
unchanged components; those integrations received new installed-code ARM
checks and dedicated Android scenes. Historical runs are not relabeled as
executions of a later final candidate.

## Method and preservation

Every run uses a **save copy**; originals are preserved and hashed. Controlled
preparation, such as event position or a supplied prerequisite, is declared
rather than presented as ordinary story progression. The two EN Search
captures were ordinary, without modifying PID or RNG.

Persistence requires Continue, in-game operations, **completed native SAVE
exported before termination**, app termination/relaunch, Continue to the field
and comparison of the acquired save. In the first historical legacy IT case,
immediate export preceded emulator flush and was excluded: accepted comparison
uses byte-identical `cold.sav` and `cold-later.sav`. Savestates do not replace
these tests. Refusals compare the entire file with its input; failed SAVE is
not accepted as successful migration.

Audits inspect Pokémon identity/content, party/PC, native/expanded inventory,
settings, Day Care/courses, rewards, contacts, bank consistency and integrity.
Allowed time/NPC changes are narrowly identified and justified; general
normalization does not erase unexplained differences. ARM tests execute game
or candidate functions, declaring simulated heap/OS/resource/flash/commit/
transport boundaries. A damage or printer-ownership test alone does not prove
the complete graphical Android sequence.

## Three defects corrected in the historical campaign

| Reproduced defect | Correction | Evidence and boundary |
| --- | --- | --- |
| An already active Training service could apply EVs and charge money before an unrelated save destination caused later SAVE refusal. | Fresh destination check before mutating operations 4–8. Refused operation 4 invalidates preview; retry requires a fresh preview. Reads/cancellation are nonmutating. The message no longer incorrectly promises ordinary SAVE. | Android EN/IT paid-EV refusal precedes mutation; EV/money remain intact, SAVE is refused and the whole file matches after cold Continue. ARM also covers other services and retry. |
| High event flags could overlap Pal Pad data: a completed Mew capture altered unrelated data. | Dedicated flag area, conservative import of previous state and before/after Continue checks, retaining event IDs. | EN/IT first relocation and final Mew capture, SAVE/cold and complete Pal Pad preservation. ARM covers every flag in the affected class, collisions, import and Sinjoh reader; not every quest on Android. |
| EN migration note clipped: 218 pixels in 204 available. | Shorter EN sentence, 193 pixels, with real-space guard. Unchanged IT is 201 pixels and already fits. | Original font/pixels reproduce the defect; transformer and independent v3 build comparison establish the bounded text change. EN v3 UI/SAVE/cold replay passed with complete note/field and strict save comparison. The earlier overlapping-command attempt is excluded. |

These three corrections do not explain every earlier freeze/missing marker.
Mew movement duration and SAVE-failure communication retain separate evidence.

## Actual balance-change coverage

- **493 species** have individual documented decisions, not 493 Android battles.
- **67 species** receive at least one change; categories overlap.
- **50 species** have changed base statistics.
- **51 personal records** change: Meganium changes only its second ability slot.
- **29 learnsets** receive **32 level/move additions**, not 32 distinct moves;
  existing Pokémon's owned moves are not silently replaced.
- Kricketune gains Technician and Meganium Natural Cure as second native slots.
  Ability behavior has ARM proofs. Ordinary Technician acquisition,
  PC→party and SAVE/cold also passed on Android EN; Technician's numerical
  effect and Natural Cure behavior remain ARM evidence.

Data census/native tests cover the finite changed set. Android scenes sample
generation, recalculation, learning and preservation; they do not estimate
whole-adventure balance or win rates.

## Historical 37-feature matrix

“Verified in the sample” refers to the described path, not every variant. The
last two agreed groups, EN EV items and EN Pro 402, were completed; listed
limits are not additional scenes claimed as executed.

| # | Feature | Available Android evidence | ARM / data / code evidence | Remaining boundary |
| --- | --- | --- | --- | --- |
| 1 | Title/version | EN/IT boot/titles documented; final campaign IT bytes match those executed. | Title/text bank checked in build comparison. | Complete EN v3 migration note, choice and SAVE/cold passed in the sample. |
| 2 | Older saves without Plus | Continue, initial question, explicit Plus/Plus choice, SAVE/cold EN/IT. | Native bank selection, integrity and initialization. | Initial fixtures have empty party/PC; populated preservation is covered elsewhere. |
| 3 | Older Plus/expanded-Bag saves | Configured/expanded EN/IT preserved; active cases retain party, PC and Day Care. | Records, extra slots, owners and bindings checked. | Extended-slot preservation proven; every slot was not visited in UI. Eight compatibility cases completed. |
| 4 | Guide entry/exit | EN/IT entry, field return/movement; later IT roundtrip saved/restarted. | Controller/window ownership/returns tested. | Representative sample, not every entry/cancellation. |
| 5 | Guide categories/content | Four categories/details readable EN/IT. | Census: 429 evolution/item/event/Training entries. | Not 429 Android openings. |
| 6 | Guide pages/scroll/links | List jumps, two-page detail, link/return to source page; sampled last item. | Controller bounds/states checked. | Misnamed captures excluded; not every key/boundary played. |
| 7 | Plus entry/native preview | EN/IT correct first Text Speed row, Plus entry, restored caption and new partial printing to completion. | Owned active-printer branch executed in ARM with declared preview/window boundaries. | Essential EN/IT path passed; no active-overlap Android Plus-entry proof. ARM branch remains declared, with no new instrumentation requirement. |
| 8 | Plus draft/cancel/apply | EN/IT five descriptions, canceled draft, application preserved after native Quit/cold. | Controller and Options/Plus structure separation. | Essential EN/IT sample, not every value combination. |
| 9 | Five legacy settings | EN/IT descriptions/values/cancel/apply/cold; native speed, L=A and frame preserved; Plus boss scene executed. | Five-option reads/writes/hooks checked. | EN/IT sample and Plus boss scene completed; selector is not a network connection test. |
| 10 | IV/EV advisers | Silver/exact/purchases EN; Gold/claim IT; valid IT services with cost/readback/cold. | Guards, prerequisites and transactions executed natively. | Positive IT integration completed; not every Mart entry direction. |
| 11 | Silver/exact IVs/Gold | Silver/exact EN; six IVs at 31 with Gold EN/IT, no-op/cold. | Complete identity/recalculation/record reconstruction and transaction boundaries. | Not every IV value replayed; unplayed branches remain native evidence. |
| 12 | Cap purchases | Silver 10,000 EN; Gold 50,000 IT with prepared prerequisite; pre-League Gold refusal. | Prices, space, funds and prerequisites. | Controlled League prerequisite is not a natural League victory. |
| 13 | Rewards/repetition | IT claim/repeat without duplicates; empty EN claim; SAVE/cold. | Historical census, ledger and delivery executed in ARM. | Not a natural all-badge/League/Red campaign. |
| 14 | Full reward stack | EN stack 999, no-op, consumption/partial delivery; pending remainder survives cold. | Full/pending and negative controls. | Full stack does not mean every Bag slot occupied. |
| 15 | EV policy | EN Classic at/above limit, Unlimited canceled/applied; IT Unlimited preserved with valid operation. Ordinary EN Protein/Kelpsy SAVE/cold. | Prerequisite census and finite boundaries. | Sampled policy/items, not every limit/item combination in both languages. |
| 16 | Quick EV training | EN reset/decrease/increase/no-op; IT HP 64→65 at cost 100, free repeat/cold. | Costs, identity and native commits. | Representative integration, not every amount/statistic per language. |
| 17 | Battle EVs/vitamins/berries | IT KO EV gain. EN Protein: Attack EV 0→10, Attack 103→104, quantity 992→991. Kelpsy: EV 10→0, Attack 104→103, quantity 999→998; repeat has no effect/extra consumption. Both SAVE/cold. | EV hooks/rules checked. | One ordinary EN vitamin/berry, not all items/statistics in both languages. |
| 18 | Course enrollment | Ordinary EN enrollment, two subjects/durable serials; IT projection/withdrawal. | Enrollment/identity/prerequisites executed in final tests for both languages. | New IT enrollment not played; declared limit without adding a new gate. |
| 19 | Course clocks/status/phone | EN RTC/playtime/offline interval; IT five phone pages, two courses and remaining status. | Projector/credits/anchors/clocks. | Not every clock change/backward RTC transition on Android. |
| 20 | Course withdrawal/compaction | Both EN withdrawals; IT withdrawal at 400 with second subject/job compacted/preserved, cold. | Withdrawal/compaction and reconstructed records. | Positive IT sample completed. |
| 21 | Earlier-course migration | Active EN/IT saves: journal migration, two courses/rewards preserved, SAVE/cold. | Integrity/versions/save composition. | RAM migrations supplement rather than replace Android cold tests. |
| 22 | Unrelated destination/admission | EN/IT paid service refused before EV/money changes; readback/whole-file equality after cold. | Fresh check for all mutating services, preview invalidation/retry. | Prior RED remains historical; not every negative service replayed on Android. |
| 23 | Boss teams/strategic moves | Normal IT Scyther 21 with Agility/Wing Attack; Plus EN six levels and Scyther 23 using Bug Bite. UI-only. | Seven teams, construction, level/move variations. | Representative gate completed; no battle SAVE/RAM-journal claim. False Swipe unobserved; not all difficulties, seven victories or early-game balance. |
| 24 | Caught marker, wild/trainers | IT wild before/after capture; trainer Scyther/Pinsir with Ball, Heracross without, consistent with initial Dex. | Native dispatcher/renderer, requests/bar types. | Ball is intended for caught trainer species too; no universal old intermittent-marker fix inferred. |
| 25 | Updated data in real Pokémon | New EN/IT captures, Tentacruel withdrawal/old Rattata; new Mew reconstructed against final data. | Census of 493, data delta/native formulas. | Plus strategic scene completed; not 493 battles or universal correction of preserved old caches. |
| 26 | Continue/damage/KO/PC withdrawal | Damaged/fainted/full-HP samples; PC withdrawal with new statistics/cold. | Native recalculation, damage/KO preservation and idempotence. | Separate samples, not every species/HP combination. |
| 27 | Learnsets/owned moves | IT Tentacruel learns Sludge Bomb normally from Move Reminder, pays Heart Scale, preserves identity/cold. | All additions/native accesses checked; owned moves/PP preserved in audits. | Not every learnset played in both languages; no silent move replacement. |
| 28 | New/owned abilities | Existing abilities preserved. Two ordinary EN Search Kricketune: Swarm then Technician; Technician PC→party→Summary→SAVE/cold passed. | Technician numerical effect; Natural Cure producer/update/party consumer executed in ARM. | Technician assignment/persistence passed Android; numerical effect/Natural Cure remain ARM, without damage inference from HP bars/hidden IVs. |
| 29 | Shiny Classic | Controlled-state shiny EN Vibrava capture/cold; ordinary non-shiny Classic static Mew EN/IT. | PID transformation/exact odds. | No empirical frequency/spontaneous-shiny waiting claim. Mew is not an excluded route. |
| 30 | Pro/target/thresholds | IT capture/KO/flee/same target; settings/chain durable. EN Pro/Kricketune two captures, chain 0→1→2, SAVE/cold. | Finite core states/odds thresholds exhausted. | EN Pro path completed, not captures at every threshold. |
| 31 | Charge/Search | IT charge-0 refusal, charge 40, Search under Repel, KO/flee. EN charge-0 refusal, charge 40, Search under Repel/two captures; consumption checked. Method selector reports unavailable in Center. | Pool/method/context/generation executed natively. | EN path completed; zero-charge refusal differs from Center Method message. Surf as an attack is not a Surf encounter. |
| 32 | Outcomes/chain | IT capture/KO increment once, flee resets, SAVE/cold. EN two ordinary captures give durable 0→1→2. | Finite outcomes/owner/settlement. | Unplayed outcomes remain limits. Exclusion from Hunt chain does not hide trainer marker. |
| 33 | Hunt persistence without courses | RNG/chain/settings persist without activating courses/rewards; coexistence in active IT cases. EN charge really 40 before SAVE, then cold field at 0 with Pro/target preserved. | Owner/coexistence/installed save checks. | 40→SAVE/cold→0 checked separately from cold after Search consumption; not every course/mode combination. |
| 34 | Eligible/excluded shiny routes | Ordinary grass EN/IT; non-forced ordinary static Mew with persisted draw. EN all 11 Rules rows readable over three pages, returning to first. | Classifiers/constructors/abort with declared boundaries. | Rules prove UI content, not execution of every route. Rare exclusions are not Android scenes; Hunt filtering and trainer marker are separate. |
| 35 | Mew relocation/movement duration | First relocation/final capture EN/IT: free field, flags/Pal Pad preserved, SAVE/cold. | Movement waits, high flags/native readers. | Prepared copies declared; not one complete continuous pursuit. Final flag value is not a trace of every intermediate write. |
| 36 | Failed SAVE/acknowledgement | Three refusals per language using A/B/touch, reopening/movement; new v2 scenes cold to field with intact raw. | Result/cleanup/acknowledgement sequence. | Android transient recovery/power loss not established; no invented extra fault requirement. |
| 37 | Adjacent native UI | IT Guide, three actual Summary Stats help pages, restoration, Bag, Pokégear, Options/Plus, field/cold; earlier EN roundtrip. | Window ownership/component returns. | Essential EN Plus/printer cycle completed with cold; misnamed captures excluded. |

## Automated counts and boundaries

Installed-v2 validation includes **86 passing tests**, zero failures/errors/
skips, and **76 RAM migrations**. Executable code/configuration is identical
in v3; evidence retains its declared simulated-service boundaries. The 76 RAM
migrations are not 76 Android SAVE/cold cycles.

A later complete final-runner invocation passed **37 Class A suites**:
806 executions excluding 52 skips. Its total 858 includes skip accounting,
not an independent discovery count. It is not added to the earlier 86 as a
new disjoint total. Class B remains separate: four synthetic reader-mutant
checks executed and 176 prerequisite skips. This is not a fresh check of all
installed ROMs. Both 52 Class A and 176 Class B skips remain visible.

## Final two sample groups

Protein/Kelpsy were used normally from the EN Bag. Audits reconstruct complete
subject records/inventory deltas; a second Kelpsy use is refused without extra
consumption. Daily changes during Protein, including another party member's
Pokérus aging, are explained separately, not attributed to the vitamin or
erased by general normalization.

The EN Pro cycle read all three Rules pages, saved with actual charge 40 and
verified cold charge zero while preserving Pro/target 402. Two Search
encounters under Repel produced ordinary captures: Swarm (68), then Technician
(101), chain 0→1→2. Actual level 19 includes WildPlus transformation of base
level 18. Both boxed captures were saved/cold-restarted before the next stage.

Ordinary Burmy deposit and Technician Kricketune withdrawal preserve their
respective 136-byte boxed identities; the other five party members and every
other PC record remain exact. The new party cache follows native calculation.
Summary and cold Summary show female level-19 Kricketune: **HP 62/62,
Attack 46, Defense 38, Special Attack 24, Special Defense 37, Speed 38**,
Technician and four full-PP moves: Fury Cutter 20/20, Bug Bite 20/20,
Leech Life 15/15, Sing 15/15. Complete post-SAVE and cold files match. The
final audit reconstructs all 45 compared regions with explicit finite changes
and no optional normalizers. It distinguishes observed map/RTC/three unused
Mail words from formula-derived values. This establishes acquisition,
PC/party conversion and persistence; Technician's numerical effect remains
ARM evidence.

## Historical input integrity and bench limits

Independent final checks preserved **23 original-input references** of several
kinds, **38 unique fixtures**, both final campaign ROMs, both 1.2.5 bases,
14 reference Options artifacts and 208 frozen code/data/test files. Those
23 references are not 23 older-save fixtures. Documentation-only changes are
outside that frozen manifest and do not require rerunning ROM/native tests.

The two installed historical ROMs match their campaign pins. The acquired
APK retains SHA-256
`198505e4f50d9eafa2dbc3f941fcec83f0b747e23c95cb00efdb57859ce8afaa`.
At final collection its crash buffer was empty; all 16 retained exit records
were user-requested force-stops consistent with controlled cold cycles. This
is a bounded observation window, not absence of all historical crashes.
Host graphics warnings remain in evidence; that campaign did not touch the
personal physical device.

The finite historical functional campaign is complete within these limits.
Private evidence/superseded candidates retain their original scope. Neither
it nor the later bounded EN smoke establishes zero bugs, a Latios fix,
universal caught-marker correction or measured FPS/input-lag improvement.
