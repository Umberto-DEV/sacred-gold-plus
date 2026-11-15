# Original NARC reader through the native filesystem

The original `ReadWholeNarcMemberByIdPair` selects NARC index 11, member 310,
copies the exact 16 bytes from the owned ROM and closes its file. Seven isolated
runs pass with **6,262 original ROM instructions: 103 Thumb and 6,159 ARM**.
There is no test caller, service model or host write after CPU entry.

This closes the caller boundary left by the [memory Read case](native-fs-memory-read-source-rom-1.3.2.md).
It uses that case's explicitly projected memory archive, rather than the natural
CARD controller. It establishes neither natural game activation nor ARM946
hardware timing. See the [owner](../../features/trainer-strategy/README.md),
[attribution method](../test-bench.md#linking-source-to-an-exact-rom) and
[complete ROM build map](../test-bench.md#from-the-source-tree-to-the-complete-rom).

## Provenance and inputs

Use your own exact r4 inputs. No ROM, extracted archive, save, BIOS or private
capture is distributed with this case.

| Input | Bytes | SHA-256 |
| --- | ---: | --- |
| EN r4 | 152786844 | `2e30d6960bb059615fca7527700d86f8282e82ccbe99bf62e22f027453dc3d3d` |
| IT r4, optional readback | 159029760 | `13ebac02bdea3036511773587e6603ce6834e25f4b13d1a4662c3e954bfd5d4a` |

Both current images retain IPKE/revision 0. Their presentation languages differ;
the header alone does not identify that property. Current EN/IT code, selected
path data and the seven payload windows agree by fresh readback. Execution here
uses EN code, not a separately observed Italian caller.

The candidate C source is `src/filesystem.c` in clean
[pret/pokeheartgold](https://github.com/pret/pokeheartgold) commit
`cb614ad23449d5852b40321dc409c4143872b35c`, SHA-256
`ee526fc2835b2c2259dd393087fb1a5ca036dbf467bcfbd7735b1476819c869d`.
The newer research checkout at `6bf138d6035aa6b43d6f8f4132a12df70f86dcec`
contains the same file. Reuse it for names, control flow, archive numbering and
the build recipe; changing a reference checkout does not change the production
pin. The [PRET comparison](../test-bench.md#using-newer-pret-references) records the wider
metadata reuse and the limits of the USA-only build targets.

Original Metrowerks compiler and Thumb objects are unavailable. Consequently,
the C candidate is documented and its valid-input selection is checked against
the installed instructions; **C-to-Thumb binary reconstruction is still open**.
The thirty SDK bodies have separate recovered assembly/ELF comparison receipts.
Those verify exact bytes, rather than recover the original compiler's origin.

## Locating code and data

ARM9 starts at ROM `0x4000`, loads at `0x02000000` and has initialized length
`0x12B8E4` in these current images. These intervals are initialized ARM9 bytes,
not overlays or compressed payloads. The reader checks physical offsets against
an independent `ndspy.code.MainCodeFile` decode. It streams the whole ROM hash,
but loads only ARM9 for that decode.

| Component | Logical interval | Physical offset | Bytes |
| --- | --- | --- | ---: |
| Whole-member wrapper | `[0x02007508,0x0200751E)` | `0xB508` | 22 |
| Parser first part | `[0x0200732C,0x0200738E)` | `0xB32C` | 98 |
| Parser middle | `[0x02007392,0x020073F4)` | `0xB392` | 98 |
| Parser last part | `[0x020073F8,0x0200740C)` | `0xB3F8` | 20 |
| Wrapper literal | `0x02007520` | `0xB520` | 4 |
| Archive table row 11 | `0x0210F23C` | `0x11323C` | 4 |
| Selected pathname | `0x0210F198` | `0x113198` | 8 |

The [resource reader](../../features/trainer-strategy/tools/rileggi_fs_memory_narc.py)
pins each complete span by SHA-256 and emits the addresses, offsets and hashes.
Capstone must decode exactly 103 starts in 238 bytes. The two assert-call holes,
alignment instruction at `0x0200751E`, literal pool and allocating neighbor at
`0x0200740C` are excluded from instruction admission. The four-byte BLX starting
at `0x020073FE` includes `0x02007400`; its second half is not a separate start.

The pool selects the table at `0x0210F210`, whose row 11 selects `a/0/1/1`.
NARC index 11, filesystem file ID 140 and NARC member 310 are distinct IDs.
FAT 140 is `[0x01093800,0x0109645C)`. BTAF count 471 and the member entry derive
file-relative offset `0x224C`, length 16, independently of the guest parser.
The member SHA-256 is
`85ac8d2ffc1e263ba41dfed64ea9b07613bd3fe76e8a68ef13e93394179dc5c8`.

## Composition, activation conditions and resources

Reuse the [thirty-object map and compiler recipes](native-fs-memory-read-source-rom-1.3.2.md#methods-components-and-recovered-compilation).
No new SDK compilation is required when authenticated artifacts are retained.
For a fresh reproduction, build those comparison objects using the documented
compiler, layout checks and source pin. Supply their JSON name-to-path mapping
and the completed memory-Read recipe directory. Its separate project-driver
artifact is verified as part of its historical receipt but **is not mapped or
executed in this case**. There is no ROM installer in this bench.

The actual caller receives `R0=destination`, `R1=11`, `R2=310`. Its fourth
argument and callee-saved registers contain declared cookies. It passes offset
zero and size zero to the parser, meaning the complete selected member. This
nonallocating entry does not call a heap allocator. The parser ignores filesystem
failure results; the admitted input has a valid path, nonempty member and member
index below the count. Malformed archives and error branches remain outside
this success case.

The CPU begins in Thumb/System state. Stack top is `0x023FD000`; the parser
locals begin at top minus 136, and its real 72-byte FILE begins at top minus 112.
Native instructions initialize that FILE and all required locals. The maximum
combined stack depth is 616 bytes, with a separate 56-byte guard. No scratch
FILE is placed inside the cached FAT. The destination has two 16-byte guards.

The archive retains its cached FAT/FNT and receives the three declared input
projections from the parent: base `0x0127C820`, read callback `0x020D7448`, and
procedure flags with bits `0x600` cleared. The callback is original SDK code.
This hybrid input is reproducible from the owned ROM without a private capture.
Optional `--snapshot` supports the qualified historical EN MainRAM resource
fixture described by the parent; its availability does not establish a natural
caller context, DTCM mapping or CARD completion.

The original parser makes five SET seeks and seven reads:

| File-relative source | Bytes | Destination |
| --- | ---: | --- |
| `0xC` | 2 | parser local +20, initially zero word |
| `0x14` | 4 | local +20 |
| `0x18` | 2 | local +8, a halfword |
| `0xED8` | 4 | local +20 |
| `0x9CC` | 4 | local +16 |
| `0x9D0` | 4 | local +12 |
| `0x224C` | 16 | final destination |

Only these 36 owned source bytes are mapped in two sparse payload pages.
Adjacent metadata slices have no overlapping canaries; surrounding synthetic
bytes are declared and cannot be read as payload. Source windows are read-only.
The memory callback receives the old file position while the FILE position has
already advanced. Seven native position stores and callbacks check that order.

## Interworking and ABI checks

The [finite predictor](../../features/trainer-strategy/test/arm_thumb_narc_oracle.py)
reuses the unchanged ARM arithmetic oracle. It carries exact registers and pages
between ARM segments and interprets only five identified return words plus the
admitted Thumb instructions. This segmentation is confined to source prediction;
the actual CPU executes all instructions without phase stops or reinjection.

Thumb BLX at `0x020073FE` uses `(PC+4)&~3` and sets LR to `0x02007403`.
The fifteen outer SDK returns use the original BX/POP instructions, including
conditional Open return and loaded PC values. `FS_InitFile` really clobbers R2
to zero before Open; an earlier service model's preservation policy is not used.

Load-PC interworking assumes CP15 control bit 15 clear, enabling TBIT loading.
This is a declared execution domain, not an observed hardware CP15 state. The
[ARM946E-S manual, DDI0155A §2.3.5](https://documentation-service.arm.com/static/5f032835cafe527e86f5b8ad)
describes that control; Arm's [branch and call guide](https://developer.arm.com/community/arm-community-blogs/b/architectures-and-processors-blog/posts/branch-and-call-sequences-explained)
explains the target-bit rule and load-PC interworking since ARMv5T.
Eleven owned synthetic kernels qualify the full context, reads, stores and pages,
including BLX at a halfword-only alignment and a false NE return with no stack
access. Unicorn 2.1.4 CPU model 17 is the Cortex-A15 backend, not ARM946 timing,
cache, interrupt, banked-stack or controller validation.

The C entry returns `void`. Its final R0=1 is the residual binary Close result,
not a newly defined Boolean API. Final R1=0, R2=`0x6000001F`, R3 and R4–R11
restore the entry cookies, IP=destination+16, SP=top, LR=`0x020D76A4`,
CPSR=`0x2000003F`. In observed runs, every executed PC is compared with all
sixteen context values. OFF runs compare counters and complete final state.

## Reproduction with owned inputs

Run from the repository root using the environment prepared under
[source requirements](../../requirements.txt). Prediction/readback/raw verification
need ndspy 4.2.0 and Capstone 5; CPU execution additionally needs Unicorn 2.1.4.
Verification does not import Unicorn or invoke a compiler. Keep site packages
enabled: `-I -S` intentionally hides the two required readback dependencies;
use `-I` for isolated verification. The ROM-free unit tests support `-I -S`.

Set `SGP_NARC_ROM` to the exact owned EN image, `SGP_NARC_OBJECTS` to the thirty
SDK object mapping, `SGP_NARC_RECIPE` to its memory-Read recipe directory,
`SGP_NARC_REFERENCE` to the clean pinned reference and `SGP_NARC_WORK` to a
fresh private evidence directory outside `source/`. Each output below must be new.

```sh
mkdir -p "$SGP_NARC_WORK"
.venv/bin/python3 -B source/features/trainer-strategy/tools/rileggi_fs_memory_narc.py \
  --rom "$SGP_NARC_ROM" --json "$SGP_NARC_WORK/resources.json"
.venv/bin/python3 -B source/features/trainer-strategy/tools/qualifica_interworking_narc.py \
  --json "$SGP_NARC_WORK/interworking.json"
.venv/bin/python3 -B source/features/trainer-strategy/tools/congela_fs_memory_narc.py \
  --rom "$SGP_NARC_ROM" --json "$SGP_NARC_WORK/input.json"
for phase in prepare matrix; do
  .venv/bin/python3 -B source/features/trainer-strategy/tools/attribuisci_fs_memory_narc.py \
    --mode "$phase" --rom "$SGP_NARC_ROM" --objects "$SGP_NARC_OBJECTS" \
    --recipe-dir "$SGP_NARC_RECIPE" --reference "$SGP_NARC_REFERENCE" \
    --input-contract "$SGP_NARC_WORK/input.json" --out-dir "$SGP_NARC_WORK/$phase"
done
.venv/bin/python3 -I -B source/features/trainer-strategy/tools/attribuisci_fs_memory_narc.py \
  --mode verify --rom "$SGP_NARC_ROM" --objects "$SGP_NARC_OBJECTS" \
  --recipe-dir "$SGP_NARC_RECIPE" --reference "$SGP_NARC_REFERENCE" \
  --input-contract "$SGP_NARC_WORK/input.json" --raw-dir "$SGP_NARC_WORK/matrix" \
  --out-dir "$SGP_NARC_WORK/verification"
python3 -I -S -B -m unittest discover -s source/features/trainer-strategy/test \
  -p test_arm_thumb_narc_oracle.py
python3 -I -S -B -m unittest discover -s source/features/trainer-strategy/test \
  -p test_fs_memory_narc.py
```

The [CLI](../../features/trainer-strategy/tools/attribuisci_fs_memory_narc.py)
also offers `--mode probe`. Add `--it-rom` to the resource reader for Italian
readback. If using an authenticated optional snapshot, pass it to the reader,
freezer and each attribution phase consistently. All runs bind source hashes,
input contract, exact ELF text, recipe receipts and reference dependencies.
Save raw evidence before judging it; source drift invalidates the binding.

## Results, counterproofs and remaining gaps

Seven guest runs cover two resource modes, normal and precompleted destinations,
and two observer-OFF controls. Each has 889 unique PCs, 1,732 data reads,
1,299 stores, a 616-byte stack peak and 17 mapped pages. The full 69,632 bytes
are compared and replayed from chronological stores. Five runs record full
observations; two OFF runs retain enforcement, counters and identical final state.
The precomputed forecast passed on the first native guest without retuning.

Four final member stores have different preimages at chronological indices
1208–1211 when the destination already contains the answer. The final output
converges, while the write transcript identifies its real cause. Camouflaging
that input or deleting any of those stores is rejected: ten forgeries across
the two resource modes. Two separate raw verifications pass without CPU or
compiler. An additional verification explicitly forbids CPU/assembler imports
and compiler subprocesses. Independent reviews check the source, addresses, mixed ISA and raw
contexts. Twenty-five ROM-free unit tests cover decoding, ABI, admission,
ownership, neighbor bytes, chronology and CLI contracts.

Proven: documented C candidate, exact installed caller/data identity, retained
SDK binary comparisons, and the full valid-input native path under the declared
memory-archive conditions. Open: original C compiler reconstruction, natural
caller activation, CARD async delivery, physical ARM946 behavior and Italian
execution. No full-ROM-from-C build, gameplay fix, speedup, memory saving or
save compatibility expansion follows from this case.

The copied member contains the base-PP field, but this case does not execute its
PP getter or setter. Extending through an actual consumer is a separate bounded
question. The parser's ignored I/O results and assert-only malformed-input paths
are potential hardening work: cost includes defining compatible error behavior,
risk includes caller/ABI changes, and verification would require error fixtures
plus unchanged valid-path behavior. No such game change is made here.

For other developers and coding tools, discover this case through
`python3 -I -S source/attribution_cases.py show native-fs-memory-narc-source-rom-1.3.2 --json`.
That catalog supplies public navigation, not an execution verdict. The commands,
source, tests, dependency versions and declared gaps above are sufficient to
reproduce the case with private inputs; assistant plans and handoffs are not
public prerequisites.

## PP consumer follow-up

The [complete native PP getter](native-pp-memory-getter-source-rom-1.3.2.md)
subsequently joins this chain to its original stack buffer, dispatch and byte
consumer. Its separate source-memory PP counterfactual changes the scalar
returned by the complete API. This NARC-only report retains its historical
scope; natural CARD delivery and original C compilation remain open.
