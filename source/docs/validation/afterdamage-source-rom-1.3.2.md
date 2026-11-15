# Native AfterDamage continuation from state0

The exact r4 EN/IT code reaches the erroneous no-item flinch **script request**
from native AfterDamage state0. HpCalc produces damage−200,the HP script updates
300→100,and native states0..6 preserve that signed word through the critical and
Shaymin checks until the installed helper clears it and requests script14.
The previous getter calls traverse the same intermediate scripts without that
request. Script14 is not executed here; applying its effect remains unqualified.

This closes the earlier [explicit-state6 gap](hp-flinch-source-rom-1.3.2.md) for
one controlled neutral path. It does not establish a naturally played battle.
See the [owner](../../features/type-consumers/README.md),
[source-to-ROM method](../test-bench.md#linking-source-to-an-exact-rom) and
[original helper/source attribution](uturn-source-rom-1.3.2.md).

## Cosa farebbe un professionista di alto livello che non sto chiedendo

Remove the host state6 injection and follow real controller increments and
script dispatch instead. An earlier clear,guard,secondary effect,ability or RNG
transition could disprove the isolated-consumer hypothesis. Execute required
scripts even when their names suggest a no-op: state0 always loads CriticalHit.
Check every intermediate state and the final summary against raw execution.
Independent Sol6.1 review read raw/helper/script lineage,executed current and
previous-hook Italian chains and checked a distinct message-type path. A final
metadata mutation which retained the same script request exposed an incomplete
summary oracle; the verifier and regression test now reject it.

## Il materiale più grezzo da cui partire

Use your own exact revision0 retail,Plus1.1,V1.3 V4 and r4 inputs as prepared in
the [input instructions](fairy-flags-source-rom-1.3.2.md#il-materiale-più-grezzo-da-cui-partire).
Whole sizes/SHA-256 are in [`baseline.py`](../../sgp131/baseline.py) and the
[r4 contract](../../distribution/game-1.3.2-r4.json); all four images for the
selected language are authenticated. No ROM,save,BIOS,retail dump,asset or
private capture is supplied. The own helper source/ELF/placement was qualified
in the [preceding attribution](uturn-source-rom-1.3.2.md) and remains unchanged.
No compiler,whole-ROM build or runtime capture is used here.

Native source correspondence is reference commit
`cb614ad23449d5852b40321dc409c4143872b35c`,
`battle_controller_player.c::{BattleControllerPlayer_HpCalc,
BattleControllerPlayer_AfterDamage,BattleControllerPlayer_RunCriticalHitScript,
BattleControllerPlayer_TryFollowupMessage,TryBuildRage}`,
`battle_util.c::{BattleSystem_TryIndirectSideEffect,CheckAbilityEffectOnHit}`
and `battle_command.c` for the interpreter and script commands. The original
native C/compiler/object is not reconstructed. Raw script16 and293 hashes are
identical across retail→Plus1.1→V4→r4 in both languages; this documents inherited
provenance rather than attributing their bytes to a new Plus compilation.

| Additional native dependency | Current logical extent and composition |
| --- | --- |
| CriticalHit helper | `0224DF7C..0224DF98`,28 bytes,26 code+2 alignment. Always loads member16. |
| Followup | `0224DF98..0224DFEC`,84 bytes,78 code+2 alignment+4 pool. Move-status zero returns without another script. |
| TryBuildRage | `0224DFEC..0224E078`,140 bytes,126 code+2 alignment+12 pool. Target Rage bit absent takes the neutral return. |
| TryIndirectSideEffect | `02250490..022506D4`,580 bytes,542 code+2 alignment+36 pool. Flags `CTX+2174/2178` zero select a path with no writes or RNG. |
| AbilityOnHit | `02253E04..022543A0`,1436 bytes,1410 code+2 alignment+24 pool. Native CheckSubstitute `02256838..02256854`,28 bytes;no substitute and modeled ability0 select the neutral return. |
| Species comparison | Opcode33→`0223E474`,184 bytes,including a14-byte jump table and alignment. Native GetBattlerVar entry `0224EDE0..0224EE02`,case0 table entry `0224EE02`→`0224EECC..0224EED0`,returns target species with null output pointer. |

Complete fixed SHA-256 values and executable/data subsets are in the
[verifier](../../features/type-consumers/tools/attribuisci_afterdamage.py).
The relevant species branch is distinct from the move/PP cases qualified in the
[native getter case](native-move-callers-1.3.2.md).

All code above is in BLZ overlay12,current base `022378C0`,decoded226176 bytes,
BSS0. Current EN stored range is `08314200..0833B940`,IT `08800000..08827740`.
Header/y9/FAT,stored/decoded hashes and independent decoder agreement are in each
report; decompressed instructions have no linear physical offsets. The helper
is ARM9 autoload `023D5A20`,physical `001252E0`,qualified separately. Retail IT
logical locations are−60hex. Only verified ARM9 call fields and the shared VM's
two pointer literals are normalized in comparison copies; target entry bytes
and instruction targets are checked before normalization. Actual execution
always uses unmodified current bytes.

## I metodi e gli strumenti da usare

[`attribuisci_afterdamage.py`](../../features/type-consumers/tools/attribuisci_afterdamage.py)
reuses the qualified Python3.14.7,ndspy4.2.0,Capstone5.0.9 and Unicorn2.1.4 tools.
Supply private paths and fresh private report outputs:

```sh
python3 source/features/type-consumers/tools/attribuisci_afterdamage.py --language EN \
  --rom "$R4_EN" --v4 "$V4_EN" --base "$BASE11_EN" --retail "$RETAIL_EN" \
  --json "$CASE/afterdamage-EN.json"
python3 source/features/type-consumers/tools/attribuisci_afterdamage.py --language IT \
  --rom "$R4_IT" --v4 "$V4_IT" --base "$BASE11_IT" --retail "$RETAIL_IT" \
  --json "$CASE/afterdamage-IT.json"
SGP_R4_ROM_DIR="$R4_DIR" SGP_R4_ROM_NOME='r4-%s.nds' PYTHONPATH=source \
  python3 -m unittest sgp131.test_type_consumers.CurrentAfterDamageContinuation -v
PYTHONPATH=source python3 -m unittest \
  sgp131.test_type_consumers.AfterDamageAttributionCLI -v
```

The CLI writes evidence and deliberately exits1 for the failed no-item script
request compatibility gate. An exception before report generation is a distinct
input/tool failure. Five fixture methods pass by detecting the recorded behavior
and rejecting invalid evidence; they do not certify repaired game behavior.
Missing private fixtures skip explicitly. Twelve no-ROM CLI cases check direct,
symbolic and hardlink aliases; output cannot replace any input.

The report contains35 native windows per role,140 per language,the two scripts'
lineage,five current chains and one previous-hook control per language. Guest
stack peaks at160 bytes in the reused HP path,104 in the new Shaymin script path;
fixture-suite maximum RSS was about227 MB. Each entry has a20000-instruction
limit and the outer continuation loop is bounded to16 entries. Native r0/r1 ABI,
output pointers,null GetBattlerVar output,SP,r4–r11,Thumb state,cache/code/data,
stack/caller canaries and store-site/field/width domains are checked. Declared
host NARC copies have separate context ranges from permitted guest stores.

| Raw intermediate script | Exact identity and exercised path |
| --- | --- |
| CriticalHit16 |204 bytes,SHA-256 `fe5396d502582ed49c1f9ed85f9fb65851b12e0bed6a877c779b573a66dbdb61`. Var44 maps via native case `0224572E`/pool `02245868` to `CTX+2150`. Multiplier1 takes comparison0→End at word50. Initial zero would enter another path. |
| CheckShayminForm293 |396 bytes,SHA-256 `ab0c96cc5eea84c41088214cbc3460414ac0d149d3fd6aa85fac26ee7f383726`. Target var16 is `CTX+006C`;target1 continues. Opcode33 reads species7 rather than492 and jumps to End at word98. The form-changing branches are not executed. |

For message type0,the real entry/resume checkpoints are:

| Checkpoint | AfterDamage state | Shared word | Target HP |
| --- | --- | --- | --- |
| Initial HpCalc input |0|0|300|
| Native HP script return |0|`FFFFFF38`|100|
| Critical script requested/returned |1|`FFFFFF38`|100|
| Shaymin script requested/returned |4|`FFFFFF38`|100|
| Installed consumer requests script14 |7|0|100|
| Previous-hook control completes |0|`FFFFFF38`|100|

Native store records prove increments1,2,3,4,5,6,7;state6 is never injected by the
host. Message type1 places Followup later but still traverses states0..6. The
intermediate scripts and neutral helpers consume no RNG. Actual native RNG and
ARM division occur in the erroneous consumer; Bite44 fails eligibility after
the RNG draw and requests no flinch script. Damage−199 also requests no flinch
script but clears the native word;damage0 omits the HP script. A changed final
summary state is rejected even when all script requests and underlying native
store records remain unchanged;summary and first/last checkpoints must agree.

NARC loading,ability lookup0,UI emission,transport-ready success,cache preparation
and asynchronous Party packet transport are explicit models. Actual controller,
helper,script command,variable/species lookup,item decoding,HP/copy emitter,RNG
and arithmetic paths execute. The shared host-range hook leaves prior defaults
unchanged: ten HP and fourteen producer complete JSON result records compare
equal after reuse. Serialized tuple arguments are compared in their JSON array
representation. Historical reports are preserved with their original source IDs.

This is observed native execution of a controlled HpCalc→AfterDamage path,not a
naturally played move or arbitrary battle-state equivalence. Nonneutral critical,
secondary effects,Rage,abilities,Shaymin form changes,other callbacks,whole pivot,
PartyMon encrypted mutation,SAVE,cold restart,hardware and timing remain open.
Script14 is only requested;no target flinch bit or turn-loss behavior is claimed.
Both installed compatibility defects remain open. No game ASM,ROM,save,ID or ABI
change,optimization or memory reclamation is included. Any later repair requires
source/byte rebuild and ordinary/pivot/lifetime/save/device verification before
acceptance;this case supplies stronger evidence for that separate decision.

The later [native flinch effect](flinch-effect-source-rom-1.3.2.md) executes the
requested script14 and its ability/status gates. It qualifies target bit application
for its initialized inputs;turn loss remains a separate consumer.
