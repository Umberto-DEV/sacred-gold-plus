# Ordinary Shell Bell: static source and exact-ROM readback

The ordinary after-move item consumer is identified independently of the
[pivot item command](uturn-shellbell-order-source-rom-1.3.2.md). Its controller
entry, native BL, selected code/data profile and actual Shell Bell record agree
between the exact current Plus EN and localized IT inputs. This is static
attribution. No new guest run, healing request or healing loss is observed here.
The two installed defects in the [flinch snapshot helpers](uturn-source-rom-1.3.2.md)
remain separate, unrepaired findings.

## Inputs and source provenance

Supply your own compatible files; keep ROMs, extracted data and generated JSON
outside the public source tree. Filenames alone do not establish identity.

| Input | Bytes | SHA-256 |
| --- | ---: | --- |
| Current Plus EN |152786844|`2e30d6960bb059615fca7527700d86f8282e82ccbe99bf62e22f027453dc3d3d`|
| Current Plus IT |159029760|`13ebac02bdea3036511773587e6603ce6834e25f4b13d1a4662c3e954bfd5d4a`|

Both current images use internal `IPKE`, revision0. Localized Plus IT and retail
Italian `IPKI` are distinct targets. The tool intentionally rejects retail,
historical or modified candidates rather than guessing a regional shift.

