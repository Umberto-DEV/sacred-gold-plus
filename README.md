# Sacred Gold Plus

**Explore Johto and Kanto with new ways to train, hunt and manage your Pokémon.**

**Version 1.3.2** · **English, Italian, French, Spanish and German** · [GPL-3.0-or-later](LICENSE) for this project's own tools and sources

An independent fan continuation of **Drayano's Sacred Gold** and **NefariousnessNo3436's Sacred Gold Plus** for Nintendo DS. Fairy typing, additional Fairy moves and the wider outdoor camera come from the original Plus project. This continuation adds native game tools, Italian/French/Spanish/German localization, adjustable settings and targeted repairs.

This is a **patch** for your own HeartGold cartridge backup. No ROM, save, BIOS or emulator is included.

## Download

[**Download Sacred Gold Plus 1.3.2 — all five languages**](https://github.com/Umberto-DEV/sacred-gold-plus/releases/download/v1.3.2-r3/Sacred-Gold-Plus-1.3.2-r3-Multilingual.zip)

Choose your language folder after extracting the ZIP:

| Language | Folder |
| --- | --- |
| English (USA) | `EN-English` |
| Italiano | `IT-Italiano` |
| Français — new in 1.3.2 | `FR-Francais` |
| Español (España) — new in 1.3.2 | `ES-Espanol` |
| Deutsch — new in 1.3.2 | `DE-Deutsch` |

Read `START-HERE.txt`, then open `Installation-1.3.2-<language>.pdf` directly
inside your language folder for an illustrated Windows/macOS walkthrough, links
and file checks. `Whats-New-1.3.2-<language>.pdf` is beside it.
Each folder contains **one** clearly named `Patch/Sacred-Gold-Plus-1.3.2-<language>.xdelta`,
for the supported original HeartGold ROM of that same language, localized
`Cheats` and `Credits-and-Licenses`. Apply the patch to a separate file with
[Rom Patcher JS](https://www.marcrobledo.com/RomPatcher.js/), leave **Fix ROM checksum**
off, and verify the complete source and target SHA-256 from the installation PDF.
`Originals` contains seven current English gameplay guides, including one Game Guide.
There are no `Documents` folders or technical JSON files in this player ZIP.

**Updating an older Plus ROM directly?** Use the separate
[optional updater download](https://github.com/Umberto-DEV/sacred-gold-plus/releases/download/v1.3.2-r3/Sacred-Gold-Plus-1.3.2-r3-Optional-Updaters.zip).
Its localized `README-Updater.txt` tables identify all 30 recognized sources,
including original Plus 1.03 and our published predecessors through 1.3.1.
Choose your current language and **one** patch matching the complete input hash;
all 150 routes lead to the same five current 1.3.2 targets. Unknown or altered
ROMs are not admitted. Older playable targets are not bundled.

Before updating, SAVE in-game, close the emulator, locate and back up the actual
raw `.sav` and installed ROM. Validate the successor on a separate save copy
through Continue, in-game SAVE and cold restart. Replace only the installed ROM,
retaining its language, filename/path and emulator association; keep the current
personal save in its original location. The main clean-ROM patch can also
reconstruct that same successor without using the older installed ROM as input.

[Release page and checksums](https://github.com/Umberto-DEV/sacred-gold-plus/releases/tag/v1.3.2-r3).
Package revision **r3** reorganizes downloads; the five game ROMs remain byte-identical
to 1.3.2. If you already have the verified 1.3.2 game, you do not need to patch it
again. Historical contracts and tags retain their identities. GitHub's automatic
**Source code** archives are for developers.

An Italian Guide-opening issue is under investigation. This packaging revision
retains the game targets and does not claim to fix that report.

The new languages combine official retail dialogue, names and graphics with
separately authored translations of Sacred Gold/Plus changes, menus and guides.
They share the same gameplay code and save layout. Locale sources are clearly
separated under [`source/localization/locales/`](source/localization/locales/);
[the build documentation](source/docs/localization.md) explains ownership,
input identities and validation. README and technical source docs stay English.

## What's new

The current game includes:

- **A field Guide with 467 entries:** evolutions, items and TMs, special events and training. Browse categories and linked detail pages with the buttons; L/R moves through lists in groups of five.
- **Reorganized Plus settings:** grouped game, Plus and shiny settings, contextual help and species search. Trainer difficulty and wild level scaling remain separate choices, capped at level 100.
- **IV consultants and Caps:** the Violet and Blackthorn PokéMarts offer Silver Caps for one IV and Gold Caps for all six. Choose 31 or an exact single-IV value from 0 to 31. Purchases and milestone rewards also support existing adventures.
- **EV services and Day Care courses:** quick training, free reductions/resets, Classic limits of 252 per stat and 510 overall, or Unlimited with 252 in all six stats. Route 34 courses provide levels and optional EV training using real time or active playtime; the Day Care phone contact reports progress.
- **Classic and Pro shiny modes:** Classic uses 1/512 for eligible generation. Pro improves the selected species' odds at chains of 10, 20 and 40, from 1/4096 to 1/512. Species Search charges with 40 valid steps and respects the area's encounter pool, terrain, time and progression.
- **Selected species and trainer improvements:** 67 species affected, including 50 stat changes and 32 level/move additions across 29 learnsets. Plus difficulty adds nine targeted move substitutions across seven trainers. The caught-species Ball also appears in trainer battles.
- **Portable Pokémon storage:** press **R** in the ordinary field party menu to open the native PC interface where the game permits it.
- **Targeted battle updates:** Will-O-Wisp has 85 accuracy; effective Keen Eye ignores the target's evasion changes. These changes retain the game's ability-suppression rules.

The species review covers all 493 species and changes selected entries. Existing Pokémon keep their identity, IVs, EVs, moves and abilities; the game recalculates affected stats through its normal loading paths. [Full changes, species and trainer details](source/docs/whats-new-1.3.1.md).

Coming from **the original Plus 1.03**? The continuation also brings English/Italian dialogue and interface work, the classic HeartGold camera in **52 interiors and caves**, an **EV/IV reader in the Pokémon summary** (L for EVs, R for IVs, SELECT to restore stats), adjustable trainer/wild levels, optional Pokémon motion in battle, spread-out NPC loading, battle-menu caches, Wi-Fi slot selection and over 200 text corrections. The expanded Bag offers **252 slots in the main pocket**, and consecutive Rare Candy use keeps the party menu open while preserving normal evolution and move-learning prompts.

## Some bugs fixed.

Repairs inherited from HeartGold/SoulSilver include the following; the version labels distinguish older fixes retained in 1.3.2 from subsequent work.

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
- **1.3.2 startup and localized menus:** the New Game reset after Mom's first conversation, native field-dialogue layout, and translated footer/confirmation controls that exceeded their actual button-layout bounds.

Earlier fixes such as Garchomp's Rough Skin, Claydol's Fly and Scizor's Night Slash remain included. Current scope is in the [1.3.2 bug list](BUG-FIXES-1.3.2.md) and [validation report](source/docs/validation/localization-1.3.2.md). The [1.3.1 bug list](BUG-FIXES-1.3.1.md), [hack research](source/docs/legacy-bugs-1.3.1.md) and [earlier validation](source/docs/ui-1.3.1-validation.md) preserve historical evidence; the [changelog](CHANGELOG.md) separates the versions.

## Development and testing

I’m a junior developer at a software company, with a solid working knowledge of programming. For about a year, I’ve used Claude Code and Codex daily, supported by custom private skills.
They assist with coding, exploratory and structural audits, debugging, testing and security work across this project and my melonDS forks.
The ideas for my additions came from me; I guided implementation, defined most tests and measurements before, during and after changes, and retained the final say.

Testing has used native melonDS and Mac-hosted melonDS Android environments, plus my AYN Thor (12 GB RAM, 256 GB storage). The final 1.3.2 checks ran on Mac; Thor results cover earlier builds.
My current Android fork is [UD Nightly 2.1, versionCode 53](https://github.com/Umberto-DEV/melonDS-android/releases/tag/ud-nightly-2.1).
I have not tested this project on MSI Claw, Steam Deck, other devices or original Nintendo DS hardware. Community reports are welcome, especially from original hardware.

Version 1.3.2 adds French, German and Spanish alongside English and Italian, with localized patches, installation instructions and guides.

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

1. **Extract the multilingual ZIP**, open your language folder and read its installation PDF. Match your own supported `.nds` against the complete source SHA-256.
2. **Choose one patch** under that folder's `Patch` matching your exact source hash. Each output language supports the same 30 recognized original/historical bases; keep your current language for an ordinary update.
3. Open [Rom Patcher JS](https://www.marcrobledo.com/RomPatcher.js/), select the checked `.nds` as **ROM file** and the matching `.xdelta` as **Patch file**. Leave **Fix ROM checksum** off, apply to a new file and verify the target SHA-256 in the installation PDF before installing it.

**Updating an existing adventure:** save in-game, close the emulator completely and find its actual current save folder. Back up both the installed ROM and current raw `.sav`. Keep the same language, ROM filename/path and emulator association. First test the verified successor with a separate copy of your save: **Continue → check progress, Pokémon, Bag and Plus settings → in-game SAVE → close fully → cold start → Continue**. Then replace only the installed ROM; retain your current personal save and its original location. A temporary test save must never replace it.

If Continue is missing, fix the save association before proceeding. A new game or settings reset is not part of updating. Resume from the normal in-game save, not an old emulator savestate. Keep the backup: older ROMs may not expose extra Bag slots, and saving there can prevent automatic recovery of those items.

**Cheats:** use only your language folder's current-revision material and read its compatibility notice. Historical databases are not carried forward automatically. The native game tools work without cheats. Network services depend on the emulator and service provider.

## Source code and contributions

Public technical documentation is maintained in English for the current release; player guides are translated in each of the five language folders. The complete implemented sources, build tools, tests and technical documentation are under [`source/`](source/README.md), including the [1.3 builder](source/sgp13/README.md) and [shared composition tools](source/sgp131/) and [locale sources](source/localization/). Building requires your own retail game and the documented external inputs. ROMs, saves, BIOS, extracted game data and private working notes are excluded from the source tree.

The [repository map](source/docs/architecture/README.md) shows where each game
subsystem, build stage, validation report and distribution tool belongs.

Contributions to code, translations, artwork, testing and documentation are welcome, together with player ideas and feedback. [Report a bug or propose a change](https://github.com/Umberto-DEV/sacred-gold-plus/issues); include the version, language and steps, without uploading your ROM or save. Independent contributors can follow the [contribution guide](CONTRIBUTING.md) from fork to pull request; maintainer changes are reviewed and validated directly on `main`. CI checks public files and runs tests that require no game file. A green run does not validate a playable ROM or an existing save.

## Credits and license

Thanks to **Drayano**, **mikelan / Mikelan98**, **NefariousnessNo3436**, **@JD48096761** and the original contributors. The original Plus author's [announcement and permission](https://www.reddit.com/r/PokemonROMhacks/comments/1m69jrj/sacred_gold_plus_fairy_type_full_implementation/) remain the reference for the project's foundation. The original gameplay manuals and trainer reference retain their authors' credits. This is an independent fan continuation, not an official handover.

Development uses [pret/pokeheartgold](https://github.com/pret/pokeheartgold), [ndspy](https://github.com/RoadrunnerWMC/ndspy), [Unicorn](https://www.unicorn-engine.org/), [Capstone](https://www.capstone-engine.org/) and the [melonDS core](https://melonds.kuribo64.net/); dependencies and external inputs are documented in the source guide.

This project's own tools and sources use [GPL-3.0-or-later](LICENSE). Pokémon, the original game and third-party contributions remain under their owners' rights. No game code, text, graphics, ROM, BIOS or save is distributed in this source tree.
