# Guide content provenance

The guide prose is newly written for this project. Names, evolution tables and
font widths are read from the private input ROM during the build; no extracted
message banks, graphics or PDF text are distributed here.

The initial fact check used the published 1.2.5 inputs:

- EN SHA-256 `a821961fc1a90e4adaa118c4a09fce5445d25d567130d0c9edb20dfb0520050e`
- IT SHA-256 `bdf50a4f327f8ea0d8a2ef312e1491d78460d34e978d9b15d160eaf140b313d4`

`content.py` reads evolution NARC `a/0/3/4`, seven records per species, and
message banks 222 (items), 237 (species), 279 (map sections), 750 (moves).
It rejects unknown evolution methods and measures every line using native font0.
These are the actual modified evolution rules, rather than a separate manually
maintained list of exceptions. Item links are emitted only when a verified
acquisition entry exists. Feebas's current beauty threshold is zero, so its
level-up requirement has no additional beauty restriction.

Manual information was checked against field scripts `a/0/1/2`, zone events
`a/0/3/2`, and actual native shop stocks. Event bindings matter: some old local
item routines are unbound, and some duplicate item balls have inaccessible
placeholder coordinates. Neither is evidence of an obtainable item.

| Guide topic | Live evidence in 1.2.5 |
| --- | --- |
| Magma Stone / Azure Flute | Script815 entry8, Cinnabar event54 object2; script772 entry1, Lavender event391 object0. Heatran capture is not required by the trade. |
| Celebi | Script92 shrine entry13; item455 check; battle at0x1158; spent flag0x3FC7. |
| Jirachi | Earth Badge script743 clears Misa's hide flag; Ecruteak script920 entry18 reveals Mt. Mortar script98 entry3. One wish. |
| Deoxys | Script175 entry8, live coordinate event8; Earth Badge, southward approach, time-of-day4. Caught result sets variable0x6132. |
| Red Chain | Power Plant script196 entry7, item441 award at0x2B7. |
| Cynthia / Regis | Script890 entry3; prior starter reward, Lock Capsule use, three encounter flags. Regis scripts98/101/108 and their live objects. |
| Lock Capsule | Oak's first Kanto-departure event: script152 entry3, award at0x85. |
| Lake / creation trios | Script131, live Mystri objects and center trigger; Earth Badge and encounter flags. Capture-specific Orb rewards. |
| Arceus | Script131 center branch: Bag items298–313, National Dex completion, six special encounter flags; battle at0xA80. An exact492-species gate has not been established. |
| Mew | Script115 entries3–6, four live Viridian Forest objects; fourth battle and capture flag0x3FC8. |
| Cresselia / Darkrai | Bedroom script846 bed trigger, Earth Badge and Wing check; Cresselia script9 entry4 awards Wing on capture. |
| Shaymin | Flower Shop script896 entry2 reveals National Park script25 entry28. Flute check and capture/hide flag0x3FBE. |
| Ice Beam / Thunderbolt / Flamethrower | Global item-ball member141 entries228/248/230 bound to Ice Path, Olivine and Bellchime Trail. Goldenrod Game Corner script910 charges4000 coins. |
| Shadow Ball | Lavender mart script768 second clerk, native stock14 includes item357. |
| Standard stones | Actual native stocks4 and12; Olivine script918 shares one daily Sun/Moon reward. |
| Custom evolution items | Sprout script18 choices; global item-ball member141 entries18/44/45/108/109/175 with live event bindings. Covenant Orb example: Violet script864 trade0, Rhyhorn for Gligar, award at0xEA. |

Plate acquisition entries correspond to these live script paths, in item-ID
order298–313: 22,156,195,249,130,98,843, global141 entry189,107,833,26,750,774,
112,62,248. Each was checked against its object/background/coordinate binding.
Toxic Plate checks badge index2 (Plain), correcting the older manual's Hive
Badge claim. Plates must be in the Bag for the Arceus condition.

