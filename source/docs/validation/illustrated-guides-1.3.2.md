# Illustrated guides and move reference: 1.3.2

This is a documentation and package refresh of the already accepted corrected
1.3.2 game. It does not rebuild a ROM or change gameplay, settings or save layout.
The five target identities remain those in
[`game-1.3.2-r4.json`](../../distribution/game-1.3.2-r4.json). Existing runtime and
save acceptance remains bounded by the [Guide-opening report](guide-opening-1.3.2.md).

## Original documents and presentation

The five original illustrated PDFs are retained byte for byte under
[`guides/originals/`](../../../guides/README.md). Each matches its loose 1.2.3
English source and its members in the English/Italian 1.2.3 and 1.2.4 ZIPs.
[`guides/catalogue.json`](../../../guides/catalogue.json) records exact sizes
and SHA-256 values for both original inputs and current outputs.

The former generated gameplay documents had no image resources and used Vera
Sans. Current documents recover the original embedded font mappings in memory;
glyph outlines and advances are preserved. Required glyphs are checked before
rendering. No separate font download or standalone font file is distributed.
Original map and event illustrations remain in the corresponding current PDFs.

None of the five original manuals was certified wholly current as a standalone
Plus guide. Pokemon data omits later balance and Fairy changes; evolution text
confuses Beauty with friendship; item and event directions contain superseded
conditions; original fishing percentages are inaccurate. Current Pokemon,
evolution and item lists are regenerated compactly from authenticated data.
Events and locations place current directions/corrections before the original
illustrated body pages, with explicit supersession notices.

Static source checks also corrected two documentation defects without modifying
game code: Sudowoodo needs the SquirtBottle, and Cynthia's Sinnoh starter reward
requires Champion status. Type ID 9 is identified as Fairy rather than printing
the stale mystery label from the ordinary type-name message bank.

## Move completeness

All 471 sixteen-byte move records were compared for each of the five exact
released candidates against its authenticated clean retail donor. Each language
has the same 52 changed playable records, no additional changed dummy rows and
the same complete current record-table hash:

```text
3c84f5684b3d7c7e652b6126b33832c5f1c7146486560e60b04fde4d7aadda87
```

The move reference covers every changed field: type, power, accuracy, PP,
category, effect, effect chance, priority, target, flags and contest fields.
Replaced slots show both names. Magical Leaf is Grass to Ice; Will-O-Wisp is
75 to 85 accuracy. Actual native mechanics are stated rather than importing
later-generation defaults: Baby Eyes has priority +6, Drain Kiss uses half-damage
healing, Moonblast has a 10% secondary chance and Dazzle Gleam selects one target.

Forty-nine current records already match verified early Plus 1.01. Moonblast and
Play Rough reach their current effect selectors by the supplied Plus 1.1, and
Will-O-Wisp's later accuracy change is owned by `sgp131/modern_moves.py`.
No authenticated original Sacred Gold ROM baseline was available to assign
each inherited change individually to Drayano or early Plus. The documentation
retains that attribution limit. Native battle bug fixes and the Fairy type chart
are separate from the move-table comparison.

## Fishing and illustrated location coverage

Every current encounter record preserves its exact English Plus 1.2.3 prefix.
The repair completes 130 truncated records and supplies the four daily fishing
outbreak species. All 540 map/encounter mappings, native swarm mappings and
selector weights are unchanged. Headbutt, Safari and Bug-Catching Contest
archives are byte-identical between those two candidates.

The original manual's fishing percentages were inaccurate even for that older
game. Current grouped fishing lists replace all old rod-percentage rows and
aggregate duplicate species slots. They state ordinary base odds before lead
abilities and other modifiers. Illustrated area pages remain visual references;
they do not establish exhaustive Headbutt or Safari object-condition coverage.

## Package and verification boundary

The [package workspace](../../../package/README.md) was seeded from the complete
verified corrected ZIP, SHA-256
`037a35d4d48118ef5fbca273de3caf97cfdfff2e58ea4328e0e5ac78095fd78e`.
All non-document payloads are locked by full size and SHA-256. Root inventories
are regenerated; nested updater inventories and every patch, cheat and builder
input remain unchanged. Historical contracts are preserved.

The composer rejects altered payloads, missing/unexpected members, unsafe paths,
links and oversized trees, and independently reopens and hashes every output
member. The current delivery identity is recorded separately in
[`build-input-delivery.json`](../../distribution/build-input-delivery.json).
The release title, tag and prose are retained; only its displayed ZIP SHA-256
is updated when the authorized asset is replaced.

The finished ZIP is **1,188,633,471 bytes**, with **256 members**, including
18 PDFs: ten unchanged localized installation/news documents and eight current
shared English guides. The composer and an independent old/new ZIP comparison
confirm that every patch, cheat, updater and developer input is unchanged.
The 235 protected members match the authenticated baseline; only seven existing
gameplay PDFs and the two root inventories change, and the move PDF and guide
index are added. The current ZIP SHA-256 is:

```text
5aa9bbbc233b0acc5cb5745a6b3feb23fa65f95063dc90253465ff48816569e8
```

All **144 ROM-free distribution tests passed**. The first visual review covered
all 235 initial pages in 24 contact sheets and 22 detailed samples. A final
location-floor clarification adds one page; its revised current section was
rendered and reviewed separately, while the other seven PDF files reproduced
byte for byte. The final guides contain **236 pages**, with preserved original
map/event page streams and image bytes. No clipping, overlaps, missing images or
unsupported glyphs were observed. This is static/layout acceptance, without a
new native-speaker editorial review of all historical prose.

All 24 release-page screenshot URLs returned complete HTTP 200 image responses
in this session. A currently missing release image was not reproduced; no image
URL or other release prose was changed as a speculative repair.

This work establishes document data, presentation and package integrity. It is
not a new playthrough of every event, encounter or move, a fresh save campaign,
or a new physical-device installation.
