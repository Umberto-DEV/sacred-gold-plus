# Trainer21 through the actual native constructor

Trainer21 now has an exact-input path from `CreateNPCTrainerParty` entry through
six native creations, strategy application, move/PP setters, PartyAdd, original
seed restoration, frees and return. No copied Pokémon or body-frame handoff is
used. BattleSetup and Plus/seed state remain initialized API fixtures; a natural
encounter and whole-battle balance remain separate questions.

## Cosa farebbe un professionista di alto livello che non sto chiedendo

The [positive hook](trainer-strategy-source-rom-1.3.2.md) and
[move consumer](strategy-move-consumer-source-rom-1.3.2.md) establish different
boundaries. The latter explicitly copies a species22 Mon. Close that gap by
starting at the native constructor API and allowing the guest to produce all
six records and its own frame. Observe six strategy calls on the actual buffer,
with one complete108-byte copy in Plus and none in Normal.

Compare the same current image with the installer's old-hook preimage recreated
at four declared RAM BL sites. This isolates the strategy contribution while
retaining the existing Plus level calculation. Require whole-packet equality
for the first five Pokémon and permit only the specified move/PP change in the
last one's128-byte plaintext. This covers metadata and mail bytes that a short
field decoder would omit. The RAM baseline is not a historical whole-ROM claim.

A correct party alone cannot prove lifetime or seed restoration. Use same-party
wrong-restore and missing-free counterproofs, plus a wrong last move argument
with the genuine edited buffer unchanged. Compare the instrumented result with
the existing bench without this observer before using its measurements.

## Il materiale più grezzo da cui partire

Use your own exact r4 ROM, rematch project objects and strategy object prepared
by the preceding [inert rematch](rematch-source-rom-1.3.2.md) and
[dependency reconstruction](rematch-consumer-source-rom-1.3.2.md) cases.
Their recipes describe source compilation, linking, insertion, header/FAT/FNT,
overlay tables, ARM9 autoload and independent byte readback.

| Input | SHA-256 |
| --- | --- |
| r4 EN,152786844B |`2e30d6960bb059615fca7527700d86f8282e82ccbe99bf62e22f027453dc3d3d`|
| r4 IT,159029760B |`13ebac02bdea3036511773587e6603ce6834e25f4b13d1a4662c3e954bfd5d4a`|
| Strategy `teams.o` |`e2429f61c7ee16071d303f7ca55cbb1553508720c6fe97b77aead9ce56e499e1`|
| Rematch `rematch-variants.o` |`cfc4dce49574df18f3064fb66c2f8d75b66f5e6ed63e26d36e97893e2168817a`|
| Rematch `rematch-stub.o` |`43848467a67b11f1fec275a63e89f861c8641f325c86af38df03320a10d7c68a`|

The source recipe and compiler flags are in the
[installer](../../sgp13/teams.py) and
[owner](../../features/trainer-strategy/README.md). Strategy580B and configuration
192B plus320B padding are reattested, as is the full2048-byte owner. The retained
reconstruction used authenticated Apple Clang21.0.0 `clang-2100.4.1.1`, compiler
SHA`fc5e3cbba6ad54059295cad716aacb05ace8235f5f7a6031f1d8c15d24bd6d66`.
This verifier invokes no compiler. The archived Plus body/table and original
native HGSS compiler remain distinct provenance limits.

The six recipe source hashes are enforced before execution. Independent ELF
mapping/relocation readback ties the objects to installed Thumb code and pools.
The owned50-byte post-form repair is the fixed recipe in
[trainer_fixes.py](../../sgp131/trainer_fixes.py), qualified by the
[first-Mon case](rematch-firstmon-source-rom-1.3.2.md); it is not original HGSS code.
The rematch module stays installed with activation0 throughout this case.

