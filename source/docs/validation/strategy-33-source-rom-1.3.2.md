# Trainer33: three changes and a PID override

Trainer33 needs three strategy substitutions in two Pokémon and a native
gender/ability override absent from the preceding constructor profiles. This
case follows the actual native entry, all six creations, setters/PartyAdd,
frees, original seed restoration and return. API input state remains initialized;
no copied Mon, body bridge or restored post-entry context is used.

## Cosa farebbe un professionista di alto livello che non sto chiedendo

Start from the [trainer32 method](strategy-32-source-rom-1.3.2.md), but qualify
the new branch before executing it. A low PID byte is persistent constructor
state, modified by gender and ability in a specific order. Verify both the raw
species ratio and the native getter, then the actual stores and subsequent PID.
Genderless species also require their own qualified return branch.

Compare complete packets by grouping all declared deltas for each Pokémon.
Normal must preserve six236B packets. Plus permits three move halfwords and
three PP bytes across two128B plaintext regions; four other packets, all target
headers and100B party tails remain identical. The fifth Pokémon already knows
move360, so finding360 in output does not establish the397→360 substitution.
Require all three real setter arguments and a separate wrong-argument
counterproof for each, with the genuine edited buffer unchanged.

The core returns the **number** of edits, not a Boolean. Its first Plus result
must be3, subsequent results0. Retain the earlier hook case's atomic rejection
evidence instead of repeating it without a new question. Independently review
new addresses, ISA boundaries, ABI, inputs and counterproofs.

## Il materiale più grezzo da cui partire

