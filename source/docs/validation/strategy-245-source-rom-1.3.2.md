# Trainer245: different move, unchanged PP

Trainer245 changes its last Pokémon's move2 from384 to94, while PP remains10.
This case follows actual constructor entry through six native Pokémon,
strategy/setters/PartyAdd, frees, original seed restoration and return. API
input state remains initialized; no copied Mon or post-entry frame bridge is
used. Identical PP alone cannot establish whether the move assignment ran.

## Cosa farebbe un professionista di alto livello che non sto chiedendo

Require actual setter arguments and complete packet comparison. Normal must
preserve six236B packets. Plus permits only the last member's move2 halfword;
PP10, every other128B plaintext field, target header/100B tail and five other
packets remain identical to the declared old-hook RAM recipe baseline. Other
party members already know94, so finding that ID somewhere in output is
insufficient attribution.

Use a wrong native setter argument94→384 with the genuine edited buffer:
the counterexample must retain PP10 yet fail move/packet validation. Keep
same-party wrong-seed and missing-free checks separate. Prove zero capsule
services as in the [trainer244 case](strategy-244-source-rom-1.3.2.md), and
qualify only the two genderless return instructions needed by this profile.
Independently review raw resources, addresses, ABI, calls and counterproofs.

## Il materiale più grezzo da cui partire

