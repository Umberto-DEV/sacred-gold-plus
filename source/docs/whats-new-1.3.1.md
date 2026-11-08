# What is new in Sacred Gold Plus 1.3.1

The shared features below continue in 1.3.2. See the [current change log](../../CHANGELOG.md)
and [five-language validation](validation/localization-1.3.2.md) for localization
and the New Game correction. The 1.3.1 hashes below retain their historical scope.
The current [1.3.2 package revision](validation/package-1.3.2-r2.md) separates the
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
