# Training rules and journal core

This folder contains the freestanding production C rules for the proposed native
training integration. It does not install hooks, edit Pokémon, debit the Bag,
read clocks or write flash. Native adapters must perform those operations through
validated game APIs. No ROM or save fixture is required for these core tests.

Run from the repository root:

```sh
python3 -m unittest discover -s source/features/training/test -v
```

The tests compile and call the actual C through ctypes. The ARM test compiles the
same sources as one translation unit for ARM946E-S Thumb and runs the existing
object loader, which rejects external symbols, external data and unsupported
relocations. It requires Clang; a missing or unusable compiler fails this suite.
The checked flags are in `test/test_arm.py`. No libc, heap or EABI division helper
is used. Byte copying and bounded quotient loops deliberately prevent Clang from
synthesizing runtime calls. Code size varies with compiler/flags; reserve ownership
and runtime loading belong to the successor builder.

## API and transactions

`training.h` is the public API. All public identifiers use `sgp_train_` or
`SGP_TRAIN_`. Values use explicit 8/16/32-bit types and unsigned 64-bit clock
seconds. Callers must provide correctly sized buffers. Struct input and output
buffers must not overlap; six-value IV/EV input/output arrays may be identical.
Except the documented record selection metadata, rejected operations leave output
arguments unchanged. Treat `NO_CHANGE` as no transaction and no payment.

| API | Responsibility |
| --- | --- |
| `iv_preview`, `payment` | Preview exact 0–31, Silver one-stat 31, Gold all 31 and one-cap cost; validate funds without debit. |
| `ev_delta` | Safe signed delta on one selected stat, including over-total old Pokémon. |
| `ev_allocate` | Validate a complete, explicit six-stat target before writing any output. |
| `mode_fits` | Strict individual-Pokémon predicate for a proposed policy. |
| `stat_from_ui` | Convert HP/Atk/Def/SpA/SpD/Speed to stored HP/Atk/Def/Speed/SpA/SpD. |
| `job_validate`, `project`, `advance`, `switch_clock` | Validate jobs, project deferred results and reconcile bounded elapsed seconds. |
| `identity`, `withdraw` | Match serial/PID/OT/species and compact two jobs with native withdrawal. |
| `defaults`, `encode`, `decode`, `select` | RAM-only defaults and canonical little-endian journal handling. |
| `queue_reward`, `reward_delivered` | Atomically queue claims without overflow and acknowledge successful native delivery. |

The table omits the common `sgp_train_` prefix. Status enums distinguish invalid
input, egg rejection, unchanged result, insufficient funds, overflow and identity
mismatch. Native adapters must validate nonempty, non-egg, checksum-valid Pokémon
for every service. The IV preview accepts explicit egg/checksum flags; EV arrays
carry no Pokémon metadata and require that validation before calling them.

IVs are real stored values. The native transaction must revalidate identity and
payment, mutate and read back a temporary native Pokémon copy, then debit and copy
back without yielding; recalculate party stats and preserve moves, HP semantics
and unrelated data. Cancellation simply does not commit the preview.

Legacy policy 0 permits native vitamin gains to 100/stat and other gains to 255/stat,
with 510 total. Classic 1 permits 252/stat and 510 total. Unlimited 2 permits 252/stat
and 1512 total. Positive gains never reduce old 253–255 values; negative deltas only
reduce the selected stat, clamp at 0, and remain safe even above the chosen total.
Explicit complete allocations always cap each target at 252. Switching policies
requires a storage-wide scan using `mode_fits`; the predicate alone is not a scan.

## Course semantics

Each active job tracks a nonzero deposit serial, PID, OT and species 1–493. Clock 0
is accumulated active-play seconds; clock 1 is RTC seconds. The native adapter
provides successful readings and handles unavailable RTC data without advancing.
It must accumulate play time independently of the native capped IGT display.

Level courses earn one level per 7,200 seconds, EV courses 32 points per 3,600
seconds. EV courses affect only the selected stat, require targets that fit the
policy, and finish at the exact target. Combined courses finish when both targets
are reached. Credit saturates at their required duration. Backward clock changes
award zero and reanchor; positive jumps are allowed. Switching clocks first
settles the old reading, preserving all partial credited seconds, then anchors
the new source. Repeating an identical reading awards nothing twice.

