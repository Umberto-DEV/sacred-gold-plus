# Native Send and ExecuteSync in one context, with explicit Translate projection

This joins [Send](native-fs-send-source-rom-1.3.2.md) and
[ExecuteSync with native callees](native-fs-exec-sync-native-callees-source-rom-1.3.2.md)
from the actual Find→Send entry to the original Find return gate. Send prepares
the queue and file itself, then executes ExecuteSync, Release, empty Wakeup,
empty Next and IRQ leaves in the same CPU. Translate remains one declared
error-field/R0 model. No game, ROM, save, ABI, identifier or default changes.

The later [isolated native Translate case](native-fs-translate-source-rom-1.3.2.md)
qualifies that component with a value-only default-handler model. Joining it to
this Send context requires a separate caller/stack/preimage proof; this case's
earlier model and coverage are preserved.

## Cosa farebbe un professionista di alto livello che non sto chiedendo

Authenticate the complete input before native preparation. Do not insert an
already completed callee image at the start of its caller. Preserve captured
predecessor guard bytes and check their actual values before native PUSH
overwrites them. Freeze earlier checkpoints and label the final POP prediction
as derived, rather than previously observed. Keep field agreement separate from
native activation; test a same-code bypass with equal public output. Review
source, ABI, collector, raw records and input provenance independently.

## Il materiale più grezzo da cui partire

