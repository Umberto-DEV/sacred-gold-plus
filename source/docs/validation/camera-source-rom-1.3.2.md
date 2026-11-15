# Inherited camera source and current exception table

The recovered project assembly reconstructs the inherited 84-byte camera body
and its r4 EN/IT successor exactly. The instruction bytes are unchanged; two
literal-pool words now address the 68-entry exception table. Native callers and
validation remain inherited. This investigation changes verification tools and
documentation, with no new game, save, camera geometry or performance change.

The [owner](../../features/camera/README.md) and
[source-to-ROM method](../test-bench.md#linking-source-to-an-exact-rom) explain
the surrounding workflow. This follows the Party, native-getter and resident
ANIM v4 cases without repeating their gameplay campaigns.

## Cosa farebbe un professionista di alto livello che non sto chiedendo

Separate the project's Plus assembly and exception policy from native HGSS
map headers, validation and field transition logic. Trace both source→ELF→ROM
and ROM hook→body→source. Test counterexamples that produce the same final
value: checking camera output alone misses an incorrect invalid-ID clamp.
Review Thumb metadata, register conventions, literal pools, language/revision,
state dependencies and the independence of expected data. Independent Sol 6.1
reviews checked raw bytes, callers, ABI and isolated execution; a later review
checked the integrated tools. No natural activation is inferred from these
isolated calls.

## Il materiale più grezzo da cui partire

Use your own exact input images. The [r4 game contract](../../distribution/game-1.3.2-r4.json)
provides full successor hashes and sizes. The reader admits only EN/IT here.
Retail images are 134217728 bytes. Historical Plus 1.1 bases must be prepared
through the corresponding original patch route; a similarly named ROM is
insufficient. Input SHA-256 values are:

| Input | EN | IT |
| --- | --- | --- |
| Retail HeartGold | `65f02a56842b75aa92d775d56d657a56fe3fa993550b04dc20704ab82d760105` | `013d04f5512b01ad98735a5f850dc039f0ee80bc57035b3a10e8b650be690ce1` |
| Plus 1.1 | `281c2d68e442479e679d8b7e36566ade614d236151c65c9684bad6985461827d` | `7b61646c627eb67cd991dbc33d68519edd69395468ea8b326e867fe98e62d077` |

Base sizes are 127104144 EN and 131906120 IT. Keep complete ROMs, extracted
retail tables, saves, BIOS and private traces outside the public tree. No save
fixture, gameplay capture or extracted asset is required for this case.

The original local project assembly was recovered in two identical snapshots,
SHA `b49cf0b0d927b7475a5669c141b5a887bcceb204322fa8b2df360e7a0501eb95`.
Its old generated include describes an earlier allocation, so copying that
include would not reconstruct the final 1.1 body. The public
[camera.S](../../features/camera/sorgenti/camera.S) preserves its instruction
body, replaces historical workspace notes with technical comments and adds
`.thumb_func`. That annotation changes the ELF symbol metadata, with identical
code bytes. The new compiler generates constants for the two final layouts.
This is a current reconstruction, not authentication of the historical assembler.

## I metodi e gli strumenti da usare

Use targeted assembly, strict ELF `.text` loading, source/build readback,
raw ARM9 autoload mapping against ndspy, native-window comparison and isolated
Unicorn execution. Dependencies are in [requirements](../../requirements.txt),
with Clang supporting ARMv5TE. Run from the repository root:

```sh
python3 -m venv .venv
.venv/bin/python3 -m pip install -r source/requirements.txt
.venv/bin/python3 source/features/camera/tools/compila.py \
  --layout base11 --uscita /tmp/sgp-camera-base
.venv/bin/python3 source/features/camera/tools/compila.py \
  --layout r4 --uscita /tmp/sgp-camera-r4
.venv/bin/python3 source/features/camera/tools/attribuisci.py \
  --language EN --retail /path/to/retail-en.nds \
  --base /path/to/plus-1.1-en.nds --rom /path/to/exact-r4-en.nds \
  --built-base /tmp/sgp-camera-base/camera.bin \
  --built-r4 /tmp/sgp-camera-r4/camera.bin --json /tmp/sgp-camera-en.json
PYTHONPATH=source .venv/bin/python3 -m unittest \
  sgp12.test_lib.TestSorgenteCameraRecuperata \
  sgp12.test_lib.TestTabellaCamera sgp12.test_lib.TestRegistroCamera -v
```

Repeat the attribution command with `--language IT` and the three IT images;
the same compiled payloads apply. The compiler accepts `--cc`; it records the
resolved executable hash/version, exact command, source/loader hashes,
constants, ELF symbol and blob hash. This reconstruction used Apple Clang
21.0.0 (`clang-2100.4.1.1`), invoked driver executable SHA
`ed6f5284033aa2aae6a58427c25ba3ab119947b40365627b24e5d51a4b70a1cd`.
No linker, external symbols or external relocations are needed. The reused
[ELF loader](../../features/anim/tools/carica_text.py) rejects unsupported
allocated sections/relocations. ndspy 4.2.0 and Unicorn 2.1.4 were used.

Success means exit 0, both 84-byte build/readback comparisons passing, exact
input admission, the table/canary and native windows matching, 1632 isolated
cases with no errors, and five rejected RAM mutants. The JSON contains hashes,
addresses, offsets and coverage; it contains no personal input paths or game
bytes. For a standalone installed-code check, the existing CLI remains:

```sh
.venv/bin/python3 source/features/camera/tools/oracolo.py \
  /path/to/exact-r4-en.nds --json /tmp/sgp-camera-oracle.json
```

That standalone oracle does not authenticate the full input: use the attribution
reader to establish identity first. Its existing `--attese id:value,...` option
replaces expected Plus exceptions. It is an explicit diagnostic override,
not a substitute for the canonical input and policy checks.

## Source, insertion, addresses and callers

[The composer](../../sgp12/blocchi/camera.py) checks inherited code/pool and
writes table136B at `023D8A10`, canary16B at `023D8A98` and pool pointers
`023DEBD4/023DEBD8`. It does not assemble a new body during normal composition.
The reconstruction establishes where that inherited body came from.

| Range | Logical RAM | Physical base EN/IT | Physical r4 EN/IT |
| --- | --- | --- | --- |
| Native hook, 4B | `0203B400` | `0003F400` | `0003F400` |
| Hook target literal, 4B | `0203B418` | `0003F418` | `0003F418` |
| Plus body/pool, 84B | `023DEB8C` | `0011790C` | `0012E44C` |
| Exceptions | `023DEB6C` base / `023D8A10` r4 | `001178EC`, 32B | `001282D0`, 136B |
| Low state byte | `023DFFFC` | `00118D7C` | `0012F8BC` |
| Native validator, 18B | `0203B268` | `0003F268` | `0003F268` |
| Native caller window, 44B | `020530F4` | `000570F4` | `000570F4` |

These base/r4 ranges are uncompressed ARM9 static/autoload bytes, not overlay
addresses. Physical offsets are derived from each image's header/module
parameters and separately checked with ndspy sections. The project's raw
readers share layout validation; they are not two wholly independent parsers.
Retail ARM9 is decompressed by ndspy; these physical offsets must not be
applied to compressed retail input.

The native entry shim loads literal `023DEB8D` and branches Thumb to the Plus
body. Entry `r0` is map ID; return `r0` is camera type. Native validator
`0203B269` runs first: unsigned IDs >=540 call `GF_AssertFail` at `0202551C`
and become map1 **if the assertion returns**. The body preserves SP and r4–r11;
r3 is caller-saved and was already overwritten by the shim. The deepest tested
stack extent is 16 bytes; writes stay within that stack. No heap, file I/O,
private task, graphics buffer or persistent write occurs in this getter.

Pool offsets +0x40/+0x44/+0x48/+0x4C/+0x50 contain validator, state, exception start/end
and map-header base respectively. The body reads the state's low byte: zero
selects Classic, any nonzero selects Plus. Classic extracts bits12..17 from
word+20 of the 24-byte record at `020F6BE0 + 24*mapId`; Plus scans sorted packed
u16 `(mapId<<4)|camera`, returning the low nibble or default11. The policy has
68 entries; the public table is project policy, not an extracted retail table.
This getter does not own state persistence or establish any save's current setting.

BL sites `02053102/02053112` both call `0203B400`. In their authenticated
44-byte window, the connection branch reads local camera and compares/asserts
a match; the alternative branch writes the getter result into local camera.
The window SHA is
`2bc9be117d5169ba402beb652c815a01f362672e78cca0d36bc95739722ff1ab`;
the validator window SHA is
`c32286b7bac5e5751f7b26d0f2d1bbeae47983ea1f9ce1414d3f75c359bba4ac`.
Both windows are identical in retail EN/IT, bases and r4. Source-only HGSS
reference `field_warp_tasks.c`, revision
`cb614ad23449d5852b40321dc409c4143872b35c`, supports the names/interpretation;
it is not an original HGSS C-to-object reconstruction or an exhaustive caller scan.

## Results, counterexamples and remaining gaps

- **Documented provenance:** identical recovered project assembly snapshots,
  public instruction body, generated layout constants and composer ownership.
- **Reconstructed binary match:** inherited body SHA
  `0832f466100bf990210485f7d43a64d908985802b548709099a0d80d3f7cdd95`;
  r4 body SHA `0c756c25d4a08bee9fbe2496c510a45de811bfaba449f3eb0a0e36cdb63ec351`.
  Both match exact EN/IT readback. Differences are byte offsets48/49/4C/4D
  (hex), confined to the two pool words; all instruction bytes are identical.
- **Demonstrated isolated semantics:** per language, states0/1/2 each execute
  540 valid IDs and 540/1000/FFFF/FFFFFFFF: 1632 cases. The actual installed
  hook/body/validator run without replacement. Only assertion transport is
  stubbed to return; normalization, assertion count, result, PC/SP/Thumb,
  r4–r11 and stack write-set are checked. This does not exercise error UI.
- **Counterexamples:** RAM-only changes to clamp1→0, exception start, first
  value, state pointer and hook target all fail the relevant observation.
  Every range is restored and the Unicorn translation cache invalidated;
  neither input ROM nor save is written. The former oracle accepted the
  clamp mutant because invalid results were merely printed. The strengthened
  oracle rejects it even when map0/map1 share the same final Plus default.
- **Activation still unobserved:** no new natural field transition, visual
  geometry, connection assertion in gameplay, latency or physical-device run.
  Isolated tests do not certify all 68 map views or compatibility of all saves.

The Python expected loop is distinct from the installed Thumb loop, but its
public exception policy is shared with the historical writer. Table readback
and isolated execution prove implementation/format consistency, not independent
editorial correctness of all 68 values. Native map-header data remain private.
The current assembler reproduces bytes; the original compiler executable and
full native C build remain unauthenticated.

The focused unit run executed 12 methods successfully; four old intermediate
composer tests skipped without their configured legacy fixture directory.
They are not reported as passing. Exact current EN/IT reader/execution checks
ran separately without skips. Final measured peak RSS was about866/893MiB
EN/IT and elapsed time under one second per command on this host. A prior
reader retained too many images and exceeded the intended1GiB budget; it was
revised to retain only small windows between inputs. Sampling alone had missed
that peak, so final peak figures come from the OS `time -l`, not periodic RSS.
No reproducible full-ROM outputs or new heavy runtime builds were retained.

A possible future optimization is a different search over68 entries, but no
CPU bottleneck is measured and changing code would require ABI, all-map,
caller and natural-transition checks. No game optimization is proposed for
installation. The reusable result is the recovered recipe, exact readback,
stronger bounds oracle and RAM counterexamples for subsequent attributions.
