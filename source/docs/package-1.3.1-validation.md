# Player package verification - 1.3.1

## Freeze-fix packages - 6 November 2026

The current contract is `4b2edbf3648050bedd2287a30f11d3ea1a6e078e195515c731a85a3df69ced32`, targeting EN `50ba570f97655cecc7b11bed06eb7f683283b191c1c21f02e49ad55f90fc7665`
and IT `c63cf9e993cbee9c38949baf9444dda3e365bddb15840aaa08905d9b02afbedb`.
Each of 25 routes per language reconstructs the complete target with both
xdelta3 and the pinned RomPatcher.js decoder: **100/100 outputs match**.
Archive readback passes for both 39-member ZIPs. No ROM, raw save, BIOS,
emulator or unverified legacy cheat catalogue is included. The five original
manual PDFs and trainer reference retain their authenticated bytes and credits.

| Player ZIP | Bytes | SHA-256 |
| --- | ---: | --- |
| Sacred-Gold-Plus-1.3.1-US.zip | 331421095 | `3c72155655fb15f58697c985c66e128cb4e61bc8bb27a2ad2a476a32f05e58c9` |
| Sacred-Gold-Plus-1.3.1-IT.zip | 354448599 | `7d82b678ce11044fb5d74ae4209c166b99c7c7aaf190320e1602b3d764c3c81a` |

The four updated PDFs were generated with ReportLab 4.4.9. All **42 pages**
were rendered and visually inspected; archive copies equal the external PDFs.
Installation documents identify the exact supported starting hashes and the
new finished-game hash. References to 1.2.5 in input routes and historical
comparisons are intentional; original author manuals are not relabelled.

| PDF | Pages | Bytes | SHA-256 |
| --- | ---: | ---: | --- |
| Come-installare-1.3.1-IT.pdf | 12 | 110757 | `46a1dbd9c05ae6023a43d69bfda013f7394e754b1d014e0bcc0ef5a5e4cda03c` |
| How-to-install-1.3.1-EN.pdf | 12 | 110121 | `3d11de3f3b0e43521b0fd7f2c3330d2ffbc05d7c4bfdcd2d4953cb4f47e42c42` |
| Novita-1.3.1-IT.pdf | 9 | 143369 | `bb20a51f22192d11dddaf5ca72eaa706dca8d7873d9deb9631fc144d08e2f42e` |
| Whats-New-1.3.1-EN.pdf | 9 | 143529 | `276cd41b4d6f9e7bbaa6f592da4c5a4c750b1d3478957b9d55a3d051ef4ca9f4` |

Candidate-bound title, party and PC captures were refreshed from the exact
formal EN/IT builds. The [runtime report](ui-1.3.1-validation.md) records fresh
older-save cycles in both languages and the physical Italian copied-save,
battle and in-place installation checks. English physical-device acceptance,
all historical save combinations and a full-game playthrough are not claimed.
File reconstruction does not establish a full-game playthrough, a GitHub
upload or a CI result.

The game-code suite collected 2,988 tests without failures: Class A ran
2,046 of 2,099 with 53 declared skips; Class B ran 581 of 889 with 308 declared
skips. All 32 distribution tests were rerun against the final contract after
the packaging/documentation updates made during that long run. The new
bootstrap's three CLI gates and exact EN/IT V4 rebuilds are separate evidence.

The receipts below are historical and do not identify the current packages.


> **Private draft; do not publish these artifacts.** The live contract has
> SHA-256
> `ffef7552a6532d6b4ea8d68706b868109458f13ecb0c4d66a9216f6c148e4070`
> and targets EN `02cccfbf…bf0af` (152,786,376 bytes) / IT
> `35d459e3…088f4` (159,029,292 bytes), including `legendary-scene-version`.
> The package is **not publishable until the exact current IT successor is
> validated on the maintainer's physical device** and the maintainer explicitly
> approves publication. The 31 October receipt remains below as historical
> evidence and does not identify the current draft.

## Current private draft - 5 November 2026

The current targets were rebuilt into a new offline player-package draft. Each
of the 25 source routes per language was decoded with both xdelta3 and the
pinned RomPatcher.js implementation: 100 reconstructed outputs matched the
complete target hash and size. Both ZIPs pass checksum verification and archive
readback, contain 39 members, and contain no ROM, save, BIOS or emulator.

| ZIP | Byte | SHA-256 |
| --- | ---: | --- |
| Sacred-Gold-Plus-1.3.1-US.zip | 331419164 | `99f3e7d310c1ec0f3dda143af45aabe02fce5798f5722c44af3321ad18f3d23e` |
| Sacred-Gold-Plus-1.3.1-IT.zip | 354446308 | `fbe6109c0bc504ff728e33b2c6bf58283f8dc31410d4254ff88fb601b3dd204d` |

The four current PDFs were regenerated with reportlab 4.4.9 and all 40 pages
were rendered and visually reviewed. Installation guides retain the genuine
1.2.5 route as an updater input while identifying the finished game as 1.3.1;
that historical input must not be relabelled as a 1.3.1 source.

