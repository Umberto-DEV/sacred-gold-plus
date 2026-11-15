# Native MonEncryptSegment on owned synthetic data

The original `MonEncryptSegment` encrypts 128 owned pattern bytes through its
original core and local LCG. Three isolated executions pass: seed `0xFC0`,
the same input with observation OFF, and counterfactual seed `0xFC1`. Every
run executes 1293 original Thumb instructions with no model, runtime host
write, heap, filesystem or global RNG access.

This is a prerequisite for understanding the encrypted Mon-data lifecycle.
It does not execute a Mon setter, checksum API or game caller. See the
[owner](../../features/trainer-strategy/README.md),
[source-to-ROM method](../test-bench.md#linking-source-to-an-exact-rom),
[complete ROM composition map](../test-bench.md#from-the-source-tree-to-the-complete-rom)
and [native MaxPP case](native-maxpp-memory-source-rom-1.3.2.md).

## Exact inputs, provenance and compilation boundary

Use an owned current r4 EN ROM: 152786844 bytes, SHA-256
`2e30d6960bb059615fca7527700d86f8282e82ccbe99bf62e22f027453dc3d3d`.
Optional current IT readback uses 159029760 bytes, SHA-256
`13ebac02bdea3036511773587e6603ce6834e25f4b13d1a4662c3e954bfd5d4a`.
Both headers identify IPKE/revision 0; presentation language is separate.
Execution here uses EN. Complete ROMs, extracted retail data, saves, BIOS and
private captures are not distributed or required as published fixtures.

The clean candidate source is [ctrl-cheeb-del/pokeheartgold](https://github.com/ctrl-cheeb-del/pokeheartgold/tree/cb614ad23449d5852b40321dc409c4143872b35c)
commit `cb614ad23449d5852b40321dc409c4143872b35c`:

| Source | Relevant definition | SHA-256 |
| --- | --- | --- |
| `src/pokemon.c` | MonEncryptSegment, lines 3933–3935 | `1d784ece4650b84e426a437ee20e4a926475fc20ef761e67440d0c0136548fa3` |
| `src/math_util.c` | core and local LCG, lines 143–157 | `ed76da9a0792494d7b22a029d903db402f5c2cec06212870e0337205be747612` |
| `include/math_util.h` | core signature | `566b25991e94325aea5d19143f559efd67606a32efb2abb48e5457f439960318` |

The wrapper delegates `(data, size, seed)` to the core. For each little-endian
halfword, the core advances the local seed using
`s = (s * 1103515245 + 24691) mod 2^32`, then XORs with `s >> 16`.
Size is in bytes; the loop uses size/2. Newer PRET references help locate and
compare these definitions; the verifier checks the exact pinned source and
clean checkout. See [using newer PRET references](../test-bench.md#using-newer-pret-references).

Original Metrowerks compiler and Thumb objects remain missing. This case
establishes documented C provenance, exact installed byte identity and targeted
semantic equivalence; it does **not** reconstruct C-to-Thumb compilation.
No compiler invocation, comparison ELF, installer or full-ROM build is added.
The complete-ROM composition procedure remains separate. An assembly copy of
installed words would not recover the missing C code-generation evidence.

## Locating code and data independently

Current ARM9 is plain, physical `0x4000`, RAM `0x02000000`, initialized length
`0x12B8E4`, entry `0x02000800`. These intervals are initialized ARM9, not
overlays, autoload, inherited Plus patches or padding. The
[reader](../../features/trainer-strategy/tools/rileggi_mon_cipher.py) streams
the complete ROM hash and compares direct physical reads to an independent
ndspy ARM9 decode. It retains only the bounded ARM9 owner and selected spans.

| Component | Logical interval, end excluded | Physical start | Bytes / starts | SHA-256 |
| --- | --- | --- | --- | --- |
| Encrypt wrapper | `0x020725D8..0x020725DC` | `0x765D8` | 4 / 2 | `8bdadb00ad3389fd9d10292c291d2b47f6d30d0531c80bbc0dbfbd0813d70c8c` |
| Wrapper pool, data | `0x020725DC..0x020725E0` | `0x765DC` | 4 / 0 | `addb0b46183eaf47ceb6aa0a83de80a6d516b55d32e16827649719e287b9243f` |
| Encrypt core | `0x0201FF44..0x0201FF6E` | `0x23F44` | 42 / 20 | `389a3db4659cbf730872a30ec4eeb8f15ae258996b4ce043a334c380ead71f4e` |
| Local LCG | `0x0201FF78..0x0201FF8E` | `0x23F78` | 22 / 11 | `9c5bf64dc199aee1c4481c4aec6d3bf09ef61fa500f29bd47075fcc4b89070f4` |
| LCG pool, data | `0x0201FF90..0x0201FF98` | `0x23F90` | 8 / 0 | `42aeea4e30dc4ac2f58e42de0ca7a7fefdd62bc97bd04a867406a09a06c16e1a` |

The wrapper pool holds odd Thumb pointer `0x0201FF45`. LCG literals are
`0x41C64E6D` and `0x6073`. Padding at `0x0201FF6E` and `0x0201FF8E`, the
neighboring decrypt wrapper and decrypt thunk are excluded. XOR symmetry
does not establish execution of those different entry points. Current EN/IT
readback agrees for all 80 bytes; Italian execution is not claimed. Historical
caller/lineage evidence is reused as provenance without repeating its campaign.
The public reader intentionally accepts the exact plain current images.

## Owned fixtures, callers, stack and ABI

The input is generated as `bytes(range(128))`, SHA-256
`471fb943aa23c511f6f72f8d1652d9c880cfa392ad80503120547703e56a2be5`.
It is opaque cipher data, not a structurally valid BoxMon or player record.
The host checksum of its 64 halfwords happens to be `0xFC0`; choosing this
seed does not execute CalcMonChecksum. Seed `0xFC1` is also a valid parameter
for this primitive, without implying a checksum-consistent Mon.

The [freezer](../../features/trainer-strategy/tools/congela_mon_cipher.py)
saves two complete input contracts before prediction or CPU execution. Each
has five sparse pages, 20480 bytes: two code/pool pages, buffer/return gate,
stack and a read-only global sentinel page. Entry is Thumb/System at wrapper
`0x020725D8`, R0=buffer `0x022F0400`, R1=128, R2=seed, R3–R12 declared cookies,
SP=`0x023FD000`, LR=`0x022F0181`, CPSR=`0x6000003F`.
Only R2 changes between the two entry contexts; initial memory is identical.
The synthetic caller above this entry is not executed.

The wrapper loads R3 with the core pointer and tail-calls through BX.
The core's two real PUSH instructions allocate 40 bytes: argument words at
top−16..top and saved registers at top−40..top−16. The local seed is the
argument copy at **top−8**. Native LCG instructions update that word 64 times;
no host initializes it and no global RNG state is consumed or changed.
A 56-byte stack guard and two 16-byte buffer guards remain unchanged.
Global address `0x021D15A8` has a synthetic sentinel and is never an allowed
read or write at any cipher site. Final-page equality alone is not the guard:
access admission rejects such an access even if its value were restored.

At return, R0 is the last ciphertext halfword (void API residue), R1=`0x7F7E`,
R2=seed63, R3=`0x022F0181`, R4–R12 restore entry cookies, SP=entry top,
LR=`0x0201FF59`, CPSR=`0x6000003F`. The single-register POP loads saved caller
LR into R3 before BX; LR itself retains the last native BL to the LCG.
The stack word at top−8 contains seed64, distinct from R2's seed63.
Full16 means R0–R14 plus CPSR, with PC checked separately.

## Prediction, instruction qualification and counterproofs

The [source bench](../../features/trainer-strategy/test/mon_cipher_bench.py)
checks the C formula independently of its finite instruction predictor. It
requires every one of the 64 seed updates and ciphertext stores, complete
full16 flow, chronological reads/stores, store preimages, forward and inverse
replay and all five final pages. Pools are native data reads, not invisible
host constants. For N=64, the manual forecast is `13+20*N = 1293` instructions,
`7+4*N = 263` reads, `10+2*N = 138` stores, 33 unique PCs and 40 bytes peak.

The [cipher frontend](../../features/trainer-strategy/test/arm_thumb_cipher_oracle.py)
adds only EOR low register, aligned word-immediate LDR/STR, BEQ and BLO to the
pinned MaxPP frontend. EOR updates N/Z and preserves C/V; word offsets scale
by four, with ownership checked before access; EQ/LO use Z/C respectively.
The primary [ARM Architecture Reference Manual, DDI0100I](https://documentation-service.arm.com/static/5f8dacc8f86e16515cdb865a)
defines the Thumb operations. Existing MUL/LSR/BL/BX/stack/halfword semantics
remain pinned. The arithmetic run retains its parent's exact bytecode and
argument defaults with three explicit effective namespace bindings.

Twenty-seven ROM-free tests cover arithmetic, owners/math/replay and completed
receipt/type checks. Eight owned synthetic CPU kernels qualify the additions
before the original cipher guest. They contain no original cipher/LCG code.
The native producer reuses the unchanged NARC CPU loop with an empty ARM corpus
and the new input/code namespace. Each run has one uninterrupted `emu_start`;
only admission sets, never arithmetic answers, reach that producer. Backend is
Unicorn 2.1.4 CPU17 (Cortex-A15), without an ARM946 timing/cache/interrupt claim.
Prediction cap is 4096; inherited guest cap is 8192 with a one-second timeout.

| Input | Ciphertext128 SHA-256 | Seed63 / seed64 | R0 residue |
| --- | --- | --- | --- |
| Seed FC0 | `304084f487616715a01a681ca2380bf2abe1913467b8ba72d03379eb3623dcdb` | `B3B58DA1 / 40FABC00` | `3F84` |
| Seed FC1 | `6d807a7bcfda32aec1d1064084a70cc0a33a72db07b8593433ac32ee1be0c0c5` | `71FBE606 / B6FB2501` | `C985` |

All three native cells match the first source forecast. OFF has no observation
ledger and retains identical enforcement, counters, final CPU and five pages.
FC1 keeps the same instruction/access route but changes all 128 buffer bytes
and the four local seed bytes. The global sentinel and other final bytes stay
unchanged. No input, result, producer or expected trace was retuned after CPU.

Thirteen raw-evidence forgeries are rejected: missing seed store, omitted XOR
with output intact, pre-advance/low16 key, wrong endian word, wrong loop count,
R2 seed64, R3 cookie, wrong LR, global RNG write, missing literal read, wrong
seed metadata and seed camouflage. These are CPU-free evidence mutations,
not extra guest runs. XOR roundtrip alone would fail to discriminate several
wrong symmetric transforms, so it is not used as the success criterion.

## Reproduction and dependencies

Use the [project requirements](../../requirements.txt): ndspy 4.2.0 and
Capstone 5 for independent readback; Unicorn 2.1.4 additionally for execution.
ROM-free tests run with only standard library. CPU-free verification uses
`-I` with site packages enabled for ndspy/Capstone, and imports no CPU backend
or assembler and invokes no compiler.

Set `SGP_CIPHER_ROM` to the owned exact EN ROM, `SGP_CIPHER_REFERENCE` to the
clean pinned source checkout and `SGP_CIPHER_WORK` to a new private directory
outside `source/`. No save, capture, extracted asset, SDK object or BIOS is
required. All output paths below must be new.

```sh
mkdir -p "$SGP_CIPHER_WORK"
.venv/bin/python3 -B source/features/trainer-strategy/tools/rileggi_mon_cipher.py \
  --rom "$SGP_CIPHER_ROM" --json "$SGP_CIPHER_WORK/resources.json"
.venv/bin/python3 -B source/features/trainer-strategy/tools/congela_mon_cipher.py \
  --rom "$SGP_CIPHER_ROM" --json "$SGP_CIPHER_WORK/input.json"
.venv/bin/python3 -B source/features/trainer-strategy/tools/qualifica_mon_cipher.py \
  --json "$SGP_CIPHER_WORK/instruction-qualification.json"
for phase in prepare matrix; do
  .venv/bin/python3 -B source/features/trainer-strategy/tools/attribuisci_mon_cipher.py \
    --mode "$phase" --rom "$SGP_CIPHER_ROM" --reference "$SGP_CIPHER_REFERENCE" \
    --input-contract "$SGP_CIPHER_WORK/input.json" --out-dir "$SGP_CIPHER_WORK/$phase"
done
.venv/bin/python3 -I -B source/features/trainer-strategy/tools/attribuisci_mon_cipher.py \
  --mode verify --rom "$SGP_CIPHER_ROM" --reference "$SGP_CIPHER_REFERENCE" \
  --input-contract "$SGP_CIPHER_WORK/input.json" --raw-dir "$SGP_CIPHER_WORK/matrix" \
  --out-dir "$SGP_CIPHER_WORK/verification"
for suite in test_arm_thumb_cipher_oracle.py test_mon_cipher.py test_mon_cipher_cli.py; do
  python3 -I -S -B -m unittest discover \
    -s source/features/trainer-strategy/test -p "$suite"
done
```

The reader optionally accepts `--it-rom`. Its EN/IT comparison receipt is
separate from the freezer's EN-only receipt binding; use the freezer output
unchanged in attribution phases. There is no `--snapshot` or `probe` mode.
The verifier binds exact raw file hashes, source identities and completed
matrix metadata, using typed JSON comparison. It checks source drift before
and after each cell and before its report. Preserve raw and receipts privately.

The measured budget was 180 seconds per host command, 1 GiB host RSS,
2 MiB per log, 16 MiB evidence and 1 GiB planned disk peak, retaining at least
10 GiB free afterward. The three-cell matrix took 0.436 s/59867136 B peak RSS;
CPU-free verification took 0.372 s/55361536 B, and an additional verification
forbidding CPU/assembler imports and compiler subprocesses took
0.356 s/54394880 B. These are host costs, not DS timings or game speedups.

## Established results and remaining gaps

| Conclusion | Evidence | Limit |
| --- | --- | --- |
| Documented provenance | Clean C/header source pin and hashes, wrapper/core/LCG recipe | Original MWC and Thumb objects absent |
| Binary identity | Current EN/IT physical/decoded 68 code + 12 data bytes, exact starts and pools | No reconstructed C-to-binary match or new full-ROM build |
| Targeted semantic equivalence | Two owned seed inputs, 64 native LCG/XOR steps, full ABI/access/replay/maps | Fixed aligned128-byte domain; no universal size/error/alias guarantee |
| Observed activation | Three original-code cells under isolated EN API entry, neutral OFF | No in-game caller, decrypt entry, setter/checksum lifecycle, IT or physical run |
| Still unattributed | Native checksum and complete encrypted Mon setter lifecycle | Require their own finite contracts and caller/resource evidence |

Independent reviews check the source, byte/ISA admission, frozen fixtures,
producer reuse, verifier and raw evidence. An early verifier review strengthened
completed-report metadata, typed equality and source-drift gates before any
native guest; the earlier CLI and preparation receipt remain archived locally.
No gameplay, ROM, save layout, IDs, ABI or defaults change. The reusable outputs
are the owned fixture recipe, finite frontend, instruction kernels and a
portable source/byte/execution verifier, available to any developer or coding
assistant through the same documented commands.

The [native Mon checksum](native-mon-checksum-source-rom-1.3.2.md) checks the next prerequisite on owned
storage: normal/odd sizes, 16-bit overflow and zero. Exact halfword access,
per-step truncation, final flags and full ABI are verified with the existing
frontend, without new ISA kernels or an original-compiler claim.
