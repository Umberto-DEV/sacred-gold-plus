# Native Mon checksum: odd size, zero and 16-bit overflow

The complete original `CalcMonChecksum` computes the sum of little-endian
halfwords modulo 65536. Five isolated executions pass: a 128-byte pattern,
the same storage with logical size 129, an overflow input, size zero and
observer OFF. No model, runtime host write or synthesized result supplies the
checksum. This is a sum, not CRC16.

This follows the [native segment cipher](native-mon-cipher-source-rom-1.3.2.md)
toward understanding encrypted Mon-data consumers. It does not execute a Mon
setter or compose checksum and cipher in one guest. See the
[owner](../../features/trainer-strategy/README.md),
[source-to-ROM method](../test-bench.md#linking-source-to-an-exact-rom) and
[complete ROM composition map](../test-bench.md#from-the-source-tree-to-the-complete-rom).

## Inputs, source and compilation boundary

Use an owned current r4 EN ROM: 152786844 bytes, SHA-256
`2e30d6960bb059615fca7527700d86f8282e82ccbe99bf62e22f027453dc3d3d`.
Optional current IT readback uses 159029760 bytes, SHA-256
`13ebac02bdea3036511773587e6603ce6834e25f4b13d1a4662c3e954bfd5d4a`.
Both current headers identify IPKE/revision 0; presentation language is
separate. Execution uses EN. No ROM, extracted retail data, player record,
save, BIOS or private capture is distributed as a fixture.

The source candidate is [ctrl-cheeb-del/pokeheartgold](https://github.com/ctrl-cheeb-del/pokeheartgold/tree/cb614ad23449d5852b40321dc409c4143872b35c)
commit `cb614ad23449d5852b40321dc409c4143872b35c`:

| Source | Definition | SHA-256 |
| --- | --- | --- |
| `src/pokemon.c` | CalcMonChecksum, lines 3941–3949 | `1d784ece4650b84e426a437ee20e4a926475fc20ef761e67440d0c0136548fa3` |
| `include/pokemon.h` | public signature, line 190 | `54a8f712af315e66776464ed2507e8970270524aa5b16ea8e610762b742ee1a1` |

The API returns u32, while its local accumulator is u16. Size is in bytes;
the loop reads `size/2` halfwords, truncating the accumulator after each
addition. Newer PRET references aid discovery and alignment, while verification
requires this exact clean source pin. See [using newer PRET references](../test-bench.md#using-newer-pret-references).

Original Metrowerks compiler and Thumb objects remain unavailable. This case
proves source provenance, installed byte identity and finite semantic
correspondence. It does not reconstruct original C-to-Thumb compilation.
No new compiler invocation, comparison ELF, installer or complete-ROM build
is needed for this question. Copying the installed words into assembly would
not resolve the missing C compilation evidence.

## Physical and logical identity

The initialized current ARM9 is plain: physical `0x4000`, RAM `0x02000000`,
length `0x12B8E4`, entry `0x02000800`. The checksum occupies
`[0x020725E8, 0x02072608)`, physical `[0x765E8, 0x76608)`, 32 bytes and
16 Thumb instruction starts, SHA-256
`6bcb00207d3f8b4ba907b5bff841ee17c7ea835258a05c47b61bd8f2a66f1fd2`.

The [reader](../../features/trainer-strategy/tools/rileggi_mon_checksum.py)
streams the full ROM hash, reads the bounded ARM9 owner and compares physical
bytes with an independent ndspy decode. Current EN and IT match. This is
initialized native HGSS code, with no pool, callee, veneer, overlay or autoload.
The neighboring decrypt wrapper and GetSubstruct at `0x02072608` are excluded.
The final `BX LR` is at `0x02072606`. Current byte agreement does not establish
Italian execution or a new eight-image historical lineage campaign.

## Owned inputs and activation contract

The [freezer](../../features/trainer-strategy/tools/congela_mon_checksum.py)
records four complete inputs before prediction and CPU execution. Storage is
always 129 owned bytes: either `bytes(range(128)) + b'\x5a'` or
`b'\xff'*128 + b'\x5a'`. It is opaque API input, not a valid BoxMon/save.
The pattern's first 128 bytes are the same owned prefix used by the cipher
case; this case now computes its checksum natively.

| Profile | Logical size / halfwords | Expected u32 checksum |
| --- | --- | --- |
| Pattern128 | 128 / 64 | `0x00000FC0` |
| Odd129, same initial storage | 129 / 64 | `0x00000FC0` |
| Overflow128, 64 halfwords FFFF | 128 / 64 | `0x0000FFC0` |
| Zero0, pattern storage | 0 / 0 | `0x00000000` |

Pattern128 and Odd129 have identical initial memory and differ only in entry
R1. The trailing `0x5A` is declared input storage that must not be read, rather
than a canary standing in for an undeclared argument byte. Overflow checks
that `64*0xFFFF = 0x003FFFC0` becomes unsigned `0xFFC0`, rather than a 32-bit
sum or signed −64. Zero uses a valid declared pointer and exercises the actual
loop skip, without introducing an unmapped-pointer failure domain.

Entry is Thumb/System at `0x020725E8`, R0=buffer `0x022F0400`, R1=logical
size, R2–R12 declared cookies, SP=`0x023FD000`, LR=`0x022F0181`,
CPSR=`0x6000003F`. A game caller above this entry is not executed. There are
three sparse pages, 12288 bytes: code, data/return gate and stack. Two 16-byte
D3 guards surround all 129 storage bytes. The function PUSHes only R3/R4 into
an 8-byte frame, with a separate 56-byte A5 guard. No heap, FS, RNG, callback,
IRQ or other function participates.

## ABI, access ownership and finite prediction

The [bench](../../features/trainer-strategy/test/mon_checksum_bench.py) compares
independent source mathematics to the pinned finite Thumb predictor. Every
iteration must expose its actual truncated R3 accumulator at `0x020725FE`.
Final masking alone would fail to distinguish deferred or omitted truncation.
The 129-byte storage and all buffer guards remain read-only.

Only these access owners are permitted:

| Instruction | Access |
| --- | --- |
| PUSH at `0x020725E8` | two 4-byte writes to top−8 and top−4 |
| LDRH at `0x020725F2` | ordered 2-byte reads buffer+2*i for i<size/2 |
| POP at `0x02072604` | two 4-byte reads from top−8 and top−4 |

Zero dynamically permits no buffer read. No source site may write the buffer,
a checksum field, a cipher pool or global RNG. Guards alone would not detect
an extra read; exact access ownership and chronology are required. The two
saved-word stores, their preimages, forward/inverse replay and every final
page must agree.

For N>0, final R0 is the zero-extended checksum, R1=`checksum<<16`, R2=N;
R3/R4 restore their cookies, R5–R12 remain unchanged, SP=entry top and
LR retains the caller's odd return sentinel. There is no BL. Final CPSR is
`0x3F` for the two nonzero checksums. The `ADDS` at `0x02072602` overwrites
the last equal-CMP flags; reporting `0x6000003F` would be incorrect.
Overflow R1=`0xFFC00000` is an unsigned32 register value. Zero returns
R0=R1=R2=0 and CPSR=`0x4000003F`, with the remaining ABI preserved.
Full16 means R0–R14 plus CPSR; PC is checked separately.

| Domain | Instructions / unique PC | Reads / stores | Peak stack / callbacks |
| --- | --- | --- | --- |
| 64 halfwords | 520 / 16 | 66 / 2 | 8 / 521 |
| Zero halfwords | 8 / 8 | 2 / 2 | 8 / 9 |

The manual formula is `8+8*N` instructions and `N+2` reads. All fetches are
original Thumb instructions. No new ISA family, arithmetic frontend or CPU
kernel is added: the exact pinned cipher frontend already qualifies every
operation. Its eight owned instruction kernels remain prior evidence; they
are not rerun or counted as new checksum executions. Thirteen new ROM-free
math/owner/replay/receipt tests cover this component.

Pattern128 and Odd129 have equal final full16, pages, reads and stores. Their
raw prefix differs: R1 starts at 128/129 and LSR at `0x020725EE` produces
carry 0/1. Full16 joins at `0x020725F6`, after the first LDRH and ADDS r2.
The verifier retains these real contexts and does not normalize carry or
remove steps. Neither profile reads the trailing byte.

The native producer reuses the unchanged NARC CPU-loop bytecode with new
input/code namespace and an empty ARM corpus. Each guest runs through one
uninterrupted `emu_start`; only access/fetch admission sets reach it. Source
prediction cap is 1024; inherited guest cap is 8192 with a one-second timeout.
Backend is Unicorn 2.1.4 CPU17 (Cortex-A15), without an ARM946 hardware,
timing/cache/interrupt claim.

## Reproduction with owned inputs

Use the [project dependencies](../../requirements.txt): ndspy 4.2.0 and
Capstone 5 for readback/verification, plus Unicorn 2.1.4 for execution.
ROM-free tests require only standard library. CPU-free verification needs
`-I` with site packages enabled for its readback dependencies; it imports no
CPU backend or assembler and invokes no compiler.

Set `SGP_CHECKSUM_ROM` to the owned exact EN ROM,
`SGP_CHECKSUM_REFERENCE` to the clean pinned source checkout and
`SGP_CHECKSUM_WORK` to a new private directory outside `source/`.
No save, BIOS, SDK object or capture is needed. Outputs must be new.

```sh
mkdir -p "$SGP_CHECKSUM_WORK"
.venv/bin/python3 -B source/features/trainer-strategy/tools/rileggi_mon_checksum.py \
  --rom "$SGP_CHECKSUM_ROM" --json "$SGP_CHECKSUM_WORK/resources.json"
.venv/bin/python3 -B source/features/trainer-strategy/tools/congela_mon_checksum.py \
  --rom "$SGP_CHECKSUM_ROM" --json "$SGP_CHECKSUM_WORK/input.json"
for phase in prepare matrix; do
  .venv/bin/python3 -B source/features/trainer-strategy/tools/attribuisci_mon_checksum.py \
    --mode "$phase" --rom "$SGP_CHECKSUM_ROM" --reference "$SGP_CHECKSUM_REFERENCE" \
    --input-contract "$SGP_CHECKSUM_WORK/input.json" --out-dir "$SGP_CHECKSUM_WORK/$phase"
done
.venv/bin/python3 -I -B source/features/trainer-strategy/tools/attribuisci_mon_checksum.py \
  --mode verify --rom "$SGP_CHECKSUM_ROM" --reference "$SGP_CHECKSUM_REFERENCE" \
  --input-contract "$SGP_CHECKSUM_WORK/input.json" --raw-dir "$SGP_CHECKSUM_WORK/matrix" \
  --out-dir "$SGP_CHECKSUM_WORK/verification"
for suite in test_mon_checksum.py test_mon_checksum_cli.py; do
  python3 -I -S -B -m unittest discover \
    -s source/features/trainer-strategy/test -p "$suite"
done
```

The reader also accepts `--it-rom`. The optional EN/IT comparison receipt is
separate from the freezer's EN-only resource binding. There is no snapshot or
probe option. The CLI records exact raw file hashes, clean source pin, frozen
inputs and tool bindings, requires a completed original matrix report with
typed metadata and checks source drift before/after cells and before reporting.
Keep raw and receipts private; they are saved before the verdict.

## Results, counterproofs and limits

All five first-matrix guests pass: four ON profiles and Pattern128 OFF, with
four distinct inputs. The first source forecasts match every count, ABI,
access and final page without retuning. OFF preserves enforcement, counters,
final CPU and maps while recording no observation ledger.

Sixteen CPU-free raw forgeries are rejected: byte/big-endian sum, overflow32,
deferred truncation with final result intact, missing/extra-tail halfword read,
odd-size camouflage, last-CMP flags, cipher LR, signed overflow R1, zero input
read, wrong saved preimage, payload write, skipped loop, bool size metadata
and wrong iteration counter. These are evidence mutations, not extra guests.
Independent source/raw and stdlib-only replay reviews check the attribution.

The recorded matrix took 0.379 s/59424768 B peak host RSS. CPU-free verification
took 0.334 s/48807936 B; an additional verification with CPU/assembler imports
and compiler subprocesses forbidden took 0.318 s/47841280 B. Limits were
180 seconds per command, 1 GiB host RSS, 2 MiB log, 16 MiB evidence and 1 GiB
planned disk peak with at least 10 GiB free afterward. Host costs do not
establish a DS speedup.

| Conclusion | Established coverage | Remaining limit |
| --- | --- | --- |
| Documented provenance | Exact C/header pin, u32 ABI and u16 local accumulator | Original MWC/Thumb objects missing |
| Binary identity | Current EN/IT physical/decoded32B and16starts | No reconstructed C binary or complete-ROM build |
| Targeted semantics | Normal/odd/overflow/zero, native per-step truncation, full ABI/access/replay/maps | No arbitrary size, unaligned pointer, alias, huge-size or error-path guarantee |
| Observed activation | Five isolated original-code EN cells, neutral OFF | No natural caller, Mon setter, checksum→cipher composition, IT or physical run |
| Still unattributed | Complete encrypted getter/setter lifecycle and substructure dispatch | Separate caller/resource contracts required |

The reusable outputs are owned fixtures and a source/byte/execution verifier
that uses the already-qualified frontend. No ROM, save layout, gameplay,
default, ABI or ID is changed by this attribution work.

The [native Mon substructure selector](native-mon-substructure-source-rom-1.3.2.md) covers all32PID rows and
four logical blocks, with exact table-byte reads, full ABI and an ignored-PID
counterfactual. Its eight-image reader finds the retail Italian table-pointer
difference. A source-only PRET adapter reuses four unchanged HGSS functions and
compares Platinum's mapping while recording its declared type differences.
