# Native relative FindPath wrapper

This follows the [complete Read/Wait caller](native-fs-read-caller-source-rom-1.3.2.md)
to its remaining modeled Find entry. It attributes `FSi_FindPath`, the wrapper
that fills directory arguments and sends command4. `FSi_FindPathCommand`, which
walks directory entries through the native filesystem, remains outside this case.
The new native execution is isolated, using copied actual caller inputs and a
declared BSS root fixture. It does not yet run in the complete original caller.
No game code, installer, ROM, save, ABI, identifier or default changes.

## Cosa farebbe un professionista di alto livello che non sto chiedendo

Distinguish path-prefix preparation from full path resolution. Check the
wrapper's source/recipe→object→ROM and ROM→caller→source links separately.
Trace actual aggregate fields, PUSH/POP ownership, R3 restoration, residual LR,
flags and modeled output. Seek a FALSE return after the same FileID bytes and
whole RAM, and a noncanonical truthy2 that the wrapper does not normalize.

Treat a literal's target as an address to map, not as evidence of initialized
ROM bytes. Follow module parameters, BSS and source initialization. Compare
languages and revisions without silently rewriting pointers for equality.
Verify source-definition hashes against the definition, skipping any forward
declaration. Preserve incomplete compiler provenance and input-state limits.

## Il materiale più grezzo da cui partire

Use developer-owned inputs and the project objects/reports from the linked
parent guides. Current EN152786844 bytes, SHA-256
`2e30d6960bb059615fca7527700d86f8282e82ccbe99bf62e22f027453dc3d3d`;
IT159029760 bytes, SHA-256
`13ebac02bdea3036511773587e6603ce6834e25f4b13d1a4662c3e954bfd5d4a`.
Both IPKE revision0; IT text is localized. ARM9 file offset`0x4000`,
load`0x02000000`. The wrapper is in the uncompressed main section, with no
overlay/autoload lifetime of its own. The independent reader uses decoded
sections for older compressed images and does not invent physical offsets.

| Component | RAM | Current ROM offset | Extent |
| --- | --- | --- | --- |
| Find wrapper | `[0x020D7FC0,0x020D8100)` | `0x000DBFC0` |320 bytes/80 ARM instructions |
| Data-only pool | `[0x020D8100,0x020D8104)` | `0x000DC100` |4-byte pointer |

The full324-byte SHA-256 is
`baf1c233ca8efcaa3ca58e996fe2f01e437fad5753dca7bbe1e6e782dd9abcf8`.
The literal is`0x021E362C`, inside static BSS
`[0x02111860,0x021E5900)`. It has **no initialized-ROM mapping**. Reading
`address−load+file_offset` for that global would select unrelated ROM bytes.
Module parameters at ARM9+`0xBA0`, bounded autoload tables, independent physical
readback and ndspy section decoding establish the distinction.

