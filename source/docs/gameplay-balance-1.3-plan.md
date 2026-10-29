# Gameplay balance and shiny modes for 1.3

The aim is to support more useful teams throughout Johto and Kanto, including
Pokémon that struggle to contribute before their strongest moves arrive. Balance
changes start from the actual Plus tables and acquisition routes. The inherited
game already raises one or more base stats for 98 species and lowers them for
five, so a weak reputation in the original games is not sufficient evidence for
another stat increase.

The development builder now installs the native shiny modes, targeting, hunt
persistence and the expanded 493-species balance audit: 67 species receive
stat, ability-slot or level-up-access changes (overlapping categories). See the [implemented mechanics and
validation](shiny-species-1.3.md) for the current scope, values and evidence.
The earlier pilot measurements below remain historical evidence. Neither the
published 1.2.5 release nor the inherited global shiny classifier is changed.

## Lessons from other hacks

[Drayano's FAQ](https://pastebin.com/UEzNBDHC) confirms Renegade Platinum's default
shiny rate of 1/512 and optional rarer alternatives, plus Redux's 1/512 rate.
It also explains why different display thresholds can change a Pokémon's shiny
appearance when traded. This supports a casual 1/512 profile and preserving the
existing classifier while changing only future generation.

[Redux 1.4.1 documentation](https://drive.google.com/file/d/1AhsdffDiz872gwIB-kiGKutDAsM-GWvS/view)
shows adjustments to early difficulty, move access and evolution timing as well
as stats and abilities. Its preceding 1.4.0 update weakened particular early
threats while retaining later challenge. We adopt that attention to progression;
Unova's move levels and opponent teams cannot be transplanted into Johto.

[Crystal Clear's official tracker documentation](https://github.com/ShockSlayer/ccdocs/blob/942f2f28154bf9536b6f75470dc6f1e1ce1f08e1/docs/Documentation.md)
provides a useful precedent for selecting a species and maintaining hunt progress.
Its DV mechanics and approximate chain rates are not the HGSS probability model.
Species selection and shiny probability will be separate, visible mechanics here.

## Expanded species balance mandate — 28 October 2026

The expanded pass is now implemented. All 493 species have an individual
[authored decision](../sgp13/data/balance-audit.json), including evolutionary
roles and reasons for retaining already useful species. It adds 49 interventions
to the earlier 18 affected species: 50 species now have revised base stats, two
have an additional native ability slot, and 29 have 32 additive learnset entries.
Those categories overlap, giving 67 affected species in total. The complete
before/after tables and validation are in [the implementation report](shiny-species-1.3.md).

The author's Redux 1.4.1 `Pokemon Changes.txt` contains 186 explicit custom
`Base Stats (Complete)` sections: 156 concern species 1–493. Of the 186, 166
increase the stated total and 20 redistribute it without increasing the total.
These are counts from that specific document, not counts of every Pokémon
affected by its wider move, ability, type or official-generation updates. The
document hash is `a7d695e001fcca49a8a1f0c74206f7b8e55f3be3bba528bc0cf5381da8e5dc3b`.
Redux gives different roles different totals: its Complete Raticate and Delibird
reach 440, Ledian 450, Sunflora 475 and Flygon 600. Ditto instead gains Imposter.
Its custom Complete changes must be distinguished from its Classic edition;
those edition names are unrelated to this project's shiny profiles.

A read-only census of our accepted v4 EN build
(`94b281572f293ba54f30ba4972bffda4bbb56d8a5c2f744e61b727de3ddda519`)
finds 229 nonlegendary/nonmythical terminal species, defined by having no
outgoing evolution in the actual evolution archive. Their mean base-stat total
is 490.50 and median is 490. Forty are below 460, including mechanical exceptions
such as Shedinja, Smeargle, Wobbuffet and Medicham. Neither 490 nor 460 is an
automatic target or buff threshold. First-stage Pokémon must be compared with
their own progression peers rather than final forms. Private extracted records
remain outside public source.

The implemented pass compares current roles, native ability effects, types,
move timing and acquisition/evolution evidence. It preserves strong low-total
mechanics such as Huge Power, Pure Power, Speed Boost, Wonder Guard and Sketch.
Early stages keep progression differences; no common final-form total is imposed.
The inherited buffs for species such as Furret, Mawile and Sableye are considered
before deciding whether another increase is justified.

Native measurements use matched levels, IVs, EVs and natures, enumerate damage,
accuracy and critical branches, and distinguish offensive improvements from
speed or durability changes. A proposed Lopunny Attack increase was rejected
because Whitney's native friendship-255 Return crossed early starter KO
thresholds too sharply. These are conditional matchup measurements, not an
estimate of whole-team or complete-adventure win rates. Broader player campaign
and hardware coverage remains a separate validation task.

The former 17-ID Continue list is replaced by a validated 64-byte bitmap covering
IDs 1–493; the final configuration selects 51 personal records, including
ability-only Meganium. Save layouts remain unchanged. Existing identity, ability,
IVs, EVs and moves are preserved; native stat recalculation retains damage and
fainting. New level-up access is additive, respects the edited reminder limits
and does not silently replace owned moves. Modern Redux abilities such as
Imposter are not included without an engine implementation.

## Selected shiny profiles

Classic makes incidental encounters more accessible. Pro is an optional, rarer
hunting challenge with species research. It is deliberately less generous per
eligible Pokémon before reaching its last stage.

The audited inherited Plus classifier corresponds to 255/65,536, approximately
1/257, for an unconstrained uniform XOR. Thus the selected Classic 1/512 is
already rarer than that inherited baseline. Special producers such as Cute Charm
and Masuda do not necessarily have this unconstrained rate. The new profiles
apply only to the explicitly admitted future-generation routes below.

| Mode and completed target successes | Chance for the next eligible Pokémon |
| --- | ---: |
| Classic | 1/512 |
| Pro, 0–9 | 1/4096 |
| Pro, 10–19 | 1/2048 |
| Pro, 20–39 | 1/1024 |
| Pro, 40 or more | 1/512 |

A success means catching or defeating the selected species in an eligible wild
battle. The tenth success improves the eleventh generation, not the tenth.
There is no guaranteed shiny at a milestone. At constant 1/512, 512 independent
eligible generations give about 63.25% probability of at least one shiny.

The model uses `1 - product(1 - p_i)`. Under the explicit assumptions that all
encounters are eligible target encounters, every nonshiny encounter advances the
chain and the chain never breaks:

| Measure | Classic | Pro |
| --- | ---: | ---: |
| At least one shiny within 100 generations | 17.76% | 13.43% |
| Within 512 generations | 63.25% | 61.31% |
| Generations reaching 50% probability | 355 | 381 |
| Generations reaching 90% probability | 1,178 | 1,205 |

These are conditional probability calculations, not time estimates or guarantees.
Searching for a rare species can improve target availability independently of
these rates. Reloading the same RNG state is not an independent new sample.

### Implemented hunt rules

- Select a species already seen and available in the current native encounter
  table, respecting method, time, level, form and progression. Ordinary grass,
  caves, Surf and fishing are the initial scope.
- Recharge an explicit search through normal steps; 40 steps is the initial
  tuning value, to be measured in ordinary play. Start the requested battle
  only from an idle field task. Preserve the species' actual eligible slot levels.
- Catching or defeating the target advances the chain once. Another ordinary
  species, escape or player defeat breaks it. Changing the target or mode resets
  chain and charge. Re-selecting the same target preserves progress.
- Menus, healing and saving preserve the chain and current charge. Invalid
  locations or methods pause searching and invalidate a queued stale request.
  Excluded battles pause the chain; an admitted ordinary defeat breaks it.
- SAVE preserves mode, target and chain. Continue resets step charge only.
  No flash write occurs per encounter, and no old Pokémon is regenerated.
- New eligible static encounters use the mode's base chance, without chain
  bonuses. Preserve forced identities and forced shiny events. Eggs, gifts,
  starters, NPC trades, Mystery Gift, previously created roamers, trainer Pokémon,
  Safari, contests and multiple encounters need separate route contracts before
  admission. The native help must state the covered methods and exceptions.

### Generation and save requirements

Keep the inherited global test `TID XOR SID XOR PID_low XOR PID_high < 255`.
Changing it would alter existing Pokémon's appearance. For newly admitted
generation, decide the outcome once: construct a shiny PID with XOR below 8 or
a nonshiny PID with XOR at least 255. Preserve selected nature, gender, ability
parity, separately stored form and final OT. Existing Pokémon remain byte-identical.

The reference sampler preserves nature and the full PID low byte, needs at most
157 candidate inspections for shiny output, and at most one correction for
nonshiny output. An exhaustive reduced-domain test covers all 6,400 classes.
It is not uniform over valid PIDs. Ordinary Wurmple's future evolution, Spinda's
spots and other derived traits follow the final PID of the new specimen.
Legacy constructors that select a PID-derived Unown letter remain excluded.

Before a native hook is added, establish final-OT timing, lottery draw placement,
IV and held-item RNG preservation, compiled cost and each producer's eligibility.
Do not retry the whole Pokémon constructor or use an uncontrolled fallback.
The Python reference remains independent; the native adapter now uses the
compiled core and guarded final-construction hooks described in the implementation report.

Hunt persistence requires explicitly owned storage and a lossless versioned
migration. Reserved journal bytes are not free space. Preserve Plus settings,
expanded Bag, courses, rewards and progress. Test copied older EN/IT raw saves
through Continue, native SAVE and cold restart, including missing new data,
interrupted writes and retries, before enabling the mode.

## First learnset additions

The builder guards personal, move and learnset archive hashes and each affected
member. It adds moves in both difficulties without removing old moves or changing
types, evolutions or existing owned moves. The later species stage changes base
stats and one ability slot as documented in the implementation report. The native move
reminder can offer the additions to eligible existing Pokémon.

| Pokémon | Addition | Intended contribution | Retained limitation |
| --- | --- | --- | --- |
| Ariados | Poison Fang at 23 | Physical Poison attack just after Spinarak evolves at 22 | Flying and other unfavorable matchups still require teammates |
| Chimecho | Psybeam at 22 | A special Psychic step between Confusion and later Extrasensory | Friendship evolution affects access; faster Ghost attackers remain dangerous |
| Kricketune | Bug Bite at 14 | Usable early physical Bug attack before X-Scissor | Does not solve its speed, bulk or Flying weakness |

Native routines supplied damage rolls, effective accuracy and critical branches
for a 150-scenario pilot. A separate exact-rational model matched 1,274
single-strike probability calculations. Repeated damage values retain their
probability mass. The model can include misses and one-use healing, but excludes
enemy decisions, switching, status turns and other unmodeled effects. A two-hit
KO chance is not a battle win rate.

For example, Chimecho at 29 improves its conditional two-attempt KO chance against
Morty's Gengar from about 78% to 100% with Psybeam. Gengar is faster and its
Shadow Ball normally knocks Chimecho out first. This is useful coverage for a
team, not a new solo answer to that boss.

In the original three-addition pilot, no baseline-level automatic trainer moves
changed across the 738 trainer records. This is not a result for the later wider batch.
Plus-adjusted levels and complete party behavior remain separate checks. The
changed member lengths are 38, 42 and 30 bytes. Chimecho reaches the native
reminder's 42-byte allocation exactly; archive alignment must remain outside the
member. Native default generation, level-up prompts and reminder probes cover
these sizes, including a negative control that detects incorrect padding.

Sunflora was deferred in this pilot; Delibird subsequently received stat,
Ice Shard and Roost changes in the wider implemented batch. Actual Magical Leaf is Ice in this base;
Sunflora also already has improved stats and alternative Grass access. Delibird
can use Ice Beam from the same area where it is caught. Icy Wind would provide
speed control rather than fill a missing high-damage Ice option. Butterfree
remains an unchanged peer control with strong existing abilities and coverage.

## Guide and preparation economy

The Guide keeps native HGSS fonts, palette, windows, touch controls and detail
navigation. Long lists now support five-entry jumps using L/R, Left/Right or
header arrows. B takes priority when inputs coincide. Paragraphs that fit one
screen stay together. Entry IDs, references, the 429-entry order and save layout
remain stable. Native EN/IT traversal, screenshots, lifecycle and raw-save checks
are required on each composed candidate.

Defer a new Game Corner Cap exchange for 1.3. Existing rewards by the first League
clear total 20 Silver and three Gold Caps: three Gold cover three whole Pokémon,
and 18 Silver cover the six IVs of three more. Repeat League rewards already
provide four Silver and one Gold. Revisit an additional purchase route only if
ordinary progression tests demonstrate a specific shortage.

## Remaining balance and integration work

1. Run level-appropriate whole-party scenarios around Bugsy, Whitney, Morty and
   Chuck for the first additions. Include status, berries, AI, switching, healing,
   obtainable moves and preparation cost; retain successful and failed RNG runs.
2. Compare multiple feasible team compositions through later Johto, Kanto,
   League, rematches, Red and additional postgame. Count outcomes per tested team
   and boss, with sample counts and uncertainty; do not extrapolate from isolated
   damage calculations or a single favorable seed.
3. Review the wider 55-record boss audit. Candidates include removing moveset
   contradictions on Clair and Rocket executives. No further trainer change is
   accepted solely from a static flag; test native move selection and counterplay.
4. Repeat the relevant Guide and save checks when later native integration
   changes their dependencies, retaining the separate stability fixes.
5. Preserve the now installed shiny generation, persistence, targeting and native
   help contracts. Broaden field-route and party scenarios beyond the finite
   native, UI and raw-save evidence in the current implementation report.
6. Run required source/public-file checks and record exact build identities and
   raw-save coverage. Development acceptance, hardware confirmation and release
   publication are separate steps.

## Earlier Guide and learnset pilot validation on 28 October 2026

The combined Guide, learnset and save-feedback candidates rebuild byte-identically
from the same source snapshot in both languages:

| Language | Candidate SHA-256 |
| --- | --- |
| EN | `9c577ae4f4d51fbbedd19bee7f65610ad4c93c04815923161752c0b8549b1031` |
| IT | `46422b8c3e97eec7c7eb7718ec1c6c6b7ffc49e79b1783435d04b89ae506f609` |

The registered source check passes with 654 tests executed and 204 explicitly
skipped. It executes all 15 probability, 12 learnset, 11 PID-reference and 40
Guide tests. A separate private Guide installer test verifies foreign-region
preservation and graphics rejection in EN/IT.

The initial candidates passed native traversal of all 429 entries per language,
491 EN and 497 IT pages, 118/123 reference roundtrips and 64 open/close cycles per
language. Original-size header, detail and paragraph screenshots were inspected.
The combined candidates above have byte-identical Guide code, configuration,
content and runtime dependencies. They additionally passed fresh physical/touch
navigation and nine copied raw-save roundtrips through ordinary Continue, Guide,
native SAVE and cold Continue: four EN and five IT cases, covering no Plus data,
configured settings, expanded Bag, active PLAY courses and an advanced IT save.
Original fixtures remained unchanged. Active courses correctly retained elapsed
playtime credited during SAVE.

These checks cover the pinned desktop interpreter and the recorded fixtures.
They do not complete whole-party balance, new shiny generation, arbitrary-save
compatibility, interrupted-save recovery or hardware acceptance.
