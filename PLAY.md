# How to play the 1.2 additions

This page covers what changed in **how you play** 1.2: the new in-game options page and its switches. For installing or updating your game file, open the installation guide included in your downloaded ZIP — it has the exact steps, tools and file checks for your platform. [The home page](README.md#download-12) lists the download links and a short summary; [known limits](CHANGELOG.md#known-limits) lists what still needs testing.

## Open the options page: press SELECT

During play — not from the pause/start menu — press **SELECT**. This opens a second page, **Sacred Gold Plus**, on top of the game's own Options menu. The original Options menu is unchanged; the new page is a separate screen reached from it.

Your choices are written into your save file, so they survive closing the emulator and starting again from a full power-off. **A** confirms and saves the page; **B** leaves without writing anything, so a change you back out of is discarded.

## The question at Continue

The first time you press **Continue** on a save that has no Sacred Gold Plus settings yet — for example, a save carried over from 1.1 or an earlier version — the game asks once whether you want to open the page and look at the new switches. Answering either way only affects whether the page opens then; you can still reach it with SELECT at any later time.

## What each switch does, and its default

| Switch | What it does | Default |
| --- | --- | --- |
| **Plus difficulty** | Trainers are tougher, up to the level cap. See the [game guide](GAME-GUIDE.md#sacred-gold-plus-12-additions) for the numbers. | Off |
| **Wild levels** | Wild Pokémon scale up with your progress instead of staying fixed to the zone. | Off |
| **Animated Pokémon** | Pokémon move gently in battle instead of standing still. | Off |
| **Characters** | Limits how many non-player characters can load in one frame, reducing stutter at town/route borders. | Smooth |
| **Online server** | Which of your emulator's three WFC connection slots is used for GTS, battles and trades. Mystery Gift always uses the first slot automatically and ignores this setting. | Original (no slot forced) |

With **Plus difficulty** and **Wild levels** both off, and **Animated Pokémon** off, the game plays byte-identical to 1.1 in those respects — turning 1.2 on does not silently change an existing save. **Characters** ships smooth (on) because it only removes a stutter; you can switch it to Normal to compare.

There is no cheat for any of these settings, and none is needed: they are part of the game itself. Do not look for a "Plus difficulty" or "animated Pokémon" code among the optional cheats — there isn't one, by design.

## The camera indoors

In eight indoor maps the camera is now the closer, native HeartGold framing, with nothing to switch on. Outdoors, the wider Plus camera is unchanged. If you prefer the original HeartGold camera everywhere, turn on the camera cheat instead of the options page — it is a separate, existing toggle, not one of the five switches above. The change is read when you walk into a new map; standing still and flipping the cheat shows nothing until you cross a doorway.

## Online connections

Configure the three WFC connection addresses inside melonDS' own Nintendo Wi-Fi Connection settings, the same way you would for any DS game — 1.2 does not add or manage a server. The **Online server** switch above only tells the game which of your already-configured slots to use for GTS, battles and trades. If the slot you picked is not configured, the game falls back to the first slot that is; if none are configured, it behaves exactly as it did before 1.2.

## Problems and updates

Check [known limits](CHANGELOG.md#known-limits) before reporting a problem. Use [Issues](https://github.com/Umberto-DEV/sacred-gold-plus/issues/new/choose) for a reproducible bug and [Discussions](https://github.com/Umberto-DEV/sacred-gold-plus/discussions) for help. Say which release, language, and which of the switches above were on when something went wrong.
