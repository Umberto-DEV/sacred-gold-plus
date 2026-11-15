# Native trainer header inside the complete caller

This case joins the [native NARC reader](native-narc-reader-source-rom-1.3.2.md)
to the [complete species-name caller](species-name-caller-source-rom-1.3.2.md).
The header55/31 is selected by native code before the same caller builds six
Pokémon and destroys its trainer message. Other constructor reads retain their
original models. Ownership at the shared reader address is part of the proof.

## Cosa farebbe un professionista di alto livello che non sto chiedendo

Prove the actual nested call, not a bridge between two standalone tests. Verify
that stub installation has preserved the native reader, that constructor calls
to the same entry still execute their original backend once, and that source
oracles no longer require an obsolete header model event or return value.
Capture the header frame before the constructor reuses it. Seek an omitted
Close with identical final game output/RAM and a short header that returns
normally. Bind counter context and checkpoints independently of claimed metadata.

## Il materiale più grezzo da cui partire

Use your own exact Plus1.3.2 r4 ROM and retained project objects:

| Language | ROM bytes | ROM SHA-256 |
| --- | ---: | --- |
| EN | 152786844 | `2e30d6960bb059615fca7527700d86f8282e82ccbe99bf62e22f027453dc3d3d` |
| IT | 159029760 | `13ebac02bdea3036511773587e6603ce6834e25f4b13d1a4662c3e954bfd5d4a` |

Whole-image identity establishes the required language/revision. See the parent
cases for retail/base/V4 lineage, ARM9 compression/autoload, independent raw
readback, original source references and the native FSFile layout limitation.
Retain `rematch-variants.o`, `rematch-stub.o` and `teams.o` using the
[rematch build instructions](rematch-source-rom-1.3.2.md) and
[constructor instructions](strategy-constructor-source-rom-1.3.2.md).
The verifier reuses their source/recipe/ELF/relocation/owner checks; no new native
compiler or ROM build is invoked. Original native compiler/objects remain
unavailable. No ROM, extracted archive, save, BIOS, object or private receipt is
included in the public tree.

Native caller entry is `020733C0`, physical `000773C0`. It reaches the tail
wrapper `TrainerData_ReadTrData` at `020735D8` through BL`020733F8`, LR`020733FD`.
The tail wrapper loads the literal reader pointer`02007509`, reorders arguments
and branches to `ReadWholeNarcMemberByIdPair` at`02007508`. Its five ordinary
Thumb instructions occupy10B, SHA-256
`1bb0ec374a927128d9cd04b2309888f257fd5b391b25750c3f281fcecbdf653d`.

The parser's238B/103 starts, four code hashes, pools, path table and five ARM FS
entries are those of the native-reader parent. Header resource is NARC55
`a/0/5/5`, FAT ID184, whole20716B at`01F91A00`, SHA-256
`4de9e541894f6573c5b52e338de911a71fcf82c206ebf041bccb81e817c13299`.
Member31 is20B at archive offset6576 / ROM`01F933B0`, SHA-256
`db2e0fa9e4d0b97a0d1721e878001bcddafe1e379827adccc37844cdbce13fff`.
Raw FAT/FNT/NARC and ndspy reads must agree. FS models supply whole-file cursor
slices; native code computes the selected member. There is no second host header
copy or fabricated legacy read event.

At reader entry R0..R3 are `[LOCAL,55,31,02007509]`; saved R4..R7 are
`[BattleSetup+4, trainerNameDestination, incomingR6, 1]`, with the actual R8..R11
cookies preserved. R12 is zero in this fixture. The caller frame96B makes
`INNER=outerSP-96`; reader SP is INNER, its136B peak is outerSP−232, and its
opaque FSFile address is INNER−112. These are synthetic fixture addresses,
not installed allocator reservations. Five FS entries are ARM/width4 and return
to Thumb; the qualified BLX across the1KiB boundary remains a single start.
The complete caller's existing608B peak remains the bound.

The snapshot is taken at the real return PC`020733FC`, before executing the
next caller instruction. The later constructor overwrites this stack region;
checking the old frame at final return would be invalid. Native reader stores,
fifteen FS boundaries, full136B frame, adjacent caller locals and all other RAM
are checked at this precise phase. LOCAL20 initially contains the declared
caller stack poison C7 or39, not the standalone reader's A5 destination fixture.
Only those20B may change in the96B caller frame; its remaining32B Trainer tail
keeps its original poison provenance. No fixture or register is reset at entry.

