# Native trainer messages inside the complete trainer31 caller

This verifier joins the [native message producer](trainer-message-source-rom-1.3.2.md)
to the [complete trainer31 caller](trainer-caller-source-rom-1.3.2.md) in one
CPU/RAM context. Message creation/decryption/copy/destruction and all six native
Pokémon execute between the actual caller entry and return. Heap/NARC services,
constructor SDK/overlay filesystem and species-name production remain explicit
models. Initialized API execution does not establish natural encounter activation.

## Cosa farebbe un professionista di alto livello che non sto chiedendo

Prove composition, rather than treating two independent API tests as one run.
Verify that the bench has not overwritten the message bodies with high-level
stubs. Preserve nested SP, real saved registers, native allocations and the
message ownership that spans the constructor. A correct name and complete party
do not prove resource closure. Check actual callsites, native writes and causal
counterproofs, with independent raw/source review.

## Il materiale più grezzo da cui partire

Use your own exact Plus1.3.2 r4 images:

| Language | Bytes | SHA-256 |
| --- | ---: | --- |
| EN | 152786844 | `2e30d6960bb059615fca7527700d86f8282e82ccbe99bf62e22f027453dc3d3d` |
| IT | 159029760 | `13ebac02bdea3036511773587e6603ce6834e25f4b13d1a4662c3e954bfd5d4a` |

Whole-image pins identify the input; internal headers alone are insufficient.
The linked parent cases document retail→inherited Plus→V4→r4 byte lineage,
source correspondence, independent ARM9/archive readback and input preparation.
This composition needs only the final exact image and retained project objects;
it does not recompile native HGSS or produce another ROM.

Retain `rematch-variants.o`, `rematch-stub.o` and `teams.o` using the build
commands and authenticated compiler/flags in the
[rematch case](rematch-source-rom-1.3.2.md) and
[constructor case](strategy-constructor-source-rom-1.3.2.md).
Their SHA-256 values are respectively
`cfc4dce49574df18f3064fb66c2f8d75b66f5e6ed63e26d36e97893e2168817a`,
`43848467a67b11f1fec275a63e89f861c8641f325c86af38df03320a10d7c68a`,
`e2429f61c7ee16071d303f7ca55cbb1553508720c6fe97b77aead9ce56e499e1`.
The verifier authenticates ELF/relocations, source recipe and installed Plus
owner using the existing readers. Objects, ROMs and reports remain private.
No extracted game data, saves, BIOS or binary fixtures are distributed here.

Native reference commit is `cb614ad23449d5852b40321dc409c4143872b35c`.
The parent documents link `trainer_data.c`, `msgdata.c`, `pm_string.c`,
`filesystem.c` and their relevant headers. Original native MW and historical
Plus compiler/objects remain unavailable: source correspondence, retained Plus
binary reconstruction and installed-byte identity are separate conclusions.

`EnemyTrainerSet_Init` is ARM9 entry`020733C0`, physical`000773C0`.
It calls the five native message APIs at these real BL sites:

| Native API | Entry | Caller BL / return LR |
| --- | --- | --- |
| NewMsgDataFromNarc | `0200BAF8` | `020733D2` / `020733D7` |
| NewString_ReadMsgData | `0200BBA0` | `02073426` / `0207342B` |
| CopyStringToU16Array | `02026A68` | `02073430` / `02073435` |
| String_Delete | `02026380` | `02073436` / `0207343B` |
| DestroyMsgData | `0200BB44` | `02073462` / `02073467` |

The lazy body`0200B9F8`, String_New`02026354`, CopyN`02026A04` and ARM
memcpy`020E5AD8` run beneath them. For these uncompressed resident spans,
physical offset is `RAM - 02000000 + 4000`. Literal pools remain data;
independent raw/decoded-section reads and hashes precede execution.
Caller138 and message228 qualified starts share40 starts, giving326 distinct
starts in their union; constructor2993 is a separate overlapping domain.
Never add these totals as if all functions were disjoint.

The constructor BL`02073440` reaches`02073604` with LR`02073445`.
The four installed strategy-hook BLs, Plus owner`023D6000`, capsule/party/move
resources and six-Pokémon semantics remain those of the linked constructor
cases. Only trainer31/type3/count6, IDs[0,31,0,0], battleType1, heap11 and cap100
are admitted. Plus0 and Plus1 use the actual native calls and original seed
setter/getter. Other trainers, rival-class and multiple active IDs are excluded.

