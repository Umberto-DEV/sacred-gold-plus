# ExecuteSync with native Release, empty Wakeup and empty Next in one CPU

This extends the [stored-error join](native-fs-exec-sync-join-source-rom-1.3.2.md)
back to the actual Send boundary. The finite question is whether the original
68-byte ExecuteSync wrapper reaches its nine earlier checkpoints in one CPU
context with native Release, Wakeup, Next and IRQ leaves. Translate remains one
explicit model: one four-byte error write and R0 result, preserving other
registers. This does not establish natural filesystem completion.

The subsequent [complete Send case](native-fs-send-native-callees-source-rom-1.3.2.md)
starts before Send preparation and observes its original POP too. It has its
own before-image proof and does not retroactively widen this isolated case.

## Cosa farebbe un professionista di alto livello che non sto chiedendo

Distinguish continuous execution from a chain of copied callee checkpoints.
Freeze earlier fields before building the new oracle. Reconstruct the original
input image before adding code; do not inject future saved registers or stack
residues. Include external model policy in grouping: identical CPU and RAM can
produce different interactions. Test a same-code bypass that returns the same
public output. Review source, ABI, raw observations and counterexamples
independently, retaining failures as verification-tool findings.

## Il materiale più grezzo da cui partire

Use your own exact [Send input set](native-fs-send-source-rom-1.3.2.md#il-materiale-più-grezzo-da-cui-partire)
and complete ancestor campaigns through the join. The current EN ROM is
152786844 bytes, SHA-256
`2e30d6960bb059615fca7527700d86f8282e82ccbe99bf62e22f027453dc3d3d`;
localized IT is 159029760 bytes, SHA-256
`13ebac02bdea3036511773587e6603ce6834e25f4b13d1a4662c3e954bfd5d4a`.
Both use internal IPKE revision0; retail Italian IPKI is a separate reference.
Keep ROMs, extracted bodies, raw RAM/captures, saves and BIOS private.

The source counterpart is `FS_archive_prefix.c::FSi_ExecuteSyncCommand`, with
`FSi_ReleaseCommand`, `FSi_NextCommand`, `OS_WakeupThread` and IRQ primitives in
the qualified SDK reference
[cb614ad23449d5852b40321dc409c4143872b35c](https://github.com/ctrl-cheeb-del/pokeheartgold/tree/cb614ad23449d5852b40321dc409c4143872b35c).
The [newer PRET comparison](../test-bench.md#using-newer-pret-references) is useful
for source discovery and metadata reuse; unmaterialized SDK wraps in those
clones do not replace the authenticated SDK sources used here.

| Native component | RAM address | Current physical ROM offset | Bytes | SHA-256 |
| --- | --- | --- | --- | --- |
| ExecuteSync | `0x020D7744` | `0x000DB744` |68| `44b2f23b47f01552bd478420b9a14ae0fc2ed6013e7d551d5112075264a43d55` |
| Release | `0x020D6864` | `0x000DA864` |92| `658daf608846bdeca5f8d48b8b0ea7d46280ebcd2ef783fce8b5f9e12735f568` |
| Wakeup | `0x020D1ECC` | `0x000D5ECC` |104| `25c7d621d6b4d855be6828b9ec8d98162df8ecdda5a22db405caf344aa4102db` |
| Next | `0x020D749C` | `0x000DB49C` |532| `d3785eb030614f3050cb9ef747e3a173e534c40ef5ffa3d75c95acd6fa778e9c` |
| DisableInterrupts | `0x020D3A38` | `0x000D7A38` |20| `a8cdb747f9936730571b220bb9570615892665b120713ffc59b1cb2d7dee76ff` |
| RestoreInterrupts | `0x020D3A4C` | `0x000D7A4C` |24| `46b5111b6fad094dfff177dca974d33b477cb72772ecfe95b74b1c7f656bc4fd` |

These 840 bytes are retained ARM9 code, not newly installed Plus payloads.
Independent physical ARM9 and decoded/autoload-aware reads agree with retained
ELF text. The 68-byte wrapper object SHA-256 is
`768a6e34e5cf2ce6535446110482f27edf3c39c3bd3105956c8037e5049bd011`.
Use the existing [wrapper recipe](../../features/trainer-strategy/sorgenti/fs-exec-sync.S)
and callee recipes linked from the parent cases. They assemble comparison
objects with authenticated Clang21, ARM946E-S ARM mode; they have no installer.
No new compiler invocation is needed for unchanged qualified objects. Exact
assembly reconstruction does not recover original Metrowerks C code generation.

The original Send420 bytes at RAM`0x020D7788`, ROM`0x000DB788`, are retained,
SHA-256`ca74d4ff51db8cb32a7d6235e6b4d453554d65ac6162dc4092b7f285d0e4051a`.
Its final POP at`0x020D7928` is a stop gate. The first four original Translate
bytes at RAM`0x020D68C0`, ROM`0x000DA8C0`, have SHA-256
`e506f1b7eb5c3563131ed686a9d777e4e9c799db0c7793becade44d0afd6048c`.
They are authenticated but intercepted before execution; no Translate native
instruction runs.

### Boundary, ABI and memory provenance

TOP=`0x023BEEC0`, file=`0x023BEDD0`, archive=`0x021E3654`.
Enter`0x020D7744` with the complete actual earlier Send16-register context:
R0=file, R4=archive, SP=TOP−304, LR=`0x020D7928`, CPSR=`0x2000001F`.
File.command=4, error=BUSY2, status=`0x45`; archive flags=`0x13`, list.next=file,
proc_flag=0. This is the finite isolated command4 input, not arbitrary FS state.

The earlier Send campaign recorded whole RAM after a value-only ExecuteSync
model and the subsequent readonly Send POP, rather than at the model boundary.
Transfer that digest back only after checking the exact BL context, model
before/after RAM equality, sole following native POP, six actual POP reads,
saved return and final full context. The unchanged model source performs no RAM
writes. This is a derived boundary identity, not a new raw boundary capture.

Reconstruct the old four-MiB Send image and require its observed final digest
before overlaying the six native components and Translate gate. Preserve all
other bytes, including retained code and old stop gates. The new fixture holds
captured304 plus captured guard56;416-byte frame plus new guard56 needs112 more
bytes. These are A5-filled bytes from the reconstructed, digest-verified parent,
not new captured data. Per-origin receipts bind parent and installed image
digests and list each code overlay's before/after hashes and changed-byte count.

Wrapper PUSH8, Release PUSH16, Wake PUSH24 and Next PUSH32+local72 execute
normally. Peak is112 below entry SP; frame base=TOP−416, lower guard56.
The hypothetical736-byte full-caller aggregate exceeds the old608-byte ownership
bound and remains unqualified. No caller mask is enlarged.

### Calls and the remaining model

| Boundary | Actual arguments / return |
| --- | --- |
| Translate`0x020D68C0` | R0=file,R1=command4, SP=TOP−312, LR=`0x020D7754`; modeled error0/1 at file+20 and R0, all other registers/CPSR preserved |
| Release`0x020D6864` | R0=file,R1=translated result; native unlink/status/error stores and nested IRQ/Wakeup |
| Wakeup`0x020D1ECC` | R0=file+24 **queue**, SP=TOP−328, LR=`0x020D68B4`; empty queue, no scheduling |
| Next`0x020D749C` | R0=archive after original LDR/BL; empty list, running flag cleared, no callbacks, returns NULL |
| Send gate`0x020D7928` | BOOL from stored error; R4=archive,SP=TOP−304, LR=`0x020D76A4`; stop before original POP |

File+48 is the command argument area, not the Wakeup queue. The independent
preprobe review caught that distinction in the negative-model guard; the
corrected guard has a regression test derived from the source checkpoint.
Final R1/R2=`0x6000009F`/`0x6000001F` are actual native volatile residues.
Success error0 returns1/CPSR`0x6000001F`; error1 returns0/CPSR`0x2000001F`.
Translate's model does not establish native translation, ID/property handling,
IS_SYNC transitions, thread/card work or callback behavior.

## I metodi e gli strumenti da usare

First reproduce the [join parent](native-fs-exec-sync-join-source-rom-1.3.2.md)
with your own inputs and receipts. Its replay JSON has four string fields:
`parent_config`, `field_contract`, `report`, `raw_dir`. Its nested configs bind
the earlier input ROMs, report families and retained object directories. Paths
resolve from repository root; do not copy another developer's personal paths.

Freeze the seven historical reports before the new oracle/guest. This exporter
uses only Python's standard library and neither imports the new predictor nor
constructs an emulated image:

```sh
python3 -I -S -B source/features/trainer-strategy/tools/congela_fs_exec_sync_native_contract.py \
  --send-en "$SEND_EN" --send-it "$SEND_IT" \
  --exec-en "$EXEC_EN" --exec-it "$EXEC_IT" \
  --composition-report "$RELEASE_WAKE" --next-report "$NEXT" --join-report "$JOIN" \
  --json "$PRIVATE/native-sync-fields.json"
```

The inspected campaign's frozen export SHA-256 is
`c0b41e0ea7bc21417a768ae2761137ccd8a30f93dc97629d2c59d4e2a46fb73a`:
16 provenance cells, each with nine checkpoints. Known bodies/inputs were
already inspected; this is not a blind experiment. Exporting alone does not
authenticate an arbitrary input report or prove chronology.

Use the project Python environment with ndspy4.2.0, Capstone5.0.9 distribution
(module5.0.7) and Unicorn2.1.4. The authenticated ancestor compiler is Clang21
SHA-256`fc5e3cbba6ad54059295cad716aacb05ace8235f5f7a6031f1d8c15d24bd6d66`.
The producer replays ancestor raw semantics without launching new ancestor
guests, verifies current source/ROM/ELF identities and re-exports the frozen
fields for comparison. CPU-free preparation still needs those dependencies.

```sh
python3 -B source/features/trainer-strategy/tools/attribuisci_fs_exec_sync_native_callees.py \
  --parent-config "$JOIN_REPLAY" --field-contract "$PRIVATE/native-sync-fields.json" \
  --prepare-only --json "$PRIVATE/native-sync-prepare.json"
python3 -B source/features/trainer-strategy/tools/attribuisci_fs_exec_sync_native_callees.py \
  --parent-config "$JOIN_REPLAY" --field-contract "$PRIVATE/native-sync-fields.json" \
  --probe --raw-dir "$PRIVATE/native-sync-probe-raw" --json "$PRIVATE/native-sync-probe.json.gz"
```

Review that probe before the complete grid. Repeat the producer without
`--probe`, with fresh output paths. Reports must be outside the raw directory;
the exact raw-file set is authenticated on replay. Keep at least 10 GiB free
after a planned 1 GiB peak, 180s/command, 1 GiB OS RSS, 2 MiB logs and 16 MiB case
output. Run only one producer. This campaign's first probe passed within these
budgets; the complete grid used 13.044s and 879722496 bytes OS peak RSS.

The pure predictor composes qualified source predictors without invoking their
image builders or CPU collectors. Its strict local Next adapter clones the
parent code while replacing only the input checker. Counter preimages are
derived from the preceding source stores and checked byte-for-byte; the old
normal-only checker is unchanged. An internal zero-digest shape sentinel used
by that legacy checker is never memory authentication or exported provenance.

The collector starts one CPU at7744 and stops at7928. It neither sets RAM nor
registers at native intermediate checkpoints. Only Translate writes one host
word and R0, then returns to actual LR. Native stores, host stores, original
code fetches and checkpoint fields have separate ledgers. Complete image
digests check memory outside the frame/archive too. OFF suppresses observation
ledgers only and must preserve CPU, RAM, model ledger and all checkpoints.

Grouping compares literal full registers, all four MiB of initial RAM **and**
Translate result policy. Hashes are reporting aids. There are two literal input
states but four interactions because error0/1 start with identical BUSY2 RAM.

### Counterexamples and success criteria

The positive source prediction is131 native contexts,109 unique starts,26
native stores,35 reads,one model and133 total fetch callbacks including the
stopped gate. The negative same-code Wakeup bypass adds a declared second model
and has110/99/20/28 and113 callbacks. Both must preserve ABI and return normally.
They converge in complete final registers/archive and the live312-byte caller
window, yet differ in exactly frame416 offsets64–71: eight retained Wakeup
stack bytes. Next PUSH overwrites the other16 bytes of Wakeup's24-byte save.

Compare nine actual full-register checkpoints and their historical312/352/416
frame windows plus archive92, without masking live fields. The bypass must fail
this comparison despite matching public output. A disguise removing its extra
model and substituting expected checkpoints must still fail on actual native
activation counts. Release's error store also needs its true preimage after
Translate; convergent final memory cannot excuse a missing model write.

Run source/export tests and opt-in raw replay without launching another guest:

```sh
python3 -B -m unittest discover -s source/features/trainer-strategy/test \
  -p 'test_fs_exec_sync_native_callees_*.py' -v
SGP_FS_EXEC_SYNC_NATIVE_REPLAY_CONFIG="$PRIVATE/native-sync-replay.json" \
  python3 -B -m unittest discover -s source/features/trainer-strategy/test \
  -p 'test_fs_exec_sync_native_callees_*.py' -v
```

The latter JSON uses the same four keys as the join configuration, now pointing
to this case's parent join configuration, frozen fields, complete report and
raw directory. Without private inputs the replay is an explicit skip. Tests
cover literal grouping even with digest collisions, model-policy separation,
strict result types, frozen provenance, counter adapter immutability, internal
Wake-window mutants, complete-parent gates and coherent raw-record forgeries.

### Conclusions and residual work

Documented provenance and reconstructed assembly bytes are distinct from
semantic equivalence on these finite states. Twelve guest runs over four
literal CPU/RAM/policy groups pass: normal,OFF and same-code bypass for each.
There are 32 provenance-member frozen checks (16 origins × normal/OFF), four
exact OFF comparisons and 16 negative member checks. The pure oracle agrees
with all 144 historical checkpoints. Fifteen source/export/gate/private-replay
tests pass with zero skips; replay does not start another guest. Independent
raw review verifies all 12 raw records, 97 source identities and 24 complete
image hashes with a separate streaming reconstruction. No game change or
optimization is proposed.
CPU17 is the Cortex-A15 Unicorn backend: this checks admitted instruction
semantics, not ARM946 silicon timing, interrupt delivery or hardware behavior.
Full Translate, nonempty queues, Async, original Send POP/full caller, natural
filesystem/card, persistent save and physical-device acceptance remain open.
