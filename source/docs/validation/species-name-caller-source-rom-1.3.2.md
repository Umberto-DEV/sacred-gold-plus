# Native species names inside the complete trainer caller

This case joins the [species-name producer](species-name-source-rom-1.3.2.md)
to the [trainer-message caller](trainer-message-caller-source-rom-1.3.2.md).
All six GetSpeciesName calls, their borrowed String copies and destructors run
inside the actual Pokémon constructor, in the same CPU and RAM as the outer
trainer caller. Heap/archive services remain declared models.

## Cosa farebbe un professionista di alto livello che non sto chiedendo

Verify composition at real callsites and real stack frames. A standalone name
producer and a constructor using a high-level name model do not establish that
link. Check source arguments, installed instructions, returned object lifetime,
borrowed consumers and final resource closure. Seek counterexamples with the
same complete party but leaked objects; review raw inputs and ABI independently.

## Il materiale più grezzo da cui partire

Use your own exact Plus1.3.2 r4 image:

| Language | Bytes | SHA-256 |
| --- | ---: | --- |
| EN | 152786844 | `2e30d6960bb059615fca7527700d86f8282e82ccbe99bf62e22f027453dc3d3d` |
| IT | 159029760 | `13ebac02bdea3036511773587e6603ce6834e25f4b13d1a4662c3e954bfd5d4a` |

The parent cases explain retail → inherited Plus → V4 → exact r4 lineage,
independent ARM9/FAT/FNT/NARC readback, compression and autoload handling.
This composition needs the exact final image and the retained rematch and
strategy objects described in the trainer-message caller case. No complete
ROM, extracted archive, object, save, BIOS or private receipt is distributed.
Whole-image hashes identify language/revision; internal header labels alone do
not. The historical species-bank generation recipe remains unavailable.

Native source reference is HGSS commit
`cb614ad23449d5852b40321dc409c4143872b35c`. The linked producer case cites
pokemon.c, msgdata.c, pm_string.c, heap definitions and their hashes. Original
native compiler/objects are unavailable; source correspondence and finite
semantic verification do not claim native binary reconstruction. The retained
Plus objects have their own authenticated source/build/insertion proof.

The outer caller starts at `020733C0` and calls constructor `02073604`.
CreateMon reaches SetBoxMonDataInternal; its default nickname path contains:

| Action | Entry | Caller BL | Return LR |
| --- | --- | --- | --- |
| GetSpeciesName(species, heap0) | `0200BCDC` | `0206F4B2` | `0206F4B7` |
| CopyStringToU16Array(String, nickname, 11) | `02026A68` | `0206F4BC` | `0206F4C1` |
| String_Delete(String) | `02026380` | `0206F4C2` | `0206F4C7` |

The 38-byte GetSpeciesName success wrapper `[0200BCDC,0200BD02)` has SHA-256
`ebd9e75544b5604322265445535b367d06926905f6a741b762746cb27e59e93e`.
The 28-byte caller span `[0206F4AE,0206F4CA)` has SHA-256
`d86015b43ee5d6fc684af1db99217d61f2a812d5bfdb7bb69e16fb9d1f36d870`.
Physical offsets are `0000FCDC` and `000734AE` in these uncompressed resident
ARM9 spans. Raw reads and decoded-section reads must agree before execution.
Literal pools remain data and are qualified separately.

Trainer31 has species355/353/93/200/302/94. Bank237 is NARC27 `a/0/2/7`,
496 records/keyD00E. Selected records contain 8/8/8/11/8/7 words including EOS;
all six are unpacked. Full bank hashes and physical data offsets follow the
producer case. Models supply only encrypted header/MAT/payload slices. Native
instructions decrypt and build MsgData/String objects; no host-decoded name or
serialized String is written into guest RAM.

