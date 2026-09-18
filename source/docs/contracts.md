# Sacred Gold Plus 1.2 — internal contracts

Five contracts that the rest of the project depends on. Each one states the rule, why it is
written that way, and which public file implements it. Addresses are ARM9 RAM addresses without
the Thumb bit; sizes are decimal unless prefixed with `0x`.

---

## 1. Save chunk

Sacred Gold Plus 1.2 keeps its own options in a 16-byte block that every feature reads and that
the game's normal save cycle writes. The block does not extend, move or rewrite any existing
save structure.

### In RAM

The 16 bytes live at `0x023D8710`, at offset `+0x10` of the 32-byte runtime state at
`0x023D8700`. A feature that wants to read or write an option touches the RAM copy, never the
32-byte working buffer used while loading and saving: that buffer is internal and is rebuilt on
every save.

| off | field | type | domain | meaning |
|---:|---|---|---|---|
| `+0x0` | `magic` | u16 LE | `0x5347` | block identity |
| `+0x2` | `version` | u8 | `1..2` (currently 2) | chunk layout version |
| `+0x3` | `plus` | u8 | `0/1` | Plus difficulty on trainers |
| `+0x4` | `wild` | u8 | `0/1` | Plus levels on wild encounters |
| `+0x5` | `over100` | u8 | `0/1` | reserved for a later level cap; accepted, currently ignored |
| `+0x6` | `anim` | u8 | `0/1` | procedural idle animation |
| `+0x7` | `npc` | u8 | `0/1` | NPC movement smoothing |
| `+0x8` | `wifi_server` | u8 | `0..3` | last online-service choice |
| `+0x9` | `peak` | u8 | `1..cap` | highest level ever owned; never decreases |
| `+0xA` | `reserved0` | u8 | `0` | must stay zero |
| `+0xB` | `reserved1` | u8 | `0` | must stay zero |
| `+0xC` | `reserved2` | u32 LE | `0` | must stay zero |

Every switch is a whole byte, not a bit. Two features writing two different fields therefore
cannot corrupt each other through a non-atomic read-modify-write.

The first bytes of the surrounding state are the operational copies the hot hooks read:
`+0x00` active trainer flag, `+0x01` active wild flag, `+0x02` level cap, `+0x03` load status,
`+0x04` initialisation guard (`0x5A` once the boot-time read has completed), then two u32
diagnostic counters. The active flag sits at offset 0 on purpose: the trainer hook reads a
single byte there, so a zeroed or never-initialised region reads as 0 and the game behaves
exactly like 1.1.

### On disk

Sector **47** (`0x2F000`) and its mirror at sector **111** (`0x6F000`), 32 bytes each: 16 bytes
of payload followed by a 16-byte footer. Those sector ranges are outside every structure the
game itself uses, and were measured as erased (all `0xFF`) across six different real saves
rather than deduced from a table.

