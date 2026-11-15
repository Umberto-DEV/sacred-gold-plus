# Native initial friendship and the owned Plus override

This case continues the [native growth/EXP caller](native-growth-caller-source-rom-1.3.2.md).
The next personal-data read supplies initial friendship35. The native getter and
setter produce a valid transient Pokémon with that value. Later, an owned Plus
patch replaces it with255 before PartyAdd. Observing only the final party would
miss this distinction. Other184 Normal/186 Plus ReadWhole calls remain explicit
models. ROMs, saves, gameplay sources, ABI and identifiers are unchanged.

## Cosa farebbe un professionista di alto livello che non sto chiedendo

Distinguish the provenance of the getter, its two different setter APIs, the
owned installer and the final data. Reconstruct both directions: source/recipe
through emitted bytes and readback; installed instructions through callers,
inputs and the matching source. Seek a counterexample whose final output is
unchanged but whose intermediate behavior differs. Verify stack, callbacks,
branch conditions, lifetime and observer effects independently. Record compiler
and source gaps instead of treating reference names as a reconstructed binary.

## Il materiale più grezzo da cui partire

Use your own exact r4 ROM and retained or reproduced project objects from the
[parent input/build guide](native-party-caller-source-rom-1.3.2.md#il-materiale-più-grezzo-da-cui-partire).
EN ROM:152786844 bytes,SHA-256
`2e30d6960bb059615fca7527700d86f8282e82ccbe99bf62e22f027453dc3d3d`;
IT:159029760 bytes,SHA-256
`13ebac02bdea3036511773587e6603ce6834e25f4b13d1a4662c3e954bfd5d4a`.
Whole-image identity takes precedence over IT's inherited header. Keep your
ROMs, extracted data, packets, full RAM, saves and BIOS private; none are shipped.

The [personal-data case](native-personal-caller-source-rom-1.3.2.md) already
checks retail→base1.1→V4→r4 in both languages. Its exact44-byte member355 in
FNT `a/0/0/2`,FAT file131,count508 has SHA-256
`1954a12fbe5fe597e544784d31c7f0a89b98b73c5e53ca1d768d481043749270`.
Here byte18 is35, selected by native attribute20. No new historical execution
is inferred or repeated. Current archive/member physical offsets are
EN `0x087FB200/0x087FFF1C`, IT `0x08D3E800/0x08D4351C`.
BTAF16/4076, BTNF4092/20, GMIF4112, member row2868,start15620/end15664,
archive offset19740. Independent FAT/FNT/NARC arithmetic and ndspy agree.
The actual native table route is `0x02007520→0x0210F210`,
row2=`0x0210F218→0x0210F1E0→a/0/0/2`. These are inherited data and native code.

The reference source counterparts in `src/pokemon.c` are CreateBoxMon,
GetMonBaseStat, AllocAndLoadMonPersonal, GetPersonalAttr, SetBoxMonData and
SetMonData. The reference fork and exact pin
`cb614ad23449d5852b40321dc409c4143872b35c` are documented in the
[native reader guide](native-narc-reader-source-rom-1.3.2.md).
Original native MW compiler/objects are unavailable. Reference semantics and
installed-byte execution remain distinct from native binary reconstruction.

The later override has a different owner:
[`sgp131/trainer_fixes.py`](../../sgp131/trainer_fixes.py), source SHA-256
`bddb793ec901d9102a3d42d6a5278b78232f26641ecd59ebe9003fd51ec89c49`.
`_patch_form_stats`, called by `apply` through
[`mechanics_stages.py`](../../sgp131/mechanics_stages.py), guards the previous
50 bytes and four form-setter/helper caller pairs before an in-place ARM9 write.
`FORM_STATS_AFTER` at RAM `0x02073AE4`, current physical `0x77AE4`, has SHA-256
`219412a0140b9076f367d53bb22bc0a80ddc1806d68d99f3a9a8f1b9e89de2e3`.
Its46-byte body has19 static instruction starts; final4 bytes are two written
NOPs outside this executed path. The selected no218 branch executes17 of those
starts. This is a literal patch recipe; no compiler or ELF is needed to emit it.
The verifier independently emits Thumb halfwords and PC-relative BL encodings,
then compares emitted bytes, recipe constant, raw ARM9 and decoded sections.
The inherited object checks also reverify the Plus module/stub and teams objects.

The full50-byte before helper is identical in retail, base1.1 and V4, in both
languages: SHA-256 `313e9e41edd7d3527070155115ea76c4726786a72ee96faba9d5df6ccb3b7574`.
Only r4 has the after recipe above. All eight4-byte BLs (four form setters and
four helper callers) retain their target across all eight images. Earlier
reports covered42/50 bytes for retail/base; the
[offline helper reader](../../features/trainer-strategy/tools/rileggi_helper_amicizia.py)
now closes the missing bytes, including padding, with82 bytes per image.
It verifies complete decoded spans and both Capstone and native BL decoding;
direct physical offsets are reported only for current uncompressed V4/r4.
This lineage concerns the code component, not all trainer data or historical
execution. The same raw personal44-byte member remains inherited data.

## I metodi e gli strumenti da usare

[Verifier](../../features/trainer-strategy/tools/attribuisci_amicizia_chiamante.py),
[adapter](../../features/trainer-strategy/test/friendship_narc_bench.py),
[portable checks](../../features/trainer-strategy/test/test_friendship_narc_bench.py)
and [receipt replay](../../features/trainer-strategy/test/test_friendship_caller_attribution.py)
compose seven authenticated parent-function recipes and a Close counter recipe.
Full parent source hashes and exact edit occurrence counts are checked. The
33 source identities include the owned installer. No sealed parent is changed.

```text
CreateBoxMon BL0206DF8A
 → GetMonBaseStat(355,20)0206FBE8
   → AllocAndLoadMonPersonal → LoadMonPersonal
     → native ReadWhole02007508 → parser0200732C → actual return0206FAA2
   → LDRB byte18 at0206FB70 → getter35
 → SetBoxMonData(mon,9,&local)0206ED70
   → internal0206EDE8 → STRB0206F03E, initial35
 → CreateMon return02073A16, valid encrypted packet35
 → Plus helper02073AE4: ability, stats, MonHasMove218
   → selected no218 →255 → SetMonData0206EC40
     → internal0206ECD0 →0206EDE8 → STRB0206F03E, override255
 → helper return02073A5E → PartyAdd return02073A68, actual party slot255
```

The direct initial getter omits the8-byte EXP wrapper. With outer SP=`0x023BF000`
and inner=outer−96, reader SP is inner−312=`0x023BEE68`. Entry R0 is arena+872,
R1=2,R2=355,R3=`0x02007509`. Saved R4..R7 are destination,355,`FFFF0000`,
`FFFF0000`; R8..R11 retain caller cookies. R12=arena+216 comes from the first
nickname copy. LR=`0x0206FAA3`. Native reader136-byte frame reaches544 below
outer; its56-byte guard ends at600. Whole caller maximum remains608.
Capture actual136-byte preimage and56-byte guard before stack reuse. The
observer borrows the existing CPU, changes no RAM/registers, and performs no
standalone setup, new CPU, synthetic read event or result bridge.

The12-point getter/setter flow checks full LDRB register transition, every frame,
high cookies, source arguments and real return residues. SetBox9 receives the
u32 local at inner−272. At its actual STRB, SP=inner−320, input R4=inner−272,
R7=blockA and target=arena+180. Header flags2 mean the box is decrypted.
The override calls **SetMonData**, without passing through SetBoxMonData:
its EC40/ECD0/EDE8 frames produce STRB SP=inner−216,input R4=inner−168.
Header flags are0 during this decryption transaction, so flags0 alone cannot
justify decoding a packet inside the setter. Both store contexts are captured
as plaintext byte transactions. Full encrypted packet decoding occurs only
outside the APIs, at six actual checkpoints: CreateMon return, helper entry,
before override, after override, helper return and PartyAdd return.

At the pre-BL callsite `0x02073B0C`, LR is still the previous call's
`0x0201FF59`; callee entry EC40 receives `0x02073B11` from the executed BL.
The inherited native API ledger checks callee entry/return ABI independently.
The first trainer31 Pokémon has species355,item0,form0,capsule0 and moves
310,109,425,228. None is218. For this finite profile, all three pre-override
236-byte packets equal the final packet with only friendship255→35, a recomputed
box checksum and corresponding128-byte box re-encryption. Party data100B and
header/PID are unchanged. All three later packets equal the actual PartyAdd slot.
This equality is checked on bytes, not inferred from a field-only decoder.

Current resident ARM9 offsets use RAM−`0x02000000`+`0x4000`, e.g.
DF8A→`0x71F8A`,FB70→`0x73B70`,F03E→`0x7303E`,ReadWhole→`0xB508`.
The previous guide retains the native reader's103 starts and five opaque FS
models. Selected44-byte delivery is now native; other184/186 original read
backends run exactly once, distributed as NARC2×76,3×23,33×6,11×79/81.
Native header, party, growth, personal-for-EXP, messages and six names keep their
qualified owners. No source/toolchain gap is filled with an assumed symbol.

## Reproduce

Use the linked parent's Python3.14,ndspy4.2.0,Unicorn2.1.4 and Capstone5 environment
and project objects. No full ROM build, emulator, save or BIOS is required.
Outputs must have fresh names outside `source` and retained object directories.

```sh
python source/features/trainer-strategy/tools/attribuisci_amicizia_chiamante.py \
  --rom "$ROM" --language EN --objects "$REMATCH_OBJECTS" \
  --strategy-object "$STRATEGY_OBJECTS/teams.o" --readback-only \
  --json "$PRIVATE_OUTPUT/friendship-readback-EN.json.gz"
python source/features/trainer-strategy/tools/attribuisci_amicizia_chiamante.py \
  --rom "$ROM" --language EN --objects "$REMATCH_OBJECTS" \
  --strategy-object "$STRATEGY_OBJECTS/teams.o" \
  --json "$PRIVATE_OUTPUT/friendship-caller-EN.json.gz"
python -m unittest discover -s source/features/trainer-strategy/test \
  -p test_friendship_narc_bench.py
SGP_FRIENDSHIP_CALLER_ROM_DIR="$ROMS" \
SGP_FRIENDSHIP_CALLER_REPORT_DIR="$PRIVATE_OUTPUT" \
SGP_REMATCH_OBJECT_DIR="$REMATCH_CASE" \
SGP_STRATEGY_OBJECT_DIR="$STRATEGY_CASE" \
python -m unittest discover -s source/features/trainer-strategy/test \
  -p test_friendship_caller_attribution.py
```

For the complete helper lineage, supply your own four exact inputs per language:

```sh
python source/features/trainer-strategy/tools/rileggi_helper_amicizia.py \
  --retail "$RETAIL" --base "$BASE11" --v4 "$V4" --rom "$ROM" \
  --language EN --json "$PRIVATE_OUTPUT/helper-lineage-EN.json"
```

Repeat for IT; replay follows the
[parent directory convention](native-party-caller-source-rom-1.3.2.md#reproduce-with-your-own-inputs).
Readback mode authenticates code, object recipes, paths, raw member and the
owned50-byte emitter without constructing a CPU. Runtime reports remain private.
Use one producer,180s/1GiB OS high-water RSS/2MiB log per command,16MiB case,
1GiB peak disk and at least10GiB free after peak. Guest limit is3M hooks/608B
stack. An external limiter must bound wall time/log output; report storage and
host budget checks also apply.

## Verified results

Final20 executions passed, ten per language, on one frozen verifier/adapter.
Ten portable tests and nine exact-input replay tests passed without skips.
Independent raw/source/ABI, counter, helper-lineage and final EN/IT reviews found
no unresolved blocker. Review exposed transcript gaps in the prior byte,
store registers and checkpoint ABI; source-derived guards and negative tests
now reject them. Earlier matrices and interrupted attempts remain separate
private evidence, rather than being relabeled as current-source executions.

All eight positive parties, Trainer52, final seeds and entire final4MiB RAM
hashes equal the preceding case, with117 extra hooks. EN totals are1040460
Normal/1056687 Plus; IT adds34. Prefix604/638 is unchanged. The reader contributes
118 hooks instead of one modeled callback fetch; these counts are not timings.

| Check | Wall time | OS peak RSS, bytes |
| --- | ---: | ---: |
| Final EN10 | 104.837s | 586072064 |
| Final IT10 | 105.019s | 599638016 |
| Portable10 | 1.136s | 76627968 |
| Replay9, both languages | 8.617s | 725893120 |
| Four-image helper lineage EN / IT | 1.570s /1.830s | 219316224 /225624064 |
| Current readback EN / IT, no CPU | 0.589s /0.552s | 220446720 /226738176 |

## Counterproofs and scope

The matrix uses Plus0/1×two seeds, another stack poison, two OFF pairs, a
volatile FS-register control and two counterproofs per language. OFF projects
exactly ten allocation canaries80B and two already-freed buffers:44B personal
at arena+384 and404B growth at+448,528B total. ON free poisons dead bytes withDD;
OFF free retains raw bytes. Prove the seven actual allocation/free events and
all preimages. Preserve the live44B at+872 and all gaps. Per-run freeze still
permits only192B reader stack and live destination; no entire-heap mask is used.

Counter1 skips Close only. It can retain phase/final RAM and packets while the
file ledger remains open; the source-bound ownership oracle rejects it even
with variant tags disguised. Counter2 changes only R5=35→0 at actual PCFB72,
after native LDRB35. Raw member, native reader and full pre-state remain equal.
Getter and initial store must really receive0; the first three packets must
match an independent one-field re-encryption. The Plus helper then restores255.
All six final packets, Trainer52, seed, all name evidence including later RAM
scope hashes, and entire final4MiB RAM are required to equal the baseline.
The positive oracle still rejects the disguised counter through the getter
result. Final equality is thus evidence of lifetime/override, not proof that
initial friendship was never executed.

| Conclusion | Evidence and limit |
| --- | --- |
| Documented provenance | Personal byte18 and getter/setters are inherited HGSS; later50-byte guarded installer belongs to Plus. |
| Reconstructed binary correspondence | Independent Thumb emission of owned50B equals recipe and installed bytes; project objects/readback rechecked. Original native MW binary reconstruction unavailable. |
| Demonstrated semantics | Actual getter/store35, six valid packet checkpoints, explicit Plus no218 override255, counter0 transient change despite final equality. |
| Observed activation | Initialized trainer31 caller under declared FS/heap models; selected Plus flags, seeds, poison and controls only. |
| Unattributed links | Native FS/heap internals,184/186 other reads, other IDs/formats/errors, natural encounters/card/full battle/UI/save/hardware. |

No game fix, speedup or recovered memory is claimed. A possible future reduction
of redundant initialization needs wider species/move/caller coverage and a
maintainer decision; this finite overwritten-field case alone does not justify
removing the initial getter or either setter.
