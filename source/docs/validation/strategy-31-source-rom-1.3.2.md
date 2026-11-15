# Trainer31 through the native constructor

This case extends the [trainer21 constructor method](strategy-constructor-source-rom-1.3.2.md)
to one different, explicitly qualified profile. It follows trainer31 from the
native constructor entry through six Pokémon, actual strategy and move setters,
PartyAdd, frees, original RNG restoration and return. API input state remains
initialized; natural encounters, SAVE and hardware are separate coverage.

## Cosa farebbe un professionista di alto livello che non sto chiedendo

Treat a new trainer as a new evidence question. Trainer31 has a different class
byte, PID state, IVs, levels, resources, capsule slice and move position. Reuse the
qualified instruction engine while authenticating those differences before
execution. Never expand an allowed address map from an unexamined trace.

Compare both directions: the source recipe and ELF to installed bytes, then
actual constructor calls and data loads back to that recipe and its raw inputs.
Use the same-image old-hook RAM recipe baseline to isolate strategy's effect.
Normal must preserve all six236-byte packets. Plus must preserve the first five
whole packets, and the last packet's header,100-byte party tail and all128-byte
plaintext except the specified move and PP. The third Pokémon also knows move325:
a blanket325→247 substitution must fail even with a valid checksum.

Require complete ABI, resource and lifetime evidence. Same-party wrong-seed and
missing-free cases, a wrong native last-move argument with a genuine edited
buffer, and a functional observer OFF comparison expose different false successes.
Independent review checks the raw class byte, capsule ABI and finite profile.

## Il materiale più grezzo da cui partire