The productive reference is the
[HGSS fork at cb614ad23449d5852b40321dc409c4143872b35c](https://github.com/ctrl-cheeb-del/pokeheartgold/tree/cb614ad23449d5852b40321dc409c4143872b35c).
The newer consultation reference is
[PRET HGSS at 6bf138d6035aa6b43d6f8f4132a12df70f86dcec](https://github.com/pret/pokeheartgold/tree/6bf138d6035aa6b43d6f8f4132a12df70f86dcec).
Use separate clean source roots at those pins. The reader authenticates six
files and eleven complete definitions per tree using the existing bounded
[C-definition reader](../../features/trainer-strategy/tools/confronta_box_move_pret.py).

In `src/battle/battle_controller_player.c`, the productive
`BattleControllerPlayer_TryAfterMoveItems` at line3870 corresponds to the newer
`ov12_0224E1BC`. The complete definitions agree after exactly two declared
identifier substitutions: the function name and
`ctx->attackerAfterMoveState` → `ctx->unk_30`. Their raw source hashes remain
distinct in the report. This is source alignment, not original compiler output
or independently established layout equivalence. The installed field offsets
are checked from actual instructions and literals.

This consumer is retained HGSS code. It has no new installer or replacement
payload in this case. The [composition map](../test-bench.md#from-the-source-tree-to-the-complete-rom)
explains how inherited code survives the Plus stages. The flinch helper's
separate source/compiler/installer/readback chain is documented in its own case;
its 68-byte installed identity is rechecked here, without a compiler invocation.
No original Metrowerks compilation or full-ROM C rebuild is claimed.

## Physical mapping and native path

The qualified overlay reader compares raw header/Y9/FAT routing and project BLZ
decoding against ndspy. Overlay12/file12 loads at `022378C0`:226176 decoded
bytes, BSS0,161600 packed bytes. Physical packed ranges are
`08314200..0833B940` EN and `08800000..08827740` IT. Decoded SHA-256 is
`6c95f5d2db58ebb3da1463c6b12bc1e47e7267cd0ccd8cb7905bf2568afb729e`.
A logical instruction inside compressed data has no linear physical byte offset.

| Link | Verified address or range |
| --- | --- |
| `sPlayerBattleCommands` | `0226CA90`; slot37 at `0226CB24` contains odd pointer `0224D225` |
| AfterMoveItems wrapper | `0224D224..0224D236`,18 code bytes; two following padding bytes |
| Actual wrapper BL | `0224D228 → 0224E1BC`, R0=`BattleSystem*`, R1=`BattleContext*` |
| Selected consumer profile | `0224E1BC..0224E384`,456 bytes |
| Profile code ranges | `E1BC..E20C` and `E214..E366`:418 bytes,200 static instruction starts |
| Switch table / padding / pool | `E20C..E214` / `E366..E368` / `E368..E384` |
| Four signed-halfword case targets | `E214`, `E244`, `E2C4`, `E348` |

The selected456-byte profile has SHA-256
`16f4fc3e37da48404fea4051c2b27c9905b4fa94c463053306b1343f54aa06be`.
Its code/data partition, direct branches, nine BLs and seven pool values are
read back; Thumb BL targets have a separate raw decoder compared with Capstone.
The profile is not an original compiler symbol extent or a guest-ISA admission.
The earlier1024-byte exploration window also contains the next function and
must never be treated as all executable consumer code.

The consumer saves24 bytes and reserves8 more; the wrapper saves8 bytes.
Its state at `CTX+30` must be in0..3. Values above3 can loop without a default
case. GetMaxBattlers, held effect and modifier precede TryFaintMon; a pending
faint can request a different script and return before case1.

## Actual item and case1 data

Item ID253 is mapped by the eight-byte row at ARM9 RAM `0210097C`, plain ROM
`0010497C`, to NARC member231. The row's other halfwords are328,77,219.
The independent raw archive reader resolves `a/0/1/7`, file146,516 records
of34 bytes. Member231 has SHA-256
`908a7f24f3f913a567fac9eb45d55b4493ab791c6f3e217345c883e8c4dc60d1`,
hold effect88 and modifier8. These values agree in EN/IT. Native cached records
use stride36: the two padding bytes and the cache preloader are separate from
the raw34-byte record. No preloader execution is proved here.

Case1 at `0224E244` requires:

- target other than `FF`, held effect88, U-turn bit `CTX+2140 &10h` clear;
- successful-move bit `CTX+213C &2000h` set;
- nonzero word at `CTX+2EC +1C×attacker`, read at `0224E274`;
- attacker different from target, nonzero partial attacker HP.

HP and maxHP are at `CTX+2D8C +C0×attacker` and the following word. The
comparison is **unsigned lower** (`BHS` rejects at `0224E28E`), consistent with
signed HP and unsigned maxHP in the productive header. A signed comparison is
not an interchangeable oracle for this instruction.

The positive static branch negates the damage at `E296`, calls DamageDivide
`02253178`, writes `hpCalc` at `CTX+215C` and the temporary battler at `CTX+118`,
then calls ReadBattleScriptFromNarc `0224EB9C` from `E2AE` with `[CTX,1,213]`.
Later instructions preserve command37 in commandNext, select RUN_SCRIPT22 and
advance state to2. A request for subscript213 is not HP application.
Avoid overflow and zero-divisor assumptions when constructing any later input;
`INT_MIN` negation and unrestricted accumulations are not qualified domains.

## Reproduce without a compiler or CPU

Run from the repository root, with the project Python environment and its
ndspy/Capstone dependencies. Git authenticates the reference roots. These tools
import neither a guest runner nor a compiler. The owned tests need only stdlib.

```sh
.venv/bin/python -B source/features/type-consumers/tools/rileggi_shellbell_ordinary.py \
  --rom /path/to/plus-en.nds --language EN \
  --reference /path/to/productive-hgss --heartgold-ref /path/to/newer-pokeheartgold \
  --json /path/to/private/ordinary-en.json
python3 -I -S -B -m unittest discover \
  -s source/features/type-consumers/test -p test_shellbell_ordinary_readback.py
```

Use IT with its exact input and a different fresh JSON path. Existing output
files and symlinks are refused. Exit0 means that the selected static profile,
source identities, routing and item data match; it is not game acceptance.
Compare consumer, wrapper, case1 and dispatch fields between the two reports;
physical offsets and whole-ROM identities remain language-specific.

The [reader](../../features/type-consumers/tools/rileggi_shellbell_ordinary.py)
and [owned counterexamples](../../features/type-consumers/test/test_shellbell_ordinary_readback.py)
check signed switch offsets, actual PC bases, literal alignment, table bounds,
nonwrapping windows, instruction-start membership and output preservation.
Actual EN/IT readback also passed with Unicorn/Keystone imports denied and only
the twelve declared read-only Git commands allowed as subprocesses.

## Optional static dependency profiles

Add `--include-neutral` to the readback command, using a fresh JSON path, to
identify the relevant dependency profiles too. This also authenticates three
source files and ten complete definitions per reference tree (some overlap the
base checks). It does not run a CPU or prove that a function is neutral at a
particular entry.

| Profile | Authenticated bytes | Selected code / static starts |
| --- | ---: | --- |
| Existing GetMaxBattlers leaf at `0223A7F0` |4|4 /2; reads `BattleSystem+44` |
| TryFaintMon at `0224DC74` |164|150 /70; two padding and12 pool bytes |
| TrySyncronizeStatus at `02254580` |412|400 /192;12 pool bytes |
| TryUseHeldItem at `0225471C` |1636|90 /43, only the common prefix and effect0/88 default route |
| CheckItemEffectOnHit at `02255634` |508|476 /228;32 pool bytes |

The initial1888-byte TryUseHeldItem exploration included a second function at
`02254D80`. That function is excluded. The selected neutral code consists of
`471C..476A`, `4D1E..4D24` and `4D4C..4D52`; gaps are not executable admission.
For effect0, signed switch entry0 at `476A` plus base`476C` reaches `4D1E`.
Effect88 takes the unsigned-above54 default branch. Other item effects, switch
entries and held-item processing are outside this selected90-byte route.
The HP literal at `4746` resolves to data at `4A40`, value`2D8C`.

“Neutral” means no relevant item/ability script request in a declared domain;
it does **not** mean no memory or RNG changes. Weather-form checking writes
`battlerIdTemp` on each iteration even when returning FALSE. Ability-on-entry
checks can choose a Trace target and advance RNG before testing for Trace.
Ordinary abilities alone do not justify a no-op model.

A sufficient source domain excludes pending status effects and special form
species, uses Shell Bell for the attacker and no target item, and declares the
active battlers, order, species, abilities, weather and entry-state fields.
Native getters, weather/form and ability-entry work still need execution checks.
Full HP does not neutralize every item: berries and other effects have different
predicates. Castform/Cherrim/Arceus/Giratina, Trace, weather requests and item
activation are counterexamples to investigate rather than skip.

The earlier API benches retain useful code/readback qualifications, but their
per-entry stack/register initialization and the action-end cancellation/reset
path do not establish a continuous ordinary controller chain. Keep a sequence
of isolated API queries distinct from one guest dispatch loop. A later execution
proof must bind its own entry state and report every remaining service boundary.

## Owned continuous dispatcher qualification

The [owned assembly driver](../../features/type-consumers/test/shellbell_dispatch.S)
is a test-memory component with no ROM installer. It reads a callback pointer
from a command table, calls it with the current system/context pointers using
`BLX r3`, and repeats without resetting registers or stack. Command39 stops the
loop before looking up that slot. The qualification supplies its **own** table
and two **own** handlers; it executes no original game function.

One authenticated compiler invocation produced an ELF556-byte object, SHA-256
`81e22493a4d8b03d6b96b37429645dd0fa222760c3cd50118827dc2c1ab38d92`.
The44-byte `.text` has SHA-256
`b2d47cc5e37fa5d3184e20531da93013f5450a9e517ffcb0fbc10e04ca9f5280`:
28 driver code bytes,4 literal bytes and two6-byte handlers. At test base
`022F1000`, the function symbols are odd offsets1,33,39 and their sizes32,6,6.
Ordered mapping symbols are `$t`0, `$d`28, `$t`32, retaining repeated names.
There are no relocations. A bounded raw ELF reader and the existing text loader
agree on the complete text and entries. The selected protected Apple clang
hash/flags and source identity are recorded before compilation; no linker or
compiler-version subprocess is needed.

The source predictor reuses the retained instruction interpreter and adds only
register `BLX r3` with an odd Thumb target. Its link register is `(pc+2)|1` and
flags stay unchanged. A separate scalar ledger agrees on all32 full-register
states,10 reads,6 writes with preimages and four final pages before the first
CPU. The retained CPU producer changes only two audited cap constants from65536
to64. It still uses one `emu_start`, with no runtime host writes or callee models.

Both first owned cells, observation ON and OFF, passed32 instructions and33
callbacks each. They execute20 distinct starts, use a16-byte frame and produce
commands28→29→39 through the two real owned calls. All saved registers and SP
are restored; the observed volatile LR residue is `022F1019`. Six actual-raw
forgeries and six altered ELF inputs are rejected. Reverification also passes
with CPU/assembler imports and compiler subprocesses denied. The backend is the
previously qualified Unicorn2.1.4/model17 semantic runner; this is not DS timing,
cache, interrupt, hardware or original-controller acceptance.

Use the project Python environment and the exact protected compiler supported
by [the compiler authentication helper](../../sgp13/compiler.py). This compiler
experiment was exercised on macOS. Another compiler or backend needs a separate
qualification. Source-only tests do not invoke a compiler or guest CPU:

```sh
python3 -I -S -B -m unittest discover   -s source/features/type-consumers/test -p test_shellbell_dispatch.py
.venv/bin/python -B source/features/type-consumers/tools/compila_shellbell_dispatch.py   --mode compile --out-dir /path/to/private/owned-build
.venv/bin/python -B source/features/type-consumers/tools/qualifica_shellbell_dispatch.py   --mode prepare --build-dir /path/to/private/owned-build   --out-dir /path/to/private/owned-prepared
```

After reviewing the frozen source/ELF/input/forecast, use `--mode execute` with
a fresh output directory to acquire the two owned cells. To rejudge them without
CPU or compiler, retain the same build and use:

```sh
.venv/bin/python -B source/features/type-consumers/tools/qualifica_shellbell_dispatch.py   --mode verify --build-dir /path/to/private/owned-build   --raw-dir /path/to/private/owned-executed --out-dir /path/to/private/owned-verified
```

`prepare` authenticates and forecasts only. Builder `--mode prepare` can also
authenticate the source/compiler without creating an object. All output
directories must be fresh and outside `source/`. Preserve the first compiler
and raw receipts. Use a bounded process runner: the builder limits stored logs
to2MiB and object readback to1MiB, while process RSS needs external control.
The [qualifier](../../features/type-consumers/tools/qualifica_shellbell_dispatch.py)
records source hashes and saves raw before judging it. The
[bench adapter](../../features/type-consumers/test/shellbell_dispatch_bench.py)
and [pure counterexamples](../../features/type-consumers/test/test_shellbell_dispatch.py)
reject typed-metadata aliases such as FALSE versus0, missing initial/backend
bindings, incorrect stack preimages and same-output state corruption.

This qualifies the owned driver, not original `BattleContext_Main`, a natural
battle or the ordinary successful caller chain. Substituting the actual game
callbacks and state requires a separate input, instruction, service and lifetime
contract. It does not follow from an owned ON/OFF pass.

## Controlled input before the damage writer

The [input preparer](../../features/type-consumers/tools/prepara_shellbell_ordinary.py)
authenticates the exact ROM above, reads ARM9 sections and overlay12 with the
existing image reader, and reads item/move/script archives with raw NARC and
ndspy agreement. It produces a **private** JSON containing ROM code and resource
bytes; keep that output out of Git. It runs no guest CPU or compiler. Use the
project environment and the dependencies in `source/requirements.txt`:

```sh
.venv/bin/python -B source/features/type-consumers/tools/prepara_shellbell_ordinary.py \
  --rom /path/to/own/Plus-EN.nds --language EN \
  --reference /path/to/productive-hgss \
  --json /path/to/private/fresh-ordinary-input.json
python3 -I -S -B -m unittest discover \
  -s source/features/type-consumers/test -p test_shellbell_ordinary_input.py
```

The reference is the productive HGSS pin described above. This preparer checks
the content hashes of `battle.h` and `battle_controller_player.c`; the separate
static reader checks clean Git roots and the wider definition set. No compiler
or package installation is needed for this step. The output must be fresh and
outside `source/`; it cannot replace an existing input.

The controlled input has attacker0, target1, single-battle type and two active
battlers. Attacker Bulbasaur has ability65, HP150/max300 and item253; target
Squirtle has ability67, HP300/max300 and item0. Tackle33 and damage−100 are
declared before HpCalc. The success flag, shared damage accumulator, hpCalc and
intermediate controller states start at zero: their later values must come
from the native writer and scripts. Unassigned arena bytes are explicitly zero.
This is an owned test input, not a captured natural battle state.

| Storage in the controlled context | Width and initialization |
| --- | --- |
| `moveNoTemp/Cur/Prev`, offsets3040/3044/3048 | three u32 fields:33/33/0; a native LDRH observes only the low half and does not redefine storage |
| `BattleMon.moves`,2D4C+192×b | four u16 fields:33/0/0/0 |
| `BattleMon.statChanges`,2D58+192×b | eight signed bytes, each6 |
| `BattleMon.hp/maxHp`,2D8C/2D90+192×b | s32/u32, distinct adjacent fields |
| OpponentData+194/+195 | u8 battlerId/battlerType; field side is derived with `battlerType & 1` |
| Item cache |516 raw34-byte records plus two declared zero padding bytes per record |
| Move cache |468 records of16 bytes at CTX+3DE; two-byte gap before itemData pointer2120 |

`make_arenas(..., full_hp=True)` supplies a negative control by changing only
attacker HP to300. Pure tests verify that difference, pre-writer state, storage
widths, stages, resource boundaries, disjoint arenas and invalid types/padding.
They use authored marker bytes, not extracted game fixtures. The owned seed
produces99 as the first LCG upper half; the actual RNG call count still needs
the complete path prediction.

One EN preparation was acquired with CPU/assembler imports and subprocesses
denied: five read-only images totaling1453120 bytes, four controlled arenas,
70 explicit fields, and scripts2/16/293 of152/204/396 bytes. A separate stdlib
verifier checked every arena byte against an independently authored field list,
unassigned zeros, hashes, mapping, scripts and the earlier overlay identity.
The first preparer called the itemData pointer `itemCache` in descriptive
metadata; the sole subsequent AST string change corrects that label. The exact
first source is retained privately; independent review verifies the delta and
unchanged arena bytes without rereading the ROM. IT input preparation has not
been acquired in this step; earlier EN/IT static coverage retains its scope.

This output is not yet a complete entry-register/stack kernel, source forecast,
admitted instruction set or original-game execution. It does not establish a
healing request, suppressed healing or a native cache/transport loader run.

The [scoped source arithmetic adapter](../../features/type-consumers/test/shellbell_ordinary_oracle.py)
adds only the Thumb forms encountered while exploring this input and a DIV
selector limited to100/8 from `DamageDivide` return address `0225318D`. It leaves
the older interpreters and MaxPP division domain unchanged. Its
[pure tests](../../features/type-consumers/test/test_shellbell_ordinary_oracle.py)
check all16 NZCV combinations for the added conditions, signed/unsigned loads,
store preimages and widths, PC pipeline arithmetic, interworking return and
zero/INT_MIN negation. They run without ROM, compiler or guest CPU:

```sh
python3 -I -S -B -m unittest discover \
  -s source/features/type-consumers/test -p test_shellbell_ordinary_oracle.py
```

These source arithmetic checks do not qualify the new forms on the CPU backend
or certify a complete continuous game path. A whole-path forecast, model-event
contract and independent review remain necessary before original execution.

## Lifetime counterproofs and remaining uncertainty

The source-supported ordinary route is AfterDamage29 →31 →32 →34 →35 →36 →37.
Unlike the pivot prefix, its item consumer can follow the flinch query. This
source path is conditional: scripts in31, faint handling, multihit reentry,
Magic Coat or additional targets, and Self-Destruct can intervene. Their neutral
outcomes must be established at a real successful boundary before composing an
execution proof. A cancelled move reaching39 bypasses37 and cannot supply it.

`BattleContext_ResetMoveStatus` clears move flags/multiplier and one battle bit;
it does not directly clear this damage word. The complete SelfTurn reset proved
in the [action-end case](action-end-source-rom-1.3.2.md) occurs later. Earlier HP
fixtures also have full attacker HP: reusing them unchanged legitimately rejects
Shell Bell. Changing HP after a captured boundary would need separate provenance.

The installed helper's clear and case1's nonzero guard make a suppressed request
a concrete hypothesis. The current readback does not prove that both occur on
one exercised successful path. No natural battle, healing loss, full caller
execution, save compatibility, physical timing or game repair is certified.
