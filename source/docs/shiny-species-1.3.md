# Shiny modes and species changes in 1.3 development

The development builder installs native Classic/Pro generation, a second Plus
page, targeted search, versioned hunt persistence and balance interventions for
67 species after an individual audit of all 493.
These changes are separate from the published 1.2.5 release. The original global
shiny classifier remains unchanged, preserving existing Pokémon's appearance.

## Controls and hunt rules

Open Options, then the Plus button or SELECT. R or the right header arrow opens
Shiny; L returns to the original five settings. Page ends clamp. D-pad Left/Right
changes the selected value. A applies both Plus pages; B or SELECT cancels them.
Native Options retains its own Confirm/Quit transaction. The interface uses the
native HGSS font, selected frame, palette, row windows and preview panel in EN/IT.

Classic gives each admitted new Pokémon 1/512. Pro gives the selected species
1/4096 at 0–9 completed successes, 1/2048 at 10–19, 1/1024 at 20–39 and 1/512
from 40 onward. The new tier starts with the next generation. Catching or
knocking out the target adds one success; another ordinary species, fleeing,
losing or drawing breaks the chain. Excluded routes pause it. No tier guarantees
a shiny. A 1/512 independent-trial model gives about 63.25% chance within 512
trials; repeating a saved RNG state is not an independent trial.

X opens Hunt. Choose a species already seen and present in the current eligible
native pool. Search supports grass/caves, Surf and each owned fishing rod at a
valid position. It respects current slots, time, forms and progression. Walk 40
accepted steps, select Search after apply, then apply Plus and leave Options.
The request launches only after the field is idle and the location, pool and
owner are revalidated. It deliberately bypasses encounter rate, Repel and
Intimidate suppression. It does not substitute a roaming Pokémon.

Actual mode/target changes reset chain and charge; toggling back before Apply
preserves them. Menus, healing and SAVE preserve chain and current charge.
Successful search consumes charge. Failed or unavailable search retains it.
Changing areas makes a stale request invalid; it does not erase the chain.
Normal SAVE stores mode, target, chain and the separate RNG state. A cold
Continue resets charge to zero. No per-encounter flash writes occur.

Ordinary grass/cave, Surf, fishing, Rock Smash and Headbutt generations use the
mode. New nonforced ordinary scripted statics use base odds, without chain
bonuses. Eggs, gifts, starters, trades, Mystery Gift, roaming Pokémon, trainer
Pokémon, Safari, contests, doubles and forced/fateful events retain their own
native paths. The in-game rules state this scope. Existing Pokémon are never
rerolled. No shiny charm or modern ability engine is added.

## First species batch retained in the expansion

These are **base statistics**, not extra EVs. They apply to wild, player and
trainer Pokémon in both difficulties. EV/IV values and training budgets remain
unchanged. The order below is **HP / Attack / Defense / Speed / Sp. Atk / Sp. Def**.
The existing hack already improves many species; this is a further targeted
batch with distinct roles, rather than a common stat total for every species.

