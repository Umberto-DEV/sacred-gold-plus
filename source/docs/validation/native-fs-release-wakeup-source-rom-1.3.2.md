# Native Release and empty Wakeup in one CPU context

This joins the original [Release](native-fs-release-source-rom-1.3.2.md) and
[empty Wakeup](native-os-wakeup-source-rom-1.3.2.md) paths from the actual incoming
Release context. The finite question is whether the previous caller-visible
registers, frame328, archive92 and queue8 remain equal while both native bodies
execute, with their real nested stack and volatile registers. This is an isolated
composition, not the complete filesystem caller or a game modification.

## Cosa farebbe un professionista di alto livello che non sto chiedendo

Use the original caller entry and one CPU/RAM image throughout; do not replace
the entry with a reconstructed callee return. Freeze the earlier caller outputs
before the new guest and compare them without calling the new predictor. Require
native instruction identities, full registers, memory events and actual boundary
observations as a separate proof. A modeled bypass can preserve the application
result while omitting the native path. Compare it under the **same complete code
and initial image**, account for its missing stack writes and reject it even when
positive policy/model metadata is disguised. Review source, ABI, ownership and
raw results independently; distinguish provenance links from distinct CPU states.

## Il materiale più grezzo da cui partire

Use your own exact inputs in the [Send input table](native-fs-send-source-rom-1.3.2.md#il-materiale-più-grezzo-da-cui-partire)
and the qualified earlier Release and Wakeup campaigns. EN/current localized IT
are IPKE revision0; retail IT is IPKI revision0. ARM9 file offset `0x4000`,
load `0x02000000`, entry `0x02000800`. All four bodies are retained main ARM9
code. Current mapping is uncompressed and resident; no overlay/autoload lifetime
or new installer is introduced.

| Component | RAM address | Current ROM offset | Bytes | SHA-256 |
| --- | --- | --- | --- | --- |
| Release | `0x020D6864` | `0x000DA864` | 92 | `658daf608846bdeca5f8d48b8b0ea7d46280ebcd2ef783fce8b5f9e12735f568` |
| Wakeup | `0x020D1ECC` | `0x000D5ECC` | 104 | `25c7d621d6b4d855be6828b9ec8d98162df8ecdda5a22db405caf344aa4102db` |
| Disable | `0x020D3A38` | `0x000D7A38` | 20 | `a8cdb747f9936730571b220bb9570615892665b120713ffc59b1cb2d7dee76ff` |
| Restore | `0x020D3A4C` | `0x000D7A4C` | 24 | `46b5111b6fad094dfff177dca974d33b477cb72772ecfe95b74b1c7f656bc4fd` |

The earlier independent readers establish each component across retail→base1.1→V4→r4
EN/IT; this case reuses those historical results and rechecks all four current
components in both exact ROMs against physical mapping, ndspy and qualified ELF
objects. Older compressed-image addresses still require section decoding.

Source counterparts are `FS_command.c::FSi_ReleaseCommand`,
`os_thread.c::OS_WakeupThread` and the original IRQ leaves at
[reference pin cb614ad23449d5852b40321dc409c4143872b35c](https://github.com/ctrl-cheeb-del/pokeheartgold/tree/cb614ad23449d5852b40321dc409c4143872b35c).
The linked component guides retain full source/definition/header hashes and
recovered recipe commands. Release object SHA-256
`7bf95cfa7e9f0abca8f3cafccc2f276a66725a2331d0f6b8e6b4588ed423526a`;
Wakeup object SHA-256
`301ee02865717259040b07b1e5f162ef43287f8b91882633cb2b0d1d805426b4`.
No recompilation is needed for this composition. The original MW C toolchain is
still missing; recovered assembly correspondence is not original C codegen.
The Wakeup guide explains explicit local Clang APCS aggregate-layout compatibility
with unmodified headers, including scalar u64 alignment8.

### Caller, state and stack

The input is the earlier **Release entry**, R0=file/R1=translated0 or1,
SP=TOP−312, SYS ARM/I0. File=`0x023BEDD0`, archive=`0x021E3654`, TOP=`0x023BEEC0`.
Release PUSH16 then Wakeup PUSH24 reach frame352/peak40. Copy all original328
frame bytes and the last24 captured guard bytes. The new lower guard56 is24
declared fill bytes plus32 retained original guard bytes. Only24 bytes are new
unknown fill; a nonuniform portable fixture verifies the equation.

Release BL `0x020D68B0` supplies the actual empty queue at file+24, SP=TOP−328,
LR=`0x020D68B4`, I1. Wakeup's original POP returns to that MOV instruction.
The collector observes the entry and return without forcing either context.
Native Wakeup returns void residue R0=`0x80`, R1/R2=`0x6000009F`, LR=`0x020D1F30`.
Release MOV r0,r6 and its Restore call absorb the volatile differences. Final
full16 equals the earlier normal Release: R0=`0x80`, R1=`0x6000009F`,
R2=`0x6000001F`, LR=`0x020D68BC`, CPSR=`0x6000001F`, original SP/callee-saved.
The original ExecuteSync return fetch `0x020D7760` is stopped before its LDR.

Archive flag`0x13`, no ACTIVATE, and empty queue originate in the declared earlier
source fixture, not natural boot initialization. Command4 remains4. Nonempty
thread removal/rescheduling is skipped. Hypothetical complete-caller peak672
exceeds its earlier608-byte ownership bound; this isolated case does not enlarge
that bound or qualify the complete caller.

## I metodi e gli strumenti da usare

Use the [source-to-ROM method](../test-bench.md#linking-source-to-an-exact-rom)
for whole-ROM composition and input preparation. Commands below run from root
with your project Python environment: ndspy, Capstone and Unicorn2.1.4 are
required by native/source imports even during CPU-free preparation. The earlier
contract exporter uses the standard library only. Keep reports, raw RAM, ROMs,
BIOS, saves and fixtures private; original fixtures remain read-only.

First reproduce complete earlier Release and Wakeup campaigns with your own
inputs. The Wakeup replay config contains exactly five string paths:
`parent_config,recipe_dir,field_contract,report,raw_dir`. Its `parent_config`
points to the earlier EN/IT Release replay config, not another Wakeup report.
A valid Wakeup probe is explicitly rejected as a parent; complete source/raw/
OFF/frozen authentication remains mandatory after that metadata gate.

Before the new guest, export the earlier **Release** caller-output contract:

```sh
python3 -I -S -B source/features/trainer-strategy/tools/congela_release_wakeup_contract.py \
  --en-report "$RELEASE_EN_REPORT" --it-report "$RELEASE_IT_REPORT" \
  --json "$PRIVATE/composition-fields.json"

python3 source/features/trainer-strategy/tools/attribuisci_release_wakeup.py \
  --parent-config "$WAKEUP_REPLAY_CONFIG" --field-contract "$PRIVATE/composition-fields.json" \
  --prepare-only --json "$PRIVATE/composition-prepare.json.gz"

python3 source/features/trainer-strategy/tools/attribuisci_release_wakeup.py \
  --parent-config "$WAKEUP_REPLAY_CONFIG" --field-contract "$PRIVATE/composition-fields.json" \
  --raw-dir "$PRIVATE/composition-raw" --json "$PRIVATE/composition-report.json.gz"
```

Use fresh private output files/directories outside `source/`. `--probe` selects
only the first group/normal policy and is mutually exclusive with `--prepare-only`.
Guest execution requires `--raw-dir`. Preserve command argv, exits, executable/
source/input hashes, resource limits and the contract's chronological receipt.
The file cannot prove its own creation time. Here16 cells were frozen before the
first composition guest; a later stdlib export reproduced the complete original
JSON byte-for-byte. This is prospective relative to the new guest, with known
previous sources/inputs, not a blind experiment.

Preparation authenticates the full earlier Wakeup matrix, all ancestors and
four code/ELF bodies in each ROM. It binds the original Release input to the
earlier actual nested Wakeup entry and guard. Eighty-six runtime source identities
are snapshotted before the probe and checked after execution. The qualified
whole-image grouping function is reused unchanged with its bench binding changed:
literal equality covers the complete initialized4MiB, entry16, entryPC, CPU17 and
Unicorn2.1.4. Sixteen provenance links yield four distinct states; language/seed
duplicates are shared runs. ON/OFF/fill39/bypass still execute separately.

### Separate caller equivalence from native activation

Normal runs have four native bodies and no modeled callee or host state writes
after initialization. Live code, permitted PC/word owners, actual boundary
registers and memory preimages are checked. Expected transcript:55 full register
contexts,44 unique starts,15 stores,14 reads and56 hooks including the original
return fetch. Disable/Restore each execute twice. Whole4MiB readback has no mask.

The bypass policy retains identical code and initial memory but explicitly models
Wakeup as a return-only R0=0 boundary with zero RAM writes. It preserves final
full16, frame328, archive92 and queue8. It omits the native six-word PUSH in
`[TOP−352,TOP−328)`, so native activation fails. Its34 native contexts/9 stores/
7 reads/36 hooks/16-byte peak must not be labeled normal. Positive policy,
service and boundary metadata are disguised in a copied receipt; retained actual
steps36 versus56 must still reject it. The unchanged earlier-output contract can
pass both paths and explicitly claims no native activation on its own.

Do not compare earlier Release and this composition as though only stack changed:
the earlier image held a four-byte modeled NOP plus fill where the104-byte native
Wakeup body now resides. The controlled bypass avoids that confound by using the
same complete code image. Both absolute whole-RAM hashes remain checked.

```sh
python3 -I -S -B -m unittest discover \
  -s source/features/trainer-strategy/test -p 'test_release_wakeup_freeze.py'
SGP_RELEASE_WAKEUP_REPLAY_CONFIG="$PRIVATE/composition-replay.json" \
python3 -m unittest discover \
  -s source/features/trainer-strategy/test -p 'test_release_wakeup*.py'
```

Private replay config has string paths `parent_config,field_contract,report,raw_dir`.
It replays raw/report/grid/source/proof/groups/earlier contract, all OFF/counter/
member proofs without guest execution. Private inputs missing means an explicit
skip, not qualification. Portable tests distinguish a complete parent from its
valid probe, check metadata before heavy work, exact configuration keys, guard
provenance, full composed predictions and strict integer/boolean contracts.
The test pattern preserves the older Release/Wakeup replay interfaces.

### Results and limits

The first native probe and independent raw/streaming whole-RAM review pass.
The full16-run campaign passes for four states, each normal/OFF/fill39/bypass,
with64 earlier-output proofs and four exact OFF pairs. Four bypass controls
retain the earlier caller outputs but fail native activation after metadata
disguise. Twelve tests pass with zero skips when own private replay inputs are
supplied (11 portable obligations and one private replay obligation). Campaign
9.645s/863846400 bytes peak OS RSS; replay/tests9.619s/863141888 bytes. These are
host tool costs. Final independent review checks all16 raw records,32 whole-image hashes by streaming,64 earlier-output proofs and four exact24-byte bypass differences. It reports no open findings. Component source provenance
and recovered binary correspondence retain their earlier limits. No original
MW C rebuild, thread/scheduler activation, complete upstream caller, natural
filesystem completion, silicon timing/IRQ delivery, SAVE/cold or device result
is established. No game performance/resource improvement follows from these
host tool checks. The reusable additions are same-context composition, an
independent earlier-output contract, same-code bypass falsification and full
raw-bound replay, rather than new game code.

The [empty Next follow-up](native-fs-next-source-rom-1.3.2.md) uses this observed return checkpoint through the original caller bridge. It is a separate downstream case and does not expand these records into a complete upstream caller.
