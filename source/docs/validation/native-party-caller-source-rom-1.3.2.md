# Native party NARC reader inside the trainer caller

This case continues the [header caller](native-header-caller-source-rom-1.3.2.md):
trainer31's initial party read now runs the installed native parser in the same
CPU as preparation, rematch wrapper, six Pokémon, six species names and return.
The [verifier](../../features/trainer-strategy/tools/attribuisci_lettore_prefisso.py)
uses the [qualified parser](native-narc-reader-source-rom-1.3.2.md). It changes no
ROM, gameplay source, save layout, ABI or identifier. Verification status and
coverage below refer only to the named exact inputs and initialized path.

## Cosa farebbe un professionista di alto livello che non sto chiedendo

Trace both directions: follow `rematch_hook` to its original reader and recover
that reader's actual path/table/member from raw ROM. Distinguish project code
reconstructed from retained objects from inherited native code whose original
compiler is unavailable. Test transport and closure independently of payload:
a zeroed destination can conceal an incomplete read of a final zero byte.
Require an independent address/ABI/counter review and preserve resource/model
boundaries when composing previously qualified standalone functions.

## Il materiale più grezzo da cui partire

Supply your own lawfully obtained exact inputs; no ROM, extracted archive,
Pokémon packet, RAM dump or private fixture is distributed here. Required ROMs:

| Language | Bytes | SHA-256 |
| --- | ---: | --- |
| EN r4 | 152786844 | `2e30d6960bb059615fca7527700d86f8282e82ccbe99bf62e22f027453dc3d3d` |
| IT r4 | 159029760 | `13ebac02bdea3036511773587e6603ce6834e25f4b13d1a4662c3e954bfd5d4a` |

Whole-image identity takes precedence over the IT image's inherited internal
header. See the [rematch recipe](rematch-source-rom-1.3.2.md) and
[strategy recipe](trainer-strategy-source-rom-1.3.2.md) for compilation and
insertion requirements. Supply retained/reproduced `rematch-variants.o`,
`rematch-stub.o` and `teams.o` from those recipes. Their SHA-256 values are,
respectively, `cfc4dce49574df18f3064fb66c2f8d75b66f5e6ed63e26d36e97893e2168817a`,
`43848467a67b11f1fec275a63e89f861c8641f325c86af38df03320a10d7c68a`, and
`e2429f61c7ee16071d303f7ca55cbb1553508720c6fe97b77aead9ce56e499e1`.
The executable verifier checks object/installed-byte agreement.

The raw FAT/FNT owner is `a/0/5/6`, file185, physical `0x01F96C00`,31286 bytes,
SHA-256 `964a3efd40d83ecb196035f257264ba0e76a55818ed0d13aadde15b890451da9`.
Member31 is108 bytes at archive offset7552/physical `0x01F98980`, SHA-256
`2096c9d5a3943dca51dec0ea9b0b006387f2fb5b0d6778a49f58c2803806395c`.
An independent raw FAT/FNT/NARC reader agrees with ndspy. The parser reads the
whole archive through FS cursor operations, derives its own member offset and
length, and never receives a host-selected member at the payload-copy boundary.

## I metodi e gli strumenti da usare

The [project hook](../../features/rematch-variants/native.c) is
`rematch_hook` at logical `0x0226B4A1` in overlay126. Its `LDR r3` at `0x0226B4A2`
loads literal `0x020735E9` from `0x0226B4BC`; **BLX r3 is at `0x0226B4A4`**,
so LR is `0x0226B4A7`. The native tail at `0x020735E8` rearranges arguments and
branches to Thumb `0x02007508`. Its path-table literal is at `0x02007520`;
row56 resolves to the raw `a/0/5/6` path. The parser qualification checks103
instruction starts/238 bytes, widths, ISA, literals and paths. Runtime rejects
live byte drift. Current ARM9 offsets come from an independent header/readback;
overlay addresses are related to the FAT extent through the actual overlay table,
not treated as directly mapped ARM9 offsets. In both exact r4 images the four
parser spans map `0x02007508→0xB508` (22B), `0x0200732C→0xB32C` (98B),
`0x02007392→0xB392` (98B), `0x020073F8→0xB3F8` (20B); the table literal
maps `0x02007520→0xB520`. These are resident, uncompressed ARM9 bytes.
Historical compression and regional
path-table differences remain covered by the standalone reader's provenance guide.

