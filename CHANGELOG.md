# What changed

## 1.3.1

The 6 November battle-freeze successors are EN
`50ba570f97655cecc7b11bed06eb7f683283b191c1c21f02e49ad55f90fc7665`
and IT
`c63cf9e993cbee9c38949baf9444dda3e365bddb15840aaa08905d9b02afbedb`.
Both formal builds reproduce the independently measured trials byte for byte.
A stale loop backedge in the Fairy AI hook entered the second half of a Thumb
BL, branched into resident data and caused an ARM9 data abort while returning
to the battle menu. The fix changes one decoded overlay byte and preserves
save layout, resident payload and gameplay data. Full native-loop tests cover
ten cases per language; all twenty fail before the fix and pass afterwards.
A no-JIT melonDS reproduction and a one-byte RAM control establish causality.
See [the diagnosis](source/docs/ai-scoring-1.3.1.md). On the physical Android device,
the exact Italian successor completed copied-save Continue, native SAVE and
cold Continue. A fresh battle passed Weavile, Honchkrow and a Houndoom turn,
then reopened the move menu with JIT and the existing compute renderer enabled.
The canonical Italian ROM was updated in place and its current raw save
loaded normally; the ROM-only replacement preserved that save's checkpoint hash.
Four additional host cycles cover two authentic older fixtures in both
languages, including existing Plus settings and three expanded Bag slots.
These bounded checks do not establish universal compatibility or resolve
the historical Latios freeze. Previous offline package drafts do not
contain this fix and are not current release artifacts.

The global source suite collected 2,988 tests with no failures: 2,627 ran and
361 were explicitly skipped. All 32 distribution tests were rerun after the
final contract update; both player ZIPs passed 100 two-decoder reconstructions.
The four current PDFs contain 42 visually reviewed pages. Historical source
and runtime limitations remain in the linked validation reports.

The following HG-T10 checkpoint is historical.

The current HG-T10 successor candidates are EN
`02cccfbfc49b6addddba90385634ffdfde22b9ff3fbae3d85ae8f5603c5bf0af`
and IT
`35d459e3fcf7cf127d6ff0aec94a5f502accfce390b2455b83fe189a5ca088f4`.
HG-T10's title-dependent legendary-scene mismatch is corrected at component
level and integrated. The confined overlay-2 stage selects Lugia scene assets
on map 244 and preserves the Ho-Oh path, ROM geometry and save layout.
Synthetic EN/IT runtime checks and the Ho-Oh control pass. Ordinary Plus
progression still cannot reach the historical inconsistent state; the full
freeze, battle and capture have not been reproduced. No new physical-device
or native SAVE/cold-restart acceptance is claimed for these hashes.

A private offline player-package draft has been rebuilt from these exact
targets. All 25 routes per language reconstruct with both decoders; the two
39-member ZIPs, four regenerated PDFs, manifests and checksums pass readback.
This is preparation only: screenshots, the exact IT physical-device gate,
release acceptance and explicit publication approval remain open.

The final repository gate for these HG-T10 candidates exits successfully.
Class A runs 2,045 of 2,098 tests with 53 declared skips; Class B runs 579 of
887 with 308 declared skips. All 2,985 tests are collected with zero failures.
Fixture-dependent skips remain recorded as limits and are not claimed as
runtime coverage.

The preceding reproducible portable-only candidates were EN
`5c5611844678d26bdc5677855da3aacbc1dd1700f97afec249b24532f2362f15`
and IT
`c5a45d169e04fd85f17889f201ba7c6fe6f5d4ad43243b6a043a5ab848777f97`.
Their formal receipts activate only portable storage; Summary controls and
configurable rematches remain inert. Both languages reach the native PC from
Party with R in the headless runtime. The exact IT image also completes
Continue→field→Party→portable Box→field in Android melonDS on the Mac. A
separate copied-save run completes native SAVE, process restart, Continue and
field; the post-SAVE and post-cold exports match, while the original fixture
and protected guest files remain unchanged. The physical test device was not
connected and was not updated. Formal runtime acceptance and the complete
release matrix remain pending.

A fresh isolated rebuild reproduces both portable-only candidates byte for
byte. A subsequent Android smoke of the rebuilt IT image again reaches the
field, Party, native portable Box and return path without an in-game SAVE; the
exported TEST raw save remains identical to its input copy. No physical device
was connected or updated.

The full repository gate for that preceding checkpoint exits successfully:
Class A runs 2,042 of
2,095 tests with 53 declared skips; Class B runs 577 of 885 with 308 declared
skips. All 2,980 tests are collected with zero failures. Portable Box coverage
passes 59/59 feature tests, 26/26 package tests, 26/26 ROM tests and the 2/2
exact-IT Android binding checks. Skipped fixture-dependent suites are not
claimed as runtime coverage, and that candidate still awaited the
physical-device update gate.

The preceding private trial candidates from 4 November are EN
`618f0501d1355f5c7ee6d0301847222fd23a3d67701027190424bf28225fb13d`
(152,786,376 bytes) and IT
`171b53b6c47555d54cb82c724569f26e9dfd92f51aa064545dd44b09179d64a0`
(159,029,292 bytes). Both pass a bounded local headless smoke through cold
boot, Continue, field and Party→R→native PC (`PC_RUNNING`) with no crash in
4,332 frames and an unchanged save copy. The IT image remains the version
installed on the device until the current candidate passes its physical gate.
On physical Android, an isolated IT
save copy completes Continue→field→native SAVE→cold restart→Continue at the
same field. The canonical Sacred Gold Plus ROM was then updated in place from
`420ec8b8…f059a` to `171b53b6…d64a0`; the personal raw save, `.ml0`, cheat
configuration and emulator association remain unchanged, and the installed
ROM cold-boots to the field without another SAVE. A verified rollback is
retained and temporary physical files were removed. Two inert cache records
without backing files remain by fail-closed melonDS policy and are not
installed ROMs. This is not player-package or release acceptance: EN has no
physical run, not every feature was exercised, and nothing was published.

The inherited GS Cup special-list/League-guard collision is now repaired in
the source pipeline, after the active private trials. Exact EN/IT script bytes
show that member 4 left map-temporary `x4005=1` after listing any eligible
legendary, while member 819 treats `x4005>=1` as the guard's already-moved
latch. A same-size member-4 repair routes the list's single teardown through
an unreachable block that clears only `x4005` before returning to the original
menu. The guard, other rulesets, entry/movement geometry, NARC size and save
layout stay unchanged. The public component test reproduces the inherited
failure and covers all nine species, omission, empty list, map reset, mutants
and bilingual producer replay. Natural IT UI navigation remains tool-limited;
no active trial, SAVE/cold or device claim includes this repair yet.

The inherited Route 43/44 invisible-grass permissions are now repaired in the
source pipeline, after the active private trials. Exact EN/IT inputs bind
matrix 0 and lands 87/102 to the recovered landmarks: six visually edge-only
cells used tall-grass permission `0x0002`. The registered stage changes only
those six words to ordinary ground `0x0400`; model, collision, matrix, NARC and
ROM geometry, every unrelated tile and the save layout remain unchanged.
Static visual/permission controls, byte confinement, mutants and targeted
composition/replay pass. No rendered encounter, follower effect, SAVE/cold or
device claim is made. Route 28 and Safari remain untouched because their
historical coordinates are not unambiguous.

The inherited Waterfall descent-facing bug is now repaired in the source
pipeline, after the active private trials. Exact EN/IT bytes reproduce the
retail mismatch: a blocked lateral turn followed by Down starts the Southbound
task while leaving the avatar facing laterally; Down-only is already South.
The registered stage changes the single successful call in overlay 1 to a
20-byte resident wrapper which sets South before starting the original task.
Failed directions and the separate script/menu ascent path are untouched.
Ordering, 8-byte stack alignment at both calls, ABI, byte confinement, mutants
and bilingual replay pass. Natural Surf rendering, SAVE/cold and device
acceptance remain pending.

The inherited follower menu-jump bug is now repaired in the source pipeline,
after the active private trials. The earlier bounded trial used one Down input
and observed ordinary follower command 9, so it did not exercise the historical
trigger. With the required second Down, exact EN/IT runtime reaches follower
command 21/step 1 and each Party-page return used to add `0x8000` again to the
retained vertical facing vector. The registered stage follows Waterfall and
changes 28 logical bytes only inside the 92-byte overlay-1 height helper: while
movement is paused it returns zero instead of reapplying the phase-table height;
the complete unpaused mode/phase/frame/table path is preserved. Exact RED/GREEN
0/1/2/3 returns, reset, stationary control, Thumb semantics/ABI, hostile
mutants, bilingual replay and an EN runtime composition after Waterfall pass on
temporary ROM/save copies. Natural saves, other submenus and environments,
SAVE/cold and device acceptance remain pending.

The inherited Pokégear pan/zoom marker-culling bug is now repaired at
source/component level. Overlay 101 ignored signed X, so far-off markers could
wrap through OAM and reappear. Its three callers now enter an in-place 36-byte
trampoline to the registered ARM9 thunk `sgp.pokegear_autocull`; the canonical
stream is 53,564 bytes and is padded to the unchanged 53,576-byte slot. Exact
EN/IT candidates pass signed X `-7..263`, Y `0..199`, `autoCull=0`, ABI,
reserve-collision and full-composition gates. Rendered pan→zoom→pan, SAVE/cold
and device acceptance remain pending.

The inherited Kate side-interaction bug on Route 34 is now repaired at
source/component level. Before her battle, talking from the side ran
`FacePlayer`, displayed the post-battle apology and ended without a fight; the
later vertical trigger could therefore start the battle with the wrong facing.
The confined script replacement now dispatches the before-sisters, pre-battle,
pending-reward and completed states to their existing paths; its even six-byte
growth preserves movement alignment. Exact EN/IT members,
vertical-path negative control, confinement and replay pass; rendered movement,
follower overlap, SAVE/cold and device acceptance remain pending.

The inherited poison-survival follower-jump bug is now repaired at
source/component and bounded-runtime level. The survival standard used to run
`ScrCmd_609` immediately before `LockAll`; the forced reset cleared the active
movement flag without clearing the jump Y vector, so `LockAll` skipped its
native wait. One standard-script entry word now starts two bytes later at the
existing `LockAll`, without changing script instructions, archive geometry,
executables or save data. Exact EN/IT contracts, hostile inputs, archive replay
and temporary-candidate runtime positives pass; off-cadence, non-poisoned and
HP4 controls are unchanged. Natural saves, other ledges/resets, SAVE/cold and
device acceptance remain pending.

