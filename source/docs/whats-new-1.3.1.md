# What is new in Sacred Gold Plus 1.3.1

The shared features below continue in 1.3.2. See the [current change log](../../CHANGELOG.md)
and [five-language validation](validation/localization-1.3.2.md) for localization
and the New Game correction. The 1.3.1 hashes below retain their historical scope.
The [1.3.2 lifecycle investigation](validation/ui-lifecycle-1.3.2.md) adds
Options/Guide loading and ownership evidence on unchanged EN/IT images; it
changes no feature, save format or performance acceptance on hardware.
The later [host development report](validation/development-host-1.3.2.md)
adds a reproducible bench and focused contracts, plus an opt-in build-time
palette demonstration; it does not change the released game's default art.
The subsequent [natural battle cadence](validation/animation-cadence-1.3.2.md)
evidence concerns the host's emulated images and tasks, not physical display
pacing or a game animation repair.
The [Bag work-observer follow-up](validation/development-host-1.3.2.md#battle-bag-work-observer--10-november-2026)
adds developer dispatch observations and scoped private experiments; it changes
no accepted game feature, save format or hardware performance status.
Its continuation also distinguishes sampled native input, displayed focus,
Android accounting and virtual frontend presentation, with explicit rejected
attempts and physical-target limitations.
The later [transfer/wait qualification](validation/development-host-1.3.2.md#direct-transfer-and-waiting-pilot--10-november-2026)
is developer evidence for a fixed host pilot. It recovers no game memory and
adds no released feature or hardware performance acceptance.
The [native asset I/O follow-up](validation/development-host-1.3.2.md#native-asset-io-pilot--10-november-2026)
records file completions and overlay lifecycle for the EN r4 control.
The [Guide opening correction](validation/guide-opening-1.3.2.md) has separate
candidate-bound evidence. The historical [1.3.2 package revision](validation/package-1.3.2-r3.md) separates the
five clean-ROM patches from optional historical updaters and places translated
installation/news PDFs beside each language's patch. It changes no game bytes.

Version 1.3.1 combines the implemented1.3 feature line with the current Guide/settings redesign, portable Box and targeted bug repairs. Current released ROMs are EN `185dc5c53a75652c021ced65157e1c3388cd661ebe90775e5b49314aee753b08` and IT `b68ddd5691538c3895b75f3f20db5a163b2bd8376629f59d2a9d55dc05935bce`. The [composition guide](../sgp131/README.md) gives exact inputs/toolchains; [UI validation](ui-1.3.1-validation.md) and [Android evidence](android-validation.md) retain candidate-specific results. Earlier tests are not silently relabeled as current-ROM acceptance.

## Guide and settings

The field Guide uses HGSS fonts, frames, palettes and controls. It is separate from the Summary EV/IV reader. The historical V4 catalogue contained429 entries:229 evolutions,156 items/TMs,38 event groups and six Training topics. The current 1.3.1 resources contain 467 selectable entries: six Training, 229 Evolution, 76 Special and 156 Item records. The 76 Special records comprise 38 canonical topics and 38 species aliases. Readback of both current ROMs (English `185dc5c53a75652c021ced65157e1c3388cd661ebe90775e5b49314aee753b08`, Italian `b68ddd5691538c3895b75f3f20db5a163b2bd8376629f59d2a9d55dc05935bce`) confirms this census in member 829 of `a/0/2/7`. Lists, paginated detail, links and return positions have independent controller tests. Font resources are owned and released on exit.

Current Guide content appears above with controls below. Settings use a continuous Game/Plus/Shiny list above and the native static Poké Ball below, operated by physical buttons. Native/Plus/Shiny drafts, cancellation, explicit Apply, Info, target selection and prepared hunts follow the [settings contract](settings-1.3.1-spec.md). Old V4 text describing an inert touch screen or a two-page Plus menu is historical behavior, not the current interface.

The6November input correction reads newKeys at System+48 and native repeat at+4C instead of heldKeys+44. It preserves remapping/timers and changes ten bytes per language including two derived CRC32 values. Static reverse projection restores the measured predecessor exactly; no new gameplay run is implied. Compiler cleanup also preserves the original ValueError when killpg raises EPERM only if poll confirms the child has already exited; live-child failure remains explicit, with bounded wait/output and toolchain pins retained.

## IV advisers and Caps

Advisers in Violet and Blackthorn Poké Marts offer real stored IV changes, which can affect breeding and Hidden Power. Silver Cap sets one IV to 31 or an exact 0–31 value; Gold Cap sets all six to 31. Selection shows current/requested values. Cancellation, no-op and refused payment consume nothing. Silver costs10,000 after one badge; Gold costs50,000 after the League.

| Milestone | Reward |
| --- | --- |
| Each Johto Gym | Two Silver Caps |
| Each Kanto Gym | Three Silver Caps |
| Eighth and sixteenth badges | One additional Gold Cap each |
| First League victory | Four Silver plus two Gold |
| Later League victories | Four Silver plus one Gold |
| First Red victory | Three Gold |

Older saves receive eligible historical rewards once. Past repeated League wins are not retroactively paid. A full reward stack leaves the remainder pending rather than losing or duplicating it. [Native services](../features/training-native/README.md) and [persistence](../features/training/README.md) describe the transaction.

## EV rules and Day Care courses

Training supports quick EV increases/reductions/reset, Classic limits and optional Unlimited policy. Costs, identity, preview, no-op and commit checks are distinct. A fresh destination check precedes mutating operations4–8; refused operation4 invalidates preview so retry requires a fresh one. EV/money must not change before a later SAVE refusal. Native battle EVs, vitamins and reducing berries use the selected policy.

Optional Day Care courses use real time or play time, show status by phone and apply results at withdrawal. Durable identity/serials distinguish two subjects; withdrawing one compacts the remaining job safely. Eggs still use steps. Courses neither turn offline time into breeding progress nor silently replace known moves. Existing active development-course journals have explicit migration checks; courses were not present in 1.2.5.

## Shiny Classic, Pro and targeted hunts

Modes are independent of Normal/Plus difficulty and EV policy.

| Mode | Completed target successes | Eligible-generation odds |
| --- | ---: | ---: |
| Classic | No chain required |1/512 |
| Pro |0–9 |1/4096 |
| Pro |10–19 |1/2048 |
| Pro |20–39 |1/1024 |
| Pro |40+ |1/512 |

Pro improvements apply to the target from the next generation. Capturing/defeating it increments once. Another ordinary species, fleeing, losing or drawing resets the chain; excluded encounters suspend it. No threshold guarantees a shiny.

Hunt/Search selects an already-seen species in the current native encounter pool: grass/caves, Surf or an owned rod at a valid position. It respects time/forms/progression and needs40 valid steps. Prepare in settings, Apply, then start when the field is free. It can work under Repel and does not replace a roamer. Effective mode/target changes reset chain/charge; cancelled changes preserve them. Successful Search consumes charge. SAVE preserves mode/target/chain/RNG; full restart resets charge tozero. No save is written per encounter.

Ordinary eligible encounters and new non-forced ordinary statics use the integration; statics use base odds without chain bonus. Eggs/gifts/starters/trades/Mystery Gift/roamers/trainer Pokémon/Safari/contests/doubles/forced events retain native paths. Existing Pokémon are never regenerated to make them shiny. See [complete rules and exclusions](shiny-species-1.3.1.md#controls-and-hunt-rules).

## Species changes

All493 species have individual decisions;67 receive at least one change. Fifty have base-stat changes;51 personal records change because Meganium gains only its second ability. Twenty-nine learnsets receive32 level/move additions, not32 distinct moves. Kricketune gains Technician, Meganium Natural Cure, as second native slots for newly generated Pokémon. Existing abilities/PID/EV/IV/moves are preserved; no automatic ability conversion or new ability-changing service is provided. Learnset additions are acquired through level-up/Move Reminder.

These are base stats, not free EVs/IVs. They affect player/wild/trainer Pokémon in both difficulties. Selective Continue recalculation preserves damage/fainting; PC withdrawal uses native conversion. Redux role ideas are adapted to HGSS/current Plus data, without importing the GenV engine or equalizing base-stat totals. Examples: Rattata HP30→35/Attack56→60/Defense35→40/Sp.Def35→40; Raticate HP65→75/Attack91→96/Defense60→65/Sp.Def70→75; Tentacruel Defense65→75/Sp.Atk80→85 and Sludge Bomb32; Ditto HP48→75/defenses48→65, no Imposter; Kricketune Attack96→106/Speed74→80 and improved bulk. Meganium's stats stay unchanged in this pass.

Complete stat tables and role evidence are in [species changes](shiny-species-1.3.1.md); individual decisions are in [balance-audit.json](../sgp13/data/balance-audit.json). Sample damage/accuracy tests do not establish whole-adventure balance.

## Trainer strategy and portable Box

Plus adds nine targeted move substitutions in seven trainers, retaining existing level scaling. Normal does not apply these substitutions; general species/learnset changes still apply.

| Trainer | Pokémon | Before → after |
| --- | --- | --- |
| Bugsy | Scyther | False Swipe → Bug Bite |
| Morty | Gengar | Shadow Punch → Shadow Ball |
| Chuck | Primeape | Rage → Brick Break |
| Jasmine | Magneton | Spark → Discharge |
| Jasmine | Steelix | Slam → Earthquake |
| Jasmine | Steelix | Rock Polish → Gyro Ball |
| Pryce | Dewgong | Sheer Cold → Rest |
| Will | Xatu | Power Swap → Psychic |
| Lance | Gyarados | Hyper Beam → Waterfall |

The caught Ball marker now also appears for trainer species recorded as caught; this does not solve every historical intermittent wild marker. [Trainer strategy](trainer-strategy-1.3.1.md) preserves the rationale.

Portable Box opens native Move Pokémon from the ordinary field Party with R or its touch command and returns to the same party slot/field. Native deposit/withdraw healing remains accepted behavior. [Its contract](portable-box-1.3.1.md) lists denied contexts, allocation handling and coverage. Summary control legend and configurable Falkner/Bugsy team variants are installed but **inactive** in the published configuration; they are not advertised as playable features.

## Battle, event and save repairs

Will-O-Wisp accuracy is 85; Keen Eye ignores target evasion changes through the same effective-ability contract as Unaware. Post-KO AI keeps the full type score while retaining the native narrow second-stage scratch value. Fairy AI/damage/Conversion2, switch immunity/trapping/absorbing abilities and scripted move evaluation have confined repairs. The battle-loop BL-suffix freeze is causally isolated and corrected; **the older Latios freeze is not proven fixed**.

The [bug audit](bug-audit-1.3.1.md) records each root cause, exact change, reproduction, controls and remaining gate: Safari window/defeat; Lyra/Ethan, Full Heal pickup, fishing, Steven/gifts; Chatot/Pal Pad ownership; Plus save mirrors/expanded Bag refusal/allocation; Waterfall/follower/GS Cup/grass; Giratina/animation/UI/audio; lottery/TM07/Kurt/evolutions/trainer forms; Rage/Transform/Pursuit/U-turn/Pressure/Wonder Guard/Tower; legendary scenes/traded eggs. It separates old inherited fixes from new repairs and from build-pipeline defects. Failed writes are not relabeled successful saves. No lossless migration is invented for already-consumed ambiguous rewards.

Save/Pokémon identifiers and layouts remain stable. New service data is separately versioned/checked, and foreign/future data is not overwritten as empty. Update an existing installation with its language/path/save/settings retained. Compatibility is forward; returning to an older ROM is not a guaranteed reverse migration. Level cap beyond100 is not implemented: reserved150 support would still require EXP,7-bit boundaries, learnsets, stats, UI, breeding/trade/scaling and lossless migration.

## Evidence boundaries

Historical Android functional campaign:49 accepted checkpoints across successive identities,45 native SAVE/cold plus four refusals with entire file unchanged. It is not49 distinct features or 493 battles. Historical final 1.3 run:37 Class A suites,809 executed/52 skips;86 installed-code checks,76 RAM migrations and Class B results are separate, overlapping evidence. Acquired Technician/PC→Party/SAVE/cold is Android proof; numeric Technician/Natural Cure remain ARM proof. Two boss scenes are UI-only without saved victory. Physical IT old-save coverage is separate from AVD Software1x; neither proves universal compatibility or native-equivalent latency.

Current build/source/toolchain/readback/public checks and candidate-bound package evidence are in [source guide](../README.md), [package validation](package-1.3.1-validation.md) and [current UI validation](ui-1.3.1-validation.md). Source-only exporter fixes include public map codecs/read-only model bridge and authenticated V4 bootstrap; they do not change save format or add gameplay. Build-tool findings are recorded separately from ROM bugs.

## Complete affected-species register

Derived from [personal changes](../sgp13/data/species-changes.json), [learnsets](../sgp13/data/learnset-changes.json) and 493 individual decisions. A dash means no new change in that column;426 unchanged species are omitted.

| No. | Pokémon | Base stats changed | New second ability slot | Level-up additions |
|---:|---|---|---|---|
| 19 | Rattata | Yes | — | — |
| 20 | Raticate | Yes | — | — |
| 22 | Fearow | Yes | — | Focus Energy L40 |
| 24 | Arbok | Yes | — | — |
| 28 | Sandslash | Yes | — | — |
| 55 | Golduck | Yes | — | — |
| 57 | Primeape | Yes | — | — |
| 73 | Tentacruel | Yes | — | Sludge Bomb L32 |
| 85 | Dodrio | Yes | — | — |
| 87 | Dewgong | Yes | — | — |
| 97 | Hypno | Yes | — | — |
| 99 | Kingler | Yes | — | — |
| 132 | Ditto | Yes | — | — |
| 144 | Articuno | — | — | Air Slash L50 |
| 154 | Meganium | — | Natural Cure | — |
| 164 | Noctowl | Yes | — | — |
| 165 | Ledyba | Yes | — | — |
| 166 | Ledian | Yes | — | Drain Punch L26 |
| 168 | Ariados | Yes | — | Poison Fang L23 |
| 178 | Xatu | Yes | — | — |
| 182 | Bellossom | — | — | Synthesis L43 |
| 191 | Sunkern | Yes | — | — |
| 199 | Slowking | — | — | Slack Off L43 |
| 206 | Dunsparce | Yes | — | Headbutt L25 |
| 210 | Granbull | Yes | — | — |
| 219 | Magcargo | Yes | — | — |
| 222 | Corsola | Yes | — | — |
| 224 | Octillery | Yes | — | — |
| 225 | Delibird | Yes | — | Ice Shard L22; Roost L32 |
| 226 | Mantine | — | — | Roost L44 |
| 234 | Stantler | Yes | — | — |
| 237 | Hitmontop | — | — | Mach Punch L35 |
| 261 | Poochyena | Yes | — | — |
| 262 | Mightyena | Yes | — | — |
| 267 | Beautifly | Yes | — | — |
| 269 | Dustox | Yes | — | Sludge L23 |
| 283 | Surskit | — | — | BubbleBeam L16 |
| 284 | Masquerain | — | — | BubbleBeam L22 |
| 294 | Loudred | — | — | Hyper Voice L36 |
| 295 | Exploud | Yes | — | Hyper Voice L40 |
| 301 | Delcatty | Yes | — | Hyper Voice L28 |
| 306 | Aggron | Yes | — | — |
| 309 | Electrike | — | — | ThunderShock L9 |
| 310 | Manectric | — | — | Discharge L36 |
| 317 | Swalot | Yes | — | — |
| 321 | Wailord | Yes | — | — |
| 323 | Camerupt | Yes | — | — |
| 326 | Grumpig | Yes | — | — |
| 329 | Vibrava | Yes | — | — |
| 336 | Seviper | Yes | — | Sludge Bomb L34 |
| 337 | Lunatone | Yes | — | — |
| 338 | Solrock | Yes | — | — |
| 340 | Whiscash | Yes | — | — |
| 345 | Lileep | — | — | Mega Drain L18 |
| 346 | Cradily | — | — | Recover L46 |
| 354 | Banette | Yes | — | — |
| 358 | Chimecho | — | — | Psybeam L22 |
| 369 | Relicanth | — | — | Head Smash L50 |
| 389 | Torterra | Yes | — | — |
| 402 | Kricketune | Yes | Technician | Bug Bite L10; Bug Bite L14; Brick Break L26 |
| 411 | Bastiodon | Yes | — | Iron Head L30 |
| 416 | Vespiquen | Yes | — | — |
| 432 | Purugly | Yes | — | — |
| 435 | Skuntank | — | — | Poison Jab L38 |
| 457 | Lumineon | Yes | — | U-turn L31 |
| 470 | Leafeon | — | — | Leaf Blade L33 |
| 477 | Dusknoir | Yes | — | — |

Developer attribution (11 November 2026): the [Battle Party case](validation/party-source-rom-1.3.2.md) connects current source, rebuilt/installed bytes and a bounded normal EN execution witness. Verification-tool changes only; no new game release or performance claim.

The [camera attribution case](validation/camera-source-rom-1.3.2.md) reconstructs the inherited assembly and current table pointers, with stronger bounds/ABI checks. Developer evidence only; no new visual or gameplay behavior.

The [Summary hint attribution](validation/summary-hint-source-rom-1.3.2.md) records exact installed bytes and bounded resource/input checks. It adds developer verification without changing the badge or viewer.

The [Summary controls source/ROM case](validation/summary-controls-source-rom-1.3.2.md) verifies the initially inactive configuration and its ownership conditions. The legend remains inactive in the published game.

The [Rare Candy attribution case](validation/candy-source-rom-1.3.2.md) adds source/byte/caller verification and stricter bench checks. Repeat-use gameplay and save behavior are unchanged.

The [expanded-Bag attribution case](validation/bag-quantity-source-rom-1.3.2.md) verifies the current composition and real Medicine dependency of Rare Candy. It adds developer verification; inventory, consumption, save layout and gameplay remain unchanged.

The [gift-script attribution case](validation/gift-source-rom-1.3.2.md) documents exact helper bytes and the limited current coverage of the inherited key table. It adds verification and records a possible future policy review; no gift, item or save behavior was changed.

The [Fairy-flags source/ROM case](validation/fairy-flags-source-rom-1.3.2.md) links the exact final overlay to both contributing source owners and stronger immunity/ABI checks. It changes verification tooling only.

The [Fairy scalar case](validation/fairy-scalar-source-rom-1.3.2.md) adds exact mixed-ISA execution and build reuse, with exhaustive monotypes and an explicit duplicate-defender falsifier. It records policy differences without changing the game.

The [post-KO caller case](validation/postko-source-rom-1.3.2.md) adds exact caller composition and per-move intermediate checks. Its immunity counterexample distinguishes equal final choices; no game behavior changes.

The [Conversion2 source/ROM case](validation/conversion2-source-rom-1.3.2.md) verifies the current compiled row reader and native RNG state, including a same-output falsifier. It adds tools/tests only.

The [Grounding source/ROM case](validation/grounding-source-rom-1.3.2.md) verifies pointer provenance, finite native damage states and ABI-aware write rules. This changes verification tooling only.

The [Wonder Guard attribution](validation/wonder-guard-source-rom-1.3.2.md) verifies the current effect gate and two status contracts using actual move data. It adds verification tools and a literal-pool admission regression only.

The [Rage attribution](validation/rage-source-rom-1.3.2.md) reconstructs the existing status repair and executes its current controller and native leaf calls. It adds verification tools and tests without changing gameplay.

The [Transform transport attribution](validation/transform-transport-source-rom-1.3.2.md) adds current native packet/consumer checks and recording-only PartyMon requests. It extends the existing Rage evidence without claiming save persistence or changing gameplay.

The [Transform reload attribution](validation/transform-reload-source-rom-1.3.2.md) adds exact source/ELF/readback and guarded-field checks for the existing repair. Optional object retention preserves the default builder behavior; no game or save changes.

The [U-turn attribution](validation/uturn-source-rom-1.3.2.md) identifies current fallback-argument and native-field marker defects and tightens their verification. Reports deliberately retain failed compatibility gates. The game ASM, ROMs and saves remain unchanged; a game repair is pending a separate maintainer decision.

The [native HP continuation](validation/hp-flinch-source-rom-1.3.2.md) reproduces the signed-word collision after the real damage writer and HP script. Earlier controller states and natural battle activation remain unqualified; this adds verification evidence, with no game repair.

The [native U-turn producer](validation/uturn-producer-source-rom-1.3.2.md) qualifies actual script command execution and intermediate packing in a bounded fixture. The existing game compatibility failures remain open; no game repair is included.

The [AfterDamage continuation](validation/afterdamage-source-rom-1.3.2.md) now reaches the erroneous flinch-script request through native states0..6 and their neutral scripts. Applying that effect and natural turn behavior remain separate; no game repair is included.

The [native flinch effect](validation/flinch-effect-source-rom-1.3.2.md) executes script14,ability gates and the target status setter in initialized EN/IT paths. This proves bit application,with lost action/natural battle still separate and no game repair.
