# Installed trainer-strategy hook: positive paths and atomic writes

The current strategy owner applies the nine specified move substitutions across
seven trainer buffers in Plus. It preserves the type3 caller's arguments,
registers, flags and inherited level calculation. This case starts at an
initialized native hook boundary and stops before CreateMon; complete Pokémon
and natural encounters remain separate execution questions.

## Cosa farebbe un professionista di alto livello che non sto chiedendo

The [earlier consumer case](rematch-consumer-source-rom-1.3.2.md) reconstructs
this dependency but executes only the712/713 exclusions. Test the positive
configuration against the exact installed bytes, rather than transferring the
historical672 comparisons or Bugsy battle evidence to another ROM revision.

Follow six sequential calls on one persistent buffer. The first matching Plus
call must apply the complete edit; the next five must fail the original-record
fingerprint and perform no buffer write. Compare Normal and the archived level
hook. Require actual helper entry/return bindings and instruction coverage as
well as final output. A preapplied buffer produces the same final bytes but
cannot prove that this invocation applied the change.

## Il materiale più grezzo da cui partire

Use your own exact r4 input and the retained strategy object from the
[dependency reconstruction](rematch-consumer-source-rom-1.3.2.md).
The [owner README](../../features/trainer-strategy/README.md),
[installer](../../sgp13/teams.py),
[native wrapper](../../features/trainer-strategy/native.c),
[C core](../../features/trainer-strategy/strategy.c) and
[specification](../../sgp13/data/strategic-teams.json) provide the complete recipe.
The specification pins each108-byte source member by SHA-256 and each changed
move by offset, before and after value.

| Input | SHA-256 |
| --- | --- |
| r4 EN,152786844B |`2e30d6960bb059615fca7527700d86f8282e82ccbe99bf62e22f027453dc3d3d`|
| r4 IT,159029760B |`13ebac02bdea3036511773587e6603ce6834e25f4b13d1a4662c3e954bfd5d4a`|
| Retained `teams.o` |`e2429f61c7ee16071d303f7ca55cbb1553508720c6fe97b77aead9ce56e499e1`|
| Strategy580B |`09e88a137b006e8ba638770ba57e1a6e5fe9960787e05ec7c253cb230da04436`|
| Config192B plus320B zero padding |`003ec5b4372e8b0070f2521d1676a8038d19b4b472218aadedb4735c0bb27114`|
| Complete2048-byte owner |`8a3450f4b0864b21ee0bdcb00b25dda966f2ad803246bbf15f343816ac2e234c`|

Compilation uses the authenticated Apple Clang21.0.0 `clang-2100.4.1.1`,
SHA-256`fc5e3cbba6ad54059295cad716aacb05ace8235f5f7a6031f1d8c15d24bd6d66`,
and the flags in `teams.compile_native`: ARMv5TE/ARM946E-S Thumb,`-Os`,
freestanding, no builtins/stack protector/jump tables/unwind tables, warnings as
errors. Its existing loader resolves the relocatable ELF at`023D6000`; the
independent ELF reader checks the resulting bytes and mapping symbols.
This case reattests that retained exact reconstruction and source pins; it does
not invoke a compiler or rebuild a ROM. Original native MW objects/compiler and
the historical Plus compiler remain unavailable.

The installer starts from a zero2048-byte owner, emits580B code,956B zero code
padding,192B configuration and320B zero config padding. It redirects four native
BLs to`strategy_hook` at`023D6228`, which tail-chains to the archived Plus hook
at`023D8194`. Existing stage comparison separates retail, inherited base, V4 and
current Plus; see the preceding case for identities and unmapped-span limits.
The current verifier checks all four BLs and the entire owner including padding.

| Component | Loaded address | Physical offset in these r4 inputs |
| --- | --- | --- |
| Strategy owner2048B |`023D6000`|`001258C0`|
| Configuration allocation512B |`023D6600`|`00125EC0`|
| Four native call sites |`02073718`,`02073802`,`0207390C`,`02073A0C`|`00077718`,`00077802`,`0007790C`,`00077A0C`|
| Archived Plus hook |`023D8194`|`00127A54`|
| Archived Plus body/table |`023D8100`/`023D8500`|`001279C0`/`00127DC0`|

These are raw ARM9/autoload section locations from independent section reading,
compared with ndspy's loaded image. They are not a rule for compressed overlays.
The input identity includes language/revision; the IT internal game code alone
does not establish language. No extracted Nintendo bytes are included here.

Raw FAT/FNT and NARC readers locate headers in`a/0/5/5` and parties in`a/0/5/6`.
Trainer IDs are21,31,32,33,34,244,245, all format3/count6. Configuration order and
nine move deltas are reconstructed from those raw members and the public spec,
then compared with all512 installed bytes. The JSON receipt records physical
member offsets, header/member hashes and archive identities for your own input.

### Actual caller, ABI and lifetime

