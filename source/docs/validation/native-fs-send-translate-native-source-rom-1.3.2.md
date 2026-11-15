# One native Send/Translate context and its residual default service

**Verified host scope:**12 guest runs across four literal CPU/RAM/policy groups,
48 frozen comparisons, four OFF checks and four causal writer controls. All
combined Translate boundary whole hashes equal the earlier isolated observations.
This extends the [complete Send case](native-fs-send-native-callees-source-rom-1.3.2.md)
with the independently qualified [native Translate body](native-fs-translate-source-rom-1.3.2.md).

## Cosa farebbe un professionista di alto livello che non sto chiedendo

Run the caller and callee in one CPU context, starting before Send prepares
the file. Preserve the exact input provenance and inherited guard. Freeze the
earlier Send's complete final fields and the isolated native Translate's actual
whole-RAM boundaries before writing the combined predictor. Do not carry over
the older model comparison's volatile-register or stack exclusions: complete
native observations are now available. Keep the remaining default service
explicit and test whether an early host write can masquerade as a native writer.

## Il materiale più grezzo da cui partire

Prepare your own complete [Send](native-fs-send-native-callees-source-rom-1.3.2.md)
and [Translate](native-fs-translate-source-rom-1.3.2.md) campaigns, their private
raw files, recovered objects, pinned reference and replay configurations. Use
the previous guides for input acquisition and identity checks. Current r4 EN
is152786844 bytes, SHA-256
`2e30d6960bb059615fca7527700d86f8282e82ccbe99bf62e22f027453dc3d3d`;
localized IT is159029760 bytes, SHA-256
`13ebac02bdea3036511773587e6603ce6834e25f4b13d1a4662c3e954bfd5d4a`.
Both use IPKE revision0; retail Italian IPKI is a distinct input.
Keep ROMs, extracted components, captures, whole-RAM images, saves and BIOS private.

