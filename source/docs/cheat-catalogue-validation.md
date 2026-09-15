# Cheat catalogue validation — 1.2.1, 15 September 2026

The updated catalogue contains **2,110 codes in 67 folders per language**.
Every code was checked for syntax and ROM guards, then executed separately in
both a field scene and a battle scene on the final EN and IT ROMs. All **11,744
short execution cases** completed without a stopped console. No static syntax
failure or unmatched ROM equality guard remains.

This is a bounded check of every entry, **not a claim that every effect works in
every story event**. A code with unchanged RAM may be waiting for its required
scene, already match the initial value, or be an informational entry. A changed
RAM value alone does not prove the advertised effect. Online services, original
DS backlight hardware, Pokéwalker and event/minigame scenarios were not exercised
end to end. The table below includes every folder without treating those missing
scenarios as passes.

## Corrections and targeted functional evidence

- **Folder 40:** replaced three Master Ball species selectors with one searchable
  picker for 493 species and levels 1–100. Kept the maximum-IV code. The companion
  melonDS Android 2.1.1 wrapper provides the L+R toggle, transient table writes,
  restoration after battle/map changes and an initially-off state. See the
  [selector report](cheat-selector-validation.md).
- **Folders 44–46:** replaced 75 nature/gender codes. The old male code left the
  encountered Pokémon unchanged and wrote an unrelated field word. The new codes
  modify native creation before encryption/checksum. Tested 1,200 ARM cases per
  final ROM (25 natures × 3 modes × 8 gender ratios × 2 native paths), plus real
  encounters/captures and save/restart. Live capture coverage is Kakuna with
  Adamant nature; other nature and Cute Charm paths have ARM coverage. See the
  [gender report](cheat-gender-validation.md).
- **Folder 01:** removed the clean-ROM DeSmuME/No$GBA overlay workaround. Its
  `0x020DDDC8` guard expected `0x1AFFFFF5`, while SGP contains `0x1AFFFFFC`;
  other blocks could still apply, making the partial patch inappropriate.
- **Bag compatibility:** the expanded Bag preserves native save layout and
  synchronizes direct writes. Added/removed the final main-pocket item through
  native UI and preserved it across normal save and cold boot. This does not
  assert the advertised effect of every gift/event code. See the
  [Bag implementation and checks](../features/capacita-borsa/README.md).

The previous 2,113-code catalogue also completed 11,780 preliminary short runs.
The final run below uses the corrected catalogue and cold-boot fixtures from the
final 17-stage ROMs, not savestates from the previous build.

## Method

The offline harness uses the real melonDS Action Replay interpreter, CPU
interpreter, software renderer, generated firmware and FreeBIOS. For each code:

1. Restore a cold-created field or battle fixture with no cheats.
2. Run two frames with no buttons, and separately each distinct key mask found
   in its `94000130` conditions; record the matched control RAM.
3. Restore the same fixture, enable only this code and run two frames with the
   same input. Compare all 4 MiB of main RAM and check console running state.
4. Start the next case from the original fixture, avoiding accumulated writes.

The field fixture is National Park; battle is an ordinary wild Pinsir encounter.
The batch evaluates the raw Action Replay code. The Android managed selector has
separate real-core ON/OFF, held-button, map, capture and savestate tests.
An 80-second group timeout is a failure, not a skipped result; none occurred.

Static checks decode E payloads before interpreting opcodes, check paired hex
words and compare guards against ARM9 and all loaded-overlay images. Restoration
guards matching writes elsewhere in the same code are distinguished from wrong
ROM preimages. Pointer-relative effects require the runtime context.

Run the public static audit on locally supplied files:

```sh
python source/cheats/audit.py catalogue.xml --rom game.nds --output audit.json
python source/cheats/catalogue.py previous.xml --language EN --output updated.xml
```

The [machine-readable summary](cheat-catalogue-validation.json) records final ROM
hashes and per-folder results. ROMs, saves, raw RAM and screenshots are local
fixtures and are not distributed with the source.

## All folders

Counts below are **per language**, combining field and battle cases. EN and IT
counts match. Every listed case completed; effect-specific scenario coverage is
limited as described above.