The inherited custom-rules Soul Dew bug is now repaired at source/component
level. Rule 13 returned the complete `totalLevel` halfword, so `0x8032` did
not match the six consumers' exact `0x8000` comparison. An eight-byte getter
hook and 24-byte resident thunk now return only bit 15 for rule 13 and preserve
rules 0–12 and invalid IDs. Exact EN/IT ARM replay, reserve ownership, canary,
confinement and the complete legacy composition pass; menu/link gameplay,
SAVE/cold and device acceptance remain pending.

The malformed Wonder Card decoration write is now repaired at source/component
level. The original EN/IT tag-6 path accepted seal ID 81 and incremented the
first byte beyond its 80-byte inventory; `0xFFFF` reached `SealCase+65822`.
The successor validates seals 1–80, fashion 0–99 and backgrounds 0–17 in
check/give and makes the affected writers fail closed when called directly.
Exact EN/IT ARM replay, registered resident ownership, canary, confinement and
legacy composition pass. An artificial invalid give may still leave the retail
queue marked received, but cannot mutate a decoration object or write OOB.
Full card delivery, persistence, ACE on Sacred Gold Plus, SAVE/cold and device
acceptance remain untested.

The inherited Victory Road Fly-marker highlight bug is now repaired at
source/component level. From Johto the selection path passed the displayed-name
map ID into the regional gate; at `(28,7)` it was classified as Kanto even
though the destination is Route 26. A confined overlay-101 gate admits only
the two shared-border coordinates `(28,6..7)` and preserves the displayed
Victory Road name, Route 26 warp, flags, ROM geometry and save layout. The real
overlay-100/101 Thumb routines, EN/IT candidates, regional negative controls,
composition and retained diagnostic postimages pass. A naturally unlocked Fly
menu capture, SAVE/cold and device acceptance remain pending.

The inherited Giratina PC form-stat mismatch is now repaired at
source/component level. PC item changes used the boxed sub-record even for a
party Pokémon, updating form and ability without recalculating cached party
stats. A confined overlay-14 exit hook now calls the existing non-forcing party
reconciliation. EN/IT, both Griseous Orb directions, mixed parties, no-change
exit and cleanup pass. Natural UI, raw SAVE/cold and device acceptance remain.

The inherited Spit Up sprite drift is now repaired at source/component level.
The real task ended at X+2 while its cleanup restored only Y and scale. The
canonical in-place overlay-7 BLZ successor now removes that exact residual;
EN/IT, four starting coordinates, live subtract-one/subtract-three mutants and
the full bilingual composition/replay pass. Rendered battle, SAVE/cold and
device acceptance remain pending.

The inherited Strength horizontal sprite drift is now repaired at
source/component level. Its real four-tick shake ends at X+2 after ten updates,
and the cleanup restores scale and Y but not X. The new stage changes only the
qualified frame count from 10 to 8 in member 70, after Helping Hand; native
8/9/10/11-frame controls, exact EN/IT application, confinement and replay pass
in 119 focused tests; the full bilingual composition/replay also passes.
Rendered battle, SAVE/cold and device acceptance remain pending.

The inherited Helping Hand sprite drift is now repaired at source/component
level. The existing one-frame delay moves inside the two-iteration loop, so
the real HGSS shake launches move from ticks 0/7/16 with bases 0/-1/-1 to
0/9/18 with bases 0/0/0. The stage changes exactly three bytes in member 270
after Facade and DynamicPunch; exact EN/IT application, native loop/delay/shake
handlers, confined replay and full bilingual composition pass. Rendered battle,
SAVE/cold and device acceptance remain pending.

The inherited DynamicPunch sprite-drift bug is now repaired at
source/component level. HGSS starts the second shake on tick seven while the
first task is temporarily at X=-1, so the new task records a displaced base.
The new stage changes only the qualified Delay from 3 to 4, starting on neutral
tick eight. It runs after the Facade repair in the same animation NARC and
authenticates and preserves Facade's six bytes. Native overlay-7 tasks, exact
EN/IT application, confinement and Facade→DynamicPunch replay pass. Helping
Hand and Spit Up are repaired as separate component-level causes above.
Rendered 1/2/16-use, side/double,
animations-off, SAVE/cold and device acceptance remain pending; no ROM or save
was retained.

Four host-suite defects were also repaired without changing gameplay bytes:
the BagView bench now loads authenticated ARM9 segments instead of inventing a
contiguous 2 MiB image; three native UI processes receive the declared source
path; BLZ canonicality tests use a distinct same-size in-place-safe optimal
stream instead of assuming a spare flag bit; and the post-UI Summary Controls
test pins the intentionally cleared Guide-slot preimage.

The inherited Facade sprite-drift bug is now repaired at source/component
level. HGSS launches six 5+5-frame scale/restore tasks eight frames apart, so
five consecutive pairs overlap. The new stage preserves every task duration
and changes only the five launch delays and synchronized looped-sound interval
from 8 to 10: six physical bytes in battle-animation member 263. Exact EN/IT
V4 application reproduces five overlaps before and zero after; the 2016 4+4
workaround, delay-only and audio-only variants are negative controls. Full
inert/active composition and replay pass in both languages. Rendered animation,
1/2/16 consecutive uses, both sprite sides, animations-off, SAVE/cold restart
and device acceptance remain pending; no ROM or save was retained.

The rematch compiler now gives authenticated Clang a private writable `TMPDIR`.
The scrubbed environment deliberately uses `HOME=/var/empty`; without an
explicit temporary directory both EN and IT full-chain builds failed before
assembly with “unable to make temporary file”. Stub compilation and the full
bilingual composition/replay now pass. This is a build-pipeline defect, not a
gameplay bug in a published ROM.

The inherited Battle Tower opponent-wrap bug is now repaired at
source/component level. HGSS preserves completed rounds as 16 bits but narrowed
them to eight bits in both opponent-generation branches: round 256, after 1792
wins, became bracket zero; later wrapped brackets could also replay Palmer and
the cycle repeated at round 512. Four confined halfwords now pass the full
round to the already-correct selector, without changing saves, trainer tables
or the RNG routine; the corrected trainer pool may consume a different number
of draws. Ten authenticated EN/IT Plus images pass 18 scenarios each and 360
native executions: 110 original divergences, zero after repair, deterministic
report `c0ec4f35…bb94f`. Direct EN/IT V4 composition after the Lottery stage,
receipts, mutants and registry tests pass. A natural Plus streak beyond 1792,
rendered rewards, a real link peer, SAVE/cold restart and device acceptance
remain pending; no ROM or save was retained.

The inherited Transform level-up glitch is now repaired at source/component
level. The retail reload routine replaced all five copied combat stats with
the original species' newly calculated values before checking Transform,
leaving copied form and moves attached to the wrong stats. An exact 340-byte
source-owned replacement preserves only those five stats while still updating
level, friendship, HP/max HP and the ordinary non-Transform/Mimic paths. Eight
authenticated EN/IT images pass 128 original and 128 fixed native executions;
the red and green reports are deterministic. Exact compiler, preimage, literal
pool, BLZ, FAT/y9 and UI-seed checks pass, as do real V4 EN/IT installation and
36 targeted EN/IT replay, peel and forgery tests. Natural level-up with and
without move learning, switch/end-battle scope, doubles/link, SAVE/cold restart
and device acceptance remain pending; no ROM or save was retained.

The inherited Pressure switch glitch is now repaired at source/component
level. Counter, Mirror Coat, Magic Coat, Snatch and the independently verified
Metal Burst caller could apply the late Pressure PP debit only to the battle
copy; an immediate manual switch then reloaded the older party PP. Five pinned
battle-script members now invoke the existing no-op status update to perform
the missing party synchronization only on successful paths. Eight authenticated
EN/IT images pass 520 helper/reload/sync executions plus 16 Metal Burst caller
controls in two deterministic runs. Natural battles, doubles/link, SAVE/cold
restart and device acceptance remain pending; no ROM or save was retained.

An isolated level-150 development contract now replaces the obsolete New
Game/level-101 proposal. It models a permanent unlock when a persisted,
non-egg owned Pokémon is observed at level 100 or above, and deterministically
extends the eight pinned growth members from 100 to 150 without changing any
original byte. Exhaustive host tests and both real EN/IT V4 preimages pass.
This is deliberately **not installed in the ROM**: EXP, Party/Box/Day Care,
Rare Candy, learnsets, stats, enemy scaling, save observers and UI still need
one coherent integration before gameplay activation.

The inherited Bag compact-view setter now honors the caller's display
position. The single-pocket Berries path passed pocket ID 4 at compact
position 0, but retail indexed entry 4 and left entry 0 empty; Items and the
normal eight-pocket view masked the defect. The source repair uses position
for the stride while retaining the pocket ID, and re-encodes the adjacent flag
setter plus its sole callsite inside 36 declared ARM9 bytes. EN/IT readback,
twelve modeled sequences and mutation checks pass without changing ROM
geometry, reserve memory, Bag ABI or save layout. Played gardening, save/cold
restart and device acceptance remain pending.

The persisted Lottery Number setter now writes its upper half to the intended
high variable instead of overwriting the low variable a second time. The
authenticated EN/IT candidates reproduce the stale-high/corrupted-low state,
including the real two-RNG daily roll path. The repair changes one Thumb
literal-load immediate, reusing the adjacent getter's high-variable literal;
one physical byte differs inside a declared two-byte span, with no reserve,
ROM geometry or save-layout change. Twelve before/after and refusal sequences
pass per language. Natural day rollover, prize lookup, native SAVE/cold restart
and device acceptance remain pending.

The current level-consumer map also identifies four pre-installation hazards:
the persistent met-level and two UI paths use seven-bit levels, Honey Gather
would index beyond its ten-row table above 100, Pokéwalker owns a separate EXP
path, and the current battle/Day Care clamp can discard same-award overflow
before the unlock commits. These are recorded blockers for the future feature,
not active cap-100 ROM bugs, and no speculative ROM patch is applied.

The Route 47 Safari follow-up now reproduces and repairs the source-bound
component defect SG-01a. On the authenticated current EN/IT candidates the
Mira partner-heal path closes its message before leaving the field; the Buck,
Cheryl and Marley paths left and restored the field before closing the old
window. The repair moves each of those three `CloseMsg` instructions directly
after its `NPCMsg`, preserving the script length, entry points and every other
byte. The archive producer is bound to the exact member-260 preimage and its
independent checker rejects reapplication or foreign bytes. The combined
SG-01a/SG-02 bank passes its focused tests and the full EN/IT archive
composition/replay; the latter ran in 310.378 seconds without retaining a ROM.

