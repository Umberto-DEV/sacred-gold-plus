# Compiling the original Reset C definition: qualified LLVM experiment

The original `MonSetMoveInSlot_ResetPpUp` C definition has been compiled into
an authenticated alternative LLVM object. Its ELF, relocation targets, code/data
boundaries and stack frame have independent readback checks. Three compiled
guest cells passed: Up3, Up0 and Up3 with observation OFF, 105586 instructions
in total. CPU-free reverification and scoped comparison against the retained
[complete native Reset case](native-mon-reset-source-rom-1.3.2.md) pass. No ROM
has been built or modified by this experiment.

## What this connects

The native baseline identifies the installed 56-byte Reset at RAM
`0x020714B0`, plain ARM9 ROM offset `0x754B0`, and its four real child calls.
Its exact EN/IT inputs, historical comparisons, source hashes and limits are
listed in the baseline guide. The current Plus EN and localized IT executables
share these selected native components; this does not make retail Italian HGSS
an interchangeable build target.

The productive source is the
[HGSS fork at cb614ad23449d5852b40321dc409c4143872b35c](https://github.com/ctrl-cheeb-del/pokeheartgold/tree/cb614ad23449d5852b40321dc409c4143872b35c).
The same complete definition appears in
[PRET HeartGold at 6bf138d6035aa6b43d6f8f4132a12df70f86dcec](https://github.com/pret/pokeheartgold/tree/6bf138d6035aa6b43d6f8f4132a12df70f86dcec).
Its 290 bytes, excluding the trailing newline, have SHA-256
`e80f65e6bfd87861d55399c0bade3e8c3beabf840a4bcf563cebaa68f53101cd`.
The [definition comparator](../../features/trainer-strategy/tools/confronta_box_move_pret.py)
selects complete global definitions, rather than callsite fragments.

For this function, `Pokemon` is an opaque pointer: the body passes it to callees
without accessing its layout. The
[compiler wrapper](../../features/trainer-strategy/tools/compila_reset_c.py)
authenticates the body, three exact prototypes, attribute IDs 58/62 and productive
`u8`/`u16` declarations, then inserts the unchanged body into a minimal C unit.
This proves compilation of that unit, not all of `pokemon.c` or its SDK headers.
The newer headers differ, and the old SDK typedef path is absent in the newer
tree. The wrapper records those source identities instead of treating the two
header sets as identical.

The authenticated compiler binary has SHA-256
`fc5e3cbba6ad54059295cad716aacb05ace8235f5f7a6031f1d8c15d24bd6d66`
and 124520368 bytes. The recorded identity is Apple clang 21.0.0
(`clang-2100.4.1.1`). Flags select `armv5te-none-eabi`, ARM946E-S, Thumb, `-Oz`,
freestanding C11, signed char, no builtins, stack protector, unwind tables,
jump tables or sibling-call optimization. Full flags and source dependencies
are recorded in the executable recipe. A different compiler needs its own
codegen qualification; `--compiler` changes the location, not the accepted hash.
The build is not claimed to be a universally hermetic toolchain.

## Object, guest linkage and ABI

One driver invocation produced an ELF32 little-endian ARM ET_REL object:
1136 bytes, SHA-256
`e6f4fa360e67810512d585c389b137c4632095c89d13251e8de04b783017863e`.
The relocated `.text` is 76 bytes, SHA-256
`7745552b68db445ba0a101912506df7cb8b66a32c5cc947e40d56e37163ba21d`.
The unchanged [text loader](../../features/native-core/tools/carica_text.py)
resolves four internal `R_ARM_THM_CALL` relocations without a linker.

| Test-memory address | Content | Destination |
| --- | --- | --- |
| `022F1000` | LDR/BX thunk, then four-byte literal | `020714E9`, native Mon veneer |
| `022F1008` | LDR/BX thunk, then four-byte literal | `0206EC41`, native SetMonData |
| `022F1010` | LDR/BX thunk, then four-byte literal | `0207332D`, native GetMoveMaxPP |
| `022F1018..022F104C` | 52-byte LLVM Reset, 22 instructions | Four calls through the three thunks |

These are real guest instructions, not host service models or ROM insertion
points. The native Mon veneer remains HGSS code. The alternative caller has
64 code bytes/28 starts and 12 literal bytes. All seven ordered `$t`/`$d` mapping
symbols are retained, including repeated names. The
[ELF reader](../../features/trainer-strategy/tools/rileggi_reset_c.py) independently
decodes raw addends and linked BL destinations and compares the complete linked
text. It also checks the single `.ARM.exidx` PREL31 relocation to root offset24
and the CANTUNWIND descriptor. That metadata is not mapped. See the
[Arm EHABI index-entry specification](https://github.com/ARM-software/abi-aa/blob/main/ehabi32/ehabi32.rst#index-table-entries)
and [ELF relocation specification](https://github.com/ARM-software/abi-aa/blob/main/aaelf32/aaelf32.rst).
The reader admits this exact qualified profile, not arbitrary ARM objects.

The LLVM caller saves eight words, using a 32-byte frame. ZeroValue is at
entry-SP−28 and PPValue at entry-SP−24. Their four-byte stores overwrite the
saved `r2` and `r3` slots. In the owned slot0 case, the zero store is already
idempotent because PUSH saved `r2=0`; the PP store replaces the entry `r3`
cookie. POP consequently returns `r1=310,r2=0,r3=15`. These volatile values,
flags, LR and dead stack must be checked per build, not normalized to the
native caller's residues. The first Box call precedes `MOVS r7,0`; it still
sees the original `r7` cookie.

## Reproduce the prepared experiment

Supply your own clean pinned source trees, exact compiler and required Plus
ROM. Keep all outputs private and outside `source/`. Source/ELF tools use Python
and Git; composition also requires the project's ndspy and Capstone versions.
Only explicit CPU modes need the qualified Unicorn backend. Dependencies and
native SDK/DIV recipes are described in the baseline guide.

```sh
python3 source/features/trainer-strategy/tools/compila_reset_c.py \
  --mode prepare --reference /path/to/productive-hgss \
  --heartgold-ref /path/to/newer-pokeheartgold --compiler /path/to/qualified-clang \
  --out-dir /path/to/private/prepared-source
```

Use `--mode compile` with a different fresh output directory to create the
object. Prepare authenticates the compiler file but never invokes it. Compile
records the argv, exit code, output/log hashes and timeout. Its stored-log cap
does not itself bound subprocess RAM; use the project's bounded producer runner.
No automatic installation, download or compiler search occurs.

```sh
python3 source/features/trainer-strategy/tools/rileggi_reset_c.py \
  --build-dir /path/to/private/compiled --reference /path/to/productive-hgss \
  --heartgold-ref /path/to/newer-pokeheartgold --out-dir /path/to/private/readback
python3 source/features/trainer-strategy/tools/qualifica_reset_c_frame.py \
  --out-dir /path/to/private/owned-frame
python3 source/features/trainer-strategy/tools/congela_reset_c.py \
  --rom /path/to/plus-en.nds --build-dir /path/to/private/compiled \
  --reference /path/to/productive-hgss --heartgold-ref /path/to/newer-pokeheartgold \
  --json /path/to/private/compiled-input.json
python3 -m unittest discover -s source/features/trainer-strategy/test \
  -p 'test_reset_c_*.py'
```

The owned nine-instruction frame program passed ON/OFF: full16 states, eight
reads, ten stores, their preimages, 32-byte peak, guards and all final pages.
It loads no ROM and executes no game function. Earlier ISA and 65536/8192
instruction limits remain unchanged.

The [attribution CLI](../../features/trainer-strategy/tools/attribuisci_reset_c.py)
has explicit `prepare`, `matrix` and CPU-free `verify` modes. Use its `--help`
for the SDK object, recipe, native-baseline and frozen-input arguments. It
rejudges the retained native Reset's three raw cells and report controls before
comparing a candidate; it never reruns the original Reset CPU. This avoids
requiring access to any maintainer-private case directory. Reproduce the native
baseline first with your own inputs as documented in its guide.

For example, after producing the native input/raw and SDK/DIV prerequisites
in the baseline guide, prepare the C comparison with fresh private outputs:

```sh
python3 source/features/trainer-strategy/tools/attribuisci_reset_c.py \
  --mode prepare --rom /path/to/plus-en.nds \
  --reference /path/to/productive-hgss --heartgold-ref /path/to/newer-pokeheartgold \
  --build-dir /path/to/private/compiled --objects /path/to/private/objects.json \
  --recipe-dir /path/to/private/sdk-recipe --div-recipe /path/to/private/div-recipe \
  --input-contract /path/to/private/compiled-input.json \
  --qualification /path/to/private/owned64.json \
  --frame-qualification /path/to/private/owned-frame/qualification.json \
  --native-input-contract /path/to/private/native-input.json \
  --native-raw-dir /path/to/private/native-matrix \
  --out-dir /path/to/private/compiled-prepared
```

Change `--mode prepare` to `--mode matrix` and supply a new output directory
to acquire the three compiled cells. Then use `--mode verify`,
`--raw-dir /path/to/private/compiled-matrix` and another fresh output directory
to rejudge saved evidence without CPU or compiler. `--raw-dir` is required only
for verify. The frame qualification defaults to the public completed owned
receipt; a freshly reproduced receipt must agree exactly. Each invocation also
checks the retained native baseline's prepared bindings, raw hashes, complete
per-build observations and recomputed historical controls.

## Execution, counterproofs and coverage

The source forecasts were frozen before the first guest instructions. The
actual candidate cells agree with them:

| Cell | Instructions | Thumb / ARM | Unique starts | Reads / stores | Peak stack |
| --- | ---: | --- | ---: | --- | ---: |
| Up3 | 35205 | 22824 / 12381 | 1347 | 7816 / 4628 | 720 bytes |
| Up0 | 35176 | 22824 / 12352 | 1318 | 7816 / 4628 | 720 bytes |
| Up3 OFF | 35205 | 22824 / 12381 | 1347 | 7816 / 4628 | 720 bytes |

Each cell uses 27 mapped pages/110592 bytes and leaves a spare return-gate
callback (N+1). There is one Uc and one uninterrupted `emu_start` per cell, no
runtime host write, callee model or phase reset. Raw is saved before judgment.
All three complete final maps have SHA-256
`5a075e2677deff9e87c1da9f7225bb647a299842a9ce58e4479a603ac84f57a5`.
That cross-profile convergence does not erase the 29-instruction difference in
the first DIV or the different transient states.

The four Mon boundaries retain keys `02AB→02B4→02B1→02A8` for Up3 and four
times `02A8` for Up0. The complete final Mon236 has SHA-256
`02a5249820ab97db2799b0e18ee906b3154915a4f42a6084bce0be4a761c9beb`,
equal to the native baseline. The actual path includes 840 payload halfword
stores, 840 private seed stores, 576 checksum reads, 20 block selectors, two
complete SDK/NARC paths and 14 real memory-read callbacks. Zero and PP Values
are published by the guest and consumed through native low-byte loads. The
zero publication and all Up0 setters are required even when idempotent.

| LLVM root BL | Guest/native route | Significant arguments | Child SP / LR |
| --- | --- | --- | --- |
| `022F1020` | `022F1000` → `020714E8` → `020714F0` | Mon,310,0 | T−32 / `022F1025` |
| `022F1030` | `022F1008` → `0206EC40` | Mon,62,T−28 | T−32 / `022F1035` |
| `022F1038` | `022F1010` → `0207332C` | 310,0 | T−32 / `022F103D` |
| `022F1046` | `022F1008` → `0206EC40` | Mon,58,T−24 | T−32 / `022F104B` |

The second MaxPP really enters with `r3=0207332D,r7=0,CPSR=6000003F`. The
first Box instead sees the original r7 cookie. The compiled void return is
`r0=2B9B,r1=310,r2=0,r3=15,IP=0,LR=0201FF59,CPSR=6000003F`; r4..r11 and SP
retain their entry values. The verifier checks these actual residues rather
than replacing them with the native caller's different volatile values.

The Box and Mon cipher seeds have distinct live addresses T−88 and T−56.
The two FILE/parser/buffer groups are T−216/T−240/T−104 and
T−184/T−208/T−72. FILE2 starts with residues from preceding Box/Mon writes,
six first-parser saved words and two first-Box PP cipher words; only one word
is untouched A5. Its input SHA-256 is
`12b5d70774ceae149b5409394199a7c97392206592d08c3285d642f682048abe`
for Up3 and `f71a7026d805aaf9fd6ad90c594b0f9ad874ca073b9ccd78c7a70dda0fcdbc4f`
for Up0. A host clear or standalone FILE fixture would lose this evidence.

Thirty-two actual transcript falsifiers are rejected: skipped idempotent
writes/Mon62, fake store preimages, narrow words, wrong consumer pointer,
missing party/seed/NARC operations, wrong second MaxPP arguments or flags,
old native Reset fetches, normalized volatile returns, injected models/host
writes and OFF journals. Three canonical-relative FAT/FNT/root mutations fail
before the source interpreter. The earlier source-shaped dry run is preserved
as control preparation; these raw checks are separate observed evidence.

The first producer initialization stopped before `emu_start`: its reader
requested the inactive native Reset from a dictionary containing only admitted
instructions. The adapter was corrected before any candidate instruction ran.
Full-resource and instruction-only decoding then agreed on all 516 starts,
and every complete source forecast remained unchanged. The failed initialization
and prior source snapshot remain separate from the subsequent three guest raw.

CPU-free verify rejudges every full16/next-PC row, read/store preimage, count
and final page against each build's own forecast. A further guarded verification
passes with Unicorn/Keystone imports and compiler processes forbidden; only the
exact read-only Git identity queries are permitted. Cross-build semantic
comparison is a second check: four complete Mon states, ordered native call
arguments and guest Value provenance, normalized callback destinations, read-only
resources, guards and callee-saved registers/SP. Code pages, volatile registers
and dead stack are validated per build and excluded from equality across builds.

Independent raw review uses a separate finite ARM/Thumb decoder rather than
the production predictor: 70381 full16 states with next-PC checks, 15632 reads
and 9256 stores for the two observed cells, forward/inverse replay of all 27
pages, current/frozen source identities and all 32 transcript edits. It also
reconstructs the scoped native-versus-LLVM semantic comparison from the actual
raw. This audits the exercised corpus, not arbitrary ARM code or hardware.

The LLVM caller uses six more instructions and eight more peak stack bytes
than the native caller in these fixtures. This is not evidence for a speedup
or a reason to replace the installed implementation. Host CPU-model instruction
counts do not measure ARM946 timing, caches, interrupts or natural activation.

Original Metrowerks code generation, full-ROM builds, Italian retail targets,
natural gameplay activation, other moves/slots/PIDs/flags, saves and physical
hardware remain outside this result. The experiment changes no game behavior
and establishes no speedup. Its reusable contribution is an authenticated
C-to-object recipe, independent ELF/ABI readback and a finite observed semantic
comparison against the exact native bytes.
