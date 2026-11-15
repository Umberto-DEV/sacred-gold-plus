# Native Box move caller: the complete move-to-PP lifecycle

The complete `BoxMonSetMoveInSlot(Box,310,0)` passes as one uninterrupted
native call: set move, get PP-Up, calculate maximum PP through the original
NARC/SDK/division code, then set current PP. Three original calls execute
51565 instructions in total: PP-Up3, PP-Up0 and observation OFF. Full16,
every read/store and all26 mapped pages match the frozen source prediction;
all32 evidence falsifiers are rejected. No model or runtime host write is used.

This closes the composition gap between the [move setter](native-box-move-setter-source-rom-1.3.2.md),
[PP-Up getter](native-box-ppup-source-rom-1.3.2.md),
[maximum-PP calculation](native-maxpp-memory-source-rom-1.3.2.md) and
[PP setter](native-box-pp-setter-source-rom-1.3.2.md).
The [owner](../../features/trainer-strategy/README.md) and
[source-to-ROM method](../test-bench.md#linking-source-to-an-exact-rom)
explain the wider pipeline. No gameplay, installed ROM, save, ABI, ID or default
changes. This is inherited native HGSS code, with an explicitly prepared
memory archive and an owned synthetic Box record.

## Inputs and source provenance

Provide your own current r4 images; ROMs, extracted retail data, raw traces,
private receipts and saves are not shipped with this repository.

| Image | Bytes | SHA-256 |
| --- | --- | --- |
| Current EN |152786844 | `2e30d6960bb059615fca7527700d86f8282e82ccbe99bf62e22f027453dc3d3d` |
| Current IT |159029760 | `13ebac02bdea3036511773587e6603ce6834e25f4b13d1a4662c3e954bfd5d4a` |

Both internal headers are IPKE/revision0; presentation language is distinct.
EN supplies the execution bytes. Optional current IT readback checks byte
identity, without claiming a separate Italian execution or localized C build.
The public manifests used by the lineage reader specify six additional exact
retail/base1.1/V4 images. The reader rejects a wrong whole-image identity.

The productive source remains
[ctrl-cheeb-del/pokeheartgold at cb614ad23449d5852b40321dc409c4143872b35c](https://github.com/ctrl-cheeb-del/pokeheartgold/tree/cb614ad23449d5852b40321dc409c4143872b35c).
`src/pokemon.c` SHA-256 is
`1d784ece4650b84e426a437ee20e4a926475fc20ef761e67440d0c0136548fa3`;
`BoxMonSetMoveInSlot` is at3132–3140, with signature
`void(BoxPokemon *, u16 move, u8 slot)`. Its source performs the four calls in
the order above. Attribute bases54/62/58 denote move, PP-Up and current PP.
`src/move.c` SHA-256 is
`e9adae2d57511a89ec5cc52ebb5741172a5d90123d02d33be66143ddf210e7b2`;
maximum PP is `basePP + basePP*20*min(PPUp,3)/100`, narrowed to a byte.
Source/header dependencies are authenticated by the verifier.

The newer
[PRET HGSS at6bf138d6035aa6b43d6f8f4132a12df70f86dcec](https://github.com/pret/pokeheartgold/tree/6bf138d6035aa6b43d6f8f4132a12df70f86dcec)
helps align names and recover constants. Brace-bounded C fragments match the
productive reference despite whole-file drift:

| Definition | UTF8 bytes | SHA-256 in both references |
| --- | --- | --- |
| `BoxMonSetMoveInSlot` |320 | `41c060b0536add51a98415666742a80ded4e677228ac955b48daa23636ad59ac` |
| `GetMoveMaxPP` |184 | `f40957552425aa458c822bdb13d88a11101277a95fb6d17c601a28a21727b195` |
| `SetBoxMonData` |558 | `300ded32f42c5d022b3c6a5e525c499af61120334d5a50cd132f4712c43fa385` |

The [definition comparator](../../features/trainer-strategy/tools/confronta_box_move_pret.py)
authenticates both clean pins and whole source files, then selects a unique
accepted global definition. Hashes cover the original UTF8 text from its first
return-type/qualifier character through the matching closing brace, excluding
the final newline, with no whitespace normalization. Comments, strings,
prototypes and earlier callsites do not select a definition. Its bounded
ordinary-C parser does not preprocess conditional or macro-generated code.

```sh
python3 source/features/trainer-strategy/tools/confronta_box_move_pret.py \
  --reference "$HGSS_REFERENCE" --heartgold-ref "$NEW_HGSS_REFERENCE" \
  --json "$OUT/source-definitions.json"
python3 -I -S -B -m unittest discover \
  -s source/features/trainer-strategy/test -p 'test_box_move_pret.py'
```

Definition-table correction,14 November2026: two earlier hashes selected
callsites through a following brace. The table now hashes actual definitions;
the comparator also checks the Mon wrapper, PP-Up reset variant and full
trainer constructor. Earlier sealed evidence remains preserved; installed-byte
and CPU evidence are unchanged.

This comparison accelerates locating the functions. It does not replace the
productive pin or establish register allocation, original object provenance or
C-to-ROM matching. Platinum's shared block mapping is a separate
[source comparison](native-mon-substructure-source-rom-1.3.2.md#aligning-with-the-newer-pret-sources),
without transferring its ABI or assuming Italian target support.

## Installed owner, calls and historical countercheck

Current ARM9 is plain: physical`0x4000`, RAM`0x02000000`, initialized size
`0x12B8E4`, entry`0x02000800`. These initialized windows have no overlay or
autoload dependency. For this owner only, physical offset is
`0x4000 + RAM - 0x02000000`.

The new caller is `[020714F0,02071532)`,66 bytes/29 Thumb starts, physical
start`0x754F0`, SHA-256
`241d632c25e2e2130111d57bd97d01fa3e0c3085fcd88383e7ea4fc0ef01c5e4`.
All66 bytes are code. The preceding thunk and literal are excluded.

| Actual BL | Target | Arguments for slot0 | Caller-owned Value |
| --- | --- | --- | --- |
| `020714FE` | `0206ED70` | Box,54,pointer | `TOP-12`, spilled move310 |
| `0207150A` | `0206E640` | Box,62,NULL | Getter returns3/0 |
| `02071516` | `0207332C` | move310,PP-Up | Native result24/15 |
| `02071526` | `0206ED70` | Box,58,pointer | `TOP-32`, native STRB result |

The [complete resource reader](../../features/trainer-strategy/tools/rileggi_box_move_caller.py)
combines924 Thumb code bytes/420 starts,30 SDK ARM bodies/1154 starts,
131 division ARM starts, pools, both188-entry attribute tables and the
original NARC inputs. Tables and pools stay data; the union is checked for
collisions. The child maps and individual hashes are in the prerequisite guides.

The [lineage reader](../../features/trainer-strategy/tools/rileggi_box_move_lineage.py)
locates a unique aligned66-byte signature in independently decoded ARM9,
follows the four BLs and the actual signed table rows54/58/62. Its bounded
16-component comparison covers1242 bytes:490 code and752 table data.
All16 components match current bytes in all eight exact EN/IT images.
Two compressed retail owners have null physical plaintext offsets; six plain
owners have16 physical checks each. These1242 bytes are a subset of the
execution resources, not a whole-ROM or complete historical execution claim.

The reader can report an unattributed layout with exit0: consumers must require
`all_images_attributed is True` and, for each entry in `images`,
`image['all_components_equal'] is True`, then inspect individual status/identity
evidence. An exit code alone does not establish attribution.
Exact signature matching deliberately refuses changed or ambiguous callers.

## Compilation, insertion and reverse attribution

There is no Plus installer at this native caller. Retail→base1.1→V4→current
comparison identifies the selected code as inherited. The current reader
also independently compares direct physical bytes with ndspy-decoded owner
bytes, allowing the reverse route ROM→caller→four callees→source candidate.

The original Metrowerks compiler, Thumb C objects and link map remain missing.
This case authenticates the30 retained SDK ELF objects and the524-byte signed
DIV object against recovered assembly, source dependencies, recipe receipts
and installed bytes. LLVM21 was used by the earlier qualified recipe; no new
compilation is needed for this case. This is reconstructed assembly-to-binary
correspondence, with finite source/byte/execution equivalence. It does not
prove a reconstructed original C build or a complete Italian ROM build.

To regenerate those comparison objects with your own inputs, use the
[SDK recipe procedure](native-fs-memory-narc-source-rom-1.3.2.md) and
[division recipe procedure](native-maxpp-memory-source-rom-1.3.2.md).
Preserve their manifests,30-path objects JSON and compiler identity. The
[complete ROM composition guide](../test-bench.md#from-the-source-tree-to-the-complete-rom)
explains the separate retail/base/Plus composition pipeline; this attribution
command creates no ROM and installs no game.

## Owned inputs, activation and lifetime

Both records are synthetic Box136, PID`0x4000`, flags0, species355, move310,
initialPP15, heldItem0; blocks are[A,C,B,D]. Only PP-Up changes in plaintext.
The checksum and ciphertext change as consequences; there is no compensating
held-item edit. The old PP-Up1 fixture with a compensated checksum is excluded.

| Input | Initial key | Calculated PP / final key | Initial Box SHA-256 | Expected final Box SHA-256 |
| --- | --- | --- | --- | --- |
| PP-Up3 | `02AB` |24 / `02B4` | `f88425686bc184b9f50a004384b16518c09f785cf190112595938e3220c72cf1` | `401b0fa15982184e6650413627b5d3540372253de0664aed7ed928d845bc9c6b` |
| PP-Up0 | `02A8` |15 / `02A8` | `3fd3c211d9881a296ca06df38cb96762a52c895c1b3a6d37d1d5d599cb7a0cee` | `3fd3c211d9881a296ca06df38cb96762a52c895c1b3a6d37d1d5d599cb7a0cee` |

Entry is Thumb`020714F0`, R0=Box`022F0000`, R1=310, R2=0, R3–R12 cookies,
SPtop=`023FD000`, LR=`022F0181`, CPSR=`6000003F`. The caller owns32 bytes;
all four callees enter with SP=`TOP-32`. There is no Value buffer at`022F0200`.
Native STRB`0207151C` writes the actual MaxPP byte to`TOP-32`; the final
setter reads that byte through its real pointer and stores it at Box+80.
Even idempotent move310, PP15 and checksum writes must appear in the transcript.

The NARC child FILE is`TOP-184`, parser local`TOP-208`, member buffer`TOP-72`.
`FS_ConvertPathToFileID` creates a second directory FILE at`TOP-312`; its
Init call is distinct from the client's. The stack peak is688 bytes, with
56 guard bytes below. At MaxPP entry, earlier Box calls have already written
part of the future FILE frame. `FS_InitFile` initializes selected fields,
without memset72. Resetting that frame would replace the behavior being tested.
The checker verifies the real residues before Init and chronological store
preimages throughout the whole API.

Memory archive resources retain the [qualified original NARC setup](native-fs-memory-narc-source-rom-1.3.2.md):
ARC92 at`021E3654`, quiescent lists/flags7, base`0127C820`, actual FAT/FNT/root,
path row11 at`0210F23C`, path at`0210F198`, seven parser/member windows36B.
Three declared input archive projections set the base, memory read callback
`020D7448` and procedure flags. Member310 supplies its original PP15 byte.
There is no PP1 projection, card response model, runtime host write or heap.
This is an explicit memory-archive activation, with synthetic API entry and
stack, not a naturally observed gameplay or CARD path.

Native execution matches the source prediction:17198/17169 original instructions,10993 Thumb
both,6205/6176 ARM,3806 reads,2245 stores and26 mapped pages. Across the three
Box callees it requires384 crypto payload stores,384 seed updates,320
checksum reads and12 actual block selectors. The final full16 is:

```text
R0=B3A0 / 2B9B, R1=0, R2=35EC47E5 / 4AA02329, R3=022F0181
R4..R11=entry cookies, R12=0, SP=023FD000, LR=0201FF59
CPSR=6000003F, PC=022F0180 (stopped before execution)
```

The function is void. R3 is the caller's final BX target and R12 retains the
native DIV effect; copying the standalone setter's residues would be wrong.

## Reproduction and success criteria

From the repository root, use Python3.14, ndspy4.2.0, Capstone distribution
5.0.9 (module5.0.7) and Unicorn2.1.4/CPU model17. The
[local caller source runner](../../features/trainer-strategy/test/arm_thumb_box_caller_oracle.py)
changes exactly three AST sites from the qualified loop: default/max32768,
and per-ARM-segment `min(8192,remaining)`. The
[CPU producer](../../features/trainer-strategy/test/box_move_caller_cpu.py)
changes only its two8192 cap literals to32768. Parents and ISA semantics stay
immutable; each native call uses one Uc and one emu_start, timeout1s.

The owned qualification covers long10001-step ON/OFF, tiny ARM interworking,
32767/32768-step boundaries and an infinite capped loop. Full16 loop states
are checked against a separate hard formula. The32768-step endpoint can be
correct without an observed return callback. Acceptance therefore requires
`source_steps+1 <=32768`, `stopped is True`, no fault, correct stop PC/full16,
all counters, whole maps and complete access/flow evidence. CPU17 is an
instruction-level host backend; ARM946 timing/cache/IRQ/CP15 and hardware
behavior remain outside this proof.

```sh
python3 -m unittest discover -s source/features/trainer-strategy/test \
  -p 'test_box_move_caller*.py'
python3 -m unittest discover -s source/features/trainer-strategy/test \
  -p 'test_box_move_lineage.py'
python3 source/features/trainer-strategy/tools/qualifica_box_move_caller.py \
  --json "$OUT/owned-limits.json"
python3 source/features/trainer-strategy/tools/rileggi_box_move_caller.py \
  --rom "$ROM_EN" --it-rom "$ROM_IT" --json "$OUT/resources.json"
python3 source/features/trainer-strategy/tools/congela_box_move_caller.py \
  --rom "$ROM_EN" --json "$OUT/input.json"

for MODE in prepare matrix verify; do
  if [ "$MODE" = verify ]; then
    set -- --raw-dir "$OUT/matrix"
  else
    set --
  fi
  python3 source/features/trainer-strategy/tools/attribuisci_box_move_caller.py \
    --mode "$MODE" --rom "$ROM_EN" --reference "$HGSS_REFERENCE" \
    --objects "$SDK_OBJECTS_JSON" --recipe-dir "$SDK_RECIPE_DIR" \
    --div-recipe "$DIV_RECIPE_DIR" --input-contract "$OUT/input.json" \
    --qualification "$OUT/owned-limits.json" --out-dir "$OUT/$MODE" "$@"
done
```

Create a fresh local`$OUT` first; each JSON and output directory must be new.
`$HGSS_REFERENCE` is a clean productive pin. The objects JSON and recipe
folders come from the linked recipe procedures. `prepare` authenticates fresh
ROM/resources, source/ELF/recipes, frozen input and current qualification;
`matrix` runs exactly three original API cells; `verify` rejudges those raw
files with no CPU/compiler. Saved predictions are recomputed and source
identities checked around each cell. The predictor's canonicality is relative
to supplied parts; the CLI's fresh reader/frozen/recipe binding supplies ROM
authority. Do not treat an isolated predictor call as a ROM authenticator.

For historical readback, run `rileggi_box_move_lineage.py --help` for its
explicit four-image arguments and run once per language. Preserve
statuses, hashes and null physical offsets. The report navigator
`python3 source/attribution_cases.py show native-box-move-caller-source-rom-1.3.2`
is documentation discovery only; it does not execute acceptance tests.

Success requires every source-predicted full16 state/read/store, the native
four-call order, causal PP-Up→DIV→stack byte→PP write, all26 final pages,
chronological forward/inverse replay, OFF neutrality and completed-report
hash bindings. Negative controls remove idempotent writes, bypass getter or
DIV, substitute a host Value, forge stack preimages/registers/keys/maps,
camouflage PP-Up0 as3 or fake a return gate/fault-free endpoint. Each must
fail its declared check, even when a forged endpoint alone looks plausible.

The first three-call matrix passed in3.228s (OS peak RSS146358272B).
CPU-free verification passed in2.480s (141639680B); a second verification
with CPU/assembler imports and compiler subprocesses denied passed separately.
The25 ROM-free unit contracts cover readers/lineage, strict limits, owned Box
fixtures and typed receipt binding. Six current owned qualification kernels
passed; an earlier six-run qualification is retained, with the rerun justified
by additional independent loop-state and complete-page checks. These are
host costs, without a DS timing or memory-saving claim.

## Coverage and remaining work

Documented provenance: pinned native C candidates, caller/field definitions
and inherited1242-byte lineage subset. Reconstructed binary match:30 SDK
assembly objects and signed DIV524, plus current physical/decoded readback.
Finite semantic prediction: two owned Box profiles, the complete caller,
all four calls and explicit memory-archive resources. Activation observed:
three original EN calls in this exact prepared API/memory-archive context,
with native getter→MaxPP→caller-stack→PP setter and OFF neutrality.
Unattributed: original Thumb C code generation, a full source ROM build,
other slots/moves/flags/PIDs/assert/fallback paths, natural gameplay caller/CARD state,
Italian execution, hardware timing and persistent save compatibility.

No optimization is justified by these results alone. Skipping an idempotent
setter would change crypto/checksum activity and possibly untested semantics;
its cost/risk requires separate whole-domain evidence and maintainer approval.
The reusable improvement is the qualified composition runner, independent
lineage/physical readback and a complete causal checker that later callers can
reuse after requalifying their own inputs, lifetimes and budgets.

The later [trainer first-move prefix](native-trainer-first-move-prefix-source-rom-1.3.2.md)
connects the actual record load and Mon veneer to this child, with new
contextual stack preimages and a stop before the loop branch.