Use your own exact r4 images and retained project objects prepared in the
[constructor foundation](strategy-constructor-source-rom-1.3.2.md#il-materiale-più-grezzo-da-cui-partire):
EN152786844B SHA-256
`2e30d6960bb059615fca7527700d86f8282e82ccbe99bf62e22f027453dc3d3d`,
IT159029760B SHA-256
`13ebac02bdea3036511773587e6603ce6834e25f4b13d1a4662c3e954bfd5d4a`.
Full hashes establish revision/language. Keep ROMs, raw members and detailed
receipts private. Exact retail/base1.1/v4 identities and preparation are in
the [lineage case](rematch-source-rom-1.3.2.md).

The [installer](../../sgp13/teams.py),
[owner](../../features/trainer-strategy/README.md) and
[ELF reconstruction](rematch-consumer-source-rom-1.3.2.md) specify project
sources, toolchain/flags, linking, insertion, padding and independent readback.
The580B strategy/config192B/padding512B/full2048B owner and rematch dependencies
are reattested without invoking a compiler. Archived Plus source correspondence
and native semantics remain distinct from unavailable original compiler/object
reconstruction. The owned50B post-form repair retains its earlier attribution.

NARC55/member245 specifies type3/count6/class87. NARC56/member245 is108B,
SHA-256`957ae8872b6d64750e657c791508175d461fd7434beb2d77f6f73865e7971bf3`.
The [strategy specification](../../sgp13/data/strategic-teams.json) changes
offset102, member5/move2,384→94. Independent NARC11 records give PP10 for both.
Species are124,337,282,80,338,178. IV31/override0 throughout preserve PID low
byte`78`. Class87's flag1 is at`020FFBE7`, physical`00103BE7`, with the native
class-table pointer bound at`02073600`.

Normal levels53,52,55,54,52,55 become Plus59,58,61,60,58,61 from maximum55,
anchor61 and cap100. Only the last member has item158; all capsule IDs are0.
Species124 is female-only,337/338 genderless. Independent FAT/FNT/NARC and
ndspy readback retain personal/growth/name/learnset/move hashes, sizes and
physical locations. No member185 is reported as used by the guest, although
the verifier may inspect its input layout. No extracted game data is shipped.

Retail EN/IT have a92B member, full SHA-256
`e0e28e3b456493ce431fa8e003154d6a7809c981b5379bd59dc8a830be83a0af`.
Their type3/count5 header declares five18B records:90B, SHA-256
`d36e0f8c1a95bb189cc49b4f2f40466d5b8eb14515908e4109da43eb0b8909c1`.
The remaining two bytes are zero, SHA-256
`96a296d224f285c67bee93c30f8a309157f0daa35dc5b87e410b78630a09cfc7`.
Reader v2 reports these intervals separately. Four-byte alignment is a padding
candidate, not recovered authoring provenance. Base1.1 already contains the
current108B six-record member and header, unchanged through v4/r4; the384→94
substitution is the later Plus RAM edit. Old lineage receipts remain intact.

### Source-derived defaults and actual calls

Raw learnset178 and `InitBoxMonMoveset` at the pinned HGSS reference
`cb614ad23449d5852b40321dc409c4143872b35c`
([pokemon.c](https://github.com/ctrl-cheeb-del/pokeheartgold/blob/cb614ad23449d5852b40321dc409c4143872b35c/src/pokemon.c))
derive four default moves by appending unknown moves through the current level,
dropping the oldest when full. Stop at the **first**`FFFF` terminator; filtering
out terminators would incorrectly admit trailing padding.

For Xatu178, the source/raw-derived defaults are`466,140,384,385` at level55 and
`140,384,385,94` at level61. These are inferences from source and raw data,
not observed RAM snapshots. At Plus's custom slot2 assignment, the inferred
prior slot value385 and requested94 both have10 PP. Existing actual caller
traces and final packet checks answer this finite question without another
probe: all24 custom move setters must execute, with the last four arguments
`466,140,94,385`. A PP-only comparison would miss the wrong move.

### Code admission, ABI and zero resources

The [same native flow/address map](strategy-constructor-source-rom-1.3.2.md#native-flow-abi-and-byte-locations)
starts at`02073604`, with a guest-produced152B frame and six236B records.
Phase bookkeeping at`0207363E` must leave registers and4MiB RAM unchanged.
Actual strategy entry is the type3 BL`02073A0C`, with one108B copy at`023D619A`
in Plus and none in Normal. Rematch overlay126 retains installed activation0.

Two extra Thumb PCs implement the genderless return: `0207000E` (`movs r0,#2`)
and`02070010` (`pop {r4,pc}`), interval[0207000E,02070012),4B, SHA-256
`512215349f12a0b3c1b5527cf3939457e9f8577aea66c2e6fbe4dee2a23f68da`.
Female-only return code is already in the base map. Profile245 qualifies
2995 PCs/92 readonly ranges and requires these two executed PCs plus the
three already admitted zero-capsule return PCs`02072A50/52/54`.

Static decoding must match the required starts **not already present in the
base map**. All five required starts must be qualified and observed. This
separates two new admissions from five activation obligations, retaining the
profile33/34 guards. Hashes, ISA/widths, overlap checks, raw ARM9 autoload,
overlay compression, pools, veneers and physical readback remain mandatory.

Six native `SetTrMonCapsule` calls receive`0,Mon,11`, return FALSE and preserve
SP/saved-register ABI. Require no capsule setters or NARC_New/Read/Delete
services, and zero capsule flags/seals. Other heap/name/archive/FS boundaries
remain explicit models. Native creation, RNG, move setters, PartyAdd, frees
and original seed restoration execute installed instructions. Three outer
APIs distinguish initial SetSeed, constructor through return and the separate
observing GetSeed; the latter cannot substitute for the actual restore store.

## I metodi e gli strumenti da usare

Install the [pinned dependencies](../../requirements.txt). From repository root:

```sh
python source/features/trainer-strategy/tools/attribuisci_costruttore.py \
  --trainer 245 --rom /private-inputs/r4-EN.nds --language EN \
  --objects /private-results/rematch-EN-build \
  --strategy-object /private-results/consumer-EN-build/teams.o \
  --json /private-results/constructor245-EN.json.gz
```

Repeat with IT input/object paths and`--language IT`, using fresh private output.
The default remains21; the finite domain is21/31/32/33/34/244/245. Eleven
observed paths per language cover four positives (two modes/two seeds), two
declared old-hook RAM recipe baselines, two guards and three counterproofs;
two functional OFF comparisons bind packets, seed, caller state and SDK events.
The four authenticated pre-entry old-hook RAM BLs do not alter the ROM and
do not claim historical whole-ROM equivalence. Each path is bounded to3M
instructions/512B stack.

The legacy name`wrong_last_move` selects member5/move2 on245. Its true
`02073A32` caller passes384 instead of94, keeping PP10 but changing the packet.
Same-party wrong-seed and108B-leak cases test separate obligations. Preserve
caller SP/R4–R11, nonzero cookies, volatile SDK/NZCV guard, canaries, frozen
unrelated RAM, closed handles and all six actual PartyAdd returns.

Use the [CPU-free lineage reader](../../features/trainer-strategy/tools/rileggi_provenienza.py)
with`--trainer 245` and the four exact inputs as in the
[trainer31 commands](strategy-31-source-rom-1.3.2.md#i-metodi-e-gli-strumenti-da-usare).
It separates content from relocation, compressed logical ARM9 sections from
raw current/v4 offsets and the unattributed retail IT class address. Replay
private receipts with fresh input/ELF proofs without guest reacquisition:

```sh
SGP_R4_ROM_DIR=/private-inputs \
SGP_REMATCH_OBJECTS_DIR=/private-results/rematch-EN-build \
SGP_STRATEGY_OBJECT=/private-results/consumer-EN-build/teams.o \
SGP_CONSTRUCTOR_REPORT_DIR=/private-results \
SGP_CONSTRUCTOR_REPORT_NOME='constructor245-%s.json.gz' \
SGP_CONSTRUCTOR_TRAINER=245 \
python source/features/trainer-strategy/test/test_constructor_attribution.py
```

Reader v2 additionally reports format/count/stride, declared record span/hash,
trailing span/hash and a bounded alignment candidate. An empty trailer has no
invented fixture hash. Synthetic tests distinguish short records, unknown
formats and nonzero/overlong tails. These metadata checks execute no guest code.

Default ROM names are`r4-EN.nds`/`r4-IT.nds`;`SGP_R4_ROM_NOME` overrides that
pattern. Project objects match across languages. Historical source/capture
hashes remain intact; a fresh trainer244 producer regression compares its
entire earlier receipt after the profile/code qualification extension.

Success requires full source-derived semantics/CRC/flags, actual move94 and
PP10, five unchanged packets, zero capsule services, all five required PCs,
helper ABI/order, resources, original seed, lifetime and OFF neutrality.
Tests reject a wrong move with unchanged PP, a valid-checksum wrong non-target
Slowbro slot3 (94→384, PP10), fake capsule services/TRUE results, missing PCs,
code/resource/profile drift, incomplete packets and forged OFF proofs.

Project binary correspondence, documented inherited provenance, targeted native
semantics and initialized activation are separate conclusions. Natural battle,
other profiles/formats, original native compilation, SDK internals, SAVE/device
compatibility and timing remain outside this case. No gameplay fix, speedup
or reclaimed memory is claimed.

Both exact languages passed11 observed paths and two functional OFF comparisons.
EN/IT acquisition took99.190/98.326s with OS maximum RSS264273920/268976128B;
the largest guest count was1206903 instructions, stack512B. Positives exercised
522 class RNG draws and12 OTID draws, with anti-shiny retry semantics retained
in the independent oracle. Sixteen replay methods passed without skips for
all seven profiles. Reader v2 also passed14 profile/language comparisons against
preserved lineage evidence: old full-member identities/offsets/comparisons remain
equal while declared records and trailers are added. These bounded host results
do not establish hardware or game performance improvements.