The API is void. Normal R0=1 is the Close model's residual; it is not the old
`B.LOADER_RESULT`. The caller overwrites it before use. Its helper record must
retain the actual result rather than normalize it to satisfy an older oracle.
The header reads no RNG: its observed RNG value must equal the actual caller
seed, including both original seeds. The native setter and final getter remain
separate actual API calls.

The same entry`02007508` has a second role during construction. Its original
member-read backend remains modeled for NARC56,2,3,33 and11. Normal has188 reads;
Plus has190 because the selected constructor paths already read NARC11 twice
more in the preceding qualified case. The respective NARC11 counts are79/81;
other counts are1/78/24/6. These counts belong to this exact profile and are not
a general cache or performance result. Original body model/resource/ABI guards
and each actual event remain required.

## I metodi e gli strumenti da usare

Use the [verifier](../../features/trainer-strategy/tools/attribuisci_lettore_chiamante.py),
[adapter](../../features/trainer-strategy/test/caller_narc_bench.py),
[portable tests](../../features/trainer-strategy/test/test_caller_narc_bench.py),
[replay tests](../../features/trainer-strategy/test/test_header_caller_attribution.py),
[owner](../../features/trainer-strategy/README.md) and
[test bench](../test-bench.md#linking-source-to-an-exact-rom).
Dependencies are Python, ndspy, Capstone and Unicorn with the previously
qualified default17/Cortex-A15 hook contract. This is not hardware timing.

```sh
python3 source/features/trainer-strategy/tools/attribuisci_lettore_chiamante.py \
  --language EN --rom /path/to/own-r4-EN.nds \
  --objects /path/to/own-rematch-objects-EN \
  --strategy-object /path/to/own-strategy-objects-EN/teams.o \
  --json /path/to/private/header-caller-EN.json.gz
```

Repeat for IT. Fresh output must be outside source and retained object
directories. Expanded report32MiB/stored8MiB; budget180s/1GiB OS RSS/2MiB log,
16MiB case,1GiB peak disk with at least10GiB free. Use one producer at a time.
The CLI enforces the qualified Mac/Linux peak-RSS units before/after acquisition
and encoding. Original fixtures remain unchanged.

The isolated bench SDK table removes only the reader entry after the preceding
name/message removals. Original `B.STUBS` remains intact for constructor audit.
During the prefix the native reader and its five FS models execute directly;
there is no existing bench callback at those five ARM entries. During construction
the parent observer records a model call, the exact original nested backend
executes once, and an explicit PC=LR replaces the removed BXLR stub. No native
reader PUSH executes in that modeled role. Every188/190 dispatch must bind its
owner, stage, argument registers, SP, saved registers, event index, raw resource,
backend result and actual return. Duplicate or missing calls must fail.
The first constructor read comes from the retained `rematch_hook` ELF symbol
at`0226B4A1`: LDR at`0226B4A2` loads the native tail pointer, while the actual
BLX-register call is`0226B4A4`, LR`0226B4A7`. The resident stub saves16B and
module hook32B below the constructor's152B frame, yielding SP=INNER−200.
That source/ELF provenance is distinct from inferring a caller only from a trace.

The reader borrows the existing CPU with only TOP/destination/return/class
bindings changed. The authenticated snapshot derivative removes the complete
standalone setup/emu_start statement; it never calls those methods or restores
a context. Counter/ABI profiles use actual caller cookies, the tail's R3,
R12 policy, caller seed and initial destination state. No fake standalone API
receipt is constructed.

Seven bounded source recipes authenticate full parents and whole function
wrappers. The twenty constructor-result statements are unchanged. The
constructor-evidence derivative changes only its outer event assertion, removing
the obsolete modeled header prefix while preserving the complete constructor
ledger. Other adaptations change the expected adapter, header result/service
assumptions, contextual reader oracle and hook accounting. Native six-name and
trainer-message guards remain in force. Original modules and shared sources are
not edited to force a result.

Total hooks are exclusive constructor + trainer message + six species names +
header reader +157. The replacement adds117 hooks to the preceding caller:
118 native-reader hooks replace one old model boundary. Prefix checkpoint is
source-derived:84 selected caller instructions +3 seed setter +27 save/header
helper instructions +118 reader +`202+34*N` message prefix, giving604 EN/638 IT.
The two-word assignment loop runs six times; class72 takes the non-rival branch.
A claimed checkpoint is compared to this path, not treated as its own authority.
Counts indicate coverage, not game responsiveness or a speedup.

The matrix admits Plus0/1 × two seeds, one second-stack-poison guard, two OFF
pairs, one FS volatile-register control and two causal falsifiers per language.
FS clobber control poisons R1/R2/R3/R12/NZCV while retaining the model's R0 policy
and saved registers; complete game output must remain identical. OFF compares
all header-phase state and whole RAM, plus every original constructor dispatch.
The inherited constructor scratch projection still applies at final return.

Skipping native Close preserves the complete party, Trainer52, restored seed,
caller return and final whole RAM while leaving the header ledger open. The
counter must fail resource closure with full original execution evidence.
A short header supplies19 of20 bytes and leaves its last byte at the incoming
caller poison. The parser returns normally; the benchmark's canonical-prefix
provenance guard then stops before any constructor instruction executes. That
benchmark rejection is not native game error handling or a cartridge failure.
Both partial and complete counters must retain actual CPU, return ISA, frame,
phase/RNG bindings and the exact source-derived checkpoint/delta.

```sh
SGP_HEADER_CALLER_ROM_DIR=/path/to/private/rom-links \
SGP_HEADER_CALLER_REPORT_DIR=/path/to/private/reports \
SGP_REMATCH_OBJECT_DIR=/path/to/private/rematch-object-root \
SGP_STRATEGY_OBJECT_DIR=/path/to/private/strategy-object-root \
python3 -m unittest discover -s source/features/trainer-strategy/test -p test_header_caller_attribution.py
python3 -m unittest discover -s source/features/trainer-strategy/test -p test_caller_narc_bench.py
```

ROM links are`r4-EN.nds`/`r4-IT.nds`, reports`header-caller-EN.json.gz`/IT;
rematch root contains`public-build-EN/` and IT, strategy root`build-EN/teams.o`
and IT. `SGP_HEADER_CALLER_LANGUAGES` selects a diagnostic subset. Replay requires
private inputs/receipts but does not execute the guest again.

Both final language campaigns passed ten runs: EN75.33s/OS551010304B,
IT75.326s/OS564314112B. Seven portable adapter methods and nine replay methods
passed with both inputs and no skips; replay7.159s/OS720781312B. Total hooks were
1039992 Normal/1056219 Plus EN,34 more in IT. Header118/136, caller608 peak and
prefix604/638 matched their source contracts. All four complete parties,
Trainer52 and restored seeds match the preceding caller in each language.

Projected old/new RAM hashes are not directly comparable: the older harness
installed a reader stub where the new harness retains native code. One actual
EN Plus/seed12345678/C7 paired readback found12 differing bytes in4MiB: ten in
already-declared scratch and two at the shared reader entry. Adding only that
two-byte harness-code interval to the existing scratch projection made this
pair equal. The diagnostic took19.265s/OS552632320B. This localizes the tested
pair; it does not claim old/new whole-RAM identity for the eight-case matrix or
for natural encounters. The installed ROM stayed identical. The Close falsifier's
whole-RAM equality compares two runs of the same current harness.

Independent raw/source/ABI reviews checked both languages, original callbacks,
regional/source provenance and complete counter premises. Initial probe established
the117-hook delta. Early validation found a standalone fixed-seed assumption,
a counter checkpoint not bound to source and unbound partial-frame metadata.
The current guards bind these explicitly, and coordinated forged-counter tests
are rejected. The first EN attempt retained two completed raw runs before its
fixed-seed oracle failed on seed79; both pass the corrected pure oracle. Final
matrices were reacquired with one exact producer snapshot, not promoted from
those diagnostics. Failed/diagnostic sources and receipts remain private.

Documented source provenance, installed-byte readback, finite semantic equality
and initialized activation retain separate scopes. Original native compilation,
real FSFile/SDK/card internals, native constructor member parsing, other trainer
profiles/errors, natural encounters, UI, SAVE/cold restart and hardware remain
outside coverage. No game source, ROM, save layout, ABI, ID or default changes;
no reclaimed memory or game speedup is claimed.