| Pokémon | Previous Plus stats | New stats |
| --- | --- | --- |
| Rattata | 30 / 56 / 35 / 72 / 25 / 35 | 35 / 60 / 40 / 72 / 25 / 40 |
| Raticate | 65 / 91 / 60 / 107 / 50 / 70 | 75 / 96 / 65 / 107 / 50 / 75 |
| Tentacruel | 80 / 70 / 65 / 100 / 80 / 120 | 80 / 70 / 75 / 100 / 85 / 120 |
| Ditto | 48 / 48 / 48 / 48 / 48 / 48 | 75 / 48 / 65 / 48 / 48 / 65 |
| Noctowl | 100 / 50 / 50 / 70 / 86 / 96 | 100 / 50 / 65 / 70 / 96 / 96 |
| Ledian | 55 / 95 / 50 / 85 / 35 / 110 | 65 / 100 / 60 / 85 / 35 / 110 |
| Ariados | 70 / 90 / 70 / 80 / 60 / 60 | 80 / 100 / 75 / 80 / 60 / 70 |
| Dunsparce | 105 / 80 / 70 / 45 / 65 / 65 | 110 / 90 / 80 / 45 / 65 / 75 |
| Magcargo | 50 / 50 / 135 / 30 / 115 / 115 | 65 / 50 / 135 / 30 / 115 / 110 |
| Corsola | 55 / 55 / 115 / 35 / 105 / 110 | 70 / 55 / 115 / 35 / 105 / 110 |
| Delibird | 45 / 55 / 45 / 75 / 65 / 45 | 65 / 85 / 60 / 95 / 70 / 60 |
| Beautifly | 60 / 70 / 50 / 85 / 105 / 65 | 70 / 70 / 60 / 85 / 110 / 70 |
| Dustox | 60 / 50 / 70 / 65 / 65 / 105 | 70 / 50 / 85 / 65 / 75 / 110 |
| Delcatty | 70 / 75 / 65 / 90 / 95 / 55 | 80 / 75 / 70 / 95 / 95 / 75 |
| Seviper | 73 / 100 / 60 / 65 / 100 / 60 | 80 / 105 / 65 / 75 / 105 / 65 |
| Kricketune | 77 / 96 / 59 / 74 / 55 / 59 | 85 / 106 / 70 / 80 / 55 / 70 |
| Lumineon | 69 / 69 / 76 / 101 / 89 / 86 | 79 / 69 / 81 / 101 / 94 / 91 |

Tentacruel keeps its fast special-tank role with a modest physical Defense and
Sp. Atk increase. Ditto gains HP and pre-Transform defenses; native Transform
copies the target's non-HP stats, so increasing its Attack would mostly be lost.
Rattata remains fragile; Raticate gains more durability while retaining the
accuracy cost of Hustle. Delibird gains priority/utility while retaining its
fourfold Rock weakness. Magcargo intentionally trades five Sp. Def points for
more HP rather than receiving increases everywhere.

The 11 further level-up additions are Sludge Bomb at 32 for Tentacruel, Drain Punch at 26
for Ledian, Headbutt at 25 for Dunsparce, Ice Shard at 22/Roost at 32 for Delibird, Sludge at 23 for
Dustox, Hyper Voice at 28 for Delcatty, Sludge Bomb at 34 for Seviper, Bug Bite at 10/Brick
Break at 26 for Kricketune and U-turn at 31 for Lumineon. The earlier Ariados Poison
Fang at 23, Chimecho Psybeam at 22 and Kricketune Bug Bite at 14 additions remain. Existing
owned moves are not replaced; eligible older Pokémon use the native reminder.
The move table, types and evolution archive are unchanged.

Kricketune retains Swarm and gains native Technician in its previously empty
second ability slot for newly generated Pokémon. Saved Swarm individuals keep
their ability. No implicit ability conversion or ability-change service exists.
The other species in this first batch keep their current ability slots.

A guarded Continue hook calls native stat recalculation only for the selected
species, preserving boxed identity, IVs, EVs, moves, ability and status. Native
HP-delta behavior retains existing damage and fainting. No new game is required.
The first batch affected 93 trainer records containing these species; improved
player options can therefore strengthen opponents too. No claim of complete
adventure balance follows from these edits alone.

## Expanded audit of all 493 species

The subsequent pass audits every species and its evolutionary role in
[the authored decision register](../sgp13/data/balance-audit.json). It retains
mechanically strong low-total species and the existing alternate-form designs.
The extension adds 49 interventions to the earlier 18 affected species:
**67 species total**, comprising **50 species with base-stat changes**, **two
ability-slot additions** (Kricketune and Meganium), and **32 additive level-up
entries across 29 species**. These categories overlap. There are 51 guarded
personal records because Meganium receives an ability slot without a stat change.

