# What changed

## 1.3.0 — in development, not released

Status recorded on **29 October 2026**. The candidate still identifies itself as
**1.3 DEV**; published 1.2.5 downloads remain unchanged.
The [complete 1.2.5 → 1.3.0 change register, in Italian](source/docs/novita-1.3.0.md)
records the before/after behavior, all 67 affected species, fixes, inherited
features and verification limits.

- Add a native field Guide with 429 entries and HGSS navigation, plus contextual Plus controls and a second Shiny page.
- Add IV consultants, Silver/Gold Caps, milestone rewards, EV policies, quick training and optional timed Day Care courses.
- Add native shiny Classic/Pro generation and targeted Search, with persistent target and chain state.
- Audit all 493 species: change base stats for 50, add two second ability slots and 32 level/move entries across 29 species; 67 species are affected overall.
- Add nine Plus-only move substitutions across seven trainers and extend the caught indicator to trainer Pokémon whose species is registered as caught.
- Correct Mew movement lifetime, SAVE-refusal feedback, high-event-flag aliasing with the Pal Pad and the clipped English migration note; harden the new Training services against payment before storage refusal.
- Preserve older save data through guarded forward migration. The [Android validation report](source/docs/android-1.3-dev-validation.md) distinguishes 49 accepted checkpoints, native-code evidence, skipped tests and remaining limits.

## 1.2.5 — 24 October 2026

