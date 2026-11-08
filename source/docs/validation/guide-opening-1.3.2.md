# Guide opening correction — 1.3.2

The original 1.3.2 Guide can refuse to open after ordinary native font managers
have been allocated again during a session. Confirmation animates, but the
application closes before presenting the Guide. A cold restart can temporarily
hide the defect. This is independent of save contents and does not require a
new game, cleared settings or a save migration.

## Diagnosis and source correction

A failing Android session retained Scene error 14: font acquisition refused.
Native lazy font initialization sets its access mode and decoder but leaves the
unused direct-cache word uninitialized. The UI incorrectly validated that word
as an active pointer in every other live font. Reused managers contained values
such as `0x06060505` and `0x43484152`, so the check rejected valid lazy fonts.

The corrected font owner checks cache extents and output separation only for
the known direct decoder. Lazy fonts must still have the exact native mode and
decoder; their unused word is never dereferenced. Bridge and Scene admission
accept the same native state. Temporary font ownership snapshots the original
word and restores it on exit. Resource retirement recognizes the exact lazy
tuple without treating its unused word as a live cache. Direct-cache ownership,
glyph/width identities, native allocation checks and alias guards remain active.

Save layouts, identifiers, Pokémon data, Bag extensions and Plus settings are
unchanged. The retired historical Guide image remains untouched.

## Component evidence

New ARM regressions first failed on the previous implementation, then passed
with the correction. They cover lazy residue in the primary and other fonts,
both Scene roles, exact restoration, resource retirement and direct-cache output
protection. Unknown mode/decoder combinations remain rejected. The foreign-font
width-alias test first proves its unmodified tuple is admissible, so its refusal
cannot be satisfied by an unrelated malformed-cache check.

- 66 compiled component tests passed.
- 30 native font/Bridge tests passed with their declared prepared-state seams.
- 6 native Scene-admission tests passed, including both language fixtures.
- The complete lazy acquire/paint/release/resource-retirement regression passed
  with residue pointing inside the resource allocation itself.

The exact original Italian ROM also reproduced the failure in a controlled
host experiment that changed only the unused lazy-cache words to the values
observed in the failing Android session. Its Scene again closed with error 14.
That diagnostic uses explicit RAM writes; it is separate from normal-input
game/save acceptance. A cold, unmodified run of the same original ROM opened
the Guide, which explains why a successful restart alone does not exclude this
regression.

## Exact successor candidates

All five languages were compiled and tested separately. EN/IT use the guarded
shared composer; FR/ES/DE compose their presentation around the exact corrected
English core and run their independent regional readbacks.

| Language | Bytes | SHA-256 |
| --- | ---: | --- |
| EN | 152786844 | `2e30d6960bb059615fca7527700d86f8282e82ccbe99bf62e22f027453dc3d3d` |
| IT | 159029760 | `13ebac02bdea3036511773587e6603ce6834e25f4b13d1a4662c3e954bfd5d4a` |
| FR | 162560728 | `e5e0b9cfe2596aa26e9043160d7b73b95d1346803c32c53411a86670a8709a0a` |
| ES | 162490072 | `015f137cff348d5028fdee91b7f640ffd36215ef836fb8dfa9d0b7db6d82b32c` |
| DE | 162932492 | `cc64522cf898965a6c677e1dd2e99f876cc9af0f1fd88b7073c8e55259058183` |

Both formal EN/IT outputs match the actually exercised four-word portable
activation derivatives byte for byte. Fresh normal-input Party → R → native PC
proofs reached the expected phase with one opening and zero failures. Regional
receipts bind the same complete English core hash.

After construction, only the stage-zero downloader and its tests changed to
preserve clock/mirror behavior for the single-ZIP delivery. All game/payload
source hashes remained identical. A fresh public-API recompilation/readback of
both exact final ROMs against the current sources reproduced their original
composition and activation results. Original construction receipts remain
unchanged; the delivery-only source delta and current-source replay are separate
records.

## Save and localized UI acceptance

Eight case/language pairs over six unique original raw fixtures passed:

| Fixture category | Languages | Verified sequence |
| --- | --- | --- |
| Legacy save without Plus data | EN, IT | Continue → native SAVE → process exit → cold Continue → UI |
| Populated save with existing Plus settings and Bag extensions | EN, IT | Same sequence, complete protected-data comparison |
| Additional current populated save | IT | Same sequence on a fresh read-only backup copy |
| Matching original regional save | FR, ES, DE | Same sequence and localized first-load Plus handling |

Every case opened, closed and reopened Options and a readable Guide topic using
normal inputs. Both screens were inspected. After-SAVE, after-cold and after-UI
raw exports are byte-identical in every case. Original fixtures and read-only
input copies remained unchanged. Party and boxed Pokémon, inventory/registered
items, expanded slots, existing Plus settings, progress flags, Pokédex, Day Care
and applicable journal state were preserved.

The populated fixture's first strict storage comparison failed on the native
`boxModifiedFlag` reset. The complete storage array differs only at two bytes
within its four-byte bookkeeping field (`0x00020006` → zero), as assigned by the
native reset on Continue. Every other storage byte, including names, wallpapers,
current box, empty slots and occupied Pokémon, remains exact. Initial strict
failures and their source-attributed refinement are retained; no broad storage
mask is applied.

The FR/ES fixtures contain one starter and five Potions; DE has an empty
party/Bag. Regional boxes/Day Care are empty and have no prior Plus settings or
populated extension slots. Configured/populated coverage comes from the EN/IT
cases. Host execution uses an interpreter/software renderer, generated firmware,
FreeBIOS and fixed initial RTC. These are bounded save/UI checks, without
universal save compatibility, a full topic traversal, a New Game campaign or a
full playthrough claim. Historical acceptance keeps its original scope in
[localization-1.3.2.md](localization-1.3.2.md).

## Italian installation and maintainer check

Only the Italian successor was installed on the connected Android installation,
in its existing filename/path and custom emulator. Fresh installed-ROM/save
backups and exact-successor host SAVE/cold testing preceded replacement. Complete
readback confirmed the installed Italian ROM hash above, the unchanged personal
raw save and the unchanged emulator APK. No test save was copied onto the device.

The maintainer then reported that both Options and Guide pass on the updated
installation. This is a maintainer-reported Italian entry check, separate from
the five-language host evidence. It establishes no handheld timing, exhaustive
navigation, physical native-SAVE cycle or physical coverage of other languages.

## Single package

[Package verification](package-1.3.2-corrected.md) records all 175 independently
decoded routes, the preserved documents/cheats/developer inputs and the one
`Sacred-Gold-Plus-1.3.2.zip` download. File reconstruction, runtime acceptance,
physical installation and hosted source CI remain separately evidenced gates.
