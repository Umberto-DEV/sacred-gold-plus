# ANIM2 — continuous battle motion

`sgp.anim2` v5d remains part of the **1.3.1** build chain. Battler sprites move
at **0.375×** the former speed, with interpolation and gradual resumption. Name,
level, HP and EXP panels remain still. Seven menu transitions preserve the task;
destruction and Safari stop it. Motion suspends during moves, entry, native
animation, resizing, disappearance and fainting. Capture stops all tasks before
Pokédex/naming can reuse their sprites.

Menu loading can still pause the whole scheduler. Keeping a task alive cannot
advance it during that pause, so this feature does not promise motion in every
frame. The [Bag](../borsa-lotta/README.md) and
[Party](../squadra-lotta/README.md) caches shorten specific loads separately.
The later [maintenance barrier](../manutenzione/README.md) also suspends motion
while native OAM copies own a sprite image.

The 2048-byte block at `0x023DB500` has separate code, canary, table, parameter,
nine-`lr`, state and four-slot regions. It uses the shared chunk's `anim` field,
which defaults to OFF. Compile independently with:

```sh
python3 source/features/anim2/tools/compila_anim2.py \
  --uscita /tmp/anim2-build --livello 5c --passo 3 --variante V1
```

## Motion and ownership

The original task advances 20 degrees per tick: 18 ticks per cycle. The fixture
observed one battler tick every two video frames. The private phase clock uses
eighths and interpolates the 18-point table without slowing other game logic.

| Rate | `--passo` | Ticks/cycle | Video frames/cycle | Nominal duration at 60 Hz |
| --- | ---: | ---: | ---: | ---: |
| Former 1× | native | 18 | 36 | 0.60 s |
| 0.5× | 4 | 36 | 72 | 1.20 s |
| **0.375× default** | **3** | **48** | **96** | **1.60 s** |
| 0.25× | 2 | 72 | 144 | 2.40 s |

The 0.25×/0.5× comparisons were RAM-step probes on independent cold boots, not
separate releases. Each 300-capture window contained at least two cycles. The
default is a design choice, not a universal comfort finding. Y ranges −3..+3 px
in the fixture. ARM tests bound adjacent Y changes and resumption from rest to
one pixel, including four staggered battlers. The envelope rises 0→16 in about
half a second at the observed cadence.

`sgp_avvia_tutti` stops only native status-bar bouncing after startup; native
HP/EXP values and indicators remain managed by the game. Seven known menu stop
sites preserve the task; destruction, Safari and unknown callers retain native
stop behavior. G4 wraps `SysTask_CreateOnMainQueue` in
`BtlCmd_StartCatchMonTask` at `ov012:0x0223EBD8`, preserving callback/data/priority
and return. OFF calls only the original. `getterWork != NULL` is not a valid
permanent capture guard because EXP uses the same context.

Destruction cleans only its own battler; collective cleanup occurs at capture
entry while all battlers are alive. The active bit frees a slot before a deleted
sprite address is reused. Suspension checks `hasVanished`, crop, `dontDraw` and
scale outside 256±8: fainting crop begins before the sprite descends, so scale
alone is insufficient. It restores owned channels once, then makes no idle writes
until resumption. The compiler rejects `--sca` outside 0–8, which would otherwise
look like native transformation. Older 5a/5b presets are no longer generated:
their extended stop could traverse already-destroyed battlers.

Implementation: [C helper](sorgenti/anim_idle5.c),
[layout](sorgenti/sgp_anim5.h), [compiler](tools/compila_anim2.py),
[installer](tools/applica_anim2.py), [independent readback](tools/rileggi_anim2.py).

## B-pose accent

V5d replaces v5c's blink with a whole-pose accent at the breathing peak. Three
independent timings agree on one tick per two video frames (30 Hz): the pinned
`pret/src/main.c:109–125`, the historical runtime timing and the audit calibration.
V5c held pose B for 2–3 ticks (4–6 frames, 0.067–0.100 s), rarely 10–12 frames. Across 9060
EN/IT frames, 42/43 intervals per battler had only 4/6/10/12-frame durations; 32%
lasted 67 ms. Native `a/1/8/0` scripts hold the same frame for a median 10 calls
(0.333 s), mode 15 (0.50 s), quartiles 5/10/15. Rear Typhlosion uses 12 calls, Kakuna 15,
Togetic 9. For 99.3–99.65% of views this is a whole-body pose, not an eye closing;
Typhlosion changes 1681 pixels and Kakuna 381. `blink_dur` had remained an absolute
tick count after slowing the breathing cycle.

V5d changes four behaviors:

- The accent starts only at `SGP_PICCO_IDX` indices 4/5, where the table is flat
  (16, 16). `blink_wait` reaches zero and stays armed until that peak.
- A suspension calls `riarma()`, clearing `blink_left` and drawing a full new
  wait. Previously a frozen remainder caused a fixed flash after every move.
- Initial wait is `BLINK_MIN + (rng & MASK)` per battler. Previously four
  simultaneous slots all accented on tick 71.
- `slot.bs_visto` at `+0x18` tracks `BattleSystem`; a new battle resets the slot
  even when native addresses are reused.

`sgp_pulisci` also runs before both option-OFF returns. Turning OFF during battle
previously left `affineW/H` (±6), `shadow.yOffset` and pose behind because native
updates restore only `yOffset`. If never enabled, no slot exists and no byte is
written; tests count `Pokepic_SetAttr` calls to verify this behavior.

The blob stays **1532/1536 bytes**, leaving four bytes before the canary. Removing
unused diagnostics (`blinks +0x14`, `rari +0x18`, `stop_visti +0x20`, `dentro +0x3C`, `maxbatt +0x3D`, `ultimo_sito +0x3E`) saves 48 bytes, verified by a 1580-byte
mutant. Their offsets remain reserved holes; the first 32 state bytes are stable.
Older tools reading `blinks`/`rari` in `anim/tools/sonda_moto.py`,
`anim/tools/misura_v4.py`, `anim/tools/misura_anim.py` and
`options/tools/misura_anim.py` read v4 state at `0x023D8E40`, which is unchanged.
Only `sonda_moto.py` reads live RAM; the others consume exported CSV.

All timings are in `par.bin`; editing them does not recompile code.

| Variant | `blink_dur` | Common pose B | Rare pose B (1/3) | Nominal wait |
| --- | ---: | --- | --- | --- |
| V1 native, default | 10 | 0.33–0.37 s | 0.50–0.53 s | 4.0–8.2 s |
| V2 readable | 15 | 0.50–0.53 s | 0.67–0.70 s | 4.0–8.2 s |
| V3 long | 30 | 1.00–1.03 s | 1.00–1.03 s | 4.0–8.2 s |

All use `blink_min=120`, `blink_mask=127`. The code retains ±1 tick duration
jitter. Accent-start intervals span 240–590 frames: the random 120–247 tick wait
(240–494 frames), then at most one 96-frame cycle to reach the peak.

The compiler rejects duration below 1 (u8 underflow would yield 255),
`blink_min + blink_mask > 255`, masks other than 2ⁿ−1, maximum duration
`blink_dur + 1 + raro_piu > 255`, and phase indices ≥18. `PICCO ROSSO` also checks
that the table maximum remains at the two hardcoded peak indices. These guards
change no ROM behavior in valid builds. Breathing, ownership, nine-site policy,
G3/G4, addresses and state prefix remain unchanged.

## Historical validation

The consolidated 14–18 September 2026 evidence belongs to those candidates and
fixtures, not automatically to the current 1.3.1 image. The initial audit used
repository `d4c0e6f`, package 1.2.1 and `pret/pokeheartgold`
`0985e8718df4f25e64d6507d89c0c97c0d288981`. Main fixture: level 49 Typhlosion
versus level 19 Kakuna in National Park, switching to level 47 Togetic.

| Check | Recorded result and boundary |
| --- | --- |
| EN HUD |144 consecutive captures/menu show one name/level/HP/EXP image after the fix instead of three. Values were constant during this measurement. |
| EN Bag | Both sprites move across 300 command-menu frames and 160 pocket/item frames; 160 does not demonstrate two 96-frame cycles. |
| IT Bag |300 frames/state show 96-frame cycles in command menu, Bag, pocket and item panel; one fixture only. |
| EN Flamethrower ON/OFF |273 move-gate captures suspend both slots and idle writes; 270 full images match OFF. First three retain the prior pose before effects. |
| Failed capture | A real Ultra Ball failure returns to battle and restarts tasks; one opponent. |
| Successful capture |240 Pokédex and 120 nickname frames have identical sprite images and free slots/tasks. Debugger substitutes Master Ball at the native command; this is not a catch-rate test. |
| EN switch/KO/end | Three cold replays match through frame 6662. Player inactive 5030, recreated same address 5077, slot reacquired 5078. KO crop/suspend 6829, descent 6831, deletion 6845. All tasks/slots free 7931 through 9326; field return inspected. |
| ARM blob |20 tests cover rate/resumption/four slots/nine sites/HUD/capture/inactive-reused sprite/scale/KO crop/teardown with another invalid pointer. Real ARM9/ov012 with explicit scheduler seams. |
| Readback |14 mutants including G4 rejected, with FAT-tail protection. This is not visual acceptance. |
| EN/IT builds | Complete 1.1-base rebuilds repeat byte-identically; readbacks and T1–T5 pass. |

