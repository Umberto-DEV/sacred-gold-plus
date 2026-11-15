# Trainer34: the first Pokémon and a male-only branch

This finite profile follows trainer34 from actual native constructor entry
through six Pokémon, strategy/setters/PartyAdd, frees, original seed restoration
and return. Its edit belongs to the **first** Pokémon. API input state remains
initialized; no copied Mon or post-entry frame/context bridge is used.

## Cosa farebbe un professionista di alto livello che non sto chiedendo

Reuse the [constructor method](strategy-33-source-rom-1.3.2.md) while qualifying
only the new paths needed by34. Its male-only species and capsule slice differ
from preceding profiles. Preserve Normal's six whole packets; Plus may change
only first-member move0 and PP0. The other five236B packets, target header and
100B party tail, and all other128B plaintext remain identical to the old-hook
RAM recipe baseline. Verify actual setter arguments, persistent PID state,
resources, saved registers, lifetime and original seed independently.

Keep static admission separate from observed activation. New instruction starts
must match raw hashes and Capstone decoding, and must appear in the executed-PC
receipt. A calibration that removes one such PC while preserving final fields
must fail. Earlier genuine captures retain their source identities and pass the
stronger readback; their executed branch evidence is not replaced by a map.

## Il materiale più grezzo da cui partire

