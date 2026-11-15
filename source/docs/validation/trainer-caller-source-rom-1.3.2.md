# Native trainer31 caller through construction and return

The exact r4 EN/IT caller now has one continuous initialized-API execution:
header/name preparation, six native Pokémon, strategy application, constructor
return, final battle-type store and caller return. One CPU and RAM context
cross every phase. Message, heap, archive and overlay-FS boundaries remain
explicit host models; natural encounter activation is a separate limit.

## Cosa farebbe un professionista di alto livello che non sto chiedendo

The [preparation case](trainer-preparation-source-rom-1.3.2.md) stops before the
constructor's first instruction. The [trainer31 constructor](strategy-31-source-rom-1.3.2.md)
starts at a separately initialized API. Join these boundaries by executing the
actual nested call, without copying Pokémon, fabricating a frame or restoring
CPU/RAM context between phases. Preserve the incoming caller registers, rather
than substituting the earlier constructor fixture's zero registers or cookies.

A correct party cannot establish caller lifetime or a final store. Require a
same-party message leak, wrong seed restoration, a missing108-byte free and a
skipped OR whose final value is unchanged. Keep entry/phase-mutation rejection
separate from completed caller paths. Independently review raw addresses, ABI,
resources, source snapshots and the evidence retained by the replay oracle.

## Il materiale più grezzo da cui partire

