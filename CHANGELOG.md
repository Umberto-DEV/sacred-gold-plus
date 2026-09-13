# What changed

## 1.2 — 13 September 2026

Download: the [1.2 release](https://github.com/Umberto-DEV/sacred-gold-plus/releases/tag/v1.2), one ZIP per language. Saves from 1.1 open in 1.2 and 1.2 saves open in 1.1, checked byte for byte. Cheat files do not carry over from 1.1, because 1.2 has a different game header: re-import the ones in the 1.2 package, where every code starts switched off.

- **Plus difficulty extended to levels.** Tougher trainers and, separately, scaling wild Pokémon. Both are optional, both are capped at level 100.
- **A Sacred Gold Plus options page**, opened with SELECT during play. On Continue the game asks once whether you want to look at it.
- **The classic HeartGold camera, restored natively** in eight indoor maps (Mahogany Town, Mt. Mortar). No cheat needed.
- **Smoother towns**: fewer characters are loaded at once when entering or leaving one.
- **Optional animated Pokémon in battle**, off by default.
- **Online server choice**: pick which Wi-Fi connection slot handles GTS and battles. Mystery Gift connects automatically. A service falls back to the first configured slot when its designated slot is not set up, and to the original behaviour when none is.
- **Over 200 text corrections** in English and Italian.
- **A cleaner title screen**, with a single, more legible credit line.
- **The EV/IV guide** on a Pokémon's Ability page no longer shows an automatic "START Guide" label; press START there to open it.
- Bug fixes.

This release also opens the development side of the project: the sources, tools and tests that build and check the game are in [`source/`](source/), the technical documentation is in [`source/docs/`](source/docs/), and [`source/README.md`](source/README.md) describes how to work on it. No game file is distributed: the tools read the player's own.

## 1.1 — 11 September 2026

Published as a development branch rather than as a player release. It carried the native indoor camera work, the bag input fix, the repel re-arm fix and the first version of the reserve used by 1.2. Its patches were superseded by 1.2.

## 1.04 — 9 September 2026

The download had a simpler layout and names: **Sacred-Gold-Plus-[Normal-Angle or New-Angle]-[IT or US].zip**. The four game outputs were unchanged from the earlier 1.04 packages; existing players with a matching game fingerprint did not need to patch again.

- Each ZIP included **Install-or-update.html**, recognizing the supported unmodified **US HeartGold** and **English Plus 1.01, 1.02 and 1.03** inputs and automatically selecting the matching update for that ZIP's language and camera. It processed files offline in the browser, with no ROM upload and no program installation, recognized an already-current target and refused unknown inputs.
- Seven optional cheat codes in **Cheats**, in desktop MCH and Android XML formats, all starting disabled.
- File checks, changes and credits collected in **Manual/Project Notes.txt**; the full licence remained included separately.
- Restored two damaged hardware-wait instructions in the 1.03 game, repaired malformed text-formatting instructions, corrected selected trade dialogue and English move names, repaired the Pokédex search resources used by the height and weight controls.
- Added Italian dialogue, menus and selected interface graphics, with an accented-character naming keyboard.
- Added the optional Normal Angle camera; New Angle retained the camera used by Sacred Gold Plus 1.03.

Fairy typing, the additional Fairy moves and the 1.03 battle changes come from the earlier project. They are not features created for 1.04.

## Known limits

- Full-story and post-game testing is still needed. Some corrected dialogue and translated screens need further in-game review.
- The original game's reported event issues are not all fixed. Please report a reproducible case rather than assuming a historical bug list is resolved.
- Newly added Fairy moves can still use their older battle animations, as reported by the original Plus author.
- The optional battle animation moves the sprite; it does not add per-species animation. Double battles, switching and capture are not covered by the checks behind it.
- The Wi-Fi slot fallback is fully demonstrated for three of its five cases on the test bench; the two that need a live online trigger were checked under emulation only. Official online services for this game are long discontinued.
- Cheats: the codes shipped in the package have bounded checks on the real game core. This is not full-game cheat coverage or a promise about every emulator.
