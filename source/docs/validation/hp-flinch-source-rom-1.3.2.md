# Native HP writer to item-flinch continuation

The exact r4 EN/IT code produces native damage−200, updates HP300→100 through
the installed HP script, and preserves the damage word until the item-flinch
consumer. Continuing `AfterDamage` at explicit state6 then causes item flinch
with no held item. The previous native getter calls preserve the word and cause
no flinch. This extends the [U-turn finding](uturn-source-rom-1.3.2.md); it does
not establish a naturally played battle or repair the game.

See the [owner](../../features/type-consumers/README.md) and
[source-to-ROM method](../test-bench.md#linking-source-to-an-exact-rom).

## Cosa farebbe un professionista di alto livello che non sto chiedendo

Start the shared word at zero and require a guest damage writer to produce it.
Follow the real intervening script and check each checkpoint, caller, ABI,
write domain and RNG transition. An intermediate clear, eligibility gate or
other script could disprove the isolated consumer hypothesis. Do not substitute
an opaque service which simply promises to preserve the interesting field.
Independent Sol6.1 review checked raw bounds, branches and fields and separately
executed current/previous-hook/ineligible-move chains against the Italian image.

## Il materiale più grezzo da cui partire

Use your own exact revision0 retail, Plus1.1, V1.3 V4 and r4 images, prepared as
in the [input identity instructions](fairy-flags-source-rom-1.3.2.md#il-materiale-più-grezzo-da-cui-partire).
The [baseline identities](../../sgp131/baseline.py) and
[r4 contract](../../distribution/game-1.3.2-r4.json) specify size and SHA-256;
the tool authenticates all four whole images for the selected language. It
supplies no ROM, save, BIOS, retail dump, extracted data or private capture.

The inherited native source correspondence is reference commit
`cb614ad23449d5852b40321dc409c4143872b35c`:
`battle_controller_player.c::{BattleControllerPlayer_HpCalc,
BattleControllerPlayer_RunScript,BattleControllerPlayer_AfterDamage}`,
`battle_command.c::{RunBattleScript,BtlCmd_UpdateHealthbarValue}` and the
associated script commands. The original native compiler/object is unavailable;
this case proves installed native bytes and bounded execution, not a native C
rebuild. The own [`uturn.S`](../../features/type-consumers/uturn.S) build,
68-byte helper, external fixups and composition/readback are qualified in the
[preceding case](uturn-source-rom-1.3.2.md). Those unchanged artifacts are reused;
no compilation, full ROM build or runtime capture is required here.

| Component | Current logical location and evidence |
| --- | --- |
| HpCalc | `0224C690..0224CAA4`,1044 bytes, SHA-256 `851df7b044230b4d44656d2e35e3397c3427cdce5bac3596cc8a43fe73f6677d`. Code excludes alignment at C9BA,44-byte embedded pool C9BC..C9E8 and12-byte trailing pool CA98..CAA4. |
| AfterDamage | Code `0224CAA4..0224CC78`,468 bytes, plus16-byte pool, whole484-byte closure SHA-256 `894ff2f35859c45cf47fe0b3aa5219d2e49476c0520ef56c84b8e0e91a9c3ce0`. Two14-byte jump tables are data. |
| Controller dispatch | Table `0226CA90`: slots28/22/29 point to HpCalc/RunScript/AfterDamage Thumb entries. RunScript `0224C370`; interpreter `0223CF68`. |
| HP subscript | NARC `a/0/0/1`,file130,member2,152 bytes/38 words, SHA-256 `bf7ad08c8f82d1b33126bf3b11cddcf34f4e7fbd49beb2fe45d90b9f65bafe70`. |
| HP command | Script opcode26→`0223E160`,updates HP/totalDamage/hitDamage, calls native copy wrapper `02250C40`, emitter `02263B4C`. Empty-item AI leaf `022585A8` writes only `CTX+0394+2*b`. |
| Flinch callers | Message types0/1,state6: BL at `0224CB8A`/`0224CC64`→`0224E078`; two installed getter hooks enter own helper at `023D5A20`/`023D5A40`. |

Overlay12 is BLZ compressed: base `022378C0`,decoded226176 bytes,BSS0.
Its stored r4 EN range is `08314200..0833B940`,IT `08800000..08827740`.
The report records header/y9/FAT,stored/decoded hashes and independent decoders.
There is no linear physical offset for each decompressed instruction. The helper
is in ARM9 autoload: specific raw mapping,physical offset `001252E0`,is qualified
in the preceding case. Retail IT overlay base is−60hex; comparison copies adjust
13 verified ARM9 call fields and two proven pointer literals. Actual targets,
entry signatures and script dispatch entries are checked first. Execution always
uses unmodified current r4 bytes.

## I metodi e gli strumenti da usare

[`attribuisci_hp_flinch.py`](../../features/type-consumers/tools/attribuisci_hp_flinch.py)
uses Python3.14.7,ndspy4.2.0,Capstone5.0.9 and Unicorn2.1.4 as recorded locally.
Use your dependency environment and private paths:

```sh
python3 source/features/type-consumers/tools/attribuisci_hp_flinch.py --language EN \
  --rom "$R4_EN" --v4 "$V4_EN" --base "$BASE11_EN" --retail "$RETAIL_EN" \
  --json "$CASE/hp-flinch-EN.json"
python3 source/features/type-consumers/tools/attribuisci_hp_flinch.py --language IT \
  --rom "$R4_IT" --v4 "$V4_IT" --base "$BASE11_IT" --retail "$RETAIL_IT" \
  --json "$CASE/hp-flinch-IT.json"
SGP_R4_ROM_DIR="$R4_DIR" SGP_R4_ROM_NOME='r4-%s.nds' PYTHONPATH=source \
  python3 -m unittest sgp131.test_type_consumers.CurrentHPFlinchPath -v
PYTHONPATH=source python3 -m unittest \
  sgp131.test_type_consumers.HPFlinchAttributionCLI -v
```

Both CLI runs write evidence and deliberately exit1 because compatibility fails.
An exception before evidence generation indicates an input/tool failure. The five
fixture test methods pass by detecting the defect and rejecting invalid evidence;
they do not certify a repaired game. Missing private fixtures explicitly skip.
The CLI protects all four input paths, including symbolic/hardlink aliases,
before reading or writing. Keep JSON outputs private and use fresh report paths.
Runs are bounded to20000 instructions per entry and eight script resumptions;
recorded runs use≤160 bytes stack,about228 MB maximum RSS in the fixture suite,
and no compiled or extracted ROM tree.

The public verifier pins26 complete windows per input role,104 per language,
independently reads the exact script and actual item/move resources, and executes
full HpCalc→RunScript/interpreter→HP command/wrapper/emitter→AfterDamage entries.
ABI is `(BattleSystem*,BattleContext*)` in r0/r1; outer SP,r4–r11,Thumb state,
code/data,stack/caller canaries,item-cache bounds and every guest state store
are checked. State6 and message type are explicit continuation inputs. The
actual script traverses13 command invocations over three native resumptions:
comparison,sound,flicker,wait,comparison,clear-flag,HP-bar,wait,HP-value,
faint check,comparison,variable copy,end. Waiting-battlers is zero; alternate
subscript264 is skipped. Target survives,items/abilities/substitute/endure are
absent,attacker0 and target1 are opposing sides in a non-link fixture.

| Checkpoint | Shared native word | Target HP | Command |
| --- | --- | --- | --- |
| Input | 0 | 300 | HpCalc28 |
| Guest HpCalc return | `FFFFFF38` (−200) | 300 | RunScript22,next29 |
| Native HP script return | `FFFFFF38` | 100 | AfterDamage29 |
| Current state6 return | 0 | 100 | Flinch script22,next29 |
| Previous-hook control | `FFFFFF38` | 100 | AfterMoveEffects31 |

The shared field is `SelfTurnData.shellBellDamage`,`CTX+02EC+28*attacker`.
The damaging move/category and item0 bytes come from real NARCs; the word is
written by native store `0224CA44`,not injected at the consumer. Current code
misreads low byte56 as hold effect and next byte255 as probability. Actual LCG
and signed ARM division produce roll99,then the flinch script is requested.
The ineligible Bite44 control causes no flinch but still advances RNG once:
the eligibility guard comes after the random draw. Damage−199 causes no flinch
but clears the native word; damage0 skips the HP script. Message type1 repeats
the same collision. Five current chains and one previous-hook chain run per
language; the control changes only the two old getter calls in private RAM.
Checkpoint/cursor/seed mutations are rejected even when final flinch is unchanged.

Ability0,NARC loading,UI emission,transport-ready success and Party packet
transport are explicit ABI-checked models. Native HP writes,script interpreter,
commands,field-side selection,item getters,copy wrapper/emitter,empty-item AI
clear,RNG and ARM arithmetic execute. The asynchronous packet consumer and
PartyMon encryption/write are outside this case. Crucially, AfterDamage
states0..5,their scripts/callbacks and the natural arrival at state6 are still
unqualified; this is a controlled continuation,not observation of a complete
battle. No claim covers Shell Bell healing loss,all damage values,doubles,
link play,SAVE,cold restart,hardware or timing.

The inherited source provenance and byte correspondence are documented; own
helper build correspondence is reused from its case. Bounded native execution
is observed here,while universal semantic equivalence and natural activation
remain open. No game ASM,ROM,save,ABI or ID changes. A later game repair must
preserve the native field and use a noncolliding snapshot namespace as well as
correct fallback arguments. Cost/risk require targeted source/byte rebuild,
ordinary and pivot coverage,full intermediate-state tests and save/device
validation before acceptance; neither repair nor optimization is included here.

The shared VM domains are reused by the
[native U-turn producer](uturn-producer-source-rom-1.3.2.md). Defaults retain the
same complete result records for the ten preceding current EN/IT HP chains.

The later [native AfterDamage continuation](afterdamage-source-rom-1.3.2.md)
executes states0..6 and the required neutral scripts without injecting6. That
extends this fixture's coverage; it still ends at a script14 request.

In these native parent fixtures, `flinch` denotes the true TryItemFlinch result
and script14 request. Applying the target status bit or losing a turn requires
execution beyond that request.
