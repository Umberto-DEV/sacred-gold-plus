# Trainer244: proving the zero-capsule path

Trainer244's six native creations use no ball capsules. This case follows
actual constructor entry through strategy, move setters, PartyAdd, frees,
original seed restoration and return, while proving the absence of capsule
services. API input state remains initialized; no copied Mon or body-frame
handoff is used. Plus changes only the first Pokémon's second move and PP.

## Cosa farebbe un professionista di alto livello che non sto chiedendo

An absent resource needs its own proof. Derive all six capsule IDs from raw
trainer data, observe six native helper calls returning FALSE, require the
zero-return instructions and reject any capsule setter or NARC capsule service.
Do not fabricate a capsule slice at offset−24 or treat an empty hash as a fixture.

Compare all six complete packets with the declared old-hook RAM recipe.
Normal must be identical. Plus allows63→127 and PP5→15 only in member0/move1;
five other236B packets, target header/100B tail and all other128B plaintext
remain identical. The duplicate species149 at slots3/5 have distinct levels;
preserve their complete outputs rather than comparing species lists alone.

Use same-party wrong-seed and missing-free counterproofs, a genuine edited
buffer with one wrong native setter argument, and observer OFF comparison.
Review source, raw input, ABI and absence evidence independently. An empty
capsule-call list is valid here; a test that replaces it with itself is no test.

## Il materiale più grezzo da cui partire

