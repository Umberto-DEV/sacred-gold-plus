# What changed

## 1.2 — 12 September 2026

Built from the finished 1.1, not alongside it: everything 1.1 had is still there. There is now **one build per language** instead of a camera choice at download time — **Sacred-Gold-Plus-1.2-[IT or US].zip**. The Plus wide camera is the default everywhere outdoors; the original HeartGold camera remains available anywhere as the existing optional cheat.

Seven additions, each with its technical line:

- **Plus difficulty and Wild levels, two separate options.** Trainers can level up to 12% higher and, independently, wild Pokémon up to 8% higher, both capped at level 100 in this release; off by default, and byte-identical to 1.1 when off.
- **Native camera in eight indoor maps.** Mahogany Town's souvenir shop and Team Rocket hideout, and Mt. Mortar, now use the closer native HeartGold framing without a cheat; the Plus camera outdoors is unchanged.
- **Lower non-player-character load at town/route borders.** The measured worst-case stutter when crossing a border drops from 5 to 4 Nintendo DS frames across the six cities tested; on by default, switchable off in options.
- **Optional animated Pokémon.** Pokémon can move gently in battle instead of standing still; off by default, and the game is byte-identical to the version without it when left off.
- **A Sacred Gold Plus options page.** Press SELECT during play to open it; choices are written to the save file and survive a cold restart, and the game asks once at Continue whether to open it.
- **A choice of online connection slot.** Pick which of the three WFC firmware connection slots handles GTS, battles and trades; Mystery Gift always uses the first slot automatically; no server address is changed by the game.
- **214 text corrections** (212 English, 2 Italian), mostly repairing words a historical global text replacement had broken mid-word, plus a handful of Italian glossary terms.

This release also carries the 1.1 audit corrections already made on the development branch: the camera cheat's guard address, the installer header, and outdated hashes in the release manifests.

The download itself changed shape: each ZIP now contains the real patch files, an installation guide written for someone who has never applied a patch before, and a document describing what is new, instead of a single embedded browser installer. It accepts **11 recognized starting files**: unmodified US and Italian HeartGold, and English Sacred Gold Plus 1.01, 1.02, 1.03, both 1.04 cameras in both languages, and 1.1 in both languages. **1.1 cheat files do not carry over**, because 1.2's game header differs from 1.1's; melonDS matches cheats to a game by that header, so the 1.2 package includes its own cheat files to import instead.

## 1.04 — 9 September 2026

The current download has a simpler layout and names: **Sacred-Gold-Plus-[Normal-Angle or New-Angle]-[IT or US].zip**. The four game outputs are unchanged from the earlier 1.04 packages. Existing players with a matching game fingerprint do not need to patch again.

- Each ZIP now includes **Install-or-update.html**. It recognizes the supported unmodified **US HeartGold** and **English Plus 1.01, 1.02 and 1.03** inputs and automatically selects the matching update to that ZIP's language and camera. No older patches are required. The older previews used a single delta from Plus 1.03.
- The installer processes files offline in the browser, with no ROM upload or program installation. It recognizes an already-current target and refuses unknown inputs.
- **README.txt** remains at the top level, with a **Manual** folder for the original references and game guide. The HTML replaces the standalone delta in the ZIP; the layout still has 13 files.
- File checks, changes and credits collected in **Manual/Project Notes.txt**. The full licence remains included separately.
- Seven optional cheat codes in **Cheats**, with Italian names/descriptions in IT downloads and English in US downloads. Both desktop MCH and Android XML formats are included; all codes start disabled.
- Removed the obsolete Extras layout, Old Patches notes and separate patching-tools file. The included HTML handles installation and updates; individual deltas remain available in the repository for advanced manual use.
- Clearer instructions for extracting the ZIP, recognizing a supported game, downloading the updated file, switching variants and keeping a normal save.
- Updated the home page, contribution invitation and development plans. Selected gameplay screenshots remain unchanged.

All 16 supported input-to-variant routes have been checked against the complete expected output SHA-256 and size. Updater tests cover its supported contracts; these checks do not establish compatibility with every browser or Android file manager.

The selected cheats have bounded checks on the real game core. This is not full-game cheat coverage or a promise about every emulator. See [installation and cheat instructions](PLAY.md), the changes below, and the known limits.

## 1.04 Preview 2 — 8 September 2026

Historical packaging revision:

This is a packaging and documentation update. The four patches produce exactly the same games as Preview 1; it adds no new gameplay fixes and requires no save migration for existing Preview 1 players.

- Restored the familiar original download layout: **Readme + Changelog.txt**, **Game Info + Learnset Changes.txt**, one clearly named patch and **Extras**.
- Updated installation, save backup, language and camera instructions.
- Checked and refreshed 284 level-up entries for the seven added Fairy moves against the actual 1.03 and 1.04 game data.
- Included five original Sacred Gold / Storm Silver PDF guides and the credited trainer reference, clearly marked as historical references where Plus differs.
- Added the original project logo and fuller acknowledgements on the home page.

Original ROMs, emulator software, old Windows patching executables and unverified cheat databases are not included. Extras explains where to find patching tools and earlier releases. Preview 1 remains available as a historical download.

## 1.04 Preview 1 — 8 September 2026

This is the first public preview of our independent continuation of Sacred Gold Plus 1.03. It packages the existing tested candidate; the version label does not introduce additional gameplay changes.

Available in **Italian (IT)** and **English (US)**, each with **Normal Angle** or **New Angle**.

### Included changes

- Restored two damaged hardware-wait instructions in the 1.03 game. The checks cover those specific operations; this is not a claim that all crashes or save problems are fixed.
- Repaired malformed text-formatting instructions, including menu alignment and text-colour reset values.
- Corrected selected trade dialogue and English move names so the wording matches the intended Pokémon or move.
- Repaired the Pokédex search resources used by the height and weight controls, and corrected mismatched language labels.
- Added Italian dialogue, menus and selected interface graphics, with an accented-character naming keyboard. The existing Plus additions are retained.
- Added the optional Normal Angle camera. New Angle retains the camera used by Sacred Gold Plus 1.03.

Fairy typing, the additional Fairy moves and the 1.03 battle changes come from the earlier project. They are not new features created for 1.04. No emulator fix is included in these game patches.

### Checks completed

The four patch outputs match the four reproducible source builds. Tests have checked message encoding, protected game data, startup, normal save/restart and selected Pokédex searches. The Italian keyboard has targeted checks. These are bounded tests, not a completed full-game playthrough.

## Known limits

**1.2, on top of the limits below:**

- Every 1.2 result to date comes from reading the game's own bytes or from an emulator (melonDS, on a Mac and on Android); nothing has been confirmed yet on a real Nintendo DS. Until that testing is done, "verified on emulator" is the most any 1.2 claim means.
- The native indoor camera has been watched running in the English build; the Italian build and the remaining maps have only been checked against the game's internal map table, not watched on screen yet.
- Animated Pokémon still has two open grading points (how natural it looks with several Pokémon animated together, and a check across more species) that carry over into hardware testing.
- The online connection slots have been exercised through Mystery Gift; reaching a live GTS or battle server has only been checked on an emulated processor, not with a real internet connection end to end. A third-party DNS used for these servers can see your name, friend code and traded Pokémon — use one knowingly, or not at all.
- Save compatibility with 1.1 has been checked on the save file itself, byte for byte, but not across a full playthrough that spans the update.
- 214 of 235 identified text corrections are in this release; the rest are held back until confirmed against an official source for that generation, and a larger backlog of untranslated technical strings is separate, ongoing work.
- The large third-party Action Replay cheat catalogue (about 1,500 codes) has not been tested against 1.2 at all; treat it as unverified material, same as in 1.1.

**Carried over from 1.04/1.1:**

- Full-story and post-game testing is still needed. Some corrected dialogue and translated screens need further in-game review.
- The original game's reported event issues are not all fixed by this release. Please report a reproducible case rather than assuming a historical bug list is resolved.
- Newly added Fairy moves can still use their older battle animations, as reported by the original Plus author.
- In Italian, Pokédex height/weight search filters still use the original US units. Species pages can use metric units. Changing the labels alone would make those filters misleading.
- The lower non-player-character load at town/route borders is a measured, bounded reduction in the worst-case stutter there, not a general frame-rate improvement; the wider or narrower camera itself remains a visual choice only.
- Repeatedly using an item from the bag menu still does not work as expected, as in 1.1.

Report new findings through [the bug form](https://github.com/Umberto-DEV/sacred-gold-plus/issues/new/choose). The next feature work is described in [the roadmap](ROADMAP.md).