Use your own exact inputs and retained project ELF objects from the
[constructor foundation](strategy-constructor-source-rom-1.3.2.md#il-materiale-più-grezzo-da-cui-partire).
The [lineage method](rematch-source-rom-1.3.2.md) identifies required retail,
base1.1 and v4 inputs and their preparation. Current images are:

| Input | Bytes | SHA-256 |
| --- | ---: | --- |
| r4 EN | 152786844 | `2e30d6960bb059615fca7527700d86f8282e82ccbe99bf62e22f027453dc3d3d` |
| r4 IT | 159029760 | `13ebac02bdea3036511773587e6603ce6834e25f4b13d1a4662c3e954bfd5d4a` |

ROMs, raw members, saves, detailed traces and reports stay private. Whole-image
hashes identify language/revision; the IT internal header alone is insufficient.
No BIOS, emulator installation, personal save or new ROM build is needed.

The [installer](../../sgp13/teams.py),
[native hook](../../features/trainer-strategy/native.c),
[core](../../features/trainer-strategy/strategy.c) and
[configuration](../../sgp13/data/strategic-teams.json) provide the owned source
and recipe. The authenticated reconstruction uses Clang21.0.0
`clang-2100.4.1.1`, SHA-256
`fc5e3cbba6ad54059295cad716aacb05ace8235f5f7a6031f1d8c15d24bd6d66`,
with `--target=armv5te-none-eabi -mcpu=arm946e-s -mthumb -Os` and the installer's
freestanding/no-builtin/no-stack-protector/no-jump-table/no-unwind flags.
The preceding cases explain compiling the three project objects, independent
ELF mapping/relocations, linking and insertion. This case reattests those objects
and invokes no native compiler.

The580-byte strategy payload at`023D6000`, configuration192B plus320B padding at
`023D6600`, and full2048-byte owner are independently read back. Four native BLs
chain through`023D6228` to inherited Plus`023D8194`; only type3 site`02073A0C`
executes in this profile. Strategy text SHA-256 is
`09e88a137b006e8ba638770ba57e1a6e5fe9960787e05ec7c253cb230da04436`;
full owner at physical`001258C0` has SHA-256
`8a3450f4b0864b21ee0bdcb00b25dda966f2ad803246bbf15f343816ac2e234c`.
The owned50-byte post-form repair retains its independently qualified
[recipe](../../sgp131/trainer_fixes.py); it is distinct from original HGSS code.
Original native HGSS/MW and archived Plus compiler/object reconstruction remain
unavailable; their source correspondence and finite semantics are separate from
the owned ELF reconstruction.

Native HGSS reference is pinned to
`cb614ad23449d5852b40321dc409c4143872b35c`:
[trainer_data.c](https://github.com/ctrl-cheeb-del/pokeheartgold/blob/cb614ad23449d5852b40321dc409c4143872b35c/src/trainer_data.c),
[save.c](https://github.com/ctrl-cheeb-del/pokeheartgold/blob/cb614ad23449d5852b40321dc409c4143872b35c/src/save.c),
[pm_string.c](https://github.com/ctrl-cheeb-del/pokeheartgold/blob/cb614ad23449d5852b40321dc409c4143872b35c/src/pm_string.c).

| Installed point | Role and observed contract |
| --- | --- |
| `020733C0`, physical`000773C0` | Caller: r0=BattleSetup*, r1=SaveData*, r2=heap11;96-byte frame. |
| `020735D8` | Native header wrapper forwards raw NARC55/member31 into local SP+`14`; boundary writes exactly20B. |
| `02073404..0207340E` | Thirteen native word stores copy52B to BattleSetup+`5C`: header20B and incoming stack32B. |
| `02026A68`, caller`02073430` | Native packed name copy to setup+`70`, capacity8;10B EN/12B IT including EOS. |
| `02026380` | Native String invalidation, then modeled Heap_Free before construction. |
| `02073440`→`02073604` | Actual nested constructor entry, LR`02073445`, SP=outerSP−96. |
| `02073444` | Actual constructor return PC; SP and R4–R11 match its incoming caller context. |
| `0207345E` | Actual final OR store to battleType; value1 remains1 for header31. |
| `02073462`→`0200BB44` | Caller invokes modeled message destruction, LR`02073467`; outer ledger closes. |
| `02073468` | Native caller POP returns to the outer API sentinel with SP/R4–R11 restored. |

The complete caller code/alignment/pool window is176B, SHA-256
`76912054c0a5f1183697cc83d7fa853fffd712b1620b9b6054e06314968e867b`.
The newly exercised suffix`02073454..0207346A` is22B/10 instructions,
SHA-256`19832b95df15aaa5b3f36e27c8ea99ac5ee179bbf9c8678819bf0ee84080aa54`.
Literal pools remain data. The runtime caller map has138 qualified starts,
including zero-ID skips; it excludes the unexercised rival branch. The first
index0 skip reaches`02073444` before index1, so that PC identifies constructor
return only when the constructor phase is active.

NARC55/member31 is20B, SHA-256
`db2e0fa9e4d0b97a0d1721e878001bcddafe1e379827adccc37844cdbce13fff`,
physical`01F933B0` in both current images. NARC56/member31 has six18B records.
Class72/IV31/PID low byte`88`, capsule14 and the last member's move2
325→247/PP20→15 retain the [profile's raw/source attribution](strategy-31-source-rom-1.3.2.md).
The native constructor executes444 source-predicted LCG draws and504 observed
main helper calls,24 move loads/setters, six PartyAdd copies and final frees/seed
restoration. The complete six236B packets also match the earlier constructor
receipts for the same mode and seed.

Trainer names remain the raw packed729 words described in the
[name case](trainer-name-source-rom-1.3.2.md). Unused name bytes and16B mail fields
retain declared stack provenance, not zero initialization. The sparse readonly
SaveData fixture exercises native array9 resolution at SaveData+`230AC` and the
rival-name pointer getter, without reading an actual save. IDs[0,31,0,0],
battleType1, heap11, Plus0/1, cap100 and initial seeds are explicit API fixtures.

## I metodi e gli strumenti da usare

Use the [owner](../../features/trainer-strategy/README.md),
[full caller verifier](../../features/trainer-strategy/tools/attribuisci_chiamante.py),
[bounded bench adapter](../../features/trainer-strategy/test/caller_bench.py),
[adapter tests](../../features/trainer-strategy/test/test_caller_bench.py) and
[caller tests](../../features/trainer-strategy/test/test_caller_attribution.py).
Prepare Python/dependencies from the
[test bench](../test-bench.md#linking-source-to-an-exact-rom): tested Python3.14.7,
ndspy4.2.0, Capstone distribution5.0.9/module5.0.7 and Unicorn2.1.4.
From the repository root:

```sh
python3 source/features/trainer-strategy/tools/attribuisci_chiamante.py \
  --language EN --rom /path/to/own-r4-EN.nds \
  --objects /path/to/private/rematch/public-build-EN \
  --strategy-object /path/to/private/strategy/build-EN/teams.o \
  --json /path/to/private/reports/caller-EN.json.gz
```

Repeat for IT with its exact inputs/objects. Outputs must be fresh and outside
source/retained-object directories; input aliases are protected. Expanded reports
are bounded32MiB, stored reports8MiB. Reports retain input/source/ELF identities,
physical/logical offsets, actual outer APIs, native calls, resource ledgers,
counterproofs and scope. The separate readonly history command is:

```sh
python3 source/features/trainer-strategy/tools/rileggi_provenienza.py \
  --language EN --trainer 31 --caller --rom /path/to/own-r4-EN.nds \
  --retail /path/to/own-retail-EN.nds --base /path/to/own-base11-EN.nds \
  --v4 /path/to/own-v4-EN.nds --json /path/to/private/fresh-lineage-EN.json
```

The opt-in schema v3 binds the176B window across retailEN→base1.1→v4→r4 and
base1.1IT→v4→r4: seven exact identities. Retail IT's caller address remains
unattributed; the EN address is not read as its alias. Independent physical
readback is provided for v4/r4; compressed retail/base use decoded logical
sections without invented linear physical offsets. Default schema v2 remains
unchanged, verified against the archived reader on fresh EN/IT inputs.

The adapter authenticates the original constructor bench file SHA-256
`2255805889cda2ef008ba221bdbb49f4dcbf7bc81805cf9dbc246f8d66e68639`
and its run-method source SHA-256
`de6b5a87600bdd7e1c1339b37ba72ff355017e9088097de26807b7f6e964d36b`.
It preserves19 nested backend functions verbatim as Python AST, changes only
configuration/preparation and caller argument sites, then reverses those edits
and requires the complete original AST. The original files remain unchanged.
The compiled Python adapter uses a private namespace with the caller entry and
original outer stack top; it explicitly binds the sole CPU factory. Original
archive/heap/name/NARC/overlay-FS backends perform the actual modeled writes.
Audit callbacks alone would not provide those service implementations.

All memory maps and fixtures precede the first API. Three real outer APIs are
recorded: native SetSeed, caller, native GetSeed. At nested constructor entry the
observer's expected stack base becomes outerSP−96; the guest SP/registers/RAM
are preserved. On return the observer scope returns to the outer base, including
on exceptions. The composed608B stack bound is caller96B plus constructor512B;
it excludes native allocator/FS bodies and hardware WCET. Every other RAM region
is frozen or assigned a specific owner. Message resources occupy a separate
fixture arena and cannot move the constructor's allocations.

The qualified constructor bench uses Unicorn CPU model17, Cortex-A15, with fixed
ARM/Thumb code windows. An explicit ARM946 diagnostic exposed a code-hook width
difference for a Thumb BL crossing a1KiB boundary:2+2 instead of4. Four tests
using only project-generated synthetic instructions reproduce identical branch/
return state with those different hook streams. This case retains the original
bench model17; it admits no extra middle-half PC. Full-constructor ARM946 hook
qualification is not claimed. These are finite instruction/value checks, not
hardware or timing equivalence.

Per language the campaign has four mode/seed cases, one second-stack-poison
case, two observer-OFF cases and seven controlled negatives. Three negatives
stop early: the108B leak stops at constructor return, while wrong SP and a
phase register mutation stop before any constructor instruction. Four completed
negatives reject missing OR, live message, wrong restored seed and wrong last
move. Identical packets or final battleType cannot replace the required store,
resource closure or restore path. Temporary constructor heap/stack differences
from canaries/free poisoning are excluded from OFF RAM comparison; all caller
registers, prepared data, six whole packets, RNG, global RAM and backend events
must otherwise agree. Normalize JSON tuple/list representation before replay.

The first independent review exposed twelve replay false successes from removed
or altered metadata. Those mutations now fail while the retained native capture
passes: full extra-helper order, qualified PC/width/ISA, post-form/PID/capsule
semantics, raw model images and lifetime, backend events, caller writes and
service ABI are all bound. Source snapshots preserve each producer; strengthening
pure replay does not rewrite prior captures. An observer overhead change was
rerun from caller entry and its **entire result** matched the prior producer.

For reports named `caller-EN.json.gz`/`caller-IT.json.gz`, exact-ROM symlinks
`r4-EN.nds`/`r4-IT.nds`, object directories `public-build-EN/IT` and strategy
directories `build-EN/IT`:

```sh
SGP_CALLER_ROM_DIR=/path/to/private/rom-links \
SGP_CALLER_OBJECTS_DIR=/path/to/private/rematch \
SGP_CALLER_STRATEGY_DIR=/path/to/private/strategy \
SGP_CALLER_REPORT_DIR=/path/to/private/reports \
python3 -m unittest discover -s source/features/trainer-strategy/test -p test_caller_attribution.py
python3 -m unittest discover -s source/features/trainer-strategy/test -p test_caller_bench.py
```

Thirteen caller test methods and five adapter methods pass with no skips using
both exact inputs. Full host campaigns took94.794s EN/94.753s IT, with OS peak
RSS511901696B/525402112B. Positive paths reached608B guest stack and at most
1053333 code-hook steps; these include modeled boundary entries, not hardware
cycle measurements. Independent reviews checked raw/ELF inputs, both complete
campaigns, counters, OFF pairs, whole-packet continuity and history-reader limits.

| Conclusion category | Established evidence and remaining scope |
| --- | --- |
| Provenienza documentata | Native caller176 identity in seven images; owned Plus source/recipe and inherited data/body provenance remain distinct. Retail IT caller address is unresolved. |
| Corrispondenza binaria ricostruita | Earlier owned strategy/rematch ELF reconstruction is reattested against exact installed bytes. No original MW/Plus object rebuild is claimed. |
| Equivalenza semantica dimostrata | Source-derived six native Pokémon, RNG, setters and finite caller preparation/return contracts agree under the stated fixtures and host boundaries. |
| Attivazione osservata | One continuous caller API reaches actual native constructor, suffix store, modeled teardown and native return; counters distinguish equal outputs with missing operations. |
| Collegamenti ancora non attribuiti | Natural encounter/upstream activation, native message/allocator/FS bodies, other IDs/formats/rival/multi-ID cases, complete UI/battle/save/hardware behavior. |

No game code, ROM, ABI, IDs, defaults or save format changed. The reusable result
is a verified way to compose previously bounded paths while preserving their
actual context, explicit service models and independent readback obligations.
