# Strategic trainer changes in the 1.3 development build

The existing Plus difficulty setting now enables nine move substitutions across
seven important trainers. Normal difficulty retains the original parties. This
is a small first balance pass, not a replacement of every trainer team.

The [Redux overview](https://smilingzero.github.io/BlazeBlack2ReduxWiki/#regarding-difficulty)
and [trainer documentation](https://smilingzero.github.io/BlazeBlack2ReduxWiki/genTrainerChange/)
informed the approach: give team members useful roles and preserve ways for the
player to prepare. Redux's species-rule modes and trainer difficulty modes are
separate choices. Its Gen V scripts and battle formats are not imported.

Sacred Gold Plus already changes many species, moves and types, and already has
six-member teams for the first eight Gyms and League. The investigation used the
actual 1.2.5 parties and move data, including repurposed Fairy move IDs, rather
than assuming the older bundled trainer manual was still accurate.

| Trainer | Pokémon | Move change | Purpose |
| --- | --- | --- | --- |
| Bugsy | Scyther | False Swipe → Bug Bite | Give its Bug type a usable attack that can finish a battle. |
| Morty | Gengar | Shadow Punch → Shadow Ball | Use its much stronger Special Attack. |
| Chuck | Primeape | Rage → Brick Break | Add Fighting damage; retain the existing elemental punches. |
| Jasmine | Magneton | Spark → Discharge | Match the attack category to its special strength. |
| Jasmine | Steelix | Slam → Earthquake | Give it a reliable Ground attack. |
| Jasmine | Steelix | Rock Polish → Gyro Ball | Use its low Speed instead of a weak speed-boosting plan. |
| Pryce | Dewgong | Sheer Cold → Rest | Make its Chesto Berry useful and remove an OHKO lottery. |
| Will | Xatu | Power Swap → Psychic | Give the Psychic specialist a Psychic attack. |
| Lance | Gyarados | Hyper Beam → Waterfall | Give Dragon Dance a physical Water attack to support. |

Existing preparation remains relevant: early Rock/Electric options for Bugsy,
Dark/Ghost options for Morty, Psychic/Flying options for Chuck, and Fire/Ground
options for Jasmine. These are options, not guaranteed counters: existing coverage
moves remain. Gyarados retains its fourfold Electric weakness. No additional
universal level, IV, EV, species, ability or held-item changes are part of this pass.

## Implementation and evidence

The new hook wraps the existing trainer-level hook at `0x023D8194`. It checks the
active Plus setting, trainer ID, party format and complete record fingerprint,
then edits a temporary loaded party record. The ROM's trainer archives remain
unchanged. The original level calculation, RNG calls and Pokémon construction
continue through their original path. Unknown records are left untouched.

Three core tests and 672 native ARM comparisons cover both languages, both modes,
four call sites, seven parties and all six slots. They compare the changed move
buffer, preserved registers, stack and condition flags against the previous hook.
Independent specification and code review passed. These checks do not measure a
full battle's difficulty or prove every AI decision; whole-adventure balance
remains a playtesting question.

A separate native battle campaign constructed Bugsy's complete six-Pokémon party
in four cases: 1.2.5 Plus EN, candidate Plus EN/IT and candidate Normal EN. Scyther
had Bug Bite only in candidate Plus. The other 23 moves, species and Plus levels
matched the baseline; Normal retained False Swipe and its original level path.
All constructed records had valid checksums. Player party, Pokédex, PC Pokémon
and input SRAM remained unchanged. Plus was selected through ordinary Options.
The test selected trainer21 at the native party factory before archive loading,
using an already reachable trainer encounter. This proves native construction
and entry into battle, not natural Gym progression or a completed balance test.
