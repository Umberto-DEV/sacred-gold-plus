# Native training adapter

This **1.3.1** dependency installs the training core into the reserved 1.3 ARM9
compartment.
The guarded builder is `source/sgp13/training.py`; it consumes private EN/IT ROMs
and a build-time character map. No retail ROM, save or extracted asset is shipped.
Existing 1.2.5 sources and save identifiers are unchanged.

## Player entry points

- IV consultants in Violet and Blackthorn Marts: native party selection, current
  and target IVs, Silver (one IV to 31 or an exact 0–31), Gold (all six to 31), purchase and
  milestone rewards. Real IVs affect breeding and Hidden Power.
- Trainer inside the Route 34 Day Care at tile (4, 9): quick EV targets 0–252,
  free reductions/reset, policy/clock selection, enrollment and course status.
  The original Lady still handles deposit and withdrawal.
- The existing Pokégear Day Care Lady contact reports the active course's clock,
  projected level, selected EV/current target and whole-course remaining seconds.
  Its original subsequent growth and conversation branches are retained.

The visible stat order is HP, Attack, Defense, Sp.Attack, Sp.Defense, Speed.
Touch menus use the native field-menu lifecycle. Longer digit lists use the
native scrolling list. Party selection restores the overworld before drawing
messages; dialogue is explicitly paginated for the two-line native window.
Unlimited requires confirmation. No-change, decline and failed payment do not
consume currency. Courses are free; ordinary Day Care withdrawal fees remain.

Existing 253–255 EV values are never silently reduced. A complete quick-training
allocation cannot leave another stat above 252; free reset or native reducing
berries can resolve such old distributions before choosing Classic/Unlimited.
Tighter modes scan party, PC, Day Care, migration storage and pending targets;
an occupied Pokéwalker conservatively blocks a mode change. Empty all-zero
external-storage records are handled without invoking encrypted accessors.

## Native bridge

Opcode 490 retains its original four-byte width. Only operand `0xF13A` invokes
this adapter; other operands fall through to the original native handler without
consuming the script pointer. Inputs are special variables 8006 (operation),
8007 (slot), 8008 (argument/stat), 8009 (value), 800A (kind). Outputs 800B (result),
800C (cost/minutes) and 8000–8005 (stats/status) are transient script variables.

| Operation | Meaning |
|---|---|
| 0 | Policy/default clock/pending rewards |
| 1 | Activate or change policy after storage admission/census |
| 2 / 3 | IV / EV preview |
| 4 | Revalidate and commit the preview |
| 5 / 6 | Buy a cap / deliver queued milestone caps |
| 7 | Change clock, preserving accrued fractions for both jobs |
| 8 / 9 | Enroll / project course status |
| 10 / 11 | Cancel pending preview / read current six stats |

Result 0 is success; 1 invalid; 2 egg; 3 unchanged; 4 payment; 7 unavailable/busy;
8 means training storage cannot safely be admitted. Native transaction errors
also retain the shared core's overflow/identity distinctions. Stat IDs in the
bridge use stored order HP/Atk/Def/Speed/SpA/SpD.

Transactions operate on a 236-byte clone, validate encrypted checksum and
identity, use native setters and recalculation, verify targets, then debit as
the last fallible step and copy back without yielding. Box-only paths validate
the corresponding checksum/decryption flag before native accessors.

Battle gains, all six vitamins and reducing berries obey the selected policy.
Power items, Macho Brace and Pokérus retain their native multipliers. Caps use
item IDs 113/114 and appended parameter records 514/515; both individual and bulk
item loaders cover those records. Old item mappings remain stable.

## Save layout and admission

The 256-byte `TNR1` v2 journal (with validated v1 read compatibility) uses sectors 49/113 (`0x31000`/`0x71000`), with
primary at +0 and mirror at +0x200. It stores native generation/main-block CRC,
policy, clocks, reward ledger, two deferred courses and the appended shiny state. Serialization comes
from the shared training core; native structs are not dumped to flash.

Each sector has a 32-byte `TNO1` v1 ownership marker at +0x400. Its first 16 bytes
are `54 4e 4f 31 01 00 20 00 00 01 00 02 00 01 00 00`; the final 16 are their
bitwise complements. It authorizes only the two 256-byte records and itself.
Before activation, both alternating sectors are checked without writing.
First ownership is allowed only in a completely erased sector, or an exact
partial marker prefix with an erased tail and every other byte erased.

Admission also reads all four 452-byte expanded-Bag destinations at `0x30000`,
`0x30200`, `0x70000` and `0x70200`. Each read must succeed, and each record must
be uniform (any repeated byte) or owned according to the Bag writer's complete
`B252` magic or nonempty interrupted magic prefix with an entirely erased tail.
A foreign nonuniform record or failed read returns service result 8 before
activation or payment. This check uses one 452-byte word-aligned stack buffer,
reused for training records; it neither allocates nor writes flash. A rejected
policy change preserves an already active journal and its save-failure barrier.

