# Full-Bag gifts: exact code, callers and script drift

Current source reconstructs the installed 658-byte gift/pickup helper and its
complete 2,048-byte initial owner in r4 EN/IT. The historical table has 110 keys,
but only **102 still match current script sites**. Eight became obsolete after
later script repairs; their exact source recipes explain the drift. The table
and game remain unchanged. A successful attribution run reports this limitation.

See the [owner](../../features/borsa/README.md),
[source-to-ROM method](../test-bench.md#linking-source-to-an-exact-rom) and
[expanded-Bag dependency case](bag-quantity-source-rom-1.3.2.md).
This owner is the free-gift helper at `023DAD00`, distinct from the inherited
4,420-byte patch at `023DEC80` and the Battle Bag cache pilot.

## Cosa farebbe un professionista di alto livello che non sto chiedendo

Verify compilation and every installed code/data region, then trace ROM command
entries back to the wrappers, source and generation recipe. Check current script
bytes rather than assuming an old fingerprint census remains valid. Distinguish
project Thumb code, native dispatcher/handlers, generated keys, original pointers,
transient relay, padding and canary. Challenge offset/window boundaries, language
revision, stale relay, fallback and bench substitution.

The old bench explicitly constructed a synthetic code/table fixture. Add an
explicit installed mode for attribution while retaining those unit tests. Require
a real return: correct result, SP, callee registers and canary alone can accept a
loop. Independent Sol 6.1 review checked raw keys, recipes, ABI, retail IT table
placement and repeated the installed execution cases separately.

## Il materiale più grezzo da cui partire

Use your own exact retail HeartGold, Plus1.1, V1.3 V4 and r4 images for each
language. Retail/base hashes, sizes and preparation are in the
[camera input table](camera-source-rom-1.3.2.md#il-materiale-più-grezzo-da-cui-partire);
r4 identities are in the [game contract](../../distribution/game-1.3.2-r4.json).
The extra V4 inputs are authenticated by the existing
[baseline contract](../../sgp131/baseline.py):

| Language | V4 bytes | SHA-256 |
| --- | ---: | --- |
| EN | 147345256 | `179edfb1ca331503f438e98f3afccfb0ab85759bf9ab88fb86c735f5fcefbf90` |
| IT | 153228136 | `2a2f0b437fca524c18b71b20feb01a1f51351e61c7c897ce73d9b3be1ee3a156` |

These are required historical inputs, not files redistributed by this case.
Obtain/prepare your copies according to the [build guide](../../README.md).
All four complete images are checked before attribution. No save, BIOS or
personal capture is required. ROMs, script members and extracted asset bytes stay
private; JSON retains hashes, offsets, arguments and observations only.

Source material includes [C and ABI header](../../features/borsa/sorgenti/),
[compiler](../../features/borsa/tools/compila_borsa.py), strict ELF loader,
[installer/table generator](../../features/borsa/tools/applica_borsa.py),
[independent reader](../../features/borsa/tools/rileggi_borsa.py) and
[signed 110-site census](../../features/borsa/permissivi-1.2.tsv).
Use `tools/py_scripts/scrcmd.json` from pret/pokeheartgold commit
`0985e8718df4f25e64d6507d89c0c97c0d288981`, SHA-256
`fbfbf438104cfc3735c3144730ed711bb882fca370a8de680db5c1d39ffaca5a`.
No charmap is needed for this code/key case; message rendering is not executed.

The separate HGSS source reference at commit
`cb614ad23449d5852b40321dc409c4143872b35c` supplies `src/script.c`,
`include/script.h`, `src/scrcmd_c.c` and script-manager facts. Original native
MW compiler/linker provenance is not reconstructed; exact bounded native-window
continuity and execution are distinguished from compilation of that source.

## I metodi e gli strumenti da usare

The recorded environment used Python3.14.7, ndspy4.2.0, Capstone5.0.9 and
Unicorn2.1.4. The actual Apple CLT Clang21.0.0 `clang-2100.4.1.1` executable had
SHA-256 `fc5e3cbba6ad54059295cad716aacb05ace8235f5f7a6031f1d8c15d24bd6d66`.
It reproduces the historical Clang21.0.0 (`clang-2100.3.34.2`) bundle's code and symbols; the original
compiler executable remains unauthenticated. The new build records compiler,
source/header, builder and loader hashes; the reader binds them to the fresh ELF,
all symbols, address metadata, blob and canary. Compiler flags remain in the
manifest and JSON. A launcher and its selected compiler are separate identities.

Set the following variables to your private inputs, pinned metadata, compiler and
output directory. Use the Python environment containing the dependencies; the
recorded commands used `.venv/bin/python3`.

```sh
python3 source/features/borsa/tools/compila_borsa.py \
  --cc "$CC" --uscita "$CASE/build"
python3 source/features/borsa/tools/attribuisci.py --language EN \
  --rom "$R4_EN" --v4 "$V4_EN" --base "$BASE11_EN" --retail "$RETAIL_EN" \
  --build "$CASE/build" --scrcmd "$SCRCMD_JSON" --json "$CASE/report-EN.json"
python3 source/features/borsa/tools/attribuisci.py --language IT \
  --rom "$R4_IT" --v4 "$V4_IT" --base "$BASE11_IT" --retail "$RETAIL_IT" \
  --build "$CASE/build" --scrcmd "$SCRCMD_JSON" --json "$CASE/report-IT.json"
python3 -m unittest discover -s source/features/borsa/test -p test_build.py -v
```

The installed/synthetic bench tests use existing input discovery. Point
`SGP_ROM_DIR` at your r4 directory and set `SGP_BORSA_ROM_NOME` to its filename
pattern containing `%s` for EN/IT, then run:

```sh
python3 -m unittest discover -s source/features/borsa/test -p test_borsa_nucleo.py -v
```

Missing private inputs produce explicit skips; skipped tests are not passes.
No full ROM rebuild or new natural capture is necessary. The reader maps inputs
read-only and materializes only ARM9 and the requested script archive. It reuses
the existing table generator through its new in-memory census entry, rather than
repeatedly duplicating complete cartridges.

### Compilation, insertion and readback

| Region | RAM | Physical r4 offset | Contents |
| --- | --- | --- | --- |
| Owner | `023DAD00` | `0012A5C0` | 2048 B |
| Compiled code | `023DAD00` | `0012A5C0` | 658 B |
| Original handler pointers | `023DB2E0` | `0012ABA0` | 127 then125, two words |
| Relay | `023DB2F0` | `0012ABB0` | four16-bit fields; initially zero |
| Generated key table | `023DB300` | `0012ABC0` | 110 increasing keys plus10 zero words |
| Canary | `023DB4F0` | `0012ADB0` | 16 B project pattern |

Compiled code SHA-256 is
`315f86bd89c49634d11bb7ef1c86746636d84af62b913a84ad2bc0b16ddf7b9e`;
key-table SHA-256 is
`f91b8fca8faa06876b282f814393663631baa70be3a418de7a56a538a8a92007`;
complete initial-owner SHA-256 is
`7d687dbae0dfc5622378500d474756c0357eb17e1446e94ec780ade04b5d089d`.
The owner is identical V4→r4 and EN/IT. Code, original pointers, generated table,
relay, all padding and canary are independently compared. Raw autoload mapping
agrees with ndspy's ARM9 sections; current owner data is uncompressed. Retail
native-window comparison uses ndspy decompression.

The generator reconstructs the V4 table from the signed census and actual V4
archive:106 unchanged entries and four regenerated entries. The actual helper
uses `(instruction_offset <<16) | FNV16`, with FNV-1a over at most32 bytes ending
at the eight-byte command. At member145@1048, the32-byte window includes two
header bytes; the census's30-byte window gives `6815`, while the installed helper
requires `C56D`. Installed execution covers that boundary explicitly.

### Callers and ABI

In r4, `gScriptCmdTable` at `020FAD00` has `[125]=023DAD09` and
`[127]=023DAD01`. The two eight-byte Thumb trampolines push r4/LR, call
`sgp_borsa_give_item` at `023DAF89` or `sgp_borsa_has_space` at `023DAD11`,
then restore r4/PC. The saved native pointers are `0204EA89` and `0204E9D9`.
Their current routines execute on strict fallback; they are not C imitations.

Retail IT places the original command table at **`020FAC78`**, whereas retail EN,
Plus1.1, V4 and r4 use `020FAD00`. The reader preserves that revision distinction.
Dispatcher `0203FD6C+108 B`, `ScriptReadHalfword` `0203FE2C+28 B` and original
handlers `0204E9D8+88 B` / `0204EA88+88 B` are identical across all eight inputs.
This does not assert equality of every command-table entry or all native code.

The native dispatcher reads `ctx->mode` at+1, `script_ptr` at+8, table at+5C and
count at+60. It consumes the opcode, loads the indexed function and executes
`BLX r1` at `0203FDCE`. The helper sees `script_ptr` immediately after the opcode;
`mapScripts` at+7C anchors its fingerprint. FieldSystem is at+80 and SaveData at
FieldSystem+0C. Actual handlers consume three halfword arguments, advance the PC
by six bytes and return FALSE.

The relay holds armed/item/requested/entered fields. It crosses the caller and
shared standard script contexts; a matching item/quantity lets a later125 use
the permissive path. Every125/127 clears **armed**, not all eight relay bytes.
Stored `entered` is diagnostic;125 recomputes current capacity. `800A` is a
transient ScriptEnvironment discard marker, initialized on every125. No new
raw-save identifier or layout is involved. This is a bounded protocol, not a
proof of every possible asynchronous or interrupted relay lifetime.

### Current script drift

Raw FAT/FNT and BTAF/GMIF parsing of `a/0/1/2` (file141) agrees with ndspy's
member extraction. All110 V4 keys match unique actual command sites. In r4,
102 remain matched; eight have no matching command/fingerprint at their old
coordinates anywhere in the archive. The current classifier has112 eligible
sites: the102 matches, eight relocated/rekeyed sites and two new Enigma guards.
Classification is a policy heuristic, not approval to add all112 to the table.

| Member / command | Old offset | Current offset | Source owner |
| --- | ---: | ---: | --- |
| 932 /127 | 167 | 197 | legacy retry/delivery repair |
| 932 /127 | 357 | 413 | legacy retry/delivery repair |
| 874 /127 | 442 | 442 | Kurt guard changes the preceding fingerprint window |
| 237 /127 | 1378 | 1384 | Kate direct-interaction repair |
| 232 /127 | 1505 | 1511 | ribbon-tail repair |
| 232 /127 | 1854 | 1860 | ribbon-tail repair |
| 938 /125 | 1705 | 1711 | ribbon-tail repair |
| 938 /125 | 1856 | 1862 | ribbon-tail repair |

Replay of [legacy script recipes](../../sgp131/legacy_scripts.py) and
[ribbon recipes](../../sgp131/gifts_scripts.py) from authenticated V4 reproduces
all six involved members232/237/757/874/932/938 exactly in both r4 images.
Independent decoded readback checks entry/branch relocation and complementary
bytes without invoking the producer. Both share the pinned decoder/metadata;
that independence is partial, not a second unrelated toolchain.
The two new member757 checks deliberately remain strict: the
[legacy archive producer](../../sgp131/legacy_archives.py) explicitly rejects
collision with the permissive table. They are not eight-key drift leftovers.

Without a matching relay, the eight moved sites now use the original handler.
This is demonstrated in isolation, not inferred solely from the count. Its
player consequence depends on quantity, script guards and retry paths; this case
does not establish that every associated gift is blocked in ordinary gameplay.

### Execution, counterproofs and limits

There are29 installed-code invocations per language: four real gift→common-give
pairs at quantities999/998/997/994, stale item/quantity pairs, Mail/Key/unknown
pocket handling, two audited blacklist sites, eight moved sites, the two strict
Enigma guards, the member145 header boundary and one native-dispatch checkpoint.
The common125 tests start with a dirty discard marker, requiring unconditional
initialization. Every normal handler invocation requires a real PC/SP/Thumb
return, r4–r11 preservation, bounded guest writes and immutable owner/table bytes.
Maximum observed stack depth is96 bytes; the4KiB allowed stack range is a fixture
limit, not a universal resource bound.

The final invocation starts at the real native dispatcher, observes its table
load and `BLX` to `023DAD01`, and stops at `0203FDD0` immediately after the callback.
The live parent frame retains r4=ctx and SP=initial−8; r5–r11 and Thumb are checked.
Opcode plus arguments advanced the script PC by eight bytes. **This is not a
complete return from the dispatcher or a naturally launched script.**

The member bytes and fingerprint windows are real; item50 and requested
quantity5 are supplied through modeled script variables. The Mail/Key/unknown
cases inject pocket5/7/8 metadata for the gate test; they do not execute a
natural use of a Mail or Key Item.

Seven variable/Bag transports remain modeled: ScriptGetVar, GetVarPointer,
Save_Bag_Get, pocket, quantity, space and add. Native halfword reads and original
command handlers execute. The separate expanded-Bag case qualifies real quantity/
consume; it is not silently imported as continuous real Bag execution here.
No message rendering, flagging of a ground pickup, natural paid transaction,
SAVE, cold restart or physical-device run is newly proved.

A false-success program restores r4/SP, preserves all expected outputs and then
loops. The old oracle accepted it after its instruction ceiling; the new oracle
requires PC at the return sentinel and rejects it. Two public bench tests cover
that counterproof and installed-code mutation. All34 methods pass (32 historical
unit cases plus two new methods); one public-bundle test and11 source/header/
builder/loader/compiler/address/symbol/blob/canary/ELF negative checks also pass.
Historical synthetic mode remains explicit; installed mode preserves the actual
code/table and permits changes only to the relay's eight mutable bytes.

Two early whole-ROM-copy prototypes exceeded the1GiB budget and remain failed
resource attempts. Sequential reads and then mapped inputs removed that overhead;
the bounded recipe replay used189,546,496 bytes OS peak RSS. Final EN/IT reader runs exited0 in1.614/1.476 seconds with OS peak RSS
365,789,184/371,851,264 bytes, under1GiB. Their receipts retain the commands,
exit codes and log hashes. Subsecond sampled RSS is not used as peak.

### Conclusions and next action

- **Documented provenance:** current C/header/compiler, historical table recipe,
  later script producers and exact input identities.
- **Reconstructed binary correspondence:**658-byte code, complete2048-byte initial
  owner, table and six whole script successors; native bounded-window continuity.
- **Demonstrated semantics:** declared isolated fixtures, relay/fallback/bounds/ABI
  and one real native table-dispatch callback.
- **Observed activation:** isolated invocations only; no new natural gameplay.
- **Unattributed or untested links:** original native toolchain, full dispatcher/
  bytecode flow, message presentation, universal relay lifetime and save/device
  behavior. Eight obsolete table keys remain in the exact game.

A possible future correction is a policy-reviewed update of affected eligibility,
not a blind regeneration of112 keys. Cost is a targeted table/recipe update plus
native script and natural saturated/retry fixtures; risk is changing intentional
refusal or granting permissive treatment to a paid/reward path. Verification must
cover each selected site, both languages, stale relay, blacklist, Mail/Key Items,
retry and raw-save acceptance. This attribution mandate changes no game bytes.