The 33 additional stat changes below are relative to the accepted first-batch
build, in HP / Attack / Defense / Speed / Sp. Atk / Sp. Def order. Original
1.2.5 member hashes guard the assembled patch. EVs, IVs, EV yields, types,
evolutions, TM compatibility and global move effects remain unchanged.

| Pokemon | Before | After |
| --- | --- | --- |
| Fearow | 65 / 95 / 65 / 105 / 61 / 61 | 65 / 105 / 65 / 105 / 61 / 61 |
| Arbok | 60 / 91 / 69 / 86 / 65 / 79 | 70 / 106 / 69 / 86 / 65 / 79 |
| Sandslash | 75 / 100 / 110 / 65 / 45 / 55 | 85 / 100 / 110 / 65 / 45 / 65 |
| Golduck | 80 / 82 / 78 / 85 / 95 / 80 | 80 / 82 / 78 / 90 / 105 / 80 |
| Primeape | 65 / 105 / 60 / 95 / 60 / 70 | 65 / 105 / 60 / 105 / 60 / 70 |
| Dodrio | 60 / 110 / 70 / 100 / 60 / 60 | 60 / 110 / 70 / 110 / 60 / 60 |
| Dewgong | 90 / 70 / 80 / 70 / 80 / 95 | 90 / 70 / 90 / 70 / 90 / 95 |
| Hypno | 85 / 73 / 70 / 67 / 73 / 115 | 95 / 73 / 80 / 67 / 73 / 115 |
| Kingler | 55 / 130 / 115 / 75 / 50 / 50 | 65 / 130 / 115 / 75 / 50 / 60 |
| Ledyba | 40 / 20 / 30 / 55 / 40 / 80 | 40 / 40 / 30 / 55 / 40 / 80 |
| Xatu | 65 / 75 / 70 / 95 / 95 / 70 | 65 / 75 / 70 / 95 / 105 / 80 |
| Sunkern | 30 / 30 / 30 / 30 / 30 / 30 | 40 / 30 / 40 / 30 / 30 / 40 |
| Granbull | 90 / 120 / 75 / 45 / 60 / 60 | 90 / 120 / 75 / 45 / 60 / 70 |
| Octillery | 75 / 105 / 75 / 45 / 105 / 75 | 75 / 105 / 75 / 45 / 115 / 75 |
| Stantler | 73 / 100 / 62 / 85 / 85 / 65 | 73 / 100 / 62 / 85 / 85 / 75 |
| Poochyena | 35 / 55 / 35 / 35 / 30 / 30 | 35 / 60 / 35 / 40 / 30 / 30 |
| Mightyena | 70 / 105 / 70 / 80 / 60 / 60 | 70 / 110 / 70 / 85 / 60 / 60 |
| Exploud | 104 / 91 / 63 / 68 / 91 / 63 | 104 / 91 / 63 / 68 / 105 / 73 |
| Aggron | 70 / 110 / 180 / 50 / 60 / 60 | 80 / 110 / 180 / 50 / 60 / 70 |
| Swalot | 100 / 83 / 83 / 55 / 83 / 83 | 110 / 83 / 88 / 55 / 83 / 88 |
| Wailord | 170 / 90 / 45 / 60 / 90 / 45 | 180 / 90 / 50 / 60 / 90 / 50 |
| Camerupt | 70 / 100 / 70 / 40 / 105 / 75 | 85 / 100 / 70 / 40 / 105 / 75 |
| Grumpig | 80 / 45 / 65 / 80 / 90 / 110 | 80 / 45 / 75 / 80 / 95 / 110 |
| Vibrava | 50 / 70 / 50 / 70 / 50 / 50 | 60 / 75 / 55 / 70 / 60 / 55 |
| Lunatone | 70 / 55 / 65 / 70 / 115 / 85 | 80 / 55 / 65 / 70 / 115 / 85 |
| Solrock | 70 / 115 / 85 / 70 / 55 / 65 | 80 / 115 / 85 / 70 / 55 / 65 |
| Whiscash | 110 / 78 / 73 / 60 / 76 / 71 | 110 / 93 / 83 / 60 / 76 / 76 |
| Banette | 64 / 115 / 65 / 65 / 103 / 63 | 74 / 120 / 65 / 65 / 103 / 68 |
| Torterra | 95 / 109 / 105 / 56 / 75 / 85 | 105 / 109 / 105 / 56 / 75 / 85 |
| Bastiodon | 60 / 52 / 168 / 30 / 47 / 138 | 70 / 72 / 168 / 30 / 47 / 138 |
| Vespiquen | 70 / 80 / 102 / 40 / 80 / 102 | 80 / 90 / 102 / 40 / 80 / 102 |
| Purugly | 100 / 86 / 64 / 112 / 64 / 59 | 100 / 95 / 70 / 112 / 64 / 59 |
| Dusknoir | 45 / 100 / 135 / 45 / 65 / 135 | 60 / 100 / 135 / 45 / 65 / 135 |

