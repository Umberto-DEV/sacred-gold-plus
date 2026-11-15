# Nested SEEKDIR dispatch: actual inputs and a distinct flag projection

**Verified host scope:** six guests over two literal CPU/RAM states, with zero
service models or runtime host writes. Thirty-two strict input comparisons pass;
16 projected-input comparisons are rejected as actual and attested separately.
Two OFF pairs and two temporal counterexamples pass. Execution stops before
the selected default handler; no SeekDir result or filesystem completion is proved.

## Cosa farebbe un professionista di alto livello che non sto chiedendo

Keep the explicit command parameter separate from the file's stored outer
command. Verify the selected table slot and stopped handler independently.
Freeze the observed parent AFTER state, reconstruct its whole image and bind
it to the observed hash before adding a new code gate. Promote existing guard
bytes into stack ownership without initializing them. Reject a deliberately
modified input as an actual parent state, even when its final CPU/RAM converge.
Final-state agreement alone does not establish entry provenance or native writers.

## Il materiale più grezzo da cui partire

Prepare your own complete [default FindPath prefix campaign](native-fs-default-findpath-source-rom-1.3.2.md)
and private raw files. It observes the nested-call state after seven native
instructions in a declared filesystem fixture. It is not a mounted natural
filesystem capture. Current r4 EN is 152786844 bytes, SHA-256
`2e30d6960bb059615fca7527700d86f8282e82ccbe99bf62e22f027453dc3d3d`;
localized IT is 159029760 bytes, SHA-256
`13ebac02bdea3036511773587e6603ce6834e25f4b13d1a4662c3e954bfd5d4a`.
Both use IPKE revision 0; retail Italian IPKI is distinct. ROMs, extracted data,
RAM images, raw captures, saves and BIOS remain private.

