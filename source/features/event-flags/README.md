# Native high event flags

The original high event flags `3F00..3FFF` address bytes beyond the native flag
array, inside Pal Pad. The shared native getter now redirects that entire bank
to reserved variables `415E..416F`. External script IDs, event objects and cached
object IDs stay stable, including Mew `3FC8` and its Sinjoh reader.

The 36-byte reservation is at SaveVarsFlags offsets `2BC..2DF`: exact four-byte
ASCII tag `HF02`, then a 32-byte bitmap. No save-array size, identifier, checksum
boundary, Training journal version or layout changes. The supported source and
field/event/Frontier archive census found no other owner of these variables.
The installer rejects literal uses in those three archives at any alignment,
checks pinned native routines and preserves the composed Training/Bag loader.
Future code using synthesized variable IDs or raw offsets needs a fresh review;
archive scans do not establish whole-program absence of indirect accesses.

HF02 also separates the finite story-gate family `612E..6139` and
`619E..61A9` from `SAVE_CHATOT`. Those invalid variable IDs previously resolved
past SaveVarsFlags into 24 Chatot halfwords: SetVar changed recorded audio and a
new recording could reopen or close map events. The exact installed SetVar and
FieldSystem_VarGet paths now redirect only that finite family to 24 unused bits
of the existing bitmap. The installer pins both native consumers and the
coordinate reader, fixes the complete 48-literal archive census, and rejects a
new literal owner of any reserved bit. Adjacent invalid IDs retain their old
behavior rather than silently widening the patch.

An entirely zero reservation imports all 256 observable legacy high-event bits
once. On a successful Continue it also snapshots each old Chatot-backed gate as
exactly zero/open or nonzero/closed; an existing `HF01` bitmap is preserved and
upgraded the same way. `HF02` is authoritative and is never resnapshotted. New
Game imports the high bank and initializes the 24 gates open. The exact tag is
written last. No migration reads through the invalid variable accessor or
writes, repairs, clears or reconstructs Chatot/Pal Pad bytes.

Foreign nonzero reservations and unknown/future tags are preserved and refused.
The composed load checks the boot-loaded arrays before Training/Bag load, then
checks successfully reloaded arrays again. FALSE propagates through the native
Continue loader (`020273B0`) to overlay 36, which requests `OS_ResetSystem(0)`
before field setup. One rejected Continue requests one reset; SDK synchronization
is not wall-clock bounded. A defensive high-bank access on foreign ownership
also resets without returning to the event. There is no migration or flash write
on either refusal path. New Game retains native whole-struct initialization and
lazy import after arrays are initialized.

Every high-flag ID outside `3F00..3FFF` retains the original getter through a
guarded trampoline. Every ordinary variable outside the exact 24-ID family and
every SetVar outside that family use complete instruction-relocated native
trampolines, including zero/low/temporary behavior. Some original hidden
item scans read malformed outlier IDs; this fix does not broaden bounds behavior.
The pre-existing release assertion/out-of-range behavior remains a separate issue.

Compatibility is forward only. An older ROM ignores the bitmap and may write
Pal Pad again; downgrade/re-upgrade event synchronization cannot be promised.
Mirroring flag writes back into Pal Pad would reintroduce the corruption.

The communication trigger is now demonstrated at component level. The real
`SavePalPad_Merge` at `0202AF28`, reached by the trade-selection callback and a
link-battle callback, reconstructs the Pal Pad. On a logically empty Pal Pad it
zeros legacy `+C4..+E3`; with a valid entry 0 it replaces the same 32 bytes with
entry 0 `+3C..+5B`. Those bytes are exactly the legacy `3F00..3FFF` high-event
bank, explaining why completed custom events can reopen after wireless use.
Simple Union Room entry has not been shown to call the merge and remains a
negative control; mixing records is not yet isolated as a distinct caller.

The retained HF01 candidates EN `90435d3c…d5fc18` and IT
`420ec8b8…f059a` still have an upgrade-order race: HF01 imports lazily on the
first high-flag Check/Set/Clear. A Pal Pad merge before that first access can
destroy the legacy source before migration; the reverse order preserves it.
HF02 closes this race for successful Continue by migrating after reload and
before field setup. Component and cold-save tests cover that order, but a real
two-peer trade/link battle, native SAVE and cold restart remain required before
claiming communication acceptance. New Game remains lazy and needs a separate
reachability test.

`sgp13.test_event_flags` executes the compiled helper with synthetic data.
`sgp13.test_event_flags_rom` additionally executes private native Check/Set/Clear,
SetVar, FieldSystem_VarGet, the real coordinate-event reader, map/daily resets,
initialization, original getters and the native Continue caller under Unicorn.
Set `SGP_EVENT_FLAGS_ROMS` to a JSON `EN`/`IT` path map. These tests
use explicit reload, checksum-bookkeeping and SDK-reset seams. They do not prove
physical flash persistence, rendered error presentation, Android cold Continue,
or Mew/Sinjoh gameplay; those require the separate candidate acceptance run.

Runtime owns `023CF900..023CFEFF` (the formerly unused shiny spare compartment):
912 compiled bytes before `023CFE80`, three guarded native trampolines through
`023CFECA`, and the delegated loader pointer at `023CFEF0`. No save address moves.
Native game instructions are copied only from the guarded private input at build
time and are never shipped as source assets.

The 3 November 2026 component campaign composes the complete UI stage from the
exact V4 inputs and obtains EN `c2b5e59b…e9cfb` and IT
`2eb93ee0…6cda`; both pass independent cartridge readback and installed-ARM
HF01 migration/SetVar/VarGet execution. Eight preserved-copy raw-save cycles
also pass Continue, native SAVE, process exit and cold Continue under both
candidates: zero-tag saves without Plus, with Plus and with expanded Bag, plus
an HF01 save. The bounded full audit preserves profile, party, boxes, daycare,
native/expanded Bag and Chatot; original fixtures remain byte-identical. This
closes component and headless persistence acceptance, not rendered gameplay:
representative gates/recording and the connected-device run remain separate
levels before release. The same is true of the two-peer communication matrix;
the retained HF01 ROMs must not be described as universally protected on first
upgrade merely because ordinary field loading often accesses a high flag early.
