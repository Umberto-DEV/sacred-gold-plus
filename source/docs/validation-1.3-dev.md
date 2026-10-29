# 1.3 development validation — 28 October 2026

This records the initial v4 checkpoint. The subsequent
[systematic playtest](playtest-1.3-dev.md) records the corrected v5 candidate and
expanded coverage; hashes and observations below remain tied to v4.

These are private development candidates, not a published release. They were
built on `main` from the exact 1.2.5 EN/IT images. Published ZIPs, tags, source
payloads and the `sgp12` build route were not replaced.

| Candidate | Bytes | SHA-256 |
| --- | ---: | --- |
| EN | 137452904 | `2bbf8fcfcfd1b54143663d0c05152e2f52c906c9ffb1953e2e1c48fd1c2386e8` |
| IT | 142977384 | `eddacce1f7151dc395f3cbf7ff94ab90f6c774489dfb5cd5eee3b18a924e49a0` |

Each builder receipt records source and charmap hashes, intermediate hashes,
compiled sizes and final composition checks. Every preexisting FAT file ID is
preserved. Unchanged files, ARM7, banner, trainer/evolution archives and reserve
guards are compared with the input. The final source snapshot matches the
receipt. Runtime evidence is separate from these build checks.

## Automated tests

The full project runner collected 753 tests: **589 executed and passed; 164
skipped**. Class A: 556 executed, 50 skipped. Class B: 33 executed, 114 skipped.
All newly registered 1.3 suites ran without skips, including the actual-ROM
training suite. Historical private-input suites were not silently counted as
executed. Compiler availability was required. Tests ran outside the sandbox
because Unicorn JIT and existing local-socket tests need host facilities.

The full run used the preceding composed checkpoint. Two subsequent resource
corrections were checked independently: two coordinate bytes moved the Day Care
consultant from `(6,7)` to the accessible floor at `(4,9)`; the 18 new phone
messages gained a clearer course-time label and the native final input wait.
Only event archive member302 and text-bank member660 changed. Every original
phone message and the entire ARM9, ARM7, overlay table and all other FAT payloads
remain identical. Native interaction verified the new position and phone wait.
Final raw-save and Guide campaigns below use the exact candidate hashes above.

Meaningful focused coverage includes:

- 31 shared training-rule/journal tests: limits, actual IV choices, rejected
  payments, timers, backward clocks, transitions, record validation and selection.
- 25 actual ARM adapter tests per language, using native Pokémon accessors,
  encryption/checksums, stat recalculation, item gates, battle EV multipliers,
  Bag/money limits, Day Care withdrawal and slot compaction. OS/flash/NARC seams
  and selected formatter calls are mocked; this is not an emulator playthrough.
- Training fault cases cover foreign sectors, both-bank admission, partial first
  ownership writes, torn owned payloads, future formats, generation mismatch,
  valid-sibling recovery and retries without a native commit on failure.
- 2,112 actual ARM caught-indicator dispatcher cases cover both languages,
  historical Pokédex states and native HUD types.
- 672 actual ARM trainer-hook comparisons cover four call sites, seven parties,
  six slots, both difficulties and both languages, preserving registers, flags,
  stack and the original level/RNG path.
- Guide bounds, content links, navigation, allocations, stale-menu ownership and
  installer compartment preservation; Plus context allocation and printer ownership.

## Older raw-save compatibility

Seven cases passed on the final candidates:

| Fixture class | EN | IT |
| --- | --- | --- |
| Older save without Plus records | Pass | Pass |
| Configured Plus settings | Pass | Pass |
| Expanded Bag contents and Plus settings | Pass | Pass |
| Advanced adventure save | — | Pass |

For each case, the same original raw `.sav` was loaded in 1.2.5 and the candidate
through ordinary Continue. The candidate then performed native SAVE and was
cold-restarted from that resulting raw save. No savestate was substituted.
Original fixtures remained byte-identical; exported SRAM after cold restart
matched the newly saved file.

Observed native arrays compared profile/options/coins, party, native Bag,
variables/flags, Pokédex, Day Care and all PC Pokémon. Existing Plus setting bytes
and the 2,380-byte expanded-Bag payload were also compared. A missing Plus header
is initialized by the existing first-save behavior; its magic/version bytes are
recorded separately from the settings rather than mistaken for a regression.
These seven cases establish their stated coverage, not universal compatibility
with every external modification. Training was inactive in this old-save matrix.

## Native interface and battle observations