Meganium keeps Overgrow and gains Natural Cure in its previously empty second
slot, matching the support ability already available to Chikorita and Bayleef.
Newly generated individuals can use that slot. Existing Meganium keep their saved
ability; loading does not silently replace Overgrow. The inherited personal table
has slots 65/0, not a pre-existing Leaf Guard slot.

Additional learnset entries preserve every existing entry and stay within the
native reminder's 20-entry limit for edited members:

| Pokemon | Additional level-up access |
| --- | --- |
| Fearow | Focus Energy at 40 |
| Articuno | Air Slash at 50 |
| Bellossom | Synthesis at 43 |
| Slowking | Slack Off at 43 |
| Mantine | Roost at 44 |
| Hitmontop | Mach Punch at 35 |
| Surskit | BubbleBeam at 16 |
| Masquerain | BubbleBeam at 22 |
| Loudred | Hyper Voice at 36 |
| Exploud | Hyper Voice at 40 |
| Electrike | ThunderShock at 9 |
| Manectric | Discharge at 36 |
| Lileep | Mega Drain at 18 |
| Cradily | Recover at 46 |
| Relicanth | Head Smash at 50 |
| Bastiodon | Iron Head at 30 |
| Skuntank | Poison Jab at 38 |
| Leafeon | Leaf Blade at 33 |

Several moves were already available late or through a TM. Earlier level-up
access helps those roles during progression; it does not grant moves directly
to existing Pokemon. Native level-up or the reminder supplies them. Existing
21-entry Lopunny data is untouched. A repeated move still known is skipped by
native generation, so generated moves are not simply the last four learnset rows.
Explicit trainer moves remain unchanged; trainer parties using default moves can
change. For example, Edwin's level-54 Cradily now initializes Amnesia,
AncientPower, Gastro Acid and Recover, replacing Confuse Ray.

The proposed Lopunny Attack increase from 76 to 96 was rejected after native
Whitney checks. Her constructor gives friendship 255, making Return power 102.
At level 21, IV 15, EV 0 and neutral nature, the conditional probability that
Fake Out plus Return knocks out Quilava rose from 12.45% to 98.97%; Attack 86
still produced 62.58%. These calculations enumerate native damage/accuracy and
critical branches under independent attacks, with no opponent actions or items;
they are not battle win rates. Lopunny retains its fast utility role and original
Attack. A future offensive redesign needs a separately evaluated early-team change.

A 64-byte bitmap replaces the former 17-ID Continue list. Its configuration
checks species bounds, count, reserved bits and population count before accessing
the party. It covers IDs 1–493 without changing saved-data layouts or identifiers.
Native recalculation preserves damage, fainting, status and boxed identity; native
withdrawal supplies current stats for boxed Pokemon.

