# How to play

## 1. Choose your version

Use the [four download links on the home page](README.md#download-104). IT means Italian; US means English. Normal Angle uses the original camera settings, while New Angle keeps the wider Sacred Gold Plus view. The language and camera choices do not change the story or battles.

Choose **one ZIP** for the language and camera you want. Each ZIP has a simple layout:

| File or folder | What it is for |
| --- | --- |
| **README.txt** | Start here: installation and saves. |
| **Install-or-update.html** | Open this in your browser to install or update the selected variant. |
| **Manual** | The original gameplay references, **Game Guide.txt**, and **Project Notes.txt** with file checks, changes and credits. |
| **Cheats** | Seven optional codes in the selected language, in desktop MCH and Android XML formats. |
| **LICENSE** | Terms for this project's original tools; third-party rights are explained in the credits. |

Extract the ZIP with your usual archive app. **The Unarchiver extracts the ZIP; it does not install the game.** The HTML installer works locally in your browser, including offline: no program installation, ROM upload or network connection is needed to process your game. The ZIP and HTML are not playable games.

## 2. Choose your game file

The installer recognizes the exact supported versions of **unmodified US Pokémon HeartGold** and **English Sacred Gold Plus 1.01, 1.02 and 1.03**. Select your own `.nds` file, then start the check to identify its version and choose the matching update automatically. No earlier patch or sequence of patches is needed. The result includes the earlier Sacred Gold and Plus changes retained in 1.04, together with this continuation's fixes.

IT means the resulting game is Italian; it does not require Italian HeartGold. Italian HeartGold and unknown or customized ROMs are not supported inputs. A familiar filename is not sufficient: recognition uses the complete file fingerprint. Supply your own lawfully obtained game file; this project does not provide ROMs.

<details>
<summary>Exact versions and file checks</summary>

The supported fingerprints and sizes are listed under `sources` in the [release manifest](patches/manifest.json). The unmodified US HeartGold input is 134,217,728 bytes with SHA-256 `65f02a56842b75aa92d775d56d657a56fe3fa993550b04dc20704ab82d760105`. Each Plus version also has its own exact fingerprint; an unknown modification to one of those versions is not accepted.

The installer performs recognition for you. For a manual check on macOS, run `shasum -a 256` followed by a space and drag the file into Terminal. On Windows PowerShell, use `Get-FileHash -Algorithm SHA256` followed by the quoted file path. Compare the complete fingerprint with the manifest.

</details>

## 3. Install or update

1. Copy your current game and its normal save to a separate backup folder.
2. Open the extracted **Install-or-update.html** in a modern browser that can open local HTML files and save downloads.
3. Check the output language and camera in the installer heading, then select your own `.nds` game. The variant is fixed by the ZIP you chose; selecting a file does not start processing.
4. Click **Check and create game** (**Controlla e crea il gioco** in Italian). The installer checks the file, selects the matching update and verifies the result. Keep the page open until it finishes.
5. Click **Download the verified game** (**Scarica il gioco verificato** in Italian) to save a **new `.nds` file**. Keep the suggested name, for example **Sacred Gold Plus - New Angle - IT.nds**, which matches the supplied desktop cheat filename. Keep the original and backup, then open the downloaded game in your Nintendo DS emulator.

If your file already matches the selected 1.04 variant, running the check reports that it is already current; no new download is offered. Unknown files are refused; do not force them through another route. If your browser cannot open the HTML or save the result, use a browser or computer that supports local files and downloads. Android browsers and file managers can handle local HTML differently; universal mobile compatibility has not been established.

| What you want to do | How to do it |
| --- | --- |
| Start playing 1.04 | Select the supported unmodified US HeartGold file in your chosen installer. |
| Update English Plus 1.01, 1.02 or 1.03 | Select the recognized Plus file directly, then test a copy of your normal save as described below. |
| Change Normal Angle ↔ New Angle | Open the other variant's installer and select a preserved supported HeartGold or Plus input. Test a copy of your normal save. If the old angle initially remains, enter and leave a building. |
| Change English ↔ Italian | Open the desired language's installer and select a preserved supported HeartGold or Plus input. Test a copy of your normal save using the steps below. |
| Keep using the same 1.04 variant | Select it and click the check button to see whether it is already current. The four game outputs are unchanged from the earlier 1.04 packages. |

A different 1.04 variant is not an update source for this release. To change variants, use one of the supported earlier inputs above. The older Preview 1 and Preview 2 downloads used a single delta from Plus 1.03; their historical instructions apply only to those older packages.

<details>
<summary>Advanced: apply a delta manually</summary>

The public repository also provides the 16 source-to-target deltas listed in [patches/manifest.json](patches/manifest.json). Match your full input fingerprint to a source, choose the route for the desired target, verify the patch fingerprint and apply it with a compatible xdelta patcher. Files follow `patches/from-{source_id}-to-{target_id}.xdelta`. Keep validation enabled and compare the complete output fingerprint and size with the target in the manifest. The HTML installer performs this selection for the normal installation path.

</details>

## 4. Continue your save

Save from the game's own menu before updating. Use the emulator's normal save import or documented save-folder method to associate a **copy** with the new game. Many emulators use matching names: for example, **Sacred Gold Plus - New Angle - IT.nds** and **Sacred Gold Plus - New Angle - IT.sav** in the configured save folder. The supplied desktop cheat file is **Sacred Gold Plus - New Angle - IT.mch**. Use the corresponding Normal Angle or US name for another variant. Rename only a copy. If Continue is missing, check the name and folder before starting a new game.

Start the updated game from its title screen and choose Continue. **Do not load a save state from the previous game version.** Save states are the emulator's quick snapshots; they are different from the normal save created by the game.

A limited English-to-Italian save migration and save/restart checks have passed. This is not a guarantee for every playthrough, trading feature or late-game event. Existing trainer names, Pokémon nicknames and origin-language data remain as saved; translating the menus does not rewrite them.

Check your location, party and bag, play a short section, save normally, close the game and reopen it. Keep cheats off during this check. If something is wrong, restore **both** the previous game and the untouched backup save. Never overwrite your only good backup with a test save.

## Optional cheats

The **Cheats** folder includes seven codes with names and descriptions in your download's language. They start disabled. Read each description, keep a backup, and try one at a time on a copied save. The selected codes have bounded real-core checks; import support does not prove every effect in every situation, and switching a code off cannot undo a change already saved.

| App | File and instructions |
| --- | --- |
| **melonDS desktop 1.1** | Use the `.mch` file. Give it the same base filename as your resulting `.nds` and place it in the configured cheat folder. The default association follows the game's filename. Open the cheat editor to select a code only when you want to use it. |
| **melonDS Android 2.0.1** | Use the `.xml` file. Open **Settings → Cheats → Import cheats**, select it, then browse the codes under **Pause → Cheats** while playing. This version imports XML, not MCH. |

These formats contain the same selection; you only use the one your app needs. The Android file identifies the selected language and camera variant. Import in 2.0.1 replaces a database with the same name; behavior can differ in development builds, so keep a copy of any existing cheat database. Do not rename MCH to XML or vice versa.

For **RetroArch with melonDS DS**, follow its [save and cheat documentation](https://docs.libretro.com/library/melonds_ds/). That core uses `.srm` cartridge saves and a separate cheat workflow; the bundled MCH/XML files are not interchangeable RetroArch imports. No new RetroArch compatibility test is claimed here.

Format references: [melonDS desktop 1.1](https://github.com/melonDS-emu/melonDS/blob/1.1/src/frontend/qt_sdl/EmuInstance.cpp#L797), [Android 2.0.1 importer](https://github.com/rafaelvcaetano/melonDS-android/blob/2.0.1/app/src/main/java/me/magnum/melonds/common/workers/CheatImportWorker.kt). On Android, the [save location can differ when launching through another frontend](https://github.com/rafaelvcaetano/melonDS-android#info-regarding-save-files); check the app's actual setting.

## Problems and updates

Check [known limits](CHANGELOG.md#known-limits) before reporting a problem. Use [Issues](https://github.com/Umberto-DEV/sacred-gold-plus/issues/new/choose) for a reproducible bug and [Discussions](https://github.com/Umberto-DEV/sacred-gold-plus/discussions) for help.

For a future release, download its new installer. Each version will list the exact inputs and update routes it has tested, so the installer can choose among those routes automatically. The current installer does not fetch future releases or accept every future or modified ROM. Future save compatibility is not certified by these checks. These downloads do not update melonDS or include an emulator APK; update your emulator through its official channel.
