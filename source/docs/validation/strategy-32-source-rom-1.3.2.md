# Trainer32: a strategy edit in the second Pokémon

This case qualifies trainer32 from the actual native constructor entry through
six Pokémon, strategy/move setters, PartyAdd, frees, original RNG restoration
and return. The target is the second Pokémon, move slot0; the final Pokémon
must remain identical to the old-hook recipe baseline. API input state remains
initialized, with no copied Mon or post-entry frame fixture.

## Cosa farebbe un professionista di alto livello che non sto chiedendo

Extend the [trainer31 method](strategy-31-source-rom-1.3.2.md) only after checking
the new class, PID carry, IVs, levels, capsule slice and target position against
raw inputs. A previous last-member edit must not silently become a rule for
every trainer. Independently review addresses, callers, ABI and counterproofs.

Compare all six complete packets against the declared old-hook RAM recipe.
Normal must be identical throughout. Plus permits only329→156 and PP5→10 in
the second Pokémon's128-byte plaintext; its header and100-byte party tail,
and the other five236-byte packets, remain identical. A valid-checksum wrong
edit of the final Pokémon must fail. Final party equality alone does not prove
original seed restoration, closed allocations or the actual setter argument.

The standalone packet comparator now requires six236-byte packets on both
sides. Review exposed that a shorter vector or equal empty/short packets could
otherwise pass a zipped comparison. The full constructor analyzer already
validated every packet before comparison; its earlier results remain within
their documented coverage. Dedicated negative tests cover both standalone
dimensions, while preserving historical capture identities.

## Il materiale più grezzo da cui partire

