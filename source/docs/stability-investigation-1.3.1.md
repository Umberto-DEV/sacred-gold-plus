# Stability and performance investigation for 1.3.1

This current subject record preserves the28October2026 investigation and 3November follow-up. It distinguishes the reproduced Mew crash, the1.3 Training/save defects and still-unisolated historical Latios freeze. [Android validation](android-validation.md) later completed49 functional checkpoints; [current UI validation](ui-1.3.1-validation.md) records later identities. Those results do not rewrite historical candidate scope.

## Reproduced Mew crash and demonstrated cause

Published1.2.5 IT ran from a copy of an advanced raw save. Native map change prepared map 147/player(22,54) facing first Mew(22,53); visibility flag was already clear. Ordinary A inputs reached cry/message then relocation. Two identical runs entered abort at bench frame 5315: main-loop counter stuck4856, ARM9 atFFFF0108 for 647 samples, input unresponsive. Same setup/no interaction ran1200 frames and accepted movement. The maintainer recognized the reproduced symptom.

Script3 started object13's arrival movement then ended; two later transfers repeated that order. `_RunObjectEventMovement` stayed queued with movement pending after script destruction, FieldSystem.taskman=0. `FieldSysGetAttrAddr` called `TaskManager_GetEnvironment(NULL)`:r0=0, CPSR97(abort), LR02050658; faulting `ldr r0,[r0,#0xC]` at 02050650 matches LR−8. Movement data also lived in the released script context. This is a lifetime violation, not infinite LockAll wait.

One private WaitMovement after the next-Mew start preserved the timeline before failure, completed movement/task and restored input. Production `sgp13/mew.py` inserts waits at all three transfers of member 115, authenticating whole member/decoder metadata and relocating offsets once.708→714 bytes; flags/nonrelative arguments/movement sequences/other files/executables unchanged. Nine ROM-free malformed/preimage/relocation/provenance tests and three EN/IT ClassB symbolic paths pass; replacing any added wait with Nop reopens that path. Native crash/recovery proof comes from emulator, not symbolic waiting. A first-wait-only counterexample passes event 1 then aborts event 2, proving all three are needed.

Independent review verifies no old branch/entry bypasses a new wait. Historical full run596A+4B=600 executed,198 skips; three Mew ClassB separately executed without skip.164 source fingerprints and composition checked. Runtime copies of the same advanced IT fixture on both languages complete all three departures, fourth Mew45 battle, native flee outcome5/field/no pending tasks, SAVE after departure3, new-process cold Continue, event state/movement and cold export=SAVE. Separate audits preserve profile/options/coins/party/native+expanded Bag/flags/Dex/Day Care/boxes/Plus. One advanced fixture in two languages is not universal compatibility. Diagnostic player repositioning was declared; unloaded-terrain images were excluded from graphic/navigation proof. Valid cold field/player41,63→41,64 used normal input. Capture/KO/perceptual audio/Android were not covered by this phase; later Android campaign has separate evidence. Published1.2.5 assets were never replaced.

## Latios remains unisolated

Same1.2.5 IT/advanced fixture/native map change/ordinary dialogue/Yes reached Latios40 battle through white transition; Soul Dew/visibility were already valid, without Bag/flag mutation. Movement finished before battle. Same-ROM diagnostic snapshot was never transferred across versions. This is non-reproduction, not a fix or universal refutation. Later20 cold boots/36 static scenarios/totem7/7/shiny route-abort53/53 remain in the bug audit. Script776/event 51 and objects20/21/22 differ structurally from Mew; do not add waits by analogy. Reopen with the actual freezing raw save/configuration or synchronized independent ARM9/ARM7/FIFO trace. A stuck note alone is not an audio-cause diagnosis.

## Training admission and native SAVE feedback

Training activation originally checked only its sectors49/113. Bag writer could reject foreign nonuniform records 48/112; training_save then returned3 before native commit because both Bag mirrors were required. Returning to Legacy policy did not disable journal. Synthetic foreign-record positive versus only-record-erased control, production Bag/Training ARM blobs and exact V8 EN/IT demonstrate it. Native cleanup restores generation/bank, flash unchanged, sleep lock balanced. Existing save not corrupted, but subsequent progress could not save.

Admission now checks all four Bag records before activation/policy change:≤four reads/1,808 bytes, reusing aligned452-byte buffer, not each frame. Code10,572→10,860 within 11,776. Active journal retains partial-commit protection. Eight address/bank foreign cases failed before; six composed synthetic tests pass after, comparing actual Bag functions including1,356 prefix mutations. Task 1 global587A/52 skips+4B/143 skips;25 native Training cases/language separately, no skips. ARM flash/OS/commit seams are declared, not emulator saves.

