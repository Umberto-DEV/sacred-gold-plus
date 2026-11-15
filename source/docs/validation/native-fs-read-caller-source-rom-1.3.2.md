# Native Read/Wait in the complete trainer caller

This case composes the qualified [Read](native-fs-read-source-rom-1.3.2.md) and
[Wait/IRQ](native-fs-wait-source-rom-1.3.2.md) bodies into the same initialized
trainer31 CPU used by the [Seek caller case](native-fs-seek-source-rom-1.3.2.md).
FindPath and SendCommand remain explicit boundaries. No game code, installer,
ROM, save, ABI, identifier or default is changed.

## Cosa farebbe un professionista di alto livello che non sto chiedendo

Check both directions: source/recipe→object→installed bytes, and exact ROM→native
caller→ABI→source. Retain the earlier whole-caller guards while replacing the
Read model. Derive flags and volatile residuals from the actual preceding native
return; do not restore old synthetic registers to make comparisons pass. Follow
stack reuse chronologically: an old FindPath ID buffer becomes dead and is
subsequently overwritten by Read/Wait PUSH instructions. Applying model writes
last would incorrectly resurrect that buffer. Seek counterexamples where the
same payload, party and final RAM conceal a different native result.

## Il materiale più grezzo da cui partire

Supply your own exact ROMs and the project objects described by the linked
parent guides. EN152786844 bytes, SHA-256
`2e30d6960bb059615fca7527700d86f8282e82ccbe99bf62e22f027453dc3d3d`;
IT159029760 bytes, SHA-256
`13ebac02bdea3036511773587e6603ce6834e25f4b13d1a4662c3e954bfd5d4a`.
Both are IPKE revision0; IT text is localized. ARM9 file offset`0x4000`,
load`0x02000000`. The relevant bodies are in the uncompressed main section;
no overlay or autoload lifetime is introduced. Retail, inherited base, V4 and
Plus lineage of the five retained native components is established by the two
linked body guides. The recovered assembly recipes have no installer.

| Component | RAM range | Current ROM offset | Bytes |
| --- | --- | --- | --- |
| Read core | `[0x020D8104,0x020D8180)` | `0x000DC104` | 124 ARM |
| Read veneer | `[0x020D83CC,0x020D83DC)` | `0x000DC3CC` | 12 ARM + 4 literal |
| Wait | `[0x020D82FC,0x020D83BC)` | `0x000DC2FC` | 192 ARM |
| Disable IRQ | `[0x020D3A38,0x020D3A4C)` | `0x000D7A38` | 20 ARM |
| Restore IRQ | `[0x020D3A4C,0x020D3A64)` | `0x000D7A4C` | 24 ARM |