A separate source-bound branch defect, SG-01b, is now composed by the same
member-260 producer. After trainer 107, the loss `GoToIf` targeted `0x6C4`,
whose control-flow graph reaches neither `WhiteOut` nor `ReleaseAll`; all four
healthy partner-loss branches target the unique `WhiteOut` at `0x7A4`. The
same-size repair retargets only that displacement. Exact EN/IT RED/GREEN,
hostile mutants, archive geometry/replay and the independent checker pass; all
SG-01a `CloseMsg` bytes, the win path and the other loss branches stay equal.
No save format or save bytes are changed. Played loss, native SAVE/cold restart
and device acceptance remain pending. This does not yet establish that the
reported runtime blackout, stuck audio or black menus are fixed. That broader
SG-01 report still needs an authenticated pre-battle raw-save copy, turbo and
menu controls, gameplay traces, native SAVE/cold restart and hardware coverage.

The distinct SG-02 Route 47 position bug is now source-bound and repaired. The
surviving 2012 screenshot shows the player below the bridge while the first
partner battle starts above. The authenticated native coordinate dispatcher
checks X/Z and state but ignores player height; the custom Mira trigger can
therefore fire from the lower level in the same tile column. A global engine
change would be unsafe because all 217 current coordinate records carry zero
height. Instead, exported script 7 points to a 23-byte appended wrapper that
reads `GetPlayerXYZ`, reaches the original entry only at bridge Y=0 and ends
before BGM, lock or movement effects at other heights. Four hypotheses and
twelve sequences cover the dead 0×0 record, the pre-fix behavior, fixed path
and boundary/state controls. Natural raw-save gameplay, SAVE/cold and hardware
remain pending.

Four stale test-harness expectations exposed by the latest global run are also
repaired: its synthetic autoload image is structurally valid again, the
mechanics chain includes `traded-egg` and `bag-foreign`, the UI write census
accounts for delegated event-flag writes, and the gifts test matches the
specific metadata-hash refusal. The affected focused groups pass 212/212.
These are harness/toolchain corrections, not additional ROM fixes; the entire
global runner has not been rerun and is not claimed green.

The current Settings/Guide audit passes 343 Class A and 38 targeted native
EN/IT tests. No naturally reachable crash, heap/VRAM leak or incomplete
rollback was found. A follow-up corrected the benchmark identity: current
sources at production configuration 64/8/240 reproduce the timed 64,728-byte
module exactly (`62ac98c1…2a8239`), while 64,712 bytes (`b036cbee…bf2cb62`)
is the reduced 4/8/240 bench configuration, not a different successor. The
84/99-frame result therefore remains module-bound evidence; acceptance of a
later composed ROM and the target device still requires an exact AB/BA run.

The maintained Settings, Guide and persistent-UI benches now add the project
`source/` directory before importing `sgp12`. Their official per-feature
invocations previously produced false import failures despite valid compiled
tests. This is test-harness repair only and changes no ROM or save behavior.

Plus-option persistence bookkeeping now handles failed mirror writes. The
runtime no longer marks a record valid when neither copy reached backup, and
records degraded one-copy redundancy. Cold load now selects the newest valid
generation, so a successful mirror B is not hidden by a valid but stale mirror
A. The save layout and vanilla save result do not change. A later exact-payload bank now covers
copies of expanded-Bag EN/IT raw saves with 0/2, A-only, B-only and 2/2 writes.
All eight cases cold-load the expected generation and settings; the originals
and every byte outside the two 32-byte Plus records remain identical. This is
followed by an IT in-game SAVE/cold restart on a physical-device copy: both
`SGP2` mirrors are valid. A loopback GDB fault injection at the real
`WriteBackup` then repeats 0/2 and 1/2 on temporary copies without patching the
ROM or emulator. Runtime status, export/stop/readback and cold load all match
the expected failed/partial states in two identical runs. A real storage-media
failure remains a separate hardware limit. The same follow-up corrected a
harness error: HGSS's exact CRC kernel uses normal CCITT `0x1021`, whereas the
old stub had reused the reflected cartridge-header `0x8408` algorithm.

The expanded-Bag private-copy constructor now handles allocator failure. The
historical implementation cleared the returned pointer unconditionally and
wrote through address zero when allocation returned NULL. The 1.3.1 successor
fits the guard inside the same 28-byte function, keeps every entry point and
the save layout unchanged, returns NULL on failure, and still clears all 2,380
bytes on success. Exact EN/IT in-memory composition and real Thumb execution
pass; gameplay heap-pressure frequency, retained-candidate save/cold and device
acceptance remain pending.

The portable Box return path now handles a second allocation failure that the
previous probe could not guarantee away. The retail party-launch wrapper
dereferenced the result of `PartyMenu_CreateArgs` before checking it; the Plus
runtime now calls the pinned constructor directly, checks for NULL, reproduces
the same field/slot initialization and launches through its guarded owner
wrapper. Failure returns to the field without a NULL access. The smaller
2,952-byte compartment passes ARM EN/IT, installer, ROM and real-UI composition
tests. The currently installed private ROM still contains the preceding
3,020-byte payload, so this fix is not yet installed there. A retained successor
candidate, heap-pressure gameplay and device acceptance remain pending.

Four inherited evolution parameters are repaired at source/component level.
Mantyke now checks for Remoraid rather than Voltorb; Feebas requires Beauty
170; female Burmy requires level 20; female Combee requires level 21. The
single archive producer changes only those four parameter halfwords and feeds
the same repaired records to the in-game Guide. Exact EN/IT in-memory UI
compositions and independent archive replay pass. Natural evolutions,
Continue/SAVE/cold restart and device acceptance remain open.

Kurt's completed Apricorn Ball batch is no longer cleared when the Bag cannot
accept it. The inherited script ignored `HasSpaceForItem`, attempted the give,
then cleared the batch unconditionally. The guarded member now follows its
existing Bag-full message and keeps the batch pending; 950+50 and 949+50 model
paths pass in both languages, along with relocation and mutation checks. The
dialogue, SAVE/cold restart and device acceptance remain open.

Pryce's TM07 reward loss at the Plus TM cap (HG-F23) is now reproduced and
repaired at source level. At 99 copies the permissive Bag path accepted the
request, inserted zero items and later let the script mark the reward as
received. The repaired member queries the real quantity before delivery,
keeps the reward pending at 99 and retries it on later conversations; 98→99
sets the once flag and subsequent talks do not duplicate it. Both EN/IT paths,
relocation and mutation controls pass. Played dialogue, save/cold restart and
device acceptance remain open; already-affected saves cannot be identified
safely from successful deliveries.

The Plus damage chart had two transposed Ghost matchups (SG-DM02): Ghost was
half-effective against Dragon and neutral against Dark. Six historical/current
EN/IT images carry the same table, while all other 322 pairs match the modern
type chart. The source pipeline now changes only those two overlay-18
multiplier bytes and composes the repair with the battle-AI stage. Independent
EN/IT readback, full-chart controls and mutation rejection pass; natural
battle, save/cold and device acceptance remain open.

The trainer AI now evaluates Fairy matchups through a dedicated 148-byte
resident helper instead of the retail sparse chart. Only Fairy rows/columns are
handled by the helper; every other pair delegates to the native consumer,
preserving Scrappy, Gravity, Iron Ball and the existing immunity fix. The two
overlay-12 seams are now composed with four additional type/battle-state repairs.
Conversion2's 64-byte helper enumerates the 325 selectable modern rows instead
of the 112-row retail table, and the Iron Ball/Gravity grounding helper reads
defender/effect columns from the same modern row indexed by the damage loop.
The charge-move gate now selects Shadow Force's effect 272 instead of the
off-by-one Fire Fang effect 273. Neutral and resisted Fire Fang hits reach both
Wonder Guard consumers; Shadow Force skips them while charging and reaches them
on its damaging turn. Super-effective hits, other charge moves and the other
elemental Fangs retain their behavior. The pre-turn Rage controller now clears
only Rage when another move is selected, instead of retaining Rage and erasing
every other volatile status. This also preserves Transform before the native
PartyMon copy gate, preventing the linked copied-moves manifestation HG-B03;
HG-B03 remains one historical ID but is not counted as a second root fix.
Real ARM execution reproduces the Fairy no-change and Ground→Flying immunity
failures before the repair and the expected results afterwards, while Fire,
Ground→Poison and Fairy→Dragon controls remain unchanged. Rage coverage adds
464 native executions across eight authenticated EN/IT inputs and every
`status2` field; the downstream consumer adds 16 Transform/Mimic controls. The
combined compressed stream grows by 20 bytes; FAT/y9 and the one derived UI y9 digest
are reconciled and independently peeled back to the cold UI. More than 76,000
dynamic cases, 13 ROM-level reproducer tests and full EN/IT compositions pass.
Natural and communication battles, encrypted PartyMon mutation, save/cold and
device acceptance remain pending.

The inherited Pursuit switch-KO bug (HG-B04, commonly exposed as Acid Rain) is
now repaired in the source pipeline. The battle script used to subtract the
fainted battler ID from the global field-condition bitmask instead of restoring
the saved `battlerIdFainted`. The canonical member delta changes exactly two
bytes in `a/0/0/1:153`; archive size, legacy name block and all other 296
members remain unchanged. The native command consumer was exercised twice on
eight authenticated EN/IT Plus images, 20 scenarios per image and 320 total
executions, covering weather, Uproar, Gravity, Fog, Trick Room, combined fields
and battler slots 0/1/3. Component tests, hostile mutations and real EN/IT
composition/replay pass. Rendered battles, Castform/Cherrim loops, link
host/client behavior, save/cold restart and device acceptance remain pending;
no new candidate ROM was produced by this cycle.

The inherited U-turn flinch-item bug (HG-B05) is now repaired in the source
pipeline. The late post-hit consumer used the attacker slot after U-turn had
already replaced its occupant, so it could ignore the outgoing holder's
King's Rock/Razor Fang or use the incoming holder's item spuriously. The pivot
script now snapshots the outgoing effective hold effect and modifier before
replacement; two 68-byte Thumb wrappers consume and clear that snapshot at the
only two late getters, while the ordinary no-snapshot path still delegates to
the retail getters. All later failure, damage, RNG, move and target-HP gates
remain byte-identical. Two repeatable runs cover eight authenticated EN/IT
Plus images, 160 native executions, both failure directions and negative
controls. TDD, hostile mutations and full EN/IT composition/replay pass.
Natural and double/link battles on matching builds, save/cold restart and
device acceptance remain pending. Mixed patched/unpatched link builds are not
supported because their RNG call counts may differ; no candidate ROM was
retained by this cycle.