Only the type3 site`02073A0C` executes here. Its BL reaches the installed
wrapper,`strategy_native` at`023D61C4`, core`strategy_apply` at`023D602C`,
archived Plus level helper`023D8134` and, when active, group maximum`023D8100`.
The hook returns at`02073A10`; the native`LSRS R3,#24` executes, then the CPU
stops at`02073A12` before its four-byte BL to`0206DE38`. Address`02073A14`
is the second half of that BL and is not an instruction boundary.

The initialized ABI has R2 pointing to the current18-byte record, R4 to a
coherent BattleSetup, R5=52 for enemy index1, R6 to a workspace, R1 to species
and R3 to the native IV value shifted24 bits. The buffer base is at`[SP+74h]`;
the wrapper's32-byte push makes this`[SP+94h]`. At the stop, R0 is the
workspace, R1 species, R2 the inherited effective level and R3 the IV value.
SP, R4–R11 and native final NZCV are checked. Seed stays unchanged; the existing
Plus hit counter advances once per call even in Normal.

The transient108-byte buffer is the only game-data output of the core. A
volatile stack copy validates all edits before108 byte stores at`023D619A`.
Local delta stores at`023D6164`/`023D6168` target the copy at core-entry SP−128.
The native helper never edits the ROM archive or save and allocates no heap.
Every guest fetch is admitted by the ELF/native code map and exact byte check;
reads and writes have explicit bounds. All other4MiB main RAM remains frozen,
except the bounded stack, transient buffer and existing Plus counter.

## I metodi e gli strumenti da usare

Install the [pinned dependencies](../../requirements.txt) in your project
environment. From repository root, use your own private paths and fresh outputs:

```sh
python source/features/trainer-strategy/tools/attribuisci.py \
  --rom /private-inputs/r4-EN.nds --language EN \
  --strategy-object /private-results/consumer-EN-build/teams.o \
  --json /private-results/strategy-EN.json.gz

python source/features/trainer-strategy/tools/attribuisci.py \
  --rom /private-inputs/r4-EN.nds --language EN \
  --strategy-object /private-results/consumer-EN-build/teams.o \
  --readback-only --json /private-results/strategy-EN-readback.json

SGP_R4_ROM_DIR=/private-inputs \
  SGP_STRATEGY_OBJECT=/private-results/consumer-EN-build/teams.o \
  python source/features/trainer-strategy/test/test_attribution.py
```

Repeat the CLI for IT with its matching input. Test ROM names default to
`r4-EN.nds`/`r4-IT.nds`;`SGP_R4_ROM_NOME` can override the pattern with one`%s`.
Missing private inputs produce explicit skips. Keep reports private: they
contain extracted trainer buffers. The CLI writes deterministic gzip or compact
JSON outside the source/object directories, refuses existing outputs and bounds
expanded output to16MiB. Record argv, exit code, source hashes and resource use.

The [verifier](../../features/trainer-strategy/tools/attribuisci.py) combines
source/ELF/configuration admission, independent raw section/member readback and
bounded actual hook execution. `--readback-only` independently reads raw sections,
FAT/NARC members and ELF without constructing a CPU or calling the runtime observer.
The existing
[stage reader](../../features/rematch-variants/tools/rileggi_stadi.py) can repeat
the retail/base/V4/current comparison without CPU execution; use the exact
inputs and command in the dependency case. Neither reader substitutes a symbol
similarity for exact readback.

The [tests](../../features/trainer-strategy/test/test_attribution.py) check:

- Seven IDs×Normal/Plus×six sequential slots, plus the same archived-hook paths.
- Repeated calls and a preapplied same-output counter rejected as a fresh apply.
- Trainer33's third delta invalidated only in RAM: the first two edits reach
  the local copy on each call, but zero output stores occur and the buffer stays
  unchanged. Other controls cover changed preimage, unknown ID, Plus2 and count5.
- Register/seed/counter/buffer/helper/code-trace false receipts, code/config/pad
  drift, instruction boundaries, memory bounds and output aliases.

The initialized frames are explicit fixtures; six hook invocations are not a
full native constructor loop. No SDK model is needed in this path. Instruction
counts and maximum stack208B are verification observations, not hardware timing.
Run budgets are180s/1GiB RSS/2MiB logs/16MiB case output, with at least10GiB
free after the planned1GiB disk peak.

### Result, uncertainty and next link

Both languages passed:14 current groups,14 archived-hook groups and six
controls, with six invocations per group. First Plus calls perform the nine
specified substitutions in total,108 stores per matched buffer; repeats and
Normal perform no buffer stores. Actual level/register/flag results match the
archived hook. Eight test methods passed with no skips. Independent raw review
caught and resolved an instruction-boundary error before execution and a report
oracle that accepted omitted helper/code traces; current tests reject both.

Provenance and strategy binary reconstruction are documented and reattested.
Semantic equivalence is demonstrated for this type3 hook boundary and finite
fixtures. Observed activation is initialized Plus0/1 state, not a natural
encounter. Complete Pokémon, final move/PP consumption, the other three formats,
SDK failure paths, whole-battle balance and hardware/save validation remain
unqualified. The next finite link is actual native consumption of the edited
move fields; this case does not claim it.