The marker is written/read back before the journal. A valid marker permits
repairing interrupted owned records. An explicitly different future version or
length still vetoes writes; an exact partial first v1 or v2 header followed entirely
by erased bytes is recoverable. Foreign bytes outside owned ranges are never
modified. A missing/unsupported journal disables training while ordinary native
saving remains available; an active journal that cannot safely persist fails
before the native main save commits.

The adapter calls the existing Bag load wrapper. Its save hook runs after the
Bag wrapper has finished and verified both copies, computes the final native
main CRC and verifies both journal writes before invoking the original native
save phase. It preserves Plus/Bag chunk IDs and bank selection. Failed native
save status uses the game's existing generation/sleep cleanup path.

`training_shiny_bind` resets the owner cache on Continue/NewGame;
`training_shiny_access` admits the new state only after read-only checks of both
training banks and every Bag destination. It never writes flash directly or
activates training. A new SHINY_ONLY journal keeps training inactive and preserves
historical reward eligibility until explicit training activation. Native SAVE
persists admitted shiny state through the same journal coordinator. Unknown
future records remain protected. The field adapter must independently prove its
live FieldSystem/SaveData owner before invoking this API.

Courses leave native encrypted Day Care boxes and breeding step counters intact
until withdrawal. Enrollment settles existing growth once. Retrieval projects a
clone, preserves the move set and EXP remainder, calls native retrieval, then
commits job compaction only on success. The party-count ABI is 02074640;
0207463C is maximum capacity and must not be substituted.

## Validation

ROM-free ownership, script and transaction tests compile the production sources.
`test_save_composition.py` additionally compiles and runs the production training
and Bag ARM blobs together on synthetic flash/RAM. It checks each Bag address
with either bank active, ownership parity against the real Bag predicates,
read failures, read alignment, unchanged admission state and the later native
save boundary. OS/flash, script lookup, reward census and the final native
commit are explicit seams; ordinary native saving remains reachable after
refused initial activation, while failed persistence of an active journal
still blocks that commit. The Class A runner includes this ROM-free suite.
Private actual-ARM tests additionally exercise encrypted native getters/setters,
stat recalculation, Bag 999/payment boundaries, battle/item EV behavior, native
withdrawal/compaction, clocks/phone buffers, corrupt data, both-sector admission,
reward anchoring and interrupted journal recovery.

```sh
SGP_TRAINING_ROM=/private/candidate.nds \
SGP_TRAINING_REPORT=/private/training-report.json \
python3 -m unittest discover -s source/features/training-native/test -v
```

The ARM bench uses private ROM assets with explicit OS/allocation/flash seams;
it is not an emulator compatibility claim. Separate native input campaigns
verify menus, exact payments, actual Pokégear calls, normal saves and cold loads.
A test fixture may be positioned with the game's native warp before a normal
save; this is documented test setup, not an unmodified legacy compatibility run.
The final release validation records the independent older-save matrix and the
bounded service campaigns. Original save fixtures are never mutated.

## One legacy PLAY course — 16 November 2026

A bounded host case prepared a real course using normal inputs and native SAVE
on r4 EN `2e30d6960bb059615fca7527700d86f8282e82ccbe99bf62e22f027453dc3d3d`, then upgraded a raw-save copy to the exact 1.3.3 EN
`d6fbdf8bd0aec528a336713b497847da36b467001b2f550c9cc583679c3e5c7d`. The v2 journal contained one level-only Blastoise course,
level 54→100, Legacy policy, PLAY clock and 22 seconds of partial credit.
The successor's native SAVE changed generation 117→118 and bank 1→0;
credit rose 22→57 seconds, with the same 35-second increase in native IGT,
PLAY and anchor. Identity, baselines, ledger, policy, defaults, shiny state,
lastRTC, the inactive second slot, Pokémon, Bag and Plus settings were preserved.

Fresh cold Continue retained the saved bytes and the live Training Status
recognized the course. The comparison uses the existing protected-field checks
and native bookkeeping rules, adding strict full-journal progression and the
existing IGT/PLAY equality rule. Owned counterexamples reject lost credit,
lost jobs and synchronized fabricated progress without matching native IGT.
The preparation's policy/clock activation and historical reward queue are
explicit setup changes, separate from the update-preservation comparison.

This is one EN, v2, one-slot, level-only PLAY case before its first 7200-second
quantum. It does not establish v1 migration, EV courses, two active jobs,
RTC/clock switching, level completion, withdrawal, other-language or hardware
coverage. No save layout or game code was changed for this validation.