| PDF | Byte | SHA-256 |
| --- | ---: | --- |
| Come-installare-1.3.1-IT.pdf | 110149 | `11de8556419cf443ceaaef4155c9722c1ea851c381f754e41927e71401becfbb` |
| How-to-install-1.3.1-EN.pdf | 109511 | `bb4a688b267089a4837c602bba507b77dcad790e83c1cd6bd78b398a0a5f9a40` |
| Novita-1.3.1-IT.pdf | 140400 | `cd0ea90d3772f5c91b9734d8a37d13c2d8b0c29b5e4c93d6867edcb3f991d94f` |
| Whats-New-1.3.1-EN.pdf | 140480 | `5690c9d527d7310018d1bbfff589a1368b0591f823a267126a08b26847678499` |

The final repository gate for this exact source checkpoint collected 2,985
tests with zero failures. Class A ran 2,045 of 2,098 with 53 declared skips;
Class B ran 579 of 887 with 308 declared skips. The skipped fixture-dependent
suites remain explicit limitations rather than inferred runtime coverage.

The exact IT target still needs the conservative copied-save and physical-device
gate. Candidate-bound screenshots remain historical development captures and
must be refreshed or explicitly requalified before publication. No push, tag,
release or upload is implied by this private draft.

## Historical receipt - 31 October 2026

Prepared on 31 October 2026 from the exact private manual-test candidates in
[the runtime report](ui-1.3.1-validation.md). No ROM was rebuilt or changed.
The maintainer's device gameplay validation and production activation/release
acceptance remain open. No push, tag, release or upload is part of this work.

## File reconstruction

The explicit [contract](../distribution/release-1.3.1.json) retains all 21
previously recognized sources and adds EN/IT 1.2.5 and device-V1.3: 25 routes
per language, 50 total. Each route was decoded with xdelta3 and pinned
RomPatcher.js, and both outputs matched the complete target SHA-256 and size.
That is 100 successful decoder reconstructions, not game or save tests.
All temporary decoded ROMs were removed. Contract SHA-256:
`6bbc998fe2c6862bf33d25367937b3563fbc7f76d0d78230a6b16bdda3d41fe4`.

| ZIP | Byte | SHA-256 |
| --- | --- | --- |
| Sacred-Gold-Plus-1.3.1-US.zip | 325940835 | `2bd0930012fed6987031e09d523b234d100b88f87f0001107e83b9f470e12ff9` |
| Sacred-Gold-Plus-1.3.1-IT.zip | 349186004 | `652f858dea7c0fddb3d8e1f77988c0f584ba38c04d39759f267e564c7f05087b` |

Each ZIP has 39 files under one `Sacred Gold Plus 1.3.1/` root. Every member
was read back. `Patch/manifest.json` describes all routes; `Patch/CONTENTS.json`
records each member's size and SHA-256. The five original gameplay PDFs and
trainer reference match their independent historical pins; the complete
reference ZIPs also match their contract hashes. Credits and license remain.
No ROM, save, BIOS, emulator or personal source-path mapping is included.
The existing 1.2.5 release contract and all published assets remain unchanged.

## Guides and images

Four PDFs were rendered with reportlab 4.4.9 and all 40 pages visually reviewed.
Installation is 12 pages per language; current features are 8 pages per language.
They include real patcher screenshots, exact source/target hashes, normal-save
update instructions, credits and explicit offline-preparation status.

| PDF | Byte | SHA-256 |
| --- | --- | --- |
| Come-installare-1.3.1-IT.pdf | 109969 | `2d85850db6026881d2026bbb0cb1e8f443c4b2e48039a599a7ac091bd474f51b` |
| How-to-install-1.3.1-EN.pdf | 109448 | `c737be0ceae7ac5a9c3d6bf6f57db6d5ade604c3e783763366a580eceae824e8` |
| Novita-1.3.1-IT.pdf | 140540 | `7cd8bea7d52576e3c1129fc53b77ce416f42fd8c6abfbcf47e515df5584000ec` |
| Whats-New-1.3.1-EN.pdf | 140720 | `803d95306db1dd456c1539e060f4b8129c408f0ba7b347912044ea6665e1f376` |

The title, field-party and PC screenshots come from the exact active candidates;
[their record](../../images/1.3.1/captures.json) pins frame, crop and hash.
Presentation captures do not add gameplay acceptance. The release-page draft
uses the [template](../distribution/RELEASE-NOTES-TEMPLATE.md), introduces the
whole game and retains the maintenance line **Some bugs fixed.**

## Tool checks and limits

The 12 distribution tests pass, including unchanged default 1.2.5 selection,
versioned routes/documents and omission of unverified legacy cheat codes.
This preparation adds no global suite, Android, performance or gameplay PASS.
The strict save audit and bounded reassessment retain their separate recorded
results; patch decoding does not expand that coverage.

No Action Replay catalogue is supplied. `Cheats/` contains current instructions;
old codes are not silently renamed for a changed candidate. Native EV/IV,
training, shiny and storage features require no cheat.

Public sources include the versioned contract, guide authoring sources,
[reproduction inputs](../distribution/reproduction-1.3.1.json), tools and tests.
The current public tree is checked separately from the outgoing history. A
normal push of the unreviewed local commit range remains disallowed: a clean
publication proposal must exclude new internal intermediate commits while
preserving already-published history. New image/download URLs remain pending
publication; the local draft is not evidence that those URLs already resolve.