Il [rapporto Android del 29 ottobre 2026](android-1.3-dev-validation.md)
registra i pin finali v3, 49 checkpoint accettati, acquisizione ordinaria di
Kricketune/Tecnico e i confini delle prove Android/ARM. Le verifiche qui sotto
restano risultati storici dei candidati balance-v1 e shiny-v4, con i propri
hash e conteggi.

### Expanded candidate verification

Fresh composed candidate-v1 builds pass all stage and final readbacks in EN and
IT. Their SHA-256 values are respectively
`a290df71a54ea016f4e19cd9e6f8f94e1f8d1f675b4d2dcd209c058d4f6a5b12` and
`f7585f5248f483a4bbe12424954a805a86ff9d744f58b62a135e750a7f00099e`.
All 203 builder-tracked sources matched the receipts at the post-build check.
A later, separate storage-maintenance task changes only host `sgp13/build.py`
and `sgp13/test_build.py`; the other 201 tracked sources remain exact. These
immutable candidate results precede that host-tool change and do not claim a new
build from it. Both final configs use
ABI 2 with the exact 51 selected species. Personal, growth, moves, effects,
learnsets and weights, both battle overlays and the sampled native stat code
match between languages.

The balance snapshot source runner passes 1,017 collected tests: Class A executes 797 and
skips 52; Class B executes nine and skips 159 without its optional input set.
Those skips are not credited as executed coverage. Separate private-input checks
pass all 29 species/learnset tests, including 918 native stat cases and 188 native
move-initialization windows. The final-candidate shiny suite passes 111 tests on
its initial run; its one parameterized EN/IT installer test stopped for host disk
exhaustion and passes on a scoped repeat after lossless intermediate compression.
All 112 focused cases are thereby exercised, with the interrupted log retained.
All 31 Plus UI tests pass, including actual EN/IT font checks.

Actual native stat measurements cover all 493 species at levels 30 and 50 on the
baseline and each final candidate: 2,958 comparisons, zero skipped species or
native assertions. Both candidates also execute 12 controlled role scenarios
with identical results. At level 50, IV 15/EV 0 and neutral nature, Hypno's
HP-times-Defense proxy rises 19.6%, Sandslash's HP-times-Sp.-Defense rises 23.0%
and Dusknoir's two proxies rise 13.4%. These products exclude typing and ability
effects. Fearow's native Drill Peck damage against the documented neutral control
rises 52–63 to 58–69; Hypno's Psychic damage remains unchanged. The archive grants
all 12 selected final moves by the tested level, possibly requiring the reminder.
Baseline Bastiodon level-30 Iron Head is explicitly counterfactual: its new
level-30 access is part of the benefit, not a demonstrated old option.

The expanded personal selection occurs in 256 trainer records, with the 50
stat-edited species appearing in 248. Explicit trainer move lists are unchanged;
level-default generation follows the updated learnsets. Primeape's Speed increase
can change Chuck's move order: at neutral level 34/IV 15/EV 0 it rises 74 to 81.
These are data and native-kernel checks, not played trainer-win-rate estimates.

The expanded raw-save matrix passes **29 Continue → native SAVE → cold pairs**,
comprising 58 successful candidate processes and 468 party observations. It covers
legacy saves without Plus, configured Plus, expanded Bag, active v1 courses,
SHINY_ONLY, positive v4 hunts, five changed party species and unchanged controls
in both languages (plus an advanced IT save). All 19 unique original fixture paths
retain their hashes. Progress, inventory, boxed Pokemon, Plus settings and
nonstat party bytes remain exact in the inspected blocks; cold SRAM matches its
saved input exactly. Active course migration preserves four jobs and their rewards,
with the documented 43-second native SAVE catch-up. Positive hunts preserve mode,
target 75, chain 1 and RNG; cold charge remains zero.

