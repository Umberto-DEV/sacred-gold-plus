# Summary control legend in 1.3.1

The implemented legend is `L:EV SELECT:Stat. R:IV` for Summary Stats, EV and IV
views. **This additional owner remains inert in the current player profile.**
It introduces no save field, ID or key remapping. Host/ARM tests below establish
component contracts; activation requires candidate-bound window/tile evidence.
See [current validation](ui-1.3.1-validation.md) for the composed ROM's state.

## Reader and window ownership

The installed V4 reader is preserved. Its ITCM payload is at `0x01FF8620`
(592 bytes), with reader at `0x01FF8658` (448 bytes). It reads physical buttons:
`gSystem.newKeysRaw` at `0x021D1148`, repeat at `0x021D114C`, literal at
`0x01FF87F8`. L/R/SELECT therefore work even with L=A. Historical
`native-eviv/eviv.c` instead reads mapped keys at `0x021D1154`; recompiling it
would lose L in that mode, demonstrated by changing the literal under Unicorn.
The reader, hooks `0x02088B40`/`0x0208D178`, label wrapper `0x01FF9348` and EV/IV
strings stay byte-identical, pinned by ranges/full instructions in
`data/controls-native-abi.json`.

`sgp_summary_controls_update(summary)` creates once, redraws and removes one
owned window; `sgp_summary_controls_destroy(summary)` releases it. Its 16-byte
`Window` and 1024-byte pixel buffer use Summary heap 19. A 32-byte resident record
(owner, generation, window, redraws, flags) is the only state. The native 34-window
array is neither extended nor modified.

Only three complete BLs change:

- `0x0208CC5A`, Skills-page rendering → `sgp_sc_redraw`: update, native function,
  then inherited reader hook.
- `0x02089D78`, page change, and `0x0208C564`, exit → `sgp_sc_teardown`: destroy
  before native `sub_0208C4E0`.

A complete ARM9 BL/pointer census finds these as the only callers. Thumb BL
range is ±4 MiB; bases through `0x023E0000` are reachable and the encoder rejects
others. No instruction is relocated.

Drawing requires the Skills/Stats page, no exit, present args, mode at `args+0x12`
neither 3 nor 4, `args+0x18 == 0` (no move to learn), a present non-egg Pokémon via
`GetBoxMonData(mon, 76)`. Otherwise it allocates nothing or removes its existing
window. Page changes/exit destroy the legend before native page/heap teardown.

`generation` is diagnostic, not a reuse guard. The complete destruction-edge
census ensures every Summary destruction traverses the rewritten BLs. Therefore
a live same-owner record cannot retain an unfreed window. Reading a possibly
freed Window to validate it would itself be unsafe. Only its creator frees it;
a stale previous-owner record is forgotten without touching the destroyed heap.
Allocation failure leaves state intact/no NULL access and retries on next redraw.
It does not use `AllocWindows`, which omits `Heap_Alloc` checking. Native
`Heap_Alloc` normally returns NULL, but pret `AllocFail()` can reset during active
communication; total request is 16+1024 bytes from heap 19.

The payload has no `gSystem` literals, enforced by readback. The legend itself
is independent of button mode. Native modes are Normal, Start=X, X/Y swap and
L=A; only L=A hides L/R from mapped input. The real raw reader passes all four
modes using inputs computed like `ApplyButtonModeToInput`; historical Android
reader checks cover Normal/L=A separately. Move-learning modes 3/4 and TM mode 2
with `moveToLearn != 0` retain functional L/R/SELECT without the legend: window 17
and a fifth move need that area. This is a conservative legend exclusion, not a
reader limitation.

## Text and geometry

The same button names/abbreviations are encoded in EN/IT with pret charmap;
unmapped characters fail. Native font 0 uses `0x000E0F00` (white/shadow, matching
battle-move/EV/IV headings) in one line.

| Variant | Literal text | Advance | Minimum window |
| --- | --- | ---: | --- |
|Compact, default|`L:EV SELECT:Stat. R:IV`|124 px|16 tiles =128 px|
|Spaced|`L:EV  SELECT:Stat.  R:IV`|132 px|17 tiles =136 px|

BaseTile 955 at (1, 18) is an **unproven proposal**, not an accepted placement.
An inert installation records `geometry_source: proposal` and
`placement.proven: false`. `prepare` rejects a window narrower than the text
(`truncated`) and records advance/width. Private offline font renders over the
29 October IT lower-screen capture show the spaced form separating commands
more clearly, both fitting the red strip at (8, 144) above tabs/below moves.
These composites are not gameplay captures.

Static tables show the proposed lower-screen BG4 rectangle (8, 144, 128×16)
overlapping `page_skills.12` (fifth move), `page_skills.17` (message `0xC2` from
`sub_0208AFA0`, flag 1), `shared.14` and `shared.29` (special-mode cleanup in
`unk_02088288.s:4913,5038`). They may be empty in normal views but that is not
established by tables alone. `prepare(..., active=True)` requires `evidence`
listing them under `hidden_windows` and the needed `free_tiles`.

Evidence binds `capture_rom_sha256` (the captured inert candidate) to explicit
`candidate_sha256`, exact `build_id`, declared `language`, identical `geometry`,
`views` containing {stats, ev, iv}, `button_modes` containing {normal, L=A},
`contexts` containing {field, pc}, and `captures` with `{name, sha256}`. Wrong
candidate/language/geometry or incomplete coverage is rejected; the entire
evidence is retained in the receipt. It records both candidate/capture hashes
and `candidate_relation`: `stage-inert-output` when recomputed from this stage's
inert bytes, or `composed-candidate` for a full composition this module cannot
recreate alone. Binding to the earlier V4 stage input would incorrectly reject
captures of the actual candidate and is no longer used.