The inherited invisible-status-icon bug (HG-B06) is now repaired in the source
pipeline. Battle script member `a/0/0/1:221` cleared the healthbar icon before
distinguishing the cured condition. Own Tempo and Oblivious therefore removed
only confusion or infatuation while hiding an unrelated persistent sleep,
poison, burn, freeze or paralysis icon. The persistent status itself was never
cured. The new producer dispatches those two volatile cases before the visual
clear and gives each a copy of the original 30-frame wait; messages, timing
and persistent cures 0–4 retain their behavior. Eight authenticated EN/IT Plus
images, 320 exact-script executions and 200 native command-consumer executions
pass, including six persistent statuses, no-status controls and hostile
mutations. Full EN/IT composition/replay merges HG-B04, HG-B05 and HG-B06 in
one battle archive. Rendered/natural battles, switch-out restoration,
double/link, save/cold restart and device acceptance remain pending; no ROM or
save was retained.

The expanded-Bag save coordinator now prevents SG-BAG-FOREIGN and
SG-BAG-WRITE-01. If an inactive bank contains unknown bytes, neither extension
copy verifies, or flash cannot be read while any expanded slot is live, the
recoverable save failure is returned before the native generation advances.
Empty expanded storage still permits the native save; a partial result with one
verified copy also remains committable. Bag ABI and save layout remain
unchanged. The current ARM composition passes 14/14 and its identity/ABI suite
passes 5/5 with direct EN/IT application; raw-save cold restart, full
BuilderChain replay and device acceptance remain open.

The first source integration of that guard exposed SG-PIPE-BAG-ABI-01: rebuilding
the whole Training compartment shifted 12 of the 16 public entries consumed by
ARM9/overlay hooks and Shiny/UI descriptors. A red Shiny transaction and a
decoded consumer matrix reproduced the mismatch. The final composition keeps
the historical Training bytes and every public entry fixed, replaces only the
first eight bytes of `training_save`, and appends a 184-byte Thumb guard while
leaving 172 bytes free. The current identity tests preserve all 16 consumers
and the Shiny transaction and apply directly to both EN/IT inputs. The full
BuilderChain replay still needs the unavailable private UI assets. This was a
development-pipeline regression, not a defect in a published ROM.

Traded-egg hatch palettes now classify shininess with the final hatcher OT and
the egg PID without moving the retail memo update. The overlay-local helper
changes only the palette bit. EN/IT replay covers overlay 95, FAT/y9 and the
shared Module96 CRC; real link trade, rendered animation and device acceptance
remain open.

The Expert trainer-AI Water Spout/Eruption HP check (AI-WEB-01) is now
reproduced and repaired at source level. Exact EN/IT overlay-10 execution
showed that both 50/51 and 70/71 score thresholds followed the target's HP and
ignored the move user's HP. The archive repair changes only the two battler
tokens in member 0 of `a/0/9/9`; the same native matrix then follows the user.
Full Expert-path Hydro Pump/Surf controls, an observed move choice, save/cold
restart and device acceptance remain open.

The Expert trainer-AI Facade status check (AI-WEB-03) is now reproduced and
repaired at source level. Exact EN/IT overlay-10 execution showed that the
bonus followed the target's poison, bad poison, burn or paralysis instead of
the move user's. One authenticated battler token in member 0 of `a/0/9/9`
changes from target to user; sleep and freeze remain excluded. The Plus
Falkner rematch supplies a reachable Swellow/Flame Orb/Facade case. A natural
Expert dispatch, observed move choice, save/cold restart and device acceptance
remain open.

The unreachable Expert trainer-AI Thunder branch (AI-WEB-04) is now
reproduced and repaired at source level. The exact EN/IT dispatch listed the
SolarBeam effect twice, so Thunder never reached its intact weather/RNG
routine. One authenticated effect word changes from 151 to 152. Native tests
then observe the rain bonus, the sun penalty at RNG 50, the 49/50 boundary,
and unchanged SolarBeam/Thunderbolt controls. Seven candidate trainers make
the Expert path reachable. Resistant/immune effectiveness, a natural move
choice, save/cold restart and device acceptance remain open.

The Basic trainer-AI Metal Burst ordering defect (AI-WEB-02) is now
reproduced and repaired at source level. The exact EN/IT script used two Stall
and two item-ID shortcuts before its complete speed-order command; item 107 is
Shiny Stone, and mixed Stall/Lagging Tail/Full Incense cases produced the
wrong score. Four relative-jump fields are changed to zero without changing
the opcodes or script layout, so all cases reach the existing `CheckSortSpeed`.
The real overlay-12 comparator passes 30 before/after cases per language,
including ties/RNG, Trick Room, Quick Claw and Custap. A natural battle and
move choice, full-battle priority, save/cold restart and device acceptance
remain open.

The inherited trainer alternate-form stat bug (HG-B16) is now repaired at
source/component level. The shared post-form ARM9 helper refreshes the
form-specific ability and recalculates stats
before its existing friendship check, covering all four trainer formats in the
same 50-byte extent without changing archives, overlays or save data. Live
melonDS component runs pass natural T0/T3, synthetic T1/T2 and a form-zero
negative control. The separate SG-TR04 matrix now also passes Horton Rotom Fan,
both ability slots across all Wormadam forms, PID/checksum replay and the
Frustration friendship rule in EN/IT. Eleven trainer tests, 94 mechanics/build
tests and both complete EN/IT chains pass. A natural battle/turn-order test,
save/cold and device acceptance remain open.

The full 1.3.1 composer no longer rebuilds the prepared rematches module from
archives already changed by earlier legacy producers. That replay incorrectly
expected the V4 fishing preimage in `a/0/5/6` and blocked the complete chain.
Writer, reader, peel and activation now consume the same immutable module delta
freshly derived from the exact V4 and bound to the UI receipt; activation can
still change only its one declared byte. Exact inert EN/IT chains through
`rematches` and independent replay pass. This is a builder integration fix,
not a newly claimed gameplay repair.

The inherited Pokéathlon friendship-summary wrap is now reproduced and fixed
at source level. Overlay 98 already returns the full 0–493 count, but overlay
99 stored and loaded it as one byte. The confined `pokeathlon` stage moves the
transient field to aligned padding and uses 16-bit operations: 38 native cases
show six divergences before and none after, with adjacent fields and the direct
counter path unchanged. Only four logical bytes in overlay 99 change; save
layout, FAT and y9 do not. Rendered room, Continue/SAVE/cold and device
acceptance remain open, and no successor ROM has been retained.

SG-TR02 is now confirmed and repaired at source level. Wade's selector uses
trainer records `461` then `460`, but the inherited Plus data assigned those
records level 52 then 46. The confined `trainer-fixes` stage swaps only those
two equal-sized party members, restoring the effective 46→52→68 progression
without changing the selector, species, moves, archive geometry or any other
trainer. Six focused tests and in-memory application to both composed EN/IT
candidates pass; no successor ROM has been retained and played rematches,
save/cold restart and device acceptance remain open. SG-TR03 Jose is separately
confirmed in the static data. A level-50 duo is an internally coherent design,
but the exact difficulty and move policy are not recoverable; no replacement
roster is invented without an authoritative source or explicit balance choice.

The maintainer-reported Vermilion totem/Latios white-screen freeze is now
mapped as SG-LATIOS but remains unisolated. The event is map 54, script 776
entry 16, event member 51 and a level-40 ordinary static WildBattle. Event,
movement and native battle-launch bytes are unchanged from Plus 1.04 through
the current candidate, while the same 1.2.5 family has both a reported freeze
and a successful traced run. Static EN/IT contract checks pass but do not
execute the battle engine. The repeated runtime matrix is now complete: ten
cold boots on 1.2.5 IT and ten on the active 1.3.1 IT candidate, with input
spacing varied from 112 to 130 frames, all reach script offset 1704 and battle
ownership with movement zero, no assertion and unchanged ROM/save inputs. This
is a bounded non-reproduction on one fixture and one deterministic runtime, not
a universal refutation; ARM7/FIFO audio, the original failing save/configuration
and an independent emulator/device are not covered. The stop criterion is met
for this exact bench, so no speculative Mew-style patch is made and another run
requires one of those new inputs.

The expanded historical search adds four qualified retail candidates without
claiming fixes. Three are trainer-switch AI defects still present byte-for-byte
in both current languages: dual-type immunity can remain marked super
effective, Arena Trap can suppress legal NPC switches, and the absorb-switch
branch omits Dry Skin and Motor Drive. The traded-egg hatch animation also
checks shininess before assigning the hatching player's OT; a four-case static
reproducer authenticates the unchanged hatch overlay across six Plus images.
The first AI defect is now reproduced and repaired at source level. The real
helper and post-KO consumer choose the false Thunderbolt reserve before the
one-halfword correction and the Ice Beam reserve after it; reversed order and
single-immunity controls stay unchanged across six inputs. A retained successor
ROM, rendered battle, save cycle, link trade and hatch animation remain open.
Separate Sacred Gold reports for Radio Tower GB Sounds, fleeing Fuchsia
Cloyster, zero Lyra/Ethan payout, Route 43 dialogue and the Ruins of Alph are
recorded as candidates rather than release claims.

The Arena Trap switch-gate candidate is now reproduced and repaired at source
level. The old trainer-AI routine duplicated only part of the normal trapping
contract, so Flying, Levitate, Magnet Rise and Shed Shell could not permit a
legal switch. A guarded 16-byte prefix now calls the engine's existing
`BattlerCanSwitch` routine and bypasses the duplicate checks. Native execution
over six EN/IT inputs covers 96 cases and 42 expected divergences, with grounded
targets, Iron Ball, Gravity, Shadow Tag, Magnet Pull, binding and non-trapping
abilities as controls. No successor ROM has been retained; a played battle,
save/cold cycle and device acceptance remain open.

The absorb-switch candidate is also reproduced and repaired at source level.
The retail routine omitted Dry Skin and Motor Drive both when checking the
active battler and when scanning reserves. Two guarded call sites now share a
20-byte helper placed after the overlay static-initializer table. Native
execution over six EN/IT inputs covers 96 cases and 24 pre-fix divergences;
legacy absorbers, RNG order, fainted/egg exclusions and wrong-type controls are
unchanged. No successor ROM has been retained; a played battle, save/cold
cycle and device acceptance remain open.

