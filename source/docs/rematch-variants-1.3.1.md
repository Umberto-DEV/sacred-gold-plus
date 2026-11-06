# Configurable rematch teams in 1.3.1: Falkner and Bugsy

**This owner is implemented but remains inert in the current player profile.**
Host/ARM tests establish the contracts below; Android context/balance acceptance
is not established by them. No move/ability/item ID, setting or save format is
added. Current composition and activation state are in
[the build guide](../sgp131/README.md) and
[validation report](ui-1.3.1-validation.md).

## Behavior when activated

With Plus difficulty, eligible ordinary single battles against Falkner 712 or
Bugsy 713 can replace the entire native party buffer with one of two authored
six-member teams, A or B. Normal, other trainers, League, doubles/link/multi/tag/
facility contexts and enemy indices other than the allowed one remain native.
Base levels, difficulty byte (31 IV), capsules, rewards, schedules, contacts and
entry routes stay unchanged. The module never reads the player's team, advances
RNG, stores a counter or persists state.

Selection is `variant = (seed ^ (seed >> 16) ^ trainer_id) & 1`, 0=A/1=B. `seed`
is the LCRNG value already saved by the native constructor at `[sp+0x68]` and
restored at `0x02073A8E`. This is a two-way selector, not a random generator.
It replaces the whole 108-byte transient buffer once, before species/overrides/
PID/ability are read; the buffer then stays fixed throughout battle. It does
not guarantee alternation: consecutive battles, retries and cold boots may
repeat the same team.

## Team data

B applies its listed substitutions to A. Base levels are native, then adjusted
by the unchanged Plus level hook. Aces remain Falkner's slot 6 Pidgeot and Bugsy's
slot 2 Scizor at base level 72. Names below use the English game resources; the
Italian build uses the same IDs and mechanics.

### Falkner (712)

#### Native baseline

| Slot | Species | Base level | Item | Moves |
| ---: | --- | ---: | --- | --- |
| 1 | Fearow | 68 | - | Roost, Drill Peck, Tailwind, Megahorn |
| 2 | Pelipper | 64 | - | Spit Up, Air Slash, Tailwind, Hydro Pump |
| 3 | Swellow | 68 | Flame Orb | Endeavor, Aerial Ace, Agility, Air Slash |
| 4 | Noctowl | 66 | - | Psycho Shift, Roost, Dream Eater, Nasty Plot |
| 5 | Staraptor | 70 | - | Close Combat, Agility, Brave Bird, Double-Edge |
| 6 | Pidgeot | 72 | Sitrus Berry | Tailwind, Mirror Move, Air Slash, Brave Bird |

#### A

| Slot | Species | Base level | Item | Moves |
| ---: | --- | ---: | --- | --- |
| 1 | Fearow | 68 | - | Roost, Drill Peck, Tailwind, Megahorn |
| 2 | Pelipper | 64 | - | Ice Beam, Air Slash, Tailwind, Hydro Pump |
| 3 | Swellow | 68 | Flame Orb | Endeavor, Aerial Ace, Agility, Facade |
| 4 | Noctowl | 66 | - | Psychic, Roost, Air Slash, Nasty Plot |
| 5 | Staraptor | 70 | - | Close Combat, Agility, Brave Bird, Double-Edge |
| 6 | Pidgeot | 72 | Sitrus Berry | Tailwind, Roost, Air Slash, Brave Bird |

#### B

| Slot | Species | Base level | Item | Moves |
| ---: | --- | ---: | --- | --- |
| 1 | Crobat | 68 | - | Roost, Brave Bird, U-turn, Cross Poison |
| 2 | Pelipper | 64 | - | Ice Beam, Air Slash, Tailwind, Hydro Pump |
| 3 | Swellow | 68 | Flame Orb | Endeavor, Aerial Ace, Agility, Facade |
| 4 | Noctowl | 66 | - | Psychic, Roost, Air Slash, Nasty Plot |
| 5 | Staraptor | 70 | - | Close Combat, U-turn, Brave Bird, Double-Edge |
| 6 | Pidgeot | 72 | Sitrus Berry | Tailwind, Roost, Air Slash, Brave Bird |

### Bugsy (713)

#### Native baseline

