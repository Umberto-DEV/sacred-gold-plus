# What's next

## Support 1.04

The immediate priority is to investigate player reports, review the Italian wording in context and protect existing saves. Follow-up corrections will receive their own release notes and clearly identified downloads.

## 1.05 — priorities, not a release promise

This is the current shortlist of candidates. They are not all confirmed for the same release.

- **1.05:** measured performance improvements in cities, remaining bug fixes, completion of the EV/IV stat display and in-game guide prototypes, English and Italian polish, and an initial scaling improvement that preserves the original graphics at 1×.
- **Later releases:** an optional difficulty mode with smarter opponents and more demanding training; additional languages and a possible in-game language selector; Gen 5-inspired Pokémon battle animations; broader graphical improvements; and new areas and events.
- **Quality across all releases:** save preservation, Nintendo DS compatibility, repeatable tests, simple instructions, and patches that check the exact starting game file.

EVs and IVs are the training and individual values behind a Pokémon's stats. The proposed display would make that information easier to read in the game. The guide would explain the hack's changes and options without requiring a separate document.

### Work behind the shortlist

| Area | Intended work |
| --- | --- |
| English and Italian | Review wording, layout, names and remaining Pokédex/UI limitations in context. |
| Bug fixes | Investigate reproducible battle, menu and event problems, with a clear check before and after each fix. |
| Performance | Investigate slow scenes and keep optimizations only when measurements show a benefit without breaking the game. |
| Quality of life | Explore clearer stat information, including EV/IV displays, and useful conveniences that fit the game. |
| Guided introduction | Explain the hack's changes and available options inside the game. |
| Graphics investigation | Identify elements that lose detail when the emulator's internal resolution increases. Preserve the current art and 1× appearance, and keep overworld characters and Pokémon unchanged. Renderer fixes belong in melonDS separately. |

These are candidates for 1.05, not promises that every item will ship together. Existing local prototypes still need integration and wider testing. There is no release date yet.

## Longer-term wishlist

- Optional harder battles with stronger tactics and more demanding training. Existing saves default to Normal, preserving the current Plus difficulty.
- More complete translations: Spanish, French, German, Japanese and Korean are candidates, depending on font support, reviewers and tests.
- Investigate an in-game language choice; separate patches remain an alternative.
- Generation 5-style Pokémon battle animations, after a working DS prototype demonstrates feasibility and acceptable performance.
- Extend graphical improvements that pass the initial tests without changing the art direction.
- Review existing Johto/Kanto content before proposing new areas, events or story additions.

These ideas require their own small proposals and compatibility checks. The game remains a Nintendo DS project; code from hacks on other platforms cannot simply be applied to it.

## How a change reaches players

Agree on one contribution, reproduce or define its expected behaviour, test it, review the source changes and check the combined candidate. A merged PR and a downloadable game release are separate steps. Public automated checks use shareable inputs; save compatibility, language quality and gameplay also need appropriate in-game review.

Each release will state its accepted game inputs, output language, file fingerprints, tested update routes and known limits. **The current 1.04 HTML installers recognize the supported US HeartGold and Plus 1.01, 1.02 and 1.03 files, then select the matching route automatically.** IT and US name the output language. The earlier Sacred Gold and Plus changes retained in 1.04 are included; no older patches are needed. [Installation details](PLAY.md). Future installers will use their own versioned, tested routes; current checks do not certify arbitrary modified ROMs, future versions or future save compatibility.

To help, [start a discussion](https://github.com/Umberto-DEV/sacred-gold-plus/discussions) about one change, then agree on a small testable contribution. A language will appear in Downloads only when an actual build is available and its testing status is clear.

This project is maintained by one fan. Help with testing, translation, code, documentation or manually created artwork is welcome. If new areas or artwork are added, the plan is to create their visuals by hand with contributing artists. AI assistance is described in the [credits](CREDITS.md).
