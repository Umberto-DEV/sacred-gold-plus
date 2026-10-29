# Native high event flags

The original high event flags `3F00..3FFF` address bytes beyond the native flag
array, inside Pal Pad. The shared native getter now redirects that entire bank
to reserved variables `415E..416F`. External script IDs, event objects and cached
object IDs stay stable, including Mew `3FC8` and its Sinjoh reader.

The 36-byte reservation is at SaveVarsFlags offsets `2BC..2DF`: exact four-byte
ASCII tag `HF01`, then a 32-byte bitmap. No save-array size, identifier, checksum
boundary, Training journal version or layout changes. The supported source and
field/event/Frontier archive census found no other owner of these variables.
The installer rejects literal uses in those three archives at any alignment,
checks pinned native routines and preserves the composed Training/Bag loader.
Future code using synthesized variable IDs or raw offsets needs a fresh review;
archive scans do not establish whole-program absence of indirect accesses.

An entirely zero reservation imports all 256 observable legacy bits once, before
the triggering Check/Set/Clear. The exact tag is written last. Recognized tagged
state is authoritative even if friend registration later changes Pal Pad. The
migration never repairs or writes Pal Pad: old event writes and friend data were
aliased, so their historical intent cannot be recovered reliably.

Foreign nonzero reservations and unknown/future tags are preserved and refused.
The composed load checks the boot-loaded arrays before Training/Bag load, then
checks successfully reloaded arrays again. FALSE propagates through the native
Continue loader (`020273B0`) to overlay 36, which requests `OS_ResetSystem(0)`
before field setup. One rejected Continue requests one reset; SDK synchronization
is not wall-clock bounded. A defensive high-bank access on foreign ownership
also resets without returning to the event. There is no migration or flash write
on either refusal path. New Game retains native whole-struct initialization and
lazy import after arrays are initialized.

Every ID outside `3F00..3FFF` retains the original getter through a guarded
trampoline, including native zero/low/temporary behavior. Some original hidden
item scans read malformed outlier IDs; this fix does not broaden bounds behavior.
The pre-existing release assertion/out-of-range behavior remains a separate issue.

Compatibility is forward only. An older ROM ignores the bitmap and may write
Pal Pad again; downgrade/re-upgrade event synchronization cannot be promised.
Mirroring flag writes back into Pal Pad would reintroduce the corruption.

`sgp13.test_event_flags` executes the compiled helper with synthetic data.
`sgp13.test_event_flags_rom` additionally executes private native Check/Set/Clear,
map/daily resets, initialization, original getter and the native Continue caller
under Unicorn. Set `SGP_EVENT_FLAGS_ROMS` to a JSON `EN`/`IT` path map. These tests
use explicit reload, checksum-bookkeeping and SDK-reset seams. They do not prove
physical flash persistence, rendered error presentation, Android cold Continue,
or Mew/Sinjoh gameplay; those require the separate candidate acceptance run.

Runtime owns `023CF900..023CFEFF` (the formerly unused shiny spare compartment):
compiled code before `023CFE80`, a 20-byte original-prologue trampoline there,
and the delegated loader pointer at `023CFEF0`. No existing address moves.
Native game instructions are copied only from the guarded private input at build
time and are never shipped as source assets.