Message source is NARC27 `a/0/2/7`, bank729/member31. EN uses5 packed words,
IT6, including EOS; copied payload is10/12B. Header/MAT/payload are supplied
as three encrypted slices by the NARC read model; native instructions decrypt,
initialize object fields and copy. Full bank hashes, physical resource offsets,
source formulas and readback commands are in the native-message parent case.
The raw trainer header remains NARC55/member31,20B copied to a52B local object;
the remaining32B preserve their initial stack provenance.

The test heap is separate from the constructor arena. Native message allocations
are Msg12B at`02360020`, String`2*N+10` at`02360040`, temporary`2*N` at`02360068`;
the NARC handle`02360800` is opaque. These are declared synthetic heap assignments,
not installed allocation addresses or the real84B filesystem-object layout.
The constructor bump cursor remains`02200000` until its own first allocation.
All message objects have canaries; free poisons their bodies with`DD`.

Caller frame96B puts every message API at `INNER=outerSP-96`.
Message peak80B below INNER gives176B total; constructor512B below INNER gives
the existing608B bound. Message frames below INNER cannot overlap local Trainer
`[outerSP-76,outerSP-24)`, whose unused32B are above that boundary. Actual native
52B stores and copied name bytes verify this provenance, rather than assuming it.
String spare follows heap fill`C7`; unused destination bytes follow stack poison
`C7` or`39`. These are distinct inputs.

Native String/temp are already freed when the constructor starts. Its real R6
still contains String pointer`02360040`; preserving that register does not make
the object live. Msg and its handle remain live and unchanged across all six
Pokémon, then the caller suffix deletes the NARC and frees Msg before returning.
Teardown R2=2/R3=`FFFFFFFF` is linked to the last native Party_AddMon/copy,
seed call and constructor POP, rather than reset to standalone test values.

## I metodi e gli strumenti da usare