The source counterpart is
[ctrl-cheeb-del/pokeheartgold at cb614ad](https://github.com/ctrl-cheeb-del/pokeheartgold/tree/cb614ad23449d5852b40321dc409c4143872b35c):
`lib/NitroSDK/src/fs/FS_file.c::FSi_FindPath`.
`FS_archive_suffix.c` defines `current_dir_pos` without an initializer;
`FS_RegisterArchiveName` sets its arc and zero own_id/index/pos when registering
the first archive. `FS_rom.c::FSi_InitRom` registers the ROM archive. This source
explains a root fixture; it does not establish that initialization was observed
in the isolated CPU or that the opaque archive token reconstructs FSArchive.

The [assembly](../../features/trainer-strategy/sorgenti/fs-find.S) is a recovered
attribution recipe with no installer. Clang targets ARMv5TE/ARM946E-S/ARM mode;
its receipt records executable hash/version, flags and all exit codes. The
qualified independent ELF parser rejects text relocations and compares324 bytes.
Original MW compiler/objects remain unavailable. The recipe matches current
installed bytes, rather than reconstructing original compiler history.

Original header checks cover18 dependencies and FSFile72, FSDirPos12,
FSFindPathInfo24 and FSFileID8. FSDirPos fields are arc0/own_id4/index6/pos8;
DIR.arc is8, ARG.pos48/12 bytes, path60, find_directory64, result68 and
FINDPATH command4. The corrected definition-only source hash for `FSi_FindPath`
is`a2175ffff02e7bfaf9532216cecb78fd3ee8db1aa4cf5c64762e75954778641a`.
An earlier receipt began at its prototype and hashed unrelated following text;
that metadata was replaced after a regression test. Assembly and object bytes
were unchanged by the receipt correction.

### Revision and language counterexample

All eight tested retail/base1.1/V4/current images contain the same320 instruction
bytes. Seven match the complete324-byte current recipe. Retail IT (IPKI revision0) differs only
at offsets320/321 in the data pool: its pointer is`0x021E35CC`, and its BSS is
`[0x02111800,0x021E58A0)`, both shifted by`−0x60`. The reader records both full
and instruction-only hashes, differing offsets and BSS bounds. It does not
modify any image or claim a full324-byte match for retail IT. Original legacy
activation and an original legacy compiler build remain unproven.
The instructions are retained native HGSS code; the current Italian pool form
is already present in the inherited base1.1 image. This case adds no Plus-compiled
payload or insertion. The classified extent contains instructions and the one
pointer, with no padding attributed to this function.

## I metodi e gli strumenti da usare

### Captured caller inputs and declared state

The original Convert BL at`0x020D81A8` targets Find at`0x020D7FC0`, returning to
ARM`0x020D81AC`. Four distinct Plus/seed parent positives are authenticated and
semantically replayed without a parent CPU. Each captured model entry16 must
match that actual Convert BL context. These are actual initialized parent API
entries, not observed native execution of the former modeled Find body.

DIR=`0x023BEDD0`, ID=`0x023BEE28`, path=`0x0210F198` contains`a/0/1/1\0`.
Input frame280 combines the actual post-Init frame240 with the last40 bytes of
the parent's preserved56-byte lower guard. No native write occurs between that
Init checkpoint and the Find call. Root `current_dir_pos` is an explicit12-byte
fixture: opaque token`0x021E3654`, then zero own_id/index/pos. The token is never
dereferenced by this relative wrapper. No boot or live filesystem state is claimed.

Find PUSH28 plus local12 lowers SP by40. It copies the12-byte global aggregate
into its local frame and then DIR. It scans only the prefix `a/`: three byte
reads, because the first character is read twice. The remaining components are
resolved by the declared Send model, rather than by native wrapper instructions.
Send4 reads actual ARG pointers/flags/position, resolves the whole actual path
against raw FNT and copies the eight-byte FSFileID for file140. The resource is
the same NARC11/`a/0/1/1` established by the parent. No raw data is published.

**Send4 models ID8 only.** Native command/error/status, queue/list/archive/card
and completion effects remain excluded. For example DIR.command stays14 from
Init in this experiment; passing argument4 is not a native command-field store.
The full source/native/model frame ordering and whole4MiB delta are checked.
No large RAM artifact is included in the public repository.

### ABI, conditional instructions and counterproof

The finite path has47 native hooks at42 unique starts,17 native word stores,
18 data reads, one Send boundary and one original return gate:49 steps.
The last loop CMPNE at`0x020D802C` is false and must not change CPSR. An independent
capability uses our own four ARM instructions with two characters:47 skips CMPNE
and preserves flags`0x6000001F`;60 executes it and produces`0x8000001F`. Raw
records precede checks. This qualifies hook delivery and effects for Unicorn2.1.4
model17 (Cortex-A15), not ARM946 silicon, timing or IRQ delivery.

Native Send entry starts`[DIR,4,0,DIR+48]`, SP=DIR−40, LR=`0x020D80F8`.
POP restores R3 and R4–R8, SP and the original ARM PC. LR itself remains
`0x020D80F8`. Normal API return leaves R1=4/R2=0/R3=0/IP0 and
CPSR=`0x6000001F`. Send0/1/2 becomes R0=0/1/2 without normalization. In
particular R0=2 can coexist with Z=1: the flags came from the earlier comparison,
not a comparison of the returned value. Send clobber changes R1/R2/IP/flags,
while the native POP still recovers R3=0. Saved state and all16 register widths
are strict. Raw FNT/path→ID is checked in both collector and independent replay.

The FALSE counter retains the same delivered ID, frame and whole RAM, but returns
native0. Disguising its policy as Send1 must still fail the positive oracle on
actual return evidence. A deliberately supplied FALSE result after successful
ID delivery is an ABI control, not a naturally observed filesystem failure.
OFF checks whole RAM and functional ABI without a projection or new mask.

This case's initialized isolated memory does not qualify a new parent guard.
A future full integration would raise reader peak240→280 and global560→600,
inside the old608 bound, but the lower guard/ownership must be re-derived first.
No change to the complete caller's current masks or expected registers occurs here.

### Reproduction

Dependencies: Python3, ndspy4.2, Capstone, Unicorn2.1.4/model17, ARMv5TE-capable
Clang and the pinned reference headers. Build the parent project objects and
Read/Wait recipes and obtain a full Read/Wait caller report using its guide.
Use fresh private output directories. The following variables refer to your own
ROM, reports, objects and reference checkout; no command patches or installs a ROM.

```sh
python3 source/features/trainer-strategy/tools/compila_fs_find.py \
  --cc "$SGP_CLANG" --reference "$SGP_REFERENCE" --uscita "$SGP_OUT/recipe"

python3 source/features/trainer-strategy/tools/attribuisci_fs_find.py \
  --conditional-capability --raw-dir "$SGP_OUT/conditional-public-raw" \
  --json "$SGP_OUT/conditional-public.json.gz"

python3 source/features/trainer-strategy/tools/attribuisci_fs_find.py \
  --rom "$SGP_ROM" --language EN --parent-report "$SGP_CALLER_REPORT" \
  --objects "$SGP_REMATCH_OBJECTS" --strategy-object "$SGP_TEAMS_OBJECT" \
  --read-recipe "$SGP_READ_RECIPE" --wait-recipe "$SGP_WAIT_RECIPE" \
  --recipe-dir "$SGP_OUT/recipe" --prepare-only \
  --json "$SGP_OUT/prepared-EN.json.gz"

python3 source/features/trainer-strategy/tools/attribuisci_fs_find.py \
  --rom "$SGP_ROM" --language EN --parent-report "$SGP_CALLER_REPORT" \
  --objects "$SGP_REMATCH_OBJECTS" --strategy-object "$SGP_TEAMS_OBJECT" \
  --read-recipe "$SGP_READ_RECIPE" --wait-recipe "$SGP_WAIT_RECIPE" \
  --recipe-dir "$SGP_OUT/recipe" --raw-dir "$SGP_OUT/raw-EN" \
  --json "$SGP_OUT/fs-find-EN.json.gz"

python3 source/features/trainer-strategy/tools/rileggi_fs_find.py \
  --retail "$SGP_RETAIL" --base "$SGP_BASE11" --v4 "$SGP_V4" \
  --rom "$SGP_ROM" --language EN --recipe-dir "$SGP_OUT/recipe" \
  --json "$SGP_OUT/lineage-EN.json"

python3 -m unittest discover -s source/features/trainer-strategy/test \
  -p 'test_fs_find*.py' -v
```

Repeat with IT and its own exact inputs. `--probe` restricts execution to one
positive; `--prepare-only` performs input/parent semantic replay and byte readback
without executing a CPU. A report comparison uses canonical JSON containers,
retaining scalar distinctions such as bool versus integer0. Raw observations,
fault/return state and source identities precede semantic checks.

Keep raw fixtures/captures/ROMs/saves/BIOS private, and preserve original inputs.
Record source snapshots, argv/exit/log hashes, compiler/header receipts and OS
peak RSS. Use one producer,180s/1GiB RSS/2MiB log/16MiB case/1GiB planned disk
peak and at least10GiB free after peak. Missing inputs must produce explicit
limits or replay skips; a final private qualification requires zero skips.

### Current evidence and remaining links

The first EN isolated probe passed49 steps/47 hooks/42 starts/17 stores/18 reads
and the independently reconstructed whole4MiB memory delta,0.744s/83066880 bytes
OS peak RSS. The final EN/IT matrix is acquired below.

| Conclusion | Scope |
| --- | --- |
| Documented provenance | Pinned C definition/header layouts, recovered recipe and source-declared root fixture |
| Reconstructed binary match | Current324 bytes/independent ELF;320 instructions in eight images, full324 in seven |
| Demonstrated semantic equivalence | Forty-eight isolated copied-context native executions, with explicit root/Send boundaries |
| Observed activation | Isolated initialized Find body; complete caller integration and natural activation pending |
| Unattributed links | Native Send4/path traversal/completion, boot state, other path modes and hardware |

The reusable improvements are BSS-aware attribution, split instruction/pool
lineage, prototype-safe definition hashes, strict receipt serialization and
field-driven Send boundaries. The next attribution task is complete caller
integration with a justified280-byte ownership frame and a new guard. Native
FindPathCommand and Send remain further links. No optimization or game fix is
established by an unchanged ID or final RAM.


The final48 runs passed24 per language: four parent Plus/seed inputs × normal,
OFF, Send FALSE, Send2, volatile clobber and alternate fill. EN3.558s/
604422144 bytes OS peak RSS; IT3.726s/618446848 bytes. Each normal run has49
steps,47 full-register hooks,42 native starts,17 stores,18 reads and40 bytes
of additional stack. Source identities cover62 runtime files. These are host
verification costs, without a game responsiveness or performance claim.

All eight FALSE counters return native0 after the same FileID/frame/whole RAM.
Disguising the Send policy fails specifically on `Find source-derived returned`.
Send2 remains2; clobber still restores saved R3. Both controls preserve memory.
OFF preserves the entire4MiB and functional context with no projection.
Alternate fill preserves the frame and ID while changing untouched RAM as expected.

Eighteen tests passed with zero skips:12 portable and six private replay tests.
The bounded command took4.948s with794066944 bytes OS peak RSS. It authenticates
both input derivations, exact source/recipe receipts, every raw matrix cell,
all native contexts and memory deltas, conditional capability and counter
rejections. Falsifiers cover false-CMPNE effects, entry/return/flow widths,
saved stores, delivered ID, extra memory change, missing reads, fault and return.
The public conditional CLI reproduced exactly the original two capability rows,
2.474s/99581952 bytes OS peak RSS.

The review found a bool/zero alias in the observed entry check and incompatible
prepare/CPU flags. Strict entry typing and mutually exclusive modes fixed both;
regression tests block CPU collectors when testing rejected mode combinations.
Only the result oracle and CLI changed; collector/predictor AST stayed unchanged.
The final matrix was acquired with the stricter tool, and every actual result
matches the preserved earlier matrix. No register normalization or memory mask
was introduced.

For CPU-free private replay, use these directory layouts: reports
`fs-find-EN.json.gz`/IT and`conditional-public.json.gz`; raw directories
`raw-EN`/IT and`conditional-public-raw`; parent reports
`read-caller-EN.json.gz`/IT; ROM links`r4-EN.nds`/IT; recovered Find recipe
`fs-find-path.o` plus its`manifesto.json`; parent project directories
`public-build-EN`/IT and`build-EN/teams.o`/IT. Then run:

```sh
SGP_FS_FIND_REPORT_DIR="$SGP_OUT" \
SGP_FS_FIND_RAW_DIR="$SGP_OUT" \
SGP_FS_FIND_ROM_DIR="$SGP_ROM_LINKS" \
SGP_FS_FIND_PARENT_DIR="$SGP_CALLER_REPORTS" \
SGP_FS_FIND_RECIPE_DIR="$SGP_OUT/recipe" \
SGP_FS_READ_CALLER_READ_RECIPE="$SGP_READ_RECIPE" \
SGP_FS_READ_CALLER_WAIT_RECIPE="$SGP_WAIT_RECIPE" \
SGP_REMATCH_OBJECT_DIR="$SGP_REMATCH_CAMPAIGN" \
SGP_STRATEGY_OBJECT_DIR="$SGP_STRATEGY_CAMPAIGN" \
python3 -m unittest discover -s source/features/trainer-strategy/test \
  -p 'test_fs_find*.py' -v
```

The shared320-byte instruction SHA-256 is
`f82ac011a9c6bd2e6794370c2fc7ce7c0f26a5de6dcdf0660205f0266fb12e11`.
Retail IT's full324-byte SHA is
`45cdbe0ce1c310cc839bf34d2102ca55cd06e0378538e37e6f6160e14ad173c3`.
A useful next investigation is the complete caller's newly required BSS input
and40-byte stack ownership. Cost/risk lies in global fixture provenance and
context propagation, not in the already matched instructions. Native Send and
actual path traversal remain subsequent work; gameplay changes require a
separate maintainer decision.

The [complete Find caller case](native-fs-find-caller-source-rom-1.3.2.md) separately qualifies integration in the original initialized CPU. Its declared root input, expanded source-owned frame and matched baseline are not inferred from this isolated case.
