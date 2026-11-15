# Native complete Mon PP-Up setter: source, exact ROM and four cipher phases

This case follows `SetMonData(mon,62,&zero)` from the HGSS C definition to
the selected native Thumb path and its complete encrypted Mon input. It extends
the [Box setters](native-box-pp-setter-source-rom-1.3.2.md) and
[trainer move prefix](native-trainer-first-move-prefix-source-rom-1.3.2.md).
The extra100 party bytes have their own PID cipher key. They are accessed here;
the prefix case's untouched opaque tail was not a valid substitute.

## Question and falsification

For flags0, valid initial checksum and PID`0x4000`, does one uninterrupted
native call decrypt party100 with the PID, decrypt Box128 with its old checksum,
check that checksum, write PP-Up0 through the internal default/leaf62, then
encrypt party100 with the PID and Box128 with the new checksum?

Two owned inputs start with PP-Up3 or0, move310, currentPP15 and heldItem0.
Their Box keys are`0x02AB` and`0x02A8`; both outputs converge to key`0x02A8`.
The Up0 input is idempotent. A third run repeats Up3 with observation OFF.
Equal counters and final bytes cannot distinguish the first two inputs.
Likewise, omitting both party passes or using the same wrong key twice leaves
the party ciphertext unchanged. Every phase's seed, read, preimage and store
must therefore agree with the independent owned plaintext calculation.

## Inputs, provenance and compilation limits

Supply your own legally obtained exact inputs. Do not add ROMs, extracted game
data, saves, BIOS or private execution records to Git.

| Current input | Bytes | SHA-256 |
| --- | ---: | --- |
| Plus EN |152786844|`2e30d6960bb059615fca7527700d86f8282e82ccbe99bf62e22f027453dc3d3d`|
| Plus IT |159029760|`13ebac02bdea3036511773587e6603ce6834e25f4b13d1a4662c3e954bfd5d4a`|

Both current inputs have internal game codeIPKE/revision0, ARM9 stored at ROM
`0x4000`, load base`0x02000000`, size`0x12B8E4`, entry`0x02000800` and plain
ARM9 storage. The Italian presentation retains the common USA executable.
This does not establish a matching Italian retail source build.

