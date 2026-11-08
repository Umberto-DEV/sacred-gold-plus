# 1.3.2 package revision r2 validation — 8 November 2026

The earlier player ZIP buried installation/news PDFs in `Documents`, mixed
historical input labels with current patch selection, and duplicated guide
material. Revision r2 changes the package and beginner instructions while
retaining every accepted 1.3.2 game byte. The primary ZIP contains five patches;
all 150 direct historical-source updaters remain in a separate optional ZIP.

## Exact game identities

| Locale | Bytes | SHA-256 |
| --- | ---: | --- |
| EN | 152786800 | `65d6d42a59543a499858ce43c5c4652ab5323fe290124daddfaf842ead1034f3` |
| IT | 159029716 | `e884761c8141042bc64eff62564c3e2a0c707379851eb0790e70f09bd4f4019e` |
| FR | 162560728 | `0366cc3d7909cc0e5996a78486a547dced3d7809a2243627828f74877ccaefa9` |
| ES | 162490072 | `ae593192321095f936b10e0ad444e238b2fcc12d471ee7b0f05896fde8e0745f` |
| DE | 162932492 | `225f21a9752a2e2388980f98186de6aa89aabcd68c0ef8c76d3fd99f4539fa25` |

These are exactly the targets in the immutable
[original 1.3.2 contract](../../distribution/release-1.3.2.json).
The [new schema-3 contract](../../distribution/release-1.3.2-r2.json) pins every
PDF, cheat file, recognized source and decoder, without repinning a game.
Its SHA-256 is `aee7dfc9cfd98a71b8ed6973287941a54713bdbd1e27e975bc1ee890d6fa2ccc`.

## Player artifacts

| File | Bytes | SHA-256 |
| --- | ---: | --- |
| `Sacred-Gold-Plus-1.3.2-r2-Multilingual.zip` | 78501892 | `a687c8125ae973e46daf50918ee4b553bddd0086c3b11e12a606b844fec93ba6` |
| `Sacred-Gold-Plus-1.3.2-r2-Optional-Updaters.zip` | 996708996 | `c2fd0cc2c7bad7ba2fd5a8e4a3742d1267d2959d171c50a35477e02ff301c8d8` |

The primary ZIP has **48 files**: five language folders, each containing one
same-language clean-ROM patch, two visible localized PDFs, three cheat files
and two credits/license notices; seven current English PDFs in `Originals`;
and root `START-HERE.txt`. There is one Game Guide, no `Documents` folder and
no JSON, internal checksum, ROM or save file. Every guide and cheat file matches
its complete contract pin. All five folders reproduce the same full English
GPLv3 text with a localized explanatory notice.

The optional ZIP has **174 files**, including all 150 patches and five readable
localized updater tables. Each table contains every source ID, complete source
SHA-256, exact source size, exact patch filename and current target identity.
The tables regenerated from final sources match the packaged bytes exactly.
Credits/licenses accompany this standalone download too. Technical manifests,
member inventories and checksums are confined to this optional archive.

## Focused verification

- **87 distribution tests passed**, including historical schemas, document
  sources, exact primary clean-language selection, missing/altered input
  rejection, archive layout, localized notices and asset-size bounds.
- Every one of the **150 routes** was freshly encoded and decoded with both
  xdelta3 and the immutable Rom Patcher JS snapshot. Every complete output
  matched its chosen accepted target hash. Temporary reconstructed ROMs were
  removed. The five main patches reuse those exact verified patch bytes.
- After restoring the illustrated installation guides, only five PDF pins and
  the primary ZIP changed. All patch bytes, the optional ZIP, five news PDFs,
  seven English gameplay PDFs and fifteen cheat files stayed unchanged. Both
  final ZIPs were reopened and their complete member contents checked. Each
  remains below GitHub's 2 GiB asset limit.
- All five installation PDFs contain **seven numbered walkthrough pages**, two
  authentic Rom Patcher JS screenshots and clickable tool/project links. They
  explain ZIP extraction, correct asset selection, ROM versus patch versus save,
  browser/Mac/Windows SHA-256 calculation, Reference A/B comparison, checksum
  settings, output verification, copied-save testing, installation and recovery.
  Real screenshots retain their 27 October 2026 capture date; no new game capture
  is presented as proof. SHA-256 is explicitly distinguished from the patcher's
  CRC32/MD5/SHA-1 displays.
- Historical `d:*` document copy remains unchanged in every locale. All 45
  default-renderer outputs remain byte-identical using the complete synthetic
  regression fixture. Current walkthrough copy uses separate `p:r2:walk:*` keys.
  Complete extracted gameplay text and page counts of all seven English guides
  are unchanged after replacing only the obsolete packaging notice.
- Installation pages and representative news/gameplay pages were visually
  checked for legibility, tables, links and clipping. This is not a visual
  inspection of every page of the large species/location references.

Reproduce the focused source checks with the declared dependencies installed:

```sh
PYTHONPATH=source python -B -m unittest discover -s source/distribution -p 'test*.py'
```

The [distribution guide](../../distribution/README.md) documents generation,
input selection, final layout and release-template variables. The
[update procedure](../update-workflow.md) identifies the source/document owners
for future changes. The release page keeps the prior game overview, testing
note, screenshots, contribution section and credits; only download instructions
and asset links are updated.

## Evidence limits and publication

No new ROM build, save-format migration, emulator run or device installation was
performed for this packaging revision. The existing bounded
[1.3.2 game/save acceptance](localization-1.3.2.md) still applies to these exact
hashes, with its original fixture, language and runtime limitations. Recognized
source routing does not establish arbitrary-ROM or universal-save compatibility.
A player already using the verified 1.3.2 game need not patch it again for r2.

Publication requires the final source commit's hosted CI, public-file admission,
diff review and an inspection of the entire outgoing history. At publication,
external `verification.json` binds the source archive, commit and exact CI run;
`SHA256SUMS` covers all three ZIPs and that report. Full anonymous download
readback checks published sizes and hashes before retiring the superseded
release page. Existing Git tags/history and historical build-input assets are
preserved. CI checks source without a commercial game and does not itself
validate gameplay or saves.