The SG-TR01 research cycle refutes the reported empty moveset for Gentleman
Alfred's final rematch on every authenticated available Plus image. Ten EN/IT
images from Plus 1.04 through the current candidate contain trainer 674 as a
three-member custom-moves record with twelve nonzero move IDs, and overlay 26
selects that exact record through `401/401/672/673/674/0`. No ROM change is
made. An authenticated 1.05/Plus 1.03 image and a played battle remain outside
the evidence; the local native bench currently stops in Unicorn with SIGILL.

The HG-B12 cycle confirmed a retail trainer-AI bug still present in every
authenticated Plus image: Basic AI checked Levitate twice and failed to score
Water moves into Dry Skin as immune. A new confined `ai-immunities` stage now
changes ability 26 to 87 in both overlay 10 and archive `a/0/9/9`. The 104-case
reproducer, negative controls, deterministic EN/IT application, dual BLZ
decode and independent NARC readback pass. No successor ROM has been retained
or installed yet; battle observation, save/cold and device acceptance remain
open. The Azurill-to-Marill gender change is now reproduced on the exact EN/IT
V4 ARM9: 14 boundary/control cases execute creation, the friendship evolution
decision, the native evolution commit and both gender getters. It is not a
claimed fix. Ratio, cached-gender and PID-rewrite approaches each violate at
least one existing-Pokémon, identity or vanilla-trade invariant. The 64 PID
low bytes `0x7F..0xBE` prove that an exact-PID Marill cannot remain female on a
vanilla peer. The lossless-update policy therefore preserves existing Pokémon,
PID, save data and vanilla trades. This is closed as a documented retail
`WONT_FIX`, not hidden as a repair or changed through a speculative migration.

The historical HG-F22 report about a follower disappearing when entering
Slowpoke Well on a bicycle was not reproduced on the authenticated EN/IT V4
candidates, so no visibility patch is applied. Eight valid Well runs on save
copies, walking and cycling, show the same brief recall state and a visibly
restored Lapras after the first interior step. Four Union Cave controls preserve
the expected hidden follower while cycling remains active. This is limited
non-reproduction with one fixture and one runtime species, not a universal
refutation of the unspecified Japanese report.

HG-F24 is now reproduced and fixed at component level. With GB Sounds active,
Pokemon Summary restores sound-heap state 4 and evicts the dynamically loaded
GB evolution sequence 1223; the native evolution flow did not start it again.
The confined wrapper preserves the native helper and requests sequence 1011
only when GB Sounds is active, letting the existing dispatcher reload 1223.
Five exact-candidate EN/IT tests, an independent bounded Thumb-1 replay,
confinement and full legacy composition pass. ROM geometry and save layout do
not change. Natural UI/PCM capture, accept/refuse/cancel, SAVE/cold and device
acceptance remain open.

Historical HG-T10 checkpoint before the scene-version successor above:
HG-T10 is not reachable through ordinary Plus progression, but its latent
Ho-Oh object-duplication mechanism is reproduced on EN and IT V4. In the
minimal artificial inconsistent state, the native `ShowPerson` consumer turns
one active ID5 Ho-Oh into two. A local archive owner now guards only Bell Tower
script member 21: hide flag `0x242` permits `ShowPerson 5` only when the object
still needs creation, so replay does not duplicate it. The global consumer and
Lugia member 104 remain byte-identical. This closes the demonstrated component
defect in source, not a second capture or full emulator/device scene. The Lugia
control refutes the earlier NULL lookup hypothesis; the title-coupled scene and
reported freeze are now classified separately. The title mismatch is a
confirmed latent component defect, but a second patch is
`DEFERRED_NO_PATCH / FIXTURE_LIMIT`: the available eight guard tests do not
execute the cinematic helpers, and no qualified full-scene scheduler trace
locates the reported freeze.

The HG-B11 research cycle confirms the retail Heavy Ball bug in US/IT and Plus
1.01--1.04, while Plus 1.1, 1.2.5 and the current EN/IT candidates already
contain the two-halfword correction. Thirteen authenticated images and 96
decoded boundary cases reproduce the transition. Fast Ball (Italian Rapid
Ball) and Quick Ball (Italian Velox Ball) were kept as separate controls and
match their base-Speed and first-turn conditions. This records an inherited
fix; it does not add another ROM patch or claim a played capture.

Two further historical reports are now qualified without a ROM change. Exact
EN/IT data tests find no water behavior on any decoded Dark Cave rock component
(HG-F12), and confirm that Plus makes Nosepass's Head Smash egg move obtainable
through male Glalie at level 42 (HG-D01). Mutant and negative controls are part
of both repeatable tests; neither result is presented as rendered gameplay.

The sealed Daybreak follow-up now has no unreproduced static candidates: 33
findings are fixed at component level and one was already resolved. Builder,
runtime and workbench publication is private, descriptor-bound and no-replace;
RSP, source snapshots and acceptance inputs are bounded; loopback peers and
reviewed evidence hashes are explicit; CSV labels are neutralized. The Android
observer now generates a per-process token, rejects shell UID and exposes one
root-only bootstrap. The private AVD was verified to contain the exact fixed
successor APK rather than the historical vulnerable build, so no reinstall was
needed; full endpoint execution remains a separate runtime-validation limit.
These are toolchain fixes, not additional gameplay fixes or a new ROM candidate.

The source and validation toolchain now rejects malformed ARM9 autoload tables
before ndspy or project readers materialize sections. Extents, ordering, row
shape, initialized sizes, 32-bit bounds and a 256-section ceiling are enforced
through every retained production, verification and reserve path. Synthetic
oversized tables are rejected; the pinned V4 EN candidate still maps its three
autoload rows/four segments without changing its hash. This is tooling
hardening and does not itself change ROM or save bytes.

The ROM-level H1 follow-up reproduced two Plus background interactions that
were incorrectly encoded as hidden items. The installed Dowsing scanner turned
their ordinary script IDs 19 and 14 into out-of-range flags E3F3/E3EE. The
`legacy-events` archive producer now changes only those two event-type
halfwords from 2 to 1, retaining scripts, coordinates, all other event members
and real hidden items. Exact EN/IT preimages, negative controls and a real EN
composition/replay pass. The full IT composition and independent replay now
pass as well, including the unchanged `8006`/type-2 hidden-item control. No new
release ZIP has been produced. Two private diagnostic through-legacy postimages
now authenticate the repair and Continue to the controlled Bugsy overworld in
both languages without changing the copied saves. They are not accepted final
candidates: the available fixture is debugger-assisted and three bounded
ordinary-input routes do not reach Azalea town, so the visual Dowsing trace,
native SAVE/cold cycle and device acceptance remain open.

The ROM-level V-CHATOT campaign confirmed that 24 historical variable IDs
(`612E..6139`, `619E..61A9`) escaped SaveVarsFlags into the saved Chatot sample.
Script writes could corrupt the recording, while recording could reopen or
close coordinate events. HF02 now snapshots each legacy gate once as
zero/open or nonzero/closed and redirects only this finite family to 24
previously unused bits in the existing reserved bitmap. Save layout, IDs,
Pal Pad and Chatot bytes do not change. Twelve reproduction sequences, 12
private native tests and complete EN/IT UI composition/readback pass. Eight
preserved-copy raw-save cycles also pass native SAVE/process-exit/cold Continue
for zero and HF01 reservations under EN/IT, with the bounded full audit and
original hashes intact. Representative gate/recording gameplay and
physical-device acceptance remain open.

The SG-16 Celebi/Giovanni follow-up did not reproduce a ROM defect. Twelve
bounded checks across nine historical EN/IT images refute a stale binding,
missing movement wait, unrestored can-lose battle field, and deterministic
cutscene-task hang. The native cutscene still has unguarded follower-pointer
uses, but the normal route supplies an eligible Celebi, follow-enabled maps and
a healed/restored loss path; no reachable null was shown. A census of 184 valid
unique raw saves found no authentic pre-event fixture, so gameplay validation
remains blocked and no ROM change was made.

The SG-17 Cynthia follow-up refuted the reported Earth Badge requirement rather
than changing the ROM. The real reward branch contains no badge check: EN/IT
messages and the Guide consistently require Champion status, a Sinnoh starter
family member as the first alive Pokémon, and two free party slots for the two
gifts. Twelve controlled sequences cover all nine species, party sizes 1--6,
negative mutants and the 3F9B lifecycle. None of 184 unique raw-save fixtures
provides the complete map/event state for gameplay, so that limitation remains
explicit and no fix is claimed.

The optional stage-0 downloader now keeps a descriptor for the private output
directory, uses unpredictable exclusive no-follow temporary files and publishes
the verified delta and receipt atomically. Previously a prepared symlink on the
predictable partial or receipt name could redirect writes outside the selected
folder. Remote input is also bounded before integrity checks: 64 KiB manifest,
exact pinned delta sizes, oversized `Content-Length` rejection and a shared
30-minute monotonic deadline using one-transport-call `read1` loops. Thirteen
focused security controls and all 59 stage-0 tests pass; no ROM or save was
used by these tooling fixes.

Release packaging now rejects unsafe/colliding member paths before insertion
and output, including Windows device aliases and version-relabel collisions.
Selected reference members are limited to 8 MiB each and 32 MiB total using
bounded STORED/DEFLATED readers. BZIP2/LZMA members are refused before decoding.
All 27 distribution tests and actual EN/IT reference/guide controls pass for
both contracts. No full ROM route package was created by these checks.
The existing RomPatcher fix also closes Git configuration helper execution;
a regression demonstrates the old fsmonitor trigger and its absence now.

Compiler authentication now precedes every reviewed 1.3/1.3.1 native launch.
The shared guard pins the actual Apple CLT executable rather than its dispatcher,
requires root-protected paths without extended ACLs, and uses a restricted
compiler environment. Five reject-before-execution controls, 27 UI tests and
all eight legacy native compilation paths pass locally. Xcode CI toolchain
identity remains unverified, so cross-environment compatibility is still open.
The test runner now reports signal termination distinctly from empty suites,
flushes progress, and includes the 1.3.1 distribution contract tests.
The Portable-after-UI test now expects the independently defined retired-Guide
slot of 3,024 zero bytes, as the production stage already does. EN/IT composition
and readback pass, and a single changed slot byte is still rejected.

