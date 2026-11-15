# Native Box PP-Up getter: encrypted input through restored output

The original `GetBoxMonData(Box, 62, NULL)` executes its complete valid-checksum
path on owned synthetic encrypted records. It decrypts 128 bytes, computes the
checksum, reads the header PID four times to select the data blocks, reads the
PP-Up byte, encrypts the payload again and returns. Three isolated calls pass:
PP-Up3, a checksum-preserving PP-Up1 counterfactual and observation OFF.
Each executes 3259 original Thumb instructions, with no service model or
runtime host write. The entire 136-byte record equals its own input on return.

This composes the qualified [cipher](native-mon-cipher-source-rom-1.3.2.md),
[checksum](native-mon-checksum-source-rom-1.3.2.md) and
[substructure selector](native-mon-substructure-source-rom-1.3.2.md).
The [owner](../../features/trainer-strategy/README.md),
[source-to-ROM method](../test-bench.md#linking-source-to-an-exact-rom) and
[complete composition map](../test-bench.md#from-the-source-tree-to-the-complete-rom)
provide the wider build context. This case does not reconstruct the original
C compiler or build a complete Italian ROM.

## Inputs, source and compilation boundary

Use your own current r4 ROMs. EN is required; IT is optional readback only.

| Input | Bytes | SHA-256 |
| --- | --- | --- |
| Current EN | 152786844 | `2e30d6960bb059615fca7527700d86f8282e82ccbe99bf62e22f027453dc3d3d` |
| Current IT | 159029760 | `13ebac02bdea3036511773587e6603ce6834e25f4b13d1a4662c3e954bfd5d4a` |

Both identify IPKE, revision0. Presentation language and game code are distinct.
The clean productive reference is
[ctrl-cheeb-del/pokeheartgold at cb614ad23449d5852b40321dc409c4143872b35c](https://github.com/ctrl-cheeb-del/pokeheartgold/tree/cb614ad23449d5852b40321dc409c4143872b35c).

| Required source file | SHA-256 |
| --- | --- |
| `src/pokemon.c` | `1d784ece4650b84e426a437ee20e4a926475fc20ef761e67440d0c0136548fa3` |
| `include/pokemon.h` | `54a8f712af315e66776464ed2507e8970270524aa5b16ea8e610762b742ee1a1` |
| `include/constants/pokemon.h` | `64d5d0cee8001830298ec7175c1863165ffccdf037685a51ea27037273187c74` |
| `include/pokemon_types_def.h` | `032888003b7a68733dedb83d55decc43cc4202b6ca66b284f62256aacb02e24d` |

`pokemon.c:463–478` defines the outer getter. The internal function starts at481;
its PP-Up cases are640–644. Constant `MON_DATA_MOVE1_PP_UPS` is62. BlockB+12
holds the first PP-Up count, while BlockB+8 holds current PP. The layout is an
eight-byte header followed by four physical 32-byte blocks.

This is inherited native HGSS code, distinct from compiled Plus additions.
Original Metrowerks compiler, Thumb objects, ELF and link map are unavailable.
The case therefore establishes documented C provenance, exact installed byte
identity and finite semantic correspondence through actual native execution.
It does not establish a reconstructed C-to-Thumb binary match. No compiler,
new installer or ROM composition step is invoked. The previous eight-image
readbacks cover their stated prerequisite windows; new getter windows are
verified here on current EN/IT only. Do not extend earlier lineage claims to
these windows without reading the other exact inputs.

The [PRET comparison method](native-mon-substructure-source-rom-1.3.2.md#aligning-with-the-newer-pret-sources)
helps reuse unchanged functions despite whole-file drift and distinguishes
Platinum's API differences. A newer upstream pin is a reference, not an
automatic replacement for the productive source or an Italian build target.

## Exact bytes and addresses

ARM9 is plain at physical `0x4000`, RAM `0x02000000`, initialized length
`0x12B8E4`, entry `0x02000800`. Every selected interval belongs to initialized
ARM9, with no overlay or autoload dependency. Physical offset for these exact
current inputs is `0x4000 + RAM - 0x02000000`.
The [reader](../../features/trainer-strategy/tools/rileggi_box_ppup.py) reuses
the independent physical/ndspy reader and authenticates the full input hashes.
It maps 324 code bytes at153 Thumb starts and528 data bytes.

| New component | RAM interval, end excluded | Physical start | Bytes / starts | SHA-256 |
| --- | --- | --- | --- | --- |
| Outer getter before successful check | `0206E640..0206E66C` | `72640` |44 /20 | `94d6f681ec0c88a47bdffe0182a02c4708484fbc15e4b53558211b72c37eb591` |
| Outer getter valid continuation | `0206E67C..0206E6A0` | `7267C` |36 /16 | `08b1c2815cc37d8524a1050a35f22d2434f980dfcf261b0309196379e3f0cef3` |
| Internal prefix | `0206E6A0..0206E6E8` | `726A0` |72 /32 | `309f123580189aa70099164b6fa2c484f390b54000cc9451932872057ee049b4` |
| Internal dispatch | `0206E6EA..0206E6F6` | `726EA` |12 /6 | `24b7c5eec85fa2487665f7a48d8de8643c17493b1de9f2a5bd5f5b3b3e7b2510` |
| PP-Up leaf | `0206E97E..0206E98A` | `7297E` |12 /6 | `2a7b6501c97854be547aa8c93d2975061395b4369a51a053312229e6f6cdf33b` |
| Internal return | `0206EC36..0206EC3C` | `72C36` |6 /3 | `137230d072c7eca5a8d6a25855af75a84edc89b985876ee421b9667d53942621` |
| Decrypt public thunk | `020725E0..020725E4` | `765E0` |4 /2 | `8bdadb00ad3389fd9d10292c291d2b47f6d30d0531c80bbc0dbfbd0813d70c8c` |
| Decrypt alias thunk | `0201FF70..0201FF74` | `23F70` |4 /2 | same thunk hash |
| Public decrypt pool, data | `020725E4..020725E8` | `765E4` |4 /0 | `777b3f69c8b59a74a66765635e7c7cddbc3a889ac265fe240a287c024d0f7b1f` |
| Alias pool, data | `0201FF74..0201FF78` | `23F74` |4 /0 | `addb0b46183eaf47ceb6aa0a83de80a6d516b55d32e16827649719e287b9243f` |
| Attribute jump table, data | `0206E6F6..0206E86E` | `726F6` |376 /0 | `be62e943e6963975954d7195c2f02162c3d8d92a6ba6de69416c3c3d1e843f97` |

Retained code/pool identities are listed in the three prerequisite guides and
are authenticated again in the new context. Decrypt follows native tail calls
`020725E0 → 0201FF71 → 0201FF45`; both low bits select Thumb. The selector's
odd table address `020FF733` is data and must remain unaligned.

The188-halfword dispatch table is data. Row62 at`0206E772` contains offset
`0x0286`; high ADD at`0206E6F4` uses PC+4 to reach`0206E97E`. The checksum
failure/assert gap`0206E66C..0206E67C`, out-of-range branch`0206E6E8`, other
attribute leaves and alignment bytes after`0206EC3C` are excluded. The next
setter begins at`0206EC40` and is not part of this getter proof.

## Owned fixture and causal counterfactual

The [freezer](../../features/trainer-strategy/tools/congela_box_ppup.py)
constructs records from logical values, not a save or extracted player data.
PID`0x4000` selects row2: physical order[A,C,B,D]. BlockA contains species355;
BlockB contains move310, currentPP15 and PP-Up3. All other plaintext bytes are
zero. Checksum is`0x02AB`, flags0. The128-byte payload is XOR-encrypted with
the private LCG, starting from that checksum.

The counter changes PP-Up3→1 and heldItem0→2. The checksum and keystream stay
identical; only ciphertext bytes10 and84 differ, each XOR2. This tests the
field's causal effect without changing the encryption key. These are coherent
API fixtures, not a claim of complete Pokémon legality or SAVE compatibility.

| Fixture | Plaintext128 SHA-256 | Box136 SHA-256 |
| --- | --- | --- |
| PP-Up3 | `f9abefd565709fe412c4320b234e8d51068874382045c1738b741f8613844111` | `f88425686bc184b9f50a004384b16518c09f785cf190112595938e3220c72cf1` |
| PP-Up1 | `26a93f1a4038edfc056c7bbec234255c3a16934891bb9f28f5c693b56a30f2d8` | `bd5ede160c2f5a32955e35ccdd7f249e4f8398e03cad93325c80b14f9aa630e2` |

## ABI, callers and temporary ownership

Entry is Thumb`0206E640`, R0=Box`022F0000`, R1=62, R2=NULL,
R3–R12 fixed cookies, SP=`023FD000`, LR=`022F0181`, CPSR=`6000003F`.
The outer caller is a synthetic return gate; no project caller or natural
encounter is claimed. All inner calls and returns execute original instructions:
decrypt, checksum, internal getter, four selectors and encrypt.

The getter checks `boxDecrypted` twice but does not set it during operation.
Flags0 can therefore accompany temporarily decrypted bytes. The header remains
read-only. Both crypto phases restart their64 local seed updates from the
native checksum header; the host does not restore a seed or payload between
phases. At the field load`0206E986`, R0 points to BlockB and LDRB writes R4,
not R0. The field is Box+84. CurrentPP is a different address.

The complete source forecast and native run agree on3259 instructions,153
unique starts,642 reads,307 stores and64 stack bytes. Every full16 state,
chronological read/store, store preimage and mapped byte is compared. Both
128-byte plaintext/ciphertext transitions,128 seed writes and64 checksum reads
are required. Forward and inverse replay verify all seven mapped pages,
28672 bytes. A guard before the page-aligned Box requires the seventh page.

The final64-byte stack, from SPtop−64 upward, is:

```text
0, Box+8, 0201FF45, PPUp,
Box, 0, entryR7, 0206E69D,
Box+8, 128, 8D9D11EB, 0201FF45,
entryR4, entryR5, entryR6, entryLR
```

The private seed slot is SPtop−24, rather than the standalone cipher's−8.
Calls overwrite one another's dead frames in order. The attribute-normalization
store at`0206E982` writes62→0 at SPtop−44 and is later overwritten. Removing
that store from a forged ledger must fail even if final registers/pages match.

Final R0=3 or1, R1=0, R2=`85732C58`(seed63), R3=`0206E69D`,
R4–R12 restored cookies, SP restored, LR=`0201FF59`, CPSR=`0000003F`.
These volatile registers and flags describe this installed path; they are not
additional guarantees of the C prototype. Across the counter pair, final CPU
differs only at R0; final memory differs only at the two input ciphertext bytes
and the saved PP-Up low byte at SPtop−52. OFF preserves the entire normal
input, endpoint and execution/access counters while recording no ledgers.

## Reproduce with your own inputs

Dependencies are in [requirements](../../requirements.txt): ndspy4.2.0,
Capstone distribution5.0.9 and Unicorn2.1.4. Tested Python3.14.7; the pure
fixtures, receipt checks and arithmetic tests use only the standard library.
Unicorn CPU17 is Cortex-A15 instruction emulation, not DS timing, ARM946 cache,
CP15, IRQ or physical hardware qualification. No compiler is required here.

From the repository root, set absolute paths for your ROMs and the clean
productive source checkout. Use a fresh private output directory outside
`source/`, with at least10GiB free after a planned1GiB disk peak.

```sh
PY=.venv/bin/python3
TOOLS=source/features/trainer-strategy/tools
OUT="$(mktemp -d)"

"$PY" -B "$TOOLS/rileggi_box_ppup.py" --rom "$ROM" --it-rom "$IT_ROM" --json "$OUT/resources.json"
"$PY" -B "$TOOLS/congela_box_ppup.py" --rom "$ROM" --json "$OUT/frozen.json"
"$PY" -B "$TOOLS/qualifica_box_ppup.py" --json "$OUT/instructions.json"

"$PY" -B "$TOOLS/attribuisci_box_ppup.py" --mode prepare --rom "$ROM" \
  --reference "$HGSS_REFERENCE" --input-contract "$OUT/frozen.json" \
  --qualification "$OUT/instructions.json" --out-dir "$OUT/prepared"
"$PY" -B "$TOOLS/attribuisci_box_ppup.py" --mode matrix --rom "$ROM" \
  --reference "$HGSS_REFERENCE" --input-contract "$OUT/frozen.json" \
  --qualification "$OUT/instructions.json" --out-dir "$OUT/matrix"
"$PY" -B "$TOOLS/attribuisci_box_ppup.py" --mode verify --rom "$ROM" \
  --reference "$HGSS_REFERENCE" --input-contract "$OUT/frozen.json" \
  --qualification "$OUT/instructions.json" --raw-dir "$OUT/matrix" --out-dir "$OUT/verify"
```

Omit `--it-rom "$IT_ROM"` if that optional input is unavailable. Reader and
freezer never execute CPU code. `prepare` predicts without a CPU; `matrix`
alone executes the original getter; `verify` reads the completed matrix and
recomputes the source prediction without importing Unicorn. It requires the
original prepared bindings, raw hashes, full matrix report and eighteen exact
forgery rejections. Raw files are written before verdicts and never overwritten.
Retain them privately; do not copy ROM bytes or traces into the public tree.

The finite [frontend](../../features/trainer-strategy/test/arm_thumb_box_oracle.py)
retains its parent's effective globals, run bytecode/defaults and arithmetic,
adding SUBS immediate8, B signed11 and only high-ADD words4478/4487. The previous
frontend allowed two different operand words, so reuse did not imply admission.
A pure failing test exposed that gap before any original getter execution.
Seven owned kernels qualify the final frontend against hard full16/flow
expectations and actual CPU execution. The [owned receipt](../../features/trainer-strategy/test/box-instruction-qualification.json)
contains synthetic program results and source hashes only. Receipt validation
rebuilds exact expected registers/flow hashes without CPU execution; well-shaped
but false registers, digests, types or source pins fail.

Run the22 ROM-free tests:

```sh
"$PY" -B -m unittest discover -s source/features/trainer-strategy/test -p test_arm_thumb_box_oracle.py
"$PY" -B -m unittest discover -s source/features/trainer-strategy/test -p 'test_box_ppup*.py'
```

These suites are also in [the public runner](../../run_tests.py). Memory replay
and contextual admission are in the [bench](../../features/trainer-strategy/test/box_ppup_bench.py);
the [CLI](../../features/trainer-strategy/tools/attribuisci_box_ppup.py) keeps
source identity, input, qualification and completed evidence bound together.

## Counterproofs, result and remaining work

Eighteen pure raw forgeries test wrong return/currentPP, LR/flags, field-load
register, attribute normalization, block pointer, header PID read, wrong field
address, checksum reading ciphertext, missing transient attribute/payload
stores, wrong preimage, standalone seed slot, frame reset, camouflaged counter,
instruction count, boolean metadata and injected host writes. Each fails at
its specified cause. No guest run is needed to fabricate these negative proofs.

A professional attribution also checks the reverse direction from the ROM
function to its source/recipe, preserves revision differences and source drift,
and seeks disconfirming paths. Here independent source/raw and instruction/ABI
reviews cover addresses, full state, temporary ownership, counterfactuals and
public fixture provenance. Missing compiler materials remain recorded rather
than inferred from similar names or a passing endpoint.

| Conclusion | Established | Remaining limit |
| --- | --- | --- |
| Documented provenance | Four exact source/header pins and valid getter recipe | Original MWC, Thumb objects and link map absent |
| Binary correspondence | Current EN/IT324code+528data bytes, physical/ndspy readback, real dispatch/tail pointers | No reconstructed C binary; no new historical getter-window lineage |
| Targeted semantic equivalence | Complete attr62 lifecycle, checksum/key-preserving counter, full state/access/replay | Other attributes, PIDs, flags and corrupt-checksum/assert paths unqualified |
| Observed activation | Three isolated original EN calls,9777Thumb instructions, neutral OFF | No natural caller, Italian execution, save or physical run |
| Still unattributed | Complete higher-level move setter/caller with its resources | Needs its own bounded input and execution contract |

First native matrix passes in1.003s with87097344B peak host RSS; CPU-free
verification takes0.810s/81002496B. Qualification7kernels takes0.087s/48742400B.
Commands were bounded to180s,1GiB RSS,2MiB log and16MiB private evidence, with
at least10GiB free after the planned disk peak. Guest execution is capped at
8192 instructions/1s; source prediction at4096. Host costs do not establish a
DS speedup. No gameplay, ROM, save format, ABI, IDs or defaults change.

Reusable results are the contextual fixture, exact reader, frontend,
qualification cache and full-state verifier. Reuse them at a new caller with
its actual frame and seed lifetime; retain the narrower prerequisite tests.
Skipping redundant checks inside an already decrypted lifetime might merit
measurement, but requires independent state/ownership and error-path proof,
an explicit game-change contract and hardware timing. No optimization is
implemented or performance benefit claimed by this case.

The subsequent [complete encrypted Box PP setter](native-box-pp-setter-source-rom-1.3.2.md)
qualifies the write side, second checksum and new encryption key under a new
contract. It does not expand this getter case to the complete move caller.
