# Wild species and level selector: Action Replay validation

15 September 2026. Scope: Sacred Gold Plus 1.2.1, English and Italian.

## melonDS Android 2.1.1: managed L+R toggle

The Android frontend now recognizes the exact 14-line selector below on the two
supported ROM headers and manages it outside the normal AR list. Leave the
selector enabled in melonDS. It starts **OFF** in the game. Press L+R to turn it
ON; release the buttons and press L+R again to turn it OFF. Holding both buttons
does not repeat the toggle. An emulator event reports each ON/OFF change.

The frontend temporarily replaces the 92 table bytes immediately before a
frame and restores them immediately afterward, before save-state or rewind
capture. The running battle keeps the opponent already generated; the next
ordinary grass encounter uses the current ON/OFF state. A new selection, reset,
state load or rewind re-arms the selector OFF. Reopening the menu without
changing the selection preserves its current state.

Restoration follows the live field application's `OverlayManager`, its
`FieldSystem` data, `mapEvents` and map identity. It does not depend on the field
overlay still being loaded after the frame: the battle can have replaced that
overlay while the encounter table remains alive. A destroyed field application's
data pointer is cleared by the game. A changed map's newly loaded table is not
replaced with the preceding map's snapshot. Individual levels and species
halfwords changed by the guest during the frame are preserved.

### Additional runtime verification

A private headless frontend linked the same production helper against the real
melonDS interpreter. Both EN and IT passed this continuous sequence:

1. Selector enabled in the emulator, game starts OFF.
2. L+R held for 60 frames turns it ON once.
3. The resulting ordinary encounter is species 25, level 10.
4. A second L+R press during battle turns it OFF.
5. After fleeing, an encounter in the same map is the normal species 402, level 18.

All five RAM checkpoints in each language (OFF, held ON, battle, return to field,
next normal battle) retained the original 92-byte table. Saving while ON,
loading that state OFF, enabling again, and removing the configured cheat also
retained the original table.

Two IT map-transition comparisons used identical inputs and compared the entire
4 MiB of main RAM between managed ON and no-selector controls. Both matched
byte for byte: National Park (96) to gate (102), using the game's own warp
function, and walking back from gate (102) to National Park (96). The latter
also restored the initial National Park table exactly.

Host tests under AddressSanitizer and UndefinedBehaviorSanitizer cover exact
code recognition, invalid constants, supported headers, held-button edges,
reset while held, frame restoration, battle overlay replacement, partial guest
table updates, changed map identity, freed field data, task transitions and
selection removal/change. The helper is included in the normal host-test script.

The wrapper was tested on candidate ROM SHA-256 values:

- IT: `8f991bdd7f8abb80aaf25855a1708203e2194c222fbcdf4f1f33d2bab93b2610`
- EN: `30bbf4cf0105688218132c5aa4e8b9b3ec8de124961103f36cfbcb4c8e48a708`

These are candidate identifiers, not an assertion about later rebuilt ROMs or
an Android device run. The tests above used the CPU interpreter. Native Android
compilation and broader device/JIT validation belong to the frontend build.

**Compatibility:** the restart advice later in this report describes the raw
AR version. New managed-toggle OFF needs no restart. Previously created states
with a raw modifier already applied can still contain its altered table or code;
restart after switching from those old modifiers. The ordinary-grass, native
level-scaling, swarm and Unown restrictions below still apply.

## Validated contract

The selector can use one combined Action Replay code for National Pokédex IDs
1–493 and levels 1–100. The code changes the current map's land encounter table
without a button condition, inventory writes, or a patch to executable game code.
It changes species and level for ordinary grass encounters. The game's native
wild level scaling must be off for the selected level to remain exact.

Use the field-overlay signature guard in **both** blocks. The terminator of the
species block resets the condition stack, so a guard on the first block alone
does not protect the level block.

Example: species 25, level 10:

```text
52246C94 28038800
6211186C 00000000
B211186C 00000000
D5000000 00000019
C0000000 00000027
D7000000 00032A48
D2000000 00000000
52246C94 28038800
6211186C 00000000
B211186C 00000000
D5000000 0000000A
C0000000 0000000B
D8000000 00032A3C
D2000000 00000000
```

Only the two `D5000000` constants vary. Replace the previous selection rather
than enabling multiple species/level writers together. Do not combine this
selector with the old Master Ball modifier, other species or level modifiers,
or native wild level scaling.

## Memory contract and guards

Let `P = u32[0x0211186C]`. The two loops write:

- Twelve level bytes at `P + 0x32A3C` through `P + 0x32A47`.
- Forty species halfwords at `P + 0x32A48` through `P + 0x32A96`.