The source interpretation of native time-of-day4 is00:00–03:59, not inclusive
04:00. Clefairy scheduling, travel routes and every battle-loss branch have not
all been exercised in an emulator. Static event verification and guide UI tests
are different coverage; avoid describing these sources as a full walkthrough
playtest. The original manuals remain useful secondary references.

## Expanded coverage

The current content also includes all 92 TMs, all eight HMs, important evolution
items, ordinary special encounters and the starter-gift groups. Every TM/HM move
mapping was checked against the actual 100-entry native table at `0x021000CC` in
both inputs. Native map names come from bank279, not translated map symbols.
Department-store floor numbering was checked against the Italian elevator and
sign text: English 1F is Italian piano terra; 5F is 4º piano; 6F is 5º piano.

The acquisition audit checked live script bindings, accessible item balls, hidden
item records and 30 native shop inventories. It covers 122 completely decoded
script members that roundtrip byte-for-byte and match EN/IT. Relevant paths in
members232,243,938 and962 were inspected separately because unrelated portions
produce errors in the legacy decoder. This is bounded static evidence, not an
end-to-end emulator playthrough of all acquisitions.

Additional evolution-item sources include scripts916 (Metal Coat),935 (King's
Rock),944 (Dragon Scale),38/117 (Up-Grade),893 (the two DeepSea gifts),883 (Razor
Claw/Fang), and live global141 item balls for the other listed items. The hidden
DeepSea sources use native hidden-item indices38 and229. Alternate pickups share
those flags; the guide does not promise independently renewable copies.

The Goldenrod lottery is a chance-based source, costing300 per draw. Its seven
first prizes were traced from weekday branches in script904. The guide explicitly
distinguishes prizes, coin exchanges, shop purchases and one-time gifts. A prize
list is not described as free or guaranteed. Actual shop21 is shared by Goldenrod
and Celadon: its Dig/Roost/Grass Knot inventory supersedes the old manual claim
that Dig was removed from Celadon. TM62's actual item ball is on Route38.

HM gifts use scripts92 (Cut),875 (Fly),928 (Surf),252 (Strength),90 (Whirlpool),
243 (Rock Smash), global141 entry149 (Waterfall), and121 (Rock Climb following the
post-Earth-Badge Oak call in741). Unown Report469 is awarded through the first
puzzle-descent event, header303 condition40CE=1 and script42 entry1.

Event and localization checks include the ordinary Johto/Kanto legends and
special gifts, actual Italian Tohjo radio choices, Marisio/Catlina, and “Tre Are”
for Mystri Stage. Retry wording is limited to the branches actually checked;
Moltres's guide promises a retry after fleeing/defeating it, not every party-wipe
outcome. The Leaf Stone entry does not claim the Sprout elder's Leafeon reward:
that reward is Woodland Ore.

## Interface inspiration

[Crystal Clear's own documentation](https://github.com/ShockSlayer/ccdocs/blob/master/docs/Documentation.md)
and [2.4.0 interface notes](https://github.com/ShockSlayer/ccdocs/blob/master/docs/changelogs/2_4_0_Changelog.md)
informed contextual explanations and compact navigation. The new guide keeps
selection when returning, links items from event/evolution pages and shows a
small number of readable lines at once. Its assets and rendering follow HGSS;
Crystal Clear's art, code and game-specific instructions are not copied.

## New training services

The fourth category and the two Cap entries describe this project's own training
rules, native adapter and localized scripts, not the older bundled manuals.
They distinguish actual IV changes from EV allocation, quick paid training from
free timed courses, real time from active playtime, and pending rewards from
items already collected. The phone's remaining time is explicitly described as
the entire course, including its level goal. Normal trainer and wild victories
do not grant Caps in this implementation.

With these additions there are 429 entries. Both language payloads are generated
and measured against the native font; their current sizes are 113,212 bytes (EN)
and 118,752 bytes (IT), below the 131,072-byte content limit. The native controller
already accepts a category count; the content compiler and independent validator
now permit four categories. A roundtrip/bounds test and fourth-category cursor
test cover the extension. Runtime navigation, item links and heap cleanup are
checked separately on the built images.