Use your own exact r4 inputs and retained project objects from the
[constructor foundation](strategy-constructor-source-rom-1.3.2.md#il-materiale-più-grezzo-da-cui-partire).
The required inputs are EN152786844B SHA-256
`2e30d6960bb059615fca7527700d86f8282e82ccbe99bf62e22f027453dc3d3d`,
and IT159029760B SHA-256
`13ebac02bdea3036511773587e6603ce6834e25f4b13d1a4662c3e954bfd5d4a`.
Full hashes establish revision/language. Keep ROMs, extracted members, saves,
BIOS and detailed execution receipts private.

The [installer](../../sgp13/teams.py),
[strategy sources](../../features/trainer-strategy/README.md) and
[ELF reconstruction](rematch-consumer-source-rom-1.3.2.md) specify compilation,
toolchain identity/flags, linking, insertion and independent readback. This
verifier invokes no compiler. Project strategy580B/config192B/padding512B/full
2048B owner and rematch dependencies are reattested. Inherited Plus code/table
and native HGSS code retain their missing-original-source/toolchain limits;
semantic correspondence is distinct from project binary reconstruction.

NARC55/member33 specifies type3/count6/class74. NARC56/member33 is108B, SHA-256
`701e542834f8d6a283890a94404201d9f7dfc222a3189278b2d2138491c8dbad`.
The [strategy specification](../../sgp13/data/strategic-teams.json) declares:

| Member/move slot (zero based) | Buffer offset | Move | Raw PP |
| --- | --- | --- | --- |
|1/0|26|209→435|20→15|
|5/0|98|21→89|20→10|
|5/1|100|397→360|20→5|

Species are375,82,205,227,437,208. IVs are31 throughout; item IDs are
0,0,0,0,285,158. Normal levels37,39,38,39,38,40 become Plus41,43,42,43,42,44
from maximum40/anchor44 and cap100. Class74's flag1 is at`020FFBDA`, physical
`00103BDA`, bound to the native class-table pointer at`02073600`.

Override bytes0,0,0,32,0,17 yield low PID state`78,78,78,79,79,80` in hexadecimal.
For Steelix208, override17 splits into gender1 and ability1. Raw personal
member208 field16 is127. The native helper loads127, adds2, then clears bit0:
127→129→128. Its incoming persistent value is`79`; the final value is`80`.
Species375/82/437 have ratio255 and follow the native genderless return.

Only the last Pokémon has capsule11, raw NARC185/member0[240:264],24B, physical
`045D832C`, SHA-256
`1876be303ff6bd3c3efcd950e6d1515dcfe0eb35f5395b1f8f3a04f342f0a79d`.
This slice already belongs to the qualified capsule model. Raw FAT/FNT/NARC
receipts also give personal/growth/name/learnset/move locations, sizes and hashes,
independently checked against the bench's ndspy view. No extracted data is shipped.

Incremental readback finds a56B retail member in both languages, SHA-256
`dbe8bee853490e3c2135b2bc618bde5a291ae770abd659a278ba125f17bda492`.
The108B member pinned above is already present in base1.1 and remains identical
through v4/r4, as does its header. The expanded roster is inherited; the three
strategy substitutions happen in Plus RAM. This identifies those intervals'
lineage without reconstructing their original authoring recipe.

### New native instructions and ABI

The [same constructor address map](strategy-constructor-source-rom-1.3.2.md#native-flow-abi-and-byte-locations)
starts at`02073604`, reads trainer33 and reaches strategy from the actual type3
site`02073A0C`. The guest owns its152B frame and all six236B Mon records. Phase
bookkeeping at`0207363E` is checked neutral over registers and4MiB RAM. Overlay126
remains installed with activation0; this is not rematch activation evidence.

Sixteen source-known PCs extend qualification to3009, with92 readonly ranges:

| Thumb interval | New PCs | SHA-256 |
| --- | --- | --- |
|`02073AB0..02073AC4`|9|`e8f6ccc6dcbb1828177c0d2b265ac03033499dbc5e4b729185a4dcff5f5c43df`|
|`02073ACC..02073AD6`|5|`f953adc99736cfcf1944feb09088338a7b797b9628b9b2039d102710eea615ad`|
|`0207000E..02070012`|2|`512215349f12a0b3c1b5527cf3939457e9f8577aea66c2e6fbe4dee2a23f68da`|

Intervals have exclusive ends. Hashes, Capstone widths, no code/data overlap
and independent raw mapping are required before CPU execution. The unused
subtract-two branch at`02073AC4/02073AC6` remains excluded. Existing ARM9
autoload, pools, veneers, overlay compression and data tables retain their
checks; qualified coverage is never grown automatically from a trace.

The call at`02073AB2` enters the already qualified getter`0206FBC4` with
R0/R1/R2=`208,0,18`, LR`02073AB7`, SP at caller-top−168 and result127. It must
return with its saved-register ABI intact, before the last IV-division event.
Three observed stores at`02073AB6`, `02073AC0`, `02073AD2` must target the same
PID word at caller-top−28, with values127,129,128. The observer records stores
without changing guest memory. The resulting PID, nature, ability, gender,
stats, CRC and complete packet are checked independently from raw resources.

The pinned reference is HGSS commit`cb614ad23449d5852b40321dc409c4143872b35c`,
particularly`TrMon_OverridePidGender` in its
[trainer_data.c](https://github.com/ctrl-cheeb-del/pokeheartgold/blob/cb614ad23449d5852b40321dc409c4143872b35c/src/trainer_data.c).
This is source correspondence and finite native semantic verification, not an
exact reconstruction of unavailable original MW objects.

## I metodi e gli strumenti da usare

Install the [pinned dependencies](../../requirements.txt). From repository root:

```sh
python source/features/trainer-strategy/tools/attribuisci_costruttore.py \
  --trainer 33 --rom /private-inputs/r4-EN.nds --language EN \
  --objects /private-results/rematch-EN-build \
  --strategy-object /private-results/consumer-EN-build/teams.o \
  --json /private-results/constructor33-EN.json.gz
```

Repeat with IT input/object paths and`--language IT`. Use fresh private outputs.
The finite profiles21/31/32 retain their earlier interfaces and trainer21
default. Profile33 checks13 observed paths per language: four positives (two
modes/two seeds), two declared old-hook RAM recipe baselines, two guards and
five counterproofs. `wrong_move_0/1/2` each reverts exactly one genuine native
setter argument; same-party wrong-seed and missing-free cases remain separate.
Two functional OFF comparisons check all packets, caller state, seed and SDK
events. Each path is bounded to3M instructions/512B stack.

Heap/name/raw archive/FS remain explicit SDK models; native code creates the
frame and packets, applies strategy, reads moves, runs setters and PartyAdd,
frees108/236B and restores its saved seed. Three outer APIs record initial
SetSeed, one constructor call through return and a separate observing GetSeed.
Caller SP/R4–R11, SDK volatile/NZCV guard, nonzero cookies, resource hashes,
allocation canaries, handles and unrelated RAM are checked. The post-getter
does not substitute for evidence of the actual restore call/store.

The [CPU-free resource lineage reader](../../features/trainer-strategy/tools/rileggi_provenienza.py)
accepts`--trainer 33` and the four exact images, as in the
[trainer31 commands](strategy-31-source-rom-1.3.2.md#i-metodi-e-gli-strumenti-da-usare).
It separates content from physical relocation, compressed logical ARM9 mapping
from raw current/v4 readback, and the unattributed retail IT class address.

Replay private receipts with fresh raw/ELF proofs, without guest reacquisition:

```sh
SGP_R4_ROM_DIR=/private-inputs \
SGP_REMATCH_OBJECTS_DIR=/private-results/rematch-EN-build \
SGP_STRATEGY_OBJECT=/private-results/consumer-EN-build/teams.o \
SGP_CONSTRUCTOR_REPORT_DIR=/private-results \
SGP_CONSTRUCTOR_REPORT_NOME='constructor33-%s.json.gz' \
SGP_CONSTRUCTOR_TRAINER=33 \
python source/features/trainer-strategy/test/test_constructor_attribution.py
```

Default ROM names are`r4-EN.nds`/`r4-IT.nds`;`SGP_R4_ROM_NOME` overrides that
pattern. The project objects are identical across languages. Historical source
hashes and captures remain intact; a fresh trainer32 regression checks its
entire preceding receipt after extending the observer and plural comparator.

Success requires all three substitutions and exact raw PP, no other packet
changes, core result3 then0, getter/store/PID chain, source-derived six-Mon
semantics and complete ABI/lifetime/seed evidence. Tests reject each individually
omitted edit after valid checksum reconstruction, wrong getter/stores/count,
profile/class/code drift, truncated vectors/packet widths and forged OFF proofs.
The earlier [hook case](trainer-strategy-source-rom-1.3.2.md) separately proves
late-delta atomic rejection and repeated-buffer behavior.

Project binary correspondence, documented inherited provenance, targeted native
semantics and initialized activation are distinct conclusions. Natural battle
activation, other trainer IDs/formats, original native compilation, SDK internals,
SAVE/device compatibility and game timing remain outside this case.

Both exact languages passed13 observed paths and two functional OFF comparisons.
EN/IT acquisition took109.124/109.835s, maximum OS RSS290439168/294109184B;
the largest guest count was1138430 instructions, stack512B. Positive paths
exercised444 class RNG draws and12 OTID draws. The source oracle retains
anti-shiny retry semantics;456 is the exercised corpus, not a universal bound.
Fifteen replay methods passed without skips for profiles21/31/32/33. These
bounded host results establish no timing improvement or hardware coverage.