The counterpart is `FS_command.c::FSi_TranslateCommand` at reference
[`cb614ad23449d5852b40321dc409c4143872b35c`](https://github.com/ctrl-cheeb-del/pokeheartgold/tree/cb614ad23449d5852b40321dc409c4143872b35c),
file SHA-256 `07333027376e89d3ecc243b0022d089f9c3153cfe4226ef433e086cbe9777e60`.
The selected table and handler declaration are in `FS_command_default.c`,
SHA-256 `040f053d87d157231bcd051731eee8bf27768a9103940b6c4016f9cf703ca513`.
The `FSi_SeekDirCommand` definition SHA-256 is
`707757982ff12c7b16ea554997052c18a15e9a5ac1c64eb16c354e526f73e74e`;
its body is not executed here. Newer PRET references remain distinct from this
pinned SDK; follow the [reference method](../test-bench.md#using-newer-pret-references).

### Bytes, addresses and compilation

Reuse the [Translate recipe](native-fs-translate-source-rom-1.3.2.md), its compiler
receipt and 18 original-header checks. No new compilation is required for this
unchanged object. The 400-byte object SHA-256 is
`230b5b3a3490447dff68e2aafe9ebce52cd1c33308b325c3bedd1f9a07d3c802`.
Original Metrowerks C code generation remains unproved. This case adds a new
readback and dispatch attribution, not an installer or a new ROM build.

| Component | RAM address | Current physical ROM offset | Bytes | SHA-256 |
| --- | --- | --- | ---: | --- |
| Translate instructions plus pool | `0x020D68C0` | `0x000DA8C0` | 400 | `f1df0f035e516cdfff9df4668530ca636f88b9a1a70d86804b9671c8bce7341a` |
| Initialized default table | `0x0210E124` | `0x00112124` | 36 | `a2a3fe2a981c9967141752f3228d54c59d73c639339443bbe0ef04f13319d287` |
| Original stopped SeekDir gate | `0x020D6BEC` | `0x000DABEC` | 4 | `cb2450f37bd96fdbd6b5ca0da7f783e6a195e37f754014852618c0f6593e4d89` |

The four-byte pool at `0x020D6A4C` selects the table. Slot2 at `0x0210E12C`
selects `0x020D6BEC`, distinct from slot4's default FindPath handler at
`0x020D6DB0`. The stopped gate is an original PUSH of r4/r5/r6/LR; neither it
nor its following stack allocation executes in this case.

The selected instructions occupy two intervals: `[0x020D68C0,0x020D6904)`
(17 ARM starts) and `[0x020D6968,0x020D6984)` (7 starts). Their ordered 96-byte
SHA-256 is `10afa067cfbc14c45d16e8126e4976e7510861f37de05ab644101947d558fe42`.
This is a selection inside the 400-byte recipe, not a new contiguous payload.
The pool and table are data and never admitted as instruction fetches.

Physical and independently decoded reads agree in both current languages.
Retail→base1.1→V4→current comparisons verify the same instruction selection,
table contents, slot2 target and gate in all eight images. Whole400 matches
seven: retail IT uses pool value `0x0210E0B8` rather than `0x0210E124`.
Do not infer a global Italian address shift, eight whole-object matches or
historical activation. Compressed historical physical offsets remain absent
where the reader cannot independently establish them.

### Caller, command and stack lifetime

The preceding default FindPath prefix reaches Translate with R0=file, R1=2,
SP=TOP−520, LR=`0x020D6DCC`, CPSR=`0x6000001F`. The file still has status
`0x45`, stored command4 and BUSY2. Archive flags are `0x213`, and proc_flag is
zero in this fixture. Changing `FILE.command` to2 would describe a different
input: the direct nested call passes its command separately.

Translate saves r4–r8/LR, sets R7=2 and R6=4, tests SYNC and the callback mask,
sets the IS_SYNC bit and selects table slot2. The normal flag store at
`0x020D68F4` is idempotent: `0x213 | 0x200 == 0x213`. It still executes and is
recorded as a native write. No path/FNT bytes, POP or file.error assignment
occur in this prefix.

At the stopped handler, R0=file, R1=`0x020D6BEC`, R5=archive, R6=4, R7=2,
SP=TOP−544, LR=`0x020D6984`, CPSR=`0x6000001F`. The saved LR remains
`0x020D6DCC`. This is a handler call boundary, not a FSResult/BOOL return.

TOP is `0x023BEEC0`. The native PUSH writes TOP−544..TOP−520: the last 24 bytes
of the earlier captured guard56, now stack ownership. Before execution:

```text
new frame544 = parent guard56[-24:] + parent frame520
new guard56 = new whole-derived24 + parent guard56[:32]
```

Only the lowest24 guard bytes are newly exposed. The parent recorded an actual
whole-RAM AFTER hash at this stopped call, but no whole-RAM blob is retained.
Reconstruct its authenticated initial image plus nine actual/source-matched
native PUSH writes and require that observed AFTER hash. Then overlay only the
new four-byte stopped gate, recording its delta. Do not confuse the parent's
observed AFTER hash with the new initial code-image hash. No stack fill is added;
the new 24 bytes happen to be A5 in these authenticated fixtures.

## I metodi e gli strumenti da usare

Use the project Python environment with ndspy4.2.0, Capstone distribution5.0.9
and Unicorn2.1.4. CPU17 provides Cortex-A15 instruction semantics, not ARM946
silicon timing or IRQ delivery. The freezer is standard-library-only. Retain
the qualified Translate object, compiler identity, original source/header pin
and flags from its guide. Its compiler SHA is
`fc5e3cbba6ad54059295cad716aacb05ace8235f5f7a6031f1d8c15d24bd6d66`;
a different toolchain requires its own qualification rather than silently
changing the recorded identity.

Set `PRIVATE` to a fresh private directory outside `source/`, `HGSS_REFERENCE`
to the clean pinned checkout, and `TRANSLATE_RECIPE` to the already qualified
400-byte recipe directory. The parent's seven-key configuration refers to its
own 28-byte default-prefix recipe. The new `--recipe-dir` below refers to the
earlier Translate400 object; those are distinct artifacts.

```sh
python3 -I -S -B source/features/trainer-strategy/tools/congela_fs_nested_seekdir_contract.py \
  --parent-report "$PRIVATE/default/matrix.json.gz" \
  --json "$PRIVATE/nested-fields.json"
python3 -B source/features/trainer-strategy/tools/attribuisci_fs_nested_seekdir.py \
  --parent-config "$PRIVATE/default/replay-config.json" --export-components \
  --json "$PRIVATE/nested-components.json"
python3 -B source/features/trainer-strategy/tools/rileggi_fs_nested_seekdir.py \
  --retail "$RETAIL" --base "$BASE11" --v4 "$V4" --rom "$R4" --language EN \
  --recipe-dir "$TRANSLATE_RECIPE" --json "$PRIVATE/nested-lineage-en.json"
```

Repeat the lineage command with each IT input and `--language IT`. Freeze before
the new oracle/guest; re-exporting later checks equality, not chronology. To
prepare without CPU, then execute the six finite guests:

```sh
python3 -B source/features/trainer-strategy/tools/attribuisci_fs_nested_seekdir.py \
  --parent-config "$PRIVATE/default/replay-config.json" \
  --recipe-dir "$TRANSLATE_RECIPE" --reference "$HGSS_REFERENCE" \
  --component-receipt "$PRIVATE/nested-components.json" \
  --field-contract "$PRIVATE/nested-fields.json" --prepare-only \
  --json "$PRIVATE/nested-prepare.json"
python3 -B source/features/trainer-strategy/tools/attribuisci_fs_nested_seekdir.py \
  --parent-config "$PRIVATE/default/replay-config.json" \
  --recipe-dir "$TRANSLATE_RECIPE" --reference "$HGSS_REFERENCE" \
  --component-receipt "$PRIVATE/nested-components.json" \
  --field-contract "$PRIVATE/nested-fields.json" \
  --raw-dir "$PRIVATE/nested-raw" --json "$PRIVATE/nested.json.gz"
```

Outputs must be fresh and private; keep the report outside its raw directory.
Preparation reauthenticates parent raw/source, the current ROMs, retained ELF,
18 headers, dispatch table and new gate without a compiler or CPU. Archive its
source identities before execution. The collector admits exactly the24 selected
ARM PCs, six native read owners and seven native stores, with a 64-callback cap.
It saves raw records before issuing a verdict.

### Strict input provenance and the counterexample

Each of two literal CPU/RAM states gets normal, OFF and `clear_sync` runs.
Sixteen historical origins are aliases, not 16 independent guest states. The
counter clears only bit `0x200` in archive.flag before CPU execution:

| Run | Input archive.flag | Final archive.flag | Frozen actual-input verdict |
| --- | --- | --- | --- |
| normal / OFF | `0x213` | `0x213` | accepted |
| clear_sync | `0x13` | `0x213` | rejected as actual; declared projection attested separately |

The strict comparator reads the actual `archive_before` supplied to the guest,
not just the canonical fixture descriptor. All other captured bytes, full16
input and provenance remain bound. No archive-field mask or generic exception
can turn the projected state into an actual parent input.

Both inputs converge in complete final CPU/RAM and instruction/read/store counts.
Temporal evidence differs: two native CPU contexts at `0x020D68E8/68EC`, read2
at `0x020D68E4`, and store6's preimage at `0x020D68F4`. Whole initial RAM hashes
differ; whole final hashes agree. Restoring input/checkpoint metadata in a forged
report still fails the CPU-context comparison. If the CPU/read transcripts are
also forged, the native store preimage still contradicts the claimed input.
These are two distinct forgery tests, not a claim that only metadata differs.
There are zero runtime host writes and zero service models in both runs.
OFF preserves complete CPU/RAM/checkpoints with zero trace projections.

For private replay without another guest, write exactly seven string keys:
`parent_config`, `recipe_dir`, `reference`, `component_receipt`, `field_contract`,
`report`, `raw_dir`. Resolve paths from the invocation directory; `recipe_dir`
must identify Translate400, while `parent_config` retains the parent's own recipe.

```sh
SGP_FS_NESTED_SEEKDIR_RECIPE_DIR="$TRANSLATE_RECIPE" \
SGP_FS_NESTED_SEEKDIR_REPLAY_CONFIG="$PRIVATE/nested-replay.json" \
  python3 -B -m unittest discover -s source/features/trainer-strategy/test \
  -p 'test_fs_nested_seekdir_*.py' -v
```

Object/raw-dependent tests explicitly skip without private inputs. Tests cover
captured byte/register mutations, projection admission, retained ELF selection,
literal-pool relocation, ABI/temporal evidence, exact read/write owners, CLI
gates and literal grouping under reporting-hash collisions. Private replay
rejects register/store/derived-guard forgeries and forbids another guest.
The freezer and source tests are also in the Class A runner.

### Observations and limits

Each selected run executes 24 native contexts, seven stores and six reads,
with 25 code callbacks including the stopped gate and a 24-byte peak. All 32
normal/OFF actual-input comparisons pass; all 16 projected states fail that
strict comparison and pass only their separate projection attestation. Two
OFF and two temporal controls pass. Independent review verifies six raw files,
120 current/snapshotted runtime sources, 12 streaming whole before/final hashes
and 16 joins to the actual parent AFTER observations. The matrix takes 18.972
seconds with 926728192-byte OS peak RSS; these are host costs, not DS performance.

Fifteen tests pass without skips in 21.847 seconds, with 937230336-byte OS peak
RSS (13.180 seconds inside unittest). The retained ELF is checked without
compiling again.

The legacy archive has no FNT/read/table callback state. Existing natural EN
material can supply such resources, but it cannot be silently grafted into
this fixture: the naturally loaded FAT range `[0x023BE580,0x023BF588)` contains
this fixture's FILE and stack addresses. Natural callback traces also use DTCM
stack addresses, which the older MainRAM-only snapshots do not preserve.
Resource provenance, arena ownership and precise caller state need their own
qualification; availability of old material does not upgrade this campaign.

Default SeekDir execution/return, path/FNT/card access, ID/property output,
full FindPath/caller integration, natural filesystem activation, IRQ delivery,
ARM946 timing and hardware SAVE/cold restart remain open. The older 608-byte
ownership boundary is unchanged. There is no gameplay, ROM/save/ABI/ID/default
change or demonstrated resource saving.

The [complete cached SeekDir follow-up](native-fs-cached-seekdir-source-rom-1.3.2.md)
now qualifies the full selected callee with real cached resources and new
disjoint synthetic arenas. It does not upgrade this case's stopped handler or
claim that its different archive/stack was an observed natural caller.