Touch caller falsely reported success after FALSE:writer returns3, native manager rolls counter back/releases sleep lock, Field_SaveGameNormal FALSE, but caller requests success sound/message. `sgp13/save_ui.py`/`features/save-ui/runtime.c` preserve TRUE path, show localized failure on FALSE, release icon/movement once, then require button release→new A/B/touch→release before field/reopen Save. Native state 9/flash fatal path not reused; foreign data not erased. Overlay30 grows224 raw bytes, compressed1,764 in original 2,048 slot, no resident reserve. Ten targeted tests(fourA/sixB EN/IT), ABI/ack/cancel/repeated refusal/mutants pass. Composed ARM I/O counterexample fails one Bag readback/rolls back; removing that fault permits generation 120/bank 0→121/bank 1, main+PC/native+extended CRCs/preserved inventory/settings/courses. Old Task 4P stub incorrectly used ROM-header IBM CRC; correct save CRC is CCITT/FFFF and checked on actual data.

Headless EN/IT raw copies with active Training and eight foreign-prefix bytes in inactive Bag record retain localized failure600 frames. Held confirmation touch during printing does not dismiss; new A/B/touch plus release returns field. Three actual reopenings/two further refusals per language retain SRAM byte-for-byte. VWait dumps show icon-destroy task removed next frame before app exit; movement/VBlank icon tasks not left pending. This proves feedback/refusal/reopen, not physical media failure or transient retry-to-success in full emulator.

Task 1 seven real cycles cover EN/IT noPlus, configured, expanded Bag, and advancedIT; Training inactive. Task 4 adds activeTraining EN/IT for nine total; some share or derive from the same input, not nine adventures. Continue→menuSAVE→new process raw cold, never savestate. Nine data groups include progress/party/allboxes/inventory/settings. Active cases retain two deposited Pokémon/course identity/goals/money/items/Plus while credited playtime advances. Every cold export=SAVE, original hashes stable;21 earlier/22 later liveness checks supplement state/data oracles, not exit0 alone. Task 4 snapshot654 executed/204 skipped; ten targeted private-input tests separate, not additive unique coverage.176 builder source hashes exclude unstated external tools. Physical faults/power interruption/new payments-rewards/perceptual audio/Android remain outside this phase.

## Diagnostic method and responsibility boundaries

Python composes/checks; ARM9/ARM7/overlays/resident Thumb execute. Native save arrays/Plus blocks/journals persist; NARC/tables hold content. Main concerns:build preimages/geometry/ABI/overlap; field object/follower/LockAll/WaitMovement/tasks; static versus random battle generation; OAM ownership/BattleContext lifetime; UI input/callback/windows/font;108 extra Bag slots and sync; save generation/CRC/sector ownership/commit order; explicit skip/seam/progress oracles. Native HGSS graphics use two256×192 screens,8px grid/native font/palettes. Existing state-driven Guide/font cache and battle caches should be measured before adding another cache.

Mew member 115 has four interactions/final WildBattle151,45,0; Latios/Latias776 uses381/380,40,0. Static SetupAndStartWildBattle/FieldSystem_GenerateSingleWildPokemon cannot be explained merely by random-wild Plus hook. LockAll mask 021D415C distinguishes player/talked object/follower/partner. Native EN/IT probe waits120 calls on pending movement and completes only when that bit clears:diagnostic discriminator, not user reproduction or authority to clear mask globally. A single CPU HALT PC is not a crash.

Observe main-loop021D1138 and VBlank separately, repeated CPU PCs/interrupts; then complete parent/child task/script chain, LeaveOverworld→StartBattle→Battle_LaunchApp→ApplicationIsRunning; only at first divergence inspect overlay I/O/allocators/assert. Binary EN/IT 1.04/1.1/1.2.3/1.2.4/1.2.5 comparison finds scripts/events143/51/LockAll/callback identical:rules out direct changes there, not interactions/runtime state. High flags/Pal Pad are a separate migration-sensitive cause.

Fresh baseline with required Apple clang21:ClassA 633 collected/581 executed/52 skipped; B147/4/143, total 585/195 skips, zero failures,13.766s. Host RunFrame time includes emulator/CSV/watch/audio; RunFrame, surface FPS and game VBlank differ. Crash tail PC-variable STALLO remains inconclusive even exit0; need dialogue/accepted battle command/field/reloaded-save oracle. No FPS/input/loading improvement follows from Training fix.

## Cadence and inclusive field cost

