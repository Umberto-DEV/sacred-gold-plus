# How to play

## 1. Choose your version

Use the [four download links on the home page](README.md#download-104). IT means Italian; US means English. Normal Angle uses the original camera settings, while New Angle keeps the wider Sacred Gold Plus view. The language and camera choices do not change the story or battles.

Each ZIP has a simple layout:

| File or folder | What it is for |
| --- | --- |
| **README.txt** | Start here: installation and saves. |
| **Sacred-Gold-Plus-[angle]-[language].xdelta** | The single patch to apply. |
| **Manual** | The original gameplay references, **Game Guide.txt**, and **Project Notes.txt** with file checks, changes and credits. |
| **Cheats** | Seven optional codes in the selected language, in desktop MCH and Android XML formats. |
| **LICENSE** | Terms for this project's original tools; third-party rights are explained in the credits. |

Open the ZIP with your usual archive app. **The Unarchiver extracts the ZIP; it does not apply the game patch.** A patcher combines the `.xdelta` with the required game to make a new `.nds`. The ZIP and `.xdelta` cannot be played directly.

## 2. Prepare the required game

The input for all four current 1.04 downloads is the same **unmodified US Pokémon HeartGold** game identified below. Each cumulative patch includes the earlier Sacred Gold and Plus changes retained in 1.04, plus this continuation's fixes. **Apply just one patch; no earlier Sacred Gold or Plus patch is required.**

IT means the resulting game is Italian; it does not require Italian HeartGold. These patches do not accept Italian HeartGold, Plus 1.03, an existing 1.04 game or another modified game as input. Supply your own lawfully obtained game file; this project does not provide ROMs.

<details>
<summary>Check that your input is the right version</summary>

The required unmodified US HeartGold file is 134,217,728 bytes. Its SHA-256 fingerprint is:

`65f02a56842b75aa92d775d56d657a56fe3fa993550b04dc20704ab82d760105`

On macOS, run `shasum -a 256` followed by a space and drag the file into Terminal. On Windows PowerShell, use `Get-FileHash -Algorithm SHA256` followed by the quoted file path. Compare the complete result above. A matching name is not enough. If it differs, stop and keep your current game.

</details>

## 3. Apply the patch

1. Copy your current game and its normal save to a separate backup folder.
2. Open [Rom Patcher JS](https://www.marcrobledo.com/RomPatcher.js/), or use [Delta Patcher](https://github.com/marco-calautti/DeltaPatcher/releases).
3. Select the matching **unmodified US HeartGold game** as the ROM/original file. Select the extracted **1.04 `.xdelta`** as the patch file. Keep checksum validation enabled.
4. Apply the patch and save the result as a **new file**, using your chosen variant's name, for example **Sacred Gold Plus - New Angle - IT.nds**. This matches the supplied desktop cheat filename. Keep the original and backup. If the patcher reports a mismatch, stop; do not force it.
5. Check the output fingerprint against **Manual/Project Notes.txt** in your download. Open the resulting `.nds` in your Nintendo DS emulator.

All four current packages start directly from the same unmodified US HeartGold file. Choose one; do not apply patches one after another. The older Preview 1 and Preview 2 downloads used Plus 1.03 as input; their historical instructions apply only to those older packages.

| What you want to do | How to do it |
| --- | --- |
| Start playing 1.04 | Apply your chosen patch to the matching unmodified US HeartGold file. |
| Continue a Plus 1.03 save | Build 1.04 from the matching unmodified US HeartGold file, then test a copy of your normal save as described below. Keep your old game and save together for recovery. |
| Change Normal Angle ↔ New Angle | Create a fresh game from your preserved unmodified US HeartGold file with the other patch. Test a copy of your normal save. If the old angle initially remains, enter and leave a building. |
| Change English ↔ Italian | Create a fresh game from your preserved unmodified US HeartGold file with the desired language patch. Test a copy of your normal save using the steps below. |
| Keep using the same 1.04 variant | Check its game fingerprint. This release produces the same four games as the earlier 1.04 packages, so matching players do not need to patch again. |

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

Future releases will state their accepted input and save-compatibility checks. Updates are manual for now. These downloads do not update melonDS or include an emulator APK. Update your emulator through its official channel.
