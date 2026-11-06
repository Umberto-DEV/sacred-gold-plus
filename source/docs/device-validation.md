# Physical-device validation evidence

This report preserves the **29 October 2026 V1.3** device campaign used to qualify unchanged components in the current source. At that historical checkpoint V1.3 was a development candidate and 1.2.5 was the published release. For current 1.3.1 identities and acceptance use [UI validation](ui-1.3.1-validation.md); these historical results do not certify a successor.

## Historical ROM identities

| Language | Revision | Bytes | SHA-256 |
| --- | --- | ---: | --- |
| EN | v4 | 147345256 | `179edfb1ca331503f438e98f3afccfb0ab85759bf9ab88fb86c735f5fcefbf90` |
| IT | v4 | 153228136 | `2a2f0b437fca524c18b71b20feb01a1f51351e61c7c897ce73d9b3be1ee3a156` |

Both builds used builder-authenticated 1.2.5 inputs. Receipts retain input/source/reference-tool/stage hashes. Composition and installed-code checks passed; those checks alone are not gameplay evidence. The preceding [Android campaign](android-validation.md) supplies the earlier functional scope.

## Name and version changes

The prior 1.2.5/v3 banner said Pokémon HeartGold in all six DS languages. V4 changes it to **Pokémon Sacred Gold Plus**, preserving icon pixels, palette and publisher line. It recomputes the banner checksum and rejects unexpected format, checksum or starting names. The title label changes from `1.3 DEV` to `V1.3`; Plus headings become `Sacred Gold Plus V1.3` and the first page includes `1/2`. Shiny controls remain intact. The new header measures 137/144 pixels in EN/IT.

Full v3→v4 comparison finds 2,396 changed EN bytes and 2,501 IT bytes, confined to banner, 384 graphical-label bytes and two Plus text areas. Executable/save code and all other resources are identical. Earlier component evidence keeps its original hashes and limits. The full suite reports 37 Class A suites, 809 executed tests and 52 skips, separately from four synthetic Class B tests and 176 Class B skips. Nine focused checks cover banner/checksum/icon/pointer bounds/graphics/text table. Independent review found no identification-diff issue.

## Observed physical run

The configuration was Android 13 ARM64, melonDS Nightly 2.1.5, versionCode 46, Compute renderer, internal resolution 6x and two screens. The test did not replace the APK or graphics configuration.

Separate copies of an older IT save completed Continue → native SAVE → process stop → cold restart on v3 and then v4. Each post-restart export matched its completed SAVE. No old emulator state was loaded. Independent comparison reconstructs all 45 regions without unexpected bytes: six party Pokémon, 248 occupied storage records, identities, moves, EV/IV, abilities, HP/stats, native inventory, expanded Bag, Plus settings, money, progress, flags and Friend Roster are preserved. Native generation advances 198→199; Plus counters 107→108; the prior bank stays intact.

Clock, play time, daily events, follower mood, Pokérus and temporary object changes were individually explained. Opening Plus before V4 SAVE initialized the SHINY_ONLY journal with Classic/defaults without applying a change, matching its existing v3 owner. It created no course/reward. Typhlosion's pre-existing stat-cache discrepancy remained unchanged.

Observed screens include V1.3 title, new Plus header, Classic 1/512 and, on v3, Pro 1/4096 preview cancelled without Apply. Guide opened on v3; touch arrows worked with native L=A. The definitive library name/icon were checked after update.

## Preservation and limits

The IT ROM replaced its predecessor at the same filename/path. The personal `.sav`, prior emulator state and cheat file were preserved; the original save stayed byte-identical. Verified host backups retained the prior ROM. Temporary test files/library entries were removed while preserving other games. Resume through Continue, without loading an older ROM's emulator state.

Coverage is one IT raw save with Plus and expanded Bag, no Day Care Pokémon or active courses. EN has build/measurement/binary comparison here; its gameplay coverage remains the earlier Android campaign. This does not repeat all captures, shiny odds, 493 species or a full playthrough. It is not a performance benchmark, approval of all old cheats or universal freeze/graphics certification. Screenshots, saves and raw audits remain private.