At each species entry R0..R3 are `[species,0,3,OTID & FFFF]`.
For Pokémon base `02200080`, let `order` be permutation
`((PID >> 13) & 31) % 24` and block address be
`base + 8 + 32 * order.index(block)`. Saved R4..R7 are `[0,B,D,A]`;
the copy/delete caller changes R4 to the returned String. The nickname
destination is block C. These addresses are derived from source/PID and the
substructure table, rather than accepted from a trace. Capacity11 includes EOS;
copy preserves the zero-filled destination tail. The eleven-word species200
exercises the full capacity. This does not cover oversized names or error paths.

The outer frame is96B. Constructor152 + CreateMon80 + CreateBoxMon48 +
SetBoxMonData16 + its internal104 place the name API at outerSP−496.
The native wrapper adds16B and nested message code reaches another80B:
name peak is outerSP−592, within the existing608B caller bound.
The synthetic name heap is `[02370000,02371000)`, separate from trainer Msg
`02360000` and constructor heap11 `02200000`. Name Msg12B is `02370020`,
String `2*N+10` at `02370040`, temporary `2*N` at the next aligned location;
handle `02370800` is opaque. These are bench assignments, not runtime allocator
addresses. Zero fill is the declared name heap fixture; trainer message uses C7.

MsgData, NARC handle and temporary are dead before GetSpeciesName returns.
Only String survives, is borrowed by the copy, invalidated with dead magic and
freed. Addresses may be reused for the next name only after this closure.
Canaries are checked before reuse: differently sized generations do not imply
that all earlier canary locations remain intact simultaneously. The frozen-RAM
mask uses the precise union of allocation bodies and canaries; unused holes
and the opaque-handle area remain frozen. The outer trainer Msg stays alive
and unchanged through all six constructions, then its caller suffix closes it.

## I metodi e gli strumenti da usare