The pinned melonDS runtime bench now verifies the complete checkout tree before
patching and again before CMake evaluates it. The previous HEAD-only check could
accept modified or untracked build logic, index-hidden changes, and replacement
refs at the pinned commit. Nine source-only regressions cover clean/idempotent,
dirty, shadow-module, ignored-file, marker-spoof, `skip-worktree` and replace-ref
cases plus shared-hardlink rejection; a real checkout configure passes while an injected CMake sentinel is
rejected without execution. This hardens development evidence only: no ROM or
save bytes change, and a same-account writer racing after the final check remains
a documented local-tool limitation. The verifier runs again whenever the core
target is built; index-only staged content is not consumed or attested.

Release reference ZIPs are now read as one bounded, no-follow authenticated
snapshot. Previously the packager hashed one open file and then reopened its
pathname, allowing a local rename race to substitute unpinned license, Game
Guide or inherited-cheat members. The exact snapshotted bytes are now both
hashed and parsed; symlinks and non-regular files are rejected. Two focused
regressions and all 14 distribution tests pass, including the unchanged real
10.2/24.0 MiB references. Member-name traversal and decompression limits remain
separate open families; no release artifact was rebuilt or published.

RomPatcher.js is now executed only from a private snapshot materialized from
the pinned commit's verified Git objects. The previous one-time HEAD and
tracked-status check still allowed extensionless untracked CommonJS shadows,
index-hidden edits, nested fake checkout paths and post-check replacement. The
packager now verifies commit/tree/blob SHA-1 identities, rejects links and
unsupported entries, disables lazy object fetching, and passes the same
committed snapshot to every Node decoder. Five red/green regressions and all
19 distribution tests pass; the
real pinned checkout materializes 58 files and its modules load under Node.
No real 42/50-route package or release asset was rebuilt in this tooling unit.

GUIDA and SETTINGS retain their appearance while reducing repeated heap/font
checks, loading turns and full cursor redraws. The installed book now owns
native focus correctly, shows GUIDA/GUIDE in uppercase and keeps both displays
black until the shared field fade. Fresh input is accepted once the new frame
is visible. Repeated local comparisons now measure SETTINGS entry at 84 and GUIDE at 99
guest frames, against native Party at 77 and Bag at 87; visible cursor updates take 6–7
frames, within the native 4–7 sample. GUIDE retains a 0.2-second entry difference
against the Bag. An in-place Italian update is prepared, without device installation.
Five current bounded raw-save cycles preserve protected data; strict audit differences,
incomplete global coverage and pending device measurements remain explicit in
the [UI validation report](source/docs/ui-1.3.1-validation.md).

Before the latency successor above, one advanced current-save copy completed
Continue, field load, native SAVE and cold restart on physical Android with
the previous Italian candidate `420ec8b8…f059a`. Protected
Pokemon/progress/inventory/settings were preserved; the personal original save
remained byte-identical while only the ROM was replaced at its existing path.
[Evidence and limitations](source/docs/ui-1.3.1-validation.md) remain distinct
from complete gameplay, English, performance and release acceptance.

Offline player packages are prepared with 25 direct input routes per language,
two independently checked decoders, current bilingual installation/feature
PDFs and unchanged credited manuals. Unverified legacy cheat catalogues are
omitted. [Package checks and identities](source/docs/package-1.3.1-validation.md)
are separate from device gameplay and production release acceptance. No files
have been published; 1.2.5 remains the public release.

The [public bug and fix list](BUG-FIXES-1.3.1.md) separates fixes inherited
from HeartGold, Sacred Gold and Plus from reports still open. The original
strict save audit remains NOT PASS for native map-object state in array10.
A bounded reassessment of exact observed changes passes all eleven Continue →
SAVE → cold cycles, including a populated Italian save; it preserves the
original reports and does not establish compatibility with every older
version. The [candidate report](source/docs/ui-1.3.1-validation.md) records
the cause, proof and remaining limits. No player package or device acceptance yet.
Two additional early-game saves from updater routes labelled retail US and
Plus 1.03 pass the same bounded EN cycle. Their earlier origin and populated
games from those versions remain outside this sample.

The new private EN/IT trial also fixes SG-11 fishing (zero night overrides in
battle and phone consumers, bounded encounter tails) and HG-T09 native IGT
rollover. All 253 focused tests pass in 31.046 seconds with no skips; an
independent review found no important issues. The maintainer performs the
extended feature tests on-device. Current identities and bounded local save
coverage are in the [candidate report](source/docs/ui-1.3.1-validation.md).
The paragraphs below retain earlier milestones and their limits; older trial
files do not contain the new repairs. No Android or release acceptance is claimed.

The inherited-bug audit also corrects the Eevee guard’s movement alignment
(BUG-131-01) and integrates guarded script repairs for the one-item
Full Heal pickup, friend-loss cleanup, Steven’s pending Lati reward and its
full-Bag guard, plus the native Lullaby underflow correction. Archive changes
are merged before the single UI append; native bytes remain confined to the
original overlay slot. Code/model before-and-after tests and independent
readback are documented in the [audit report](source/docs/bug-audit-1.3.1.md).
The expanded catalogue contains 43 qualified retail cases and six further
leads; Hail was already corrected in Plus 1.03. Earlier manual-trial files stay
unchanged; new SAVE/cold, visual/device and release acceptance remain open.
The bounded follow-up audit found no additional confirmed gameplay defect;
its scanner overflow hypothesis was withdrawn after checking the real buffer.
The Reddit commenter’s unnamed alternative remains unidentified.

A private manual-device trial is available with the three guarded features
active, at the maintainer’s request to perform functional testing on-device.
It differs from the independently verified inert image only in six activation
booleans and is explicitly not runtime-accepted. Production proof gates remain
strict. The extended campaign was stopped; its incomplete result is retained.
The stale cold-retirement interval assertion is corrected;161 targeted checks
pass. Runtime/save/performance acceptance is delegated and remains unclaimed.

A [source-qualified retail HGSS catalogue](source/docs/known-bugs-hgss.md) and
[twenty-case legacy hack register](source/docs/legacy-bugs-1.3.md) now distinguish
reports, code evidence and exact-candidate static checks. The inspected inert
1.3.1 pending files retain the Lullaby path, Facade/Strength resources and
several legacy script/data defects. The first research pass applied no gameplay fixes. The subsequent repairs
above establish no new gameplay or save compatibility acceptance. Its findings
are bound to the documented inert hashes, not automatically to later trials.

At this historical checkpoint the full 1.3.1 chain was integrated through the
V1.3.1 title identity.
Verified old Guide retirement gates the four resident child slots; overlay126
is appended once and included in the UI seeds. Separate immutable mechanics
configuration is independently replayed and checked against one common inert
candidate. Both complete inert candidates reach Continue and the field in the
local native harness. Summary legend, portable storage and rematch variants
still awaited candidate-bound Android activation evidence. A later private IT
candidate `420ec8b8…f059a` activated all three in its bytes; portable storage
has since been used manually on physical hardware and passes the bilingual local smoke,
while Summary controls and configurable rematches still lack equivalent
candidate-bound runtime acceptance. Final save/cold and performance acceptance
remain open; this checkpoint is not transfer-ready.

The frozen mechanics source delivery now includes one append for declared archive
changes, the guarded Keen Eye stage, six ribbon-dialogue tail repairs and the
full-party Eevee guard. Mandatory archive producers are derived by the builder.
In those checkpoint images Summary controls, portable storage and rematch
variants remained inert pending verified Guide retirement and overlay
integration. Later private candidates activate their bytes; that later state
does not retroactively add runtime acceptance to this source checkpoint.
Portable storage is now separately proven usable, while Summary controls and
configurable rematches still need their own runtime evidence. This source
integration establishes no new Android or save acceptance; 1.3.1 is not yet
ready to replace the current device copy.

The successor builder now composes UI, modern move data and the post-KO AI
scoring correction, with independent stage replay and protected UI seeds.
The AI reader now rejects altered BLZ encodings and missing receipt hashes.
The resident policy reconciles conditional slots for controls, portable box,
module stubs and Keen Eye; these reservations do not activate those features.
Source checks and the Italian integrated Android entry/Guide/Settings/return
smoke pass on `d8a71af2…c32f115`, with unchanged saves after normal exit.
Final battle/save/restart/performance acceptance is still pending. The controlled L retest remains on page2/2, despite passing
controller tests; this is an open runtime issue.

The Guide now restores list borders after native text rendering, preserving
glyphs and dirty-row boundaries. Five focused tests, seven native-font frames
and both canonical ROM compositions pass; the Italian Android candidate
`85ac4963…bbfc48` confirms the border fix, Info/selector/cancel paths and unchanged
saves. The module uses 63,220 of 65,536 bytes. Entry timing is not accepted:
a single video pilot shows about 6.6 seconds for Guide and 4.7 for Settings
from initial fade to visible content. L paging needs a controlled retest.
Full runtime, save/restart and mechanics integration remain open.

The visual revision is implemented and independently reviewed: upper-screen
Guide content and physical commands, a static native Pokéball below in Guide
and Settings, and consistent button hints. The Italian candidate `97ec6430…175379`
passes the observed entry, Guide paging and return-to-field paths with unchanged
saves after normal exit without saving. Original PNG pixel comparisons confirm
the unchanged lower background across settled views; complete runtime and
performance acceptance remain open.

The Italian Android smoke now opens the HGSS-style Settings and Guide, enters
a Guide category and returns to the original field. Existing saves remain
byte-identical after normal exit without saving. Full navigation, English,
save/restart compatibility and performance validation remain open.

The Guide now opens and returns to the original field in the actual native
Italian replay. A second correction validates its native file-table cache
against the arena address range, preserving alignment and ownership checks;
17 distinct focused tests and independent review pass. This result is still
separate from Android, full navigation, save persistence and timing acceptance.

The next Guide entry correction preserves fresh-touch arming when the native
field menu is inactive, while retaining explicit B/X cancellation and native
menu activation. Independent review and 27 focused tests pass; three key
regressions were also repeated by the integrator. The 2,608-byte entry payload
still requires a canonical rebuild and actual native/Android entry validation.
The last tested candidate has working Settings entry but failing Guide entry;
this source result does not change that runtime status.

