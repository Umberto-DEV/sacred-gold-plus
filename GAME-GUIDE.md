# Game guide

Sacred Gold Plus builds on Drayano's Sacred Gold, a HeartGold hack. The notes below summarize the original author's **1.03 documentation**. They describe the game we started from; our own 1.04 and 1.2 changes are listed separately in the [changelog](CHANGELOG.md).

## Sacred Gold Plus 1.2 additions

These are new in 1.2, on top of everything described below for Plus. Each one is a switch on the in-game [options page](PLAY.md), except the camera, which is either automatic or an existing cheat.

- **Plus difficulty.** With the option on, trainers battle up to **12%** higher level than the base game, stopping at a **level 100** cap in this release. A higher cap is a candidate for a later release; see the [roadmap](ROADMAP.md#beyond-12). With the option off, battles play out identical to 1.1, down to the byte.
- **Wild levels.** With the option on, wild Pokémon can level up to **8%** higher than the base game's encounter tables, up to the same level 100 cap; it is a separate switch from Plus difficulty. Off by default, matching 1.1 when off.
- **Native camera in eight indoor maps.** Mahogany Town's souvenir shop and the Team Rocket hideout beneath it, and Mt. Mortar, now use the closer native HeartGold framing on their own, with nothing to switch on. Every other indoor and outdoor area keeps the wider Plus camera. The original HeartGold camera is still available everywhere through the existing optional cheat; toggling it takes effect the next time you walk into a map. Verified running in the English build; the Italian build has been checked against the game's own map data but not yet watched on screen.
- **Smoother towns**, the options page's **Characters** switch. Entering or leaving a town can momentarily ask the game to load several non-player characters in the same frame; 1.2 limits how many load at once, cutting the worst measured delay at a town/route border from 5 to 4 Nintendo DS frames across the cities tested. It ships smooth (on) by default and can be switched to Normal to compare.
- **Animated Pokémon.** Pokémon can move gently while waiting in battle — a small, continuous sway — instead of holding perfectly still. It ships off by default; with it off, battles are byte-identical to a game without the option at all.
- **A choice of online connection.** The options page can pick which of your emulator's three Nintendo Wi-Fi Connection slots is used for GTS, battles and trades; Mystery Gift always uses the first slot on its own. The game does not run a server or change any server address — it only chooses among the slots you have already configured in your emulator.

## What Plus changes

- **Fairy typing:** Pokémon that gained the Fairy type in Generation 6 receive it here too.
- **Fairy moves:** seven moves replace older moves, and several existing moves become Fairy type. The original 1.03 notes describe updated ways for Pokémon to learn the new moves.
- **Trainer battles:** Sacred Gold's teams and levels remain, but Plus 1.03 generally uses moves from the Pokémon's level-up learnset instead of Drayano's custom battle movesets. This changes some battle strategies; it is not a claim that every trainer follows one universal rule.
- **Camera:** Plus introduced a wider, Black/White-inspired view. Our **New Angle** download keeps it; **Normal Angle** uses HeartGold's original camera settings.

## Move changes in the original notes

| Added move | Replaces |
| --- | --- |
| Baby-Doll Eyes | Pay Day |
| Dazzling Gleam | Barrage |
| Disarming Voice | Rolling Kick |
| Draining Kiss | Kinesis |
| Fairy Wind | Spider Web |
| Moonblast | Conversion |
| Play Rough | Conversion 2 |

Charm, Moonlight, Sweet Kiss, Comet Punch, Dizzy Punch and Covet become Fairy type. Curse becomes Ghost type.

Some new moves still use the animations of the moves they replaced. The original author reported this limitation; 1.04 does not claim to fix it. Turning battle animations off is an optional workaround.

## Earlier fixes and balance changes

The author's 1.02 changelog reports fixes for Garchomp's Rough Skin, Claydol's ability to learn Fly, Scizor's Night Slash, Ledyba's intended stat change, some names and descriptions, and the names shown for new moves in battle. Version 1.03 then revised how the new Fairy moves are learned and adjusted trainer movesets.

These are earlier authors' changes, not new fixes made by this continuation. Original documents can also describe Sacred Gold before Plus changed it, so their trainer movesets and some move information may differ from Plus.

## Original references

The original package includes gameplay notes, learnset lists, and Sacred Gold / Storm Silver guides for encounters, events, evolutions and items. Keep them as useful references; the older guides are not a verified walkthrough for every 1.04 situation.

Start with **README.txt** in your download. **Manual/Game Guide.txt** includes 284 level-up entries for the seven added Fairy moves, checked against Plus 1.03 and all four 1.04 game outputs. The **Manual** folder also contains five original PDF guides and the credited trainer reference. **Manual/Project Notes.txt** collects file checks, current changes and credits. The older references remain useful, but some details differ from Plus as explained above.

| Looking for | Where to start |
| --- | --- |
| Pokémon locations and encounters | **Pokemon Locations.pdf** in the download's Manual folder |
| Evolution methods | **Evolution Changes.pdf** in Manual |
| Items and TMs | **Important Item Locations.pdf** in Manual |
| Events and special encounters | **Special Event Guide.pdf** in Manual |
| Earlier Pokémon changes | **Pokemon Changes.pdf** in Manual |
| Fairy moves and checked level-up lists | **Manual/Game Guide.txt** |
| Optional cheats for the current game | **Cheats** in your download, with the note on reimporting them in the [home page](README.md#download-12) |
| Earlier Action Replay and cheat notes | [Historical cheat references](guides/historical-cheats/README.md) in this repository |

The two historical cheat documents are preserved from the original 1.03 package. They are **not a verified 1.04 cheat collection**: read their compatibility notes before using a code. They remain separate from the seven-code selection in the current ZIPs. Nothing in the download installs or enables cheats automatically.

- [Original release post and download](https://www.reddit.com/r/PokemonROMhacks/comments/1m69jrj/sacred_gold_plus_fairy_type_full_implementation/)
- [Author's features and learnset document](https://docs.google.com/document/d/1IbXXpWf9HUO7uCwn1tOxgd8MpsNa2FNiZxpxTmBXYJA/edit)
- [How to play the 1.2 additions](PLAY.md) — the installation guide is included in your downloaded package; the original package's instructions apply only to its own older patch.

Thank you to **NefariousnessNo3436**, **Drayano**, **mikelan / Mikelan98** and the original contributors for the game, patches and documentation. [Full credits](CREDITS.md).
