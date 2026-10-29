# Native field Guide

This is the field-menu Guide application, independent of Plus settings and the
existing Summary EV/IV guide. It never reads or writes save structures.

`sgp13.guide.install` consumes an expanded 1.3 ROM, a validated language-specific
content payload and the private reference charmap. It returns native hook and
allocation metadata. It preserves file IDs and all existing message members:
content is a new member of `a/0/2/7`; the grown archive and patched overlay27 are
appended through `sgp13.resources.append_file`, without ROM repacking.

## Ownership

- Code: `0x023D4000..0x023D6000` (actual size checked on every compile).
- Foreign gap: `0x023D6000..0x023D7B00` belongs to Teams/training. The installer
  neither checks it for emptiness nor writes it; complete before/after bytes
  must compare equal independently of Guide readback.
- Config/template: `0x023D7B00..0x023D7B40`.
- Private-build native graphics recipe: `0x023D7B40..0x023D7C04`.
- Encoded interface labels: `0x023D7C40..0x023D7E00`.
- Ephemeral state: `0x023D7E00..0x023D7EF0`, checked by C static assertion.
- Canary: `0x023D7EF0..0x023D7F00`; allocator boundary starts at `0x023D7F00`.

Heap38 is created only while the field application owns the screen and the
native Options app is absent. It has 256 KiB; content is bounded to 128 KiB.
The remaining space owns windows, strings, BG buffers and temporary native
resource loading. The content allocation is checked before the native read.
Font0's native lazy cartridge reads made long pages block rapid input. The
Guide now acquires a checked temporary glyph cache on Heap38 (32,576 bytes for
the verified EN/IT fonts; bounded to 32 KiB). An existing direct-access font is
borrowed without taking ownership. Allocation failure leaves the native lazy
renderer unchanged. Exit restores the native lazy callback before freeing the
Guide-owned cache; no persistent heap or save data is added. The change adds
196 code bytes and four bytes of state. Native ARM ownership/failure tests and
full-page melonDS replays cover this path.

All acquired app objects are released by the child app Exit, then the original
start-menu task reloads the field overlay and resumes its return/fade path.

The separate Guide cursor never expands the seven physical menu-slot arrays.
Indices7/8 retain their registered-item meanings. Input hooks preserve vanilla
call-site movement/task/fade guards and additionally require normal menu mode.
Every native menu construction resets Guide selection, even if the allocator
reuses its address. B/X closure and excluded-mode transitions clear pending and
selected state. The final launch guard resolves the live menu from the current
FieldSystem's SysTask controller and checks its type, phase, child task, owning
FieldSystem and normal menu mode. Saved pointers are compared as values only;
no stale menu pointer is dereferenced to establish eligibility.
A code-generated book glyph sits in the native 40×26 frame, centered at(124,155).
A temporary 8×4 Window on BG4 uses shared character tiles390..421 after the
eight native label windows. BG5 retains the labels, including the Options label
that shares tile row17 with the icon. The overwritten BG4 area is a solid native
background; unused palette5 color1 preserves it and the cut frame corners.
The normal/selected icon palette is copied into bank5; native graphics members
7/8/9/14 and the full field-menu overlay are guarded before installation.
No extracted icon is distributed.

Touch and A use the same nine-frame confirmation and five temporary page-turn
draws. No icon allocation survives a draw or runs on idle frames. Pending
confirmation suppresses native item dispatch. B/X, replacement and excluded
menus release only the Guide-owned touch command32 before clearing selection;
other native commands remain untouched. This preserves the original menu
handler's touch-before-button ordering without leaving a blocking command.

Both screens use native HGSS font0, Options palettes/backgrounds, a highlighted
subject band, five inset list rows and visible page/reference controls. They use native
frame graphics. Main/BG1 windows end at tile589; frame tiles600..635. Sub/BG5
text ends at tile504; its frame also uses600..635. This is below its screen-map
address; using the older tile988 frame convention here would overlap that map.

## Content API

`build_content(categories, encode, measure)` accepts categories with `id`, `title`
and `entries`; entries have stable `id`, `title`, and `pages`. A page is a list of
lines, or `{ "lines": [...], "reference": entry_id }`. The optional reference
opens via X or its bottom-screen footer control. B restores the exact originating
page and list position. Reference history is bounded to eight levels. At that depth its Open control
is hidden; B continues to restore each recorded origin without history loss. The generator rejects missing targets, duplicate IDs, empty categories,
overlong text, malformed EOS, oversized counts, and bad binary offsets.

`encode(text)` returns game u16 codes including `0xFFFF`.
`measure(text)` returns the width in pixels measured with the actual game font.
Entry/category titles and detail lines must fit208px, at most7 per page and127 glyphs
per string. No automatic truncation is permitted. Five list rows are visible;
D-pad Up/Down scrolls, A opens, B returns, Left/Right or L/R changes detail pages.
Touch rows and the footer use bounded, edge-triggered input. Explicit Up/Down
footer arrows make every list entry reachable using only the stylus.

Binary SGG1 uses little endian values and absolute byte offsets from its start:

| Record | Layout |
|---|---|
| Header (12B) | magic4, totalSize u32, categoryCount u16, entryCount u16 |
| Category (12B) | id u16, count u16, firstEntry u32, titleOffset u32 |
| Entry (16B) | id u16, categoryID u16, pageCount u16, zero u16, titleOffset u32, pageTableOffset u32 |
| Page table | pageCount x u32 offsets |
| Page | lineCount u16, optional referenceID u16, lineCount x u32 string offsets |
| String | game u16 codes ending0xFFFF |

Categories and entries immediately follow the header. All referenced offsets
are validated independently by `validate_content` before installation.

## Checks

Run `python -m unittest discover -s source/features/field-guide/test -v` from the
repository root using the project environment. Tests exercise real content
packing, malformed offset rejection, glyph/line bounds, reference resolution,
native compilation with no external symbols, allocation boundaries, and the
actual C navigation logic compiled on the host. Focused ARM hook tests cover
excluded controllers/modes, stale unmapped pointers, changed owner tasks, X
closure, reused-address construction and a valid launch. Set
`SGP_GUIDE_BASE_DIR` to the private directory containing expanded v2 EN/IT ROMs
and `SGP_PRET_SOURCE` to the reference checkout to execute the sentinel-filled
foreign-gap installer test; absent private inputs are explicitly skipped.

Runtime acceptance additionally requires both language builds, raw-save cold
boots, touch and D-pad launch, list scrolling/back restoration, reference return,
repeated exits with heap handles cleared and canaries intact, and subsequent
field applications. Synthetic test content is not player-facing content and
must never be treated as evidence for factual guide completeness.