Use the [owner](../../features/trainer-strategy/README.md),
[verifier](../../features/trainer-strategy/tools/attribuisci_messaggi_chiamante.py),
[adapter](../../features/trainer-strategy/test/caller_message_bench.py),
[adapter tests](../../features/trainer-strategy/test/test_caller_message_bench.py)
and [replay tests](../../features/trainer-strategy/test/test_message_caller_attribution.py).
Dependencies and environment identity follow the
[test bench](../test-bench.md#linking-source-to-an-exact-rom): Python, ndspy,
Capstone and Unicorn default17/Cortex-A15 with the qualified hook-width contract.
This is not a console hardware timing model.

From repository root, using your own input/object files and fresh private output:

```sh
python3 source/features/trainer-strategy/tools/attribuisci_messaggi_chiamante.py \
  --language EN --rom /path/to/own-r4-EN.nds \
  --objects /path/to/own-rematch-objects-EN \
  --strategy-object /path/to/own-strategy-objects-EN/teams.o \
  --json /path/to/private/messages-caller-EN.json.gz
```

Repeat for IT with the matching input and retained objects. Existing outputs,
aliases, source-directory outputs and retained-object-directory outputs are
refused. Expanded report is bounded32MiB; stored output8MiB. Use one producer
at a time,180s/1GiB RSS/2MiB log/16MiB case budget, allowing1GiB peak disk
growth while retaining at least10GiB free. No build, capture or save is needed.

The adapter authenticates the unchanged bench and caller sources, preserves
the19 nested constructor SDK implementations and removes exactly three
high-level Msg stubs from an isolated function namespace. Native message code
must still equal installed instructions after SDK stub setup and at API entry.
Its six SDK services use the pinned standalone message models with only their
observer TOP bound to INNER. No standalone setup/call/run is invoked; there is
one CPU, no nested emu_start and no register/frame/packet bridge.

A stage/owner dispatcher executes each message service once and leaves the
constructor back-ends unchanged. Shared CopyTo/Delete calls inside the
constructor belong to that constructor, not to a second trainer-message API
sequence. Message and constructor SDK ledgers remain separate from the start;
the original header55 plus constructor event sequence is not manufactured by
filtering a combined trace.

Constructor replay reuses two literal source guard blocks authenticated against
the pinned parent AST, including complete function signatures/wrappers. Nested
actual caller/message contexts use their own source-derived oracle, not a
normalized standalone receipt. Five API entries/returns,11 message SDK entries,
five native nested helpers and all228 message starts are required. The entire
native message write transcript includes38 contextual stack stores and`11+5*N`
object/decrypt/copy writes. Msg-only hook count is`217+34*N`:387 EN31/421 IT31.
Total hooks equal constructor hooks + message hooks +158, independently derived
as124 caller fetches,27 save/header helper fetches, one raw-header SDK entry
and six native RNG setter/getter fetches. Counts do not measure speed or WCET.

The finite matrix comprises Plus0/1 × two original seeds, one stack-poison
guard, two paired observer OFF runs and four causal falsifiers per language.
Two completed falsifiers omit temporary/Msg free while retaining the exact name,
six packets, seed and declared functional RAM. Two early falsifiers corrupt the
encrypted-read destination or overwrite the live high-level entry with a stub.
Each must fail at its named stage with its expected allocation or mutation
evidence; an arbitrary exception is insufficient.

OFF compares complete API/register/party/message/service state and guarded
functional/global RAM. Constructor return's raw RAM digest can differ because
the qualified ON observer poisons declared constructor scratch. Transition
registers, neutral flags and entry RAM must still agree; functional hashes and
object-lifetime checks remain required. Whole-RAM digests alone do not localize
a difference or replace guarded ownership checks.

For replay, provide exact-ROM links `r4-EN.nds`/`r4-IT.nds`; under the object
root place `public-build-EN/` and `public-build-IT/` with both rematch objects,
and under the strategy root place `build-EN/teams.o` and `build-IT/teams.o`:

```sh
SGP_MSG_CALLER_ROM_DIR=/path/to/private/rom-links \
SGP_MSG_CALLER_OBJECTS_DIR=/path/to/private/rematch-object-root \
SGP_MSG_CALLER_STRATEGY_DIR=/path/to/private/strategy-object-root \
SGP_MSG_CALLER_REPORT_DIR=/path/to/private/reports \
python3 -m unittest discover -s source/features/trainer-strategy/test -p test_message_caller_attribution.py
python3 -m unittest discover -s source/features/trainer-strategy/test -p test_caller_message_bench.py
```

`SGP_MSG_CALLER_LANGUAGES` selects a comma-separated subset during diagnosis;
both languages are required for the combined claim. Replay reads original
inputs and verifies metadata/counterproofs without executing the guest again.
Both complete language campaigns passed:11 runs each, about69s/language,
OS peak RSS522272768B EN/535937024B IT, maximum608B guest stack. Thirteen replay
methods and three adapter methods passed with both inputs and no skips.
All four positive complete parties, prepared52B Trainer and restored seeds
match the corresponding earlier caller results in each language. Native message
production and ownership are new observations; whole old/new RAM identity is
not claimed because message allocations and stack contents genuinely differ.

Independent reviews checked raw/source/ABI, producer/counter evidence and public
instructions. Before execution, review caught an oracle-wrapper bypass and
shared String APIs incorrectly routed as trainer-message calls; both were
fixed and calibrated with portable tests. An initial OFF comparison included
the suffix raw RAM hash; a retained diagnostic pair isolated one suffix
raw-digest field difference while the declared scratch projection remained equal.
The narrowed comparison retains
context and functional-state gates, with mutation rejection tests. An early
diagnostic probe lacked the later cross-constructor object checkpoint and was
not promoted or rewritten as a complete campaign.

Documented provenance, installed-byte identity, finite source semantics and
initialized caller/API activation are established in their respective scopes.
Original native C-to-object reconstruction remains unavailable. These results
provide a reusable producer/ownership method and identify remaining model
boundaries; they do not establish an allocator optimization or game speedup.
Private receipts preserve commands, exits, source snapshots, hashes and failures.
No game source, ROM, save layout, identifier, setting or default is changed.
Natural encounters, native heap/NARC/FS bodies, original compiler reconstruction,
species-name production, other formats/error paths, whole battle, UI, SAVE/cold
restart and physical-device validation remain outside coverage.
