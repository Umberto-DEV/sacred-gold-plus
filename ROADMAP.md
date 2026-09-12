# What's next

## Support 1.2

The immediate priority is to finish testing 1.2 on real Nintendo DS hardware, investigate player reports and protect existing saves. Follow-up corrections will receive their own release notes and clearly identified downloads.

## Beyond 1.2

This is the current shortlist of candidates. They are not all confirmed for the same release, and none of them changes what already shipped in 1.2.

### 1.2b

- **Raise the level cap to 150.** Each stat would grow normally up to its own ceiling (for example 999 HP) and then stop there on its own, while other stats keep climbing to 150 or their own ceiling — not one shared stop for the whole Pokémon.
- **A boost past level 100** for Pokémon that reach the current cap, as part of the same difficulty option.
- Both depend on in-game confirmation that the numbers feel right to play with, not only that they compute correctly.

### 1.3

- Ask which online server to use from inside the Pokémon Center clerk's own dialogue, instead of only from the options page.
- More complete translations: German, French, Spanish, Japanese and Korean are candidates, depending on font support, reviewers and tests.
- Investigate an in-game language choice; separate patches remain an alternative.

### Abandoned

- **Porting Generation 5's battle animations.** Measured and set aside: Gen 5's battle sprites are animated as jointed puppets — head, limbs and tail moving independently — redrawn at a real rate of about 10 frames per second, and that combination is exactly what gives Gen 5 battles their soft, blurred look. Bringing that motion style to HGSS's frame-based battlers would need a new animation engine and would still reproduce the same blur that made the idea appealing, which is a technical contradiction, not a style choice. 1.2's own Animated Pokémon option is what remains useful from this investigation.

### Quality across all releases

Save preservation, Nintendo DS compatibility, repeatable tests, simple instructions, and patches that check the exact starting game file.

### Longer-term wishlist

- Extend graphical improvements that pass the initial tests without changing the art direction. Renderer fixes (for example melonDS' own upscaling) belong in melonDS separately.
- Review existing Johto/Kanto content before proposing new areas, events or story additions.
- Explore clearer stat information and other quality-of-life conveniences that fit the game, including the EV/IV stat display and in-game guide prototypes started for earlier releases.

These ideas require their own small proposals and compatibility checks. The game remains a Nintendo DS project; code from hacks on other platforms cannot simply be applied to it.

## How a change reaches players

Agree on one contribution, reproduce or define its expected behaviour, test it, review the source changes and check the combined candidate. A merged PR and a downloadable game release are separate steps. Public automated checks use shareable inputs; save compatibility, language quality and gameplay also need appropriate in-game review.

Each release will state its accepted game inputs, output language, file fingerprints, tested update routes and known limits. **The 1.2 installation guide recognizes the supported US and Italian HeartGold and Plus 1.01, 1.02, 1.03, 1.04 and 1.1 files, and helps you apply the matching patch.** IT and US name the output language. The earlier Sacred Gold and Plus changes retained through 1.1 are included; no older patches are needed first. [Installation details](PLAY.md). Future releases will use their own versioned, tested inputs; current checks do not certify arbitrary modified ROMs, future versions or future save compatibility.

To help, [start a discussion](https://github.com/Umberto-DEV/sacred-gold-plus/discussions) about one change, then agree on a small testable contribution. A language will appear in Downloads only when an actual build is available and its testing status is clear.

This project is maintained by one fan. Help with testing, translation, code, documentation or manually created artwork is welcome. If new areas or artwork are added, the plan is to create their visuals by hand with contributing artists. AI assistance is described in the [credits](CREDITS.md).
