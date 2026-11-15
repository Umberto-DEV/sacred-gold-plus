# Native next-action dispatch after flinch completion

The exact r4 EN/IT continuation now runs controller8 and the complete
FightInput13 handler after [native action completion](action-end-source-rom-1.3.2.md).
It selects the remaining actor0,sets Tackle33,target1 and returns to TryMove23.
Changing relative speeds changes turnOrder while the inherited executionOrder
and selected action remain unchanged. A direct pending23 counter reaches the
same final command but leaves the old attacker1/target0.

TryMove23 for the new actor is not executed. This remains an initialized host
path with explicit initial action order;both installed game defects are unfixed.
See the [owner](../../features/type-consumers/README.md),
[source-to-ROM method](../test-bench.md#linking-source-to-an-exact-rom) and
[original helper compilation/composition](uturn-source-rom-1.3.2.md).

## Cosa farebbe un professionista di alto livello che non sto chiedendo

Separate turnOrder from executionOrder and a selected handler from initialized
attacker/move/target state. Start with native FIGHT_INPUT13 action rows instead
of the preceding case's explicitly late23 rows. Require FightInput's complete
return:it writes command23 before target selection finishes. Check native speed
arithmetic,ability/item scans,RNG,exact field stores and another speed ordering.
Reject a stale-actor counter even when command23 matches. Independent Sol6.1
review replicated Italian positive,reverse-speed and stale-actor paths,then
rejected removed target/return evidence and wrong division results.

## Il materiale più grezzo da cui partire

Use your own exact revision0 retail,Plus1.1,V4 and r4 images following the
[input instructions](fairy-flags-source-rom-1.3.2.md#il-materiale-più-grezzo-da-cui-partire).
Whole hashes and sizes are specified in [`baseline.py`](../../sgp131/baseline.py)
and the [r4 contract](../../distribution/game-1.3.2-r4.json). The CLI authenticates
all four roles for its selected language. No ROM,dump,retail asset,save,BIOS or
private capture is included. The preceding script/helper lineage is reused.

Native source correspondence uses the
[pinned HGSS reference tree](https://github.com/ctrl-cheeb-del/pokeheartgold/tree/cb614ad23449d5852b40321dc409c4143872b35c):
`battle_controller_player.c::{ExecuteNextAction,FightInput}`,
`battle_util.c::{BattleController_TryEmitExitRecording,SortMonsBySpeed,
CheckSortSpeed,CheckAbilityActive,Battler_CanSelectAction,BattleSystem_GetMoveTarget}`
and `battle_system.c::BattleSystem_IsRecordingPaused`. The original native
C/compiler/object is unavailable;this case documents correspondence and observed
native execution. Own Plus helper reconstruction is reused unchanged from the
[U-turn case](uturn-source-rom-1.3.2.md). No compiler,ROM build or new capture is
needed for this extension.

| Additional native window | Current address,extent and role |
| --- | --- |
|ExecuteNextAction8|`02249460..022494DC`,124B=110 code+2 alignment+12 pool;SHA-256 `0dd689792e6a99f35fee48d56c77e1a9dd92837e53e473bc6e5683d897b1b966`.|
|FightInput13|`0224A9B0..0224AAF0`,320B=296 code+24 pool;SHA-256 `ba093f320b0f4918e53aa4aa25ee66038882ad18ed589145cfaffaba3381aaa1`.|
|Recording exit / paused predicate|`022581BC`24B / `0223BFEC`16B. Actual predicate reads bit0 of `BS+2478`;initialized0.|
|SortMonsBySpeed|`02252D3C`136B,132 code+4 pool;resets and sorts turnOrder.|
|CheckSortSpeed|`0224FC48`1832B;native math/ability/item checks and effective-speed cache stores.|
|CheckAbilityActive|`02252324`648B;10-entry table excluded from executable subsets. The exercised scan is type8,all live battlers.|
|CanSelectAction|`022567A0`52B;native status2 checks for recharge/rampage/uproar/locked move.|
|Move target selector|`022506D4`836B;actual selected-live-target path with no redirection or random selection.|

All nine full hashes and code/data subsets are fixed in the
[verifier](../../features/type-consumers/tools/attribuisci_next_action.py).
The complete matrix contains88 windows per role,352 per language. Controller
slots8/13 at `0226CA90` select the Thumb entries. Native signed ARM division
`020F2998..020F2BA4`,524B,is reused with its existing pin;this path uses
denominator10 instead of the preceding flinch arithmetic's100.

Overlay12 remains BLZ,base `022378C0`,decoded226176B,BSS0. Current stored spans
are EN `08314200..0833B940`,IT `08800000..08827740`. Raw header/y9/FAT/BLZ mapping
is compared with ndspy;decoded instructions have no linear physical ROM offset.
ARM9 math is read through its section mapping. The own helper remains at
autoload `023D5A20`,physical `001252E0`.

Retail IT logical overlay addresses are−60hex. New historical comparison rules
verify13 ARM9 call destinations/signatures and four exact table-pointer literals.
Two pointers address numerator/denominator bytes of the26-byte stat-ratio table
`0226CB88` and `0226CB89`;two reference the8-byte speed-halving item-effect table
`0226CB50`. Each rule validates its native LDR binding,regional pointer and table
bytes before normalization. All execution uses unchanged current bytes;the rules
qualify comparison fields rather than all unused branches.

## I metodi e gli strumenti da usare

Use qualified Python3.14.7,ndspy4.2.0,Capstone5.0.9 and Unicorn2.1.4,with your own
private inputs and fresh report paths:

```sh
python3 source/features/type-consumers/tools/attribuisci_next_action.py --language EN \
  --rom "$R4_EN" --v4 "$V4_EN" --base "$BASE11_EN" --retail "$RETAIL_EN" \
  --json "$CASE/next-action-EN.json"
python3 source/features/type-consumers/tools/attribuisci_next_action.py --language IT \
  --rom "$R4_IT" --v4 "$V4_IT" --base "$BASE11_IT" --retail "$RETAIL_IT" \
  --json "$CASE/next-action-IT.json"
SGP_R4_ROM_DIR="$R4_DIR" SGP_R4_ROM_NOME='r4-%s.nds' PYTHONPATH=source \
  python3 -m unittest sgp131.test_type_consumers.CurrentNativeNextAction -v
PYTHONPATH=source python3 -m unittest \
  sgp131.test_type_consumers.NextActionAttributionCLI -v
```

Both CLI runs deliberately exit1 after generating evidence:attribution passes,
but no-item action compatibility still fails. Exceptions before generation mean
separate input/tool failures. Five fixture methods verify this behavior and
reject drift,without certifying repaired gameplay. Missing local ROMs explicitly
skip. Twelve path/symbolic-link/hardlink CLI cases protect all four inputs from
JSON replacement before analysis.

All fixture changes precede guest execution:action rows13,13,selected moves33,
move slot0,declared target1/0,stat stages6 and speeds100/200 or200/100. The preceding
controlled executionOrder1,0,index0 and actual HP→flinch→cancellation→native
history/action-end chain remain. Native completion leaves action rows13,40,
index1,HP300/100 and35 PP each,then command8. The parent oracle accepts pending13
only when explicitly requested;its default23 behavior and four complete preceding
EN/IT result records remain unchanged. The exact earlier verifier snapshot is
retained locally for its historical source identity.

ExecuteNextAction reads the native recording predicate,counts one unfinished
action at `CTX+3150` and calls real SortMonsBySpeed. CheckSortSpeed receives
battlers0/1 and stack flag1. Native ability lookup and all-live weather scans
for Cloud Nine13/Air Lock76 execute;no service supplies a speed or sort result.
With neutral stages,the two actual ARM divisions compute1000/10 and2000/10,
with quotient100/200 and remainder0;the reversed fixture swaps these numerators.
Native cache stores `02250132`/`0225013A` write `CTX+21F0`/`21F4`.

Sort resets turnOrder then swaps its first two bytes only when actor1 is faster.
Thus turnOrder becomes1,0 or0,1,while executionOrder stays1,0. Native controller8
uses executionOrder[index1]=0 and that row's13. It leaves CTX attacker1 until
FightInput actually runs. These unequal-speed paths consume no additional RNG;
the preceding native action-end two calls remain accounted for.

FightInput stores attacker0 at `0224A9CC`,takes native CanSelectAction's neutral
path and reads the selected Tackle from the actual BattleMon. The current/temp
move fields become33. Store `0224AAB4` sets command23,then the real target selector
runs with actor0/move33 and stack arguments0,0. The selected target1 is live,
Follow Me is clear,and native store `0224AACC` sets target1. An ABI-checked omitted
blank-message UI emission follows;the native handler returns through `0224AAD6`.
The verifier requires that return and the target store after the command write.
It stops before executing the next TryMove23 body or consuming its PP.

The previous actor's MoveFail mask40 remains in its own row `CTX+348`;the new
actor's row `CTX+344` stays0. HP,PP,execution order,index,RNG and the completed
actor row remain unchanged during the new dispatch. Every guest store has a
PC/field/width or exact two-battler loop contract. Native division and sort
entry/return SP,r4–r11,results,canaries,code/data/cache and unrelated memory are
checked. New dispatch stack peaks at320B (FightInput88B);the preceding
action-end chain peaks at328B. The fixture suite used about227 MB RSS.
There is no host assignment of the new attacker,move or target after
guest execution begins. The only new model omits blank-message emission;earlier
NARC/UI/Ready/cache/Party-transport models remain explicit.

The named late-pending counter initializes rows23,23 before the whole chain.
Native8 then reaches the same command23 directly,with attacker1/target0 and no
FightInput execution. It is rejected even if its label is changed to current.
The reverse-speed control proves that a speed-order change alone does not
change the selected execution row. Tests also reject changed dependencies,
wrong division/sort results,missing actor/target stores,missing native return,
wrong snapshots and out-of-bounds turn-order writes.

Provenance is documented and prior own-helper binary reconstruction is reused.
Activation is observed only for these initialized paths. Initial execution-order
selection,recording-paused activation,speed ties,other statuses/abilities/items,
other target modes,the next move's PP/attack,whole pivot,SAVE,cold restart,
hardware and timing remain open. No game ASM,ROM,save,ABI,ID or settings changes,
optimization or memory reclamation are included. Both installed compatibility
findings remain unfixed and any repair requires separate maintainer acceptance.
