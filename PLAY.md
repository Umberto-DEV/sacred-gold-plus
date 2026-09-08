# How to play

## 1. Choose your version

Use the [four download links on the home page](README.md#download-104). IT means Italian; US means English. Normal Angle uses the original camera settings, while New Angle keeps the wider Sacred Gold Plus view. The language and camera choices do not change the story or battles.

Each ZIP follows the original package layout. Open **Readme + Changelog.txt** first, use the single `.xdelta` patch, and consult **Game Info + Learnset Changes.txt** and **Extras** when needed. **FILE-CHECKS.txt** identifies the exact game files. On macOS, Finder can open ZIP files; **The Unarchiver extracts archives but does not apply a game patch**.

Preview 2 updates the download layout and documentation. If you already use the matching Preview 1 game, you do not need to patch it again: the resulting ROM is identical.

## 2. Prepare the required game

The input for every 1.04 download is **Sacred Gold Plus 1.03 in English**. An Italian 1.04 patch turns that specific English game into the Italian version. Do not apply it directly to Italian HeartGold or to an unknown modified game.

If you are starting from HeartGold, follow the [original author's 1.03 release instructions](https://www.reddit.com/r/PokemonROMhacks/comments/1m69jrj/sacred_gold_plus_fairy_type_full_implementation/) first. The author specifies a clean US HeartGold input. Supply your own lawfully obtained game files; this project does not provide ROMs.

<details>
<summary>Check that your input is the right version</summary>

The required 1.03 file is 126,979,552 bytes. Its SHA-256 fingerprint is:

`78b198fbad961970ef8563587fb2278ee957e6297589a847dbe78f73d12cc0c1`

On macOS, run `shasum -a 256` followed by a space and drag the file into Terminal. On Windows PowerShell, use `Get-FileHash -Algorithm SHA256` followed by the quoted file path. Compare the complete result above. A matching name is not enough. If it differs, stop and keep your current game.

</details>

## 3. Apply the patch

1. Copy your current game and its normal save to a separate backup folder.
2. Open [Rom Patcher JS](https://www.marcrobledo.com/RomPatcher.js/), or use [Delta Patcher](https://github.com/marco-calautti/DeltaPatcher/releases).
3. Select the matching **1.03 English game** as the ROM/original file. Select the extracted **1.04 `.xdelta`** as the patch file. Keep checksum validation enabled.
4. Apply the patch and save the result as a **new file**. Keep the original and backup. If the patcher reports a mismatch, stop; do not force it.
5. Check the output fingerprint against the `FILE-CHECKS.txt` in your download, then open the new game in your emulator.

All four packages update directly from 1.03. Choose one; do not apply the four patches one after another. To change camera or language later, create a fresh result from the same preserved 1.03 input. A 1.04 game is not an accepted input to these patches.

## 4. Continue your save

Use the emulator's normal save import or documented save-folder method. Many emulators associate the save with the game's filename, so preserve that association or explicitly import the save. Start the game normally, without loading an old save state.

A limited English-to-Italian save migration and save/restart checks have passed. This is not a guarantee for every playthrough, trading feature or late-game event. Existing trainer names, Pokémon nicknames and origin-language data remain as saved; translating the menus does not rewrite them.

Check your location, party and bag, play a short section, save normally, close the game and reopen it. Keep cheats off during this check. If something is wrong, restore **both** the previous game and the untouched backup save. Never overwrite your only good backup with a test save.

## Problems and updates

Check [known limits](CHANGELOG.md#known-limits) before reporting a problem. Use [Issues](https://github.com/Umberto-DEV/sacred-gold-plus/issues/new/choose) for a reproducible bug and [Discussions](https://github.com/Umberto-DEV/sacred-gold-plus/discussions) for help.

Future releases will state their accepted input and save-compatibility checks. Updates are manual for now. These downloads do not update melonDS or include an emulator APK. Update your emulator through its official channel.