Use your own exact r4 images and retained project objects from the
[constructor foundation](strategy-constructor-source-rom-1.3.2.md#il-materiale-più-grezzo-da-cui-partire):
EN152786844B SHA-256
`2e30d6960bb059615fca7527700d86f8282e82ccbe99bf62e22f027453dc3d3d`,
IT159029760B SHA-256
`13ebac02bdea3036511773587e6603ce6834e25f4b13d1a4662c3e954bfd5d4a`.
Full identity establishes language/revision. ROMs, raw members and execution
receipts stay private. Exact retail/base1.1/v4 identities and preparation are
in the [lineage case](rematch-source-rom-1.3.2.md).

The [installer](../../sgp13/teams.py),
[owner](../../features/trainer-strategy/README.md) and
[ELF reconstruction](rematch-consumer-source-rom-1.3.2.md) give compilation,
linking, toolchain identity/flags, insertion, padding and independent readback.
The580B strategy/config192B/padding512B/full2048B owner and rematch dependencies
are reattested here without invoking a compiler. Archived Plus source
correspondence and native HGSS semantics remain distinct from original
compiler/object reconstruction, which is unavailable.

NARC55/member244 specifies type3/count6/class86. NARC56/member244 is108B,
SHA-256`630de408577b0c708617171db42a4d68d49069ed03a376ea49819f9dafb0abf4`.
The [strategy specification](../../sgp13/data/strategic-teams.json) changes
offset10, first Pokémon/move slot1,63→127. Independent raw NARC11 supplies
PP5→15. Species are130,445,142,149,6,149; IV31 and override0 throughout yield
PID low byte`88` for all six. Class86's flag0 is at`020FFBE6`, physical
`00103BE6`, with the native table pointer bound at`02073600`.

Normal levels56,54,54,56,57,60 become Plus63,61,61,63,64,67 from maximum60,
anchor67 and cap100. Only the last Pokémon has item158. **Every capsule ID is0.**
Independent FAT/FNT/NARC readback records personal/growth/name/learnset/move
locations, hashes and sizes against the bench's ndspy view. NARC185's layout
may be inspected as part of input qualification; no member185 is reported as
used by this guest path. The resource summary derives members from actual
service events instead of adding capsule member0 unconditionally.

Both retail party members are also108B, SHA-256
`de6b09b527da2b5bd617b500b1bc477df170d4d872e39d2fcb970a4590fb4c1f`.
Their header content matches base1.1/v4/r4, but their party content differs.
The base1.1 member already has the current630d…abf4 hash, unchanged through
v4/r4. Thus size/header equality alone would miss the inherited party change;
the63→127 substitution is a further Plus RAM edit. Original authoring of the
base roster is not recovered by these interval comparisons.

### Native early return and ABI

The [same constructor address map](strategy-constructor-source-rom-1.3.2.md#native-flow-abi-and-byte-locations)
starts at`02073604`, with a guest-produced152B frame and all six236B records.
The bookkeeping transition at`0207363E` must preserve registers and4MiB RAM.
Actual strategy entry is the type3 site`02073A0C`; Plus copies108B once at
`023D619A`, Normal does not copy. All24 native move loads/setters and six
PartyAdd returns must agree with the source-derived packets. Rematch overlay126
retains installed activation0.

Each `SetTrMonCapsule` call at`02072A44` receives R0/R1/R2=`0,Mon,11`, LR
`02073A4F`, returns R0=0 with saved-register/SP ABI intact, and takes the existing
zero-return path. Required executed PCs are`02072A50/02072A52/02072A54`:
restore32B stack, setR0=0, pop saved registers/PC. Interval[02072A50,02072A56),6B,
SHA-256`e1f191ad802cc5ea54b396a7ee9df0d39d1abbbe75b7b06ac47010d2bd8e1650`.
These instructions were already statically qualified. The profile's map remains
2993 PCs/92 readonly ranges, with no new code or SDK admission.

The source counterpart is `SetTrMonCapsule` in HGSS
[pokemon.c](https://github.com/ctrl-cheeb-del/pokeheartgold/blob/cb614ad23449d5852b40321dc409c4143872b35c/src/pokemon.c)
at reference commit`cb614ad23449d5852b40321dc409c4143872b35c`: capsule0 returns
FALSE before NARC_New. Require no capsule data setters and no NARC_New,
NARC_ReadFromMember or NARC_Delete events, plus zero capsule flag/seals in all
decoded native outputs. This is absence in these exercised paths, not proof
that the game never uses the resource elsewhere.

ARM9 autoload, overlay compression, pools, veneers and data/code separation
retain their independent checks. Other SDK heap/name/archive/FS boundaries
remain explicit models; native creation, RNG, moves, PartyAdd, frees and return
execute installed instructions. Initial SetSeed, one full constructor call and
the separate post-return GetSeed are recorded as three outer APIs. The actual
restore call/store and frees must precede the observing getter.

## I metodi e gli strumenti da usare

Install the [pinned dependencies](../../requirements.txt). From repository root:

```sh
python source/features/trainer-strategy/tools/attribuisci_costruttore.py \
  --trainer 244 --rom /private-inputs/r4-EN.nds --language EN \
  --objects /private-results/rematch-EN-build \
  --strategy-object /private-results/consumer-EN-build/teams.o \
  --json /private-results/constructor244-EN.json.gz
```

Repeat with IT input/object paths and`--language IT`, with fresh private output.
The default remains21;244 is a separately admitted finite profile. Eleven
observed paths per language cover four positives (two modes/two seeds), two
declared old-hook RAM recipe baselines, two guards and three counterproofs.
Two functional OFF comparisons bind packets, seed, caller state and SDK events.
The old-hook baseline changes four authenticated pre-entry RAM BLs and does
not establish historical whole-ROM equivalence. Each path is bounded to3M
instructions/512B stack.

The legacy name`wrong_last_move` targets the **first** Pokémon's slot1 on244:
the real`02073A32` caller passes63 instead of127 with the authentic edited
buffer unchanged. Other counterproofs preserve the correct party while breaking
original-seed restoration or leaving108B live. Guard nonzero caller cookies,
SDK volatile registers/NZCV, canaries, frozen unrelated RAM and closed handles.

Use the [CPU-free lineage reader](../../features/trainer-strategy/tools/rileggi_provenienza.py)
with`--trainer 244` and your four exact inputs as in the
[trainer31 commands](strategy-31-source-rom-1.3.2.md#i-metodi-e-gli-strumenti-da-usare).
It separates content from relocation and compressed logical ARM9 sections from
raw current/v4 offsets; retail IT's native class address remains unattributed.
Replay receipts with fresh input/ELF proofs without guest reacquisition:

```sh
SGP_R4_ROM_DIR=/private-inputs \
SGP_REMATCH_OBJECTS_DIR=/private-results/rematch-EN-build \
SGP_STRATEGY_OBJECT=/private-results/consumer-EN-build/teams.o \
SGP_CONSTRUCTOR_REPORT_DIR=/private-results \
SGP_CONSTRUCTOR_REPORT_NOME='constructor244-%s.json.gz' \
SGP_CONSTRUCTOR_TRAINER=244 \
python source/features/trainer-strategy/test/test_constructor_attribution.py
```

ROM names default to`r4-EN.nds`/`r4-IT.nds`;`SGP_R4_ROM_NOME` overrides that
pattern. Project objects match across languages. Historical captures/source
hashes are retained; a fresh trainer34 producer regression checks its entire
preceding receipt after the optional-capsule oracle change.

Success requires complete source-derived packet semantics/CRC/flags, native
helper order/ABI, actual zero-return PCs and FALSE results, absence of capsule
setters/services, exact move/PP, whole-packet baseline, original seed, closed
lifetime and functional OFF neutrality. Tests inject capsule setters/services
or a TRUE result, remove a required return PC and modify a non-target packet
with a valid checksum. They also retain profile/code/resource drift, incomplete
packet and forged OFF-proof counterchecks.

Project binary correspondence, documented inherited provenance, targeted native
semantics and initialized activation are separate results. Natural battle,
other profiles/formats, original native compilation, SDK internals, SAVE/device
compatibility and timing remain outside this case. No resource reclamation,
speedup or gameplay correction is claimed.

Both languages passed11 observed paths and two functional OFF comparisons.
EN/IT acquisition took94.107/94.191s with OS maximum RSS263798784/268222464B;
the largest guest count was1161854 instructions, stack512B. Each positive
exercised516 class RNG draws and12 OTID draws; anti-shiny retries remain in
the independent oracle rather than treating528 as universal. Fifteen replay
methods passed without skips for all six admitted profiles. These are bounded
host verification results and establish no hardware or timing improvement.