The source counterpart remains the SDK `FS_command.c`, `FS_command_default.c`
and related original headers at reference
[`cb614ad23449d5852b40321dc409c4143872b35c`](https://github.com/ctrl-cheeb-del/pokeheartgold/tree/cb614ad23449d5852b40321dc409c4143872b35c).
The isolated guide records exact source/header/compiler/ELF hashes, physical
offsets,18-header ARM32 layout checks and eight-image lineage readbacks. The
recovered Translate object is400 bytes, SHA-256
`230b5b3a3490447dff68e2aafe9ebce52cd1c33308b325c3bedd1f9a07d3c802`.
Its recipe has no installer. Original Metrowerks C code generation is unproved.
No new compilation is necessary when reusing that authenticated object.

### Code, data and calling convention

The same retained ARM9 components are used:1656 instruction bytes across Send,
ExecuteSync, Translate, Release, Wakeup, Next and IRQ helpers. Main-code physical
offsets and hashes are in the two prerequisite guides. In current EN/IT,
Translate starts at RAM`0x020D68C0`/ROM`0x000DA8C0`; its396-byte instruction
region ends before the four-byte pool at`0x020D6A4C`. The pool selects the
36-byte initialized table at RAM`0x0210E124`/ROM`0x00112124`. Slot4 points to
`0x020D6DB0`/ROM`0x000DADB0`, the default FindPathCommand handler. That is
different from the higher Find wrapper at`0x020D7FC0`. The default's four-byte
prologue is an intercepted gate, never admitted as native code here.

The copied Send input has command4, initial file error0 and archive flag3.
Send natively prepares status`0x45`/BUSY2 and archive flag`0x13`. Translate
enters with R0=file, R1=4, SP=TOP−312 and LR=`0x020D7754`; its PUSH24 reaches
TOP−336. Native dispatch sets archive IS_SYNC, reads the pool/table, and calls
the default with R0=file, R1=`0x020D6DB0`, SP=TOP−336,
LR=`0x020D6984`, CPSR=`0x6000001F`.

The only positive model returns FSResult0 or1 and writes zero RAM. Preserving
all other registers/CPSR is the declared model policy, not a universal default
handler ABI. Translate clears IS_SYNC and writes file.error natively. Its
returned R1 and LR differ from the older Translate model. The real instructions
at`0x020D7754/7758/775C` consume/replace those values before Release. Translate's
saved24 bytes are subsequently overwritten by Release and Wakeup. Six native
store preimages change: combined ledger indices26–29 and39–40. They must be
recomputed in order, never normalized to the old fill. From Wakeup return the
complete frame and CPU converge with the earlier Send path. The original Send
POP returns to stopped Find ADD at`0x020D80F8`.

## I metodi e gli strumenti da usare

Use the existing Python environment with ndspy4.2.0, Capstone distribution5.0.9
and Unicorn2.1.4, CPU17. The backend is Cortex-A15 instruction semantics, not
ARM946 timing, interrupts or silicon. The freezer uses only the standard library.
Define `PRIVATE` as a fresh private directory outside `source/` and supply the
two completed prerequisite reports and Translate configuration:

```sh
python3 -I -S -B source/features/trainer-strategy/tools/congela_fs_send_translate_contract.py \
  --send-report "$PRIVATE/send/matrix.json.gz" \
  --translate-report "$PRIVATE/translate/matrix.json.gz" \
  --json "$PRIVATE/send-translate-fields.json"
python3 -B source/features/trainer-strategy/tools/attribuisci_fs_send_translate_native.py \
  --parent-config "$PRIVATE/translate/replay-config.json" \
  --field-contract "$PRIVATE/send-translate-fields.json" --prepare-only \
  --json "$PRIVATE/send-translate-prepare.json"
python3 -B source/features/trainer-strategy/tools/attribuisci_fs_send_translate_native.py \
  --parent-config "$PRIVATE/translate/replay-config.json" \
  --field-contract "$PRIVATE/send-translate-fields.json" \
  --raw-dir "$PRIVATE/send-translate-raw" --json "$PRIVATE/send-translate.json.gz"
```

Outputs must be fresh; report and raw directory must be separate. The parent
configuration is the exact seven-string schema in the Translate guide. Preparation
reauthenticates the complete prerequisite raw chain, current physical/decoded
ROM bytes, recipe and source identities without another CPU or compiler.
Initial RAM starts at the observed Send prestate, then overlays the qualified
Translate400/table36/defaultgate4 bytes. The17 prefix stores and these overlays
are disjoint. Consequently, the whole-RAM hashes reached at Translate entry
and return must equal the earlier isolated campaign's **actual** before/after
hashes. Do not substitute its pre-overlay derived-boundary fixture hash.
Do not compare the unchanged old Send's whole final hash: its code/data image
does not include these overlays.

The predictor computes transitions and every store preimage from initial fields.
The collector executes one guest without checkpoint reinjection. It admits
only ARM instruction extents, checks live bytes and per-PC read/write owners,
and records native stores separately from host writes. Instruction callback
limit384 replaces the previous driver's256: the combined path predicts262.
This changes the bench bound, not the game or the ancestor campaign.

The negative `early_error` policy writes the same result into file.error inside
the default model. It can converge in complete final CPU/RAM, flow, reads and
counts. The first native error STR at`0x020D6A40`, combined store index25, must
see BUSY2 in the positive run and the result in the counter. Metadata camouflage
must still fail the native-store comparison. Frozen fields alone intentionally
accept that counter and make no writer/activation claim. OFF must preserve
complete CPU/RAM, models and checkpoints while emitting no trace projections.

For private replay without another guest, write a JSON object with exactly
four string keys: `parent_config`, `field_contract`, `report`, `raw_dir`. Paths
are resolved from the invocation directory. The first points to your Translate
configuration; the remaining keys identify the combined outputs above.

```sh
SGP_FS_SEND_TRANSLATE_REPLAY_CONFIG="$PRIVATE/send-translate-replay.json" \
  python3 -B -m unittest discover -s source/features/trainer-strategy/test \
  -p 'test_fs_send_translate_*.py' -v
```

The public suite covers full-field mutations, typed input admission, causal
preimages, ABI bridges, source convergence, CLI modes and literal grouping even
under reporting-hash collisions. Private replay rechecks actual raw and rejects
whole-boundary and native-store forgeries; without private inputs it explicitly
skips only that replay. Source tests are also in the Class A runner.

### Results and limits

Observed in each selected run:260 native contexts,216 unique starts,50 native
stores,68 reads,262 callbacks and136-byte peak from Send entry inside the
existing416-byte frame. Sixteen historical origins reduce to four literal
CPU/RAM/default-result interactions, not16 independent states. All48 frozen
comparisons pass, including the16 early-write comparisons which make no writer
claim. Four OFF pairs preserve whole CPU/RAM/models/checkpoints with zero
projections. Four actual writer pairs converge in whole final RAM and CPU but
change store25's preimage; metadata camouflage is rejected on native stores.
The matrix takes15.580 seconds with898547712-byte OS peak RSS on this host;
these are host qualification costs, not Nintendo DS timing. Eleven tests pass without skips (15.185 seconds,898875392-byte OS peak RSS;
8.918 seconds inside unittest). Independent review checks all12 raw files,
110 current/snapshotted runtime sources,48 streaming whole-image hashes,
48 frozen comparisons, four OFF pairs and four writer controls without another
guest. These exact identities and command receipts remain in the private campaign.

The default handler itself requires184 additional stack bytes before doing its
work and remains unexecuted. Native default behavior, path ID/property/FNT/card,
callback, asynchronous/non-SYNC branches, nonempty scheduling, higher callers,
natural filesystem, SAVE/cold hardware and IRQ delivery remain separate questions.
The larger caller ownership issue stays open; no reservation or ABI is enlarged.
There is no gameplay change or demonstrated resource saving. Reusing a compiled
object and frozen contracts accelerates attribution; it does not establish a
complete Italian PRET build. See the broader
[PRET reference method](../test-bench.md#using-newer-pret-references).

A subsequent [default FindPath prefix case](native-fs-default-findpath-source-rom-1.3.2.md) executes the residual handler’s preparation up to its first nested Translate call, with zero service models. Full default return and filesystem effects remain excluded; this does not retroactively change the earlier modeled campaign.
