# Sacred Gold Plus

**A fan-made continuation of Sacred Gold Plus, for the Nintendo DS.**

**Version 1.2.5** · **License:** [GPL-3.0-or-later](LICENSE) (this project's own tools; third-party rights below)

Sacred Gold Plus adds Fairy typing, new Fairy moves and a wider camera option to Drayano's *Sacred Gold*. This continuation keeps that foundation and adds an Italian translation, a native indoor camera, adjustable difficulty, and a set of quality fixes.

Original project: [Sacred Gold Plus by NefariousnessNo3436](https://www.reddit.com/r/PokemonROMhacks/comments/1m69jrj/sacred_gold_plus_fairy_type_full_implementation/) — the author’s announcement, with its documentation and downloads.

This is a **patch**, not a ROM: you apply it to your own legally obtained game file. No game file is distributed here.

## Screenshots

Captured on the local melonDS test bench. Each image shows one DS screen; the bottom screens demonstrate the Plus settings and guide.

| | |
| --- | --- |
| ![Ecruteak City](images/01-ecruteak-city.png)<br>Ecruteak City | ![Bellchime Trail](images/03-bellchime-trail.png)<br>Bellchime Trail |
| ![New Bark Town](images/02-new-bark-town.png)<br>New Bark Town | ![Wild battle](images/10-wild-battle.png)<br>Wild battle |
| ![Plus options — English (bottom screen)](images/11-plus-options-english-bottom.png)<br>Plus options — English (bottom screen) | ![Plus options — Italian (bottom screen)](images/12-plus-options-italian-bottom.png)<br>Plus options — Italian (bottom screen) |
| ![EV viewer in the Pokémon summary](images/13-ev-viewer-top.png)<br>EV viewer in the Pokémon summary | ![IV viewer in the Pokémon summary](images/14-iv-viewer-top.png)<br>IV viewer in the Pokémon summary |
| ![In-game EV/IV guide (bottom screen)](images/15-ev-iv-guide-bottom.png)<br>In-game EV/IV guide (bottom screen) | ![Version 1.2.5 title screen](images/17-version-title-top.png)<br>Version 1.2.5 title screen |
| ![Goldenrod City — exploring the city.](images/18-goldenrod-city.png)<br>Goldenrod City — exploring the city. | ![Violet City — outside the Poké Mart.](images/19-violet-city.png)<br>Violet City — outside the Poké Mart. |
| ![Lake of Rage — a rainy day by the water.](images/20-lake-of-rage.png)<br>Lake of Rage — a rainy day by the water. | ![Blackthorn City — the entrance to Dragon's Den.](images/21-blackthorn-city.png)<br>Blackthorn City — the entrance to Dragon's Den. |

<details>
<summary>More locations, interiors and guide controls</summary>

| | |
| --- | --- |
| ![Olivine City](images/04-olivine-city.png)<br>Olivine City | ![Cherrygrove City](images/05-cherrygrove-city.png)<br>Cherrygrove City |
| ![National Park](images/06-national-park.png)<br>National Park | ![Professor Elm's laboratory](images/07-elms-lab.png)<br>Professor Elm's laboratory |
| ![Inside a Pokémon Center](images/08-pokemon-center.png)<br>Inside a Pokémon Center | ![Mt. Mortar — native indoor camera](images/09-mt-mortar.png)<br>Mt. Mortar — native indoor camera |
| ![Guide controls (bottom screen)](images/16-guide-controls-bottom.png)<br>Guide controls (bottom screen) |  |
| ![Inside the Ecruteak Dance Theater.](images/22-dance-theater.png)<br>Inside the Ecruteak Dance Theater. | ![Inside Sprout Tower.](images/23-sprout-tower.png)<br>Inside Sprout Tower. |
| ![Inside the Violet City Poké Mart.](images/24-violet-pokemart.png)<br>Inside the Violet City Poké Mart. | ![Inside a house at the Lake of Rage.](images/25-lakeside-house.png)<br>Inside a house at the Lake of Rage. |

</details>

The locations are part of the existing game. All views were captured in 1.2.5 except the wild battle, captured in 1.2.4 with unchanged battle graphics. These are actual game frames, cropped to one screen and enlarged 4× without smoothing. [Capture details and image hashes](images/captures.json).

## Main features

- **English and Italian editions**, with translated dialogue and menus.
- **Adjustable Plus difficulty:** optional trainer and wild Pokémon level scaling, configured from the Plus options page with SELECT.
- **Optional Pokémon motion in battle**, switchable in the game settings.
- **Classic HeartGold camera in 52 interior and cave maps**, with the wider Plus camera outdoors.
- **Expanded Bag:** 252 slots in the main pocket and consecutive Rare Candy use from the party menu.
- **Quality-of-life improvements:** an in-game EV/IV guide, Wi-Fi connection slot selection, text corrections and gameplay fixes.

## Download

Choose the language you want to **play in**. Both packages work on **Windows and macOS**:

| Edition | Download 1.2.5 |
| --- | --- |
| **English** | [**Download English ZIP**](https://github.com/Umberto-DEV/sacred-gold-plus/releases/download/v1.2.5/Sacred-Gold-Plus-1.2.5-US.zip) |
| **Italiano** | [**Scarica ZIP italiano**](https://github.com/Umberto-DEV/sacred-gold-plus/releases/download/v1.2.5/Sacred-Gold-Plus-1.2.5-IT.zip) |

[Release page and all downloads](https://github.com/Umberto-DEV/sacred-gold-plus/releases/tag/v1.2.5). Use the named player ZIP above. GitHub's automatic **Source code** archives are developer files and are not needed to play.

## Install for the first time

1. **Extract the ZIP.** Windows: right-click → **Extract All**. Mac: double-click. Open **Sacred Gold Plus 1.2.5** inside the extracted download.
2. **Read `How-to-install-1.2.5-EN.pdf`** (English) or **`Come-installare-1.2.5-IT.pdf`** (Italian). This illustrated guide sits directly in the main folder, beside **Whats-New-1.2.5-EN.pdf** / **Novita-1.2.5-IT.pdf**. Follow its numbered steps, screenshots and SHA-256 reference list.
3. **Identify your own HeartGold `.nds`.** The guide shows how to calculate its SHA-256 in your browser or with built-in Windows/Mac commands, and exactly which expected value to compare. A matching filename is not enough. Use your own cartridge backup; do not download pirated ROMs.
4. **Choose one patch.** For a matching original USA HeartGold: `Patch/From Clean ROM/US/from-clean-us.xdelta`. For a matching Italian original: `Patch/From Clean ROM/IT/from-clean-it.xdelta`. You do **not** need Sacred Gold or an older Plus version first.
5. **Apply it with [Rom Patcher JS](https://www.marcrobledo.com/RomPatcher.js/).** Select your checked `.nds` under **ROM file**, the matching `.xdelta` under **Patch file**, then **Apply patch**. Leave **Fix ROM checksum** off in Settings. Verify the new file's SHA-256 against the guide's **finished game** value, then open it in your DS emulator.

**The ZIP edition chooses the final language. The US/IT subfolder chooses the language of your starting ROM.** For example, the English ZIP can produce English from either a supported USA or Italian original.

**Already playing Plus?** Back up your current ROM and save, then use the `From Plus` folder for your current version and language. All 21 supported paths go directly to 1.2.5; apply only one patch. Older 1.01, 1.02 and 1.03 inputs exist only in English. The guide also distinguishes the 1.04 camera variants and the two 1.2.2 editions by their SHA-256.

**What you need:** your own supported HeartGold or Plus `.nds`, a patcher and a DS emulator/flashcart. ROMs, BIOS and emulators are not included. Cheats are optional. The searchable cheat picker and L+R toggle require [this fork's melonDS Android 2.1.1](https://github.com/Umberto-DEV/melonDS-android/releases/tag/v2.1.1); this is separate from patch installation.

## Compatibility

Updates preserve existing raw `.sav` files; start the updated ROM and choose **Continue**. Save in-game and close the emulator before changing ROMs. Keep a backup, and use your emulator’s save import or matching ROM/save filenames if the new filename changes. Emulator quick saves/savestates are tied to the old running game and should not be used to resume after an update.

Version **V.1.2.5** appears on the upper title screen and in **Options → SELECT → Plus**. [Fix and save-compatibility validation](source/docs/version-1.2.5.md).

- **Saves:** existing 1.1/1.2/1.2.1/1.2.2 saves import. Extra Bag slots use a save extension; older ROMs do not expose those items, and saving there prevents automatic recovery of the extra slots. Keep a backup when changing ROM builds and load the normal in-game save.
- **Cheats:** the game header is unchanged from 1.2, but import the updated catalogue to get the corrected codes. 1.1 catalogues have a different header. Every supplied code starts disabled.

## Source code and contributing

Everything that builds and checks this game is in [`source/`](source/README.md): the library that rebuilds 1.2.5 from an unmodified HeartGold ROM with one command and verifies it with another, one folder per feature with our C sources, tools and tests, and the technical reference in [`source/docs/`](source/docs/). The only game file you need is the retail game you already own — the first build step derives our 1.1 base from it with a published patch of differences, so no intermediate ROM of ours is needed and none is distributed.

- The maintainer and coding assistants work **only on `main`, without creating branches or pull requests**, in every current and future chat or session. See the standing instructions in [AGENTS.md](AGENTS.md). Changes are reviewed and checked before publication; community contributions from other accounts may still use pull requests.
- Every push and pull request runs the tests that need no game file (`source/run_tests.py`). Building the game needs your own copy of it, so that step happens on your machine, never on GitHub; the pull request template asks what you ran locally.
- Finished versions are tags (`v1.2.5`) with the player ZIPs attached to the [release](https://github.com/Umberto-DEV/sacred-gold-plus/releases); previews are marked pre-release.
- Never commit ROMs, saves, BIOS, dumps, game text or extracted game data. The public-file check in CI refuses them.

## Credits

Built on **Drayano**'s *Sacred Gold* and Storm Silver; **mikelan / Mikelan98** contributed the Fairy-type implementation; **NefariousnessNo3436** created Sacred Gold Plus and its 1.03 additions, and [allowed reuse with credit](https://www.reddit.com/r/PokemonROMhacks/comments/1m69jrj/sacred_gold_plus_fairy_type_full_implementation/). This is an independent continuation, not an official handover. The original PDF guides in the packages remain credited to Drayano and the original contributors; **@JD48096761** compiled the trainer reference. Developed by a fan, with community contributions.

Third-party material used by the tools, none of it redistributed here: the character mapping from [pret/pokeheartgold](https://github.com/pret/pokeheartgold) (read from your own checkout), [ndspy](https://github.com/RoadrunnerWMC/ndspy), [Unicorn](https://www.unicorn-engine.org/) and [Capstone](https://www.capstone-engine.org/) as pinned dependencies, and the [melonDS](https://melonds.kuribo64.net/) core (GPL-3.0-or-later) as the base of the headless test bench you build yourself.

## License

This project's own tools and sources are licensed under [GPL-3.0-or-later](LICENSE). Pokémon, the original game and third-party contributions remain under their owners' rights; attribution does not transfer them. No game code, text, graphics, ROM, BIOS or save is distributed here.

---

## In italiano

**Sacred Gold Plus** è una continuazione amatoriale di Sacred Gold Plus per Nintendo DS: tipo Folletto, nuove mosse Folletto e camera panoramica, con in più traduzione italiana, camera originale negli interni, difficoltà regolabile e correzioni.

Progetto originale: [Sacred Gold Plus di NefariousnessNo3436](https://www.reddit.com/r/PokemonROMhacks/comments/1m69jrj/sacred_gold_plus_fairy_type_full_implementation/) — il post dell’autore con documentazione e download.

Questa è una **patch**, non una ROM: va applicata a una copia posseduta legalmente del gioco. Nessun file di gioco è distribuito qui.

**Funzioni principali:**

- **Edizioni italiana e inglese**, con dialoghi e menu tradotti.
- **Difficoltà Plus regolabile:** livelli di allenatori e Pokémon selvatici configurabili dalla pagina Plus, accessibile con SELECT.
- **Animazioni opzionali dei Pokémon in lotta**, attivabili dalle impostazioni del gioco.
- **Camera classica di HeartGold in 52 mappe di interni e grotte**, con camera panoramica Plus all’aperto.
- **Borsa espansa:** 252 slot nella tasca principale e uso consecutivo delle Caramelle Rare dal menu Squadra.
- **Migliorie pratiche:** guida EV/IV nel gioco, scelta dello slot Wi-Fi, correzioni dei testi e del gioco.

**Download 1.2.5:** [**Edizione italiana**](https://github.com/Umberto-DEV/sacred-gold-plus/releases/download/v1.2.5/Sacred-Gold-Plus-1.2.5-IT.zip) · [**English edition**](https://github.com/Umberto-DEV/sacred-gold-plus/releases/download/v1.2.5/Sacred-Gold-Plus-1.2.5-US.zip). Entrambi gli ZIP funzionano su Windows e Mac. Scegli la lingua in cui vuoi giocare; gli archivi automatici “Source code” sono per sviluppatori.

**Prima installazione:**

1. Estrai lo ZIP: su Windows clic destro → **Estrai tutto**, su Mac doppio clic. Apri la cartella **Sacred Gold Plus 1.2.5**.
2. Leggi **`Come-installare-1.2.5-IT.pdf`**: è la guida illustrata da seguire, direttamente nella cartella principale insieme a **Novita-1.2.5-IT.pdf**. Contiene passaggi numerati, schermate e riferimenti SHA-256.
3. Controlla lo **SHA-256** del tuo HeartGold `.nds`: la guida spiega come calcolarlo e dove trovare il valore atteso. Il nome del file non basta. Usa la copia della tua cartuccia; non scaricare ROM piratate.
4. Per la ROM originale italiana corrispondente scegli `Patch/From Clean ROM/IT/from-clean-it.xdelta`; per quella USA scegli `Patch/From Clean ROM/US/from-clean-us.xdelta`. Non serve installare prima Sacred Gold o una vecchia Plus.
5. Su [Rom Patcher JS](https://www.marcrobledo.com/RomPatcher.js/) scegli il `.nds` in **ROM file** e il `.xdelta` in **Patch file**, poi premi **Apply patch**. Lascia **Fix ROM checksum** spento in Settings. Controlla lo SHA del nuovo file usando il valore del **gioco ottenuto** nella guida e aprilo nel tuo emulatore DS.

**La lingua dello ZIP è quella del risultato; US/IT dentro Patch identifica la ROM di partenza.** Lo ZIP italiano produce il gioco italiano anche partendo dall'originale USA supportato.

**Aggiornamento:** salva nel gioco, chiudi l'emulatore e copia ROM e salvataggio in un backup. Scegli la cartella `From Plus` della tua versione e lingua attuali. Le 21 patch portano direttamente alla 1.2.5: ne basta una. La guida distingue anche le varianti della camera 1.04 e le due edizioni 1.2.2; 1.01–1.03 hanno solo ingressi inglesi verificati. Cheat, emulatore e BIOS non servono per applicare la patch; per giocare occorre configurare il proprio emulatore o flashcart.

**Compatibilità:** i salvataggi esistenti vengono importati. Gli slot aggiuntivi della Borsa usano un’estensione del salvataggio: tornando a una ROM vecchia, gli oggetti negli slot extra non sono disponibili; salvando con quella ROM non si recuperano automaticamente al ritorno. Carica il salvataggio normale del gioco, non un savestate precedente. L’intestazione è invariata dalla 1.2, ma importa il catalogo aggiornato per le correzioni. Tutti i codici sono spenti di default.

**Per chi sviluppa:** i sorgenti, gli strumenti e i test stanno in [`source/`](source/README.md). Il manutentore e gli assistenti lavorano **solo su `main`, senza creare branch o pull request**, anche in tutte le chat future: la regola permanente è in [AGENTS.md](AGENTS.md). Le modifiche si verificano e si pubblicano direttamente lì; la ROM si costruisce sulla propria macchina, con il proprio file di gioco, mai su GitHub. L'unico ingresso è la **HeartGold originale** della propria lingua: il primo stadio della costruzione ne ricava la base 1.1 applicando una patch pubblica di sole differenze, quindi non serve nessuna ROM intermedia e nessuna ROM viene distribuita.

**Crediti:** basato su *Sacred Gold* di **Drayano**, continuazione di **Sacred Gold Plus** con credito alla community originale. Sviluppato da un appassionato, con contributi della community.

**Licenza:** strumenti di questo progetto sotto [GPL-3.0-or-later](LICENSE); Pokémon, il gioco originale e i contributi di terzi restano dei rispettivi proprietari — crediti completi in `Come-installare-1.2.5-IT.pdf` nel pacchetto.
