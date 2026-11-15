# Native path-conversion wrapper and two Init lifetimes

This extends the [Open case](native-fs-open-source-rom-1.3.2.md) through the
installed `FS_ConvertPathToFileID`. The same CPU now executes the wrapper and
a second native Init on its local directory. `FSi_FindPath`, OpenFast and
Seek/Read/Close remain explicit models. No ROM, game behavior or save changes.

## Cosa farebbe un professionista di alto livello che non sto chiedendo

Distinguish two calls to the same code by object, stack and return ISA. Verify
source/recipe→ELF→installed bytes and ROM→caller→source in both directions.
Check ARM ABI, saved R3, aggregate output, conditional effects and object
lifetime. Seek a counterexample with correct final output but incorrect Init.
Keep original compiler provenance, recovered bytes and finite execution claims
separate. Review addresses and counterproofs against raw evidence independently.

## Il materiale più grezzo da cui partire

Use your own authenticated inputs from the
[parent input guide](native-party-caller-source-rom-1.3.2.md#il-materiale-più-grezzo-da-cui-partire).
Current EN:152786844 bytes, SHA-256
`2e30d6960bb059615fca7527700d86f8282e82ccbe99bf62e22f027453dc3d3d`;
IT:159029760 bytes, SHA-256
`13ebac02bdea3036511773587e6603ce6834e25f4b13d1a4662c3e954bfd5d4a`.
Both headers are `IPKE`, revision0, including the text-localized IT image.
ARM9 starts at ROM `0x4000`, loads at `0x02000000`; this body is in its main
section, without overlay, compression or autoload at this address. ARM7 and
full boot are outside the initialized ARM9 contract.

Convert occupies RAM `[0x020D8180,0x020D81C0)`, physical ROM `0x000DC180` in
both current images:64 bytes,16 ARM starts, SHA-256
`8455d062eee662f58fefa731950eab06ecedb77279478b2ef41123ab5128d172`.
The exclusive end starts OpenFileDirect, which is excluded. No pool or embedded
data occurs in this body. BL at `0x020D8194` targets Init `0x020D7F98`;
BL at `0x020D81A8` targets FindPath `0x020D7FC0`.

The documented counterpart is
`lib/NitroSDK/src/fs/FS_file.c::FS_ConvertPathToFileID` in
[ctrl-cheeb-del/pokeheartgold](https://github.com/ctrl-cheeb-del/pokeheartgold/tree/cb614ad23449d5852b40321dc409c4143872b35c),
pin `cb614ad23449d5852b40321dc409c4143872b35c`, file SHA-256
`7b54df220e89b6786743c2996e1e085bd29a9774a96af3551c84e600086e8e8f`.
It declares a local FSFile, initializes it, calls FindPath with directory,
path, output FSFileID and NULL, then normalizes the result. Actual ARM32 headers
verify FSFile72 and FSFileID8; a historical comment suggesting80 is not a layout
proof. No original SDK compiler or object is available.

The resource remains [custom move310 PP15](native-pp-caller-source-rom-1.3.2.md):
NARC11, FNT `a/0/1/1`, FAT140,16-byte member310, byte6. Its raw FAT/FNT/NARC
selection and ndspy readback remain checked. Keep ROMs, extracted retail bytes,
RAM, Pokémon packets, saves and BIOS private; the repository supplies methods,
recipes, hashes and tests rather than those fixtures.

## I metodi e gli strumenti da usare

The [assembly recipe](../../features/trainer-strategy/sorgenti/fs-convert.S)
and [builder](../../features/trainer-strategy/tools/compila_fs_convert.py)
reconstruct exactly64 bytes, including the two ARM BL displacements computed
from explicit sites using PC+8 and signed24-bit arithmetic. The strict project
ELF loader remains unchanged. Apple Clang21 `clang-2100.4.1.1` was authenticated
by SHA-256 `fc5e3cbba6ad54059295cad716aacb05ace8235f5f7a6031f1d8c15d24bd6d66`;
target `armv5te-none-eabi -mcpu=arm946e-s -marm`. Optional header assertions
record18 actual header dependencies. This recovered assembly match does not
reconstruct the original C compiler invocation.

From repository root, use Python3 with `source/requirements.txt` dependencies
and a compatible Clang. Define the private paths as in the parent guide:

```sh
python3 source/features/trainer-strategy/tools/compila_fs_convert.py \
  --uscita "$PRIVATE/fs-convert-recipe" --cc clang --reference "$REFERENCE"
python3 source/features/trainer-strategy/tools/rileggi_fs_convert.py \
  --retail "$RETAIL" --base "$BASE11" --v4 "$V4" --rom "$R4" \
  --language EN --recipe-object "$PRIVATE/fs-convert-recipe/fs-convert.o" \
  --json "$PRIVATE/fs-convert-history.json"
python3 source/features/trainer-strategy/tools/attribuisci_fs_convert.py \
  --rom "$R4" --language EN --objects "$REMATCH_OBJECTS" \
  --strategy-object "$TEAMS_OBJECT" --json "$PRIVATE/fs-convert-EN.json.gz"
```

Repeat with corresponding IT inputs and fresh private outputs. Manifests
contain local paths and remain private. `--readback-only` verifies current
composition without CPU execution. The
[lineage reader](../../features/trainer-strategy/tools/rileggi_fs_convert.py)
parses ELF independently and reads only the new64-byte question across
retail→base1.1→V4→r4. Legacy compressed/autoload images use decoded addresses;
no direct physical offset is inferred. A matching window does not establish
whole-image equivalence or historical activation.

The [verifier](../../features/trainer-strategy/tools/attribuisci_fs_convert.py)
and [adapter](../../features/trainer-strategy/test/fs_convert_bench.py) reuse
immutable, hash-checked parents through11 explicit source recipes and41 source
identities. Six runtime recipes, three context oracles, one native oracle and
one OFF oracle preserve prior contracts. Source drift is rejected.

```text
native custom PP caller → native NARC parser → outer Init → native Open
 → native Convert: PUSH R3/R4/R5/LR, reserve directory72
   → same native Init body, distinct directory and ARM return
   → modeled FindPath(directory, path, outputID, NULL): writes caller ID8
   → native BOOL normalization, POP restores saved R3/R4/R5 and ARM PC
 → native Open LDM reads ID8 → modeled OpenFast → Thumb parser continuation
 → modeled Seek/Read/Close, native parser/getter/setter → complete six-Mon caller
```

TOP/destination=`0x023BEEC0`; Open's ID8 is TOP−152=`0x023BEE28`.
Convert's saved16 bytes occupy `[TOP−168,TOP−152)`; its directory72 occupies
`[TOP−240,TOP−168)`, DIR/SP=`0x023BEDD0`. Convert adds88 bytes; reader peak240,
global guest peak560, within the unchanged608-byte bound. The actual56-byte
guard is `[TOP−296,TOP−240)`, global extent616: its lowest8 bytes are host
readonly observations, receive no initialization or guest writes and remain
outside the unchanged608-byte final projection. Exact240/152/136-byte frame
views are linked. The inherited1124-byte heap-only OFF projection is unchanged.

Convert entry R0=ID,R1=path,R2=R3=0,R4=outerFILE,R5=310,R6=MON,R7=0,
SP=ID,LR=`0x020D828C`,ARM. Inner Init receives R0=DIR,SP=DIR,
LR=`0x020D8198` and returns ARM; the outer file Init returns through
LR=`0x0200734B` to Thumb. Inner Init performs seven actual word stores,28 bytes,
preserving44 bytes of its own72-byte object. It does not rebind the host file
ledger. Full16-register checkpoints distinguish the two invocations.

Find receives R0=DIR,R1=path,R2=callerID,R3=NULL,SP=DIR,LR=`0x020D81AC`.
The model validates raw FNT selection and writes only ID8 in the caller, using
opaque archive token `0x021E3654` and file140. It does not write directory fields
or open an archive. The token is not reconstructed FSArchive state. Native
Convert restores saved R3=0 even when the model clobbers volatile registers;
R4=outerFILE,R5=310,SP=ID,PC=`0x020D828C`,while LR remains `0x020D81AC`.
R1/R2/IP and flags follow the declared backend policy, rather than being
normalized to the former opaque Convert model. Open then performs its actual
aggregate LDM and modeled OpenFast as in the parent case.

The reader has169 hooks,144 unique native starts and37 native stores. The
second Init repeats ten existing starts; it does not add ten unique locations.
Convert adds16 starts and four saved-word stores; inner Init adds seven stores.
There are15 modeled boundaries in five categories. On qualified Unicorn2.1.4,
CPU model17, false EQ at `0x020D81B4` still yields a code hook. Its register state
matches the following instruction: the conditional write has no effect. Runtime
identity and full registers are checked; a hook does not prove an ARM effect.
A declared Find return2 control exercises native normalization to1, without
claiming the SDK naturally returns2.

The counter changes R1 from14 to0 only at the inner Init command store,
requiring DIR/SP/LR to identify that invocation. The outer Init stays intact.
Find's opaque model still supplies the correct ID, so PP/party and whole final
RAM can remain correct despite this altered initialization. Phase RAM differs:
exactly the directory command word differs in the captured240-byte frame and
Find input; their RAM digests are not treated as equal. The positive oracle
rejects the disguised counter at full native Convert flow. This is not an
observed native Find error policy. Only the first two second-name transition
RAM digests may differ in the paired counter comparison; all other name fields
and all other name digests remain exact. No byte location is inferred from a
digest difference alone.

Portable checks need no ROM:

```sh
python3 -m unittest discover -s source/features/trainer-strategy/test \
  -p test_fs_convert_bench.py -v
```

For [pure receipt replay](../../features/trainer-strategy/test/test_fs_convert_attribution.py),
set `SGP_FS_CONVERT_ROM_DIR` to the directory containing authenticated
`r4-EN.nds`/`r4-IT.nds`, and `SGP_FS_CONVERT_REPORT_DIR` to generated
`fs-convert-EN.json.gz`/`fs-convert-IT.json.gz`. Set `SGP_REMATCH_OBJECT_DIR`
and `SGP_STRATEGY_OBJECT_DIR` as in the parent guide. Run discovery with
`-p 'test_fs_convert*.py'`. Missing private inputs cause explicit skips,
which do not establish exact-ROM verification.

Documented provenance covers the SDK counterpart and recovered recipe; exact
binary correspondence covers64 installed bytes. Finite execution covers the
initialized selected caller and declared lower models. Native Find/archive/
card/scheduler/error paths, original compiler provenance, natural encounters,
full battle, UI, SAVE/cold restart and hardware remain unverified. No gameplay
fix, speedup or reclaimed memory follows from this attribution.


The final matrix passed20 complete runs,10 per language: four Normal/Plus and
seed positives, one alternate fill, two lower-model controls, two OFF runs and
the directory-command counter. EN106.283s/595083264 bytes OS peak RSS;
IT109.293s/567689216 bytes. Thirteen portable/replay tests passed without skips,
7.586s/721092608 bytes OS peak. These are host verification costs, not game
measurements. Independent reviews covered raw/source/recipe, ABI, observer,
OFF, counter, both final languages and public CLI/documentation.

All eight positives preserve the Open-parent six packets, Trainer data, seed,
PP checkpoints and whole final4MiB RAM hash, with26 extra hooks. Exactly five
RAM digest fields in the second name's transitions differ; other name fields
and names remain exact. This describes digest differences without claiming a
byte location. All eight historical retail/base1.1/V4/r4 bodies also match the
64-byte recovered recipe and both signed BL targets, using independent ELF
readback without CPU execution. The already closed provider campaigns were
not repeated.
