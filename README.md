# Sacred Gold Plus

**Explore Johto and Kanto with new ways to train, hunt and manage your Pokémon.**

**Version 1.3.1** · **English and Italian** · [GPL-3.0-or-later](LICENSE) for this project's own tools and sources

An independent fan continuation of **Drayano's Sacred Gold** and **NefariousnessNo3436's Sacred Gold Plus** for Nintendo DS. Fairy typing, additional Fairy moves and the wider outdoor camera come from the original Plus project. This continuation adds native game tools, an Italian translation, adjustable settings and targeted repairs.

This is a **patch** for your own HeartGold cartridge backup. No ROM, save, BIOS or emulator is included.

**Development status:** the source tree contains an unreleased 1.3.2 correction
for a New Game reset. The downloads and screenshots below are still the
published 1.3.1 release. See the [1.3.2 source bug note](BUG-FIXES-1.3.2.md).

## Download

Choose the language you want to **play in**. Both packages can be patched on Windows and macOS.

| Edition | Player package |
| --- | --- |
| **English** | [**Download English 1.3.1 ZIP**](https://github.com/Umberto-DEV/sacred-gold-plus/releases/download/v1.3.1-r2/Sacred-Gold-Plus-1.3.1-US.zip) |
| **Italian** | [**Download Italian 1.3.1 ZIP**](https://github.com/Umberto-DEV/sacred-gold-plus/releases/download/v1.3.1-r2/Sacred-Gold-Plus-1.3.1-IT.zip) |

[Release page and checksums](https://github.com/Umberto-DEV/sacred-gold-plus/releases/tag/v1.3.1-r2). Extract the ZIP and open **How-to-install-1.3.1-EN.pdf** or **Come-installare-1.3.1-IT.pdf**. The matching **Whats-New-1.3.1-EN.pdf** / **Novita-1.3.1-IT.pdf** introduces the current game. Original gameplay references remain in `Manual` with their credits.

Each ZIP includes **25 direct patch routes** from recognized USA/Italian HeartGold and Plus inputs through V1.3. The ZIP chooses the **finished language**; US/IT folders inside `Patch` identify the **starting ROM**. Match its complete SHA-256 in the installation guide and apply **one** patch. You do not need older releases first. GitHub's automatic **Source code** archives are for developers.

## What's new

Since **1.2.5**, the game adds:

- **A field Guide with 467 entries:** evolutions, items and TMs, special events and training. Browse categories and linked detail pages with the buttons; L/R moves through lists in groups of five.
- **Reorganized Plus settings:** contextual help and a second page for shiny modes and species search. Trainer difficulty and wild level scaling remain separate choices, capped at level 100.
- **IV consultants and Caps:** the Violet and Blackthorn PokéMarts offer Silver Caps for one IV and Gold Caps for all six. Choose 31 or an exact single-IV value from 0 to 31. Purchases and milestone rewards also support existing adventures.
- **EV services and Day Care courses:** quick training, free reductions/resets, Classic limits of 252 per stat and 510 overall, or Unlimited with 252 in all six stats. Route 34 courses provide levels and optional EV training using real time or active playtime; the Day Care phone contact reports progress.
- **Classic and Pro shiny modes:** Classic uses 1/512 for eligible generation. Pro improves the selected species' odds at chains of 10, 20 and 40, from 1/4096 to 1/512. Species Search charges with 40 valid steps and respects the area's encounter pool, terrain, time and progression.
- **Selected species and trainer improvements:** 67 species affected, including 50 stat changes and 32 level/move additions across 29 learnsets. Plus difficulty adds nine targeted move substitutions across seven trainers. The caught-species Ball also appears in trainer battles.
- **Portable Pokémon storage:** press **R** in the ordinary field party menu to open the native PC interface where the game permits it.
- **Targeted battle updates:** Will-O-Wisp has 85 accuracy; effective Keen Eye ignores the target's evasion changes. These changes retain the game's ability-suppression rules.

The species review covers all 493 species and changes selected entries. Existing Pokémon keep their identity, IVs, EVs, moves and abilities; the game recalculates affected stats through its normal loading paths. [Full changes, species and trainer details](source/docs/whats-new-1.3.1.md).

Coming from **the original Plus 1.03**? The continuation also brings English/Italian dialogue and interface work, the classic HeartGold camera in **52 interiors and caves**, an **EV/IV reader in the Pokémon summary** (L for EVs, R for IVs, SELECT to restore stats), adjustable trainer/wild levels, optional Pokémon motion in battle, spread-out NPC loading, battle-menu caches, Wi-Fi slot selection and over 200 text corrections. The expanded Bag offers **252 slots in the main pocket**, and consecutive Rare Candy use keeps the party menu open while preserving normal evolution and move-learning prompts.

## Some bugs fixed.

Repairs inherited from HeartGold/SoulSilver include the following; the version labels distinguish older fixes retained by 1.3.1 from new work.

- **Heavy Ball:** the neutral 102.4–204.7 kg weight band no longer receives the retail penalty. This was already fixed in **Plus 1.1**. Fast Ball and Quick Ball use their separate rules.
- **Moves:** Fire Fang respects Wonder Guard; leaving Rage preserves Transform and other battle state; transformed stats and moves are handled correctly in the repaired reload paths. The Hail/Snow Warning fix was already present in **Plus 1.03**.
- **Pokémon and abilities:** repairs cover trainer alternate-form stats/abilities, Giratina's party stats after leaving the PC, and AI handling of Dry Skin, Motor Drive, immunities and legal switches.
- **Field and rewards:** targeted repairs cover the poisoned follower's interrupted jump, Waterfall facing, six invisible-grass tiles on Routes 43/44, the League guard after viewing GS Cup species, and pending Kurt/Pryce rewards when the relevant Bag pocket is full.
- **Audio and counters:** targeted fixes address GB Sounds returning from evolution move-learning, the 999-hour playtime boundary and the Pokéathlon species counter.

[Retail bug catalogue and evidence](source/docs/known-bugs-hgss.md) · [Fixes and their tested scope](BUG-FIXES-1.3.1.md). The catalogue also records unresolved and inapplicable reports; its total is not a count of fixed bugs.

## More bugs fixed.

Further repairs address Sacred Gold/Plus behaviour and this continuation's own regressions:

- **Battle and AI:** Fairy matchups and Conversion 2, Ghost damage against Dragon/Dark, Iron Ball/Gravity interactions, move scoring and a type-check loop that could freeze battles when returning to the move menu.
- **Pokémon and progression:** evolution parameters for Mantyke, Feebas, Burmy and Combee; selected fishing records; Mew's event movement; Steven's pending reward and the Ho-Oh/Lugia scene selectors.
- **Items, saves and interface:** the Goldenrod Underground pickup quantity, full-Bag gift handling, Plus-settings recovery, extra Bag data protection, story flags that overlapped Friend Roster/Chatot data, and Guide/Options navigation, transitions and native button-repeat timing.

Earlier fixes such as Garchomp's Rough Skin, Claydol's Fly and Scizor's Night Slash remain included. Specific scenarios have different test coverage; unresolved reports and historical limitations remain in the [bug list](BUG-FIXES-1.3.1.md), [hack research](source/docs/legacy-bugs-1.3.1.md), [changelog](CHANGELOG.md) and [validation report](source/docs/ui-1.3.1-validation.md).

## Screenshots

Actual game frames. Title, Guide and Options captures use the published 1.3.1 ROMs; storage captures retain their earlier 1.3.1 build identities. Location captures are from 1.2.5, and the wild battle is from 1.2.4. The galleries record their original build identities: [1.3.1 captures](images/1.3.1/captures.json) · [location captures](images/captures.json).

| | |
| --- | --- |
| ![English 1.3.1 title](images/1.3.1/title-EN.png)<br>English title | ![Italian 1.3.1 title](images/1.3.1/title-IT.png)<br>Italian title |
| ![Party menu with R Box shortcut](images/1.3.1/party-EN.png)<br>R: Box from the field party | ![Native Pokémon storage](images/1.3.1/pc-EN.png)<br>Native Pokémon storage |
| ![Italian party menu](images/1.3.1/party-IT.png)<br>Party: R opens the Box | ![Italian Pokémon storage](images/1.3.1/pc-IT.png)<br>Native Pokémon storage |
| ![Current field Guide](images/1.3.1/guide-EN.png)<br>Field Guide | ![Current Plus options](images/1.3.1/options-EN.png)<br>Plus options |
| ![Ecruteak City](images/01-ecruteak-city.png)<br>Ecruteak City | ![Goldenrod City](images/18-goldenrod-city.png)<br>Goldenrod City |
| ![Bellchime Trail](images/03-bellchime-trail.png)<br>Bellchime Trail | ![Lake of Rage](images/20-lake-of-rage.png)<br>Lake of Rage |

<details>
<summary>More locations and existing game tools</summary>

| | |
| --- | --- |
| ![New Bark Town](images/02-new-bark-town.png)<br>New Bark Town | ![Olivine City](images/04-olivine-city.png)<br>Olivine City |
| ![Cherrygrove City](images/05-cherrygrove-city.png)<br>Cherrygrove City | ![National Park](images/06-national-park.png)<br>National Park |
| ![Professor Elm's laboratory](images/07-elms-lab.png)<br>Professor Elm's laboratory | ![Pokémon Center](images/08-pokemon-center.png)<br>Pokémon Center |
| ![Mt. Mortar](images/09-mt-mortar.png)<br>Classic indoor camera | ![Wild battle](images/10-wild-battle.png)<br>Wild battle |
| ![EV viewer](images/13-ev-viewer-top.png)<br>EV viewer in the summary | ![IV viewer](images/14-iv-viewer-top.png)<br>IV viewer in the summary |
| ![Violet City](images/19-violet-city.png)<br>Violet City | ![Dragon's Den entrance](images/21-blackthorn-city.png)<br>Blackthorn City |
| ![Ecruteak Dance Theater](images/22-dance-theater.png)<br>Dance Theater | ![Sprout Tower](images/23-sprout-tower.png)<br>Sprout Tower |
| ![Violet Poké Mart](images/24-violet-pokemart.png)<br>Violet Poké Mart | ![Lake of Rage house](images/25-lakeside-house.png)<br>A lakeside house |

</details>

## Install or update

1. **Extract your language's ZIP** and read its installation PDF. Use your own supported HeartGold or Plus `.nds` and match its full SHA-256 in **Reference A**.
2. **Choose one patch** under `Patch/From Clean ROM` or `Patch/From Plus <version>`. The guide distinguishes both 1.04 cameras and both 1.2.2 editions; 1.01–1.03 have verified English inputs only.
3. Open [Rom Patcher JS](https://www.marcrobledo.com/RomPatcher.js/), select the checked `.nds` as **ROM file** and the matching `.xdelta` as **Patch file**. Leave **Fix ROM checksum** off, apply the patch to a new file and verify **Reference B** before installing it.

**Updating an existing adventure:** save in-game, close the emulator completely and find its actual current save folder. Back up both the installed ROM and current raw `.sav`. Keep the same language, ROM filename/path and emulator association. First test the verified successor with a separate copy of your save: **Continue → check progress, Pokémon, Bag and Plus settings → in-game SAVE → close fully → cold start → Continue**. Then replace only the installed ROM; retain your current personal save and its original location. A temporary test save must never replace it.

If Continue is missing, fix the save association before proceeding. A new game or settings reset is not part of updating. Resume from the normal in-game save, not an old emulator savestate. Keep the backup: older ROMs may not expose extra Bag slots, and saving there can prevent automatic recovery of those items.

**Cheats:** no catalogue is included because old codes are not verified against these game bytes. The native game tools work without cheats; read the package's `Cheats` notice. Network services depend on the emulator and service provider.

## Source code and contributions

Public technical documentation is maintained in English for the current release; Italian player guides are included in the downloadable Italian package. The complete implemented sources, build tools, tests and technical documentation are under [`source/`](source/README.md), including the [1.3 builder](source/sgp13/README.md) and [1.3.1 composition tools](source/sgp131/). Building requires your own retail game and the documented external inputs. ROMs, saves, BIOS, extracted game data and private working notes are excluded from the source tree.

The [repository map](source/docs/architecture/README.md) shows where each game
subsystem, build stage, validation report and distribution tool belongs.

Contributions to code, translations, artwork, testing and documentation are welcome, together with player ideas and feedback. [Report a bug or propose a change](https://github.com/Umberto-DEV/sacred-gold-plus/issues); include the version, language and steps, without uploading your ROM or save. Maintainer changes are reviewed and validated on `main`; independent contributors may submit pull requests. CI runs the tests that require no game file; game-dependent validation is recorded separately.

## Credits and license

Thanks to **Drayano**, **mikelan / Mikelan98**, **NefariousnessNo3436**, **@JD48096761** and the original contributors. The original Plus author's [announcement and permission](https://www.reddit.com/r/PokemonROMhacks/comments/1m69jrj/sacred_gold_plus_fairy_type_full_implementation/) remain the reference for the project's foundation. The original gameplay manuals and trainer reference retain their authors' credits. This is an independent fan continuation, not an official handover.

Some patch features, bug diagnosis and security checks were developed with
AI-assisted tools, including Codex and Claude Code. The maintainer has 2–3 years
of development experience and uses these tools daily; changes are reviewed
against the game code and measured with focused tests. This describes the
actual review process, not a claim of formal penetration-test certification.
Development uses [pret/pokeheartgold](https://github.com/pret/pokeheartgold), [ndspy](https://github.com/RoadrunnerWMC/ndspy), [Unicorn](https://www.unicorn-engine.org/), [Capstone](https://www.capstone-engine.org/) and the [melonDS core](https://melonds.kuribo64.net/); dependencies and external inputs are documented in the source guide.

This project's own tools and sources use [GPL-3.0-or-later](LICENSE). Pokémon, the original game and third-party contributions remain under their owners' rights. No game code, text, graphics, ROM, BIOS or save is distributed in this source tree.