The approved successor now has reviewed source units for the settings model and
atomic owners, physical input, checked UI allocation and resource loading,
native backgrounds, incremental panel updates, bounded dynamic text rendering,
bilingual copy, persistent module loading and allocation, paired Guide screens,
native retired-heap count handling, resident ownership checks without ROM
writes, a settings render planner with corrected native-frame geometry and
a bounded pixel backend checked against independent native rendering,
a separate checked Guide reader, a resident native caller, corrected field-menu
Guide focus/input ownership and alphabetical
Guide content with immutable page sharing. The
[source verification report](source/docs/ui-1.3.1-validation.md) records focused
tests and their limits. The V4 game files remain unchanged; complete UI, Android,
old-save and composed-mechanics acceptance are still pending. Local commits do
not establish a new green GitHub CI run.

The private Android observer has passed a limited actual V4 Italian Continue,
frame/input transport and session-close test. It does not yet measure game
readiness, consumed actions, heap usage or before/after performance. The
maintainer rejected the provisional settings appearance. Source revision
`71d0ecc` adds HGSS panels, section groups, selection and command tiles, with
reviewed native pixel comparisons and a cross-view background fix. Total counted
CPU work grows by about 28%; composed Android timing and visual acceptance remain open.
The conditional Fieldbook partition has more room within the unchanged old
Guide region. Its successor entry passes 23 focused EN/IT tests and independent
review; complete game integration and all installation claims remain blocked.
A private observer successor passes independent review and 38 native/Python
checks for semantic associations and seven heap owners. It has not yet been
built as a new APK or run on Android; runtime measurement gates remain open.
Resident caller `f2aa567` preserves heap authority after application free and
refuses code release until native retirement succeeds. Focused native tests
and review pass; complete Scene integration remains pending.
Read-only Scene admission `730832e` passes independent review and 17 focused
tests. It checks current context, font and native producers; installer and
runtime evidence must still establish the full ownership lifetime.
Guide component `58eab41` adds the upper reader, lower controls, distinct button
states and lossless long-title wrapping. Its review and focused source checks
pass. Scene `3b489a8` fixes touch release during pressed feedback and retryable
suspend acknowledgement, with independent review and five focused integrator
checks. Installation and composed Android acceptance remain open gates.
The private dispatch observer also passes host review and guarded lifetime tests, including the existing non-dispatch path. Its successor
APK is built and reviewed but not installed. The separate Android synthetic
executable fails its initial compound pthread stack check before starting the
worker; diagnosis and actual game measurements remain pending. No ROM changed.
Installer `4d71e43` composes and independently checks both UI languages in
memory. Review fixes compiler scratch admission and dependency temporaries;
23 contract tests and separate canonical production checks pass. The complete
dynamic module uses 63,244 of 65,536 bytes. Persistent workbench integration,
actual game startup and Android/save acceptance remain pending.

Workbench `0489f4f` integrates the UI stage and binds historical file identities
before candidate admission and transaction changes. Independent review and 83
focused tests pass. The first persistent Italian test candidate matches the
previously checked in-memory bytes; originals remain unchanged. It has not been
promoted: actual game, performance and save acceptance remain open.

The first actual Italian Android smoke boots and continues the old save, but
Options returns to the field after a black transition without showing Settings.
The failure is retained for diagnosis; all tested save copies remain unchanged.
Guide, persistence and performance acceptance are still open.
The diagnosed entry check now recognizes the native retired-WVR bank D state
without modifying the bank. A focused regression also adds a bank recheck
before publication. Independent review and focused tests pass; the final module
fits in 63,388 bytes. The added masked work and actual Android behavior still
require runtime validation.
Android rerun of `5a0a6de` with the same APK now passes Settings entry,
selection and cancel. Guide entry still returns to the field without opening
its reader, so composed acceptance remains failed. Save copies are unchanged;
performance and persistence gates remain open.

The native test harness can select an initial hardware RTC with `--rtc` while
retaining its exact default. Parser/CLI checks and a limited EN native comparison
cover this test tool; it does not change game files or establish Android results.

## 1.3.0 — in development, not released

Status recorded on **29 October 2026**. The candidate now identifies itself as
**V1.3**; this display label does not publish a release, and 1.2.5 downloads remain unchanged.
The [complete 1.2.5 → 1.3.0 change register, in Italian](source/docs/novita-1.3.0.md)
records the before/after behavior, all 67 affected species, fixes, inherited
features and verification limits.

- Show Pokémon Sacred Gold Plus in the ROM library while retaining the original icon; use V1.3 on the title screen and Plus settings.
- Add a native field Guide with 429 entries and HGSS navigation, plus contextual Plus controls and a second Shiny page.
- Add IV consultants, Silver/Gold Caps, milestone rewards, EV policies, quick training and optional timed Day Care courses.
- Add native shiny Classic/Pro generation and targeted Search, with persistent target and chain state.
- Audit all 493 species: change base stats for 50, add two second ability slots and 32 level/move entries across 29 species; 67 species are affected overall.
- Add nine Plus-only move substitutions across seven trainers and extend the caught indicator to trainer Pokémon whose species is registered as caught.
- Correct Mew movement lifetime, SAVE-refusal feedback, high-event-flag aliasing with the Pal Pad and the clipped English migration note; harden the new Training services against payment before storage refusal.
- Preserve older save data through guarded forward migration. The [Android validation report](source/docs/android-1.3-dev-validation.md) distinguishes 49 accepted checkpoints, native-code evidence, skipped tests and remaining limits.

The [physical-device report](source/docs/device-1.3-validation.md) records the current bilingual candidate hashes, a byte-level bridge from the previous build and controlled old-save checks on Android hardware.

The V1.3 interface observations and later corrections retain their exact
candidate scope in the [UI validation](source/docs/ui-1.3.1-validation.md).

## 1.2.5 — 24 October 2026

