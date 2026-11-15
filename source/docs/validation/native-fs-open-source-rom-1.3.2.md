# Native Open wrapper and by-value file identity

This case extends [native file initialization](native-fs-init-source-rom-1.3.2.md)
through the installed SDK`FS_OpenFile` wrapper in the same PP caller CPU.
Native instructions pass an eight-byte file identity by value and normalize
the two-call boolean expression. Path conversion and OpenFast remain explicit
lower models, along with Seek/Read/Close. No game source, ROM or save changes.

## Cosa farebbe un professionista di alto livello che non sto chiedendo

Separate wrapper semantics from the effects of its callees. Identify the
aggregate ABI, temporary buffer, ARM call/return, flags and Thumb continuation.
Verify source/recipe→ELF→ROM readback and ROM→wrapper→caller→source. Keep native
stores distinct from model writes and an opaque archive token distinct from a
native FSArchive. Seek counterproofs where a false return is ignored despite
correct payload and party output. Review addresses, frames and oracles against
raw evidence independently.

## Il materiale più grezzo da cui partire

Use your own exact r4 images and project objects from the
[parent input guide](native-party-caller-source-rom-1.3.2.md#il-materiale-più-grezzo-da-cui-partire).
EN:152786844 bytes,SHA-256
`2e30d6960bb059615fca7527700d86f8282e82ccbe99bf62e22f027453dc3d3d`;
IT:159029760 bytes,SHA-256
`13ebac02bdea3036511773587e6603ce6834e25f4b13d1a4662c3e954bfd5d4a`.
The selected resource remains the [custom move310 PP record](native-pp-caller-source-rom-1.3.2.md):
NARC11/FNT`a/0/1/1`,FAT file140,16-byte member310,byte6 PP15. Raw FAT/FNT/NARC
arithmetic and ndspy authenticate it. ROMs, extracted bytes, full RAM, Pokémon
packets, saves and BIOS remain local and are not supplied by this repository.
Both current headers are`IPKE`,revision0,including the text-localized IT image.
ARM9 loads at`0x02000000` from ROM offset`0x4000`; this qualified SDK window
maps directly into its main section. It has no overlay or autoload lifetime.
The initialized ARM9 contract does not execute ARM7 or establish a full ROM boot.

The SDK wrapper occupies RAM`0x020D8278..0x020D82C0`,72 bytes,18 ARM starts,
physical ROM`0x000DC278` in both current images. SHA-256:
`844c19c244efe83b1be9dd83f73da60917d201793d237d72cf0a429ca9158a2d`.
The exclusive end starts a separate Close function. There is no pool or
embedded data in the72-byte body. BL`0x020D8288→0x020D8180` calls path conversion;
BL`0x020D82A0→0x020D8208` calls OpenFast. Both calls remain in ARM mode.

The counterpart is`lib/NitroSDK/src/fs/FS_file.c::FS_OpenFile` in
[ctrl-cheeb-del/pokeheartgold](https://github.com/ctrl-cheeb-del/pokeheartgold/tree/cb614ad23449d5852b40321dc409c4143872b35c),
pin`cb614ad23449d5852b40321dc409c4143872b35c`. Its source SHA-256 is
`7b54df220e89b6786743c2996e1e085bd29a9774a96af3551c84e600086e8e8f`.
The C expression is path conversion into a local`FSFileID`, followed by
`FS_OpenFileFast(file, file_id)` only when conversion succeeds; the result is
normalized boolean AND. ARM32 header assertions verify FSFileID8,archive
pointer at0,file ID at4, together with the previously qualified FSFile72.

## I metodi e gli strumenti da usare

The [recovered assembly](../../features/trainer-strategy/sorgenti/fs-open.S)
and [builder](../../features/trainer-strategy/tools/compila_fs_open.py) reuse the
qualified ELF loader and original-header layout checks. The two BL words are
computed from explicit callsite and target VMAs using ARM`PC+8` and signed
24-bit displacements. The exact72-byte hash rejects callsite drift. No external
ARM relocation or unqualified linker is introduced. The source uses constants
for the callsites because this Clang rejects section-symbol differences in
`.inst` at parse time; a minimal literal/difference/absolute-expression
diagnostic isolated that restriction before the recipe was corrected.

The authenticated local assembler was Apple Clang21`clang-2100.4.1.1`, SHA-256
`fc5e3cbba6ad54059295cad716aacb05ace8235f5f7a6031f1d8c15d24bd6d66`,
target`armv5te-none-eabi -mcpu=arm946e-s -marm`. The recipe reconstructs bytes,
not the original SDK compiler invocation. Optional layout compilation uses the
clean pinned reference's actual headers, records18 dependency hashes and checks
the two-word aggregate. It does not rebuild the wrapper's native callees.

From the repository root, using Python3 with the pinned dependencies in
`source/requirements.txt` and an available compatible Clang:

```sh
python3 source/features/trainer-strategy/tools/compila_fs_open.py \
  --uscita "$PRIVATE/fs-open-recipe" --cc clang --reference "$REFERENCE"

python3 source/features/trainer-strategy/tools/rileggi_fs_open.py \
  --retail "$RETAIL" --base "$BASE11" --v4 "$V4" --rom "$R4" \
  --language EN --recipe-object "$PRIVATE/fs-open-recipe/fs-open.o" \
  --json "$PRIVATE/fs-open-history.json"

python3 source/features/trainer-strategy/tools/attribuisci_fs_open.py \
  --rom "$R4" --language EN --objects "$REMATCH_OBJECTS" \
  --strategy-object "$TEAMS_OBJECT" --json "$PRIVATE/fs-open-EN.json.gz"
```

Use corresponding IT inputs for IT. Outputs must be fresh and outside`source`.
Generated manifests contain local paths and stay private. Add`--readback-only`
to verify composed current-code/object identity without a CPU. The
[lineage reader](../../features/trainer-strategy/tools/rileggi_fs_open.py) uses
the independently parsed ELF section, checks signed BL target arithmetic and
authenticates each historical input. Compressed/autoload code uses decoded
sections without an inferred direct physical offset. A matching body does not
establish historical activation or whole-image equivalence.
All eight tested retail/base1.1/V4/r4 wrappers match the current72-byte recipe
and the same two BL targets. No previous NARC/provider campaign was repeated.

The [caller verifier](../../features/trainer-strategy/tools/attribuisci_fs_open.py)
and [adapter](../../features/trainer-strategy/test/fs_open_bench.py) authenticate
the immutable Init/PP parents and enumerate exact source edits. Earlier readers
keep their qualified contracts. Only the first custom move310 PP Open after
CreateMon returns is selected; the earlier default-learnset occurrence remains
separate.

```text
native PP reader/parser
 → native Init (seven field stores)
 → Thumb BLX at0200734E → ARM Open020D8278
   → PUSH savedR4/LR8; reserve localFSFileID8
   → modeled ConvertPath(&id, actual path): raw FNT file140, opaque archive token
   → native LDM reads two actual ID words
   → modeled OpenFast(file, id.arc, id.file_id), passed by value in R1/R2
   → native CMP / conditional return normalizes result to1
 ← Thumb02007352 → Seek/Read/Close models with native NARC parsing
 ← PP getter/arithmetic/setter → six Pokémon and complete caller return
```

PP TOP/destination is`0x023BEEC0`,parserSP=TOP−136,file=TOP−112.
Open's PUSH8 plus local8 use`[TOP−152,TOP−136)`: ID8 at`0x023BEE28` and
savedR4/LR8 at`0x023BEE30`. The original parser frame136 remains protected;
the effective reader frame is152,global peak472. The old guard overlapped the
new16 bytes, so the new56-byte guard is`[TOP−208,TOP−152)`,global528,within
the existing608-byte full-caller limit. Its before-image is captured, including
the16 newly observed lower bytes; no assumed poison or arbitrary mask is used.

At entry,R0=file,R1=path,R2=0,R3=0,R4=path,R5=310,R6=MON,R7=0,followed by the
parent's high-register cookies. R2 is a volatile residue, not a third Open
argument. Conversion receives R0=localID,R1=path,SP=TOP−152,ARM LR`0x020D828C`.
Native`LDM R1,{R1,R2}` then loads archive token and file140 into the argument
registers for OpenFast,whose ARM LR is`0x020D82A4`.

Successful Open restores R4/SP and loads saved`0x02007353` into PC,returning
to Thumb`0x02007352`; LR itself remains`0x020D82A4`. R0 is canonical1 and
CPSR`0x2000003F`. Full16-register checkpoints, both model ARM returns and
the native LDM reads are checked. The model's archive token`0x021E3654` is never
dereferenced here. It does not prove a native FSArchive or path resolver.

The wrapper's only native memory writes are its two PUSH words. Conversion's
exact8-byte ID write is separately attributed to the model. Neither the wrapper
nor the OpenFast model fabricates guest FSFile fields: native Init's72-byte
object remains intact while the host ledger opens the raw archive. This is
wrapper/callee-contract execution, not native OpenFast or filesystem state.

The positive reader has128 observed native locations (103 parser,10 Init,15
Open),15 modeled boundaries and143 hooks. There are26 native stores,including
Init's seven and Open's two PUSH words. The full152-byte before/after frame
and inherited136-byte views are cross-checked; the actual guard56,borrowed
payload16 and saved upper16 remain protected. OFF executes the same native
writes and modeled ID write,disabling only native store logs. No file/stack
projection is added to the inherited1124-byte heap projection.

A modeled OpenFast result2 exercises normalization to native R0=1. This is a
declared noncanonical truthy backend control,not an observed SDK result2.
The counter instead changes only R0 from1 to0 after a valid modeled OpenFast
return. The host archive remains open; native Open takes its false path and
returns0/CPSR`0x6000003F`. The parser overwrites that return value and proceeds.
Correct PP/party output therefore cannot prove the wrapper's boolean path.
This does not exercise an actual failed SDK open or its error policy.
Conversion-failure short-circuiting is attributed statically from source and
the BEQ target; it is not executed here. The counter reaches the shared false
exit after OpenFast while retaining a valid modeled archive.

On qualified Unicorn2.1.4 CPU model17,the three false NE instruction locations
still produce code hooks while their effects remain suppressed. The counter
therefore has18 Open hook locations,131 native locations and146 reader hooks,
three more than the positive. Full register/stack checkpoints distinguish a
hook from an executed conditional effect. Runtime identity is checked for this
counter; the assembler target does not establish ARM946 hardware timing.

Portable checks need no ROM:

```sh
python3 -m unittest discover -s source/features/trainer-strategy/test \
  -p test_fs_open_bench.py -v
```

For [receipt replay](../../features/trainer-strategy/test/test_fs_open_attribution.py),
set`SGP_FS_OPEN_ROM_DIR` to your authenticated`r4-EN.nds`/`r4-IT.nds` directory
and`SGP_FS_OPEN_REPORT_DIR` to the generated`fs-open-EN.json.gz`/`fs-open-IT.json.gz`
reports. Set`SGP_REMATCH_OBJECT_DIR` and`SGP_STRATEGY_OBJECT_DIR` as in the parent
guide (`public-build-EN`/`public-build-IT`,and`build-EN`/`build-IT` containing
`teams.o`). Run discovery with`-p 'test_fs_open*.py'`. Missing private inputs
cause explicit skips; they do not establish exact-ROM verification.

The final matrix has20 complete runs,10 per language: four Normal/Plus and
seed positives,one alternate fill,two lower-model controls,two OFF runs and the
false-return counter. EN106.076s/598016000 bytes OS peak RSS;
IT107.389s/567574528 bytes. Fifteen portable/replay tests passed without skips,
7.653s/720568320 bytes OS peak. These are host verification costs,not game
timings. Independent reviews checked source/raw/recipe,aggregate ABI,frame and
guard,model effects,conditional hooks and captured final observations.

All eight final positives match the corresponding Init-parent party,Trainer,
seed,PP checkpoints,names and whole final4MiB RAM hash,with16 extra hooks. The
reader-phase RAM differs because the native wrapper and modeled ID now write
their actual16-byte temporary area. The false-return counter has the same
phase and final RAM as its positive,despite a different boolean path. The
positive oracle rejects it after its counter label is hidden.

The case has no claim of original compiler provenance,native path conversion,
OpenFast/Seek/Read/Close,card/scheduler/error paths,natural activation,whole
battle,UI,SAVE/cold restart or hardware. No gameplay fix,speedup or reclaimed
memory follows from replacing a model in a host verification bench.