Use your own exact [Send input set](native-fs-send-source-rom-1.3.2.md#il-materiale-più-grezzo-da-cui-partire)
and the complete native ExecuteSync parent, including its replay configuration,
raw normal/OFF/counter records, frozen contract, source identities and retained
objects. Current r4 EN is 152786844 bytes, SHA-256
`2e30d6960bb059615fca7527700d86f8282e82ccbe99bf62e22f027453dc3d3d`;
localized IT is 159029760 bytes, SHA-256
`13ebac02bdea3036511773587e6603ce6834e25f4b13d1a4662c3e954bfd5d4a`.
Both use internal IPKE revision0. Retail Italian IPKI is a distinct input.
Keep ROMs, extracted bodies, RAM/captures, saves, BIOS and game assets private.

Send's counterpart is
`lib/NitroSDK/src/fs/fs_send_command.c::FSi_SendCommand`, at
[reference cb614ad23449d5852b40321dc409c4143872b35c](https://github.com/ctrl-cheeb-del/pokeheartgold/tree/cb614ad23449d5852b40321dc409c4143872b35c).
File SHA-256 is `4cc68728ca70d26fb620e996493b7b7ef259d07d8150aab607957851a502e587`.
The [recovered assembly](../../features/trainer-strategy/sorgenti/fs-send.S)
has no installer. Retained object SHA-256 is
`028aa5b34853fdbf9500e15766a91d9626383773e59f6e933eb020c57a9f5492`.
Its recipe, headers and compiler were qualified in the earlier Send case.
Reuse unchanged objects; original Metrowerks C code generation remains missing.
The [new PRET references](../test-bench.md#using-newer-pret-references) support
source/metadata discovery without silently replacing production pins.

| Component | RAM | Current physical ROM offset | Bytes | SHA-256 |
| --- | --- | --- | --- | --- |
| Original Send | `0x020D7788` | `0x000DB788` |420| `ca74d4ff51db8cb32a7d6235e6b4d453554d65ac6162dc4092b7f285d0e4051a` |
| Original Find stopped ADD SP | `0x020D80F8` | `0x000DC0F8` |4| `1f3c4d672cc9b41d3b170c8de89a6e18fb504b5c460860090adf23660bc3c735` |

Add the six native components from the
[ExecuteSync table](native-fs-exec-sync-native-callees-source-rom-1.3.2.md#il-materiale-più-grezzo-da-cui-partire):
68+92+104+532+20+24=840 bytes. Total admitted native bodies are 1260 bytes;
the original intercepted Translate gate is another four bytes. Independent
physical ARM9 and decoded/autoload-aware reads authenticate these components.
The new Find gate readback agrees in both current ROMs with `ADD sp,sp,#12`.
It is stopped before execution. This is retained HGSS code, not inserted Plus
code, data or padding; addresses cannot be transferred to another revision.

### Input, state and resources

TOP=`0x023BEEC0`, file=`0x023BEDD0`, archive=`0x021E3654`.
Start at `0x020D7788` using the actual earlier full16-register Send input:
R0=file,R1=command4,R3=file+48,R4=1,R6=ID,R7=path,
SP=TOP−280,LR=`0x020D80F8`,CPSR=`0x6000001F`.
File.command14/error0/status0 and idle archive flags3/list empty are the
authenticated isolated fixture. Archive92 remains a declared source fixture,
not an observed natural boot archive.

The old Send record already has an observed `before_whole_ram_sha256` at this
entry. Reconstruct that exact four-MiB isolated image before overlaying the
qualified callee code. Unlike the earlier ExecuteSync boundary, this identity
does not require a readonly transfer from a later final digest. Preserve every
parent byte, including Send and old gates. Per-origin receipts record each
code overlay, hashes before/after and actual changed-byte counts.

Frame304 combines actual caller280 with 24 preserved bytes of its predecessor
guard. Those 24 bytes are **not A5 fill**. A review caught an initial input
check and synthetic fixture that incorrectly assumed A5 there; corrected source preserves all
304 bytes and tests each PUSH preimage. Frame416 plus lower guard56 requires
112 additional bytes beyond the old frame304/guard56 span. Those extra bytes
are A5-filled in the old isolated image and authenticated by the original
whole-image digest. No future callee stack image is installed beforehand.

Send's PUSH24 and native stores must produce command4/errorBUSY2/status`0x45`,
the linked file and archive flags`0x13`, then deliver the actual earlier
ExecuteSync entry at`0x020D7744`. The native callees generate their stack saves,
unlink/error state and empty-queue completion in the same CPU. Peak is136 bytes
below the Send entry SP, reaching TOP−416. The hypothetical full higher caller
still requires736 bytes versus its old608-byte ownership bound; no mask or
guard is enlarged here.

### Original Send return ABI

At`0x020D7928`, the original POP reads six words at TOP−304 through TOP−284.
It restores R3=argument pointer,R4=1,R5=0,R6=ID,R7=path and returns PC to
`0x020D80F8`,SP=TOP−280. It does not restore LR: actual native
LR=`0x020D76A4`,R1=`0x6000009F`,R2=`0x6000001F` persist. These differ from the
older ExecuteSync value-only model and must not be normalized to that model.
Error0 returns BOOL1/CPSR`0x6000001F`; error1 returns BOOL0/CPSR`0x2000001F`.

Translate's positive model remains exactly one four-byte write at file.error20
and R0=result0/1, preserving other registers/CPSR and returning to actual LR.
Its native body, directory ID/property delivery, IS_SYNC transitions and
card/thread work are not exercised. A true Send BOOL under this projection
does not establish a naturally completed directory Find operation.

## I metodi e gli strumenti da usare

First reproduce the complete native ExecuteSync parent. Its replay JSON has
four string fields: `parent_config`, `field_contract`, `report`, `raw_dir`.
The nested existing configurations supply your own ROM paths, object recipes
and exact historical report families. Paths resolve from repository root;
keep all fixtures, reports and raw output outside `source/` and Git.

Freeze the earlier Send EN/IT reports and native ExecuteSync report with the
standard-library-only exporter:

```sh
python3 -I -S -B source/features/trainer-strategy/tools/congela_fs_send_native_contract.py \
  --send-en "$SEND_EN" --send-it "$SEND_IT" --native-report "$NATIVE_EXEC_REPORT" \
  --json "$PRIVATE/send-native-fields.json"
```

The campaign export is 133289 bytes, SHA-256
`2a302c8699eb868d7a1351269c59d85d2ec07ae6aa306ecefa1b29ce327166a2`:
16 origins ×11 checkpoints. Nine earlier native phases are preserved, with
their old `final` explicitly renamed `send_pop` at7928. Add the actual
ExecuteSync entry and a **derived**, initially unobserved final80F8 context
projected solely from that POP and its six saved words. Registers not popped,
flags, frame and archive are preserved. The export predates the new predictor
and guest; bodies and inputs were already known, not blind. Re-export equality
and authentication of historical reports are separate checks.

Use the existing project Python environment: ndspy4.2.0, Capstone5.0.9 distribution
(module5.0.7), Unicorn2.1.4. The qualified compiler is Clang21
SHA-256`fc5e3cbba6ad54059295cad716aacb05ace8235f5f7a6031f1d8c15d24bd6d66`,
ARM946E-S/ARMv5TE ARM mode. No new compiler invocation is needed. Prepare-only
still needs these dependencies and authenticates current source/ROM/object
identities and all ancestor raw semantics without starting their guests.

```sh
python3 -B source/features/trainer-strategy/tools/attribuisci_fs_send_native_callees.py \
  --parent-config "$NATIVE_EXEC_REPLAY" --field-contract "$PRIVATE/send-native-fields.json" \
  --prepare-only --json "$PRIVATE/send-native-prepare.json"
python3 -B source/features/trainer-strategy/tools/attribuisci_fs_send_native_callees.py \
  --parent-config "$NATIVE_EXEC_REPLAY" --field-contract "$PRIVATE/send-native-fields.json" \
  --probe --raw-dir "$PRIVATE/send-native-probe-raw" --json "$PRIVATE/send-native-probe.json.gz"
```

Review the first probe before running the same producer without `--probe`,
using fresh report/raw paths. The report must be outside the exact raw
directory. Keep one producer, at least 10 GiB free after a planned 1 GiB peak,
180s/command,1 GiB OS RSS,2 MiB logs and16 MiB case output. The first probe
passed in 12.065s with 882343936 bytes OS peak RSS; this is host validation cost,
not game performance or DS timing.

The pure oracle composes the old Send source transitions with the qualified
native ExecuteSync oracle and an explicit readonly POP. It never invokes a
parent image builder or guest. Its internal zero-digest legacy shape sentinel
is not memory authentication or exported provenance. The collector runs one
CPU without reinjecting RAM/registers at checkpoints; only the declared
Translate model mutates guest state from the host. All native reads/stores and
model stores are distinct. Absolute final image hashes include code and dead
stack. Grouping requires literal full CPU/RAM **and external Translate policy**;
identical initial RAM with result0/1 does not authorize merging interactions.

### Counterexamples and acceptance

The normal source prediction is221 native hook records,177 unique starts,
41 native stores,54 reads and223 total callbacks including one model and the
stop gate. False conditional ARM starts are included as hooks, not claimed
hardware work. Wakeup bypass is a declared negative adding a second model only
there:200/167/35/47 and203 callbacks. It must return normally and converge in
full final CPU/archive/live caller state, while exactly frame416 offsets64–71
remain different. The original Send POP reads112–135 and cannot erase those
eight retained Wakeup bytes.

Frozen comparisons check full16 registers and complete416-byte frame/archive92
at all11 phases; OFF must preserve all CPU/RAM/model/checkpoint fields without
projection. A bypass disguised with normal policy/services/checkpoints must
still fail native activation counts. Mutating predecessor guard bytes and
coherently updating the source transcript may converge after PUSH; it must
still fail the original input provenance comparison. Source consistency alone
does not authenticate the exact required input.

```sh
python3 -B -m unittest discover -s source/features/trainer-strategy/test \
  -p 'test_fs_send_native_callees_*.py' -v
SGP_FS_SEND_NATIVE_REPLAY_CONFIG="$PRIVATE/send-native-replay.json" \
  python3 -B -m unittest discover -s source/features/trainer-strategy/test \
  -p 'test_fs_send_native_callees_*.py' -v
```

The optional replay JSON uses the same four keys, now pointing to this case's
parent native ExecuteSync configuration, frozen fields, complete report and
raw directory. Without private inputs the raw replay is an explicit skip.
Replay tests do not launch a new guest.

### Results and limits

Twelve guest runs over four literal CPU/RAM/policy groups pass: normal, OFF
and Wakeup bypass. There are 32 frozen member checks (16 origins × normal/OFF),
four exact OFF comparisons and 16 negative member checks. The normal run
agrees with all 176 earlier/derived checkpoints. Thirteen tests pass with zero
skips, including raw replay and coherent predecessor-guard input forgery
checks without a new guest. The complete grid costs 13.777s/882540544 bytes OS
peak RSS; the test invocation costs 12.897s/881262592 bytes (unittest's internal
7.198s is a different interval). Independent raw review verifies all 12 records,
100 source identities, 24 new-image hashes and the original Send before hashes
using a separate streaming reconstruction.

Documented SDK provenance, reconstructed assembly
bytes, finite semantic equivalence and actual continuous activation remain
separate conclusions. Original Metrowerks C generation, native Translate,
nonempty queues/scheduling, Async/callbacks, natural filesystem/card, higher
caller integration and persistent-save/hardware acceptance remain unqualified.
CPU17 is the Cortex-A15 Unicorn backend, not ARM946 silicon timing or interrupt
delivery. No game optimization or recovered resource budget is inferred.
