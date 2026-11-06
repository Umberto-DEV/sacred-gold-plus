# Expanded Bag capacity

This module is retained in the **1.3.1** build chain. It adds distinct-item slots;
stack limits remain 999, or 99 for TMs/HMs.

| Pocket | Native slots | Expanded slots | Six-row pages |
| --- | ---: | ---: | ---: |
| Items | 165 | 252 | 42 |
| Medicine | 40 | 42 | 7 |
| Poké Balls | 24 | 30 | 5 |
| TMs/HMs | 101 | 102 | 17 |
| Berries | 64 | 66 | 11 |
| Mail | 12 | 12 | 2 |
| Battle Items | 30 | 30 | 5 |
| Key Items | 50 | 60 | 10 |

The field screen allocates names/IDs for 252 items. The sixth item on page 42
can be selected, used, discarded and filled through normal add functions.
The battle view enumerates through the extended getter.

## Architecture

- `sorgenti/core.c`: 594-slot representation, native-layout import/export and
  per-slot synchronization between direct menu writes and cheat addresses.
- `sorgenti/runtime.c`: routes all Bag APIs, including private battle/trade
  objects, registration and sorting; `Save_Bag_sizeof` remains unchanged.
- `sorgenti/journal.c`: 432-byte extension plus 20-byte metadata/checksum,
  primary/mirror per flash bank, bound to native generation and main-block
  CRC 16, prepared before native commit.
- ARM9 reserve: `0x023DBF00–0x023DEB00`; state at `0x023DD700` (4808 bytes).

## Load and write behavior

Each copy is classified independently. An unusable copy is ignored; if none is
usable, the extension is absent and loading uses 486 native slots. Foreign bytes
left by converters, flashcart backups or save editors are handled silently.
No extension-load branch invokes the native read-error screen. The first matching
row wins; `stato_caricamento` is at `0x023DE9C0` (`CapState + 0x12C0`).

| Condition | Inventory | `stato_caricamento` | `owned` |
| --- | --- | ---: | ---: |
| Primary matches this save | 594 slots from primary; mirror is not read | 1 | 1 |
| Mirror matches this save | 594 slots from mirror | 2 | 1 |
| Flash copy cannot be read | 486 native slots | 5 | 0 |
| Intact copy belongs to another generation | 486 native slots | 3 | 1 |
| Our magic, damaged record | 486 native slots | 4 | 0 |
| Foreign bytes | 486 native slots | 6 | 0 |
| Both copies erased (`0xFF`) | 486 native slots | 0 | 0 |

`rejected` (`CapState + 0x0C`) is diagnostic: the active bank failed a flash
read. It does not veto the next save, which writes the inactive bank. An unreadable
destination is reported separately by `stato_scrittura=4`. The former session-wide
veto could silently lose all 108 extra slots after one unreadable sector.

Each write destination must independently be claimable: erased (`0xFF`), uniform
(all 452 bytes equal), or already ours. A uniform sector may come from a converter
or clean card. Foreign nonuniform bytes are never replaced: neither copy is
written and `stato_scrittura` stays 2.

Before serialization, `cap_record_create` clears invalid extension slots in place
to `{0, 0}`: zero quantity/ID, ID above 536, or quantity above the pocket limit.
It preserves every other slot index and applies the same cleanup to the RAM
extension only; the 486 native slots are untouched. Native compaction retains the
ID of exhausted slots, so normal play can produce `{id, 0}` in the extension.
Previously this created a record rejected by its own validator, preventing future
extension writes. Leaving those records in RAM could also make an empty pocket
appear occupied or let an invalid ID reach the item table. Readback therefore
compares the exact 452 written bytes, rather than repeating domain validation.

`stato_scrittura` (`CapState + 0x12C4`, `0x023DE9C4`) is 0 not attempted, 1 both
copies written/verified, 2 foreign destination (no write), 3 no usable copy written,
4 unreadable flash (skipped), or 5 one copy verified.

If status 2 persists, extra slots disappear on reload and the game uses 486 native
slots without a message. The historical manual recovery procedure applies only
to a **disposable save copy**: set the 452 bytes at each of `0x30000`, `0x30200`,
`0x70000`, `0x70200` in the 512 KiB `.sav` to `0xFF` (or a uniform zero pattern),
leaving all other bytes intact. A later native save can claim these destinations.
This is a diagnostic repair procedure, not the normal update route; preserve an
unaltered backup before any manual save editing.

Native saving always runs and returns its own result. This hook never invents
`WRITE_STATUS_TOTAL_FAIL`: the touch-save caller historically discarded it and
showed success, silently losing the session. If the extension cannot be written,
the native save can still advance generation; the old extension becomes stale
and the next load falls back to 486 slots. Overlay 15 retains its original FAT slot
and compressed length, independently checked by in-place decompression. Readback
does not call the installer.

The [save contract](../../docs/contracts.md#expanded-bag-121) defines recovery and
compatibility. **Saving with an older ROM can make the extra slots unavailable on
re-upgrade.** Keep the newer raw save before any downgrade.

## Build and validation

```sh
python source/features/capacita-borsa/tools/compila.py --uscita source/sgp12/build/capacita_borsa
python -m unittest discover -s source/features/capacita-borsa/test -p test_core.py
python -m unittest discover -s source/features/capacita-borsa/test -p test_journal.py
python -m unittest discover -s source/features/capacita-borsa/test -p test_build.py
```

Class B inputs are `SGP_CAPACITY_ROM` (private final ROM),
`SGP_CAPACITY_BEFORE` (preceding stage) and `SGP_CAPACITY_BUILD` (compiled bundle).
`test_arm.py` executes modified native ARM functions in Unicorn: slot 252, private
copies, read failure, all 452 interrupted-write points followed by restart/retry,
corrupt/erased mirror, foreign data in either destination, uniform 00/AA SRAM,
the 36 primary×mirror combinations including failed reads, failed active-bank
read followed by inactive-bank save, valid-but-different readback, and invalid
extension slots `{id, 0}` / `id > 536`. It verifies that the tested ROM contains
the exact supplied `blob.bin`. `test_reader.py` mutates ABI, code, state, native
Bag size and UI counts.

The historical local melonDS fixture filled the first 251 main-pocket slots and
added a final item: page 42 was full, discard worked, native retrieval of a held
item restored it, and native SAVE/cold SRAM restart kept it in the sixth cell.
The re-exported SRAM matched the saved bytes exactly. This bounded fixture is
not universal save compatibility or fresh acceptance of the 1.3.1 ROM. See
[current validation](../../docs/ui-1.3.1-validation.md). ROMs, SRAM, dumps,
savestates and captures remain private.
