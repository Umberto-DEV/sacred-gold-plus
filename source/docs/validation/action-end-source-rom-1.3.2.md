# Native completion after flinch cancellation

The exact r4 EN/IT continuation now executes UpdateMoveHistory39 and ordinary
ActionEnd40 after the [native cancellation case](flinch-consumer-source-rom-1.3.2.md).
It marks the selected action40,advances executionIndex0→1,performs native reset
and reaches controller8. Both initialized Pokémon retain their HP and35 PP.
The preceding no-item cancellation defect remains unfixed. Command8 and natural
turn selection are not executed.

See the [owner](../../features/type-consumers/README.md),
[source-to-ROM method](../test-bench.md#linking-source-to-an-exact-rom) and
[own helper reconstruction and compatibility findings](uturn-source-rom-1.3.2.md).

## Cosa farebbe un professionista di alto livello che non sto chiedendo

Follow actual canceled-action memory into native completion,including ordinary
heal,experience,battle-over,entry-ability,form,item,vanish and reset gates. Do not
substitute a service deciding that an action completed. Check which row is
marked:the native code uses executionOrder[executionIndex],not attacker alone.
An incoherent-order counter reaches the same command8 but completes the wrong
actor,and must fail. Preserve cancellation evidence before Init legitimately
clears temporary state. Check every native bulk store and RNG transition rather
than treating all neutral ability checks as RNG-neutral. Independent Sol6.1
review replicated the ordinary Italian path and inspected raw dispatch,ABI,
clear buffers and evidence limits.

## Il materiale più grezzo da cui partire

Use your own exact revision0 retail,Plus1.1,V4 and r4 images following the
[input preparation instructions](fairy-flags-source-rom-1.3.2.md#il-materiale-più-grezzo-da-cui-partire).
Whole hashes and sizes are in [`baseline.py`](../../sgp131/baseline.py) and the
[r4 identity contract](../../distribution/game-1.3.2-r4.json). Each CLI authenticates
all four roles for its selected language. No ROM,retail dump,asset,save,BIOS or
private capture is included. Script15/278 lineage and the actual produced-bit
chain are qualified by the [preceding case](flinch-consumer-source-rom-1.3.2.md).

Native source correspondence uses the
[pinned HGSS reference tree](https://github.com/ctrl-cheeb-del/pokeheartgold/tree/cb614ad23449d5852b40321dc409c4143872b35c),
`battle_controller_player.c::{UpdateMoveHistory,ActionEnd,UpdateTargetMoveHistory,
TryGrantExp,CheckBattleOver,TryVanishOff,ResetActionStatus}` and
`battle_util.c::{TryAbilityOnEntry,CheckStatusHealAbility,Battler_CheckWeatherFormChange,
CheckUseHeldItem,ChooseTraceTarget,BattleContext_Init}`. The original native
C/compiler/object is not reconstructed. Own Plus helper compilation/composition
is inherited unchanged from the [U-turn reconstruction](uturn-source-rom-1.3.2.md).
No compiler,ROM build or runtime capture is needed here.

| Additional native component | Current location and authenticated extent |
| --- | --- |
|UpdateMoveHistory39|`0224D23C..0224D368`,300B=276 code+24 pool;SHA-256 `7a0f6b67eb736c852a87ece8e6d6d3cea720ec4cc0b5634799184d16459d4b9e`.|
|ActionEnd40|`0224D368..0224D448`,224B=218 code+2 alignment+4 pool;SHA-256 `b62b821962ed2e8b3fcc2adc27bceda9b04e2b455fa4642e68540d0e4fe02f07`.|
|Target history / Metronome fail bookkeeping|`0224DD74`520B / `02256694`180B.|
|Status-heal / experience / battle-over gates|`022543A0`392B / `0224DD18`92B / `0224D7EC`888B.|
|Ability entry / form / held-item gates|`02253194`3084B / `02256914`1556B / `02254E7C`1696B.|
|Trace target / weather / opponent selector|`022585B8`164B / `0223BAF8`12B / `0223ABB8`104B.|
|Vanish / action reset / context Init|`0224E130`140B / `0224DC0C`104B / `02250F44`244B.|
|Native CpuClearFast|ARM `020D4858..020D48B4`,92B,SHA-256 `10577c29bdbc6913eba507a029157099a73f377ee8d0e6617ff2cc72def5f8a5`.|

The [tool](../../features/type-consumers/tools/attribuisci_actionend.py) fixes all17
full-window hashes and executable subsets,excluding literal islands,jump tables
and alignment. Combined with earlier windows,it checks79 per role,316 per
language. Controller table `0226CA90` slots39/40 point to the two Thumb entries.

Overlay12 remains BLZ,base `022378C0`,decoded226176B,BSS0;current stored spans
EN `08314200..0833B940`,IT `08800000..08827740`. Independent raw header/y9/FAT/BLZ
readback is compared with ndspy. A decoded instruction has no linear physical
file offset. The own helper remains in ARM9 autoload at `023D5A20`,physical
`001252E0`. CpuClearFast is read through the ARM9 section mapping.

Retail IT logical overlay addresses differ by−60hex. New comparison rules
validate ARM9 call destinations and target code signatures before normalizing
branch fields. The unexercised nature-stat reader uses its20-byte body;its
regional data pool and semantics are not qualified by that signature. One
literal at `02253814` references stat-ratio table `0226CB88`:the exact regional
pointer,four native LDRs and26 unchanged table bytes are verified. These are
comparison copies only. Actual execution uses intact current instructions and
data;no general relocation or unused-branch activation is inferred.

## I metodi e gli strumenti da usare

Use qualified Python3.14.7,ndspy4.2.0,Capstone5.0.9 and Unicorn2.1.4,with your own
private inputs and fresh report paths:

```sh
python3 source/features/type-consumers/tools/attribuisci_actionend.py --language EN \
  --rom "$R4_EN" --v4 "$V4_EN" --base "$BASE11_EN" --retail "$RETAIL_EN" \
  --json "$CASE/action-end-EN.json"
python3 source/features/type-consumers/tools/attribuisci_actionend.py --language IT \
  --rom "$R4_IT" --v4 "$V4_IT" --base "$BASE11_IT" --retail "$RETAIL_IT" \
  --json "$CASE/action-end-IT.json"
SGP_R4_ROM_DIR="$R4_DIR" SGP_R4_ROM_NOME='r4-%s.nds' PYTHONPATH=source \
  python3 -m unittest sgp131.test_type_consumers.CurrentNativeActionEnd -v
PYTHONPATH=source python3 -m unittest \
  sgp131.test_type_consumers.ActionEndAttributionCLI -v
```

Both CLI runs generate evidence and deliberately exit1:attribution/completion
passes,but no-item action compatibility fails. An exception before generation
is a separate input/tool failure. Five fixture methods pass by detecting the
recorded behavior and rejecting altered evidence;missing private ROM fixtures
skip explicitly. Twelve CLI path/symbolic-link/hardlink cases protect all four
inputs from JSON replacement before analysis.

Before any guest instruction,the fixture initializes execution order1,0,2,3,
index0,action commands23,23,Tackle33 and35 PP in both live BattleMons,HP300/300,
and explicit previous-move history33. The inherited HP path reduces battler1 to
100 HP,produces the erroneous flinch bit and natively cancels its next selected
action. The prior controlled actor-selection boundary remains explicit. No
host assignment marks an action40,advances the index or clears temporary state.

UpdateMoveHistory executes actual held-item lookup,target history and Metronome
bookkeeping. It clears the declared previous/protect/hit/conversion fields,
sets missing-battler history values toFF,and returns command40. ActionEnd uses
ordinary battleType0;Safari/Pal Park shortcuts are not used. Heal,experience and
battle-over gates return neutral through actual code with both battlers live.
Ability-entry states0..15/reset0 execute actual weather/opponent/ability/form/
item checks. No model returns their cancellation/completion decisions.

ChooseTraceTarget is called for both battlers before checking whether their
abilities are Trace. In this initialized path it consumes two actual native RNG
calls despite Overgrow65/Torrent67. The recorded seed6488064 becomes2686024554
after two LCG steps. This is observed native behavior within this fixture;
removing those calls would alter the RNG stream and is not a safe optimization
inferred from unused Trace results. Other ability/weather/status branches are
not exercised.

After native vanish/reset checks,the store at `0224D3FE` marks
`CTX+21A8+16*executionOrder[index]`,here actor1 at `CTX+21B8`,with40. Store
`0224D434` advances `CTX+00EC` from0 to1. Native Init resets move-status/controller
states and four28-byte SelfTurnData buffers starting at `CTX+02D4`. Its real ARM
CpuClearFast runs four times and issues28 exact zero word stores at `020D48A4`.
AI switched-slot bytes `CTX+21A4..21A8` become6. Store at `0224D43E` sets command8;return is at `0224D440`.
Flinch failure mask40 remains at `CTX+0348`;the earlier cancellation evidence is
checkpointed before reset. HP300/100 and both35 PP counts are unchanged.

The new native-bulk freeze allowance is separate from host script-copy ranges.
Every guest store still needs its precise native PC,field,width and loop/buffer
bounds. The clear ABI requires value0,size28,each expected destination and native
return;SP,r4–r11,caller/stack canaries,code/data/cache and unrelated memory remain
checked. Maximum native guest stack is328B;the fixture suite used about245 MB
RSS. Extending the runner with default-empty guest ranges and a default-preserved
RNG policy leaves six complete preceding-case EN/IT result records unchanged.

The named wrong-order RAM fixture initializes order0,1 while attacker remains1.
It reaches the same command8 and index1 but marks actor0 instead of1. The exact
selected-row/cancellation continuity oracle rejects it even if its report label
is changed to current. Additional tests reject changed native dependencies,
summary/stores/RNG/buffer evidence,and bulk writes with overflow,misalignment,
wrong width or nonzero fill. A final controller value alone is insufficient.

Provenance and native source correspondence are documented;own Plus binary
reconstruction is reused. Native completion is observed for the initialized
ordinary canceled-action path. It is not a natural battle capture or execution
of command8. Natural order selection,other abilities/statuses,battle outcomes,
Trick Room reordering,whole pivot,PartyMon asynchronous transport,SAVE,cold
restart,hardware and timing remain open. Earlier NARC/UI/Ready/cache/transport
models remain explicit;the new history/action-end closure invokes none. Both
game defects remain unfixed. No game ASM,ROM,save,ABI,ID or settings changes are
included. Repair and broader acceptance remain separate maintainer decisions.
