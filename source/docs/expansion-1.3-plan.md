# Native training and field guides — implementation plan

Goal: build a private successor to 1.2.5 with player-controlled IV/EV services,
timed Day Care, a native field-guide application and coherent HGSS menus.
The maintainer approved implementation on 27 October 2026. This document is
an execution record, not a claim that the features already ship.

Architecture: preserve the reproducible 1.2.5 builder; apply guarded successor
stages to a verified 1.2.5 image. Allocate new native code once, below the existing
reserve. Keep native Pokémon, inventory and save accessors. Store new settings
and course metadata separately from existing Plus and expanded-Bag records.

Tech stack: Python/ndspy build tooling, freestanding ARMv5TE Thumb C/assembly,
native HGSS windows and field application lifecycle, host and Unicorn tests,
headless melonDS raw-save testing.

Spec: the approved requirements and decisions below. Exact native addresses
must be verified against both supported ROMs before their implementation task.

## Global constraints

- Work on `main`; no branches, worktrees or pull requests.
- Preserve published 1.2.5 bytes and its reproducible builder. Work on private copies.
- Keep every existing public RAM address, item ID and save structure stable.
- Preserve old saves, progress, Pokémon, inventory and Plus settings. No reset.
- New raw-save data must have a version, checksum, save-generation binding and
  crash-safe selection. Missing records mean defaults; invalid records cannot
  overwrite valid native data.
- EN and IT have the same behavior. Guides and player-facing service text are localized.
- Native game assets are read from the user's input at build time, never committed.
- Never weaken a preimage check or relabel skipped tests as passing coverage.
- New code requires meaningful behavioral tests. Runtime and raw-save coverage
  are separate claims from host/Unicorn tests.

## Approved behavior and implementation decisions

IV service: a consultant at a PokéMart accepts Silver Bottle Caps for one IV and
Gold Bottle Caps for all six. Max means 31, not an increment. Advanced selection
can set an individual IV between 0 and 31. Show before/after and confirm cost;
cancel, eggs, insufficient payment and unchanged values consume nothing. Changes
are actual IVs, so explain effects on breeding and Hidden Power.

EV service: the Day Care offers free resetting and paid targeted training. Classic
allows 252 per stat and 510 total. Unlimited allows 252 in all six stats and
requires an explicit imbalance warning. Never silently reduce existing EVs when
changing mode. Stat order in the UI is HP, Attack, Defense, Sp. Atk, Sp. Def, Speed.

Timed courses: one level per two hours, with selectable emulator RTC and active
play-time clocks. RTC is the default requested most recently. Clock edits and
fast-forward are permitted. Keep breeding independent of training time and protect
the current moveset. EV courses use player-selected targets; the initial pacing
decision is 32 EV per hour. Complete at the selected target, with no hidden overflow.
Remote status reports levels, EVs and remaining time through the existing Pokégear
Day Care contact or the guide application.

Caps economy: buy silver after the first badge and gold after the League. Default
prices are 10,000 / 50,000. Johto Gym first wins give two silver; Kanto gives three.
First League completion gives four silver and two gold; repeat completions give
four silver and one gold. Eighth and sixteenth badge milestones give one gold;
first Red victory gives three gold. Existing saves can claim earned one-time
milestones once. Add optional Game Corner exchange only after verifying its UI
and currency. Reward grants must be atomic and survive full bags without loss.

Guide application: a new Guide / Guides button occupies the empty bottom-screen
field-menu slot, outside Plus options. Categories lead to paged lists and detail
pages: evolutions, important items/TMs, special Pokémon/events. Details distinguish
prerequisites and steps and link referenced items. Use actual built evolution and
move tables; reconcile old PDF prose with Plus event scripts before publication.
Use native HGSS fonts, windows, sounds and navigation, including touch and buttons.

Plus UI: retain controls and settings while matching native layout, selection,
spacing and visual feedback. Redux inspiration means purposeful teams and move
coverage, not universal level inflation or an unexplained copy of another hack.
Inspect actual existing teams before selecting changes; preserve accessible counters.

Caught icon: identify a reproducible defect before changing behavior. Do not infer
Pokédex state from current box membership or alter save flags to hide a rendering bug.

## Task 1 — verified baseline and native space

- [x] Check clean `main`; duplicate EN/IT 1.2.5 privately and verify hashes.
- [x] Install requested REA and Impeccable skills from pinned revisions.
- [x] Record the baseline test result and distinguish environment failures.
- [x] Add a successor builder with exact input hashes and transactional output.
- [x] Test relocation on synthetic NDS data before implementing it.
- [x] Allocate the new region in a separate successor reserve manifest, preserving
  the old manifest used for 1.2.5 verification. Verify file identities and RAM sections.
- [x] Cold boot both languages and verify reserve/heap canaries before other features.