Use your own exact r4 EN/IT images and retained project ELF objects from the
[constructor foundation](strategy-constructor-source-rom-1.3.2.md#il-materiale-più-grezzo-da-cui-partire):
EN152786844B SHA-256
`2e30d6960bb059615fca7527700d86f8282e82ccbe99bf62e22f027453dc3d3d`,
IT159029760B SHA-256
`13ebac02bdea3036511773587e6603ce6834e25f4b13d1a4662c3e954bfd5d4a`.
Full identity establishes the required language/revision. ROMs, raw members and
receipts stay private. The [rematch lineage case](rematch-source-rom-1.3.2.md)
identifies the exact retail/base1.1/v4 inputs for incremental comparison.

The [installer](../../sgp13/teams.py),
[strategy owner](../../features/trainer-strategy/README.md) and
[consumer reconstruction](rematch-consumer-source-rom-1.3.2.md) give sources,
toolchain identity/flags, linking, insertion and independent ELF/raw readback.
The580B strategy/config192B plus padding to512B/full2048B owner are reattested;
no compiler is invoked here. Inherited Plus code/table and HGSS native code
remain distinct from reconstructed project code. Their original objects and
toolchains are not recovered by semantic correspondence.

NARC55/member32 specifies type3/count6/class73. NARC56/member32 is108B, SHA-256
`03df312faca35cdb867513503effa947e05c1a0649899b1a944c36893140b812`.
The [public strategy specification](../../sgp13/data/strategic-teams.json)
changes only offset26: member slot1/move slot0,329→156. Raw NARC11 records
supply PP5/10, independently of the observed setter output.

Species are460,87,131,478,362,473; all IVs are31. Override bytes0,0,0,0,32,32
carry PID low byte`88,88,88,88,89,89`. The native class flag is0 at`020FFBD9`,
physical`00103BD9` in these r4 inputs, bound to the table pointer at`02073600`.
Normal levels42,43,43,42,42,44 become Plus46,47,47,46,46,48 from maximum44,
anchor48 and cap100. Item IDs are0,150,158,0,0,214. Female-only species478
exercises an already qualified native gender branch; no trace-derived code
admission is added.

Only the last Pokémon uses capsule24: NARC185/member0[552:576],24B, SHA-256
`87a2ba4d70a7135a24e2ef3d854a01e2317259d471c0cc5cbc1dc0b9f904f8da`.
Resource receipts retain independent FAT/FNT/NARC locations, sizes and hashes
for personal, growth, names, learnsets, moves and seals. Extracted game data is
not included in the repository.

Incremental readback in both languages finds a56B retail party member, SHA-256
`f88f3364330478ba945dfa8e7ff50300e6353a1e7f22c409bb1b1e3b069dd57b`.
Base1.1 already has the108B member pinned above, unchanged through v4/r4.
The expanded roster is inherited;329→156 is the Plus RAM edit. Matching these
intervals does not recover the original author's team-generation recipe.
The capsule slice's physical offset is`045D8464` in both exact r4 inputs.

### Native caller, state and resource boundaries

The [same native flow/addresses](strategy-constructor-source-rom-1.3.2.md#native-flow-abi-and-byte-locations)
start at`02073604`. The prefix allocates108/236B, reads trainer32, loads/unloads
inert rematch overlay126 and reaches`0207363E`. The same UC/RAM continues:
phase bookkeeping must leave registers and4MiB RAM unchanged. The guest owns
the152B constructor frame, creates all six Mon records and calls strategy at
the real type3 site`02073A0C`. Plus copies108B exactly once at`023D619A`;
Normal does not copy. All24 move loads at`02073A2C` reach their native setters.

The instruction qualification remains2993 PCs/92 readonly ranges, with only
the selected class73 byte added to the inherited finite map. ARM9 autoload,
overlay compression, pools, permutation/nature tables, veneers and data/code
mapping retain their independent checks. A previously qualified function is
not permission to admit an unknown executed address.

The capsule SDK boundary is limited to handle185/member0/offset552/length24,
LR`02072A77`, destinationSP+8 and the bounded stack. Heap/name/archive/FS remain
explicit models; native setters, RNG, CreateMon and PartyAdd execute installed
instructions. The opaque NARC token does not establish native SDK layout or
memory savings. The final free108/236, actual native seed restoration and
constructor return precede a separately recorded GetSeed observation. SP and
R4–R11, handles, allocation canaries and unrelated RAM must remain valid.

## I metodi e gli strumenti da usare

Install the [pinned dependencies](../../requirements.txt). From repository root:

```sh
python source/features/trainer-strategy/tools/attribuisci_costruttore.py \
  --trainer 32 --rom /private-inputs/r4-EN.nds --language EN \
  --objects /private-results/rematch-EN-build \
  --strategy-object /private-results/consumer-EN-build/teams.o \
  --json /private-results/constructor32-EN.json.gz
```

Repeat with IT paths and`--language IT`. Outputs must be fresh and outside the
source and retained object directories. The finite profiles21/31/32 are explicit;
the default remains21. Eleven observed paths per language comprise four
positives (two modes/two seeds), two old-hook RAM recipe baselines, two ABI/SDK
guards and three counterproofs. Two additional functional OFF comparisons bind
all packets, seed, caller return and SDK events. Each path is bounded to3M
instructions/512B stack. No source patch is installed into the input ROM.

The historical variant name`wrong_last_move` is retained for receipt continuity.
For32 its register counter changes the **second** Pokémon's real move-slot0
argument156→329 at`02073A32`, with the genuinely edited buffer unchanged.
Same-party wrong-seed and missing-free counterproofs remain separate checks.

Use the [CPU-free lineage reader](../../features/trainer-strategy/tools/rileggi_provenienza.py)
with`--trainer 32` and the four exact inputs as described in the
[trainer31 commands](strategy-31-source-rom-1.3.2.md#i-metodi-e-gli-strumenti-da-usare).
Compare member content independently of relocation; compressed retail/base
ARM9 uses decoded logical sections, with raw current/v4 crosschecks. Retail IT's
native class address remains unattributed here rather than aliasing the EN one.

Replay fresh input proofs and private receipts without repeating guest work:

```sh
SGP_R4_ROM_DIR=/private-inputs \
SGP_REMATCH_OBJECTS_DIR=/private-results/rematch-EN-build \
SGP_STRATEGY_OBJECT=/private-results/consumer-EN-build/teams.o \
SGP_CONSTRUCTOR_REPORT_DIR=/private-results \
SGP_CONSTRUCTOR_REPORT_NOME='constructor32-%s.json.gz' \
SGP_CONSTRUCTOR_TRAINER=32 \
python source/features/trainer-strategy/test/test_constructor_attribution.py
```

Default ROM names are`r4-EN.nds`/`r4-IT.nds`;`SGP_R4_ROM_NOME` overrides that
pattern. The retained project objects match across languages. Replay preserves
the capture's recorded source SHA and checks unchanged parent sources. A new
producer regression also checks the entire earlier trainer31 receipt after the
capsule boundary extension; it does not rewrite the historical receipt.

Success requires complete source-derived semantics, CRC/flags, PID/OTID/RNG,
level/stats/moves/PP/capsule, helper order/ABI, single copy, resource hashes,
original seed, closed lifetime, full-packet delta and functional OFF neutrality.
Tests also reject wrong target packets with valid checksums, profile/class/
capsule drift, missing evidence, truncated packet vectors, invalid widths and
forged OFF proofs. Reconstructed project bytes, documented inherited provenance,
targeted native semantics and initialized activation are distinct results.
Natural encounters, other IDs/formats, SDK internals, original native compilation,
SAVE/device coverage and game performance remain separate questions.

Both languages passed the11 observed paths and two OFF comparisons. EN/IT
acquisition took91.145/92.434s with OS maximum RSS248397824/252280832B;
the largest guest count was1144865 instructions, stack512B. Each positive
exercised438 class RNG draws and12 OTID draws; the source oracle retains
anti-shiny retry logic rather than treating450 as a universal count.
Fourteen replay methods passed without skips for each of profiles21,31,32.
The new capsule observer also reproduced the entire previous trainer31 positive
receipt. These are bounded host verification results, not performance claims.
