# Native flinch-bit consumption and action cancellation

The exact r4 EN/IT native caller consumes the bit actually produced by the
[preceding effect case](flinch-effect-source-rom-1.3.2.md),clears it,marks flinch
failure and runs script15 until controller command39. The initialized no-item
negative-damage path therefore reaches native action cancellation after an
explicit next-action selection boundary. Command39 UpdateMoveHistory and
command40 ActionEnd are not executed here;action completion and natural turn
selection remain separate links.

See the [owner](../../features/type-consumers/README.md),
[source-to-ROM method](../test-bench.md#linking-source-to-an-exact-rom) and
[compiled helper and two open compatibility defects](uturn-source-rom-1.3.2.md).
No gameplay repair is included.

## Cosa farebbe un professionista di alto livello che non sto chiedendo

Separate an applied bit,its native consumer,a cancellation route and completed
action bookkeeping. Preserve the positive bit across the declared host boundary
instead of synthesizing it. Start the status loop at state0 through its real
caller,execute required scripts and check native BOOL/ABI,clear/failure stores,
RNG and another actor. A no-bit direct status return does not prove a successful
move through PP,disobedience and target checks. Independent Sol6.1 review checked
source/raw addresses,Italian positive/other-actor execution and coverage limits.
Strict store checks caught an erroneous field annotation before acceptance:
MoveFail is `CTX+0344+4*b`,not `0334+4*b`.

## Il materiale più grezzo da cui partire

Prepare your own exact revision0 retail,Plus1.1,V4 and r4 images using the
[input instructions](fairy-flags-source-rom-1.3.2.md#il-materiale-più-grezzo-da-cui-partire).
Whole hashes and sizes are in [`baseline.py`](../../sgp131/baseline.py) and the
[r4 contract](../../distribution/game-1.3.2-r4.json). The CLI authenticates all
four roles for its selected language. No ROM,dump,asset,save,BIOS or private
capture is supplied. Language is established by the declared whole-image hash,
not header text alone.

The inherited source correspondence uses the
[pinned HGSS reference](https://github.com/ctrl-cheeb-del/pokeheartgold/tree/cb614ad23449d5852b40321dc409c4143872b35c):
`battle_controller_player.c::{TryMove,CheckAttackerStatus,CheckQuickClaw}`,
`battle_command.c` handlers and `battle_util.c` helpers below,plus scripts0015
and0278. This documents native source correspondence;the original native
compiler/object is unavailable. The own Plus helper/source/ELF reconstruction
from the [U-turn case](uturn-source-rom-1.3.2.md) remains unchanged. No compiler,
full-ROM build or new runtime capture is required for this extension.

NARC `a/0/0/1`,file130,297 members has the following unchanged members across
all eight input-role images:

| Member | Bytes | SHA-256 |
| --- | --- | --- |
|15 Flinched|116|`cf4783da2e5bfc50a35612dddc858f08a8794f1438101066cbea823bf49efcc3`|
|278 QuickClaw|260|`417cdf4b035ca0285e17692524f68d5953835af6c985da4045b0eb3a6be86d52`|

| Native dependency | Current logical span;code/data distinction |
| --- | --- |
|TryMove|`0224C38C..0224C4D8`,332 bytes;314-byte code/table region (300 executable bytes+14 table bytes),2 alignment,16 pool. Controller slot23;BL at `0224C3C8` targets CheckAttackerStatus.|
|CheckAttackerStatus|`0224B528..0224BC2C`,1796 bytes;34-byte switch table and two40-byte literal islands excluded from execution,plus alignment. Full window pinned.|
|CheckQuickClaw|`0224BCA4..0224BCC4`,32 bytes;26 code,2 alignment,4 pool. Always requests script278 before status checks.|
|Neutral-status leaves|Truant `02252C40`52B,Imprison `02252C74`116B,Gravity `02252DC4`52B,HealBlock `02252DF8`56B,MaxBattlers `0223A7F0`4B.|
|Flinched script handlers|Print18 `0223DEF0`52B,WaitButton30 `0223E2F0`156B,CheckAbility55 `0223F524`192B,Unlock65 `0223FA98`44B;native unlock leaf `02250CA0`92B.|
|Message/input leaves|Native message parser `022478F4`204B,with122-byte tag table;TouchNew getter `02025358`12B=6 code+2 alignment+4 pool.|
|QuickClaw flags|GetBattlerVar85/86 table targets `0224F0F0`/`0224F0FA`,10B each;reads activation bits28/29 from BattleMon+8C.|

All17 additional window hashes and executable subsets are fixed in the
[verifier](../../features/type-consumers/tools/attribuisci_flinch_consumer.py).
Together with the earlier45 windows,this gives62 per role,248 per language.
Overlay12 is BLZ,base `022378C0`,decoded226176 bytes,BSS0. Current stored spans
are EN `08314200..0833B940`,IT `08800000..08827740`. Independent raw y9/FAT/BLZ
and ndspy readback are reused;decoded instructions have no linear physical ROM
offset. The compiled helper is at ARM9 autoload `023D5A20`,physical `001252E0`.

Retail IT overlay addresses differ by−60hex. Comparison validates three ARM9
call targets/signatures,using the six-byte TouchNew body rather than bytes from
adjacent functions. Two exact overlay table pointers are checked against their
12/28-byte tables and load instructions. Two exact input-reader literal fields
also differ by−60hex: `02025360` and `0223E37C`,current values `021D114C` and
`021D110C`. Their coupled values and complete normalized windows are checked.
This qualifies those fields for historical comparison;it establishes no general
RAM/BSS relocation. Execution always uses intact current bytes.

## I metodi e gli strumenti da usare

The tool reuses Python3.14.7,ndspy4.2.0,Capstone5.0.9 and Unicorn2.1.4. Use fresh
private output paths and your own inputs:

```sh
python3 source/features/type-consumers/tools/attribuisci_flinch_consumer.py --language EN \
  --rom "$R4_EN" --v4 "$V4_EN" --base "$BASE11_EN" --retail "$RETAIL_EN" \
  --json "$CASE/flinch-consumer-EN.json"
python3 source/features/type-consumers/tools/attribuisci_flinch_consumer.py --language IT \
  --rom "$R4_IT" --v4 "$V4_IT" --base "$BASE11_IT" --retail "$RETAIL_IT" \
  --json "$CASE/flinch-consumer-IT.json"
SGP_R4_ROM_DIR="$R4_DIR" SGP_R4_ROM_NOME='r4-%s.nds' PYTHONPATH=source \
  python3 -m unittest sgp131.test_type_consumers.CurrentNativeFlinchConsumer -v
PYTHONPATH=source python3 -m unittest \
  sgp131.test_type_consumers.FlinchConsumerAttributionCLI -v
```

Both CLI reports deliberately exit1 after generation:attribution passes but
no-item cancellation compatibility fails. An exception before generation means
an input/tool failure. Five fixture methods verify the recorded behavior and
reject drift;they do not certify repaired gameplay. Missing local fixtures skip
explicitly. Twelve CLI cases check output/input path,symbolic-link and hardlink
aliases before analysis. Keep inputs and reports private.

The positive starts with the actual HP→AfterDamage→script14 chain,status0→8 for
battler1. The declared host boundary selects actor1/target0,Tackle33,controller23,
TryMove state0 and status state0,preserving both status words and HP. Natural
execution-order selection is not executed. Neutral fixtures have no other
statuses,Gravity,HealBlock,Imprison or QuickClaw/Custap activation flags. Abilities
remain65/67 with native lookup. Empty held item alone does not prove activation
flags are clear;the initialized flags are a separate declared condition.

Native TryMove0 requests278. Actual flag getters and script comparisons take
`33@0,33@6,End@64`. TryMove1 then calls CheckAttackerStatus from state0. Its
states0..4 perform cleanup and neutral sleep/freeze/Truant/recharge checks;state5
reads and clears flinch at `0224B7A0`,stores MoveFail mask40 at `0224B7AC`,loads15
and sets current22/next39. The native return BOOL1 is checked at caller
`0224C3CC`,including SP and r4–r11. BattleStatus `CTX+213C` gains mask2 and
MoveStatus `CTX+216C` gains `80000000` (NO_MORE_WORK). The caller's later
PP/disobedience/attack stages are not entered.

Script15 executes `18@0,14@4,30@5` (31 polls),`65@7,55@9,End@28`. The actual
message parser produces ID181/tag2/actor1;formatting and UI emission are explicit
omitted models. The native wait reads zero keys/touch at current `021D1154` and
`021D1170`,rewinds the cursor,counts1..30 then resets0. These are VM polls,not
measured rendering frames or elapsed time. Native unlock executes its precise
status/effect-field stores. Ability67 is not Steadfast80,so the final native gate
takes End28. Actual RunScript returns controller39 after36 entry/resume calls.
No input-return or cancellation-BOOL service substitutes for these native paths.

The previous-hook RAM control produces no bit;full CheckAttackerStatus directly
returns false after states0..16/reset0,without requesting15. Running that same
full status entry for actor0 also returns false and leaves actor1's actual bit8
intact. These controls stop before the rest of TryMove and prove no successful
normal move. Exact raw clear/failure stores,wait counter,cursor sequence,summary
fields,unchanged RNG,code/data/cache freezes,PC/field/width guards,stack canaries
and returns are checked. Tests reject changed dependencies/scripts and reports
which retain command39 while corrupting the clear,failure flag or wait sequence.

Provenance is documented;the own helper's binary reconstruction is inherited
from its separate case. The native C build is not reconstructed. Activation and
cancellation are observed only for these initialized,controlled-boundary paths.
Command39/40,action-done writes,natural turn selection,Steadfast/other statuses,
whole pivot,asynchronous PartyMon transport,SAVE,cold restart,hardware and timing
remain open. NARC loading,Ready/cache preparation and prior transport models
remain explicit. Both installed game defects remain unfixed;no game ASM,ROM,
save,ABI,ID or settings changes are included.