At this call, `R0=0x02200000`, `R1=56`, `R2=31`, `R3=0x02007509`.
Saved R4..R7 are setup, packed trainer name, Mon buffer `0x02200080`, and4;
R8..R11 retain the initialized caller cookies. `R12=0x02200160` follows the last
qualified native ClearFast: `MonBuffer + 32*(236>>5)`. It is a concrete volatile
residue for this path/model policy, not an AAPCS promise. SP is caller-inner SP
minus200: constructor152 + resident stub16 + module hook32. The reader adds136,
reaching432 bytes below outer SP; the complete caller still has a608-byte bound.

The observer borrows the existing Unicorn CPU. It does not invoke standalone
setup, start a second CPU, reset registers or initialize the reader frame.
It captures the actual136-byte preimage and56-byte guard left by the earlier
loader, then reconstructs17 ordered native stack writes plus six metadata reads
over that preimage. Snapshot occurs at actual return `0x0226B4A6`, before module
or constructor reuse. The module saves the reader's residual R0, forwards it
through unload and returns to constructor seam `0x0207363E`; R0 is not replaced
with the former synthetic callback result.

The108-byte destination is already zero because the retained allocation model
zeroes it. This is recorded and bound to its actual allocation event; it is not
a claim about native heap initialization. No artificial high-level read56 event
or constructor prefix-model entry is inserted. The other187 Normal/189 Plus
ReadWhole calls retain their original backend, once each, with actual argument,
resource, event index, saved-register and return checks. Header55 remains a
separate native owner. Five opaque FS services remain models: Init, Open, Seek,
Read and Close. No reference FSFile layout is fabricated in the guest stack.

[Bounded adapter recipes](../../features/trainer-strategy/test/prefix_narc_bench.py)
authenticate complete parent source hashes and exact edit counts before compiling
one derived observer/oracle function. The20 constructor result statements remain
unchanged; evidence removes only the obsolete prefix callback/event assumptions.
The global hook equation is constructor + messages + six names + native header +
native party reader +157. Removing one old callback fetch and adding118 native
reader/FS fetches predicts +117 relative to the header-only composition.

## Reproduce with your own inputs

Use Python3.14, ndspy4.2.0, Unicorn2.1.4 and the Capstone5 API qualified in the
parent guides. The recorded environment had Capstone distribution5.0.9,
module5.0.7/core5.0.1280; do not infer equivalence from a package label alone.
The bench requires qualified CPU model17 and the parent's synthetic instruction
calibration. Do not install an emulator or build another ROM for this verifier.

```sh
python source/features/trainer-strategy/tools/attribuisci_lettore_prefisso.py \
  --rom "$ROM" --language EN --objects "$REMATCH_OBJECTS" \
  --strategy-object "$STRATEGY_OBJECTS/teams.o" \
  --json "$PRIVATE_OUTPUT/prefix-caller-EN.json.gz"
python -m unittest discover -s source/features/trainer-strategy/test \
  -p test_prefix_narc_bench.py
SGP_PREFIX_CALLER_ROM_DIR="$ROMS" \
SGP_PREFIX_CALLER_REPORT_DIR="$PRIVATE_OUTPUT" \
SGP_REMATCH_OBJECT_DIR="$REMATCH_CASE" \
SGP_STRATEGY_OBJECT_DIR="$STRATEGY_CASE" \
python -m unittest discover -s source/features/trainer-strategy/test \
  -p test_prefix_caller_attribution.py
```