Raw NARC`a/0/5/5` and`a/0/5/6` supply trainer21 header/member. The public
[specification](../../sgp13/data/strategic-teams.json) pins the108-byte member by
SHA-256 and changes only offset100,206→450. The native class is67 and its
qualified table flag is1. Difficulty200 produces IV24 for the first five
members;255 produces IV31 for the last. PID state persists as
`78,78,79,79,79,79` hexadecimal across override values`0,0,32,0,0,32`.

The six species are12,15,127,193,214,123. Source-derived levels are
`18,18,19,18,19,21` in Normal and`20,20,21,20,21,23` in Plus, from the existing
opponent-level table at maximum21/anchor23 and cap100. Native raw resources
provide personal records, growth, names, learnsets, moves and the last member's
capsule12. Resource receipts include actual member hashes and physical offsets.
Only members exercised by the run are summarized; extracted data stays private.

### Native flow, ABI and byte locations

The driver initializes a coherent BattleSetup for enemy index1/battleType1,
heap11, Plus0/1, cap100 and one of two original seeds. It then calls the actual
constructor once. The native prefix allocates108/236 bytes, reads NARC56/member21,
loads/unloads the installed inert overlay126 and reaches`0207363E`. The observer
records registers/RAM, changes only its Python bookkeeping, verifies neutrality
and lets the same CPU continue. It performs no context restoration, Mon copy or
body-frame write.

The guest constructs all six Pokémon. Each reaches the actual strategy hook,
existing Plus level routine, CreateMon and setters, followed by the owned
post-form helper and actual PartyAdd return. Capsule12 uses the native
24-byte setters and the qualified raw member185 model. The last calls at
`02073A84`/`02073A8A` free the original108/236 allocations;`02073A90` calls
native SetSeed using the saved original value;`02073A96` restores the caller
frame and returns.

Three outer emulation calls are explicitly recorded: initial native SetSeed,
one constructor entry-to-return, then a separate native GetSeed observation.
The post-getter cannot substitute for evidence of the actual restore store.
SP and R4–R11 at the constructor return are checked, including a guard with
nonzero R4–R7. The SDK volatile-register/NZCV guard preserves the six outputs;
C caller-saved registers/flags are not assigned an invented preservation rule.

| Region | Loaded address | Physical offset in these r4 inputs |
| --- | --- | --- |
| Native constructor entry |`02073604`|`00077604`|
| Resident forwarding stub64B |`023D59E0`|`001252A0`|
| Strategy owner2048B |`023D6000`|`001258C0`|
| Type3 level BL |`02073A0C`|`00077A0C`|
| Native final restore BL |`02073A90`|`00077A90`|
| Observing GetSeed12B |`0201FD2C`|`00023D2C`|

The qualified union has2993 code PCs and91 readonly ranges. The inherited sparse
maps are checked by hash, Capstone ISA/width and independent raw ARM9 sections;
ELF maps admit the complete580-byte strategy code. Newly needed readonly
coverage is bounded to source-known pools and formula-checked tables.
GetSeed has6B code,2B alignment and4B pool; its base`021D15A4` plus4 addresses
the native RNG state. The full128-byte substructure table at`020FF733` is
bound by the literal at`02072630` and checked against32 inverse-permutation rows
(SHA`13df5d291eb7b8276c065d7033d8044a9b430df77c05d04069cd3438e54b179a`).
New trainer PIDs exercise rows absent from the earlier sparse receipts.
Native CreateMon clears all236 workspace bytes before field generation; the
zero-allocator model does not replace that native initialization.