Ordinary battles on the original ROM prepared two additional raw fixtures.
Damaged Sandslash changes from 8/65 to 12/69 in each candidate, retaining exactly
57 damage. Fainted Sandslash changes from 0/65 to 0/69 and remains fainted; PP 38
and identity are preserved. Both first passed independent old-ROM cold Continue.
This raw matrix observes refreshed species 19, 28, 87, 97 and 262; it does not
claim all 51 species or universal save compatibility. Ten initial input/capture
failures are retained: an extra A reopened the PC, or the RAM dump landed during
native Pokemon decryption. Corrected input and checksum-valid stable snapshots
pass; all accepted party bytes also match the actual raw SAVE. No guest writes,
cheats or savestates substitute for these checks.

Two independent final-candidate wild-battle scripts and their separate cold
processes pass in EN and IT, totaling four accepted processes and 44,156 guest
frames. Sandslash uses max HP 69 and Sp. Def 36 after normal item healing and in
battle. EN faces Graveler 45: Rock Blast takes 51 HP, Rock Smash deals 24, and a
normal switch to Blastoise followed by Surf wins. IT faces newly changed Grumpig
46: its generated stats match the candidate oracle; Rock Smash deals three,
Blastoise takes 22 from Dazzle Gleam, then escapes. These different encounters
are not paired balance trials. A first shared-timing IT attempt is retained and
excluded because it navigated different turn messages incorrectly.

Both runs visibly open the second native Plus/Shiny page, stage Pro, cancel,
and reopen unchanged Classic settings; both the legacy Plus region and logical
Shiny state remain exact. Guide topic/content navigation returns to the field.
A normally consumed Hyper Potion and all battle party changes persist through
native SAVE and cold Continue, with exact raw-party bytes. An apparent 65/65 HUD
reading was independently resolved as a small-font misreading of 69/69 by enlarged
pixels and actual BattleMon data; no stat reset occurred.

A separate ordinary EN trainer fight passes against Fisherman Wilton 124 on
Route 44, reached by native Fly and walking. His Wailord 48 has actual IV/EV 0,
nature Brave and native stats 230/100/53/55/91/53; old bases would yield
221/100/48/55/91/48. Surf changes its HP 230→186, a second underwater hit gives
186→94, and Thunderbolt finishes it. Wailord uses Dive and deals 55 damage.
Victory awards 1,536, sets the trainer flag, returns to the field, and survives
native SAVE/cold Continue. Both processes pass crash and reserve checks. The
only logical party-byte difference on cold registration is the native follower
mood reset 39→0; identity, moves, PP, EVs, IVs, HP and stats persist. Raw cold SRAM
remains byte-exact with the saved input. This is one representative affected
trainer, not a campaign difficulty or boss win-rate study.

Independent final code/data/evidence review accepts this local balance expansion
without a production-code fix. The older v4 campaign below remains historical
evidence. Published release assets are unchanged.


## Research and measured effects

