# Native Translate: reconstructed bytes, dispatch data and native writer

**Verified host scope:** twelve guest runs over four literal CPU/RAM/policy
groups,48 earlier-field comparisons, four OFF checks and four writer controls.
Fourteen tests pass without skips. One value-only default-handler model remains.
This does not retroactively upgrade the
modeled Translate boundary in the [complete Send case](native-fs-send-native-callees-source-rom-1.3.2.md).

## Cosa farebbe un professionista di alto livello che non sto chiedendo

Distinguish instruction bytes, literal pool, initialized dispatch table and
the selected handler. Compare retail→inherited base→V4→current in each language
without assuming identical addresses. Reconstruct the actual input image
forward from an observed digest and native write journal. Freeze only fields
that the earlier model qualified; native volatile registers and saved stack
are separate obligations. A final output match alone cannot identify whether
the host model or the native STR wrote the file error.

## Il materiale più grezzo da cui partire

Use the exact [Send input set](native-fs-send-source-rom-1.3.2.md#il-materiale-più-grezzo-da-cui-partire)
and complete native Send campaign with its source identities, raw files,
replay configuration and ancestor recipes. Current r4 EN is152786844 bytes,
SHA-256`2e30d6960bb059615fca7527700d86f8282e82ccbe99bf62e22f027453dc3d3d`;
localized IT is159029760 bytes,
SHA-256`13ebac02bdea3036511773587e6603ce6834e25f4b13d1a4662c3e954bfd5d4a`.
They use internal IPKE revision0. Retail Italian IPKI is a different image.
ROMs, extracted data, RAM, raw captures, saves and BIOS remain private.

The counterpart is `lib/NitroSDK/src/fs/FS_command.c::FSi_TranslateCommand`,
file SHA-256`07333027376e89d3ecc243b0022d089f9c3153cfe4226ef433e086cbe9777e60`,
at [reference cb614ad23449d5852b40321dc409c4143872b35c](https://github.com/ctrl-cheeb-del/pokeheartgold/tree/cb614ad23449d5852b40321dc409c4143872b35c).
`FS_command_default.c` has SHA-256
`040f053d87d157231bcd051731eee8bf27768a9103940b6c4016f9cf703ca513`;
its nine-entry `fsi_default_command` declaration names FINDPATH at index4.
Its handler body is not qualified by this case's four-byte fetch gate.
The [newer PRET references](../test-bench.md#using-newer-pret-references) remain
useful research inputs; their unmaterialized SDK wraps do not replace this pin.

| Region | Current RAM | Current physical ROM offset | Bytes | SHA-256 |
| --- | --- | --- | --- | --- |
| Translate instructions |`0x020D68C0`|`0x000DA8C0`|396|`9c42ca76b2fa192199ad1687f07ea9bcf54a90f5b6fe950c6fd9cbb641fb719d`|
| Instructions plus literal pool |`0x020D68C0`|`0x000DA8C0`|400|`f1df0f035e516cdfff9df4668530ca636f88b9a1a70d86804b9671c8bce7341a`|
| Default table |`0x0210E124`|`0x00112124`|36|`a2a3fe2a981c9967141752f3228d54c59d73c639339443bbe0ef04f13319d287`|
| Default handler stopped gate |`0x020D6DB0`|`0x000DADB0`|4|`462b796a6c11d4277cd269fd03b7c46c2e0de0394c8071aa4a7a8d079be7bb87`|

These are retained main ARM9 bytes. The final POP is at`0x020D6A48`; four-byte
pool at`0x020D6A4C` contains the table address. Do not decode that word as an
instruction. Conversely, the nine B instructions at`0x020D6924..0x020D6944`
are a callback dispatch switch, not the external data table. The next function
prologue at`0x020D6A50` is outside this extent.

### The retail Italian counterexample

All eight lineage inputs have identical396-byte instruction regions and
identical36-byte table contents, with slot4 selecting`0x020D6DB0`. Seven have
the current400-byte extent. Retail IT instead has pool value`0x0210E0B8`,108
bytes below the current table address. Its whole400 SHA-256 is
`2f23783562dc64f44b7dfdd081981ffb147a3011b4ecf3af79c77cf2968f2c0c`.
Only extent byte offsets396 and397 differ. Base1.1 IT, V4 IT and current
localized IT use the current literal. Do not claim eight whole-payload matches
or infer an original Italian build from the current localized game's label.
Historical compressed-image physical offsets remain absent where the reader
cannot independently establish them. No historical activation is proved here.

## I metodi e gli strumenti da usare

The [recovered assembly](../../features/trainer-strategy/sorgenti/fs-translate.S)
is a comparison recipe with no installer. Use the existing project environment
for ndspy, Capstone and transitive bench imports; the standalone freezer needs
only Python's standard library. The qualified compiler is Clang21, SHA-256
`fc5e3cbba6ad54059295cad716aacb05ace8235f5f7a6031f1d8c15d24bd6d66`,
with `--target=armv5te-none-eabi -mcpu=arm946e-s -marm`.
Provide a clean checkout of the pinned reference for the header checks.
For a prospective repetition, prepare the component receipt and run the
[freezer below](#frozen-fields-and-explicit-model-differences) **before** these
compiler commands. Re-exporting later checks equality, not the earlier export's
chronology.

```sh
python3 -B source/features/trainer-strategy/tools/compila_fs_translate.py \
  --uscita "$PRIVATE/translate-recipe" --cc "$CLANG" --reference "$HGSS_REFERENCE"
SGP_FS_TRANSLATE_RECIPE_DIR="$PRIVATE/translate-recipe" \
  python3 -B -m unittest discover -s source/features/trainer-strategy/test \
  -p test_fs_translate_recipe.py -v
python3 -B source/features/trainer-strategy/tools/rileggi_fs_translate.py \
  --retail "$RETAIL" --base "$BASE11" --v4 "$V4" --rom "$R4" --language EN \
  --recipe-dir "$PRIVATE/translate-recipe" --json "$PRIVATE/translate-lineage-en.json"
```

Repeat the lineage command with the corresponding IT inputs and `--language IT`.
Outputs must be fresh and outside `source/`. The builder reuses the qualified
compiler/ELF pipeline and verifies400 bytes plus the entry symbol. The separate
ELF reader checks ELF32 ARM, bounds, a single `.text` and no text relocations.
It separates99 instructions from the pool; tests reject missing/changed pools.
Physical readback and decoded ARM9 sections agree for current/V4 components.
The observed object SHA-256 is
`230b5b3a3490447dff68e2aafe9ebce52cd1c33308b325c3bedd1f9a07d3c802`.
This is exact recovered assembly, not original Metrowerks C code generation.

The actual build passes18 original-header dependencies and ARM32 layout checks:
FSFile72,FSArchive92, archive flag28/proc84/proc_flag88/sync_q12, SYNC4,
IS_SYNC`0x200`,IS_ASYNC`0x100`, and FSResult values0/1/2/6/7/8.
Both object tests pass without skips when the recovered object is supplied;
without it the object-dependent test is explicitly skipped.

### Actual entry and forward-derived whole image

At the earlier Send guest's actual Translate entry, R0=file`0x023BEDD0`,
R1=command4, SP=TOP−312, LR=`0x020D7754`, CPSR=`0x2000001F`;
TOP=`0x023BEEC0`,archive=`0x021E3654`. File.status=`0x45`,error=BUSY2,
archive flags=`0x13`,proc_flag=0. Complete16-register context, frame416,
archive92 and guard56 are retained from that observed isolated checkpoint.

No whole-RAM hash was recorded at that intermediate boundary. Start from the
authenticated **P75 Send before-image**, including its qualified code overlays,
and replay the first17 actual native writes (15 Send+2 ExecuteSync PUSH words).
Check each address, PC, preimage and source prediction. The prefix has93 native
contexts, ending at the original BL`0x020D7750`. Verify its LR delivery and
resulting frame/archive/guard against the actual Translate entry.

Four groups' complete images were reconstructed this way, with eight independent
streaming hash checks covering observed-before and derived boundary images.
This is a derived identity, not an extra whole-RAM capture. A readonly transfer
from final RAM is invalid: the old Translate model and later native callees
write memory. New Translate400/table36/defaultgate4 overlays still require their
own delta accounting before any P76 guest.

### Frozen fields and explicit model differences

The prospective exporter consumes the complete parent report and a private
component receipt exported from your own inputs. It authenticates their reported
relationships, not their ROM provenance by itself. Native preparation must
also verify source, ROM, object and raw identities independently.

The receipt has `case: "P76"`, `new_CPU_executed: false`,
`new_compiler_invoked: false` and `roms.EN`/`roms.IT`. Each language contains
`regions` named `code`, `code_and_pool`, `table`, `default_gate`; each region
records `ram` as a hexadecimal string, `bytes`, `sha256` and `local_hex` read
from that owned ROM. `default_slot4` records `ram: "0x210e134"` and
`target: "0x20d6db0"`. Sizes/hashes are the table above, including the separate
396-byte code region. Keep this extracted-byte receipt private. Produce it
before freezing or compiling the new component:

```sh
python3 -B source/features/trainer-strategy/tools/attribuisci_fs_translate.py \
  --parent-config "$SEND_NATIVE_REPLAY" --export-components \
  --json "$PRIVATE/translate-components.json"
```

This mode independently compares physical and decoded current ROM components
without invoking the compiler, parent guests or a new Translate guest. Its
receipt metadata may differ from this campaign's earlier offline receipt;
compare component identity and bind your actual receipt hash in the contract.

```sh
python3 -I -S -B source/features/trainer-strategy/tools/congela_fs_translate_contract.py \
  --parent-report "$SEND_NATIVE_REPORT" --component-receipt "$COMPONENT_RECEIPT" \
  --json "$PRIVATE/translate-fields.json"
python3 -I -S -B -m unittest discover -s source/features/trainer-strategy/test \
  -p test_fs_translate_freeze.py -v
```

The export SHA-256 is
`1bb3164b492c0ff06abf5884852e1956291b3de526310c862c92ab33f9a474a0`:
16 origins, exact input/journal/component hashes and earlier stable output
fields. It predates the new compiler/oracle/guest, after body inspection;
known inputs, not a blind experiment. Two source-only tests pass. Independent
review verifies re-export equality and336 rejected stable-field mutations.

Only register indices1(R1) and14(LR) are excluded from earlier-model comparison:
native source analysis predicts R1=default target`0x020D6DB0`,LR=`0x020D6984`,
where the old model preserved4/`0x020D7754`. Native PUSH24 occupies frame416
offsets80–103; compare earlier-model frame spans0–79 and104–415 exactly. A new
native oracle must independently verify all24 saved bytes and the full image.
These explicit exclusions do not prove full ABI or stack equivalence.

### Native execution and writer controls

The selected source path sets archive flags13→213, loads the literal/table,
uses actual BLX`0x020D6980` to the default slot4, then clears flags213→13 and
writes FILE.error at native STR`0x020D6A40`. The positive default model must
return FSResult0/1 at actual LR, preserve other registers/CPSR as a declared
service policy and perform **zero RAM writes**. This does not establish the
default handler's native ABI or filesystem effects.

The acquired normal/OFF/counter runs observe39 native contexts,9 stores,14 reads,
one service plus stopped return=41 callbacks,24 bytes below entry SP. Final
CPSR is`0x2000001F`, including success FSResult0: flags reflect the
sync-mode comparison, not R0. PROC_ASYNC, callbacks and non-sync paths remain
excluded. The default handler's original prologue alone needs184 bytes;
it must be intercepted before execution rather than admitted within this scope.

The [source oracle and collector](../../features/trainer-strategy/test/fs_translate_bench.py)
have separate source prediction and original-instruction execution paths.
Four synthetic tests cover dispatch, FSResult/CPSR, transient flags,
store preimages and typed scope rejection. Run them separately from the
object-dependent checks:

```sh
python3 -B -m unittest discover -s source/features/trainer-strategy/test \
  -p test_fs_translate_bench.py -v
```

Independent static ARM decoding agrees over16 actual origins ×2 declared
profiles, including full contexts, store preimages, reads and four checkpoints.
This is source-oracle validation, not new guest activation.

The negative `early_error` service also writes FILE.error before returning.
It can converge in every final field and whole RAM while native STR sees
result0/1 instead of BUSY2. Old frozen fields may correctly accept both paths;
host-write ledger and native store preimage must distinguish their writers.
All four actual early-error pairs have identical initial and final whole RAM,
returned CPU, native flow and reads. Their sole native-store transcript difference
is STR`0x020D6A40`'s preimage: BUSY2 versus the already supplied result. The host
ledger has zero writes in normal execution and one in the declared negative.
Disguising policy, services, host ledger and checkpoints still fails on the
actual native store preimage, with39 native records/41 callbacks unchanged.
All48 old-field comparisons pass, including16 negative provenance members:
their explicit writer/activation claim remains false. Four OFF pairs preserve
CPU/RAM/models/checkpoints exactly with zero projection.

No resource recovery,
game optimization, natural filesystem/card/thread completion, higher-caller
integration, ARM946 timing/IRQ delivery or save/hardware coverage is established.

The producer authenticates all parent raw/source identities, the pinned clean
SDK/header/recipe/compiler receipt and the current physical/decoded/object
bytes. It reconstructs the before-boundary image, verifies the17-store journal,
then overlays only400+36+4 bytes and records their exact deltas. No intermediate
guest checkpoint is reinjected. Only Translate's396 instruction bytes are
admitted; the default prologue, literal pool as code, IRQ/callback/async helpers
and writes to pool/table are rejected.

```sh
python3 -B source/features/trainer-strategy/tools/attribuisci_fs_translate.py \
  --parent-config "$SEND_NATIVE_REPLAY" --recipe-dir "$PRIVATE/translate-recipe" \
  --reference "$HGSS_REFERENCE" --component-receipt "$COMPONENT_RECEIPT" \
  --field-contract "$PRIVATE/translate-fields.json" --prepare-only \
  --json "$PRIVATE/translate-prepare.json"
python3 -B source/features/trainer-strategy/tools/attribuisci_fs_translate.py \
  --parent-config "$SEND_NATIVE_REPLAY" --recipe-dir "$PRIVATE/translate-recipe" \
  --reference "$HGSS_REFERENCE" --component-receipt "$COMPONENT_RECEIPT" \
  --field-contract "$PRIVATE/translate-fields.json" --probe \
  --raw-dir "$PRIVATE/translate-probe-raw" --json "$PRIVATE/translate-probe.json.gz"
```

After independent probe review, repeat without `--probe`, using fresh output
paths. Reports must be outside the exact raw directory. Budget one producer,
180s/command,1 GiB OS RSS,2 MiB logs,16 MiB case output and at least10 GiB free
after a planned1 GiB peak. This campaign's first probe used13.767s and896466944
bytes OS peak RSS; it did not invoke a compiler. CPU17 is the qualified
Unicorn2.1.4 Cortex-A15 backend, not ARM946 silicon timing.

The complete grid used14.440s/896548864 bytes OS peak RSS. The fourteen-test
invocation used14.953s/896434176 bytes; unittest's internal8.758s is a different
interval. Independent final raw review verifies all12 records,107 current and
archived runtime source identities,24 new-image hashes and24 ancestral
before/derived hashes through a separate streaming reconstruction. It starts
no guest or compiler and does not allocate a full image.

Optional replay uses `SGP_FS_TRANSLATE_REPLAY_CONFIG` and
`test_fs_translate_attribution.py`, without launching another guest. Its JSON
has exactly seven string fields: `parent_config`, `recipe_dir`, `reference`,
`component_receipt`, `field_contract`, `report`, `raw_dir`. Paths resolve from
repository root. A missing private replay input is an explicit skip.

```sh
SGP_FS_TRANSLATE_REPLAY_CONFIG="$PRIVATE/translate-replay.json" \
SGP_FS_TRANSLATE_RECIPE_DIR="$PRIVATE/translate-recipe" \
  python3 -B -m unittest discover -s source/features/trainer-strategy/test \
  -p 'test_fs_translate_*.py' -v
```

Keep documented provenance, exact assembled bytes, finite semantic agreement
and observed activation separate. The default handler's native code, ID/props,
natural card/thread/filesystem behavior and caller integration remain open.

The subsequent [combined Send/Translate case](native-fs-send-translate-native-source-rom-1.3.2.md) qualifies caller integration separately with complete native fields and both actual whole-RAM boundary hashes; the default handler remains modeled.