Use your own exact inputs and retained project objects prepared in the
[constructor foundation](strategy-constructor-source-rom-1.3.2.md#il-materiale-più-grezzo-da-cui-partire).
Required r4 images are EN152786844B SHA-256
`2e30d6960bb059615fca7527700d86f8282e82ccbe99bf62e22f027453dc3d3d`,
and IT159029760B SHA-256
`13ebac02bdea3036511773587e6603ce6834e25f4b13d1a4662c3e954bfd5d4a`.
Full identity determines revision/language. Keep ROMs, extracted members,
raw traces and saves private. Exact retail/base1.1/v4 requirements are in the
[incremental lineage case](rematch-source-rom-1.3.2.md).

The [installer](../../sgp13/teams.py),
[owner](../../features/trainer-strategy/README.md) and
[ELF reconstruction](rematch-consumer-source-rom-1.3.2.md) give sources,
compiler identity/flags, linking, insertion, padding and independent readback.
This case reattests project strategy580B/config192B plus padding to512B/full
2048B owner and rematch dependencies, invoking no compiler. Native HGSS and
inherited Plus level code/table remain distinct provenance categories. Archived
Plus source correspondence is available; original MW/Plus compiler/object
reconstruction remains unavailable and is not replaced by these semantics.

NARC55/member34 specifies type3/count6/class75. NARC56/member34 is108B, SHA-256
`4bfe62cfddc19cc603131926291df285ad7588ab8f0398e460d52fa583ffa155`.
The [strategy specification](../../sgp13/data/strategic-teams.json) changes
offset8, first Pokémon/move slot0:99→280, with PP20→15 from raw NARC11.

Species are57,286,106,107,297,62; IVs are31 throughout. Override bytes
32,0,32,32,0,0 change the first PID low byte`88`→`89`, which persists for all
six members. Class75's flag0 is at`020FFBDB`, physical`00103BDB`, bound to the
table pointer at`02073600`. Normal levels34,33,34,34,33,35 become
Plus37,36,37,37,36,38 from maximum35/anchor38 and cap100. Only the last Pokémon
has item158 and capsule8. Species106/107 have raw gender ratio0.

Capsule8 is NARC185/member0[168:192],24B, physical`045D82E4`, SHA-256
`c2f79c344decafc3d8735a576f59448acfdd1cc469a9b501b86f7c639a6b2016`.
The model admits precisely handle185/member0/offset168/length24,
LR`02072A77`, destinationSP+8 and the bounded stack for34. Other profiles keep
their own admitted slices. Independent FAT/FNT/NARC and ndspy readback records
actual resource offsets/sizes/hashes, including personal/growth/names/moves.
No extracted data is distributed.

Both retail inputs have a36B trainer34 party member, SHA-256
`028c1c346e1522e360783c93c97f6add37a7af9ace8eda415b2cf4a48dc485e1`.
Base1.1 already contains the108B member pinned above; its content and header
remain identical through v4/r4. The roster is inherited, while99→280 is the
guarded Plus RAM edit. Matching these intervals does not recover their original
authoring recipe.

### Instructions, caller ABI and state

The [native flow and address map](strategy-constructor-source-rom-1.3.2.md#native-flow-abi-and-byte-locations)
start at`02073604`. The guest produces its152B frame and all six236B records;
phase bookkeeping at`0207363E` is checked neutral over registers and4MiB RAM.
Strategy is entered from the real type3 BL`02073A0C`, with one108B copy at
`023D619A` in Plus and none in Normal. All24 native move loads/setters, six
PartyAdd returns, original108/236B frees, saved-seed restore and caller return
must be present. The separate post-return GetSeed is an observing API.

Only two additional Thumb PCs are needed: `02070006` (`movs r0,#0`) and
`02070008` (`pop {r4,pc}`), interval[02070006,0207000A),4B, SHA-256
`78e48386a8c4b5d6db45a5d1f5db617019b0d50a52ee01c8c9ccacdd129eb2f5`.
They implement the source-known male-only gender return. Both raw input images
and decoded mappings must agree. Profile34 qualifies2995 PCs/92 readonly ranges;
the16 extra PCs specific to33 are not admitted into34 merely because they were
previously verified. ARM9 autoload, overlay compression, pools, veneers and
data/code separation retain the inherited independent checks.

Native correspondence uses HGSS reference
`cb614ad23449d5852b40321dc409c4143872b35c`, particularly
[pokemon.c](https://github.com/ctrl-cheeb-del/pokeheartgold/blob/cb614ad23449d5852b40321dc409c4143872b35c/src/pokemon.c)
and the constructor's
[trainer_data.c](https://github.com/ctrl-cheeb-del/pokeheartgold/blob/cb614ad23449d5852b40321dc409c4143872b35c/src/trainer_data.c).
This establishes finite semantic correspondence, not original native binary
recompilation. The installed inert rematch overlay retains activation0.

## I metodi e gli strumenti da usare

Install the [pinned dependencies](../../requirements.txt). From repository root:

```sh
python source/features/trainer-strategy/tools/attribuisci_costruttore.py \
  --trainer 34 --rom /private-inputs/r4-EN.nds --language EN \
  --objects /private-results/rematch-EN-build \
  --strategy-object /private-results/consumer-EN-build/teams.o \
  --json /private-results/constructor34-EN.json.gz
```

Repeat with IT paths and`--language IT`, using fresh private outputs. The default
remains21, with finite profiles21/31/32/33/34. Eleven observed paths per language
cover four positives (two modes/two seeds), two declared old-hook RAM recipe
baselines, two ABI/SDK guards and three counterproofs; two functional OFF
comparisons bind packets, caller state, seed and SDK events. The old-hook
baseline changes four authenticated pre-entry RAM BLs, not the input ROM, and
does not claim historical whole-ROM equivalence.

The legacy name`wrong_last_move` remains for receipt continuity; on34 it changes
the **first** member's move-slot0 argument280→99 at the real`02073A32` caller,
with the genuine edited buffer unchanged. Same-party wrong-seed and missing-free
cases test separate obligations. Guest paths are bounded to3M instructions and
512B stack. Heap/name/raw archive/FS remain explicit SDK models, while native
CreateMon, RNG, setters, PartyAdd and constructor execute installed instructions.

Use the [CPU-free lineage reader](../../features/trainer-strategy/tools/rileggi_provenienza.py)
with`--trainer 34` and the four exact images as in the
[trainer31 commands](strategy-31-source-rom-1.3.2.md#i-metodi-e-gli-strumenti-da-usare).
It separates member content from physical relocation, compressed ARM9 logical
sections from raw current/v4 readback, and the unattributed retail IT class
address. Replay private captures with fresh raw/ELF proofs without guest work:

```sh
SGP_R4_ROM_DIR=/private-inputs \
SGP_REMATCH_OBJECTS_DIR=/private-results/rematch-EN-build \
SGP_STRATEGY_OBJECT=/private-results/consumer-EN-build/teams.o \
SGP_CONSTRUCTOR_REPORT_DIR=/private-results \
SGP_CONSTRUCTOR_REPORT_NOME='constructor34-%s.json.gz' \
SGP_CONSTRUCTOR_TRAINER=34 \
python source/features/trainer-strategy/test/test_constructor_attribution.py
```

ROM names default to`r4-EN.nds`/`r4-IT.nds`;`SGP_R4_ROM_NOME` overrides that
pattern. Project objects are identical across these languages. A fresh producer
regression also compares the entire earlier trainer33 receipt after extending
the capsule observer. Historical capture/source hashes remain intact.

Success requires source-derived six-Mon semantics/CRC/flags, PID carry, actual
helper and setter ABI/order, all resources, frozen unrelated RAM, original seed,
closed lifetime, whole-packet delta and functional OFF neutrality. Tests reject
wrong last-member slot0 (move ID3→280) with a valid checksum, wrong profile/
capsule/code, missing executed profile PCs, incomplete packets and forged OFF
proofs. Static code admission alone is insufficient evidence of execution.

Project binary correspondence, documented inherited provenance, targeted native
semantics and initialized activation are separate conclusions. Natural battle,
other profiles/formats, original native compilation, SDK internals, SAVE/device
compatibility and timing remain outside this case.

Both exact languages passed11 observed paths and two functional OFF comparisons.
EN/IT acquisition took88.465/91.416s with OS maximum RSS248758272/252788736B;
the largest guest count was1097136 instructions, stack512B. Positive paths
exercised450 class RNG draws and12 OTID draws; the independent oracle retains
anti-shiny retries rather than treating462 as universal. Fifteen replay methods
passed without skips for all five profiles. These bounded host observations
claim no speedup, SDK implementation coverage or hardware validation.