The design used [Redux 1.4.1's author documentation](https://drive.google.com/file/d/1AhsdffDiz872gwIB-kiGKutDAsM-GWvS/view),
[Renegade Platinum's species document](https://pastebin.com/uw0pkBWN) and
[Inclement Emerald 1.13's pinned source](https://github.com/BuffelSaft/pokeemerald/blob/cf41a95b68a39ca74fefeb934c460f6f47eb0b3b/src/data/pokemon/base_stats.h).
They support role-specific stats, ability synergy and earlier useful moves,
but disagree on individual roles. We used only abilities and effects present in
this engine and authored the local values. Foreign documentation/tables are not
bundled. Modern Imposter, Strong Jaw and Refrigerate were not imported.

Controlled native damage probes at level 30, IV 15, EV 0 and neutral nature found
Tentacruel's incoming neutral Body Slam range fall from 45–54 to 40–48, with HP 92
unchanged. Raticate's corresponding range falls 48–57 to 45–54 while HP 83 becomes 89.
Ditto's controlled maximum physical hit falls 67 to 54 and HP 73 becomes 89; native
Transform retains those HP while copying the target's other stats and ability.
These execute native damage/stat/effect code with explicit harness services.
They are conditional calculations, not measured complete-battle win rates.

## Ownership and evidence boundaries

The new code lives in the guarded ARM9 reserve at 0x023C8000–0x023D0000; older
public addresses remain fixed. The installer checks native instruction hashes,
resident bounds, overlay metadata, archive members and final composed output.
It preserves the already installed Guide, expanded Bag and save-feedback fix.

Training owns the two 256-byte TNR1 journal records. Wire v2 keeps all v1 offsets
and CRC placement; validated v1 migrates losslessly. A SHINY_ONLY flag allows
hunt persistence without activating training or consuming historical rewards.
Future/foreign storage is refused. Shiny UI calls an owner API with epoch/context
checks; it never reads guessed save offsets or calls an unloaded field overlay.

The pure lottery has exhaustive word-threshold tests, 6,400 reduced PID classes
executed as Thumb and a finite 157-probe transform bound. It preserves nature and
the full low PID byte, while using final OT. The native generation differential
checks preserve IVs, held-item/form behavior and native RNG position for the
recorded constructor, Synchronize, Cute Charm and Unown cases. This does not
establish every native branch or uniform distribution among valid PIDs.

The first-batch stat suite checked 306 native recalculations (17 species × 3 levels × 3 EV
profiles × 2 languages). Continue tests include damaged/fainted Raticate and
idempotent repeated loading. The UI suite executes the compiled controller,
including cancel/apply, simultaneous inputs, short legacy layout, allocation
failure and method-only changes; both-language font checks cover 493 species
names. Kernel tests are not a substitute for whole-party boss trials or hardware
testing. The full-game campaign below records separate evidence and found defects
that the earlier component tests missed.


## Full-game acceptance campaign

Private tests use the software-interpreter melonDS harness, ordinary game input,
copied raw saves and separate cold processes. No cheats, guest RAM writes or
savestates are used for these acceptance runs. Original fixtures are hashed and
retained. ROMs, raw saves, extracted game data and RAM dumps are private artifacts.

The v3 save matrix passed 22 processes: nine older-save fixtures through native
SAVE and cold Continue (legacy/no Plus, configured Plus, expanded Bag and active
courses in EN/IT, plus one advanced IT fixture), and two mode-only SHINY_ONLY
fixtures through SAVE/cold. Both active-course v1 journals migrate to v2 while
preserving jobs and rewards; native elapsed play time advances normally. Player
progress, inventory, existing Plus settings, party identity, boxes and daycare
are compared. These stationary fixtures do not exercise the complete shiny
generation route.

A separate real 1.2.5 PC withdrawal and native SAVE produces an older fixture
with level-43 Rattata in the party. Both v3 languages load it through Continue,
recalculate its stats from 92/59/52/80/39/48 to 96/62/57/80/39/52, save normally
and retain the result after cold restart. An independent formula agrees. The
136-byte boxed identity, moves, PP, IVs, EVs and other five Pokémon remain exact.
This is one changed species at full HP; the 306 recalculation cases and 34 actual
native boxed-to-party conversion cases provide additional bounded coverage.

UI stress passed 64 open/navigate/close cycles per language (21,254 frames each)
on v2b, with reserve guards, released owned strings and unchanged raw SRAM. The
UI controller is unchanged in v3. Heap snapshots return to their prior free-byte
counts after closing Guide; no continuous minimum or universal leak claim follows.

Two defects were discovered by ordinary gameplay and are retained in the private
evidence rather than counted as successful shiny acceptance. First, native
Options entry bypassed the general field-exit hook and left the previous area's
encounter pool cached. A guarded Options-launch hook and an actual-native caller
regression repair this in v3; the real Route 45 selector then lists its current
species. Second, v3's generation guard rejects the native DTCM stack address of
its temporary encounter structure. Search reaches the selected battle and
consumes charge, but the new lottery and chain are bypassed. V4 repairs the scoped pointer guard with full-object alignment/bounds checks
while retaining strict owner/setup checks. The new regression executes the
actual native Regular caller, producer and constructor with DTCM stack and
main-RAM/DTCM encounter objects across all five methods and both languages.
Twenty cases verify one committed draw and exactly one KO settlement.

The v3 nonzero-charge fixture proves SAVE retains charge40 and cold Continue
resets it to0 in both languages. Its journal has Pro/Graveler but chain0 and an
uninitialized lottery RNG, so this result does not prove positive-chain/RNG
persistence. Corrected-candidate gameplay results are recorded below.


## Corrected v4 candidate and final results

These are private development builds, not a replacement for any published file:

| Language | ROM SHA256 |
| --- | --- |
| EN | `94b281572f293ba54f30ba4972bffda4bbb56d8a5c2f744e61b727de3ddda519` |
| IT | `d928304a324d1cb8bd8c4fa249df629d2a63b8789ef285d94b8d248b98fd2ecd` |

Both builds pass the full installer/readback/composition checks after Guide. The
final registered runner passes **995 collected, 786 executed, 209 explicitly
skipped**: Class A 777 executed/52 skipped; Class B 9 executed/157 skipped.
Unavailable private-input suites are not counted as exercised. The separate
private native-shiny suite passes **87 test executions with no skips**, including
actual constructors, DTCM callers and both-language installation verification;
inherited cases mean this is not 87 distinct gameplay scenarios. The all17-species
306 stat calculations and 34 boxed-copy cases are additional earlier evidence
for unchanged final personal data and recalculation code.

The complete older-save campaign is repeated on these exact v4 builds:
**26 successful processes** cover the 22-process matrix above and four additional
changed-party SAVE/cold processes. Rattata recalculation, party identity, boxes,
inventory, expanded Bag, Plus settings and active courses pass the same strict
comparisons. Original fixtures remain unchanged.

Four additional ordinary-input gameplay processes pass in EN/IT:

- Classic produces a new ordinary wild encounter through the real field engine,
  initializes/advances the separate lottery RNG once and arms one battle outcome.
- Pro charges to40, queues Search in Options, waits until the field is idle,
  bypasses an active Repel and generates the selected Graveler at native level45.
  Charge becomes0, one draw is committed and the target KO advances chain0→1
  exactly once. Canceling a draft mode change preserves mode, target, chain and
  RNG. Walking recharges to40; native SAVE writes valid generation118 journals
  with chain1 and initialized RNG in each language.

Offline native Pokémon getters on copied battle RAM verify final species, level,
PID and full OT while restoring encrypted records exactly. The PID classifier
agrees with each recorded lottery outcome. These four observed encounters are
nonshiny; they establish actual wiring, not an empirical frequency estimate.
The forced-shiny constructor tests and exhaustive threshold tests cover the
other outcome. All four processes pass crash and reserve-guard checks.

The first scripted positive-state export was rejected because native Repel
expiry/reuse prompts intercepted the SAVE input. Its raw journal was unchanged;
it is not counted as persistence evidence. The successful rerun explicitly
dismisses those prompts and checks the real SAVE screen and raw journal CRC.

Two further cold processes pass from those separately verified positive raw saves.
Both retain mode Pro, target75, chain1 and the exact initialized RNG, while charge
resets40→0. Native/Plus field hashes, full raw SRAM and original fixtures remain
exact. This makes **32 accepted final-v4 runtime processes** across the older-save,
changed-party, Classic, Pro and positive-state cold tests.

Remaining limits: no DS hardware campaign, full-adventure boss win-rate study,
or exhaustive real-game map/time/pool/method coverage. This batch improves
measured roles and move access; it does not establish equal strength for every
species or globally optimal teams.
