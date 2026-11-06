# Native Summary and New Game Guide

This module remains a **1.3.1** build dependency. The guarded
`build_combined_guide.py` composes the [EV/IV r5 reader](../native-eviv/README.md)
and the same three-panel native presentation in Summary and New Game. The
standalone input allowlist is exact Plus Community 1 EN/IT, not arbitrary ROMs.
Current full-game builds use the [1.3.1 composer](../sgp131/README.md).

The presentation never reads or initializes `SaveData`. It borrows graphics
and heap resources temporarily and restores them before returning to the host.
It leaves the upper Summary page in its selected ordinary/EV/IV mode. The field
menu Guide is a [separate application](../features/field-guide/README.md).

## Resource ownership

The rejected fullscreen design needed 44928 bytes plus overhead, exceeding the
24528–25728 free bytes in the four historical Summary samples. The implemented
compact layout uses **289 tiles /9248 bytes**: title 40 tiles, page indicator 6,
three-line body 168, reopen hint 24, Back 18, Next/Done 16, Exit 16 and one repeated
opaque-background tile. Text uses native font 0, 16-pixel line spacing, and
maximum 216-pixel lines within a 224-pixel body. Native glyph measurement, including
L=A variants, rejects overflow rather than shrinking/truncating text.

Snapshot 9248 + bitmap 9248 + tilemap 2048 =20544 bytes. The **22528-byte (`0x5800`)
raw NNS lease** bounds all context/Window/font scratch/alignment as well. The
combined context/backups/maps/bitmap/Oak extras use 21304 bytes plus a separate
four-byte final canary. Oak extras include its 64-byte lazy glyph buffer and
eight brightness/blend bytes. The builder calculates/asserts final bounds.

| Region | Normal combined composition |
| --- | --- |
| Added ITCM partition after r5 | `0x01FF8880–0x01FFA000`, 6016 bytes |
| Code |4748 bytes, ending `0x01FF9B0C`|
| Text at `0x01FF9B10` | EN 1098 / IT 1176 bytes |
| State at `0x01FF9FC0` |64 bytes|
| Total remaining margin | EN 106 / IT 28 bytes |

The explicit 64-byte owner serves Summary and Oak in disjoint lifetimes; all
resources are released before ownership changes. No save/game padding is used.
`combined_guide.c` derives from preserved `summary_guide.c`. Shared
`guide_present.c` only parameterizes text positions and `copy16`; default
Summary payload bytes remain identical. The combined build uses a noninline
halfword copy to fit its code bound. The validated heap resolver accepts
explicit host heap 19 or 80; allocation/free/IRQ reuse unchanged `lease.c`.
The r5 object loader accepts only `.text` and internal Thumb BL relocations,
not `.data/.bss/.rodata` or ABS32. Build limits must not be bypassed by adding
unloaded static state or consuming DTCM/BSS/stack.

### Summary host

`PokemonSummary_Init/Main/Exit` are at `0x02088298/0x02088424/0x0208856C`.
Heap 19 is child of 3, size `0x45000`; Summary state is `0x7D8` bytes. Native
`OverlayManager_GetData=0x02007290` reads manager `+0x1C`;
`GetArgs=0x020072A4` reads `+0x18`. These are distinct; the old design's swapped
GetData attribution was corrected before implementation. Dynamic Summary/heap
pointers must be resolved, never copied from sample addresses.

The input hook is `0x02088B40`; Skills/Stats renderer `0x0208D178`, fixed-window
builder `0x0208C3E4`, page windows `0x0208C42C`, removal `0x0208C4E0`,
VBlank `0x020885DC`. `summary+0x224/+0x228` hold the page-window pointer/count,
`+0x22C` args,`+0x7BC` page and `+0x7BF` flags. The normal entry requires state 2,
page 1, mode 0 and no conflicting move-selection transition. Other modes need
their own contract. PC-relative BL prologues must be re-emitted/relocated, not
copied as raw trampoline bytes. The Main wrapper verifies `38b50c1c7ef732ff`
and resumes at `0x0208842C` after the native GetData call.

