# Credits and permissions

**Drayano** created Sacred Gold and Storm Silver. **mikelan / Mikelan98** contributed the Fairy-type implementation used by this line of projects. **NefariousnessNo3436** created Sacred Gold Plus and its 1.03 additions.

Thank you to NefariousnessNo3436 for making this work available to players and other developers, and to everyone who contributed to Sacred Gold and Storm Silver. This continuation would not exist without that foundation.

The [original Sacred Gold Plus release post](https://www.reddit.com/r/PokemonROMhacks/comments/1m69jrj/sacred_gold_plus_fairy_type_full_implementation/) describes that work and includes the author's reply permitting reuse with credit. This repository is an independent continuation, not an official handover or endorsement by those authors. Its 1.04, 1.1 and 1.2 numbering refers to this continuation.

The original Sacred Gold / Storm Silver PDF guides included in the player downloads remain credited to **Drayano and the original contributors**. **@JD48096761** compiled the included trainer reference, with inspiration credited there to **u/ittapubas**. These original documents are preserved as references; the current package adds separate explanations of the differences in Plus.

The historical cheat documents from the Plus 1.03 package keep their original credits; individual codes are not automatically covered by our tools' licence. The author also mentioned separate follow-up work by DeadSkullzJr on GBAtemp in a later reply. This repository does not claim to be the only continuation, or to include that separate work. The cheat selection shipped with the current downloads has had its labels and format prepared for the chosen language; that does not claim authorship of the original codes or validation of the complete historical catalogue.

The screenshots in the README are unedited captures of 1.2 using a test character. The underlying artwork remains credited to the original game and hack creators.

## Third-party material used by the tools

| What | Where it comes from | Terms |
| --- | --- | --- |
| Character mapping (`charmap.txt`) for the game's text encoding | [pret/pokeheartgold](https://github.com/pret/pokeheartgold), pinned at commit `0985e8718df4f25e64d6507d89c0c97c0d288981` | **Not redistributed here.** The text tools read it from a checkout you make yourself; `source/README.md` gives the command. Its licensing was not established to our satisfaction, so it is an external input like the game file. |
| Structure knowledge for save data, message banks and the ARM9 layout | pret/pokeheartgold, same commit | Knowledge, not code: the implementations in `source/` are written here. |
| [ndspy](https://github.com/RoadrunnerWMC/ndspy) | pinned in `source/requirements.txt` | Its own licence; installed as a dependency, not vendored. |
| [Unicorn](https://www.unicorn-engine.org/) and [Capstone](https://www.capstone-engine.org/) | pinned in `source/requirements.txt` | Their own licences; installed as dependencies, used to run and disassemble our own compiled code in the tests. |
| [melonDS](https://melonds.kuribo64.net/) | the headless test bench in `source/runtime/` is a harness around the upstream core, pinned at commit `906e9ebb27da8c6a715cd7abab4abfe8a8d29427` | GPL-3.0-or-later, the same licence as this project. No binary is distributed here; `source/runtime/README.md` explains how to build it. |
| Marc Robledo's [RomPatcher.js](https://github.com/marcrobledo/RomPatcher.js) engine files, pinned at commit [3183884](https://github.com/marcrobledo/RomPatcher.js/tree/3183884086825c3a57c72026234debcef1e2240c) | used by the offline HTML installer shipped with the 1.04 packages | [MIT](https://github.com/marcrobledo/RomPatcher.js/blob/3183884086825c3a57c72026234debcef1e2240c/LICENSE); the copyright and full notice travel inside each installer file. |

## No game material in this repository

This repository carries the tools, our own C and assembly sources, the code we compiled from them, and the addresses, sizes and fingerprints needed to place that code. It does not carry game code, game text, game graphics, archives, tables extracted from the ROM, saves, BIOS or firmware. Where a tool needs one of those, it reads it from your own file at build time: the text corrections, for example, are published as edits keyed to a message and its SHA-256, and the table the applier consumes is rebuilt from your ROM.

## Licence

The [GPL-3.0-or-later licence](LICENSE) applies to this project's original tools and code. Pokémon, the original game material and third-party contributions remain under their respective owners' rights and terms. Attribution does not transfer those rights or make every game asset freely reusable. This project distributes changes for use with the player's own required game file, not complete ROMs, BIOS or saves.

This continuation is maintained by one fan, with help from AI tools for bug investigation, development, translation, testing scripts and documentation. It does not claim that every generated suggestion or translated line has received a complete human review. Test claims are limited to the checks described in the release notes and in [DEVELOPMENT.md](DEVELOPMENT.md), and further human language review and playtesting are welcome.