## Task 2 — training rules and persistence

- [x] Implement shared C rules for IV edits, EV allocation, caps costs and timers.
- [x] Cover rejected transactions, 510/1512 boundaries, 0/31 IVs, timer rollover,
  backwards clocks, target completion and mode changes without data loss.
- [x] Audit unused item IDs, save sectors and all EV applicability/mutation paths.
- [x] Implement and test the additional save journal with interrupted-write cases.
- [x] Connect native setters and recalculation; preserve species, PID, moves and HP state.

## Task 3 — NPC services, courses and rewards

- [x] Add the cap consultant and Day Care service via verified map/script hooks.
- [x] Add native service UI, confirmation, target choice and result feedback.
- [x] Decouple timed experience from the existing egg counter; handle two deposits,
  withdrawal compaction, save/reload and remote status.
- [x] Implement purchases and first/repeat milestone rewards with full-bag handling.
- [x] Verify all entry points in both languages using raw-save copies.

## Task 4 — field guide and Plus visual integration

- [x] Confirm field-menu overlay hooks, empty-slot geometry and app lifecycle.
- [x] Generate indexed guide data from the player's ROM; write original EN/IT
  event instructions only after verifying prerequisites and locations.
- [x] Implement native category/list/detail navigation and item cross references.
- [x] Integrate the Guide button and restyle Plus without changing existing settings.
- [x] Inspect native screenshots at 256×192 and exercise touch, buttons and return.

## Task 5 — caught icon and purposeful difficulty

- [x] Trace and reproduce the caught-icon report, then test and fix the root cause.
- [x] Research Redux primary documentation; inventory current boss teams and available
  counters at each milestone. Record concrete team changes and their rationale.
- [x] Integrate reviewed trainer changes with a clearly identified difficulty choice.

## Task 6 — integration and compatibility

- [x] Review each completed implementation task for requirements and code quality.
- [x] Run Class A and the applicable native/ROM tests with explicit coverage counts.
- [x] EN/IT: old saves without Plus, with Plus, and with extended Bag: normal Continue,
  in-game save, cold restart, compare progress/Pokémon/inventory/settings.
- [x] Review diffs and `git diff --check`; register public source files and run the
  public-file check when staging is appropriate. No publication in this task.
- [x] Deliver private playable candidates and an accurate validation/limitations record.

## Review focus

Atomic Pokémon/payment changes; native encrypted-data access; save-generation
selection; no accidental EV truncation; native heap ownership; overlay lifetimes;
touch boundaries and language overflow; consistency between guide text and scripts;
honest distinction between observed runtime evidence and static inference.

## Current evidence and remaining gates

The baseline suite passed outside the filesystem sandbox: 457 Class A tests
executed, 50 skipped; four Class B tests executed, 114 skipped. The initial
sandbox failures concerned local sockets and Unicorn JIT permissions. They were
rerun without changing assertions. The successor-wide run passed: 589 executed and 164 explicitly skipped; all new suites ran without skips.

The core rules and journal passed 31 tests and independent review. The native
adapter passed live EN/IT service tests and independent review; review
found and corrected whole-sector admission, delayed League reward accounting,
boxed-data checksum admission and phone time-width issues. These corrections
are included in the final composed candidates and seven-case save matrix.

The Guide now has 429 entries across four categories, including the new services.
Its EN/IT runtime campaigns completed 23 opens and closes per language, including
the fourth category and a Cap link, with no retained owned allocations, intact
guards, unchanged raw SRAM and unchanged observed save arrays/settings. The
initial first-run Plus setup prompt was completed before measuring these runs.
The Plus asynchronous-preview fix passed independent review and native EN/IT
rapid-input tests. Both title screens display the development version.

Seven old-save cases passed Continue, native SAVE and cold restart on the final
composed candidates: plain EN/IT, configured EN/IT, expanded Bag EN/IT and advanced
IT. Observed state included party, boxes, inventory, progression, Pokédex, Day Care,
Plus settings and expanded Bag records. Active IV transactions and timed Day Care courses also passed normal save and
cold restart in both languages, including projected growth and exact payment.

The trainer caught-indicator change passed 2,112 actual ARM dispatcher cases. A
real trainer battle against a previously caught Dragonair also shows the icon
in EN/IT while 1.2.5 hides it; native Pokédex and input SRAM remained unchanged.
Test setup used the game's warp routine and temporarily rearmed one trainer's
defeated flag, with no save or Pokémon/Dex edit. The intermittent wild report
remains unreproduced and is not claimed fixed.

Strategic teams passed three core tests and 672 actual ARM comparisons, plus
independent review. Whole-adventure balance remains a playtesting limitation.
No release has been published. Exact final hashes, input setup, test receipts
and bounded limitations are recorded in [validation-1.3-dev.md](validation-1.3-dev.md).
