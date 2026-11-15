# Native trainer first move: record → veneer → complete Box caller

The first custom-move iteration of the type3 trainer constructor passes from
its actual instruction prefix through `MonSetMoveInSlot` and the complete
[Box move caller](native-box-move-caller-source-rom-1.3.2.md). Three original
runs execute51613 instructions total: PP-Up3, PP-Up0 and observation OFF.
Every full16 state, read, store/preimage and all26 pages match the source
prediction. Forty-five raw falsifiers and three cached-input falsifiers fail.

Entry is a new, explicitly owned fixture at`02073A22`, after the held-item
setter in the source path. The run stops at`02073A40` **before executing BLT**.
This is a complete first iteration within a bounded prefix, not a function
return, full trainer constructor, four-slot loop or natural gameplay capture.
No ROM, save, gameplay, ABI, identifier or default changes.

The [owner](../../features/trainer-strategy/README.md),
[source-to-ROM method](../test-bench.md#linking-source-to-an-exact-rom) and
[complete ROM composition guide](../test-bench.md#from-the-source-tree-to-the-complete-rom)
provide the wider context. The existing Plus strategy modifies another member
of this trainer's party; no Plus/Normal matrix is relevant to this first slot.

## Exact inputs and source

Use your own current r4 cartridges. Optional IT is fresh readback only; EN
supplies the bytes for the three execution cells.

| Image | Bytes | SHA-256 |
| --- | --- | --- |
| EN |152786844 | `2e30d6960bb059615fca7527700d86f8282e82ccbe99bf62e22f027453dc3d3d` |
| IT |159029760 | `13ebac02bdea3036511773587e6603ce6834e25f4b13d1a4662c3e954bfd5d4a` |

Both headers are IPKE/revision0, despite different presentation languages.
Productive source is
[ctrl-cheeb-del/pokeheartgold at cb614ad23449d5852b40321dc409c4143872b35c](https://github.com/ctrl-cheeb-del/pokeheartgold/tree/cb614ad23449d5852b40321dc409c4143872b35c).

| Source | SHA-256 |
| --- | --- |
| `src/trainer_data.c` | `2e5232c4989f6f2752087bf46579e8207b90b2e5abf65f04dac72e2b03496803` |
| `include/trainer_data.h` | `6498920abbabd2f06ba85ee822b31e6059e604de5044ae2e2d8f332399742f3d` |
| `src/pokemon.c` | `1d784ece4650b84e426a437ee20e4a926475fc20ef761e67440d0c0136548fa3` |
| `src/move.c` | `e9adae2d57511a89ec5cc52ebb5741172a5d90123d02d33be66143ddf210e7b2` |

`CreateNPCTrainerParty` starts at271; its type3 custom-move call is at422.
Type3 records have stride18/item+6/moves+8. Type1 uses stride16/moves+6:
those layouts are not interchangeable. `MonSetMoveInSlot` at3128 forwards
`&mon->box` without resetting PP-Up. The separate
`MonSetMoveInSlot_ResetPpUp` at3117 performs additional setters and another
MaxPP calculation; it is not the trainer's target.

The [source-definition comparator](../../features/trainer-strategy/tools/confronta_box_move_pret.py)
authenticates two clean pins and eight source files, then verifies six actual
definitions against newer PRET HGSS6bf138. It distinguishes prototypes,
callsites and function bodies. The
[definition table and exact hash convention](native-box-move-caller-source-rom-1.3.2.md#inputs-and-source-provenance)
include the documented correction of two previously mislabeled callsite hashes.
The Mon wrapper, reset variant and8462-byte constructor definitions also match.
This is source alignment, without transferring a newer header ABI or claiming
original C code generation or an Italian build target. Earlier sealed proof
snapshots remain preserved.

## Installed windows and reverse route

Current plain ARM9: physical`0x4000`, RAM`0x02000000`, initialized size
`0x12B8E4`. These windows belong to initialized ARM9; there is no overlay or
autoload dependency. Physical offset here is`0x4000+RAM-0x02000000`.

| Component | RAM interval, end excluded | Physical start | Bytes / starts | SHA-256 |
| --- | --- | --- | --- | --- |
| Type3 prefix | `02073A22..02073A40` | `77A22` |30 /14 | `f0cf7e6ea2bf9a23e10a5b15407e73ab7332565696bacc9113991561a2a28a9c` |
| Mon veneer | `020714E8..020714EC` | `754E8` |4 /2 | `8bdadb00ad3389fd9d10292c291d2b47f6d30d0531c80bbc0dbfbd0813d70c8c` |
| Veneer literal, data | `020714EC..020714F0` | `754EC` |4 /0 | `1546a4580bb2146c10d9a99c44c9a226821a7cf8955b67aa4b3437ac10536a15` |
| Excluded branch gate | `02073A40..02073A42` | `77A40` |2 /0 executed | `33b2105ff852e91db7fe48ade9b9bd8e231b1be0e90301c59b2adb9c36dcbe78` |

BL`02073A32` reaches veneer`020714E8`. Its LDR/BX reads the actual literal
`020714F1`, retaining Thumb state and entering Box caller`020714F0`.
The prefix loads the current-record pointer from`[SP+64h]`, publishes the
cursor at`[SP+5Ch]`, reads move310 from`record+8`, derives slot0 in R7/R2,
calls the veneer and then advances cursor by2/index by1. CMP against4 sets
the final flags. The excluded BLT would loop to`02073A28`; it is never admitted
as an executed Thumb start.

The [reader](../../features/trainer-strategy/tools/rileggi_trainer_move_prefix.py)
reuses the complete-caller readback, adds34 executed code bytes/16 starts,
four literal bytes and the separately authenticated two-byte gate.
It admits958 Thumb code bytes/436 starts, plus the unchanged30 SDK ARM
functions and signed DIV. The generic shared slice reader places non-admitted
slices in its DATA collection; its inner gate slice therefore uses that category.
The outer gate record and lineage classify these bytes as **excluded branch
code**, not an executed instruction or an attribute table.

The [lineage reader](../../features/trainer-strategy/tools/rileggi_trainer_move_lineage.py)
locates the unique aligned30-byte prefix in decoded ARM9, follows its actual
BL, validates LDR/BX and the Thumb literal bit, then reads the66-byte target.
Five components106B=40new+66target match all eight exact retail/base1.1/V4/r4
EN/IT inputs. Two retail BLZ owners retain null physical plaintext offsets;
six plain owners have five physical checks each. This extends the native
code link; it repeats neither the earlier party-resource campaign nor gameplay.
Require top-level`all_images_attributed is True` and every entry in`images`
to have`all_components_equal is True`. Exit0 alone can also record an
unattributed layout or a difference.

## The record in your ROM

The reader reuses the qualified
[Bag raw NARC reader](../../features/borsa/tools/attribuisci.py) through
read-only mmap: native path row→FNT file ID→FAT archive→BTAF/BTNF/GMIF→member31,
then independently compares ndspy and direct physical member bytes.
It does not initialize the constructor, invoke its models or load unrelated
personal/name/capsule resources.

| Resource | Header archive55 | Party archive56 |
| --- | --- | --- |
| Path | `a/0/5/5` | `a/0/5/6` |
| FAT file ID |184 |185 |
| Archive physical start / bytes | `01F91A00` /20716 | `01F96C00` /31286 |
| Member31 physical start / bytes | `01F933B0` /20 | `01F98980` /108 |
| Member SHA-256 | `db2e0fa9e4d0b97a0d1721e878001bcddafe1e379827adccc37844cdbce13fff` | `2096c9d5a3943dca51dec0ea9b0b006387f2fb5b0d6778a49f58c2803806395c` |

The header declares type3/class72/count6; six18-byte records consume all108B,
without a trailer. Record0 has level27/species355/form0/heldItem0 and first
move310 at+8. Its18-byte SHA is
`d8633b3decabc64d9098784c47c1b1b3bc07843a67661a07df1bf24378e8fdfa`.
Archive IDs55/56 are not FAT file IDs55/56. Physical offsets are for these
current exact images, without assuming a retail-Italian address alias.
The strategy's change at offset102 concerns the last Mon; this first move
retains its ROM value. Record108 is supplied before entry, rather than read
by native FS during this prefix. Native FS during the run reads move310's
PP15 from NARC11, as in the complete-caller proof.

## Explicit fixture and stack lifetime

An earlier constructor packet and later wrapper registers do not form a
lossless checkpoint at3A22. The freezer creates a new synthetic entry:

- Mon at`022F0000`: owned encrypted Box136/PID4000/flags0/species355/move310/
  initialPP15/heldItem0, followed by100 bytes of a deterministic nonaccess
  pattern. This tail is not a legalized or decoded party/save record.
- ROM-derived record108 at`022F0200`,16-byte guards around record and Mon236.
  The old guard after Box136 is replaced only while preparing this new input;
  the actual Mon guard follows all236 bytes. No runtime replacement occurs.
- Function-top symbol T=`023FD000`; entry SP S=`T-152=023FCF68`.
  Caller frame152 starts at S, current-record pointer at S+64h, cursor at
  S+5Ch initially`DEADC0DE`. R6 points to Mon; R7 starts as a nonzero cookie.
  The native prefix must initialize slot0 and publish the cursor itself.
- Other registers are declared cookies, initial CPSR=`6000003F` and
  LR=`0DDD0001`, not a fake function-return gate. The source fixture/JSON gives
  the complete full16 and every mapped-page identity.

The veneer changes R3 to`020714F1`; the child caller therefore spills a word
whose low byte is F1. The PP stack writer's preimage must be F1, rather than
the direct-entry cookie03 of the previous case. BL supplies LR=`02073A37`.

| Child resource | Relative to S | Current logical address |
| --- | --- | --- |
| Move Value |−12 | `023FCF5C` |
| PP Value |−32 | `023FCF48` |
| FILE client |−184 | `023FCEB0` |
| Parser locals |−208 | `023FCE98` |
| Native move buffer |−72 | `023FCF20` |

Observed peak is688B below entry S. Adding the declared existing caller
frame gives840B relative to T,896B including the lower56-byte guard. The
prefix does not execute the constructor prologue. All152 upper-frame bytes
are checked; only the cursor word changes to record+2. Tail100 and all guards
have zero overlapping accesses and retain every byte.

The old standalone SDK guard could admit addresses in this upper frame under
its former TOP. A new interval guard rejects those accesses, allowing only
three explicit prefix loads. The predictor also pins the complete cached
FAT4104/FNT2902/root12 blobs; canonicality relative to supplied parts alone
would not authenticate an unused modified byte. Three canonical-relative
mutants must fail those hash gates before source execution.

## Native result, coverage and counterproofs

Each run uses26 pages106496B,3811 reads and2247 stores. Source prediction and
native execution agree:

| Cell | Instructions | ARM / Thumb | Unique starts | Gate callbacks |
| --- | --- | --- | --- | --- |
| PP-Up3 |17214 |6205 /11009 |1267 |17215 |
| PP-Up0 |17185 |6176 /11009 |1238 |17186 |
| PP-Up3 OFF |17214 |6205 /11009 |1267 |17215 |

The child preserves the PP-Up read from the Box. Original PP15 and DIV
900/100 or0/100 produce24/15; native caller STRB writes that result on the
stack, and the final setter consumes the same pointer. Checksums become
02B4/02A8. The full child includes384 crypto stores/384 seed updates/320
checksum reads and12 block selectors per run, including idempotent writers.
The final Box hashes are those of the linked complete-caller case.

At the unexecuted gate:

```text
R0=022F0202 (record+2), R1=0, R2=35EC47E5 / 4AA02329
R3=02073A37, R4/R5/R8..R11=entry, R6=Mon, R7=1, R12=0
SP=023FCF68, LR=0201FF59, CPSR=8000003F, PC=02073A40
```

These are observed stop-state values, not a C function-return ABI. The child
source checks reuse the qualified Box semantics on views derived from the
single source trace's actual entry/return and ordered stores. No child CPU
runs separately, and no phase bridge, reset or state repair reaches the producer.
All full-prefix flow/access/page comparisons remain mandatory.

Forty-five raw falsifiers cover wrong type1 pointer/+6 move, a second-move
read, missing cursor publication/advance, missing native slot initialization,
missing veneer/literal/BL, old direct-entry SP/R3/PP-spill preimage, changed
MaxPP/DIV/PP reads, removed idempotent writers, false final cursor/index/flags,
changed tail/maps, host writes/models, premature child-return stop and absent
callback/fault/type/hash camouflage. OFF retains complete endpoint and counters
while omitting observation projections. Three additional input controls mutate
cached FAT/FNT/root copies and require their exact pre-ISA rejection causes.

The unchanged local runner uses32768 outer instructions, ARM segments capped
at`min(8192,remaining)` and one uninterrupted Uc/emu_start per cell, timeout1s.
Require source-count+1≤32768 and an actual stop callback, in addition to fault,
PC/full16/counters/maps and full transcripts. The parent owned qualification
is reused unchanged; no new ISA/producer/limit or kernel campaign is introduced.

## Compile/composition boundary and reproduction

This is inherited native HGSS code. No new installer or game build executes.
The verifier authenticates retained reconstructed30SDK ELF objects and DIV524
against source/recipes/installed bytes using the
[SDK](native-fs-memory-narc-source-rom-1.3.2.md) and
[division recipe procedures](native-maxpp-memory-source-rom-1.3.2.md).
Original MWC/Thumb C objects, compiler and link map remain missing; this is
not an original C-to-ROM match or a full Italian source build.

Use Python3.14, ndspy4.2.0, Capstone distribution5.0.9/module5.0.7 and
Unicorn2.1.4/CPU17. Pure tests need only the standard library. Actual execution
has no ARM946 silicon/timing/cache/IRQ/CP15 or natural CARD qualification.
From the repository root, create a fresh local`$OUT` and set your own input paths:

```sh
python3 -I -S -B -m unittest discover -s source/features/trainer-strategy/test \
  -p 'test_trainer_move_prefix*.py'
python3 -I -S -B -m unittest discover -s source/features/trainer-strategy/test \
  -p 'test_box_move_pret.py'
python3 source/features/trainer-strategy/tools/rileggi_trainer_move_prefix.py \
  --rom "$ROM_EN" --it-rom "$ROM_IT" --json "$OUT/resources.json"
python3 source/features/trainer-strategy/tools/congela_trainer_move_prefix.py \
  --rom "$ROM_EN" --json "$OUT/input.json"
python3 source/features/trainer-strategy/tools/qualifica_box_move_caller.py \
  --json "$OUT/owned-limits.json"

for MODE in prepare matrix verify; do
  if [ "$MODE" = verify ]; then set -- --raw-dir "$OUT/matrix"; else set --; fi
  python3 source/features/trainer-strategy/tools/attribuisci_trainer_move_prefix.py \
    --mode "$MODE" --rom "$ROM_EN" --reference "$HGSS_REFERENCE" \
    --objects "$SDK_OBJECTS_JSON" --recipe-dir "$SDK_RECIPE_DIR" \
    --div-recipe "$DIV_RECIPE_DIR" --input-contract "$OUT/input.json" \
    --qualification "$OUT/owned-limits.json" --out-dir "$OUT/$MODE" "$@"
done
```

The productive reference must be clean at the stated pin. Regenerate your
comparison objects/manifests using the linked recipe instructions. Each JSON
and output directory must be new. An unchanged completed parent qualification
may be reused; otherwise run its owned qualifier as above. `prepare` authenticates
fresh resources, frozen input, source, recipes, qualification and three input
controls. `matrix` makes exactly three native prefix runs. `verify` recomputes
predictions and rejudges the saved raw/prepared/report hashes without CPU or
compiler. Source identities are checked before/after every cell. Private raw
traces, ROMs, extracted records, saves and source snapshots stay local.

For the new106-byte historical comparison, use
`rileggi_trainer_move_lineage.py --help`, supply retail/base1.1/V4/current
paths for one language and a fresh JSON, then repeat for the other language.
Do not repeat the old party-member lineage for an unchanged question.
`python3 source/attribution_cases.py show native-trainer-first-move-prefix-source-rom-1.3.2 --json`
is report discovery only, not an automatic acceptance verdict.

The first native matrix passed in4.251s/OS peak RSS165036032B. CPU-free
verification passed in3.463s/158072832B; verification with CPU/assembler imports
and compiler subprocesses denied passed in3.378s/157286400B. Thirty-one
ROM-free tests pass, including eight definition-parser counterexamples;
23 prefix contracts ran together in0.248s/91881472B. These are host costs,
without a game responsiveness or memory-saving claim.

## What is proved and what remains

| Conclusion | Evidence and boundary |
| --- | --- |
| Documented provenance | Pinned constructor/type3 layout/Mon wrapper/Box source; six actual source definitions aligned to newer HGSS |
| Reconstructed binary correspondence | Retained SDK/DIV assembly ELFs; current physical/ndspy readback and106-byte eight-image code lineage |
| Finite semantic equivalence | Record+8→slot0→veneer→complete child→cursor/index/CMP, owned PP-Up3/0 context, every full16/access/page |
| Activation observed | Three exact synthetic prefix entries, memory-archive mode and stop before the first loop branch |
| Unattributed | Original C code generation/full ROM build, actual lost checkpoint3A22, constructor setup/full trainer/four-slot loop, Plus strategy execution here, other records/slots/PIDs/flags/fallbacks, Italian guest, natural CARD, saves/hardware |

No game optimization follows automatically. The first slot does not consume
the strategy's last-member change. Skipping idempotent setters or replacing
this wrapper with ResetPpUp would alter semantics; either proposal needs a
separate maintainer decision and broader state/caller evidence. The reusable
result is a verified record-to-callee bridge, contextual upper-frame guards,
whole cached-data pins, strict definition comparison and a complete native
checker that can support the next finite attribution.
