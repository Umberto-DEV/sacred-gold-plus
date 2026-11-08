**Pokémon Sacred Gold Plus** is an independent fan continuation of Sacred Gold Plus, built on Drayano's Sacred Gold for Nintendo DS. Explore Johto and Kanto with the original Plus project's Fairy typing, additional Fairy moves and wider outdoor camera, alongside new settings and quality-of-life improvements.

Available in **English, Italian, French, Spanish and German**.

## Download

| Editions | Player package |
| --- | --- |
| All five languages | [Download the multilingual patch package](https://github.com/Umberto-DEV/sacred-gold-plus/releases/download/{{RELEASE_TAG}}/Sacred-Gold-Plus-{{PACKAGE_VERSION}}-Multilingual.zip) |
| Direct updates from older Plus ROMs | [Optional updater download](https://github.com/Umberto-DEV/sacred-gold-plus/releases/download/{{RELEASE_TAG}}/Sacred-Gold-Plus-{{PACKAGE_VERSION}}-Optional-Updaters.zip) |

**Windows and Mac:** download and extract the main ZIP, open **Sacred Gold Plus {{VERSION}}**, then read **START-HERE.txt**. Choose **EN-English**, **IT-Italiano**, **FR-Francais**, **ES-Espanol** or **DE-Deutsch**.

Open **Installation-{{VERSION}}-EN.pdf** directly inside the English folder, or the matching `-IT`, `-FR`, `-ES` or `-DE` file in your language folder. **Whats-New-{{VERSION}}-<language>.pdf** is beside it. The illustrated installation guide includes real patcher screenshots, clickable links and Windows/macOS file checks. Each folder contains one current patch in `Patch`, localized `Cheats` and `Credits-and-Licenses`. `Originals` contains seven current English gameplay PDFs: events, Pokémon changes and locations, evolutions, items/TMs, trainers and one Game Guide. There are no `Documents` folders or technical JSON files in the main ZIP.

**New to patching?** Start from your own supported original HeartGold `.nds` of the same language. Check its full SHA-256 against the installation PDF, apply **Patch/Sacred-Gold-Plus-{{VERSION}}-<language>.xdelta** to a separate file with [Rom Patcher JS](https://www.marcrobledo.com/RomPatcher.js/), leave **Fix ROM checksum** off, and verify the complete target SHA-256 before installing it.

**Updating Plus?** Keep your current language for an ordinary update. SAVE in-game, fully close the emulator, locate its actual raw `.sav`, and back up that save and the installed ROM. Test the verified successor with a separate save copy: **Continue → check progress, Pokémon, Bag and Plus settings → in-game SAVE → close fully → cold start → Continue**. Then replace only the installed ROM, retaining its filename/path and emulator association. Keep your current personal save in its original location.

The **optional updater ZIP** has all **150 direct routes: 30 recognized starting ROMs for each of five current language targets**. Its localized **README-Updater.txt** tables list the complete source hash, size and exact patch name, plus the current target hash. They cover the supported retail editions and verified historical Plus inputs through 1.3.1, including original Plus 1.03 and separately identified 1.04 and 1.2.2 editions. Apply **one** patch matching your exact input. Older versions are input identities; only the current {{VERSION}} targets are produced. Unknown or modified ROMs are not admitted.

Cheats are optional. Each language's `Cheats` folder in the main ZIP contains localized project code files for that exact target, initially disabled, with `README.txt` explaining their static admission checks and runtime coverage. Native features such as the Guide and EV/IV reader need no cheats. Historical third-party cheat catalogues are not carried forward.

Package revision **r3** changes the download layout and document notices; the five game ROMs remain byte-identical to 1.3.2. If you already have the verified 1.3.2 game, you do not need to patch it again. Both downloads retain credits and the complete original English GPLv3 with localized explanations. Use the main player ZIP to play; GitHub's automatic **Source code (zip / tar.gz)** files are for developers. No ROM is included: use your own cartridge backup.

<details>
<summary>Build inputs for developers</summary>

The source tools use these authenticated inputs, preserved with their original hashes:
[English base delta](https://github.com/Umberto-DEV/sacred-gold-plus/releases/download/{{RELEASE_TAG}}/base-1.1-EN.xdelta),
[Italian base delta](https://github.com/Umberto-DEV/sacred-gold-plus/releases/download/{{RELEASE_TAG}}/base-1.1-IT.xdelta),
[English reference documents](https://github.com/Umberto-DEV/sacred-gold-plus/releases/download/{{RELEASE_TAG}}/SGP-Source-References-EN.zip),
[Italian reference documents](https://github.com/Umberto-DEV/sacred-gold-plus/releases/download/{{RELEASE_TAG}}/SGP-Source-References-IT.zip).
Use the multilingual player ZIP above to install the current game.

</details>

## Game features

- **Five language editions:** English, Italian, French, Spanish and German dialogue, names, menus, Guide and player documents. Regional editions combine official retail presentation with translated Sacred Gold/Plus additions, while sharing the same gameplay rules and save layout.
- **EV/IV tools inside the game:** inspect EVs with L and IVs with R in the Pokémon summary, and return to the normal stats with SELECT. No cheat is needed. The field Guide covers evolutions, items and TMs, events and training.
- **Adjustable difficulty:** optional trainer level increases and a separate setting for wild Pokémon level scaling, capped at level 100.
- **Grouped settings:** press SELECT in Options for the Game, Plus and Shiny groups, with contextual help. Manage difficulty, wild levels, Pokémon motion, NPC smoothing, Wi-Fi connection slot selection and shiny profiles. Apply confirms Plus edits; cancelling retains the previous settings.
- **Classic HeartGold camera in 52 interiors and caves:** paths and objects are easier to see in the affected maps, while the wider Plus camera remains outdoors.
- **Optional Pokémon motion in battle:** both sides can move while waiting for an action and during menu selection. It uses the existing sprites and yields to the game's move, entrance and fainting animations.
- **Smoother town loading and quicker battle menus:** NPC loading is spread out when entering or leaving towns, and the Bag and party menus reuse data already loaded for the battle.
- **Expanded Bag and consecutive Rare Candy use:** 252 slots in the main pocket, expanded capacity in the other pockets, and a party menu that stays open after using a Rare Candy. Evolution and move-learning prompts follow the normal game flow.
- **Text and gameplay corrections:** over 200 English/Italian text fixes, Pokédex search repairs, corrected move names and dialogue, and fixes for item pickups, Bag handling and battle sprite copies.

- **IV consultants and EV training:** Silver and Gold Caps at the Violet and Blackthorn PokéMarts, quick EV services and free level/EV courses at the Route 34 Day Care. Set one IV to 31 or an exact value from 0 to 31, or use a Gold Cap for all six. Classic EV rules allow 252 per stat and 510 overall; Unlimited allows 252 in all six stats. Choose real time or active playtime for courses; milestone rewards support existing adventures.
- **Classic and Pro shiny modes:** Classic uses 1/512 for eligible generation. Pro improves the selected species' odds at chains of 10, 20 and 40, from 1/4096 to 1/512. Species Search charges with 40 valid steps and respects the area's eligible encounter pool, terrain, rods, time and progression.
- **Selected species and trainer improvements:** targeted stat and learnset changes across the roster, purposeful Plus trainer moves, 85-accuracy Will-O-Wisp and the Keen Eye evasion rule. These are specific changes rather than a complete later-generation ruleset.
- **Portable Pokémon storage:** press R in the ordinary field party menu to open the native PC interface in permitted contexts.

## Development and testing

I’m a junior developer at a software company, with a solid working knowledge of programming. For about a year, I’ve used Claude Code and Codex daily, supported by custom private skills.
They assist with coding, exploratory and structural audits, debugging, testing and security work across this project and my melonDS forks.
The ideas for my additions came from me; I guided implementation, defined most tests and measurements before, during and after changes, and retained the final say.

Testing has used native melonDS and Mac-hosted melonDS Android environments, plus my AYN Thor (12 GB RAM, 256 GB storage). The final 1.3.2 checks ran on Mac; Thor results cover earlier builds.
My current Android fork is [UD Nightly 2.1, versionCode 53](https://github.com/Umberto-DEV/melonDS-android/releases/tag/ud-nightly-2.1).
I have not tested this project on MSI Claw, Steam Deck, other devices or original Nintendo DS hardware. Community reports are welcome, especially from original hardware.

Version 1.3.2 adds French, German and Spanish alongside English and Italian, with localized patches, installation instructions and guides.

## Screenshots

Historical game captures illustrating the existing world and features. The titles are from published 1.3.1; party and storage images retain their earlier 1.3.1 build identities. Location captures are from 1.2.5, and the wild battle is from 1.2.4. Exact capture identities are recorded in the [1.3.1 gallery](https://github.com/Umberto-DEV/sacred-gold-plus/blob/main/images/1.3.1/captures.json) and [location gallery](https://github.com/Umberto-DEV/sacred-gold-plus/blob/main/images/captures.json).

| | |
| --- | --- |
| ![Ecruteak City]({{IMAGE_BASE_URL}}/01-ecruteak-city.png)<br>Ecruteak City | ![Bellchime Trail]({{IMAGE_BASE_URL}}/03-bellchime-trail.png)<br>Bellchime Trail |
| ![Goldenrod City]({{IMAGE_BASE_URL}}/18-goldenrod-city.png)<br>Goldenrod City | ![Lake of Rage]({{IMAGE_BASE_URL}}/20-lake-of-rage.png)<br>Lake of Rage |
| ![Wild battle]({{IMAGE_BASE_URL}}/10-wild-battle.png)<br>A wild battle - historical capture | ![1.3.1 title]({{IMAGE_BASE_URL}}/1.3.1/title-EN.png)<br>English 1.3.1 title |
| ![Historical 1.3.1 party shortcut]({{IMAGE_BASE_URL}}/1.3.1/party-EN.png)<br>R: Box from the field party - historical 1.3.1 | ![Historical 1.3.1 native storage]({{IMAGE_BASE_URL}}/1.3.1/pc-EN.png)<br>Native Pokémon storage - historical 1.3.1 |
| ![Italian 1.3.1 title]({{IMAGE_BASE_URL}}/1.3.1/title-IT.png)<br>Italian 1.3.1 title | ![Historical Italian 1.3.1 storage]({{IMAGE_BASE_URL}}/1.3.1/pc-IT.png)<br>Native Italian storage - historical 1.3.1 |

<details>
<summary>More cities, interiors and game screens</summary>

| | |
| --- | --- |
| ![New Bark Town]({{IMAGE_BASE_URL}}/02-new-bark-town.png)<br>New Bark Town | ![Olivine City]({{IMAGE_BASE_URL}}/04-olivine-city.png)<br>Olivine City |
| ![Cherrygrove City]({{IMAGE_BASE_URL}}/05-cherrygrove-city.png)<br>Cherrygrove City | ![National Park]({{IMAGE_BASE_URL}}/06-national-park.png)<br>National Park |
| ![Elm's laboratory]({{IMAGE_BASE_URL}}/07-elms-lab.png)<br>Professor Elm's laboratory | ![Pokémon Center]({{IMAGE_BASE_URL}}/08-pokemon-center.png)<br>Pokémon Center |
| ![Mt. Mortar]({{IMAGE_BASE_URL}}/09-mt-mortar.png)<br>Mt. Mortar | ![Historical Italian 1.3.1 party shortcut]({{IMAGE_BASE_URL}}/1.3.1/party-IT.png)<br>Party: R opens the Box - historical 1.3.1 |
| ![Violet City]({{IMAGE_BASE_URL}}/19-violet-city.png)<br>Violet City | ![New Bark Town]({{IMAGE_BASE_URL}}/02-new-bark-town.png)<br>New Bark Town |
| ![Blackthorn City]({{IMAGE_BASE_URL}}/21-blackthorn-city.png)<br>Dragon's Den entrance, Blackthorn City | ![Dance Theater]({{IMAGE_BASE_URL}}/22-dance-theater.png)<br>Ecruteak Dance Theater |
| ![Sprout Tower]({{IMAGE_BASE_URL}}/23-sprout-tower.png)<br>Sprout Tower | ![Violet Poké Mart]({{IMAGE_BASE_URL}}/24-violet-pokemart.png)<br>Violet City Poké Mart |
| ![Lakeside house]({{IMAGE_BASE_URL}}/25-lakeside-house.png)<br>A house at the Lake of Rage | |

</details>

[Full gallery and capture details](https://github.com/Umberto-DEV/sacred-gold-plus/tree/main/images). The locations shown are part of the existing game.

## Community and credits

I'd like the community to help carry this project forward. Contributions to code, translations, artwork, testing and documentation are welcome, as are ideas and feedback from players.

[Source code and contributions](https://github.com/Umberto-DEV/sacred-gold-plus) · [Report a bug or propose a change](https://github.com/Umberto-DEV/sacred-gold-plus/issues)

Thanks to **NefariousnessNo3436, Drayano, mikelan / Mikelan98**, and the original contributors. Fairy typing, the additional Fairy moves and the wider camera come from the original Plus project.

[Original Sacred Gold Plus announcement](https://www.reddit.com/r/PokemonROMhacks/comments/1m69jrj/sacred_gold_plus_fairy_type_full_implementation/)

[Detailed bug and fix list](https://github.com/Umberto-DEV/sacred-gold-plus/blob/main/BUG-FIXES-1.3.2.md) · [Changelog and validation](https://github.com/Umberto-DEV/sacred-gold-plus/blob/main/CHANGELOG.md)

## Latest update

Some bugs fixed.