Repeat the verifier for IT and its corresponding objects. Replay expects
`r4-EN.nds`, `r4-IT.nds`, `public-build-{EN,IT}` under the rematch case, and
`build-{EN,IT}/teams.o` under the strategy case. Keep all outputs outside `source`.
A fresh destination is required. Bound each command to180 seconds,1GiB RSS and
2MiB log; allow16MiB retained evidence,1GiB transient disk and at least10GiB free
after that peak. The executable enforces guest3M hooks, stack608, bounded report
encoding and OS high-water RSS. An external limiter must enforce wall time/logs.

## Success, counterproofs and limits

The finite matrix is Plus0/1 × two initial seeds, a second stack poison, two
observer OFF pairs, one FS volatile-register control and two late counterproofs,
per language. Success requires exact six full packets, prepared Trainer52,
restored seed, complete native header/message/name evidence, actual parser ABI,
all15 FS calls, seven reads, requested/delivered sizes, cursor and closure.
The recorded20 executions passed. EN hook totals are1040109 Normal and1056336
Plus; IT adds34. All eight positive parties, prepared Trainer52 and final seeds
match the preceding header-only case, with exactly117 additional hooks each.
Eight portable tests and eight exact-input replay tests passed without skips.
The campaigns took87.770s EN/88.663s IT, with OS peak RSS564297728/577830912 bytes;
replay took9.186s/722665472 bytes, below the1GiB ceiling. Independent source/raw/
ABI/counter reviews and pure final replay found no unresolved blocker.
The pre-constructor checkpoint remains604 EN/638 IT.

Observer OFF omits native store logs. The original prefix audit also places
four8-byte allocation canaries only when ON. Compare actual before/after canary
bytes separately and project exactly those32 bytes from phase RAM comparisons;
retain all other stack/context/transport checks. The observer's own unload count
is1 ON/0 OFF, while native handback, overlay registry and FS/model dispatch agree.
Do not silently mask an entire heap or infer whole final RAM equality from the
existing scratch projection.

Skipping native Close leaves a live file and117 hooks despite identical payload.
Returning107 for the final108-byte read leaves an already-zero last byte and can
preserve all six Pokémon. The required transport ledger must reject this even
when payload and reader-phase RAM match the positive run. A normal native return
on a short read is not native error handling. Counter replay must preserve the
full execution evidence, not merely the rejection label. On both recorded
languages, each counter also has the same entire final4MiB main-RAM hash and
reader-phase RAM hash as its positive baseline. The skipped-close snapshot
still has a different live file ledger and actual forwarded R0; later scratch
reuse removes that difference from final RAM. This equality is finite evidence,
not a general claim about arbitrary calls or error conditions.

Provenance is documented for project hook/recipe and inherited native function.
Project object/readback correspondence is checked; rebuilding the original
native parser with its original compiler is not established. Native activation
is observed only in the initialized bench path, under explicit SDK models.
No natural encounter, card I/O, complete battle, save/restart, UI performance or
physical-device validation follows from this case. Native FS/heap internals and
remaining constructor reads are still unqualified links. No game optimization
or error-path repair is included; a production short-read policy would need its
own ABI/error-path and gameplay validation with the maintainer.


| Conclusion | Evidence and scope |
| --- | --- |
| Documented provenance | Project `rematch_hook`, installer, retained ELF and exact overlay readback; native function/reference/path-table identity distinguished from project code. |
| Reconstructed binary correspondence | Project payload/object correspondence retained from the linked qualified builds; no new compilation and no reconstruction of the original native parser toolchain. |
| Demonstrated semantics | Native selection/metadata arithmetic/108-byte delivery and actual constructor handback for trainer31 under five FS models; complete source-derived party guards retained. |
| Observed activation | Actual installed reader instructions in the initialized complete-caller CPU, Plus0/1, two seeds, two poisons and declared controls. |
| Unattributed links | Native FS/heap internals,187/189 other reader calls, other members/error paths and natural/device execution. |