The footer has the shape of the game's own array footer — `{u32 magic; u32 saveno; u32 size;
u16 idx; u16 crc}`, with the CRC computed over `size + 14` bytes by the game's own CRC16
routine — but a different magic: `'SGP2'` (`0x32504753`) instead of the game's. One of our
sectors can therefore never be mistaken for a game chunk, nor a game chunk for ours.

Reading happens once, at boot, from a hook inside the game's save-init path: after the game has
read and validated its own save, and before the title screen. Writing happens at the tail of
the game's save routine, on every successful save, keyed on the routine's original success
value. A feature that changes a byte of the chunk does nothing else to persist it; there is no
"write now" entry point and none is needed.

### Validity

Checked on every read, before the content is used at all:

```
footer.magic == 0x32504753
footer.crc   == CRC16(payload, 30)
magic        == 0x5347
1 <= version <= 2
plus, wild, over100, anim, npc in {0, 1}
wifi_server <= 3
reserved0 == reserved1 == reserved2 == 0
1 <= peak <= cap
```

`footer.size` and `footer.idx` are not checked separately: they sit inside the 30 bytes the CRC
covers, so a correct CRC has already verified them.

Three outcomes, recorded in the load-status byte:

| case | status | behaviour |
|---|---|---|
| chunk absent (a 1.1 save) | `1 ABSENT` | every byte 0 except `peak = 1` **and `npc = 1`** — see below |
| chunk valid | `2 VALID` | applied as written |
| chunk present, an invariant violated | `3 REJECT` | the chunk is neither zeroed nor rewritten, not even on the next save; the game runs in 1.1 mode |

"Chunk absent means behave exactly like 1.1" is the rule that makes the whole arrangement safe
to ship. It has **one declared exception**, and the exception is in the shipped binary: with the
chunk absent, `npc = 1`, so NPC movement smoothing is on from the first field frame of a 1.1
save. This is a deliberate decision, not a default that leaked: the smoothing changes no game
state — it only raises how many NPC models the field loads per frame — so it is reversible from
the options page at any moment and it cannot make a save behave differently if it is turned off
again. Every other byte is 0, and every option that *does* change game state (Plus difficulty,
Plus wild levels, the level cap) stays off until the player asks for it.

Read the sentence literally, then: a 1.1 save opened in 1.2 is byte-identical to 1.1 **on disk**,
and behaves like 1.1 in everything that the save records. It is not frame-identical on the field.

Any other feature that wants a default of "on" sets that byte the first time 1.2 writes a chunk
of its own — from the options page, or on a new game — and from then on the byte stays 1.

**Implemented by** `source/features/native-core/sorgenti-v-finale/salva_blob.c` (the two `strb`
that write `peak` and `npc` when the chunk is absent).

### One accessor, no caching

Every feature reads its flag through the shared accessor, on each use, and never caches the
value at init. The accessor checks the guard byte and the load status first, returns 0 for
`REJECT` and for "not read yet", and only then reads the byte. Before it existed, each feature
wrote its own guard and the guards did not all mean the same thing. Caching at init is also
wrong for a second reason: the options page can change a byte while the game is running.

**Implemented by** `source/sgp12/chunk.py` (format, offsets, footer and CRC, encode/decode with
the invariants) and `source/features/native-core/sorgenti-v-finale/sgp_chunk.h` (the on-target
struct definitions and the shared accessor). Written into the ROM by
`source/sgp12/blocchi/plus_chunk.py`.

---

## 2. Overlay patched in place

HGSS keeps most of its code in BLZ-compressed ARM9 overlays. Sacred Gold Plus patches bytes
inside an overlay by decompressing it, editing the image, recompressing it, and writing the
result back **into the same file slot, without moving it a single byte**. Relocating an overlay
to the end of the ROM is refused.

### Why relocation is refused

The NitroSDK copies the FAT into RAM once, at boot, but re-reads the overlay table (y9) entry
from the cartridge on every overlay load. A run that resumes from a savestate therefore carries
a frozen FAT while still reading a fresh y9 entry. Anyone who relocates an overlay **and**
changes its size makes the game read the new size from the old address: the compressed stream's
trailer lands in padding, and decompression produces code that does not exist.

Six runs on the same base, the same savestate and the same input script make the mechanism
plain:

| what was done to an overlay | result |
|---|---|
| original battle overlay relocated to the end, FAT updated | alive, frame log identical |
| original field overlay relocated to the end | alive, identical |
| recompressed field overlay (same size) relocated to the end | alive, identical |
| recompressed battle overlay (larger) relocated to the end | ARM9 exception vector |
| decompressed battle overlay, flag cleared, at the end | ARM9 exception vector |
| original battle overlay relocated **and the old copy erased** | ARM9 exception vector |

The last row is the decisive one. Relocating without erasing the old copy works; erasing it
kills the game. The game never reads from the new address at all — the first three rows were
not evidence that relocation works, only that the original bytes were still where they had
always been. The field overlay happened to recompress to exactly its original size, which is
why nothing broke for it and why the picture was confusing for a day.

Two consequences hold for the whole project, not just for overlays:

- a run from a savestate does not see changes to the FAT, so anything that moves a file in the
  ROM must be tested from a cold boot;
- "it does not work from a savestate" is not the same statement as "it does not work".

Patching in place has neither problem, and does not make the ROM grow.

### How the in-place patch is built

To stay inside the slot the project needs a better compressor than the one the game shipped
with. Ours does an **optimal** analysis — a minimum-cost path over the token stream, with the
cost counted in eighths of a byte (a literal 9/8, a match 17/8; the 1/8 is the flag bit) —
rather than the greedy longest-match choice:

| overlay | original | greedy | optimal | slot |
|---|---:|---:|---:|---:|
| field | 42,964 | 42,964 | 42,696 | 43,008 |
| battle | 162,296 | 162,464 (does not fit) | 161,556 | 162,304 |

The cut point between the raw prefix and the encoded body is then chosen so the stream hits a
**target** size exactly, computed in one pass from the dynamic-programming tables without
emitting the stream. Targeting the original size means the FAT entry and the y9 entry are
rewritten with the values they already had, and the only region of the ROM that changes is the
overlay body. The header — used size, capacity, CRC16 — does not change, and the file does not
grow. If a future stream did come out shorter, the FAT end offset and the y9 size word would
change by four bytes each, the freed bytes would return to `0xFF`, the header CRC would be
recomputed only if something inside the first `0x15E` bytes actually changed, and the ROM would
still not grow.

Two further rules of the applier:

- **An address does not identify an overlay.** Several overlays can be resident at the same RAM
  address. Every patch therefore carries one or more content guards, and automatic overlay
  selection refuses unless exactly one candidate matches. A patch is idempotent by
  construction: reapplying it is a rejection, because the preimage is gone.
- **A decoder that does not simulate in-place decompression is not a verification.** BLZ
  decompresses backwards, in place, with two pointers that must never cross. A decoder working
  on a separate buffer will happily accept a stream the game cannot decode — that exact failure
  cost a day of work. The project's decoder therefore runs on a buffer as long as the final
  image, with the same two pointers, and refuses the moment the destination drops below the
  source. On a good stream the minimum margin is exactly 0.

### The size check that catches a regression

Every block applier ends with a gate asserting that the produced ROM is **exactly as long as
the base it was built from**, and the independent readers assert it again. The overlay applier
additionally refuses to relocate unless an explicit opt-in flag is passed, which exists only so
the measurement above can be repeated. If a new stream ever fails to fit the slot, the order of
remedies is: combine several patches into one pass so the stream is recompressed once; recover
bytes from dead padding inside the image; and only as a last resort relocate — which then has
to be tested from a cold boot and makes the ROM grow.

**Implemented by** `source/sgp12/overlay.py` (slot geometry, content guards, in-place write) and
`source/sgp12/blz.py` (the codec: backward in-place decoder, optimal compressor, exact-size
targeting), with the standalone applier and independent re-reader in
`source/features/overlay/tools/`.

---

## 3. Wi-Fi connection slot

The DS firmware holds three connection settings. The game picks one for each online service.
Sacred Gold Plus lets the player nominate a slot for the online services and then applies this
rule, in this order:

1. Each online service has a **designated slot**: the slot the player chose for the general
   online services, and a fixed slot for Mystery Gift.
2. If that designated slot **is configured in the firmware**, it is used.
3. If it is not, fall back to the **first configured slot**, scanning 1, 2, 3 in order.
4. If **no** slot is configured, do nothing: the game keeps its original behaviour. There is
   nothing to force, and forcing an unconfigured slot would be worse than the default.

The option itself is read fresh from the save chunk through the shared accessor on every
connection, never cached at install time, because the options page can change it mid-game. A
chunk the loader did not validate reads as 0, which means "original behaviour".

Before the fallback existed, a designated-but-unconfigured slot simply left the selector
untouched — the connection then used whatever the game would have used, silently ignoring the
player's choice. The fallback was added as one helper and three lines in the selector function;
the external state layout and its version did not change, only the internal logic.

### Cache maintenance is part of this contract

The hook installer writes an ARM branch word **into the RAM copy of an overlay**, at runtime.
On the ARM946E-S the data cache is write-back and the instruction cache is separate, so a plain
store leaves the word dirty in the D-cache while the CPU may still fetch the old instruction
from the I-cache. The hook can then fail to fire, intermittently. The overlay loader invalidates
the I-cache *before* our write, so it does not cover us.

Every runtime write of an instruction therefore goes through one helper that does the store, a
data-cache flush of that word and an instruction-cache invalidate of that word, as a single
gesture nobody can half-forget. This is a project-wide rule, not a Wi-Fi habit.

melonDS does not model the ARM9 caches, so **no run on the test bench can observe this**. The
automated test can only assert that both maintenance calls are present in the compiled blob;
the behaviour itself is only distinguishable on real hardware.

### One declared deviation: stack alignment in the two ARM veneers

Every Thumb trampoline in this project pushes a multiple of 8 bytes, so that the C function it
calls is entered with the stack 8-byte aligned, as AAPCS requires. The two ARM veneers of this
contract (`0x023DA000` and `0x023DA020`) do not: they push five registers, 20 bytes, and enter
`sgp_wfc_nibble` with `sp ≡ 4 (mod 8)`. It is harmless in the shipped build — the callees are
Thumb-1 `-Oz` and emit neither `LDRD`/`STRD` nor VFP, the only instructions that would care —
and melonDS would never show it either way. It is written down here because it is the single
place in the project where the rule is broken, and because a future recompilation with different
flags could start to care. Fixing it means changing the veneer bytes, so it belongs to a release
that rebuilds the Wi-Fi blob, not to a patch release.

**Implemented by** `source/features/native-core/sorgenti-v-finale/wifi_slot4.c` (service
recognition, slot-configured probe, fallback, selector write) and
`source/features/native-core/sorgenti-v-finale/sgp_chunk.h` (the shared accessor and the
instruction-write helper). Written into the ROM by `source/sgp12/blocchi/wifi.py`.

---

## 4. EV/IV guide

### Where it lives

The guide is a small native component in the same static region as the EV/IV reader, hosted by
the Pokémon Summary overlay. It presents three text panels on the touch screen, in the game's
own font, over the Stats/Skills page; the top screen stays in the existing parameters/EV/IV
mode. It is opened with START or the equivalent on-screen target, and it borrows background
layer 4 — saving the characters and the tilemap it covers and giving them back before the
summary is re-enabled.

### What it reads

Its host hands it everything it needs: background and window ownership, language, font, a pixel
budget and already-normalised input. It reads the summary's own state through the overlay
manager (page, mode, arguments, position) rather than from hardcoded pointers, which are
dynamic; it reads raw key state and touch coordinates from the system input block; it uses the
game's font 0 on loan, without changing its reference count or access mode; and it draws from
its own encoded strings, measured against the game's own width table.

### What it must not touch

- **Save data.** The component never receives a save-data pointer and writes no "already seen"
  flag into the save.
- **The new game flow.** It does not call the intro sequence, does not reuse its windows or its
  heap, and does not attach itself to that sequence's exit. Hosting the same panels before a new
  game is a separate integration with its own contract.
- **The summary's own buffers.** The existing windows and their pixel buffers still belong to
  the summary: the guide owns only its own window, its own bitmap and its restore copy, and
  frees only those. It must not call the summary's page-window teardown, its skills renderer,
  its init or its exit to restore the view — any of those would destroy the EV/IV mode or the
  ownership. On the way out it waits for its own transfers to finish, restores the borrowed
  characters, the tilemap and the exact visibility mask, and only then releases what it owns,
  leaving the host's state unchanged. Input is consumed entirely while the guide is open and is
  released with a guard, so that B does not also close the summary and a touch on the panel does
  not activate whatever sits underneath.

### What the shipped 1.2 build does

The shipped 1.2 ROMs have the **automatic on-screen label turned off**: 96 machine bytes are
replaced inside the guide entry point at `0x01FF8A1A`, identical in EN and IT. START and the
touch target still open the three panels normally. Nothing else moves: no trampoline, no intro
template, no text region, and no part of the 1.2 ARM9 reserve — the patched area is the static
region inherited from 1.1.

This is a surgical byte patch, not a recompilation, and deliberately so. An earlier attempt
rebuilt the component from source and replaced the whole code region; on the test bench that
build faulted the ARM9 as soon as START was pressed — reproduced even when rebuilding the source
with no changes at all, so the recompilation itself was the hazard in this environment, not the
edit. That attempt was discarded.

**Implemented by** `source/native-guide/` (the contract, the presentation spec, the sources and
the independent verifiers) and `source/features/guide/`, applied by
`source/sgp12/blocchi/guida.py`.

---

## 5. Rare Candy reuse

### The hook

One hook, six bytes, in the static ARM9 at `0x02081E96`: the tail of sub-state 6 of
`PartyMenu_ItemUseFunc_LevelUpLearnMovesLoop`. A `BL` into `sgp.caramelle` (4 bytes) plus
`pop {r3,r4,r5,pc}` (2 bytes) replace `cmp r0,#0 / beq / movs r0,#9`. The ten bytes at
`0x02081E9A..0x02081EA3` stay written as they were but become unreachable.

