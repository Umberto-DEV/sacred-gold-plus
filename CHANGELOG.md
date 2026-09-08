# What changed

## 1.04 Preview 2 — 8 September 2026

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

### Known limits

- Full-story and post-game testing is still needed. Some corrected dialogue and translated screens need further in-game review.
- The original game's reported event issues are not all fixed by this release. Please report a reproducible case rather than assuming a historical bug list is resolved.
- Newly added Fairy moves can still use their older battle animations, as reported by the original Plus author.
- In Italian, Pokédex height/weight search filters still use the original US units. Species pages can use metric units. Changing the labels alone would make those filters misleading.
- Save compatibility is verified only for the tested cases. Keep an untouched backup, especially when changing language.
- A wider or narrower camera is a visual choice. No general frame-rate improvement is claimed.
- Cheats are not included in these patch downloads. Third-party cheat lists can contain duplicates, incompatible codes or item codes that overwrite custom items. Test without cheats first.

Report new findings through [the bug form](https://github.com/Umberto-DEV/sacred-gold-plus/issues/new/choose). The next feature work is described in [the 1.05 plan](ROADMAP.md).