The [verifier](../../features/trainer-strategy/tools/attribuisci_nomi_chiamante.py),
[adapter](../../features/trainer-strategy/test/caller_species_bench.py),
[portable tests](../../features/trainer-strategy/test/test_caller_species_bench.py)
and [replay tests](../../features/trainer-strategy/test/test_species_caller_attribution.py)
reuse Python, ndspy, Capstone and Unicorn default17/Cortex-A15. See the
[test bench](../test-bench.md#linking-source-to-an-exact-rom) and
[owner](../../features/trainer-strategy/README.md). The qualified hook contract
is an instruction observation mechanism, not a console timing model.

From the repository root, with private inputs and a fresh private output:

```sh
python3 source/features/trainer-strategy/tools/attribuisci_nomi_chiamante.py \
  --language EN --rom /path/to/own-r4-EN.nds \
  --objects /path/to/own-rematch-objects-EN \
  --strategy-object /path/to/own-strategy-objects-EN/teams.o \
  --json /path/to/private/species-caller-EN.json.gz
```

Repeat with IT and its objects. Output must be fresh, outside source and retained
object directories. Expanded report32MiB/stored8MiB; allow180s/1GiB RSS/2MiB log,
16MiB total case,1GiB peak disk while retaining at least10GiB free. Public CLI
checks the OS peak RSS in Mac/Linux units, including after JSON encoding.
Use one producer at a time. No ROM build or emulator capture is necessary.

The adapter authenticates full parent source hashes. Four exact recipes extend
only precise frozen spans, compose the parent body collector, add native name
receipts and account for name instructions in the caller oracle. The two pure
constructor guard blocks remain unchanged. The isolated bench namespace removes
only the GetSpeciesName high-level stub in addition to the already qualified
trainer-message removals. Native bodies must still match readback after stub
setup. The shared parent modules and original SDK table remain unchanged.

All three name APIs are intercepted before the inherited constructor observer;
otherwise it would record a second, modeled allocation. The six native SDK
boundaries dispatch once through the existing bench callback. Name and
constructor ledgers are separate from their creation: no fabricated name event
or post hoc filtering recreates the old ledger. Constructor heap allocation
addresses consequently become more compact; their remaining original backends
and sequential lifetime guards remain unchanged.

The species observer reuses authenticated producer method code with actual
stack/heap/destination bindings. No standalone setup/call/run, nested emu_start,
register restoration, CPU swap or packet bridge is used. Metadata scope changes
must preserve registers and all guest RAM. The oracle derives ABI, stack stores,
helper returns, cipher destinations and every native write from source, including
STRB hook sign extension and the wrapper's preserved R3. Each name requires244
qualified native starts, eleven SDK calls and all three actual API returns.
Its hook count is `233 + 34*N`; six names total3098. Caller total is exclusive
constructor hooks + trainer-message hooks + native-name hooks +158. Compared
with the earlier modeled-name path, source-derived delta is2470 hooks in either
language; this is coverage accounting, not a speed measurement.

The campaign contract admits Plus0/1 × two seeds, a second stack poison, two
OFF pairs and four causal falsifiers per language. Two leaks are introduced only
for the last name, avoiding a later legitimate allocator reuse. They preserve the
complete party/name/seed while omitting native String free or MsgData destruction.
Wrong bank and a high-level stub overwrite must be rejected at their specific
native stage before any party member is added. An unrelated exception does not
satisfy a falsifier. Replay checks the causal premises and the exact rejection.

OFF preserves native execution/models and disables native write logs. It compares
all API/internal registers, String bytes, copied names, objects, SDK dispatch,
neutral scope contexts and declared functional RAM. Raw whole-RAM hashes at
individual name scopes are excluded because the inherited constructor observer
poisons its own declared scratch; the same guarded projection remains required.
This exclusion does not hide a change in arguments, state or copied bytes.

For replay use private `r4-EN.nds`/`r4-IT.nds` links, a rematch root with
`public-build-EN/` and `public-build-IT/`, a strategy root with
`build-EN/teams.o` and `build-IT/teams.o`, and the fresh reports:

```sh
SGP_SPECIES_CALLER_ROM_DIR=/path/to/private/rom-links \
SGP_SPECIES_CALLER_REPORT_DIR=/path/to/private/reports \
SGP_REMATCH_OBJECT_DIR=/path/to/private/rematch-object-root \
SGP_STRATEGY_OBJECT_DIR=/path/to/private/strategy-object-root \
python3 -m unittest discover -s source/features/trainer-strategy/test -p test_species_caller_attribution.py
python3 -m unittest discover -s source/features/trainer-strategy/test -p test_caller_species_bench.py
```

`SGP_SPECIES_CALLER_LANGUAGES` selects a comma-separated diagnostic subset;
both languages are needed for the combined result. Replay requires inputs and
receipts but does not execute the guest again.

Both language campaigns passed: eleven runs each,73.784s EN/74.684s IT,
OS peak RSS540606464B EN/554319872B IT. The six name paths reached592B below
the outer stack, while the complete caller retained its608B peak. Total hooks
were1039875 Normal/1056102 Plus EN, and34 more in IT for the trainer message;
name hooks were3098 in either language. Ten replay methods and six portable
adapter methods passed with both languages and no skips. Replay OS peak was
710410240B; it does not rerun the guest. All four complete parties, prepared52B
Trainer and restored seeds match the earlier modeled-name caller in each
language. Entire old/new RAM equality is not claimed: modeled allocation
addresses and actual stack contents differ.

Independent source/raw/ABI review checked both languages and the original Plus
object/readback chain. Before the campaigns, review demonstrated that the leak
counter validator could accept a truncated trace missing its first five names.
The corrected gate requires all six lifetimes, exact last-only SDK dispatch and
global instruction delta; the original falsification is now rejected and retained
as a replay regression. An initial probe stopped before the constructor body
because a controller attribute collided with the inherited trainer-name bytes;
that failed probe and its source remain private evidence. A replay test initially
used a malformed phantom event lacking ABI fields; the corrected test supplies a
complete plausible SDK event. Neither issue changed game bytes or campaign data.

Documented provenance, reconstructed Plus payloads, finite source semantics,
initialized activation and remaining unattributed links retain separate scopes. Native SDK/allocator internals, other species/trainers,
natural encounters, battle rendering, SAVE/cold restart and hardware remain
outside this contract. No game behavior, ROM, save format, ABI, ID or default is
changed; no memory saving or game speedup is claimed.