The guides publish the five byte hashes and source/compiler/header identities.
Pinned reference: [ctrl-cheeb-del/pokeheartgold at cb614ad](https://github.com/ctrl-cheeb-del/pokeheartgold/tree/cb614ad23449d5852b40321dc409c4143872b35c).
`src/filesystem.c` calls Seek/Read/Close while parsing the selected NARC member;
`lib/NitroSDK/src/fs/FS_file.c` supplies the Read/Wait counterparts. Wait calls
`OS_DisableInterrupts` and `OS_RestoreInterrupts` from `os_system.c`.
Original MW compiler/objects are unavailable. A recovered binary match and a
source-level counterpart are recorded separately from original build provenance.

The resource is NARC11/FNT`a/0/1/1`, FAT file140,11356 bytes, SHA-256
`beed8ddf861e575b9c38dfa65a6c0c51fb237305ddd73c393f5e2009fbc75260`.
Its current ROM extent is`[0x01093800,0x0109645C)`; member310 is16 bytes at
archive offset8780/ROM`0x01095A4C`, with PP15 at byte6. Full FAT/FNT/NARC
readback is inherited. ROMs, extracted data, payload fixtures, RAM, saves and
BIOS are local inputs; none belongs in Git.

## I metodi e gli strumenti da usare

### Finite contract and temporal checks

The question is whether native Read→nonbusy Wait→IRQ executes in the complete
selected caller while preserving native Init/Open/Convert/Fast/Seek/Close,
the six Pokémon, PP consumer, RNG, ownership and earlier ABI checks. The source
calls Read seven times and ignores its return values. The counter supplies
completion error1 only on the first Read, while delivering the same raw bytes
and advancing the same physical position. A success oracle must reject its
actual native−1 return even when metadata is disguised.

A finite Thumb interpreter follows the authenticated original parser from
`0x02007352` through the final Close call at`0x02007404`. It admits only the
exercised loads/stores/arithmetic/NE/GT/BLX instructions and the three qualified
API targets. Native assertion paths remain unexercised and fail closed.
It predicts full16-register entries, incoming NZCV, frame changes and the next
call from raw instructions and data, rather than copying observed ABI values.

Native Read supplies ARG48/dst,52/original length,56/length and SYNC. Modeled
Send0 consumes those actual fields and FILE.pos, copies the independently
selected raw slice and advances pos. A separate12-byte model completion then
writes stat&`~0x4F`, command0 and error0 (counter1). This is a declared field
input projection, **not complete SDK completion**. Native queue/list/archive,
card, thread, wakeup and Release ordering remain unqualified. The opaque
archive token is not a reconstructed FSArchive.

The normal Read return has R1=`0x6000009F`, R2=`0x6000001F`, R3=0,
IP=`0x020D8104`, LR=`0x020D8394`, CPSR=`0x2000003F`. Error1 returns−1 with
CPSR=`0x6000003F`. Read restores its saved registers; IRQ leaves determine R1/R2.
The subsequent source bridge overwrites the first error return before Seek2.
The second completion resets error0. Both effects are verified in the finite complete CPU matrix. This is not a
natural filesystem failure claim.

Each Read records65 native full-register contexts,16 stores,19 owned reads on
success (18 on error), the actual Send context, completion and pre/post page.
Read PUSH24 and Wait PUSH24 nest within the old240-byte frame. TOP=`0x023BEEC0`,
FILE=`0x023BEE50`, DIR=`0x023BEDD0`, API SP=TOP−136, minimum Read SP=TOP−184.
The existing global560/608 bound,56-byte guard and1124-byte OFF heap projection
are retained. No new stack or output exclusion is allowed.

A4096-byte page witness checks the entire frame and payload plus all other page
bytes. Overlapping frame/payload predictions must agree. The producer compares
all actual bytes outside that page and records hashes. Those hashes are an
observation, not an independent reconstruction. The first Read of a representative
run also exports compressed full4MiB before/after RAM for independent replay.
Sparse initialized state and declared host services do not establish boot.
Unicorn2.1.4 model17 is Cortex-A15: this checks the admitted ARMv5TE instruction
semantics, without an ARM946 hardware, IRQ-delivery or timing claim.

### Reproduction with local inputs

Use Python3, ndspy, Capstone, Unicorn2.1.4/model17, and the qualified project
objects. The parent guides build `rematch-variants.o`, `rematch-stub.o`,
`teams.o`, `fs-read-core.o`, `fs-read-wrapper.o`, and the three `fs-wait-*.o`
objects with authenticated compiler/flags/reference headers. The caller verifier
independently parses their ELF text, rejects relocations and compares exact raw
ROM bytes. No recompile or ROM composition is needed for this integration.

Define the paths below for your own files. Outputs must be fresh, private and
outside `source/`. Repeat with IT and its exact ROM/project objects.

```sh
python3 source/features/trainer-strategy/tools/attribuisci_fs_read_chiamante.py \
  --rom "$SGP_ROM" --language EN --objects "$SGP_REMATCH_OBJECTS" \
  --strategy-object "$SGP_TEAMS_OBJECT" --read-recipe "$SGP_READ_RECIPE" \
  --wait-recipe "$SGP_WAIT_RECIPE" --readback-only \
  --json "$SGP_OUT/read-caller-readback-EN.json.gz"

python3 source/features/trainer-strategy/tools/attribuisci_fs_read_chiamante.py \
  --rom "$SGP_ROM" --language EN --objects "$SGP_REMATCH_OBJECTS" \
  --strategy-object "$SGP_TEAMS_OBJECT" --read-recipe "$SGP_READ_RECIPE" \
  --wait-recipe "$SGP_WAIT_RECIPE" --probe --raw-dir "$SGP_OUT/probe-raw" \
  --json "$SGP_OUT/read-caller-probe-EN.json.gz"

python3 source/features/trainer-strategy/tools/attribuisci_fs_read_chiamante.py \
  --rom "$SGP_ROM" --language EN --objects "$SGP_REMATCH_OBJECTS" \
  --strategy-object "$SGP_TEAMS_OBJECT" --read-recipe "$SGP_READ_RECIPE" \
  --wait-recipe "$SGP_WAIT_RECIPE" --raw-dir "$SGP_OUT/raw-EN" \
  --json "$SGP_OUT/read-caller-EN.json.gz"

python3 -m unittest discover -s source/features/trainer-strategy/test \
  -p 'test_fs_read_caller*.py' -v
```

For private CPU-free replay, provide report directories containing
`read-caller-EN.json.gz` and IT, raw directories `raw-EN` and IT with the eleven
numbered JSON records and representative full RAM pairs. Set:

```sh
SGP_FS_READ_CALLER_REPORT_DIR="$SGP_CALLER_REPORTS" \
SGP_FS_READ_CALLER_RAW_DIR="$SGP_CALLER_RAW" \
SGP_FS_READ_CALLER_ROM_DIR="$SGP_ROM_LINKS" \
SGP_FS_READ_CALLER_READ_RECIPE="$SGP_READ_RECIPE" \
SGP_FS_READ_CALLER_WAIT_RECIPE="$SGP_WAIT_RECIPE" \
SGP_FS_SEEK_REPORT_DIR="$SGP_SEEK_REPORTS" \
SGP_REMATCH_OBJECT_DIR="$SGP_REMATCH_CAMPAIGN" \
SGP_STRATEGY_OBJECT_DIR="$SGP_STRATEGY_CAMPAIGN" \
python3 -m unittest discover -s source/features/trainer-strategy/test \
  -p 'test_fs_read_caller*.py' -v
```

Replay authenticates runtime identities, exact recipes, distinct matrix cells,
all original parent guards, raw/report equality and full RAM witness hashes.
It independently compares the outside-page bytes and rejects forged registers,
completion, flow, duplicate reads/models, native stores and unowned page writes.

The portable bridge/context/page tests need no ROM. The optional prefix replay
uses `SGP_FS_SEEK_REPORT_DIR` with the previously qualified Seek report; missing
private inputs produce an explicit skip. A final private qualification requires
zero skips. Raw per-run evidence is saved **before** semantic evaluation. Keep
argv, exit codes, logs, source snapshots/hashes and OS peak RSS in the private
case. Use one producer,180s/1GiB RSS/2MiB log/16MiB case caps and at least10GiB
free after peak; do not write original fixtures.

### Classification and remaining links

| Conclusion | Scope |
| --- | --- |
| Documented provenance | Pinned source counterparts and qualified parent recipes/header/toolchain receipts |
| Reconstructed binary match | Five retained native components,376 bytes including4-byte literal, independent ROM/ELF readback |
| Demonstrated semantic equivalence | Twenty-two initialized complete caller runs, with explicit Find/Send/completion boundaries |
| Observed activation | Seven native Read/Wait/IRQ calls per complete caller in EN/IT; natural upstream activation remains unobserved |
| Unattributed links | Native Find/Send/completion/list/queue/card, busy Wait, natural upstream activation and hardware |

The reusable additions are the finite source bridge, temporal frame composition,
Read page witnesses and exact contextual ABI checks. A concrete follow-up is
attribution of Send0 and its state dependencies; cost/risk is substantially
higher because queue/thread/archive ownership replaces the current finite field
projection. No gameplay fix or optimization follows from unchanged payloads.

The first complete EN probe passed732 reader hooks,266 unique native starts and169 native stores,14.519s/595017728 bytes OS peak RSS. Independent raw replay bound57 archived source identities and the full4MiB first-Read pair:48 changed bytes, all inside the captured page, with byte-for-byte equality outside it. The final EN/IT matrix is acquired below.


The final matrix passed22 complete caller executions,11 per language:
four distinct Plus0/1 × seed inputs, two OFF, alternate fill, volatile clobber,
Close truthy2, Read-Send FALSE and first completion error1. All154 Read/Wait
invocations run in their original complete caller CPU, with732 reader hooks,
266 unique native starts and169 native stores per ON caller. EN126.784s/
634421248 bytes OS peak RSS; IT126.983s/642465792 bytes. These are host costs,
not game timings. Five counted source recipes and one unchanged-code namespace
binding authenticate the composition across57 runtime identities.

Error1 produces native−1 and failure flags after the same delivered first slice.
The next Thumb bridge overwrites that return; the error word persists through
Seek2 until the second completion resets it. Later complete Read records,
Close, six Pokémon, PP flow/stores/checkpoint, RNG and whole final RAM agree
with success. Disguising both variant and error-policy metadata still rejects
the counter on its actual native return. This does not establish universal error
handling or naturally occurring failure behavior. Send FALSE with raw delivery
is also a deliberate ABI control, rather than a real failed filesystem operation.

Eighteen tests passed with zero skips:13 portable tests and five private replay
tests, including the acquired prefix. The bounded command took11.055s with
874020864 bytes OS peak RSS. Raw/report comparison covers every matrix cell;
independent full4MiB pairs cover the first Read of one positive per language.
Other calls have exact page witnesses and producer byte comparisons outside it;
no independent full-RAM artifact is claimed for every Read.

Two oracle issues were found before closure. Strict unsigned32 checks now reject
Python bool/zero aliases in full-register receipts. An OFF replay initially
called a positive-only constructor ledger check; that ledger is deliberately
absent with logging disabled. OFF now retains native guards, temporal checks and
the inherited paired functional/phase oracle, excluding only the disabled store
logs, including nested Init. Existing raw OFF data passed the corrected check;
the producer AST stayed unchanged. Earlier raw records and source snapshots
remain private evidence. No added RAM mask or register restoration was used.

An evidence-backed maintenance opportunity is to diagnose ignored Read failures
at the source parser boundary. This counter proves a finite ignored−1 return,
with an explicitly supplied error field and successful payload. Establishing a
real failure, an appropriate fallback and save/ABI compatibility would require
native Send/completion attribution and new tests. No game behavior is changed
here; any correction or optimization requires a separate maintainer decision.

Against the corresponding Seek-parent positives, complete parties, prepared Trainer, RNG and whole final RAM agree, with455 extra guest steps. The PP trace retains the actual changed R2/IP contexts; five RAM transition hashes in the second species-name phase also differ. Those phase observations are preserved, so complete traces are not claimed identical to the parent.

The next [relative Find wrapper case](native-fs-find-source-rom-1.3.2.md) attributes the remaining modeled Find in an isolated copied context, with explicit BSS input and Send4 limits. Complete parent integration is a separate ownership/ABI contract.

The [complete Find caller case](native-fs-find-caller-source-rom-1.3.2.md) replaces this case's remaining Find model while retaining these Read/Wait checks.