| Slot | Species | Base level | Item | Moves |
| ---: | --- | ---: | --- | --- |
| 1 | Yanmega | 70 | - | Screech, U-turn, Air Slash, Bug Buzz |
| 2 | Scizor | 72 | Sitrus Berry | Iron Head, Swords Dance, Feint, Night Slash |
| 3 | Heracross | 68 | Damp Rock | Reversal, Feint, Megahorn, Horn Drill |
| 4 | Masquerain | 70 | - | Air Slash, Whirlwind, Bug Buzz, Hydro Pump |
| 5 | Vespiquen | 68 | - | Toxic, Defend Order, Destiny Bond, Air Slash |
| 6 | Pinsir | 69 | - | Guillotine, Superpower, Megahorn, Close Combat |

#### A

| Slot | Species | Base level | Item | Moves |
| ---: | --- | ---: | --- | --- |
| 1 | Yanmega | 70 | - | Protect, U-turn, Air Slash, Bug Buzz |
| 2 | Scizor | 72 | Sitrus Berry | Iron Head, Swords Dance, Bug Bite, Night Slash |
| 3 | Heracross | 68 | - | Reversal, Rock Slide, Megahorn, Close Combat |
| 4 | Masquerain | 70 | - | Air Slash, Whirlwind, Bug Buzz, Hydro Pump |
| 5 | Vespiquen | 68 | - | Toxic, Defend Order, Heal Order, Air Slash |
| 6 | Pinsir | 69 | - | X-Scissor, Superpower, Megahorn, Close Combat |

#### B

| Slot | Species | Base level | Item | Moves |
| ---: | --- | ---: | --- | --- |
| 1 | Yanmega | 70 | - | Psychic, U-turn, Air Slash, Bug Buzz |
| 2 | Scizor | 72 | Sitrus Berry | Iron Head, Swords Dance, Bug Bite, Night Slash |
| 3 | Heracross | 68 | - | Reversal, Rock Slide, Megahorn, Close Combat |
| 4 | Forretress | 70 | - | Spikes, Rapid Spin, Gyro Ball, Earthquake |
| 5 | Vespiquen | 68 | - | Toxic, Defend Order, Heal Order, Air Slash |
| 6 | Pinsir | 69 | - | X-Scissor, Superpower, Megahorn, Close Combat |

## Rationale and risks

