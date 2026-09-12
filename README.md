![Sacred Gold Plus — original project logo](sacred-gold-plus-logo.webp)

# Sacred Gold Plus

An independent continuation of Sacred Gold Plus 1.03, maintained by one fan. I started this to keep a game I enjoy alive, bring it to Italian and give others a place to help improve it. I'm one person learning as I go, and anyone who wants to join in is very welcome: players, testers, translators, artists and developers.

[Download](#download-12) · [How to play](PLAY.md) · [Game guide](GAME-GUIDE.md) · [Contribute](CONTRIBUTING.md)

Sacred Gold Plus adds Fairy typing, new Fairy moves and a wider camera option to Drayano's Sacred Gold. The original trainer teams and levels are retained, while their moves follow the Plus learnsets. The [game guide](GAME-GUIDE.md) explains these inherited changes and links to the original documentation.

## Download 1.2

**Version 1.2 is available.** It is built from the finished 1.1, so it carries everything 1.1 had. There is now **one build per language**: the camera is the Plus wide view everywhere outdoors, with the original HeartGold view restored natively in eight indoor maps and still available everywhere as the optional camera cheat. Keep a backup of your game and save before updating; [the changelog](CHANGELOG.md#known-limits) explains what has been checked and what still needs testing.

| Language | Download |
| --- | --- |
| Italian (IT) | [Download IT](https://github.com/Umberto-DEV/sacred-gold-plus/releases/download/v1.2/Sacred-Gold-Plus-1.2-IT.zip) |
| English (US) | [Download US](https://github.com/Umberto-DEV/sacred-gold-plus/releases/download/v1.2/Sacred-Gold-Plus-1.2-US.zip) |

**What 1.2 adds**, on top of everything 1.1 already had:

- **Plus difficulty** and **Wild levels**, two separate in-game options: tougher trainers and, independently, wild Pokémon that scale with your progress, both capped at level 100 in this release. Leave them off and the game plays byte-identical to 1.1.
- **Native camera in eight indoor maps** (Mahogany Town's souvenir shop and Team Rocket hideout, and Mt. Mortar): no cheat needed. The classic HeartGold camera stays available everywhere as an optional cheat.
- **Smoother towns**: fewer non-player characters loaded in a single frame at a town/route border, which measurably reduces the worst stutter there.
- **Optional animated Pokémon**: Pokémon can move gently in battle instead of standing still. Off by default.
- **A Sacred Gold Plus options page**: press SELECT during play. Your choices save with your game, and the game asks once, on Continue, whether you want to look at them.
- **A choice of online connection**: pick which of your emulator's three WFC firmware slots handles GTS, battles and trades. Mystery Gift always uses the first slot automatically. No server address is changed by the game itself.
- **214 text corrections** in English and Italian, mostly repairing words broken by an old global text replacement.

Extract your ZIP and open the installation guide included inside it: it walks through picking the right patch for your file and applying it with one of three free tools (a desktop program, an Android app, or a page that runs in your browser). It recognizes the supported **unmodified US and Italian HeartGold** and **English Sacred Gold Plus 1.01, 1.02, 1.03, 1.04 (both cameras) and 1.1** as starting files; no older patches are needed first. [Installation, supported files and saves](PLAY.md). You do not need the source folders or GitHub's “Source code” ZIP to play.

[What changed in 1.2](CHANGELOG.md) · [Plans beyond 1.2](ROADMAP.md) · [All releases](https://github.com/Umberto-DEV/sacred-gold-plus/releases)

**Emulator:** [melonDS](https://melonds.kuribo64.net/) Android 2.1 or newer is recommended; it is the build the new options page and the online-connection choice were checked against. If you use the three WFC connection slots, remember they are configured inside melonDS' own Wi-Fi settings, one address per slot — 1.2 only chooses which configured slot a given online service uses, it does not add or change any address itself.

**Cheats:** your 1.1 cheat files do not carry over. melonDS matches a cheat catalogue to a game by its header, and 1.2's header is different from 1.1's. Re-import the cheat files from the 1.2 package; all codes start switched off.

**Saves:** a 1.1 save opens in 1.2 and a 1.2 save opens in 1.1 — checked byte for byte on the save file. What is not yet checked is a full playthrough across the change; keep your previous game file and an untouched save until you are satisfied. [Full details](PLAY.md).

Tested so far on emulator: melonDS on desktop and on Android. Testing on real Nintendo DS hardware is in progress; [known limits](CHANGELOG.md#known-limits) says exactly what has and has not been watched running yet.

## See the game

| Title screen | Exploring New Bark Town |
| --- | --- |
| ![The title screen of the English game](images/06-title-screen.png) | ![Exploring New Bark Town in the English game](images/01-new-bark-town.png) |

[More screenshots, including 1.2's native indoor camera and options page](SCREENSHOTS.md).

## Development: beyond 1.2

These are candidates for future work, not a promise that everything will be included in one release:

- **1.2b:** raising the level cap further, to 150, with a per-stat ceiling instead of one global stop.
- **1.3:** asking which online server to use from inside the Pokémon Center clerk's own dialogue, instead of only in the options page; more complete translations for other languages.
- **Throughout development:** preserve saves and Nintendo DS compatibility, use repeatable tests, keep instructions simple, and make patches check the exact game version they start from.

[Read the development plan](ROADMAP.md). There is no release date yet.

## Help improve the game

[Report a problem](https://github.com/Umberto-DEV/sacred-gold-plus/issues/new/choose), [share an idea or ask a question](https://github.com/Umberto-DEV/sacred-gold-plus/discussions), or [contribute a fix or translation](CONTRIBUTING.md). A clear report from a player is useful even without programming experience.

AI tools help me investigate bugs, work on code and translations, write test scripts and prepare documentation. Further human review and playtesting are welcome. If future updates add new areas or artwork, the plan is to create those visuals by hand, with help from artists who want to contribute.

<details>
<summary>For contributors: what is in the folders?</summary>

`patches` contains the downloadable changes and file checks; `source` contains the tools and recipes used to build them; `.github` provides contribution forms, review rules and a file-checking script. Players only need the download links and installation guide above.

</details>

## Thanks to the original creators

Thank you to **NefariousnessNo3436** for creating Sacred Gold Plus, sharing its patches and documentation, and allowing others to build on it with credit. Thank you to **Drayano** for Sacred Gold and Storm Silver, and **mikelan / Mikelan98** for the Fairy-type work that made Plus possible.

The logo above comes from the [original Sacred Gold Plus post](https://www.reddit.com/r/PokemonROMhacks/comments/1m69jrj/sacred_gold_plus_fairy_type_full_implementation/). This is an independent community project, not an official release or endorsement by the earlier authors. [Full credits](CREDITS.md).
