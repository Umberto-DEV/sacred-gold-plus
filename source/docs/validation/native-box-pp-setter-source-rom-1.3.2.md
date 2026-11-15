# Native Box PP setter: field write, checksum and new encryption key

The original `SetBoxMonData(Box, 58, Value)` completes the encrypted-record
lifecycle on owned synthetic data. It decrypts, validates the old checksum,
selects the four blocks from the header PID, writes currentPP0, calculates a
new checksum, stores it in the header and encrypts with that new key.
Three native calls pass: Value24, counterfactual Value23 and observation OFF.
Each executes3780 original Thumb instructions with no models or runtime host
writes. This is a complete setter path for the stated input domain.

The [encrypted PP-Up getter](native-box-ppup-source-rom-1.3.2.md) establishes
the read lifecycle and supplies the owned input recipe. The
[cipher](native-mon-cipher-source-rom-1.3.2.md),
[checksum](native-mon-checksum-source-rom-1.3.2.md) and
[block selector](native-mon-substructure-source-rom-1.3.2.md) remain narrower
prerequisites. See the [owner](../../features/trainer-strategy/README.md),
[source-to-ROM method](../test-bench.md#linking-source-to-an-exact-rom) and
[complete composition map](../test-bench.md#from-the-source-tree-to-the-complete-rom).
No gameplay, ROM, save format, ABI, IDs or defaults change.

## Inputs and source provenance

Use your own exact current r4 ROMs. EN executes; optional IT is readback only.

| Input | Bytes | SHA-256 |
| --- | --- | --- |
| Current EN |152786844 | `2e30d6960bb059615fca7527700d86f8282e82ccbe99bf62e22f027453dc3d3d` |
| Current IT |159029760 | `13ebac02bdea3036511773587e6603ce6834e25f4b13d1a4662c3e954bfd5d4a` |

Both current headers identify IPKE/revision0. Presentation language is separate.
The clean productive source is
[ctrl-cheeb-del/pokeheartgold at cb614ad23449d5852b40321dc409c4143872b35c](https://github.com/ctrl-cheeb-del/pokeheartgold/tree/cb614ad23449d5852b40321dc409c4143872b35c).

| Source file | SHA-256 |
| --- | --- |
| `src/pokemon.c` | `1d784ece4650b84e426a437ee20e4a926475fc20ef761e67440d0c0136548fa3` |
| `include/pokemon.h` | `54a8f712af315e66776464ed2507e8970270524aa5b16ea8e610762b742ee1a1` |
| `include/constants/pokemon.h` | `64d5d0cee8001830298ec7175c1863165ffccdf037685a51ea27037273187c74` |
| `include/pokemon_types_def.h` | `032888003b7a68733dedb83d55decc43cc4202b6ca66b284f62256aacb02e24d` |

The outer setter is `pokemon.c:953–970`; its internal function starts at972.
The four selector calls are986–989 and currentPP cases1106–1110. Attribute58
is `MON_DATA_MOVE1_PP`. Its byte lies at BlockB+8, distinct from PP-Up at+12.
The input pointer is `const void *`; this branch loads one byte from it.
The source return type is `void`, so a volatile R0 residue is not a PP result.

This is inherited native HGSS code. Original Metrowerks compiler, Thumb
objects, ELF and link map remain unavailable; no compiler or installer runs
here. The case establishes documented source provenance, installed byte
identity and finite semantic correspondence, without claiming reconstructed
C-to-Thumb binary equality or a complete source-built Italian ROM.
New PRET references help [align components despite file drift](native-mon-substructure-source-rom-1.3.2.md#aligning-with-the-newer-pret-sources);
they do not replace this productive pin or transfer Platinum ABI/layout.

## Installed windows and the static caller

ARM9 is plain at physical`0x4000`, RAM`0x02000000`, initialized length
`0x12B8E4`, entry`0x02000800`. Selected bytes belong to initialized ARM9,
without an overlay or autoload dependency. Physical offset for these exact
current inputs is`0x4000 + RAM - 0x02000000`.
The [reader](../../features/trainer-strategy/tools/rileggi_box_pp_setter.py)
streams exact ROM identity and compares physical bytes with independent ndspy
decoding. Execution uses328 code bytes/154 Thumb starts and528 data bytes;
a separate26-byte caller window is authenticated but never mapped or executed.

| New window | RAM interval, end excluded | Physical start | Bytes / starts | SHA-256 |
| --- | --- | --- | --- | --- |
| Outer setter before valid check | `0206ED70..0206ED9C` | `72D70` |44 /20 | `53acd545c111ee51a5f83580b2170664e73d4b313c28b1f5fc7a587a3cdfbdeb` |
| Outer valid continuation | `0206EDBA..0206EDE6` | `72DBA` |44 /19 | `87d29463274cb7305fa4013331e2b39644e1660de7c1ef4b4c7d64123a85d4e3` |
| Internal prefix | `0206EDE8..0206EE2E` | `72DE8` |70 /31 | `a0a536f377fdc4f126ffb6777eab009dd12a91952af247d7fef4e7cbc38d0741` |
| Internal dispatch | `0206EE30..0206EE3C` | `72E30` |12 /6 | `24b7c5eec85fa2487665f7a48d8de8643c17493b1de9f2a5bd5f5b3b3e7b2510` |
| PP leaf and internal return | `0206F0F4..0206F104` | `730F4` |16 /8 | `c7ea46cc0aa29cacf23d9c24f99a622124919eff60bd008a85896056b8f630ae` |
| Attribute table, data | `0206EE3C..0206EFB4` | `72E3C` |376 /0 | `fd895513256dc971df570f3f9f8bc069c9f41bb58da799241a4eadf5aa6aa2bf` |
| Static outer caller | `02071512..0207152C` | `75512` |26 /11 | `47456def46a6a888550aacbb7c4a496a10aa92d15b1f96f8c3e6ddd71c1c3c9d` |

Retained cipher/decrypt/checksum/selector code and pool hashes are specified
in the prerequisite guides and checked again. The188-halfword dispatch table
is data, not Thumb instructions. Row58 at`0206EEB0` contains`0x02B6`;
ADDpc at`0206EE3A` uses PC+4=`0206EE3E` to reach`0206F0F4`.
The invalid-checksum/assert gap`0206ED9C..0206EDBA`, default branch`0206EE2E`,
other attribute leaves and alignment bytes are excluded.

The source caller `BoxMonSetMoveInSlot` is at`pokemon.c:3132–3140`. Its PP
write calls this setter from BL`02071526`, following MaxPP at BL`02071516`
and a stack byte store of the result. The reader checks those two targets.
This is static caller attribution: Value24 is synthetic here, not an observed
MaxPP result bridged into the setter. The complete caller also writes the move
and remains a separate execution question. Earlier historical readbacks cover
their stated windows; these new windows are checked on current EN/IT only.

## Owned input and causal write

The [freezer](../../features/trainer-strategy/tools/congela_box_pp_setter.py)
reuses the preceding getter's owned PP-Up3 Box recipe: PID`0x4000`, flags0,
checksum`0x02AB`, physical blocks[A,C,B,D], species355, move310, currentPP15,
PP-Up3 and other plaintext bytes zero. Its Box136 SHA-256 is
`f88425686bc184b9f50a004384b16518c09f785cf190112595938e3220c72cf1`.
This is a coherent synthetic API fixture, not player data or save validation.

Separate Value storage contains24 or23. Initial CPU and Box are identical;
the sole initial mapped-byte difference is that Value byte. Each call starts
from its own frozen input, not from a preceding setter output. The native
LDRB at`0206F0F6` reads Value; STRB at`0206F0FE` writes Box+80, before the
internal ADDSP80 and return. The plaintext changes only at currentPP0.

| Value | New checksum | Seed63 | Seed64 | Final Box136 SHA-256 |
| --- | --- | --- | --- | --- |
|24 | `02B4` | `35EC47E5` | `B3A0C2F4` | `401b0fa15982184e6650413627b5d3540372253de0664aed7ed928d845bc9c6b` |
|23 | `02B3` | `77A5EF80` | `3DA059F3` | `8cc5a0fe1b2e992e59ae979d2886d1600d00e526d3fd10f33f1044a8665b321b` |

The first checksum validates the decrypted input. The second checksum reads
the modified plaintext; native STRH at`0206EDD6` writes the new header word.
LDRH at`0206EDDA` reloads it for encryption. A correct header paired with
old-key encryption fails the proof. All64 decrypt seed updates use old key
`02AB`; the64 encrypt updates restart from the new header key. No host seed
reset, checksum repair, field write or endpoint injection is allowed.

All128 crypto payload stores,128 seed updates,128 checksum reads, the PP
byte store and checksum-header store are required in order. The header PID
is read four times for selectors0–3. Flags remain0, even while the payload is
temporarily plaintext. PP-Up and all other decoded fields remain unchanged.

## ABI, stack and complete memory evidence

Entry is Thumb`0206ED70`, R0=Box`022F0000`, R1=58, R2=Value`022F0200`,
R3–R12 fixed cookies, SPtop=`023FD000`, LR=`022F0181`, CPSR=`6000003F`.
The outer caller is a synthetic return gate. At the PP store:

```text
R0=Box+72, R1=ValueByte, R2=3, R3=0206ED8D
R4=ValuePointer, R5=BlockB, R6=BlockD, R7=BlockA
SP=SPtop-120, LR=0206EE27, CPSR=0000003F
```

Each call executes3780 Thumb instructions/154 unique starts, with709 reads,
312 stores and136 bytes of peak stack. The internal PUSH24+SUB80 leaves a
larger frame than the getter; nested selectors add16 more bytes. The final
34 stack words, starting at SPtop−136, are:

```text
ValuePointer, BlockB, ValuePointer, 0206EE27,
Box, 0, BlockC,
thirteen words A5A5A5A5,
0201FF45, 58, Box, ValuePointer, entryR7, 0206EDE5,
Box+8, 128, newSeed64, 0201FF45,
entryR4, entryR5, entryR6, entryLR
```

Unused local bytes retain their actual fill, while crypto/checksum/selector
frames overwrite other locations chronologically. The private seed slot is
SPtop−24. Neither dead-frame masking nor resetting bytes between calls is
accepted. Eight mapped pages total32768 bytes; the new leaf needs page
`0206F000`, while the Box's preceding guard occupies`022EF000`.

Final R0=`B3A0` or`3DA0`, R1=0, R2=newSeed63, R3=`0206EDE5`,
R4–R12 restored cookies, SP restored, LR=`0201FF59`, CPSR=`6000003F`.
R0 is the void function's last cipher residue, not PP or a success boolean.
Volatile registers/flags are observed properties of this installed sequence,
not extra C calling-convention guarantees. Full16 states at every instruction,
read/store chronology, store preimages and every mapped byte match the source
forecast. Forward and inverse store replay recover all pages and input hashes.

Across the counter pair, final CPU differs at R0 and R2. Final mapped memory
differs in132 bytes: one checksum byte,127 ciphertext bytes, the separate
Value byte and three bytes of the final seed slot. All128 crypto payload halfword stores (64decrypt+64encrypt) still occur;
changed-value count is distinct from executed-write coverage. OFF has
identical full input, endpoint and enforcement counters, with empty ledgers.

## Reproduce with your own copies

Use [requirements](../../requirements.txt): ndspy4.2.0, Capstone distribution
5.0.9 and Unicorn2.1.4. Tested Python3.14.7. The pure tests use the standard
library. CPU17 is Cortex-A15 instruction emulation; it does not qualify DS
timing, ARM946 silicon, cache, CP15 or IRQ behavior. No compiler is required.

Set absolute paths for `ROM`, optional `IT_ROM` and the clean productive
`HGSS_REFERENCE`. Use a fresh private output directory outside`source/`.
Keep at least10GiB free after a planned1GiB disk peak.

```sh
PY=.venv/bin/python3
TOOLS=source/features/trainer-strategy/tools
OUT="$(mktemp -d)"

"$PY" -B "$TOOLS/rileggi_box_pp_setter.py" --rom "$ROM" --it-rom "$IT_ROM" --json "$OUT/resources.json"
"$PY" -B "$TOOLS/congela_box_pp_setter.py" --rom "$ROM" --json "$OUT/frozen.json"
"$PY" -B "$TOOLS/qualifica_box_pp_setter.py" --json "$OUT/instructions.json"

"$PY" -B "$TOOLS/attribuisci_box_pp_setter.py" --mode prepare --rom "$ROM" \
  --reference "$HGSS_REFERENCE" --input-contract "$OUT/frozen.json" \
  --qualification "$OUT/instructions.json" --out-dir "$OUT/prepared"
"$PY" -B "$TOOLS/attribuisci_box_pp_setter.py" --mode matrix --rom "$ROM" \
  --reference "$HGSS_REFERENCE" --input-contract "$OUT/frozen.json" \
  --qualification "$OUT/instructions.json" --out-dir "$OUT/matrix"
"$PY" -B "$TOOLS/attribuisci_box_pp_setter.py" --mode verify --rom "$ROM" \
  --reference "$HGSS_REFERENCE" --input-contract "$OUT/frozen.json" \
  --qualification "$OUT/instructions.json" --raw-dir "$OUT/matrix" --out-dir "$OUT/verify"
```

Omit the optional IT flag if unavailable. Reader/freezer execute no CPU code.
`prepare` predicts; `matrix` alone executes the original setter. `verify`
recomputes the prediction and validates the original completed report, prepared
bindings, input and raw hashes without importing Unicorn. A guarded replay also
passes with CPU/assembler imports and compiler/non-Git subprocesses forbidden.
Raw files are written before verdicts and never overwritten. Keep raw traces,
ROMs and extracted data private; the public fixture contains owned programs only.

The [frontend](../../features/trainer-strategy/test/arm_thumb_box_setter_oracle.py)
adds only STRB immediate5 over the pinned preceding frontend. Address is
base+imm5 without scaling, wrapped to32 bits; value is low8; registers/flags
remain unchanged. Source and base register may alias. Four owned kernels test
the actual word7201, max offset31, aliasing, truncation and wrap, with exact
byte preimages, neighboring bytes, full16/flow and all pages checked against
hard expectations and actual CPU execution before any original setter run.

The [owned receipt](../../features/trainer-strategy/test/box-setter-instruction-qualification.json)
contains source hashes, synthetic registers and flow/store/page digests. Its
validator reconstructs exact expected content without invoking the oracle or
CPU; false values, digests, JSON types or source pins fail. The previous getter
and standalone crypto/checksum profiles remain unchanged.

Run the22 ROM-free tests, also included in [the public runner](../../run_tests.py):

```sh
"$PY" -B -m unittest discover -s source/features/trainer-strategy/test -p test_arm_thumb_box_setter_oracle.py
"$PY" -B -m unittest discover -s source/features/trainer-strategy/test -p 'test_box_pp_setter*.py'
```

Contextual access ownership, two-key source math and full replay live in the
[bench](../../features/trainer-strategy/test/box_pp_setter_bench.py). The
[CLI](../../features/trainer-strategy/tools/attribuisci_box_pp_setter.py) binds
the source graph before/after every cell and requires a completed exact matrix.

## Counterproofs and scope of the conclusion

Twenty-five pure raw forgeries test PP-as-return, old seed, wrong LR/flags,
old-key reload, missing second-checksum/Value/PID reads, wrong Value address,
PP-Up target, word-width/untruncated/missing PP stores, old/missing checksum
header store, bad preimage, old encrypt key, shadow field value, wrong BlockB,
missing transient normalization, bad stack preimage, camouflaged counter,
instruction count, boolean metadata and an injected host write. Each fails at
the specified cause. Endpoint-correct but missing-write evidence is rejected.

A professional attribution checks both source→recipe→bytes→execution and
ROM→function→source, records language/revision drift and seeks disconfirming
branches. Independent source/raw and instruction/ABI reviews examine the
actual records, addresses, temporary lifetimes and counterproofs. Similar
symbols or a correct final field alone do not establish this lifecycle.

| Conclusion | Established coverage | Remaining limit |
| --- | --- | --- |
| Documented provenance | Four source/header pins, complete valid attr58 recipe, static caller | Original MWC/Thumb objects and link map absent |
| Binary correspondence | Current EN/IT856execution bytes plus26static caller bytes, physical/ndspy mapping | No rebuilt C object or newly expanded historical-window lineage |
| Targeted semantic equivalence | Two-checksum/two-key lifecycle, exact PP/header writes, full state/maps/replay | Other attributes, PIDs, flags and assertion paths unqualified |
| Observed activation | Three isolated original EN calls,11340Thumb instructions, Value counter/OFF | No MaxPP→Value link, complete move caller, Italian or physical run |
| Still unattributed | Move-field setter and complete higher move caller | Requires a separate bounded contract and actual composition |

First native matrix passes in1.457s/104923136B peak host RSS. CPU-free
verification takes1.241s/104546304B; guarded replay1.258s/101335040B. Four
owned kernels take0.082s/39829504B. Limits are180s,1GiB RSS,2MiB log and16MiB
private case evidence; guest cap8192 instructions/1s, predictor4096. Host costs
do not establish a game speedup. All38 runtime source bindings are unchanged
after execution. No original API rerun or expected-result adjustment was needed.

Reuse the exact reader, owned fixture, STRB qualification/cache and contextual
two-key verifier at the next bounded caller. A future optimization of repeated
decrypt/checksum/encrypt calls would require proof of shared ownership, error
handling and save invariants, plus measured hardware benefit and a separate
game-change decision. No such optimization is implemented here.

The [complete move halfword setter](native-box-move-setter-source-rom-1.3.2.md)
subsequently checks attr54 under its own two-byte fixture and post-ADDSP writer
context. Its idempotent-store evidence does not enlarge this PP-byte case.