| Folder | Codes | Executions | RAM changed | RAM unchanged |
|---|---:|---:|---:|---:|
| 00 - Sacred Gold Plus 1.2.1 (verificati) | 7 | 16 | 13 | 3 |
| 01 - System · compatibility and boot | 1 | 2 | 2 | 0 |
| 02 - System · WFC online services | 1 | 2 | 2 | 0 |
| 03 - System · animations and speed | 2 | 4 | 4 | 0 |
| 04 - System · play time | 2 | 4 | 4 | 0 |
| 05 - System · randomness (RNG) | 3 | 12 | 10 | 2 |
| 06 - System · weather and time of day | 9 | 18 | 10 | 8 |
| 07 - System · Nintendo DS backlight | 2 | 8 | 4 | 4 |
| 08 - System · view and camera | 6 | 16 | 10 | 6 |
| 09 - System · original SG+ codes (historic, mixed) | 22 | 50 | 37 | 13 |
| 10 - Player · money and coins | 2 | 8 | 4 | 4 |
| 11 - Player · exploration and progress | 17 | 66 | 31 | 35 |
| 12 - Player · movement speed | 1 | 2 | 2 | 0 |
| 13 - Player · Trainer information | 1 | 4 | 2 | 2 |
| 14 - Player · Trainer gender | 2 | 8 | 2 | 6 |
| 15 - Player · name used in dialogue | 12 | 24 | 24 | 0 |
| 16 - Player · Pokégear | 6 | 24 | 10 | 14 |
| 17 - Player · Pokégear colours | 5 | 10 | 10 | 0 |
| 18 - Player · Pokéwalker | 3 | 12 | 6 | 6 |
| 19 - Player · other conveniences | 6 | 26 | 13 | 13 |
| 20 - Party · Pokédex | 5 | 20 | 6 | 14 |
| 21 - Party · moves and traits | 6 | 18 | 14 | 4 |
| 22 - Party · eggs and cloning | 11 | 38 | 20 | 18 |
| 23 - Party · shiny hatching (Charm) | 20 | 120 | 120 | 0 |
| 24 - Party · EV multipliers | 4 | 8 | 4 | 4 |
| 25 - Party · experience multipliers | 11 | 22 | 11 | 11 |
| 26 - Party · Hidden Power (type via IV) | 14 | 28 | 28 | 0 |
| 27 - Party · changes via ribbon mark | 17 | 34 | 34 | 0 |
| 28 - Party · Mystery Gift (Pokémon) | 23 | 92 | 46 | 46 |
| 30 - Battle · battles and Trainers | 28 | 88 | 36 | 52 |
| 31 - Battle · Battle Frontier | 10 | 36 | 17 | 19 |
| 32 - Battle · Pokéathlon | 7 | 28 | 14 | 14 |
| 33 - Battle · Voltorb Flip | 2 | 4 | 0 | 4 |
| 34 - Battle · Catch the Disc | 2 | 8 | 4 | 4 |
| 35 - Battle · battle music (Johto) | 16 | 64 | 30 | 34 |
| 36 - Battle · battle music (Kanto) | 16 | 64 | 30 | 34 |
| 40 - Wild encounters · choose Pokémon and level | 2 | 4 | 3 | 1 |
| 41 - Wild · level (classic method) | 13 | 30 | 16 | 14 |
| 42 - Wild · encounter rate | 5 | 16 | 8 | 8 |
| 43 - Wild · encounter rate (variants) | 4 | 10 | 3 | 7 |
| 44 - Wild · nature | 25 | 50 | 50 | 0 |
| 45 - Wild · male + nature | 25 | 100 | 50 | 50 |
| 46 - Wild · female + nature | 25 | 100 | 50 | 50 |
| 47 - Wild · repeat special encounters | 14 | 56 | 28 | 28 |
| 48 - Wild · Safari Zone | 3 | 12 | 6 | 6 |
| 49 - Wild · level 1-100 (direct choice) | 100 | 200 | 100 | 100 |
| 50 - Wild · species #001-050 | 51 | 202 | 100 | 102 |
| 51 - Wild · species #051-100 | 51 | 202 | 100 | 102 |
| 52 - Wild · species #101-150 | 51 | 202 | 100 | 102 |
| 53 - Wild · species #151-200 | 51 | 202 | 100 | 102 |
| 54 - Wild · species #201-250 | 51 | 202 | 100 | 102 |
| 55 - Wild · species #251-300 | 51 | 202 | 100 | 102 |
| 56 - Wild · species #301-350 | 51 | 202 | 100 | 102 |
| 57 - Wild · species #351-400 | 51 | 202 | 100 | 102 |
| 58 - Wild · species #401-450 | 51 | 202 | 100 | 102 |
| 59 - Wild · species #451-493 | 44 | 174 | 86 | 88 |
| 60 - List · player appearance (characters) | 214 | 428 | 426 | 2 |
| 61 - List · player appearance (objects) | 62 | 124 | 124 | 0 |
| 62 - List · player appearance (other sprites) | 56 | 112 | 112 | 0 |
| 63 - List · Pokémon appearance (generation 1) | 153 | 306 | 306 | 0 |
| 64 - List · Pokémon appearance (generation 2) | 132 | 264 | 264 | 0 |
| 65 - List · Pokémon appearance (generation 3) | 138 | 276 | 276 | 0 |
| 66 - List · Pokémon appearance (generation 4) | 143 | 286 | 286 | 0 |
| 67 - List · abilities via ribbon mark | 124 | 248 | 248 | 0 |
| 68 - List · Wi-Fi arena background | 44 | 176 | 88 | 88 |
| 80 - Bag · items, medicine, Balls, TM/HM | 20 | 82 | 34 | 48 |
| 81 - Bag · Mystery Gift (items, routes) | 3 | 12 | 6 | 6 |