The final EN/IT candidates each completed **23 Guide opens and closes**, including
touch, buttons, paging, item links, all four categories and return to native
Options/field menus. The 429-entry payloads are 113,212/118,752 bytes. Owned
allocation handles were cleared, guards remained intact, observed save arrays
and settings were unchanged, and raw SRAM stayed byte-identical. Native screenshots
were inspected at DS resolution. The initial Plus setup prompt was completed
before collecting the legacy fixture's baseline.

Plus was separately exercised in both languages with all five context rows,
touch, cancel and apply. Changing Text Speed and immediately opening Plus exposed
an asynchronous-printer race. The corrected code completes only the current
app's owned printer, keeps its contextual text stable and restores the complete
native preview on B/SELECT. A later animated preview still works. Native title
screens in both languages display `1.3 DEV`.

An actual trainer battle against a previously caught Dragonair showed no ball
in 1.2.5 and a ball in both development languages. The native Pokédex flag was
already set in all runs; field Pokédex and input SRAM stayed unchanged. Setup
used the game's map-change function and temporarily rearmed that trainer's
defeated flag, with no save or Pokémon/Dex edit. This is one caught species and
one trainer, not a real uncaught-species or wild encounter campaign.

Four further native battles constructed Bugsy's complete party: old Plus EN,
candidate Plus EN/IT and candidate Normal EN. Only candidate Plus substituted
Scyther's False Swipe with Bug Bite; the other 23 moves and all species/Plus
levels matched. Every Pokémon checksum was valid. Plus was selected through
ordinary Options. The trainer ID was selected at the native factory before
archive reads, without editing Pokémon/Dex data. Party, Pokédex, PC Pokémon and
input SRAM stayed unchanged. This covers construction and battle entry, not a
completed battle, natural Gym progression or all AI choices.

Native service acceptance passed in both languages. Ordinary interaction opens
the Violet and Blackthorn consultants and returns control on cancel. Violet's
map test used a native warp to its floor; arrival/menu/exit preserved party,
inventory, Pokédex, Day Care, PC data and SRAM. Blackthorn's complete IV flow
covered Silver, Gold, a declined edit and exact HP IV of 0. The accepted exact edit
spent one Silver Cap (15 to 14), with no money change; native SAVE and cold restart
retained IVs `[0,31,31,31,31,31]` and 14 Silver Caps.

Day Care campaigns in both languages covered Classic activation, the Unlimited
warning's decline and acceptance, free EV reset, normal deposit, target 64 HP EV
enrollment and both clock selections. Active-course native SAVE created matching
generation 116 journal copies with valid checksums. A new process advanced the
emulator RTC through its own `RTC.SetDateTime` API, without editing game RAM or
Pokémon data. Local status and an actual Pokégear call then showed the projected
Lv55 and 64 HP EVs from a Lv54/0-EV start. The course's final phone page stayed
visible until input, and the original conversation continued afterward.

Ordinary withdrawal charged the native 200 fee and produced Lv55, 64 HP EVs and
the original moves/IVs. Quick training from 64 to 100 HP EVs then cost exactly 3600.
A normal save wrote generation 117 with inactive jobs; another cold restart in
both languages retained Lv55, 100 HP EVs, EXP 165715, original moves/IVs, wallet 203769,
Unlimited policy and empty Day Care. Other party members remained unchanged.
The disposable Day Care fixture was positioned using the game's map-change
function followed by native SAVE; it is separate from the old-save matrix.

Fresh frozen-candidate focused tests also passed: EN 41/41 and IT 25/25, no skips.
Those service candidates and the composed candidates have identical native
training code and the same service resources; final composition was independently
checked. A real two-hour wall-clock wait, complete egg-generation/hatching
campaign and physical power-cut experiment were not performed. Playtime selection
was observed in-game; clock fractions and interruption cases have production-ARM
coverage with explicit seams.

## Review and limits

Independent specification and code reviews passed for space/build composition,
core training, native adapters, Guide, strategic teams and Plus. Review findings
led to fixes for stale Guide ownership, split reserve ownership, active native
text printing, whole-sector training admission, delayed League reward accounting,
boxed-data checksum admission and six-digit phone times. Review is distinct from
the tests and gameplay observations above.

The intermittent missing caught icon in wild encounters remains unreproduced.
The trainer change is an extension of native rendering, not a repair of Pokédex
save flags. Strategic changes are a bounded nine-move pass; a complete adventure
and competitive balance playthrough has not been performed. Optional Game Corner
Cap exchange is not implemented. The Guide uses original instructions based on
verified live tables/scripts; it does not embed or reproduce the bundled PDFs.
