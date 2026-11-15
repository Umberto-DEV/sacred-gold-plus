# Native nonbusy Wait and IRQ helpers

This extends the [isolated Read case](native-fs-read-source-rom-1.3.2.md) through
`FS_WaitAsync` and its two IRQ helpers in the same isolated CPU. Wait now reads
actual guest fields and returns its own BOOL. A declared completion-field
projection supplies those inputs after modeled Send0. Native Send, queue/archive
completion and the complete original caller remain outside this case. No game,
ROM, save, ABI or identifier changes.

## Cosa farebbe un professionista di alto livello che non sto chiedendo

Attribute the state needed by Wait before replacing its former BOOL model.
Distinguish a field projection from complete SDK completion. Check raw encodings,
source and actual CPU state when a disassembler prints an APSR alias for MRS:
the full CPSR control bits matter here. Verify both source/recipe→ELF→ROM and
ROM→Read caller→Wait/IRQ→source. Seek identical bytes with an incorrect IRQ
return state, and a native failure return after the same raw payload. Review
stack reuse, flags, mode, buffer ownership and OFF neutrality independently.

## Il materiale più grezzo da cui partire

Use developer-owned exact inputs, objects and reports from the
[parent guide](native-fs-read-source-rom-1.3.2.md#il-materiale-più-grezzo-da-cui-partire).
Current EN:152786844 bytes, SHA-256
`2e30d6960bb059615fca7527700d86f8282e82ccbe99bf62e22f027453dc3d3d`;
IT:159029760 bytes, SHA-256
`13ebac02bdea3036511773587e6603ce6834e25f4b13d1a4662c3e954bfd5d4a`.
Both IPKE revision0; IT is text-localized. ARM9 file offset`0x4000`,
load`0x02000000`. These bodies occupy the main ARM9 section without overlay,
autoload or compression lifetime. ROMs, extracted retail data, RAM, payloads,
saves and BIOS remain private. Initialized isolated CPUs do not establish boot.

| Component | RAM range | Current ROM offset | SHA-256 |
| --- | --- | --- | --- |
| Wait192B/48 ARM starts | `[0x020D82FC,0x020D83BC)` | `0x000DC2FC` | `74a4b27bab72e380afd92fbdf9cae9b524f24641668dae54a2af802184caf167` |
| Disable IRQ20B/5 ARM | `[0x020D3A38,0x020D3A4C)` | `0x000D7A38` | `a8cdb747f9936730571b220bb9570615892665b120713ffc59b1cb2d7dee76ff` |
| Restore IRQ24B/6 ARM | `[0x020D3A4C,0x020D3A64)` | `0x000D7A4C` | `46b5111b6fad094dfff177dca974d33b477cb72772ecfe95b74b1c7f656bc4fd` |

All three ranges are byte-identical across the tested retail, inherited base,
V4 and exact Plus images. They are retained native HGSS SDK code within this
coverage, rather than a new Plus-compiled insertion. The recovered recipes are
attribution artifacts with no installer. All236 bytes here are ARM instructions;
no padding or embedded data is included. Other ranges remain unclassified.

The source counterpart is pinned at
[ctrl-cheeb-del/pokeheartgold](https://github.com/ctrl-cheeb-del/pokeheartgold/tree/cb614ad23449d5852b40321dc409c4143872b35c),
commit`cb614ad23449d5852b40321dc409c4143872b35c`:
`lib/NitroSDK/src/fs/FS_file.c::FS_WaitAsync` and
`lib/NitroSDK/src/os/os_system.c::OS_DisableInterrupts`/`OS_RestoreInterrupts`.
`fs_send_command.c::FSi_SendCommand` assigns command0;
`FS_command.c::FSi_ReleaseCommand`, reached through synchronous completion,
clears CANCEL|BUSY|SYNC|ASYNC|OPERATING mask`0x4F` and writes the result to error.
The build receipt records all four source-file/function hashes and the18 real
header dependency hashes. Original headers assert FSFile72, stat12/command16/
error20, BUSY1, SYNC4, SUCCESS0, FAILURE1, IRQ-disable`0x80` and four-byte
OSIntrMode. The IRQ counterpart already contains inline assembly; Wait's
assembly is a recovered recipe. Neither establishes original MW object history.

Wait's five signed ARM BL sites are`0x020D8308`→Disable,
`0x020D8350`/`0x020D8370`→SleepThread`0x020D1E7C`,
`0x020D8390`→Restore and`0x020D83A0`→ExecuteSync`0x020D7744`.
Binary readback checks all five; only Disable/Restore execute in this experiment.
Busy, owner, SleepThread and ExecuteSync paths remain unexercised.

## I metodi e gli strumenti da usare

The finite question is whether the seven derived Read inputs, after explicit
completion-field input projection, take the native nonbusy Wait path, read error,
produce the BOOL consumed by Read, and restore the incoming IRQ bit while
preserving saved state. The error1 control retains raw delivery and position
advance but must return FALSE from native Wait and−1 from Read. Its modeled
error word differs, so it must not be called identical whole RAM. An I1 input
instead preserves memory and byte count while changing the expected control ABI.

### Provenance and modeled completion

The preparer authenticates the current ROM, full Seek source/recipe proof and
four distinct Plus/seed positives, then replays the qualified49-row Read parent
without running a parent CPU. Seven baseline entry16/frame templates retain the
[parent's source-bound derivation](native-fs-read-source-rom-1.3.2.md#input-derivation-and-resources).
They are not captured full natural entry snapshots. Sparse code and copied
frames initialize fresh canary RAM; each input is an independent isolated run.
I1 is a declared metamorphic change to the derived input's CPSR I bit.

The native Read core still writes dst48/original length52/clamped length56 and
SYNC. Modeled Send0 copies authenticated raw bytes and advances physical FILE.pos.
Immediately afterward a **modeled12-byte, three-word field projection** writes:

| Field | Projected final input | Source owner |
| --- | --- | --- |
| stat12 | previous stat &`~0x4F` | ReleaseCommand |
| command16 | READFILE0 | SendCommand |
| error20 | SUCCESS0, or FAILURE1 in the declared counter | ReleaseCommand result |

This is source-derived final field input, not a reconstruction of SDK ordering
or full completion. Known link-list, queue, archive flags/procedures, thread,
card and wakeup effects remain excluded. The opaque archive token is never
dereferenced by the nonbusy Wait path. All three modeled words are recorded
separately from the16 native word stores (Read10 plus Wait's six PUSH words).
A bulk host field write is not a native store observation.

The raw resource remains NARC11/FNT`a/0/1/1`, FAT file140,11356 bytes,
SHA-256`beed8ddf861e575b9c38dfa65a6c0c51fb237305ddd73c393f5e2009fbc75260`.
Current physical top`0x01093800`/bottom`0x0109645C` come from independent parent
FAT/FNT/NARC readback. The seven positions/lengths and caller LRs remain those
in the Read guide; the final16-byte member310 has PP15 at byte6. No new data
layout, identity or resource routing is introduced.

### Native path, ABI and IRQ capability

The executed Wait path contains20 starts, including the status test, Disable,
Restore and error test. Its192-byte extent has48 admissible binary starts;
28 unexercised starts do not become execution coverage. Disable/Restore add11
starts. Together with Read's34, the finite combined path has65 native hooks,
one Send boundary and the original Thumb caller return:67 steps. Instruction
and read/write ownership are strict; a false conditional hook is not an effect.

Wait PUSH24 nests inside Read PUSH24. With TOP=`0x023BEEC0`, FILE=`0x023BEE50`
and API SP=TOP−136, minimum SP is TOP−184, inside the existing240-byte frame.
No new RAM exclusion or guard expansion is needed. Native fields, saved frames,
modeled projection, raw output, all16 registers and the exact full4MiB RAM delta
are checked. OFF retains active guards and functional state without trace logs.

The normal API return preserves R4–R11/SP, restores R3=0 and leaves
IP=`0x020D8104`, LR=`0x020D8394`, R1=`0x6000009F`,
R2=`0x6000001F`|initial I. CPSR is`0x2000003F`|initial I on success,
`0x6000003F`|initial I on error. With Send volatile clobber, IP remains the
explicit clobbered value; the IRQ leaves overwrite R1/R2 themselves.
These values differ from the former Wait model and must not be normalized away.

Unicorn2.1.4 model17 is **Cortex-A15**, not ARM9 silicon. The admitted guest
instructions are the recovered ARMv5TE code. Results establish their exercised
instruction semantics, not ARM9 timing, IRQ delivery or hardware behavior.
A separate capability qualification ran16 CPSR combinations (four NZCV patterns,
I0/I1, F0/F1), each with observation ON and OFF:32 Disable→Restore paired runs,
64 leaf executions. Every5+6 instruction/register state, endpoint and whole RAM
hash matched; I restored exactly while F, mode and flags remained intact.
Four independent I/F/NZCV/mode mutants were rejected. Raw MRS encodings
`E10F0000`/`E10F1000` select CPSR (SPSR bit22 clear); MSR uses control mask c.
The disassembler's APSR alias does not remove the control bits from the proof.
The main Read matrix uses privileged SYS mode and baseline F0 only.

### Reproduction

Dependencies: Python3, ndspy, Capstone, Unicorn2.1.4/model17, ARMv5TE-capable
Clang and the pinned original-reference headers. Generate Seek and Read reports
and project objects using their linked guides. Outputs must be fresh and local;
no command patches or installs a ROM. The builder produces three small objects,
records compiler identity/flags and verifies236 bytes with the qualified loader.
The readback parses ELF section bounds and rejects text relocations independently.

```sh
python3 source/features/trainer-strategy/tools/compila_fs_wait.py \
  --cc "$SGP_CLANG" --reference "$SGP_REFERENCE" --uscita "$SGP_OUT/recipe"

python3 source/features/trainer-strategy/tools/attribuisci_fs_wait.py \
  --rom "$SGP_ROM" --language EN --irq-capability \
  --raw-dir "$SGP_OUT/irq-raw" --json "$SGP_OUT/irq-public-EN.json.gz"

python3 source/features/trainer-strategy/tools/attribuisci_fs_wait.py \
  --rom "$SGP_ROM" --language EN --parent-report "$SGP_READ_REPORT" \
  --seek-report "$SGP_SEEK_REPORT" --objects "$SGP_REMATCH_OBJECTS" \
  --strategy-object "$SGP_TEAMS_OBJECT" --recipe-dir "$SGP_OUT/recipe" \
  --prepare-only --json "$SGP_OUT/prepared.json"

python3 source/features/trainer-strategy/tools/attribuisci_fs_wait.py \
  --rom "$SGP_ROM" --language EN --parent-report "$SGP_READ_REPORT" \
  --seek-report "$SGP_SEEK_REPORT" --objects "$SGP_REMATCH_OBJECTS" \
  --strategy-object "$SGP_TEAMS_OBJECT" --recipe-dir "$SGP_OUT/recipe" \
  --raw-dir "$SGP_OUT/raw" --json "$SGP_OUT/fs-wait-EN.json.gz"

python3 source/features/trainer-strategy/tools/rileggi_fs_wait.py \
  --retail "$SGP_RETAIL" --base "$SGP_BASE11" --v4 "$SGP_V4" \
  --rom "$SGP_ROM" --language EN --recipe-dir "$SGP_OUT/recipe" \
  --json "$SGP_OUT/lineage-EN.json"

python3 -m unittest discover -s source/features/trainer-strategy/test \
  -p 'test_fs_wait_bench.py' -v

SGP_FS_WAIT_ROM_DIR="$SGP_ROM_LINKS" \
SGP_FS_WAIT_REPORT_DIR="$SGP_WAIT_REPORTS" \
SGP_FS_WAIT_PARENT_DIR="$SGP_READ_REPORTS" \
SGP_FS_WAIT_SEEK_DIR="$SGP_SEEK_REPORTS" \
SGP_FS_WAIT_RECIPE_DIR="$SGP_RECIPE" \
SGP_REMATCH_OBJECT_DIR="$SGP_REMATCH_CAMPAIGN" \
SGP_STRATEGY_OBJECT_DIR="$SGP_STRATEGY_CAMPAIGN" \
python3 -m unittest discover -s source/features/trainer-strategy/test \
  -p 'test_fs_wait*.py' -v
```

The IRQ-only command needs no parent reports, objects or recipe directory. It
saves32 raw records before semantic evaluation and verifies the full16-register
state,5+6 starts and unchanged RAM for all16 CPSR inputs with ON/OFF. Its output
`irq-public-EN.json.gz` must be available in the Wait report directory for replay.

Repeat the main case with IT and its own exact ROM/object/report identities. ENV directories
contain`r4-EN.nds`/IT,`fs-wait-EN.json.gz`/IT,`fs-read-EN.json.gz`/IT,
`fs-seek-EN.json.gz`/IT, the three`fs-wait-*.o` objects,
`public-build-EN`/IT and`build-EN/teams.o`/IT respectively. Missing private inputs
cause explicit replay skips; a qualified final verification requires zero skips.

Raw observations, including fault/halt states, precede semantic checks. Preserve
argv/exit/log/source hashes, source snapshots and OS peak RSS privately. Use one
producer with explicit time, RSS, log and storage caps and at least10GiB free
after peak. Never write original ROM/save fixtures. The three counted source
composition recipes authenticate the complete Read bench before deriving
prediction, collector and replay functions in isolated namespaces.

### Results, classification and remaining links

Recovered236-byte recipes/header18 and eight-image lineage are qualified:
24 component comparisons, all five Wait BLs and both call-free IRQ leaves match.
Original compiler history and legacy activation remain unknown. Legacy decoded
sections do not imply a current physical offset when compression/autoload differ.
Finite main-matrix results and costs are appended after qualification.

| Conclusion | Scope |
| --- | --- |
| Documented provenance | Pinned C/inline-asm counterparts, headers, project recipes and exact inputs |
| Reconstructed binary match | Wait192 plus IRQ20/24 in eight images with independent ELF/readback |
| Demonstrated semantic equivalence | Finite nonbusy Read→Wait/IRQ under explicit completion-field input |
| Observed activation | Isolated derived-input CPUs; not natural activation or the complete parent caller |
| Unattributed links | Native Send/release/list/queue/archive/card, busy/owner paths and hardware |

A useful next step is full original caller integration of Read/Wait with the new
ARG/stat/volatile ABI oracles. Cost is temporal ownership and context refinement;
risk is false equivalence from widened masks or restored synthetic registers.
Verification must preserve complete caller/OFF/counter checks and expose real
phase-memory/ABI differences. This is an attribution/tooling opportunity;
gameplay optimization remains a maintainer decision.

The final main matrix passed126 isolated executions,63 per language: seven
inputs × nine policies (normal, OFF, error1, Send FALSE, Send clobber, alternate
fill, I1, I1 OFF, I1/error1). EN3.463s/578846720 bytes OS peak RSS;
IT3.464s/592527360 bytes. Each ON run records65 native starts and16 stores;
all runs take67 steps. Error1 has18 owned reads; success has19.
The public IRQ-only mode independently passed32 paired runs/64 leaf executions,
2.133s/240336896 bytes OS peak, with exactly the same records as the initial
capability qualification. These are host verification costs, not game timings.

Thirteen tests (six portable, seven private replay) passed with zero skips,
5.448s/758972416 bytes OS peak. Replay authenticates55 runtime source identities,
three exact composition recipes, parent input derivation, the public IRQ grid,
all per-run raw records and the modeled/native temporal frames. Falsifiers cover
I/F/mode/NZCV, full register width, missing false hooks, field projection,
saved-word ownership, SDK ABI, fault/return state, whole RAM and duplicate cells.

OFF preserves functional registers and complete memory. I1 also preserves memory
and byte count while changing the required R2/I return state. Error1 preserves
delivered bytes and position but changes the declared error word and native
return; the exact reconstructed RAM delta permits no other change. Send FALSE
with raw delivery is an intentional ABI control, not a naturally observed SDK
failure. Full original caller integration remains a separate next verification.

The subsequent [complete Read/Wait caller case](native-fs-read-caller-source-rom-1.3.2.md) closes the initialized full-caller integration for its finite EN/IT matrix, retaining the modeled completion and natural-activation limits.