These are 92 consecutive bytes. The species region contains the 36 morning,
day and night land slots and four radio replacement species. It ends before
the surfing table. It does not include swarm replacement species.

In both language runtimes the table base `P + 0x32A34` was independently
compared with `fieldSystem->mapEvents->wildEncounters`, using the game's live
structure pointers and the `MapEvents` layout. The addresses matched.

The first guard requires `u32[0x02246C94] == 0x28038800`, an instruction signature
of the field overlay. The second rejects a null `P`. In the tested field the
signature matched; during battle the same location held `0xFF4EF7F3`. Enabling a
different guarded selection during that battle and running one frame produced
RAM identical to a control with no cheat, across the full 4 MiB of main RAM.

This is a version-specific code, not a general memory-safety guarantee for
other ROMs. The address relationship and signature must be revalidated when
changing the game build or its memory layout.

## Headless runtime evidence

The tests used the real melonDS Action Replay interpreter via `hg_runtime-gdb`
with CPU interpreter, software renderer, generated firmware and FreeBIOS.
Both language field fixtures were created by cold-booting the tested ROM with
a local save and entering the National Park. No device was touched.

| Language | Selection | Observed encounter |
|---|---|---|
| IT | 25 / level 10 | Species 25, level 10 |
| IT | 25 / 10, changed to 493 / 100 | Species 493, level 100 |
| IT | 25 / 10, changed to 201 / 1 | Species 201, level 1 |
| EN | 25 / level 10 | Species 25, level 10 |
| EN | 493 / level 100, enabled before cold boot | Species 493, level 100 |
| EN | 25 / 10, changed to 201 / 1 | Species 201, level 1 |

Battle screenshots were visually inspected for species and level. Movement
used only the directional pad; no L, R or other activation combination was
sent. Species 201 was tested with a save that satisfies its game prerequisites.

For each of the two IT selection changes, matched runs from the same state
were compared after one, two and three frames. All six 4 MiB RAM comparisons
had **zero differences outside the 92-byte target region**. The counts of
changed bytes inside that region were 69 for species 25 / level 10 and species
201 / level 1, and 75 for species 493 / level 100; some bytes already matched
and therefore were not differences. This confirms that the cheat introduced
no inventory or executable-code changes in these comparisons.

Turning the cheat off after the second frame left all selected values intact
on the third frame. A fresh process boot without the cheat loaded the normal,
mixed species table from the original save.

## User-visible limits

- **Turning it off stops future writes; it does not undo the current table.**
  Restart the game with the selector off to restore normal encounters. Normal
  map initialization reloads encounter data; merely crossing a visual border
  is not a guaranteed reload. A saved emulator state can retain the modified
  table even after the selector is disabled.
- **Ordinary grass encounters only.** Surf, fishing, Rock Smash, Headbutt,
  Safari, Bug-Catching Contest, roaming and scripted encounters are outside
  this contract. Swarm replacements can also override the selected species.
- **Species 201 requires an unlocked Ruins of Alph puzzle.** The game explicitly
  refuses an ordinary land encounter for it if no puzzle flag is set. The
  selector does not change progression flags. Its form follows the game's
  normal unlocked-form rules.
- Other species' forms follow their normal generation rules; this is not a
  form selector. Repels and encounter-suppressing effects still apply.
- Changing a selection during battle affects a future encounter after returning
  to the field. It does not replace the current opponent.

The source-level basis is the local `pokeheartgold` definitions in
`include/wild_encounter.h`, `include/map_events_internal.h`, and the functions
`EncSlotArray_Init_Land`, `EncounterGen_CanGenerateUnownEncounter`,
`EncounterGen_ChooseUnownForm`, and `Field_InitMapEvents`. Runtime results above
are the independent confirmation on the modified game. No full campaign,
all-species sweep, Android UI import, JIT run, or every menu/overlay transition
is claimed by this audit.

## Reproduction identifiers

| Artifact | SHA-256 |
|---|---|
| Tested 1.2.1 IT ROM | `495ab9226277fc0f4b926e265a5b95093525318d5afebc048926347ceb7b3b14` |
| Tested 1.2.1 EN ROM | `c7f9562c6e369bb1aff446270969e85f198a396c6cabbbed77b3c9730d9ab2fa` |
| Headless runtime | `0afd2926507f718e739160e7e0f915153ca9ee3653e42875c17a205d6497f942` |

Private screenshots, RAM dumps, states and command logs remain local. They
are not release artifacts. This report contains no extracted game assets.