The hook sits there and nowhere else because the Rare Candy never passes through the 1.1
"use again" path: `ItemId_GetPartyUseType` gives it type 2, the table at `0x020812E8` installs
`PartyMenu_ItemUseFunc_LevelUp`, and that chain ends in the loop above, which returns
`BEGIN_EXIT` on its own. By the time the hook runs, the text is closed, the stats window is
closed, new moves have been handled, and the evolution species is already in `args->species`:
no state is half-finished.

### The context it runs in

The routine is entered with `r0 = args->species`, `r1 = args` (`PartyMenuArgs`) and
`r4 = PartyMenu`, and what it returns is what the game's own function returns. It **does the
whole job of the code it replaced**: it writes `args->selectedAction` itself and returns the
state itself, so the "leave" case is not an imitation of vanilla — it *is* vanilla.

It reads `PartyMenu` and `PartyMenuArgs` and calls six game functions whose addresses are
identical in EN and IT (measured on four ROMs: 1.1 and 1.2 for each language). It never reads or
calls `borsa.text`, the 1.1 bag code: that region is frozen by the 1.1-zone rule, and the
re-entry sequence — clear window 34, print message 33, reset the cursor palette — is repeated
here with its own literals so that the two functions can die separately.

### The rule: ITEM_NONE and evolution