Published1.2.5 IT scenes Goldenrod76/Cherrygrove67 prepared by native map change on raw copy; same-ROM snapshots only for measurement, not save compatibility. Six initial offsets90–95,48 Down frames,60 release:two effective cycle phases, not six independent states. Both end six tiles south, same map/field/no task or pause, save unchanged. All frames 263 scanlines:main loop everytwo hardware frames, press→raw polling1–2 completed frames, press→continuous position2–3. Samples at frame end exclude subframe/visual controller-display latency. `game_vblank_counter` increments after waits in main loop, not interrupt count; game_frame_counter resets there. Neither alone is FPS. Initial route entering building excluded; corrected route checks map each sample. No city-wide or before/after improvement claim.

Inclusive FieldSystem_Control measured entry→caller return with PC/stack/CPU-mode guards, including callees/interrupts/waits. Dispatcher visits include unexecuted conditional instructions; emulated cycles, not host time. Synthetic observer tests plus29 verifier tests precede two single runs of same Goldenrod snapshot:90neutral,48Down or neutral,60drain. Each24 complete calls, no observer error/reentry/pending; walk six tiles/control stays still.

| Metric,24 calls | Walk | Neutral |
| --- | ---: | ---: |
| Elapsed ARM9 emulated cycles |4126732 |4831709 |
| Dispatcher visits |2352769 |2819978 |
| Cycles/call min–max |102813–493332 |201242–202001 |
| Calls crossing hardware frame |6 |0 |

Lower walking total is not a gain:actions differ, ROM same. Six peaks need synchronous/interrupt attribution; crossing frame does not prove lost update. No dominant city cost or gameplay optimization was established.

## Historical Android acquisition and Mac laboratory

28October acquisition identifies melonDS2.1.4 PROFILING, Android 13/API 33 ARM64,4KiB pages, JIT, Compute6x, threaded renderer, two displays. Private evidence identifies APK/signature/native libraries/ROM/raw/BIOS/preferences/controller/five selected cheats. Preference export excludes cheat DB/SAF grants, so UI checks cover those. Personal ROM differs from canonical1.2.5 IT in six stat bytes; executables/scripts match. Neither proves freeze cause or source/APK correspondence.

Original raw preserved. Derived Goldenrod copy uses native warp/SAVE/cold on Mac, then Android direction/release/video/nativeSAVE/process stop/cold Continue. Same written raw reloaded in fresh Mac interpreter/software/fixedRTC:map/position/counter/field and byte-identical export, valid CRCs, preserved party/boxes/Dex/inventory/Plus. Explicit time/position/RTC/step deltas retained. One derived IT fixture, not all saves or 1.3 acceptance.

| Observation | Result and boundary |
| --- | --- |
| Goldenrod idle |Three≈30s windows, median11.87 process CPU-s, range11.67–11.92;≈39.5% of one core, not total capacity/headroom. |
| Koga room idle |Two valid9.97/10.08 CPU-s; paused2.33. Different scenes, no optimization comparison. |
| SurfaceFlinger |≈60 presentations/s even paused; not guest FPS. Integer16ms bucket gives62.5, not exact framerate. |
| Perfetto |Global FrameTimeline decodes; requested scheduler/ftrace/process-stat payload absent, no process attribution. Missing is not zero CPU. |
| FPS/input |Screenshot60 is not time series; Android ACK is not physical/guest-action latency. |

CPU recomputed from raw PID/starttime/ticks/stderr/quantization; bounds nonstatistical. Two pause/overlap-contaminated runs excluded and retained. Charging/overlay/point frequencies/unready Thermal HAL limit interpretation. More city CPU does not localize bottleneck.14 source hashes stable; FPS/auto-sleep restored; verified device test ROM/raw/traces/video/helpers removed. Preference export private.

AVD ARM64/API 33 recovered after two userdata-space refusals; exact APK/4KiB pages, different GPU/driver/display. UI preference import, SAF regrant, verified BIOS/raw, five cheat definitions compared, not whole private DB. Imported Compute6x fails GLES3.0 shader (`unsupported shader version`, `#version 320 es`), same-process SIGNALED11; selector hidden. Suspected fallback/cast needs authenticated backtrace. Laboratory incompatibility, not game-freeze cause. ftruncate also appears in working profile; JIT preference alone does not prove actual path.

Explicit Software1x completes Continue→Goldenrod→direction/release→nativeSAVE→quit→new-process Continue; raw after exit=postSAVE. Six party/boxes/Dex/native+108 extra slots/Plus/profile preserved; position/three counters advance three steps, other dynamics explained. Preference changes only renderer/scale/layout; controller/layout definitions match, SAF/cheats separate. Host Software1x and physical Compute6x are different work; no performance delta computed.