BG structures begin at `BgConfig+8`, stride `0x2C`; BG4 is `+0xB8`, never stride
`0x30`. Summary uses BG4 characters `0x06210000`, screen map `0x0620F800`, 4 bpp,
32-byte tiles, 32×32 map and palette 13. Font 0 is already direct-access and is
borrowed without mode/refcount changes. The closed badge at tile(21, 18), 10×2,
baseTile `0x3C0` borrows 20 tiles/map cells; it is removed before transitions or the
large modal lease. Its rectangle `[168,248)×[144,160)` avoids the checked native
move/Box/page targets in the supported page. It is not valid on arbitrary pages.

The modal keeps the original `Window` objects and their pixel buffers intact.
It owns only its own buffers and saved characters/map. Never pass an interior
raw-lease pointer to `Heap_Free` or `RemoveWindow`. Native font 0 is NARC 16,
member 0 of `a/0/1/6`, header 16 bytes, width-data offset 32592, 509 glyphs; measured
EN/IT member hash `9a17de30…9e73` matches but the entire archive differs. Text
uses mapped u16 glyphs, spacing 0 and native widths. Unmapped characters are
rejected; the typographic apostrophe U+2019 maps to `0x01B3`.

### New Game host

Only the three ARM9 Oak template pointers change; overlay 53 and original
Init/Main/Exit remain. Native Init completes the first graphics setup before
`newgame_host.c` suspends Main ahead of the first Oak task. An instance marker
survives the naming keyboard, preventing a second presentation, and Exit clears
it before calling the original Exit exactly once. Original New Game initialization,
name/gender/rival writes and continuation remain native. Overlays 36/53 occupy
the same RAM and cannot run simultaneously.

The historical base EN hash is
`3ed4ea0291092d46def2f71454821bbde7832014ec020680468af7bfca686248`, IT
`217daa45f4945abd3feda6f583f5163db029d1aa361c33c18f12b32ad4eca4a4`.
The inspected r5 hashes are EN
`a1d7ed3ecb8aa98f96f65c17015cb49df5bda84323459cb17fd3d4c4501f556e`, IT
`96c41b594349e22c34789a52123327093b78e92a5be926f4e3000dd32a8e8ed3`.
These identify the old component research, not the 1.3.1 release.

Oak uses heap 80 (parent 3, size `0x40000`), lazy font 0, palette 14/background 15,
BG4 characters `0x06218000` and map `0x06207800`. The compact borrowed character
range is `[0x06218020,0x0621A440)`. At first setup both MASTER_BRIGHT values are
`0x8010`; sub DISPCNT `0x00011010`, BLDCNT `0x3944`, BLDALPHA `0x001F`, BLDY 0.
Enabling BG4 alone would leave the Guide black. It checks callback/video/heap/
font, shows BG4 with neutral sub brightness and blend disabled, then restores
exact black/blend/visibility/maps/characters/font scratch before resuming Oak.
Main brightness/graphics remain owned by Oak. Lazy font 0 callback `0x02026111`
and its 64-byte glyphReadBuf must be preserved, without converting to direct
mode or blindly restoring private filesystem objects. Later Oak rendering,
font mode/refcount/header/pointers are separate restoration checks.

### Allocation, transfers and input

`lease.c` resolves the current native heap table/index and calls ARM
`NNS_FndAllocFromExpHeapEx=0x020B53A0` and
`NNS_FndFreeToExpHeap=0x020B5530`, protected by native interrupt disable/restore
`0x020D3A38/0x020D3A4C`. Only the returned raw pointer is owned; release clears
it once and is harmless at NULL. It does not change native `numMemBlocks`.
`Heap_Alloc` is unsuitable for a capacity probe because its failure can reset.
Total free space alone does not establish contiguous capacity.

Init checks host mode/resources, drains earlier transfers, then snapshots. No
allocation/free occurs in IRQ. While active, the modal consumes host input and
suspends normal Main, including its animation tail, while retaining host VBlank.
No global queue is cleared. `ScheduleWindowCopyToVram` schedules the map but
copies characters immediately, so presentation must delimit hidden/drawn phases
to avoid tearing. Exit waits for Guide transfers, restores characters/CPU map,
schedules the original map and keeps buffers valid through its completing
VBlank, then restores visibility, releases only owned resources and resumes.
It must not reinitialize Summary, redraw ordinary stats or invoke Oak to repair
Summary. Partial-init/repeated cleanup uses explicit ownership/transfer flags.