A removes unsupported combinations: Spit Up without Stockpile, Mirror Move in
singles, unsupported Psycho Shift/Dream Eater, two OHKO moves (Guillotine/Horn
Drill) and ineffective Feint. Facade/Nasty Plot intentionally add pressure using
existing moves/items. B replaces Falkner's Fearow with Poison/Flying Crobat
(U-turn pivot) and Staraptor Agility with U-turn; for Bugsy it replaces Yanmega
Protect with Psychic and Bug/Water Masquerain (this hack's type, not Bug/Flying)
with Bug/Steel Forretress carrying Spikes/Rapid Spin/Gyro Ball/Earthquake.

There is no uniform EV/IV increase or new effect. Move IDs are 1..467 with current
`a/0/1/1` effects: Facade 263/effect 169, Psychic 94/72, Protect 182/111,
Bug Bite 450/224, Rock Slide 157/31, Heal Order 456/32, X-Scissor 404/0,
Spikes 191/112, Rapid Spin 229/129, Gyro Ball 360/219, Earthquake 89/147,
U-turn 369/228, Cross Poison 440/209, Ice Beam 58/5. Repurposed IDs
6/27/134/140/160/169/176 never appear, enforced by a test. Feint 364 and Toxic 92
retain the hack's existing power/accuracy differences from retail.

Each added species/move pair is legal by current level/TM/HM data:
`a/0/3/3` learnsets, `a/0/0/2` TM compatibility and native TM table `0x021000CC`.
Exact sources are pinned in JSON; changed data rejects the configuration. Type
checks confirm Poison/Flying Crobat, Bug/Steel Forretress and Bug/Water Masquerain.

Unmeasured risks remain explicit: Guts Swellow's existing Flame Orb plus Facade
is the largest added physical threat; Nasty Plot/Psychic/Air Slash gives Noctowl
reliable special setup; Forretress Spikes/Rapid Spin and native AI choices may
create setup/recovery loops (including Heal Order/Roost/Swords Dance). Bugsy's
coverage broadens and B adds a Steel resistance. No balance comparison has been
run; higher damage or a boss win would not by itself demonstrate better AI.

## Preparation sources checked in game data

The Guide's static acquisition audit covers scripts/item balls and 30 shop
inventories, not a full emulator playthrough. Rematches need 16 badges via the
native gate; every source's reachability at that moment and the acquisitions
themselves were not played.

Falkner's Flying teams have several preparation routes:

- TM80 Rock Slide: Ruins of Alph southeast chamber, second room.
- TM13 Ice Beam: Ice Path B1F, Seafoam Islands B4F or 4000 Goldenrod Game Corner coins.
- TM24 Thunderbolt: shore beside Olivine Lighthouse, Cerulean Cave 2F, or 4000 coins.
- TM12 Taunt: Celadon Department Store 3F; limits Nasty Plot/Roost/Tailwind/Agility.

Against B's Crobat/U-turn, the first three hit all Flying members; Taunt limits
Noctowl setup/recovery. These routes do not require one rare species or a hidden
counter, and no single preparation is promised sufficient.

Bugsy requires species-specific type accounting: Rock is **neutral** against
Bug/Steel Scizor/Forretress (Bug 2× × Steel 0.5×), not super effective.

| Route | Checked sources and coverage |
| --- | --- |
|Fire|4× against Scizor/Forretress; 2× against Heracross/Pinsir/Yanmega/Vespiquen. TM35 Flamethrower: Bellchime Trail, Route 28 or 4000 coins. TM38 Fire Blast: Goldenrod Department Store 5F beside TM17 Protect (native shop 7 contains item 365 in EN/IT). TM50 Overheat: Burned Tower B1F item ball.|
|Rock|4× against Yanmega/Vespiquen; 2× against Pinsir; no advantage on Scizor/Forretress/Heracross. TM80 Rock Slide as above; TM39 Rock Tomb at Union Cave B1F.|
|Taunt|TM12 as above; prevents Spikes/Swords Dance/Toxic/Heal Order/Defend Order.|

Against B's Forretress/Scizor, independent Fire sources TM35/TM38/TM50 and Taunt
are relevant; Rock helps against Yanmega/Vespiquen. Field pickups for TM39/50/80
and TM35 are statically verified Guide sources, not played acquisitions.

## Native mechanism and ARM evidence

The seam replaces `BL 0x020735E8` (`TrainerData_ReadTrPoke`) at `0x0207363A`
inside `CreateNPCTrainerParty` (`0x02073604`), resuming `0x0207363E`. The wrapper
saves r0–r2, r4–r7, LR (eight words, 8-byte SP alignment), calls the reader **once**,
conditionally applies the core, and returns the native result. Four Plus level
hooks `0x02073718/0x02073802/0x0207390C/0x02073A0C` remain intact.

Guards require Plus byte `0x023D8700` (read by level function `0x023D8134`), exact
enemy-index/battleType whitelists, coherent buffer/ID versus host frame, format 3,
six members and byte-identical freshly read native party. It remains installed
with `active=0` until real `context_proof` identifies `capture_file`,
`capture_rom_sha256`, `build_id`, and explicit matching `candidate_sha256` of
the captured inert candidate. Test-only synthetic proof is refused by default
and marked `synthetic`; reference values (1, 1) are not measured evidence.

The module is a nonresident overlay 126 replacing a 20-byte unused placeholder.
Its y9 window is `0x0226B000`, uncompressed; a 2048-byte image is appended as
file 126. Measured code 1216 bytes/config 716; module stack 184 bytes below host SP,
200 with stub frame, no allocations or persistent state. A 60-byte resident
`stub.S` uses reserve owner `c8.module-stubs`, whose base must come from a
policy-rechecked `sgp131.reserve.allocate` receipt. It calls
`HandleLoadOverlay(126)`, runs the module, and calls `UnloadOverlayByID(126)`
on success, inert, occupied-window and failed-load paths. Rejected/failed loading
falls back to the native reader. Its RAM window overlaps only battle overlay 12;
the stub never writes r4–r7 (`r4` is the module's BattleSetup).

Every trainer-party construction loads/unloads this overlay: an ID filter does
not fit the 64-byte stub budget. Device cost and real filesystem stack/timing
(`FS_LoadOverlayImage`) remain unmeasured; that boundary is stubbed in the bench.

Unicorn executes real EN/IT V4 ARM9 construction (CreateMon, encryption, stats,
LCRNG and level hooks), stubbing only allocator/archive reader/species-name/NARC
handles. All six produced records match native construction from the selected
team: species/form, PID, gender, ability, nature, IV/EV, level, moves/PP, item, capsules,
checksum and full struct. Matrix: EN/IT × Normal/Plus × A/B. Global seed,
alloc/free sequence, SP, registers, RAM match; excluded contexts/inert forwarding
match native; seven existing 1.3 strategic trainers remain unchanged. This is not
Android evidence. Only used move records are read, never Will-O-Wisp member 261,
so `modern_moves` installation order does not matter.

## Checks

```sh
PYTHONPATH=source .venv/bin/python -m unittest sgp131.test_rematches -v
(cd source/features/rematch-variants/test && ../../../../.venv/bin/python -m unittest test_variants -v)
PYTHONPATH=source SGP_REMATCH_REQUIRE_INPUTS=1 .venv/bin/python -m unittest sgp131.test_rematches_rom -v
(cd source/features/rematch-variants/test && SGP_REMATCH_REQUIRE_INPUTS=1 ../../../../.venv/bin/python -m unittest test_hooks -v)
SGP13_BASE_DIR=/private/path/1.2.5 PYTHONPATH=source .venv/bin/python -B -m unittest sgp13.test_teams_arm -v
```

Historical suite sizes: 26 host, 6 C core, 40 ROM/Unicorn, 6 hook tests. The final command
checks seven existing trainers using exact 1.2.5 inputs; absent inputs skip.
ROM suites read SHA-256-verified V4 EN/IT in memory only;
`SGP_REMATCH_REQUIRE_INPUTS=1` makes missing inputs fail instead of skip.
`rom_fixture.declared_reserve` is an explicit test policy with its own version/
digest, rejected by the production policy. It grants copied map slot
`c8.module-stubs` at `0x023D59E0`, 192 zero bytes in V4/UI output, while its parent
was conditional. Production needs an independently granted current allocation.
`test_rematches_rom.RealUiComposition` uses the actual UI output.

No alternation or player-team adaptation is promised. The 18-battles-per-trainer/
language plus baseline balance campaign and natural phone/Dojo entry paths
are not established by this report.

## Proof and post-review safeguards

`validate_context_proof` rejects `synthetic_harness_only` unless test-only
`allow_synthetic=True`. Measured proof requires matching candidate/capture SHA-256,
`capture_file`, `build_id`; receipts record `proof_origin` (`android`/`synthetic`),
`proof_sha256`, both hashes, `function_state` recomputed from installed `active`,
and `candidate_relation`. Removed `context.status` process labels are not
program state.

`REMATCH_CONFIG_BYTES` is a compile-time bound equal to the allocation and limits
the core at runtime. `test_hooks.AllTrainersSweep` compares active/native for
one trainer per archive (format, count), Plus 0/1, both selector outcomes, EN/IT:
zero differences. Enemy indices are bounded 0..3 in wrapper/config; `DirectGate`
also exercises 4/7/8. Item pins cover records 158/273/285 and member count rather
than the whole `a/0/1/7`. Plus is 0/1 by contract; wrapper requires `==1`, whereas
the native level hook treats any nonzero as Plus. An invalid third value would
retain native rematch teams while applying Plus levels.

The inherited Dojo script 832 enters trainers 712/713 with `a4=1`.
`SetupAndStartTrainerBattle` at V4 `0x02051370` (184-byte pinned `setup` function,
executed in Unicorn) creates battleType `0x1` for phone (`a4=0`) and `0x801`
(`BATTLE_TYPE_11`) for Dojo. Exact whitelist is `{0x1, 0x801}`, one entry per family
in `gate.context.families`; all others (including `0x800`, `0x803`, `0x13`, `0x4B`, `0x3`)
forward natively. Proof observations use `family`, not `entry`, and require exact
family/value for both trainers and both families. A preceding stage changing
`setup` is refused by installer/readback. These runtime values still require
real Android capture before activation.

`verify(require_measured=True)` defaults to refusing synthetic receipts and
requires matching candidate/capture hashes and coherent origin when active.
The final builder must call `rematches.candidate_gate(final_rom, receipt)`:
`inert_view` zeros only `active` in overlay 126 found through FAT, and the final hash
must equal proof `candidate_sha256`. The relation label alone is not attestation.
Clang version/binary hash is pinned like `controls.py`.

Overlay 126 modifies y9, FAT, cartridge length and header CRC. UI length/y9 CRC
seeds must include this appended-file change; finalization must therefore run
in the correct composition order. Pin audits apply before installation, not
after the guarded sites have changed.