Staying in the party menu is the exception, not the default. The routine stays only when every
one of five preconditions holds, and **leaves exactly as vanilla does** otherwise:

| gate | leaves with |
|---|---|
| an evolution is queued (`args->species != 0`) | `BEGIN_EXIT`, action **9** — the evolution scene is the game's, untouched |
| `args->itemId == ITEM_NONE` | `BEGIN_EXIT`, action 0 — this is the relaunch after "forget a move": re-entering without an item is the one way this could hang |
| `args->context != PARTY_MENU_CONTEXT_USE_ITEM (5)` | `BEGIN_EXIT`, action 0 — the same relaunch, seen from the other side |
| the bag no longer holds the item | `BEGIN_EXIT`, action 0 — the last candy returns you to the Bag |
| the party slot is not `< count` and `< capacity` | `BEGIN_EXIT`, action 0 — the guard `0x02074644` applies to itself |

Level 100 needs no gate: on re-entry `CanUseItemOnMonInParty` refuses, the game prints "it will
have no effect" and leaves through the existing 1.1 code. `selectedAction` is always written,
never left at whatever it held.

**Implemented by** `source/features/caramelle/` (sources, applicator, independent re-reader,
Unicorn bench and mutants), applied by `source/sgp12/blocchi/caramelle.py`.