- Show “Sacred Gold Plus 1.2.5” in the Plus options heading (Options → SELECT), so players can check the version after the one-time setup prompt has gone. Addresses [issue #6](https://github.com/Umberto-DEV/sacred-gold-plus/issues/6).
- Display **V.1.2.5** on the upper title screen, aligned with **Developed by A FAN**, and restore the missing descender in **by**. Only version text and these title graphics change from 1.2.4 in each language. Save code, the native save layout, Plus settings and expanded Bag storage are unchanged; no new game or save conversion is needed. See the [validation and upgrade notes](source/docs/version-1.2.5.md).

## 1.2.4 — 24 October 2026

- Coordinate optional battle idle animation with native OAM sprite copies: reset before copying, suspend while copies live, resume after the final owner is freed.
- Skip the field party search for Waterfall outside Surf moving south. No FPS unlock or gameplay-speed change.
- A player completed the previously blocked Latios encounter with the maintenance candidate and reported no further slowdowns. The old freeze happened after battle started; event scripts and flags are unchanged, and its specific cause remains unproven.
- Integrate maintenance and the 1.2.4 title into the public build and read-back chain. Preserve all existing save formats and public addresses.
- Ship 19 input routes in each language ZIP, including original HeartGold US/IT and all previously recognized Plus versions through 1.2.3. Every route is checked with xdelta3 and the pinned RomPatcher.js.
- Preserve original manuals and trainer reference byte for byte. Include current installation instructions, checksums, a 1.2.4 PDF guide and public reproducible packaging tools.


## 1.2.3 — 20 September 2026

- **The classic HeartGold camera in every real cave.** The native camera — the one the original game uses underground — is restored in **44 more maps**, on top of the eight indoor maps 1.2 already covered (Mahogany Town, Mt. Mortar). In Kanto: Rock Tunnel (1F and B1F), Mt. Moon and its Square entrance, Diglett's Cave, Cerulean Cave (1F, 2F, B1F) and the Seafoam Islands (1F to B4F, including the Cinnabar Gym room). Between the two regions: Tohjo Falls (both rooms), Victory Road (1F, 2F, 3F) and Mt. Silver Cave (all floors and the outdoor ledges). In Johto: Union Cave (1F, B1F, B2F), Slowpoke Well (entrance, B1F, B2F), the Ice Path (1F, B1F, B2F), the Whirl Islands (1F, B1F, B2F), Dark Cave on the Route 45 side, the Dragon's Den and its entrance, and Cliff Cave. With the Plus angled camera these caves hid paths and items behind ledges and walls; the native camera shows them as the original game intended. Outdoors, in towers, forests, the Lighthouse, the Safari Zone and the Ruins of Alph the Plus camera is unchanged, and the Plus wide camera is still what you get everywhere else. The exception table grows from 24 to 68 entries and moves from `0x023D8040` into the ARM9 reserve at `0x023D8A10`, where it has room to grow; the hook's only change is the two pool literals that point at it. No map data and no code instruction changes: the ROM differs from 1.2.2 by 208 bytes for the camera plus the one byte of the version string. Verified on all 540 map headers in both languages, with the read-back, 30 mutants and a three-cave run on the headless bench. **A save made inside one of these caves keeps the previous camera until the next map change** — the map's camera type is frozen in the field data when the save is written. This is the behaviour Mt. Mortar has had since 1.2, not a new defect.
- **The Fly landing was investigated and is not a ROM defect.** The landing in front of a Pokémon Center was captured frame by frame on the headless bench with the software renderer: 1.2.2 draws it exactly as 1.1 does, with NPC smoothing on or off. The flicker reported on Android comes from the emulator's OpenGL renderer; switching melonDS to the software renderer avoids it. Nothing was changed in the ROM for this.
- The in-game version now reads "Sacred Gold Plus 1.2.3" on the screen shown at Continue. The title screen and game header remain unchanged, so 1.2.2 cheat files still apply. Each ZIP carries direct patch routes from both 1.2.2 editions.

## 1.2.2 — updated 19 September 2026 (second edition)

- **The "SELECT → Plus" hint in the Options menu is back on every visit.** The bottom-left line reminding you that SELECT opens the Sacred Gold Plus page showed only on the first visit of a session and after opening and closing the page: leave the Options menu, come back, and it was gone. The game destroys and recreates its Options app at the same heap address and clears the layer, while the page trusted its own "already drawn" flag, which lives in the ARM9 reserve and outlives the app. `opz_suggerimento` now reads the game's own tilemap for that layer (the cell at the hint's position holds the hint's first tile or it does not) and redraws when needed; the flag is kept only as a mirror for the read-back. Present since 1.2. Reproduced and verified on the headless melonDS bench in both languages: first visit, second visit and after closing the page give pixel-identical bottom screens, and the Unicorn suite has two new tests that fail on the previous payload. The published 1.2.2 downloads were replaced in place, as the 1.2.1 update was, and each ZIP now also carries a direct patch route from the first-edition 1.2.2 game, so nobody has to go back to 1.2.1. Saves are unchanged.
- **Build from the original ROM.** `sgp12.costruisci` and `sgp12.verifica` now start from an unmodified Pokémon HeartGold ROM, US or Italian, and nothing else: a new first step ("stage 0") derives our 1.1 base from it by applying a published xdelta patch, then the seventeen blocks run as before. Rebuilding no longer depends on owning an intermediate ROM of ours. The two patches are release assets and contain only differences — they are not ROMs and do nothing without the HeartGold they belong to; no game file is distributed. `source/sgp12/base11.json` pins, for each language, the accepted ROM's SHA-256, the patch's name and SHA-256, and the SHA-256 the resulting base must have; all three are checked before any block runs, and any mismatch is a refusal. `python3 -m sgp12.scarica_base --destinazione "$SGP_ROM_DIR"` fetches the patches once and deletes anything that does not match its pin; it is the only command here that uses the network, and nothing calls it for you. `xdelta3` is now a build requirement, and the refusal names the package to install. A 1.1 base passed to `--base` is still accepted and skips stage 0 with a warning; `--lingua` became optional, since the language follows from the ROM's SHA-256.

## 1.2.2 — initial release, 19 September 2026

The initial 19 September build (morning) lacked the Options-menu hint fix above. The current [1.2.2 downloads](https://github.com/Umberto-DEV/sacred-gold-plus/releases/tag/v1.2.2) include it, and take the first-edition game as one of their patch sources. The game header remains unchanged.

- **The expanded Bag no longer loses its extra slots in silence.** A save whose extension sectors could not be read once, or that a converter normalised to a single repeated byte, is written again instead of dropping the 108 extra slots at every reload. A spent or out-of-range slot is emptied where it sits, so nothing else changes position, and the game keeps the same cleaned inventory in memory. Foreign data in those two sectors is still never overwritten: the [feature notes](source/features/capacita-borsa/README.md) say how to tell and how to clear them by hand.
- Optional battle motion: the B-pose accent now holds the pose for the time the game itself uses for the same frame (0.33–1.00 s depending on tuning, chosen with `--variante`) instead of 2–3 ticks, and starts only at the breathing motion's resting peak. See the [v5d notes](source/features/anim2/README.md#v5d--accento-di-posa-b-18-settembre-2026).
- **A successful pickup no longer reports "Bag is full".** Picking a Poké Ball up off the ground showed the "left behind" message every time the item was in fact collected. The capacity check was not at fault: the capped-gift block kept its "I discarded something" flag on a script variable the engine writes itself with the id of the object you interacted with, which is `1` for a ground ball — the exact value the guard compares. The flag moved to a special variable no script and no engine path writes, and the hook now always sets it. The warning is shown only when the item really is left behind.
- The in-game version now reads "Sacred Gold Plus 1.2.2" on the screen shown at Continue. The title screen and game header remain unchanged, so 1.2.1 cheat files still apply.
- Tools and documents: the ARM9 reserve register is back in step with the blocks, `sgp12.verifica` tells PARTIAL apart from GREEN instead of reporting both as green, and the bench probes and scripts for the battle-animation phases were corrected.

## 1.2.1 — updated 15 September 2026

- Expanded all Bag pockets to whole six-slot pages: 252/42/30/102/66/12/30/60 slots. Existing saves import; extra slots are stored in a checked save extension and are unavailable to older ROMs.
- Added the searchable 493-species/level picker with the companion melonDS Android 2.1.1 build and an in-game L+R toggle.
- Replaced broken male/female + nature codes, updated the nature-only family and removed the incompatible clean-ROM overlay workaround. The current catalogue contains 2,110 codes in 67 folders. See the [catalogue audit](source/docs/cheat-catalogue-validation.md).
- Reduced party menu opening from 33 to 20 frames in the tested battles by reusing loaded move data.

- Refined optional battle motion: the idle cycle runs at 0.375× with interpolated steps and a gradual restart; the name, level, HP and EXP panels stay still. Motion continues through menu selections and yields to native move, entrance and fainting animations.
- Stops battle idle tasks before capture so they cannot animate the Pokémon reused by the Pokédex or nickname screen. Corrects cleanup when a Pokémon is replaced or the battle ends.
- Reduced the battle Bag opening pause with optional battle motion enabled: the Bag reuses item data already loaded for the battle. Local English and Italian tests reduce the pause from about 0.9 to 0.12 seconds; short loading pauses remain. See the [implementation and checks](source/features/borsa-lotta/README.md).
- Added regression coverage and a [source-backed animation audit](source/features/anim2/AUDIT-2026-09-14.md).

## 1.2.1 — initial release, 13 September 2026

The initial 13 September build used the previous Bag capacity and save layout. The current [1.2.1 downloads](https://github.com/Umberto-DEV/sacred-gold-plus/releases/tag/v1.2.1) include the 15 September changes above; the extra Bag slots are not available in older ROMs. The game header remains unchanged.

- **A full item stack no longer blocks a free gift or pickup.** The existing quantity cap stays in place; excess items are discarded and a message names the item that could not be kept. Purchases, exchanges, mail and key items keep their original checks.
- **Optional battle motion extends to both sides and the Bag and party menus.** Motion pauses during move animations. The setting remains off by default; loading transitions can still pause the whole battle display.
- **The in-game version now reads "Sacred Gold Plus 1.2.1"** on the screen shown at Continue. The title screen and game header remain unchanged.
- **The cheat catalogue is reordered and grown**: 67 folders instead of 56, 2113 codes instead of 1510. The 1510 existing codes keep their exact bytes — order, naming and notes are what changed. The 603 new ones are the wild-encounter family, 493 species and 100 levels. Every code that needs a button now says which one; 94 of them did not.
- The guard the wild-encounter codes check was re-read from the 1.2.1 image in both languages and matches, and one species and one level were measured on a headless emulator running the English build. The other 492 species and 99 levels differ by a single field and were not measured one by one; the Italian build was checked statically only. The shipped notes say so.
- **A Rare Candy no longer closes the party menu.** Use one and the menu stays open on the same Pokémon, ready for the next: levelling a team no longer means walking back through the Bag for every single candy. It leaves the menu exactly as before whenever the game has something of its own to do — an evolution, a move to replace, the last candy in the bag — so nothing about those paths changes.
- **The options page no longer lets you change a setting that would not stick.** When the save's Sacred Gold Plus block is missing or has been rejected, all five entries are now shown as unavailable instead of only the two difficulty ones. Before, the animation, NPC and online entries let you move the cursor, press A and see the new value drawn while nothing was written — not then, not later.
- **Turning NPC smoothing off now takes effect immediately.** The setting gave the game back its own character-loading budget only at the next map change; within the same area, switching it off did nothing visible. It is handed back on the first frame after you confirm.

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
- The optional battle motion moves existing sprites; it does not add per-species animation frames. Full-story and hardware coverage remain incomplete.
- The Wi-Fi slot fallback is fully demonstrated for three of its five cases on the test bench; the two that need a live online trigger were checked under emulation only. Official online services for this game are long discontinued.
- Cheats: the codes shipped in the package have bounded checks on the real game core. This is not full-game cheat coverage or a promise about every emulator.