Native HGSS correspondence uses reference commit
`cb614ad23449d5852b40321dc409c4143872b35c`, particularly
[trainer_data.c](https://github.com/ctrl-cheeb-del/pokeheartgold/blob/cb614ad23449d5852b40321dc409c4143872b35c/src/trainer_data.c)
and [pokemon.c](https://github.com/ctrl-cheeb-del/pokeheartgold/blob/cb614ad23449d5852b40321dc409c4143872b35c/src/pokemon.c).
This is correspondence and targeted semantic verification, not reconstruction
of the missing original MW objects. Overlay compression/autoload and physical
mapping are read explicitly; the table is not a universal address-offset rule.

## I metodi e gli strumenti da usare

Install the [pinned dependencies](../../requirements.txt). From repository root,
use private exact inputs, retained project objects and fresh output paths:

```sh
python source/features/trainer-strategy/tools/attribuisci_costruttore.py \
  --rom /private-inputs/r4-EN.nds --language EN \
  --objects /private-results/rematch-EN-build \
  --strategy-object /private-results/consumer-EN-build/teams.o \
  --json /private-results/constructor-EN.json.gz
```

Repeat with IT and its matching input. The object identities above are shared
across the qualified EN/IT builds. The CLI refuses existing outputs, input
aliases, source paths and retained-object directories. It bounds expanded
output to16MiB and supports deterministic gzip. Keep reports private: they
contain generated Pokémon and extracted resource data.

The [verifier](../../features/trainer-strategy/tools/attribuisci_costruttore.py)
runs four ordinary cases per language (two modes×two seeds), two declared
old-recipe RAM baselines, two ABI guards and three counterproofs. The original
seed affects restoration but not the resulting party: the native routine
reseeds each member from its source record/class before generation.

```sh
SGP_R4_ROM_DIR=/private-inputs \
  SGP_REMATCH_OBJECTS_DIR=/private-results/rematch-EN-build \
  SGP_STRATEGY_OBJECT=/private-results/consumer-EN-build/teams.o \
  SGP_CONSTRUCTOR_REPORT_DIR=/private-results \
  python source/features/trainer-strategy/test/test_constructor_attribution.py
```

The [test suite](../../features/trainer-strategy/test/test_constructor_attribution.py)
replays those receipts against freshly authenticated input/code/object/resource
proofs. It checks call/RNG/lifetime traces, whole-packet strategy deltas, OFF
proof binding, forged receipts, getter/table drift and output protection.
Replay is not a fresh constructor execution and retains each capture's recorded
source identity. Missing private material causes explicit skips. Default file
patterns are`r4-%s.nds` and`constructor-%s.json.gz`, configurable through
`SGP_R4_ROM_NOME` and`SGP_CONSTRUCTOR_REPORT_NOME`.

The functional OFF comparison uses the existing bench without this observer,
with the same declared SDK boundaries. All six packets, final registers, seed
and every SDK event must agree. Canary/free-poison scratch is explicitly
separate. Replay binds the OFF proof's party/event hashes, seed, end state and
scope to its paired positive receipt; a bare success flag is insufficient.

Counterproofs preserve the relevant premises: wrong restoration and a missing
108-byte free keep the complete party identical; the latter also keeps the
original seed. A wrong last move argument keeps the genuinely edited buffer
but gives the native setter206 instead of450. All three reach the native return
and fail the corresponding semantic/lifetime checks when relabeled ordinary.

Record argv, exit codes, exact source/input hashes and OS receipts. Budgets are
180s/1GiB RSS/2MiB logs/16MiB case output and3million guest instructions/512B
stack, retaining10GiB after a planned1GiB disk peak. Counts and host wall time
are verification bounds, not game cadence or hardware speed measurements.

### Result and remaining links

The finite contract qualifies six actual native Pokémon, the one-time strategy
copy and final lifetime for trainer21. Normal/Plus source fields, IV24/31,
stateful PID, OTID/RNG draws, stats, move/PP resources, capsule12 and copied
slots agree. The old-recipe baseline shows the strategy preserves the existing
level/stat/RNG behavior while changing only the intended last move and PP.

The eleven paths passed in each language, including all counter premises. Nine
receipt-replay methods passed without skips, with fresh raw admission and forged
proof checks; replay adds no new CPU campaign.

This closes the copied-Mon gap for trainer21. The other six strategy IDs,
other formats/forms, naturally produced encounter/overlay state, whole-battle
balance, native SDK failures and hardware/raw-save validation remain separate.
No game repair, optimization, installed ROM/save change or performance gain is
implemented. Original native and historical Plus compiler limits remain explicit.
