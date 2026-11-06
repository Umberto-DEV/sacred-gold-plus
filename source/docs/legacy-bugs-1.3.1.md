# Legacy hack bugs: evidence and repairs in 1.3.1

This register reconciles historical Sacred Gold/Storm Silver reports with Plus
author claims and authenticated input bytes. The first read-only survey was on
**31 October 2026**; later sections retain the dated follow-up evidence. For
original HGSS, see the [retail catalog](known-bugs-hgss.md). Current release
identities and integrated acceptance belong to the
[validation report](ui-1.3.1-validation.md) and
[implemented bug summary](../../BUG-FIXES-1.3.1.md).

The initial survey did not modify a save or establish new runtime compatibility.
Follow-up source work implemented SG-08, SG-09, SG-11, SG-15 and SG-15b, among
other cases below. [The code audit](bug-audit-1.3.1.md) identifies that later work,
its before/after bytecode models and independent readbacks separately from the
unchanged earlier inputs. An older observation is never relabeled as evidence
for newer ROM bytes.

## Sources and distinct version lines

The original source is the bugs section of
[Drayano's thread](https://gbatemp.net/threads/pokemon-sacred-gold-storm-silver.327567/),
identifying **1.05, 1 June 2012**. GengarFan95's comment on the
[22 July 2025 Plus post](https://www.reddit.com/r/PokemonROMhacks/comments/1m69jrj/sacred_gold_plus_fairy_type_full_implementation/)
repeats the list. That post claims seven fixes since **Plus 1.02**, one concerning
documentation, and describes the MooMoo Milk wording as intentional slang.
Author claims still require verification against the actual installed version.

Keep these lines distinct: regional/revision-specific retail HGSS; Drayano's
Sacred Gold/Storm Silver **1.05**; mikelan98/MeroMero's Fairy **1.1/1.1.0**;
DeadSkullzJr's **1.1.1/1.1.2** maintenance; NefariousnessNo3436's Plus **1.03**;
and this project's **1.2.5**, **1.3 V4**, historical **1.3.1** candidates and
current **1.3.1** release. A larger number in another line does not prove it
contains these fixes. The survey downloaded no ROM, BIOS, save or alternative
build.

## Authenticated survey inputs

Hashes were checked before and after inspection without copying ROMs. Retail
and 1.2.5 inputs are also identified in the [retail catalog](known-bugs-hgss.md).

| Input | SHA-256 |
| --- | --- |
| Plus 1.2.5 EN | `a821961fc1a90e4adaa118c4a09fce5445d25d567130d0c9edb20dfb0520050e` |
| Plus 1.2.5 IT | `bdf50a4f327f8ea0d8a2ef312e1491d78460d34e978d9b15d160eaf140b313d4` |
| Plus 1.3 V4 EN | `179edfb1ca331503f438e98f3afccfb0ab85759bf9ab88fb86c735f5fcefbf90` |
| Plus 1.3 V4 IT | `2a2f0b437fca524c18b71b20feb01a1f51351e61c7c897ce73d9b3be1ee3a156` |
| Historical 1.3.1 pending EN | `15f379ebc7e99ce0ec0daa39a5627ccc3dbf4360601d82f59d7b7201078b76a6` |
| Historical 1.3.1 pending IT | `bc566c14050fae3ac7f204e65a63371954b3d7d7fcfb49689bc726cc903b57f1` |

Those pending images contain three inert modules and **are not the accepted
final candidates**. Successors need their own identity/readback. Data inspection
does not certify a complete composition, gameplay or saves.

Script reference: `pret/pokeheartgold`
`0985e8718df4f25e64d6507d89c0c97c0d288981`; command metadata SHA-256
`fbfbf438104cfc3735c3144730ed711bb882fca370a8de680db5c1d39ffaca5a`.
The [public decoder](../features/borsa/tools/scr_disasm.py) roundtrips the relevant
members; this does not validate every script in the cartridge.

## The twenty original reports

**D** means inspected data/bindings; **P** means a symbolic path using reference
semantics; **historical R** means a previously documented execution, not a new
run here. An open report is not necessarily reproduced on this project's ROM.
The limitations below belong to each cited campaign, not an assertion that no
later integrated test exists.

| ID | Historical report | Evidence, resolution and limits |
| --- | --- | --- |
| SG-01 | Safari black/white screens. | **Two distinct source-bound defects are repaired as SG-01a/SG-01b; generic menu/audio blackout remains unisolated.** A [Storm Silver V1.1 Delta/3 DS report](https://www.reddit.com/r/Delta_Emulator/comments/1d4yw1m/storm_silver_freezing_in_safari_zone_takeover/) locates some cases near the bridge and also reports black Bag/Party/Pokégear with stuck audio. SG-01a concerns window lifetime; SG-01b only losing to the final executive. The read-only save census did not supply a useful fixture for the remaining symptoms. Raw save versus savestate, turbo OFF/ON, menus, audio, SAVE/cold and hardware remain distinct coverage. |
| SG-01a | Route 47 partner-healing dialogue window lifetime. | **Source-bound component defect demonstrated/repaired; runtime acceptance separate.** Map 151→script 260/event 146: coordinate records 7/9/14/17 reach Mira/Buck/Cheryl/Marley. Mira closes before leaving the field; the others ran `LeaveOverworld`→`RestoreOverworld` before `CloseMsg`. Moving each close immediately after `NPCMsg` preserves length, offsets and all complementary bytes. [safari_lifetime.py](../sgp131/safari_lifetime.py) authenticates dispatcher, native handlers/tasks and pinned pret source. Sole producer [safari_archives.py](../sgp131/safari_archives.py) changes only member 260 and verifies SG-01a/SG-02 then SG-01b in sequence. No ROM is retained. This does not attribute all black-menu/audio/SG-01 reports to the defect; raw-save gameplay, SAVE/cold and hardware remain separate. Safari gate `6130` already belongs to V-CHATOT/HF02. |
| SG-01b | Losing to the final Route 47 executive. | **Source-bound defect demonstrated/repaired; runtime acceptance separate.** In member 260, trainer 107's loss branch at `0x61C` jumped to initialization path `0x6C4`, reaching neither `WhiteOut` nor `ReleaseAll`. All four healthy partner-loss branches reach sole `WhiteOut` at `0x7A4`; the author's 1.05 changelog describes the same correction. A same-size retarget changes only two displacement bytes, preserving SG-01a closes, victory and all other loss branches. [safari_defeat_whiteout.py](../sgp131/safari_defeat_whiteout.py) and an independent checker cover RED/GREEN, mutants, EN/IT replay/geometry and sole member 260 ownership. Played defeat, SAVE/cold and device coverage are not established here; generic menu/audio/turbo symptoms remain separate. |
| SG-02 | Route 47 battle triggers from the wrong elevation. | **Source-bound defect demonstrated/repaired; natural runtime coverage separate.** [Original post 1460](https://gbatemp.net/threads/pokemon-sacred-gold-storm-silver.327567/page-73) retains its [screenshot](https://imgur.com/JNtrO): the player below the bridge triggers the first duo above. Native `sub_0203DE04` checks X/Z, rectangle and variable but ignores Y; custom Mira trigger `script7 @ (141,397)` can fire from the lower level's same column. The unreachable 0×0 record is not the cause. Global dispatch is untouched: all 217 current `CoordEvent` records have Y=0. Export 7 now uses an appended 23-byte wrapper calling `GetPlayerXYZ`, exiting without effects when Y≠0 and reaching original entry `0x1BF` only at bridge height. Four hypotheses/twelve sequences, mutants, roundtrip, producer and EN/IT composition/replay pass; private deterministic output SHA-256 `65e05d94…ab11`. Pre-event raw save, natural battle, SAVE/cold and hardware remain separate; no defect is claimed for the other three triggers without a demonstrated overlapping lower route. |
| SG-03 | Altered MooMoo Milk dialogue. | Slang is separate from structural text damage. [Earlier 1.04 work](../../CHANGELOG.md#104--9-september-2026) repairs controls. In 1.2.5 and pending EN/IT, bank 397 entries 12–14 have valid centering controls. No new rendered scene was observed in this survey. |
| SG-04 | Icicle Plate/Steven in Vermilion fail on R4. | **Hardware report open; no demonstrated common cause.** The [original list](https://gbatemp.net/threads/pokemon-sacred-gold-storm-silver.327567/) combines two events. A [contemporary R4 report](https://gbatemp.net/threads/pokemon-sacred-gold-storm-silver.327567/page-25) concerns immobile Steven; Drayano separately documents [Steven script ordering](https://gbatemp.net/threads/pokemon-sacred-gold-storm-silver.327567/page-59), repaired as SG-15. Current waits/paths show no common divergence. Another ROM patch needs an authenticated R4 model/kernel/save and first incorrect callback. |
| SG-05 | Mew event freeze. | **Documented 1.3 repair; historical R.** Three movement waits; see [cause, hashes and evidence](stability-investigation-1.3.1.md) and [EN/IT campaign](android-validation.md). No new 1.3.1/flashcart playtest is claimed here. |
| SG-06 | Garchomp lacks Rough Skin. | **D consistent with inherited fix.** Ability slots 8/24 include Rough Skin in 1.2.5 and pending EN/IT; battle effect not re-executed here. |
| SG-07 | Claydol cannot learn Fly. | **D consistent with inherited fix.** HM02 compatibility bit is present in 1.2.5/pending EN/IT; no learning UI playtest here. |
| SG-08 | Duplicate Lyra/Ethan after a Goldenrod defeat. | **Repaired in successor source:** SetFlag 712 before WhiteOut while preserving retry; three modeled loss paths. All six survey inputs retain the defect. This component evidence does not itself establish visible deduplication or save compatibility on a newer composition. |
| SG-09 | Ground Ball contains about 450 Full Heals. | **Successor source repairs request 436→1.** All six survey inputs request 436, not 450. Preserved Bag hooks determine actual addition/saturation. Bytecode models are not an observed in-game inventory count. |
| SG-10 | Odd Keystone description typo. | Plus author claims a 1.02 fix. Current EN/IT text is readable; exact historic typo is unidentified for comparison. Do not count a new project repair. |
| SG-11 | Night fishing produces empty/MissingNo slots. | **D/P defect present in all six hack inputs**, absent as truncation in two checked retail images. Swarms/phone also consume the data; details below and later SG-11 implementation are distinct. No capture/crash was induced by the survey. |
| SG-12 | Manual places Silver Wind on Route 39 instead of 38. | Documentary correction claimed since 1.02; [acquisition audit](../sgp13/data/guide-content-sources.md) places TM62's Ball on 38. No new engine patch or complete historical-PDF review. |
| SG-13 | Route 34 Gentleman/Lady names. | **Data bug confirmed; `SOURCE_EXHAUSTED`, no safe patch.** Map 38/event 35 binds Gentleman object 0 to trainer 62 and Lady/Socialite object 13 to 409. Classes/sprites fit, but names remain retail Youngster Samuel/Emanuele and Pokéfan M Brandon/Mariano; ten Gentleman records control the decoder. Drayano only said names had not stuck. Thread/Wayback, byte-identical official 2012 ZIP/mirror, all six PDFs, FAQ/video/guides and multilingual searches do not reveal intended names. Brenda/Mariana or others would be invented; reopen only with new author evidence. |
| SG-14 | Route 13 couple's name. | **D consistent with inherited fix.** Trainer 559 is Tim＆Sue EN/Udo&Mia IT, doubles flag 2; battle intro not observed here. |
| SG-15 | Steven fails to recognize Lati after Regigigas. | **Repaired in successor source:** prioritize the correct still-owed Lati while preserving other 775 states. Before/after models pass; all six survey inputs retain wrong precedence. SG-15b separately guards reward loss with a full Bag. No new rendered scene in the component survey. |
| SG-16 | Celebi/Giovanni freeze at Tohjo Falls. | **Unconfirmed, D/P/model; runtime fixture unavailable.** Member 114 and map 298 binding are identical in nine historical EN/IT images. Twelve checks refute wrong binding, missing movement wait, missing field restore after defeat and deterministic nonterminating task. None of 184 unique valid raw saves provides a usable pre-event state. Three native follower dereferences remain a latent risk, but no ordinarily reachable NULL is demonstrated. No ROM change without first played divergence. |
| SG-17 | Cynthia withholds Sinnoh starter after Earth Badge. | **Refuted requirement, D/P/model; no patch.** Twelve sequences on real member 890, identical in nine EN/IT images, show no Earth-Badge check: Champion status, clear `3F9B`, live lead Sinnoh starter/evolution and two free party slots are required. EN/IT text and Guide agree. Species 387..395, party 1..6, mutants and flag-cycle models pass. None of 184 unique raw fixtures supports complete playtest; reopen with a compliant save still refused. |
| SG-18 | Scizor learns Night Shade instead of Night Slash. | **D consistent with inherited fix.** Night Slash 400 at levels 45/65 in 1.2.5/pending EN/IT. The original report did not concern Dark Pulse. |
| SG-19 | Custom flags apparently reset. | The 1.3 line repairs concrete [high-flag/Pal Pad overlap](../features/event-flags/README.md), with [historical evidence](android-validation.md). A [community 1.0.5 save](https://gbatemp.net/threads/pokemon-sacred-gold-storm-silver.327567/page-113) loses Jirachi/Manaphy triggers together: useful new fixture, not a second demonstrated cause. Do not assign one cause to all reported resets. |
| SG-20 | Ledyba Attack/Sp.Attack not swapped. | **D: author's 1.02 claim not confirmed in this project's 1.2.5**, still 20/40. V4/pending use 40/40 as [intentional balancing](shiny-species-1.3.1.md), not 40/20. Do not reduce Sp.Attack to imitate the old claim. |

## Additional community and component findings

These are separate from the original twenty. Some were refuted on available
inputs, others repaired in source; source exhaustion is not a license to invent
a replacement name or roster.

| ID | Report/source | Evidence, resolution and limits |
| --- | --- | --- |
| SG-TR01 | Alfred's highest Lighthouse rematch allegedly gives Noctowl/Arcanine/Nidoking no moves, only Struggle. [18 September 2012 first-hand report](https://gbatemp.net/threads/pokemon-sacred-gold-storm-silver.327567/page-67). | **Refuted on available line, D/P; no fix.** Ten authenticated EN/IT images from Plus 1.04 to the then-current candidate share trainer 674 format 1/custom moves: three records with twelve nonzero move IDs. Overlay 26 has sole progression `401/401/672/673/674/0`, reaching that record. Repeated results are identical. Native local bench was limited by `SIGILL`; no played battle or authenticated 1.05/Plus 1.03 input. The report may concern an older artifact, not this demonstrated candidate. |
| SG-TR02 | Wade's first rematches allegedly decrease from about 52 to 46. [Community-hosted v1.05 trainer guide](https://www.scribd.com/document/866552982/SS-SG-Trainer-Pokemon-by-JD48096761). | **Confirmed/repaired in source, D/P.** Sole selector `4/4/461/460/512/0` really yields 52→46→68. `trainer-fixes` swaps equal-size party members 460/461 to 46→52→68, preserving selector/header/species/moves/NARC geometry/all other trainers. Six focused tests and in-memory EN/IT application pass; only eight level bytes differ. Played rematches on the same save were not part of this component evidence. |
| SG-TR03 | Jose's first rematch uses retail solo Farfetch'd 44 between Plus teams. [Played trainer guide](https://www.scribd.com/document/866552982/SS-SG-Trainer-Pokemon-by-JD48096761). | **Anomaly reproduced; `SOURCE_EXHAUSTED`, missing authoritative replacement.** Selector `414/414/303/446/602/0` yields Farfetch'd+Chatot 48, solo 44, duo 55, trio 68, identical from Plus 1.04 through EN/IT V4. JD labels it probably a bug but explicitly provides a played log, not author documentation. Thread/Wayback, official 2012 ZIP, six PDFs, FAQ/video, mirrors and multilingual guides prescribe no tuple. Reena/Gaven/Jamie suggest a level 50 duo but do not determine records/difficulty/move policy. Replacing it would be a balance decision, not recovery of a proven historic fix. |
| SG-EV01 | Mantyke does not evolve with Remoraid; [contemporary report](https://gbatemp.net/threads/pokemon-sacred-gold-storm-silver.327567/page-36), [author confirms Voltorb requirement](https://gbatemp.net/threads/pokemon-sacred-gold-storm-silver.327567/page-59). | **Confirmed/repaired in source/component.** Evolution member 458 in `a/0/3/4` required Voltorb 100 instead of Remoraid 223. Producer changes only the parameter with pre/post hashes and semantic readback. Guide derives from the same corrected records. Played evolution, SAVE/cold and device are not established by this campaign. |
| SG-EV02 | Feebas attempts evolution every level with zero Beauty; [author note](https://gbatemp.net/threads/pokemon-sacred-gold-storm-silver.327567/), [independent report](https://www.reddit.com/r/PokemonROMhacks/comments/ff16ju/sacred_goldstorm_silver_feebas_randomly_evolved/). | **Confirmed/repaired in source/component.** Member 349 Beauty threshold 0→170 only. Required gameplay controls include 169/170 and cancel/retry. |
| SG-EV03 | Female Combee evolves as early aslevel 6; [community report](https://www.reddit.com/r/PokemonROMhacks/comments/cgxkao). | **Confirmed data/repaired source/component.** Member 415 level 0→21; male and 20→21 boundary are negatives. Randomized report still matches identical preimage in ten EN/IT Plus images. |
| SG-EV04 | Female Burmy attempts early evolution. | **Confirmed data/repaired source/component.** Female branch of member 412 level 0→20; male branch already 20 provides a differential control. |
| SG-AI01 | Plus AI choices/switching ignore Fairy despite correct damage. | **Confirmed/repaired in source/component; natural battle coverage separate.** Eight-ROM old bench retains 120 Fairy divergences/zero retail as preimage. Fix uses 148-byte resident Thumb helper SHA `d965f5ff…b2a6f` and two overlay 12 seams, handling only Fairy rows/columns and delegating other pairs natively while preserving HG-B13/Scrappy/Gravity/Iron Ball. SG-AI01 alone adds 8 compressed bytes; SG-AI02/SG-DM01 composition adds 20. FAT 12/y9 size and derived Module96 y9 CRC are independently reconciled; peeling reconstructs cold UI. Helper, over 76000 dynamic cases, mutants and full EN/IT chains pass. Natural battle/communication, SAVE/cold and device remain separate. |
| SG-AI02 | Conversion 2 ignores Fairy when selecting a type. | **Confirmed/repaired in source/component; natural battle coverage separate.** Command `0x02240C98` called `GetTypeEffectivnessData` at `0x0225260C`, limited to 112 retail rows. Last-type Fairy scanned without changing type; ARM EN/IT reproduces failure with valid Fire control. Writer replaces exactly 64 helper bytes with authenticated SHA `1ab0ab8d…5875`, using 325 selectable modern-chart rows and native RNG/modulo. Fairy then chooses a valid resistance without reading retail chart. Replay/mutants/full EN/IT chains pass; natural battle/SAVE/cold/device remain separate. |
| SG-DM01 | Iron Ball/Gravity damage uses modern indices on retail columns. | **Confirmed/repaired in source/component; natural battle coverage separate.** Native `0x02251D28` indexes modern chart but helper `0x02251C74` still dereferenced retail columns. ARM EN/IT shows Ground→Flying correctly immune normally but wrongly immune with Iron Ball/Gravity. Only literals `0x02251D20/24` change to `modern+1/+2`; grounded cases become damage 100/no `NO_EFFECT`, Ground→Poison/Fairy→Dragon controls remain green. Replay/full EN/IT chains pass; natural battle/SAVE/cold/device remain separate. |
| SG-DM02 | Plus Ghost→Dragon/Dark multipliers swapped; [also reported on 1.1.2](https://gbatemp.net/threads/pokemon-sacred-gold-storm-silver.327567/page-114). | **Confirmed/repaired in source/component.** Six versions from Plus 1.04 through manual-test 1.3.1 EN/IT use 5 for Dragon/10 for Dark; 322 other pairs match modern oracle. Confined producer swaps two overlay 18 bytes inside `ai`; double EN/IT readback, replay and mutants pass. Natural battle/SAVE/cold/device not established by this campaign. |

Internal **V-CHATOT** was discovered after the original catalog: 24 out-of-domain
story variables `612E..6139`/`619E..61A9` aliased Chatot samples. HF02 reproduces
and repairs it at component level; see [code audit](bug-audit-1.3.1.md) and
[native contract](../features/event-flags/README.md). It is not artificially
renumbered SG-21.

## SG-LATIOS: unresolved maintainer report

At Vermilion's central totem, dialogue/movement followed by Latios battle entry
can leave a white screen and audio stuck on one note. **This remains open and
unisolated.** Map 54 uses script 776/entry 16, event 51 and `WildBattle(381,40,0)`.
Script `f70f4320…cbf2`, event `e407ae57…b9a26`, movement and native battle-launch
windows are unchanged across all 26 retained ROMs. The same exact 1.2.5 image has
both a reported freeze and a successful run.

Missing `WaitMovement` is not a demonstrated cause: movement had completed
before `WildBattle` in the successful run. The then-current EN/IT candidates
passed 18 static scenarios each. Their 1.3.1 change for this encounter was only
the BL to the shiny hook: it needs its own testing but cannot explain the older
1.2.5 report. Do not transfer Mew's repair by analogy or claim Latios fixed
without the first machine divergence. Private Latios campaign records retain
the detailed protocol/identities.

On 3 November, 10 cold boots of 1.2.5 IT and 10 of candidate IT `420ec8b8…f059a`, varying
input intervals 112..130 frames, all reached offset 1704 and battle ownership:
**20/20**, movement 0, no assert, unchanged ROM/fixtures. Digest `51a28336…657f`.
This strengthens non-reproduction, not a repair or universal refutation: one
fixture/runtime, without ARM7/FIFO, audio or physical device. The identical-bench
stop criterion was reached; repeat only with the failing save/configuration or
an independent environment.

The 4 November Victory Road postimage recheck retained script/event hashes and
passed 36 combined static scenarios and 7/7 bench tests. It still did not isolate
a cause or justify a movement-wait patch. Targeted external research found no
second independent freeze report. A distinct healthy control in a
[Polish play diary](https://pokemon.fandom.com/pl/wiki/Blog_u%C5%BCytkownika:Jetian/Pok%C3%A9mon_Sacred_Gold_i_Storm_Silver)
describes Soul Dew's reaction, appearance, battle and capture. This agrees with
the local success but does not disprove intermittent/save-dependent failure.
Audio held on its last note is a non-advancement symptom, not independent proof
of an audio cause. The later 1.3.1 battle type-loop repair is a separate defect;
it does not establish resolution of this historical Latios report.

Trainer-name resolution must add `FIRST_TRAINER_INDEX = 1` after subtracting
3000/5000, or it misattributes the preceding trainer's name; see
[reference code](https://github.com/pret/pokeheartgold/blob/0985e8718df4f25e64d6507d89c0c97c0d288981/src/script_manager.c#L425).

## Initial root-cause evidence and later repairs

The following observations concern the original six survey images. Their
hashes remain unchanged. The original proposals were subsequently implemented
where stated in the [code audit](bug-audit-1.3.1.md); these are technical records,
not a request to apply a second patch over an accepted ROM.

### SG-09: pickup quantity

`a/0/1/2` member 141, zero-based entry 56, global script 7056: `0x0862` sets item 27;
`0x0868` sets quantity **436**, operand at `0x086C`. The common branch copies it
into the space check and GiveItem. Binding: map 201, Goldenrod Tunnel B2F,
event 194/object 35 at (7, 4), hideflag 1095. It is bound to a live object, although
walking to the Ball was not part of the survey.

Plus Bag modifies HasSpaceForItem/GiveItem. Script bytes alone do not prove
all inventories receive 436, that full stacks leave the Ball, or that the gift
cannot be partial. Include the [Bag contract](../features/borsa/README.md) in
the oracle. The later repair changes only the requested quantity to 1, preserving
IDs/flags and already obtained items without retroactive subtraction. The
acceptance matrix distinguishes empty/populated inventory, cap/insufficient
space, one-time collection and EN/IT SAVE/cold.

### SG-08: losing to the friend

Member 93 is identical across the six original inputs:
`99681fdf303533d7eae6bf06ef672a5b947ee1a2b4a3261a7929bfe363d051e0`.
Map 118, Goldenrod Tunnel 1F, event 115: friend/Marill objects 2/3 share hideflag 712
(`0x2C8`). The still-enabled scene at `40F8=0` reveals the flag and creates both
objects. Trainer 11/19 loss paths reach `0x0553`: WhiteOut, ReleaseAll, End,
without restoring 712. A later load can therefore prepare objects that the scene
creates again. The object implementation corroborates missing ordinary
deduplication; this survey did not execute/compare all relevant functions in ARM.

The later repair restores **the same** hideflag before WhiteOut, preserving
`40F8=0` and retry without new variable/save migration. Coverage must distinguish
both genders, north/south entry, loss/return, later victory, NPC count and
SAVE/cold, including an older post-loss save. Already serialized duplicates
need their own observation rather than assumed cleanup.

### SG-15: Steven's check ordering

Member 757 is identical in the six original inputs:
`c223b9665a411c9d99a1e73a5857d87931ec41a24a126ad288f55c3bfd1b4b69`.
Binding: map 477, Steven's Pewter house, event 430/object 0, one-based entry 1
(index 0). After introduction/Hoenn gift, `0x0037` checks 775 (`0x0307`); when set,
`0x003B` jumps to `0x0458` **before** Lati `3FCA`/reward `3FB8` checks. It shows
message 23 and may open Steven's battle without delivering the still-owed Enigma
Stone.

Native `FLAG_HIDE_MT_SILVER_CAVE_MOLTRES` 775 is reused for Regigigas in script 106
and also script 815; captureflag 365 is also reused. Hall of Fame 825 clears 775
only if 365 is unset, so it does not clear after capture. Clearing flags or
repeating the League is not a valid repair instruction.

The successor repairs precedence/dialogue guarding while preserving event IDs,
already caught legendaries and one-time delivery. Acceptance distinguishes both
Lati/Regigigas orders, reward claimed/unclaimed, correct/incorrect Lati, Earth
Badge present/absent, full Bag and EN/IT SAVE/cold. Symbolic paths with/without 775
do not replace those rendered scenes. SG-15b's full-Bag reward guard is distinct.

### SG-11: fishing and secondary consumers

Both inspected retail images have 142 records of 196 bytes in `a/0/3/7`. The six
hack archives are identical:
`a66f72f48341a1ec3131b521641ab6e671ad890d07676131b00fed2704ec3d4d`.
They contain 130 records of 192 bytes and 12 complete; **70 truncated records have
active fishing**. Missing bytes hold `nightFish` at 192 and `fishSwarm` at 194.
The loader clears the buffer before reading, leaving them zero.

The original consumer inspection, rather than execution, found:

- Overlay 2 `0x02246AD4` replaces Good Rodslot 3 and Super Rodslot 1 with unguarded
  zero species at night: ordinary weights 10%/30% of generated encounters, not
  all casts.
- Overlay 2 `0x02246BD8` fishing swarms can zero additional slots, even by day.
- Overlay 101 `0x021F2E24` fisherman phone calls also read the night field; fixing
  only battle leaves this consumer.
- Pokémon Talk already guards nonzero values.

**Copying retail tails would alter valid hack encounters.** The original
packaged *Pokemon Locations.pdf*, page 2, specifies New Bark Good Rod
Shellder 60%/Chinchou 40%, Super Rod Shellder 60%/Lanturn 30%/Gyarados 10%, without a
time distinction. Current base slots match; retail replacement would remove
30%Lanturn and would not be a neutral repair.

The resulting policy treats zero as no night substitution in the two affected
consumers, completes records preserving their first 192 bytes, and restores only
mapped swarms: Violet/Whiscash, Route 12/Relicanth, Route 44/Remoraid,
Route 32/Qwilfish. The manual lacks Route 32's Swarm row; that source instead is
the native table and same retail map. This documentary difference stays explicit.

The initial Python model enumerated 1125 record/rod/time/swarm combinations:
340 zero-species outcomes with transcribed consumers, none under the proposed
policy. **That is a model, not ARM execution or played fishing.** The original
sandbox Unicorn attempt died with SIGILL and was not a pass. Later installed
code evidence is separate. Gameplay acceptance distinguishes negative controls,
three rods, five periods, four swarms, phone, radio, separate Safari, both
languages and SAVE/cold.

## Alternative versions mentioned in the discussion

**The comment was found; its patch identity remains unattributed.** Public user
speedguru wrote it on
[30 October 2026 at 23: 54 UTC](https://www.reddit.com/r/RomHacks/comments/1xebcg1/comment/19rwjjgmhq8ar/).
At the recorded review, the live comment named/linked no patch and had no visible
replies. Search cache showed two comments while the browser showed 17, allowing
confirmation. The public profile hid comments; no private access/message was
attempted. The maintainer's public crossposts supplied no name.

DeadSkullzJr, SunGold/MoonSilver and Reforged are comparison candidates, not an
established identification. DeadSkullzJr separates
[packaging/AP from gameplay](https://gbatemp.net/threads/pokemon-sacred-gold-storm-silver.327567/page-110);
[1.1.1/1.1.2](https://gbatemp.net/threads/pokemon-sacred-gold-storm-silver.327567/page-111)
do not claim every original case repaired. A
[March 2026 Mew report](https://gbatemp.net/threads/pokemon-sacred-gold-storm-silver.327567/page-114)
lacks hashes and establishes no universal cause, but prevents that promise.

For [Reforged Alpha 5 a](https://github.com/oliverdesa/Sacred-Gold-Reforged/blob/main/patcher/KNOWN_ISSUES.md),
the historical review authenticated three small source/documentation files by
SHA-256 and Git blob, about 27 KB, without obtaining game/donor files. Alpha 4 ab's
claimed Safari partner cleanup was not shown equivalent to SG-01.
The [installer source](https://github.com/oliverdesa/Sacred-Gold-Reforged/blob/main/patcher/sacred_gold_patcher.py)
applies an xdelta with two donors, not the Safari fix's source. Packaging alone
does not reveal that implementation. No game delta was imported or cross-line
compatibility assumed.

| Line | Primary claims found in the historical review | Boundary |
| --- | --- | --- |
|Original Plus 1.02/1.03|Seven named Reddit fixes: moves/abilities, text and one document.|Ledyba shows why actual input bytes must be checked.|
|DeadSkullzJr 1.1.1|[Author, page 110](https://gbatemp.net/threads/pokemon-sacred-gold-storm-silver.327567/page-110): plays like 1.1.0; image/Classic/AP work. [19 August 2025 reupload](https://gbatemp.net/threads/pokemon-sacred-gold-storm-silver.327567/page-111) concerns held-item effects.|Version alone does not distinguish reupload or repair every quest.|
|DeadSkullzJr 1.1.2|[13 September 2025](https://gbatemp.net/threads/pokemon-sacred-gold-storm-silver.327567/post-10726814): restores English Pokédex assets.|[Mew report on 1.1.2](https://gbatemp.net/threads/pokemon-sacred-gold-storm-silver.327567/page-114) prevents universal inference.|
|SunGold/MoonSilver|[Author topic](https://projectpokemon.org/%68ome/forums/topic/37260-pok%C3%A9mon-sungold-amp-pok%C3%A9mon-moonsilver/), March 2016: balancing with Safari-crash warning.|Direct access 403; indexed primary text readable. Not a validated repair baseline.|
|Sacred Gold Reforged|[Author repository](https://github.com/oliverdesa/Sacred-Gold-Reforged), created 26 October 2026. [Alpha 5 a](https://github.com/oliverdesa/Sacred-Gold-Reforged/blob/main/patcher/KNOWN_ISSUES.md) also claims Safari partner cleanup in Alpha 4 ab.|Gen V/Anvil integration; [README](https://github.com/oliverdesa/Sacred-Gold-Reforged/blob/main/patcher/README.md) calls it a prototype without universal save compatibility. No project build/test or identification with the unnamed comment.|
|Sacred Gold Revamped|[Author, 2015/2020](https://www.pokecommunity.com/threads/sacred-gold-revamped.359688/): teams through Chuck; incomplete/abandoned.|Not demonstrated general repair.|

Redistributor claims such as complete/fixed/no-bugs were not accepted as evidence.
Loader/AP/emulator defects remain separate from ROM defects; a closed issue alone
does not establish a game repair.

## Separate reports and their present limits

- **Fuchsia Cloyster:** a [13 September 2024 report](https://www.reddit.com/r/PokemonROMhacks/comments/1ffyvun/)
  describes overlap/a coordinate workaround. Map 56, script 807/event 53 object
  layout alone does not prove interaction impossible. A
  [contemporary 1.05 report](https://gbatemp.net/threads/pokemon-sacred-gold-storm-silver.327567/page-33)
  adds a different concern: successful escape allegedly removes Cloyster and
  advances the event as victory. Distinguish all three Cloyster, win/loss,
  successful/failed escape and before/after flags. Open; no fix from one frame.
- **GB Sounds during Radio Tower takeover:** two 1.05 users report overlapping
  GB/modern music then silence after opening X/menu following the key; Drayano
  links early GB Sounds acquisition ([page 33](https://gbatemp.net/threads/pokemon-sacred-gold-storm-silver.327567/page-33),
  [page 47](https://gbatemp.net/threads/pokemon-sacred-gold-storm-silver.327567/page-47)).
  Separate from Surf HG-F06. Compare takeover OFF/ON, activation before/after,
  same retail path and cold boot without cheats/turbo.
- **Zero Lyra/Ethan prize money:** Drayano confirms the special class has money
  multiplier 0 ([page 59](https://gbatemp.net/threads/pokemon-sacred-gold-storm-silver.327567/page-59)).
  Candidate class 1/native class 1→0 mapping is static evidence, not an observed
  balance. Compare Silver/ordinary trainer, Amulet Coin OFF/ON and before/after
  money.
- **Route 43 Gastrodon called Nidoking:** the author acknowledges wrong text
  ([page 23](https://gbatemp.net/threads/pokemon-sacred-gold-storm-silver.327567/page-23)).
  Trainer 132 has one level 40 Gastrodon; English bank still says `My Nidoking was
  outstanding!`. Inspect EN/IT binding and any rematch; none of this case's
  current parties contains Nidoking.
- **Ruins of Alph Unown gift:** one 1.05 user with 18 Unown reports a communication
  error at the second man from left, not repeated after reset
  ([page 35](https://gbatemp.net/threads/pokemon-sacred-gold-storm-silver.327567/page-35)).
  Low priority until reproducible with 17/18/19 Unown, cold boot versus savestate,
  other NPCs/gifts, cheats/turbo OFF and EN/IT.
- **Union Room/trades reopening custom events:** three historical groups report
  completed gifts/events returning after trade, Union Room or record mixing:
  [2012 page 46](https://gbatemp.net/threads/pokemon-sacred-gold-storm-silver.327567/page-46),
  [2018 page 99](https://gbatemp.net/threads/pokemon-sacred-gold-storm-silver.327567/page-99),
  [2018 page 100](https://gbatemp.net/threads/pokemon-sacred-gold-storm-silver.327567/page-100).
  Jasmine's Gym Rocket, Pikachu gift and Jirachi Kimono Girl corroborate symptoms
  beyond page 115, without establishing cause. Compare entry/trade/record mixing
  separately on the same flags before/after SAVE/cold. This is the strongest
  external regression for the local high-flag/Pal Pad repair, not another bug
  to count without a residual delta.
- **Moltres capture→SAVE→black Continue:** a
  [Reddit report](https://www.reddit.com/r/PokemonHGSS/comments/1mkvka5/game_crash_in_sacred_gold/)
  includes a DraStic case as well as its melonDS author; an older 2018 case is on
  [GBAtemp page 100](https://gbatemp.net/threads/pokemon-sacred-gold-storm-silver.327567/page-100).
  Versions/hashes are missing but the sequence is more than one hypothesis.
  [Page 115](https://gbatemp.net/threads/pokemon-sacred-gold-storm-silver.327567/page-115)
  adds a claimed recovery involving save byte `0x18BA` and seven Safari flags,
  based on explicitly AI-generated analysis. No cause/repair follows without
  watchpoint, both-slot comparison and pre-capture fixture. No blanket save
  clearing.
- **Route 47 Dragon Tail during Rocket/Safari arc:**
  [2012](https://gbatemp.net/threads/pokemon-sacred-gold-storm-silver.327567/page-25)
  and [2022](https://gbatemp.net/threads/pokemon-sacred-gold-storm-silver.327567/page-108)
  reports associate early pickup with black screens/locked menus. A
  [2025 case](https://gbatemp.net/threads/pokemon-sacred-gold-storm-silver.327567/page-110)
  broadens symptoms without isolating the item. Compare before/after duo and
  arc completion, then Bag/Party/Pokégear/SAVE/map change. Do not collapse all
  takeover symptoms into the reward script before the post-arc control isolates
  a cause.
- **Week Siblings' ribbons:** two 18–19 September 2012 reports describe stopped
  music/freezing after Tuscany's gift, then all siblings. This corroborates the
  already repaired [gift-script family](gift-script-fixes-1.3.1.md); it is an
  additional historical source, not another open bug or duplicate patch.
- **QA-05:** Mr.Mime/Lopunny retain 46-byte learnsets with terminator at 42 and
  two trailing zeros across six hack inputs, including pending images. This
  violates the consumer contract without a demonstrated crash/data loss here.
- **Icicle Plate:** the inspected branch does not directly set hideflag `3FAB`.
  Possible repeatability needs its own consumer trace; it is not an established
  explanation for the R4 freeze.
- **Storm Silver Fairy 1.1 stone shop:** [Drayano FAQ Q 85](https://pastebin.com/UEzNBDHC)
  attributes it to that variant and distinguishes unaffected Sacred Gold. No
  new defect of this base is demonstrated.
- **Battle Frontier guard:** a [report with Drayano's reply](https://gbatemp.net/threads/pokemon-sacred-gold-storm-silver.327567/page-23)
  describes freezing before Cianwood/Jasmine; he believed it already repaired.
  A regression screen should distinguish before/after Mineral Badge, dialogue/
  collision, melonDS/DeSmuME. One report does not reopen the candidate defect.
- **Apricorn Box:** a [single Delta case](https://www.reddit.com/r/Delta_Emulator/comments/1e8i7ey)
  reports black screen after Kurt; another commenter suspects wrong ROM. First
  authenticate hash/patch and compare the same raw save on candidate/retail.
  Low priority, possibly packaging/emulator related.
- **Olivine/rival and letter-bearing Spearow:** historical cases were declared
  repaired in 1.0.1/1.0.4 respectively. Modern hashless Delta reports justify
  quick regressions, not automatic reopening/new patches. Preserve ROM identity,
  cheat/turbo state and the same raw save.

## Additional hack-specific leads from 3 November

- **Deoxys event/battle:** reports describe a 2012 crash and 2020 failure to appear
  at the expected time, without build identity. Compare authenticated 1.05 and
  EN/IT candidate with Earth Badge and RTC 23: 59/00: 00/03: 59/04: 00 boundaries.
  [2012](https://gbatemp.net/threads/pokemon-sacred-gold-storm-silver.327567/page-45),
  [2020](https://gbatemp.net/threads/pokemon-sacred-gold-storm-silver.327567/page-104).
- **Outdated Pokédex areas:** coherent 2016–2025 reports require joining actual
  encounters to area resources by time/variant, separate from retail regional
  filters. [2016](https://gbatemp.net/threads/pokemon-sacred-gold-storm-silver.327567/page-94),
  [2025](https://gbatemp.net/threads/pokemon-sacred-gold-storm-silver.327567/page-110).
- **Union Cave vicinity freeze:** one report identifies a bridge fisherman and
  external hiker toward Azalea; version/emulator unknown. Map trainer/script IDs
  and repeat talk→battle with a clean save.
  [Source](https://gbatemp.net/threads/pokemon-sacred-gold-storm-silver.327567/page-104).
- **Map Card on a second playthrough:** two 2025 posts by one author are one
  testimony. Inspect Guide Gent/Map Card flags before promoting it to a bug.

## Save continuity and composition requirements

Repairs must preserve event identifiers and require no new save format. That
constraint alone is **not tested compatibility**. Already owned items/Pokémon,
progress and Plus settings must never be removed/reset, and access to repairs
must not require New Game.

Integration requires a failing original regression, passing repair, pinned
preimages, independent readback and foreign-resource confinement. The 1.3.1
composition has one archive writer and UI seeds bound to FAT/header; appending
a second archive after UI would invalidate that contract. Register changes in
the correct producer and verify final composition rather than layering onto an
accepted ROM.

Acceptance uses preserved copies of older saves without Plus, configured saves,
expanded Bag and active Training: Continue, native SAVE, cold restart and
independent semantic comparison. Available fixtures are bounded, not universal.
The initial survey included no SAVE/cold/build/Android runs; later component/
composition evidence is separately documented and originals remain preserved.
Private small reports/reproducers retain inspected-data hashes. No extracted
scripts, ROM or saves are distributed. Every future resolved status needs exact
candidate identity, executed evidence and limits without reassigning old reports
to new bytes.

## HG-B16 and SG-TR04: trainer alternate forms

The first dedicated campaign authenticated ten Plus EN/IT images across 1.04,
1.1, 1.2.5, V4 and 1.3.1. Horton 396 really has five level 57 Rotom forms 1–5. Native
HGSS first creates base Rotom/calculates stats, then sets only `MON_DATA_FORM`.
The independent oracle applies `CalcMonStats`' formula to the resolved form's
personal data.

All 50 reachable slots diverge; ten form 0 controls remain identical.
Heat/Wash/Frost/Mow produce `124/62/101/108/124/92` rather than
`124/79/138/92/124/126`; Fan should be `124/79/119/123/124/109`.
Two complete runs produced the same file, SHA-256
`bc1e98e1bcf5084e42fda53f21b80cd9c7bf60448b7e273f71cc53bba1a8058e`;
canonical result digest
`480e44ecbe03f04035ebc34da23e7edc4d4e84654e2bee777a6fe1c8ab6cf6e7`.

The actual ARM9 constructor then ran twice inside melonDS with real heap,
NARC readers, Pokémon encryption and Party code. Both returned forms 1–5,
valid checksums and identical vulnerable stats; component digest
`6c103588bb48e3e82e40e7a0ab789668c964ff642e5ea1917047676d59c39248`.
Both allocations were freed, runtime exited 0, originals/copies stayed unchanged.

The TDD repair is in `trainer-fixes`: the same 50-byte shared ARM9 helper now
calls `UpdateMonAbility`, `CalcMonStats`, then the existing Frustration/friendship
check. All four trainer formats converge there; NARC/overlays/save layout/IDs
stay unchanged. Post-fix melonDS passes natural T0 twice, synthetic T1/T2,
natural T3 and form 0 negative with expected stats, valid checksums and freed heap.
This is debugger-assisted component execution on an IT candidate; natural battle/
turn order, EN runtime, SAVE/cold and device remain separate.

The separate **SG-TR04** cycle showed that `CalcMonStats` alone left wrong
abilities: Horton's Rotom Fan retained Levitate 26 instead of Motor Drive 78;
Wormadam Sandy/Trash with ability slot 1 retained 102 instead of 8/5. ARM bench
observed six EN/IT failures before repair. Adding `UpdateMonAbility` first in
the same 50 bytes makes Horton, both slots/all three Wormadam forms, form 0,
PID/checksum/Frustration/friendship/stats pass. Trainer suite 11/11, mechanics/
build 94 tests and full EN/IT chains pass. Natural battle, SAVE/cold/device remain
separate; this restores native form construction rather than intentionally
changing rosters or balance.