## City-latency follow-up —3 November 2026

Reported heaviness spans Goldenrod/Radio Tower, Cianwood/sea/islands, Cerulean, Celadon, Saffron, Pewter. Separate guest cadence, input→movement, frame→display. Evidence supports no single cause:sync model loading/banner residue explain entry peaks; NPC cap 5→4 frames at boundaries is not smoother continuous walking; Waterfall/field callbacks need matched attribution. Retail/Plus 1.03/Community share two three-frame Goldenrod gaps. Classic camera reduces polygons15–16%, both remain0.5 logical loops/hardware frame. Near60 surface/global CPU-GPU metrics can repeat guest frames.

Goldenrod exterior has most data; Radio Tower separate. Violet/Azalea/Ecruteak/Mahogany/Olivine transitions partial; Cianwood, Route41/Whirl Islands/reported Kanto cities lack matched benchmarks. Neither current defect nor elimination is established.

Future comparison fixes ROM/raw/route/coordinates/RTC/weather/party/follower/camera/audio/core/APK/JIT/renderer/scale/layout/power/thermal state. Idle/walk/cold-warm entry, randomizedAB order,≥five valid pairs; record map/subtile/input/objects/tasks/scripts/overlays/CPU cycles/loops/polygons/framebuffer hashes. Report host→guest, guest→movement, movement→changed frame, frame→presentation separately with median/p95/p99/duplicates. Improvement requires target metric/same scene/no control regressions. Free RAM/ROM is not latency/CPU evidence.

## Historical sources and identities

Sources below retain the original investigation's provenance; this English migration makes no new online-verification claim. REA was consulted for method only:its local registration/runtime/engine were not ready and no REA decompilation ran. Actual evidence used available ARM tools/disassembly. Missing original pre-freeze device state remains a limit, despite reproduced Mew and maintainer confirmation.

### Task 4 integrated save-feedback candidate

| Language | SHA-256 |
| --- | --- |
| EN | `9c577ae4f4d51fbbedd19bee7f65610ad4c93c04815923161752c0b8549b1031` |
| IT | `46422b8c3e97eec7c7eb7718ec1c6c6b7ffc49e79b1783435d04b89ae506f609` |

### Training and Mew repaired candidate

| Language | SHA-256 |
| --- | --- |
| EN | `6bd84a67db6478c390d949a8e08358fcc4fb4c64626cee33d9fc7b85c9cfc17b` |
| IT | `83f8129d4037254eeae357ee647b3590fdc4f2e28df1099cf8f47529aefe9d24` |

- [Historical source 1](https://github.com/pret/pokeheartgold/blob/0985e8718df4f25e64d6507d89c0c97c0d288981/src/touch_save_app.c#L460)
- [Historical source 2](https://gbatemp.net/threads/pokemon-sacred-gold-storm-silver.327567/)
- [Historical source 3](https://gbatemp.net/threads/pokemon-sacred-gold-storm-silver.327567/page-114)
- [Historical source 4](https://github.com/Umberto-DEV/sacred-gold-plus/issues)
- [Historical source 5](https://github.com/rafaelvcaetano/melonDS-android)
- [Historical source 6](https://perfetto.dev/docs/getting-started/system-tracing)
- [Historical source 7](https://perfetto.dev/docs/analysis/stdlib-docs)
- [Historical source 8](https://github.com/google/perfetto/blob/main/docs/data-sources/frametimeline.md)
- [Historical source 9](https://github.com/pret/pokeheartgold/tree/0985e8718df4f25e64d6507d89c0c97c0d288981)
- [Historical source 10](https://github.com/DS-Homebrew/nds-bootstrap/issues/1610)
- [Historical source 11](https://www.reddit.com/r/PokemonHGSS/comments/1k79vaq)

### Additional historical artifact fingerprints

These are historical input/output/evidence identities, not extra accepted current ROMs. Their component/scenario boundaries remain those described above.

| Fingerprint |
| --- |
| `f18ccb0a3899b993edc53575bef185093f08c7653227c0a73ccaab5cd583d106` |
| `5dc3d7db53c98c9ba5c85b0707eac0c81420b86c1da2ec447fd580ef27f926be` |

### Task1 exact candidates before Mew repair

| Language | SHA-256 |
| --- | --- |
| EN | `f18ccb0a3899b993edc53575bef185093f08c7653227c0a73ccaab5cd583d106` |
| IT | `5dc3d7db53c98c9ba5c85b0707eac0c81420b86c1da2ec447fd580ef27f926be` |
