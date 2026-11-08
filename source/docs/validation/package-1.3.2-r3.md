# 1.3.2 package revision r3 validation — 8 November 2026

Revision r3 republishes the corrected five-language package under a new tag
following removal of the previous release pages and retirement of old tags.
The game remains 1.3.2. Every accepted target hash, source identity and all
150 patch payloads are unchanged from the [r2 verification](package-1.3.2-r2.md).
The [r3 contract](../../distribution/release-1.3.2-r3.json) pins current PDFs and
package metadata; the original 1.3.2 and r2 contracts remain historical records.

## Exact downloads

| File | Bytes | SHA-256 |
| --- | ---: | --- |
| `Sacred-Gold-Plus-1.3.2-r3-Multilingual.zip` | 78501892 | `58f0f94600bf5ec58bf919911c78c4a0cfb45e77b7ffab06de8544fa2db500e7` |
| `Sacred-Gold-Plus-1.3.2-r3-Optional-Updaters.zip` | 996708993 | `ac70842152a90dd4ff06f1b26c9995bda6d70204de8341001b702673cef311b0` |

The main ZIP retains exactly 48 files: five language folders, each with one
same-language clean-ROM patch, seven-page illustrated installation PDF,
localized news PDF, three cheat files and two credits/license notices;
seven current English PDFs in `Originals`; and `START-HERE.txt`.
It contains no ROM, save, `Documents` directory or technical JSON file.
The optional ZIP retains 174 files, including all 150 historical updaters and
five readable localized source-hash/size/patch-name tables. Its inventories
and all complete member contents were checked after reopening the ZIP.

## Preserved source inputs

Only these four authenticated developer inputs are rehosted in the current
release. Older player/source ZIPs and standalone historical PDFs are unnecessary.

| Build input | Bytes | SHA-256 |
| --- | ---: | --- |
| `base-1.1-EN.xdelta` | 5747714 | `0bd20d17c8b18ee0a369d812b01facd83b00b3179d5fdca2ab149274b8248fc0` |
| `base-1.1-IT.xdelta` | 16183741 | `818bba0618da350440c6516a56ddc557c445cdbc79699835361866b3152c2014` |
| `SGP-Source-References-EN.zip` | 2482924 | `dae462265bd0bd6f0cb7e703cd5029fe25e78c35115f6939bf61841c449e9053` |
| `SGP-Source-References-IT.zip` | 2483578 | `4ef686035cd65b89db79dd8738743f4c4bf305b90d8c267eaffc7f6779f96674` |

All 13 locally retained ancestor assets were authenticated against their prior
server digests before selecting these four. The base downloader changes exactly
five delivery/release strings to `v1.3.2-r3`; every hash, size, name and decoder
option remains unchanged. Historical contracts keep their provenance URLs;
reference ZIPs supplied locally to the packager are obtained from the current
release and checked against the same original pins. Bootstrap uses a literal
commit reachable from `main`, so old tags are not required to retrieve its code.

## Bounded checks

- **88 distribution tests** and **59 base/downloader tests** passed.
  These are focused, ROM-free checks. No game compilation or emulator campaign
  was added for this publication change.
- All 150 patch payloads were read from the authenticated r2 optional ZIP and
  matched their individual manifests and complete hashes. That exact payload
  set had passed both xdelta3 and pinned Rom Patcher JS reconstruction against
  the five accepted target hashes. The r3 package reuses those verified bytes;
  it does not claim a second encoding/decoding campaign or new runtime evidence.
- New r3 metadata, filenames, credits, references, member inventories and all
  PDF/cheat pins were independently checked. Primary clean patches match the
  corresponding optional routes. Both assets remain below 2 GiB.
- Only the installation ZIP basename changes in the five player PDFs.
  Their first pages were visually checked; the other 30 installation-page
  streams remain byte-identical. All five retain seven numbered pages, the
  two authentic screenshots and five clickable tool/project links.
  R2 reproduction of all ten localized PDFs remains byte-identical.
  The five news PDFs, seven English guides and fifteen cheat files are unchanged.
- Source publication requires diff/public-file checks, explicit admission of
  new files and review of the entire outgoing history. The source ZIP is checked
  against every Git blob in the final source commit. Tag cleanup retains local
  object references and changes no `main` commit or game input.

The [distribution guide](../../distribution/README.md) and
[update procedure](../update-workflow.md) describe reproduction and future edits.
The full player release explanation, testing note, screenshots and credits are
preserved; only download/delivery instructions change.

## Scope and delivery

A separately reported Italian Guide-opening issue is under investigation. This
publication preserves the game bytes and does not claim that repair; a verified
game correction requires its own successor identity and bounded evidence.

The existing [1.3.2 game/save acceptance](localization-1.3.2.md) applies to the
same exact target hashes with its original limits. This package introduces no
save layout, migration, ROM build or device installation. A user already playing
the verified 1.3.2 game does not need to patch it again.

A public test prerelease can be provided while the final source CI is running,
with that pending status stated explicitly. Stable promotion requires the exact
source CI to pass. External verification/checksums bind the final ZIPs, source
commit, CI run and four preserved inputs. Anonymous full-download readback
checks asset bytes. Only the newly published tag remains remotely after the
explicit old-tag cleanup; source history remains intact.