- Show “Sacred Gold Plus 1.2.5” in the Plus options heading (Options → SELECT), so players can check the version after the one-time setup prompt has gone. Addresses [issue #6](https://github.com/Umberto-DEV/sacred-gold-plus/issues/6).
- Display **V.1.2.5** on the upper title screen, aligned with **Developed by A FAN**, and restore the missing descender in **by**. Only version text and these title graphics change from 1.2.4 in each language. Save code, the native save layout, Plus settings and expanded Bag storage are unchanged; no new game or save conversion is needed. See the [validation and upgrade notes](source/docs/version-1.2.5.md).

## 1.2.4 — 24 October 2026

- Coordinate optional battle idle animation with native OAM sprite copies: reset before copying, suspend while copies live, resume after the final owner is freed.
- Skip the field party search for Waterfall outside Surf moving south. No FPS unlock or gameplay-speed change.
- A player completed the previously blocked Latios encounter with the maintenance candidate and reported no further slowdowns. The old freeze happened after battle started; event scripts and flags are unchanged, and its specific cause remains unproven.
- Integrate maintenance and the 1.2.4 title into the public build and read-back chain. Preserve all existing save formats and public addresses.
- Ship 19 input routes in each language ZIP, including original HeartGold US/IT and all previously recognized Plus versions through 1.2.3. Every route is checked with xdelta3 and the pinned RomPatcher.js.
- Preserve original manuals and trainer reference byte for byte. Include current installation instructions, checksums, a 1.2.4 PDF guide and public reproducible packaging tools.


## 1.2.3 — 20 September 2026

- **The classic HeartGold camera in every real cave.** The native camera — the one the original game uses underground — is restored in **44 more maps**, on top of the eight indoor maps 1.2 already covered (Mahogany Town, Mt. Mortar). In Kanto: Rock Tunnel (1F and B1F), Mt. Moon and its Square entrance, Diglett's Cave, Cerulean Cave (1F, 2F, B1F) and the Seafoam Islands (1F to B4F, including the Cinnabar Gym room). Between the two regions: Tohjo Falls (both rooms), Victory Road (1F, 2F, 3F) and Mt. Silver Cave (all floors and the outdoor ledges). In Johto: Union Cave (1F, B1F, B2F), Slowpoke Well (entrance, B1F, B2F), the Ice Path (1F, B1F, B2F), the Whirl Islands (1F, B1F, B2F), Dark Cave on the Route 45 side, the Dragon's Den and its entrance, and Cliff Cave. With the Plus angled camera these caves hid paths and items behind ledges and walls; the native camera shows them as the original game intended. Outdoors, in towers, forests, the Lighthouse, the Safari Zone and the Ruins of Alph the Plus camera is unchanged, and the Plus wide camera is still what you get everywhere else. The exception table grows from 24 to 68 entries and moves from `0x023D8040` into the ARM9 reserve at `0x023D8A10`, where it has room to grow; the hook's only change is the two pool literals that point at it. No map data and no code instruction changes: the ROM differs from 1.2.2 by 208 bytes for the camera plus the one byte of the version string. Verified on all 540 map headers in both languages, with the read-back, 30 mutants and a three-cave run on the headless bench. **A save made inside one of these caves keeps the previous camera until the next map change** — the map's camera type is frozen in the field data when the save is written. This is the behaviour Mt. Mortar has had since 1.2, not a new defect.
- **The Fly landing was investigated and is not a ROM defect.** The landing in front of a Pokémon Center was captured frame by frame on the headless bench with the software renderer: 1.2.2 draws it exactly as 1.1 does, with NPC smoothing on or off. The flicker reported on Android comes from the emulator's OpenGL renderer; switching melonDS to the software renderer avoids it. Nothing was changed in the ROM for this.
- The in-game version now reads "Sacred Gold Plus 1.2.3" on the screen shown at Continue. The title screen and game header remain unchanged, so 1.2.2 cheat files still apply. Each ZIP carries direct patch routes from both 1.2.2 editions.

## 1.2.2 — updated 19 September 2026 (second edition)

- **The "SELECT → Plus" hint in the Options menu is back on every visit.** The bottom-left line reminding you that SELECT opens the Sacred Gold Plus page showed only on the first visit of a session and after opening and closing the page: leave the Options menu, come back, and it was gone. The game destroys and recreates its Options app at the same heap address and clears the layer, while the page trusted its own "already drawn" flag, which lives in the ARM9 reserve and outlives the app. `opz_suggerimento` now reads the game's own tilemap for that layer (the cell at the hint's position holds the hint's first tile or it does not) and redraws when needed; the flag is kept only as a mirror for the read-back. Present since 1.2. Reproduced and verified on the headless melonDS bench in both languages: first visit, second visit and after closing the page give pixel-identical bottom screens, and the Unicorn suite has two new tests that fail on the previous payload. The published 1.2.2 downloads were replaced in place, as the 1.2.1 update was, and each ZIP now also carries a direct patch route from the first-edition 1.2.2 game, so nobody has to go back to 1.2.1. Saves are unchanged.
- **Build from the original ROM.** `sgp12.costruisci` and `sgp12.verifica` now start from an unmodified Pokémon HeartGold ROM, US or Italian, and nothing else: a new first step ("stage 0") derives our 1.1 base from it by applying a published xdelta patch, then the seventeen blocks run as before. Rebuilding no longer depends on owning an intermediate ROM of ours. The two patches are release assets and contain only differences — they are not ROMs and do nothing without the HeartGold they belong to; no game file is distributed. `source/sgp12/base11.json` pins, for each language, the accepted ROM's SHA-256, the patch's name and SHA-256, and the SHA-256 the resulting base must have; all three are checked before any block runs, and any mismatch is a refusal. `python3 -m sgp12.scarica_base --destinazione "$SGP_ROM_DIR"` fetches the patches once and deletes anything that does not match its pin; it is the only command here that uses the network, and nothing calls it for you. `xdelta3` is now a build requirement, and the refusal names the package to install. A 1.1 base passed to `--base` is still accepted and skips stage 0 with a warning; `--lingua` became optional, since the language follows from the ROM's SHA-256.

## 1.2.2 — initial release, 19 September 2026

The initial 19 September build (morning) lacked the Options-menu hint fix above. The current [1.2.2 downloads](https://github.com/Umberto-DEV/sacred-gold-plus/releases/tag/v1.2.2) include it, and take the first-edition game as one of their patch sources. The game header remains unchanged.

- **The expanded Bag no longer loses its extra slots in silence.** A save whose extension sectors could not be read once, or that a converter normalised to a single repeated byte, is written again instead of dropping the 108 extra slots at every reload. A spent or out-of-range slot is emptied where it sits, so nothing else changes position, and the game keeps the same cleaned inventory in memory. Foreign data in those two sectors is still never overwritten: the [feature notes](source/features/capacita-borsa/README.md) say how to tell and how to clear them by hand.
- Optional battle motion: the B-pose accent now holds the pose for the time the game itself uses for the same frame (0.33–1.00 s depending on tuning, chosen with `--variante`) instead of 2–3 ticks, and starts only at the breathing motion's resting peak. See the [v5d notes](source/features/anim2/README.md#v5d--accento-di-posa-b-18-settembre-2026).
- **A successful pickup no longer reports "Bag is full".** Picking a Poké Ball up off the ground showed the "left behind" message every time the item was in fact collected. The capacity check was not at fault: the capped-gift block kept its "I discarded something" flag on a script variable the engine writes itself with the id of the object you interacted with, which is `1` for a ground ball — the exact value the guard compares. The flag moved to a special variable no script and no engine path writes, and the hook now always sets it. The warning is shown only when the item really is left behind.
- The in-game version now reads "Sacred Gold Plus 1.2.2" on the screen shown at Continue. The title screen and game header remain unchanged, so 1.2.1 cheat files still apply.
- Tools and documents: the ARM9 reserve register is back in step with the blocks, `sgp12.verifica` tells PARTIAL apart from GREEN instead of reporting both as green, and the bench probes and scripts for the battle-animation phases were corrected.

## 1.2.1 — updated 15 September 2026

- Expanded all Bag pockets to whole six-slot pages: 252/42/30/102/66/12/30/60 slots. Existing saves import; extra slots are stored in a checked save extension and are unavailable to older ROMs.
- Added the searchable 493-species/level picker with the companion melonDS Android 2.1.1 build and an in-game L+R toggle.
- Replaced broken male/female + nature codes, updated the nature-only family and removed the incompatible clean-ROM overlay workaround. The current catalogue contains 2,110 codes in 67 folders. See the [catalogue audit](source/docs/cheat-catalogue-validation.md).
- Reduced party menu opening from 33 to 20 frames in the tested battles by reusing loaded move data.

- Refined optional battle motion: the idle cycle runs at 0.375× with interpolated steps and a gradual restart; the name, level, HP and EXP panels stay still. Motion continues through menu selections and yields to native move, entrance and fainting animations.
- Stops battle idle tasks before capture so they cannot animate the Pokémon reused by the Pokédex or nickname screen. Corrects cleanup when a Pokémon is replaced or the battle ends.
- Reduced the battle Bag opening pause with optional battle motion enabled: the Bag reuses item data already loaded for the battle. Local English and Italian tests reduce the pause from about 0.9 to 0.12 seconds; short loading pauses remain. See the [implementation and checks](source/features/borsa-lotta/README.md).
- Added regression coverage and a [source-backed animation audit](source/features/anim2/AUDIT-2026-09-14.md).

## 1.2.1 — initial release, 13 September 2026

The initial 13 September build used the previous Bag capacity and save layout. The current [1.2.1 downloads](https://github.com/Umberto-DEV/sacred-gold-plus/releases/tag/v1.2.1) include the 15 September changes above; the extra Bag slots are not available in older ROMs. The game header remains unchanged.

- **A full item stack no longer blocks a free gift or pickup.** The existing quantity cap stays in place; excess items are discarded and a message names the item that could not be kept. Purchases, exchanges, mail and key items keep their original checks.
- **Optional battle motion extends to both sides and the Bag and party menus.** Motion pauses during move animations. The setting remains off by default; loading transitions can still pause the whole battle display.
- **The in-game version now reads "Sacred Gold Plus 1.2.1"** on the screen shown at Continue. The title screen and game header remain unchanged.
- **The cheat catalogue is reordered and grown**: 67 folders instead of 56, 2113 codes instead of 1510. The 1510 existing codes keep their exact bytes — order, naming and notes are what changed. The 603 new ones are the wild-encounter family, 493 species and 100 levels. Every code that needs a button now says which one; 94 of them did not.
- The guard the wild-encounter codes check was re-read from the 1.2.1 image in both languages and matches, and one species and one level were measured on a headless emulator running the English build. The other 492 species and 99 levels differ by a single field and were not measured one by one; the Italian build was checked statically only. The shipped notes say so.
- **A Rare Candy no longer closes the party menu.** Use one and the menu stays open on the same Pokémon, ready for the next: levelling a team no longer means walking back through the Bag for every single candy. It leaves the menu exactly as before whenever the game has something of its own to do — an evolution, a move to replace, the last candy in the bag — so nothing about those paths changes.
- **The options page no longer lets you change a setting that would not stick.** When the save's Sacred Gold Plus block is missing or has been rejected, all five entries are now shown as unavailable instead of only the two difficulty ones. Before, the animation, NPC and online entries let you move the cursor, press A and see the new value drawn while nothing was written — not then, not later.
- **Turning NPC smoothing off now takes effect immediately.** The setting gave the game back its own character-loading budget only at the next map change; within the same area, switching it off did nothing visible. It is handed back on the first frame after you confirm.

## 1.2 — 13 September 2026

Download: the [1.2 release](https://github.com/Umberto-DEV/sacred-gold-plus/releases/tag/v1.2), one ZIP per language. Saves from 1.1 open in 1.2 and 1.2 saves open in 1.1, checked byte for byte. Cheat files do not carry over from 1.1, because 1.2 has a different game header: re-import the ones in the 1.2 package, where every code starts switched off.

- **Plus difficulty extended to levels.** Tougher trainers and, separately, scaling wild Pokémon. Both are optional, both are capped at level 100.
- **A Sacred Gold Plus options page**, opened with SELECT during play. On Continue the game asks once whether you want to look at it.
- **The classic HeartGold camera, restored natively** in eight indoor maps (Mahogany Town, Mt. Mortar). No cheat needed.
- **Smoother towns**: fewer characters are loaded at once when entering or leaving one.
- **Optional animated Pokémon in battle**, off by default.
- **Online server choice**: pick which Wi-Fi connection slot handles GTS and battles. Mystery Gift connects automatically. A service falls back to the first configured slot when its designated slot is not set up, and to the original behaviour when none is.
- **Over 200 text corrections** in English and Italian.
- **A cleaner title screen**, with a single, more legible credit line.
- **The EV/IV guide** on a Pokémon's Ability page no longer shows an automatic "START Guide" label; press START there to open it.
- Bug fixes.

This release also opens the development side of the project: the sources, tools and tests that build and check the game are in [`source/`](source/), the technical documentation is in [`source/docs/`](source/docs/), and [`source/README.md`](source/README.md) describes how to work on it. No game file is distributed: the tools read the player's own.

## 1.1 — 11 September 2026

Published as a development branch rather than as a player release. It carried the native indoor camera work, the bag input fix, the repel re-arm fix and the first version of the reserve used by 1.2. Its patches were superseded by 1.2.

## 1.04 — 9 September 2026

The download had a simpler layout and names: **Sacred-Gold-Plus-[Normal-Angle or New-Angle]-[IT or US].zip**. The four game outputs were unchanged from the earlier 1.04 packages; existing players with a matching game fingerprint did not need to patch again.

- Each ZIP included **Install-or-update.html**, recognizing the supported unmodified **US HeartGold** and **English Plus 1.01, 1.02 and 1.03** inputs and automatically selecting the matching update for that ZIP's language and camera. It processed files offline in the browser, with no ROM upload and no program installation, recognized an already-current target and refused unknown inputs.
- Seven optional cheat codes in **Cheats**, in desktop MCH and Android XML formats, all starting disabled.
- File checks, changes and credits collected in **Manual/Project Notes.txt**; the full licence remained included separately.
- Restored two damaged hardware-wait instructions in the 1.03 game, repaired malformed text-formatting instructions, corrected selected trade dialogue and English move names, repaired the Pokédex search resources used by the height and weight controls.
- Added Italian dialogue, menus and selected interface graphics, with an accented-character naming keyboard.
- Added the optional Normal Angle camera; New Angle retained the camera used by Sacred Gold Plus 1.03.

Fairy typing, the additional Fairy moves and the 1.03 battle changes come from the earlier project. They are not features created for 1.04.

## Known limits

- Full-story and post-game testing is still needed. Some corrected dialogue and translated screens need further in-game review.
- The original game's reported event issues are not all fixed. Please report a reproducible case rather than assuming a historical bug list is resolved.
- Newly added Fairy moves can still use their older battle animations, as reported by the original Plus author.
- The optional battle motion moves existing sprites; it does not add per-species animation frames. Full-story and hardware coverage remain incomplete.
- The Wi-Fi slot fallback is fully demonstrated for three of its five cases on the test bench; the two that need a live online trigger were checked under emulation only. Official online services for this game are long discontinued.
- Cheats: the codes shipped in the package have bounded checks on the real game core. This is not full-game cheat coverage or a promise about every emulator.