Use your own exact r4 inputs and retained project objects. Their SHA-256 values,
preparation, dependency versions and compiler identity are listed in the
[preceding case](strategy-constructor-source-rom-1.3.2.md#il-materiale-più-grezzo-da-cui-partire).
The input ROMs are EN152786844B,
`2e30d6960bb059615fca7527700d86f8282e82ccbe99bf62e22f027453dc3d3d`,
and IT159029760B,
`13ebac02bdea3036511773587e6603ce6834e25f4b13d1a4662c3e954bfd5d4a`.
Full input identity determines language/revision; an internal header label alone
does not. Keep ROMs, raw members and output receipts outside the source tree.

The [installer](../../sgp13/teams.py) compiles
[native.c](../../features/trainer-strategy/native.c) and
[strategy.c](../../features/trainer-strategy/strategy.c), links580B at`023D6000`
and composes the configuration from
[strategic-teams.json](../../sgp13/data/strategic-teams.json). The
[rematch consumer reconstruction](rematch-consumer-source-rom-1.3.2.md) supplies
the exact object recipe, flags, ELF/symbol/relocation checks and compiler hash.
This case invokes no compiler. Inherited Plus level code/table and original HGSS
native code have separate provenance; their original compiler objects remain
unavailable. Data, code and padding are checked separately within the2048B owner.

The canonical trainer member is NARC56/member31,108B, SHA-256
`2096c9d5a3943dca51dec0ea9b0b006387f2fb5b0d6778a49f58c2803806395c`.
Its NARC55 header specifies type3/count6/class72. Species are
355,353,93,200,302,94. Difficulty255 yields IV31 for every member;
override0 throughout preserves PID low byte`88`. Class72 means432 class RNG
draws across six creations, followed by12 OTID draws in the exercised corpus.
The source oracle also models anti-shiny retries;444 is this corpus, not a
universal bound. Normal levels are27,27,28,28,28,29. The inherited table's
maximum29/anchor31 yields Plus29,29,30,30,30,31 at cap100.

| Data | Loaded address / member slice | Physical offset in both exact inputs |
| --- | --- | --- |
| Class72 flag0 |`020FFBD8`,1B |`00103BD8`|
| Last capsule14 |NARC185/member0,312..336 |`045D8374`|
| Move325 resource |NARC11/member325,16B |`01095B3C`|
| Move247 resource |NARC11/member247,16B |`0109565C`|

The capsule24B slice SHA-256 is
`51b35c8116900ddb06e7c25c463d69740a87b08bf3934d7bfd03c6e683a53949`.
Only the last Pokémon has capsule14 and held item158. Raw FAT/FNT/NARC readback
is compared with the bench's independent ndspy view. Resource receipts record
member sizes, hashes, physical offsets, growth, personal, name and move inputs;
retail bytes are not distributed here.

The incremental resource comparison separates inherited team data from Plus's
runtime strategy. Both retail inputs have a72B trainer31 party member, SHA-256
`b64f34511a747d18f7e1e64addfc5e746f222cb6c005eae88d823f65ce0afbd0`.
Both base1.1 inputs already contain the108B member pinned above; its content
remains identical through v4 and r4. Thus the six-member roster is inherited,
while325→247 is the guarded Plus RAM edit, not a rewritten ROM party member.
This proves content lineage in these intervals, not the unavailable original
authoring history. Native class flag0 agrees across the seven address-qualified
images. Retail IT's native class address is deliberately left unattributed.

### Caller, ABI and lifetime

The [same native flow and address map](strategy-constructor-source-rom-1.3.2.md#native-flow-abi-and-byte-locations)
starts at`02073604`, reads trainer31 and reaches the real type3 BL at`02073A0C`.
The guest creates all236-byte Pokémon and its152-byte constructor frame; no Mon
fixture, body bridge or context restoration is used. At`0207363E`, changing the
observer's Python phase bookkeeping is verified neutral over registers and4MiB
RAM. Rematch overlay126 remains installed with activation0.

The qualified union remains2993 instruction PCs. One source-known class-table
byte adds a92nd readonly range. The original pointer at`02073600` must still
reference`020FFB90`; both raw ROM and mapped image must supply flag0 at class72.
The same formula-checked nature/permutation tables and GetSeed code apply.
ARM9 sections/autoload and overlay compression are read explicitly; physical
offsets above are exact-input facts, not a universal address subtraction rule.

Strategy copies108 bytes once in Plus at`023D619A`, none in Normal. The delta is
offset102, last Pokémon/move slot2 with zero-based slots:325→247, PP20→15.
All24 move loads at`02073A2C` must reach the real setter chain. The constructor
restores its original seed at`02073A90`, frees108/236B at the original callers
and returns with SP/R4–R11 intact. The separate post-return GetSeed API is an
observation, not a substitute for proof of the actual restoration call/store.

Capsule's native caller requires handle185/member0/offset312/size24, LR`02072A77`
and destinationSP+8 within the bounded stack. This one profile adds that exact
SDK boundary; the trainer21 model remains unchanged. Heap/name/raw archive/FS
operations remain explicit models. The opaque32B NARC token is not a native
84B NARC allocation or evidence of recovered game memory. Native setters, RNG,
CreateMon, PartyAdd and the constructor itself execute installed instructions.

## I metodi e gli strumenti da usare

Install the [pinned dependencies](../../requirements.txt). From repository root,
run the existing [constructor verifier](../../features/trainer-strategy/tools/attribuisci_costruttore.py)
with the explicit profile and fresh private output:

```sh
python source/features/trainer-strategy/tools/attribuisci_costruttore.py \
  --trainer 31 --rom /private-inputs/r4-EN.nds --language EN \
  --objects /private-results/rematch-EN-build \
  --strategy-object /private-results/consumer-EN-build/teams.o \
  --json /private-results/constructor31-EN.json.gz
```

Repeat with the IT input, IT object paths,`--language IT` and a new IT output.
The command authenticates sources/ELF/raw inputs, then runs four positive paths
(Normal/Plus and two seeds), two old-hook recipe baselines, two guards (SDK
volatile-register/NZCV poison and nonzero caller cookies), three counterproofs
and two functional OFF comparisons. Guard and counter results are checked
against their premises, not only against a final packet. Normal/Plus use the
same actual constructor API. A3M-instruction/512B-stack budget bounds each run.

For the CPU-free incremental comparison, use
[the resource reader](../../features/trainer-strategy/tools/rileggi_provenienza.py).
Input identities and preparation are in the
[rematch lineage case](rematch-source-rom-1.3.2.md); no historical image is
substituted by a current input or a zero-filled missing range:

```sh
python source/features/trainer-strategy/tools/rileggi_provenienza.py \
  --trainer 31 --language EN --rom /private-inputs/r4-EN.nds \
  --retail /private-inputs/retail-EN.nds \
  --base /private-inputs/base11-EN.nds --v4 /private-inputs/v4-EN.nds \
  --json /private-results/lineage31-EN.json
```

Repeat with IT. The reader authenticates all four complete images, reads actual
header/party members and compares content separately from physical relocation.
Compressed retail/base ARM9 uses decoded logical sections; it does not invent a
linear physical offset. Current/v4 data also receives independent raw readback.

Replay both private receipts against fresh exact input readback without
repeating guest execution:

```sh
SGP_R4_ROM_DIR=/private-inputs \
SGP_REMATCH_OBJECTS_DIR=/private-results/rematch-EN-build \
SGP_STRATEGY_OBJECT=/private-results/consumer-EN-build/teams.o \
SGP_CONSTRUCTOR_REPORT_DIR=/private-results \
SGP_CONSTRUCTOR_REPORT_NOME='constructor31-%s.json.gz' \
SGP_CONSTRUCTOR_TRAINER=31 \
python source/features/trainer-strategy/test/test_constructor_attribution.py
```

ROM names default to`r4-EN.nds`/`r4-IT.nds`;`SGP_R4_ROM_NOME` overrides the
`%s` pattern. The project objects are identical across these two inputs. Omit
the trainer environment variable and CLI option to retain the trainer21 default.
Historical captures retain their original producer source hashes. Extending
the verifier does not rewrite capture provenance. Replay reattests unchanged
parent tools and the current raw/ELF proof.

Success requires full six-packet source semantics, CRC/flags, actual helper
order and return ABI, resource hashes, frozen unrelated RAM, guarded allocations,
closed handles, single strategy copy, original seed and entire old-hook delta.
Tests reject forged/missing evidence, wrong profile/class byte/capsule slice,
an additional valid-checksum325→247 rewrite, OFF proof forgery and code/data
drift. Receipt replay is distinct from fresh CPU acquisition.

Both exact languages passed the11 observed paths and two OFF comparisons.
The EN/IT acquisition took83.251/83.592s, with maximum OS RSS252903424/257228800B;
the largest guest count was1053093 instructions, stack512B. These are bounded
host observations, not game performance measurements. The trainer21 refactor
regression reproduced its entire earlier producer receipt, adding only explicit
trainer21 metadata. The earlier producer source hash and receipts remain intact.

The result establishes reconstructed binary correspondence for project-owned
strategy/rematch bytes, documented inherited provenance and targeted native
semantic equivalence on these fixtures. Activation is observed inside the
initialized API paths. Natural activation, other trainer IDs/formats, original
native compilation, SDK internals, save compatibility, hardware and timing
remain separate. No gameplay correction, speedup or memory saving is claimed.