The wider historical 1.2.1 campaign covered command/Bag/Party/switch menus in
both languages; six native animation scripts selected in RAM in one test move
(3120 identical ON/OFF captures, not six menu-selected moves); 20 cold starts across
13 player species with four empty slots on exit; Kakuna shadow edges in nine
captures per run; native trainer entry, doubles with four slots, Safari, capture,
KO and escape. Safari intentionally keeps motion disabled. Summary/Pokédex have
no task. EN Hall of Fame through SAVE/credits produced 13572 trace rows and 38
captures identical to the pre-ANIM2 control with option/counters zero. These
wider cases were not all repeated on v5c/v5d: all species/forms, rendered Safari
and doubles, already-recorded capture, full IT battle, Hall of Fame and hardware
remain outside that revision's runtime coverage.

A separate 15 September regression on the 17-stage Bag-capacity candidates ran 14
cold EN/IT cases from raw SRAM: Party ON/OFF, Bag ON, switch/move/KO ON/OFF, and
capture→field→SAVE ON/OFF. Party ON stayed 20 task frames, Bag ON 7; Party OFF 32 VBlank
frames uses a different counter. Four fixture Master Ball captures reached
Pokédex/deposit/field/SAVE with valid saved PID `94332253`, checksum `5BCD` EN or
`5B4B` IT, identical ON/OFF within each language. Bag/Party blobs and canaries
remained intact. Final 100 menu frames had 11 enemy-crop images ON and one OFF,
with stationary message text.

Those exact ROM hashes were:

- EN `09528bd920609b14484bdf6d12fc9fe1c3239934dfdb92a3816a38fac6579d0b`.
- IT `8a28781bcd8debab4a0bfe8c7f8c6b50361733f5a6cce2ffdf8835ab7d8ebe9a`.

Private reports/captures retain the underlying evidence. No regression was
reproduced in this bounded matrix; it was not physical-console or exhaustive
animation coverage. Current candidate identities and coverage are in
[1.3.1 validation](../../docs/ui-1.3.1-validation.md).

## Reproduce and interpret

Class A `test_metadata.py` needs no ROM. Class B `test_blob5.py` needs extracted
ARM9/ov012 via `SGP_MODULI`, a directory with `moduli.json`. Installer/readback
mutants use `SGP_ROM_BASE` and `SGP_ROM_ANIM2`. Unicorn/headless JIT may require
execution outside the macOS sandbox.

```sh
python3 -m unittest discover -s source/features/anim2/test -p test_metadata.py
SGP_MODULI=/path/to/modules \
  python3 -m unittest discover -s source/features/anim2/test -p test_blob5.py
SGP_ROM_BASE=/path/to/pre-anim2-EN.nds \
SGP_ROM_ANIM2=/path/to/post-anim2-EN.nds \
  python3 -m unittest discover -s source/features/anim2/test -p test_mutanti_anim2.py
python3 source/features/anim2/tools/copioni.py borsa /tmp/bag.script --fotogrammi 300
```

`tools/sonda_fasi.py` observes real start/stop sites by `lr`;
`tools/copioni.py` generates scripts for the [runtime](../../runtime/README.md).
Both take caller paths. Their prologue/pointers target the National Park fixture
and need adaptation for other saves. `--politica nessuna` observes the actual
build. Other policies, `--anima-avversario` and `--siti-finti` alter RAM for debug;
they cannot establish natural reachability. Inspect events, counters, missing
sites and captures; process exit alone does not prove coverage. No ROM/save is
included. Whole-image reconstruction uses `sgp12.verifica` and the
[base-stage guide](../../docs/base-stage-build.md).

The [native renderer](https://raw.githubusercontent.com/pret/pokeheartgold/0985e8718df4f25e64d6507d89c0c97c0d288981/src/pokepic.c)
uses an 80×80 image, pose index and whole-image affine transform, as described in
[pokepic.h](https://raw.githubusercontent.com/pret/pokeheartgold/0985e8718df4f25e64d6507d89c0c97c0d288981/include/pokepic.h).
It cannot add independent limb/head/wing articulation. The historic audit also
credited Kalalokki's account of artists' Black/White-style sprite work in the
[Johto Times interview](https://johto.substack.com/p/vol2-50). That is artistic
practice, not a Nintendo engine specification. Species profiles, more poses
and a new rendering pipeline remain unimplemented research ideas; they are not
features of the 1.3.1 release.