START and the matching visible touch target open the Guide. Input release is
required at entry/exit to prevent held START/A/B/touch from skipping panels,
closing Summary or reopening. While open: B/Exit first, then Left/Back, then
A/Right/Next; one new event per frame, no repeat, no wrap. Back on the first
panel is visibly disabled; Next on the last becomes Done. Touch bounds equal
visible bounds. Closed-host native precedence remains unchanged. The historical
standalone r5 source used mapped keys, so its L=A instructions
explain choosing Normal/NORM. without changing player settings. The later V4
composition retains its patched raw-key reader; its actual contract is recorded
in [Summary controls](../docs/summary-controls-1.3.1.md). `gSystem.buttonMode` is
`+0x34`, value 3 for L=A.
Raw held/new are `+0x38/+0x3C`, mapped new/repeated `+0x48/+0x4C`, and
touch X/Y/new/held `+0x60/+0x62/+0x64/+0x66`. Do not mutate global key bits to
consume input; suspend host dispatch.

## Reproduce and validation limits

From the repository root, using identified private inputs and the project
environment; see the [runtime guide](../docs/test-bench.md):

```sh
python3 source/native-guide/build_combined_guide.py \
  --rom /private/path/base-plus.nds --charmap /path/to/verified-charmap \
  --out /private/path/new-directory
python3 -m unittest discover -s source/native-guide -p 'test_lease_*.py'
```

`verify_newgame_guide.py` starts without SRAM and uses ordinary input: Guide/skip,
gender, explicit TEST name, confirmation, bedroom, native mother dialogue enabling
the menu, first SAVE, and cold boot from that new save. It verifies all FF SRAM
before SAVE, exact saved/reloaded bytes, name/gender/game/location. Cross-New-Game
comparisons distinguish ID/avatar/variable `0x403C` differences already present
in original r5; RNG is unchanged. `verify_combined_summary.py` reuses reviewed
Summary inputs/assertions with only provenance/text offsets adapted.
`verify_newgame_transitions.py` checks entry/exit and Oak's native fade. The
identified Task 3 observer/core is unchanged.

The separate `build_newgame_pressure.py` / `verify_newgame_pressure.py` use a
174000-byte owned reservation before a real 22528-byte UI request returns NULL,
then verify canaries/native free. These diagnostic ROMs retain r5 Summary and
are not normal candidates; they do not edit free lists/heap size.

The historical 7 September lease prerequisite passed four EN/IT Party/Box
fixtures, ten cycles each: 10 successful 22528-byte allocations, 10 second requests
returning NULL while owned, 10 matching frees, 20 empty cleanup calls and 112640
checked pattern words. Every cycle restored complete free/used lists, heap
header, native counter 329, callback/args/page/windows; SRAM/Pokémon remained
unchanged. Held START 120 frames ran once; other controls preserved native
behavior. That probe was 792 code bytes at `0x01FF8880`, ending `0x01FF8B98`, with
explicit zeroed marker reserve `[0x01FF9F00,0x01FFA000)`. It was a prerequisite,
not a second installed feature or universal capacity proof.

`build_lease_rom.py` reconstructs/hash-checks r5 from exact Plus bases and guards
helper preimages. `prepare_lease_observer.py` adds read-only 32 KiB `dumpitcm` to
the pinned historical frontend without rebuilding its core; manifests bind
sources, objects/libraries, commands and binary. `run_lease_probe.py` /
`lease_oracle.py` reject stale source/object/ROM provenance and check actual
loaded ITCM. RED on each exact r5 fails with `Missing game-executed lease result`.
Six focused tests reject unknown bases, existing output, wrong hook/ITCM size,
code/marker overlap and stale provenance. Static fixtures now build fresh
recognized inputs under system temporary storage and clean up; missing private
ROM/charmap inputs skip explicitly rather than relying on vanished old tmp paths.

A rejected composition exceeded the compressed r5 ARM9 limit; the corrected
composer starts from the exact base container and adds only r5's message bank.
Roundtrip validation calculates exactly the three rewritten autoload/compressed-
data metadata fields rather than ignoring a broad header area.

The component evidence uses pinned melonDS core `906e9ebb…`, Mac interpreter,
software 1×, fixed RTC, FreeBIOS and no cheats. It is not GUI/audio/Android/handheld
or all-save acceptance. Pixel equality includes the lower screen, numeric rows
and upper title, excluding animated upper sprite/indicator. Original fixtures
and prior failed attempts remain private. Current 1.3.1 acceptance and exact
successor identities are in [current validation](../docs/ui-1.3.1-validation.md).
