# Native flinch effect after the script request

The exact r4 EN/IT initialized path now executes script14 and sets the target's
volatile flinch bit through the native setter. Existing status bits are preserved.
Inner Focus,Shield Dust,already-acted and substitute-hit controls retain the same
initial request but block that write. This extends the
[AfterDamage request case](afterdamage-source-rom-1.3.2.md); losing an action is a
separate,unqualified consumer of the bit.

See the [owner](../../features/type-consumers/README.md),
[source-to-ROM method](../test-bench.md#linking-source-to-an-exact-rom) and
[original compiled helper attribution](uturn-source-rom-1.3.2.md).

## Cosa farebbe un professionista di alto livello che non sto chiedendo

Distinguish a parent BOOL,script request,completed script,target write and actual
turn behavior. Execute the real ability gates and field accessor/setter rather
than a service which writes a flag. Check another status bit and another battler.
A wrong-mask RAM counter must fail even when the original request and script
completion remain unchanged. Independent Sol6.1 review checked raw identities,
ABI,field mapping,Italian success/gated paths and the wrong-mask counter. A
matching-ability bookkeeping store was first refused,then admitted at its exact
native PC/field after raw review; no broad context write allowance was added.

## Il materiale più grezzo da cui partire

Use your own exact revision0 retail,Plus1.1,V1.3 V4 and r4 images following the
[input preparation instructions](fairy-flags-source-rom-1.3.2.md#il-materiale-più-grezzo-da-cui-partire).
Sizes and whole SHA-256 are specified in [`baseline.py`](../../sgp131/baseline.py)
and the [r4 contract](../../distribution/game-1.3.2-r4.json). Each CLI authenticates
all four images for its selected language. No ROM,save,BIOS,retail dump,asset or
private capture is included. Header text alone does not establish the Italian
candidate's identity.

Raw NARC `a/0/0/1`,file130,297 members,member14 is224 bytes, SHA-256
`8cd5d72da2f91298d0c14a1e5fb816bfeafbf71a2b382c8c23430868d1ec544a`.
It is identical across all eight input-role images. The inherited native source
correspondence uses the [HGSS reference tree](https://github.com/ctrl-cheeb-del/pokeheartgold/tree/cb614ad23449d5852b40321dc409c4143872b35c)
at commit `cb614ad23449d5852b40321dc409c4143872b35c`:
script0014,`battle_command.c::{BtlCmd_IfMovedThisTurn,BtlCmd_CheckSubstitute,
BtlCmd_CheckIgnorableAbility,BtlCmd_UpdateMonData}` and
`battle_util.c::{GetBattlerAbility,CheckBattlerAbilityIfNotIgnored,
BattleContext_IsActionDone}`. The original native C/compiler/object is not
reconstructed. The own68-byte helper/source/ELF/composition is reused from the
[preceding case](uturn-source-rom-1.3.2.md),with unchanged source and bytes; no
compiler,full-ROM build or new runtime capture is needed here.

| Additional native dependency | Current logical location and role |
| --- | --- |
| IfMoved165 | `0224424C..0224428C`,64 bytes of code. Native predicate `0225561C..02255634`,24 bytes,checks `CTX+21A8+16*b ==40`. |
| CheckSubstitute210 | `0224514C..022451A8`,92 bytes,88 code+4 pool. Checks BattleMon status2 bit24 and SelfTurnData statusFlags mask8 (bit3). |
| CheckIgnorableAbility161 | `02243F18..02244040`,296 bytes,286 code+2 alignment+8 pool. Matching side7 branch stores ability battler at `CTX+0080`,PC `02244002`. |
| Native ability lookup | `022527CC..02252834`,104 bytes,100 code+4 pool. CheckIgnorable helper `02252834..02252890`,92 bytes,86 code+2 alignment+4 pool. Actual field lookup and comparison execute. |
| UpdateMonData52 | `0223F38C..0223F4B0`,292 bytes,290 code including42-byte table+2 alignment. Reads attr53,ORs8,passes a stack word pointer to native SetBattlerVar,then calls the copy wrapper/emitter. |
| Field access | Getter prefix `0224EDE0..0224EE02`,case53 `0224EFD2..0224EFD6`;setter prefix `0224F168..0224F18C`,case53 `0224F3DE..0224F3E4`. Actual store PC `0224F3E0` writes BattleMon+70. |

Complete SHA-256 and code/data subsets are fixed in the
[verifier](../../features/type-consumers/tools/attribuisci_flinch_effect.py).
The status2 field is `CTX+2DB0+C0*b`;flinch is mask8,bit3. Parent-produced side7
selects `CTX+0094`,and script var5 maps to `CTX+0088`,type2. The test never assigns
these two values immediately before the effect: native TryItemFlinch supplies them.

Native code is in BLZ overlay12,base `022378C0`,decoded226176 bytes,BSS0.
Current EN stored span is `08314200..0833B940`,IT `08800000..08827740`.
Reports record header/y9/FAT and independent stored/decoded readback; a decoded
instruction has no linear physical file offset. The own helper uses ARM9
autoload `023D5A20`,physical `001252E0`,qualified separately. Retail IT logical
addresses are−60hex. Only proven ARM9 call fields are normalized for comparison,
with target/signature checks first; the ten additional windows need four such
fields in retail IT. Shared VM comparison rules retain their two pointer literals.
Actual execution always uses unmodified current bytes.

## I metodi e gli strumenti da usare

[`attribuisci_flinch_effect.py`](../../features/type-consumers/tools/attribuisci_flinch_effect.py)
uses qualified Python3.14.7,ndspy4.2.0,Capstone5.0.9 and Unicorn2.1.4. With private
inputs and fresh private report paths:

```sh
python3 source/features/type-consumers/tools/attribuisci_flinch_effect.py --language EN \
  --rom "$R4_EN" --v4 "$V4_EN" --base "$BASE11_EN" --retail "$RETAIL_EN" \
  --json "$CASE/flinch-effect-EN.json"
python3 source/features/type-consumers/tools/attribuisci_flinch_effect.py --language IT \
  --rom "$R4_IT" --v4 "$V4_IT" --base "$BASE11_IT" --retail "$RETAIL_IT" \
  --json "$CASE/flinch-effect-IT.json"
SGP_R4_ROM_DIR="$R4_DIR" SGP_R4_ROM_NOME='r4-%s.nds' PYTHONPATH=source \
  python3 -m unittest sgp131.test_type_consumers.CurrentNativeFlinchEffect -v
PYTHONPATH=source python3 -m unittest \
  sgp131.test_type_consumers.FlinchEffectAttributionCLI -v
```

Both CLI runs generate evidence and deliberately exit1: native attribution and
gates pass,but no-item status compatibility fails. An exception before generation
means a distinct input/tool failure. Six fixture methods pass by detecting the
recorded behavior and rejecting invalid evidence,not by certifying repaired game
behavior. Missing private fixtures explicitly skip. Twelve no-ROM CLI cases check
input paths and symbolic/hardlink aliases before analysis; JSON cannot replace
any of the four inputs.

Each language records45 windows per role,180 in total,seven current chains,one
previous-hook control and one named RAM wrong-mask counter. Native ability values
are declared RAM inputs: attacker Overgrow65,target Torrent67,Inner Focus39 or
Shield Dust19. The lookups and gates execute native code;there is no ability
return-value model in this case. Suppression,Gravity,Ingrain and Mold Breaker
branches are not exercised. Native ability entry/return SP,r4–r11,lookup values,
getter null output and setter aligned stack pointer are checked. All guest state
stores have PC/field/width contracts;code,pools,tables,cache,unrelated context,
stack/caller canaries and returns remain checked. Maximum guest stack is176 bytes
in the effect's native copy/emitter path;the fixture suite used about232 MB RSS.
Entry/resume limits reuse the preceding bounded VM.

The input-preparation hook runs before any guest instruction and leaves the
preceding verifier's default unchanged: twelve complete EN/IT continuation result
records compare equal. Script14 is copied from the authenticated member when the
real parent requests it,then RunScript executes its actual dispatch. No late host
assignment applies the flinch bit. Effect script paths are:

| Condition after actual request | Opcode/cursor path | Target status2 |
| --- | --- | --- |
| Torrent,not already acted |165@0,210@3,161@6,32@11,161@16,52@21,End@26|`400→408`|
| Inner Focus39 |165@0,210@3,161@6,32@27,32@32,End@45|`400→400`|
| Shield Dust19 |165@0,210@3,161@6,32@11,161@16,End@26|`400→400`|
| Already acted |165@0,End@26|`400→400`|
| Prior substitute-hit flag |165@0,210@3,32@46,End@55|`400→400`|

The substitute control is an explicit initial SelfTurnData flag fixture,not
observation that a naturally played Tackle produced it. The already-acted input
uses the native action predicate's command40. Both controls preserve the original
script14 request while blocking the target write. Starting with status0 produces
8;the attacker status remains0. Bite44 and previous-hook controls request no
script14 and execute no effect. The effect script consumes no additional RNG,
even though the earlier erroneous request path already advanced it.

The native setter's recorded store is exactly word `CTX+2E70 =400|8` for target1.
The same native wrapper/emitter is executed afterward;asynchronous transport and
encrypted PartyMon consumption remain modeled/unqualified. Status2 is volatile
BattleMon state;no save-layout or persistence change is inferred.

The wrong-mask counter changes only script word25 in private RAM,8→16,after
normal raw-member admission. It completes the same requested script but writes
410 instead of408;the exact status/store/script oracle rejects it. Normal
constructors refuse a changed raw member. This illustrates why request and
completed-script checks alone are insufficient.

Observed execution now extends HpCalc→native AfterDamage0..6→script14→target
flinch bit,for the declared initialized inputs. Natural move calculation,turn
selection and the native consumer which loses an action are not executed.
Other abilities/conditions,whole pivot,PartyMon encrypted mutation,SAVE,cold
restart,hardware and timing remain open. NARC loading,UI emission,transport-ready
success,cache preparation and asynchronous packet transport remain explicit
models. Both installed compatibility defects remain unfixed. No game ASM,ROM,
save,ID or ABI change,optimization or memory reclamation is included. A later
repair needs source/byte reconstruction and ordinary/pivot/lifetime/save/device
verification before acceptance;it remains a separate maintainer decision.