The productive source is the
[HGSS fork at cb614ad](https://github.com/ctrl-cheeb-del/pokeheartgold/tree/cb614ad23449d5852b40321dc409c4143872b35c).
`src/pokemon.c` has SHA-256
`1d784ece4650b84e426a437ee20e4a926475fc20ef761e67440d0c0136548fa3`;
`include/pokemon_types_def.h` has
`032888003b7a68733dedb83d55decc43cc4202b6ca66b284f62256aacb02e24d`.
The CLI authenticates a clean commit and four participating source/header files.

| Complete productive definition | Line / UTF-8 bytes | SHA-256 |
| --- | --- | --- |
|`SetMonData`|886 /620|`768f3eedda5da496f027a8137452f90e4e937e730f8982d4e09613ce34455644`|
|`SetMonDataInternal`|907 /1252|`8a0a62dde61696b05c20f64f082ea7a9bb7f5b74ead3bb66172db92b661e85f1`|
|`SetBoxMonDataInternal`|972 /12824|`c6446593099b57375e5d6f46985c0f3d9e014f4e8ee63fa9fe0ffa16b65757fe`|

Extents run from the first return-type/qualifier character through the matching
closing brace, excluding a trailing newline, without whitespace normalization.
The [definition reader](../../features/trainer-strategy/tools/confronta_box_move_pret.py)
distinguishes definitions from prototypes and callsites. In newer PRET HeartGold
`6bf138d6035aa6b43d6f8f4132a12df70f86dcec`, the outer and Box-internal definitions
agree; Mon-internal is1256 bytes, SHA-256
`4ec51f90996250a878d40bf663ed39fcb49c16f08b7204c3a5d0abe339e9f0a7`.
Its excluded BALL_CAPSULE case changes a cast from`CAPSULE` to`BallCapsule`.
The selected default is unchanged; the entire function is not byte-identical.

This is native HGSS code retained through retail→inherited base→Plus, rather
than a newly compiled Plus payload. No installer or new C compilation is needed
to execute its installed bytes. Original Metrowerks Thumb objects/maps and a
matching original C build remain unavailable here. Source alignment and finite
semantic equivalence do not claim reconstructed C code generation. The
[source-to-complete-ROM guide](../test-bench.md#from-the-source-tree-to-the-complete-rom)
separates that remaining requirement from the existing Plus composition route.

## Installed locations, control flow and ABI

| Selected code | RAM range, end excluded | Current plain ROM offset | Bytes / starts |
| --- | --- | --- | --- |
|Mon entry/check|`0206EC40..0206EC78`|`0x72C40`|56 /25|
|valid path/return|`0206EC96..0206ECCE`|`0x72C96`|56 /24|
|Mon internal prefix|`0206ECD0..0206ECDC`|`0x72CD0`|12 /6|
|Mon internal default|`0206ED68..0206ED70`|`0x72D68`|8 /3|
|Box internal leaf62/return|`0206F104..0206F114`|`0x73104`|16 /8|

These are148 new code bytes/66 starts. With retained cipher, localLCG,
checksum, block selector and internal-dispatch code, execution admits372 code
bytes/173 Thumb starts, plus528 data bytes. The resource reader records every
component digest, independent direct-ROM and ndspy readback, and current EN/IT
identity. Error paths, the Mon-internal status/stat/mail/capsule cases and its
24-byte jump table are excluded.

The actual default calls `SetBoxMonDataInternal` at`0x0206EDE8` directly.
It does **not** call the outer Box API at`0x0206ED70`. The Box attribute table
starts`0x0206EE3C`; row62 at`0x0206EEB8` contains little-endian`C6 02`.
Signed offset`0x02C6` plus dispatch PC base`0x0206EE3E` selects`0x0206F104`.
The table is data, not admitted executable code.

| BL site | Native target | Significant inputs / return LR |
| --- | --- | --- |
|`0206EC58`|`020725E0` decrypt|Mon+136,100,PID4000 /`0206EC5D`|
|`0206EC64`|`020725E0` decrypt|Mon+8,128,old checksum /`0206EC69`|
|`0206EC6E`|`020725E8` checksum|Mon+8,128 /`0206EC73`|
|`0206EC9C`|`0206ECD0` Mon internal|Mon,62,Value /`0206ECA1`|
|`0206ED6A`|`0206EDE8` Box internal|Mon,62,Value /`0206ED6F`|
|`0206ECB0`|`020725D8` encrypt|Mon+136,100,PID4000 /`0206ECB5`|
|`0206ECBA`|`020725E8` checksum|Mon+8,128 /`0206ECBF`|
|`0206ECC8`|`020725D8` encrypt|Mon+8,128,new checksum /`0206ECCD`|

Owned entry: R0=Mon`0x022F0000`,R1=62,R2=Value`0x022F0200`; R3..R12 distinct
cookies, SP=`T=0x023FD000`, odd LR=`0x022F0181`, CPSR=`0x6000003F`.
Mon is236 bytes: header8, encrypted Box128 and encrypted party100. Flags at+4
are0. PID4000 gives A,C,B,D physical order; PP-Up0 lies at Mon+84.
Value is a separate read-only four-byte zero; actual leaf reads only its low
byte at`0206F106` and stores one byte at`0206F10E`.

Outer frame16, bridge8, Box internal24+80 locals, and selector16 produce a
144-byte peak. Leaf SP=T−128; local cipher seed is at T−24. Reused stack
contents are preserved between native callees. Guards are16 bytes before and
after Mon,16 around Value and56 below the frame. The before-Mon guard occupies
an additional page at`0x022EF000`: the complete fixture has **8 pages/32768 bytes**.
This is host fixture mapping, not DS heap usage or recovered game RAM.

The void return is R0=`0x2B9B`,R1=0,R2=`0x4AA02329`,R3=`0x0206ECCD`;
R4..R12 and SP retain entry values, LR=`0x0201FF59`, CPSR=`0x6000003F`.
Do not interpret R0 as PP-Up, a Boolean result, or the outer Box API residue.

## Repeat with your own inputs

Use the project Python environment described in [source README](../../README.md).
Verified packages: ndspy4.2.0, Capstone distribution5.0.9 (module5.0.7),
Unicorn2.1.4/CPU model17. This model verifies the selected instruction semantics,
not ARM946 silicon timing. No compiler, SDK libraries, filesystem model or
extracted trainer/save fixture is required. Source-only tests and discovery do
not require starting a guest.

Run from the repository root. Replace `/path/to/private` with an existing private
directory and use fresh files/directories for each invocation:

```sh
python3 source/features/trainer-strategy/tools/rileggi_mon_ppup_setter.py \
  --rom /path/to/plus-en.nds --it-rom /path/to/plus-it.nds \
  --json /path/to/private/resources.json
python3 source/features/trainer-strategy/tools/qualifica_mon_party100.py \
  --json /path/to/private/owned100.json
python3 source/features/trainer-strategy/tools/congela_mon_ppup_setter.py \
  --rom /path/to/plus-en.nds --json /path/to/private/input.json
python3 source/features/trainer-strategy/tools/attribuisci_mon_ppup_setter.py \
  --mode prepare --rom /path/to/plus-en.nds \
  --reference /path/to/productive-hgss --input-contract /path/to/private/input.json \
  --qualification /path/to/private/owned100.json --out-dir /path/to/private/prepared
```

The owned qualifier executes four synthetic451-instruction loops, each with
50 halfword reads/stores: PID encrypt/decrypt, wrong-key counter and OFF.
It loads no ROM program. Independent scalar full-state arithmetic, the retained
Thumb interpreter and the unchanged CPU producer agree. OFF records endpoint
pages/counters but no per-instruction native trace; source forecast hashes are
labeled separately. The freeze prepares new owned plaintext100 and encrypts it
with PID4000; it contains no extracted or player data and makes no claim that
arbitrary party-field values constitute a legal in-game Pokémon.

Change `--mode prepare` to`--mode matrix` and choose another fresh output
directory to execute the three original native API calls. The producer has one
Uc context and one `emu_start` per call, cap8192, timeout1000000 microseconds.
It receives fetch/access admission metadata, never predicted values or a host
phase callback. Raw files are saved before acceptance. Keep that directory.
Then use `--mode verify --raw-dir /path/to/private/matrix` and a fresh
`--out-dir` to rejudge it without executing the CPU or invoking a compiler.
This verifier still needs ndspy/Capstone; it is not standard-library-only.

For historical mapping, use
[`rileggi_mon_ppup_lineage.py`](../../features/trainer-strategy/tools/rileggi_mon_ppup_lineage.py)
with `--retail RETAIL --base BASE11 --v4 V4 --rom CURRENT --language EN`
(or IT) and`--json FRESH_PRIVATE_JSON`. Its manifest pins are inherited from the
[selector lineage](native-mon-substructure-source-rom-1.3.2.md).
It locates the unique Mon entry, follows actual BL/default/table targets and
compares244 bytes:148 new,82 retained internal code,2 row bytes and12 primitive
entry bytes. BLZ or nonlinear owners retain null physical plaintext offsets;
decode the owner rather than applying the current plain offset formula.

ROM-free counterexamples:

```sh
python3 -m unittest discover -s source/features/trainer-strategy/test \
  -p 'test_mon_ppup_*.py'
python3 -m unittest discover -s source/features/trainer-strategy/test \
  -p test_mon_party100.py
```

## Evidence, coverage and remaining work

Current EN/IT readback and244-byte lineage in
all eight retail/base1.1/V4/current images agree. Two retail owners are BLZ;
six plain owners provide11 independent physical reads each. Four owned-loop
CPU tests and25 ROM-free tests passed. The pre-CPU forecast is5827 Thumb,
173 distinct starts,1128 reads,534 stores,144-byte stack; both inputs converge
to complete Mon SHA-256
`02a5249820ab97db2799b0e18ee906b3154915a4f42a6084bce0be4a761c9beb`.
The three original API runs passed on the first attempt:17481 instructions
total, each5827 Thumb/0ARM,173 distinct starts,1128 reads,534 stores and
144-byte stack. Each has5828 callbacks including the return stop. All8 pages,
the complete void ABI and each observed intermediate agree with the frozen
source forecast. OFF has the same endpoints/counters and empty observations.
The two ON inputs converge to identical complete final maps despite differing
initial ciphertext, keys and intermediate evidence.

Success requires all16 registers before every observed instruction, exact
next-PC order, read values, store preimages, every final page and inverse replay.
There must be228 local-seed stores and228 cipher halfword stores, including
50 party halfwords in each direction, plus128 checksum plaintext reads.
The suite rejected24 transcript forgeries against the native records, including same-count input camouflage,
omitted party phases, wrong seed/field/width, old stack depth/key, metadata types
and injected host writes. Source-only dry rejection was checked separately
before original execution. Mutants are judged and released one at a time.
CPU-free verification passed again with Unicorn/assembler imports and compiler
subprocesses denied; only read-only pinned Git queries were admitted.

First native matrix:2.252s/74530816-byte peak RSS; CPU-free rejudgment:
1.924s/74055680 bytes. These are bounded host validation costs, not game speed
or DS memory measurements. No native run was repeated to tune an expectation.

Independent review used a separate Thumb checker, without importing the case
benchmark, its predictor or Unicorn:11654 full16/next-PC states,2256 reads,
1068 stores, all8 pages in forward/inverse replay and45 current/frozen runtime
sources agreed. Its checker also rejected all24 public transcript mutations.
The first input-dependent state differs at`0206EC60` in the old checksum R2,
despite identical final CPU state, maps and counts. This is why binding only
the endpoint to a claimed input would produce a false attribution.

Documented provenance, installed-byte equality and a finite API semantic result
remain separate from reconstructed original compilation and natural activation.
This case excludes other attributes/slots/PIDs/flags, corrupt-checksum paths,
save compatibility, hardware, Italian guest execution and the complete trainer
constructor. The ResetPpUp caller is a future composition with different PP/key
intermediates and a larger instruction budget; standalone passes cannot simply
be concatenated to claim it ran. No game behavior, ROM, ABI, ID or save changed.

The reusable additions are the Mon reader, two-key owned fixture,50-halfword
qualifier, contextual access owners and CPU-free raw verifier. They reduce the
next attribution's preparation work without broadening earlier sealed claims.
No game optimization is justified by this result; any later change needs its
own measured benefit, cost/risk and maintainer decision.