Projection reads the baseline plus total credited time; it does not modify
BoxPokemon, experience, steps, breeding state or moves. Both supported versions therefore require
both settled-quanta fields to remain zero. Native retrieval must apply the final
projection once, preserve the current moveset, and move/clear jobs with the native
slots. Level-to-experience conversion, preservation of the within-level remainder,
and enrollment settlement of previously earned walking growth are adapter work.
Level-only jobs retain any baseline EVs, including 253–255; disabled EV targets
and rates are zero, with stat 255. EV-course target arrays preserve unselected EVs.
Inactive job records are entirely zero. Only successful native withdrawal should
commit the corresponding job compaction.

## Journal version 2, with version 1 read compatibility

Validated v1 records remain readable: their old fields retain the same offsets,
and the new shiny state defaults to Classic. Encoding writes v2. In v1, flags
and all 28 bytes at 0xE0 must be zero. In v2, SHINY_ONLY permits hunt persistence
while training stays inactive: Legacy policy, no jobs/claims/pending rewards.
Explicit training activation clears the flag before the normal historical reward
census. Shiny fields occupy bytes 224–232; bytes 233–251 remain canonical zero.
Unknown future versions are refused.

The 256-byte format is manually serialized, never a raw C struct. CRC32 uses the
standard reflected polynomial 0xEDB88320, initial/final XOR 0xFFFFFFFF, over bytes 0–251.

| Offset | Contents |
| --- | --- |
| 0x00 | `TNR1`, u16 version 2, u16 length 256 |
| 0x08 | u32 native generation, u16 native-main CRC16, u16 flags (0 or `SHINY_ONLY` = 1) |
| 0x10 | u8 policy, default clock, initialization version 1, zero |
| 0x14 | u32 next deposit serial, nonzero and greater than active job serials |
| 0x18 | u64 accumulated active-play seconds |
| 0x20 | u64 last observed RTC seconds |
| 0x28 | u32 milestone claims; badge bits 0–15, first League 16, first Red 17 |
| 0x2C | u32 League completions seen |
| 0x30 | u16 pending Silver, u16 pending Gold; each 0–999 |
| 0x34 | Twelve zero bytes |
| 0x40 | Job 0, 80 bytes |
| 0x90 | Job 1, 80 bytes |
| 0xE0 | u32 shiny RNG; u16 target; u8 chain, mode, initialized; 19 zero bytes |
| 0xFC | u32 CRC32 |

Job offsets: serial/PID/OT at 0/4/8, species 12, active 14, clock 15, kinds 16,
start/target levels 17/18, stat 19, baseline experience 20, enrollment steps 24,
level quanta settled 28, clock anchor 32, credited seconds 40, six baseline EVs 48,
six target EVs 54, EV period 60, EV points 64, zero u16 at 66, EV quanta settled 68,
and zero u32 fields 72/76. Kind bits 1/2 select level/EV courses. Active job serials
cannot collide; exhausted serial space requires an explicit integration decision,
never wrapping or silently recycling a serial.

Only uniformly 00 or uniformly FF records are erased. Valid matching records must
pass CRC, range, reserved-byte and job checks and match both native generation and
main CRC. Selection prefers matching primary, then matching mirror; it never
imports another generation. Two erased records produce Legacy/RTC defaults in RAM
without writing. Corrupt, mismatched or foreign records leave state output alone.
Unknown magic/version/length is foreign and must never be overwritten. Selection
sets `writable=0` if either copy is corrupt or foreign, even when the other copy
loads successfully; this conservative result requires the integration coordinator
to resolve ownership/recovery before any write. It is not a flash write permission
by itself. Primary/mirror buffers must belong to the native bank being considered;
the core does not discover banks or arbitrate native saves.

Reward additions exceeding 999 reject atomically; they do not saturate or set the
claim bit. Duplicate one-time claims and repeated League counters do nothing.
Repeat rewards use claim 255 and require a larger observed League counter.
`reward_delivered` must run only after successful atomic native Bag delivery;
a full Bag retains the pending queue. The native save coordinator must persist
Bag state, Pokémon and this journal consistently in the same generation.

## Validation boundary

Host and ARM compile tests establish pure arithmetic, serialization and object
constraints. They do not establish hook correctness, save-sector ownership, native
Pokémon transactions, payment atomicity, breeding behavior, RTC/IGT behavior,
move preservation, UI or raw-save compatibility. Those require the full adapter,
EN/IT ROM checks and normal Continue/save/cold-restart testing on copies of old
saves, including saves without Plus data and with Plus/expanded Bag data.