---

## See also

- `docs/test-bench.md` — the headless runtime harness and the gates that judge a run.
- `docs/arm9-reserve-map.md` — the ARM9 reserve layout every native block allocates from.
- `docs/rebuilding-1.2.md` — building a 1.2 ROM from your own 1.1 base.

## Expanded Bag (1.2.1)

The main pocket has **252 distinct slots, 42 pages of six**. Pocket-ID order
capacities are `[252, 42, 30, 102, 66, 12, 30, 60]`; quantities remain 999,
or 99 for TM/HM. The complete contract and tests live in
[`features/capacita-borsa`](../features/capacita-borsa/README.md).

`Save_Bag_sizeof()` remains **1948 bytes**. All existing save-array offsets,
registered items and legacy cheat addresses remain fixed. Runtime Bag objects
use 2380 bytes and every pocket getter, slot enumerator, view, copy, registered
item operation and reorder operation routes to that representation. Native
Add/Take/Has/Quantity functions retain their original implementation.

The 108 extra slots use two 452-byte records per save bank, in reserved flash
sectors **48 and 112**, at offsets 0 and 0x200. These do not overlap the native
extra-save arrays or SGP options sectors47/111. Each record contains format1,
the **native save generation and main-block CRC16**, and its own CRC32.

**The extension can never stop a save from loading.** Each copy is classified on
its own; a copy that is not usable is ignored, and if no copy is usable the
extension is ABSENT and the game opens with its 486 native slots. Sectors that
hold foreign bytes — zeroed by a converter, a flashcart backup or a save editor —
are a normal, silent case, not a failure. **No path in the load opens the native
save-read-error screen.** The outcome is recorded in `stato_caricamento`, a
diagnostic word at `0x023DE9C0` (`CapState + 0x12C0`), first matching rule wins:

| condition | inventory | `stato_caricamento` | `owned` |
|---|---|---:|---:|
| primary record matches this save | 594 slots, from the primary (mirror not read) | 1 | 1 |
| mirror record matches this save | 594 slots, from the mirror | 2 | 1 |
| a copy could not be read from flash | 486 native slots | 5 | 0 |
| a copy is intact but from another generation | 486 native slots | 3 | 1 |
| a copy carries our magic but is damaged | 486 native slots | 4 | 0 |
| a copy carries bytes that are not ours at all | 486 native slots | 6 | 0 |
| both copies erased (0xFF) | 486 native slots | 0 | 0 |

`rejected` (`CapState + 0x0C`) is **diagnostic only**: "the flash could not read
the bank we loaded from". It blocks nothing, and in particular it does not veto
the next save: the load reads the *active* bank while the save writes the
*inactive* one, and an unreadable destination reports itself through the two
ownership reads (`stato_scrittura` 4). It used to veto the whole session, so one
unreadable sector silently cost the 108 extra slots.

**The extension can never stop a save from being written either.** Before any
write each destination must independently be *claimable*: erased (0xFF),
**uniform** — 452 identical bytes, as left by a converter that zeroes unused
sectors or by a card wiped with a fill pattern — or already ours. Foreign bytes
that are not uniform are never replaced: neither copy is written and
`stato_scrittura` stays 2. `cap_record_create` sanitises the inventory first — an
extension cell with quantity 0, with id 0 or id above 536, or with a quantity
over its pocket limit, is **emptied in place** (`{0, 0}`), nothing is shifted,
and every other cell keeps exactly the index it had in the Bag. The sanitised
cells are written back into the runtime Bag as well (extension cells only; the
486 native ones are never touched), because `{id, 0}` still makes its pocket
answer "not empty" and an id above 536 can still reach the item table from the
menu. The native pocket compaction pushes a spent slot to the end of the pocket
*keeping its id*, so `{id, 0}` lands inside the extension by normal play; writing
it produced a record our own validator rejected, and the save then failed for
ever. The readback after the write is a **byte-by-byte comparison of the 452
bytes written**, not a second validation of the domain, for the same reason.
`stato_scrittura` (`CapState + 0x12C4`) records what happened: 0 not attempted,
1 both copies written and verified, 2 foreign data in a destination (nothing
written), 3 nothing usable written, 4 flash unreadable (skipped), 5 only one
copy verified.

**When `stato_scrittura` stays 2** the extension is no longer written at all,
so the 108 extra slots are lost at every reload and the game silently falls back
to its 486 native ones. That word at `0x023DE9C4` is the only indication. The
remedy is manual and is performed on a *copy* of the save: with a hex editor,
restore to `0xFF` (or zero) the 452 bytes at offsets `0x30000`, `0x30200`,
`0x70000` and `0x70200` of the 512 KB `.sav` — a uniform destination is
claimable — and the next save writes the extension again. Nothing else in the
file may be touched.

**Whatever happens, the vanilla save runs and its own result is returned.** The
hook never answers `WRITE_STATUS_TOTAL_FAIL` on its own: the touch-save app
discards that value and prints "saved the game" regardless, so a refusal by the
extension lost the whole session silently. The price is bounded: when the
extension is not written the vanilla save still commits a new generation, so the
old record becomes stale and the next load degrades to 486 slots — the 108 extra
slots, rather than everything played since the last successful save.

An interrupted owned record can be retried. A matching mirror recovers an erased
or corrupt primary record.

Existing 1.1/1.2/1.2.1/earlier 1.2.2 saves import with zero extra slots. Opening a save
with no extension does not write flash. **Older ROMs cannot access extra slots;
saving in an older ROM changes the native generation and invalidates the old
extension association. Returning to 1.2.2 then imports only the native inventory.**
Keep the last save made in 1.2.2 when changing ROM versions. This is input
compatibility with older saves, not full bidirectional inventory compatibility.
Load the normal in-game save after a ROM update: emulator savestates also retain
old executable RAM and are not an update mechanism.