Native BG4 windows end at 954; 10-bit tilemaps end at 1023. Base 955 with 32/34 tiles
fits that numeric limit, but tables alone do not prove absence of other graphics
above 954. `sub_0208CBD4` clears BG4 columns 0..17/rows 1..23 at every page redraw;
the legend redraws with it. A tile is never claimed merely because it looks empty.

## Composition and receipts

`audit`/`prepare`/`verify` pin consumed/modified ranges rather than an entire V4
image. `controls.intervals()` includes the EV/IV reader/display payload, two
hook words, full bodies of ten native callees plus the function containing
`0x02089D78`, four Window tables, two BG descriptors, literals, and three BL sites
(the only changed ARM9 bytes beyond the slot). A separate predicate checks the
complete BL caller set of four hooked targets. A preceding stage that preserves
these ranges is accepted; a conflict names its range.

`test_controls_rom.RealUiComposition` proves UI→legend using actual
`sgp131.ui.install` output. Legend→UI is rejected by the UI's exact V4 requirement.
No overlap exists with UI writes at `0x0201A556`, `0x02000DB0`, `0x0203BFE4`,
template `0x020FA354`, payloads `0x023CB800`/`0x023D4000`/`0x023D6800`/
`0x023D6E10`, seeds or zeroing (`test_controls.Intervals`). The 512-byte
`summary-controls.runtime` slot at `0x023D4C10` begins 16 bytes beyond Fieldbook's
`0x023D4C00` payload end.

`prepare(..., allocation=<reserve receipt>, preimage_sha256=...)` requires the
`sgp131.reserve.allocate` receipt for `summary-controls.runtime`, rechecked
against current policy, same-language V4 input, unconditional owner names and
exact allocation assignments. The historical component campaign used explicit
`bench.declared_reserve` because the then-current policy's `field-guide.code`
parent was conditional. Production must prove retirement and obtain its own
current policy allocation; a test policy is not production authorization.
The receipt records `function_state` (`inert`/`active`) recomputed by `verify`
from the installed activation word, not review/Android process labels.

## Component validation and remaining activation coverage

| Layer | Evidence | Status in this component campaign |
| --- | --- | --- |
|ROM-free host|Pins, comparison, BL encoder/hooks, geometry/text, prepare contract|Executed|
|EN/IT V4 ARM Unicorn|Real AddWindow/FillWindowPixelBuffer/ScheduleWindowCopyToVram/ClearWindowTilemapAndCopyToVram/WindowArray_Delete, raw EV/IV reader, patched dispatcher/exit|Executed|
|Android legend rendering|Actual tiles, visible windows and live states|Not established|

The bench fills new blocks with `0xCD`, requiring the legend to clear its pixel
buffer, and freed blocks with `0xDD`; a hook detects every access to freed ranges.
Declared stubs: `Heap_Alloc`/`Heap_Free`,
`AddTextPrinterParameterizedWithColor` (printer stack unmeasured), `GetMon`,
`GetBoxMonData`, VRAM transfers, and native teardown in the exit flow. Summary,
BgConfig and Pokémon are synthetic/scattered. Page-change site `0x02089D78`
is checked statically only; it shares the tested exit wrapper.

Activation coverage still requires preserved-copy EN/IT advanced saves with an
egg, nonzero EV/IV and level/TM move learning. It must observe: legend at normal
Stats without overlap; repeated L/R/SELECT with Normal/L=A; member/page changes,
redraw/generation increment; B/Exit and Party exit with owner 0; egg and
move-learning exclusions; field and nested PC paths; active/inactive move
selection and window 17; native SAVE/cold restart with data preserved; actual
BG4 tile/Window use at (8, 144)–(136, 160) and heap 19 allocations before/after.
These are required coverage, not claimed completed runs.

```sh
PYTHONPATH=source .venv/bin/python -m unittest sgp131.test_controls -v
PYTHONPATH=source SGP_CONTROLS_REQUIRE_INPUTS=1 .venv/bin/python -m unittest sgp131.test_controls_rom -v
PYTHONPATH=source SGP_CONTROLS_REQUIRE_INPUTS=1 .venv/bin/python -m unittest discover -s source/features/summary-controls/test -p 'test_*.py' -v
```

The final builder must call `controls.candidate_gate(final_rom, receipt)`.
`controls.inert_view` zeros only this stage's activation words/flags; that final
ROM hash must equal the captured `candidate_sha256`. Without it,
`candidate_relation: composed-candidate` is only a label: tests show an invented
candidate can pass prepare but fails this gate.

`controls.slot_preimage_from_v4(v4, language, allocation)` derives expected slot
bytes from exact V4, never from the current input's own slot (a tautological check).
If an intermediate stage legitimately leaves data there, its fixed manifest hash
must instead supply `preimage_sha256`. Clang/charmap are pinned by hash;
`controls.verify(..., charmap=...)` recompiles with receipt geometry/variant/flags.
Known limits: the caller predicate sees static Thumb BL only, not ARM BLX,
literal-pool or overlay calls. `audit` applies before prepare; installed sites/
functions no longer match old pins. Transitive native callees are not individually
pinned; composition relies on a verified closed list of other-stage writes.
