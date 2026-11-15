# U-turn snapshot through native script commands

The exact r4 EN/IT native script interpreter and installed commands produce the
expected outgoing-item snapshot,then the installed consumer uses and clears it.
A wrong-shift fixture produces the same flinch result but the wrong snapshot;
the intermediate-state oracle rejects it. The repeat still exposes the known
fallback ABI failure. This case qualifies the bounded producer; it does not
repair the [two compatibility defects](uturn-source-rom-1.3.2.md).

See the [owner](../../features/type-consumers/README.md),
[HP continuation](hp-flinch-source-rom-1.3.2.md) and
[source-to-ROM method](../test-bench.md#linking-source-to-an-exact-rom).

## Cosa farebbe un professionista di alto livello che non sto chiedendo

Replace a semantic command interpreter with the actual opcode table,handlers,
script cursor,variable-pointer lookup and native item decoding. Preserve and
check intermediate scratch state,including a nonzero CalcTemp which the branch
must leave untouched. Track RNG separately from flinch. Qualify the artificial
stop and controlled slot replacement explicitly; neither proves a natural pivot.
Independent Sol6.1 review checked raw bounds/source correspondence and separately
executed Italian non-effective/effective paths with different battler slots.

## Il materiale più grezzo da cui partire

Supply your own exact revision0 retail,Plus1.1,V1.3 V4 and r4 images using the
[input preparation instructions](fairy-flags-source-rom-1.3.2.md#il-materiale-più-grezzo-da-cui-partire).
The [baseline identities](../../sgp131/baseline.py) and
[r4 contract](../../distribution/game-1.3.2-r4.json) specify whole size/SHA-256.
The tool authenticates all four inputs for each language; game-code text alone
is insufficient to identify the Italian candidate. No ROM,save,BIOS,extracted
retail data or private capture is supplied.

[`uturn_script.py`](../../sgp131/uturn_script.py) inserts104 bytes/26 words in
NARC `a/0/0/1`,file130,member175,at byte3C. Current800-byte member SHA-256 is
`eaa254c435e16397b233c8f3e796f1655003358e4252bcc57352f3ca89b58c9a`.
The preceding [source/ELF/composition case](uturn-source-rom-1.3.2.md) rebuilds
that insertion and two branch relocations and the68-byte helper in its128-byte
ARM9 tail. Source and recipe are unchanged; no compiler or full ROM rebuild is
needed for this follow-up. The original native C/object/compiler is unavailable.
Native source correspondence is reference commit
`cb614ad23449d5852b40321dc409c4143872b35c`,
`battle_command.c::{RunBattleScript,BtlCmd_UpdateVar,BtlCmd_UpdateVar2,
BtlCmd_Goto,BtlCmd_CheckItemHoldEffect,BtlCmd_GetItemEffectParam}`.

| Installed component | Identity and ABI |
| --- | --- |
| Opcode table | `0226C6C8`; entries50/57/59/166/168 point to native Thumb handlers. Script VM `0223CF68`,outer RunScript `0224C370`. r0/r1 are BattleSystem/Context pointers. |
| CheckItemHoldEffect166 | `0224428C..022442F8`,108 bytes, SHA-256 `0c4f06f4eb9797ff72d01c3005445fa219c41459cdb3ea27cd7bb088b062dc7a`; code only,32-byte own frame. Effective-item getter `02255830`. |
| GetItemEffectParam168 | `02244344..02244390`,76 bytes, SHA-256 `b007656dca26bd28b6100c88067ea07bc91d4d07c72d74f975a37baf243c281d`;74-byte code,2-byte alignment,24-byte frame. Calls HeldItem `022555EC`,then GetItemVar `02257E74` with attribute2; does not call GetHeldItemModifier. |
| Goto59 | `0223F894..0223F8B4`,32 bytes, SHA-256 `69f5a232eaef629793d981c254a7370de6188abe36e58a0c3afff95dd138c3ec`;30-byte code,2-byte alignment,8-byte frame. |
| Variable lookup | `02245528`,table `0224553E`: var9→case `02245602`→`CTX+0134` CalcTemp;var68→case `02245810`→`CTX+02EC+28*attacker`. |
| Side category1 | `0224768C`; signed table entry at `022476AA` selects `022476DC`,reads attacker from `CTX+0064`. It is distinct from category255/temp used by the HP case. |

The inherited VM/windows/readback methods are reused from the
[HP case](hp-flinch-source-rom-1.3.2.md),including raw y9/FAT/BLZ versus ndspy,
ARM9 autoload,RNG and signed arithmetic. Overlay12 current EN stored range is
`08314200..0833B940`,IT `08800000..08827740`,decoded base `022378C0`,size226176,
BSS0. Decompressed instruction addresses have no linear physical byte offset.
The three additional handler windows match all eight input-role images; retail
IT logical addresses are−60hex. The shared26 windows per role retain their
verified regional call/pointer comparison rules; actual current execution bytes
are never normalized.

## I metodi e gli strumenti da usare

[`attribuisci_uturn_producer.py`](../../features/type-consumers/tools/attribuisci_uturn_producer.py)
uses the qualified Python3.14.7,ndspy4.2.0,Capstone5.0.9,Unicorn2.1.4 environment.
Use private report directories and your own input paths:

```sh
python3 source/features/type-consumers/tools/attribuisci_uturn_producer.py --language EN \
  --rom "$R4_EN" --v4 "$V4_EN" --base "$BASE11_EN" --retail "$RETAIL_EN" \
  --json "$CASE/uturn-producer-EN.json"
python3 source/features/type-consumers/tools/attribuisci_uturn_producer.py --language IT \
  --rom "$R4_IT" --v4 "$V4_IT" --base "$BASE11_IT" --retail "$RETAIL_IT" \
  --json "$CASE/uturn-producer-IT.json"
SGP_R4_ROM_DIR="$R4_DIR" SGP_R4_ROM_NOME='r4-%s.nds' PYTHONPATH=source \
  python3 -m unittest sgp131.test_type_consumers.CurrentNativeUTurnProducer -v
PYTHONPATH=source python3 -m unittest \
  sgp131.test_type_consumers.UTurnProducerAttributionCLI -v
```

The CLI generates evidence and exits1 for the still-failed repeat fallback ABI
gate; producer attribution passes. An exception before generation means a
separate input/tool failure. Five fixture methods pass by checking the declared
behavior and rejecting counterexamples,not by accepting repaired game behavior.
Missing private fixtures explicitly skip; twelve path/alias CLI cases require no
ROM. Output cannot replace any input,including symbolic/hardlink aliases.

The fixture copies the authenticated800-byte member into private RAM,starts at
word15 and replaces only word41/byteA4 with synthetic End224. Words15..40 are
exactly the own104-byte insertion; all other member bytes remain identical.
The native VM returns normally via End/ScriptReturn at depth0. The original
member prefix and switch continuation are not executed. No mutation reaches the
input file. Guest stores are restricted by PC,field and width; code,pools,tables,
stack/caller canaries,unrelated Context/BS,cache and ABI are checked. The shared
VM verifier exposes overridable domains for reuse; its default HP behavior was
checked byte-for-byte at the complete result-record level for ten EN/IT chains.

Effective-item branch command/cursor path is
`50@15 →166@19 →50@26 →168@30 →50@33 →57@37 →224@41`.
The non-effective path is `50@15 →166@19 →59@24 →224@41`.
The native getter executes Klutz/Embargo checks and actual item0/221/327 decoding
from NARC item records,with the independently verified ID→member mapping and
36-byte cache stride. Cache construction from34-byte raw records plus two
synthetic padding bytes remains a model. Ability queries are an explicit model.
No producer RNG is consumed. Effective modifiers are read by the real cmd168
callgraph; the earlier semantic model's modifier-getter substitution is not
presented as identical native dispatch.

| Outgoing state | Snapshot | CalcTemp after | Consumer roll9 |
| --- | --- | --- | --- |
| Effective King's Rock221/Razor Fang327 | `00010A38` | `00000A00` | Flinch,word cleared |
| Empty/Klutz/Embargo | `00010000` | Preserved nonzero initial value | No flinch,word cleared |
| Named wrong-shift counter,9 instead of8 | `00011438` | `00001400` | Same flinch,but exact-packing oracle rejects |

The native var68 setter overwrites an initial−200 field in this producer
fixture. Seven current chains per language cover two real items,empty with
incoming Rock,Klutz,Embargo,attacker3 and roll10. One additional wrong-shift chain
per language checks intermediate exactness. Stack maximum is104 bytes in the
producer; the marked consumer and repeat use their previously qualified native
paths. Non-effective cases preserve a nonzero CalcTemp sentinel; this broadens
the earlier model's initial-zero scope without relabelling historical coverage.

A controlled item/ability replacement separates producer from consumer. The
marked consumer uses the outgoing word and clears it once. The repeat has no
new producer and records the existing fallback ABI failure. With incoming Rock
it consumes RNG despite no flinch; no-flinch is not RNG neutrality. The original
pivot switch,callbacks,whole script,earlier AfterDamage0..5,asynchronous PartyMon
transport,natural battle,SAVE,cold restart,hardware and timing remain unqualified.

Native source correspondence and installed byte identities are documented;
own helper binary reconstruction is reused; bounded native producer activation
is observed. There is no original native C rebuild,universal equivalence or
claim of natural gameplay. Both existing game defects remain open,with no
ASM,ROM,save,ID or ABI change. A repair must separately verify fallback arguments,
noncolliding storage,native-field lifetime and full pivot/ordinary paths before
save/device acceptance. This case adds verification capability,not optimization.

In these native parent fixtures, `flinch` denotes the true TryItemFlinch result
and script14 request. Applying the target status bit or losing a turn requires
execution beyond that request.
